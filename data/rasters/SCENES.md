# Stage 1 raster inputs

**Status: partial.** The Copernicus GLO-30 source tiles and derived HAND/TWI raster are now present. Sentinel-1 and Sentinel-2 scenes are still missing. The `data/rasters/manifest.json` records terrain source IDs, checksums, license attribution, AOI, and processing settings. The project specification gave an approximate 40 × 40 km AOI but no coordinates; this work records the selected bounds as 73.81–74.19°E, 18.32–18.68°N.

| Planned asset | Date | Expected bands | Current status |
|---|---:|---|---|
| Sentinel-2 L2A pre-event | 2024-07-18 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-2 L2A window 1 | 2024-08-03 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-2 L2A window 2 | 2024-08-13 | B02, B03, B04, B05, B08, B8A, B11, SCL | 🔎 missing; clear fraction not measured |
| Sentinel-1A GRD pre-event | 2024-07-15 | VV, VH | 🔎 missing; product/pass metadata not measured |
| Sentinel-1A GRD peak | 2024-07-27 | VV, VH | 🔎 missing; product/pass metadata not measured |
| HAND/TWI terrain | source date not applicable | HAND_m, TWI | ✅ derived from GLO-30; 30 m source resampled to 10 m; 3 km² D8 stream-initiation threshold is initial/untuned |

The optional post-event SAR scene near 2024-08-08 has not been searched for; it is not assumed to exist. Sentinel-2 L2A and Sentinel-1 GRD are discoverable from the [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/about).

## Terrain processing record

- Output: [`terrain_hand_twi_32643.tif`](terrain_hand_twi_32643.tif), EPSG:32643, 10 m grid, bands `HAND_m` and `TWI`, nodata `-9999`.
- Source: Copernicus DEM GLO-30 Public 1° COG tiles [`E073`](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N18_00_E073_00_DEM/Copernicus_DSM_COG_10_N18_00_E073_00_DEM.tif) and [`E074`](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N18_00_E074_00_DEM/Copernicus_DSM_COG_10_N18_00_E074_00_DEM.tif); raw downloads are under ignored `data/raw/terrain/` and are not committed.
- Source tile SHA-256: `e5e127b1a1b56c0415276707bbb8c4e7bb357cf0976030a19f8d166cd9d590c9` (E073) and `1a44c053a6ef9e06fc522c532bde90b29c0039b45290b8974021497902d1136e` (E074).
- Output SHA-256: `ff71939a957762c4bd74a852e67850115ac128647ef4adb502e9350091b50559`.
- Rebuild with `pip install -r requirements.txt` and `make derive-terrain`. The script conditions pits/depressions/flats, uses D8 routing, and derives HAND with a 3 km² stream-initiation area (3,334 cells at 30 m). TWI is `ln(specific catchment area / tan(slope))`, with the slope tangent floored at 0.001.
- The 10 m output grid is resampled from approximately 30 m input and does not add 10 m source detail. The DEM is a DSM that includes buildings and vegetation. The 3 km² drainage threshold is initial and has not been independently calibrated against an authoritative local hydrography layer. The processing records 3,519 cells without a D8 HAND assignment and fills those from the nearest assigned cell (maximum distance 11.7 output cells); this limitation must be considered before using HAND for parcel placement.
- Attribution for redistributed adapted data: “produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved”. See the [official Copernicus DEM access and licensing page](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

This terrain grid becomes the target reference when the Sentinel rasters are acquired; reproject them to its transform, shape, and CRS. Until then, the overall manifest and Stage 1 raster check remain unready because the required optical and SAR scenes are absent.

When assets are supplied, run `python scripts/check_rasters.py`. It writes `quality_report.json`, flags absent or invalid layers, checks required CRS/resolution/band count/nodata and clear SCL fraction, and checks the six core rasters share one grid. Readiness stays false until the manifest is `VERIFIED` (or `SYNTHETIC` for a fully tagged fixture) and every required asset has an exact product/tile ID, verified source status, approved license status and attribution, acquisition date or explicit not-applicable marker, and nodata policy. A report with missing products or incomplete provenance is expected to exit nonzero. Do not describe missing scenes as low-cloud or validated inputs.
