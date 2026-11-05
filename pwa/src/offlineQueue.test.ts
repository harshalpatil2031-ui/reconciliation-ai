import 'fake-indexeddb/auto';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { enqueueBundle, flushQueue, listBundles } from './offlineQueue';
import type { QueuedBundle } from './lib/types';

function makeBundle(status: QueuedBundle['status'] = 'PENDING'): QueuedBundle {
  return {
    id: `bundle-${crypto.randomUUID()}`, caseId: 'case-1', token: 'private-token',
    payload: {
      client_bundle_signature: 'abc', locale: 'mr',
      form: { damaged_share_pct: 50, water_depth_band: 'NONE', water_days: 0, crop_stage: 'VEGETATIVE', note: null },
      photos: [{ client_photo_signature: 'photo', lat: 18, lon: 74, acc_m: 5, azimuth_deg: 90,
        pitch_deg: 75, captured_at: new Date().toISOString(), in_app_capture: true, frames: ['photo0_frame0'] }]
    },
    blobs: [new window.Blob(['frame'], { type: 'image/jpeg' })], status, attempts: 0,
    lastError: null, createdAt: Date.now(), uploadStartedAt: status === 'UPLOADING' ? Date.now() - 121_000 : undefined
  };
}

class SuccessfulRequest {
  static sends = 0;
  upload = { onprogress: null as ((event: ProgressEvent) => void) | null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  status = 201;
  responseText = '';
  open() {}
  setRequestHeader() {}
  send(body: TestFormData) {
    expect(body.get('payload')).toBeTruthy();
    expect(body.get('photo0_frame0')).toBeTruthy();
    SuccessfulRequest.sends += 1;
    queueMicrotask(() => this.onload?.());
  }
}

class TestFormData {
  private entries = new Map<string, unknown>();
  append(name: string, value: unknown) { this.entries.set(name, value); }
  get(name: string) { return this.entries.get(name) ?? null; }
}

class RejectedRequest {
  upload = { onprogress: null as ((event: ProgressEvent) => void) | null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  responseText = 'request rejected';
  constructor(public status: number) {}
  open() {}
  setRequestHeader() {}
  send(_body: TestFormData) { queueMicrotask(() => this.onload?.()); }
}

class NetworkFailureRequest {
  upload = { onprogress: null as ((event: ProgressEvent) => void) | null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  responseText = '';
  open() {}
  setRequestHeader() {}
  send(_body: TestFormData) { queueMicrotask(() => this.onerror?.()); }
}

class CapturingRequest extends SuccessfulRequest {
  static body: TestFormData | null = null;
  send(body: TestFormData) {
    CapturingRequest.body = body;
    super.send(body);
  }
}

class UploadFormData extends TestFormData {
  append(name: string, value: unknown, filename?: string) {
    super.append(name, filename ? { value, filename } : value);
  }
}

afterEach(async () => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  await new Promise<void>((resolve) => {
    const request = indexedDB.deleteDatabase('recon-ai');
    request.onsuccess = () => resolve();
    request.onerror = () => resolve();
    request.onblocked = () => resolve();
  });
});

describe('offline queue', () => {
  it('persists a bundle locally without sending it while offline', async () => {
    const bundle = makeBundle();
    await enqueueBundle(bundle);
    const [saved] = await listBundles();
    expect(saved.status).toBe('PENDING');
    expect(saved.blobs).toHaveLength(1);
    expect(saved.token).toBe('private-token');
  });

  it('recovers a stale upload, prevents concurrent duplicate sends, and purges private data on success', async () => {
    SuccessfulRequest.sends = 0;
    vi.stubGlobal('FormData', TestFormData);
    const bundle = makeBundle('UPLOADING');
    await enqueueBundle(bundle);
    const requestFactory = () => new SuccessfulRequest() as unknown as XMLHttpRequest;
    await Promise.all([
      flushQueue('http://localhost:8000', undefined, undefined, requestFactory),
      flushQueue('http://localhost:8000', undefined, undefined, requestFactory)
    ]);
    const [saved] = await listBundles();
    expect(saved).toBeDefined();
    expect(SuccessfulRequest.sends).toBe(1);
    expect(saved.status).toBe('DONE');
    expect(saved.token).toBeNull();
    expect(saved.payload).toBeNull();
    expect(saved.blobs).toHaveLength(0);
  });

  it.each([404, 413])('stops retrying permanent HTTP %i errors and clears private bundle data', async (status) => {
    vi.stubGlobal('FormData', TestFormData);
    const bundle = makeBundle();
    await enqueueBundle(bundle);
    const timer = vi.spyOn(window, 'setTimeout');
    const requestFactory = () => new RejectedRequest(status) as unknown as XMLHttpRequest;
    await flushQueue('http://localhost:8000', undefined, undefined, requestFactory);
    const [saved] = await listBundles();
    expect(saved.status).toBe('FAILED');
    expect(saved.attempts).toBe(1);
    expect(saved.token).toBeNull();
    expect(saved.payload).toBeNull();
    expect(saved.blobs).toHaveLength(0);
    expect(timer).not.toHaveBeenCalled();
    timer.mockRestore();
  });

  it('retains payload and token after a transient network error and schedules an exponential retry', async () => {
    vi.stubGlobal('FormData', TestFormData);
    const bundle = makeBundle();
    await enqueueBundle(bundle);
    const timer = vi.spyOn(window, 'setTimeout');
    const requestFactory = () => new NetworkFailureRequest() as unknown as XMLHttpRequest;
    await flushQueue('http://localhost:8000', undefined, undefined, requestFactory);
    const [saved] = await listBundles();
    expect(saved.status).toBe('PENDING');
    expect(saved.attempts).toBe(1);
    expect(saved.token).toBe('private-token');
    expect(saved.payload).toEqual(bundle.payload);
    expect(saved.blobs).toHaveLength(1);
    expect(timer).toHaveBeenCalledWith(expect.any(Function), 2_000);
  });

  it('maps every burst frame to multipart data and clears private data after a successful upload', async () => {
    vi.stubGlobal('FormData', UploadFormData);
    SuccessfulRequest.sends = 0;
    CapturingRequest.body = null;
    const bundle = makeBundle();
    bundle.payload!.photos[0].frames = ['photo0_frame0', 'photo0_frame1', 'photo0_frame2'];
    bundle.blobs = [0, 1, 2].map((frame) => new window.Blob([`frame-${frame}`], { type: 'image/jpeg' }));
    await enqueueBundle(bundle);
    await flushQueue('http://localhost:8000', undefined, undefined, () => new CapturingRequest() as unknown as XMLHttpRequest);
    const [saved] = await listBundles();
    const requestBody = CapturingRequest.body as TestFormData | null;
    expect(requestBody?.get('payload')).toBeTruthy();
    expect(requestBody?.get('photo0_frame0')).toMatchObject({ value: bundle.blobs[0], filename: 'photo0_frame0.jpg' });
    expect(requestBody?.get('photo0_frame1')).toMatchObject({ value: bundle.blobs[1], filename: 'photo0_frame1.jpg' });
    expect(requestBody?.get('photo0_frame2')).toMatchObject({ value: bundle.blobs[2], filename: 'photo0_frame2.jpg' });
    expect(saved.status).toBe('DONE');
    expect(saved.token).toBeNull();
    expect(saved.payload).toBeNull();
    expect(saved.blobs).toHaveLength(0);
  });

  it('does not steal an upload lock that is still fresh', async () => {
    vi.stubGlobal('FormData', TestFormData);
    SuccessfulRequest.sends = 0;
    const bundle = makeBundle();
    bundle.status = 'UPLOADING';
    bundle.uploadStartedAt = Date.now() - 1_000;
    await enqueueBundle(bundle);
    await flushQueue('http://localhost:8000', undefined, undefined, () => new SuccessfulRequest() as unknown as XMLHttpRequest);
    const [saved] = await listBundles();
    expect(SuccessfulRequest.sends).toBe(0);
    expect(saved.status).toBe('UPLOADING');
  });
});
