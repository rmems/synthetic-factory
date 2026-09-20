#!/usr/bin/env python3
"""Oracle-identity checks for ``neuromorphic-fault-recovery`` records.

Split out of ``fault_check.py`` verbatim: bind the recorded oracle name,
implementation string, simulator type, and configuration to this family so a
renamed or foreign oracle cannot carry an authoritative verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import envelope  # noqa: E402

if __package__:
    from .fault_types import (
        DEFAULT_SYSTEM,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        OUTCOME_PRECEDENCE,
    )
else:
    from fault_types import (
        DEFAULT_SYSTEM,
        ORACLE_IMPLEMENTATION,
        ORACLE_NAME,
        OUTCOME_PRECEDENCE,
    )


def _is_relay_simulator_oracle(oracle: Any) -> bool:
    """The oracle block this binding governs, or False for foreign oracles."""

    if not isinstance(oracle, dict) or oracle.get("name") != ORACLE_NAME:
        return False
    return (
        oracle.get("implementation") == ORACLE_IMPLEMENTATION
        or oracle.get("type") == "deterministic_simulator"
    )


def _configuration_errors(
    configuration: dict[str, Any], effective_system: dict[str, Any], where: str
) -> list[str]:
    """Configuration entries that must match the run that produced the label."""

    errors: list[str] = []
    # Strict JSON equality: Python's == conflates true with 1.0, so a record
    # could replace a numeric setting with a boolean, recompute its digest,
    # and still claim the oracle block describes the replayed configuration.
    if not envelope.strict_json_equal(configuration.get("system"), effective_system):
        errors.append(
            f"{where}.oracle.configuration.system does not match "
            "scenario.system — the oracle block must describe the "
            "configuration that produced its label"
        )
    if configuration.get("precedence") != list(OUTCOME_PRECEDENCE):
        errors.append(
            f"{where}.oracle.configuration.precedence must be the canonical "
            f"outcome precedence {list(OUTCOME_PRECEDENCE)}"
        )
    return errors


def _check_oracle_configuration_binding(
    record: dict[str, Any], where: str
) -> list[str]:
    """The oracle block must describe the configuration behind its label.

    The replay reads only ``scenario.system``, so a rewritten or deleted
    ``oracle.configuration.system`` stayed validation-clean while the
    authoritative oracle block no longer described the run that produced its
    label — breaking reproducibility and provenance audits.
    """

    oracle = record.get("oracle")
    if not _is_relay_simulator_oracle(oracle):
        return []
    scenario = record.get("scenario")
    recorded_system = scenario.get("system", {}) if isinstance(scenario, dict) else {}
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict):
        return [
            f"{where}.oracle.configuration must record the simulator's "
            "system and precedence"
        ]
    # The recorded system is the *effective* one: the oracle fills every key
    # the scenario omits from DEFAULT_SYSTEM before running, so the binding
    # compares against that merged configuration, not the partial input.
    return _configuration_errors(
        configuration, {**DEFAULT_SYSTEM, **recorded_system}, where
    )



def _canonical_oracle_name(name: str) -> str:
    """Collapse orthography that still *looks* like ``ORACLE_NAME``.

    Used only to detect near-miss escapes. Acceptance still requires the exact
    ``ORACLE_NAME`` string — we never strip-and-accept a forged name.
    """

    # Zero-width / BOM format chars survive ``str.strip``; drop them explicitly.
    for noise in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        name = name.replace(noise, "")
    # Unicode whitespace (ASCII space, NBSP, thin space, …) via strip.
    collapsed = name.strip().replace("_", "-").casefold()
    return collapsed


def _oracle_name_is_near_miss(name: Any) -> bool:
    """True when ``name`` is not exact ``ORACLE_NAME`` but canonicalizes to it."""

    if not isinstance(name, str) or name == ORACLE_NAME:
        return False
    return _canonical_oracle_name(name) == _canonical_oracle_name(ORACLE_NAME)


def _check_oracle_name_identity(
    record: dict[str, Any], where: str
) -> list[str]:
    """``oracle.name`` must be exact ``ORACLE_NAME`` for this family.

    Trailing/leading space, NBSP, underscore rename, case variants, and foreign
    names used to early-return out of type-binding + re-sim (exact
    ``== ORACLE_NAME``), leaving a forged ``hardware_replay`` continue
    curation-eligible (FAULT-NAME-IDENTITY-ESCAPE). Reject any non-exact name;
    do not normalize-and-accept.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    name = oracle.get("name")
    if name == ORACLE_NAME:
        return []
    if _oracle_name_is_near_miss(name):
        detail = (
            f"near-miss name {name!r} must be exact {ORACLE_NAME!r} "
            "(whitespace / underscore / case variants are not accepted)"
        )
    else:
        detail = (
            f"foreign name {name!r} must be exact {ORACLE_NAME!r} "
            "(this family does not accept other oracle names)"
        )
    return [f"{where}.oracle.name: ORACLE_NAME_MISMATCH — {detail}"]


def _check_oracle_implementation_identity(
    record: dict[str, Any], where: str
) -> list[str]:
    """``relay-reflex-sim`` must declare the exact in-process implementation.

    Trailing whitespace or a truncated class name used to miss both the type
    binder and the re-sim gate (exact ``== ORACLE_IMPLEMENTATION``), leaving a
    forged ``hardware_replay`` continue curation-eligible.
    """

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    if oracle.get("name") != ORACLE_NAME:
        return []
    implementation = oracle.get("implementation")
    if implementation == ORACLE_IMPLEMENTATION:
        return []
    return [
        f"{where}.oracle.implementation: ORACLE_IMPLEMENTATION_MISMATCH — "
        f"{ORACLE_NAME} must declare implementation {ORACLE_IMPLEMENTATION!r}, "
        f"got {implementation!r}"
    ]


def _check_simulator_type_binding(record: dict[str, Any], where: str) -> list[str]:
    """Our in-process simulator must declare deterministic_simulator type."""

    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return []
    if oracle.get("name") != ORACLE_NAME:
        return []
    if oracle.get("implementation") != ORACLE_IMPLEMENTATION:
        return []
    if oracle.get("type") == "deterministic_simulator":
        return []
    return [
        f"{where}.oracle.type: ORACLE_TYPE_MISMATCH — {ORACLE_IMPLEMENTATION} "
        f"must declare type deterministic_simulator, got {oracle.get('type')!r}"
    ]

