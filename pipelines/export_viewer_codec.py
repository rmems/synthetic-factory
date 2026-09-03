#!/usr/bin/env python3
"""Thrift compact-protocol and Parquet primitives shared by the viewer codec.

Split out of ``export_viewer.py`` by responsibility: the constants, the
compact-protocol encoders, and the generic decoder that both the lossless
viewer writer and reader build on. The Parquet payload itself is assembled
in ``export_viewer_writer`` and authenticated in ``export_viewer_reader``.
"""

from __future__ import annotations

import struct
import sys
from typing import Any, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_viewer_codec")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_viewer_codec"
    )

# ── Thrift compact protocol ───────

STOP = 0
BYTE = 3
I16 = 4
I32 = 5
I64 = 6
DOUBLE = 7
BINARY = 8
LIST = 9
SET = 10
MAP = 11
STRUCT = 12
TRUE = 1
FALSE = 2

# Parquet enums (parquet.thrift).
TYPE_INT64 = 2
TYPE_BYTE_ARRAY = 6
REPETITION_REQUIRED = 0
CONVERTED_UTF8 = 0
ENCODING_PLAIN = 0
ENCODING_RLE = 3
CODEC_UNCOMPRESSED = 0
PAGE_TYPE_DATA_PAGE = 0
PARQUET_MAGIC = b"PAR1"
TRUNCATED_PARQUET_PAGE = "Parquet page is truncated"


def uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("unsigned varint cannot encode a negative value")
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def zigzag(value: int) -> int:
    if not -(2**63) <= value < 2**63:
        raise ValueError(f"integer out of Thrift 64-bit range: {value}")
    return (value << 1) ^ (value >> 63)


def integer(value: int) -> bytes:
    return uvarint(zigzag(value))


def binary(data: bytes) -> bytes:
    return uvarint(len(data)) + data


def string(value: str) -> bytes:
    return binary(value.encode("utf-8"))


def struct_bytes(fields: Sequence[tuple[int, int, bytes]]) -> bytes:
    out = bytearray()
    previous = 0
    for field_id, field_type, payload in fields:
        delta = field_id - previous
        if 0 < delta <= 15:
            out.append((delta << 4) | field_type)
        else:
            out.append(field_type)
            out += integer(field_id)
        out += payload
        previous = field_id
    out.append(STOP)
    return bytes(out)


def list_bytes(item_type: int, items: Sequence[bytes]) -> bytes:
    out = bytearray()
    if len(items) <= 14:
        out.append((len(items) << 4) | item_type)
    else:
        out.append(0xF0 | item_type)
        out += uvarint(len(items))
    for item in items:
        out += item
    return bytes(out)


class CompactDecoder:
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
            TRUE: self._true_value,
            FALSE: self._false_value,
            BYTE: self._signed_byte,
            I16: self._integer,
            I32: self._integer,
            I64: self._integer,
            DOUBLE: self._double_value,
            BINARY: self._binary_value,
            LIST: self._sequence_value,
            SET: self._sequence_value,
            MAP: self._mapping_value,
            STRUCT: self.read_struct,
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
            if header == STOP:
                return fields
            field_type = header & 0x0F
            delta = header >> 4
            field_id = previous + delta if delta else self._integer()
            fields[field_id] = self._value(field_type)
            previous = field_id


if __package__:
    _expose_package_sibling(__name__)
