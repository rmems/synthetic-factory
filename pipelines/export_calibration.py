#!/usr/bin/env python3
"""Reward-calibration authentication for the export replay.

Split out of ``export_hf.py`` by responsibility: the COMPOSE.json calibration
descriptor is proven against exact file evidence (or its provable absence)
before any replay trusts the catalog it names.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
from export_contract import (  # noqa: E402
    ExportError,
    _reject_json_constant,
    _reject_nonfinite_json_float,
)
from export_members import _read_exact_regular_file  # noqa: E402
from curate_identity import _reject_duplicate_object_keys  # noqa: E402
from reward_calibration import _entry_calibrations  # noqa: E402,F401

def _load_calibration_payload(payload: bytes, path: Path) -> dict[str, Any]:
    """Load reward calibration from pinned bytes while preserving evidence labels."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"calibration {path}: payload is not UTF-8: {exc}") from exc
    try:
        # Match compose: duplicate keys in calibration evidence are ambiguous
        # conversion factors, never a last-value-wins choice.
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_reject_nonfinite_json_float,
        )
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ExportError(f"calibration {path}: invalid JSON: {exc}") from exc
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise ExportError(f"calibration {path}: records must be a list")

    catalog: dict[str, Any] = {}
    for index, entry in enumerate(records):
        for record_id, calibration in _entry_calibrations(
            entry, path=path, index=index
        ):
            key = record_id.lower()
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise ExportError(
                    f"calibration {path}: conflicting calibrations for {record_id}"
                )
            catalog[key] = calibration
    return catalog

def _validated_calibration_descriptor(
    summary: dict[str, Any],
) -> tuple[dict[str, Any], Any, int]:
    """Validate the descriptor envelope and return (descriptor, mode, records)."""

    descriptor = summary.get("calibration")
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "mode",
        "path",
        "sha256",
        "records",
    }:
        raise ExportError("COMPOSE.json: calibration descriptor is incomplete")
    records = descriptor.get("records")
    if isinstance(records, bool) or not isinstance(records, int) or records < 0:
        raise ExportError("COMPOSE.json: calibration.records must be nonnegative")
    return descriptor, descriptor.get("mode"), records


def _absent_calibration_catalog(
    descriptor: dict[str, Any], source_root: Path
) -> dict[str, Any]:
    """The empty catalog for mode "none", provably still current."""

    if descriptor.get("path") is not None or descriptor.get("sha256") is not None:
        raise ExportError("COMPOSE.json: absent calibration must not name a file")
    # Compose auto-discovers the canonical default calibration file, so a
    # "none" descriptor only replays the current source snapshot if that
    # file is still absent. Trusting the stale descriptor once the default
    # has appeared would export uncalibrated rewards while claiming the
    # snapshot was replayed; require recomposition instead.
    default_calibration = source_root / compose_curated.FFPC_UNITS_MIGRATION
    if os.path.lexists(default_calibration):
        raise ExportError(
            "COMPOSE.json: compose recorded no calibration, but default "
            f"calibration evidence now exists at {default_calibration}; "
            "recompose the source run before exporting"
        )
    return {}


def _file_calibration_catalog(
    descriptor: dict[str, Any], mode: str, source_root: Path
) -> dict[str, Any]:
    """The catalog rebuilt from the descriptor's authenticated file evidence."""

    raw_path = descriptor.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ExportError("COMPOSE.json: calibration.path must be an absolute string")
    path = Path(raw_path)
    if not path.is_absolute():
        raise ExportError("COMPOSE.json: calibration.path must be absolute")
    if mode == "source_run" and path != source_root / compose_curated.FFPC_UNITS_MIGRATION:
        raise ExportError("COMPOSE.json: source-run calibration path is not canonical")
    _path, payload = _read_exact_regular_file(
        path.parent, path.name, "COMPOSE calibration"
    )
    digest = hashlib.sha256(payload).hexdigest()
    if descriptor.get("sha256") != digest:
        raise ExportError("COMPOSE.json: calibration digest mismatch")
    return _load_calibration_payload(payload, path)


def _authenticated_calibration(
    summary: dict[str, Any], source_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    descriptor, mode, records = _validated_calibration_descriptor(summary)
    if mode == "none":
        catalog = _absent_calibration_catalog(descriptor, source_root)
    elif mode in {"source_run", "explicit"}:
        catalog = _file_calibration_catalog(descriptor, mode, source_root)
    else:
        raise ExportError(f"COMPOSE.json: unsupported calibration mode {mode!r}")
    if len(catalog) != records or summary.get("calibrated_records") != records:
        raise ExportError("COMPOSE.json: calibrated record count does not authenticate")
    return catalog, dict(descriptor)
