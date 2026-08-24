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
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import training_audit  # noqa: E402

EXPORT_NAME = "export_hf"
EXPORT_VERSION = "export-hf-v1"
CREATED_BY = f"synthetic-factory {EXPORT_NAME} ({EXPORT_VERSION})"

CURATED_DIRNAME = "data/curated"
VIEWER_PATH = "data/viewer/records.parquet"
TRAIN_PATH = "data/splits/train.jsonl"
EVAL_PATH = "data/splits/eval.jsonl"
PROVENANCE_PATH = "provenance.json"
PROTOCOL_PATH = "EVAL_PROTOCOL.md"

VIEWER_COLUMNS = ("source_file", "source_line", "record_json")
DEFAULT_EVAL_FRACTION = 0.1
DEFAULT_SPLIT_SALT = "spikenaut.synthetic-factory.split-v1"
SPLIT_POLICY = (
    "sha256(salt|source_file|source_line) mapped to [0,1); a row is eval when "
    "its value is below eval_fraction. Every factory with at least two rows "
    "contributes at least one row to each split."
)

# Thrift compact protocol field types.
_STOP = 0
_BYTE = 3
_I16 = 4
_I32 = 5
_I64 = 6
_DOUBLE = 7
_BINARY = 8
_LIST = 9
_SET = 10
_MAP = 11
_STRUCT = 12
_TRUE = 1
_FALSE = 2

# Parquet enums (parquet.thrift).
_TYPE_INT64 = 2
_TYPE_BYTE_ARRAY = 6
_REPETITION_REQUIRED = 0
_CONVERTED_UTF8 = 0
_ENCODING_PLAIN = 0
_ENCODING_RLE = 3
_CODEC_UNCOMPRESSED = 0
_PAGE_TYPE_DATA_PAGE = 0
_PARQUET_MAGIC = b"PAR1"


class ExportError(RuntimeError):
    """Raised when the export input, gate, or destination is unsafe."""


@dataclass(frozen=True)
class ViewerRow:
    """One lossless viewer row: the exact curated line and its coordinate."""

    source_file: str
    source_line: int
    record_json: str


@dataclass(frozen=True)
class CuratedFile:
    """One curated JSONL file, its exact bytes, and its viewer rows."""

    source_file: str
    payload: bytes
    rows: tuple[ViewerRow, ...]


# ── Thrift compact protocol ───────────────────────────────────────────


def _uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned varint cannot encode a negative value")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _zigzag(value: int) -> int:
    if not -(2**63) <= value < 2**63:
        raise ValueError(f"integer out of Thrift 64-bit range: {value}")
    return (value << 1) ^ (value >> 63)


def _integer(value: int) -> bytes:
    return _uvarint(_zigzag(value))


def _binary(data: bytes) -> bytes:
    return _uvarint(len(data)) + data


def _string(value: str) -> bytes:
    return _binary(value.encode("utf-8"))


def _struct_bytes(fields: Sequence[tuple[int, int, bytes]]) -> bytes:
    out = bytearray()
    previous = 0
    for field_id, field_type, payload in fields:
        delta = field_id - previous
        if 0 < delta <= 15:
            out.append((delta << 4) | field_type)
        else:
            out.append(field_type)
            out += _integer(field_id)
        out += payload
        previous = field_id
    out.append(_STOP)
    return bytes(out)


def _list_bytes(item_type: int, items: Sequence[bytes]) -> bytes:
    out = bytearray()
    if len(items) <= 14:
        out.append((len(items) << 4) | item_type)
    else:
        out.append(0xF0 | item_type)
        out += _uvarint(len(items))
    for item in items:
        out += item
    return bytes(out)


