"""Pin the refusal branches of the viewer Parquet codec and reader.

The reader authenticates one fixed-schema, uncompressed, PLAIN, single-page
projection and refuses everything else. A small test-side builder assembles
payloads that differ from the writer's layout in exactly one property so each
refusal is reached on its own; the messages are asserted verbatim.
"""

from __future__ import annotations

import struct
import sys
import unittest
from dataclasses import dataclass, replace
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import export_viewer
import export_viewer_codec as codec
import export_viewer_reader
from export_contract import ViewerRow
from refusal_case_support import RefusalCaseAssertions

_ROW = ViewerRow(source_file="a.jsonl", source_line=7, record_json='{"id":"r1"}')


def _byte_array(text: str) -> bytes:
    encoded = text.encode("utf-8")
    return len(encoded).to_bytes(4, "little") + encoded


@dataclass(frozen=True)
class _Column:
    name: str
    physical_type: int
    values: bytes
    path: tuple[str, ...] = ()


_DEFAULT_COLUMNS = (
    _Column("source_file", codec.TYPE_BYTE_ARRAY, _byte_array(_ROW.source_file)),
    _Column("source_line", codec.TYPE_INT64, _ROW.source_line.to_bytes(8, "little")),
    _Column("record_json", codec.TYPE_BYTE_ARRAY, _byte_array(_ROW.record_json)),
)


@dataclass(frozen=True)
class _Spec:
    """One viewer payload; each field defaults to what the writer emits."""

    columns: tuple[_Column, ...] = _DEFAULT_COLUMNS
    schema_names: tuple[str, ...] = ("source_file", "source_line", "record_json")
    rows: int = 1
    page_rows: int = 1
    page_type: int = codec.PAGE_TYPE_DATA_PAGE
    encoding: int = codec.ENCODING_PLAIN
    compression: int = codec.CODEC_UNCOMPRESSED


def _page(spec: _Spec, values: bytes) -> bytes:
    data_page = codec.struct_bytes(
        [
            (1, codec.I32, codec.integer(spec.page_rows)),
            (2, codec.I32, codec.integer(spec.encoding)),
        ]
    )
    header = codec.struct_bytes(
        [
            (1, codec.I32, codec.integer(spec.page_type)),
            (3, codec.I32, codec.integer(len(values))),
            (5, codec.STRUCT, data_page),
        ]
    )
    return header + values


def _chunk(spec: _Spec, column: _Column, offset: int) -> bytes:
    path = column.path or (column.name,)
    metadata = codec.struct_bytes(
        [
            (1, codec.I32, codec.integer(column.physical_type)),
            (3, codec.LIST, codec.list_bytes(codec.BINARY, [codec.string(p) for p in path])),
            (4, codec.I32, codec.integer(spec.compression)),
            (9, codec.I64, codec.integer(offset)),
        ]
    )
    return codec.struct_bytes([(3, codec.STRUCT, metadata)])


def _footer(spec: _Spec, chunks: list[bytes]) -> bytes:
    schema = [codec.struct_bytes([(4, codec.BINARY, codec.string("root"))])]
    schema += [codec.struct_bytes([(4, codec.BINARY, codec.string(n))]) for n in spec.schema_names]
    row_group = codec.struct_bytes(
        [
            (1, codec.LIST, codec.list_bytes(codec.STRUCT, chunks)),
            (3, codec.I64, codec.integer(spec.rows)),
        ]
    )
    return codec.struct_bytes(
        [
            (2, codec.LIST, codec.list_bytes(codec.STRUCT, schema)),
            (4, codec.LIST, codec.list_bytes(codec.STRUCT, [row_group])),
        ]
    )


def _payload(spec: _Spec) -> bytes:
    payload = bytearray(codec.PARQUET_MAGIC)
    chunks = []
    for column in spec.columns:
        chunks.append(_chunk(spec, column, len(payload)))
        payload += _page(spec, column.values)
    footer = _footer(spec, chunks)
    return bytes(payload + footer + len(footer).to_bytes(4, "little") + codec.PARQUET_MAGIC)


def _with_column(index: int, **changes) -> tuple[_Column, ...]:
    columns = list(_DEFAULT_COLUMNS)
    columns[index] = replace(columns[index], **changes)
    return tuple(columns)


def _with_footer_length(length: int) -> bytes:
    payload = export_viewer.write_viewer_parquet([_ROW])
    return payload[:-8] + length.to_bytes(4, "little") + codec.PARQUET_MAGIC


