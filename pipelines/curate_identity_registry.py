#!/usr/bin/env python3
"""Reviewed factory-registry loading and row validation for identity curation.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single File)
by responsibility; every name is re-exported from ``curate_identity`` so
existing ``curate_identity.X`` call sites and test seams resolve unchanged.

The registry is the identity authority.  A hosted row needs a reviewed
registry row *and* a matching ``(generator, generator_version)`` entry in
``_REVIEWED_GENERATOR_RIGHTS``; the loader rejects one without the other and
raises on the first invalid field, in the order the ``_*_RULES`` tables list
them.  The procedural route keeps its separate, independently sealed
authority in ``code_repair.source_policy``.  Every refusal raises at load so
an invalid registry stops the run before any record is curated.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry")
    from . import curate_identity_checks as _identity_checks
    from . import curate_identity_json as _identity_json
    from . import curate_identity_registry_fields as _fields
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        HOSTED_FRONTIER_PROFILE_ID,
    )
    from .rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry"
    )
    import curate_identity_checks as _identity_checks
    import curate_identity_json as _identity_json
    import curate_identity_registry_fields as _fields
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        HOSTED_FRONTIER_PROFILE_ID,
    )
    from rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
    )

IdentityCurationError = _identity_json.IdentityCurationError

CONTRACT_REQUIRE_STATE = "require_state_claim"
CONTRACT_SHAPE_DESIGNED = "synthetic_shape_implies_designed"
ALLOWED_CONTRACTS = frozenset({CONTRACT_REQUIRE_STATE, CONTRACT_SHAPE_DESIGNED})

FACTORY_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "FACTORY-REGISTRY.json"
REGISTRY_SCHEMA_VERSION = "factory-registry-v0.3"
HOSTED_REGISTRY_SCHEMA_VERSION = "factory-registry-v0.2"
LEGACY_REGISTRY_SCHEMA_VERSION = "factory-registry-v0.1"
SUPPORTED_REGISTRY_SCHEMA_VERSIONS = frozenset(
    {LEGACY_REGISTRY_SCHEMA_VERSION, HOSTED_REGISTRY_SCHEMA_VERSION, REGISTRY_SCHEMA_VERSION}
)
_RIGHTS_ROW_FIELDS = (
    "provider",
    "channel",
    "rights_profile_id",
    "intended_use",
    "project_training_policy",
)
_REQUIRED_ROW_FIELDS = (
    "path_id",
    "payload_factory",
    "generator",
    "generator_version",
    *_RIGHTS_ROW_FIELDS,
    "record_kinds",
    "identity_authoritative",
    "publication_target",
    "training_ready_policy",
    "allowed_curation_lanes",
    "provenance_contract_by_kind",
)

_REVIEWED_GENERATOR_RIGHTS = MappingProxyType(
    {
        ("fable-5", "fable-5"): ("anthropic", "consumer"),
        ("gpt-5.6-sol", "gpt-5.6-sol"): ("openai", "consumer"),
        ("grok-4.6", "grok-4.6"): ("xai", "consumer"),
        ("muse-spark-1.2", "muse-spark-1.2"): ("meta", "api"),
    }
)
if PROVIDERS != CANONICAL_PROVIDERS or RIGHTS_CHANNELS != CHANNELS:
    raise RuntimeError("loaded rights policy vocabulary drifted from sealed mapping")

_DEFAULT_REGISTRY: FactoryRegistry | None = None


class FactoryRow(NamedTuple):
    path_id: str
    payload_factory: str
    generator: str
    generator_version: str
    provider: str | None
    channel: str | None
    rights_profile_id: str
    intended_use: str
    project_training_policy: str
    record_kinds: frozenset[str]
    identity_authoritative: bool
    publication_target: str | None
    training_ready_policy: str
    allowed_curation_lanes: tuple[str, ...]
    provenance_contract_by_kind: Mapping[str, str]
    preference_side_kinds: frozenset[str] = frozenset()
    source_type: str = "hosted"
    generator_ownership: str | None = None
    generation_method: str | None = None
    source_license_evidence: Mapping[str, str] | None = None
    procedural_policy_sha256: str | None = None
    catalog_id: str | None = None
    catalog_sha256: str | None = None
    programs_sha256: str | None = None


@dataclass(frozen=True)
class FactoryRegistry:
    """Reviewed factory table plus the exact bytes that pin a cleaned tree."""

    schema_version: str
    sha256: str
    raw_bytes: bytes
    by_path_id: Mapping[str, FactoryRow]


_apply_field_rules = _fields._apply_field_rules
_PATH_RULES = _fields._PATH_RULES
_RIGHTS_VOCABULARY_RULES = _fields._RIGHTS_VOCABULARY_RULES
_SHAPE_RULES = _fields._SHAPE_RULES
_PREFERENCE_SIDE_RULES = _fields._PREFERENCE_SIDE_RULES


def _generator_identity(raw: Mapping[str, Any], index: int) -> tuple[str, str]:
    values: list[str] = []
    for field in ("generator", "generator_version"):
        value = raw[field]
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
        ):
            raise IdentityCurationError(
                f"factories[{index}].{field} must be a non-empty normalized string"
            )
        values.append(value)
    return values[0], values[1]


def _legacy_generator_identity(
    raw: Mapping[str, Any], index: int
) -> tuple[str, str]:
    missing = [
        field for field in ("generator", "generator_version") if field not in raw
    ]
    if missing:
        raise IdentityCurationError(
            f"factories[{index}] missing fields: {missing}"
        )
    return _generator_identity(raw, index)


def _require_reviewed_rights(
    raw: Mapping[str, Any], identity: tuple[str, str], index: int
) -> None:
    """The row's rights fields must be the reviewed assignment the loaded policy authorizes."""

    expected_assignment = _REVIEWED_GENERATOR_RIGHTS.get(identity)
    if expected_assignment is None:
        raise IdentityCurationError(
            f"factories[{index}] has unknown reviewed (generator, generator_version)"
        )
    if (raw["provider"], raw["channel"]) != expected_assignment:
        raise IdentityCurationError(
            f"factories[{index}] generator/provider/channel assignment is not reviewed"
        )
    authorization = RIGHTS_AUTHORIZATIONS.get((*expected_assignment, raw["rights_profile_id"]))
    if authorization is None:
        raise IdentityCurationError(
            f"factories[{index}] rights fields are not authorized by loaded policy"
        )
    if (
        raw["intended_use"] != authorization.intended_use
        or raw["project_training_policy"] != authorization.project_training_policy
    ):
        raise IdentityCurationError(
            f"factories[{index}] rights fields drift from loaded policy"
        )


