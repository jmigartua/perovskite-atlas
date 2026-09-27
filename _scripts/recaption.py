"""Re-read every plate and table caption from the OCR Markdown, keeping the LaTeX as written
(the site renders it with KaTeX), and store a plain-text variant for search and page titles.

Uses the evidence locator (doc, md_line, figure/table number) stored in each record. Records
whose caption was written by hand (no md_line, or number not found in the window) are left as they are.

Usage: python3 _scripts/recaption.py
"""
from __future__ import annotations
import pathlib, re, yaml
from common import ROOT
from crop_plates import FIG, TAB, plain_caption, raw_caption

def md_for(doc_id: str) -> pathlib.Path | None:
    slug = doc_id.split(":", 1)[1]
    for cand in (ROOT / f"sources/theses/{slug}.md", ROOT / f"sources/articles/{slug}.md"):
        if cand.exists():
            return cand
    return None

def find(lines, md_line: int, number: str, pat) -> str | None:
    lo, hi = max(0, md_line - 6), min(len(lines), md_line + 10)
    for j in range(lo, hi):
        m = pat.match(lines[j].strip())
        if m and m.group(1) == number:
            return m.group(2)
    return None

def main():
    n = 0; skipped = 0
    cache: dict[str, list[str]] = {}
    for kind, pat in (("plate", FIG), ("table", TAB)):
        for f in sorted((ROOT / ("plates" if kind == "plate" else "tables")).glob(f"*/*/{kind}.yaml")):
            rec = yaml.safe_load(f.read_text())
            ev = next((e for e in rec.get("evidence", []) if e.get("md_line")), None)
            if not ev:
                skipped += 1; continue
            md = md_for(rec["doc"])
            if not md:
                skipped += 1; continue
            if md.name not in cache:
                cache[md.name] = md.read_text().splitlines()
            raw = find(cache[md.name], ev["md_line"], rec["number"].split("-")[0], pat)
            if raw is None:
                skipped += 1; continue
            rec["caption"] = raw_caption(raw)
            rec["caption_plain"] = plain_caption(raw)
            f.write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=1000))
            n += 1
    print(f"recaption: {n} captions restored to LaTeX, {skipped} left as written")

if __name__ == "__main__":
    main()
