"""Gated Sentinel-1 inundation evidence with traceable quality diagnostics.

Thresholds in ``config/defaults.yaml`` are initial settings and need regional
calibration. Otsu is used only after histogram bimodality and Ashman's-D gates.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
import json
from typing import Any
from uuid import UUID

import numpy as np
from scipy.ndimage import gaussian_filter1d, uniform_filter
from scipy.signal import find_peaks


def _sar_settings(cfg: Any = None) -> dict[str, float]:
    defaults = {
        "lee_window": 3,
        "ashman_d_min": 2.0,
        "open_water_vv_drop_db": -2.5,
        "open_water_vh_max_db": -20.0,
        "fallback_vv_drop_db": -3.0,
        "double_bounce_hand_max_m": 4.0,
        "double_bounce_ndvi_pre_min": 0.35,
        "double_bounce_ctrl_excess_db": 2.5,
    }
    if cfg is None:
        return defaults
    settings = getattr(cfg, "sar", cfg)
    if isinstance(settings, Mapping):
        if "sar" in settings and isinstance(settings["sar"], Mapping):
            settings = settings["sar"]
        return {**defaults, **settings}
    return {key: getattr(settings, key, value) for key, value in defaults.items()}


def _as_array(values: Any, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim < 1:
        raise ValueError(f"{name} must be a pixel array")
    return array


def _aligned_arrays(*arrays: Any) -> tuple[np.ndarray, ...]:
    converted = tuple(np.asarray(array, dtype=float) for array in arrays)
    shapes = {array.shape for array in converted}
    if len(shapes) != 1:
        raise ValueError("SAR pixel arrays must have identical shapes")
    return converted


def _looks_estimate(power: np.ndarray) -> float:
    valid = power[np.isfinite(power) & (power > 0)]
    if valid.size < 2:
        return 1.0
    mean = float(np.mean(valid))
    variance = float(np.var(valid))
    if variance <= np.finfo(float).eps:
        return 8.0
    return float(np.clip(mean * mean / variance, 1.0, 8.0))


def lee_filter(db_array: np.ndarray, size: int = 3) -> np.ndarray:
    """Apply a local-statistics Lee filter in linear power, then return dB.

    Equivalent looks are estimated from the finite scene-wide coefficient of
    variation and clamped to 1–8. NaN pixels do not contribute to local moments.
    """
    db = _as_array(db_array, "db_array")
    if db.ndim != 2:
        raise ValueError("Lee filtering expects a 2D raster")
    if size < 1 or size % 2 == 0:
        raise ValueError("Lee filter size must be a positive odd integer")
    valid = np.isfinite(db)
    if not np.any(valid):
        return np.full(db.shape, np.nan, dtype=float)
    safe_power = np.zeros(db.shape, dtype=float)
    np.power(10.0, db / 10.0, out=safe_power, where=valid)
    footprint = float(size * size)
    count = uniform_filter(valid.astype(float), size=size, mode="nearest") * footprint
    local_mean = uniform_filter(safe_power, size=size, mode="nearest") * footprint
    local_second = uniform_filter(safe_power**2, size=size, mode="nearest") * footprint
    np.divide(local_mean, count, out=local_mean, where=count > 0)
    np.divide(local_second, count, out=local_second, where=count > 0)
    local_variance = np.maximum(local_second - local_mean**2, 0.0)
    looks = _looks_estimate(safe_power[valid])
    noise_variance = local_mean**2 / looks
    weight = np.zeros(db.shape, dtype=float)
    np.divide(
        np.maximum(local_variance - noise_variance, 0.0),
        local_variance,
        out=weight,
        where=local_variance > 0,
    )
    filtered = local_mean + weight * (safe_power - local_mean)
    result = np.full(db.shape, np.nan, dtype=float)
    good = valid & np.isfinite(filtered) & (filtered > 0)
    result[good] = 10.0 * np.log10(filtered[good])
    return result


def _otsu_threshold(values: np.ndarray) -> float:
    """NumPy-only Otsu threshold for finite values."""
    data = values[np.isfinite(values)]
    if data.size == 0:
        return float("nan")
    low, high = float(data.min()), float(data.max())
    if low == high:
        return low
    histogram, edges = np.histogram(data, bins=256, range=(low, high))
    probabilities = histogram.astype(float) / data.size
    centers = (edges[:-1] + edges[1:]) / 2.0
    cumulative_weight = np.cumsum(probabilities)
    cumulative_mean = np.cumsum(probabilities * centers)
    total_mean = cumulative_mean[-1]
    denominator = cumulative_weight * (1.0 - cumulative_weight)
    between = np.zeros_like(denominator)
    valid = denominator > 0
    between[valid] = (
        (total_mean * cumulative_weight[valid] - cumulative_mean[valid]) ** 2
        / denominator[valid]
    )
    return float(centers[int(np.argmax(between))])


def _histogram_bimodality(values: np.ndarray) -> tuple[bool, int, float | None]:
    """Require two prominent histogram peaks separated by a clear valley.

    Ashman's D calculated after an Otsu split can exceed 2 for a single
    Gaussian mode, so it cannot by itself establish bimodality. Smooth the
    histogram to suppress sampling noise, then require two prominent modes
    with a valley no higher than 80% of the smaller peak.
    """
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data)]
    if data.size < 50:
        return False, 0, None
    low, high = float(data.min()), float(data.max())
    span = high - low
    if span <= 0:
        return False, 0, None
    padding = span * 0.05
    histogram, _ = np.histogram(data, bins=128, range=(low - padding, high + padding))
    smoothed = gaussian_filter1d(histogram.astype(float), sigma=2.0)
    peaks, _ = find_peaks(
        smoothed,
        distance=3,
        prominence=max(float(smoothed.max()) * 0.05, 1.0),
    )
    if peaks.size < 2:
        return False, int(peaks.size), None
    dominant = sorted(
        (int(peak) for peak in peaks),
        key=lambda peak: smoothed[peak],
        reverse=True,
    )[:2]
    left, right = sorted(dominant)
    smaller_peak = min(float(smoothed[left]), float(smoothed[right]))
    valley_ratio = float(np.min(smoothed[left : right + 1]) / smaller_peak)
    return valley_ratio <= 0.80, int(peaks.size), valley_ratio


def ashman_d(vals: np.ndarray, thresh: float) -> float:
    """Return Ashman's D after splitting values at ``thresh``."""
    values = np.asarray(vals, dtype=float)
    values = values[np.isfinite(values)]
    if values.ndim != 1:
        values = values.ravel()
    lower = values[values <= thresh]
    upper = values[values > thresh]
    if lower.size < 10 or upper.size < 10:
        return 0.0
    mean_lower, mean_upper = float(np.mean(lower)), float(np.mean(upper))
    std_lower, std_upper = float(np.std(lower)), float(np.std(upper))
    return float(
        np.sqrt(2.0)
        * abs(mean_lower - mean_upper)
        / np.sqrt(max(std_lower**2 + std_upper**2, 1e-6))
    )


