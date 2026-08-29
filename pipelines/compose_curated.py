#!/usr/bin/env python3
"""Compose the record-level curation transforms into one curated destination.

The transforms (``curate_identity``, ``curate_bridge``,
``curate_preferences``, ``curate_coding``, ``curate_agentic``, and
``curate_rewards``) are deliberately record-level and independent.  This
module is the missing composition step: it applies them in one documented
order to every JSONL record under a source run and writes a brand-new curated
tree.  Tag normalization is not composed here; that lane does not exist yet.

Lane order (each lane only sees records it owns)::

    identity -> bridge -> preferences -> coding/agentic -> rewards

Identity runs first because it assigns the canonical top-level ID and canonical
provenance that later lanes and the audit read.  Rewards run last so their
restoration sidecar binds the final record emitted by every earlier mutation.
The coding slot dispatches episode records to ``curate_coding`` and registered
multi-agent/safety-case records to ``curate_agentic``.  The remaining lanes are
shape-gated with the same predicates the lanes themselves use, so a Thalamic
record is never quarantined for "not a bridge pair".

Layout of the destination::

    <destination>/records/<factory>/<file>.jsonl   curated payload (audited)
    <destination>/manifest/compose-manifest.jsonl  one entry per source record
    <destination>/manifest/reward-sidecars.jsonl   reversible reward sources
    <destination>/COMPOSE.json                     counts, hashes, audit

``records/`` is the only subtree with curated payload, so
``training_audit.audit_run`` can be pointed at it without seeing the manifest.

This command never mutates the source run and never replaces an existing
destination.  It does not promote, publish, or train.

Usage::

    python3 pipelines/compose_curated.py outputs/raw/2026-08-17 outputs/curated/2026-08-23
    python3 pipelines/compose_curated.py --strict <source_run> <destination>
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import stat
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, MutableMapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_agentic  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_identity  # noqa: E402
import curate_preferences  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402
from check_records import reject_json_constant  # noqa: E402
from record_kind import PREFERENCE_SIDE_KINDS, preference_side_kinds  # noqa: E402
from validate_run import THALAMIC_CORE_KEYS, check_episode  # noqa: E402

try:  # PR #93 is a sibling stack; consume its reviewed contract when present.
    import curate_trajectory_preferences  # type: ignore[import-not-found]  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - branch topology decides this
    if exc.name != "curate_trajectory_preferences":
        raise
    curate_trajectory_preferences = None

COMPOSE_NAME = "compose_curated"
COMPOSE_VERSION = "curated-compose-v4"
LANE_ORDER = ("identity", "bridge", "preferences", "coding", "rewards")

RECORDS_DIRNAME = "records"
MANIFEST_DIRNAME = "manifest"
MANIFEST_FILENAME = "compose-manifest.jsonl"
REWARD_SIDECAR_FILENAME = "reward-sidecars.jsonl"
SUMMARY_FILENAME = "COMPOSE.json"

ACTION_RETAINED = "retained"
ACTION_EXCLUDED = "excluded"
ACTION_NOT_APPLICABLE = "not_applicable"

REASON_INVALID_UTF8 = "compose.source_line_invalid_utf8"
REASON_INVALID_JSON = "compose.source_line_invalid_json"
REASON_DUPLICATE_SOURCE_RECORD = "compose.source_record_semantic_duplicate"
REASON_DUPLICATE_CURATED_RECORD = "compose.curated_record_semantic_duplicate"
REASON_REWARD_ONTOLOGY = "compose.reward_ontology_refused"
REASON_MIXED_PREFERENCE_FAMILIES = "compose.preference_side_families_mixed"
REASON_TRAJECTORY_SIDE_INVALID = "TRAJECTORY_PAIR_SIDE_EPISODE_INVALID"
REASON_TRAJECTORY_STEPS_INVALID = "TRAJECTORY_STEPS_MISSING_OR_INVALID"
REASON_TRAJECTORY_STEPS_EMPTY = "TRAJECTORY_STEPS_EMPTY"
REASON_TRAJECTORY_IDENTICAL = "TRAJECTORY_PAIR_IDENTICAL"
REASON_TRAJECTORY_PREFIX_ABSENT = "TRAJECTORY_PREFIX_OVERLAP_ABSENT"
REASON_TRAJECTORY_OUTCOME_MISSING = "TRAJECTORY_OUTCOME_MISSING"
REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT = "TRAJECTORY_OUTCOME_DOES_NOT_DIVERGE"
REASON_TRAJECTORY_REWARD_MISSING = "TRAJECTORY_REWARD_MISSING"
REASON_TRAJECTORY_REWARD_NOT_DIVERGENT = "TRAJECTORY_REWARD_DOES_NOT_DIVERGE"
REASON_TRAJECTORY_GATE_PASSED = "TRAJECTORY_PAIR_SHARED_GOAL_AND_PREFIX"
REASON_TRAJECTORY_GOAL_NORMALIZED = "TRAJECTORY_GOAL_WHITESPACE_NORMALIZED"
REASON_EMPTY_CORPUS = "curated corpus contains no records"

# ``curate_preferences`` keeps its candidate predicate private.  These are the
# same keys it selects on; ``tests/test_compose_curated.py`` pins the parity so
# the two cannot drift apart silently.
PREFERENCE_CANDIDATE_KEYS = ("chosen", "rejected", "reward_delta")

FFPC_UNITS_MIGRATION = "failure-as-fuel-preference-cascade/units-migration.json"
TRAJECTORY_GOAL_LOCATIONS = (("goal",), ("chosen", "goal"), ("rejected", "goal"))


class ComposeError(RuntimeError):
    """Raised when composition input, output, or run integrity is unsafe."""


@dataclass(frozen=True)
class ComposeDecision:
    """One deterministic compose decision and its per-lane evidence."""

    action: str
    record: dict[str, Any] | None
    reason_codes: tuple[str, ...]
    stages: tuple[dict[str, Any], ...]
    reward_sidecar: dict[str, Any] | None
    output_id: str | None


@dataclass(frozen=True)
class _TrajectoryPreferenceDecision:
    """Small compatibility surface for the reviewed PR #93 trajectory gate."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    shared_goal: bool | None
    overlap: dict[str, Any] | None
    side_validation_errors: dict[str, tuple[str, ...]] | None = None


def canonical_json(value: Any) -> str:
    """Serialize JSON data byte-stably (shared with the curation lanes)."""

    return curate_identity.canonical_json(value)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return sha256_hex(canonical_json(value).encode("utf-8"))


