#!/usr/bin/env python3
"""Calibration loading and compact audit reporting for curated composition."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated_calibration", allow_initializing=True):
        import compose_curated_calibration as _direct_compose_curated_calibration

        _require_local_sibling(
            _direct_compose_curated_calibration,
            "compose_curated_calibration",
        )
        del _direct_compose_curated_calibration
    from .compose_contract import (
        ComposeError,
        FFPC_UNITS_MIGRATION,
        REASON_EMPTY_CORPUS,
        RECORDS_DIRNAME,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_calibration"
    )
    from compose_contract import (
        ComposeError,
        FFPC_UNITS_MIGRATION,
        REASON_EMPTY_CORPUS,
        RECORDS_DIRNAME,
    )


@dataclass(frozen=True)
class CalibrationContext:
    """Immutable inputs used to select one calibration document."""

    source_run: Path
    units_migration: Path | None


@dataclass(frozen=True)
class CalibrationServices:
    """Call boundaries supplied by the ``compose_curated`` facade.

    Supplying these collaborators at each facade call preserves its historical
    monkeypatch seams while this module remains independent of that facade.
    """

    read_exact_child_file: Callable[..., tuple[Path, bytes]]
    reject_duplicate_object_keys: Callable[..., Any]
    reject_json_constant: Callable[[str], Any]
    parse_finite_json_float: Callable[[str], Any]
    units_migration_catalog: Callable[[Any, Path], dict[str, Any]]
    sha256_hex: Callable[[bytes], str]
    audit_run: Callable[[Path], Mapping[str, Any]]


def _calibration_path(context: CalibrationContext) -> tuple[Path | None, str]:
    """Select explicit, canonical, or absent calibration evidence."""

    if context.units_migration is not None:
        return Path(os.path.abspath(context.units_migration)), "explicit"
    default = context.source_run / FFPC_UNITS_MIGRATION
    if default.is_file():
        return default, "source_run"
    if os.path.lexists(default):
        raise ComposeError(
            f"default calibration evidence is not an exact regular file: {default}"
        )
    return None, "none"


def _decode_calibration(
    calibration_path: Path, payload: bytes, services: CalibrationServices
) -> Any:
    """Decode finite, duplicate-free calibration JSON."""

    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=services.reject_duplicate_object_keys,
            parse_constant=services.reject_json_constant,
            parse_float=services.parse_finite_json_float,
        )
    except ValueError as exc:
        raise ComposeError(
            f"{calibration_path}: invalid calibration JSON: {exc}"
        ) from exc


def load_calibration(
    context: CalibrationContext, services: CalibrationServices
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load calibration plus the exact file evidence needed for replay."""

    calibration_path, mode = _calibration_path(context)
    if calibration_path is None:
        return {}, {"mode": mode, "path": None, "sha256": None, "records": 0}
    calibration_path, payload = services.read_exact_child_file(
        calibration_path.parent,
        calibration_path.name,
        "units-migration calibration",
    )
    document = _decode_calibration(calibration_path, payload, services)
    catalog = services.units_migration_catalog(document, calibration_path)
    return catalog, {
        "mode": mode,
        "path": str(calibration_path),
        "sha256": services.sha256_hex(payload),
        "records": len(catalog),
    }


def compact_audit_report(
    report: Mapping[str, Any] | None, record_count: int
) -> dict[str, Any]:
    """Return the compact audit declaration stored in ``COMPOSE.json``."""

    if record_count == 0:
        return {
            "run_dir": RECORDS_DIRNAME,
            "records": 0,
            "training_ready": False,
            "blockers": [REASON_EMPTY_CORPUS],
        }
    if report is None:
        raise ComposeError("nonempty compact audit requires an audit report")
    return {
        "run_dir": RECORDS_DIRNAME,
        "records": report["totals"]["records"],
        "training_ready": bool(report["training_ready"]),
        "blockers": list(report["blockers"]),
        "identity_coverage_pct": report["identity"]["coverage_pct"],
        "provenance_canonical_pct": report["provenance"]["canonical_pct"],
        "preference_context_purity_pct": report["preferences"]["context_purity_pct"],
    }


def audit_records(
    records_dir: Path, record_count: int, services: CalibrationServices
) -> dict[str, Any]:
    """Audit curated payload and refuse to call an empty corpus ready."""

    report = services.audit_run(records_dir) if record_count else None
    return compact_audit_report(report, record_count)


__all__ = [
    "CalibrationContext",
    "CalibrationServices",
    "audit_records",
    "compact_audit_report",
    "load_calibration",
]


if __package__:
    _expose_package_sibling(__name__)
