#!/usr/bin/env python3
"""Promotion of a reviewed cleaned destination into a new curated tree.

``curate_gate promote`` captures corpus, governance, controls and review once,
replays every gate against those sealed bytes, and publishes only when nothing
moved. The facade owns the CLI and passes live seams in via PromotionTools so
``mock.patch.object(curate_gate, ...)`` redirections keep flowing.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_promotion")
    from . import curate_gate_bindings as _bindings
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_evidence_verify as _evidence_verify
    from . import curate_gate_gates as _gates
    from . import curate_gate_manifests as _manifests
    from . import curate_gate_paths as _paths
    from . import curate_gate_review as _review
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_promotion"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_bindings as _bindings
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_evidence_verify as _evidence_verify
    import curate_gate_gates as _gates
    import curate_gate_manifests as _manifests
    import curate_gate_paths as _paths
    import curate_gate_review as _review

GateError = _contract.GateError
MANIFEST_FILENAME = _contract.MANIFEST_FILENAME
SAMPLE_FILENAME = _contract.SAMPLE_FILENAME
REVIEW_FILENAME = _contract.REVIEW_FILENAME
GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
CONTROL_FILENAMES = frozenset({MANIFEST_FILENAME, SAMPLE_FILENAME, REVIEW_FILENAME})

sha256_hex = _digest.sha256_hex
file_sha256 = _digest.file_sha256
jsonl_paths = _digest.jsonl_paths
corpus_digest = _digest.corpus_digest
record_sha256 = _digest.record_sha256
_lf_lines = _digest._lf_lines
_load_json = _digest._load_json
_normalized_sha256 = _digest._normalized_sha256
_tree_snapshot = _digest._tree_snapshot
_write_json = _digest._write_json
_snapshot_bytes = _paths._snapshot_bytes
verify_lane_evidence = _evidence_verify.verify_lane_evidence
RetentionView = _manifests.RetentionView
_normalize_record_bindings = _bindings._normalize_record_bindings
build_sample = _review.build_sample
check_review = _review.check_review
manifest_evidence_digest = _gates.manifest_evidence_digest
_corpus_counts = _gates._corpus_counts


class PromotionTools(NamedTuple):
    """The facade seams one promotion publishes through.

    ``run_gates`` and ``rename_noreplace`` are patched by the tests on the
    facade; ``promotion_outputs`` is wrapped there to simulate a tree that
    changes after validation.  Passing them in keeps every redirection live.
    """

    run_gates: Callable[..., dict[str, Any]]
    rename_noreplace: Callable[..., None]
    promotion_outputs: Callable[[Path], list[dict[str, Any]]]
    canonical_blob: Callable[[Any], str]


class PromotionPaths(NamedTuple):
    """The four already-confined paths one promotion runs between."""

    staged: Path
    cleaned: Path
    curated: Path
    review: Path


def promotion_outputs(curated: Path) -> list[dict[str, Any]]:
    """Every published file except the three control files, with digests."""
    entries = []
    for path in sorted(curated.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(curated).as_posix()
        if relative in CONTROL_FILENAMES:
            continue
        entries.append(
            {
                "path": relative,
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


class _PromotionSources(NamedTuple):
    """Every file a promotion copies, in the order it copies them."""

    corpus: list[Path]
    governance: list[Path]
    ordered: list[Path]


def _promotion_inputs(cleaned: Path) -> _PromotionSources:
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
    return _PromotionSources(
        corpus_paths,
        governance_paths,
        [*corpus_paths, *governance_paths, *control_paths],
    )


def _snapshot_one(source: Path, cleaned: Path, destination: Path) -> tuple[bytes, dict[str, Any]]:
    """Copy one confined file into the staging tree and record its bytes."""
    relative = source.relative_to(cleaned)
    payload = _snapshot_bytes(source, cleaned, "cleaned promotion input")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return payload, {
        "path": relative.as_posix(),
        "sha256": sha256_hex(payload),
        "bytes": len(payload),
    }


def _snapshot_corpus_records(payload: bytes, source: Path) -> int:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GateError(f"cannot snapshot invalid UTF-8 JSONL {source}: {exc}") from exc
    return sum(1 for line in _lf_lines(text) if line.strip())


def _snapshot_review(review_path: Path, destination: Path) -> dict[str, Any]:
    review_payload = _snapshot_bytes(review_path, review_path.parent, "review evidence")
    (destination / REVIEW_FILENAME).write_bytes(review_payload)
    return {
        "path": REVIEW_FILENAME,
        "source_path": str(review_path),
        "sha256": sha256_hex(review_payload),
        "bytes": len(review_payload),
    }


def snapshot_reviewed_tree(paths: PromotionPaths) -> dict[str, Any]:
    """Capture once, then validate and publish only these staged bytes.

    No source file is read again after this function returns.  Cross-file
    digests and all gates are evaluated on the staged tree, which is renamed
    directly into place after successful validation.
    """
    cleaned, destination = paths.cleaned, paths.staged
    sources = _promotion_inputs(cleaned)
    corpus_paths = sources.corpus

    destination.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    records = 0
    for source in sources.ordered:
        payload, entry = _snapshot_one(source, cleaned, destination)
        entries.append(entry)
        if source in corpus_paths:
            records += _snapshot_corpus_records(payload, source)

    review_entry = _snapshot_review(paths.review, destination)
    entries.append({key: value for key, value in review_entry.items() if key != "source_path"})

    by_path = {entry["path"]: entry for entry in entries}
    governance_entries = [
        entry for entry in entries if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
    ]
    return {
        "files": len(corpus_paths),
        "records": records,
        "resorted": 0,
        "governance_files": len(sources.governance),
        "inputs": entries,
        "review": review_entry,
        "integration_manifest": by_path[MANIFEST_FILENAME],
        "review_sample": by_path[SAMPLE_FILENAME],
        "governance": governance_entries,
    }


class PromotionEvidence(NamedTuple):
    """The staged integration evidence one promotion is replayed against."""

    manifest: dict[str, Any]
    sample: dict[str, Any]
    review: Any
    digest: str
    evidence_digest: str
    bindings: list[dict[str, Any]]


class _Regate(NamedTuple):
    """What replaying the sealed evidence produced."""

    gate_result: dict[str, Any]
    lane_manifests: dict[str, Any]
    expected_sample: dict[str, Any]


class PromotedTree(NamedTuple):
    """The digest and output listing the published tree must still match."""

    digest: str
    outputs: list[dict[str, Any]]


class PromotionOutcome(NamedTuple):
    """A promotion's exit status and the JSON summary printed for it."""

    status: int
    summary: dict[str, Any]


