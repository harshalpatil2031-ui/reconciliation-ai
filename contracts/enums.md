# Shared enums

This file transcribes relay Section 2.3. `backend.models` is the Python source for these values.

| Enum / field | Allowed values |
|---|---|
| `tier` | `PRIORITY_REVIEW`, `REVIEW`, `NOTE`, `CONSISTENT`, `INSUFFICIENT_EVIDENCE` |
| `grade` | `A`, `B`, `C`, `D` |
| `pooling_status` | `OK`, `SOURCE_CONFLICT`, `SAT_ONLY`, `GROUND_ONLY`, `NO_OBSERVATION` |
| `boundary_crossing` | `NONE`, `SAT_UNDER_RISK`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `OVER_RISK` |
| `observed_estimates.source` | `satellite`, `ground` |
| `scene_observations.sensor` | `S2_IMMEDIATE`, `S2_DELAYED`, `S1_SAR` |
| `photos.verification_tier` | `1`, `2`, `3` |
| `parcels.role` | `case`, `control` |
| `plausibility` | `LOW`, `MODERATE`, `HIGH` |
| `factor.status` | `TRIGGERED`, `NOT_TRIGGERED`, `CANNOT_ASSESS` |
| `factor.code` | `LATE_ASSESSMENT`, `PEER_INCONSISTENCY`, `BLANKET_PANCHNAMA_CLUSTER`, `PARTIAL_PARCEL_SUBMERGENCE`, `SILT_RECOVERY_OBSERVED`, `DELAYED_WATERLOGGING_ROT`, `DISCHARGE_EXPOSURE`, `GROUND_DRIVEN_BOUNDARY_CROSSING`, `PHOTO_INTEGRITY_ALERT`, `CROP_MISMATCH`, `SOURCE_CONFLICT`, `NON_FLOOD_CAUSE_POSSIBLE` |
| `satellite quality.flags` | `SILT_RECOVERY_OBSERVED`, `DELAYED_WATERLOGGING_ROT`, `SMALL_PARCEL_LIMITATION`, `LOW_CLEAR_FRACTION`, `STANDING_WATER_AT_SCENE` |
| `photo flags` | `OUTSIDE_PARCEL_BOUNDARY`, `FRUSTUM_OUTSIDE_PARCEL`, `PITCH_OUT_OF_RANGE`, `SINGLE_ANGLE_ONLY`, `BURST_PARALLAX_FAIL`, `SCREEN_MOIRE_SUSPECTED`, `DUPLICATE_PHOTO_EMBEDDING`, `CROP_MISMATCH`, `COMPASS_MISSING`, `GALLERY_UPLOAD`, `LOW_GPS_ACCURACY` |
| review `decision` | `CONFIRM_FLAG`, `DISMISS_FLAG`, `ESCALATE`, `REQUEST_FIELD_VISIT` |
| review `reason_code` | `SATELLITE_EVIDENCE_ACCEPTED`, `SATELLITE_EVIDENCE_REJECTED`, `PHOTO_FRAUD_SUSPECTED`, `ASSESSOR_BIAS_CONFIRMED`, `DATA_QUALITY_ISSUE`, `OTHER` |
| language | `en`, `mr` |

The database enforces the enumerations for `parcels.role`, `detections.pooling_status`, `detections.boundary_crossing`, `detections.tier`, `detections.grade`, `photos.verification_tier`, and review decisions/reasons. Other JSON and column values are validated by the shared Pydantic models or the owning stage.
