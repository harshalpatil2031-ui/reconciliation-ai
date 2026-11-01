# Contract change log

This file records the relay's binding decisions and later changes to shared contracts. The detailed rationale and complete decision text live in [`reconciliation_ai_work_split.md`](../reconciliation_ai_work_split.md), Section 2.5. Do not silently diverge from those decisions in code or docs.

## 2026-11-01 — Baseline decision register transcribed from relay plan

**Change:** Added a traceable index for global decisions D-1 through D-22 and stage-local decisions L2-1 through L2-5, L3-1 through L3-5, and L4-1 through L4-5 already specified in the relay plan. This entry records the documented baseline; it does not claim that all four owners have acknowledged it, that code implements it, or that tests have passed. The relay currently contains no L1 decision table; do not invent L1 IDs.

**Affected:** P1 schema/data/satellite work, P2 photo verifier and farmer form, P3 pooling/detectors/grading, and P4 API/dashboard/benchmark. The decision owner(s), precise resolution, affected work package, and acceptance checks are in the referenced Section 2.5 and stage work packages.

| Decision IDs | Primary stage(s) | Status |
|---|---|---|
| D-1, D-8, D-9, D-11, D-12, D-15, D-18, D-20, D-21, D-22 | P1 (some shared with P3/P4) | Recorded from relay; owner acknowledgement and implementation evidence pending |
| D-2, D-3, D-4, D-19 | P2 (some shared with P3) | Recorded from relay; owner acknowledgement and implementation evidence pending |
| D-5, D-6, D-7, D-13, D-14, D-17 | P3 | Recorded from relay; owner acknowledgement and implementation evidence pending |
| D-10 | P1, P3 | Recorded from relay; scene availability check and implementation evidence pending |
| D-16 | P1, P3, P4 | Recorded from relay; implementation and benchmark evidence pending |

| Local decision IDs | Primary stage(s) | Status |
|---|---|---|
| L2-1 through L2-5 | P2 (some shared with P1/P3) | Recorded from relay; owner acknowledgement and implementation evidence pending |
| L3-1 through L3-5 | P3 | Recorded from relay; owner acknowledgement and implementation evidence pending |
| L4-1 through L4-5 | P4 | Recorded from relay; owner acknowledgement and implementation evidence pending |

**Next step:** Before implementation starts, all four owners should acknowledge D-1 through D-22 and L2-1 through L2-5, L3-1 through L3-5, and L4-1 through L4-5 in the tracker or an appended sign-off table. Each decision's specified tests/acceptance checks must be linked from its implementation issue. If a decision changes, append a dated entry below with the decision ID, old and new behavior, reason, affected contract/payload/work packages, approving owners, and regression fixture.

## Change entry template

### YYYY-MM-DD — D-xx: Short change title

- **Decision / previous behavior:**
- **New behavior and reason:**
- **Affected contracts, payloads, work packages:**
- **Approvers:**
- **Regression fixture or acceptance check:**
