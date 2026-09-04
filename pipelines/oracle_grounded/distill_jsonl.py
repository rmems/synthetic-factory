#!/usr/bin/env python3
"""JSONL I/O for oracle-grounded records (issue #78).

Reading is streamed and fails per line, never per file: an undecodable byte,
a malformed line or a bare ``NaN`` is reported as the one bad record it is.
Writing is canonical JSON and refuses to overwrite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import envelope
from .import_twins import bind_import_twin


def _parse_jsonl_line(raw: bytes) -> tuple[bool, Any]:
    """``(has_content, parsed_or_None)`` for one raw JSONL line.

    Decoding failures are a per-line finding, not an abort: ``read_text`` on
    the whole file raised ``UnicodeDecodeError`` before any record was seen,
    so one undecodable byte took down the validation of the entire corpus
    instead of being reported as the one bad line it is.
    """

    try:
        stripped = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return True, None
    if not stripped:
        return False, None
    try:
        return True, json.loads(
            stripped,
            parse_constant=envelope.reject_json_constant,
            parse_float=envelope.reject_nonfinite_float,
        )
    except ValueError:  # JSONDecodeError included
        return True, None


def iter_jsonl(path):
    """Yield ``(line_number, parsed_or_None)`` pairs, one line at a time.

    Streaming, so validating a scaled corpus needs memory for one record,
    never for the whole raw file plus every decoded record at once.

    Non-finite constants are a parse failure, not a value. ``json.loads``
    accepts bare ``NaN`` and ``Infinity``; letting one through means the first
    canonical re-serialisation (``allow_nan=False``) raises and takes down the
    validation of every other record in the run. Reporting the offending line
    is strictly better than aborting the corpus.
    """

    with Path(path).open("rb") as handle:
        for lineno, raw in enumerate(handle, start=1):
            has_content, parsed = _parse_jsonl_line(raw)
            if has_content:
                yield lineno, parsed


def read_jsonl(path) -> list[tuple[int, Any]]:
    """Eager form of :func:`iter_jsonl`, for small inputs and tests."""

    return list(iter_jsonl(path))


def write_jsonl(path, records) -> int:
    """Write records as JSONL. Refuses to overwrite an existing destination."""

    destination = Path(path)
    if destination.exists():
        raise envelope.ContractError(f"refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [envelope.canonical_json(record) for record in records]
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


bind_import_twin(__name__)
