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
import stat
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402

EXPORT_NAME = "export_hf"
EXPORT_VERSION = "export-hf-v3"
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
    "deterministic snapshot split: sha256(salt|source_file|source_line) maps each "
    "row to [0,1); rows below eval_fraction are eval, every factory with at least "
    "two rows contributes to both sides, and a global hash-order fallback keeps "
    "every corpus of at least two records two-sided"
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


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def _loads_json(payload: str, label: str) -> Any:
    try:
        return json.loads(payload, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ExportError(f"{label}: invalid JSON: {exc}") from exc


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
    for path in sorted(records_dir.rglob("*.jsonl")):
        relative = path.relative_to(records_dir).as_posix()
        exact_path, payload = _read_exact_regular_file(
            records_dir, relative, f"curated payload {relative}"
        )
        files.append(_read_curated_file(exact_path, relative, payload=payload))
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
    """Partition one immutable snapshot deterministically, with two-sided fallback."""

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
    for factory in sorted(by_factory):
        group = by_factory[factory]
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

    globally_ordered = sorted(
        ((split_bucket(row, salt), row) for row in rows),
        key=lambda item: (item[0], item[1].source_file, item[1].source_line),
    )
    if not evaluation:
        _bucket, row = globally_ordered[0]
        evaluation.add((row.source_file, row.source_line))
    elif len(evaluation) == len(rows):
        _bucket, row = globally_ordered[-1]
        evaluation.remove((row.source_file, row.source_line))

    train = [row for row in rows if (row.source_file, row.source_line) not in evaluation]
    evaluate = [row for row in rows if (row.source_file, row.source_line) in evaluation]
    if not train or not evaluate:  # defensive: len(rows) >= 2 makes this unreachable
        raise ExportError("deterministic fallback failed to produce both split sides")
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


def _contains_raw_segments(parts: tuple[str, ...]) -> bool:
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _is_under_raw(path: Path) -> bool:
    """Reject both a lexical raw path and a symlink-resolved raw destination."""

    return _contains_raw_segments(path.parts) or _contains_raw_segments(
        path.resolve(strict=False).parts
    )


def _compose_member_path(curated_root: Path, raw_path: Any, label: str) -> Path:
    """Resolve one exact regular COMPOSE member without aliases or tree escape."""

    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        raise ExportError(f"{label}: path must be a nonempty POSIX string")
    relative = PurePosixPath(raw_path)
    if (
        relative.as_posix() != raw_path
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ExportError(f"{label}: unsafe relative path {raw_path!r}")
    candidate = curated_root.joinpath(*relative.parts)
    try:
        root_resolved = curated_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    expected = root_resolved.joinpath(*relative.parts)
    if resolved != expected or root_resolved not in resolved.parents:
        raise ExportError(f"{label}: path is a symlink alias or escapes its root: {raw_path}")
    try:
        metadata = candidate.lstat()
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: declared file is missing: {raw_path}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ExportError(f"{label}: path is not an exact regular file: {raw_path}")
    if metadata.st_nlink != 1:
        raise ExportError(f"{label}: hard-link aliases are not accepted: {raw_path}")
    return candidate


def _read_exact_regular_file(root: Path, raw_path: Any, label: str) -> tuple[Path, bytes]:
    """Read one path through a pinned descriptor and reject identity changes."""

    path = _compose_member_path(root, raw_path, label)
    before = path.lstat()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ExportError(f"{label}: cannot open exact regular file {raw_path!r}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise ExportError(f"{label}: opened identity is not a unique regular file")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ExportError(f"{label}: path identity changed while opening")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino):
        raise ExportError(f"{label}: path identity changed while reading")
    if path.resolve(strict=True) != root.resolve(strict=True).joinpath(
        *PurePosixPath(str(raw_path)).parts
    ):
        raise ExportError(f"{label}: path became a symlink alias while reading")
    return path, b"".join(chunks)


def _lf_jsonl_documents(payload: bytes, label: str) -> list[Any]:
    """Parse JSONL with LF as the only record separator."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{label}: payload is not UTF-8: {exc}") from exc
    if text and not text.endswith("\n"):
        raise ExportError(f"{label}: JSONL must end with a newline")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    documents: list[Any] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            raise ExportError(f"{label}:{line_number}: JSONL has a blank line")
        documents.append(_loads_json(line, f"{label}:{line_number}"))
    return documents


def _authenticated_descriptor(
    curated_root: Path,
    summary: dict[str, Any],
    key: str,
    expected_path: str,
) -> tuple[dict[str, Any], list[Any]]:
    descriptor = summary.get(key)
    if not isinstance(descriptor, dict):
        raise ExportError(f"COMPOSE.json: {key} descriptor must be an object")
    if descriptor.get("path") != expected_path:
        raise ExportError(
            f"COMPOSE.json: {key} path must be {expected_path!r}, "
            f"got {descriptor.get('path')!r}"
        )
    _path, payload = _read_exact_regular_file(
        curated_root, descriptor["path"], f"COMPOSE {key}"
    )
    digest = hashlib.sha256(payload).hexdigest()
    if descriptor.get("sha256") != digest:
        raise ExportError(f"COMPOSE.json: {key} digest mismatch")
    documents = _lf_jsonl_documents(payload, descriptor["path"])
    entries = descriptor.get("entries")
    if isinstance(entries, bool) or not isinstance(entries, int) or entries < 0:
        raise ExportError(f"COMPOSE.json: {key}.entries must be nonnegative")
    if entries != len(documents):
        raise ExportError(
            f"COMPOSE.json: {key} entry count {entries} != {len(documents)}"
        )
    return dict(descriptor), documents


def _require_exact_directory(path: Path, label: str) -> Path:
    """Require a real directory reached without a symlinked path alias."""

    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ExportError(f"{label}: directory is missing: {path}") from exc
    absolute = Path(os.path.abspath(path))
    if not stat.S_ISDIR(metadata.st_mode) or resolved != absolute:
        raise ExportError(f"{label}: directory path must be an exact non-symlink identity")
    return resolved


def _create_pinned_destination(
    curated_root: Path, destination: Path
) -> compose_curated._PinnedDestination:
    """Create the export directory through the same parent pin compose uses."""

    try:
        return compose_curated._create_pinned_destination(curated_root, destination)
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _finish_pinned_destination(pinned: compose_curated._PinnedDestination) -> None:
    try:
        pinned.finish()
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _load_calibration_payload(payload: bytes, path: Path) -> dict[str, Any]:
    """Load reward calibration from pinned bytes while preserving evidence labels."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"calibration {path}: payload is not UTF-8: {exc}") from exc
    document = _loads_json(text, f"calibration {path}")
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise ExportError(f"calibration {path}: records must be a list")

    catalog: dict[str, Any] = {}
    for index, entry in enumerate(records):
        if not isinstance(entry, dict):
            continue
        factor = curate_rewards._decimal(entry.get("usd_conversion_factor"))
        if factor is None or factor <= 0:
            continue
        scope = entry.get("scope")
        if not isinstance(scope, str):
            continue
        for record_id in sorted(set(curate_rewards.RECORD_ID_RE.findall(scope))):
            calibration = {
                "source_unit_usd": curate_rewards._json_number(
                    factor * curate_rewards.CANONICAL_UNIT_USD
                ),
                "canonical_factor": curate_rewards._json_number(factor),
                "evidence_ref": f"{path.as_posix()}#/records/{index}",
            }
            key = record_id.lower()
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise ExportError(
                    f"calibration {path}: conflicting calibrations for {record_id}"
                )
            catalog[key] = calibration
    return catalog


def _authenticated_calibration(
    summary: dict[str, Any], source_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    descriptor = summary.get("calibration")
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "mode",
        "path",
        "sha256",
        "records",
    }:
        raise ExportError("COMPOSE.json: calibration descriptor is incomplete")
    mode = descriptor.get("mode")
    records = descriptor.get("records")
    if isinstance(records, bool) or not isinstance(records, int) or records < 0:
        raise ExportError("COMPOSE.json: calibration.records must be nonnegative")
    if mode == "none":
        if descriptor.get("path") is not None or descriptor.get("sha256") is not None:
            raise ExportError("COMPOSE.json: absent calibration must not name a file")
        catalog: dict[str, Any] = {}
    elif mode in {"source_run", "explicit"}:
        raw_path = descriptor.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ExportError("COMPOSE.json: calibration.path must be an absolute string")
        path = Path(raw_path)
        if not path.is_absolute():
            raise ExportError("COMPOSE.json: calibration.path must be absolute")
        if mode == "source_run" and path != source_root / compose_curated.FFPC_UNITS_MIGRATION:
            raise ExportError("COMPOSE.json: source-run calibration path is not canonical")
        _path, payload = _read_exact_regular_file(
            path.parent, path.name, "COMPOSE calibration"
        )
        digest = hashlib.sha256(payload).hexdigest()
        if descriptor.get("sha256") != digest:
            raise ExportError("COMPOSE.json: calibration digest mismatch")
        catalog = _load_calibration_payload(payload, path)
    else:
        raise ExportError(f"COMPOSE.json: unsupported calibration mode {mode!r}")
    if len(catalog) != records or summary.get("calibrated_records") != records:
        raise ExportError("COMPOSE.json: calibrated record count does not authenticate")
    return catalog, dict(descriptor)


@dataclass(frozen=True)
class _ReplaySnapshot:
    """Everything replaying the source lines accumulates for authentication.

    ``expected_*`` are what the compose lanes deterministically produce from
    the current source snapshot; the caller compares them against the
    already-published manifest, sidecars, and outputs.
    """

    counts: Counter[str]
    exclusions: Counter[str]
    lane_actions: dict[str, Counter[str]]
    expected_manifest: list[dict[str, Any]]
    expected_sidecars: list[dict[str, Any]]
    expected_outputs: list[dict[str, Any]]
    expected_payloads: dict[str, bytes]
    source_files: list[dict[str, Any]]


def _replay_source_lines(source_root: Path, catalog: Any) -> _ReplaySnapshot:
    """Run every source JSONL line back through compose and record what it yields."""

    counts: Counter[str] = Counter()
    exclusions: Counter[str] = Counter()
    lane_actions: dict[str, Counter[str]] = {
        lane: Counter() for lane in compose_curated.LANE_ORDER
    }
    expected_manifest: list[dict[str, Any]] = []
    expected_sidecars: list[dict[str, Any]] = []
    expected_outputs: list[dict[str, Any]] = []
    expected_payloads: dict[str, bytes] = {}
    emitted_ids: dict[str, str] = {}
    source_files: list[dict[str, Any]] = []
    seen_source_semantics: dict[str, tuple[str, int]] = {}
    seen_curated_semantics: dict[str, tuple[str, int]] = {}

    try:
        source_members = compose_curated.source_jsonl_members(source_root)
    except compose_curated.ComposeError as exc:
        raise ExportError(f"COMPOSE source tree cannot be replayed safely: {exc}") from exc
    for relative in source_members:
        _path, raw_file = _read_exact_regular_file(
            source_root, relative, f"compose source {relative}"
        )
        source_file_sha256 = hashlib.sha256(raw_file).hexdigest()
        source_files.append(
            {
                "path": relative,
                "bytes": len(raw_file),
                "sha256": source_file_sha256,
            }
        )
        counts["source_files"] += 1
        emitted: list[str] = []

        physical_lines = raw_file.split(b"\n")
        if physical_lines and physical_lines[-1] == b"":
            physical_lines.pop()
        for line_number, physical_line in enumerate(physical_lines, 1):
            if not physical_line.strip():
                counts["blank_lines"] += 1
                continue
            counts["source_records"] += 1
            source_sha256 = hashlib.sha256(physical_line).hexdigest()
            decision = compose_curated.compose_source_line(
                physical_line,
                source_path=relative,
                source_line=line_number,
                source_file_sha256=source_file_sha256,
                calibration_catalog=catalog,
                seen_source_semantics=seen_source_semantics,
                seen_curated_semantics=seen_curated_semantics,
            )
            entry: dict[str, Any] = {
                "compose_name": compose_curated.COMPOSE_NAME,
                "compose_version": compose_curated.COMPOSE_VERSION,
                "lane_order": list(compose_curated.LANE_ORDER),
                "source_path": relative,
                "source_line": line_number,
                "source_sha256": source_sha256,
                "source_file_sha256": source_file_sha256,
                "action": decision.action,
                "reason_codes": list(decision.reason_codes),
                "stages": [dict(stage) for stage in decision.stages],
            }
            for stage in decision.stages:
                lane = stage["lane"]
                if lane in lane_actions:
                    lane_actions[lane][stage["action"]] += 1

            if (
                decision.action == compose_curated.ACTION_RETAINED
                and decision.record is not None
            ):
                line = compose_curated.canonical_json(decision.record)
                output_id = decision.output_id
                if output_id is not None:
                    previous = emitted_ids.get(output_id)
                    if previous is not None:
                        raise ExportError(
                            f"replayed canonical ID collision {output_id!r}: "
                            f"{previous} and {relative}:{line_number}"
                        )
                    emitted_ids[output_id] = f"{relative}:{line_number}"
                emitted.append(line)
                entry.update(
                    {
                        "output_path": f"{compose_curated.RECORDS_DIRNAME}/{relative}",
                        "output_line": len(emitted),
                        "output_id": output_id,
                        "output_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                    }
                )
                counts["retained"] += 1
                if decision.reward_sidecar is not None:
                    entry["reward_sidecar_id"] = decision.reward_sidecar["sidecar_id"]
                    expected_sidecars.append(decision.reward_sidecar)
            else:
                entry.update(
                    {
                        "output_path": None,
                        "output_line": None,
                        "output_id": None,
                        "output_sha256": None,
                    }
                )
                counts["excluded"] += 1
                for reason in decision.reason_codes or ("compose.unspecified",):
                    exclusions[reason] += 1
            expected_manifest.append(entry)

        if emitted:
            output_path = f"{compose_curated.RECORDS_DIRNAME}/{relative}"
            payload = "".join(line + "\n" for line in emitted).encode("utf-8")
            expected_payloads[output_path] = payload
            expected_outputs.append(
                {
                    "path": output_path,
                    "records": len(emitted),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
            counts["output_files"] += 1

    counts["reward_sidecars"] = len(expected_sidecars)
    return _ReplaySnapshot(
        counts=counts,
        exclusions=exclusions,
        lane_actions=lane_actions,
        expected_manifest=expected_manifest,
        expected_sidecars=expected_sidecars,
        expected_outputs=expected_outputs,
        expected_payloads=expected_payloads,
        source_files=source_files,
    )


def _verify_replay_matches(
    snapshot: _ReplaySnapshot,
    *,
    summary: dict[str, Any],
    actual_outputs: dict[str, CuratedFile],
    manifest_documents: Sequence[Any],
    sidecar_documents: Sequence[Any],
) -> None:
    """Raise ``ExportError`` unless every declared artifact reproduces from ``snapshot``."""

    if list(manifest_documents) != snapshot.expected_manifest:
        raise ExportError(
            "compose manifest does not reproduce from the authenticated current source snapshot"
        )
    if list(sidecar_documents) != snapshot.expected_sidecars:
        raise ExportError(
            "reward sidecars do not reproduce from the authenticated current source snapshot"
        )
    if summary.get("outputs") != snapshot.expected_outputs:
        raise ExportError("COMPOSE.json: output declarations do not reproduce from source")
    if set(actual_outputs) != set(snapshot.expected_payloads):
        raise ExportError("curated output paths do not reproduce from the source snapshot")
    for output_path, payload in snapshot.expected_payloads.items():
        if actual_outputs[output_path].payload != payload:
            raise ExportError(f"curated output bytes do not reproduce: {output_path}")

    expected_counts = {
        "source_files": snapshot.counts["source_files"],
        "source_records": snapshot.counts["source_records"],
        "blank_lines": snapshot.counts["blank_lines"],
        "retained": snapshot.counts["retained"],
        "excluded": snapshot.counts["excluded"],
        "output_files": snapshot.counts["output_files"],
        "reward_sidecars": snapshot.counts["reward_sidecars"],
    }
    if summary.get("counts") != expected_counts:
        raise ExportError("COMPOSE.json: source/output counts do not reproduce")
    expected_lane_actions = {
        lane: dict(sorted(actions.items()))
        for lane, actions in snapshot.lane_actions.items()
    }
    if summary.get("lane_actions") != expected_lane_actions:
        raise ExportError("COMPOSE.json: lane action counts do not reproduce")
    if summary.get("exclusions") != dict(sorted(snapshot.exclusions.items())):
        raise ExportError("COMPOSE.json: exclusions do not reproduce")
    if summary.get("transforms") != compose_curated.transform_contract():
        raise ExportError("COMPOSE.json: transform declarations do not match this contract")


def _authenticate_source_replay(
    curated_root: Path,
    summary: dict[str, Any],
    actual_outputs: dict[str, CuratedFile],
    manifest_documents: Sequence[Any],
    sidecar_documents: Sequence[Any],
) -> dict[str, Any]:
    """Replay current source bytes and authenticate the complete compose mapping.

    This proves that the currently available source snapshot deterministically
    produces the declared outputs.  It deliberately does not claim that the
    source directory was immutable between the original compose and this replay.
    """

    raw_source_root = summary.get("source_run")
    if not isinstance(raw_source_root, str) or not Path(raw_source_root).is_absolute():
        raise ExportError("COMPOSE.json: source_run must be an absolute directory string")
    source_root = _require_exact_directory(Path(raw_source_root), "COMPOSE source_run")
    if raw_source_root != str(source_root):
        raise ExportError("COMPOSE.json: source_run must use its exact canonical path")
    catalog, calibration_descriptor = _authenticated_calibration(summary, source_root)

    snapshot = _replay_source_lines(source_root, catalog)
    _verify_replay_matches(
        snapshot,
        summary=summary,
        actual_outputs=actual_outputs,
        manifest_documents=manifest_documents,
        sidecar_documents=sidecar_documents,
    )

    snapshot_digest = hashlib.sha256(
        compose_curated.canonical_json(snapshot.source_files).encode("utf-8")
    ).hexdigest()
    return {
        "path": str(source_root),
        "authentication_scope": "current_source_snapshot_replayed",
        "historical_immutability_proven": False,
        "files": snapshot.counts["source_files"],
        "records": snapshot.counts["source_records"],
        "blank_lines": snapshot.counts["blank_lines"],
        "snapshot_index_sha256": snapshot_digest,
        "calibration": calibration_descriptor,
    }


def _compose_metadata(
    curated_root: Path,
    curated_files: Sequence[CuratedFile],
    audit_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Authenticate COMPOSE paths, bytes, coordinates, and reward links."""

    summary_path, summary_payload = _read_exact_regular_file(
        curated_root,
        compose_curated.SUMMARY_FILENAME,
        "COMPOSE summary",
    )
    try:
        summary_text = summary_payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{summary_path}: compose summary is not UTF-8: {exc}") from exc
    summary = _loads_json(summary_text, str(summary_path))
    if not isinstance(summary, dict):
        raise ExportError(f"{summary_path}: compose summary must be an object")

    if summary.get("compose_name") != compose_curated.COMPOSE_NAME:
        raise ExportError("COMPOSE.json: unexpected compose_name")
    if summary.get("compose_version") != compose_curated.COMPOSE_VERSION:
        raise ExportError(
            "COMPOSE.json: compose_version does not match this export contract"
        )
    if summary.get("lane_order") != list(compose_curated.LANE_ORDER):
        raise ExportError("COMPOSE.json: lane_order does not match the compose contract")
    if summary.get("destination") != str(curated_root.resolve()):
        raise ExportError("COMPOSE.json: destination does not name this curated root")

    actual_outputs: dict[str, CuratedFile] = {}
    for curated in curated_files:
        prefix = f"{CURATED_DIRNAME}/"
        if not curated.source_file.startswith(prefix):
            raise ExportError(f"invalid curated source path: {curated.source_file}")
        compose_path = (
            f"{compose_curated.RECORDS_DIRNAME}/"
            f"{curated.source_file.removeprefix(prefix)}"
        )
        actual_outputs[compose_path] = curated

    declared_outputs = summary.get("outputs")
    if not isinstance(declared_outputs, list):
        raise ExportError("COMPOSE.json: outputs must be a list")
    authenticated_outputs: list[dict[str, Any]] = []
    seen_output_paths: set[str] = set()
    for index, entry in enumerate(declared_outputs):
        if not isinstance(entry, dict):
            raise ExportError(f"COMPOSE.json: outputs[{index}] must be an object")
        raw_path = entry.get("path")
        _path, current_payload = _read_exact_regular_file(
            curated_root, raw_path, f"COMPOSE outputs[{index}]"
        )
        if raw_path in seen_output_paths:
            raise ExportError(f"COMPOSE.json: duplicate output path {raw_path!r}")
        seen_output_paths.add(raw_path)
        curated = actual_outputs.get(raw_path)
        if curated is None:
            raise ExportError(f"COMPOSE.json: undeclared or non-payload output {raw_path!r}")
        if current_payload != curated.payload:
            raise ExportError(
                f"COMPOSE.json: output identity changed after snapshot capture: {raw_path}"
            )
        # Bind the descriptor to the same immutable snapshot already parsed
        # into ``curated`` and later written to the export, avoiding a second
        # file read with different bytes under a concurrent source mutation.
        digest = hashlib.sha256(curated.payload).hexdigest()
        if entry.get("sha256") != digest:
            raise ExportError(f"COMPOSE.json: output digest mismatch for {raw_path}")
        records = entry.get("records")
        if isinstance(records, bool) or not isinstance(records, int) or records < 1:
            raise ExportError(f"COMPOSE.json: invalid record count for {raw_path}")
        if records != len(curated.rows):
            raise ExportError(
                f"COMPOSE.json: output record count mismatch for {raw_path}"
            )
        authenticated_outputs.append(
            {"path": raw_path, "records": records, "sha256": digest}
        )
    if seen_output_paths != set(actual_outputs):
        missing = sorted(set(actual_outputs) - seen_output_paths)
        raise ExportError(f"COMPOSE.json: payload outputs missing from summary: {missing}")

    manifest, manifest_documents = _authenticated_descriptor(
        curated_root,
        summary,
        "manifest",
        f"{compose_curated.MANIFEST_DIRNAME}/{compose_curated.MANIFEST_FILENAME}",
    )
    reward_sidecars, sidecar_documents = _authenticated_descriptor(
        curated_root,
        summary,
        "reward_sidecars",
        (
            f"{compose_curated.MANIFEST_DIRNAME}/"
            f"{compose_curated.REWARD_SIDECAR_FILENAME}"
        ),
    )

    sidecars_by_id: dict[str, dict[str, Any]] = {}
    for index, document in enumerate(sidecar_documents):
        try:
            curate_rewards.validate_ontology_document(document)
        except curate_rewards.RewardOntologyError as exc:
            raise ExportError(f"reward sidecar {index + 1} is invalid: {exc}") from exc
        sidecar_id = document["sidecar_id"]
        if sidecar_id in sidecars_by_id:
            raise ExportError(f"duplicate reward sidecar id {sidecar_id}")
        sidecars_by_id[sidecar_id] = document

    expected_coordinates = {
        (path, row.source_line)
        for path, curated in actual_outputs.items()
        for row in curated.rows
    }
    manifest_coordinates: set[tuple[str, int]] = set()
    referenced_sidecars: set[str] = set()
    for index, entry in enumerate(manifest_documents):
        if not isinstance(entry, dict):
            raise ExportError(f"compose manifest entry {index + 1} must be an object")
        if entry.get("compose_name") != compose_curated.COMPOSE_NAME:
            raise ExportError(
                f"compose manifest entry {index + 1} has an unexpected compose_name"
            )
        if entry.get("compose_version") != compose_curated.COMPOSE_VERSION:
            raise ExportError(
                f"compose manifest entry {index + 1} has an unexpected compose_version"
            )
        if entry.get("lane_order") != list(compose_curated.LANE_ORDER):
            raise ExportError(
                f"compose manifest entry {index + 1} has an unexpected lane_order"
            )
        if entry.get("action") != compose_curated.ACTION_RETAINED:
            if any(
                entry.get(field) is not None
                for field in (
                    "output_path",
                    "output_line",
                    "output_id",
                    "output_sha256",
                    "reward_sidecar_id",
                )
            ):
                raise ExportError(
                    f"compose manifest entry {index + 1} gives an excluded row output"
                )
            continue
        output_path = entry.get("output_path")
        output_line = entry.get("output_line")
        if (
            not isinstance(output_path, str)
            or isinstance(output_line, bool)
            or not isinstance(output_line, int)
        ):
            raise ExportError(
                f"compose manifest entry {index + 1} has an invalid output coordinate"
            )
        coordinate = (output_path, output_line)
        if coordinate in manifest_coordinates:
            raise ExportError(f"duplicate compose manifest coordinate {coordinate}")
        manifest_coordinates.add(coordinate)
        curated = actual_outputs.get(output_path)
        if curated is None or not 1 <= output_line <= len(curated.rows):
            raise ExportError(f"compose manifest coordinate does not resolve: {coordinate}")
        row = curated.rows[output_line - 1]
        digest = hashlib.sha256(row.record_json.encode("utf-8")).hexdigest()
        if entry.get("output_sha256") != digest:
            raise ExportError(f"compose manifest output digest mismatch: {coordinate}")
        record = _loads_json(row.record_json, f"compose output {coordinate}")
        output_id = record.get("id") if isinstance(record, dict) else None
        if not isinstance(output_id, str) or entry.get("output_id") != output_id:
            raise ExportError(f"compose manifest output id mismatch: {coordinate}")
        sidecar_id = entry.get("reward_sidecar_id")
        if sidecar_id is not None:
            if not isinstance(sidecar_id, str):
                raise ExportError(
                    f"compose manifest entry {index + 1} has an invalid reward sidecar id"
                )
            if sidecar_id not in sidecars_by_id:
                raise ExportError(
                    f"compose manifest references missing reward sidecar {sidecar_id}"
                )
            sidecar_source = sidecars_by_id[sidecar_id]["source"]
            if (
                sidecar_source.get("path") != entry.get("source_path")
                or sidecar_source.get("line") != entry.get("source_line")
            ):
                raise ExportError(
                    f"compose manifest and reward sidecar source disagree: {coordinate}"
                )
            try:
                curate_rewards.restore_source_record(
                    record, sidecars_by_id[sidecar_id]
                )
            except curate_rewards.RewardOntologyError as exc:
                raise ExportError(
                    f"compose output {coordinate} does not authenticate its reward "
                    f"sidecar: {exc}"
                ) from exc
            referenced_sidecars.add(sidecar_id)
        elif (
            isinstance(record, dict)
            and curate_rewards.ANNOTATION_FIELD in record
        ):
            raise ExportError(
                f"compose output {coordinate} has an unmanifested reward annotation"
            )

    if manifest_coordinates != expected_coordinates:
        missing = sorted(expected_coordinates - manifest_coordinates)
        extra = sorted(manifest_coordinates - expected_coordinates)
        raise ExportError(
            f"compose manifest/output coordinate mismatch; missing={missing}, extra={extra}"
        )
    if referenced_sidecars != set(sidecars_by_id):
        raise ExportError("compose manifest and reward sidecar sets do not match")

    counts = summary.get("counts")
    if not isinstance(counts, dict):
        raise ExportError("COMPOSE.json: counts must be an object")
    expected_counts = {
        "source_records": len(manifest_documents),
        "retained": len(expected_coordinates),
        "excluded": len(manifest_documents) - len(expected_coordinates),
        "output_files": len(actual_outputs),
        "reward_sidecars": len(sidecar_documents),
    }
    for key, expected in expected_counts.items():
        value = counts.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise ExportError(
                f"COMPOSE.json: counts.{key} {value!r} != {expected}"
            )

    source_snapshot = _authenticate_source_replay(
        curated_root,
        summary,
        actual_outputs,
        manifest_documents,
        sidecar_documents,
    )
    expected_audit = compose_curated.compact_audit_report(
        audit_report, len(expected_coordinates)
    )
    if summary.get("audit") != expected_audit:
        raise ExportError("COMPOSE.json: audit declaration does not match exported bytes")

    return {
        "present": True,
        "summary": {
            "path": compose_curated.SUMMARY_FILENAME,
            "sha256": hashlib.sha256(summary_payload).hexdigest(),
        },
        "compose_version": summary.get("compose_version"),
        "lane_order": summary.get("lane_order"),
        "transforms": compose_curated.transform_contract(),
        "source": source_snapshot,
        "outputs": authenticated_outputs,
        "manifest": manifest,
        "reward_sidecars": reward_sidecars,
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
        "   `meta.factory` value carried in each split record.",
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
    compose_metadata = _compose_metadata(curated_root, curated_files, report)

    train, evaluate = split_rows(rows, eval_fraction=eval_fraction, salt=split_salt)

    pinned_destination = _create_pinned_destination(resolved_root, destination)
    destination_root = pinned_destination.root
    try:
        files: list[dict[str, Any]] = []
        for curated in curated_files:
            digest = _write_new_bytes(destination_root / curated.source_file, curated.payload)
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
        viewer_digest = _write_new_bytes(destination_root / VIEWER_PATH, viewer_bytes)

        train_digest = _write_new_bytes(destination_root / TRAIN_PATH, _jsonl_payload(train))
        eval_digest = _write_new_bytes(destination_root / EVAL_PATH, _jsonl_payload(evaluate))

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
            destination_root / PROTOCOL_PATH, render_eval_protocol(provenance).encode("utf-8")
        )
        provenance["splits"]["protocol_sha256"] = protocol_digest
        _write_new_bytes(
            destination_root / PROVENANCE_PATH,
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
