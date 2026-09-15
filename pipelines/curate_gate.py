#!/usr/bin/env python3
"""Integration and promotion gate for the curation pass (bead ``sf-c5l.7``).

The six curation lanes each write their own curated JSONL tree plus a
record-level manifest. This module is the seventh, final step: it composes
those lane outputs into **one brand-new cleaned destination**, runs every
structural and corpus-level gate on that destination, records a stratified
human-review sample, and promotes to a **brand-new curated path** only when
``training_ready`` is true and the sample has been reviewed.

Siblings
--------

The shared vocabulary (``curate_gate_contract``), the hashing and tree capture
(``curate_gate_digest``), the path confinement and atomic publication
(``curate_gate_paths``), the integration-plan loader (``curate_gate_plan``),
the three-way merge (``curate_gate_merge``), lane authentication
(``curate_gate_lanes``), record-level composition (``curate_gate_compose``),
manifest-entry parsing and the manifest fold (``curate_gate_manifests``),
governance-evidence loading and sealing (``curate_gate_evidence``), the
re-verification of sealed evidence (``curate_gate_evidence_verify``), corpus
record iteration (``curate_gate_records``), the final-output bindings
(``curate_gate_bindings``), identity source-claim authentication
(``curate_gate_identity_gate``), the retained identity/provenance mapping gate
(``curate_gate_identity_mapping``), the stratified review sample
(``curate_gate_review``), the reward ontology and semantics
(``curate_gate_reward``), reward-source sidecar authentication
(``curate_gate_reward_sidecars``), and gate orchestration with the integration
manifest (``curate_gate_gates``) live in siblings. Every name they own is
re-exported here, so an existing ``curate_gate.X`` call site resolves
unchanged. What stays here is the command line: the ``integrate`` and
``promote`` subcommands, the repository roots they redirect, and the two
validator script paths they hand to ``run_gates``.

Composition order and evidence
------------------------------

The order is data, not code: it lives in an integration plan (``--plan``) so a
reviewer can read the exact chain that produced a corpus. Every lane must pair
its output tree with a record-level manifest. The gate authenticates each
emitted record and its exact source bytes against that manifest, then composes
lanes by stable source identity. Each lane output is a three-way delta from the
immutable source: changes at disjoint JSON paths survive together, while two
different changes to the same path fail closed. Terminal exclusion and
quarantine decisions suppress that source record. Unrelated records in the
same JSONL path survive, and every composition is recorded in the manifest.

The documented order for run ``2026-08-17`` is::

    1. sf-c5l.1  bridge_event_time_order   (timing repair / quarantine)
    2. sf-c5l.2  curate_identity           (canonical IDs + provenance)
    3. sf-c5l.3  preference_purity         (same-context pairs)
    4. sf-c5l.4  reward_ontology           (comparability classes)
    5. sf-c5l.5  coding_observability      (no hidden chain-of-thought)
    6. sf-c5l.6  tag_taxonomy              (controlled vocabulary)

Plan schema (``curation-integration-plan/v1``)::

    {
      "schema": "curation-integration-plan/v1",
      "source_run": "outputs/raw/2026-08-17",
      "lanes": [
        {
          "bead": "sf-c5l.1",
          "transform": "bridge_event_time_order",
          "version": "1.0.0",
          "outputs": "lane-bridge",              # dir of curated *.jsonl
          "manifest": "lane-bridge/manifest.jsonl"  # required, record-level
        }
      ]
    }

The reward lane also declares its ``reward_source_sidecars`` artifact. A
lane that used ``--units-migration`` additionally declares the copied
``reward_units_migration`` artifact so calibration claims can be rederived
from the sealed catalog. A
production ``source_run`` beginning with ``outputs/raw`` resolves from the
repository root, so the example remains valid when the plan lives under
``outputs/curation``. A short value such as ``raw`` remains plan-relative for
isolated fixtures. Relative ``outputs``/``manifest``/artifact paths always
resolve against the plan file's directory. Authenticated manifests and reward
sidecars are copied into the cleaned tree as governance evidence and verified
again before promotion.

Usage
-----

::

    python3 pipelines/curate_gate.py integrate \\
        --plan outputs/curation/plan.json \\
        --cleaned-out outputs/cleaned/2026-08-17-curated-v1

    # a human fills in verdicts for every sampled record, then:
    python3 pipelines/curate_gate.py promote \\
        --cleaned outputs/cleaned/2026-08-17-curated-v1 \\
        --review review-verdicts.json \\
        --curated-out outputs/curated/2026-08-17-v1

Both subcommands refuse to write into a destination that already exists, and
neither ever writes into ``outputs/raw/``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, NamedTuple, Sequence

_PIPELINES = Path(__file__).resolve().parent
_REPO = _PIPELINES.parent

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate")
    from . import curate_gate_bindings as _bindings
    from . import curate_gate_compose as _compose
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_evidence as _evidence
    from . import curate_gate_evidence_verify as _evidence_verify
    from . import curate_gate_gates as _gates
    from . import curate_gate_identity_gate as _identity_gate
    from . import curate_gate_identity_mapping as _identity_mapping
    from . import curate_gate_lanes as _lanes
    from . import curate_gate_manifests as _manifests
    from . import curate_gate_merge as _merge
    from . import curate_gate_paths as _paths
    from . import curate_gate_plan as _plan
    from . import curate_gate_promotion as _promotion
    from . import curate_gate_records as _records
    from . import curate_gate_review as _review
    from . import curate_gate_reward as _reward
    from . import curate_gate_reward_sidecars as _reward_sidecars
    from . import training_audit
    from .operator_paths import operator_path
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_bindings as _bindings  # noqa: E402
    import curate_gate_compose as _compose  # noqa: E402
    import curate_gate_contract as _contract  # noqa: E402
    import curate_gate_digest as _digest  # noqa: E402
    import curate_gate_evidence as _evidence  # noqa: E402
    import curate_gate_evidence_verify as _evidence_verify  # noqa: E402
    import curate_gate_gates as _gates  # noqa: E402
    import curate_gate_identity_gate as _identity_gate  # noqa: E402
    import curate_gate_identity_mapping as _identity_mapping  # noqa: E402
    import curate_gate_lanes as _lanes  # noqa: E402
    import curate_gate_manifests as _manifests  # noqa: E402
    import curate_gate_merge as _merge  # noqa: E402
    import curate_gate_paths as _paths  # noqa: E402
    import curate_gate_plan as _plan  # noqa: E402
    import curate_gate_promotion as _promotion  # noqa: E402
    import curate_gate_records as _records  # noqa: E402
    import curate_gate_review as _review  # noqa: E402
    import curate_gate_reward as _reward  # noqa: E402
    import curate_gate_reward_sidecars as _reward_sidecars  # noqa: E402
    import training_audit  # noqa: E402
    from operator_paths import operator_path  # noqa: E402

# ---------------------------------------------------------------------------
# shared contract, re-exported so every ``curate_gate.X`` call site still works
# ---------------------------------------------------------------------------

TOOL_NAME = _contract.TOOL_NAME
TOOL_VERSION = _contract.TOOL_VERSION

PLAN_SCHEMA = _contract.PLAN_SCHEMA
MANIFEST_SCHEMA = _contract.MANIFEST_SCHEMA
SAMPLE_SCHEMA = _contract.SAMPLE_SCHEMA
REVIEW_SCHEMA = _contract.REVIEW_SCHEMA

MANIFEST_FILENAME = _contract.MANIFEST_FILENAME
SAMPLE_FILENAME = _contract.SAMPLE_FILENAME
REVIEW_FILENAME = _contract.REVIEW_FILENAME
GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
LANE_MANIFEST_DIRNAME = _contract.LANE_MANIFEST_DIRNAME
REWARD_SIDECAR_DIRNAME = _contract.REWARD_SIDECAR_DIRNAME
REWARD_CALIBRATION_DIRNAME = _contract.REWARD_CALIBRATION_DIRNAME

REWARD_SIDECAR_KIND = _contract.REWARD_SIDECAR_KIND
REWARD_CALIBRATION_KIND = _contract.REWARD_CALIBRATION_KIND
REWARD_ARTIFACT_KINDS = _contract.REWARD_ARTIFACT_KINDS
SHA256_HEX_RE = _contract.SHA256_HEX_RE

DEFAULT_PER_STRATUM = _contract.DEFAULT_PER_STRATUM
REQUIRED_LANES = _contract.REQUIRED_LANES
DECISION_ROLE_PRIORITY = _contract.DECISION_ROLE_PRIORITY

EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
RETAIN_ACTIONS = _contract.RETAIN_ACTIONS
REPAIR_ACTIONS = _contract.REPAIR_ACTIONS
NO_OUTPUT_ACTIONS = _contract.NO_OUTPUT_ACTIONS
OUTPUT_ACTIONS = _contract.OUTPUT_ACTIONS
KNOWN_ACTIONS = _contract.KNOWN_ACTIONS
DERIVED_CHANGE_REASON = _contract.DERIVED_CHANGE_REASON

ACCEPT_VERDICTS = _contract.ACCEPT_VERDICTS
REJECT_VERDICTS = _contract.REJECT_VERDICTS

MANIFEST_LIST_KEYS = _contract.MANIFEST_LIST_KEYS

GateError = _contract.GateError

# The repository roots stay here. Tests redirect the gate at a temporary
# repository by patching ``_REPO`` and ``RAW_OUTPUT_ROOT`` on this module, so
# the siblings take the roots they need as explicit parameters and the
# redirection stays visible at every call site below.
# The one label every cleaned-destination refusal and publication shares.
_CLEANED_LABEL = "cleaned destination"

VALIDATOR = _PIPELINES / "validate_run.py"
CHECKER = _PIPELINES / "check_records.py"
RAW_OUTPUT_ROOT = (_REPO / "outputs" / "raw").resolve()


# ---------------------------------------------------------------------------
# hashing, tree capture, and exact-JSON file I/O (curate_gate_digest)
# ---------------------------------------------------------------------------

sha256_hex = _digest.sha256_hex
file_sha256 = _digest.file_sha256
jsonl_paths = _digest.jsonl_paths
count_records = _digest.count_records
corpus_digest = _digest.corpus_digest
record_sha256 = _digest.record_sha256
_all_jsonl_paths = _digest._all_jsonl_paths
_lf_lines = _digest._lf_lines
_load_json = _digest._load_json
_normalized_sha256 = _digest._normalized_sha256
_read_regular_file_snapshot = _digest._read_regular_file_snapshot
_tree_snapshot = _digest._tree_snapshot
_write_json = _digest._write_json

# ---------------------------------------------------------------------------
# path confinement and atomic publication (curate_gate_paths)
# ---------------------------------------------------------------------------

_assert_disjoint_trees = _paths._assert_disjoint_trees
_assert_new_destination = _paths._assert_new_destination
_assert_no_symlink = _paths._assert_no_symlink
_lane_manifest_format = _paths._lane_manifest_format
_logical_source_path = _paths._logical_source_path
_normalized_output_path = _paths._normalized_output_path
_relative_artifact_destination = _paths._relative_artifact_destination
_rename_noreplace = _paths._rename_noreplace
_resolve_declared_path = _paths._resolve_declared_path
_resolve_source_run_path = _paths._resolve_source_run_path
_snapshot_bytes = _paths._snapshot_bytes


# ---------------------------------------------------------------------------
# integration plan
# ---------------------------------------------------------------------------


def load_plan(plan_path: Path) -> dict[str, Any]:
    """Read and validate an integration plan; resolve its lane paths."""
    return _plan.load_plan(plan_path, repo_root=_REPO, raw_output_root=RAW_OUTPUT_ROOT)


# ---------------------------------------------------------------------------
# composition: three-way merge (curate_gate_merge), lane authentication
# (curate_gate_lanes), and record-level composition (curate_gate_compose)
# ---------------------------------------------------------------------------

_load_source_records = _merge._load_source_records
_MISSING = _merge._MISSING
_same_json = _merge._same_json
_json_pointer = _merge._json_pointer
_merge_lane_delta = _merge._merge_lane_delta

_prepare_lane = _lanes._prepare_lane
prepare_lanes = _lanes.prepare_lanes
MergeScope = _merge.MergeScope
ComposeTarget = _compose.ComposeTarget


def compose(
    plan: dict[str, Any],
    destination: Path,
    *,
    logical_destination: Path | None = None,
    prepared_lanes: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Three-way-compose authenticated lane deltas by source identity."""
    return _compose.compose(
        plan,
        ComposeTarget(destination, RAW_OUTPUT_ROOT, logical_destination),
        prepared_lanes,
    )


