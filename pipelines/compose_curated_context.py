#!/usr/bin/env python3
"""Typed, immutable inputs shared by curated composition stages.

These values separate stable source coordinates and transform metadata from
the mutable record/manifest state that each stage deliberately updates.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, MutableMapping


if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_context")
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
class SourceLineCoordinate:
    """Authenticated location of one physical source line and its file digest."""

    path: str
    line: int
    file_sha256: str


@dataclass(frozen=True)
class SemanticRegistry:
    """Shared semantic indexes that detect duplicate source and curated records."""

    seen_source: MutableMapping[str, tuple[str, int]] | None = None
    seen_curated: MutableMapping[str, tuple[str, int]] | None = None


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
