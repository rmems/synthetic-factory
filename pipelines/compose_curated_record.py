#!/usr/bin/env python3
"""Record-level lane pipeline for curated composition."""

from __future__ import annotations

from typing import Any

from compose_contract import ACTION_RETAINED, ComposeDecision
from compose_curated_coding import _compose_coding_stage, _compose_rewards_stage
from compose_curated_context import RecordContext
from compose_curated_identity import _compose_bridge_stage, _compose_identity_stage
from compose_curated_preferences import _compose_preferences_stage


def _early_decision(outcome: Any) -> ComposeDecision | None:
    """Return an early terminal decision, otherwise let composition continue."""

    return outcome if isinstance(outcome, ComposeDecision) else None


def _retained_decision(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    sidecar: dict[str, Any] | None,
) -> ComposeDecision:
    """Assemble the terminal retained decision from all lane evidence."""

    output_id = current.get("id")
    reasons = tuple(
        dict.fromkeys(reason for item in stages for reason in item["reason_codes"])
    )
    return ComposeDecision(
        ACTION_RETAINED,
        current,
        reasons,
        tuple(stages),
        sidecar,
        output_id if isinstance(output_id, str) else None,
    )


def compose_record(record: Any, context: RecordContext) -> ComposeDecision:
    """Apply identity, bridge, preference, coding, and reward lanes in order."""

    stages: list[dict[str, Any]] = []
    identity = _compose_identity_stage(record, stages, context.source)
    if terminal := _early_decision(identity):
        return terminal
    current, registered_kind = identity

    bridge = _compose_bridge_stage(current, stages, context.source)
    if terminal := _early_decision(bridge):
        return terminal
    current = bridge

    preferences = _compose_preferences_stage(current, stages, context)
    if terminal := _early_decision(preferences):
        return terminal
    current = preferences

    coding = _compose_coding_stage(current, registered_kind, stages, context)
    if terminal := _early_decision(coding):
        return terminal
    current = coding

    rewards = _compose_rewards_stage(current, stages, context)
    if terminal := _early_decision(rewards):
        return terminal
    current, sidecar = rewards
    return _retained_decision(current, stages, sidecar)