# ---------------------------------------------------------------------------
# lane manifests (curate_gate_manifests): exclusions, quarantines, action
# counts; governance evidence (curate_gate_evidence, curate_gate_evidence_verify)
# and the final-output bindings (curate_gate_bindings)
# ---------------------------------------------------------------------------

_manifest_entries = _manifests._manifest_entries
_normalize_entry = _manifests._normalize_entry
_public_manifest_entry = _manifests._public_manifest_entry
collect_lane_manifests = _manifests.collect_lane_manifests
RetentionView = _manifests.RetentionView

_load_reward_sidecars = _evidence._load_reward_sidecars
_evidence_file = _evidence._evidence_file
copy_lane_evidence = _evidence.copy_lane_evidence
verify_lane_evidence = _evidence_verify.verify_lane_evidence

_normalize_record_bindings = _bindings._normalize_record_bindings
_output_evidence_gate = _bindings._output_evidence_gate


# Identity source-claim authentication (curate_gate_identity_gate) and the
# manifest-wide mapping gate that consumes it (curate_gate_identity_mapping);
# the test fixtures reach these through the facade.
_mapping_value = _identity_gate._mapping_value
_mapping_pointer = _identity_gate._mapping_pointer
_identity_owner_specs = _identity_gate._identity_owner_specs
_source_original_ids = _identity_gate._source_original_ids
_source_original_provenance = _identity_gate._source_original_provenance
_claimed_identity_source_evidence = _identity_gate._claimed_identity_source_evidence
_authenticate_identity_source_claims = _identity_gate._authenticate_identity_source_claims


