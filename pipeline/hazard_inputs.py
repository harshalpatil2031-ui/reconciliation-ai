"""Validation helpers for rainfall and river/discharge inputs."""

from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Any, Mapping

from shapely.geometry import LineString

from pipeline.hazard_extractor import classify_imd_rainfall


def _provenance_flags(payload: Mapping[str, Any]) -> list[str]:
    provenance = payload.get("provenance") or {}
    flags: list[str] = []
    if not isinstance(provenance, Mapping):
        provenance = {}
        flags.append("PROVENANCE_METADATA_INVALID")
    if not payload.get("source"):
        flags.append("SOURCE_MISSING")
    if not provenance.get("url") and not provenance.get("product_id"):
        flags.append("SOURCE_IDENTIFIER_MISSING")
    if not provenance.get("retrieved_at"):
        flags.append("RETRIEVAL_DATE_MISSING")
    if not provenance.get("license_status"):
        flags.append("LICENSE_STATUS_MISSING")
    if payload.get("synthetic"):
        flags.append("SYNTHETIC_INPUT")
    elif payload.get("provenance_status", "UNVERIFIED") != "VERIFIED":
        flags.append("UNVERIFIED_SOURCE")
    return flags


def validate_rain_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    flags = _provenance_flags(payload)
    errors: list[str] = []
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        errors.append("RAIN_CELLS_MISSING")
        cells = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, Mapping):
            errors.append(f"RAIN_CELL_{index}_INVALID_FIELDS")
            continue
        try:
            lat, lon = float(cell["lat"]), float(cell["lon"])
            amount = float(cell["max_24h_mm"])
            date.fromisoformat(str(cell["max_24h_date"]))
        except (KeyError, TypeError, ValueError):
            errors.append(f"RAIN_CELL_{index}_INVALID_FIELDS")
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and amount >= 0 and isfinite(amount)):
            errors.append(f"RAIN_CELL_{index}_OUT_OF_RANGE")
        expected_class = classify_imd_rainfall(amount)
        if cell.get("imd_class") != expected_class:
            flags.append("RAIN_CLASS_MISMATCH")
        for field in ("percentile", "antecedent_30d_percentile"):
            value = cell.get(field)
            if value is None:
                flags.append(f"{field.upper()}_MISSING")
            elif not 0 <= float(value) <= 100:
                errors.append(f"RAIN_CELL_{index}_{field.upper()}_OUT_OF_RANGE")
    return {
        "kind": "rainfall",
        "status": "INVALID" if errors else ("LOW_QUALITY" if "RAIN_CLASS_MISMATCH" in flags else "SYNTHETIC" if payload.get("synthetic") else "UNVERIFIED" if "UNVERIFIED_SOURCE" in flags else "VALID"),
        "quality_flags": sorted(set(flags + errors)),
        "cell_count": len(cells),
        "source": payload.get("source"),
    }


def rain_cells_with_provenance(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Propagate the file-level status to each cell consumed by extract_hazard."""
    return [
        {
            **cell,
            "synthetic": bool(payload.get("synthetic", False)),
            "provenance_status": payload.get("provenance_status", "UNVERIFIED"),
            "source": payload.get("source"),
        }
        for cell in payload.get("cells", [])
        if isinstance(cell, Mapping)
    ]


def validate_discharge_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    flags = _provenance_flags(payload)
    errors: list[str] = []
    try:
        release = float(payload["release_cusecs"])
        date.fromisoformat(str(payload["date"]))
        reach = payload["reach"]
        line = LineString(reach)
        buffer_m = float(payload["reach_buffer_m"])
        if release < 0 or not isfinite(release) or buffer_m <= 0:
            errors.append("DISCHARGE_MEASURE_INVALID")
        if not all(-180 <= x <= 180 and -90 <= y <= 90 for x, y, *_ in line.coords):
            errors.append("DISCHARGE_REACH_COORDINATES_INVALID")
    except (KeyError, TypeError, ValueError):
        errors.append("DISCHARGE_FIELDS_INVALID")
    return {
        "kind": "discharge",
        "status": "INVALID" if errors else ("SYNTHETIC" if payload.get("synthetic") else "UNVERIFIED" if "UNVERIFIED_SOURCE" in flags else "VALID"),
        "quality_flags": sorted(set(flags + errors)),
        "source": payload.get("source"),
        "date": payload.get("date"),
    }
