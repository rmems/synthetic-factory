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
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    DEFAULT_SPLIT,
    DEFAULT_SPLIT_SALT,
    EVAL_PATH,
    EXPORT_NAME,
    EXPORT_VERSION,
    ExportError,
    PROTOCOL_PATH,
    PROVENANCE_PATH,
    SPLIT_POLICY,
    SplitOptions,
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
from export_curated import (  # noqa: E402,F401
    _curated_snapshot_fingerprint,
    _snapshot_payloads,
    collect_files,
    collect_rows,
)
from export_destination import (  # noqa: E402,F401
    _create_pinned_destination,
    _finish_pinned_destination,
    _jsonl_payload,
    _refuse_authenticated_source_destination,
    _validated_export_paths,
    _write_new_bytes,
)
from export_protocol import (  # noqa: E402,F401
    render_eval_protocol,
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
    "DEFAULT_SPLIT",
    "DEFAULT_SPLIT_SALT",
    "EVAL_PATH",
    "EXPORT_NAME",
    "EXPORT_VERSION",
    "ExportError",
    "PROTOCOL_PATH",
    "PROVENANCE_PATH",
    "SPLIT_POLICY",
    "SplitOptions",
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
    split: SplitOptions = DEFAULT_SPLIT,
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Export one composed curated tree, refusing anything not training-ready."""

    return _export_request(
        _ExportRequest(
            Path(curated_root),
            Path(destination),
            split.eval_fraction,
            split.salt,
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
            split=SplitOptions(args.eval_fraction, args.split_salt),
            dataset_name=args.dataset_name,
        )
    except (ExportError, OSError, ValueError) as exc:
        print(f"export_hf: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
