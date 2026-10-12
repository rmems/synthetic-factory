"""Import-form probe for the formerly direct-only pipeline CLIs, run fresh.

``next_round``, ``quality_gate_audit``, ``quality_gate_embedding``,
``card_schema``, ``card_schema_validate``, ``card_schema_yaml``,
``verify_execution`` and ``verify_execution_shapes`` once imported their
siblings by bare name only, so ``import pipelines.next_round`` raised
``ModuleNotFoundError``. Their package form now imports those siblings
relatively, so every pipelines module a converted module loads, not only the
converted module itself, has to stay one object under its two names.

Each ``run_*`` function executes in a child interpreter started with the
``spawn`` method (:func:`in_fresh_interpreters`). It first isolates the child
the way ``python -I`` starts one (:func:`isolate`): every repository module is
forgotten and ``sys.path`` keeps only the interpreter's own standard library and
site-packages, so no ``''``, working directory, ``PYTHONPATH`` or user-site entry
the parent had can make ``pipelines`` importable by accident. Only plain data
crosses the process boundary, and every import below names its module
literally.
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
FRESH_INTERPRETER_TIMEOUT_SECONDS = 300
FRESH_INTERPRETER_WORKERS = 4

PACKAGE_LOADERS = {
    "card_schema": lambda: importlib.import_module("pipelines.card_schema"),
    "card_schema_validate": lambda: importlib.import_module("pipelines.card_schema_validate"),
    "card_schema_yaml": lambda: importlib.import_module("pipelines.card_schema_yaml"),
    "next_round": lambda: importlib.import_module("pipelines.next_round"),
    "quality_gate_audit": lambda: importlib.import_module("pipelines.quality_gate_audit"),
    "quality_gate_embedding": lambda: importlib.import_module("pipelines.quality_gate_embedding"),
    "verify_execution": lambda: importlib.import_module("pipelines.verify_execution"),
    "verify_execution_shapes": lambda: importlib.import_module("pipelines.verify_execution_shapes"),
}
FLAT_LOADERS = {
    "card_schema": lambda: importlib.import_module("card_schema"),
    "card_schema_validate": lambda: importlib.import_module("card_schema_validate"),
    "card_schema_yaml": lambda: importlib.import_module("card_schema_yaml"),
    "next_round": lambda: importlib.import_module("next_round"),
    "quality_gate_audit": lambda: importlib.import_module("quality_gate_audit"),
    "quality_gate_embedding": lambda: importlib.import_module("quality_gate_embedding"),
    "verify_execution": lambda: importlib.import_module("verify_execution"),
    "verify_execution_shapes": lambda: importlib.import_module("verify_execution_shapes"),
}
MODULES = tuple(PACKAGE_LOADERS)

# Classes a caller catches or constructs by name; a split here means an error
# raised through one import name is not caught through the other.
SHARED_CLASSES = (
    ("card_schema", "CardSchemaError"),
    ("next_round", "RoundExistsError"),
    ("next_round", "TransactionError"),
    ("quality_gate_audit", "AuditOptions"),
)


def in_fresh_interpreters(target, calls: list[tuple]) -> list[Any]:
    """``target(*args)`` for each ``args`` in ``calls``, each in its own spawned interpreter."""

    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=FRESH_INTERPRETER_WORKERS, mp_context=context, max_tasks_per_child=1
    ) as pool:
        futures = [pool.submit(target, *args) for args in calls]
        return [future.result(timeout=FRESH_INTERPRETER_TIMEOUT_SECONDS) for future in futures]


def _interpreter_prefixes() -> tuple[Path, ...]:
    prefixes = (sys.base_prefix, sys.base_exec_prefix, sys.prefix, sys.exec_prefix)
    return tuple(Path(prefix).resolve() for prefix in prefixes)


def _isolated_entry(entry: str, prefixes: tuple[Path, ...]) -> bool:
    """Whether ``python -I`` would start with ``entry``: the interpreter's own library."""

    if not entry:
        return False
    path = Path(entry).resolve()
    if path.is_relative_to(REPO):
        return False
    return any(path.is_relative_to(prefix) for prefix in prefixes)


def isolate() -> None:
    """Forget every repository module and every ``sys.path`` entry ``python -I`` lacks."""

    for name, module in list(sys.modules.items()):
        location = getattr(module, "__file__", None) or ""
        if name != __name__ and location.startswith(str(REPO)):
            del sys.modules[name]
    prefixes = _interpreter_prefixes()
    sys.path[:] = [entry for entry in sys.path if _isolated_entry(entry, prefixes)]


def _put_first(directory: Path) -> None:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))


def _package_then_flat(name: str) -> None:
    PACKAGE_LOADERS[name]()
    _put_first(PIPELINES)
    FLAT_LOADERS[name]()


def _flat_then_package(name: str) -> None:
    FLAT_LOADERS[name]()
    _put_first(REPO)
    PACKAGE_LOADERS[name]()


