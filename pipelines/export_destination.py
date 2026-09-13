#!/usr/bin/env python3
"""Export destination safety: pinned writes and destination validation.

Split out of ``export_hf.py`` by responsibility. Export shares compose's
pinned-directory writer so derived bytes can never be steered into the
curated source, the authenticated compose source, or ``outputs/raw/``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("export_destination")
    from . import compose_curated
    from .export_contract import ExportError, ViewerRow
    from .export_members import _is_under_raw, _require_exact_directory
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "export_destination"
    )
    import compose_curated
    from export_contract import ExportError, ViewerRow
    from export_members import _is_under_raw, _require_exact_directory


def _write_new_bytes(
    destination_target: int | compose_curated.PinnedDestination,
    relative: Any,
    payload: bytes,
) -> str:
    """Create one new export file with every path component pinned.

    Export shares compose's pinned writer so a same-user process cannot swap a
    child such as ``data/splits`` for a symlink between its ``mkdir`` and the
    matching ``open`` and steer derived output into ``outputs/raw/``.
    """

    try:
        return compose_curated.write_pinned_new_bytes(
            destination_target, relative, payload, f"export {relative}"
        )
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _jsonl_payload(rows: Sequence[ViewerRow]) -> bytes:
    return "".join(row.record_json + "\n" for row in rows).encode("utf-8")


def _create_pinned_destination(
    curated_root: Path, destination: Path
) -> compose_curated.PinnedDestination:
    """Create the export directory through the same parent pin compose uses."""

    try:
        return compose_curated.create_pinned_destination(curated_root, destination)
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _finish_pinned_destination(pinned: compose_curated.PinnedDestination) -> None:
    try:
        pinned.finish()
    except compose_curated.ComposeError as exc:
        raise ExportError(str(exc)) from exc


def _validated_curated_tree(curated_root: Path) -> tuple[Path, Path]:
    """Require the exact curated root and its exact records directory."""

    curated_root = _require_exact_directory(curated_root, "curated root")
    records_dir = curated_root / compose_curated.RECORDS_DIRNAME
    try:
        records_dir = _require_exact_directory(records_dir, "curated records")
    except ExportError as exc:
        raise ExportError(
            f"curated root has no exact {compose_curated.RECORDS_DIRNAME}/ payload: "
            f"{curated_root}"
        ) from exc
    return curated_root, records_dir


def _require_new_export_destination(destination: Path) -> None:
    """Require a new destination under one exact non-raw parent."""

    if os.path.lexists(destination):
        raise ExportError(f"refusing to overwrite an existing destination: {destination}")
    if _is_under_raw(destination):
        raise ExportError(
            f"refusing to write inside immutable raw evidence: {destination}"
        )
    if not destination.parent.is_dir():
        raise ExportError(f"destination parent does not exist: {destination.parent}")
    _require_exact_directory(destination.parent, "destination parent")


def _require_destination_outside_curated(
    resolved_root: Path, destination: Path
) -> None:
    """Refuse a destination at or below the curated source root."""

    resolved_destination = destination.resolve(strict=False)
    if resolved_root == resolved_destination:
        raise ExportError("destination cannot be written inside the curated root")
    if resolved_root in resolved_destination.parents:
        raise ExportError("destination cannot be written inside the curated root")


def _validated_export_paths(
    curated_root: Path, destination: Path
) -> tuple[Path, Path, Path]:
    """Validate both trees and return (curated root, records dir, resolved root)."""

    curated_root, records_dir = _validated_curated_tree(curated_root)
    _require_new_export_destination(destination)
    resolved_root = curated_root.resolve()
    _require_destination_outside_curated(resolved_root, destination)
    return curated_root, records_dir, resolved_root


def _refuse_authenticated_source_destination(
    compose_metadata: Mapping[str, Any], destination: Path
) -> None:
    """Keep derived export bytes outside the authenticated compose source."""

    source_root = Path(compose_metadata["source"]["path"])
    resolved_destination = destination.resolve(strict=False)
    if source_root == resolved_destination or source_root in resolved_destination.parents:
        raise ExportError(
            "destination cannot be written inside the authenticated compose source"
        )


if __package__:
    _expose_package_sibling(__name__)
