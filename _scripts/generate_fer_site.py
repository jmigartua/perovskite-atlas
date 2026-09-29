"""Generate the fer viewer: pages under fer/ rendered ONLY from the fer documents in _data/computed/fer/.

The viewer never reads the atlas records; that is the point. If something is missing on a fer page,
the fer document is missing it. Links back to the atlas are derived from the atlas ids the documents
carry (str:, mod:, fnd:), and the atlas pages link here (see generate.py, fer_link()).

Output (gitignored): fer/index.qmd, fer/<kind>/<slug>/index.qmd, plus the raw JSON served from
_data/computed/fer/ (declared as a Quarto resource).
"""
from __future__ import annotations
import json, html, re, pathlib, yaml
from common import ROOT

FER = ROOT / "_data/computed/fer"
OUTDIR = ROOT / "fer"
KINDS = {"structures": "Refined structures", "modes": "Symmetry-mode decompositions", "geometry": "Derived geometry"}

def fm(d): return "---\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True) + "---\n\n"
def write(rel, text):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
def esc(s): return html.escape(str(s), quote=False)
def unit(u: str) -> str:
    return {"Å^2": "Å²", "Å^3": "Å³", "1": ""}.get(u, u)
def atlas_url(aid: str) -> str | None:
    kind, _, slug = aid.partition(":")
    if kind == "str": return f"/structures/{slug}/"
    if kind == "mod": return f"/structures/{slug}/#symmetry-mode-decomposition"
    if kind == "fnd" and slug.endswith(".geometry"): return f"/structures/{slug[:-9]}/#geometry-as-reported"
    if kind == "dat": return f"/datasets/"
    return None
def fer_url(aid: str, kind: str) -> str:
    return f"/fer/{kind}/{aid.split(':', 1)[1]}/"
def table(headers, rows):
    if not rows: return "*None.*\n\n"
    return "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n" + "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows) + "\n\n"
def crumbs(items):
    return "<nav class='crumbs' aria-label='Breadcrumb'>" + " <span class='sep'>›</span> ".join(f"<a href='{u}'>{l}</a>" if u else f"<span>{l}</span>" for l, u in items) + "</nav>\n\n"
def fmt(v: float) -> str:
    return f"{v:.10g}"

def qv_table(q: dict) -> str:
    rep = (q.get("atlas") or {}).get("uncertainty_reported")
    rows = []
    reported_as = (q.get("atlas") or {}).get("reported_as") or []
    for i, name in enumerate(q["quantities"]):
        val = q["values"][i][0] if q["values"][i] else ""
        if i < len(reported_as):  # keep the reported precision (1.200 rather than 1.2)
            val = re.sub(r"\(\d+\)$", "", str(reported_as[i])).replace("\u2212", "-")
        u = q["standard_uncertainties"][i][0] if q["standard_uncertainties"][i] else ""
        sym = q["symbols"][i] if i < len(q.get("symbols", [])) else ""
        flag = "" if rep is None else ("" if rep[i] else "<span class='flag'>not reported</span>")
        rows.append([esc(name), sym, val if isinstance(val, str) else fmt(val), (fmt(u) if u != "" else ""), unit(q["units"][i]), flag])
    body = f"**{esc(q['name'])}**" + (f" · {esc(q['description'])}" if q.get("description") else "") + "\n\n"
    return body + table(["quantity", "symbol", "value", "u (standard)", "unit", ""], rows)

def bar_chart(q: dict, title: str) -> str:
    """Inline SVG: one bar per quantity with a standard-uncertainty whisker; axis at zero; theme tokens for colour."""
    names = q["quantities"]; vals = [v[0] for v in q["values"]]; unc = [u[0] for u in q["standard_uncertainties"]]
    n = len(vals)
    if n == 0: return ""
    W, H, L, R, T, B = 720, 260, 56, 16, 18, 44
    lo = min(0, min(v - u for v, u in zip(vals, unc))); hi = max(0, max(v + u for v, u in zip(vals, unc))); span = (hi - lo) or 1
    hi += span * 0.08; lo -= span * 0.08 if lo < 0 else 0; span = hi - lo
    y = lambda v: T + (hi - v) / span * (H - T - B)
    bw = (W - L - R) / n; bar = bw * 0.6
    ticks = 4; s = f"<svg class='fer-chart' viewBox='0 0 {W} {H}' role='img' aria-label='{esc(title)}'>"
    for k in range(ticks + 1):
        tv = lo + span * k / ticks; ty = y(tv)
        s += f"<line x1='{L}' x2='{W-R}' y1='{ty:.1f}' y2='{ty:.1f}' class='grid'/><text x='{L-6}' y='{ty+4:.1f}' class='tick' text-anchor='end'>{tv:.2f}</text>"
    s += f"<line x1='{L}' x2='{W-R}' y1='{y(0):.1f}' y2='{y(0):.1f}' class='axis'/>"
    for i, (nm, v, u) in enumerate(zip(names, vals, unc)):
        x = L + bw * i + (bw - bar) / 2; y0, y1 = y(0), y(v)
        s += f"<rect x='{x:.1f}' y='{min(y0,y1):.1f}' width='{bar:.1f}' height='{abs(y1-y0):.1f}' class='bar'/>"
        if u: cx = x + bar / 2; s += f"<line x1='{cx:.1f}' x2='{cx:.1f}' y1='{y(v-u):.1f}' y2='{y(v+u):.1f}' class='whisker'/>"
        s += f"<text x='{x + bar/2:.1f}' y='{H-B+16}' class='label' text-anchor='middle'>{esc(nm)}</text>"
    s += f"<text x='{L}' y='{H-6}' class='caption'>{esc(title)} · unit {unit(q['units'][0])} · whiskers: standard uncertainty</text></svg>"
    return "```{=html}\n" + s + "\n```\n\n"

