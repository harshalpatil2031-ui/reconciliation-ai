# Specification reference gaps

This register is the repository-facing resolution for X-04. It identifies references that cannot currently be followed from the files committed here and assigns an owner and a closure action. It does not claim missing documents have been recovered.

| Missing reference or gap | Where referenced | What is available now | Owner / action before pilot | Status |
|---|---|---|---|---|
| `Reconciliation_AI_Implementation_v2.md` | v3 says it supersedes v2; v3 §11 says v2 Sections 11–15 and Appendices A–B still apply | v3’s own validation, privacy, build-plan summary; relay risk R14 | P4: locate the approved v2 source or replace each required item with an explicit v3/relay section; do not assume omitted v2 content | Missing |
| `Reconciliation_AI_Detailed_Implementation_Plan.md` | v3 §11 and relay source-document header / pilot §10 | The four-owner relay provides implementation WPs; it is a substitute for many build steps but may not contain every original plan detail | P4: locate it or record which relay sections replace it; resolve any remaining requirement before pilot | Missing |
| v3 §15 external references | v3 status legend refers to sources listed in §15, but the committed v3 file ends at §11 and an appendix | `DATA_PROVENANCE.md` starter register; citations still need exact source URLs/product IDs | P1/P4: add direct citations and dates for every ✅ claim; maintain license/provenance records | Incomplete |
| v3 §7.5 | Relay traceability explicitly says this subsection is missing | No implementation requirement is available from that subsection | P3 with P4: confirm whether the gap affects a required behavior; document “not specified” or add an approved replacement without inventing requirements | Open |
| Grade rubric reference (§7.9 / grade dimensions) | v3 has a numbering gap; relay D-14/WP-3.7 supplies a rubric | Relay WP-3.7 contains the operational rubric and tests | P3: use WP-3.7 as the implementation source; record any later change in `contracts/CHANGELOG.md` | Replacement available; sign-off pending |
| Pilot validation and privacy appendix requirements | v3 §11 delegates to absent v2 sections/appendices | Summary safeguards in v3 and relay Sections 2.8, 6.1, 8, and 10; `DATA_PROVENANCE.md` | P4 coordinates; P1/P2/P3 review their data, photo, engine and audit controls; close before pilot authorization | Partial |

## Closure rule

For each row, link either (a) the recovered approved source, or (b) a replacement section that states the requirement, owner, evidence, and limitations. If a referenced requirement is irrelevant or unavailable, retain that explicit decision and risk in the pilot checklist. X-04 is complete only when every row is resolved or explicitly accepted as unavailable with an owner and plan.
