"""Leak checks: re-derive a row from its record and report every divergence by code.

``view_findings`` compares a row against the row ``render.render_row`` derives
from the same record and returns the declared leak codes it violates:

* ``VIEW_EXTRA_KEYS`` -- the row is not exactly the declared shape;
* ``PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW`` -- the prompt (or choice options)
  differs from the public-view rendering;
* ``COMPLETION_NOT_FROM_MEASUREMENT`` / ``LABEL_NOT_DERIVED_FROM_MEASUREMENT`` --
  the completion or choice answer differs from the measured label;
* ``PROPOSAL_DIGEST_MISMATCH`` / ``MEASUREMENT_DIGEST_MISMATCH`` -- the scenario
  or measurement the row was derived from no longer matches its stored hash;
* ``CANDIDATE_PREDICTION_LEAKED`` -- see ``leaks``;
* ``HIDDEN_REASONING_KEY`` -- a hidden-reasoning key in the row, its completion
  object or the public sections it was rendered from;
* ``ROW_FROM_NON_POSITIVE_RECORD`` -- the record does not pass the gate.

A row rendered by ``render_row`` from a positive record has no findings.
"""

from __future__ import annotations

from typing import Any

from . import gate, leaks, render
from . import vocabulary as tv
from ._contract import bind_import_twin, contains_hidden_reasoning_key

__all__ = ["view_findings"]

_ANSWER_CODES = {
    tv.KIND_SFT: tv.LEAK_COMPLETION_NOT_FROM_MEASUREMENT,
    tv.KIND_CHAT: tv.LEAK_COMPLETION_NOT_FROM_MEASUREMENT,
    tv.KIND_CHOICE: tv.LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT,
}


def _expected_row(record: Any, kind: str) -> dict[str, Any] | None:
    try:
        return render.render_row(record, kind)
    except tv.TextViewRefusal:
        return None


def _prompt_differs(pair: render.RowPair, expected: dict[str, Any]) -> bool:
    if render.prompt_text(pair.row, pair.kind) != render.prompt_text(expected, pair.kind):
        return True
    return pair.row.get("options") != expected.get("options")


def _answer_differs(pair: render.RowPair, expected: dict[str, Any]) -> bool:
    answer = render.completion_text(pair.row, pair.kind)
    return not leaks.same(answer, render.completion_text(expected, pair.kind))


def _derivation_findings(pair: render.RowPair) -> list[str]:
    answer_code = _ANSWER_CODES[pair.kind]
    expected = pair.expected
    if expected is None:
        return [tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, answer_code]
    checks = (
        (_prompt_differs(pair, expected), tv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW),
        (_answer_differs(pair, expected), answer_code),
    )
    return [code for differs, code in checks if differs]


def _hidden_reasoning(record: dict[str, Any], pair: render.RowPair) -> bool:
    sections = [record.get("scenario"), record.get("intervention")]
    completion = render.completion_object(pair.row, pair.kind)
    return any(contains_hidden_reasoning_key(value) for value in (pair.row, sections, completion))


def _record_leaks(record: dict[str, Any], pair: render.RowPair) -> list[str]:
    checks = (
        (leaks.candidate_leaked(record, pair), tv.LEAK_CANDIDATE_PREDICTION_LEAKED),
        (_hidden_reasoning(record, pair), tv.LEAK_HIDDEN_REASONING_KEY),
    )
    return gate.seal_findings(record) + [code for leaked, code in checks if leaked]


def view_findings(record: Any, row: Any) -> list[str]:
    """Every declared leak code ``row`` violates against ``record``, in a fixed order."""

    shaped = row if isinstance(row, dict) else {}
    kind = render.row_kind(shaped)
    pair = render.RowPair(shaped, _expected_row(record, kind), kind)
    findings = [] if render.shape_matches(shaped, kind) else [tv.LEAK_VIEW_EXTRA_KEYS]
    findings += _derivation_findings(pair)
    findings += _record_leaks(record, pair) if isinstance(record, dict) else []
    if not gate.is_positive(record):
        findings.append(tv.LEAK_ROW_FROM_NON_POSITIVE_RECORD)
    return findings


bind_import_twin(__name__)
