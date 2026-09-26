# ADR 0007 · fer (Framework for Experimental Results) as an export first, candidate record format at schema v0.2

Status: accepted, 2026-09-26.

Context: fer (Gabirondo-López, González de Arrieta, Arredondo, López, Anhalt, Igartua; IEEE Trans. Instrum. Meas. 74, 2025) defines a JSON-Schema structure for experimental results: `quantity_values` (values with `standard_uncertainties`, `units`, `coverages`, correlations), `measurement` (results, measurands, `source`), and `source` (model, `influence_quantities`, `input_quantities`) forming a traceability chain, with per-object changelogs. Reference implementation `ferpy` (PyPI). The atlas records currently keep reported numbers as strings in crystallographic notation (`"5.5570(1)"`) and provenance as document locators.

Decision:
1. Records stay as they are through Phase 1. Reported values remain crystallographic strings with document locators, because that is what the sources say and what a reviewer confronts with the page.
2. From Phase 2, `build.py` emits fer JSON in the computed layer for every refinement, mode decomposition and derived quantity: `quantity_values` from the parsed strings (value, standard uncertainty from the parenthesis digits, unit from the schema), `measurement` per refinement or decomposition, `source` chains linking a refined structure to its dataset (instrument, wavelength, temperature as influence quantities) and a derived quantity (tolerance factor, bond-valence sum, re-derived amplitude) to its inputs. Exports are validated against the fer schema.
3. If the export proves useful, fer objects become the record format for measured quantities at schema v0.2 by a one-script migration; the string form is kept as `reported` alongside for confrontation with the page. Evidence locators stay: fer describes how a number was obtained, the locator says where it was read.

Why not adopt fer in the records now: it would slow Phase 1 (rescue, plates, materials) for no visible gain, the fer schema is at v0.1 and may move, and the computed layer is exactly the place where a representation can be tried without touching the sources.

Consequences: no change to the entity model, the site or the pipeline verbs; one new export in `build.py`; the atlas becomes a fer application to crystallography and interoperates with EKHI tooling. Migration cost later is one script, because every measured string parses deterministically.
