#!/usr/bin/env python3
"""Inspect the shape of one agentic record, without deciding anything about it.

Everything here reads a single decoded record and answers a structural
question: which agentic kind is it, does it hide a chain-of-thought key, do
its preference sides describe one problem, which of its turns lack an
observable ``decision_basis``, how much of its step prefix is shared. None of
these functions curate, exclude, count, or write; turning their answers into
a curation decision is ``curate_agentic.py``'s job.

The canonical-JSON and hashing primitives live here too, because record
identity is a property of record shape and both the decision pass and the
output writer need them.

Split out of ``curate_agentic.py`` verbatim; every public name is re-exported
from ``curate_agentic`` so existing ``from curate_agentic import
classify_record`` call sites resolve unchanged.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from coding_constants import HIDDEN_REASONING_KEYS, HIDDEN_REASONING_PREFIX
from record_kind import (
    classify_kind as classify_payload_kind,
    preference_side_kinds,
)

HIDDEN_THOUGHT_KEYS = frozenset(
    {"thought", "chain_of_thought", "scratch", "inner_monologue"}
)
# training_audit.is_hidden_thought_key refuses HIDDEN_THOUGHT_KEYS *and*
# coding_constants.HIDDEN_REASONING_KEYS (the coding-factory ``reasoning``
# key plus the ``internal_reasoning*`` family Thalamic wrap records carry),
# via an exact-or-prefix match. A multi_agent or safety_case record this
# lane retains without stripping one of those keys would still fail that
# stricter audit downstream, so the stripper below must refuse the same
# union, not just the narrower scratch-pad vocabulary.
FORBIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | HIDDEN_REASONING_KEYS

INVALID_PREFERENCE_KIND = "invalid_preference"

# The preference-goal verdicts ``shared_preference_goal`` returns. They live
# here rather than with the rest of the curation reason vocabulary because
# they are this module's own return values; ``curate_agentic`` re-exports them
# so callers still import one curation vocabulary from one place.
REASON_GOAL_DIVERGES = "PREFERENCE_GOAL_DIVERGES"
REASON_GOAL_MISSING = "PREFERENCE_GOAL_MISSING"
REASON_GOAL_NOT_TEXT = "PREFERENCE_GOAL_NOT_TEXT"
REASON_SIDES_NOT_OBJECTS = "PREFERENCE_SIDES_NOT_OBJECTS"


def canonical_json(value: Any) -> str:
    """Stable JSON used for hashes and step-prefix equality."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def hash_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalized_key_name(value: Any) -> str:
    """Normalize JSON keys across case, separators, and camel-case boundaries."""
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value)).casefold(),
    ).strip("_")


def _is_forbidden_reasoning_key(key: Any) -> bool:
    """Whether a JSON key names model-private reasoning text.

    Mirrors ``training_audit.is_hidden_thought_key`` exactly: the shared
    scratch-pad vocabulary, the exact coding-factory key ``reasoning``, and
    the whole ``internal_reasoning*`` family.
    """
    normalized = normalized_key_name(key)
    return normalized in FORBIDDEN_REASONING_KEYS or normalized.startswith(
        HIDDEN_REASONING_PREFIX
    )