def _package_first(name: str) -> None:
    """A package consumer first, from the repository root; the CLI path comes later."""

    _put_first(REPO)
    _package_then_flat(name)


def _package_first_both_paths(name: str) -> None:
    """The package name first with ``pipelines/`` already on ``sys.path``, as in the test runner."""

    _put_first(REPO)
    _put_first(PIPELINES)
    _package_then_flat(name)


def _direct_first(name: str) -> None:
    """``python3 pipelines/x.py`` first, before anything has imported ``pipelines``."""

    _put_first(PIPELINES)
    _flat_then_package(name)


def _direct_first_package_loaded(name: str) -> None:
    """The bare name first after ``pipelines`` itself is loaded, so the package branch runs."""

    _put_first(REPO)
    _put_first(PIPELINES)
    importlib.import_module("pipelines")
    _flat_then_package(name)


FORMS = {
    "package_first": _package_first,
    "package_first_both_paths": _package_first_both_paths,
    "direct_first": _direct_first,
    "direct_first_package_loaded": _direct_first_package_loaded,
}


def _flat_name(module: object) -> str | None:
    """The bare import name of a module loaded from ``pipelines/``, or None."""

    origin = getattr(module, "__file__", None)
    if not origin:
        return None
    path = Path(origin).resolve()
    if not path.is_relative_to(PIPELINES):
        return None
    parts = list(path.relative_to(PIPELINES).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or None


def _split_reason(name: str, bindings: dict[str, ModuleType]) -> str | None:
    """Why ``name`` is not one object under both spellings, or None when it is."""

    if len({id(module) for module in bindings.values()}) > 1:
        return "two_objects"
    if name not in bindings or f"pipelines.{name}" not in bindings:
        return "one_name_only"
    return None


def closure_report() -> dict[str, Any]:
    """Every pipelines module now loaded, and those not one object under both names.

    ``one_name_only`` is a latent split: the module is bound under one spelling, so
    importing the other spelling would load a second copy.
    """

    bound: dict[str, dict[str, ModuleType]] = {}
    for key, module in list(sys.modules.items()):
        name = _flat_name(module)
        if name is not None:
            bound.setdefault(name, {})[key] = module
    reasons = {name: _split_reason(name, bindings) for name, bindings in bound.items()}
    return {
        "loaded": sorted(bound),
        "split": {name: reason for name, reason in sorted(reasons.items()) if reason},
    }


def run_closure(form: str, name: str) -> dict[str, Any]:
    """Import ``name`` under both spellings in ``form`` and report the loaded closure."""

    isolate()
    FORMS[form](name)
    return {"form": form, "module": name, **closure_report()}


def _card_schema_error_caught(card_schema: ModuleType, error: type) -> bool:
    """Whether ``except error`` catches what the package-form validator raises."""

    try:
        card_schema.validate([], "dataset")
    except error:
        return True
    except card_schema.CardSchemaError:
        return False
    return False


def run_shared_objects() -> dict[str, bool]:
    """The package form first, then each helper's bare name: one class, one sentinel each."""

    isolate()
    _put_first(REPO)
    _put_first(PIPELINES)
    card_schema = importlib.import_module("pipelines.card_schema")
    audit = importlib.import_module("pipelines.quality_gate_audit")
    importlib.import_module("pipelines.verify_execution")
    shapes = importlib.import_module("pipelines.verify_execution_shapes")
    core = importlib.import_module("card_schema_core")
    identity = importlib.import_module("quality_gate_identity")
    packaged_identity = importlib.import_module("pipelines.quality_gate_identity")
    records = importlib.import_module("check_records")
    packaged_records = importlib.import_module("pipelines.check_records")
    return {
        "card_schema_error_caught": _card_schema_error_caught(card_schema, core.CardSchemaError),
        "card_schema_error_one_class": card_schema.CardSchemaError is core.CardSchemaError,
        "gate_snn_carrier_sentinel": (
            identity._NO_GATE_SNN_CARRIER is packaged_identity._NO_GATE_SNN_CARRIER
        ),
        "canonical_primitive_sentinel": (
            identity._NOT_CANONICAL_PRIMITIVE is packaged_identity._NOT_CANONICAL_PRIMITIVE
        ),
        "record_hash": audit.record_hash is identity.record_hash,
        "factory_staging": records.FactoryStaging is packaged_records.FactoryStaging,
        "safety_module": shapes._safety is importlib.import_module("verify_execution_safety"),
    }


def caught_across(raiser: dict[str, ModuleType], catcher: dict[str, ModuleType]) -> bool:
    """Whether ``catcher``'s ``CardSchemaError`` catches what ``raiser``'s validator raises."""

    try:
        raiser["card_schema_validate"].validate([], "dataset")
    except catcher["card_schema"].CardSchemaError:
        return True
    except raiser["card_schema"].CardSchemaError:
        return False
    return False
