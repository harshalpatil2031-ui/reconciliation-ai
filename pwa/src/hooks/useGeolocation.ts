import { useEffect, useState } from 'react';

export interface LocationFix { lat: number; lon: number; acc: number; timestamp: number }

export function useGeolocation() {
  const [fix, setFix] = useState<LocationFix | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const freshnessTimer = window.setInterval(() => setNow(Date.now()), 1_000);
    if (!navigator.geolocation) {
      setError('unsupported');
      return () => window.clearInterval(freshnessTimer);
    }
    const watch = navigator.geolocation.watchPosition(
      (position) => {
        setError(null);
        setFix({ lat: position.coords.latitude, lon: position.coords.longitude,
          acc: position.coords.accuracy, timestamp: position.timestamp });
      },
      (reason) => setError(reason.code === reason.PERMISSION_DENIED ? 'denied' : 'unavailable'),
      { enableHighAccuracy: true, maximumAge: 0 }
    );
    return () => { window.clearInterval(freshnessTimer); navigator.geolocation.clearWatch(watch); };
  }, []);
  const ready = !!fix && fix.acc <= 25 && now - fix.timestamp < 10_000;
  return { fix, error, ready };
}
