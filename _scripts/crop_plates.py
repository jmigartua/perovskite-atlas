"""Stage B: crop every figure and table out of the theses and articles into plates/ and tables/.

Sources: the Mathpix OCR Markdown next to each PDF. Every image line carries the crop box in its URL
(`cropped/<id>-<page>.jpg?height=H&width=W&top_left_y=Y&top_left_x=X`, page index 1-based). Those pixel
coordinates are in a space about 1.23 times smaller than our 300 dpi page render (measured on all four theses and the
articles; see OCR_SCALE_POS / OCR_SCALE_SIZE), so the first crops of 2026-09-26 were cut short at the right and bottom.
`--refit` rescales every box and adjusts it to the ink extent (small gaps tolerated, so tick labels and axis titles
are kept, captions and text are not); the original OCR box is kept as `bbox_ocr` in the evidence. We render the PDF page locally with pdftoppm and cut the same box, so nothing
depends on the Mathpix CDN. Captions are taken from the "Figure N.N:" / "Fig. N." / "Figura N.N" line
that follows (or precedes) the image; pipe tables that follow a "Table N.N:" / "Tabla" caption become CSV.

Existing plate.yaml / table.yaml records are kept; only a missing `image` is filled in.

Usage: python3 _scripts/crop_plates.py [--docs thesis-03,10.1107-...] [--dpi 300] [--dry-run]
"""
from __future__ import annotations
import argparse, csv, io, re, subprocess, sys, pathlib, yaml
from PIL import Image
from common import ROOT

PAGES = ROOT / "_data/computed/pages"
IMG = re.compile(r"!\[[^\]]*\]\(https://cdn\.mathpix\.com/cropped/([0-9a-f-]+)-(\d+)\.jpg\?height=(\d+)&width=(\d+)&top_left_y=(\d+)&top_left_x=(\d+)\)")
FIG = re.compile(r"^(?:Figure|Fig\.|Figura|FIGURE)\s*([0-9]+(?:\.[0-9]+)?)[.:]?\s*(.*)$")
TAB = re.compile(r"^(?:Table|Tabla|TABLE)\s*([0-9]+(?:\.[0-9]+)?)[.:]?\s*(.*)$")
MIN_W, MIN_H, MAX_OUT_W = 300, 150, 1800
OCR_SCALE_POS, OCR_SCALE_SIZE = 1.23, 1.20   # Mathpix crop coordinates -> 300 dpi page pixels (empirical, all four theses and the articles)

KINDS = [
    ("rietveld-plot", r"rietveld|observed.*calculated|calculated.*observed|experimental \(symbols\)|difference"),
    ("amplitude-vs-t", r"amplitude"),
    ("cell-vs-t", r"cell parameter|lattice parameter|cell-volume|cell volume|temperature evolution|evolución|parámetros de (la )?celda"),
    ("group-subgroup-tree", r"group.subgroup|subgroup|árbol"),
    ("mode-drawing", r"\bmode\b.*(displacement|polarization|scheme|representation)|distortion mode"),
    ("structure-drawing", r"structure|octahedr|view of|projection|estructura|octaedr"),
    ("raman", r"raman"),
    ("magnetization", r"magneti|susceptib"),
    ("dsc", r"\bdsc\b|calorimet"),
    ("tem", r"\btem\b|electron"),
    ("pattern", r"diffraction pattern|diffractogram|difractograma|xrd|npd|reflection|reflexi"),
    ("phase-diagram", r"phase diagram"),
]

def kind_of(caption: str) -> str:
    c = caption.lower()
    for k, pat in KINDS:
        if re.search(pat, c):
            return k
    return "other"

