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
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

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
    _read_exact_regular_file,
    _require_exact_directory,
)
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
    "_load_calibration_payload",
    "_loads_json",
    "_read_exact_regular_file",
    "_reject_json_constant",
    "_replay_source_lines",
    "_require_exact_directory",
    "_validated_calibration_descriptor",
    "_verify_replay_matches",
    "collect_files",
    "collect_rows",
    "export_run",
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
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{relative}: curated payload is not UTF-8: {exc}") from exc
    # Split on LF only: ``str.splitlines`` also breaks on U+2028/U+2029, which
    # curated records may legitimately contain inside a JSON string.
    lines = text.split("\n")
    trailing = lines.pop() if lines else ""
    if trailing:
        raise ExportError(f"{relative}: curated JSONL must end with a newline")
    rows: list[ViewerRow] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            raise ExportError(f"{relative}:{line_number}: curated JSONL has a blank line")
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


def _write_new_bytes(root_descriptor: int, relative: Any, payload: bytes) -> str:
    """Create one new export file with every path component pinned.

    Export shares compose's pinned writer so a same-user process cannot swap a
    child such as ``data/splits`` for a symlink between its ``mkdir`` and the
    matching ``open`` and steer derived output into ``outputs/raw/``.
    """

    try:
        return compose_curated.write_pinned_new_bytes(
            root_descriptor, relative, payload, f"export {relative}"
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




def render_eval_protocol(provenance: dict[str, Any]) -> str:
    """Render the one-page evaluation protocol that ships with the split."""

    splits = provenance["splits"]
    audit = provenance["audit"]
    lines = [
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
        "## Losslessness",
        "",
        "`data/viewer/records.parquet` carries `{source_file, source_line,",
        "record_json}`. Concatenating a file's `record_json` rows in `source_line`",
        "order reproduces that curated JSONL byte for byte, so the viewer is a",
        "projection and never a second source of truth.",
        "",
    ]
    return "\n".join(lines)


def _validated_export_paths(
    curated_root: Path, destination: Path
) -> tuple[Path, Path, Path]:
    """Validate both trees and return (curated root, records dir, resolved root)."""

    curated_root = _require_exact_directory(curated_root, "curated root")
    records_dir = curated_root / compose_curated.RECORDS_DIRNAME
    try:
        records_dir = _require_exact_directory(records_dir, "curated records")
    except ExportError as exc:
        raise ExportError(
            f"curated root has no exact {compose_curated.RECORDS_DIRNAME}/ payload: "
            f"{curated_root}"
        ) from exc
    if os.path.lexists(destination):
        raise ExportError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ExportError(
            f"refusing to write inside immutable raw evidence: {destination}"
        )
    if not destination.parent.is_dir():
        raise ExportError(f"destination parent does not exist: {destination.parent}")
    _require_exact_directory(destination.parent, "destination parent")
    resolved_root = curated_root.resolve()
    resolved_destination = destination.resolve(strict=False)
    if resolved_root == resolved_destination or resolved_root in resolved_destination.parents:
        raise ExportError("destination cannot be written inside the curated root")
    return curated_root, records_dir, resolved_root


def _curated_snapshot(
    records_dir: Path,
) -> tuple[list[CuratedFile], list[ViewerRow], dict[str, bytes]]:
    """Collect the curated corpus once as (files, rows, exact byte snapshot)."""

    curated_files = collect_files(records_dir)
    rows = [row for curated in curated_files for row in curated.rows]
    if not rows:
        raise ExportError("refusing to export an empty curated corpus")
    snapshot: dict[str, bytes] = {}
    prefix = f"{CURATED_DIRNAME}/"
    for curated in curated_files:
        if not curated.source_file.startswith(prefix):
            raise ExportError(f"invalid curated source path: {curated.source_file}")
        relative = curated.source_file.removeprefix(prefix)
        if relative in snapshot:
            raise ExportError(f"duplicate curated snapshot path: {relative}")
        snapshot[relative] = curated.payload
    return curated_files, rows, snapshot


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
    destination_descriptor: int, curated_files: list[CuratedFile]
) -> list[dict[str, Any]]:
    """Copy every curated payload byte-identically into the destination."""

    files: list[dict[str, Any]] = []
    for curated in curated_files:
        digest = _write_new_bytes(
            destination_descriptor, curated.source_file, curated.payload
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
    destination_descriptor: int, rows: list[ViewerRow]
) -> str:
    """Write the viewer parquet only after it proves losslessly re-readable."""

    viewer_bytes = write_viewer_parquet(rows)
    round_trip = read_viewer_parquet(viewer_bytes)
    if round_trip != list(rows):
        raise ExportError("viewer projection failed its lossless round-trip check")
    return _write_new_bytes(destination_descriptor, VIEWER_PATH, viewer_bytes)


