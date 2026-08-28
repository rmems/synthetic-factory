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
    python3 pipelines/curate_rewards.py convert input.jsonl output.jsonl sidecars.jsonl \
        --manifest manifest.json
    python3 pipelines/curate_rewards.py run source-run new-reward-lane
    python3 pipelines/curate_rewards.py census input.jsonl --tables

The conversion policy itself is not hard-coded here. Scopes, arithmetic
methods, unit-calibration evidence, comparability classes, reason codes, and
the ordered classification rules are all read from the machine-readable mapping
at ``schemas/reward-ontology-v1.mapping.json``, which also freezes the
2026-08-17 run's 510 reward component keys and 140 structural shapes. The
read-only census subcommand recomputes that vocabulary from any JSONL corpus.

The run mode preserves every source JSONL's relative path and writes one
``reward-sidecars.jsonl`` artifact plus one aggregate ``manifest.json`` at the
new lane root.  When ``--units-migration`` is supplied, its exact bytes are
copied into the lane as ``units-migration.json`` and every applied calibration
is sealed onto the matching sidecar.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import shutil
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

VALUE_TYPES = frozenset(
    {
        "number",
        "value-object",
        "object",
        "array",
        "string",
        "boolean",
        "null",
        "unknown",
    }
)

ARITHMETIC_STATUSES = frozenset({"valid", "invalid", "unsupported"})
RULE_SCOPES = frozenset({"any", "preference", "single"})
REQUIRED_CLASSIFICATION_RULE_IDS = frozenset(
    {"R00"}
    | {f"P{index:02d}" for index in range(1, 9)}
    | {f"S{index:02d}" for index in range(1, 9)}
)
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
RUN_MANIFEST_FILENAME = "manifest.json"
RUN_SIDECAR_FILENAME = "reward-sidecars.jsonl"
RUN_CALIBRATION_FILENAME = "units-migration.json"


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


def _mapping_integer(container, key, where, *, minimum=0):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "nonnegative" if minimum == 0 else f">= {minimum}"
        raise _policy_error(where, f"{key} must be an integer {qualifier}")
    return value


def _mapping_pattern(container, key, where, *, groups=0, numeric_group=False):
    pattern = _mapping_str(container, key, where)
    try:
        compiled = re.compile(pattern, re.I)
    except re.error as exc:
        raise _policy_error(where, f"{key} is not a valid regular expression: {exc}") from exc
    if compiled.groups != groups:
        raise _policy_error(where, f"{key} must declare exactly {groups} capture group(s)")
    if numeric_group:
        haystack = "rounded to 3-decimal 1 reward unit = USD 10,000.5 abc"
        match = compiled.search(haystack)
        if match is not None:
            try:
                Decimal(str(match.group(1)).replace(",", ""))
            except (InvalidOperation, TypeError, IndexError, ArithmeticError) as exc:
                raise _policy_error(
                    where, f"{key} capture group must be numeric"
                ) from exc
    return compiled


def _numeric_capture(match, *, integer=False):
    try:
        token = str(match.group(1)).replace(",", "")
        value = int(token) if integer else Decimal(token)
    except (InvalidOperation, TypeError, ValueError, IndexError, ArithmeticError) as exc:
        raise RewardOntologyError("numeric regex capture is not a number") from exc
    return value


def _validate_conversion_block(policy, where):
    conversion = _mapping_object(policy, "conversion", where)
    canonical_unit = _mapping_str(conversion, "canonical_unit", where)
    if canonical_unit != "usd_10000_risk_adjusted_delta":
        raise _policy_error(
            where, "canonical_unit must match the annotation schema constant"
        )
    _mapping_positive(conversion, "canonical_unit_usd", where)
    aggregation = _mapping_str(conversion, "aggregation", where)
    if aggregation != "linear_unit_conversion_only":
        raise _policy_error(
            where, "aggregation must match the annotation schema constant"
        )
    _mapping_str(conversion, "required_semantics_substring", where)
    structured = _mapping_str(conversion, "structured_unit_field", where)
    textual = _mapping_str(conversion, "text_unit_field", where)
    if structured == textual:
        raise _policy_error(where, "structured and textual unit fields must be distinct")
    _mapping_pattern(
        conversion, "usd_unit_pattern", where, groups=1, numeric_group=True
    )
    external = _mapping_object(conversion, "external_calibration", where)
    _mapping_pattern(external, "record_id_pattern", where, groups=0)
    factor_field = _mapping_str(external, "factor_field", where)
    scope_field = _mapping_str(external, "scope_field", where)
    if factor_field == scope_field:
        raise _policy_error(where, "external calibration fields must be distinct")
    return conversion


