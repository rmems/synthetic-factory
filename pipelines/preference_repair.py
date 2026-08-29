#!/usr/bin/env python3
"""Repair an impure pair only when the record itself attests the identity.

A repair is the one path by which a pair whose branches differ can still be
published, so the bar is deliberately narrow. One branch must carry an exact
canonical copy of the intended context, and the *other* branch must state, in
a bounded annotation this module knows by name, that its context is that same
reference. Anything wider -- a heuristic merge, a "close enough" comparison,
a branch that merely looks repairable -- would let a genuinely divergent pair
into the corpus, so it is refused and left for exclusion instead.

Each function returns ``None`` when it cannot prove the identity, which the
caller reads as "not repairable by this rule", never as "repaired".

``agreement`` is the *source* pair's per-field agreement, measured before any
repair and stated on the decision a rule returns. A repair must never report
the agreement of its own output, or the audit would stop naming a repaired
pair as the impure evidence it is.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_context import (  # noqa: E402
    all_context_diffs,
    diff_paths_between,
    pair_context,
    context_is_pure,
)
from preference_model import (  # noqa: E402
    ACTION_REPAIRED,
    CurationDecision,
    canonical_json,
)

__all__ = [
    "repair_attested_identity",
    "repair_attested_proposal",
]


def _identity_annotation_reference(
    chosen_value: dict[str, Any],
    rejected_value: dict[str, Any],
    field: str,
) -> tuple[dict[str, Any], str, str] | None:
    """Find an exact reference side for a top-level ``identity_note`` diff.

    The attesting side must become byte-equivalent to the other side after
    removing exactly one top-level annotation, and that annotation must start
    with a literal identity claim naming the other side and context field.
    """

    candidates = (
        ("chosen", chosen_value, "rejected", rejected_value),
        ("rejected", rejected_value, "chosen", chosen_value),
    )
    for attester_name, attester, reference_name, reference in candidates:
        note = attester.get("identity_note")
        if "identity_note" in reference or not isinstance(note, str):
            continue
        expected_prefix = f"IDENTICAL to {reference_name}.{field}"
        if not note.strip().startswith(expected_prefix):
            continue
        stripped = copy.deepcopy(attester)
        stripped.pop("identity_note")
        if canonical_json(stripped) == canonical_json(reference):
            return copy.deepcopy(reference), attester_name, reference_name
    return None


def _repair_identity_annotations(
    record: dict[str, Any], agreement: tuple[bool | None, bool | None]
) -> CurationDecision | None:
    """Repair context that differs only by explicit branch identity notes."""

    context = pair_context(record)
    if context is None:
        return None
    chosen, rejected = context
    repaired = copy.deepcopy(record)
    changed: list[str] = []

    for field in ("state", "proposed_action"):
        if canonical_json(chosen[field]) == canonical_json(rejected[field]):
            continue
        reference = _identity_annotation_reference(chosen[field], rejected[field], field)
        if reference is None:
            return None
        exact_value, attester_name, reference_name = reference
        repaired[attester_name][field] = copy.deepcopy(exact_value)
        repaired[reference_name][field] = copy.deepcopy(exact_value)
        changed.append(f"{attester_name}.{field}")

    if not changed or not context_is_pure(repaired):
        return None
    source_chosen, source_rejected = context
    return CurationDecision(
        action=ACTION_REPAIRED,
        classification="attested_identity_annotation_only",
        reason_codes=(
            "EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_IDENTITY_NOTE_REMOVED",
        ),
        record=repaired,
        context_diff_paths=all_context_diffs(source_chosen, source_rejected),
        changed_context_fields=tuple(changed),
        same_state=agreement[0],
        same_proposed_action=agreement[1],
    )


def _without_proposal_annotations(value: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(value)
    stripped.pop("source", None)
    readout = stripped.get("snn_readout")
    if isinstance(readout, dict):
        readout.pop("note", None)
    return stripped


def _proposal_annotation_reference(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> tuple[dict[str, Any], str, str] | None:
    """Find an exact proposal reference under a literal branch-identity claim."""

    diff_paths = set(diff_paths_between(chosen, rejected, "proposed_action"))
    allowed_paths = {
        "proposed_action.source",
        "proposed_action.snn_readout.note",
    }
    if not diff_paths or not diff_paths.issubset(allowed_paths):
        return None
    if canonical_json(_without_proposal_annotations(chosen)) != canonical_json(
        _without_proposal_annotations(rejected)
    ):
        return None

    candidates = (
        ("chosen", chosen, "rejected", rejected),
        ("rejected", rejected, "chosen", chosen),
    )
    for attester_name, attester, reference_name, reference in candidates:
        attester_source = attester.get("source")
        reference_source = reference.get("source")
        if not isinstance(attester_source, str) or not isinstance(reference_source, str):
            continue
        marker = f" — IDENTICAL proposal to the {reference_name} branch"
        if attester_source.startswith(reference_source + marker):
            return copy.deepcopy(reference), attester_name, reference_name
    return None


def _repair_proposal_annotations(
    record: dict[str, Any], agreement: tuple[bool | None, bool | None]
) -> CurationDecision | None:
    """Repair an attested proposal whose only differences are annotations."""

    context = pair_context(record)
    if context is None:
        return None
    chosen, rejected = context
    if canonical_json(chosen["state"]) != canonical_json(rejected["state"]):
        return None
    reference = _proposal_annotation_reference(
        chosen["proposed_action"], rejected["proposed_action"]
    )
    if reference is None:
        return None

    exact_value, attester_name, reference_name = reference
    repaired = copy.deepcopy(record)
    repaired[attester_name]["proposed_action"] = copy.deepcopy(exact_value)
    repaired[reference_name]["proposed_action"] = copy.deepcopy(exact_value)
    if not context_is_pure(repaired):
        return None
    return CurationDecision(
        action=ACTION_REPAIRED,
        classification="attested_proposal_annotation_only",
        reason_codes=(
            "EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE",
            "BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED",
        ),
        record=repaired,
        context_diff_paths=all_context_diffs(chosen, rejected),
        changed_context_fields=(f"{attester_name}.proposed_action",),
        same_state=agreement[0],
        same_proposed_action=agreement[1],
    )



# Public aliases: the decision module applies these two rules in order.
repair_attested_identity = _repair_identity_annotations
repair_attested_proposal = _repair_proposal_annotations
