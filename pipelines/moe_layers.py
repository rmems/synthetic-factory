#!/usr/bin/env python3
"""Routing-layer shapes for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: the :class:`LayerRouting` /
:class:`RouterObservation` record shapes, the declared-cardinality readers, and
the per-layer consistency checks (index order, expert validity, logits
agreement, margin, entropy, modal/top expert agreement). Every name here is
re-exported from ``moe_router`` so existing call sites resolve unchanged.
"""

from __future__ import annotations

import math
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
    from .moe_featurizer import (
        RECOMPUTE_TOLERANCE,
        entropy_nats,
        softmax,
    )
else:
    from moe_featurizer import (
        RECOMPUTE_TOLERANCE,
        entropy_nats,
        softmax,
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



class _LayerOrder:
    """Running layer-index state carried across the recorded layers."""

    def __init__(self) -> None:
        self.seen: set[int] = set()
        self.previous: int | None = None


def _declared_positive_int(fingerprint: Any, field: str) -> int | None:
    """A positive-integer fingerprint field, when it is declared as one."""

    if not isinstance(fingerprint, dict):
        return None
    declared = fingerprint.get(field)
    if isinstance(declared, int) and not isinstance(declared, bool) and declared > 0:
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


def _check_layer_index(layer: dict[str, Any], spot: str, order: _LayerOrder) -> list[str]:
    """The layer index: an integer, unseen, and in model order."""

    errors: list[str] = []
    layer_index = layer.get("layer")
    if not isinstance(layer_index, int) or isinstance(layer_index, bool):
        errors.append(f"{spot}.layer must be an integer")
    elif layer_index in order.seen:
        errors.append(f"{spot}.layer {layer_index} is duplicated")
    else:
        # router_baseline._target_label reads the last-layer decision as
        # `layers[-1]`. Unique-but-unordered indices such as [3, 0, 1, 2]
        # would silently make layer 2 the training target while the record
        # advertises layer 3 — and a merely increasing sequence such as
        # [0, 2] would let interior layers vanish while still looking
        # ordered, so the trajectory must be contiguous from zero.
        expected_index = 0 if order.previous is None else order.previous + 1
        if layer_index != expected_index:
            errors.append(
                f"{spot}.layer {layer_index} where {expected_index} was "
                "expected; routing layers must be recorded contiguously "
                "from 0 in model order so the last entry is the last layer"
            )
        order.previous = layer_index
        order.seen.add(layer_index)
    return errors


def _invalid_expert_entries(experts: list[Any]) -> list[Any]:
    return [
        expert
        for expert in experts
        if not isinstance(expert, int) or isinstance(expert, bool)
    ]


def _check_layer_experts(
    layer: dict[str, Any], spot: str, expert_count: int | None,
    top_k: int | None = None,
) -> list[str]:
    """The routed expert ids: the declared width, distinct, and in range."""

    experts = layer.get("top_k_experts")
    if not isinstance(experts, list) or len(experts) < 2:
        return [f"{spot}.top_k_experts must list at least the top two"]
    if top_k is not None and len(experts) != top_k:
        # A wider (or narrower) list than the teacher's declared top-k is a
        # distillation target that contradicts the recorded configuration.
        return [
            f"{spot}.top_k_experts lists {len(experts)} experts but the "
            f"oracle fingerprint declares num_experts_per_tok {top_k}"
        ]
    invalid_experts = _invalid_expert_entries(experts)
    if invalid_experts:
        return [f"{spot}.top_k_experts contains invalid entries: {invalid_experts}"]
    if len(set(experts)) != len(experts):
        return [f"{spot}.top_k_experts must not repeat an expert"]
    if expert_count is not None and not all(
        0 <= value < expert_count for value in experts
    ):
        # Checked independently of router_logits, because a recorded
        # teacher may legitimately omit logits and would otherwise be
        # free to record ids like [-1, 999] as authoritative routing
        # labels.
        return [
            f"{spot}.top_k_experts must lie in [0, {expert_count}) — the "
            "expert count the oracle fingerprint declares"
        ]
    return []


def _experts_index_logits(experts: list[Any], size: int) -> bool:
    """True when every expert id is a genuine int indexing the logit array."""

    return all(
        isinstance(expert, int)
        and not isinstance(expert, bool)
        and 0 <= expert < size
        for expert in experts
    )


def _is_top_of_logits(experts: list[int], logits: list[Any]) -> bool:
    """True when the experts carry, position for position, the top values."""

    recorded_values = [float(logits[expert]) for expert in experts]
    top_values = sorted(
        (float(value) for value in logits), reverse=True
    )[: len(experts)]
    return recorded_values == top_values


def _check_layer_logits(
    layer: dict[str, Any], spot: str, expert_count: int | None = None
) -> list[str]:
    """Router logits, and the expert order they imply.

    The recorded top-k must carry, position for position, the largest logit
    values — but *which* expert wins an exact tie is not checked. The stored
    logits are serialised at six decimal places, so a teacher that ordered by
    full precision can legitimately disagree with an id-ordered tie-break
    over values that round together; demanding one canonical tie-break would
    reject honest records. An expert with a strictly smaller logit still
    cannot appear.
    """

    logits = layer.get("router_logits")
    if logits is None:
        return []
    if not isinstance(logits, list) or not all(
        oc.is_number(value) for value in logits
    ):
        return [f"{spot}.router_logits must be an array of numbers"]
    if expert_count is not None and len(logits) != expert_count:
        # A truncated array that still contains the selected ids passes the
        # ordering check below, but it turns the promised full teacher
        # distribution into a partial one — and both the entropy and the
        # logit distillation targets change with it.
        return [
            f"{spot}.router_logits lists {len(logits)} values but the oracle "
            f"fingerprint declares num_local_experts {expert_count}"
        ]
    experts = layer.get("top_k_experts")
    if not isinstance(experts, list) or not experts:
        return []
    if not _experts_index_logits(experts, len(logits)) or not _is_top_of_logits(
        experts, logits
    ):
        return [f"{spot}.top_k_experts disagrees with router_logits ordering"]
    return []


def _exposed_logits(layer: dict[str, Any]) -> list[float] | None:
    """The logits when they are usable for recomputation, else None.

    Both layer summaries are exact functions of the logits, so when the
    logits are exposed they are recomputed rather than range-checked. A range
    check alone let any non-negative margin and any entropy below
    ln(num_experts) stand in for the real ones — and both are
    distillation targets.
    """

    logits = layer.get("router_logits")
    if (
        isinstance(logits, list)
        and len(logits) >= 2
        and all(oc.is_number(value) for value in logits)
    ):
        return [float(value) for value in logits]
    return None


def _check_layer_margin(
    layer: dict[str, Any], spot: str, exposed_logits: list[float] | None
) -> list[str]:
    """top1_top2_margin, recomputed from the logits when they are recorded."""

    margin = layer.get("top1_top2_margin")
    if not oc.is_number(margin) or float(margin) < 0.0:
        return [f"{spot}.top1_top2_margin must be a non-negative number"]
    if exposed_logits is None:
        return []
    ordered = sorted(exposed_logits, reverse=True)
    recomputed_margin = ordered[0] - ordered[1]
    # The stored logits are themselves rounded to 6 places, so the
    # recomputation carries that rounding; the tolerance covers it and
    # nothing wider.
    if abs(float(margin) - recomputed_margin) > RECOMPUTE_TOLERANCE:
        return [
            f"{spot}.top1_top2_margin is {margin} but the recorded "
            f"router_logits give {round(recomputed_margin, 6)}"
        ]
    return []


def _check_layer_entropy(
    layer: dict[str, Any],
    spot: str,
    exposed_logits: list[float] | None,
    expert_count: int | None,
) -> list[str]:
    """routing_entropy, recomputed from the logits or bounded by ln(support)."""

    routing_entropy = layer.get("routing_entropy")
    if not oc.is_number(routing_entropy) or float(routing_entropy) < 0.0:
        return [f"{spot}.routing_entropy must be a non-negative number"]
    if exposed_logits is not None:
        recomputed_entropy = entropy_nats(softmax(exposed_logits))
        if abs(float(routing_entropy) - recomputed_entropy) > RECOMPUTE_TOLERANCE:
            return [
                f"{spot}.routing_entropy is {routing_entropy} but the "
                f"recorded router_logits give {round(recomputed_entropy, 6)}"
            ]
        return []
    # No logits to recompute from, so fall back to bounding the entropy
    # by ln(num_experts) using the recorded expert count. Kept separate
    # from `expert_count` above so one layer's logit width does not
    # become the id range every later layer is checked against.
    logits = layer.get("router_logits")
    support = len(logits) if isinstance(logits, list) and logits else expert_count
    if support and float(routing_entropy) > math.log(support) + 1e-6:
        return [
            f"{spot}.routing_entropy exceeds ln({support}) — not a "
            "distribution over these experts"
        ]
    return []


def _check_layer_signals(
    layer: dict[str, Any], spot: str, expert_count: int | None,
    top_k: int | None = None,
) -> list[str]:
    """The routed experts, their logits, and the summaries derived from them."""

    exposed_logits = _exposed_logits(layer)
    return (
        _check_layer_experts(layer, spot, expert_count, top_k)
        + _check_layer_logits(layer, spot, expert_count)
        + _check_layer_margin(layer, spot, exposed_logits)
        + _check_layer_entropy(layer, spot, exposed_logits, expert_count)
    )


def _check_expert_agreement_range(routing: dict[str, Any], where: str) -> list[str]:
    """expert_agreement is a fraction, so it lives in [0, 1]."""

    agreement = routing.get("expert_agreement")
    if not oc.is_number(agreement) or not 0.0 <= float(agreement) <= 1.0:
        return [f"{where}.result.routing.expert_agreement must be in [0, 1]"]
    return []


def _layer_top_experts(layers: list[Any]) -> list[int]:
    """The top-1 expert of every layer that recorded a usable one."""

    return [
        layer["top_k_experts"][0]
        for layer in layers
        if isinstance(layer, dict)
        and isinstance(layer.get("top_k_experts"), list)
        and layer["top_k_experts"]
        and isinstance(layer["top_k_experts"][0], int)
        and not isinstance(layer["top_k_experts"][0], bool)
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
