#!/usr/bin/env python3
"""Mapping-authorized rights decisions and byte-bound envelope verification."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_classifier")
    from .rights_mapping import (
        EVIDENCE_STATUS_FIELDS,
        policy_error,
        require_hash,
        sha256_digest,
    )
    from .rights_policy import (
        PROVIDERS,
        REASON_CODES,
        RIGHTS_CHANNELS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_POLICY_BYTES,
        RIGHTS_PROFILE_IDS,
        RIGHTS_POLICY_SHA256,
        load_rights_policy_bytes,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_classifier"
    )
    from rights_mapping import (
        EVIDENCE_STATUS_FIELDS,
        policy_error,
        require_hash,
        sha256_digest,
    )
    from rights_policy import (
        PROVIDERS,
        REASON_CODES,
        RIGHTS_CHANNELS,
        RIGHTS_AUTHORIZATIONS,
        RIGHTS_POLICY_BYTES,
        RIGHTS_PROFILE_IDS,
        RIGHTS_POLICY_SHA256,
        load_rights_policy_bytes,
    )


PUBLIC_PAYLOAD_FIELDS = frozenset(
    {
        "rights_profile_id",
        "provider",
        "channel",
        "intended_use",
        "project_training_policy",
        *EVIDENCE_STATUS_FIELDS,
        "reason_codes",
        "source_sha256",
        "factory_registry_sha256",
        "rights_policy_sha256",
    }
)

@dataclass(frozen=True)
class RightsDecision:
    rights_profile_id: str
    provider: str
    channel: str
    intended_use: str
    project_training_policy: str
    research_retention_status: str
    research_evaluation_status: str
    redistribution_status: str
    provider_training_status: str
    weight_publication_status: str
    reason_codes: tuple[str, ...]
    source_sha256: str
    factory_registry_sha256: str
    rights_policy_sha256: str

    def to_public_payload(self) -> dict[str, object]:
        """Return the JSON-ready public envelope without exposing mutable state."""

        return {
            "rights_profile_id": self.rights_profile_id,
            "provider": self.provider,
            "channel": self.channel,
            "intended_use": self.intended_use,
            "project_training_policy": self.project_training_policy,
            "research_retention_status": self.research_retention_status,
            "research_evaluation_status": self.research_evaluation_status,
            "redistribution_status": self.redistribution_status,
            "provider_training_status": self.provider_training_status,
            "weight_publication_status": self.weight_publication_status,
            "reason_codes": list(self.reason_codes),
            "source_sha256": self.source_sha256,
            "factory_registry_sha256": self.factory_registry_sha256,
            "rights_policy_sha256": self.rights_policy_sha256,
        }

    @property
    def public_payload(self) -> Mapping[str, object]:
        return MappingProxyType(self.to_public_payload())


def _authorization(provider: str, channel: str, profile_id: str):
    authorization = RIGHTS_AUTHORIZATIONS.get((provider, channel, profile_id))
    if authorization is None:
        raise policy_error(
            "rights classification",
            "provider/channel/profile combination is not authorized by policy",
        )
    return authorization


def classify_rights(
    provider: str,
    channel: str,
    rights_profile_id: str,
    source_sha256: str,
    factory_registry_sha256: str,
) -> RightsDecision:
    """Return the one static verdict authorized for a bound source and registry."""

    where = "rights classification"
    if not isinstance(provider, str) or provider not in PROVIDERS:
        raise policy_error(where, f"unknown canonical provider {provider!r}")
    if not isinstance(channel, str) or channel not in RIGHTS_CHANNELS:
        raise policy_error(where, f"unknown channel {channel!r}")
    if (
        not isinstance(rights_profile_id, str)
        or rights_profile_id not in RIGHTS_PROFILE_IDS
    ):
        raise policy_error(where, f"unknown rights profile {rights_profile_id!r}")
    source_digest = require_hash(source_sha256, "source_sha256", where=where)
    registry_digest = require_hash(
        factory_registry_sha256,
        "factory_registry_sha256",
        where=where,
    )
    authorization = _authorization(provider, channel, rights_profile_id)
    return RightsDecision(
        rights_profile_id=rights_profile_id,
        provider=provider,
        channel=channel,
        intended_use=authorization.intended_use,
        project_training_policy=authorization.project_training_policy,
        research_retention_status=authorization.research_retention_status,
        research_evaluation_status=authorization.research_evaluation_status,
        redistribution_status=authorization.redistribution_status,
        provider_training_status=authorization.provider_training_status,
        weight_publication_status=authorization.weight_publication_status,
        reason_codes=authorization.reason_codes,
        source_sha256=source_digest,
        factory_registry_sha256=registry_digest,
        rights_policy_sha256=RIGHTS_POLICY_SHA256,
    )


def _payload_object(envelope: object) -> dict[str, object]:
    if isinstance(envelope, RightsDecision):
        return envelope.to_public_payload()
    if not isinstance(envelope, Mapping):
        raise policy_error("rights envelope", "envelope must be an object")
    payload = dict(envelope)
    if set(payload) != set(PUBLIC_PAYLOAD_FIELDS):
        raise policy_error(
            "rights envelope",
            f"envelope fields must be exactly {sorted(PUBLIC_PAYLOAD_FIELDS)}",
        )
    return payload


def _bound_bytes(value: object, field: str) -> bytes:
    if not isinstance(value, bytes):
        raise policy_error("rights envelope", f"{field} must be bytes")
    return value


def verify_rights_envelope(
    envelope: object,
    *,
    source_bytes: bytes,
    factory_registry_bytes: bytes,
    policy_bytes: bytes | None = None,
) -> RightsDecision:
    """Recompute byte digests and require the mapping's exact static verdict."""

    payload = _payload_object(envelope)
    source = _bound_bytes(source_bytes, "source_bytes")
    registry = _bound_bytes(factory_registry_bytes, "factory_registry_bytes")
    supplied_policy = (
        RIGHTS_POLICY_BYTES
        if policy_bytes is None
        else _bound_bytes(policy_bytes, "policy_bytes")
    )
    load_rights_policy_bytes(supplied_policy, where="rights envelope policy_bytes")

    digest_inputs = (
        ("source_sha256", source),
        ("factory_registry_sha256", registry),
        ("rights_policy_sha256", supplied_policy),
    )
    for field, bound_bytes in digest_inputs:
        actual = require_hash(payload.get(field), field, where="rights envelope")
        expected = sha256_digest(bound_bytes)
        if actual != expected:
            raise policy_error("rights envelope", f"{field} does not match bound bytes")
    if payload["rights_policy_sha256"] != RIGHTS_POLICY_SHA256:
        raise policy_error(
            "rights envelope",
            "rights_policy_sha256 does not identify the committed policy",
        )

    reasons = payload.get("reason_codes")
    if (
        not isinstance(reasons, list)
        or not reasons
        or not all(isinstance(reason, str) and reason for reason in reasons)
        or len(reasons) != len(set(reasons))
    ):
        raise policy_error("rights envelope", "reason_codes must be unique strings")
    unknown_reasons = sorted(set(reasons) - REASON_CODES)
    if unknown_reasons:
        raise policy_error(
            "rights envelope", f"unknown reason codes {unknown_reasons}"
        )

    expected_decision = classify_rights(
        provider=payload.get("provider"),
        channel=payload.get("channel"),
        rights_profile_id=payload.get("rights_profile_id"),
        source_sha256=payload["source_sha256"],
        factory_registry_sha256=payload["factory_registry_sha256"],
    )
    if payload != expected_decision.to_public_payload():
        raise policy_error(
            "rights envelope",
            "envelope fields drift from the policy-authorized profile verdict",
        )
    return expected_decision


if __package__:
    _expose_package_sibling(__name__)
