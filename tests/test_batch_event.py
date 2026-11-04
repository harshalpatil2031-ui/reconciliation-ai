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


def _quality_report(ready: bool = True) -> dict:
    return {
        "ready": ready,
        "assets": [
            {"id": scene_id, "status": "VALID", "source": {
                "provenance_status": "VERIFIED", "license_status": "APPROVED"
            }}
            for scene_id in ("S2-1", "S2-2")
        ],
    }


def test_batch_runs_v3_estimator_for_300_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_estimator(parcel, rasters, controls, cfg, mode):
        calls.append(parcel["case_id"])
        assert mode == "v3"
        return SatelliteResult([], {"source": "satellite", "value": 0.42}, {"quality_flags": []})

    monkeypatch.setattr(run_batch_event, "compute_parcel_satellite", fake_estimator)
    result = run_batch_event.run_batch(_payload(), _quality_report())
    assert len(calls) == len(result["cases"]) == 300
    assert result["cases"][0]["v_sat"] == 0.42
    assert result["mode"] == "v3"


def test_batch_refuses_unverified_imagery() -> None:
    payload = _payload()
    payload["image_provenance"]["status"] = "UNVERIFIED"
    with pytest.raises(ValueError, match="verified image_provenance"):
        run_batch_event.run_batch(payload, _quality_report())


def test_batch_requires_quality_report_for_listed_scenes() -> None:
    payload = _payload()
    with pytest.raises(ValueError, match="ready raster_quality_report"):
        run_batch_event.run_batch(payload, _quality_report(ready=False))


def test_batch_requires_license_and_provenance_validation() -> None:
    payload = _payload()
    report = _quality_report()
    report["assets"][0]["source"]["license_status"] = "PENDING"
    with pytest.raises(ValueError, match="APPROVED license"):
        run_batch_event.run_batch(payload, report)


def test_batch_requires_exact_case_count() -> None:
    with pytest.raises(ValueError, match="exactly 300"):
        run_batch_event.run_batch(_payload(count=299), _quality_report())
