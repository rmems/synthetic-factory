#!/usr/bin/env python3
"""Conservatively map legacy rewards into reward ontology v1.

This module is intentionally record-level. It never edits raw data and it does
not infer a common magnitude merely because component arithmetic reconciles.
Callers receive:

* a deep-copied record with a top-level ``reward_training`` annotation; and
* a hash-addressed sidecar containing exact copies of every source reward.

Only ``magnitude_comparable`` annotations expose canonical numeric values.
``canonical_magnitudes`` refuses both other comparability classes.

The optional CLI writes only caller-specified, previously nonexistent files:

    python3 pipelines/curate_rewards.py classify input.jsonl
    python3 pipelines/curate_rewards.py convert input.jsonl output.jsonl sidecars.jsonl \
        --manifest manifest.json
    python3 pipelines/curate_rewards.py run source-run new-reward-lane

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
ANNOTATION_FIELD = "reward_training"
CANONICAL_UNIT = "usd_10000_risk_adjusted_delta"
CANONICAL_UNIT_USD = Decimal("10000")
DEFAULT_TOLERANCE = Decimal("0.0001")

MAGNITUDE_COMPARABLE = "magnitude_comparable"
SIGN_ORDER_ONLY = "sign_order_only"
EXCLUDE = "exclude_from_reward_training"
COMPARABILITY_CLASSES = frozenset(
    {MAGNITUDE_COMPARABLE, SIGN_ORDER_ONLY, EXCLUDE}
)

PREFERENCE_POINTERS = (
    "/chosen/reward_components",
    "/rejected/reward_components",
)
REWARD_KEYS = frozenset({"reward_components", "reward"})
UNWEIGHTED_EXCLUDE = frozenset(
    {
        "aggregation",
        "component_notes",
        "convention",
        "frame",
        "native_unit",
        "notes",
        "provenance_notes",
        "rounding_decimals",
        "total",
        "total_basis",
        "unit_usd",
        "units",
        "weights",
    }
)
WEIGHTED_CONTAINERS = (
    "components",
    "actual",
    "components_executed",
    "components_realized",
    "components_realized_inworld",
    "components_executed_realized_inworld",
)
WEIGHT_ALIASES = {
    "coord": ("coord", "coordination", "coordination_integrity"),
    "incentive": ("incentive", "incentive_integrity"),
    "safety": ("safety", "safety_alignment", "safety_process"),
    "task": ("task", "task_progress", "task_outcome"),
}

ROUNDING_RE = re.compile(r"(?:rounded?\s+(?:to\s+)?)?(\d+)[- ]decimal", re.I)
USD_UNIT_RE = re.compile(
    r"\b1(?:\.0)?(?:\s+reward\s+unit)?\s*=\s*"
    r"(?:USD\s*|\$\s*)([0-9][0-9,]*(?:\.[0-9]+)?)",
    re.I,
)
RECORD_ID_RE = re.compile(r"\bffpc-r\d+-\d+\b", re.I)
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

RUN_MANIFEST_FILENAME = "manifest.json"
RUN_SIDECAR_FILENAME = "reward-sidecars.jsonl"
RUN_CALIBRATION_FILENAME = "units-migration.json"


class RewardOntologyError(ValueError):
    """Raised when a reward document violates ontology-v1 invariants."""


class MagnitudeNotComparable(RewardOntologyError):
    """Raised when a caller asks an uncalibrated record for magnitudes."""


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


def _walk_rewards(value, tokens=()):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == ANNOTATION_FIELD:
                continue
            child_tokens = (*tokens, key)
            if key in REWARD_KEYS:
                yield _pointer(child_tokens), child
            yield from _walk_rewards(child, child_tokens)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_rewards(child, (*tokens, index))


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


def _reward_tolerance(reward) -> Decimal:
    decimals = reward.get("rounding_decimals")
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        decimals = None
        for key in ("notes", "aggregation", "convention"):
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
    component_container = reward.get("components")
    nested = isinstance(component_container, dict)
    siblings = [
        component
        for key, value in reward.items()
        if key not in UNWEIGHTED_EXCLUDE and not (nested and key == "components")
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

    total = _decimal(reward.get("total"))
    if total is None:
        return {**base, "status": "unsupported", "method": "no_numeric_total"}

    weights = reward.get("weights")
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
    units_text = reward.get("units")
    parsed = None
    if isinstance(units_text, str):
        match = USD_UNIT_RE.search(units_text)
        if match:
            parsed = Decimal(match.group(1).replace(",", ""))

    structured_present = "unit_usd" in reward
    structured = _decimal(reward.get("unit_usd")) if structured_present else None
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
    if not isinstance(units_text, str) or "risk-adjusted" not in units_text.lower():
        return None, "missing_risk_adjusted_semantics", None
    return unit, "explicit_usd_unit_calibration", "source_reward_fields"


def _classify(source_rewards, arithmetic, calibration=None):
    rewards_by_pointer = {
        item["json_pointer"]: item["value"] for item in source_rewards
    }
    arithmetic_by_pointer = {
        item["json_pointer"]: item for item in arithmetic
    }
    chosen_pointer, rejected_pointer = PREFERENCE_POINTERS
    is_preference = chosen_pointer in rewards_by_pointer or rejected_pointer in rewards_by_pointer

    if not source_rewards:
        return EXCLUDE, ["no_source_reward"], None

    if is_preference:
        if set(rewards_by_pointer) != set(PREFERENCE_POINTERS):
            return EXCLUDE, ["ambiguous_preference_reward_scopes"], None
        chosen_arithmetic = arithmetic_by_pointer[chosen_pointer]
        rejected_arithmetic = arithmetic_by_pointer[rejected_pointer]
        statuses = {chosen_arithmetic["status"], rejected_arithmetic["status"]}
        if "invalid" in statuses:
            return EXCLUDE, ["reward_arithmetic_mismatch"], None
        if statuses != {"valid"}:
            return EXCLUDE, ["unsupported_reward_layout"], None

        chosen_total = _decimal(chosen_arithmetic["source_total"])
        rejected_total = _decimal(rejected_arithmetic["source_total"])
        if chosen_total is None or rejected_total is None:
            return EXCLUDE, ["unsupported_reward_layout"], None
        if chosen_total <= rejected_total:
            return EXCLUDE, ["reward_order_conflicts_with_preference"], None

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
            )

        reasons = ["preference_order_verified"]
        if any("conflict" in status for status in unit_statuses):
            reasons.append("magnitude_calibration_conflict")
        elif any(status != "missing_unit_calibration" for status in unit_statuses):
            reasons.append("magnitude_calibration_incomplete")
        else:
            reasons.append("magnitude_calibration_missing")
        return SIGN_ORDER_ONLY, reasons, {
            "preferred_json_pointer": chosen_pointer,
            "dispreferred_json_pointer": rejected_pointer,
            "relation": "preferred_gt_dispreferred",
        }

    if len(source_rewards) != 1:
        return EXCLUDE, ["multiple_reward_scopes"], None
    pointer = source_rewards[0]["json_pointer"]
    if pointer != "/reward_components":
        return EXCLUDE, ["noncanonical_reward_scope"], None
    result = arithmetic_by_pointer[pointer]
    if result["status"] == "invalid":
        return EXCLUDE, ["reward_arithmetic_mismatch"], None
    if result["status"] != "valid":
        return EXCLUDE, ["unsupported_reward_layout"], None
    unit, unit_status, calibration_source = _extract_unit_usd(
        rewards_by_pointer[pointer], calibration
    )
    if unit is None:
        if "conflict" in unit_status:
            return EXCLUDE, ["magnitude_calibration_conflict"], None
        if unit_status == "missing_risk_adjusted_semantics":
            return EXCLUDE, ["magnitude_semantics_missing"], None
        return EXCLUDE, ["magnitude_calibration_missing"], None
    return (
        MAGNITUDE_COMPARABLE,
        ["explicit_usd_unit_calibration", "reward_arithmetic_verified"],
        _magnitude_payload(
            {pointer: result},
            {pointer: unit},
            {pointer: calibration_source},
        ),
    )


classify_source_rewards = _classify


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
        "aggregation": "linear_unit_conversion_only",
        "values": values,
    }


def validate_ontology_document(document):
    """Validate the invariants that prevent unsafe canonical magnitudes."""
    if not isinstance(document, dict):
        raise RewardOntologyError("ontology document must be an object")
    if document.get("ontology_version") != ONTOLOGY_VERSION:
        raise RewardOntologyError("unknown reward ontology version")
    kind = document.get("document_type")
    if kind == "reward_training_annotation":
        comparability = document.get("comparability")
        if comparability not in COMPARABILITY_CLASSES:
            raise RewardOntologyError("invalid comparability class")
        reasons = document.get("reason_codes")
        if not isinstance(reasons, list) or not reasons or len(reasons) != len(set(reasons)):
            raise RewardOntologyError("reason_codes must be nonempty and unique")
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
                or magnitude.get("aggregation") != "linear_unit_conversion_only"
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
    comparability, reason_codes, payload = _classify(
        source_rewards,
        arithmetic,
        normalized_calibration,
    )

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
    return {
        value["json_pointer"]: value["canonical_value"]
        for value in annotation["magnitude"]["values"]
    }


def units_migration_catalog(document, evidence_path):
    """Build explicit per-record conversions from authenticated JSON evidence."""

    path = Path(evidence_path)
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        raise RewardOntologyError(f"{path}: calibration records must be a list")

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
    return units_migration_catalog(document, path)


def load_units_migration_bytes(payload, *, label="<memory>"):
    """Parse exact migration bytes into the same catalog ``load_units_migration`` builds."""
    if not isinstance(payload, bytes):
        raise RewardOntologyError("calibration payload must be bytes")
    try:
        document = json.loads(payload.decode("utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RewardOntologyError(f"{label}: invalid calibration JSON: {exc}") from exc
    return units_migration_catalog(document, label)


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
    convert.add_argument("--manifest", required=True)
    convert.add_argument("--source-path")
    convert.add_argument("--units-migration")

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
        calibration_catalog = (
            load_units_migration(args.units_migration)
            if args.units_migration
            else None
        )
        if args.command == "classify":
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
