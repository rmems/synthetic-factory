#!/usr/bin/env python3
"""Import-form probe for the ACTF family, run in a fresh interpreter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
MODULES = (
    "_contract",
    "vocabulary",
    "lineage",
    "ast_scan",
    "records",
    "cli",
)


def _forget_repository_modules() -> None:
    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry
        for entry in sys.path
        if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _cli_form() -> Any:
    sys.path.insert(0, str(PIPELINES))
    from actf import cli as flat

    return flat


def _package_form() -> Any:
    sys.path.insert(0, str(REPO))
    from pipelines.actf import cli as packaged

    return packaged


def _split() -> list[str]:
    split = []
    for name in MODULES:
        flat = sys.modules.get(f"actf.{name}")
        packaged = sys.modules.get(f"pipelines.actf.{name}")
        if flat is None or packaged is None or flat is not packaged:
            split.append(name)
    return split


def run_form(form: str) -> dict[str, Any]:
    _forget_repository_modules()
    if form == "cli":
        flat = _cli_form()
        from actf import vocabulary as cv

        return {"family": cv.FAMILY, "cli": flat.__name__}
    if form == "package":
        packaged = _package_form()
        from pipelines.actf import vocabulary as cv

        return {"family": cv.FAMILY, "cli": packaged.__name__}
    if form == "cli_then_package":
        flat = _cli_form()
        packaged = _package_form()
        from actf import vocabulary as cv

        return {
            "one_object": flat is packaged,
            "one_refusal_class": cv.ActfRefusal is sys.modules["pipelines.actf.vocabulary"].ActfRefusal,
            "split_modules": _split(),
            "family": cv.FAMILY,
        }
    if form == "package_then_cli":
        packaged = _package_form()
        flat = _cli_form()
        from pipelines.actf import vocabulary as cv

        return {
            "one_object": flat is packaged,
            "one_refusal_class": cv.ActfRefusal is sys.modules["actf.vocabulary"].ActfRefusal,
            "split_modules": _split(),
            "family": cv.FAMILY,
        }
    raise ValueError(form)
