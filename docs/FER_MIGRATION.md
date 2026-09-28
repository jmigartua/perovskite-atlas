# Protocol: creating the fer version of the atlas records

Status: v1, 2026-09-28. Complements ADR 0007. "Migration" here means producing fer documents from the records; the records themselves stay as they are (plain-text, crystallographic notation, document locators).

## 1. Scope and principles

1. **Records are the source; fer documents are computed.** `_scripts/fer_export.py` reads the records and writes `_data/computed/fer/**.json`. Nothing is written back. Re-running regenerates everything deterministically from the same git commit.
2. **One fer document per measurement-like record.** Refined structure (with its refinement) → one `Measurement`. Mode decomposition → one `Measurement` whose `source.input_quantities` nests the structure document. Reported geometry → one `Measurement` nesting the structure document. Datasets appear as input `Measurement` stubs with empty `results` until the raw patterns are rescued.
3. **Deterministic identifiers.** fer `id` fields reuse the atlas ids (`str:…`, `mod:…`, `fnd:…`, `ref:…`, `dat:…`); quantity-value ids are `<record id>#<part>` (`#cell`, `#atom:O1`, `#amplitudes`, `#bonds`). No UUIDs: the atlas id is the citable, stable name and the fer file is reproducible.
4. **Provenance twice.** The fer `changelog` records when and from which git commit the document was generated. The atlas evidence (document, page, table, cell, status) travels in an `atlas` extension object on each `Measurement` and `QuantityValues`. Extension keys are additive; the vendored schema does not forbid them.
5. **Validation is mandatory.** Every document is validated against the vendored `_schemas/external/fer-schema.json` (draft-07) before it is written; invalid documents are listed in `_data/computed/reports/fer.md` and not written.

## 2. Field mapping

| Atlas | fer | Rule |
|---|---|---|
| `structure.cell` a, b, c, α, β, γ | `results[0]` QuantityValues "Unit cell" | six quantities, units Å and °, one value each |
| `structure.cell.volume` | QuantityValues "Cell volume" | Å³ |
| each `structure.atoms[i]` | QuantityValues "Atom ⟨label⟩" | quantities x, y, z (unit 1) and B_iso (Å²) when present; occupancy and "fixed" go in the description |
| `refinement.r_p … chi2` | QuantityValues "Rietveld reliability factors" | %, χ² unit 1; uncertainties 0, flagged unreported |
| `structure.conditions.temperature_k` | `state[0]` and `source.influence_quantities[0]` | K; uncertainty 0 and flagged until a reported one exists |
| `refinement` (software, method, variant, notes) | `source` of the structure measurement | `name`, `model`, `description` |
| `dataset` (technique, instrument) | `source.input_quantities[0]` (a Measurement stub) | results empty until raw data is attached |
| `modes.irreps[*].amplitude` | QuantityValues "Symmetry-mode amplitudes by irrep" | quantities are irrep labels, unit Å; parent, transformation and convention in `source.model`; the full irrep list (k-vector, isotropy subgroup, primary flag) in `atlas.irreps` |
| `geometry.bonds / angles / tilts / bvs / octahedra` | one QuantityValues each | Å, °, °, 1, Å³ or Å |
| `evidence`, `status`, `id`, `schema_version` | `atlas` extension | verbatim |

Not mapped, by design: series, materials, transitions, plates, tables, publications, theses, people. fer describes measurement results; those entities describe identity, documents and events and stay atlas-only. A transition temperature will be mapped once transitions carry a measured value with an uncertainty and a method (Phase 3).

## 3. Numbers and uncertainties

- Crystallographic notation `5.5570(1)` is parsed as value 5.5570 with standard uncertainty 0.0001 (the parenthesis gives the estimated standard deviation from the least-squares refinement on the last digits). `-0.0066(5)` → −0.0066 ± 0.0005. `0.750(1)` → 0.750 ± 0.001.
- A bare number (`90`, `2.1105`, `3.82`) has no reported uncertainty: `standard_uncertainties` is 0 and `atlas.uncertainty_reported` is `false` for that quantity. Consumers must not read 0 as "exact"; the flag is the truth. Values fixed by symmetry (α = γ = 90° in P2₁/n) are the common case.
- Values are never rounded or re-derived at export; `atlas.reported_as` keeps the original string.
- Units: Å, Å², Å³, °, K, %, and 1 for dimensionless quantities. Symbols are LaTeX as in the fer example (`$a$`, `$B_{\mathrm{iso}}$`, `$\chi^2$`).

## 4. Files

```
_data/computed/fer/
  index.json                     generated, git sha, fer schema version, list of documents
  structures/<slug>.json         one per refined structure (includes refinement and dataset stub)
  modes/<slug>.json              one per decomposition, nesting the structure document
  geometry/<slug>.json           one per geometry finding, nesting the structure document
_data/computed/reports/fer.md    counts, quantities without reported uncertainty, schema errors
```

The directory is computed (gitignored). Releases publish it as a zip with the SQLite and Parquet exports (Phase 4) and it is what a fer-aware tool such as `ferpy` reads.

## 5. Procedure

1. `make validate` (records must be valid).
2. `make fer` → runs `_scripts/fer_export.py`; read `_data/computed/reports/fer.md`.
3. Zero schema errors is the gate. Any error means either a record with an unparsable measured value (fix the record, it is the source) or a schema change upstream (re-vendor the schema, adjust the exporter, bump the version string in the exporter).
4. Spot-check one document per kind against its record (values, uncertainties, evidence). The first three checked documents are listed in § 7.
5. Commit the exporter changes; the fer files themselves are regenerated by the build, never committed.

## 6. Versioning and the promotion decision (schema v0.2)

- The vendored fer schema is copied with the date in the exporter's version string; upstream changes are adopted deliberately, not automatically.
- The atlas records stay at schema v0.1 while the fer export proves itself. Promotion to v0.2 (fer objects inside the records, with the reported string kept as `reported`) is decided after Phase 2 on three tests: the export has been consumed by at least one external tool without manual fixes; the extension keys (`atlas`) are either accepted upstream or stable; and no field needed by the site is lost in the round trip fer → record. The migration script for v0.2 is the inverse of this exporter and is written only then.

## 7. Worked check (first export)

Records from thesis 3, chapter 5 to 10 (19 refined structures, 19 decompositions, 19 geometry findings). Documents to check against their records: `structures/srndznruo6.p21n.300k.iturbe2012.json` (Table 5.1), `modes/srprcoruo6.p21n.300k.iturbe2012.json` (Table 6.4, column Co), `geometry/srlaferuo6.pbnm.300k.iturbe2012.json` (Table 9.2).

## 8. Questions for the fer authors

1. Are additive extension objects (`atlas`) acceptable, or should atlas provenance be encoded in `description` strings only?
2. Recommended representation of "uncertainty not reported": 0 with a flag (this protocol), `null`, or omission?
3. Should fixed-by-symmetry values be modelled as `state` rather than `results`?
4. Deterministic ids versus UUIDs: any consumer that requires UUID syntax?
