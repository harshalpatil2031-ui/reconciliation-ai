from fastapi.testclient import TestClient

from backend.demo_app import app


def test_local_demo_api_saves_lists_reviews_and_resets_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("RECON_DEMO_DB", str(tmp_path / "demo.sqlite3"))
    payload = {
        "locale": "mr",
        "form": {
            "damaged_share_pct": 70,
            "water_depth_band": "KNEE",
            "water_days": 3,
            "crop_stage": "VEGETATIVE",
            "note": "demo only",
        },
    }
    with TestClient(app) as client:
        cases = client.get("/demo/cases")
        assert cases.status_code == 200
        assert len(cases.json()) == 3
        assert cases.json()[2]["satellite_style_pct"] is None

        created = client.post("/demo/reports", json=payload)
        assert created.status_code == 201
        report = created.json()
        assert report["status"] == "NEEDS_HUMAN_REVIEW"
        assert all(value in report["explanation"] for value in ("20%", "40%", "70%"))
        assert "synthetic demo values" in report["explanation"].lower()
        assert "synthetic" in report["data_status"]

        listed = client.get("/demo/reports")
        assert [item["id"] for item in listed.json()] == [report["id"]]

        reviewed = client.post(
            f"/demo/reports/{report['id']}/review", json={"note": "Checked in demo"}
        )
        assert reviewed.status_code == 200
        assert reviewed.json()["status"] == "REVIEWED_FOR_DEMO"
        assert reviewed.json()["review_note"] == "Checked in demo"

        assert client.delete("/demo/reports").status_code == 204
        assert client.get("/demo/reports").json() == []


def test_demo_api_validates_ranges_and_enumerations(tmp_path, monkeypatch):
    monkeypatch.setenv("RECON_DEMO_DB", str(tmp_path / "demo.sqlite3"))
    payload = {
        "locale": "mr",
        "form": {
            "damaged_share_pct": 101,
            "water_depth_band": "KNEE",
            "water_days": 3,
            "crop_stage": "VEGETATIVE",
        },
    }
    with TestClient(app) as client:
        assert client.post("/demo/reports", json=payload).status_code == 422
        payload["form"]["damaged_share_pct"] = 50
        payload["form"]["water_depth_band"] = "FLOODED"
        assert client.post("/demo/reports", json=payload).status_code == 422


def test_demo_reports_survive_a_client_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("RECON_DEMO_DB", str(tmp_path / "demo.sqlite3"))
    payload = {
        "locale": "en",
        "form": {
            "damaged_share_pct": 45,
            "water_depth_band": "ANKLE",
            "water_days": 1,
            "crop_stage": "SOWN_ONLY",
        },
    }
    with TestClient(app) as first_client:
        created = first_client.post("/demo/reports", json=payload)
        assert created.status_code == 201
        report_id = created.json()["id"]

    with TestClient(app) as restarted_client:
        reports = restarted_client.get("/demo/reports").json()
        assert [report["id"] for report in reports] == [report_id]


def test_missing_fixture_evidence_stays_unknown_with_explanation(tmp_path, monkeypatch):
    monkeypatch.setenv("RECON_DEMO_DB", str(tmp_path / "demo.sqlite3"))
    with TestClient(app) as client:
        missing_case = client.get("/demo/cases").json()[2]
        assert missing_case["satellite_style_pct"] is None
        assert missing_case["source_labels"]["satellite_style_pct"] == "MISSING"
        assert "evidence is insufficient" in missing_case["reason"].lower()
        assert "unknown" in missing_case["reason"].lower()
        assert "no value is inferred" in missing_case["reason"].lower()
