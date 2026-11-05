# Reconciliation AI — Four-person prototype plan

> **Purpose:** build a small, presentable demonstration of evidence-led crop-loss review. The system is advisory and uses labeled synthetic examples. It is not a pilot, a measurement of real-world performance, or a compensation decision system.
>
> **Current scope:** [`PROTOTYPE_SCOPE.md`](PROTOTYPE_SCOPE.md). The detailed v3 document remains a future technical vision; it is not the acceptance checklist for this demo.

## Demo flow

```text
Synthetic scenarios (P1) → Farmer intake (P2) → Explainable rules (P3) → Officer review (P4)
      └────────────────────── shared fixture contract ──────────────────────┘
```

People can build in parallel. They agree on a small JSON fixture shape first, use a local browser/API stub, and integrate without requiring stage database dumps.

## Shared fixture contract

Each case in `fixtures/demo_cases.json` contains:

- `id` and `title`
- `official_pct` and `satellite_style_pct` (illustrative numbers; `null` means missing)
- `status` with one of `NEEDS_HUMAN_REVIEW`, `CONSISTENT_FOR_DEMO`, `INSUFFICIENT_EVIDENCE`
- `reason` explaining the example in plain language

Farmer reports use `{locale, form}` with the structured `GroundForm` fields. The local API returns a report ID, `NEEDS_HUMAN_REVIEW`, an explanation, and `data_status: "synthetic demo example"`.

Every numeric fixture value must be visibly labeled synthetic. Missing input stays missing; do not fill it with a plausible-looking number. Fixtures are examples for UI and rule behavior, not a benchmark or validation set.

## Work by person

### P1 — Synthetic cases and data setup

**Build:** 3–6 small cases in `fixtures/demo_cases.json`; include one near-threshold disagreement, one consistent case, one missing-evidence case, and optionally one high farmer-reported / low satellite-style case. Add a short data dictionary and a one-command seed/reset path if the existing app needs it.

**Done when:** fixture schema validates; provenance and synthetic labels are visible; values and expected flags are internally consistent; no real person, parcel or claim is represented.

### P2 — Farmer intake

**Build:** retain the Marathi/English structured intake already present, but make the demo path straightforward. The standalone walkthrough does not need a photo; camera, location and compass must not block it. Submit to P3's localhost demo API and show that the report is synthetic/demo data.

**Done when:** a user can complete the short form and submit through the local API, then refresh and see the saved state; the demo flow works without camera, GPS, compass, account or external service.

### P3 — Explainable comparison

**Build:** a lightweight local FastAPI + SQLite service for fixture reads, farmer submissions and review notes, plus a small deterministic rule over fixture values. Show the values and a reason for each flag. Keep hazard/context separate from observed loss. Do not present a confidence percentage or automatic eligibility recommendation.

**Done when:** tests cover fixture reads, create/list submissions, review notes and reset; rule examples have unit tests; missing data never becomes zero; outputs are traceable; a human can annotate the demo state. Bind the API to localhost and label it demo-only.

### P4 — Officer review and presentation

**Build:** a compact case list and detail view consuming the local API, including both fixtures and newly submitted farmer reports, a review note/action, a visible synthetic-data banner, reset instructions, and a 3–5 minute walkthrough.

**Done when:** all three core scenarios plus a newly submitted report are demonstrable on one laptop with the local service; the script explains the synthetic inputs and limitations; no slide or screen implies that the tool determines payment.

## Integration order

1. Agree on `fixtures/demo_cases.json` and synthetic-data labels.
2. P1 publishes the fixture examples; P2/P3/P4 work against them in parallel.
3. P3 publishes `/demo/cases` and `/demo/reports`; P2 submits farmer intake to the local service; P4 renders the cases and submissions and records a demo review note.
4. Rehearse the complete flow, run the demo checks, and document reset/recovery steps.

There are no required database-snapshot handoffs for this scope. A missing future production component must be labeled deferred; it must not block the prototype demonstration.

## Deferred technical vision

The detailed specifications in `reconciliation_ai_implementation_v3.md` and the older `IMPLEMENTATION.md` are retained for design history and future planning. For this prototype, defer real Sentinel processing, licensed imagery acquisition, 450-parcel seeding, SAR/HAND calibration, photo anti-spoofing or embeddings, crop classification, server-side idempotency, hash-chained audit, a full dashboard/fairness monitor, trained NLP/ML, government integrations, field testing, and shadow-pilot work.

## Prototype exit checklist

- [ ] Scope and synthetic-data boundaries are clear in README and demo UI.
- [ ] A clean local setup and reset path are documented.
- [ ] Farmer intake → local saved record → officer evidence review works.
- [ ] Three core scenarios render and produce expected explanations.
- [ ] Automated tests cover fixture validation, rules, payload and end-to-end flow.
- [ ] Demo script completes in 3–5 minutes and includes limitations.
- [ ] Deferred work is listed separately; no pilot-readiness claim is made.
