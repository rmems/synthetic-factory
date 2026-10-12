"""Whether a row carries the non-authoritative candidate prediction.

``candidate_prediction`` is a deliberately non-authoritative heuristic guess and
must never reach a prompt or completion. A row leaks it when:

* a ``predicted_*`` key name or the heuristic ``basis`` text appears anywhere in
  the row;
* a completion field or choice answer disagrees with the measurement but equals
  the guess (the label was taken from the guess); or
* the prompt carries a guessed value more often than the public-view rendering
  of the same record does (the guess was added to the prompt).

A row rendered from its record has none of these by construction, so the checks
compare against that rendering rather than searching for short values (a guess
such as ``"A"`` or ``"temporal"`` legitimately appears in a canonical prompt).
"""

from __future__ import annotations

import re
from typing import Any

from . import labels, render
from . import vocabulary as tv
from ._contract import bind_import_twin, dumps_exact_json

__all__ = ["candidate_leaked", "same"]


def same(left: Any, right: Any) -> bool:
    """Equality that never confuses a boolean with the number it subclasses."""

    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    return left == right


def _strings(value: Any) -> list[str]:
    """Every string in ``value``, mapping keys included; iterative, so depth cannot overflow."""

    found: list[str] = []
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, dict):
            found.extend(map(str, item))
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return found


def _basis_phrases(candidate: dict[str, Any]) -> list[str]:
    texts = [candidate.get(key) for key in tv.CANDIDATE_TEXT_KEYS]
    return [text for text in texts if isinstance(text, str) and text.strip()]


def _names_the_guess(row: dict[str, Any], candidate: dict[str, Any]) -> bool:
    markers = [tv.PREDICTED_PREFIX, *_basis_phrases(candidate)]
    return any(marker in text for text in _strings(row) for marker in markers)


def _copied(value: Any, measured: Any, guessed: Any) -> bool:
    """A value that disagrees with the measurement but equals the guess."""

    return not same(value, measured) and same(value, guessed)


def _answer_copied(family: str, row: dict[str, Any], expected: dict, candidate: dict) -> bool:
    guess_key = tv.GUESS_FIELDS[family].get(tv.CHOICE_FIELD[family])
    if guess_key not in candidate:
        return False
    guessed = labels.choice_option(family, candidate[guess_key])
    return _copied(row.get("answer"), expected["answer"], guessed)


def _fields_copied(record: dict[str, Any], row: dict[str, Any], kind: str, candidate: dict) -> bool:
    completion = render.completion_object(row, kind)
    measured = labels.label_of(record)
    guesses = tv.GUESS_FIELDS[record["family"]].items()
    return any(
        _copied(completion[field], measured[field], candidate[key])
        for field, key in guesses
        if field in completion and key in candidate
    )


def _label_copied(record: dict, pair: render.RowPair, expected: dict, candidate: dict) -> bool:
    if pair.kind == tv.KIND_CHOICE:
        return _answer_copied(record["family"], pair.row, expected, candidate)
    return _fields_copied(record, pair.row, pair.kind, candidate)


def _guess_tokens(candidate: dict[str, Any]) -> list[str]:
    values = [value for key, value in candidate.items() if str(key).startswith(tv.PREDICTED_PREFIX)]
    scalars = [value for value in values if isinstance(value, (str, int, float))]
    return [value if isinstance(value, str) else dumps_exact_json(value) for value in scalars]


def _occurrences(text: str, token: str) -> int:
    return len(re.findall(rf"(?<![\w.]){re.escape(token)}(?![\w.])", text))


def _guess_added_to_prompt(pair: render.RowPair, expected: dict, candidate: dict) -> bool:
    prompt = render.prompt_text(pair.row, pair.kind)
    rendered = render.prompt_text(expected, pair.kind)
    if not isinstance(prompt, str) or prompt == rendered:
        return False
    tokens = [token for token in _guess_tokens(candidate) if token]
    return any(_occurrences(prompt, token) > _occurrences(rendered, token) for token in tokens)


def candidate_leaked(record: dict[str, Any], pair: render.RowPair) -> bool:
    """Whether ``pair.row`` carries ``record``'s candidate prediction in any of the three ways."""

    candidate = record.get("candidate_prediction")
    if not isinstance(candidate, dict):
        return False
    if _names_the_guess(pair.row, candidate):
        return True
    expected = pair.expected
    if expected is None:
        return False
    return _label_copied(record, pair, expected, candidate) or _guess_added_to_prompt(
        pair, expected, candidate
    )


bind_import_twin(__name__)
