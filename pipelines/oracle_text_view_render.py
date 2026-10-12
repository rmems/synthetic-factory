"""Ungated row rendering for the three row shapes, and reading a row back.

``render_row`` is the one place a row is assembled from a record: the prompt
from the public view, the completion or answer from the measured label. It does
not consult the positive-example gate -- the gated builders in
``oracle_text_view_rows`` do, and ``oracle_text_view_findings`` re-derives the
expected row through this same function to compare against a row it is handed.
The readers below take any value and return ``None`` for anything that is not
where the declared shape puts it.
"""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_view_render")
    from . import oracle_text_view_labels as labels
    from . import oracle_text_view_public as public
    from . import oracle_text_view_vocabulary as tv
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_view_render"
    )
    import oracle_text_view_labels as labels
    import oracle_text_view_public as public
    import oracle_text_view_vocabulary as tv

__all__ = ["completion_text", "prompt_text", "render_row", "row_kind", "shape_matches"]


def _choice_row(record: dict[str, Any], view: public.PublicView) -> dict[str, Any]:
    options = public.choice_options(view)
    answer = labels.choice_answer_of(record)
    tv.refuse_when(
        answer not in options, tv.FINDING_UNSUPPORTED_RECORD_SHAPE,
        f"measured answer {tv.shown(answer)} is not one of the options {list(options)}",
    )
    return {
        "prompt": public.render_choice_prompt(view, options),
        "options": list(options),
        "answer": answer,
    }


def render_row(record: dict[str, Any], kind: str) -> dict[str, Any]:
    """The ``kind`` row for ``record``; a malformed record raises a coded refusal."""

    view = public.public_view(record)
    if kind == tv.KIND_CHOICE:
        return _choice_row(record, view)
    prompt, completion = public.render_prompt(view), labels.completion_of(record)
    if kind == tv.KIND_CHAT:
        return {
            "messages": [
                {"role": tv.ROLE_USER, "content": prompt},
                {"role": tv.ROLE_ASSISTANT, "content": completion},
            ]
        }
    return {"prompt": prompt, "completion": completion}


def row_kind(row: dict[str, Any]) -> str:
    """The shape a row claims: chat by ``messages``, choice by ``options``/``answer``."""

    if "messages" in row:
        return tv.KIND_CHAT
    if "options" in row or "answer" in row:
        return tv.KIND_CHOICE
    return tv.KIND_SFT


def _message(row: dict[str, Any], index: int) -> dict[str, Any] | None:
    messages = row.get("messages")
    if isinstance(messages, list) and len(messages) > index and isinstance(messages[index], dict):
        return messages[index]
    return None


def shape_matches(row: dict[str, Any], kind: str) -> bool:
    """Exactly the declared keys; a chat row exactly one user then one assistant message."""

    if set(row) != tv.ROW_KEYS[kind]:
        return False
    if kind != tv.KIND_CHAT:
        return True
    roles = (tv.ROLE_USER, tv.ROLE_ASSISTANT)
    messages = row["messages"]
    return isinstance(messages, list) and len(messages) == len(roles) and all(
        isinstance(message, dict) and set(message) == tv.MESSAGE_KEYS and message["role"] == role
        for message, role in zip(messages, roles)
    )


def prompt_text(row: dict[str, Any], kind: str) -> Any:
    """The prompt side of a row: ``prompt``, or the first chat message's content."""

    if kind == tv.KIND_CHAT:
        message = _message(row, 0)
        return None if message is None else message.get("content")
    return row.get("prompt")


def completion_text(row: dict[str, Any], kind: str) -> Any:
    """The answer side of a row: ``completion``, the second chat message, or ``answer``."""

    if kind == tv.KIND_CHAT:
        message = _message(row, 1)
        return None if message is None else message.get("content")
    if kind == tv.KIND_CHOICE:
        return row.get("answer")
    return row.get("completion")


if __package__:
    _expose_package_sibling(__name__)
