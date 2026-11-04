"""Create deterministic synthetic official claims from measured satellite results."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import random
from typing import Any

from shapely.geometry import shape

SEED = 42
PEAK_DATE = date(2024, 7, 25)
CLASS_COUNTS = {1: 15, 2: 15, 3: 20, 4: 15, 5: 15}
EXPECTED_FLAGS = {
    1: "SAT_UNDER_RISK",
    2: "PEER_INCONSISTENCY",
    3: "CLUSTER_BIAS",
    4: "PHOTO_INTEGRITY_ALERT",
    5: "GROUND_DRIVEN_BOUNDARY_CROSSING",
}


def _value(item: dict[str, Any]) -> float:
    value = float(item["v_sat"])
    if not 0 <= value <= 1:
        raise ValueError(f"case {item.get('case_id')} has invalid measured v_sat={value}")
    return value


def _draw(
    cases: list[dict[str, Any]], chosen: set[str], low: float, high: float, count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    eligible = [item for item in cases if str(item["case_id"]) not in chosen
                and low <= _value(item) <= high]
    rng.shuffle(eligible)
    if len(eligible) < count:
        raise ValueError(
            f"need {count} cases with measured v_sat in [{low}, {high}], found {len(eligible)}; "
            "do not relax the anomaly strata"
        )
    result = eligible[:count]
    chosen.update(str(item["case_id"]) for item in result)
    return result


def _connected_class3(
    cases: list[dict[str, Any]], chosen: set[str], rng: random.Random
) -> list[dict[str, Any]]:
    eligible = [item for item in cases if str(item["case_id"]) not in chosen
                and 0.45 <= _value(item) <= 0.70 and item.get("geom_utm")]
    by_village: dict[str, list[dict[str, Any]]] = {}
    for item in eligible:
        by_village.setdefault(str(item.get("village", "")), []).append(item)
    best: list[dict[str, Any]] = []
    for villagers in by_village.values():
        remaining = {str(row["case_id"]): row for row in villagers}
        geometries = {key: shape(row["geom_utm"]) for key, row in remaining.items()}
        while remaining:
            start = min(remaining)
            component, queue = {start}, [start]
            while queue:
                current = queue.pop()
                for other in sorted(remaining):
                    if other in component:
                        continue
                    if geometries[current].distance(geometries[other]) <= 2.0:
                        component.add(other)
                        queue.append(other)
            group = [remaining[key] for key in sorted(component)]
            if len(group) > len(best):
                best = group
            for key in sorted(component):
                remaining.pop(key, None)
    if len(best) < CLASS_COUNTS[3]:
        raise ValueError(
            f"need a contiguous, single-village set of {CLASS_COUNTS[3]} cases with measured "
            f"v_sat in [0.45, 0.70]; largest eligible component is {len(best)}"
        )
    remaining = {str(item["case_id"]): item for item in best}
    geometries = {key: shape(item["geom_utm"]) for key, item in remaining.items()}
    start = rng.choice(list(remaining))
    selected_ids = [start]
    while len(selected_ids) < CLASS_COUNTS[3]:
        frontier = [
            key for key in remaining if key not in selected_ids
            and any(geometries[key].distance(geometries[chosen_id]) <= 2.0
                    for chosen_id in selected_ids)
        ]
        if not frontier:
            raise ValueError("eligible connected component could not produce a 20-parcel subset")
        selected_ids.append(rng.choice(frontier))
    selected = [remaining[key] for key in selected_ids]
    chosen.update(str(item["case_id"]) for item in selected)
    return selected


def plant_anomalies(
    cases: list[dict[str, Any]], *, seed: int = SEED,
    image_provenance: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Build official records, a complete manifest, and stage-2 ground scenarios.

    Input cases must come from the Stage-1 runner and include measured ``v_sat``.
    Missing strata fail loudly; no synthetic measurement is substituted.
    """
    if len(cases) != 300:
        raise ValueError(f"expected 300 case results from Stage 1, received {len(cases)}")
    if len({str(row["case_id"]) for row in cases}) != 300:
        raise ValueError("case_id values must be unique")
    for item in cases:
        _value(item)
    provenance = image_provenance or {"status": "TEST_FIXTURE"}
    measured_from_verified_imagery = provenance.get("status") == "VERIFIED"
    rng = random.Random(seed)
    chosen: set[str] = set()
    selected: dict[int, list[dict[str, Any]]] = {}
    # Protect the connected riverside cohort before drawing overlapping value strata.
    selected[3] = _connected_class3(cases, chosen, rng)
    selected[1] = _draw(cases, chosen, 0.50, 0.70, CLASS_COUNTS[1], rng)
    selected[2] = _draw(cases, chosen, 0.35, 0.60, CLASS_COUNTS[2], rng)
    selected[4] = _draw(cases, chosen, 0.0, 0.12, CLASS_COUNTS[4], rng)
    selected[5] = _draw(cases, chosen, 0.20, 0.30, CLASS_COUNTS[5], rng)
    classes = {
        str(item["case_id"]): class_id
        for class_id, items in selected.items() for item in items
    }
    clean = [item for item in cases if str(item["case_id"]) not in chosen]
    if len(clean) != 220:
        raise RuntimeError(f"expected 220 clean cases, got {len(clean)}")

    villages = sorted({str(item.get("village", "Synthetic-V00")) for item in cases})
    assessor_by_village = {village: f"ASR-{(i % 20) + 1:02d}" for i, village in enumerate(villages)}
    cluster_assessor = "ASR-20"
    cluster_delay = rng.randint(3, 20)
    officials: list[dict[str, Any]] = []
    manifest_cases: list[dict[str, Any]] = []
    for item in cases:
        case_id = str(item["case_id"])
        class_id = classes.get(case_id, 0)
        satellite = _value(item)
        if class_id == 1:
            mid = satellite - 0.35
        elif class_id == 2:
            mid = satellite - 0.20
        elif class_id == 3:
            mid = 0.20
        elif class_id == 4:
            mid = round(satellite / 0.05) * 0.05
        elif class_id == 5:
            mid = 0.15
        else:
            mid = round(min(1.0, max(0.0, satellite + rng.gauss(0, 0.05))) / 0.05) * 0.05
            mid = min(1.0, max(0.0, mid))
        lo, hi = max(0.0, mid - 0.05), min(1.0, mid + 0.05)
        delay = cluster_delay if class_id == 3 else rng.randint(3, 20)
        assessor = cluster_assessor if class_id == 3 else assessor_by_village.get(
            str(item.get("village", "Synthetic-V00")), "ASR-01"
        )
        official = {
            "case_id": case_id,
            "damage_lo": round(lo, 3),
            "damage_hi": round(hi, 3),
            "assessed_on": (PEAK_DATE + timedelta(days=delay)).isoformat(),
            "assessor_token": assessor,
            "method": "synthetic benchmark claim",
        }
        officials.append(official)
        manifest_cases.append({
            "case_id": case_id,
            "class": class_id,
            "v_sat_measured": round(satellite, 4),
            "official": [official["damage_lo"], official["damage_hi"]],
            "assessor_token": assessor,
            "expected_flag": EXPECTED_FLAGS.get(class_id),
            "parcel_synthetic": True,
            "official_synthetic": True,
            "v_sat_measured_from_imagery": measured_from_verified_imagery,
            "assessed_on": official["assessed_on"],
            "synthetic_fields": [
                "parcel_geometry", "parcel_attributes", "official_interval", "assessor_token"
            ],
        })

    class4 = selected[4]
    class5 = selected[5]
    clean_for_ground = clean.copy()
    stage1_anomalies = selected[1] + selected[2]
    rng.shuffle(clean_for_ground)
    rng.shuffle(stage1_anomalies)
    honest = clean_for_ground[:40] + stage1_anomalies[:10]
    rng.shuffle(honest)
    if len(honest) != 50:
        raise RuntimeError("could not choose the 50 honest ground scenarios")
    honest_tier1 = honest[:30]
    honest_tier1_ids = [str(item["case_id"]) for item in honest_tier1]
    scenarios: list[dict[str, Any]] = []
    for index, item in enumerate(honest):
        scenarios.append({
            "case_id": str(item["case_id"]),
            "scenario": "HONEST_TIER1" if index < 30 else "HONEST_TIER2",
            "claimed_damage": round(min(1.0, max(0.0, _value(item) + rng.gauss(0, 0.08))), 4),
            "n_photos": 2,
            "synthetic": True,
        })
    fraud = class4.copy()
    rng.shuffle(fraud)
    for index, item in enumerate(fraud):
        scenario = "NEIGHBOR_FRUSTUM" if index < 8 else "CROPPED_DUPLICATE"
        row = {
            "case_id": str(item["case_id"]),
            "scenario": scenario,
            "claimed_damage": 0.75,
            "n_photos": 2,
            "synthetic": True,
        }
        if scenario == "CROPPED_DUPLICATE":
            row["dup_source_case_id"] = honest_tier1_ids[index % len(honest_tier1_ids)]
        scenarios.append(row)
    for item in class5:
        scenarios.append({
            "case_id": str(item["case_id"]),
            "scenario": "SURFING_TIER1",
            "claimed_damage": 0.58,
            "n_photos": 2,
            "synthetic": True,
        })
    manifest = {
        "seed": seed,
        "event_id": "MH-2024-07-PUNE",
        "synthetic_parcels_and_officials": True,
        "v_sat_source": provenance,
        "cases": manifest_cases,
    }
    return officials, manifest, scenarios


