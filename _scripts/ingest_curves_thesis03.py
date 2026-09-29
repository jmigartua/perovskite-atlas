"""Temperature-series curves from the tables of thesis 3 that report several temperatures.

- Table 9.9  SrLaFeRuO6, Pbnm, NPD (D1B, ILL) at 2, 50, 150, 200, 250 K: cell parameters, volume, Fe/Ru moment.
- Table 5.6  SrNdCoRuO6 mode amplitudes: P2_1/n at 300, 453, 603 K (column (a), all modes) and P4_2/n at 653, 803, 953 K
             (column (b), 4 highest modes; 653 K also has (a)). Signed amplitudes as reported.

Each curve is a record (`curves/<slug>/curve.yaml` + `curve.csv`) with the table locator as evidence and
`point_status: table`. Digitised figures and rescued refinements will add curves with their own status.
"""
from __future__ import annotations
import csv, io, re, pathlib, yaml
from common import ROOT
from ingest_thesis03 import rows, ev, clean_num, is_num, dump, plain_caption

SV = "0.1"; DOC = "doc:thesis-03"

def split_u(s: str) -> tuple[str, str]:
    """'5.5703(3)' -> ('5.5703', '0.0003'); '242.58(2)' -> ('242.58', '0.02'); '0.31' -> ('0.31', '')."""
    m = re.fullmatch(r"(-?\d+)(?:\.(\d+))?(?:\((\d+)\))?", s.replace("−", "-"))
    if not m: return s, ""
    ip, fp, u = m.group(1), m.group(2) or "", m.group(3)
    val = f"{ip}.{fp}" if fp else ip
    if u is None: return val, ""
    return val, f"{float(u) * 10 ** (-len(fp)):.{len(fp)}f}"

def write_curve(slug: str, rec: dict, header: list[str], points: list[list[str]]):
    d = ROOT / "curves" / slug; d.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(header); w.writerows(points)
    (d / "curve.csv").write_text(buf.getvalue())
    rec = {"id": f"crv:{slug}", "schema_version": SV, **rec, "csv": "curve.csv"}
    dump(rec, d / "curve.yaml")

def table_9_9():
    R = rows("9.9"); temps = [c for c in R[0][2:] if c]
    want = {"a": ("a", "$a$", "Å"), "b": ("b", "$b$", "Å"), "c": ("c", "$c$", "Å"), "V": ("V", "$V$", "Å^3")}
    series = {}
    moment = None
    for r in R[1:]:
        lab = plain_caption(r[0]).strip(); par = plain_caption(r[1]).strip() if len(r) > 1 else ""
        key = re.match(r"^(a|b|c|V)\b", lab)
        if key and all(is_num(clean_num(v)) for v in r[2:2 + len(temps)]):
            series[key.group(1)] = [clean_num(v) for v in r[2:2 + len(temps)]]
        if par.startswith("m(Fe"):
            moment = [clean_num(v) for v in r[2:2 + len(temps)]]
    header = ["T"]; cols = []
    for k in ("a", "b", "c", "V"):
        header += [k, f"{k}_u"]; cols.append(k)
    pts = []
    for i, t in enumerate(temps):
        row = [t]
        for k in cols:
            v, u = split_u(series[k][i]); row += [v, u]
        pts.append(row)
    write_curve("srlaferuo6.cell-vs-t.iturbe2012", {
        "status": "thesis-only", "visibility": "public", "material": "mat:srlaferuo6", "title": "SrLaFeRuO6 · cell parameters vs T (2–250 K, NPD D1B)",
        "kind": "cell-vs-t", "technique": "npd", "instrument": "ins:ill-d1b", "phase": "Pbnm",
        "x": {"quantity": "Temperature", "symbol": "$T$", "unit": "K", "column": "T"},
        "y": [{"quantity": k, "symbol": want[k][1], "unit": want[k][2], "column": k, "group": "cell" if k != "V" else "volume"} for k in cols],
        "point_status": "table", "reproduces": ["plt:thesis-03.9.7"] if False else [],
        "notes": "Low-temperature NPD (D1B, ILL) refinements in Pbnm; the table also gives atomic coordinates and the magnetic moment per temperature.",
        "evidence": [ev("9.9")]}, header, pts)
    if moment:
        pts = []
        for i, t in enumerate(temps):
            v, u = split_u(moment[i]); pts.append([t, v, u])
        write_curve("srlaferuo6.moment-vs-t.iturbe2012", {
            "status": "thesis-only", "visibility": "public", "material": "mat:srlaferuo6", "title": "SrLaFeRuO6 · ordered magnetic moment on Fe/Ru vs T (NPD D1B)",
            "kind": "moment-vs-t", "technique": "npd", "instrument": "ins:ill-d1b", "phase": "Pbnm",
            "x": {"quantity": "Temperature", "symbol": "$T$", "unit": "K", "column": "T"},
            "y": [{"quantity": "m(Fe/Ru)", "symbol": "$m_{\\mathrm{Fe/Ru}}$", "unit": "μB", "column": "m"}],
            "point_status": "table", "evidence": [ev("9.9")]}, ["T", "m", "m_u"], pts)

