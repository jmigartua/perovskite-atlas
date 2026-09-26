"""Generate pages from records.

- yaml-kit records (series, structures, transitions, plates, tables) get a generated
  `index.qmd` next to them (gitignored).
- record `.qmd` pages (materials, theses, people, publications) are their own pages and end
  with `{{< include /_gen/includes/<kind>/<slug>.md >}}`, which this script writes.
- listing pages `<dir>/index.qmd` are generated (gitignored).
- the home page includes `_gen/includes/home.md` (counts, composition grid).

Records with `visibility: hidden` are never written; `review` only when ATLAS_REVIEW=1.
"""
from __future__ import annotations
import csv, os, re, pathlib, yaml
from collections import defaultdict
from common import ROOT, iter_records

REVIEW = os.environ.get("ATLAS_REVIEW") == "1"

# ----------------------------------------------------------------- helpers
def sub(formula: str) -> str:
    """SrNdZnRuO6 -> SrNdZnRuO<sub>6</sub>; Sr2Cd0.5Ca0.5WO6 handled."""
    return re.sub(r"(\d+(?:\.\d+)?)", r"<sub>\1</sub>", formula or "")

def sg(hm: str) -> str:
    """P2_1/n -> P2<sub>1</sub>/n ; Fm-3m -> overline 3."""
    s = re.sub(r"_(\d)", r"<sub>\1</sub>", hm or "")
    s = re.sub(r"-(\d)", r"<span style=\"text-decoration:overline\">\1</span>", s)
    return s

def slug_of(rid: str) -> str:
    return rid.split(":", 1)[1]

def fm(d: dict) -> str:
    return "---\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True) + "---\n\n"

def write(rel: str, text: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)

def visible(rec: dict) -> bool:
    v = rec.get("visibility", "public")
    return v == "public" or (v == "review" and REVIEW)

def ev_line(e: dict) -> str:
    parts = [f"[{e['doc']}]({url.get(e['doc'], '#')})"]
    if e.get("table"): parts.append(f"table {e['table']}")
    if e.get("figure"): parts.append(f"figure {e['figure']}")
    if e.get("section"): parts.append(f"§ {e['section']}")
    if e.get("page"): parts.append(f"page {e['page']}")
    if e.get("md_line"): parts.append(f"OCR line {e['md_line']}")
    if e.get("cell"): parts.append("cell " + ", ".join(f"{k} = {v}" for k, v in e["cell"].items()))
    if e.get("status"): parts.append(f"*{e['status']}*")
    if e.get("note"): parts.append(e["note"])
    return " · ".join(parts)

def evidence_block(rec: dict) -> str:
    return "\n### Evidence\n\n" + "\n".join("- " + ev_line(e) for e in rec.get("evidence", [])) + "\n"

def status_line(rec: dict) -> str:
    return f"<p class='meta'>status <b>{rec.get('status','')}</b> · visibility <b>{rec.get('visibility','')}</b> · id <code>{rec['id']}</code></p>\n\n"

def table(headers, rows) -> str:
    if not rows:
        return "*None yet.*\n\n"
    out = "| " + " | ".join(headers) + " |\n|" + "---|" * len(headers) + "\n"
    for r in rows:
        out += "| " + " | ".join(str(c) if c is not None else "" for c in r) + " |\n"
    return out + "\n"

def article(title: str, body: str) -> str:
    plain = re.sub(r"<[^>]+>", "", title)
    return fm({"title": title, "pagetitle": plain}) + "::: {.page-article}\n" + body + "\n:::\n"

# ----------------------------------------------------------------- load
by_kind: dict[str, list[dict]] = defaultdict(list)
by_id: dict[str, dict] = {}
for kind, path, rec in iter_records():
    if not isinstance(rec, dict) or not rec.get("id"):
        continue
    rec = dict(rec); rec["_kind"] = kind; rec["_path"] = path
    by_kind[kind].append(rec); by_id[rec["id"]] = rec

