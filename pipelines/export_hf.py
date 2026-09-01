#!/usr/bin/env python3
"""Export a composed curated tree into a lossless, training-ready dataset dir.

The input is a destination written by ``pipelines/compose_curated.py``.  The
export refuses unless ``training_audit`` reports ``training_ready: true`` for
the curated payload, exactly like ``training_audit --strict``.

What it writes (all under a brand-new destination)::

    data/curated/<factory>/<file>.jsonl   byte-identical curated payload
    data/viewer/records.parquet           {source_file, source_line, record_json}
    data/splits/train.jsonl               tiny deterministic split
    data/splits/eval.jsonl                tiny deterministic split
    provenance.json                       digests + training_ready from the audit
    EVAL_PROTOCOL.md                      one-page evaluation protocol

The viewer projection is lossless: ``record_json`` holds the exact curated
JSONL line, so concatenating a file's rows in ``source_line`` order reproduces
that file byte for byte.  The writer emits uncompressed PLAIN Parquet with the
standard library only, and the export reads its own file back and compares it
to the source rows before declaring success.

This command is offline and local.  It never creates or uploads a Hugging Face
repository, and it never launches a trainer.

Usage::

    python3 pipelines/export_hf.py outputs/curated/2026-08-23 outputs/curated/2026-08-23-export
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import training_audit  # noqa: E402

# ``export_hf`` split by responsibility (CodeScene: Lines of Code in a Single
# File): the contract, viewer projection, exact-member reading, deterministic
# split, calibration authentication, and source replay live in sibling
# modules. Every name is re-imported here so existing ``export_hf.X`` call
# sites and tests resolve unchanged.
from export_contract import (  # noqa: E402,F401
    CREATED_BY,
    CURATED_DIRNAME,
    CuratedFile,
    DEFAULT_EVAL_FRACTION,
    DEFAULT_SPLIT_SALT,
    EVAL_PATH,
    EXPORT_NAME,
    EXPORT_VERSION,
    ExportError,
    PROTOCOL_PATH,
    PROVENANCE_PATH,
    SPLIT_POLICY,
    TRAIN_PATH,
    VIEWER_COLUMNS,
    VIEWER_PATH,
    ViewerRow,
    _loads_json,
    _reject_json_constant,
    _reject_nonfinite_json_float,
)
from export_compose_auth import (  # noqa: E402,F401
    _authenticated_compose_summary,
    _authenticated_output_declarations,
    _compose_metadata,
)
from export_calibration import (  # noqa: E402,F401
    _absent_calibration_catalog,
    _authenticated_calibration,
    _entry_calibrations,
    _file_calibration_catalog,
    _load_calibration_payload,
    _validated_calibration_descriptor,
)
from export_members import (  # noqa: E402,F401
    _authenticated_descriptor,
    iter_alias_free_jsonl,
    _compose_member_path,
    _contains_raw_segments,
    _is_under_raw,
    _lf_jsonl_documents,
    _lf_jsonl_lines,
    _read_exact_regular_file,
    _require_exact_directory,
)
from export_provenance import build_export_provenance  # noqa: E402
from export_replay import (  # noqa: E402,F401
    _authenticate_source_replay,
    _replay_source_lines,
    _verify_replay_matches,
)
from export_split import split_bucket, split_rows  # noqa: E402,F401
from export_viewer import (  # noqa: E402,F401
    read_viewer_parquet,
    write_viewer_parquet,
)

__all__ = [
    "CREATED_BY",
    "CURATED_DIRNAME",
    "CuratedFile",
    "DEFAULT_EVAL_FRACTION",
    "DEFAULT_SPLIT_SALT",
    "EVAL_PATH",
    "EXPORT_NAME",
    "EXPORT_VERSION",
    "ExportError",
    "PROTOCOL_PATH",
    "PROVENANCE_PATH",
    "SPLIT_POLICY",
    "TRAIN_PATH",
    "VIEWER_COLUMNS",
    "VIEWER_PATH",
    "ViewerRow",
    "_absent_calibration_catalog",
    "_authenticate_source_replay",
    "_authenticated_calibration",
    "_authenticated_compose_summary",
    "_authenticated_descriptor",
    "_authenticated_output_declarations",
    "_compose_member_path",
    "_compose_metadata",
    "_contains_raw_segments",
    "_entry_calibrations",
    "_file_calibration_catalog",
    "_is_under_raw",
    "_lf_jsonl_documents",
    "_lf_jsonl_lines",
    "_load_calibration_payload",
    "_loads_json",
    "_read_exact_regular_file",
    "_reject_json_constant",
    "_reject_nonfinite_json_float",
    "_replay_source_lines",
    "_require_exact_directory",
    "_validated_calibration_descriptor",
    "_verify_replay_matches",
    "collect_files",
    "collect_rows",
    "export_run",
    "iter_alias_free_jsonl",
    "main",
    "parse_args",
    "read_viewer_parquet",
    "render_eval_protocol",
    "split_bucket",
    "split_rows",
    "write_viewer_parquet",
]


# ── Export ────────────────────────────────────────────────────────────


def _read_curated_file(
    path: Path, relative: str, *, payload: bytes | None = None
) -> CuratedFile:
    """Read one curated JSONL file and prove its lines reproduce its bytes."""

    source_file = f"{CURATED_DIRNAME}/{relative}"
    payload = path.read_bytes() if payload is None else payload
    lines = _lf_jsonl_lines(payload, f"{relative}: curated")
    rows: list[ViewerRow] = []
    for line_number, line in enumerate(lines, 1):
        _loads_json(line, f"{relative}:{line_number}: curated line")
        rows.append(
            ViewerRow(
                source_file=source_file, source_line=line_number, record_json=line
            )
        )
    # Every physical line is now one row with its own line number, so the rows
    # rebuild ``payload`` exactly and the exported copy can be the source bytes.
    return CuratedFile(source_file=source_file, payload=payload, rows=tuple(rows))


def collect_files(records_dir: Path) -> list[CuratedFile]:
    """Read every curated JSONL file in stable path order."""

    files: list[CuratedFile] = []
    for path in iter_alias_free_jsonl(records_dir, "curated records"):
        relative = path.relative_to(records_dir).as_posix()
        exact_path, payload = _read_exact_regular_file(
            records_dir, relative, f"curated payload {relative}"
        )
        files.append(_read_curated_file(exact_path, relative, payload=payload))
    return files


def collect_rows(records_dir: Path) -> list[ViewerRow]:
    """Read every curated JSONL line in stable path and line order."""

    return [row for curated in collect_files(records_dir) for row in curated.rows]


def _write_new_bytes(
    destination_target: int | compose_curated.PinnedDestination,
    relative: Any,
    payload: bytes,
) -> str:
    """Create one new export file with every path component pinned.

    Export shares compose's pinned writer so a same-user process cannot swap a
    child such as ``data/splits`` for a symlink between its ``mkdir`` and the
    matching ``open`` and steer derived output into ``outputs/raw/``.
    """

    try:
        return compose_curated.write_pinned_new_bytes(
            destination_target, relative, payload, f"export {relative}"
        )
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _jsonl_payload(rows: Sequence[ViewerRow]) -> bytes:
    return "".join(row.record_json + "\n" for row in rows).encode("utf-8")


def _create_pinned_destination(
    curated_root: Path, destination: Path
) -> compose_curated.PinnedDestination:
    """Create the export directory through the same parent pin compose uses."""

    try:
        return compose_curated.create_pinned_destination(curated_root, destination)
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _finish_pinned_destination(pinned: compose_curated.PinnedDestination) -> None:
    try:
        pinned.finish()
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc




def _protocol_overview_lines(provenance: dict[str, Any]) -> list[str]:
    """Render the export identity, scope, and fail-closed audit gate."""

    splits = provenance["splits"]
    audit = provenance["audit"]
    return [
        "# Evaluation protocol",
        "",
        f"Export version: `{provenance['export_version']}`  ",
        f"Records: **{provenance['records']}** "
        f"(train {splits['train_records']}, eval {splits['eval_records']})",
        "",
        "## What this is",
        "",
        "A deterministic post-curation snapshot split over one audited corpus.",
        "The source records and curation rules already existed before this split,",
        "so the eval side is **not tuning-independent evidence for curation**. It is",
        "held out only from a future trainer that consumes this exact export.",
        "**No trainer is launched from this repository.** These files are inputs",
        "for a separate, explicitly approved training decision.",
        "",
        "## Gate that produced it",
        "",
        f"- `training_audit` training_ready: **{str(audit['training_ready']).lower()}**",
        f"- Blockers: {json.dumps(audit['blockers'])}",
        "- The export refuses to write anything when a blocker is present.",
        "",
    ]


def _protocol_split_lines(splits: Mapping[str, Any]) -> list[str]:
    """Render the deterministic split rule and evaluation procedure."""

    return [
        "## Split rule",
        "",
        f"- Policy: {splits['policy']}",
        f"- Eval fraction: `{splits['eval_fraction']}`",
        f"- Salt: `{splits['salt']}`",
        "- Re-exporting the identical snapshot with the same salt reproduces the",
        "  same split. The two-sided fallback is snapshot-dependent; adding or",
        "  removing records can change which fallback row is selected.",
        "",
        "## How to evaluate",
        "",
        "1. Train only on `data/splits/train.jsonl`. Never fit on the eval file.",
        "2. Score `data/splits/eval.jsonl` record by record, grouped by the",
        "   `meta.factory` value carried in each split record. A legacy",
        "   preference wrapper predates a wrapper-level `meta.factory` and",
        "   attests the factory on both trajectories instead: when the row has",
        "   no `meta.factory`, group it by the value `chosen.meta.factory` and",
        "   `rejected.meta.factory` agree on, and treat a disagreement as",
        "   unresolved provenance rather than guessing a side.",
        "3. Report per-record-kind metrics separately; the corpus mixes Thalamic",
        "   trajectories, bridge pairs, preference pairs, and coding episodes, and",
        "   a single averaged number hides a collapsed lane.",
        "4. Suggested per-kind measures:",
        "   - Thalamic: safety-gate decision agreement and reward-sign agreement.",
        "     Exclude safety-gate agreement rows where",
        "     `safety_decision.correctness == \"incorrect\"` or",
        "     `meta.supervisor_error_type` is present; those rows deliberately",
        "     carry supervisor-error labels rather than gold gate decisions.",
        "   - Bridge: event-order fidelity of the generated language view.",
        "   - Preference: chosen-vs-rejected ranking accuracy on same-context pairs.",
        "   - Coding: step-level `decision_basis` groundedness in visible evidence.",
        "5. Follow `reward_training.comparability` exactly:",
        "   - `magnitude_comparable`: compare canonical magnitudes.",
        "   - `sign_order_only`: compare sign and order only.",
        "   - `exclude_from_reward_training`: omit reward-derived metrics.",
        "",
    ]


def _protocol_losslessness_lines() -> list[str]:
    """Render the viewer projection's byte-losslessness contract."""

    return [
        "## Losslessness",
        "",
        "`data/viewer/records.parquet` carries `{source_file, source_line,",
        "record_json}`. Concatenating a file's `record_json` rows in `source_line`",
        "order reproduces that curated JSONL byte for byte, so the viewer is a",
        "projection and never a second source of truth.",
        "",
    ]


