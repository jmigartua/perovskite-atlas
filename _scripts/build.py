"""sqlite, parquet, json, cif zip, bibtex -> _data/computed/

Phase 0 stub: establishes the verb and its contract (see _schemas/INTERFACES.md). Implemented in Phase 1.
"""
import sys
from common import ROOT
out = ROOT / "_data/computed"
out.mkdir(parents=True, exist_ok=True)
print("build: not implemented yet (Phase 1); contract in _schemas/INTERFACES.md")
sys.exit(0)
