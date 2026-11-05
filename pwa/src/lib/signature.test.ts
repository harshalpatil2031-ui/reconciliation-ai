import { describe, expect, it } from 'vitest';
import { bundleSignature, bytesSignature, canonical, photoSignature } from './signature';
import type { GroundForm, Telemetry } from './types';

const form: GroundForm = {
  damaged_share_pct: 50,
  water_depth_band: 'KNEE',
  water_days: 3,
  crop_stage: 'VEGETATIVE',
  note: 'पाणी साचले'
};

const telemetry: Telemetry = {
  lat: 18.5, lon: 73.9, acc_m: 5,
  azimuth_deg: 90, pitch_deg: 75,
  captured_at: '2024-07-25T10:00:00.000Z'
};

describe('client signatures', () => {
  it('canonicalizes objects with sorted keys', () => {
    expect(canonical({ z: 1, a: { d: true, b: 2 } })).toBe('{"a":{"b":2,"d":true},"z":1}');
    expect(canonical({ a: 1, b: 2 })).toBe(canonical({ b: 2, a: 1 }));
  });

  it('creates repeatable SHA-256 signatures for frame bytes and photo telemetry', async () => {
    const frame = new Blob(['frame-bytes'], { type: 'image/jpeg' });
    if (!frame.arrayBuffer) {
      Object.defineProperty(frame, 'arrayBuffer', { value: async () => new TextEncoder().encode('frame-bytes').buffer });
    }
    expect(await bytesSignature(frame)).toBe(await bytesSignature(frame));
    expect(await photoSignature([frame], telemetry)).toBe(await photoSignature([frame], telemetry));
    expect(await photoSignature([frame], telemetry)).not.toBe(await photoSignature([frame], { ...telemetry, lat: 18.6 }));
  });

  it('makes a bundle signature independent of photo order but sensitive to form changes', async () => {
    expect(await bundleSignature(['photo-b', 'photo-a'], form))
      .toBe(await bundleSignature(['photo-a', 'photo-b'], form));
    expect(await bundleSignature(['photo-a'], form))
      .not.toBe(await bundleSignature(['photo-a'], { ...form, damaged_share_pct: 55 }));
  });
});