def staged_evidence(staged: Path) -> PromotionEvidence:
    """Read the captured manifest, sample and review; nothing is read twice."""
    manifest_path = staged / MANIFEST_FILENAME
    sample_path = staged / SAMPLE_FILENAME
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise GateError(f"{manifest_path}: manifest must be a JSON object")
    sample = _load_json(sample_path)
    if not isinstance(sample, dict) or not isinstance(sample.get("items"), list):
        raise GateError(f"{sample_path}: review sample must be an object with an 'items' list")
    review = _load_json(staged / REVIEW_FILENAME)

    digest = corpus_digest(staged)
    evidence_digest = manifest.get("evidence_digest")
    if not isinstance(evidence_digest, str) or not evidence_digest.startswith("sha256:"):
        raise GateError(f"{manifest_path}: evidence_digest must be a SHA-256")
    _normalized_sha256(evidence_digest, f"{manifest_path}: evidence_digest")
    bindings = _normalize_record_bindings(manifest.get("record_bindings"))
    return PromotionEvidence(manifest, sample, review, digest, evidence_digest, bindings)


def _completion_source(manifest: dict[str, Any]) -> Path | None:
    plan = manifest.get("plan")
    if not isinstance(plan, dict):
        raise GateError("curation manifest plan must be an object")
    source = plan.get("source_run_dir")
    if source is None:
        return None
    if not isinstance(source, str) or not Path(source).is_absolute():
        raise GateError("curation completion source must be an absolute path")
    return Path(source)


