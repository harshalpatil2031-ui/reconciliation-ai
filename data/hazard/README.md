# Hazard input contract and provenance

Hazard inputs are kept separate from `observed_estimates`; they produce only `hazard_context` plus a separate quality report. Rainfall, discharge, HAND, TWI, and soil explain whether flood damage is plausible. They never change a damage estimate.

## Rain JSON

```json
{
  "source": "IMD 0.25 degree / GPM IMERG V07",
  "synthetic": false,
  "provenance_status": "UNVERIFIED",
  "provenance": {"url": "...", "product_id": "...", "retrieved_at": "YYYY-MM-DD", "license_status": "exact license/terms", "license_review_status": "PENDING"},
  "cells": [{"lat": 18.50, "lon": 73.85, "max_24h_mm": 118.4, "max_24h_date": "2024-07-25", "imd_class": "VERY_HEAVY", "percentile": 99.2, "antecedent_30d_percentile": 91.0}]
}
```

The nearest grid cell to the parcel centroid is used. The rainfall amount is reclassified by the IMD 24-hour thresholds in the relay, and a supplied class disagreement emits `RAIN_CLASS_MISMATCH`. Classification bands are from the official [IMD heavy-rainfall review](https://internal.imd.gov.in/press_release/20250114_pr_3552.pdf). IMD gridded data availability and requested citation are recorded at the official [IMD Pune gridded rainfall page](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html); access and redistribution terms still require review. Real inputs cannot pass `make check-hazard` as ready unless provenance is verified and `license_review_status` is `APPROVED`. Synthetic fixtures must set `synthetic: true` and `license_status: "GENERATED"`.

## Discharge JSON

```json
{
  "source": "CWC or WRD bulletin identifier",
  "synthetic": false,
  "provenance_status": "UNVERIFIED",
  "provenance": {"url": "...", "product_id": "...", "retrieved_at": "YYYY-MM-DD", "license_status": "exact license/terms", "license_review_status": "PENDING"},
  "release_cusecs": 37500,
  "date": "2024-07-25",
  "reach": [[73.85, 18.48], [73.90, 18.51]],
  "reach_buffer_m": 1500
}
```

`reach` is an EPSG:4326 coordinate array. Exposure is measured against the nearest valid HAND <= 0.5 m raster cell within the buffered reach. Until an event bulletin URL/product ID and reuse terms are recorded and approved, the release stays 🔎 unverified and readiness fails; simulated examples must set `synthetic: true` and `license_status: "GENERATED"`.

## Raster provenance

`../rasters/manifest.json` records each expected raster's provider, acquisition date, expected CRS/resolution/band count, nodata policy and licensing status. `scripts/check_rasters.py` records measured metadata and quality flags in a machine-readable report. No source image or raster is included until its exact product ID, retrieval date, processing parameters and license/attribution are checked.

HAND/TWI are area-weighted over parcel pixels. Missing data returns null context values and explicit `quality_flags`; it does not silently become zero. `plausibility` defaults to `MODERATE` if evidence is insufficient.
