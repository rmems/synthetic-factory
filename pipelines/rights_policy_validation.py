#!/usr/bin/env python3
"""Structural and rule-coverage validation for rights-policy v1."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from itertools import product

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy_validation")
    from . import rights_mapping as _rights_mapping
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy_validation"
    )
    import rights_mapping as _rights_mapping


CANONICAL_PROVIDERS = _rights_mapping.CANONICAL_PROVIDERS
CHANNELS = _rights_mapping.CHANNELS
HOSTED_FRONTIER_PROFILE_ID = _rights_mapping.HOSTED_FRONTIER_PROFILE_ID
REQUIRED_PROFILE_IDS = _rights_mapping.REQUIRED_PROFILE_IDS
UNKNOWN_PROVENANCE_PROFILE_ID = _rights_mapping.UNKNOWN_PROVENANCE_PROFILE_ID
policy_error = _rights_mapping.policy_error
require_nonempty_string = _rights_mapping.require_nonempty_string
require_unique_strings = _rights_mapping.require_unique_strings


_RULE_FIELDS = frozenset({
    "id", "providers", "channels", "rights_profile_id", "intended_use",
    "project_training_policy", "reason_codes",
})


def _exact_object(value: object, fields: frozenset[str], label: str, where: str) -> dict:
    """Require an exact JSON object shape."""
    if not isinstance(value, dict):
        raise policy_error(where, f"{label} must be an object")
    if set(value) != fields:
        raise policy_error(
            where,
            f"{label} fields must be exactly {sorted(fields)}",
        )
    return value


def _catalogue_ids(
    entries: object,
    label: str,
    fields: frozenset[str],
    where: str,
) -> tuple[str, ...]:
    """Validate one nonempty, uniquely identified policy catalogue."""
    if not isinstance(entries, list) or not entries:
        raise policy_error(where, f"{label} must be a nonempty list")
    identifiers: list[str] = []
    for index, entry in enumerate(entries):
        checked = _exact_object(entry, fields, f"{label}[{index}]", where)
        identifiers.append(
            require_nonempty_string(checked.get("id"), "id", where=where)
        )
    if len(identifiers) != len(set(identifiers)):
        raise policy_error(where, f"duplicate {label} id")
    return tuple(identifiers)


def _validate_rule_lists(
    rule: dict,
    rule_id: str,
    where: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    providers = require_unique_strings(rule.get("providers"), "providers", where=where)
    channels = require_unique_strings(rule.get("channels"), "channels", where=where)
    unknown_providers = sorted(set(providers) - CANONICAL_PROVIDERS)
    unknown_channels = sorted(set(channels) - CHANNELS)
    if unknown_providers:
        raise policy_error(where, f"rule {rule_id!r} has unknown providers {unknown_providers}")
    if unknown_channels:
        raise policy_error(where, f"rule {rule_id!r} has unknown channels {unknown_channels}")
    return providers, channels


@dataclass(frozen=True)
class _ValidatedRule:
    identifier: str
    providers: tuple[str, ...]
    channels: tuple[str, ...]
    profile_id: str
    reasons: tuple[str, ...]


@dataclass
class _RuleCoverage:
    reasons: set[str] = field(default_factory=set)
    providers: set[str] = field(default_factory=set)
    profiles: set[str] = field(default_factory=set)
    hosted_providers: set[str] = field(default_factory=set)
    combinations: set[tuple[str, str, str]] = field(default_factory=set)


def _rule_verdict(rule: dict, reasons: tuple[str, ...]) -> tuple[object, ...]:
    return (
        rule.get("intended_use"),
        rule.get("project_training_policy"),
        list(reasons),
    )


def _validated_rule(
    rule: dict,
    profiles: dict[str, dict],
    reason_ids: frozenset[str],
    where: str,
) -> _ValidatedRule:
    rule_id = rule["id"]
    providers, channels = _validate_rule_lists(rule, rule_id, where)
    profile_id = rule.get("rights_profile_id")
    if not isinstance(profile_id, str) or profile_id not in profiles:
        raise policy_error(where, f"rule {rule_id!r} cites unknown profile")
    reasons = require_unique_strings(
        rule.get("reason_codes"), "reason_codes", where=where
    )
    unknown_reasons = sorted(set(reasons) - reason_ids)
    if unknown_reasons:
        raise policy_error(
            where,
            f"rule {rule_id!r} cites unknown reasons {unknown_reasons}",
        )
    profile = profiles[profile_id]
    verdict = _rule_verdict(rule, reasons)
    expected = (
        profile["intended_use"],
        profile["project_training_policy"],
        profile["reason_codes"],
    )
    if verdict != expected:
        raise policy_error(where, f"rule {rule_id!r} authorizes a verdict outside profile")
    return _ValidatedRule(rule_id, providers, channels, profile_id, reasons)


def _record_rule_coverage(
    coverage: _RuleCoverage,
    rule: _ValidatedRule,
    where: str,
) -> None:
    for provider, channel in product(rule.providers, rule.channels):
        key = (provider, channel, rule.profile_id)
        if key in coverage.combinations:
            raise policy_error(where, f"duplicate authorized combination {key!r}")
        coverage.combinations.add(key)
    coverage.reasons.update(rule.reasons)
    coverage.providers.update(rule.providers)
    coverage.profiles.add(rule.profile_id)
    if rule.profile_id == HOSTED_FRONTIER_PROFILE_ID:
        coverage.hosted_providers.update(rule.providers)


def _require_exact_providers(coverage: _RuleCoverage, where: str) -> None:
    if coverage.providers != set(CANONICAL_PROVIDERS):
        raise policy_error(where, "rules do not provide exact canonical provider coverage")


def _require_hosted_providers(coverage: _RuleCoverage, where: str) -> None:
    if coverage.hosted_providers != set(CANONICAL_PROVIDERS):
        raise policy_error(where, "hosted rules do not provide canonical provider coverage")


def _require_profile_paths(coverage: _RuleCoverage, where: str) -> None:
    missing_profiles = sorted(REQUIRED_PROFILE_IDS - coverage.profiles)
    if missing_profiles:
        raise policy_error(
            where,
            f"required profiles missing authorization paths: {missing_profiles}",
        )


def _require_reason_coverage(
    coverage: _RuleCoverage,
    reason_ids: frozenset[str],
    where: str,
) -> None:
    uncovered = sorted(reason_ids - coverage.reasons)
    if uncovered:
        raise policy_error(where, f"reason codes not covered by rules: {uncovered}")


def _require_fallback_coverage(coverage: _RuleCoverage, where: str) -> None:
    expected = set(product(CANONICAL_PROVIDERS, CHANNELS))
    actual = {
        (provider, channel)
        for provider, channel, profile_id in coverage.combinations
        if profile_id == UNKNOWN_PROVENANCE_PROFILE_ID
    }
    if actual != expected:
        raise policy_error(
            where,
            "unknown-provenance rule must provide exact provider/channel coverage",
        )


def _require_rule_coverage(
    coverage: _RuleCoverage,
    reason_ids: frozenset[str],
    where: str,
) -> None:
    _require_exact_providers(coverage, where)
    _require_hosted_providers(coverage, where)
    _require_profile_paths(coverage, where)
    _require_reason_coverage(coverage, reason_ids, where)
    _require_fallback_coverage(coverage, where)


def _validate_rules(
    document: dict,
    profiles: dict[str, dict],
    reason_ids: frozenset[str],
    where: str,
) -> None:
    """Validate every authorization rule and the complete coverage lattice."""
    _catalogue_ids(document.get("rules"), "rules", _RULE_FIELDS, where)
    coverage = _RuleCoverage()
    for rule in document["rules"]:
        checked = _validated_rule(rule, profiles, reason_ids, where)
        _record_rule_coverage(coverage, checked, where)
    _require_rule_coverage(coverage, reason_ids, where)


if __package__:
    _expose_package_sibling(__name__)
