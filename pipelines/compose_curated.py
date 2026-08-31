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
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableMapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_mill  # noqa: E402
import curate_agentic  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_identity  # noqa: E402
import curate_preferences  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402
from check_records import reject_json_constant  # noqa: E402
from record_kind import preference_side_kinds  # noqa: E402
from round_txn import TransactionError  # noqa: E402

try:  # PR #93 is a sibling stack; consume its reviewed contract when present.
    import curate_trajectory_preferences  # type: ignore[import-not-found]  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover - branch topology decides this
    if exc.name != "curate_trajectory_preferences":
        raise
    curate_trajectory_preferences = None

# ``compose_curated`` split by responsibility (CodeScene: Lines of Code in a
# Single File): the shared contract, the trajectory-preference gate core, and
# the filesystem safety layer live in sibling modules. Every name is
# re-imported here so existing ``compose_curated.X`` call sites, the export
# authenticator, and tests resolve unchanged.
from compose_contract import (  # noqa: E402,F401
    ACTION_EXCLUDED,
    ACTION_NOT_APPLICABLE,
    ACTION_RETAINED,
    COMPOSE_NAME,
    COMPOSE_VERSION,
    ComposeDecision,
    ComposeError,
    FFPC_UNITS_MIGRATION,
    LANE_ORDER,
    MANIFEST_DIRNAME,
    MANIFEST_FILENAME,
    PREFERENCE_CANDIDATE_KEYS,
    REASON_DUPLICATE_CURATED_RECORD,
    REASON_DUPLICATE_SOURCE_RECORD,
    REASON_EMPTY_CORPUS,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_MIXED_PREFERENCE_FAMILIES,
    REASON_REWARD_ONTOLOGY,
    REASON_TRAJECTORY_GATE_PASSED,
    REASON_TRAJECTORY_GOAL_NORMALIZED,
    REASON_TRAJECTORY_IDENTICAL,
    REASON_TRAJECTORY_OUTCOME_MISSING,
    REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT,
    REASON_TRAJECTORY_PREFIX_ABSENT,
    REASON_TRAJECTORY_REWARD_MISSING,
    REASON_TRAJECTORY_REWARD_NOT_DIVERGENT,
    REASON_TRAJECTORY_SIDE_INVALID,
    REASON_TRAJECTORY_STEPS_EMPTY,
    REASON_TRAJECTORY_STEPS_INVALID,
    RECORDS_DIRNAME,
    REWARD_SIDECAR_FILENAME,
    SUMMARY_FILENAME,
    TRAJECTORY_GOAL_LOCATIONS,
    _TrajectoryPreferenceDecision,
    _canonical_sha256,
    canonical_json,
    sha256_hex,
)
from compose_destination import (  # noqa: E402,F401
    _PinnedDestination,
    _assert_destination_disjoint,
    _assert_new_destination,
    _assert_opened_source_identity,
    _assert_source_path_unchanged,
    _assert_unaliased_regular_member,
    _collect_source_directory,
    _contains_raw_segments,
    _create_pinned_destination,
    _destination_write_parts,
    _directory_binding_matches,
    _directory_identity,
    _discard_created_destination,
    _drain_descriptor,
    _is_under_raw,
    _open_pinned_child,
    _open_pinned_child_directory,
    _pinned_root_path,
    _read_exact_child_file,
    _read_exact_regular_file,
    _read_pinned_child_bytes,
    _refuse_existing_destination,
    _require_exact_directory,
    _scan_source_directory,
    _source_entry_metadata,
    _source_member_path,
    _stable_file_identity,
    _validated_member_relative,
    _verify_directory_binding,
    _verify_pinned_child,
    _write_new_text,
    _write_pinned_new_bytes,
    source_jsonl_members,
)
from compose_trajectory import (  # noqa: E402,F401
    _TRAJECTORY_DIVERGENCE_FIELDS,
    _compat_trajectory_preference,
    _curate_trajectory_sides,
    _is_same_state_pair,
    _mixed_preference_families,
    _normalize_trajectory_goal_whitespace,
    _present_trajectory_goals,
    _trajectory_divergence_reasons,
    _trajectory_gate_passed,
    _trajectory_goal_owner,
    _trajectory_side_needs_coding,
    _trajectory_side_validation_errors,
    _trajectory_step_reasons,
    _whitespace_only_goal,
    is_bridge_record,
    is_episode_record,
    is_preference_record,
)


