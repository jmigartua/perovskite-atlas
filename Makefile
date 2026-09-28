PY := python3
.PHONY: validate derive confront build generate render audit datasets fer clean all

validate:      ## schemas, references, units, space groups, evidence
	$(PY) _scripts/validate.py

derive:        ## tolerance factors, volumes, geometry from CIF, decompositions -> _data/computed/
	$(PY) _scripts/derive.py

confront:      ## reported vs recomputed -> _data/computed/reports/confrontation.md
	$(PY) _scripts/confront.py

build:         ## sqlite, parquet, json, cif zip, bibtex -> _data/computed/
	$(PY) _scripts/build.py

generate:      ## entity pages -> _gen/
	$(PY) _scripts/generate.py

render: generate
	quarto render

audit:         ## orphans, missing evidence, hidden leaks, coverage -> _data/computed/reports/audit.md
	$(PY) _scripts/audit.py

fer:           ## fer documents for every refined structure, decomposition and geometry -> _data/computed/fer/
	$(PY) _scripts/fer_export.py

datasets:      ## propose dataset records from sources/rescue/INVENTORY.csv
	$(PY) _scripts/datasets_from_inventory.py

all: validate derive confront build generate render audit

clean:
	rm -rf _site _gen _data/computed .quarto
