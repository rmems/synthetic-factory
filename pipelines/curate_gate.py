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
(``curate_gate_identity_mapping``), and the stratified review sample
(``curate_gate_review``) live in siblings. Every name they own is re-exported
here, so an existing ``curate_gate.X`` call site resolves unchanged.

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
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

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
    from . import curate_gate_identity_gate as _identity_gate
    from . import curate_gate_identity_mapping as _identity_mapping
    from . import curate_gate_lanes as _lanes
    from . import curate_gate_manifests as _manifests
    from . import curate_gate_merge as _merge
    from . import curate_gate_paths as _paths
    from . import curate_gate_plan as _plan
    from . import curate_gate_records as _records
    from . import curate_gate_review as _review
    from . import curate_rewards
    from . import training_audit
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
    import curate_gate_identity_gate as _identity_gate  # noqa: E402
    import curate_gate_identity_mapping as _identity_mapping  # noqa: E402
    import curate_gate_lanes as _lanes  # noqa: E402
    import curate_gate_manifests as _manifests  # noqa: E402
    import curate_gate_merge as _merge  # noqa: E402
    import curate_gate_paths as _paths  # noqa: E402
    import curate_gate_plan as _plan  # noqa: E402
    import curate_gate_records as _records  # noqa: E402
    import curate_gate_review as _review  # noqa: E402
    import curate_rewards  # noqa: E402
    import training_audit  # noqa: E402

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
        destination,
        raw_output_root=RAW_OUTPUT_ROOT,
        logical_destination=logical_destination,
        prepared_lanes=prepared_lanes,
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
# gates
# ---------------------------------------------------------------------------