class _CompactDecoder:
    """Generic Thrift compact decoder for the metadata this module writes."""

    def __init__(self, data: bytes, offset: int = 0) -> None:
        self.data = data
        self.offset = offset

    def _read(self, count: int) -> bytes:
        end = self.offset + count
        if end > len(self.data):
            raise ValueError("Parquet metadata is truncated")
        chunk = self.data[self.offset : end]
        self.offset = end
        return chunk

    def _byte(self) -> int:
        return self._read(1)[0]

    def _uvarint(self) -> int:
        value = 0
        shift = 0
        while True:
            byte = self._byte()
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return value
            shift += 7
            if shift > 63:
                raise ValueError("Parquet metadata contains an oversized varint")

    def _integer(self) -> int:
        raw = self._uvarint()
        return (raw >> 1) ^ -(raw & 1)

    def _value(self, field_type: int) -> Any:
        if field_type == _TRUE:
            return True
        if field_type == _FALSE:
            return False
        if field_type == _BYTE:
            byte = self._byte()
            return byte - 256 if byte > 127 else byte
        if field_type in {_I16, _I32, _I64}:
            return self._integer()
        if field_type == _DOUBLE:
            return struct.unpack("<d", self._read(8))[0]
        if field_type == _BINARY:
            return self._read(self._uvarint())
        if field_type in {_LIST, _SET}:
            header = self._byte()
            size = header >> 4
            item_type = header & 0x0F
            if size == 15:
                size = self._uvarint()
            return [self._value(item_type) for _ in range(size)]
        if field_type == _MAP:
            size = self._uvarint()
            if not size:
                return {}
            types = self._byte()
            key_type = types >> 4
            value_type = types & 0x0F
            mapping: dict[Any, Any] = {}
            for _ in range(size):
                # Read key then value explicitly; comprehension evaluation order
                # is not part of the wire contract.
                key = self._value(key_type)
                mapping[key] = self._value(value_type)
            return mapping
        if field_type == _STRUCT:
            return self.read_struct()
        raise ValueError(f"unsupported Thrift field type {field_type}")

    def read_struct(self) -> dict[int, Any]:
        fields: dict[int, Any] = {}
        previous = 0
        while True:
            header = self._byte()
            if header == _STOP:
                return fields
            field_type = header & 0x0F
            delta = header >> 4
            field_id = previous + delta if delta else self._integer()
            fields[field_id] = self._value(field_type)
            previous = field_id


# ── Minimal Parquet writer / reader ───────────────────────────────────


def _plain_byte_array(values: Iterable[str]) -> bytes:
    out = bytearray()
    for value in values:
        encoded = value.encode("utf-8")
        out += len(encoded).to_bytes(4, "little")
        out += encoded
    return bytes(out)


def _plain_int64(values: Iterable[int]) -> bytes:
    out = bytearray()
    for value in values:
        out += int(value).to_bytes(8, "little", signed=True)
    return bytes(out)


def _schema_element(name: str, physical_type: int, *, utf8: bool) -> bytes:
    fields: list[tuple[int, int, bytes]] = [
        (1, _I32, _integer(physical_type)),
        (3, _I32, _integer(_REPETITION_REQUIRED)),
        (4, _BINARY, _string(name)),
    ]
    if utf8:
        fields.append((6, _I32, _integer(_CONVERTED_UTF8)))
        # LogicalType union with StringType selected.
        fields.append((10, _STRUCT, _struct_bytes([(1, _STRUCT, _struct_bytes([]))])))
    return _struct_bytes(fields)


def _data_page_header(num_values: int, page_size: int) -> bytes:
    data_page = _struct_bytes(
        [
            (1, _I32, _integer(num_values)),
            (2, _I32, _integer(_ENCODING_PLAIN)),
            (3, _I32, _integer(_ENCODING_RLE)),
            (4, _I32, _integer(_ENCODING_RLE)),
        ]
    )
    return _struct_bytes(
        [
            (1, _I32, _integer(_PAGE_TYPE_DATA_PAGE)),
            (2, _I32, _integer(page_size)),
            (3, _I32, _integer(page_size)),
            (5, _STRUCT, data_page),
        ]
    )


