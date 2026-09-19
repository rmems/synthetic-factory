"""Independently sealed native parity authority for research-only assembly."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("curate_parity_policy")
    from . import curate_identity_json as _json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("curate_parity_policy")
    import curate_identity_json as _json

POLICY_PATH = Path(__file__).resolve().parents[1] / "schemas/parity-source-policy-v1.json"
# Reviewed together with the producer closure; update only after combined source freeze.
POLICY_SHA256 = "a5f4d9b75b6ecdc851e7ac801dceef728268527368ab233e5c6a73d56a504243"
KINDS = frozenset({"hardware_parity", "nir_equivalence"})
FACTORIES = frozenset({"hardware-parity-spike-trajectories", "nir-cross-runtime-equivalence"})


class ParityPolicyError(ValueError):
    """Parity research authority or source validation failed."""


def load_policy(path=POLICY_PATH):
    try:
        payload = Path(path).read_bytes()
        if hashlib.sha256(payload).hexdigest() != POLICY_SHA256:
            raise ParityPolicyError("parity policy differs from independently reviewed bytes")
        return _json._strict_json_loads(payload.decode("utf-8"))
    except (OSError, ValueError, RecursionError) as exc:
        raise ParityPolicyError(f"parity policy unreadable or invalid: {exc}") from exc


def reviewed_row(kind):
    for row in load_policy()["rows"]:
        if row["record_kinds"] == [kind]:
            return dict(row, parity_policy_sha256=POLICY_SHA256)
    raise ParityPolicyError("unreviewed native parity kind")


def _representation(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_registry_row(raw):
    if not isinstance(raw, Mapping):
        raise ParityPolicyError("parity registry row must be an object")
    kinds = raw.get("record_kinds")
    if not isinstance(kinds, list) or len(kinds) != 1:
        raise ParityPolicyError("parity registry requires exactly one reviewed kind")
    if _representation(dict(raw)) != _representation(reviewed_row(kinds[0])):
        raise ParityPolicyError("parity registry row drifts from independently sealed policy")


def claims_parity_route(raw):
    if not isinstance(raw, Mapping):
        return False
    kinds = raw.get("record_kinds")
    declared = isinstance(kinds, list) and any(kind in KINDS for kind in kinds if isinstance(kind, str))
    path = raw.get("path_id")
    canonical_path = isinstance(path, str) and path in FACTORIES
    return (raw.get("source_type") == "frontier_session" or "parity_policy_sha256" in raw
            or canonical_path or declared)


def require_row(row, kind):
    expected = reviewed_row(kind)
    if row is None:
        raise ParityPolicyError("native parity source directory has no reviewed authority")
    actual = {key: getattr(row, key, None) for key in expected}
    actual["record_kinds"] = sorted(actual["record_kinds"])
    actual["allowed_curation_lanes"] = list(actual["allowed_curation_lanes"])
    actual["provenance_contract_by_kind"] = dict(actual["provenance_contract_by_kind"])
    validate_registry_row(actual)


if __package__:
    _expose_package_sibling(__name__)
