"""Parcel hazard plausibility extraction, kept separate from damage estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from pyproj import CRS, Transformer
from rasterio.features import geometry_mask
from rasterio.transform import xy
from shapely import contains_xy
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform as transform_geometry

HEAVY_CLASSES = {"HEAVY", "VERY_HEAVY", "EXTREMELY_HEAVY"}
LOW_RAIN_CLASSES = {"VERY_LIGHT", "LIGHT", "MODERATE"}
WGS84 = CRS.from_epsg(4326)
UTM_ZONE_43N = CRS.from_epsg(32643)
_TREE_CACHE: dict[tuple[Any, ...], tuple[Any, cKDTree | None]] = {}


@dataclass(frozen=True)
class RasterLayer:
    data: np.ndarray
    transform: Any
    crs: Any
    nodata: float | int | None = None

    @classmethod
    def from_dataset(cls, dataset: Any, band: int = 1) -> "RasterLayer":
        return cls(dataset.read(band, masked=True), dataset.transform, dataset.crs, dataset.nodata)


def classify_imd_rainfall(amount_mm: float | None) -> str | None:
    """Apply IMD 24-hour amount bands from the contract; zero is mapped to very light."""
    if amount_mm is None or not np.isfinite(amount_mm) or amount_mm < 0:
        return None
    if amount_mm <= 2.4:
        return "VERY_LIGHT"
    if amount_mm <= 15.5:
        return "LIGHT"
    if amount_mm <= 64.4:
        return "MODERATE"
    if amount_mm <= 115.5:
        return "HEAVY"
    if amount_mm <= 204.4:
        return "VERY_HEAVY"
    return "EXTREMELY_HEAVY"


def _valid_array(layer: RasterLayer) -> np.ma.MaskedArray:
    values = np.ma.asarray(layer.data, dtype=np.float64)
    data = np.asarray(values.filled(np.nan), dtype=np.float64)
    mask = np.ma.getmaskarray(values) | ~np.isfinite(data)
    if layer.nodata is not None:
        mask |= data == layer.nodata
    return np.ma.array(data, mask=mask)


def _geom_for_layer(parcel_row: Mapping[str, Any], layer: RasterLayer) -> Any:
    projected = CRS.from_user_input(layer.crs).is_projected
    geometry_key = "geom_utm" if projected else "geom"
    geometry = parcel_row.get(geometry_key)
    if geometry is None:
        return None
    if isinstance(geometry, Mapping):
        geometry = shape(geometry)
    source_crs = UTM_ZONE_43N if geometry_key == "geom_utm" else WGS84
    target_crs = CRS.from_user_input(layer.crs)
    if source_crs != target_crs:
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        geometry = transform_geometry(transformer.transform, geometry)
    return geometry


def _weighted_mean(
    layer: RasterLayer,
    parcel_row: Mapping[str, Any],
) -> tuple[float | None, list[str]]:
    geometry = _geom_for_layer(parcel_row, layer)
    values = _valid_array(layer)
    flags: list[str] = []
    if geometry is None:
        return None, ["PARCEL_GEOMETRY_MISSING"]
    inside = geometry_mask(
        [geometry.__geo_interface__],
        out_shape=values.shape,
        transform=layer.transform,
        all_touched=True,
        invert=True,
    )
    valid = ~np.ma.getmaskarray(values)
    mask = inside & valid
    supplied_weights = parcel_row.get("pixel_weights")
    weights = (
        np.ones(values.shape, dtype=float)
        if supplied_weights is None
        else np.asarray(supplied_weights, dtype=float)
    )
    if weights.shape != values.shape:
        return None, ["PIXEL_WEIGHT_SHAPE_MISMATCH"]
    mask &= np.isfinite(weights) & (weights > 0)
    if not mask.any():
        return None, ["NO_VALID_PARCEL_PIXELS"]
    if np.any(inside & ~valid):
        flags.append("RASTER_NODATA_WITHIN_PARCEL")
    selected_weights = weights[mask]
    return float(np.average(np.asarray(values.data)[mask], weights=selected_weights)), flags


def _centroid_wgs84(parcel_row: Mapping[str, Any]) -> tuple[float, float] | None:
    if parcel_row.get("centroid_lon") is not None and parcel_row.get("centroid_lat") is not None:
        return float(parcel_row["centroid_lon"]), float(parcel_row["centroid_lat"])
    geometry = parcel_row.get("geom")
    if geometry is None:
        return None
    if isinstance(geometry, Mapping):
        geometry = shape(geometry)
    centroid = geometry.centroid
    return float(centroid.x), float(centroid.y)


def _nearest_rain_cell(
    lon: float,
    lat: float,
    cells: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    if not cells:
        return None
    # Equirectangular distance is sufficient for selecting nearby cells over a small AOI.
    cos_lat = np.cos(np.deg2rad(lat))
    return min(
        cells,
        key=lambda cell: (
            ((float(cell["lon"]) - lon) * cos_lat) ** 2
            + (float(cell["lat"]) - lat) ** 2
        ),
    )


def _reach_geometry(discharge: Mapping[str, Any]) -> tuple[Any, Any, float] | None:
    line_coords = discharge.get("reach") or discharge.get("reach_geojson")
    if isinstance(line_coords, Mapping):
        line = shape(line_coords)
    elif line_coords:
        line = LineString(line_coords)
    else:
        return None
    transformer = Transformer.from_crs(WGS84, UTM_ZONE_43N, always_xy=True)
    line_utm = transform_geometry(transformer.transform, line)
    buffer_m = float(discharge.get("reach_buffer_m", 1500.0))
    return line_utm, line_utm.buffer(buffer_m), buffer_m


def _low_hand_tree(
    data_identity: int,
    transform_tuple: tuple[float, ...],
    shape_tuple: tuple[int, int],
    reach_key: tuple[Any, ...],
    buffer_m: float,
    _layer: Any,
    _line: Any,
) -> cKDTree | None:
    """Cache spatial index of HAND <= 0.5 m cells within the reported reach buffer."""
    key = (data_identity, transform_tuple, shape_tuple, reach_key, buffer_m)
    if key in _TREE_CACHE:
        cached_data, cached_tree = _TREE_CACHE[key]
        if cached_data is _layer.data:
            return cached_tree
    layer = _layer
    line_utm = _line
    values = _valid_array(layer)
    rows, cols = np.where((~np.ma.getmaskarray(values)) & (np.asarray(values.data) <= 0.5))
    if not len(rows):
        _TREE_CACHE[key] = (_layer.data, None)
        return None
    xs, ys = xy(layer.transform, rows, cols, offset="center")
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if not CRS.from_user_input(layer.crs).equals(UTM_ZONE_43N):
        transformer = Transformer.from_crs(layer.crs, UTM_ZONE_43N, always_xy=True)
        x, y = transformer.transform(x, y)
        x, y = np.asarray(x), np.asarray(y)
    reach_buffer = line_utm.buffer(buffer_m)
    keep = np.asarray(contains_xy(reach_buffer, x, y), dtype=bool)
    points = np.column_stack([x, y])
    if not keep.any():
        _TREE_CACHE[key] = (_layer.data, None)
        return None
    tree = cKDTree(points[keep])
    _TREE_CACHE[key] = (_layer.data, tree)
    if len(_TREE_CACHE) > 8:
        _TREE_CACHE.pop(next(iter(_TREE_CACHE)))
    return tree


def _distance_to_reach(
    parcel_row: Mapping[str, Any],
    hand_layer: RasterLayer,
    discharge: Mapping[str, Any],
) -> tuple[float | None, bool, list[str]]:
    flags: list[str] = []
    reach = _reach_geometry(discharge)
    centroid = _centroid_wgs84(parcel_row)
    if reach is None:
        return None, False, ["DISCHARGE_REACH_MISSING"]
    if centroid is None:
        return None, False, ["PARCEL_CENTROID_MISSING"]
    line_utm, reach_buffer, buffer_m = reach
    to_utm = Transformer.from_crs(WGS84, UTM_ZONE_43N, always_xy=True)
    cx, cy = to_utm.transform(*centroid)
    identity = id(hand_layer.data)
    tree = _low_hand_tree(
        identity,
        tuple(float(v) for v in hand_layer.transform),
        tuple(hand_layer.data.shape),
        tuple(line_utm.coords),
        buffer_m,
        hand_layer,
        line_utm,
    )
    if tree is None:
        flags.append("LOW_HAND_REACH_CELLS_MISSING")
        return None, False, flags
    else:
        distance = float(tree.query([cx, cy])[0])
    return distance, bool(reach_buffer.covers(Point(cx, cy))), flags


def _hand_percentile(value: float | None, taluka_values: Sequence[float]) -> float | None:
    finite = np.asarray([v for v in taluka_values if v is not None and np.isfinite(v)], dtype=float)
    if value is None or not len(finite):
        return None
    return float(100.0 * np.count_nonzero(finite < value) / len(finite))


def _plausibility(
    rain_class: str | None,
    rain_amount: float | None,
    in_reach: bool,
    hand_percentile: float | None,
    heavy_rain_mm: float,
    discharge_hand_percentile_max: float,
    low_plausibility_hand_percentile_min: float,
) -> str:
    if (rain_class in HEAVY_CLASSES) or (rain_amount is not None and rain_amount >= heavy_rain_mm):
        return "HIGH"
    if (
        in_reach
        and hand_percentile is not None
        and hand_percentile <= discharge_hand_percentile_max
    ):
        return "HIGH"
    if (
        rain_class in LOW_RAIN_CLASSES
        and not in_reach
        and hand_percentile is not None
        and hand_percentile >= low_plausibility_hand_percentile_min
    ):
        return "LOW"
    return "MODERATE"


def extract_hazard(
    parcel_row: Mapping[str, Any],
    hand_raster: RasterLayer | None,
    twi_raster: RasterLayer | None,
    rain_cells: Sequence[Mapping[str, Any]],
    discharge: Mapping[str, Any] | None,
    taluka_hand_values: Sequence[float],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Return hazard-context columns plus quality flags; never returns damage metrics."""
    thresholds = thresholds or {}
    flags: list[str] = []
    centroid = _centroid_wgs84(parcel_row)
    if centroid is None:
        flags.append("PARCEL_CENTROID_MISSING")
        rain_cell = None
    else:
        rain_cell = _nearest_rain_cell(*centroid, rain_cells)
        if rain_cell is None:
            flags.append("RAIN_DATA_MISSING")

    try:
        rain_amount = None if rain_cell is None else float(rain_cell.get("max_24h_mm"))
    except (TypeError, ValueError):
        rain_amount = None
        flags.append("RAIN_AMOUNT_INVALID")
    rain_class = None if rain_cell is None else rain_cell.get("imd_class")
    calculated_class = classify_imd_rainfall(rain_amount)
    if rain_class and calculated_class and rain_class != calculated_class:
        flags.append("RAIN_CLASS_MISMATCH")
        rain_class = calculated_class
    elif calculated_class:
        rain_class = calculated_class

    hand_m, hand_flags = (
        (None, ["HAND_LAYER_MISSING"])
        if hand_raster is None
        else _weighted_mean(hand_raster, parcel_row)
    )
    twi, twi_flags = (
        (None, ["TWI_LAYER_MISSING"])
        if twi_raster is None
        else _weighted_mean(twi_raster, parcel_row)
    )
    hand_flags = [
        f"HAND_{flag}" if flag == "RASTER_NODATA_WITHIN_PARCEL" else flag
        for flag in hand_flags
    ]
    twi_flags = [
        f"TWI_{flag}" if flag == "RASTER_NODATA_WITHIN_PARCEL" else flag
        for flag in twi_flags
    ]
    flags.extend(hand_flags)
    flags.extend(twi_flags)
    hand_percentile = _hand_percentile(hand_m, taluka_hand_values)
    if hand_percentile is None:
        flags.append("HAND_PERCENTILE_UNAVAILABLE")

    if discharge is None:
        exposure = None
        distance = None
        in_reach = False
        flags.append("DISCHARGE_DATA_MISSING")
    elif hand_raster is None:
        exposure = {
            "release_cusecs": discharge.get("release_cusecs"),
            "date": discharge.get("date"),
            "distance_to_river_m": None,
            "in_reach": False,
        }
        distance = None
        in_reach = False
        flags.append("HAND_LAYER_MISSING")
    else:
        distance, in_reach, reach_flags = _distance_to_reach(parcel_row, hand_raster, discharge)
        flags.extend(reach_flags)
        exposure = {
            "release_cusecs": discharge.get("release_cusecs"),
            "date": discharge.get("date"),
            "distance_to_river_m": distance,
            "in_reach": in_reach,
        }

    if rain_cell and rain_cell.get("synthetic"):
        flags.append("SYNTHETIC_RAIN_INPUT")
    if rain_cell and rain_cell.get("provenance_status", "UNVERIFIED") != "VERIFIED":
        flags.append("UNVERIFIED_RAIN_SOURCE")
    if discharge and discharge.get("synthetic"):
        flags.append("SYNTHETIC_DISCHARGE_INPUT")
    if discharge and discharge.get("provenance_status", "UNVERIFIED") != "VERIFIED":
        flags.append("UNVERIFIED_DISCHARGE_SOURCE")
    plausibility = _plausibility(
        rain_class,
        rain_amount,
        in_reach,
        hand_percentile,
        float(thresholds.get("heavy_rain_mm", 64.5)),
        float(thresholds.get("discharge_hand_pctile_max", 25.0)),
        float(thresholds.get("low_plausibility_hand_pctile_min", 50.0)),
    )
    return {
        "hazard_context": {
            "rain_24h_max_mm": rain_amount,
            "rain_imd_class": rain_class,
            "rain_percentile": None if rain_cell is None else rain_cell.get("percentile"),
            "antecedent_30d_percentile": (
                None if rain_cell is None else rain_cell.get("antecedent_30d_percentile")
            ),
            "discharge_exposure": exposure,
            "hand_m": hand_m,
            "twi": twi,
            "hand_pctile_in_taluka": hand_percentile,
            "soil_class": parcel_row.get("soil_class"),
            "plausibility": plausibility,
        },
        "quality_flags": sorted(set(flags)),
    }