def write_viewer_parquet(rows: Sequence[ViewerRow]) -> bytes:
    """Return an uncompressed PLAIN Parquet file for the viewer projection."""

    if not rows:
        raise ExportError("refusing to write a Parquet file with no rows")
    columns = (
        ("source_file", _TYPE_BYTE_ARRAY, _plain_byte_array(row.source_file for row in rows)),
        ("source_line", _TYPE_INT64, _plain_int64(row.source_line for row in rows)),
        ("record_json", _TYPE_BYTE_ARRAY, _plain_byte_array(row.record_json for row in rows)),
    )

    payload = bytearray(_PARQUET_MAGIC)
    chunks: list[bytes] = []
    total_byte_size = 0
    for name, physical_type, values in columns:
        header = _data_page_header(len(rows), len(values))
        offset = len(payload)
        payload += header
        payload += values
        chunk_size = len(header) + len(values)
        total_byte_size += chunk_size
        meta = _struct_bytes(
            [
                (1, _I32, _integer(physical_type)),
                (2, _LIST, _list_bytes(_I32, [_integer(_ENCODING_PLAIN)])),
                (3, _LIST, _list_bytes(_BINARY, [_string(name)])),
                (4, _I32, _integer(_CODEC_UNCOMPRESSED)),
                (5, _I64, _integer(len(rows))),
                (6, _I64, _integer(chunk_size)),
                (7, _I64, _integer(chunk_size)),
                (9, _I64, _integer(offset)),
            ]
        )
        chunks.append(
            _struct_bytes([(2, _I64, _integer(offset)), (3, _STRUCT, meta)])
        )

    row_group = _struct_bytes(
        [
            (1, _LIST, _list_bytes(_STRUCT, chunks)),
            (2, _I64, _integer(total_byte_size)),
            (3, _I64, _integer(len(rows))),
        ]
    )
    schema = [
        _struct_bytes(
            [(4, _BINARY, _string("spikenaut_curated_records")), (5, _I32, _integer(len(columns)))]
        ),
        _schema_element("source_file", _TYPE_BYTE_ARRAY, utf8=True),
        _schema_element("source_line", _TYPE_INT64, utf8=False),
        _schema_element("record_json", _TYPE_BYTE_ARRAY, utf8=True),
    ]
    footer = _struct_bytes(
        [
            (1, _I32, _integer(1)),
            (2, _LIST, _list_bytes(_STRUCT, schema)),
            (3, _I64, _integer(len(rows))),
            (4, _LIST, _list_bytes(_STRUCT, [row_group])),
            (6, _BINARY, _string(CREATED_BY)),
        ]
    )
    payload += footer
    payload += len(footer).to_bytes(4, "little")
    payload += _PARQUET_MAGIC
    return bytes(payload)


def _decode_plain(physical_type: int, data: bytes, num_values: int) -> list[Any]:
    values: list[Any] = []
    offset = 0
    for _ in range(num_values):
        if physical_type == _TYPE_BYTE_ARRAY:
            if offset + 4 > len(data):
                raise ValueError("Parquet page is truncated")
            length = int.from_bytes(data[offset : offset + 4], "little")
            offset += 4
            if offset + length > len(data):
                raise ValueError("Parquet page is truncated")
            values.append(data[offset : offset + length].decode("utf-8"))
            offset += length
        elif physical_type == _TYPE_INT64:
            if offset + 8 > len(data):
                raise ValueError("Parquet page is truncated")
            values.append(int.from_bytes(data[offset : offset + 8], "little", signed=True))
            offset += 8
        else:
            raise ValueError(f"unsupported Parquet physical type {physical_type}")
    return values


def read_viewer_parquet(payload: bytes) -> list[ViewerRow]:
    """Read back a viewer projection written by :func:`write_viewer_parquet`."""

    if len(payload) < 12 or not payload.startswith(_PARQUET_MAGIC):
        raise ValueError("not a Parquet file")
    if not payload.endswith(_PARQUET_MAGIC):
        raise ValueError("Parquet footer magic is missing")
    footer_size = int.from_bytes(payload[-8:-4], "little")
    if footer_size <= 0 or footer_size > len(payload) - 8:
        raise ValueError("Parquet footer length is invalid")
    footer_start = len(payload) - 8 - footer_size
    metadata = _CompactDecoder(payload, footer_start).read_struct()

    schema = metadata.get(2) or []
    names = [
        element.get(4, b"").decode("utf-8")
        for element in schema[1:]
        if isinstance(element, dict)
    ]
    if names != list(VIEWER_COLUMNS):
        raise ValueError(f"unexpected viewer columns: {names}")

    rows: list[ViewerRow] = []
    for row_group in metadata.get(4) or []:
        num_rows = row_group.get(3, 0)
        column_values: dict[str, list[Any]] = {}
        for chunk in row_group.get(1) or []:
            meta = chunk.get(3) or {}
            if meta.get(4, _CODEC_UNCOMPRESSED) != _CODEC_UNCOMPRESSED:
                raise ValueError("compressed Parquet chunks are not supported")
            path = [item.decode("utf-8") for item in meta.get(3) or []]
            if len(path) != 1:
                raise ValueError("nested Parquet columns are not supported")
            decoder = _CompactDecoder(payload, meta.get(9, 0))
            page_header = decoder.read_struct()
            if page_header.get(1) != _PAGE_TYPE_DATA_PAGE:
                raise ValueError("only Parquet v1 data pages are supported")
            data_page = page_header.get(5) or {}
            if data_page.get(2) != _ENCODING_PLAIN:
                raise ValueError("only PLAIN-encoded Parquet pages are supported")
            page_values = data_page.get(1, 0)
            if page_values != num_rows:
                raise ValueError("Parquet column chunk must hold exactly one page")
            page_size = page_header.get(3, 0)
            page = payload[decoder.offset : decoder.offset + page_size]
            column_values[path[0]] = _decode_plain(meta.get(1), page, page_values)
        missing = set(VIEWER_COLUMNS) - set(column_values)
        if missing:
            raise ValueError(f"Parquet row group is missing columns: {sorted(missing)}")
        for index in range(num_rows):
            rows.append(
                ViewerRow(
                    source_file=column_values["source_file"][index],
                    source_line=column_values["source_line"][index],
                    record_json=column_values["record_json"][index],
                )
            )
    return rows