def is_bridge_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_bridge.curate_record`` applies itself."""

    return (
        isinstance(record, Mapping)
        and "language_view" in record
        and isinstance(record.get("spike_events"), list)
    )


def is_preference_record(record: Mapping[str, Any]) -> bool:
    """Mirror the candidate gate ``curate_preferences`` applies to a corpus."""

    return isinstance(record, Mapping) and any(
        key in record for key in PREFERENCE_CANDIDATE_KEYS
    )


def is_episode_record(record: Mapping[str, Any]) -> bool:
    """Mirror the shape gate ``curate_coding.curate_episode`` applies itself."""

    return isinstance(record, Mapping) and isinstance(record.get("steps"), list)


def _mixed_preference_families(side_kinds: tuple[str, str]) -> bool:
    """Whether two recognized preference-side families disagree."""

    return (
        all(kind in PREFERENCE_SIDE_KINDS for kind in side_kinds)
        and side_kinds[0] != side_kinds[1]
    )


def _is_same_state_pair(record: Mapping[str, Any]) -> bool:
    """Match PR #93's precedence for Fable same-context preference pairs.

    A side can carry episode fields in addition to ``state`` and
    ``proposed_action``.  Those extra fields must not move the pair into the
    trajectory lane and bypass its state/proposal equality contract.
    """

    sides = (record.get("chosen"), record.get("rejected"))
    return all(
        isinstance(side, Mapping)
        and all(
            isinstance(side.get(field_name), Mapping)
            for field_name in ("state", "proposed_action")
        )
        for side in sides
    )


def _trajectory_side_validation_errors(
    record: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    """Run the canonical episode validator over each trajectory-preference side."""

    found: dict[str, tuple[str, ...]] = {}
    for side_name in ("chosen", "rejected"):
        side = record.get(side_name)
        if not isinstance(side, dict):
            continue
        errors = check_episode(side, side_name, require_goal=False)
        if all(key in side for key in THALAMIC_CORE_KEYS):
            errors.append(f"{side_name}: Thalamic trajectory side is not an episode")
        if errors:
            found[side_name] = tuple(errors)
    return found


def _trajectory_goal_owner(
    record: dict[str, Any], path: tuple[str, ...]
) -> dict[str, Any] | None:
    owner: Any = record
    for key in path[:-1]:
        owner = owner.get(key) if isinstance(owner, dict) else None
    return owner if isinstance(owner, dict) else None


def _normalize_trajectory_goal_whitespace(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Apply PR #93's evidence-preserving goal whitespace repair."""

    present: list[tuple[tuple[str, ...], str]] = []
    for path in TRAJECTORY_GOAL_LOCATIONS:
        owner = _trajectory_goal_owner(record, path)
        if owner is None:
            continue
        value = owner.get(path[-1])
        if isinstance(value, str):
            present.append((path, value))
    if len(present) < 2:
        return None
    values = [value for _path, value in present]
    normalized = {" ".join(value.split()) for value in values}
    if len(set(values)) == 1 or len(normalized) != 1:
        return None
    canonical_goal = normalized.pop()
    if not canonical_goal:
        return None

    repaired = copy.deepcopy(record)
    for path, _value in present:
        owner = _trajectory_goal_owner(repaired, path)
        if owner is not None:
            owner[path[-1]] = canonical_goal
    return repaired


def _compat_trajectory_preference(
    record: dict[str, Any],
) -> _TrajectoryPreferenceDecision:
    """Enforce PR #93's non-repairing core when its sibling module is absent.

    The sibling owns richer reject diagnostics. This compatibility path keeps
    its acceptance contract and evidence-preserving repairs: valid episode
    sides, one goal, a non-empty shared step prefix, non-identical trajectories,
    divergent outcome and reward evidence, hidden-thought removal, and
    whitespace-only goal normalization.
    """

    curated, removed_thoughts = curate_agentic.strip_hidden_thought_keys(record)
    normalized = _normalize_trajectory_goal_whitespace(curated)
    if normalized is not None:
        curated = normalized
    reasons: list[str] = []
    shared_goal, goal_reason = curate_agentic.shared_preference_goal(curated)
    if not shared_goal and goal_reason is not None:
        reasons.append(goal_reason)

    side_errors = _trajectory_side_validation_errors(curated)
    if side_errors:
        reasons.append(REASON_TRAJECTORY_SIDE_INVALID)

    chosen = curated.get("chosen")
    rejected = curated.get("rejected")
    chosen_steps = chosen.get("steps") if isinstance(chosen, dict) else None
    rejected_steps = rejected.get("steps") if isinstance(rejected, dict) else None
    overlap = curate_agentic.prefix_overlap(chosen, rejected)
    if not isinstance(chosen_steps, list) or not isinstance(rejected_steps, list):
        reasons.append(REASON_TRAJECTORY_STEPS_INVALID)
    elif not chosen_steps or not rejected_steps:
        reasons.append(REASON_TRAJECTORY_STEPS_EMPTY)
    else:
        if canonical_json(chosen_steps) == canonical_json(rejected_steps):
            reasons.append(REASON_TRAJECTORY_IDENTICAL)
        if not overlap["shared_steps"]:
            reasons.append(REASON_TRAJECTORY_PREFIX_ABSENT)

    if isinstance(chosen, dict) and isinstance(rejected, dict):
        for field, missing_reason, same_reason in (
            (
                "outcome",
                REASON_TRAJECTORY_OUTCOME_MISSING,
                REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
            ),
            (
                "reward",
                REASON_TRAJECTORY_REWARD_MISSING,
                REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
            ),
        ):
            if chosen.get(field) is None or rejected.get(field) is None:
                reasons.append(missing_reason)
            elif canonical_json(chosen[field]) == canonical_json(rejected[field]):
                reasons.append(same_reason)

    if reasons:
        return _TrajectoryPreferenceDecision(
            action=ACTION_EXCLUDED,
            classification="unsupported_trajectory_pair",
            reason_codes=tuple(dict.fromkeys(reasons)),
            record=None,
            shared_goal=shared_goal,
            overlap=overlap,
            side_validation_errors=side_errors or None,
        )

    passed_reasons = []
    if removed_thoughts:
        passed_reasons.append(curate_agentic.REASON_THOUGHT_REMOVED)
    if normalized is not None:
        passed_reasons.append(REASON_TRAJECTORY_GOAL_NORMALIZED)
    passed_reasons.append(REASON_TRAJECTORY_GATE_PASSED)
    return _TrajectoryPreferenceDecision(
        action=(
            "repaired"
            if removed_thoughts or normalized is not None
            else ACTION_RETAINED
        ),
        classification=(
            "trajectory_pair_repaired"
            if removed_thoughts or normalized is not None
            else "trajectory_pair_gate_passed"
        ),
        reason_codes=tuple(passed_reasons),
        record=curated,
        shared_goal=True,
        overlap=overlap,
    )


def _trajectory_preference(
    record: dict[str, Any],
) -> tuple[Any, str, str, str]:
    """Return a trajectory decision plus transform identity and implementation."""

    if curate_trajectory_preferences is not None:
        return (
            curate_trajectory_preferences.curate_trajectory_pair(record),
            curate_trajectory_preferences.TRANSFORM_NAME,
            curate_trajectory_preferences.TRANSFORM_VERSION,
            "reviewed_module",
        )
    return (
        _compat_trajectory_preference(record),
        "trajectory-pair-preference-curation",
        "1.1.0-compatible-core",
        "compatible_core",
    )


def _trajectory_side_needs_coding(side: Any) -> bool:
    """Whether an episode side needs the coding lane before preference checks."""

    if not isinstance(side, dict):
        return False
    if curate_coding.contains_hidden_reasoning_key(side):
        return True
    steps = side.get("steps")
    return isinstance(steps, list) and any(
        isinstance(step, dict)
        and (
            not isinstance(step.get("decision_basis"), str)
            or not step["decision_basis"].strip()
        )
        for step in steps
    )