def _require_kind_contracts(raw: Mapping[str, Any], kinds: frozenset[str], index: int) -> None:
    contracts = raw["provenance_contract_by_kind"]
    for kind in kinds:
        contract = contracts.get(kind)
        if contract not in ALLOWED_CONTRACTS:
            raise IdentityCurationError(
                f"factories[{index}] missing allowed provenance_contract for {kind}"
            )
        if contract == CONTRACT_SHAPE_DESIGNED and not raw["identity_authoritative"]:
            raise IdentityCurationError(
                f"factories[{index}] synthetic_shape_implies_designed requires "
                "identity_authoritative"
            )


def _require_preference_side_kinds(
    raw: Mapping[str, Any], kinds: frozenset[str], index: int
) -> None:
    if "preference" in kinds:
        _apply_field_rules({"preference_side_kinds": raw.get("preference_side_kinds")},
                           _PREFERENCE_SIDE_RULES, index)
    elif raw.get("preference_side_kinds") is not None:
        raise IdentityCurationError(
            f"factories[{index}].preference_side_kinds requires preference authority"
        )


def _hosted_factory_row(raw: Mapping[str, Any], identity: tuple[str, str]) -> FactoryRow:
    contracts = raw["provenance_contract_by_kind"]
    return FactoryRow(
        path_id=raw["path_id"],
        payload_factory=raw["payload_factory"],
        generator=identity[0],
        generator_version=identity[1],
        provider=raw["provider"],
        channel=raw["channel"],
        rights_profile_id=raw["rights_profile_id"],
        intended_use=raw["intended_use"],
        project_training_policy=raw["project_training_policy"],
        record_kinds=frozenset(raw["record_kinds"]),
        identity_authoritative=raw["identity_authoritative"],
        publication_target=raw["publication_target"],
        training_ready_policy=raw["training_ready_policy"],
        allowed_curation_lanes=tuple(raw["allowed_curation_lanes"]),
        provenance_contract_by_kind={str(key): str(value) for key, value in contracts.items()},
        preference_side_kinds=frozenset(raw.get("preference_side_kinds") or ()),
    )


