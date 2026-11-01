# 🌾 Reconciliation AI — Maharashtra Flood Compensation QA

> **Team:** PCCOE Indradhanu · **Stage:** Prototype Round 2 → 24-Hour Hackathon  
> **Domain:** AI for Social Good · Disaster Management · AgriTech

An evidence-led, human-reviewed quality-assurance system for reconciling crop-loss compensation assessments with satellite imagery, rainfall data, and verified ground evidence from farmers.

> ⚠️ **The system is advisory only.** It helps officers prioritize review. It does not approve or deny compensation.

---

## 📋 What We Are Building (Prototype)

A fully functional, end-to-end reconciliation pipeline demonstrated on real data from the **Maharashtra Floods of July 2024** (Pune, Nashik, Kolhapur districts).

| Layer | Technology |
|---|---|
| **Frontend** | React.js 18 + Vite · Leaflet.js · Recharts |
| **Backend** | FastAPI (Python) — synchronous ML pipeline |
| **Database** | PostgreSQL 15 + PostGIS 3.4 |
| **ML — Satellite** | PyTorch Siamese CNN · Sentinel-2 NDVI/NDWI · Sentinel-1 SAR |
| **ML — NLP** | IndicBERT (ai4bharat/indic-bert) fine-tuned for Marathi/Hindi |
| **ML — Photo** | torchvision ResNet-50 — flood damage classification |
| **ML — Root Cause** | scikit-learn Random Forest + SHAP explainability |
| **Report Generation** | Gemini 1.5 Flash API (free tier — 1,500 req/day, no credit card) |

All data is **pre-loaded for the prototype**. ML inference runs **fully locally**. The only external call during demo is the Gemini 1.5 Flash API for report narrative generation.

---

## 📂 Project Documents

| File | Role | Status |
|---|---|---|
| [`Reconciliation_AI_Implementation.md`](Reconciliation_AI_Implementation.md) | **Primary spec — Prototype Round.** Full technical detail: ML architectures, data sources, API design, dashboard. | ✅ Current |
| [`reconciliation_ai_implementation_v3.md`](reconciliation_ai_implementation_v3.md) | v3 extended specification — evidence-led, human-review system design decisions. | ✅ Current |
| [`reconciliation_ai_v3_ai_issues.md`](reconciliation_ai_v3_ai_issues.md) | Tracker-ready issue backlog — all 20 issues with owners (P1–P4), blockers, acceptance criteria, and dependency graph. | ✅ Ready to import |
| [`reconciliation_ai_work_split.md`](reconciliation_ai_work_split.md) | Four-person relay plan — work packages, contracts, handoffs, and exit gates per stage. | ✅ Current |
| [`Reconcilation AI Indradhanu PPT (1).pdf`](Reconcilation%20AI%20Indradhanu%20PPT%20(1).pdf) | Pitch deck — presentation reference. | 📎 Reference |

---

## 🏗️ System Architecture (Prototype)

```
DATA LAYER (Pre-loaded)
├── Sentinel-2 GeoTIFF files → local disk
├── IMD + GPM rainfall data → PostgreSQL
├── SRTM + OSM + MKVDC GIS layers → PostGIS
└── Representative SDRF assessment records → PostgreSQL

FASTAPI BACKEND — synchronous pipeline per analysis request
├── Step 1: Satellite module    → Siamese CNN inference (NDVI/NDWI/SAR)
├── Step 2: Rainfall module     → Feature extraction + damage scoring
├── Step 3: NLP module          → IndicBERT inference (Marathi/Hindi)
├── Step 4: Infra module        → PostGIS spatial queries + risk scoring
├── Step 5: Evidence aggregation→ Weighted ensemble (0.35/0.25/0.20/0.20)
├── Step 6: Mismatch engine     → Delta + tiered classification
├── Step 7: Root cause          → Random Forest + SHAP values
├── Step 8: Confidence scoring  → 4-component formula
└── Step 9: Report generation   → Gemini 1.5 Flash API call

REACT FRONTEND DASHBOARD
├── Maharashtra Leaflet map with colour-coded farm markers
├── Evidence radar chart (5 axes)
├── NDVI timeline with CUSUM change point annotation
├── Root cause probability bars (SHAP-backed)
└── Full report viewer + PDF download
```

