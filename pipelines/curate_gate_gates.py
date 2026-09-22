#!/usr/bin/env python3
"""Gate orchestration and the integration manifest for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

``run_gates`` is the single place that decides whether one cleaned destination
is ``training_ready``. It runs, in this order and never short-circuiting:
final-output evidence authentication, the identity/provenance mapping gate,
``validate_run.py`` and ``check_records.py --strict`` in-process (both modules
are already imported for the audit gates, so their ``main`` entry points run
under redirected streams rather than in a fresh interpreter), the training
audit with its duplicate and canonical-id findings, and the two reward gates.
Every failure becomes a blocker string, and the corpus is ready only when the
blocker list is empty.

``build_manifest`` renders the integration manifest -- the immutable evidence
record a promotion is later replayed against -- and
``manifest_evidence_digest`` hashes it, excluding its own self-reference and
the three fields (``review``, ``blockers``, ``promotion``) that a promotion is
entitled to rewrite.

The repository-rooted paths stay in ``curate_gate``: the siblings take the
roots they need as explicit parameters so that redirecting the gate at a
temporary repository stays visible at the facade call site.
"""

from __future__ import annotations

import contextlib
import copy
import io
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_gates")
    from . import check_records as _check_records
    from . import curate_gate_bindings as _bindings
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_identity_mapping as _identity_mapping
    from . import curate_gate_reward as _reward
    from . import curate_gate_reward_sidecars as _reward_sidecars
    from . import training_audit
    from . import validate_run as _validate_run
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_gates"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import check_records as _check_records
    import curate_gate_bindings as _bindings
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_identity_mapping as _identity_mapping
    import curate_gate_reward as _reward
    import curate_gate_reward_sidecars as _reward_sidecars
    import training_audit
    import validate_run as _validate_run

GateError = _contract.GateError
TOOL_NAME = _contract.TOOL_NAME
TOOL_VERSION = _contract.TOOL_VERSION
MANIFEST_SCHEMA = _contract.MANIFEST_SCHEMA

jsonl_paths = _digest.jsonl_paths
record_sha256 = _digest.record_sha256
_output_evidence_gate = _bindings._output_evidence_gate
_identity_mapping_gate = _identity_mapping._identity_mapping_gate
_reward_ontology_gate = _reward._reward_ontology_gate
_reward_sidecar_gate = _reward_sidecars._reward_sidecar_gate

if __package__:
    from .curate_gate_rights import evaluate_rights
else:
    from curate_gate_rights import evaluate_rights


# ---------------------------------------------------------------------------
# validator gates
# ---------------------------------------------------------------------------


def _exit_code(value: object, stderr: io.StringIO) -> int:
    """Translate a CLI return value or ``SystemExit.code`` to a process code."""
    if value is None:
        return 0
    if isinstance(value, int):
        return int(value)
    print(value, file=stderr)
    return 1


def _run_tool(main: Callable[[list[str]], object], argv: list[str]) -> tuple[int, str]:
    """Run one validator CLI's ``main`` in-process; return ``(exit, stderr)``.

    The gates once spawned ``sys.executable <script>`` children purely for an
    exit code and the stderr lines; both validators are already imported here,
    so their entry points run under redirected streams instead. ``SystemExit``
    maps back to the exit code a child interpreter would have returned, and
    any other exception maps to exit 1 with its traceback captured, keeping
    the fail-closed blocker behaviour unchanged.
    """
    stderr = io.StringIO()
    code = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            code = _exit_code(main(list(argv)), stderr)
    except SystemExit as exc:  # NOSONAR S5754 - a CLI's exit request is the gate's exit code here
        code = _exit_code(exc.code, stderr)
    except Exception:  # a validator crash must still fail closed
        code = 1
        traceback.print_exc(file=stderr)
    return code, stderr.getvalue()


def _findings(stderr: str, limit: int = 10) -> list[str]:
    return [line for line in stderr.splitlines() if line.strip()][:limit]


# ---------------------------------------------------------------------------
# gate orchestration
# ---------------------------------------------------------------------------


class GateInputs(NamedTuple):
    """The authenticated composition evidence every gate reads."""

    record_bindings: Any
    prepared_lanes: Sequence[dict[str, Any]]
    lane_manifests: dict[str, Any]


class _GateLog(NamedTuple):
    """The report under construction: one entry per gate, blockers in order."""

    gates: dict[str, Any]
    blockers: list[str]


