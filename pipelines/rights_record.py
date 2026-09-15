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
ENVELOPE_FIELD = "rights"
LANE_FIELD = "rights_lane"
BLOCKER_PREFIX = "rights:"
PROCEDURAL_REASON = "PROCEDURAL_REVIEWED_SOURCE"
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
    if unresolved:
        blockers.append(
            f"{BLOCKER_PREFIX} evidence is not reviewed ({', '.join(unresolved)})"
        )
    return blockers


def training_export_blockers(envelope: object) -> tuple[bool, tuple[str, ...]]:
    """Return whether one envelope may enter a training-ready export."""

    if not isinstance(envelope, Mapping):
        return False, (f"{BLOCKER_PREFIX} envelope must be an object",)
    blockers: list[str] = []
    if envelope.get("intended_use") != "training_candidate":
        blockers.append(f"{BLOCKER_PREFIX} intended_use is not training_candidate")
    if envelope.get("project_training_policy") != "allowed":
        blockers.append(f"{BLOCKER_PREFIX} project_training_policy is not allowed")
    if envelope.get("provider_training_status") != "allowed":
        blockers.append(f"{BLOCKER_PREFIX} provider_training_status is not allowed")
    blockers.extend(_require_reviewed_evidence(envelope))
    for field in ("source_sha256", "factory_registry_sha256"):
        try:
            prefixed_sha256(envelope.get(field))
        except RightsPolicyError:
            blockers.append(f"{BLOCKER_PREFIX} missing exact {field} binding")
    if envelope.get("authority") == AUTHORITY_PROCEDURAL:
        if envelope.get("eligible_training_candidate") is not True:
            blockers.append(
                f"{BLOCKER_PREFIX} procedural record is not an eligible training candidate"
            )
    return (not blockers, tuple(blockers))


def hosted_envelope(
    *,
    provider: str,
    channel: str,
    rights_profile_id: str,
    source_sha256: str,
    factory_registry_sha256: str,
) -> dict[str, Any]:
    """Return the policy-authorized hosted envelope bound to source and registry."""

    decision = classify_rights(
        RightsRoute(provider, channel, rights_profile_id),
        source_sha256=prefixed_sha256(source_sha256),
        factory_registry_sha256=prefixed_sha256(factory_registry_sha256),
    )
    payload = decision.to_public_payload()
    payload["authority"] = AUTHORITY_HOSTED
    return payload


