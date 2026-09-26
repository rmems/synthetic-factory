"""CSV leftover leftover leftover mill: pinned catalog, generate, CLI.

The leftover mill on ``legacy-mill-lane`` is not vendored. ``PAIRS`` was
AST-extracted (``git show`` + ``ast.parse``, never ``exec``) into
``config/csv/``. This package loads that catalog and emits success/handoff
episode pairs. It does not hop factories, does not write ``outputs/raw/``,
and does not stamp ``grok-4.6``.
"""

from ._contract import bind_import_twin

__all__ = [
    "_contract",
    "catalog",
    "catalog_extract",
    "catalog_io",
    "catalog_models",
    "catalog_source",
    "catalog_validation",
    "cli",
    "generate",
    "generate_io",
    "generate_parent",
    "steps",
    "steps_templates",
]

bind_import_twin(__name__)
