# Sources

- `theses/`   PDF and OCR Markdown of the four theses (`thesis-01.pdf`, `thesis-01.md`, …). Copy from the MatDB repository `sources_thesis/`.
- `articles/` PDF and Markdown of articles, named by DOI slug. Copy from MatDB `all_articles_thesis/` and `all_articles_no_thesis/`.
- `raw/`      rescued original data, `<thesis>/<chapter>/<original-name>`; see `rescue/RESCUE.md`. Large binaries go through git LFS.
- `rescue/`   inventory of what was found where.

Nothing under `sources/` is rendered. Everything under `sources/` is immutable once committed; corrections are new files.