def _curate_trajectory_sides(
    record: dict[str, Any],
    *,
    source_path: str,
    source_line: int,
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], list[str], bool]:
    """Migrate repairable episode sides before the trajectory preference gate."""

    curated = copy.deepcopy(record)
    manifests: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    changed = False
    failed = False
    for side_name in ("chosen", "rejected"):
        side = curated.get(side_name)
        if not _trajectory_side_needs_coding(side):
            manifests[side_name] = {
                "transform_name": curate_coding.TRANSFORM_NAME,
                "transform_version": curate_coding.TRANSFORM_VERSION,
                "action": ACTION_NOT_APPLICABLE,
                "reason_codes": [],
            }
            continue
        curated_side, manifest = curate_coding.curate_episode(
            side,
            source_path=f"{source_path}#{side_name}",
            source_line=source_line,
            source_hash=_canonical_sha256(side),
        )
        detail = copy.deepcopy(manifest)
        detail["transform_name"] = curate_coding.TRANSFORM_NAME
        detail["transform_version"] = curate_coding.TRANSFORM_VERSION
        manifests[side_name] = detail
        reasons.extend(detail.get("reason_codes", []))
        if curated_side is None:
            failed = True
            continue
        changed = changed or curated_side != side
        curated[side_name] = curated_side
    return (
        None if failed else curated,
        manifests,
        list(dict.fromkeys(reasons)),
        changed,
    )


def _stage(lane: str, name: str, version: str, action: str, **extra: Any) -> dict[str, Any]:
    stage: dict[str, Any] = {
        "lane": lane,
        "transform_name": name,
        "transform_version": version,
        "action": action,
        "reason_codes": list(extra.pop("reason_codes", []) or []),
    }
    stage.update(extra)
    return stage