def procedural_envelope(
    *,
    rights_profile_id: str,
    intended_use: str,
    project_training_policy: str,
    source_sha256: str,
    factory_registry_sha256: str,
    procedural_policy_sha256: str,
    catalog_sha256: str,
    programs_sha256: str,
    eligible: bool,
    ineligibility_reasons: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Return the independently sealed procedural envelope for one retained record."""

    reasons = [PROCEDURAL_REASON]
    extra = [reason for reason in ineligibility_reasons if is_exact_string(reason)]
    if extra:
        reasons.extend(dict.fromkeys(extra))
    return {
        "authority": AUTHORITY_PROCEDURAL,
        "rights_profile_id": rights_profile_id,
        "intended_use": intended_use,
        "project_training_policy": project_training_policy,
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "unresolved",
        "provider_training_status": "allowed",
        "weight_publication_status": "unresolved",
        "reason_codes": reasons,
        "eligible_training_candidate": bool(eligible),
        "ineligibility_reasons": list(ineligibility_reasons),
        "source_sha256": prefixed_sha256(source_sha256),
        "factory_registry_sha256": prefixed_sha256(factory_registry_sha256),
        "procedural_policy_sha256": prefixed_sha256(procedural_policy_sha256),
        "catalog_sha256": prefixed_sha256(catalog_sha256),
        "programs_sha256": prefixed_sha256(programs_sha256),
        "rights_policy_sha256": RIGHTS_POLICY_SHA256,
    }


def envelope_for_row(
    row: Any,
    *,
    source_sha256: str,
    factory_registry_sha256: str,
    eligible: bool | None = None,
    ineligibility_reasons: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Build the envelope authorized by one reviewed registry row."""

    if getattr(row, "source_type", "hosted") == AUTHORITY_PROCEDURAL:
        return procedural_envelope(
            rights_profile_id=row.rights_profile_id,
            intended_use=row.intended_use,
            project_training_policy=row.project_training_policy,
            source_sha256=source_sha256,
            factory_registry_sha256=factory_registry_sha256,
            procedural_policy_sha256=row.procedural_policy_sha256,
            catalog_sha256=row.catalog_sha256,
            programs_sha256=row.programs_sha256,
            eligible=bool(eligible),
            ineligibility_reasons=ineligibility_reasons,
        )
    if row.provider is None or row.channel is None:
        raise policy_error(_WHERE, "hosted row is missing provider/channel")
    return hosted_envelope(
        provider=row.provider,
        channel=row.channel,
        rights_profile_id=row.rights_profile_id,
        source_sha256=source_sha256,
        factory_registry_sha256=factory_registry_sha256,
    )


def attach_identity_rights(
    mapping: dict[str, Any],
    row: Any,
    *,
    source_sha256: str,
    factory_registry_sha256: str,
) -> dict[str, Any]:
    """Attach a lane-tagged envelope onto one retained identity mapping."""

    authority = mapping.get("procedural_authority")
    eligible = None
    reasons: list[str] = []
    if isinstance(authority, Mapping):
        eligible = authority.get("eligible_training_candidate")
        raw_reasons = authority.get("ineligibility_reasons") or []
        if isinstance(raw_reasons, (list, tuple)):
            reasons = [str(item) for item in raw_reasons]
    envelope = envelope_for_row(
        row,
        source_sha256=source_sha256,
        factory_registry_sha256=factory_registry_sha256,
        eligible=eligible,
        ineligibility_reasons=reasons,
    )
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


def verify_bound_envelope(
    envelope: object,
    *,
    source_bytes: bytes,
    factory_registry_bytes: bytes,
    expected_row: Any | None = None,
    eligible: bool | None = None,
    ineligibility_reasons: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Recompute bound digests and require the reviewed row's exact verdict."""

    if not isinstance(envelope, Mapping):
        raise policy_error(_WHERE, "envelope must be an object")
    if envelope.get("authority") == AUTHORITY_PROCEDURAL:
        return _verify_procedural_envelope(
            envelope,
            source_bytes=source_bytes,
            factory_registry_bytes=factory_registry_bytes,
            expected_row=expected_row,
            eligible=False if eligible is None else bool(eligible),
            ineligibility_reasons=ineligibility_reasons,
        )
    if expected_row is None or expected_row.provider is None or expected_row.channel is None:
        raise policy_error(_WHERE, "hosted envelope requires a reviewed hosted row")
    verified = verify_rights_envelope(
        _public_hosted_payload(envelope),
        source_bytes=source_bytes,
        factory_registry_bytes=factory_registry_bytes,
        verification=RightsVerification(
            expected_route=RightsRoute(
                expected_row.provider,
                expected_row.channel,
                expected_row.rights_profile_id,
            )
        ),
    )
    payload = verified.to_public_payload()
    payload["authority"] = AUTHORITY_HOSTED
    if envelope.get("authority") not in {None, AUTHORITY_HOSTED}:
        raise policy_error(_WHERE, "hosted envelope authority drifted")
    return payload


def _verify_procedural_envelope(
    envelope: Mapping[str, Any],
    *,
    source_bytes: bytes,
    factory_registry_bytes: bytes,
    expected_row: Any | None,
    eligible: bool,
    ineligibility_reasons: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    if expected_row is None or getattr(expected_row, "source_type", None) != AUTHORITY_PROCEDURAL:
        raise policy_error(_WHERE, "procedural envelope requires a reviewed procedural row")
    expected = envelope_for_row(
        expected_row,
        source_sha256=sha256_digest(source_bytes)[7:],
        factory_registry_sha256=sha256_digest(factory_registry_bytes)[7:],
        eligible=eligible,
        ineligibility_reasons=ineligibility_reasons,
    )
    actual_source = prefixed_sha256(envelope.get("source_sha256"))
    actual_registry = prefixed_sha256(envelope.get("factory_registry_sha256"))
    if actual_source != sha256_digest(source_bytes):
        raise policy_error(_WHERE, "source_sha256 does not match bound bytes")
    if actual_registry != sha256_digest(factory_registry_bytes):
        raise policy_error(_WHERE, "factory_registry_sha256 does not match bound bytes")
    if envelope.get("procedural_policy_sha256") != expected["procedural_policy_sha256"]:
        raise policy_error(_WHERE, "procedural_policy_sha256 does not match bound bytes")
    if envelope.get("rights_policy_sha256") != RIGHTS_POLICY_SHA256:
        raise policy_error(
            _WHERE, "rights_policy_sha256 does not identify the committed policy"
        )
    comparable = dict(envelope)
    expected_comparable = dict(expected)
    if comparable != expected_comparable:
        raise policy_error(
            _WHERE, "envelope fields drift from the reviewed procedural verdict"
        )
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
