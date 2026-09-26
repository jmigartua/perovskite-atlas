# Data rescue procedure (Phase 1, first task)

1. List every location that may hold 2003–2015 files: old disks, student folders, supplementary material, e-mail attachments.
2. For each file: copy untouched into `sources/raw/<thesis>/<chapter>/`, keep the original name, add a row to `INVENTORY.csv` with `sha256`.
3. Kinds: `pcr` (FullProf control), `dat`/`xye`/`xy` (pattern), `prf` (fit), `out`/`sum` (FullProf output), `cif`, `amplimodes` (server output), `isodistort`, `raman`, `dsc`, `magnetization`, `notebook` (lab notes), `other`.
4. Never rename, never re-save. Convert only in the computed layer.
5. When the inventory is complete, run `make datasets` to propose dataset records from it.
