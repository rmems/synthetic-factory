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
    implementation = oracle.get("implementation")
    if not isinstance(implementation, str) or not implementation.startswith(
        "pipelines/energy_preferences.py:"
    ):
        return None
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return None
    fine = configuration.get("fine_steps")
    coarse = configuration.get("coarse_steps")
    for steps in (fine, coarse):
        if not _genuine_int_at_least(steps, 1) or steps > MAX_REPLAY_STEPS:
            return None
    return int(fine), int(coarse)

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

    errors: list[str] = []
    probe = configuration.get("meter_probe")
    if not isinstance(probe, dict):
        return errors + [
            f"{where}.oracle.configuration.meter_probe must document the "
            "probed meters and the selection"
        ]
    selected = probe.get("selected")
    if not isinstance(selected, str) or not selected.strip():
        errors.append(
            f"{where}.oracle.configuration.meter_probe.selected must name "
            "the selected meter"
        )
    else:
        probed = probe.get("probed")
        entries = (
            [entry for entry in probed if isinstance(entry, dict)]
            if isinstance(probed, list)
            else []
        )
        if not any(
            entry.get("meter") == selected and entry.get("available") is True
            for entry in entries
        ):
            errors.append(
                f"{where}.oracle.configuration.meter_probe.selected is "
                f"{selected!r} but the probe found no such meter available — "
                "the audit must name a meter that was actually probed and "
                "usable"
            )
    corpus_quantity = result.get("cost_quantity") if isinstance(result, dict) else None
    cost_is_energy = result.get("cost_is_energy") if isinstance(result, dict) else None
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

def _check_configuration_bounds(configuration: dict[str, Any], where: str) -> list[str]:
    """Match declared execution bounds to the domains accepted by the builder."""

    errors: list[str] = []
    # The same domains the builder refuses to run outside of. "Any number"
    # let a record declare a fractional warmup or a billion-step grid — an
    # audit no execution matches, and (for the grid) a replay bound nothing
    # could afford to honour.
    for key, floor, ceiling in (
        ("repeats", 1, None),
        ("warmup", 0, None),
        ("fine_steps", 1, MAX_REPLAY_STEPS),
        ("coarse_steps", 1, MAX_REPLAY_STEPS),
    ):
        value = configuration.get(key)
        if not _genuine_int_at_least(value, floor) or (
            ceiling is not None and value > ceiling
        ):
            bound = f" and <= {ceiling}" if ceiling is not None else ""
            errors.append(
                f"{where}.oracle.configuration.{key} must be an integer "
                f">= {floor}{bound}, got {value!r}"
            )
    return errors

def _check_fingerprinted_meter(
    record: dict[str, Any], candidates: list[Any], where: str
) -> list[str]:
    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    meter = fingerprint.get("meter") if isinstance(fingerprint, dict) else None
    if not isinstance(meter, str) or not meter.strip():
        return [f"{where}.oracle.fingerprint.meter must name the physical instrument"]
    return [
        f"{where}.result.candidates[{index}].cost_meter must match oracle.fingerprint.meter"
        for index, candidate in enumerate(candidates)
        if isinstance(candidate, dict) and candidate.get("cost_meter") != meter
    ]