def _regate_staged(
    staged: Path,
    evidence: PromotionEvidence,
    run_gates: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Rebuild every lane decision from the sealed bytes, then re-run the gates."""
    retained_source_keys = {
        (binding["source_path"], binding["source_line"]) for binding in evidence.bindings
    }
    source_record_sha256_by_key = {
        (binding["source_path"], binding["source_line"]): binding["source_record_sha256"]
        for binding in evidence.bindings
    }
    evidence_lanes, rebuilt_lane_manifests = verify_lane_evidence(
        staged,
        evidence.manifest,
        RetentionView(retained_source_keys, source_record_sha256_by_key),
    )
    evidence_lanes[0]["_completion_source"] = _completion_source(evidence.manifest)
    gate_result = run_gates(
        staged,
        record_bindings=evidence.bindings,
        prepared_lanes=evidence_lanes,
        lane_manifests=rebuilt_lane_manifests,
    )
    return gate_result, rebuilt_lane_manifests


def _expected_review_sample(
    paths: PromotionPaths,
    evidence: PromotionEvidence,
    rebuilt_lane_manifests: dict[str, Any],
) -> dict[str, Any]:
    """Re-derive the sample the recorded ``per_stratum`` must have produced."""
    manifest_path = paths.staged / MANIFEST_FILENAME
    sampling = evidence.manifest.get("review_sampling")
    if not isinstance(sampling, dict):
        raise GateError(f"{manifest_path}: review_sampling must be an object")
    per_stratum = sampling.get("per_stratum")
    if not isinstance(per_stratum, int) or isinstance(per_stratum, bool) or per_stratum < 1:
        raise GateError(f"{manifest_path}: review_sampling.per_stratum must be at least 1")
    expected_sample = build_sample(
        paths.staged,
        per_stratum,
        rebuilt_lane_manifests["review_candidates"],
        evidence_digest=evidence.evidence_digest,
    )
    expected_sample["cleaned_dir"] = str(paths.cleaned)
    return expected_sample


def _regate(paths: PromotionPaths, evidence: PromotionEvidence, tools: PromotionTools) -> _Regate:
    gate_result, rebuilt_lane_manifests = _regate_staged(paths.staged, evidence, tools.run_gates)
    expected_sample = _expected_review_sample(paths, evidence, rebuilt_lane_manifests)
    return _Regate(gate_result, rebuilt_lane_manifests, expected_sample)


def _lane_evidence_sections(rebuilt_lane_manifests: dict[str, Any]) -> dict[str, Any]:
    return {
        "exclusions": rebuilt_lane_manifests["exclusions"],
        "quarantines": rebuilt_lane_manifests["quarantines"],
        "repairs": rebuilt_lane_manifests["repairs"],
        "identity_mappings": rebuilt_lane_manifests["identity_mappings"],
        "review_candidates": rebuilt_lane_manifests["review_candidates"],
        "exclusion_reason_codes": rebuilt_lane_manifests["reason_codes"],
        "lanes_without_record_manifest": [],
    }


def _promotion_review_blockers(
    evidence: PromotionEvidence,
    regate: _Regate,
    cleaned: Path,
    canonical_blob: Callable[[Any], str],
) -> tuple[list[str], dict[str, Any]]:
    """Bind the supplied verdicts to the corpus, the manifest and the sample."""
    expected_sample = regate.expected_sample
    review_blockers, review_summary = check_review(
        expected_sample,
        evidence.review,
        evidence.digest,
        evidence.evidence_digest,
    )
    manifest = evidence.manifest
    if manifest_evidence_digest(manifest) != evidence.evidence_digest:
        review_blockers.append("INTEGRATION_EVIDENCE_MISMATCH")
    if manifest.get("cleaned_dir") != str(cleaned):
        review_blockers.append("CLEANED_DESTINATION_MISMATCH")
    evidence_sections = _lane_evidence_sections(regate.lane_manifests)
    if any(manifest.get(key) != value for key, value in evidence_sections.items()):
        review_blockers.append("LANE_EVIDENCE_SUMMARY_MISMATCH")
    expected_sample_hash = sha256_hex(canonical_blob(expected_sample).encode("utf-8"))
    if manifest["review_sampling"].get("sample_sha256") != expected_sample_hash:
        review_blockers.append("SAMPLE_MANIFEST_MISMATCH")
    if evidence.sample.get("corpus_digest") != evidence.digest:
        review_blockers.append("SAMPLE_CORPUS_MISMATCH")
    if evidence.sample != expected_sample:
        review_blockers.append("SAMPLE_SELECTION_MISMATCH")
    return review_blockers, review_summary


def _final_promotion_manifest(
    evidence: PromotionEvidence,
    gate_result: dict[str, Any],
    review_summary: dict[str, Any],
) -> dict[str, Any]:
    final_manifest = copy.deepcopy(evidence.manifest)
    final_manifest["corpus_digest"] = evidence.digest
    final_manifest["gates"] = gate_result["gates"]
    counts = final_manifest.get("counts")
    if not isinstance(counts, dict):
        counts = {}
    counts.update(_corpus_counts(gate_result["audit"]))
    final_manifest["counts"] = counts
    final_manifest["review"] = review_summary
    final_manifest["training_ready"] = gate_result["training_ready"]
    final_manifest["blockers"] = []
    return final_manifest


def _promotion_record(
    paths: PromotionPaths,
    promotion: dict[str, Any],
    evidence: PromotionEvidence,
    tools: PromotionTools,
) -> tuple[PromotedTree, dict[str, Any]]:
    promoted_digest = corpus_digest(paths.staged)
    if promoted_digest != evidence.digest:
        raise GateError("staged corpus changed after validation")
    promoted_outputs = tools.promotion_outputs(paths.staged)
    governance_outputs = [
        entry
        for entry in promoted_outputs
        if Path(entry["path"]).parts[0] == GOVERNANCE_DIRNAME
    ]
    record = {
        "curated_dir": str(paths.curated),
        "promoter": "pipelines/curate_gate.py immutable-staged-snapshot",
        "files": promotion["files"],
        "records": promotion["records"],
        "resorted": promotion["resorted"],
        "governance_files": promotion["governance_files"],
        "outputs": promoted_outputs,
        "corpus_digest": promoted_digest,
        "evidence_digest": evidence.evidence_digest,
        "integration_manifest_sha256": promotion["integration_manifest"]["sha256"],
        "review_sample_sha256": promotion["review_sample"]["sha256"],
        "review_sha256": promotion["review"]["sha256"],
        "governance_evidence_digest": "sha256:" + record_sha256(governance_outputs),
    }
    return PromotedTree(promoted_digest, promoted_outputs), record


def _publish_promotion(
    paths: PromotionPaths,
    promotion: dict[str, Any],
    tree: PromotedTree,
    tools: PromotionTools,
) -> None:
    """Publish only bytes that have not moved since they were validated."""
    staged = paths.staged
    expected_tree = _tree_snapshot(staged)
    if file_sha256(staged / SAMPLE_FILENAME) != promotion["review_sample"]["sha256"]:
        raise GateError("staged review sample changed after validation")
    if file_sha256(staged / REVIEW_FILENAME) != promotion["review"]["sha256"]:
        raise GateError("staged review evidence changed after validation")
    if corpus_digest(staged) != tree.digest:
        raise GateError("staged corpus changed after final promotion validation")
    if tools.promotion_outputs(staged) != tree.outputs:
        raise GateError("staged promotion outputs changed after final validation")
    tools.rename_noreplace(staged, paths.curated, "curated destination", expected_tree)


def _promoted_summary(
    paths: PromotionPaths,
    promotion: dict[str, Any],
    record: dict[str, Any],
    reviewer: Any,
) -> dict[str, Any]:
    return {
        "promoted": True,
        "cleaned": str(paths.cleaned),
        "curated_out": str(paths.curated),
        "corpus_digest": record["corpus_digest"],
        "files": promotion["files"],
        "records": promotion["records"],
        "reviewer": reviewer,
        "manifest": str(paths.curated / MANIFEST_FILENAME),
    }


def promote_staged(paths: PromotionPaths, tools: PromotionTools) -> PromotionOutcome:
    """Capture, replay, bind the review, and publish; refuse on any blocker."""
    # Capture the corpus, governance evidence, integration controls, and
    # supplied review exactly once.  Everything below reads only ``staged``.
    promotion = snapshot_reviewed_tree(paths)
    evidence = staged_evidence(paths.staged)
    regate = _regate(paths, evidence, tools)
    review_blockers, review_summary = _promotion_review_blockers(
        evidence, regate, paths.cleaned, tools.canonical_blob
    )

    blockers = list(dict.fromkeys([*regate.gate_result["blockers"], *review_blockers]))
    if blockers:
        return refused_promotion(paths.cleaned, paths.curated, blockers)

    review_summary["review_sha256"] = promotion["review"]["sha256"]
    final_manifest = _final_promotion_manifest(evidence, regate.gate_result, review_summary)
    tree, record = _promotion_record(paths, promotion, evidence, tools)
    final_manifest["promotion"] = record

    # The final manifest replaces its captured integration predecessor;
    # corpus, governance, sample, and review bytes are never recopied.
    _write_json(paths.staged / MANIFEST_FILENAME, final_manifest)
    _publish_promotion(paths, promotion, tree, tools)
    return PromotionOutcome(
        0, _promoted_summary(paths, promotion, record, review_summary.get("reviewer"))
    )


def refused_promotion(cleaned: Path, curated: Path, blockers: list[str]) -> PromotionOutcome:
    summary = {
        "promoted": False,
        "cleaned": str(cleaned),
        "curated_out": str(curated),
        "blockers": blockers,
        "manifest": str(cleaned / MANIFEST_FILENAME),
    }
    return PromotionOutcome(1, summary)


if __package__:
    _expose_package_sibling(__name__)
