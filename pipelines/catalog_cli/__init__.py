"""Command-line layer shared by the catalog-backed mill packages.

``subcommands`` holds the two command shapes each package's ``cli`` module
used to copy. Like the packages it serves, every module here ends with
``bind_import_twin(__name__)``, so ``catalog_cli.x`` (with ``pipelines/`` on
``sys.path``) and ``pipelines.catalog_cli.x`` are one object.
"""

import sys

from .subcommands import bind_import_twin

__all__ = ["subcommands"]

bind_import_twin(__name__)

# ``bind_import_twin`` puts ``pipelines.catalog_cli`` in ``sys.modules`` when the flat
# form loads first, but only CPython's own import of a child sets the attribute on its
# parent. ``pipelines/__init__.py`` closes that gap when ``pipelines`` loads afterwards;
# when it is already loaded, attach the package here so ``pipelines.catalog_cli``
# resolves as an attribute after ``import pipelines.catalog_cli.subcommands``.
if __name__ == "catalog_cli" and "pipelines" in sys.modules:
    vars(sys.modules["pipelines"]).setdefault("catalog_cli", sys.modules["pipelines.catalog_cli"])