def calibration_for(record: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> Any:
    """Look a reward calibration up by the record's *source* identifier.

    ``curate_rewards`` resolves calibrations from ``id``/``meta.id``.  Compose
    runs the identity lane first, which replaces ``id`` with a canonical
    digest, so the lookup has to use the pre-identity record.
    """

    if not catalog or not isinstance(record, Mapping):
        return None
    record_id = record.get("id")
    if not isinstance(record_id, str):
        meta = record.get("meta")
        record_id = meta.get("id") if isinstance(meta, Mapping) else None
    if not isinstance(record_id, str):
        return None
    return catalog.get(record_id.lower())


def compose_record(
    record: Any,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None = None,
    calibration: Any = None,
) -> ComposeDecision:
    """Run every applicable lane over one record without mutating the input."""

    stages: list[dict[str, Any]] = []
    source_side_kinds = (
        preference_side_kinds(record)
        if is_preference_record(record) and isinstance(record, Mapping)
        else None
    )
    source_same_state_pair = (
        _is_same_state_pair(record)
        if is_preference_record(record) and isinstance(record, Mapping)
        else False
    )
    mixed_preference_families = (
        source_side_kinds is not None
        and not source_same_state_pair
        and _mixed_preference_families(source_side_kinds)
    )

    identity_result = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=record,
            source_path=source_path,
            source_line=source_line,
            source_sha256=source_sha256,
        )
    )
    identity_reasons = list(identity_result.mapping.get("reason_codes", []))
    identity_detail = copy.deepcopy(identity_result.mapping)
    if source_side_kinds is not None:
        identity_detail["preference_side_kinds"] = list(source_side_kinds)
    if mixed_preference_families:
        # Identity correctly refuses this shape first. Replace its generic
        # unsupported-shape summary with the composition contract's explicit
        # family mismatch while retaining the identity diagnostics as detail.
        identity_detail["identity_reason_codes"] = identity_reasons
        identity_reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    stages.append(
        _stage(
            "identity",
            curate_identity.TRANSFORM_NAME,
            curate_identity.TRANSFORM_VERSION,
            ACTION_RETAINED if identity_result.action == "retained" else ACTION_EXCLUDED,
            reason_codes=identity_reasons,
            lane_action=identity_result.action,
            detail=identity_detail,
        )
    )
    if identity_result.action != "retained" or identity_result.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED, None, tuple(identity_reasons), tuple(stages), None, None
        )
    current: dict[str, Any] = identity_result.record
    registered_kind = identity_result.mapping.get("record_kind")

    if is_bridge_record(current):
        bridge_decision = curate_bridge.curate_record(
            current,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
            source_file_hash=source_file_sha256,
        )
        bridge_reasons = list(bridge_decision.manifest.get("reason_codes", []))
        retained = bridge_decision.output_record is not None
        stages.append(
            _stage(
                "bridge",
                curate_bridge.TRANSFORM_NAME,
                curate_bridge.TRANSFORM_VERSION,
                ACTION_RETAINED if retained else ACTION_EXCLUDED,
                reason_codes=bridge_reasons,
                lane_action=bridge_decision.action,
                detail=bridge_decision.manifest,
            )
        )
        if not retained:
            return ComposeDecision(
                ACTION_EXCLUDED, None, tuple(bridge_reasons), tuple(stages), None, None
            )
        current = bridge_decision.output_record
    else:
        stages.append(
            _stage(
                "bridge",
                curate_bridge.TRANSFORM_NAME,
                curate_bridge.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )

    if is_preference_record(current):
        side_kinds = preference_side_kinds(current)
        if _is_same_state_pair(current):
            (
                curated_sides,
                side_curation,
                side_curation_reasons,
                side_curation_changed,
            ) = _curate_trajectory_sides(
                current,
                source_path=source_path,
                source_line=source_line,
            )
            if curated_sides is None:
                preference_reasons = list(
                    dict.fromkeys(
                        [REASON_TRAJECTORY_SIDE_INVALID, *side_curation_reasons]
                    )
                )
                stages.append(
                    _stage(
                        "preferences",
                        COMPOSE_NAME,
                        COMPOSE_VERSION,
                        ACTION_EXCLUDED,
                        reason_codes=preference_reasons,
                        lane_action=ACTION_EXCLUDED,
                        classification="same_state_side_curation_failed",
                        side_kinds=list(side_kinds),
                        schema="same_state_pair",
                        side_curation=side_curation,
                        side_curation_changed=side_curation_changed,
                    )
                )
                return ComposeDecision(
                    ACTION_EXCLUDED,
                    None,
                    tuple(preference_reasons),
                    tuple(stages),
                    None,
                    None,
                )
            preference_decision = curate_preferences.curate_preference_record(
                curated_sides
            )
            retained = preference_decision.record is not None
            preference_reasons = list(preference_decision.reason_codes)
            if retained:
                preference_reasons = list(
                    dict.fromkeys(
                        [*side_curation_reasons, *preference_reasons]
                    )
                )
            stages.append(
                _stage(
                    "preferences",
                    curate_preferences.TRANSFORM_NAME,
                    curate_preferences.TRANSFORM_VERSION,
                    ACTION_RETAINED if retained else ACTION_EXCLUDED,
                    reason_codes=preference_reasons,
                    lane_action=(
                        "repaired"
                        if retained and side_curation_changed
                        else preference_decision.action
                    ),
                    classification=preference_decision.classification,
                    side_kinds=list(side_kinds),
                    schema="same_state_pair",
                    context_diff_paths=list(preference_decision.context_diff_paths),
                    side_curation=side_curation,
                    side_curation_changed=side_curation_changed,
                )
            )
        elif _mixed_preference_families(side_kinds):
            preference_reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
            stages.append(
                _stage(
                    "preferences",
                    COMPOSE_NAME,
                    COMPOSE_VERSION,
                    ACTION_EXCLUDED,
                    reason_codes=preference_reasons,
                    lane_action=ACTION_EXCLUDED,
                    classification="mixed_preference_side_families",
                    side_kinds=list(side_kinds),
                )
            )
            return ComposeDecision(
                ACTION_EXCLUDED,
                None,
                tuple(preference_reasons),
                tuple(stages),
                None,
                None,
            )

        elif side_kinds == ("episode", "episode"):
            (
                curated_sides,
                side_curation,
                side_curation_reasons,
                side_curation_changed,
            ) = _curate_trajectory_sides(
                current,
                source_path=source_path,
                source_line=source_line,
            )
            if curated_sides is None:
                preference_reasons = list(
                    dict.fromkeys(
                        [REASON_TRAJECTORY_SIDE_INVALID, *side_curation_reasons]
                    )
                )
                stages.append(
                    _stage(
                        "preferences",
                        COMPOSE_NAME,
                        COMPOSE_VERSION,
                        ACTION_EXCLUDED,
                        reason_codes=preference_reasons,
                        lane_action=ACTION_EXCLUDED,
                        classification="trajectory_side_curation_failed",
                        side_kinds=list(side_kinds),
                        side_curation=side_curation,
                        side_curation_changed=side_curation_changed,
                    )
                )
                return ComposeDecision(
                    ACTION_EXCLUDED,
                    None,
                    tuple(preference_reasons),
                    tuple(stages),
                    None,
                    None,
                )
            preference_decision, transform_name, transform_version, implementation = (
                _trajectory_preference(curated_sides)
            )
            preference_reasons = list(
                dict.fromkeys(
                    [*side_curation_reasons, *preference_decision.reason_codes]
                )
            )
            retained = preference_decision.record is not None
            stages.append(
                _stage(
                    "preferences",
                    transform_name,
                    transform_version,
                    ACTION_RETAINED if retained else ACTION_EXCLUDED,
                    reason_codes=preference_reasons,
                    lane_action=(
                        "repaired"
                        if retained and side_curation_changed
                        else preference_decision.action
                    ),
                    classification=preference_decision.classification,
                    side_kinds=list(side_kinds),
                    implementation=implementation,
                    shared_goal=preference_decision.shared_goal,
                    overlap=preference_decision.overlap,
                    side_validation_errors=(
                        preference_decision.side_validation_errors or {}
                    ),
                    side_curation=side_curation,
                    side_curation_changed=side_curation_changed,
                )
            )
        else:
            preference_decision = curate_preferences.curate_preference_record(current)
            preference_reasons = list(preference_decision.reason_codes)
            retained = preference_decision.record is not None
            stages.append(
                _stage(
                    "preferences",
                    curate_preferences.TRANSFORM_NAME,
                    curate_preferences.TRANSFORM_VERSION,
                    ACTION_RETAINED if retained else ACTION_EXCLUDED,
                    reason_codes=preference_reasons,
                    lane_action=preference_decision.action,
                    classification=preference_decision.classification,
                    side_kinds=list(side_kinds),
                    context_diff_paths=list(preference_decision.context_diff_paths),
                )
            )
        if not retained:
            return ComposeDecision(
                ACTION_EXCLUDED,
                None,
                tuple(preference_reasons),
                tuple(stages),
                None,
                None,
            )
        current = preference_decision.record
    else:
        stages.append(
            _stage(
                "preferences",
                curate_preferences.TRANSFORM_NAME,
                curate_preferences.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )

    if registered_kind in {"multi_agent", "safety_case"}:
        curated_agentic, agentic_manifest = curate_agentic.curate_record(
            current,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
        )
        agentic_reasons = list(agentic_manifest.get("reason_codes", []))
        stages.append(
            _stage(
                "coding",
                curate_agentic.TRANSFORM_NAME,
                curate_agentic.TRANSFORM_VERSION,
                ACTION_RETAINED if curated_agentic is not None else ACTION_EXCLUDED,
                reason_codes=agentic_reasons,
                lane_action=agentic_manifest.get("action"),
                detail=agentic_manifest,
            )
        )
        if curated_agentic is None:
            return ComposeDecision(
                ACTION_EXCLUDED,
                None,
                tuple(agentic_reasons),
                tuple(stages),
                None,
                None,
            )
        current = curated_agentic
    elif is_episode_record(current):
        curated_episode, coding_manifest = curate_coding.curate_episode(
            current,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
        )
        coding_reasons = list(coding_manifest.get("reason_codes", []))
        stages.append(
            _stage(
                "coding",
                curate_coding.TRANSFORM_NAME,
                curate_coding.TRANSFORM_VERSION,
                ACTION_RETAINED if curated_episode is not None else ACTION_EXCLUDED,
                reason_codes=coding_reasons,
                lane_action=coding_manifest.get("action"),
                detail=coding_manifest,
            )
        )
        if curated_episode is None:
            return ComposeDecision(
                ACTION_EXCLUDED, None, tuple(coding_reasons), tuple(stages), None, None
            )
        current = curated_episode
    else:
        stages.append(
            _stage(
                "coding",
                curate_coding.TRANSFORM_NAME,
                curate_coding.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )

    sidecar: dict[str, Any] | None = None
    try:
        annotated, reward_sidecar = curate_rewards.curate_record(
            current,
            source_path=source_path,
            source_line=source_line,
            calibration=calibration,
        )
    except curate_rewards.RewardOntologyError as exc:
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.ONTOLOGY_VERSION,
                ACTION_EXCLUDED,
                reason_codes=[REASON_REWARD_ONTOLOGY],
                lane_action=ACTION_EXCLUDED,
                detail={"error": str(exc)},
            )
        )
        return ComposeDecision(
            ACTION_EXCLUDED,
            None,
            (REASON_REWARD_ONTOLOGY,),
            tuple(stages),
            None,
            None,
        )
    annotation = annotated[curate_rewards.ANNOTATION_FIELD]
    if annotation["source_reward_count"]:
        current = annotated
        sidecar = reward_sidecar
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.ONTOLOGY_VERSION,
                ACTION_RETAINED,
                reason_codes=annotation["reason_codes"],
                lane_action=annotation["comparability"],
                comparability=annotation["comparability"],
                source_sidecar_id=annotation["source_sidecar_id"],
                source_reward_count=annotation["source_reward_count"],
            )
        )
    else:
        # ``curate_record`` removes any incoming annotation before rebuilding
        # it. Adopt that stripped result, then omit the newly generated empty
        # annotation and sidecar so stale reward_training can never survive.
        current = annotated
        current.pop(curate_rewards.ANNOTATION_FIELD, None)
        stages.append(
            _stage(
                "rewards",
                curate_rewards.ANNOTATION_FIELD,
                curate_rewards.ONTOLOGY_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
                source_reward_count=0,
            )
        )

    output_id = current.get("id") if isinstance(current, dict) else None
    reasons = tuple(
        dict.fromkeys(
            reason
            for stage in stages
            for reason in stage["reason_codes"]
        )
    )
    return ComposeDecision(
        ACTION_RETAINED,
        current,
        reasons,
        tuple(stages),
        sidecar,
        output_id if isinstance(output_id, str) else None,
    )


