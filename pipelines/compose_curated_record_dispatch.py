#!/usr/bin/env python3
"""Branching lane dispatch behind the historical record-facade signatures."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

if __package__:
    from . import _expose_package_sibling


@dataclass(frozen=True)
class PreferenceDispatchContext:
    facade: Any
    decision_type: type
    excluded_action: str
    source_path: str
    source_line: int


@dataclass(frozen=True)
class CodingDispatchContext:
    facade: Any
    source_path: str
    source_line: int
    source_sha256: str


def compose_preferences_stage(
    context: PreferenceDispatchContext,
    current: dict[str, Any],
    stages: list[dict[str, Any]],
) -> Any:
    """Dispatch a preference record through live facade-owned branches."""

    facade = context.facade
    source_path = context.source_path
    source_line = context.source_line
    if not facade.is_preference_record(current):
        stages.append(
            facade._stage(
                "preferences",
                facade.curate_preferences.TRANSFORM_NAME,
                facade.curate_preferences.TRANSFORM_VERSION,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    side_kinds = facade.preference_side_kinds(current)
    if facade._is_same_state_pair(current):
        outcome = facade._compose_same_state_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    elif facade._mixed_preference_families(side_kinds):
        return facade._compose_mixed_family_preference_exclusion(side_kinds, stages)
    elif side_kinds == ("episode", "episode"):
        outcome = facade._compose_episode_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    else:
        outcome = facade._compose_legacy_preference(current, side_kinds, stages)
    if isinstance(outcome, context.decision_type):
        return outcome
    decision, reasons = outcome
    if decision.record is None:
        return context.decision_type(
            context.excluded_action,
            None,
            tuple(reasons),
            tuple(stages),
            None,
            None,
        )
    return decision.record


def compose_coding_stage(
    context: CodingDispatchContext,
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
) -> Any:
    """Dispatch coding curation while resolving every facade seam live."""

    facade = context.facade
    source_path = context.source_path
    source_line = context.source_line
    module = facade._coding_lane_curator(current, registered_kind)
    if module is None:
        trajectory = (
            facade._bridge_view_trajectory(current) if facade.is_bridge_record(current) else None
        )
        if trajectory is not None:
            return facade._compose_bridge_view_coding(
                current,
                trajectory,
                stages,
                source_path=source_path,
                source_line=source_line,
            )
        if facade._hidden_only_curation_applies(current, registered_kind):
            cleaned, detail = facade._strip_hidden_only_side(current)
            return facade._append_coding_lane_stage(stages, facade.curate_agentic, cleaned, detail)
        stages.append(
            facade._stage(
                "coding",
                facade.curate_coding.TRANSFORM_NAME,
                facade.curate_coding.TRANSFORM_VERSION,
                facade.ACTION_NOT_APPLICABLE,
                lane_action=facade.ACTION_NOT_APPLICABLE,
            )
        )
        return current
    curator = (
        facade.curate_agentic.curate_record
        if module is facade.curate_agentic
        else facade.curate_coding.curate_episode
    )
    curated, manifest = curator(
        current,
        source_path=source_path,
        source_line=source_line,
        source_hash=context.source_sha256,
    )
    return facade._append_coding_lane_stage(stages, module, curated, manifest)


if __package__:
    _expose_package_sibling(__name__)
else:
    package = sys.modules.get("pipelines")
    expose = getattr(package, "_expose_package_sibling", None)
    if expose is not None:
        expose(__name__)
