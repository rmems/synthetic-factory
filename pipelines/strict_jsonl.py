#!/usr/bin/env python3
"""Neutral strict UTF-8 and LF-only framing for authenticated JSONL."""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("strict_jsonl")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "strict_jsonl"
    )


class StrictJsonlError(ValueError):
    """Raised when bytes do not form strict LF-framed UTF-8 JSONL."""


def _require_lf_framing(payload: bytes, label: str) -> None:
    if b"\r" in payload:
        raise StrictJsonlError(f"{label}: LF-only JSONL cannot contain carriage returns")
    if payload and not payload.endswith(b"\n"):
        raise StrictJsonlError(f"{label}: JSONL must end with a newline")


def _require_nonblank_records(records: list[bytes], label: str) -> None:
    for line_number, record in enumerate(records, 1):
        if not record.strip():
            raise StrictJsonlError(f"{label}:{line_number}: JSONL has a blank line")


def strict_lf_jsonl_records(payload: bytes, label: str) -> list[bytes]:
    """Split one payload into physical LF records without decoding their JSON."""

    _require_lf_framing(payload, label)
    records = payload.split(b"\n")
    if records and records[-1] == b"":
        records.pop()
    _require_nonblank_records(records, label)
    return records


def strict_lf_jsonl_lines(payload: bytes, label: str) -> list[str]:
    """Decode strict JSONL while preserving Unicode line separators as data."""

    records = strict_lf_jsonl_records(payload, label)
    try:
        return [record.decode("utf-8") for record in records]
    except UnicodeDecodeError as exc:
        raise StrictJsonlError(f"{label}: payload is not UTF-8: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
