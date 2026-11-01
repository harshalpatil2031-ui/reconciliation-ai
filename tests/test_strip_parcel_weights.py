from __future__ import annotations

import asyncio
import json

import numpy as np
import pytest
from affine import Affine
from shapely import affinity
from shapely.geometry import box

from pipeline.parcel_prep import (
    assign_spectral_clusters,
    compute_subpixel_weights,
    effective_pixels,
    reliability,
    persist_parcel_weights,
    select_controls,
)


@pytest.mark.parametrize("angle", [0, 17, 45])
def test_narrow_strip_survives_rotated_subpixel_extraction(angle: float) -> None:
    parcel = affinity.rotate(box(0, 0, 22, 320), angle, origin="centroid")
    weights, min_width = compute_subpixel_weights(
        parcel, Affine(10, 0, -100, 0, -10, 500), (80, 80)
    )
    assert min_width == pytest.approx(22.0, abs=0.5)
    assert effective_pixels(weights) >= 18.0
    assert np.any(weights > 0)


def test_large_parcel_uses_interior_buffer_and_width() -> None:
    weights, min_width = compute_subpixel_weights(
        box(0, 0, 60, 60), Affine(10, 0, -10, 0, -10, 70), (8, 8)
    )
    assert min_width == pytest.approx(60.0)
    assert weights.sum() == pytest.approx(25.0, abs=4.0)
    assert np.count_nonzero(weights) < 36


def test_reliability_uses_configured_effective_pixel_bands() -> None:
    assert reliability(25) == "HIGH"
    assert reliability(8) == "MEDIUM"
    assert reliability(7.99) == "LOW"


def test_spectral_clusters_are_deterministic_per_taluka() -> None:
    ndvi = {f"p{i}": [i / 10, i / 20, i / 30, i / 40] for i in range(8)}
    ndmi = {f"p{i}": i / 25 for i in range(8)}
    taluka = {f"p{i}": "A" for i in range(8)}
    assert assign_spectral_clusters(ndvi, ndmi, taluka) == assign_spectral_clusters(
        ndvi, ndmi, taluka
    )


def test_control_selection_matches_crop_date_and_widens_radius() -> None:
    target = {"parcel_id": "case", "role": "case", "crop": "soy",
              "sowing_date": "2024-06-28", "centroid_lon": 73.0, "centroid_lat": 18.0}
    candidates = [
        {"parcel_id": f"c{i}", "role": "control", "crop": "soy",
         "sowing_date": f"2024-07-{day:02d}",
         "centroid_lon": 73.0 + i * 0.005, "centroid_lat": 18.0}
        for i, day in enumerate([1, 2, 3, 4, 5])
    ]
    selected = select_controls(
        target, [target, *candidates], {f"c{i}": 0.0 for i in range(5)},
        {f"c{i}": 10.0 for i in range(5)},
        {"controls": {"radius_km": [10, 25], "min_controls": 5,
                       "min_hand_m": 8, "max_sar_water_frac": 0.02}},
    )
    assert selected == [f"c{i}" for i in range(5)]


def test_persist_parcel_weights_stores_sparse_grid_and_effective_count() -> None:
    class Connection:
        def __init__(self) -> None:
            self.calls = []

        async def execute(self, query, *args):
            self.calls.append((query, args))
            return "UPDATE 1"

    connection = Connection()
    asyncio.run(persist_parcel_weights(
        connection,
        case_id="00000000-0000-0000-0000-000000000001",
        sensor="S2_IMMEDIATE",
        scene_date="2024-08-03",
        parcel_id="00000000-0000-0000-0000-000000000002",
        stack={"weights": np.array([[0.0, 0.5], [0.25, 0.0]]),
               "transform": Affine(10, 0, 0, 0, -10, 20), "min_width_m": 22.0},
    ))
    payload = json.loads(connection.calls[0][1][0])
    assert payload["shape"] == [2, 2]
    assert payload["weights"] == [[0, 1, 0.5], [1, 0, 0.25]]
    assert connection.calls[0][1][1] == pytest.approx(0.75)
    assert "pixel_weights" in connection.calls[0][0]
    assert "min_width_m" in connection.calls[1][0]