def _validate_arithmetic_block(policy, where):
    arithmetic = _mapping_object(policy, "arithmetic", where)
    _mapping_positive(arithmetic, "default_tolerance", where)
    _mapping_str(arithmetic, "declared_total_field", where)
    _mapping_str(arithmetic, "weights_field", where)
    _mapping_str(arithmetic, "rounding_decimals_field", where)
    _mapping_pattern(
        arithmetic,
        "rounding_declaration_pattern",
        where,
        groups=1,
        numeric_group=True,
    )
    _mapping_str_list(arithmetic, "rounding_declaration_fields", where)
    containers = _mapping_str_list(arithmetic, "weighted_containers", where)
    nested = _mapping_str(arithmetic, "nested_component_key", where)
    if nested not in containers:
        raise _policy_error(where, "nested_component_key must be a declared weighted container")
    aliases = _mapping_object(arithmetic, "weight_aliases", where)
    seen_aliases = set()
    for name in sorted(aliases):
        members = _mapping_str_list(aliases, name, where)
        if name not in members:
            raise _policy_error(where, f"weight_aliases[{name!r}] must contain its own key")
        overlap = seen_aliases.intersection(members)
        if overlap:
            raise _policy_error(where, "weight alias groups must be disjoint")
        seen_aliases.update(members)
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
    missing_runtime_rules = sorted(REQUIRED_CLASSIFICATION_RULE_IDS - seen_ids)
    if missing_runtime_rules:
        raise _policy_error(
            where,
            "comparability_rules is missing runtime-required ids "
            f"{missing_runtime_rules}",
        )
    orphans = sorted(set(reason_codes) - covered)
    if orphans:
        raise _policy_error(where, f"reason codes cited by no rule: {orphans}")
    return tuple(rules)


def _arithmetic_methods_for_signature(signature, arithmetic, where):
    """Return the arithmetic methods the structural signature can select."""
    if signature == "":
        return frozenset({"no_numeric_total"})
    if ":" not in signature:
        return frozenset({"non_object_reward"})

    members = {}
    for part in signature.split("|"):
        if ":" not in part:
            raise _policy_error(where, "signature contains an invalid member")
        key, value_type = part.rsplit(":", 1)
        if not value_type or key in members:
            raise _policy_error(where, "signature contains an invalid member")
        members[key] = value_type

    total_type = members.get(arithmetic["declared_total_field"])
    if total_type not in {"int", "float"}:
        return frozenset({"no_numeric_total"})
    if members.get(arithmetic["weights_field"]) == "object":
        return frozenset(
            {"declared_weighted_sum", "declared_weighted_sum_unresolved"}
        )
    return frozenset(
        {"unweighted_component_sum", "unweighted_component_sum_unresolved"}
    )


def _policy_disposition(key, observed_types, arithmetic):
    groups = arithmetic["non_component_keys"]
    if key == arithmetic["declared_total_field"]:
        return DISPOSITION_DECLARED_TOTAL
    if key in groups[DISPOSITION_UNIT_CALIBRATION]:
        return DISPOSITION_UNIT_CALIBRATION
    if key in groups[DISPOSITION_NARRATIVE]:
        return DISPOSITION_NARRATIVE
    types = set(observed_types)
    if types <= {"number", "value-object"}:
        return DISPOSITION_MAGNITUDE_TERM
    if types == {"string"}:
        return DISPOSITION_NARRATIVE
    if types == {"object"}:
        return (
            DISPOSITION_CONTAINER
            if key in arithmetic["weighted_containers"]
            else DISPOSITION_STRUCTURAL
        )
    if types <= {"object", "array"}:
        return DISPOSITION_STRUCTURAL
    return DISPOSITION_AMBIGUOUS


