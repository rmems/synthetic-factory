#!/usr/bin/env python3
"""Focused stdlib-only Parquet writer for the lossless viewer projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class _EncodedColumn:
    name: str
    physical_type: int
    values: bytes


class _ParquetWriter:
    """Assemble one immutable three-column PLAIN Parquet payload."""

    def __init__(self, rows: Sequence[Any], codec: Any):
        self.rows = rows
        self.codec = codec
        self.payload = bytearray(codec._PARQUET_MAGIC)

    @staticmethod
    def _plain_byte_array(values: Iterable[str]) -> bytes:
        output = bytearray()
        for value in values:
            encoded = value.encode("utf-8")
            output += len(encoded).to_bytes(4, "little")
            output += encoded
        return bytes(output)

    @staticmethod
    def _plain_int64(values: Iterable[int]) -> bytes:
        output = bytearray()
        for value in values:
            output += int(value).to_bytes(8, "little", signed=True)
        return bytes(output)

    def _columns(self) -> tuple[_EncodedColumn, ...]:
        return (
            _EncodedColumn(
                "source_file",
                self.codec._TYPE_BYTE_ARRAY,
                self._plain_byte_array(row.source_file for row in self.rows),
            ),
            _EncodedColumn(
                "source_line",
                self.codec._TYPE_INT64,
                self._plain_int64(row.source_line for row in self.rows),
            ),
            _EncodedColumn(
                "record_json",
                self.codec._TYPE_BYTE_ARRAY,
                self._plain_byte_array(row.record_json for row in self.rows),
            ),
        )

    def _schema_element(self, name: str, physical_type: int, *, utf8: bool) -> bytes:
        fields = [
            (1, self.codec._I32, self.codec._integer(physical_type)),
            (3, self.codec._I32, self.codec._integer(self.codec._REPETITION_REQUIRED)),
            (4, self.codec._BINARY, self.codec._string(name)),
        ]
        if utf8:
            fields.append((6, self.codec._I32, self.codec._integer(self.codec._CONVERTED_UTF8)))
            logical_type = self.codec._struct_bytes(
                [(1, self.codec._STRUCT, self.codec._struct_bytes([]))]
            )
            fields.append((10, self.codec._STRUCT, logical_type))
        return self.codec._struct_bytes(fields)

    def _data_page_header(self, page_size: int) -> bytes:
        data_page = self.codec._struct_bytes(
            [
                (1, self.codec._I32, self.codec._integer(len(self.rows))),
                (2, self.codec._I32, self.codec._integer(self.codec._ENCODING_PLAIN)),
                (3, self.codec._I32, self.codec._integer(self.codec._ENCODING_RLE)),
                (4, self.codec._I32, self.codec._integer(self.codec._ENCODING_RLE)),
            ]
        )
        return self.codec._struct_bytes(
            [
                (1, self.codec._I32, self.codec._integer(self.codec._PAGE_TYPE_DATA_PAGE)),
                (2, self.codec._I32, self.codec._integer(page_size)),
                (3, self.codec._I32, self.codec._integer(page_size)),
                (5, self.codec._STRUCT, data_page),
            ]
        )

    def _append_column(self, column: _EncodedColumn) -> tuple[bytes, int]:
        header = self._data_page_header(len(column.values))
        offset = len(self.payload)
        self.payload += header
        self.payload += column.values
        chunk_size = len(header) + len(column.values)
        metadata = self.codec._struct_bytes(
            [
                (1, self.codec._I32, self.codec._integer(column.physical_type)),
                (
                    2,
                    self.codec._LIST,
                    self.codec._list_bytes(
                        self.codec._I32,
                        [self.codec._integer(self.codec._ENCODING_PLAIN)],
                    ),
                ),
                (
                    3,
                    self.codec._LIST,
                    self.codec._list_bytes(
                        self.codec._BINARY,
                        [self.codec._string(column.name)],
                    ),
                ),
                (4, self.codec._I32, self.codec._integer(self.codec._CODEC_UNCOMPRESSED)),
                (5, self.codec._I64, self.codec._integer(len(self.rows))),
                (6, self.codec._I64, self.codec._integer(chunk_size)),
                (7, self.codec._I64, self.codec._integer(chunk_size)),
                (9, self.codec._I64, self.codec._integer(offset)),
            ]
        )
        chunk = self.codec._struct_bytes(
            [
                (2, self.codec._I64, self.codec._integer(offset)),
                (3, self.codec._STRUCT, metadata),
            ]
        )
        return chunk, chunk_size

    def _schema(self, column_count: int) -> list[bytes]:
        return [
            self.codec._struct_bytes(
                [
                    (
                        4,
                        self.codec._BINARY,
                        self.codec._string("spikenaut_curated_records"),
                    ),
                    (5, self.codec._I32, self.codec._integer(column_count)),
                ]
            ),
            self._schema_element("source_file", self.codec._TYPE_BYTE_ARRAY, utf8=True),
            self._schema_element("source_line", self.codec._TYPE_INT64, utf8=False),
            self._schema_element("record_json", self.codec._TYPE_BYTE_ARRAY, utf8=True),
        ]

    def _footer(
        self, columns: Sequence[_EncodedColumn], chunks: list[bytes], total_size: int
    ) -> bytes:
        row_group = self.codec._struct_bytes(
            [
                (
                    1,
                    self.codec._LIST,
                    self.codec._list_bytes(self.codec._STRUCT, chunks),
                ),
                (2, self.codec._I64, self.codec._integer(total_size)),
                (3, self.codec._I64, self.codec._integer(len(self.rows))),
            ]
        )
        return self.codec._struct_bytes(
            [
                (1, self.codec._I32, self.codec._integer(1)),
                (
                    2,
                    self.codec._LIST,
                    self.codec._list_bytes(
                        self.codec._STRUCT,
                        self._schema(len(columns)),
                    ),
                ),
                (3, self.codec._I64, self.codec._integer(len(self.rows))),
                (
                    4,
                    self.codec._LIST,
                    self.codec._list_bytes(self.codec._STRUCT, [row_group]),
                ),
                (
                    6,
                    self.codec._BINARY,
                    self.codec._string(self.codec._WRITER_CREATED_BY),
                ),
            ]
        )

    def write(self) -> bytes:
        columns = self._columns()
        chunks: list[bytes] = []
        total_size = 0
        for column in columns:
            chunk, chunk_size = self._append_column(column)
            chunks.append(chunk)
            total_size += chunk_size
        footer = self._footer(columns, chunks, total_size)
        self.payload += footer
        self.payload += len(footer).to_bytes(4, "little")
        self.payload += self.codec._PARQUET_MAGIC
        return bytes(self.payload)


def write_viewer_parquet(rows: Sequence[Any], codec: Any) -> bytes:
    """Return an uncompressed PLAIN Parquet file using ``codec`` primitives."""

    if not rows:
        raise codec.ExportError("refusing to write a Parquet file with no rows")
    return _ParquetWriter(rows, codec).write()
