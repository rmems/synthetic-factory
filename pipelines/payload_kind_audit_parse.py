#!/usr/bin/env python3
"""JSONL / UTF-8 / surrogate / decimal parse helpers for payload-kind audit.

Extracted from ``payload_kind_audit`` so that module's total complexity stays
under the qlty High threshold. Callers continue to import through
``payload_kind_audit``; this module is an internal split.
"""

from __future__ import annotations

import json
import math
import os
import stat
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))


class PayloadKindAuditError(ValueError):
    """The corpus cannot be audited without guessing."""


# The row fields copied verbatim out of a record. Everything else on a row is
# derived here (a digest, a count, a coordinate) and cannot carry a corpus
# value out unchanged or otherwise.
_EMITTED_RECORD_FIELDS = ("id", "domain", "supervisor_id", "gate_decision")


def _reject_rounded_fields(fields: Mapping[str, Any], where: str) -> None:
    """Reject emitted metadata a binary float cannot carry back out unchanged.

    ``parse_float`` turns every JSON decimal into a Python float, so a literal
    like ``0.1234567890123456789`` would be reported — and pinned by
    ``--expect`` — as a different value than the corpus holds. That is true of
    every field this audit republishes, not just the identifier, and of a
    decimal nested inside a container-valued field, which is emitted just as
    verbatim. Integers and strings round-trip exactly, so only the decimal
    case fails closed.
    """
    for name in _EMITTED_RECORD_FIELDS:
        _reject_rounded_value(fields.get(name), name, where)


def _container_children(value: Any, name: str) -> Iterable[tuple[str, Any]]:
    """Label each child of a container value with the path a rejection reports."""
    if isinstance(value, Mapping):
        return ((f"{name}.{key}", item) for key, item in value.items())
    if isinstance(value, list):
        return ((f"{name}[{index}]", item) for index, item in enumerate(value))
    return ()


def _reject_rounded_value(value: Any, name: str, where: str) -> None:
    """Reject a decimal at ``name`` or anywhere inside a container it holds."""
    if isinstance(value, float):
        raise PayloadKindAuditError(
            f"{where}: record {name} is a JSON decimal this audit cannot "
            f"report exactly: {value!r}"
        )
    for child_name, child in _container_children(value, name):
        _reject_rounded_value(child, child_name, where)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _parse_finite_float(value: str) -> float:
    """Parse one JSON number without accepting binary-float overflow."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number is outside the finite float range: {value!r}")
    return parsed


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject repeated object keys at every depth instead of last-key-wins."""
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _is_unpaired_surrogate(character: str) -> bool:
    return 0xD800 <= ord(character) <= 0xDFFF


def _reject_unpaired_surrogates_in_string(value: str) -> None:
    if any(_is_unpaired_surrogate(character) for character in value):
        raise ValueError("unpaired UTF-16 surrogate in JSON string")


def _reject_unpaired_surrogates_in_mapping(value: Mapping) -> None:
    for key, item in value.items():
        _reject_unpaired_surrogates(key)
        _reject_unpaired_surrogates(item)


def _reject_unpaired_surrogates_in_list(value: list) -> None:
    for item in value:
        _reject_unpaired_surrogates(item)


def _reject_unpaired_surrogates(value: Any) -> None:
    """Reject strings the UTF-8 stdout path cannot encode."""
    if isinstance(value, str):
        _reject_unpaired_surrogates_in_string(value)
    elif isinstance(value, Mapping):
        _reject_unpaired_surrogates_in_mapping(value)
    elif isinstance(value, list):
        _reject_unpaired_surrogates_in_list(value)


def _is_json_whitespace(value: str) -> bool:
    """Return whether non-empty text contains only RFC 8259 JSON whitespace."""
    return bool(value) and all(character in " \t\r\n" for character in value)


