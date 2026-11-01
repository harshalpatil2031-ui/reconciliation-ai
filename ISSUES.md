# Reconciliation AI — Consolidated Issue Backlog (v3 + AI Version)

**Prepared:** 1 November 2026  
**Sources reviewed:** `reconciliation_ai_implementation_v3.md`, `Reconciliation_AI_Implementation.md`, and `reconciliation_ai_work_split.md`  
**Ownership:** Four existing roles (P1–P4) from the work-split document. Names were not present, so roles are preserved rather than guessed.  
**Purpose:** Convert the design decisions and version differences into actionable, reviewable issues. This is a backlog proposal; no issue tracker was connected, so no external issues were filed.

## 1. Executive summary

The project has three distinct documents: an older AI-heavy prototype specification, the revised v3 technical specification, and the detailed four-person relay plan. The relay plan is the implementation source of truth because it maps v3 decisions to concrete work packages and acceptance checks. The older AI document should be treated as historical context where it conflicts with v3.

The biggest shift is architectural: v3 replaces unvalidated predictive claims and blended scoring with an evidence-led, human-reviewed system. It keeps observed damage separate from hazard context; uses satellite and verified ground evidence; emits flags, evidence grades, and traceable factors; and does not autonomously decide compensation.

## 2. Version comparison and disposition

| Topic | Older AI implementation | v3 direction | Backlog disposition |
|---|---|---|---|
| Damage / hazard scoring | Weighted aggregation mixes rainfall, infrastructure risk, ground NLP, satellite scores | Separate observed damage from hazard plausibility; hazard explains context, not damage | Implement v3 separation; do not carry old weighted score forward |
| Satellite model | Siamese CNN and model-performance claims | Control-differenced optical loss, sub-pixel geometry, dual loss metrics, multi-index time windows, gated SAR | Use transparent v3 pipeline; validate every threshold and label synthetic results |
| Root cause | Random Forest + SHAP on proposed labels | Deterministic contributing-factor screen with evidence trace | Use factor codes/rules; remove unsupported ML cause probabilities |
| Confidence | Numeric confidence formula and bands | Evidence Strength Grade A–D plus spatial block-bootstrap intervals | Implement grade rubric and report intervals; avoid probability-like confidence |
| Ground language | IndicBERT fine-tuning and free-text severity extraction | Structured form first; language model only consistency check; MahaBERT benchmark | Keep structured Marathi form; defer model training pending labeled corpus |
| Photos | ResNet-50 / broad GPS validation | Frustum, pitch/horizon, burst liveness, embedding dedup, crop consistency | Implement v3 photo checks; no single image classifier as proof |
| Identity/privacy | Aadhaar hashing is described in older version | No Aadhaar; case/Gat/Agri Stack references and pseudonymous tokens | Enforce no Aadhaar collection and scrub identifiers |
| Payout decision | Prototype score and mismatch tiers risk implying decisions | Human review only; system is QA/triage | Preserve human decision and reasoned review trail |
| Data / claims | Older source contains accuracy claims and proposed external feeds | v3 status tags distinguish verified, unverified, synthetic, target, roadmap | Audit claims and label all demo/benchmark numbers |
| Implementation plan | Older document describes model modules; work split maps v3 into staged WPs | Four-person relay with gates, interfaces and test criteria | Treat work-split WPs and global contracts as executable issue plan |

### Key version conflicts to resolve explicitly

1. **Do not mix hazard context into observed damage.** Rainfall, dam release, HAND and TWI are explanatory plausibility signals, not extra terms in the damage score.
2. **Do not revive the Siamese CNN, Random Forest/SHAP, IndicBERT severity model, or weighted evidence formula** unless a separately approved, labeled-data evaluation justifies a future change.
3. **Do not report older model metrics as current performance.** The v3 rule is measured numbers only, with synthetic versus real origin stated.
4. **Keep system output advisory.** The officer remains the decision maker; the tool must not approve or reject compensation.
5. **Check document references before pilot.** The v3 file references v2 sections and appendices not present in the folder; the relay risk register calls this out.
6. **Reconcile detailed-plan ambiguities only through the relay’s global decision register (D-1 onward)** and record any new choice in the contract change log.

