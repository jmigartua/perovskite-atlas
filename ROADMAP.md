# Roadmap and decision log

## Decisions (2026-09-26)

| # | Question | Decision | Consequence |
|---|---|---|---|
| 1 | Original data | Almost all FullProf `.pcr`/`.dat`, ILL/ESRF patterns, AMPLIMODES outputs and CIFs from 2003–2015 exist | Data rescue moves to Phase 1. Original CIFs and outputs become the primary source of structures and decompositions; rebuilding CIFs from tables becomes the fallback and a cross-check. Refinements can be re-run. |
| 2 | Scope | Perovskites only for the first release | Envelope stays general; non-perovskite work waits for Phase 5. |
| 3 | Name and palette | Perovskite Atlas; teal / gold / oxygen red on cool-green paper | Kit ported from igartua-site and retinted. |
| 4 | Hosting | Under the igartua site | GitHub Pages project page at `jmigartua.github.io/perovskite-atlas/`; a true subdomain needs a custom domain first. Assumed private (repository private, site not linked) until Phase 2. |
| 5 | Thesis-only results | Marked and hidden until reviewed | `visibility: hidden` by default for unpublished intermediate results; audit blocks leaks. |
| 6 | Contributors | Former students review at the end | Phase 5 review round with per-chapter review CSVs; pull-request workflow prepared now. |
| 7 | Figures and licence | Use every figure now; reproduce paper figures from data later | `rights` and `reproduce` fields on plates; the plates gallery doubles as the reproduction queue. |
| 8 | First analyses | § 7.2 (primary-mode amplitude vs radius and tolerance factor) and § 7.3 (phase-route map) | Phase 2 extracts RT mode amplitudes and transition sequences for every material first; other tables follow. |

## Phases

### Phase 0 · Foundations (now → 2 weeks)
- [x] Repository scaffolded with the three layers, kit, schemas v0.1, pipeline verbs, conventions, ADRs
- [x] Worked example: SrNdZnRuO₆ at RT (thesis 3, ch. 5) as series, material, structure, modes, geometry, transitions, table, plate
- [x] `make validate` green on the example; `quarto render` green
- [x] GitHub repository created (private, github.com/jmigartua/perovskite-atlas), Pages workflow
- [ ] First tag `v0.0.1`; Pages on a private repository needs a paid plan, otherwise switch the repository to public (unlinked) when the site should go live
- [x] 45 perovskite publications imported from jmi-db (22 with local PDF + OCR Markdown), four theses and five people recorded

### Phase 1 · Data rescue, plates, tables and the map (weeks 3–10)
- [ ] Inventory of original data: `sources/rescue/INVENTORY.csv` filled (one row per file: origin disk, path, sha256, kind, material, thesis chapter)
- [ ] Rescued files copied under `sources/raw/<thesis>/<chapter>/` with checksums; datasets records created
- [ ] Plates and tables cropped locally from the 4 theses and 28 articles (bboxes from the Mathpix URLs), captioned, typed, linked to materials
- [ ] Series and materials entered from the inventory CSV with proper identity
- [ ] Composition grid on the home page; series, material and plates pages live
- [ ] Coverage and evidence audits running

### Phase 2 · Structures and modes for analyses 2 and 3 (weeks 11–22)
- [ ] For every material: RT structure with CIF (original where rescued), RT mode decomposition, transition sequence with temperatures and order
- [ ] Physics confrontation (bond lengths, BVS from CIF vs reported) on every RT structure
- [ ] Notebooks: amplitude vs radius / tolerance factor; phase-route map
- [ ] Structure pages with 3D view and mode panel; transitions page; modes explorer v1
- [ ] Papers linked to chapters; `published` vs `thesis-only` set

### Phase 3 · Every temperature, every table (weeks 23–32)
- [ ] All non-RT structures, all geometry tables, magnetic structures, solid solutions
- [ ] Re-derived decompositions from rescued parent/child/transformation kits
- [ ] Theses 1 and 2 (Spanish) complete

### Phase 4 · Analysis and openness (weeks 33–40)
- [ ] Remaining notebooks (§ 7 of the proposal); data page; DuckDB-WASM query page; OPTIMADE-style JSON
- [ ] Public release: repository public, site linked from igartua, Zenodo DOI

### Phase 5 · Review and extension (ongoing)
- [ ] Former students review their chapters (review CSVs, pull requests)
- [ ] Paper figures reproduced from data; publisher plates retired
- [ ] Non-perovskite work in the same envelope