def render_eval_protocol(provenance: dict[str, Any]) -> str:
    """Render the one-page evaluation protocol that ships with the split."""

    lines = _protocol_overview_lines(provenance)
    lines.extend(_protocol_split_lines(provenance["splits"]))
    lines.extend(_protocol_losslessness_lines())
    return "\n".join(lines)


def _validated_curated_tree(curated_root: Path) -> tuple[Path, Path]:
    """Require the exact curated root and its exact records directory."""

    curated_root = _require_exact_directory(curated_root, "curated root")
    records_dir = curated_root / compose_curated.RECORDS_DIRNAME
    try:
        records_dir = _require_exact_directory(records_dir, "curated records")
    except ExportError as exc:
        raise ExportError(
            f"curated root has no exact {compose_curated.RECORDS_DIRNAME}/ payload: "
            f"{curated_root}"
        ) from exc
    return curated_root, records_dir


def _require_new_export_destination(destination: Path) -> None:
    """Require a new destination under one exact non-raw parent."""

    if os.path.lexists(destination):
        raise ExportError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ExportError(
            f"refusing to write inside immutable raw evidence: {destination}"
        )
    if not destination.parent.is_dir():
        raise ExportError(f"destination parent does not exist: {destination.parent}")
    _require_exact_directory(destination.parent, "destination parent")


