import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import mr from './i18n/mr.json';

const mocks = vi.hoisted(() => ({
  enqueueBundle: vi.fn(),
  flushQueue: vi.fn(),
  listBundles: vi.fn(),
  bundleSignature: vi.fn()
}));

vi.mock('./offlineQueue', () => ({
  enqueueBundle: mocks.enqueueBundle,
  flushQueue: mocks.flushQueue,
  listBundles: mocks.listBundles
}));

vi.mock('./lib/signature', () => ({ bundleSignature: mocks.bundleSignature }));

vi.mock('./CameraBurstCapture', () => ({
  default: ({ onCapture }: { onCapture: (photo: unknown) => void }) => (
    <button onClick={() => onCapture({
      signature: 'photo-signature',
      telemetry: { lat: 18.5, lon: 73.9, acc_m: 5, azimuth_deg: 90, pitch_deg: 75, captured_at: '2024-07-25T10:00:00.000Z' },
      frames: [new Blob(['frame'], { type: 'image/jpeg' })],
      inAppCapture: true
    })}>Capture test photo</button>
  )
}));

describe('PWA submission workflow', () => {
  let originalOnline: PropertyDescriptor | undefined;

  beforeEach(() => {
    originalOnline = Object.getOwnPropertyDescriptor(navigator, 'onLine');
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 501 }));
    mocks.enqueueBundle.mockReset().mockResolvedValue(undefined);
    mocks.flushQueue.mockReset().mockResolvedValue(undefined);
    mocks.listBundles.mockReset().mockResolvedValue([]);
    mocks.bundleSignature.mockReset().mockResolvedValue('bundle-signature');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    if (originalOnline) Object.defineProperty(navigator, 'onLine', originalOnline);
    else Reflect.deleteProperty(navigator, 'onLine');
  });

  it('captures the documented payload offline and starts the queue when the device reconnects', async () => {
    window.history.replaceState({}, '', '/?case=case-789&t=case-token');
    render(<App />);
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: mr.start_report }));
    fireEvent.change(screen.getByLabelText(mr.damage_q), { target: { value: '75' } });
    fireEvent.click(screen.getByRole('button', { name: mr.depth_knee }));
    fireEvent.change(screen.getByLabelText(mr.note_opt), { target: { value: 'पाणी चार दिवस साचले' } });
    fireEvent.click(screen.getByRole('button', { name: mr.continue }));
    fireEvent.click(screen.getByRole('button', { name: 'Capture test photo' }));
    fireEvent.click(screen.getByRole('button', { name: mr.skip_second }));
    fireEvent.click(screen.getByRole('button', { name: mr.send }));

    await waitFor(() => expect(mocks.enqueueBundle).toHaveBeenCalledOnce());
    const [bundle] = mocks.enqueueBundle.mock.calls[0];
    expect(bundle).toMatchObject({ id: 'bundle-signature', caseId: 'case-789', token: 'case-token', status: 'PENDING' });
    expect(bundle.blobs).toHaveLength(1);
    expect(bundle.payload).toEqual({
      client_bundle_signature: 'bundle-signature',
      locale: 'mr',
      form: {
        damaged_share_pct: 75,
        water_depth_band: 'KNEE',
        water_days: 0,
        crop_stage: 'VEGETATIVE',
        note: 'पाणी चार दिवस साचले'
      },
      photos: [{
        lat: 18.5, lon: 73.9, acc_m: 5, azimuth_deg: 90, pitch_deg: 75,
        captured_at: '2024-07-25T10:00:00.000Z',
        client_photo_signature: 'photo-signature', in_app_capture: true,
        frames: ['photo0_frame0']
      }]
    });
    expect(mocks.flushQueue).not.toHaveBeenCalled();
    expect(screen.getByText(mr.saved_offline)).toBeInTheDocument();

    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    fireEvent(window, new Event('online'));
    await waitFor(() => expect(mocks.flushQueue).toHaveBeenCalled());
  });
});