_READER_REFUSALS = (
    ("zero footer length", _with_footer_length(0), "Parquet footer length is invalid"),
    ("oversized footer length", _with_footer_length(1 << 30), "Parquet footer length is invalid"),
    (
        "renamed schema column",
        _payload(_Spec(schema_names=("source_file", "line", "record_json"))),
        "unexpected viewer columns: ['source_file', 'line', 'record_json']",
    ),
    (
        "compressed chunk",
        _payload(_Spec(compression=1)),
        "compressed Parquet chunks are not supported",
    ),
    (
        "nested column path",
        _payload(_Spec(columns=_with_column(0, path=("outer", "source_file")))),
        "nested Parquet columns are not supported",
    ),
    (
        "dictionary page",
        _payload(_Spec(page_type=2)),
        "only Parquet v1 data pages are supported",
    ),
    (
        "RLE-encoded page",
        _payload(_Spec(encoding=codec.ENCODING_RLE)),
        "only PLAIN-encoded Parquet pages are supported",
    ),
    (
        "page row count differs from the row group",
        _payload(_Spec(page_rows=2)),
        "Parquet column chunk must hold exactly one page",
    ),
    (
        "row group lacks a column",
        _payload(_Spec(columns=_DEFAULT_COLUMNS[:2])),
        "Parquet row group is missing columns: ['record_json']",
    ),
    (
        "INT32 physical type",
        _payload(_Spec(columns=_with_column(1, physical_type=1))),
        "unsupported Parquet physical type 1",
    ),
    (
        "byte-array length prefix cut short",
        _payload(_Spec(columns=_with_column(0, values=b"\x05\x00"))),
        codec.TRUNCATED_PARQUET_PAGE,
    ),
    (
        "byte-array value cut short",
        _payload(_Spec(columns=_with_column(0, values=b"\x05\x00\x00\x00ab"))),
        codec.TRUNCATED_PARQUET_PAGE,
    ),
    (
        "int64 value cut short",
        _payload(_Spec(columns=_with_column(1, values=b"\x07\x00\x00\x00"))),
        codec.TRUNCATED_PARQUET_PAGE,
    ),
)


class ViewerReaderRefusals(RefusalCaseAssertions, unittest.TestCase):
    def test_builder_matches_the_reader_contract(self):
        self.assertEqual(export_viewer_reader.read_viewer_parquet(_payload(_Spec())), [_ROW])

    def test_an_empty_row_group_decodes_to_no_rows(self):
        empty = _payload(_Spec(rows=0, page_rows=0))
        self.assertEqual(export_viewer_reader.read_viewer_parquet(empty), [])

    def test_payloads_outside_the_viewer_contract_are_refused(self):
        self.assert_each_refuses(
            ValueError, export_viewer_reader.read_viewer_parquet, _READER_REFUSALS
        )


def _struct_payload(field_type: int, payload: bytes) -> bytes:
    """One struct holding field 1 of ``field_type`` with a raw payload."""

    return bytes([(1 << 4) | field_type]) + payload + bytes([codec.STOP])


_DECODED_VALUES = (
    ("negative signed byte", _struct_payload(codec.BYTE, b"\xff"), {1: -1}),
    ("positive signed byte", _struct_payload(codec.BYTE, b"\x05"), {1: 5}),
    ("boolean true", _struct_payload(codec.TRUE, b""), {1: True}),
    ("boolean false", _struct_payload(codec.FALSE, b""), {1: False}),
    ("double", _struct_payload(codec.DOUBLE, struct.pack("<d", 1.5)), {1: 1.5}),
    ("empty map", _struct_payload(codec.MAP, codec.uvarint(0)), {1: {}}),
    (
        "binary-to-i32 map",
        _struct_payload(
            codec.MAP,
            codec.uvarint(1)
            + bytes([(codec.BINARY << 4) | codec.I32])
            + codec.string("k")
            + codec.integer(-3),
        ),
        {1: {b"k": -3}},
    ),
    (
        "long-form field id",
        codec.struct_bytes([(20, codec.I32, codec.integer(7))]),
        {20: 7},
    ),
    (
        "descending field ids",
        codec.struct_bytes([(5, codec.I32, codec.integer(1)), (3, codec.I32, codec.integer(2))]),
        {5: 1, 3: 2},
    ),
    (
        "long-form list header",
        codec.struct_bytes(
            [(1, codec.LIST, codec.list_bytes(codec.I32, [codec.integer(n) for n in range(15)]))]
        ),
        {1: list(range(15))},
    ),
)

_DECODER_REFUSALS = (
    ("truncated metadata", b"\x15", "Parquet metadata is truncated"),
    (
        "oversized varint",
        _struct_payload(codec.I32, b"\xff" * 10),
        "Parquet metadata contains an oversized varint",
    ),
    ("unknown field type", _struct_payload(13, b""), "unsupported Thrift field type 13"),
)


def _decode_struct(payload: bytes) -> dict:
    return codec.CompactDecoder(payload).read_struct()


_OUT_OF_RANGE = "integer out of Thrift 64-bit range: "


class CompactCodecBranches(RefusalCaseAssertions, unittest.TestCase):
    def test_encoders_refuse_values_outside_their_ranges(self):
        self.assert_each_refuses(
            ValueError,
            codec.uvarint,
            (("negative varint", -1, "unsigned varint cannot encode a negative value"),),
        )
        self.assert_each_refuses(
            ValueError,
            codec.zigzag,
            (
                ("above int64", 2**63, f"{_OUT_OF_RANGE}{2**63}"),
                ("below int64", -(2**63) - 1, f"{_OUT_OF_RANGE}{-(2**63) - 1}"),
            ),
        )

    def test_decoder_reads_every_supported_field_shape(self):
        for label, payload, expected in _DECODED_VALUES:
            with self.subTest(label):
                self.assertEqual(_decode_struct(payload), expected)

    def test_decoder_refuses_malformed_metadata(self):
        self.assert_each_refuses(ValueError, _decode_struct, _DECODER_REFUSALS)


if __name__ == "__main__":
    unittest.main()
