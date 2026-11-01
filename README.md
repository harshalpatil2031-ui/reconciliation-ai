# 🌾 Reconciliation AI — Maharashtra Flood Compensation QA

> **Team:** PCCOE Indradhanu · **Stage:** Prototype Round 2 → 24-Hour Hackathon  
> **Domain:** AI for Social Good · Disaster Management · AgriTech

An evidence-led, human-reviewed quality-assurance system for reconciling crop-loss compensation assessments with satellite imagery, rainfall data, and verified ground evidence from farmers.

> ⚠️ **The system is advisory only.** It helps officers prioritize review. It does not approve or deny compensation.

---

## 📂 Repository Structure

```
reconciliation-ai/
├── IMPLEMENTATION.md     ← Full technical spec (ML models, APIs, architecture)
├── ISSUES.md             ← All 26 backlog issues with owners, blockers, acceptance criteria
├── README.md             ← This file
└── .github/
    └── ISSUE_TEMPLATE/   ← GitHub issue templates
```

---

## 📋 Key Documents

| File | What it contains |
|---|---|
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | Tech stack, ML model architectures, data sources, API design, dashboard spec, end-to-end example |
| [`ISSUES.md`](ISSUES.md) | All 26 backlog issues (X-01→X-05, P1-01→P1-06, P2-01→P2-05, P3-01→P3-06, P4-01→P4-04) with blockers and dependency graph |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js 18 + Vite · Leaflet.js · Recharts |
| **Backend** | FastAPI (Python) |
| **Database** | PostgreSQL 15 + PostGIS 3.4 |
| **ML — Satellite** | PyTorch Siamese CNN · Sentinel-2 NDVI/NDWI · Sentinel-1 SAR |
| **ML — NLP** | IndicBERT fine-tuned for Marathi/Hindi |
| **ML — Photo** | torchvision ResNet-50 |
| **ML — Root Cause** | scikit-learn Random Forest + SHAP |
| **Report Generation** | Gemini 1.5 Flash (free tier) |

---

## 🚀 Implementation Order

```
X-01 → X-02 → P1-01           ← Freeze contracts first
P1-02 → P1-03 → P1-04/05 → P1-06    ← Stage 1: Data + Satellite (P1)
P2-01 → P2-02/03/04 → P2-05         ← Stage 2: Ground Evidence (P2)
P3-01 → P3-02/03/04/05 → P3-06      ← Stage 3: Decision Engine (P3)
P4-01 → P4-02/03 → P4-04            ← Stage 4: Dashboard + Demo (P4)
```

> Start at [Issues #1](https://github.com/harshalpatil2031-ui/reconciliation-ai/issues/1). Everything is blocked by X-01.

---

## ⚖️ Hard Constraints

- ❌ Cannot write to government assessment database
- ❌ Cannot communicate compensation outcomes to farmers  
- ✅ Every prediction has a mandatory confidence/evidence grade
- ✅ Immutable audit log for all AI decisions
- ✅ No Aadhaar collected · EXIF stripped · AES-256 on bank details

---

*PCCOE Indradhanu · Reconciliation AI · November 2026*
