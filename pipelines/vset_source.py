"""Source-kind and payload shape checks for VSET records."""

from __future__ import annotations

from typing import Any, Mapping

from vset_constants import (
    IDENTITY_ENV_KEYS,
    KIND_PAYLOAD_KEYS,
    SOURCE_KINDS,
    SYNTHETIC_PACK_PREFIX,
    VSetValidationError,
    _contains_prometheus_marker,
)


def source_kind_errors(record: Mapping[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    source_kind = record.get("source_kind")
    if source_kind not in SOURCE_KINDS:
        errors.append(
            VSetValidationError(
                "vset.source_kind_invalid",
                "source_kind must be synthetic or real_public_engineering",
            )
        )
        return errors
    environment = record.get("environment")
    env = environment if isinstance(environment, Mapping) else {}
    if source_kind == "synthetic":
        errors.extend(_synthetic_masquerade_errors(record, env))
    if source_kind == "real_public_engineering":
        pack_id = env.get("repo_pack_id")
        if isinstance(pack_id, str) and pack_id.startswith(SYNTHETIC_PACK_PREFIX):
            errors.append(
                VSetValidationError(
                    "vset.source_kind_masquerade",
                    "real_public_engineering must not use a synthetic VSET repo pack as its identity",
                )
            )
    return errors


def _prometheus_identity_claimed(record: Mapping[str, Any], env: Mapping[str, Any]) -> bool:
    scoped = {key: env.get(key) for key in IDENTITY_ENV_KEYS if key in env}
    return _contains_prometheus_marker(scoped) or _contains_prometheus_marker(
        record.get("prometheus_lineage")
    )


def _real_family_claimed(env: Mapping[str, Any]) -> bool:
    if env.get("claimed_source_kind") == "real_public_engineering":
        return True
    family = env.get("source_family")
    if not isinstance(family, str):
        return False
    return family.lower() in {"prometheus_real", "prometheus"}


def _synthetic_masquerade_errors(
    record: Mapping[str, Any], env: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if _prometheus_identity_claimed(record, env):
        errors.append(
            VSetValidationError(
                "vset.source_kind_masquerade",
                "synthetic records must not claim Operation Prometheus as source identity",
            )
        )
    if _real_family_claimed(env):
        errors.append(
            VSetValidationError(
                "vset.source_kind_masquerade",
                "synthetic records must not masquerade as real_public_engineering / Prometheus",
            )
        )
    return errors


def payload_errors(kind: str, payload: Any) -> list[VSetValidationError]:
    if not isinstance(payload, dict) or not payload:
        return [
            VSetValidationError("vset.payload_invalid", "payload must be a non-empty object")
        ]
    missing = [key for key in KIND_PAYLOAD_KEYS[kind] if key not in payload]
    if missing:
        return [
            VSetValidationError(
                "vset.payload_invalid",
                f"{kind} payload missing {missing}",
            )
        ]
    return []


