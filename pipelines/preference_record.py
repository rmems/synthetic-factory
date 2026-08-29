#!/usr/bin/env python3
"""Decide the fate of one preference pair, in isolation from any corpus.

``curate_preference_record`` is a pure function of a single record. A pair is
retained only when ``chosen`` and ``rejected`` have canonically identical
``state`` and ``proposed_action`` values. An impure pair is handed to the
attested-identity repair rules in ``preference_repair``; if none of them can
prove the identity, the pair is excluded with machine-readable reason codes
derived from exactly which canonical paths diverged.

Source-side agreement is recorded per canonical context field *before* any
repair, so a repaired pair never launders itself into the same-context
counters. The scan in ``curate_preferences.py`` only tallies what these
decisions report; it never re-derives them.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_context import (  # noqa: E402
    _all_context_diffs,
    _preference_context,
    context_field_agreement,
    context_is_pure,
)
from preference_model import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_RETAINED,
    CurationDecision,
    is_canonicalizable as _is_canonicalizable,
)
from preference_repair import (  # noqa: E402
    repair_attested_identity,
    repair_attested_proposal,
)

__all__ = [
    "context_field_agreement",
    "context_is_pure",
    "curate_preference_record",
]


def _paths_with_prefix(paths: tuple[str, ...], prefix: str) -> list[str]:
    return [path for path in paths if path.startswith(prefix)]


def _state_exclusion_reason(state_paths: list[str]) -> str | None:
    if not state_paths:
        return None
    if set(state_paths).issubset({"state.episode_id", "state.note"}):
        return "BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE"
    if any(path.startswith("state.agent.gate_memory") for path in state_paths):
        return "POLICY_MEMORY_CONTEXT_DIVERGES"
    return "STATE_CONTEXT_DIVERGES"


def _exclusion_reasons(context_diff_paths: tuple[str, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    state_reason = _state_exclusion_reason(_paths_with_prefix(context_diff_paths, "state"))
    if state_reason is not None:
        reasons.append(state_reason)
    if _paths_with_prefix(context_diff_paths, "proposed_action"):
        reasons.append("PROPOSED_ACTION_CONTEXT_DIVERGES")
    if reasons:
        return tuple(reasons)
    return ("PREFERENCE_CONTEXT_DIVERGES",)


def curate_preference_record(record: dict[str, Any]) -> CurationDecision:
    """Curate one pair without mutating ``record``."""

    if not isinstance(record, dict):
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_RECORD_NOT_AN_OBJECT",),
            record=None,
            context_diff_paths=(),
        )
    same_state, same_proposed_action = context_field_agreement(record)
    if not _is_canonicalizable(record):
        # Checked before the context shape so a non-finite float anywhere in
        # the pair is reported precisely instead of surfacing as a bare
        # ValueError from the first canonical comparison.
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",),
            record=None,
            context_diff_paths=(),
            same_state=same_state,
            same_proposed_action=same_proposed_action,
        )
    context = _preference_context(record)
    if context is None:
        return CurationDecision(
            action=ACTION_EXCLUDED,
            classification="malformed_preference_context",
            reason_codes=("PREFERENCE_CONTEXT_MISSING_OR_INVALID",),
            record=None,
            context_diff_paths=(),
            same_state=same_state,
            same_proposed_action=same_proposed_action,
        )

    chosen, rejected = context
    context_diff_paths = _all_context_diffs(chosen, rejected)
    if not context_diff_paths:
        return CurationDecision(
            action=ACTION_RETAINED,
            classification="already_same_context",
            reason_codes=("PREFERENCE_CONTEXT_ALREADY_IDENTICAL",),
            record=copy.deepcopy(record),
            context_diff_paths=(),
            same_state=same_state,
            same_proposed_action=same_proposed_action,
        )

    # Repairs report the agreement of the *source* pair, not of their own
    # output: the audit has to keep naming a repaired pair as impure evidence.
    for repair in (repair_attested_identity, repair_attested_proposal):
        repaired = repair(record)
        if repaired is not None:
            return replace(
                repaired,
                same_state=same_state,
                same_proposed_action=same_proposed_action,
            )

    return CurationDecision(
        action=ACTION_EXCLUDED,
        classification="unsupported_context_divergence",
        reason_codes=_exclusion_reasons(context_diff_paths),
        record=None,
        context_diff_paths=context_diff_paths,
        same_state=same_state,
        same_proposed_action=same_proposed_action,
    )