url: dict[str, str] = {}
for rid, rec in by_id.items():
    p = rec["_path"]; rel = p.parent.relative_to(ROOT)
    url[rid] = f"/{rel}/" if p.name in ("structure.yaml", "plate.yaml", "table.yaml", "index.qmd") else f"/{rel}/{p.stem}/"

def L(rid: str, text: str | None = None) -> str:
    rec = by_id.get(rid)
    label = text or (rec.get("title") if rec else None) or slug_of(rid)
    return f"[{label}]({url.get(rid, '#')})"

def doc_label(did: str) -> str:
    d = by_id.get(did)
    if not d: return slug_of(did)
    if d["_kind"] == "thesis":
        a = by_id.get(d.get("author", ""), {}); surname = (a.get("name", "") or "").split()[-2] if a.get("name") and len(a["name"].split()) > 2 else (a.get("name", "") or "").split()[-1] if a.get("name") else slug_of(d["author"])
        return f"Thesis {slug_of(did)[-1]} · {surname} {d['year']}"
    au = d.get("authors") or []
    first = au[0].split()[-1] if au else slug_of(did)
    return f"{first}{' et al.' if len(au) > 1 else ''} {d.get('year', '')}"

def DL(did: str) -> str:
    return L(did, doc_label(did))

def mat_label(mid: str) -> str:
    m = by_id.get(mid)
    return L(mid, sub(m["formula"]) if m else slug_of(mid))

def T(r): return r["conditions"]["temperature_k"]

structures_of = defaultdict(list); transitions_of = defaultdict(list); plates_of = defaultdict(list)
modes_of: dict[str, dict] = {}; geometry_of: dict[str, dict] = {}; refinement_of: dict[str, dict] = {}
for r in by_kind["structure"]:
    if visible(r): structures_of[r["material"]].append(r)
for r in by_kind["transition"]:
    if visible(r): transitions_of[r["material"]].append(r)
for r in by_kind["plate"]:
    if visible(r):
        for m in r.get("materials", []): plates_of[m].append(r)
for r in by_kind["modes"]: modes_of[r["structure"]] = r
for r in by_kind["geometry"]: geometry_of[r["structure"]] = r
for r in by_kind["refinement"]: refinement_of[r["structure"]] = r
vis = lambda k: [r for r in by_kind[k] if visible(r)]

