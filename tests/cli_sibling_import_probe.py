"""Import-form probe for the formerly direct-only pipeline CLIs, run fresh.

``next_round``, ``quality_gate_audit``, ``quality_gate_embedding``,
``card_schema``, ``card_schema_validate``, ``card_schema_yaml``,
``verify_execution`` and ``verify_execution_shapes`` once imported their
siblings by bare name only, so ``import pipelines.next_round`` raised
``ModuleNotFoundError``. :func:`run_form` executes in a child interpreter
started with the ``spawn`` method (:func:`in_fresh_interpreter`), forgets every
repository module and path entry it inherited, imports in the order the form
names and reports plain data, so nothing the parent already imported can mask
a split between the two spellings.
"""

from __future__ import annotations

import importlib
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import ModuleType
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

MODULES = (
    "card_schema",
    "card_schema_validate",
    "card_schema_yaml",
    "next_round",
    "quality_gate_audit",
    "quality_gate_embedding",
    "verify_execution",
    "verify_execution_shapes",
)

# Classes a caller catches or constructs by name; a split here means an error
# raised through one import name is not caught through the other.
SHARED_CLASSES = (
    ("card_schema", "CardSchemaError"),
    ("next_round", "RoundExistsError"),
    ("next_round", "TransactionError"),
    ("quality_gate_audit", "AuditOptions"),
)


def in_fresh_interpreter(target, *args: Any) -> Any:
    """Run ``target(*args)`` in a spawned interpreter and return its result."""

    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=context) as pool:
        return pool.submit(target, *args).result(timeout=180)


def _forget_repository_modules() -> None:
    """Drop every module and path entry of this repository, except the probe."""

    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    sys.path[:] = [
        entry for entry in sys.path if Path(entry or ".").resolve() not in (REPO, PIPELINES)
    ]


def import_flat() -> dict[str, ModuleType]:
    """``python3 pipelines/x.py``: ``pipelines/`` first, every module by bare name."""

    sys.path.insert(0, str(PIPELINES))
    return {name: importlib.import_module(name) for name in MODULES}


def import_packaged() -> dict[str, ModuleType]:
    """The package form from the repository root: ``pipelines.<name>``."""

    sys.path.insert(0, str(REPO))
    return {name: importlib.import_module(f"pipelines.{name}") for name in MODULES}


LOADERS = {"cli": import_flat, "package": import_packaged}


def split_modules() -> list[str]:
    """The modules whose two spellings are not one loaded module object."""

    return [
        name
        for name in MODULES
        if sys.modules.get(name) is None
        or sys.modules.get(name) is not sys.modules.get(f"pipelines.{name}")
    ]


def _paired_report(flat: dict[str, ModuleType], packaged: dict[str, ModuleType]) -> dict[str, Any]:
    return {
        "one_object": {name: flat[name] is packaged[name] for name in MODULES},
        "one_class": {
            f"{module}.{attribute}": getattr(flat[module], attribute)
            is getattr(packaged[module], attribute)
            for module, attribute in SHARED_CLASSES
        },
        "split_modules": split_modules(),
    }


def run_form(form: str) -> dict[str, Any]:
    """Load ``form`` ("cli", "package" or "<first>_then_<second>") and report it."""

    _forget_repository_modules()
    if form in LOADERS:
        loaded = LOADERS[form]()
        return {
            "names": sorted(module.__name__ for module in loaded.values()),
            "pipelines_on_path": str(PIPELINES) in sys.path,
            "split_modules": split_modules(),
        }
    first, _then, second = form.partition("_then_")
    bound = {first: LOADERS[first](), second: LOADERS[second]()}
    return _paired_report(bound["cli"], bound["package"])
