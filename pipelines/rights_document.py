#!/usr/bin/env python3
"""Strict validation for public ``rights.json`` schema 0.1.0 documents."""

from __future__ import annotations

import re
import sys
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
        require_nonempty_string,
    )
    from .rights_policy import RIGHTS_AUTHORIZATIONS
    from . import rights_document_support as _rights_document_support
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
        require_nonempty_string,
    )
    from rights_policy import RIGHTS_AUTHORIZATIONS
    import rights_document_support as _rights_document_support


_DocumentIdentity = _rights_document_support._DocumentIdentity
_ProviderRoute = _rights_document_support._ProviderRoute
_EvidenceReferences = _rights_document_support._EvidenceReferences
_EvidenceStatuses = _rights_document_support._EvidenceStatuses
_PublicDecision = _rights_document_support._PublicDecision
_EvidenceReview = _rights_document_support._EvidenceReview
_LegacyRelease = _rights_document_support._LegacyRelease
RightsDocument = _rights_document_support.RightsDocument
_exact_document = _rights_document_support.exact_document
_closed_value = _rights_document_support.closed_value
_calendar_date = _rights_document_support.calendar_date
_optional_nonempty_string = _rights_document_support.optional_nonempty_string
_optional_date = _rights_document_support.optional_date
_optional_hash = _rights_document_support.optional_hash
_provider_alias = _rights_document_support.provider_alias
require_hash = _rights_document_support.require_hash


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
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


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
    provider, canonical_provider = _provider_alias(
        document["provider"], PROVIDER_ALIASES, where
    )
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
    checked = _exact_document(document, REQUIRED_FIELDS, OPTIONAL_FIELDS, where)
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
