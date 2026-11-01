"""Parcel geometry, fractional pixel weights, spectral clusters, and controls."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
import json
import math
from typing import Any
from uuid import UUID

import numpy as np
from affine import Affine
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from shapely.geometry import shape
from shapely.ops import transform as transform_geometry
from sklearn.cluster import KMeans


def _parcel_settings(cfg: Any = None) -> dict[str, Any]:
    if cfg is None:
        return {"min_width_for_buffer_m": 35.0, "adaptive_buffer_m": 5.0,
                "min_overlap_weight_large": 0.65, "min_overlap_weight_strip": 0.50,
                "min_eff_pixels": 8.0, "high_reliability_eff_pixels": 25.0,
                "supersample": 5}
    settings = getattr(cfg, "parcel", cfg)
    if isinstance(settings, Mapping):
        return dict(settings)
    return {name: getattr(settings, name) for name in (
        "min_width_for_buffer_m", "adaptive_buffer_m", "min_overlap_weight_large",
        "min_overlap_weight_strip", "min_eff_pixels", "high_reliability_eff_pixels",
        "supersample") if hasattr(settings, name)}


def _db_uuid(value: Any) -> Any:
    return UUID(value) if isinstance(value, str) else value


def minimum_width_m(parcel_utm: Any) -> float:
    """Return the shorter side of the parcel's minimum rotated rectangle."""
    geom = shape(parcel_utm) if isinstance(parcel_utm, Mapping) else parcel_utm
    if geom.is_empty or not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty:
        raise ValueError("parcel geometry must have positive area")
    coords = list(geom.minimum_rotated_rectangle.exterior.coords)
    lengths = [math.dist(coords[i], coords[i + 1]) for i in range(4)]
    positive = sorted((length for length in lengths if length > 1e-8))
    if len(positive) < 2:
        raise ValueError("parcel geometry must have positive area")
    return float(positive[0])


def compute_subpixel_weights(
    parcel_utm: Any,
    window_transform: Affine,
    out_shape: tuple[int, int],
    cfg: Any = None,
) -> tuple[np.ndarray, float]:
    """Supersample pixel/parcel intersection; preserve narrow strips unbuffered."""
    settings = _parcel_settings(cfg)
    factor = int(settings.get("supersample", 5))
    if factor < 1 or len(out_shape) != 2 or min(out_shape) < 1:
        raise ValueError("supersample and output dimensions must be positive")
    geom = shape(parcel_utm) if isinstance(parcel_utm, Mapping) else parcel_utm
    if geom.is_empty or not geom.is_valid:
        geom = geom.buffer(0)
    if geom.is_empty:
        raise ValueError("parcel geometry must have positive area")
    width = minimum_width_m(geom)
    threshold = (float(settings.get("min_overlap_weight_large", 0.65))
                 if width >= float(settings.get("min_width_for_buffer_m", 35.0))
                 else float(settings.get("min_overlap_weight_strip", 0.50)))
    if width >= float(settings.get("min_width_for_buffer_m", 35.0)):
        interior = geom.buffer(-float(settings.get("adaptive_buffer_m", 5.0)))
        if not interior.is_empty:
            geom = interior

    rows, cols = out_shape
    high_shape = (rows * factor, cols * factor)
    high_transform = window_transform * Affine.scale(1 / factor, 1 / factor)
    coverage = rasterize(
        [(geom, 1)], out_shape=high_shape, transform=high_transform,
        fill=0, all_touched=False, dtype="uint8",
    ).reshape(rows, factor, cols, factor).mean(axis=(1, 3))
    retained = coverage >= threshold
    weights = np.where(retained, coverage if width >= float(
        settings.get("min_width_for_buffer_m", 35.0)) else coverage**2, 0.0)
    return weights.astype(np.float32), width


def effective_pixels(weights: np.ndarray) -> float:
    values = np.asarray(weights, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values < 0):
        raise ValueError("pixel weights must be finite and non-negative")
    return float(values.sum())


def reliability(n_eff: float, cfg: Any = None) -> str:
    settings = _parcel_settings(cfg)
    if n_eff >= float(settings.get("high_reliability_eff_pixels", 25.0)):
        return "HIGH"
    if n_eff >= float(settings.get("min_eff_pixels", 8.0)):
        return "MEDIUM"
    return "LOW"


