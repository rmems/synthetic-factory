"""Structural record checks. The acceptance gate re-measures what this only shapes."""

from __future__ import annotations

from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .validate_body import provenance_codes, trajectory_codes
from .validate_preds import exact_keys, nonneg_int, text_ok

__all__ = ["validate_record", "validate_text"]


def _key_codes(record: dict) -> tuple[str, ...]:
    extra = set(record) - set(cv.RECORD_KEYS)
    if extra:
        return ("record.keys",)
    return tuple(key for key in cv.RECORD_KEYS if key not in record)


def _record_id_ok(record_id: object) -> bool:
    if not text_ok(record_id):
        return False
    if len(record_id) > 80:
        return False
    return record_id.startswith("stop-")


def _identity(record: dict) -> tuple[str, ...]:
    found = []
    if not _record_id_ok(record["record_id"]):
        found.append("record_id")
    if record["family"] != cv.FAMILY:
        found.append("family")
    if not text_ok(record["task"]):
        found.append("task")
    return tuple(found)


def _context(record: dict) -> tuple[str, ...]:
    context = record["context"]
    if not exact_keys(context, cv.CONTEXT_KEYS):
        return ("context",)
    found = []
    if not text_ok(context["scenario_id"]):
        found.append("context.scenario_id")
    if not nonneg_int(context["seed"]):
        found.append("context.seed")
    if not text_ok(context["task_id"]):
        found.append("context.task_id")
    if context["world"] != cv.WORLD:
        found.append("context.world")
    return tuple(found)


def _action(record: dict) -> tuple[str, ...]:
    action = record["correct_action"]
    if not exact_keys(action, cv.ACTION_KEYS):
        return ("correct_action",)
    found = []
    if action["type"] not in cv.ACTION_TYPES:
        found.append("correct_action.type")
    if not text_ok(action["message"]):
        found.append("correct_action.message")
    return tuple(found)


def _counterfactual(record: dict) -> tuple[str, ...]:
    value = record["counterfactual_fake_success"]
    if not isinstance(value, str):
        return ("counterfactual_fake_success",)
    if not value.strip():
        return ("counterfactual_fake_success",)
    return ()


def _result(record: dict) -> tuple[str, ...]:
    result = record["result"]
    if not exact_keys(result, cv.RESULT_KEYS):
        return ("result",)
    if isinstance(result["verified_blocker"], bool):
        return ()
    return ("result.verified_blocker",)


def _fields(record: dict) -> tuple[str, ...]:
    found: list[str] = []
    found.extend(_identity(record))
    found.extend(_context(record))
    found.extend(trajectory_codes(record))
    found.extend(_action(record))
    found.extend(_counterfactual(record))
    found.extend(_result(record))
    found.extend(provenance_codes(record))
    return tuple(found)


def validate_record(record: Any) -> tuple[str, ...]:
    """Return stable codes for structural problems. An empty tuple is well-shaped."""

    if not isinstance(record, dict):
        return ("record.type",)
    missing = _key_codes(record)
    if missing:
        return missing
    return _fields(record)


def validate_text(text: str) -> tuple[str, ...]:
    """Parse strict JSON, then :func:`validate_record`."""

    try:
        record = load_strict_json(text)
    except ValueError, RecursionError:
        return ("record.json",)
    return validate_record(record)


bind_import_twin(__name__)
