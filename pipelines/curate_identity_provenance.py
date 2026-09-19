#!/usr/bin/env python3
"""Provenance claim vocabulary, resolution, and sealed mapping evidence.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single
File) by responsibility; every name is re-exported from ``curate_identity``
so existing ``curate_identity.X`` call sites and test seams resolve
unchanged.

Claim normalization is intentionally first-match ordered: a synthetic
narrative claiming live/production use remains designed even if it also
mentions simulated or HIL calibration.  ``map_claim`` is supplied per call
so the facade's documented patch seam stays live after this split.
"""

from __future__ import annotations

import copy
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_provenance")
    from . import curate_identity_json as _identity_json
    from . import curate_identity_sources as _sources
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_provenance"
    )
    import curate_identity_json as _identity_json
    import curate_identity_sources as _sources

IdentityCurationError = _identity_json.IdentityCurationError

CANONICAL_PROVENANCE = frozenset({"designed", "simulated", "hil"})
HIL_RE = re.compile(r"\bhil\b", re.IGNORECASE)
# Standalone 'real'/'live' claims only: 'realistic' and 'real-time' describe a
# simulation and must not be read as a real-world deployment claim.
REAL_WORLD_RE = re.compile(r"^(?:real|live)(?![\w-])", re.IGNORECASE)
_REAL_WORLD_TOKENS = ("actions live", "production")
_SIMULATED_TOKENS = ("simulat", "high-fidelity")


@dataclass(frozen=True)
class ProvenanceDependencies:
    """Live facade claim operations used while resolving provenance."""

    map_claim: Callable[[Any], str | None]


