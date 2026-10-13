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
from collections.abc import Callable
from typing import Any

from . import public
from . import vocabulary as tv
from ._contract import bind_import_twin, dumps_exact_json, families, sim

__all__ = ["choice_answer_of", "choice_option", "completion_of", "label_of"]


def _require(holds: bool, what: str) -> None:
    tv.refuse_when(
        not holds, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"result.measured {what} is outside the view's label vocabulary",
    )


def _count(value: Any, what: str) -> int:
    _require(public.is_integer(value) and value >= 0, what)
    return value


def _flag(value: Any, what: str) -> bool:
    _require(isinstance(value, bool), what)
    return value


def _numbers(values: Any) -> bool:
    if not isinstance(values, list) or not values:
        return False
    return all(public.is_number(value) for value in values)


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
    _require(public.is_number(delay) if reached else delay is None, what)
    return delay


_REACHABILITY_OUTCOMES = {
    (False, False): tv.MESH_SINK_NOT_REACHED,
    (False, True): tv.MESH_SINK_NEWLY_REACHED,
    (True, False): tv.MESH_SINK_NO_LONGER_REACHED,
}


def _delay_outcome(shift: float) -> str:
    if abs(shift) <= families.ROUNDING_TOL:
        return tv.MESH_SINK_REACHED_UNCHANGED
    return tv.MESH_SINK_REACHED_EARLIER if shift < 0 else tv.MESH_SINK_REACHED_LATER


def _mesh_outcome(reached: tuple[bool, bool], delays: tuple[Any, Any]) -> str:
    outcome = _REACHABILITY_OUTCOMES.get(reached)
    return outcome if outcome is not None else _delay_outcome(delays[1] - delays[0])


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


def _update_of(deltas: list[Any]) -> dict[str, Any]:
    """The strongest synapse and net direction; no update when every delta is negligible."""

    if all(abs(delta) <= sim.WEIGHT_UPDATE_EPS for delta in deltas):
        return {"strongest_synapse": None, "weight_direction": tv.CREDIT_NO_CHANGE}
    strongest = max(range(len(deltas)), key=lambda index: (abs(deltas[index]), -index))
    return {"strongest_synapse": strongest, "weight_direction": _weight_direction(deltas)}


def _credit(measured: dict[str, Any]) -> dict[str, Any]:
    valence = measured["critic"]["valence"]
    _require(valence in tv.CREDIT_VALENCES, "critic.valence")
    deltas = measured["plasticity"]["weight_deltas"]
    _require(_numbers(deltas), "plasticity.weight_deltas")
    return {"valence": valence, **_update_of(deltas)}


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


def _measured_of(record: dict[str, Any]) -> dict[str, Any]:
    result = record.get("result")
    measured = result.get("measured") if isinstance(result, dict) else None
    if isinstance(measured, dict):
        return measured
    raise tv.TextViewRefusal(
        tv.FINDING_UNSUPPORTED_RECORD_SHAPE, "result.measured is not an object"
    )


def label_of(record: dict[str, Any]) -> dict[str, Any]:
    """The family's answer fields, re-derived from ``result.measured`` alone."""

    family = public.family_of(record)
    measured = _measured_of(record)
    try:
        return _LABELS[family](measured)
    except (KeyError, TypeError, IndexError, OverflowError) as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
            f"result.measured cannot yield the {family} label: {type(exc).__name__}",
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


bind_import_twin(__name__)
