from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import box
from shapely.ops import transform as transform_geometry

from pipeline.hazard_extractor import RasterLayer, classify_imd_rainfall, extract_hazard
from pipeline.hazard_ingest import quality_summary, upsert_hazard_context
from pipeline.hazard_inputs import rain_cells_with_provenance, validate_discharge_payload, validate_rain_payload
from pipeline.raster_inputs import (
    align_to_reference,
    dn_to_reflectance,
    inspect_asset,
    report_for_manifest,
)


def _write_raster(path: Path, data: np.ndarray, *, transform=None, crs="EPSG:32643", nodata=255) -> None:
    transform = transform or from_origin(300000, 2050000, 10, 10)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        count=data.shape[0],
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dataset:
        dataset.write(data)


def test_dn_conversion_uses_offset_and_clips_reflectance() -> None:
    result = dn_to_reflectance(np.array([-1000, 0, 10000, 20000]), -1000)
    np.testing.assert_allclose(result, [0.0, 0.0, 0.9, 1.2])


def test_imd_rainfall_class_boundaries() -> None:
    assert classify_imd_rainfall(2.4) == "VERY_LIGHT"
    assert classify_imd_rainfall(2.5) == "LIGHT"
    assert classify_imd_rainfall(15.6) == "MODERATE"
    assert classify_imd_rainfall(64.5) == "HEAVY"
    assert classify_imd_rainfall(115.6) == "VERY_HEAVY"
    assert classify_imd_rainfall(204.5) == "EXTREMELY_HEAVY"


def test_missing_raster_emits_quality_flag(tmp_path: Path) -> None:
    report = inspect_asset(
        tmp_path,
        {"id": "required", "path": "missing.tif", "required": True, "expected": {"band_count": 1}},
    )
    assert report["status"] == "MISSING"
    assert report["quality_flags"] == ["MISSING_RASTER"]


