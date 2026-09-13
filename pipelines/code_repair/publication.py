"""Transactional procedural publication: fresh execution on writes, pure checks on reads.

The round-scoped input artifact stores exact original RUN and candidate bytes as
UTF-8 JSON strings, keeping all rejected/provisional evidence outside training
JSONL census. The completion summary is derived from captured bytes and sealed
authority. Its persisted replay claims never authorize a new publication/export;
those boundaries always execute fresh replay.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import admission, publication_receipt, source_policy as sp
from ._contract import bind_import_twin, load_strict_json, oc
from .selection import DEFAULT_LINEAGE_CAP

GATE = publication_receipt.GATE
INPUT_FORMAT = "code-repair-publication-input/1"
_PACKAGE_PREFIX = "pipelines."
is_procedural_verification = publication_receipt.is_procedural_verification


@dataclass(frozen=True)
class PublishRequest:
    run_dir: Path
    factory_dir: Path
    round_number: int
    lineage_cap: int = DEFAULT_LINEAGE_CAP


def _transaction():
    for name in ("round_txn", "pipelines.round_txn", "__main__"):
        module = sys.modules.get(name)
        path = getattr(module, "__file__", "")
        if path and Path(path).resolve() == sp.ROOT / "pipelines/round_txn.py":
            return module
    if __name__.startswith(_PACKAGE_PREFIX):
        from .. import round_txn
    else:
        import round_txn
    return round_txn


def _fail(detail: str):
    raise _transaction().TransactionError(f"procedural publication refused: {detail}")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def input_name(round_number: int) -> str:
    return f"code-repair-input-r{round_number:02d}.json"


def requires_gate(factory: Path, batch: Path) -> bool:
    records, _errors = _transaction()._jsonl_records(batch)
    return factory.name == sp.POLICY["path_id"] or any(
        _family_record(record)
        for _, record in records
    )


def _family_record(record) -> bool:
    return isinstance(record, dict) and record.get("family") == sp.POLICY["family"]


def _unmixed_records(records, errors) -> bool:
    return not errors and bool(records) and all(_family_record(record) for _, record in records)


def require_legacy_only(factory, paths):
    if any(requires_gate(factory, path) for path in paths):
        _fail("procedural records require an actual completed marker round")


def inspect_completed_if_required(batch, manifest) -> bool:
    if requires_gate(batch.parent, batch):
        validate_completed(batch, manifest)
        return True
    return False


def require_route(factory: Path, batch: Path, *, override=None) -> bool:
    """Reject wrong-path, mixed-family and waiver attempts before legacy checks."""
    if not requires_gate(factory, batch):
        return False
    if override is not None:
        _fail("the procedural fresh execution gate cannot be waived")
    if factory.name != sp.POLICY["path_id"]:
        _fail("code_repair records require the independently reviewed factory path")
    records, errors = _transaction()._jsonl_records(batch)
    if not _unmixed_records(records, errors):
        _fail("the procedural route requires a nonempty unmixed code_repair batch")
    return True


def _records(payload: bytes) -> tuple[list[dict], dict[str, bytes]]:
    if __name__.startswith(_PACKAGE_PREFIX):
        from ..strict_jsonl import strict_lf_jsonl_records
    else:
        from strict_jsonl import strict_lf_jsonl_records
    records, by_id = [], {}
    for raw in strict_lf_jsonl_records(payload, "procedural candidates"):
        record = load_strict_json(raw.decode("utf-8"))
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            _fail("candidate lacks a canonical ID")
        if record["id"] in by_id:
            _fail("duplicate candidate ID")
        records.append(record)
        by_id[record["id"]] = raw
    return records, by_id


def _load_input(path: Path) -> tuple[dict, bytes, bytes]:
    value = load_strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail("round-scoped input must be an object")
    if set(value) != {"format", "run_json", "candidates_jsonl", "lineage_cap"}:
        _fail("invalid round-scoped input fields")
    if value["format"] != INPUT_FORMAT:
        _fail("invalid round-scoped input artifact")
    if not isinstance(value["run_json"], str) or not isinstance(value["candidates_jsonl"], str):
        _fail("original run inputs must be exact UTF-8 strings")
    return value, value["run_json"].encode("utf-8"), value["candidates_jsonl"].encode("utf-8")


def inspect_inputs(factory: Path, batch: Path, round_number: int) -> tuple[dict, list, Any]:
    """Recompute source, full-run and selected-byte bindings without execution."""
    if not require_route(factory, batch):
        _fail("input inspection requires a procedural source route")
    from .selection import selected_records
    from .validation import validate_run
    if __name__.startswith(_PACKAGE_PREFIX):
        from ..curate_identity import default_registry
    else:
        from curate_identity import default_registry
    registry = default_registry()
    row = registry.by_path_id.get(factory.name)
    catalog = admission.load_trusted_catalog(row)
    artifact = batch.parent / input_name(round_number)
    value, run_bytes, candidates = _load_input(artifact)
    run = load_strict_json(run_bytes.decode("utf-8"))
    records, by_id = _records(candidates)
    findings = validate_run(run, records, catalog=catalog, candidates_sha256=_sha(candidates))
    if findings:
        _fail("full original run failed validation: " + "; ".join(findings))
    positives = eligible_records(records, row, catalog)
    selected = selected_records(positives, lineage_cap=value["lineage_cap"])
    expected_batch = _selected_payload(selected, by_id)
    if batch.read_bytes() != expected_batch:
        _fail("published batch must equal exact deterministic selected source bytes")
    binding = {
        "factory": factory.name, "round": round_number,
        "registry_sha256": registry.sha256, "policy_sha256": sp.POLICY_SHA256,
        "catalog_sha256": sp.POLICY["catalog_sha256"],
        "programs_sha256": catalog.programs_sha256,
        "source_license_evidence": dict(sp.POLICY["source_license_evidence"]),
        "run_sha256": _sha(run_bytes), "candidates_sha256": _sha(candidates),
        "input_artifact": artifact.name, "input_sha256": _sha(artifact.read_bytes()),
        "batch_sha256": _sha(expected_batch), "lineage_cap": value["lineage_cap"],
        "candidate_count": len(records), "positive_count": len(positives),
        "selected": [{"id": r["id"], "source_sha256": _sha(by_id[r["id"]])} for r in selected],
        "harness_sha256": run["harness_sha256"],
    }
    return binding, positives, catalog


def eligible_records(records, row, catalog) -> list[dict]:
    """Validate every candidate, preserving only naturally eligible records for selection."""
    return [record for record in records
            if admission.natural_eligibility(record, row, catalog=catalog)[0]]


def _selected_payload(selected, by_id):
    if not selected:
        _fail("publication requires a nonempty selected batch")
    return b"".join(by_id[record["id"]] + b"\n" for record in selected)


def _replay_evidence(records: list[dict]) -> list[dict]:
    return [{"id": r["id"], "evidence_sha256": r["result"]["evidence_sha256"]}
            for r in records]


def _summary(binding: dict, records: list[dict]) -> dict:
    total = len(binding["selected"])
    return {
        "gate": GATE, "strict": True, "semantics_version": 1, "override": None,
        "counts": {"total": total, "verified": total, "failed": 0, "inconclusive": 0},
        "procedural": binding, "fresh_replay": _replay_evidence(records),
    }


def validate_summary(summary: Any) -> dict:
    """Validate tagged marker syntax only; this function grants no authority."""
    try:
        return publication_receipt.validate_summary(summary)
    except ValueError as exc:
        _fail(str(exc))


def fresh_gate(factory: Path, batch: Path, round_number: int) -> dict:
    """Freshly execute all positive input evidence, including positives removed by selection."""
    from . import executor, replay, vocabulary as cv
    try:
        binding, positives, catalog = inspect_inputs(factory, batch, round_number)
        for record in positives:
            engine = executor.Executor(timeout_s=record["oracle"]["configuration"]["timeout_s"])
            result = replay.replay_record(record, catalog, engine)
            if (result.get("code") != cv.REPLAY_PASSED
                    or result.get("fresh_evidence_sha256") != record["result"]["evidence_sha256"]):
                _fail(f"fresh replay failed for {record['id']}: {result}")
        return _summary(binding, positives)
    except (OSError, ValueError) as exc:
        _fail(str(exc))


def validate_completed(batch: Path, manifest: dict) -> dict:
    """Pure revalidation of persisted bindings, never execution or new permission."""
    transaction = _transaction()
    if (transaction.completion_marker_version(manifest, batch)
            != transaction.EXECUTION_VERIFIED_COMPLETION_MARKER_VERSION):
        _fail("procedural completion requires the fresh-gate marker version")
    summary = validate_summary(manifest.get("execution_verification"))
    # Exact int rejects bool and subclasses in the persisted round identity.
    if manifest.get("factory") != batch.parent.name or type(manifest.get("round")) is not int:  # pylint: disable=unidiomatic-typecheck
        _fail("completion factory/round does not bind this batch")
    try:
        binding, positives, _catalog = inspect_inputs(batch.parent, batch, manifest["round"])
        if oc.canonical_json(summary) != oc.canonical_json(_summary(binding, positives)):
            _fail("completion evidence differs from captured original inputs and selected batch")
        _validate_completed_files(batch, manifest)
        return summary
    except (OSError, ValueError) as exc:
        _fail(str(exc))


def _validate_completed_files(batch, manifest):
    required = {batch.name, input_name(manifest["round"])}
    if not required <= {entry.get("name") for entry in manifest.get("files", [])}:
        _fail("completion marker does not own required procedural artifacts")
    for filename in required:
        _transaction().completion_manifest_file_matches(batch.parent / filename, manifest)


def _prepare_captured_run(request: PublishRequest, scratch: Path) -> tuple[bytes, dict]:
    """Capture once, select exact source rows, then run the complete pure preflight."""
    from .selection import selected_records
    if __name__.startswith(_PACKAGE_PREFIX):
        from ..curate_identity import default_registry
    else:
        from curate_identity import default_registry
    transaction = _transaction()
    for filename in ("RUN.json", "candidates.jsonl"):
        transaction.capture_regular_file(request.run_dir / filename, scratch / filename)
    candidates = (scratch / "candidates.jsonl").read_bytes()
    records, by_id = _records(candidates)
    row = default_registry().by_path_id.get(request.factory_dir.name)
    catalog = admission.load_trusted_catalog(row)
    positives = eligible_records(records, row, catalog)
    selected = selected_records(positives, lineage_cap=request.lineage_cap)
    payload = _selected_payload(selected, by_id)
    artifact = {
        "format": INPUT_FORMAT,
        "run_json": (scratch / "RUN.json").read_bytes().decode("utf-8"),
        "candidates_jsonl": candidates.decode("utf-8"), "lineage_cap": request.lineage_cap,
    }
    batch = scratch / f"batch-r{request.round_number:02d}.jsonl"
    with batch.open("xb") as handle:
        handle.write(payload)
    transaction.write_exclusive_json(scratch / input_name(request.round_number), artifact)
    binding, _positives, _catalog = inspect_inputs(request.factory_dir, batch, request.round_number)
    return payload, binding


def publish_run(request: PublishRequest) -> dict:
    """Publish a local completed round after real fresh replay; no Hub or training launch."""
    if request.factory_dir.name != sp.POLICY["path_id"]:
        _fail("request must name the approved factory")
    # Exact int rejects bool and subclasses at the publication boundary.
    if type(request.round_number) is not int or request.round_number < 1:  # pylint: disable=unidiomatic-typecheck
        _fail("request must name a positive round number")
    transaction = _transaction()
    try:
        with tempfile.TemporaryDirectory(prefix="code-repair-publish-") as directory:
            scratch = Path(directory)
            payload, binding = _prepare_captured_run(request, scratch)
            reservation = transaction.reserve(request.factory_dir, request.round_number,
                                              len(binding["selected"]))
            stage = Path(reservation["staging_dir"])
            batch_name = reservation["batch_file"]
            transaction.copy_verified_exclusive(scratch / batch_name, stage / batch_name,
                                                _sha(payload))
            artifact = input_name(request.round_number)
            transaction.copy_verified_exclusive(scratch / artifact, stage / artifact,
                                                binding["input_sha256"])
            notes = (
                "# Procedural code-repair round\n\n"
                f"Selected {len(binding['selected'])} accepted, validated records from "
                f"{binding['candidate_count']} captured candidates. All original records, "
                "including natural rejections and provisional evidence, remain in the "
                f"round-scoped {artifact}.\n\n"
                "The transactional publication gate freshly replays every positive candidate "
                "against the independently pinned reviewed catalog. Selection uses exact/AST "
                f"deduplication and a per-lineage cap of {request.lineage_cap}. "
                "This local round is a training candidate; no model training was launched.\n"
            )
            with (stage / reservation["notes_file"]).open("x", encoding="utf-8") as handle:
                handle.write(notes)
            return transaction.publish(request.factory_dir, request.round_number, reservation["token"])
    except (OSError, ValueError) as exc:
        _fail(str(exc))


bind_import_twin(__name__)
