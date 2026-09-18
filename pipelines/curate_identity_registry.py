#!/usr/bin/env python3
"""Reviewed factory-registry loading for identity curation.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single File)
by responsibility; every name is re-exported from ``curate_identity`` so
existing ``curate_identity.X`` call sites and test seams resolve unchanged.

Row construction lives in ``curate_identity_registry_rows``.  This module
reads the registry bytes, refuses ``training_ready: true``, and pins the
reviewed table.  The process cache name ``_DEFAULT_REGISTRY`` stays on the
identity facade so publication-boundary tests can inject a reviewed table.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry")
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_json as _identity_json
    from . import curate_identity_registry_rows as _rows
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry"
    )
    import curate_identity_checks as _identity_checks
    import curate_identity_json as _identity_json
    import curate_identity_registry_rows as _rows

IdentityCurationError = _identity_json.IdentityCurationError
FactoryRow = _rows.FactoryRow
FactoryRegistry = _rows.FactoryRegistry

CONTRACT_REQUIRE_STATE = _rows.CONTRACT_REQUIRE_STATE
CONTRACT_SHAPE_DESIGNED = _rows.CONTRACT_SHAPE_DESIGNED
ALLOWED_CONTRACTS = _rows.ALLOWED_CONTRACTS

FACTORY_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "FACTORY-REGISTRY.json"
REGISTRY_SCHEMA_VERSION = _rows.REGISTRY_SCHEMA_VERSION
HOSTED_REGISTRY_SCHEMA_VERSION = _rows.HOSTED_REGISTRY_SCHEMA_VERSION
LEGACY_REGISTRY_SCHEMA_VERSION = _rows.LEGACY_REGISTRY_SCHEMA_VERSION
SUPPORTED_REGISTRY_SCHEMA_VERSIONS = _rows.SUPPORTED_REGISTRY_SCHEMA_VERSIONS
CANONICAL_PROVIDERS = _rows.CANONICAL_PROVIDERS
CHANNELS = _rows.CHANNELS
HOSTED_FRONTIER_PROFILE_ID = _rows.HOSTED_FRONTIER_PROFILE_ID
INTENDED_USES = _rows.INTENDED_USES
PROJECT_TRAINING_POLICIES = _rows.PROJECT_TRAINING_POLICIES
PROVIDERS = _rows.PROVIDERS
RIGHTS_AUTHORIZATIONS = _rows.RIGHTS_AUTHORIZATIONS
RIGHTS_CHANNELS = _rows.RIGHTS_CHANNELS
RIGHTS_PROFILE_IDS = _rows.RIGHTS_PROFILE_IDS
_RIGHTS_ROW_FIELDS = _rows._RIGHTS_ROW_FIELDS
_REQUIRED_ROW_FIELDS = _rows._REQUIRED_ROW_FIELDS
_REVIEWED_GENERATOR_RIGHTS = _rows._REVIEWED_GENERATOR_RIGHTS

_apply_field_rules = _rows._apply_field_rules
_PATH_RULES = _rows._PATH_RULES
_RIGHTS_VOCABULARY_RULES = _rows._RIGHTS_VOCABULARY_RULES
_SHAPE_RULES = _rows._SHAPE_RULES
_PREFERENCE_SIDE_RULES = _rows._PREFERENCE_SIDE_RULES
_generator_identity = _rows._generator_identity
_legacy_generator_identity = _rows._legacy_generator_identity
_require_reviewed_rights = _rows._require_reviewed_rights
_require_kind_contracts = _rows._require_kind_contracts
_require_preference_side_kinds = _rows._require_preference_side_kinds
_hosted_factory_row = _rows._hosted_factory_row
_parse_factory_row = _rows._parse_factory_row
_legacy_registry_row = _rows._legacy_registry_row
_source_policy = _rows._source_policy
_is_procedural_row = _rows._is_procedural_row
_registry_row_for_validation = _rows._registry_row_for_validation
_parse_procedural_row = _rows._parse_procedural_row

_DEFAULT_REGISTRY: FactoryRegistry | None = None


def _registry_payload(registry_path: Path) -> tuple[bytes, Mapping[str, Any]]:
    """Read the registry bytes and decode them strictly, refusing any training_ready: true."""

    try:
        raw_bytes = registry_path.read_bytes()
    except OSError as exc:
        raise IdentityCurationError(
            f"factory registry is unreadable: {registry_path}: {exc}"
        ) from exc
    try:
        payload = _identity_json._strict_json_loads(raw_bytes.decode("utf-8"))
    except ValueError as exc:
        raise IdentityCurationError(
            f"factory registry is not UTF-8 JSON: {registry_path}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise IdentityCurationError("factory registry must be a JSON object")
    _identity_json._reject_training_ready_true(payload)
    return raw_bytes, payload


def _require_registry_schema_version(payload: Mapping[str, Any]) -> str:
    schema_version = payload.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or schema_version not in SUPPORTED_REGISTRY_SCHEMA_VERSIONS
    ):
        raise IdentityCurationError(
            "factory registry schema_version must be one of "
            f"{sorted(SUPPORTED_REGISTRY_SCHEMA_VERSIONS)}"
        )
    return schema_version


def _require_registry_factories(payload: Mapping[str, Any]) -> list[Any]:
    if payload.get("lookup_key") != "path_id":
        raise IdentityCurationError("factory registry lookup_key must be path_id")
    factories = payload.get("factories")
    if not isinstance(factories, list) or not factories:
        raise IdentityCurationError("factory registry factories must be a non-empty list")
    return factories


def _registry_rows(payload: Mapping[str, Any]) -> tuple[str, list[Any]]:
    schema_version = _require_registry_schema_version(payload)
    factories = _require_registry_factories(payload)
    return schema_version, factories


def _parse_loaded_registry_row(raw_row: Any, index: int, schema_version: str) -> FactoryRow:
    if schema_version == REGISTRY_SCHEMA_VERSION and _rows._parity_policy().claims_parity_route(raw_row):
        return _rows._parse_parity_row(raw_row, index)
    if _is_procedural_row(raw_row, schema_version):
        return _parse_procedural_row(raw_row, index)
    row_payload = _registry_row_for_validation(raw_row, index, schema_version)
    return _parse_factory_row(row_payload, index)


def _record_registry_row(by_path_id: dict[str, FactoryRow], row: FactoryRow) -> None:
    if row.path_id in by_path_id:
        raise IdentityCurationError(f"duplicate registry path_id: {row.path_id}")
    by_path_id[row.path_id] = row


def load_registry(path: Path | None = None) -> FactoryRegistry:
    """Load reviewed registry bytes. Pin = SHA-256 of those exact bytes."""

    registry_path = Path(FACTORY_REGISTRY_PATH if path is None else path)
    raw_bytes, payload = _registry_payload(registry_path)
    schema_version, factories = _registry_rows(payload)
    by_path_id: dict[str, FactoryRow] = {}
    for index, raw_row in enumerate(factories):
        _record_registry_row(
            by_path_id, _parse_loaded_registry_row(raw_row, index, schema_version)
        )
    return FactoryRegistry(
        schema_version=schema_version,
        sha256=_identity_checks.sha256_bytes(raw_bytes),
        raw_bytes=raw_bytes,
        by_path_id=by_path_id,
    )


def _facade_registry_cache():
    """The identity facade owns ``_DEFAULT_REGISTRY`` so tests can inject it."""

    for name in ("curate_identity", "pipelines.curate_identity"):
        module = sys.modules.get(name)
        if module is not None and "_DEFAULT_REGISTRY" in vars(module):
            return module
    return sys.modules[__name__]


def default_registry() -> FactoryRegistry:
    """Return the committed reviewed registry, loaded once per process."""

    holder = _facade_registry_cache()
    cached = getattr(holder, "_DEFAULT_REGISTRY")
    if cached is None:
        cached = load_registry(FACTORY_REGISTRY_PATH)
        setattr(holder, "_DEFAULT_REGISTRY", cached)
    global _DEFAULT_REGISTRY
    _DEFAULT_REGISTRY = cached
    return cached


if __package__:
    _expose_package_sibling(__name__)
