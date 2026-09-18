#!/usr/bin/env python3
"""Completed-batch JSONL framing for the training audit.

Unmatched payloads stay on the LF-only contract. Authenticated completed
procedural bytes may keep their original physical frames.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit_completion")
    from .strict_jsonl import StrictJsonlError, strict_lf_jsonl_records
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_completion"
    )
    from strict_jsonl import StrictJsonlError, strict_lf_jsonl_records


def completed_published_payload(source_root: Path, relative, payload: bytes) -> bool:
    if __package__:
        from .code_repair.publication_export import completed_published_batch_matches
    else:
        from code_repair.publication_export import completed_published_batch_matches
    return completed_published_batch_matches(source_root, relative, payload)


def physical_jsonl_records(payload: bytes) -> list[bytes]:
    if __package__:
        from .compose_curated_run_lines import jsonl_physical_lines
    else:
        from compose_curated_run_lines import jsonl_physical_lines
    return jsonl_physical_lines(payload)


def audit_jsonl_records(relative, payload: bytes, completed) -> list[bytes]:
    try:
        return strict_lf_jsonl_records(payload, Path(relative).as_posix())
    except StrictJsonlError:
        if completed(relative, payload):
            return physical_jsonl_records(payload)
        raise


if __package__:
    _expose_package_sibling(__name__)