def _identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    """Resolve an identity manifest owner pointer within one curated record."""

    if pointer == "/":
        return record
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    owner: Any = record
    for token in pointer[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(owner, dict):
            return None
        owner = owner.get(key)
    return owner if isinstance(owner, dict) else None


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    """Drop one JSON-pointer field from a copied record, if it still exists."""

    if not isinstance(pointer, str) or not pointer.startswith("/") or pointer == "/":
        return
    tokens = [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Collect every identity-mapped legacy identifier path for one record."""

    if not isinstance(detail, Mapping):
        return ()
    paths: list[str] = []
    seen: set[str] = set()

    def add_originals(originals: Any) -> None:
        if not isinstance(originals, list):
            return
        for item in originals:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if isinstance(path, str) and path not in seen:
                seen.add(path)
                paths.append(path)

    add_originals(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                add_originals(mapping.get("original_ids"))
    return tuple(paths)


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    """Hash training content without coordinate-derived identity bindings."""

    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    identity_stage = next(
        (stage for stage in decision.stages if stage.get("lane") == "identity"),
        None,
    )
    detail = identity_stage.get("detail") if isinstance(identity_stage, dict) else None
    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    if isinstance(mappings, list):
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            owner = _identity_owner(semantic, mapping.get("owner_path"))
            if owner is not None and owner.get("id") == mapping.get("output_id"):
                owner.pop("id", None)
    for path in _mapped_legacy_id_paths(detail if isinstance(detail, dict) else None):
        _pop_json_pointer(semantic, path)

    meta = semantic.get("meta")
    if isinstance(meta, dict):
        # The same episode can be authorized under more than one factory
        # path_id (the registry declares dozens of distinct "episode"-kind
        # factories). ``meta.factory``/``meta.generator`` name which pipeline
        # and model produced the row, not part of the trained-on content, so
        # two rows that are otherwise byte-identical after curation must not
        # be kept apart by that label alone -- doing so would let the same
        # content land in both the train and eval split. Normalize both
        # fields out of the digest; they stay untouched on the emitted
        # record itself, since ``semantic`` is a deep copy.
        meta.pop("factory", None)
        meta.pop("generator", None)

    annotation = semantic.get(curate_rewards.ANNOTATION_FIELD)
    if isinstance(annotation, dict):
        # The sidecar digest authenticates source coordinates.  Keep the
        # comparability class and any magnitude/order payload, but remove the
        # coordinate binding that would otherwise hide converged examples.
        annotation.pop("source_sidecar_id", None)
    return _canonical_sha256(semantic)


def _deduplicate_curated_record(
    decision: ComposeDecision,
    *,
    source_path: str,
    source_line: int,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None,
) -> ComposeDecision:
    """Exclude records that converge only after the lossy curation lanes."""

    if (
        seen_curated_semantics is None
        or decision.action != ACTION_RETAINED
        or decision.record is None
    ):
        return decision
    semantic_sha256 = _post_transform_semantic_sha256(decision)
    first_coordinate = seen_curated_semantics.get(semantic_sha256)
    if first_coordinate is None:
        seen_curated_semantics[semantic_sha256] = (source_path, source_line)
        return decision
    duplicate_stage = _stage(
        "post_transform_dedup",
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=semantic_sha256,
        first_source_path=first_coordinate[0],
        first_source_line=first_coordinate[1],
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (REASON_DUPLICATE_CURATED_RECORD,),
        (*decision.stages, duplicate_stage),
        None,
        None,
    )


def compose_source_line(
    physical_line: bytes,
    *,
    source_path: str,
    source_line: int,
    source_file_sha256: str,
    calibration_catalog: Mapping[str, Any] | None = None,
    seen_source_semantics: MutableMapping[str, tuple[str, int]] | None = None,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None = None,
) -> ComposeDecision:
    """Compose one LF-framed source line using the run writer's exact contract."""

    source_sha256 = sha256_hex(physical_line)
    try:
        text = physical_line.decode("utf-8")
    except UnicodeDecodeError as exc:
        return ComposeDecision(
            ACTION_EXCLUDED,
            None,
            (REASON_INVALID_UTF8,),
            (
                _stage(
                    "source",
                    COMPOSE_NAME,
                    COMPOSE_VERSION,
                    ACTION_EXCLUDED,
                    reason_codes=[REASON_INVALID_UTF8],
                    detail={"error": str(exc)},
                ),
            ),
            None,
            None,
        )
    try:
        record = json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        return ComposeDecision(
            ACTION_EXCLUDED,
            None,
            (REASON_INVALID_JSON,),
            (
                _stage(
                    "source",
                    COMPOSE_NAME,
                    COMPOSE_VERSION,
                    ACTION_EXCLUDED,
                    reason_codes=[REASON_INVALID_JSON],
                    detail={"error": str(exc)},
                ),
            ),
            None,
            None,
        )
    semantic_sha256 = _canonical_sha256(record)
    if seen_source_semantics is not None:
        first_coordinate = seen_source_semantics.get(semantic_sha256)
        if first_coordinate is not None:
            return ComposeDecision(
                ACTION_EXCLUDED,
                None,
                (REASON_DUPLICATE_SOURCE_RECORD,),
                (
                    _stage(
                        "source",
                        COMPOSE_NAME,
                        COMPOSE_VERSION,
                        ACTION_EXCLUDED,
                        reason_codes=[REASON_DUPLICATE_SOURCE_RECORD],
                        detail={
                            "semantic_sha256": semantic_sha256,
                            "first_source_path": first_coordinate[0],
                            "first_source_line": first_coordinate[1],
                        },
                    ),
                ),
                None,
                None,
            )
    decision = compose_record(
        record,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
        source_file_sha256=source_file_sha256,
        calibration=calibration_for(record, calibration_catalog),
    )
    decision = _deduplicate_curated_record(
        decision,
        source_path=source_path,
        source_line=source_line,
        seen_curated_semantics=seen_curated_semantics,
    )
    if (
        seen_source_semantics is not None
        and decision.action == ACTION_RETAINED
        and decision.record is not None
    ):
        seen_source_semantics[semantic_sha256] = (source_path, source_line)
    return decision


def transform_contract() -> dict[str, Any]:
    """Return the exact transform declaration written into ``COMPOSE.json``."""

    return {
        "identity": {
            "name": curate_identity.TRANSFORM_NAME,
            "version": curate_identity.TRANSFORM_VERSION,
        },
        "bridge": {
            "name": curate_bridge.TRANSFORM_NAME,
            "version": curate_bridge.TRANSFORM_VERSION,
        },
        "preferences": {
            "name": curate_preferences.TRANSFORM_NAME,
            "version": curate_preferences.TRANSFORM_VERSION,
            "trajectory": {
                "name": (
                    curate_trajectory_preferences.TRANSFORM_NAME
                    if curate_trajectory_preferences is not None
                    else "trajectory-pair-preference-curation"
                ),
                "version": (
                    curate_trajectory_preferences.TRANSFORM_VERSION
                    if curate_trajectory_preferences is not None
                    else "1.1.0-compatible-core"
                ),
                "implementation": (
                    "reviewed_module"
                    if curate_trajectory_preferences is not None
                    else "compatible_core"
                ),
            },
        },
        "coding": {
            "name": curate_coding.TRANSFORM_NAME,
            "version": curate_coding.TRANSFORM_VERSION,
            "registered_agentic": {
                "name": curate_agentic.TRANSFORM_NAME,
                "version": curate_agentic.TRANSFORM_VERSION,
                "record_kinds": ["multi_agent", "safety_case"],
            },
        },
        "rewards": {
            "name": curate_rewards.ANNOTATION_FIELD,
            "version": curate_rewards.ONTOLOGY_VERSION,
        },
    }


def _contains_raw_segments(parts: tuple[str, ...]) -> bool:
    return any(
        parts[index : index + 2] == ("outputs", "raw") for index in range(len(parts) - 1)
    )


def _is_under_raw(path: Path) -> bool:
    """Reject lexical raw aliases as well as symlink-resolved raw paths."""

    return _contains_raw_segments(path.parts) or _contains_raw_segments(
        path.resolve(strict=False).parts
    )


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ComposeError(f"{label} is missing: {path}") from exc
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode) or resolved != absolute:
        raise ComposeError(f"{label} must be an exact non-symlink directory: {path}")
    return resolved


def _directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    """Identity fields that do not change when directory entries are added."""

    return (metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode))


