#!/usr/bin/env python3
"""Shared oracle-grounded record contract for the distillation dataset families.

Introduced by issue #78 for the three control-oriented families:

* ``neuromorphic-fault-recovery``
* ``snn-energy-routing-preferences``
* ``moe-router-distillation-trajectories``

The envelope follows the shared contract sketched in the parent epic (#76):
``generator`` / ``scenario`` / ``intervention`` / ``candidate_prediction`` /
``oracle`` / ``result`` / ``provenance`` / ``validation``.

Three invariants matter more than the field list:

1. **Generators propose, oracles decide.** ``generator.authority`` is pinned to
   ``propose_only``. Any oracle-measured key (``measurements``, ``outcome``,
   ``energy_j``, ``router_logits``, ...) appearing inside a generator-owned
   namespace is a contract violation, not a convenience.
2. **Measurements carry units and a meter.** Energy-class quantities are only
   accepted from a meter that physically measures energy. An analytic
   operation-count or synaptic-operation model can be recorded, but it can
   never stand in for a measured joule.
3. **Nothing self-certifies.** Producers write ``validation.status =
   "unvalidated"``. Only a validator may stamp ``passed``/``failed``, and only
   with its own name and version attached. Curation fails closed unless an
   *authoritative* oracle actually produced a measured result.

This module is standard library only, like the rest of ``pipelines/``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "oracle-grounded/1.0.0"

FAMILIES = (
    "neuromorphic-fault-recovery",
    "snn-energy-routing-preferences",
    "moe-router-distillation-trajectories",
)

GENERATOR_AUTHORITY = "propose_only"
GENERATOR_KINDS = frozenset({"programmatic", "llm", "human", "hybrid"})

AUTHORITY_AUTHORITATIVE = "authoritative"
AUTHORITY_REFERENCE_ONLY = "reference_only"
ORACLE_AUTHORITIES = frozenset({AUTHORITY_AUTHORITATIVE, AUTHORITY_REFERENCE_ONLY})

# An oracle type names *how* truth was obtained, never who asked for it.
ORACLE_TYPES = frozenset(
    {
        "deterministic_simulator",
        "measured_execution",
        "recorded_measurement",
        "real_model_router",
        "reference_model_router",
        "hardware_replay",
    }
)

RESULT_MEASURED = "measured"
RESULT_ABSTAINED = "abstained"
RESULT_STATUSES = frozenset({RESULT_MEASURED, RESULT_ABSTAINED})

VALIDATION_UNVALIDATED = "unvalidated"
VALIDATION_PASSED = "passed"
VALIDATION_FAILED = "failed"
VALIDATION_STATUSES = frozenset(
    {VALIDATION_UNVALIDATED, VALIDATION_PASSED, VALIDATION_FAILED}
)

# Namespaces a generator owns. Oracle-measured keys may never appear here.
GENERATOR_NAMESPACES = ("generator", "scenario", "intervention", "candidate_prediction")

# Keys that only an oracle may write. Compared by exact key name at any depth
# inside a generator-owned namespace.
ORACLE_ONLY_KEYS = frozenset(
    {
        "measurements",
        "measurement",
        "measured_by",
        "outcome",
        "reason_codes",
        "joules",
        "energy_j",
        "power_w",
        "cpu_time_s",
        "wall_time_s",
        "latency_ms",
        "router_logits",
        "top_k_experts",
        "expert_ids",
        "routing_entropy",
        "top1_top2_margin",
        "expert_agreement",
        "task_quality",
        "preference",
        "safety_ok",
        "result",
        # Emitted oracle summaries. `top1_expert` was missing, so a router
        # record could copy the teacher label into the student-visible
        # scenario namespace, rehash, and hand training a trivially leaked
        # target; the rest are the same class of oracle-owned outputs.
        "top1_expert",
        "routing",
        "teacher_grounded",
        "outcome_label",
        "prediction_agreement",
        "integrity_violation",
        "detection_latency_ms",
        "recovery_latency_ms",
        "candidates",
        "reference_objective",
        "cost_is_energy",
        "abstention_reason",
    }
)

# Direct keys allowed under candidate_prediction. Everything else must be
# ``predicted_*`` so a generator guess can never be mistaken for a label.
PREDICTION_FREE_KEYS = frozenset({"rationale", "confidence", "method"})
PREDICTION_PREFIX = "predicted_"

# quantity -> canonical unit. A measurement must declare the canonical unit.
QUANTITY_UNITS = {
    "energy_j": "J",
    "energy_per_op_j": "J",
    "power_w": "W",
    "cpu_time_s": "s",
    "wall_time_s": "s",
    "latency_ms": "ms",
    "detection_latency_ms": "ms",
    "recovery_latency_ms": "ms",
    "temperature_c": "degC",
    "peak_temperature_c": "degC",
    "max_rss_kb": "kB",
    "context_switches": "count",
    "healthy_channel_count": "count",
    "dropped_event_count": "count",
    "residual_error": "ratio",
    "corrupt_ratio": "ratio",
    "task_quality": "ratio",
    "routing_entropy": "nat",
    "top1_top2_margin": "logit",
    "expert_agreement": "ratio",
    "repeats": "count",
}

# Quantity domains. `is_number` alone accepted any finite value, so a
# rehashed record could serve wall_time_s = -5, a negative event count, or a
# ratio outside [0, 1] as an oracle measurement target. Temperatures are the
# only listed quantities a physical reading may take below zero.
NON_NEGATIVE_QUANTITIES = frozenset(
    {
        "energy_j",
        "energy_per_op_j",
        "power_w",
        "cpu_time_s",
        "wall_time_s",
        "latency_ms",
        "detection_latency_ms",
        "recovery_latency_ms",
        "max_rss_kb",
        "context_switches",
        "healthy_channel_count",
        "dropped_event_count",
        "repeats",
        "routing_entropy",
        "top1_top2_margin",
    }
)
UNIT_INTERVAL_QUANTITIES = frozenset(
    {
        "residual_error",
        "corrupt_ratio",
        "task_quality",
        "expert_agreement",
    }
)

ENERGY_QUANTITIES = frozenset({"energy_j", "energy_per_op_j", "power_w"})

# Meters that physically measure energy. Anything outside this set may not
# produce an energy-class quantity. `recorded_power_run` is deliberately
# absent: it is the replay *wrapper*, not an instrument — a replayed joule
# must name the physical meter the recording says took it, or a file of bare
# observations could launder energy readings behind the wrapper's name.
MEASURED_ENERGY_METERS = frozenset(
    {
        "intel_rapl_powercap",
        "external_power_meter",
        "board_power_rail",
    }
)

# Meters that model rather than measure. Legal for non-energy bookkeeping and
# for explicitly modeled quantities, never for an energy claim.
MODELED_METERS = frozenset(
    {
        "analytic_op_count",
        "synops_model",
        "spike_energy_model",
        "datasheet_estimate",
    }
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

ISO_8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class ContractError(ValueError):
    """Raised when a record cannot be built inside the contract."""


class OracleUnavailable(RuntimeError):
    """Raised when a named oracle cannot run in this environment.

    Callers must let this propagate or record an explicit abstention. It must
    never be swallowed into a synthesized result.
    """

    def __init__(self, oracle: str, detail: str) -> None:
        super().__init__(f"{oracle} unavailable: {detail}")
        self.oracle = oracle
        self.detail = detail


def canonical_json(value: Any) -> str:
    """Return the canonical JSON form used for digests and equality."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing ``Z``."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def is_number(value: Any) -> bool:
    """True for a real, finite, non-boolean number."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def is_enum_value(value: Any, allowed) -> bool:
    """Membership test for enum-like JSON fields that cannot raise.

    A JSON-valid record can put an array or object where a string enum
    belongs. Testing such an unhashable value against a set (or using it as a
    dict key) raises ``TypeError``, and ``validate_path`` does not catch that —
    one malformed line would abort validation of the entire run. A non-string
    is simply not a member.
    """

    return isinstance(value, str) and value in allowed


def is_true(value: Any) -> bool:
    """Identity test against ``True`` for fields untrusted input controls.

    ``bool(value)`` would accept any truthy JSON value — ``"yes"``, ``[0]``,
    ``1`` — where the contract demands the boolean itself, so gates built on
    truthiness fail open on malformed records. Only ``True`` is true here.
    """

    return value is True


def is_genuine_int(value: Any) -> bool:
    """True for a genuine integer — never a boolean wearing int's clothes."""

    return isinstance(value, int) and not isinstance(value, bool)


