"""Thesis 4 (Orayech 2015), phase B: the antimonates A2MSbO6, M = Nd, Eu, Gd, Dy, Ho, Y, Er, Tm, Yb.

- Sr2MSbO6 (chapter 8, published as Polyhedron 123 (2016) 265, doi 10.1016/j.poly.2016.09.066): synthesis and tolerance
  factors (Table 8.1 = article Table 1), RT structures P2_1/n from synchrotron XRPD at BM25-A (ESRF) with the GM4+, X3+ and
  X5+ amplitudes (Table 8.2 = article Table 2), the two high-temperature transitions P2_1/n → R-3 (discontinuous) and
  R-3 → Fm-3m (continuous) with the temperatures given in § 8.2 (laboratory XRPD, 300–1475 K).
- Ca2MSbO6 (Part III, "M3+ size effect in the Ca2MSbO6 (M = Ln, Y) …", in preparation at the time of the thesis):
  RT structures P2_1/n from laboratory XRPD with partial Ca/M antisite disorder (Table 10.4). Thesis-only, unpublished
  results: visibility `review` until the author checks them. Table 10.5 gives P2_1/n as the only phase (no HT study).

Site labels for M and Sb (special positions, no coordinates in the tables) are assigned from the setting of each table
and flagged `fixed`, as in phase A.
"""
from __future__ import annotations
import csv, re, yaml
from common import ROOT
from ingest_thesis03 import plain_caption, clean_num, is_num, dump, slug, sgslug, composition, IRREP_META, PHYS, SG

DOC = "doc:thesis-04"; SRC = "orayech2015"; SV = "0.1"
POLY = "doc:10.1016-j.poly.2016.09.066"
T4 = ROOT / "tables/thesis-04"
M = ["Nd", "Eu", "Gd", "Dy", "Ho", "Y", "Er", "Tm", "Yb"]
# § 8.2 (md_line 1820 and 1822/1842): P2_1/n → R-3 and R-3 → Fm-3m temperatures, in the order of M above
T1 = [925, 825, 800, 750, 725, 675, 675, 625, 500]
T2 = [1200, 1150, 1100, 975, 925, 875, 875, 850, 750]
SG["R-3"] = SG.get("R-3", (148, "trigonal", "hexagonal axes"))

def md_line_of(table): return next(e["md_line"] for e in yaml.safe_load((T4 / table / "table.yaml").read_text())["evidence"] if e.get("md_line"))
def rows(table):
    with (T4 / table / "table.csv").open() as f: return [[c.strip() for c in r] for r in csv.reader(f)]
def ev(table, col=None, status="thesis-only", **extra):
    e = {"doc": DOC, "md_line": md_line_of(table), "table": table, "status": status}
    if col: e["cell"] = {"col": col}
    e.update(extra); return e
POLY_LINES = {"1": 64, "2": 126, "3": 186, "fig9": 238, "exp": 60}   # md_line of sources/articles/10.1016-j.poly.2016.09.066.md
def ev_poly(table, col=None, **extra):
    e = {"doc": POLY, "md_line": POLY_LINES[table], "status": "published", **({"table": table} if table in ("1", "2", "3") else {})}
    if col: e["cell"] = {"col": col}
    e.update(extra); return e
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")

def parse_8_1():
    """Table 8.1: ionic radius, Δr, tolerance factor, synthesis temperature, impurities (rows without a compound are literature values)."""
    out = {}
    for r in rows("8.1")[1:]:
        f = plain_caption(r[0]).replace(" ", "")
        if not f: continue
        imp = plain_caption(r[5]).strip().replace("leqslant", "≤").replace("leq", "≤")
        imp = re.sub(r"([A-Za-z0-9])\s+([A-Z])", r"\1\2", imp) if "%" in imp else imp
        out[f] = {"ionic_radius": clean_num(r[1]), "delta_r": clean_num(r[2]), "t": clean_num(r[3]), "synth_k": clean_num(r[4]), "impurity": imp, "sg": plain_caption(r[6]).strip()}
    return out

