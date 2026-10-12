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
* ``is_positive(record)`` -- accepted, publishable, simulated, self-attributed and
  sealed; anything else is refused with a coded ``TextViewRefusal``;
* ``view_findings(record, row)`` -- the declared leak codes a row violates.

Every builder gates the record, renders the row and re-checks it with
``view_findings``; a row with any finding is refused, never returned. The view
is a projection and makes no training-readiness claim.
"""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_rows")
    from . import oracle_text_view_findings as _findings
    from . import oracle_text_view_gate as _gate
    from . import oracle_text_view_labels as _labels
    from . import oracle_text_view_public as _public
    from . import oracle_text_view_render as _render
    from . import oracle_text_view_vocabulary as tv
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_rows"
    )
    import oracle_text_view_findings as _findings
    import oracle_text_view_gate as _gate
    import oracle_text_view_labels as _labels
    import oracle_text_view_public as _public
    import oracle_text_view_render as _render
    import oracle_text_view_vocabulary as tv

PublicView = _public.PublicView
TextViewRefusal = tv.TextViewRefusal
public_view = _public.public_view
render_prompt = _public.render_prompt
choice_options = _public.choice_options
completion_of = _labels.completion_of
choice_answer_of = _labels.choice_answer_of
is_positive = _gate.is_positive
refusal_of = _gate.refusal_of
render_row = _render.render_row
view_findings = _findings.view_findings

__all__ = [
    "PublicView", "TextViewRefusal", "chat_row", "choice_answer_of", "choice_options",
    "choice_row", "completion_of", "is_positive", "public_view", "refusal_of", "render_prompt",
    "render_row", "rows_for", "sft_row", "view_findings",
]


def _checked(record: dict[str, Any], kind: str) -> dict[str, Any]:
    row = _render.render_row(record, kind)
    findings = view_findings(record, row)
    tv.refuse_when(
        bool(findings), tv.FINDING_RECORD_FAILS_VIEW_GATE,
        f"record {tv.shown(record.get('id'))} {kind} row fails the leak checks: "
        + ", ".join(findings),
    )
    return row


def rows_for(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every row shape for one positive record, keyed by kind; refused otherwise."""

    _gate.require_positive(record)
    return {kind: _checked(record, kind) for kind in tv.ROW_KINDS}


def sft_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"prompt", "completion"}`` for a positive record."""

    _gate.require_positive(record)
    return _checked(record, tv.KIND_SFT)


def chat_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"messages": [user, assistant]}`` for a positive record."""

    _gate.require_positive(record)
    return _checked(record, tv.KIND_CHAT)


def choice_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"prompt", "options", "answer"}`` over the family's closed label vocabulary."""

    _gate.require_positive(record)
    return _checked(record, tv.KIND_CHOICE)


if __package__:
    _expose_package_sibling(__name__)
