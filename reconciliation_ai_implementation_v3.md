# Reconciliation AI — Maharashtra Flood Compensation

## Revised Technical Implementation Document (v3)

> **Team:** PCCOE Indradhanu · **Stage:** Round 2 prototype → 24-hour hackathon & pilot readiness
> **Revision date:** 1 November 2026 · **Supersedes:** v2 (`Reconciliation_AI_Implementation_v2.md`) and v1 (`Reconciliation_AI_Implementation.md`)
> **What this version is:** v3 retains the sound two-pillar architecture of v2 (separating *Observed Damage* from *Hazard Plausibility*) while fixing critical vulnerabilities discovered during adversarial and geometric stress-testing: farmer photo spoofing and neighbor-plot fraud, riverine strip-parcel geometry erasure, Difference-in-Differences truncation bias, silt-vs-root-rot spectral confusion, SAR Otsu unimodal failure, 33% threshold-surfing in pooling, village-wide blanket-panchnama blindness, SQL timezone hash drift, and percentage/Devanagari bugs in the LLM numeric verifier.

## 0. Read this first

### 0.1 Status legend (used throughout)

| Tag | Meaning | 
| ----- | ----- | 
| ✅ | Verified against an external source listed in §15 | 
| 🔎 | Plausible but **not verified**. Check before you claim it in front of judges | 
| 🧪 | Synthetic or simulated. Never present as real-world performance | 
| 🎯 | A target or initial setting. Not yet measured, to be tuned | 
| 🗺️ | Roadmap. Not part of the prototype | 

**Rule for the whole document:** no performance number appears unless it was measured, and every measured number must say whether it came from real or synthetic data. All unverified accuracy figures from v1 remain removed and replaced with the evaluation protocol (§11) and reporting template.

### 0.2 What changed from v2 to v3, and why

| \# | Area | v2 | v3 | Why (short) | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | Photo & farm ownership check | 100 m GPS buffer + 64-bit `pHash` + in-app capture | **PostGIS compass frustum ray-casting (`ST_Project`) + pitch/horizon gate + 3-frame burst parallax/Moiré check + `pgvector` embedding deduplication + 7/12 crop match** | A 100 m buffer covers 8–15 neighboring farms; farmers could stand on a road or photograph a neighbor's flooded field or a 2 m puddle | 
| 2 | Narrow strip-parcel geometry | Fixed `-10 m` inner buffer on all parcels | **Sub-pixel area-weighted extraction (`exactextract` overlap weights** $w_i$**) + adaptive buffer** | Riverine farms in Pune/Western Maharashtra are often 20–30 m wide ribbons; a `-10 m` buffer erases them to `POLYGON EMPTY` | 
| 3 | Partial-parcel submergence | Mean parcel loss $\bar{L}_{\text{farm}}$ only | **Dual metric: mean canopy loss** $\bar{L}_{\text{farm}}$ **AND damaged area fraction (**$\text{share of pixels with } L_i \ge 0.35$**)** | Riverbank floods often destroy the lower 40% of a long strip plot while leaving the upper 60% untouched | 
| 4 | Satellite DiD math | Clip pixel loss to $[0,1]$ *before* subtracting control median | **Unclipped vigour deficit DiD (**$D_{\text{farm}} - \text{median}(D_{\text{controls}})$**), clipped to** $[0,1]$ **only at the final step** | Clipping controls at 0 before taking the median truncates healthy controls and biases flood-attributable loss downward by 5–10% | 
| 5 | Mud coating vs delayed root rot | Single-index NDVI on earliest clear post-event scene | **Multi-index check (`NDVI` + Red-Edge `NDRE` + SWIR `NDMI`) across two windows (Day +1..+5 vs Day +10..+16)** | Silt-coated live crops recover after rain washes leaves, whereas waterlogged black-soil soybean rots 7–14 days later | 
| 6 | SAR change detection | Otsu threshold on 2 km window flagging both decreases and increases | **Ashman's** $D > 2.0$ **bimodality gate + physical bounds (**$\Delta\text{VV} \le -2.5\text{ dB}, \text{VH} \le -20\text{ dB}$**); positive** $\Delta\text{VV}$ **allowed only when** $\text{HAND} \le 4\text{ m}$ **and above upland rain-fed controls** | Otsu splits unimodal noise when flood fraction is small; ordinary rain increases soil backscatter by +2 to +4 dB everywhere | 
| 7 | Pooling & 33% boundary surfing | Inverse-variance pooling; conflict returns no value | **Satellite-gated 33% boundary rule (`GROUND_DRIVEN_BOUNDARY_CROSSING`) + fallback to** $V_{\text{sat}}$ **when `SOURCE_CONFLICT` fires** | Prevent self-reports from pulling a 26% satellite loss over 33% unnoticed, and prevent panicked farmer over-reports from crashing Detectors A & B | 
| 8 | Blanket village panchnamas | Nearest 60 peers within 15 km | **Cross-assessor peer requirement (**$\ge 50\%$ **from other officers/villages) + Detector D (`CLUSTER_BIAS`)** | If one officer writes a flat 20% across a whole village, village peers have median 20% and $z = 0$, blinding peer discordance | 
| 9 | Missing e-Peek Pahani data | SQL requires exact `crop` and `sowing_date` match | **Spectral phenology fallback (k-NN matching on May–June pre-flood NDVI trajectory)** | Early-July flood victims often have not filed Kharif crop surveys yet, causing `INSUFFICIENT_PEERS` cold-start failures | 
| 10 | Database idempotency & audit hash | Raw string concat + `NEW.ts::text`; missing primary keys | **UTC ISO-8601 epoch + `jsonb_build_array` canonical hashing; `PRIMARY KEY` constraints for idempotent `UPSERT`s** | `NEW.ts::text` changes with session `TimeZone`, breaking `verify_chain()`; re-running `/analyze` duplicated rows | 
| 11 | Report numeric verifier | Regex matches raw floats in `facts` dict | **Percentage-aware (`x` and `x*100`), date-aware, Devanagari-normalized (`०-९` → `0-9`), and direction-checked verifier** | v2's `numbers_ok()` rejected 100% of valid LLM outputs because `"64%"` did not match `0.64` in `facts` | 

### 0.3 Summary of v1 → v2 foundational changes (retained in v3)

| Area | v1 | v2 / v3 Foundation | 
| ----- | ----- | ----- | 
| Evidence model | 4 sources averaged into one score | **Observation** (satellite + ground) kept strictly separate from **Hazard context** (rain, river/dam, terrain) | 
| Root cause | Random Forest + SHAP on synthetic labels | **Transparent contributing-factor screen** (rules + evidence trace, no circular ML probabilities) | 
| Confidence | "Confidence 87%" from a weighted formula | **Evidence Strength Grade (A–D)** + spatial block-bootstrap **intervals** | 
| Marathi NLP | IndicBERT on mixed samples | **Structured form first**, LLM extraction for consistency check only, **MahaBERT** benchmark | 
| Identity | SHA-256 of Aadhaar | **Zero Aadhaar collection.** Case ID + Survey/Gat No. + Agri Stack Farmer ID | 
| Demo event | 14–16 July 2024 | **24–26 July 2024** (Pune / Khadakwasla release of \~35,000–40,000 cusecs) ✅ | 

## 1. Project summary

### 1.1 Problem

After a flood, crop-loss assessments (panchnamas) drive compensation. Under SDRF/NDRF norms, input subsidy is available where crop loss is **33% or more**, restricted to **sown area** ✅. Assessments are made by field officers (Talathi, Krushi Sahayak, Gramsevak) under severe time pressure, often days after floodwaters have receded, and no independent parcel-level check exists at scale. Errors cut both ways:

* **Under-assessment:** Farmers assessed below the 33% cutoff—or omitted via blanket village-wide estimates—lose vital relief.

* **Over-assessment & Fraud:** Falsified claims, reused WhatsApp flood photos, or photos taken of a neighbor's flooded field divert public disaster funds.

### 1.2 Concept

For each parcel, compare three pillars **without mixing them**:

1. **What the official record says:** recorded damage %, assessment date, and assessor group token.

2. **What was observed on the parcel:** phenology-adjusted, control-differenced satellite vegetation loss (mean loss and sub-parcel damaged area fraction), SAR inundation evidence, and multi-layer verified ground evidence.

3. **What the hazard makes plausible:** IMD rainfall class/percentile, CWC/WRD river and dam release exposure, Height Above Nearest Drainage (HAND), and Topographic Wetness Index (TWI).

The system flags **discordance** for human review, separates **satellite-backed flags** from **ground-report-driven flags**, traces the exact contributing factors, and grades evidence strength (A–D). It **never** autonomously approves or denies compensation.

### 1.3 Positioning

