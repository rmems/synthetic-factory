#!/usr/bin/env python3
"""Record-level reward classification and comparability-rule matching."""

from __future__ import annotations

import copy
from decimal import Decimal

from reward_mapping import (
    DISPOSITION_AMBIGUOUS,
    DISPOSITION_CONTAINER,
    DISPOSITION_DECLARED_TOTAL,
    DISPOSITION_MAGNITUDE_TERM,
    DISPOSITION_NARRATIVE,
    DISPOSITION_STRUCTURAL,
    DISPOSITION_UNIT_CALIBRATION,
    MAGNITUDE_COMPARABLE,
    RewardOntologyError,
    _UNSET,
    _decimal,
    _escape_signature_token,
    _json_number,
    _pointer,
    _pointer_unescape,
)
from reward_policy import (
    ANNOTATION_FIELD,
    CALIBRATION_KEYS,
    CANONICAL_SCOPE,
    CANONICAL_UNIT,
    CANONICAL_UNIT_USD,
    COMPARABILITY_RULES,
    DECLARED_TOTAL_KEY,
    MAGNITUDE_AGGREGATION,
    NARRATIVE_KEYS,
    PREFERENCE_POINTERS,
    PREFERENCE_RELATION,
    REASON_CODES,
    REWARD_KEYS,
    SOURCE_VOCABULARY,
    UNWEIGHTED_EXCLUDE,
    WEIGHTED_CONTAINERS,
)
from reward_units import _component_value, _extract_unit_usd


def _walk_rewards(value, tokens=(), reward_keys=None):
    if reward_keys is None:
        reward_keys = REWARD_KEYS
    if isinstance(value, dict):
        for key, child in value.items():
            if key == ANNOTATION_FIELD:
                continue
            child_tokens = (*tokens, key)
            if key in reward_keys:
                yield _pointer(child_tokens), child
            yield from _walk_rewards(child, child_tokens, reward_keys)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_rewards(child, (*tokens, index), reward_keys)


def _set_pointer_token(target, token, pointer):
    if isinstance(target, list):
        try:
            return target[int(token)]
        except (ValueError, IndexError) as exc:
            raise RewardOntologyError(
                f"sidecar pointer does not resolve: {pointer}"
            ) from exc
    if isinstance(target, dict) and token in target:
        return target[token]
    raise RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")


def _assign_pointer_token(target, token, value, pointer):
    if isinstance(target, list):
        try:
            target[int(token)] = copy.deepcopy(value)
            return
        except (ValueError, IndexError) as exc:
            raise RewardOntologyError(
                f"sidecar pointer does not resolve: {pointer}"
            ) from exc
    if isinstance(target, dict):
        target[token] = copy.deepcopy(value)
        return
    raise RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")


def _set_pointer(document, pointer, value):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise RewardOntologyError(f"invalid JSON pointer: {pointer!r}")
    tokens = [_pointer_unescape(token) for token in pointer[1:].split("/")]
    target = document
    for token in tokens[:-1]:
        target = _set_pointer_token(target, token, pointer)
    _assign_pointer_token(target, tokens[-1], value, pointer)


def value_type(value):
    """Return the mapping's value-type name for one source reward member.

    Booleans are reported as ``boolean``, and ``{"value": true}`` as a plain
    ``object``, because neither yields a numeric component. That is deliberately
    stricter than :func:`reward_signature`, which mirrors the audit's shape
    vocabulary rather than the arithmetic layer's numeric test.
    """
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float, Decimal)):
        return "number" if _decimal(value) is not None else "unknown"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        inner = value.get("value")
        if _decimal(inner) is not None:
            return "value-object"
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    return "unknown"


def reward_signature(value):
    """Return the structural shape signature for one reward scope.

    Identical to ``training_audit.reward_shape``. It is restated here so the
    ontology's own vocabulary census does not depend on the audit stack, and
    ``tests/test_curate_rewards.py`` pins the two definitions together.
    """
    if not isinstance(value, dict):
        return type(value).__name__
    parts = []
    for key, item in sorted(value.items()):
        if isinstance(item, dict):
            subtype = (
                "value-object"
                if isinstance(item.get("value"), (int, float))
                else "object"
            )
        elif isinstance(item, list):
            subtype = "array"
        else:
            subtype = type(item).__name__
        parts.append(f"{_escape_signature_token(key)}:{subtype}")
    return "|".join(parts)


