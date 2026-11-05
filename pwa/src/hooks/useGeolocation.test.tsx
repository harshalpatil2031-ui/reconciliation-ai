import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useGeolocation } from './useGeolocation';

describe('geolocation readiness and errors', () => {
  let success!: PositionCallback;
  let failure!: PositionErrorCallback;
  const clearWatch = vi.fn();
  let originalDescriptor: PropertyDescriptor | undefined;

  beforeEach(() => {
    vi.useFakeTimers();
    success = () => undefined;
    failure = () => undefined;
    clearWatch.mockReset();
    originalDescriptor = Object.getOwnPropertyDescriptor(navigator, 'geolocation');
    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: {
        watchPosition: vi.fn((onSuccess: PositionCallback, onError: PositionErrorCallback, options: PositionOptions) => {
          success = onSuccess;
          failure = onError;
          expect(options).toEqual({ enableHighAccuracy: true, maximumAge: 0 });
          return 42;
        }),
        clearWatch
      }
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    if (originalDescriptor) Object.defineProperty(navigator, 'geolocation', originalDescriptor);
    else Reflect.deleteProperty(navigator, 'geolocation');
  });

  it('opens the shutter only for a fresh fix with accuracy at most 25 metres', () => {
    const { result, unmount } = renderHook(() => useGeolocation());
    expect(result.current.ready).toBe(false);
    act(() => success({
      timestamp: Date.now(),
      coords: { latitude: 18.5, longitude: 73.9, accuracy: 25 } as GeolocationCoordinates
    } as GeolocationPosition));
    expect(result.current.ready).toBe(true);

    act(() => success({
      timestamp: Date.now(),
      coords: { latitude: 18.5, longitude: 73.9, accuracy: 25.1 } as GeolocationCoordinates
    } as GeolocationPosition));
    expect(result.current.ready).toBe(false);

    act(() => success({
      timestamp: Date.now(),
      coords: { latitude: 18.5, longitude: 73.9, accuracy: 5 } as GeolocationCoordinates
    } as GeolocationPosition));
    expect(result.current.ready).toBe(true);
    act(() => { vi.advanceTimersByTime(10_000); });
    expect(result.current.ready).toBe(false);
    unmount();
    expect(clearWatch).toHaveBeenCalledWith(42);
  });

  it('reports a denied location permission', () => {
    const { result } = renderHook(() => useGeolocation());
    act(() => failure({ code: 1, message: 'denied', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 }));
    expect(result.current.error).toBe('denied');
    expect(result.current.ready).toBe(false);
  });

  it('reports unsupported geolocation', () => {
    Object.defineProperty(navigator, 'geolocation', { configurable: true, value: undefined });
    const { result } = renderHook(() => useGeolocation());
    expect(result.current.error).toBe('unsupported');
    expect(result.current.ready).toBe(false);
  });
});
