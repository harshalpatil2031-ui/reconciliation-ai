import json
from pathlib import Path


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "demo_cases.json"
PERCENT_FIELDS = (
    "official_pct",
    "satellite_style_pct",
    "farmer_report_pct",
    "review_threshold_pct",
)
EVIDENCE_FIELDS = {"official_pct", "satellite_style_pct", "farmer_report_pct"}
SOURCE_LABELS = {"SYNTHETIC", "SYNTHETIC_DEMO_RULE", "MISSING"}
CASE_STATUSES = {
    "NEEDS_HUMAN_REVIEW",
    "CONSISTENT_FOR_DEMO",
    "INSUFFICIENT_EVIDENCE",
}


def test_demo_fixtures_follow_versioned_synthetic_contract():
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))

    assert 3 <= len(cases) <= 6
    assert len({case["id"] for case in cases}) == len(cases)

    for case in cases:
        assert case["schema_version"] == 1
        assert case["data_status"] == "SYNTHETIC"
        assert case["status"] in CASE_STATUSES
        assert case["title"].strip()
        assert case["reason"].strip()
        assert set(case["source_labels"]) == set(PERCENT_FIELDS)

        for field in PERCENT_FIELDS:
            value = case[field]
            label = case["source_labels"][field]
            assert label in SOURCE_LABELS
            if value is None:
                assert field != "review_threshold_pct"
                assert label == "MISSING"
            else:
                assert type(value) in (int, float)
                assert 0 <= value <= 100
                assert label in {"SYNTHETIC", "SYNTHETIC_DEMO_RULE"}
                if field in EVIDENCE_FIELDS:
                    assert f"{value}%" in case["reason"]


def test_fixture_set_covers_required_scenarios_and_preserves_unknowns():
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))
    by_status = {case["status"]: case for case in cases}

    assert set(by_status) == CASE_STATUSES

    disagreement = by_status["NEEDS_HUMAN_REVIEW"]
    assert disagreement["official_pct"] < disagreement["review_threshold_pct"]
    assert disagreement["satellite_style_pct"] > disagreement["review_threshold_pct"]

    missing = by_status["INSUFFICIENT_EVIDENCE"]
    assert missing["satellite_style_pct"] is None
    assert missing["source_labels"]["satellite_style_pct"] == "MISSING"
    assert "unknown" in missing["reason"].lower()
    assert "no value is inferred" in missing["reason"].lower()
