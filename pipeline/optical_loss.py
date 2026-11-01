"""Optical vegetation loss metrics and traceable per-parcel scene summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import math
from typing import Any, Mapping, Sequence

import numpy as np
from pyproj import Transformer
from rasterio.transform import Affine
from rasterio.features import rasterize
from shapely.geometry import Polygon, shape
from shapely.ops import transform as transform_geometry

BAD_SCL_CLASSES = {0, 1, 3, 8, 9, 10}


@dataclass(frozen=True)
class SatelliteResult:
    scene_observations: list[dict[str, Any]]
    observed_estimate: dict[str, Any] | None
    quality_report: dict[str, Any] = field(default_factory=dict)


def spectral_indices(bands: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Compute NDVI, NDRE, NDMI, and NDWI from reflectance arrays."""
    required = {"B03", "B04", "B05", "B08", "B8A", "B11"}
    missing = required - set(bands)
    if missing:
        raise ValueError(f"missing spectral bands: {', '.join(sorted(missing))}")

    def index(numerator: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        denominator = left + right
        output = np.full(np.broadcast_shapes(left.shape, right.shape), np.nan, dtype=float)
        valid = np.isfinite(denominator) & (denominator >= 1e-6)
        np.divide(numerator, denominator, out=output, where=valid)
        return output

    b03, b04, b05, b08, b8a, b11 = (
        np.asarray(bands[key], dtype=float)
        for key in ("B03", "B04", "B05", "B08", "B8A", "B11")
    )
    return {
        "NDVI": index(b08 - b04, b08, b04),
        "NDRE": index(b8a - b05, b8a, b05),
        "NDMI": index(b8a - b11, b8a, b11),
        "NDWI": index(b03 - b08, b03, b08),
    }


def scl_valid_mask(scl: np.ndarray) -> np.ndarray:
    values = np.asarray(scl)
    return np.isfinite(values) & ~np.isin(values, list(BAD_SCL_CLASSES))


def _validate_shapes(*arrays: Any) -> tuple[int, ...]:
    shapes = [np.shape(array) for array in arrays if array is not None and np.ndim(array) > 0]
    if not shapes:
        raise ValueError("at least one pixel array is required")
    if any(shape != shapes[0] for shape in shapes[1:]):
        raise ValueError("satellite inputs must have identical shapes")
    return shapes[0]


def _farm_deficit(
    ndvi_obs: np.ndarray,
    ndvi_exp: np.ndarray,
    ndvi_bare: np.ndarray | float,
    weights: np.ndarray,
    valid: np.ndarray | None = None,
    *,
    pixel_clip: bool = False,
    denom_floor: float = 0.05,
) -> tuple[float, np.ndarray, np.ndarray] | None:
    shape = _validate_shapes(ndvi_obs, ndvi_exp, weights)
    obs = np.asarray(ndvi_obs, dtype=float)
    exp = np.asarray(ndvi_exp, dtype=float)
    bare = np.broadcast_to(np.asarray(ndvi_bare, dtype=float), shape)
    weight = np.asarray(weights, dtype=float)
    mask = (
        np.isfinite(obs)
        & np.isfinite(exp)
        & np.isfinite(bare)
        & np.isfinite(weight)
        & (weight > 0)
    )
    if valid is not None:
        mask &= np.broadcast_to(np.asarray(valid, dtype=bool), shape)
    if not np.any(mask):
        return None
    denominator = np.maximum(exp - bare, denom_floor)
    deficits = np.full(shape, np.nan, dtype=float)
    deficits[mask] = (exp[mask] - obs[mask]) / denominator[mask]
    if pixel_clip:
        deficits[mask] = np.clip(deficits[mask], 0.0, 1.0)
    total_weight = float(weight[mask].sum())
    if total_weight <= 0:
        return None
    return float(np.sum(weight[mask] * deficits[mask]) / total_weight), deficits, mask


def compute_satellite_loss(
    ndvi_obs: np.ndarray,
    ndvi_exp: np.ndarray,
    ndvi_bare: np.ndarray | float,
    weights: np.ndarray,
    ctrl_deficits: Sequence[float] | np.ndarray = (),
    dmg_threshold: float = 0.35,
    denom_floor: float = 0.05,
    valid: np.ndarray | None = None,
    *,
    mode: str = "v3",
) -> dict[str, Any] | None:
    """Compute parcel loss using unclipped DiD; v2 is retained for ablation only."""
    shape = _validate_shapes(ndvi_obs, ndvi_exp, weights)
    if np.any(np.asarray(weights, dtype=float) < 0):
        raise ValueError("weights must be non-negative")
    if valid is not None and np.shape(valid) != shape:
        raise ValueError("valid mask must have the same shape as pixel arrays")
    if mode not in {"v2", "v3"}:
        raise ValueError("mode must be 'v2' or 'v3'")
    if denom_floor <= 0:
        raise ValueError("denom_floor must be positive")
    result = _farm_deficit(
        ndvi_obs,
        ndvi_exp,
        ndvi_bare,
        weights,
        valid,
        pixel_clip=mode == "v2",
        denom_floor=denom_floor,
    )
    if result is None:
        return None
    farm_deficit, pixel_deficit, mask = result
    controls = np.asarray(ctrl_deficits, dtype=float)
    controls = controls[np.isfinite(controls)]
    if mode == "v2":
        controls = np.clip(controls, 0.0, 1.0)
    control_median = float(np.nanmedian(controls)) if controls.size else 0.0
    weight = np.asarray(weights, dtype=float)
    selected_weights = weight[mask]
    pixel_attr = pixel_deficit[mask] - control_median
    # V3 subtracts the unclipped control median before the final clip. V2 has
    # already clipped both its pixel deficits and the supplied control values.
    loss_attr = float(np.clip(farm_deficit - control_median, 0.0, 1.0))
    area_dmg = float(
        np.sum(selected_weights * (pixel_attr >= dmg_threshold)) / selected_weights.sum()
    )
    return {
        "deficit_farm": round(farm_deficit, 4),
        "deficit_controls": round(control_median, 4),
        "loss_attr": round(loss_attr, 4),
        "area_dmg_frac": round(area_dmg, 4),
        "v_sat": round(loss_attr if mode == "v2" else max(loss_attr, area_dmg), 4),
        "n_eff": round(float(selected_weights.sum()), 2),
        "_pixel_deficit": pixel_deficit,
        "_valid_mask": mask,
    }


def _weighted_mean(values: Any, weights: np.ndarray, mask: np.ndarray) -> float | None:
    array = np.broadcast_to(np.asarray(values, dtype=float), weights.shape)
    keep = mask & np.isfinite(array) & (weights > 0)
    if not np.any(keep):
        return None
    return float(np.sum(array[keep] * weights[keep]) / np.sum(weights[keep]))


def parcel_window_metrics(
    pixels: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any] | float] = (),
    *,
    mode: str = "v3",
    cfg: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Summarize one optical scene, excluding SCL-invalid and scene-one water pixels."""
    cfg = cfg or {}
    cfg = cfg.get("satellite", cfg)
    ndvi_obs = np.asarray(pixels["ndvi_obs"], dtype=float)
    ndvi_exp = np.asarray(pixels.get("ndvi_exp", pixels.get("ndvi_pre")), dtype=float)
    weights = np.asarray(pixels["weights"], dtype=float)
    shape = _validate_shapes(ndvi_obs, ndvi_exp, weights)
    if np.any(weights < 0):
        raise ValueError("weights must be non-negative")
    base_valid = np.isfinite(ndvi_obs) & np.isfinite(ndvi_exp) & (weights > 0)
    if "scl" in pixels:
        base_valid &= np.broadcast_to(scl_valid_mask(pixels["scl"]), shape)
    if "valid" in pixels:
        base_valid &= np.broadcast_to(np.asarray(pixels["valid"], dtype=bool), shape)
    valid_weight = float(weights[base_valid].sum())
    total_weight = float(weights[np.isfinite(weights) & (weights > 0)].sum())
    clear_fraction = valid_weight / total_weight if total_weight else 0.0
    water_values = np.asarray(pixels.get("water", np.zeros(shape, dtype=bool)), dtype=bool)
    water = np.broadcast_to(water_values, shape)
    water_fraction = (
        float(weights[base_valid & water].sum() / valid_weight) if valid_weight else 0.0
    )
    deficit_valid = base_valid & ~water
    control_values: list[float] = []
    for control in controls:
        if isinstance(control, Mapping):
            control_result = _farm_deficit(
                np.asarray(control["ndvi_obs"], dtype=float),
                np.asarray(control.get("ndvi_exp", control.get("ndvi_pre")), dtype=float),
                control.get(
                    "ndvi_bare",
                    pixels.get("ndvi_bare", cfg.get("bare_ndvi_default", 0.12)),
                ),
                np.asarray(control.get("weights", weights), dtype=float),
                _control_valid_mask(control),
                pixel_clip=mode == "v2",
                denom_floor=float(cfg.get("denom_floor", 0.05)),
            )
            if control_result is not None:
                control_values.append(control_result[0])
        elif np.isfinite(float(control)):
            control_values.append(float(control))
    metrics = compute_satellite_loss(
        ndvi_obs,
        ndvi_exp,
        pixels.get("ndvi_bare", cfg.get("bare_ndvi_default", 0.12)),
        weights,
        control_values,
        float(cfg.get("damaged_area_pixel_threshold", 0.35)),
        float(cfg.get("denom_floor", 0.05)),
        deficit_valid,
        mode=mode,
    )
    if metrics is None:
        return None
    metrics.update(
        {
            "clear_frac": clear_fraction,
            "water_frac_optical": water_fraction,
            "ndvi_obs": _weighted_mean(ndvi_obs, weights, base_valid),
            "ndvi_exp": _weighted_mean(ndvi_exp, weights, base_valid),
            "ndvi_bare": _weighted_mean(
                pixels.get("ndvi_bare", cfg.get("bare_ndvi_default", 0.12)),
                weights,
                base_valid,
            ),
            "ndre_obs": _weighted_mean(
                pixels.get("ndre_obs", np.full(shape, np.nan)), weights, base_valid
            ),
            "ndmi_obs": _weighted_mean(
                pixels.get("ndmi_obs", np.full(shape, np.nan)), weights, base_valid
            ),
            "_deficit_valid": deficit_valid,
            "_weights": weights,
            "_control_deficits": np.asarray(control_values, dtype=float),
        }
    )
    return metrics


def _control_valid_mask(control: Mapping[str, Any]) -> np.ndarray | None:
    mask = None
    if "scl" in control:
        mask = scl_valid_mask(control["scl"])
    if "valid" in control:
        valid = np.asarray(control["valid"], dtype=bool)
        mask = valid if mask is None else mask & valid
    return mask


def _blocks(shape: tuple[int, int], size: int) -> list[tuple[slice, slice]]:
    rows, cols = shape
    return [
        (slice(row, min(row + size, rows)), slice(col, min(col + size, cols)))
        for row in range(0, rows, size)
        for col in range(0, cols, size)
    ]


def bootstrap_sigma(
    pixel_deficit: np.ndarray,
    weights: np.ndarray,
    valid: np.ndarray,
    control_median: float,
    *,
    block_size: int = 3,
    n_boot: int = 2000,
    sigma_floor: float = 0.05,
    dmg_threshold: float = 0.35,
) -> dict[str, Any]:
    """Block-bootstrap V_sat, retaining partial edge blocks and a fixed control median."""
    deficit = np.asarray(pixel_deficit, dtype=float)
    weight = np.asarray(weights, dtype=float)
    mask = np.asarray(valid, dtype=bool)
    if deficit.shape != weight.shape or deficit.shape != mask.shape:
        raise ValueError("bootstrap arrays must have identical shapes")
    if block_size < 1 or n_boot < 1:
        raise ValueError("block_size and n_boot must be positive")
    blocks = _blocks(deficit.shape, block_size)
    usable = [
        block for block in blocks
        if np.any(mask[block] & np.isfinite(deficit[block]) & (weight[block] > 0))
    ]
    if len(usable) < 4:
        return {"sigma": 0.10, "ci_lo": None, "ci_hi": None,
                "quality_flags": ["SMALL_PARCEL_LIMITATION"], "blocks": len(usable)}
    rng = np.random.default_rng(42)
    estimates = np.empty(n_boot, dtype=float)
    for index in range(n_boot):
        chosen = rng.integers(0, len(usable), size=len(usable))
        values: list[np.ndarray] = []
        weights_for_sample: list[np.ndarray] = []
        for block_index in chosen:
            block = usable[int(block_index)]
            block_mask = mask[block] & np.isfinite(deficit[block]) & (weight[block] > 0)
            values.append(deficit[block][block_mask])
            weights_for_sample.append(weight[block][block_mask])
        sampled = np.concatenate(values)
        sampled_weights = np.concatenate(weights_for_sample)
        loss = float(np.clip(
            np.sum(sampled_weights * sampled) / sampled_weights.sum() - control_median,
            0.0,
            1.0,
        ))
        damaged = float(np.sum(sampled_weights * (sampled - control_median >= dmg_threshold))
                        / sampled_weights.sum())
        estimates[index] = max(loss, damaged)
    ci_lo, ci_hi = (float(value) for value in np.percentile(estimates, [10, 90]))
    sigma = max((ci_hi - ci_lo) / 2.56, sigma_floor)
    return {"sigma": sigma, "ci_lo": ci_lo, "ci_hi": ci_hi,
            "quality_flags": [], "blocks": len(usable)}


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _date_key(scene: Mapping[str, Any]) -> date:
    return _as_date(scene["date"])


def _prepare_scene(
    scene: Mapping[str, Any],
    window_id: int,
    cfg: Mapping[str, Any],
    mode: str,
    parcel_row: Mapping[str, Any],
) -> dict[str, Any]:
    prepared = dict(scene)
    parcel_stack = prepared.pop("parcel_stack", None)
    if parcel_stack is not None:
        if not isinstance(parcel_stack, Mapping) or "weights" not in parcel_stack:
            raise ValueError("parcel_stack must be a parcel_prep pixel stack with weights")
        stack_weights = np.asarray(parcel_stack["weights"], dtype=float)
        if "weights" in prepared and not np.array_equal(
            np.asarray(prepared["weights"], dtype=float), stack_weights
        ):
            raise ValueError("scene weights conflict with parcel_stack weights")
        prepared["weights"] = stack_weights
        prepared.setdefault("transform", parcel_stack.get("transform"))
        stack_arrays = parcel_stack.get("arrays")
        if "bands" not in prepared and isinstance(stack_arrays, Mapping):
            required_bands = {"B03", "B04", "B05", "B08", "B8A", "B11"}
            if required_bands.issubset(stack_arrays):
                prepared["bands"] = stack_arrays
    if "ndvi_exp" not in prepared and "ndvi_pre" in prepared:
        prepared["ndvi_exp"] = prepared["ndvi_pre"]
    if "bands" in prepared:
        indices = spectral_indices(prepared["bands"])
        prepared.setdefault("ndvi_obs", indices["NDVI"])
        prepared.setdefault("ndre_obs", indices["NDRE"])
        prepared.setdefault("ndmi_obs", indices["NDMI"])
        prepared.setdefault("ndwi_obs", indices["NDWI"])
    water_status_available = "water" in prepared or "ndwi_obs" in prepared
    if "water" not in prepared and "ndwi_obs" in prepared:
        prepared["water"] = np.asarray(prepared["ndwi_obs"], dtype=float) > float(
            cfg.get("standing_water_ndwi", 0.05)
        )
    elif "water" not in prepared:
        # Without a water mask, do not turn potentially submerged pixels into
        # apparent vegetation loss. The caller will skip this scene and cap
        # the evidence grade if no water-observable scene is available.
        prepared["water"] = np.ones_like(prepared["weights"], dtype=bool)
    prepared["water_status_available"] = water_status_available
    if mode == "v2":
        if "weights_v2" in prepared:
            prepared["weights"] = prepared["weights_v2"]
        elif parcel_row.get("geom_utm") is not None and prepared.get("transform") is not None:
            geom = parcel_row["geom_utm"]
            if isinstance(geom, Mapping):
                geom = shape(geom)
            transform = prepared["transform"]
            if not isinstance(transform, Affine):
                transform = Affine(*transform[:6])
            legacy_buffer = geom.buffer(-10.0)
            prepared["weights"] = (
                np.zeros_like(prepared["weights"], dtype=float)
                if legacy_buffer.is_empty
                else rasterize(
                    [(legacy_buffer, 1)],
                    out_shape=np.shape(prepared["weights"]),
                    transform=transform,
                    fill=0,
                    dtype="float32",
                )
            )
    return prepared


def _make_pixel_grid(
    scene: Mapping[str, Any],
    metrics: Mapping[str, Any],
    control_median: float,
    min_weight: float,
) -> dict[str, Any] | None:
    transform = scene.get("transform")
    if transform is None:
        return None
    if not isinstance(transform, Affine):
        transform = Affine(*transform[:6])
    crs = str(scene.get("crs", "EPSG:32643"))
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    weights = np.asarray(metrics["_weights"], dtype=float)
    mask = np.asarray(metrics["_deficit_valid"], dtype=bool)
    deficits = np.asarray(metrics["_pixel_deficit"], dtype=float)
    overlap = np.asarray(scene.get("overlap_weights", weights), dtype=float)
    features: list[dict[str, Any]] = []
    for row, col in zip(*np.nonzero(mask & (overlap >= min_weight)), strict=True):
        corners = [
            transform * (col, row),
            transform * (col + 1, row),
            transform * (col + 1, row + 1),
            transform * (col, row + 1),
            transform * (col, row),
        ]
        polygon = Polygon(corners)
        wgs = transform_geometry(transformer.transform, polygon)
        coords = [
            [[round(float(x), 6), round(float(y), 6)] for x, y in wgs.exterior.coords]
        ]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "attr_deficit": round(float(deficits[row, col] - control_median), 4),
                    "w": round(float(overlap[row, col]), 4),
                },
                "geometry": {"type": "Polygon", "coordinates": coords},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def compute_parcel_satellite(
    parcel_row: Mapping[str, Any],
    rasters: Sequence[Mapping[str, Any]],
    controls_deficits: Mapping[str, Sequence[float]] | Sequence[float],
    cfg: Mapping[str, Any],
    mode: str = "v3",
) -> SatelliteResult:
    """Select two post-event windows and return scene and satellite estimate contracts."""
    if mode not in {"v2", "v3"}:
        raise ValueError("mode must be 'v2' or 'v3'")
    cfg = cfg.get("satellite", cfg)
    peak_date = _as_date(
        parcel_row.get("peak_date", parcel_row.get("event_peak_date", cfg.get("peak_date")))
    )
    clear_min = float(cfg.get("min_clear_fraction", 0.40))
    candidate_scenes = sorted(rasters, key=_date_key)
    window_ranges = {1: (1, 10), 2: (11, 20)}
    selected: dict[int, tuple[Mapping[str, Any], dict[str, Any]]] = {}
    water_status_unavailable = False
    controls_map = controls_deficits if isinstance(controls_deficits, Mapping) else {}
    flat_controls = [] if isinstance(controls_deficits, Mapping) else controls_deficits
    if mode == "v2":
        candidates_by_window = {
            1: [scene for scene in candidate_scenes if _date_key(scene) >= peak_date][:1]
        }
    else:
        candidates_by_window = {
            window_id: [
                scene for scene in candidate_scenes
                if start_day <= (_date_key(scene) - peak_date).days <= end_day
            ]
            for window_id, (start_day, end_day) in window_ranges.items()
        }
    for window_id, candidates in candidates_by_window.items():
        evaluated: list[tuple[float, Mapping[str, Any], dict[str, Any]]] = []
        missing_water_status = False
        for scene in candidates:
            scene_controls = controls_map.get(
                str(scene["date"]), scene.get("controls", flat_controls)
            )
            scene_data = _prepare_scene(scene, window_id, cfg, mode, parcel_row)
            if not scene_data["water_status_available"]:
                missing_water_status = True
                continue
            metrics = parcel_window_metrics(scene_data, scene_controls, mode=mode, cfg=cfg)
            if metrics is not None:
                evaluated.append((float(metrics["clear_frac"]), scene_data, metrics))
        if evaluated:
            _, scene, metrics = max(
                evaluated,
                key=lambda value: (value[0], str(value[1].get("scene_id", ""))),
            )
            selected[window_id] = (scene, metrics)
        elif missing_water_status:
            water_status_unavailable = True

    if not selected:
        flags = ["NO_VALID_OPTICAL_SCENE"]
        if candidate_scenes:
            flags.append("LOW_CLEAR_FRACTION")
        if water_status_unavailable:
            flags.append("WATER_STATUS_UNAVAILABLE")
        return SatelliteResult(
            [],
            None,
            {
                "quality_flags": flags,
                "grade_cap": "C",
                "flags_assessable": False,
            },
        )
    if 2 in selected and selected[2][1]["clear_frac"] >= clear_min:
        used_window = 2
    elif 1 in selected:
        used_window = 1
    else:
        used_window = 2
    final_scene, final_metrics = selected[used_window]
    flags: list[str] = []
    if water_status_unavailable:
        flags.append("WATER_STATUS_UNAVAILABLE")
    if final_metrics["n_eff"] < 8:
        flags.append("SMALL_PARCEL_LIMITATION")
    if final_metrics["clear_frac"] < clear_min:
        flags.append("LOW_CLEAR_FRACTION")
    if selected.get(1) and selected[1][1]["water_frac_optical"] > 0:
        flags.append("STANDING_WATER_AT_SCENE")
    if len(selected) < 2:
        flags.append("FLAGS_NOT_ASSESSABLE_SINGLE_WINDOW")

    if 1 in selected and 2 in selected:
        first = selected[1][1]
        second = selected[2][1]
        if (
            first["loss_attr"] >= float(cfg.get("silt_w1_loss_min", 0.35))
            and first["ndre_obs"] is not None
            and second["ndre_obs"] is not None
            and second["ndre_obs"] - first["ndre_obs"]
            >= float(cfg.get("silt_ndre_rebound_threshold", 0.12))
            and second["loss_attr"] < float(cfg.get("silt_w2_loss_max", 0.25))
        ):
            flags.append("SILT_RECOVERY_OBSERVED")
            used_window = 2
            final_scene, final_metrics = selected[2]
        if (
            first["loss_attr"] < float(cfg.get("rot_w1_loss_max", 0.20))
            and first["ndmi_obs"] is not None
            and second["ndmi_obs"] is not None
            and second["loss_attr"] >= float(cfg.get("rot_w2_loss_min", 0.35))
            and second["ndmi_obs"] - first["ndmi_obs"]
            <= -float(cfg.get("rot_ndmi_drop", 0.15))
            and parcel_row.get("soil_class") == "vertisol"
        ):
            flags.append("DELAYED_WATERLOGGING_ROT")
            used_window = 2
            final_scene, final_metrics = selected[2]

    control_median = float(final_metrics["deficit_controls"])
    block = int(cfg.get("bootstrap_block", 3))
    if mode == "v2":
        bootstrap = {"sigma": 0.10, "ci_lo": None, "ci_hi": None, "quality_flags": []}
    else:
        bootstrap = bootstrap_sigma(
            np.asarray(final_metrics["_pixel_deficit"], dtype=float),
            np.asarray(final_metrics["_weights"], dtype=float),
            np.asarray(final_metrics["_deficit_valid"], dtype=bool),
            control_median,
            block_size=block,
            n_boot=int(cfg.get("bootstrap_n", 2000)),
            sigma_floor=float(cfg.get("sigma_floor", 0.05)),
            dmg_threshold=float(cfg.get("damaged_area_pixel_threshold", 0.35)),
        )
    flags.extend(bootstrap["quality_flags"])
    if final_metrics["n_eff"] < 8 and "SMALL_PARCEL_LIMITATION" not in flags:
        flags.append("SMALL_PARCEL_LIMITATION")

    post_scenes = [scene for scene in candidate_scenes if _date_key(scene) >= peak_date]
    loss_scenes = [
        (scene, metrics)
        for scene, metrics in selected.values()
        if metrics["loss_attr"] >= float(cfg.get("onset_threshold", 0.15))
    ]
    first_scene_with_loss = None
    onset_in_window = None
    if loss_scenes:
        onset_scene, _ = min(loss_scenes, key=lambda item: _date_key(item[0]))
        onset_date = _date_key(onset_scene)
        first_post_date = min((_date_key(scene) for scene in post_scenes), default=None)
        delta = (onset_date - peak_date).days
        onset_days = cfg.get("onset_window_days", [-2, 14])
        first_scene_with_loss = onset_date.isoformat()
        onset_in_window = (
            int(onset_days[0]) <= delta <= int(onset_days[1])
        ) or onset_date == first_post_date

    scene_observations: list[dict[str, Any]] = []
    for window_id, scene_type in ((1, "S2_IMMEDIATE"), (2, "S2_DELAYED")):
        if window_id not in selected:
            continue
        scene, metrics = selected[window_id]
        scene_observations.append(
            {
                "case_id": parcel_row.get("case_id"),
                "scene_date": _date_key(scene).isoformat(),
                "sensor": scene_type,
                "clear_frac": metrics["clear_frac"],
                "n_eff_pixels": metrics["n_eff"],
                "ndvi_obs": metrics["ndvi_obs"],
                "ndvi_exp": metrics["ndvi_exp"],
                "ndvi_bare": metrics["ndvi_bare"],
                "ndre_obs": metrics["ndre_obs"],
                "ndmi_obs": metrics["ndmi_obs"],
                "deficit_farm": metrics["deficit_farm"],
                "deficit_controls": metrics["deficit_controls"],
                "loss_attr": metrics["loss_attr"],
                "area_dmg_frac": metrics["area_dmg_frac"],
                "water_frac": metrics["water_frac_optical"],
            }
        )

    width = parcel_row.get("min_width_m")
    min_weight = float(
        cfg.get("min_overlap_weight_strip", 0.50)
        if width is None or float(width) < 35.0
        else cfg.get("min_overlap_weight_large", 0.65)
    )
    pixel_grid = _make_pixel_grid(final_scene, final_metrics, control_median, min_weight)
    control_values = [
        float(value)
        for value in np.asarray(final_metrics["_control_deficits"], dtype=float)
        if np.isfinite(float(value))
    ]
    quality = {
        "loss_attr": final_metrics["loss_attr"],
        "area_dmg_frac": final_metrics["area_dmg_frac"],
        "n_eff": final_metrics["n_eff"],
        "clear_frac": final_metrics["clear_frac"],
        "water_frac_peak": None,
        "water_frac_recession": None,
        "water_frac_optical": final_metrics["water_frac_optical"],
        "window_used": used_window,
        "flags": sorted(set(flags)),
        "flags_assessable": (
            mode == "v3"
            and len(selected) > 1
            and all(metrics["clear_frac"] >= clear_min for _, metrics in selected.values())
            and not water_status_unavailable
        ),
        "controls_n": len(control_values),
        "controls_deficit_median": final_metrics["deficit_controls"],
        "controls_deficit_range": (
            [round(float(np.min(control_values)), 4), round(float(np.max(control_values)), 4)]
            if control_values else None
        ),
        "onset_in_window": onset_in_window,
        "first_scene_with_loss": first_scene_with_loss,
        "min_width_m": parcel_row.get("min_width_m"),
        "mode": mode,
        "pixel_grid": pixel_grid,
        "grade_cap": "C"
        if {"LOW_CLEAR_FRACTION", "SMALL_PARCEL_LIMITATION", "WATER_STATUS_UNAVAILABLE"} & set(flags)
        else None,
    }
    estimate = {
        "source": "satellite",
        "value": final_metrics["v_sat"],
        "sigma": round(float(bootstrap["sigma"]), 4),
        "ci_lo": (
            bootstrap["ci_lo"]
            if bootstrap["ci_lo"] is not None
            else round(max(0.0, final_metrics["v_sat"] - 1.28 * bootstrap["sigma"]), 4)
        ),
        "ci_hi": (
            bootstrap["ci_hi"]
            if bootstrap["ci_hi"] is not None
            else round(min(1.0, final_metrics["v_sat"] + 1.28 * bootstrap["sigma"]), 4)
        ),
        "quality": quality,
    }
    return SatelliteResult(
        scene_observations,
        estimate,
        {
            "quality_flags": sorted(set(flags)),
            "grade_cap": (
                "C"
                if {"LOW_CLEAR_FRACTION", "SMALL_PARCEL_LIMITATION", "WATER_STATUS_UNAVAILABLE"} & set(flags)
                else None
            ),
            "flags_assessable": quality["flags_assessable"],
        },
    )
