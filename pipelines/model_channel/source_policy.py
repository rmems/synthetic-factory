"""Independently sealed model-channel source authority.

The snapshot loaded at import remains immutable for the process lifetime.
Caller-supplied JSON cannot authorize a new local or OpenRouter identity.
Pins live here rather than as model-specific literals in shared pipelines.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from ._contract import bind_import_twin, freeze, load_strict_json

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "schemas/model-channel-source-policy-v1.json"
# Independent trust anchor: update only with the reviewed catalog change.
POLICY_SHA256 = "bc17bbeec8bfe3d26b777fa25b1d6d68bec9e03c68c4104aa816e2464c0fdc55"
MODEL_CHANNEL_FIELDS = frozenset({
    "model_id",
    "model_revision",
    "generation_surface",
    "runtime_tag",
    "model_channel_policy_sha256",
})


class SourcePolicyError(ValueError):
    """A model-channel authority differs from the reviewed source policy."""


def load_policy(path: Path = POLICY_PATH) -> Mapping[str, Any]:
    """Read exact trusted bytes; alternate paths have no independent authority."""
    try:
        raw = path.read_bytes()
        value = load_strict_json(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise SourcePolicyError(
            f"model-channel policy unreadable or invalid: {exc}"
        ) from exc
    if hashlib.sha256(raw).hexdigest() != POLICY_SHA256:
        raise SourcePolicyError(
            "model-channel policy differs from independently reviewed bytes"
        )
    return freeze(value)


POLICY = load_policy()


def _catalog_rows() -> tuple[Mapping[str, Any], ...]:
    rows = POLICY.get("rows")
    if not isinstance(rows, tuple) or not rows:
        raise SourcePolicyError("model-channel policy must declare reviewed rows")
    return rows


def _public_row(row: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result.update(
        source_type="model_channel", payload_factory=row["path_id"],
        model_channel_policy_sha256=POLICY_SHA256,
        source_license_evidence=dict(row["source_license_evidence"]),
        record_kinds=list(row["record_kinds"]),
        allowed_curation_lanes=list(row["allowed_curation_lanes"]),
        provenance_contract_by_kind=dict(row["provenance_contract_by_kind"]),
    )
    return result


def reviewed_row(path_id: str) -> dict[str, Any]:
    """Fresh registry representation of one sealed, approved model-channel route."""
    for row in _catalog_rows():
        if row["path_id"] == path_id:
            return _public_row(row)
    raise SourcePolicyError(f"unknown reviewed model-channel path_id: {path_id}")


def reviewed_rows() -> tuple[dict[str, Any], ...]:
    """Fresh registry representations of every sealed model-channel route."""
    return tuple(reviewed_row(row["path_id"]) for row in _catalog_rows())


def validate_registry_row(raw: Any) -> None:
    """Only the exact reviewed discriminated row grants model-channel authority."""
    if not isinstance(raw, Mapping):
        raise SourcePolicyError("model-channel registry row must be an object")
    if raw.get("identity_authoritative") is not True:
        raise SourcePolicyError("model-channel registry row must be identity-authoritative")
    path_id = raw.get("path_id")
    if not isinstance(path_id, str) or not path_id:
        raise SourcePolicyError("model-channel registry row must name a path_id")
    _require_reviewed_row(raw, path_id)


def _require_reviewed_row(raw: Mapping, path_id: str) -> None:
    if dict(raw) != reviewed_row(path_id):
        raise SourcePolicyError(
            "model-channel registry row drifts from independently sealed policy"
        )


def claims_model_channel_route(raw: Any) -> bool:
    """Identify fields forbidden on hosted rows, including older registry schemas."""
    if not isinstance(raw, Mapping):
        return False
    if raw.get("source_type") == "model_channel":
        return True
    return bool(MODEL_CHANNEL_FIELDS.intersection(raw))


bind_import_twin(__name__)
