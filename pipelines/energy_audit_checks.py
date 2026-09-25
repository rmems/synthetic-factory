#!/usr/bin/env python3
"""Oracle-audit checks for ``snn-energy-routing-preferences`` records.

Split out of ``energy_check.py`` verbatim: replay the oracle
implementation identity and solver settings, audit the recorded meter
probe and configuration bounds, and bind the fingerprinted meter.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

if __package__:
    from .energy_contract import (
        MAX_REPLAY_STEPS,
        _ORACLE_TYPE_BY_IMPLEMENTATION,
        _genuine_int_at_least,
    )
else:
    from energy_contract import (
        MAX_REPLAY_STEPS,
        _ORACLE_TYPE_BY_IMPLEMENTATION,
        _genuine_int_at_least,
    )


def _check_oracle_implementation_replayable(
    record: dict[str, Any], where: str
) -> list[str]:
    """Foreign ``oracle.implementation`` must not skip allocation replay.

    Renaming the implementation off ``pipelines/energy_preferences.py:`` used
    to set solver=None and leave allocation checks as no-ops while safety and
    quality still passed against a forged stored allocation.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    implementation = oracle.get("implementation")
    if isinstance(implementation, str) and implementation.startswith(
        "pipelines/energy_preferences.py:"
    ):
        expected_type = _ORACLE_TYPE_BY_IMPLEMENTATION.get(implementation)
        if expected_type is not None and oracle.get("type") != expected_type:
            # A live meter stamped `recorded_measurement` (or a replay meter
            # stamped `measured_execution`) erases the distinction between a
            # cost measured on this run and one replayed from another run.
            return [
                f"{where}.oracle.type: ORACLE_TYPE_MISMATCH — "
                f"{implementation} must declare type {expected_type!r}, got "
                f"{oracle.get('type')!r}"
            ]
        return []
    return [
        f"{where}.oracle.implementation: ORACLE_IMPLEMENTATION_NOT_REPLAYABLE — "
        "this family's allocations are only authenticable when implementation "
        f"is under pipelines/energy_preferences.py:, got {implementation!r}"
    ]

def _replay_solver_settings(record: dict[str, Any]) -> tuple[int, int] | None:
    """``(fine_steps, coarse_steps)`` when this module's suite is replayable.

    Only records produced by this module's policy implementations can have
    their allocations recomputed; a foreign oracle's policies are not
    executable here. Malformed or out-of-range solver settings are reported
    by the oracle-audit check, so returning ``None`` for them does not open
    a bypass.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    if not _replayable_implementation(oracle.get("implementation")):
        return None
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return None
    steps = (configuration.get("fine_steps"), configuration.get("coarse_steps"))
    if not all(_bounded_step_count(step) for step in steps):
        return None
    return int(steps[0]), int(steps[1])


def _replayable_implementation(implementation: Any) -> bool:
    return isinstance(implementation, str) and implementation.startswith(
        "pipelines/energy_preferences.py:"
    )


def _bounded_step_count(steps: Any) -> bool:
    return _genuine_int_at_least(steps, 1) and steps <= MAX_REPLAY_STEPS

def _check_oracle_audit(record: dict[str, Any], where: str) -> list[str]:
    """The audit metadata behind an authoritative measured preference.

    Nothing validated ``oracle.configuration`` or ``oracle.fingerprint``, so
    deleting both left a record curation-eligible while no longer
    identifying the meter host, probe result, repeat/warmup settings, or
    solver configuration behind its measured costs — the documented audit
    trail for oracle-grounded energy.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        # The envelope reports a missing or malformed oracle block.
        return []
    errors: list[str] = []
    fingerprint = oracle.get("fingerprint")
    if not isinstance(fingerprint, dict) or not fingerprint:
        errors.append(
            f"{where}.oracle.fingerprint must identify the meter host that "
            "measured this record"
        )
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return errors + [
            f"{where}.oracle.configuration must record the meter probe and "
            "solver settings behind the measured costs"
        ]
    errors += _check_configuration_bounds(configuration, where)
    return errors + _check_meter_probe(configuration, record.get("result"), where)

def _check_meter_probe(configuration: dict[str, Any], result: Any, where: str) -> list[str]:
    """Reconcile the selected meter probe with the declared cost quantity."""

    probe = configuration.get("meter_probe")
    if not isinstance(probe, dict):
        return [
            f"{where}.oracle.configuration.meter_probe must document the "
            "probed meters and the selection"
        ]
    return _check_selected_meter(probe, where) + _check_probe_cost_fields(
        probe, result, where
    )