# ----------------------------------------------------------------- structures
for r in vis("structure"):
    m = by_id.get(r["material"]); cell = r["cell"]; s = r["space_group"]
    title = f"{sub(m['formula']) if m else slug_of(r['material'])} · {sg(s['hm'])} · {T(r):g} K"
    body = status_line(r)
    body += f"Material {mat_label(r['material'])} · space group {sg(s['hm'])} (No. {s['number']}{', ' + s['setting'] if s.get('setting') else ''}) · {r.get('phase_label','')} · {T(r):g} K\n\n"
    body += "### Cell\n\n" + table(["a (Å)", "b (Å)", "c (Å)", "α (°)", "β (°)", "γ (°)", "V (Å³)"],
                                   [[cell["a"], cell["b"], cell["c"], cell["alpha"], cell["beta"], cell["gamma"], cell.get("volume", "")]])
    body += "### Atoms\n\n" + table(["label", "element", "Wyckoff", "x", "y", "z", "occ.", "B<sub>iso</sub> (Å²)"],
                                    [[a["label"], a["element"], a["wyckoff"], a["x"], a["y"], a["z"], a.get("occupancy", "1"), str(a.get("b_iso", "")) + (" (fixed)" if "b_iso" in a.get("fixed", []) else "")] for a in r["atoms"]])
    body += f"CIF: {r.get('cif_origin','absent')}" + (f" · [{r['cif']}]({r['cif']})" if r.get("cif") else "") + "\n\n"
    ref = refinement_of.get(r["id"])
    if ref:
        body += "### Refinement\n\n" + table(["software", "method", "variant", "R<sub>p</sub>", "R<sub>wp</sub>", "R<sub>exp</sub>", "R<sub>Bragg</sub>", "χ²", "parameters"],
                                             [[ref.get("software"), ref.get("method"), ref.get("variant", ""), ref.get("r_p"), ref.get("r_wp"), ref.get("r_exp"), ref.get("r_bragg"), ref.get("chi2"), ref.get("refined_parameters", "")]])
        if ref.get("notes"): body += ref["notes"] + "\n\n"
    md = modes_of.get(r["id"])
    if md:
        body += f"### Symmetry-mode decomposition\n\nParent {sg(md['parent_space_group'])}" + (f" · transformation `{md['transformation']}`" if md.get("transformation") else "") + f" · {md['software']} · convention `{md['convention']}`" + (f" · {md['refinement_variant']}" if md.get("refinement_variant") else "") + "\n\n"
        body += table(["irrep", "k", "direction", "dim", "isotropy subgroup", "amplitude (Å)", "role", "physical meaning"],
                      [[("**" + i["label"] + "**") if i.get("primary") else i["label"], i.get("k_vector", ""), i.get("direction", ""), i.get("dimension", ""), sg(i.get("isotropy_subgroup", "")), i["amplitude"], "primary" if i.get("primary") else "", i.get("physical", "")] for i in md["irreps"]])
        if md.get("notes"): body += md["notes"] + "\n\n"
    g = geometry_of.get(r["id"])
    if g:
        body += "### Geometry (as reported)\n\n"
        if g.get("tilts"): body += "Tilt angles: " + ", ".join(f"{k} = {v}°" for k, v in g["tilts"].items()) + (f" · Glazer {g['glazer']}" if g.get("glazer") else "") + "\n\n"
        for name, o in g.get("octahedra", {}).items():
            body += f"**{sub(name)}** · V = {o.get('volume','')} Å³ · " + ", ".join(f"{k} {v} Å" for k, v in o.get("bonds", {}).items()) + f" · mean {o.get('average_bond','')} (predicted {o.get('predicted_bond','')})\n\n"
        if g.get("angles"): body += "Angles: " + ", ".join(f"{k} {v}°" for k, v in g["angles"].items()) + "\n\n"
        if g.get("bvs"): body += "Bond-valence sums: " + ", ".join(f"{k} {v}" for k, v in g["bvs"].items()) + "\n\n"
    trs = [t for t in transitions_of[r["material"]] if t.get("from_structure") == r["id"] or t.get("to_structure") == r["id"]]
    if trs:
        body += "### Transitions involving this phase\n\n" + "\n".join(f"- {L(t['id'], sg(t['from_space_group']) + ' → ' + sg(t['to_space_group']))} at {t['temperature_k']:g} K, {t['order']}" for t in trs) + "\n\n"
    if r.get("notes"): body += r["notes"] + "\n"
    body += evidence_block(r)
    write(f"structures/{slug_of(r['id'])}/index.qmd", article(title, body))

# ----------------------------------------------------------------- transitions
for t in vis("transition"):
    m = by_id.get(t["material"])
    title = f"{sub(m['formula']) if m else slug_of(t['material'])} · {sg(t['from_space_group'])} → {sg(t['to_space_group'])}"
    body = status_line(t) + f"Material {mat_label(t['material'])}\n\n"
    body += table(["from", "to", "T (K)", "order", "techniques", "primary irrep"],
                  [[sg(t["from_space_group"]), sg(t["to_space_group"]), t.get("temperature_k"), t.get("order"), ", ".join(t.get("techniques", [])), t.get("primary_irrep", "")]])
    for k in ("from_structure", "to_structure"):
        if t.get(k): body += f"{k.replace('_', ' ')}: {L(t[k])}\n\n"
    body += evidence_block(t)
    write(f"transitions/{slug_of(t['id'])}/index.qmd", article(title, body))

