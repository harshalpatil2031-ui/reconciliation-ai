"""Typed, immutable application settings loaded from defaults.yaml."""

from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "defaults.yaml"


class FrozenSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ParcelSettings(FrozenSettings):
    min_width_for_buffer_m: float
    adaptive_buffer_m: float
    min_overlap_weight_large: float
    min_overlap_weight_strip: float
    min_eff_pixels: float
    high_reliability_eff_pixels: float
    supersample: int


class PeerSettings(FrozenSettings):
    radius_km: float
    sowing_window_days: int
    observed_similarity: float
    min_peers: int
    max_candidates: int
    min_external_assessor_frac: float


class ControlSettings(FrozenSettings):
    radius_km: tuple[float, float]
    min_controls: int
    min_hand_m: float
    max_sar_water_frac: float


class SatelliteSettings(FrozenSettings):
    window1_days: tuple[int, int]
    window2_days: tuple[int, int]
    min_clear_fraction: float
    bare_ndvi_default: float
    denom_floor: float
    damaged_area_pixel_threshold: float
    standing_water_ndwi: float
    silt_ndre_rebound_threshold: float
    silt_w1_loss_min: float
    silt_w2_loss_max: float
    rot_w1_loss_max: float
    rot_w2_loss_min: float
    rot_ndmi_drop: float
    bootstrap_block: int
    bootstrap_n: int
    sigma_floor: float
    interval_percentiles: tuple[int, int]
    onset_threshold: float
    onset_window_days: tuple[int, int]


class SarSettings(FrozenSettings):
    lee_window: int
    ashman_d_min: float
    open_water_vv_drop_db: float
    open_water_vh_max_db: float
    fallback_vv_drop_db: float
    double_bounce_hand_max_m: float
    double_bounce_ndvi_pre_min: float
    double_bounce_ctrl_excess_db: float


class HazardSettings(FrozenSettings):
    heavy_rain_mm: float
    discharge_hand_pctile_max: float
    low_plausibility_hand_pctile_min: float


class GroundSettings(FrozenSettings):
    sigma_tier1_verified: float
    sigma_tier2_partial: float
    sigma_tier3_unverified: float
    photo_max_boundary_dist_m: float
    photo_max_accuracy_m: float
    frustum_range_m: float
    frustum_half_angle_deg: float
    frustum_min_overlap: float
    pitch_min_deg: float
    pitch_max_deg: float
    min_angle_sep_deg: float
    min_pos_sep_m: float
    pgvector_dup_cosine_threshold: float
    moire_max: float
    parallax_ratio_min: float
    fg_motion_range_px: tuple[float, float]


class OfficialSettings(FrozenSettings):
    rounding_tolerance: float


class PoolingSettings(FrozenSettings):
    conflict_k: float
    interval_z: float


class DetectorSettings(FrozenSettings):
    gap_note: float
    gap_review: float
    gap_priority: float
    peer_z_note: float
    peer_z_flag: float
    mad_scale_floor: float
    cluster_min_cases: int
    cluster_max_iqr: float
    cluster_min_gap: float
    timing_rho: float
    timing_p: float
    timing_hand_band_m: float
    timing_min_cohort: int
    timing_radius_km: float
    boundary: float


class GradeSettings(FrozenSettings):
    a_min: int
    b_min: int
    c_min: int


class ReportSettings(FrozenSettings):
    llm_polish_enabled: bool


class Config(FrozenSettings):
    parcel: ParcelSettings
    peers: PeerSettings
    controls: ControlSettings
    satellite: SatelliteSettings
    sar: SarSettings
    hazard: HazardSettings
    ground: GroundSettings
    official: OfficialSettings
    pooling: PoolingSettings
    detectors: DetectorSettings
    grade: GradeSettings
    report: ReportSettings


def _config_path() -> Path:
    override = os.getenv("RECON_CONFIG")
    return Path(override).expanduser() if override else DEFAULT_CONFIG


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load and cache validated settings; missing keys raise a validation error."""
    path = _config_path()
    with path.open("rb") as stream:
        payload = yaml.safe_load(stream)
    return Config.model_validate(payload)


def config_sha() -> str:
    """SHA-256 digest of the exact configuration file bytes."""
    return hashlib.sha256(_config_path().read_bytes()).hexdigest()