# Everything callers may import from this module, including the names
# re-exported from the compose_* siblings after the split.
__all__ = [
    "ACTION_EXCLUDED",
    "ACTION_NOT_APPLICABLE",
    "ACTION_RETAINED",
    "COMPOSE_NAME",
    "COMPOSE_VERSION",
    "ComposeDecision",
    "ComposeError",
    "FFPC_UNITS_MIGRATION",
    "LANE_ORDER",
    "MANIFEST_DIRNAME",
    "MANIFEST_FILENAME",
    "PREFERENCE_CANDIDATE_KEYS",
    "REASON_DUPLICATE_CURATED_RECORD",
    "REASON_DUPLICATE_SOURCE_RECORD",
    "REASON_EMPTY_CORPUS",
    "REASON_INVALID_JSON",
    "REASON_INVALID_UTF8",
    "REASON_MIXED_PREFERENCE_FAMILIES",
    "REASON_REWARD_ONTOLOGY",
    "REASON_TRAJECTORY_GATE_PASSED",
    "REASON_TRAJECTORY_GOAL_NORMALIZED",
    "REASON_TRAJECTORY_IDENTICAL",
    "REASON_TRAJECTORY_OUTCOME_MISSING",
    "REASON_TRAJECTORY_OUTCOME_NOT_DIVERGENT",
    "REASON_TRAJECTORY_PREFIX_ABSENT",
    "REASON_TRAJECTORY_REWARD_MISSING",
    "REASON_TRAJECTORY_REWARD_NOT_DIVERGENT",
    "REASON_TRAJECTORY_SIDE_INVALID",
    "REASON_TRAJECTORY_STEPS_EMPTY",
    "REASON_TRAJECTORY_STEPS_INVALID",
    "RECORDS_DIRNAME",
    "REWARD_SIDECAR_FILENAME",
    "SUMMARY_FILENAME",
    "TRAJECTORY_GOAL_LOCATIONS",
    "_PinnedDestination",
    "_TRAJECTORY_DIVERGENCE_FIELDS",
    "_TrajectoryPreferenceDecision",
    "_assert_destination_disjoint",
    "_assert_new_destination",
    "_assert_opened_source_identity",
    "_assert_source_path_unchanged",
    "_assert_unaliased_regular_member",
    "_canonical_sha256",
    "_collect_source_directory",
    "_compat_trajectory_preference",
    "_contains_raw_segments",
    "_create_pinned_destination",
    "_curate_trajectory_sides",
    "_destination_write_parts",
    "_directory_binding_matches",
    "_directory_identity",
    "_discard_created_destination",
    "_drain_descriptor",
    "_is_same_state_pair",
    "_is_under_raw",
    "_mixed_preference_families",
    "_normalize_trajectory_goal_whitespace",
    "_open_pinned_child",
    "_open_pinned_child_directory",
    "_pinned_root_path",
    "_present_trajectory_goals",
    "_read_exact_child_file",
    "_read_exact_regular_file",
    "_read_pinned_child_bytes",
    "_refuse_existing_destination",
    "_require_exact_directory",
    "_scan_source_directory",
    "_source_entry_metadata",
    "_source_member_path",
    "_stable_file_identity",
    "_trajectory_divergence_reasons",
    "_trajectory_gate_passed",
    "_trajectory_goal_owner",
    "_trajectory_side_needs_coding",
    "_trajectory_side_validation_errors",
    "_trajectory_step_reasons",
    "_validated_member_relative",
    "_verify_directory_binding",
    "_verify_pinned_child",
    "_whitespace_only_goal",
    "_write_new_text",
    "_write_pinned_new_bytes",
    "calibration_for",
    "canonical_json",
    "compose_record",
    "compose_run",
    "compose_source_line",
    "curate_trajectory_preferences",
    "is_bridge_record",
    "is_episode_record",
    "is_preference_record",
    "main",
    "parse_args",
    "sha256_hex",
    "source_jsonl_members",
    "transform_contract",
]


def _trajectory_preference(
    record: dict[str, Any],
) -> tuple[Any, str, str, str]:
    """Return a trajectory decision plus transform identity and implementation.

    Reads the optional reviewed module through this module's own global so a
    test (or a stacked branch) that patches
    ``compose_curated.curate_trajectory_preferences`` steers the dispatch.
    """

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


def _calibration_id_candidates(record: Mapping[str, Any]):
    """Yield the record's declared source identifiers in identity's order.

    The identity lane accepts every ``curate_identity.LEGACY_ID_KEYS`` form on
    the record root and its ``meta``/``state`` containers, so calibration has
    to consider the same vocabulary: an FFPC pair that carries its catalogued
    id only as ``pair_id`` must not be silently downgraded to
    ``sign_order_only`` while its ``id``-carrying twin calibrates.
    """

    containers = (record, record.get("meta"), record.get("state"))
    for container in containers:
        if not isinstance(container, Mapping):
            continue
        for key in curate_identity.LEGACY_ID_KEYS:
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                yield value.strip()


def calibration_for(record: Mapping[str, Any], catalog: Mapping[str, Any] | None) -> Any:
    """Look a reward calibration up by the record's *source* identifiers.

    Compose runs the identity lane first, which replaces ``id`` with a
    canonical digest, so the lookup has to use the pre-identity record. The
    first declared identifier with catalog evidence wins, deterministically.
    """

    if not catalog or not isinstance(record, Mapping):
        return None
    for candidate in _calibration_id_candidates(record):
        calibration = catalog.get(candidate.lower())
        if calibration is not None:
            return calibration
    return None


REASON_IDENTITY_INVALID_PAYLOAD_SHAPE = "identity.invalid_payload_shape"

# ``validate_run.check_spike_order`` phrases the ordering violation this way.
# ``test_bridge_order_error_fragment_matches_the_validator`` pins the coupling
# so a reworded validator message fails loudly instead of silently turning the
# deferral below back into a terminal exclusion.
BRIDGE_ORDER_ERROR_FRAGMENT = "spike_events not globally non-decreasing"


