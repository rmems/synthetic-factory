"""Sandbox-refusal mill (prefix ``sbox``).

AST-extracted leftover dump plants for ``sandbox-refusal-factory``.
Mill scripts named ``sbox-mill*.py`` are not vendored;
``generate.plants_from_source`` is the extract seam.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