def _verify_directory_binding(
    path: Path,
    descriptor: int,
    label: str,
    *,
    expected_identity: tuple[int, int, int] | None = None,
) -> None:
    """Require ``path`` and a pinned descriptor to name the same directory."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        opened = os.fstat(descriptor)
    except (FileNotFoundError, OSError) as exc:
        raise ComposeError(f"{label} changed while it was pinned: {path}") from exc
    absolute = Path(os.path.abspath(path))
    path_identity = _directory_identity(metadata)
    opened_identity = _directory_identity(opened)
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or not stat.S_ISDIR(opened.st_mode)
        or resolved != absolute
        or path_identity != opened_identity
        or (expected_identity is not None and opened_identity != expected_identity)
    ):
        raise ComposeError(f"{label} changed while it was pinned: {path}")


@dataclass
class _PinnedDestination:
    """A new destination held by directory descriptors until commit or cleanup."""

    path: Path
    root: Path
    parent_descriptor: int
    destination_descriptor: int
    parent_identity: tuple[int, int, int]
    destination_identity: tuple[int, int, int]
    closed: bool = False

    def _entry_is_ours(self) -> bool:
        try:
            current = os.stat(
                self.path.name,
                dir_fd=self.parent_descriptor,
                follow_symlinks=False,
            )
        except (FileNotFoundError, OSError):
            return False
        return (
            stat.S_ISDIR(current.st_mode)
            and _directory_identity(current) == self.destination_identity
        )

    def cleanup(self) -> None:
        """Remove only the directory created through the pinned parent."""

        if self.closed:
            return
        os.close(self.destination_descriptor)
        if self._entry_is_ours():
            shutil.rmtree(
                self.path.name,
                ignore_errors=True,
                dir_fd=self.parent_descriptor,
            )
        os.close(self.parent_descriptor)
        self.closed = True

    def finish(self) -> None:
        """Verify the lexical bindings survived, then release the descriptors."""

        if self.closed:
            raise ComposeError("destination pin was already closed")
        try:
            _verify_directory_binding(
                self.path.parent,
                self.parent_descriptor,
                "destination parent",
                expected_identity=self.parent_identity,
            )
            _verify_directory_binding(
                self.path,
                self.destination_descriptor,
                "destination",
                expected_identity=self.destination_identity,
            )
        except BaseException:
            self.cleanup()
            raise
        os.close(self.destination_descriptor)
        os.close(self.parent_descriptor)
        self.closed = True


def _source_member_path(root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular source member without aliases or tree escape."""

    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        raise ComposeError(f"{label}: path must be a nonempty POSIX string")
    relative = PurePosixPath(raw_path)
    if (
        relative.as_posix() != raw_path
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ComposeError(f"{label}: unsafe relative path {raw_path!r}")
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(f"{label}: source member is missing: {raw_path}") from exc
    expected = root_resolved.joinpath(*relative.parts)
    if resolved != expected or root_resolved not in resolved.parents:
        raise ComposeError(f"{label}: source member is a symlink alias: {raw_path}")
    if not stat.S_ISREG(metadata.st_mode):
        raise ComposeError(f"{label}: source member is not a regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ComposeError(f"{label}: hard-link aliases are not accepted: {raw_path}")
    return candidate


def _stable_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    """Fields that must remain stable while one source member is read."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _read_exact_regular_file(root: Path, raw_path: Any, label: str) -> tuple[Path, bytes]:
    """Read one unique source file through a pinned descriptor."""

    path = _source_member_path(root, raw_path, label)
    before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc
    opened_before: os.stat_result | None = None
    opened_after: os.stat_result | None = None
    try:
        opened_before = os.fstat(descriptor)
        if not stat.S_ISREG(opened_before.st_mode):
            raise ComposeError(f"{label}: opened identity is not a regular file")
        if opened_before.st_nlink != 1:
            raise ComposeError(f"{label}: hard-link aliases are not accepted")
        if _stable_file_identity(before) != _stable_file_identity(opened_before):
            raise ComposeError(f"{label}: source identity changed while opening")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        opened_after = os.fstat(descriptor)
        if _stable_file_identity(opened_before) != _stable_file_identity(opened_after):
            raise ComposeError(f"{label}: source identity changed while reading")
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except FileNotFoundError as exc:
        raise ComposeError(f"{label}: source member disappeared while reading") from exc
    if opened_after is None or _stable_file_identity(after) != _stable_file_identity(
        opened_after
    ):
        raise ComposeError(f"{label}: source path identity changed while reading")
    expected = root.resolve(strict=True).joinpath(*PurePosixPath(str(raw_path)).parts)
    if path.resolve(strict=True) != expected:
        raise ComposeError(f"{label}: source path became a symlink alias while reading")
    return path, b"".join(chunks)


def _read_exact_child_file(parent: Path, name: str, label: str) -> tuple[Path, bytes]:
    """Read one direct child while its exact parent directory remains pinned."""

    parent = _require_exact_directory(parent, f"{label} parent")
    expected_parent_identity = _directory_identity(parent.lstat())
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_descriptor = os.open(parent, directory_flags)
    except OSError as exc:
        raise ComposeError(f"{label} parent changed while it was pinned: {parent}") from exc
    file_descriptor: int | None = None
    try:
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_parent_identity,
        )
        try:
            before = os.stat(
                name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            file_descriptor = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_descriptor,
            )
        except OSError as exc:
            raise ComposeError(f"{label}: cannot open exact source file: {exc}") from exc
        opened_before = os.fstat(file_descriptor)
        if not stat.S_ISREG(opened_before.st_mode):
            raise ComposeError(f"{label}: opened identity is not a regular file")
        if opened_before.st_nlink != 1:
            raise ComposeError(f"{label}: hard-link aliases are not accepted")
        if _stable_file_identity(before) != _stable_file_identity(opened_before):
            raise ComposeError(f"{label}: source identity changed while opening")
        chunks: list[bytes] = []
        while chunk := os.read(file_descriptor, 1024 * 1024):
            chunks.append(chunk)
        opened_after = os.fstat(file_descriptor)
        after = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            _stable_file_identity(opened_before) != _stable_file_identity(opened_after)
            or _stable_file_identity(after) != _stable_file_identity(opened_after)
        ):
            raise ComposeError(f"{label}: source identity changed while reading")
        _verify_directory_binding(
            parent,
            parent_descriptor,
            f"{label} parent",
            expected_identity=expected_parent_identity,
        )
        return parent / name, b"".join(chunks)
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        os.close(parent_descriptor)


def source_jsonl_members(root: Path) -> tuple[str, ...]:
    """Enumerate a source tree without silently following filesystem aliases."""

    root = _require_exact_directory(root, "source run")
    members: list[str] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        if _require_exact_directory(directory, "source directory") != directory:
            raise ComposeError(f"source directory identity changed: {directory}")
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError as exc:
            raise ComposeError(f"cannot enumerate source directory {directory}: {exc}") from exc
        child_directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ComposeError(f"cannot inspect source member {path}: {exc}") from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise ComposeError(f"source tree contains a symlink alias: {path}")
            if stat.S_ISDIR(metadata.st_mode):
                child_directories.append(path)
                continue
            if not entry.name.endswith(".jsonl"):
                continue
            relative = path.relative_to(root).as_posix()
            _source_member_path(root, relative, f"compose source {relative}")
            members.append(relative)
        pending.extend(reversed(child_directories))
    return tuple(sorted(members))


def _assert_new_destination(
    source_run: Path, destination: Path
) -> tuple[Path, tuple[int, int, int]]:
    if os.path.lexists(destination):
        raise ComposeError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ComposeError(f"refusing to write inside immutable raw evidence: {destination}")
    resolved_source = source_run.resolve()
    resolved_destination = destination.resolve(strict=False)
    if resolved_source == resolved_destination:
        raise ComposeError("destination cannot replace the source run")
    if resolved_source in resolved_destination.parents:
        raise ComposeError("destination cannot be written inside the source run")
    if resolved_destination in resolved_source.parents:
        raise ComposeError("destination cannot contain the source run")
    parent = _require_exact_directory(destination.parent, "destination parent")
    return parent, _directory_identity(parent.lstat())


def _create_pinned_destination(
    source_run: Path, destination: Path
) -> _PinnedDestination:
    """Create one exclusive destination relative to a pinned parent descriptor."""

    parent, expected_parent_identity = _assert_new_destination(
        source_run, destination
    )
    destination = Path(os.path.abspath(destination))
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    parent_descriptor = os.open(parent, flags)
    destination_descriptor: int | None = None
    created_identity: tuple[int, int, int] | None = None
    try:
        _verify_directory_binding(
            parent,
            parent_descriptor,
            "destination parent",
            expected_identity=expected_parent_identity,
        )
        try:
            os.stat(
                destination.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise ComposeError(
                f"refusing to overwrite an existing destination: {destination}"
            )
        os.mkdir(destination.name, 0o755, dir_fd=parent_descriptor)
        created = os.stat(
            destination.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        created_identity = _directory_identity(created)
        if not stat.S_ISDIR(created.st_mode):
            raise ComposeError(f"new destination is not a directory: {destination}")
        destination_descriptor = os.open(
            destination.name,
            flags,
            dir_fd=parent_descriptor,
        )
        if _directory_identity(os.fstat(destination_descriptor)) != created_identity:
            raise ComposeError("destination identity changed while opening")
        root = Path(f"/proc/self/fd/{destination_descriptor}")
        if not root.is_dir():
            raise ComposeError("pinned destination descriptor is not path-addressable")
        return _PinnedDestination(
            path=destination,
            root=root,
            parent_descriptor=parent_descriptor,
            destination_descriptor=destination_descriptor,
            parent_identity=expected_parent_identity,
            destination_identity=created_identity,
        )
    except BaseException:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if created_identity is not None:
            try:
                current = os.stat(
                    destination.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except (FileNotFoundError, OSError):
                current = None
            if current is not None and _directory_identity(current) == created_identity:
                shutil.rmtree(
                    destination.name,
                    ignore_errors=True,
                    dir_fd=parent_descriptor,
                )
        os.close(parent_descriptor)
        raise


def _write_new_text(path: Path, text: str) -> str:
    """Create one new file exclusively and return its SHA-256 digest."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return sha256_hex(text.encode("utf-8"))


def _load_calibration(
    source_run: Path, units_migration: Path | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load calibration plus the exact file evidence needed for later replay."""

    calibration_path: Path | None = None
    mode = "none"
    if units_migration is not None:
        calibration_path = Path(os.path.abspath(units_migration))
        mode = "explicit"
    default = source_run / FFPC_UNITS_MIGRATION
    if calibration_path is None and default.is_file():
        calibration_path = default
        mode = "source_run"
    if calibration_path is None:
        return {}, {
            "mode": mode,
            "path": None,
            "sha256": None,
            "records": 0,
        }
    calibration_path, payload = _read_exact_child_file(
        calibration_path.parent,
        calibration_path.name,
        "units-migration calibration",
    )
    try:
        document = json.loads(
            payload.decode("utf-8"),
            parse_constant=reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ComposeError(
            f"{calibration_path}: invalid calibration JSON: {exc}"
        ) from exc
    catalog = curate_rewards.units_migration_catalog(document, calibration_path)
    return catalog, {
        "mode": mode,
        "path": str(calibration_path),
        "sha256": sha256_hex(payload),
        "records": len(catalog),
    }


def compact_audit_report(
    report: Mapping[str, Any] | None, record_count: int
) -> dict[str, Any]:
    """Return the exact compact audit declaration stored in ``COMPOSE.json``."""

    if record_count == 0:
        return {
            "run_dir": RECORDS_DIRNAME,
            "records": 0,
            "training_ready": False,
            "blockers": [REASON_EMPTY_CORPUS],
        }
    if report is None:
        raise ComposeError("nonempty compact audit requires an audit report")
    return {
        "run_dir": RECORDS_DIRNAME,
        "records": report["totals"]["records"],
        "training_ready": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
        "identity_coverage_pct": report["identity"]["coverage_pct"],
        "provenance_canonical_pct": report["provenance"]["canonical_pct"],
        "preference_context_purity_pct": report["preferences"]["context_purity_pct"],
    }


def _audit_records(records_dir: Path, record_count: int) -> dict[str, Any]:
    """Audit the curated payload and refuse to call an empty corpus ready."""

    report = training_audit.audit_run(records_dir) if record_count else None
    return compact_audit_report(report, record_count)


def compose_run(
    source_run: str | Path,
    destination: str | Path,
    *,
    units_migration: str | Path | None = None,
) -> dict[str, Any]:
    """Compose every JSONL record under ``source_run`` into ``destination``."""

    source_run = Path(source_run)
    destination = Path(destination)
    resolved_source = _require_exact_directory(source_run, "source run")
    source_members = source_jsonl_members(resolved_source)
    catalog, calibration_descriptor = _load_calibration(
        resolved_source,
        Path(units_migration) if units_migration is not None else None,
    )
    pinned_destination = _create_pinned_destination(resolved_source, destination)
    destination_root = pinned_destination.root
    records_dir = destination_root / RECORDS_DIRNAME
    manifest_dir = destination_root / MANIFEST_DIRNAME

    counts: Counter[str] = Counter()
    exclusions: Counter[str] = Counter()
    lane_actions: dict[str, Counter[str]] = {lane: Counter() for lane in LANE_ORDER}
    manifest_lines: list[str] = []
    sidecar_lines: list[str] = []
    outputs: list[dict[str, Any]] = []
    emitted_ids: dict[str, str] = {}
    seen_source_semantics: dict[str, tuple[str, int]] = {}
    seen_curated_semantics: dict[str, tuple[str, int]] = {}

    try:
        records_dir.mkdir()
        manifest_dir.mkdir()
        for relative in source_members:
            _source_file, raw_file = _read_exact_regular_file(
                resolved_source,
                relative,
                f"compose source {relative}",
            )
            source_file_sha256 = sha256_hex(raw_file)
            counts["source_files"] += 1
            emitted: list[str] = []

            # JSONL is LF-framed. ``splitlines`` also treats Unicode line and
            # paragraph separators as record boundaries after text decoding;
            # splitting the source bytes on LF preserves those legal JSON
            # string characters. Drop only the terminal newline sentinel.
            physical_lines = raw_file.split(b"\n")
            if physical_lines and physical_lines[-1] == b"":
                physical_lines.pop()
            for line_number, physical_line in enumerate(physical_lines, 1):
                if not physical_line.strip():
                    counts["blank_lines"] += 1
                    continue
                counts["source_records"] += 1
                source_sha256 = sha256_hex(physical_line)
                entry = {
                    "compose_name": COMPOSE_NAME,
                    "compose_version": COMPOSE_VERSION,
                    "lane_order": list(LANE_ORDER),
                    "source_path": relative,
                    "source_line": line_number,
                    "source_sha256": source_sha256,
                    "source_file_sha256": source_file_sha256,
                }
                decision = compose_source_line(
                    physical_line,
                    source_path=relative,
                    source_line=line_number,
                    source_file_sha256=source_file_sha256,
                    calibration_catalog=catalog,
                    seen_source_semantics=seen_source_semantics,
                    seen_curated_semantics=seen_curated_semantics,
                )

                entry["action"] = decision.action
                entry["reason_codes"] = list(decision.reason_codes)
                entry["stages"] = [dict(stage) for stage in decision.stages]
                for stage in decision.stages:
                    lane = stage["lane"]
                    if lane in lane_actions:
                        lane_actions[lane][stage["action"]] += 1

                if decision.action == ACTION_RETAINED and decision.record is not None:
                    line = canonical_json(decision.record)
                    output_sha256 = sha256_hex(line.encode("utf-8"))
                    if decision.output_id is not None:
                        previous = emitted_ids.get(decision.output_id)
                        if previous is not None:
                            raise ComposeError(
                                "canonical ID collision "
                                f"{decision.output_id!r}: {previous} and "
                                f"{relative}:{line_number}"
                            )
                        emitted_ids[decision.output_id] = f"{relative}:{line_number}"
                    emitted.append(line)
                    entry["output_path"] = f"{RECORDS_DIRNAME}/{relative}"
                    entry["output_line"] = len(emitted)
                    entry["output_id"] = decision.output_id
                    entry["output_sha256"] = output_sha256
                    counts["retained"] += 1
                    if decision.reward_sidecar is not None:
                        entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
                        sidecar_lines.append(canonical_json(decision.reward_sidecar))
                else:
                    entry["output_path"] = None
                    entry["output_line"] = None
                    entry["output_id"] = None
                    entry["output_sha256"] = None
                    counts["excluded"] += 1
                    for reason in decision.reason_codes or ("compose.unspecified",):
                        exclusions[reason] += 1
                manifest_lines.append(canonical_json(entry))

            if emitted:
                digest = _write_new_text(
                    records_dir / relative, "".join(line + "\n" for line in emitted)
                )
                outputs.append(
                    {
                        "path": f"{RECORDS_DIRNAME}/{relative}",
                        "records": len(emitted),
                        "sha256": digest,
                    }
                )
                counts["output_files"] += 1

        manifest_path = manifest_dir / MANIFEST_FILENAME
        manifest_sha256 = _write_new_text(
            manifest_path, "".join(line + "\n" for line in manifest_lines)
        )
        sidecar_path = manifest_dir / REWARD_SIDECAR_FILENAME
        sidecar_sha256 = _write_new_text(
            sidecar_path, "".join(line + "\n" for line in sidecar_lines)
        )

        summary = {
            "compose_name": COMPOSE_NAME,
            "compose_version": COMPOSE_VERSION,
            "source_run": str(resolved_source),
            "destination": str(pinned_destination.path),
            "lane_order": list(LANE_ORDER),
            "transforms": transform_contract(),
            "calibration": calibration_descriptor,
            "calibrated_records": len(catalog),
            "counts": {
                "source_files": counts["source_files"],
                "source_records": counts["source_records"],
                "blank_lines": counts["blank_lines"],
                "retained": counts["retained"],
                "excluded": counts["excluded"],
                "output_files": counts["output_files"],
                "reward_sidecars": len(sidecar_lines),
            },
            "lane_actions": {
                lane: dict(sorted(actions.items())) for lane, actions in lane_actions.items()
            },
            "exclusions": dict(sorted(exclusions.items())),
            "outputs": outputs,
            "manifest": {
                "path": f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
                "entries": len(manifest_lines),
                "sha256": manifest_sha256,
            },
            "reward_sidecars": {
                "path": f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
                "entries": len(sidecar_lines),
                "sha256": sidecar_sha256,
            },
            "audit": _audit_records(records_dir, counts["retained"]),
        }
        _write_new_text(
            destination_root / SUMMARY_FILENAME,
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    except BaseException:
        pinned_destination.cleanup()
        raise
    pinned_destination.finish()
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source_run", help="source run directory (read-only)")
    parser.add_argument("destination", help="new curated destination (must not exist)")
    parser.add_argument(
        "--units-migration",
        help="explicit reward calibration sidecar; defaults to the FFPC sidecar",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when the composed tree is not training_ready",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = compose_run(
            args.source_run, args.destination, units_migration=args.units_migration
        )
    except (ComposeError, curate_identity.IdentityCurationError,
            curate_rewards.RewardOntologyError, OSError) as exc:
        print(f"compose_curated: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if args.strict and not summary["audit"]["training_ready"]:
        for blocker in summary["audit"]["blockers"]:
            print(f"blocker: {blocker}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
