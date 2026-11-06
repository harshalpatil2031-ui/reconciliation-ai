import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

vi.mock('./offlineQueue', () => ({ enqueueBundle: vi.fn(), flushQueue: vi.fn(), listBundles: vi.fn().mockResolvedValue([]) }));
vi.mock('./lib/signature', () => ({ bundleSignature: vi.fn().mockResolvedValue('unused') }));
vi.mock('./CameraBurstCapture', () => ({ default: () => <div>camera mock</div> }));

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, '', '/');
});

describe('standalone prototype mode', () => {
  it('saves a farmer report through the local API and opens a synthetic officer review without sensors', async () => {
    window.history.replaceState({}, '', '/?demo=1');
    const report = { id: 'rpt-12345678', created_at: '2026-11-05T00:00:00Z', form: { damaged_share_pct: 65 }, status: 'NEEDS_HUMAN_REVIEW', review_note: null, official_pct: 20, satellite_style_pct: 40, explanation: 'Farmer report (65%) differs from the illustrative value.', data_status: 'synthetic demo example' };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/demo/cases')) return { ok: true, json: async () => [
        { id: 'CASE-DEMO-01', title: 'Near threshold', official_pct: 20, satellite_style_pct: 40, farmer_report_pct: 34, review_threshold_pct: 33, data_status: 'SYNTHETIC', status: 'NEEDS_HUMAN_REVIEW', reason: 'Sources differ.' },
        { id: 'CASE-DEMO-02', title: 'Agree', official_pct: 55, satellite_style_pct: 58, farmer_report_pct: 56, review_threshold_pct: 33, data_status: 'SYNTHETIC', status: 'CONSISTENT', reason: 'Values match.' },
        { id: 'CASE-DEMO-03', title: 'Missing', official_pct: 35, satellite_style_pct: null, farmer_report_pct: 42, review_threshold_pct: 33, data_status: 'SYNTHETIC', source_labels: { satellite_style_pct: 'MISSING' }, status: 'INSUFFICIENT', reason: 'Unavailable.' }
      ] };
      if (url.endsWith('/demo/reports') && init?.method === 'POST') return { ok: true, json: async () => report };
      if (url.endsWith('/demo/reports')) return { ok: true, json: async () => [] };
      return { ok: true, json: async () => report };
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);
    expect(screen.getByText(/Synthetic examples · Local prototype API · Nothing sent externally/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    fireEvent.click(screen.getByRole('button', { name: 'Start demo report' }));
    fireEvent.change(screen.getByLabelText('How much of your field is damaged?'), { target: { value: '65' } });
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save on this device' }));
    await waitFor(() => expect(screen.getByText(/not sent to any real service/)).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/demo/reports'), expect.objectContaining({ method: 'POST' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open officer view' }));
    expect(screen.getByText(/CASE-DEMO-01/)).toBeInTheDocument();
    expect(screen.getByText(/CASE-DEMO-03/)).toBeInTheDocument();
    expect(screen.getByText(/Missing evidence: Satellite-style value is unknown \(MISSING\); no value is inferred\./)).toBeInTheDocument();
    expect(screen.getByText(/Farmer-reported damage: 65%/)).toBeInTheDocument();
  });

  it('explains a failed save, keeps submission retryable, and shows the values returned by the API', async () => {
    window.history.replaceState({}, '', '/?demo=1');
    const report = {
      id: 'rpt-retry-1234', created_at: '2026-11-05T00:00:00Z',
      form: { damaged_share_pct: 65, water_depth_band: 'KNEE', water_days: 2, crop_stage: 'VEGETATIVE', note: null },
      status: 'NEEDS_HUMAN_REVIEW', review_note: null, official_pct: 31, satellite_style_pct: 37,
      explanation: 'Farmer report (65%) differs from the synthetic comparison values; ask a person to compare them.',
      data_status: 'synthetic demo example'
    };
    let submitAttempts = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/demo/cases')) return { ok: true, json: async () => [] };
      if (url.endsWith('/demo/reports') && init?.method === 'POST') {
        submitAttempts += 1;
        if (submitAttempts === 1) return { ok: false, status: 503, json: async () => ({ detail: 'unavailable' }) };
        return { ok: true, json: async () => report };
      }
      return { ok: true, json: async () => [] };
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    fireEvent.click(screen.getByRole('button', { name: 'Start demo report' }));
    fireEvent.change(screen.getByLabelText('How much of your field is damaged?'), { target: { value: '65' } });
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    fireEvent.click(screen.getByRole('button', { name: 'Save on this device' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/then retry/);
    expect(screen.getByRole('button', { name: 'Save on this device' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Save on this device' }));
    await waitFor(() => expect(screen.getByText(/not sent to any real service/)).toBeInTheDocument());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.getByText(/Official assessment: 31% · Satellite-style example: 37% · Farmer report: 65%/)).toBeInTheDocument();
    expect(screen.getByText(report.explanation)).toBeInTheDocument();
    expect(screen.getByText('synthetic demo example')).toBeInTheDocument();
    expect(submitAttempts).toBe(2);
  });

  it('records a custom officer review note, refreshes persisted reports, and resets demo reports', async () => {
    window.history.replaceState({}, '', '/?demo=1');
    const persistedReport = {
      id: 'rpt-officer-99',
      created_at: '2026-11-06T00:00:00Z',
      form: { damaged_share_pct: 70, water_depth_band: 'KNEE', water_days: 3, crop_stage: 'VEGETATIVE', note: 'Waterlogged corner' },
      status: 'NEEDS_HUMAN_REVIEW',
      review_note: null,
      official_pct: 20,
      satellite_style_pct: 40,
      explanation: 'Synthetic demo values: official assessment (20%), satellite-style example (40%), farmer report (70%).',
      data_status: 'synthetic demo example'
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/demo/cases')) {
        return {
          ok: true,
          json: async () => [
            {
              id: 'CASE-DEMO-01',
              title: 'Near threshold disagreement',
              data_status: 'SYNTHETIC',
              official_pct: 30,
              satellite_style_pct: 36,
              farmer_report_pct: 34,
              review_threshold_pct: 33,
              status: 'NEEDS_HUMAN_REVIEW',
              reason: 'Synthetic official example (30%) is below the illustrative 33% demo line.'
            }
          ]
        };
      }
      if (url.endsWith('/demo/reports/rpt-officer-99/review') && init?.method === 'POST') {
        const body = JSON.parse(String(init.body));
        return {
          ok: true,
          json: async () => ({
            ...persistedReport,
            status: 'REVIEWED_FOR_DEMO',
            review_note: body.note
          })
        };
      }
      if (url.endsWith('/demo/reports') && init?.method === 'DELETE') {
        return { ok: true, status: 204, json: async () => ({}) };
      }
      if (url.endsWith('/demo/reports')) {
        return { ok: true, json: async () => [persistedReport] };
      }
      return { ok: true, json: async () => ({}) };
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open officer demo' }));

    expect(await screen.findByText(/CASE-DEMO-01 · Near threshold disagreement \(SYNTHETIC\)/)).toBeInTheDocument();
    expect(screen.getByText(/Official 30% · Satellite-style 36% · Farmer report 34% · Demo threshold 33% · Demo result: NEEDS_HUMAN_REVIEW\./)).toBeInTheDocument();
    expect(screen.getByText(/Submitted field details: Water depth KNEE \(3 days\) · Crop stage VEGETATIVE · Farmer note: Waterlogged corner/)).toBeInTheDocument();

    const noteInput = screen.getByLabelText('Review note for rpt-officer-99');
    fireEvent.change(noteInput, { target: { value: 'Compare field drainage note with village talathi record' } });
    fireEvent.click(screen.getByRole('button', { name: 'Mark reviewed in demo' }));

    await waitFor(() => {
      expect(screen.getByText(/Status: REVIEWED_FOR_DEMO · Compare field drainage note with village talathi record/)).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/demo/reports/rpt-officer-99/review'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ note: 'Compare field drainage note with village talathi record' })
      })
    );

    fireEvent.click(screen.getByRole('button', { name: 'Reset demo reports' }));
    await waitFor(() => {
      expect(screen.getByText('No reports yet. Submit one from the farmer demo.')).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/demo/reports'), expect.objectContaining({ method: 'DELETE' }));
  });
});