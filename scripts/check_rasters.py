"""Inspect raster inputs against data/rasters/manifest.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.raster_inputs import report_for_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/rasters/manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/rasters/quality_report.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = report_for_manifest(manifest, ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ready": report["ready"], "quality_flags": report["quality_flags"], "output": str(args.output)}))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
