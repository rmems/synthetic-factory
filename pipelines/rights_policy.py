#!/usr/bin/env python3
"""Strict loading and semantic validation for rights-policy v1."""

from __future__ import annotations

import json
import math
import sys
from itertools import product
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy")
    from .rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        MAPPING_PATH,
        MAPPING_VERSION,
        POLICY_DOCUMENT_TYPE,
        POLICY_VERSION,
        PROJECT_TRAINING_POLICIES,
        REQUIRED_PROFILE_IDS,
        UNKNOWN_PROVENANCE_PROFILE_ID,
        RightsPolicyError,
        policy_error,
        require_nonempty_string,
        require_unique_strings,
        sha256_digest,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy"
    )
    from rights_mapping import (
        CANONICAL_PROVIDERS,
        CHANNELS,
        EVIDENCE_STATUSES,
        EVIDENCE_STATUS_FIELDS,
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        MAPPING_PATH,
        MAPPING_VERSION,
        POLICY_DOCUMENT_TYPE,
        POLICY_VERSION,
        PROJECT_TRAINING_POLICIES,
        REQUIRED_PROFILE_IDS,
        UNKNOWN_PROVENANCE_PROFILE_ID,
        RightsPolicyError,
        policy_error,
        require_nonempty_string,
        require_unique_strings,
        sha256_digest,
    )


_TOP_LEVEL_FIELDS = frozenset(
    {
        "document_type",
        "policy_version",
        "mapping_version",
        "vocabularies",
        "evidence_status_fields",
        "invariants",
        "required_profile_ids",
        "reason_codes",
        "profiles",
        "rules",
    }
)
_VOCABULARY_FIELDS = frozenset(
    {
        "providers",
        "channels",
        "intended_use",
        "project_training_policy",
        "evidence_status",
    }
)
_PROFILE_FIELDS = frozenset(
    {
        "id",
        "intended_use",
        "project_training_policy",
        "evidence_statuses",
        "reason_codes",
    }
)
_RULE_FIELDS = frozenset(
    {
        "id",
        "providers",
        "channels",
        "rights_profile_id",
        "intended_use",
        "project_training_policy",
        "reason_codes",
    }
)
_INTENDED_USE_POLICY = {
    "research_only": "blocked",
    "training_candidate": "allowed",
}


def _exact_object(value: object, fields: frozenset[str], label: str, where: str) -> dict:
    if not isinstance(value, dict):
        raise policy_error(where, f"{label} must be an object")
    if set(value) != fields:
        raise policy_error(
            where,
            f"{label} fields must be exactly {sorted(fields)}",
        )
    return value


def _exact_vocabulary(
    vocabularies: dict,
    name: str,
    required: frozenset[str],
    where: str,
) -> tuple[str, ...]:
    values = require_unique_strings(vocabularies.get(name), name, where=where)
    if set(values) != set(required):
        raise policy_error(where, f"{name} must declare exactly {sorted(required)}")
    return values


def _catalogue_ids(entries: object, label: str, fields: frozenset[str], where: str):
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


def _validate_identity(document: object, where: str) -> dict:
    checked = _exact_object(document, _TOP_LEVEL_FIELDS, "rights policy", where)
    identities = (
        ("document_type", POLICY_DOCUMENT_TYPE),
        ("policy_version", POLICY_VERSION),
        ("mapping_version", MAPPING_VERSION),
    )
    for field, expected in identities:
        if checked.get(field) != expected:
            raise policy_error(where, f"unknown {field}")
    return checked


def _validate_vocabularies(document: dict, where: str) -> None:
    vocabularies = _exact_object(
        document.get("vocabularies"),
        _VOCABULARY_FIELDS,
        "vocabularies",
        where,
    )
    for name, required in (
        ("providers", CANONICAL_PROVIDERS),
        ("channels", CHANNELS),
        ("intended_use", INTENDED_USES),
        ("project_training_policy", PROJECT_TRAINING_POLICIES),
        ("evidence_status", EVIDENCE_STATUSES),
    ):
        _exact_vocabulary(vocabularies, name, required, where)

    status_fields = require_unique_strings(
        document.get("evidence_status_fields"),
        "evidence_status_fields",
        where=where,
    )
    if status_fields != EVIDENCE_STATUS_FIELDS:
        raise policy_error(
            where,
            f"evidence_status_fields must be exactly {list(EVIDENCE_STATUS_FIELDS)}",
        )
    invariants = _exact_object(
        document.get("invariants"),
        frozenset({"provider_training_status"}),
        "invariants",
        where,
    )
    if invariants["provider_training_status"] != "evidence_only":
        raise policy_error(
            where,
            "provider_training_status must be evidence_only",
        )


