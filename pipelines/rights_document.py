#!/usr/bin/env python3
"""Strict validation for public ``rights.json`` schema 0.1.0 documents."""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any

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
        policy_error,
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
        policy_error,
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
if frozenset(PROVIDER_ALIASES.values()) != CANONICAL_PROVIDERS:
    raise RightsPolicyError(
        "public provider aliases must cover the canonical provider vocabulary exactly"
    )

_DATASET_ID_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class RightsDocument:
    """Normalized immutable public rights declaration."""

    schema_version: str
    dataset_id: str
    policy_source: str
    provider: str
    canonical_provider: str
    model: str
    channel: str
    subscription_plan: str
    generation_surface: str
    generated_at: str
    terms_document: str | None
    terms_effective_date: str | None
    terms_snapshot_sha256: str | None
    provider_output_attribution: str
    intended_use: str
    project_training_policy: str
    research_retention_status: str
    research_evaluation_status: str
    redistribution_status: str
    provider_training_status: str
    weight_publication_status: str
    status_basis: str
    reviewed_at: str
    original_release_license: str | None
    original_release_commit: str | None
    legacy_public_release: bool
    notes: str | None


def _exact_document(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise policy_error(where, "rights document must be an object")
    fields = set(value)
    if not (fields == REQUIRED_FIELDS or fields == REQUIRED_FIELDS | OPTIONAL_FIELDS):
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
    canonical_provider: str,
    channel: str,
    intended_use: str,
    project_training_policy: str,
    where: str,
) -> None:
    authorization = RIGHTS_AUTHORIZATIONS.get(
        (canonical_provider, channel, HOSTED_FRONTIER_PROFILE_ID)
    )
    if authorization is None:
        raise policy_error(
            where,
            "no hosted-frontier authorization for public provider/channel route",
        )
    if (
        intended_use != authorization.intended_use
        or project_training_policy != authorization.project_training_policy
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
    statuses: dict[str, str],
    where: str,
) -> tuple[str | None, str | None, str | None]:
    terms_document = _optional_nonempty_string(
        document["terms_document"], "terms_document", where
    )
    terms_effective_date = _optional_date(
        document["terms_effective_date"], "terms_effective_date", where
    )
    terms_snapshot_sha256 = _optional_hash(
        document["terms_snapshot_sha256"], "terms_snapshot_sha256", where
    )
    references = (terms_document, terms_effective_date, terms_snapshot_sha256)
    populated = tuple(value is not None for value in references)
    if any(populated) and not all(populated):
        raise policy_error(
            where,
            "evidence references must be all null or all non-null",
        )
    if any(status != "unresolved" for status in statuses.values()) and not all(
        populated
    ):
        raise policy_error(
            where,
            "non-unresolved evidence requires terms_document, "
            "terms_effective_date, terms_snapshot_sha256, and status_basis",
        )
    return references


def _validate_legacy_provenance(
    document: dict[str, object], where: str
) -> tuple[str | None, str | None, bool]:
    legacy = document["legacy_public_release"]
    if not isinstance(legacy, bool):
        raise policy_error(where, "legacy_public_release must be a boolean")
    release_license = document["original_release_license"]
    release_commit = document["original_release_commit"]
    if legacy:
        try:
            checked_license = require_nonempty_string(
                release_license,
                "original_release_license",
                where=where,
            )
        except RightsPolicyError as exc:
            raise policy_error(
                where,
                "legacy_public_release true requires a nonempty "
                "original_release_license",
            ) from exc
        if (
            not isinstance(release_commit, str)
            or _GIT_COMMIT_RE.fullmatch(release_commit) is None
        ):
            raise policy_error(
                where,
                "legacy_public_release true requires original_release_commit "
                "as lowercase 40 hex",
            )
        return checked_license, release_commit, legacy
    if release_license is not None or release_commit is not None:
        raise policy_error(
            where,
            "original_release_license and original_release_commit must be null "
            "when legacy_public_release is false",
        )
    return None, None, legacy


