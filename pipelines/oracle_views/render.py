"""Ungated row rendering for the three row shapes, and reading a row back.

``render_row`` is the one place a row is assembled from a record: the prompt
from the public view, the completion or answer from the measured label. It does
not consult the positive-example gate -- the gated builders in ``rows`` do, and
``findings`` re-derives the expected row through this same function to compare
against a row it is handed. The readers below take any value and return
``None`` (or an empty mapping) for anything that is not where the declared shape
puts it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from . import labels, public
from . import vocabulary as tv
from ._contract import bind_import_twin, envelope

__all__ = [
    "RowPair", "completion_object", "completion_text", "prompt_text", "render_row", "row_kind",
    "shape_matches",
]


@dataclass(frozen=True)
class RowPair:
    """A row as handed in, the row its record renders to (None if it cannot), and its shape."""

    row: dict[str, Any]
    expected: dict[str, Any] | None
    kind: str


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


def _chat_row(prompt: str, completion: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": tv.ROLE_USER, "content": prompt},
            {"role": tv.ROLE_ASSISTANT, "content": completion},
        ]
    }


def _sft_row(prompt: str, completion: str) -> dict[str, Any]:
    return {"prompt": prompt, "completion": completion}


_TEXT_ROWS = {tv.KIND_SFT: _sft_row, tv.KIND_CHAT: _chat_row}


def render_row(record: dict[str, Any], kind: str) -> dict[str, Any]:
    """The ``kind`` row for ``record``; a malformed record raises a coded refusal.

    ``kind`` is one of ``ROW_KINDS``; any other value is a programming error and
    raises ``KeyError`` rather than falling back to another shape.
    """

    text_row = None if kind == tv.KIND_CHOICE else _TEXT_ROWS[kind]
    view = public.public_view(record)
    if text_row is None:
        return _choice_row(record, view)
    return text_row(public.render_prompt(view), labels.completion_of(record))


def row_kind(row: dict[str, Any]) -> str:
    """The shape a row claims: chat by ``messages``, choice by ``options``/``answer``."""

    if "messages" in row:
        return tv.KIND_CHAT
    if "options" in row or "answer" in row:
        return tv.KIND_CHOICE
    return tv.KIND_SFT


def _role_of(message: Any) -> Any:
    if isinstance(message, dict) and set(message) == tv.MESSAGE_KEYS:
        return message["role"]
    return None


def _chat_messages_match(messages: Any) -> bool:
    roles = [_role_of(message) for message in messages] if isinstance(messages, list) else []
    return roles == [tv.ROLE_USER, tv.ROLE_ASSISTANT]


def shape_matches(row: dict[str, Any], kind: str) -> bool:
    """Exactly the declared keys; a chat row exactly one user then one assistant message."""

    if set(row) != tv.ROW_KEYS[kind]:
        return False
    return kind != tv.KIND_CHAT or _chat_messages_match(row["messages"])


def _message_content(row: dict[str, Any], index: int) -> Any:
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) <= index:
        return None
    message = messages[index]
    return message.get("content") if isinstance(message, dict) else None


def prompt_text(row: dict[str, Any], kind: str) -> Any:
    """The prompt side of a row: ``prompt``, or the first chat message's content."""

    if kind == tv.KIND_CHAT:
        return _message_content(row, 0)
    return row.get("prompt")


_ANSWER_KEYS = {tv.KIND_SFT: "completion", tv.KIND_CHOICE: "answer"}


def completion_text(row: dict[str, Any], kind: str) -> Any:
    """The answer side of a row: ``completion``, the second chat message, or ``answer``."""

    if kind == tv.KIND_CHAT:
        return _message_content(row, 1)
    return row.get(_ANSWER_KEYS[kind])


def completion_object(row: dict[str, Any], kind: str) -> dict[str, Any]:
    """The completion parsed as a JSON object; empty when it is not one."""

    text = completion_text(row, kind)
    try:
        value = json.loads(text, parse_constant=envelope.reject_json_constant)
    except (TypeError, ValueError, RecursionError):
        return {}
    return value if isinstance(value, dict) else {}


bind_import_twin(__name__)
