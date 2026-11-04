import type { CropStage, GroundForm, WaterDepth } from './lib/types';

interface Props { value: GroundForm; onChange: (next: GroundForm) => void; copy: Record<string, string>; locale: 'mr' | 'en' }

const depths: Array<[WaterDepth, string]> = [
  ['ANKLE', 'depth_ankle'], ['KNEE', 'depth_knee'], ['WAIST', 'depth_waist'],
  ['ABOVE_WAIST', 'depth_above'], ['NONE', 'depth_none']
];
const stages: Array<[CropStage, string]> = [
  ['SOWN_ONLY', 'stage_sown'], ['VEGETATIVE', 'stage_vegetative'],
  ['FLOWERING', 'stage_flowering'], ['PODDING_OR_MATURE', 'stage_mature']
];

export default function StructuredClaimForm({ value, onChange, copy, locale }: Props) {
  const patch = (part: Partial<GroundForm>) => onChange({ ...value, ...part });
  const number = new Intl.NumberFormat(locale === 'mr' ? 'mr-IN-u-nu-deva' : 'en-IN');
  return <section className="card form-card">
    <label className="question" htmlFor="damage">{copy.damage_q}</label>
    <div className="damage-readout"><button type="button" aria-label={copy.decrease} onClick={() => patch({ damaged_share_pct: Math.max(0, value.damaged_share_pct - 5) })}>−</button>
      <output>{number.format(value.damaged_share_pct)}%</output>
      <button type="button" aria-label={copy.increase} onClick={() => patch({ damaged_share_pct: Math.min(100, value.damaged_share_pct + 5) })}>+</button></div>
    <input id="damage" type="range" min="0" max="100" step="5" value={value.damaged_share_pct}
      onChange={(event) => patch({ damaged_share_pct: Number(event.target.value) })} />
    <div className="range-labels"><span>0–30</span><span>35–60</span><span>65–100</span></div>

    <fieldset><legend>{copy.depth_q}</legend><div className="choice-grid">
      {depths.map(([code, key]) => <button type="button" key={code} className={value.water_depth_band === code ? 'choice selected' : 'choice'}
        aria-pressed={value.water_depth_band === code} onClick={() => patch({ water_depth_band: code })}>{copy[key]}</button>)}
    </div></fieldset>
    <label className="question" htmlFor="water-days">{copy.days_q}</label>
    <div className="stepper"><button type="button" aria-label={`${copy.decrease} ${copy.days_q}`} onClick={() => patch({ water_days: Math.max(0, value.water_days - 1) })}>−</button>
      <output>{number.format(value.water_days)}</output>
      <button type="button" aria-label={`${copy.increase} ${copy.days_q}`} onClick={() => patch({ water_days: Math.min(14, value.water_days + 1) })}>+</button></div>
    <fieldset><legend>{copy.stage_q}</legend><div className="choice-grid">
      {stages.map(([code, key]) => <button type="button" key={code} className={value.crop_stage === code ? 'choice selected' : 'choice'}
        aria-pressed={value.crop_stage === code} onClick={() => patch({ crop_stage: code })}>{copy[key]}</button>)}
    </div></fieldset>
    <label className="question" htmlFor="note">{copy.note_opt}</label>
    <textarea id="note" maxLength={300} rows={3} value={value.note ?? ''} onChange={(event) => patch({ note: event.target.value || null })} />
  </section>;
}
