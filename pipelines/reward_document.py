#!/usr/bin/env python3
"""Ontology document validation, record curation, and vocabulary census."""

from __future__ import annotations

import copy
from collections import Counter

from reward_mapping import (
    ARITHMETIC_STATUSES,
    COMPONENT_DISPOSITIONS,
    MAGNITUDE_COMPARABLE,
    ONTOLOGY_VERSION,
    POLICY_DOCUMENT_TYPE,
    SHA256_RE,
    SIGN_ORDER_ONLY,
    MagnitudeNotComparable,
    RewardOntologyError,
    _canonical_record_id,
    _decimal,
    _json_number,
    _reject_nonfinite_numbers,
    _sha256,
)
from reward_policy import (
    ANNOTATION_FIELD,
    ARITHMETIC_METHODS,
    CANONICAL_SCOPE,
    CANONICAL_UNIT,
    CANONICAL_UNIT_USD,
    COMPARABILITY_CLASSES,
    DEFAULT_TOLERANCE,
    MAGNITUDE_AGGREGATION,
    REWARD_KEYS,
    SOURCE_VOCABULARY,
    validate_conversion_policy,
)
from reward_units import assess_arithmetic, _normalize_calibration
from reward_ontology import (
    _annotation_scope,
    _classify,
    _layout_scope,
    _require_catalogued_reasons,
    _require_declared_rule,
    _require_declared_verdict,
    _set_pointer,
    _walk_rewards,
    disposition_for_observed_types,
    reward_signature,
    value_type,
)


def _require_unique_string_codes(reasons, *, empty_message):
    if (
        not isinstance(reasons, list)
        or not reasons
        or not all(isinstance(code, str) for code in reasons)
        or len(reasons) != len(set(reasons))
    ):
        raise RewardOntologyError(empty_message)
    return reasons


def _validate_magnitude_value(value):
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


def _validate_magnitude_payload(magnitude):
    if (
        not isinstance(magnitude, dict)
        or magnitude.get("canonical_unit") != CANONICAL_UNIT
        or magnitude.get("aggregation") != MAGNITUDE_AGGREGATION
        or not isinstance(magnitude.get("values"), list)
        or not magnitude["values"]
    ):
        raise RewardOntologyError("invalid canonical magnitude payload")
    for value in magnitude["values"]:
        _validate_magnitude_value(value)


def _validate_annotation_payload(document, comparability):
    has_magnitude = "magnitude" in document
    has_order = "order" in document
    if comparability == MAGNITUDE_COMPARABLE:
        if not has_magnitude or has_order:
            raise RewardOntologyError("magnitude class requires magnitude only")
        _validate_magnitude_payload(document["magnitude"])
    elif has_magnitude:
        raise RewardOntologyError(
            "uncalibrated classes must not expose canonical magnitudes"
        )
    if comparability == SIGN_ORDER_ONLY:
        if not has_order:
            raise RewardOntologyError("sign/order class requires order evidence")
    elif has_order:
        raise RewardOntologyError("order evidence belongs only to sign/order class")


def _validate_training_annotation(document):
    comparability = document.get("comparability")
    if comparability not in COMPARABILITY_CLASSES:
        raise RewardOntologyError("invalid comparability class")
    reasons = _require_unique_string_codes(
        document.get("reason_codes"),
        empty_message="reason_codes must be nonempty and unique",
    )
    _require_catalogued_reasons(reasons)
    _require_declared_verdict(
        comparability, reasons, scope=_annotation_scope(document)
    )
    if not SHA256_RE.fullmatch(str(document.get("source_sidecar_id", ""))):
        raise RewardOntologyError("invalid source_sidecar_id")
    source_reward_count = document.get("source_reward_count")
    if (
        isinstance(source_reward_count, bool)
        or not isinstance(source_reward_count, int)
        or source_reward_count < 0
    ):
        raise RewardOntologyError("source_reward_count must be nonnegative")
    _validate_annotation_payload(document, comparability)
    return document


def _validate_sidecar_identity(document):
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


def _validate_sidecar_reward_entry(reward):
    if (
        not isinstance(reward, dict)
        or not SHA256_RE.fullmatch(str(reward.get("value_sha256", "")))
        or not isinstance(reward.get("json_pointer"), str)
        or not reward["json_pointer"].startswith("/")
        or "value" not in reward
    ):
        raise RewardOntologyError("invalid source reward entry")