def record_digest(record: dict[str, Any]) -> str:
    """SHA-256 over the record with volatile/derived fields removed.

    ``validation`` and ``provenance.record_sha256`` are excluded so stamping a
    validation verdict does not change the identity of the measured record.
    """

    payload = copy.deepcopy(record)
    payload.pop("validation", None)
    provenance = payload.get("provenance")
    if isinstance(provenance, dict):
        provenance.pop("record_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def new_measurement(
    quantity: str,
    value: float,
    meter: str,
    *,
    unit: str | None = None,
    measured: bool = True,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one oracle-side measurement.

    Raises ``ContractError`` for an unknown quantity, a unit that disagrees
    with the registry, or an energy-class quantity from a non-energy meter.
    """

    if quantity not in QUANTITY_UNITS:
        raise ContractError(f"unknown measurement quantity: {quantity!r}")
    canonical_unit = QUANTITY_UNITS[quantity]
    if unit is not None and unit != canonical_unit:
        raise ContractError(
            f"{quantity} must be reported in {canonical_unit!r}, got {unit!r}"
        )
    if not is_number(value):
        raise ContractError(f"{quantity} value must be a finite number, got {value!r}")
    if quantity in ENERGY_QUANTITIES and (
        not measured or meter not in MEASURED_ENERGY_METERS
    ):
        raise ContractError(
            f"{quantity} requires a measured energy meter "
            f"(one of {sorted(MEASURED_ENERGY_METERS)}), got {meter!r}"
        )
    payload: dict[str, Any] = {
        "quantity": quantity,
        "value": float(value),
        "unit": canonical_unit,
        "meter": meter,
        "measured": bool(measured),
        "source": "oracle",
    }
    if detail:
        payload["detail"] = copy.deepcopy(detail)
    return payload


def new_generator(
    name: str,
    *,
    version: str,
    kind: str = "programmatic",
    seed: int | None = None,
    model: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build the generator block. Authority is pinned to ``propose_only``."""

    if kind not in GENERATOR_KINDS:
        raise ContractError(f"unknown generator kind: {kind!r}")
    if kind == "llm" and not model:
        raise ContractError("an llm generator must name its model")
    block: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "version": version,
        "seed": seed,
        "authority": GENERATOR_AUTHORITY,
    }
    if model:
        block["model"] = model
    if notes:
        block["notes"] = notes
    return block


