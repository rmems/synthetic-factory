#!/usr/bin/env python3
"""Factory-row construction for the identity factory registry.

Hosted, legacy, and procedural rows are validated here in refusal order:
field-rule tables first, then the reviewed-rights assignment, then
kind-contract and preference-side checks. ``curate_identity_registry``
loads bytes and pins the resulting table.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry_rows")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_registry_evidence as _evidence
    from . import curate_identity_registry_fields as _fields
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        DEEPSEEK_PLACEHOLDER_PROFILE_ID,
        HOSTED_FRONTIER_PROFILE_ID,
        NEMOTRON_PLACEHOLDER_PROFILE_ID,
        PROCEDURAL_PROFILE_ID,
        SIMULATOR_PROFILE_ID,
    )
    from .rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry_rows"
    )
    import curate_identity_json as _identity_json
    import curate_identity_registry_evidence as _evidence
    import curate_identity_registry_fields as _fields
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        DEEPSEEK_PLACEHOLDER_PROFILE_ID,
        HOSTED_FRONTIER_PROFILE_ID,
        NEMOTRON_PLACEHOLDER_PROFILE_ID,
        PROCEDURAL_PROFILE_ID,
        SIMULATOR_PROFILE_ID,
    )
    from rights_policy import (
        PROVIDERS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_CHANNELS,
    )

IdentityCurationError = _identity_json.IdentityCurationError
INTENDED_USES = _fields.INTENDED_USES
PROJECT_TRAINING_POLICIES = _fields.PROJECT_TRAINING_POLICIES
RIGHTS_PROFILE_IDS = _fields.RIGHTS_PROFILE_IDS

CONTRACT_REQUIRE_STATE = "require_state_claim"
CONTRACT_SHAPE_DESIGNED = "synthetic_shape_implies_designed"
ALLOWED_CONTRACTS = frozenset({CONTRACT_REQUIRE_STATE, CONTRACT_SHAPE_DESIGNED})

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
        ("fable-5", "fable-5"): ("anthropic", "consumer", HOSTED_FRONTIER_PROFILE_ID),
        ("gpt-5.6-sol", "gpt-5.6-sol"): ("openai", "consumer", HOSTED_FRONTIER_PROFILE_ID),
        ("grok-4.6", "grok-4.6"): ("xai", "consumer", HOSTED_FRONTIER_PROFILE_ID),
        ("muse-spark-1.2", "muse-spark-1.2"): ("meta", "api", HOSTED_FRONTIER_PROFILE_ID),
        ("procedural-attested", "1"): ("procedural", "local", PROCEDURAL_PROFILE_ID),
        ("relay-reflex-simulator", "1"): ("simulator", "local", SIMULATOR_PROFILE_ID),
        ("deepseek-placeholder", "pending-terms"): (
            "deepseek",
            "api",
            DEEPSEEK_PLACEHOLDER_PROFILE_ID,
        ),
        ("nemotron-placeholder", "pending-terms"): (
            "nemotron",
            "api",
            NEMOTRON_PLACEHOLDER_PROFILE_ID,
        ),
    }
)
if PROVIDERS != CANONICAL_PROVIDERS or RIGHTS_CHANNELS != CHANNELS:
    raise RuntimeError("loaded rights policy vocabulary drifted from sealed mapping")


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
    catalog_authorship: str | None = None
    generator_source_digest: str | None = None
    commit_sha: str | None = None
    module_digest: str | None = None


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
_require_profile_evidence = _evidence._require_profile_evidence


def _is_normalized_token(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _generator_identity(raw: Mapping[str, Any], index: int) -> tuple[str, str]:
    values: list[str] = []
    for field in ("generator", "generator_version"):
        value = raw[field]
        if not _is_normalized_token(value):
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


def _reviewed_assignment(identity: tuple[str, str], index: int) -> tuple[str, str, str]:
    expected_assignment = _REVIEWED_GENERATOR_RIGHTS.get(identity)
    if expected_assignment is None:
        raise IdentityCurationError(
            f"factories[{index}] has unknown reviewed (generator, generator_version)"
        )
    return expected_assignment


def _require_reviewed_provider_channel(
    raw: Mapping[str, Any], expected_assignment: tuple[str, str, str], index: int
) -> None:
    actual = (raw["provider"], raw["channel"], raw["rights_profile_id"])
    if actual != expected_assignment:
        raise IdentityCurationError(
            f"factories[{index}] generator/provider/channel assignment is not reviewed"
        )


def _require_reviewed_authorization(
    raw: Mapping[str, Any], expected_assignment: tuple[str, str, str], index: int
) -> None:
    authorization = RIGHTS_AUTHORIZATIONS.get(expected_assignment)
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


def _require_reviewed_rights(
    raw: Mapping[str, Any], identity: tuple[str, str], index: int
) -> None:
    """The row's rights fields must be the reviewed assignment the loaded policy authorizes."""

    expected_assignment = _reviewed_assignment(identity, index)
    _require_reviewed_provider_channel(raw, expected_assignment, index)
    _require_reviewed_authorization(raw, expected_assignment, index)
    _require_profile_evidence(raw, index)


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
        catalog_authorship=raw.get("catalog_authorship"),
        generator_source_digest=raw.get("generator_source_digest"),
        commit_sha=raw.get("commit_sha"),
        module_digest=raw.get("module_digest"),
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


def _legacy_reviewed_authorization(
    generator: str, generator_version: str, index: int
):
    expected_assignment = _reviewed_assignment((generator, generator_version), index)
    provider, channel, profile_id = expected_assignment
    if profile_id != HOSTED_FRONTIER_PROFILE_ID:
        raise IdentityCurationError(
            f"factories[{index}] v0.1 rows cannot carry non-hosted rights profiles"
        )
    authorization = RIGHTS_AUTHORIZATIONS.get(
        (provider, channel, HOSTED_FRONTIER_PROFILE_ID)
    )
    if authorization is None:
        raise IdentityCurationError(
            f"factories[{index}] reviewed rights assignment is not authorized by policy"
        )
    return (provider, channel), authorization


def _legacy_registry_row(raw: Any, index: int) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise IdentityCurationError(f"factories[{index}] must be an object")
    unexpected = [field for field in _RIGHTS_ROW_FIELDS if field in raw]
    if unexpected:
        raise IdentityCurationError(
            f"factories[{index}] v0.1 rows must not declare rights fields: {unexpected}"
        )
    generator, generator_version = _legacy_generator_identity(raw, index)
    expected_assignment, authorization = _legacy_reviewed_authorization(
        generator, generator_version, index
    )
    augmented = dict(raw)
    augmented.update(
        provider=expected_assignment[0],
        channel=expected_assignment[1],
        rights_profile_id=HOSTED_FRONTIER_PROFILE_ID,
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


if __package__:
    _expose_package_sibling(__name__)