_canonical_identity_output_id = _identity_gate._canonical_identity_output_id
_identity_mapping_gate = _identity_mapping._identity_mapping_gate


# ---------------------------------------------------------------------------
# stratified review sample (curate_gate_review)
# ---------------------------------------------------------------------------

_primary_decision = _review._primary_decision
_repair_action = _review._repair_action
iter_records = _records.iter_records
_review_candidates_from_manifest = _review._review_candidates_from_manifest
_manifest_factory = _review._manifest_factory
build_sample = _review.build_sample
review_template = _review.review_template
check_review = _review.check_review


# ---------------------------------------------------------------------------
# reward ontology and semantics (curate_gate_reward), reward-source sidecar
# authentication (curate_gate_reward_sidecars)
# ---------------------------------------------------------------------------

_reward_field_count = _reward._reward_field_count
_reward_ontology_gate = _reward._reward_ontology_gate
_pointer_value = _reward._pointer_value
_walk_reward_values = _reward._walk_reward_values
_reward_calibration_catalog = _reward._reward_calibration_catalog
_authenticated_record_calibration = _reward._authenticated_record_calibration
_derived_reward_contract = _reward._derived_reward_contract
_authenticate_reward_semantics = _reward._authenticate_reward_semantics
RewardSemanticsInputs = _reward.RewardSemanticsInputs

