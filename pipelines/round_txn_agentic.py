#!/usr/bin/env python3
"""Agentic envelope contract for pipelines/round_txn.py as a per-factory rule table.

Split out of ``round_txn`` (A8 of #211). ``round_txn.validate_agentic_envelope``
stays the public entry point; it builds an :class:`AgenticPolicy` from its own
namespace (factory kinds, quotas, the reviewed-generator authority, and the
physical-LF JSONL reader) so every facade name remains a live seam, then hands
the staged batch to :func:`validate_envelope` here.

Each record is checked by the rule tuple ``record_rules`` composes for its
factory: the shared wrapper ban, the restart-lane scenario rule when the lane
has scenario terms, the lane's own rules from ``LANE_RECORD_RULES``, the
kind-wide rules from ``KIND_RECORD_RULES``, and finally the meta binding. Batch
totals collected in :class:`EnvelopeTally` are then judged by
``LANE_BATCH_RULES``. Every checker returns its error strings in the order the
original single-function contract emitted them; the strings are unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("round_txn_agentic")
    from . import round_txn_agentic_cascade as _cascade
    from . import round_txn_agentic_terms as _terms
    from . import round_txn_coverage as _coverage
    from .round_txn_agentic_types import (
        AgenticPolicy,
        BatchContract,
        BatchRule,
        EnvelopeContext,
        EnvelopeTally,
        RecordRule,
        _is_plain_int,
        _nonempty_str,
        _outcome_text,
    )
    from .validate_run import THALAMIC_CORE_KEYS, terminal_outcome_agrees
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "round_txn_agentic"
    )
    import round_txn_agentic_cascade as _cascade
    import round_txn_agentic_terms as _terms
    import round_txn_coverage as _coverage
    from round_txn_agentic_types import (
        AgenticPolicy,
        BatchContract,
        BatchRule,
        EnvelopeContext,
        EnvelopeTally,
        RecordRule,
        _is_plain_int,
        _nonempty_str,
        _outcome_text,
    )
    from validate_run import THALAMIC_CORE_KEYS, terminal_outcome_agrees


# --- shared rules -----------------------------------------------------------


def _banned_wrapper_errors(ctx: EnvelopeContext) -> list[str]:
    return [
        f"{ctx.where}: agentic records must not include spike_events, Spikenaut, "
        f"or neuromorphic rasters at {path}"
        for path in sorted(set(_coverage.banned_agentic_wrapper_paths(ctx.record)))
    ]


def _ordered_scenario_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    if _coverage.demonstrates_ordered_scenario(ctx.record, ctx.batch.scenario_terms):
        return []
    return [
        f"{ctx.where}: {ctx.factory_name} must demonstrate its required "
        "failure scenario, bounded correction, and observable verification "
        "in ordered trajectory evidence"
    ]


def _meta_errors(ctx: EnvelopeContext) -> list[str]:
    meta = ctx.get("meta")
    if not isinstance(meta, dict):
        return [f"{ctx.where}: agentic record meta must be an object"]
    errors = []
    if meta.get("factory") != ctx.factory_name:
        errors.append(f"{ctx.where}: meta.factory must be {ctx.factory_name!r}")
    meta_round = meta.get("round")
    if not _is_plain_int(meta_round) or meta_round != ctx.batch.round_number:
        errors.append(
            f"{ctx.where}: meta.round must match reservation r{ctx.batch.round_number:02d}"
        )
    if meta.get("generator") != ctx.batch.expected_generator:
        errors.append(f"{ctx.where}: meta.generator must be {ctx.batch.expected_generator!r}")
    return errors


# --- safety-calibration-factory --------------------------------------------


def _collect_safety_case_type(ctx: EnvelopeContext) -> list[str]:
    if isinstance(ctx.record, dict):
        ctx.tally.safety_case_types.append(ctx.record.get("case_type"))
    return []


def _safety_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    del quota
    required = _terms.SAFETY_REQUIRED_CASE_TYPES
    if len(tally.safety_case_types) == len(required) and set(tally.safety_case_types) == required:
        return []
    return [
        "safety-calibration-factory requires exactly one each of "
        "correct_refusal, incorrect_refusal, and missed_refusal per batch"
    ]


# --- long-horizon-coding-factory -------------------------------------------


def _long_horizon_scenario_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    signature = _coverage.long_horizon_scenario_signature(ctx.record)
    if signature is None:
        return [
            f"{ctx.where}: long-horizon episodes require explicit non-empty "
            "codebase_type and bug_class categories"
        ]
    ctx.tally.long_horizon_scenario_signatures.append(signature)
    return []


def _long_horizon_step_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    steps = ctx.record.get("steps")
    errors = []
    for index, step in enumerate(steps if isinstance(steps, list) else ()):
        basis = step.get("decision_basis") if isinstance(step, dict) else None
        if isinstance(basis, str) and len(basis) > 240:
            errors.append(
                f"{ctx.where}: long-horizon steps[{index}].decision_basis "
                "must be at most 240 characters"
            )
    errors.extend(
        _coverage.numbered_horizon_errors(ctx.where, steps, "long-horizon coding", (18, 28))
    )
    if not _coverage.has_long_horizon_debug_loop(steps):
        errors.append(
            f"{ctx.where}: long-horizon episodes require an observable edit, "
            "failing test, re-read, fix, and passing verification loop"
        )
    return errors


def _long_horizon_outcome_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    reward = ctx.record.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if not isinstance(success, bool):
        return []
    ctx.tally.long_horizon_success_values.append(success)
    outcome = ctx.record.get("outcome")
    outcome_text = _outcome_text(outcome)
    completion_evidence = _terms.LONG_HORIZON_COMPLETION_RE.search(outcome_text)
    partial_evidence = _terms.PARTIAL_OUTCOME_RE.search(outcome_text)
    contradictory = _terms.LONG_HORIZON_CONTRADICTORY_COMPLETION_RE.search(outcome_text)
    errors = []
    if success and (
        completion_evidence is None
        or partial_evidence is not None
        or not terminal_outcome_agrees(outcome, True)
    ):
        errors.append(
            f"{ctx.where}: successful long-horizon outcome must report "
            "observable verification without partial or handoff language"
        )
    if not success and (partial_evidence is None or contradictory is not None):
        errors.append(
            f"{ctx.where}: unsuccessful long-horizon outcome must report "
            "partial containment, mitigation, or handoff"
        )
    return errors


def _long_horizon_success_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    del quota
    if sorted(tally.long_horizon_success_values) == [False, True]:
        return []
    return [
        "long-horizon-coding-factory requires one success and one partial "
        "containment, mitigation, or handoff per batch"
    ]


def _long_horizon_scenario_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    signatures = tally.long_horizon_scenario_signatures
    codebases = {signature[0] for signature in signatures}
    bug_classes = {signature[1] for signature in signatures}
    if len(codebases) == quota and len(bug_classes) == quota:
        return []
    return [
        "long-horizon-coding-factory requires two distinct codebase and "
        "bug-class scenarios per batch"
    ]


# --- multi-agent-coordination-factory --------------------------------------


def _turn_indexes(turn_contents: list, text) -> list[int]:
    return [
        index
        for index, content in enumerate(turn_contents)
        if _coverage.shares_visible_terms(text, content)
    ]


def _plan_changes_after(disagreement_turns, resolution_turns, resolution, turn_contents) -> bool:
    for disagreement_index in disagreement_turns:
        for resolution_index in resolution_turns:
            candidate = f"{resolution} {turn_contents[resolution_index] or ''}".casefold()
            if (
                disagreement_index < resolution_index
                and any(term in candidate for term in _terms.PLAN_CHANGE_TERMS)
                and not any(term in candidate for term in _terms.IGNORED_PLAN_TERMS)
            ):
                return True
    return False


def _resolution_is_grounded(disagreements, resolution, turn_contents) -> bool:
    if not (isinstance(disagreements, list) and isinstance(resolution, str)):
        return False
    resolution_turns = _turn_indexes(turn_contents, resolution)
    for disagreement in disagreements:
        if not _coverage.shares_visible_terms(disagreement, resolution):
            continue
        disagreement_turns = _turn_indexes(turn_contents, disagreement)
        if _plan_changes_after(disagreement_turns, resolution_turns, resolution, turn_contents):
            return True
    return False


def _coordination_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    transcript = ctx.record.get("transcript")
    if not isinstance(transcript, list):
        return []
    errors = []
    if not 6 <= len(transcript) <= 16:
        errors.append(f"{ctx.where}: coordination transcripts require 6 to 16 turns")
    turn_contents = [turn.get("content") if isinstance(turn, dict) else None for turn in transcript]
    if not _resolution_is_grounded(
        ctx.record.get("disagreements"), ctx.record.get("resolution"), turn_contents
    ):
        errors.append(
            f"{ctx.where}: resolution must cite a disagreement and "
            "observably change the later coordination plan"
        )
    return errors


# --- sparse-reward-long-task-factory ---------------------------------------


def _sparse_forbidden_field_errors(where: str, index: int, step: dict) -> list[str]:
    errors = []
    for field_name in _terms.SPARSE_FORBIDDEN_STEP_FIELDS:
        for path in _coverage.nested_key_paths(step, field_name):
            if field_name == "reward":
                errors.append(
                    f"{where}: sparse long-task steps[{index}] must not carry reward at {path}"
                )
            else:
                errors.append(
                    f"{where}: sparse long-task steps[{index}] "
                    f"must not carry intermediate {field_name} at {path}"
                )
    return errors


def _sparse_step_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    steps = ctx.record.get("steps")
    if not isinstance(steps, list):
        return []
    errors = _coverage.numbered_horizon_errors(ctx.where, steps, "sparse long-task", (25, 60))
    errors.extend(_coverage.sparse_step_progress_errors(ctx.where, steps))
    for index, step in enumerate(steps):
        if isinstance(step, dict):
            errors.extend(_sparse_forbidden_field_errors(ctx.where, index, step))
    reward = ctx.record.get("reward")
    horizon_steps = reward.get("horizon_steps") if isinstance(reward, dict) else None
    if not _is_plain_int(horizon_steps) or horizon_steps != len(steps):
        errors.append(f"{ctx.where}: reward.horizon_steps must equal the staged step count")
    if len(_coverage.abandoned_failed_hypotheses(steps)) < 2:
        errors.append(
            f"{ctx.where}: sparse long-task episodes require at least two "
            "explicit hypotheses whose failure observations precede abandonment"
        )
    return errors


def _sparse_terminal_only_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    reward = ctx.record.get("reward")
    if isinstance(reward, dict) and reward.get("terminal_only") is True:
        return []
    return [f"{ctx.where}: reward.terminal_only must be true"]


def _sparse_outcome_mismatch(success: bool, outcome_text: str) -> bool:
    completion = list(_terms.SPARSE_COMPLETION_RE.finditer(outcome_text))
    failed = list(_terms.SPARSE_FAILED_RE.finditer(outcome_text))
    incomplete = _terms.SPARSE_INCOMPLETE_RE.search(outcome_text)
    failed_last = bool(failed) and (not completion or failed[-1].start() > completion[-1].start())
    completed_last = bool(completion) and (not failed or completion[-1].start() > failed[-1].start())
    if success:
        return not completion or incomplete is not None or failed_last
    return incomplete is None and (not failed or completed_last)


def _sparse_outcome_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    reward = ctx.record.get("reward")
    success = reward.get("success") if isinstance(reward, dict) else None
    if not isinstance(success, bool):
        return []
    if not _sparse_outcome_mismatch(success, _outcome_text(ctx.record.get("outcome"))):
        return []
    if success:
        return [
            f"{ctx.where}: successful sparse terminal reward must match "
            "a verified completed outcome"
        ]
    return [
        f"{ctx.where}: unsuccessful sparse terminal reward must match "
        "an explicit failure, partial result, or handoff"
    ]


# --- preference kinds -------------------------------------------------------


def _tool_use_lesson_errors(ctx: EnvelopeContext) -> list[str]:
    if not isinstance(ctx.record, dict):
        return []
    lesson_category = ctx.record.get("lesson_category")
    if not _nonempty_str(lesson_category):
        return [f"{ctx.where}: tool-use preferences require a non-empty lesson_category"]
    lesson_signature = _coverage.normalized_category(lesson_category)
    if not lesson_signature:
        return [
            f"{ctx.where}: tool-use preference lesson_category must contain a letter or number"
        ]
    ctx.tally.tool_use_lesson_signatures.append(lesson_signature)
    return []


def _preference_side_errors(ctx: EnvelopeContext, side_name: str) -> list[str]:
    side = ctx.get(side_name)
    errors = []
    if not isinstance(side, dict) or not isinstance(side.get("steps"), list):
        errors.append(f"{ctx.where}: {side_name} must be an episode side with steps")
    elif all(key in side for key in THALAMIC_CORE_KEYS):
        errors.append(f"{ctx.where}: {side_name} must not wrap a Thalamic trajectory")
    if ctx.factory_name == "tool-use-preference-factory" and isinstance(side, dict):
        errors.extend(
            _coverage.numbered_horizon_errors(
                ctx.where, side.get("steps"), f"tool-use preference {side_name}", (4, 10)
            )
        )
    side_reward = side.get("reward") if isinstance(side, dict) else None
    success = side_reward.get("success") if isinstance(side_reward, dict) else None
    required_success = side_name == "chosen"
    if isinstance(success, bool) and success is not required_success:
        errors.append(
            f"{ctx.where}: {side_name}.reward.success must be {str(required_success).lower()}"
        )
    if isinstance(success, bool) and not terminal_outcome_agrees(side.get("outcome"), success):
        errors.append(
            f"{ctx.where}: {side_name}.outcome must agree with {side_name}.reward.success"
        )
    return errors


def _preference_sides_errors(ctx: EnvelopeContext) -> list[str]:
    return _preference_side_errors(ctx, "chosen") + _preference_side_errors(ctx, "rejected")


def _tool_use_lesson_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    if len(set(tally.tool_use_lesson_signatures)) == quota:
        return []
    return ["tool-use-preference-factory requires three distinct tool-use lessons per batch"]


# --- the rule table ---------------------------------------------------------

LANE_RECORD_RULES: dict[str, tuple[RecordRule, ...]] = {
    "safety-calibration-factory": (_collect_safety_case_type,),
    "cascading-error-recovery-factory": _cascade.RECORD_RULES,
    "long-horizon-coding-factory": (
        _long_horizon_scenario_errors,
        _long_horizon_step_errors,
        _long_horizon_outcome_errors,
    ),
    "multi-agent-coordination-factory": (_coordination_errors,),
    "sparse-reward-long-task-factory": (
        _sparse_step_errors,
        _sparse_terminal_only_errors,
        _sparse_outcome_errors,
    ),
    "tool-use-preference-factory": (_tool_use_lesson_errors,),
}

KIND_RECORD_RULES: dict[str, tuple[RecordRule, ...]] = {
    "preference": (_preference_sides_errors,),
}

LANE_BATCH_RULES: dict[str, tuple[BatchRule, ...]] = {
    "safety-calibration-factory": (_safety_batch_errors,),
    "cascading-error-recovery-factory": _cascade.BATCH_RULES,
    "long-horizon-coding-factory": (
        _long_horizon_success_batch_errors,
        _long_horizon_scenario_batch_errors,
    ),
    "tool-use-preference-factory": (_tool_use_lesson_batch_errors,),
}


def record_rules(contract: BatchContract) -> tuple[RecordRule, ...]:
    """The ordered record rules for one batch: shared, scenario, lane, kind, then meta."""
    scenario: tuple[RecordRule, ...] = ()
    if contract.scenario_terms is not None:
        scenario = (_ordered_scenario_errors,)
    return (
        (_banned_wrapper_errors,)
        + scenario
        + LANE_RECORD_RULES.get(contract.factory_name, ())
        + KIND_RECORD_RULES.get(contract.kind, ())
        + (_meta_errors,)
    )


class EnvelopeRequest(NamedTuple):
    """The staged batch one envelope check reads, including factory-staging skips."""

    batch: Path
    factory_dir: Path
    round_number: int
    factory_staging_exempt_lines: frozenset = frozenset()


def validate_envelope(request: EnvelopeRequest, policy: AgenticPolicy) -> list[str]:
    """Return fixed-contract envelope errors for one staged agentic batch."""
    factory_name = request.factory_dir.name
    if factory_name not in policy.factory_kinds:
        return []
    contract = BatchContract(
        factory_name=factory_name,
        kind=policy.factory_kinds[factory_name],
        round_number=request.round_number,
        expected_generator=policy.reviewed_hosted_generator(request.factory_dir),
        scenario_terms=policy.scenario_terms.get(factory_name),
    )
    records, errors = policy.jsonl_records(request.batch)
    rules = record_rules(contract)
    tally = EnvelopeTally()
    for lineno, record in records:
        if lineno in request.factory_staging_exempt_lines:
            continue
        ctx = EnvelopeContext(contract, f"{request.batch.name}:{lineno}", record, tally)
        for rule in rules:
            errors.extend(rule(ctx))
    batch_rules = LANE_BATCH_RULES.get(factory_name, ())
    if batch_rules:
        quota = policy.factory_quotas[factory_name]
        for batch_rule in batch_rules:
            errors.extend(batch_rule(tally, quota))
    return errors


if __package__:
    _expose_package_sibling(__name__)
