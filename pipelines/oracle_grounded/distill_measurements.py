#!/usr/bin/env python3
"""Measurement checks for the distillation contract (issue #78).

Every measurement carries a registered quantity, its canonical unit, the
meter that took it and an oracle source; and no energy number may be modelled
rather than measured -- whether it sits in ``result.measurements`` with a
modelling meter, as a bare field anywhere under ``result``, or as the
denomination of a preference with no measured energy behind it.
"""

from __future__ import annotations

from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def _mapping_entries(value: Any, path: str):
    """``(child_path, key, item)`` for one dict's entries; nothing for a non-dict."""

    if not isinstance(value, dict):
        return ()
    return ((f"{path}.{key}" if path else key, key, item) for key, item in value.items())


def _sequence_entries(value: Any, path: str):
    """``(child_path, item)`` for one list's items; nothing for a non-list."""

    if not isinstance(value, list):
        return ()
    return ((f"{path}[{index}]", item) for index, item in enumerate(value))


def walk_keys(value: Any, path: str):
    """Yield ``(path, key, value)`` for every dict entry beneath ``value``.

    Serves the bare-energy scan over ``result``. The generator-side
    reserved-key scan is the envelope's bounded walker, not this one.
    """

    for child, key, item in _mapping_entries(value, path):
        yield child, key, item
        yield from walk_keys(item, child)
    for child, item in _sequence_entries(value, path):
        yield from walk_keys(item, child)


def _quantity_domain_errors(quantity: str, value: float, spot: str) -> list[str]:
    """The domain a quantity's value must lie in, beyond being finite."""

    if quantity in vocab.NON_NEGATIVE_QUANTITIES and value < 0.0:
        return [f"{spot}: {quantity} cannot be negative, got {value}"]
    if quantity in vocab.UNIT_INTERVAL_QUANTITIES and not 0.0 <= value <= 1.0:
        return [f"{spot}: {quantity} must lie in [0, 1], got {value}"]
    return []


def _measurement_value_errors(item: dict[str, Any], quantity: str, spot: str) -> list[str]:
    """A finite value inside the quantity's domain."""

    if not envelope.is_number(item.get("value")):
        return [f"{spot}: value must be a finite number"]
    return _quantity_domain_errors(quantity, float(item["value"]), spot)


def _measurement_provenance_errors(item: dict[str, Any], spot: str) -> list[str]:
    """The meter, the oracle source and the measured flag."""

    errors: list[str] = []
    if vocab.missing_string(item.get("meter")):
        errors.append(f"{spot}: meter must be a non-empty string")
    if item.get("source") != "oracle":
        errors.append(f"{spot}: source must be 'oracle'")
    if not isinstance(item.get("measured"), bool):
        errors.append(f"{spot}: measured must be a boolean")
    return errors


def _check_measurement_item(item: Any, spot: str) -> list[str]:
    """One measurement's quantity, unit, meter and provenance."""

    if not isinstance(item, dict):
        return [f"{spot}: measurement must be an object"]
    quantity = item.get("quantity")
    if not envelope.is_enum_value(quantity, vocab.QUANTITY_UNITS):
        return [f"{spot}: unknown quantity {quantity!r}"]
    errors = _measurement_value_errors(item, quantity, spot)
    expected_unit = vocab.QUANTITY_UNITS[quantity]
    if item.get("unit") != expected_unit:
        errors.append(
            f"{spot}: {quantity} must declare unit {expected_unit!r}, "
            f"got {item.get('unit')!r}"
        )
    return errors + _measurement_provenance_errors(item, spot)


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
    if lowered in vocab.ENERGY_QUANTITIES:
        return True
    return any(hint in lowered for hint in ENERGY_KEY_HINTS)


def _energy_claim_error(item: dict[str, Any], quantity: str, spot: str) -> str | None:
    """Why this energy reading is a theoretical claim, or None when measured."""

    meter = item.get("meter")
    if envelope.is_enum_value(meter, vocab.MODELED_METERS) or item.get("measured") is not True:
        return (
            f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} came from "
            f"meter {meter!r}; energy must be physically measured"
        )
    if not envelope.is_enum_value(meter, vocab.MEASURED_ENERGY_METERS):
        return (
            f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} needs a meter in "
            f"{sorted(vocab.MEASURED_ENERGY_METERS)}, got {meter!r}"
        )
    return None


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
        if not envelope.is_enum_value(quantity, vocab.ENERGY_QUANTITIES):
            continue
        error = _energy_claim_error(item, quantity, f"{where}.result.measurements[{index}]")
        if error is not None:
            errors.append(error)
            continue
        measured_energy_quantities.add(quantity)
    return errors, measured_energy_quantities


def _is_bare_energy_field(key: str, value: Any) -> bool:
    """A number under an energy-sounding name, outside ``measurements``.

    Only a number can be an energy value. A boolean is a flag
    (`cost_is_energy`, `measures_energy`) and a string names a quantity.
    """

    return key != "measurements" and envelope.is_number(value) and _is_energy_key(key)


def _bare_energy_field_errors(result: dict[str, Any]) -> list[str]:
    """A bare energy number anywhere under ``result`` is an energy claim too.

    Without this, ``result["energy_j"] = 1e-7`` sails past the measurement
    checks because it never appears in ``result.measurements`` at all.
    """

    return [
        f"{path}: THEORETICAL_ENERGY_CLAIM — an energy value must be carried "
        "as a measurement with a meter, not as a bare field"
        for path, key, value in walk_keys(result, "result")
        if _is_bare_energy_field(key, value)
    ]


def _energy_preference_errors(
    result: dict[str, Any], measured_energy_quantities: set[str], where: str
) -> list[str]:
    """A preference denominated in energy needs a measured energy reading."""

    preference = result.get("preference")
    if not isinstance(preference, dict):
        return []
    cost_quantity = preference.get("cost_quantity")
    if (
        envelope.is_enum_value(cost_quantity, vocab.ENERGY_QUANTITIES)
        and cost_quantity not in measured_energy_quantities
    ):
        return [
            f"{where}.result.preference: THEORETICAL_ENERGY_CLAIM — preference "
            f"is denominated in {cost_quantity!r} with no measured energy "
            f"measurement behind it"
        ]
    return []


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
    return errors + _energy_preference_errors(result, measured_energy_quantities, where)


bind_import_twin(__name__)