def _validate_sidecar_classification(classification):
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
    return reason_codes


def _validate_sidecar_arithmetic_entry(entry):
    if not isinstance(entry, dict):
        raise RewardOntologyError("invalid sidecar arithmetic entry")
    if entry.get("status") not in ARITHMETIC_STATUSES:
        raise RewardOntologyError("invalid sidecar arithmetic status")
    if entry.get("method") not in ARITHMETIC_METHODS:
        raise RewardOntologyError(
            f"uncatalogued arithmetic method: {entry.get('method')!r}"
        )


def _validate_sidecar_calibration(document, classification):
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
        return
    if "external_calibration_evidence" in classification["reason_codes"]:
        raise RewardOntologyError(
            "external_calibration_evidence requires an applied sidecar calibration"
        )


def _validate_source_sidecar(document):
    _validate_sidecar_identity(document)
    rewards = document.get("source_rewards")
    if not isinstance(rewards, list):
        raise RewardOntologyError("source_rewards must be a list")
    for reward in rewards:
        _validate_sidecar_reward_entry(reward)
    classification = document.get("classification")
    reason_codes = _validate_sidecar_classification(classification)
    arithmetic_entries = document.get("arithmetic", [])
    if not isinstance(arithmetic_entries, list):
        raise RewardOntologyError("sidecar arithmetic must be a list")
    for entry in arithmetic_entries:
        _validate_sidecar_arithmetic_entry(entry)
    _validate_sidecar_calibration(document, classification)
    _require_declared_verdict(
        classification["comparability"],
        reason_codes,
        scope=_layout_scope(rewards),
    )
    return document


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
        return _validate_training_annotation(document)
    if kind == "reward_source_sidecar":
        return _validate_source_sidecar(document)
    raise RewardOntologyError(f"unknown ontology document_type: {kind!r}")


def _source_identity(source_path, source_line, source_record):
    identity = {
        "path": source_path,
        "line": source_line,
        "record_sha256": _sha256(source_record),
    }
    source_record_id = _canonical_record_id(source_record)
    if source_record_id is not None:
        identity["record_id"] = source_record_id
    return identity


def _annotation_payload(comparability, payload):
    if comparability == MAGNITUDE_COMPARABLE:
        return {"magnitude": payload}
    if comparability == SIGN_ORDER_ONLY:
        return {"order": payload}
    return {}


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
    _reject_nonfinite_numbers(source_record, where=source_path)
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

    sidecar_body = {
        "document_type": "reward_source_sidecar",
        "ontology_version": ONTOLOGY_VERSION,
        "source": _source_identity(source_path, source_line, source_record),
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
        **_annotation_payload(comparability, payload),
    }

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


def _census_shape_row(signature, occurrences, outcomes):
    row = {"signature": signature, "occurrences": occurrences}
    if len(outcomes) == 1:
        row["arithmetic_status"], row["arithmetic_method"] = outcomes[0]
    else:
        row["arithmetic_outcomes"] = [
            {"status": status, "method": method} for status, method in outcomes
        ]
    return row


def _census_record(record, scope_keys, key_types, key_counts, shapes, shape_outcomes, arithmetic):
    if not isinstance(record, dict):
        raise RewardOntologyError("census records must be objects")
    ontology_instances = sum(1 for _ in _walk_rewards(record))
    instances = 0
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
    return ontology_instances, instances


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
        record_ontology, record_instances = _census_record(
            record, scope_keys, key_types, key_counts, shapes, shape_outcomes, arithmetic
        )
        ontology_instances += record_ontology
        instances += record_instances

    dispositions = Counter({name: 0 for name in COMPONENT_DISPOSITIONS})
    component_keys = {}
    for key in sorted(key_types):
        disposition = disposition_for_observed_types(key, key_types[key])
        dispositions[disposition] += 1
        component_keys[key] = {
            "disposition": disposition,
            "observed_types": sorted(key_types[key]),
            "occurrences": key_counts[key],
        }

    shape_rows = [
        _census_shape_row(signature, shapes[signature], sorted(shape_outcomes[signature]))
        for signature in sorted(shapes)
    ]

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


