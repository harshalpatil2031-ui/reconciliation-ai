# Prototype issues — four-person build

These are the **four active work items** for the smaller, dynamic classroom prototype. The matching GitHub issues are live. The older P1–P4 technical backlog is deferred future work, not the prototype acceptance plan. Closed issues retain their history and include links to the replacements.

## Issue 1 — Person 1: synthetic cases and shared data contract

**GitHub issue:** [#39](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/39)
**Title:** `[PROTO-P1] Prepare synthetic case fixtures and prototype data contract`
**Owner:** Person 1 — Data & Scenarios
**Priority:** Prototype critical
**Labels:** `prototype`, `data`
**Depends on:** None. This contract unblocks P2, P3 and P4.

Create 3–6 small, hand-authored example cases for the demo and agree the JSON shape with P2–P4.

**Acceptance criteria**

- Include a near-threshold disagreement, a consistent example and a missing-evidence example.
- Mark every case and number synthetic; do not imply parcel-level measurements are real.
- Document fields, status values, reason text and missing-value behavior.
- Keep fixtures small and readable; no rasters, 450-parcel world, real claims or database snapshot.

**Deliverables:** `fixtures/demo_cases.json` and a short data dictionary.

## Issue 2 — Person 2: Marathi farmer intake

**GitHub issue:** [#40](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/40)
**Title:** `[PROTO-P2] Connect the Marathi farmer intake to the local demo API`
**Owner:** Person 2 — Farmer Intake
**Priority:** Prototype critical
**Labels:** `prototype`, `farmer-pwa`
**Depends on:** P1 fixture/payload agreement and P3's localhost API contract.

Use the existing Marathi/English PWA form in standalone demo mode. POST submissions to the local demo service and make clear that this is synthetic demonstration data.

**Acceptance criteria**

- `/?demo=1` works without a case token, user account, camera, GPS or compass.
- User can complete the form and submit to the local API.
- A successful save is confirmed; API errors are explained and can be retried.
- Standalone demo flow does not require a photo; no photo is described as verified.
- The PWA test covers the dynamic submit flow.

**Deferred:** production upload, offline sync guarantees, native-device field validation.

## Issue 3 — Person 3: local API and explainable rules

**GitHub issue:** [#41](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/41)
**Title:** `[PROTO-P3] Build the local SQLite API and explainable demo rules`
**Owner:** Person 3 — Backend & Rules
**Priority:** Prototype critical
**Labels:** `prototype`, `backend`
**Depends on:** P1 fixture contract. P2 and P4 consume the API contract.

Build a small localhost-only FastAPI service backed by SQLite. Serve P1's fixtures; accept/list farmer demo reports; allow an officer to record a demo review note; support reset. Return a simple deterministic explanation tied to submitted and fixture values.

**Acceptance criteria**

- `GET /demo/cases`, `GET/POST /demo/reports`, `POST /demo/reports/{id}/review`, and `DELETE /demo/reports` work locally.
- Report validation rejects invalid ranges and enumerations.
- Data survives server/page refresh and reset clears demo submissions.
- Missing evidence remains null/unknown.
- Tests cover fixture load, create/list, review and reset.
- App is clearly demo-only and run bound to localhost; no authentication or production-readiness claim.

**Deferred:** PostgreSQL/PostGIS workflow, full v3 endpoints, production auth, audit hash-chain and deployment.

## Issue 4 — Person 4: officer review and demo walkthrough

**GitHub issue:** [#42](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/42)
**Title:** `[PROTO-P4] Build the dynamic officer review screen and demo walkthrough`
**Owner:** Person 4 — Officer View & Demo
**Priority:** Prototype critical
**Labels:** `prototype`, `demo`, `frontend`
**Depends on:** P1 fixture contract and P3 API; coordinate integration with P2.

Build a compact officer view consuming P3's local API. Show P1's synthetic scenarios and farmer reports created through P2; allow a demo-only review action.

**Acceptance criteria**

- Shows official, satellite-style, farmer-reported and missing evidence distinctly.
- Each case explains its displayed status from its fixture values.
- New farmer submissions appear after saving and after page refresh.
- Officer can record a local demo review note/status.
- UI states all cases are synthetic and never presents automatic approval/denial.
- Provide setup/reset steps and a 3–5 minute script; walkthrough runs with local services only.

**Deferred:** maps/frustums, full queue API, fairness monitor, benchmark claims and pilot.

## Dependency order

```text
PROTO-P1 ──┬──> PROTO-P2 ──┐
           ├──> PROTO-P3 ──┼──> PROTO-P4 integration and demo
           └───────────────┘
```

P2 and P3 can proceed in parallel once their shared request/response shape is agreed. P4 builds against fixtures while the local API is in progress, then integrates. Database snapshots, real imagery, phone testing and pilot approvals are not prototype blockers.

## Tracker migration note

The earlier field-system issues #12–#26 were closed as not planned for the current classroom prototype. Each has a closure comment linking to the replacement issue(s). Keep the detailed v3 backlog as future planning; new prototype work should use issues #39–#42 and check their dependency notes before starting.