def new_oracle(
    name: str,
    *,
    oracle_type: str,
    implementation: str,
    version: str,
    authority: str = AUTHORITY_AUTHORITATIVE,
    configuration: dict[str, Any] | None = None,
    seed: int | None = None,
    commit: str | None = None,
    fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the oracle block.

    ``authority`` is ``authoritative`` for an oracle whose output may ground a
    training label, and ``reference_only`` for a stand-in whose output proves
    the pipeline shape but must never be curated as teacher truth.
    """

    if oracle_type not in ORACLE_TYPES:
        raise ContractError(f"unknown oracle type: {oracle_type!r}")
    if authority not in ORACLE_AUTHORITIES:
        raise ContractError(f"unknown oracle authority: {authority!r}")
    block: dict[str, Any] = {
        "name": name,
        "type": oracle_type,
        "implementation": implementation,
        "version": version,
        "authority": authority,
        "configuration": copy.deepcopy(configuration) if configuration else {},
        "seed": seed,
        "commit": commit,
    }
    if fingerprint is not None:
        block["fingerprint"] = copy.deepcopy(fingerprint)
    return block


def new_result(
    *,
    status: str = RESULT_MEASURED,
    measurements: list[dict[str, Any]] | None = None,
    abstention_reason: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build the oracle-side result block."""

    if status not in RESULT_STATUSES:
        raise ContractError(f"unknown result status: {status!r}")
    payload: dict[str, Any] = {
        "status": status,
        "measurements": list(measurements or []),
    }
    if status == RESULT_MEASURED and not payload["measurements"]:
        raise ContractError("a measured result needs at least one measurement")
    if status == RESULT_ABSTAINED:
        if not (abstention_reason or "").strip():
            raise ContractError("an abstained result needs an abstention_reason")
        payload["abstention_reason"] = abstention_reason
    payload.update(copy.deepcopy(fields))
    return payload


def new_provenance(producer: str, **fields: Any) -> dict[str, Any]:
    """Build the provenance block with a UTC production timestamp."""

    payload: dict[str, Any] = {"producer": producer, "produced_at": utc_now_iso()}
    payload.update(copy.deepcopy(fields))
    return payload


def unvalidated() -> dict[str, Any]:
    """Return the only validation block a producer is allowed to write."""

    return {"status": VALIDATION_UNVALIDATED, "validator": None, "findings": []}


def build_record(
    *,
    record_id: str,
    family: str,
    generator: dict[str, Any],
    scenario: dict[str, Any],
    oracle: dict[str, Any],
    result: dict[str, Any],
    provenance: dict[str, Any],
    intervention: dict[str, Any] | None = None,
    candidate_prediction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble one oracle-grounded record and stamp its content digest."""

    if family not in FAMILIES:
        raise ContractError(f"unknown family: {family!r}")
    record: dict[str, Any] = {
        "id": record_id,
        "family": family,
        "schema_version": SCHEMA_VERSION,
        "generator": copy.deepcopy(generator),
        "scenario": copy.deepcopy(scenario),
        "oracle": copy.deepcopy(oracle),
        "result": copy.deepcopy(result),
        "provenance": copy.deepcopy(provenance),
        "validation": unvalidated(),
    }
    if intervention is not None:
        record["intervention"] = copy.deepcopy(intervention)
    if candidate_prediction is not None:
        record["candidate_prediction"] = copy.deepcopy(candidate_prediction)
    record["provenance"]["record_sha256"] = record_digest(record)
    return record


def _walk_keys(value: Any, path: str):
    """Yield ``(path, key, value)`` for every dict entry beneath ``value``."""

    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}" if path else key
            yield child, key, item
            yield from _walk_keys(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_keys(item, f"{path}[{index}]")


def check_generator_oracle_separation(record: dict[str, Any], where: str) -> list[str]:
    """Reject oracle-owned keys hiding inside generator-owned namespaces."""

    errors: list[str] = []
    for namespace in GENERATOR_NAMESPACES:
        block = record.get(namespace)
        if block is None:
            continue
        if not isinstance(block, (dict, list)):
            errors.append(f"{where}.{namespace} must be an object")
            continue
        for path, key, _ in _walk_keys(block, namespace):
            if key in ORACLE_ONLY_KEYS:
                errors.append(
                    f"{where}: ORACLE_FIELD_IN_GENERATOR_NAMESPACE at {path} "
                    f"(key {key!r} may only be written by an oracle)"
                )
    prediction = record.get("candidate_prediction")
    if isinstance(prediction, dict):
        for key in sorted(prediction):
            if key in PREDICTION_FREE_KEYS or key.startswith(PREDICTION_PREFIX):
                continue
            errors.append(
                f"{where}.candidate_prediction.{key}: generator predictions must be "
                f"named {PREDICTION_PREFIX}* (or one of "
                f"{sorted(PREDICTION_FREE_KEYS)})"
            )
    return errors


def _quantity_domain_errors(quantity: str, value: float, spot: str) -> list[str]:
    """The domain a quantity's value must lie in, beyond being finite."""

    if quantity in NON_NEGATIVE_QUANTITIES and value < 0.0:
        return [f"{spot}: {quantity} cannot be negative, got {value}"]
    if quantity in UNIT_INTERVAL_QUANTITIES and not 0.0 <= value <= 1.0:
        return [f"{spot}: {quantity} must lie in [0, 1], got {value}"]
    return []


def _check_measurement_item(item: Any, spot: str) -> list[str]:
    """One measurement's quantity, unit, meter and provenance."""

    if not isinstance(item, dict):
        return [f"{spot}: measurement must be an object"]
    quantity = item.get("quantity")
    if not is_enum_value(quantity, QUANTITY_UNITS):
        return [f"{spot}: unknown quantity {quantity!r}"]
    errors: list[str] = []
    if not is_number(item.get("value")):
        errors.append(f"{spot}: value must be a finite number")
    else:
        errors.extend(_quantity_domain_errors(quantity, float(item["value"]), spot))
    expected_unit = QUANTITY_UNITS[quantity]
    if item.get("unit") != expected_unit:
        errors.append(
            f"{spot}: {quantity} must declare unit {expected_unit!r}, "
            f"got {item.get('unit')!r}"
        )
    meter = item.get("meter")
    if not isinstance(meter, str) or not meter.strip():
        errors.append(f"{spot}: meter must be a non-empty string")
    if item.get("source") != "oracle":
        errors.append(f"{spot}: source must be 'oracle'")
    if not isinstance(item.get("measured"), bool):
        errors.append(f"{spot}: measured must be a boolean")
    return errors


def check_measurements(record: dict[str, Any], where: str) -> list[str]:
    """Validate every measurement's quantity, unit, meter and provenance."""

    result = record.get("result")
    if not isinstance(result, dict):
        return [f"{where}.result must be an object"]
    measurements = result.get("measurements")
    if not isinstance(measurements, list):
        return [f"{where}.result.measurements must be an array"]
    errors: list[str] = []
    for index, item in enumerate(measurements):
        errors += _check_measurement_item(
            item, f"{where}.result.measurements[{index}]"
        )
    return errors


ENERGY_KEY_HINTS = ("joule", "energy", "watt", "_wh", "kwh", "power_w")


def _is_energy_key(key: str) -> bool:
    """True when a field name reads as an energy value rather than a label."""

    lowered = key.lower()
    if lowered in ENERGY_QUANTITIES:
        return True
    return any(hint in lowered for hint in ENERGY_KEY_HINTS)


def _energy_measurement_claims(
    measurements: list[Any], where: str
) -> tuple[list[str], set[str]]:
    """Errors for modeled energy readings, plus the honestly measured ones."""

    errors: list[str] = []
    measured_energy_quantities: set[str] = set()
    for index, item in enumerate(measurements):
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        if not is_enum_value(quantity, ENERGY_QUANTITIES):
            continue
        spot = f"{where}.result.measurements[{index}]"
        meter = item.get("meter")
        if is_enum_value(meter, MODELED_METERS) or item.get("measured") is not True:
            errors.append(
                f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} came from "
                f"meter {meter!r}; energy must be physically measured"
            )
            continue
        if not is_enum_value(meter, MEASURED_ENERGY_METERS):
            errors.append(
                f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} needs a meter in "
                f"{sorted(MEASURED_ENERGY_METERS)}, got {meter!r}"
            )
            continue
        measured_energy_quantities.add(quantity)
    return errors, measured_energy_quantities