def _disposition_for_types(key, types):
    types = set(types)
    if not types:
        return DISPOSITION_AMBIGUOUS
    if types <= {"number", "value-object"}:
        return DISPOSITION_MAGNITUDE_TERM
    if types == {"string"}:
        return DISPOSITION_NARRATIVE
    if types == {"object"}:
        return (
            DISPOSITION_CONTAINER
            if key in WEIGHTED_CONTAINERS
            else DISPOSITION_STRUCTURAL
        )
    if types <= {"object", "array"}:
        return DISPOSITION_STRUCTURAL
    return DISPOSITION_AMBIGUOUS


def disposition_for_observed_types(key, observed_types):
    """Apply the mapping's ordered disposition rules to one key's value types."""
    if key == DECLARED_TOTAL_KEY:
        return DISPOSITION_DECLARED_TOTAL
    if key in CALIBRATION_KEYS:
        return DISPOSITION_UNIT_CALIBRATION
    if key in NARRATIVE_KEYS:
        return DISPOSITION_NARRATIVE
    return _disposition_for_types(key, observed_types)


def component_disposition(key, value=_UNSET):
    """Return the conversion disposition the mapping assigns to one key.

    With a ``value``, the disposition is derived from that value's type, which
    is what the arithmetic layer actually sees. Without one, the frozen
    source-vocabulary census answers for keys observed in the mapped run and
    ``ambiguous_preserve_only`` answers for everything else, so an unseen key
    is never silently promoted to a magnitude term.
    """
    if value is not _UNSET:
        return disposition_for_observed_types(key, {value_type(value)})
    entry = SOURCE_VOCABULARY.get("component_keys", {}).get(key)
    observed = entry.get("observed_types", ()) if isinstance(entry, dict) else ()
    if not isinstance(observed, (list, tuple, set, frozenset)):
        observed = ()
    return disposition_for_observed_types(key, observed)


def contributes_to_total(key, value):
    """Report whether one member is summed as a component of the plain total."""
    return key not in UNWEIGHTED_EXCLUDE and _component_value(value) is not None

def _mapped_verdict(rule_id, payload=None, *, optional_reason_codes=()):
    """Build a verdict from the matched machine-readable policy rule."""
    rule = comparability_rule(rule_id)
    reasons = list(rule["reason_codes"])
    allowed = set(reasons) | set(rule.get("optional_reason_codes", ()))
    unknown = sorted(set(optional_reason_codes) - allowed)
    if unknown:
        raise RewardOntologyError(
            f"rule {rule_id} does not allow optional reason codes {unknown}"
        )
    reasons.extend(reason for reason in optional_reason_codes if reason not in reasons)
    return rule["comparability"], reasons, payload, rule_id


def _preference_optional_reasons(unit_statuses):
    optional_reasons = []
    if all(status == "explicit_usd_unit_calibration" for status in unit_statuses):
        optional_reasons.append("explicit_usd_unit_calibration")
    if "external_calibration_evidence" in unit_statuses:
        optional_reasons.append("external_calibration_evidence")
    return optional_reasons


def _preference_units(rewards_by_pointer, calibration):
    units = {}
    calibration_sources = {}
    unit_statuses = []
    for pointer in PREFERENCE_POINTERS:
        unit, status, calibration_source = _extract_unit_usd(
            rewards_by_pointer[pointer], calibration
        )
        units[pointer] = unit
        calibration_sources[pointer] = calibration_source
        unit_statuses.append(status)
    return units, calibration_sources, unit_statuses


def _classify_preference_calibrated(
    chosen_total,
    rejected_total,
    units,
    unit_statuses,
    arithmetic_by_pointer,
    calibration_sources,
    chosen_pointer,
    rejected_pointer,
):
    chosen_canonical = chosen_total * units[chosen_pointer] / CANONICAL_UNIT_USD
    rejected_canonical = rejected_total * units[rejected_pointer] / CANONICAL_UNIT_USD
    if chosen_canonical <= rejected_canonical:
        return _mapped_verdict("P04")
    return _mapped_verdict(
        "P05",
        _magnitude_payload(arithmetic_by_pointer, units, calibration_sources),
        optional_reason_codes=_preference_optional_reasons(unit_statuses),
    )


