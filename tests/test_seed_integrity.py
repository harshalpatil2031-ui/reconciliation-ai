from __future__ import annotations

import numpy as np
import pytest
from affine import Affine
from shapely.geometry import box, mapping

from scripts.generate_seed import generate_seed, render_seed_sql
from scripts.plant_anomalies import plant_anomalies, render_official_sql


def test_seed_generator_is_deterministic_and_matches_parcel_counts() -> None:
    hand = np.zeros((1000, 1000), dtype=float)
    hand[:, 400:700] = 10.0
    hand[:, 700:] = 12.0
    transform = Affine(10, 0, 300000, 0, -10, 2060000)
    first = generate_seed(hand, transform)
    second = generate_seed(hand, transform)
    assert [row["parcel_id"] for row in first] == [row["parcel_id"] for row in second]
    cases = [row for row in first if row["role"] == "case"]
    controls = [row for row in first if row["role"] == "control"]
    assert len(cases) == 300
    assert len(controls) == 150
    assert sum(row["kind"] == "strip" for row in cases) == 80
    assert sum(row["crop"] is None for row in cases) == 75
    assert sum(row["crop"] == "soybean" for row in cases) == 150
    assert sum(row["kind"] == "floodplain" for row in cases) == 120
    assert sum(row["kind"] == "midslope" for row in cases) == 100
    assert all(row["min_width_m"] < 35 for row in cases if row["kind"] == "strip")
    assert all(0.8 <= row["area_ha"] <= 3.0 for row in cases if row["kind"] != "strip")
    geometries = [row["geometry"] for row in first]
    assert all(
        not geometries[i].intersects(geometries[j])
        for i in range(len(geometries))
        for j in range(i + 1, len(geometries))
    )
    assert all(row["hand_m"] >= 8 for row in controls)
    assert "ON CONFLICT (event_id, parcel_id) DO NOTHING" in render_seed_sql(first)


def _measured_cases() -> list[dict]:
    cases = []
    for i in range(15):
        cases.append({"case_id": f"class1-{i}", "v_sat": 0.65, "village": "V1"})
    for i in range(15):
        cases.append({"case_id": f"class2-{i}", "v_sat": 0.40, "village": "V2"})
    for i in range(20):
        geom = box(i * 30, 0, (i + 1) * 30, 30)
        cases.append({"case_id": f"class3-{i}", "v_sat": 0.55, "village": "Riverside",
                      "geom_utm": mapping(geom)})
    for i in range(15):
        cases.append({"case_id": f"class4-{i}", "v_sat": 0.08, "village": "V4"})
    for i in range(15):
        cases.append({"case_id": f"class5-{i}", "v_sat": 0.25, "village": "V5"})
    for i in range(220):
        cases.append({"case_id": f"clean-{i}", "v_sat": 0.80, "village": f"V{i % 12}"})
    return cases


def test_anomaly_manifest_is_deterministic_and_uses_exact_strata() -> None:
    cases = _measured_cases()
    first = plant_anomalies(cases)
    second = plant_anomalies(cases)
    officials, manifest, scenarios = first
    assert first == second
    assert len(officials) == len(manifest["cases"]) == 300
    counts = {class_id: sum(row["class"] == class_id for row in manifest["cases"])
              for class_id in range(6)}
    assert counts == {0: 220, 1: 15, 2: 15, 3: 20, 4: 15, 5: 15}
    class3_ids = {row["case_id"] for row in manifest["cases"] if row["class"] == 3}
    class3_official = [row for row in officials if row["case_id"] in class3_ids]
    assert len({row["assessor_token"] for row in class3_official}) == 1
    assert len({row["assessed_on"] for row in class3_official}) == 1
    assert all(row["damage_lo"] == 0.15 and row["damage_hi"] == 0.25
               for row in class3_official)
    assert sum(row["scenario"] == "HONEST_TIER1" for row in scenarios) == 30
    assert sum(row["scenario"] == "HONEST_TIER2" for row in scenarios) == 20
    assert sum(row["scenario"] == "NEIGHBOR_FRUSTUM" for row in scenarios) == 8
    assert sum(row["scenario"] == "CROPPED_DUPLICATE" for row in scenarios) == 7
    assert sum(row["scenario"] == "SURFING_TIER1" for row in scenarios) == 15
    honest_tier1 = {row["case_id"] for row in scenarios if row["scenario"] == "HONEST_TIER1"}
    assert all(row["dup_source_case_id"] in honest_tier1
               for row in scenarios if row["scenario"] == "CROPPED_DUPLICATE")
    assert len(render_official_sql(officials)) > 1000


def test_missing_measured_anomaly_stratum_fails_without_relaxing_values() -> None:
    cases = _measured_cases()
    for item in cases:
        if item["case_id"].startswith("class4-"):
            item["v_sat"] = 0.5
    with pytest.raises(ValueError, match="do not relax the anomaly strata"):
        plant_anomalies(cases)
