"""Write a Stage 1 handoff only after measured outputs and snapshot exist."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    missing = [str(path) for path in (args.measured, args.manifest, args.snapshot)
               if not path.is_file()]
    if missing:
        parser.error("handoff prerequisites missing: " + ", ".join(missing))
    measured = json.loads(args.measured.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    provenance = measured.get("image_provenance", {})
    if provenance.get("status") != "VERIFIED" or not provenance.get("scene_ids"):
        parser.error("measured output has no verified imagery provenance")
    if len(measured.get("cases", [])) != 300:
        parser.error("Stage 1 handoff requires exactly 300 measured case results")
    if manifest.get("synthetic_parcels_and_officials") is not True:
        parser.error("benchmark manifest must identify synthetic parcels and official claims")
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unavailable"
    content = [
        "# Stage 1 benchmark handoff",
        "",
        f"Created: {datetime.now(timezone.utc).isoformat()}",
        f"Repository revision: `{commit}`",
        "",
        "## Artifacts",
        "",
        f"- Measured Stage 1 results: `{args.measured}` (SHA-256 `{sha256(args.measured)}`)",
        f"- Benchmark manifest: `{args.manifest}` (SHA-256 `{sha256(args.manifest)}`)",
        f"- PostgreSQL custom-format snapshot: `{args.snapshot}` (SHA-256 `{sha256(args.snapshot)}`)",
        f"- Verified scene IDs: {', '.join(map(str, provenance['scene_ids']))}",
        "",
        "## Counts and review notes",
        "",
        f"- Measured cases: {len(measured['cases'])}",
        f"- Manifest cases: {len(manifest.get('cases', []))}",
        "- Parcel geometries and official benchmark claims are synthetic.",
        "- Satellite estimates are measured from the listed verified imagery.",
        "- This handoff is for review and reproduction; it is not field validation or a compensation decision.",
        "",
        "## Restore",
        "",
        "Use `make restore S=1` from the repository root after starting the configured database. Verify table counts with `make counts`.",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
