#!/usr/bin/env python3
"""Fail-closed checks for mill episodes, pairs, and local run trees."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from . import catalog as cat
from . import vocabulary as cv
from ._contract import bind_import_twin, contains_hidden_reasoning_key

__all__ = ["check_pair", "check_record", "scan_payload"]


def _refuse_banned_entry(key: Any, value: Any, path: str) -> None:
    cv.refuse_when(
        key in cv.BANNED_KEYS,
        cv.FINDING_BANNED_KEY,
        f"banned key {key} at {path}",
    )
    cv.refuse_when(
        key == "sim_or_real" and value == cv.BANNED_SIM_OR_REAL,
        cv.FINDING_BANNED_KEY,
        f"sim_or_real real at {path}",
    )
    cv.refuse_when(
        key == "spike_events",
        cv.FINDING_BANNED_KEY,
        f"spike_events at {path}",
    )


def _scan_text(text: str, path: str) -> None:
    for banned in cv.BANNED_SUBSTRINGS:
        cv.refuse_when(
            banned in text,
            cv.FINDING_BANNED_SUBSTRING,
            f"banned substring {banned!r} at {path}",
        )


def _scan_children(obj: Any, path: str) -> Iterator[tuple[Any, str]]:
    """Each child of a mapping or list with its path; a mapping entry's key is vetted first.

    A generator, so it is suspended (off the stack) while ``scan_payload`` recurses.
    """

    if isinstance(obj, dict):
        for key, value in obj.items():
            _refuse_banned_entry(key, value, path)
            yield value, f"{path}.{key}"
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            yield item, f"{path}[{index}]"


def scan_payload(obj: Any, path: str = "") -> None:
    """Refuse banned keys, hidden-reasoning keys, and banned substrings."""
    if contains_hidden_reasoning_key(obj):
        cv.refuse(cv.FINDING_BANNED_KEY, f"hidden-reasoning key at {path or '/'}")
    if isinstance(obj, str):
        _scan_text(obj, path)
    for child, child_path in _scan_children(obj, path):
        scan_payload(child, child_path)


def _require_mapping(record: Any) -> dict[str, Any]:
    cv.refuse_when(
        not isinstance(record, dict),
        cv.FINDING_INPUT_NOT_AN_OBJECT,
        "record must be an object",
    )
    return record


def _refuse_identity_drift(
    payload: dict[str, Any], meta: Mapping[str, Any], stem: str, success: bool
) -> None:
    """Id, factory, generator, kind, seed, step count, and outcome match the plant side."""
    round_n = meta.get("round")
    expected_id = cv.record_id(round_n, stem) if isinstance(round_n, int) else None
    steps = payload.get("steps")
    expected_steps = cv.SUCCESS_STEPS if success else cv.FAIL_STEPS
    cv.refuse_first((
        (payload.get("id") != expected_id, cv.FINDING_RECORD_MALFORMED,
         f"id {cv.shown(payload.get('id'))} is not {expected_id}"),
        (meta.get("factory") != cv.FACTORY_ID, cv.FINDING_FACTORY_MISMATCH,
         f"factory {cv.shown(meta.get('factory'))} is not {cv.FACTORY_ID}"),
        (meta.get("generator") != cv.GENERATOR_NAME, cv.FINDING_RECORD_MALFORMED,
         f"generator {cv.shown(meta.get('generator'))} is not {cv.GENERATOR_NAME}"),
        (meta.get("kind") != cv.RECORD_KIND, cv.FINDING_RECORD_MALFORMED,
         f"kind {cv.shown(meta.get('kind'))} is not {cv.RECORD_KIND}"),
        (meta.get("seed") != stem, cv.FINDING_RECORD_MALFORMED,
         f"seed {cv.shown(meta.get('seed'))} is not {stem}"),
        (not isinstance(steps, list) or len(steps) != expected_steps, cv.FINDING_STEP_COUNT_INVALID,
         f"steps {len(steps) if isinstance(steps, list) else cv.shown(steps)} != {expected_steps}"),
        (payload.get("reward", {}).get("success") is not success, cv.FINDING_RECORD_MALFORMED,
         f"reward.success is not {success}"),
    ))


def _refuse_step_drift(steps: list[Any]) -> None:
    for index, step in enumerate(steps, start=1):
        cv.refuse_when(not isinstance(step, dict), cv.FINDING_RECORD_MALFORMED, f"step {index} is not an object")
        basis = step.get("decision_basis")
        cv.refuse_when(
            not isinstance(basis, str) or not basis.startswith(cv.DB_PREFIXES),
            cv.FINDING_DECISION_BASIS_INVALID,
            f"step {index} decision_basis prefix",
        )
        cv.refuse_when(
            isinstance(basis, str) and len(basis) > cv.MAX_DECISION_BASIS,
            cv.FINDING_DECISION_BASIS_INVALID,
            f"step {index} decision_basis length {len(basis)}",
        )
        cv.refuse_when(step.get("n") != index, cv.FINDING_RECORD_MALFORMED, f"step {index} n drifted")


def check_record(record: Any, plant: cat.Plant, *, success: bool) -> None:
    """One episode matches the plant, the mill identity, and the step contract."""
    payload = _require_mapping(record)
    scan_payload(payload)
    meta = payload.get("meta")
    if not isinstance(meta, Mapping):
        cv.refuse(cv.FINDING_RECORD_MALFORMED, "meta must be an object")
    stem = plant.plant_id if success else plant.fail_id
    _refuse_identity_drift(payload, meta, stem, success)
    _refuse_step_drift(payload["steps"])


def check_pair(success: Any, failure: Any, plant: cat.Plant, round_n: int) -> None:
    """Both sides of one quota-2 pair belong to ``plant`` at ``round_n``."""
    check_record(success, plant, success=True)
    check_record(failure, plant, success=False)
    cv.refuse_when(
        success["meta"]["round"] != round_n or failure["meta"]["round"] != round_n,
        cv.FINDING_RECORD_MALFORMED,
        f"pair round is not {round_n}",
    )
    cv.refuse_when(
        success["id"] == failure["id"],
        cv.FINDING_RECORD_MALFORMED,
        "pair ids must differ",
    )


bind_import_twin(__name__)