SUBS = str.maketrans("0123456789+-=()x", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₓ")
SUPS = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
GREEK = {"Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
         "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ", "nu": "ν",
         "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
         "AA": "Å", "circ": "°", "pm": "±", "times": "×", "cdot": "·", "leftarrow": "←", "rightarrow": "→", "leftrightarrow": "↔", "to": "→",
         "angle": "∠", "approx": "≈", "sim": "~", "le": "≤", "ge": "≥", "neq": "≠", "infty": "∞", "prime": "′", "ldots": "…", "dots": "…", "%": "%", "&": "&", "_": "_", "#": "#"}
WRAP = re.compile(r"\\(?:mathrm|operatorname|text|textit|textbf|mathbf|mathit|bf|it|rm|boldsymbol|mathcal)\s*\{([^{}]*)\}")

def plain_caption(s: str) -> str:
    """Unicode rendering of a LaTeX caption, for search indexes and page titles."""
    s = s.replace("$", "")
    for _ in range(3):
        s = WRAP.sub(r"\1", s)
    s = re.sub(r"\\(?:overline|bar)\s*\{?(\d)\}?", "\\1\u0304", s)
    s = re.sub(r"\\(?:left|right|,|;|!|quad|qquad)\b", " ", s)
    s = re.sub(r"\\([A-Za-z]+|[%&_#])", lambda m: GREEK.get(m.group(1), m.group(1)), s)
    s = re.sub(r"\^\{([^{}]*)\}", lambda m: m.group(1).translate(SUPS) if re.fullmatch(r"[0-9+\-=()n]+", m.group(1)) else "^" + m.group(1), s)
    s = re.sub(r"\^([0-9+\-])", lambda m: m.group(1).translate(SUPS), s)
    s = re.sub(r"_\{([^{}]*)\}", lambda m: m.group(1).translate(SUBS) if re.fullmatch(r"[0-9+\-=()x.]+", m.group(1)) else "_" + m.group(1), s)
    s = re.sub(r"_([0-9])", lambda m: m.group(1).translate(SUBS), s)
    s = re.sub(r"[{}]", "", s).replace("~", " ")
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def raw_caption(s: str) -> str:
    """Caption as written by the OCR, LaTeX kept for KaTeX; only whitespace and a few OCR tics normalised."""
    s = s.replace("\\mathrm{~K}", "\\mathrm{K}").replace("~", " ")
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()

def clean_caption(s: str) -> str:  # kept for callers; captions are stored raw
    return raw_caption(s)

def render_page(pdf: pathlib.Path, doc: str, page: int, dpi: int) -> pathlib.Path:
    out = PAGES / doc / f"{page:04d}.png"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png", "-singlefile", str(pdf), str(out.with_suffix(""))], check=True)
    return out

def fit_bbox(im, bbox, limit=700, pad=10, thresh=200, gap=32):
    """Expand a crop box outward from the page render to the ink extent. On each side the scan continues while
    the border line has ink; white runs shorter than `gap` px (tick labels, axis titles) are crossed, a longer
    white run (the space before a caption or text) stops it. At most `limit` px per side. Returns (x, y, w, h)."""
    g = im.convert("L"); W, H = g.size
    x0, y0, w, h = bbox; x1, y1 = x0 + w, y0 + h
    px = g.load()
    def col_ink(x, ya, yb): return any(px[x, y] < thresh for y in range(max(0, ya), min(H, yb)))
    def row_ink(y, xa, xb): return any(px[x, y] < thresh for x in range(max(0, xa), min(W, xb)))
    def scan(start, step, stop_at, has_ink):
        last = start; pos = start; white = 0; n = 0
        while 0 <= pos + step < stop_at if step > 0 else pos + step >= stop_at:
            pos += step; n += 1
            if n > limit: break
            if has_ink(pos): last = pos; white = 0
            else:
                white += 1
                if white > gap: break
        return last
    # trim inward first: a box starting in white space near a header or caption must not adopt it
    def trim(pos, step, stop, has_ink):
        n = 0
        while not has_ink(pos) and n < limit and (pos + step < stop if step > 0 else pos + step > stop): pos += step; n += 1
        return pos
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    x0 = trim(x0, +1, cx, lambda x: col_ink(x, y0, y1)); x1 = trim(x1 - 1, -1, cx, lambda x: col_ink(x, y0, y1)) + 1
    y0 = trim(y0, +1, cy, lambda y: row_ink(y, x0, x1)); y1 = trim(y1 - 1, -1, cy, lambda y: row_ink(y, x0, x1)) + 1
    x1 = scan(x1, +1, W - 1, lambda x: col_ink(x, y0, y1))
    x0 = scan(x0, -1, 0, lambda x: col_ink(x, y0, y1))
    y1 = scan(y1, +1, H - 1, lambda y: row_ink(y, x0, x1))
    y0 = scan(y0, -1, 0, lambda y: row_ink(y, x0, x1))
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad); x1 = min(W, x1 + pad + 1); y1 = min(H, y1 + pad + 1)
    return (x0, y0, x1 - x0, y1 - y0)

