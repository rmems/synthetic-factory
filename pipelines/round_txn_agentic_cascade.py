#!/usr/bin/env python3
"""Cascading-error-recovery envelope rules for the agentic round contract.

Split out of ``round_txn_agentic`` so the per-factory rule table stays under
the 500-line file bar. Error strings and their order are unchanged; the
functions here are the same record and batch rules the table previously
held inline.
"""

from __future__ import annotations

import sys
from typing import NamedTuple, TypeGuard

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("round_txn_agentic_cascade")
    from . import round_txn_agentic_terms as _terms
    from . import round_txn_coverage as _coverage
    from .round_txn_agentic_types import (
        BatchRule,
        EnvelopeContext,
        EnvelopeTally,
        RecordRule,
        _nonempty_str,
        _outcome_text,
    )
    from .validate_run import terminal_outcome_agrees
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "round_txn_agentic_cascade"
    )
    import round_txn_agentic_terms as _terms
    import round_txn_coverage as _coverage
    from round_txn_agentic_types import (
        BatchRule,
        EnvelopeContext,
        EnvelopeTally,
        RecordRule,
        _nonempty_str,
        _outcome_text,
    )
    from validate_run import terminal_outcome_agrees


def _is_plain_int(value) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


class _CascadeChain(NamedTuple):
    where: str
    steps: list
    fault_text: str
    diagnosis: str
    fault_step: int
    cascade_steps: int


def _cascade_step_errors(ctx: EnvelopeContext) -> list[str]:
    return _coverage.contiguous_step_number_errors(
        ctx.where, ctx.get("steps"), "cascading-error recovery"
    )


def _cascade_fault_kind_errors(ctx: EnvelopeContext, fault: dict) -> list[str]:
    if not _nonempty_str(fault.get("kind")):
        return [f"{ctx.where}: error_introduced.kind must be a non-empty string"]
    fault_kind = _coverage.normalized_category(fault["kind"])
    if not fault_kind:
        return [f"{ctx.where}: error_introduced.kind must contain a letter or number"]
    ctx.tally.cascade_fault_kinds.append(fault_kind)
    return []


def _cascade_introduction_errors(where: str, fault: dict, steps) -> list[str]:
    step_number = fault.get("step")
    if not (_is_plain_int(step_number) and isinstance(steps, list)):
        return []
    if not 1 <= step_number <= len(steps):
        return []
    introduced_step = steps[step_number - 1]
    introduced_text = ""
    if isinstance(introduced_step, dict):
        introduced_text = " ".join(
            _coverage.nested_strings(
                {
                    "action": introduced_step.get("action"),
                    "tool_call": introduced_step.get("tool_call"),
                    "observation": introduced_step.get("observation"),
                }
            )
        )
    if _coverage.visibly_names_fault(introduced_text, fault.get("kind"), fault.get("payload")):
        return []
    return [
        f"{where}: error_introduced.step action or observation "
        "must visibly introduce the declared fault"
    ]


def _cascade_fault_errors(ctx: EnvelopeContext) -> list[str]:
    fault = ctx.get("error_introduced")
    steps = ctx.get("steps")
    if not isinstance(fault, dict):
        return [f"{ctx.where}: error_introduced must be an object"]
    errors = []
    step_number = fault.get("step")
    if (
        not _is_plain_int(step_number)
        or step_number < 2
        or not isinstance(steps, list)
        or step_number >= len(steps)
    ):
        errors.append(f"{ctx.where}: error_introduced.step must name a non-final step at least 2")
    errors.extend(_cascade_fault_kind_errors(ctx, fault))
    if not _nonempty_str(fault.get("payload")):
        errors.append(f"{ctx.where}: error_introduced.payload must be a non-empty string")
    errors.extend(_cascade_introduction_errors(ctx.where, fault, steps))
    return errors


def _cascade_diagnosis_errors(ctx: EnvelopeContext) -> list[str]:
    if _nonempty_str(ctx.get("diagnosis")):
        return []
    return [f"{ctx.where}: diagnosis must be a non-empty string"]


def _cascade_outcome_errors(where: str, outcome, recovered: int) -> list[str]:
    outcome_text = _outcome_text(outcome)
    if recovered == 0:
        partial_evidence = _terms.PARTIAL_OUTCOME_RE.search(outcome_text)
        contradictory = _terms.CONTRADICTORY_COMPLETION_RE.search(outcome_text)
        if partial_evidence is None or contradictory is not None:
            return [
                f"{where}: unrecovered cascade outcome must report "
                "partial containment, mitigation, or handoff without "
                "full-completion claims"
            ]
        return []
    completion_evidence = _terms.CASCADE_COMPLETION_RE.search(outcome_text)
    if completion_evidence is None or not terminal_outcome_agrees(outcome, True):
        return [
            f"{where}: recovered cascade outcome must report "
            "verified full recovery without terminal failure, "
            "negation, partial, unresolved, or handoff claims"
        ]
    return []


