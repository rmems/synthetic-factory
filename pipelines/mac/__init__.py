"""Multi-agent coordination mill (prefix ``mac``).

AST-extracted leftover plants for ``multi-agent-coordination-factory``.
Mill scripts named ``mac-mill*.py`` are not vendored;
``generate.plants_from_source`` is the extract seam.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
