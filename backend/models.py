"""Canonical Pydantic models for the contracts shared across stages."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Tier(str, Enum):
    PRIORITY_REVIEW = "PRIORITY_REVIEW"
    REVIEW = "REVIEW"
    NOTE = "NOTE"
    CONSISTENT = "CONSISTENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Grade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class PoolingStatus(str, Enum):
    OK = "OK"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    SAT_ONLY = "SAT_ONLY"
    GROUND_ONLY = "GROUND_ONLY"
    NO_OBSERVATION = "NO_OBSERVATION"


class BoundaryCrossing(str, Enum):
    NONE = "NONE"
    SAT_UNDER_RISK = "SAT_UNDER_RISK"
    GROUND_DRIVEN_BOUNDARY_CROSSING = "GROUND_DRIVEN_BOUNDARY_CROSSING"
    OVER_RISK = "OVER_RISK"


class EstimateSource(str, Enum):
    SATELLITE = "satellite"
    GROUND = "ground"


class Sensor(str, Enum):
    S2_IMMEDIATE = "S2_IMMEDIATE"
    S2_DELAYED = "S2_DELAYED"
    S1_SAR = "S1_SAR"


class VerificationTier(IntEnum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class ParcelRole(str, Enum):
    CASE = "case"
    CONTROL = "control"


class Plausibility(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class FactorStatus(str, Enum):
    TRIGGERED = "TRIGGERED"
    NOT_TRIGGERED = "NOT_TRIGGERED"
    CANNOT_ASSESS = "CANNOT_ASSESS"


class FactorCode(str, Enum):
    LATE_ASSESSMENT = "LATE_ASSESSMENT"
    PEER_INCONSISTENCY = "PEER_INCONSISTENCY"
    BLANKET_PANCHNAMA_CLUSTER = "BLANKET_PANCHNAMA_CLUSTER"
    PARTIAL_PARCEL_SUBMERGENCE = "PARTIAL_PARCEL_SUBMERGENCE"
    SILT_RECOVERY_OBSERVED = "SILT_RECOVERY_OBSERVED"
    DELAYED_WATERLOGGING_ROT = "DELAYED_WATERLOGGING_ROT"
    DISCHARGE_EXPOSURE = "DISCHARGE_EXPOSURE"
    GROUND_DRIVEN_BOUNDARY_CROSSING = "GROUND_DRIVEN_BOUNDARY_CROSSING"
    PHOTO_INTEGRITY_ALERT = "PHOTO_INTEGRITY_ALERT"
    CROP_MISMATCH = "CROP_MISMATCH"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    NON_FLOOD_CAUSE_POSSIBLE = "NON_FLOOD_CAUSE_POSSIBLE"


class SatelliteFlag(str, Enum):
    SILT_RECOVERY_OBSERVED = "SILT_RECOVERY_OBSERVED"
    DELAYED_WATERLOGGING_ROT = "DELAYED_WATERLOGGING_ROT"
    SMALL_PARCEL_LIMITATION = "SMALL_PARCEL_LIMITATION"
    LOW_CLEAR_FRACTION = "LOW_CLEAR_FRACTION"
    STANDING_WATER_AT_SCENE = "STANDING_WATER_AT_SCENE"


class PhotoFlag(str, Enum):
    OUTSIDE_PARCEL_BOUNDARY = "OUTSIDE_PARCEL_BOUNDARY"
    FRUSTUM_OUTSIDE_PARCEL = "FRUSTUM_OUTSIDE_PARCEL"
    PITCH_OUT_OF_RANGE = "PITCH_OUT_OF_RANGE"
    SINGLE_ANGLE_ONLY = "SINGLE_ANGLE_ONLY"
    BURST_PARALLAX_FAIL = "BURST_PARALLAX_FAIL"
    SCREEN_MOIRE_SUSPECTED = "SCREEN_MOIRE_SUSPECTED"
    DUPLICATE_PHOTO_EMBEDDING = "DUPLICATE_PHOTO_EMBEDDING"
    CROP_MISMATCH = "CROP_MISMATCH"
    COMPASS_MISSING = "COMPASS_MISSING"
    GALLERY_UPLOAD = "GALLERY_UPLOAD"
    LOW_GPS_ACCURACY = "LOW_GPS_ACCURACY"


class ReviewDecision(str, Enum):
    CONFIRM_FLAG = "CONFIRM_FLAG"
    DISMISS_FLAG = "DISMISS_FLAG"
    ESCALATE = "ESCALATE"
    REQUEST_FIELD_VISIT = "REQUEST_FIELD_VISIT"


class ReviewReasonCode(str, Enum):
    SATELLITE_EVIDENCE_ACCEPTED = "SATELLITE_EVIDENCE_ACCEPTED"
    SATELLITE_EVIDENCE_REJECTED = "SATELLITE_EVIDENCE_REJECTED"
    PHOTO_FRAUD_SUSPECTED = "PHOTO_FRAUD_SUSPECTED"
    ASSESSOR_BIAS_CONFIRMED = "ASSESSOR_BIAS_CONFIRMED"
    DATA_QUALITY_ISSUE = "DATA_QUALITY_ISSUE"
    OTHER = "OTHER"


class Language(str, Enum):
    EN = "en"
    MR = "mr"


class SatelliteQuality(ContractModel):
    loss_attr: float | None = Field(default=None, ge=0, le=1)
    area_dmg_frac: float | None = Field(default=None, ge=0, le=1)
    n_eff: float | None = Field(default=None, ge=0)
    clear_frac: float | None = Field(default=None, ge=0, le=1)
    water_frac_peak: float | None = Field(default=None, ge=0, le=1)
    water_frac_recession: float | None = Field(default=None, ge=0, le=1)
    window_used: int | None = Field(default=None, ge=1, le=2)
    flags: list[SatelliteFlag] = Field(default_factory=list)
    flags_assessable: bool
    controls_n: int = Field(ge=0)
    controls_deficit_median: float | None = None
    controls_deficit_range: tuple[float, float] | None = None
    onset_in_window: bool | None = None
    first_scene_with_loss: str | None = None
    min_width_m: float | None = None
    mode: str = "v3"
    pixel_grid: dict[str, Any] | None = None


class GroundForm(ContractModel):
    damaged_share_pct: float | None = Field(default=None, ge=0, le=100)
    water_depth_band: str | None = None
    water_days: int | None = Field(default=None, ge=0)
    crop_stage: str | None = None
    note_present: bool = False


class GroundQuality(ContractModel):
    tier: VerificationTier
    excluded: bool
    n_photos: int = Field(ge=0)
    n_photos_passing_all: int = Field(ge=0)
    photo_ids: list[str] = Field(default_factory=list)
    flags: list[PhotoFlag] = Field(default_factory=list)
    form: GroundForm
    form_consistency: str
    max_dup_similarity: float | None = Field(default=None, ge=0, le=1)
    frustum_overlaps: list[float] = Field(default_factory=list)
    locale: Language


class FactorResult(ContractModel):
    code: FactorCode
    status: FactorStatus
    evidence: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class GradePoints(ContractModel):
    coverage: int = Field(ge=0)
    spatial: int = Field(ge=0)
    agreement: int = Field(ge=0)
    attribution: int = Field(ge=0)
    margin: int = Field(ge=0)


class GradeRationale(ContractModel):
    coverage: str
    spatial: str
    agreement: str
    attribution: str
    margin: str


class GradeDetail(ContractModel):
    points: GradePoints
    total: int = Field(ge=0)
    caps_applied: list[str] = Field(default_factory=list)
    rationale: GradeRationale


class DataAvailability(ContractModel):
    sentinel2_windows: list[int] = Field(default_factory=list)
    sar_scenes: int = Field(ge=0)
    ground: str | None = None
    peers: int = Field(ge=0)
    controls: int = Field(ge=0)
    official: bool
    hazard: bool
    missing: list[str] = Field(default_factory=list)


class ModelVersions(ContractModel):
    engine: str
    config_sha: str
    pipeline_commit: str
    embedding_model: str | None = None
    template_version: str
