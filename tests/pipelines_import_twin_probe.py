"""Import-twin probe for the flat ``pipelines/`` modules.

A flat module under ``pipelines/`` has two import names: the bare name a direct
CLI uses (``pipelines/`` on ``sys.path``, ``import census``) and the package
name (``pipelines.census``). The binding prelude (``_assert_direct_sibling``,
``_join_package_sibling`` and the ``_expose_package_sibling`` finalizer) makes
the two names one module object. A module without it loads a second copy as
soon as a process uses both names, and an error class raised through one copy
is not caught through the other (``preference_model``, #427).

:func:`isolated_report` unloads every pipelines module, then imports each named
module under both names in the order given, from a clean slate of its own.
An earlier sibling that bare-imports a later one (``baseline_eval`` imports
``moe_router``) therefore cannot choose that later module's first import.
The report names every module whose two spellings are not one object, and
every module that was already loaded before its own turn. A module that fails
to import raises out of the probe with its own traceback.
:func:`isolated_shim_report` does the same for the thin CLI shims and reports
whether both copies of each expose the one ``pipelines.<package>.cli`` object
and which names they define.
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


def _prepare_import_path() -> None:
    _put_first(REPO)
    _put_first(PIPELINES)
    # Both orders start with the package imported, the state a direct CLI meets
    # once anything it loaded has imported ``pipelines``.
    importlib.import_module("pipelines")


def _each_fresh(names: Sequence[str], visit: Callable[[str, bool], None]) -> None:
    """Call ``visit(name, leaked)`` with pipeline modules unloaded, once per name.

    ``leaked`` is true when ``name`` is already in ``sys.modules`` before this
    turn imports ``pipelines``. That is an earlier sibling choosing the first
    import. Modules ``pipelines`` itself loads (``exact_json``) are not leaks:
    the check runs before that import.
    """

    for name in names:
        with clean_package_imports():
            leaked = _already_loaded(name)
            _prepare_import_path()
            visit(name, leaked)


def _already_loaded(name: str) -> bool:
    return name in sys.modules or f"pipelines.{name}" in sys.modules


def split_modules(order: str, names: Sequence[str]) -> dict[str, Any]:
    """Import every name under both spellings in ``order``; report splits.

    Each name starts unloaded. A sibling imported earlier in ``names`` cannot
    leave a bare module in ``sys.modules`` for the next name.
    """

    spellings = ORDERS[order]
    split: list[str] = []
    preloaded: list[str] = []

    def visit(name: str, leaked: bool) -> None:
        if leaked:
            preloaded.append(name)
        for spelling in spellings(name):
            __import__(spelling)
        if not _one_object(name):
            split.append(name)

    _each_fresh(names, visit)
    return {
        "order": order,
        "modules": len(names),
        "split": split,
        "preloaded": preloaded,
    }


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

    spellings = ORDERS[order]
    facts: dict[str, Any] = {}

    def visit(name: str, _leaked: bool) -> None:
        for spelling in spellings(name):
            __import__(spelling)
        facts[name] = _shim_facts(name, shims[name])

    with clean_package_imports():
        _each_fresh(tuple(shims), visit)
    return facts


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