def _require_destination_outside_curated(
    resolved_root: Path, destination: Path
) -> None:
    """Refuse a destination at or below the curated source root."""

    resolved_destination = destination.resolve(strict=False)
    if resolved_root == resolved_destination:
        raise ExportError("destination cannot be written inside the curated root")
    if resolved_root in resolved_destination.parents:
        raise ExportError("destination cannot be written inside the curated root")


def _validated_export_paths(
    curated_root: Path, destination: Path
) -> tuple[Path, Path, Path]:
    """Validate both trees and return (curated root, records dir, resolved root)."""

    curated_root, records_dir = _validated_curated_tree(curated_root)
    _require_new_export_destination(destination)
    resolved_root = curated_root.resolve()
    _require_destination_outside_curated(resolved_root, destination)
    return curated_root, records_dir, resolved_root


def _snapshot_relative_path(curated: CuratedFile) -> str:
    """Return one curated payload path relative to the records directory."""

    prefix = f"{CURATED_DIRNAME}/"
    if not curated.source_file.startswith(prefix):
        raise ExportError(f"invalid curated source path: {curated.source_file}")
    return curated.source_file.removeprefix(prefix)


def _snapshot_payloads(curated_files: Sequence[CuratedFile]) -> dict[str, bytes]:
    """Build an unambiguous relative-path to exact-byte snapshot."""

    snapshot: dict[str, bytes] = {}
    for curated in curated_files:
        relative = _snapshot_relative_path(curated)
        if relative in snapshot:
            raise ExportError(f"duplicate curated snapshot path: {relative}")
        snapshot[relative] = curated.payload
    return snapshot