def _is_bridge_order_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused a record for spike ordering and nothing else."""

    if list(mapping.get("reason_codes", [])) != [
        REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
    ]:
        return False
    details = mapping.get("details")
    if not isinstance(details, list) or not details:
        return False
    return all(
        isinstance(detail, str) and BRIDGE_ORDER_ERROR_FRAGMENT in detail
        for detail in details
    )


def _bridge_order_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    """Return the bridge lane's stable-sorted copy, or None if it will not repair.

    ``curate_bridge`` owns the ordering invariant and repairs a single-clock
    stream deterministically.  Asking the lane itself keeps every guard it
    applies -- explicit order fields, raster budgets, multiple clocks -- so a
    record it would quarantine is never smuggled past identity.
    """

    try:
        decision = curate_bridge.curate_record(
            record,
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
            source_file_hash=None,
        )
    except Exception:  # noqa: BLE001 - a probe must never fail composition
        return None
    if decision.action != "repair" or not isinstance(decision.output_record, dict):
        return None
    return decision.output_record


# Identity's step-shape diagnostics for a top-level episode. Wrap records
# validate through the Thalamic structural path and never produce this form.
CODING_STEP_ERROR_RE = re.compile(r"^record step \d+: ")


def _is_coding_step_only_rejection(mapping: Mapping[str, Any]) -> bool:
    """Whether identity refused an episode for step shape and nothing else."""

    if list(mapping.get("reason_codes", [])) != [
        REASON_IDENTITY_INVALID_PAYLOAD_SHAPE
    ]:
        return False
    details = mapping.get("details")
    if not isinstance(details, list) or not details:
        return False
    return all(
        isinstance(detail, str) and CODING_STEP_ERROR_RE.match(detail)
        for detail in details
    )


def _coding_steps_repaired_copy(
    record: Mapping[str, Any],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> dict[str, Any] | None:
    """Return the coding lane's own repaired copy, or None if it will not repair.

    ``curate_coding`` owns step-level repair: it excludes an unusable step and
    retains the episode with ``coding_steps_excluded``. Asking the lane itself
    keeps every guard it applies, so an episode it would exclude outright is
    never smuggled past identity.
    """

    try:
        curated, _manifest = curate_coding.curate_episode(
            copy.deepcopy(dict(record)),
            source_path=source_path,
            source_line=source_line,
            source_hash=source_sha256,
        )
    except Exception:  # noqa: BLE001 - a probe must never fail composition
        return None
    return curated if isinstance(curated, dict) else None


def _source_preference_shape(record: Any) -> tuple[Any, bool]:
    """Return (side kinds, mixed-family flag) for a source preference record."""

    if not (is_preference_record(record) and isinstance(record, Mapping)):
        return None, False
    side_kinds = preference_side_kinds(record)
    mixed = not _is_same_state_pair(record) and _mixed_preference_families(
        side_kinds
    )
    return side_kinds, mixed


def _identity_retry(
    repaired: dict[str, Any] | None,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
):
    """Re-validate identity against a lane's repaired copy.

    Returns the retained identity result, or None when the repair did not
    satisfy identity either.
    """

    if repaired is None:
        return None
    retry = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=repaired,
            source_path=source_path,
            source_line=source_line,
            source_sha256=source_sha256,
        )
    )
    if retry.action == "retained" and isinstance(retry.record, dict):
        return retry
    return None


def _deferred_lane_repair(
    record: Any,
    identity_result: Any,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> tuple[Any, str | None]:
    """Hand an identity refusal to the downstream lane that can repair it.

    A bridge stream with one valid global clock but unsorted events is
    explicitly repairable: ``curate_bridge`` stable-sorts it and records
    BRIDGE_EVENTS_STABLE_SORTED_SINGLE_GLOBAL_CLOCK. The coding lane owns
    step-level repair the same way: an episode with one usable step plus an
    unusable one keeps its usable steps under ``coding_steps_excluded``.
    Identity applies the same invariants first, so leaving its refusal
    terminal would drop a record the pipeline knows how to fix. Re-validate
    identity against the owning lane's repaired copy; the caller then hands
    the original payload forward so that lane performs and records the repair
    itself. Returns ``(identity_result, deferred lane name or None)``.
    """

    if identity_result.action == "retained" or not isinstance(record, Mapping):
        return identity_result, None
    coordinates = {
        "source_path": source_path,
        "source_line": source_line,
        "source_sha256": source_sha256,
    }

    def lane_retry(applies: bool, repaired_copy):
        if not applies:
            return None
        return _identity_retry(
            repaired_copy(record, **coordinates), **coordinates
        )

    retry = lane_retry(
        is_bridge_record(record)
        and _is_bridge_order_only_rejection(identity_result.mapping),
        _bridge_order_repaired_copy,
    )
    if retry is not None:
        return retry, "bridge"
    retry = lane_retry(
        isinstance(record.get("steps"), list)
        and _is_coding_step_only_rejection(identity_result.mapping),
        _coding_steps_repaired_copy,
    )
    if retry is not None:
        return retry, "coding"
    return identity_result, None


def _identity_stage_evidence(
    identity_result: Any,
    deferred_lane: str | None,
    source_side_kinds: Any,
    mixed_preference_families: bool,
) -> tuple[list[str], dict[str, Any]]:
    """Assemble the identity stage's reason codes and detail mapping."""

    identity_reasons = list(identity_result.mapping.get("reason_codes", []))
    identity_detail = copy.deepcopy(identity_result.mapping)
    if deferred_lane == "bridge":
        identity_detail["bridge_order_deferred_to_bridge_lane"] = True
    if deferred_lane == "coding":
        identity_detail["coding_steps_deferred_to_coding_lane"] = True
    if source_side_kinds is not None:
        identity_detail["preference_side_kinds"] = list(source_side_kinds)
    if mixed_preference_families:
        # Identity correctly refuses this shape first. Replace its generic
        # unsupported-shape summary with the composition contract's explicit
        # family mismatch while retaining the identity diagnostics as detail.
        identity_detail["identity_reason_codes"] = identity_reasons
        identity_reasons = [REASON_MIXED_PREFERENCE_FAMILIES]
    return identity_reasons, identity_detail