def _bare_energy_field_errors(result: dict[str, Any]) -> list[str]:
    """A bare energy number anywhere under ``result`` is an energy claim too.

    Without this, ``result["energy_j"] = 1e-7`` sails past the measurement
    checks because it never appears in ``result.measurements`` at all.
    """

    errors: list[str] = []
    for path, key, value in _walk_keys(result, "result"):
        # Only a number can be an energy value. A boolean is a flag
        # (`cost_is_energy`, `measures_energy`) and a string names a quantity.
        if key == "measurements" or not is_number(value) or not _is_energy_key(key):
            continue
        errors.append(
            f"{path}: THEORETICAL_ENERGY_CLAIM — an energy value must be carried "
            "as a measurement with a meter, not as a bare field"
        )
    return errors


def check_no_theoretical_energy_claim(record: dict[str, Any], where: str) -> list[str]:
    """Refuse an energy number that was modeled rather than measured.

    Covers both directions: an energy-class quantity produced by a modeled
    meter, and a preference/comparison denominated in an energy quantity that
    has no measured energy behind it.
    """

    result = record.get("result")
    if not isinstance(result, dict):
        return []
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    errors, measured_energy_quantities = _energy_measurement_claims(
        measurements, where
    )
    errors += _bare_energy_field_errors(result)

    preference = result.get("preference")
    if isinstance(preference, dict):
        cost_quantity = preference.get("cost_quantity")
        if (
            is_enum_value(cost_quantity, ENERGY_QUANTITIES)
            and cost_quantity not in measured_energy_quantities
        ):
            errors.append(
                f"{where}.result.preference: THEORETICAL_ENERGY_CLAIM — preference "
                f"is denominated in {cost_quantity!r} with no measured energy "
                f"measurement behind it"
            )
    return errors


