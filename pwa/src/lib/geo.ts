export function normalizeHeading(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

export function circularMean(degrees: number[]): number | null {
  if (!degrees.length) return null;
  const radians = degrees.map((value) => normalizeHeading(value) * Math.PI / 180);
  const x = radians.reduce((sum, value) => sum + Math.cos(value), 0);
  const y = radians.reduce((sum, value) => sum + Math.sin(value), 0);
  if (Math.hypot(x, y) < 1e-8) return null;
  return normalizeHeading(Math.atan2(y, x) * 180 / Math.PI);
}

export function circularDifference(a: number, b: number): number {
  const delta = Math.abs(normalizeHeading(a) - normalizeHeading(b));
  return Math.min(delta, 360 - delta);
}

function bearing(fromLat: number, fromLon: number, toLat: number, toLon: number): number {
  const rad = Math.PI / 180;
  const lat1 = fromLat * rad;
  const lat2 = toLat * rad;
  const deltaLon = (toLon - fromLon) * rad;
  const y = Math.sin(deltaLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLon);
  return normalizeHeading(Math.atan2(y, x) / rad);
}

export function headingPointsToParcel(
  heading: number | null,
  lat: number,
  lon: number,
  bbox: [number, number, number, number],
  tolerance = 12
): boolean {
  if (heading === null) return false;
  const [minLon, minLat, maxLon, maxLat] = bbox;
  const bearings = [
    bearing(lat, lon, minLat, minLon), bearing(lat, lon, minLat, maxLon),
    bearing(lat, lon, maxLat, minLon), bearing(lat, lon, maxLat, maxLon)
  ];
  const reference = bearings[0];
  const offsets = bearings.map((value) => ((value - reference + 540) % 360) - 180);
  const low = Math.min(...offsets) + reference;
  const high = Math.max(...offsets) + reference;
  return offsets.some((offset) => circularDifference(heading, normalizeHeading(reference + offset)) <= tolerance)
    || (() => {
      const center = normalizeHeading(reference + (low - reference + high - reference) / 2);
      const halfSpan = Math.min(180, (high - low) / 2 + tolerance);
      return circularDifference(heading, center) <= halfSpan;
    })();
}

export function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function distanceMeters(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLon = (b.lon - a.lon) * rad;
  const lat1 = a.lat * rad;
  const lat2 = b.lat * rad;
  const haversine = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 6_371_000 * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine));
}