def export_run(
    curated_root: str | Path,
    destination: str | Path,
    *,
    eval_fraction: float = DEFAULT_EVAL_FRACTION,
    split_salt: str = DEFAULT_SPLIT_SALT,
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Export one composed curated tree, refusing anything not training-ready."""

    destination = Path(destination)
    curated_root, records_dir, resolved_root = _validated_export_paths(
        Path(curated_root), destination
    )

    curated_files, rows, snapshot = _curated_snapshot(records_dir)
    report, audit = _training_ready_audit(records_dir, snapshot)
    compose_metadata = _compose_metadata(curated_root, curated_files, report)

    train, evaluate = split_rows(rows, eval_fraction=eval_fraction, salt=split_salt)

    pinned_destination = _create_pinned_destination(resolved_root, destination)
    destination_descriptor = pinned_destination.destination_descriptor
    try:
        files = _write_curated_payloads(destination_descriptor, curated_files)
        viewer_digest = _write_viewer_projection(destination_descriptor, rows)

        train_digest = _write_new_bytes(
            destination_descriptor, TRAIN_PATH, _jsonl_payload(train)
        )
        eval_digest = _write_new_bytes(
            destination_descriptor, EVAL_PATH, _jsonl_payload(evaluate)
        )

        provenance = {
            "document_type": "curated_export_provenance",
            "export_name": EXPORT_NAME,
            "export_version": EXPORT_VERSION,
            "dataset_name": dataset_name,
            "curated_root": str(resolved_root),
            "compose": compose_metadata,
            "records": len(rows),
            "training_ready": audit["training_ready"],
            "audit": audit,
            "payload_published": False,
            "trainer_launched": False,
            "files": files,
            "viewer": {
                "path": VIEWER_PATH,
                "rows": len(rows),
                "columns": list(VIEWER_COLUMNS),
                "encoding": "PLAIN/uncompressed",
                "sha256": viewer_digest,
                "lossless": True,
            },
            "splits": {
                "policy": SPLIT_POLICY,
                "scope": "post_curation_snapshot_future_trainer_holdout",
                "eval_fraction": eval_fraction,
                "salt": split_salt,
                "train": {"path": TRAIN_PATH, "records": len(train), "sha256": train_digest},
                "eval": {"path": EVAL_PATH, "records": len(evaluate), "sha256": eval_digest},
                "train_records": len(train),
                "eval_records": len(evaluate),
                "protocol": PROTOCOL_PATH,
            },
        }
        protocol_digest = _write_new_bytes(
            destination_descriptor,
            PROTOCOL_PATH,
            render_eval_protocol(provenance).encode("utf-8"),
        )
        provenance["splits"]["protocol_sha256"] = protocol_digest
        _write_new_bytes(
            destination_descriptor,
            PROVENANCE_PATH,
            (json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
    except BaseException:
        pinned_destination.cleanup()
        raise
    _finish_pinned_destination(pinned_destination)
    return provenance


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
