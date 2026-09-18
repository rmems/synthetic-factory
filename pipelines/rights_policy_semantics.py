#!/usr/bin/env python3
"""Required-profile defining reasons and fail-closed verdicts."""

from __future__ import annotations

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy_semantics")
    from . import rights_mapping as _rights_mapping
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy_semantics"
    )
    import rights_mapping as _rights_mapping


DEEPSEEK_PLACEHOLDER_PROFILE_ID = _rights_mapping.DEEPSEEK_PLACEHOLDER_PROFILE_ID
HOSTED_FRONTIER_PROFILE_ID = _rights_mapping.HOSTED_FRONTIER_PROFILE_ID
NEMOTRON_PLACEHOLDER_PROFILE_ID = _rights_mapping.NEMOTRON_PLACEHOLDER_PROFILE_ID
PROCEDURAL_PROFILE_ID = _rights_mapping.PROCEDURAL_PROFILE_ID
SIMULATOR_PROFILE_ID = _rights_mapping.SIMULATOR_PROFILE_ID
UNKNOWN_PROVENANCE_PROFILE_ID = _rights_mapping.UNKNOWN_PROVENANCE_PROFILE_ID
policy_error = _rights_mapping.policy_error


_REQUIRED_PROFILE_REASONS = {
    HOSTED_FRONTIER_PROFILE_ID: "HOSTED_FRONTIER_RESEARCH_ONLY",
    UNKNOWN_PROVENANCE_PROFILE_ID: "UNKNOWN_PROVENANCE",
    PROCEDURAL_PROFILE_ID: "PROCEDURAL_ATTESTED_LOCAL",
    SIMULATOR_PROFILE_ID: "SIMULATOR_ORACLE_PINNED",
    DEEPSEEK_PLACEHOLDER_PROFILE_ID: "DEEPSEEK_TERMS_SNAPSHOT_PENDING",
    NEMOTRON_PLACEHOLDER_PROFILE_ID: "NEMOTRON_TERMS_SNAPSHOT_PENDING",
}
_TRAINING_CANDIDATE_PROFILE_IDS = frozenset(
    {PROCEDURAL_PROFILE_ID, SIMULATOR_PROFILE_ID}
)
_HOSTED_FRONTIER_VERDICT = ("research_only", "blocked", {"unresolved"})
_BLOCKED_DECISION = ("research_only", "blocked")
_ALLOWED_DECISION = ("training_candidate", "allowed")
_CANDIDATE_EVIDENCE_STATUSES = ("allowed", "allowed", "unresolved", "unresolved", "unresolved")


def _decision_pair(profile: dict) -> tuple[str, str]:
    return (profile["intended_use"], profile["project_training_policy"])


def _require_defining_reasons(profiles: dict[str, dict], where: str) -> None:
    for profile_id, defining_reason in _REQUIRED_PROFILE_REASONS.items():
        if defining_reason not in profiles[profile_id]["reason_codes"]:
            raise policy_error(
                where,
                f"profile {profile_id!r} is missing its required defining reason "
                f"{defining_reason!r}",
            )


def _require_hosted_frontier_verdict(profiles: dict[str, dict], where: str) -> None:
    hosted = profiles[HOSTED_FRONTIER_PROFILE_ID]
    hosted_verdict = (
        hosted["intended_use"],
        hosted["project_training_policy"],
        set(hosted["evidence_statuses"].values()),
    )
    if hosted_verdict != _HOSTED_FRONTIER_VERDICT:
        raise policy_error(
            where,
            "hosted-frontier profile must be research_only/blocked with all statuses unresolved",
        )


def _require_unknown_provenance_verdict(profiles: dict[str, dict], where: str) -> None:
    unknown = profiles[UNKNOWN_PROVENANCE_PROFILE_ID]
    if _decision_pair(unknown) != _BLOCKED_DECISION:
        raise policy_error(where, "unknown-provenance profile must fail closed")


def _require_candidate_reasons(profile: dict, where: str) -> None:
    blocked_reasons = {
        reason for profile_id, reason in _REQUIRED_PROFILE_REASONS.items()
        if profile_id not in _TRAINING_CANDIDATE_PROFILE_IDS
    }
    if blocked_reasons.intersection(profile["reason_codes"]):
        raise policy_error(where, "allowed profile cannot carry fail-closed defining reasons")


def _require_training_candidate_verdicts(profiles: dict[str, dict], where: str) -> None:
    for profile_id in _TRAINING_CANDIDATE_PROFILE_IDS:
        candidate = profiles[profile_id]
        _require_candidate_reasons(candidate, where)
        _require_candidate_evidence_statuses(candidate, where)
        if _decision_pair(candidate) != _ALLOWED_DECISION:
            raise policy_error(
                where,
                f"profile {profile_id!r} must be training_candidate/allowed",
            )


def _require_candidate_evidence_statuses(profile: dict, where: str) -> None:
    statuses = tuple(profile["evidence_statuses"][field]
                     for field in _rights_mapping.EVIDENCE_STATUS_FIELDS)
    if statuses != _CANDIDATE_EVIDENCE_STATUSES:
        raise policy_error(where, "training-candidate evidence statuses differ from reviewed policy")


def validate_required_profile_semantics(profiles: dict[str, dict], where: str) -> None:
    """Require defining reasons and the fail-closed verdicts each profile owns."""

    _require_defining_reasons(profiles, where)
    _require_hosted_frontier_verdict(profiles, where)
    _require_unknown_provenance_verdict(profiles, where)
    _require_training_candidate_verdicts(profiles, where)


if __package__:
    _expose_package_sibling(__name__)