def json_html(obj, depth: int = 0, key: str | None = None, comma: bool = False) -> str:
    """Pretty JSON as block lines with colour classes; objects/arrays are collapsible <details> (open to depth 2)."""
    ind = "\u00a0" * (2 * depth)
    k = f"<span class='jk'>\"{esc(key)}\"</span><span class='jp'>: </span>" if key is not None else ""
    c = "<span class='jp'>,</span>" if comma else ""
    def line(inner): return f"<div class='jl'>{ind}{inner}</div>"
    if isinstance(obj, dict) or (isinstance(obj, list) and not (all(not isinstance(x, (dict, list)) for x in obj) and len(obj) <= 12)):
        is_obj = isinstance(obj, dict); ob, cb = ("{", "}") if is_obj else ("[", "]")
        if not obj: return line(f"{k}<span class='jp'>{ob}{cb}</span>{c}")
        items = list(obj.items()) if is_obj else [(None, v) for v in obj]
        inner = "".join(json_html(v, depth + 1, kk, i < len(items) - 1) for i, (kk, v) in enumerate(items))
        op = " open" if depth < 2 else ""
        n = f"{len(items)} {'keys' if is_obj else 'items'}"
        return f"<details class='jn'{op}><summary>{ind}{k}<span class='jp'>{ob}</span><span class='jc'> {n} {cb}{',' if comma else ''}</span></summary>{inner}<div class='jl'>{ind}<span class='jp'>{cb}</span>{c}</div></details>"
    if isinstance(obj, list):
        return line(f"{k}<span class='jp'>[</span>" + "<span class='jp'>, </span>".join(json_scalar(x) for x in obj) + f"<span class='jp'>]</span>{c}")
    return line(f"{k}{json_scalar(obj)}{c}")

def json_scalar(obj) -> str:
    if obj is None: return "<span class='jnull'>null</span>"
    if isinstance(obj, bool): return f"<span class='jb'>{str(obj).lower()}</span>"
    if isinstance(obj, (int, float)): return f"<span class='jnum'>{json.dumps(obj)}</span>"
    return f"<span class='js'>{esc(json.dumps(obj, ensure_ascii=False))}</span>"

def json_tab(doc: dict, kind: str) -> str:
    aid = doc["id"]; jid = "json-" + aid.split(":", 1)[1].replace(".", "-")
    raw = json.dumps(doc, indent=2, ensure_ascii=False)
    return ("```{=html}\n<div class='fer-tabs' data-tabs>\n<div class='tabbar' role='tablist'><button type='button' class='tab is-active' data-tab='view'>Rendered</button><button type='button' class='tab' data-tab='json'>JSON</button>"
            f"<span class='tab-actions'><button type='button' class='copy' data-copy='{jid}'>Copy JSON</button><a class='btn' href='/_data/computed/fer/{kind}/{aid.split(':',1)[1]}.json' download>Download</a><button type='button' class='btn' data-json-expand='{jid}'>Expand all</button><button type='button' class='btn' data-json-collapse='{jid}'>Collapse</button></span></div>\n"
            f"<div class='tabpanel is-active' data-panel='view'></div>\n"
            f"<div class='tabpanel' data-panel='json'><div class='json' id='{jid}-view'>{json_html(doc)}</div><pre id='{jid}' hidden>{esc(raw)}</pre></div>\n</div>\n```\n\n")

