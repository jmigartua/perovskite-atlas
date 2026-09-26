# Ingestion procedure

Stages, each with a verification loop. See the proposal § 5.

A. **Rescue** original files → `sources/raw/`, checksums, `sources/rescue/INVENTORY.csv`, dataset records.
B. **Crop** plates and tables from PDFs (300 dpi renders; bboxes from Mathpix URLs) → `plates/`, `tables/`.
C. **Extract** records per chapter with locators, into `_data/review/<batch>.csv`; human review; approved rows become records (pull request).
D. **Confront**: CIF from table vs original CIF; geometry recomputed vs reported; decomposition re-run vs reported. Disagreements listed, never silently fixed.
E. **Link** chapters to papers; set `status` and `visibility`.

Order: theses 3 and 4, their papers, theses 2 and 1, the eleven other articles. Within each, first RT structures, RT decompositions and transition sequences (analyses 2 and 3), then the rest.