def _check_generator_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.generator must be an object"]
    errors: list[str] = []
    if not isinstance(block.get("name"), str) or not block["name"].strip():
        errors.append(f"{where}.generator.name must be a non-empty string")
    if not is_enum_value(block.get("kind"), GENERATOR_KINDS):
        errors.append(
            f"{where}.generator.kind must be one of {sorted(GENERATOR_KINDS)}"
        )
    if not isinstance(block.get("version"), str) or not block["version"].strip():
        errors.append(f"{where}.generator.version must be a non-empty string")
    if block.get("authority") != GENERATOR_AUTHORITY:
        errors.append(
            f"{where}.generator.authority must be {GENERATOR_AUTHORITY!r} — "
            "a generator may never certify its own result"
        )
    if block.get("kind") == "llm" and not isinstance(block.get("model"), str):
        errors.append(f"{where}.generator.model is required for an llm generator")
    if "seed" not in block:
        errors.append(f"{where}.generator.seed must be present (null when unseeded)")
    elif block["seed"] is not None and not is_genuine_int(block["seed"]):
        # The shared envelope restricts the seed to integer/null. Presence
        # alone accepted {"seed": {}} or "seed": true, so malformed
        # reproducibility metadata stayed curation-eligible.
        errors.append(
            f"{where}.generator.seed must be an integer or null, "
            f"got {block['seed']!r}"
        )
    return errors


