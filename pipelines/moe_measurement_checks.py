#!/usr/bin/env python3
"""Measurement-reconciliation checks for ``moe-router-distillation-trajectories``.

Split out of ``moe_check.py`` verbatim: the recorded router measurements must
be numeric, metered, and complete relative to what the oracle promised, and
declared counts must carry an authority the record can prove.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

def _check_measurement_reconciliation(
    result: dict[str, Any], routing: dict[str, Any], layers: list[Any], where: str
) -> list[str]:
    """Reconcile the compact targets with the routing they summarise.

    The compact targets in result.measurements describe the last layer and
    the cross-layer agreement.
    """

    last = layers[-1] if isinstance(layers[-1], dict) else {}
    expected_measurements = {
        "top1_top2_margin": last.get("top1_top2_margin"),
        "routing_entropy": last.get("routing_entropy"),
        "expert_agreement": routing.get("expert_agreement"),
    }
    readings = list(
        _numeric_router_measurements(result.get("measurements"), expected_measurements)
    )
    # A `measured: false` reading is a modelled value wearing a promised
    # router target's name — it does not satisfy the completeness check.
    reconciled = {
        quantity
        for item, quantity, _ in readings
        if oc.is_true(item.get("measured"))
    }
    errors = [
        error
        for reading in readings
        for error in _reconcile_reading(reading, layers, where)
    ]
    return errors + _missing_promised_measurements(
        expected_measurements, reconciled, where
    )

def _reconcile_reading(
    reading: tuple[dict[str, Any], str, Any],
    layers: list[Any],
    where: str,
) -> list[str]:
    """Value and attribution errors in one numeric router reading."""

    item, quantity, expected = reading
    errors: list[str] = []
    if abs(float(item["value"]) - float(expected)) > 1e-6:
        errors.append(
            f"{where}.result: measured {quantity} is {item['value']} but the "
            f"recorded routing says {expected}"
        )
    errors.extend(_attribution_errors(item, quantity, layers, where))
    return errors


def _attribution_errors(
    item: dict[str, Any], quantity: str, layers: list[Any], where: str
) -> list[str]:
    detail = item.get("detail")
    detail = detail if isinstance(detail, dict) else {}
    if quantity in ("top1_top2_margin", "routing_entropy"):
        # These targets summarise the last layer; claiming another layer
        # keeps the value right while the trajectory attribution lies.
        last = layers[-1] if isinstance(layers[-1], dict) else {}
        if detail.get("layer") != last.get("layer"):
            return [
                f"{where}.result: {quantity} is attributed to layer "
                f"{detail.get('layer')!r} but the routing's last layer is "
                f"{last.get('layer')!r}"
            ]
        return []
    if quantity != "expert_agreement":
        return []
    if detail.get("across_layers") != len(layers):
        return [
            f"{where}.result: expert_agreement claims to cover "
            f"{detail.get('across_layers')!r} layers but the routing "
            f"records {len(layers)}"
        ]
    return []


def _check_router_measurement_meters(result: dict[str, Any], oracle: Any, where: str) -> list[str]:
    """The producer stamps its own name on each compact router reading."""

    meter = oracle.get("name") if isinstance(oracle, dict) else None
    measurements = result.get("measurements")
    if not isinstance(measurements, list):
        return []
    return [
        f"{where}.result.measurements[{index}].meter: MEASUREMENT_ORACLE_MISMATCH "
        "— router measurements must name the producing oracle"
        for index, item in enumerate(measurements)
        if _meter_mismatch(item, meter)
    ]


_ROUTER_MEASUREMENT_QUANTITIES = (
    "top1_top2_margin",
    "routing_entropy",
    "expert_agreement",
)


def _meter_mismatch(item: Any, meter: Any) -> bool:
    if not isinstance(item, dict):
        return False
    if item.get("quantity") not in _ROUTER_MEASUREMENT_QUANTITIES:
        return False
    if not isinstance(meter, str) or not meter.strip():
        return True
    return item.get("meter") != meter


def _numeric_router_measurements(measurements, expected_measurements):
    """Yield numeric readings whose quantities are promised by the routing."""

    if not isinstance(measurements, list):
        return
    for item in measurements:
        reading = _router_reading(item, expected_measurements)
        if reading is not None:
            yield reading


def _router_reading(item: Any, expected_measurements):
    if not isinstance(item, dict):
        return None
    quantity = item.get("quantity")
    if not isinstance(quantity, str):
        # An unhashable quantity raised TypeError out of the dict lookup
        # and aborted validation of the whole run; the shared measurement
        # checker already reports the malformed item as a finding.
        return None
    expected = expected_measurements.get(quantity)
    if not oc.is_number(expected):
        return None
    if not oc.is_number(item.get("value")):
        return None
    return item, quantity, expected

def _missing_promised_measurements(
    expected_measurements: dict[str, Any], reconciled: set[str], where: str
) -> list[str]:
    """Every promised compact target must be present, not just the survivors.

    Validating only the readings that happen to be present would let a record
    delete ``routing_entropy`` and ``expert_agreement`` while keeping its
    digest and curation eligibility — measurement-based consumers would
    silently lose two of the three promised router targets.
    """

    return [
        f"{where}.result.measurements must record {quantity} as a measured "
        "numeric reading — the recorded routing promises it"
        for quantity, expected in sorted(expected_measurements.items())
        if oc.is_number(expected) and quantity not in reconciled
    ]

def _check_declared_count_authority(
    expert_count: int | None, oracle: Any, where: str
) -> list[str]:
    if expert_count is not None:
        return []
    if not isinstance(oracle, dict):
        return []
    if oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE:
        # Without a declared count the per-layer range check is disabled, so
        # an authoritative recording with no logits could carry expert ids
        # like [-1, 999] straight into curation.
        return [
            f"{where}.oracle.fingerprint.num_local_experts must declare a "
            "positive expert count for an authoritative router record — "
            "without it the routed expert ids cannot be range-checked"
        ]
    return []
