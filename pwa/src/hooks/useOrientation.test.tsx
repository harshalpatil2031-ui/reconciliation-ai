import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useOrientation } from './useOrientation';

class PermissionDeviceOrientationEvent {
  static requestPermission = vi.fn<() => Promise<'granted' | 'denied'>>();
}

afterEach(() => vi.unstubAllGlobals());

describe('orientation permission and readings', () => {
  it('keeps orientation unavailable when the user denies the sensor permission', async () => {
    PermissionDeviceOrientationEvent.requestPermission.mockResolvedValue('denied');
    vi.stubGlobal('DeviceOrientationEvent', PermissionDeviceOrientationEvent);
    const { result } = renderHook(() => useOrientation());
    let granted = true;
    await act(async () => { granted = await result.current.request(); });
    expect(granted).toBe(false);
    expect(result.current.available).toBe(false);
    expect(PermissionDeviceOrientationEvent.requestPermission).toHaveBeenCalledOnce();
  });

  it('accepts permission and records pitch plus the iOS compass heading', async () => {
    PermissionDeviceOrientationEvent.requestPermission.mockResolvedValue('granted');
    vi.stubGlobal('DeviceOrientationEvent', PermissionDeviceOrientationEvent);
    const { result } = renderHook(() => useOrientation());
    await act(async () => { await result.current.request(); });
    const event = Object.assign(new Event('deviceorientation'), {
      beta: 76, alpha: 0, gamma: 0, webkitCompassHeading: 112
    });
    act(() => window.dispatchEvent(event));
    expect(result.current.pitch).toBe(76);
    expect(result.current.heading).toBe(112);
  });
});
