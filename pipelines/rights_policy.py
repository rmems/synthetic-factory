#!/usr/bin/env python3
"""Strict loading and semantic validation for rights-policy v1."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from types import MappingProxyType

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy")
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        MAPPING_PATH,
        MAPPING_VERSION,
        POLICY_DOCUMENT_TYPE,
        POLICY_VERSION,
        PROJECT_TRAINING_POLICIES,
        REQUIRED_PROFILE_IDS,
        UNKNOWN_PROVENANCE_PROFILE_ID,
        RightsPolicyError,
        freeze_json,
        parse_strict_json_bytes,
        policy_error,
        reject_unpaired_surrogates,
        require_nonempty_string,
        require_unique_strings,
        sha256_digest,
    )
    from .rights_policy_validation import _catalogue_ids, _exact_object, _validate_rules
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy"
    )
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        MAPPING_PATH,
        MAPPING_VERSION,
        POLICY_DOCUMENT_TYPE,
        POLICY_VERSION,
        PROJECT_TRAINING_POLICIES,
        REQUIRED_PROFILE_IDS,
        UNKNOWN_PROVENANCE_PROFILE_ID,
        RightsPolicyError,
        freeze_json,
        parse_strict_json_bytes,
        policy_error,
        reject_unpaired_surrogates,
        require_nonempty_string,
        require_unique_strings,
        sha256_digest,
    )
    from rights_policy_validation import _catalogue_ids, _exact_object, _validate_rules


_TOP_LEVEL_FIELDS = frozenset({
    "document_type", "policy_version", "mapping_version", "vocabularies",
    "evidence_status_fields", "invariants", "required_profile_ids",
    "reason_codes", "profiles", "rules",
})
_VOCABULARY_FIELDS = frozenset({
    "providers", "channels", "intended_use", "project_training_policy",
    "evidence_status",
})
_PROFILE_FIELDS = frozenset({
    "id", "intended_use", "project_training_policy", "evidence_statuses",
    "reason_codes",
})
_INTENDED_USE_POLICY = {
    "research_only": "blocked",
    "training_candidate": "allowed",
}
_POLICY_LABEL = "rights policy"


def _exact_vocabulary(
    vocabularies: dict,
    name: str,
    required: frozenset[str],
    where: str,
) -> tuple[str, ...]:
    values = require_unique_strings(vocabularies.get(name), name, where=where)
    if set(values) != set(required):
        raise policy_error(where, f"{name} must declare exactly {sorted(required)}")
    return values


def _validate_identity(document: object, where: str) -> dict:
    checked = _exact_object(document, _TOP_LEVEL_FIELDS, _POLICY_LABEL, where)
    identities = (
        ("document_type", POLICY_DOCUMENT_TYPE),
        ("policy_version", POLICY_VERSION),
        ("mapping_version", MAPPING_VERSION),
    )
    for field, expected in identities:
        if checked.get(field) != expected:
            raise policy_error(where, f"unknown {field}")
    return checked


def _validate_vocabularies(document: dict, where: str) -> None:
    vocabularies = _exact_object(
        document.get("vocabularies"),
        _VOCABULARY_FIELDS,
        "vocabularies",
        where,
    )
    for name, required in (
        ("providers", CANONICAL_PROVIDERS),
        ("channels", CHANNELS),
        ("intended_use", INTENDED_USES),
        ("project_training_policy", PROJECT_TRAINING_POLICIES),
        ("evidence_status", EVIDENCE_STATUSES),
    ):
        _exact_vocabulary(vocabularies, name, required, where)

    status_fields = require_unique_strings(
        document.get("evidence_status_fields"),
        "evidence_status_fields",
        where=where,
    )
    if status_fields != EVIDENCE_STATUS_FIELDS:
        raise policy_error(
            where,
            f"evidence_status_fields must be exactly {list(EVIDENCE_STATUS_FIELDS)}",
        )
    invariants = _exact_object(
        document.get("invariants"),
        frozenset({"provider_training_status"}),
        "invariants",
        where,
    )
    if invariants["provider_training_status"] != "evidence_only":
        raise policy_error(
            where,
            "provider_training_status must be evidence_only",
        )


def _validate_reason_catalogue(document: dict, where: str) -> frozenset[str]:
    reason_ids = _catalogue_ids(
        document.get("reason_codes"),
        "reason_codes",
        frozenset({"id", "description"}),
        where,
    )
    for entry in document["reason_codes"]:
        require_nonempty_string(entry.get("description"), "description", where=where)
    return frozenset(reason_ids)


def _validate_profile(
    profile: dict,
    reason_ids: frozenset[str],
    where: str,
) -> None:
    profile_id = profile["id"]
    _validate_profile_decision(profile, profile_id, where)
    _validate_profile_statuses(profile, profile_id, where)
    _validate_profile_reasons(profile, profile_id, reason_ids, where)


def _validate_profile_decision(profile: dict, profile_id: str, where: str) -> None:
    intended_use = _profile_value(profile, "intended_use", INTENDED_USES, where)
    project_policy = _profile_value(
        profile,
        "project_training_policy",
        PROJECT_TRAINING_POLICIES,
        where,
    )
    if _INTENDED_USE_POLICY[intended_use] != project_policy:
        raise policy_error(
            where,
            f"profile {profile_id!r} has inconsistent intended_use and project policy",
        )


def _profile_value(
    profile: dict, field_name: str, vocabulary: frozenset[str], where: str
) -> str:
    value = profile.get(field_name)
    if not isinstance(value, str) or value not in vocabulary:
        raise policy_error(
            where,
            f"profile {profile['id']!r} has unknown {field_name}",
        )
    return value


def _validate_profile_statuses(profile: dict, profile_id: str, where: str) -> None:
    statuses = profile.get("evidence_statuses")
    if not isinstance(statuses, dict):
        raise policy_error(
            where,
            f"profile {profile_id!r} evidence status fields must be exactly "
            f"{list(EVIDENCE_STATUS_FIELDS)}",
        )
    if set(statuses) != set(EVIDENCE_STATUS_FIELDS):
        raise policy_error(
            where,
            f"profile {profile_id!r} evidence status fields must be exactly "
            f"{list(EVIDENCE_STATUS_FIELDS)}",
        )
    for field in EVIDENCE_STATUS_FIELDS:
        _profile_value(
            {"id": profile_id, field: statuses[field]},
            field,
            EVIDENCE_STATUSES,
            where,
        )


def _validate_profile_reasons(
    profile: dict,
    profile_id: str,
    reason_ids: frozenset[str],
    where: str,
) -> None:
    reasons = require_unique_strings(
        profile.get("reason_codes"), "reason_codes", where=where
    )
    unknown = sorted(set(reasons) - reason_ids)
    if unknown:
        raise policy_error(where, f"profile {profile_id!r} cites unknown reasons {unknown}")


def _profiles_by_id(document: dict, where: str) -> dict[str, dict]:
    required_ids = require_unique_strings(
        document.get("required_profile_ids"), "required_profile_ids", where=where
    )
    if set(required_ids) != set(REQUIRED_PROFILE_IDS):
        raise policy_error(
            where,
            f"required_profile_ids must be exactly {sorted(REQUIRED_PROFILE_IDS)}",
        )
    profile_ids = _catalogue_ids(
        document.get("profiles"), "profiles", _PROFILE_FIELDS, where
    )
    if set(profile_ids) != set(required_ids):
        raise policy_error(where, "profiles must declare every required profile id exactly")
    return {profile["id"]: profile for profile in document["profiles"]}


def _validate_required_profile_semantics(
    profiles: dict[str, dict], where: str
) -> None:
    hosted = profiles[HOSTED_FRONTIER_PROFILE_ID]
    hosted_verdict = (
        hosted["intended_use"],
        hosted["project_training_policy"],
        set(hosted["evidence_statuses"].values()),
    )
    if hosted_verdict != ("research_only", "blocked", {"unresolved"}):
        raise policy_error(
            where,
            "hosted-frontier profile must be research_only/blocked with all statuses unresolved",
        )
    unknown = profiles[UNKNOWN_PROVENANCE_PROFILE_ID]
    unknown_verdict = (
        unknown["intended_use"],
        unknown["project_training_policy"],
    )
    if unknown_verdict != ("research_only", "blocked"):
        raise policy_error(where, "unknown-provenance profile must fail closed")


def _validate_profiles(
    document: dict,
    reason_ids: frozenset[str],
    where: str,
) -> dict[str, dict]:
    profiles = _profiles_by_id(document, where)
    for profile in profiles.values():
        _validate_profile(profile, reason_ids, where)
    _validate_required_profile_semantics(profiles, where)
    return profiles


def _validate_policy_unicode(document: object, where: str) -> None:
    try:
        reject_unpaired_surrogates(document)
    except ValueError as exc:
        raise RightsPolicyError(
            f"{where}: invalid rights policy Unicode: {exc}"
        ) from exc


def validate_rights_policy(document: object, *, where: str = _POLICY_LABEL) -> dict:
    """Validate policy identity, catalogues, profiles, and authorizing rules."""
    _validate_policy_unicode(document, where)
    checked = _validate_identity(document, where)
    _validate_vocabularies(checked, where)
    reason_ids = _validate_reason_catalogue(checked, where)
    profiles = _validate_profiles(checked, reason_ids, where)
    _validate_rules(checked, profiles, reason_ids, where)
    return checked


def load_rights_policy_bytes(payload: bytes, *, where: str = "rights policy bytes") -> dict:
    """Strictly decode and validate rights-policy JSON bytes."""
    if not isinstance(payload, bytes):
        raise policy_error(where, "policy input must be bytes")
    try:
        document = parse_strict_json_bytes(payload)
    except (ValueError, RecursionError) as exc:
        raise RightsPolicyError(f"{where}: invalid rights policy JSON: {exc}") from exc
    return validate_rights_policy(document, where=where)


def _load_rights_policy(path: Path) -> tuple[dict, bytes]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RightsPolicyError(f"{path}: rights policy is unreadable: {exc}") from exc
    return load_rights_policy_bytes(payload, where=str(path)), payload


def load_rights_policy(path: str | Path | None = None) -> dict:
    """Load an explicit policy path, failing closed on bytes or semantics."""
    try:
        policy_path = Path(path) if path is not None else MAPPING_PATH
    except TypeError as exc:
        raise policy_error(_POLICY_LABEL, "policy path must be string or Path") from exc
    document, _ = _load_rights_policy(policy_path)
    return document


@dataclass(frozen=True, slots=True)
class _EvidenceStatuses:
    research_retention_status: str
    research_evaluation_status: str
    redistribution_status: str
    provider_training_status: str
    weight_publication_status: str


@dataclass(frozen=True, slots=True)
class RightsAuthorization:  # noqa: D203,D211
    """One fully compiled verdict containing no mutable policy nodes."""

    intended_use: str
    project_training_policy: str
    evidence_statuses: _EvidenceStatuses
    reason_codes: tuple[str, ...]

    @property
    def research_retention_status(self) -> str:
        """Return the sealed research-retention evidence status."""
        return self.evidence_statuses.research_retention_status

    @property
    def research_evaluation_status(self) -> str:
        """Return the sealed research-evaluation evidence status."""
        return self.evidence_statuses.research_evaluation_status

    @property
    def redistribution_status(self) -> str:
        """Return the sealed redistribution evidence status."""
        return self.evidence_statuses.redistribution_status

    @property
    def provider_training_status(self) -> str:
        """Return the sealed provider-training evidence status."""
        return self.evidence_statuses.provider_training_status

    @property
    def weight_publication_status(self) -> str:
        """Return the sealed weight-publication evidence status."""
        return self.evidence_statuses.weight_publication_status


def _compile_authorizations(document: dict) -> MappingProxyType:
    profiles = {profile["id"]: profile for profile in document["profiles"]}
    compiled = {}
    for rule in document["rules"]:
        profile = profiles[rule["rights_profile_id"]]
        statuses = profile["evidence_statuses"]
        authorization = RightsAuthorization(
            intended_use=rule["intended_use"],
            project_training_policy=rule["project_training_policy"],
            evidence_statuses=_EvidenceStatuses(
                research_retention_status=statuses["research_retention_status"],
                research_evaluation_status=statuses["research_evaluation_status"],
                redistribution_status=statuses["redistribution_status"],
                provider_training_status=statuses["provider_training_status"],
                weight_publication_status=statuses["weight_publication_status"],
            ),
            reason_codes=tuple(rule["reason_codes"]),
        )
        for provider, channel in product(rule["providers"], rule["channels"]):
            compiled[(provider, channel, rule["rights_profile_id"])] = authorization
    return MappingProxyType(compiled)


_RIGHTS_POLICY_DOCUMENT, RIGHTS_POLICY_BYTES = _load_rights_policy(MAPPING_PATH)
RIGHTS_POLICY_SHA256 = sha256_digest(RIGHTS_POLICY_BYTES)
PROVIDERS = frozenset(_RIGHTS_POLICY_DOCUMENT["vocabularies"]["providers"])
RIGHTS_CHANNELS = frozenset(_RIGHTS_POLICY_DOCUMENT["vocabularies"]["channels"])
RIGHTS_PROFILE_IDS = frozenset(
    profile["id"] for profile in _RIGHTS_POLICY_DOCUMENT["profiles"]
)
RIGHTS_AUTHORIZATIONS = _compile_authorizations(_RIGHTS_POLICY_DOCUMENT)
REASON_CODES = frozenset(item["id"] for item in _RIGHTS_POLICY_DOCUMENT["reason_codes"])
RIGHTS_POLICY = freeze_json(_RIGHTS_POLICY_DOCUMENT)


if __package__:
    _expose_package_sibling(__name__)
