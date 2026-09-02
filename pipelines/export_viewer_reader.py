#!/usr/bin/env python3
"""Focused reader for the lossless stdlib-only viewer Parquet projection."""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_viewer_reader")
    from . import export_viewer_codec as codec
    from .export_contract import VIEWER_COLUMNS, ViewerRow
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_viewer_reader"
    )
    import export_viewer_codec as codec
    from export_contract import VIEWER_COLUMNS, ViewerRow


class _ParquetReader:
    """Authenticate and decode one fixed-schema viewer projection."""

    def __init__(self, payload: bytes):
        self.payload = payload

    def _decode_byte_array_at(self, data: bytes, offset: int) -> tuple[str, int]:
        if offset + 4 > len(data):
            raise ValueError(codec.TRUNCATED_PARQUET_PAGE)
        length = int.from_bytes(data[offset : offset + 4], "little")
        offset += 4
        if offset + length > len(data):
            raise ValueError(codec.TRUNCATED_PARQUET_PAGE)
        return data[offset : offset + length].decode("utf-8"), offset + length

    def _decode_int64_at(self, data: bytes, offset: int) -> tuple[int, int]:
        if offset + 8 > len(data):
            raise ValueError(codec.TRUNCATED_PARQUET_PAGE)
        value = int.from_bytes(data[offset : offset + 8], "little", signed=True)
        return value, offset + 8

    def _plain_decoder(self, physical_type: int):
        decoders = {
            codec.TYPE_BYTE_ARRAY: self._decode_byte_array_at,
            codec.TYPE_INT64: self._decode_int64_at,
        }
        decode_at = decoders.get(physical_type)
        if decode_at is None:
            raise ValueError(f"unsupported Parquet physical type {physical_type}")
        return decode_at

    def _decode_plain(self, physical_type: int, data: bytes, num_values: int) -> list[Any]:
        if not num_values:
            return []
        decode_at = self._plain_decoder(physical_type)
        values: list[Any] = []
        offset = 0
        for _ in range(num_values):
            value, offset = decode_at(data, offset)
            values.append(value)
        return values

    def _require_envelope(self) -> None:
        payload = self.payload
        if len(payload) < 12:
            raise ValueError("not a Parquet file")
        if not payload.startswith(codec.PARQUET_MAGIC):
            raise ValueError("not a Parquet file")
        if not payload.endswith(codec.PARQUET_MAGIC):
            raise ValueError("Parquet footer magic is missing")

    def _footer_size(self) -> int:
        payload = self.payload
        footer_size = int.from_bytes(payload[-8:-4], "little")
        if footer_size <= 0:
            raise ValueError("Parquet footer length is invalid")
        if footer_size > len(payload) - 8:
            raise ValueError("Parquet footer length is invalid")
        return footer_size

    def _footer_start(self) -> int:
        self._require_envelope()
        return len(self.payload) - 8 - self._footer_size()

    def _metadata(self) -> dict[int, Any]:
        decoder = codec.CompactDecoder(self.payload, self._footer_start())
        return decoder.read_struct()

    def _require_viewer_columns(self, metadata: dict[int, Any]) -> None:
        schema = metadata.get(2) or []
        names = [
            element.get(4, b"").decode("utf-8")
            for element in schema[1:]
            if isinstance(element, dict)
        ]
        if names != list(VIEWER_COLUMNS):
            raise ValueError(f"unexpected viewer columns: {names}")

    def _column_metadata(self, chunk: dict[int, Any]) -> dict[int, Any]:
        metadata = chunk.get(3) or {}
        compression = metadata.get(4, codec.CODEC_UNCOMPRESSED)
        if compression != codec.CODEC_UNCOMPRESSED:
            raise ValueError("compressed Parquet chunks are not supported")
        return metadata

    @staticmethod
    def _column_name(metadata: dict[int, Any]) -> str:
        path = [item.decode("utf-8") for item in metadata.get(3) or []]
        if len(path) != 1:
            raise ValueError("nested Parquet columns are not supported")
        return path[0]

    def _plain_data_page(self, metadata: dict[int, Any], num_rows: int) -> tuple[bytes, int]:
        decoder = codec.CompactDecoder(self.payload, metadata.get(9, 0))
        page_header = decoder.read_struct()
        if page_header.get(1) != codec.PAGE_TYPE_DATA_PAGE:
            raise ValueError("only Parquet v1 data pages are supported")
        data_page = page_header.get(5) or {}
        if data_page.get(2) != codec.ENCODING_PLAIN:
            raise ValueError("only PLAIN-encoded Parquet pages are supported")
        page_values = data_page.get(1, 0)
        if page_values != num_rows:
            raise ValueError("Parquet column chunk must hold exactly one page")
        page_size = page_header.get(3, 0)
        page = self.payload[decoder.offset : decoder.offset + page_size]
        return page, page_values

    def _decode_column(self, chunk: dict[int, Any], num_rows: int) -> tuple[str, list[Any]]:
        metadata = self._column_metadata(chunk)
        name = self._column_name(metadata)
        page, page_values = self._plain_data_page(metadata, num_rows)
        return name, self._decode_plain(metadata.get(1), page, page_values)

    def _row_group_rows(self, row_group: dict[int, Any]) -> list[Any]:
        num_rows = row_group.get(3, 0)
        column_values: dict[str, list[Any]] = {}
        for chunk in row_group.get(1) or []:
            name, values = self._decode_column(chunk, num_rows)
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

    def read(self) -> list[Any]:
        metadata = self._metadata()
        self._require_viewer_columns(metadata)
        rows: list[Any] = []
        for row_group in metadata.get(4) or []:
            rows.extend(self._row_group_rows(row_group))
        return rows


def read_viewer_parquet(payload: bytes) -> list[Any]:
    """Read one viewer projection written by ``export_viewer_writer``."""

    return _ParquetReader(payload).read()


if __package__:
    _expose_package_sibling(__name__)
