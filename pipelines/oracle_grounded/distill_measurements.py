#!/usr/bin/env python3
"""Measurement checks for the distillation contract (issue #78).

Every measurement carries a registered quantity, its canonical unit, the
meter that took it and an oracle source; a meter that models rather than
measures may never carry ``measured: true``, for any quantity; and no energy
number may be modelled rather than measured -- whether it sits in
``result.measurements`` with a modelling meter, anywhere else under ``result``
as a bare number or inside an object that identifies itself as energy, or as
the denomination of a preference with no measured energy behind it.

The energy-claim scan (D3) is structural. Energy numbers are legal in three
places only: a ``result.measurements`` entry from a measuring meter, the
preference's ``cost_value`` when a measured reading of its ``cost_quantity``
exists, and any other object that identifies energy through its own
``quantity`` / ``cost_quantity`` / ``unit`` / ``cost_unit`` fields, under the
same backing rule and never from a modelled meter. Everything else that
identifies itself as energy -- a bare number under an energy key, the numbers
in a list under one, an unbacked energy object -- is a theoretical claim.
``result.measurements`` entries, their ``detail`` included, stay with the
measurement rule (row 15 of the D3 matrix is held).
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


def _is_energy_key(key: str) -> bool:
    """True when a field name identifies an energy value: a quantity name or a unit token."""

    lowered = key.lower()
    if lowered in vocab.ENERGY_QUANTITIES:
        return True
    return any(token in vocab.ENERGY_TOKENS for token in lowered.split("_"))


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


def _energy_identity(value: dict[str, Any]) -> frozenset[str] | None:
    """The energy quantities an object claims through its own fields, or None.

    ``quantity`` / ``cost_quantity`` name the quantity outright; ``unit`` /
    ``cost_unit`` identify it through the registry (``J`` is either energy
    quantity, ``Wh`` names no registry quantity and so can never be backed).
    """

    quantity = value.get("quantity") if "quantity" in value else value.get("cost_quantity")
    if envelope.is_enum_value(quantity, vocab.ENERGY_QUANTITIES):
        return frozenset({quantity})
    unit = value.get("unit") if "unit" in value else value.get("cost_unit")
    if envelope.is_enum_value(unit, vocab.ENERGY_UNITS):
        return frozenset(q for q in vocab.ENERGY_QUANTITIES if vocab.QUANTITY_UNITS[q] == unit)
    return None


def _object_claim(value: dict[str, Any], path: str, measured: set[str]) -> str | None:
    """Why an energy-identified object with numeric content is a claim, or None.

    Metadata alone (a probe entry naming a meter and a quantity, a flag, a
    label) is never a claim: only an object that also carries a number is.
    """

    quantities = _energy_identity(value)
    if quantities is None or not any(envelope.is_number(item) for item in value.values()):
        return None
    meter = value.get("meter") if "meter" in value else value.get("cost_meter")
    if envelope.is_enum_value(meter, vocab.MODELED_METERS):
        return f"{path} (modelled meter {meter!r})"
    if "measured" in value and value["measured"] is not True:
        return f"{path} (declared unmeasured)"
    if quantities & measured:
        return None
    backing = "/".join(sorted(quantities)) or "that unit"
    return f"{path} (no measured {backing} reading backs it)"


def _energy_scan_hits(result: dict[str, Any], measured: set[str]) -> list[str]:
    """Paths of energy claims outside ``result.measurements``, bounded.

    An explicit stack keeps the walk flat, so a pathologically nested result
    is reported rather than blowing the recursion limit; at most
    ``envelope.MAX_RESERVED_KEY_HITS`` paths are collected, one already
    rejects the record. ``result.preference`` itself is the preference rule's
    business (S2); everything inside it is walked like any other value.
    """

    # ``result`` itself is an object too: ``cost_quantity`` flipped to an
    # energy quantity beside numeric content is the relabelling the energy
    # family's review reproduced, and it needs the same backing as any other.
    hits = [claim for claim in (_object_claim(result, "result", measured),) if claim is not None]
    stack = [
        (f"result.{key}", key, value)
        for key, value in reversed(list(result.items()))
        if key != "measurements"
    ]
    while stack and len(hits) < envelope.MAX_RESERVED_KEY_HITS:
        path, key, value = stack.pop()
        if isinstance(value, dict):
            claim = None if path == "result.preference" else _object_claim(value, path, measured)
            if claim is not None:
                hits.append(claim)
            stack.extend(
                (f"{path}.{child}", child, item) for child, item in reversed(list(value.items()))
            )
        elif isinstance(value, list):
            # A list keeps its key: the numbers in a list under an energy key
            # are energy numbers (R3); objects inside any list are walked (R1).
            stack.extend(
                (f"{path}[{index}]", key, item) for index, item in reversed(list(enumerate(value)))
            )
        elif envelope.is_number(value) and _is_energy_key(key):
            hits.append(path)
    return hits


def _energy_scan_errors(result: dict[str, Any], measured: set[str], where: str) -> list[str]:
    """One finding listing every energy claim the structural scan found."""

    hits = _energy_scan_hits(result, measured)
    if not hits:
        return []
    listed = ", ".join(sorted(hits))
    if len(hits) >= envelope.MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return [
        f"{where}.result: THEORETICAL_ENERGY_CLAIM — energy numbers outside "
        f"measurements at {listed} (an energy value must be carried as a "
        "measurement with a meter, or sit in an object backed by a measured "
        "reading of its quantity)"
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
    errors += _energy_scan_errors(result, measured_energy_quantities, where)
    return errors + _energy_preference_errors(result, measured_energy_quantities, where)


bind_import_twin(__name__)