def _evidence_gates(cleaned: Path, inputs: GateInputs, log: _GateLog) -> list[dict[str, Any]]:
    output_evidence, records_by_source, normalized_bindings = _output_evidence_gate(
        cleaned,
        inputs.record_bindings,
        inputs.prepared_lanes,
    )
    log.gates["output_evidence"] = output_evidence
    if not output_evidence["passed"]:
        log.blockers.append(
            f"OUTPUT_EVIDENCE_AUTHENTICATION:{output_evidence['invalid_bindings']} invalid"
        )

    identity_mappings = _identity_mapping_gate(
        inputs.lane_manifests["identity_mappings"],
        records_by_source,
    )
    log.gates["identity_mappings"] = identity_mappings
    if not identity_mappings["passed"]:
        log.blockers.append(
            f"IDENTITY_MAPPING_AUTHENTICATION:{identity_mappings['invalid_mappings']} invalid"
        )
    return normalized_bindings


def _completion_source(inputs: GateInputs) -> Path | None:
    for lane in inputs.prepared_lanes:
        if "_completion_source" in lane:
            return lane["_completion_source"]
    return None


def _tool_gates(cleaned: Path, log: _GateLog, completion_source: Path | None) -> dict[str, Any]:
    code, err = _run_tool(_validate_run.main, [str(cleaned)])
    log.gates["structural_validator"] = {
        "tool": "validate_run.py",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        log.blockers.append(f"STRUCTURAL_VALIDATOR_FAILED:exit {code}")

    code, err = _run_tool(_check_records.main, ["--strict", str(cleaned)])
    log.gates["record_invariants"] = {
        "tool": "check_records.py --strict",
        "exit": code,
        "passed": code == 0,
        "findings": _findings(err),
    }
    if code:
        log.blockers.append(f"RECORD_INVARIANTS_FAILED:exit {code}")

    report = training_audit.audit_run(cleaned, completion_source=completion_source)
    log.gates["training_audit"] = {
        "tool": "training_audit.py --strict",
        "passed": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
    }
    if not report["training_ready"]:
        log.blockers.append(f"TRAINING_NOT_READY:{len(report['blockers'])} audit blockers")
    return report


def _audit_gates(report: dict[str, Any], log: _GateLog) -> None:
    exact_duplicates = report.get("exact_duplicates") or []
    log.gates["exact_duplicates"] = {
        "passed": not exact_duplicates,
        "count": len(exact_duplicates),
        "examples": exact_duplicates[:5],
    }
    if exact_duplicates:
        log.blockers.append(f"EXACT_DUPLICATES:{len(exact_duplicates)}")

    identity = report.get("identity") or {}
    collisions = identity.get("duplicates") or []
    log.gates["canonical_id_collisions"] = {
        "passed": not collisions,
        "count": len(collisions),
        "examples": collisions[:5],
    }
    if collisions:
        log.blockers.append(f"CANONICAL_ID_COLLISIONS:{len(collisions)}")

    missing_ids = identity.get("missing_top_level", 0)
    log.gates["canonical_id_coverage"] = {
        "passed": not missing_ids,
        "coverage_pct": identity.get("coverage_pct", 0),
        "missing_top_level": missing_ids,
        "examples": (identity.get("missing_examples") or [])[:5],
    }
    if missing_ids:
        log.blockers.append(f"CANONICAL_ID_COVERAGE:{missing_ids} records lack a top-level id")


def _rights_gate(identity_mappings, log: _GateLog, prepared_lanes=()) -> None:
    report, blockers = evaluate_rights(identity_mappings, prepared_lanes)
    log.gates["rights"] = report
    log.blockers.extend(blockers)


def _reward_gates(
    cleaned: Path,
    normalized_bindings: Sequence[dict[str, Any]],
    prepared_lanes: Sequence[dict[str, Any]],
    log: _GateLog,
) -> None:
    reward_gate = _reward_ontology_gate(cleaned)
    log.gates["reward_ontology"] = reward_gate
    if not reward_gate["passed"]:
        log.blockers.append(
            "REWARD_ONTOLOGY_COVERAGE:"
            f"{reward_gate['missing_annotations']} missing, "
            f"{reward_gate['invalid_annotations']} invalid"
        )

    reward_sidecars = _reward_sidecar_gate(cleaned, normalized_bindings, prepared_lanes)
    log.gates["reward_sidecars"] = reward_sidecars
    if not reward_sidecars["passed"]:
        log.blockers.append(
            "REWARD_SIDECAR_AUTHENTICATION:"
            f"{reward_sidecars['missing_sidecars']} missing, "
            f"{reward_sidecars['invalid_links']} invalid"
        )


def run_gates(cleaned: Path, *, inputs: GateInputs) -> dict[str, Any]:
    """Structural, deep-invariant, and strict corpus gates on one destination."""
    cleaned = Path(cleaned).resolve()
    if not cleaned.is_dir():
        raise GateError(f"not a directory: {cleaned}")
    if not jsonl_paths(cleaned):
        raise GateError(f"cleaned destination holds no *.jsonl: {cleaned}")

    log = _GateLog({}, [])
    normalized_bindings = _evidence_gates(cleaned, inputs, log)
    report = _tool_gates(cleaned, log, _completion_source(inputs))
    _audit_gates(report, log)
    _rights_gate(inputs.lane_manifests.get("identity_mappings") or [], log, inputs.prepared_lanes)
    _reward_gates(cleaned, normalized_bindings, inputs.prepared_lanes, log)

    return {
        "gates": log.gates,
        "blockers": log.blockers,
        "audit": report,
        "training_ready": not log.blockers,
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


class ManifestInputs(NamedTuple):
    """What the integration produced, in the order the manifest reports it."""

    plan: dict[str, Any]
    composition: dict[str, Any]
    lane_manifests: dict[str, Any]
    gate_result: dict[str, Any]
    sample: dict[str, Any]


class ManifestEvidence(NamedTuple):
    """The sealed governance evidence and the mutable review/blocker fields."""

    lane_evidence: Sequence[dict[str, Any]]
    governance_outputs: Sequence[dict[str, Any]]
    review: dict[str, Any] | None
    blockers: Sequence[str]


def _manifest_counts(inputs: ManifestInputs) -> dict[str, Any]:
    lane_manifests = inputs.lane_manifests
    counts = _corpus_counts(inputs.gate_result["audit"])
    counts["lane_actions"] = lane_manifests["actions_by_lane"]
    counts["exclusions"] = len(lane_manifests["exclusions"])
    counts["quarantines"] = len(lane_manifests["quarantines"])
    counts["repairs"] = len(lane_manifests["repairs"])
    counts["identity_mappings"] = len(lane_manifests["identity_mappings"])
    counts["sampled_for_review"] = inputs.sample["sampled_records"]
    counts["review_strata"] = inputs.sample["strata_count"]
    return counts


def build_manifest(inputs: ManifestInputs, evidence: ManifestEvidence) -> dict[str, Any]:
    """Render the immutable integration manifest for one cleaned destination."""
    plan = inputs.plan
    composition = inputs.composition
    lane_manifests = inputs.lane_manifests
    counts = _manifest_counts(inputs)
    return {
        "schema": MANIFEST_SCHEMA,
        "generated_by": f"{TOOL_NAME}/{TOOL_VERSION}",
        "plan": {
            "path": str(plan["plan_path"]),
            "sha256": plan["plan_sha256"],
            "source_run": plan["source_run"],
            "source_run_dir": str(plan["source_run_dir"]),
        },
        "cleaned_dir": str(composition["destination"]),
        "corpus_digest": inputs.sample["corpus_digest"],
        "composition_order": composition["composition_order"],
        "transform_versions": plan["transform_versions"],
        "counts": counts,
        "inputs": composition["inputs"],
        "outputs": composition["outputs"],
        "record_bindings": composition["record_bindings"],
        "governance_outputs": list(evidence.governance_outputs),
        "supersessions": composition["supersessions"],
        "lane_evidence": list(evidence.lane_evidence),
        "exclusions": lane_manifests["exclusions"],
        "quarantines": lane_manifests["quarantines"],
        "repairs": lane_manifests["repairs"],
        "identity_mappings": lane_manifests["identity_mappings"],
        "review_candidates": lane_manifests["review_candidates"],
        "review_sampling": {
            "per_stratum": inputs.sample["per_stratum"],
            "sample_sha256": None,
        },
        "evidence_digest": None,
        "exclusion_reason_codes": lane_manifests["reason_codes"],
        "lanes_without_record_manifest": lane_manifests["lanes_without_manifest"],
        "gates": inputs.gate_result["gates"],
        "review": evidence.review if evidence.review is not None else {"recorded": False},
        "blockers": list(evidence.blockers),
        "training_ready": inputs.gate_result["training_ready"],
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


if __package__:
    _expose_package_sibling(__name__)
