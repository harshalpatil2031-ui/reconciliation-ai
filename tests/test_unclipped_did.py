from __future__ import annotations

import numpy as np
import pytest
from rasterio.transform import from_origin

from pipeline.optical_loss import (
    bootstrap_sigma,
    compute_parcel_satellite,
    compute_satellite_loss,
    parcel_window_metrics,
    scl_valid_mask,
    spectral_indices,
)


def _pixels(loss: float, *, shape=(20, 20), ndre=0.2, ndmi=0.3):
    expected = np.full(shape, 0.54, dtype=float)
    bare = np.full(shape, 0.12, dtype=float)
    observed = expected - loss * (expected - bare)
    return {
        "ndvi_exp": expected,
        "ndvi_obs": observed,
        "ndvi_bare": bare,
        "weights": np.ones(shape, dtype=float),
        "ndre_obs": np.full(shape, ndre, dtype=float),
        "ndmi_obs": np.full(shape, ndmi, dtype=float),
        "ndwi_obs": np.full(shape, -0.1, dtype=float),
        "scl": np.full(shape, 4, dtype=np.uint8),
        "transform": from_origin(300000, 2050000, 10, 10),
        "crs": "EPSG:32643",
    }


def test_spectral_indices_guard_small_denominators() -> None:
    bands = {
        "B03": np.array([0.0, 0.3]),
        "B04": np.array([0.0, 0.2]),
        "B05": np.array([0.0, 0.1]),
        "B08": np.array([0.0, 0.6]),
        "B8A": np.array([0.0, 0.4]),
        "B11": np.array([0.0, 0.2]),
    }
    indices = spectral_indices(bands)
    assert np.isnan(indices["NDVI"][0])
    assert indices["NDVI"][1] == pytest.approx(0.5)
    assert indices["NDRE"][1] == pytest.approx(0.6)
    assert indices["NDMI"][1] == pytest.approx(1 / 3)
    assert indices["NDWI"][1] == pytest.approx(-1 / 3)


def test_scl_quality_mask_excludes_cloud_shadow_and_nodata() -> None:
    assert scl_valid_mask(np.array([0, 1, 2, 3, 4, 7, 8, 9, 10, 11])).tolist() == [
        False, False, True, False, True, True, False, False, False, True
    ]


def test_worked_example_uses_unclipped_control_deficit() -> None:
    result = compute_satellite_loss(
        np.array([[0.22]]),
        np.array([[0.54]]),
        0.12,
        np.ones((1, 1)),
        [0.02],
    )
    assert result["deficit_farm"] == pytest.approx(0.762, abs=0.005)
    assert result["deficit_controls"] == pytest.approx(0.02)
    assert result["loss_attr"] == pytest.approx(0.742, abs=0.01)


def test_negative_farm_and_control_deficits_are_subtracted_before_final_clip() -> None:
    result = compute_satellite_loss(
        np.array([[0.582]]),
        np.array([[0.54]]),
        0.12,
        np.ones((1, 1)),
        [-0.2, -0.2, -0.1],
    )
    assert result["deficit_farm"] == pytest.approx(-0.1, abs=0.005)
    assert result["deficit_controls"] == pytest.approx(-0.2)
    assert result["loss_attr"] == pytest.approx(0.1, abs=0.01)


def test_strip_parcel_reports_both_mean_loss_and_damaged_area() -> None:
    expected = np.full(100, 0.54)
    observed = expected.copy()
    observed[:78] = 0.22
    result = compute_satellite_loss(
        observed,
        expected,
        0.12,
        np.ones(100),
        [0.0],
    )
    assert result["area_dmg_frac"] == pytest.approx(0.78)
    assert result["loss_attr"] < result["area_dmg_frac"]
    assert result["v_sat"] == result["area_dmg_frac"]


def test_clear_fraction_and_water_are_separate_from_loss_mask() -> None:
    pixels = _pixels(0.5)
    pixels["water"] = np.zeros((20, 20), dtype=bool)
    pixels["water"][:, :10] = True
    metrics = parcel_window_metrics(pixels)
    assert metrics["clear_frac"] == pytest.approx(1.0)
    assert metrics["water_frac_optical"] == pytest.approx(0.5)
    assert metrics["loss_attr"] == pytest.approx(0.5)