def _run_tool(script: Path, run_dir: Path, *options: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *options, str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _findings(stderr: str, limit: int = 10) -> list[str]:
    return [line for line in stderr.splitlines() if line.strip()][:limit]


def _reward_field_count(value: Any) -> int:
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            if key in curate_rewards.REWARD_KEYS:
                count += 1
            count += _reward_field_count(child)
        return count
    if isinstance(value, list):
        return sum(_reward_field_count(item) for item in value)
    return 0


def _reward_ontology_gate(cleaned: Path) -> dict[str, Any]:
    reward_bearing = 0
    annotated = 0
    missing: list[str] = []
    invalid: list[dict[str, str]] = []
    comparability: Counter[str] = Counter()

    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        reward_count = _reward_field_count(record)
        if not reward_count:
            continue
        reward_bearing += 1
        where = f"{relative}:{line}"
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if annotation is None:
            missing.append(where)
            continue
        annotated += 1
        try:
            curate_rewards.validate_ontology_document(annotation)
            if annotation.get("source_reward_count") != reward_count:
                raise curate_rewards.RewardOntologyError(
                    "source_reward_count does not match record reward fields"
                )
        except curate_rewards.RewardOntologyError as exc:
            invalid.append({"source": where, "error": str(exc)})
            continue
        comparability[str(annotation["comparability"])] += 1

    return {
        "tool": "curate_rewards.validate_ontology_document",
        "passed": not missing and not invalid,
        "reward_bearing_records": reward_bearing,
        "annotated_records": annotated,
        "missing_annotations": len(missing),
        "invalid_annotations": len(invalid),
        "comparability": dict(sorted(comparability.items())),
        "examples": [
            *(
                {"source": source, "error": "reward_training annotation missing"}
                for source in missing[:5]
            ),
            *invalid[:5],
        ][:5],
    }


def _pointer_value(document: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise curate_rewards.RewardOntologyError(f"invalid JSON pointer: {pointer!r}")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            try:
                value = value[int(token)]
            except (ValueError, IndexError) as exc:
                raise curate_rewards.RewardOntologyError(
                    f"sidecar pointer does not resolve: {pointer}"
                ) from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise curate_rewards.RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")
    return value


def _walk_reward_values(value: Any, path: tuple[str | int, ...] = ()) -> Iterable[tuple[str, Any]]:
    """Yield reward scopes from retained output, independent of sidecar claims."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            child_path = (*path, key)
            if key in curate_rewards.REWARD_KEYS:
                yield _json_pointer(child_path), child
            yield from _walk_reward_values(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_reward_values(child, (*path, index))


def _reward_calibration_catalog(
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    catalogs = [
        dict(artifact.get("_catalog") or {})
        for lane in prepared_lanes
        for artifact in lane.get("artifacts", [])
        if artifact.get("kind") == REWARD_CALIBRATION_KIND
    ]
    if len(catalogs) > 1:
        raise GateError("more than one calibration artifact across all lanes")
    return catalogs[0] if catalogs else {}


def _authenticated_record_calibration(
    source_record: dict[str, Any] | None,
    sidecar: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    claimed = sidecar.get("calibration")
    source = sidecar.get("source") if isinstance(sidecar.get("source"), dict) else {}
    sidecar_record_id = source.get("record_id")
    authenticated_id = (
        curate_rewards.canonical_source_record_id(source_record)
        if source_record is not None
        else None
    )
    if (
        source_record is not None
        and sidecar_record_id is not None
        and (
            authenticated_id is None
            or not isinstance(sidecar_record_id, str)
            or curate_rewards.catalog_record_key(authenticated_id)
            != curate_rewards.catalog_record_key(sidecar_record_id)
        )
    ):
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration source identity does not match the authenticated record"
        )
    lookup_id = authenticated_id or sidecar_record_id
    expected = (
        catalog.get(curate_rewards.catalog_record_key(lookup_id))
        if isinstance(lookup_id, str) and lookup_id.strip()
        else None
    )
    if claimed is None:
        classification = sidecar.get("classification")
        comparability = (
            classification.get("comparability") if isinstance(classification, dict) else None
        )
        if expected is not None and comparability == curate_rewards.MAGNITUDE_COMPARABLE:
            raise curate_rewards.RewardOntologyError(
                "sidecar omits calibration evidence present in the migration artifact"
            )
        return expected
    normalized_claimed = curate_rewards.normalize_calibration(claimed)
    if expected is None:
        raise curate_rewards.RewardOntologyError(
            "external calibration has no matching record in the migration artifact"
        )
    normalized_expected = curate_rewards.normalize_calibration(expected)
    if normalized_claimed["source_unit_usd"] != normalized_expected["source_unit_usd"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration does not match the migration artifact for its source record"
        )
    return expected


def _derived_reward_contract(
    record: dict[str, Any],
    sidecar: dict[str, Any],
    calibration_catalog: dict[str, dict[str, Any]],
    source_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Recompute ontology semantics from row values and authenticated evidence."""
    calibration = _authenticated_record_calibration(
        source_record,
        sidecar,
        calibration_catalog,
    )
    output_record = copy.deepcopy(record)
    output_record.pop(curate_rewards.ANNOTATION_FIELD, None)
    reward_items = sorted(_walk_reward_values(output_record), key=lambda item: item[0])
    source_rewards = [
        {
            "json_pointer": pointer,
            "value_sha256": "sha256:" + record_sha256(value),
            "value": copy.deepcopy(value),
        }
        for pointer, value in reward_items
    ]
    arithmetic = [
        curate_rewards.assess_arithmetic(value, pointer) for pointer, value in reward_items
    ]
    comparability, reason_codes, payload = curate_rewards.classify_source_rewards(
        source_rewards,
        arithmetic,
        calibration,
    )
    return {
        "source_rewards": source_rewards,
        "arithmetic": arithmetic,
        "classification": {
            "comparability": comparability,
            "reason_codes": reason_codes,
        },
        "payload": payload,
    }


def _authenticate_reward_semantics(
    record: dict[str, Any],
    annotation: dict[str, Any],
    sidecar: dict[str, Any],
    calibration_catalog: dict[str, dict[str, Any]],
    source_record: dict[str, Any] | None,
) -> None:
    derived = _derived_reward_contract(
        record,
        sidecar,
        calibration_catalog,
        source_record,
    )
    if sidecar.get("source_rewards") != derived["source_rewards"]:
        raise curate_rewards.RewardOntologyError(
            "source_rewards do not match independently enumerated reward values"
        )
    if sidecar.get("arithmetic") != derived["arithmetic"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar arithmetic does not match independent recomputation"
        )
    if sidecar.get("classification") != derived["classification"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar classification does not match independent derivation"
        )
    classification = derived["classification"]
    if (
        annotation.get("comparability") != classification["comparability"]
        or annotation.get("reason_codes") != classification["reason_codes"]
    ):
        raise curate_rewards.RewardOntologyError(
            "record classification does not match independent derivation"
        )
    if annotation.get("source_reward_count") != len(derived["source_rewards"]):
        raise curate_rewards.RewardOntologyError(
            "record annotation reward count mismatches independent enumeration"
        )
    comparability = classification["comparability"]
    if comparability == curate_rewards.MAGNITUDE_COMPARABLE:
        if annotation.get("magnitude") != derived["payload"] or "order" in annotation:
            raise curate_rewards.RewardOntologyError(
                "canonical magnitude or calibration does not match independent derivation"
            )
    elif comparability == curate_rewards.SIGN_ORDER_ONLY:
        if annotation.get("order") != derived["payload"] or "magnitude" in annotation:
            raise curate_rewards.RewardOntologyError(
                "preference order does not match independent derivation"
            )
    elif "magnitude" in annotation or "order" in annotation:
        raise curate_rewards.RewardOntologyError(
            "excluded reward class must not carry magnitude or order claims"
        )


def _reward_sidecar_gate(
    cleaned: Path,
    bindings: Sequence[dict[str, Any]],
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    sidecars: dict[str, dict[str, Any]] = {}
    sidecar_root = cleaned / GOVERNANCE_DIRNAME / REWARD_SIDECAR_DIRNAME
    artifact_paths = (
        [path for path in sorted(sidecar_root.rglob("*")) if path.is_file()]
        if sidecar_root.is_dir()
        else []
    )
    invalid: list[dict[str, str]] = []
    sidecar_sources: dict[tuple[str, int], str] = {}
    for path in artifact_paths:
        try:
            documents = _load_reward_sidecars(path)
        except GateError as exc:
            invalid.append({"source": path.relative_to(cleaned).as_posix(), "error": str(exc)})
            continue
        for document in documents:
            sidecar_id = document["sidecar_id"]
            if sidecar_id in sidecars:
                invalid.append(
                    {
                        "source": path.relative_to(cleaned).as_posix(),
                        "error": f"duplicate sidecar_id {sidecar_id}",
                    }
                )
            else:
                sidecars[sidecar_id] = document
                source = document.get("source")
                try:
                    if not isinstance(source, dict):
                        raise GateError("sidecar source must be an object")
                    source_key = (
                        _logical_source_path(source.get("path"), "sidecar source.path"),
                        source.get("line"),
                    )
                    if (
                        not isinstance(source_key[1], int)
                        or isinstance(source_key[1], bool)
                        or source_key[1] < 1
                    ):
                        raise GateError("sidecar source.line must be a positive integer")
                    if source_key in sidecar_sources:
                        raise GateError(
                            f"sidecar source identity duplicates {sidecar_sources[source_key]}"
                        )
                    sidecar_sources[source_key] = sidecar_id
                except GateError as exc:
                    invalid.append(
                        {"source": path.relative_to(cleaned).as_posix(), "error": str(exc)}
                    )

    linked = 0
    missing: list[str] = []
    used_sidecars: dict[str, str] = {}
    calibration_catalog = _reward_calibration_catalog(prepared_lanes)
    binding_by_output = {
        (binding["output_path"], binding["output_line"]): binding for binding in bindings
    }
    final_source_keys = {(binding["source_path"], binding["source_line"]) for binding in bindings}
    terminal_source_keys: set[tuple[str, int]] = set()
    known_source_keys: set[tuple[str, int]] = set()
    known_source_record_hashes: dict[tuple[str, int], str] = {}
    source_records_by_key: dict[tuple[str, int], Any] = {}
    for lane in prepared_lanes:
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            known_source_keys.add(source_key)
            action = str(entry.get("action") or "").strip().lower()
            if action in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                terminal_source_keys.add(source_key)
            source_record = entry.get("_source_record")
            if source_record is not None:
                known_source_record_hashes[source_key] = record_sha256(source_record)
                source_records_by_key[source_key] = source_record
    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if not isinstance(annotation, dict):
            continue
        where = f"{relative}:{line}"
        sidecar_id = annotation.get("source_sidecar_id")
        sidecar = sidecars.get(sidecar_id)
        if sidecar is None:
            missing.append(where)
            continue
        try:
            curate_rewards.validate_ontology_document(annotation)
            binding = binding_by_output.get((relative, line))
            if binding is None:
                raise curate_rewards.RewardOntologyError(
                    "reward annotation has no authenticated final-output binding"
                )
            source = sidecar.get("source")
            if not isinstance(source, dict):
                raise curate_rewards.RewardOntologyError("sidecar source must be an object")
            sidecar_source_path = _logical_source_path(
                source.get("path"), f"{where} sidecar source.path"
            )
            sidecar_source_line = source.get("line")
            if (
                sidecar_source_path != binding["source_path"]
                or sidecar_source_line != binding["source_line"]
            ):
                raise curate_rewards.RewardOntologyError(
                    "sidecar source identity mismatches final record binding"
                )
            source_record_sha256 = _normalized_sha256(
                source.get("record_sha256"), f"{where} sidecar source.record_sha256"
            )
            if source_record_sha256 != binding["source_record_sha256"]:
                raise curate_rewards.RewardOntologyError(
                    "sidecar source record digest mismatches final record binding"
                )
            first_use = used_sidecars.get(sidecar_id)
            if first_use is not None:
                raise curate_rewards.RewardOntologyError(
                    f"sidecar is linked by more than one final record (first {first_use})"
                )
            source_key = (binding["source_path"], binding["source_line"])
            source_record = source_records_by_key.get(source_key)
            _authenticate_reward_semantics(
                record,
                annotation,
                sidecar,
                calibration_catalog,
                source_record if isinstance(source_record, dict) else None,
            )
            for reward in sidecar["source_rewards"]:
                current = _pointer_value(record, reward.get("json_pointer"))
                expected_hash = _normalized_sha256(
                    reward.get("value_sha256"), f"{where} sidecar reward value_sha256"
                )
                if record_sha256(reward.get("value")) != expected_hash:
                    raise curate_rewards.RewardOntologyError(
                        "source reward sidecar value hash mismatch"
                    )
                if record_sha256(current) != expected_hash:
                    raise curate_rewards.RewardOntologyError(
                        f"record reward differs from sidecar at {reward.get('json_pointer')}"
                    )
                if isinstance(source_record, dict):
                    source_value = _pointer_value(source_record, reward.get("json_pointer"))
                    if record_sha256(source_value) != record_sha256(reward.get("value")):
                        raise curate_rewards.RewardOntologyError(
                            f"sidecar reward does not match authenticated source at {reward.get('json_pointer')}"
                        )
        except (curate_rewards.RewardOntologyError, GateError) as exc:
            invalid.append({"source": where, "error": str(exc)})
            continue
        used_sidecars[sidecar_id] = where
        linked += 1

    orphan_ids = sorted(set(sidecars) - set(used_sidecars))
    terminal_sidecars = 0
    for sidecar_id in orphan_ids:
        sidecar = sidecars[sidecar_id]
        source = sidecar.get("source")
        try:
            if not isinstance(source, dict):
                raise GateError("sidecar source must be an object")
            source_key = (
                _logical_source_path(source.get("path"), "sidecar source.path"),
                source.get("line"),
            )
            if source_key not in known_source_keys:
                raise GateError("orphan sidecar source is absent from lane evidence")
            if source_key in final_source_keys or source_key not in terminal_source_keys:
                raise GateError("reward sidecar has no bound final or terminal source record")
            expected_source_record_hash = known_source_record_hashes.get(source_key)
            if (
                expected_source_record_hash is not None
                and _normalized_sha256(source.get("record_sha256"), "sidecar source.record_sha256")
                != expected_source_record_hash
            ):
                raise GateError("terminal sidecar source record digest mismatches source evidence")
            terminal_sidecars += 1
        except GateError as exc:
            invalid.append({"source": sidecar_id, "error": str(exc)})

    return {
        "tool": "curate_rewards reward-source sidecar verifier",
        "passed": not missing and not invalid,
        "artifact_files": len(artifact_paths),
        "sidecars": len(sidecars),
        "linked_records": linked,
        "missing_sidecars": len(missing),
        "orphan_sidecars": len(orphan_ids),
        "terminal_sidecars": terminal_sidecars,
        "invalid_links": len(invalid),
        "examples": [
            *(
                {"source": source, "error": "source_sidecar_id does not resolve"}
                for source in missing[:5]
            ),
            *invalid[:5],
        ][:5],
    }


def run_gates(
    cleaned: Path,
    *,
    record_bindings: Any,
    prepared_lanes: Sequence[dict[str, Any]],
    lane_manifests: dict[str, Any],
) -> dict[str, Any]:
    """Structural, deep-invariant, and strict corpus gates on one destination."""
    cleaned = Path(cleaned).resolve()
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    if not jsonl_paths(cleaned):
        raise GateError(f"cleaned destination holds no *.jsonl: {cleaned}")

    blockers: list[str] = []
    gates: dict[str, Any] = {}

    output_evidence, records_by_source, normalized_bindings = _output_evidence_gate(
        cleaned,
        record_bindings,
        prepared_lanes,
    )
    gates["output_evidence"] = output_evidence
    if not output_evidence["passed"]:
        blockers.append(
            f"OUTPUT_EVIDENCE_AUTHENTICATION:{output_evidence['invalid_bindings']} invalid"
        )

    identity_mappings = _identity_mapping_gate(
        lane_manifests["identity_mappings"],
        records_by_source,
    )
    gates["identity_mappings"] = identity_mappings
    if not identity_mappings["passed"]:
        blockers.append(
            f"IDENTITY_MAPPING_AUTHENTICATION:{identity_mappings['invalid_mappings']} invalid"
        )

    code, _out, err = _run_tool(VALIDATOR, cleaned)
    gates["structural_validator"] = {
        "tool": "validate_run.py",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"STRUCTURAL_VALIDATOR_FAILED:exit {code}")

    code, _out, err = _run_tool(CHECKER, cleaned, "--strict")
    gates["record_invariants"] = {
        "tool": "check_records.py --strict",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        blockers.append(f"RECORD_INVARIANTS_FAILED:exit {code}")

    report = training_audit.audit_run(cleaned)
    gates["training_audit"] = {
        "tool": "training_audit.py --strict",
        "passed": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
    }
    if not report["training_ready"]:
        blockers.append(f"TRAINING_NOT_READY:{len(report['blockers'])} audit blockers")

    exact_duplicates = report.get("exact_duplicates") or []
    gates["exact_duplicates"] = {
        "passed": not exact_duplicates,
        "count": len(exact_duplicates),
        "examples": exact_duplicates[:5],
    }
    if exact_duplicates:
        blockers.append(f"EXACT_DUPLICATES:{len(exact_duplicates)}")

    identity = report.get("identity") or {}
    collisions = identity.get("duplicates") or []
    gates["canonical_id_collisions"] = {
        "passed": not collisions,
        "count": len(collisions),
        "examples": collisions[:5],
    }
    if collisions:
        blockers.append(f"CANONICAL_ID_COLLISIONS:{len(collisions)}")

    missing_ids = identity.get("missing_top_level", 0)
    gates["canonical_id_coverage"] = {
        "passed": not missing_ids,
        "coverage_pct": identity.get("coverage_pct", 0),
        "missing_top_level": missing_ids,
        "examples": (identity.get("missing_examples") or [])[:5],
    }
    if missing_ids:
        blockers.append(f"CANONICAL_ID_COVERAGE:{missing_ids} records lack a top-level id")

    reward_gate = _reward_ontology_gate(cleaned)
    gates["reward_ontology"] = reward_gate
    if not reward_gate["passed"]:
        blockers.append(
            "REWARD_ONTOLOGY_COVERAGE:"
            f"{reward_gate['missing_annotations']} missing, "
            f"{reward_gate['invalid_annotations']} invalid"
        )

    reward_sidecars = _reward_sidecar_gate(cleaned, normalized_bindings, prepared_lanes)
    gates["reward_sidecars"] = reward_sidecars
    if not reward_sidecars["passed"]:
        blockers.append(
            "REWARD_SIDECAR_AUTHENTICATION:"
            f"{reward_sidecars['missing_sidecars']} missing, "
            f"{reward_sidecars['invalid_links']} invalid"
        )

    return {
        "gates": gates,
        "blockers": blockers,
        "audit": report,
        "training_ready": not blockers,
    }


def _corpus_counts(report: dict[str, Any]) -> dict[str, Any]:
    totals = report.get("totals") or {}
    factories = report.get("factories") or {}
    return {
        "files": totals.get("files", 0),
        "records": totals.get("records", 0),
        "bytes": totals.get("bytes", 0),
        "by_kind": dict(totals.get("by_kind") or {}),
        "by_factory": {
            name: bucket.get("records", 0) for name, bucket in sorted(factories.items())
        },
    }


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------


def build_manifest(
    *,
    plan: dict[str, Any],
    composition: dict[str, Any],
    lane_manifests: dict[str, Any],
    gate_result: dict[str, Any],
    sample: dict[str, Any],
    lane_evidence: Sequence[dict[str, Any]],
    governance_outputs: Sequence[dict[str, Any]],
    review: dict[str, Any] | None,
    blockers: Sequence[str],
) -> dict[str, Any]:
    report = gate_result["audit"]
    counts = _corpus_counts(report)
    counts["lane_actions"] = lane_manifests["actions_by_lane"]
    counts["exclusions"] = len(lane_manifests["exclusions"])
    counts["quarantines"] = len(lane_manifests["quarantines"])
    counts["repairs"] = len(lane_manifests["repairs"])
    counts["identity_mappings"] = len(lane_manifests["identity_mappings"])
    counts["sampled_for_review"] = sample["sampled_records"]
    counts["review_strata"] = sample["strata_count"]

    return {
        "schema": MANIFEST_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "plan": {
            "path": str(plan["plan_path"]),
            "sha256": plan["plan_sha256"],
            "source_run": plan["source_run"],
        },
        "cleaned_dir": str(composition["destination"]),
        "corpus_digest": sample["corpus_digest"],
        "composition_order": composition["composition_order"],
        "transform_versions": plan["transform_versions"],
        "counts": counts,
        "inputs": composition["inputs"],
        "outputs": composition["outputs"],
        "record_bindings": composition["record_bindings"],
        "governance_outputs": list(governance_outputs),
        "supersessions": composition["supersessions"],
        "lane_evidence": list(lane_evidence),
        "exclusions": lane_manifests["exclusions"],
        "quarantines": lane_manifests["quarantines"],
        "repairs": lane_manifests["repairs"],
        "identity_mappings": lane_manifests["identity_mappings"],
        "review_candidates": lane_manifests["review_candidates"],
        "review_sampling": {
            "per_stratum": sample["per_stratum"],
            "sample_sha256": None,
        },
        "evidence_digest": None,
        "exclusion_reason_codes": lane_manifests["reason_codes"],
        "lanes_without_record_manifest": lane_manifests["lanes_without_manifest"],
        "gates": gate_result["gates"],
        "review": review if review is not None else {"recorded": False},
        "blockers": list(blockers),
        "training_ready": gate_result["training_ready"],
        "promotion": None,
    }


def manifest_evidence_digest(manifest: dict[str, Any]) -> str:
    """Hash the immutable integration manifest, excluding its self-reference."""
    payload = copy.deepcopy(manifest)
    payload.pop("evidence_digest", None)
    for mutable_key in ("review", "blockers", "promotion"):
        payload.pop(mutable_key, None)
    sampling = payload.get("review_sampling")
    if isinstance(sampling, dict):
        sampling.pop("sample_sha256", None)
    return "sha256:" + record_sha256(payload)


# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------


def cmd_integrate(args: argparse.Namespace) -> int:
    if args.per_stratum < 1:
        raise GateError("--per-stratum must be at least 1")
    plan = load_plan(Path(args.plan))
    declared_destination = Path(args.cleaned_out)
    if declared_destination.is_symlink():
        _assert_new_destination(declared_destination, "cleaned destination", RAW_OUTPUT_ROOT)
    destination = declared_destination.resolve(strict=False)
    _assert_disjoint_trees(
        plan["source_run_dir"],
        destination,
        source_label="source_run",
        destination_label="cleaned destination",
    )
    destination = _assert_new_destination(
        declared_destination,
        "cleaned destination",
        RAW_OUTPUT_ROOT,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    staged = stage_root / "tree"
    try:
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
        sample = build_sample(staged, args.per_stratum, lane_manifests["review_candidates"])
        sample["cleaned_dir"] = str(destination)

        blockers = list(gate_result["blockers"])
        blockers.append("REVIEW_NOT_RECORDED")

        manifest = build_manifest(
            plan=plan,
            composition=composition,
            lane_manifests=lane_manifests,
            gate_result=gate_result,
            sample=sample,
            lane_evidence=lane_evidence,
            governance_outputs=governance_outputs,
            review=None,
            blockers=blockers,
        )
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
        _rename_noreplace(staged, destination, "cleaned destination", expected_tree)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    summary = {
        "cleaned_out": str(destination),
        "corpus_digest": sample["corpus_digest"],
        "training_ready": gate_result["training_ready"],
        "gate_blockers": gate_result["blockers"],
        "counts": manifest["counts"],
        "review_sample": str(destination / SAMPLE_FILENAME),
        "review_template": str(destination / REVIEW_FILENAME),
        "manifest": str(destination / MANIFEST_FILENAME),
        "next_step": (
            "record a verdict for every sampled record, then run "
            f"'{TOOL_NAME}.py promote --cleaned {destination} --review <file> "
            "--curated-out <new path>'"
        ),
    }
    print(json.dumps(summary, indent=2))
    return 0 if gate_result["training_ready"] else 1


def _promotion_outputs(curated: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(curated.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(curated).as_posix()
        if relative in {MANIFEST_FILENAME, SAMPLE_FILENAME, REVIEW_FILENAME}:
            continue
        entries.append(
            {
                "path": relative,
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def _snapshot_reviewed_tree(
    cleaned: Path,
    review_path: Path,
    destination: Path,
) -> dict[str, Any]:
    """Capture once, then validate and publish only these staged bytes.

    No source file is read again after this function returns.  Cross-file
    digests and all gates are evaluated on ``destination``, which is renamed
    directly into place after successful validation.
    """
    corpus_paths = jsonl_paths(cleaned)
    if not corpus_paths:
        raise GateError(f"no JSONL corpus files under {cleaned}")
    governance = cleaned / GOVERNANCE_DIRNAME
    if not governance.is_dir():
        raise GateError(f"cleaned corpus is missing {GOVERNANCE_DIRNAME} evidence")
    governance_paths = [path for path in sorted(governance.rglob("*")) if path.is_file()]
    control_paths = [cleaned / MANIFEST_FILENAME, cleaned / SAMPLE_FILENAME]
    for control in control_paths:
        if not control.is_file():
            raise GateError(f"cleaned corpus is missing promotion control file: {control}")

    destination.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    records = 0
    for source in [*corpus_paths, *governance_paths, *control_paths]:
        relative = source.relative_to(cleaned)
        payload = _snapshot_bytes(source, cleaned, "cleaned promotion input")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        entry = {
            "path": relative.as_posix(),
            "sha256": sha256_hex(payload),
            "bytes": len(payload),
        }
        entries.append(entry)
        if source in corpus_paths:
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise GateError(f"cannot snapshot invalid UTF-8 JSONL {source}: {exc}") from exc
            records += sum(1 for line in _lf_lines(text) if line.strip())

    review_payload = _snapshot_bytes(review_path, review_path.parent, "review evidence")
    (destination / REVIEW_FILENAME).write_bytes(review_payload)
    review_entry = {
        "path": REVIEW_FILENAME,
        "source_path": str(review_path),
        "sha256": sha256_hex(review_payload),
        "bytes": len(review_payload),
    }
    entries.append({key: value for key, value in review_entry.items() if key != "source_path"})

    by_path = {entry["path"]: entry for entry in entries}
    governance_entries = [
        entry for entry in entries if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
    ]
    return {
        "files": len(corpus_paths),
        "records": records,
        "resorted": 0,
        "governance_files": len(governance_paths),
        "inputs": entries,
        "review": review_entry,
        "integration_manifest": by_path[MANIFEST_FILENAME],
        "review_sample": by_path[SAMPLE_FILENAME],
        "governance": governance_entries,
    }


def cmd_promote(args: argparse.Namespace) -> int:
    cleaned = Path(args.cleaned).resolve()
    curated = _assert_new_destination(
        Path(args.curated_out),
        "curated destination",
        RAW_OUTPUT_ROOT,
    )
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    _assert_disjoint_trees(cleaned, curated)
    review_path = Path(args.review).resolve()
    if not review_path.is_file():
        raise GateError(f"review evidence is missing: {review_path}")
    curated.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{curated.name}.staging-", dir=curated.parent))
    staged = stage_root / "tree"
    try:
        # Capture the corpus, governance evidence, integration controls, and
        # supplied review exactly once.  Everything below reads only ``staged``.
        promotion = _snapshot_reviewed_tree(cleaned, review_path, staged)
        manifest_path = staged / MANIFEST_FILENAME
        sample_path = staged / SAMPLE_FILENAME
        staged_review_path = staged / REVIEW_FILENAME
        manifest = _load_json(manifest_path)
        if not isinstance(manifest, dict):
            raise GateError(f"{manifest_path}: manifest must be a JSON object")
        sample = _load_json(sample_path)
        if not isinstance(sample, dict) or not isinstance(sample.get("items"), list):
            raise GateError(f"{sample_path}: review sample must be an object with an 'items' list")
        review = _load_json(staged_review_path)

        digest = corpus_digest(staged)
        evidence_digest = manifest.get("evidence_digest")
        if not isinstance(evidence_digest, str) or not evidence_digest.startswith("sha256:"):
            raise GateError(f"{manifest_path}: evidence_digest must be a SHA-256")
        _normalized_sha256(evidence_digest, f"{manifest_path}: evidence_digest")
        normalized_bindings = _normalize_record_bindings(manifest.get("record_bindings"))
        retained_source_keys = {
            (binding["source_path"], binding["source_line"]) for binding in normalized_bindings
        }
        source_record_sha256_by_key = {
            (binding["source_path"], binding["source_line"]): binding["source_record_sha256"]
            for binding in normalized_bindings
        }
        evidence_lanes, rebuilt_lane_manifests = verify_lane_evidence(
            staged,
            manifest,
            retained_source_keys,
            source_record_sha256_by_key,
        )
        gate_result = run_gates(
            staged,
            record_bindings=normalized_bindings,
            prepared_lanes=evidence_lanes,
            lane_manifests=rebuilt_lane_manifests,
        )
        sampling = manifest.get("review_sampling")
        if not isinstance(sampling, dict):
            raise GateError(f"{manifest_path}: review_sampling must be an object")
        per_stratum = sampling.get("per_stratum")
        if not isinstance(per_stratum, int) or isinstance(per_stratum, bool) or per_stratum < 1:
            raise GateError(f"{manifest_path}: review_sampling.per_stratum must be at least 1")
        expected_sample = build_sample(
            staged,
            per_stratum,
            rebuilt_lane_manifests["review_candidates"],
            evidence_digest=evidence_digest,
        )
        expected_sample["cleaned_dir"] = str(cleaned)
        review_blockers, review_summary = check_review(
            expected_sample,
            review,
            digest,
            evidence_digest,
        )
        if manifest_evidence_digest(manifest) != evidence_digest:
            review_blockers.append("INTEGRATION_EVIDENCE_MISMATCH")
        if manifest.get("cleaned_dir") != str(cleaned):
            review_blockers.append("CLEANED_DESTINATION_MISMATCH")
        evidence_sections = {
            "exclusions": rebuilt_lane_manifests["exclusions"],
            "quarantines": rebuilt_lane_manifests["quarantines"],
            "repairs": rebuilt_lane_manifests["repairs"],
            "identity_mappings": rebuilt_lane_manifests["identity_mappings"],
            "review_candidates": rebuilt_lane_manifests["review_candidates"],
            "exclusion_reason_codes": rebuilt_lane_manifests["reason_codes"],
            "lanes_without_record_manifest": [],
        }
        if any(manifest.get(key) != value for key, value in evidence_sections.items()):
            review_blockers.append("LANE_EVIDENCE_SUMMARY_MISMATCH")
        expected_sample_hash = sha256_hex(
            training_audit.canonical_blob(expected_sample).encode("utf-8")
        )
        if sampling.get("sample_sha256") != expected_sample_hash:
            review_blockers.append("SAMPLE_MANIFEST_MISMATCH")
        if sample.get("corpus_digest") != digest:
            review_blockers.append("SAMPLE_CORPUS_MISMATCH")
        if sample != expected_sample:
            review_blockers.append("SAMPLE_SELECTION_MISMATCH")

        blockers = list(dict.fromkeys([*gate_result["blockers"], *review_blockers]))
        if blockers:
            print(
                json.dumps(
                    {
                        "promoted": False,
                        "cleaned": str(cleaned),
                        "curated_out": str(curated),
                        "blockers": blockers,
                        "manifest": str(cleaned / MANIFEST_FILENAME),
                    },
                    indent=2,
                )
            )
            return 1

        final_manifest = copy.deepcopy(manifest)
        final_manifest["corpus_digest"] = digest
        final_manifest["gates"] = gate_result["gates"]
        counts = final_manifest.get("counts")
        if not isinstance(counts, dict):
            counts = {}
        counts.update(_corpus_counts(gate_result["audit"]))
        final_manifest["counts"] = counts
        review_summary["review_sha256"] = promotion["review"]["sha256"]
        final_manifest["review"] = review_summary
        final_manifest["training_ready"] = gate_result["training_ready"]
        final_manifest["blockers"] = []

        promoted_digest = corpus_digest(staged)
        if promoted_digest != digest:
            raise GateError("staged corpus changed after validation")
        promoted_outputs = _promotion_outputs(staged)
        governance_outputs = [
            entry
            for entry in promoted_outputs
            if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
        ]
        final_manifest["promotion"] = {
            "curated_dir": str(curated),
            "promoter": "pipelines/curate_gate.py immutable-staged-snapshot",
            "files": promotion["files"],
            "records": promotion["records"],
            "resorted": promotion["resorted"],
            "governance_files": promotion["governance_files"],
            "outputs": promoted_outputs,
            "corpus_digest": promoted_digest,
            "evidence_digest": evidence_digest,
            "integration_manifest_sha256": promotion["integration_manifest"]["sha256"],
            "review_sample_sha256": promotion["review_sample"]["sha256"],
            "review_sha256": promotion["review"]["sha256"],
            "governance_evidence_digest": "sha256:" + record_sha256(governance_outputs),
        }

        # The final manifest replaces its captured integration predecessor;
        # corpus, governance, sample, and review bytes are never recopied.
        _write_json(staged / MANIFEST_FILENAME, final_manifest)
        expected_tree = _tree_snapshot(staged)
        if file_sha256(staged / SAMPLE_FILENAME) != promotion["review_sample"]["sha256"]:
            raise GateError("staged review sample changed after validation")
        if file_sha256(staged / REVIEW_FILENAME) != promotion["review"]["sha256"]:
            raise GateError("staged review evidence changed after validation")
        if corpus_digest(staged) != promoted_digest:
            raise GateError("staged corpus changed after final promotion validation")
        if _promotion_outputs(staged) != promoted_outputs:
            raise GateError("staged promotion outputs changed after final validation")
        _rename_noreplace(staged, curated, "curated destination", expected_tree)
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    print(
        json.dumps(
            {
                "promoted": True,
                "cleaned": str(cleaned),
                "curated_out": str(curated),
                "corpus_digest": final_manifest["promotion"]["corpus_digest"],
                "files": promotion["files"],
                "records": promotion["records"],
                "reviewer": review_summary.get("reviewer"),
                "manifest": str(curated / MANIFEST_FILENAME),
            },
            indent=2,
        )
    )
    return 0


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
    integrate.set_defaults(handler=cmd_integrate)

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
    promote_cmd.set_defaults(handler=cmd_promote)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.handler(args)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
