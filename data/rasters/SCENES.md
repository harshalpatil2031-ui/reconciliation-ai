# Stage 1 raster inputs

**Status: 🔎 not acquired in this repository.** This folder contains the input manifest and validation tools; it contains no Sentinel imagery or terrain rasters. The `data/rasters/manifest.json` entries describe target products, not downloaded scenes. Product IDs, tile IDs, exact processing baselines, nodata values, DEM drainage threshold, and licenses remain to be recorded after authorized acquisition.

| Planned asset | Date | Expected bands | Current status |
|---|---:|---|---|
| Sentinel-2 L2A pre-event | 2024-07-18 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-2 L2A window 1 | 2024-08-03 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-2 L2A window 2 | 2024-08-13 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-1A GRD pre-event | 2024-07-15 | VV, VH | 🔎 missing; product/pass metadata not measured |
| Sentinel-1A GRD peak | 2024-07-27 | VV, VH | 🔎 missing; product/pass metadata not measured |
| HAND/TWI terrain | source date not applicable | HAND_m, TWI | 🔎 missing; DEM tile IDs and drainage threshold not recorded |

The optional post-event SAR scene near 2024-08-08 has not been searched for; it is not assumed to exist. Sentinel-2 L2A and Sentinel-1 GRD are discoverable from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/about). The Copernicus DEM GLO-30 entry records its required source attribution and access conditions in the [source catalogue](../hazard/sources.json).

When assets are supplied, run `python scripts/check_rasters.py`. It writes `quality_report.json`, flags absent or invalid layers, checks required CRS/resolution/band count/nodata and clear SCL fraction, and checks the six core rasters share one grid. Readiness stays false until the manifest is `VERIFIED` (or `SYNTHETIC` for a fully tagged fixture) and every required asset has an exact product/tile ID, verified source status, approved license status and attribution, acquisition date or explicit not-applicable marker, and nodata policy. A report with missing products or incomplete provenance is expected to exit nonzero. Do not describe missing scenes as low-cloud or validated inputs.
