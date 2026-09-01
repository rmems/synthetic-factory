#!/usr/bin/env python3
"""Shared contract for the compose pipeline and its siblings.

Split out of ``compose_curated.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``compose_curated``
so existing ``compose_curated.X`` call sites resolve unchanged. This module
holds the error type, the decision dataclasses, the compose vocabulary, and
the canonical hashing primitives that two or more siblings need.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__:
    from . import curate_identity
else:
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
