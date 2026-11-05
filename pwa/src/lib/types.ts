export type Locale = 'mr' | 'en';
export type WaterDepth = 'NONE' | 'ANKLE' | 'KNEE' | 'WAIST' | 'ABOVE_WAIST';
export type CropStage = 'SOWN_ONLY' | 'VEGETATIVE' | 'FLOWERING' | 'PODDING_OR_MATURE';

export interface GroundForm {
  damaged_share_pct: number;
  water_depth_band: WaterDepth;
  water_days: number;
  crop_stage: CropStage;
  note: string | null;
}

export interface Telemetry {
  lat: number;
  lon: number;
  acc_m: number;
  azimuth_deg: number | null;
  pitch_deg: number | null;
  captured_at: string;
}

export interface CapturedPhoto {
  signature: string;
  telemetry: Telemetry;
  frames: Blob[];
  inAppCapture: boolean;
}

export interface GroundPayload {
  client_bundle_signature: string;
  locale: Locale;
  form: GroundForm;
  photos: Array<Telemetry & {
    client_photo_signature: string;
    in_app_capture: boolean;
    frames: string[];
  }>;
}

export interface ParcelContext {
  case_id: string;
  declared_crop: string | null;
  parcel_bbox_wgs84: [number, number, number, number];
  parcel_polygon?: { type: 'Polygon'; coordinates: number[][][] };
  min_width_m?: number | null;
  boundary_tolerance_m: number;
  required_photos: number;
}

export interface QueuedBundle {
  id: string;
  caseId: string;
  token: string | null;
  payload: GroundPayload | null;
  blobs: Blob[];
  status: 'PENDING' | 'UPLOADING' | 'DONE' | 'FAILED';
  uploadStartedAt?: number;
  attempts: number;
  lastError: string | null;
  createdAt: number;
}
