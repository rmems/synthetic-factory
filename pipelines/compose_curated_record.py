#!/usr/bin/env python3
"""Record-level lane pipeline for curated composition."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_record")
    from .compose_contract import ACTION_RETAINED, ComposeDecision
    from .compose_curated_coding import _compose_coding_stage, _compose_rewards_stage
    from .compose_curated_context import RecordContext
    from .compose_curated_identity import (
        _compose_bridge_stage_with_source,
        _compose_identity_stage_with_source,
    )
    from .compose_curated_preferences import _compose_preferences_stage
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_record"
    )
    from compose_contract import ACTION_RETAINED, ComposeDecision
    from compose_curated_coding import _compose_coding_stage, _compose_rewards_stage
    from compose_curated_context import RecordContext
    from compose_curated_identity import (
        _compose_bridge_stage_with_source,
        _compose_identity_stage_with_source,
    )
    from compose_curated_preferences import _compose_preferences_stage


@dataclass(frozen=True)
class RecordServices:
    """Stage boundaries selected by the compatibility facade at call time."""

    identity: Callable[..., Any] = _compose_identity_stage_with_source
    bridge: Callable[..., Any] = _compose_bridge_stage_with_source
    preferences: Callable[..., Any] = _compose_preferences_stage
    coding: Callable[..., Any] = _compose_coding_stage
    rewards: Callable[..., Any] = _compose_rewards_stage


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


def compose_record(
    record: Any,
    context: RecordContext,
    services: RecordServices | None = None,
) -> ComposeDecision:
    """Apply identity, bridge, preference, coding, and reward lanes in order."""

    active = services or RecordServices()
    stages: list[dict[str, Any]] = []
    identity = active.identity(record, stages, context.source)
    if terminal := _early_decision(identity):
        return terminal
    current, registered_kind = identity

    bridge = active.bridge(current, stages, context.source)
    if terminal := _early_decision(bridge):
        return terminal
    current = bridge

    preferences = active.preferences(current, stages, context)
    if terminal := _early_decision(preferences):
        return terminal
    current = preferences

    coding = active.coding(current, registered_kind, stages, context)
    if terminal := _early_decision(coding):
        return terminal
    current = coding

    rewards = active.rewards(current, stages, context)
    if terminal := _early_decision(rewards):
        return terminal
    current, sidecar = rewards
    return _retained_decision(current, stages, sidecar)


if __package__:
    _expose_package_sibling(__name__)
