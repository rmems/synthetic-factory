#!/usr/bin/env python3
"""Lossless viewer projection: minimal PLAIN Parquet writer and reader.

Split out of ``export_hf.py`` by responsibility. The writer emits
uncompressed PLAIN Parquet with the standard library only, and the reader
proves the projection is lossless by rebuilding the exact rows.
"""

from __future__ import annotations

import struct
import sys
from typing import Any, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_viewer")
    from . import export_contract as _export_contract
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_viewer"
    )
    import export_contract as _export_contract

CREATED_BY = _export_contract.CREATED_BY
VIEWER_COLUMNS = _export_contract.VIEWER_COLUMNS
ExportError = _export_contract.ExportError
ViewerRow = _export_contract.ViewerRow

_WRITER_CREATED_BY = CREATED_BY
_READER_VIEWER_COLUMNS = VIEWER_COLUMNS

if __package__:
    from . import export_viewer_reader as _reader
    from . import export_viewer_writer as _writer
else:
    import export_viewer_reader as _reader
    import export_viewer_writer as _writer

# ── Thrift compact protocol ───────

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
_TRUNCATED_PARQUET_PAGE = "Parquet page is truncated"


def _uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned varint cannot encode a negative value")
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
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

    def _signed_byte(self) -> int:
        byte = self._byte()
        return byte - 256 if byte > 127 else byte

    def _sequence_value(self) -> list[Any]:
        header = self._byte()
        size = header >> 4
        item_type = header & 0x0F
        if size == 15:
            size = self._uvarint()
        return [self._value(item_type) for _ in range(size)]

    def _mapping_value(self) -> dict[Any, Any]:
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

    @staticmethod
    def _true_value() -> bool:
        return True

    @staticmethod
    def _false_value() -> bool:
        return False

    def _double_value(self) -> float:
        return struct.unpack("<d", self._read(8))[0]

    def _binary_value(self) -> bytes:
        return self._read(self._uvarint())

    def _value(self, field_type: int) -> Any:
        readers = {
            _TRUE: self._true_value,
            _FALSE: self._false_value,
            _BYTE: self._signed_byte,
            _I16: self._integer,
            _I32: self._integer,
            _I64: self._integer,
            _DOUBLE: self._double_value,
            _BINARY: self._binary_value,
            _LIST: self._sequence_value,
            _SET: self._sequence_value,
            _MAP: self._mapping_value,
            _STRUCT: self.read_struct,
        }
        try:
            reader = readers[field_type]
        except KeyError as exc:
            raise ValueError(f"unsupported Thrift field type {field_type}") from exc
        return reader()

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


# ── Minimal Parquet writer / reader ───────


def write_viewer_parquet(rows: Sequence[ViewerRow]) -> bytes:
    """Return an uncompressed PLAIN Parquet file for the viewer projection."""

    if not rows:
        raise ExportError("refusing to write a Parquet file with no rows")
    return _writer.write_viewer_parquet(rows, sys.modules[__name__])


def read_viewer_parquet(payload: bytes) -> list[ViewerRow]:
    """Read back a viewer projection written by :func:`write_viewer_parquet`."""

    return _reader.read_viewer_parquet(payload, sys.modules[__name__])


if __package__:
    _expose_package_sibling(__name__)