## 3. Issue conventions and ownership

- **Priority:** P0 blocks safe/core implementation; P1 required for the prototype exit gates; P2 important quality or pilot readiness; P3 future/pilot.
- **Labels:** `v3`, `version-reconciliation`, plus area labels such as `satellite`, `ground-evidence`, `decision-engine`, `frontend`, `privacy`, `benchmark`, `docs`, `integration`.
- **Dependencies:** Stage gates are real dependencies. Work in parallel only where the relay’s waiting-time section allows fixture/stub work.
- **Dependency enforcement:** Before starting or merging an issue, the assignee or AI agent must inspect its blocker issues in the tracker. If any blocker is not **Done/Closed**, report the blocking IDs, statuses, owners, and missing handoff/artifact; do not start dependent integration work. Only explicitly separable fixture/stub tasks allowed by the relay may continue, and the issue cannot be marked complete until blockers clear.
- **Definition of done:** acceptance checks below are evidenced in the relevant handoff README and tests/demo artifacts specified by the work split.
- **People:** P1–P4 match the four-person file. Replace labels with actual names when available; assignments are otherwise ready to use.

## 4. Proposed issues by owner

## Person 1 (P1) — Data Foundation & Satellite Evidence

### P1-01 — Establish the v3 data foundation and frozen contracts
**Priority:** P0 · **Labels:** `v3`, `data-foundation`, `integration`  
**Scope:** Implement environment, Docker/PostGIS schema, configuration, API shell/router stubs, shared enums and JSON contracts from relay Sections 2 and 3.  
**Acceptance criteria:**
- Schema and configuration load from a clean local setup.
- Required enums and cross-stage payloads match the relay contracts.
- API stubs return documented shapes.
- Any clarification is recorded in the contract change log before downstream consumers depend on it.
**Blocked by:** X-01, X-02. **Blocks:** P1-02, P1-03, P1-04, P1-05, P2-01, P2-04, P3-01, P4-01.

### P1-02 — Build reproducible raster and hazard inputs
**Priority:** P1 · **Labels:** `v3`, `satellite`, `hazard`  
**Scope:** Prepare/validate raster inputs and ingest rainfall, river/dam/discharge, HAND and TWI context per v3 and WP-1.4/1.5. Keep hazard fields separate from damage observations.  
**Acceptance criteria:**
- Inputs have recorded source, date range, CRS, resolution, nodata handling and licensing/provenance.
- Raster checks pass and missing/low-quality layers produce explicit quality flags.
- Hazard plausibility is stored separately and never added to the damage estimate.
- Unverified sources/settings are tagged 🔎 or 🎯; simulated inputs are 🧪.
- **Blocked by:** P1-01.

### P1-03 — Implement parcel geometry, controls and peer-ready features
**Priority:** P1 · **Labels:** `v3`, `satellite`, `geospatial`  
**Scope:** Prepare parcels, adaptive buffer/sub-pixel overlap weights, effective pixel count, controls and parcel geometry quality fields.  
**Acceptance criteria:**
- Narrow strip parcels are retained; no fixed negative buffer can erase them.
- Area weights and (n_{eff}) are persisted and exposed to downstream analysis.
- Small/low-support parcels receive explicit quality limitations rather than fabricated precision.
- Peer/control candidates retain crop/phenology and assessor/village/date fields required by P3.
- **Blocked by:** P1-01, P1-02.

