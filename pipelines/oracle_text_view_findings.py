"""Leak checks: re-derive a row from its record and report every divergence by code.

``view_findings`` compares a row against the row ``render_row`` derives from the
same record and returns the declared leak codes it violates:

* ``VIEW_EXTRA_KEYS`` -- the row is not exactly the declared shape;
* ``PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW`` -- the prompt (or choice options)
  differs from the public-view rendering;
* ``COMPLETION_NOT_FROM_MEASUREMENT`` / ``LABEL_NOT_DERIVED_FROM_MEASUREMENT`` --
  the completion or choice answer differs from the measured label;
* ``PROPOSAL_DIGEST_MISMATCH`` / ``MEASUREMENT_DIGEST_MISMATCH`` -- the scenario
  or measurement the row was derived from no longer matches its stored hash;
* ``CANDIDATE_PREDICTION_LEAKED`` -- a ``predicted_*`` key name or the heuristic
  ``basis`` text appears anywhere in the row, a label disagrees with the
  measurement but equals the guess, or the prompt carries a guessed value more
  often than the public-view rendering does;
* ``HIDDEN_REASONING_KEY`` -- a hidden-reasoning key in the row, its completion
  object or the public sections it was rendered from;
* ``ROW_FROM_NON_POSITIVE_RECORD`` -- the record does not pass the gate.

A row rendered by ``render_row`` from a positive record has no findings.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_findings")
    from . import oracle_text_view_gate as gate
    from . import oracle_text_view_labels as labels
    from . import oracle_text_view_render as render
    from . import oracle_text_view_vocabulary as tv
    from .curate_coding import contains_hidden_reasoning_key
    from .exact_json import dumps_exact_json
    from .oracle_grounded.envelope import reject_json_constant
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_findings"
    )
    import oracle_text_view_gate as gate
    import oracle_text_view_labels as labels
    import oracle_text_view_render as render
    import oracle_text_view_vocabulary as tv
    from curate_coding import contains_hidden_reasoning_key
    from exact_json import dumps_exact_json
    from oracle_grounded.envelope import reject_json_constant

__all__ = ["view_findings"]


def _strings(value: Any) -> Iterator[str]:
    """Every string in ``value``, mapping keys included."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _parsed_object(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    try:
        value = json.loads(text, parse_constant=reject_json_constant)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _same(left: Any, right: Any) -> bool:
    """Equality that never confuses a boolean with the number it subclasses."""

    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    return left == right


def _guess_tokens(candidate: dict[str, Any]) -> Iterator[str]:
    for key, value in candidate.items():
        if not str(key).startswith(tv.PREDICTED_PREFIX) or isinstance(value, (dict, list)):
            continue
        if value is not None and value != "":
            yield value if isinstance(value, str) else dumps_exact_json(value)


def _occurrences(text: str, token: str) -> int:
    return len(re.findall(rf"(?<![\w.]){re.escape(token)}(?![\w.])", text))


def _guess_added_to_prompt(row: dict, kind: str, expected: dict, candidate: dict) -> bool:
    prompt, rendered = render.prompt_text(row, kind), render.prompt_text(expected, kind)
    if not isinstance(prompt, str) or prompt == rendered:
        return False
    return any(
        _occurrences(prompt, token) > _occurrences(rendered, token)
        for token in _guess_tokens(candidate)
    )


def _label_copied_from_guess(
    record: dict, row: dict, kind: str, expected: dict, candidate: dict
) -> bool:
    family = record["family"]
    guesses = tv.GUESS_FIELDS[family]
    if kind == tv.KIND_CHOICE:
        guess_key = guesses.get(tv.CHOICE_FIELD[family])
        if guess_key not in candidate:
            return False
        answer = row.get("answer")
        guessed = labels.choice_option(family, candidate[guess_key])
        return not _same(answer, expected["answer"]) and _same(answer, guessed)
    completion = _parsed_object(render.completion_text(row, kind))
    if completion is None:
        return False
    measured = labels.label_of(record)
    return any(
        field in completion and guess_key in candidate
        and not _same(completion[field], measured[field])
        and _same(completion[field], candidate[guess_key])
        for field, guess_key in guesses.items()
    )


def _candidate_leaked(record: dict, row: dict, kind: str, expected: dict | None) -> bool:
    candidate = record.get("candidate_prediction")
    if not isinstance(candidate, dict):
        return False
    basis = [
        text for text in (candidate.get(key) for key in tv.CANDIDATE_TEXT_KEYS)
        if isinstance(text, str) and text.strip()
    ]
    if any(
        tv.PREDICTED_PREFIX in text or any(phrase in text for phrase in basis)
        for text in _strings(row)
    ):
        return True
    if expected is None:
        return False
    return _label_copied_from_guess(record, row, kind, expected, candidate) or (
        _guess_added_to_prompt(row, kind, expected, candidate)
    )


def _hidden_reasoning(record: dict, row: dict, kind: str) -> bool:
    sections = [record.get("scenario"), record.get("intervention")]
    completion = _parsed_object(render.completion_text(row, kind))
    return any(contains_hidden_reasoning_key(value) for value in (row, sections, completion))


def _expected_row(record: dict, kind: str) -> dict | None:
    try:
        return render.render_row(record, kind)
    except tv.TextViewRefusal:
        return None


def _derivation_findings(row: dict, kind: str, expected: dict | None) -> list[str]:
    answer_code = (
        tv.LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT if kind == tv.KIND_CHOICE
        else tv.LEAK_COMPLETION_NOT_FROM_MEASUREMENT
    )
    if expected is None:
        return [tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, answer_code]
    findings = []
    prompt_differs = render.prompt_text(row, kind) != render.prompt_text(expected, kind)
    options_differ = kind == tv.KIND_CHOICE and row.get("options") != expected["options"]
    if prompt_differs or options_differ:
        findings.append(tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW)
    if not _same(render.completion_text(row, kind), render.completion_text(expected, kind)):
        findings.append(answer_code)
    return findings


def _record_leaks(record: dict, row: dict, kind: str, expected: dict | None) -> list[str]:
    leaks = gate.seal_findings(record)
    if _candidate_leaked(record, row, kind, expected):
        leaks.append(tv.LEAK_CANDIDATE_PREDICTION_LEAKED)
    if _hidden_reasoning(record, row, kind):
        leaks.append(tv.LEAK_HIDDEN_REASONING_KEY)
    return leaks


def view_findings(record: dict[str, Any], row: Any) -> list[str]:
    """Every declared leak code ``row`` violates against ``record``, in a fixed order."""

    row = row if isinstance(row, dict) else {}
    kind = render.row_kind(row)
    expected = _expected_row(record, kind)
    findings = [] if render.shape_matches(row, kind) else [tv.LEAK_VIEW_EXTRA_KEYS]
    findings += _derivation_findings(row, kind, expected)
    if isinstance(record, dict):
        findings += _record_leaks(record, row, kind, expected)
    if not gate.is_positive(record):
        findings.append(tv.LEAK_ROW_FROM_NON_POSITIVE_RECORD)
    return findings


if __package__:
    _expose_package_sibling(__name__)
