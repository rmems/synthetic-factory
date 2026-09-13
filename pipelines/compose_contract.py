#!/usr/bin/env python3
"""Shared contract for the compose pipeline and its siblings.

Split out of ``compose_curated.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``compose_curated``
so existing ``compose_curated.X`` call sites resolve unchanged. This module
holds the error type, the decision dataclasses, the compose vocabulary, and
the canonical hashing primitives that two or more siblings need.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_contract")
    from . import curate_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_contract"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_identity

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


def default_units_migration_path(source_root: Path) -> Path:
    """Return the canonical calibration candidate for either supported root."""

    relative = Path(FFPC_UNITS_MIGRATION)
    if source_root.name == relative.parts[0]:
        return source_root / relative.name
    return source_root / relative


def published_source_coordinate(relative: str, factory: str) -> str:
    """Return the factory-qualified coordinate published for one source member."""

    factory_path = PurePosixPath(factory)
    if factory_path.name != factory or factory == "..":
        raise ComposeError(f"invalid factory identity for published source coordinate: {factory!r}")
    source_path = PurePosixPath(relative)
    if source_path.parts[: len(factory_path.parts)] == factory_path.parts:
        return source_path.as_posix()
    return (factory_path / source_path).as_posix()


def published_source_snapshot(
    source_members: tuple[str, ...],
    payload_by_member: Mapping[str, bytes],
    identities: Mapping[str, tuple[str, bool]],
) -> tuple[tuple[str, ...], dict[str, bytes], dict[str, tuple[str, bool]]]:
    """Rekey captured bytes from physical paths to collision-free published paths."""

    published_members: list[str] = []
    published_payloads: dict[str, bytes] = {}
    published_identities: dict[str, tuple[str, bool]] = {}
    for relative in source_members:
        factory, verified = identities[relative]
        coordinate = published_source_coordinate(relative, factory)
        if coordinate in published_payloads:
            raise ComposeError(
                "published source coordinate collision: "
                f"{relative!r} and another source member both map to {coordinate!r}"
            )
        published_members.append(coordinate)
        published_payloads[coordinate] = payload_by_member[relative]
        published_identities[coordinate] = factory, verified
    return tuple(published_members), published_payloads, published_identities


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
class TrajectoryPreferenceDecision:
    """Small compatibility surface for the reviewed PR #93 trajectory gate."""

    action: str
    classification: str
    reason_codes: tuple[str, ...]
    record: dict[str, Any] | None
    shared_goal: bool | None
    overlap: dict[str, Any] | None
    side_validation_errors: dict[str, tuple[str, ...]] | None = None


# Identity owns the byte-stable JSON and digest primitives.  Re-export those
# exact callables here instead of wrapping them in a second utility layer.
canonical_json = curate_identity.canonical_json
sha256_hex = curate_identity.sha256_bytes
canonical_sha256 = curate_identity.sha256_json

# Historical private spellings, kept for direct importers and tests.
_TrajectoryPreferenceDecision = TrajectoryPreferenceDecision
_canonical_sha256 = canonical_sha256


if __package__:
    _expose_package_sibling(__name__)
