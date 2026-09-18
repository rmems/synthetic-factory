"""AST-only extraction of recovered ACTF generator lineages (burst corpus B).

Reads a recover-grok session tree. Never imports, compiles, or executes
recovered sources. Does not vendor mill scripts.
"""

__all__ = ("_contract vocabulary lineage ast_scan records catalog cli").split()

from ._contract import bind_import_twin

bind_import_twin(__name__)