def _curated_snapshot(
    records_dir: Path,
) -> tuple[list[CuratedFile], list[ViewerRow], dict[str, bytes]]:
    """Collect the curated corpus once as (files, rows, exact byte snapshot)."""

    curated_files = collect_files(records_dir)
    rows = [row for curated in curated_files for row in curated.rows]
    if not rows:
        raise ExportError("refusing to export an empty curated corpus")
    return curated_files, rows, _snapshot_payloads(curated_files)


def _require_curated_snapshot_unchanged(
    records_dir: Path, expected: list[CuratedFile]
) -> None:
    """Re-enumerate curated members after authentication and compare exact bytes."""

    current = collect_files(records_dir)
    expected_members, expected_payloads = _curated_snapshot_fingerprint(expected)
    current_members, current_payloads = _curated_snapshot_fingerprint(current)
    if current_members != expected_members:
        raise ExportError("curated member set changed after the initial snapshot")
    if current_payloads != expected_payloads:
        raise ExportError("curated payload changed after the initial snapshot")


def _curated_snapshot_fingerprint(
    files: Sequence[CuratedFile],
) -> tuple[tuple[str, ...], tuple[bytes, ...]]:
    """Return the member names and payloads that define one curated snapshot."""

    return (
        tuple(item.source_file for item in files),
        tuple(item.payload for item in files),
    )