def table_5_6():
    R = rows("5.6")
    # block 1 header: Irrep, Mode, 300 K (a), 300 K (b), 453 K (a), 453 K (b), 603 K (a), 603 K (b)
    def temps_of(header):
        out = []
        for c in header[2:]:
            m = re.search(r"(\d{3,4})\s*K.*\((a|b)\)", plain_caption(c))
            out.append((m.group(1), m.group(2)) if m else None)
        return out
    blocks = []; cur = None
    for r in R:
        if r[0].strip() == "Irrep":
            cur = {"temps": temps_of(r), "rows": []}; blocks.append(cur); continue
        if cur is not None: cur["rows"].append(r)
    IRREPS = {"GM3+": "$\\mathrm{GM}_3^+$", "GM4+": "$\\mathrm{GM}_4^+$", "X3+": "$\\mathrm{X}_3^+$", "X5+": "$\\mathrm{X}_5^+$"}
    def lab(s):
        s = plain_caption(s).replace(" ", "")
        s = re.sub(r"[₀-₉]", lambda m: str("₀₁₂₃₄₅₆₇₈₉".index(m.group(0))), s).replace("⁺", "+")
        return s
    points = {}  # (T, phase) -> {irrep: (v,u)}
    phase = None
    for b in blocks:
        for r in b["rows"]:
            l0 = lab(r[0])
            if l0.startswith("P21/n"): phase = "P2_1/n"; continue
            if l0.startswith("P42/n"): phase = "P4_2/n"; continue
            if l0 in ("GM4+", "X3+", "GM3+") or (l0 == "X5+"):
                # first mode row of each irrep carries the irrep label; for X5+ take the first row (A10 / A8)
                for tv, v in zip(b["temps"], r[2:]):
                    if not tv: continue
                    t, var = tv
                    want = "a" if phase == "P2_1/n" else "b"
                    if var != want or not is_num(clean_num(v)): continue
                    if phase == "P2_1/n" and l0 == "GM3+": continue
                    points.setdefault((int(t), phase), {})[l0] = split_u(clean_num(v))
    irreps = ["GM3+", "GM4+", "X3+", "X5+"]
    header = ["T", "phase"] + [x for i in irreps for x in (i, i + "_u")]
    pts = []
    for (t, ph), d in sorted(points.items()):
        row = [str(t), ph]
        for i in irreps:
            v, u = d.get(i, ("", "")); row += [v, u]
        pts.append(row)
    write_curve("srndcoruo6.modes-vs-t.iturbe2012", {
        "status": "thesis-only", "visibility": "public", "material": "mat:srndcoruo6", "title": "SrNdCoRuO6 · symmetry-mode amplitudes vs T (NPD; P2₁/n then P4₂/n)",
        "kind": "modes-vs-t", "technique": "npd", "instrument": "ins:ill-d2b",
        "x": {"quantity": "Temperature", "symbol": "$T$", "unit": "K", "column": "T"},
        "y": [{"quantity": i, "symbol": IRREPS[i], "unit": "Å", "column": i, "group": "amplitude"} for i in irreps],
        "point_status": "table",
        "notes": "P2_1/n points from column (a) (all modes refined); P4_2/n points from column (b) (four highest modes). Amplitudes are signed as reported; GM3+ is only refined in P4_2/n. Convention amplimodes-cell.",
        "evidence": [ev("5.6")]}, header, pts)

def main():
    for iid, name, fac in [("ins:ill-d1b", "D1B neutron powder diffractometer", "Institut Laue-Langevin, Grenoble")]:
        dump({"id": iid, "schema_version": SV, "status": "published", "visibility": "public", "name": name, "facility": fac, "evidence": [ev("9.9", note="instrument named in the table caption")]}, ROOT / f"instruments/{iid.split(':')[1]}.yaml")
    table_9_9(); table_5_6()
    print("ingest_curves_thesis03: 3 curves")

if __name__ == "__main__":
    main()