def _compose_identity_stage(
    record: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | tuple[dict[str, Any], Any]":
    """Run the identity lane and append its stage.

    Returns ``(current, registered_kind)`` to continue, or an early
    :class:`ComposeDecision` when identity refuses the record.
    """

    source_side_kinds, mixed_preference_families = _source_preference_shape(record)

    identity_result = curate_identity.curate_record(
        curate_identity.SourceRecord(
            record=record,
            source_path=source_path,
            source_line=source_line,
            source_sha256=source_sha256,
        )
    )
    identity_result, deferred_lane = _deferred_lane_repair(
        record,
        identity_result,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
    )
    deferred_bridge_order = deferred_lane == "bridge"
    deferred_coding_steps = deferred_lane == "coding"

    identity_reasons, identity_detail = _identity_stage_evidence(
        identity_result,
        deferred_lane,
        source_side_kinds,
        mixed_preference_families,
    )
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
    if deferred_bridge_order:
        # Identity validated the repaired order; the bridge lane still has to
        # see the source order so its manifest carries the repair.
        current["spike_events"] = copy.deepcopy(record["spike_events"])
    if deferred_coding_steps:
        # Identity validated the repaired steps; the coding lane still has to
        # see the source steps so its manifest carries the repair.
        current["steps"] = copy.deepcopy(record["steps"])
    registered_kind = identity_result.mapping.get("record_kind")
    return current, registered_kind


def _compose_bridge_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None,
) -> "ComposeDecision | dict[str, Any]":
    """Run the bridge lane and append its stage.

    Returns the next ``current`` to continue, or an early
    :class:`ComposeDecision` when bridge curation excludes the record.
    """

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
        return bridge_decision.output_record
    stages.append(
        _stage(
            "bridge",
            curate_bridge.TRANSFORM_NAME,
            curate_bridge.TRANSFORM_VERSION,
            ACTION_NOT_APPLICABLE,
            lane_action=ACTION_NOT_APPLICABLE,
        )
    )
    return current


