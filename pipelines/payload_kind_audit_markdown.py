#!/usr/bin/env python3
"""Markdown rendering helpers for the payload-kind audit.

Extracted from ``payload_kind_audit`` so that module's total complexity stays
under the qlty High threshold. ``render_markdown`` remains the public entry
point re-exported by ``payload_kind_audit``.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))


def render_markdown(audit: Mapping[str, Any]) -> str:
    """Render the per-record table an operator can paste into a card."""
    lines = [
        "| Source | Kind | Record id | Gate | Wraps a coding episode | Coding steps |",
        "|---|---|---|---|---|---:|",
    ]
    for row in audit["records"]:
        supervisor_id = row.get("supervisor_id")
        gate = _markdown_cell(supervisor_id) if supervisor_id is not None else "—"
        decision = row.get("gate_decision")
        if decision is not None:
            gate = f"{gate} / {_markdown_cell(decision)}"
        record_id = _markdown_code(row["id"]) if row.get("id") is not None else "—"
        source = _markdown_code(f"{row['source_file']}:{row['source_line']}")
        lines.append(
            f"| {source} | {_markdown_cell(row['kind'])} | "
            f"{record_id} | {gate} | {'yes' if row['wraps_coding_episode'] else 'no'} | "
            f"{row['coding_steps']} |"
        )
    return "\n".join(lines) + "\n"


# ``json.loads`` decodes an escaped C0/C1 control such as ``\u001b`` into the
# raw byte, which neither ``html.escape`` nor the pipe/bracket escaping above
# neutralizes, so ``--markdown`` would write it straight to a terminal or a
# card. Render every remaining control as its visible ``\uXXXX`` source form.
# CR and LF are absent by the time this runs: they become ``<br>`` first.
_MARKDOWN_CONTROL_ESCAPES = {
    code: f"\\u{code:04x}"
    for code in (*range(0x00, 0x20), 0x7F, *range(0x80, 0xA0))
}


def _markdown_text(value: Any) -> str:
    """Return the value's faithful text form.

    A container is emitted verbatim onto the row — the decimal guard permits
    one — so ``str()`` would publish a Python repr (``{'key': None}``) that
    differs from the JSON the corpus holds. Serialize those as JSON. Scalars
    keep ``str()``: their rendering is pinned by the falsy-value tests.
    """
    if isinstance(value, (Mapping, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


# Markdown inline syntax that must not activate on audited corpus data. The
# link/image brackets were escaped first; backtick and the emphasis markers
# are the rest of what renders formatting instead of literal evidence.
_MARKDOWN_SYNTAX_ESCAPES = (
    ("|", "&#124;"),
    ("[", "&#91;"),
    ("]", "&#93;"),
    ("`", "&#96;"),
    ("*", "&#42;"),
    ("_", "&#95;"),
)

_BARE_URL_PREFIXES = ("http://", "https://")


def _is_plain_url(text: str) -> bool:
    """Return whether a scalar would activate GFM's bare-URL autolinker."""
    lowered = text.lower()
    return lowered.startswith(_BARE_URL_PREFIXES) and not any(
        marker in text for marker in ("`", "|", "\r", "\n")
    )


def _markdown_cell(value: Any) -> str:
    """Render one value as inert Markdown table text."""
    text = _markdown_text(value)
    if _is_plain_url(text):
        # Bracket escaping does not stop GFM from autolinking a bare URL.
        # A code span keeps the visible audit value unchanged and inert.
        return _markdown_code(text)
    rendered = html.escape(text, quote=False)
    for character, escape in _MARKDOWN_SYNTAX_ESCAPES:
        rendered = rendered.replace(character, escape)
    return (
        rendered.replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
        .translate(_MARKDOWN_CONTROL_ESCAPES)
    )


def _markdown_code(value: Any) -> str:
    """Render one value as an inline code span.

    A code span already disables every inline construct, so its contents need
    no metacharacter escaping — and escaping them would publish the entity
    itself (``&#42;``) rather than the character the corpus holds. Only text
    that would break out of the span falls back to ``<code>``, where the
    entities are decoded again.
    """
    text = _markdown_text(value)
    if not text:
        # Backticks around an empty accepted identifier collapse into one
        # uninterrupted two-backtick delimiter — malformed Markdown, not an
        # empty span — so only the closed element can render this value.
        return "<code></code>"
    if any(marker in text for marker in ("`", "|", "\r", "\n")):
        return f"<code>{_markdown_cell(text)}</code>"
    rendered = text.translate(_MARKDOWN_CONTROL_ESCAPES)
    if text.startswith(" ") and text.endswith(" ") and text.strip():
        # GFM removes one boundary space from a non-all-space code span. Add
        # one sentinel space to each side so the rendered value preserves the
        # audited leading/trailing spaces exactly.
        rendered = f" {rendered} "
    return rendered.join("``")
