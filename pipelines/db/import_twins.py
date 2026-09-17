#!/usr/bin/env python3
"""Bind the two import names of a ``db`` module to one object."""

from __future__ import annotations

import sys

_PACKAGE_PREFIX = "pipelines."

__all__ = ["bind_import_twin", "import_twin_of"]


def import_twin_of(qualified_name: str) -> str:
    """The other supported import name of ``qualified_name``."""
    if qualified_name.startswith(_PACKAGE_PREFIX):
        return qualified_name[len(_PACKAGE_PREFIX):]
    return f"{_PACKAGE_PREFIX}{qualified_name}"


def bind_import_twin(qualified_name: str) -> None:
    """Register ``qualified_name`` under its twin; first finisher wins."""
    sys.modules.setdefault(import_twin_of(qualified_name), sys.modules[qualified_name])
    package_name = qualified_name.rpartition(".")[0]
    package = sys.modules.get(package_name)
    if package is not None:
        sys.modules.setdefault(import_twin_of(package_name), package)


bind_import_twin(__name__)