_reward_sidecar_gate = _reward_sidecars._reward_sidecar_gate


# ---------------------------------------------------------------------------
# gate orchestration and the integration manifest (curate_gate_gates)
# ---------------------------------------------------------------------------

_run_tool = _gates._run_tool
_findings = _gates._findings
_corpus_counts = _gates._corpus_counts
GateInputs = _gates.GateInputs
GateTools = _gates.GateTools
ManifestInputs = _gates.ManifestInputs
ManifestEvidence = _gates.ManifestEvidence
build_manifest = _gates.build_manifest
manifest_evidence_digest = _gates.manifest_evidence_digest


def run_gates(
    cleaned: Path,
    *,
    record_bindings: Any,
    prepared_lanes: Sequence[dict[str, Any]],
    lane_manifests: dict[str, Any],
) -> dict[str, Any]:
    """Structural, deep-invariant, and strict corpus gates on one destination."""
    return _gates.run_gates(
        cleaned,
        inputs=GateInputs(record_bindings, prepared_lanes, lane_manifests),
        tools=GateTools(VALIDATOR, CHECKER),
    )


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------


class IntegrateInputs(NamedTuple):
    """The confined ``integrate`` arguments; no sink reads ``args`` again."""

    plan: Path
    cleaned_out: Path
    per_stratum: int


class _Integration(NamedTuple):
    """What one staged integration produced, for the summary printed after it."""

    gate_result: dict[str, Any]
    sample: dict[str, Any]
    manifest: dict[str, Any]


def _integrate_destination(plan: dict[str, Any], declared_destination: Path) -> Path:
    """Refuse a cleaned destination that exists, aliases raw, or overlaps the source."""
    if declared_destination.is_symlink():
        _assert_new_destination(declared_destination, _CLEANED_LABEL, RAW_OUTPUT_ROOT)
    destination = declared_destination.resolve(strict=False)
    _assert_disjoint_trees(
        plan["source_run_dir"],
        destination,
        source_label="source_run",
        destination_label=_CLEANED_LABEL,
    )
    return _assert_new_destination(
        declared_destination,
        _CLEANED_LABEL,
        RAW_OUTPUT_ROOT,
    )


