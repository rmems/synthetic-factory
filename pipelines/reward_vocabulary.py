#!/usr/bin/env python3
"""Fail-closed validation of the frozen reward source vocabulary."""

from __future__ import annotations

from collections import Counter

from reward_mapping import (
    ARITHMETIC_STATUSES,
    COMPONENT_DISPOSITIONS,
    VALUE_TYPES,
    _SHAPE_STATUS_METHODS,
    _arithmetic_methods_for_signature,
    _mapping_integer,
    _mapping_object,
    _mapping_str,
    _mapping_str_list,
    _policy_disposition,
    _policy_error,
)


def _validate_vocabulary_counts(vocabulary, reward_keys, where):
    vocabulary_where = f"{where}.source_vocabulary"
    _mapping_str(vocabulary, "run", vocabulary_where)
    scope_keys = _mapping_str_list(vocabulary, "scope_keys", vocabulary_where)
    unknown_scopes = sorted(set(scope_keys) - set(reward_keys))
    if unknown_scopes:
        raise _policy_error(
            vocabulary_where, f"scope_keys names non-reward keys {unknown_scopes}"
        )
    reward_instances = _mapping_integer(
        vocabulary, "reward_instances", vocabulary_where, minimum=1
    )
    ontology_scope_instances = _mapping_integer(
        vocabulary, "ontology_scope_instances", vocabulary_where, minimum=1
    )
    if ontology_scope_instances < reward_instances:
        raise _policy_error(
            vocabulary_where,
            "ontology_scope_instances must be at least reward_instances",
        )
    return vocabulary_where, reward_instances


def _validate_one_component_key(key, entry, arithmetic, reward_instances, vocabulary_where):
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
    occurrences = _mapping_integer(entry, "occurrences", entry_where, minimum=1)
    if occurrences > reward_instances:
        raise _policy_error(
            entry_where,
            "occurrences must not exceed reward_instances",
        )
    return disposition


def _validate_component_keys(vocabulary, arithmetic, reward_instances, vocabulary_where):
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
        disposition = _validate_one_component_key(
            key, entry, arithmetic, reward_instances, vocabulary_where
        )
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
    return disposition_counts


def _shape_outcome_keys(has_singular):
    if has_singular:
        return "arithmetic_status", "arithmetic_method"
    return "status", "method"


def _validate_shape_outcome(
    outcome, has_singular, allowed_methods, arithmetic, seen_outcomes, where
):
    if not isinstance(outcome, dict):
        raise _policy_error(where, "outcome must be an object")
    status_key, method_key = _shape_outcome_keys(has_singular)
    status = _mapping_str(outcome, status_key, where)
    if status not in ARITHMETIC_STATUSES:
        raise _policy_error(where, f"unknown arithmetic status {status!r}")
    method = _mapping_str(outcome, method_key, where)
    if method not in arithmetic["methods"]:
        raise _policy_error(where, f"unknown arithmetic method {method!r}")
    if method not in allowed_methods:
        raise _policy_error(
            where,
            f"arithmetic method {method!r} is incompatible with signature",
        )
    if method not in _SHAPE_STATUS_METHODS.get(status, ()):
        raise _policy_error(
            where,
            f"arithmetic status {status!r} is incompatible with method {method!r}",
        )
    pair = (status, method)
    if pair in seen_outcomes:
        raise _policy_error(where, "duplicate arithmetic outcome")
    seen_outcomes.add(pair)


def _validate_one_shape(shape, index, arithmetic, signatures, vocabulary_where):
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
    occurrences = _mapping_integer(
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
        _validate_shape_outcome(
            outcome,
            has_singular,
            allowed_methods,
            arithmetic,
            seen_outcomes,
            outcome_where,
        )
    return occurrences


def _validate_vocabulary_shapes(vocabulary, arithmetic, reward_instances, vocabulary_where):
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
        occurrence_total += _validate_one_shape(
            shape, index, arithmetic, signatures, vocabulary_where
        )
    if occurrence_total != reward_instances:
        raise _policy_error(
            vocabulary_where,
            "shape occurrences must sum to reward_instances",
        )


def _validate_vocabulary_arithmetic(vocabulary, arithmetic, reward_instances, vocabulary_where):
    declared_arithmetic = vocabulary.get("arithmetic")
    if not isinstance(declared_arithmetic, list) or not declared_arithmetic:
        raise _policy_error(
            vocabulary_where, "arithmetic must be a nonempty list"
        )
    arithmetic_total = 0
    seen_arithmetic = set()
    for index, row in enumerate(declared_arithmetic):
        row_where = f"{vocabulary_where}.arithmetic[{index}]"
        if not isinstance(row, dict):
            raise _policy_error(row_where, "arithmetic census row must be an object")
        status = _mapping_str(row, "status", row_where)
        if status not in ARITHMETIC_STATUSES:
            raise _policy_error(row_where, f"unknown arithmetic status {status!r}")
        method = _mapping_str(row, "method", row_where)
        if method not in arithmetic["methods"]:
            raise _policy_error(row_where, f"unknown arithmetic method {method!r}")
        pair = (status, method)
        if pair in seen_arithmetic:
            raise _policy_error(row_where, "duplicate arithmetic census row")
        seen_arithmetic.add(pair)
        arithmetic_total += _mapping_integer(
            row, "occurrences", row_where, minimum=1
        )
    if arithmetic_total != reward_instances:
        raise _policy_error(
            vocabulary_where,
            "arithmetic occurrences must sum to reward_instances",
        )


def _validate_source_vocabulary(document, arithmetic, reward_keys, where):
    vocabulary = _mapping_object(document, "source_vocabulary", where)
    vocabulary_where, reward_instances = _validate_vocabulary_counts(
        vocabulary, reward_keys, where
    )
    _validate_component_keys(
        vocabulary, arithmetic, reward_instances, vocabulary_where
    )
    _validate_vocabulary_shapes(
        vocabulary, arithmetic, reward_instances, vocabulary_where
    )
    _validate_vocabulary_arithmetic(
        vocabulary, arithmetic, reward_instances, vocabulary_where
    )
    return vocabulary


def _validate_expected_totals(expected, expected_where, classes, reason_codes, run):
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
    return records, comparability, expected_reasons


def _validate_factory_entry(factory, entry, expected_where, classes, reason_codes):
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
    factory_comparability = Counter()
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
    factory_reasons = Counter()
    for reason in entry_reasons:
        factory_reasons[reason] += _mapping_integer(
            entry_reasons, reason, factory_where
        )
    return entry_records, factory_comparability, factory_reasons


def _validate_expected_classification(document, classes, reason_codes, run, where):
    expected = _mapping_object(document, "expected_classification", where)
    expected_where = f"{where}.expected_classification"
    records, comparability, expected_reasons = _validate_expected_totals(
        expected, expected_where, classes, reason_codes, run
    )
    by_factory = _mapping_object(expected, "by_factory", expected_where)
    factory_records = 0
    factory_comparability = Counter()
    factory_reasons = Counter()
    for factory, entry in by_factory.items():
        entry_records, entry_classes, entry_reasons = _validate_factory_entry(
            factory, entry, expected_where, classes, reason_codes
        )
        factory_records += entry_records
        factory_comparability.update(entry_classes)
        factory_reasons.update(entry_reasons)
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

