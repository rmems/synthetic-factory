#!/usr/bin/env python3
"""Typed, immutable inputs shared by curated composition stages.

These values separate stable source coordinates and transform metadata from
the mutable record/manifest state that each stage deliberately updates.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any


if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated_context", allow_initializing=True):
        import compose_curated_context as _direct_compose_curated_context

        _require_local_sibling(
            _direct_compose_curated_context,
            "compose_curated_context",
        )
        del _direct_compose_curated_context
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_context"
    )


@dataclass(frozen=True)
class SourceCoordinates:
    """Authenticated location and digest of one source record."""

    path: str
    line: int
    sha256: str
    file_sha256: str | None = None


@dataclass(frozen=True)
class RecordContext:
    """Stable inputs shared by every record-level curation stage."""

    source: SourceCoordinates
    calibration: Any = None
    trajectory_preferences: Any = None


@dataclass(frozen=True)
class StageDefinition:
    """The immutable identity of one manifest stage."""

    lane: str
    transform_name: str
    transform_version: str


def stage(
    definition: StageDefinition,
    action: str,
    **evidence: Any,
) -> dict[str, Any]:
    """Build one stage manifest without mutating caller-owned evidence."""

    reason_codes = list(evidence.pop("reason_codes", []) or [])
    return {
        "lane": definition.lane,
        "transform_name": definition.transform_name,
        "transform_version": definition.transform_version,
        "action": action,
        "reason_codes": reason_codes,
        **evidence,
    }


if __package__:
    _expose_package_sibling(__name__)
