#!/usr/bin/env python3
"""Placeholder profile field shape and blocked-verdict checks."""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy_placeholders")
    from . import rights_mapping as _rights_mapping
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy_placeholders"
    )
    import rights_mapping as _rights_mapping


PLACEHOLDER_PROFILE_IDS = _rights_mapping.PLACEHOLDER_PROFILE_IDS
UNBLOCK_TERMS_SNAPSHOT_FIELD = _rights_mapping.UNBLOCK_TERMS_SNAPSHOT_FIELD
policy_error = _rights_mapping.policy_error
require_hash = _rights_mapping.require_hash


def extra_profile_fields(profile_id: str) -> frozenset[str]:
    """Return the extra fields a terms-placeholder profile must declare."""

    if profile_id in PLACEHOLDER_PROFILE_IDS:
        return frozenset({UNBLOCK_TERMS_SNAPSHOT_FIELD})
    return frozenset()


def validate_placeholder_unblock(profile: dict, profile_id: str, where: str) -> None:
    """Accept a snapshot hash on a placeholder without changing its verdict."""

    if profile_id not in PLACEHOLDER_PROFILE_IDS:
        return
    value = profile.get(UNBLOCK_TERMS_SNAPSHOT_FIELD)
    if value is None:
        return
    require_hash(value, UNBLOCK_TERMS_SNAPSHOT_FIELD, where=where)


def require_placeholder_verdicts(profiles: dict[str, dict], where: str) -> None:
    """Keep DeepSeek and Nemotron profiles blocked until a reviewed profile change."""

    for profile_id in PLACEHOLDER_PROFILE_IDS:
        placeholder = profiles[profile_id]
        _require_unresolved_evidence(placeholder, profile_id, where)
        placeholder_verdict = (
            placeholder["intended_use"],
            placeholder["project_training_policy"],
        )
        if placeholder_verdict != ("research_only", "blocked"):
            raise policy_error(
                where,
                f"profile {profile_id!r} must remain a blocked terms placeholder",
            )


def _require_unresolved_evidence(profile: dict, profile_id: str, where: str) -> None:
    statuses = profile["evidence_statuses"]
    if any(statuses[field] != "unresolved" for field in _rights_mapping.EVIDENCE_STATUS_FIELDS):
        raise policy_error(where, f"profile {profile_id!r} must keep all terms evidence unresolved")


if __package__:
    _expose_package_sibling(__name__)
