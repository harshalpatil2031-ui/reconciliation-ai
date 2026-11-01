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

This repository currently contains the specifications and issue-planning materials. The product implementation, live data pipeline, and benchmark outputs are not included yet. Consult the v3 spec’s scope and the relay exit gates before treating any feature as implemented.
