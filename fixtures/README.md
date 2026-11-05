# Synthetic demo case contract

`demo_cases.json` is a hand-authored, version 1 fixture set for the classroom prototype. It contains no real parcel, farmer, government, image, or satellite data. All percentage values are illustrative synthetic inputs, not measurements or policy thresholds.

## Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | integer (`1`) | Version of this fixture contract. |
| `id` | string | Stable synthetic case identifier. |
| `title` | string | Short display label for the scenario. |
| `data_status` | `SYNTHETIC` | Labels the whole case as synthetic. |
| `official_pct` | number or `null` | Synthetic illustrative official-assessment percentage. |
| `satellite_style_pct` | number or `null` | Synthetic illustrative satellite-style percentage; this is not computed from imagery. |
| `farmer_report_pct` | number or `null` | Synthetic illustrative farmer-reported percentage; it is not an actual farmer claim. |
| `review_threshold_pct` | number | Synthetic demo-only comparison line, not a compensation or eligibility policy. |
| `source_labels` | object | Per-measure provenance: `SYNTHETIC`, `SYNTHETIC_DEMO_RULE`, or `MISSING`. A missing measure must have a `null` value and `MISSING` label. |
| `status` | enum | `NEEDS_HUMAN_REVIEW`, `CONSISTENT_FOR_DEMO`, or `INSUFFICIENT_EVIDENCE`. These are illustrative case statuses, not decisions. |
| `reason` | string | Plain-language explanation tied to the displayed values; missing values are described as unknown. |

## Missing values and status meanings

- Use JSON `null` for unavailable evidence. Never replace it with `0`, an empty string, or an estimate.
- `NEEDS_HUMAN_REVIEW` means the illustrative sources conflict and a person should compare them.
- `CONSISTENT_FOR_DEMO` means the illustrative values are close in this example only.
- `INSUFFICIENT_EVIDENCE` means at least one needed source is missing; no comparison result is inferred from that missing source.
- `REVIEWED_FOR_DEMO` is reserved for a local review action on a submitted report. It is not a fixture-case status.

## Included scenarios

1. `CASE-DEMO-01` straddles the illustrative 33% demo line.
2. `CASE-DEMO-02` contains three close synthetic values.
3. `CASE-DEMO-03` keeps the satellite-style value missing (`null`).

The values and reasons are teaching examples only. They do not describe real farms, establish model accuracy, or determine compensation.
