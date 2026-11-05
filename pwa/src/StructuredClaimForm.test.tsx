import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import StructuredClaimForm from './StructuredClaimForm';
import en from './i18n/en.json';
import mr from './i18n/mr.json';
import type { GroundForm } from './lib/types';

vi.mock('./CameraBurstCapture', () => ({
  default: ({ onCapture }: { onCapture: (photo: { signature: string; telemetry: { lat: number; lon: number; acc_m: number; azimuth_deg: number | null; pitch_deg: number | null; captured_at: string }; frames: Blob[]; inAppCapture: boolean }) => void }) =>
    <button onClick={() => onCapture({ signature: 'photo-1',
      telemetry: { lat: 18.5, lon: 73.9, acc_m: 5, azimuth_deg: 90, pitch_deg: 75, captured_at: new Date().toISOString() },
      frames: [new Blob(['frame'], { type: 'image/jpeg' })], inAppCapture: true })}>Capture test photo</button>
}));

vi.mock('./offlineQueue', () => ({
  enqueueBundle: vi.fn(),
  flushQueue: vi.fn().mockResolvedValue(undefined),
  listBundles: vi.fn().mockResolvedValue([])
}));

const initial: GroundForm = {
  damaged_share_pct: 50, water_depth_band: 'NONE', water_days: 0,
  crop_stage: 'VEGETATIVE', note: null
};

describe('Marathi and English intake', () => {
  it('has matching translation keys', () => {
    expect(Object.keys(mr).sort()).toEqual(Object.keys(en).sort());
  });

  it('keeps form values within the contract ranges and uses Marathi digits', () => {
    const onChange = vi.fn();
    const { rerender } = render(<StructuredClaimForm value={initial} onChange={onChange} copy={mr} locale="mr" />);
    const damage = screen.getByLabelText(mr.damage_q);
    fireEvent.change(damage, { target: { value: '100' } });
    expect(onChange).toHaveBeenCalledWith({ ...initial, damaged_share_pct: 100 });
    expect(screen.getByText('५०%')).toBeInTheDocument();

    rerender(<StructuredClaimForm value={{ ...initial, damaged_share_pct: 100, water_days: 14 }} onChange={onChange} copy={mr} locale="mr" />);
    expect(screen.getByText('१४')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: mr.depth_none })).toHaveAttribute('aria-pressed', 'true');

    rerender(<StructuredClaimForm value={initial} onChange={onChange} copy={en} locale="en" />);
    expect(screen.getByLabelText(en.damage_q)).toBeInTheDocument();
    expect(screen.getByLabelText(en.note_opt)).toHaveAttribute('maxLength', '300');
  });

  it('requires explicit consent before opening the form and supports language switching', async () => {
    window.history.replaceState({}, '', '/?case=case-123&t=test-token');
    render(<App />);
    const start = screen.getByRole('button', { name: mr.start_report });
    expect(start).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(start).toBeEnabled();
    fireEvent.click(start);
    expect(screen.getByLabelText(mr.damage_q)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    expect(screen.getByLabelText(en.damage_q)).toBeInTheDocument();
  });

  it('keeps the camera step mounted after the first photo so the second-photo gate is retained', () => {
    window.history.replaceState({}, '', '/?case=case-456&t=test-token');
    render(<App />);
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: mr.start_report }));
    fireEvent.click(screen.getByRole('button', { name: mr.continue }));
    fireEvent.click(screen.getByRole('button', { name: 'Capture test photo' }));
    expect(screen.getByRole('button', { name: mr.skip_second })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: mr.continue })).not.toBeInTheDocument();
  });
});
