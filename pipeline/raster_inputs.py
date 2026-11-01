"""Raster source provenance, metadata checks, quality flags, and grid alignment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

CLEAR_SCL_CLASSES = {4, 5, 6, 7}
VALID_SCL_CLASSES = set(range(12))


def inspect_asset(root: Path, asset: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect one declared raster and return its measured metadata and quality flags."""
    relative_path = Path(str(asset["path"]))
    path = relative_path if relative_path.is_absolute() else root / relative_path
    result: dict[str, Any] = {
        "id": asset["id"],
        "path": str(relative_path).replace("\\", "/"),
        "source": asset.get("source", {}),
        "acquisition_date": asset.get("acquisition_date"),
        "synthetic": bool(asset.get("synthetic", False)),
        "exists": path.is_file(),
        "quality_flags": [],
        "metadata": None,
    }
    flags: list[str] = result["quality_flags"]
    if not path.is_file():
        flags.append("MISSING_RASTER")
        result["status"] = "MISSING"
        return result

    with rasterio.open(path) as dataset:
        xres, yres = dataset.res
        measured = {
            "crs": dataset.crs.to_string() if dataset.crs else None,
            "width": dataset.width,
            "height": dataset.height,
            "band_count": dataset.count,
            "resolution": [abs(float(xres)), abs(float(yres))],
            "transform": list(dataset.transform)[:6],
            "nodata": dataset.nodata,
            "bounds": list(dataset.bounds),
            "dtypes": list(dataset.dtypes),
            "band_descriptions": list(dataset.descriptions),
        }
        result["metadata"] = measured

        expected = asset.get("expected", {})
        if expected.get("crs") and measured["crs"] != expected["crs"]:
            flags.append("RASTER_CRS_MISMATCH")
        if expected.get("band_count") and measured["band_count"] != expected["band_count"]:
            flags.append("RASTER_BAND_COUNT_MISMATCH")
        expected_resolution = expected.get("resolution_m")
        is_utm = measured["crs"] and measured["crs"].upper().startswith("EPSG:326")
        if expected_resolution is not None and is_utm:
            target_resolution = [expected_resolution, expected_resolution]
            if not np.allclose(measured["resolution"], target_resolution, atol=0.01):
                flags.append("RASTER_RESOLUTION_MISMATCH")
        if expected.get("require_nodata", True) and dataset.nodata is None:
            flags.append("RASTER_NODATA_UNDECLARED")

        scl_band = expected.get("scl_band")
        if scl_band is not None and 1 <= int(scl_band) <= dataset.count:
            scl = dataset.read(int(scl_band), masked=True)
            values = np.asarray(scl.compressed())
            if values.size:
                unexpected = set(np.unique(values).astype(int)) - VALID_SCL_CLASSES
                if unexpected:
                    flags.append("SCL_CLASS_OUT_OF_RANGE")
                else:
                    clear_fraction = float(np.isin(values, list(CLEAR_SCL_CLASSES)).mean())
                    result["clear_fraction"] = clear_fraction
                    if clear_fraction < float(expected.get("min_clear_fraction", 0.40)):
                        flags.append("LOW_CLEAR_FRACTION")
            else:
                flags.append("SCL_HAS_NO_VALID_PIXELS")

    result["status"] = "LOW_QUALITY" if flags else "VALID"
    return result


def check_alignment(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return explicit flags when available raster grids do not share one grid."""
    grids = [r["metadata"] for r in reports if r.get("metadata")]
    if len(grids) < 2:
        return []
    reference = grids[0]
    flags: list[str] = []
    for grid in grids[1:]:
        if any(grid[key] != reference[key] for key in ("crs", "width", "height", "transform")):
            flags.append("RASTER_GRID_MISMATCH")
            break
    return flags


def report_for_manifest(manifest: Mapping[str, Any], root: Path) -> dict[str, Any]:
    """Build an auditable check report, preserving missing and low-quality assets."""
    reports = [inspect_asset(root, asset) for asset in manifest.get("assets", [])]
    alignment_flags = check_alignment(reports)
    if alignment_flags:
        for report in reports:
            if report.get("metadata"):
                report["quality_flags"].extend(alignment_flags)
                report["status"] = "LOW_QUALITY"
    has_required_failure = any(
        asset.get("required", True) and report["status"] != "VALID"
        for asset, report in zip(manifest.get("assets", []), reports, strict=True)
    )
    return {
        "schema_version": 1,
        "manifest_status": manifest.get("status", "UNSPECIFIED"),
        "assets": reports,
        "quality_flags": sorted({flag for report in reports for flag in report["quality_flags"]}),
        "ready": not has_required_failure,
    }


def align_to_reference(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
    *,
    categorical_bands: Sequence[int] = (),
) -> None:
    """Reproject/resample a raster onto a reference grid without resampling classes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(source_path) as source, rasterio.open(reference_path) as reference:
        profile = source.profile.copy()
        profile.update(
            driver="GTiff",
            crs=reference.crs,
            transform=reference.transform,
            width=reference.width,
            height=reference.height,
            tiled=True,
            compress="deflate",
        )
        with rasterio.open(output_path, "w", **profile) as destination:
            categorical = set(categorical_bands)
            for band in range(1, source.count + 1):
                resampling = Resampling.nearest if band in categorical else Resampling.bilinear
                reproject(
                    source=rasterio.band(source, band),
                    destination=rasterio.band(destination, band),
                    src_transform=source.transform,
                    src_crs=source.crs,
                    src_nodata=source.nodata,
                    dst_transform=reference.transform,
                    dst_crs=reference.crs,
                    dst_nodata=source.nodata,
                    resampling=resampling,
                )


def dn_to_reflectance(
    dn: np.ndarray,
    boa_add_offset: float,
    quantification_value: float = 10_000.0,
) -> np.ndarray:
    """Apply Sentinel-2 metadata offset, then clip reflectance to the relay's range."""
    if quantification_value <= 0:
        raise ValueError("quantification_value must be positive")
    reflectance = (np.asarray(dn, dtype=np.float32) + float(boa_add_offset)) / quantification_value
    return np.clip(reflectance, 0.0, 1.2)
