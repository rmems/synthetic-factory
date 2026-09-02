#!/usr/bin/env python3
"""Import bootstrap for the stable ``compose_curated`` compatibility facade."""

from __future__ import annotations

import importlib
import sys
from typing import Any


def _prepare_facade_identity(package: str | None) -> None:
    package_api = sys.modules.get(package or "pipelines")
    if package:
        getattr(package_api, "_assert_direct_sibling")("compose_curated")
        return
    getattr(package_api, "_join_package_sibling", lambda name: None)("compose_curated")


def _facade_import_order(package: str | None) -> list[str]:
    if package:
        return """
        compose_mill curate_agentic curate_bridge curate_coding curate_identity
        curate_preferences curate_rewards training_audit compose_contract
        compose_curated_calibration compose_curated_coding compose_curated_identity
        compose_curated_identity_facade compose_curated_record_facade
        compose_curated_record compose_curated_run compose_curated_run_facade
        compose_destination compose_trajectory check_records census record_kind round_txn
        """.split()
    return """
        compose_contract compose_curated_calibration compose_curated_coding
        compose_curated_identity compose_curated_identity_facade
        compose_curated_record_facade compose_curated_record compose_curated_run
        compose_curated_run_facade compose_destination compose_mill compose_trajectory
        curate_agentic curate_bridge curate_coding curate_identity curate_preferences
        curate_rewards training_audit check_records census record_kind round_txn
        """.split()


def _optional_trajectory_module(package: str | None, prefix: str):
    optional_name = f"{prefix}curate_trajectory_preferences"
    allowed_missing = {"curate_trajectory_preferences", f"{package}.curate_trajectory_preferences"}
    try:
        return importlib.import_module(optional_name), allowed_missing
    except ModuleNotFoundError as missing_import:
        if missing_import.name not in allowed_missing:
            raise
        return None, allowed_missing


def bootstrap_facade_imports(package: str | None) -> dict[str, Any]:
    """Load facade dependencies in their canonical direct/package order."""

    _prepare_facade_identity(package)
    prefix = f"{package}." if package else ""
    modules = {
        name: importlib.import_module(f"{prefix}{name}") for name in _facade_import_order(package)
    }
    modules["curate_trajectory_preferences"], allowed_missing = _optional_trajectory_module(
        package, prefix
    )
    modules["allowed_missing"] = allowed_missing
    return modules


getattr(sys.modules.get(__package__), "_expose_package_sibling", lambda name: None)(__name__)
