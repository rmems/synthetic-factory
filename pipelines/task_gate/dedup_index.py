#!/usr/bin/env python3
"""The persisted duplicate index: kept-proposal keys across runs, read-only until a new write.

A key is ``sha256(program_id, program_sha256, normalized mutant)``. The mutant is normalized
with ``ast.dump`` before hashing, so whitespace and redundant parentheses are one mutant.
``minimal_edit`` still returns the raw byte span for the index row. The key also binds the
program's own sha256, so a key kept against an older catalog text never matches the program
once its text changes. The hashed bytes are exact JSON of ``[KEY_FORMAT, program_id,
program_sha256, normalized_mutant]``. Only kept proposals are indexed: a rejected proposal is
deterministic and is re-rejected on its own merits, so the index stays the list of tasks that
already exist. Each run reads every prior index file it is given and writes a new, cumulative
``dedup-index.jsonl`` into its own new destination; no existing file is touched, and the next
run needs only the newest one. Keys minted under ``task-gate-key/2`` (the raw edit) do not
match these.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import stat
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import (
    StrictJsonlError, bind_import_twin, dumps_exact_json, load_strict_json, strict_lf_jsonl_lines,
)
from .checks import is_count

__all__ = [
    "PriorIndex", "dedup_key", "index_bytes", "load_prior", "minimal_edit", "normalized_text",
]

_KEY = re.compile(r"[0-9a-f]{64}")
_FIELDS = frozenset({"format", "key", "program_id", "start_byte", "end_byte"})


def _skip_field(name: str, value: object) -> bool:
    """Defaults that ``ast.dump`` prints on one of 3.14 and 3.15 and not the other."""

    if name == "is_lazy" and not value:
        return True
    return name == "ctx" and isinstance(value, ast.Load)


def _dump(node: object) -> str:
    """``ast.dump`` with those defaults removed from the tree, not from the text.

    A string replace would also edit a literal that happens to contain ``ctx=Load()``.
    """

    if isinstance(node, ast.AST):
        parts = []
        for name in node._fields:
            try:
                value = getattr(node, name)
            except AttributeError:
                continue
            if _skip_field(name, value):
                continue
            if value is None and getattr(type(node), name, ...) is None:
                continue
            if value == []:
                field_type = type(node)._field_types.get(name, object)
                if getattr(field_type, "__origin__", ...) is list:
                    continue
            parts.append(f"{name}={_dump(value)}")
        return f"{type(node).__name__}({', '.join(parts)})"
    if isinstance(node, list):
        return "[" + ", ".join(_dump(item) for item in node) + "]"
    return repr(node)


def normalized_text(text: str) -> str:
    """The mutant's tree without positions, so spacing and redundant parentheses collapse.

    A falsy ``is_lazy`` and a ``Load`` context are omitted, because 3.15 prints the first and
    3.14 prints the second. A true lazy import and a ``Store`` or ``Del`` context stay.
    """

    return _dump(ast.parse(text))


def minimal_edit(original: bytes, mutant: bytes) -> tuple[int, int, bytes]:
    """The smallest ``(start, end, replacement)`` with ``original[:start] + replacement +
    original[end:] == mutant``: the common prefix, then the common suffix of what remains."""

    start = len(os.path.commonprefix([original, mutant]))
    room = min(len(original), len(mutant)) - start
    tail = min(len(os.path.commonprefix([original[::-1], mutant[::-1]])), room)
    return start, len(original) - tail, mutant[start:len(mutant) - tail]


def dedup_key(program_id: str, program_text: str, mutant_text: str) -> tuple[str, int, int]:
    """The key of the normalized mutant, plus the raw minimal-edit span of the program."""

    original = program_text.encode("utf-8")
    start, end, _replacement = minimal_edit(original, mutant_text.encode("utf-8"))
    payload = dumps_exact_json([
        cv.KEY_FORMAT, program_id, hashlib.sha256(original).hexdigest(),
        normalized_text(mutant_text),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), start, end


@dataclass(frozen=True)
class PriorIndex:
    """Every key seen in prior runs, the rows that carry them, and each file's digest."""

    rows: Mapping[str, dict[str, Any]]
    files: tuple[dict[str, Any], ...]

    def __contains__(self, key: object) -> bool:
        return key in self.rows

    @classmethod
    def empty(cls) -> PriorIndex:
        return cls({}, ())


def _shape_is_sound(row: object) -> bool:
    return isinstance(row, dict) and set(row) == _FIELDS


def _key_is_sound(row: dict) -> bool:
    return isinstance(row["key"], str) and _KEY.fullmatch(row["key"]) is not None


def _program_is_sound(row: dict) -> bool:
    return isinstance(row["program_id"], str) and bool(row["program_id"])


def _span_is_sound(row: dict) -> bool:
    return is_count(row["start_byte"]) and is_count(row["end_byte"])


_ROW_CHECKS = (
    lambda row: row["format"] == cv.INDEX_FORMAT, _key_is_sound, _program_is_sound, _span_is_sound,
)


def _row_is_sound(row: object) -> bool:
    return _shape_is_sound(row) and all(check(row) for check in _ROW_CHECKS)


def _read(path: Path) -> bytes:
    try:
        cv.refuse_when(
            not stat.S_ISREG(os.stat(path).st_mode), cv.REFUSE_INDEX_UNREADABLE,
            f"prior index {path} is not a regular file",
        )
        with path.open("rb") as handle:
            data = handle.read(cv.MAX_INDEX_BYTES + 1)
    except OSError as exc:
        raise cv.GateRefusal(cv.REFUSE_INDEX_UNREADABLE, f"prior index {path}: {exc}") from exc
    cv.refuse_when(
        len(data) > cv.MAX_INDEX_BYTES, cv.REFUSE_INDEX_MALFORMED, f"prior index {path} is too large",
    )
    return data


def _parse_file(path: Path, data: bytes) -> list[dict[str, Any]]:
    try:
        lines = strict_lf_jsonl_lines(data, str(path))
        rows = [load_strict_json(line) for line in lines]
    except (StrictJsonlError, ValueError, RecursionError) as exc:
        raise cv.GateRefusal(cv.REFUSE_INDEX_MALFORMED, f"prior index {path}: {exc}") from exc
    bad = next((n for n, row in enumerate(rows, 1) if not _row_is_sound(row)), None)
    cv.refuse_when(bad is not None, cv.REFUSE_INDEX_MALFORMED, f"prior index {path}:{bad} is not an index row")
    keys = [row["key"] for row in rows]
    cv.refuse_when(
        len(set(keys)) != len(keys), cv.REFUSE_INDEX_MALFORMED, f"prior index {path} repeats a key",
    )
    return rows


def load_prior(paths: Iterable[Path | str]) -> PriorIndex:
    """Union of the given index files; an absent or malformed file refuses the run."""

    merged: dict[str, dict[str, Any]] = {}
    files: list[dict[str, Any]] = []
    for item in paths:
        path = Path(item)
        data = _read(path)
        rows = _parse_file(path, data)
        files.append({"path": path.name, "sha256": hashlib.sha256(data).hexdigest(), "keys": len(rows)})
        for row in rows:
            merged.setdefault(row["key"], row)
    return PriorIndex(merged, tuple(files))


def index_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    """Deterministic index bytes: one exact-JSON row per key, sorted by key."""

    ordered = sorted(rows, key=lambda row: row["key"])
    return "".join(dumps_exact_json(dict(row)) + "\n" for row in ordered).encode("utf-8")


bind_import_twin(__name__)
