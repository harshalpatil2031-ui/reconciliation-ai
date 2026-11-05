# Reconciliation AI — Prototype Scope

**Current goal:** deliver a clear, runnable classroom/demo prototype of an evidence-led crop-loss review workflow. This repository is not a pilot system and does not make compensation decisions.

## What the prototype demonstrates

1. A farmer-facing Marathi/English intake with a few structured answers. The local walkthrough does not require or collect a photo.
2. A small set of clearly labeled **synthetic** cases with internally consistent official, satellite-style, and farmer-reported evidence.
3. A deterministic, explainable comparison that shows why a case is marked for human review.
4. A small local FastAPI + SQLite backend that stores demo reports and review notes, plus an officer screen that displays them dynamically.
5. A short scenario walkthrough that works on one laptop without external accounts, government records, live sensors, or internet access after setup.

The demo may use the 24–26 July 2024 Khadakwasla event as narrative context only. Unless provenance and permission are documented, every parcel, crop, loss estimate, official assessment, photo and case outcome remains synthetic. The realistic element is the workflow and the evidence trade-off, not a claim that the measurements describe real farms.

## Prototype boundary

| Keep for the demo | Simplify or defer |
|---|---|
| Marathi-first form and language toggle | Real farmer identity, OTP, Agri Stack or government integrations |
| Existing camera pathway remains available outside the local walkthrough | Photo capture/storage in the local API, mandatory GPS accuracy, compass calibration, multi-angle capture, spoof detection and image embeddings |
| 3–6 hand-authored synthetic case fixtures with provenance labels | 300+ parcel world, scene acquisition, live satellite/SAR processing, calibrated damage estimates |
| Transparent rules and evidence-quality labels | Probabilistic confidence, tuned thresholds, trained classifiers, claims of accuracy |
| Local SQLite persistence and a visible demo reset | Production offline synchronization, guaranteed server idempotency, multi-user security |
| One officer case view, evidence comparison and human review note | Full REST surface, audit hash chain, fairness monitoring, pagination, maps and pilot operations |
| Tests for deterministic rules, payload shape and the happy-path demo | Field validation, security certification and shadow-pilot readiness |

## Four-person demo plan

| Person | Owns | Prototype deliverable |
|---|---|---|
| **P1 — Data & scenarios** | Fixtures and evidence labels | 3–6 synthetic cases in a versioned JSON file; source labels; one “near the 33% line” walkthrough |
| **P2 — Farmer intake** | Marathi/English intake | Short form, submit to local API, and a clear demo-saved state; no image needed |
| **P3 — Local backend & rules** | FastAPI + SQLite, demo persistence, deterministic comparison | Local report create/list/review/reset; rule reasons carry source values; missing evidence yields “not enough information” |
| **P4 — Officer demo** | Review screen and rehearsal | Case list/detail, evidence cards, live farmer submissions, human review action, 3–5 minute script and reset instructions |

Work can proceed in parallel against the checked-in fixture contract and small localhost API contract. Integrate when each piece is ready; PostgreSQL database snapshot handoffs are unnecessary for this prototype.

## Demo acceptance checklist

- [ ] Clean setup instructions work on one supported laptop.
- [ ] Demo loads with the small local API; it makes no external service calls.
- [ ] Farmer flow saves one demo submission to the local SQLite API and it appears in the officer view after refresh.
- [ ] Officer view shows at least three labeled synthetic scenarios, including a near-threshold disagreement and a missing-evidence case.
- [ ] Each flag has a plain-language reason and links to the displayed fixture values.
- [ ] “Needs human review” and “insufficient evidence” are possible outcomes; no automatic approve/deny language appears.
- [ ] Demo reset returns fixtures and local state to the starting point.
- [ ] Automated checks cover fixture schema, rule examples, farmer payload, and one end-to-end demo path.
- [ ] Demo script says which inputs are synthetic and what the demo does not validate.

## After the prototype

Real imagery, official records, parcel geometry, robust offline synchronization, server-side duplicate protection, field usability, Marathi language review, audit/security controls, representative evaluation and any pilot are separate follow-up work. They need data permission, provenance, technical owners and appropriate human review. Passing the demo checklist does not authorize a live pilot or establish field performance.

## Scope-change rule

If a demo task requires real government or farmer data, a production service, specialized field devices, a trained model, or an unmeasured claim of accuracy, defer it and keep the demo moving with labeled fixtures. Update this file before expanding the accepted prototype scope.
