import asyncio

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from backend.config import config_sha, get_config
from backend.main import app, health
from backend.models import FactorCode, FactorResult, FactorStatus


def test_typed_config_is_cached_frozen_and_hashed() -> None:
    config = get_config()
    assert config.detectors.boundary == 0.33
    assert get_config() is config
    assert len(config_sha()) == 64
    with pytest.raises(ValidationError):
        config.detectors.boundary = 0.4


def test_factor_contract_rejects_unknown_enum_values() -> None:
    factor = FactorResult(
        code=FactorCode.PEER_INCONSISTENCY,
        status=FactorStatus.CANNOT_ASSESS,
        evidence={},
        reason="INSUFFICIENT_PEERS",
    )
    assert factor.reason == "INSUFFICIENT_PEERS"
    with pytest.raises(ValidationError):
        FactorResult(code="UNKNOWN", status="TRIGGERED", evidence={})


def test_openapi_lists_all_nine_contract_endpoints_with_501_stubs() -> None:
    document = app.openapi()
    expected = {
        ("post", "/cases"),
        ("post", "/cases/{case_id}/ground"),
        ("post", "/cases/{case_id}/analyze"),
        ("get", "/cases/{case_id}"),
        ("get", "/cases/{case_id}/report"),
        ("get", "/events/{event_id}/queue"),
        ("get", "/events/{event_id}/fairness"),
        ("post", "/cases/{case_id}/review"),
        ("get", "/audit/verify"),
    }
    actual = {
        (method, path)
        for path, methods in document["paths"].items()
        for method in methods
        if method in {"get", "post"}
    }
    assert expected <= actual
    for method, path in expected:
        assert "501" in document["paths"][path][method]["responses"]


def test_health_response_includes_database_and_config_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    async def healthy_ping() -> bool:
        return True

    monkeypatch.setattr("backend.main.db.ping", healthy_ping)
    response = asyncio.run(health())
    assert response == {"status": "ok", "db": True, "config_sha": config_sha()}


def test_stage_router_stubs_return_owned_by_stage_501() -> None:
    client = TestClient(app)
    cases = client.get("/cases/00000000-0000-0000-0000-000000000001")
    ground = client.post("/cases/00000000-0000-0000-0000-000000000001/ground", json={})
    analyze = client.post("/cases/00000000-0000-0000-0000-000000000001/analyze")
    report = client.get("/cases/00000000-0000-0000-0000-000000000001/report")
    audit = client.get("/audit/verify")
    assert (cases.status_code, cases.json()) == (501, {"detail": "owned by stage 4"})
    assert (ground.status_code, ground.json()) == (501, {"detail": "owned by stage 2"})
    assert (analyze.status_code, analyze.json()) == (501, {"detail": "owned by stage 3"})
    assert (report.status_code, report.json()) == (501, {"detail": "owned by stage 3"})
    assert (audit.status_code, audit.json()) == (501, {"detail": "owned by stage 3"})
