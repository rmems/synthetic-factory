#!/usr/bin/env python3
"""Per-layer field checks for ``moe-router-distillation-trajectories``.

Split out of ``moe_layers.py`` verbatim: every check that validates one
routing layer's own fields — index order (``_LayerOrder`` /
``_check_layer_index``), expert ids, logit agreement, margin and entropy, and
the ``_check_layer_signals`` per-layer umbrella. Record-level and summary
checks stay in ``moe_layers``.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402

if __package__:
    from .moe_featurizer import RECOMPUTE_TOLERANCE, entropy_nats, softmax
else:
    from moe_featurizer import RECOMPUTE_TOLERANCE, entropy_nats, softmax


class _LayerOrder:
    """Running layer-index state carried across the recorded layers."""

    def __init__(self) -> None:
        self.seen: set[int] = set()
        self.previous: int | None = None




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


def _genuine_expert_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _invalid_expert_entries(experts: list[Any]) -> list[Any]:
    return [expert for expert in experts if not _genuine_expert_id(expert)]


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
    return _expert_id_problems(experts, spot, expert_count)


def _expert_id_problems(
    experts: list[Any], spot: str, expert_count: int | None
) -> list[str]:
    """Validity, distinctness, and range of the routed expert ids."""

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
    return _logits_order_problem(layer, logits, spot)


def _logits_order_problem(
    layer: dict[str, Any], logits: list[Any], spot: str
) -> list[str]:
    """The recorded top-k order checked against the logits, when both exist."""

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
    if not _usable_logit_vector(logits):
        return None
    return [float(value) for value in logits]


def _usable_logit_vector(logits: Any) -> bool:
    if not isinstance(logits, list) or len(logits) < 2:
        return False
    return all(oc.is_number(value) for value in logits)


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
    if not oc.is_number(routing_entropy):
        return [f"{spot}.routing_entropy must be a non-negative number"]
    if float(routing_entropy) < 0.0:
        return [f"{spot}.routing_entropy must be a non-negative number"]
    if exposed_logits is not None:
        return _check_recomputed_entropy(routing_entropy, exposed_logits, spot)
    # No logits to recompute from, so fall back to bounding the entropy
    # by ln(num_experts) using the recorded expert count. Kept separate
    # from `expert_count` above so one layer's logit width does not
    # become the id range every later layer is checked against.
    support = _entropy_support(layer, expert_count)
    if support and float(routing_entropy) > math.log(support) + 1e-6:
        return [
            f"{spot}.routing_entropy exceeds ln({support}) — not a "
            "distribution over these experts"
        ]
    return []


def _entropy_support(layer: dict[str, Any], expert_count: int | None) -> int | None:
    logits = layer.get("router_logits")
    if isinstance(logits, list) and logits:
        return len(logits)
    return expert_count


def _check_recomputed_entropy(
    routing_entropy: Any, exposed_logits: list[float], spot: str
) -> list[str]:
    recomputed_entropy = entropy_nats(softmax(exposed_logits))
    if abs(float(routing_entropy) - recomputed_entropy) > RECOMPUTE_TOLERANCE:
        return [
            f"{spot}.routing_entropy is {routing_entropy} but the "
            f"recorded router_logits give {round(recomputed_entropy, 6)}"
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


