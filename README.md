# Reconciliation AI — Maharashtra Flood Compensation QA

An evidence-led, human-reviewed quality-assurance system for reconciling crop-loss assessments with satellite and verified ground evidence. It helps officers prioritize review; it does not approve or deny compensation.

## Source of truth

Use **`reconciliation_ai_implementation_v3.md`** for the current technical design and **`reconciliation_ai_work_split.md`** for the four-person ownership, work packages, shared contracts, dependency decisions, handoffs, and exit gates. Read both before implementing a feature. If they conflict, resolve the ambiguity through the relay decision register and record the result in its contract change log; do not silently choose an interpretation.

The v3 spec references companion v2 validation/build-plan material and a detailed implementation plan that are not currently present in this repository. Track recovery or replacement of those references under **X-04** before pilot planning.

**`IMPLEMENTATION.md` is the historical prototype proposal.** Its Siamese CNN, weighted evidence score, IndicBERT severity model, Random Forest/SHAP, numeric confidence score, and LLM report proposal are superseded where they conflict with v3. Do not present its unverified metrics as current results.

## Project documents

| File | Purpose |
|---|---|
| [`reconciliation_ai_implementation_v3.md`](reconciliation_ai_implementation_v3.md) | Current technical specification: evidence model, data/schema, satellite and ground methods, detectors, grading, reports, API, and dashboard. |
| [`reconciliation_ai_work_split.md`](reconciliation_ai_work_split.md) | Four-person relay plan: P1–P4 roles, contracts, work packages, decision register, handoffs, blockers, and exit gates. |
| [`ISSUES.md`](ISSUES.md) | Tracker-ready backlog with owners, acceptance criteria, blockers, dependency graph, and AI-agent blocker-check procedure. |
| [`contracts/CHANGELOG.md`](contracts/CHANGELOG.md) | Baseline register for relay decisions D-1 through D-22 and a template for future contract changes. |
| [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) | Starter register for data, model, photo and claim provenance; entries still require source/license review. |
| [`docs/REFERENCE_GAPS.md`](docs/REFERENCE_GAPS.md) | Missing v2/detailed-plan references and the owner/action needed to close each gap. |
| [`PILOT_READINESS.md`](PILOT_READINESS.md) | Draft four-week shadow-pilot plan; prerequisites and approvals are still pending. |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | Historical prototype AI proposal, retained for comparison only. |
| `.github/ISSUE_TEMPLATE/` | GitHub issue templates, including required blocker fields. |

The four roles are called P1–P4 because the source work-split document does not contain team members’ names. Map them to actual GitHub assignees while preserving the role responsibilities.

## Issue workflow and dependencies

Keep each backlog ID (for example, `P1-01` or `X-01`) in the GitHub issue title. Link every **Blocked by** item using GitHub’s native dependency relationship where available. Before starting an issue, the assignee or AI agent must check the live status and required handoff artifacts for every blocker. If a blocker is not Done/Closed, report its ID, status, owner, and missing handoff; only isolated fixture/stub work explicitly permitted by the relay may proceed. Do not close a dependent issue until its blockers and acceptance criteria are satisfied.

Start with X-01, then X-02, then P1-01. Follow the dependency graph and stage gates in `ISSUES.md`; its per-issue **Blocked by** fields are authoritative.

## Version and evidence rules

- Observed damage and hazard plausibility remain separate; hazard context does not enter the numerical damage estimate.
- A human officer makes the compensation decision.
- Tag claims and numbers as verified, unverified, synthetic, initial/untuned, or roadmap according to the v3 status legend.
- Do not describe synthetic benchmark results as real-world performance.
- Do not collect Aadhaar.

## Repository status

The initial data foundation is now scaffolded: PostgreSQL/PostGIS/pgvector schema, typed shared configuration and contracts, FastAPI endpoint stubs, raster quality/alignment helpers, and hazard-context extraction. Satellite source files, authorized rainfall/discharge inputs, populated demo data, production APIs, and benchmark outputs are not included yet. Consult the v3 spec’s scope and the relay exit gates before treating any feature as implemented.

## Local foundation setup

Requirements: Docker Compose and Python 3.11 or newer.

```sh
cp .env.example .env
make up
make schema
python -m pip install -r requirements.txt
make test
make openapi
```

The API runs with `uvicorn backend.main:app`. Stage-owned API routes currently return HTTP 501; `/health` reports database availability and the active configuration digest. The database initialization SQL is safe to apply repeatedly with `make schema`.

After the source rasters and hazard JSON inputs have been acquired and their licenses recorded, run `make check-rasters` and `make check-hazard`. Both commands emit quality reports and exit nonzero while required source files are missing or invalid; they never replace missing evidence with zero-valued measurements.

## Optical pipeline

The optical pipeline expects aligned per-scene arrays and does not claim scene acquisition or validation. Its onset flag uses the earliest selected post-event scene with attributable loss; with only two windows, timing cannot be localized more precisely. Missing scenes return `NO_VALID_OPTICAL_SCENE`; low clear fraction and low spatial support carry a grade cap of C for the downstream grader. Supply the parcel preparation result as each scene's `parcel_stack` so its fractional pixel weights and aligned spectral arrays are used by the optical metrics. Scenes without an explicit water mask or NDWI water evidence are skipped and flagged rather than counted as vegetation loss.

## Parcel preparation

`pipeline/parcel_prep.py` supersamples pixel/parcel intersections at the configured factor, applies the 5 m interior buffer only to parcels at least 35 m wide, and preserves narrow parcels using squared overlap weights. It also provides effective-pixel reliability, deterministic per-taluka spectral clustering, matched upland-control selection, async persistence of cluster labels and sparse per-pixel weights, and a snapped raster-window reader. Persisted scene observations include the sparse overlap grid and `n_eff_pixels`; parcel rows retain the measured minimum width. No pre-event source rasters are included, so this repository does not claim actual scene dates or populated clusters. When rasters are supplied, pass all available pre-event NDVI observations (late May through mid-July where available) and the last pre-event NDMI to the clustering function; missing scenes are not fabricated.
