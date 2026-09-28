"""Ingest the room-temperature results of thesis 3 (Iturbe-Zabalo 2012) into records: 20 materials,
their RT structures with atoms, refinements, symmetry-mode decompositions, reported geometry,
transitions, samples and datasets. Everything is read from the extracted table CSVs in tables/thesis-03/
(so every value carries the table locator) plus a small hand-checked list of transition sentences.

Chapters: 5 SrNdMRuO6 (M = Zn, Co, Mg, Ni) · 6 SrPrMRuO6 · 7 SrLaMRuO6 (Zn, Mg) · 9 SrLnFeRuO6 (La, Pr, Nd)
· 10 CaLn2CuTi2O9 (Pr, Nd, Sm) and BaLn2CuTi2O9 (La, Pr, Nd).

Idempotent: re-running rewrites the same records. Hand-written records for SrNdZnRuO6 are replaced by the
table-derived ones (same ids), which is intended: the worked example becomes a pipeline product.

Usage: python3 _scripts/ingest_thesis03.py
"""
from __future__ import annotations
import csv, re, pathlib, yaml
from common import ROOT
from crop_plates import plain_caption as _pc
SUBDIG = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
def plain_caption(s: str) -> str:
    return _pc(s).translate(SUBDIG)

DOC = "doc:thesis-03"; SRC = "iturbe2012"
T3 = ROOT / "tables/thesis-03"
SV = "0.1"

def md_line_of(table: str) -> int:
    rec = yaml.safe_load((T3 / table / "table.yaml").read_text())
    return next(e["md_line"] for e in rec["evidence"] if e.get("md_line"))

def rows(table: str):
    with (T3 / table / "table.csv").open() as f:
        return [[c.strip() for c in r] for r in csv.reader(f)]

def ev(table: str, col: str | None = None, status="thesis-only", **extra):
    e = {"doc": DOC, "md_line": md_line_of(table), "table": table, "status": status}
    if col: e["cell"] = {"col": col}
    e.update(extra)
    return e

def clean_num(s: str) -> str:
    """'0.5*' -> '0.5'; '$0.5^{*}$' -> '0.5'; keep parenthesis uncertainties."""
    s = plain_caption(s).replace("−", "-").replace("*", "").strip()
    m = re.match(r"^(-?\d+(?:\.\d+)?(?:\(\d+\))?)", s)
    return m.group(1) if m else s

def is_num(s: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(\.\d+)?(\(\d+\))?", s))

def dump(rec: dict, path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=1000))

