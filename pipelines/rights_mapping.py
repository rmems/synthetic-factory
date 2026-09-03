#!/usr/bin/env python3
"""Small shared primitives for rights-policy loading and classification."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

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


class RightsPolicyError(ValueError):  # noqa: D203,D211
    """Raised when rights policy or a rights envelope fails closed."""


def policy_error(where: str, message: str) -> RightsPolicyError:
    """Build a consistently scoped policy error."""
    return RightsPolicyError(f"{where}: {message}")


def sha256_digest(payload: bytes) -> str:
    """Return the canonical prefixed SHA-256 spelling."""
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def require_hash(value: object, field: str, *, where: str) -> str:
    """Require one canonical prefixed SHA-256 value."""
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise policy_error(where, f"{field} must be lowercase sha256:<64 hex>")
    return value


def require_nonempty_string(value: object, field: str, *, where: str) -> str:
    """Require a nonempty string without normalizing its public text."""
    if not isinstance(value, str) or not value.strip():
        raise policy_error(where, f"{field} must be a nonempty string")
    return value


def _invalid_string_list(field: str, where: str) -> RightsPolicyError:
    return policy_error(where, f"{field} must be a unique nonempty list of strings")


def _require_string_list(value: object, field: str, where: str) -> list[object]:
    if not isinstance(value, list):
        raise _invalid_string_list(field, where)
    if not value:
        raise _invalid_string_list(field, where)
    return value


def _require_nonempty_strings(values: list[object], field: str, where: str) -> None:
    for item in values:
        if not isinstance(item, str):
            raise _invalid_string_list(field, where)
        if not item.strip():
            raise _invalid_string_list(field, where)


def require_unique_strings(value: object, field: str, *, where: str) -> tuple[str, ...]:
    """Require a unique nonempty list of nonempty strings."""
    values = _require_string_list(value, field, where)
    _require_nonempty_strings(values, field, where)
    if len(values) != len(set(values)):
        raise _invalid_string_list(field, where)
    return tuple(values)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object while rejecting duplicate member names."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def reject_json_constant(token: str) -> None:
    """Reject non-standard JSON numeric constants."""
    raise ValueError(f"non-finite JSON constant {token}")


def parse_finite_json_float(token: str) -> float:
    """Parse a JSON float only when Python can represent it finitely."""
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number is not finitely representable: {token}")
    return value


def _list_children(value: list[object], path: str) -> list[tuple[str, object]]:
    return [(f"{path}[{index}]", item) for index, item in enumerate(value)]


def _dict_children(value: dict, path: str) -> list[tuple[str, object]]:
    children = [
        (f"{path}.<member-name:{index}>", key)
        for index, key in enumerate(value)
    ]
    children.extend(
        (f"{path}[{index}]", item) for index, item in enumerate(value.values())
    )
    return children


def _json_children(value: object, path: str) -> list[tuple[str, object]]:
    if isinstance(value, list):
        return _list_children(value, path)
    if isinstance(value, dict):
        return _dict_children(value, path)
    return []


def _reject_surrogate_text(value: str, path: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"unpaired surrogate at {path}") from exc


def _schedule_container(
    item: object,
    path: str,
    pending: list[tuple[str, object, bool]],
    active_containers: set[int],
) -> None:
    if not isinstance(item, (dict, list)):
        return
    identity = id(item)
    if identity in active_containers:
        raise ValueError(f"cyclic JSON container at {path}")
    active_containers.add(identity)
    pending.append((path, item, True))
    pending.extend(
        (child_path, child, False)
        for child_path, child in _json_children(item, path)
    )


def reject_unpaired_surrogates(value: object) -> None:
    """Reject strings that cannot be encoded as Unicode scalar-value text."""
    pending = [("$", value, False)]
    active_containers: set[int] = set()
    while pending:
        path, item, exiting = pending.pop()
        if exiting:
            active_containers.remove(id(item))
            continue
        if isinstance(item, str):
            _reject_surrogate_text(item, path)
            continue
        _schedule_container(item, path, pending, active_containers)


def parse_strict_json_bytes(payload: bytes) -> object:
    """Decode strict finite UTF-8 JSON with unique keys and scalar text."""
    document = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_json_constant,
        parse_float=parse_finite_json_float,
    )
    reject_unpaired_surrogates(document)
    return document


if __package__:
    _expose_package_sibling(__name__)
