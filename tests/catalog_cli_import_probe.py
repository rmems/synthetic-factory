"""Fresh-interpreter probe for ``pipelines.catalog_cli`` in each import order.

:func:`report` runs in a child started with the ``spawn`` method, so nothing the test
process already imported can mask a missing parent attribute. It forgets every module
loaded from this repository, puts both import roots on ``sys.path``, imports the
shared module in the named order with literal import statements, and returns plain
data: whether ``pipelines.catalog_cli`` resolves as an attribute to the twin of
``catalog_cli``, and whether both names of ``subcommands`` are one object.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"


def _forget_repository_modules() -> None:
    for name, module in tuple(sys.modules.items()):
        if (getattr(module, "__file__", None) or "").startswith(str(REPO)):
            del sys.modules[name]


def _package_root() -> ModuleType:
    import pipelines

    return pipelines


def _flat_form() -> ModuleType:
    import catalog_cli.subcommands

    return catalog_cli.subcommands


def _package_form() -> ModuleType:
    import pipelines.catalog_cli.subcommands

    return pipelines.catalog_cli.subcommands


def _pipelines_then_flat() -> tuple[ModuleType, ...]:
    return _package_root(), _flat_form()


def _flat_then_pipelines() -> tuple[ModuleType, ...]:
    return _flat_form(), _package_root()


def _package_only() -> tuple[ModuleType, ...]:
    return (_package_form(),)


ORDERS = {
    "pipelines_then_flat": _pipelines_then_flat,
    "flat_then_pipelines": _flat_then_pipelines,
    "package_only": _package_only,
}


def report(order: str) -> dict[str, bool]:
    """Import in ``order`` in this (fresh) interpreter and report the bindings."""

    _forget_repository_modules()
    sys.path[:0] = [str(REPO), str(PIPELINES)]
    ORDERS[order]()
    import pipelines.catalog_cli.subcommands

    package = sys.modules["pipelines.catalog_cli"]
    return {
        "attribute": getattr(pipelines, "catalog_cli", None) is package,
        "chain": pipelines.catalog_cli.subcommands is sys.modules["catalog_cli.subcommands"],
        "package_twin": sys.modules.get("catalog_cli") is package,
    }
