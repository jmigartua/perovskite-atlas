# Interfaces between layers

- Records → `validate.py`: every file under the record directories must satisfy its schema and reference only existing ids.
- Records → `derive.py`: reads records and CIFs, writes `_data/computed/derived/*.parquet`; never writes records.
- `confront.py`: reads records and derived tables, writes `_data/computed/reports/confrontation.md`.
- `build.py`: writes `_data/computed/atlas.sqlite`, `parquet/`, `json/`, `cif/atlas-cifs.zip`, `atlas.bib`.
- `generate.py`: reads records and computed tables, writes `_gen/**/index.qmd`; templates in `_templates/`.
- `audit.py`: reads `_site/` and records; fails on hidden leaks and orphans.
