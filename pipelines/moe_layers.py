#!/usr/bin/env python3
"""Routing-layer shapes for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: the :class:`LayerRouting` /
:class:`RouterObservation` record shapes, the declared-cardinality readers, and
the record-level checks (summary labels, routing-layer walk, declared
trajectory authority, layer count, recompute mismatches, modal/top expert
agreement). The per-layer field checks live in ``moe_layer_fields``. Every
name here is re-exported from ``moe_router`` so existing call sites resolve
unchanged.
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


if __package__:
    from .moe_featurizer import RECOMPUTE_TOLERANCE
    from .moe_layer_fields import (
        _check_layer_index,
        _check_layer_signals,
        _genuine_expert_id,
        _LayerOrder,
    )
else:
    from moe_featurizer import RECOMPUTE_TOLERANCE
    from moe_layer_fields import (
        _check_layer_index,
        _check_layer_signals,
        _genuine_expert_id,
        _LayerOrder,
    )


@dataclass(frozen=True)
class LayerRouting:
    """One layer's routing decision as the router actually computed it."""

    layer: int
    top_k_experts: tuple[int, ...]
    router_logits: tuple[float, ...] | None
    top1_top2_margin: float
    routing_entropy: float


@dataclass(frozen=True)
class RouterObservation:
    """Compact distillation targets for one context."""

    layers: tuple[LayerRouting, ...]
    top1_expert: int
    expert_agreement: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "layers": [
                {
                    "layer": layer.layer,
                    "top_k_experts": list(layer.top_k_experts),
                    "router_logits": (
                        list(layer.router_logits)
                        if layer.router_logits is not None
                        else None
                    ),
                    "top1_top2_margin": layer.top1_top2_margin,
                    "routing_entropy": layer.routing_entropy,
                }
                for layer in self.layers
            ],
            "top1_expert": self.top1_expert,
            "expert_agreement": self.expert_agreement,
        }



def _declared_positive_int(fingerprint: Any, field: str) -> int | None:
    """A positive-integer fingerprint field, when it is declared as one."""

    if not isinstance(fingerprint, dict):
        return None
    declared = fingerprint.get(field)
    if oc.is_genuine_int(declared) and declared > 0:
        return declared
    return None


def _declared_expert_count(fingerprint: Any) -> int | None:
    """The expert count the oracle fingerprint declares, when it declares one."""

    return _declared_positive_int(fingerprint, "num_local_experts")


def _declared_top_k(fingerprint: Any) -> int | None:
    """The per-token top-k width the fingerprint declares, when it does."""

    return _declared_positive_int(fingerprint, "num_experts_per_tok")


def _declared_layer_count(fingerprint: Any) -> int | None:
    """The routed layer count the fingerprint declares, when it does."""

    return _declared_positive_int(fingerprint, "num_layers")


def _check_expert_agreement_range(routing: dict[str, Any], where: str) -> list[str]:
    """expert_agreement is a fraction, so it lives in [0, 1]."""

    agreement = routing.get("expert_agreement")
    if not oc.is_number(agreement) or not 0.0 <= float(agreement) <= 1.0:
        return [f"{where}.result.routing.expert_agreement must be in [0, 1]"]
    return []


def _top_expert_of(layer: Any) -> int | None:
    """One layer's top-1 expert id, when a usable one was recorded."""

    if not isinstance(layer, dict):
        return None
    experts = layer.get("top_k_experts")
    if not isinstance(experts, list) or not experts:
        return None
    top = experts[0]
    return top if _genuine_expert_id(top) else None


def _layer_top_experts(layers: list[Any]) -> list[int]:
    """The top-1 expert of every layer that recorded a usable one."""

    return [
        top for top in (_top_expert_of(layer) for layer in layers)
        if top is not None
    ]


def _check_modal_agreement(
    result: dict[str, Any], routing: dict[str, Any], tops: list[int], where: str
) -> list[str]:
    """Compare the recorded label and agreement against the modal top-1 expert."""

    errors: list[str] = []
    try:
        modal, count = Counter(tops).most_common(1)[0]
    except (TypeError, ValueError):
        errors.append(f"{where}.result.routing: cannot compute top1_expert from invalid layer data")
        modal, count = None, 0
    if modal is None:
        return errors
    if result.get("top1_expert") != modal:
        errors.append(
            f"{where}.result.top1_expert is {result.get('top1_expert')!r} but the "
            f"recorded layers route to {modal!r}"
        )
    if routing.get("top1_expert") != modal:
        errors.append(
            f"{where}.result.routing.top1_expert disagrees with its own layers"
        )
    agreement = routing.get("expert_agreement")
    expected_agreement = count / len(tops)
    if oc.is_number(agreement) and abs(float(agreement) - expected_agreement) > 1e-6:
        errors.append(
            f"{where}.result.routing.expert_agreement is {agreement} but the "
            f"recorded layers agree {expected_agreement:.6f} of the time"
        )
    return errors


