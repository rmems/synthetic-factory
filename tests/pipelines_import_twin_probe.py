"""Import-twin probe for the flat ``pipelines/`` modules.

A flat module under ``pipelines/`` has two import names: the bare name a direct
CLI uses (``pipelines/`` on ``sys.path``, ``import census``) and the package
name (``pipelines.census``). The binding prelude (``_assert_direct_sibling``,
``_join_package_sibling`` and the ``_expose_package_sibling`` finalizer) makes
the two names one module object. A module without it loads a second copy as
soon as a process uses both names, and an error class raised through one copy
is not caught through the other (``preference_model``, #427).

:func:`isolated_report` unloads every pipelines module, imports each named
module under both names in the order given, and reports the names whose two
spellings are not one object. A module that fails to import raises out of the
probe with its own traceback. :func:`isolated_shim_report` does the same for
the thin CLI shims and reports whether both copies of each expose the one
``pipelines.<package>.cli`` object and which names they define.
:func:`in_fresh_interpreter` runs either report in a child started with the
``spawn`` method, so nothing the calling test process already imported, popped
or patched can mask a split. Only plain data crosses the process boundary: the
order, the module names, and the report.
"""

from __future__ import annotations

import importlib
import multiprocessing
import sys
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from pipeline_import_test_support import PIPELINES, REPO, clean_package_imports

FRESH_INTERPRETER_TIMEOUT_SECONDS = 300


def _package_first(name: str) -> tuple[str, str]:
    return f"pipelines.{name}", name


def _direct_first(name: str) -> tuple[str, str]:
    return name, f"pipelines.{name}"


# Which of a module's two names is imported first. Both orders run after the
# package itself is imported, the state a direct CLI meets once anything it
# loaded has imported ``pipelines``.
ORDERS = {"package_first": _package_first, "direct_first": _direct_first}


def flat_modules() -> tuple[str, ...]:
    """Every module file directly under ``pipelines/``, by its bare import name."""

    return tuple(sorted(path.stem for path in PIPELINES.glob("*.py") if path.stem != "__init__"))


def _put_first(directory: Path) -> None:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def _one_object(name: str) -> bool:
    module = sys.modules.get(name)
    return module is not None and module is sys.modules.get(f"pipelines.{name}")


def split_modules(order: str, names: Sequence[str]) -> dict[str, Any]:
    """Import every name under both spellings in ``order`` here; report the split ones."""

    spellings = ORDERS[order]
    _put_first(REPO)
    _put_first(PIPELINES)
    importlib.import_module("pipelines")  # both orders start with the package imported

    for name in names:
        for spelling in spellings(name):
            __import__(spelling)
    split = [name for name in names if not _one_object(name)]
    return {"order": order, "modules": len(names), "split": split}


def isolated_report(order: str, names: Sequence[str]) -> dict[str, Any]:
    """:func:`split_modules` with every pipelines module unloaded first and restored after."""

    with clean_package_imports():
        return split_modules(order, names)


def _shim_facts(shim: str, package: str) -> dict[str, Any]:
    """Whether both copies of ``shim`` expose the one ``<package>.cli``, and what they define."""

    cli = sys.modules[f"pipelines.{package}.cli"]
    copies = (sys.modules[shim], sys.modules[f"pipelines.{shim}"])
    return {
        "one_cli": sys.modules.get(f"{package}.cli") is cli
        and all(copy.cli is cli for copy in copies),
        "names": sorted({name for copy in copies for name in vars(copy) if name[:2] != "__"}),
    }


def isolated_shim_report(order: str, shims: Mapping[str, str]) -> dict[str, Any]:
    """Import each shim (``{shim: subpackage}``) under both names in ``order``; report its facts."""

    with clean_package_imports():
        split_modules(order, tuple(shims))
        return {shim: _shim_facts(shim, package) for shim, package in shims.items()}


def in_fresh_interpreter(report: Callable[..., dict[str, Any]], *args: Any) -> dict[str, Any]:
    """``report(*args)`` in a child interpreter started with ``spawn``."""

    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
        future = pool.submit(report, *args)
        try:
            return future.result(timeout=FRESH_INTERPRETER_TIMEOUT_SECONDS)
        except TimeoutError:
            pool.terminate_workers()
            raise
