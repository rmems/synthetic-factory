#!/usr/bin/env python3
"""Conservatively map legacy rewards into reward ontology v1.

This module is intentionally record-level. It never edits raw data and it does
not infer a common magnitude merely because component arithmetic reconciles.
Callers receive:

* a deep-copied record with a top-level ``reward_training`` annotation; and
* a hash-addressed sidecar containing exact copies of every source reward.

Only ``magnitude_comparable`` annotations expose canonical numeric values.
``canonical_magnitudes`` refuses both other comparability classes, and
``magnitude_training_cohort`` refuses a whole cohort the moment one member is
uncalibrated, so a magnitude-weighted set cannot be mixed by accident.

The optional CLI writes only caller-specified, previously nonexistent files:

    python3 pipelines/curate_rewards.py classify input.jsonl
    python3 pipelines/curate_rewards.py convert input.jsonl output.jsonl sidecars.jsonl

The conversion policy itself is not hard-coded here. Scopes, arithmetic
methods, unit-calibration evidence, comparability classes, reason codes, and
the ordered classification rules are all read from the machine-readable mapping
at ``schemas/reward-ontology-v1.mapping.json``, which also freezes the
2026-08-17 run's 510 reward component keys and 140 structural shapes. The
read-only census subcommand recomputes that vocabulary from any JSONL corpus:

    python3 pipelines/curate_rewards.py census input.jsonl --tables
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

ONTOLOGY_VERSION = "reward-ontology-v1"
MAPPING_VERSION = "reward-mapping-v1"
POLICY_DOCUMENT_TYPE = "reward_conversion_policy"
MAPPING_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "reward-ontology-v1.mapping.json"
)

MAGNITUDE_COMPARABLE = "magnitude_comparable"
SIGN_ORDER_ONLY = "sign_order_only"
EXCLUDE = "exclude_from_reward_training"

DISPOSITION_DECLARED_TOTAL = "declared_total"
DISPOSITION_UNIT_CALIBRATION = "unit_calibration"
DISPOSITION_NARRATIVE = "narrative_annotation"
DISPOSITION_CONTAINER = "component_container"
DISPOSITION_MAGNITUDE_TERM = "magnitude_term"
DISPOSITION_STRUCTURAL = "structural_context"
DISPOSITION_AMBIGUOUS = "ambiguous_preserve_only"
COMPONENT_DISPOSITIONS = (
    DISPOSITION_DECLARED_TOTAL,
    DISPOSITION_UNIT_CALIBRATION,
    DISPOSITION_NARRATIVE,
    DISPOSITION_CONTAINER,
    DISPOSITION_MAGNITUDE_TERM,
    DISPOSITION_STRUCTURAL,
    DISPOSITION_AMBIGUOUS,
)

ARITHMETIC_STATUSES = frozenset({"valid", "invalid", "unsupported"})
RULE_SCOPES = frozenset({"any", "preference", "single"})
REQUIRED_ARITHMETIC_METHODS = frozenset(
    {
        "declared_weighted_sum",
        "declared_weighted_sum_unresolved",
        "unweighted_component_sum",
        "unweighted_component_sum_unresolved",
        "no_numeric_total",
        "non_object_reward",
    }
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_UNSET = object()


class RewardOntologyError(ValueError):
    """Raised when a reward document violates ontology-v1 invariants."""


class MagnitudeNotComparable(RewardOntologyError):
    """Raised when a caller asks an uncalibrated record for magnitudes."""


def _policy_error(where, message):
    return RewardOntologyError(f"{where}: {message}")


def _mapping_str(container, key, where, *, prefix=None):
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _policy_error(where, f"{key} must be a nonempty string")
    if prefix is not None and not value.startswith(prefix):
        raise _policy_error(where, f"{key} must start with {prefix!r}")
    return value


def _mapping_str_list(container, key, where):
    value = container.get(key)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
        or len(set(value)) != len(value)
    ):
        raise _policy_error(where, f"{key} must be a unique nonempty list of strings")
    return tuple(value)


def _mapping_object(container, key, where):
    value = container.get(key)
    if not isinstance(value, dict) or not value:
        raise _policy_error(where, f"{key} must be a nonempty object")
    return value


def _mapping_positive(container, key, where):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _policy_error(where, f"{key} must be a number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise _policy_error(where, f"{key} must be a finite number") from exc
    if not number.is_finite() or number <= 0:
        raise _policy_error(where, f"{key} must be positive and finite")
    return number


def _mapping_pattern(container, key, where, *, groups=0):
    pattern = _mapping_str(container, key, where)
    try:
        compiled = re.compile(pattern, re.I)
    except re.error as exc:
        raise _policy_error(where, f"{key} is not a valid regular expression: {exc}") from exc
    if compiled.groups != groups:
        raise _policy_error(where, f"{key} must declare exactly {groups} capture group(s)")
    return compiled


def _validate_conversion_block(policy, where):
    conversion = _mapping_object(policy, "conversion", where)
    _mapping_str(conversion, "canonical_unit", where)
    _mapping_positive(conversion, "canonical_unit_usd", where)
    _mapping_str(conversion, "aggregation", where)
    _mapping_str(conversion, "required_semantics_substring", where)
    _mapping_str(conversion, "structured_unit_field", where)
    _mapping_str(conversion, "text_unit_field", where)
    _mapping_pattern(conversion, "usd_unit_pattern", where, groups=1)
    external = _mapping_object(conversion, "external_calibration", where)
    _mapping_pattern(external, "record_id_pattern", where, groups=0)
    _mapping_str(external, "factor_field", where)
    _mapping_str(external, "scope_field", where)
    return conversion


def _validate_arithmetic_block(policy, where):
    arithmetic = _mapping_object(policy, "arithmetic", where)
    _mapping_positive(arithmetic, "default_tolerance", where)
    _mapping_str(arithmetic, "declared_total_field", where)
    _mapping_str(arithmetic, "weights_field", where)
    _mapping_str(arithmetic, "rounding_decimals_field", where)
    _mapping_pattern(arithmetic, "rounding_declaration_pattern", where, groups=1)
    _mapping_str_list(arithmetic, "rounding_declaration_fields", where)
    containers = _mapping_str_list(arithmetic, "weighted_containers", where)
    nested = _mapping_str(arithmetic, "nested_component_key", where)
    if nested not in containers:
        raise _policy_error(where, "nested_component_key must be a declared weighted container")
    aliases = _mapping_object(arithmetic, "weight_aliases", where)
    for name in sorted(aliases):
        members = _mapping_str_list(aliases, name, where)
        if name not in members:
            raise _policy_error(where, f"weight_aliases[{name!r}] must contain its own key")
    groups = _mapping_object(arithmetic, "non_component_keys", where)
    expected_groups = {
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_UNIT_CALIBRATION,
        DISPOSITION_NARRATIVE,
    }
    if set(groups) != expected_groups:
        raise _policy_error(
            where, f"non_component_keys must declare exactly {sorted(expected_groups)}"
        )
    seen = set()
    for name in sorted(groups):
        members = _mapping_str_list(groups, name, where)
        if seen & set(members):
            raise _policy_error(where, "non_component_keys groups must be disjoint")
        seen.update(members)
    if len(groups[DISPOSITION_DECLARED_TOTAL]) != 1:
        raise _policy_error(where, "non_component_keys.declared_total must name one key")
    if arithmetic["declared_total_field"] != groups[DISPOSITION_DECLARED_TOTAL][0]:
        raise _policy_error(
            where, "declared_total_field must match non_component_keys.declared_total"
        )
    for field in ("weights_field", "rounding_decimals_field"):
        if arithmetic[field] not in groups[DISPOSITION_UNIT_CALIBRATION]:
            raise _policy_error(
                where, f"{field} must be a declared unit_calibration key"
            )
    methods = _mapping_object(arithmetic, "methods", where)
    if not REQUIRED_ARITHMETIC_METHODS <= set(methods):
        missing = sorted(REQUIRED_ARITHMETIC_METHODS - set(methods))
        raise _policy_error(where, f"arithmetic.methods is missing {missing}")
    return arithmetic


def _validate_rule_block(policy, where, classes, reason_codes):
    rules = policy.get("comparability_rules")
    if not isinstance(rules, list) or not rules:
        raise _policy_error(where, "comparability_rules must be a nonempty list")
    seen_ids = set()
    covered = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise _policy_error(where, "each comparability rule must be an object")
        rule_id = _mapping_str(rule, "id", where)
        if rule_id in seen_ids:
            raise _policy_error(where, f"duplicate comparability rule id {rule_id!r}")
        seen_ids.add(rule_id)
        _mapping_str(rule, "condition", where)
        scope = _mapping_str(rule, "scope", where)
        if scope not in RULE_SCOPES:
            raise _policy_error(where, f"rule {rule_id} declares unknown scope {scope!r}")
        comparability = _mapping_str(rule, "comparability", where)
        if comparability not in classes:
            raise _policy_error(
                where, f"rule {rule_id} declares unknown comparability {comparability!r}"
            )
        codes = _mapping_str_list(rule, "reason_codes", where)
        optional = ()
        if "optional_reason_codes" in rule:
            optional = _mapping_str_list(rule, "optional_reason_codes", where)
        unknown = sorted((set(codes) | set(optional)) - set(reason_codes))
        if unknown:
            raise _policy_error(where, f"rule {rule_id} cites uncatalogued reason codes {unknown}")
        covered.update(codes)
        covered.update(optional)
    orphans = sorted(set(reason_codes) - covered)
    if orphans:
        raise _policy_error(where, f"reason codes cited by no rule: {orphans}")
    return tuple(rules)


def validate_conversion_policy(document, *, where="conversion policy"):
    """Validate the machine-readable conversion policy and return it unchanged."""
    if not isinstance(document, dict):
        raise _policy_error(where, "conversion policy must be an object")
    if document.get("document_type") != POLICY_DOCUMENT_TYPE:
        raise _policy_error(where, "unknown conversion policy document_type")
    if document.get("ontology_version") != ONTOLOGY_VERSION:
        raise _policy_error(where, "unknown reward ontology version")
    if document.get("mapping_version") != MAPPING_VERSION:
        raise _policy_error(where, "unknown reward mapping version")

    policy = _mapping_object(document, "policy", where)
    _mapping_str(policy, "annotation_field", where)
    reward_keys = _mapping_str_list(policy, "reward_keys", where)
    canonical_scope = _mapping_str(policy, "canonical_scope", where, prefix="/")
    if canonical_scope[1:] not in reward_keys:
        raise _policy_error(where, "canonical_scope must name a declared reward key")
    preference = _mapping_object(policy, "preference_scope", where)
    preferred = _mapping_str(preference, "preferred", where, prefix="/")
    dispreferred = _mapping_str(preference, "dispreferred", where, prefix="/")
    if preferred == dispreferred:
        raise _policy_error(where, "preference pointers must be distinct")
    if _mapping_str(preference, "relation", where) != "preferred_gt_dispreferred":
        raise _policy_error(where, "unsupported preference relation")

    arithmetic = _validate_arithmetic_block(policy, where)
    conversion = _validate_conversion_block(policy, where)
    calibration_keys = arithmetic["non_component_keys"][DISPOSITION_UNIT_CALIBRATION]
    for field in ("structured_unit_field", "text_unit_field"):
        if conversion[field] not in calibration_keys:
            raise _policy_error(where, f"conversion.{field} must be a unit_calibration key")
    if conversion["required_semantics_substring"] != conversion[
        "required_semantics_substring"
    ].lower():
        raise _policy_error(
            where, "conversion.required_semantics_substring must be lowercase"
        )

    dispositions = _mapping_object(policy, "component_dispositions", where)
    if set(dispositions) != set(COMPONENT_DISPOSITIONS):
        raise _policy_error(
            where, f"component_dispositions must declare exactly {sorted(COMPONENT_DISPOSITIONS)}"
        )
    classes = _mapping_object(policy, "comparability_classes", where)
    if set(classes) != {MAGNITUDE_COMPARABLE, SIGN_ORDER_ONLY, EXCLUDE}:
        raise _policy_error(where, "comparability_classes must declare exactly the three classes")
    reason_codes = _mapping_object(policy, "reason_codes", where)
    for code, description in sorted(reason_codes.items()):
        if not isinstance(description, str) or not description.strip():
            raise _policy_error(where, f"reason code {code!r} has no description")
    _validate_rule_block(policy, where, classes, reason_codes)
    return document


def load_conversion_policy(path=None):
    """Read, validate, and return the machine-readable conversion policy."""
    path = Path(path) if path is not None else MAPPING_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RewardOntologyError(f"{path}: conversion policy is unreadable: {exc}") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RewardOntologyError(f"{path}: invalid conversion policy JSON: {exc}") from exc
    return validate_conversion_policy(document, where=str(path))


CONVERSION_POLICY = load_conversion_policy()
_POLICY = CONVERSION_POLICY["policy"]
_ARITHMETIC = _POLICY["arithmetic"]
_CONVERSION = _POLICY["conversion"]

ANNOTATION_FIELD = _POLICY["annotation_field"]
REWARD_KEYS = frozenset(_POLICY["reward_keys"])
CANONICAL_SCOPE = _POLICY["canonical_scope"]
PREFERENCE_POINTERS = (
    _POLICY["preference_scope"]["preferred"],
    _POLICY["preference_scope"]["dispreferred"],
)
PREFERENCE_RELATION = _POLICY["preference_scope"]["relation"]

DEFAULT_TOLERANCE = Decimal(str(_ARITHMETIC["default_tolerance"]))
WEIGHTS_FIELD = _ARITHMETIC["weights_field"]
ROUNDING_DECIMALS_FIELD = _ARITHMETIC["rounding_decimals_field"]
ROUNDING_RE = re.compile(_ARITHMETIC["rounding_declaration_pattern"], re.I)
ROUNDING_FIELDS = tuple(_ARITHMETIC["rounding_declaration_fields"])
WEIGHTED_CONTAINERS = tuple(_ARITHMETIC["weighted_containers"])
NESTED_COMPONENT_KEY = _ARITHMETIC["nested_component_key"]
WEIGHT_ALIASES = {
    name: tuple(aliases) for name, aliases in _ARITHMETIC["weight_aliases"].items()
}
_NON_COMPONENT_GROUPS = _ARITHMETIC["non_component_keys"]
DECLARED_TOTAL_KEY = _NON_COMPONENT_GROUPS[DISPOSITION_DECLARED_TOTAL][0]
CALIBRATION_KEYS = frozenset(_NON_COMPONENT_GROUPS[DISPOSITION_UNIT_CALIBRATION])
NARRATIVE_KEYS = frozenset(_NON_COMPONENT_GROUPS[DISPOSITION_NARRATIVE])
UNWEIGHTED_EXCLUDE = frozenset(
    {DECLARED_TOTAL_KEY} | set(CALIBRATION_KEYS) | set(NARRATIVE_KEYS)
)
ARITHMETIC_METHODS = frozenset(_ARITHMETIC["methods"])

CANONICAL_UNIT = _CONVERSION["canonical_unit"]
CANONICAL_UNIT_USD = Decimal(str(_CONVERSION["canonical_unit_usd"]))
MAGNITUDE_AGGREGATION = _CONVERSION["aggregation"]
REQUIRED_SEMANTICS = _CONVERSION["required_semantics_substring"]
STRUCTURED_UNIT_FIELD = _CONVERSION["structured_unit_field"]
TEXT_UNIT_FIELD = _CONVERSION["text_unit_field"]
USD_UNIT_RE = re.compile(_CONVERSION["usd_unit_pattern"], re.I)
_EXTERNAL = _CONVERSION["external_calibration"]
RECORD_ID_RE = re.compile(_EXTERNAL["record_id_pattern"], re.I)
MIGRATION_FACTOR_FIELD = _EXTERNAL["factor_field"]
MIGRATION_SCOPE_FIELD = _EXTERNAL["scope_field"]

COMPARABILITY_CLASSES = frozenset(_POLICY["comparability_classes"])
REASON_CODES = frozenset(_POLICY["reason_codes"])
COMPARABILITY_RULES = tuple(_POLICY["comparability_rules"])
SOURCE_VOCABULARY = CONVERSION_POLICY.get("source_vocabulary", {})


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _pointer_escape(token) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _pointer_unescape(token) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _pointer(tokens) -> str:
    return "/" + "/".join(_pointer_escape(token) for token in tokens)


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


def _set_pointer(document, pointer, value):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise RewardOntologyError(f"invalid JSON pointer: {pointer!r}")
    tokens = [_pointer_unescape(token) for token in pointer[1:].split("/")]
    target = document
    for token in tokens[:-1]:
        if isinstance(target, list):
            try:
                target = target[int(token)]
            except (ValueError, IndexError) as exc:
                raise RewardOntologyError(
                    f"sidecar pointer does not resolve: {pointer}"
                ) from exc
        elif isinstance(target, dict) and token in target:
            target = target[token]
        else:
            raise RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")
    final = tokens[-1]
    if isinstance(target, list):
        try:
            target[int(final)] = copy.deepcopy(value)
        except (ValueError, IndexError) as exc:
            raise RewardOntologyError(
                f"sidecar pointer does not resolve: {pointer}"
            ) from exc
    elif isinstance(target, dict):
        target[final] = copy.deepcopy(value)
    else:
        raise RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _json_number(value: Decimal) -> float:
    return float(value)


def _component_value(value):
    direct = _decimal(value)
    if direct is not None:
        return direct
    if isinstance(value, dict):
        return _decimal(value.get("value"))
    return None


def value_type(value):
    """Return the mapping's value-type name for one source reward member.

    Booleans are reported as ``boolean``, and ``{"value": true}`` as a plain
    ``object``, because neither yields a numeric component. That is deliberately
    stricter than :func:`reward_signature`, which mirrors the audit's shape
    vocabulary rather than the arithmetic layer's numeric test.
    """
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        inner = value.get("value")
        if isinstance(inner, (int, float)) and not isinstance(inner, bool):
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
        parts.append(f"{key}:{subtype}")
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


def _reward_tolerance(reward) -> Decimal:
    decimals = reward.get(ROUNDING_DECIMALS_FIELD)
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        decimals = None
        for key in ROUNDING_FIELDS:
            text = reward.get(key)
            if not isinstance(text, str):
                continue
            match = ROUNDING_RE.search(text)
            if match:
                decimals = int(match.group(1))
                break
    if decimals is None:
        return DEFAULT_TOLERANCE
    rounded = Decimal("0.5") * (Decimal(10) ** -decimals)
    return max(DEFAULT_TOLERANCE, rounded)


def _weighted_total(reward, weights):
    containers = [reward]
    containers.extend(
        reward[key]
        for key in WEIGHTED_CONTAINERS
        if isinstance(reward.get(key), dict)
    )
    terms = []
    missing = []
    for key, raw_weight in weights.items():
        weight = _decimal(raw_weight)
        if weight is None:
            continue
        component = None
        for container in containers:
            for alias in WEIGHT_ALIASES.get(key, (key,)):
                if alias in container:
                    component = _component_value(container[alias])
                    if component is not None:
                        break
            if component is not None:
                break
        if component is None:
            missing.append(key)
        else:
            terms.append(weight * component)
    if missing or not terms:
        return None
    return sum(terms, Decimal(0))


def _unweighted_total(reward):
    component_container = reward.get(NESTED_COMPONENT_KEY)
    nested = isinstance(component_container, dict)
    siblings = [
        component
        for key, value in reward.items()
        if key not in UNWEIGHTED_EXCLUDE and not (nested and key == NESTED_COMPONENT_KEY)
        for component in [_component_value(value)]
        if component is not None
    ]
    if nested:
        if siblings:
            # Mixed legacy layout: publish-time validation sums the direct
            # numeric siblings while this nested map declares its own
            # components. Refuse to reconcile rather than claim an arithmetic
            # verdict the publish gate contradicts.
            return None
        values = [
            component
            for component in (
                _component_value(value) for value in component_container.values()
            )
            if component is not None
        ]
    else:
        values = siblings
    if not values:
        return None
    return sum(values, Decimal(0))


def assess_arithmetic(reward, pointer):
    """Return a machine-readable, conservative total reconciliation result."""
    base = {"json_pointer": pointer}
    if not isinstance(reward, dict):
        return {**base, "status": "unsupported", "method": "non_object_reward"}

    total = _decimal(reward.get(DECLARED_TOTAL_KEY))
    if total is None:
        return {**base, "status": "unsupported", "method": "no_numeric_total"}

    weights = reward.get(WEIGHTS_FIELD)
    if isinstance(weights, dict):
        recomputed = _weighted_total(reward, weights)
        method = "declared_weighted_sum"
    else:
        recomputed = _unweighted_total(reward)
        method = "unweighted_component_sum"
    if recomputed is None:
        return {
            **base,
            "status": "unsupported",
            "method": f"{method}_unresolved",
            "source_total": _json_number(total),
        }

    difference = abs(recomputed - total)
    tolerance = _reward_tolerance(reward)
    return {
        **base,
        "status": "valid" if difference <= tolerance else "invalid",
        "method": method,
        "source_total": _json_number(total),
        "recomputed_total": _json_number(recomputed),
        "absolute_difference": _json_number(difference),
        "tolerance": _json_number(tolerance),
    }


def _normalize_calibration(calibration):
    if calibration is None:
        return None
    if not isinstance(calibration, dict):
        raise RewardOntologyError("calibration must be an object")
    unit = _decimal(calibration.get("source_unit_usd"))
    evidence_ref = calibration.get("evidence_ref")
    if unit is None or unit <= 0:
        raise RewardOntologyError("calibration source_unit_usd must be positive")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        raise RewardOntologyError("calibration evidence_ref must be nonempty")
    factor = calibration.get("canonical_factor")
    if factor is not None:
        factor = _decimal(factor)
        if factor is None or factor <= 0 or factor != unit / CANONICAL_UNIT_USD:
            raise RewardOntologyError("calibration canonical_factor is inconsistent")
    return {
        "source_unit_usd": unit,
        "evidence_ref": evidence_ref.strip(),
    }


def _extract_unit_usd(reward, calibration=None):
    """Return (USD per native unit, status) from explicit, consistent evidence."""
    if not isinstance(reward, dict):
        return None, "unsupported_reward_object", None
    calibration = _normalize_calibration(calibration)
    units_text = reward.get(TEXT_UNIT_FIELD)
    parsed = None
    if isinstance(units_text, str):
        match = USD_UNIT_RE.search(units_text)
        if match:
            parsed = Decimal(match.group(1).replace(",", ""))

    structured_present = STRUCTURED_UNIT_FIELD in reward
    structured = (
        _decimal(reward.get(STRUCTURED_UNIT_FIELD)) if structured_present else None
    )
    if structured_present and (structured is None or structured <= 0):
        return None, "invalid_structured_unit_usd", None
    if parsed is not None and parsed <= 0:
        return None, "invalid_text_unit_usd", None
    if structured is not None and parsed is not None and structured != parsed:
        return None, "conflicting_unit_declarations", None

    unit = structured if structured is not None else parsed
    if calibration is not None:
        calibrated_unit = calibration["source_unit_usd"]
        if unit is not None and unit != calibrated_unit:
            return None, "calibration_evidence_conflict", None
        return (
            calibrated_unit,
            "external_calibration_evidence",
            calibration["evidence_ref"],
        )
    if unit is None:
        return None, "missing_unit_calibration", None
    if not isinstance(units_text, str) or REQUIRED_SEMANTICS not in units_text.lower():
        return None, "missing_risk_adjusted_semantics", None
    return unit, "explicit_usd_unit_calibration", "source_reward_fields"


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
    is_preference = chosen_pointer in rewards_by_pointer or rejected_pointer in rewards_by_pointer

    if not source_rewards:
        return EXCLUDE, ["no_source_reward"], None, "R00"

    if is_preference:
        if set(rewards_by_pointer) != set(PREFERENCE_POINTERS):
            return EXCLUDE, ["ambiguous_preference_reward_scopes"], None, "P01"
        chosen_arithmetic = arithmetic_by_pointer[chosen_pointer]
        rejected_arithmetic = arithmetic_by_pointer[rejected_pointer]
        statuses = {chosen_arithmetic["status"], rejected_arithmetic["status"]}
        if "invalid" in statuses:
            return EXCLUDE, ["reward_arithmetic_mismatch"], None, "P02"
        if statuses != {"valid"}:
            return EXCLUDE, ["unsupported_reward_layout"], None, "P03"

        chosen_total = _decimal(chosen_arithmetic["source_total"])
        rejected_total = _decimal(rejected_arithmetic["source_total"])
        if chosen_total is None or rejected_total is None:
            return EXCLUDE, ["unsupported_reward_layout"], None, "P03"
        if chosen_total <= rejected_total:
            return EXCLUDE, ["reward_order_conflicts_with_preference"], None, "P04"

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
        if all(unit is not None for unit in units.values()):
            reasons = [
                "explicit_usd_unit_calibration",
                "preference_order_verified",
                "reward_arithmetic_verified",
            ]
            if "external_calibration_evidence" in unit_statuses:
                reasons.append("external_calibration_evidence")
            return (
                MAGNITUDE_COMPARABLE,
                reasons,
                _magnitude_payload(
                    arithmetic_by_pointer,
                    units,
                    calibration_sources,
                ),
                "P05",
            )

        reasons = ["preference_order_verified"]
        if any("conflict" in status for status in unit_statuses):
            reasons.append("magnitude_calibration_conflict")
            rule_id = "P06"
        elif any(status != "missing_unit_calibration" for status in unit_statuses):
            reasons.append("magnitude_calibration_incomplete")
            rule_id = "P07"
        else:
            reasons.append("magnitude_calibration_missing")
            rule_id = "P08"
        return (
            SIGN_ORDER_ONLY,
            reasons,
            {
                "preferred_json_pointer": chosen_pointer,
                "dispreferred_json_pointer": rejected_pointer,
                "relation": PREFERENCE_RELATION,
            },
            rule_id,
        )

    if len(source_rewards) != 1:
        return EXCLUDE, ["multiple_reward_scopes"], None, "S01"
    pointer = source_rewards[0]["json_pointer"]
    if pointer != CANONICAL_SCOPE:
        return EXCLUDE, ["noncanonical_reward_scope"], None, "S02"
    result = arithmetic_by_pointer[pointer]
    if result["status"] == "invalid":
        return EXCLUDE, ["reward_arithmetic_mismatch"], None, "S03"
    if result["status"] != "valid":
        return EXCLUDE, ["unsupported_reward_layout"], None, "S04"
    unit, unit_status, calibration_source = _extract_unit_usd(
        rewards_by_pointer[pointer], calibration
    )
    if unit is None:
        if "conflict" in unit_status:
            return EXCLUDE, ["magnitude_calibration_conflict"], None, "S05"
        if unit_status == "missing_risk_adjusted_semantics":
            return EXCLUDE, ["magnitude_semantics_missing"], None, "S06"
        return EXCLUDE, ["magnitude_calibration_missing"], None, "S07"
    return (
        MAGNITUDE_COMPARABLE,
        ["explicit_usd_unit_calibration", "reward_arithmetic_verified"],
        _magnitude_payload(
            {pointer: result},
            {pointer: unit},
            {pointer: calibration_source},
        ),
        "S08",
    )


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


def validate_ontology_document(document):
    """Validate the invariants that prevent unsafe canonical magnitudes."""
    if not isinstance(document, dict):
        raise RewardOntologyError("ontology document must be an object")
    if document.get("ontology_version") != ONTOLOGY_VERSION:
        raise RewardOntologyError("unknown reward ontology version")
    kind = document.get("document_type")
    if kind == POLICY_DOCUMENT_TYPE:
        return validate_conversion_policy(document)
    if kind == "reward_training_annotation":
        comparability = document.get("comparability")
        if comparability not in COMPARABILITY_CLASSES:
            raise RewardOntologyError("invalid comparability class")
        reasons = document.get("reason_codes")
        if not isinstance(reasons, list) or not reasons or len(reasons) != len(set(reasons)):
            raise RewardOntologyError("reason_codes must be nonempty and unique")
        _require_catalogued_reasons(reasons)
        if not SHA256_RE.fullmatch(str(document.get("source_sidecar_id", ""))):
            raise RewardOntologyError("invalid source_sidecar_id")
        source_reward_count = document.get("source_reward_count")
        if (
            isinstance(source_reward_count, bool)
            or not isinstance(source_reward_count, int)
            or source_reward_count < 0
        ):
            raise RewardOntologyError("source_reward_count must be nonnegative")
        has_magnitude = "magnitude" in document
        has_order = "order" in document
        if comparability == MAGNITUDE_COMPARABLE:
            if not has_magnitude or has_order:
                raise RewardOntologyError("magnitude class requires magnitude only")
            magnitude = document["magnitude"]
            if (
                not isinstance(magnitude, dict)
                or magnitude.get("canonical_unit") != CANONICAL_UNIT
                or magnitude.get("aggregation") != MAGNITUDE_AGGREGATION
                or not isinstance(magnitude.get("values"), list)
                or not magnitude["values"]
            ):
                raise RewardOntologyError("invalid canonical magnitude payload")
            for value in magnitude["values"]:
                if not isinstance(value, dict):
                    raise RewardOntologyError("invalid canonical magnitude value")
                for field in (
                    "source_total",
                    "source_unit_usd",
                    "conversion_factor",
                    "canonical_value",
                ):
                    if _decimal(value.get(field)) is None:
                        raise RewardOntologyError(
                            f"canonical magnitude {field} must be finite"
                        )
                if (
                    _decimal(value["source_unit_usd"]) <= 0
                    or _decimal(value["conversion_factor"]) <= 0
                ):
                    raise RewardOntologyError("canonical magnitude scale must be positive")
                expected_factor = (
                    _decimal(value["source_unit_usd"]) / CANONICAL_UNIT_USD
                )
                if (
                    abs(_decimal(value["conversion_factor"]) - expected_factor)
                    > DEFAULT_TOLERANCE
                ):
                    raise RewardOntologyError("canonical conversion factor mismatch")
                expected_value = _decimal(value["source_total"]) * expected_factor
                if (
                    abs(_decimal(value["canonical_value"]) - expected_value)
                    > DEFAULT_TOLERANCE
                ):
                    raise RewardOntologyError("canonical converted value mismatch")
        elif has_magnitude:
            raise RewardOntologyError(
                "uncalibrated classes must not expose canonical magnitudes"
            )
        if comparability == SIGN_ORDER_ONLY:
            if not has_order:
                raise RewardOntologyError("sign/order class requires order evidence")
        elif has_order:
            raise RewardOntologyError("order evidence belongs only to sign/order class")
        return document

    if kind == "reward_source_sidecar":
        sidecar_id = document.get("sidecar_id")
        if not SHA256_RE.fullmatch(str(sidecar_id or "")):
            raise RewardOntologyError("invalid sidecar_id")
        sidecar_body = dict(document)
        sidecar_body.pop("sidecar_id", None)
        if _sha256(sidecar_body) != sidecar_id:
            raise RewardOntologyError("sidecar_id content hash mismatch")
        source = document.get("source")
        if not isinstance(source, dict) or not SHA256_RE.fullmatch(
            str(source.get("record_sha256", ""))
        ):
            raise RewardOntologyError("invalid sidecar source")
        rewards = document.get("source_rewards")
        if not isinstance(rewards, list):
            raise RewardOntologyError("source_rewards must be a list")
        for reward in rewards:
            if not isinstance(reward, dict) or not SHA256_RE.fullmatch(
                str(reward.get("value_sha256", ""))
            ):
                raise RewardOntologyError("invalid source reward entry")
        classification = document.get("classification")
        if (
            not isinstance(classification, dict)
            or classification.get("comparability") not in COMPARABILITY_CLASSES
            or not isinstance(classification.get("reason_codes"), list)
            or not classification["reason_codes"]
        ):
            raise RewardOntologyError("invalid sidecar classification")
        _require_catalogued_reasons(classification["reason_codes"])
        for entry in document.get("arithmetic", []):
            if not isinstance(entry, dict):
                raise RewardOntologyError("invalid sidecar arithmetic entry")
            if entry.get("status") not in ARITHMETIC_STATUSES:
                raise RewardOntologyError("invalid sidecar arithmetic status")
            if entry.get("method") not in ARITHMETIC_METHODS:
                raise RewardOntologyError(
                    f"uncatalogued arithmetic method: {entry.get('method')!r}"
                )
        return document
    raise RewardOntologyError(f"unknown ontology document_type: {kind!r}")


def curate_record(
    record,
    *,
    source_path="<memory>",
    source_line=1,
    calibration=None,
):
    """Return ``(annotated_record, reversible_sidecar)`` without mutating input."""
    if not isinstance(record, dict):
        raise RewardOntologyError("record must be an object")
    if isinstance(source_line, bool) or not isinstance(source_line, int) or source_line < 1:
        raise RewardOntologyError("source_line must be a positive integer")
    source_path = str(source_path).replace("\\", "/")
    if not source_path:
        raise RewardOntologyError("source_path must be nonempty")

    existing = record.get(ANNOTATION_FIELD)
    if existing is not None:
        validate_ontology_document(existing)

    source_record = copy.deepcopy(record)
    source_record.pop(ANNOTATION_FIELD, None)
    reward_items = sorted(_walk_rewards(source_record), key=lambda item: item[0])
    source_rewards = [
        {
            "json_pointer": pointer,
            "value_sha256": _sha256(value),
            "value": copy.deepcopy(value),
        }
        for pointer, value in reward_items
    ]
    arithmetic = [
        assess_arithmetic(value, pointer) for pointer, value in reward_items
    ]
    comparability, reason_codes, payload, rule_id = _classify(
        source_rewards,
        arithmetic,
        calibration,
    )
    _require_declared_rule(comparability, reason_codes, rule_id)

    sidecar_body = {
        "document_type": "reward_source_sidecar",
        "ontology_version": ONTOLOGY_VERSION,
        "source": {
            "path": source_path,
            "line": source_line,
            "record_sha256": _sha256(source_record),
        },
        "classification": {
            "comparability": comparability,
            "reason_codes": reason_codes,
        },
        "source_rewards": source_rewards,
        "arithmetic": arithmetic,
    }
    sidecar = {**sidecar_body, "sidecar_id": _sha256(sidecar_body)}

    annotation = {
        "document_type": "reward_training_annotation",
        "ontology_version": ONTOLOGY_VERSION,
        "comparability": comparability,
        "reason_codes": reason_codes,
        "source_sidecar_id": sidecar["sidecar_id"],
        "source_reward_count": len(source_rewards),
    }
    if comparability == MAGNITUDE_COMPARABLE:
        annotation["magnitude"] = payload
    elif comparability == SIGN_ORDER_ONLY:
        annotation["order"] = payload

    validate_ontology_document(sidecar)
    validate_ontology_document(annotation)
    curated = copy.deepcopy(source_record)
    curated[ANNOTATION_FIELD] = annotation
    return curated, sidecar


def restore_source_record(curated_record, sidecar):
    """Restore reward values and verify the exact source-record digest."""
    validate_ontology_document(sidecar)
    annotation = (
        curated_record.get(ANNOTATION_FIELD)
        if isinstance(curated_record, dict)
        else None
    )
    validate_ontology_document(annotation)
    if annotation["source_sidecar_id"] != sidecar["sidecar_id"]:
        raise RewardOntologyError("record annotation references a different sidecar")
    if annotation["source_reward_count"] != len(sidecar["source_rewards"]):
        raise RewardOntologyError("record annotation reward count mismatches sidecar")
    if (
        annotation["comparability"]
        != sidecar["classification"]["comparability"]
        or annotation["reason_codes"]
        != sidecar["classification"]["reason_codes"]
    ):
        raise RewardOntologyError("record annotation classification mismatches sidecar")
    restored = copy.deepcopy(curated_record)
    restored.pop(ANNOTATION_FIELD, None)
    for reward in sidecar["source_rewards"]:
        if _sha256(reward["value"]) != reward["value_sha256"]:
            raise RewardOntologyError("source reward sidecar value hash mismatch")
        _set_pointer(restored, reward["json_pointer"], reward["value"])
    if _sha256(restored) != sidecar["source"]["record_sha256"]:
        raise RewardOntologyError("restored source record hash mismatch")
    return restored


def canonical_magnitudes(record):
    """Return canonical values, refusing uncalibrated classes by construction."""
    annotation = record.get(ANNOTATION_FIELD) if isinstance(record, dict) else None
    validate_ontology_document(annotation)
    if annotation["comparability"] != MAGNITUDE_COMPARABLE:
        raise MagnitudeNotComparable(
            f"record is {annotation['comparability']}, not magnitude_comparable"
        )
    return {
        value["json_pointer"]: value["canonical_value"]
        for value in annotation["magnitude"]["values"]
    }


def _require_catalogued_reasons(reasons):
    unknown = sorted(set(reasons) - REASON_CODES)
    if unknown:
        raise RewardOntologyError(f"uncatalogued reason codes: {unknown}")


def comparability_rule(rule_id):
    """Return one declared comparability rule from the conversion policy."""
    for rule in COMPARABILITY_RULES:
        if rule["id"] == rule_id:
            return rule
    raise RewardOntologyError(f"undeclared comparability rule: {rule_id!r}")


def _require_declared_rule(comparability, reason_codes, rule_id):
    """Refuse any verdict the machine-readable rule table does not authorise."""
    rule = comparability_rule(rule_id)
    if rule["comparability"] != comparability:
        raise RewardOntologyError(
            f"rule {rule_id} declares {rule['comparability']}, not {comparability}"
        )
    required = list(rule["reason_codes"])
    optional = set(rule.get("optional_reason_codes", ()))
    emitted = list(reason_codes)
    if sorted(set(emitted) - optional) != sorted(required):
        raise RewardOntologyError(
            f"rule {rule_id} declares reason codes {sorted(required)}, "
            f"not {sorted(emitted)}"
        )
    if len(set(emitted)) != len(emitted):
        raise RewardOntologyError(f"rule {rule_id} emitted duplicate reason codes")
    _require_catalogued_reasons(emitted)
    return rule


def comparability_of(record):
    """Return the comparability class a curated record declares."""
    annotation = record.get(ANNOTATION_FIELD) if isinstance(record, dict) else None
    if annotation is None:
        raise RewardOntologyError(
            f"record declares no {ANNOTATION_FIELD} comparability class"
        )
    validate_ontology_document(annotation)
    return annotation["comparability"]


def magnitude_training_cohort(records):
    """Return canonical magnitudes for a cohort, or refuse to build one.

    This is the only supported way to assemble a magnitude-weighted training
    set. It refuses the whole cohort as soon as one member is not
    ``magnitude_comparable``, so an uncalibrated record cannot be mixed into a
    magnitude-weighted set by being averaged, concatenated, or silently
    dropped. Callers that want the comparable subset must partition the corpus
    explicitly and say so.
    """
    cohort = []
    for index, record in enumerate(records):
        try:
            comparability = comparability_of(record)
        except RewardOntologyError as exc:
            raise MagnitudeNotComparable(
                f"cohort member {index} declares no usable comparability class: {exc}"
            ) from exc
        if comparability != MAGNITUDE_COMPARABLE:
            raise MagnitudeNotComparable(
                f"cohort member {index} is {comparability}; a magnitude-weighted "
                "set may contain only magnitude_comparable records"
            )
        magnitude = record[ANNOTATION_FIELD]["magnitude"]
        cohort.append(
            {
                "index": index,
                "canonical_unit": magnitude["canonical_unit"],
                "aggregation": magnitude["aggregation"],
                "values": canonical_magnitudes(record),
            }
        )
    return cohort


def reward_census(records, *, scope_keys=None):
    """Return the reward vocabulary census for an iterable of source records.

    The census is what ``source_vocabulary`` in the mapping freezes for the
    2026-08-17 run. ``scope_keys`` defaults to the mapped run's census scope so
    the counts stay comparable with the training audit's reward vocabulary.
    """
    if scope_keys is None:
        scope_keys = SOURCE_VOCABULARY.get("scope_keys") or [CANONICAL_SCOPE[1:]]
    scope_keys = frozenset(scope_keys)
    unknown = sorted(scope_keys - REWARD_KEYS)
    if unknown:
        raise RewardOntologyError(f"census scope names non-reward keys: {unknown}")

    key_types = {}
    key_counts = Counter()
    shapes = Counter()
    shape_outcomes = {}
    arithmetic = Counter()
    total_records = 0
    instances = 0
    ontology_instances = 0
    for record in records:
        total_records += 1
        ontology_instances += sum(1 for _ in _walk_rewards(record))
        for pointer, reward in _walk_rewards(record, reward_keys=scope_keys):
            instances += 1
            signature = reward_signature(reward)
            shapes[signature] += 1
            result = assess_arithmetic(reward, pointer)
            outcome = (result["status"], result["method"])
            arithmetic[outcome] += 1
            shape_outcomes.setdefault(signature, set()).add(outcome)
            if not isinstance(reward, dict):
                continue
            for key, value in reward.items():
                key_types.setdefault(key, Counter())[value_type(value)] += 1
                key_counts[key] += 1

    component_keys = {}
    dispositions = Counter()
    for key in sorted(key_types):
        disposition = disposition_for_observed_types(key, key_types[key])
        dispositions[disposition] += 1
        component_keys[key] = {
            "disposition": disposition,
            "observed_types": sorted(key_types[key]),
            "occurrences": key_counts[key],
        }

    shape_rows = []
    for signature in sorted(shapes):
        outcomes = sorted(shape_outcomes[signature])
        row = {"signature": signature, "occurrences": shapes[signature]}
        if len(outcomes) == 1:
            row["arithmetic_status"], row["arithmetic_method"] = outcomes[0]
        else:
            row["arithmetic_outcomes"] = [
                {"status": status, "method": method} for status, method in outcomes
            ]
        shape_rows.append(row)

    return {
        "records": total_records,
        "scope_keys": sorted(scope_keys),
        "reward_instances": instances,
        "ontology_scope_keys": sorted(REWARD_KEYS),
        "ontology_scope_instances": ontology_instances,
        "unique_component_keys": len(component_keys),
        "unique_shapes": len(shape_rows),
        "dispositions": dict(sorted(dispositions.items())),
        "arithmetic": [
            {"status": status, "method": method, "occurrences": count}
            for (status, method), count in sorted(arithmetic.items())
        ],
        "component_keys": component_keys,
        "shapes": shape_rows,
    }


def load_units_migration(path):
    """Load only explicit, positive per-record conversions from an FFPC sidecar.

    Null factors and the documented coarse affine guess are deliberately
    ignored. Broad filename scopes without explicit record IDs are also
    ignored because the record itself already carries structured units there.
    """
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RewardOntologyError(f"{path}: invalid calibration JSON: {exc}") from exc
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise RewardOntologyError(f"{path}: calibration records must be a list")

    catalog = {}
    for index, entry in enumerate(records):
        if not isinstance(entry, dict):
            continue
        factor = _decimal(entry.get(MIGRATION_FACTOR_FIELD))
        if factor is None or factor <= 0:
            continue
        scope = entry.get(MIGRATION_SCOPE_FIELD)
        if not isinstance(scope, str):
            continue
        for record_id in sorted(set(RECORD_ID_RE.findall(scope))):
            calibration = {
                "source_unit_usd": _json_number(factor * CANONICAL_UNIT_USD),
                "canonical_factor": _json_number(factor),
                "evidence_ref": f"{path.as_posix()}#/records/{index}",
            }
            key = record_id.lower()
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise RewardOntologyError(
                    f"{path}: conflicting calibrations for {record_id}"
                )
            catalog[key] = calibration
    return catalog


def _record_calibration(record, catalog):
    if not catalog or not isinstance(record, dict):
        return None
    record_id = record.get("id")
    if not isinstance(record_id, str):
        meta = record.get("meta")
        record_id = meta.get("id") if isinstance(meta, dict) else None
    if not isinstance(record_id, str):
        return None
    return catalog.get(record_id.lower())


def _load_jsonl(path):
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RewardOntologyError(
                    f"{path}:{line_number}: invalid JSON: {exc}"
                ) from exc
            yield line_number, record


def classify_jsonl(input_path, *, source_path=None, calibration_catalog=None):
    source_path = source_path or str(input_path)
    counts = Counter()
    reasons = Counter()
    records = 0
    for line_number, record in _load_jsonl(input_path):
        curated, _sidecar = curate_record(
            record,
            source_path=source_path,
            source_line=line_number,
            calibration=_record_calibration(record, calibration_catalog),
        )
        annotation = curated[ANNOTATION_FIELD]
        counts[annotation["comparability"]] += 1
        reasons.update(annotation["reason_codes"])
        records += 1
    return {
        "input": str(input_path),
        "records": records,
        "comparability": dict(sorted(counts.items())),
        "reason_codes": dict(sorted(reasons.items())),
    }


def census_jsonl(input_paths, *, scope_keys=None):
    """Recompute the source-vocabulary census over one or more JSONL inputs."""

    def _records():
        for input_path in input_paths:
            for _line_number, record in _load_jsonl(input_path):
                yield record

    census = reward_census(_records(), scope_keys=scope_keys)
    return {"inputs": [str(path) for path in input_paths], **census}


def _write_new_text(path, text):
    """Create one new file exclusively; never replace an existing path."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RewardOntologyError(
            f"refusing to overwrite existing path: {path}"
        ) from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def convert_jsonl(
    input_path,
    output_path,
    sidecar_path,
    *,
    source_path=None,
    calibration_catalog=None,
):
    """Convert one JSONL file with no-clobber output and sidecar destinations."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    sidecar_path = Path(sidecar_path)
    if input_path.resolve() in {output_path.resolve(), sidecar_path.resolve()}:
        raise RewardOntologyError("input and output paths must be distinct")
    if output_path.resolve() == sidecar_path.resolve():
        raise RewardOntologyError("record and sidecar outputs must be distinct")
    for destination in (output_path, sidecar_path):
        if destination.exists():
            raise RewardOntologyError(f"refusing to overwrite existing path: {destination}")

    stable_source_path = source_path or str(input_path)
    output_lines = []
    sidecar_lines = []
    counts = Counter()
    for line_number, record in _load_jsonl(input_path):
        curated, sidecar = curate_record(
            record,
            source_path=stable_source_path,
            source_line=line_number,
            calibration=_record_calibration(record, calibration_catalog),
        )
        output_lines.append(json.dumps(curated, ensure_ascii=False, sort_keys=True))
        sidecar_lines.append(json.dumps(sidecar, ensure_ascii=False, sort_keys=True))
        counts[curated[ANNOTATION_FIELD]["comparability"]] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    _write_new_text(
        output_path,
        "\n".join(output_lines) + ("\n" if output_lines else ""),
    )
    try:
        _write_new_text(
            sidecar_path,
            "\n".join(sidecar_lines) + ("\n" if sidecar_lines else ""),
        )
    except BaseException:
        # Both required outputs or neither, so a retry is not blocked by a
        # curated file left without its reversible sidecar.
        output_path.unlink(missing_ok=True)
        raise
    return {
        "input": str(input_path),
        "output": str(output_path),
        "sidecars": str(sidecar_path),
        "records": len(output_lines),
        "comparability": dict(sorted(counts.items())),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify", help="read-only JSONL classification")
    classify.add_argument("input")
    classify.add_argument("--source-path")
    classify.add_argument("--units-migration")

    convert = subparsers.add_parser("convert", help="write annotated JSONL and sidecars")
    convert.add_argument("input")
    convert.add_argument("output")
    convert.add_argument("sidecars")
    convert.add_argument("--source-path")
    convert.add_argument("--units-migration")

    census = subparsers.add_parser(
        "census", help="read-only reward vocabulary census over JSONL inputs"
    )
    census.add_argument("inputs", nargs="+")
    census.add_argument(
        "--scope-key",
        action="append",
        dest="scope_keys",
        help="reward key to census (repeatable); defaults to the mapped scope",
    )
    census.add_argument(
        "--tables",
        action="store_true",
        help="include the full per-key and per-shape tables in the output",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        migration = getattr(args, "units_migration", None)
        calibration_catalog = load_units_migration(migration) if migration else None
        if args.command == "census":
            summary = census_jsonl(args.inputs, scope_keys=args.scope_keys)
            if not args.tables:
                summary.pop("component_keys", None)
                summary.pop("shapes", None)
        elif args.command == "classify":
            summary = classify_jsonl(
                args.input,
                source_path=args.source_path,
                calibration_catalog=calibration_catalog,
            )
        else:
            summary = convert_jsonl(
                args.input,
                args.output,
                args.sidecars,
                source_path=args.source_path,
                calibration_catalog=calibration_catalog,
            )
    except (OSError, RewardOntologyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
