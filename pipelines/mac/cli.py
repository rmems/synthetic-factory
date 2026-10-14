"""MAC commands: catalog-check and AST extract.

Read-only. This command does not reserve or publish a raw round and does
not write mill scripts. Exit 0 on success, 2 on a coded refusal or usage
error. ``--json`` prints one object so an agent never parses prose.
"""
import importlib

from . import catalog as cat

_pkg = __package__ or ""
_name = "pipelines.catalog_cli.entry" if _pkg.startswith("pipelines.") else "catalog_cli.entry"
importlib.import_module(_name).install_extract(globals(), cat)
