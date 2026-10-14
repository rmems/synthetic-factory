import importlib
import sys
from pathlib import Path

_pkg = __package__ or ""
_root = str(Path(__file__).resolve().parents[1])
if not _pkg.startswith("pipelines.") and _root not in sys.path:
    sys.path.insert(0, _root)
importlib.import_module(
    "pipelines.catalog_cli.entry" if _pkg.startswith("pipelines.") else "catalog_cli.entry"
).install_generate(globals())