def _classify_preference_uncalibrated(
    chosen_total,
    rejected_total,
    unit_statuses,
    chosen_pointer,
    rejected_pointer,
):
    if chosen_total <= rejected_total:
        return _mapped_verdict("P04")
    if any("conflict" in status for status in unit_statuses):
        rule_id = "P06"
    elif any(status != "missing_unit_calibration" for status in unit_statuses):
        rule_id = "P07"
    else:
        rule_id = "P08"
    return _mapped_verdict(
        rule_id,
        {
            "preferred_json_pointer": chosen_pointer,
            "dispreferred_json_pointer": rejected_pointer,
            "relation": PREFERENCE_RELATION,
        },
    )


def _classify_preference(rewards_by_pointer, arithmetic_by_pointer, calibration):
    if set(rewards_by_pointer) != set(PREFERENCE_POINTERS):
        return _mapped_verdict("P01")
    chosen_pointer, rejected_pointer = PREFERENCE_POINTERS
    chosen_arithmetic = arithmetic_by_pointer[chosen_pointer]
    rejected_arithmetic = arithmetic_by_pointer[rejected_pointer]
    statuses = {chosen_arithmetic["status"], rejected_arithmetic["status"]}
    if "invalid" in statuses:
        return _mapped_verdict("P02")
    if statuses != {"valid"}:
        return _mapped_verdict("P03")
    chosen_total = _decimal(chosen_arithmetic["source_total"])
    rejected_total = _decimal(rejected_arithmetic["source_total"])
    if chosen_total is None or rejected_total is None:
        return _mapped_verdict("P03")
    units, calibration_sources, unit_statuses = _preference_units(
        rewards_by_pointer, calibration
    )
    if all(unit is not None for unit in units.values()):
        return _classify_preference_calibrated(
            chosen_total,
            rejected_total,
            units,
            unit_statuses,
            arithmetic_by_pointer,
            calibration_sources,
            chosen_pointer,
            rejected_pointer,
        )
    return _classify_preference_uncalibrated(
        chosen_total,
        rejected_total,
        unit_statuses,
        chosen_pointer,
        rejected_pointer,
    )


def _single_optional_reasons(unit_status):
    if unit_status == "explicit_usd_unit_calibration":
        return ["explicit_usd_unit_calibration"]
    if unit_status == "external_calibration_evidence":
        return ["external_calibration_evidence"]
    return []


def _classify_single(source_rewards, rewards_by_pointer, arithmetic_by_pointer, calibration):
    if len(source_rewards) != 1:
        return _mapped_verdict("S01")
    pointer = source_rewards[0]["json_pointer"]
    if pointer != CANONICAL_SCOPE:
        return _mapped_verdict("S02")
    result = arithmetic_by_pointer[pointer]
    if result["status"] == "invalid":
        return _mapped_verdict("S03")
    if result["status"] != "valid":
        return _mapped_verdict("S04")
    unit, unit_status, calibration_source = _extract_unit_usd(
        rewards_by_pointer[pointer], calibration
    )
    if unit is None:
        if "conflict" in unit_status:
            return _mapped_verdict("S05")
        if unit_status == "missing_risk_adjusted_semantics":
            return _mapped_verdict("S06")
        return _mapped_verdict("S07")
    return _mapped_verdict(
        "S08",
        _magnitude_payload(
            {pointer: result},
            {pointer: unit},
            {pointer: calibration_source},
        ),
        optional_reason_codes=_single_optional_reasons(unit_status),
    )


def _classify(source_rewards, arithmetic, calibration=None):
    """Return ``(comparability, reason_codes, payload, rule_id)``.

    Every return names the ``comparability_rules`` entry in the mapping that
    authorises it, and :func:`curate_record` refuses any verdict that does not
    match that entry's declared class and reason codes.
    """
    rewards_by_pointer = {
        item["json_pointer"]: item["value"] for item in source_rewards
    }
    arithmetic_by_pointer = {
        item["json_pointer"]: item for item in arithmetic
    }
    chosen_pointer, rejected_pointer = PREFERENCE_POINTERS
    is_preference = (
        chosen_pointer in rewards_by_pointer or rejected_pointer in rewards_by_pointer
    )
    if not source_rewards:
        return _mapped_verdict("R00")
    if is_preference:
        return _classify_preference(
            rewards_by_pointer, arithmetic_by_pointer, calibration
        )
    return _classify_single(
        source_rewards, rewards_by_pointer, arithmetic_by_pointer, calibration
    )


