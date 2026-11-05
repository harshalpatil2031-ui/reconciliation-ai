import { describe, expect, it } from 'vitest';
import { circularDifference, circularMean, distanceMeters, headingPointsToParcel, median } from './geo';

describe('geometry and sensor helpers', () => {
  it('uses circular arithmetic at north and returns null for an empty mean', () => {
    expect(circularMean([359, 1])).toBeCloseTo(0, 5);
    expect(circularDifference(359, 1)).toBe(2);
    expect(circularMean([])).toBeNull();
  });

  it('accepts headings toward the parcel bearing span and rejects headings away from it', () => {
    const parcel: [number, number, number, number] = [73.9, 18.45, 73.92, 18.47];
    expect(headingPointsToParcel(90, 18.46, 73.8, parcel)).toBe(true);
    expect(headingPointsToParcel(270, 18.46, 73.8, parcel)).toBe(false);
    expect(headingPointsToParcel(null, 18.46, 73.8, parcel)).toBe(false);
  });

  it('measures GPS movement and computes odd/even medians', () => {
    expect(distanceMeters({ lat: 18.5, lon: 73.9 }, { lat: 18.5, lon: 73.9 })).toBe(0);
    expect(distanceMeters({ lat: 0, lon: 0 }, { lat: 0, lon: 0.001 })).toBeGreaterThan(100);
    expect(median([3, 1, 2])).toBe(2);
    expect(median([4, 1, 3, 2])).toBe(2.5);
  });
});
