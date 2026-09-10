#!/usr/bin/env python3
"""Observable-decision and hidden-reasoning measurements for training audits."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable
from typing import Any, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_reasoning")
    from .curate_coding import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        normalized_key_name,
    )
    from .validate_run import HIDDEN_THOUGHT_KEYS, episode_like
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_reasoning"
    )
    from curate_coding import (
        HIDDEN_REASONING_KEYS,
        HIDDEN_REASONING_PREFIX,
        normalized_key_name,
    )
    from validate_run import HIDDEN_THOUGHT_KEYS, episode_like


CURATED_FORBIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | HIDDEN_REASONING_KEYS


class AgenticTurnReaders(NamedTuple):
    """Live facade seams used while enumerating observable agentic turns."""

    list_field: Callable[[Any, str], Iterable[Any]]
    preference_turns: Callable[[Any], Iterable[Any]]
    coordination_turns: Callable[[Any], Iterable[Any]]
    embedded_episodes: Callable[[Any, str], Iterable[tuple[str, dict[str, Any]]]]


def dict_field(value, key):
    """Return a nested mapping, treating malformed values as absent."""
    nested = value.get(key) if isinstance(value, dict) else None
    return nested if isinstance(nested, dict) else {}


def list_field(value, key):
    """Return a nested list, treating malformed values as absent."""
    items = value.get(key) if isinstance(value, dict) else None
    return items if isinstance(items, list) else ()


def preference_turns(
    obj,
    *,
    mapping_reader=dict_field,
    episode_check=episode_like,
    list_reader=list_field,
):
    for side_name in ("chosen", "rejected"):
        side = mapping_reader(obj, side_name)
        if episode_check(side):
            yield from list_reader(side, "steps")


def coordination_turns(obj, *, list_reader=list_field):
    return (
        turn
        for turn in list_reader(obj, "transcript")
        if isinstance(turn, dict) and "tool_call" in turn
    )


def agentic_turns(
    obj,
    kind,
    readers,
):
    """Yield each observable decision turn used by agentic curation."""
    if kind in {"episode", "safety_case"}:
        yield from readers.list_field(obj, "steps")
    elif kind == "preference":
        yield from readers.preference_turns(obj)
    elif kind == "multi_agent":
        yield from readers.coordination_turns(obj)
    for _path, episode in readers.embedded_episodes(obj, kind):
        yield from readers.list_field(episode, "steps")


def has_observable_decision_basis(turn):
    basis = turn.get("decision_basis") if isinstance(turn, dict) else None
    return isinstance(basis, str) and bool(basis.strip())


def is_hidden_thought_key(key):
    """Return whether a JSON key names model-private reasoning text."""
    normalized = normalized_key_name(key)
    return normalized in CURATED_FORBIDDEN_REASONING_KEYS or normalized.startswith(
        HIDDEN_REASONING_PREFIX
    )


def _mapping_children(value, path):
    return (
        (key, item, f"{path}.{key}" if path else key)
        for key, item in value.items()
    )


def _sequence_children(value, path):
    return ((None, item, f"{path}[{index}]") for index, item in enumerate(value))


def _child_nodes(value, path):
    if isinstance(value, dict):
        return _mapping_children(value, path)
    if isinstance(value, list):
        return _sequence_children(value, path)
    return ()


def hidden_thought_paths(value, path="", *, key_classifier=is_hidden_thought_key):
    """Yield every recursively hidden-reasoning field in one record."""
    for key, item, child_path in _child_nodes(value, path):
        if key is not None and key_classifier(key):
            yield child_path
        yield from hidden_thought_paths(item, child_path, key_classifier=key_classifier)


if __package__:
    _expose_package_sibling(__name__)
