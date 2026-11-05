import type { GroundPayload, QueuedBundle } from './lib/types';

const DB_NAME = 'recon-ai';
const STORE = 'bundles';
const PERMANENT_HTTP_STATUSES = new Set([400, 401, 403, 404, 409, 413, 422]);

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function put(bundle: QueuedBundle): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(bundle);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
  db.close();
}

async function claimForUpload(id: string): Promise<QueuedBundle | null> {
  const db = await openDb();
  const result = await new Promise<QueuedBundle | null>((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite');
    const store = tx.objectStore(STORE);
    const req = store.get(id);
    let claimed: QueuedBundle | null = null;
    req.onsuccess = () => {
      const current = req.result as QueuedBundle | undefined;
      if (!current || current.status === 'DONE' || current.status === 'FAILED') return;
      const staleUpload = current.status === 'UPLOADING'
        && (!current.uploadStartedAt || Date.now() - current.uploadStartedAt > 120_000);
      if (current.status !== 'PENDING' && !staleUpload) return;
      claimed = { ...current, status: 'UPLOADING', uploadStartedAt: Date.now() };
      store.put(claimed);
    };
    tx.oncomplete = () => resolve(claimed);
    tx.onerror = () => reject(tx.error);
  });
  db.close();
  return result;
}

export async function listBundles(): Promise<QueuedBundle[]> {
  const db = await openDb();
  const rows = await new Promise<QueuedBundle[]>((resolve, reject) => {
    const req = db.transaction(STORE).objectStore(STORE).getAll();
    req.onsuccess = () => resolve(req.result as QueuedBundle[]);
    req.onerror = () => reject(req.error);
  });
  db.close();
  return rows.sort((a, b) => a.createdAt - b.createdAt);
}

export async function enqueueBundle(bundle: QueuedBundle): Promise<void> {
  await put(bundle);
}

async function upload(
  bundle: QueuedBundle,
  endpoint: string,
  requestFactory: () => XMLHttpRequest,
  onProgress?: (id: string, percent: number) => void
) {
  if (!bundle.token || !bundle.payload) throw Object.assign(new Error('Queued upload is missing required data'), { permanent: true });
  const payload = bundle.payload;
  const body = new FormData();
  body.append('payload', JSON.stringify(payload));
  let blobIndex = 0;
  payload.photos.forEach((photo, photoIndex) => photo.frames.forEach((frameName, frameIndex) => {
    const blob = bundle.blobs[blobIndex++];
    if (blob) body.append(frameName, blob, `photo${photoIndex}_frame${frameIndex}.jpg`);
  }));
  return new Promise<void>((resolve, reject) => {
    const request = requestFactory();
    request.open('POST', `${endpoint}/cases/${encodeURIComponent(bundle.caseId)}/ground`);
    request.setRequestHeader('Authorization', `Bearer ${bundle.token}`);
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(bundle.id, Math.round(event.loaded / event.total * 100));
    };
    request.onload = () => request.status >= 200 && request.status < 300
      ? resolve() : reject(Object.assign(new Error(request.responseText || `HTTP ${request.status}`), { permanent: PERMANENT_HTTP_STATUSES.has(request.status) }));
    request.onerror = () => reject(new Error('Network error'));
    request.send(body);
  });
}

export async function flushQueue(
  endpoint: string,
  onChange?: () => void,
  onProgress?: (id: string, percent: number) => void,
  requestFactory: () => XMLHttpRequest = () => new XMLHttpRequest()
) {
  for (const pending of await listBundles()) {
    if (pending.status === 'DONE' || pending.status === 'FAILED') continue;
    const bundle = await claimForUpload(pending.id);
    if (!bundle) continue;
    onChange?.();
    try {
      await upload(bundle, endpoint, requestFactory, onProgress);
      bundle.status = 'DONE'; bundle.lastError = null;
      bundle.token = null;
      bundle.payload = null;
      bundle.blobs = [];
      delete bundle.uploadStartedAt;
    } catch (error) {
      bundle.attempts += 1;
      bundle.lastError = error instanceof Error
        ? error.message
        : error && typeof error === 'object' && 'message' in error
          ? String((error as { message: unknown }).message)
          : String(error || 'Upload failed');
      bundle.status = (error as { permanent?: boolean }).permanent ? 'FAILED' : 'PENDING';
      delete bundle.uploadStartedAt;
      if (bundle.status === 'FAILED') {
        bundle.token = null;
        bundle.payload = null;
        bundle.blobs = [];
      }
      await put(bundle); onChange?.();
      if (bundle.status === 'PENDING') {
        const delay = Math.min(300_000, 2_000 * 2 ** Math.min(bundle.attempts - 1, 8));
        window.setTimeout(() => void flushQueue(endpoint, onChange, onProgress, requestFactory), delay);
      }
      continue;
    }
    await put(bundle); onChange?.();
  }
}

export type { GroundPayload };
