from __future__ import annotations

from datetime import date
import json

import numpy as np
import pytest

from pipeline.sar_inundation import (
    ashman_d,
    lee_filter,
    persist_sar_observation,
    sar_water_fraction,
)


def _sar_inputs(delta: np.ndarray, *, hand: float = 10.0, ndvi: float = 0.2):
    shape = delta.shape
    return {
        "vv_pre_db": np.full(shape, -10.0),
        "vv_post_db": -10.0 + delta,
        "vh_post_db": np.full(shape, -22.0),
        "hand_m": np.full(shape, hand),
        "ndvi_pre": np.full(shape, ndvi),
    }


def test_lee_filter_handles_nan_and_preserves_raster_shape() -> None:
    data = np.full((9, 9), -10.0)
    data[4, 4] = -2.0
    data[0, 0] = np.nan
    filtered = lee_filter(data)
    assert filtered.shape == data.shape
    assert np.isnan(filtered[0, 0])
    assert filtered[4, 4] < data[4, 4]


def test_small_unimodal_flood_fraction_uses_fixed_fallback_not_otsu() -> None:
    rng = np.random.default_rng(42)
    window = rng.normal(-0.2, 0.45, size=(50, 50))
    # Ashman's D after a one-threshold split can be high even for one Gaussian
    # mode, so the histogram peak/valley check must reject Otsu here.
    assert ashman_d(window, -0.2) > 2.0
    delta = np.zeros((10, 10))
    delta.flat[:3] = -5.0
    result = sar_water_fraction(
        **_sar_inputs(delta), ctrl_delta_vv_median=0.0, window_delta_vv=window
    )
    quality = result["quality"]
    assert quality["threshold_method"] == "FIXED_FALLBACK"
    assert quality["histogram_peak_count"] < 2
    assert quality["open_water_threshold_db"] == -3.0
    assert "SAR_UNIMODAL_FALLBACK" in quality["flags"]


def test_bimodal_neighborhood_enables_otsu_gated_open_water() -> None:
    window = np.r_[np.full(1250, -5.0), np.full(1250, 0.0)].reshape(50, 50)
    delta = np.r_[np.full(50, -5.0), np.zeros(50)].reshape(10, 10)
    result = sar_water_fraction(
        **_sar_inputs(delta), ctrl_delta_vv_median=0.0, window_delta_vv=window
    )
    quality = result["quality"]
    assert quality["ashman_d"] > 2.0
    assert quality["histogram_peak_count"] >= 2
    assert quality["histogram_valley_ratio"] <= 0.80
    assert quality["threshold_method"] == "ASHMAN_GATED_OTSU"
    assert result["quality"]["open_water_frac"] > 0.35
    assert result["water_frac"] == pytest.approx(result["quality"]["open_water_frac"])


def test_uniform_rain_wetting_does_not_trigger_double_bounce() -> None:
    result = sar_water_fraction(
        **_sar_inputs(np.full((10, 10), 3.0), hand=2.0, ndvi=0.5),
        ctrl_delta_vv_median=3.0,
        window_delta_vv=np.zeros((8, 8)),
    )
    assert result["quality"]["double_bounce_frac"] == 0.0


def test_control_excess_and_low_hand_gate_positive_double_bounce() -> None:
    result = sar_water_fraction(
        **_sar_inputs(np.full((10, 10), 3.0), hand=4.0, ndvi=0.35),
        ctrl_delta_vv_median=0.3,
        window_delta_vv=np.zeros((8, 8)),
    )
    assert result["quality"]["double_bounce_frac"] == 1.0
    assert result["water_frac"] == 1.0


def test_sar_inputs_require_aligned_arrays() -> None:
    with pytest.raises(ValueError, match="identical shapes"):
        sar_water_fraction(
            np.zeros((2, 2)), np.zeros((3, 3)), np.zeros((2, 2)),
            np.zeros((2, 2)), np.zeros((2, 2)), 0.0, np.zeros((10, 10)),
        )


async def test_sar_result_and_quality_are_persisted() -> None:
    class Connection:
        def __init__(self) -> None:
            self.call = None

        async def execute(self, query, *args):
            self.call = (query, args)
            return "UPDATE 1"

    result = {
        "water_frac": 0.25,
        "sar_change_db": -1.2,
        "quality": {"threshold_method": "FIXED_FALLBACK", "flags": ["SAR_UNIMODAL_FALLBACK"]},
    }
    connection = Connection()
    await persist_sar_observation(
        connection,
        case_id="00000000-0000-0000-0000-000000000001",
        scene_date=date(2024, 8, 3),
        result=result,
    )
    assert connection.call is not None
    assert "sensor = 'S1_SAR'" in connection.call[0]
    assert connection.call[1][0:2] == (-1.2, 0.25)
    assert json.loads(connection.call[1][2]) == result["quality"]
