# PROTO-P4: Officer Review & 3–5 Minute Classroom Demo Walkthrough

This document provides the setup, reset, and 3–5 minute live walkthrough script for **[PROTO-P4] ([Issue #42](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/42))** in [`harshalpatil2031-ui/reconciliation-ai`](https://github.com/harshalpatil2031-ui/reconciliation-ai). Everything runs locally on a single laptop without external network calls, GPS/camera permissions, or live government/satellite services.

## 1. Local Setup & Verification Commands

### Prerequisites
- Python 3.11+ and Node.js 18+

### Install & Run Automated Checks
```sh
python -m pip install -r requirements.txt
make test
cd pwa
npm ci
npm test
npm run build
```

### Start the Standalone Demo (Two Terminals)

**Terminal 1 — Start the local SQLite-backed Demo API (`127.0.0.1:8001`):**
```sh
python -m uvicorn backend.demo_app:app --host 127.0.0.1 --port 8001
```

**Terminal 2 — Start the PWA Frontend (`localhost:5173`):**
```sh
cd pwa
npm run dev
```

Open **`http://localhost:5173/?demo=1`** in your browser.

## 2. Reset & Recovery Instructions

Before starting a live presentation (or between walkthrough runs), reset the local demo state so only the three baseline synthetic fixtures in [`fixtures/demo_cases.json`](https://github.com/harshalpatil2031-ui/reconciliation-ai/blob/main/fixtures/demo_cases.json) remain:

- **Option A (In Browser UI):** Open `http://localhost:5173/?demo=1`, select **Open officer demo** (`अधिकारी प्रात्यक्षिक उघडा`), and click **Reset demo reports**.
- **Option B (Terminal CLI):**
  ```sh
  curl -X DELETE http://127.0.0.1:8001/demo/reports
  ```
- **Option C (Hard File Reset):** Delete `data/demo.sqlite3` and restart `uvicorn backend.demo_app:app --host 127.0.0.1 --port 8001`.

## 3. Timed 3–5 Minute Classroom Walkthrough Script

| Time Window | Screen / Action | What to Show & Explain |
| :--- | :--- | :--- |
| **0:00 – 0:45** | **Welcome Screen (`/?demo=1`)** | Point out the top banner: `DEMO · Synthetic examples · Local prototype API · Nothing sent externally`. State upfront that all cases and comparison numbers are synthetic classroom examples and that the tool is strictly advisory—it never approves or denies crop-loss compensation. |
| **0:45 – 2:00** | **Officer Demo — Synthetic Scenarios** (`Open officer demo`) | Walk through the three bundled scenarios from [`fixtures/demo_cases.json`](https://github.com/harshalpatil2031-ui/reconciliation-ai/blob/main/fixtures/demo_cases.json):<br>1. **`CASE-DEMO-01` (Near threshold disagreement):** Official `30%` is below the illustrative `33%` demo line, while Satellite-style (`36%`) and Farmer report (`34%`) are above it $\rightarrow$ `NEEDS_HUMAN_REVIEW`.<br>2. **`CASE-DEMO-02` (Evidence agrees):** Official `55%`, Satellite-style `58%`, and Farmer report `56%` are all above `33%` and within 3 percentage points $\rightarrow$ `CONSISTENT_FOR_DEMO`.<br>3. **`CASE-DEMO-03` (Missing satellite-style evidence):** Official `35%` and Farmer report `42%` are present, while Satellite-style is `unavailable` (`MISSING`). Highlight the explicit notice: *Missing evidence: Satellite-style value is unknown (MISSING); no value is inferred* $\rightarrow$ `INSUFFICIENT_EVIDENCE`. |
| **2:00 – 3:15** | **Farmer Marathi/English Intake** (`Back to demo start` $\rightarrow$ `प्रात्यक्षिक अर्ज सुरू करा` / `Start demo report`) | Demonstrate the farmer intake in Marathi (`मराठी`) or switch to English (`English`). Set damaged share to `65%`, choose water depth `Up to knee` (`KNEE`), `2` days, crop stage `Growing` (`VEGETATIVE`), and add a short field note. Click **Continue** $\rightarrow$ **Save on this device**. Show the confirmation screen displaying `Official assessment: 20% · Satellite-style example: 40% · Farmer report: 65%`, the plain-language explanation of the 45-point spread, and the `synthetic demo example` label. |
| **3:15 – 4:30** | **Officer Review & Page Refresh** (`Open officer view` / Browser Refresh) | Open the officer view and click **Refresh officer data** (or refresh the browser page) to show that the newly submitted farmer report persists in local SQLite (`GET /demo/reports`). Point out the farmer's submitted field details (`Water depth KNEE (2 days) · Crop stage VEGETATIVE`). Type a custom note in **Officer review note (demo only)** (e.g., `"Verify field drainage note with village officer"`), and click **Mark reviewed in demo**. Observe the status change from `NEEDS_HUMAN_REVIEW` to `REVIEWED_FOR_DEMO` with the saved note attached. |
| **4:30 – 5:00** | **Limitations & Reset** (`Reset demo reports`) | Reiterate what this classroom prototype intentionally does **not** validate: no live satellite/rainfall ingestion, no GPS/camera anti-spoofing in standalone demo mode, no automated eligibility or payout determination, and no pilot readiness. Click **Reset demo reports** to return the database to its clean starting state. |
