#!/usr/bin/env python3
"""Fail-closed eval-denylist / do-not-train gate over composed decisions (#494).

Compose applies this gate to every line after the lanes (and after any oracle
training selection) have decided it, exactly as export replays it. A retained
record is scanned for a source identity on every record kind (see
``eval_exclusion_subject``). A denylist or do-not-train hit refuses the shard
instead of dropping the row. A public-source claimant whose repository cannot
be resolved offline is still excluded with the matching reason codes and no
output, id, or reward sidecar. Records without a governed identity, and lines
already excluded, pass through unchanged.

Every compose summary records the policy it ran under (both list sha256 values
and the alias-cache sha256) under ``eval_exclusion``; export refuses a summary
whose block differs from the policy committed now.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_eval_gate")
    from . import eval_exclusion_policy as _policy
    from .compose_contract import ACTION_EXCLUDED, ACTION_RETAINED, LANE_ORDER, ComposeError
    from .eval_exclusion_subject import requires_repo, source_identities
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_eval_gate"
    )
    import eval_exclusion_policy as _policy
    from compose_contract import ACTION_EXCLUDED, ACTION_RETAINED, LANE_ORDER, ComposeError
    from eval_exclusion_subject import requires_repo, source_identities

NAME = "eval-exclusion-gate"
VERSION = 1
LANE = "eval_exclusion"
SUMMARY_KEY = "eval_exclusion"
# Lanes whose stage actions COMPOSE.json totals under ``lane_actions``: the five
# curation lanes plus this gate, counted identically by compose and export replay.
ACCOUNTED_LANES = (*LANE_ORDER, LANE)
LIST_HIT_REASONS = frozenset((_policy.REASON_EVAL_DENYLISTED, _policy.REASON_DO_NOT_TRAIN))


def active_policy(policy: Any = None) -> Any:
    """The supplied policy, or the one loaded at import (read live, so tests can patch it)."""

    return _policy.ACTIVE_POLICY if policy is None else policy


def descriptor(policy: Any = None) -> dict[str, Any]:
    """The ``eval_exclusion`` block a compose summary declares."""

    return {"name": NAME, "version": VERSION, **active_policy(policy).descriptor()}


def require_published(summary: Mapping[str, Any], policy: Any = None) -> dict[str, Any]:
    """Require a compose summary to declare exactly the committed exclusion policy."""

    declared = summary.get(SUMMARY_KEY)
    expected = descriptor(policy)
    if declared != expected:
        raise ComposeError(
            "COMPOSE.json: eval_exclusion does not match the committed eval denylist, "
            "do-not-train list, and repository alias cache; recompose"
        )
    return expected


def _gate_stage(rule: str, identity: Any, evaluation: Any) -> dict[str, Any]:
    return {
        "lane": LANE,
        "transform_name": NAME,
        "transform_version": VERSION,
        "action": ACTION_EXCLUDED if evaluation.excluded else ACTION_RETAINED,
        "reason_codes": list(evaluation.reason_codes),
        "detail": {
            "rule": rule,
            "source_repo": identity.repo,
            "canonical_repo": evaluation.canonical_repo,
            "program_id": identity.program_id,
            "task_id": identity.task_id,
            "base_commit": identity.base_commit,
            "matches": [dict(match) for match in evaluation.matches],
        },
    }


def _refuse_listed_hit(evaluation: Any) -> None:
    hits = tuple(code for code in evaluation.reason_codes if code in LIST_HIT_REASONS)
    if hits:
        raise ComposeError(
            "eval_exclusion: retained record matches the committed denylist or "
            f"do-not-train list ({', '.join(hits)}); refuse the shard rather than drop the row"
        )


def apply_gate(decision: Any, policy: Any = None) -> Any:
    """Refuse a listed hit; exclude a public-source record the policy cannot resolve."""

    if decision.action != ACTION_RETAINED or decision.record is None:
        return decision
    subjects = source_identities(decision.record)
    if not subjects:
        return decision
    loaded = active_policy(policy)
    stages = list(decision.stages)
    evaluation = None
    for rule, identity in subjects:
        evaluation = loaded.evaluate(identity, require_repo=requires_repo(rule))
        _refuse_listed_hit(evaluation)
        stages.append(_gate_stage(rule, identity, evaluation))
    if evaluation is None or not evaluation.excluded:
        return replace(decision, stages=tuple(stages))
    return replace(
        decision,
        action=ACTION_EXCLUDED,
        record=None,
        reason_codes=evaluation.reason_codes,
        stages=tuple(stages),
        output_id=None,
        reward_sidecar=None,
    )


if __package__:
    _expose_package_sibling(__name__)
