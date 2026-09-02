#!/usr/bin/env python3
"""Strict LF-framed JSONL parsing for authenticated export members."""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_members_jsonl")
    from .export_contract import ExportError, _loads_json
    from .strict_jsonl import StrictJsonlError, strict_lf_jsonl_lines
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_members_jsonl"
    )
    from export_contract import ExportError, _loads_json
    from strict_jsonl import StrictJsonlError, strict_lf_jsonl_lines


def lf_jsonl_lines(payload: bytes, label: str) -> list[str]:
    """Decode one strictly LF-framed JSONL payload into physical lines."""

    try:
        return strict_lf_jsonl_lines(payload, label)
    except StrictJsonlError as exc:
        raise ExportError(str(exc)) from exc


def lf_jsonl_documents(payload: bytes, label: str) -> list[Any]:
    """Authenticate every JSON document after the strict framing check."""

    lines = lf_jsonl_lines(payload, label)
    return [
        _loads_json(line, f"{label}:{line_number}") for line_number, line in enumerate(lines, 1)
    ]


if __package__:
    _expose_package_sibling(__name__)
