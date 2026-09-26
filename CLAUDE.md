# Perovskite Atlas — repository rules

- Source of truth is the plain-text records (`series/ materials/ structures/ transitions/ plates/ tables/ publications/ theses/ people/ ...`). Never edit `_data/computed/`, `_gen/` or `_site/` by hand; never write computed values back into records.
- A value without `evidence` does not enter a record. Locators need `doc` and at least one of `page`, `md_line`; add `table`/`figure` and `cell` when known.
- Identifiers follow `CONVENTIONS.md` (`mat:`, `ser:`, `str:`, `trn:`, `mod:`, `doc:`, `plt:`, `tbl:`, `per:`). Never reuse or rename an id; add `aliases`.
- Formulas: perovskite site order as written by the group (A2BB'O6), ASCII in ids and tables, subscripts only in prose.
- Uncertainties stay in parenthesis notation as strings (`5.5570(1)`); the pipeline parses them.
- `visibility: hidden` records must never reach `_site/`; `make audit` checks it. Thesis-only intermediate results start as `hidden` until reviewed.
- Plates from publisher PDFs carry `rights: publisher` and `reproduce: pending`; own theses `rights: own`.
- Run `make validate` before committing records. Commit records and code separately.
- Design kit: `theme: none`, `assets/styles/theme.css` tokens only; no Bootstrap, no icon fonts, no gradients, no placeholder numbers on pages.
- The old MatDB repository (`~/Desktop/2026/20260100/20260122_JMI_database_project`) is read-only reference: its inventory CSV, ORCID JSON, article PDFs/markdown and per-thesis extraction files are inputs to ingestion, nothing else is carried over.