def _check_derived_routing_labels(
    result: dict[str, Any], routing: dict[str, Any], layers: list[Any], where: str
) -> list[str]:
    """Recompute the distillation label and agreement from the recorded layers.

    The distillation label and the summary statistics are derived, not
    independent facts. Recompute them from the layers the oracle recorded, so
    a fabricated top-1 expert cannot be trained on.
    """

    errors = _check_expert_agreement_range(routing, where)
    errors += _check_summary_label_types(result, routing, where)
    tops = _layer_top_experts(layers)
    if len(tops) == len(layers) and tops:
        errors += _check_modal_agreement(result, routing, tops, where)
    return errors


def _check_summary_label_types(
    result: dict[str, Any], routing: dict[str, Any], where: str
) -> list[str]:
    """Both summary labels must be genuine integers, never booleans.

    When the modal expert is 0 or 1, a JSON boolean passes the modal equality
    checks (``False == 0`` and ``True == 1``), yet ``router_baseline``'s
    ``_genuine_int`` rejects it and silently drops the sample — so a record
    that validates cleanly here could still skew the baseline and the SNN
    escalation verdict by vanishing from it.
    """

    return [
        f"{where}.{field} must be a genuine integer expert id, got {value!r}"
        for field, value in (
            ("result.top1_expert", result.get("top1_expert")),
            ("result.routing.top1_expert", routing.get("top1_expert")),
        )
        if not isinstance(value, int) or isinstance(value, bool)
    ]


def _check_routing_layers(
    layers: list[Any], expert_count: int | None, top_k: int | None, where: str
) -> list[str]:
    errors: list[str] = []
    order = _LayerOrder()
    for index, layer in enumerate(layers):
        spot = f"{where}.result.routing.layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{spot} must be an object")
            continue
        errors += _check_layer_index(layer, spot, order)
        errors += _check_layer_signals(layer, spot, expert_count, top_k)
    return errors


def _check_declared_trajectory_authority(
    fingerprint: Any, oracle: Any, where: str
) -> list[str]:
    """An authoritative router must declare its top-k width and layer count.

    Both equality checks are conditional on the declaration being present, so
    deleting ``num_experts_per_tok`` freed every layer to widen its top-k and
    deleting ``num_layers`` let a contiguous suffix vanish — while the record
    stayed validation-clean and curation-eligible.
    """

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        return []
    return [
        f"{where}.oracle.fingerprint.{field} must declare a positive value "
        f"for an authoritative router record — without it {consequence}"
        for field, declared, consequence in (
            (
                "num_experts_per_tok",
                _declared_top_k(fingerprint),
                "the recorded top-k width cannot be checked",
            ),
            (
                "num_layers",
                _declared_layer_count(fingerprint),
                "a dropped layer suffix cannot be detected",
            ),
        )
        if declared is None
    ]


def _check_layer_count(
    layers: list[Any], fingerprint: Any, where: str
) -> list[str]:
    """The recorded trajectory length against the declared layer count.

    Contiguity alone still lets a suffix vanish: a record keeping layers
    [0, 1] of a four-layer teacher looks ordered while ``router_baseline``
    reads a mid-network decision as the last-layer target.
    """

    declared = _declared_layer_count(fingerprint)
    if declared is not None and len(layers) != declared:
        return [
            f"{where}.result.routing.layers has {len(layers)} layers but the "
            f"oracle fingerprint declares num_layers {declared} — a dropped "
            "suffix would change the last-layer target"
        ]
    return []


def _recomputed_layer_mismatches(
    layer: dict[str, Any], actual: LayerRouting, spot: str
) -> list[str]:
    errors: list[str] = []
    if layer.get("top_k_experts") != list(actual.top_k_experts):
        errors.append(
            f"{spot}.top_k_experts is {layer.get('top_k_experts')!r} but "
            f"the reference router computes {list(actual.top_k_experts)!r}"
        )
        return errors
    for field, value in (
        ("top1_top2_margin", actual.top1_top2_margin),
        ("routing_entropy", actual.routing_entropy),
    ):
        recorded = layer.get(field)
        if not oc.is_number(recorded) or abs(float(recorded) - value) > RECOMPUTE_TOLERANCE:
            errors.append(
                f"{spot}.{field} is {recorded!r} but the reference router "
                f"computes {value!r}"
            )
            break
    return errors
