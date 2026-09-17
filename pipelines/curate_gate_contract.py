#!/usr/bin/env python3
"""Shared vocabulary for the curation integration gate and its siblings.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged. This module holds the error
type, the schema and filename constants, the lane contract, and the decision
vocabularies that two or more siblings need.

The repository-rooted paths (``_PIPELINES``, ``_REPO``, ``RAW_OUTPUT_ROOT``,
``VALIDATOR``, ``CHECKER``) deliberately stay in ``curate_gate`` itself: tests
redirect the gate at a temporary repository by patching those facade globals,
and the siblings take the roots they need as explicit parameters so the
redirection stays visible at the call site.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_contract")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_contract"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))

TOOL_NAME = "curate_gate"
TOOL_VERSION = "1.0.0"

PLAN_SCHEMA = "curation-integration-plan/v1"
MANIFEST_SCHEMA = "curation-manifest/v1"
SAMPLE_SCHEMA = "curation-review-sample/v1"
REVIEW_SCHEMA = "curation-review-verdicts/v1"

MANIFEST_FILENAME = "curation-manifest.json"
SAMPLE_FILENAME = "review-sample.json"
REVIEW_FILENAME = "review-verdicts.json"
GOVERNANCE_DIRNAME = "governance"
LANE_MANIFEST_DIRNAME = "lane-manifests"
REWARD_SIDECAR_DIRNAME = "reward-sidecars"
REWARD_CALIBRATION_DIRNAME = "reward-calibrations"

REWARD_SIDECAR_KIND = "reward_source_sidecars"
REWARD_CALIBRATION_KIND = "reward_units_migration"
REWARD_ARTIFACT_KINDS = frozenset({REWARD_SIDECAR_KIND, REWARD_CALIBRATION_KIND})
SHA256_HEX_RE = re.compile(r"^(?:sha256:)?([0-9a-f]{64})$")

DEFAULT_PER_STRATUM = 2

# The integration gate is meaningful only after every upstream lane has run.
# Bead IDs fix the dependency order; transform names bind each position to the
# reviewed implementation contract rather than accepting an arbitrary subset.
REQUIRED_LANES = (
    ("sf-c5l.1", "bridge_event_time_order"),
    ("sf-c5l.2", "curate_identity"),
    ("sf-c5l.3", "same-context-preference-curation"),
    ("sf-c5l.4", "reward_ontology"),
    ("sf-c5l.5", "coding_observability"),
    ("sf-c5l.6", "tag_taxonomy"),
)

# Which Thalamic view speaks for a record when stratifying by safety gate.
DECISION_ROLE_PRIORITY = ("record", "chosen", "language_view.trajectory", "rejected")

EXCLUSION_ACTIONS = frozenset({"excluded", "exclude", "dropped", "drop"})
QUARANTINE_ACTIONS = frozenset({"quarantine", "quarantined"})
RETAIN_ACTIONS = frozenset({"retained", "retain", "unchanged"})
REPAIR_ACTIONS = frozenset(
    {"changed", "flagged", "migrated", "modified", "modify", "repair", "repaired", "transformed"}
)
NO_OUTPUT_ACTIONS = EXCLUSION_ACTIONS | QUARANTINE_ACTIONS | frozenset({"skipped", "skip"})
OUTPUT_ACTIONS = RETAIN_ACTIONS | REPAIR_ACTIONS
KNOWN_ACTIONS = OUTPUT_ACTIONS | NO_OUTPUT_ACTIONS
DERIVED_CHANGE_REASON = "INTEGRATION_OUTPUT_DIFFERS_FROM_SOURCE"

ACCEPT_VERDICTS = frozenset({"accept", "accepted", "pass"})
REJECT_VERDICTS = frozenset({"reject", "rejected", "fail", "block"})

MANIFEST_LIST_KEYS = ("decisions", "manifest", "entries", "records", "items")


class GateError(Exception):
    """Operator-facing failure: bad plan, bad input, or an unsafe destination."""


if __package__:
    _expose_package_sibling(__name__)
