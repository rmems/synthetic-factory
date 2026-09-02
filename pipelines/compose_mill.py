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
from dataclasses import dataclass
from typing import Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_mill")
    from .check_records import reject_json_constant
    from .curate_identity import _reject_duplicate_object_keys
    from .mill_family import MillFinding, MillIndex
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_mill"
    )
    from check_records import reject_json_constant
    from curate_identity import _reject_duplicate_object_keys
    from mill_family import MillFinding, MillIndex


@dataclass(frozen=True)
class _MillMember:
    relative: str
    payload: bytes
    factory_identity: tuple[str, bool]
    frame_lines: Callable[[bytes], list[bytes]]


def _decode_mill_record(raw_line: bytes) -> object | None:
    """Decode one evidence-bearing physical line, if it is usable."""

    if not raw_line.strip():
        return None
    try:
        return json.loads(
            raw_line.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=reject_json_constant,
        )
    except (ValueError, RecursionError):
        # No ownership evidence; the per-line pass excludes it anyway.
        return None


def _index_member_mills(
    mills: MillIndex,
    member: _MillMember,
) -> None:
    """Add usable ownership evidence from one captured member."""

    factory, verified = member.factory_identity
    for line_number, raw_line in enumerate(member.frame_lines(member.payload), 1):
        record = _decode_mill_record(raw_line)
        if record is None:
            continue
        mills.add(
            factory,
            record,
            (member.relative, line_number),
            factory_verified=verified,
        )


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
        _index_member_mills(
            mills,
            _MillMember(
                relative,
                payload_by_member[relative],
                factory_identity_by_member[relative],
                frame_lines,
            ),
        )
    return {finding.ref: finding for finding in mills.findings()}


if __package__:
    _expose_package_sibling(__name__)
