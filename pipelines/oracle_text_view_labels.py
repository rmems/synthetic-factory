"""The label: a short canonical answer re-derived from ``result.measured``.

Each family reads only the measured fields that define its answer, re-derives
the categorical outcome from the primary measurement where the record carries
one (spike counts for the neuron direction, reachability and delays for the mesh
outcome, weight deltas for the credit update), and checks every categorical
value against the family's closed vocabulary. ``candidate_prediction`` is never
read here: the guess is non-authoritative and cannot become a label.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_labels")
    from . import oracle_text_view_public as public
    from . import oracle_text_view_vocabulary as tv
    from .exact_json import dumps_exact_json
    from .oracle_grounded import families, sim
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_labels"
    )
    import oracle_text_view_public as public
    import oracle_text_view_vocabulary as tv
    from exact_json import dumps_exact_json
    from oracle_grounded import families, sim

__all__ = ["choice_answer_of", "choice_option", "completion_of", "label_of"]


def _require(holds: bool, what: str) -> None:
    tv.refuse_when(
        not holds, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"result.measured {what} is outside the view's label vocabulary",
    )


def _count(value: Any, what: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, what)
    return value


def _flag(value: Any, what: str) -> bool:
    _require(isinstance(value, bool), what)
    return value


def _encoder(measured: dict[str, Any]) -> dict[str, Any]:
    winner, basis = measured["winner"], measured["winner_basis"]
    _require(basis in tv.ENCODER_BASES, "winner_basis")
    _require((winner is None) == (basis == tv.ENCODER_TIE_OPTION), "winner on a tie")
    _require(winner is None or isinstance(winner, str), "winner")
    return {"winner": winner, "winner_basis": basis}


def _neuron(measured: dict[str, Any]) -> dict[str, Any]:
    before = _count(measured["before"]["spike_count"], "before.spike_count")
    after = _count(measured["after"]["spike_count"], "after.spike_count")
    increases, decreases, unchanged = tv.NEURON_DIRECTIONS
    direction = increases if after > before else decreases if after < before else unchanged
    return {"direction": direction, "spike_count_after": after, "spike_count_before": before}


def _delay(side: dict[str, Any], reached: bool, what: str) -> Any:
    delay = side["propagation_delay_ms"]
    numeric = isinstance(delay, (int, float)) and not isinstance(delay, bool)
    _require(numeric if reached else delay is None, what)
    return delay


def _mesh_outcome(reached: tuple[bool, bool], delays: tuple[Any, Any]) -> str:
    reached_before, reached_after = reached
    if not (reached_before or reached_after):
        return tv.MESH_SINK_NOT_REACHED
    if not reached_before:
        return tv.MESH_SINK_NEWLY_REACHED
    if not reached_after:
        return tv.MESH_SINK_NO_LONGER_REACHED
    shift = delays[1] - delays[0]
    if abs(shift) <= families.ROUNDING_TOL:
        return tv.MESH_SINK_REACHED_UNCHANGED
    return tv.MESH_SINK_REACHED_EARLIER if shift < 0 else tv.MESH_SINK_REACHED_LATER


def _mesh(measured: dict[str, Any]) -> dict[str, Any]:
    before, after = measured["before"], measured["after"]
    reached = (
        _flag(before["sink_reached"], "before.sink_reached"),
        _flag(after["sink_reached"], "after.sink_reached"),
    )
    delays = (
        _delay(before, reached[0], "before.propagation_delay_ms"),
        _delay(after, reached[1], "after.propagation_delay_ms"),
    )
    return {
        "outcome": _mesh_outcome(reached, delays),
        "propagation_delay_after_ms": delays[1],
        "propagation_delay_before_ms": delays[0],
        "sink_reached_after": reached[1],
        "sink_reached_before": reached[0],
    }


def _weight_direction(deltas: list[Any]) -> str:
    net = math.fsum(deltas)
    if net > sim.WEIGHT_UPDATE_EPS:
        return tv.CREDIT_POTENTIATION
    if net < -sim.WEIGHT_UPDATE_EPS:
        return tv.CREDIT_DEPRESSION
    return tv.CREDIT_NO_CHANGE


def _credit(measured: dict[str, Any]) -> dict[str, Any]:
    valence = measured["critic"]["valence"]
    _require(valence in tv.CREDIT_VALENCES, "critic.valence")
    deltas = measured["plasticity"]["weight_deltas"]
    numeric = isinstance(deltas, list) and all(
        isinstance(delta, (int, float)) and not isinstance(delta, bool) for delta in deltas
    )
    _require(numeric and bool(deltas), "plasticity.weight_deltas")
    if all(abs(delta) <= sim.WEIGHT_UPDATE_EPS for delta in deltas):
        return {
            "strongest_synapse": None,
            "valence": valence,
            "weight_direction": tv.CREDIT_NO_CHANGE,
        }
    strongest = max(range(len(deltas)), key=lambda index: (abs(deltas[index]), -index))
    return {
        "strongest_synapse": strongest,
        "valence": valence,
        "weight_direction": _weight_direction(deltas),
    }


def _memory(measured: dict[str, Any]) -> dict[str, Any]:
    response = measured["baseline"]["response"]
    _require(response in tv.MEMORY_RESPONSES, "baseline.response")
    invariant = measured["distractor_invariant"]
    _require(invariant is None or isinstance(invariant, bool), "distractor_invariant")
    return {"distractor_invariant": invariant, "response": response}


_LABELS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    tv.ENCODER_FAMILY: _encoder,
    tv.NEURON_FAMILY: _neuron,
    tv.MESH_FAMILY: _mesh,
    tv.CREDIT_FAMILY: _credit,
    tv.MEMORY_FAMILY: _memory,
}


def label_of(record: dict[str, Any]) -> dict[str, Any]:
    """The family's answer fields, re-derived from ``result.measured`` alone."""

    family = public.family_of(record)
    result = record.get("result")
    measured = result.get("measured") if isinstance(result, dict) else None
    try:
        return _LABELS[family](measured)
    except (KeyError, TypeError, IndexError) as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
            f"result.measured lacks a field the {family} label needs: {type(exc).__name__}",
        ) from exc


def completion_of(record: dict[str, Any]) -> str:
    """The label as one compact, key-sorted JSON object."""

    return dumps_exact_json(label_of(record), sort_keys=True)


def choice_option(family: str, value: Any) -> Any:
    """The multiple-choice option a label value is spelled as."""

    if family == tv.ENCODER_FAMILY:
        return tv.ENCODER_TIE_OPTION if value is None else value
    if family == tv.CREDIT_FAMILY:
        return tv.CREDIT_NO_UPDATE if value is None else f"{tv.CREDIT_SYNAPSE_PREFIX}{value}"
    return value


def choice_answer_of(record: dict[str, Any]) -> Any:
    """The correct option: the family's choice field of the measured label."""

    family = public.family_of(record)
    return choice_option(family, label_of(record)[tv.CHOICE_FIELD[family]])


if __package__:
    _expose_package_sibling(__name__)
