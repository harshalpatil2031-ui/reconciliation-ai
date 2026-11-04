import type { GroundForm, Telemetry } from './types';

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

async function sha256(data: BufferSource): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function bytesSignature(blob: Blob): Promise<string> {
  return sha256(await blob.arrayBuffer());
}

export async function photoSignature(frames: Blob[], telemetry: Telemetry): Promise<string> {
  const frameHashes = await Promise.all(frames.map(bytesSignature));
  const { acc_m, captured_at, ...rest } = telemetry;
  const payload = { frames: frameHashes, ...rest, acc: acc_m, timestamp: captured_at };
  return sha256(new TextEncoder().encode(canonical(payload)));
}

export async function bundleSignature(photoSignatures: string[], form: GroundForm): Promise<string> {
  const payload = { photo_signatures: [...photoSignatures].sort(), form };
  return sha256(new TextEncoder().encode(canonical(payload)));
}

export { canonical };