def crop(pdf, doc, page, bbox, dpi, dest: pathlib.Path):
    x, y, w, h = bbox
    im = Image.open(render_page(pdf, doc, page, dpi))
    W, H = im.size
    box = (max(0, x), max(0, y), min(W, x + w), min(H, y + h))
    if box[2] <= box[0] or box[3] <= box[1]:
        return False
    c = im.crop(box)
    if c.width > MAX_OUT_W:
        c = c.resize((MAX_OUT_W, round(c.height * MAX_OUT_W / c.width)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    c.save(dest, optimize=True)
    return True

def documents():
    docs = []
    for i in (1, 2, 3, 4):
        docs.append(dict(id=f"doc:thesis-0{i}", slug=f"thesis-0{i}", md=ROOT / f"sources/theses/thesis-0{i}.md", pdf=ROOT / f"sources/theses/thesis-0{i}.pdf", rights="own", reproduce="not-needed", status="thesis-only"))
    for md in sorted((ROOT / "sources/articles").glob("*.md")):
        pdf = md.with_suffix(".pdf")
        if pdf.exists():
            docs.append(dict(id=f"doc:{md.stem}", slug=md.stem, md=md, pdf=pdf, rights="publisher", reproduce="pending", status="published"))
    return docs

def dump(rec: dict, path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=1000))

def process(doc: dict, dpi: int, dry: bool) -> tuple[int, int]:
    lines = doc["md"].read_text().splitlines()
    n_pl = n_tb = 0
    used_ids: dict[str, int] = {}
    # ---- figures
    for i, line in enumerate(lines):
        m = IMG.search(line)
        if not m:
            continue
        page = int(m.group(2)); h, w, y, x = (int(m.group(k)) for k in (3, 4, 5, 6))
        caption = number = None
        window = [(j, lines[j].strip()) for j in range(i + 1, min(i + 8, len(lines))) if lines[j].strip()][:4]
        window += [(j, lines[j].strip()) for j in range(max(0, i - 3), i) if lines[j].strip()]
        for j, t in window:
            fm = FIG.match(t)
            if fm:
                number, caption = fm.group(1), clean_caption(fm.group(2)); break
        if number is None and (w < MIN_W or h < MIN_H):
            continue
        base = number if number else f"p{page}-{i + 1}"
        used_ids[base] = used_ids.get(base, 0) + 1
        n = base if used_ids[base] == 1 else f"{base}-{used_ids[base]}"
        d = ROOT / "plates" / doc["slug"] / n
        ypath = d / "plate.yaml"
        if dry:
            n_pl += 1; continue
        ok = crop(doc["pdf"], doc["slug"], page, (x, y, w, h), dpi, d / "plate.png")
        if not ok:
            continue
        if ypath.exists():
            rec = yaml.safe_load(ypath.read_text())
            changed = False
            if not rec.get("image"): rec["image"] = "plate.png"; changed = True
            for e in rec.get("evidence", []):
                if e.get("doc") == doc["id"] and not e.get("bbox"):
                    e["bbox"] = [x, y, w, h]; e.setdefault("page", page); changed = True
            if changed: dump(rec, ypath)
        else:
            rec = {
                "id": f"plt:{doc['slug']}.{n}", "schema_version": "0.1", "status": doc["status"],
                "visibility": "public" if doc["rights"] == "own" else "review",
                "doc": doc["id"], "number": n, "caption": caption or "(no caption found; uncaptioned image)", "caption_plain": plain_caption(caption) if caption else "(no caption found; uncaptioned image)",
                "kind": kind_of(caption or ""), "image": "plate.png", "rights": doc["rights"], "reproduce": doc["reproduce"],
                "notes": "auto-cropped from the OCR Markdown crop box (stage B); materials and kind to be reviewed in Phase 1",
                "evidence": [{"doc": doc["id"], "page": page, "md_line": i + 1, **({"figure": number} if number else {}), "bbox": [x, y, w, h], "status": doc["status"]}],
            }
            dump(rec, ypath)
        n_pl += 1
    # ---- tables
    used_t: dict[str, int] = {}
    for i, line in enumerate(lines):
        tm = TAB.match(line.strip())
        if not tm:
            continue
        # pipe rows within the next 3 lines
        j = i + 1
        while j < len(lines) and j <= i + 3 and not lines[j].lstrip().startswith("|"):
            j += 1
        if j >= len(lines) or not lines[j].lstrip().startswith("|"):
            continue
        rows = []
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                rows.append(cells)
            j += 1
        if len(rows) < 2:
            continue
        base = tm.group(1); used_t[base] = used_t.get(base, 0) + 1
        n = base if used_t[base] == 1 else f"{base}-{used_t[base]}"
        d = ROOT / "tables" / doc["slug"] / n
        if dry:
            n_tb += 1; continue
        if (d / "table.yaml").exists():
            n_tb += 1; continue
        d.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO(); wr = csv.writer(buf)
        width = max(len(r) for r in rows)
        for r in rows: wr.writerow(r + [""] * (width - len(r)))
        (d / "table.csv").write_text(buf.getvalue())
        dump({
            "id": f"tbl:{doc['slug']}.{n}", "schema_version": "0.1", "status": doc["status"], "visibility": "public",
            "doc": doc["id"], "number": n, "caption": raw_caption(tm.group(2)) or "(no caption text)", "caption_plain": plain_caption(tm.group(2)) or "(no caption text)", "csv": "table.csv",
            "notes": "auto-extracted from the OCR Markdown pipe table (stage B); cells unreviewed",
            "evidence": [{"doc": doc["id"], "md_line": i + 1, "table": n, "status": doc["status"]}],
        }, d / "table.yaml")
        n_tb += 1
    return n_pl, n_tb

def refit(docs_sel, dpi, dry):
    """Re-fit every existing plate crop whose OCR box cut the figure; updates plate.png and the evidence bbox."""
    n_changed = 0; n_seen = 0
    for doc in documents():
        if docs_sel and doc["slug"] not in docs_sel: continue
        for ypath in sorted((ROOT / "plates" / doc["slug"]).glob("*/plate.yaml")):
            rec = yaml.safe_load(ypath.read_text())
            ev = next((e for e in rec.get("evidence", []) if e.get("bbox") and e.get("page")), None)
            if not ev or not rec.get("image"): continue
            n_seen += 1
            page = ev["page"]; ox, oy, ow, oh = ev.get("bbox_ocr") or ev["bbox"]
            # Mathpix boxes are in a ~1.23x smaller coordinate space than the 300 dpi render (measured on all documents)
            x, y, w, h = int(ox * OCR_SCALE_POS), int(oy * OCR_SCALE_POS), int(ow * OCR_SCALE_SIZE), int(oh * OCR_SCALE_SIZE)
            im = Image.open(render_page(doc["pdf"], doc["slug"], page, dpi))
            nb = fit_bbox(im, (x, y, w, h), limit=90, gap=14)
            if list(nb) == list(ev["bbox"]): continue
            w, h = ev["bbox"][2], ev["bbox"][3]
            n_changed += 1
            print(f"  {rec['id']}: {w}x{h} -> {nb[2]}x{nb[3]}")
            if dry: continue
            crop(doc["pdf"], doc["slug"], page, nb, dpi, ypath.parent / rec["image"])
            ev.setdefault("bbox_ocr", [ox, oy, ow, oh]); ev["bbox"] = list(nb); ev["note"] = "crop box: OCR box scaled to the 300 dpi page and fitted to the ink extent"
            dump(rec, ypath)
    print(f"refit: {n_changed} of {n_seen} plates re-cropped{' (dry run)' if dry else ''}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--docs"); ap.add_argument("--dpi", type=int, default=300); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--refit", action="store_true")
    a = ap.parse_args()
    if a.refit:
        refit(set(a.docs.split(",")) if a.docs else None, a.dpi, a.dry_run); return
    sel = set(a.docs.split(",")) if a.docs else None
    tot_p = tot_t = 0
    for doc in documents():
        if sel and doc["slug"] not in sel:
            continue
        p, t = process(doc, a.dpi, a.dry_run)
        tot_p += p; tot_t += t
        print(f"{doc['slug']}: {p} plates, {t} tables")
    print(f"crop_plates: {tot_p} plates, {tot_t} tables{' (dry run)' if a.dry_run else ''}")

if __name__ == "__main__":
    main()
