import { useCallback, useEffect, useRef, useState } from 'react';
import { circularMean, normalizeHeading } from '../lib/geo';

export function compassHeading(alpha: number, beta: number, gamma: number): number {
  const d = Math.PI / 180, x = beta * d, y = gamma * d, z = alpha * d;
  const cY = Math.cos(y), cZ = Math.cos(z), sX = Math.sin(x), sY = Math.sin(y), sZ = Math.sin(z);
  const vx = -cZ * sY - sZ * sX * cY;
  const vy = -sZ * sY + cZ * sX * cY;
  let heading = Math.atan(vx / vy);
  if (vy < 0) heading += Math.PI; else if (vx < 0) heading += 2 * Math.PI;
  return normalizeHeading(heading * 180 / Math.PI);
}

export function useOrientation() {
  const [pitch, setPitch] = useState<number | null>(null);
  const [heading, setHeading] = useState<number | null>(null);
  const [available, setAvailable] = useState(false);
  const history = useRef<number[]>([]);
  const request = useCallback(async () => {
    const eventType = DeviceOrientationEvent as typeof DeviceOrientationEvent & {
      requestPermission?: () => Promise<'granted' | 'denied'>;
    };
    if (eventType.requestPermission) {
      try { if (await eventType.requestPermission() !== 'granted') return false; }
      catch { return false; }
    }
    setAvailable(true);
    return true;
  }, []);
  useEffect(() => {
    if (!available) return;
    const handler = (event: DeviceOrientationEvent) => {
      if (event.beta !== null) setPitch(event.beta);
      const absolute = event as DeviceOrientationEvent & { webkitCompassHeading?: number; absolute?: boolean };
      const value = typeof absolute.webkitCompassHeading === 'number'
        ? absolute.webkitCompassHeading
        : event.alpha !== null && event.beta !== null && event.gamma !== null
          ? compassHeading(event.alpha, event.beta, event.gamma) : null;
      if (value !== null && Number.isFinite(value)) {
        history.current = [...history.current, value].slice(-5);
        setHeading(circularMean(history.current));
      }
    };
    window.addEventListener('deviceorientationabsolute', handler as EventListener);
    window.addEventListener('deviceorientation', handler as EventListener);
    return () => {
      window.removeEventListener('deviceorientationabsolute', handler as EventListener);
      window.removeEventListener('deviceorientation', handler as EventListener);
    };
  }, [available]);
  return { pitch, heading, available, request };
}
