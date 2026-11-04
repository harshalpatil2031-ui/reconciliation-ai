import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { describe, expect, it, vi } from 'vitest';
import App from './App';
import StructuredClaimForm from './StructuredClaimForm';
import en from './i18n/en.json';
import mr from './i18n/mr.json';
import type { GroundForm } from './lib/types';

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
});
