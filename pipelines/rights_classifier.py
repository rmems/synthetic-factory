#!/usr/bin/env python3
"""Mapping-authorized rights decisions and byte-bound envelope verification."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_classifier")
    from .rights_mapping import (
        EVIDENCE_STATUS_FIELDS,
        policy_error,
        protect_frozen_slots,
        require_hash,
        sha256_digest,
    )
    from .rights_policy import (
        PROVIDERS,
        REASON_CODES,
        RIGHTS_CHANNELS,
        RIGHTS_AUTHORIZATIONS,
        RightsAuthorization,
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
        protect_frozen_slots,
        require_hash,
        sha256_digest,
    )
    from rights_policy import (
        PROVIDERS,
        REASON_CODES,
        RIGHTS_CHANNELS,
        RIGHTS_AUTHORIZATIONS,
        RightsAuthorization,
        RIGHTS_POLICY_BYTES,
        RIGHTS_PROFILE_IDS,
        RIGHTS_POLICY_SHA256,
        load_rights_policy_bytes,
    )


PUBLIC_PAYLOAD_FIELD_ORDER = (
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
)
PUBLIC_PAYLOAD_FIELDS = frozenset(PUBLIC_PAYLOAD_FIELD_ORDER)
_ENVELOPE_WHERE = "rights envelope"
_CLASSIFICATION_WHERE = "rights classification"
_REASON_CODES_ERROR = "reason_codes must be unique strings"
_VERDICT_STRING_FIELDS = (
    "intended_use",
    "project_training_policy",
    *EVIDENCE_STATUS_FIELDS,
)


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class RightsRoute:  # noqa: D203,D211
    """Canonical provider/channel/profile coordinates for one decision."""

    provider: str
    channel: str
    rights_profile_id: str


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class RightsVerification:
    """Trusted route and optional policy bytes for envelope verification."""

    expected_route: RightsRoute
    policy_bytes: bytes | None = None


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _BoundDigests:
    source_sha256: str
    factory_registry_sha256: str
    rights_policy_sha256: str


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class RightsDecision:  # noqa: D203,D211
    """Immutable rights verdict with byte-bound evidence identifiers."""

    route: RightsRoute
    authorization: RightsAuthorization
    bindings: _BoundDigests

    def __getattr__(self, name: str) -> object:
        """Expose immutable aggregate fields through the original flat API."""
        if name.startswith("__") or name in {"route", "authorization", "bindings"}:
            raise AttributeError(name)
        for section in (self.route, self.authorization, self.bindings):
            if hasattr(section, name):
                return getattr(section, name)
        raise AttributeError(name)

    def to_public_payload(self) -> dict[str, object]:
        """Return the JSON-ready public envelope without exposing mutable state."""
        payload = {
            field: getattr(self, field)
            for field in PUBLIC_PAYLOAD_FIELD_ORDER
            if field != "reason_codes"
        }
        payload["reason_codes"] = list(self.reason_codes)
        return payload

    @property
    def public_payload(self) -> Mapping[str, object]:
        """Return a read-only view of the public envelope."""
        payload = self.to_public_payload()
        payload["reason_codes"] = self.reason_codes
        return MappingProxyType(payload)


def _authorization(route: RightsRoute) -> RightsAuthorization:
    authorization = RIGHTS_AUTHORIZATIONS.get(
        (route.provider, route.channel, route.rights_profile_id)
    )
    if authorization is None:
        raise policy_error(
            _CLASSIFICATION_WHERE,
            "provider/channel/profile combination is not authorized by policy",
        )
    return authorization


def _require_route_value(
    value: object,
    vocabulary: frozenset[str],
    label: str,
    *,
    where: str = _CLASSIFICATION_WHERE,
) -> None:
    if type(value) is not str:
        raise policy_error(
            where,
            f"unknown {label}",
        )
    if value not in vocabulary:
        raise policy_error(
            where,
            f"unknown {label}",
        )


def _validated_route(route: object) -> RightsRoute:
    if not isinstance(route, RightsRoute):
        raise policy_error(_CLASSIFICATION_WHERE, "route must be a RightsRoute")
    _require_route_value(route.provider, PROVIDERS, "canonical provider")
    _require_route_value(route.channel, RIGHTS_CHANNELS, "channel")
    _require_route_value(route.rights_profile_id, RIGHTS_PROFILE_IDS, "rights profile")
    return route


def _classification_route(
    route: RightsRoute | None, route_fields: dict[str, object]
) -> RightsRoute:
    if route is not None:
        if route_fields:
            raise policy_error(
                _CLASSIFICATION_WHERE,
                "route cannot be combined with provider/channel/profile keywords",
            )
        return _validated_route(route)
    required = {"provider", "channel", "rights_profile_id"}
    if set(route_fields) != required:
        raise policy_error(
            _CLASSIFICATION_WHERE,
            f"route fields must be exactly {sorted(required)}",
        )
    return _validated_route(RightsRoute(**route_fields))


def classify_rights(
    route: RightsRoute | None = None,
    source_sha256: object = None,
    factory_registry_sha256: object = None,
    **route_fields: object,
) -> RightsDecision:
    """Return the one static verdict authorized for a bound source and registry."""
    where = _CLASSIFICATION_WHERE
    checked_route = _classification_route(route, route_fields)
    source_digest = require_hash(source_sha256, "source_sha256", where=where)
    registry_digest = require_hash(
        factory_registry_sha256,
        "factory_registry_sha256",
        where=where,
    )
    authorization = _authorization(checked_route)
    return RightsDecision(
        route=checked_route,
        authorization=authorization,
        bindings=_BoundDigests(
            source_sha256=source_digest,
            factory_registry_sha256=registry_digest,
            rights_policy_sha256=RIGHTS_POLICY_SHA256,
        ),
    )


def _payload_object(envelope: object) -> dict[str, object]:
    if isinstance(envelope, RightsDecision):
        return envelope.to_public_payload()
    if not isinstance(envelope, Mapping):
        raise policy_error(_ENVELOPE_WHERE, "envelope must be an object")
    payload = dict(envelope)
    if any(type(field) is not str for field in payload):
        raise policy_error(
            _ENVELOPE_WHERE,
            f"envelope fields must be exactly {sorted(PUBLIC_PAYLOAD_FIELDS)}",
        )
    if set(payload) != PUBLIC_PAYLOAD_FIELDS:
        raise policy_error(
            _ENVELOPE_WHERE,
            f"envelope fields must be exactly {sorted(PUBLIC_PAYLOAD_FIELDS)}",
        )
    return payload


def _bound_bytes(value: object, field: str) -> bytes:
    if not isinstance(value, bytes):
        raise policy_error(_ENVELOPE_WHERE, f"{field} must be bytes")
    return value


@protect_frozen_slots
@dataclass(frozen=True, slots=True)
class _EnvelopeBytes:
    source: bytes
    registry: bytes
    policy: bytes


def _envelope_bytes(
    source_bytes: object,
    factory_registry_bytes: object,
    policy_bytes: object,
) -> _EnvelopeBytes:
    policy = (
        RIGHTS_POLICY_BYTES
        if policy_bytes is None
        else _bound_bytes(policy_bytes, "policy_bytes")
    )
    return _EnvelopeBytes(
        _bound_bytes(source_bytes, "source_bytes"),
        _bound_bytes(factory_registry_bytes, "factory_registry_bytes"),
        policy,
    )


def _verify_bound_digests(payload: dict[str, object], bound: _EnvelopeBytes) -> None:
    digest_inputs = (
        ("source_sha256", bound.source),
        ("factory_registry_sha256", bound.registry),
        ("rights_policy_sha256", bound.policy),
    )
    for field, bound_bytes in digest_inputs:
        actual = require_hash(payload[field], field, where=_ENVELOPE_WHERE)
        if actual != sha256_digest(bound_bytes):
            raise policy_error(_ENVELOPE_WHERE, f"{field} does not match bound bytes")
    if payload["rights_policy_sha256"] != RIGHTS_POLICY_SHA256:
        raise policy_error(
            _ENVELOPE_WHERE,
            "rights_policy_sha256 does not identify the committed policy",
        )


def _reason_list(value: object) -> list[object]:
    if not isinstance(value, (list, tuple)):
        raise policy_error(_ENVELOPE_WHERE, _REASON_CODES_ERROR)
    if not value:
        raise policy_error(_ENVELOPE_WHERE, _REASON_CODES_ERROR)
    return list(value)


def _require_reason_strings(reasons: list[object]) -> None:
    for reason in reasons:
        if type(reason) is not str:
            raise policy_error(_ENVELOPE_WHERE, _REASON_CODES_ERROR)
        if not reason:
            raise policy_error(_ENVELOPE_WHERE, _REASON_CODES_ERROR)


def _require_unique_reasons(reasons: list[object]) -> None:
    if len(reasons) != len(set(reasons)):
        raise policy_error(_ENVELOPE_WHERE, _REASON_CODES_ERROR)


def _verify_reason_codes(payload: dict[str, object]) -> None:
    reasons = _reason_list(payload["reason_codes"])
    payload["reason_codes"] = reasons
    _require_reason_strings(reasons)
    _require_unique_reasons(reasons)
    unknown_reasons = sorted(set(reasons) - REASON_CODES)
    if unknown_reasons:
        raise policy_error(
            _ENVELOPE_WHERE, f"unknown reason codes {unknown_reasons}"
        )


def _require_verdict_strings(payload: dict[str, object]) -> None:
    for field in _VERDICT_STRING_FIELDS:
        if type(payload[field]) is not str:
            raise policy_error(_ENVELOPE_WHERE, f"{field} must be a string")


def _payload_route(payload: dict[str, object]) -> RightsRoute:
    route_fields = (
        ("provider", PROVIDERS, "canonical provider"),
        ("channel", RIGHTS_CHANNELS, "channel"),
        ("rights_profile_id", RIGHTS_PROFILE_IDS, "rights profile"),
    )
    for field, vocabulary, label in route_fields:
        _require_route_value(
            payload[field],
            vocabulary,
            label,
            where=_ENVELOPE_WHERE,
        )
    return RightsRoute(
        provider=payload["provider"],
        channel=payload["channel"],
        rights_profile_id=payload["rights_profile_id"],
    )


def _expected_decision(
    payload: dict[str, object], expected_route: RightsRoute
) -> RightsDecision:
    route = _payload_route(payload)
    trusted_route = _validated_route(expected_route)
    if route != trusted_route:
        raise policy_error(
            _ENVELOPE_WHERE,
            "envelope route does not match trusted expected route",
        )
    return classify_rights(
        trusted_route,
        source_sha256=payload["source_sha256"],
        factory_registry_sha256=payload["factory_registry_sha256"],
    )


def verify_rights_envelope(
    envelope: object,
    *,
    source_bytes: bytes,
    factory_registry_bytes: bytes,
    verification: RightsVerification,
) -> RightsDecision:
    """Recompute digests and require the trusted route's exact static verdict."""
    if not isinstance(verification, RightsVerification):
        raise policy_error(_ENVELOPE_WHERE, "verification must be trusted")
    payload = _payload_object(envelope)
    _require_verdict_strings(payload)
    bound = _envelope_bytes(
        source_bytes,
        factory_registry_bytes,
        verification.policy_bytes,
    )
    if verification.policy_bytes is not None:
        load_rights_policy_bytes(bound.policy, where="rights envelope policy_bytes")
    _verify_bound_digests(payload, bound)
    _verify_reason_codes(payload)
    expected_decision = _expected_decision(payload, verification.expected_route)
    if payload != expected_decision.to_public_payload():
        raise policy_error(
            _ENVELOPE_WHERE,
            "envelope fields drift from the policy-authorized profile verdict",
        )
    return expected_decision


if __package__:
    _expose_package_sibling(__name__)
