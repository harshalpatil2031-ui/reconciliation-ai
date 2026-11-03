CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS events (
  event_id      TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  start_date    DATE NOT NULL,
  peak_date     DATE NOT NULL,
  end_date      DATE NOT NULL,
  notes         TEXT
);

CREATE TABLE IF NOT EXISTS parcels (
  parcel_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  survey_no     TEXT NOT NULL,
  village       TEXT NOT NULL,
  taluka        TEXT NOT NULL,
  district      TEXT NOT NULL,
  area_ha       NUMERIC(8,3) NOT NULL,
  min_width_m   NUMERIC(6,1),
  geom          geometry(Polygon,4326) NOT NULL,
  geom_utm      geometry(Polygon,32643) NOT NULL,
  crop          TEXT,
  sowing_date   DATE,
  spectral_cluster INT,
  soil_class    TEXT,
  is_synthetic  BOOLEAN NOT NULL DEFAULT FALSE,
  role          TEXT NOT NULL DEFAULT 'case' CHECK (role IN ('case','control'))
);
CREATE INDEX IF NOT EXISTS idx_parcels_geom_utm ON parcels USING GIST (geom_utm);
CREATE INDEX IF NOT EXISTS idx_parcels_lookup ON parcels (taluka, crop, spectral_cluster);
CREATE INDEX IF NOT EXISTS idx_parcels_role ON parcels(role);

CREATE TABLE IF NOT EXISTS cases (
  case_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id      TEXT NOT NULL REFERENCES events(event_id),
  parcel_id     UUID NOT NULL REFERENCES parcels(parcel_id),
  farmer_ref    TEXT,
  status        TEXT NOT NULL DEFAULT 'open',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (event_id, parcel_id)
);

CREATE TABLE IF NOT EXISTS official_assessments (
  case_id        UUID PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  damage_lo      NUMERIC(4,3) NOT NULL CHECK (damage_lo BETWEEN 0 AND 1),
  damage_hi      NUMERIC(4,3) NOT NULL CHECK (damage_hi BETWEEN 0 AND 1),
  assessed_on    DATE NOT NULL,
  assessor_token TEXT NOT NULL,
  method         TEXT
);

CREATE TABLE IF NOT EXISTS scene_observations (
  case_id          UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  sensor           TEXT NOT NULL,
  scene_date       DATE NOT NULL,
  clear_frac       NUMERIC(4,3),
  n_eff_pixels     NUMERIC(7,2),
  pixel_weights    JSONB,
  ndvi_obs         NUMERIC(5,4),
  ndvi_exp         NUMERIC(5,4),
  ndvi_bare        NUMERIC(5,4),
  ndre_obs         NUMERIC(5,4),
  ndmi_obs         NUMERIC(5,4),
  deficit_farm     NUMERIC(5,3),
  deficit_controls NUMERIC(5,3),
  loss_attr        NUMERIC(4,3),
  area_dmg_frac    NUMERIC(4,3),
  sar_change_db    NUMERIC(6,3),
  water_frac       NUMERIC(4,3),
  quality          JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (case_id, sensor, scene_date)
);
ALTER TABLE scene_observations ADD COLUMN IF NOT EXISTS pixel_weights JSONB;
ALTER TABLE scene_observations ADD COLUMN IF NOT EXISTS quality JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS observed_estimates (
  case_id   UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  source    TEXT NOT NULL CHECK (source IN ('satellite', 'ground')),
  value     NUMERIC(4,3) NOT NULL,
  sigma     NUMERIC(4,3) NOT NULL,
  ci_lo     NUMERIC(4,3) NOT NULL,
  ci_hi     NUMERIC(4,3) NOT NULL,
  quality   JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (case_id, source)
);

