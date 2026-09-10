"""Independently sealed procedural source authority; no hosted policy vocabulary.

Catalog rebuilds update the reviewed JSON pins and POLICY_SHA256 below in the
same review. Caller-supplied JSON cannot authorize a new source or generator.
The snapshot loaded at import remains immutable for the process lifetime.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from ._contract import bind_import_twin, load_strict_json

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "schemas/procedural-source-policy-v1.json"
# Independent trust anchor: update only with the reviewed catalog/policy change.
POLICY_SHA256 = "e364aebf97be641b06f8cf88afc1a0361d89cb2fff0b80741f81e49c6a719a74"
PROCEDURAL_FIELDS = frozenset({
    "source_type", "generator_ownership", "generation_method", "source_license_evidence",
    "procedural_policy_sha256", "catalog_id", "catalog_sha256", "programs_sha256",
})


class SourcePolicyError(ValueError):
    """A procedural authority differs from the reviewed source policy."""


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def load_policy(path: Path = POLICY_PATH) -> Mapping[str, Any]:
    """Read exact trusted bytes; alternate paths have no independent authority."""
    try:
        raw = path.read_bytes()
        value = load_strict_json(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise SourcePolicyError(f"procedural policy unreadable or invalid: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != POLICY_SHA256:
        raise SourcePolicyError("procedural policy differs from independently reviewed bytes")
    return _freeze(value)


POLICY = load_policy()


def reviewed_row() -> dict[str, Any]:
    """Fresh registry representation of the sealed, single approved route."""
    result = {key: POLICY[key] for key in (
        "path_id", "generator", "generator_version", "generator_ownership", "generation_method",
        "catalog_id", "catalog_sha256", "programs_sha256", "intended_use",
        "project_training_policy", "publication_target",
    )}
    result.update(
        source_type="procedural", payload_factory=POLICY["path_id"],
        source_license_evidence=dict(POLICY["source_license_evidence"]),
        procedural_policy_sha256=POLICY_SHA256, record_kinds=["code_repair"],
        identity_authoritative=True, training_ready_policy="fresh_code_repair_gate",
        allowed_curation_lanes=["curate_identity"],
        provenance_contract_by_kind={"code_repair": "preserve_oracle_envelope"},
    )
    return result


def validate_registry_row(raw: Any) -> None:
    """Only the exact reviewed discriminated row grants procedural authority."""
    if not isinstance(raw, Mapping) or dict(raw) != reviewed_row():
        raise SourcePolicyError("procedural registry row drifts from independently sealed policy")


bind_import_twin(__name__)
