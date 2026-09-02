#!/usr/bin/env python3
"""Lossless viewer projection: minimal PLAIN Parquet writer and reader.

Split out of ``export_hf.py`` by responsibility. The writer emits
uncompressed PLAIN Parquet with the standard library only, and the reader
proves the projection is lossless by rebuilding the exact rows.
"""

from __future__ import annotations

import sys
from typing import Sequence

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

if __package__:
    from . import export_viewer_reader as _reader
    from . import export_viewer_writer as _writer
else:
    import export_viewer_reader as _reader
    import export_viewer_writer as _writer

def write_viewer_parquet(rows: Sequence[ViewerRow]) -> bytes:
    """Return an uncompressed PLAIN Parquet file for the viewer projection."""

    if not rows:
        raise ExportError("refusing to write a Parquet file with no rows")
    return _writer.write_viewer_parquet(rows)


def read_viewer_parquet(payload: bytes) -> list[ViewerRow]:
    """Read back a viewer projection written by :func:`write_viewer_parquet`."""

    return _reader.read_viewer_parquet(payload)


if __package__:
    _expose_package_sibling(__name__)