def _validate_source_vocabulary(document, arithmetic, where):
    vocabulary = _mapping_object(document, "source_vocabulary", where)
    vocabulary_where = f"{where}.source_vocabulary"
    _mapping_str(vocabulary, "run", vocabulary_where)

    component_keys = _mapping_object(
        vocabulary, "component_keys", vocabulary_where
    )
    unique_component_keys = _mapping_integer(
        vocabulary, "unique_component_keys", vocabulary_where, minimum=1
    )
    if unique_component_keys != len(component_keys):
        raise _policy_error(
            vocabulary_where,
            "unique_component_keys must equal the number of component_keys",
        )

    disposition_counts = Counter()
    for key, entry in component_keys.items():
        entry_where = f"{vocabulary_where}.component_keys[{key!r}]"
        if not isinstance(key, str) or not key:
            raise _policy_error(vocabulary_where, "component key names must be nonempty")
        if not isinstance(entry, dict) or not entry:
            raise _policy_error(entry_where, "entry must be a nonempty object")
        disposition = _mapping_str(entry, "disposition", entry_where)
        if disposition not in COMPONENT_DISPOSITIONS:
            raise _policy_error(
                entry_where, f"unknown component disposition {disposition!r}"
            )
        observed_types = _mapping_str_list(entry, "observed_types", entry_where)
        unknown_types = sorted(set(observed_types) - VALUE_TYPES)
        if unknown_types:
            raise _policy_error(
                entry_where, f"unknown observed value types {unknown_types}"
            )
        expected = _policy_disposition(key, observed_types, arithmetic)
        if disposition != expected:
            raise _policy_error(
                entry_where,
                f"disposition must be {expected!r} for {list(observed_types)!r}",
            )
        _mapping_integer(entry, "occurrences", entry_where, minimum=1)
        disposition_counts[disposition] += 1

    declared_dispositions = _mapping_object(
        vocabulary, "dispositions", vocabulary_where
    )
    if set(declared_dispositions) != set(COMPONENT_DISPOSITIONS):
        raise _policy_error(
            vocabulary_where,
            "dispositions must count exactly the declared component dispositions",
        )
    for disposition in COMPONENT_DISPOSITIONS:
        declared = _mapping_integer(
            declared_dispositions, disposition, vocabulary_where
        )
        if declared != disposition_counts[disposition]:
            raise _policy_error(
                vocabulary_where,
                f"dispositions[{disposition!r}] does not match component_keys",
            )

    shapes = vocabulary.get("shapes")
    if not isinstance(shapes, list) or not shapes:
        raise _policy_error(vocabulary_where, "shapes must be a nonempty list")
    unique_shapes = _mapping_integer(
        vocabulary, "unique_shapes", vocabulary_where, minimum=1
    )
    if unique_shapes != len(shapes):
        raise _policy_error(
            vocabulary_where, "unique_shapes must equal the number of shapes"
        )
    signatures = set()
    occurrence_total = 0
    for index, shape in enumerate(shapes):
        shape_where = f"{vocabulary_where}.shapes[{index}]"
        if not isinstance(shape, dict):
            raise _policy_error(shape_where, "shape must be an object")
        signature = shape.get("signature")
        if not isinstance(signature, str):
            raise _policy_error(shape_where, "signature must be a string")
        if signature in signatures:
            raise _policy_error(shape_where, f"duplicate shape signature {signature!r}")
        signatures.add(signature)
        allowed_methods = _arithmetic_methods_for_signature(
            signature, arithmetic, shape_where
        )
        occurrence_total += _mapping_integer(
            shape, "occurrences", shape_where, minimum=1
        )
        has_singular = (
            "arithmetic_status" in shape or "arithmetic_method" in shape
        )
        has_plural = "arithmetic_outcomes" in shape
        if has_singular == has_plural:
            raise _policy_error(
                shape_where,
                "shape must declare exactly one of singular arithmetic fields "
                "or arithmetic_outcomes",
            )
        outcomes = [shape] if has_singular else shape["arithmetic_outcomes"]
        if not isinstance(outcomes, list) or not outcomes:
            raise _policy_error(
                shape_where, "arithmetic_outcomes must be a nonempty list"
            )
        seen_outcomes = set()
        for outcome_index, outcome in enumerate(outcomes):
            outcome_where = (
                shape_where
                if has_singular
                else f"{shape_where}.arithmetic_outcomes[{outcome_index}]"
            )
            if not isinstance(outcome, dict):
                raise _policy_error(outcome_where, "outcome must be an object")
            status_key = "arithmetic_status" if has_singular else "status"
            method_key = "arithmetic_method" if has_singular else "method"
            status = _mapping_str(outcome, status_key, outcome_where)
            if status not in ARITHMETIC_STATUSES:
                raise _policy_error(
                    outcome_where, f"unknown arithmetic status {status!r}"
                )
            method = _mapping_str(outcome, method_key, outcome_where)
            if method not in arithmetic["methods"]:
                raise _policy_error(
                    outcome_where, f"unknown arithmetic method {method!r}"
                )
            if method not in allowed_methods:
                raise _policy_error(
                    outcome_where,
                    f"arithmetic method {method!r} is incompatible with signature",
                )
            allowed_status = {
                "valid": {
                    "declared_weighted_sum",
                    "unweighted_component_sum",
                },
                "invalid": {
                    "declared_weighted_sum",
                    "unweighted_component_sum",
                },
                "unsupported": {
                    "declared_weighted_sum_unresolved",
                    "unweighted_component_sum_unresolved",
                    "no_numeric_total",
                    "non_object_reward",
                },
            }
            if method not in allowed_status.get(status, ()):
                raise _policy_error(
                    outcome_where,
                    f"arithmetic status {status!r} is incompatible with method {method!r}",
                )
            pair = (status, method)
            if pair in seen_outcomes:
                raise _policy_error(outcome_where, "duplicate arithmetic outcome")
            seen_outcomes.add(pair)
    reward_instances = _mapping_integer(
        vocabulary, "reward_instances", vocabulary_where, minimum=1
    )
    if occurrence_total != reward_instances:
        raise _policy_error(
            vocabulary_where,
            "shape occurrences must sum to reward_instances",
        )
    return vocabulary


