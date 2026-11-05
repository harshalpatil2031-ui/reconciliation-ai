import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CameraBurstCapture from './CameraBurstCapture';
import { useGeolocation } from './hooks/useGeolocation';
import en from './i18n/en.json';

const { orientationPermission } = vi.hoisted(() => ({ orientationPermission: vi.fn() }));
vi.mock('./hooks/useGeolocation', () => ({
  useGeolocation: vi.fn(() => ({ fix: { lat: 18.5, lon: 73.9, acc: 5, timestamp: Date.now() }, error: null, ready: true }))
}));
vi.mock('./hooks/useOrientation', () => ({
  useOrientation: () => ({ pitch: 75, heading: 90, available: false, request: orientationPermission })
}));
vi.mock('./lib/signature', () => ({ photoSignature: vi.fn().mockResolvedValue('photo-signature') }));

const originalVideoWidth = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, 'videoWidth');
const originalVideoHeight = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, 'videoHeight');
const originalReadyState = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'readyState');

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  if (originalVideoWidth) Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', originalVideoWidth);
  else Reflect.deleteProperty(HTMLVideoElement.prototype, 'videoWidth');
  if (originalVideoHeight) Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', originalVideoHeight);
  else Reflect.deleteProperty(HTMLVideoElement.prototype, 'videoHeight');
  if (originalReadyState) Object.defineProperty(HTMLMediaElement.prototype, 'readyState', originalReadyState);
  else Reflect.deleteProperty(HTMLMediaElement.prototype, 'readyState');
});

describe('camera permission handling', () => {
  beforeEach(() => {
    orientationPermission.mockReset();
    orientationPermission.mockResolvedValue(false);
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: vi.fn().mockRejectedValue(new DOMException('Permission denied', 'NotAllowedError')) }
    });
  });

  it('requests sensor access from the camera action and explains camera denial', async () => {
    render(<CameraBurstCapture parcel={null} onCapture={vi.fn()} count={0} copy={en} />);
    fireEvent.click(screen.getByRole('button', { name: en.open_camera }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(en.camera_denied));
    expect(orientationPermission).toHaveBeenCalledOnce();
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false
    });
  });

  it('captures three JPEG frames and emits the photo telemetry bundle', async () => {
    const onCapture = vi.fn();
    const track = { stop: vi.fn() };
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [track] }) }
    });
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', { configurable: true, get: () => 1920 });
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', { configurable: true, get: () => 1080 });
    Object.defineProperty(HTMLMediaElement.prototype, 'readyState', { configurable: true, get: () => HTMLMediaElement.HAVE_CURRENT_DATA });
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockImplementation(function (this: HTMLMediaElement) {
      Object.defineProperty(this, 'readyState', { configurable: true, value: HTMLMediaElement.HAVE_CURRENT_DATA });
      return Promise.resolve();
    });
    orientationPermission.mockResolvedValue(true);
    window.dispatchEvent(new Event('deviceorientation'));
    const drawImage = vi.fn();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback) => callback(new Blob(['jpeg-frame'], { type: 'image/jpeg' })));
    const burstTimers = vi.spyOn(window, 'setTimeout');

    const { container } = render(<CameraBurstCapture parcel={null} onCapture={onCapture} count={0} copy={en} />);
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: en.open_camera })); await Promise.resolve(); });
    const shutter = screen.getByRole('button', { name: en.take_photo });
    await waitFor(() => expect(shutter).toBeEnabled());
    Object.defineProperty(container.querySelector('video')!, 'readyState', { configurable: true, value: HTMLMediaElement.HAVE_CURRENT_DATA });
    await act(async () => { fireEvent.loadedData(container.querySelector('video')!); });
    await act(async () => {
      fireEvent.click(shutter);
      await new Promise((resolve) => window.setTimeout(resolve, 1_600));
    });
    await waitFor(() => expect(onCapture).toHaveBeenCalledOnce());

    expect(screen.queryByRole('alert')).toBeNull();
    const [photo] = onCapture.mock.calls[0];
    expect(photo).toMatchObject({ signature: 'photo-signature', inAppCapture: true });
    expect(photo.frames).toHaveLength(3);
    expect(photo.frames.every((frame: Blob) => frame.type === 'image/jpeg')).toBe(true);
    expect(photo.telemetry).toMatchObject({ lat: 18.5, lon: 73.9, acc_m: 5, azimuth_deg: 90, pitch_deg: 75 });
    expect(drawImage).toHaveBeenCalledTimes(3);
    expect(burstTimers.mock.calls.filter((call) => call[1] === 750)).toHaveLength(2);
  });

  it('explains unavailable location services with an accessible alert', () => {
    vi.mocked(useGeolocation).mockReturnValue({ fix: null, error: 'unsupported', ready: false });
    render(<CameraBurstCapture parcel={null} onCapture={vi.fn()} count={0} copy={{ ...en, location_unavailable: 'Location unavailable' }} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Location unavailable');
  });
});
