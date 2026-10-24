"""Trajectory and provenance shape checks for an honest-stop record."""

from __future__ import annotations

from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin
from .validate_preds import digest_ok, exact_keys, nonneg_int, text_ok, timestamp_ok

__all__ = ["provenance_codes", "trajectory_codes"]

_TOOL_CALL = "trajectory.tool_call"
_LINEAGE = "provenance.lineage"


def _arg_value(value: Any) -> bool:
    if isinstance(value, (bool, str)):
        return True
    return isinstance(value, int)


def _arg_item(key: object, item: object) -> bool:
    if not isinstance(key, str):
        return False
    if not key:
        return False
    return _arg_value(item)


def _args_ok(args: Any) -> bool:
    if not isinstance(args, dict):
        return False
    return all(_arg_item(key, item) for key, item in args.items())


def _named_call(call: dict) -> bool:
    if text_ok(call["name"]):
        return _args_ok(call["args"])
    return False


def _tool_call(call: Any) -> tuple[str, ...]:
    if not exact_keys(call, cv.TOOL_CALL_KEYS):
        return (_TOOL_CALL,)
    if _named_call(call):
        return ()
    return (_TOOL_CALL,)


def _index_ok(value: Any, index: int) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value == index


def _observation_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value != ""


def _step(step: Any, index: int) -> tuple[str, ...]:
    if not exact_keys(step, cv.STEP_KEYS):
        return ("trajectory.step",)
    found = []
    if not _index_ok(step["n"], index):
        found.append("trajectory.n")
    found.extend(_tool_call(step["tool_call"]))
    if not _observation_ok(step["observation"]):
        found.append("trajectory.observation")
    return tuple(found)


def _steps_ok(steps: object) -> bool:
    if not isinstance(steps, list):
        return False
    if not steps:
        return False
    return len(steps) <= cv.MAX_STEPS


def trajectory_codes(record: dict) -> tuple[str, ...]:
    steps = record["trajectory"]
    if not _steps_ok(steps):
        return ("trajectory",)
    found: list[str] = []
    for index, step in enumerate(steps, start=1):
        found.extend(_step(step, index))
    return tuple(found)


def _actor(actor: Any) -> bool:
    if not exact_keys(actor, cv.ACTOR_KEYS):
        return False
    if not text_ok(actor["role"]):
        return False
    if not text_ok(actor["name"]):
        return False
    return digest_ok(actor["digest"])


def _actor_list(actors: object) -> bool:
    if not isinstance(actors, list):
        return False
    if not actors:
        return False
    return all(_actor(item) for item in actors)


def _actors(provenance: dict) -> tuple[str, ...]:
    if _actor_list(provenance["actors"]):
        return ()
    return ("provenance.actors",)


def _parent_ids(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(item, str) and item for item in value)


def _lineage_text(lineage: dict) -> bool:
    if text_ok(lineage["scenario_id"]):
        return text_ok(lineage["builder"])
    return False


def _lineage_numbers(lineage: dict) -> bool:
    if nonneg_int(lineage["seed"]):
        return nonneg_int(lineage["run_seed"])
    return False


def _lineage_links(lineage: dict) -> bool:
    if digest_ok(lineage["config_sha256"]):
        return _parent_ids(lineage["parent_ids"])
    return False


def _lineage_fields(lineage: dict) -> bool:
    if not _lineage_text(lineage):
        return False
    if not _lineage_numbers(lineage):
        return False
    return _lineage_links(lineage)


def _lineage(provenance: dict) -> tuple[str, ...]:
    lineage = provenance["lineage"]
    if not exact_keys(lineage, cv.LINEAGE_KEYS):
        return (_LINEAGE,)
    if _lineage_fields(lineage):
        return ()
    return (_LINEAGE,)


def provenance_codes(record: dict) -> tuple[str, ...]:
    provenance = record["provenance"]
    if not exact_keys(provenance, cv.PROVENANCE_KEYS):
        return ("provenance",)
    found = []
    if not timestamp_ok(provenance["produced_at"]):
        found.append("provenance.produced_at")
    found.extend(_actors(provenance))
    found.extend(_lineage(provenance))
    return tuple(found)


bind_import_twin(__name__)
