#!/usr/bin/env python3
"""Import bootstrap for the stable ``compose_curated`` compatibility facade."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any, Callable


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


# Every facade dependency is imported through a literal module name, in both
# the direct-CLI and the package spelling.  The allow-list is the table itself:
# a name that is not declared here cannot be imported by the facade.
_FACADE_LOADERS: dict[str, tuple[Callable[[], ModuleType], Callable[[str], ModuleType]]] = {
    "compose_mill": (
        lambda: importlib.import_module("compose_mill"),
        lambda package: importlib.import_module(".compose_mill", package),
    ),
    "curate_agentic": (
        lambda: importlib.import_module("curate_agentic"),
        lambda package: importlib.import_module(".curate_agentic", package),
    ),
    "curate_bridge": (
        lambda: importlib.import_module("curate_bridge"),
        lambda package: importlib.import_module(".curate_bridge", package),
    ),
    "curate_coding": (
        lambda: importlib.import_module("curate_coding"),
        lambda package: importlib.import_module(".curate_coding", package),
    ),
    "curate_identity": (
        lambda: importlib.import_module("curate_identity"),
        lambda package: importlib.import_module(".curate_identity", package),
    ),
    "curate_preferences": (
        lambda: importlib.import_module("curate_preferences"),
        lambda package: importlib.import_module(".curate_preferences", package),
    ),
    "curate_rewards": (
        lambda: importlib.import_module("curate_rewards"),
        lambda package: importlib.import_module(".curate_rewards", package),
    ),
    "training_audit": (
        lambda: importlib.import_module("training_audit"),
        lambda package: importlib.import_module(".training_audit", package),
    ),
    "compose_contract": (
        lambda: importlib.import_module("compose_contract"),
        lambda package: importlib.import_module(".compose_contract", package),
    ),
    "compose_curated_calibration": (
        lambda: importlib.import_module("compose_curated_calibration"),
        lambda package: importlib.import_module(".compose_curated_calibration", package),
    ),
    "compose_curated_coding": (
        lambda: importlib.import_module("compose_curated_coding"),
        lambda package: importlib.import_module(".compose_curated_coding", package),
    ),
    "compose_curated_identity": (
        lambda: importlib.import_module("compose_curated_identity"),
        lambda package: importlib.import_module(".compose_curated_identity", package),
    ),
    "compose_curated_identity_facade": (
        lambda: importlib.import_module("compose_curated_identity_facade"),
        lambda package: importlib.import_module(".compose_curated_identity_facade", package),
    ),
    "compose_curated_record_facade": (
        lambda: importlib.import_module("compose_curated_record_facade"),
        lambda package: importlib.import_module(".compose_curated_record_facade", package),
    ),
    "compose_curated_record": (
        lambda: importlib.import_module("compose_curated_record"),
        lambda package: importlib.import_module(".compose_curated_record", package),
    ),
    "compose_curated_run": (
        lambda: importlib.import_module("compose_curated_run"),
        lambda package: importlib.import_module(".compose_curated_run", package),
    ),
    "compose_curated_run_facade": (
        lambda: importlib.import_module("compose_curated_run_facade"),
        lambda package: importlib.import_module(".compose_curated_run_facade", package),
    ),
    "compose_destination": (
        lambda: importlib.import_module("compose_destination"),
        lambda package: importlib.import_module(".compose_destination", package),
    ),
    "compose_trajectory": (
        lambda: importlib.import_module("compose_trajectory"),
        lambda package: importlib.import_module(".compose_trajectory", package),
    ),
    "check_records": (
        lambda: importlib.import_module("check_records"),
        lambda package: importlib.import_module(".check_records", package),
    ),
    "census": (
        lambda: importlib.import_module("census"),
        lambda package: importlib.import_module(".census", package),
    ),
    "record_kind": (
        lambda: importlib.import_module("record_kind"),
        lambda package: importlib.import_module(".record_kind", package),
    ),
    "round_txn": (
        lambda: importlib.import_module("round_txn"),
        lambda package: importlib.import_module(".round_txn", package),
    ),
    "curate_trajectory_preferences": (
        lambda: importlib.import_module("curate_trajectory_preferences"),
        lambda package: importlib.import_module(".curate_trajectory_preferences", package),
    ),
}


def _import_facade_module(name: str, package: str | None) -> ModuleType:
    """Import one allow-listed facade dependency in the requested import mode."""

    direct_loader, package_loader = _FACADE_LOADERS[name]
    return package_loader(package) if package else direct_loader()


def _optional_trajectory_module(package: str | None):
    allowed_missing = {"curate_trajectory_preferences", f"{package}.curate_trajectory_preferences"}
    try:
        return _import_facade_module("curate_trajectory_preferences", package), allowed_missing
    except ModuleNotFoundError as missing_import:
        if missing_import.name not in allowed_missing:
            raise
        return None, allowed_missing


def bootstrap_facade_imports(package: str | None) -> dict[str, Any]:
    """Load facade dependencies in their canonical direct/package order."""

    _prepare_facade_identity(package)
    modules = {name: _import_facade_module(name, package) for name in _facade_import_order(package)}
    modules["curate_trajectory_preferences"], allowed_missing = _optional_trajectory_module(package)
    modules["allowed_missing"] = allowed_missing
    return modules


getattr(sys.modules.get(__package__), "_expose_package_sibling", lambda name: None)(__name__)