def _cascade_recovery_errors(ctx: EnvelopeContext) -> list[str]:
    reward = ctx.get("reward")
    recovered = reward.get("recovered") if isinstance(reward, dict) else None
    if not _is_plain_int(recovered) or recovered not in (0, 1):
        return [f"{ctx.where}: reward.recovered must be 0 or 1"]
    ctx.tally.cascade_recovery_values.append(recovered)
    errors = []
    success = reward.get("success")
    if isinstance(success, bool) and success != bool(recovered):
        errors.append(f"{ctx.where}: reward.success must agree with reward.recovered")
    errors.extend(_cascade_outcome_errors(ctx.where, ctx.get("outcome"), recovered))
    return errors


def _diagnosis_step_text(diagnosis_step):
    if not isinstance(diagnosis_step, dict):
        return None
    return " ".join(
        value
        for value in (diagnosis_step.get("observation"), diagnosis_step.get("reflection"))
        if isinstance(value, str)
    )


def _cascade_inherited_errors(chain: _CascadeChain, diagnosis_text) -> list[str]:
    diagnosis_index = chain.fault_step + chain.cascade_steps
    inherited = chain.steps[chain.fault_step : diagnosis_index]
    errors = []
    if any(
        not isinstance(step, dict)
        or not _coverage.shares_visible_terms(step.get("observation"), chain.fault_text)
        for step in inherited
    ):
        errors.append(f"{chain.where}: each inherited cascade step must visibly reference the fault")
    if not _coverage.shares_visible_terms(diagnosis_text, chain.fault_text):
        errors.append(f"{chain.where}: diagnosis step must visibly name the fault")
    if not (
        _coverage.shares_visible_terms(chain.diagnosis, chain.fault_text)
        and _coverage.shares_visible_terms(chain.diagnosis, diagnosis_text)
    ):
        errors.append(
            f"{chain.where}: top-level diagnosis must remain grounded "
            "in the introduced fault and diagnosis step"
        )
    return errors


def _cascade_recovery_basis_errors(chain: _CascadeChain, diagnosis_text) -> list[str]:
    recovery_step = chain.steps[chain.fault_step + chain.cascade_steps + 1]
    recovery_basis = None
    if isinstance(recovery_step, dict):
        recovery_basis = recovery_step.get("decision_basis")
    errors = []
    if not _coverage.shares_visible_terms(recovery_basis, chain.diagnosis):
        errors.append(f"{chain.where}: recovery decision_basis must cite the diagnosis")
    if not (
        _coverage.shares_visible_terms(recovery_basis, chain.fault_text)
        and _coverage.shares_visible_terms(recovery_basis, diagnosis_text)
    ):
        errors.append(
            f"{chain.where}: recovery decision_basis must remain grounded "
            "in the introduced fault and diagnosis-step evidence"
        )
    return errors


def _cascade_chain_errors(chain: _CascadeChain) -> list[str]:
    diagnosis_index = chain.fault_step + chain.cascade_steps
    if diagnosis_index + 1 >= len(chain.steps):
        return [
            f"{chain.where}: cascade needs {chain.cascade_steps} inherited steps, "
            "then diagnosis and recovery"
        ]
    diagnosis_text = _diagnosis_step_text(chain.steps[diagnosis_index])
    return _cascade_inherited_errors(chain, diagnosis_text) + _cascade_recovery_basis_errors(
        chain, diagnosis_text
    )


def _cascade_steps_errors(ctx: EnvelopeContext) -> list[str]:
    reward = ctx.get("reward")
    cascade_steps = reward.get("cascade_steps") if isinstance(reward, dict) else None
    if not _is_plain_int(cascade_steps) or not 3 <= cascade_steps <= 8:
        return [f"{ctx.where}: reward.cascade_steps must be an integer from 3 to 8"]
    fault = ctx.get("error_introduced")
    steps = ctx.get("steps")
    diagnosis = ctx.get("diagnosis")
    if not (
        isinstance(fault, dict)
        and _is_plain_int(fault.get("step"))
        and isinstance(steps, list)
        and _nonempty_str(diagnosis)
    ):
        return []
    chain = _CascadeChain(
        where=ctx.where,
        steps=steps,
        fault_text=f"{fault.get('kind', '')} {fault.get('payload', '')}",
        diagnosis=diagnosis,
        fault_step=fault["step"],
        cascade_steps=cascade_steps,
    )
    return _cascade_chain_errors(chain)


def _cascade_recovery_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    del quota
    if sorted(tally.cascade_recovery_values) == [0, 1]:
        return []
    return [
        "cascading-error-recovery-factory requires one full recovery and "
        "one partial containment or handoff per batch"
    ]


def _cascade_fault_kind_batch_errors(tally: EnvelopeTally, quota: int) -> list[str]:
    del quota
    kinds = tally.cascade_fault_kinds
    if len(kinds) != 2 or len(set(kinds)) == 2:
        return []
    return [
        "cascading-error-recovery-factory requires two distinct "
        "error_introduced.kind fault classes per batch"
    ]


RECORD_RULES: tuple[RecordRule, ...] = (
    _cascade_step_errors,
    _cascade_fault_errors,
    _cascade_diagnosis_errors,
    _cascade_recovery_errors,
    _cascade_steps_errors,
)

BATCH_RULES: tuple[BatchRule, ...] = (
    _cascade_recovery_batch_errors,
    _cascade_fault_kind_batch_errors,
)


if __package__:
    _expose_package_sibling(__name__)