def parse_structures(table, formulas):
    """Tables 8.2 / 10.4: one column per M; rows 'site, param, v1 … v9'. Returns atoms, occupancies, cell, amplitudes per formula."""
    R = rows(table); out = {f: {"atoms": {}, "occ": {}, "cell": {}, "modes": {}} for f in formulas}
    atom = None; section = None
    for r in R[1:]:
        lab = plain_caption(r[0]).strip(); par = plain_caption(r[1]).strip() if len(r) > 1 else ""
        if lab:
            if lab.startswith("Occupancy"): section = "occ"
            elif lab.startswith("B"): section = "biso"
            elif lab.startswith("Cell"): section = "cell"
            elif lab.startswith("Modes"): section = "modes"
            else: section = "atom"; atom = re.sub(r"\s*\(\s*4e\s*\)", "", lab).replace(" ", "")
        for f, v in zip(formulas, r[2:]):
            v = clean_num(re.sub(r"\s+\(", "(", plain_caption(v)))
            if not is_num(v): continue
            if section == "atom" and par in ("x", "y", "z"): out[f]["atoms"].setdefault(atom, {})[par] = v
            elif section == "biso":
                for lab2 in [s.strip() for s in par.split(",")]: out[f]["atoms"].setdefault(lab2, {})["b_iso"] = v
            elif section == "occ": out[f]["occ"][par.replace(" ", "")] = v
            elif section == "cell":
                key = re.match(r"^(a|b|c|β|V)", par)
                if key: out[f]["cell"][{"a": "a", "b": "b", "c": "c", "β": "beta", "V": "volume"}[key.group(1)]] = v
            elif section == "modes":
                l2 = par.replace(" ", "").translate(SUP).replace("^", "")
                if re.match(r"^(GM|X)\d\+$", l2): out[f]["modes"][l2] = v
    return out

def disp(f): return re.sub(r"(\d+(?:\.\d+)?)", lambda m: m.group(1).translate(str.maketrans("0123456789.", "₀₁₂₃₄₅₆₇₈₉.")), f)

def material(f, A, m, series_id, status, vis, synth, notes, extra_ev, impurity=None):
    mid = f"mat:{slug(f)}"
    rec = {"id": mid, "schema_version": SV, "status": status, "visibility": vis, "title": f, "formula": f, "formula_display": disp(f),
           "composition": composition(f), "sites": {"A": [A] if A == "Sr" else [A, m], "B": [m] if A == "Sr" else [m, A], "Bp": ["Sb"], "X": ["O"]},
           "oxidation_states": {A: 2, m: 3, "Sb": 5, "O": -2},
           "structural_family": "double-perovskite", "material_status": "primary", "b_site_order": "ordered" if A == "Sr" else "partial",
           "series": [{"id": series_id, "slot_values": {"M": m}}], "synthesis": synth, "notes": notes, **({"draft": True} if vis != "public" else {}),
           "evidence": [{"doc": DOC, "md_line": 496, "section": "2.2", "status": "thesis-only", "note": "synthesis"}, {"doc": DOC, "md_line": 512, "table": "2.1", "status": "thesis-only", "note": "final sintering"}] + extra_ev}
    if impurity: rec["impurities"] = [{"phase": impurity.split("%")[-1].strip(), "fraction_percent": re.sub(r"\s+", " ", impurity.split("%")[0]).strip()}]
    p = ROOT / f"materials/{slug(f)}/index.qmd"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\n" + yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=1000) + "---\n\n::: {.page-article}\n" + f"{{{{< include /_gen/includes/materials/{slug(f)}.md >}}}}\n:::\n")
    dump({"id": f"smp:{slug(f)}.{SRC}", "schema_version": SV, "status": status, "visibility": vis, "material": mid, "method": synth["method"], "schedule": synth.get("schedule", ""), "evidence": rec["evidence"][:2]}, ROOT / f"samples/{slug(f)}.{SRC}.yaml")
    return mid

