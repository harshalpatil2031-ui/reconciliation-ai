import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CameraBurstCapture from './CameraBurstCapture';
import en from './i18n/en.json';

const { orientationPermission } = vi.hoisted(() => ({ orientationPermission: vi.fn() }));
vi.mock('./hooks/useGeolocation', () => ({
  useGeolocation: () => ({ fix: { lat: 18.5, lon: 73.9, acc: 5, timestamp: Date.now() }, error: null, ready: true })
}));
vi.mock('./hooks/useOrientation', () => ({
  useOrientation: () => ({ pitch: null, heading: null, available: false, request: orientationPermission })
}));

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
});