# ── Export ────────────────────────────────────────────────────────────


def _read_curated_file(path: Path, relative: str) -> CuratedFile:
    """Read one curated JSONL file and prove its lines reproduce its bytes."""

    source_file = f"{CURATED_DIRNAME}/{relative}"
    payload = path.read_bytes()
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
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExportError(
                f"{relative}:{line_number}: curated line is not JSON: {exc}"
            ) from exc
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
    for path in sorted(records_dir.rglob("*.jsonl")):
        if not path.is_file():
            continue
        files.append(_read_curated_file(path, path.relative_to(records_dir).as_posix()))
    return files


def collect_rows(records_dir: Path) -> list[ViewerRow]:
    """Read every curated JSONL line in stable path and line order."""

    return [row for curated in collect_files(records_dir) for row in curated.rows]


def split_bucket(row: ViewerRow, salt: str) -> float:
    """Map a row to a stable [0,1) bucket that does not depend on ordering."""

    digest = hashlib.sha256(
        f"{salt}|{row.source_file}|{row.source_line}".encode("utf-8")
    ).hexdigest()
    return int(digest[:8], 16) / 2**32


def split_rows(
    rows: Sequence[ViewerRow], *, eval_fraction: float, salt: str
) -> tuple[list[ViewerRow], list[ViewerRow]]:
    """Partition rows into train and eval deterministically, per factory."""

    if not 0 < eval_fraction < 1:
        raise ExportError("eval_fraction must be between 0 and 1 exclusive")
    if len(rows) < 2:
        raise ExportError("refusing to split a corpus with fewer than two records")

    by_factory: dict[str, list[tuple[float, ViewerRow]]] = {}
    for row in rows:
        parts = row.source_file.split("/")
        factory = parts[2] if len(parts) > 3 else parts[-1]
        by_factory.setdefault(factory, []).append((split_bucket(row, salt), row))

    evaluation: set[tuple[str, int]] = set()
    for group in by_factory.values():
        ordered = sorted(
            group,
            key=lambda item: (item[0], item[1].source_file, item[1].source_line),
        )
        chosen = [item for item in ordered if item[0] < eval_fraction]
        if len(ordered) >= 2:
            if not chosen:
                chosen = ordered[:1]
            elif len(chosen) == len(ordered):
                chosen = ordered[:-1]
        evaluation.update((row.source_file, row.source_line) for _bucket, row in chosen)

    train = [row for row in rows if (row.source_file, row.source_line) not in evaluation]
    evaluate = [row for row in rows if (row.source_file, row.source_line) in evaluation]
    if not train or not evaluate:
        raise ExportError("split produced an empty train or eval file")
    return train, evaluate


