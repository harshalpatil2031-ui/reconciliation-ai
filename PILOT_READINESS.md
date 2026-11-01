# Four-week shadow pilot readiness plan

**Status:** Draft derived from the four-week roadmap in `reconciliation_ai_work_split.md` §10. This plan does not authorize access to government records or a live pilot. X-05 remains blocked until X-03/X-04 and the prototype exit gates are complete.

## Preconditions before Week 1

- X-03 provenance/privacy register reviewed; every real dataset, model, and photo has a documented access basis and use restriction.
- X-04 reference gaps resolved or explicitly accepted with named owner and plan.
- Prototype Exit Gates 1–4 passed; benchmark results tagged real/synthetic and reported with intervals.
- Pilot sponsor, data steward, officer reviewers, security contact, and shadow-mode owner identified.
- Written approval covers data access, retention, review protocol, and the no-payment-impact boundary.

## Work plan

| Week | Lead / support | Deliverables | Exit evidence / dependencies |
|---|---|---|---|
| 1 — Data access and historical baseline | P1 lead; P4 support | Confirm access for Bhunaksha Gat polygons in two selected flood-prone talukas; ingest permitted historical Sentinel-2 baselines by spectral cluster; document source IDs, license/access basis, coverage and missingness | Data steward approval; completed provenance entries; reproducible baseline manifest. Blocked by X-03/X-04 and authorized data access. |
| 2 — Blind gold set and rubric calibration | P3 lead; P4 review tool; P1 case selection | Three agriculture/revenue officers review 80 stratified historical cases, including narrow ribbon plots and delayed black-soil rot; collect independent labels before comparison; measure inter-rater agreement (Fleiss’ κ); calibrate A–D grade thresholds | Approved reviewer protocol; de-identified case list; completed labels; metric with uncertainty and limitations; signed calibration change in contract log. No tuning on the same cases used for a headline benchmark. |
| 3 — Security and crop-record sandbox | P2 lead; P3 audit support | Test authorized e-Peek Pahani sandbox flow; assess uploader attestation (WebAuthn / Android Play Integrity) and pre-flood photo background/horizon checks; document threat model and failures | Sandbox approval; privacy/security review; audit fields verified; no Aadhaar or unnecessary identity capture. |
| 4 — Shadow audit | P4 lead; all owners support | Run beside live panchnamas in shadow mode; officers review flags and provide reason codes; measure review time per flagged case and district/group fairness | Written sponsor approval; no effect on payments; audit trail and reason codes complete; metrics with intervals; issue log and stop/rollback criteria. |

## Pilot guardrails and reporting

- The system remains advisory and has no write path to government assessment or payment systems.
- No model output is communicated as an award, denial, or eligibility decision to farmers.
- Every officer disposition has a reason code; preserve disagreements and overrides for analysis.
- Report sample sizes, missing data, uncertainty intervals, and real-versus-synthetic status. Do not claim field accuracy from the synthetic prototype benchmark.
- Thresholds tagged 🎯 change only through the blind gold-set calibration and a dated contract change with owner acknowledgement.
- Define data minimization, access, retention, deletion, incident response, and rollback before the first case is loaded.

## Go / no-go checklist

- [ ] X-03 and X-04 are closed with review evidence.
- [ ] Prototype Exit Gates 1–4 and offline smoke criteria pass.
- [ ] Data, image/model licenses and official access are documented and approved.
- [ ] Three reviewers, blind protocol, stratification, and metric definitions are confirmed.
- [ ] Security, privacy, retention, audit, and rollback reviews are signed.
- [ ] Shadow-only boundary is technically and operationally enforced.
- [ ] Sponsor approves start; no external pilot begins based on this draft alone.
