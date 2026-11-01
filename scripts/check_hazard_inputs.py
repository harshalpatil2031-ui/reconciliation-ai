"""Validate local hazard JSON files and emit explicit missing/provenance flags."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.hazard_inputs import validate_discharge_payload, validate_rain_payload  # noqa: E402


def _validate(path: Path, kind: str) -> dict[str, object]:
    if not path.is_file():
        return {"kind": kind, "status": "MISSING", "quality_flags": [f"{kind.upper()}_INPUT_MISSING"], "path": str(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_rain_payload(payload) if kind == "rainfall" else validate_discharge_payload(payload)
    report["path"] = str(path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rain", type=Path, default=ROOT / "data/hazard/imd_imerg_pune_202407.json")
    parser.add_argument("--discharge", type=Path, default=ROOT / "data/hazard/cwc_wrd_khadakwasla.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/hazard/quality_report.json")
    args = parser.parse_args()
    items = [_validate(args.rain, "rainfall"), _validate(args.discharge, "discharge")]
    flags = sorted({flag for item in items for flag in item["quality_flags"]})
    report = {"schema_version": 1, "inputs": items, "quality_flags": flags,
              "ready": all(item["status"] in {"VALID", "SYNTHETIC"} for item in items)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ready": report["ready"], "quality_flags": flags, "output": str(args.output)}))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