# ----------------------------------------------------------------- series
for s in vis("series"):
    rows = []
    for mid in s.get("members", []):
        m = by_id.get(mid)
        if not m or not visible(m): continue
        rt = sorted(structures_of[mid], key=lambda r: abs(T(r) - 300))
        rt_sg = sg(rt[0]["space_group"]["hm"]) if rt else ""
        seq = " → ".join(f"{sg(t['to_space_group'])} ({t['temperature_k']:g} K)" for t in sorted(transitions_of[mid], key=lambda t: t["temperature_k"]))
        md = modes_of.get(rt[0]["id"]) if rt else None
        prim = ", ".join(f"{i['label']} {i['amplitude']}" for i in md["irreps"] if i.get("primary")) if md else ""
        slots = next((x["slot_values"] for x in m.get("series", []) if x["id"] == s["id"]), {})
        rows.append([mat_label(mid), ", ".join(f"{k} = {v}" for k, v in slots.items()), rt_sg, seq, prim])
    body = status_line(s) + f"Template `{s['template']}` · slots " + "; ".join(f"{k} ∈ {{{', '.join(v)}}}" for k, v in s["slots"].items()) + f" · {s['structural_family']} · aristotype {sg(s['aristotype'])}\n\n"
    body += "### Members\n\n" + table(["material", "slots", "RT space group", "transitions", "primary irreps at RT (Å)"], rows)
    body += evidence_block(s)
    write(f"series/{slug_of(s['id'])}/index.qmd", article(s.get("title", s["template"]), body))

# ----------------------------------------------------------------- plates and tables
from PIL import Image
THUMBS = ROOT / "_data/computed/thumbs"
def thumb(p: dict) -> str | None:
    if not p.get("image"): return None
    src = p["_path"].parent / p["image"]
    if not src.exists(): return None
    out = THUMBS / slug_of(p["doc"]) / f"{p['number']}.png"
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        out.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src); im.thumbnail((360, 360)); im.save(out, optimize=True)
    return f"/_data/computed/thumbs/{slug_of(p['doc'])}/{p['number']}.png"

for p in vis("plate"):
    body = status_line(p) + (f"![{p['caption']}]({p['image']})\n\n" if p.get("image") else "*Image not yet cropped (Phase 1, stage B).*\n\n")
    body += f"**{p['caption']}**\n\n{DL(p['doc'])} · figure {p['number']} · kind `{p['kind']}` · rights `{p['rights']}` · reproduce `{p['reproduce']}`\n\n"
    if p.get("materials"): body += "Materials: " + ", ".join(mat_label(m) for m in p["materials"]) + "\n\n"
    if p.get("transitions"): body += "Transitions: " + ", ".join(L(t) for t in p["transitions"]) + "\n\n"
    if p.get("data"): body += f"Data behind this figure: [{p['data']}]({p['data']})\n\n"
    if p.get("notes"): body += p["notes"] + "\n\n"
    body += evidence_block(p)
    write(f"{p['_path'].parent.relative_to(ROOT)}/index.qmd", article(f"Figure {p['number']} · {slug_of(p['doc'])}", body))

for tb in vis("table"):
    body = status_line(tb) + f"**{tb['caption']}**\n\n{DL(tb['doc'])} · table {tb['number']}\n\n"
    csv_path = tb["_path"].parent / tb["csv"]
    if csv_path.exists():
        with csv_path.open() as f:
            rows = list(csv.reader(f))
        if rows: body += table(rows[0], rows[1:])
    if tb.get("extracted_into"): body += "Extracted into: " + ", ".join(L(x) for x in tb["extracted_into"]) + "\n\n"
    body += evidence_block(tb)
    write(f"{tb['_path'].parent.relative_to(ROOT)}/index.qmd", article(f"Table {tb['number']} · {slug_of(tb['doc'])}", body))