def _side_curation_failed_decision(
    stages: list[dict[str, Any]],
    side_curation: dict[str, dict[str, Any]],
    side_curation_reasons: list[str],
    side_curation_changed: bool,
    *,
    side_kinds: tuple[str, str],
    classification: str,
    **stage_extra: Any,
) -> ComposeDecision:
    """Exclusion shared by both trajectory branches when a side will not repair."""

    preference_reasons = list(
        dict.fromkeys([REASON_TRAJECTORY_SIDE_INVALID, *side_curation_reasons])
    )
    stages.append(
        _stage(
            "preferences",
            COMPOSE_NAME,
            COMPOSE_VERSION,
            ACTION_EXCLUDED,
            reason_codes=preference_reasons,
            lane_action=ACTION_EXCLUDED,
            classification=classification,
            side_kinds=list(side_kinds),
            **stage_extra,
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


def _compose_same_state_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    """Preferences branch for a same-state (Thalamic) trajectory pair."""

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
        return _side_curation_failed_decision(
            stages,
            side_curation,
            side_curation_reasons,
            side_curation_changed,
            side_kinds=side_kinds,
            classification="same_state_side_curation_failed",
            schema="same_state_pair",
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
    return preference_decision, preference_reasons


def _compose_mixed_family_preference_exclusion(
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
) -> ComposeDecision:
    """Preferences branch that refuses mixed-family (episode + Thalamic) sides."""

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


def _compose_episode_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | tuple[Any, list[str]]":
    """Preferences branch for an episode/episode (coding-style) trajectory pair."""

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
        return _side_curation_failed_decision(
            stages,
            side_curation,
            side_curation_reasons,
            side_curation_changed,
            side_kinds=side_kinds,
            classification="trajectory_side_curation_failed",
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
    return preference_decision, preference_reasons


def _compose_legacy_preference(
    current: dict[str, Any],
    side_kinds: tuple[str, str],
    stages: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    """Preferences branch for a legacy (pre-episode) Thalamic-shaped pair."""

    preference_decision = curate_preferences.curate_preference_record(current)
    preference_reasons = list(preference_decision.reason_codes)
    stages.append(
        _stage(
            "preferences",
            curate_preferences.TRANSFORM_NAME,
            curate_preferences.TRANSFORM_VERSION,
            (
                ACTION_RETAINED
                if preference_decision.record is not None
                else ACTION_EXCLUDED
            ),
            reason_codes=preference_reasons,
            lane_action=preference_decision.action,
            classification=preference_decision.classification,
            side_kinds=list(side_kinds),
            context_diff_paths=list(preference_decision.context_diff_paths),
        )
    )
    return preference_decision, preference_reasons


def _compose_preferences_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
) -> "ComposeDecision | dict[str, Any]":
    """Run the preferences lane and append its stage.

    Dispatches to the branch matching the pair's side kinds -- same-state
    (Thalamic), mixed families (always refused), episode/episode, or legacy
    -- then applies the one retained-or-excluded check every branch shares.
    Returns the next ``current`` to continue, or an early
    :class:`ComposeDecision` when preference curation excludes the record.
    """

    if not is_preference_record(current):
        stages.append(
            _stage(
                "preferences",
                curate_preferences.TRANSFORM_NAME,
                curate_preferences.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current

    side_kinds = preference_side_kinds(current)
    if _is_same_state_pair(current):
        branch_outcome = _compose_same_state_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    elif _mixed_preference_families(side_kinds):
        return _compose_mixed_family_preference_exclusion(side_kinds, stages)
    elif side_kinds == ("episode", "episode"):
        branch_outcome = _compose_episode_preference(
            current,
            side_kinds,
            stages,
            source_path=source_path,
            source_line=source_line,
        )
    else:
        branch_outcome = _compose_legacy_preference(current, side_kinds, stages)

    if isinstance(branch_outcome, ComposeDecision):
        return branch_outcome
    preference_decision, preference_reasons = branch_outcome
    if preference_decision.record is None:
        return ComposeDecision(
            ACTION_EXCLUDED,
            None,
            tuple(preference_reasons),
            tuple(stages),
            None,
            None,
        )
    return preference_decision.record


def _coding_lane_curator(current: dict[str, Any], registered_kind: Any) -> Any:
    """The coding-lane module for this record, or ``None`` if it has no lane.

    Multi-agent and safety-case records are curated by ``curate_agentic``;
    episode records by ``curate_coding``. Both expose the same
    ``(curated, manifest)`` contract, so the caller treats them alike.
    """

    if registered_kind in {"multi_agent", "safety_case"}:
        return curate_agentic
    if is_episode_record(current):
        return curate_coding
    return None


def _append_coding_lane_stage(
    stages: list[dict[str, Any]],
    module: Any,
    curated: Any,
    manifest: Mapping[str, Any],
) -> "ComposeDecision | Any":
    """Append one coding-lane stage; exclude the record if the lane refused it."""

    reasons = list(manifest.get("reason_codes", []))
    stages.append(
        _stage(
            "coding",
            module.TRANSFORM_NAME,
            module.TRANSFORM_VERSION,
            ACTION_RETAINED if curated is not None else ACTION_EXCLUDED,
            reason_codes=reasons,
            lane_action=manifest.get("action"),
            detail=manifest,
        )
    )
    if curated is None:
        return ComposeDecision(
            ACTION_EXCLUDED,
            None,
            tuple(reasons),
            tuple(stages),
            None,
            None,
        )
    return curated


def _compose_coding_stage(
    current: dict[str, Any],
    registered_kind: Any,
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
) -> "ComposeDecision | dict[str, Any]":
    """Run the coding lane and append its stage.

    Returns the next ``current`` to continue, or an early
    :class:`ComposeDecision` when coding curation excludes the record.
    """

    module = _coding_lane_curator(current, registered_kind)
    if module is None:
        stages.append(
            _stage(
                "coding",
                curate_coding.TRANSFORM_NAME,
                curate_coding.TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
            )
        )
        return current

    curate = (
        curate_agentic.curate_record
        if module is curate_agentic
        else curate_coding.curate_episode
    )
    curated, manifest = curate(
        current,
        source_path=source_path,
        source_line=source_line,
        source_hash=source_sha256,
    )
    return _append_coding_lane_stage(stages, module, curated, manifest)


def _compose_rewards_stage(
    current: dict[str, Any],
    stages: list[dict[str, Any]],
    *,
    source_path: str,
    source_line: int,
    calibration: Any,
) -> "ComposeDecision | tuple[dict[str, Any], dict[str, Any] | None]":
    """Run the rewards lane and append its stage.

    Returns ``(current, sidecar)`` to continue, or an early
    :class:`ComposeDecision` when the reward ontology refuses the record.
    """

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
                curate_rewards.REWARD_TRANSFORM_VERSION,
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
                curate_rewards.REWARD_TRANSFORM_VERSION,
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
                curate_rewards.REWARD_TRANSFORM_VERSION,
                ACTION_NOT_APPLICABLE,
                lane_action=ACTION_NOT_APPLICABLE,
                source_reward_count=0,
            )
        )

    return current, sidecar


def compose_record(
    record: Any,
    *,
    source_path: str,
    source_line: int,
    source_sha256: str,
    source_file_sha256: str | None = None,
    calibration: Any = None,
) -> ComposeDecision:
    """Run every applicable lane over one record without mutating the input.

    Each lane is a private ``_compose_<lane>_stage`` helper that appends its
    own stage(s) to the shared ``stages`` list and either returns the next
    ``current`` record to hand to the following lane, or an early
    :class:`ComposeDecision` that this function returns immediately without
    running any later lane -- the same short-circuiting order the lanes ran
    in before this function was split: identity, then bridge, then
    preferences, then coding, then rewards.
    """

    stages: list[dict[str, Any]] = []

    identity_outcome = _compose_identity_stage(
        record,
        stages,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
    )
    if isinstance(identity_outcome, ComposeDecision):
        return identity_outcome
    current, registered_kind = identity_outcome

    bridge_outcome = _compose_bridge_stage(
        current,
        stages,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
        source_file_sha256=source_file_sha256,
    )
    if isinstance(bridge_outcome, ComposeDecision):
        return bridge_outcome
    current = bridge_outcome

    preferences_outcome = _compose_preferences_stage(
        current,
        stages,
        source_path=source_path,
        source_line=source_line,
    )
    if isinstance(preferences_outcome, ComposeDecision):
        return preferences_outcome
    current = preferences_outcome

    coding_outcome = _compose_coding_stage(
        current,
        registered_kind,
        stages,
        source_path=source_path,
        source_line=source_line,
        source_sha256=source_sha256,
    )
    if isinstance(coding_outcome, ComposeDecision):
        return coding_outcome
    current = coding_outcome

    rewards_outcome = _compose_rewards_stage(
        current,
        stages,
        source_path=source_path,
        source_line=source_line,
        calibration=calibration,
    )
    if isinstance(rewards_outcome, ComposeDecision):
        return rewards_outcome
    current, sidecar = rewards_outcome

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


def _json_pointer_tokens(pointer: Any) -> list[str] | None:
    """Decode a JSON pointer into unescaped tokens, or ``None`` if unusable."""

    if not isinstance(pointer, str) or not pointer.startswith("/") or pointer == "/":
        return None
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    """Drop one JSON-pointer field from a copied record, if it still exists."""

    tokens = _json_pointer_tokens(pointer)
    if tokens is None:
        return
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def _original_id_paths(originals: Any) -> list[str]:
    """Every ``path`` carried by one list of original-id entries."""

    if not isinstance(originals, list):
        return []
    return [
        item["path"]
        for item in originals
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Collect every identity-mapped legacy identifier path for one record."""

    if not isinstance(detail, Mapping):
        return ()
    paths = _original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                paths.extend(_original_id_paths(mapping.get("original_ids")))
    # First-seen order, deduplicated.
    return tuple(dict.fromkeys(paths))


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Every owner that may carry a factory declaration for one record.

    Mirrors ``curate_identity._payload_factory``: the wrapper itself plus both
    preference sides, since a legacy preference wrapper attests its factory on
    ``chosen``/``rejected`` and omits a wrapper-level ``meta`` entirely.
    """

    owners = [record]
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, dict):
            owners.append(owner)
    return owners


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    """Return the identity stage's detail mapping, when one was recorded."""

    identity_stage = next(
        (stage for stage in decision.stages if stage.get("lane") == "identity"),
        None,
    )
    detail = identity_stage.get("detail") if isinstance(identity_stage, dict) else None
    return detail if isinstance(detail, dict) else None


def _strip_assigned_ids(semantic: dict[str, Any], detail: dict[str, Any] | None) -> None:
    """Drop the coordinate-derived ids the identity lane assigned."""

    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = _identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in _mapped_legacy_id_paths(detail):
        _pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    """Drop pipeline-provenance labels from every identity owner.

    The same episode can be authorized under more than one factory path_id
    (the registry declares dozens of distinct "episode"-kind factories).
    ``meta.factory``/``meta.generator`` name which pipeline and model produced
    the row, and ``meta.run``/``meta.round`` name when it was produced -- none
    of that is trained-on content, so two rows that are otherwise
    byte-identical after curation must not be kept apart by those labels
    alone -- doing so would let the same content land in both the train and
    eval split. Normalize the fields on every identity owner: a Fable
    preference wrapper predates a wrapper-level ``meta`` and carries the
    declaration on ``chosen``/``rejected`` instead, exactly as
    ``curate_identity._payload_factory`` resolves it. They stay untouched on
    the emitted record itself, since ``semantic`` is a deep copy.
    """

    for owner in _semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for provenance_field in ("factory", "generator", "run", "round"):
            meta.pop(provenance_field, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    """Drop the reward annotation's source-coordinate binding.

    The sidecar digest authenticates source coordinates. Keep the
    comparability class and any magnitude/order payload, but remove the
    coordinate binding that would otherwise hide converged examples.
    """

    annotation = semantic.get(curate_rewards.ANNOTATION_FIELD)
    if isinstance(annotation, dict):
        annotation.pop("source_sidecar_id", None)


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    """Hash training content without coordinate-derived identity bindings."""

    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    _strip_assigned_ids(semantic, _identity_stage_detail_of(decision))
    _strip_provenance_labels(semantic)
    _strip_sidecar_binding(semantic)
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


def _excluded_source_line(reason: str, detail: dict[str, Any]) -> ComposeDecision:
    """One source-lane exclusion carrying its own evidence stage.

    The three source-lane rejections -- undecodable bytes, unparseable or
    unhashable JSON, and a duplicate source record -- differ only in the
    reason code and the detail they attach.
    """

    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (reason,),
        (
            _stage(
                "source",
                COMPOSE_NAME,
                COMPOSE_VERSION,
                ACTION_EXCLUDED,
                reason_codes=[reason],
                detail=detail,
            ),
        ),
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
        return _excluded_source_line(REASON_INVALID_UTF8, {"error": str(exc)})
    try:
        # Decoding and canonical hashing both recurse over the document, and a
        # deeply nested line can exhaust the stack in either -- ``json.loads``
        # may even succeed on a depth the hash cannot walk. ``RecursionError``
        # is not a ``ValueError``, so leaving it unguarded let one malformed
        # line abort the whole composition with a traceback and roll the
        # destination back. Excluded per line instead, as the other curation
        # readers already do (``curate_coding``, ``tag_jsonl``). Duplicate
        # object keys are rejected with the identity lane's own hook: plain
        # ``json.loads`` keeps the last value silently, which creates
        # parser-dependent source semantics and hides which value the raw
        # record actually asserted.
        record = json.loads(
            text,
            object_pairs_hook=curate_identity._reject_duplicate_object_keys,
            parse_constant=reject_json_constant,
        )
        semantic_sha256 = _canonical_sha256(record)
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        return _excluded_source_line(REASON_INVALID_JSON, {"error": str(exc)})
    if seen_source_semantics is not None:
        first_coordinate = seen_source_semantics.get(semantic_sha256)
        if first_coordinate is not None:
            return _excluded_source_line(
                REASON_DUPLICATE_SOURCE_RECORD,
                {
                    "semantic_sha256": semantic_sha256,
                    "first_source_path": first_coordinate[0],
                    "first_source_line": first_coordinate[1],
                },
            )
    try:
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
    except RecursionError as exc:
        # A depth that survives decoding and the canonical hash can still
        # exhaust the stack inside a lane (``copy.deepcopy`` uses several
        # frames per level). The record is unwalkable evidence, not a reason
        # to roll back the whole destination.
        return _excluded_source_line(
            REASON_INVALID_JSON,
            {"error": f"recursion depth exhausted during curation: {exc}"},
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
            "version": curate_rewards.REWARD_TRANSFORM_VERSION,
        },
    }


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
    if calibration_path is None and os.path.lexists(default):
        # A directory, broken symlink, or fifo at the canonical path is not
        # "no calibration": recording mode "none" here would compose a tree
        # the export step must then refuse (it checks lexists), so fail now.
        raise ComposeError(
            f"default calibration evidence is not an exact regular file: {default}"
        )
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


@dataclass
class _ComposeRunState:
    """Mutable accumulators shared by every source line of one compose run."""

    counts: Counter[str] = field(default_factory=Counter)
    exclusions: Counter[str] = field(default_factory=Counter)
    lane_actions: dict[str, Counter[str]] = field(
        default_factory=lambda: {lane: Counter() for lane in LANE_ORDER}
    )
    manifest_lines: list[str] = field(default_factory=list)
    sidecar_lines: list[str] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    emitted_ids: dict[str, str] = field(default_factory=dict)
    seen_source_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)
    seen_curated_semantics: dict[str, tuple[str, int]] = field(default_factory=dict)


def _jsonl_physical_lines(raw_file: bytes) -> list[bytes]:
    """Split LF-framed JSONL into physical lines without decoding first.

    ``splitlines`` also treats Unicode line and paragraph separators as
    record boundaries after text decoding; splitting the source bytes on LF
    preserves those legal JSON string characters. Only the terminal newline
    sentinel is dropped.
    """

    physical_lines = raw_file.split(b"\n")
    if physical_lines and physical_lines[-1] == b"":
        physical_lines.pop()
    return physical_lines


def _new_manifest_entry(
    relative: Any, line_number: int, source_sha256: str, source_file_sha256: str
) -> dict[str, Any]:
    """The provenance header every manifest entry opens with."""

    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "lane_order": list(LANE_ORDER),
        "source_path": relative,
        "source_line": line_number,
        "source_sha256": source_sha256,
        "source_file_sha256": source_file_sha256,
    }


def _claim_output_id(state: _ComposeRunState, output_id: Any, location: str) -> None:
    """Reserve a canonical ID for one output line, or fail the whole run."""

    if output_id is None:
        return
    previous = state.emitted_ids.get(output_id)
    if previous is not None:
        raise ComposeError(
            f"canonical ID collision {output_id!r}: {previous} and {location}"
        )
    state.emitted_ids[output_id] = location


def _record_retained_line(
    state: _ComposeRunState,
    decision: ComposeDecision,
    entry: dict[str, Any],
    *,
    relative: Any,
    location: str,
    emitted: list[str],
) -> None:
    """Emit one retained record and stamp its manifest entry."""

    line = canonical_json(decision.record)
    output_sha256 = sha256_hex(line.encode("utf-8"))
    _claim_output_id(state, decision.output_id, location)
    emitted.append(line)
    entry["output_path"] = f"{RECORDS_DIRNAME}/{relative}"
    entry["output_line"] = len(emitted)
    entry["output_id"] = decision.output_id
    entry["output_sha256"] = output_sha256
    state.counts["retained"] += 1
    if decision.reward_sidecar is not None:
        entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
        state.sidecar_lines.append(canonical_json(decision.reward_sidecar))


def _record_excluded_line(
    state: _ComposeRunState, decision: ComposeDecision, entry: dict[str, Any]
) -> None:
    """Account one excluded record against its reason codes."""

    entry["output_path"] = None
    entry["output_line"] = None
    entry["output_id"] = None
    entry["output_sha256"] = None
    state.counts["excluded"] += 1
    for reason in decision.reason_codes or ("compose.unspecified",):
        state.exclusions[reason] += 1


def _mill_quarantined_decision(finding: Any) -> ComposeDecision:
    """Exclude a corpus-level mill finding before any lane can run.

    The identity lane would otherwise replace the foreign id prefix with a
    canonical digest, erasing the very evidence the shared detector keys on;
    the later audit of the curated tree could then no longer see it.
    """

    reasons = list(finding.reason_codes)
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        tuple(reasons),
        (
            _stage(
                "source",
                COMPOSE_NAME,
                COMPOSE_VERSION,
                ACTION_EXCLUDED,
                reason_codes=reasons,
                classification="foreign_mill_quarantined",
                detail=finding.as_dict(),
            ),
        ),
        None,
        None,
    )


def _compose_one_line(
    state: _ComposeRunState,
    physical_line: bytes,
    *,
    relative: Any,
    line_number: int,
    source_file_sha256: str,
    catalog: Mapping[str, Any] | None,
    emitted: list[str],
    mill_findings: Mapping[tuple[str, int], Any] | None = None,
) -> None:
    """Compose one non-blank source line into the run's accumulators."""

    state.counts["source_records"] += 1
    entry = _new_manifest_entry(
        relative, line_number, sha256_hex(physical_line), source_file_sha256
    )
    finding = (
        mill_findings.get((relative, line_number)) if mill_findings else None
    )
    if finding is not None:
        decision = _mill_quarantined_decision(finding)
    else:
        decision = compose_source_line(
            physical_line,
            source_path=relative,
            source_line=line_number,
            source_file_sha256=source_file_sha256,
            calibration_catalog=catalog,
            seen_source_semantics=state.seen_source_semantics,
            seen_curated_semantics=state.seen_curated_semantics,
        )
    entry["action"] = decision.action
    entry["reason_codes"] = list(decision.reason_codes)
    entry["stages"] = [dict(stage) for stage in decision.stages]
    for stage in decision.stages:
        lane = stage["lane"]
        if lane in state.lane_actions:
            state.lane_actions[lane][stage["action"]] += 1

    if decision.action == ACTION_RETAINED and decision.record is not None:
        _record_retained_line(
            state,
            decision,
            entry,
            relative=relative,
            location=f"{relative}:{line_number}",
            emitted=emitted,
        )
    else:
        _record_excluded_line(state, decision, entry)
    state.manifest_lines.append(canonical_json(entry))


def _write_emitted_records(
    state: _ComposeRunState,
    destination_descriptor: int,
    relative: Any,
    emitted: list[str],
) -> None:
    """Write one source file's retained records to the destination."""

    digest = _write_new_text(
        destination_descriptor,
        f"{RECORDS_DIRNAME}/{relative}",
        "".join(line + "\n" for line in emitted),
    )
    state.outputs.append(
        {
            "path": f"{RECORDS_DIRNAME}/{relative}",
            "records": len(emitted),
            "sha256": digest,
        }
    )
    state.counts["output_files"] += 1


def _compose_source_file(
    state: _ComposeRunState,
    *,
    relative: Any,
    raw_file: bytes,
    destination_descriptor: int,
    catalog: Mapping[str, Any] | None,
    mill_findings: Mapping[tuple[str, int], Any] | None = None,
) -> None:
    """Compose every record of one captured source file, then write its output."""

    source_file_sha256 = sha256_hex(raw_file)
    state.counts["source_files"] += 1
    emitted: list[str] = []

    for line_number, physical_line in enumerate(_jsonl_physical_lines(raw_file), 1):
        if not physical_line.strip():
            state.counts["blank_lines"] += 1
            continue
        _compose_one_line(
            state,
            physical_line,
            relative=relative,
            line_number=line_number,
            source_file_sha256=source_file_sha256,
            catalog=catalog,
            emitted=emitted,
            mill_findings=mill_findings,
        )

    if emitted:
        _write_emitted_records(state, destination_descriptor, relative, emitted)


def _captured_source_payloads(
    resolved_source: Path, source_members: tuple[str, ...]
) -> dict[str, bytes]:
    """Read every member exactly once so mills and lanes see the same bytes."""

    return {
        relative: _read_exact_regular_file(
            resolved_source, relative, f"compose source {relative}"
        )[1]
        for relative in source_members
    }


def _write_compose_provenance(
    state: _ComposeRunState, destination_descriptor: int
) -> tuple[str, str]:
    """Write the manifest and reward sidecar files; return their digests."""

    manifest_sha256 = _write_new_text(
        destination_descriptor,
        f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
        "".join(line + "\n" for line in state.manifest_lines),
    )
    sidecar_sha256 = _write_new_text(
        destination_descriptor,
        f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
        "".join(line + "\n" for line in state.sidecar_lines),
    )
    return manifest_sha256, sidecar_sha256


def _compose_run_summary(
    state: _ComposeRunState,
    *,
    resolved_source: Path,
    destination_path: Path,
    calibration_descriptor: Any,
    calibrated_records: int,
    manifest_sha256: str,
    sidecar_sha256: str,
    records_dir: Path,
) -> dict[str, Any]:
    """The run summary written last and returned to the caller."""

    counts = state.counts
    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "source_run": str(resolved_source),
        "destination": str(destination_path),
        "lane_order": list(LANE_ORDER),
        "transforms": transform_contract(),
        "calibration": calibration_descriptor,
        "calibrated_records": calibrated_records,
        "counts": {
            "source_files": counts["source_files"],
            "source_records": counts["source_records"],
            "blank_lines": counts["blank_lines"],
            "retained": counts["retained"],
            "excluded": counts["excluded"],
            "output_files": counts["output_files"],
            "reward_sidecars": len(state.sidecar_lines),
        },
        "lane_actions": {
            lane: dict(sorted(actions.items()))
            for lane, actions in state.lane_actions.items()
        },
        "exclusions": dict(sorted(state.exclusions.items())),
        "outputs": state.outputs,
        "manifest": {
            "path": f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
            "entries": len(state.manifest_lines),
            "sha256": manifest_sha256,
        },
        "reward_sidecars": {
            "path": f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
            "entries": len(state.sidecar_lines),
            "sha256": sidecar_sha256,
        },
        "audit": _audit_records(records_dir, counts["retained"]),
    }


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
    payload_by_member = _captured_source_payloads(resolved_source, source_members)
    mill_findings = compose_mill.index_compose_mills(
        resolved_source, payload_by_member, _jsonl_physical_lines
    )
    catalog, calibration_descriptor = _load_calibration(
        resolved_source,
        Path(units_migration) if units_migration is not None else None,
    )
    pinned_destination = _create_pinned_destination(resolved_source, destination)
    destination_descriptor = pinned_destination.destination_descriptor
    records_dir = pinned_destination.root / RECORDS_DIRNAME
    state = _ComposeRunState()

    try:
        records_dir.mkdir()
        (pinned_destination.root / MANIFEST_DIRNAME).mkdir()
        for relative in source_members:
            _compose_source_file(
                state,
                relative=relative,
                raw_file=payload_by_member[relative],
                destination_descriptor=destination_descriptor,
                catalog=catalog,
                mill_findings=mill_findings,
            )

        manifest_sha256, sidecar_sha256 = _write_compose_provenance(
            state, destination_descriptor
        )
        summary = _compose_run_summary(
            state,
            resolved_source=resolved_source,
            destination_path=pinned_destination.path,
            calibration_descriptor=calibration_descriptor,
            calibrated_records=len(catalog),
            manifest_sha256=manifest_sha256,
            sidecar_sha256=sidecar_sha256,
            records_dir=records_dir,
        )
        _write_new_text(
            destination_descriptor,
            SUMMARY_FILENAME,
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
            curate_rewards.RewardOntologyError, TransactionError, OSError) as exc:
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
