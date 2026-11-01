# Reconciliation AI — Relay Work Specification (4 Owners)

> **Project:** Reconciliation AI — Maharashtra Flood Compensation Quality-Assurance Layer
> **Demo event:** Pune District / Khadakwasla release flood, 24–26 July 2024
> **Source documents:** `reconciliation_ai_implementation_v3.md` (the "v3 spec") and `reconciliation_ai_detailed_implementation_plan.md` (the "detailed plan")
> **Working model:** *Relay.* Person 1 finishes and hands over; Person 2 builds on that; Person 3 builds on that; Person 4 finishes the project.
> **Status legend (same as v3):** ✅ verified · 🔎 unverified · 🧪 synthetic · 🎯 initial setting to be tuned · 🗺️ roadmap

---

## 0. How to use this document

1. **Everyone reads Sections 1 and 2.** They define the relay, the shared contracts and the decisions that remove ambiguity from the source documents.
2. **Each person then reads only their own stage** (Section 3, 4, 5 or 6) plus the stage before theirs, because that is where their input comes from.
3. **Every work package (WP) has the same shape:** purpose, files, exact specification, acceptance criteria, estimated hours. If a WP says "acceptance criteria", it is not done until each line is demonstrably true.
4. **Nothing in this file overrides the v3 spec silently.** Where this document changes or completes the spec, the change is listed in Section 2.5 with an ID (`D-1`, `D-2`, …) and referenced from the WP that uses it.
5. **Hour estimates are relative** (±20%). They exist so that the four stages stay roughly equal, not to be used as deadlines.

---

## 1. Relay overview

### 1.1 The four stages

| Stage | Owner | Title | Est. hours | Receives | Hands over |
|---|---|---|---|---|---|
| 1 | **Person 1** | Data Foundation & Satellite Evidence | 35 | The two source documents | Running database + API shell + all 450 parcels with satellite evidence, hazard context and simulated official records |
| 2 | **Person 2** | Ground Evidence: Photo Verifier & Farmer PWA | 32 | Stage 1 snapshot | Stage 1 snapshot + verified farmer photos and ground estimates, including the planted fraud cases |
| 3 | **Person 3** | Decision Engine, Audit & Reports | 36 | Stage 2 snapshot | Stage 2 snapshot + a `detections` row, grade, factors, report and audit chain for every case |
| 4 | **Person 4** | Officer Dashboard, Benchmark & Demo | 33 | Stage 3 snapshot | The finished, demo-ready project |

### 1.2 Flow

```text
 P1: Data Foundation            P2: Ground Evidence            P3: Decision Engine            P4: Presentation
 ───────────────────────        ───────────────────────        ───────────────────────        ───────────────────────
 schema, Docker, config  ──►    photo verifier          ──►    reconcile + detectors   ──►    read APIs + dashboard
 rasters, HAND/TWI              farmer PWA (Marathi)           factors + grade                 injection benchmark
 satellite pipeline             ground estimates               audit hash chain                fairness monitor
 hazard context                 demo photo bundles             bilingual reports               pitch + demo
 450 parcels + officials        fraud scenarios                /analyze /report /audit         offline rehearsal
        │                              │                              │                              │
        ▼                              ▼                              ▼                              ▼
  stage1.dump + README           stage2.dump + README           stage3.dump + README           final project
  (EXIT GATE 1)                  (EXIT GATE 2)                  (EXIT GATE 3)                  (EXIT GATE 4)
```

### 1.3 Why this order

Evidence flows in one direction: **satellite → ground → decision → presentation**. Each stage consumes only what the previous stage produced. Nobody ever needs something from a later stage, so nobody blocks anybody.

### 1.4 The relay's cost, and how it is managed

* The elapsed time is the **sum** of the four stages (about 136 engineer-hours), not the longest stage. At about 7 productive hours per day each stage takes roughly 5 working days, so plan for about **4 working weeks end to end** (20 working days, including handoff walk-throughs). If people can only give half-days, double it. Section 9 has the day-by-day schedule.
* A bad assumption made in Stage 1 may not surface until Stage 3 runs the detectors. To catch this early, **Person 3 runs a 10-parcel smoke test on Stage 1's snapshot while Person 2 is still working** (see WP-3.0).
* People who are waiting are not idle. Section 7 lists "waiting-time work" for each person: reading their stage, writing tests from the spec, and reviewing the previous handoff.

---

## 2. Global contracts (frozen before Person 1 starts)

These are agreed **once**, in a single 60-minute meeting of all four people, and committed under `contracts/`. After that they change only through `contracts/CHANGELOG.md` (Section 2.8).

### 2.1 Repository layout and stage ownership

The tree below extends the detailed plan's layout. New items are marked `(new)`. The comment shows which stage creates the item.

```text
reconciliation-ai/
├── Makefile                             (new) P1 creates; every stage adds its targets
├── docker-compose.yml                   (new) P1
├── contracts/                           (new) frozen in kickoff meeting
│   ├── enums.md
│   ├── json_shapes.md
│   ├── decisions.md                     # Section 2.5 of this document, copied verbatim
│   └── CHANGELOG.md
├── handoffs/                            (new) one folder per stage
│   ├── stage1/ {README.md, stage1.dump}
│   ├── stage2/ {README.md, stage2.dump}
│   ├── stage3/ {README.md, stage3.dump}
│   └── stage4/ {README.md}
├── config/
│   └── defaults.yaml                    # P1 creates; any stage may tune its own keys
├── sql/
│   ├── 01_extensions_and_schema.sql     # P1
│   ├── 02_frustum_and_spatial.sql       # P2
│   ├── 03_audit_hash_chain.sql          # P3
│   └── 04_seed_pune_july2024.sql        # P1 (generated by scripts/generate_seed.py)
├── scripts/                             (new)
│   ├── prepare_rasters.py               # P1
│   ├── generate_seed.py                 # P1
│   ├── plant_anomalies.py               # P1
│   ├── clone_event_for_v2.sql           # P1
│   ├── ingest_ground_scenarios.py       # P2
│   ├── analyze_all.py                   # P3
│   └── smoke.py                         # P4
├── data/
│   ├── rasters/                         # P1 (list in the detailed plan §1.1)
│   └── hazard/                          # P1
├── benchmark/                           (new)
│   ├── manifest.json                    # P1 writes (what was planted where)
│   ├── ground_scenarios.json            # P1 writes the claims, P2 realises them as photos
│   └── results/                         # P4 writes
├── fixtures/                            (new) small JSON files used for tests and UI offline mode
│   ├── detections/                      # P3 writes (one per tier)
│   └── case_detail/                     # P3 writes, P4 consumes
├── pipeline/                            # P1
├── backend/
│   ├── main.py, db.py, models.py        # P1 creates the shell; P4 extends models.py
│   ├── config.py                        (new) P1 — typed loader for defaults.yaml
│   ├── routers/                         (new)
│   │   ├── cases.py                     # P4  (POST /cases, GET /cases/{id}, POST /cases/{id}/review)
│   │   ├── ground.py                    # P2  (POST /cases/{id}/ground)
│   │   ├── analyze.py                   # P3  (POST /cases/{id}/analyze)
│   │   ├── reports.py                   # P3  (GET /cases/{id}/report)
│   │   ├── audit.py                     # P3  (GET /audit/verify)
│   │   └── events.py                    # P4  (GET /events/{id}/queue, /fairness)
│   ├── services/
│   │   ├── photo_verifier.py            # P2
│   │   ├── ground_estimate.py           (new) P2
│   │   ├── embeddings.py                (new) P2
│   │   ├── reconciler.py                # P3
│   │   ├── detectors.py                 (new) P3
│   │   ├── peers.py                     (new) P3
│   │   ├── grading.py                   (new) P3
│   │   ├── factors.py                   # P3
│   │   ├── reporter.py                  # P3
│   │   └── audit.py                     # P3
│   └── templates/ {report_en.j2, report_mr.j2}   # P3
├── frontend/                            # P4
├── pwa/                                 # P2
└── tests/
    ├── test_unclipped_did.py            # P1
    ├── test_strip_parcel_weights.py     # P1
    ├── test_sar_gate.py                 (new) P1
    ├── test_seed_integrity.py           (new) P1
    ├── test_photo_anti_spoofing.py      # P2
    ├── test_ground_estimate.py          (new) P2
    ├── test_pooling_and_detectors.py    # P3
    ├── test_factors_and_grade.py        (new) P3
    ├── test_report_verifier.py          # P3
    ├── test_audit_hash_chain.py         (new, see D-7) P3
    ├── test_api_contract.py             (new) P4
    └── run_injection_benchmark.py       # P4 (moved from the detailed plan's Track D; P1 only prepares its data)
```

### 2.2 Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | `ruff` + `black` configured by P1 |
| Database | PostgreSQL 16 + PostGIS + pgcrypto + pgvector | Single Docker service; boots in under 15 s |
| API | FastAPI + Uvicorn, Pydantic v2, SQLAlchemy 2 (async) or `psycopg[binary]` | Pick one in the kickoff meeting and use it everywhere |
| Geospatial | `numpy`, `scipy`, `rasterio`, `shapely`, `pyproj`, `scikit-image`, `scikit-learn` (KMeans) | `scikit-learn` is added to the detailed plan's list because Step 1.2 needs `KMeans` |
| Vision | `opencv-python-headless`, `Pillow`, `imagehash`, `onnxruntime` (preferred) or `open-clip-torch` | CPU-only |
| Templates | `jinja2` | |
| Frontends | React 18 + TypeScript + Vite; Leaflet (dashboard); `vite-plugin-pwa` (PWA) | |
| Tests | `pytest`, `httpx`, `pytest-asyncio` | UI: `vitest` + optional Playwright |
| Task runner | `make` | Every stage adds its own targets |

### 2.3 Enumerations (single source of truth)

| Enum | Allowed values |
|---|---|
| `tier` | `PRIORITY_REVIEW`, `REVIEW`, `NOTE`, `CONSISTENT`, `INSUFFICIENT_EVIDENCE` |
| `grade` | `A`, `B`, `C`, `D` |
| `pooling_status` | `OK`, `SOURCE_CONFLICT`, `SAT_ONLY`, `GROUND_ONLY`, `NO_OBSERVATION` (see D-1) |
| `boundary_crossing` | `NONE`, `SAT_UNDER_RISK`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `OVER_RISK` |
| `observed_estimates.source` | `satellite`, `ground` |
| `scene_observations.sensor` | `S2_IMMEDIATE`, `S2_DELAYED`, `S1_SAR` |
| `photos.verification_tier` | `1`, `2`, `3` |
| `parcels.role` | `case`, `control` (see D-8) |
| `plausibility` | `LOW`, `MODERATE`, `HIGH` |
| `factor.status` | `TRIGGERED`, `NOT_TRIGGERED`, `CANNOT_ASSESS` |
| Factor codes (12) | `LATE_ASSESSMENT`, `PEER_INCONSISTENCY`, `BLANKET_PANCHNAMA_CLUSTER`, `PARTIAL_PARCEL_SUBMERGENCE`, `SILT_RECOVERY_OBSERVED`, `DELAYED_WATERLOGGING_ROT`, `DISCHARGE_EXPOSURE`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `PHOTO_INTEGRITY_ALERT`, `CROP_MISMATCH`, `SOURCE_CONFLICT`, `NON_FLOOD_CAUSE_POSSIBLE` |
| Satellite flags (in `quality.flags`) | `SILT_RECOVERY_OBSERVED`, `DELAYED_WATERLOGGING_ROT`, `SMALL_PARCEL_LIMITATION`, `LOW_CLEAR_FRACTION`, `STANDING_WATER_AT_SCENE` |
| Photo flags (in `photos` / `ground.quality.flags`) | `OUTSIDE_PARCEL_BOUNDARY`, `FRUSTUM_OUTSIDE_PARCEL`, `PITCH_OUT_OF_RANGE`, `SINGLE_ANGLE_ONLY`, `BURST_PARALLAX_FAIL`, `SCREEN_MOIRE_SUSPECTED`, `DUPLICATE_PHOTO_EMBEDDING`, `CROP_MISMATCH`, `COMPASS_MISSING`, `GALLERY_UPLOAD`, `LOW_GPS_ACCURACY` |
| Review `decision` | `CONFIRM_FLAG`, `DISMISS_FLAG`, `ESCALATE`, `REQUEST_FIELD_VISIT` |
| Review `reason_code` | `SATELLITE_EVIDENCE_ACCEPTED`, `SATELLITE_EVIDENCE_REJECTED`, `PHOTO_FRAUD_SUSPECTED`, `ASSESSOR_BIAS_CONFIRMED`, `DATA_QUALITY_ISSUE`, `OTHER` |
| Language | `en`, `mr` |

### 2.4 JSON shapes that cross stages

These are the **only** places where one stage's output is parsed by another stage's code. Everything else is a plain column.

**A. `observed_estimates.quality` where `source='satellite'` (written by P1, read by P3 and P4)**

```json
{
  "loss_attr": 0.74,
  "area_dmg_frac": 0.78,
  "n_eff": 94.2,
  "clear_frac": 0.72,
  "water_frac_peak": 0.68,
  "water_frac_recession": 0.03,
  "window_used": 2,
  "flags": ["SILT_RECOVERY_OBSERVED"],
  "flags_assessable": true,
  "controls_n": 11,
  "controls_deficit_median": 0.02,
  "controls_deficit_range": [-0.09, 0.11],
  "onset_in_window": true,
  "first_scene_with_loss": "2024-08-03",
  "min_width_m": 32.0,
  "mode": "v3",
  "pixel_grid": {
    "type": "FeatureCollection",
    "features": [
      {"type": "Feature",
       "properties": {"attr_deficit": 0.81, "w": 1.0},
       "geometry": {"type": "Polygon", "coordinates": [[[73.8501, 18.4802], "…"]]}}
    ]
  }
}
```

Rules: `pixel_grid` coordinates are **EPSG:4326** (Leaflet-ready), rounded to 6 decimals, one polygon per 10 m Sentinel-2 pixel that has `w ≥ min_overlap_weight`. `water_frac_recession` is `null` when no later SAR scene exists (see D-10). `flags_assessable` is `false` when only one optical window is valid.

**B. `observed_estimates.quality` where `source='ground'` (written by P2, read by P3 and P4)**

```json
{
  "tier": 1,
  "excluded": false,
  "n_photos": 2,
  "n_photos_passing_all": 2,
  "photo_ids": ["0c1f…", "9a7b…"],
  "flags": [],
  "form": {
    "damaged_share_pct": 75,
    "water_depth_band": "KNEE",
    "water_days": 4,
    "crop_stage": "VEGETATIVE",
    "note_present": false
  },
  "form_consistency": "OK",
  "max_dup_similarity": 0.41,
  "frustum_overlaps": [0.84, 0.79],
  "locale": "mr"
}
```

Rules: if `excluded` is `true`, **P3 must ignore this row for pooling** but must still raise `PHOTO_INTEGRITY_ALERT` from `flags`. `value`, `sigma`, `ci_lo`, `ci_hi` columns are always filled so the NOT NULL constraints hold.

**C. `detections.factors` (written by P3, read by P4)** — always an array of exactly 12 objects, one per factor code, in the order of the enum above.

```json
{
  "code": "PEER_INCONSISTENCY",
  "status": "TRIGGERED",
  "evidence": {"peer_n": 20, "peer_external_frac": 0.60, "peer_median": 0.60, "mad": 0.09, "z": -3.0},
  "reason": null
}
```

`reason` is a short machine-readable string (e.g. `"INSUFFICIENT_PEERS"`) only when `status` is `CANNOT_ASSESS`.

**D. `detections.grade_detail`**

```json
{
  "points": {"coverage": 3, "spatial": 2, "agreement": 2, "attribution": 2, "margin": 1},
  "total": 10,
  "caps_applied": [],
  "rationale": {
    "coverage": "Sentinel-2 clear 0.72 + verified ground (tier 1)",
    "spatial": "n_eff 94.2 ≥ 25",
    "agreement": "|0.78−0.75| ≤ σ_comb 0.164",
    "attribution": "11 controls, onset in window, plausibility HIGH",
    "margin": "ref interval [0.67, 0.86] does not straddle 0.33"
  }
}
```

**E. `detections.data_availability`**

```json
{"sentinel2_windows": [1, 2], "sar_scenes": 2, "ground": "tier1", "peers": 20, "controls": 11,
 "official": true, "hazard": true, "missing": []}
```

**F. `detections.model_versions`**

```json
{"engine": "v3", "config_sha": "<sha256 of defaults.yaml>", "pipeline_commit": "<git sha>",
 "embedding_model": "mobileclip-s0-onnx", "template_version": "1"}
```

### 2.5 Decisions that close gaps in the source documents

While reading both documents we found contradictions, missing definitions and a few details that do not match the demo data. Each is resolved here. **These are binding for all four stages.**

| ID | Gap found in the source | Decision | Primary stage |
|---|---|---|---|
| **D-1** | `reconcile_observations()` can return `GROUND_ONLY`, but `detections.pooling_status` only lists `OK / SOURCE_CONFLICT / SAT_ONLY / NO_OBSERVATION` | Add `GROUND_ONLY` everywhere | P1 (DDL), P3 |
| **D-2** | Photo Tier 3 is described both as "σ = 0.35" and as "excluded" | **Tier 3 stays in pooling at σ = 0.35.** Only a duplicate embedding, a Moiré screen spoof or a failed burst-liveness check sets `excluded = true` | P2, P3 |
| **D-3** | v3 spec D9 puts "frustum overlap < 0.40" in Tier 2; the detailed plan puts it in Tier 3 and its test expects rejection | **Frustum computed and < 0.40 → Tier 3** (`FRUSTUM_OUTSIDE_PARCEL`). **Compass sensor missing → Tier 2** (`COMPASS_MISSING`). Outside parcel boundary (> 15 m) → Tier 3 (`OUTSIDE_PARCEL_BOUNDARY`) | P2 |
| **D-4** | v3 spec says Lucas-Kanade optical flow; the detailed plan's code uses Farneback | Use **Farneback** (`cv2.calcOpticalFlowFarneback`) as in the plan's code | P2 |
| **D-5** | Detector D: v3 §7.7 says "same assessor and same date", §2 says "or village" | Cohort = same `assessor_token` **and** (same `assessed_on` **or** same `village`) | P3 |
| **D-6** | Detector C: spec says partial Spearman controlling for HAND; plan says Spearman inside a ±2.5 m HAND band | Use the **HAND-band** version (simpler to test) | P3 |
| **D-7** | The plan says "6 test modules" but its tree lists 5 plus the benchmark; `test_audit_hash_chain.py` is missing | Add `tests/test_audit_hash_chain.py`, owned by P3 | P3 |
| **D-8** | "300 parcels … and 150 upland control parcels" is ambiguous | **300 case parcels** (80 of them 20–35 m wide strips) **plus 150 control-only parcels** = 450 rows in `parcels`. Add column `parcels.role` (`case` / `control`). Control parcels have no `cases` row | P1 |
| **D-9** | The windows "Day +1..+6" and "Day +7..+16" after peak (25 Jul) do not match the demo scenes of 3 Aug (= +9 d) and 13 Aug (= +19 d) | Make windows configurable and set them to match the data: **Window 1 = peak +1..+10, Window 2 = peak +11..+20** 🎯 (`satellite.window1_days`, `satellite.window2_days`) | P1 |
| **D-10** | The worked example quotes `water_frac = 0.03 by 8 Aug`, but only two SAR scenes are listed (15 Jul pre, 27 Jul peak) | P1 checks whether a third SAR scene near 8 Aug exists. If yes, add `s1_20240808_post_vv_vh.tif`. If no, `water_frac_recession` is `null` and `LATE_ASSESSMENT` is `CANNOT_ASSESS` on the SAR part | P1, P3 |
| **D-11** | "Expected NDVI" `E` and "bare NDVI" `B` are never defined | `E` = the pixel's **own pre-event NDVI** (18 Jul scene). `B` = `bare_ndvi_default` (0.12). Phenology drift is removed by the control subtraction (controls will show slightly negative or positive deficits, as in the worked example) | P1 |
| **D-12** | Which window supplies the final `V_sat` is unclear | Use **Window 2 if valid** (clear fraction ≥ 0.40), else Window 1. Silt-recovery and delayed-rot checks need both windows | P1 |
| **D-13** | Tier rules do not say what happens when only Detector C fires, or when Grade D coexists with a flag | **C alone → `NOTE`.** **Grade D → `INSUFFICIENT_EVIDENCE`** even if a detector fired (the detector results stay visible in factors) | P3 |
| **D-14** | The v3 spec cites a Grade rubric in §7.9, which is not in the document. The plan only lists dimension ranges | Numeric scoring rules are defined in WP-3.7 🎯 | P3 |
| **D-15** | Hazard context is "computed identically to v2", but v2 is not provided | The plausibility rule is defined in WP-1.5 🎯 | P1 |
| **D-16** | The v2-vs-v3 ablation table needs the old logic to run | Implemented as a **cloned event** `MH-2024-07-PUNE-V2`: P1's batch has `--mode v2` (−10 m buffer, clipped DiD, NDVI only, Otsu SAR); P3's `/analyze?mode=v2` skips the surfing guard, cross-assessor rule and Detector D | P1, P3, P4 |
| **D-17** | `min_peers: 8` exists in config but the behaviour below it is unspecified | Fewer than 8 peers → Detector B is `CANNOT_ASSESS` with reason `INSUFFICIENT_PEERS` (never silently "no flag") | P3 |
| **D-18** | `POST /cases/{id}/review` exists in the API list, but there is no table to store reviews | Add table `reviews` (see Section 3, WP-1.1) | P1 (DDL), P4 |
| **D-19** | The structured farmer form is never specified | Fields are defined in WP-2.6 | P2 |
| **D-20** | The satellite `quality` JSON has no place for onset, controls count or pixel grid | Defined in Section 2.4-A | P1 |
| **D-21** | `compute_subpixel_weights()` is annotated as returning `np.ndarray` but returns a tuple; its large-parcel threshold (0.65) differs from `min_overlap_weight` (0.50) | Return type is `tuple[np.ndarray, float]`. Add config keys `min_overlap_weight_large: 0.65` and `min_overlap_weight_strip: 0.50` | P1 |
| **D-22** | The monsoon makes clear Sentinel-2 scenes unlikely. The spec assumes 3 Aug and 13 Aug are usable | P1 must report the real `clear_frac` of each scene in the Stage 1 README. Parcels below `min_clear_fraction` get the flag `LOW_CLEAR_FRACTION` and Grade cannot exceed C (enforced in WP-3.7) | P1, P3 |

### 2.6 `config/defaults.yaml` (complete, with the additions from Section 2.5)

Created by P1 in WP-1.2. Values marked 🎯 are tuned later by the stage that owns the keyword.

