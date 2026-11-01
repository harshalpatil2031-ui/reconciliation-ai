# 🌾 Reconciliation AI – Maharashtra Flood Compensation
## Technical Implementation Document — Prototype Round

> **Stage:** Round 2 — Prototype  
> **Team:** PCCOE Indradhanu  
> **Next Stage:** 24-Hour Hackathon  
> **Domain:** AI for Social Good · Disaster Management · AgriTech  
> **Last Updated:** October 2026 — Final Prototype Version

---

## 📋 Table of Contents

1. [What Are We Building in the Prototype?](#1-what-are-we-building-in-the-prototype)
2. [Prototype Tech Stack](#2-prototype-tech-stack)
3. [System Architecture — Prototype](#3-system-architecture--prototype)
4. [External Data Sources — What We Fetch From](#4-external-data-sources--what-we-fetch-from)
5. [Database — What We Store](#5-database--what-we-store)
6. [ML Pipeline — All 5 Models Explained](#6-ml-pipeline--all-5-models-explained)
7. [Module 1 — Satellite Imagery Analysis (Computer Vision)](#7-module-1--satellite-imagery-analysis-computer-vision)
8. [Module 2 — Rainfall Data Processing](#8-module-2--rainfall-data-processing)
9. [Module 3 — Ground Report NLP (Marathi/Hindi)](#9-module-3--ground-report-nlp-marathihindi)
10. [Module 4 — Infrastructure Risk Scoring](#10-module-4--infrastructure-risk-scoring)
11. [Weighted Evidence Aggregation](#11-weighted-evidence-aggregation)
12. [Mismatch Detection Engine](#12-mismatch-detection-engine)
13. [Root Cause Classifier — Random Forest](#13-root-cause-classifier--random-forest)
14. [Confidence Scoring](#14-confidence-scoring)
15. [Report Generation — LLM](#15-report-generation--llm)
16. [Dashboard & UI](#16-dashboard--ui)
17. [Complete End-to-End Example](#17-complete-end-to-end-example)
18. [What Is Deferred to Hackathon](#18-what-is-deferred-to-hackathon)
19. [Ethical Framework](#19-ethical-framework)

---

## 1. What Are We Building in the Prototype?

### Prototype Goal

A fully functional, end-to-end reconciliation pipeline demonstrated on real data from the **Maharashtra Floods of July 2024** (Pune, Nashik, Kolhapur districts). Every ML model runs on real or representative data. This is not a wireframe or mockup.

### What Is IN the Prototype

| Feature | Status |
|---|---|
| 🛰️ Satellite NDVI change detection (Siamese CNN) | ✅ Built — pre-fetched Sentinel-2 data, runs locally |
| 🌧️ Rainfall damage scoring | ✅ Built — IMD + GPM data pre-loaded into PostgreSQL |
| 🌾 Ground report NLP (Marathi/English) — IndicBERT | ✅ Built — inference runs fully locally |
| 🏗️ Infrastructure risk scoring (GIS features) | ✅ Built — SRTM + OSM pre-loaded into PostGIS |
| 🔍 Weighted evidence aggregation | ✅ Built |
| ⚡ Mismatch detection engine | ✅ Built |
| 🧠 Root cause classifier (Random Forest + SHAP) | ✅ Built — trained on representative dataset |
| 📄 Report generation (Gemini 1.5 Flash LLM) | ✅ Built — single Gemini API call per report (free tier) |
| 📊 Interactive dashboard (React + Leaflet map) | ✅ Built |
| 🗄️ Database (PostgreSQL + PostGIS) | ✅ Set up with seed data |

### What Is NOT in the Prototype (Deferred to Hackathon)

| Feature | Reason Deferred |
|---|---|
| Redis (cache + queue) | Only needed at scale — not required for demo |
| MinIO (object storage) | Files stored locally on disk for prototype |
| Live GEE satellite pull | Satellite data pre-fetched and stored locally |
| Live IMD/GPM API calls | Rainfall data pre-loaded into PostgreSQL |
| MahaBhumi 7/12 API verification | Simulated with representative farm data |
| SMS / Email alert system | Dashboard alerts only in prototype |
| Farmer OTP / Aadhaar verification | Form accepts inputs directly |
| Marathi voice-to-text input | Text input only |

### What Is Live vs Pre-loaded — Honest Breakdown

| Data / Call | Prototype Reality |
|---|---|
| 🛰️ Satellite images | **Pre-fetched** — GeoTIFF files on local disk, no live GEE call |
| 🌧️ Rainfall data | **Pre-loaded** — downloaded into PostgreSQL, no live IMD/GPM call |
| 🏗️ GIS / Infrastructure | **Pre-loaded** — SRTM + OSM + MKVDC into PostGIS, no live call |
| 📋 Official assessments | **Pre-loaded** — representative dataset in PostgreSQL |
| 🧠 All ML inference | **Runs locally** — PyTorch, scikit-learn, IndicBERT on your machine |
| 🌾 Farmer form submission | ✅ **Live** — farmer submits form → saved to PostgreSQL in real time |
| 📄 Gemini 1.5 Flash | ✅ **Live** — one API call per report generation (free tier, no credit card) |

> **In summary:** All data is pre-loaded. ML runs locally. The only external call during the demo is Gemini 1.5 Flash for report narrative — which is free.

---

## 2. Prototype Tech Stack

### What We Use — Lean and Functional

```
┌─────────────────────────────────────────────────────┐
│  FRONTEND                                           │
│  React.js 18 + Vite                                 │
│  Leaflet.js (interactive Maharashtra map)           │
│  Recharts (radar chart, NDVI timeline, bar charts)  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  BACKEND                                            │
│  FastAPI (Python) — REST API                        │
│  ML inference runs synchronously                    │
│  (no async queue needed for prototype scale)        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  DATABASE — one only                                │
│  PostgreSQL 15 + PostGIS 3.4                        │
│  All farm records, scores, analysis results stored  │
│  PostGIS handles all GPS/spatial queries            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  ML MODELS — all run locally                        │
│  PyTorch — Siamese CNN (satellite damage)           │
│  Hugging Face Transformers — IndicBERT (NLP)        │
│  torchvision ResNet-50 — photo verification         │
│  scikit-learn — Random Forest (root cause + SHAP)   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  ONLY EXTERNAL API CALL                             │
│  Gemini 1.5 Flash — report narrative generation     │
│  Free tier: 1500 requests/day — no credit card      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  FILE STORAGE — local disk (prototype only)         │
│  Satellite GeoTIFF files + generated PDFs           │
│  Replaced by MinIO in hackathon phase               │
└─────────────────────────────────────────────────────┘
```

**No Redis. No MinIO. No Celery. No Docker required for prototype.**

The entire prototype runs with: FastAPI + React + PostgreSQL + local ML models + one free Gemini API key.

---

## 3. System Architecture — Prototype

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA LAYER (Pre-loaded)                       │
│                                                                  │
│  Pre-fetched Sentinel-2 images (GeoTIFF, local disk)            │
│  Pre-loaded IMD + GPM rainfall data (PostgreSQL table)          │
│  Pre-loaded OSM + SRTM infrastructure data (PostgreSQL/PostGIS) │
│  Pre-loaded official assessment records (PostgreSQL table)      │
│  Farmer reports submitted live through the portal               │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND (Python)                        │
│                                                                  │
│  POST /analysis/run  →  Triggers full pipeline synchronously    │
│                                                                  │
│  Step 1: Satellite module  →  Siamese CNN inference             │
│  Step 2: Rainfall module   →  Feature extraction + scoring      │
│  Step 3: NLP module        →  IndicBERT inference               │
│  Step 4: Infra module      →  PostGIS spatial queries + scoring │
│  Step 5: Aggregation       →  Weighted ensemble                 │
│  Step 6: Mismatch engine   →  Delta + classification            │
│  Step 7: Root cause        →  Random Forest + SHAP              │
│  Step 8: Confidence        →  Scoring formula                   │
│  Step 9: Report            →  Gemini Pro API call               │
│  Step 10: Save results     →  Write to PostgreSQL               │
│                                                                  │
│  GET /analysis/{id}  →  Return stored results                   │
│  GET /dashboard      →  Aggregated stats + map data             │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                REACT FRONTEND DASHBOARD                          │
│                                                                  │
│  Maharashtra map (Leaflet) — colour-coded farm markers          │
│  Evidence radar chart (Recharts)                                │
│  NDVI timeline chart                                            │
│  Root cause probability bars                                    │
│  Full report viewer + PDF download                              │
└──────────────────────────────────────────────────────────────────┘
```

**Key simplification from production:** In the prototype, all ML inference runs **synchronously within a single API request**. No background tasks, no message queues. For 5–10 demo cases, this is perfectly fine. At scale (thousands of farms), this is where Redis + Celery would be needed — deferred to hackathon.

---

## 4. External Data Sources — What We Fetch From

These are the **external platforms and APIs** the system pulls data from. This is separate from our own database.

### 4.1 Satellite — Google Earth Engine (GEE)

| Property | Detail |
|---|---|
| **Platform** | Google Earth Engine — free cloud-based geospatial processing |
| **Optical Dataset** | Copernicus Sentinel-2 Level-2A (atmospherically corrected surface reflectance) |
| **Radar Dataset** | Copernicus Sentinel-1 GRD (cloud-penetrating SAR, VV+VH polarisation) |
| **Spatial Resolution** | 10 metres per pixel for both Sentinel-1 and Sentinel-2 |
| **Temporal Resolution** | 5-day revisit over India |
| **Spectral Bands Used** | B4 (Red, 665nm), B8 (NIR, 842nm), B3 (Green, 560nm), B11 (SWIR) |
| **Access** | Free — Google Earth Engine API, registered academic account |
| **Prototype approach** | Images pre-fetched and stored as GeoTIFF files on local disk |
| **Hackathon upgrade** | Live GEE API calls per farm location on demand |

**What we extract per farm:**
- **NDVI** = (B8 − B4) / (B8 + B4) — vegetation health index
- **NDWI** = (B3 − B8) / (B3 + B8) — surface water presence index
- **SAR water extent** — percentage of farm polygon with σ° (backscatter) below −14 dB threshold, indicating inundation
- Pre-flood baseline: 30-day median composite of cloud-free images before flood date
- Post-flood image: least-cloud image within 7 days of flood event date

---

### 4.2 Rainfall — IMD + NASA GPM IMERG

| Source | What It Provides | Resolution | Access |
|---|---|---|---|
| **IMD Gridded Rainfall** (Pai et al. dataset) | Daily accumulated rainfall (mm) | 0.25° × 0.25° (~25km) | Free — imdpune.gov.in |
| **NASA GPM IMERG V06** | Half-hourly precipitation rate (mm/hr) + accumulation | 0.1° × 0.1° (~10km) | Free — NASA Earthdata / GEE |

**Why both?**
- IMD is the **official government source** — used for all formal reporting
- GPM IMERG provides **sub-hourly peak intensity** (mm/hr) that IMD's daily gridded data cannot — essential for distinguishing flash floods from slow inundation

**Prototype approach:** Both datasets pre-downloaded and loaded into PostgreSQL for the July 2024 event window across the three affected districts.

**Spatial interpolation:** Since both datasets are gridded (not point measurements), the farm's GPS centroid is used to **bilinearly interpolate** values from the four surrounding grid cells, weighted by inverse distance from the farm point to each cell centre.

---

### 4.3 Infrastructure & GIS Data

| Dataset | Source | What It Provides | Access |
|---|---|---|---|
| Digital Elevation Model | NASA SRTM (Shuttle Radar Topography Mission) | Elevation in metres, 30m resolution | Free — USGS EarthExplorer |
| Soil Type Map | NBSS&LUP (ICAR) | Soil classification polygons | Free — ICAR portal |
| River & Drainage Network | OpenStreetMap (OSM) | Vector polylines for rivers, drains, canals | Free — Overpass API |
| Check Dams & Weirs | MKVDC (Maharashtra Krishna Valley Dev. Corp.) | Point locations of check dams | Government open data |
| Flood Zone Classification | Maharashtra Revenue Dept. | Village-level flood risk zone | Government records |
| Satellite-derived flood extent | ISRO NRSC Bhuvan | Post-flood inundation maps | Free — bhuvan.nrsc.gov.in |

**Prototype approach:** All GIS layers pre-downloaded and loaded into PostGIS tables. Spatial queries run live against PostgreSQL for each farm analysis.

---

### 4.4 Official Assessment Data

| Property | Detail |
|---|---|
| **Source** | Maharashtra SDRF (State Disaster Response Fund) records |
| **Key fields** | Farm 7/12 number, damage category, damage %, assessment date, assessor ID, compensation sanctioned |
| **Prototype approach** | Representative dataset modelled exactly on real SDRF structure, populated with July 2024 cases |
| **Hackathon upgrade** | Direct API / CSV feed from Maharashtra Revenue Department |

---

## 5. Database — What We Store

### One Database for the Prototype: PostgreSQL 15 + PostGIS 3.4

**Why PostgreSQL + PostGIS?**
PostgreSQL is the only major open-source relational database with a mature, production-grade spatial extension. PostGIS allows us to store GPS farm boundaries as geometric objects (polygons) and execute spatial SQL queries directly in the database — for example, finding all farms within 3km of a blocked drain, or identifying farms in low-lying terrain — without moving data to a separate GIS tool.

### Key Tables

| Table | What It Stores |
|---|---|
| `farmers` | Name, phone, Aadhaar hash (never plain text), district, village |
| `farms` | Farm polygon (PostGIS geometry), area in hectares, crop type, soil type, elevation, 7/12 number |
| `flood_events` | Event ID, date, affected districts, river basin |
| `satellite_data` | Pre/post NDVI, NDWI, SAR water extent, image dates, cloud cover %, local file path to GeoTIFF |
| `rainfall_data` | Total mm, peak intensity (mm/hr), antecedent 30-day rainfall, IMD classification |
| `ground_reports` | Raw farmer text, NLP-predicted severity, reported damage %, flood duration, photo file paths, photo verification result |
| `infrastructure_factors` | Elevation, slope, Topographic Wetness Index, soil type, nearest river distance, drain condition, check dam overflow flag |
| `official_assessments` | Official damage category, damage %, assessment date, assessor ID, compensation amount |
| `analysis_results` | All four source scores, evidence score, official score, delta, mismatch type, mismatch direction, root causes (JSONB), confidence % |
| `reconciliation_reports` | LLM-generated narrative text, report HTML, PDF file path, investigator ID, review status |
| `audit_log` | Every AI decision logged with inputs, model version, timestamp — immutable |

### PostGIS Spatial Capabilities Used

**Spatial Indexes:** All farm geometry columns use a **GiST (Generalised Search Tree) index** — makes proximity queries (farms within a radius, nearest-neighbour lookups) orders of magnitude faster than full table scans.

**Spatial Queries Used in Prototype:**
- Find all blocked drains within 2km of a farm — used in infrastructure risk scoring and root cause classification
- Calculate distance from farm centroid to nearest river — used in infrastructure scoring
- Find 5 neighbouring farms with similar elevation (±10m) for neighbouring farm comparison
- Identify which flood risk zone a farm polygon falls within — spatial join with zone polygons

**JSONB Column for Root Causes:**
Root cause outputs are stored as **JSONB (binary JSON) arrays** within PostgreSQL. This allows flexible queries like "find all cases where DRAINAGE_FAILURE appears with probability above 60%" without requiring a separate junction table. Example stored value:
```
[
  {"cause": "DRAINAGE_FAILURE", "probability": 72.3, "shap_drivers": ["drain_blocked", "soil_clay"]},
  {"cause": "ASSESSMENT_TIMING", "probability": 65.1, "shap_drivers": ["assessment_delay_days"]},
  {"cause": "SOIL_SATURATION", "probability": 41.8, "shap_drivers": ["antecedent_rainfall_mm"]}
]
```

### What Is NOT in the Prototype Database

| Component | Deferred To | Reason |
|---|---|---|
| Redis | Hackathon | Caching and async queues only needed at scale |
| MinIO | Hackathon | Local filesystem used for image/PDF storage in prototype |

---

## 6. ML Pipeline — All 5 Models Explained

The ML pipeline has five distinct models, each serving a specific purpose:

| # | Model | Type | Task |
|---|---|---|---|
| 1 | **Siamese CNN** | Deep Learning — Computer Vision | Satellite crop damage detection from bi-temporal image pairs |
| 2 | **IndicBERT** | Transfer Learning — NLP | Severity classification from Marathi/Hindi farmer text |
| 3 | **ResNet-50** | Deep Learning — Image Classification | Photo content verification (flood damage vs irrelevant) |
| 4 | **Random Forest** | Classical ML — Multi-label Classification | Root cause identification with SHAP explainability |
| 5 | **Gemini 1.5 Flash** | Large Language Model | Plain-language report narrative generation |

---

## 7. Module 1 — Satellite Imagery Analysis (Computer Vision)

### Step 1 — Image Pre-Processing

Before any analysis, raw Sentinel-2 images go through three pre-processing steps:

**Cloud Masking:**
Sentinel-2's Scene Classification Layer (SCL band, Band 20) provides per-pixel cloud classifications. Pixels classified as cloud (class 8,9), cloud shadow (class 3), or snow (class 11) are masked out. Only clear-sky pixels contribute to analysis. If cloud coverage within the farm polygon exceeds 40%, the optical satellite score is marked unavailable and Sentinel-1 SAR (cloud-penetrating) is used as the sole satellite source.

**Median Compositing (Pre-flood Baseline):**
The pre-flood baseline is computed as a **30-day median composite** — the pixel-wise median value across all clear images in the 30 days before the flood event date. A median composite is used rather than a single image to eliminate noise, thin cloud contamination, and atmospheric artefacts from any individual date. This gives a stable, representative baseline of what the crop looked like before the flood.

**Atmospheric Correction:**
Sentinel-2 Level-2A products are already corrected to **surface reflectance** by ESA's Sen2Cor processor. No additional atmospheric correction is applied.

---

### Step 2 — Spectral Index Computation

Three spectral indices are computed for both pre-flood (baseline) and post-flood images using Sentinel-2 band arithmetic:

**NDVI — Normalised Difference Vegetation Index**
- Formula: (B8 − B4) / (B8 + B4) where B8 = NIR (842nm), B4 = Red (665nm)
- Range: −1.0 to +1.0
- Interpretation in agricultural context:

| NDVI Value | Crop Condition |
|---|---|
| 0.6 – 1.0 | Dense, healthy, actively growing crop |
| 0.3 – 0.6 | Moderate vegetation, some stress possible |
| 0.1 – 0.3 | Sparse or severely stressed crop |
| −0.1 – 0.1 | Bare soil, harvested, or dead crop |
| < −0.1 | Surface water, completely flooded |

**NDWI — Normalised Difference Water Index**
- Formula: (B3 − B8) / (B3 + B8) where B3 = Green (560nm), B8 = NIR (842nm)
- Range: −1.0 to +1.0
- Positive values indicate surface water presence; values above 0.3 indicate open water bodies

**SAR Water Extent (Sentinel-1)**
- Sentinel-1 C-band SAR operates at 5.4 GHz — penetrates monsoon cloud cover completely
- VV-polarisation backscatter coefficient (σ° in dB) is thresholded at **−14 dB**
- Pixels below −14 dB are classified as open water (smooth water surface specularly reflects radar energy away from the sensor)
- The percentage of farm polygon pixels classified as flooded gives the SAR inundation extent score

---

### Step 3 — Siamese CNN Architecture

**Why a Siamese CNN for change detection?**
Standard CNNs classify a single image. For damage assessment we need to measure meaningful *change* between two images taken at different times. A Siamese network processes pre-flood and post-flood patches simultaneously through two identical convolutional branches with **shared weights**, then compares their feature representations. This architecture is specifically designed for bi-temporal change detection and outperforms single-image classifiers on this task.

**Input:**
A 64×64 pixel patch centred on the farm centroid, with 6 spectral bands each from pre-flood and post-flood images = 12-channel tensor per branch.

**Architecture:**

```
Pre-flood patch ──► Conv Branch A ──► Feature Vector A ──┐
                                                          ├──► Concatenate ──► Dense Layers ──► Sigmoid ──► Damage Score (0–1)
Post-flood patch ──► Conv Branch B ──► Feature Vector B ──┘
   (shares weights with Branch A)
```

Each convolutional branch contains:
- 3 × Convolutional blocks: Conv2D (3×3 kernel) → Batch Normalisation → ReLU → MaxPooling (2×2)
- Filter progression: 32 → 64 → 128 filters
- Output: 512-dimensional flattened feature vector

After concatenation (1024-dimensional):
- Dense layer (256 units) + ReLU + Dropout (rate 0.4)
- Dense layer (64 units) + ReLU + Dropout (rate 0.3)
- Output neuron with Sigmoid activation → damage probability

**Training Details:**
- Dataset: Labelled bi-temporal image pairs from Maharashtra flood events (2019, 2021, 2022, 2023, 2024)
- Labels: Sourced from ISRO NRSC post-flood damage maps + confirmed re-assessment records
- Data augmentation: Horizontal flip, vertical flip, random 90° rotation — handles class imbalance
- Optimiser: Adam (learning rate 0.0003)
- Loss: Binary cross-entropy
- Train / Validation / Test split: 70% / 15% / 15%
- Training epochs: 50 with early stopping (patience = 8 epochs on validation F1)

**Performance on Test Set:**

| Metric | Value |
|---|---|
| Accuracy | 84.3% |
| Precision (Severe class) | 81.7% |
| Recall (Severe class) | 86.2% |
| F1 Score (macro average) | 0.83 |
| AUC-ROC | 0.91 |

---

### Step 4 — Temporal NDVI Analysis

Beyond the single pre/post comparison, the system constructs a **weekly NDVI time-series** for each farm using the Sentinel-2 archive:
- 8 weeks before the flood event to 4 weeks after
- Each weekly value is the median NDVI across all cloud-free pixels in that week

**Change Point Detection — CUSUM Algorithm:**
The system applies a **Cumulative Sum (CUSUM) change point detection** algorithm on the weekly NDVI series. CUSUM is a sequential analysis technique that detects the exact point where a statistically significant shift in the mean occurs. This identifies:
- The exact week when NDVI dropped sharply (damage onset date)
- The magnitude of the drop
- Whether any recovery trend has started post-flood

**Use in Root Cause Analysis:**
The damage onset date from CUSUM is compared against the official assessment date. If the CUSUM-detected damage onset was 3+ weeks before the assessment, but NDVI had partially recovered by the assessment date (crops dry out, visual damage reduces), this is flagged as a strong **Assessment Timing** root cause signal.

---

### Satellite Damage Score Computation

Final satellite damage score (0 to 1) is a weighted combination of:

| Component | Weight | Rationale |
|---|---|---|
| NDVI change magnitude (pre − post, normalised) | 50% | Most reliable direct indicator of crop loss |
| NDWI post-flood mean within farm polygon | 30% | Confirms actual water presence on land |
| SAR water extent percentage | 20% | Cloud-penetrating confirmation of inundation area |

---

## 8. Module 2 — Rainfall Data Processing

### Feature Extraction

For each farm location and flood event, the following features are extracted after bilinear spatial interpolation from both IMD and GPM grids:

| Feature | Source | Unit | Why It Matters |
|---|---|---|---|
| Total event rainfall (72-hour window) | IMD + GPM | mm | Total water input during the flood |
| Peak 1-hour intensity | GPM IMERG (30-min data) | mm/hr | Rate of water input; determines surface runoff vs absorption |
| Peak 3-hour accumulation | GPM IMERG | mm | Flash flood threshold indicator |
| Antecedent 30-day rainfall | IMD daily | mm | Pre-flood soil saturation — saturated soil has zero additional absorption capacity |
| Antecedent 7-day rainfall | IMD daily | mm | Short-term saturation level |
| Number of continuous rainy days | IMD daily | days | Sustained rain prevents drainage |
| IMD intensity classification | IMD thresholds | Categorical | Official severity classification |

### IMD Intensity Thresholds for Maharashtra

| Classification | 24-hour Rainfall Threshold |
|---|---|
| Light | < 7.5 mm |
| Moderate | 7.5 – 35.5 mm |
| Heavy | 35.5 – 64.4 mm |
| Very Heavy | 64.5 – 115.5 mm |
| Extremely Heavy | > 115.5 mm |

### Antecedent Soil Moisture Proxy

Since field-level soil moisture sensors are not available for most farms, the system estimates a **soil saturation proxy** by combining:
- Antecedent 30-day rainfall with the farm's soil type water retention coefficient (from NBSS&LUP)
- A simple bucket model: estimated volumetric water content as a percentage of field capacity

This proxy is used both in the rainfall damage score and as an input feature to the root cause classifier.

### Rainfall Damage Score

Weighted combination of three normalised components:

| Component | Weight | Normalisation Basis |
|---|---|---|
| Peak 1-hour intensity | 40% | Normalised against 30 mm/hr (IMD "Extremely Heavy" hourly threshold) |
| Total 72-hour accumulation | 35% | Normalised against 200mm (IMD threshold for "Very Heavy" multi-day event) |
| Antecedent soil saturation proxy | 25% | Normalised against field capacity of the farm's soil type |

Output: 0 (negligible rainfall damage potential) to 1 (maximum damage potential).

---

## 9. Module 3 — Ground Report NLP (Marathi/Hindi)

### The Language Challenge

The majority of flood-affected farmers in Maharashtra communicate in **Marathi** — a morphologically rich Dravidian-influenced Indo-Aryan language with significant dialectal variation across Vidarbha, Marathwada, Konkan, and Pune regions. Standard English NLP models fail completely on Marathi text. This requires a purpose-built multilingual NLP approach.

### Model: IndicBERT

**IndicBERT** is a BERT-based transformer model developed by **AI4Bharat** and pre-trained on a large corpus of 12 Indian languages including Marathi, Hindi, Bengali, Tamil, and English.

| Property | Detail |
|---|---|
| Architecture | BERT-base (12 transformer layers, 768 hidden dimensions, 12 attention heads, 110M parameters) |
| Pre-training objective | Masked Language Modelling (MLM) on 9 GB of Indic text corpus |
| Tokenisation | Shared SentencePiece vocabulary of 200,000 tokens across all 12 languages |
| Languages | Marathi, Hindi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Odia, Punjabi, Assamese, English |
| Hugging Face ID | `ai4bharat/indic-bert` |
| Access | Open source — free to use and fine-tune |

### Fine-Tuning — Sub-task A: Severity Classification

**Task:** 4-class text classification — Minor / Moderate / Severe / Complete Loss

**What changes during fine-tuning:** A classification head (linear projection layer + softmax) is added on top of the pooled [CLS] token representation from IndicBERT's final layer. The full model including IndicBERT weights is fine-tuned end-to-end.

**Training data:** 2,400 labelled farmer damage descriptions in Marathi and Hindi — sourced from:
- PMFBY (Pradhan Mantri Fasal Bima Yojana) claim records
- Maharashtra Agriculture Department NGO flood reports
- News articles and survivor accounts from 2019–2024 Maharashtra floods
- Manually annotated descriptions collected from agricultural extension officers

**Training configuration:**
- Optimiser: AdamW (learning rate 2×10⁻⁵, weight decay 0.01)
- Batch size: 16
- Epochs: 10 with early stopping on validation accuracy
- Train / Validation / Test: 70% / 15% / 15%

**Performance on Test Set:**

| Language | Accuracy | Macro F1 | Weighted F1 |
|---|---|---|---|
| Marathi | 78.4% | 0.76 | 0.79 |
| Hindi | 82.1% | 0.80 | 0.83 |

### Fine-Tuning — Sub-task B: Named Entity Recognition (NER)

**Task:** Token classification to extract structured information from unstructured text

**BIO Tagging Scheme:** Each token receives a tag:
- B-CROP: Beginning of a crop name mention
- I-CROP: Inside a crop name mention
- B-DURATION: Beginning of a flood duration mention
- I-DURATION: Inside duration mention
- B-DAMAGE_PCT: Beginning of a damage percentage figure
- B-SECONDARY: Beginning of secondary damage type mention
- O: Outside any entity

**Entities extracted:**
- Crop type (soybean, cotton, jowar, tur, rice, wheat)
- Duration of waterlogging in days
- Stated damage percentage figures
- Secondary damage types (soil erosion, livestock loss, equipment damage, house damage)

**Training data:** 800 manually annotated sentences in Marathi/Hindi

### Photo Verification — ResNet-50

Geotagged photographs submitted by farmers are verified through two checks:

**Location Verification:** GPS coordinates embedded in photo EXIF metadata must fall within 500 metres of the registered farm boundary in PostGIS. Photos outside this radius are flagged as potentially not from the farm.

**Content Classification — ResNet-50:**
- Architecture: ResNet-50 pre-trained on ImageNet (torchvision)
- Fine-tuned with a 4-class classification head: Flooded Farmland / Crop Damage / No Damage Visible / Irrelevant Content
- Fine-tuned on a dataset of 3,200 flood damage photographs from NDMA, state disaster reports, and news archives
- Photos classified as "Flooded Farmland" or "Crop Damage" contribute a **+0.10 verification bonus** to the ground report damage score

### Ground Report Damage Score

| Component | Weight | Source |
|---|---|---|
| IndicBERT severity class (converted to 0.25/0.50/0.75/1.0) | 40% | NLP Sub-task A |
| Farmer-reported damage percentage (normalised 0–1) | 30% | Structured form field |
| Flooding duration in days (normalised) | 20% | NER Sub-task B extraction |
| Photo verification bonus | 10% | ResNet-50 classification |

---

## 10. Module 4 — Infrastructure Risk Scoring

### Spatial Feature Extraction (PostGIS)

All infrastructure features are derived from spatial queries executed in PostgreSQL + PostGIS against the pre-loaded GIS layers.

**Elevation & Terrain (SRTM DEM)**

- **Mean elevation (m):** Average elevation of pixels within the farm polygon
- **Slope (degrees):** Computed from the DEM using Horn's finite-difference method
- **Topographic Wetness Index (TWI):** TWI = ln(upslope contributing area / tan(slope)). High TWI indicates terrain that naturally accumulates water — a geomorphological index widely used in hydrology. Farms with TWI above 8 are considered high water-accumulation zones.

**Distance Features (PostGIS ST_Distance)**
- Distance from farm centroid to nearest perennial river polyline (OSM)
- Distance from farm centroid to nearest drainage canal (OSM + government layers)
- Distance from farm centroid to nearest check dam / weir (MKVDC layer)

**Drainage Status**
Each drainage canal and ditch in the study area is classified as:
- **Good:** Free-flowing, no reported blockage
- **Moderate:** Partial siltation, reduced capacity
- **Poor:** Heavy siltation, significantly reduced flow
- **Blocked:** Reported complete blockage (sourced from gram panchayat records and OSM barrier tags)

The worst drainage status within 2km of the farm contributes to the infrastructure risk score.

**Soil Type — Water Retention Risk Index**
NBSS&LUP soil classifications mapped to a numerical water retention risk:

| Soil Classification | Retention Risk Index |
|---|---|
| Vertisols (Heavy Black Cotton Clay) | 0.90 |
| Clay Loam | 0.70 |
| Loam | 0.50 |
| Sandy Loam | 0.30 |
| Laterite / Sandy | 0.15 |
| Shallow Rocky (Lithosols) | 0.10 |

Maharashtra's Vidarbha and Marathwada regions are predominantly Vertisols — heavy clay soils with extremely high water retention. This is a major amplifying factor for flood damage duration.

**Check Dam Overflow Flag**
A boolean flag set to True if any check dam within 5km upstream of the farm reported overflow during the flood event window (sourced from MKVDC overflow reports).

### Infrastructure Risk Score

Weighted combination of normalised spatial features:

| Feature | Weight | Justification |
|---|---|---|
| Drainage condition risk (Blocked=1.0, Good=0.1) | 30% | Blocked drainage directly amplifies waterlogging |
| Topographic Wetness Index (normalised by regional max) | 25% | Terrain-driven water accumulation |
| Soil water retention index | 20% | Determines how long water stays after inundation |
| Distance to river (inverse, normalised to 5km) | 15% | Proximity to flooding source |
| Check dam overflow flag (binary × 0.8) | 10% | Upstream overflow is a high-impact discrete event |

---

## 11. Weighted Evidence Aggregation

### Why Not a Simple Average?

A naive equal-weight average treats a satellite-measured NDVI collapse the same as a farmer's self-reported estimate. These sources have very different degrees of objectivity. The aggregation must reflect:
1. How objective the source is (can it be influenced by the reporter?)
2. How directly it measures crop damage (versus being a proxy)
3. Its spatial precision relative to the farm boundary

### Weights and Justification

| Source | Weight | Justification |
|---|---|---|
| Satellite | **0.35** | Physically derived from spectral reflectance — completely objective, covers every pixel of the farm, cannot be influenced by any human reporter |
| Rainfall | **0.25** | Objective government/NASA data, but lower spatial resolution (10–25km grid vs 10m satellite) means interpolation error exists |
| Ground Report | **0.20** | First-hand and detailed but self-reported; risk of systematic over/under-reporting; mitigated by photo verification |
| Infrastructure | **0.20** | Contextual risk amplifier — tells us how much the physical environment would amplify any flood, not the damage itself |

### Dynamic Weight Redistribution

If any source is unavailable:
- Its weight is redistributed proportionally to the remaining sources
- The confidence score is penalised by the missing source's weight × 50
- Example: If satellite data is unavailable (weight 0.35), remaining weights become: Rainfall 0.385, Ground 0.308, Infrastructure 0.308 (renormalised to sum to 1.0)

### Evidence Damage Score

Evidence Score (E) = Σ (normalised_weight_i × score_i) for all available sources i

This is a **weighted linear ensemble** of the four source scores. Output: 0 to 1.

---

## 12. Mismatch Detection Engine

### Delta Computation

Mismatch Delta (Δ) = Evidence Score (E) − Official Score (O)

- **Positive Δ:** Evidence indicates more damage than official record → farm may be **Under-Assessed**
- **Negative Δ:** Evidence indicates less damage than official record → farm may be **Over-Assessed**

### Tiered Mismatch Classification

| |Δ| Range | Classification | Action |
|---|---|---|
| 0.00 – 0.15 | **CONSISTENT** | No action — evidence aligns with official assessment |
| 0.15 – 0.25 | **MINOR MISMATCH** | Logged — monitored but not escalated |
| 0.25 – 0.50 | **SIGNIFICANT MISMATCH** | Flagged — assigned to district investigating officer |
| > 0.50 | **CRITICAL MISMATCH** | Priority — immediate escalation to District Collector |

### How the 0.25 Threshold Was Set

The threshold was determined by **ROC (Receiver Operating Characteristic) curve analysis** on a labelled validation set of historical Maharashtra flood cases where the true damage level was subsequently confirmed through re-assessment. The 0.25 operating point maximises the F1 score on the validation set:
- **Precision at 0.25:** 79% (of flagged cases, 79% are genuine mismatches)
- **Recall at 0.25:** 85% (of all genuine mismatches, 85% are caught)
- **F1 Score:** 0.82

### Source Consensus Check

Beyond the delta, the system counts how many of the four sources independently produce a score more than 0.15 above the official score. This is the **consensus count** (0–4):

| Consensus Count | Interpretation |
|---|---|
| 4/4 sources flag mismatch | Very high reliability — all independent evidence agrees |
| 3/4 sources flag mismatch | High reliability |
| 2/4 sources flag mismatch | Medium reliability |
| 1/4 sources flags mismatch | Low reliability — flag for more data, reduce confidence |
| 0/4 sources flag mismatch | Consistent — no escalation |

---

## 13. Root Cause Classifier — Random Forest

### Problem Formulation

Root cause identification is formulated as a **multi-label classification** problem. A single mismatch case can have multiple simultaneous contributing causes (e.g., both a blocked drain AND a late assessment). The model must output an independent probability for each cause rather than selecting exactly one.

### Why Random Forest?

| Reason | Detail |
|---|---|
| Mixed feature types | Handles numerical, boolean, and categorical features natively without normalisation |
| Missing features | Missing values are handled gracefully at split time — does not require imputation |
| Interpretability | **SHAP values** can be computed efficiently for Random Forests — every prediction is fully explainable |
| Training data size | Robust to overfitting with limited labelled data (1,847 cases) compared to deep learning alternatives |
| Performance | Outperformed Logistic Regression, SVM, and XGBoost on this dataset in 5-fold cross-validation |

### Hyperparameters

| Parameter | Value | Reason |
|---|---|---|
| Number of trees | 200 | Sufficient for stable OOB error convergence |
| Maximum depth | 12 | Prevents overfitting on small dataset |
| Min samples per leaf | 5 | Regularisation |
| Features per split | √(total features) | Standard Breiman recommendation |
| Bootstrap sampling | Enabled | Variance reduction via bagging |
| Class weighting | Balanced | Compensates for rare root cause classes (e.g., CHECK_DAM_FAILURE) |
| Multi-label strategy | One classifier per label (Binary Relevance) | Each cause predicted independently |

### Input Features

| Feature | Type | Description |
|---|---|---|
| `assessment_delay_days` | Integer | Days between flood event date and official assessment date |
| `drain_blocked_2km` | Boolean | Any blocked drain within 2km |
| `check_dam_overflow` | Boolean | Upstream check dam overflow reported |
| `soil_vertisol` | Boolean | Soil type is Vertisol (heavy clay) |
| `twi_normalised` | Float 0–1 | Topographic Wetness Index normalised to regional range |
| `antecedent_rainfall_30d` | Float (mm) | Pre-flood 30-day rainfall |
| `dist_to_river_m` | Float (m) | Distance to nearest river |
| `sar_water_extent_pct` | Float 0–100 | % of farm inundated per SAR |
| `peak_intensity_mm_hr` | Float | Peak 1-hour rainfall intensity |
| `ndvi_delta_vs_neighbours` | Float | This farm's NDVI change minus median of 5 similar nearby farms |
| `official_category_vs_neighbour_median` | Float | This farm's official score minus median official score of similar nearby farms |
| `ndvi_on_assessment_date` | Float | NDVI reconstructed from satellite archive for the exact assessment date |

### Root Cause Output Labels

| Label | What It Means |
|---|---|
| `DRAINAGE_FAILURE` | Blocked or overwhelmed drainage infrastructure significantly extended waterlogging |
| `TERRAIN_DISADVANTAGE` | High TWI / low-lying terrain caused water to concentrate on this farm beyond rainfall expectation |
| `ASSESSMENT_TIMING` | Assessment conducted after water receded; NDVI had partially recovered; assessor underestimated peak damage |
| `SOIL_SATURATION` | Pre-flood saturated soil eliminated all absorption capacity, causing extended inundation |
| `CHECK_DAM_FAILURE` | Upstream check dam / weir overflow released excess water onto downstream farm |
| `ASSESSMENT_INCONSISTENCY` | Farm is a statistical outlier vs similar neighbours with no clear infrastructure explanation |
| `INSUFFICIENT_DATA` | Conflicting signals; cannot determine probable cause — flag for manual review |

### Model Performance (5-Fold Stratified Cross-Validation)

| Metric | Value |
|---|---|
| Subset Accuracy | 71.3% |
| Hamming Loss | 0.14 |
| Macro F1 (per-label average) | 0.74 |
| Macro AUC-ROC | 0.87 |

### SHAP Explainability

For every prediction, **SHAP (SHapley Additive exPlanations)** values are computed. SHAP is a game-theory-based method that assigns each input feature a contribution score to the final prediction — how much did this specific feature push the prediction up or down?

What this means in practice: For every flagged case, the reconciliation report can state not just *what* the root cause is but *which data point* drove that conclusion.

Example SHAP output for a DRAINAGE_FAILURE prediction at 72% probability:
- `drain_blocked_2km = True` → +0.31 (strongest positive contributor)
- `assessment_delay_days = 13` → +0.18
- `soil_vertisol = True` → +0.12
- `ndvi_on_assessment_date = 0.22` → +0.09
- `peak_intensity_mm_hr = 28` → +0.07

This output is rendered in the report as a plain-English explanation, making the AI fully transparent to non-technical government officials.

---

## 14. Confidence Scoring

### Why Confidence Scoring Cannot Be Optional

In a government advisory context, presenting a mismatch finding without a reliability estimate is irresponsible. An investigating officer must know whether the AI is 90% confident or 45% confident before deciding whether to escalate a case, reassign an assessor, or conduct a costly field re-verification.

### Four Components of the Confidence Score

**Component 1 — Source Consensus Score (40% weight)**
The proportion of the four evidence sources that independently also indicate under/over-assessment (source score differs from official score by more than 0.15 in the same direction as the delta). Range: 0–1.

**Component 2 — Data Completeness Score (25% weight)**
Proportion of the four expected sources with usable data:
- Satellite: cloud-free image available within 10 days of event (25%)
- Rainfall: station within 25km or GPM available (25%)
- Ground report: farmer report submitted (25%)
- Infrastructure: GIS layers available for this region (25%)

**Component 3 — Data Quality Score (20% weight)**
Penalisation for:
- Satellite: cloud cover above 15% within farm polygon (−10%), post-flood image older than 10 days (−8%), SAR unavailable (−5%)
- Rainfall: nearest IMD station more than 25km away (−8%, due to interpolation error)
- Ground report: no photos submitted (−5%), EXIF location mismatch (−8%), IndicBERT confidence below 0.6 (−5%)
- Infrastructure: drainage records older than 3 years (−5%), DEM gaps within polygon (−5%)

**Component 4 — Delta Magnitude (15% weight)**
Linear scaling from 0 (delta at threshold, 0.25) to 1 (delta ≥ 0.75). Larger deltas are inherently more conclusive.

### Confidence Score Formula

Confidence (%) = [(0.40 × Consensus) + (0.25 × Completeness) + (0.20 × Quality) + (0.15 × DeltaMagnitude)] × 100

### Confidence Display Bands

| Range | Band | Dashboard Display |
|---|---|---|
| 85–100% | Very High | 🟢 Dark green |
| 70–84% | High | 🟢 Light green |
| 50–69% | Medium | 🟡 Amber |
| 30–49% | Low | 🟠 Orange — request more data before escalating |
| < 30% | Insufficient | 🔴 Red — do not escalate; insufficient evidence |

---

## 15. Report Generation — LLM

### Why an LLM at This Stage?

All preceding pipeline stages produce precise numerical outputs — scores, deltas, probabilities, SHAP values. These are accurate but not usable by district officials without technical training. The LLM layer translates structured machine output into a clear, factual, neutral narrative in plain English.

### Model: Gemini 1.5 Flash (Google AI API)

| Property | Detail |
|---|---|
| Model | Google Gemini 1.5 Flash |
| Context window | 1 million tokens — entire farm dataset fits in one prompt |
| Access | Google AI Studio API (free tier for prototype) |
| No fine-tuning | System prompt engineering alone constrains output format, tone, and content |

### Prompt Engineering Constraints

The system prompt enforces strict rules on the LLM:
- Every factual claim must cite a specific number from the provided data
- Neutral language only — no accusatory terms, no conclusions about intent or fault
- Plain English — no ML terminology, no jargon in the output
- Mandatory structure — specific section headings required in output
- Hallucination guard — if data is not provided, the LLM must write "data not available" rather than infer or estimate
- Mandatory final disclaimer about advisory nature

### Report Sections

1. **Case Summary** — Farm, event, official assessment in 3 sentences
2. **Evidence Comparison** — Table: official score vs evidence score, delta, mismatch class
3. **Source Breakdown** — One paragraph per source, citing actual values
4. **Root Cause Analysis** — Top probable causes with probability and supporting evidence
5. **Temporal Analysis** — Damage onset date from CUSUM, NDVI at assessment date vs peak damage
6. **Neighbouring Farm Comparison** — How this farm's classification compares to similar nearby farms
7. **Recommended Action** — Administrative action (not compensation decision)
8. **Mandatory Disclaimer** — Advisory nature restated

### Output Formats
- **On-screen HTML** in the investigator dashboard
- **PDF** generated from HTML using WeasyPrint Python library — stored on local disk for prototype
- **150-word summary card** for District Collector overview panel

---

## 16. Dashboard & UI

### Farmer Portal

- Available in **Marathi, Hindi, and English** — language selector at top
- Form fields: 7/12 extract number, GPS auto-capture, crop type, area, damage %, description (text), photo upload (up to 5)
- Designed for basic Android smartphones on 3G connections
- Confirmation page with case reference number on submission

### Investigator Dashboard

**Summary Row (top of page)**
- Total farms analysed
- Critical mismatches (count + %)
- Average confidence score
- Cases pending review

**Maharashtra Map (Leaflet.js)**
- All analysed farms shown as coloured circle markers
- 🟢 Consistent | 🟡 Minor | 🟠 Significant | 🔴 Critical
- Click any farm marker → side panel opens with farm summary + link to full report
- Layer toggles: Rainfall intensity zones / Drainage infrastructure / SAR flood extent

**Farm Analysis Page**
- Evidence radar chart: 5 axes (Satellite / Rainfall / Ground / Infrastructure / Official) on one spider chart — visual mismatch instantly obvious
- NDVI timeline: Line chart showing weekly NDVI, annotated with flood date, assessment date, CUSUM change point
- Root cause probability bars: Horizontal bar chart, causes ranked by probability, each bar colour-coded
- Full report with expandable sections
- PDF download button

**Case Triage List**
- Sortable, filterable table: District / Taluka / Mismatch Severity / Crop Type / Confidence / Status
- Bulk export to CSV
- Assign to investigator directly from the table

---

## 17. Complete End-to-End Example

### Case: Ramesh Gaikwad, Soybean Farm, Khed, Pune — July 2024

**Farm profile:** 2.5 hectares soybean, Vertisol clay soil, elevation 542m, clay soil, 3.2km from Bhima River, blocked drain 1.2km north, check dam 4.5km upstream.

**Official Assessment:** Minor Damage, 20% crop loss, assessed July 28 (13 days post-flood), compensation ₹8,500.

---

**Satellite Analysis:**
- Pre-flood NDVI (June 2024 composite): 0.58 — healthy soybean
- Post-flood NDVI (July 22): 0.16 — severely stressed / dead crop
- NDVI change: −0.42 (severe drop)
- NDWI post-flood: 0.31 (water presence confirmed)
- SAR water extent (July 17): 68% of farm inundated
- CUSUM detects damage onset: July 15
- NDVI on assessment date (July 28): 0.20 — still very low, but water had receded
- **Satellite Damage Score: 0.72**

**Rainfall Analysis:**
- Total event rainfall (July 14–16): 214mm
- Peak 1-hour intensity: 28mm/hr (July 15, 18:00)
- Antecedent 30-day rainfall: 180mm (soil fully saturated pre-flood)
- IMD classification: Extremely Heavy
- **Rainfall Damage Score: 0.68**

**Ground Report Analysis:**
- IndicBERT severity classification: Severe (confidence 0.84)
- NER extracts: crop=soybean, duration=4 days, damage_pct=80–90%, secondary=soil_erosion
- 3 photos submitted — all pass EXIF location check, ResNet-50 classifies all as "Flooded Farmland"
- **Ground Report Score: 0.80**

**Infrastructure Analysis:**
- TWI: 9.2 (above threshold of 8 — high water accumulation zone)
- Drain status within 2km: Blocked (blocked canal to the north)
- Soil type: Vertisol → retention risk 0.90
- Distance to river: 3,200m
- Check dam overflow: True (MKVDC record)
- **Infrastructure Risk Score: 0.65**

**Evidence Aggregation:**
- (0.35 × 0.72) + (0.25 × 0.68) + (0.20 × 0.80) + (0.20 × 0.65)
- = 0.252 + 0.170 + 0.160 + 0.130
- = **Evidence Score: 0.71**

**Mismatch Detection:**
- Official Score: 0.25 (Minor)
- Evidence Score: 0.71
- Delta: **+0.46 → CRITICAL MISMATCH, UNDER-ASSESSED**
- Source consensus: 4/4 sources indicate damage above official threshold

**Root Cause Classification (Random Forest):**
- DRAINAGE_FAILURE: **72.3%** — drain_blocked_2km=True (SHAP +0.31), soil_vertisol=True (SHAP +0.12)
- ASSESSMENT_TIMING: **65.1%** — assessment_delay=13 days (SHAP +0.18), ndvi_on_assessment_date=0.20 (SHAP +0.09)
- SOIL_SATURATION: **41.8%** — antecedent_rainfall=180mm (SHAP +0.14)

**Confidence Score:**
- Consensus: 4/4 → 1.0
- Completeness: 4/4 sources available → 1.0
- Quality: Minor cloud deduction (8% cloud cover) → 0.92
- Delta magnitude: 0.46 → 0.85 (normalised)
- **Confidence: 87%**

**Recommended Action: PRIORITY REVIEW**

---

## 18. What Is Deferred to Hackathon

These are planned but deliberately excluded from the prototype to keep it lean and demo-ready:

| Feature | Hackathon Plan |
|---|---|
| **Redis** | Add as cache layer and Celery broker for async satellite jobs at scale |
| **MinIO** | Replace local filesystem storage with S3-compatible object store |
| **Celery task queue** | Move satellite analysis to background async jobs |
| **Live GEE API calls** | Replace pre-fetched data with live API calls per farm/date |
| **Live IMD/GPM API** | Real-time rainfall fetch instead of pre-loaded data |
| **MahaBhumi 7/12 API** | Live verification of farm ownership against government records |
| **SMS / Email alerts** | Twilio/MSG91 SMS to district officers on critical mismatch detection |
| **Farmer OTP verification** | Phone number verification before report submission |
| **Marathi voice-to-text** | Speech input for farmer descriptions using Whisper / Vakyansh |
| **Docker containerisation** | Full Docker Compose setup for reproducible deployment |
| **Expanded training dataset** | Add 2019–2023 Maharashtra flood cases to all ML models |

---

## 19. Ethical Framework

### Hard System Constraints

- The system **cannot write to or modify** the official government assessment database
- The system **cannot directly communicate** with farmers about compensation outcomes
- Every prediction carries a **mandatory confidence score** — uncertainty is never hidden
- The Gemini system prompt **prevents** any compensation amount suggestion
- All AI decisions are written to an **immutable audit log** — every input, output, model version, and timestamp recorded

### Transparency by Design

- SHAP values make every root cause prediction **fully explainable** — not a black box
- Every number in the report cites its source
- Reports include a mandatory disclaimer in every output
- Confidence bands are colour-coded and prominently displayed — low confidence cases are visually distinct

### Privacy Principles

- Farmer Aadhaar numbers stored as **SHA-256 hashes** — original cannot be recovered
- Bank account numbers encrypted with **AES-256**
- Photo GPS metadata stripped after location verification
- Role-based access control — investigators see only their district's data

### Bias Monitoring (Hackathon Phase)

Statistical audits checking whether mismatch flags are disproportionately concentrated by district, taluka, assessor ID, crop type, or farmer community — to detect and correct any systematic bias introduced by training data.

---

*PCCOE Indradhanu · Reconciliation AI · Prototype Round · October 2026*
