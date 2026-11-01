"""Load, extract, and persist hazard context independently of observed damage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pipeline.hazard_extractor import RasterLayer, extract_hazard
from pipeline.hazard_inputs import (
    rain_cells_with_provenance,
    validate_discharge_payload,
    validate_rain_payload,
)


def load_rain_file(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Rainfall input {path} must be a JSON object")
    validation = validate_rain_payload(payload)
    if validation["status"] == "INVALID":
        raise ValueError(f"Invalid rainfall input {path}: {validation['quality_flags']}")
    cells = rain_cells_with_provenance(payload)
    for cell in cells:
        cell["input_status"] = validation["status"]
        cell["input_quality_flags"] = validation["quality_flags"]
    return cells, {
        "source": payload.get("source"),
        "synthetic": bool(payload.get("synthetic", False)),
        "provenance_status": payload.get("provenance_status", "UNVERIFIED"),
        "validation_status": validation["status"],
        "quality_flags": validation["quality_flags"],
    }


def load_discharge_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Discharge input {path} must be a JSON object")
    validation = validate_discharge_payload(payload)
    if validation["status"] == "INVALID":
        raise ValueError(f"Invalid discharge input {path}: {validation['quality_flags']}")
    payload.setdefault("provenance_status", "UNVERIFIED")
    payload["input_status"] = validation["status"]
    payload["input_quality_flags"] = validation["quality_flags"]
    return payload


def extract_for_case_parcels(
    parcels: Sequence[Mapping[str, Any]],
    hand_raster: RasterLayer | None,
    twi_raster: RasterLayer | None,
    rain_cells: Sequence[Mapping[str, Any]],
    discharge: Mapping[str, Any] | None,
    hand_values_by_taluka: Mapping[str, Sequence[float]],
    *,
    thresholds: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Return case_id, hazard_context, and quality flags for each parcel row."""
    rows = []
    for parcel in parcels:
        result = extract_hazard(
            parcel,
            hand_raster,
            twi_raster,
            rain_cells,
            discharge,
            hand_values_by_taluka.get(str(parcel.get("taluka", "")), []),
            thresholds=thresholds,
        )
        rows.append({
            "case_id": parcel["case_id"],
            "hazard_context": result["hazard_context"],
            "quality_flags": result["quality_flags"],
        })
    return rows


async def upsert_hazard_context(connection: Any, rows: Sequence[Mapping[str, Any]]) -> None:
    """Persist only hazard columns; flags remain in the separate quality report."""
    statement = """
        INSERT INTO hazard_context (
            case_id, rain_24h_max_mm, rain_imd_class, rain_percentile,
            antecedent_30d_percentile, discharge_exposure, hand_m, twi,
            hand_pctile_in_taluka, soil_class, plausibility
        ) VALUES (
            $1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, $11
        )
        ON CONFLICT (case_id) DO UPDATE SET
            rain_24h_max_mm = EXCLUDED.rain_24h_max_mm,
            rain_imd_class = EXCLUDED.rain_imd_class,
            rain_percentile = EXCLUDED.rain_percentile,
            antecedent_30d_percentile = EXCLUDED.antecedent_30d_percentile,
            discharge_exposure = EXCLUDED.discharge_exposure,
            hand_m = EXCLUDED.hand_m,
            twi = EXCLUDED.twi,
            hand_pctile_in_taluka = EXCLUDED.hand_pctile_in_taluka,
            soil_class = EXCLUDED.soil_class,
            plausibility = EXCLUDED.plausibility
    """
    for row in rows:
        hazard = row["hazard_context"]
        await connection.execute(
            statement,
            row["case_id"],
            hazard["rain_24h_max_mm"],
            hazard["rain_imd_class"],
            hazard["rain_percentile"],
            hazard["antecedent_30d_percentile"],
            json.dumps(hazard["discharge_exposure"]) if hazard["discharge_exposure"] is not None else None,
            hazard["hand_m"],
            hazard["twi"],
            hazard["hand_pctile_in_taluka"],
            hazard["soil_class"],
            hazard["plausibility"],
        )


def quality_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        for flag in row.get("quality_flags", []):
            counts[flag] = counts.get(flag, 0) + 1
    return {
        "schema_version": 1,
        "parcel_count": len(rows),
        "quality_flag_counts": dict(sorted(counts.items())),
        "damage_estimates_modified": False,
    }
