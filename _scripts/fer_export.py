"""Export the atlas records as fer (Framework for Experimental Results) documents.

Protocol: docs/FER_MIGRATION.md. The records are not modified; fer documents are a computed layer
(`_data/computed/fer/`), one JSON per refined structure, per mode decomposition and per geometry
finding, each validated against the vendored schema `_schemas/external/fer-schema.json` (draft-07).

Usage: python3 _scripts/fer_export.py            # writes _data/computed/fer/**.json and reports/fer.md
"""
from __future__ import annotations
import json, re, subprocess, datetime, pathlib
from collections import defaultdict
from jsonschema import Draft7Validator
from common import ROOT, iter_records

OUT = ROOT / "_data/computed/fer"
SCHEMA = json.loads((ROOT / "_schemas/external/fer-schema.json").read_text())
VALIDATOR = Draft7Validator(SCHEMA)
ATLAS_VERSION = "0.1"
FER_SCHEMA_VERSION = "fer-schema.json (jongablop/fer main, vendored 2026-09-28)"

def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"

NOW = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")
SHA = git_sha()

# ----------------------------------------------------------------- uncertainty parsing
def parse_measured(s) -> tuple[float, float, bool]:
    """'5.5570(1)' -> (5.5570, 0.0001, True); '90' -> (90.0, 0.0, False); '-0.0066(5)' -> (-0.0066, 0.0005, True)."""
    s = str(s).strip().replace("−", "-")
    m = re.fullmatch(r"(-?\d+)(?:\.(\d+))?(?:\((\d+)\))?", s)
    if not m:
        raise ValueError(f"not a measured value: {s!r}")
    ip, fp, u = m.group(1), m.group(2) or "", m.group(3)
    value = float(f"{ip}.{fp}" if fp else ip)
    if u is None:
        return value, 0.0, False
    return value, float(u) * 10.0 ** (-len(fp)), True

# ----------------------------------------------------------------- fer builders
def changelog(desc: str):
    return [{"timestamp": NOW, "user": "perovskite-atlas/fer_export.py", "description": f"{desc} Generated from atlas records at git {SHA}."}]

def qv(qid: str, name: str, quantities, symbols, units, measured, description: str = ""):
    """QuantityValues from a list of measured strings (one value per quantity)."""
    vals, unc, reported = [], [], []
    for m in measured:
        v, u, r = parse_measured(m); vals.append([v]); unc.append([u]); reported.append(r)
    d = {"id": qid, "name": name, "description": description, "quantities": list(quantities), "symbols": list(symbols), "units": list(units),
         "values": vals, "standard_uncertainties": unc,
         "atlas": {"uncertainty_reported": reported, "reported_as": [str(m) for m in measured]}}
    return d

def source(sid: str, name: str, model: str, influence=(), inputs=(), description: str = ""):
    return {"id": sid, "name": name, "description": description, "model": model, "influence_quantities": list(influence), "input_quantities": list(inputs)}

def measurement(mid: str, description: str, results, src, measurands, state=(), atlas=None, log="Export."):
    d = {"id": mid, "changelog": changelog(log), "description": description, "correct": True, "state": list(state), "results": list(results),
         "measurands": list(measurands), "source": src}
    if atlas: d["atlas"] = atlas
    return d

def evidence_of(rec: dict):
    return {"record_id": rec["id"], "status": rec.get("status"), "evidence": rec.get("evidence", []), "atlas_schema_version": rec.get("schema_version")}

# ----------------------------------------------------------------- load records
by_id = {}; kits = defaultdict(dict)
for kind, path, rec in iter_records():
    if isinstance(rec, dict) and rec.get("id"):
        rec = dict(rec); rec["_kind"] = kind; by_id[rec["id"]] = rec
        if kind in ("refinement", "modes", "geometry"): kits[rec["structure"]][kind] = rec

def temperature_state(struct):
    T = struct["conditions"]["temperature_k"]
    q = qv(f"{struct['id']}#T", "Temperature", ["Temperature"], ["$T$"], ["K"], [str(T)], "Temperature of the measurement as reported (uncertainty not reported)")
    return {"name": "temperature", "description": "conditions of the refined structure", "quantity_value": q}

def dataset_measurement(ds: dict | None, struct: dict):
    """The diffraction pattern as an input measurement (results empty until raw data is rescued)."""
    if not ds:
        return None
    ins = by_id.get(ds.get("instrument", ""), {})
    return measurement(ds["id"], f"{ds['technique'].upper()} pattern of {struct['material']} at {struct['conditions']['temperature_k']} K" + (f" on {ins.get('name')} ({ins.get('facility')})" if ins else ""),
                       [], source(ds.get("instrument", "ins:unknown"), ins.get("name", "instrument"), "powder diffraction", inputs=[]), ["diffraction pattern"],
                       atlas=evidence_of(ds) | {"note": "raw pattern not yet attached; results are empty by design until data rescue"}, log="Dataset stub.")

