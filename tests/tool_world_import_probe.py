#!/usr/bin/env python3
"""Import-form probe for the tool-world package, run in a fresh interpreter.

Every module of ``pipelines/tool_world/`` (the surfaces and policies
subpackages included) must resolve to one object whether it is imported as
``tool_world.x`` with ``pipelines/`` on ``sys.path`` or as
``pipelines.tool_world.x`` from the repository root, whichever form loads
first. Each form imports the ``cli`` entry module by one literal statement
and the package loads behind it; ``MODULES`` is discovered from the package
directory, so a module file that import leaves unloaded is reported, and a
new file is probed without being listed anywhere. ``run_form`` and
``run_entry`` are executed in a spawned interpreter
(``in_fresh_interpreter``) by ``test_tool_world_imports`` and
``test_tool_world_cli``: each first forgets every repository module and path
entry the parent handed down, so what the operator entry point bootstraps on
its own is what the probe sees.
"""

from __future__ import annotations

import contextlib
import io
import multiprocessing
import runpy
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
ENTRY = PIPELINES / "tool_world_cli.py"
PACKAGE = "tool_world"


def _discovered() -> tuple[str, ...]:
    """Every module file under the package, named below it: ``""`` is the package itself."""
    package = PIPELINES / PACKAGE
    names = []
    for path in sorted(package.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        parts = list(path.relative_to(package).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            names.append(".".join(parts))
    return tuple(names)


MODULES = _discovered()


def spellings(name: str) -> tuple[str, str]:
    """``(flat, packaged)`` import names of one module; ``""`` names the package itself."""
    suffix = f".{name}" if name else ""
    return f"{PACKAGE}{suffix}", f"pipelines.{PACKAGE}{suffix}"


def in_fresh_interpreter(target, *args: Any) -> Any:
    """Run ``target(*args)`` in a spawned interpreter and return its result."""
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
        return pool.submit(target, *args).result(timeout=120)


def _forget_repository_modules() -> None:
    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def _put_first(directory: Path) -> None:
    """Put ``directory`` at the front of ``sys.path`` unless it is already listed."""
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def _relative(module: ModuleType) -> str:
    """The module's name below the package: ``""`` for the package, ``surfaces.mcp`` for a child."""
    _above, _package, below = module.__name__.partition(PACKAGE)
    return below.removeprefix(".")


def _index(*modules: ModuleType) -> dict[str, ModuleType]:
    return {_relative(module): module for module in modules}


def _loaded_behind(entry: ModuleType) -> dict[str, ModuleType]:
    """The package ``entry`` belongs to and every module of it now loaded, keyed below the package."""
    prefix = entry.__name__.rpartition(".")[0]
    return _index(
        *(
            module
            for name, module in sys.modules.items()
            if isinstance(module, ModuleType) and (name == prefix or name.startswith(f"{prefix}."))
        )
    )


def import_flat() -> dict[str, ModuleType]:
    """Import the package as ``tool_world`` with ``pipelines/`` first on ``sys.path``."""
    _put_first(PIPELINES)
    from tool_world import cli

    return _loaded_behind(cli)


def import_packaged() -> dict[str, ModuleType]:
    """Import the package as ``pipelines.tool_world`` with the repository root first."""
    _put_first(REPO)
    from pipelines.tool_world import cli

    return _loaded_behind(cli)


LOADERS = {"cli": import_flat, "package": import_packaged}


def _split() -> list[str]:
    split = []
    for name in ("", *MODULES):
        flat, packaged = spellings(name)
        if sys.modules.get(flat) is None or sys.modules.get(flat) is not sys.modules.get(packaged):
            split.append(flat)
    return split


def _paired_report(one: dict[str, ModuleType], two: dict[str, ModuleType]) -> dict[str, Any]:
    return {
        "one_object": all(one.get(name) is two.get(name) for name in {*one, *two}),
        "one_refusal_class": one["cli"].cv.ToolWorldRefusal is two["cli"].cv.ToolWorldRefusal,
        "split_modules": _split(),
    }


def run_form(form: str) -> dict[str, Any]:
    """Load ``form`` ("cli", "package", or "<first>_then_<second>") and report what it bound."""
    _forget_repository_modules()
    if form in LOADERS:
        return {"family": LOADERS[form]()["cli"].cv.FAMILY}
    first, _then, second = form.partition("_then_")
    return _paired_report(LOADERS[first](), LOADERS[second]())


def run_entry(argv: list[str]) -> dict[str, Any]:
    """Run ``pipelines/tool_world_cli.py`` as ``__main__`` with ``argv`` and capture its exit.

    Nothing of the repository is importable beforehand, so the script's own
    ``sys.path`` bootstrap is what resolves ``tool_world``; the exit code is
    ``None`` when the script returns without calling ``sys.exit``.
    """
    _forget_repository_modules()
    out, err = io.StringIO(), io.StringIO()
    code = None
    with (
        mock.patch.object(sys, "argv", [str(ENTRY), *argv]),
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
    ):
        try:
            runpy.run_path(str(ENTRY), run_name="__main__")
        except SystemExit as stop:
            code = stop.code
    return {"code": code, "stdout": out.getvalue(), "stderr": err.getvalue()}
