# Conventions

## Identifiers

| Kind | Pattern | Example |
|---|---|---|
| series | `ser:<template-slug>` | `ser:sr-ln-m-ruo6` |
| material | `mat:<formula-slug>` | `mat:srndznruo6`, `mat:sr2cd0.5ca0.5wo6` |
| sample | `smp:<material-slug>.<author><year>[.<n>]` | `smp:srndznruo6.iturbe2012` |
| dataset | `dat:<sample-slug>.<technique>.<instrument>.<T>k` | `dat:srndznruo6.iturbe2012.npd.d2b.300k` |
| structure | `str:<material-slug>.<sg-slug>.<T>k[.<x>].<author><year>` | `str:srndcoruo6.p42n.653k.iturbe2012` |
| refinement | `ref:<structure-slug>[.<variant>]` | `ref:srndznruo6.p21n.300k.iturbe2012.all-modes` |
| mode decomposition | `mod:<structure-slug>` | `mod:srndznruo6.p21n.300k.iturbe2012` |
| transition | `trn:<material-slug>.<from-sg>-<to-sg>.<author><year>` | `trn:srndznruo6.p21n-p42n.iturbe2012` |
| document | `doc:thesis-0N` or `doc:<doi-slug>` | `doc:thesis-03`, `doc:10.1016-j.jssc.2012.10.012` |
| plate / table | `plt:<doc-slug>.<n>` / `tbl:<doc-slug>.<n>` | `plt:thesis-03.5.12`, `tbl:thesis-03.5.4` |
| person | `per:<surname>-<initials>` | `per:iturbe-zabalo-e` |
| instrument | `ins:<facility>-<name>` | `ins:ill-d2b` |
| curve | `crv:<material-slug>.<kind>.<author><year>` | `crv:srlaferuo6.cell-vs-t.iturbe2012` |

Ids are lowercase ASCII; slugs replace anything else with `-`. Space-group slugs drop spaces, slashes and bars: `P2_1/n` → `p21n`, `Fm-3m` → `fm3m`, `R-3` → `r3b` (b = bar, to distinguish from `R3`), `I4/m` → `i4m`, `P4_2/n` → `p42n`. Ids are never reused or renamed; add `aliases: [...]` instead.

## Formulas

`formula` is the group's own site-ordered ASCII formula (`SrNdZnRuO6`, `Sr2Cd0.5Ca0.5WO6`). `formula_display` may carry subscripts for prose. `composition` is an element→count map. `sites` assigns elements to A, A', B, B', X. Solid solutions are a series with a numeric slot; each measured composition is its own material.

## Units and numbers

Å for lengths, degrees for angles, K for temperature, GPa for pressure, μB for moments, % for R factors. Reported values keep the parenthesis uncertainty notation as strings: `"5.5570(1)"`. The pipeline parses value and σ. Never round a reported value. Recomputed values live in the computed layer only.

## Status and visibility

`status`: `published` (in a paper), `thesis-only`, `re-derived` (from stored inputs by our pipeline), `unverified` (extracted, not confronted).
`visibility`: `public`, `review` (rendered only in review builds: `ATLAS_REVIEW=1 QUARTO_PROFILE=review quarto render`), `hidden` (never rendered). Records that are Quarto pages (materials, publications, theses, people) must carry `draft: true` in the front matter whenever their visibility is not public, so that Quarto leaves the page out of the output (`validate.py` enforces both directions); the generator gives such pages an empty include and never links to them. Thesis-only intermediate results (failed syntheses, unpublished magnetic models, unpublished temperatures) start as `hidden`.

## Evidence locators

```yaml
evidence:
  - doc: doc:thesis-03
    page: 112            # PDF page, when known
    md_line: 950         # line in sources/theses/thesis-03.md, always available
    table: "5.1"         # or figure: "5.12"
    cell: {row: "a", col: "SrNdZnRuO6"}
    bbox: [x, y, w, h]   # px on the 300 dpi page render, for the crop
    status: thesis-only
```

## Plates and rights

`rights`: `own` (own theses and own drawings), `publisher` (from a journal PDF), `reproduced` (regenerated from data by us). `reproduce`: `pending`, `done`, `not-needed`. Publisher plates are kept as reference for reproduction and are not distributed until reproduced or cleared.

## Files

One directory per record where a record owns files (structures, plates, tables, publications, theses, people, materials); one `.yaml` per record otherwise. YAML: two-space indent, keys in the order given by the schema, no tabs, strings quoted only when needed. CSV: UTF-8, header row, `,` separator, `.` decimal.

## Git

`main` is always renderable. Records and code in separate commits. Commit messages: `records: ...`, `pipeline: ...`, `site: ...`, `docs: ...`, `sources: ...`. Ingestion batches are pull requests with the review CSV attached.

## Generated pages

Record `.qmd` pages (materials, theses, people, publications) are their own pages and end with `{{< include /_gen/includes/<kind>/<slug>.md >}}`; `make generate` writes that include from the records. Yaml-kit records (series, structures, transitions, plates, tables) and all listing pages get a generated `index.qmd` (gitignored). Never edit a generated file; change the record or `_scripts/generate.py`.