def render_official_sql(records: list[dict[str, Any]]) -> str:
    lines = [
        "-- Synthetic official claims generated from measured Stage-1 satellite results.",
        "BEGIN;",
    ]
    for row in records:
        case_id = row["case_id"]
        assessor = row["assessor_token"].replace("'", "''")
        method = row["method"].replace("'", "''")
        lines.append(
            "INSERT INTO official_assessments "
            "(case_id, damage_lo, damage_hi, assessed_on, assessor_token, method) VALUES "
            f"('{case_id}', {row['damage_lo']:.3f}, {row['damage_hi']:.3f}, "
            f"'{row['assessed_on']}', '{assessor}', '{method}') "
            "ON CONFLICT (case_id) DO UPDATE SET damage_lo = EXCLUDED.damage_lo, "
            "damage_hi = EXCLUDED.damage_hi, assessed_on = EXCLUDED.assessed_on, "
            "assessor_token = EXCLUDED.assessor_token, method = EXCLUDED.method;"
        )
    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "measured_cases", type=Path,
        help="JSON with 300 case_id, v_sat, village and geom_utm records from Stage 1",
    )
    parser.add_argument("--sql", type=Path, default=Path("sql/05_official_assessments.sql"))
    parser.add_argument("--manifest", type=Path, default=Path("benchmark/manifest.json"))
    parser.add_argument("--scenarios", type=Path, default=Path("benchmark/ground_scenarios.json"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if not args.measured_cases.is_file():
        parser.error(f"measured case results not found: {args.measured_cases}")
    payload = json.loads(args.measured_cases.read_text(encoding="utf-8"))
    provenance = payload.get("image_provenance", {})
    if provenance.get("status") != "VERIFIED" or not provenance.get("scene_ids"):
        parser.error(
            "measured case input must record verified imagery provenance and scene_ids; "
            "synthetic or unverified satellite values cannot be used to plant official claims"
        )
    cases = payload["cases"]
    officials, manifest, scenarios = plant_anomalies(
        cases, seed=args.seed, image_provenance=provenance
    )
    for path in (args.sql, args.manifest, args.scenarios):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.sql.write_text(render_official_sql(officials), encoding="utf-8")
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    args.scenarios.write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "official_assessments": len(officials),
        "manifest_cases": len(manifest["cases"]),
        "ground_scenarios": len(scenarios),
        "seed": args.seed,
        "synthetic": True,
    }, indent=2))


if __name__ == "__main__":
    main()
