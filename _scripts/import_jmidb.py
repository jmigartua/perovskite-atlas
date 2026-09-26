"""Import the perovskite subset of publications from jmi-db (thermomat knowledge base) as atlas records,
and copy the local article PDFs/Markdown from the old MatDB repository into sources/articles/.

Run once (Phase 0); re-running overwrites the same records. Selection is explicit (SELECT below), so
curation stays visible in code. Records are created with status `published`, visibility `public`.
"""
from __future__ import annotations
import re, shutil, pathlib, yaml
from common import ROOT

JMI = pathlib.Path("/Users/User/Desktop/2026/20260200/20260213_thermomat_db_project/jmi-db/publications")
OLD = pathlib.Path("/Users/User/Desktop/2026/20260100/20260122_JMI_database_project")

SELECT = """
2002_004 2003_001 2003_002 2003_008 2003_010 2004_001 2004_004 2007_003 2007_004 2008_006 2008_007 2008_010 2008_011
2009_007 2009_010 2009_011 2009_012 2009_014 2009_015 2010_005 2010_006 2010_010 2010_011 2011_007 2012_007 2012_008
2012_011 2012_012 2012_014 2012_017 2013_004 2013_007 2013_010 2013_011 2015_007 2015_008 2015_013 2015_014 2016_007
2016_009 2016_012 2019_006 2019_017 2022_011 2023_018
""".split()

FM = re.compile(r"^---\n(.*?)\n---", re.S)

def doi_slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", doi.lower()).strip("-")

def local_files(doi: str) -> dict:
    """Find PDF/MD in the old repo via the definitive inventory report (DOI -> file)."""
    rep = (OLD / "reports/definitive_inventory_report.md").read_text()
    out = {}
    for block in rep.split("\n---\n"):
        if doi and doi.lower() in block.lower():
            m = re.search(r"\[(.+?\.pdf)\]\(\./(all_articles_[a-z_]+)/", block)
            if m:
                src = OLD / m.group(2) / m.group(1)
                if src.exists():
                    out["pdf"] = src; md = src.with_suffix(".md")
                    if md.exists(): out["md"] = md
                break
    return out

def main():
    n = 0
    for d in sorted(JMI.iterdir()):
        if not any(d.name.startswith(s) for s in SELECT):
            continue
        src = yaml.safe_load(FM.match((d / "index.qmd").read_text()).group(1))
        doi = src.get("doi")
        slug = doi_slug(doi) if doi else re.sub(r"[^a-z0-9]+", "-", d.name.lower()).strip("-")
        rid = f"doc:{slug}"
        rec = {
            "id": rid, "schema_version": "0.1", "status": "published", "visibility": "public",
            "title": str(src.get("title", "")).replace("\textit", "\\textit"),
            "year": int(src["year"]), "entry_type": src.get("entry_type", "journal-article"),
            "journal_name": src.get("journal"), "volume": src.get("volume"), "issue": src.get("issue"), "pages": src.get("pages"),
            "doi": doi, "authors": src.get("authors", []),
            "author_ids": ["per:igartua-jm"] if "igartua-jm" in (src.get("thermomat_authors") or []) else [],
            "urls": {k: v for k, v in {"doi": src.get("url_doi"), "publisher": src.get("url_publisher"), "pdf": src.get("url_pdf")}.items() if v},
            "provenance": {"source": "jmi-db (thermomat knowledge base) publication record", "jmi_db_slug": d.name,
                            "openalex_id": ((src.get("extensions") or {}).get("provenance") or {}).get("openalex_id")},
            "evidence": [{"doc": rid, "page": 1, "note": "self; bibliographic record"}],
        }
        rec = {k: v for k, v in rec.items() if v is not None}
        rec["provenance"] = {k: v for k, v in rec["provenance"].items() if v is not None}
        files = local_files(doi) if doi else {}
        if files:
            dest = ROOT / "sources/articles"; dest.mkdir(parents=True, exist_ok=True)
            for kind, f in files.items():
                shutil.copy2(f, dest / f"{slug}{f.suffix}")
            rec["pdf"] = f"sources/articles/{slug}.pdf"
            if "md" in files: rec["md"] = f"sources/articles/{slug}.md"
        out = ROOT / "publications" / slug / "index.qmd"
        out.parent.mkdir(parents=True, exist_ok=True)
        body = ""
        if out.exists():
            old = out.read_text(); mm = FM.match(old)
            body = old[mm.end():] if mm else ""
        if "{{< include" not in body:
            body = f"\n{{{{< include /_gen/includes/publications/{slug}.md >}}}}\n"
        out.write_text("---\n" + yaml.safe_dump(rec, sort_keys=False, allow_unicode=True) + "---\n" + body)
        n += 1
    print(f"import_jmidb: {n} publication record(s)")

if __name__ == "__main__":
    main()
