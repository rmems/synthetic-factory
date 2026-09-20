#!/usr/bin/env python3
"""Integrity-bound rights envelopes for retained curated records.

Identity attaches one envelope per retained record without changing canonical
content IDs. Compose, the training audit, the curation gate, and Hugging Face
export verify that envelope and keep research-only output in a distinct
lane that cannot become training-ready or exportable.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_record")
    from .rights_classifier import (
        RightsRoute,
        RightsVerification,
        classify_rights,
        verify_rights_envelope,
    )
    from .rights_mapping import (
        EVIDENCE_STATUS_FIELDS,
        RightsPolicyError,
        is_exact_string,
        policy_error,
        sha256_digest,
    )
    from .rights_policy import RIGHTS_POLICY_SHA256
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_record"
    )
    from rights_classifier import (
        RightsRoute,
        RightsVerification,
        classify_rights,
        verify_rights_envelope,
    )
    from rights_mapping import (
        EVIDENCE_STATUS_FIELDS,
        RightsPolicyError,
        is_exact_string,
        policy_error,
        sha256_digest,
    )
    from rights_policy import RIGHTS_POLICY_SHA256


LANE_RESEARCH = "research"
LANE_TRAINING = "training"
AUTHORITY_HOSTED = "hosted"
AUTHORITY_PROCEDURAL = "procedural"
AUTHORITY_NATIVE = "native"
NATIVE_SOURCE_TYPE = "frontier_session"
ENVELOPE_FIELD = "rights"
LANE_FIELD = "rights_lane"
BLOCKER_PREFIX = "rights:"
PROCEDURAL_REASON = "PROCEDURAL_REVIEWED_SOURCE"
NATIVE_PARITY_REASON = "NATIVE_PARITY_RESEARCH_ONLY"
_WHERE = "rights envelope"


def prefixed_sha256(value: object) -> str:
    """Return a canonical ``sha256:<hex>`` digest from hex or prefixed input."""

    if not is_exact_string(value) or not value:
        raise policy_error(_WHERE, "digest must be a lowercase SHA-256")
    digest = value if value.startswith("sha256:") else f"sha256:{value}"
    if len(digest) != 71 or any(character not in "0123456789abcdef" for character in digest[7:]):
        raise policy_error(_WHERE, "digest must be a lowercase SHA-256")
    return digest


def bytes_digest(payload: bytes) -> str:
    """Return the prefixed SHA-256 of exact bytes."""

    if not isinstance(payload, bytes):
        raise policy_error(_WHERE, "bound input must be bytes")
    return sha256_digest(payload)


def envelope_lane(envelope: Mapping[str, Any]) -> str:
    """Return the research or training lane for one verified envelope."""

    exportable, _blockers = training_export_blockers(envelope)
    return LANE_TRAINING if exportable else LANE_RESEARCH


def _require_reviewed_evidence(envelope: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    unresolved = [
        field
        for field in EVIDENCE_STATUS_FIELDS
        if envelope.get(field) == "unresolved"
    ]
    if envelope.get("authority") == AUTHORITY_PROCEDURAL:
        for field in ("procedural_policy_sha256", "catalog_sha256", "programs_sha256"):
            if not is_exact_string(envelope.get(field)):
                blockers.append(f"{BLOCKER_PREFIX} missing reviewed {field}")
        return blockers
    if envelope.get("authority") == AUTHORITY_NATIVE:
        for field in ("parity_policy_sha256", "catalog_sha256"):
            if not is_exact_string(envelope.get(field)):
                blockers.append(f"{BLOCKER_PREFIX} missing sealed {field}")
        return blockers
    if unresolved:
        blockers.append(
            f"{BLOCKER_PREFIX} evidence is not reviewed ({', '.join(unresolved)})"
        )
    return blockers


def _verdict_blockers(envelope: Mapping) -> list[str]:
    required = {
        "intended_use": "training_candidate",
        "project_training_policy": "allowed",
        "provider_training_status": "allowed",
    }
    return [f"{BLOCKER_PREFIX} {field} is not {expected}"
            for field, expected in required.items() if envelope.get(field) != expected]


def _binding_blockers(envelope: Mapping) -> list[str]:
    blockers = []
    for field in ("source_sha256", "factory_registry_sha256"):
        try:
            prefixed_sha256(envelope.get(field))
        except RightsPolicyError:
            blockers.append(f"{BLOCKER_PREFIX} missing exact {field} binding")
    return blockers


def _eligibility_blockers(envelope: Mapping) -> list[str]:
    if envelope.get("authority") != AUTHORITY_PROCEDURAL:
        return []
    if envelope.get("eligible_training_candidate") is True:
        return []
    return [f"{BLOCKER_PREFIX} procedural record is not an eligible training candidate"]


def training_export_blockers(envelope: object) -> tuple[bool, tuple[str, ...]]:
    """Check export eligibility after the caller authenticates the envelope."""
    if not isinstance(envelope, Mapping):
        return False, (f"{BLOCKER_PREFIX} envelope must be an object",)
    checks = (_verdict_blockers, _require_reviewed_evidence, _binding_blockers, _eligibility_blockers)
    blockers = tuple(blocker for check in checks for blocker in check(envelope))
    return not blockers, blockers


@dataclass(frozen=True)
class RecordRights:
    """Reviewed authority and exact bindings for a single retained record."""

    row: Any
    source_sha256: str
    factory_registry_sha256: str
    eligible: bool = False
    ineligibility_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.eligible, bool):
            raise policy_error(_WHERE, "procedural eligibility must be a boolean")
        if not all(is_exact_string(reason) for reason in self.ineligibility_reasons):
            raise policy_error(_WHERE, "ineligibility reasons must be strings")


@dataclass(frozen=True)
class BoundRights:
    """Exact byte evidence and reviewed authority used to verify an envelope."""

    source_bytes: bytes
    factory_registry_bytes: bytes
    row: Any
    eligible: bool = False
    ineligibility_reasons: tuple[str, ...] = ()

    def record_rights(self) -> RecordRights:
        return RecordRights(
            self.row, bytes_digest(self.source_bytes), bytes_digest(self.factory_registry_bytes),
            self.eligible, self.ineligibility_reasons,
        )


def hosted_envelope(context: RecordRights) -> dict[str, Any]:
    """Return a policy-authorized hosted envelope bound to exact evidence."""
    row = context.row
    if row.provider is None or row.channel is None:
        raise policy_error(_WHERE, "hosted row is missing provider/channel")
    decision = classify_rights(
        RightsRoute(row.provider, row.channel, row.rights_profile_id),
        source_sha256=prefixed_sha256(context.source_sha256),
        factory_registry_sha256=prefixed_sha256(context.factory_registry_sha256),
    )
    return {**decision.to_public_payload(), "authority": AUTHORITY_HOSTED}


def procedural_envelope(context: RecordRights) -> dict[str, Any]:
    """Return the independently sealed procedural verdict and byte bindings."""
    row = context.row
    return {
        "authority": AUTHORITY_PROCEDURAL,
        "rights_profile_id": row.rights_profile_id,
        "intended_use": row.intended_use,
        "project_training_policy": row.project_training_policy,
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "allowed",
        "weight_publication_status": "unresolved",
        "reason_codes": list(dict.fromkeys((PROCEDURAL_REASON, *context.ineligibility_reasons))),
        "eligible_training_candidate": context.eligible,
        "ineligibility_reasons": list(context.ineligibility_reasons),
        "source_sha256": prefixed_sha256(context.source_sha256),
        "factory_registry_sha256": prefixed_sha256(context.factory_registry_sha256),
        "procedural_policy_sha256": prefixed_sha256(row.procedural_policy_sha256),
        "catalog_sha256": prefixed_sha256(row.catalog_sha256),
        "programs_sha256": prefixed_sha256(row.programs_sha256),
        "rights_policy_sha256": RIGHTS_POLICY_SHA256,
    }


def native_envelope(context: RecordRights) -> dict[str, Any]:
    """Return the sealed native-parity verdict bound to exact evidence."""
    row = context.row
    if not is_exact_string(getattr(row, "parity_policy_sha256", None)):
        raise policy_error(_WHERE, "native row is missing its sealed parity policy digest")
    return {
        "authority": AUTHORITY_NATIVE,
        "rights_profile_id": row.rights_profile_id,
        "intended_use": row.intended_use,
        "project_training_policy": row.project_training_policy,
        "training_ready_policy": row.training_ready_policy,
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "unresolved",
        "weight_publication_status": "unresolved",
        "reason_codes": list(dict.fromkeys((NATIVE_PARITY_REASON, *context.ineligibility_reasons))),
        "eligible_training_candidate": context.eligible,
        "ineligibility_reasons": list(context.ineligibility_reasons),
        "source_sha256": prefixed_sha256(context.source_sha256),
        "factory_registry_sha256": prefixed_sha256(context.factory_registry_sha256),
        "parity_policy_sha256": prefixed_sha256(row.parity_policy_sha256),
        "catalog_id": row.catalog_id,
        "catalog_sha256": prefixed_sha256(row.catalog_sha256),
        "generator_version": row.generator_version,
        "rights_policy_sha256": RIGHTS_POLICY_SHA256,
    }


def envelope_for_row(context: RecordRights) -> dict[str, Any]:
    """Build the envelope authorized by one reviewed registry row."""
    source_type = getattr(context.row, "source_type", "hosted")
    if source_type == AUTHORITY_PROCEDURAL:
        return procedural_envelope(context)
    if source_type == NATIVE_SOURCE_TYPE:
        return native_envelope(context)
    return hosted_envelope(context)


def procedural_eligibility(mapping: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """Read eligibility without coercing malformed declarations to authorization."""
    authority = mapping.get("procedural_authority")
    if not isinstance(authority, Mapping):
        return False, ()
    reasons = authority.get("ineligibility_reasons", ())
    if not isinstance(reasons, (list, tuple)):
        raise policy_error(_WHERE, "ineligibility reasons must be a sequence")
    return authority.get("eligible_training_candidate", False), tuple(reasons)


def attach_identity_rights(
    mapping: dict[str, Any],
    row: Any,
    *,
    source_sha256: str,
    factory_registry_sha256: str,
) -> dict[str, Any]:
    """Attach a lane-tagged envelope onto one retained identity mapping."""

    eligible, reasons = procedural_eligibility(mapping)
    envelope = envelope_for_row(RecordRights(
        row, source_sha256, factory_registry_sha256, eligible, reasons,
    ))
    mapping[ENVELOPE_FIELD] = envelope
    mapping[LANE_FIELD] = envelope_lane(envelope)
    return envelope


def hosted_route(envelope: Mapping[str, Any]) -> RightsRoute:
    """Return the trusted hosted route declared by one envelope."""

    return RightsRoute(
        envelope["provider"],
        envelope["channel"],
        envelope["rights_profile_id"],
    )


def _public_hosted_payload(envelope: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(envelope)
    payload.pop("authority", None)
    return payload


def verify_bound_envelope(envelope: object, evidence: BoundRights) -> dict[str, Any]:
    """Recompute byte bindings and require the reviewed row's exact verdict."""
    if not isinstance(envelope, Mapping):
        raise policy_error(_WHERE, "envelope must be an object")
    authority = envelope.get("authority")
    if authority == AUTHORITY_PROCEDURAL:
        return _verify_procedural_envelope(envelope, evidence)
    if authority == AUTHORITY_NATIVE:
        return _verify_native_envelope(envelope, evidence)
    return _verify_hosted_envelope(envelope, evidence)