def _parse_factory_row(raw: Any, index: int) -> FactoryRow:
    if not isinstance(raw, Mapping):
        raise IdentityCurationError(f"factories[{index}] must be an object")
    missing = [key for key in _REQUIRED_ROW_FIELDS if key not in raw]
    if missing:
        raise IdentityCurationError(f"factories[{index}] missing fields: {missing}")
    _apply_field_rules(raw, _PATH_RULES, index)
    identity = _generator_identity(raw, index)
    _apply_field_rules(raw, _RIGHTS_VOCABULARY_RULES, index)
    _require_reviewed_rights(raw, identity, index)
    _apply_field_rules(raw, _SHAPE_RULES, index)
    kinds = frozenset(raw["record_kinds"])
    _require_kind_contracts(raw, kinds, index)
    _require_preference_side_kinds(raw, kinds, index)
    return _hosted_factory_row(raw, identity)


def _legacy_registry_row(raw: Any, index: int) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise IdentityCurationError(f"factories[{index}] must be an object")
    unexpected = [field for field in _RIGHTS_ROW_FIELDS if field in raw]
    if unexpected:
        raise IdentityCurationError(
            f"factories[{index}] v0.1 rows must not declare rights fields: {unexpected}"
        )
    generator, generator_version = _legacy_generator_identity(raw, index)
    expected_assignment = _REVIEWED_GENERATOR_RIGHTS.get(
        (generator, generator_version)
    )
    if expected_assignment is None:
        raise IdentityCurationError(
            f"factories[{index}] has unknown reviewed (generator, generator_version)"
        )
    profile_id = HOSTED_FRONTIER_PROFILE_ID
    authorization = RIGHTS_AUTHORIZATIONS.get((*expected_assignment, profile_id))
    if authorization is None:
        raise IdentityCurationError(
            f"factories[{index}] reviewed rights assignment is not authorized by policy"
        )
    augmented = dict(raw)
    augmented.update(
        provider=expected_assignment[0],
        channel=expected_assignment[1],
        rights_profile_id=profile_id,
        intended_use=authorization.intended_use,
        project_training_policy=authorization.project_training_policy,
    )
    return augmented


def _source_policy():
    """The procedural route's separately sealed authority, bound lazily as before."""

    if __package__:
        from .code_repair import source_policy
    else:
        from code_repair import source_policy
    return source_policy


def _is_procedural_row(raw: Any, schema_version: str) -> bool:
    if schema_version != REGISTRY_SCHEMA_VERSION:
        return False
    return isinstance(raw, Mapping) and raw.get("source_type") == "procedural"


def _registry_row_for_validation(
    raw: Any, index: int, schema_version: str
) -> Any:
    if _source_policy().claims_procedural_route(raw):
        raise IdentityCurationError(f"factories[{index}] procedural fields require v0.3 route")
    if schema_version == LEGACY_REGISTRY_SCHEMA_VERSION:
        return _legacy_registry_row(raw, index)
    return raw


