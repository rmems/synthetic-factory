#!/usr/bin/env python3
"""JSONL I/O for oracle-grounded records (issue #78).

Reading is streamed and fails per line, never per file: an undecodable byte,
a malformed line, a bare ``NaN`` or a duplicated object key is reported as the
one bad record it is.
Writing is canonical JSON, refuses to overwrite, and refuses any destination
that names or aliases the immutable raw tree (``raw_tree_guard``) before it
creates so much as a directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import envelope
from .import_twins import bind_import_twin

try:
    from pipelines.raw_tree_guard import is_under_raw as _is_under_raw_tree
    from pipelines.tag_jsonutil import (
        reject_duplicate_object_keys as _reject_duplicate_object_keys,
    )
except ImportError:
    from raw_tree_guard import is_under_raw as _is_under_raw_tree
    from tag_jsonutil import reject_duplicate_object_keys as _reject_duplicate_object_keys


def _parse_jsonl_line(raw: bytes) -> tuple[bool, Any]:
    """``(has_content, parsed_or_None)`` for one raw JSONL line.

    Decoding failures are a per-line finding, not an abort: ``read_text`` on
    the whole file raised ``UnicodeDecodeError`` before any record was seen,
    so one undecodable byte took down the validation of the entire corpus
    instead of being reported as the one bad line it is.

    A duplicated object key is a parse failure too. ``json.loads`` keeps the
    last value silently, so a line carrying two ``result`` objects would
    validate, and be digested, as whichever came last; the repository's
    strict loaders reject the same bytes through
    ``tag_jsonutil.reject_duplicate_object_keys``, and so does this reader.

    A pathologically nested line is a parse failure as well. ``json.loads``
    raises ``RecursionError`` on it, which is not a ``ValueError``, so one
    such line used to escape this boundary and abort the read of the whole
    file; ``check_records`` on main treats it as the one bad line it is.
    """

    try:
        stripped = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return True, None
    if not stripped:
        return False, None
    try:
        parsed = json.loads(
            stripped,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=envelope.reject_json_constant,
            parse_float=envelope.reject_nonfinite_float,
        )
        # The envelope's canonical form is what every digest and every write
        # is computed over. A line that parses but cannot take it (a lone
        # surrogate escape such as \ud800 re-encodes as nothing) is this
        # line's parse failure, not a downstream exception.
        envelope.canonical_json(parsed).encode("utf-8")
        return True, parsed
    except (ValueError, RecursionError):  # JSONDecodeError and UnicodeEncodeError included
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


def iter_jsonl_bytes(data: bytes):
    """:func:`iter_jsonl` over bytes already in hand, so a digest and a parse share one read."""

    for lineno, raw in enumerate(data.splitlines(keepends=True), start=1):
        has_content, parsed = _parse_jsonl_line(raw)
        if has_content:
            yield lineno, parsed


def _refuse_raw_destination(destination: Path) -> None:
    """Refuse a destination under ``outputs/raw`` before touching the filesystem.

    ``raw_tree_guard`` is the repository's one raw-path detector: it recognises
    the raw tree by name in any checkout, through a symlink alias and through a
    bind mount, so the family CLIs' ``--output`` and the validator's
    ``--stamp-output`` cannot drop a non-transactional batch beside published
    evidence the way every other writer in ``pipelines/`` already refuses to.
    """

    if _is_under_raw_tree(destination):
        raise envelope.ContractError(
            f"refusing to write inside immutable raw evidence: {destination}"
        )


def write_jsonl(path, records) -> int:
    """Write records as JSONL. Refuses raw-tree and existing destinations."""

    destination = Path(path)
    _refuse_raw_destination(destination)
    if destination.exists():
        raise envelope.ContractError(f"refusing to overwrite existing file: {destination}")
    # Every record takes the envelope's canonical form, and the whole payload
    # is UTF-8, before a directory or a file exists; content that cannot is a
    # ContractError, never a partial file beside a no-overwrite rule.
    try:
        lines = [envelope.canonical_json(record) for record in records]
        payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:
        raise envelope.ContractError(
            f"refusing to write {destination}: a record's content cannot take the "
            "envelope's canonical form"
        ) from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    # The parent may have been created through a link that appeared after the
    # first check; look again at what mkdir actually produced.
    _refuse_raw_destination(destination.parent)
    # Exclusive creation: the file is made here or not at all. A destination
    # that appeared since the check, or a link planted at the path, fails the
    # open instead of being truncated or followed.
    try:
        with open(destination, "xb") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise envelope.ContractError(
            f"refusing to overwrite existing file: {destination}"
        ) from exc
    return len(lines)


bind_import_twin(__name__)
