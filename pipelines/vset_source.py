"""Source-kind and payload shape checks for VSET records."""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_source")
    from .vset_constants import (
        KIND_PAYLOAD_KEYS,
        PROMETHEUS_FAMILIES,
        SOURCE_KINDS,
        SYNTHETIC_PACK_PREFIX,
        VSetValidationError,
        _contains_prometheus_marker,
        _normalized_identity_text,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_source"
    )
    from vset_constants import (
        KIND_PAYLOAD_KEYS,
        PROMETHEUS_FAMILIES,
        SOURCE_KINDS,
        SYNTHETIC_PACK_PREFIX,
        VSetValidationError,
        _contains_prometheus_marker,
        _normalized_identity_text,
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
    # The whole environment mapping is scanned: pack and task identities
    # (repo_pack_id, task_id) are as much lineage claims as the named
    # provenance keys, and additionalProperties keeps them writable.
    return _contains_prometheus_marker(env) or _contains_prometheus_marker(
        record.get("prometheus_lineage")
    )


def _real_family_claimed(env: Mapping[str, Any]) -> bool:
    claimed = env.get("claimed_source_kind")
    if isinstance(claimed, str) and _normalized_identity_text(claimed) == (
        "real-public-engineering"
    ):
        return True
    family = env.get("source_family")
    if not isinstance(family, str):
        return False
    return _normalized_identity_text(family) in PROMETHEUS_FAMILIES


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


if __package__:
    _expose_package_sibling(__name__)