def _validate_expected_classification(document, classes, reason_codes, run, where):
    expected = _mapping_object(document, "expected_classification", where)
    expected_where = f"{where}.expected_classification"
    if _mapping_str(expected, "run", expected_where) != run:
        raise _policy_error(
            expected_where, "run must match source_vocabulary.run"
        )
    records = _mapping_integer(expected, "records", expected_where)
    comparability = _mapping_object(expected, "comparability", expected_where)
    if set(comparability) != set(classes):
        raise _policy_error(
            expected_where,
            "comparability must count exactly the declared comparability classes",
        )
    classified = sum(
        _mapping_integer(comparability, name, expected_where) for name in classes
    )
    if classified != records:
        raise _policy_error(
            expected_where, "comparability counts must sum to records"
        )
    expected_reasons = _mapping_object(expected, "reason_codes", expected_where)
    unknown_reasons = sorted(set(expected_reasons) - set(reason_codes))
    if unknown_reasons:
        raise _policy_error(
            expected_where, f"uncatalogued reason-code counts {unknown_reasons}"
        )
    for reason in expected_reasons:
        _mapping_integer(expected_reasons, reason, expected_where)
    by_factory = _mapping_object(expected, "by_factory", expected_where)
    factory_records = 0
    factory_comparability = Counter()
    factory_reasons = Counter()
    for factory, entry in by_factory.items():
        factory_where = f"{expected_where}.by_factory[{factory!r}]"
        if not isinstance(factory, str) or not factory:
            raise _policy_error(expected_where, "factory names must be nonempty strings")
        if not isinstance(entry, dict) or not entry:
            raise _policy_error(factory_where, "entry must be a nonempty object")
        entry_records = _mapping_integer(entry, "records", factory_where)
        entry_comparability = _mapping_object(
            entry, "comparability", factory_where
        )
        unknown_classes = sorted(set(entry_comparability) - set(classes))
        if unknown_classes:
            raise _policy_error(
                factory_where,
                f"unknown comparability classes {unknown_classes}",
            )
        entry_classified = 0
        for name in entry_comparability:
            count = _mapping_integer(
                entry_comparability, name, factory_where
            )
            entry_classified += count
            factory_comparability[name] += count
        if entry_classified != entry_records:
            raise _policy_error(
                factory_where, "comparability counts must sum to records"
            )
        entry_reasons = _mapping_object(entry, "reason_codes", factory_where)
        unknown_factory_reasons = sorted(
            set(entry_reasons) - set(reason_codes)
        )
        if unknown_factory_reasons:
            raise _policy_error(
                factory_where,
                f"uncatalogued reason-code counts {unknown_factory_reasons}",
            )
        for reason in entry_reasons:
            factory_reasons[reason] += _mapping_integer(
                entry_reasons, reason, factory_where
            )
        factory_records += entry_records
    if factory_records != records:
        raise _policy_error(
            expected_where, "by_factory records must sum to records"
        )
    for name in classes:
        if factory_comparability[name] != comparability[name]:
            raise _policy_error(
                expected_where,
                "by_factory comparability counts must match the global census",
            )
    if dict(sorted(factory_reasons.items())) != dict(sorted(expected_reasons.items())):
        raise _policy_error(
            expected_where,
            "by_factory reason-code counts must match the global census",
        )
    return expected


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
    annotation_field = _mapping_str(policy, "annotation_field", where)
    reward_keys = _mapping_str_list(policy, "reward_keys", where)
    if annotation_field in reward_keys:
        raise _policy_error(where, "annotation_field must not be a declared reward key")
    canonical_scope = _mapping_str(policy, "canonical_scope", where, prefix="/")
    if canonical_scope[1:] not in reward_keys:
        raise _policy_error(where, "canonical_scope must name a declared reward key")
    preference = _mapping_object(policy, "preference_scope", where)
    preferred = _mapping_str(preference, "preferred", where, prefix="/")
    dispreferred = _mapping_str(preference, "dispreferred", where, prefix="/")
    if preferred == dispreferred:
        raise _policy_error(where, "preference pointers must be distinct")
    for pointer, label in ((preferred, "preferred"), (dispreferred, "dispreferred")):
        terminal = pointer.rsplit("/", 1)[-1]
        if terminal not in reward_keys:
            raise _policy_error(
                where, f"{label} pointer must target a declared reward key"
            )
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
    vocabulary = _validate_source_vocabulary(document, arithmetic, where)
    _validate_expected_classification(
        document, classes, reason_codes, vocabulary["run"], where
    )
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
SOURCE_VOCABULARY = CONVERSION_POLICY["source_vocabulary"]


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
                decimals = _numeric_capture(match, integer=True)
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