def test_window_trajectory_flags_silt_and_vertisol_rot_only() -> None:
    cfg = {
        "satellite": {
            "bootstrap_n": 100,
            "min_clear_fraction": 0.4,
            "silt_w1_loss_min": 0.35,
            "silt_ndre_rebound_threshold": 0.12,
            "silt_w2_loss_max": 0.25,
            "rot_w1_loss_max": 0.20,
            "rot_w2_loss_min": 0.35,
            "rot_ndmi_drop": 0.15,
        }
    }
    first, second = _pixels(0.5, ndre=0.2), _pixels(0.15, ndre=0.35)
    first.update(date="2024-08-03", scene_id="w1")
    second.update(date="2024-08-13", scene_id="w2")
    silt = compute_parcel_satellite(
        {"peak_date": "2024-07-30", "soil_class": "alluvial"},
        [first, second],
        {"2024-08-03": [0.0], "2024-08-13": [0.0]},
        cfg,
    )
    assert "SILT_RECOVERY_OBSERVED" in silt.observed_estimate["quality"]["flags"]
    assert silt.observed_estimate["quality"]["window_used"] == 2
    assert [row["sensor"] for row in silt.scene_observations] == [
        "S2_IMMEDIATE",
        "S2_DELAYED",
    ]
    assert silt.observed_estimate["quality"]["pixel_grid"]["features"]

    rot_first, rot_second = _pixels(0.1, ndmi=0.5), _pixels(0.4, ndmi=0.3)
    rot_first["date"], rot_second["date"] = "2024-08-03", "2024-08-13"
    vertisol = compute_parcel_satellite(
        {"peak_date": "2024-07-30", "soil_class": "vertisol"},
        [rot_first, rot_second],
        {"2024-08-03": [0.0], "2024-08-13": [0.0]},
        cfg,
    )
    alluvial = compute_parcel_satellite(
        {"peak_date": "2024-07-30", "soil_class": "alluvial"},
        [rot_first, rot_second],
        {"2024-08-03": [0.0], "2024-08-13": [0.0]},
        cfg,
    )
    assert "DELAYED_WATERLOGGING_ROT" in vertisol.observed_estimate["quality"]["flags"]
    assert "DELAYED_WATERLOGGING_ROT" not in alluvial.observed_estimate["quality"]["flags"]


def test_block_bootstrap_is_deterministic_and_keeps_partial_edge_blocks() -> None:
    deficit = np.linspace(-0.1, 0.8, 10 * 11).reshape(10, 11)
    weights = np.ones_like(deficit)
    valid = np.ones_like(deficit, dtype=bool)
    first = bootstrap_sigma(deficit, weights, valid, 0.02, n_boot=100)
    second = bootstrap_sigma(deficit, weights, valid, 0.02, n_boot=100)
    assert first == second
    assert first["blocks"] == 16
    assert first["ci_lo"] is not None and first["ci_hi"] is not None


def test_missing_or_clouded_scenes_return_grade_limited_quality_report() -> None:
    cfg = {"satellite": {"min_clear_fraction": 0.4}}
    empty = compute_parcel_satellite(
        {"peak_date": "2024-07-30"}, [], [], cfg
    )
    assert empty.observed_estimate is None
    assert "NO_VALID_OPTICAL_SCENE" in empty.quality_report["quality_flags"]
    assert empty.quality_report["grade_cap"] == "C"

    cloudy = _pixels(0.5)
    cloudy["date"] = "2024-08-03"
    cloudy["scl"][:] = 9
    no_clear = compute_parcel_satellite(
        {"peak_date": "2024-07-30"},
        [cloudy],
        [],
        cfg,
    )
    assert no_clear.observed_estimate is None
    assert "LOW_CLEAR_FRACTION" in no_clear.quality_report["quality_flags"]
    assert no_clear.quality_report["grade_cap"] == "C"
