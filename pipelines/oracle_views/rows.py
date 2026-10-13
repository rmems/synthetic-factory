"""The oracle-grounded text view: gated row builders and the per-record surface.

One import for consumers of the five neuromorphic families' text projection:

* ``public_view(record)`` / ``render_prompt(view)`` -- the allowlisted scenario and
  intervention, never ``result``, ``oracle``, ``candidate_prediction`` or
  ``validation``;
* ``completion_of(record)`` -- the short canonical answer re-derived from
  ``result.measured``;
* ``sft_row`` -> ``{"prompt", "completion"}``, ``chat_row`` -> ``{"messages": [user,
  assistant]}``, ``choice_row`` -> ``{"prompt", "options", "answer"}`` over the
  family's closed label vocabulary;
* ``is_positive(record)`` -- accepted, publishable, simulated, self-attributed,
  sealed and replayed to ``result_hash``; anything else is refused with a coded
  ``TextViewRefusal``;
* ``view_findings(record, row)`` -- the declared leak codes a row violates.

Every builder gates the record, renders the row and re-checks it with
``view_findings``; a row with any finding is refused, never returned. The view
is a projection and makes no training-readiness claim.
"""

from __future__ import annotations

from typing import Any

from . import findings, gate, labels, public, render
from . import vocabulary as tv
from ._contract import bind_import_twin

PublicView = public.PublicView
TextViewRefusal = tv.TextViewRefusal
public_view = public.public_view
render_prompt = public.render_prompt
choice_options = public.choice_options
completion_of = labels.completion_of
choice_answer_of = labels.choice_answer_of
is_positive = gate.is_positive
refusal_of = gate.refusal_of
render_row = render.render_row
view_findings = findings.view_findings

__all__ = (
    "PublicView TextViewRefusal chat_row choice_answer_of choice_options choice_row completion_of "
    "is_positive public_view refusal_of render_prompt render_row rows_for sft_row view_findings"
).split()


def _checked(record: dict[str, Any], kind: str) -> dict[str, Any]:
    row = render.render_row(record, kind)
    codes = view_findings(record, row)
    tv.refuse_when(
        bool(codes), tv.FINDING_RECORD_FAILS_VIEW_GATE,
        f"record {tv.shown(record.get('id'))} {kind} row fails the leak checks: "
        + ", ".join(codes),
    )
    return row


def _gated(record: dict[str, Any], kind: str) -> dict[str, Any]:
    gate.require_positive(record)
    return _checked(record, kind)


def rows_for(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every row shape for one positive record, keyed by kind; refused otherwise."""

    gate.require_positive(record)
    return {kind: _checked(record, kind) for kind in tv.ROW_KINDS}


def sft_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"prompt", "completion"}`` for a positive record."""

    return _gated(record, tv.KIND_SFT)


def chat_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"messages": [user, assistant]}`` for a positive record."""

    return _gated(record, tv.KIND_CHAT)


def choice_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"prompt", "options", "answer"}`` over the family's closed label vocabulary."""

    return _gated(record, tv.KIND_CHOICE)


bind_import_twin(__name__)