### P1-04 — Implement v3 optical satellite damage metrics
**Priority:** P1 · **Labels:** `v3`, `satellite`, `validation`  
**Scope:** Implement unclipped Difference-in-Differences, final-step clipping, mean loss and damaged-area fraction, and two-window NDVI/NDRE/NDMI trajectory flags.  
**Acceptance criteria:**
- Tests prove control deficits are not clipped before differencing.
- Both (L_{attr}) and (A_{dmg}) are reported; (V_{sat} = max(L_{attr}, A_{dmg})) follows the relay contract.
- Water-submerged pixels are not treated as final vegetation loss before recession.
- Silt recovery and delayed waterlogging signals are separately represented when scenes exist.
- Missing scenes / clouds produce quality flags and grade-limiting inputs.
- **Blocked by:** P1-01, P1-02, P1-03.

### P1-05 — Implement gated SAR inundation evidence
**Priority:** P1 · **Labels:** `v3`, `satellite`, `validation`  
**Scope:** Add speckle filtering, Ashman bimodality gate, physical open-water bounds, and HAND/control-gated double-bounce detection.  
**Acceptance criteria:**
- Unimodal scenes do not trigger Otsu-only classification.
- Positive backscatter is not treated as flood without low HAND, pre-event vegetation, and control-relative rise conditions.
- SAR outputs and quality flags are traceable per parcel.
- 🎯 thresholds remain marked as initial until measured/calibrated.
- **Blocked by:** P1-01, P1-02, P1-03.

### P1-06 — Seed the benchmark world and hand off Stage 1
**Priority:** P1 · **Labels:** `v3`, `benchmark`, `handoff`  
**Scope:** Create the planned parcel fixtures, simulated official records and planted anomaly classes; provide batch runner, tests, versioned database snapshot and handoff.  
**Acceptance criteria:**
- Manifest documents every synthetic field and planted case class.
- Required classes and counts follow the relay contract; no planted value is silently altered.
- Batch run is repeatable/idempotent and snapshot can be restored.
- Exit Gate 1 checklist is complete and P2 can start from the handoff README alone.
**Blocked by:** P1-01, P1-02, P1-03, P1-04, P1-05. **Blocks:** P2-01, P2-05, P3-01, P3-02, P4-03.

## Person 2 (P2) — Ground Evidence: Photo Verifier & Farmer PWA

### P2-01 — Implement parcel-aware photo intake and frustum checks
**Priority:** P1 · **Labels:** `v3`, `ground-evidence`, `geospatial`  
**Scope:** Add photo schema and spatial helpers, camera location/direction inputs, frustum intersection, pitch/horizon and parcel-boundary checks per WP-2.1/2.2.  
**Acceptance criteria:**
- Inside-parcel, neighbor-farm, puddle/low-pitch and outside-boundary fixtures reproduce the documented tiers/flags.
- Missing compass is downgraded per the relay decision; it is not treated as proof of fraud.
- Original image EXIF is stripped from stored/served derivatives and farmer references are masked in logs.
- Spatial thresholds are configurable and documented.
- **Blocked by:** P1-01, P1-06.

### P2-02 — Add burst liveness and screen-spoof detection
**Priority:** P1 · **Labels:** `v3`, `ground-evidence`, `anti-spoofing`  
**Scope:** Capture multi-frame bursts and implement parallax/Moiré checks with explicit quality outcomes.  
**Acceptance criteria:**
- Genuine-burst and screen-spoof test bundles exercise the checks.
- Failed liveness is excluded from pooling where the relay contract requires; low quality alone maps to the specified tier.
- Calibration evidence/distributions are recorded and no synthetic benchmark is represented as real field validation.
- **Blocked by:** P2-01; P1-06 for parcel-linked integration.

### P2-03 — Add embedding deduplication and crop consistency
**Priority:** P1 · **Labels:** `v3`, `ground-evidence`, `ml-evaluation`  
**Scope:** Implement pgvector-backed photo deduplication and declared-crop consistency check with a measured fixture set.  
**Acceptance criteria:**
- Cropped/rotated/brightness-shifted duplicate case is caught per configured threshold.
- Distinct-field false-positive checks are reported alongside duplicate recall.
- Crop classifier output is a consistency flag, not a final damage decision.
- Model, weights, license and threshold provenance are captured.
- **Blocked by:** P2-01; P1-06 for parcel-linked integration.

