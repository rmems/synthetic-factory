#!/usr/bin/env python3
"""Focused stdlib-only Parquet writer for the lossless viewer projection."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any, Iterable, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_viewer_writer")
    from . import export_viewer_codec as codec
    from .export_contract import CREATED_BY, ExportError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_viewer_writer"
    )
    import export_viewer_codec as codec
    from export_contract import CREATED_BY, ExportError


@dataclass(frozen=True)
class _EncodedColumn:
    name: str
    physical_type: int
    values: bytes


class _ParquetWriter:
    """Assemble one immutable three-column PLAIN Parquet payload."""

    def __init__(self, rows: Sequence[Any]):
        self.rows = rows
        self.payload = bytearray(codec.PARQUET_MAGIC)

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
                codec.TYPE_BYTE_ARRAY,
                self._plain_byte_array(row.source_file for row in self.rows),
            ),
            _EncodedColumn(
                "source_line",
                codec.TYPE_INT64,
                self._plain_int64(row.source_line for row in self.rows),
            ),
            _EncodedColumn(
                "record_json",
                codec.TYPE_BYTE_ARRAY,
                self._plain_byte_array(row.record_json for row in self.rows),
            ),
        )

    @staticmethod
    def _schema_element(name: str, physical_type: int, *, utf8: bool) -> bytes:
        fields = [
            (1, codec.I32, codec.integer(physical_type)),
            (3, codec.I32, codec.integer(codec.REPETITION_REQUIRED)),
            (4, codec.BINARY, codec.string(name)),
        ]
        if utf8:
            fields.append((6, codec.I32, codec.integer(codec.CONVERTED_UTF8)))
            logical_type = codec.struct_bytes(
                [(1, codec.STRUCT, codec.struct_bytes([]))]
            )
            fields.append((10, codec.STRUCT, logical_type))
        return codec.struct_bytes(fields)

    def _data_page_header(self, page_size: int) -> bytes:
        data_page = codec.struct_bytes(
            [
                (1, codec.I32, codec.integer(len(self.rows))),
                (2, codec.I32, codec.integer(codec.ENCODING_PLAIN)),
                (3, codec.I32, codec.integer(codec.ENCODING_RLE)),
                (4, codec.I32, codec.integer(codec.ENCODING_RLE)),
            ]
        )
        return codec.struct_bytes(
            [
                (1, codec.I32, codec.integer(codec.PAGE_TYPE_DATA_PAGE)),
                (2, codec.I32, codec.integer(page_size)),
                (3, codec.I32, codec.integer(page_size)),
                (5, codec.STRUCT, data_page),
            ]
        )

    def _append_column(self, column: _EncodedColumn) -> tuple[bytes, int]:
        header = self._data_page_header(len(column.values))
        offset = len(self.payload)
        self.payload += header
        self.payload += column.values
        chunk_size = len(header) + len(column.values)
        metadata = codec.struct_bytes(
            [
                (1, codec.I32, codec.integer(column.physical_type)),
                (
                    2,
                    codec.LIST,
                    codec.list_bytes(
                        codec.I32,
                        [codec.integer(codec.ENCODING_PLAIN)],
                    ),
                ),
                (
                    3,
                    codec.LIST,
                    codec.list_bytes(
                        codec.BINARY,
                        [codec.string(column.name)],
                    ),
                ),
                (4, codec.I32, codec.integer(codec.CODEC_UNCOMPRESSED)),
                (5, codec.I64, codec.integer(len(self.rows))),
                (6, codec.I64, codec.integer(chunk_size)),
                (7, codec.I64, codec.integer(chunk_size)),
                (9, codec.I64, codec.integer(offset)),
            ]
        )
        chunk = codec.struct_bytes(
            [
                (2, codec.I64, codec.integer(offset)),
                (3, codec.STRUCT, metadata),
            ]
        )
        return chunk, chunk_size

    def _schema(self, column_count: int) -> list[bytes]:
        return [
            codec.struct_bytes(
                [
                    (
                        4,
                        codec.BINARY,
                        codec.string("spikenaut_curated_records"),
                    ),
                    (5, codec.I32, codec.integer(column_count)),
                ]
            ),
            self._schema_element("source_file", codec.TYPE_BYTE_ARRAY, utf8=True),
            self._schema_element("source_line", codec.TYPE_INT64, utf8=False),
            self._schema_element("record_json", codec.TYPE_BYTE_ARRAY, utf8=True),
        ]

    def _footer(
        self, columns: Sequence[_EncodedColumn], chunks: list[bytes], total_size: int
    ) -> bytes:
        row_group = codec.struct_bytes(
            [
                (
                    1,
                    codec.LIST,
                    codec.list_bytes(codec.STRUCT, chunks),
                ),
                (2, codec.I64, codec.integer(total_size)),
                (3, codec.I64, codec.integer(len(self.rows))),
            ]
        )
        return codec.struct_bytes(
            [
                (1, codec.I32, codec.integer(1)),
                (
                    2,
                    codec.LIST,
                    codec.list_bytes(
                        codec.STRUCT,
                        self._schema(len(columns)),
                    ),
                ),
                (3, codec.I64, codec.integer(len(self.rows))),
                (
                    4,
                    codec.LIST,
                    codec.list_bytes(codec.STRUCT, [row_group]),
                ),
                (
                    6,
                    codec.BINARY,
                    codec.string(CREATED_BY),
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
        self.payload += codec.PARQUET_MAGIC
        return bytes(self.payload)


def write_viewer_parquet(rows: Sequence[Any]) -> bytes:
    """Return an uncompressed PLAIN Parquet file for the viewer projection."""

    if not rows:
        raise ExportError("refusing to write a Parquet file with no rows")
    return _ParquetWriter(rows).write()


if __package__:
    _expose_package_sibling(__name__)
