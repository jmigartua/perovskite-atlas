"""Thesis 4 (Orayech 2015), phase A: the tellurate solid solutions.

- Sr2Co1-xMgxTeO6, x = 0, 0.1, 0.2, 0.5 (chapter 9): RT structures (Table 9.3, columns (a) = all modes refined),
  mode decompositions (Table 9.2, parent Fm-3m, Table 9.1 for the transformation), geometry (Table 9.4).
  x = 0 and 0.1 are P2_1/n from NPD; x = 0.2 and 0.5 are I2/m from XRPD.
- Sr2Ni1-xMgxTeO6, x = 0, 0.1, 0.2, 0.3, 0.5 (chapter 10): materials and series only; the RT structure table
  (10.1) did not survive the OCR, so Table 10.2 (geometry) cannot be attached yet.

Site labels for Te and Co/Mg (no coordinates in Table 9.3, i.e. special positions) are assigned from the space-group
setting and flagged in the atom's `fixed`/notes; everything else is as reported. Published as chapters 9 and 10 →
Dalton Trans. 2015 (c5dt02026c) and 2016 (c6dt02473d).
"""
from __future__ import annotations
import csv, re, pathlib, yaml
from common import ROOT
from ingest_thesis03 import plain_caption, clean_num, is_num, dump, slug, sgslug, composition, IRREP_META, PHYS, SG

DOC = "doc:thesis-04"; SRC = "orayech2015"; SV = "0.1"
T4 = ROOT / "tables/thesis-04"

def md_line_of(table): return next(e["md_line"] for e in yaml.safe_load((T4 / table / "table.yaml").read_text())["evidence"] if e.get("md_line"))
def rows(table):
    with (T4 / table / "table.csv").open() as f: return [[c.strip() for c in r] for r in csv.reader(f)]
def ev(table, col=None, status="thesis-only", **extra):
    e = {"doc": DOC, "md_line": md_line_of(table), "table": table, "status": status}
    if col: e["cell"] = {"col": col}
    e.update(extra); return e

CO = [("Sr2CoTeO6", 0.0, "P2_1/n", "npd", 2), ("Sr2Co0.9Mg0.1TeO6", 0.1, "P2_1/n", "npd", 4), ("Sr2Co0.8Mg0.2TeO6", 0.2, "I2/m", "xrpd", 6), ("Sr2Co0.5Mg0.5TeO6", 0.5, "I2/m", "xrpd", 8)]
NI = [("Sr2NiTeO6", 0.0), ("Sr2Ni0.9Mg0.1TeO6", 0.1), ("Sr2Ni0.8Mg0.2TeO6", 0.2), ("Sr2Ni0.7Mg0.3TeO6", 0.3), ("Sr2Ni0.5Mg0.5TeO6", 0.5)]
SG["I2/m"] = (12, "monoclinic", "I 1 2/m 1 (non-standard setting of C2/m, No. 12)")
PUB = {9: "doc:10.1039-c5dt02026c", 10: "doc:10.1039-c6dt02473d"}

def parse_9_3():
    R = rows("9.3"); out = {f: {"atoms": {}, "cell": {}, "R": {}, "t": None} for f, *_ in CO}
    atom = None
    for r in R[3:]:
        lab = plain_caption(r[0]).strip(); par = plain_caption(r[1]).strip() if len(r) > 1 else ""
        if lab and not re.match(r"^(a|b|c|β|V|R|χ|t)\b", lab): atom = lab.replace(" ", "")
        for f, x, sg, tech, ci in CO:
            raw = plain_caption(r[ci]).strip() if ci < len(r) else ""
            v = "0.5" if raw in ("1/2", "1 / 2") else clean_num(raw)
            if lab == "t" and is_num(v): out[f]["t"] = v; continue
            key = {"x": "x", "y": "y", "z": "z"}.get(par) or ("b_iso" if par.startswith("B") else None)
            if atom and key and is_num(v):
                out[f]["atoms"].setdefault(atom, {})[key] = v; continue
            m0 = re.match(r"^(a|b|c|β|V)\b", lab)
            if m0 and is_num(v): out[f]["cell"][{"a": "a", "b": "b", "c": "c", "β": "beta", "V": "volume"}[m0.group(1)]] = v; continue
            l2 = lab.replace(" ", "").replace("(%)", "")
            for k, kk in {"Rp": "r_p", "Rwp": "r_wp", "Rexp": "r_exp", "RBragg": "r_bragg", "χ²": "chi2"}.items():
                if l2.startswith(k) and is_num(v): out[f]["R"][kk] = float(v)
    return out