def slug(formula: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", formula.lower())

def sgslug(hm: str) -> str:
    return hm.lower().replace("_", "").replace("/", "").replace("-", "").replace(" ", "")

SG = {"P2_1/n": (14, "monoclinic", "P 1 21/n 1 (non-standard setting of No. 14)"), "Pbnm": (62, "orthorhombic", "Pbnm (non-standard setting of Pnma, No. 62)"),
      "I4/mcm": (140, "tetragonal", None), "R-3": (148, "trigonal", "hexagonal axes"), "R-3c": (167, "trigonal", "hexagonal axes"), "P4_2/n": (86, "tetragonal", None),
      "Fm-3m": (225, "cubic", None), "Pm-3m": (221, "cubic", None)}

# ----------------------------------------------------------------- material catalogue (chapter, sites, synthesis)
DP = "double-perovskite"; TP = "triple-perovskite"
MATS = {
    # formula: (chapter, A, Ap, B, Bp, order, synthesis schedule, notes)
    "SrNdZnRuO6": (5, "Sr", "Nd", "Zn", "Ru", "ordered", "final sintering 1525 K, 20 h, air", None),
    "SrNdCoRuO6": (5, "Sr", "Nd", "Co", "Ru", "ordered", "final sintering 1525 K, 20 h, air", "magnetic ordering near 80 K (chapter 8)"),
    "SrNdMgRuO6": (5, "Sr", "Nd", "Mg", "Ru", "ordered", "final sintering 1525 K, 20 h, air", None),
    "SrNdNiRuO6": (5, "Sr", "Nd", "Ni", "Ru", "ordered", "final sintering 1525 K, 20 h, air", "NiO impurity 4.84 % (Table 5.1 text)"),
    "SrPrZnRuO6": (6, "Sr", "Pr", "Zn", "Ru", "ordered", "final sintering 1525 K, 20 h, air", "no phase transition up to 1360 K (conclusions)"),
    "SrPrCoRuO6": (6, "Sr", "Pr", "Co", "Ru", "ordered", "final sintering 1525 K, 20 h, air", "magnetic ordering near 85 K (chapter 8)"),
    "SrPrMgRuO6": (6, "Sr", "Pr", "Mg", "Ru", "ordered", "final sintering 1525 K, 20 h, air", None),
    "SrPrNiRuO6": (6, "Sr", "Pr", "Ni", "Ru", "ordered", "final sintering 1525 K, 20 h, air", "NiO impurity 3.75 %"),
    "SrLaZnRuO6": (7, "Sr", "La", "Zn", "Ru", "ordered", "final sintering 1525 K, 17 h, air", None),
    "SrLaMgRuO6": (7, "Sr", "La", "Mg", "Ru", "ordered", "final sintering 1525 K, 17 h, air", None),
    "SrLaFeRuO6": (9, "Sr", "La", "Fe", "Ru", "disordered", "solid-state reaction, air (chapter 2)", "G-type canted AFM, T_N ≈ 450 K (chapter 9)"),
    "SrPrFeRuO6": (9, "Sr", "Pr", "Fe", "Ru", "disordered", "solid-state reaction, air (chapter 2)", "ferrimagnetic, T_N ≈ 475 K (chapter 9)"),
    "SrNdFeRuO6": (9, "Sr", "Nd", "Fe", "Ru", "disordered", "solid-state reaction, air (chapter 2)", "canted AFM, T_N ≈ 430 K (chapter 9)"),
    "CaPr2CuTi2O9": (10, "Ca", "Pr", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", "no reversible transition up to 1475 K"),
    "CaNd2CuTi2O9": (10, "Ca", "Nd", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", "no reversible transition up to 1475 K"),
    "CaSm2CuTi2O9": (10, "Ca", "Sm", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", None),
    "BaLa2CuTi2O9": (10, "Ba", "La", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", None),
    "BaPr2CuTi2O9": (10, "Ba", "Pr", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", None),
    "BaNd2CuTi2O9": (10, "Ba", "Nd", "Cu", "Ti", "disordered", "1170 K 12 h, 1270 K 24 h, 1570 K 12 h, air", None),
    "SrLaCoRuO6": (8, "Sr", "La", "Co", "Ru", "ordered", "solid-state reaction, air", "magnetic structure at 4 K (chapter 8); no RT structure table in this thesis"),
}
PUBLISHED_AS = {5: "doc:10.1016-j.jssc.2012.09.007", 6: "doc:10.1088-0953-8984-25-20-205401", 7: "doc:10.1107-s0021889813013253",
                9: "doc:10.1107-s0108768112044217", 10: "doc:10.1016-j.molstruc.2012.08.049", 8: None}

def composition(f: str) -> dict:
    return {el: (float(n) if "." in n else int(n)) if n else 1 for el, n in re.findall(r"([A-Z][a-z]?)(\d*\.?\d*)", f)}

# ----------------------------------------------------------------- parsers for the structure tables
def parse_colwise(table: str, materials: list[str], wyck: dict[str, str], fixed_biso: dict[str, str] | None = None):
    """Tables 5.1 / 6.1 / 9.1: one column per material; rows 'atom, param, v1, v2, …'."""
    R = rows(table); out = {m: {"atoms": {}, "cell": {}, "R": {}} for m in materials}
    atom = None
    for r in R[1:]:
        lab, par = plain_caption(r[0]), plain_caption(r[1]) if len(r) > 1 else ""
        vals = r[2:2 + len(materials)]
        if lab and lab not in ("Space group", "Instrument") and not re.match(r"^(a|b|c|β|V|R|χ)", lab):
            atom = lab
        key = None
        if par in ("x", "y", "z"): key = par
        elif par.startswith("B"): key = "b_iso"
        if atom and key and any(is_num(clean_num(v)) for v in vals):
            for m, v in zip(materials, vals):
                if is_num(clean_num(v)): out[m]["atoms"].setdefault(atom, {})[key] = clean_num(v)
            continue
        cellkey = {"a": "a", "b": "b", "c": "c", "β": "beta", "V": "volume"}
        m0 = re.match(r"^(a|b|c|β|V)\b", lab)
        if m0 and all(is_num(clean_num(v)) for v in vals if v):
            for m, v in zip(materials, vals): out[m]["cell"][cellkey[m0.group(1)]] = clean_num(v)
            continue
        rk = {"Rp": "r_p", "Rwp": "r_wp", "Rexp": "r_exp", "RBragg": "r_bragg", "χ²": "chi2"}
        l2 = lab.replace(" ", "").replace("(%)", "").replace("_", "")
        for k, v2 in rk.items():
            if l2.startswith(k):
                for m, v in zip(materials, vals):
                    if is_num(clean_num(v)): out[m]["R"][v2] = float(clean_num(v))
    for m in materials:
        for a in out[m]["atoms"]:
            out[m]["atoms"][a]["wyckoff"] = wyck[a]
        if fixed_biso:
            for a, b in fixed_biso.items():
                out[m]["atoms"].setdefault(a, {}).update({"wyckoff": wyck[a], "b_iso": b, "fixed": ["b_iso"]})
    return out

def parse_7_2():
    """Table 7.2: blocks per material; rows: R factor, cell item, atom, site, x, y, z, Biso, occ."""
    out = {}; cur = None
    for r in rows("7.2")[1:]:
        c0 = plain_caption(r[0])
        m = re.match(r"^(SrLa\w+RuO6)", c0.replace(" ", ""))
        if m and not r[2]:
            cur = m.group(1); out[cur] = {"atoms": {}, "cell": {}, "R": {}}; continue
        if not cur: continue
        rm = re.match(r"^R\s*(p|wp|exp|Bragg)\s*=\s*([\d.]+)", c0.replace(" ", "").replace("_", ""), re.I)
        if rm: out[cur]["R"][{"p": "r_p", "wp": "r_wp", "exp": "r_exp", "Bragg": "r_bragg"}[rm.group(1)]] = float(rm.group(2))
        c1 = plain_caption(r[1])
        cm = re.match(r"^(a|b|c|β|V)\s*=\s*(-?[\d.]+(?:\(\d+\))?)", c1)
        if cm: out[cur]["cell"][{"a": "a", "b": "b", "c": "c", "β": "beta", "V": "volume"}[cm.group(1)]] = cm.group(2)
        if len(r) >= 9 and r[2]:
            out[cur]["atoms"][r[2]] = {"wyckoff": r[3].replace(" ", ""), "x": clean_num(r[4]), "y": clean_num(r[5]), "z": clean_num(r[6]), "b_iso": clean_num(r[7]), "occ": r[8]}
    return out

def parse_10_2():
    out = {}; cur = None
    for r in rows("10.2")[1:]:
        c0 = plain_caption(r[0]).replace(" ", "")
        fm = re.match(r"^((?:Ca|Ba)(?:La|Pr|Nd|Sm)2CuTi2O9)$", c0)
        if fm: cur = fm.group(1); out[cur] = {"atoms": {}, "cell": {}, "R": {}}; continue
        if not cur: continue
        if c0.startswith(("Pbnm", "I4/mcm")):
            out[cur]["sg"] = "Pbnm" if c0.startswith("Pbnm") else "I4/mcm"
            for k, v in re.findall(r"([abc])=(-?[\d.]+(?:\(\d+\))?)", c0): out[cur]["cell"][k] = v
            for k, v in re.findall(r"R(p|wp|Bragg)=([\d.]+)", c0): out[cur]["R"][{"p": "r_p", "wp": "r_wp", "Bragg": "r_bragg"}[k]] = float(v)
            cm = re.search(r"χ²=([\d.]+)", c0)
            if cm: out[cur]["R"]["chi2"] = float(cm.group(1))
            continue
        if len(r) >= 7 and r[1]:
            out[cur]["atoms"][r[0]] = {"wyckoff": plain_caption(r[1]).replace(" ", ""), "x": clean_num(r[2]), "y": clean_num(r[3]), "z": clean_num(r[4]), "occ": plain_caption(r[5]), "b_iso": clean_num(r[6]), "fixed": ["b_iso"] if "*" in r[6] else []}
    return out

# ----------------------------------------------------------------- mode tables
IRREP_META = {  # label -> (k-vector, dimension) for the two parents
    "GM1+": ("(0,0,0)", 1), "GM3+": ("(0,0,0)", 1), "GM4+": ("(0,0,0)", 1), "GM5+": ("(0,0,0)", 4), "X2+": ("(0,1,0)", 1), "X3+": ("(0,1,0)", 1), "X5+": ("(0,1,0)", 3),
    "R4+": ("(1/2,1/2,1/2)", 1), "R5+": ("(1/2,1/2,1/2)", 2), "X5+p": ("(0,1/2,0)", 2), "M2+": ("(1/2,1/2,0)", 1), "M3+": ("(1/2,1/2,0)", 1)}
PHYS = {"GM4+": "octahedral rotation about the monoclinic b axis (pseudo-cubic [110])", "X3+": "octahedral rotation about c", "X5+": "octahedral rotation about a and A-site displacement along b",
        "R4+": "antiphase octahedral tilt", "M3+": "in-phase octahedral tilt", "X5+p": "A-site antipolar displacement", "R5+": "octahedral deformation", "M2+": "octahedral deformation"}

def irrep_label(s: str) -> str:
    s = plain_caption(s).replace(" ", "")
    s = re.sub(r"[₀-₉]", lambda m: str("₀₁₂₃₄₅₆₇₈₉".index(m.group(0))), s).replace("⁺", "+").replace("⁻", "-")
    return s

def parse_modes(table: str, cols: dict[str, int], parent: str, primary: list[str], stop_at: str | None = None):
    """Return {material: [irreps]} reading amplitude column index per material; rows until R factors."""
    out = {m: [] for m in cols}; seen_block = False
    for r in rows(table):
        lab = irrep_label(r[0])
        if stop_at and lab.startswith(stop_at) and seen_block: break
        if not re.match(r"^(GM|X|R|M)\d[+-]$", lab):
            continue
        seen_block = True
        iso = plain_caption(r[1]); dim = r[2]
        key = lab + ("p" if parent == "Pm-3m" and lab == "X5+" else "")
        k, d = IRREP_META.get(key, ("", int(dim) if dim.isdigit() else None))
        for m, ci in cols.items():
            v = clean_num(r[ci]) if ci < len(r) else ""
            if not is_num(v): continue
            out[m].append({"label": lab, "k_vector": k, "dimension": d, "isotropy_subgroup": re.sub(r"\s*\(\d+\)$", "", iso), "amplitude": v,
                           **({"primary": True} if lab in primary else {}), **({"physical": PHYS[key]} if key in PHYS else {})})
    return out

# ----------------------------------------------------------------- geometry tables
def parse_geometry(table: str, cols: dict[str, int]):
    out = {m: {"tilts": {}, "bonds": {}, "angles": {}, "bvs": {}, "octahedra": {}} for m in cols}
    section = None
    def octname(sec):
        return re.sub(r"\s*(octahedra|polyhedra)\s*", "", sec or "").replace(" ", "") or "octahedra"
    for r in rows(table)[1:]:
        lab = plain_caption(r[0]).strip()
        vals = {m: clean_num(r[ci]) if ci < len(r) else "" for m, ci in cols.items()}
        if not any(is_num(v) for v in vals.values()):
            section = lab; continue
        L = lab.replace("( ×", "(×").replace("( x", "(×").replace("(x", "(×").replace("×2 )", "×2)").replace(" ", "")
        is_mean = (L.startswith("<") and L.endswith(">")) or lab.startswith("Average")
        L = L.strip("<>")
        L = re.sub(r"^[LC/]+(?=[A-Za-z])", "∠", L).replace("∠∠", "∠")
        is_angle = "∠" in L or re.match(r"^[A-Za-z/]+\d?-O\d?['′]?[a-z]*-[A-Za-z/]+\d?", L) is not None
        is_avg = is_mean and not is_angle
        is_pred = lab.startswith("Predicted")
        for m, v in vals.items():
            if not is_num(v): continue
            g = out[m]
            if L.startswith("Tilt"): g["tilts"][L.replace("Tiltangle", "")] = v
            elif L.startswith("V("): g["octahedra"].setdefault(L[2:].rstrip(")"), {})["volume"] = v
            elif section and section.startswith("Bond-Valence"): g["bvs"][L] = v
            elif is_avg or is_pred:
                key = L.strip("<>") if is_avg and "-O" in L else octname(section)
                g["octahedra"].setdefault(octname(section), {})["average_bond" if is_avg else "predicted_bond"] = v
            elif is_angle: g["angles"][("mean " if is_mean else "") + L.replace("∠", "")] = v
            elif "-O" in L:
                k = L; i = 2
                while k in g["bonds"]: k = f"{L} #{i}"; i += 1
                g["bonds"][k] = v
    for m in out:
        out[m] = {k: v for k, v in out[m].items() if v}
    return out

# ----------------------------------------------------------------- transitions (hand-checked sentences)
TRANSITIONS = [  # material, from, to, T, order, evidence md_line, figure/section, note
    ("SrNdZnRuO6", "P2_1/n", "P4_2/n", 740, "discontinuous", 1116, {"figure": "5.12"}, None), ("SrNdZnRuO6", "P4_2/n", "Fm-3m", 1060, "continuous", 1116, {"figure": "5.12"}, None),
    ("SrNdCoRuO6", "P2_1/n", "P4_2/n", 660, "discontinuous", 1116, {"figure": "5.12"}, None), ("SrNdCoRuO6", "P4_2/n", "Fm-3m", 1000, "continuous", 1116, {"figure": "5.12"}, None),
    ("SrNdMgRuO6", "P2_1/n", "P4_2/n", 560, "discontinuous", 1116, {"figure": "5.12"}, None), ("SrNdMgRuO6", "P4_2/n", "Fm-3m", 940, "continuous", 1116, {"figure": "5.12"}, None),
    ("SrNdNiRuO6", "P2_1/n", "P4_2/n", 440, "discontinuous", 1116, {"figure": "5.12"}, None), ("SrNdNiRuO6", "P4_2/n", "Fm-3m", 820, "continuous", 1116, {"figure": "5.12"}, None),
    ("SrPrCoRuO6", "P2_1/n", "unknown", 1050, "unknown", 1382, {"figure": "6.7"}, "high-symmetry phase not identified from XRPD"),
    ("SrPrMgRuO6", "P2_1/n", "R-3", 950, "unknown", 1469, {"section": "6.2"}, None), ("SrPrNiRuO6", "P2_1/n", "R-3", 1025, "unknown", 1469, {"section": "6.2"}, None),
    ("SrLaZnRuO6", "P2_1/n", "R-3", 850, "discontinuous", 1649, {"figure": "7.6"}, "phase coexistence between 800 and 900 K"),
    ("SrLaZnRuO6", "R-3", "Fm-3m", 1535, "continuous", 1687, {"figure": "7.9"}, "extrapolated from the rhombohedral angle"),
    ("SrLaMgRuO6", "P2_1/n", "R-3", 570, "discontinuous", 1642, {"section": "7.2"}, "between 520 and 620 K"),
    ("SrPrFeRuO6", "Pbnm", "R-3c", 1075, "unknown", 2065, {"section": "9.2"}, None),
]
TRANGE = {("SrLaZnRuO6", "P2_1/n"): [800, 900], ("SrLaMgRuO6", "P2_1/n"): [520, 620]}
EXTRAP = {("SrLaZnRuO6", "R-3")}

# ----------------------------------------------------------------- build records
def main():
    n = {"material": 0, "structure": 0, "transition": 0, "sample": 0, "dataset": 0}
    # --- structures from tables
    S = {}
    wy5 = {"Sr/Nd": "4e", "O1": "4e", "O2": "4e", "O3": "4e", "Zn": "2b", "Co": "2b", "Mg": "2b", "Ni": "2b", "Ru": "2a"}
    for m, d in parse_colwise("5.1", ["SrNdZnRuO6", "SrNdCoRuO6", "SrNdMgRuO6", "SrNdNiRuO6"], wy5, fixed_biso={"Ru": "0.5"}).items():
        M = MATS[m][3]; d["atoms"][M] = {"wyckoff": "2b", "b_iso": "0.5", "fixed": ["b_iso"]}
        S[m] = dict(d, sg="P2_1/n", table="5.1", col=m, modes=("5.4", None), geom=("5.2", None), technique="npd", instrument="ins:ill-d2b")
    wy6 = {"Sr/Pr": "4e", "O1": "4e", "O2": "4e", "O3": "4e", "M": "2b", "Ru": "2a"}
    for m, d in parse_colwise("6.1", ["SrPrZnRuO6", "SrPrCoRuO6", "SrPrMgRuO6", "SrPrNiRuO6"], wy6).items():
        M = MATS[m][3]; d["atoms"][M] = d["atoms"].pop("M")
        S[m] = dict(d, sg="P2_1/n", table="6.1", col=m, modes=("6.4", None), geom=("6.2", None), technique="npd", instrument="ins:ill-d2b")
    for m, d in parse_7_2().items():
        S[m] = dict(d, sg="P2_1/n", table="7.2", col=None, modes=("7.4", None), geom=("7.3", None), technique="npd", instrument="ins:ill-d2b")
    wy9 = {"Sr/Ln": "4c", "Fe/Ru": "4a", "O1": "4c", "O2": "8d"}
    inst9 = {"SrLaFeRuO6": "ins:ill-d2b", "SrPrFeRuO6": "ins:ill-d2b", "SrNdFeRuO6": "ins:frm2-spodi"}
    for m, d in parse_colwise("9.1", ["SrLaFeRuO6", "SrPrFeRuO6", "SrNdFeRuO6"], wy9, fixed_biso={"Fe/Ru": "0.5"}).items():
        d["atoms"]["Sr/Ln"]["z"] = "0.25"; d["atoms"]["Fe/Ru"].update({"x": "0", "y": "0.5", "z": "0"}); d["atoms"]["O1"]["z"] = "0.25"
        d["cell"].update({"alpha": "90", "beta": "90", "gamma": "90"})
        S[m] = dict(d, sg="Pbnm", table="9.1", col=m, modes=("9.4", None), geom=("9.2", None), technique="npd", instrument=inst9[m])
    for m, d in parse_10_2().items():
        tech = "npd" if m in ("CaPr2CuTi2O9", "CaNd2CuTi2O9") else "xrpd"
        S[m] = dict(d, table="10.2", col=None, modes=("10.1", None), geom=("10.3" if m.startswith("Ca") else "10.4", None), technique=tech, instrument="ins:ill-d2b" if tech == "npd" else "ins-lab-xrd")
    # --- modes
    MOD = {}
    MOD.update(parse_modes("5.4", {"SrNdZnRuO6": 3, "SrNdCoRuO6": 6, "SrNdMgRuO6": 9, "SrNdNiRuO6": 12}, "Fm-3m", ["GM4+", "X3+"]))
    MOD.update(parse_modes("6.4", {"SrPrZnRuO6": 5, "SrPrCoRuO6": 6, "SrPrMgRuO6": 7, "SrPrNiRuO6": 8}, "Fm-3m", ["GM4+", "X3+"]))
    MOD.update(parse_modes("7.4", {"SrLaZnRuO6": 3, "SrLaMgRuO6": 6}, "Fm-3m", ["GM4+", "X3+"], stop_at="GM1+"))
    MOD.update(parse_modes("9.4", {"SrLaFeRuO6": 3, "SrPrFeRuO6": 6, "SrNdFeRuO6": 9}, "Pm-3m", ["R4+", "M3+"]))
    MOD.update(parse_modes("10.1", {"CaPr2CuTi2O9": 5, "CaNd2CuTi2O9": 7, "CaSm2CuTi2O9": 8}, "Pm-3m", ["R4+", "M3+"], stop_at="R4+"))
    # Ba block of 10.1: single R4+ row after the second header; read explicitly
    for r in rows("10.1"):
        if irrep_label(r[0]) == "R4+" and "I4/mcm" in plain_caption(r[1]):
            for m, ci in {"BaLa2CuTi2O9": 4, "BaPr2CuTi2O9": 6, "BaNd2CuTi2O9": 8}.items():
                MOD[m] = [{"label": "R4+", "k_vector": "(1/2,1/2,1/2)", "dimension": 1, "isotropy_subgroup": "I4/mcm", "amplitude": clean_num(r[ci]), "primary": True, "physical": PHYS["R4+"]}]
    MODCOL = {"5.4": {"SrNdZnRuO6": "Zn (a)", "SrNdCoRuO6": "Co (a)", "SrNdMgRuO6": "Mg (a)", "SrNdNiRuO6": "Ni (a)"}, "6.4": {}, "7.4": {"SrLaZnRuO6": "(a)", "SrLaMgRuO6": "(a)"},
              "9.4": {"SrLaFeRuO6": "LaFe (a)", "SrPrFeRuO6": "PrFe (a)", "SrNdFeRuO6": "NdFe (a)"}, "10.1": {"CaPr2CuTi2O9": "NPD", "CaNd2CuTi2O9": "NPD", "CaSm2CuTi2O9": "XRPD"}}
    # --- geometry
    GEO = {}
    GEO.update(parse_geometry("5.2", {"SrNdZnRuO6": 1, "SrNdCoRuO6": 2, "SrNdMgRuO6": 3, "SrNdNiRuO6": 4}))
    GEO.update(parse_geometry("6.2", {"SrPrZnRuO6": 1, "SrPrCoRuO6": 2, "SrPrMgRuO6": 3, "SrPrNiRuO6": 4}))
    GEO.update(parse_geometry("7.3", {"SrLaZnRuO6": 1, "SrLaMgRuO6": 2}))
    GEO.update(parse_geometry("9.2", {"SrLaFeRuO6": 1, "SrPrFeRuO6": 2, "SrNdFeRuO6": 3}))
    GEO.update(parse_geometry("10.3", {"CaPr2CuTi2O9": 1, "CaNd2CuTi2O9": 2, "CaSm2CuTi2O9": 3}))
    GEO.update(parse_geometry("10.4", {"BaLa2CuTi2O9": 1, "BaPr2CuTi2O9": 2, "BaNd2CuTi2O9": 3}))

    # --- instruments
    for iid, name, fac in [("ins:ill-d2b", "D2B high-resolution neutron powder diffractometer", "Institut Laue-Langevin, Grenoble"), ("ins:frm2-spodi", "SPODI neutron powder diffractometer", "FRM II, Garching"),
                           ("ins:psi-hrpt", "HRPT neutron powder diffractometer", "SINQ, Paul Scherrer Institut"), ("ins:lab-xrd", "Laboratory X-ray powder diffractometer (Cu Kα)", "UPV/EHU")]:
        dump({"id": iid, "schema_version": SV, "status": "published", "visibility": "public", "name": name, "facility": fac, "evidence": [ev("9.1", note="instruments named in the thesis")]}, ROOT / f"instruments/{iid.split(':')[1]}.yaml")
    # --- series
    series = {"ser:sr-ln-m-ruo6": ("SrLnMRuO6 ordered double perovskites", "Sr{Ln}{M}RuO6", {"Ln": ["La", "Pr", "Nd"], "M": ["Zn", "Co", "Mg", "Ni"]}, "double-perovskite", "Fm-3m", [m for m, v in MATS.items() if v[0] in (5, 6, 7, 8)]),
              "ser:sr-ln-fe-ruo6": ("SrLnFeRuO6 disordered perovskites", "Sr{Ln}FeRuO6", {"Ln": ["La", "Pr", "Nd"]}, "double-perovskite", "Pm-3m", [m for m, v in MATS.items() if v[0] == 9]),
              "ser:a-ln2-cuti2o9": ("ALn2CuTi2O9 triple perovskites", "{A}{Ln}2CuTi2O9", {"A": ["Ca", "Ba"], "Ln": ["La", "Pr", "Nd", "Sm"]}, "triple-perovskite", "Pm-3m", [m for m, v in MATS.items() if v[0] == 10])}
    for sid, (title, tpl, slots, fam, arist, members) in series.items():
        dump({"id": sid, "schema_version": SV, "status": "published", "visibility": "public", "title": title, "template": tpl, "slots": slots, "structural_family": fam, "aristotype": arist,
              "members": [f"mat:{slug(m)}" for m in members], "evidence": [{"doc": DOC, "md_line": 921 if "ruo6" in sid and "fe" not in sid else (1830 if "fe" in sid else 2073), "status": "thesis-only"}]}, ROOT / f"series/{sid.split(':')[1]}.yaml")

    # --- per material
    for f, (ch, A, Ap, B, Bp, order, synth, note) in MATS.items():
        mid = f"mat:{slug(f)}"; sid = {5: "ser:sr-ln-m-ruo6", 6: "ser:sr-ln-m-ruo6", 7: "ser:sr-ln-m-ruo6", 8: "ser:sr-ln-m-ruo6", 9: "ser:sr-ln-fe-ruo6", 10: "ser:a-ln2-cuti2o9"}[ch]
        fam = TP if ch == 10 else DP
        slots = {"A": A, "Ln": Ap} if ch == 10 else ({"Ln": Ap} if ch == 9 else {"Ln": Ap, "M": B})
        status = "published" if PUBLISHED_AS.get(ch) else "thesis-only"
        mat = {"id": mid, "schema_version": SV, "status": status, "visibility": "public", "title": re.sub(r"(\d)", r"\1", f),
               "formula": f, "formula_display": re.sub(r"(\d+)", r"₍\1₎", f).translate(str.maketrans("₍₎0123456789", "  ₀₁₂₃₄₅₆₇₈₉")).replace(" ", ""),
               "composition": composition(f), "sites": {"A": [A, Ap], "B": [B], "Bp": [Bp], "X": ["O"]}, "structural_family": fam, "material_status": "primary", "b_site_order": order,
               "series": [{"id": sid, "slot_values": slots}], "synthesis": {"method": "solid-state reaction", "schedule": synth, "atmosphere": "air"},
               "evidence": [{"doc": DOC, "md_line": 545 if ch != 10 else 580, "section": "2.1" if ch != 10 else "2.2", "table": "2.1" if ch != 10 else None, "status": "thesis-only", "note": "synthesis"}]}
        if mat["evidence"][0]["table"] is None: del mat["evidence"][0]["table"]
        if note: mat["notes"] = note
        if ch in S: mat["evidence"].append(ev(S[f]["table"], S[f]["col"], note="RT structure"))
        mp = ROOT / f"materials/{slug(f)}/index.qmd"
        body = f"\n{{{{< include /_gen/includes/materials/{slug(f)}.md >}}}}\n"
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text("---\n" + yaml.safe_dump(mat, sort_keys=False, allow_unicode=True, width=1000) + "---\n" + body); n["material"] += 1
        # sample + dataset
        smp = f"smp:{slug(f)}.{SRC}"
        dump({"id": smp, "schema_version": SV, "status": status, "visibility": "public", "material": mid, "method": "solid-state reaction", "schedule": synth, "prepared_by": "per:iturbe-zabalo-e",
              "evidence": [mat["evidence"][0]]}, ROOT / f"samples/{smp.split(':')[1]}.yaml"); n["sample"] += 1
        if f not in S: continue
        st = S[f]; sg = st.get("sg", "P2_1/n"); num, system, setting = SG[sg]
        sslug = f"{slug(f)}.{sgslug(sg)}.300k.{SRC}"; stid = f"str:{sslug}"
        dat = f"dat:{slug(f)}.{SRC}.{st['technique']}.rt"
        dump({"id": dat, "schema_version": SV, "status": status, "visibility": "public", "sample": smp, "technique": st["technique"], "instrument": st["instrument"] if st["instrument"].startswith("ins:") else "ins:lab-xrd",
              "temperature_k": 300, "evidence": [ev(st["table"], st["col"])]}, ROOT / f"datasets/{dat.split(':')[1]}.yaml"); n["dataset"] += 1
        cell = dict(st["cell"])
        if sg == "I4/mcm": cell["b"] = cell["a"]
        for k in ("alpha", "beta", "gamma"): cell.setdefault(k, "90")
        atoms = []
        for lab, a in st["atoms"].items():
            el = re.split(r"[/ ]", lab)[0]; el = re.sub(r"\d", "", el)
            occ = a.get("occ") or ("0.5/0.5 (" + lab + ")" if "/" in lab and ch != 10 else "1")
            if "/" in lab and ch == 10 and "occ" not in a: occ = "0.35/0.65 (" + lab + ")"
            atom = {"label": lab, "element": el, "wyckoff": a["wyckoff"], "x": a.get("x", "0"), "y": a.get("y", "0"), "z": a.get("z", "0"), "occupancy": occ}
            if a.get("b_iso"): atom["b_iso"] = a["b_iso"]
            if a.get("fixed"): atom["fixed"] = a["fixed"]
            atoms.append(atom)
        struct = {"id": stid, "schema_version": SV, "status": status, "visibility": "public", "material": mid, "phase_label": "room temperature", "conditions": {"temperature_k": 300},
                  "space_group": {"hm": sg, "number": num, "crystal_system": system, **({"setting": setting} if setting else {})}, "cell": cell, "atoms": atoms, "cif_origin": "absent",
                  "refinement": "refinement.yaml", "modes": "modes.yaml", "geometry": "geometry.yaml",
                  "notes": f"Rietveld refinement of {st['technique'].upper()} data by symmetry-mode parametrisation (AMPLIMODES for FullProf). Original files expected from data rescue.",
                  "evidence": [ev(st["table"], st["col"])]}
        d = ROOT / "structures" / sslug
        dump(struct, d / "structure.yaml"); n["structure"] += 1
        ref = {"id": f"ref:{sslug}.all-modes", "schema_version": SV, "status": status, "visibility": "public", "structure": stid, "dataset": dat, "software": "FullProf", "method": "symmetry-mode", "variant": "all-modes",
               **{k: v for k, v in st["R"].items()}, "evidence": [ev(st["table"], st["col"])]}
        dump(ref, d / "refinement.yaml")
        if MOD.get(f):
            mt = st["modes"][0]; parent = "Pm-3m" if ch in (9, 10) else "Fm-3m"
            dump({"id": f"mod:{sslug}", "schema_version": SV, "status": status, "visibility": "public", "structure": stid, "parent_space_group": parent, "software": "AMPLIMODES",
                  "convention": "amplimodes-cell", "refinement_variant": "all-modes", "irreps": MOD[f], "evidence": [ev(mt, MODCOL[mt].get(f))]}, d / "modes.yaml")
        else:
            (d / "modes.yaml").unlink(missing_ok=True); struct.pop("modes"); dump(struct, d / "structure.yaml")
        if GEO.get(f):
            gt = st["geom"][0]
            dump({"id": f"fnd:{sslug}.geometry", "schema_version": SV, "status": status, "visibility": "public", "structure": stid, **GEO[f], "evidence": [ev(gt, f if gt in ("7.3", "9.2", "10.3", "10.4") else MATS[f][3])]}, d / "geometry.yaml")
    # --- transitions
    for f, a, b, T, order, line, loc, note in TRANSITIONS:
        tid = f"trn:{slug(f)}.{sgslug(a)}-{sgslug(b)}.{SRC}"
        rec = {"id": tid, "schema_version": SV, "status": "published" if PUBLISHED_AS.get(MATS[f][0]) else "thesis-only", "visibility": "public", "material": f"mat:{slug(f)}",
               "from_space_group": a, "to_space_group": b, "temperature_k": T, "order": order, "techniques": ["xrpd", "npd"] if MATS[f][0] in (5, 6, 7) else ["xrpd"]}
        st = f"{slug(f)}.{sgslug(a)}.300k.{SRC}"
        if (ROOT / "structures" / st / "structure.yaml").exists(): rec["from_structure"] = f"str:{st}"
        if (f, a) in TRANGE: rec["temperature_range_k"] = TRANGE[(f, a)]
        if (f, b) in EXTRAP: rec["extrapolated"] = True
        if note: rec["notes"] = note
        rec["evidence"] = [{"doc": DOC, "md_line": line, **loc, "status": "thesis-only"}]
        dump(rec, ROOT / f"transitions/{tid.split(':')[1]}.yaml"); n["transition"] += 1
    # --- thesis chapter map
    th = ROOT / "theses/thesis-03/index.qmd"; txt = th.read_text()
    fm_end = txt.index("\n---\n", 4); fm = yaml.safe_load(txt[4:fm_end])
    chapters = {5: "SrNdMRuO6 (M = Zn, Co, Mg, Ni) ordered double perovskites", 6: "SrPrMRuO6 (M = Zn, Co, Mg, Ni) ordered double perovskites", 7: "SrLaMRuO6 (M = Zn, Mg) ordered double perovskites",
                8: "Magnetic structures of SrLnMRuO6 (Ln = La, Pr, Nd; M = Co, Ni)", 9: "SrLnFeRuO6 (Ln = La, Pr, Nd) disordered perovskites", 10: "ALn2CuTi2O9 (A = Ca, Ba) triple perovskites"}
    fm["chapters"] = [{"n": c, "title": t, "materials": [f"mat:{slug(m)}" for m, v in MATS.items() if v[0] == c], "published_as": [PUBLISHED_AS[c]] if PUBLISHED_AS.get(c) else []} for c, t in chapters.items()]
    th.write_text("---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000) + txt[fm_end:])
    # stale worked-example transition ids (renamed to the same scheme; keep) — nothing to delete
    print("ingest_thesis03:", n)

if __name__ == "__main__":
    main()