def contains_hidden_thought_key(value: Any) -> bool:
    """Return whether any nested mapping exposes a banned hidden-thought key."""
    if isinstance(value, dict):
        return any(
            _is_forbidden_reasoning_key(key) for key in value
        ) or any(contains_hidden_thought_key(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_hidden_thought_key(item) for item in value)
    return False


def _strip_mapping(value: dict) -> tuple[dict[str, Any], int]:
    """Strip one mapping level, recursing into its surviving values."""
    cleaned: dict[str, Any] = {}
    removed = 0
    for key, item in value.items():
        if _is_forbidden_reasoning_key(key):
            removed += 1
            continue
        clean_item, nested = strip_hidden_thought_keys(item)
        cleaned[key] = clean_item
        removed += nested
    return cleaned, removed


def _strip_sequence(value: list) -> tuple[list[Any], int]:
    """Strip every element of a list, preserving order."""
    cleaned_items = []
    removed = 0
    for item in value:
        clean_item, nested = strip_hidden_thought_keys(item)
        cleaned_items.append(clean_item)
        removed += nested
    return cleaned_items, removed


def strip_hidden_thought_keys(value: Any) -> tuple[Any, int]:
    """Deep-copy ``value`` while removing banned hidden-thought keys."""
    if isinstance(value, dict):
        return _strip_mapping(value)
    if isinstance(value, list):
        return _strip_sequence(value)
    return copy.deepcopy(value), 0


def _preference_kind(obj: Any) -> str:
    """Route a record the payload classifier called ``preference``.

    Legacy Thalamic preference pairs deliberately have chosen/rejected
    trajectory objects rather than agentic episode sides. They belong in the
    skipped bucket, not in the agentic goal-impurity statistics.
    """
    sides = (obj.get("chosen"), obj.get("rejected"))
    if not all(isinstance(side, dict) for side in sides):
        return "preference"
    side_kinds = preference_side_kinds(obj)
    if side_kinds == ("thalamic", "thalamic"):
        return "legacy_preference"
    if side_kinds == ("episode", "episode"):
        return "preference"
    if any(side_kind != "unknown" for side_kind in side_kinds):
        return INVALID_PREFERENCE_KIND
    return "preference"


def classify_record(obj: Any) -> str:
    """Route a record to an agentic kind, or a skippable non-agentic kind.

    Kind order is the shared payload classifier. ``legacy_preference`` remains
    an agentic skip subkind after that function returns ``preference``.
    """
    kind = classify_payload_kind(obj)
    return _preference_kind(obj) if kind == "preference" else kind


def record_identifier(record: Any) -> str | None:
    """Return the record's own id, falling back to ``meta.id``."""
    if not isinstance(record, dict):
        return None
    for container in (record, record.get("meta")):
        if not isinstance(container, dict):
            continue
        value = container.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _norm_goal(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.split())
    return normalized or None


def preference_goals(record: dict[str, Any]) -> tuple[str | None, ...]:
    """Return (top, chosen, rejected) normalized goals; missing sides are None."""
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    top = _norm_goal(record.get("goal"))
    chosen_goal = (
        _norm_goal(chosen.get("goal")) if isinstance(chosen, dict) else None
    )
    rejected_goal = (
        _norm_goal(rejected.get("goal")) if isinstance(rejected, dict) else None
    )
    return top, chosen_goal, rejected_goal


def _side_goal_uncovered(
    top: str | None, chosen_goal: str | None, rejected_goal: str | None
) -> bool:
    """True when a side goal is missing and no top-level goal stands in for it."""
    if top is not None:
        return False
    return chosen_goal is None or rejected_goal is None


def _goal_agreement(
    top: str | None, chosen_goal: str | None, rejected_goal: str | None
) -> tuple[bool, str | None]:
    """Judge the three normalized goals once they are known to be text."""
    present = [
        goal for goal in (top, chosen_goal, rejected_goal) if goal is not None
    ]
    if not present:
        return False, REASON_GOAL_MISSING
    if _side_goal_uncovered(top, chosen_goal, rejected_goal):
        return False, REASON_GOAL_MISSING
    if len(set(present)) != 1:
        return False, REASON_GOAL_DIVERGES
    return True, None


def shared_preference_goal(record: dict[str, Any]) -> tuple[bool, str | None]:
    """Whether chosen/rejected describe one problem.

    A shared goal is required. Top-level ``goal`` may stand in for a missing
    side goal. Any present goals must be identical after whitespace normalize.
    """
    chosen = record.get("chosen")
    rejected = record.get("rejected")
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        return False, REASON_SIDES_NOT_OBJECTS
    raw_goals = (
        record.get("goal"),
        chosen.get("goal"),
        rejected.get("goal"),
    )
    if any(value is not None and _norm_goal(value) is None for value in raw_goals):
        return False, REASON_GOAL_NOT_TEXT
    return _goal_agreement(*preference_goals(record))


def _basis_missing(step: Any) -> bool:
    if not isinstance(step, dict):
        return True
    basis = step.get("decision_basis")
    return not (isinstance(basis, str) and basis.strip())


def _step_locations(prefix: str, owner: Any) -> list[tuple[str, Any]]:
    """Return the ``steps`` array turn sites of one record or preference side."""
    if not isinstance(owner, dict):
        return []
    steps = owner.get("steps")
    if not isinstance(steps, list):
        return []
    return [
        (f"{prefix}steps[{step_index}]", step)
        for step_index, step in enumerate(steps)
    ]


def _transcript_locations(record: dict[str, Any]) -> list[tuple[str, Any]]:
    """Return the tool-using transcript turn sites of one record."""
    transcript = record.get("transcript")
    if not isinstance(transcript, list):
        return []
    return [
        (f"transcript[{turn_index}]", turn)
        for turn_index, turn in enumerate(transcript)
        if isinstance(turn, dict) and "tool_call" in turn
    ]


def iter_turn_locations(record: Any) -> list[tuple[str, Any]]:
    """ToolMind-style turn sites: ``steps`` arrays and tool-using transcript turns."""
    if not isinstance(record, dict):
        return []
    locations = list(_step_locations("", record))
    for side in ("chosen", "rejected"):
        locations.extend(_step_locations(f"{side}.", record.get(side)))
    locations.extend(_transcript_locations(record))
    return locations


def missing_decision_basis_paths(record: Any) -> list[str]:
    """Return turn paths that lack a non-empty observable ``decision_basis``."""
    return [
        path
        for path, step in iter_turn_locations(record)
        if _basis_missing(step)
    ]


def _shared_step_prefix(chosen_steps: list, rejected_steps: list) -> int:
    """Count leading steps that are identical once hidden thoughts are stripped."""
    shared = 0
    for left, right in zip(chosen_steps, rejected_steps):
        clean_left, _ = strip_hidden_thought_keys(left)
        clean_right, _ = strip_hidden_thought_keys(right)
        if canonical_json(clean_left) != canonical_json(clean_right):
            break
        shared += 1
    return shared


def prefix_overlap(chosen: Any, rejected: Any) -> dict[str, Any]:
    """Count leading thought-stripped steps shared by chosen and rejected.

    Zero overlap is recorded and is not a fail. A positive count is an
    optional purity note: DPO prefers a shared prefix and a suffix contrast.
    """
    chosen_steps = chosen.get("steps") if isinstance(chosen, dict) else None
    rejected_steps = rejected.get("steps") if isinstance(rejected, dict) else None
    chosen_len = len(chosen_steps) if isinstance(chosen_steps, list) else 0
    rejected_len = len(rejected_steps) if isinstance(rejected_steps, list) else 0
    shared = (
        _shared_step_prefix(chosen_steps, rejected_steps)
        if isinstance(chosen_steps, list) and isinstance(rejected_steps, list)
        else 0
    )
    return {
        "shared_steps": shared,
        "chosen_steps": chosen_len,
        "rejected_steps": rejected_len,
        "noted": shared > 0,
    }
