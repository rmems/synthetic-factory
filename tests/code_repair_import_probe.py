#!/usr/bin/env python3
"""Import-form probe for the code-repair family, run in a fresh interpreter.

Mirrors ``distill_import_probe``: a spawned child forgets every repository
module, puts ``sys.path`` the way one import form would, imports in the
form's order and reports what it bound as plain data.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
MODULES = tuple(
    "_contract vocabulary catalog catalog_check mutate mutate_span mutate_literals executor "
    "verify records views generate export export_integrity cli record_validation evidence "
    "publication publication_export publication_receipt selection admission source_policy validation "
    "planning candidate_io row_validation"
    .split()
)


def _forget_repository_modules() -> None:
    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)]


def _cli_form() -> Any:
    sys.path.insert(0, str(PIPELINES))
    from code_repair import cli as flat

    return flat


def _package_form() -> Any:
    sys.path.insert(0, str(REPO))
    from pipelines.code_repair import cli as packaged

    return packaged


def _split() -> list[str]:
    return [
        name for name in MODULES
        if sys.modules.get(f"code_repair.{name}") is None
        or sys.modules.get(f"code_repair.{name}") is not sys.modules.get(f"pipelines.code_repair.{name}")
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
        "one_refusal_class": one.cv.RepairRefusal is two.cv.RepairRefusal,
        "split_modules": _split(),
    }
