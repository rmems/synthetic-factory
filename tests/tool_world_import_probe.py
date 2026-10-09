#!/usr/bin/env python3
"""Import-form probe for the tool-world package, run in a fresh interpreter.

Every module of ``pipelines/tool_world/`` (the surfaces and policies
subpackages included) must resolve to one object whether it is imported as
``tool_world.x`` with ``pipelines/`` on ``sys.path`` or as
``pipelines.tool_world.x`` from the repository root, whichever form loads
first. ``run_form`` is executed in a spawned interpreter by
``test_tool_world_imports``.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
PACKAGE = "tool_world"
MODULES = (
    "_contract",
    "vocabulary",
    "schema_lite",
    "faults",
    "pack",
    "catalog",
    "env",
    "predicates",
    "records",
    "replay",
    "generate",
    "cli",
    "surfaces",
    "surfaces.base",
    "surfaces.workspace",
    "surfaces.mcp",
    "surfaces.browser",
    "surfaces.browser_dom",
    "surfaces.delegation",
    "policies",
    "policies.scripted",
)


def spellings(name: str) -> tuple[str, str]:
    """``(flat, packaged)`` import names of one module; ``""`` names the package itself."""
    suffix = f".{name}" if name else ""
    return f"{PACKAGE}{suffix}", f"pipelines.{PACKAGE}{suffix}"


def _forget_repository_modules() -> None:
    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _import_all(root: str) -> Any:
    for name in MODULES:
        importlib.import_module(f"{root}.{name}")
    return importlib.import_module(f"{root}.cli")


def _cli_form() -> Any:
    sys.path.insert(0, str(PIPELINES))
    return _import_all(PACKAGE)


def _package_form() -> Any:
    sys.path.insert(0, str(REPO))
    return _import_all(f"pipelines.{PACKAGE}")


def _split() -> list[str]:
    split = []
    for name in ("", *MODULES):
        flat, packaged = spellings(name)
        if sys.modules.get(flat) is None or sys.modules.get(flat) is not sys.modules.get(packaged):
            split.append(flat)
    return split


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
        "one_refusal_class": one.cv.ToolWorldRefusal is two.cv.ToolWorldRefusal,
        "split_modules": _split(),
    }