```yaml
parcel:
  min_width_for_buffer_m: 35.0
  adaptive_buffer_m: 5.0
  min_overlap_weight_large: 0.65      # D-21
  min_overlap_weight_strip: 0.50      # D-21
  min_eff_pixels: 8.0
  high_reliability_eff_pixels: 25.0
  supersample: 5
peers:
  radius_km: 15.0
  sowing_window_days: 10
  observed_similarity: 0.15
  min_peers: 8
  max_candidates: 60
  min_external_assessor_frac: 0.50
controls:
  radius_km: [10.0, 25.0]
  min_controls: 5
  min_hand_m: 8.0                     # upland = well above the river
  max_sar_water_frac: 0.02
satellite:
  window1_days: [1, 10]               # D-9
  window2_days: [11, 20]              # D-9
  min_clear_fraction: 0.40
  bare_ndvi_default: 0.12
  denom_floor: 0.05
  damaged_area_pixel_threshold: 0.35
  standing_water_ndwi: 0.05
  silt_ndre_rebound_threshold: 0.12
  silt_w1_loss_min: 0.35
  silt_w2_loss_max: 0.25
  rot_w1_loss_max: 0.20
  rot_w2_loss_min: 0.35
  rot_ndmi_drop: 0.15
  bootstrap_block: 3
  bootstrap_n: 2000
  sigma_floor: 0.05
  interval_percentiles: [10, 90]
  onset_threshold: 0.15
  onset_window_days: [-2, 14]
sar:
  lee_window: 3
  ashman_d_min: 2.0
  open_water_vv_drop_db: -2.5
  open_water_vh_max_db: -20.0
  fallback_vv_drop_db: -3.0
  double_bounce_hand_max_m: 4.0
  double_bounce_ndvi_pre_min: 0.35
  double_bounce_ctrl_excess_db: 2.5
hazard:                               # D-15
  heavy_rain_mm: 64.5
  discharge_hand_pctile_max: 25.0
  low_plausibility_hand_pctile_min: 50.0
ground:
  sigma_tier1_verified: 0.14
  sigma_tier2_partial: 0.22
  sigma_tier3_unverified: 0.35
  photo_max_boundary_dist_m: 15.0
  photo_max_accuracy_m: 25.0
  frustum_range_m: 60.0
  frustum_half_angle_deg: 25.0
  frustum_min_overlap: 0.40
  pitch_min_deg: 65.0
  pitch_max_deg: 88.0
  min_angle_sep_deg: 35.0
  min_pos_sep_m: 15.0
  pgvector_dup_cosine_threshold: 0.92
  moire_max: 6.5
  parallax_ratio_min: 0.08
  fg_motion_range_px: [0.2, 45.0]
official:
  rounding_tolerance: 0.05
pooling:
  conflict_k: 2.0
  interval_z: 1.28
detectors:
  gap_note: 0.10
  gap_review: 0.20
  gap_priority: 0.25
  peer_z_note: 1.5
  peer_z_flag: 2.0
  mad_scale_floor: 0.05
  cluster_min_cases: 5
  cluster_max_iqr: 0.05
  cluster_min_gap: 0.20
  timing_rho: -0.40
  timing_p: 0.05
  timing_hand_band_m: 2.5
  timing_min_cohort: 10
  timing_radius_km: 25.0
  boundary: 0.33
grade:                                # D-14
  a_min: 8
  b_min: 6
  c_min: 4
report:
  llm_polish_enabled: false           # templates are the default; LLM text is optional
```

### 2.7 Handoff protocol

A handoff is **a database snapshot plus a one-page README**. It is not a conversation.

**Make targets every stage must support**

```makefile
make up           # start Postgres+PostGIS+pgvector (docker compose up -d --wait)
make restore S=1  # drop DB, restore handoffs/stage1/stage1.dump   (S=2, 3 likewise)
make snapshot S=1 # pg_dump -Fc into handoffs/stage1/stage1.dump
make test         # pytest -q tests/ (only the modules that exist so far)
make smoke        # added by P4 at the end; until then each stage runs its own smoke script
```

**Handoff README template (`handoffs/stageN/README.md`)** — the sender fills every heading:

```markdown
# Stage N Handoff — <name>, <date>
## 1. What is in this snapshot
Tables filled and row counts (copy the output of the `make counts` query).
## 2. How to start
`make up && make restore S=N` then the 3 commands that prove it works.
## 3. Contracts used
Enums and JSON shapes produced. Any deviation from Section 2.4 of the spec (should be none).
## 4. Known gaps and limitations
Real data limitations, e.g. scenes with low clear fraction, parcels with no controls.
## 5. Numbers measured in this stage (tagged real or 🧪)
## 6. Test results
Output of `make test` for the stage's modules.
## 7. Questions the next person is likely to ask
```

**Exit gate rule:** the next person starts only when the sender has (a) committed the snapshot and README, (b) run every acceptance line of the stage, and (c) had a 15-minute walk-through with the next person.

**Bug policy:** if a later stage finds a defect in an earlier stage's output, it opens an issue labelled `upstream-bug` assigned to the owner. The owner fixes it and re-issues the snapshot (version bump: `stage1.v2.dump`). The finder re-runs from that snapshot. Nobody patches another stage's tables by hand.

### 2.8 Working conventions

* **Branches:** `stage1/<topic>`, `stage2/<topic>`, … merged to `main` by the stage owner. `main` must always pass `make test` for finished stages.
* **CODEOWNERS:** exactly the ownership comments in Section 2.1.
* **Contract changes:** a one-paragraph entry in `contracts/CHANGELOG.md` with date, what changed, who is affected. The next-stage owner must acknowledge it in a comment.
* **Reproducibility:** every random process uses a fixed seed (`random_state=42`; `numpy.random.default_rng(42)`). Re-running a stage yields identical rows.
* **Idempotency:** every writer uses `INSERT … ON CONFLICT (…) DO UPDATE`. Re-running a script never duplicates data.
* **Number honesty:** no performance number is written in any README or slide unless it was measured, and it is tagged "real" or 🧪 (synthetic).
* **Privacy:** never store Aadhaar. `farmer_ref` is an opaque token or Agri Stack Farmer ID only.
* **Commit hygiene:** raster files and dumps are tracked with Git LFS or kept out of Git and described by a `checksums.txt`; the README names where to get them.

---

# 3. STAGE 1 — Person 1: Data Foundation & Satellite Evidence

**Mission.** Build the platform everything else sits on (database, config, API shell), then produce trustworthy per-parcel **satellite evidence**, **hazard context** and a realistic **simulated official-assessment world** with planted anomalies.

**You receive:** the two source documents and the contracts of Section 2.
**You hand over:** `handoffs/stage1/stage1.dump` and its README (Exit Gate 1).
**You never touch:** `photos`, ground `observed_estimates`, `detections`, `audit_log`, `frontend/`, `pwa/`.

### 3.0 Work-package summary