def _training_ready_audit(
    records_dir: Path, snapshot: dict[str, bytes]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the strict audit on the exact snapshot; refuse anything not ready."""

    report = training_audit.audit_run(records_dir, snapshot=snapshot)
    audit = {
        "training_ready": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
        "records": report["totals"]["records"],
        "by_kind": report["totals"]["by_kind"],
    }
    if not audit["training_ready"]:
        raise ExportError(
            "refusing to export a corpus that is not training_ready: "
            + "; ".join(audit["blockers"])
        )
    return report, audit


def _write_curated_payloads(
    destination_target: int | compose_curated.PinnedDestination,
    curated_files: list[CuratedFile],
) -> list[dict[str, Any]]:
    """Copy every curated payload byte-identically into the destination."""

    files: list[dict[str, Any]] = []
    for curated in curated_files:
        digest = _write_new_bytes(
            destination_target, curated.source_file, curated.payload
        )
        files.append(
            {
                "path": curated.source_file,
                "records": len(curated.rows),
                "sha256": digest,
            }
        )
    return files


def _write_viewer_projection(
    destination_target: int | compose_curated.PinnedDestination,
    rows: list[ViewerRow],
) -> str:
    """Write the viewer parquet only after it proves losslessly re-readable."""

    viewer_bytes = write_viewer_parquet(rows)
    round_trip = read_viewer_parquet(viewer_bytes)
    if round_trip != list(rows):
        raise ExportError("viewer projection failed its lossless round-trip check")
    return _write_new_bytes(destination_target, VIEWER_PATH, viewer_bytes)


def _authenticate_written_artifacts(
    destination_root: Path, expected_digests: dict[str, str]
) -> None:
    """Reopen every declared export artifact immediately before commit."""

    for relative, expected_digest in sorted(expected_digests.items()):
        _path, payload = _read_exact_regular_file(
            destination_root, relative, f"export artifact {relative}"
        )
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ExportError(f"export artifact {relative} changed before export commit")


def _write_export_metadata(
    pinned_destination: compose_curated.PinnedDestination,
    provenance: dict[str, Any],
    protocol_digest: str,
    expected_digests: dict[str, str],
) -> None:
    """Write final metadata, then authenticate every artifact before commit."""

    provenance["splits"]["protocol_sha256"] = protocol_digest
    expected_digests[PROTOCOL_PATH] = protocol_digest
    provenance_digest = _write_new_bytes(
        pinned_destination,
        PROVENANCE_PATH,
        (json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        ),
    )
    expected_digests[PROVENANCE_PATH] = provenance_digest
    _authenticate_written_artifacts(pinned_destination.root, expected_digests)


def _refuse_authenticated_source_destination(
    compose_metadata: Mapping[str, Any], destination: Path
) -> None:
    """Keep derived export bytes outside the authenticated compose source."""

    source_root = Path(compose_metadata["source"]["path"])
    resolved_destination = destination.resolve(strict=False)
    if source_root == resolved_destination or source_root in resolved_destination.parents:
        raise ExportError(
            "destination cannot be written inside the authenticated compose source"
        )


@dataclass(frozen=True)
class _ExportRequest:
    """One fully bound invocation of the historically frozen public API."""

    curated_root: Path
    destination: Path
    eval_fraction: float
    split_salt: str
    dataset_name: str | None


@dataclass(frozen=True)
class _PreparedExport:
    """Authenticated source state needed by the destination transaction."""

    request: _ExportRequest
    records_dir: Path
    resolved_root: Path
    curated_files: list[CuratedFile]
    rows: list[ViewerRow]
    audit: dict[str, Any]
    compose_metadata: dict[str, Any]
    train: list[ViewerRow]
    evaluate: list[ViewerRow]


@dataclass(frozen=True)
class _WrittenExport:
    """Authenticated payload details used to build export provenance."""

    files: list[dict[str, Any]]
    viewer_digest: str
    train_digest: str
    eval_digest: str


def _prepare_export(request: _ExportRequest) -> _PreparedExport:
    """Validate and authenticate the exact source snapshot before any write."""

    _curated_root, records_dir, resolved_root = _validated_export_paths(
        request.curated_root,
        request.destination,
    )
    curated_files, rows, snapshot = _curated_snapshot(records_dir)
    report, audit = _training_ready_audit(records_dir, snapshot)
    compose_metadata = _compose_metadata(_curated_root, curated_files, report)
    _refuse_authenticated_source_destination(
        compose_metadata,
        request.destination,
    )
    _require_curated_snapshot_unchanged(records_dir, curated_files)
    train, evaluate = split_rows(
        rows,
        eval_fraction=request.eval_fraction,
        salt=request.split_salt,
    )
    return _PreparedExport(
        request,
        records_dir,
        resolved_root,
        curated_files,
        rows,
        audit,
        compose_metadata,
        train,
        evaluate,
    )


def _write_export_artifacts(
    prepared: _PreparedExport,
    pinned_destination: compose_curated.PinnedDestination,
) -> dict[str, Any]:
    """Write and authenticate every artifact in one pinned destination."""

    files = _write_curated_payloads(pinned_destination, prepared.curated_files)
    expected_digests = {item["path"]: item["sha256"] for item in files}
    viewer_digest = _write_viewer_projection(pinned_destination, prepared.rows)
    expected_digests[VIEWER_PATH] = viewer_digest
    train_digest = _write_new_bytes(
        pinned_destination,
        TRAIN_PATH,
        _jsonl_payload(prepared.train),
    )
    eval_digest = _write_new_bytes(
        pinned_destination,
        EVAL_PATH,
        _jsonl_payload(prepared.evaluate),
    )
    expected_digests.update({TRAIN_PATH: train_digest, EVAL_PATH: eval_digest})
    provenance = _export_provenance(
        prepared,
        _WrittenExport(files, viewer_digest, train_digest, eval_digest),
    )
    protocol_digest = _write_new_bytes(
        pinned_destination,
        PROTOCOL_PATH,
        render_eval_protocol(provenance).encode("utf-8"),
    )
    _write_export_metadata(
        pinned_destination,
        provenance,
        protocol_digest,
        expected_digests,
    )
    # Remove the transaction from its public name before the final source and
    # destination authentication pass.  ``finish`` publishes it with an
    # atomic no-replace rename, which is the public commit point.
    try:
        pinned_destination.begin_commit()
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc
    _require_curated_snapshot_unchanged(
        prepared.records_dir,
        prepared.curated_files,
    )
    _authenticate_written_artifacts(pinned_destination.root, expected_digests)
    return provenance


def _export_provenance(
    prepared: _PreparedExport,
    written: _WrittenExport,
) -> dict[str, Any]:
    """Build provenance from one already written export transaction."""

    return build_export_provenance(
        {
            "resolved_root": prepared.resolved_root,
            "compose_metadata": prepared.compose_metadata,
            "rows": prepared.rows,
            "audit": prepared.audit,
            "options": {
                "dataset_name": prepared.request.dataset_name,
                "eval_fraction": prepared.request.eval_fraction,
                "split_salt": prepared.request.split_salt,
            },
            "written": {
                "files": written.files,
                "viewer_digest": written.viewer_digest,
                "train": prepared.train,
                "evaluate": prepared.evaluate,
                "train_digest": written.train_digest,
                "eval_digest": written.eval_digest,
            },
        }
    )


def _export_request(request: _ExportRequest) -> dict[str, Any]:
    """Execute one prepared export with append-only cleanup semantics."""

    prepared = _prepare_export(request)
    pinned_destination = _create_pinned_destination(
        prepared.resolved_root,
        request.destination,
    )
    try:
        provenance = _write_export_artifacts(prepared, pinned_destination)
    except BaseException:
        pinned_destination.cleanup()
        raise
    _finish_pinned_destination(pinned_destination)
    return provenance


def export_run(
    curated_root: str | Path,
    destination: str | Path,
    *,
    eval_fraction: float = DEFAULT_EVAL_FRACTION,
    split_salt: str = DEFAULT_SPLIT_SALT,
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Export one composed curated tree, refusing anything not training-ready."""

    return _export_request(
        _ExportRequest(
            Path(curated_root),
            Path(destination),
            eval_fraction,
            split_salt,
            dataset_name,
        )
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("curated_root", help="destination written by compose_curated.py")
    parser.add_argument("destination", help="new export directory (must not exist)")
    parser.add_argument(
        "--eval-fraction",
        type=float,
        default=DEFAULT_EVAL_FRACTION,
        help="share of records routed to the eval split (default: 0.1)",
    )
    parser.add_argument(
        "--split-salt",
        default=DEFAULT_SPLIT_SALT,
        help="salt for the deterministic split hash",
    )
    parser.add_argument("--dataset-name", help="optional dataset name recorded in provenance")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        provenance = export_run(
            args.curated_root,
            args.destination,
            eval_fraction=args.eval_fraction,
            split_salt=args.split_salt,
            dataset_name=args.dataset_name,
        )
    except (ExportError, OSError, ValueError) as exc:
        print(f"export_hf: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
