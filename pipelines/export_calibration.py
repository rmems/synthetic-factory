#!/usr/bin/env python3
"""Reward-calibration authentication for the export replay.

Split out of ``export_hf.py`` by responsibility: the COMPOSE.json calibration
descriptor is proven against exact file evidence (or its provable absence)
before any replay trusts the catalog it names.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import curate_rewards  # noqa: E402
from export_contract import ExportError, _loads_json  # noqa: E402
from export_members import _read_exact_regular_file  # noqa: E402

def _load_calibration_payload(payload: bytes, path: Path) -> dict[str, Any]:
    """Load reward calibration from pinned bytes while preserving evidence labels."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"calibration {path}: payload is not UTF-8: {exc}") from exc
    document = _loads_json(text, f"calibration {path}")
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise ExportError(f"calibration {path}: records must be a list")

    catalog: dict[str, Any] = {}
    for index, entry in enumerate(records):
        for record_id, calibration in _entry_calibrations(entry, index, path):
            key = record_id.lower()
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise ExportError(
                    f"calibration {path}: conflicting calibrations for {record_id}"
                )
            catalog[key] = calibration
    return catalog


def _entry_calibrations(entry: Any, index: int, path: Path):
    """Yield (record id, calibration) for one usable calibration entry.

    Entries without an explicit positive factor or a string scope are skipped
    rather than fatal, matching ``curate_rewards.units_migration_catalog``.
    """

    if not isinstance(entry, dict):
        return
    factor = curate_rewards._decimal(entry.get("usd_conversion_factor"))
    if factor is None or factor <= 0:
        return
    scope = entry.get("scope")
    if not isinstance(scope, str):
        return
    for record_id in sorted(set(curate_rewards.RECORD_ID_RE.findall(scope))):
        yield record_id, {
            "source_unit_usd": curate_rewards._json_number(
                factor * curate_rewards.CANONICAL_UNIT_USD
            ),
            "canonical_factor": curate_rewards._json_number(factor),
            "evidence_ref": f"{path.as_posix()}#/records/{index}",
        }


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