def assign_spectral_clusters(
    ndvi_series_by_parcel: Mapping[str, Sequence[float]],
    ndmi_last_by_parcel: Mapping[str, float],
    taluka_of_parcel: Mapping[str, str],
) -> dict[str, int]:
    """Fit deterministic per-taluka k-means labels over pre-event spectral curves."""
    parcels = sorted(taluka_of_parcel)
    by_taluka: dict[str, list[str]] = {}
    for parcel_id in parcels:
        by_taluka.setdefault(str(taluka_of_parcel[parcel_id]), []).append(parcel_id)
    labels: dict[str, int] = {}
    for ids in by_taluka.values():
        if len(ids) == 1:
            labels[ids[0]] = 0
            continue
        width = max((len(ndvi_series_by_parcel.get(pid, ())) for pid in ids), default=0)
        if width == 0:
            raise ValueError("at least one pre-event NDVI observation is required per taluka")
        matrix = np.full((len(ids), width + 1), np.nan, dtype=float)
        for row, pid in enumerate(ids):
            series = np.asarray(ndvi_series_by_parcel.get(pid, ()), dtype=float).ravel()
            matrix[row, :min(width, series.size)] = series[:width]
            value = ndmi_last_by_parcel.get(pid)
            if value is not None:
                matrix[row, -1] = float(value)
        medians = np.nanmedian(matrix, axis=0)
        medians[~np.isfinite(medians)] = 0.0
        missing = ~np.isfinite(matrix)
        matrix[missing] = np.broadcast_to(medians, matrix.shape)[missing]
        means = matrix.mean(axis=0)
        scales = matrix.std(axis=0)
        scales[scales < 1e-12] = 1.0
        standardized = (matrix - means) / scales
        # Keep cohorts large enough to contain peers. Using k == len(ids)
        # assigns every parcel its own label and makes spectral matching useless.
        k = min(6, max(1, len(ids) // 2))
        assigned = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(standardized)
        labels.update({pid: int(label) for pid, label in zip(ids, assigned, strict=True)})
    return labels


async def persist_spectral_clusters(connection: Any, labels: Mapping[str, int]) -> None:
    """Persist labels for every supplied parcel using an asyncpg connection."""
    if not labels:
        return
    await connection.executemany(
        "UPDATE parcels SET spectral_cluster = $1 WHERE parcel_id = $2",
        [(int(cluster), _db_uuid(parcel_id)) for parcel_id, cluster in labels.items()],
    )


async def persist_parcel_weights(
    connection: Any,
    *,
    case_id: str,
    sensor: str,
    scene_date: date | str,
    parcel_id: str,
    stack: Mapping[str, Any],
) -> None:
    """Store sparse sub-pixel weights and n_eff on the matching scene observation."""
    weights = np.asarray(stack["weights"], dtype=float)
    if weights.ndim != 2 or np.any(~np.isfinite(weights)) or np.any(weights < 0):
        raise ValueError("weights must be a finite, non-negative 2D array")
    rows, cols = np.nonzero(weights)
    payload = {
        "shape": list(weights.shape),
        "transform": list(stack["transform"])[:6],
        "weights": [[int(row), int(col), round(float(weights[row, col]), 6)]
                    for row, col in zip(rows, cols, strict=True)],
    }
    result = await connection.execute(
        "UPDATE scene_observations SET pixel_weights = $1::jsonb, n_eff_pixels = $2 "
        "WHERE case_id = $3 AND sensor = $4 AND scene_date = $5",
        json.dumps(payload, separators=(",", ":")),
        effective_pixels(weights), _db_uuid(case_id), sensor, _date(scene_date),
    )
    if result == "UPDATE 0":
        raise ValueError("scene observation must exist before parcel weights are persisted")
    await connection.execute(
        "UPDATE parcels SET min_width_m = $1 WHERE parcel_id = $2",
        float(stack["min_width_m"]), _db_uuid(parcel_id),
    )


def _date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _point(parcel: Mapping[str, Any]) -> tuple[float, float] | None:
    if parcel.get("centroid_lon") is not None and parcel.get("centroid_lat") is not None:
        return float(parcel["centroid_lon"]), float(parcel["centroid_lat"])
    geom = parcel.get("geom")
    if geom is None:
        return None
    geom = shape(geom) if isinstance(geom, Mapping) else geom
    if parcel.get("geom_utm") is not None and geom is parcel.get("geom_utm"):
        # For projected geometries, callers should supply the WGS84 centroid fields.
        return None
    centroid = geom.centroid
    return float(centroid.x), float(centroid.y)


def _distance_km(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    pa, pb = _point(a), _point(b)
    if pa is None or pb is None:
        return math.inf
    lon1, lat1, lon2, lat2 = map(math.radians, (*pa, *pb))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(hav)))


def select_controls(
    parcel_row: Mapping[str, Any],
    all_parcels: Sequence[Mapping[str, Any]],
    sar_water_frac_by_parcel: Mapping[str, float],
    hand_by_parcel: Mapping[str, float],
    cfg: Any,
) -> list[str]:
    """Choose nearby upland/non-flooded controls with crop-date or spectral matching."""
    settings = getattr(cfg, "controls", cfg.get("controls", {}) if isinstance(cfg, Mapping) else {})
    if isinstance(settings, Mapping):
        radius_pair = settings.get("radius_km", (10.0, 25.0))
        min_controls = int(settings.get("min_controls", 5))
        min_hand = float(settings.get("min_hand_m", 8.0))
        max_water = float(settings.get("max_sar_water_frac", 0.02))
    else:
        radius_pair = settings.radius_km
        min_controls = int(settings.min_controls)
        min_hand = float(settings.min_hand_m)
        max_water = float(settings.max_sar_water_frac)
    pid = str(parcel_row.get("parcel_id", parcel_row.get("case_id", "")))
    source_crop, source_sown = parcel_row.get("crop"), _date(parcel_row.get("sowing_date"))
    candidates: list[tuple[float, str]] = []
    for candidate in all_parcels:
        candidate_id = str(candidate.get("parcel_id", candidate.get("case_id", "")))
        if not candidate_id or candidate_id == pid:
            continue
        if source_crop is None or source_sown is None:
            if (
                parcel_row.get("spectral_cluster") is None
                or candidate.get("spectral_cluster") != parcel_row.get("spectral_cluster")
            ):
                continue
        else:
            candidate_sown = _date(candidate.get("sowing_date"))
            if (
                candidate.get("crop") != source_crop
                or candidate_sown is None
                or abs((candidate_sown - source_sown).days) > 10
            ):
                continue
        # Explicitly tagged controls must still pass the same upland and
        # non-flooded checks as automatically discovered control candidates.
        is_upland = (
            float(hand_by_parcel.get(candidate_id, -math.inf)) >= min_hand
            and float(sar_water_frac_by_parcel.get(candidate_id, math.inf)) <= max_water
        )
        if not is_upland:
            continue
        distance = _distance_km(parcel_row, candidate)
        if math.isfinite(distance):
            candidates.append((distance, candidate_id))
    candidates.sort()
    for radius in radius_pair:
        selected = [
            candidate_id for distance, candidate_id in candidates if distance <= float(radius)
        ]
        if len(selected) >= min_controls:
            return selected
    return [
        candidate_id
        for distance, candidate_id in candidates
        if distance <= float(radius_pair[-1])
    ]


def compute_pixel_stack(
    parcel_utm: Any,
    rasters: Mapping[str, Any],
    window: Any = None,
    cfg: Any = None,
) -> dict[str, Any]:
    """Read aligned raster bands in a snapped, one-pixel-padded parcel window."""
    if not rasters:
        raise ValueError("at least one raster dataset is required")
    datasets = {name: value for name, value in rasters.items()}
    first = next(iter(datasets.values()))
    transform = first.transform
    crs = first.crs
    for dataset in datasets.values():
        if dataset.transform != transform or dataset.crs != crs:
            raise ValueError("raster bands must share an aligned grid and CRS")
    geom = shape(parcel_utm) if isinstance(parcel_utm, Mapping) else parcel_utm
    bounds = geom.bounds
    if getattr(crs, "to_epsg", lambda: None)() != 32643:
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:32643", crs, always_xy=True)
        geom = transform_geometry(transformer.transform, geom)
        bounds = geom.bounds
    raw = from_bounds(*bounds, transform=transform)
    row0 = math.floor(raw.row_off) - 1
    col0 = math.floor(raw.col_off) - 1
    row1 = math.ceil(raw.row_off + raw.height) + 1
    col1 = math.ceil(raw.col_off + raw.width) + 1
    read_window = Window(col0, row0, col1-col0, row1-row0)
    out_transform = transform * Affine.translation(col0, row0)
    arrays = {name: dataset.read(1, window=read_window, boundless=True, fill_value=np.nan)
              for name, dataset in datasets.items()}
    shape_out = next(iter(arrays.values())).shape
    if any(values.shape != shape_out for values in arrays.values()):
        raise ValueError("raster bands must share an aligned grid")
    weights, width = compute_subpixel_weights(geom, out_transform, shape_out, cfg)
    return {"arrays": arrays, "weights": weights, "n_eff": effective_pixels(weights),
            "min_width_m": width, "transform": out_transform, "crs": str(crs),
            "window": read_window}
