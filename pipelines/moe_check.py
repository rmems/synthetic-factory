#!/usr/bin/env python3
"""Family validator for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: :func:`check_family` re-derives the
routing labels from the recorded context, pins the teacher identity against
the sealed Hub cards, and recomputes the reference router's layers. Scenario
checks live in ``moe_scenario_checks``, teacher-identity checks in
``moe_teacher_checks``, and measurement/recompute checks in
``moe_recompute_checks``. Every name here is re-exported from ``moe_router``
so existing call sites resolve unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .moe_layers import (
        _check_declared_trajectory_authority,
        _check_derived_routing_labels,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_top_k,
    )
    from .moe_checkpoint_checks import (
        _check_authoritative_checkpoint,
        _check_sealed_hub_cardinality,
        _check_teacher_router_logits,
    )
    from .moe_measurement_checks import (
        _check_declared_count_authority,
        _check_measurement_reconciliation,
        _check_router_measurement_meters,
    )
    from .moe_recompute_checks import (
        _check_configuration_binding,
        _check_reference_recompute,
    )
    from .moe_scenario_checks import _check_scenario_context
    from .moe_teacher_checks import (
        _check_teacher_fingerprint,
        _check_teacher_grounding,
    )
else:
    from moe_layers import (
        _check_declared_trajectory_authority,
        _check_derived_routing_labels,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_top_k,
    )
    from moe_checkpoint_checks import (
        _check_authoritative_checkpoint,
        _check_sealed_hub_cardinality,
        _check_teacher_router_logits,
    )
    from moe_measurement_checks import (
        _check_declared_count_authority,
        _check_measurement_reconciliation,
        _check_router_measurement_meters,
    )
    from moe_recompute_checks import (
        _check_configuration_binding,
        _check_reference_recompute,
    )
    from moe_scenario_checks import _check_scenario_context
    from moe_teacher_checks import (
        _check_teacher_fingerprint,
        _check_teacher_grounding,
    )


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: real routing, recorded teacher identity, sane targets."""

    errors = _check_scenario_context(record.get("scenario"), where)
    errors += oc.check_oracle_label_leak(record, where)

    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    errors += _check_teacher_fingerprint(oracle, fingerprint, where)
    errors += _check_configuration_binding(record, oracle, fingerprint, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    errors += _check_teacher_grounding(result, oracle, fingerprint, where)

    routing = result.get("routing")
    if not isinstance(routing, dict):
        return errors + [f"{where}.result.routing must be an object"]
    layers = routing.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + [f"{where}.result.routing.layers must be a non-empty array"]

    expert_count = _declared_expert_count(fingerprint)
    errors += _check_declared_count_authority(expert_count, oracle, where)
    errors += _check_declared_trajectory_authority(fingerprint, oracle, where)
    errors += _check_authoritative_checkpoint(oracle, fingerprint, where)
    errors += _check_sealed_hub_cardinality(fingerprint, oracle, result, where)
    errors += _check_routing_layers(
        layers, expert_count, _declared_top_k(fingerprint), where
    )
    errors += _check_teacher_router_logits(layers, record, where)
    errors += _check_layer_count(layers, fingerprint, where)
    errors += _check_reference_recompute(record, layers, where)
    errors += _check_derived_routing_labels(result, routing, layers, where)
    errors += _check_measurement_reconciliation(result, routing, layers, where)
    errors += _check_router_measurement_meters(result, oracle, where)
    return errors