def export_structure(st: dict) -> dict:
    ref = kits[st["id"]].get("refinement", {})
    cell = st["cell"]
    results = [qv(f"{st['id']}#cell", "Unit cell", ["a", "b", "c", "alpha", "beta", "gamma"], ["$a$", "$b$", "$c$", "$\\alpha$", "$\\beta$", "$\\gamma$"], ["Å", "Å", "Å", "°", "°", "°"],
                  [cell["a"], cell["b"], cell["c"], cell["alpha"], cell["beta"], cell["gamma"]], f"Cell parameters, space group {st['space_group']['hm']} (No. {st['space_group']['number']})")]
    if cell.get("volume"):
        results.append(qv(f"{st['id']}#volume", "Cell volume", ["V"], ["$V$"], ["Å^3"], [cell["volume"]]))
    for a in st["atoms"]:
        qs, syms, units, vals = ["x", "y", "z"], ["$x$", "$y$", "$z$"], ["1", "1", "1"], [a["x"], a["y"], a["z"]]
        if a.get("b_iso"):
            qs.append("B_iso"); syms.append("$B_{\\mathrm{iso}}$"); units.append("Å^2"); vals.append(a["b_iso"])
        results.append(qv(f"{st['id']}#atom:{a['label']}", f"Atom {a['label']} ({a['element']}, Wyckoff {a['wyckoff']})", qs, syms, units, vals,
                          f"Fractional coordinates and isotropic displacement; occupancy {a.get('occupancy', '1')}" + ("; B_iso fixed" if "b_iso" in a.get("fixed", []) else "")))
    if ref:
        rq = [(k, ref[k]) for k in ("r_p", "r_wp", "r_exp", "r_bragg", "chi2") if ref.get(k) is not None]
        if rq:
            results.append(qv(f"{st['id']}#reliability", "Rietveld reliability factors", [k for k, _ in rq], ["$R_p$", "$R_{wp}$", "$R_{exp}$", "$R_{Bragg}$", "$\\chi^2$"][:0] + [{"r_p": "$R_p$", "r_wp": "$R_{wp}$", "r_exp": "$R_{exp}$", "r_bragg": "$R_{Bragg}$", "chi2": "$\\chi^2$"}[k] for k, _ in rq],
                              ["%" if k != "chi2" else "1" for k, _ in rq], [str(v) for _, v in rq], "As reported; no uncertainties"))
    ds = by_id.get(ref.get("dataset", "")) if ref else None
    inputs = [m for m in [dataset_measurement(ds, st)] if m]
    src = source(ref.get("id", f"{st['id']}#refinement"), f"Rietveld refinement ({ref.get('software', 'unknown software')}, {ref.get('method', 'unknown method')})",
                 "Least-squares Rietveld refinement of the powder pattern; symmetry-mode parametrisation where method = symmetry-mode" + (f"; variant {ref['variant']}" if ref.get("variant") else ""),
                 influence=[temperature_state(st)["quantity_value"]], inputs=inputs, description=ref.get("notes", ""))
    return measurement(st["id"], f"Refined crystal structure of {by_id[st['material']]['formula']} at {st['conditions']['temperature_k']} K, {st['space_group']['hm']}",
                       results, src, ["unit cell", "atomic coordinates", "displacement parameters"], state=[temperature_state(st)], atlas=evidence_of(st) | {"refinement": evidence_of(ref) if ref else None},
                       log="Refined structure.")

def export_modes(md: dict, st_doc: dict) -> dict:
    st = by_id[md["structure"]]
    labels = [i["label"] for i in md["irreps"]]
    res = [qv(f"{md['id']}#amplitudes", "Symmetry-mode amplitudes by irrep", labels, [f"$A({l})$" for l in labels], ["Å"] * len(labels), [i["amplitude"] for i in md["irreps"]],
              f"Global amplitude per irreducible representation of the parent {md['parent_space_group']}; convention {md.get('convention')}; primary: " + ", ".join(i["label"] for i in md["irreps"] if i.get("primary")))]
    src = source(f"{md['id']}#decomposition", f"Symmetry-mode decomposition ({md.get('software')})",
                 f"Projection of the refined structure onto symmetry-adapted modes of the parent {md['parent_space_group']}" + (f"; transformation {md['transformation']}" if md.get("transformation") else "") + f"; normalization {md.get('convention')}",
                 inputs=[st_doc], description=md.get("notes", ""))
    return measurement(md["id"], f"Symmetry-mode decomposition of {by_id[st['material']]['formula']} at {st['conditions']['temperature_k']} K", res, src, ["mode amplitudes"],
                       state=[temperature_state(st)], atlas=evidence_of(md) | {"irreps": md["irreps"]}, log="Mode decomposition.")

