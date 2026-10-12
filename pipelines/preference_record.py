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
from pathlib import Path
from typing import Any

if __package__:
    from .preference_context import (
        all_context_diffs,
        context_field_agreement,
        context_is_pure,
        is_trajectory_pair,
        pair_context,
    )
    from .preference_model import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        CLASSIFICATION_TRAJECTORY_PAIR,
        REASON_TRAJECTORY_PAIR,
        CurationDecision,
        is_canonicalizable as _is_canonicalizable,
    )
    from .preference_repair import repair_attested_identity, repair_attested_proposal
else:
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from preference_context import (
        all_context_diffs,
        context_field_agreement,
        context_is_pure,
        is_trajectory_pair,
        pair_context,
    )
    from preference_model import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        CLASSIFICATION_TRAJECTORY_PAIR,
        REASON_TRAJECTORY_PAIR,
        CurationDecision,
        is_canonicalizable as _is_canonicalizable,
    )
    from preference_repair import repair_attested_identity, repair_attested_proposal

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


_MALFORMED_CONTEXT = "malformed_preference_context"

#: ``(same_state, same_proposed_action)`` of the source pair, before any repair.
_Agreement = tuple[bool | None, bool | None]


def _excluded_decision(
    classification: str,
    reason_codes: tuple[str, ...],
    agreement: _Agreement,
    context_diff_paths: tuple[str, ...] = (),
) -> CurationDecision:
    """An exclusion that keeps the source pair's per-field agreement."""

    same_state, same_proposed_action = agreement
    return CurationDecision(
        action=ACTION_EXCLUDED,
        classification=classification,
        reason_codes=reason_codes,
        record=None,
        context_diff_paths=context_diff_paths,
        same_state=same_state,
        same_proposed_action=same_proposed_action,
    )


def _absent_context_decision(
    record: dict[str, Any], same_state: Any, same_proposed_action: Any
) -> CurationDecision:
    """Name a pair that carries no same-state context, by the lane that owns it."""

    agreement = (same_state, same_proposed_action)
    if is_trajectory_pair(record):
        # A shared-goal trajectory pair is a different schema, not a
        # malformed same-state pair. Naming that keeps a 0% same-state
        # yield readable and stops anyone from inventing state here.
        return _excluded_decision(
            CLASSIFICATION_TRAJECTORY_PAIR, (REASON_TRAJECTORY_PAIR,), agreement
        )
    return _excluded_decision(
        _MALFORMED_CONTEXT, ("PREFERENCE_CONTEXT_MISSING_OR_INVALID",), agreement
    )


def _repaired_or_excluded(
    record: dict[str, Any],
    agreement: _Agreement,
    context_diff_paths: tuple[str, ...],
) -> CurationDecision:
    """An attested-identity repair of an impure pair, or its coded exclusion."""

    # Repairs are handed the agreement of the *source* pair, not of their own
    # output: the audit has to keep naming a repaired pair as impure evidence.
    for repair in (repair_attested_identity, repair_attested_proposal):
        repaired = repair(record, agreement)
        if repaired is not None:
            return repaired

    return _excluded_decision(
        "unsupported_context_divergence",
        _exclusion_reasons(context_diff_paths),
        agreement,
        context_diff_paths,
    )


def curate_preference_record(record: dict[str, Any]) -> CurationDecision:
    """Curate one pair without mutating ``record``."""

    if not isinstance(record, dict):
        # No comparable context at all: both agreement fields stay None.
        return _excluded_decision(
            _MALFORMED_CONTEXT, ("PREFERENCE_RECORD_NOT_AN_OBJECT",), (None, None)
        )
    agreement = context_field_agreement(record)
    same_state, same_proposed_action = agreement
    if not _is_canonicalizable(record):
        # Checked before the context shape so a non-finite float anywhere in
        # the pair is reported precisely instead of surfacing as a bare
        # ValueError from the first canonical comparison.
        return _excluded_decision(
            _MALFORMED_CONTEXT, ("PREFERENCE_RECORD_NOT_JSON_SERIALIZABLE",), agreement
        )
    context = pair_context(record)
    if context is None:
        return _absent_context_decision(
            record, same_state, same_proposed_action
        )
    return _paired_context_decision(record, agreement, context)


def _paired_context_decision(
    record: dict[str, Any],
    agreement: _Agreement,
    context: tuple[dict[str, Any], dict[str, Any]],
) -> CurationDecision:
    """Retain an already-identical pair; otherwise repair it or exclude it."""

    same_state, same_proposed_action = agreement
    chosen, rejected = context
    context_diff_paths = all_context_diffs(chosen, rejected)
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
    return _repaired_or_excluded(record, agreement, context_diff_paths)