def classify_source_rewards(source_rewards, arithmetic, calibration=None):
    """Public 3-tuple classifier used by the promotion gate.

    Internal classification also names the mapping rule that authorised the
    verdict; the gate only consumes comparability, reason codes, and payload.
    """
    comparability, reason_codes, payload, _rule_id = _classify(
        source_rewards, arithmetic, calibration
    )
    return comparability, reason_codes, payload


def _magnitude_payload(arithmetic_by_pointer, units, calibration_sources):
    values = []
    for pointer in sorted(units):
        source_total = _decimal(arithmetic_by_pointer[pointer]["source_total"])
        unit = units[pointer]
        factor = unit / CANONICAL_UNIT_USD
        value = {
            "json_pointer": pointer,
            "source_total": _json_number(source_total),
            "source_unit_usd": _json_number(unit),
            "conversion_factor": _json_number(factor),
            "canonical_value": _json_number(source_total * factor),
        }
        calibration_source = calibration_sources.get(pointer)
        if calibration_source:
            value["calibration_source"] = calibration_source
        values.append(value)
    return {
        "canonical_unit": CANONICAL_UNIT,
        "aggregation": MAGNITUDE_AGGREGATION,
        "values": values,
    }


def _require_catalogued_reasons(reasons):
    unknown = sorted(set(reasons) - REASON_CODES)
    if unknown:
        raise RewardOntologyError(f"uncatalogued reason codes: {unknown}")


def comparability_rule(rule_id):
    """Return one declared comparability rule from the conversion policy."""
    for rule in COMPARABILITY_RULES:
        if rule["id"] == rule_id:
            return copy.deepcopy(rule)
    raise RewardOntologyError(f"undeclared comparability rule: {rule_id!r}")


def _layout_scope(source_rewards):
    """Map enumerated reward pointers onto a comparability-rule scope."""
    pointers = [
        item.get("json_pointer")
        for item in source_rewards
        if isinstance(item, dict)
    ]
    if any(
        pointer in PREFERENCE_POINTERS
        or (
            isinstance(pointer, str)
            and (pointer.startswith("/chosen/") or pointer.startswith("/rejected/"))
        )
        for pointer in pointers
    ):
        return "preference"
    if pointers:
        return "single"
    return "any"


def _annotation_scope(document):
    magnitude = document.get("magnitude")
    if isinstance(magnitude, dict) and isinstance(magnitude.get("values"), list):
        values = [
            {"json_pointer": value.get("json_pointer")}
            for value in magnitude["values"]
            if isinstance(value, dict)
        ]
        if values:
            return _layout_scope(values)
    return None


def _rule_accepts_verdict(rule, comparability, reason_codes, *, scope=None):
    if rule["comparability"] != comparability:
        return False
    emitted = set(reason_codes)
    if len(emitted) != len(reason_codes):
        return False
    required = set(rule["reason_codes"])
    optional = set(rule.get("optional_reason_codes", ()))
    if not required <= emitted <= required | optional:
        return False
    if comparability == MAGNITUDE_COMPARABLE and not emitted.intersection(
        {"explicit_usd_unit_calibration", "external_calibration_evidence"}
    ):
        return False
    if scope is not None and rule["scope"] not in {scope, "any"}:
        return False
    return True


def _require_declared_verdict(comparability, reason_codes, *, scope=None):
    """Require a stored class/reason pair to match at least one policy rule."""
    _require_catalogued_reasons(reason_codes)
    matches = [
        rule["id"]
        for rule in COMPARABILITY_RULES
        if _rule_accepts_verdict(
            rule, comparability, reason_codes, scope=scope
        )
    ]
    if not matches:
        raise RewardOntologyError(
            f"{comparability} with reason codes {sorted(reason_codes)} does not "
            "match any declared comparability rule"
        )
    return tuple(matches)


def _require_declared_rule(comparability, reason_codes, rule_id):
    """Refuse any verdict the machine-readable rule table does not authorise."""
    rule = comparability_rule(rule_id)
    if rule["comparability"] != comparability:
        raise RewardOntologyError(
            f"rule {rule_id} declares {rule['comparability']}, not {comparability}"
        )
    required = list(rule["reason_codes"])
    emitted = list(reason_codes)
    if not _rule_accepts_verdict(rule, comparability, emitted):
        raise RewardOntologyError(
            f"rule {rule_id} declares reason codes {sorted(required)}, "
            f"not {sorted(emitted)}"
        )
    if len(set(emitted)) != len(emitted):
        raise RewardOntologyError(f"rule {rule_id} emitted duplicate reason codes")
    _require_catalogued_reasons(emitted)
    return rule


