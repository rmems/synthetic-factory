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
    from rights_mapping import (
        PROCEDURAL_PROFILE_ID,
        SHA256_RE,
        SIMULATOR_PROFILE_ID,
    )


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
    if value not in CATALOG_AUTHORSHIP_VALUES:
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


def _require_simulator_evidence(raw: Mapping[str, Any], index: int) -> None:
    _require_commit_sha(raw, index)
    _require_prefixed_digest(raw, "module_digest", index)
    _reject_unexpected_evidence(
        raw, index, ("catalog_authorship", "generator_source_digest")
    )


_PROFILE_EVIDENCE_CHECKERS = {
    PROCEDURAL_PROFILE_ID: _require_procedural_evidence,
    SIMULATOR_PROFILE_ID: _require_simulator_evidence,
}


def _require_profile_evidence(raw: Mapping[str, Any], index: int) -> None:
    checker = _PROFILE_EVIDENCE_CHECKERS.get(
        raw["rights_profile_id"], _require_no_profile_evidence
    )
    checker(raw, index)


if __package__:
    _expose_package_sibling(__name__)