def parse_9_2():
    R = rows("9.2"); out = {f: [] for f, *_ in CO}
    for r in R[4:]:
        lab = plain_caption(r[0]).replace(" ", ""); lab = re.sub(r"[₀-₉]", lambda m: str("₀₁₂₃₄₅₆₇₈₉".index(m.group(0))), lab).replace("⁺", "+")
        if not re.match(r"^(GM|X)\d\+$", lab): continue
        for f, x, sg, tech, ci in CO:
            v = clean_num(r[ci - 1]) if ci - 1 < len(r) else ""   # (a) columns are at ci-1 in this table
            if not is_num(v): continue
            k, d = IRREP_META.get(lab, ("", None)); primary = lab in (("GM4+", "X3+") if sg == "P2_1/n" else ("GM4+",))
            iso = {"GM1+": "Fm-3m", "GM3+": "I4/mmm", "GM4+": "C2/m", "GM5+": "C2/m", "X2+": "P4_2/mnm", "X3+": "P4/mnc", "X5+": "Pnnm"}[lab]
            out[f].append({"label": lab, "k_vector": k, "dimension": d, "isotropy_subgroup": iso, "amplitude": v, **({"primary": True} if primary else {}), **({"physical": PHYS[lab]} if lab in PHYS else {})})
    return out

def parse_9_4():
    R = rows("9.4"); out = {f: {"bonds": {}, "angles": {}, "octahedra": {}} for f, *_ in CO}; section = None
    for r in R[3:]:
        lab = plain_caption(r[0]).replace(" ", "")
        vals = {f: (r[ci - 1] if ci - 1 < len(r) else "") for f, x, sg, tech, ci in CO}
        if not any(is_num(clean_num(v)) for v in vals.values()): section = lab.replace("octahedra", ""); continue
        for f, raw in vals.items():
            v = clean_num(raw)
            if not is_num(v): continue
            mult = re.search(r"×\s*(\d)", plain_caption(raw)); key = lab + (f"(×{mult.group(1)})" if mult else "")
            g = out[f]
            if lab.startswith("Average"): g["octahedra"].setdefault(section, {})["average_bond"] = v
            elif lab.startswith("Predicted"): g["octahedra"].setdefault(section, {})["predicted_bond"] = v
            elif "∠" in lab or lab.count("-") >= 2: g["angles"][key.replace("∠", "")] = v
            else: g["bonds"][key] = v
    return out

def material(f, x, ch, series_id, order, synth, notes, extra_ev):
    mid = f"mat:{slug(f)}"
    B = "Co" if "Co" in f else "Ni"
    rec = {"id": mid, "schema_version": SV, "status": "published", "visibility": "public", "title": f, "formula": f,
           "formula_display": re.sub(r"(\d+(?:\.\d+)?)", lambda m: m.group(1).translate(str.maketrans("0123456789.", "₀₁₂₃₄₅₆₇₈₉.")), f),
           "composition": composition(f), "sites": {"A": ["Sr"], "B": [B, "Mg"] if x > 0 else [B], "Bp": ["Te"], "X": ["O"]},
           "oxidation_states": {"Sr": 2, B: 2, "Mg": 2, "Te": 6, "O": -2} if x > 0 else {"Sr": 2, B: 2, "Te": 6, "O": -2},
           "structural_family": "double-perovskite", "material_status": "primary", "b_site_order": order,
           "series": [{"id": series_id, "slot_values": {"x": x}}], "synthesis": synth, "notes": notes,
           "evidence": [{"doc": DOC, "md_line": 542, "section": "2.3.1", "status": "thesis-only", "note": "synthesis"}] + extra_ev}
    p = ROOT / f"materials/{slug(f)}/index.qmd"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("---\n" + yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=1000) + "---\n\n::: {.page-article}\n" + f"{{{{< include /_gen/includes/materials/{slug(f)}.md >}}}}\n:::\n")
    dump({"id": f"smp:{slug(f)}.{SRC}", "schema_version": SV, "status": "published", "visibility": "public", "material": mid, "method": synth["method"], "schedule": synth.get("schedule", ""), "prepared_by": "Ortega-San Martín et al. (freeze-drying); see thesis § 2.3.1", "evidence": [rec["evidence"][0]]}, ROOT / f"samples/{slug(f)}.{SRC}.yaml")
    return mid

