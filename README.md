# Reconciliation AI — Maharashtra Flood Compensation QA

An evidence-led, human-reviewed quality-assurance concept for reconciling crop-loss assessments with satellite and verified ground evidence. The system is intended to help officers prioritize review; it does not approve or deny compensation.

## Project documents

| File | Role |
|---|---|
| [`reconciliation_ai_implementation_v3.md`](reconciliation_ai_implementation_v3.md) | Current technical specification and v3 decisions. |
| [`reconciliation_ai_work_split.md`](reconciliation_ai_work_split.md) | Four-person relay plan, work packages, contracts, handoffs, and exit gates. |
| [`reconciliation_ai_v3_ai_issues.md`](reconciliation_ai_v3_ai_issues.md) | Tracker-ready issue drafts, ownership, explicit blockers, and dependency graph. |
| [`Reconciliation_AI_Implementation.md`](Reconciliation_AI_Implementation.md) | Older AI implementation proposal; historical context where it conflicts with v3. |
| [`Reconcilation AI Indradhanu PPT (1).pdf`](Reconcilation%20AI%20Indradhanu%20PPT%20(1).pdf) | Existing presentation reference. |

**Implementation source of truth:** v3 plus the relay work split. The older AI proposal is not the implementation plan where it conflicts with v3. See the issue backlog’s version comparison before carrying forward older model or performance claims.

## Issue workflow

The backlog uses local IDs such as `P1-01` and `X-01`. When creating GitHub issues, keep the ID in the title and copy the issue’s **Blocked by** line into GitHub’s native dependency relationship (or link the blocker in the issue body). Do not treat a dependent issue as ready until all blockers are closed and the required handoff artifact exists.

The four owners are currently called P1–P4 because the source work-split file does not provide names. Replace those labels with the team’s names in GitHub while preserving the role mapping.

## Status and scope

This repository currently contains planning and specification documents. The application implementation, data pipeline, and test suite are not included yet. Performance numbers or thresholds marked synthetic, unverified, or initial in the specs must retain those qualifications in any demo or report.

## Getting started

1. Read the v3 specification’s status legend and architecture.
2. Read Sections 1–2 of the relay plan for roles, shared contracts, and dependency rules.
3. Pick work only after checking its blockers in the issue tracker.
4. Record any contract change in the relay’s change log before downstream work relies on it.