def validate_rights_document(
    document: object, *, where: str = "rights document"
) -> RightsDocument:
    """Validate one parsed public sidecar and return immutable normalized data."""

    checked = _exact_document(document, where)
    try:
        _reject_unpaired_surrogates(checked)
    except ValueError as exc:
        raise RightsPolicyError(f"{where}: invalid rights document Unicode: {exc}") from exc

    if checked["schema_version"] != RIGHTS_DOCUMENT_SCHEMA_VERSION:
        raise policy_error(
            where,
            f"schema_version must be exactly {RIGHTS_DOCUMENT_SCHEMA_VERSION}",
        )
    dataset_id = checked["dataset_id"]
    if not isinstance(dataset_id, str) or _DATASET_ID_RE.fullmatch(dataset_id) is None:
        raise policy_error(where, "dataset_id must be an exact owner/name identifier")

    provider, canonical_provider = _provider_alias(checked["provider"], where)
    channel = _closed_value(checked["channel"], "channel", CHANNELS, where)
    intended_use = _closed_value(
        checked["intended_use"], "intended_use", INTENDED_USES, where
    )
    project_training_policy = _closed_value(
        checked["project_training_policy"],
        "project_training_policy",
        PROJECT_TRAINING_POLICIES,
        where,
    )
    _validate_hosted_authorization(
        canonical_provider,
        channel,
        intended_use,
        project_training_policy,
        where,
    )

    statuses = {
        field: _closed_value(checked[field], field, EVIDENCE_STATUSES, where)
        for field in EVIDENCE_STATUS_FIELDS
    }
    status_basis = require_nonempty_string(
        checked["status_basis"], "status_basis", where=where
    )
    evidence = _validate_evidence(checked, statuses, where)
    release_license, release_commit, legacy = _validate_legacy_provenance(
        checked, where
    )
    notes = (
        require_nonempty_string(checked["notes"], "notes", where=where)
        if "notes" in checked
        else None
    )

    return RightsDocument(
        schema_version=RIGHTS_DOCUMENT_SCHEMA_VERSION,
        dataset_id=dataset_id,
        policy_source=require_nonempty_string(
            checked["policy_source"], "policy_source", where=where
        ),
        provider=provider,
        canonical_provider=canonical_provider,
        model=require_nonempty_string(checked["model"], "model", where=where),
        channel=channel,
        subscription_plan=require_nonempty_string(
            checked["subscription_plan"], "subscription_plan", where=where
        ),
        generation_surface=require_nonempty_string(
            checked["generation_surface"], "generation_surface", where=where
        ),
        generated_at=require_nonempty_string(
            checked["generated_at"], "generated_at", where=where
        ),
        terms_document=evidence[0],
        terms_effective_date=evidence[1],
        terms_snapshot_sha256=evidence[2],
        provider_output_attribution=require_nonempty_string(
            checked["provider_output_attribution"],
            "provider_output_attribution",
            where=where,
        ),
        intended_use=intended_use,
        project_training_policy=project_training_policy,
        research_retention_status=statuses["research_retention_status"],
        research_evaluation_status=statuses["research_evaluation_status"],
        redistribution_status=statuses["redistribution_status"],
        provider_training_status=statuses["provider_training_status"],
        weight_publication_status=statuses["weight_publication_status"],
        status_basis=status_basis,
        reviewed_at=_calendar_date(checked["reviewed_at"], "reviewed_at", where),
        original_release_license=release_license,
        original_release_commit=release_commit,
        legacy_public_release=legacy,
        notes=notes,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON constant {token}")


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number is not finitely representable: {token}")
    return value


def _reject_unpaired_surrogates(value: object, path: str = "$") -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError(f"unpaired surrogate at {path}") from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unpaired_surrogates(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unpaired_surrogates(key, f"{path}.<key>")
            _reject_unpaired_surrogates(item, f"{path}.{key}")


def load_rights_document_bytes(
    payload: bytes, *, where: str = "rights document bytes"
) -> RightsDocument:
    """Strictly decode JSON bytes and validate a public rights declaration."""

    if not isinstance(payload, bytes):
        raise policy_error(where, "rights document input must be bytes")
    try:
        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
        )
        _reject_unpaired_surrogates(document)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise RightsPolicyError(f"{where}: invalid rights document JSON: {exc}") from exc
    return validate_rights_document(document, where=where)


if __package__:
    _expose_package_sibling(__name__)
