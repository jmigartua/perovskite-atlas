# ADR 0003 · Every value carries an evidence locator

Status: accepted, 2026-09-26.

Decision: records without `evidence` fail validation. A locator names a document and a position (`page` and/or `md_line`, plus `table`/`figure`, `cell`, `bbox`). Status (`published`, `thesis-only`, `re-derived`, `unverified`) is explicit per value or per record.

Consequences: thesis-only results are countable and filterable; page crops can be rendered for any value; ingestion must be schema-constrained.
