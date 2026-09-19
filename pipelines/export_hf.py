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
# modules. The historical ``export_hf.X`` surface is re-bound through the
# sibling imports below so existing call sites resolve unchanged and the
# documented patch seams (``export_hf._compose_metadata`` and friends) stay
# live.
import export_calibration as _calibration  # noqa: E402
import export_compose_auth as _compose_auth  # noqa: E402
import export_contract as _contract  # noqa: E402
import export_curated as _curated  # noqa: E402
import export_members as _members  # noqa: E402
import export_replay as _replay  # noqa: E402
import export_split as _split  # noqa: E402
from export_destination import (  # noqa: E402
    _create_pinned_destination,
    _finish_pinned_destination,
    _jsonl_payload,
    _refuse_authenticated_source_destination,
    _validated_export_paths,
    _write_new_bytes,
)
from export_protocol import (  # noqa: E402
    render_eval_protocol,
)
from export_provenance import build_export_provenance  # noqa: E402
from export_viewer import (  # noqa: E402
    read_viewer_parquet,
    write_viewer_parquet,
)

CURATED_DIRNAME = _contract.CURATED_DIRNAME
CuratedFile = _contract.CuratedFile
DEFAULT_EVAL_FRACTION = _contract.DEFAULT_EVAL_FRACTION
DEFAULT_SPLIT = _contract.DEFAULT_SPLIT
DEFAULT_SPLIT_SALT = _contract.DEFAULT_SPLIT_SALT
EVAL_PATH = _contract.EVAL_PATH
ExportError = _contract.ExportError
PROTOCOL_PATH = _contract.PROTOCOL_PATH
PROVENANCE_PATH = _contract.PROVENANCE_PATH
SplitOptions = _contract.SplitOptions
TRAIN_PATH = _contract.TRAIN_PATH
VIEWER_COLUMNS = _contract.VIEWER_COLUMNS
VIEWER_PATH = _contract.VIEWER_PATH
ViewerRow = _contract.ViewerRow
_loads_json = _contract._loads_json

_compose_metadata = _compose_auth._compose_metadata

_authenticated_calibration = _calibration._authenticated_calibration
_load_calibration_payload = _calibration._load_calibration_payload

_read_exact_regular_file = _members._read_exact_regular_file

_curated_snapshot_fingerprint = _curated._curated_snapshot_fingerprint
_snapshot_payloads = _curated._snapshot_payloads
collect_files = _curated.collect_files
collect_rows = _curated.collect_rows

_verify_replay_matches = _replay._verify_replay_matches

split_rows = _split.split_rows

__all__ = """
CURATED_DIRNAME CuratedFile DEFAULT_EVAL_FRACTION DEFAULT_SPLIT
DEFAULT_SPLIT_SALT EVAL_PATH ExportError ExportRequest
PROTOCOL_PATH PROVENANCE_PATH SplitOptions TRAIN_PATH VIEWER_COLUMNS
VIEWER_PATH ViewerRow _authenticated_calibration _compose_metadata
_load_calibration_payload _loads_json _read_exact_regular_file
_verify_replay_matches collect_files collect_rows export_run
main parse_args read_viewer_parquet render_eval_protocol split_rows
write_viewer_parquet
""".split()


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
class ExportRequest:
    """One fully bound invocation of the export."""

    curated_root: str | Path
    destination: str | Path
    split: SplitOptions = DEFAULT_SPLIT
    dataset_name: str | None = None
    oracle_rust_bin: str | Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "curated_root", Path(self.curated_root))
        object.__setattr__(self, "destination", Path(self.destination))


@dataclass(frozen=True)
class _PreparedExport:
    """Authenticated source state needed by the destination transaction."""

    request: ExportRequest
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


def _prepare_export(request: ExportRequest) -> _PreparedExport:
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
        eval_fraction=request.split.eval_fraction,
        salt=request.split.salt,
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
                "eval_fraction": prepared.request.split.eval_fraction,
                "split_salt": prepared.request.split.salt,
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


def _export_request(request: ExportRequest) -> dict[str, Any]:
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


def export_run(request: ExportRequest) -> dict[str, Any]:
    """Export one composed curated tree, refusing anything not training-ready."""

    if __package__:
        from .oracle_grounded.native_gate import runtime_gate
    else:
        from oracle_grounded.native_gate import runtime_gate
    with runtime_gate(request.oracle_rust_bin):
        return _export_request(request)


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
    parser.add_argument("--oracle-rust-bin", help="prebuilt native oracle executable for fresh replay")
    parser.add_argument("--dataset-name", help="optional dataset name recorded in provenance")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        provenance = export_run(
            ExportRequest(
                args.curated_root,
                args.destination,
                split=SplitOptions(args.eval_fraction, args.split_salt),
                dataset_name=args.dataset_name,
                oracle_rust_bin=args.oracle_rust_bin,
            )
        )
    except (ExportError, OSError, ValueError) as exc:
        print(f"export_hf: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
