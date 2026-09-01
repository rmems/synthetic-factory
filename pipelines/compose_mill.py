#!/usr/bin/env python3
"""Corpus-level foreign-mill quarantine for the compose pipeline.

The identity lane assigns canonical ids before any later pass can see a
foreign mill's id prefix, so mill ownership has to be resolved against the
*source* identities — from the same LF-framed physical lines composition
itself consumes — before the first lane runs. Both ``compose_run`` and the
export replay run this pass over the same captured bytes, so a quarantined
line is excluded, and authenticated as excluded, identically in both.
"""

from __future__ import annotations

import json
from importlib import import_module
import sys
from pathlib import Path
from typing import Callable, Mapping

_PIPELINES = Path(__file__).resolve().parent
if not __package__ and str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

_SIBLING_PREFIX = f"{__package__}." if __package__ else ""
_check_records = import_module(f"{_SIBLING_PREFIX}check_records")
_curate_identity = import_module(f"{_SIBLING_PREFIX}curate_identity")
_mill_family = import_module(f"{_SIBLING_PREFIX}mill_family")
reject_json_constant = _check_records.reject_json_constant
_reject_duplicate_object_keys = _curate_identity._reject_duplicate_object_keys
MillFinding = _mill_family.MillFinding
MillIndex = _mill_family.MillIndex


def index_compose_mills(
    payload_by_member: Mapping[str, bytes],
    factory_identity_by_member: Mapping[str, tuple[str, bool]],
    frame_lines: Callable[[bytes], list[bytes]],
) -> dict[tuple[str, int], MillFinding]:
    """Return {(member, line): finding} for foreign-mill source lines.

    ``frame_lines`` is the caller's own physical-line framer, so finding
    coordinates always match the lines the caller then composes or replays.
    Undecodable lines carry no ownership evidence and are skipped here; the
    per-line pass excludes them on its own terms.
    """

    mills = MillIndex()
    for relative in sorted(payload_by_member):
        factory, verified = factory_identity_by_member[relative]
        for line_number, raw_line in enumerate(
            frame_lines(payload_by_member[relative]), 1
        ):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(
                    raw_line.decode("utf-8"),
                    object_pairs_hook=_reject_duplicate_object_keys,
                    parse_constant=reject_json_constant,
                )
            except (ValueError, RecursionError):
                # No ownership evidence; the per-line pass excludes it anyway.
                continue
            mills.add(
                factory,
                record,
                (relative, line_number),
                factory_verified=verified,
            )
    return {finding.ref: finding for finding in mills.findings()}
