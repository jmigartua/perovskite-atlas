# ADR 0001 · Plain-text records in git are the source of truth

Status: accepted, 2026-09-26.

Context: the first approach (MatDB, 2026-01) made a hand-seeded SQLite file the source of truth. Provenance stayed empty, the schema outran the data, and diffs were unreadable.

Decision: typed records (YAML front matter `.qmd` or `.yaml`), CIF, CSV and PNG in git are the truth. SQLite, Parquet, JSON, crops and the site are computed, never hand-edited, not committed. Build scripts never write into records.

Consequences: every change is a reviewable diff; validation lives in scripts, not a database engine; scale ceiling is thousands of records, far above this corpus; same pattern as thermomat and jmi-db.
