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
        assert "70%" in report["explanation"]
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