def _jsonl_lines(raw: bytes, source_file: str):
    """Yield LF-delimited UTF-8 records without splitting on Unicode separators."""
    segments = raw.split(b"\n")
    last_index = len(segments) - 1
    for line_number, line_bytes in enumerate(segments, 1):
        # CRLF is one record terminator, so neither byte belongs to the record
        # digest. Strip the paired CR only on segments that were actually
        # terminated by LF. A bare CR on the final unterminated segment stays
        # in the payload, matching the curation reader.
        lf_terminated = line_number - 1 != last_index
        if lf_terminated and line_bytes.endswith(b"\r"):
            line_bytes = line_bytes[:-1]
        try:
            line = line_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PayloadKindAuditError(
                f"{source_file}:{line_number}: payload is not valid UTF-8: {exc}"
            ) from exc
        yield line_number, line_bytes, line


def _is_safe_jsonl_name(name: Any) -> bool:
    if not isinstance(name, str):
        return False
    if not name.endswith(".jsonl"):
        return False
    return Path(name).name == name


def _validate_payload_name(name: Any) -> None:
    """A snapshot payload name must be a bare ``*.jsonl`` filename, not a path."""
    if not _is_safe_jsonl_name(name):
        raise PayloadKindAuditError(f"unsafe snapshot payload name: {name!r}")


def _resolve_named_payload_paths(corpus: Path, payload_names: Iterable[str]) -> list[Path]:
    names = list(payload_names)
    for name in names:
        _validate_payload_name(name)
    if len(names) != len(set(names)):
        raise PayloadKindAuditError("snapshot payload names must be unique")
    return [corpus / name for name in sorted(names)]


def _validate_reported_name(name: str, *, kind: str) -> None:
    """Reject a path component this audit cannot emit in JSON/Markdown.

    On POSIX a name is bytes, and Python represents undecodable bytes with
    surrogate escapes. Emitting that value succeeds (escaped lone surrogates
    in JSON), but ``--expect`` then rejects the same document — so the CLI
    would publish an audit it cannot consume.
    """
    try:
        name.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise PayloadKindAuditError(f"{kind} is not valid UTF-8: {name!r}") from exc


def _validate_payload_encoding(path: Path) -> None:
    """Reject a payload filename this audit cannot report as ``source_file``."""
    _validate_reported_name(path.name, kind="payload filename")


def _resolve_payload_paths(corpus: Path, payload_names: Iterable[str] | None) -> list[Path]:
    """Return the sorted ``*.jsonl`` paths to scan, validating any explicit names."""
    if payload_names is None:
        payload_paths = sorted(corpus.glob("*.jsonl"))
    else:
        payload_paths = _resolve_named_payload_paths(corpus, payload_names)
    if not payload_paths:
        raise PayloadKindAuditError(f"corpus contains no *.jsonl payloads: {corpus}")
    for path in payload_paths:
        _validate_payload_encoding(path)
    return payload_paths


def _load_payload_bytes(path: Path) -> bytes:
    """Read one payload file without a check-then-open symlink race.

    Open with ``O_NOFOLLOW``, confirm the opened descriptor is a regular file,
    then read from that descriptor — so a TOCTOU swap to a symlink after an
    ``is_file()`` check cannot redirect the read (CodeRabbit CWE-367).
    """
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PayloadKindAuditError(f"unsafe payload entry: {path}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise PayloadKindAuditError(f"unsafe payload entry: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError as exc:
        raise PayloadKindAuditError(f"cannot read payload {path}: {exc}") from exc
    finally:
        os.close(descriptor)


def _parse_json_record(source_file: str, line_number: int, line: str) -> dict:
    """Parse one JSONL line into a JSON object, or raise PayloadKindAuditError."""
    try:
        record = json.loads(
            line,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
        )
        _reject_unpaired_surrogates(record)
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PayloadKindAuditError(f"{source_file}:{line_number}: {exc}") from exc
    if not isinstance(record, dict):
        raise PayloadKindAuditError(f"{source_file}:{line_number}: record must be a JSON object")
    return record