def _check_oracle_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.oracle must be an object"]
    errors: list[str] = []
    if not isinstance(block.get("name"), str) or not block["name"].strip():
        errors.append(f"{where}.oracle.name must be a non-empty string")
    if not is_enum_value(block.get("type"), ORACLE_TYPES):
        errors.append(f"{where}.oracle.type must be one of {sorted(ORACLE_TYPES)}")
    for key in ("implementation", "version"):
        value = block.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}.oracle.{key} must be a non-empty string")
    if not is_enum_value(block.get("authority"), ORACLE_AUTHORITIES):
        errors.append(
            f"{where}.oracle.authority must be one of {sorted(ORACLE_AUTHORITIES)}"
        )
    if not isinstance(block.get("configuration"), dict):
        errors.append(f"{where}.oracle.configuration must be an object")
    # Presence is not enough: the shared schema restricts these to
    # integer/null and string/null, and nothing else inspected them — so
    # ``seed: {}`` and ``commit: []`` passed as reproducibility metadata.
    if "seed" not in block:
        errors.append(f"{where}.oracle.seed must be present (null when n/a)")
    elif block["seed"] is not None and not is_genuine_int(block["seed"]):
        errors.append(
            f"{where}.oracle.seed must be an integer or null, got {block['seed']!r}"
        )
    if "commit" not in block:
        errors.append(f"{where}.oracle.commit must be present (null when n/a)")
    elif block["commit"] is not None and not isinstance(block["commit"], str):
        errors.append(
            f"{where}.oracle.commit must be a string or null, got {block['commit']!r}"
        )
    return errors


def _check_result_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.result must be an object"]
    errors: list[str] = []
    status = block.get("status")
    if not is_enum_value(status, RESULT_STATUSES):
        errors.append(f"{where}.result.status must be one of {sorted(RESULT_STATUSES)}")
        return errors
    measurements = block.get("measurements")
    if not isinstance(measurements, list):
        errors.append(f"{where}.result.measurements must be an array")
    elif status == RESULT_MEASURED and not measurements:
        errors.append(
            f"{where}.result: ORACLE_RESULT_MISSING — a measured result needs at "
            "least one measurement"
        )
    if status == RESULT_ABSTAINED:
        reason = block.get("abstention_reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{where}.result.abstention_reason must explain why the oracle "
                "produced no measurement"
            )
    return errors


def _check_provenance_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.provenance must be an object"]
    errors: list[str] = []
    producer = block.get("producer")
    if not isinstance(producer, str) or not producer.strip():
        errors.append(f"{where}.provenance.producer must be a non-empty string")
    produced_at = block.get("produced_at")
    if not isinstance(produced_at, str) or not ISO_8601_RE.match(produced_at):
        errors.append(
            f"{where}.provenance.produced_at must be an ISO-8601 UTC timestamp"
        )
    # Required, not optional. If the digest may be absent, deleting it is all it
    # takes to switch off tamper detection for the whole record.
    digest = block.get("record_sha256")
    if not isinstance(digest, str) or not SHA256_RE.match(digest):
        errors.append(f"{where}.provenance.record_sha256 must be a sha256 hex digest")
    return errors


def _check_validation_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.validation must be an object"]
    errors: list[str] = []
    status = block.get("status")
    if not is_enum_value(status, VALIDATION_STATUSES):
        errors.append(
            f"{where}.validation.status must be one of {sorted(VALIDATION_STATUSES)}"
        )
        return errors
    validator = block.get("validator")
    if status == VALIDATION_UNVALIDATED:
        if validator not in (None, {}):
            errors.append(
                f"{where}.validation: unvalidated records must not name a validator"
            )
        return errors
    return errors + _check_validator_object(validator, where)