def _validate_reason_catalogue(document: dict, where: str) -> frozenset[str]:
    reason_ids = _catalogue_ids(
        document.get("reason_codes"),
        "reason_codes",
        frozenset({"id", "description"}),
        where,
    )
    for entry in document["reason_codes"]:
        require_nonempty_string(entry.get("description"), "description", where=where)
    return frozenset(reason_ids)


def _validate_profile(
    profile: dict,
    reason_ids: frozenset[str],
    where: str,
) -> None:
    profile_id = profile["id"]
    intended_use = profile.get("intended_use")
    project_policy = profile.get("project_training_policy")
    if not isinstance(intended_use, str) or intended_use not in INTENDED_USES:
        raise policy_error(where, f"profile {profile_id!r} has unknown intended_use")
    if (
        not isinstance(project_policy, str)
        or project_policy not in PROJECT_TRAINING_POLICIES
    ):
        raise policy_error(
            where,
            f"profile {profile_id!r} has unknown project_training_policy",
        )
    if _INTENDED_USE_POLICY[intended_use] != project_policy:
        raise policy_error(
            where,
            f"profile {profile_id!r} has inconsistent intended_use and project policy",
        )
    statuses = profile.get("evidence_statuses")
    if not isinstance(statuses, dict) or set(statuses) != set(EVIDENCE_STATUS_FIELDS):
        raise policy_error(
            where,
            f"profile {profile_id!r} evidence status fields must be exactly "
            f"{list(EVIDENCE_STATUS_FIELDS)}",
        )
    for field in EVIDENCE_STATUS_FIELDS:
        if (
            not isinstance(statuses[field], str)
            or statuses[field] not in EVIDENCE_STATUSES
        ):
            raise policy_error(
                where,
                f"profile {profile_id!r} {field} has unknown evidence status",
            )
    reasons = require_unique_strings(
        profile.get("reason_codes"), "reason_codes", where=where
    )
    unknown = sorted(set(reasons) - reason_ids)
    if unknown:
        raise policy_error(where, f"profile {profile_id!r} cites unknown reasons {unknown}")


def _validate_profiles(
    document: dict,
    reason_ids: frozenset[str],
    where: str,
) -> dict[str, dict]:
    required_ids = require_unique_strings(
        document.get("required_profile_ids"), "required_profile_ids", where=where
    )
    if set(required_ids) != set(REQUIRED_PROFILE_IDS):
        raise policy_error(
            where,
            f"required_profile_ids must be exactly {sorted(REQUIRED_PROFILE_IDS)}",
        )
    profile_ids = _catalogue_ids(
        document.get("profiles"), "profiles", _PROFILE_FIELDS, where
    )
    if set(profile_ids) != set(required_ids):
        raise policy_error(where, "profiles must declare every required profile id exactly")
    profiles = {profile["id"]: profile for profile in document["profiles"]}
    for profile in profiles.values():
        _validate_profile(profile, reason_ids, where)

    hosted = profiles[HOSTED_FRONTIER_PROFILE_ID]
    if (
        hosted["intended_use"] != "research_only"
        or hosted["project_training_policy"] != "blocked"
        or set(hosted["evidence_statuses"].values()) != {"unresolved"}
    ):
        raise policy_error(
            where,
            "hosted-frontier profile must be research_only/blocked with all statuses unresolved",
        )
    unknown = profiles[UNKNOWN_PROVENANCE_PROFILE_ID]
    if (
        unknown["intended_use"] != "research_only"
        or unknown["project_training_policy"] != "blocked"
    ):
        raise policy_error(where, "unknown-provenance profile must fail closed")
    return profiles


def _validate_rule_lists(rule: dict, rule_id: str, where: str):
    providers = require_unique_strings(rule.get("providers"), "providers", where=where)
    channels = require_unique_strings(rule.get("channels"), "channels", where=where)
    unknown_providers = sorted(set(providers) - CANONICAL_PROVIDERS)
    unknown_channels = sorted(set(channels) - CHANNELS)
    if unknown_providers:
        raise policy_error(where, f"rule {rule_id!r} has unknown providers {unknown_providers}")
    if unknown_channels:
        raise policy_error(where, f"rule {rule_id!r} has unknown channels {unknown_channels}")
    return providers, channels


