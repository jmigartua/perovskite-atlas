"""Validate every record against its schema, check references and evidence. Exit 1 on any error."""
from __future__ import annotations
import sys, pathlib, yaml
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)
from jsonschema import Draft202012Validator, RefResolver
from common import ROOT, iter_records, id_index

SCHEMAS = ROOT / "_schemas"

def load_schema(name):
    return yaml.safe_load((SCHEMAS / f"{name}.schema.yaml").read_text())

def main() -> int:
    store = {}
    for p in SCHEMAS.glob("*.schema.yaml"):
        s = yaml.safe_load(p.read_text()); store[s["$id"]] = s
    defs = store["_defs.schema.yaml"]
    errors = []
    ids = id_index()
    dupes = {}
    for kind, path, rec in iter_records():
        if not isinstance(rec, dict):
            errors.append(f"{path}: not a mapping"); continue
        schema_name = f"{kind}.schema.yaml"
        if schema_name not in store:
            errors.append(f"{path}: no schema for kind '{kind}'"); continue
        resolver = RefResolver(base_uri="", referrer=store[schema_name], store=store)
        v = Draft202012Validator(store[schema_name], resolver=resolver)
        for e in sorted(v.iter_errors(rec), key=lambda e: list(e.path)):
            errors.append(f"{path}: {'/'.join(map(str, e.path)) or '<root>'}: {e.message}")
        rid = rec.get("id")
        if rid:
            dupes.setdefault(rid, []).append(path)
        # references: any string value starting with a known prefix must resolve
        def walk(x):
            if isinstance(x, dict):
                for k, val in x.items():
                    if k == "id": continue
                    walk(val)
            elif isinstance(x, list):
                for val in x: walk(val)
            elif isinstance(x, str) and len(x) > 4 and x[3] == ":" and x[:3] in ("ser","mat","smp","dat","str","ref","mod","trn","mag","fnd","doc","plt","tbl","per","ins","crv"):
                if x not in ids:
                    errors.append(f"{path}: reference '{x}' does not resolve")
        walk(rec)
    for rid, paths in dupes.items():
        if len(paths) > 1:
            errors.append(f"duplicate id {rid}: {', '.join(map(str, paths))}")
    n = sum(1 for _ in iter_records())
    if errors:
        print(f"validate: {len(errors)} error(s) in {n} record(s)")
        for e in errors: print("  " + e)
        return 1
    print(f"validate: ok, {n} record(s), {len(ids)} id(s)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