def _check_validator_object(validator: Any, where: str) -> list[str]:
    """The validator identity a passed/failed verdict must carry."""

    if not isinstance(validator, dict):
        return [
            f"{where}.validation.validator must be an object naming the validator "
            "that stamped this verdict"
        ]
    errors: list[str] = []
    for key in ("name", "version"):
        value = validator.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}.validation.validator.{key} must be a non-empty string")
    checked_at = validator.get("checked_at")
    if not isinstance(checked_at, str) or not ISO_8601_RE.match(checked_at):
        errors.append(
            f"{where}.validation.validator.checked_at must be an ISO-8601 UTC timestamp"
        )
    validated_digest = validator.get("validated_digest")
    if validated_digest is not None and not (
        isinstance(validated_digest, str) and SHA256_RE.match(validated_digest)
    ):
        errors.append(
            f"{where}.validation.validator.validated_digest must be a sha256 digest"
        )
    return errors


def check_envelope(record: Any, where: str) -> list[str]:
    """Validate the shared envelope. Returns a list of human-readable errors."""

    if not isinstance(record, dict):
        return [f"{where}: record must be a JSON object"]
    errors: list[str] = []
    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id.strip():
        errors.append(f"{where}.id must be a non-empty string")
    if record.get("family") not in FAMILIES:
        errors.append(f"{where}.family must be one of {sorted(FAMILIES)}")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"{where}.schema_version must be {SCHEMA_VERSION!r}, "
            f"got {record.get('schema_version')!r}"
        )
    if not isinstance(record.get("scenario"), dict) or not record["scenario"]:
        errors.append(f"{where}.scenario must be a non-empty object")
    for optional in ("intervention", "candidate_prediction"):
        # Must be an object, not a list: the predicted_* naming rule below is
        # only expressible over named keys, so a list would slip past it.
        if optional in record and not isinstance(record[optional], dict):
            errors.append(f"{where}.{optional} must be an object")
    errors += _check_generator_block(record.get("generator"), where)
    errors += _check_oracle_block(record.get("oracle"), where)
    errors += _check_result_block(record.get("result"), where)
    errors += _check_provenance_block(record.get("provenance"), where)
    errors += _check_validation_block(record.get("validation"), where)
    errors += check_generator_oracle_separation(record, where)
    errors += check_measurements(record, where)
    errors += check_no_theoretical_energy_claim(record, where)
    return errors


def check_digest(record: dict[str, Any], where: str) -> list[str]:
    """Verify ``provenance.record_sha256`` still matches the record content."""

    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or "record_sha256" not in provenance:
        return []
    expected = record_digest(record)
    actual = provenance.get("record_sha256")
    if actual != expected:
        return [
            f"{where}.provenance.record_sha256 mismatch: recorded {actual!r}, "
            f"content hashes to {expected!r}"
        ]
    return []


def stamp_validation(
    record: dict[str, Any],
    *,
    validator: str,
    version: str,
    findings: list[str],
) -> dict[str, Any]:
    """Return a copy of ``record`` with a validator-owned verdict attached.

    The producer never calls this; only a validator does. The measured content
    digest is unchanged because ``record_digest`` excludes ``validation``, and
    the verdict carries the digest it was formed over so a stamp cannot be
    lifted from one record onto another.

    A stamp records that a validation happened; it is not evidence that one
    did. See :func:`curation_eligible`, which decides on the caller's own
    findings and never reads this block.
    """

    stamped = copy.deepcopy(record)
    stamped["validation"] = {
        "status": VALIDATION_FAILED if findings else VALIDATION_PASSED,
        "validator": {
            "name": validator,
            "version": version,
            "checked_at": utc_now_iso(),
            "validated_digest": record_digest(record),
        },
        "findings": list(findings),
    }
    return stamped


def curation_eligible(
    record: dict[str, Any], findings: list[str]
) -> tuple[bool, list[str]]:
    """Fail closed: only an authoritative oracle's measured, validated result.

    ``findings`` must come from the caller's *own* validation run over this
    record; an empty list means it validated clean. The ``validation`` block
    already sitting in the record is deliberately not consulted. Nothing stored
    in a file can prove who wrote it, so trusting it would let a producer stamp
    itself ``passed`` and walk straight through this gate.

    Structural validity alone never makes a record training-ready, and a
    ``reference_only`` oracle proves the pipeline shape without ever grounding
    a label.
    """

    reasons: list[str] = []
    if findings:
        reasons.append(f"VALIDATION_FINDINGS:{len(findings)}")
    reasons += _oracle_authority_reasons(record.get("oracle"))
    reasons += _measured_result_reasons(record.get("result"))
    reasons += _digest_reasons(record)
    return (not reasons), reasons