def _parse_procedural_row(raw: Any, index: int) -> FactoryRow:
    policy = _source_policy()
    try:
        policy.validate_registry_row(raw)
    except policy.SourcePolicyError as exc:
        raise IdentityCurationError(f"factories[{index}]: {exc}") from exc
    return FactoryRow(
        path_id=raw["path_id"], payload_factory=raw["payload_factory"],
        generator=raw["generator"], generator_version=raw["generator_version"],
        provider=None, channel=None, rights_profile_id=policy.POLICY["policy_id"],
        intended_use=raw["intended_use"], project_training_policy=raw["project_training_policy"],
        record_kinds=frozenset(raw["record_kinds"]), identity_authoritative=True,
        publication_target=None, training_ready_policy=raw["training_ready_policy"],
        allowed_curation_lanes=tuple(raw["allowed_curation_lanes"]),
        provenance_contract_by_kind=MappingProxyType(dict(raw["provenance_contract_by_kind"])),
        source_type="procedural", generator_ownership=raw["generator_ownership"],
        generation_method=raw["generation_method"],
        source_license_evidence=MappingProxyType(dict(raw["source_license_evidence"])),
        procedural_policy_sha256=raw["procedural_policy_sha256"], catalog_id=raw["catalog_id"],
        catalog_sha256=raw["catalog_sha256"], programs_sha256=raw["programs_sha256"],
    )


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


def _registry_rows(payload: Mapping[str, Any]) -> tuple[str, list[Any]]:
    schema_version = payload.get("schema_version")
    if (
        not isinstance(schema_version, str)
        or schema_version not in SUPPORTED_REGISTRY_SCHEMA_VERSIONS
    ):
        raise IdentityCurationError(
            "factory registry schema_version must be one of "
            f"{sorted(SUPPORTED_REGISTRY_SCHEMA_VERSIONS)}"
        )
    if payload.get("lookup_key") != "path_id":
        raise IdentityCurationError("factory registry lookup_key must be path_id")
    factories = payload.get("factories")
    if not isinstance(factories, list) or not factories:
        raise IdentityCurationError("factory registry factories must be a non-empty list")
    return schema_version, factories


def load_registry(path: Path | None = None) -> FactoryRegistry:
    """Load reviewed registry bytes. Pin = SHA-256 of those exact bytes."""

    registry_path = Path(FACTORY_REGISTRY_PATH if path is None else path)
    raw_bytes, payload = _registry_payload(registry_path)
    schema_version, factories = _registry_rows(payload)
    by_path_id: dict[str, FactoryRow] = {}
    for index, raw_row in enumerate(factories):
        if _is_procedural_row(raw_row, schema_version):
            row = _parse_procedural_row(raw_row, index)
        else:
            row_payload = _registry_row_for_validation(raw_row, index, schema_version)
            row = _parse_factory_row(row_payload, index)
        if row.path_id in by_path_id:
            raise IdentityCurationError(f"duplicate registry path_id: {row.path_id}")
        by_path_id[row.path_id] = row
    return FactoryRegistry(
        schema_version=schema_version,
        sha256=_identity_checks.sha256_bytes(raw_bytes),
        raw_bytes=raw_bytes,
        by_path_id=by_path_id,
    )


def default_registry() -> FactoryRegistry:
    """Return the committed reviewed registry, loaded once per process."""

    global _DEFAULT_REGISTRY
    for name in ("curate_identity", "pipelines.curate_identity"):
        module = sys.modules.get(name)
        if module is None or module is sys.modules[__name__]:
            continue
        cached = getattr(module, "_DEFAULT_REGISTRY", None)
        if cached is not None:
            return cached
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = load_registry(FACTORY_REGISTRY_PATH)
    return _DEFAULT_REGISTRY


if __package__:
    _expose_package_sibling(__name__)
