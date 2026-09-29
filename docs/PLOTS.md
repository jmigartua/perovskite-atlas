# Study: plots, temperature series and comparison

Status: v1, 2026-09-29. Requested as "the evolution of the cell parameters with temperature, or of the modes; and a way to mix the plots for comparison, as in EKHI". A first prototype ships with this study (see § 7).

## 1. What EKHI does (observed on thermomat.ehu.eus/ekhi, 2026-09-29)

- One page per publication. Materials of the publication are tabs; each tab has **one Plotly plot with every curve** of that material (e.g. "Normal spectral reflectance of OXIDE MINERALS", x = wavelength, y = reflectance), lines and markers, legend "Curve 1 … n", Plotly modebar (zoom, pan, save PNG).
- Below the plot, one card per curve: conditions (temperature, wavelength range, geometry), composition and remarks, and three actions: **Download JSON** (the fer measurement), **See source**, **View Table**.
- Library: plotly.js 3.1 from cdn.plot.ly. Data is embedded in the page (`Plotly.newPlot` with inline JSON). Publication-level actions: Download BibTeX, How to cite, Download dataset.
- Not present: comparing curves across publications, changing axes or units, error bars, normalisation. Selection is implicit (everything in the tab is plotted).

So the atlas can reuse the good parts (Plotly, one default plot per object, per-curve JSON/source/table) and add what EKHI lacks: a cross-record comparison with explicit selection, uncertainties, and physically meaningful scales.

## 2. What the atlas has to plot

Three families of x–y data, all with standard uncertainties:

| Family | x | y | Where the points come from | Status today |
|---|---|---|---|---|
| Cell vs T | temperature | a, b, c (reduced or not), β, V | tables at several T (thesis 3 Table 9.9; article on La₂CoMnO₆); figures kind `cell-vs-t` (73 plates); rescued sequential refinements | 1 curve from a table |
| Modes vs T | temperature | amplitude per irrep, signed | tables (thesis 3 Table 5.6, 6.7); figures kind `amplitude-vs-t` (40 plates); rescued AMPLIMODES/FullProf outputs | 1 curve from a table |
| Property vs T or x | temperature or composition | magnetic moment, tilt angles, bond lengths, R factors, T_c vs tolerance factor | tables (Table 9.9 moment), series pages (across materials) | 1 curve (moment) |

Point provenance matters and is stored per curve as `point_status`: `table` (read from a table), `digitised` (read off a figure), `rescued` (from the original refinement files), `derived` (computed from structure records). The same physical curve may exist twice with different statuses; the site shows both and the rescued one is the reference.

## 3. Data model

A **curve** is a record (`curves/<material>.<kind>.<source>/curve.yaml` + `curve.csv`, schema `_schemas/curve.schema.yaml`):

- `x`: one quantity with symbol, unit and CSV column.
- `y`: one or more quantities, each with symbol, unit, column, an optional `group` (cell, volume, amplitude…) so that the site never puts Å and Å³ on one axis, and an optional `phase`.
- `csv`: columns `T, a, a_u, b, b_u, …`; `_u` is the standard uncertainty, empty when not reported; an optional `phase` column labels each point with its space group (used for the P2₁/n → P4₂/n series of SrNdCoRuO₆).
- `point_status`, `technique`, `instrument`, `phase`, `structures` (structure records behind the points, when they exist), `reproduces` (plates the curve reproduces), `evidence` (the table or figure locator, as everywhere).

Curves are records because they are read from sources with a locator. A second, computed kind of curve is derived at build time from structure records of the same material at different temperatures (once Phase 3 adds them): those carry `point_status: derived` and are regenerated, not stored.

### fer

A curve is one fer `Measurement`; each y quantity is one `QuantityValues` with two quantities (x and y) and array values: `values: [[T…], [a…]]`, `standard_uncertainties: [[0…], [u_a…]]`. This is fer's native shape for a series and needs no extension; point provenance and phase labels go in the `atlas` extension. Curves are exported by `make fer` under `fer/curves/` and the fer view renders them as a points table plus the plot.

## 4. Plots on the site

