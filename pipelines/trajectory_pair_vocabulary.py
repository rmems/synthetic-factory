#!/usr/bin/env python3
"""Shared vocabulary for the trajectory-pair preference lane.

``curate_trajectory_preferences.py`` is the CLI and source scanner. The gate it
runs is split across three sibling modules so no single file owns both the
reason vocabulary and the rules that emit it:

* this module — reason codes, actions, decisions, and gate policy,
* ``trajectory_pair_shape`` — what a well-formed trajectory pair looks like,
* ``trajectory_pair_gate`` — which well-formed pairs carry usable contrast,
* ``trajectory_pair_curation`` — repairs and the per-record decision.

Every name here is re-exported from ``curate_trajectory_preferences`` so the
lane keeps one public import surface.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

if __package__:
    from .curate_agentic import (
        REASON_GOAL_DIVERGES,
        REASON_GOAL_MISSING,
        REASON_GOAL_NOT_TEXT,
    )
    from .curate_preferences import PreferenceCurationError
else:
    from curate_agentic import (
        REASON_GOAL_DIVERGES,
        REASON_GOAL_MISSING,
        REASON_GOAL_NOT_TEXT,
    )
    from curate_preferences import PreferenceCurationError


TRANSFORM_NAME = "trajectory-pair-preference-curation"
TRANSFORM_VERSION = "1.2.0"

ACTION_RETAINED = "retained"
ACTION_REPAIRED = "repaired"
ACTION_EXCLUDED = "excluded"
ACTION_SKIPPED = "skipped"

REASON_RECORD_NOT_OBJECT = "TRAJECTORY_RECORD_NOT_AN_OBJECT"
REASON_NOT_A_PAIR = "NOT_A_PREFERENCE_PAIR_RECORD"
REASON_SIDES_NOT_OBJECTS = "TRAJECTORY_PAIR_SIDES_NOT_OBJECTS"
REASON_SAME_STATE_SCHEMA = "SAME_STATE_PAIR_DEFERRED_TO_CURATE_PREFERENCES"
REASON_PAIR_ENVELOPE_INVALID = "TRAJECTORY_PAIR_ENVELOPE_INVALID"
REASON_SIDE_EPISODE_INVALID = "TRAJECTORY_PAIR_SIDE_EPISODE_INVALID"
REASON_STEPS_INVALID = "TRAJECTORY_STEPS_MISSING_OR_INVALID"
REASON_STEPS_EMPTY = "TRAJECTORY_STEPS_EMPTY"
REASON_PAIR_IDENTICAL = "TRAJECTORY_PAIR_IDENTICAL"
REASON_PREFIX_ABSENT = "TRAJECTORY_PREFIX_OVERLAP_ABSENT"
REASON_BRANCH_LABEL_ONLY = "FIRST_STEP_DIFFERS_BY_BRANCH_LABEL_ONLY"
REASON_OUTCOME_MISSING = "TRAJECTORY_OUTCOME_MISSING"
REASON_OUTCOME_INVALID = "TRAJECTORY_OUTCOME_INVALID"
REASON_OUTCOME_NOT_DIVERGENT = "TRAJECTORY_OUTCOME_DOES_NOT_DIVERGE"
REASON_REWARD_MISSING = "TRAJECTORY_REWARD_MISSING"
REASON_REWARD_INVALID = "TRAJECTORY_REWARD_INVALID"
REASON_REWARD_NOT_DIVERGENT = "TRAJECTORY_REWARD_DOES_NOT_DIVERGE"
REASON_PREFERENCE_DIRECTION_INVALID = "TRAJECTORY_PREFERENCE_DIRECTION_INVALID"
REASON_GATE_PASSED = "TRAJECTORY_PAIR_SHARED_GOAL_AND_PREFIX"
REASON_GOAL_WHITESPACE_NORMALIZED = "TRAJECTORY_GOAL_WHITESPACE_NORMALIZED"

# A step whose only cross-branch difference is the literal word "chosen" or
# "rejected" leaks the branch label into the trajectory itself. It is reported
# on the reject path as native impurity; it is never repaired here, because
# rewriting generated step text would fabricate evidence.
BRANCH_LABEL_RE = re.compile(r"\b(?:chosen|rejected)\b", re.IGNORECASE)
BRANCH_LABEL_MASK = "<branch>"

# Goal vocabulary is shared with curate_agentic so the two lanes never
# disagree about what "one problem" means.
GOAL_REASONS = (REASON_GOAL_MISSING, REASON_GOAL_NOT_TEXT, REASON_GOAL_DIVERGES)
SAME_STATE_FIELDS = ("state", "proposed_action")
GOAL_LOCATIONS = (("goal",), ("chosen", "goal"), ("rejected", "goal"))

PAIR_SIDES = ("chosen", "rejected")
# A DPO pair only supervises in one direction: the chosen arm must carry the
# success label and the rejected arm must carry the failure label.
REQUIRED_SIDE_SUCCESS = (("chosen", True), ("rejected", False))


class TrajectoryCurationError(PreferenceCurationError):
    """Raised when trajectory-pair source or destination handling is unsafe."""


@dataclass(frozen=True)
class GatePolicy:
    """Operator-selected strictness for one scan.

    ``enforce_outcome_agreement`` runs ``validate_run.terminal_outcome_agrees``
    over each arm, the way ``round_txn`` does at publication time, so a side
    whose prose contradicts its own ``reward.success`` label is rejected.

    It is **off by default**, and that default is a measurement rather than a
    preference. ``terminal_outcome_agrees`` is a lexical heuristic calibrated
    for the outcome vocabulary the Thalamic factory generates. Run over the
    published Grok mirrors it is dominated by false positives: it rejects
    282 of 2964 ``code-review-preference-pairs`` and 5936 of 6192
    ``tool-use-preference-pairs``, because tool names collide with its failure
    vocabulary (``faillock``, ``fail2ban-client`` match ``fail\\w*``), correctly
    labelled failures narrate the defect they describe (``evidence deleted;
    hallucinated success``), and review verdicts quote the defect text they
    reject. This lane scans external mirrors whose prose it does not control,
    so the agreement check is offered to an operator who has judged their
    corpus rather than imposed on every scan.

    The lane's *structural* direction invariant is always enforced and is not
    heuristic: see ``trajectory_pair_gate.preference_direction_failures``.
    """

    enforce_outcome_agreement: bool = False


DEFAULT_POLICY = GatePolicy()


@dataclass(frozen=True)
class TrajectoryDecision:
    """One deterministic record-level trajectory-pair decision."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    shared_goal: bool | None = None
    overlap: dict[str, Any] | None = None
    changed_fields: tuple[str, ...] = ()
    pair_validation_errors: tuple[str, ...] | None = None
    side_validation_errors: dict[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class CurationRun:
    """Curated records, manifest entries, and aggregate counts for one source."""

    records: tuple[dict[str, Any], ...]
    manifest: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


def parse_finite_json_float(text: str) -> float:
    """Decode one JSON float without accepting finite-token overflow."""

    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {text}")
    return value


def is_finite_json_number(value: Any) -> bool:
    """Accept arbitrary-size JSON integers and finite floats, but not booleans."""

    return type(value) is int or (type(value) is float and math.isfinite(value))