def _oracle_authority_reasons(oracle: Any) -> list[str]:
    if not isinstance(oracle, dict):
        return ["ORACLE_BLOCK_MISSING"]
    if oracle.get("authority") != AUTHORITY_AUTHORITATIVE:
        return [f"ORACLE_NOT_AUTHORITATIVE:{oracle.get('authority')!r}"]
    return []


def _measured_result_reasons(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return ["ORACLE_RESULT_MISSING"]
    if result.get("status") != RESULT_MEASURED:
        return [f"ORACLE_RESULT_NOT_MEASURED:{result.get('status')!r}"]
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    if not measurements:
        return ["ORACLE_RESULT_MISSING"]
    if not any(
        isinstance(item, dict) and item.get("measured") is True
        for item in measurements
    ):
        # A list of `measured: false` readings is a modelled result wearing
        # a measured status. Curating it would admit modelled labels.
        return ["NO_MEASURED_READING"]
    return []


def _digest_reasons(record: dict[str, Any]) -> list[str]:
    provenance = record.get("provenance")
    recorded_digest = (
        provenance.get("record_sha256") if isinstance(provenance, dict) else None
    )
    if not isinstance(recorded_digest, str) or not SHA256_RE.match(recorded_digest):
        # Without a digest there is nothing for check_digest to compare, so a
        # deleted digest would otherwise be a clean bypass of tamper detection.
        return ["RECORD_DIGEST_MISSING"]
    if check_digest(record, "record"):
        return ["RECORD_DIGEST_MISMATCH"]
    return []


def stamp_is_bound_to_content(record: dict[str, Any]) -> bool:
    """True when a stamped verdict was formed over this exact content.

    Catches a verdict lifted from one record onto another. It says nothing
    about *who* stamped it, which is why :func:`curation_eligible` does not
    rely on the stamp at all.
    """

    validation = record.get("validation")
    if not isinstance(validation, dict):
        return False
    validator = validation.get("validator")
    if not isinstance(validator, dict):
        return False
    return validator.get("validated_digest") == record_digest(record)


def _reject_json_constant(name: str):
    """Refuse ``NaN`` / ``Infinity``, which json.loads accepts by default."""

    raise ValueError(f"non-finite JSON constant {name!r}")


def _finite_json_float(text: str) -> float:
    """Refuse float literals that overflow to infinity (for example 1e999).

    ``parse_constant`` only covers the bare constants; an overflowing literal
    otherwise becomes ``inf`` and the first canonical re-serialisation
    (``allow_nan=False``) raises out of validation instead of reporting the
    offending line as a parse failure.
    """

    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON float {text!r}")
    return value


def _parse_jsonl_line(raw: bytes) -> tuple[bool, Any]:
    """``(has_content, parsed_or_None)`` for one raw JSONL line.

    Decoding failures are a per-line finding, not an abort: ``read_text`` on
    the whole file raised ``UnicodeDecodeError`` before any record was seen,
    so one undecodable byte took down the validation of the entire corpus
    instead of being reported as the one bad line it is.
    """

    try:
        stripped = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return True, None
    if not stripped:
        return False, None
    try:
        return True, json.loads(
            stripped,
            parse_constant=_reject_json_constant,
            parse_float=_finite_json_float,
        )
    except ValueError:  # JSONDecodeError included
        return True, None


def iter_jsonl(path):
    """Yield ``(line_number, parsed_or_None)`` pairs, one line at a time.

    Streaming, so validating a scaled corpus needs memory for one record,
    never for the whole raw file plus every decoded record at once.

    Non-finite constants are a parse failure, not a value. ``json.loads``
    accepts bare ``NaN`` and ``Infinity``; letting one through means the first
    canonical re-serialisation (``allow_nan=False``) raises and takes down the
    validation of every other record in the run. Reporting the offending line
    is strictly better than aborting the corpus.
    """

    with Path(path).open("rb") as handle:
        for lineno, raw in enumerate(handle, start=1):
            has_content, parsed = _parse_jsonl_line(raw)
            if has_content:
                yield lineno, parsed


def read_jsonl(path) -> list[tuple[int, Any]]:
    """Eager form of :func:`iter_jsonl`, for small inputs and tests."""

    return list(iter_jsonl(path))


def write_jsonl(path, records) -> int:
    """Write records as JSONL. Refuses to overwrite an existing destination."""

    destination = Path(path)
    if destination.exists():
        raise ContractError(f"refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [canonical_json(record) for record in records]
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)