def modes_rec(sslug, stid, amps, status, vis, evidence, note):
    irreps = []
    for lab, v in amps.items():
        k, d = IRREP_META[lab]; iso = {"GM4+": "C2/m", "X3+": "P4/mnc", "X5+": "Pnnm"}[lab]
        irreps.append({"label": lab, "k_vector": k, "dimension": d, "isotropy_subgroup": iso, "amplitude": v, **({"primary": True} if lab in ("GM4+", "X3+") else {}), **({"physical": PHYS[lab]} if lab in PHYS else {})})
    dump({"id": f"mod:{sslug}", "schema_version": SV, "status": status, "visibility": vis, "structure": stid, "parent_space_group": "Fm-3m", "transformation": "a+b, -a+b, c (virtual reference structure of Table 6.1)",
          "software": "AMPLIMODES", "convention": "amplimodes-cell", "refinement_variant": "all-modes", "irreps": irreps, "notes": note, "evidence": evidence}, ROOT / "structures" / sslug / "modes.yaml")

def main():
    P = parse_8_1()
    SR = [f"Sr2{m}SbO6" for m in M]; CA = [f"Ca2{m}SbO6" for m in M]
    S_SR = parse_structures("8.2", SR); S_CA = parse_structures("10.4", CA)
    synth_base = "solid-state reaction of ACO3, M2O3 and Sb2O5 in air (6 h 870 K; 24 h 1270 K; 24 h 1470 K; final sintering 1570–1870 K, 48–72 h; slow cooling 3 K/min, regrinding between steps)"
    final = {r[0]: (r[1], r[2]) for r in [[plain_caption(c).replace(" ", "") for c in row] for row in rows("2.1")[1:]]}
    for sid, title, tpl, members, ev0 in [("ser:sr2-m-sbo6", "Sr2MSbO6 antimonates (M = Ln, Y)", "Sr2{M}SbO6", SR, {"doc": DOC, "md_line": 1676, "section": "8", "status": "thesis-only"}),
                                          ("ser:ca2-m-sbo6", "Ca2MSbO6 antimonates (M = Ln, Y)", "Ca2{M}SbO6", CA, {"doc": DOC, "md_line": 2384, "section": "Part III (in preparation)", "status": "thesis-only"})]:
        pub = sid == "ser:sr2-m-sbo6"
        dump({"id": sid, "schema_version": SV, "status": "published" if pub else "thesis-only", "visibility": "public" if pub else "review", "title": title, "template": tpl, "slots": {"M": M},
              "structural_family": "double-perovskite", "aristotype": "Fm-3m", "members": [f"mat:{slug(m)}" for m in members],
              "notes": ("Room-temperature P2_1/n for every M; two high-temperature transitions P2_1/n → R-3 (discontinuous) → Fm-3m (continuous), both temperatures decreasing with the M3+ radius (phase diagram Figure 8.9). Published as Polyhedron 123 (2016) 265."
                        if pub else "Room-temperature P2_1/n for every M with partial Ca/M antisite disorder over the A and B sites; no high-temperature study (Table 10.5 lists P2_1/n only). Unpublished at the time of the thesis (chapter marked 'in preparation')."),
              "evidence": [ev0] + ([ev_poly("1"), ev_poly("2")] if pub else [])}, ROOT / f"series/{sid.split(':')[1]}.yaml")
    n = 0; ntr = 0
    for i, m in enumerate(M):
        # ---------------- Sr2MSbO6: published (chapter 8 = Polyhedron 2016)
        f = SR[i]; p = P[f]; st = S_SR[f]; tk, dur = final.get(f, (p["synth_k"], ""))
        synth = {"method": synth_base, "schedule": f"final sintering {tk} K, {dur} h", "atmosphere": "air"}
        notes = (f"Room-temperature P2_1/n (synchrotron XRPD, BM25-A ESRF). Ionic radius r(M3+) = {p['ionic_radius']} Å, Δr = {p['delta_r']} Å, tolerance factor t = {p['t']} (Table 8.1). "
                 f"Phase sequence on heating P2_1/n → R-3 at about {T1[i]} K (discontinuous) and R-3 → Fm-3m at about {T2[i]} K (continuous), laboratory XRPD 300–1475 K (§ 8.2, Figures 8.6–8.8). Mode amplitudes vs T in Figure 8.7 and cell vs T in Figure 8.8, to be digitised.")
        mid = material(f, "Sr", m, "ser:sr2-m-sbo6", "published", "public", synth, notes, [ev("8.1", f, note="tolerance factor, synthesis"), ev_poly("1", f), ev("8.2", f, note="RT structure"), ev_poly("2", f)], p["impurity"] or None)
        sslug = f"{slug(f)}.p21n.300k.{SRC}"; stid = f"str:{sslug}"; d = ROOT / "structures" / sslug
        dat = f"dat:{slug(f)}.{SRC}.sxrpd.rt"
        dump({"id": dat, "schema_version": SV, "status": "published", "visibility": "public", "sample": f"smp:{slug(f)}.{SRC}", "technique": "sxrpd", "instrument": "ins:esrf-bm25a", "temperature_k": 300, "notes": "1 mm rotating capillary (article § 2).", "evidence": [ev("8.2", f), ev_poly("2", f)]}, ROOT / f"datasets/{dat.split(':')[1]}.yaml")
        atoms = []
        for lab, a in st["atoms"].items():
            if lab in ("M", "Sb"): continue
            el = "Sr" if lab == "Sr" else "O"
            fixed = ["x", "z"] if lab == "Sr" else (["z"] if lab == "O2" else [])
            atoms.append({"label": lab, "element": el, "wyckoff": "4e", "x": a.get("x", "0"), "y": a.get("y", "0"), "z": a.get("z", "0"), "occupancy": "1", **({"b_iso": a["b_iso"]} if a.get("b_iso") else {}), **({"fixed": fixed} if fixed else {})})
        for lab, el, w, xx, yy, zz in [("Sb", "Sb", "2a", "0", "0", "0"), (m, m, "2b", "0.5", "0.5", "0")]:
            b = st["atoms"].get("Sb" if el == "Sb" else "M", {})
            atoms.append({"label": lab, "element": el, "wyckoff": w, "x": xx, "y": yy, "z": zz, "occupancy": "1", **({"b_iso": b["b_iso"]} if b.get("b_iso") else {}), "fixed": ["x", "y", "z"]})
        cell = dict(st["cell"]); cell.setdefault("alpha", "90"); cell.setdefault("gamma", "90")
        num, system, setting = SG["P2_1/n"]
        dump({"id": stid, "schema_version": SV, "status": "published", "visibility": "public", "material": mid, "phase_label": "room temperature", "conditions": {"temperature_k": 300},
              "space_group": {"hm": "P2_1/n", "number": num, "crystal_system": system, "setting": setting}, "cell": cell, "atoms": atoms, "cif_origin": "absent",
              "refinement": "refinement.yaml", "modes": "modes.yaml",
              "notes": "Table 8.2 (= article Table 2). Sr x and z, and O2 z, are fixed values in the table (setting with Sr at (0, ~0.53, 1/4)). M and Sb have no reported coordinates; in this setting they sit at 2b (1/2,1/2,0) and 2a (0,0,0), assigned here and marked fixed. Article Table 3 gives the AMPLIMODES reference setting (M 2d, Sb 2c), which differs by the origin shift (0,1/2,0). No R factors in the tables. Original FullProf files expected from data rescue.",
              "evidence": [ev("8.2", f), ev_poly("2", f)]}, d / "structure.yaml")
        dump({"id": f"ref:{sslug}.all-modes", "schema_version": SV, "status": "published", "visibility": "public", "structure": stid, "dataset": dat, "software": "FullProf", "method": "symmetry-mode", "variant": "all-modes", "notes": "R factors not reported in Table 8.2 / article Table 2.", "evidence": [ev("8.2", f), ev_poly("2", f)]}, d / "refinement.yaml")
        modes_rec(sslug, stid, st["modes"], "published", "public", [ev("8.2", f, note="mode amplitudes rows"), ev_poly("2", f), ev_poly("3", note="parent and reference structures")], "Amplitudes of the three irreps (GM4+ and X3+ primary; X5+ secondary, components A10 and A11 summed) from the bottom rows of Table 8.2; convention amplimodes-cell.")
        for j, (sg0, sg1, tk_, order, line, rng) in enumerate([("P2_1/n", "R-3", T1[i], "discontinuous", 1820, 25), ("R-3", "Fm-3m", T2[i], "continuous", 1822, 25)]):
            tslug = f"{slug(f)}.{sgslug(sg0)}-{sgslug(sg1)}.{SRC}"
            dump({"id": f"trn:{tslug}", "schema_version": SV, "status": "published", "visibility": "public", "material": mid, "from_space_group": sg0, "to_space_group": sg1, "temperature_k": tk_, "temperature_range_k": [tk_ - rng, tk_ + rng],
                  "order": order, "techniques": ["xrpd"], **({"from_structure": stid} if j == 0 else {}), "primary_irrep": "GM4+",
                  "notes": ("Discontinuous: no group–subgroup relation between P2_1/n and R-3; the splitting of the monoclinic lines and the primitive reflections disappear at about this temperature (25 K steps of the HT XRPD series)." if j == 0 else
                            "Continuous: the trigonal splitting of the (642) cubic reflection closes; GM4+ amplitude in R-3 follows A(0)(Tc−T)^α with α close to the tricritical value 0.25 (§ 8.2)."),
                  "evidence": [{"doc": DOC, "md_line": line, "section": "8.2", "status": "thesis-only"}, {"doc": DOC, "md_line": 1842, "section": "8.2", "status": "thesis-only", "figure": "8.8"}, ev_poly("fig9", figure="9", note="phase diagram")]}, ROOT / f"transitions/{tslug}.yaml")
            ntr += 1
        n += 1
        # ---------------- Ca2MSbO6: thesis-only, in preparation → review
        f = CA[i]; st = S_CA[f]; tk, dur = final.get(f, ("", ""))
        synth = {"method": synth_base, "schedule": f"final sintering {tk} K, {dur} h", "atmosphere": "air"}
        occ = st["occ"]
        notes = (f"Room-temperature P2_1/n (laboratory XRPD) with partial Ca/M antisite disorder, [Ca1+xM1−x][MxCa1−x]SbO6: reported occupancies Ca1/M1 = {occ.get('Ca1/M1', '?')} and M2/Ca2 = {occ.get('M2/Ca2', '?')} (Table 10.4). "
                 "No high-temperature study; Table 10.5 lists P2_1/n as the only phase. Results of a chapter marked 'in preparation' in the thesis: unpublished, under review.")
        mid = material(f, "Ca", m, "ser:ca2-m-sbo6", "thesis-only", "review", synth, notes, [ev("10.4", f, note="RT structure and occupancies")])
        sslug = f"{slug(f)}.p21n.300k.{SRC}"; stid = f"str:{sslug}"; d = ROOT / "structures" / sslug
        dat = f"dat:{slug(f)}.{SRC}.xrpd.rt"
        dump({"id": dat, "schema_version": SV, "status": "thesis-only", "visibility": "review", "sample": f"smp:{slug(f)}.{SRC}", "technique": "xrpd", "instrument": "ins:lab-xrd", "temperature_k": 300, "evidence": [ev("10.4", f)]}, ROOT / f"datasets/{dat.split(':')[1]}.yaml")
        atoms = []
        a = st["atoms"].get("M1/Ca2", {})
        atoms.append({"label": "Ca1/M1", "element": "Ca", "wyckoff": "4e", "x": a.get("x", "0"), "y": a.get("y", "0"), "z": a.get("z", "0"), "occupancy": f"Ca1/M1 {occ.get('Ca1/M1', '?')} (as reported; A site shared by Ca and {m})"})
        for lab in ("O1", "O2", "O3"):
            a = st["atoms"].get(lab, {})
            atoms.append({"label": lab, "element": "O", "wyckoff": "4e", "x": a.get("x", "0"), "y": a.get("y", "0"), "z": a.get("z", "0"), "occupancy": "1", **({"b_iso": a["b_iso"]} if a.get("b_iso") else {})})
        atoms.append({"label": "Sb", "element": "Sb", "wyckoff": "2c", "x": "0", "y": "0.5", "z": "0", "occupancy": "1", **({"b_iso": st["atoms"]["Sb"]["b_iso"]} if st["atoms"].get("Sb", {}).get("b_iso") else {}), "fixed": ["x", "y", "z"]})
        atoms.append({"label": "M2/Ca2", "element": m, "wyckoff": "2d", "x": "0.5", "y": "0", "z": "0", "occupancy": f"M2/Ca2 {occ.get('M2/Ca2', '?')} (as reported; B site shared by {m} and Ca)", "fixed": ["x", "y", "z"]})
        cell = dict(st["cell"]); cell.setdefault("alpha", "90"); cell.setdefault("gamma", "90")
        dump({"id": stid, "schema_version": SV, "status": "thesis-only", "visibility": "review", "material": mid, "phase_label": "room temperature", "conditions": {"temperature_k": 300},
              "space_group": {"hm": "P2_1/n", "number": num, "crystal_system": system, "setting": setting}, "cell": cell, "atoms": atoms, "cif_origin": "absent",
              "refinement": "refinement.yaml", "modes": "modes.yaml",
              "notes": "Table 10.4. Model with Ca and M partially disordered over the A (4e) and B (2d) sites, [Ca1+xM1−x][MxCa1−x]SbO6 (text at md_line 2410–2412); the two occupancy rows are copied as reported and their mapping onto site fractions must be confirmed from the refinement files. Setting with the A site near (0, 0.05, 1/4): Sb at 2c (0,1/2,0) and M at 2d (1/2,0,0), assigned here and marked fixed. B_iso of Ca/M not reported. No R factors.",
              "evidence": [ev("10.4", f)]}, d / "structure.yaml")
        dump({"id": f"ref:{sslug}.all-modes", "schema_version": SV, "status": "thesis-only", "visibility": "review", "structure": stid, "dataset": dat, "software": "FullProf", "method": "symmetry-mode", "variant": "all-modes", "notes": "R factors not reported in Table 10.4.", "evidence": [ev("10.4", f)]}, d / "refinement.yaml")
        modes_rec(sslug, stid, st["modes"], "thesis-only", "review", [ev("10.4", f, note="mode amplitudes rows")], "Amplitudes of GM4+, X3+ and X5+ from the bottom rows of Table 10.4, same virtual reference structure as the Sr series (Table 6.1); convention amplimodes-cell.")
        n += 1
    dump({"id": "ins:esrf-bm25a", "schema_version": SV, "status": "published", "visibility": "public", "name": "BM25 (SpLine, Spanish CRG) branch A, Debye–Scherrer powder diffractometer", "facility": "European Synchrotron Radiation Facility, Grenoble",
          "evidence": [ev_poly("exp", section="2", note="instrument named in the experimental section")]}, ROOT / "instruments/esrf-bm25a.yaml")
    th = ROOT / "theses/thesis-04/index.qmd"; txt = th.read_text(); fm_end = txt.index("\n---\n", 4); fm = yaml.safe_load(txt[4:fm_end])
    chap = {c["n"]: c for c in fm.get("chapters", [])}
    chap[8] = {"n": 8, "title": "Sr2MSbO6 (M = Ln, Y): mode-crystallography approach of the structural and high-temperature phase-transition studies", "materials": [f"mat:{slug(f)}" for f in SR], "published_as": [POLY]}
    chap[11] = {"n": 11, "title": "M3+ size effect in the Ca2MSbO6 (M = Ln, Y) and their mode-amplitude changes (Part III, in preparation)", "materials": [f"mat:{slug(f)}" for f in CA], "published_as": []}
    fm["chapters"] = [chap[k] for k in sorted(chap)]
    th.write_text("---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000) + txt[fm_end:])
    print(f"ingest_thesis04b: {n} structures, {n} materials, {ntr} transitions, 2 series")

if __name__ == "__main__":
    main()
