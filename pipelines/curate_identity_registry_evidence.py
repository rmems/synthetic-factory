#!/usr/bin/env python3
"""Per-profile rights-evidence fields on hosted factory-registry rows."""

from __future__ import annotations

import re
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry_evidence")
    from .curate_identity_json import IdentityCurationError
    from .curate_identity_registry_sources import require_simulator_sources
    from .rights_mapping import (
        PROCEDURAL_PROFILE_ID,
        SHA256_RE,
        SIMULATOR_PROFILE_ID,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry_evidence"
    )
    from curate_identity_json import IdentityCurationError
    from curate_identity_registry_sources import require_simulator_sources
    from rights_mapping import (
        PROCEDURAL_PROFILE_ID,
        SHA256_RE,
        SIMULATOR_PROFILE_ID,
    )


# Sealed from pipelines/oracle_grounded/fault_simulator.py at this commit;
# UTF-8 source with CRLF/CR normalized to LF, SHA-256 prefixed with its algorithm.
REVIEWED_SIMULATOR_COMMIT = "6ca641465bbf8ce8339de1dce6ce77f77186e34a"
REVIEWED_SIMULATOR_DIGEST = "sha256:be267e0720662cf1f8c79b24384bd335df9ec127fce8184459e2e64e31c8d3e4"

_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CATALOG_AUTHORSHIP_VALUES = frozenset(
    {"human-authored", "permissive-upstream-license"}
)
_PROFILE_EVIDENCE_FIELDS = (
    "catalog_authorship",
    "generator_source_digest",
    "commit_sha",
    "module_digest",
)


def _require_prefixed_digest(raw: Mapping[str, Any], field: str, index: int) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise IdentityCurationError(
            f"factories[{index}].{field} must be lowercase sha256:<64 hex>"
        )
    return value


def _require_catalog_authorship(raw: Mapping[str, Any], index: int) -> str:
    value = raw.get("catalog_authorship")
    if not isinstance(value, str) or value not in CATALOG_AUTHORSHIP_VALUES:
        raise IdentityCurationError(
            f"factories[{index}] procedural rows require catalog_authorship "
            f"{sorted(CATALOG_AUTHORSHIP_VALUES)}"
        )
    return value


def _require_commit_sha(raw: Mapping[str, Any], index: int) -> str:
    value = raw.get("commit_sha")
    if not isinstance(value, str) or _GIT_COMMIT_RE.fullmatch(value) is None:
        raise IdentityCurationError(
            f"factories[{index}].commit_sha must be a 40-character lowercase git SHA"
        )
    return value


def _reject_unexpected_evidence(
    raw: Mapping[str, Any], index: int, fields: tuple[str, ...]
) -> None:
    unexpected = [field for field in fields if field in raw]
    if unexpected:
        raise IdentityCurationError(
            f"factories[{index}] unexpected rights evidence fields: {unexpected}"
        )


def _require_no_profile_evidence(raw: Mapping[str, Any], index: int) -> None:
    _reject_unexpected_evidence(raw, index, _PROFILE_EVIDENCE_FIELDS)


def _require_procedural_evidence(raw: Mapping[str, Any], index: int) -> None:
    _require_catalog_authorship(raw, index)
    _require_prefixed_digest(raw, "generator_source_digest", index)
    _reject_unexpected_evidence(raw, index, ("commit_sha", "module_digest"))
    raise IdentityCurationError(
        f"factories[{index}] procedural-attested has no independently reviewed source assignment; "
        "use the separately sealed v0.3 code-repair route"
    )


def _require_simulator_assignment(raw: Mapping[str, Any], index: int) -> None:
    expected = {
        "path_id": "fault-recovery-simulator-factory",
        "payload_factory": "fault-recovery-simulator-factory",
        "record_kinds": ["thalamic"],
        "identity_authoritative": True,
        "publication_target": None,
        "training_ready_policy": "never",
        "allowed_curation_lanes": ["curate_identity"],
        "provenance_contract_by_kind": {"thalamic": "require_state_claim"},
    }
    for field, value in expected.items():
        if raw.get(field) != value:
            raise IdentityCurationError(f"factories[{index}].{field} differs from reviewed simulator assignment")


def _require_simulator_evidence(raw: Mapping[str, Any], index: int) -> None:
    commit = _require_commit_sha(raw, index)
    digest = _require_prefixed_digest(raw, "module_digest", index)
    if (commit, digest) != (REVIEWED_SIMULATOR_COMMIT, REVIEWED_SIMULATOR_DIGEST):
        raise IdentityCurationError(f"factories[{index}] simulator pins differ from reviewed module")
    _reject_unexpected_evidence(
        raw, index, ("catalog_authorship", "generator_source_digest")
    )
    _require_simulator_assignment(raw, index)
    require_simulator_sources()


_PROFILE_EVIDENCE_CHECKERS = {
    PROCEDURAL_PROFILE_ID: _require_procedural_evidence,
    SIMULATOR_PROFILE_ID: _require_simulator_evidence,
}


def require_profile_evidence(raw: Mapping[str, Any], index: int) -> None:
    checker = _PROFILE_EVIDENCE_CHECKERS.get(
        raw["rights_profile_id"], _require_no_profile_evidence
    )
    checker(raw, index)


if __package__:
    _expose_package_sibling(__name__)
