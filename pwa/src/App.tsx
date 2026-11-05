import { useCallback, useEffect, useMemo, useState } from 'react';
import mr from './i18n/mr.json';
import en from './i18n/en.json';
import CameraBurstCapture from './CameraBurstCapture';
import StructuredClaimForm from './StructuredClaimForm';
import { bundleSignature } from './lib/signature';
import { enqueueBundle, flushQueue, listBundles } from './offlineQueue';
import type { CapturedPhoto, GroundForm, GroundPayload, Locale, ParcelContext, QueuedBundle } from './lib/types';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEMO_API = 'http://127.0.0.1:8001';
const initialForm: GroundForm = { damaged_share_pct: 50, water_depth_band: 'NONE', water_days: 0, crop_stage: 'VEGETATIVE', note: null };

interface DemoCase { id: string; title: string; official_pct: number; satellite_style_pct: number | null; status: string; reason: string }
interface DemoReport { id: string; created_at: string; form: GroundForm; status: string; review_note: string | null; official_pct: number; satellite_style_pct: number; explanation: string }

export default function App() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const demoMode = params.get('demo') === '1';
  const caseId = params.get('case') || (demoMode ? 'DEMO-CASE' : '');
  const token = params.get('t') || (demoMode ? 'local-demo-token' : '');
  const [locale, setLocale] = useState<Locale>('mr');
  const copy = locale === 'mr' ? mr : en;
  const [step, setStep] = useState<'welcome' | 'form' | 'camera' | 'review' | 'received' | 'officer'>('welcome');
  const [form, setForm] = useState<GroundForm>(initialForm);
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [parcel, setParcel] = useState<ParcelContext | null>(null);
  const [queue, setQueue] = useState<QueuedBundle[]>([]);
  const [online, setOnline] = useState(navigator.onLine);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState<Record<string, number>>({});
  const [consented, setConsented] = useState(false);
  const [demoCases, setDemoCases] = useState<DemoCase[]>([]);
  const [demoReports, setDemoReports] = useState<DemoReport[]>([]);
  const [demoError, setDemoError] = useState('');

  const refreshQueue = useCallback(async () => {
    const bundles = await listBundles();
    setQueue(Array.isArray(bundles) ? bundles : []);
  }, []);
  useEffect(() => {
    if (demoMode) {
      let active = true;
      const loadDemo = async () => {
        try {
          const [caseResponse, reportResponse] = await Promise.all([
            fetch(`${DEMO_API}/demo/cases`), fetch(`${DEMO_API}/demo/reports`)
          ]);
          if (!caseResponse.ok || !reportResponse.ok) throw new Error('Demo API is unavailable');
          const [cases, reports] = await Promise.all([caseResponse.json(), reportResponse.json()]);
          if (active) { setDemoCases(cases); setDemoReports((current) => current.length ? current : reports); setDemoError(''); }
        } catch { if (active) setDemoError('Start the local demo API to load and save reports.'); }
      };
      void loadDemo();
      return () => { active = false; };
    }
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
  }, [caseId, token, refreshQueue, demoMode]);

  async function submit() {
    if (demoMode) {
      try {
        const response = await fetch(`${DEMO_API}/demo/reports`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ locale, form })
        });
        if (!response.ok) throw new Error('Demo report could not be saved');
        const report = await response.json() as DemoReport;
        setDemoReports((old) => [report, ...old.filter((item) => item.id !== report.id)]);
        setMessage('Demo report saved to the local prototype backend. It was not sent to any real service.');
        setStep('received');
      } catch { setDemoError('Could not reach the local demo API. Start it and try again.'); }
      return;
    }
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
    setMessage(navigator.onLine ? copy.sending : copy.saved_offline);
    if (navigator.onLine) {
      await flushQueue(API, refreshQueue, (id, value) => setProgress((p) => ({ ...p, [id]: value })));
      const latest = (await listBundles()).find((item) => item.id === signature);
      if (latest?.status === 'DONE') setMessage(copy.upload_success);
      else if (latest?.status === 'FAILED') setMessage(latest.lastError || copy.upload_error);
      else setMessage(copy.upload_pending);
    } else setMessage(copy.saved_offline);
  }

  if (!caseId || !token) return <main className="app-shell"><header><h1>{copy.title}</h1></header><section className="card"><p>{copy.empty_case}</p></section></main>;
  return <main className="app-shell">
    <header className="topbar"><div><h1>{copy.title}</h1><p>{copy.case}: {caseId.slice(0, 8)}…</p></div>
      <button className="language" onClick={() => setLocale(locale === 'mr' ? 'en' : 'mr')}>{copy.language}</button></header>
    <div className="connection" role="status"><span className={online ? 'online-dot' : 'offline-dot'} />{demoMode ? (demoError ? 'Local demo service unavailable' : 'Local demo service') : online ? copy.online : copy.offline}</div>
    {demoMode && <p className="demo-banner" role="note">DEMO · Synthetic examples · Local prototype API · Nothing sent externally</p>}
    {demoMode && demoError && <p className="error" role="alert">{demoError}</p>}
    {step === 'welcome' && <section className="card welcome"><p>{copy.subtitle}</p>{!demoMode && <><h2>{copy.permissions_title}</h2>
      <ul><li>{copy.permission_location}</li><li>{copy.permission_camera}</li><li>{copy.permission_motion}</li></ul>
      <label className="consent"><input type="checkbox" checked={consented} onChange={(event) => setConsented(event.target.checked)} />
        {locale === 'mr' ? 'अहवाल पाठवण्यासाठी माझे स्थान आणि फोटो वापरण्यास मी सहमती देतो.' : 'I agree to use my location and photos to submit this report.'}</label></>}
      <button disabled={!demoMode && !consented} onClick={() => setStep('form')}>{demoMode ? (locale === 'mr' ? 'नमुना अहवाल सुरू करा' : 'Start demo report') : copy.start_report}</button>
      {demoMode && <button className="secondary" onClick={() => setStep('officer')}>{locale === 'mr' ? 'अधिकारी नमुना दृश्य' : 'Open officer demo'}</button>}</section>}
    {step === 'form' && <><StructuredClaimForm value={form} onChange={setForm} copy={copy} locale={locale} />
      <button onClick={() => setStep(demoMode ? 'review' : 'camera')}>{copy.continue}</button></>}
    {step === 'camera' && <><CameraBurstCapture parcel={parcel} count={photos.length} copy={copy}
      onCapture={(photo) => setPhotos((old) => old.length < 2 ? [...old, photo] : old)} />
      <div className="button-row">{photos.length === 0 && <button className="secondary" onClick={() => setStep('form')}>{copy.continue}</button>}
        {photos.length === 1 && <button className="secondary" onClick={() => setStep('review')}>{copy.skip_second}</button>}
        {photos.length >= 2 && <button onClick={() => setStep('review')}>{copy.review_send}</button>}</div></>}
    {step === 'review' && <section className="card"><h2>{copy.review_send}</h2><p>{copy.damage_q}: {form.damaged_share_pct}%</p>
      {!demoMode && <p>{copy.photos_count}: {photos.length}</p>}{demoMode && <p>This illustrative report stays on this browser. No GPS or photo is required.</p>}
      <button onClick={() => void submit()}>{demoMode ? (locale === 'mr' ? 'या डिव्हाइसवर जतन करा' : 'Save on this device') : copy.send}</button></section>}
    {step === 'received' && <section className="card"><h2>{copy.report_saved}</h2><p role="status">{message || copy.saved_offline}</p>
      {demoMode && <><p><strong>Demo review:</strong> Needs human review. This is not a compensation decision.</p>
        <p>Official assessment: 20% · Satellite-style example: 40% · Farmer report: {form.damaged_share_pct}%</p>
        <p>Why shown: the illustrative evidence differs and needs a person to compare the sources.</p>
        <button className="secondary" onClick={() => setStep('officer')}>Open officer view</button>
        <button className="secondary" onClick={() => setStep('welcome')}>Back to demo start</button></>}
      {!demoMode && <button className="secondary" onClick={() => setStep('review')}>{copy.retry}</button>}</section>}
    {step === 'officer' && <section className="card"><h2>Officer demo · synthetic scenarios</h2>
      {demoCases.map((item) => <article key={item.id}><h3>{item.id} · {item.title}</h3>
        <p>Official {item.official_pct}% · Satellite-style {item.satellite_style_pct === null ? 'unavailable' : `${item.satellite_style_pct}%`} · Demo result: {item.status}.</p>
        <p>Reason: {item.reason}</p></article>)}
      <h3>Submitted demo reports</h3>
      {!demoReports.length && <p>No reports yet. Submit one from the farmer demo.</p>}
      {demoReports.map((report) => <article key={report.id}><h3>Report {report.id.slice(0, 8)}</h3>
        <p>Farmer-reported damage: {report.form.damaged_share_pct}% · Official example: {report.official_pct}% · Satellite-style example: {report.satellite_style_pct}%</p>
        <p>{report.explanation}</p><p>Status: {report.status}{report.review_note ? ` · ${report.review_note}` : ''}</p>
        {report.status !== 'REVIEWED_FOR_DEMO' && <button onClick={async () => {
          const response = await fetch(`${DEMO_API}/demo/reports/${report.id}/review`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ note: 'Reviewed in prototype demo' })
          });
          if (response.ok) { const updated = await response.json() as DemoReport; setDemoReports((old) => old.map((item) => item.id === updated.id ? updated : item)); }
        }}>Mark reviewed in demo</button>}</article>)}
      <p>All values above are synthetic examples. The tool does not approve or deny compensation.</p>
      <button className="secondary" onClick={() => setStep('welcome')}>Back to demo start</button>
      <button className="secondary" onClick={async () => {
        const response = await fetch(`${DEMO_API}/demo/reports`, { method: 'DELETE' });
        if (response.ok) setDemoReports([]);
      }}>Reset demo reports</button>
    </section>}
    {!!queue.length && <section className="queue"><h2>{copy.queued}</h2>{queue.filter((item) => item.caseId === caseId).map((item) =>
      <p key={item.id}>{item.status} {progress[item.id] ? `${progress[item.id]}%` : ''} {item.lastError || ''}</p>)}</section>}
  </main>;
}
