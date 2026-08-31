#!/usr/bin/env python3
"""Fail-closed JSONL source reading for the spike probe.

The probe's input contract is deterministic: a target expands to a stable set
of JSONL files, and every physical line either parses under the strict numeric
hooks or is reported with a named reason code.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_bridge import REASON_INVALID_JSON, REASON_INVALID_UTF8  # noqa: E402
from census import visible_jsonl_paths  # noqa: E402
from exact_json import parse_finite_json_float as _parse_exact_json_float  # noqa: E402
from round_txn_raster import RASTER_FACTORY_SLUGS  # noqa: E402
from validate_run import reject_json_constant  # noqa: E402

REASON_INPUT_UNREADABLE = "BRIDGE_SOURCE_UNREADABLE"


def _expanded_jsonl_targets(targets: Iterable[str | Path]) -> Iterator[Path]:
    """Yield explicit files or transaction-visible JSONL from directories."""

    for target in targets:
        path = Path(target)
        yield from visible_jsonl_paths(path) if path.is_dir() else (path,)


def _is_raster_factory_path(path: Path) -> bool:
    """Return whether a JSONL path is enclosed by a raster-gated factory."""

    supplied_parts = path.parts
    resolved_parts = path.resolve(strict=False).parts
    return any(part in RASTER_FACTORY_SLUGS for part in (*supplied_parts, *resolved_parts))


def jsonl_paths(targets: Iterable[str | Path]) -> list[Path]:
    """Expand run directories into sorted JSONL paths; keep explicit files.

    An input reached twice -- named twice, or named once directly and once
    through a containing directory -- is expanded once. Reading it twice
    emitted every raster twice and silently doubled the spike and energy
    totals, changing the weighting of a distillation dataset with no report
    that anything was wrong. Identity is the resolved path, so two names for
    one file (a symlink, ``./x`` vs ``x``) also count once.
    """

    unique: dict[Path, Path] = {}
    for path in _expanded_jsonl_targets(targets):
        unique.setdefault(path.resolve(strict=False), path)
    return list(unique.values())


def _read_jsonl(path: Path) -> tuple[str | None, str | None]:
    """Read UTF-8 without universal-newline translation."""

    try:
        payload = path.read_bytes()
    except OSError:
        return None, REASON_INPUT_UNREADABLE
    try:
        return payload.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, REASON_INVALID_UTF8


def _parse_finite_json_float(text: str) -> float:
    """Reject a finite JSON token such as ``1e999`` that overflows to infinity."""

    return _parse_exact_json_float(text)


def _parse_record(line: str) -> tuple[Any, str | None]:
    """Parse one physical JSONL record using strict numeric hooks."""

    try:
        record = json.loads(
            line,
            parse_constant=reject_json_constant,
            parse_float=_parse_finite_json_float,
        )
    except (ValueError, RecursionError):
        return None, REASON_INVALID_JSON
    return record, None


def _records_in_path(path: Path) -> Iterator[tuple[str, Any, str | None]]:
    """Yield parsed records and named input problems from one JSONL path."""

    text, read_problem = _read_jsonl(path)
    if read_problem is not None:
        yield f"{path}:0", None, read_problem
        return
    for line_number, line in enumerate(text.split("\n"), 1):
        if line.strip():
            record, parse_problem = _parse_record(line)
            yield f"{path}:{line_number}", record, parse_problem


def iter_records(paths: Iterable[Path]) -> Iterator[tuple[str, Any, str | None]]:
    """Yield ``(where, record, problem_code)`` for every JSONL input line."""

    for path in paths:
        yield from _records_in_path(path)
