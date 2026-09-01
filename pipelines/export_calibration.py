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
from typing import Any, TypeGuard

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

_NONNEGATIVE_RECORDS_ERROR = (
    "COMPOSE.json: calibration.records must be nonnegative"
)


def _decoded_utf8(payload: bytes, path: Path) -> str:
    """Decode pinned calibration bytes without replacing invalid input."""

    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExportError(f"calibration {path}: payload is not UTF-8: {exc}") from exc


def _parsed_calibration_document(text: str, path: Path) -> dict[str, Any]:
    """Parse one calibration object with strict finite, unique-key JSON."""

    try:
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_reject_nonfinite_json_float,
        )
    except (ValueError, RecursionError) as exc:
        raise ExportError(f"calibration {path}: invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise ExportError(f"calibration {path}: records must be a list")
    return document


def _calibration_records(document: dict[str, Any], path: Path) -> list[Any]:
    """Return the descriptor records after validating their container type."""

    records = document.get("records")
    if not isinstance(records, list):
        raise ExportError(f"calibration {path}: records must be a list")
    return records


def _add_calibration(
    catalog: dict[str, Any], record_id: str, calibration: Any, path: Path
) -> None:
    """Add one calibration while rejecting conflicting case-folded identities."""

    key = record_id.lower()
    previous = catalog.get(key)
    if previous is not None and previous != calibration:
        raise ExportError(
            f"calibration {path}: conflicting calibrations for {record_id}"
        )
    catalog[key] = calibration


def _load_calibration_payload(payload: bytes, path: Path) -> dict[str, Any]:
    """Load reward calibration from pinned bytes while preserving evidence labels."""

    document = _parsed_calibration_document(_decoded_utf8(payload, path), path)
    records = _calibration_records(document, path)

    catalog: dict[str, Any] = {}
    for index, entry in enumerate(records):
        for record_id, calibration in _entry_calibrations(
            entry, path=path, index=index
        ):
            _add_calibration(catalog, record_id, calibration, path)
    return catalog


def _is_complete_calibration_descriptor(
    descriptor: Any,
) -> TypeGuard[dict[str, Any]]:
    """Return whether the descriptor has the one accepted envelope shape."""

    required = {"mode", "path", "sha256", "records"}
    return isinstance(descriptor, dict) and set(descriptor) == required


def _nonnegative_record_count(value: Any) -> int:
    """Validate a descriptor count without accepting booleans as integers."""

    if isinstance(value, bool):
        raise ExportError(_NONNEGATIVE_RECORDS_ERROR)
    if not isinstance(value, int):
        raise ExportError(_NONNEGATIVE_RECORDS_ERROR)
    if value < 0:
        raise ExportError(_NONNEGATIVE_RECORDS_ERROR)
    return value


def _validated_calibration_descriptor(
    summary: dict[str, Any],
) -> tuple[dict[str, Any], Any, int]:
    """Validate the descriptor envelope and return (descriptor, mode, records)."""

    descriptor = summary.get("calibration")
    if not _is_complete_calibration_descriptor(descriptor):
        raise ExportError("COMPOSE.json: calibration descriptor is incomplete")
    records = _nonnegative_record_count(descriptor.get("records"))
    return descriptor, descriptor.get("mode"), records


def _absent_calibration_catalog(
    descriptor: dict[str, Any], source_root: Path
) -> dict[str, Any]:
    """The empty catalog for mode "none", provably still current."""

    if descriptor.get("path") is not None:
        raise ExportError("COMPOSE.json: absent calibration must not name a file")
    if descriptor.get("sha256") is not None:
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


def _descriptor_calibration_path(descriptor: dict[str, Any]) -> Path:
    """Return the absolute file path named by a file-backed descriptor."""

    raw_path = descriptor.get("path")
    if not isinstance(raw_path, str):
        raise ExportError("COMPOSE.json: calibration.path must be an absolute string")
    if not raw_path:
        raise ExportError("COMPOSE.json: calibration.path must be an absolute string")
    path = Path(raw_path)
    if not path.is_absolute():
        raise ExportError("COMPOSE.json: calibration.path must be absolute")
    return path


def _require_canonical_source_calibration(
    path: Path, mode: str, source_root: Path
) -> None:
    """Bind source-run mode to the canonical sidecar location."""

    if mode != "source_run":
        return
    canonical = source_root / compose_curated.FFPC_UNITS_MIGRATION
    if path != canonical:
        raise ExportError("COMPOSE.json: source-run calibration path is not canonical")


def _authenticated_calibration_payload(
    descriptor: dict[str, Any], path: Path
) -> bytes:
    """Read and authenticate the exact calibration bytes named by compose."""

    _path, payload = _read_exact_regular_file(
        path.parent, path.name, "COMPOSE calibration"
    )
    digest = hashlib.sha256(payload).hexdigest()
    if descriptor.get("sha256") != digest:
        raise ExportError("COMPOSE.json: calibration digest mismatch")
    return payload


def _file_calibration_catalog(
    descriptor: dict[str, Any], mode: str, source_root: Path
) -> dict[str, Any]:
    """The catalog rebuilt from the descriptor's authenticated file evidence."""

    path = _descriptor_calibration_path(descriptor)
    _require_canonical_source_calibration(path, mode, source_root)
    payload = _authenticated_calibration_payload(descriptor, path)
    return _load_calibration_payload(payload, path)


def _calibration_catalog_for_mode(
    descriptor: dict[str, Any], mode: Any, source_root: Path
) -> dict[str, Any]:
    """Rebuild the calibration catalog selected by the authenticated mode."""

    if mode == "none":
        return _absent_calibration_catalog(descriptor, source_root)
    if mode in {"source_run", "explicit"}:
        return _file_calibration_catalog(descriptor, mode, source_root)
    raise ExportError(f"COMPOSE.json: unsupported calibration mode {mode!r}")


def _require_authenticated_record_count(
    summary: dict[str, Any], catalog: dict[str, Any], records: int
) -> None:
    """Require descriptor, summary, and rebuilt catalog counts to agree."""

    if len(catalog) != records:
        raise ExportError("COMPOSE.json: calibrated record count does not authenticate")
    if summary.get("calibrated_records") != records:
        raise ExportError("COMPOSE.json: calibrated record count does not authenticate")


def _authenticated_calibration(
    summary: dict[str, Any], source_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    descriptor, mode, records = _validated_calibration_descriptor(summary)
    catalog = _calibration_catalog_for_mode(descriptor, mode, source_root)
    _require_authenticated_record_count(summary, catalog, records)
    return catalog, dict(descriptor)