def render_measurement(doc: dict, kind: str, known: dict[str, str], depth: int = 0) -> str:
    """Markdown for a fer Measurement. `known` maps document ids to their viewer urls (for nested inputs)."""
    b = ""
    b += f"<p class='meta'>id <code>{esc(doc['id'])}</code> · correct <b>{str(doc.get('correct', '')).lower()}</b> · measurands <b>{esc(', '.join(doc.get('measurands', [])))}</b></p>\n\n"
    if depth == 0:
        aid = doc["id"]; au = atlas_url(aid)
        b += "<div class='fer-actions'>" + (f"<a class='btn' href='{au}'>Open in the atlas</a>" if au else "") + f"<a class='btn' href='/_data/computed/fer/{kind}/{aid.split(':',1)[1]}.json' download>Download fer JSON</a></div>\n\n"
    if doc.get("state"):
        b += "#### State\n\n" + "".join(qv_table(s["quantity_value"]) for s in doc["state"] if s.get("quantity_value"))
    b += "#### Results\n\n" if doc.get("results") else "#### Results\n\n*Empty (no results attached yet).*\n\n"
    for q in doc.get("results", []):
        b += qv_table(q)
        if kind == "modes" and depth == 0 and "amplitude" in q["name"].lower():
            b += bar_chart(q, q["name"])
    src = doc.get("source", {})
    b += "#### Source\n\n" + f"**{esc(src.get('name',''))}**" + (f" · model: {esc(src.get('model',''))}" if src.get("model") else "") + (f"\n\n{esc(src['description'])}" if src.get("description") else "") + "\n\n"
    if src.get("influence_quantities"):
        b += "Influence quantities\n\n" + "".join(qv_table(q) for q in src["influence_quantities"])
    if src.get("input_quantities"):
        b += "Input quantities\n\n"
        for inp in src["input_quantities"]:
            link = known.get(inp["id"])
            b += f"<details class='fer-input'><summary><code>{esc(inp['id'])}</code> · {esc(inp.get('description',''))}" + (f" · <a href='{link}'>own page</a>" if link else "") + "</summary>\n\n" + render_measurement(inp, kind, known, depth + 1) + "</details>\n\n"
    if doc.get("changelog"):
        b += "#### Changelog\n\n" + table(["timestamp", "user", "description"], [[esc(c.get("timestamp","")), esc(c.get("user","")), esc(c.get("description",""))] for c in doc["changelog"]])
    at = doc.get("atlas")
    if at and depth == 0:
        b += "#### Atlas extension\n\n" + f"record <code>{esc(at.get('record_id',''))}</code> · status <b>{esc(at.get('status',''))}</b>\n\n"
        if at.get("evidence"):
            b += "\n".join("- " + " · ".join(f"{k} {esc(v)}" for k, v in e.items() if k != "cell") + ("" if not e.get("cell") else " · cell " + esc(str(e["cell"]))) for e in at["evidence"]) + "\n\n"
    return b

def main():
    idx = json.loads((FER / "index.json").read_text())
    docs = {}
    for d in idx["documents"]:
        docs[d["id"]] = (d["kind"], json.loads((FER / d["file"]).read_text()))
    known = {aid: fer_url(aid, kind) for aid, (kind, _) in docs.items()}
    n = 0
    for aid, (kind, doc) in docs.items():
        title = esc(doc.get("description", aid))
        body = crumbs([("fer", "/fer/"), (KINDS[kind], f"/fer/#{kind}"), (aid, None)]) + f"# {title}\n\n" + json_tab(doc, kind) + "::: {.fer-rendered}\n" + render_measurement(doc, kind, known) + "\n:::\n"
        write(f"fer/{kind}/{aid.split(':',1)[1]}/index.qmd", fm({"title": doc.get("description", aid), "pagetitle": doc.get("description", aid)}) + "::: {.page-article .with-crumbs .fer}\n" + body + ":::\n"); n += 1
    # landing
    counts = {k: sum(1 for _, (kk, _) in docs.items() if kk == k) for k in KINDS}
    body = ("This is the same corpus as the atlas, read back from its **fer** documents (Framework for Experimental Results). Every page here is generated only from the JSON files under `_data/computed/fer/`; "
            "nothing is taken from the atlas records. Each document is a fer *measurement*: results as quantity values with standard uncertainties and units, a *source* that names the model and nests the input measurements, "
            "the *state* (conditions), a changelog, and an `atlas` extension carrying the evidence locators. From any page, *Open in the atlas* goes to the record it was made from; atlas pages link back here.\n\n"
            f"Generated {esc(idx['generated'])} from git `{esc(idx['git'])}` · fer schema: {esc(idx['fer_schema'])} · [protocol](/about/#fer) · [download all (zip)](/_data/computed/fer/perovskite-atlas-fer.zip) · [index.json](/_data/computed/fer/index.json)\n\n")
    body += "<div class='counts'>" + "".join(f"<div><b>{counts[k]}</b><span>{v}</span></div>" for k, v in KINDS.items()) + "</div>\n\n"
    for k, label in KINDS.items():
        rows = [[f"[{esc(doc['description'])}]({fer_url(aid, k)})", f"<code>{esc(aid)}</code>", len(doc.get("results", [])), sum(len(q['quantities']) for q in doc.get("results", []))] for aid, (kk, doc) in docs.items() if kk == k]
        body += f"## {label} {{#{k}}}\n\n" + table(["document", "id", "results", "quantities"], rows)
    write("fer/index.qmd", fm({"title": "fer view"}) + "::: {.page-article .fer}\n" + body + ":::\n")
    print(f"generate_fer_site: {n} fer pages + landing -> fer/")

if __name__ == "__main__":
    main()
