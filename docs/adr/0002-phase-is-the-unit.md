# ADR 0002 · The structure at conditions is the unit of record

Status: accepted, 2026-09-26.

Decision: a `structure` record is one phase of one material at stated conditions (T, P, x) with cell, atoms, CIF, refinement, geometry and, when performed, mode decomposition. Materials aggregate structures; series aggregate materials by a variable slot; transitions connect two structures of one material.

Consequences: structure pages are the atom of the site; material pages are summaries; no field of a page is rendered empty.