* **Second-opinion quality-assurance layer:** Complements SDRF/NDRF panchnamas and PMFBY localized-calamity assessments ✅.

* **Distinct from YES-TECH:** PMFBY's YES-TECH estimates yield at the Insurance Unit (village/circle) level ✅. Reconciliation AI audits **individual parcel assessment records** against independent spatial and ground evidence.

## 2. Critical review → decisions (v1 → v2 → v3 complete matrix)

| \# | Problem Identified | Origin | Severity | Resolution Decision | 
| ----- | ----- | ----- | ----- | ----- | 
| P1 | Hazard proxies averaged with damage observations | v1 | 🔴 Critical | **D1:** Separate Observation pillar from Hazard Plausibility pillar | 
| P2 | Absolute gap fails under uniform bias or phenology shifts | v1 | 🔴 Critical | **D2 & D15:** Cross-assessor peer discordance + control-differenced DiD + cluster bias detector | 
| P3 | Siamese CNN lacks labels; 64×64 patch ≫ parcel; fixed `-10 m` buffer erases narrow strip plots | v1 / v2 | 🔴 Critical | **D3:** Unclipped DiD fractional loss + sub-pixel area weighting + dual mean/area-damaged metrics + NDRE/NDMI | 
| P4 | Root-cause RF + SHAP trained on circular synthetic labels | v1 | 🔴 Critical | **D6:** Deterministic contributing-factor screen with explicit data trace | 
| P5 | Spatial leakage in random splits | v1 | 🔴 Critical | **D14:** Leave-one-event-out + spatial block CV + injection & ecological benchmarks | 
| P6 | "Confidence %" misleads officers into seeing a calibrated probability | v1 | 🟠 High | **D7:** Evidence Strength Grade (A–D) + 3×3 block-bootstrap intervals | 
| P7 | Fixed weights / conflict rule either allows 33% threshold-surfing or crashes detectors | v1 / v2 | 🔴 Critical | **D5:** Inverse-variance pooling + satellite-gated 33% boundary + satellite fallback on `SOURCE_CONFLICT` | 
| P8 | SAR fixed threshold misses double-bounce; v2 Otsu fails on unimodal scenes and rain-wet soil | v1 / v2 | 🔴 Critical | **D4:** Ashman's $D$ bimodality check + physical dB bounds + HAND-gated double-bounce relative to controls | 
| P9 | Retired LLM IDs & 100% false-rejection bug in `numbers_ok()` due to % vs decimal & Devanagari | v1 / v2 | 🔴 Critical | **D10 & D16:** Template-first report + unit-normalized, Devanagari-aware, direction-checked verifier | 
| P10 | Aadhaar storage / raw SHA-256 hashing compliance risk | v1 | 🟠 High | **D11:** Do not collect Aadhaar; use Case ID + Gat No. + Agri Stack Farmer ID | 
| P11 | Missing drain/dam datasets; wrong IMD classes; IMERG V06 retired | v1 | 🟠 High | **D12:** CWC/WRD/GUARDIAN discharge + HAND/TWI + IMD standard 24-h classes + IMERG V07 | 
| P12 | Marathi free-text double counting & weak multilingual baseline | v1 | 🟡 Medium | **D8:** Structured inputs primary; free text used only for consistency flags; MahaBERT benchmark | 
| P13 | Photo fraud: 100 m GPS buffer allows neighbor-farm & puddle photos; `pHash` bypassed by cropping | v1 / v2 | 🔴 Critical | **D9:** PostGIS compass frustum ray-casting + pitch/horizon check + 3-frame burst parallax/Moiré + `pgvector` embeddings + 7/12 crop match | 
| P14 | Duplicate farmer portal & cold-start failure when e-Peek Pahani crop data is missing | v1 / v2 | 🟠 High | **D13 & D15:** Integrate e-Peek Pahani; spectral phenology k-NN fallback when crop/sowing date is null | 
| P15 | SQL `NEW.ts::text` timezone drift breaks hash chain; missing primary keys break idempotency | v2 | 🟠 High | **D16:** UTC ISO-8601 epoch + `jsonb_build_array` hash input; strict `PRIMARY KEY`s for `UPSERT` | 

## 3. Decision records (options compared & v3 upgrades)

Effort scale for a 24-hour hackathon: **S** ≤ 2 h · **M** 3–6 h · **L** > 6 h.

### D1 — Evidence model: hazard vs observation

**Decision:** Maintain two strict pillars: **Observed Damage** (satellite optical/SAR + verified farmer ground report) and **Hazard Plausibility** (rainfall, dam/river release, HAND, TWI, soil). Hazard context never enters the numerical damage estimate; it validates plausibility and triggers explanatory flags (`NON_FLOOD_CAUSE_POSSIBLE`, `DISCHARGE_EXPOSURE`).

### D2 & D15 — Four-layer detection engine & spectral peer fallback

**Problem in v2:**

1. v2 selected peers within 15 km without checking `assessor_token`. When a field officer records a blanket "20% loss" across 40 farms in one village, the peer median becomes 20% and $z = 0$, blinding the peer discordance detector.

2. v2 required exact SQL matches on `crop` and `sowing_date` (`abs(p.sowing_date - :sowing_date) <= 10`). When farmers haven't filed e-Peek Pahani before an early-monsoon flood, the query returns 0 peers (`INSUFFICIENT_PEERS`).

| Layer | What It Detects | v3 Upgrade | 
| ----- | ----- | ----- | 
| **A. Absolute Plausibility & 33% Boundary** | Interval separation between official $[O_{\text{lo}}, O_{\text{hi}}]$ and observed $[P_{\text{lo}}, P_{\text{hi}}]$, plus crossing the 33% SDRF threshold | Distinguishes `SAT_BACKED_BOUNDARY_CROSSING` ($V_{\text{sat,lo}} \ge 0.33$) from `GROUND_DRIVEN_BOUNDARY_CROSSING` ($V_{\text{sat}} < 0.33$ pulled over 0.33 by ground report) | 
| **B. Cross-Assessor Peer Discordance** | Individual parcel assessed inconsistently relative to peers with similar observed loss | Requires $\ge 50\%$ of peers to come from **different assessor tokens / neighboring villages**; falls back to **pre-event NDVI spectral curve matching** when `crop`/`sowing_date` is null | 
| **C. Timing Gradient** | Systematic decay in recorded official damage as `delay_days` increases | Controls for parcel elevation (`HAND`) so late visits to inaccessible riverside plots are distinguished from faded water marks | 
| **D. Village / Assessor Cluster Bias (`CLUSTER_BIAS`)** | Blanket village-wide under-assessment (e.g., flat 15–20% panchnama across a flooded village) | Fires when $\ge 5$ parcels under the same `assessor_token` or village have $V_{\text{sat,lo}} - O_{\text{hi}} \ge 0.20$, escalating the batch to `PRIORITY_REVIEW` even when internal peer $z \approx 0$ | 

### D3 — Satellite damage: sub-pixel geometry, unclipped DiD, dual loss metrics & multi-index trajectory

**Problems in v2:**

1. **Ribbon-parcel erasure:** Along Maharashtra rivers, generational plot division creates strips $20\text{–}30\text{ m}$ wide by $250\text{ m}$ long. A `-10 m` buffer shrinks a 20 m-wide plot to zero area.

2. **Truncation bias:** Clipping per-pixel loss $L = \text{clip}((E-O)/(E-B), 0, 1)$ *before* computing $\text{median}(L_{\text{controls}})$ clamps all healthier-than-average control pixels to 0, biasing $\text{median}(L_{\text{controls}})$ upward by 0.05–0.10 and artificially penalizing the farmer.

3. **Partial submergence dilution:** If the riverside 40% of a long plot is 100% destroyed and the upper 60% is unharmed, whole-parcel averaging dilutes the loss.

4. **Silt vs root rot:** Silt coating drops NDVI immediately after flood recession even if crops survive, whereas black-soil waterlogging causes root rot 7–14 days later.

**v3 Decisions:**

1. **Sub-pixel area-weighted extraction:** Instead of a hard `-10 m` buffer that deletes narrow plots, compute exact pixel-polygon overlap fractions $w_i \in (0, 1]$ (`rasterio` / `exactextract`). Keep interior pixels ($w_i \ge 0.65$) and define effective pixel count $n_{\text{eff}} = \sum w_i$. Apply a `-5 m` buffer only when `ST_MinimumClearance` (or minimum bounding rectangle width) $\ge 35\text{ m}$.