def _probed_meter_entries(probe: dict[str, Any]) -> list[dict[str, Any]]:
    probed = probe.get("probed")
    if not isinstance(probed, list):
        return []
    return [entry for entry in probed if isinstance(entry, dict)]


def _check_selected_meter(probe: dict[str, Any], where: str) -> list[str]:
    selected = probe.get("selected")
    if not isinstance(selected, str) or not selected.strip():
        return [
            f"{where}.oracle.configuration.meter_probe.selected must name "
            "the selected meter"
        ]
    usable = any(
        entry.get("meter") == selected and entry.get("available") is True
        for entry in _probed_meter_entries(probe)
    )
    if usable:
        return []
    return [
        f"{where}.oracle.configuration.meter_probe.selected is "
        f"{selected!r} but the probe found no such meter available — "
        "the audit must name a meter that was actually probed and "
        "usable"
    ]


def _check_probe_cost_fields(
    probe: dict[str, Any], result: Any, where: str
) -> list[str]:
    corpus_quantity = result.get("cost_quantity") if isinstance(result, dict) else None
    cost_is_energy = result.get("cost_is_energy") if isinstance(result, dict) else None
    errors: list[str] = []
    if probe.get("cost_quantity") != corpus_quantity:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_quantity is "
            f"{probe.get('cost_quantity')!r} but the corpus is denominated "
            f"in {corpus_quantity!r}"
        )
    if probe.get("cost_is_energy") != cost_is_energy:
        errors.append(
            f"{where}.oracle.configuration.meter_probe.cost_is_energy is "
            f"{probe.get('cost_is_energy')!r} but result.cost_is_energy is "
            f"{cost_is_energy!r}"
        )
    return errors

# The same domains the builder refuses to run outside of. "Any number"
# let a record declare a fractional warmup or a billion-step grid — an
# audit no execution matches, and (for the grid) a replay bound nothing
# could afford to honour.
_CONFIGURATION_BOUNDS = (
    ("repeats", 1, None),
    ("warmup", 0, None),
    ("fine_steps", 1, MAX_REPLAY_STEPS),
    ("coarse_steps", 1, MAX_REPLAY_STEPS),
)


def _over_ceiling(value: Any, ceiling: int | None) -> bool:
    if ceiling is None:
        return False
    return value > ceiling


def _bound_error(
    value: Any, bound: tuple[str, int, int | None], where: str
) -> str | None:
    _key, floor, ceiling = bound
    if not _genuine_int_at_least(value, floor) or _over_ceiling(value, ceiling):
        return _bound_message(value, bound, where)
    return None


def _bound_message(
    value: Any, bound: tuple[str, int, int | None], where: str
) -> str:
    key, floor, ceiling = bound
    upper = f" and <= {ceiling}" if ceiling is not None else ""
    return (
        f"{where}.oracle.configuration.{key} must be an integer "
        f">= {floor}{upper}, got {value!r}"
    )


def _check_configuration_bounds(configuration: dict[str, Any], where: str) -> list[str]:
    """Match declared execution bounds to the domains accepted by the builder."""

    errors: list[str] = []
    for bound in _CONFIGURATION_BOUNDS:
        problem = _bound_error(configuration.get(bound[0]), bound, where)
        if problem is not None:
            errors.append(problem)
    return errors

def _check_fingerprinted_meter(
    record: dict[str, Any], candidates: list[Any], where: str
) -> list[str]:
    meter = _declared_fingerprint_meter(record)
    if meter is None:
        return [f"{where}.oracle.fingerprint.meter must name the physical instrument"]
    return [
        f"{where}.result.candidates[{index}].cost_meter must match oracle.fingerprint.meter"
        for index, candidate in enumerate(candidates)
        if isinstance(candidate, dict) and candidate.get("cost_meter") != meter
    ]


def _declared_fingerprint_meter(record: dict[str, Any]) -> str | None:
    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    fingerprint = oracle.get("fingerprint")
    if not isinstance(fingerprint, dict):
        return None
    meter = fingerprint.get("meter")
    if not isinstance(meter, str) or not meter.strip():
        return None
    return meter
