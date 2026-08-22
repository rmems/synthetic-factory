#!/usr/bin/env python3
"""Shared payload-first record-kind classifier.

Census, identity, and agentic consume this one order so overlapping keys do
not grow a fourth classifier. ``legacy_preference`` is an agentic skip
subkind applied after this function returns ``preference``.
"""

from __future__ import annotations

from typing import Any, Mapping

THALAMIC_REQUIRED = (
    "state",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "reward_components",
)

KIND_ORDER = (
    "thalamic",
    "preference",
    "bridge_pair",
    "safety_case",
    "multi_agent",
    "episode",
    "unknown",
)


def classify_kind(obj: Any) -> str:
    """Name a record from payload keys, never from a directory slug.

    Order (census/agentic, issue #32 comment 5377279101):

    1. thalamic — all six ``THALAMIC_REQUIRED`` keys at top level
    2. preference — ``chosen`` and ``rejected``
    3. bridge_pair — ``language_view`` and ``spike_events``
    4. safety_case — ``case_type``
    5. multi_agent — ``transcript`` and ``agents``
    6. episode — ``goal`` and ``steps``
    7. unknown
    """

    if not isinstance(obj, Mapping):
        return "unknown"
    if all(key in obj for key in THALAMIC_REQUIRED):
        return "thalamic"
    if "chosen" in obj and "rejected" in obj:
        return "preference"
    if "language_view" in obj and "spike_events" in obj:
        return "bridge_pair"
    if "case_type" in obj:
        return "safety_case"
    if "transcript" in obj and "agents" in obj:
        return "multi_agent"
    if "goal" in obj and "steps" in obj:
        return "episode"
    return "unknown"