# ----------------------------------------------------------------- includes for record pages
for m in vis("material"):
    body = status_line(m)
    body += f"Formula {sub(m['formula'])} · {m['structural_family']} · {m['material_status']}" + (f" · B-site {m['b_site_order']}" if m.get("b_site_order") else "") + "\n\n"
    if m.get("series"): body += "Series: " + ", ".join(L(x["id"]) + " (" + ", ".join(f"{k} = {v}" for k, v in x["slot_values"].items()) + ")" for x in m["series"]) + "\n\n"
    if m.get("synthesis"):
        sy = m["synthesis"]; body += f"Synthesis: {sy.get('method','')}" + (f", from {', '.join(sy['precursors'])}" if sy.get("precursors") else "") + (f"; {sy['schedule']}" if sy.get("schedule") else "") + (f", {sy['atmosphere']}" if sy.get("atmosphere") else "") + "\n\n"
    trs = sorted(transitions_of[m["id"]], key=lambda t: t["temperature_k"])
    if trs:
        body += "### Phase sequence\n\n" + " → ".join([sg(trs[0]["from_space_group"])] + [f"{sg(t['to_space_group'])} at {t['temperature_k']:g} K ({t['order']})" for t in trs]) + "\n\n"
    sts = sorted(structures_of[m["id"]], key=T)
    body += "### Structures\n\n" + table(["T (K)", "space group", "a", "b", "c", "β", "R<sub>wp</sub>", "modes", "status"],
                                         [[f"{T(r):g}", L(r["id"], sg(r["space_group"]["hm"])), r["cell"]["a"], r["cell"]["b"], r["cell"]["c"], r["cell"]["beta"], (refinement_of.get(r["id"]) or {}).get("r_wp", ""), "yes" if r["id"] in modes_of else "", r["status"]] for r in sts])
    if trs: body += "### Transitions\n\n" + "\n".join(f"- {L(t['id'], sg(t['from_space_group']) + ' → ' + sg(t['to_space_group']))} at {t['temperature_k']:g} K, {t['order']}" for t in trs) + "\n\n"
    pls = plates_of[m["id"]]
    if pls: body += "### Figures\n\n" + "\n".join(f"- {L(p['id'], 'Figure ' + p['number'] + ' of ' + slug_of(p['doc']))}: {p['caption']}" for p in pls) + "\n\n"
    body += evidence_block(m)
    write(f"_gen/includes/materials/{slug_of(m['id'])}.md", body)

for th in vis("thesis"):
    body = status_line(th) + f"{L(th['author'])}, {th['year']}" + (f" · supervisor {L(th['supervisor'])}" if th.get("supervisor") else "") + f" · {th.get('institution','')} · language {th.get('thesis_language','')}\n\n"
    if th.get("files"): body += "Files: " + ", ".join(f"`{v}`" for v in th["files"].values()) + "\n\n"
    if th.get("chapters"):
        body += "### Chapters\n\n" + table(["chapter", "title", "materials", "published as"],
                                           [[c["n"], c["title"], ", ".join(mat_label(x) for x in c.get("materials", [])), ", ".join(L(x) for x in c.get("published_as", []))] for c in th["chapters"]])
    pls = [p for p in vis("plate") if p["doc"] == th["id"]]
    tbs = [t for t in vis("table") if t["doc"] == th["id"]]
    if pls: body += "### Figures\n\n" + "\n".join(f"- {L(p['id'], 'Figure ' + p['number'])}: {p['caption']}" for p in pls) + "\n\n"
    if tbs: body += "### Tables\n\n" + "\n".join(f"- {L(t['id'], 'Table ' + t['number'])}: {t['caption']}" for t in tbs) + "\n\n"
    write(f"_gen/includes/theses/{slug_of(th['id'])}.md", body)

for pe in vis("person"):
    body = status_line(pe)
    if pe.get("orcid"): body += f"ORCID [{pe['orcid']}](https://orcid.org/{pe['orcid']})\n\n"
    if pe.get("roles"): body += "Roles: " + "; ".join(f"{r['role']} {r.get('from','')}–{r.get('to','')}" for r in pe["roles"]) + "\n\n"
    ths = [t for t in vis("thesis") if t.get("author") == pe["id"]]
    if ths: body += "### Thesis\n\n" + "\n".join(f"- {L(t['id'])} ({t['year']})" for t in ths) + "\n\n"
    variants = set(pe.get("name_variants", [])) | {pe["name"]}
    pubs = [p for p in vis("publication") if pe["id"] in p.get("author_ids", []) or variants & set(p.get("authors", []))]
    if pubs: body += "### Publications in the atlas\n\n" + "\n".join(f"- {L(p['id'])} ({p['year']})" for p in sorted(pubs, key=lambda p: p['year'])) + "\n\n"
    write(f"_gen/includes/people/{slug_of(pe['id'])}.md", body)

