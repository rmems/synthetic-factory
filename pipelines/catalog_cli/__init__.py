"""Command-line layer shared by the catalog-backed mill packages.

``subcommands`` holds the two command shapes each package's ``cli`` module
used to copy. Like the packages it serves, every module here ends with
``bind_import_twin(__name__)``, so ``catalog_cli.x`` (with ``pipelines/`` on
``sys.path``) and ``pipelines.catalog_cli.x`` are one object.
"""

from .subcommands import bind_import_twin

__all__ = ["subcommands"]

bind_import_twin(__name__)
