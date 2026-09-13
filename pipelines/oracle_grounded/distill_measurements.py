#!/usr/bin/env python3
"""Measurement checks for the distillation contract (issue #78).

Every measurement carries a registered quantity, its canonical unit, the
meter that took it and an oracle source, its value lies in the quantity's
domain, and a meter that models rather than measures may never carry
``measured: true``, for any quantity. The no-theoretical-energy rule -- the
structural scan for energy numbers outside ``result.measurements`` -- is the
sibling ``distill_energy_claims``; ``check_envelope`` composes both.
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
    if quantity in vocab.INTEGER_QUANTITIES and not vocab.is_genuine_int(item["value"]):
        return [f"{spot}: {quantity} must be an integer, got {item['value']!r}"]
    return _quantity_domain_errors(quantity, float(item["value"]), spot)


def _modelled_meter_claim_error(item: dict[str, Any], spot: str) -> str | None:
    """A modelled meter wearing ``measured: true``, whatever it counts.

    ``measured`` is what the curation gate's NO_MEASURED_READING check trusts,
    so it must mean "an instrument took this", not "the producer said so".
    The energy rule already refuses this for joules; the registry answer is
    the same for every other quantity.
    """

    meter = item.get("meter")
    if envelope.is_enum_value(meter, vocab.MODELED_METERS) and item.get("measured") is True:
        return (
            f"{spot}: MODELLED_METER_CLAIMS_MEASURED — meter {meter!r} models "
            "rather than measures, so measured must be false"
        )
    return None


def _measurement_provenance_errors(item: dict[str, Any], spot: str) -> list[str]:
    """The meter, the oracle source and the measured flag."""

    errors: list[str] = []
    if vocab.missing_string(item.get("meter")):
        errors.append(f"{spot}: meter must be a non-empty string")
    if item.get("source") != "oracle":
        errors.append(f"{spot}: source must be 'oracle'")
    if not isinstance(item.get("measured"), bool):
        errors.append(f"{spot}: measured must be a boolean")
    if "detail" in item and not isinstance(item["detail"], dict):
        errors.append(f"{spot}: detail must be an object")
    claim_error = _modelled_meter_claim_error(item, spot)
    if claim_error is not None:
        errors.append(claim_error)
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


bind_import_twin(__name__)