def test_low_clear_scl_is_flagged_and_grid_can_be_aligned(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    reference = tmp_path / "reference.tif"
    output = tmp_path / "aligned.tif"
    data = np.ones((8, 8, 8), dtype=np.uint8)
    data[7] = np.array([[4] * 8] * 2 + [[9] * 8] * 6, dtype=np.uint8)
    _write_raster(source, data, transform=from_origin(300000, 2050000, 20, 20))
    _write_raster(reference, np.ones((1, 16, 16), dtype=np.uint8))
    asset = {
        "id": "optical",
        "path": "source.tif",
        "expected": {"crs": "EPSG:32643", "resolution_m": 10, "band_count": 8, "scl_band": 8, "min_clear_fraction": 0.4},
    }
    report = inspect_asset(tmp_path, asset)
    assert report["clear_fraction"] == 0.25
    assert "LOW_CLEAR_FRACTION" in report["quality_flags"]
    assert report["status"] == "LOW_QUALITY"
    align_to_reference(source, reference, output, categorical_bands=[8])
    with rasterio.open(output) as aligned, rasterio.open(reference) as reference_grid:
        assert aligned.transform == reference_grid.transform
        assert aligned.width == 16 and aligned.height == 16 and aligned.count == 8


def test_raster_manifest_reports_missing_layers_not_as_ready(tmp_path: Path) -> None:
    manifest = {
        "status": "UNVERIFIED",
        "assets": [{"id": "hand", "path": "hand.tif", "required": True}],
    }
    report = report_for_manifest(manifest, tmp_path)
    assert not report["ready"]
    assert "MISSING_RASTER" in report["quality_flags"]


def test_hazard_json_inputs_validate_and_propagate_synthetic_tag() -> None:
    rain = {
        "source": "synthetic fixture",
        "synthetic": True,
        "provenance": {"product_id": "fixture-v1", "retrieved_at": "2026-11-01", "license_status": "generated"},
        "cells": [{"lat": 18.5, "lon": 73.85, "max_24h_mm": 118.4, "max_24h_date": "2024-07-25", "imd_class": "VERY_HEAVY", "percentile": 99.2, "antecedent_30d_percentile": 91.0}],
    }
    discharge = {
        "source": "synthetic fixture",
        "synthetic": True,
        "provenance": {"product_id": "fixture-v1", "retrieved_at": "2026-11-01", "license_status": "generated"},
        "release_cusecs": 37500,
        "date": "2024-07-25",
        "reach": [[73.8, 18.4], [73.9, 18.5]],
        "reach_buffer_m": 1500,
    }
    assert validate_rain_payload(rain)["status"] == "SYNTHETIC"
    assert validate_discharge_payload(discharge)["status"] == "SYNTHETIC"
    assert rain_cells_with_provenance(rain)[0]["synthetic"] is True


def _parcel(x1: float, y1: float, x2: float, y2: float) -> dict:
    geom_utm = box(x1, y1, x2, y2)
    to_wgs84 = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    geom = transform_geometry(to_wgs84.transform, geom_utm)
    centroid = geom.centroid
    return {"geom_utm": geom_utm, "geom": geom, "centroid_lon": centroid.x, "centroid_lat": centroid.y, "soil_class": "alluvial"}


def _layers(hand_value: float) -> tuple[RasterLayer, RasterLayer]:
    hand = np.full((40, 40), hand_value, dtype=np.float32)
    hand[0, 0] = 0.4  # one low-HAND drainage cell near the reach
    twi = np.full((40, 40), 7.0, dtype=np.float32)
    transform = from_origin(300000, 2050000, 10, 10)
    return RasterLayer(hand, transform, "EPSG:32643", -9999), RasterLayer(twi, transform, "EPSG:32643", -9999)


def _discharge(reach_x: float, reach_buffer_m: float) -> dict:
    to_wgs84 = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    start = to_wgs84.transform(reach_x, 2049800)
    end = to_wgs84.transform(reach_x, 2050000)
    return {
        "release_cusecs": 37500,
        "date": "2024-07-25",
        "reach": [list(start), list(end)],
        "reach_buffer_m": reach_buffer_m,
        "synthetic": True,
    }


def test_hazard_extractor_high_low_moderate_and_separate_context() -> None:
    hand, twi = _layers(1.0)
    parcel_high = _parcel(300020, 2049950, 300040, 2049970)
    high = extract_hazard(
        parcel_high,
        hand,
        twi,
        [{"lat": parcel_high["centroid_lat"], "lon": parcel_high["centroid_lon"], "max_24h_mm": 118.4, "imd_class": "VERY_HEAVY", "percentile": 99.2, "antecedent_30d_percentile": 91.0, "synthetic": True}],
        _discharge(300005, 100),
        [0.5, 0.8, 1.0, 2.0],
    )
    assert high["hazard_context"]["plausibility"] == "HIGH"
    assert "hand_m" in high["hazard_context"] and "twi" in high["hazard_context"]
    assert "damage" not in high["hazard_context"] and "damage_estimate" not in high

    hand_low, twi_low = _layers(15.0)
    parcel_low = _parcel(300250, 2049950, 300270, 2049970)
    low = extract_hazard(
        parcel_low,
        hand_low,
        twi_low,
        [{"lat": parcel_low["centroid_lat"], "lon": parcel_low["centroid_lon"], "max_24h_mm": 20.0, "imd_class": "MODERATE"}],
        _discharge(300005, 20),
        [1.0, 5.0, 15.0],
    )
    assert low["hazard_context"]["plausibility"] == "LOW"

    hand_mid, twi_mid = _layers(8.0)
    parcel_mid = _parcel(300140, 2049950, 300160, 2049970)
    moderate = extract_hazard(
        parcel_mid,
        hand_mid,
        twi_mid,
        [{"lat": parcel_mid["centroid_lat"], "lon": parcel_mid["centroid_lon"], "max_24h_mm": 20.0, "imd_class": "MODERATE"}],
        _discharge(300005, 20),
        [1.0, 8.0, 20.0],
    )
    assert moderate["hazard_context"]["plausibility"] == "MODERATE"


def test_missing_hazard_layers_return_nulls_and_quality_flags() -> None:
    parcel = _parcel(300020, 2049950, 300040, 2049970)
    output = extract_hazard(parcel, None, None, [], None, [])
    assert output["hazard_context"]["hand_m"] is None
    assert output["hazard_context"]["twi"] is None
    assert "HAND_LAYER_MISSING" in output["quality_flags"]
    assert "TWI_LAYER_MISSING" in output["quality_flags"]
    assert "DISCHARGE_DATA_MISSING" in output["quality_flags"]


def test_hazard_persistence_targets_only_hazard_context() -> None:
    class Connection:
        def __init__(self) -> None:
            self.calls = []

        async def execute(self, query, *args):
            self.calls.append((query, args))

    rows = [{
        "case_id": "case-1",
        "quality_flags": ["UNVERIFIED_RAIN_SOURCE"],
        "hazard_context": {
            "rain_24h_max_mm": 20.0,
            "rain_imd_class": "MODERATE",
            "rain_percentile": 75.0,
            "antecedent_30d_percentile": 60.0,
            "discharge_exposure": {"in_reach": False},
            "hand_m": 15.0,
            "twi": 8.0,
            "hand_pctile_in_taluka": 80.0,
            "soil_class": "vertisol",
            "plausibility": "LOW",
        },
    }]
    connection = Connection()
    import asyncio

    asyncio.run(upsert_hazard_context(connection, rows))
    statement = connection.calls[0][0]
    assert "INSERT INTO hazard_context" in statement
    assert "observed_estimates" not in statement
    assert quality_summary(rows)["damage_estimates_modified"] is False