def _integrate_evidence(
    plan: dict[str, Any],
    staged: Path,
    destination: Path,
    per_stratum: int,
) -> _Integration:
    """Compose, gate and sample into ``staged``; nothing is published yet."""
    prepared_lanes = prepare_lanes(plan)
    composition = compose(
        plan,
        staged,
        logical_destination=destination,
        prepared_lanes=prepared_lanes,
    )
    lane_evidence, governance_outputs = copy_lane_evidence(prepared_lanes, staged)
    retained_source_keys = {
        (binding["source_path"], binding["source_line"])
        for binding in composition["record_bindings"]
    }
    lane_manifests = collect_lane_manifests(prepared_lanes, retained_source_keys)
    gate_result = run_gates(
        staged,
        record_bindings=composition["record_bindings"],
        prepared_lanes=prepared_lanes,
        lane_manifests=lane_manifests,
    )
    sample = build_sample(staged, per_stratum, lane_manifests["review_candidates"])
    sample["cleaned_dir"] = str(destination)

    blockers = list(gate_result["blockers"])
    blockers.append("REVIEW_NOT_RECORDED")

    manifest = build_manifest(
        ManifestInputs(plan, composition, lane_manifests, gate_result, sample),
        ManifestEvidence(lane_evidence, governance_outputs, None, blockers),
    )
    return _Integration(gate_result, sample, manifest)


def _publish_integration(staged: Path, destination: Path, staging: _Integration) -> None:
    """Seal the staged evidence and publish only a complete tree."""
    manifest = staging.manifest
    sample = staging.sample
    evidence_digest = manifest_evidence_digest(manifest)
    manifest["evidence_digest"] = evidence_digest
    sample["evidence_digest"] = evidence_digest
    manifest["review_sampling"]["sample_sha256"] = sha256_hex(
        training_audit.canonical_blob(sample).encode("utf-8")
    )
    _write_json(staged / MANIFEST_FILENAME, manifest)
    _write_json(staged / SAMPLE_FILENAME, sample)
    _write_json(staged / REVIEW_FILENAME, review_template(sample))

    # Publish only a complete tree. A copy, manifest, gate, or sidecar
    # failure leaves the requested destination absent and retryable.
    expected_tree = _tree_snapshot(staged)
    if corpus_digest(staged) != sample["corpus_digest"]:
        raise GateError("staged corpus changed after integration validation")
    _rename_noreplace(staged, destination, _CLEANED_LABEL, expected_tree)


def _integrate_summary(destination: Path, staging: _Integration) -> dict[str, Any]:
    return {
        "cleaned_out": str(destination),
        "corpus_digest": staging.sample["corpus_digest"],
        "training_ready": staging.gate_result["training_ready"],
        "gate_blockers": staging.gate_result["blockers"],
        "counts": staging.manifest["counts"],
        "review_sample": str(destination / SAMPLE_FILENAME),
        "review_template": str(destination / REVIEW_FILENAME),
        "manifest": str(destination / MANIFEST_FILENAME),
        "next_step": (
            "record a verdict for every sampled record, then run "
            f"'{TOOL_NAME}.py promote --cleaned {destination} --review <file> "
            "--curated-out <new path>'"
        ),
    }


