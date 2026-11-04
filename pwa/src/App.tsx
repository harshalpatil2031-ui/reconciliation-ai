import { useCallback, useEffect, useMemo, useState } from 'react';
import mr from './i18n/mr.json';
import en from './i18n/en.json';
import CameraBurstCapture from './CameraBurstCapture';
import StructuredClaimForm from './StructuredClaimForm';
import { bundleSignature } from './lib/signature';
import { enqueueBundle, flushQueue, listBundles } from './offlineQueue';
import type { CapturedPhoto, GroundForm, GroundPayload, Locale, ParcelContext, QueuedBundle } from './lib/types';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const initialForm: GroundForm = { damaged_share_pct: 50, water_depth_band: 'NONE', water_days: 0, crop_stage: 'VEGETATIVE', note: null };

export default function App() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const caseId = params.get('case') || '';
  const token = params.get('t') || '';
  const [locale, setLocale] = useState<Locale>('mr');
  const copy = locale === 'mr' ? mr : en;
  const [step, setStep] = useState<'welcome' | 'form' | 'camera' | 'review' | 'received'>('welcome');
  const [form, setForm] = useState<GroundForm>(initialForm);
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [parcel, setParcel] = useState<ParcelContext | null>(null);
  const [queue, setQueue] = useState<QueuedBundle[]>([]);
  const [online, setOnline] = useState(navigator.onLine);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState<Record<string, number>>({});
  const [consented, setConsented] = useState(false);

  const refreshQueue = useCallback(async () => {
    const bundles = await listBundles();
    setQueue(Array.isArray(bundles) ? bundles : []);
  }, []);
  useEffect(() => {
    let active = true;
    void refreshQueue().then(() => {
      if (navigator.onLine) return flushQueue(API, refreshQueue);
      return undefined;
    });
    const onOnline = () => { setOnline(true); void flushQueue(API, refreshQueue, (id, value) => setProgress((p) => ({ ...p, [id]: value }))); };
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline); window.addEventListener('offline', onOffline);
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible' && navigator.onLine) void flushQueue(API, refreshQueue); }, 30_000);
    if (caseId && token) fetch(`${API}/cases/${encodeURIComponent(caseId)}/ground-context`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.json() as Promise<ParcelContext> : null)
      .then((data) => { if (active && data) setParcel(data); }).catch(() => undefined);
    return () => { active = false; clearInterval(timer); window.removeEventListener('online', onOnline); window.removeEventListener('offline', onOffline); };
  }, [caseId, token, refreshQueue]);

  async function submit() {
    if (!caseId || !token || !photos.length) return;
    const signature = await bundleSignature(photos.map((photo) => photo.signature), form);
    const payload: GroundPayload = {
      client_bundle_signature: signature, locale, form,
      photos: photos.map((photo, photoIndex) => ({ ...photo.telemetry,
        client_photo_signature: photo.signature, in_app_capture: photo.inAppCapture,
        frames: photo.frames.map((_, frameIndex) => `photo${photoIndex}_frame${frameIndex}`) }))
    };
    const bundle: QueuedBundle = { id: signature, caseId, token, payload, blobs: photos.flatMap((photo) => photo.frames),
      status: 'PENDING', attempts: 0, lastError: null, createdAt: Date.now() };
    await enqueueBundle(bundle);
    setStep('received');
    if (navigator.onLine) {
      await flushQueue(API, refreshQueue, (id, value) => setProgress((p) => ({ ...p, [id]: value })));
      const latest = (await listBundles()).find((item) => item.id === signature);
      if (latest?.status === 'FAILED') setMessage(latest.lastError || copy.upload_error);
      else if (latest?.status === 'PENDING') setMessage(copy.saved_offline);
    } else setMessage(copy.saved_offline);
  }

  if (!caseId || !token) return <main className="app-shell"><header><h1>{copy.title}</h1></header><section className="card"><p>{copy.empty_case}</p></section></main>;
  return <main className="app-shell">
    <header className="topbar"><div><h1>{copy.title}</h1><p>{copy.case}: {caseId.slice(0, 8)}…</p></div>
      <button className="language" onClick={() => setLocale(locale === 'mr' ? 'en' : 'mr')}>{copy.language}</button></header>
    <div className="connection" role="status"><span className={online ? 'online-dot' : 'offline-dot'} />{online ? copy.online : copy.offline}</div>
    {step === 'welcome' && <section className="card welcome"><p>{copy.subtitle}</p><h2>{copy.permissions_title}</h2>
      <ul><li>{copy.permission_location}</li><li>{copy.permission_camera}</li><li>{copy.permission_motion}</li></ul>
      <label className="consent"><input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />
        {locale === 'mr' ? 'अहवाल पाठवण्यासाठी माझे स्थान आणि फोटो वापरण्यास मी सहमती देतो.' : 'I agree to use my location and photos to submit this report.'}</label>
      <button disabled={!consented} onClick={() => setStep('form')}>{copy.start_report}</button></section>}
    {step === 'form' && <><StructuredClaimForm value={form} onChange={setForm} copy={copy} locale={locale} />
      <button onClick={() => setStep('camera')}>{copy.continue}</button></>}
    {step === 'camera' && <><CameraBurstCapture parcel={parcel} count={photos.length} copy={copy}
      onCapture={(photo) => setPhotos((old) => old.length < 2 ? [...old, photo] : old)} />
      <div className="button-row"><button className="secondary" onClick={() => setStep('form')}>{copy.continue}</button>
        {photos.length === 1 && <button className="secondary" onClick={() => setStep('review')}>{copy.skip_second}</button>}
        {photos.length >= 2 && <button onClick={() => setStep('review')}>{copy.review_send}</button>}</div></>}
    {step === 'review' && <section className="card"><h2>{copy.review_send}</h2><p>{copy.damage_q}: {form.damaged_share_pct}%</p>
      <p>{copy.photos_count}: {photos.length}</p><button onClick={() => void submit()}>{copy.send}</button></section>}
    {step === 'received' && <section className="card"><h2>{copy.received}</h2><p role="status">{message || copy.saved_offline}</p>
      <button className="secondary" onClick={() => setStep('review')}>{copy.retry}</button></section>}
    {!!queue.length && <section className="queue"><h2>{copy.queued}</h2>{queue.filter((item) => item.caseId === caseId).map((item) =>
      <p key={item.id}>{item.status} {progress[item.id] ? `${progress[item.id]}%` : ''} {item.lastError || ''}</p>)}</section>}
  </main>;
}
