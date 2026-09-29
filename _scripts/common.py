"""Shared helpers: record discovery, front-matter loading, id index."""
from __future__ import annotations
import pathlib, re, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD_DIRS = {
    "series": "series", "material": "materials", "sample": "samples", "dataset": "datasets",
    "structure": "structures", "transition": "transitions", "magnetic": "magnetic", "finding": "findings",
    "plate": "plates", "table": "tables", "publication": "publications", "thesis": "theses",
    "person": "people", "instrument": "instruments", "curve": "curves",
}
QMD_KINDS = {"material", "publication", "thesis", "person"}
KIT_FILES = {"modes": "modes.yaml", "refinement": "refinement.yaml", "geometry": "geometry.yaml"}

FM = re.compile(r"^---\n(.*?)\n---", re.S)

def load_record(path: pathlib.Path) -> dict:
    text = path.read_text()
    if path.suffix == ".qmd":
        m = FM.match(text)
        if not m:
            raise ValueError(f"{path}: no YAML front matter")
        return yaml.safe_load(m.group(1)) or {}
    return yaml.safe_load(text) or {}

def iter_records():
    """Yield (kind, path, record) for every record file in the source layer.

    Layouts: <dir>/<slug>.yaml | <dir>/<slug>/index.qmd | structures/<slug>/structure.yaml (+ kit files)
             plates/<doc>/<n>/plate.yaml | tables/<doc>/<n>/table.yaml
    """
    for kind, d in RECORD_DIRS.items():
        base = ROOT / d
        if not base.exists():
            continue
        if kind == "structure":
            for p in sorted(base.glob("*/structure.yaml")):
                yield kind, p, load_record(p)
                for k, fn in KIT_FILES.items():
                    q = p.parent / fn
                    if q.exists():
                        yield k, q, load_record(q)
            continue
        if kind in ("plate", "table"):
            for p in sorted(base.glob(f"*/*/{kind}.yaml")):
                yield kind, p, load_record(p)
            continue
        if kind == "curve":
            for p in sorted(base.glob("*/curve.yaml")):
                yield kind, p, load_record(p)
            continue
        if kind in QMD_KINDS:
            for p in sorted(base.glob("*/index.qmd")):
                yield kind, p, load_record(p)
        else:  # yaml records; a sibling <slug>/index.qmd is a generated page, not a record
            for p in sorted(base.glob("*.yaml")):
                yield kind, p, load_record(p)

def id_index():
    return {rec.get("id"): (kind, path) for kind, path, rec in iter_records() if isinstance(rec, dict) and rec.get("id")}
