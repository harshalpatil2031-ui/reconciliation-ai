# Reconciliation AI — Evidence-led crop-loss review demo

A classroom prototype that demonstrates a simple workflow: a farmer submits a short Marathi/English report, an explainable rule compares a few evidence fields, and an officer reviews the case. It is advisory; it never decides compensation.

## Current scope

Read [`PROTOTYPE_SCOPE.md`](PROTOTYPE_SCOPE.md) first. The live demo is intentionally small and uses labeled synthetic cases. It demonstrates the workflow and how conflicting or missing evidence should be surfaced. Synthetic values do not describe real farms and do not establish accuracy.

- **v3 design:** [`reconciliation_ai_implementation_v3.md`](reconciliation_ai_implementation_v3.md) is retained as a future technical vision, not the demo checklist.
- **Four-person plan:** [`reconciliation_ai_work_split.md`](reconciliation_ai_work_split.md) describes the lightweight P1–P4 demo deliverables.
- **Issues:** [`ISSUES.md`](ISSUES.md) maps the remaining work and dependencies; completed work stays recorded as completed.
- **History and provenance:** [`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md), and [`contracts/CHANGELOG.md`](contracts/CHANGELOG.md).
- **Pilot:** [`PILOT_READINESS.md`](PILOT_READINESS.md) is explicitly deferred and is not authorization to use live data.

## Prototype experience

1. Open the farmer intake in Marathi or English and answer a few structured questions.
2. Complete the short form; the standalone walkthrough does not require camera, location or compass permission.
3. Save the report through the small local FastAPI/SQLite demo service.
4. Open the officer view, compare labeled evidence and live submissions, read why a case is flagged, and record a demo-only review note.
5. Reset and repeat with one of the bundled synthetic scenarios.

No external data service, government account or live imagery is required for the walkthrough. The 24–26 July 2024 Khadakwasla event may be used as narrative context only; any parcel-level evidence shown remains synthetic unless separately sourced and approved.

## Local setup

Requirements: Python 3.11 or newer and Node.js for the PWA. Docker is optional for the existing backend scaffold.

```sh
python -m pip install -r requirements.txt
make test
cd pwa
npm ci
npm test
npm run build
```

For the local dynamic walkthrough, start these in separate terminals from the repository root:

```sh
python -m uvicorn backend.demo_app:app --host 127.0.0.1 --port 8001
cd pwa
npm run dev
```

Open `http://localhost:5173/?demo=1`. Choose **Open officer demo** to review the bundled examples, or submit a farmer demo report; the SQLite-backed API makes it appear in the officer view, where it can be marked reviewed. **Reset demo reports** clears local demo submissions. This isolated API is demo-only, has no authentication, and must be bound to localhost; it does not call a government or production service. Demo mode does not request camera, location or motion permissions.

The standalone walkthrough skips photo capture. The existing camera flow remains in the non-demo PWA path. The original v3 backend and production integrations are still scaffolding; several routes return HTTP 501. The demo API is separate and uses a local SQLite file. Do not describe either API as a government or production integration.

## Prototype rules

- Label every example case and displayed measure as **synthetic**.
- Keep observed loss separate from hazard/context notes.
- Explain each demo flag with the input values that produced it.
- Missing evidence remains missing; it is not silently converted to zero.
- Show “needs human review” or “insufficient evidence,” never automatic approve/deny language.
- Do not collect Aadhaar, real farmer identity, or government records in the demo.
- Do not claim model accuracy, field validation, pilot readiness or decision support effectiveness.

## Deferred work

Real satellite/rainfall ingestion, parcel-level measurement, trained models, anti-spoofing, production offline synchronization, server-side duplicate prevention, authentication, audit/security certification, field studies and shadow-pilot work are future projects. See `PROTOTYPE_SCOPE.md` for the boundary and acceptance checklist.