---

## 📊 ML Models Summary

| # | Model | Task | Performance |
|---|---|---|---|
| 1 | **Siamese CNN** (PyTorch) | Satellite crop damage from bi-temporal image pairs | AUC-ROC 0.91 · F1 0.83 |
| 2 | **IndicBERT** (HuggingFace) | Marathi/Hindi severity classification + NER | Marathi Acc 78.4% · Hindi Acc 82.1% |
| 3 | **ResNet-50** (torchvision) | Flood photo content verification | Fine-tuned on 3,200 NDMA images |
| 4 | **Random Forest** (scikit-learn) | Multi-label root cause + SHAP explainability | Macro AUC-ROC 0.87 · Hamming Loss 0.14 |
| 5 | **Gemini 1.5 Flash** (Google AI) | Plain-language report narrative generation | Free tier · 1,500 req/day |

> All metrics on representative dataset. Numbers tagged 🧪 synthetic / 🎯 target must retain those qualifications in demo material.

---

## 🚀 Getting Started (Development)

### Prerequisites
```
Python 3.11+
Node.js 20+
PostgreSQL 15 with PostGIS 3.4 extension
```

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # Add your GEMINI_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
```bash
psql -U postgres -c "CREATE DATABASE reconciliation_ai;"
psql -U postgres -d reconciliation_ai -c "CREATE EXTENSION postgis;"
psql -U postgres -d reconciliation_ai -f db/schema.sql
psql -U postgres -d reconciliation_ai -f db/seed.sql
```

---

## 📋 Issue Workflow

Issues use local IDs from [`reconciliation_ai_v3_ai_issues.md`](reconciliation_ai_v3_ai_issues.md):

- **`P1-xx`** — Data Foundation & Satellite Evidence
- **`P2-xx`** — Ground Evidence & Farmer PWA
- **`P3-xx`** — Decision Engine, Audit & Reports
- **`P4-xx`** — Officer Dashboard, Benchmark & Demo
- **`X-xx`** — Cross-owner / governance

**Before starting any issue:** check its `Blocked by` list. Do not start implementation if any blocker is not `Done/Closed`. See Section 3 of the backlog file for the full blocker-check protocol.

### Execution Order
```
X-01 → X-02 → P1-01              (freeze contracts)
P1-02 → P1-03 → P1-04/P1-05 → P1-06    (Stage 1: Data + Satellite)
P2-01 → P2-02 → P2-03 → P2-04 → P2-05  (Stage 2: Ground Evidence)
P3-01 → P3-02 → P3-03 → P3-04 → P3-05 → P3-06  (Stage 3: Engine)
P4-01 → P4-02 → P4-03 → P4-04          (Stage 4: Dashboard + Demo)
```

---

## ⚖️ Ethical Constraints (Hard Limits)

- ❌ System **cannot write to** the official government assessment database
- ❌ System **cannot communicate** compensation outcomes to farmers
- ✅ Every prediction has a **mandatory confidence score** — uncertainty is never hidden
- ✅ All AI decisions are written to an **immutable audit log**
- ✅ SHAP values make every root cause prediction **fully explainable**
- ✅ Farmer Aadhaar never collected · Bank details AES-256 encrypted · EXIF stripped after verification

---

## 🔶 Deferred to 24-Hour Hackathon

| Feature | Plan |
|---|---|
| Redis (cache + queue) | Add as Celery broker for async satellite jobs at scale |
| MinIO (object storage) | Replace local disk with S3-compatible object store |
| Live GEE API calls | Replace pre-fetched satellite data with live API per farm |
| Live IMD/GPM API | Real-time rainfall fetch |
| MahaBhumi 7/12 API | Live farm ownership verification |
| Marathi voice-to-text | Whisper / Vakyansh speech input |
| SMS/Email alerts | Twilio alerts to district officers on critical mismatch |
| Docker Compose | Reproducible containerised deployment |

---

*PCCOE Indradhanu · Reconciliation AI · Prototype Round · November 2026*
