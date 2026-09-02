#!/usr/bin/env python3
"""Small shared primitives for rights-policy loading and classification."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_mapping")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_mapping"
    )


POLICY_DOCUMENT_TYPE = "rights_policy"
POLICY_VERSION = "rights-policy-v1"
MAPPING_VERSION = "rights-mapping-v1"
MAPPING_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "rights-policy-v1.mapping.json"
)

CANONICAL_PROVIDERS = frozenset({"anthropic", "meta", "openai", "xai"})
CHANNELS = frozenset({"consumer", "api", "enterprise", "local"})
INTENDED_USES = frozenset({"research_only", "training_candidate"})
PROJECT_TRAINING_POLICIES = frozenset({"blocked", "allowed"})
EVIDENCE_STATUSES = frozenset({"allowed", "restricted", "unresolved"})
EVIDENCE_STATUS_FIELDS = (
    "research_retention_status",
    "research_evaluation_status",
    "redistribution_status",
    "provider_training_status",
    "weight_publication_status",
)

HOSTED_FRONTIER_PROFILE_ID = "hosted-frontier-research-only-v1"
UNKNOWN_PROVENANCE_PROFILE_ID = "unknown-provenance-fail-closed-v1"
REQUIRED_PROFILE_IDS = frozenset(
    {HOSTED_FRONTIER_PROFILE_ID, UNKNOWN_PROVENANCE_PROFILE_ID}
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class RightsPolicyError(ValueError):
    """Raised when rights policy or a rights envelope fails closed."""


def policy_error(where: str, message: str) -> RightsPolicyError:
    return RightsPolicyError(f"{where}: {message}")


def sha256_digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def require_hash(value: object, field: str, *, where: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise policy_error(where, f"{field} must be lowercase sha256:<64 hex>")
    return value


def require_nonempty_string(value: object, field: str, *, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise policy_error(where, f"{field} must be a nonempty string")
    return value


def require_unique_strings(value: object, field: str, *, where: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        raise policy_error(where, f"{field} must be a unique nonempty list of strings")
    return tuple(value)


if __package__:
    _expose_package_sibling(__name__)