for pu in vis("publication"):
    body = status_line(pu) + f"{', '.join(pu.get('authors', []))} · *{pu.get('journal_name') or ''}* {pu.get('volume') or ''}" + (f" ({pu.get('issue')})" if pu.get('issue') else "") + (f", {pu['pages']}" if pu.get("pages") else "") + f" ({pu['year']})\n\n"
    if pu.get("doi"): body += f"DOI [{pu['doi']}](https://doi.org/{pu['doi']})\n\n"
    if pu.get("pdf"): body += f"Local file: `{pu['pdf']}`\n\n"
    mats = sorted({m for th in vis("thesis") for c in th.get("chapters", []) if pu["id"] in c.get("published_as", []) for m in c.get("materials", [])})
    if mats: body += "Materials: " + ", ".join(mat_label(m) for m in mats) + "\n\n"
    write(f"_gen/includes/publications/{slug_of(pu['id'])}.md", body)

# ----------------------------------------------------------------- listings
def listing(rel, title, intro, body):
    write(rel, article(title, intro + "\n\n" + body))

listing("series/index.qmd", "Series", "Parametric families with a variable cation slot. Each series page compares its members: room-temperature symmetry, transition sequence and primary-mode amplitudes.",
        table(["series", "template", "family", "members"], [[L(s["id"]), f"`{s['template']}`", s["structural_family"], len(s.get("members", []))] for s in vis("series")]))
listing("materials/index.qmd", "Materials", "One record per composition. Solid solutions are series; each measured composition is its own material.",
        table(["formula", "family", "status", "structures", "transitions", "series"], [[mat_label(m["id"]), m["structural_family"], m["material_status"], len(structures_of[m["id"]]), len(transitions_of[m["id"]]), ", ".join(L(x["id"]) for x in m.get("series", []))] for m in sorted(vis("material"), key=lambda m: m["formula"])]))
listing("structures/index.qmd", "Structures", "A structure is one phase of one material at stated conditions, with cell, atoms, CIF, refinement and, when performed, the symmetry-mode decomposition.",
        table(["material", "space group", "T (K)", "a", "b", "c", "modes", "status"], [[mat_label(r["material"]), L(r["id"], sg(r["space_group"]["hm"])), f"{T(r):g}", r["cell"]["a"], r["cell"]["b"], r["cell"]["c"], "yes" if r["id"] in modes_of else "", r["status"]] for r in sorted(vis("structure"), key=lambda r: (r["material"], T(r)))]))
listing("transitions/index.qmd", "Transitions", "Every phase transition in the corpus, with temperature, order and the technique that evidenced it.",
        table(["material", "from", "to", "T (K)", "order", "techniques", "status"], [[mat_label(t["material"]), sg(t["from_space_group"]), L(t["id"], sg(t["to_space_group"])), t["temperature_k"], t["order"], ", ".join(t.get("techniques", [])), t["status"]] for t in sorted(vis("transition"), key=lambda t: (t["material"], t["temperature_k"]))]))
irrep_rows = defaultdict(list); mode_rows = []
for md in by_kind["modes"]:
    st = by_id.get(md["structure"])
    if not st or not visible(st): continue
    label = sub(by_id[st["material"]]["formula"]) + " " + sg(st["space_group"]["hm"]) + f" {T(st):g} K"
    mode_rows.append([L(st["id"], label), sg(md["parent_space_group"]), ", ".join(f"{i['label']} {i['amplitude']}" for i in md["irreps"] if i.get("primary")), md["software"], md["convention"]])
    for i in md["irreps"]:
        irrep_rows[i["label"]].append([L(st["id"], label), sg(md["parent_space_group"]), i["amplitude"], "primary" if i.get("primary") else "", md["convention"]])
modes_body = table(["structure", "parent", "primary irreps (Å)", "software", "convention"], mode_rows)
for lab in sorted(irrep_rows):
    modes_body += f"### {lab}\n\n" + table(["structure", "parent", "amplitude (Å)", "role", "convention"], irrep_rows[lab])
