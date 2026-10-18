#!/usr/bin/env python3
"""The chat view: the SFT pair as one user turn and one assistant turn.

A chat-template trainer consumes ``{"messages": [user, assistant]}`` rows. The
user turn is exactly the SFT prompt of :mod:`views` and the assistant turn the
verified corrected module, so this view adds no text a record could leak into:
:func:`chat_findings` unwraps the pair and re-runs the SFT view's checks on it,
and reports any other shape with a declared code; an export aborts on any.
"""

from __future__ import annotations

from typing import Any

from . import views
from . import vocabulary as cv
from ._contract import bind_import_twin, contains_hidden_reasoning_key

CHAT_KEYS = frozenset({"messages"})
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

__all__ = ["CHAT_KEYS", "ROLE_ASSISTANT", "ROLE_USER", "chat_candidate", "chat_findings",
           "chat_pair", "chat_row"]


def chat_candidate(record: dict[str, Any]) -> dict[str, Any]:
    """The chat rendering of a record's pair, before any leak check."""

    prompt = views.render_prompt(views.public_view(record))
    return {"messages": [{"role": ROLE_USER, "content": prompt},
                         {"role": ROLE_ASSISTANT, "content": views.completion_of(record)}]}


def chat_row(record: dict[str, Any]) -> dict[str, Any]:
    """``{"messages": [user, assistant]}`` for a positive record; refused otherwise.

    The user turn is the SFT prompt and the assistant turn the verified module,
    so a chat-template trainer consumes exactly the pair ``sft_row`` renders.
    """

    views.sft_row(record)
    row = chat_candidate(record)
    findings = chat_findings(record, row)
    cv.refuse_when(bool(findings), cv.FINDING_RECORD_MALFORMED,
                   "record fails chat view validation: " + ", ".join(findings))
    return row


def _message_text(message: Any, role: str) -> str | None:
    """The content of a ``{"role", "content"}`` message with this role, else ``None``."""

    if not isinstance(message, dict) or set(message) != {"role", "content"}:
        return None
    content = message["content"]
    return content if message["role"] == role and isinstance(content, str) else None


def chat_pair(row: Any) -> tuple[str, str] | None:
    """The ``(prompt, completion)`` a well-formed chat row carries, else ``None``."""

    messages = row.get("messages") if isinstance(row, dict) and set(row) == CHAT_KEYS else None
    if not isinstance(messages, list) or len(messages) != 2:
        return None
    prompt = _message_text(messages[0], ROLE_USER)
    completion = _message_text(messages[1], ROLE_ASSISTANT)
    return None if prompt is None or completion is None else (prompt, completion)


def chat_findings(record: dict[str, Any], row: Any) -> list[str]:
    """Every declared leak code a chat row violates against its record."""

    if not isinstance(row, dict) or set(row) != CHAT_KEYS:
        return [cv.LEAK_VIEW_EXTRA_KEYS]
    pair = chat_pair(row)
    if pair is None:
        return [cv.LEAK_CHAT_MESSAGES_MALFORMED]
    findings = views.view_findings(record, {"prompt": pair[0], "completion": pair[1]})
    if contains_hidden_reasoning_key(row) and cv.LEAK_HIDDEN_REASONING_KEY not in findings:
        findings.append(cv.LEAK_HIDDEN_REASONING_KEY)
    return findings


bind_import_twin(__name__)