def cmd_integrate(inputs: IntegrateInputs) -> int:
    if inputs.per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    plan = load_plan(inputs.plan)
    destination = _integrate_destination(plan, inputs.cleaned_out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
        staging = _integrate_evidence(plan, staged, destination, inputs.per_stratum)
        _publish_integration(staged, destination, staging)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    print(json.dumps(_integrate_summary(destination, staging), indent=2))
    return 0 if staging.gate_result["training_ready"] else 1


# ---------------------------------------------------------------------------
# promotion of a reviewed cleaned destination (curate_gate_promotion)
# ---------------------------------------------------------------------------

PromotionTools = _promotion.PromotionTools
PromotionPaths = _promotion.PromotionPaths
_promotion_outputs = _promotion.promotion_outputs
_PromotionSources = _promotion._PromotionSources
_promotion_inputs = _promotion._promotion_inputs
_snapshot_one = _promotion._snapshot_one
_snapshot_corpus_records = _promotion._snapshot_corpus_records
_snapshot_review = _promotion._snapshot_review
_snapshot_reviewed_tree = _promotion.snapshot_reviewed_tree
_PromotionEvidence = _promotion.PromotionEvidence
_PromotedTree = _promotion.PromotedTree
_PromotionOutcome = _promotion.PromotionOutcome
_staged_evidence = _promotion.staged_evidence
_lane_evidence_sections = _promotion._lane_evidence_sections
_final_promotion_manifest = _promotion._final_promotion_manifest
_promote_staged = _promotion.promote_staged
_refused_promotion = _promotion.refused_promotion


def _promotion_tools():
    """The seams a promotion publishes through, read from this live namespace."""
    return PromotionTools(
        run_gates, _rename_noreplace, _promotion_outputs, training_audit.canonical_blob
    )


class PromoteInputs(NamedTuple):
    """The confined ``promote`` arguments; no sink reads ``args`` again."""

    cleaned: Path
    review: Path
    curated_out: Path


def _promotion_destinations(inputs: PromoteInputs) -> tuple[Path, Path, Path]:
    """Resolve and refuse the three promotion paths before anything is staged."""
    cleaned = inputs.cleaned.resolve()
    curated = _assert_new_destination(inputs.curated_out, "curated destination", RAW_OUTPUT_ROOT)
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    _assert_disjoint_trees(cleaned, curated)
    review_path = inputs.review.resolve()
    if not review_path.is_file():
        raise GateError(f"review evidence is missing: {review_path}")
    return cleaned, curated, review_path


def cmd_promote(inputs: PromoteInputs) -> int:
    cleaned, curated, review_path = _promotion_destinations(inputs)
    curated.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{curated.name}.staging-", dir=curated.parent))
    staged = stage_root / "tree"
    try:
        outcome = _promote_staged(
            PromotionPaths(staged, cleaned, curated, review_path), _promotion_tools()
        )
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    print(json.dumps(outcome.summary, indent=2))
    return outcome.status


# ---------------------------------------------------------------------------
# command line: operator paths are confined right after parsing
# ---------------------------------------------------------------------------


def _confined_path(value: str) -> Path:
    try:
        return operator_path(value)
    except argparse.ArgumentTypeError as exc:
        raise GateError(f"{value}: {exc}") from exc


def _confined_destination(value: str, label: str) -> Path:
    """Refuse a destination typed as a symlink, then confine it.

    Confinement resolves through the symlink, which would let a dangling
    destination publish through to its target. Existing non-symlink
    destinations stay for the disjoint and overwrite checks that follow.
    """
    typed = Path(value)
    if typed.is_symlink():
        _assert_new_destination(typed, label, RAW_OUTPUT_ROOT)
    return _confined_path(value)


def _integrate_inputs(args: argparse.Namespace) -> IntegrateInputs:
    return IntegrateInputs(
        _confined_path(args.plan),
        _confined_destination(args.cleaned_out, _CLEANED_LABEL),
        args.per_stratum,
    )


def _promote_inputs(args: argparse.Namespace) -> PromoteInputs:
    return PromoteInputs(
        _confined_path(args.cleaned),
        _confined_path(args.review),
        _confined_destination(args.curated_out, "curated destination"),
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compose curation lanes into one new cleaned destination, gate it, "
            "and promote it to a new curated path."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    integrate = sub.add_parser(
        "integrate",
        help="compose lane outputs in plan order, gate them, record a review sample",
    )
    integrate.add_argument("--plan", required=True, help="integration plan JSON")
    integrate.add_argument(
        "--cleaned-out", required=True, help="brand-new cleaned destination (must not exist)"
    )
    integrate.add_argument(
        "--per-stratum",
        type=int,
        default=DEFAULT_PER_STRATUM,
        help=f"records sampled per stratum (default {DEFAULT_PER_STRATUM})",
    )
    integrate.set_defaults(handler=cmd_integrate, inputs=_integrate_inputs)

    promote_cmd = sub.add_parser(
        "promote",
        help="re-gate a cleaned destination and promote it once the sample is reviewed",
    )
    promote_cmd.add_argument(
        "--cleaned", required=True, help="cleaned destination written by 'integrate'"
    )
    promote_cmd.add_argument("--review", required=True, help="reviewed verdict file")
    promote_cmd.add_argument(
        "--curated-out", required=True, help="brand-new curated destination (must not exist)"
    )
    promote_cmd.set_defaults(handler=cmd_promote, inputs=_promote_inputs)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.handler(args.inputs(args))
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
