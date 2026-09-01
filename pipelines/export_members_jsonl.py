#!/usr/bin/env python3
"""Strict LF-framed JSONL parsing for authenticated export members."""

from __future__ import annotations

from typing import Any

from export_contract import ExportError, _loads_json


def _decoded_utf8(payload: bytes, label: str) -> str:
    """Decode member bytes without replacing malformed UTF-8."""

    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"{label}: payload is not UTF-8: {exc}") from exc


def _without_terminal_separator(text: str, label: str) -> list[str]:
    """Split one LF-terminated payload without manufacturing a final record."""

    if text and not text.endswith("\n"):
        raise ExportError(f"{label}: JSONL must end with a newline")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _require_lf_only(text: str, label: str) -> None:
    """Reject CR and leave LF as the only accepted record separator."""

    if "\r" in text:
        raise ExportError(f"{label}: LF-only JSONL cannot contain carriage returns")


def _require_nonblank(line: str, line_number: int, label: str) -> None:
    """Reject an empty or whitespace-only physical JSONL record."""

    if not line.strip():
        raise ExportError(f"{label}:{line_number}: JSONL has a blank line")


def lf_jsonl_lines(payload: bytes, label: str) -> list[str]:
    """Decode one strictly LF-framed JSONL payload into physical lines."""

    text = _decoded_utf8(payload, label)
    _require_lf_only(text, label)
    lines = _without_terminal_separator(text, label)
    for line_number, line in enumerate(lines, 1):
        _require_nonblank(line, line_number, label)
    return lines


def lf_jsonl_documents(payload: bytes, label: str) -> list[Any]:
    """Authenticate every JSON document after the strict framing check."""

    lines = lf_jsonl_lines(payload, label)
    return [
        _loads_json(line, f"{label}:{line_number}")
        for line_number, line in enumerate(lines, 1)
    ]
