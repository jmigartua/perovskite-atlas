# ADR 0004 · Unreviewed thesis-only results are hidden by default

Status: accepted, 2026-09-26 (decision 5).

Decision: `visibility` ∈ {public, review, hidden}. Unpublished intermediate results (failed syntheses, unpublished magnetic models, unpublished temperatures) start as `hidden`. `make audit` fails if a hidden record reaches `_site/`. Review builds (`ATLAS_REVIEW=1`) render `review` records for the former students' review round (Phase 5).