- **Plotly.js 3.1** (as EKHI; consistent for users of both). Loaded only on pages that contain a plot. Colours, fonts and grid come from the design tokens, so plots follow the light and dark themes. Every plot has error bars, hover with phase, and SVG export from the modebar.
- **Default plots.** Material page: one plot per y-group of each curve of that material (reduced cell parameters; cell volume; mode amplitudes; moment). Curve page: the same plus the points table and the actions. Series page (next): one curve per member for the chosen quantity. fer page: the plot next to the fer table.
- **Physically meaningful scales.** Cell lengths are drawn **reduced** by default (a/√2, b/√2, c/2 for monoclinic and orthorhombic; a/√2, c/(2√3) for rhombohedral; a/2 for cubic), which is what the theses plot and what makes phases comparable; the raw values are one click away. Amplitudes keep their sign as reported. A "relative to first point" scale allows curves of different quantities to be compared.
- **Transitions on the plot.** For any curve versus temperature, the material's transition records are drawn as dotted vertical lines with the from → to space groups, so the plot and the transitions table can never disagree.

## 5. Comparison ("bring to the plot")

- Every curve, on its page and on its material page, has **Add to comparison**. The selection ("basket") is kept in the browser (localStorage) and shown as a count in the header. The **Plot** page draws the basket: pick one quantity or all, reduced or raw cell, as-reported or relative scale, error bars, log y. Each curve gets a colour and a marker; the list under the plot has remove buttons.
- **Links instead of state.** `/plot/?c=crv:…,crv:…` draws exactly those curves, so a comparison can be sent to a colleague or put in a paper's supplementary material; "Copy link" builds it. "Download CSV" exports the plotted points in one tidy table (curve, material, x, quantity, value, u).
- Default comparison sets are one line of generator code away: a series page will offer "compare all members" (the SrLnMRuO₆ amplitudes vs T once digitised), and a material page "compare with the other Ln".

## 6. Where the points will come from, in order

1. **Tables (now).** Every table with a temperature or composition axis becomes a curve by a small ingestion script, like the two of thesis 3 done here. Candidates already extracted: La₂CoMnO₆ 2–300 K (article c5dt01532d, Table 3), SrLaMnRuO₆ and SrLaCuRuO₆ RT/HT pairs (thesis 1), the Sr₂Co₁₋ₓFeₓTeO₆ composition series (thesis 4 articles), all `x`-series in the antimonates.
2. **Digitised figures (Phase 2–3).** 113 plates of kinds `cell-vs-t` and `amplitude-vs-t`. Procedure: open the plate, calibrate the axes on two ticks each, click the points (WebPlotDigitizer or a small in-site tool on the plate page), save as `curve.csv` with `point_status: digitised`, uncertainty from the symbol size, evidence = the plate. The curve page then shows the plate and the digitised curve side by side, which is also the check.
3. **Rescued refinements (Phase 3).** The FullProf `.sum`/`.out` files of the sequential refinements give every temperature the group ever measured, with uncertainties: hundreds of points per material instead of five. A parser writes one curve per material and quantity with `point_status: rescued`, and the structure records for every temperature. Digitised curves are then retired or kept as the "as published" version.
4. **Derived (Phase 3–4).** From the structure records: tolerance factor vs T, tilt angles vs T (recomputed from the CIFs), amplitude vs tolerance factor across a series (analysis 2 of the roadmap), T_c vs tolerance factor (analysis 1).

## 7. Prototype shipped with this study

- Records: `curves/srlaferuo6.cell-vs-t.iturbe2012` (a, b, c, V at 2–250 K, Table 9.9), `curves/srlaferuo6.moment-vs-t.iturbe2012` (Fe/Ru moment, same table), `curves/srndcoruo6.modes-vs-t.iturbe2012` (GM4⁺, X3⁺, X5⁺ in P2₁/n at 300–603 K and GM3⁺, GM4⁺, X3⁺, X5⁺ in P4₂/n at 653–953 K, Table 5.6).
- Site: curve pages with plot, points table and actions; temperature-evolution section on the two material pages with transitions drawn; `/curves/` listing; `/plot/` comparison page; **Plot** entry with the basket count in the header; fer documents for the three curves and their pages in the fer view.
- Scripts: `_scripts/ingest_curves_thesis03.py`, plot code in `assets/includes/atlas-plots.html`, curve JSON written by `generate.py` to `_data/computed/curves/`.

## 8. Decisions to take

1. Reduced-cell conventions per space group (the ones above follow the theses; confirm for I2/m and the tetragonal I4/m settings).
2. Whether digitisation is done in the site (a small tool on each plate page, points saved by pull request) or with WebPlotDigitizer and a CSV drop.
3. Whether curves from different techniques for the same quantity (XRPD vs NPD) are separate curves (proposed) or one curve with a technique column.
4. Fits: Landau-type fit of the primary amplitude (A ∝ (T_c − T)^β, as in thesis 4, Figure 6.8) as a derived object with its own fer document.
