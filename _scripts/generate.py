"""Generate entity pages into _gen/ from records. Record .qmd files (materials, people, theses, publications) are their own pages; yaml-kit records (structures, series, transitions, plates, tables) get a generated index.qmd next to them, which is gitignored."""
from __future__ import annotations
import pathlib, yaml
from common import ROOT, iter_records

GEN = ROOT / "_gen"

def fm(d): return "---\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True) + "---\n"

def main():
    GEN.mkdir(exist_ok=True)
    n = 0
    for kind, path, rec in iter_records():
        if kind != "structure":
            continue
        slug = rec["id"].split(":", 1)[1]
        page = ROOT / "structures" / slug / "index.qmd"
        page.parent.mkdir(parents=True, exist_ok=True)
        cell = rec["cell"]; sg = rec["space_group"]; T = rec["conditions"]["temperature_k"]
        atoms = "\n".join(f"| {a['label']} | {a['element']} | {a['wyckoff']} | {a['x']} | {a['y']} | {a['z']} | {a.get('occupancy','1')} | {a.get('b_iso','')} |" for a in rec["atoms"])
        body = f"""
::: {{.page-article}}
# {rec['material'].split(':')[1]} · {sg['hm']} · {T:g} K

Status: {rec['status']} · visibility: {rec['visibility']} · id `{rec['id']}`

## Cell

| a | b | c | α | β | γ | V |
|---|---|---|---|---|---|---|
| {cell['a']} | {cell['b']} | {cell['c']} | {cell['alpha']} | {cell['beta']} | {cell['gamma']} | {cell.get('volume','')} |

## Atoms

| label | element | Wyckoff | x | y | z | occ | B_iso |
|---|---|---|---|---|---|---|---|
{atoms}

## Evidence

{chr(10).join('- ' + e['doc'] + (' · table ' + e['table'] if e.get('table') else '') + (' · page ' + str(e['page']) if e.get('page') else '') + (' · md line ' + str(e['md_line']) if e.get('md_line') else '') for e in rec['evidence'])}
:::
"""
        page.write_text(fm({"title": f"{rec['material'].split(':')[1]} {sg['hm']} {T:g} K"}) + body)
        n += 1
    print(f"generate: {n} structure page(s) -> structures/*/index.qmd")

if __name__ == "__main__":
    main()
