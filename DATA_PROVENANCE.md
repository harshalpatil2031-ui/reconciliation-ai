# Data, model and claim provenance register

**Purpose:** Track the origin, access basis, license, version, and evidence status of every external dataset, model, photo fixture, and number used in Reconciliation AI. This is a starter register populated from the v3 specification; it is not proof that any data has been acquired, licensed, or validated.

**Rule:** Do not ingest or redistribute an asset until its exact source, version/date, permitted use, attribution requirements, and storage restrictions are recorded and reviewed. A status of ✅ in the design spec means the source was described there as verified; it does not establish that this repository has the asset or a license to redistribute it.

## External data and imagery

| Asset / source | Intended use | Spec status | Repository access / license state | Owner / next action |
|---|---|---|---|---|
| Sentinel-2 L2A | Optical indices and parcel observation | ✅ standard source in v3 | No imagery files committed; record product IDs, acquisition dates, processing baseline, provider terms, and attribution before ingest | P1 — capture source manifest |
| Sentinel-1A GRD | SAR inundation evidence | Exact pass dates require verification | No scenes committed; confirm pass dates, product IDs, processing, and permitted use | P1 — verify acquisition/source |
| Sen1Floods11-tuned Prithvi-EO-2.0-300M / water masks | Candidate flood-water mask | v3 labels source verified | No model weights or masks committed; record model card, weights/version, license, input restrictions, and validation before use | P1 — document model provenance |
| Maharashtra Bhunaksha cadastral polygons | Parcel boundaries | 🔎 access needs confirmation | No polygons committed; obtain written access/usage terms and confirm redistribution limits | P1 — confirm API/shapefile rights |
| e-Peek Pahani / 7/12 crop registry | Crop and sowing-date context | ✅ source identified; state integration needed | No records or integration credentials committed; document authorized access and field minimization | P2 — confirm sandbox/access |
| Revenue/Agriculture panchnama records | Official assessment reference | Requires MoU | No real records committed; use clearly labeled simulated records until authorized data access exists | P1 — record MoU/data steward |
| IMD gridded rainfall; NASA GPM IMERG V07 | Rainfall hazard context | ✅ sources identified in v3 | No data files committed; capture dataset version, time/space coverage, citation, and terms | P1 — add ingestion manifest |
| CWC flood portal; GUARDIAN gauges; WRD bulletins | River/discharge context | ✅ sources identified in v3 | No source extracts committed; record exact bulletin/gauge URLs or identifiers, retrieval date, units, and reuse terms | P1 — cite each event observation |
| Copernicus DEM GLO-30 Public | Terrain, HAND/TWI derivation | ✅ source selected and acquired | Two source tile hashes, redistribution attribution, AOI, and derivation are recorded in `data/rasters/SCENES.md` and `data/rasters/manifest.json`; source is a ~30 m DSM resampled to 10 m; drainage threshold is initial/untuned | P1 — calibrate threshold against authoritative local hydrography and align Sentinel scenes |

## Models, photos and generated data

| Asset | Required record before use | Current state |
|---|---|---|
| Photo verifier / crop-consistency model and weights | Exact model and weights, version/hash, source, license, intended use, known limits, threshold calibration set | No selected artifacts or license register committed; P2 owns this |
| Demo photo bundles | Per-image source, photographer/permission, license, capture metadata handling, expected scenario, real/synthetic label | No bundles in repository; the relay requires `ATTRIBUTION.md`; P2 owns it |
| Synthetic parcels, officials, planted anomalies, synthetic embeddings | Generator version/seed, manifest, planted class, generated fields, 🧪 label | No generated benchmark data committed; P1/P4 own the manifest and runner |
| Worked examples and benchmark metrics | Exact input fixture, calculation/version, sample size, interval, real-vs-synthetic tag | v3 §10 is marked 🧪; no benchmark `RESULTS.md` is present |

## Privacy and publication checks

- Never collect or store Aadhaar. Use only the case and parcel references allowed by the frozen contract.
- Strip EXIF from stored/served derivatives; do not expose raw farmer references in logs or demo screenshots.
- Use pseudonymous officer tokens. Do not include personal data in synthetic fixtures.
- Review each asset for redistribution restrictions before committing it. Keep restricted raw data outside Git and commit only permitted, minimized derivatives or manifests.
- Tag verified, unverified, synthetic, initial/untuned, and roadmap claims using the v3 status legend. Do not present simulated metrics as real-world performance.

## Entry template

| Field | Value |
|---|---|
| Asset / claim | |
| Source and exact version/date | |
| URL / product ID / model hash | |
| Retrieved / generated date | |
| License / permission / attribution | |
| Storage and redistribution constraints | |
| Real / synthetic / unverified / target status | |
| Owner and reviewer | |
| Evidence / validation / limitations | |
