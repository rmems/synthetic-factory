#!/usr/bin/env python3
"""Strict validation for public ``rights.json`` schema 0.1.0 documents."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_document")
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
        RightsPolicyError,
        parse_strict_json_bytes,
        policy_error,
        reject_unpaired_surrogates,
        require_hash,
        require_nonempty_string,
    )
    from .rights_policy import RIGHTS_AUTHORIZATIONS
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_document"
    )
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
        RightsPolicyError,
        parse_strict_json_bytes,
        policy_error,
        reject_unpaired_surrogates,
        require_hash,
        require_nonempty_string,
    )
    from rights_policy import RIGHTS_AUTHORIZATIONS


RIGHTS_DOCUMENT_SCHEMA_VERSION = "0.1.0"
REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "dataset_id",
        "policy_source",
        "provider",
        "model",
        "channel",
        "subscription_plan",
        "generation_surface",
        "generated_at",
        "terms_document",
        "terms_effective_date",
        "terms_snapshot_sha256",
        "provider_output_attribution",
        "intended_use",
        "project_training_policy",
        *EVIDENCE_STATUS_FIELDS,
        "status_basis",
        "reviewed_at",
        "original_release_license",
        "original_release_commit",
        "legacy_public_release",
    }
)
OPTIONAL_FIELDS = frozenset({"notes"})

# Public attribution text is deliberately not canonicalized by case, substring,
# or a provider-name fallback. Each accepted spelling is independently reviewed.
PROVIDER_ALIASES = MappingProxyType(
    {
        "Anthropic": "anthropic",
        "xAI (SpaceXAI)": "xai",
        "OpenAI": "openai",
        "Meta": "meta",
    }
)
if (
    len(PROVIDER_ALIASES) != len(CANONICAL_PROVIDERS)
    or frozenset(PROVIDER_ALIASES.values()) != CANONICAL_PROVIDERS
):
    raise RightsPolicyError(
        "public provider aliases must cover the canonical provider vocabulary exactly"
    )

_DATASET_ID_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$", re.ASCII)
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class _DocumentIdentity:
    schema_version: str
    dataset_id: str
    policy_source: str
    model: str
    generated_at: str


@dataclass(frozen=True, slots=True)
class _ProviderRoute:
    provider: str
    canonical_provider: str
    channel: str
    subscription_plan: str
    generation_surface: str
    provider_output_attribution: str


@dataclass(frozen=True, slots=True)
class _EvidenceReferences:
    terms_document: str | None
    terms_effective_date: str | None
    terms_snapshot_sha256: str | None

    def values(self) -> tuple[str | None, str | None, str | None]:
        """Return the evidence references in schema order."""
        return (
            self.terms_document,
            self.terms_effective_date,
            self.terms_snapshot_sha256,
        )


@dataclass(frozen=True, slots=True)
class _EvidenceStatuses:
    research_retention_status: str
    research_evaluation_status: str
    redistribution_status: str
    provider_training_status: str
    weight_publication_status: str

    def values(self) -> tuple[str, str, str, str, str]:
        """Return all evidence statuses in schema order."""
        return (
            self.research_retention_status,
            self.research_evaluation_status,
            self.redistribution_status,
            self.provider_training_status,
            self.weight_publication_status,
        )


@dataclass(frozen=True, slots=True)
class _PublicDecision:
    intended_use: str
    project_training_policy: str
    evidence_statuses: _EvidenceStatuses


@dataclass(frozen=True, slots=True)
class _EvidenceReview:
    references: _EvidenceReferences
    status_basis: str
    reviewed_at: str


@dataclass(frozen=True, slots=True)
class _LegacyRelease:
    original_release_license: str | None
    original_release_commit: str | None
    legacy_public_release: bool


@dataclass(frozen=True, slots=True)
class RightsDocument:  # noqa: D203,D211
    """Normalized immutable public rights declaration."""

    identity: _DocumentIdentity
    route: _ProviderRoute
    decision: _PublicDecision
    evidence: _EvidenceReview
    legacy: _LegacyRelease
    notes: str | None

    def __getattr__(self, name: str) -> object:
        """Expose immutable aggregate fields through the original flat API."""
        section_names = {"identity", "route", "decision", "evidence", "legacy"}
        if name.startswith("__") or name in section_names:
            raise AttributeError(name)
        sections = (
            self.identity,
            self.route,
            self.decision,
            self.decision.evidence_statuses,
            self.evidence,
            self.evidence.references,
            self.legacy,
        )
        for section in sections:
            if hasattr(section, name):
                return getattr(section, name)
        raise AttributeError(name)


def _exact_document(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise policy_error(where, "rights document must be an object")
    fields = set(value)
    allowed_field_sets = (REQUIRED_FIELDS, REQUIRED_FIELDS | OPTIONAL_FIELDS)
    if fields not in allowed_field_sets:
        raise policy_error(
            where,
            "rights document fields must be exactly the required fields, "
            "with only notes permitted as optional",
        )
    return value


def _closed_value(
    value: object,
    field: str,
    vocabulary: frozenset[str],
    where: str,
) -> str:
    if not isinstance(value, str) or value not in vocabulary:
        raise policy_error(where, f"{field} has an unknown value")
    return value


def _calendar_date(value: object, field: str, where: str) -> str:
    if not isinstance(value, str) or _DATE_RE.fullmatch(value) is None:
        raise policy_error(where, f"{field} must be an ISO YYYY-MM-DD calendar date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise policy_error(
            where,
            f"{field} must be an ISO YYYY-MM-DD calendar date",
        ) from exc
    return value


def _optional_nonempty_string(value: object, field: str, where: str) -> str | None:
    if value is None:
        return None
    return require_nonempty_string(value, field, where=where)


def _optional_date(value: object, field: str, where: str) -> str | None:
    if value is None:
        return None
    return _calendar_date(value, field, where)


def _optional_hash(value: object, field: str, where: str) -> str | None:
    if value is None:
        return None
    return require_hash(value, field, where=where)


def _provider_alias(value: object, where: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise policy_error(where, "unknown public provider")
    canonical = PROVIDER_ALIASES.get(value)
    if canonical is None:
        raise policy_error(where, f"unknown public provider {value!r}")
    return value, canonical


def _validate_hosted_authorization(
    route: _ProviderRoute, decision: _PublicDecision, where: str
) -> None:
    authorization = RIGHTS_AUTHORIZATIONS.get(
        (route.canonical_provider, route.channel, HOSTED_FRONTIER_PROFILE_ID)
    )
    if authorization is None:
        raise policy_error(
            where,
            "no hosted-frontier authorization for public provider/channel route",
        )
    if (
        decision.intended_use != authorization.intended_use
        or decision.project_training_policy != authorization.project_training_policy
    ):
        raise policy_error(
            where,
            "public rights decision differs from hosted-frontier authorization: "
            "research_only requires project training to be blocked; "
            f"sealed decision is {authorization.intended_use}/"
            f"{authorization.project_training_policy}",
        )


def _validate_evidence(
    document: dict[str, object],
    decision: _PublicDecision,
    where: str,
) -> _EvidenceReview:
    terms_document = _optional_nonempty_string(
        document["terms_document"], "terms_document", where
    )
    terms_effective_date = _optional_date(
        document["terms_effective_date"], "terms_effective_date", where
    )
    terms_snapshot_sha256 = _optional_hash(
        document["terms_snapshot_sha256"], "terms_snapshot_sha256", where
    )
    references = _EvidenceReferences(
        terms_document,
        terms_effective_date,
        terms_snapshot_sha256,
    )
    populated = tuple(value is not None for value in references.values())
    _require_complete_references(populated, where)
    _require_evidence_for_resolved_status(decision, populated, where)
    status_basis = require_nonempty_string(
        document["status_basis"], "status_basis", where=where
    )
    reviewed_at = _calendar_date(document["reviewed_at"], "reviewed_at", where)
    return _EvidenceReview(references, status_basis, reviewed_at)


def _require_complete_references(populated: tuple[bool, ...], where: str) -> None:
    if any(populated) and not all(populated):
        raise policy_error(
            where,
            "evidence references must be all null or all non-null",
        )


def _require_evidence_for_resolved_status(
    decision: _PublicDecision, populated: tuple[bool, ...], where: str
) -> None:
    statuses = decision.evidence_statuses.values()
    if any(status != "unresolved" for status in statuses) and not all(populated):
        raise policy_error(
            where,
            "non-unresolved evidence requires terms_document, "
            "terms_effective_date, terms_snapshot_sha256, and status_basis",
        )


def _validate_legacy_release(
    release_license: object, release_commit: object, where: str
) -> _LegacyRelease:
    try:
        checked_license = require_nonempty_string(
            release_license,
            "original_release_license",
            where=where,
        )
    except RightsPolicyError as exc:
        raise policy_error(
            where,
            "legacy_public_release true requires a nonempty original_release_license",
        ) from exc
    if not isinstance(release_commit, str) or _GIT_COMMIT_RE.fullmatch(release_commit) is None:
        raise policy_error(
            where,
            "legacy_public_release true requires original_release_commit as lowercase 40 hex",
        )
    return _LegacyRelease(checked_license, release_commit, True)


def _validate_legacy_provenance(
    document: dict[str, object], where: str
) -> _LegacyRelease:
    legacy = document["legacy_public_release"]
    if not isinstance(legacy, bool):
        raise policy_error(where, "legacy_public_release must be a boolean")
    release_license = document["original_release_license"]
    release_commit = document["original_release_commit"]
    if legacy:
        return _validate_legacy_release(release_license, release_commit, where)
    if release_license is not None or release_commit is not None:
        raise policy_error(
            where,
            "original_release_license and original_release_commit must be null "
            "when legacy_public_release is false",
        )
    return _LegacyRelease(None, None, False)


def _validate_document_identity(
    document: dict[str, object], where: str
) -> _DocumentIdentity:
    if document["schema_version"] != RIGHTS_DOCUMENT_SCHEMA_VERSION:
        raise policy_error(
            where,
            f"schema_version must be exactly {RIGHTS_DOCUMENT_SCHEMA_VERSION}",
        )
    dataset_id = document["dataset_id"]
    if not isinstance(dataset_id, str) or _DATASET_ID_RE.fullmatch(dataset_id) is None:
        raise policy_error(where, "dataset_id must be an exact owner/name identifier")
    return _DocumentIdentity(
        RIGHTS_DOCUMENT_SCHEMA_VERSION,
        dataset_id,
        require_nonempty_string(document["policy_source"], "policy_source", where=where),
        require_nonempty_string(document["model"], "model", where=where),
        require_nonempty_string(document["generated_at"], "generated_at", where=where),
    )


def _validate_provider_route(
    document: dict[str, object], where: str
) -> _ProviderRoute:
    provider, canonical_provider = _provider_alias(document["provider"], where)
    return _ProviderRoute(
        provider,
        canonical_provider,
        _closed_value(document["channel"], "channel", CHANNELS, where),
        require_nonempty_string(
            document["subscription_plan"], "subscription_plan", where=where
        ),
        require_nonempty_string(
            document["generation_surface"], "generation_surface", where=where
        ),
        require_nonempty_string(
            document["provider_output_attribution"],
            "provider_output_attribution",
            where=where,
        ),
    )


def _validate_public_decision(
    document: dict[str, object], where: str
) -> _PublicDecision:
    statuses = {
        field: _closed_value(document[field], field, EVIDENCE_STATUSES, where)
        for field in EVIDENCE_STATUS_FIELDS
    }
    return _PublicDecision(
        _closed_value(document["intended_use"], "intended_use", INTENDED_USES, where),
        _closed_value(
            document["project_training_policy"],
            "project_training_policy",
            PROJECT_TRAINING_POLICIES,
            where,
        ),
        _EvidenceStatuses(**statuses),
    )


def _validate_document_unicode(document: object, where: str) -> None:
    try:
        reject_unpaired_surrogates(document)
    except ValueError as exc:
        raise RightsPolicyError(
            f"{where}: invalid rights document Unicode: {exc}"
        ) from exc


def validate_rights_document(
    document: object, *, where: str = "rights document"
) -> RightsDocument:
    """Validate one parsed public sidecar and return immutable normalized data."""
    checked = _exact_document(document, where)
    _validate_document_unicode(checked, where)
    identity = _validate_document_identity(checked, where)
    route = _validate_provider_route(checked, where)
    decision = _validate_public_decision(checked, where)
    _validate_hosted_authorization(route, decision, where)
    evidence = _validate_evidence(checked, decision, where)
    legacy = _validate_legacy_provenance(checked, where)
    notes = (
        require_nonempty_string(checked["notes"], "notes", where=where)
        if "notes" in checked
        else None
    )

    return RightsDocument(
        identity=identity,
        route=route,
        decision=decision,
        evidence=evidence,
        legacy=legacy,
        notes=notes,
    )


def load_rights_document_bytes(
    payload: bytes, *, where: str = "rights document bytes"
) -> RightsDocument:
    """Strictly decode JSON bytes and validate a public rights declaration."""
    if not isinstance(payload, bytes):
        raise policy_error(where, "rights document input must be bytes")
    try:
        document = parse_strict_json_bytes(payload)
    except (ValueError, RecursionError) as exc:
        raise RightsPolicyError(f"{where}: invalid rights document JSON: {exc}") from exc
    return validate_rights_document(document, where=where)


if __package__:
    _expose_package_sibling(__name__)