listing("modes/index.qmd", "Modes", "Symmetry-mode decompositions across the corpus. Amplitudes are comparable only within one normalization convention.", modes_body)
plates_body = ""
docs_order = [d["id"] for d in sorted(vis("thesis"), key=lambda t: t["year"])] + [d["id"] for d in sorted(vis("publication"), key=lambda p: p["year"])]
for did in docs_order:
    ps = [p for p in vis("plate") if p["doc"] == did]
    if not ps: continue
    plates_body += f"### {doc_label(did)}\n\n<p class='meta'>{L(did)} · {len(ps)} figures</p>\n\n<div class='gallery'>\n"
    for p in sorted(ps, key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"[.\-]", p["number"].lstrip("p"))]):
        th = thumb(p)
        cap = p["caption"][:140] + ("…" if len(p["caption"]) > 140 else "")
        plates_body += f"<a class='tile' href='{url[p['id']]}'>" + (f"<img src='{th}' alt='' loading='lazy'>" if th else "<span class='noimg'>no image</span>") + f"<span class='tile-n'>Figure {p['number']} · {p['kind']}</span><span class='tile-c'>{cap}</span></a>\n"
    plates_body += "</div>\n\n"
listing("plates/index.qmd", "Plates", "Every figure and table from the theses and articles, cropped locally, captioned, typed and linked. Publisher figures are held for reproduction from data.", plates_body)
listing("publications/index.qmd", "Publications", "Articles and proceedings on perovskite-type oxides, harvested from ORCID/OpenAlex and curated. Each links to the materials and structures extracted from it.",
        table(["year", "title", "journal"], [[p["year"], L(p["id"]), p.get("journal_name") or ""] for p in sorted(vis("publication"), key=lambda p: (-p["year"], str(p.get("title", ""))))]))
listing("theses/index.qmd", "Theses", "The four doctoral theses behind the atlas. Each thesis page maps chapters to materials, figures, tables and the papers they became.",
        table(["year", "author", "title", "language"], [[t["year"], L(t["author"]), L(t["id"]), t.get("thesis_language", "")] for t in sorted(vis("thesis"), key=lambda t: t["year"])]))
listing("people/index.qmd", "People", "Authors, students and collaborators.",
        table(["name", "roles"], [[L(p["id"], p["name"]), "; ".join(f"{r['role']} {r.get('from','')}–{r.get('to','')}" for r in p.get("roles", []))] for p in sorted(vis("person"), key=lambda p: p["name"])]))

# ----------------------------------------------------------------- home include
n_modes = len([m for m in by_kind["modes"] if by_id.get(m["structure"]) and visible(by_id[m["structure"]])])
tiles = [("series", len(vis("series"))), ("materials", len(vis("material"))), ("structures", len(vis("structure"))), ("transitions", len(vis("transition"))),
         ("mode decompositions", n_modes), ("plates", len(vis("plate"))), ("tables", len(vis("table"))), ("publications", len(vis("publication"))), ("theses", len(vis("thesis")))]
home = "<div class='counts'>" + "".join(f"<div><b>{v}</b><span>{k}</span></div>" for k, v in tiles) + "</div>\n\n"
grid = defaultdict(lambda: defaultdict(list)); Bs = set(); Bps = set()
for m in vis("material"):
    B = (m["sites"].get("B") or ["—"])[0]; Bp = (m["sites"].get("Bp") or ["—"])[0]
    Bs.add(B); Bps.add(Bp)
    grid[Bp][B].append(L(m["id"], "".join(m["sites"].get("A", [])) or m["formula"]))
if Bs:
    cols = sorted(Bs)
    home += "### Composition grid\n\nRows: B′ cation. Columns: B cation. Cells: A-site cations of the materials studied. Grows as materials are entered.\n\n" + table(["B′ \\ B"] + cols, [[bp] + [", ".join(grid[bp].get(b, [])) for b in cols] for bp in sorted(Bps)])
write("_gen/includes/home.md", home)
print("generate: " + ", ".join(f"{v} {k}" for k, v in tiles))
