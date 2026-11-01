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
VERIFIED_MANIFEST_STATUSES = {"VERIFIED", "SYNTHETIC"}


def _provenance_flags(asset: Mapping[str, Any]) -> list[str]:
    source = asset.get("source") or {}
    if not isinstance(source, Mapping):
        return ["RASTER_PROVENANCE_INVALID"]
    flags: list[str] = []
    if not source.get("provider"):
        flags.append("RASTER_PROVIDER_MISSING")
    if not source.get("product_id"):
        flags.append("RASTER_PRODUCT_ID_MISSING")
    synthetic = bool(asset.get("synthetic", False))
    expected_license_status = "GENERATED" if synthetic else "APPROVED"
    if not source.get("license_status"):
        flags.append("RASTER_LICENSE_STATUS_MISSING")
    elif str(source["license_status"]).upper() != expected_license_status:
        flags.append("RASTER_LICENSE_UNVERIFIED")
    if not source.get("license_or_attribution"):
        flags.append("RASTER_ATTRIBUTION_MISSING")
    expected_status = "SYNTHETIC" if synthetic else "VERIFIED"
    if source.get("provenance_status") != expected_status:
        flags.append("RASTER_SOURCE_UNVERIFIED")
    if not asset.get("acquisition_date") and not asset.get("date_not_applicable", False):
        flags.append("RASTER_ACQUISITION_DATE_MISSING")
    if not asset.get("nodata_policy"):
        flags.append("RASTER_NODATA_POLICY_MISSING")
    return flags


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
    flags.extend(_provenance_flags(asset))

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
    manifest_status = str(manifest.get("status", "UNSPECIFIED")).upper()
    manifest_flags = []
    if not manifest.get("assets"):
        manifest_flags.append("RASTER_ASSETS_MISSING")
    if manifest_status not in VERIFIED_MANIFEST_STATUSES:
        manifest_flags.append("RASTER_MANIFEST_UNVERIFIED")
    has_required_failure = any(
        asset.get("required", True) and report["status"] != "VALID"
        for asset, report in zip(manifest.get("assets", []), reports, strict=True)
    )
    has_required_failure |= bool(manifest_flags)
    quality_flags = {flag for report in reports for flag in report["quality_flags"]}
    quality_flags.update(manifest_flags)
    return {
        "schema_version": 1,
        "manifest_status": manifest_status,
        "assets": reports,
        "quality_flags": sorted(quality_flags),
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