### P2-04 — Build Marathi structured intake and offline PWA
**Priority:** P1 · **Labels:** `v3`, `farmer-pwa`, `accessibility`  
**Scope:** Build camera/orientation guide, structured Marathi form, offline queue, upload idempotency and consent/help copy per WP-2.7–2.9.  
**Acceptance criteria:**
- User can capture bundle, complete structured fields and queue/upload while offline/online.
- Retry cannot create duplicate submissions.
- Form fields feed documented contract shape; free text is supplemental consistency evidence.
- Marathi strings are reviewed and accessibility/camera permission failures are handled.
- **Blocked by:** P1-01; shell/form work can proceed against a stub before Stage 1 handoff.

### P2-05 — Package photo fixtures, licenses and Stage 2 handoff
**Priority:** P1 · **Labels:** `v3`, `ground-evidence`, `handoff`, `privacy`  
**Scope:** Gather/license-check example photos, create the six demo bundles, implement ground tier/estimate API and hand off Stage 2.  
**Acceptance criteria:**
- Fixture manifest states source/license and synthetic/real status for every bundle.
- All six expected scenarios match the relay truth table, including duplicate, screen spoof and missing compass.
- Tier 3 pooling/exclusion semantics follow frozen D-2; no ambiguity leaks to P3.
- Exit Gate 2 is complete and snapshot restores cleanly.
**Blocked by:** P1-06, P2-01, P2-02, P2-03, P2-04. **Blocks:** P3-01, P3-03, P3-05, P3-06.

## Person 3 (P3) — Decision Engine, Audit & Reports

### P3-01 — Reconcile satellite and ground evidence safely
**Priority:** P0 · **Labels:** `v3`, `decision-engine`, `integration`  
**Scope:** Implement observation pooling, source conflict behavior, satellite fallback interval, boundary-surfing guard and missing-source states per D5/WP-3.1.  
**Acceptance criteria:**
- Conflict preserves satellite interval so detectors continue rather than crash.
- Satellite-backed and ground-driven 33% crossings are distinguishable.
- Ground-only/satellite-only/no-observation cases match shared enums.
- Both conflict examples in the relay's local decisions are covered.
- Hazard context never enters numerical observation pooling.
**Blocked by:** P1-01, P1-06, P2-05. **Blocks:** P3-02, P3-03, P3-06, P4-02.

### P3-02 — Implement peer, timing, cluster and boundary detectors
**Priority:** P1 · **Labels:** `v3`, `decision-engine`, `detectors`  
**Scope:** Implement A–D detectors and peer selection with cross-assessor peer minimum, phenology fallback, HAND-adjusted timing and cluster-bias detection.  
**Acceptance criteria:**
- Cross-assessor share requirement and minimum cohort behavior match the relay decisions.
- Crop/sowing-date null path uses the specified spectral phenology fallback.
- Detector C handles unavailable recession evidence as CANNOT_ASSESS.
- Blanket village/assessor bias fires when the v3 cohort gap rule is met.
- Detector outputs use documented triggered/not-triggered/cannot-assess semantics and include evidence traces.
- **Blocked by:** P1-03, P1-06, P3-01.

### P3-03 — Build contributing-factor screen and evidence grade
**Priority:** P1 · **Labels:** `v3`, `decision-engine`, `explainability`  
**Scope:** Add deterministic factor codes and A–D evidence grade; use observability and limitations, not model probability.  
**Acceptance criteria:**
- All configured factor codes and firing/suppression rules are implemented.
- Each factor includes its input values and supporting evidence identifiers.
- Grade rubric is explicit, deterministic and caps grades for low clear fraction/small parcels/missing inputs as specified.
- Output does not expose unsupported “confidence %” as a calibrated probability.
- **Blocked by:** P1-04, P1-05, P2-05, P3-01, P3-02.

