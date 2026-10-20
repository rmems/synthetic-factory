"""Structural record checks. The acceptance gate re-measures what this only shapes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json

__all__ = ["validate_record", "validate_text"]

_DIGEST_PREFIX = "sha256:"
_DIGEST_WIDTH = 64


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonneg(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value >= 0


def _exact(value: Any, keys: tuple[str, ...]) -> bool:
    return isinstance(value, dict) and set(value) == set(keys)


def _digest(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith(_DIGEST_PREFIX):
        return False
    body = value[len(_DIGEST_PREFIX) :]
    return (
        len(body) == _DIGEST_WIDTH
        and body == body.lower()
        and all(character in "0123456789abcdef" for character in body)
    )


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return False
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value


def _key_codes(record: dict) -> tuple[str, ...]:
    extra = set(record) - set(cv.RECORD_KEYS)
    if extra:
        return ("record.keys",)
    return tuple(key for key in cv.RECORD_KEYS if key not in record)


def _identity(record: dict) -> tuple[str, ...]:
    found = []
    record_id = record["record_id"]
    if not _text(record_id) or len(record_id) > 80 or not record_id.startswith("stop-"):
        found.append("record_id")
    if record["family"] != cv.FAMILY:
        found.append("family")
    if not _text(record["task"]):
        found.append("task")
    return tuple(found)


def _context(record: dict) -> tuple[str, ...]:
    context = record["context"]
    if not _exact(context, cv.CONTEXT_KEYS):
        return ("context",)
    found = []
    if not _text(context["scenario_id"]):
        found.append("context.scenario_id")
    if not _nonneg(context["seed"]):
        found.append("context.seed")
    if not _text(context["task_id"]):
        found.append("context.task_id")
    if context["world"] != cv.WORLD:
        found.append("context.world")
    return tuple(found)


def _arg_value(value: Any) -> bool:
    if isinstance(value, (bool, str)):
        return True
    return isinstance(value, int)


def _args_ok(args: Any) -> bool:
    if not isinstance(args, dict):
        return False
    return all(isinstance(key, str) and key and _arg_value(item) for key, item in args.items())


def _tool_call(call: Any) -> tuple[str, ...]:
    if not _exact(call, cv.TOOL_CALL_KEYS):
        return ("trajectory.tool_call",)
    if not _text(call["name"]) or not _args_ok(call["args"]):
        return ("trajectory.tool_call",)
    return ()


def _index_ok(value: Any, index: int) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value == index


def _step(step: Any, index: int) -> tuple[str, ...]:
    if not _exact(step, cv.STEP_KEYS):
        return ("trajectory.step",)
    found = []
    if not _index_ok(step["n"], index):
        found.append("trajectory.n")
    found.extend(_tool_call(step["tool_call"]))
    if not isinstance(step["observation"], str) or step["observation"] == "":
        found.append("trajectory.observation")
    return tuple(found)


def _trajectory(record: dict) -> tuple[str, ...]:
    steps = record["trajectory"]
    if not isinstance(steps, list) or not steps or len(steps) > cv.MAX_STEPS:
        return ("trajectory",)
    found: list[str] = []
    for index, step in enumerate(steps, start=1):
        found.extend(_step(step, index))
    return tuple(found)


def _action(record: dict) -> tuple[str, ...]:
    action = record["correct_action"]
    if not _exact(action, cv.ACTION_KEYS):
        return ("correct_action",)
    found = []
    if action["type"] not in cv.ACTION_TYPES:
        found.append("correct_action.type")
    if not _text(action["message"]):
        found.append("correct_action.message")
    return tuple(found)


def _counterfactual(record: dict) -> tuple[str, ...]:
    value = record["counterfactual_fake_success"]
    if not isinstance(value, str) or not value.strip():
        return ("counterfactual_fake_success",)
    return ()


def _result(record: dict) -> tuple[str, ...]:
    result = record["result"]
    if not _exact(result, cv.RESULT_KEYS):
        return ("result",)
    if not isinstance(result["verified_blocker"], bool):
        return ("result.verified_blocker",)
    return ()


def _actor(actor: Any) -> bool:
    if not _exact(actor, cv.ACTOR_KEYS):
        return False
    return _text(actor["role"]) and _text(actor["name"]) and _digest(actor["digest"])


def _actors(provenance: dict) -> tuple[str, ...]:
    actors = provenance["actors"]
    if not isinstance(actors, list) or not actors or not all(_actor(item) for item in actors):
        return ("provenance.actors",)
    return ()


def _parent_ids(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _lineage(provenance: dict) -> tuple[str, ...]:
    lineage = provenance["lineage"]
    if not _exact(lineage, cv.LINEAGE_KEYS):
        return ("provenance.lineage",)
    if not _text(lineage["scenario_id"]) or not _text(lineage["builder"]):
        return ("provenance.lineage",)
    if not _nonneg(lineage["seed"]) or not _nonneg(lineage["run_seed"]):
        return ("provenance.lineage",)
    if not _digest(lineage["config_sha256"]) or not _parent_ids(lineage["parent_ids"]):
        return ("provenance.lineage",)
    return ()


def _provenance(record: dict) -> tuple[str, ...]:
    provenance = record["provenance"]
    if not _exact(provenance, cv.PROVENANCE_KEYS):
        return ("provenance",)
    found = []
    if not _timestamp(provenance["produced_at"]):
        found.append("provenance.produced_at")
    found.extend(_actors(provenance))
    found.extend(_lineage(provenance))
    return tuple(found)


def _fields(record: dict) -> tuple[str, ...]:
    found: list[str] = []
    for check in (_identity, _context, _trajectory, _action, _counterfactual, _result, _provenance):
        found.extend(check(record))
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
    except ValueError, RecursionError, UnicodeError:
        return ("record.json",)
    return validate_record(record)


bind_import_twin(__name__)