def is_real_world_claim(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip().casefold()
    return bool(
        REAL_WORLD_RE.match(normalized)
        or any(token in normalized for token in _REAL_WORLD_TOKENS)
    )


def _claim_keyword_kind(value: str) -> str | None:
    # Preserve the repository's documented first-match order.  A synthetic
    # narrative claiming live/production use remains designed even if it also
    # mentions simulated or HIL calibration.
    if is_real_world_claim(value):
        return "designed"
    if any(token in value for token in _SIMULATED_TOKENS):
        return "simulated"
    if "hardware-in-the-loop" in value or HIL_RE.search(value):
        return "hil"
    return None


def map_claim(claimed: Any) -> str | None:
    if not isinstance(claimed, str) or not claimed.strip():
        return None
    value = claimed.strip().lower()
    if value in CANONICAL_PROVENANCE:
        return value
    return _claim_keyword_kind(value)


def existing_claimed(provenance: Any, kind: str) -> Any:
    if not isinstance(provenance, Mapping) or provenance.get("kind") != kind:
        return None
    return copy.deepcopy(provenance.get("claimed"))


def _state_claim_resolution(
    owner: Mapping[str, Any], state: Mapping[str, Any], state_value: Any, kind: str
) -> tuple[str, Any, str]:
    # On a second pass over already-curated output, recover the original
    # claim so normalization remains idempotent rather than replacing it
    # with the canonical state value.
    claimed = copy.deepcopy(state_value)
    if isinstance(state_value, str) and state_value.strip().lower() == kind:
        recovered = existing_claimed(state.get("provenance"), kind)
        if recovered is None:
            recovered = existing_claimed(owner.get("provenance"), kind)
        if recovered is not None:
            claimed = recovered
    return kind, claimed, "state.sim_or_real"


def _provenance_field_resolution(
    owner: Mapping[str, Any], state: Mapping[str, Any], state_value: Any
) -> tuple[str | None, Any, str]:
    for basis, provenance in (
        ("state.provenance.kind", state.get("provenance")),
        ("owner.provenance.kind", owner.get("provenance")),
    ):
        if not isinstance(provenance, Mapping):
            continue
        candidate = provenance.get("kind")
        if candidate in CANONICAL_PROVENANCE:
            return str(candidate), copy.deepcopy(provenance.get("claimed")), basis
    return None, copy.deepcopy(state_value), "unresolved"


def resolve_provenance(
    owner: Mapping[str, Any], state: Mapping[str, Any], deps: ProvenanceDependencies
) -> tuple[str | None, Any, str]:
    state_value = state.get("sim_or_real") if "sim_or_real" in state else None
    kind = deps.map_claim(state_value)
    if kind is not None:
        return _state_claim_resolution(owner, state, state_value, kind)
    return _provenance_field_resolution(owner, state, state_value)


def provenance_snapshot(
    owner: Mapping[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "sim_or_real": {
            "present": "sim_or_real" in state,
            "value": copy.deepcopy(state.get("sim_or_real")),
        },
        "state_provenance": {
            "present": "provenance" in state,
            "value": copy.deepcopy(state.get("provenance")),
        },
        "owner_provenance": {
            "present": "provenance" in owner,
            "value": copy.deepcopy(owner.get("provenance")),
        },
    }


def _unresolved_resolution(state_path: str, reason: str, original: Any) -> dict[str, Any]:
    return {"path": state_path, "reason": reason, "original": original}


def collect_state_resolutions(
    owners: list[tuple[str, Mapping[str, Any]]], deps: ProvenanceDependencies
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    provenance_resolutions: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for owner_path, owner in owners:
        state = owner.get("state")
        state_path = _sources.pointer(owner_path, "state")
        if not isinstance(state, Mapping):
            unresolved.append(
                _unresolved_resolution(
                    state_path, "missing_or_non_object_state", copy.deepcopy(state)
                )
            )
            continue
        snapshot = provenance_snapshot(owner, state)
        provenance_kind, claimed, basis = resolve_provenance(owner, state, deps)
        if provenance_kind is None:
            unresolved.append(
                _unresolved_resolution(state_path, "unresolved_provenance", snapshot)
            )
            continue
        if provenance_kind == "real":
            raise IdentityCurationError(
                "identity must never emit provenance.kind=real"
            )
        provenance_resolutions.append(
            {
                "owner_path": owner_path,
                "state_path": state_path,
                "kind": provenance_kind,
                "claimed": claimed,
                "basis": basis,
                "original": snapshot,
            }
        )
    return provenance_resolutions, unresolved


def _child_items(value: Any, path: str) -> list[tuple[Any, str]]:
    if isinstance(value, Mapping):
        return [(item, f"{path}.{key}") for key, item in value.items()]
    if isinstance(value, list):
        return [(item, f"{path}[{index}]") for index, item in enumerate(value)]
    return []


def _walk_paths(value: Any, path: str, collect) -> list[str]:
    paths = list(collect(value, path))
    for item, child_path in _child_items(value, path):
        paths.extend(_walk_paths(item, child_path, collect))
    return paths


def _training_ready_hits(value: Any, path: str) -> list[str]:
    if isinstance(value, Mapping) and value.get("training_ready"):
        return [f"{path}.training_ready"]
    return []


def _residual_claim_hits(value: Any, path: str) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    hits: list[str] = []
    if is_real_world_claim(value.get("sim_or_real")):
        hits.append(f"{path}.sim_or_real")
    provenance = value.get("provenance")
    if isinstance(provenance, Mapping) and is_real_world_claim(provenance.get("kind")):
        hits.append(f"{path}.provenance.kind")
    return hits


def training_ready_true_paths(value: Any, path: str = "$") -> list[str]:
    return _walk_paths(value, path, _training_ready_hits)


def residual_real_claim_paths(value: Any, path: str = "$") -> list[str]:
    return _walk_paths(value, path, _residual_claim_hits)


def provenance_mapping_sha256(mapping: Mapping[str, Any]) -> str:
    payload = dict(mapping)
    payload.pop("mapping_sha256", None)
    return _identity_json.sha256_json(payload)


def seal_provenance_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    sealed = copy.deepcopy(dict(mapping))
    sealed["mapping_sha256"] = provenance_mapping_sha256(sealed)
    return sealed


if __package__:
    _expose_package_sibling(__name__)
