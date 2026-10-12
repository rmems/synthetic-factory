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
import sys
from dataclasses import dataclass
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_public")
    from . import oracle_text_view_vocabulary as tv
    from .exact_json import dumps_exact_json
    from .oracle_grounded import canon
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_public"
    )
    import oracle_text_view_vocabulary as tv
    from exact_json import dumps_exact_json
    from oracle_grounded import canon

__all__ = [
    "PublicView", "choice_options", "compact", "family_of", "public_view", "render_choice_prompt",
    "render_prompt", "summarize",
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
    tv.refuse_when(
        not isinstance(family, str) or family not in tv.FAMILY_SET, tv.FINDING_UNKNOWN_FAMILY,
        f"family {tv.shown(family)} is not one of the five oracle-grounded families",
    )
    return family


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def summarize(values: list[Any]) -> dict[str, Any]:
    """Length, min, max and mean of a numeric array, rounded to canonical precision."""

    return {
        tv.SUMMARY_MARKER: True,
        "length": len(values),
        "min": canon.normalize(min(values)),
        "max": canon.normalize(max(values)),
        "mean": canon.normalize(math.fsum(values) / len(values)),
    }


def compact(value: Any) -> Any:
    """``value`` with every long numeric array replaced by its summary."""

    if isinstance(value, dict):
        return {key: compact(item) for key, item in value.items()}
    if isinstance(value, list):
        if len(value) > tv.MAX_INLINE_VALUES and all(_is_number(item) for item in value):
            return summarize(value)
        return [compact(item) for item in value]
    return value


def _allowlisted(section: Any, keys: tuple[str, ...], name: str) -> dict[str, Any]:
    missing = [key for key in keys if not isinstance(section, dict) or key not in section]
    tv.refuse_when(
        bool(missing), tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"{name} lacks the public keys {missing}",
    )
    return {key: section[key] for key in keys}


def _public_intervention(record: dict[str, Any], family: str) -> dict[str, Any] | None:
    keys = tv.INTERVENTION_KEYS[family]
    intervention = record.get("intervention")
    if keys is None:
        tv.refuse_when(
            intervention is not None, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
            f"{family} records carry no intervention",
        )
        return None
    return compact(_allowlisted(intervention, keys, "intervention"))


def public_view(record: dict[str, Any]) -> PublicView:
    """The allowlisted projection: the question, the scenario keys, the intervention keys."""

    family = family_of(record)
    scenario = record.get("scenario")
    question = scenario.get(tv.QUESTION_KEY) if isinstance(scenario, dict) else None
    tv.refuse_when(
        not isinstance(question, str) or not question.strip(),
        tv.FINDING_UNSUPPORTED_RECORD_SHAPE, "scenario.question must be a non-empty string",
    )
    return PublicView(
        family,
        question,
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


def _encoder_options(view: PublicView) -> tuple[str, ...]:
    pair = view.scenario["encoding_pair"]
    distinct_names = (
        isinstance(pair, list) and len(pair) == 2
        and all(isinstance(name, str) for name in pair)
        and pair[0] != pair[1] and tv.ENCODER_TIE_OPTION not in pair
    )
    tv.refuse_when(
        not distinct_names, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"encoding_pair {tv.shown(pair)} is not two distinct encodings",
    )
    return (*pair, tv.ENCODER_TIE_OPTION)


def _credit_options(view: PublicView) -> tuple[str, ...]:
    circuit = view.scenario["circuit"]
    count = circuit.get("pre_neuron_count") if isinstance(circuit, dict) else None
    tv.refuse_when(
        not isinstance(count, int) or isinstance(count, bool) or count < 1,
        tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"circuit.pre_neuron_count {tv.shown(count)} is not a positive integer",
    )
    synapses = tuple(f"{tv.CREDIT_SYNAPSE_PREFIX}{index}" for index in range(count))
    return (*synapses, tv.CREDIT_NO_UPDATE)


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


if __package__:
    _expose_package_sibling(__name__)