def export_geometry(g: dict, st_doc: dict) -> dict:
    st = by_id[g["structure"]]; res = []
    if g.get("bonds"): res.append(qv(f"{g['id']}#bonds", "Bond lengths", list(g["bonds"]), [f"$d({k})$" for k in g["bonds"]], ["Å"] * len(g["bonds"]), list(g["bonds"].values())))
    if g.get("angles"): res.append(qv(f"{g['id']}#angles", "Bond angles", list(g["angles"]), [f"$\\angle({k})$" for k in g["angles"]], ["°"] * len(g["angles"]), list(g["angles"].values())))
    if g.get("tilts"): res.append(qv(f"{g['id']}#tilts", "Octahedral tilt angles", list(g["tilts"]), list(g["tilts"]), ["°"] * len(g["tilts"]), list(g["tilts"].values())))
    if g.get("bvs"): res.append(qv(f"{g['id']}#bvs", "Bond-valence sums", list(g["bvs"]), [f"$V({k})$" for k in g["bvs"]], ["1"] * len(g["bvs"]), list(g["bvs"].values())))
    for name, o in g.get("octahedra", {}).items():
        qs = [k for k in ("volume", "average_bond", "predicted_bond") if o.get(k)]
        if qs: res.append(qv(f"{g['id']}#octahedron:{name}", f"Octahedron {name}", qs, [f"${k}$" for k in qs], ["Å^3" if k == "volume" else "Å" for k in qs], [o[k] for k in qs]))
    src = source(f"{g['id']}#derivation", "Geometry derived from the refined structure", "Interatomic distances, angles and bond-valence sums computed from the refined coordinates and cell (as reported in the source document)", inputs=[st_doc])
    return measurement(g["id"], f"Reported geometry of {by_id[st['material']]['formula']} at {st['conditions']['temperature_k']} K", res, src, ["bond lengths", "bond angles", "bond-valence sums"],
                       state=[temperature_state(st)], atlas=evidence_of(g), log="Geometry.")

def main():
    n = defaultdict(int); errors = []; unreported = 0; total_q = 0
    for kind_dir in ("structures", "modes", "geometry"):
        (OUT / kind_dir).mkdir(parents=True, exist_ok=True)
    index = []
    for st in [r for r in by_id.values() if r["_kind"] == "structure" and r.get("visibility") == "public"]:
        docs = {"structures": export_structure(st)}
        if "modes" in kits[st["id"]]: docs["modes"] = export_modes(kits[st["id"]]["modes"], docs["structures"])
        if "geometry" in kits[st["id"]]: docs["geometry"] = export_geometry(kits[st["id"]]["geometry"], docs["structures"])
        for kind_dir, doc in docs.items():
            errs = sorted(VALIDATOR.iter_errors(doc), key=lambda e: list(e.path))
            if errs:
                errors.append((doc["id"], [f"{'/'.join(map(str, e.path))}: {e.message}" for e in errs[:3]])); continue
            slug = doc["id"].split(":", 1)[1]
            (OUT / kind_dir / f"{slug}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
            n[kind_dir] += 1; index.append({"id": doc["id"], "kind": kind_dir, "file": f"{kind_dir}/{slug}.json", "description": doc["description"]})
            for r in doc["results"]:
                total_q += len(r["quantities"]); unreported += sum(1 for x in r["atlas"]["uncertainty_reported"] if not x)
    (OUT / "index.json").write_text(json.dumps({"generated": NOW, "git": SHA, "atlas_schema_version": ATLAS_VERSION, "fer_schema": FER_SCHEMA_VERSION, "documents": index}, indent=1, ensure_ascii=False))
    rep = ROOT / "_data/computed/reports"; rep.mkdir(parents=True, exist_ok=True)
    lines = [f"# fer export report ({NOW}, git {SHA})", "", f"- structures: {n['structures']}", f"- mode decompositions: {n['modes']}", f"- geometry findings: {n['geometry']}",
             f"- quantities exported: {total_q}, of which {unreported} without a reported uncertainty (standard_uncertainty set to 0, flagged in atlas.uncertainty_reported)", f"- schema errors: {len(errors)}"]
    for did, es in errors: lines += [f"  - {did}"] + [f"      {e}" for e in es]
    (rep / "fer.md").write_text("\n".join(lines) + "\n")
    print(f"fer_export: {dict(n)} · {total_q} quantities ({unreported} without reported uncertainty) · {len(errors)} schema error(s) → _data/computed/fer/")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
