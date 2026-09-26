# ADR 0006 · Rescued original files are the primary source; tables are the cross-check

Status: accepted, 2026-09-26 (decision 1).

Context: almost all FullProf `.pcr`/`.dat`, ILL/ESRF raw patterns, AMPLIMODES outputs and CIFs from 2003–2015 still exist.

Decision: data rescue is Phase 1. Structures and decompositions are built from original CIFs and outputs where they exist; tables in theses and papers are extracted as well and confronted against them. Where an original is missing, the CIF is rebuilt from the table and verified against reported geometry (ADR 0003 pipeline).

Consequences: refinements can be re-run; patterns can be plotted; `sources/raw/` needs checksums and an inventory with origin (disk, folder, student).