def _verify_hosted_envelope(envelope: Mapping, evidence: BoundRights) -> dict[str, Any]:
    row = evidence.row
    if row is None or getattr(row, "source_type", "hosted") not in {AUTHORITY_HOSTED, "dedicated"}:
        raise policy_error(_WHERE, "hosted envelope requires a reviewed hosted row")
    if envelope.get("authority") not in {None, AUTHORITY_HOSTED}:
        raise policy_error(_WHERE, "hosted envelope authority drifted")
    verified = verify_rights_envelope(
        _public_hosted_payload(envelope),
        source_bytes=evidence.source_bytes,
        factory_registry_bytes=evidence.factory_registry_bytes,
        verification=RightsVerification(
            expected_route=RightsRoute(row.provider, row.channel, row.rights_profile_id)
        ),
    )
    return {**verified.to_public_payload(), "authority": AUTHORITY_HOSTED}


def _verify_procedural_envelope(envelope: Mapping, evidence: BoundRights) -> dict[str, Any]:
    if getattr(evidence.row, "source_type", None) != AUTHORITY_PROCEDURAL:
        raise policy_error(_WHERE, "procedural envelope requires a reviewed procedural row")
    expected = envelope_for_row(evidence.record_rights())
    if envelope.get("eligible_training_candidate") is not expected["eligible_training_candidate"]:
        raise policy_error(_WHERE, "procedural eligibility differs from the reviewed verdict")
    if dict(envelope) != expected:
        raise policy_error(_WHERE, "envelope fields drift from the reviewed procedural verdict")
    return expected