### P3-04 — Implement UTC-stable tamper-evident audit and idempotent analysis
**Priority:** P1 · **Labels:** `v3`, `audit`, `privacy`  
**Scope:** Canonical UTC timestamp hashing, JSON array canonicalization, primary keys/upserts, append-only audit log and verifier.  
**Acceptance criteria:**
- Verification is stable across database timezone settings.
- Repeated analysis/review does not duplicate case outputs.
- Tampering is detected and concurrent writes preserve chain ordering.
- Audit entries avoid Aadhaar and mask farmer/officer identifiers as designed.
- **Blocked by:** P1-01, X-03.

### P3-05 — Produce bilingual template reports with robust numeric verification
**Priority:** P1 · **Labels:** `v3`, `reports`, `localization`  
**Scope:** Build deterministic Marathi/English templates and verifier for decimal/percent equivalence, dates, Devanagari digits and direction checks.  
**Acceptance criteria:**
- Valid values like decimal and percentage forms pass, including Devanagari numerals.
- Wrong, unsupported, reversed and invented numeric claims fail verification.
- Report text cannot alter source values or the case tier.
- Marathi wording is reviewed by P2/native speaker.
- **Blocked by:** P2-05, P3-01, P3-03.

### P3-06 — Integrate analysis API, smoke fixtures and Stage 3 handoff
**Priority:** P1 · **Labels:** `v3`, `api`, `handoff`  
**Scope:** Wire `/analyze`, `/report`, `/audit/verify`; generate detection/factor/report fixtures and run integration handoff.  
**Acceptance criteria:**
- Every manifest case has a detection, grade, factors, report and audit link, including insufficient-evidence cases.
- API response matches frozen contracts and repeat calls are idempotent.
- Stage 3 handoff documents limitations, tests, known gaps and required downstream behavior.
**Blocked by:** P1-06, P2-05, P3-01, P3-02, P3-03, P3-04, P3-05. **Blocks:** P4-01, P4-02, P4-03, P4-04.

## Person 4 (P4) — Officer Dashboard, Benchmark & Demo

### P4-01 — Build read/review APIs and typed UI contracts
**Priority:** P1 · **Labels:** `v3`, `api`, `frontend`  
**Scope:** Implement queue/case/photo/review read APIs and response models used by the dashboard.  
**Acceptance criteria:**
- Filtering, ordering, facets and pagination behave per relay WP-4.1.
- High-priority dismissal requires a reason and writes review plus audit records.
- API responses validate against fixtures and typed client models.
- **Blocked by:** P1-01, P3-06; fixture scaffolding may proceed before handoff.

### P4-02 — Build evidence-first officer dashboard
**Priority:** P1 · **Labels:** `v3`, `frontend`, `accessibility`  
**Scope:** Implement queue, evidence ladder, parcel/frustum map, factor/grade cards, report/review panels and fairness monitor.  
**Acceptance criteria:**
- Shows official record, satellite observation, ground evidence and hazard context as distinct sections.
- Renders both satellite loss metrics, flags, grade limitations and evidence provenance.
- Map geometry/photo frustums match server-side spatial checks.
- Human review controls require reason codes where specified and expose audit outcome.
- Fairness view can filter/disaggregate by strip width and relevant groups, with limits explained.
- **Blocked by:** P3-06, P4-01; fixture-mode components may proceed during waiting time.

### P4-03 — Benchmark v3 against legacy design and report honest results
**Priority:** P1 · **Labels:** `v3`, `benchmark`, `version-reconciliation`  
**Scope:** Build injection benchmark and v2/v3 ablation where feasible; compare detector behavior without presenting synthetic cases as real-world validation.  
**Acceptance criteria:**
- Manifest, injection classes, metrics, intervals and thresholds are documented.
- Results tag synthetic data 🧪, show uncertainty intervals and state what they do not establish.
- Comparison isolates changed components and records excluded/future ablations.
- No old AI accuracy claim is copied into project materials as a current result.
- **Blocked by:** P1-06, P3-06, X-01, X-02.