def _weighted_fraction(mask: np.ndarray, valid: np.ndarray, weights: np.ndarray) -> float:
    selected = valid & (weights > 0)
    denominator = float(weights[selected].sum())
    if denominator <= 0:
        return 0.0
    return float(weights[selected & mask].sum() / denominator)


def sar_water_fraction(
    vv_pre_db: np.ndarray,
    vv_post_db: np.ndarray,
    vh_post_db: np.ndarray,
    hand_m: np.ndarray,
    ndvi_pre: np.ndarray,
    ctrl_delta_vv_median: float | None,
    window_delta_vv: np.ndarray,
    cfg: Any = None,
    *,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    """Calculate open-water and double-bounce fractions with quality evidence.

    ``window_delta_vv`` is the filtered ΔVV sample from the 2 km parcel-centred
    neighborhood. A gated Otsu threshold is capped by the physical −2.5 dB
    bound. Unimodal or undersized neighborhoods use the configured −3 dB fallback.
    """
    settings = _sar_settings(cfg)
    vv_pre, vv_post, vh_post, hand, ndvi = _aligned_arrays(
        vv_pre_db, vv_post_db, vh_post_db, hand_m, ndvi_pre
    )
    weight = np.ones(vv_pre.shape, dtype=float) if weights is None else np.asarray(
        weights, dtype=float
    )
    if weight.shape != vv_pre.shape:
        raise ValueError("weights must have the same shape as parcel SAR arrays")
    if np.any(np.isfinite(weight) & (weight < 0)):
        raise ValueError("weights must be non-negative")
    neighborhood = _as_array(window_delta_vv, "window_delta_vv")
    if neighborhood.ndim != 2:
        neighborhood = neighborhood.ravel()
    neighborhood = neighborhood[np.isfinite(neighborhood)]
    flags: list[str] = []
    otsu_threshold = None
    d_value = 0.0
    bimodal = False
    peak_count = 0
    valley_ratio = None
    minimum = float(settings["ashman_d_min"])
    if neighborhood.size >= 50:
        otsu_threshold = _otsu_threshold(neighborhood)
        d_value = ashman_d(neighborhood, otsu_threshold)
        bimodal, peak_count, valley_ratio = _histogram_bimodality(neighborhood)
    else:
        flags.append("SAR_WINDOW_TOO_SMALL")

    if otsu_threshold is not None and bimodal and d_value > minimum:
        drop_threshold = min(otsu_threshold, float(settings["open_water_vv_drop_db"]))
        threshold_method = "ASHMAN_GATED_OTSU"
    else:
        drop_threshold = float(settings["fallback_vv_drop_db"])
        threshold_method = "FIXED_FALLBACK"
        flags.append("SAR_UNIMODAL_FALLBACK")

    delta_vv = lee_filter(vv_post, int(settings["lee_window"])) - lee_filter(
        vv_pre, int(settings["lee_window"])
    )
    valid = (
        np.isfinite(delta_vv)
        & np.isfinite(vh_post)
        & np.isfinite(hand)
        & np.isfinite(ndvi)
        & np.isfinite(weight)
        & (weight > 0)
    )
    if not np.any(valid):
        flags.append("NO_VALID_SAR_PIXELS")
    open_water = (
        (delta_vv <= drop_threshold)
        & (vh_post <= float(settings["open_water_vh_max_db"]))
    )
    if ctrl_delta_vv_median is None or not np.isfinite(ctrl_delta_vv_median):
        double_bounce = np.zeros(vv_pre.shape, dtype=bool)
        flags.append("NO_VALID_CONTROL_DELTA")
    else:
        double_bounce = (
            (hand <= float(settings["double_bounce_hand_max_m"]))
            & (ndvi >= float(settings["double_bounce_ndvi_pre_min"]))
            & (
                delta_vv - float(ctrl_delta_vv_median)
                >= float(settings["double_bounce_ctrl_excess_db"])
            )
        )
    open_fraction = _weighted_fraction(open_water, valid, weight)
    bounce_fraction = _weighted_fraction(double_bounce, valid, weight)
    total_fraction = _weighted_fraction(open_water | double_bounce, valid, weight)
    mean_delta = (
        float(np.average(delta_vv[valid], weights=weight[valid])) if np.any(valid) else None
    )
    return {
        "water_frac": total_fraction,
        "sar_change_db": mean_delta,
        "quality": {
            "open_water_frac": open_fraction,
            "double_bounce_frac": bounce_fraction,
            "ashman_d": round(float(d_value), 4),
            "histogram_peak_count": peak_count,
            "histogram_valley_ratio": (
                round(valley_ratio, 4) if valley_ratio is not None else None
            ),
            "otsu_threshold_db": (
                round(float(otsu_threshold), 4) if otsu_threshold is not None else None
            ),
            "open_water_threshold_db": round(float(drop_threshold), 4),
            "threshold_method": threshold_method,
            "valid_pixels": int(valid.sum()),
            "n_eff": round(float(weight[valid].sum()), 2),
            "flags": sorted(set(flags)),
            "thresholds_status": "INITIAL_UNTUNED",
        },
    }


async def persist_sar_observation(
    connection: Any,
    *,
    case_id: str | UUID,
    scene_date: date,
    result: Mapping[str, Any],
) -> None:
    """Persist per-parcel SAR metrics and diagnostic flags on an existing scene row."""
    quality = result.get("quality")
    if not isinstance(quality, Mapping):
        raise ValueError("SAR result must include a quality mapping")
    normalized_id = UUID(case_id) if isinstance(case_id, str) else case_id
    status = await connection.execute(
        "UPDATE scene_observations SET sar_change_db = $1, water_frac = $2, quality = $3::jsonb "
        "WHERE case_id = $4 AND sensor = 'S1_SAR' AND scene_date = $5",
        result.get("sar_change_db"), float(result["water_frac"]),
        json.dumps(dict(quality), separators=(",", ":")), normalized_id, scene_date,
    )
    if status == "UPDATE 0":
        raise ValueError("S1_SAR scene observation must exist before SAR metrics are persisted")