2. **Unclipped Difference-in-Differences (DiD):**
   For each pixel $i$, compute unclipped vigour deficit:
   

   $$
   d_i = \frac{E_i - O_i}{\max(E_i - B_i, 0.05)}
   $$

   
   Aggregate area-weighted parcel deficit $\bar{d}_{\text{farm}} = \frac{\sum w_i d_i}{\sum w_i}$ and control median $d_{\text{ctrl}} = \text{median}(\bar{d}_{\text{controls}})$. Then clip **only after differencing**:
   

   $$
   L_{\text{attr}} = \text{clip}(\bar{d}_{\text{farm}} - d_{\text{ctrl}}, 0.0, 1.0)
   $$

3. **Dual loss metrics (Mean Canopy Loss + Damaged Area Fraction):**
   Alongside $L_{\text{attr}}$, compute the **damaged area fraction**:
   

   $$
   A_{\text{dmg}} = \frac{\sum_{i} w_i \cdot \mathbb{I}(d_i - d_{\text{ctrl}} \ge 0.35)}{\sum_{i} w_i}
   $$

   
   Report $V_{\text{sat}} = \max(L_{\text{attr}}, A_{\text{dmg}})$ with both values shown on the dashboard so partial-plot riverbank destruction is never diluted away.

4. **Multi-index two-window trajectory (`NDVI` + `NDRE` + `NDMI`):**
   Compute Red-Edge $\text{NDRE} = \frac{B08A - B05}{B08A + B05}$ (penetrates thin leaf silt better than red band) and moisture index $\text{NDMI} = \frac{B08A - B11}{B08A + B11}$. Evaluate across two post-event windows when scenes exist:

   * **Window 1 (Immediate: Peak +1 to +6 days):** Captures physical washout and standing water (`NDWI > 0`). Never treat submerged water pixels as final vegetation loss until water recedes.

   * **Window 2 (Delayed: Peak +7 to +16 days):** Captures root-rot wilting (`NDRE` and `NDMI` continuing to drop) vs silt wash-off recovery (`NDRE` rebounding by $> 0.12$, which triggers flag `SILT_RECOVERY_OBSERVED`).

### D4 — SAR flood evidence: bimodality gate, physical bounds & HAND-filtered double bounce

**Problems in v2:**

1. Otsu thresholding on a 2 km window splits unimodal noise in half whenever the window is $< 10\%$ or $> 90\%$ flooded.

2. Flagging positive backscatter increases ($\Delta\text{VV} > 0$) flags every rain-wet non-flooded field in the district because soil moisture raises dielectric constant.

**v3 Decisions:**

1. **Speckle filtering:** Apply a $3 \times 3$ Refined Lee (or median-ratio) filter to pre- and post-event Sentinel-1A $\sigma^0$ (dB) rasters.

2. **Bimodality gate + physical bounds for open water:** Run Otsu on $\Delta\text{VV} = \text{VV}_{\text{post}} - \text{VV}_{\text{pre}}$ over the 2 km neighborhood **only if** Ashman's $D > 2.0$ (confirming a bimodal histogram); otherwise use fixed physical thresholds. A pixel is flagged as **open-water inundation** if:
   

   $$
   \Delta\text{VV} \le \min(\tau_{\text{Otsu}}, -2.5\text{ dB}) \quad \text{AND} \quad \text{VH}_{\text{post}} \le -20.0\text{ dB}
   $$

3. **Terrain- and control-gated double bounce for flooded crops:** A pixel is flagged as **sub-canopy flooded vegetation** only if all three conditions hold:

   * Parcel terrain is low-lying: $\text{HAND} \le 4.0\text{ m}$ 🎯,

   * Pre-event vegetation was standing: $\text{NDVI}_{\text{pre}} \ge 0.35$,

   * Backscatter jump exceeds regional rain-wetting on upland controls: $\Delta\text{VV}_{\text{pixel}} - \text{median}(\Delta\text{VV}_{\text{controls}}) \ge +2.5\text{ dB}$.

### D5 — Inverse-variance pooling, 33% boundary protection & conflict fallback

**Problems in v2:**

1. With $\sigma_{\text{sat}} = 0.09$ and $\sigma_{\text{ground}} = 0.15$, the $2\sigma$ conflict threshold is $0.35$. A farmer with $26\%$ satellite loss can self-report $60\%$ loss ($|0.26 - 0.60| = 0.34 < 0.35$, no conflict!) and pull the pooled score to $35\%$—crossing the 33% payout threshold purely via self-reporting.

2. When `SOURCE_CONFLICT` fired in v2, `observed_estimate()` returned no `value`, `lo`, or `hi`, crashing Detectors A & B.

**v3 Decisions:**

1. **Conflict fallback preserves satellite detection:** When $|V_{\text{sat}} - V_{\text{ground}}| > 2\sqrt{\sigma_{\text{sat}}^2 + \sigma_{\text{ground}}^2}$, set status to `SOURCE_CONFLICT`, **do not pool**, and set the reference interval $[P_{\text{lo}}, P_{\text{hi}}]$ to the **satellite interval** $[V_{\text{sat,lo}}, V_{\text{sat,hi}}]$ so Detectors A, B, and D still run without crashing.

2. **33% Boundary Surfing Guard:** When $V_{\text{sat}} < 0.33$ and $V_{\text{ground}} \ge 0.33$ causes the pooled estimate $P$ to cross $0.33$, do **not** emit a standard `UNDER_RISK` flag; emit `GROUND_DRIVEN_BOUNDARY_CROSSING` and cap Evidence Strength Grade at **B** until physical field verification.

### D9 — Deep-dive photo authenticity & farm ownership verification

**Problem in v2:** How do we know a farmer's uploaded flood photo is (a) real and live, (b) actually showing **their own parcel** rather than a neighbor's flooded field 40 m away, (c) showing field-scale flooding rather than a $2\text{ m}$ puddle, and (d) not a cropped WhatsApp forward?

**v3 Multi-Layer Verification Pipeline:**

