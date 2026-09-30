# Perovskite Atlas

A knowledge base of thirty years of research on perovskite-type oxides at UPV/EHU: crystal structures, symmetry-mode decompositions, phase transitions, figures, tables, articles and theses, with every value traced to its source page.

Design document: `docs/PROPOSAL.md` (v2, 2026-09-25) and the decision log in `ROADMAP.md`.

## Three layers

| Layer | Where | Rule |
|---|---|---|
| Source (human-edited, git is the truth) | `series/ materials/ samples/ datasets/ structures/ transitions/ magnetic/ findings/ plates/ tables/ publications/ theses/ people/ instruments/ sources/` | typed files with YAML front matter or `.yaml`; every value has evidence |
| Computed (machine-generated) | `_data/computed/` | SQLite, Parquet, JSON, CIF zip, crops, reports; never hand-edited, not committed |
| Presentation (rendered) | generated `index.qmd` next to yaml records (gitignored), `_gen/`, `_site/` | record `.qmd` files are their own pages; yaml-kit records get a generated page; never hand-edited, not committed |

Build scripts must not write into the source layer. Ingestion scripts write to a review queue; a human moves records into the source layer.

## Quick start

```bash
python3 -m pip install -r requirements.txt
make validate        # schemas, references, units, space groups, evidence
make derive          # tolerance factors, volumes, geometry from CIF, decompositions
make confront        # reported vs recomputed -> _data/computed/reports/confrontation.md
make build           # sqlite, parquet, json, cif zip, bibtex
make generate        # entity pages -> _gen/
quarto preview       # site
make audit           # orphans, missing evidence, hidden records leaking, coverage
```

`make validate` halts on any error; the site never renders from inconsistent data.

## Layout

```
_schemas/     JSON Schema (YAML) per entity, INTERFACES.md
_scripts/     pipeline, one module per verb
_data/        config.yml (vocabularies, radii); computed/ (ignored)
sources/      documents (PDF, OCR markdown) and rescued raw data; see sources/README.md
docs/         proposal, ADRs, ingestion procedure
series/ materials/ structures/ transitions/ plates/ tables/ ...   the records
notebooks/    reproducible analyses (Quarto)
assets/       family design kit (theme.css, includes)
```

## Conventions

See `CONVENTIONS.md`: identifiers, formula canonicalization, units, uncertainty notation, statuses, visibility, file naming.

## Licence

Data, text and own figures: CC BY 4.0. Code: MIT. Figures reproduced from publisher PDFs are held for reproduction from data (see ADR 0005) and are not yet redistributable.

## Search

`/search/` indexes every public record (materials, structures, transitions, series, curves, plates, tables, publications, theses, people, instruments). Free words match titles, formulas, captions and notes; keywords narrow: `kind:`, `el:`, `sg:`, `irrep:`, `tech:`, `fig:`, `doc:`, `status:`, `year:`, `series:` and temperature constraints `T:300`, `T>600`, `T:600-900`; `-word` excludes. The index is `_data/computed/search/index.json`, written by `generate.py`; the page keeps the query in the address bar. Press `/` anywhere to search.