### P4-04 — Deliver offline-ready demo, attribution and handoff
**Priority:** P1 · **Labels:** `v3`, `demo`, `docs`, `handoff`  
**Scope:** Contract tests, offline smoke path, pitch/demo/Q&A, rehearsals and backup video.  
**Acceptance criteria:**
- Demo succeeds with network disabled and a documented recovery path.
- All presented numbers trace to tagged results or verified sources.
- Q&A accurately states limits, synthetic inputs, human-in-loop and privacy safeguards.
- Exit Gate 4 checklist and final known-limitations/not-implemented list are complete.
- **Blocked by:** P3-06, P4-01, P4-02, P4-03, X-03.

## 5. Cross-owner issues

### X-01 — Freeze source-of-truth and archive legacy AI claims
**Priority:** P0 · **Owner:** P3 (decision engine) + P4 (docs); all owners review  
**Labels:** `version-reconciliation`, `docs`, `governance`  
**Description:** Mark the v3 spec and relay plan as current implementation sources. Add a short deprecation note to the old AI document (or an index/README if editing that historical artifact is undesirable) that identifies superseded modules and forbids carrying its unvalidated performance claims into demo material.  
**Acceptance criteria:** One authoritative source statement exists; older model/score proposals are explicitly historical; no contradictory claim remains in implementation-facing docs.
**Blocked by:** None. **Blocks:** X-02, P4-03, X-03.

### X-02 — Resolve and record cross-document ambiguities
**Priority:** P1 · **Owner:** P3; P1/P2/P4 review by area  
**Labels:** `contracts`, `version-reconciliation`, `integration`  
**Description:** Review relay Section 2.5 decisions (D-1 through D-22) and the stage-local decision tables (L2-1 through L2-5, L3-1 through L3-5, L4-1 through L4-5) against v3; record every selected interpretation in `contracts/CHANGELOG.md` before implementation. The relay contains no L1 decision table; do not invent L1 IDs.
**Acceptance criteria:** Every listed decision has an owner, affected payload/WP and linked regression fixture; all four owners acknowledge the baseline; contradictions are not silently resolved in code.
**Blocked by:** X-01. **Blocks:** P1-01, P3-01, P4-03.

### X-03 — Audit provenance, privacy and claim tags
**Priority:** P1 · **Owner:** P2 + P4; P1/P3 support  
**Labels:** `privacy`, `provenance`, `docs`  
**Description:** Establish a reusable provenance/claim checklist for external datasets, model weights, images and all numerical statements. Enforce no Aadhaar collection, EXIF removal, pseudonymous logging and real/synthetic/target tags.  
**Acceptance criteria:** Dataset/license register exists; sample reports and demo slides pass a traceability review; no sensitive identifiers appear in logs or thumbnails.
**Blocked by:** X-01; P2-05 and P3-05 for complete sample artifacts. **Blocks:** P4-04, X-05.
**Working document:** `DATA_PROVENANCE.md` (starter register; source/license review is still pending).

### X-04 — Complete missing v2/v3 references before pilot
**Priority:** P2 · **Owner:** P4, with P1/P3 input  
**Labels:** `docs`, `pilot-readiness`  
**Description:** Recover/replace the missing referenced sections/appendices and document v3 validation, privacy and build-plan requirements that the relay has only summarized.  
**Acceptance criteria:** Pilot checklist points to available documents; missing references are either restored or marked explicitly unavailable with an owner and plan.
**Blocked by:** X-01. **Blocks:** X-05.
**Working document:** `docs/REFERENCE_GAPS.md`.

### X-05 — Prepare four-week shadow pilot plan
**Priority:** P3 · **Owner:** P4; week leads P1/P3/P2 respectively  
**Labels:** `pilot`, `roadmap`, `human-review`  
**Description:** Turn the roadmap into week-specific deliverables, data access needs, responsible reviewer roles, blind gold-set procedure and shadow-mode safeguards.  
**Acceptance criteria:** No live payment effect; reason codes and human decisions retained; metrics and fairness are reported with intervals; thresholds change only via documented calibration.
**Blocked by:** X-03, X-04, P1-06, P2-05, P3-06, P4-03, P4-04.
**Working document:** `PILOT_READINESS.md` (draft only; blocker and approval gates remain open).

