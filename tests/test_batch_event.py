from __future__ import annotations

import pytest

from pipeline import run_batch_event
from pipeline.optical_loss import SatelliteResult


def _payload(count: int = 300) -> dict:
    return {
        "event_id": "MH-2024-07-PUNE",
        "image_provenance": {"status": "VERIFIED", "scene_ids": ["S2-1", "S2-2"]},
        "parcels": [
            {"case_id": f"case-{i}", "village": "test", "rasters": [{"date": "2024-08-03"}]}
            for i in range(count)
        ],
    }


def test_batch_runs_v3_estimator_for_300_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_estimator(parcel, rasters, controls, cfg, mode):
        calls.append(parcel["case_id"])
        assert mode == "v3"
        return SatelliteResult([], {"source": "satellite", "value": 0.42}, {"quality_flags": []})

    monkeypatch.setattr(run_batch_event, "compute_parcel_satellite", fake_estimator)
    result = run_batch_event.run_batch(_payload())
    assert len(calls) == len(result["cases"]) == 300
    assert result["cases"][0]["v_sat"] == 0.42
    assert result["mode"] == "v3"


def test_batch_refuses_unverified_imagery() -> None:
    payload = _payload()
    payload["image_provenance"]["status"] = "UNVERIFIED"
    with pytest.raises(ValueError, match="verified image_provenance"):
        run_batch_event.run_batch(payload)


def test_batch_requires_exact_case_count() -> None:
    with pytest.raises(ValueError, match="exactly 300"):
        run_batch_event.run_batch(_payload(count=299))
