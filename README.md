# Reconciliation AI — Evidence-led crop-loss review demo

A classroom prototype that demonstrates a simple workflow: a farmer submits a short Marathi/English report, an explainable rule compares a few evidence fields, and an officer reviews the case. It is advisory; it never decides compensation.

## Current scope

Read [`PROTOTYPE_SCOPE.md`](PROTOTYPE_SCOPE.md) first. The live demo is intentionally small and uses labeled synthetic cases. It demonstrates the workflow and how conflicting or missing evidence should be surfaced. Synthetic values do not describe real farms and do not establish accuracy.

- **v3 design:** [`reconciliation_ai_implementation_v3.md`](reconciliation_ai_implementation_v3.md) is retained as a future technical vision, not the demo checklist.
- **Four-person plan:** [`reconciliation_ai_work_split.md`](reconciliation_ai_work_split.md) describes the lightweight P1–P4 demo deliverables.
- **Issues:** [`ISSUES.md`](ISSUES.md) maps the remaining work and dependencies; completed work stays recorded as completed.
- **Walkthrough script (PROTO-P4):** [`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) provides the 3–5 minute live classroom demo script, talking points, and reset steps.
- **History and provenance:** [`IMPLEMENTATION.md`](IMPLEMENTATION.md), [`DATA_PROVENANCE.md`](DATA_PROVENANCE.md) .
- **Pilot:** [`PILOT_READINESS.md`](PILOT_READINESS.md) is explicitly deferred and is not authorization to use live data.

## Prototype experience

1. Open the farmer intake in Marathi or English and answer a few structured questions.
2. Complete the short form; the standalone walkthrough does not require camera, location or compass permission.
3. Save the report through the small local FastAPI/SQLite demo service.
4. Open the officer view, compare labeled evidence (`Official`, `Satellite-style`, `Farmer report`, and explicit `MISSING` indicators) and live submissions, read why a case is flagged, and record a custom demo-only officer review note.
5. Refresh or reset and repeat with one of the bundled synthetic scenarios (`CASE-DEMO-01`, `CASE-DEMO-02`, `CASE-DEMO-03`).

No external data service, government account or live imagery is required for the walkthrough. The 24–26 July 2024 sample window is retained for classroom consistency.

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

```sh
python -m uvicorn backend.demo_app:app --host 127.0.0.1 --port 8001
```

In a second terminal, start the PWA:

```sh
cd pwa
npm run dev
```

Open `http://localhost:5173/?demo=1`. Choose **Open officer demo** (`अधिकारी प्रात्यक्षिक उघडा`) to review the bundled examples (`CASE-DEMO-01`, `CASE-DEMO-02`, `CASE-DEMO-03`), or submit a farmer demo report; the SQLite-backed API makes it appear in the officer view (and persist across page refreshes), where an officer can enter a custom review note and click **Mark reviewed in demo**. **Reset demo reports** (or `curl -X DELETE http://127.0.0.1:8001/demo/reports`) restores the clean starting state. See [`DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) for the 3–5 minute walkthrough script.

The standalone walkthrough skips photo capture. The existing camera flow remains in the non-demo PWA path. The original v3 backend and production integrations are still scaffolding; several routes return HTTP 501. The demo API is separate.

## Non-goals for this classroom repo

Real satellite/rainfall ingestion, parcel-level measurement, trained models, anti-spoofing, production offline synchronization, server-side duplicate prevention, authentication, audit/security certification, field studies and shadow operation.
