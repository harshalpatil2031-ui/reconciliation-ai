# Cross-stage JSON shapes

These shapes are transcribed from relay Section 2.4. `backend.models` provides the canonical Pydantic v2 models.

## Satellite estimate quality

`observed_estimates.quality` for `source='satellite'` contains `loss_attr`, `area_dmg_frac`, `n_eff`, `clear_frac`, `water_frac_peak`, nullable `water_frac_recession`, `window_used`, `flags`, `flags_assessable`, `controls_n`, control deficit summary/range, onset fields, `min_width_m`, `mode`, and a Leaflet-ready GeoJSON `pixel_grid`. Pixel-grid coordinates are EPSG:4326 rounded to 6 decimals; one feature represents each eligible 10 m pixel. `water_frac_recession` is null when no later SAR scene exists; `flags_assessable` is false when only one optical window is valid.

## Ground estimate quality

`observed_estimates.quality` for `source='ground'` contains verification `tier`, `excluded`, photo counts and IDs, flags, structured form values, consistency status, maximum duplicate similarity, frustum overlaps, and `locale`. If `excluded` is true, Stage 3 ignores the row for pooling but still raises `PHOTO_INTEGRITY_ALERT`. Estimate value, sigma, and interval columns remain populated.

## Detection factors

`detections.factors` is an array of exactly 12 factor objects in the `FactorCode` enum order. Each has `code`, `status`, `evidence`, and nullable `reason`. `reason` is a machine-readable string when status is `CANNOT_ASSESS`.

## Grade detail

`detections.grade_detail` has integer point values for coverage, spatial, agreement, attribution, and margin; a total; applied caps; and a rationale string for each dimension.

## Availability and model versions

`detections.data_availability` records optical windows, SAR scene count, ground tier, peer/control counts, official/hazard availability, and missing evidence. `detections.model_versions` records engine, `config_sha`, pipeline commit, embedding model, and report template version.

## API shell responses

The stage-owned implementation endpoints return HTTP 501 with `{"detail":"owned by stage N"}` until their owning stage implements them. `GET /health` returns `{"status":"ok","db":<boolean>,"config_sha":"<sha256>"}`.