| WP | Title | Hours |
|---|---|---|
| 1.1 | Environment, Docker, database schema | 3 |
| 1.2 | `config/defaults.yaml` and typed loader | 1 |
| 1.3 | FastAPI shell and router stubs | 3 |
| 1.4 | Raster preparation (Sentinel-2, Sentinel-1, HAND/TWI) | 4 |
| 1.5 | Hazard context and plausibility | 2 |
| 1.6 | Parcel preparation (sub-pixel weights, spectral clusters, controls) | 4 |
| 1.7 | Optical satellite loss (unclipped DiD, dual metrics, windows, bootstrap) | 6 |
| 1.8 | SAR inundation (Lee, Ashman's D, bounds, double bounce) | 3 |
| 1.9 | Batch runner `run_batch_event.py` (v3 and v2 modes) | 3 |
| 1.10 | Seed world: 450 parcels, simulated officials, planted anomalies | 4 |
| 1.11 | Tests, snapshot and handoff README | 2 |
| | **Total** | **35** |

---

### WP-1.1 Environment, Docker and database schema (3 h)

**Purpose.** One command starts the whole data layer; the schema is the contract for every later stage.

**Files.** `docker-compose.yml`, `Makefile`, `sql/01_extensions_and_schema.sql`, `.env.example`, `requirements.txt`, `pyproject.toml`.

**Specification.**

1. `docker-compose.yml` runs one service, `db`, from an image that contains PostGIS and pgvector (e.g. `pgvector/pgvector:pg16` plus PostGIS installed, or a small custom Dockerfile). Expose port 5432; add a healthcheck (`pg_isready`); `docker compose up -d --wait` must return in under 15 seconds on a warm machine.
2. `sql/01_extensions_and_schema.sql` contains, in this order:
   * `CREATE EXTENSION IF NOT EXISTS postgis; pgcrypto; vector;`
   * Every `CREATE TABLE` and index from **v3 spec §6**, copied verbatim **except** for these changes:
     * `parcels`: add `role TEXT NOT NULL DEFAULT 'case' CHECK (role IN ('case','control'))` (D-8). Add `CREATE INDEX idx_parcels_role ON parcels(role)`.
     * `detections.pooling_status`: add `CHECK (pooling_status IN ('OK','SOURCE_CONFLICT','SAT_ONLY','GROUND_ONLY','NO_OBSERVATION'))` (D-1).
     * `detections.tier`: add `CHECK (tier IN ('PRIORITY_REVIEW','REVIEW','NOTE','CONSISTENT','INSUFFICIENT_EVIDENCE'))`; `detections.grade`: `CHECK (grade IN ('A','B','C','D'))`.
     * `detections.boundary_crossing`: add the four-value `CHECK` from Section 2.3.
     * `photos.verification_tier`: add `CHECK (verification_tier IN (1,2,3))`.
     * `events`: no change, but the seed must set `peak_date = '2024-07-25'`.
   * New table `reviews` (D-18):

     ```sql
     CREATE TABLE reviews (
       review_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       case_id           UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
       officer_token     TEXT NOT NULL,
       decision          TEXT NOT NULL CHECK (decision IN
                           ('CONFIRM_FLAG','DISMISS_FLAG','ESCALATE','REQUEST_FIELD_VISIT')),
       reason_code       TEXT CHECK (reason_code IN
                           ('SATELLITE_EVIDENCE_ACCEPTED','SATELLITE_EVIDENCE_REJECTED',
                            'PHOTO_FRAUD_SUSPECTED','ASSESSOR_BIAS_CONFIRMED',
                            'DATA_QUALITY_ISSUE','OTHER')),
       priority_override BOOLEAN NOT NULL DEFAULT FALSE,
       note              TEXT,
       created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
       CHECK (NOT priority_override OR reason_code IS NOT NULL)
     );
     CREATE INDEX idx_reviews_case ON reviews(case_id, created_at DESC);
     ```
   * A convenience view used by Stages 3 and 4, so nobody re-writes the same join:

     ```sql
     CREATE VIEW v_case_base AS
     SELECT c.case_id, c.event_id, c.parcel_id, c.farmer_ref, c.status,
            p.survey_no, p.village, p.taluka, p.district, p.area_ha, p.min_width_m,
            p.geom, p.geom_utm, p.crop, p.sowing_date, p.spectral_cluster, p.soil_class,
            o.damage_lo, o.damage_hi, (o.damage_lo + o.damage_hi) / 2.0 AS official_mid,
            o.assessed_on, o.assessor_token,
            (o.assessed_on - e.peak_date) AS delay_days,
            h.hand_m, h.twi, h.hand_pctile_in_taluka, h.plausibility, h.rain_imd_class
     FROM cases c
     JOIN parcels p ON p.parcel_id = c.parcel_id
     JOIN events  e ON e.event_id  = c.event_id
     LEFT JOIN official_assessments o ON o.case_id = c.case_id
     LEFT JOIN hazard_context h       ON h.case_id = c.case_id;
     ```
   * `sql/01_…sql` **does not** contain the audit trigger (Stage 3, `03_…sql`) or `compute_frustum_overlap()` (Stage 2, `02_…sql`). Both later scripts must be runnable on top of `01`.
3. `Makefile` targets: `up`, `down`, `schema` (applies `sql/01` then, if present, `02`, `03`), `counts` (prints row counts of all tables), `snapshot`, `restore`, `test`.
4. `requirements.txt` pins versions for everything in Section 2.2. Check that `pip install -r requirements.txt` works on a clean Python 3.11 virtualenv.

**Acceptance criteria.**
* `make up && make schema` works on a clean checkout; running `make schema` twice does not fail (use `IF NOT EXISTS`/`CREATE OR REPLACE` where possible, or drop and recreate in `make schema`).
* `\d+ parcels` shows `role`; `\d+ reviews` exists; inserting `pooling_status='GROUND_ONLY'` succeeds; inserting `'FOO'` fails.
* `SELECT * FROM v_case_base LIMIT 1;` runs (empty result is fine).

---

### WP-1.2 Configuration (1 h)

**Files.** `config/defaults.yaml`, `backend/config.py`.

**Specification.**
1. Copy the YAML from Section 2.6 verbatim into `config/defaults.yaml`.
2. `backend/config.py` exposes `get_config() -> Config`, a cached, **frozen** dataclass tree (use `pydantic.BaseModel` with `model_config = {"frozen": True}`), one class per YAML top-level section. Access must be typed: `cfg.ground.frustum_min_overlap`, not `cfg["ground"]["frustum_min_overlap"]`.
3. `config_sha() -> str` returns the SHA-256 of the YAML bytes; stages 3 and 4 store it in `model_versions.config_sha`.
4. Environment override: if `RECON_CONFIG` is set, load that file instead. Fail loudly (raise) if a key is missing.

**Acceptance criteria.** A unit test loads the config, asserts `cfg.detectors.boundary == 0.33`, and asserts that mutating a field raises.

---

### WP-1.3 FastAPI shell and router stubs (3 h)

**Files.** `backend/main.py`, `backend/db.py`, `backend/models.py`, `backend/routers/*.py` (stubs only).

**Specification.**
1. `db.py`: one async connection pool (`asyncpg` via SQLAlchemy, or `psycopg_pool`) created at startup, closed at shutdown. Provide an async context manager `transaction()` that yields a connection inside `BEGIN … COMMIT` and rolls back on any exception. Set `SET TIME ZONE 'UTC'` on every connection (important for the audit hash in Stage 3).
2. `main.py`: create the app, enable CORS for `http://localhost:5173` (dashboard) and `http://localhost:5174` (PWA), register **all six routers** from Section 2.1 (each file exists, each declares its routes and returns `501 Not Implemented` with body `{"detail": "owned by stage N"}`). `GET /health` returns `{"status":"ok","db":true,"config_sha":"…"}`.
3. `models.py`: Pydantic v2 models for the JSON shapes in Section 2.4 (`SatelliteQuality`, `GroundQuality`, `FactorResult`, `GradeDetail`, `DataAvailability`, `ModelVersions`) and for the enums. These models are the programmatic form of the contract; the later stages **import** them rather than redefining them.
4. Add an OpenAPI export: `make openapi` writes `contracts/openapi.json`. Stage 4 uses it to generate the TypeScript client.

**Acceptance criteria.** `uvicorn backend.main:app` starts in under 3 s; `/health` returns `db: true`; `/docs` lists all nine endpoints of the v3 spec §8 with `501` responses.

---

### WP-1.4 Raster preparation (4 h)

**Purpose.** Produce the offline raster library so the demo never needs the internet.

**Files.** `scripts/prepare_rasters.py`, `data/rasters/*.tif`, `data/rasters/checksums.txt`, `data/rasters/SCENES.md`.

**Specification.**

1. **Area of interest.** One bounding box covering the Mula-Mutha reach through Haveli and Daund, large enough for 300 flood-reach parcels and 150 upland controls (roughly 40 × 40 km). Record it in `SCENES.md`.
2. **Sentinel-2 L2A scenes** (these three, or the nearest cloud-usable alternatives; **record the actual dates** — D-22):
   * `s2_20240718_pre.tif` (pre-event), `s2_20240803_post1.tif` (Window 1), `s2_20240813_post2.tif` (Window 2).
   * Band order inside each file (8 bands, in this exact order): `B02, B03, B04, B05, B08, B8A, B11, SCL`.
   * All files: EPSG:32643, 10 m pixel grid **aligned to the same origin** (check with `rasterio` that all six rasters have identical `transform` and `shape`).
   * Convert digital numbers to reflectance with `(DN + BOA_ADD_OFFSET) / 10000`. For scenes processed with baseline ≥ 04.00 the offset is −1000; read it from the scene metadata rather than assuming. Clip reflectance to [0, 1.2].
   * Resample the 20 m bands (`B05, B8A, B11`) to 10 m with **bilinear** interpolation; resample `SCL` with **nearest neighbour**. Do not interpolate classes.
3. **Sentinel-1A GRD:** `s1_20240715_pre_vv_vh.tif` and `s1_20240727_peak_vv_vh.tif`, 2 bands (`VV`, `VH`), calibrated σ⁰ in **dB**, terrain-corrected, 10 m, EPSG:32643, same grid. Check whether a pass near 8 Aug exists; if so add `s1_20240808_post_vv_vh.tif` (D-10), otherwise write "not available" in `SCENES.md`.
4. **Terrain:** from Copernicus GLO-30 (or FABDEM/SRTM fallback) compute **HAND** (metres above nearest drainage) and **TWI**. Save `terrain_hand_twi_32643.tif` with two bands (`HAND_m`, `TWI`) on the same 10 m grid. For HAND use a drainage-initiation threshold that reproduces the main Mula-Mutha channel (document the threshold). Tools: `pysheds` (conditioning, flow direction, accumulation, HAND) or WhiteboxTools.
5. **Scene report.** `SCENES.md` must contain, for every optical scene: acquisition date, tile ID, **fraction of AOI with clear SCL** (classes 4, 5, 6, 7 are usable; 0, 1, 3, 8, 9, 10 are not), and cloud notes. This is the honest answer to D-22.
6. `checksums.txt` lists SHA-256 of every raster so the team can verify copies.

**Acceptance criteria.**
* A script `scripts/check_rasters.py` (run by `make check-rasters`) asserts: identical CRS/transform/shape across all six rasters; band counts correct; no NaN in HAND inside the AOI; SCL values only in 0–11.
* `SCENES.md` lists a clear fraction for each Sentinel-2 scene. If any is below 0.40 over the flood reach, say so in the handoff README; do not hide it.

---

### WP-1.5 Hazard context and plausibility (2 h)

**Files.** `data/hazard/imd_imerg_pune_202407.json`, `data/hazard/cwc_wrd_khadakwasla.json`, `pipeline/hazard_extractor.py`.

**Specification.**

1. **Rain JSON schema** (`imd_imerg_pune_202407.json`):

   ```json
   {"source": "IMD 0.25° / IMERG V07 0.1°", "synthetic": false,
    "cells": [{"lat": 18.50, "lon": 73.85, "max_24h_mm": 118.4, "max_24h_date": "2024-07-25",
               "imd_class": "VERY_HEAVY", "percentile": 99.2, "antecedent_30d_percentile": 91.0}]}
   ```

   IMD 24-hour classes (mm): `VERY_LIGHT` 0.1–2.4, `LIGHT` 2.5–15.5, `MODERATE` 15.6–64.4, `HEAVY` 64.5–115.5, `VERY_HEAVY` 115.6–204.4, `EXTREMELY_HEAVY` ≥ 204.5. Verify the boundaries against the IMD publication before presenting (🔎). If real gridded data cannot be obtained in time, fill cells with clearly labelled synthetic values and set `"synthetic": true`; the dashboard and reports will display the tag.
2. **Discharge JSON** (`cwc_wrd_khadakwasla.json`): release of about 35,000–40,000 cusecs on 25 Jul 2024 (✅ per v3 spec §5), source citation, affected reach as a polyline in EPSG:4326, and a `reach_buffer_m` (e.g. 1,500 m) within which a parcel counts as exposed.
3. **`hazard_extractor.py`** exposes:

   ```python
   def extract_hazard(parcel_row, hand_raster, twi_raster, rain_cells, discharge, taluka_hand_values) -> dict
   ```

   returning every column of `hazard_context`:
   * `rain_24h_max_mm`, `rain_imd_class`, `rain_percentile`, `antecedent_30d_percentile`: nearest rain cell to the parcel centroid.
   * `hand_m`, `twi`: **area-weighted mean** of HAND and TWI over the parcel's pixels (use the weights from WP-1.6).
   * `hand_pctile_in_taluka`: percentile rank of this parcel's `hand_m` among all case parcels in the same taluka (0 = lowest, lowest HAND is nearest the river).
   * `discharge_exposure` (JSON): `{"release_cusecs": 37500, "date": "2024-07-25", "distance_to_river_m": …, "in_reach": true|false}`. `distance_to_river_m` = distance to the nearest raster cell with `HAND ≤ 0.5 m` that lies inside the reach buffer.
   * `soil_class`: copied from `parcels.soil_class`.
   * `plausibility` per **D-15**:

     ```text
     HIGH      if (rain_imd_class in {HEAVY, VERY_HEAVY, EXTREMELY_HEAVY} or rain_24h_max_mm >= hazard.heavy_rain_mm)
               or (discharge_exposure.in_reach and hand_pctile_in_taluka <= hazard.discharge_hand_pctile_max)
     LOW       if rain_imd_class in {VERY_LIGHT, LIGHT, MODERATE}
               and not discharge_exposure.in_reach
               and hand_pctile_in_taluka >= hazard.low_plausibility_hand_pctile_min
     MODERATE  otherwise
     ```

4. Hazard values are **never** used to change a damage number. They only feed `plausibility`, `DISCHARGE_EXPOSURE` and `NON_FLOOD_CAUSE_POSSIBLE` in Stage 3.

**Acceptance criteria.** Unit tests: a parcel with HAND 1 m inside the reach and 118 mm rain → `HIGH`; a parcel with HAND 15 m, 20 mm rain, outside reach → `LOW`; a mixed case → `MODERATE`.

---

### WP-1.6 Parcel preparation (4 h)

**Files.** `pipeline/parcel_prep.py`, `tests/test_strip_parcel_weights.py`.

**Specification.** Four functions.

1. **`compute_subpixel_weights(parcel_utm, window_transform, out_shape) -> tuple[np.ndarray, float]`**
   Implement exactly the version in the detailed plan §2.1 Step 1.1, with these corrections (D-21):
   * Return type is `tuple[np.ndarray, float]` (weights, `min_width_m`).
   * Large parcels (`min_width_m ≥ 35`): apply a −5 m buffer (if the result is empty, fall back to the original polygon), keep pixels with `w ≥ min_overlap_weight_large` (0.65), weight = `w`.
   * Strip parcels (`min_width_m < 35`): no negative buffer, keep pixels with `w ≥ min_overlap_weight_strip` (0.50), weight = `w²`.
   * Supersample factor comes from `cfg.parcel.supersample` (5).
   * Also compute `min_width_m` robustly: `minimum_rotated_rectangle` edge lengths → the **smaller** of the two distinct edge lengths (there are four edges but only two distinct values).
   * Provide `effective_pixels(weights) -> float` = `sum(w)`, and `reliability(n_eff) -> "HIGH"|"MEDIUM"|"LOW"` using 25 and 8.
2. **`assign_spectral_clusters(ndvi_series_by_parcel, ndmi_last_by_parcel, taluka_of_parcel) -> dict[parcel_id, int]`**
   Per taluka, build `v_p = [NDVI_t1..NDVI_t4, NDMI_t4]` per detailed plan Step 1.2 (late May, mid-June, early July, mid-July). Standardise columns (z-score) before KMeans. Run `KMeans(n_clusters=6, random_state=42, n_init=10)`. Write the cluster id to `parcels.spectral_cluster` for **all** parcels, not only those with missing crop (so peers can fall back at any time). If fewer than four pre-event scenes are available in the raster library, use the available subset and record the count in the README. Document which scenes were used.
3. **`select_controls(parcel_row, all_parcels, sar_water_frac_by_parcel, hand_by_parcel, cfg) -> list[parcel_id]`**
   * Candidates: `role='control'` **or** any case parcel with `hand_m ≥ controls.min_hand_m` and `sar_water_frac ≤ controls.max_sar_water_frac`.
   * Same crop and sowing date within ±10 days; if the parcel's `crop`/`sowing_date` is NULL, use the same `spectral_cluster`.
   * Distance within 10 km first; if fewer than `controls.min_controls` (5) are found, widen to 25 km. If still fewer than 5, return what exists and let the caller set `controls_n` honestly (Stage 3 will reduce the Attribution score).
4. **`compute_pixel_stack(parcel_utm, rasters, window)`** returns the aligned arrays (indices later computed in WP-1.7) plus the weights for the window around the parcel (bounds snapped to the 10 m grid, with a 1-pixel margin).

**Acceptance criteria.**
* `test_strip_parcel_weights.py`: a 22 m × 320 m polygon rotated 0°, 17°, and 45° each returns `n_eff ≥ 18.0` and `min_width_m ≈ 22 ± 0.5`; a 60 m × 60 m polygon returns the buffered interior and `min_width_m ≈ 60`; no case returns an all-zero weight array.
* Spectral clustering is deterministic: two runs give identical labels.
* `select_controls` returns at least 5 controls for ≥ 95% of case parcels in the seed world (check after WP-1.10).

---

### WP-1.7 Optical satellite loss (6 h)

**Files.** `pipeline/optical_loss.py`, `tests/test_unclipped_did.py`.

This is the scientific core of Stage 1. Implement the following functions in this order.

1. **Indices** (all inputs reflectance 0–1):
   * `NDVI = (B08 − B04) / (B08 + B04)`
   * `NDRE = (B8A − B05) / (B8A + B05)`
   * `NDMI = (B8A − B11) / (B8A + B11)`
   * `NDWI = (B03 − B08) / (B03 + B08)`
   * Guard divisions: where the denominator is `< 1e-6`, output `NaN`.
2. **Valid mask:** `valid = ~isin(SCL, [0, 1, 3, 8, 9, 10])`. Record `clear_frac = Σ(w · valid) / Σ(w)` per parcel per scene.
3. **Water mask (Window 1 only):** `water = NDWI > cfg.satellite.standing_water_ndwi (0.05)`. Compute `water_frac_optical = Σ(w · water · valid) / Σ(w · valid)`. Water pixels are **excluded** from the deficit of that window (spec D3: "never treat submerged pixels as final vegetation loss").
4. **`compute_satellite_loss(...)`** — copy the function from **v3 §7.2** unchanged (it already implements the unclipped DiD, `loss_attr`, `area_dmg_frac`, `v_sat = max(...)`). Add: a `valid` mask argument for SCL/water, and input validation (shapes equal; weights non-negative). Expected NDVI per pixel `E_i` = that pixel's pre-event NDVI (D-11); `B_i = cfg.satellite.bare_ndvi_default`.
5. **`parcel_window_metrics(pixels, controls) -> dict`** — for one window returns:
   * `deficit_farm` (unclipped), `deficit_controls` (unclipped median over control parcels' **parcel-level** unclipped deficits), `loss_attr`, `area_dmg_frac`, `v_sat`, `n_eff`, `clear_frac`, `water_frac_optical`, and the means `ndvi_obs`, `ndre_obs`, `ndmi_obs`.
   * Control parcels are processed through the same function with the same window and weights procedure, but **without** subtracting a control median (their raw unclipped deficit is the output).
6. **Window logic (D-9, D-12).**
   * Select the scene for each window by date: Window 1 = `peak + 1 … peak + 10` days, Window 2 = `peak + 11 … peak + 20` days. If several scenes qualify, take the one with the highest `clear_frac`. Write `S2_IMMEDIATE` and `S2_DELAYED` rows to `scene_observations`.
   * `window_used = 2` if Window 2 exists and `clear_frac ≥ min_clear_fraction`, else `1`. If neither window is valid: no satellite estimate is written at all (the case later gets `NO_OBSERVATION` or `GROUND_ONLY` in Stage 3).
   * **Silt wash-off check** (needs both windows): if `L_attr(1) ≥ silt_w1_loss_min (0.35)` and `NDRE(2) − NDRE(1) ≥ silt_ndre_rebound_threshold (0.12)` and `L_attr(2) < silt_w2_loss_max (0.25)` → add flag `SILT_RECOVERY_OBSERVED`, `window_used = 2`.
   * **Delayed root-rot check** (needs both windows): if `L_attr(1) < rot_w1_loss_max (0.20)` and `L_attr(2) ≥ rot_w2_loss_min (0.35)` and `NDMI(2) − NDMI(1) ≤ −rot_ndmi_drop (0.15)` and `soil_class == 'vertisol'` → add flag `DELAYED_WATERLOGGING_ROT`, `window_used = 2`.
   * If only one window is valid, set `flags_assessable = false`.
   * Onset: `first_scene_with_loss` = the earliest post-event scene whose `L_attr ≥ onset_threshold (0.15)`; `onset_in_window` = whether `(scene_date − peak) ∈ onset_window_days [-2, 14]` **or** the scene is the first post-event scene available (state this in the README, because with only two scenes onset cannot be pinned more tightly).
7. **Block bootstrap (`bootstrap_sigma`)**:
   * Take the final window's pixel deficit grid. Tile it into non-overlapping **3 × 3 pixel blocks** (`cfg.satellite.bootstrap_block`); a partial edge block is kept as its own block.
   * Draw `n_boot = 2000` resamples **of blocks with replacement** (use `np.random.default_rng(42)`), recompute `v_sat` for each (holding the control median fixed), and take the 10th and 90th percentiles → `[V_sat,lo, V_sat,hi]`.
   * `σ_sat = max((V_sat,hi − V_sat,lo) / 2.56, cfg.satellite.sigma_floor)`. Example check: 0.67 and 0.89 give 0.0859.
   * If there are fewer than 4 blocks, skip the bootstrap and set `σ_sat = 0.10`, flagging `SMALL_PARCEL_LIMITATION`.
   * Also set `SMALL_PARCEL_LIMITATION` whenever `n_eff < 8`, and `LOW_CLEAR_FRACTION` when the used window's `clear_frac < 0.40` (D-22).
8. **`pixel_grid` export**: build the GeoJSON per Section 2.4-A. Convert each retained pixel's UTM square to EPSG:4326 with `pyproj`. `attr_deficit = pixel_deficit − deficit_controls`.
9. **Main entry point:**

   ```python
   def compute_parcel_satellite(parcel_row, rasters, controls_deficits, cfg, mode="v3") -> SatelliteResult
   ```

   `SatelliteResult` contains the `scene_observations` rows, the `observed_estimates` row (`value = v_sat`, `sigma`, `ci_lo`, `ci_hi`, `quality` per 2.4-A). `mode="v2"` reproduces the old behaviour for the ablation (D-16): fixed −10 m buffer, per-pixel loss clipped to [0, 1] **before** the control median, NDVI only, no windows logic, plain mean loss as `v_sat`.

**Acceptance criteria** (`tests/test_unclipped_did.py`):
* 100 synthetic control parcels with Gaussian NDVI noise `N(0, 0.06)` and no flood → mean and median `loss_attr` across them is `0.00 ± 0.01`. The same data through `mode="v2"` shows an upward bias of about `+0.06` (assert it is `> +0.03` to prove the test can detect the bug).
* Worked example reproduction: `E = 0.54, O = 0.22, B = 0.12` gives `deficit_farm = 0.762 ± 0.005`; with `d_ctrl = 0.02` → `loss_attr = 0.74 ± 0.01`.
* A strip parcel whose lower 78% is destroyed and upper 22% intact returns `area_dmg_frac ≈ 0.78` and `loss_attr` lower than `area_dmg_frac`; `v_sat = area_dmg_frac`.
* Silt scenario (W1 loss 0.5, NDRE rebounds +0.15, W2 loss 0.15) triggers `SILT_RECOVERY_OBSERVED`; rot scenario on `vertisol` triggers `DELAYED_WATERLOGGING_ROT`; the same rot numbers on `alluvial` soil do not.
* Bootstrap is deterministic (same seed → same σ).

---

### WP-1.8 SAR inundation (3 h)

**Files.** `pipeline/sar_inundation.py`, `tests/test_sar_gate.py`.

**Specification.**

1. **`lee_filter(db_array, size=3)`**: convert dB → linear power (`10**(x/10)`), apply a Lee filter with a 3×3 window (local mean and variance via `scipy.ndimage.uniform_filter`; equivalent number of looks estimated from the scene), convert back to dB. A refined Lee or median-ratio filter is acceptable; document which one you used.
2. **`ashman_d`**, **`sar_water_fraction`**: copy from **v3 §7.2** with these fixes:
   * Use `cfg.sar.*` values instead of literals.
   * The 2 km neighbourhood window (`window_delta_vv`) is built per parcel as a 2 km square around the centroid, clipped to the raster.
   * If the 2 km window has fewer than 50 valid pixels use the fallback threshold `cfg.sar.fallback_vv_drop_db` (−3.0).
   * Return both `water_frac` (open water + double bounce combined) and the two components separately inside `quality`.
3. **`ctrl_delta_vv_median`**: median of ΔVV over upland control parcels (those chosen in WP-1.6) to remove rain-wetting.
4. **Output per parcel:** a `scene_observations` row with `sensor='S1_SAR'`, `scene_date` of the peak scene, `sar_change_db` (mean Lee-filtered ΔVV over the parcel) and `water_frac`. If a third SAR scene exists (D-10), compute `water_frac_recession` the same way and store it in `quality`.
5. Only the **peak** scene is used for inundation evidence; SAR never changes `v_sat` directly. It supports Stage 3's `LATE_ASSESSMENT`, `NON_FLOOD_CAUSE_POSSIBLE` and the Agreement score.

**Acceptance criteria** (`tests/test_sar_gate.py`):
* A synthetic window that is 3% flooded (unimodal) gives `ashman_d < 2.0`, so the fixed −3.0 dB threshold is used (not Otsu).
* A synthetic 50% flooded window with clearly separated modes gives `ashman_d > 2.0` and Otsu is used.
* Positive ΔVV of +3 dB on **all** pixels (rain-wet soil) produces `double_bounce = 0` because the control excess is ≈ 0.
* The same +3 dB on a low-HAND (≤ 4 m), NDVI ≥ 0.35 pixel with controls at +0.3 dB produces `double_bounce = 1`.

---

### WP-1.9 Batch runner (3 h)

**Files.** `pipeline/run_batch_event.py`, Makefile target `make batch`.

**Specification.**

1. CLI: `python -m pipeline.run_batch_event --event MH-2024-07-PUNE [--mode v3|v2] [--limit N] [--parcel-id UUID]`.
2. For each parcel (case **and** control; controls only need their raw deficits) the runner:
   1. computes weights and `n_eff` (WP-1.6) and updates `parcels.min_width_m`;
   2. runs `compute_parcel_satellite()` (WP-1.7) and `sar_water_fraction()` (WP-1.8);
   3. runs `extract_hazard()` (WP-1.5);
   4. **upserts** `scene_observations`, `observed_estimates (source='satellite')`, `hazard_context`.
3. Two passes: **pass 1** computes control deficits for all control parcels and caches them in memory (and in `data/cache/control_deficits.parquet`); **pass 2** processes case parcels using that cache.
4. Parallelise by parcel with `concurrent.futures.ProcessPoolExecutor`; the DB write happens in the main process in batches of 50 inside one transaction per batch.
5. `--mode v2` writes into the cloned event `MH-2024-07-PUNE-V2` (D-16). The clone is created by `scripts/clone_event_for_v2.sql`, which copies `events`, `cases`, `official_assessments` with new `case_id`s and records the mapping in a table `v2_case_map(v3_case_id, v2_case_id)` that P1 adds to `01_…sql`.
6. Print a summary: parcels processed, how many have `window_used = 2`, `SMALL_PARCEL_LIMITATION` count, `LOW_CLEAR_FRACTION` count, parcels with fewer than 5 controls, median runtime per parcel.
7. Never crash on one bad parcel: log the error with the parcel id, continue, and list failures at the end (the README must say how many and why).

**Acceptance criteria.** `make batch` on the full seed finishes (state the measured runtime in the README); running it twice gives identical `observed_estimates` (idempotent); `--mode v2` populates the V2 event; at least 95% of case parcels have a satellite estimate.

---

### WP-1.10 Seed world: parcels, simulated officials, planted anomalies (4 h)

**Files.** `scripts/generate_seed.py`, `scripts/plant_anomalies.py`, `sql/04_seed_pune_july2024.sql` (generated), `benchmark/manifest.json`, `benchmark/ground_scenarios.json`, `tests/test_seed_integrity.py`.

The world is 🧪 **synthetic** (parcels and official records are simulated), placed on **real** imagery. Everything must say so (`parcels.is_synthetic = TRUE`).

**Step A — `generate_seed.py` (parcels, cases, event).**

| Item | Rule |
|---|---|
| Event | `MH-2024-07-PUNE`, `start_date 2024-07-24`, `peak_date 2024-07-25`, `end_date 2024-07-26` |
| Case parcels | 300 total: **80 strips** (width 20–35 m, length 250–450 m, oriented along the nearest drainage; placed where `HAND ≤ 3 m`) and **220 regular** (60–150 m on a side, 0.8–3 ha; 120 on the flood plain with `HAND ≤ 6 m`, 100 on mid-slope) |
| Control parcels | 150 with `role='control'`, `HAND ≥ 8 m`, in upland areas with SAR water fraction ≈ 0, no `cases` row |
| No overlap | Use a `shapely.STRtree`; reject overlapping candidates |
| Naming | `survey_no = "PUN-<TALUKA>-<seq:04d>"` (`HAV`, `DAU`); synthetic village names `Synthetic-V01 … V12` assigned by KMeans of centroids; taluka by location |
| Crop / sowing | soybean 50% (sown 15 Jun – 5 Jul), sugarcane 12%, bajra 8%, tur 5%, **crop and sowing_date NULL for 25%** (to exercise the spectral fallback) |
| Soil | `vertisol` for about 40% (mid-slope and Daund side), `alluvial` for flood-plain parcels, `murrum` for upland; uses a simple spatial rule plus noise |
| `farmer_ref` | opaque token `FRM-000123`; never real identifiers |
| `area_ha`, `min_width_m` | computed from geometry |
| Determinism | `rng = np.random.default_rng(42)` |

After generating: write `sql/04_seed_pune_july2024.sql` containing the `INSERT`s (or `COPY`) for `events`, `parcels`, `cases`. Official assessments are **not** written yet because they depend on satellite results.

**Step B — run WP-1.9 batch** so every case parcel has `V_sat`.

**Step C — `plant_anomalies.py` (official records and manifest).**

1. Assign each case parcel an **assessor token** `ASR-01 … ASR-20`; each token covers 1–2 whole villages. Assessed date = `peak_date + delay_days`, `delay_days` drawn from 3–20.
2. **Clean parcels (220):** `official_mid = V_sat + N(0, 0.05)`, rounded to the nearest 0.05, clipped to [0, 1]; interval `[mid − 0.05, mid + 0.05]` clipped (the spec's `rounding_tolerance`).
3. **Plant the five anomaly classes** from the detailed plan §3.2, selecting parcels by their **measured** `V_sat` (the imagery decides what is possible):

| Class | n | Selection from measured `V_sat` | Planted official / ground |
|---|---|---|---|
| 1 Individual severe under-assessment | 15 | `V_sat ∈ [0.50, 0.70]` | official mid = `V_sat − 0.35` (ends below 0.33) |
| 2 Individual moderate under-assessment | 15 | `V_sat ∈ [0.35, 0.60]` | official mid = `V_sat − 0.20` |
| 3 Blanket village panchnama bias | 20 | contiguous riverside parcels, `V_sat ∈ [0.45, 0.70]`, all under **one** token and one date | official = flat 0.20 (`[0.15, 0.25]`) for all 20 |
| 4 Fraudulent ground claim | 15 | `V_sat ≤ 0.12` (dry) | official ≈ `V_sat`; **ground claim 0.75**; 8 with scenario `NEIGHBOR_FRUSTUM`, 7 with `CROPPED_DUPLICATE` |
| 5 33% threshold surfing | 15 | `V_sat ∈ [0.20, 0.30]` | official 0.15; **ground claim 0.58** with legitimate-looking Tier-1 photos (scenario `SURFING_TIER1`) |

   If the measured imagery does not supply enough parcels in a stratum (very likely for Class 5 and Class 4 on real data), **generate additional candidate parcels** near the flood margin (`HAND 3–6 m`) or in dry areas and re-run the batch for them. Do not relax the planted values. Record any shortfall in the README.
4. Honest ground reports for realism: for 40 clean parcels plus 10 from Classes 1–2, create scenarios `HONEST_TIER1` (30) and `HONEST_TIER2` (20) with claimed damage `V_sat + N(0, 0.08)`.
5. Write `benchmark/manifest.json`:

   ```json
   {"seed": 42, "event_id": "MH-2024-07-PUNE",
    "cases": [{"case_id": "…", "class": 3, "v_sat_measured": 0.58,
               "official": [0.15, 0.25], "assessor_token": "ASR-14",
               "expected_flag": "CLUSTER_BIAS"}]}
   ```

   Every case appears; clean cases have `"class": 0` and `"expected_flag": null`. Valid `expected_flag` values: `SAT_UNDER_RISK`, `PEER_INCONSISTENCY`, `CLUSTER_BIAS`, `PHOTO_INTEGRITY_ALERT`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `null`.
6. Write `benchmark/ground_scenarios.json` (read by Stage 2):

   ```json
   [{"case_id": "…", "scenario": "CROPPED_DUPLICATE", "claimed_damage": 0.75,
     "n_photos": 2, "dup_source_case_id": "<an HONEST_TIER1 case>"},
    {"case_id": "…", "scenario": "SURFING_TIER1", "claimed_damage": 0.58, "n_photos": 2}]
   ```

   Allowed scenarios: `HONEST_TIER1`, `HONEST_TIER2`, `NEIGHBOR_FRUSTUM`, `CROPPED_DUPLICATE`, `PUDDLE`, `SCREEN_SPOOF`, `SURFING_TIER1`.
7. The v2 clone (`scripts/clone_event_for_v2.sql`) runs after this step, then `make batch MODE=v2`.

**Acceptance criteria** (`tests/test_seed_integrity.py`):
* 450 parcels (300 `case`, 150 `control`); 80 case parcels with `min_width_m < 35`; no overlaps; 25% (±3%) of case parcels have NULL crop.
* 300 `cases`, 300 `official_assessments`; the manifest counts per class are exactly 15 / 15 / 20 / 15 / 15.
* Class 3 parcels share one `assessor_token`, one `assessed_on`, and all have official mid 0.20.
* Class 4 parcels have measured `V_sat ≤ 0.12`; Class 5 parcels have measured `V_sat ∈ [0.20, 0.30]`.
* Running generation twice yields identical output (determinism).

---

### WP-1.11 Tests, snapshot and handoff (2 h)

1. `make test` passes for: `test_unclipped_did`, `test_strip_parcel_weights`, `test_sar_gate`, `test_seed_integrity`, the config test and the hazard test.
2. `make snapshot S=1` produces `handoffs/stage1/stage1.dump`. Verify by restoring into a **fresh** database and running `make counts`.
3. Write the README using the template in Section 2.7. It **must** contain:
   * row counts per table;
   * the real clear fraction of each Sentinel-2 scene (D-22) and whether the third SAR scene exists (D-10);
   * how many parcels have `window_used = 2`, `SMALL_PARCEL_LIMITATION`, `LOW_CLEAR_FRACTION`, fewer than 5 controls;
   * the distribution of `V_sat` over the 300 case parcels (min, quartiles, max) tagged *real imagery, synthetic parcels*;
   * every deviation from the contracts, or the sentence "No deviations";
   * pipeline runtime and machine description.
4. 15-minute walk-through with Person 2.

### 3.X Exit Gate 1 checklist (Person 1 signs)

- [ ] `make up && make restore S=1 && make counts` works on a clean machine
- [ ] 450 parcels, 300 cases, 300 official assessments, ≥ 95% of case parcels with a satellite estimate
- [ ] `scene_observations`, `hazard_context` populated; `pixel_grid` present for case parcels
- [ ] `manifest.json` and `ground_scenarios.json` committed; class counts exact
- [ ] V2 clone exists and is populated
- [ ] All Stage 1 tests green; README complete with real data caveats

---

# 4. STAGE 2 — Person 2: Ground Evidence (Photo Verifier & Farmer PWA)

**Mission.** Make the farmer's report trustworthy. Own everything from the phone camera to a verified **ground estimate**: the Marathi-first PWA, the six-layer photo verifier, the `POST /cases/{id}/ground` endpoint, and the fraud scenarios that the benchmark needs.

**You receive:** `handoffs/stage1/stage1.dump` + README, `benchmark/ground_scenarios.json`.
**You hand over:** `handoffs/stage2/stage2.dump` + README (Exit Gate 2): Stage 1's database plus `photos` and ground `observed_estimates`.
**You never touch:** `pipeline/`, satellite `observed_estimates`, `detections`, `audit_log`, `frontend/`.

### 4.0 Work-package summary

| WP | Title | Hours |
|---|---|---|
| 2.1 | Frustum SQL, schema additions, spatial helpers | 2 |
| 2.2 | Verifier checks 1–3: distance, frustum, pitch and two-angle gate | 3 |
| 2.3 | Verifier check 4: 3-frame burst parallax and Moiré | 3 |
| 2.4 | Verifier check 5: embeddings and `pgvector` deduplication | 4 |
| 2.5 | Verifier check 6: zero-shot crop consistency | 2 |
| 2.6 | Tier assignment, ground estimate, `POST /ground`, `GET /ground-context` | 5 |
| 2.7 | PWA camera burst, compass and level guide | 4 |
| 2.8 | PWA Marathi structured form and flow | 3 |
| 2.9 | PWA offline queue and upload | 2 |
| 2.10 | Demo photo bundles and benchmark scenario ingestion | 2 |
| 2.11 | Tests, snapshot and handoff | 2 |
| | **Total** | **32** |

### 4.1 Intake (do this first, ≈ 30 min, not counted above)

1. `make up && make restore S=1 && make counts`. Compare with the Stage 1 README.
2. Read `benchmark/ground_scenarios.json` and Section 2.4-B (the ground `quality` shape you must write).
3. Run `SELECT count(*) FROM parcels WHERE role='case'` and look at five strip parcels on a map to understand the geometry the frustum must hit.
4. Any contradiction with the contracts → open an `upstream-bug` issue for Person 1 before you build on it.

### 4.2 Local decisions for this stage

| ID | Decision |
|---|---|
| **L2-1** | A photo flagged `DUPLICATE_PHOTO_EMBEDDING` or `SCREEN_MOIRE_SUSPECTED` makes the **whole ground estimate** `excluded = true` (a tainted photo taints the claim). A photo that fails **only** the parallax test (`BURST_PARALLAX_FAIL`, no Moiré) is removed from the usable set and raises `PHOTO_INTEGRITY_ALERT`, but does not exclude the claim; if no usable photo remains the claim becomes Tier 3 (σ 0.35), not excluded. This avoids punishing a farmer whose hand was simply too steady. |
| **L2-2** | The burst is 3 frames at t = 0, 750 ms, 1500 ms (1.5 s total, as in v3 spec D9). The detailed plan's "500 ms apart" gives only 1 s and less parallax. |
| **L2-3** | Ownership binding for the prototype: the PWA link carries `?case=<case_id>&t=<farmer_ref>`; the API compares `t` with `cases.farmer_ref` (header `X-Farmer-Token`). Real OTP / Agri Stack verification is 🗺️ roadmap. |
| **L2-4** | Additive schema changes are allowed in `02_…sql` and must be logged in `contracts/CHANGELOG.md`: `photos.client_signature TEXT`, `photos.flags JSONB NOT NULL DEFAULT '[]'`, `photos.excluded BOOLEAN NOT NULL DEFAULT FALSE`, `photos.frames_path TEXT` and `photos.thumb_path TEXT` (the v3 `photos` table has no place to find the image files again, and Stage 4's evidence view needs them; see WP-2.6), unique index on `(case_id, client_signature)`. |
| **L2-5** | In the 300-parcel benchmark the embedding model cannot be fed ~150 truly distinct real photos. Benchmark ingestion uses an injected `SyntheticEmbedder` (🧪). Frustum, distance, pitch and burst checks still run for real. The six demo bundles use the real model. |

---

### WP-2.1 Frustum SQL, schema additions, spatial helpers (2 h)

**Files.** `sql/02_frustum_and_spatial.sql`, `tests/test_frustum_sql.py` (part of `test_photo_anti_spoofing.py` is allowed instead).

**Specification.** The script must be re-runnable (`CREATE OR REPLACE`, `IF NOT EXISTS`) and contain:

1. `compute_frustum_overlap(user_lon, user_lat, azimuth_deg, cone_half_angle_deg, range_m, parcel_geom_utm)`: copy the function from **v3 spec §6** unchanged. Keep `RETURNS NUMERIC` and the `ROUND(…, 3)`. Note that the function converts compass azimuth (0° = north, clockwise) to the mathematical angle with `radians(90 − azimuth)`.
2. `photo_boundary_distance(user_lon, user_lat, parcel_geom_utm) RETURNS DOUBLE PRECISION`: `ST_Distance(ST_Transform(ST_SetSRID(ST_MakePoint(lon, lat), 4326), 32643), parcel_geom_utm)`; returns 0 when the point is inside the parcel.
3. `frustum_geojson(user_lon, user_lat, azimuth_deg, cone_half_angle_deg, range_m) RETURNS JSONB`: builds the same triangle as (1) but returns `ST_AsGeoJSON(ST_Transform(frustum, 4326))::jsonb`. Stage 4's map calls this so the front end does no geometry.
4. The additive columns from **L2-4**.
5. `EXPLAIN` the overlap function on one strip parcel; if `compute_frustum_overlap` takes more than 5 ms per call, add a `ST_Intersects` pre-check.

**Acceptance criteria.** With a 100 m × 100 m test square: a point 10 m west of the west edge, azimuth 110°, returns overlap ≥ 0.70; azimuth 290° returns 0.000; `NULL` azimuth returns 0.0. `frustum_geojson` returns a valid GeoJSON `Polygon` with 4 distinct vertices + closing vertex.

---

### WP-2.2 Verifier checks 1–3 (3 h)

**Files.** `backend/services/photo_verifier.py` (first part).

**Data model** (put the dataclasses at the top of the file; they are the internal contract of the module):

```python
@dataclass
class PhotoInput:
    photo_id: UUID
    captured_at: datetime            # tz-aware
    lat: float; lon: float; acc_m: float
    azimuth_deg: float | None        # None → compass missing
    pitch_deg: float | None
    frames_bgr: list[np.ndarray]     # 3 frames, BGR uint8
    in_app_capture: bool
    client_signature: str

@dataclass
class PhotoResult:
    photo_id: UUID
    dist_to_parcel_m: float
    dist_ok: bool
    frustum_overlap: float | None
    frustum_ok: bool | None          # None when compass missing
    pitch_ok: bool | None            # None when pitch missing
    burst_parallax_ok: bool | None
    moire_score: float | None
    parallax_ratio: float | None
    embedding: np.ndarray | None
    dup_of: UUID | None
    dup_similarity: float | None
    crop_match_ok: bool | None       # None = uncertain / not applicable
    zero_shot: dict | None
    flags: list[str]
    excluded: bool                   # photo removed from usable set
    taints_claim: bool               # True for duplicate / Moiré
    passes_all: bool
```

**Check 1: parcel distance and GPS accuracy.**
`dist = photo_boundary_distance(lon, lat, parcel.geom_utm)`.
`dist_ok = dist ≤ 15.0 and acc_m ≤ 25.0` (config `ground.photo_max_boundary_dist_m`, `ground.photo_max_accuracy_m`).
Failure flags: `OUTSIDE_PARCEL_BOUNDARY` if `dist > 15`; `LOW_GPS_ACCURACY` if `acc_m > 25`.

**Check 2: viewing-frustum ray-cast.**
If `azimuth_deg is None` → `frustum_overlap = None`, flag `COMPASS_MISSING`.
Else `frustum_overlap = compute_frustum_overlap(lon, lat, azimuth, 25.0, 60.0, geom_utm)`; `frustum_ok = overlap ≥ 0.40`. Failure flag: `FRUSTUM_OUTSIDE_PARCEL`.

**Check 3: pitch and two-angle gate.**
Per photo: `pitch_ok = 65 ≤ pitch ≤ 88` (None if pitch is missing). Failure flag: `PITCH_OUT_OF_RANGE`.
Bundle-level (implemented in WP-2.6): among photos with `pitch_ok`, there must be two whose azimuth differs by ≥ 35° (use circular difference `min(|a−b|, 360−|a−b|)`) **or** whose GPS positions are ≥ 15 m apart (`ST_Distance` in UTM). Else flag `SINGLE_ANGLE_ONLY`.

Also set `flags += ['GALLERY_UPLOAD']` and treat the photo as non-qualifying for Tier 1/2 when `in_app_capture` is false.

**Acceptance criteria.** Unit tests (no DB mocks: use a test PostGIS) cover each flag with at least one positive and one negative example; circular azimuth difference is correct across the 0°/360° seam (350° vs 20° = 30°).

---

### WP-2.3 Check 4: burst parallax and Moiré (3 h)

**Files.** `backend/services/photo_verifier.py` (second part).

**Specification.**

1. Copy `verify_burst_liveness_and_screen_spoof()` from the **detailed plan §2.2** (Farneback flow and FFT ring score, D-4). Required modifications:
   * Read thresholds from config: `fg_motion_range_px [0.2, 45]`, `parallax_ratio_min 0.08`, `moire_max 6.5`.
   * Normalise frame size first: resize every frame so the long edge is 640 px; flow magnitudes are thus comparable across phones.
   * Compare first and last frame; the middle frame is kept for the Moiré score of the sharpest frame (choose the frame with the highest Laplacian variance, not always `g1`).
   * Return the two outcomes separately: `parallax_ok` and `moire_suspected = (moire_score ≥ 6.5)` so that L2-1 can treat them differently.
2. Mapping to flags:
   * `parallax_ok == False` → `BURST_PARALLAX_FAIL`
   * `moire_suspected` → `SCREEN_MOIRE_SUSPECTED` and `taints_claim = True`
   * both → photo `excluded = True`.
3. If fewer than 2 frames are supplied: `parallax_ok = False`, `moire_score = 1.0`, flag `BURST_PARALLAX_FAIL`.
4. **Calibration step (mandatory, 🎯):** with the demo bundles of WP-2.10 record `parallax_ratio` and `moire_score` for genuine bursts and screen-of-a-screen bursts. Report the two distributions in the README; if `6.5` or `0.08` separate them poorly, tune the config values and say so. Do not claim the thresholds are validated.
5. *Optional, only if ahead of schedule:* sun-elevation plausibility from `captured_at` + GPS (`astral` library): if the sun is below −6° but the frame's mean luminance > 0.35, flag `TIMESTAMP_IMPLAUSIBLE` (this requires a CHANGELOG entry adding the flag to the enum).

**Acceptance criteria** (`test_photo_anti_spoofing.py`, burst part):
* A synthetic 3-frame burst where the lower half shifts 8 px and the upper half 2 px passes (`parallax_ratio ≥ 0.08`).
* A synthetic burst produced by one global shift (rigid homography) fails parallax.
* A frame with a periodic 4-px grid overlay yields `moire_score ≥ 6.5`; a natural texture image does not.
* A burst of three identical frames fails (`fg_motion < 0.2`).

---

### WP-2.4 Check 5: embeddings and `pgvector` deduplication (4 h)

**Files.** `backend/services/embeddings.py`, `backend/services/photo_verifier.py` (third part), `backend/assets/`.

**Specification.**

1. **Interface.**

   ```python
   class EmbeddingBackend(Protocol):
       dim: int  # 512
       def embed(self, image_bgr: np.ndarray) -> np.ndarray: ...        # L2-normalised float32
       def embed_text(self, prompts: list[str]) -> np.ndarray: ...      # for zero-shot, L2-normalised
   ```

   Implementations: `OnnxClipBackend` (MobileCLIP-S0 or CLIP ViT-B/32 image and text encoders exported to ONNX; 512-D; CPU; target ≤ 300 ms per image) and `SyntheticEmbedder` (L2-5; deterministic random unit vectors seeded by `photo_id`; supports `force_similar_to(vector, cosine)`).
2. **Pre-processing.** Resize to the model's input, centre crop, normalise with the model's mean/std. Document the model file hash in `model_versions.embedding_model`.
3. **Multi-view query.** Because a cropped duplicate can fall below 0.92 with the full image, compute embeddings for four views of each new photo: full, centre-70% crop, left-80% crop, right-80% crop. Query the nearest neighbour for each; `max_cosine_sim` is the largest of the four. Only the **full-image** embedding is stored in `photos.embedding`.
4. **Query** (scoped to the same event so photos from other disasters do not collide):

   ```sql
   SELECT p.photo_id, p.case_id, 1 - (p.embedding <=> :emb) AS sim
   FROM photos p JOIN cases c ON c.case_id = p.case_id
   WHERE c.event_id = :event_id AND p.case_id <> :case_id AND p.embedding IS NOT NULL
   ORDER BY p.embedding <=> :emb
   LIMIT 1;
   ```

   `pgvector` index: the spec's `ivfflat (lists = 50)` needs a populated table before it is effective; set `SET ivfflat.probes = 10` on the connection and run `ANALYZE photos` after bulk loads.
5. **Decision.** `sim ≥ 0.92` (config) → `dup_of = photo_id`, `dup_similarity = sim`, flag `DUPLICATE_PHOTO_EMBEDDING`, `taints_claim = True`, `excluded = True`.
6. **Within-bundle repeats.** If two photos of the same bundle have cosine ≥ 0.97 they count as one photo for the two-angle gate (flag `SINGLE_ANGLE_ONLY`) but are not duplicates.
7. **Order of writes.** Insert the photo row only **after** the dedup query so a re-submitted bundle is not matched against itself; the unique `(case_id, client_signature)` index makes re-submission idempotent (return the stored result).
8. 🎯 **Calibration:** measure and report, on the demo bundles, the cosine between the original flood photo and its cropped/rotated duplicate, and the largest similarity among distinct genuine photos. If the cropped duplicate scores below 0.92, tune the multi-view crops (not the threshold) first.

**Acceptance criteria.**
* Logic tests with injected vectors: cosine 0.95 → flagged; 0.80 → not flagged; same case → not flagged; other event → not flagged.
* With the real model: a 75% centre crop plus 8° rotation plus brightness shift of a demo photo yields `max_cosine_sim ≥ 0.92` (if not, see calibration step 8 and report).
* Re-submitting an identical bundle returns `200` with the original result and inserts no new rows.

---

### WP-2.5 Check 6: zero-shot crop consistency (2 h)

**Files.** `backend/services/photo_verifier.py` (fourth part), `backend/assets/crop_prompts.json`.

**Specification.**

1. Prompt set (English; the text embeddings are precomputed once and cached):

   | Class key | Prompt |
   |---|---|
   | `short_crop_flooded` | "a photo of a flooded soybean or short crop field" |
   | `tall_sugarcane` | "a photo of a tall sugarcane field" |
   | `bare_fallow` | "a photo of bare fallow farmland" |
   | `non_farm` | "a photo of a road, house or building" |
   | `water_only` | "a photo of open water with no crop" |

2. Compute softmax over `100 × cosine` (CLIP logit scale) → `zero_shot` JSON with the five probabilities.
3. Compatibility map: `soybean, bajra, tur, groundnut, maize` ↔ `short_crop_flooded`; `sugarcane` ↔ `tall_sugarcane`; if `parcel.crop IS NULL` only `non_farm` and `bare_fallow` count as a mismatch.
4. `crop_match_ok = False` only if the top class has probability ≥ 0.50 **and** is incompatible; otherwise `True` when compatible, and `None` when the top probability is < 0.50 (uncertain). Mismatch sets flag `CROP_MISMATCH` (it does not exclude the photo; it only prevents the photo from counting as "passes all checks", so the bundle cannot be Tier 1).
5. Pre-flood landmark/horizon matching with e-Peek Pahani photos is 🗺️ (Week 3 of the pilot). Do not implement it; do mention it in the README as not done.

**Acceptance criteria.** Using five demo images (flooded soybean, sugarcane, bare field, road, water): each gets its expected top class with the real model; `parcel.crop='sugarcane'` + soybean photo → `CROP_MISMATCH`.

---

### WP-2.6 Tier assignment, ground estimate, API endpoints (5 h)

**Files.** `backend/services/photo_verifier.py` (`verify_bundle`), `backend/services/ground_estimate.py`, `backend/routers/ground.py`, `tests/test_ground_estimate.py`.

**A. Bundle tier algorithm** (implements v3 D9 with decisions D-2, D-3, L2-1):

```python
def assign_tier(photos: list[PhotoResult]) -> BundleResult:
    any_taint = any(p.taints_claim for p in photos)
    usable    = [p for p in photos if not p.excluded]
    flags     = sorted({f for p in photos for f in p.flags})
    if any_taint:
        return BundleResult(tier=3, sigma=0.35, excluded=True,  flags=flags + ["PHOTO_INTEGRITY_ALERT"])
    qualifying = [p for p in usable if p.in_app and p.dist_ok and p.frustum_ok is not False]
    passing    = [p for p in usable if p.passes_all]
    angle_ok   = exists_pair(passing, min_az_sep=35.0, min_pos_sep_m=15.0)
    if len(passing) >= 2 and angle_ok:
        return BundleResult(tier=1, sigma=0.14, excluded=False, flags=flags)
    if qualifying:
        return BundleResult(tier=2, sigma=0.22, excluded=False, flags=flags + ([] if angle_ok else ["SINGLE_ANGLE_ONLY"]))
    return BundleResult(tier=3, sigma=0.35, excluded=False, flags=flags)
```

`passes_all` for a photo = in-app AND `dist_ok` AND `frustum_ok is True` AND `pitch_ok is True` AND `burst_parallax_ok is True` AND no Moiré AND no duplicate AND `crop_match_ok is not False`. If any usable photo had `BURST_PARALLAX_FAIL`, add `PHOTO_INTEGRITY_ALERT` to the flags.

Truth table (use it as the test oracle):

| Scenario | Expected tier | Excluded | Key flags |
|---|---|---|---|
| 2 good photos, ≥ 35° apart, all checks pass | 1 (σ 0.14) | no | — |
| 2 good photos but only 20° apart and 5 m apart | 2 (σ 0.22) | no | `SINGLE_ANGLE_ONLY` |
| 1 good photo | 2 | no | `SINGLE_ANGLE_ONLY` |
| Compass missing | 2 | no | `COMPASS_MISSING` |
| Puddle shot (pitch 25°), near parcel, pointing in | 2 | no | `PITCH_OUT_OF_RANGE` |
| Standing 10 m outside, pointing away (α 290°) | 3 (σ 0.35) | no | `FRUSTUM_OUTSIDE_PARCEL` |
| 60 m outside parcel | 3 | no | `OUTSIDE_PARCEL_BOUNDARY` |
| Gallery upload | 3 | no | `GALLERY_UPLOAD` |
| Cropped duplicate of another case's photo | 3 | **yes** | `DUPLICATE_PHOTO_EMBEDDING`, `PHOTO_INTEGRITY_ALERT` |
| Screen-of-a-screen | 3 | **yes** | `SCREEN_MOIRE_SUSPECTED`, `BURST_PARALLAX_FAIL`, `PHOTO_INTEGRITY_ALERT` |
| Soybean claim with sugarcane photos | 2 | no | `CROP_MISMATCH` |

**B. Ground estimate (D-19).** `ground_estimate.py`:

```python
def build_ground_estimate(form: GroundForm, bundle: BundleResult, cfg) -> dict
```

* `value = form.damaged_share_pct / 100.0`.
* `sigma` = tier σ from the bundle (0.14 / 0.22 / 0.35). If `form_consistency == "INCONSISTENT"`, multiply σ by 1.25 and cap at 0.35.
* `ci_lo = max(0, value − 1.28σ)`, `ci_hi = min(1, value + 1.28σ)` (same `interval_z` as pooling).
* **Form fields:** `damaged_share_pct` (int 0–100, multiples of 5), `water_depth_band` ∈ {`NONE`, `ANKLE`, `KNEE`, `WAIST`, `ABOVE_WAIST`}, `water_days` (0–14), `crop_stage` ∈ {`SOWN_ONLY`, `VEGETATIVE`, `FLOWERING`, `PODDING_OR_MATURE`}, optional `note` (≤ 300 chars), optional voice note (stored, not transcribed; transcription is 🗺️).
* **Consistency check** (flags only, never changes `value`): `INCONSISTENT` if (`damaged_share_pct ≥ 60` and `water_depth_band == 'NONE'`) or (`damaged_share_pct ≤ 10` and `water_days ≥ 7` and `water_depth_band in ('WAIST','ABOVE_WAIST')`); else `OK`. Free text is **never** used to compute the value (avoids double counting).
* Output goes to `observed_estimates (source='ground')` with the `quality` JSON of Section 2.4-B (`UPSERT` on `(case_id, source)`).

**C. Endpoints** (`backend/routers/ground.py`):

`GET /cases/{id}/ground-context` → used by the PWA before capture. (This route is **new**: it is not in the nine-endpoint list of v3 §8. Log it in `contracts/CHANGELOG.md` and regenerate `contracts/openapi.json`.)

```json
{"case_id": "…", "declared_crop": "soybean", "parcel_bbox_wgs84": [73.84, 18.47, 73.86, 18.49],
 "parcel_polygon": {"type": "Polygon", "coordinates": []}, "min_width_m": 32.0,
 "boundary_tolerance_m": 15.0, "required_photos": 2}
```

`POST /cases/{id}/ground` → `multipart/form-data`. Parts: `payload` (JSON string) and image files named `photo{i}_frame{j}.jpg`.

```json
{"client_bundle_signature": "sha256hex", "locale": "mr",
 "form": {"damaged_share_pct": 75, "water_depth_band": "KNEE", "water_days": 4,
          "crop_stage": "VEGETATIVE", "note": null},
 "photos": [{"client_photo_signature": "sha256hex", "captured_at": "2024-08-05T10:14:22+05:30",
             "lat": 18.4802, "lon": 73.8501, "acc_m": 6.1, "azimuth_deg": 112.0, "pitch_deg": 76.0,
             "in_app_capture": true,
             "frames": ["photo0_frame0", "photo0_frame1", "photo0_frame2"]}]}
```

Response `201` (or `200` for an idempotent repeat):

```json
{"case_id": "…", "tier": 1, "sigma": 0.14, "excluded": false, "value": 0.75, "ci": [0.57, 0.93],
 "flags": [], "photos": [{"photo_id": "…", "frustum_overlap": 0.84, "dist_to_parcel_m": 0.0,
 "burst_parallax_ok": true, "moire_score": 2.1, "dup_similarity": 0.41, "crop_match_ok": true,
 "status": "PASS"}]}
```

Errors: `404` unknown case; `403` token mismatch (L2-3); `409` ground estimate already submitted with a different signature (keep first, officers can review; do not overwrite silently); `413` body > 15 MB; `422` schema violations (2–4 photos, exactly 3 frames each, `damaged_share_pct` multiple of 5). Validation rules live in Pydantic models that Stage 4 will import from `backend/models.py` (add them there, log in CHANGELOG).

**Column names.** The v3 `photos` table calls the GPS accuracy `acc_m` and the heading `compass_azimuth_deg`; the verifier's internal dataclasses and the API payload use `acc_m` and `azimuth_deg`. Map them in one place (a `to_db_row()` method) and test the mapping.

**Image storage (gap closed here).** Write each frame to `data/uploads/<case_id>/<photo_id>/f<j>.jpg` and a 320 px-wide JPEG thumbnail of the sharpest frame to `data/uploads/<case_id>/<photo_id>/thumb.jpg`. Store the directory in `photos.frames_path` and the thumbnail file in `photos.thumb_path`. Never store images in the database. Include `data/uploads/` in `handoffs/stage2/` (or document how to regenerate it with `ingest_ground_scenarios.py`), because Stage 4 serves the thumbnails. Strip EXIF from the thumbnail (it contains GPS).

**Transaction.** Parse → verify photos → compute tier → write image files → insert `photos` rows → upsert ground `observed_estimates` → all in one DB transaction (delete the written files if the transaction fails). Write **no** `audit_log` rows (Stage 3 owns audit; the ground submission is audited the next time `/analyze` runs, which records `ground_tier` and `photo_ids`).

**Acceptance criteria** (`test_ground_estimate.py` and API tests):
* Each row of the truth table is reproduced through the real endpoint with prepared bundles.
* `value` is exactly `damaged_share_pct / 100`; `ci` uses 1.28σ; inconsistent forms inflate σ by 1.25 (cap 0.35).
* Idempotent repeat returns `200`; wrong token returns `403`; 5 photos returns `422`.
* The row in `observed_estimates` validates against `GroundQuality` from `models.py`.

---

### WP-2.7 PWA camera burst, compass and level guide (4 h)

**Files.** `pwa/src/CameraBurstCapture.tsx`, `pwa/src/hooks/useGeolocation.ts`, `pwa/src/hooks/useOrientation.ts`, `pwa/src/lib/geo.ts`.

**Specification.**

1. **Camera.** `navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false })`. No `<input type="file">` anywhere in the standard flow (v3 D9: gallery photos cannot be trusted). A hidden developer flag `?mode=gallery` shows a file input and sets `in_app_capture = false` (used to demonstrate Tier 3).
2. **Location.** `navigator.geolocation.watchPosition(..., { enableHighAccuracy: true, maximumAge: 0 })`. The shutter is disabled until `accuracy ≤ 25 m` and a fix is < 10 s old; show the live accuracy in metres.
3. **Orientation.**
   * iOS requires `DeviceOrientationEvent.requestPermission()` triggered from a user tap; handle denial with a clear Marathi message and let the user continue (the verifier will mark Tier 2, `COMPASS_MISSING`).
   * Android Chrome: use the `deviceorientationabsolute` event; fall back to `deviceorientation`.
   * `pitch = beta` (portrait lock; ask the user to hold the phone upright).
   * Heading of the **rear camera**: use the W3C compass-heading formula on `(alpha, beta, gamma)`:

     ```ts
     function compassHeading(alpha: number, beta: number, gamma: number): number {
       const d = Math.PI / 180, x = beta * d, y = gamma * d, z = alpha * d;
       const cY = Math.cos(y), cZ = Math.cos(z), sX = Math.sin(x), sY = Math.sin(y), sZ = Math.sin(z);
       const Vx = -cZ * sY - sZ * sX * cY;
       const Vy = -sZ * sY + cZ * sX * cY;
       let h = Math.atan(Vx / Vy);
       if (Vy < 0) h += Math.PI; else if (Vx < 0) h += 2 * Math.PI;
       return (h * 180) / Math.PI;
     }
     ```

     **Field-test it** against a reference compass app at four headings and record the offsets in `pwa/FIELD_TEST.md`. On iOS also compare with `webkitCompassHeading`. Magnetic declination in Pune is small (< 1°) and may be ignored; say so in the README.
   * Smooth with a short moving average (5 samples) and a circular mean for the heading.
4. **Live level and compass guide** (spec §2.4 of the detailed plan): a circular overlay that turns **green** only when `65° ≤ pitch ≤ 88°` **and** the heading lies within the angular span from the user's GPS position to the parcel bounding-box corners (computed in `geo.ts` from `parcel_bbox_wgs84`, accounting for wrap-around at 360°). Otherwise it is amber with a Marathi hint ("फोन सरळ धरा", "शेताकडे तोंड करा").
5. **Burst.** One tap triggers three frames at t = 0, 750, 1500 ms (L2-2). For each frame: draw the `<video>` to an offscreen canvas (long edge ≤ 1280 px) and `toBlob('image/jpeg', 0.85)`. Record `{azimuth, pitch, lat, lon, acc, timestamp}` per frame; the stored values for the photo are the **median** of the three. While the burst runs, show a Marathi prompt "फोन हळू हळू थोडा बाजूला हलवा" (move the phone slowly a little sideways) with a 1.5 s progress ring — genuine parallax needs slight natural motion.
6. **Two-photo flow.** After photo 1 the app asks for photo 2 and **locally** checks the angle/position gate: `Δazimuth ≥ 35°` or `≥ 15 m` moved; the shutter for photo 2 stays amber until satisfied. A "skip" button allows a single photo (the server will assign Tier 2).
7. **Do not show verification outcomes to the farmer.** After submission show a neutral "तुमचा अहवाल मिळाला" (your report was received). Telling a fraudster which check failed helps them adapt.
8. Accessibility: touch targets ≥ 48 px; high contrast; text ≥ 18 px; works at 360 px width.

**Acceptance criteria.** On a real Android phone and (if available) an iPhone: permissions flow works; shutter locks until GPS accuracy ≤ 25 m; guide colour matches the pitch/heading rules in the field; three frames are produced per tap; telemetry values are present in the produced payload; no file picker is visible.

---

### WP-2.8 PWA Marathi structured form and flow (3 h)

**Files.** `pwa/src/StructuredClaimForm.tsx`, `pwa/src/i18n/{mr,en}.json`, `pwa/src/App.tsx`.

**Screens.** S0 Landing (reads `?case=&t=`, language toggle, default `mr`) → S1 Permissions (location, camera, motion, each with a one-line reason) → S2 Form → S3 Photo 1 → S4 Photo 2 → S5 Review & Send → S6 Received/Queued.

**Form controls (mobile-first).**
* Damage slider 0–100 in steps of 5 with a large numeric readout and colour bands (0–30 / 35–60 / 65–100), plus ± buttons for accessibility.
* Water depth: five icon cards (ankle, knee, waist, above waist, none).
* Days water stayed: stepper 0–14.
* Crop stage: four cards.
* Optional note (≤ 300 chars) and optional voice note (`MediaRecorder`, ≤ 30 s, shown as audio chip). The voice note is stored only.

**Marathi-first strings** (have a native speaker review them before the demo):

| Key | Marathi | English |
|---|---|---|
| `title` | शेतपाहणी अहवाल | Field damage report |
| `damage_q` | तुमच्या शेताचे किती नुकसान झाले? | How much of your field is damaged? |
| `depth_q` | शेतात पाणी किती खोल होते? | How deep was the water in your field? |
| `depth_ankle` | घोट्यापर्यंत | Up to ankle |
| `depth_knee` | गुडघ्यापर्यंत | Up to knee |
| `depth_waist` | कमरेपर्यंत | Up to waist |
| `depth_above` | कमरेपेक्षा जास्त | Above waist |
| `depth_none` | पाणी नव्हते | No water |
| `days_q` | पाणी किती दिवस साचले? | How many days did the water stay? |
| `stage_q` | पीक कोणत्या अवस्थेत होते? | What stage was the crop in? |
| `note_opt` | टीप (ऐच्छिक) | Note (optional) |
| `open_camera` | कॅमेरा उघडा | Open camera |
| `take_photo` | फोटो काढा | Take photo |
| `hold_upright` | फोन सरळ धरा | Hold the phone upright |
| `face_field` | शेताकडे तोंड करा | Face your field |
| `move_slowly` | फोन हळू हळू थोडा बाजूला हलवा | Move the phone slowly a little sideways |
| `turn_second` | आता दुसऱ्या दिशेने फोटो काढा | Now take a photo from another direction |
| `locating` | तुमचे स्थान शोधत आहे… | Finding your location… |
| `compass_missing` | होकायंत्र उपलब्ध नाही | Compass not available |
| `send` | पाठवा | Send |
| `saved_offline` | ऑफलाइन जतन केले; नेटवर्क मिळताच पाठवले जाईल | Saved offline; will be sent when the network returns |
| `received` | तुमचा अहवाल मिळाला | Your report was received |
| `retry` | पुन्हा प्रयत्न करा | Try again |

Numbers are shown in Devanagari digits when the locale is `mr` (use `Intl.NumberFormat('mr-IN-u-nu-deva')`), but the payload always contains ASCII integers.

**Acceptance criteria.** The whole flow can be completed by someone who reads only Marathi; the payload produced matches the schema in WP-2.6-C (validate with a JSON-schema test in `vitest`); switching language mid-flow does not lose state.

---

### WP-2.9 PWA offline queue and upload (2 h)

**Files.** `pwa/src/offlineQueue.ts`, `pwa/src/lib/signature.ts`, `pwa/vite.config.ts` (PWA plugin), service worker.

**Specification.**

1. **Local signature.** SHA-256 (`crypto.subtle.digest`) over a canonical JSON string with **sorted keys** of `{frames: [sha256(jpegBytes)…], lat, lon, acc, azimuth, pitch, timestamp}` per photo (→ `client_photo_signature`); the bundle signature is the SHA-256 of the concatenated sorted photo signatures plus the form JSON (→ `client_bundle_signature`). This is for integrity and idempotency, **not** security: a malicious client can fabricate signatures. Real attestation (WebAuthn / Play Integrity) is 🗺️ pilot week 3.
2. **IndexedDB.** Database `recon-ai`, store `bundles` with `{ id: signature, caseId, token, payload, blobs: Blob[], status: 'PENDING'|'UPLOADING'|'DONE'|'FAILED', attempts, lastError, createdAt }`. A bundle with 2 photos × 3 frames at ≈ 200 KB is ≈ 1.2 MB.
3. **Upload worker.** Triggered on app start, on the `online` event, on Background Sync (if supported) and every 30 s while visible. Upload the whole multipart body (idempotent on the server). Retry with exponential back-off 2 s, 4 s, 8 s … capped at 5 min; show per-bundle progress (use `XMLHttpRequest.upload.onprogress`). On `200/201` mark `DONE`; on `403/422` mark `FAILED` with the server message and stop retrying; on network errors keep `PENDING`.
4. **App shell offline.** `vite-plugin-pwa` precaches the shell and i18n bundles; the manifest is Marathi-named; `display: "standalone"`; `orientation: "portrait"`.
5. **Throttled network test.** Simulate Slow 3G in browser dev tools and a flight-mode toggle during upload; the bundle must eventually arrive exactly once.

**Acceptance criteria.** With the network off, a full capture is stored; turning the network on uploads it; killing the tab mid-upload does not lose it or duplicate it (check the `photos` table count); `vitest` covers signature determinism (same input → same hash; key order irrelevant).

---

### WP-2.10 Demo photo bundles and benchmark scenario ingestion (2 h)

**Files.** `scripts/make_demo_bundles.py`, `pwa/demo_bundles/`, `data/photo_library/` (not committed if large), `ATTRIBUTION.md`, `scripts/ingest_ground_scenarios.py`.

**A. Six demo bundles (real photos, real model).** Photographers must use their own photos or openly licensed images; list every source and licence in `ATTRIBUTION.md`. Each bundle folder contains `bundle.json`, the frames, and `expected.json` (tier, excluded, flags). Choose a demo case whose parcel is a strip near the river.

| # | Bundle | How it is produced | Expected |
|---|---|---|---|
| 1 | `valid` | Two real in-app bursts, user 6 m inside the west boundary, azimuth 112° and 148°, pitch 76° | Tier 1, σ 0.14 |
| 2 | `neighbor_farm` | Same telemetry but azimuth 290° (camera pointing away) | Tier 3, `FRUSTUM_OUTSIDE_PARCEL` |
| 3 | `puddle` | Pitch 25°, camera pointing at a puddle | Tier 2, `PITCH_OUT_OF_RANGE` |
| 4 | `duplicate` | A 75%-crop + 8° rotation + brightness shift of the photo in `valid`, submitted on a different case | Tier 3, excluded, `DUPLICATE_PHOTO_EMBEDDING` |
| 5 | `screen_spoof` | A real burst of a monitor showing a flood photo (shows pixel-grid Moiré, rigid motion) | Tier 3, excluded, `SCREEN_MOIRE_SUSPECTED` |
| 6 | `compass_missing` | Valid photos but `azimuth_deg = null` | Tier 2, `COMPASS_MISSING` |

**B. Benchmark scenario ingestion (🧪).** `ingest_ground_scenarios.py` reads `benchmark/ground_scenarios.json` and, for every entry, builds a bundle and posts it through the **service layer** (not the HTTP API, for speed) with the injected `SyntheticEmbedder` (L2-5):

| Scenario | Telemetry generated | Photo content |
|---|---|---|
| `HONEST_TIER1` | position inside the parcel (3–15 m from boundary); azimuth = bearing user→parcel centroid ± 15°; second photo ≥ 35° apart; pitch 70–85° | burst synthesised from a base image (lower half shifted 6–10 px, upper half 1–3 px) |
| `HONEST_TIER2` | same but `azimuth = null` or a single photo | same |
| `NEIGHBOR_FRUSTUM` | user 5–12 m outside; azimuth = bearing user→**away** from parcel ± 20° | same |
| `CROPPED_DUPLICATE` | valid telemetry | embedding = source case's embedding at cosine 0.95 ± 0.02 |
| `PUDDLE` | pitch 20–30° | same |
| `SCREEN_SPOOF` | valid telemetry | burst with one rigid shift + 4-px grid overlay |
| `SURFING_TIER1` | valid, passes everything | distinct synthetic embeddings, so it is genuinely Tier 1 |

Everything created this way must carry `zero_shot = {"synthetic": true}` and `ground.quality.synthetic_embedding = true`. The README states plainly that embeddings and zero-shot results for the benchmark are simulated.

**Acceptance criteria.** All six demo bundles produce exactly the `expected.json` through the real HTTP endpoint; after ingestion the distribution of tiers per scenario equals the expectation (e.g. all `NEIGHBOR_FRUSTUM` → Tier 3; all `CROPPED_DUPLICATE` → excluded; all `SURFING_TIER1` → Tier 1).

---

### WP-2.11 Tests, snapshot and handoff (2 h)

1. **`tests/test_photo_anti_spoofing.py`** must include, as the detailed plan §3.1 requires: (a) 10 m outside pointing away at α = 290° → `frustum_overlap = 0.0`, rejected; (b) pointing into the parcel at α = 110° → `overlap ≥ 0.70`, accepted; (c) pitch 25° → downgraded to Tier 2; (d) rotated/cropped duplicate → cosine ≥ 0.92 caught. Add the burst, Moiré, within-bundle repeat and truth-table tests from WP-2.3 to 2.6.
2. `make test` passes for all Stage 1 and Stage 2 modules.
3. `make snapshot S=2`; restore on a clean DB; `make counts`.
4. README (Section 2.7 template) must additionally contain:
   * `parallax_ratio` and `moire_score` distributions for genuine vs screen bursts (WP-2.3 step 4);
   * measured duplicate cosines (WP-2.4 step 8);
   * photo-pipeline latency per photo on a laptop CPU (median and 95th percentile);
   * field-test table for compass offsets on the phones used (WP-2.7);
   * tier distribution per scenario after ingestion;
   * the sentence on what is **simulated** in the benchmark (L2-5) and what is **not implemented** (OTP, attestation, pre-flood landmark matching, voice transcription, sun-elevation check unless done).
5. 15-minute walk-through with Person 3, including a live submission from a phone.

### 4.X Exit Gate 2 checklist (Person 2 signs)

- [ ] `photos` and ground `observed_estimates` populated for all `ground_scenarios.json` entries
- [ ] Six demo bundles reproduce their expected tiers through the real endpoint
- [ ] A phone completes capture → offline queue → upload → database row, exactly once
- [ ] `GroundQuality` validation passes on every ground row; `excluded` rows still carry `value`/`sigma`
- [ ] Calibration numbers and what is simulated are written in the README
- [ ] Stage 1 and 2 tests green

---

# 5. STAGE 3 — Person 3: Decision Engine, Audit & Reports

**Mission.** Turn the three pillars of evidence (official record, satellite, verified ground) into a decision-support result for every case: a pooled reference interval, four detector results, a tier, an A–D evidence grade, a twelve-factor trace, a bilingual report and a tamper-evident audit log. The engine **never** approves or denies compensation; it only flags discordance for human review.

**You receive:** `handoffs/stage2/stage2.dump` + README.
**You hand over:** `handoffs/stage3/stage3.dump` + README (Exit Gate 3): every case has a `detections` row, audit entries and a renderable report.
**You never touch:** `pipeline/`, `photos`, `observed_estimates`, `frontend/`, `pwa/`. If an input looks wrong, file an `upstream-bug`.

### 5.0 Work-package summary

| WP | Title | Hours |
|---|---|---|
| 3.0 | Early smoke test on Stage 1 data (runs while Stage 2 is in progress) | (inside 3.1) |
| 3.1 | Input loading and `reconcile_observations()` | 3 |
| 3.2 | Peer selection and Detector B | 5 |
| 3.3 | Detector A, boundary logic and tier rules | 3 |
| 3.4 | Detector C (HAND-controlled timing gradient) | 2 |
| 3.5 | Detector D (`CLUSTER_BIAS`) | 3 |
| 3.6 | Twelve-factor screen | 5 |
| 3.7 | Evidence Strength Grade A–D | 3 |
| 3.8 | Hash-chained audit log | 4 |
| 3.9 | Bilingual report and numeric verifier | 4 |
| 3.10 | `/analyze`, `/report`, `/audit/verify` and v2 mode | 2 |
| 3.11 | Integration run, fixtures, snapshot, handoff | 2 |
| | **Total** | **36** |

### 5.1 Local decisions for this stage

| ID | Decision |
|---|---|
| **L3-1** | **Detectors only read inputs, never other cases' `detections`.** The result for a case therefore does not depend on the order in which cases are analysed, and the whole event can be re-run safely in any order or in parallel. |
| **L3-2** | Every factor and detector writes its computed statistics into `evidence` **even when not triggered**, so Stage 4's charts (e.g. peer quartiles) always have numbers to draw. |
| **L3-3** | `OVER_RISK` (official ≥ 0.33 but reference below 0.33) is added to the `REVIEW` conditions of §7.7, so over-assessments are not silently `CONSISTENT`. |
| **L3-4** | For `GROUND_ONLY` pooling, `ground_driven_crossing` is true only when the ground value itself is ≥ 0.33 (the v3 snippet returns `True` unconditionally, which would flag every ground-only case). |
| **L3-5** | The detailed plan's test (a) "V_sat 0.26 / V_ground 0.60" produces `SOURCE_CONFLICT` with the v3 tier-1 σ (0.09 and 0.14): `2·√(0.09²+0.14²) = 0.333 < 0.34`. The same numbers reproduce the v2 "boundary surfing" example only with σ_g = 0.15. Both variants must be tested (see WP-3.1). |

---

### WP-3.0 Early smoke test (done while Person 2 works)

Goal: discover Stage 1 surprises **before** Stage 2 finishes.

1. `make restore S=1`. Write `scripts/early_smoke.py` that, for 10 case parcels chosen across classes 0, 1, 3, 5 in `manifest.json`, loads inputs and runs `reconcile_observations` (satellite only) and the peer query of WP-3.2.
2. Report to Person 1 (as `upstream-bug` issues) anything like: peers returning 0 rows, `NULL` `ci_lo`/`ci_hi`, `quality` JSON failing `SatelliteQuality` validation, controls count 0, implausible `V_sat` distribution.
3. Keep the script; it becomes the first integration test.

---

### WP-3.1 Input loading and `reconcile_observations()` (3 h)

**Files.** `backend/services/reconciler.py`, `tests/test_pooling_and_detectors.py` (part).

**A. Input loader.**

```python
@dataclass
class CaseInputs:
    base: dict                    # one row of v_case_base
    official: Interval            # lo, hi, mid, assessed_on, assessor_token, delay_days
    sat: Obs | None               # value, sigma, lo, hi, quality(SatelliteQuality)
    ground: Obs | None            # as stored
    ground_for_pooling: Obs | None  # None if quality.excluded is true
    hazard: dict | None
    scenes: list[dict]            # scene_observations rows
    photos: list[dict]            # for evidence only
async def load_case_inputs(conn, case_id) -> CaseInputs
```

Use `v_case_base` (Stage 1). Validate `quality` JSON through the Pydantic models in `backend/models.py`; a validation failure raises a clear error naming the case and the field.

**B. `reconcile_observations(sat, ground, boundary=0.33)`.** Copy from **v3 §7.6** with these changes: use `cfg.pooling.conflict_k` and `cfg.pooling.interval_z`; apply **L3-4** for `GROUND_ONLY`; return a typed `Pooled` dataclass containing `status`, `value`, `sigma`, `lo`, `hi`, `ref_lo`, `ref_hi`, `ground_driven_crossing`, and the two source observations. Round to 4 decimals only at the output.

Behaviour table:

| sat | ground (not excluded) | Result |
|---|---|---|
| none | none | `NO_OBSERVATION`; everything `None` |
| yes | none | `SAT_ONLY`; reference = satellite interval |
| none | yes | `GROUND_ONLY`; reference = ground interval |
| yes | yes, `|Δ| > 2√(σs²+σg²)` | `SOURCE_CONFLICT`; **not pooled**; reference = satellite interval |
| yes | yes, otherwise | `OK`; inverse-variance pooled; `lo/hi = value ∓ 1.28σ`, clipped to [0, 1]; `ground_driven_crossing = sat.value < 0.33 ≤ pooled` |

**Acceptance criteria** (tests; use `pytest.approx`):

| Case | Inputs | Expected |
|---|---|---|
| Surfing (L3-5, tier-1 variant) | sat 0.26 σ 0.09; ground 0.58 σ 0.14 | `OK`, pooled ≈ 0.354, `ground_driven_crossing = True` |
| Surfing (v2 example) | sat 0.26 σ 0.09; ground 0.60 σ 0.15 | `OK`, pooled ≈ 0.350, `ground_driven_crossing = True` |
| Conflict | sat 0.26 σ 0.09; ground 0.60 σ 0.14 | `SOURCE_CONFLICT`, reference = satellite interval, no crash downstream |
| Genuine under-assessment with panic report | sat 0.60 σ 0.09 (lo 0.485); ground 0.98 σ 0.14 | `SOURCE_CONFLICT`, reference keeps the satellite interval |
| Worked example | sat 0.78 σ 0.086; ground 0.75 σ 0.14 | `OK`, value ≈ 0.772, σ ≈ 0.073, interval ≈ [0.68, 0.87] |
| Excluded ground | ground row has `excluded = true` | treated as `SAT_ONLY`; the exclusion is visible in `data_availability` |
| No data | both missing | `NO_OBSERVATION` |

---

### WP-3.2 Peer selection and Detector B (5 h)

**Files.** `backend/services/peers.py`, `backend/services/detectors.py` (B part).

**A. Candidate query** (the spectral fallback is built in; it uses the satellite value of the current case as the similarity anchor):

```sql
WITH me AS (SELECT * FROM v_case_base WHERE case_id = :case_id)
SELECT b.case_id, b.official_mid, b.assessor_token, b.village,
       o.value AS v_sat_peer,
       ST_Distance(b.geom_utm, me.geom_utm) AS dist_m
FROM v_case_base b
JOIN me ON TRUE
JOIN observed_estimates o ON o.case_id = b.case_id AND o.source = 'satellite'
WHERE b.event_id = me.event_id
  AND b.case_id <> me.case_id
  AND b.official_mid IS NOT NULL
  AND ST_DWithin(b.geom_utm, me.geom_utm, :radius_m)            -- 15 000 m
  AND ABS(o.value - :v_sat) <= :similarity                       -- 0.15
  AND (
        (me.crop IS NOT NULL AND me.sowing_date IS NOT NULL
         AND b.crop = me.crop AND ABS(b.sowing_date - me.sowing_date) <= :sow_win)
     OR ((me.crop IS NULL OR me.sowing_date IS NULL)
         AND b.spectral_cluster = me.spectral_cluster)
      )
ORDER BY dist_m
LIMIT :max_candidates;                                           -- 60
```

**B. Cross-assessor construction (v3 D2/D15; detailed plan §2.3 step 4).**
1. Partition candidates by `assessor_token`: `ext` (≠ current token) and `same` (= current token).
2. Final peers = all of `ext` plus at most `len(ext)` of `same` (the nearest ones). If the pool is larger than 60, cut `ext` first by distance, then apply the cap.
3. `peer_external_frac = len(ext_used) / len(final)`.
4. If `len(final) < cfg.peers.min_peers (8)` → Detector B is `CANNOT_ASSESS`, reason `INSUFFICIENT_PEERS` (D-17). If the current case has no satellite estimate → reason `NO_SATELLITE`.

**C. Robust z-score.**

```python
def robust_z(x, peer_mids, scale_floor=0.05):
    med = np.median(peer_mids)
    mad = np.median(np.abs(np.asarray(peer_mids) - med))
    scale = max(1.4826 * mad, scale_floor)          # floor avoids z → ∞ when all peers agree
    return (x - med) / scale, med, mad
```

* Fires when `|z| ≥ detectors.peer_z_flag (2.0)`; "NOTE level" when `1.5 ≤ |z| < 2.0`.
* Evidence always includes: `peer_n`, `peer_external_frac`, `peer_median`, `q25`, `q75`, `mad`, `z`, and the list of peer case ids (max 60) so officers can inspect them.
* Writes `detections.peer_n`, `peer_external_frac`, `peer_z`.

**Acceptance criteria.**
* Worked example: 20 peers (12 external), median 0.60, MAD 0.09 → `z = −3.00 ± 0.01`.
* A village with 40 parcels all at 20% under one token and 6 external peers at 60%: the cap keeps at most 6 same-token peers, so the median is not 20%; `peer_external_frac ≥ 0.5`.
* A parcel with `crop IS NULL` finds peers through `spectral_cluster`.
* A parcel with 5 candidate peers → `CANNOT_ASSESS` (`INSUFFICIENT_PEERS`), not "no flag".
* Query plan uses the GiST index (`EXPLAIN` in the README).

---

### WP-3.3 Detector A, boundary logic and tier rules (3 h)

**Files.** `backend/services/detectors.py` (A part), `backend/services/tiering.py`.

**A. Detector A** (inputs: `Pooled`, official interval, satellite):

```python
ref_value = pooled.value                    # = sat value on SOURCE_CONFLICT, ground value on GROUND_ONLY
gap = ref_value - official.mid              # signed; positive = official is lower than evidence
intervals_separated = official.hi < pooled.ref_lo or official.lo > pooled.ref_hi

# boundary_crossing, first match wins
if official.hi < 0.33 and sat and sat.lo >= 0.33:                       'SAT_UNDER_RISK'
elif official.hi < 0.33 and pooled.ground_driven_crossing and pooled.lo >= 0.33
     and (sat is None or sat.value < 0.33):                              'GROUND_DRIVEN_BOUNDARY_CROSSING'
elif official.lo >= 0.33 and pooled.ref_hi < 0.33:                       'OVER_RISK'
else:                                                                    'NONE'
```

Writes `ref_lo`, `ref_hi`, `pooled_value/lo/hi`, `gap`, `intervals_separated`, `boundary_crossing`.

**B. Tier assignment** (implements v3 §7.7 with D-13 and L3-3; the order matters):

```python
def assign_tier(a, b, c, d, pooled, grade, gap, z):
    if grade == "D":                                   # D-13
        return "INSUFFICIENT_EVIDENCE"
    sep25 = a.intervals_separated and abs(gap) >= cfg.detectors.gap_priority      # 0.25
    sep20 = a.intervals_separated and abs(gap) >= cfg.detectors.gap_review        # 0.20
    if (a.boundary == "SAT_UNDER_RISK" and (b.fires or d.fires)) \
       or (sep25 and grade in ("A", "B") and (b.fires or d.fires)):
        return "PRIORITY_REVIEW"
    if sep20 or a.boundary in ("SAT_UNDER_RISK", "GROUND_DRIVEN_BOUNDARY_CROSSING", "OVER_RISK") \
       or b.fires or d.fires or (pooled.status == "SOURCE_CONFLICT" and abs(gap) >= 0.20):
        return "REVIEW"
    if abs(gap) >= cfg.detectors.gap_note or (b.z is not None and 1.5 <= abs(b.z) < 2.0) or c.fires:
        return "NOTE"
    return "CONSISTENT"
```

The grade is computed **before** the tier (WP-3.7). The grade never reads the tier, so there is no circularity.

**Acceptance criteria.** One unit test per branch of the tier ladder; worked example gives `SAT_UNDER_RISK`, `gap ≈ +0.57`, `intervals_separated = True`, tier `PRIORITY_REVIEW`; a `GROUND_ONLY` case with official 0.15 and ground 0.70 gives `GROUND_DRIVEN_BOUNDARY_CROSSING` but **not** `SAT_UNDER_RISK`; Grade D with a large gap is `INSUFFICIENT_EVIDENCE`. **Plan test (b)** (sat 0.60, ground 0.98, official 0.15) reaches `PRIORITY_REVIEW` only if Detector B or D also fires, so its fixture must include at least 10 peers (≥ 5 from other assessors) with official medians near 0.60, or a same-assessor cohort of ≥ 5 flat records; without them the correct tier is `REVIEW`. Test both variants.

---

### WP-3.4 Detector C: HAND-controlled timing gradient (2 h)

**Files.** `backend/services/detectors.py` (C part).

**Specification (D-6).**
1. `delay_days = assessed_on − event.peak_date` (already in `v_case_base`).
2. Cohort = all cases of the event with a satellite estimate, within `timing_radius_km` (25 km) and `|hand_m − this.hand_m| ≤ timing_hand_band_m` (2.5), **including** the current case.
3. If cohort size `< timing_min_cohort (10)` → `CANNOT_ASSESS` (`SMALL_COHORT`); if `delay_days` has no variation in the cohort → `CANNOT_ASSESS` (`NO_DELAY_VARIATION`).
4. `x = delay_days`, `y = official_mid − sat_value`; `rho, p = scipy.stats.spearmanr(x, y)`.
5. **Fires** when `rho ≤ −0.40`, `p < 0.05` **and** this case's delay is in the top tercile (≥ the 67th percentile of cohort delays).
6. Evidence: `rho`, `p`, `cohort_n`, `delay_days`, `delay_percentile`, `hand_band`. Writes `detections.timing_rho`.

**Acceptance criteria.** A synthetic cohort where official mid falls 0.02 per extra day of delay fires for a 20-day-delay case and not for a 4-day-delay case; the same pattern in a different HAND band is not used; a cohort of 9 → `CANNOT_ASSESS`.

---

### WP-3.5 Detector D: `CLUSTER_BIAS` (3 h)

**Files.** `backend/services/detectors.py` (D part).

**Specification (D-5).**

```sql
SELECT b.case_id, b.official_mid, b.damage_hi, o.ci_lo AS sat_lo
FROM v_case_base b
JOIN observed_estimates o ON o.case_id = b.case_id AND o.source = 'satellite'
WHERE b.event_id = :event_id
  AND b.assessor_token = :token
  AND (b.assessed_on = :assessed_on OR b.village = :village);
```

Then:
* `n = len(cohort)`; `iqr = Q75 − Q25` of `official_mid`; `med_gap = median(sat_lo − damage_hi)`.
* **Fires** when `n ≥ cluster_min_cases (5)`, `iqr ≤ cluster_max_iqr (0.05)` and `med_gap ≥ cluster_min_gap (0.20)`.
* Writes `detections.cluster_bias_flag`. Evidence: `cohort_n`, `iqr`, `median_gap`, `assessor_token`, `village`, `date`. **Never** put other officers' personal data beyond the pseudonymous token in the evidence.
* Escalation: when it fires, every case in the cohort is eligible for `PRIORITY_REVIEW` via the tier rules; the dashboard groups them by `assessor_token` (Stage 4).
* Because of L3-1, each case recomputes the cohort itself; for the full-event run, memoise by `(event_id, token, assessed_on, village)` inside a single `analyze_all` process.

**Acceptance criteria.** 10 village farms all at 0.20 under `ASR-09` with satellite lows ≥ 0.45 → fires; same 10 with official values spread over [0.1, 0.5] → does not fire (IQR); 4 farms → does not fire (count); official values flat but satellite also ≈ 0.20 → does not fire (gap).

---

### WP-3.6 Twelve-factor screen (5 h)

**Files.** `backend/services/factors.py`, `tests/test_factors_and_grade.py` (part).

**Contract.** `evaluate_factors(inputs, pooled, detectors) -> list[FactorResult]` always returns **12 entries in enum order** (Section 2.3), each with `status ∈ {TRIGGERED, NOT_TRIGGERED, CANNOT_ASSESS}`, `evidence` and, for `CANNOT_ASSESS`, a `reason`. No factor changes any number; they explain.

| # | Code | Triggers when | `CANNOT_ASSESS` when | Evidence (always filled) |
|---|---|---|---|---|
| 1 | `LATE_ASSESSMENT` | `delay_days ≥ 7` **and** SAR water had receded by then (`water_frac_recession ≤ 0.10`) **and** Detector C fired | Detector C is `CANNOT_ASSESS`, or `water_frac_recession` is `null` (D-10) | `delay_days`, `water_frac_peak`, `water_frac_recession`, `rho`, `p` |
| 2 | `PEER_INCONSISTENCY` | Detector B fires | Detector B is `CANNOT_ASSESS` | peer stats (WP-3.2) |
| 3 | `BLANKET_PANCHNAMA_CLUSTER` | Detector D fires | cohort smaller than 5 is `NOT_TRIGGERED`; no satellite → `CANNOT_ASSESS` | `cohort_n`, `iqr`, `median_gap`, token |
| 4 | `PARTIAL_PARCEL_SUBMERGENCE` | `area_dmg_frac − loss_attr ≥ 0.15` | no satellite | `area_dmg_frac`, `loss_attr`, `n_eff` |
| 5 | `SILT_RECOVERY_OBSERVED` | satellite `quality.flags` contains it | `flags_assessable = false` or no satellite | W1 vs W2 `ndvi`, `ndre` from `scene_observations` |
| 6 | `DELAYED_WATERLOGGING_ROT` | satellite `quality.flags` contains it | `flags_assessable = false` or no satellite | W1 vs W2 `ndvi`, `ndmi`, `soil_class` |
| 7 | `DISCHARGE_EXPOSURE` | `discharge_exposure.in_reach` and `hand_pctile_in_taluka ≤ 25` | no `hazard_context` | `release_cusecs`, `distance_to_river_m`, `hand_m`, `hand_pctile` |
| 8 | `GROUND_DRIVEN_BOUNDARY_CROSSING` | `boundary_crossing == 'GROUND_DRIVEN_BOUNDARY_CROSSING'` | no ground estimate | `v_sat`, `v_ground`, `pooled` |
| 9 | `PHOTO_INTEGRITY_ALERT` | ground `quality.flags` contains any of `DUPLICATE_PHOTO_EMBEDDING`, `SCREEN_MOIRE_SUSPECTED`, `BURST_PARALLAX_FAIL`, `FRUSTUM_OUTSIDE_PARCEL`, `OUTSIDE_PARCEL_BOUNDARY` | no ground estimate | similarity, `frustum_overlaps`, azimuths, photo ids, flags |
| 10 | `CROP_MISMATCH` | ground flags contain `CROP_MISMATCH` | no ground estimate | declared crop, `zero_shot` top class and probability |
| 11 | `SOURCE_CONFLICT` | `pooled.status == 'SOURCE_CONFLICT'` | — | `v_sat`, `v_ground`, `|Δ|`, `2σ_comb` |
| 12 | `NON_FLOOD_CAUSE_POSSIBLE` | satellite `onset_in_window == false`, **or** `controls_deficit_median ≥ 0.5 × deficit_farm`, **or** hazard `plausibility == 'LOW'` | no satellite and no hazard | onset flag, control deficit, farm deficit, plausibility |

Also write `detections.data_availability` (Section 2.4-E): which windows exist, number of SAR scenes, ground tier, `peer_n`, `controls_n`, and a `missing` list for anything that caused a `CANNOT_ASSESS`.

**Acceptance criteria.** One test per factor (triggered, not triggered, cannot-assess); the worked-example case triggers `PEER_INCONSISTENCY`, `BLANKET_PANCHNAMA_CLUSTER`, `PARTIAL_PARCEL_SUBMERGENCE` is **not** triggered (0.78 − 0.74 = 0.04), `DISCHARGE_EXPOSURE` triggered; a case with no ground has factors 8–10 as `CANNOT_ASSESS`; the list always has length 12.

---

### WP-3.7 Evidence Strength Grade A–D (3 h)

**Files.** `backend/services/grading.py`, `tests/test_factors_and_grade.py` (part).

The v3 spec §7.9 is missing; this WP defines it (D-14, 🎯 all thresholds tuned later).

**Five dimensions (max 10 points):**

| Dimension | Points | Rule |
|---|---|---|
| **Observation coverage** | 0–3 | Satellite valid (clear fraction ≥ 0.40 in the used window) = **2**; verified ground (tier 1 or 2, not excluded) = **+1**; ground only (no satellite) = 1; nothing usable = **0** |
| **Spatial reliability** | 0–2 | `n_eff ≥ 25` → 2; `8 ≤ n_eff < 25` → 1; `< 8` → 0 (and flag `SMALL_PARCEL_LIMITATION`). No satellite → 0 |
| **Independent agreement** | 0–2 | Satellite and ground both usable and `|Δ| ≤ σ_comb` → 2; `σ_comb < |Δ| ≤ 2σ_comb` → 1; satellite only with SAR agreement (SAR `water_frac_peak ≥ 0.20` when `v_sat ≥ 0.33`, or `< 0.20` when `v_sat < 0.33`) → 1; conflict or no corroboration → 0 |
| **Attribution quality** | 0–2 | Start at 2, subtract 1 for each of: controls < 5; `NON_FLOOD_CAUSE_POSSIBLE` triggered; plausibility `LOW`. Floor 0. |
| **Margin** | 0–1 | 1 if the reference interval does **not** straddle 0.33 (`ref_lo ≥ 0.33` or `ref_hi < 0.33`), else 0 |

**Letter:** `A` if total ≥ 8, `B` if 6–7, `C` if 4–5, `D` if ≤ 3 (config `grade.a_min/b_min/c_min`).

**Caps applied after the letter** (record each in `grade_detail.caps_applied`):
* Observation coverage = 0 → **D** (forced).
* `boundary_crossing == 'GROUND_DRIVEN_BOUNDARY_CROSSING'` → at most **B** (v3 D5).
* `SMALL_PARCEL_LIMITATION` → at most **C**.
* `LOW_CLEAR_FRACTION` → at most **C** (D-22).
* `SOURCE_CONFLICT` → at most **C** (a conflicting pair is not strong evidence).

Write `grade`, `grade_points`, `grade_detail` (Section 2.4-D with one human-readable `rationale` string per dimension).

**Acceptance criteria.** Worked example = `3 + 2 + 2 + 2 + 1 = 10` → **A**, no caps; the surfing case (sat 0.26, ground 0.58 at tier 1) is capped at **B**; a strip parcel with `n_eff = 6` is at most **C**; ground-only with tier 3 → low score; no observation → **D**; changing a threshold in a test config changes the result (config is really used).

---

### WP-3.8 Hash-chained audit log (4 h)

**Files.** `sql/03_audit_hash_chain.sql`, `backend/services/audit.py`, `backend/routers/audit.py`, `tests/test_audit_hash_chain.py`.

**A. SQL** (`03_audit_hash_chain.sql`, re-runnable):
1. `audit_log` table, `audit_chain()` trigger function and `trg_audit_chain` exactly as in **v3 §6** (UTC-canonical `jsonb_build_array` input, `pg_advisory_xact_lock(424242)`).
2. `audit_block()` trigger on `UPDATE OR DELETE` (row-level) **plus** a statement-level `BEFORE TRUNCATE` trigger raising the same exception (row triggers do not stop `TRUNCATE`).
3. Verification function that recomputes the chain **inside the database** so JSON canonicalisation is identical to the writer:

   ```sql
   CREATE OR REPLACE FUNCTION audit_verify()
   RETURNS TABLE(ok boolean, n bigint, first_bad_id bigint) AS $$
     WITH r AS (
       SELECT id, prev_hash, row_hash,
              lag(row_hash) OVER (ORDER BY id) AS lag_hash,
              digest(COALESCE(lag(row_hash) OVER (ORDER BY id), ''::bytea) ||
                     convert_to(jsonb_build_array(case_id::text, actor, event, payload,
                       COALESCE(model_versions, '{}'::jsonb),
                       to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text, 'UTF8'),
                     'sha256') AS expected
       FROM audit_log)
     SELECT NOT EXISTS (SELECT 1 FROM r WHERE expected <> row_hash OR prev_hash IS DISTINCT FROM lag_hash),
            (SELECT count(*) FROM r),
            (SELECT min(id) FROM r WHERE expected <> row_hash OR prev_hash IS DISTINCT FROM lag_hash);
   $$ LANGUAGE sql STABLE;
   ```

4. A SQL helper so Stage 4 does not import Python from this stage:

   ```sql
   CREATE OR REPLACE FUNCTION append_audit_event(p_case uuid, p_actor text, p_event text, p_payload jsonb)
   RETURNS bigint AS $$
     INSERT INTO audit_log(case_id, actor, event, payload, model_versions)
     VALUES (p_case, p_actor, p_event, p_payload, '{}'::jsonb) RETURNING id;
   $$ LANGUAGE sql;
   ```

**B. `audit.py`.**
* `append_audit(conn, case_id, actor, event, payload, model_versions)`; allowed `event` values: `ANALYZE_RUN`, `REVIEW_RECORDED`, `GROUND_SEEN`, `REPORT_RENDERED`.
* `ANALYZE_RUN` payload ≤ 4 KB: `inputs_digest` (SHA-256 of the canonical JSON of the inputs), `tier`, `grade`, `grade_points`, `pooling_status`, `boundary_crossing`, list of triggered factor codes, `ground_tier`, `photo_ids`, `config_sha`.
* `verify_chain(conn)` calls `audit_verify()` and returns the result dictionary.

**C. Endpoint.** `GET /audit/verify` → `{"ok": true, "rows": 312, "first_bad_id": null, "checked_at": "…Z"}`.

**Acceptance criteria** (`test_audit_hash_chain.py`, D-7):
1. `SET TIME ZONE 'Asia/Kolkata'`, insert 20 rows (several concurrently from two connections), then `SET TIME ZONE 'UTC'` and `audit_verify()` returns `ok = true, n = 20`.
2. `UPDATE audit_log …` raises `audit_log is append-only`; so does `DELETE`; so does `TRUNCATE`.
3. Tamper simulation: disable the trigger as superuser, modify one `payload`, re-enable; `audit_verify()` returns `ok = false` and `first_bad_id` equals that row.

---

### WP-3.9 Bilingual report and numeric verifier (4 h)

**Files.** `backend/services/reporter.py`, `backend/templates/report_en.j2`, `report_mr.j2`, `tests/test_report_verifier.py`.

**A. Facts builder.** `build_facts(inputs, detection) -> dict` produces **every number a report may contain**. Keys (ratios stored as 0–1 floats; the templates format them):

`case_ref` (survey number), `village`, `taluka`, `official_lo`, `official_hi`, `official_mid`, `assessed_on` (ISO), `delay_days`, `observed_val`, `observed_lo`, `observed_hi`, `sat_val`, `ground_val`, `ground_tier`, `area_dmg_frac`, `loss_attr`, `peer_median`, `peer_n`, `cluster_n`, `cluster_iqr`, `cluster_gap`, `release_cusecs`, `peak_date`, `tier`, `grade`, `factors_triggered` (codes), `declared_crop`, `photo_reason` (words only), `boundary` (0.33). `observed_val` is the pooled value, or the satellite value on conflict.

**B. Template rules.**
1. Sections: **(1)** Summary with tier in plain words; **(2)** What the record says; **(3)** What was observed (satellite, ground, tier of ground evidence); **(4)** Why this case was flagged (one sentence per triggered factor, texts below); **(5)** Hazard context; **(6)** Data limits (every `CANNOT_ASSESS` reason); **(7)** Mandatory closing: "This is a decision-support note. A human officer decides." / "हा निर्णय-सहाय्य अहवाल आहे. अंतिम निर्णय अधिकारी घेतील."
2. Templates never use the words fraud, false, guilty, approve, reject, deny (Marathi equivalents: फसवणूक, खोटे, दोषी, मंजूर, नामंजूर). A test scans every rendered report for them.
3. In the Marathi template, numbers are rendered with Devanagari digits through a Jinja filter `num(lang)`; the English template uses ASCII. Percentages are formatted `{{ x|pct }}` → `round(x*100)` plus `%`.
4. Factor sentences (use these exact texts as the base; have a native speaker review the Marathi):

| Factor | English | Marathi |
|---|---|---|
| `LATE_ASSESSMENT` | The assessment was recorded {{delay_days}} days after the flood peak, after floodwater had receded. | पुराच्या शिखरानंतर {{delay_days}} दिवसांनी, पाणी ओसरल्यानंतर, पंचनामा नोंदवला गेला. |
| `PEER_INCONSISTENCY` | Similarly affected parcels assessed by other officers have a median record of {{peer_median}}%, against {{official_mid}}% for this parcel. | इतर अधिकाऱ्यांनी मूल्यांकन केलेल्या तशाच बाधित शेतांचे सरासरी नुकसान {{peer_median}}% आहे, तर या शेताची नोंद {{official_mid}}% आहे. |
| `BLANKET_PANCHNAMA_CLUSTER` | {{cluster_n}} parcels under the same assessor have almost identical records (spread {{cluster_iqr}} points) while satellite evidence is higher by a median of {{cluster_gap}} points. | एकाच मूल्यांकन अधिकाऱ्याच्या {{cluster_n}} शेतांच्या नोंदी जवळजवळ सारख्या आहेत (फरक {{cluster_iqr}} गुण), तर उपग्रह पुरावा सरासरी {{cluster_gap}} गुणांनी जास्त आहे. |
| `PARTIAL_PARCEL_SUBMERGENCE` | About {{area_dmg_frac}}% of the parcel area is severely damaged, although the parcel average is {{loss_attr}}%. | शेताच्या सुमारे {{area_dmg_frac}}% क्षेत्राचे गंभीर नुकसान झाले आहे, मात्र संपूर्ण शेताची सरासरी {{loss_attr}}% आहे. |
| `SILT_RECOVERY_OBSERVED` | Early images showed heavy loss, but later images show recovery; silt may have hidden living crop. | सुरुवातीच्या प्रतिमांत मोठे नुकसान दिसले, पण नंतरच्या प्रतिमांत सुधारणा दिसते; गाळामुळे जिवंत पीक झाकले गेले असू शकते. |
| `DELAYED_WATERLOGGING_ROT` | Loss appeared only in later images, consistent with root rot after waterlogging in black soil. | नुकसान फक्त नंतरच्या प्रतिमांत दिसले; काळ्या जमिनीत पाणी साचल्यामुळे मुळे कुजण्याशी हे सुसंगत आहे. |
| `DISCHARGE_EXPOSURE` | The parcel lies in the river reach affected by the reported dam release of about {{release_cusecs}} cusecs, at low elevation above the river. | सुमारे {{release_cusecs}} क्युसेक धरण विसर्गामुळे बाधित नदीपट्ट्यात, नदीपासून कमी उंचीवर हे शेत आहे. |
| `GROUND_DRIVEN_BOUNDARY_CROSSING` | Satellite evidence alone is below 33% ({{sat_val}}%); the combined estimate crosses 33% only because of the farmer report. Field verification is advised. | केवळ उपग्रह पुरावा 33% पेक्षा कमी ({{sat_val}}%) आहे; शेतकऱ्याच्या अहवालामुळेच एकत्रित अंदाज 33% पेक्षा वर जातो. प्रत्यक्ष तपासणी सुचवली आहे. |
| `PHOTO_INTEGRITY_ALERT` | The submitted photos did not pass an automatic check ({{photo_reason}}); the ground report was given reduced or no weight. | सादर केलेले फोटो स्वयंचलित तपासणीत उत्तीर्ण झाले नाहीत ({{photo_reason}}); शेतकऱ्याच्या अहवालाला कमी किंवा शून्य महत्त्व दिले आहे. |
| `CROP_MISMATCH` | The photos appear to show a different crop from the declared crop ({{declared_crop}}). | फोटोंमधील पीक नोंदवलेल्या पिकापेक्षा ({{declared_crop}}) वेगळे दिसते. |
| `SOURCE_CONFLICT` | Satellite ({{sat_val}}%) and farmer report ({{ground_val}}%) disagree too much to combine; the satellite value is used as the reference. | उपग्रह ({{sat_val}}%) आणि शेतकऱ्याचा अहवाल ({{ground_val}}%) यात खूप तफावत आहे; म्हणून उपग्रह मूल्य संदर्भ म्हणून वापरले आहे. |
| `NON_FLOOD_CAUSE_POSSIBLE` | Timing, nearby control parcels or rainfall suggest the damage may not be flood-related. | वेळ, जवळच्या नियंत्रण शेतांची स्थिती किंवा पाऊस पाहता नुकसान पुराशी संबंधित नसण्याची शक्यता आहे. |

**C. Numeric verifier.** Implement `verify_llm_report(text, facts)` and `_collect_allowed_numbers` from **v3 §7.10**. Known limits to fix or document:
* The standard constants set `{33, 80, 90, 95, 10}` is the only allowance outside `facts`; add `12` only if you mention "12 factors".
* The reversal check currently handles one pattern; extend it to also catch the Marathi keywords (`अधिकृत`, `पंचनामा`, `नोंद`) in front of the observed percentage, and the English phrase "record is".
* The verifier is applied to **LLM-polished** text only. Template output is deterministic and is tested directly instead.

**D. Optional LLM polish.** Off by default (`report.llm_polish_enabled: false`). If switched on: send `facts` + the template text with the instruction "Rewrite in plain language; do not add, remove or change any number or date." Verify the answer; if verification fails, return the template text. Store `source: "template" | "llm"` in the response. The model name comes from an environment variable; never hard-code a model ID in the repository (v1's retired-model failure).

**Acceptance criteria** (`test_report_verifier.py`, as the detailed plan §3.1 requires):
* Accepts: English text with `"64%"` and `"25 July"` when `facts` has `0.64` and `"2024-07-25"` → `True`.
* Accepts: Marathi text with `"६४%"` → `True`.
* Rejects: "Official record is 64%" when `official_mid = 0.20` and `observed_val = 0.64` → `False`.
* Rejects: an invented figure (`"71%"` not in facts) → `False`.
* Both templates render for 10 different cases without exceptions, contain no banned words, and every number in the English **and** Marathi output passes the verifier (the verifier is also run on the templates as a self-check).

---

### WP-3.10 `/analyze`, `/report`, `/audit/verify` and v2 mode (2 h)

**Files.** `backend/routers/analyze.py`, `backend/routers/reports.py`, `backend/routers/audit.py`, `scripts/analyze_all.py`.

**`POST /cases/{id}/analyze?mode=v3|v2`** runs the whole pipeline in **one database transaction** (detailed plan §2.3):

1. `load_case_inputs`
2. `reconcile_observations`
3. Detectors A, B, C, D
4. Factors, then grade, then tier (order matters: grade before tier)
5. `UPSERT` into `detections` (`INSERT … ON CONFLICT (case_id) DO UPDATE`)
6. `append_audit(... 'ANALYZE_RUN' ...)`
7. Commit. Return the detection as JSON.

Properties: **idempotent** (re-running yields the same row; only `computed_at` and a new audit row differ) and **order-independent** (L3-1). Errors roll back everything, including the audit row.

**v2 mode (D-16).** Behaviour that reproduces v2 for the ablation, used only on the cloned event: no boundary-surfing guard and no `GROUND_DRIVEN` status; peers are the nearest 60 regardless of assessor; no spectral fallback (exact `crop` + `sowing_date` only → `INSUFFICIENT_PEERS`); Detector D disabled; on `SOURCE_CONFLICT` the reference interval is **empty** and Detectors A/B/D are skipped (the exact crash behaviour v2 had, handled gracefully). `model_versions.engine = "v2"`.

**`GET /cases/{id}/report?lang=mr|en`** → `{"lang":"mr","text":"…","source":"template","facts_digest":"…"}`; `409` if the case has not been analysed; `422` for another language; writes `REPORT_RENDERED` to the audit log (hash of the text only).

**`scripts/analyze_all.py`**: `--event`, `--mode`, `--workers 1..4` (each worker uses its own connection and its own per-case transaction; the advisory lock in the audit trigger serialises only the insert), progress bar, final summary of tier counts.

**Acceptance criteria.** Calling `/analyze` twice leaves one `detections` row and two audit rows; shuffling the order of cases yields identical `detections`; an induced exception inside factors leaves no partial `detections` or audit rows.

---

### WP-3.11 Integration run, fixtures, snapshot, handoff (2 h)

1. `python scripts/analyze_all.py --event MH-2024-07-PUNE` and the V2 event. Expect zero failures; record runtime.
2. **Sanity table** (not the official benchmark; Stage 4 owns that), printed into the README: for each class of `manifest.json`, the share of cases whose `expected_flag` was raised. Tag it "🧪 synthetic officials on real imagery". Do not tune thresholds to make the table look good; if numbers are poor, report them and open an `upstream-bug` for the likely source (satellite value, photo tier, config).
3. `make test` for all modules of Stages 1–3 (including the six required by the detailed plan: `test_unclipped_did`, `test_strip_parcel_weights`, `test_photo_anti_spoofing`, `test_pooling_and_detectors`, `test_report_verifier`, `test_audit_hash_chain`).
4. **Fixtures for Stage 4** (`fixtures/detections/*.json`): one illustrative real row for each tier (`PRIORITY_REVIEW`, `REVIEW`, `NOTE`, `CONSISTENT`, `INSUFFICIENT_EVIDENCE`), plus `worked_example.json` hand-built to match v3 §10 exactly. `fixtures/case_detail/<case_id>.json` for about 12 cases: a raw export (`scripts/export_case_bundle.py`) containing `{base, official, satellite, ground, photos, hazard, scenes, detection, report_en, report_mr}`; Stage 4 maps this to its API shape.
5. `make snapshot S=3`; restore on a clean DB; `GET /audit/verify` returns `ok`.
6. README (Section 2.7 template) must also list: tier and grade distributions, count of `CANNOT_ASSESS` per factor, runtime per case, the thresholds you changed (if any) and why, and every ambiguity of the spec you resolved (L3-1 … L3-5, D-13, D-14, D-17).
7. 15-minute walk-through with Person 4, including one case per tier.

### 5.X Exit Gate 3 checklist (Person 3 signs)

- [ ] All 300 cases have a `detections` row with exactly 12 factors; no analysis errors
- [ ] V2 event analysed in v2 mode
- [ ] `/audit/verify` returns `ok: true` after restore under a different session timezone
- [ ] Both report languages render for every case and pass the banned-word and number checks
- [ ] Six required `pytest` modules green, plus factor/grade tests
- [ ] Fixtures exported for Stage 4; README complete, including the sanity table and its caveats

---

# 6. STAGE 4 — Person 4: Officer Dashboard, Benchmark & Demo

**Mission.** Make the engine usable and believable. Build the read APIs and every officer screen, measure the system honestly with the injection benchmark (v2 vs v3), and deliver a demo that works with the Wi-Fi off. You finish the project.

**You receive:** `handoffs/stage3/stage3.dump` + README, `fixtures/detections/`, `fixtures/case_detail/`, `contracts/openapi.json`.
**You hand over:** the finished project plus `handoffs/stage4/README.md` (Exit Gate 4).
**You never touch:** satellite or ground estimate logic, detector or grading logic. If a number looks wrong, file an `upstream-bug` with the owner of that stage; do not "fix" it in the UI.

### 6.0 Work-package summary

| WP | Title | Hours |
|---|---|---|
| 4.1 | Read APIs: cases, queue, fairness, review, photo thumbnails | 4 |
| 4.2 | Frontend scaffold, typed client, fixtures mode, offline basemap | 2 |
| 4.3 | `ReviewQueue.tsx` | 3 |
| 4.4 | `EvidenceLadder.tsx` | 4 |
| 4.5 | `ParcelFrustumMap.tsx` | 5 |
| 4.6 | `FactorScreenCard.tsx`, grade breakdown, report and review panels, case page | 3 |
| 4.7 | `FairnessMonitor.tsx` | 3 |
| 4.8 | Injection benchmark and v2-vs-v3 ablation | 5 |
| 4.9 | API contract tests, `make smoke`, offline check | 1 |
| 4.10 | Pitch deck, demo script, Q&A sheet, rehearsal, backup video | 3 |
| | **Total** | **33** |

### 6.1 Local decisions for this stage

| ID | Decision |
|---|---|
| **L4-1** | **The front end computes no statistics and no geometry.** Frustum polygons come from the SQL function `frustum_geojson()` (Stage 2); pooled values, gaps, z-scores and grades come from `detections`. This keeps the UI from disagreeing with the audit trail. |
| **L4-2** | `VITE_USE_FIXTURES=1` makes the UI read `fixtures/` instead of the API. Both modes must render the same screens. |
| **L4-3** | Officer identity is a pseudonymous `X-Officer-Token` header (a demo value such as `OFF-014`). Real authentication and roles are 🗺️. Farmer identifiers are shown masked (last 3 characters). |
| **L4-4** | The demo must run **offline**: no map tile server, no CDN fonts. The base map is a pre-rendered Sentinel-2 true-colour PNG placed as a Leaflet `ImageOverlay`; fonts (including Noto Sans Devanagari) are bundled locally. |
| **L4-5** | Benchmark "flag" means tier ∈ {`PRIORITY_REVIEW`, `REVIEW`}. A continuous benchmarking score is used **only** to read recall at a fixed 5% false-flag rate; it is a measurement device, not part of the product. |

---

### WP-4.1 Read APIs (4 h)

**Files.** `backend/routers/cases.py`, `backend/routers/events.py`, additions to `backend/models.py`, `contracts/openapi.json` (regenerate with `make openapi`).

**Intake (30 min, not counted).** `make restore S=3`; read the Stage 3 README; open three `fixtures/case_detail/*.json` files; note any field you need that is not there and ask Person 3 now.

**A. `POST /cases`** — create or update a case together with its official record (used by loaders and tests). Body: `event_id`, `parcel_id` **or** `survey_no`, `farmer_ref`, `official: {damage_lo, damage_hi, assessed_on, assessor_token}`. Upsert on `(event_id, parcel_id)`. Validation: `0 ≤ lo ≤ hi ≤ 1`; `assessed_on ≥ event.start_date`. Returns the case id.

**B. `GET /cases/{id}`** — the one aggregated view the UI needs. One round trip, gzip-compressed, target under 300 ms for a strip parcel with a pixel grid.

```json
{
  "case":   {"case_id": "…", "event_id": "MH-2024-07-PUNE", "status": "open",
            "survey_no": "PUN-HAV-0001", "village": "Synthetic-V03", "taluka": "Haveli",
            "area_ha": 0.74, "min_width_m": 22.0, "crop": "soybean", "sowing_date": "2024-06-24",
            "soil_class": "alluvial", "farmer_ref_masked": "…123",
            "geometry": {"type": "Polygon", "coordinates": []}, "centroid": [73.85, 18.48],
            "is_synthetic": true},
  "official":  {"lo": 0.15, "hi": 0.25, "mid": 0.20, "assessed_on": "2024-08-01",
                "assessor_token": "ASR-14", "delay_days": 7},
  "satellite": {"value": 0.78, "sigma": 0.086, "lo": 0.67, "hi": 0.89,
                "quality": {"…": "SatelliteQuality without pixel_grid"},
                "scenes": [{"sensor": "S2_IMMEDIATE", "scene_date": "2024-08-03", "clear_frac": 0.72}]},
  "pixel_grid": {"type": "FeatureCollection", "features": []},
  "neighbors":  {"type": "FeatureCollection", "features": []},
  "ground":    {"value": 0.75, "sigma": 0.14, "lo": 0.57, "hi": 0.93, "tier": 1, "excluded": false,
                "flags": [], "form": {"damaged_share_pct": 75, "water_depth_band": "KNEE"},
                "photos": [{"photo_id": "…", "lat": 18.4802, "lon": 73.8501, "azimuth_deg": 112.0,
                            "pitch_deg": 76.0, "frustum_overlap": 0.84, "dist_to_parcel_m": 0.0,
                            "status": "PASS", "flags": [], "frustum_geojson": {},
                            "thumb_url": "/photos/…/thumb"}]},
  "hazard":    {"rain_imd_class": "VERY_HEAVY", "hand_m": 1.4, "plausibility": "HIGH",
                "discharge_exposure": {"release_cusecs": 37500, "in_reach": true}},
  "detection": {"tier": "PRIORITY_REVIEW", "grade": "A", "grade_points": 10, "grade_detail": {},
                "pooling_status": "OK", "pooled": {"value": 0.77, "lo": 0.68, "hi": 0.87},
                "ref": {"lo": 0.68, "hi": 0.87}, "gap": 0.57, "boundary_crossing": "SAT_UNDER_RISK",
                "intervals_separated": true,
                "peer": {"n": 20, "external_frac": 0.60, "z": -3.0, "median": 0.60, "q25": 0.52, "q75": 0.66},
                "cluster_bias": true, "timing_rho": -0.52,
                "factors": [], "data_availability": {}, "model_versions": {}, "computed_at": "…Z"},
  "reviews": [],
  "report_available": true
}
```

Sources and rules:
* `ground` is `null` when no ground row exists; `ground.excluded` and flags are passed through so the UI can show *why* a row is hatched.
* `photos[].frustum_geojson` = `SELECT frustum_geojson(lon, lat, azimuth, 25, 60)` (WP-2.1). Never compute it in the browser (L4-1).
* `neighbors` = parcels within 150 m of the case parcel (`ST_DWithin` on `geom_utm`), geometry only (no survey numbers, no names) so the map can show whether a camera pointed at someone else's field.
* `peer.q25/q75/median` come from the `PEER_INCONSISTENCY` factor evidence (L3-2). If the factor is `CANNOT_ASSESS` the fields are `null`.
* The pixel grid is returned as its own key so the client can lazy-load it; it is stripped from `satellite.quality`.
* `404` if unknown; `409` if the case exists but has no `detections` row yet (returns the partial case so the UI can say "not analysed yet").

**C. `GET /photos/{photo_id}/thumb`** (a **new** route, not in v3 §8; log it in `contracts/CHANGELOG.md`) → `image/jpeg` from `photos.thumb_path` (WP-2.6, Stage 2); `404` if missing; `Cache-Control: max-age=3600`. Do not serve original frames.

**D. `GET /events/{id}/queue`**

Query parameters: `tier` (repeatable), `taluka`, `crop`, `cluster_bias` (bool), `grade`, `assessor_token`, `reviewed` (bool), `sort` (`priority` default | `gap` | `grade` | `village`), `limit` (default 50, max 200), `offset`.

Default sort ("priority"): tier rank (`PRIORITY_REVIEW`=1 … `INSUFFICIENT_EVIDENCE`=5), then `cluster_bias_flag` descending, then `|gap|` descending, then `grade_points` descending.

```json
{"total": 300, "facets": {"tier": {"PRIORITY_REVIEW": 38, "REVIEW": 51}, "taluka": {}, "crop": {}},
 "items": [{"case_id": "…", "survey_no": "PUN-HAV-0001", "village": "Synthetic-V03", "taluka": "Haveli",
            "crop": "soybean", "tier": "PRIORITY_REVIEW", "grade": "A", "grade_points": 10,
            "official_mid": 0.20, "ref_value": 0.77, "gap": 0.57,
            "pills": ["SAT_UNDER_RISK", "CLUSTER_BIAS"], "assessor_token": "ASR-14",
            "reviewed": false, "computed_at": "…Z"}]}
```

`pills` is derived from the 12-factor list and `boundary_crossing`: include `SAT_UNDER_RISK`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `CLUSTER_BIAS` (when `cluster_bias_flag`), `SOURCE_CONFLICT`, `PHOTO_INTEGRITY_ALERT`, `OVER_RISK` as applicable. Facet counts must reflect the **other** active filters (standard faceted search).

**E. `GET /events/{id}/fairness`**

Groupings: `taluka`, `crop` (NULL shown as `unknown`), `strip_width_band` (`<25 m`, `25–35 m`, `≥35 m` from `min_width_m`). For each group:

```json
{"group_by": "strip_width_band",
 "overall": {"n": 300, "flag_rate": 0.29, "grade_d_share": 0.06, "cluster_bias_cases": 20},
 "groups": [{"key": "<25 m", "n": 34, "flag_rate": 0.32, "grade_d_share": 0.12, "cluster_bias_cases": 3,
             "disparity_ratio": 1.10, "low_n": false}]}
```

`flag_rate` = share with tier ∈ {`PRIORITY_REVIEW`, `REVIEW`}; `disparity_ratio` = group rate / overall rate; `low_n = n < 10`. No statistical significance claims; this monitor lets reviewers see whether the **tool** treats groups differently (for example, whether narrow strip parcels end up in Grade D far more often).

**F. `POST /cases/{id}/review`**

Body: `{"officer_token": "OFF-014", "decision": "DISMISS_FLAG", "reason_code": "SATELLITE_EVIDENCE_REJECTED", "priority_override": true, "note": "…"}`.
Rules (D-18): `decision` and `reason_code` use the enums of Section 2.3; **`reason_code` is mandatory whenever the detection tier is `PRIORITY_REVIEW` or `REVIEW` and the decision is `DISMISS_FLAG`** (then `priority_override = true` is set server-side). In **one transaction**: insert into `reviews`; call `SELECT append_audit_event(:case, :officer, 'REVIEW_RECORDED', :payload)` (Stage 3's SQL helper, so there is no Python import across stages); set `cases.status = 'reviewed'`. Reviews never change `detections`.

**Acceptance criteria.** Pydantic response models exist for all endpoints; `test_api_contract.py` (WP-4.9) validates fixtures and live responses against them; queue ordering test with 6 hand-made rows; facet counts correct under combined filters; review without reason on a `PRIORITY_REVIEW` dismissal returns `422`; review writes exactly one `reviews` row and one `audit_log` row and `audit_verify()` still passes.

---

### WP-4.2 Frontend scaffold, typed client, fixtures mode, offline basemap (2 h)

**Files.** `frontend/` (Vite + React 18 + TypeScript + React Router + TanStack Query + Tailwind), `frontend/src/api/client.ts`, `frontend/src/api/fixtures.ts`, `scripts/make_basemap.py`, `frontend/public/basemap/`.

**Specification.**
1. Generate the TypeScript types from `contracts/openapi.json` with `openapi-typescript`; never hand-write response types.
2. `client.ts` wraps `fetch` and switches to fixtures when `VITE_USE_FIXTURES=1` (L4-2). `fixtures.ts` maps `fixtures/case_detail/<id>.json` (raw bundles from Stage 3) to the `GET /cases/{id}` shape; write one adapter and unit-test it against the worked example.
3. **Routes:** `/` (queue), `/cases/:id` (case page), `/fairness`, `/audit`.
4. **Basemap:** `make_basemap.py` renders the 3 Aug Sentinel-2 scene (B04, B03, B02) with a 2–98% percentile stretch into `s2_truecolor.png` plus `bounds.json` (EPSG:4326 corners). Leaflet `ImageOverlay` uses it (L4-4). Bundle fonts with `@fontsource` packages (Latin and Devanagari) so nothing is fetched at runtime.
5. Design tokens: tier colours must not rely on colour alone (each tier also has an icon and a text label); minimum contrast 4.5:1; font size ≥ 14 px.

**Acceptance criteria.** `npm run build` succeeds with the network disabled; the app opens at `/` in fixtures mode with no server; `grep -r "https://" frontend/dist` shows no runtime third-party URLs except documentation links in text.

---

### WP-4.3 `ReviewQueue.tsx` (3 h)

**Behaviour.**
* Table columns: tier pill (colour + icon + text), grade badge A–D, survey number and village, official mid vs reference value with the signed gap, pills (WP-4.1-D), assessor token, "reviewed" tick.
* Filters as chips: tier (multi), taluka, crop, cluster bias toggle, grade, reviewed state; filter state lives in the URL query string (shareable, back-button safe).
* **Cluster grouping toggle:** when on, cases that share a flagged `assessor_token` cluster collapse into one row ("ASR-14 · 20 parcels · median gap +0.46") that expands to its cases. Default off.
* Sorting per WP-4.1-D; keyboard: `j/k` to move, `Enter` to open a case, `/` to focus search.
* Counters at the top from `facets`; empty and error states with plain language; loading skeleton.
* Clicking a case opens `/cases/:id` and preserves the queue position when navigating back.

**Acceptance criteria.** With the full 300-case dataset: filtering by `PRIORITY_REVIEW + cluster bias` shows the Class 3 cohort; the URL reproduces the view when pasted into a new tab; all pills render for the worked example (`SAT_UNDER_RISK`, `CLUSTER_BIAS`); `vitest` + Testing Library cover filter-to-URL sync and the grouping toggle.

---

### WP-4.4 `EvidenceLadder.tsx` (4 h)

**Props.** `{ official, satellite, ground, pooled, peer, areaDmgFrac, boundary = 0.33, status, dataAvailability }`.

**Specification.** A hand-written responsive SVG forest plot (no charting library, so the layout is exact and works offline). X axis 0–100% damage. Rows, top to bottom, always in this order:

| Row | Mark | Source |
|---|---|---|
| Official record | interval `[lo, hi]` with a centre tick | `official` |
| Satellite mean loss | interval `[lo, hi]` + point at `value` | `satellite` |
| Satellite damaged-area fraction | single marker at `area_dmg_frac` | `satellite.quality` |
| Ground report | interval + tier badge (T1/T2/T3) | `ground` |
| Pooled / reference | interval; **label switches** to "Pooled" (status `OK`) or "Reference (satellite only)" (`SAT_ONLY`, `SOURCE_CONFLICT`) or "Reference (ground only)" | `detection` |
| Cross-assessor peer median | interval `[q25, q75]` with median tick | `peer` |

* A vertical dashed line at **33%** labelled "SDRF eligibility 33%". A shaded band for "below threshold" on the left.
* Each interval prints its numeric end points at the ends (e.g. `15 – 25%`).
* Missing rows are shown as a muted line "not available" with the reason from `dataAvailability.missing`; never omit a row silently.
* Excluded ground evidence is drawn hatched with the text "excluded: duplicate photo / screen / failed liveness".
* `SOURCE_CONFLICT`: show a small note "satellite and ground disagree; not pooled".
* Colour-blind safe: distinguish sources by marker shape and pattern as well as colour (official = square, satellite = circle, ground = triangle, pooled = diamond).
* Visually hidden `<table>` with the same values for screen readers and for the print stylesheet.
* Tooltip on hover/focus shows value, interval, σ and source.

**Acceptance criteria.** Rendering the worked-example fixture places the official bar (`15–25%`) left of the 33% line and the satellite bar (`67–89%`) clear to its right; switching `status` to `SOURCE_CONFLICT` changes the pooled label and shows the note; a case with no ground estimate shows "not available"; a snapshot test per variant (`vitest` + `@testing-library`), plus a check that bars never overflow the 0–100% axis.

---

### WP-4.5 `ParcelFrustumMap.tsx` (5 h)

**Props.** `{ geometry, pixelGrid, neighbors, photos, basemap }`.

**Specification.**
1. Leaflet map (no tile layer; offline). Layers, from bottom to top:
   1. Sentinel-2 true-colour `ImageOverlay` (L4-4);
   2. `neighbors` as thin grey outlines;
   3. **pixel heatmap**: one GeoJSON polygon per 10 m pixel in `pixelGrid`, fill by `attr_deficit` using a sequential colour scale (0 = pale, 1 = dark) with a separate neutral grey for negative values; opacity 0.7; legend with the scale and the text "flood-attributable deficit (pixel deficit − control median)";
   4. the parcel outline (2 px, high contrast);
   5. **camera frustums**: each photo's `frustum_geojson` filled **green** if `frustum_overlap ≥ 0.40`, otherwise **red**, 25% opacity, plus a camera marker at `(lat, lon)` with an arrow showing `azimuth_deg`;
   6. marker popup: thumbnail (`/photos/{id}/thumb`), `captured_at`, tier flags, overlap value, distance to parcel.
2. Layer toggles (heatmap, frustums, neighbours, basemap), scale bar, north arrow; `fitBounds` to the parcel with padding; `maxZoom` 21 so a 22 m wide strip fills the screen.
3. When `pixelGrid` has no features (e.g. `SMALL_PARCEL_LIMITATION` or no satellite), show the outline plus the message "No usable pixels for this parcel", never an empty map.
4. Performance: render up to ~600 pixel polygons smoothly (use `L.geoJSON` with `canvas` renderer).
5. Do not compute frustum geometry in the browser (L4-1); the only client geometry allowed is the arrow rotation.

**Acceptance criteria.** Worked-example fixture: heatmap visible inside the parcel, two green frustums pointing into it; the `NEIGHBOR_FRUSTUM` demo case shows a **red** frustum pointing at grey neighbouring outlines; a strip parcel is usable at max zoom; toggles work; with the network disabled everything still renders.

---

### WP-4.6 `FactorScreenCard.tsx`, grade breakdown, report and review panels, case page (3 h)

**`FactorScreenCard`.** Props: `factors` (12 items). Three groups with counts in the headers: **Triggered** (expanded), **Cannot assess** (expanded, with the reason in plain words), **Not triggered** (collapsed). Each factor shows a short title, "what it means" (one sentence), and an evidence table. Map codes to text in `frontend/src/content/factors.ts` (English; Marathi optional). Evidence tables format numbers per key (`z` two decimals, fractions as %, dates localised), never show raw JSON.

**`GradeBreakdown`.** Five horizontal bars (Coverage 0–3, Spatial 0–2, Agreement 0–2, Attribution 0–2, Margin 0–1) with the `rationale` string beneath each, the letter grade, and any `caps_applied` as chips ("capped at B: ground-driven crossing").

**`ReportPanel`.** Language toggle EN/मराठी calls `GET /cases/{id}/report?lang=`. Show the banner "Decision-support note. A human officer decides." Copy-to-clipboard and print-friendly CSS. If the API returns `409`, show "Not analysed yet".

**`ReviewPanel`.** Buttons for the four decisions; when the tier is `PRIORITY_REVIEW`/`REVIEW` and the officer chooses *Dismiss*, a reason dropdown appears and is required (mirrors WP-4.1-F). After submission the review appears in a timeline and a toast confirms that an audit entry was written.

**Case page layout (≥ 1024 px).** Left column: header (survey number, village, tier pill, grade), `EvidenceLadder`, `FactorScreenCard`. Right column: `ParcelFrustumMap`, `GradeBreakdown`, `ReportPanel`, `ReviewPanel`. On a phone: single column in the same order. A footer chip shows the live result of `GET /audit/verify` ("Audit chain verified ✓ · 312 entries").

**Acceptance criteria.** The twelve factors render for the worked example with the correct three groups; dismissing a `PRIORITY_REVIEW` case without a reason is blocked in the UI and by the API; layout holds from 360 px to 1440 px; keyboard-only navigation reaches every control.

---

### WP-4.7 `FairnessMonitor.tsx` (3 h)

**Behaviour.**
* Three small-multiple bar charts (by taluka, crop, strip-width band) from `/events/{id}/fairness`. Each bar shows flag rate and a thinner second bar for Grade-D share; the label shows `n`.
* A horizontal reference line at the overall flag rate; bars with `low_n` are hatched and carry the text "n < 10, interpret with care".
* Groups whose `disparity_ratio` is above 1.5 or below 0.67 (and `n ≥ 20`) get a visible marker and a sentence: "This group is flagged at X× the overall rate. This is a prompt to inspect the tool, not a finding about people."
* Panel "What this monitor cannot tell you": it does not measure correctness; synthetic data; small groups; discordance may be real.
* CSV export of the table.

**Acceptance criteria.** Strip-width band chart shows three bars with the correct `n`; `low_n` hatching appears for any group under 10; CSV opens in a spreadsheet with the same numbers as the chart.

---

### WP-4.8 Injection benchmark and v2-vs-v3 ablation (5 h)

**Files.** `tests/run_injection_benchmark.py`, `benchmark/results/` (`summary.json`, `confusion_v3.csv`, `confusion_v2.csv`, `ablation.csv`, `recall_at_5pct_fpr.csv`, `RESULTS.md`, optional PNGs).

Everything this script prints and writes must be tagged **🧪 synthetic officials and anomalies on real Sentinel imagery** (and, for Classes 4 and 5, simulated embeddings, L2-5).

**1. Inputs.** `benchmark/manifest.json` (true class of every case), the v3 event (`MH-2024-07-PUNE`) and the v2 event (`MH-2024-07-PUNE-V2`) with their `detections`.

**2. Success definitions (per class).**

| Class | Success ("detected") | Additional "neutralised" check |
|---|---|---|
| 0 clean | **false flag** if tier ∈ {`PRIORITY_REVIEW`, `REVIEW`} | — |
| 1 severe under-assessment | tier ∈ {`PRIORITY_REVIEW`, `REVIEW`} **and** `boundary_crossing = SAT_UNDER_RISK` | — |
| 2 moderate under-assessment | tier ∈ {`PRIORITY_REVIEW`, `REVIEW`} | — |
| 3 blanket village bias | `cluster_bias_flag` true **and** tier ∈ {`PRIORITY_REVIEW`, `REVIEW`} | — |
| 4 fraudulent ground claim | `PHOTO_INTEGRITY_ALERT` triggered | reference value within 0.15 of `V_sat` (the fraud did not move the reference) |
| 5 33% surfing | `GROUND_DRIVEN_BOUNDARY_CROSSING` triggered and tier ≥ `REVIEW` | — |

**3. Outputs.**
* **Confusion matrix:** rows = true class 0–5, columns = predicted tier (5 tiers), for v3 and v2; counts and row percentages.
* **Per-class recall** with **95% Wilson intervals** (n is only 15–20 per class, so intervals are wide; show them in every table and slide).
* **Recall at 5% false-flag rate.** Define the benchmarking score `s = max(|gap| / 0.25, |peer_z| / 2.0, 1·cluster_bias, 1·photo_alert, 1·[boundary ≠ NONE])`. Find the threshold τ so that the share of class-0 cases with `s ≥ τ` is 5%; report each class's recall at that τ. State plainly that this score exists only for the benchmark (L4-5).
* **Shipped operating point:** recall per class and the false-flag rate with the real tiers.
* **Ablation table v2 vs v3** on identical cases: per class recall and false-flag rate; strip parcels (80) vs regular (220) separately; Grade-D share; count of `CANNOT_ASSESS` factors. The story to verify (not to assume): v3 recovers Class 3, narrow strips, Class 4 and Class 5. If any of these does **not** improve, report it and open an `upstream-bug`.
* **Subgroup fairness check:** false-flag rate for strip vs non-strip clean parcels.
* `RESULTS.md` starts with a "What this does and does not show" box: synthetic anomalies, one random realisation (seed 42), small n, simulated embeddings for Classes 4–5, single event, real imagery limits (clear fraction).

**4. Quality rules.**
* Deterministic: running twice yields identical files (fixed seeds, sorted keys).
* Reads only from the database and `manifest.json`; it does not call the analysis code.
* Exits non-zero if the manifest and database disagree (e.g. a case missing from `detections`).
* Never prints a headline number without its interval and tag.

**Acceptance criteria.** `make benchmark` writes all outputs in under 2 minutes; the confusion matrix sums to 300 per model; a unit test with a hand-made 20-case manifest reproduces hand-computed recall, Wilson interval and τ.

---

### WP-4.9 API contract tests, `make smoke`, offline check (1 h)

1. `tests/test_api_contract.py`: for each endpoint, validate the live response and the fixture against the Pydantic/OpenAPI schema; the factor list always has 12 entries in enum order; `GET /cases/{id}` for an unanalysed case returns `409`.
2. `make smoke` (`scripts/smoke.py`): `make up` → `make restore S=3` → start API → `GET /health` → `GET /events/…/queue?limit=5` → `GET /cases/{worked-example}` → `GET /cases/{id}/report?lang=mr` → `GET /audit/verify` → `POST /cases/{id}/review` on a scratch case → print a green summary. Exit code non-zero on any failure.
3. **Offline check:** disable the network (or the Wi-Fi) and run `make smoke` plus the front-end build served statically; nothing may need the internet.

**Acceptance criteria.** `make smoke` finishes in under 90 seconds on the demo laptop and is green with Wi-Fi off.

---

### WP-4.10 Pitch deck, demo script, Q&A sheet, rehearsal, backup video (3 h)

**Files.** `docs/pitch.pptx` (or markdown slides), `docs/demo_script.md`, `docs/qa_sheet.md`, `docs/backup_video.mp4` (not committed if large; recorded locally).

**A. Seven slides.**
1. **The problem:** under-assessment around the 33% eligibility line, narrow riverside plots, village-wide flat panchnamas, photo fraud. Only ✅ facts; no invented statistics.
2. **Why earlier approaches fail:** the corrections that v1→v3 made (one line each: clipped DiD bias, strip parcels turning empty, GPS buffer too loose, pooled-score surfing).
3. **The method in one picture:** official record + satellite + verified ground → reconcile → tier + grade → human decides.
4. **Live demo** (slide is just the title; you are in the app).
5. **Measured results:** the benchmark table from `RESULTS.md` with 🧪 tags, Wilson intervals and the "what this does not show" line.
6. **Safeguards and limits:** audit chain, fairness monitor, no Aadhaar, human in the loop; what is simulated; what is not implemented.
7. **Pilot plan and ask:** the four-week plan (Section 10 of this document) and what data access is needed.

Rules: every number on a slide has a source and a tag (✅ / 🔎 / 🧪 / 🎯); screenshots come from the real app; no slide claims accuracy on real officers.

**B. Five-minute demo script (`demo_script.md`)** — rehearse with a stopwatch:

| Time | Screen | What you say and do |
|---|---|---|
| 0:00–0:30 | Queue | "300 cases, ordered by tier." Filter to `PRIORITY_REVIEW`. Point at the pills. |
| 0:30–1:30 | Worked-example case | Evidence ladder: official 15–25% vs satellite 67–89% either side of the 33% line. Map heatmap; two green frustums. Factor card: peer discordance z = −3.0, cluster bias. Grade A, 10/10 and why. |
| 1:30–2:00 | Report panel | Toggle Marathi; "numbers are checked by a verifier; the report cannot reverse them." |
| 2:00–2:45 | Class 3 cluster | Toggle cluster grouping: 20 parcels, one assessor, flat 20%. |
| 2:45–3:45 | Live phone | Submit the `valid` bundle from the PWA (offline queue then upload); show Tier 1. Then submit `neighbor_farm`; show the **red** frustum. (If the phone fails, play the pre-recorded burst, see backup.) |
| 3:45–4:15 | Audit | `GET /audit/verify` green; in a terminal try an `UPDATE` on `audit_log` and show the exception. |
| 4:15–4:40 | Fairness | Strip-width chart; say what it cannot tell. |
| 4:40–5:00 | Limits and ask | Synthetic officials, small n, simulated embeddings; the pilot ask. |

**C. Q&A sheet.** One page of likely questions with the owner who answers: why 33%? (the SDRF eligibility line cited in the spec ✅); why not a trained model? (no labelled ground truth; evidence-based interval comparison instead); what if clouds? (windows, SAR, Grade D); small plots? (sub-pixel weights, grade caps); photo fraud? (six layers; what remains open: attestation); privacy? (no Aadhaar, pseudonymous tokens, EXIF stripped); who decides? (human); what is synthetic? (parcels, officials, benchmark embeddings); what happens to false flags? (fairness monitor, reason codes); scalability? (idempotent batch, per-case transactions). Owner mapping: satellite → P1, photos → P2, detectors/audit/reports → P3, UI/architecture/benchmark → P4.

**D. Rehearsal and backup.** Three full runs: (1) normal, (2) Wi-Fi off, (3) phone fails (play the recorded burst bundle via `make demo-bundles`). Record a 3-minute backup video of run 2. Prepare the demo laptop: pre-started containers, `make restore S=3`, browser zoom, notifications off, charger, spare USB with the `stage3.dump` and the built front end.

**Acceptance criteria.** The script fits in 5:00 ± 15 s on two consecutive rehearsals; the backup video exists and plays offline; every number in the deck appears in `RESULTS.md` or a stage README.

### 6.X Exit Gate 4 checklist (Person 4 signs; project done)

- [ ] `make smoke` green with the network off
- [ ] All five dashboard components, case page and fairness page work in fixtures mode and live mode
- [ ] `benchmark/results/RESULTS.md` generated with tags, intervals and limits; deck numbers traced to it
- [ ] `test_api_contract.py` and all earlier test modules green (`make test`)
- [ ] Demo rehearsed three ways; backup video recorded
- [ ] `handoffs/stage4/README.md` lists known limitations and the not-implemented list (OTP, attestation, pre-flood landmark matching, voice transcription, real authentication, Bhunaksha polygons)

---

# 7. Waiting-time work and upstream support

In a relay, three people are always waiting. This is how they stay useful **without** breaking the rule that a stage starts after the previous handoff. Everything below depends only on the source documents and the frozen contracts, never on another stage's unfinished output.

| Person | While waiting (stages) | Useful work that does not need upstream output | Upstream-support duty |
|---|---|---|---|
| **P1** | Stages 2–4 | Hour-for-hour: answer `upstream-bug` issues first. Then: write the Stage 1 "method note" (one page on unclipped DiD, sub-pixel weights, silt-vs-rot, with the measured numbers); sensitivity check of `silt_*` and `rot_*` thresholds; static fallback GeoJSON export of key parcels (for an offline UI fallback); research Bhunaksha polygon access for the pilot; help P4 with `make_basemap.py` | On call for the satellite pipeline and seed data until Exit Gate 4. Re-issue `stage1.vN.dump` on any fix, with a CHANGELOG entry |
| **P2** | Stage 1 (before start) and Stages 3–4 | **Before starting:** gather and license-check the photo library; build the PWA scaffold, camera and orientation hooks, i18n files and offline queue against a local stub endpoint (they need no database); field-test compass offsets on 2–3 phones; draft `ATTRIBUTION.md`. **After handing over:** review P3's reports in Marathi; refine Marathi strings; write the "photo fraud" part of the Q&A sheet | On call for the photo verifier and PWA until Exit Gate 4 |
| **P3** | Stages 1–2 | Write all pure-function detector and tier code against hand-made inputs (no database); write the test tables of Sections 5 WP-3.1, 3.3 to 3.7 as `pytest` files that initially fail; draft report templates; run WP-3.0 smoke test on Stage 1 output | On call for engine, audit and reports until Exit Gate 4 |
| **P4** | Stages 1–3 | Build the front end entirely from `fixtures/` (hand-write the worked example JSON from v3 §10 if Stage 3 fixtures do not exist yet); components in Storybook or isolated pages; draft the slide deck skeleton; build `run_injection_benchmark.py` against a hand-made manifest and unit-test the metrics (Wilson interval, τ) | Reviews each handoff README as the "first consumer" of the contracts and reports gaps |

**Rules for waiting-time work.**
* It must be mergeable behind a feature flag or in a folder that nobody else touches.
* If the real upstream output later contradicts what you assumed, **the upstream output wins**; adapt your code, and if the contract was wrong, file a CHANGELOG entry.
* Waiting-time work is *not* a way to start your stage early. The Exit Gate checklist of the previous stage still decides when you begin integration.

---

# 8. Risk register

| # | Risk | Stage | Likelihood / impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | **Monsoon cloud:** July–August Sentinel-2 scenes may have little clear sky, so the two windows may not exist for many parcels | 1 | High / High | Report real clear fractions (D-22); flag `LOW_CLEAR_FRACTION`; SAR still gives inundation evidence; Grade caps; pick alternative scene dates early and record them | P1 |
| R2 | Real imagery cannot supply enough parcels at the needed `V_sat` for planted classes 4 and 5 | 1 | Medium / High | Generate extra candidates near the flood margin and in dry areas (WP-1.10 step 3); never alter planted values | P1 |
| R3 | A defect found late in Stage 1 output forces re-runs of Stages 2–3 | 1→3 | Medium / High | WP-3.0 early smoke test; per-stage exit tests; snapshot versioning (`stage1.v2.dump`); idempotent writers make re-runs cheap | P1, P3 |
| R4 | Strip parcels (22 m wide, ~2 pixels) are unreliable even with sub-pixel weights | 1, 3 | High / Medium | `n_eff` thresholds, `SMALL_PARCEL_LIMITATION`, Grade cap C, fairness monitor by strip-width band | P1, P3 |
| R5 | Compass and orientation readings differ across Android models and iOS | 2 | High / Medium | Field-test table (WP-2.7), `COMPASS_MISSING` → Tier 2 (not rejection), tolerance in cone half-angle | P2 |
| R6 | CLIP-style similarity threshold 0.92 misses cropped duplicates or flags distinct fields | 2 | Medium / Medium | Multi-view query (WP-2.4); measure and report on demo bundles; benchmark uses simulated embeddings, which the README states | P2 |
| R7 | Marathi text quality and terminology | 2, 3 | Medium / Medium | Native-speaker review before demo; Marathi sentences are templates, not free generation | P2, P3 |
| R8 | Benchmark looks better than reality because officials and anomalies are synthetic | 4 | High / High (credibility) | Tag 🧪 everywhere; Wilson intervals; "what this does not show" box; no claim about real officers; pilot plan validates on a blind gold set | P4 |
| R9 | Small n per class (15–20) makes recall figures unstable | 4 | Certain / Medium | Report intervals; do not tune thresholds on the same cases used for the headline numbers; say so | P4 |
| R10 | Audit hash differs across timezones or concurrent inserts | 3 | Medium / High | UTC canonical timestamp, advisory lock, timezone test, in-database verifier (WP-3.8) | P3 |
| R11 | Relay slip: each delay pushes every later stage | all | High / High | Buffer day per stage (Section 9); waiting-time work (Section 7); scope cuts list below; weekly status in the CHANGELOG | all |
| R12 | Demo fails on stage (network, phone, GPU/CPU speed) | 4 | Medium / High | Offline-first build, three rehearsals, pre-recorded bundles, backup video | P4 |
| R13 | Privacy: EXIF GPS in thumbnails, farmer identifiers in logs | 2, 4 | Medium / High | Strip EXIF (WP-2.6), mask `farmer_ref`, no Aadhaar, pseudonymous officer tokens | P2, P4 |
| R14 | v3 refers to v2 sections 11–15 and appendices (validation, privacy, build plan) that were not provided | all | Certain / Low | Minimal privacy and validation rules are stated here (Sections 2.8, 6.1, 10); obtain the v2 text before pilot | P4 |
| R15 | Single point of failure: one person owns a whole stage | all | Medium / High | Buddy pairs review each other's handoffs; READMEs written for a stranger; no hidden local state | all |

**Scope-cut order if time runs short** (cut from the top; never cut an acceptance test, only features):
1. Optional LLM polish (WP-3.9-D), sun-elevation check (WP-2.3-5), voice-note recording (WP-2.8).
2. Cluster-grouping toggle (WP-4.3), CSV export (WP-4.7), PNG charts of the benchmark.
3. V2 clone and ablation table (WP-1.9-5, WP-3.10 v2 mode, WP-4.8 ablation) — keep the v3 benchmark and say the ablation is future work.
4. Spectral-cluster fallback for crop-NULL parcels (keep exact crop matching only; report the effect).
5. Marathi version of the factor texts in the UI (reports stay bilingual).

**Never cut:** unclipped DiD, sub-pixel weights for strips, surfing guard, cross-assessor peers, hash-chained audit, numeric verifier, the 🧪 tagging, the fairness monitor.

---

# 9. Day-by-day schedule (≈ 7 productive hours per day)

| Working days | Stage | Person | Content | Gate at end of the stage |
|---|---|---|---|---|
| 1 | 1 | P1 | WP-1.1, 1.2, 1.3 (platform up) | Contract freeze already done on day 0; `make up && make schema` works; **P3 starts WP-3.0 prerequisites** |
| 2–3 | 1 | P1 | WP-1.4, 1.5, 1.6 (rasters, hazard, parcel prep) | `check-rasters` green |
| 4 | 1 | P1 | WP-1.7 (optical) | `test_unclipped_did` green |
| 5 | 1 | P1 | WP-1.8, 1.9, 1.10, 1.11 (SAR, batch, seed, snapshot) | **Exit Gate 1**; handoff walk-through to P2 |
| 6 | 2 | P2 | Intake, WP-2.1, 2.2 | frustum tests green |
| 6–7 | 2 | P2 | WP-2.3, 2.4, 2.5 (liveness, dedup, crop) | calibration numbers recorded |
| 8 | 2 | P2 | WP-2.6 (tiering, endpoints) | truth table reproduced via HTTP |
| 9 | 2 | P2 | WP-2.7, 2.8, 2.9 (PWA, mostly pre-built while waiting) | phone submits once, exactly once |
| 10 | 2 | P2 | WP-2.10, 2.11 | **Exit Gate 2**; walk-through to P3 |
| 11–12 | 3 | P3 | WP-3.1 to 3.5 (reconcile, detectors) | detector tests green |
| 13 | 3 | P3 | WP-3.6, 3.7 (factors, grade) | factor/grade tests green |
| 14 | 3 | P3 | WP-3.8, 3.9 (audit, reports) | audit and verifier tests green |
| 15 | 3 | P3 | WP-3.10, 3.11 | **Exit Gate 3**; walk-through to P4 |
| 16 | 4 | P4 | WP-4.1, 4.2 | contract tests green |
| 17 | 4 | P4 | WP-4.3, 4.4, 4.5 | queue, ladder, map render from live API |
| 18 | 4 | P4 | WP-4.6, 4.7 | case page and fairness complete |
| 19 | 4 | P4 | WP-4.8, 4.9 | benchmark results written; smoke green offline |
| 20 | 4 | P4 | WP-4.10 (+ buffer) | **Exit Gate 4**; code freeze; rehearsals |

Each stage includes roughly 10–15% slack inside its days for fixes requested through `upstream-bug` issues. If a stage ends early, the owner uses the surplus for upstream support, not for adding features.

---

# 10. After the project: four-week pilot roadmap (who leads)

From the detailed plan §4.2, mapped to owners.

| Week | Focus (from the source plan) | Lead | Support |
|---|---|---|---|
| 1 | Integrate official **Bhunaksha** village Gat polygons for 2 flood-prone talukas (Pune / Sangli); ingest historical Sentinel-2 (2019–2024) baselines per spectral cluster | P1 | P4 (loaders and tests) |
| 2 | **Blind gold set:** 3 agriculture/revenue officers review 80 stratified historical flood cases (including ribbon plots and delayed black-soil rot); measure Fleiss' κ; calibrate Grade A–D thresholds | P3 | P4 (review tool), P1 (case selection) |
| 3 | **Security & e-Peek Pahani sandbox:** WebAuthn / Android Play Integrity attestation on the PWA uploader; test pre-flood sowing photos for background/horizon matching | P2 | P3 (audit fields) |
| 4 | **Shadow audit pilot:** run in shadow mode beside live post-monsoon panchnamas; measure officer review time per flagged case and district-level fairness | P4 | all |

Pilot principles: shadow mode only (no effect on payments); every officer decision requires a reason code; metrics are reported with intervals and with the synthetic-versus-real distinction; thresholds tagged 🎯 are only changed through the gold-set calibration, never to improve a headline number.

---

# 11. Traceability: where each part of the source specs is built

| Source (v3 spec unless stated) | Built in |
|---|---|
| §0–1 Status legend, summary | Section 0 of this document (tagging rule), WP-4.10 |
| §2–3 Decision records D1–D16 | D1 → WP-3.1/3.3; D2/D15 → WP-3.2, 3.5, 1.6; D3 → WP-1.6, 1.7; D4 → WP-1.8; D5 → WP-3.1, 3.7; D9 → WP-2.1 to 2.9; D10/D16 → WP-3.9 |
| §4 Architecture, §4.1 pipeline | Whole relay (Section 1.2) |
| §5 Data sources | WP-1.4, 1.5 |
| §6 Database (+ frustum helper) | WP-1.1 (DDL), WP-2.1 (frustum SQL), WP-3.8 (audit SQL) |
| §7.1 Parcel prep, peers, controls | WP-1.6 (parcels, controls), WP-3.2 (peers) |
| §7.2 Satellite observation, SAR gate | WP-1.7, 1.8 |
| §7.3 Hazard context | WP-1.5 |
| §7.4 Ground evidence and photo verification | WP-2.2 to 2.6 |
| §7.5 *(missing from the v3 file)* | not available; nothing built from it |
| §7.6 Pooling and surfing guard | WP-3.1 |
| §7.7 Detectors and tiers | WP-3.2 to 3.5, 3.3 (tiers) |
| §7.8 Factor screen | WP-3.6 |
| §7.9 *(cited but missing)* Grade rubric | defined in WP-3.7 (D-14) |
| §7.10 Report and verifier | WP-3.9 |
| §8 API | WP-1.3 (stubs), WP-2.6 (`/ground`), WP-3.10 (`/analyze`, `/report`, `/audit/verify`), WP-4.1 (the rest) |
| §9 Dashboard | WP-4.3 to 4.7 |
| §10 Worked example | tests in WP-3.1/3.3/3.6/3.7/3.9; demo (WP-4.10); `fixtures/detections/worked_example.json` |
| §11 and appendix config | Section 2.6, WP-1.2 |
| Detailed plan §1 file layout | Section 2.1 |
| Detailed plan §2.1 (Track A) | Stage 1 |
| Detailed plan §2.2 (photo verifier) | Stage 2 |
| Detailed plan §2.3 (engine) | Stage 3 |
| Detailed plan §2.4 (dashboard, PWA) | WP-4.3 to 4.7 (dashboard); WP-2.7 to 2.9 (PWA) |
| Detailed plan §3.1 (six test modules) | P1: unclipped DiD, strip weights; P2: anti-spoofing; P3: pooling/detectors, verifier, audit chain |
| Detailed plan §3.2 (benchmark) | data and manifest: WP-1.10; runner and tables: WP-4.8 |
| Detailed plan §4.1 (24-hour matrix) | replaced by the relay (Section 9) |
| Detailed plan §4.2 (pilot) | Section 10 |

---

# 12. Master checklist and glossary

### 12.1 End-to-end completion checklist

- [ ] Contracts frozen and committed (`contracts/`), decisions D-1 … D-22 acknowledged by all four
- [ ] Exit Gate 1 signed by P1 and accepted by P2
- [ ] Exit Gate 2 signed by P2 and accepted by P3
- [ ] Exit Gate 3 signed by P3 and accepted by P4
- [ ] Exit Gate 4 signed by P4
- [ ] Six required test modules from the detailed plan are green, plus the extra tests listed in each stage
- [ ] `make smoke` green with the network off
- [ ] `benchmark/results/RESULTS.md` published with tags, intervals and limits
- [ ] No number in any README, slide or report lacks its ✅ / 🔎 / 🧪 / 🎯 tag
- [ ] Not-implemented list is in the final README (OTP, attestation, pre-flood landmark matching, voice transcription, real authentication, Bhunaksha polygons, sun-elevation check unless done)

### 12.2 Glossary

| Term | Meaning |
|---|---|
| **33% line / SDRF eligibility** | The damage threshold the project treats as the eligibility boundary for compensation, per the v3 spec |
| **DiD (unclipped)** | Difference-in-differences: the farm's vegetation deficit minus the median deficit of nearby unflooded control parcels, without clipping per-pixel values at zero |
| **`loss_attr`** | Attributable mean loss = farm deficit − control deficit |
| **`area_dmg_frac`** | Share of the weighted parcel area whose pixel deficit exceeds the damaged-area threshold (0.35) |
| **`V_sat`, `V_ground`** | Satellite and ground damage estimates (0–1) |
| **`n_eff`** | Effective number of 10 m pixels, the sum of the sub-pixel weights; the spatial reliability measure |
| **HAND** | Height Above Nearest Drainage in metres; low values mean close to the river level |
| **Frustum** | The triangular viewing cone (25° half-angle, 60 m) of a photo, intersected with the parcel to check that the camera pointed at the right field |
| **Tier (photo)** | 1 = verified (σ 0.14), 2 = partially verified (σ 0.22), 3 = unverified (σ 0.35) |
| **Tier (case)** | `PRIORITY_REVIEW`, `REVIEW`, `NOTE`, `CONSISTENT`, `INSUFFICIENT_EVIDENCE` |
| **Grade** | A–D evidence strength, separate from the tier |
| **Surfing** | Using a ground claim to push a pooled estimate across the 33% line while the satellite stays below it |
| **Cluster bias** | A group of parcels under one assessor with near-identical official values and much higher satellite evidence |
| **Handoff** | A database snapshot plus README that lets the next person start with no conversation |
| **Exit gate** | The checklist that must be true before a stage's output is handed over |
| **🧪 / ✅ / 🔎 / 🎯 / 🗺️** | Synthetic / verified / unverified / initial setting to tune / roadmap |

---

*End of document.*