def _validate_rules(
    document: dict,
    profiles: dict[str, dict],
    reason_ids: frozenset[str],
    where: str,
) -> None:
    _catalogue_ids(document.get("rules"), "rules", _RULE_FIELDS, where)
    covered_reasons: set[str] = set()
    covered_providers: set[str] = set()
    hosted_providers: set[str] = set()
    combinations: set[tuple[str, str, str]] = set()
    for rule in document["rules"]:
        rule_id = rule["id"]
        providers, channels = _validate_rule_lists(rule, rule_id, where)
        profile_id = rule.get("rights_profile_id")
        if not isinstance(profile_id, str) or profile_id not in profiles:
            raise policy_error(where, f"rule {rule_id!r} cites unknown profile")
        profile = profiles[profile_id]
        reasons = require_unique_strings(
            rule.get("reason_codes"), "reason_codes", where=where
        )
        unknown_reasons = sorted(set(reasons) - reason_ids)
        if unknown_reasons:
            raise policy_error(
                where,
                f"rule {rule_id!r} cites unknown reasons {unknown_reasons}",
            )
        if (
            rule.get("intended_use") != profile["intended_use"]
            or rule.get("project_training_policy")
            != profile["project_training_policy"]
            or list(reasons) != profile["reason_codes"]
        ):
            raise policy_error(where, f"rule {rule_id!r} authorizes a verdict outside profile")
        for combination in product(providers, channels):
            key = (combination[0], combination[1], profile_id)
            if key in combinations:
                raise policy_error(where, f"duplicate authorized combination {key!r}")
            combinations.add(key)
        covered_reasons.update(reasons)
        covered_providers.update(providers)
        if profile_id == HOSTED_FRONTIER_PROFILE_ID:
            hosted_providers.update(providers)

    if covered_providers != set(CANONICAL_PROVIDERS):
        raise policy_error(where, "rules do not provide exact canonical provider coverage")
    if hosted_providers != set(CANONICAL_PROVIDERS):
        raise policy_error(where, "hosted rules do not provide canonical provider coverage")
    uncovered = sorted(reason_ids - covered_reasons)
    if uncovered:
        raise policy_error(where, f"reason codes not covered by rules: {uncovered}")


def validate_rights_policy(document: object, *, where: str = "rights policy") -> dict:
    """Validate policy identity, catalogues, profiles, and authorizing rules."""

    checked = _validate_identity(document, where)
    _validate_vocabularies(checked, where)
    reason_ids = _validate_reason_catalogue(checked, where)
    profiles = _validate_profiles(checked, reason_ids, where)
    _validate_rules(checked, profiles, reason_ids, where)
    return checked


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON constant {token}")


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"JSON number is not finitely representable: {token}")
    return value


def _reject_unpaired_surrogates(value: object, path: str = "$") -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError(f"unpaired surrogate at {path}") from exc
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unpaired_surrogates(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unpaired_surrogates(key, f"{path}.<key>")
            _reject_unpaired_surrogates(item, f"{path}.{key}")


def load_rights_policy_bytes(payload: bytes, *, where: str = "rights policy bytes") -> dict:
    """Strictly decode and validate rights-policy JSON bytes."""

    if not isinstance(payload, bytes):
        raise policy_error(where, "policy input must be bytes")
    try:
        text = payload.decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
        )
        _reject_unpaired_surrogates(document)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise RightsPolicyError(f"{where}: invalid rights policy JSON: {exc}") from exc
    return validate_rights_policy(document, where=where)


def _load_rights_policy(path: Path) -> tuple[dict, bytes]:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RightsPolicyError(f"{path}: rights policy is unreadable: {exc}") from exc
    return load_rights_policy_bytes(payload, where=str(path)), payload


def load_rights_policy(path: str | Path | None = None) -> dict:
    """Load an explicit policy path, failing closed on bytes or semantics."""

    document, _ = _load_rights_policy(Path(path) if path is not None else MAPPING_PATH)
    return document


RIGHTS_POLICY, RIGHTS_POLICY_BYTES = _load_rights_policy(MAPPING_PATH)
RIGHTS_POLICY_SHA256 = sha256_digest(RIGHTS_POLICY_BYTES)
PROVIDERS = frozenset(RIGHTS_POLICY["vocabularies"]["providers"])
RIGHTS_CHANNELS = frozenset(RIGHTS_POLICY["vocabularies"]["channels"])
RIGHTS_PROFILES = tuple(RIGHTS_POLICY["profiles"])
RIGHTS_RULES = tuple(RIGHTS_POLICY["rules"])
REASON_CODES = frozenset(item["id"] for item in RIGHTS_POLICY["reason_codes"])


if __package__:
    _expose_package_sibling(__name__)
