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
import sys
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from census import factory_identity_for_path  # noqa: E402
from check_records import reject_json_constant  # noqa: E402
from mill_family import MillFinding, MillIndex  # noqa: E402


def index_compose_mills(
    source_run: Path,
    payload_by_member: Mapping[str, bytes],
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
        path = source_run.joinpath(*PurePosixPath(relative).parts)
        factory, verified = factory_identity_for_path(source_run, path)
        for line_number, raw_line in enumerate(
            frame_lines(payload_by_member[relative]), 1
        ):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(
                    raw_line.decode("utf-8"),
                    parse_constant=reject_json_constant,
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                ValueError,
                RecursionError,
            ):
                # No ownership evidence; the per-line pass excludes it anyway.
                continue
            mills.add(
                factory,
                record,
                (relative, line_number),
                factory_verified=verified,
            )
    return {finding.ref: finding for finding in mills.findings()}