normalize_calibration = _normalize_calibration


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
            parsed = _numeric_capture(match)

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
        return _mapped_verdict("R00")

    if is_preference:
        if set(rewards_by_pointer) != set(PREFERENCE_POINTERS):
            return _mapped_verdict("P01")
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
        if chosen_total <= rejected_total:
            return _mapped_verdict("P04")

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
            optional_reasons = (
                ["external_calibration_evidence"]
                if "external_calibration_evidence" in unit_statuses
                else []
            )
            return _mapped_verdict(
                "P05",
                _magnitude_payload(
                    arithmetic_by_pointer,
                    units,
                    calibration_sources,
                ),
                optional_reason_codes=optional_reasons,
            )

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
    optional_reasons = (
        ["external_calibration_evidence"]
        if unit_status == "external_calibration_evidence"
        else []
    )
    return _mapped_verdict(
        "S08",
        _magnitude_payload(
            {pointer: result},
            {pointer: unit},
            {pointer: calibration_source},
        ),
        optional_reason_codes=optional_reasons,
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
        _require_declared_verdict(comparability, reasons)
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
        reason_codes = (
            classification.get("reason_codes")
            if isinstance(classification, dict)
            else None
        )
        if (
            not isinstance(classification, dict)
            or classification.get("comparability") not in COMPARABILITY_CLASSES
            or not isinstance(reason_codes, list)
            or not reason_codes
            or not all(isinstance(code, str) for code in reason_codes)
            or len(reason_codes) != len(set(reason_codes))
        ):
            raise RewardOntologyError("invalid sidecar classification")
        _require_catalogued_reasons(reason_codes)
        _require_declared_verdict(
            classification["comparability"], reason_codes
        )
        arithmetic_entries = document.get("arithmetic", [])
        if not isinstance(arithmetic_entries, list):
            raise RewardOntologyError("sidecar arithmetic must be a list")
        for entry in arithmetic_entries:
            if not isinstance(entry, dict):
                raise RewardOntologyError("invalid sidecar arithmetic entry")
            if entry.get("status") not in ARITHMETIC_STATUSES:
                raise RewardOntologyError("invalid sidecar arithmetic status")
            if entry.get("method") not in ARITHMETIC_METHODS:
                raise RewardOntologyError(
                    f"uncatalogued arithmetic method: {entry.get('method')!r}"
                )
        calibration = document.get("calibration")
        if calibration is not None:
            normalized = _normalize_calibration(calibration)
            if (
                normalized["source_unit_usd"] != _decimal(calibration.get("source_unit_usd"))
                or normalized["evidence_ref"] != calibration.get("evidence_ref")
            ):
                raise RewardOntologyError("sidecar calibration is not canonical")
            if "external_calibration_evidence" not in classification["reason_codes"]:
                raise RewardOntologyError(
                    "sidecar calibration requires external_calibration_evidence"
                )
        elif "external_calibration_evidence" in classification["reason_codes"]:
            raise RewardOntologyError(
                "external_calibration_evidence requires an applied sidecar calibration"
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
    normalized_calibration = _normalize_calibration(calibration)
    comparability, reason_codes, payload, rule_id = _classify(
        source_rewards,
        arithmetic,
        normalized_calibration,
    )
    _require_declared_rule(comparability, reason_codes, rule_id)

    source_identity = {
        "path": source_path,
        "line": source_line,
        "record_sha256": _sha256(source_record),
    }
    source_record_id = _canonical_record_id(source_record)
    if source_record_id is not None:
        source_identity["record_id"] = source_record_id
    sidecar_body = {
        "document_type": "reward_source_sidecar",
        "ontology_version": ONTOLOGY_VERSION,
        "source": source_identity,
        "classification": {
            "comparability": comparability,
            "reason_codes": reason_codes,
        },
        "source_rewards": source_rewards,
        "arithmetic": arithmetic,
    }
    if normalized_calibration is not None and (
        "external_calibration_evidence" in reason_codes
    ):
        sidecar_body["calibration"] = {
            "source_unit_usd": _json_number(normalized_calibration["source_unit_usd"]),
            "evidence_ref": normalized_calibration["evidence_ref"],
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
    values = annotation["magnitude"]["values"]
    if not isinstance(values, list):
        raise RewardOntologyError("magnitude values must be a list")
    pointers = [value.get("json_pointer") for value in values]
    if len(pointers) != len(set(pointers)):
        raise RewardOntologyError("duplicate magnitude json_pointer")
    if len(pointers) != annotation["source_reward_count"]:
        raise RewardOntologyError(
            "magnitude values must match source_reward_count"
        )
    return {
        value["json_pointer"]: value["canonical_value"]
        for value in values
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


def _rule_accepts_verdict(rule, comparability, reason_codes):
    if rule["comparability"] != comparability:
        return False
    emitted = set(reason_codes)
    if len(emitted) != len(reason_codes):
        return False
    required = set(rule["reason_codes"])
    optional = set(rule.get("optional_reason_codes", ()))
    return required <= emitted <= required | optional


def _require_declared_verdict(comparability, reason_codes):
    """Require a stored class/reason pair to match at least one policy rule."""
    _require_catalogued_reasons(reason_codes)
    matches = [
        rule["id"]
        for rule in COMPARABILITY_RULES
        if _rule_accepts_verdict(rule, comparability, reason_codes)
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
    dispositions = Counter({name: 0 for name in COMPONENT_DISPOSITIONS})
    for record in records:
        if not isinstance(record, dict):
            raise RewardOntologyError("census records must be objects")
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
        "dispositions": {name: dispositions[name] for name in COMPONENT_DISPOSITIONS},
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
            key = catalog_record_key(record_id)
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise RewardOntologyError(
                    f"{path}: conflicting calibrations for {record_id}"
                )
            catalog[key] = calibration
    return catalog


def load_units_migration_bytes(payload, *, label="<memory>"):
    """Parse exact migration bytes into the same catalog ``load_units_migration`` builds."""
    if not isinstance(payload, bytes):
        raise RewardOntologyError("calibration payload must be bytes")
    try:
        document = json.loads(payload.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RewardOntologyError(f"{label}: invalid calibration JSON: {exc}") from exc
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise RewardOntologyError(f"{label}: calibration records must be a list")
    catalog = {}
    for index, entry in enumerate(records):
        if not isinstance(entry, dict):
            continue
        factor = _decimal(entry.get("usd_conversion_factor"))
        if factor is None or factor <= 0:
            continue
        scope = entry.get("scope")
        if not isinstance(scope, str):
            continue
        for record_id in sorted(set(RECORD_ID_RE.findall(scope))):
            calibration = {
                "source_unit_usd": _json_number(factor * CANONICAL_UNIT_USD),
                "canonical_factor": _json_number(factor),
                "evidence_ref": f"{label}#/records/{index}",
            }
            key = catalog_record_key(record_id)
            previous = catalog.get(key)
            if previous is not None and previous != calibration:
                raise RewardOntologyError(
                    f"{label}: conflicting calibrations for {record_id}"
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
    return catalog.get(catalog_record_key(record_id))


def _load_jsonl(path):
    for line_number, _raw_line, record in _load_jsonl_with_source_bytes(path):
        yield line_number, record


def _reject_json_constant(value):
    raise ValueError(f"non-standard JSON numeric constant {value}")


def _load_jsonl_with_source_bytes(path):
    path = Path(path)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise RewardOntologyError(f"cannot read {path}: {exc}") from exc
    for line_number, terminated in enumerate(payload.split(b"\n"), 1):
        raw_line = terminated[:-1] if terminated.endswith(b"\r") else terminated
        if not raw_line.strip():
            continue
        try:
            line = raw_line.decode("utf-8")
            record = json.loads(line, parse_constant=_reject_json_constant)
        except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise RewardOntologyError(
                f"{path}:{line_number}: invalid JSON: {exc}"
            ) from exc
        yield line_number, raw_line, record


def catalog_record_key(record_id):
    """Catalog insertion and lookup use str.lower, not casefold."""
    return record_id.lower()


def _canonical_record_id(record):
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    value = meta.get("id") if isinstance(meta, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


canonical_source_record_id = _canonical_record_id


def _converted_jsonl_rows(
    input_path,
    *,
    source_path,
    calibration_catalog=None,
):
    """Yield deterministic output, sidecar, and manifest rows for one JSONL."""
    stable_source_path = str(source_path).replace("\\", "/")
    for line_number, raw_line, record in _load_jsonl_with_source_bytes(input_path):
        curated, sidecar = curate_record(
            record,
            source_path=stable_source_path,
            source_line=line_number,
            calibration=_record_calibration(record, calibration_catalog),
        )
        annotation = curated[ANNOTATION_FIELD]
        manifest_entry = {
            "source_path": stable_source_path,
            "source_line": line_number,
            "source_hash": hashlib.sha256(raw_line).hexdigest(),
            "transform_name": "reward_ontology",
            "transform_version": ONTOLOGY_VERSION,
            "action": "retained",
            "reason_codes": list(annotation["reason_codes"]),
            "classification": annotation["comparability"],
            "output_id": _canonical_record_id(curated),
            "output_hash": hashlib.sha256(_canonical_bytes(curated)).hexdigest(),
        }
        yield (
            json.dumps(curated, ensure_ascii=False, sort_keys=True),
            json.dumps(sidecar, ensure_ascii=False, sort_keys=True),
            manifest_entry,
            annotation["comparability"],
        )


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


def _write_new_bytes(path, payload):
    """Create one new file exclusively; never replace an existing path."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RewardOntologyError(
            f"refusing to overwrite existing path: {path}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_new_text(path, text):
    """Create one new file exclusively; never replace an existing path."""
    _write_new_bytes(path, text.encode("utf-8"))


def convert_jsonl(
    input_path,
    output_path,
    sidecar_path,
    *,
    source_path=None,
    calibration_catalog=None,
    manifest_path=None,
):
    """Convert JSONL and optionally emit a gate-compatible record manifest."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    sidecar_path = Path(sidecar_path)
    manifest_path = Path(manifest_path) if manifest_path is not None else None
    destinations = [output_path, sidecar_path]
    if manifest_path is not None:
        destinations.append(manifest_path)
    resolved_destinations = {destination.resolve() for destination in destinations}
    if input_path.resolve() in resolved_destinations:
        raise RewardOntologyError("input and output paths must be distinct")
    if len(resolved_destinations) != len(destinations):
        raise RewardOntologyError("record, sidecar, and manifest outputs must be distinct")
    for destination in destinations:
        if destination.exists():
            raise RewardOntologyError(f"refusing to overwrite existing path: {destination}")

    stable_source_path = source_path or str(input_path)
    output_lines = []
    sidecar_lines = []
    manifest_entries = []
    counts = Counter()
    for output_line, sidecar_line, manifest_entry, comparability in _converted_jsonl_rows(
        input_path,
        source_path=stable_source_path,
        calibration_catalog=calibration_catalog,
    ):
        output_lines.append(output_line)
        sidecar_lines.append(sidecar_line)
        manifest_entries.append(manifest_entry)
        counts[comparability] += 1

    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
    written = []
    try:
        _write_new_text(
            output_path,
            "\n".join(output_lines) + ("\n" if output_lines else ""),
        )
        written.append(output_path)
        _write_new_text(
            sidecar_path,
            "\n".join(sidecar_lines) + ("\n" if sidecar_lines else ""),
        )
        written.append(sidecar_path)
        if manifest_path is not None:
            _write_new_text(
                manifest_path,
                json.dumps(manifest_entries, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            )
            written.append(manifest_path)
    except BaseException:
        # Every requested output or none, so a retry is never blocked by a
        # partial record/sidecar/manifest transaction.
        for destination in reversed(written):
            destination.unlink(missing_ok=True)
        raise
    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "sidecars": str(sidecar_path),
        "records": len(output_lines),
        "comparability": dict(sorted(counts.items())),
    }
    if manifest_path is not None:
        summary["manifest"] = str(manifest_path)
    return summary


def _absolute_path(path):
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path, label):
    """Reject an existing symlink anywhere in an absolute path."""
    absolute = _absolute_path(path)
    parts = absolute.parts
    walked = Path(parts[0])
    for part in parts[1:]:
        walked /= part
        if walked.is_symlink():
            raise RewardOntologyError(
                f"{label} contains a symlinked path component: {walked}"
            )
        if walked != absolute and os.path.lexists(walked) and not walked.is_dir():
            raise RewardOntologyError(
                f"{label} has a non-directory path component: {walked}"
            )
    return absolute


def _is_under_raw(path):
    parts = Path(path).resolve(strict=False).parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _run_source_paths(source_root):
    source_root = _reject_symlink_components(source_root, "source run")
    if not source_root.is_dir():
        raise RewardOntologyError(f"source run is not a directory: {source_root}")

    discovered = []
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise RewardOntologyError(f"source run contains a symlinked path: {path}")
        if path.is_file() and path.suffix == ".jsonl":
            discovered.append(path)
    paths = sorted(
        discovered,
        key=lambda jsonl_path: jsonl_path.relative_to(source_root).as_posix(),
    )
    if not paths:
        raise RewardOntologyError(f"source run holds no JSONL files: {source_root}")
    reserved = source_root / RUN_SIDECAR_FILENAME
    if reserved in paths:
        raise RewardOntologyError(
            f"source JSONL path conflicts with aggregate sidecar name: {RUN_SIDECAR_FILENAME}"
        )
    return source_root, paths


def _new_run_destination(destination, source_root):
    destination = _reject_symlink_components(destination, "run destination")
    if _is_under_raw(destination):
        raise RewardOntologyError(
            f"refusing to write run destination beneath immutable outputs/raw: {destination}"
        )
    if os.path.lexists(destination):
        raise RewardOntologyError(
            f"refusing to overwrite existing run destination: {destination}"
        )
    if destination == source_root or source_root in destination.parents:
        raise RewardOntologyError(
            f"run destination must be outside the source run: {destination}"
        )
    return destination


def convert_run(
    input_dir,
    output_dir,
    *,
    calibration_catalog=None,
    units_migration=None,
):
    """Convert a source run into one new, gate-ready reward lane tree.

    Source JSONLs are processed in stable relative-path order. Their relative
    output paths are preserved, while sidecars and manifest entries are
    aggregated at the lane root. Any failure removes the entire new tree.
    """
    source_root, source_paths = _run_source_paths(input_dir)
    output_root = _new_run_destination(output_dir, source_root)
    try:
        output_root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RewardOntologyError(
            f"refusing to overwrite existing run destination: {output_root}"
        ) from exc

    sidecar_lines = []
    manifest_entries = []
    counts = Counter()
    records = 0
    try:
        for input_path in source_paths:
            relative = input_path.relative_to(source_root)
            relative_source = relative.as_posix()
            output_lines = []
            for (
                output_line,
                sidecar_line,
                manifest_entry,
                comparability,
            ) in _converted_jsonl_rows(
                input_path,
                source_path=relative_source,
                calibration_catalog=calibration_catalog,
            ):
                output_lines.append(output_line)
                sidecar_lines.append(sidecar_line)
                manifest_entries.append(manifest_entry)
                counts[comparability] += 1
                records += 1
            output_path = output_root / relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            _write_new_text(
                output_path,
                "\n".join(output_lines) + ("\n" if output_lines else ""),
            )

        if not records:
            raise RewardOntologyError(f"source run holds no JSONL records: {source_root}")
        sidecar_path = output_root / RUN_SIDECAR_FILENAME
        manifest_path = output_root / RUN_MANIFEST_FILENAME
        _write_new_text(sidecar_path, "\n".join(sidecar_lines) + "\n")
        _write_new_text(
            manifest_path,
            json.dumps(manifest_entries, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
        )
        if units_migration is not None:
            migration_path = Path(units_migration)
            try:
                migration_payload = migration_path.read_bytes()
            except OSError as exc:
                raise RewardOntologyError(
                    f"cannot read calibration {migration_path}: {exc}"
                ) from exc
            _write_new_bytes(output_root / RUN_CALIBRATION_FILENAME, migration_payload)
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        raise

    return {
        "input": str(source_root),
        "output": str(output_root),
        "sidecars": str(output_root / RUN_SIDECAR_FILENAME),
        "manifest": str(output_root / RUN_MANIFEST_FILENAME),
        "files": len(source_paths),
        "records": records,
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
    convert.add_argument("--manifest")
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
    run = subparsers.add_parser(
        "run",
        aliases=["convert-run"],
        help="write a new gate-ready reward lane from a source run directory",
    )
    run.add_argument("input")
    run.add_argument("output")
    run.add_argument("--units-migration")
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
        elif args.command == "convert":
            summary = convert_jsonl(
                args.input,
                args.output,
                args.sidecars,
                source_path=args.source_path,
                calibration_catalog=calibration_catalog,
                manifest_path=args.manifest,
            )
        else:
            summary = convert_run(
                args.input,
                args.output,
                calibration_catalog=calibration_catalog,
                units_migration=args.units_migration,
            )
    except (OSError, RewardOntologyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
