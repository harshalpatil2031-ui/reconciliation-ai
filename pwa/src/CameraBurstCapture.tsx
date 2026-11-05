import { useEffect, useRef, useState } from 'react';
import type { CapturedPhoto, ParcelContext, Telemetry } from './lib/types';
import { circularDifference, circularMean, distanceMeters, headingPointsToParcel, median } from './lib/geo';
import { photoSignature } from './lib/signature';
import { useGeolocation } from './hooks/useGeolocation';
import { useOrientation } from './hooks/useOrientation';

interface Props {
  parcel: ParcelContext | null;
  onCapture: (photo: CapturedPhoto) => void;
  count: number;
  copy: Record<string, string>;
}

export default function CameraBurstCapture({ parcel, onCapture, count, copy }: Props) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const { fix, error: locationError, ready } = useGeolocation();
  const orientation = useOrientation();
  const liveFix = useRef(fix);
  const liveOrientation = useRef(orientation);
  liveFix.current = fix;
  liveOrientation.current = orientation;
  const [firstTelemetry, setFirstTelemetry] = useState<Telemetry | null>(null);
  const [motionDenied, setMotionDenied] = useState(false);

  useEffect(() => () => stream.current?.getTracks().forEach((track) => track.stop()), []);

  async function openCamera() {
    try {
      void orientation.request().then((granted) => setMotionDenied(!granted));
      stream.current = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false
      });
      if (video.current) {
        video.current.srcObject = stream.current;
        await video.current.play();
        if (video.current.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) setVideoReady(true);
      }
      setCameraOpen(true);
    } catch { setCameraError(true); }
  }

  async function capture() {
    if (!video.current || !liveFix.current || !ready || busy) return;
    setBusy(true);
    const frames: Blob[] = [];
    const samples: Array<{ lat: number; lon: number; acc: number; azimuth: number | null; pitch: number | null; at: number }> = [];
    try {
      for (let i = 0; i < 3; i += 1) {
        if (i) await new Promise((resolve) => window.setTimeout(resolve, 750));
        const element = video.current;
        if (element.videoWidth <= 0 || element.videoHeight <= 0) throw new Error('Camera frame is not ready');
        const scale = Math.min(1, 1280 / Math.max(element.videoWidth, element.videoHeight));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(element.videoWidth * scale);
        canvas.height = Math.round(element.videoHeight * scale);
        canvas.getContext('2d')!.drawImage(element, 0, 0, canvas.width, canvas.height);
        const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob((value) => value ? resolve(value) : reject(new Error('Image capture failed')), 'image/jpeg', 0.85));
        frames.push(blob);
        const current = liveFix.current;
        const currentOrientation = liveOrientation.current;
        if (!current) throw new Error('Location fix expired during camera burst');
        samples.push({ lat: current.lat, lon: current.lon, acc: current.acc,
          azimuth: currentOrientation.heading, pitch: currentOrientation.pitch, at: Date.now() });
      }
      const validHeadings = samples.map((sample) => sample.azimuth).filter((value): value is number => value !== null);
      const validPitches = samples.map((sample) => sample.pitch).filter((value): value is number => value !== null);
      const telemetry: Telemetry = {
        lat: median(samples.map((sample) => sample.lat)), lon: median(samples.map((sample) => sample.lon)),
        acc_m: median(samples.map((sample) => sample.acc)),
        azimuth_deg: circularMean(validHeadings), pitch_deg: validPitches.length ? median(validPitches) : null,
        captured_at: new Date(median(samples.map((sample) => sample.at))).toISOString()
      };
      const signature = await photoSignature(frames, telemetry);
      onCapture({ signature, telemetry, frames, inAppCapture: true });
      setFirstTelemetry(telemetry);
    } catch { setCameraError(true); }
    finally { setBusy(false); }
  }

  const secondAngleReady = !firstTelemetry || (firstTelemetry.azimuth_deg !== null && orientation.heading !== null
    && circularDifference(firstTelemetry.azimuth_deg, orientation.heading) >= 35)
    || (!!firstTelemetry && !!fix && distanceMeters(firstTelemetry, fix) >= 15);
  const headingOkay = !!fix && parcel && headingPointsToParcel(orientation.heading, fix.lat, fix.lon, parcel.parcel_bbox_wgs84);
  const levelOkay = orientation.pitch !== null && orientation.pitch >= 65 && orientation.pitch <= 88;
  const galleryMode = new URLSearchParams(window.location.search).get('mode') === 'gallery';
  const disabled = !ready || !secondAngleReady || busy || count >= 2 || !videoReady;

  async function galleryUpload(file: File) {
    const image = await createImageBitmap(file);
    const scale = Math.min(1, 1280 / Math.max(image.width, image.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(image.width * scale);
    canvas.height = Math.round(image.height * scale);
    canvas.getContext('2d')!.drawImage(image, 0, 0, canvas.width, canvas.height);
    image.close();
    const cleanJpeg = await new Promise<Blob>((resolve, reject) => canvas.toBlob(
      (value) => value ? resolve(value) : reject(new Error('Image conversion failed')), 'image/jpeg', 0.85
    ));
    const telemetry: Telemetry = { lat: fix?.lat ?? 0, lon: fix?.lon ?? 0, acc_m: fix?.acc ?? 999,
      azimuth_deg: orientation.heading, pitch_deg: orientation.pitch, captured_at: new Date().toISOString() };
    const sig = await photoSignature([cleanJpeg], telemetry);
    onCapture({ signature: sig, telemetry, frames: [cleanJpeg, cleanJpeg, cleanJpeg], inAppCapture: false });
  }

  return <section className="card camera-card">
    <div className="camera-guidance">
      <span className={`guide-dot ${levelOkay && headingOkay ? 'good' : ''}`} aria-hidden="true">◎</span>
      <div><strong>{copy.hold_upright}</strong><p>{copy.face_field}</p></div>
    </div>
    {!ready && <p role="status">{copy.gps_wait} {fix ? `(${Math.round(fix.acc)} m)` : ''}</p>}
    {locationError === 'denied' && <p className="error" role="alert">{copy.location_denied}</p>}
    {locationError && locationError !== 'denied' && <p className="error" role="alert">{copy.location_unavailable}</p>}
    {motionDenied && <p role="status">{copy.compass_missing}</p>}
    {cameraError && <p className="error" role="alert">{copy.camera_denied}</p>}
    <video ref={video} autoPlay muted playsInline onLoadedData={() => setVideoReady(true)} className="camera-view" aria-label={copy.open_camera} />
    <div className="camera-actions">
      {!cameraOpen && <button className="secondary" onClick={() => void openCamera()}>{copy.open_camera}</button>}
      <button disabled={disabled || !cameraOpen} onClick={() => void capture()}>{busy ? copy.move_slowly : copy.take_photo}</button>
    </div>
    {firstTelemetry && count === 1 && <p>{copy.turn_second}</p>}
    <p className="muted">{copy.photos_count}: {count}/2 · {fix ? `${Math.round(fix.acc)} m` : copy.locating}</p>
    {galleryMode && <label className="developer-upload">Developer gallery mode
      <input type="file" accept="image/*" onChange={(event) => event.target.files?.[0] && void galleryUpload(event.target.files[0])} />
    </label>}
  </section>;
}
