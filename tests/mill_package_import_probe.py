#!/usr/bin/env python3
"""Import-form probe for the mill family, run in a fresh interpreter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
MODULES = tuple(
    "_contract vocabulary catalog catalog_load records generate validation publication cli".split()
)


def _forget_repository_modules() -> None:
    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _cli_form() -> Any:
    sys.path.insert(0, str(PIPELINES))
    from mill import catalog_load  # noqa: F401
    from mill import cli as flat

    return flat


def _package_form() -> Any:
    sys.path.insert(0, str(REPO))
    from pipelines.mill import catalog_load  # noqa: F401
    from pipelines.mill import cli as packaged

    return packaged


def _split() -> list[str]:
    return [
        name
        for name in MODULES
        if sys.modules.get(f"mill.{name}") is None
        or sys.modules.get(f"mill.{name}") is not sys.modules.get(f"pipelines.mill.{name}")
    ]


def run_form(form: str) -> dict[str, Any]:
    _forget_repository_modules()
    if form == "cli":
        return {"family": _cli_form().cv.FAMILY}
    if form == "package":
        return {"family": _package_form().cv.FAMILY}
    first, _then, second = form.partition("_then_")
    loaders = {"cli": _cli_form, "package": _package_form}
    one, two = loaders[first](), loaders[second]()
    return {
        "one_object": one is two,
        "one_refusal_class": one.cv.MillRefusal is two.cv.MillRefusal,
        "split_modules": _split(),
    }