def main():
    synth = {"method": "freeze-drying (nitrate solution frozen in liquid nitrogen, freeze-dried, calcined 1170 K 6 h, then higher-temperature treatments)", "atmosphere": "air"}
    S = parse_9_3(); MD = parse_9_2(); GE = parse_9_4()
    for sid, title, tpl, xs, members in [("ser:sr2-co1-x-mgx-teo6", "Sr2Co1−xMgxTeO6 tellurate solid solution", "Sr2Co{1-x}Mg{x}TeO6", [x for _, x, *_ in CO], [f for f, *_ in CO]),
                                          ("ser:sr2-ni1-x-mgx-teo6", "Sr2Ni1−xMgxTeO6 tellurate solid solution", "Sr2Ni{1-x}Mg{x}TeO6", [x for _, x in NI], [f for f, _ in NI])]:
        dump({"id": sid, "schema_version": SV, "status": "published", "visibility": "public", "title": title, "template": tpl, "slots": {"x": [str(x) for x in xs]},
              "structural_family": "double-perovskite", "aristotype": "Fm-3m", "members": [f"mat:{slug(m)}" for m in members],
              "evidence": [{"doc": DOC, "md_line": 1903 if "co1" in sid else 2122, "section": "9" if "co1" in sid else "10", "status": "thesis-only"}]}, ROOT / f"series/{sid.split(':')[1]}.yaml")
    n = 0
    for f, x, sg, tech, ci in CO:
        st = S[f]; num, system, setting = SG[sg]
        notes = f"Room-temperature symmetry {sg} ({tech.upper()}). Tolerance factor t = {st['t']} (Table 9.3). Phase sequence on cooling Fm-3m → I4/m → I2/m → P2_1/n (chapter 9); transition temperatures in Figure 9.7, to be digitised."
        mid = material(f, x, 9, "ser:sr2-co1-x-mgx-teo6", "ordered", synth, notes, [ev("9.3", f, note="RT structure")])
        sslug = f"{slug(f)}.{sgslug(sg)}.300k.{SRC}"; stid = f"str:{sslug}"; d = ROOT / "structures" / sslug
        dat = f"dat:{slug(f)}.{SRC}.{tech}.rt"
        dump({"id": dat, "schema_version": SV, "status": "published", "visibility": "public", "sample": f"smp:{slug(f)}.{SRC}", "technique": tech, "instrument": "ins:ill-d2b" if tech == "npd" else "ins:lab-xrd", "temperature_k": 300, "evidence": [ev("9.3", f)]}, ROOT / f"datasets/{dat.split(':')[1]}.yaml")
        B = "Co/Mg" if x > 0 else "Co"
        if sg == "P2_1/n":
            wy = {"Sr": "4e", "O1": "4e", "O2": "4e", "O3": "4e"}; fixed = [("Te", "Te", "2a", "0", "0", "0"), (B, "Co", "2b", "0", "0", "0.5")]
        else:
            wy = {"Sr": "4i", "O1": "8j", "O2": "4i"}; fixed = [("Te", "Te", "2a", "0", "0", "0"), (B, "Co", "2d", "0", "0", "0.5")]
        atoms = []
        for lab, a in st["atoms"].items():
            if lab in ("Te", "Co/Mg", "Co"): continue
            el = "Sr" if lab == "Sr" else "O"
            atoms.append({"label": lab, "element": el, "wyckoff": wy.get(lab, "?"), "x": a.get("x", "0"), "y": a.get("y", "0"), "z": a.get("z", "0"), "occupancy": "1", **({"b_iso": a["b_iso"]} if a.get("b_iso") else {})})
        for lab, el, w, xx, yy, zz in fixed:
            b = st["atoms"].get(lab, {}) or st["atoms"].get("Co/Mg", {}) or st["atoms"].get("Te", {})
            atoms.append({"label": lab, "element": el, "wyckoff": w, "x": xx, "y": yy, "z": zz, "occupancy": f"{1-x:g}/{x:g} (Co/Mg)" if (x > 0 and el == "Co") else "1", **({"b_iso": b["b_iso"]} if b.get("b_iso") else {}), "fixed": ["x", "y", "z"]})
        cell = dict(st["cell"]); cell.setdefault("alpha", "90"); cell.setdefault("gamma", "90")
        dump({"id": stid, "schema_version": SV, "status": "published", "visibility": "public", "material": mid, "phase_label": "room temperature", "conditions": {"temperature_k": 300},
              "space_group": {"hm": sg, "number": num, "crystal_system": system, "setting": setting}, "cell": cell, "atoms": atoms, "cif_origin": "absent",
              "refinement": "refinement.yaml", "modes": "modes.yaml", "geometry": "geometry.yaml",
              "notes": "Column (a) of Table 9.3 (all mode amplitudes refined). Te and Co/Mg have no refined coordinates (special positions); their Wyckoff labels are assigned from the space-group setting and marked fixed. Original FullProf files expected from data rescue.",
              "evidence": [ev("9.3", f)]}, d / "structure.yaml")
        dump({"id": f"ref:{sslug}.all-modes", "schema_version": SV, "status": "published", "visibility": "public", "structure": stid, "dataset": dat, "software": "FullProf", "method": "symmetry-mode", "variant": "all-modes", **st["R"], "evidence": [ev("9.3", f)]}, d / "refinement.yaml")
        if MD.get(f):
            dump({"id": f"mod:{sslug}", "schema_version": SV, "status": "published", "visibility": "public", "structure": stid, "parent_space_group": "Fm-3m", "transformation": "a+b, -a+b, c (Table 9.1; origin shift as given there)",
                  "software": "AMPLIMODES", "convention": "amplimodes-cell", "refinement_variant": "all-modes", "irreps": MD[f], "evidence": [ev("9.2", f), ev("9.1", note="parent structure and transformation")]}, d / "modes.yaml")
        g = GE.get(f, {})
        if g and (g["bonds"] or g["angles"]):
            dump({"id": f"fnd:{sslug}.geometry", "schema_version": SV, "status": "published", "visibility": "public", "structure": stid, **{k: v for k, v in g.items() if v}, "evidence": [ev("9.4", f)]}, d / "geometry.yaml")
        n += 1
    for f, x in NI:
        material(f, x, 10, "ser:sr2-ni1-x-mgx-teo6", "ordered", synth, "Room-temperature symmetry I4/m for all x (chapter 10, Table 10.2 gives bond lengths and tilt angles; the structure table did not survive the OCR and is entered later). Phase sequence on cooling Fm-3m → I4/m → I2/m → P2_1/n at low temperature.", [{"doc": DOC, "md_line": md_line_of("10.2"), "table": "10.2", "status": "thesis-only", "note": "geometry"}])
    for iid, name, fac in [("ins:lab-xrd", "Laboratory X-ray powder diffractometer (Cu Kα)", "UPV/EHU")]:
        dump({"id": iid, "schema_version": SV, "status": "published", "visibility": "public", "name": name, "facility": fac, "evidence": [ev("9.3", note="instrument named in the table header")]}, ROOT / f"instruments/{iid.split(':')[1]}.yaml")
    th = ROOT / "theses/thesis-04/index.qmd"; txt = th.read_text(); fm_end = txt.index("\n---\n", 4); fm = yaml.safe_load(txt[4:fm_end])
    chap = {c["n"]: c for c in fm.get("chapters", [])}
    chap[9] = {"n": 9, "title": "Sr2Co1−xMgxTeO6 (x = 0.1, 0.2, 0.5): structural phase transitions, magnetic and spectroscopic properties", "materials": [f"mat:{slug(f)}" for f, *_ in CO], "published_as": [PUB[9]]}
    chap[10] = {"n": 10, "title": "Sr2Ni1−xMgxTeO6 (x = 0.1, 0.2, 0.3, 0.5): structural phase transitions, magnetic and spectroscopic properties", "materials": [f"mat:{slug(f)}" for f, _ in NI], "published_as": [PUB[10]]}
    fm["chapters"] = [chap[k] for k in sorted(chap)]
    th.write_text("---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000) + txt[fm_end:])
    print(f"ingest_thesis04a: {n} structures, {len(CO) + len(NI)} materials, 2 series")

if __name__ == "__main__":
    main()