## 6. Suggested execution order

1. **Source/contract freeze:** X-01 → X-02 → P1-01.
2. **Stage 1:** P1-02 through P1-06; P3 prepares pure functions/tests and P4 prepares fixture UI/benchmark during allowed wait time.
3. **Stage 2:** P2-01 through P2-05 after Stage 1 handoff.
4. **Stage 3:** P3-01 through P3-06 after Stage 2 handoff.
5. **Stage 4:** P4-01 through P4-04 after Stage 3 handoff.
6. **Pilot readiness:** X-03 through X-05 as applicable.

## 7. Risks and open questions

- Actual names for P1–P4 are not included in the inspected work-split file; role assignment is therefore used.
- The project workspace does not contain a connected issue tracker or code repository implementation to receive these issues. This file contains proposed, tracker-ready issue text; filing externally would require a tracker connection and project selection.
- Confirm whether the detailed implementation plan referenced by the work split exists elsewhere; the listed workspace contains the three reviewed files only.
- Thresholds marked 🎯 remain calibration settings, not validated performance claims.
- The older AI document includes proposed metrics/models and formulas that conflict with v3; treat them as retired unless specifically re-evaluated.

## 8. Source mapping

- **v3 spec:** D1–D16; §§4–10; database schema; modules for parcels, optical/SAR, hazard context, ground verification, pooling, detectors, factors, grades, reports, APIs and dashboard.
- **AI version:** modules 1–5, weighted aggregation, random-forest root cause, confidence scoring, LLM report proposal, ethics and deferred scope.
- **Four-person work split:** role names, relay dependencies, WPs, global decisions, handoff/exit gates, risk register, waiting-time work and pilot roadmap.

---
*Issue descriptions are ready to copy into an issue tracker; IDs here are local backlog IDs and do not imply issues were created externally.*

## 9. Dependency graph and tracker behavior

### Critical path

```text
X-01 → X-02 → P1-01
                 ├─→ P1-02 → P1-03 → P1-04 / P1-05 ─┐
                 └───────────────────────────────────┴→ P1-06 → P2 stage → P2-05
                                                               ↓
                                                        P3-01 → P3-02 → P3-03 ─┐
                                                           ├──→ P3-04 ─────────┤
                                                           └──→ P3-05 ─────────┴→ P3-06
                                                                                       ↓
                                                    P4-01 → P4-02 ─┐                   │
                                                    P4-03 ─────────┼───────────────────┤
                                                    X-03 ──────────┘                   ↓
                                                                       P4-04 → X-05
X-04 (pilot documentation) ───────────────────────────────────────────────→ X-05
```

This graph is a summary. Each issue's **Blocked by** line is authoritative. Commas mean all listed blockers must be Done/Closed, except explicitly allowed fixture/stub work.

### Blocker check required when an issue is picked up

For every issue, the assigned person or AI agent should:

1. Read **Blocked by** and fetch each referenced issue's live tracker status.
2. If any blocker is open, in progress, or otherwise not Done/Closed, stop blocked implementation and report: `Blocked by <ID> — <status> — <owner> — <missing handoff/decision>`.
3. Do not mark the dependent issue Done while any blocker remains unresolved.
4. Continue only work explicitly marked as fixture/stub or waiting-time work in the relay. Keep it isolated and label the issue partially blocked.
5. When blockers close, verify the promised contract, handoff or artifact exists before proceeding; closing a ticket alone is insufficient if its acceptance criteria are unmet.

When imported into a tracker, map each **Blocked by** ID to a native “is blocked by” link. Keep local IDs in titles/descriptions so an AI coding agent can resolve dependencies even when tracker links are unavailable. This backlog does not claim live status; check the tracker when work is attempted.