CREATE TABLE IF NOT EXISTS hazard_context (
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

CREATE TABLE IF NOT EXISTS detections (
  case_id             UUID PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  pooling_status      TEXT NOT NULL CHECK (pooling_status IN ('OK','SOURCE_CONFLICT','SAT_ONLY','GROUND_ONLY','NO_OBSERVATION')),
  pooled_value        NUMERIC(4,3),
  pooled_lo           NUMERIC(4,3),
  pooled_hi           NUMERIC(4,3),
  ref_lo              NUMERIC(4,3),
  ref_hi              NUMERIC(4,3),
  gap                 NUMERIC(5,3),
  intervals_separated BOOLEAN,
  boundary_crossing   TEXT CHECK (boundary_crossing IN ('NONE','SAT_UNDER_RISK','GROUND_DRIVEN_BOUNDARY_CROSSING','OVER_RISK')),
  peer_n              INT,
  peer_external_frac  NUMERIC(4,3),
  peer_z              NUMERIC(6,2),
  cluster_bias_flag   BOOLEAN DEFAULT FALSE,
  timing_rho          NUMERIC(4,2),
  tier                TEXT NOT NULL CHECK (tier IN ('PRIORITY_REVIEW','REVIEW','NOTE','CONSISTENT','INSUFFICIENT_EVIDENCE')),
  grade               TEXT NOT NULL CHECK (grade IN ('A','B','C','D')),
  grade_points        INT NOT NULL,
  grade_detail        JSONB NOT NULL,
  factors             JSONB NOT NULL,
  data_availability   JSONB NOT NULL,
  model_versions      JSONB NOT NULL,
  computed_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS photos (
  photo_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  captured_at         TIMESTAMPTZ NOT NULL,
  server_received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  lat                 DOUBLE PRECISION NOT NULL,
  lon                 DOUBLE PRECISION NOT NULL,
  acc_m               REAL NOT NULL,
  compass_azimuth_deg REAL,
  pitch_deg           REAL,
  frustum_overlap     NUMERIC(4,3),
  burst_parallax_ok   BOOLEAN,
  moire_score         REAL,
  phash               BIGINT,
  embedding           vector(512),
  dup_of              UUID REFERENCES photos(photo_id),
  dup_similarity      REAL,
  in_app_capture      BOOLEAN NOT NULL,
  crop_match_ok       BOOLEAN,
  verification_tier   INT NOT NULL CHECK (verification_tier IN (1,2,3)),
  zero_shot           JSONB
);
CREATE INDEX IF NOT EXISTS idx_photos_embedding ON photos USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TABLE IF NOT EXISTS audit_log (
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

CREATE TABLE IF NOT EXISTS reviews (
  review_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id           UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  officer_token     TEXT NOT NULL,
  decision          TEXT NOT NULL CHECK (decision IN ('CONFIRM_FLAG','DISMISS_FLAG','ESCALATE','REQUEST_FIELD_VISIT')),
  reason_code       TEXT CHECK (reason_code IN ('SATELLITE_EVIDENCE_ACCEPTED','SATELLITE_EVIDENCE_REJECTED','PHOTO_FRAUD_SUSPECTED','ASSESSOR_BIAS_CONFIRMED','DATA_QUALITY_ISSUE','OTHER')),
  priority_override BOOLEAN NOT NULL DEFAULT FALSE,
  note              TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (NOT priority_override OR reason_code IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_reviews_case ON reviews(case_id, created_at DESC);

CREATE OR REPLACE VIEW v_case_base AS
SELECT c.case_id, c.event_id, c.parcel_id, c.farmer_ref, c.status,
       p.survey_no, p.village, p.taluka, p.district, p.area_ha, p.min_width_m,
       p.geom, p.geom_utm, p.crop, p.sowing_date, p.spectral_cluster, p.soil_class,
       o.damage_lo, o.damage_hi, (o.damage_lo + o.damage_hi) / 2.0 AS official_mid,
       o.assessed_on, o.assessor_token,
       (o.assessed_on - e.peak_date) AS delay_days,
       h.hand_m, h.twi, h.hand_pctile_in_taluka, h.plausibility, h.rain_imd_class
FROM cases c
JOIN parcels p ON p.parcel_id = c.parcel_id
JOIN events e ON e.event_id = c.event_id
LEFT JOIN official_assessments o ON o.case_id = c.case_id
LEFT JOIN hazard_context h ON h.case_id = c.case_id;
