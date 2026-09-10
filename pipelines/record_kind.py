#!/usr/bin/env python3
"""Shared payload-first record-kind classifier.

Census, identity, and agentic consume this one order so overlapping keys do
not grow a fourth classifier. Agentic preference subkinds are applied after
this function returns ``preference``.
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
    "code_repair",
    "thalamic",
    "preference",
    "bridge_pair",
    "safety_case",
    "multi_agent",
    "episode",
    "unknown",
)

SUPPORTED_RECORD_KINDS = frozenset(KIND_ORDER) - {"unknown"}

PREFERENCE_SIDE_KINDS = frozenset({"episode", "thalamic"})

_PAYLOAD_KEY_RULES = (
    ("thalamic", frozenset(THALAMIC_REQUIRED)),
    ("preference", frozenset({"chosen", "rejected"})),
    ("bridge_pair", frozenset({"language_view", "spike_events"})),
    ("safety_case", frozenset({"case_type"})),
    ("multi_agent", frozenset({"transcript", "agents"})),
    ("episode", frozenset({"goal", "steps"})),
)


def classify_kind(obj: Any) -> str:
    """Name a record from payload keys, never from a directory slug.

    Order (census/agentic, issue #32 comment 5377279101):

    1. code_repair — ``family`` is ``python-function-repair``
    2. thalamic — all six ``THALAMIC_REQUIRED`` keys at top level
    3. preference — ``chosen`` and ``rejected``
    4. bridge_pair — ``language_view`` and ``spike_events``
    5. safety_case — ``case_type``
    6. multi_agent — ``transcript`` and ``agents``
    7. episode — ``goal`` and ``steps``
    8. unknown
    """

    kind = "unknown"
    if isinstance(obj, Mapping):
        # A malformed claimant stays in its family and fails that family's validator.
        if obj.get("family") == "python-function-repair":
            kind = "code_repair"
        else:
            keys = obj.keys()
            kind = next(
                (name for name, required in _PAYLOAD_KEY_RULES if required <= keys),
                "unknown",
            )
    return kind


def preference_side_kinds(record: Any) -> tuple[str, str]:
    """Classify chosen/rejected trajectories within a preference wrapper.

    Agentic preference records may keep their shared goal on the wrapper, so
    a side with ``steps`` inherits that goal for shape classification.  The
    caller remains responsible for validating the goal value and requiring a
    homogeneous pair.
    """

    if not isinstance(record, Mapping):
        return "unknown", "unknown"
    wrapper_has_goal = "goal" in record
    kinds: list[str] = []
    for name in ("chosen", "rejected"):
        side = record.get(name)
        kind = classify_kind(side)
        if (
            kind == "unknown"
            and wrapper_has_goal
            and isinstance(side, Mapping)
            and "steps" in side
        ):
            kind = "episode"
        kinds.append(kind)
    return kinds[0], kinds[1]
