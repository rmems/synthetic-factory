#!/usr/bin/env python3
"""Lossless viewer projection: minimal PLAIN Parquet writer and reader.

Split out of ``export_hf.py`` by responsibility. The writer emits
uncompressed PLAIN Parquet with the standard library only, and the reader
proves the projection is lossless by rebuilding the exact rows.
"""

from __future__ import annotations

import struct
from typing import Any, Iterable, Sequence

from export_contract import CREATED_BY, VIEWER_COLUMNS, ExportError, ViewerRow

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

    def _value(self, field_type: int) -> Any:
        if field_type == _TRUE:
            return True
        if field_type == _FALSE:
            return False
        if field_type == _BYTE:
            return self._signed_byte()
        if field_type in {_I16, _I32, _I64}:
            return self._integer()
        if field_type == _DOUBLE:
            return struct.unpack("<d", self._read(8))[0]
        if field_type == _BINARY:
            return self._read(self._uvarint())
        if field_type in {_LIST, _SET}:
            return self._sequence_value()
        if field_type == _MAP:
            return self._mapping_value()
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


# ── Minimal Parquet writer / reader ───────


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


def _decode_byte_array_at(data: bytes, offset: int) -> tuple[str, int]:
    """Decode one length-prefixed UTF-8 value, returning it and the next offset."""

    if offset + 4 > len(data):
        raise ValueError("Parquet page is truncated")
    length = int.from_bytes(data[offset : offset + 4], "little")
    offset += 4
    if offset + length > len(data):
        raise ValueError("Parquet page is truncated")
    return data[offset : offset + length].decode("utf-8"), offset + length


def _decode_int64_at(data: bytes, offset: int) -> tuple[int, int]:
    """Decode one little-endian signed 64-bit value and the next offset."""

    if offset + 8 > len(data):
        raise ValueError("Parquet page is truncated")
    value = int.from_bytes(data[offset : offset + 8], "little", signed=True)
    return value, offset + 8


_PLAIN_DECODERS = {
    _TYPE_BYTE_ARRAY: _decode_byte_array_at,
    _TYPE_INT64: _decode_int64_at,
}


def _decode_plain(physical_type: int, data: bytes, num_values: int) -> list[Any]:
    decode_at = _PLAIN_DECODERS.get(physical_type)
    # An empty page never reached a per-value decode, so it is only the
    # first requested value that rejects an unsupported physical type.
    if num_values and decode_at is None:
        raise ValueError(f"unsupported Parquet physical type {physical_type}")
    values: list[Any] = []
    offset = 0
    for _ in range(num_values):
        value, offset = decode_at(data, offset)
        values.append(value)
    return values


def _viewer_footer_metadata(payload: bytes) -> dict[int, Any]:
    """Validate the Parquet envelope and decode its footer metadata struct."""

    if len(payload) < 12 or not payload.startswith(_PARQUET_MAGIC):
        raise ValueError("not a Parquet file")
    if not payload.endswith(_PARQUET_MAGIC):
        raise ValueError("Parquet footer magic is missing")
    footer_size = int.from_bytes(payload[-8:-4], "little")
    if footer_size <= 0 or footer_size > len(payload) - 8:
        raise ValueError("Parquet footer length is invalid")
    footer_start = len(payload) - 8 - footer_size
    return _CompactDecoder(payload, footer_start).read_struct()


def _require_viewer_columns(metadata: dict[int, Any]) -> None:
    """Require the schema to declare exactly the viewer projection columns."""

    schema = metadata.get(2) or []
    names = [
        element.get(4, b"").decode("utf-8")
        for element in schema[1:]
        if isinstance(element, dict)
    ]
    if names != list(VIEWER_COLUMNS):
        raise ValueError(f"unexpected viewer columns: {names}")


def _decode_column_chunk(
    payload: bytes, chunk: dict[int, Any], num_rows: int
) -> tuple[str, list[Any]]:
    """Decode one single-page PLAIN column chunk into (column name, values)."""

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
    return path[0], _decode_plain(meta.get(1), page, page_values)


def _row_group_rows(payload: bytes, row_group: dict[int, Any]) -> list[ViewerRow]:
    """Decode one row group into viewer rows, requiring every column."""

    num_rows = row_group.get(3, 0)
    column_values: dict[str, list[Any]] = {}
    for chunk in row_group.get(1) or []:
        name, values = _decode_column_chunk(payload, chunk, num_rows)
        column_values[name] = values
    missing = set(VIEWER_COLUMNS) - set(column_values)
    if missing:
        raise ValueError(f"Parquet row group is missing columns: {sorted(missing)}")
    return [
        ViewerRow(
            source_file=column_values["source_file"][index],
            source_line=column_values["source_line"][index],
            record_json=column_values["record_json"][index],
        )
        for index in range(num_rows)
    ]


def read_viewer_parquet(payload: bytes) -> list[ViewerRow]:
    """Read back a viewer projection written by :func:`write_viewer_parquet`."""

    metadata = _viewer_footer_metadata(payload)
    _require_viewer_columns(metadata)
    rows: list[ViewerRow] = []
    for row_group in metadata.get(4) or []:
        rows.extend(_row_group_rows(payload, row_group))
    return rows
