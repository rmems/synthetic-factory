#!/usr/bin/env python3
"""Immutable values and primitive validators for public rights documents."""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_document_support")
    from . import rights_mapping as _rights_mapping
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_document_support"
    )
    import rights_mapping as _rights_mapping


policy_error = _rights_mapping.policy_error
protect_frozen_slots = _rights_mapping.protect_frozen_slots
require_hash = _rights_mapping.require_hash
require_nonempty_string = _rights_mapping.require_nonempty_string


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$", re.ASCII)


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _DocumentIdentity:
    schema_version: str
    dataset_id: str
    policy_source: str
    model: str
    generated_at: str


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _ProviderRoute:
    provider: str
    canonical_provider: str
    channel: str
    subscription_plan: str
    generation_surface: str
    provider_output_attribution: str


@protect_frozen_slots
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


@protect_frozen_slots
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


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _PublicDecision:
    intended_use: str
    project_training_policy: str
    evidence_statuses: _EvidenceStatuses


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _EvidenceReview:
    references: _EvidenceReferences
    status_basis: str
    reviewed_at: str


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _LegacyRelease:
    original_release_license: str | None
    original_release_commit: str | None
    legacy_public_release: bool


@protect_frozen_slots
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


def exact_document(
    value: object,
    required_fields: frozenset[str],
    optional_fields: frozenset[str],
    where: str,
) -> dict[str, object]:
    """Require the exact public document field set."""
    if not isinstance(value, dict):
        raise policy_error(where, "rights document must be an object")
    fields = set(value)
    allowed_field_sets = (required_fields, required_fields | optional_fields)
    if fields not in allowed_field_sets:
        raise policy_error(
            where,
            "rights document fields must be exactly the required fields, "
            "with only notes permitted as optional",
        )
    return value


def closed_value(
    value: object,
    field: str,
    vocabulary: frozenset[str],
    where: str,
) -> str:
    """Require one exact closed-vocabulary string."""
    if not isinstance(value, str) or value not in vocabulary:
        raise policy_error(where, f"{field} has an unknown value")
    return value


def calendar_date(value: object, field: str, where: str) -> str:
    """Require one real ISO calendar date."""
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


def optional_nonempty_string(value: object, field: str, where: str) -> str | None:
    """Validate an optional nonempty string."""
    if value is None:
        return None
    return require_nonempty_string(value, field, where=where)


def optional_date(value: object, field: str, where: str) -> str | None:
    """Validate an optional ISO calendar date."""
    if value is None:
        return None
    return calendar_date(value, field, where)


def optional_hash(value: object, field: str, where: str) -> str | None:
    """Validate an optional canonical hash."""
    if value is None:
        return None
    return require_hash(value, field, where=where)


def provider_alias(
    value: object,
    aliases: Mapping[str, str],
    where: str,
) -> tuple[str, str]:
    """Resolve one exact reviewed public provider alias."""
    if not isinstance(value, str):
        raise policy_error(where, "unknown public provider")
    canonical = aliases.get(value)
    if canonical is None:
        raise policy_error(where, f"unknown public provider {value!r}")
    return value, canonical


if __package__:
    _expose_package_sibling(__name__)