def _verify_native_envelope(envelope: Mapping, evidence: BoundRights) -> dict[str, Any]:
    row = evidence.row
    if getattr(row, "source_type", None) != NATIVE_SOURCE_TYPE or not is_exact_string(
        getattr(row, "parity_policy_sha256", None)
    ):
        raise policy_error(_WHERE, "native envelope requires a reviewed frontier-session parity row")
    expected = envelope_for_row(evidence.record_rights())
    if dict(envelope) != expected:
        raise policy_error(_WHERE, "envelope fields drift from the sealed native parity verdict")
    return expected


def identity_envelope(mapping: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Return the rights envelope recorded on one identity mapping, if any."""

    if not isinstance(mapping, Mapping):
        return None
    envelope = mapping.get(ENVELOPE_FIELD)
    return dict(envelope) if isinstance(envelope, Mapping) else None


def research_only_blocker(count: int) -> str:
    """Return the stable audit/export blocker for retained research-only records."""

    return (
        f"{BLOCKER_PREFIX} {count} research-only records are retained "
        "and blocked from training export"
    )


def missing_envelope_blocker(count: int) -> str:
    """Return the stable blocker when retained records lack a rights envelope."""

    return f"{BLOCKER_PREFIX} {count} retained records lack a bound rights envelope"


def invalid_envelope_blocker(count: int) -> str:
    """Return the stable blocker for tampered or stale envelopes."""

    return f"{BLOCKER_PREFIX} {count} tampered or stale policy/binding digests"


if __package__:
    _expose_package_sibling(__name__)