| Check Layer | Technical Mechanism | Fraud / Error Defeated | 
| ----- | ----- | ----- | 
| **1. Ownership & Plot Binding** | Match OTP-authenticated mobile / Agri Stack Farmer ID to the 7/12 (Satbara) survey/Gat number; load the parcel's `geom_utm` polygon and declared crop from e-Peek Pahani. | Prevents filing claims on someone else's Gat number. | 
| **2. PostGIS Camera Viewing-Frustum Ray-Cast** | Record GPS `[lat, lon, accuracy_m]` **plus** magnetometer compass heading $\alpha \in [0^\circ, 360^\circ)$ (`DeviceOrientationEvent`). Construct a 60 m triangular viewing sector ($\alpha \pm 25^\circ$) in UTM (`ST_MakePolygon` + `ST_Project`). Require `ST_Area(ST_Intersection(frustum, parcel.geom_utm)) / ST_Area(frustum) >= 0.40` 🎯 (the camera must be pointing *into* the farmer's own parcel, and user position must be inside or within 15 m of the parcel boundary). | Defeats the **"Neighbor's Farm / Roadside Canal" attack** where a farmer stands near their plot but points the camera at an adjacent flooded plot or ditch. | 
| **3. Pitch, Horizon & Two-Angle Geometry Gate** | Require phone pitch $\beta \in [65^\circ, 88^\circ]$ (phone held upright viewing across the parcel, showing ≥15% sky/horizon or boundary bund) across **at least 2 photos** taken either $\ge 15\text{ m}$ apart or rotated $\ge 35^\circ$ in azimuth. | Defeats the **"Micro-Puddle Trick"** (pointing the camera straight down at a small mud puddle so it fills the frame). | 
| **4. 3-Frame Burst Liveness, Parallax & Moiré Check** | On shutter press, the PWA captures a 1.5-second 3-frame burst via `getUserMedia`. Compute Lucas-Kanade optical flow between frames 1 and 3: real 3D scenes show foreground-vs-background parallax; a flat screen or printed photo shows rigid homography + high-frequency 2D FFT Moiré spikes. Cross-check sun azimuth/sky luminance against capture timestamp. | Defeats **"Screen-of-a-Screen" spoofing** (photographing another phone/laptop showing flood footage) and device-clock tampering. | 
| **5. `pgvector` Embedding Deduplication + Spatial Clustering** | Extract a 512-D normalized embedding using a lightweight vision backbone (CLIP/SigLIP) and store in PostgreSQL `pgvector`. Flag `DUPLICATE_PHOTO_EMBEDDING` if cosine similarity $\ge 0.92$ against any photo from another `case_id` in the event, even if cropped, rotated, or color-shifted. | Defeats **WhatsApp viral flood photos** and multiple farmers photographing the exact same flooded corner from slightly different angles. | 
| **6. Zero-Shot Crop & Pre-Flood Landmark Consistency** | Compare zero-shot class probabilities (`flooded soybean/short crop`, `tall sugarcane`, `bare fallow`, `non-farm road/building`) against the 7/12 declared crop. When pre-flood e-Peek Pahani photos exist for that Gat number, compare background horizon/tree-line embeddings. | Catches **`CROP_MISMATCH`** (e.g., claiming soybean loss using a photo of flooded sugarcane or fallow wasteland). | 

**Impact on** $\sigma_{\text{ground}}$ **🎯:**

* **Tier 1 Verified (**$\sigma_g = 0.14$**):** $\ge 2$ photos pass all 6 checks (frustum intersection $\ge 40\%$, pitch/parallax valid, liveness passed, zero duplicates, crop consistent).

* **Tier 2 Partially Verified (**$\sigma_g = 0.22$**):** In-app capture near parcel with no duplicates, but compass sensor absent or frustum overlap $< 40\%$.

* **Tier 3 Unverified / Gallery (**$\sigma_g = 0.35$ **or excluded):** Gallery upload or failed liveness/frustum check. If duplicate embedding (`sim >= 0.92`) or screen Moiré is detected, **exclude ground estimate entirely** and raise `PHOTO_INTEGRITY_ALERT` for audit (never auto-rejecting the satellite evidence).

### D10 & D16 — Deterministic template report & fixed numeric/Devanagari verifier

**Problems in v2:**

1. `numbers_ok(text, facts)` compared raw regex numbers in the LLM text (e.g., `"64"` from `"64%"`, `"25"` from `"25 July"`) against raw floats in `facts` (`0.64`, `"2024-07-25"`), causing **100% false rejection**.

2. In Marathi (`?lang=mr`), Devanagari digits (`६४%`) matched regex `\d+` but failed ASCII set membership.

3. Swapped numbers (*"Official is 64% and observed is 20%"*) passed set membership.

**v3 Decision:** Normalize Devanagari digits to ASCII before checking, populate `allowed` with decimal values ($x$), percentage equivalents ($100x$), and date day/month/year integers, and add a **directional order assertion** verifying that the number immediately following the official-record clause matches `official_pct` rather than `observed_pct`.

## 4. Revised system architecture (v3)

### 4.1 End-to-end processing pipeline

| Stage | Module | Inputs | Core Processing (v3) | Outputs | 
| ----- | ----- | ----- | ----- | ----- | 
| **Stage 1** | **7.1 Parcel & Peer Prep** | Parcel polygon (`EPSG:32643`), crop/sowing record, S-2 pre-event stack | Compute sub-pixel overlap weights $w_i$; select cross-assessor peers ($\ge 50\%$ external assessor) & non-flooded controls; fallback to pre-flood NDVI curve k-NN if crop/sowing missing | `w_i` mask, $n_{\text{eff}}$, peer set, control set | 
| **Stage 2A** | **7.2 Satellite Observation** | S-2 L2A (pre, immediate post, +10–16d post), S-1A GRD | Unclipped DiD on `NDVI`, `NDRE`, `NDMI`; compute mean loss $L_{\text{attr}}$ and damaged area fraction $A_{\text{dmg}}$; 3×3 block bootstrap $\sigma_{\text{sat}}$; Lee-filtered S-1A change with Ashman's $D$ & HAND gate | $V_{\text{sat}}, \sigma_{\text{sat}}, [V_{\text{sat,lo}}, V_{\text{sat,hi}}], A_{\text{dmg}}, \text{water\_frac}$ | 
| **Stage 2B** | **7.4 Ground & Photo Verifier** | Structured form, in-app burst frames, GPS + compass $(\alpha, \beta)$ | PostGIS frustum intersection with `geom_utm`; pitch/horizon check; 3-frame optical flow & Moiré check; `pgvector` cosine deduplication; 7/12 crop match | $V_{\text{ground}}, \sigma_{\text{ground}}$, photo integrity flags | 
| **Stage 2C** | **7.3 Hazard Context** | IMD/IMERG V07 rain, CWC/WRD discharge, DEM (HAND/TWI), soil | Compute 24-h IMD class, local rain percentile, antecedent 30-d wetness, HAND percentile, dam-release reach exposure | `plausibility` (`LOW`, `MODERATE`, `HIGH`), hazard JSON | 
| **Stage 3** | **7.6 Pooling & Conflict Engine** | $(V_{\text{sat}}, \sigma_{\text{sat}})$, $(V_{\text{ground}}, \sigma_{\text{ground}})$ | Test $2\sigma$ conflict rule; if conflict, emit `SOURCE_CONFLICT` and use $V_{\text{sat}}$ as reference; else inverse-variance pool; check 33% boundary-surfing guard | $[P_{\text{lo}}, P_{\text{hi}}]$, pooling status, boundary status | 
| **Stage 4** | **7.7–7.9 Detectors, Factors & Grade** | Official $[O_{\text{lo}}, O_{\text{hi}}]$, $[P_{\text{lo}}, P_{\text{hi}}]$, peers, delay, hazard | Run Detector A (Interval/33%), Detector B (Cross-Assessor Peer $z$), Detector C (Timing $\rho$), Detector D (`CLUSTER_BIAS`); evaluate 12 contributing factors; score Grade A–D | `tier`, `grade` (A–D), `factors` trace | 
| **Stage 5** | **7.10 Report & Hash Audit** | `facts` JSON, `model_versions` | Render Jinja2 Marathi/English report; optional LLM polish gated by unit/Devanagari/direction verifier; append to UTC-canonical SHA-256 hash-chained `audit_log` | Bilingual report, review queue item, tamper-evident log | 

## 5. Data sources and availability

| Input | Source | Status | Fallback if unavailable | 
| ----- | ----- | ----- | ----- | 
| Optical imagery | Sentinel-2 L2A (10 m B02/B03/B04/B08; 20 m B05/B08A/B11/B12/SCL) | ✅ standard | Harmonized Landsat-Sentinel (HLS) 🔎 | 
| SAR imagery | Sentinel-1A GRD (VV, VH; \~12-day repeat in July 2024) ✅ | Verify exact pass dates first | NRSC/Bhuvan flood layers 🔎, Copernicus EMS, optical NDWI water mask | 
| Flood water mask | Sen1Floods11-tuned Prithvi-EO-2.0-300M ✅, NDWI/MNDWI | ✅ | Ashman-gated SAR change + physical dB threshold | 
| Parcel boundaries | Maharashtra Bhunaksha cadastral polygons (Gat/Survey numbers) 🔎 | Confirm API/shapefile access | Realistic riverside strip-parcel polygons over real Pune S-2 imagery 🧪 | 
| Crop & sowing date | **e-Peek Pahani** (7/12 Form 12 crop registry + pre-flood geotagged photo) ✅ | Needs state integration | Spectral phenology k-NN matching on pre-flood S-2 time series + synthetic demo records 🧪 | 
| Official assessments | Revenue/Agriculture panchnama records | Needs MoU | Simulated records with planted individual & village-level anomalies 🧪 | 
| Rainfall | IMD gridded (0.25°), NASA GPM IMERG V07 (0.1°) ✅ | ✅ | Maharashtra Mahavedh automated weather stations (AWS) 🔎 | 
| River / dam release | CWC flood portal ✅, GUARDIAN sub-daily gauge dataset ✅, WRD bulletins (Khadakwasla \~35,000–40,000 cusecs on 25 Jul 2024) ✅ | ✅ | Published WRD/Situation Report figures with citation | 
| Terrain (DEM) | Copernicus GLO-30 / FABDEM / CartoDEM 🔎 | ✅ | SRTM 30 m conditioned via `pysheds` | 

## 6. Database design (v3 idempotent & tamper-evident schema)

```
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector for 512-D photo deduplication

CREATE TABLE events (
  event_id      TEXT PRIMARY KEY,        -- e.g. 'MH-2024-07-PUNE'
  name          TEXT NOT NULL,
  start_date    DATE NOT NULL,
  peak_date     DATE NOT NULL,
  end_date      DATE NOT NULL,
  notes         TEXT
);

CREATE TABLE parcels (
  parcel_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  survey_no     TEXT NOT NULL,
  village       TEXT NOT NULL,
  taluka        TEXT NOT NULL,
  district      TEXT NOT NULL,
  area_ha       NUMERIC(8,3) NOT NULL,
  min_width_m   NUMERIC(6,1),            -- minimum bounding width to detect narrow strip plots
  geom          geometry(Polygon,4326) NOT NULL,
  geom_utm      geometry(Polygon,32643) NOT NULL,
  crop          TEXT,                    -- nullable; falls back to spectral phenology cluster
  sowing_date   DATE,
  spectral_cluster INT,                  -- pre-monsoon NDVI trajectory k-NN cluster ID
  soil_class    TEXT,
  is_synthetic  BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_parcels_geom_utm ON parcels USING GIST (geom_utm);
CREATE INDEX idx_parcels_lookup ON parcels (taluka, crop, spectral_cluster);

CREATE TABLE cases (
  case_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id      TEXT NOT NULL REFERENCES events(event_id),
  parcel_id     UUID NOT NULL REFERENCES parcels(parcel_id),
  farmer_ref    TEXT,                    -- Agri Stack Farmer ID or opaque token; NEVER Aadhaar
  status        TEXT NOT NULL DEFAULT 'open',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (event_id, parcel_id)
);

CREATE TABLE official_assessments (
  case_id        UUID PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  damage_lo      NUMERIC(4,3) NOT NULL CHECK (damage_lo BETWEEN 0 AND 1),
  damage_hi      NUMERIC(4,3) NOT NULL CHECK (damage_hi BETWEEN 0 AND 1),
  assessed_on    DATE NOT NULL,
  assessor_token TEXT NOT NULL,          -- pseudonymous officer/team token for cross-assessor peer rules
  method         TEXT
);

CREATE TABLE scene_observations (
  case_id          UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  sensor           TEXT NOT NULL,        -- 'S2_IMMEDIATE' | 'S2_DELAYED' | 'S1_SAR'
  scene_date       DATE NOT NULL,
  clear_frac       NUMERIC(4,3),
  n_eff_pixels     NUMERIC(7,2),         -- sum of sub-pixel overlap weights w_i
  ndvi_obs         NUMERIC(5,4),
  ndvi_exp         NUMERIC(5,4),
  ndvi_bare        NUMERIC(5,4),
  ndre_obs         NUMERIC(5,4),
  ndmi_obs         NUMERIC(5,4),
  deficit_farm     NUMERIC(5,3),         -- unclipped vigour deficit
  deficit_controls NUMERIC(5,3),
  loss_attr        NUMERIC(4,3),         -- clipped DiD mean loss
  area_dmg_frac    NUMERIC(4,3),         -- fraction of parcel area with deficit >= 0.35
  sar_change_db    NUMERIC(6,3),
  water_frac       NUMERIC(4,3),
  PRIMARY KEY (case_id, sensor, scene_date)
);

CREATE TABLE observed_estimates (
  case_id   UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  source    TEXT NOT NULL CHECK (source IN ('satellite', 'ground')),
  value     NUMERIC(4,3) NOT NULL,
  sigma     NUMERIC(4,3) NOT NULL,
  ci_lo     NUMERIC(4,3) NOT NULL,
  ci_hi     NUMERIC(4,3) NOT NULL,
  quality   JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (case_id, source)
);

CREATE TABLE hazard_context (
  case_id                   UUID PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  rain_24h_max_mm           NUMERIC(6,1),
  rain_imd_class            TEXT,
  rain_percentile           NUMERIC(5,2),
  antecedent_30d_percentile NUMERIC(5,2),
  discharge_exposure        JSONB,
  hand_m                    NUMERIC(5,2),
  twi                       NUMERIC(5,2),
  hand_pctile_in_taluka     NUMERIC(5,2),
  soil_class                TEXT,
  plausibility              TEXT CHECK (plausibility IN ('LOW', 'MODERATE', 'HIGH'))
);

CREATE TABLE detections (
  case_id            UUID PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  pooling_status     TEXT NOT NULL,      -- 'OK' | 'SOURCE_CONFLICT' | 'SAT_ONLY' | 'NO_OBSERVATION'
  pooled_value       NUMERIC(4,3),
  pooled_lo          NUMERIC(4,3),
  pooled_hi          NUMERIC(4,3),
  ref_lo             NUMERIC(4,3),       -- equals pooled_lo (or sat_lo on SOURCE_CONFLICT)
  ref_hi             NUMERIC(4,3),
  gap                NUMERIC(5,3),
  intervals_separated BOOLEAN,
  boundary_crossing  TEXT,               -- 'NONE' | 'SAT_UNDER_RISK' | 'GROUND_DRIVEN_BOUNDARY_CROSSING' | 'OVER_RISK'
  peer_n             INT,
  peer_external_frac NUMERIC(4,3),
  peer_z             NUMERIC(6,2),
  cluster_bias_flag  BOOLEAN DEFAULT FALSE,
  timing_rho         NUMERIC(4,2),
  tier               TEXT NOT NULL,
  grade              TEXT NOT NULL,
  grade_points       INT NOT NULL,
  grade_detail       JSONB NOT NULL,
  factors            JSONB NOT NULL,
  data_availability  JSONB NOT NULL,
  model_versions     JSONB NOT NULL,
  computed_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE photos (
  photo_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  captured_at         TIMESTAMPTZ NOT NULL,
  server_received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  lat                 DOUBLE PRECISION NOT NULL,
  lon                 DOUBLE PRECISION NOT NULL,
  acc_m               REAL NOT NULL,
  compass_azimuth_deg REAL,              -- 0..360 magnetic/true north heading
  pitch_deg           REAL,              -- 65..88 deg upright field view check
  frustum_overlap     NUMERIC(4,3),      -- fraction of viewing cone inside own parcel
  burst_parallax_ok   BOOLEAN,           -- 3-frame optical flow vs flat screen check
  moire_score         REAL,              -- 2D FFT high-frequency screen artifact score
  phash               BIGINT,
  embedding           vector(512),       -- CLIP/SigLIP normalized embedding for deduplication
  dup_of              UUID REFERENCES photos(photo_id),
  dup_similarity      REAL,
  in_app_capture      BOOLEAN NOT NULL,
  crop_match_ok       BOOLEAN,
  verification_tier   INT NOT NULL,      -- 1 (sigma=0.14), 2 (sigma=0.22), 3 (excluded/0.35)
  zero_shot           JSONB
);
CREATE INDEX idx_photos_embedding ON photos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TABLE audit_log (
  id             BIGSERIAL PRIMARY KEY,
  ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
  case_id        UUID NOT NULL REFERENCES cases(case_id),
  actor          TEXT NOT NULL,
  event          TEXT NOT NULL,
  payload        JSONB NOT NULL,
  model_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
  prev_hash      BYTEA,
  row_hash       BYTEA NOT NULL
);

-- Timezone-independent, delimiter-safe SHA-256 hash chain
CREATE OR REPLACE FUNCTION audit_chain() RETURNS trigger AS $$
DECLARE
  last_h BYTEA;
  canonical_json TEXT;
BEGIN
  PERFORM pg_advisory_xact_lock(424242);
  SELECT row_hash INTO last_h FROM audit_log ORDER BY id DESC LIMIT 1;
  NEW.prev_hash := last_h;
  canonical_json := jsonb_build_array(
    NEW.case_id::text,
    NEW.actor,
    NEW.event,
    NEW.payload,
    COALESCE(NEW.model_versions, '{}'::jsonb),
    to_char(NEW.ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
  )::text;
  NEW.row_hash := digest(
    COALESCE(last_h, ''::bytea) || convert_to(canonical_json, 'UTF8'),
    'sha256'
  );
  RETURN NEW;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_chain BEFORE INSERT ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_chain();

CREATE OR REPLACE FUNCTION audit_block() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'audit_log is append-only'; END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_block BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION audit_block();

```

### PostGIS camera viewing-frustum helper function

To verify whether a farmer's camera is actually pointing into their own parcel (`geom_utm` in `EPSG:32643`), add this SQL function:

```
CREATE OR REPLACE FUNCTION compute_frustum_overlap(
  user_lon DOUBLE PRECISION,
  user_lat DOUBLE PRECISION,
  azimuth_deg DOUBLE PRECISION,
  cone_half_angle_deg DOUBLE PRECISION,
  range_m DOUBLE PRECISION,
  parcel_geom_utm geometry
) RETURNS NUMERIC AS $$
DECLARE
  pt_wgs geometry;
  pt_utm geometry;
  az_rad DOUBLE PRECISION;
  half_rad DOUBLE PRECISION;
  p1 geometry;
  p2 geometry;
  p3 geometry;
  frustum geometry;
  inter_area DOUBLE PRECISION;
BEGIN
  IF azimuth_deg IS NULL THEN RETURN 0.0; END IF;
  pt_wgs := ST_SetSRID(ST_MakePoint(user_lon, user_lat), 4326);
  pt_utm := ST_Transform(pt_wgs, 32643);
  -- Convert geographic azimuth (0=N, 90=E) to mathematical angle in UTM plane
  az_rad := radians(90.0 - azimuth_deg);
  half_rad := radians(cone_half_angle_deg);
  p1 := ST_Translate(pt_utm, range_m * cos(az_rad - half_rad), range_m * sin(az_rad - half_rad));
  p2 := ST_Translate(pt_utm, range_m * cos(az_rad),            range_m * sin(az_rad));
  p3 := ST_Translate(pt_utm, range_m * cos(az_rad + half_rad), range_m * sin(az_rad + half_rad));
  frustum := ST_SetSRID(ST_MakePolygon(ST_MakeLine(ARRAY[pt_utm, p1, p2, p3, pt_utm])), 32643);
  inter_area := ST_Area(ST_Intersection(frustum, parcel_geom_utm));
  RETURN ROUND((inter_area / NULLIF(ST_Area(frustum), 0))::numeric, 3);
END $$ LANGUAGE plpgsql IMMUTABLE;

```

## 7. Module specifications (v3)

All numeric thresholds marked 🎯 are **initial settings** stored in `config/defaults.yaml` and tuned via the injection benchmark (§11.2).

### 7.1 Parcel preparation, sub-pixel weights, peers and controls

**Sub-pixel extraction for narrow strip plots:**
Instead of a rigid `-10 m` inner buffer that erases 20–30 m wide riverside strip parcels, compute the minimum bounding width $W_{\text{min}}$ of `geom_utm`.

* If $W_{\text{min}} \ge 35\text{ m}$, apply a `-5 m` inner buffer to drop mixed boundary bunds, then compute pixel-polygon fractional overlap weights $w_i \in (0, 1]$.

* If $W_{\text{min}} < 35\text{ m}$ (strip parcel), apply **no negative buffer**; instead extract all pixels with overlap fraction $w_i \ge 0.50$ and weight each pixel by $w_i^2$ (favoring centerline pixels).

* Define effective pixel count $n_{\text{eff}} = \sum w_i$.

| $n_{\text{eff}}$ | Spatial reliability | Action | 
| ----- | ----- | ----- | 
| $\ge 25.0$ | High (2 grade pts) | Full parcel-level + sub-parcel area analysis | 
| $8.0\text{–}24.9$ | Medium (1 grade pt) | Full analysis, 1-point spatial grade deduction | 
| $< 8.0$ | Low (0 grade pts) | Flag `SMALL_PARCEL_LIMITATION`; cap grade at C; require ground or cluster corroboration | 

**Cross-assessor peer query with spectral fallback:**
Select up to 60 candidate parcels within 15 km that share either `(crop, sowing_date ± 10d)` **or** (when `crop`/`sowing_date` is null) the same `spectral_cluster` (k-NN cluster on May–June pre-event NDVI time series), and filter to those with similar observed satellite loss ($|V_{\text{sat,peer}} - V_{\text{sat}}| \le 0.15$).

* **Anti-blanket-panchnama constraint:** Cap peers from the **same `assessor_token`** at 50% of the peer pool so a single officer's uniform village entry cannot dominate the peer median.

### 7.2 Satellite observation (unclipped DiD, dual loss & SAR bimodality gate)

```
import numpy as np
from skimage.filters import threshold_otsu

def compute_satellite_loss(
    ndvi_obs: np.ndarray,
    ndvi_exp: np.ndarray,
    ndvi_bare: np.ndarray,
    weights: np.ndarray,
    ctrl_deficits: np.ndarray,
    dmg_threshold: float = 0.35,
    denom_floor: float = 0.05,
):
    """
    Computes unclipped Difference-in-Differences (DiD) canopy loss and damaged area fraction.
    Eliminates v2 truncation bias by clipping only after control subtraction.
    """
    valid = np.isfinite(ndvi_obs) & (weights >= 0.5)
    if valid.sum() == 0:
        return None

    denom = np.maximum(ndvi_exp[valid] - ndvi_bare[valid], denom_floor)
    pixel_deficit = (ndvi_exp[valid] - ndvi_obs[valid]) / denom  # unclipped!
    w = weights[valid]

    farm_deficit = float(np.sum(w * pixel_deficit) / np.sum(w))
    ctrl_median_deficit = float(np.nanmedian(ctrl_deficits))     # unclipped controls!

    # Attributable loss clipped only AFTER subtracting control median
    loss_attr = float(np.clip(farm_deficit - ctrl_median_deficit, 0.0, 1.0))

    # Damaged area fraction: share of parcel area with flood-attributable deficit >= 0.35
    pixel_attr = pixel_deficit - ctrl_median_deficit
    area_dmg_frac = float(np.sum(w * (pixel_attr >= dmg_threshold)) / np.sum(w))

    # Primary satellite proxy takes the higher of mean canopy loss or severely damaged area share
    v_sat = max(loss_attr, area_dmg_frac)
    return {
        "deficit_farm": round(farm_deficit, 4),
        "deficit_controls": round(ctrl_median_deficit, 4),
        "loss_attr": round(loss_attr, 4),
        "area_dmg_frac": round(area_dmg_frac, 4),
        "v_sat": round(v_sat, 4),
        "n_eff": round(float(np.sum(w)), 2),
    }

def ashman_d(vals: np.ndarray, thresh: float) -> float:
    """Ashman's D statistic (> 2.0 required for clean bimodal separation)."""
    g1, g2 = vals[vals <= thresh], vals[vals > thresh]
    if len(g1) < 10 or len(g2) < 10:
        return 0.0
    m1, m2 = np.mean(g1), np.mean(g2)
    s1, s2 = np.std(g1), np.std(g2)
    return float(np.sqrt(2.0) * abs(m1 - m2) / np.sqrt(max(s1**2 + s2**2, 1e-6)))

def sar_water_fraction(
    vv_pre_db: np.ndarray,
    vv_post_db: np.ndarray,
    vh_post_db: np.ndarray,
    hand_m: np.ndarray,
    ndvi_pre: np.ndarray,
    ctrl_delta_vv_median: float,
    window_delta_vv: np.ndarray,
) -> float:
    """
    Computes parcel SAR inundation fraction combining open-water backscatter drop
    and terrain-gated double-bounce increase.
    """
    delta_vv = vv_post_db - vv_pre_db
    clean_win = window_delta_vv[np.isfinite(window_delta_vv)]
    otsu_t = threshold_otsu(clean_win) if len(clean_win) > 50 else -3.0
    use_otsu = ashman_d(clean_win, otsu_t) > 2.0
    drop_thresh = min(float(otsu_t), -2.5) if use_otsu else -3.0

    open_water = (delta_vv <= drop_thresh) & (vh_post_db <= -20.0)
    double_bounce = (
        (hand_m <= 4.0)
        & (ndvi_pre >= 0.35)
        & ((delta_vv - ctrl_delta_vv_median) >= 2.5)
    )
    inundated = open_water | double_bounce
    return float(np.mean(inundated))

```

### 7.3 Hazard context

Computed identically to v2 (§3 D12) and stored in `hazard_context`. Never pooled into the damage percentage.

### 7.4 Ground evidence & multi-layer photo verification

1. Execute the 6-layer photo verification pipeline (D9):

   * Compute `frustum_overlap = compute_frustum_overlap(lon, lat, compass_azimuth_deg, 25.0, 60.0, parcel.geom_utm)`.

   * Verify pitch $\beta \in [65^\circ, 88^\circ]$ and two-photo spatial/angular separation ($\ge 15\text{ m}$ or $\ge 35^\circ$).

   * Verify 3-frame burst optical flow parallax (`burst_parallax_ok = True`) and 2D FFT screen Moiré score below threshold.

   * Query `pgvector` for nearest embedding across other cases (`SELECT photo_id, 1 - (embedding <=> :emb) AS sim FROM photos WHERE case_id <> :case_id ORDER BY embedding <=> :emb LIMIT 1`). If `sim >= 0.92`, flag `DUPLICATE_PHOTO_EMBEDDING`.

   * Verify zero-shot crop class compatibility with `parcel.crop`.

2. Assign $\sigma_{\text{ground}}$:

   * Tier 1 ($\ge 2$ photos passing all checks): $\sigma_{\text{ground}} = 0.14$.

   * Tier 2 (in-app GPS valid, no duplicates, but compass missing/partial frustum): $\sigma_{\text{ground}} = 0.22$.

   * Tier 3 (duplicate embedding or Moiré screen spoof detected): exclude ground estimate from pooling and trigger `PHOTO_INTEGRITY_ALERT`.

### 7.6 Pooling & 33% boundary-surfing guard

```
import numpy as np

def reconcile_observations(sat: dict | None, ground: dict | None, boundary: float = 0.33):
    """
    sat / ground: {"value": float, "sigma": float, "lo": float, "hi": float}
    Returns pooled estimate AND reference interval for downstream detectors.
    Never leaves reference interval undefined when SOURCE_CONFLICT occurs.
    """
    if not sat and not ground:
        return {"status": "NO_OBSERVATION", "value": None, "sigma": None, "lo": None, "hi": None,
                "ref_lo": None, "ref_hi": None, "ground_driven_crossing": False}

    if sat and not ground:
        return {"status": "SAT_ONLY", **sat, "ref_lo": sat["lo"], "ref_hi": sat["hi"],
                "ground_driven_crossing": False}

    if ground and not sat:
        return {"status": "GROUND_ONLY", **ground, "ref_lo": ground["lo"], "ref_hi": ground["hi"],
                "ground_driven_crossing": True}

    # Both present: check 2-sigma conflict rule
    comb_sigma = float(np.sqrt(sat["sigma"] ** 2 + ground["sigma"] ** 2))
    if abs(sat["value"] - ground["value"]) > 2.0 * comb_sigma:
        # Do NOT average conflicting sources, but keep satellite interval as reference so detectors run!
        return {
            "status": "SOURCE_CONFLICT",
            "value": sat["value"],
            "sigma": sat["sigma"],
            "lo": sat["lo"],
            "hi": sat["hi"],
            "ref_lo": sat["lo"],
            "ref_hi": sat["hi"],
            "sat": sat,
            "ground": ground,
            "ground_driven_crossing": False,
        }

    w_s = 1.0 / (sat["sigma"] ** 2)
    w_g = 1.0 / (ground["sigma"] ** 2)
    val = float((w_s * sat["value"] + w_g * ground["value"]) / (w_s + w_g))
    sig = float(np.sqrt(1.0 / (w_s + w_g)))
    lo = max(0.0, val - 1.28 * sig)
    hi = min(1.0, val + 1.28 * sig)

    # Detect 33% threshold-surfing where satellite alone is below 0.33
    ground_driven_crossing = (sat["value"] < boundary) and (val >= boundary)
    return {
        "status": "OK",
        "value": round(val, 4),
        "sigma": round(sig, 4),
        "lo": round(lo, 4),
        "hi": round(hi, 4),
        "ref_lo": round(lo, 4),
        "ref_hi": round(hi, 4),
        "ground_driven_crossing": ground_driven_crossing,
    }

```

### 7.7 Detectors and tiers (v3)

* **Detector A (Interval Separation & Boundary Risk):**

  * Uses `[ref_lo, ref_hi]` against `[O_lo, O_hi]`.

  * `SAT_UNDER_RISK`: $O_{\text{hi}} < 0.33$ and $V_{\text{sat,lo}} \ge 0.33$.

  * `GROUND_DRIVEN_BOUNDARY_CROSSING`: $O_{\text{hi}} < 0.33$, $V_{\text{sat}} < 0.33$, and $P_{\text{lo}} \ge 0.33$.

  * `OVER_RISK`: $O_{\text{lo}} \ge 0.33$ and $\text{ref\_hi} < 0.33$.

* **Detector B (Cross-Assessor Peer Discordance):**

  * Robust $z$-score of official damage against peers ($\ge 50\%$ external `assessor_token`). Fires when $|z| \ge 2.0$.

* **Detector C (Timing Gradient):**

  * Partial Spearman $\rho$ between `delay_days` and $(O - V_{\text{sat}})$ controlling for `hand_m`. Fires when $\rho \le -0.40, p < 0.05$, and parcel delay is in top tercile.

* **Detector D (Assessor / Village Blanket Cluster Bias — `CLUSTER_BIAS`):**

  * Fires when $\ge 5$ parcels assessed by the same `assessor_token` on the same date have $\text{IQR}(O) \le 0.05$ (nearly identical official numbers) and median $(V_{\text{sat,lo}} - O_{\text{hi}}) \ge 0.20$.

**Tier assignment rules 🎯:**

* `PRIORITY_REVIEW`: (`SAT_UNDER_RISK` and (Detector B or Detector D fires)) **or** (Detector A separated by $\ge 0.25$ and Grade A/B and (Detector B or Detector D fires)).

* `REVIEW`: Detector A separated ($\text{gap} \ge 0.20$), **or** `SAT_UNDER_RISK`, **or** `GROUND_DRIVEN_BOUNDARY_CROSSING`, **or** Detector B fires, **or** Detector D fires, **or** `SOURCE_CONFLICT` with gap $\ge 0.20$.

* `NOTE`: $|\text{gap}| \ge 0.10$ with overlapping intervals, or $1.5 \le |z| < 2.0$.

* `CONSISTENT`: None of A/B/C/D fires and Grade $\in \{\text{A, B, C}\}$.

* `INSUFFICIENT_EVIDENCE`: Grade D.

### 7.8 Contributing-factor screen (v3 expanded codes)

| Code | Trigger 🎯 | Evidence Shown | 
| ----- | ----- | ----- | 
| `LATE_ASSESSMENT` | delay $\ge 7\text{ d}$ and SAR/NDWI water receded by assessment date and `TIMING_GRADIENT` | delay days, water_frac peak vs assessment date, $\rho$ | 
| `PEER_INCONSISTENCY` | Detector B fires (\$ | z | 
| `BLANKET_PANCHNAMA_CLUSTER` | Detector D (`CLUSTER_BIAS`) fires for this `assessor_token`/village | cluster size, assessor IQR, median gap | 
| `PARTIAL_PARCEL_SUBMERGENCE` | $A_{\text{dmg}} - L_{\text{attr}} \ge 0.15$ (severe localized riverbank loss on strip plot) | $A_{\text{dmg}}$, $L_{\text{attr}}$, sub-parcel map | 
| `SILT_RECOVERY_OBSERVED` | Immediate scene shows loss $\ge 0.35$, but Day +10..16 scene shows `NDRE` rebound $\ge 0.12$ | Window 1 vs Window 2 `NDVI`/`NDRE` | 
| `DELAYED_WATERLOGGING_ROT` | Immediate scene loss $< 0.20$, but Day +10..16 scene shows progressive drop $\ge 0.35$ in black soil | Window 1 vs Window 2 `NDVI`/`NDMI`, soil class | 
| `DISCHARGE_EXPOSURE` | Parcel within river reach of reported dam release and `hand_pctile` $\le 25$ | release cusecs, distance, HAND | 
| `GROUND_DRIVEN_BOUNDARY_CROSSING` | $V_{\text{sat}} < 0.33$ pulled over $0.33$ by farmer report | $V_{\text{sat}}, V_{\text{ground}}, P$ | 
| `PHOTO_INTEGRITY_ALERT` | Duplicate `pgvector` embedding ($\ge 0.92$), Moiré screen spoof, or frustum pointing outside parcel | similarity score, frustum overlap, azimuth | 
| `CROP_MISMATCH` | Zero-shot photo crop class contradicts 7/12 / e-Peek Pahani crop | declared crop vs detected visual class | 
| `SOURCE_CONFLICT` | \$ | V\_{\\text{sat}} - V\_{\\text{ground}} | 
| `NON_FLOOD_CAUSE_POSSIBLE` | Onset outside flood window, or controls show equal loss, or hazard plausibility `LOW` | onset date, control deficit, plausibility | 

### 7.10 Report generation & v3 Devanagari/percentage-aware numeric verifier

```
import re

DEVANAGARI_MAP = str.maketrans("०१२३४५६७८९", "0123456789")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")
DATE_STR_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

def _collect_allowed_numbers(obj) -> set[str]:
    """
    Collects all valid numeric tokens from facts JSON, including:
    - raw values rounded to 0..3 decimals
    - percentage equivalents (x * 100) for ratios in [0, 1]
    - integer day/month/year tokens from ISO date strings
    """
    allowed = {"33", "80", "90", "95", "10"}  # standard policy/interval constants
    def _walk(item):
        if isinstance(item, bool) or item is None:
            return
        if isinstance(item, (int, float)):
            val = float(item)
            for d in (0, 1, 2, 3):
                s = f"{round(val, d):.{d}f}".rstrip("0").rstrip(".") if d > 0 else str(int(round(val)))
                allowed.add(s or "0")
            if 0.0 <= abs(val) <= 1.0:
                pct = val * 100.0
                for d in (0, 1):
                    sp = f"{round(pct, d):.{d}f}".rstrip("0").rstrip(".") if d > 0 else str(int(round(pct)))
                    allowed.add(sp or "0")
        elif isinstance(item, str):
            for y, m, day in DATE_STR_RE.findall(item):
                allowed.update({y, str(int(m)), str(int(day))})
            for tok in NUM_RE.findall(item.translate(DEVANAGARI_MAP)):
                allowed.add(tok)
        elif isinstance(item, dict):
            for v in item.values():
                _walk(v)
        elif isinstance(item, (list, tuple)):
            for v in item:
                _walk(v)
    _walk(obj)
    return allowed

def verify_llm_report(text: str, facts: dict) -> bool:
    """
    1. Normalizes Devanagari digits (०-९ -> 0-9).
    2. Verifies every numeric token in text exists in allowed facts set (including % conversions).
    3. Verifies directional consistency (cannot swap official and observed percentages).
    """
    norm_text = text.translate(DEVANAGARI_MAP)
    allowed = _collect_allowed_numbers(facts)
    tokens = NUM_RE.findall(norm_text)
    if not all(t in allowed for t in tokens):
        return False

    # Directional swap check: if official != observed, ensure official_pct appears before observed_pct
    # when template structure states official record first
    off_pct = str(int(round(facts.get("official_mid", 0) * 100)))
    obs_pct = str(int(round(facts.get("observed_val", 0) * 100)))
    if off_pct != obs_pct and off_pct in tokens and obs_pct in tokens:
        # Check against hallucinated reversal such as "official record is <obs_pct>%"
        bad_pattern = re.compile(rf"(?:official|अधिकृत|पंचनामा)[^.\n]{{0,25}}\b{re.escape(obs_pct)}\s*%")
        if bad_pattern.search(norm_text.lower()):
            return False
    return True

```

## 8. API (v3 minimum set)

| Method | Path | Purpose | 
| ----- | ----- | ----- | 
| POST | `/cases` | Create or update case (event, parcel, official record) | 
| POST | `/cases/{id}/ground` | Submit structured ground report + burst photos with GPS/compass telemetry | 
| POST | `/cases/{id}/analyze` | Run idempotent v3 pipeline (`UPSERT`s estimates/detections; appends hash-chained audit log) | 
| GET | `/cases/{id}` | Full detection JSON: intervals, sub-parcel area loss, frustum map, factors, grade, data gaps | 
| GET | `/cases/{id}/report?lang=mr` | Render verified Marathi or English report (`mr` / `en`) | 
| GET | `/events/{id}/queue` | Review queue ordered by tier, grade points, and cluster bias | 
| GET | `/events/{id}/fairness` | Flag rate, Grade-D share, and cluster-bias count by taluka, crop, and strip-parcel width band | 
| POST | `/cases/{id}/review` | Record officer decision + mandatory reason code on priority override | 
| GET | `/audit/verify` | Run full cryptographic hash-chain verification across `audit_log` | 

## 9. Dashboard and farmer channel (v3 upgrades)

1. **Evidence Ladder Chart:** Horizontal forest plot showing `official [O_lo, O_hi]`, `satellite mean loss [lo, hi]`, `satellite damaged area fraction`, `ground report [lo, hi]`, `pooled/reference [ref_lo, ref_hi]`, and `cross-assessor peer median [IQR]`, with the vertical 33% line.

2. **Sub-Parcel Heatmap & Camera Frustum Map Overlay:** On the Leaflet parcel view, render the 10 m Sentinel-2 pixel deficit grid inside the parcel polygon **plus** the green/red 60 m triangular viewing frustums of the farmer's uploaded photos so the reviewing officer immediately sees where the farmer stood and which way the camera pointed.

## 10. Worked example 🧪 (v3 arithmetic with unclipped DiD & frustum verification)

**Event:** Pune district, 24–26 July 2024, peak 25 July (Khadakwasla release \~35,000–40,000 cusecs) ✅.
**Parcel PUN-HAV-0001 (synthetic):** soybean, sown 28 June 2024, 1.4 ha riverside ribbon parcel ($32\text{ m} \times 435\text{ m}$) along the Mula-Mutha reach, effective pixel count $n_{\text{eff}} = 94.2$ (clear fraction 0.72).

| Input / Step | v3 Computed Value | 
| ----- | ----- | 
| **Official record** | 20% ($\pm 0.05 \rightarrow [0.15, 0.25]$), assessed 7 Aug 2024 (**delay 13 days**), `assessor_token = 'ASR-14'` | 
| **Satellite (S-2, 3 Aug & 13 Aug)** | $E = 0.54, O = 0.22, B = 0.12 \rightarrow$ unclipped parcel deficit $\bar{d}_{\text{farm}} = (0.54 - 0.22)/(0.54 - 0.12) = \mathbf{0.76}$ | 
| **Controls (11 upland parcels)** | Unclipped control deficits range from $-0.09$ to $+0.11$; **unclipped median** $d_{\text{ctrl}} = +0.02$ (zero truncation bias!) | 
| **Attributable loss & area** | Mean attributable loss $L_{\text{attr}} = \text{clip}(0.76 - 0.02, 0, 1) = \mathbf{0.74}$. Damaged area fraction $A_{\text{dmg}} = \mathbf{0.78}$ (lower 78% of strip submerged). $V_{\text{sat}} = \mathbf{0.78}$, block-bootstrap 80% CI $[0.67, 0.89] \rightarrow \sigma_{\text{sat}} = \mathbf{0.086}$ | 
| **Delayed scene check (13 Aug)** | `NDRE` remained depressed ($0.14$, no silt rebound) $\rightarrow$ permanent flood/waterlogging loss confirmed | 
| **SAR (S-1A)** | Lee-filtered $\Delta\text{VV} = -4.1\text{ dB}$, Ashman's $D = 2.64 > 2.0$, `water_frac` $= 0.68$ on peak pass, $0.03$ by 8 Aug | 
| **Ground report & photo check** | Farmer reports 75% ($0.75$). 2 in-app burst photos: GPS 6 m from west boundary, compass azimuth $\alpha_1 = 112^\circ, \alpha_2 = 148^\circ$ pointing into parcel (`frustum_overlap` $= 0.84$ and $0.79$), pitch $\beta = 76^\circ$, 3-frame parallax valid, `pgvector` max similarity across taluka $= 0.41$ (unique), zero-shot matches flooded soybean $\rightarrow$ **Tier 1 Verified (**$\sigma_{\text{ground}} = 0.14$**)** | 
| **Pooling** | \$ | 
| **Detectors** | **A:** Official $[0.15, 0.25]$ vs Observed $[0.68, 0.86] \rightarrow$ separated, gap $= +0.57$, `SAT_UNDER_RISK`. **B:** 20 peers (12 from external assessors), peer median $= 0.60$, MAD $= 0.09 \rightarrow z = (0.20 - 0.60)/(1.4826 \times 0.09) = \mathbf{-3.00}$. **D:** 7 riverside plots under `ASR-14` all recorded at flat 20% with median gap $+0.46 \rightarrow$ `CLUSTER_BIAS` fires | 
| **Grade & Tier** | Coverage 3 + Spatial 2 ($n_{\text{eff}} = 94.2$) + Agreement 2 + Attribution 2 + Margin 1 = **10/10 (Grade A)** $\rightarrow$ **`PRIORITY_REVIEW`** | 

## 11. Validation, privacy, build plan & references

Sections 11–15 and Appendices A–B from v2 apply in full, augmented with the v3 benchmarks (testing photo frustum rejection, narrow strip-parcel recovery, unclipped DiD bias elimination, and Devanagari/percentage report verification) detailed in the companion **`Reconciliation_AI_Detailed_Implementation_Plan.md`**.

## Appendix — Updated `config/defaults.yaml` (v3 🎯)

```
parcel:
  min_width_for_buffer_m: 35.0
  adaptive_buffer_m: 5.0
  min_overlap_weight: 0.50
  min_eff_pixels: 8.0
  high_reliability_eff_pixels: 25.0
peers:
  radius_km: 15.0
  sowing_window_days: 10
  observed_similarity: 0.15
  min_peers: 8
  min_external_assessor_frac: 0.50
controls:
  radius_km: [10.0, 25.0]
  min_controls: 5
satellite:
  min_clear_fraction: 0.40
  bare_ndvi_default: 0.12
  denom_floor: 0.05
  damaged_area_pixel_threshold: 0.35
  silt_ndre_rebound_threshold: 0.12
  bootstrap_block: 3
  sigma_floor: 0.05
  onset_threshold: 0.15
  onset_window_days: [-2, 14]
sar:
  lee_window: 3
  ashman_d_min: 2.0
  open_water_vv_drop_db: -2.5
  open_water_vh_max_db: -20.0
  double_bounce_hand_max_m: 4.0
  double_bounce_ndvi_pre_min: 0.35
  double_bounce_ctrl_excess_db: 2.5
ground:
  sigma_tier1_verified: 0.14
  sigma_tier2_partial: 0.22
  sigma_tier3_unverified: 0.35
  photo_max_boundary_dist_m: 15.0
  photo_max_accuracy_m: 25.0
  frustum_range_m: 60.0
  frustum_half_angle_deg: 25.0
  frustum_min_overlap: 0.40
  pitch_min_deg: 65.0
  pitch_max_deg: 88.0
  min_angle_sep_deg: 35.0
  min_pos_sep_m: 15.0
  pgvector_dup_cosine_threshold: 0.92
official:
  rounding_tolerance: 0.05
pooling:
  conflict_k: 2.0
  interval_z: 1.28
detectors:
  gap_note: 0.10
  gap_review: 0.20
  peer_z_note: 1.5
  peer_z_flag: 2.0
  cluster_min_cases: 5
  cluster_max_iqr: 0.05
  cluster_min_gap: 0.20
  timing_rho: -0.40
  timing_p: 0.05
  boundary: 0.33

```
