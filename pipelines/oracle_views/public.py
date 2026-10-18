"""The public view: an allowlisted projection of ``scenario`` and ``intervention``.

A prompt is a pure function of a :class:`PublicView`, and a public view reads
exactly the keys ``SCENARIO_KEYS`` and ``INTERVENTION_KEYS`` declare for the
record's family -- never ``result``, ``oracle``, ``candidate_prediction`` or
``validation``. A numeric array longer than ``MAX_INLINE_VALUES`` is replaced
by a deterministic summary (length, min, max, mean at the canonical six-decimal
precision) under an explicit ``summarized`` marker, so a 64-sample trace does not
dominate the prompt. The multiple-choice options are drawn from the family's
closed label vocabulary and, where the answer space depends on the scenario (the
compared encoding pair, the synapse count), from the public view alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, TypeGuard

from . import vocabulary as tv
from ._contract import bind_import_twin, canon, dumps_exact_json

__all__ = [
    "PublicView", "choice_options", "compact", "family_of", "is_integer", "is_number",
    "public_view", "render_choice_prompt", "render_prompt", "summarize",
]


@dataclass(frozen=True)
class PublicView:
    """The only fields a prompt is rendered from."""

    family: str
    question: str
    scenario: dict[str, Any]
    intervention: dict[str, Any] | None


def family_of(record: Any) -> str:
    """The record's family when it is one of the five; refused otherwise."""

    family = record.get("family") if isinstance(record, dict) else None
    if isinstance(family, str) and family in tv.FAMILY_SET:
        return family
    raise tv.TextViewRefusal(
        tv.FINDING_UNKNOWN_FAMILY,
        f"family {tv.shown(family)} is not one of the five oracle-grounded families",
    )


def is_number(value: Any) -> bool:
    """An int or float that is not a boolean."""

    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer(value: Any) -> TypeGuard[int]:
    """An int that is not a boolean."""

    return isinstance(value, int) and not isinstance(value, bool)


def _is_long_numeric(value: Any) -> bool:
    if not isinstance(value, list) or len(value) <= tv.MAX_INLINE_VALUES:
        return False
    return all(is_number(item) for item in value)


def _mean(values: list[Any]) -> float:
    try:
        return math.fsum(values) / len(values)
    except OverflowError as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_UNSUPPORTED_RECORD_SHAPE, "a numeric array overflows its mean"
        ) from exc


def summarize(values: list[Any]) -> dict[str, Any]:
    """Length, min, max and mean of a numeric array, rounded to canonical precision."""

    return {
        tv.SUMMARY_MARKER: True,
        "length": len(values),
        "min": canon.normalize(min(values)),
        "max": canon.normalize(max(values)),
        "mean": canon.normalize(_mean(values)),
    }


def compact(value: Any) -> Any:
    """``value`` with every long numeric array replaced by its summary."""

    if isinstance(value, dict):
        return {key: compact(item) for key, item in value.items()}
    if _is_long_numeric(value):
        return summarize(value)
    if isinstance(value, list):
        return [compact(item) for item in value]
    return value


def _allowlisted(section: Any, keys: tuple[str, ...], name: str) -> dict[str, Any]:
    present = section if isinstance(section, dict) else {}
    missing = [key for key in keys if key not in present]
    tv.refuse_when(
        bool(missing), tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"{name} lacks the public keys {missing}",
    )
    return {key: present[key] for key in keys}


def _public_intervention(record: dict[str, Any], family: str) -> dict[str, Any] | None:
    keys = tv.INTERVENTION_KEYS[family]
    intervention = record.get("intervention")
    if keys is not None:
        return compact(_allowlisted(intervention, keys, "intervention"))
    tv.refuse_when(
        intervention is not None, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"{family} records carry no intervention",
    )
    return None


def _question_of(scenario: Any) -> str:
    question = scenario.get(tv.QUESTION_KEY) if isinstance(scenario, dict) else None
    if isinstance(question, str) and question.strip():
        return question
    raise tv.TextViewRefusal(
        tv.FINDING_UNSUPPORTED_RECORD_SHAPE, "scenario.question must be a non-empty string"
    )


def public_view(record: dict[str, Any]) -> PublicView:
    """The allowlisted projection: the question, the scenario keys, the intervention keys."""

    family = family_of(record)
    scenario = record.get("scenario")
    return PublicView(
        family,
        _question_of(scenario),
        compact(_allowlisted(scenario, tv.SCENARIO_KEYS[family], "scenario")),
        _public_intervention(record, family),
    )


def _json(value: Any) -> str:
    return dumps_exact_json(value, sort_keys=True)


def _context_blocks(view: PublicView) -> list[str]:
    blocks = [view.question, f"{tv.SCENARIO_HEADING}\n{_json(view.scenario)}"]
    if view.intervention is not None:
        blocks.append(f"{tv.INTERVENTION_HEADING}\n{_json(view.intervention)}")
    return blocks


def render_prompt(view: PublicView) -> str:
    """The question, the compact scenario and intervention, and the family's instruction."""

    blocks = _context_blocks(view)
    blocks.append(f"{tv.INSTRUCTIONS_HEADING}\n{tv.INSTRUCTIONS[view.family]}")
    return "\n\n".join(blocks) + "\n"


def _two_distinct_encodings(pair: Any) -> bool:
    if not isinstance(pair, list):
        return False
    names = {name for name in pair if isinstance(name, str)} - {tv.ENCODER_TIE_OPTION}
    return len(names) == len(pair) == 2


def _encoder_options(view: PublicView) -> tuple[str, ...]:
    pair = view.scenario["encoding_pair"]
    tv.refuse_when(
        not _two_distinct_encodings(pair), tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"encoding_pair {tv.shown(pair)} is not two distinct encodings",
    )
    return *pair, tv.ENCODER_TIE_OPTION


def _synapse_count(circuit: Any) -> int:
    count = circuit.get("pre_neuron_count") if isinstance(circuit, dict) else None
    if is_integer(count) and count >= 1:
        return count
    raise tv.TextViewRefusal(
        tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"circuit.pre_neuron_count {tv.shown(count)} is not a positive integer",
    )


def _credit_options(view: PublicView) -> tuple[str, ...]:
    count = _synapse_count(view.scenario["circuit"])
    synapses = tuple(f"{tv.CREDIT_SYNAPSE_PREFIX}{index}" for index in range(count))
    return *synapses, tv.CREDIT_NO_UPDATE


_OPTIONS = {
    tv.ENCODER_FAMILY: _encoder_options,
    tv.NEURON_FAMILY: lambda _view: tv.NEURON_DIRECTIONS,
    tv.MESH_FAMILY: lambda _view: tv.MESH_OUTCOMES,
    tv.CREDIT_FAMILY: _credit_options,
    tv.MEMORY_FAMILY: lambda _view: tv.MEMORY_RESPONSES,
}


def choice_options(view: PublicView) -> tuple[str, ...]:
    """The family's closed answer space, specialised only by public scenario fields."""

    return tuple(_OPTIONS[view.family](view))


def render_choice_prompt(view: PublicView, options: tuple[str, ...]) -> str:
    """The same context, the options as a list, and the family's choice question."""

    blocks = _context_blocks(view)
    blocks.append(tv.OPTIONS_HEADING + "\n" + "\n".join(f"- {option}" for option in options))
    blocks.append(
        f"{tv.INSTRUCTIONS_HEADING}\n{tv.CHOICE_QUESTIONS[view.family]} {tv.CHOICE_INSTRUCTION}"
    )
    return "\n\n".join(blocks) + "\n"


bind_import_twin(__name__)
