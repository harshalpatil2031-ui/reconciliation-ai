"""Align a source GeoTIFF to a reference grid; categorical bands use nearest resampling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.raster_inputs import align_to_reference  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--categorical-band", type=int, action="append", default=[])
    args = parser.parse_args()
    align_to_reference(
        args.source,
        args.reference,
        args.output,
        categorical_bands=args.categorical_band,
    )
    print(f"Aligned {args.source} onto {args.reference}: {args.output}")


if __name__ == "__main__":
    main()