def _write_new_bytes(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return hashlib.sha256(payload).hexdigest()


def _jsonl_payload(rows: Sequence[ViewerRow]) -> bytes:
    return "".join(row.record_json + "\n" for row in rows).encode("utf-8")


def _compose_metadata(curated_root: Path) -> dict[str, Any]:
    summary_path = curated_root / compose_curated.SUMMARY_FILENAME
    if not summary_path.is_file():
        return {"present": False}
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"{summary_path}: invalid compose summary: {exc}") from exc
    if not isinstance(summary, dict):
        raise ExportError(f"{summary_path}: compose summary must be an object")
    return {
        "present": True,
        "compose_version": summary.get("compose_version"),
        "lane_order": summary.get("lane_order"),
        "transforms": summary.get("transforms"),
        "source_run": summary.get("source_run"),
        "manifest": summary.get("manifest"),
    }


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
        "A tiny held-out split over one curated, audited corpus. It exists so a",
        "future training run has a fixed evaluation set that was never touched by",
        "curation tuning. **No trainer is launched from this repository.** These",
        "files are inputs for a separate, explicitly approved training decision.",
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
        "- The rule is a pure function of `(salt, source_file, source_line)`, so",
        "  re-exporting the same corpus reproduces the same split, and appending",
        "  new records never reshuffles the existing ones.",
        "",
        "## How to evaluate",
        "",
        "1. Train only on `data/splits/train.jsonl`. Never fit on the eval file.",
        "2. Score `data/splits/eval.jsonl` record by record, grouped by factory",
        "   (the path segment after `data/curated/` in `source_file`).",
        "3. Report per-record-kind metrics separately; the corpus mixes Thalamic",
        "   trajectories, bridge pairs, preference pairs, and coding episodes, and",
        "   a single averaged number hides a collapsed lane.",
        "4. Suggested per-kind measures:",
        "   - Thalamic: safety-gate decision agreement and reward-sign agreement.",
        "   - Bridge: event-order fidelity of the generated language view.",
        "   - Preference: chosen-vs-rejected ranking accuracy on same-context pairs.",
        "   - Coding: step-level `decision_basis` groundedness in visible evidence.",
        "5. Reward magnitudes are only comparable where `reward_training.comparability`",
        "   is `magnitude_comparable`; otherwise compare sign and order only.",
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


def export_run(
    curated_root: str | Path,
    destination: str | Path,
    *,
    eval_fraction: float = DEFAULT_EVAL_FRACTION,
    split_salt: str = DEFAULT_SPLIT_SALT,
    dataset_name: str | None = None,
) -> dict[str, Any]:
    """Export one composed curated tree, refusing anything not training-ready."""

    curated_root = Path(curated_root)
    destination = Path(destination)
    records_dir = curated_root / compose_curated.RECORDS_DIRNAME
    if not records_dir.is_dir():
        raise ExportError(
            f"curated root has no {compose_curated.RECORDS_DIRNAME}/ payload: {curated_root}"
        )
    if destination.exists():
        raise ExportError(f"refusing to overwrite an existing destination: {destination}")
    if not destination.parent.is_dir():
        raise ExportError(f"destination parent does not exist: {destination.parent}")
    resolved_root = curated_root.resolve()
    resolved_destination = destination.resolve(strict=False)
    if resolved_root == resolved_destination or resolved_root in resolved_destination.parents:
        raise ExportError("destination cannot be written inside the curated root")

    compose_metadata = _compose_metadata(curated_root)
    curated_files = collect_files(records_dir)
    rows = [row for curated in curated_files for row in curated.rows]
    if not rows:
        raise ExportError("refusing to export an empty curated corpus")

    report = training_audit.audit_run(records_dir)
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

    train, evaluate = split_rows(rows, eval_fraction=eval_fraction, salt=split_salt)

    destination.mkdir(parents=True)
    try:
        files: list[dict[str, Any]] = []
        for curated in curated_files:
            digest = _write_new_bytes(destination / curated.source_file, curated.payload)
            files.append(
                {
                    "path": curated.source_file,
                    "records": len(curated.rows),
                    "sha256": digest,
                }
            )

        viewer_bytes = write_viewer_parquet(rows)
        round_trip = read_viewer_parquet(viewer_bytes)
        if round_trip != list(rows):
            raise ExportError("viewer projection failed its lossless round-trip check")
        viewer_digest = _write_new_bytes(destination / VIEWER_PATH, viewer_bytes)

        train_digest = _write_new_bytes(destination / TRAIN_PATH, _jsonl_payload(train))
        eval_digest = _write_new_bytes(destination / EVAL_PATH, _jsonl_payload(evaluate))

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
            destination / PROTOCOL_PATH, render_eval_protocol(provenance).encode("utf-8")
        )
        provenance["splits"]["protocol_sha256"] = protocol_digest
        _write_new_bytes(
            destination / PROVENANCE_PATH,
            (json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
    except BaseException:
        # The destination was brand new and created here, so a failed export
        # leaves nothing half-written behind.
        shutil.rmtree(destination, ignore_errors=True)
        raise
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
