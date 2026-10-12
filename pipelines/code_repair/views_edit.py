#!/usr/bin/env python3
"""The edit view: the SFT prompt with one SEARCH/REPLACE block as the completion.

The whole-module completion of :mod:`views` spends most of its tokens copying
the prompt back; every mutation is one span, so the verified repair is also one
small edit. This view keeps the public prompt (task, broken module, bounded
failure evidence; only the instruction line differs) and renders the completion
as one SEARCH/REPLACE block: the smallest window of whole lines around the
changed block that occurs exactly once in the broken module, and the same
window taken from the verified repaired module. A block is a valid completion
only when applying it to the broken text reproduces the repaired module byte
for byte (``result.repaired_sha256``), so the edit is exactly as verified as
the module it stands for. :func:`edit_findings` re-derives a row from its
record and reports every divergence with a declared code; an export aborts on
any.
"""

from __future__ import annotations

from typing import Any

from . import catalog as cat
from . import views
from . import vocabulary as cv
from ._contract import bind_import_twin, contains_hidden_reasoning_key

__all__ = [
    "apply_block", "edit_candidate", "edit_findings", "edit_row", "occurrences", "parse_block",
    "render_block", "render_edit_prompt", "search_replace",
]

_SEARCH = cv.EDIT_SEARCH_MARKER + "\n"
_DIVIDER = cv.EDIT_DIVIDER + "\n"
_REPLACE = cv.EDIT_REPLACE_MARKER + "\n"
_MARKER_LINES = frozenset({_SEARCH, _DIVIDER, _REPLACE})


def render_edit_prompt(view: views.PublicView) -> str:
    """The SFT prompt with the edit instruction in place of the whole-module one."""

    return views.render_prompt(view, cv.EDIT_INSTRUCTIONS)


def _shared_prefix(left: list[str], right: list[str]) -> int:
    count = 0
    for old, new in zip(left, right):
        if old != new:
            break
        count += 1
    return count


def _changed_window(broken: list[str], repaired: list[str]) -> tuple[int, int, int]:
    """``(start, broken_end, repaired_end)`` of the block that differs, by whole lines."""

    prefix = _shared_prefix(broken, repaired)
    room = min(len(broken), len(repaired)) - prefix
    suffix = min(_shared_prefix(broken[::-1], repaired[::-1]), room)
    return prefix, len(broken) - suffix, len(repaired) - suffix


def occurrences(text: str, fragment: str) -> int:
    """How many positions ``fragment`` starts at in ``text``, overlapping matches included.

    ``str.count`` skips overlapping matches, so ``"a\na\n"`` would read as unique
    in ``"a\na\na\n"`` although it starts at two positions.
    """

    count, start = 0, text.find(fragment)
    while start != -1:
        count += 1
        start = text.find(fragment, start + 1)
    return count


def _unique_frame(broken: str, search: str, replace: str) -> bool:
    framed = all((search, replace)) and _framed(search, replace)
    return framed and occurrences(broken, search) == 1


def _widened(lo: int, hi: int, total: int) -> tuple[int, int] | None:
    """One more context line, below first and then above; ``None`` at the whole module."""

    if hi < total:
        return lo, hi + 1
    if lo > 0:
        return lo - 1, hi
    return None


def search_replace(broken: str, repaired: str) -> tuple[str, str]:
    """The canonical ``(search, replace)`` texts: minimal, unique in ``broken``, nonempty.

    The window starts as the changed lines and widens one context line at a
    time, below first and then above, until the search text starts at exactly
    one position in the broken module and both sides carry at least one line.
    The whole module is always such a window, so the loop terminates.
    """

    cv.refuse_when(broken == repaired, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE,
                   "an edit needs a broken module that differs from its repair")
    broken_lines = broken.splitlines(keepends=True)
    repaired_lines = repaired.splitlines(keepends=True)
    start, broken_end, repaired_end = _changed_window(broken_lines, repaired_lines)
    window: tuple[int, int] | None = (start, broken_end)
    while window is not None:
        lo, hi = window
        search = "".join(broken_lines[lo:hi])
        replace = "".join(repaired_lines[lo:repaired_end + (hi - broken_end)])
        if _unique_frame(broken, search, replace):
            return search, replace
        window = _widened(lo, hi, len(broken_lines))
    raise cv.RepairRefusal(cv.FINDING_RECORD_MALFORMED,
                           "no SEARCH window renders the repair as one framed block")


def _framed(*texts: str) -> bool:
    """Whole LF-terminated lines, none of which is a block marker."""

    return all(
        text.endswith("\n") and not _MARKER_LINES.intersection(text.splitlines(keepends=True))
        for text in texts
    )


def render_block(search: str, replace: str) -> str:
    return _SEARCH + search + _DIVIDER + replace + _REPLACE


def parse_block(completion: Any) -> tuple[str, str] | None:
    """``(search, replace)`` of a well-formed block, else ``None``.

    Well-formed means: the marker lines open, divide and close the block
    exactly once each, every content line is LF-terminated, no content line is
    a marker, and both sides are nonempty.
    """

    body = _block_body(completion)
    sides = None if body is None else _divided(body)
    return sides if _well_framed(sides) else None


def _well_framed(sides: tuple[str, str] | None) -> bool:
    return sides is not None and all(sides) and _framed(*sides)


def _block_body(completion: Any) -> list[str] | None:
    """The lines between the opening and closing markers, else ``None``."""

    if not isinstance(completion, str):
        return None
    lines = completion.splitlines(keepends=True)
    opened = len(lines) >= 4 and lines[0] == _SEARCH and lines[-1] == _REPLACE
    return lines[1:-1] if opened else None


def _divided(body: list[str]) -> tuple[str, str] | None:
    """``(search, replace)`` around the one divider when no other marker line is present."""

    dividers = [i for i, line in enumerate(body) if line == _DIVIDER]
    clean = len(dividers) == 1 and not any(line in (_SEARCH, _REPLACE) for line in body)
    if not clean:
        return None
    return "".join(body[:dividers[0]]), "".join(body[dividers[0] + 1:])


def apply_block(broken: str, completion: Any) -> tuple[str | None, str | None]:
    """``(repaired_text, None)`` when the block applies, else ``(None, leak_code)``."""

    parsed = parse_block(completion)
    if parsed is None:
        return None, cv.LEAK_EDIT_BLOCK_MALFORMED
    search, replace = parsed
    if occurrences(broken, search) != 1:
        return None, cv.LEAK_EDIT_SEARCH_NOT_UNIQUE
    return broken.replace(search, replace, 1), None


def edit_candidate(record: dict[str, Any]) -> dict[str, str]:
    """The edit rendering of a record's pair, before any leak check."""

    view = views.public_view(record)
    search, replace = search_replace(view.program_text, views.completion_of(record))
    return {"prompt": render_edit_prompt(view), "completion": render_block(search, replace)}


def edit_row(record: dict[str, Any]) -> dict[str, str]:
    """``{"prompt", "completion"}`` with a verified edit block; refused otherwise."""

    views.sft_row(record)
    row = edit_candidate(record)
    findings = edit_findings(record, row)
    cv.refuse_when(bool(findings), cv.FINDING_RECORD_MALFORMED,
                   "record fails edit view validation: " + ", ".join(findings))
    return row


def _block_findings(record: dict[str, Any], broken: str, completion: Any) -> list[str]:
    applied, code = apply_block(broken, completion)
    if applied is None:
        return [code or cv.LEAK_EDIT_BLOCK_MALFORMED]
    findings = []
    if applied == broken:
        findings.append(cv.LEAK_COMPLETION_EQUALS_BROKEN)
    predicted = record["candidate_prediction"]["predicted_repair"]["sha256"]
    verified = (views.is_positive(record)
                and cat.sha256_text(applied) == record["result"]["repaired_sha256"] == predicted)
    if not verified:
        findings.append(cv.LEAK_EDIT_DOES_NOT_APPLY)
    # Applying is not enough: the row must be the one canonical (minimal, unique) block.
    elif completion != render_block(*search_replace(broken, applied)):
        findings.append(cv.LEAK_EDIT_BLOCK_NOT_CANONICAL)
    return findings


def edit_findings(record: dict[str, Any], row: Any) -> list[str]:
    """Every declared leak code an edit row violates against its record."""

    if not isinstance(row, dict) or set(row) != views.VIEW_KEYS:
        return [cv.LEAK_VIEW_EXTRA_KEYS]
    findings = []
    view = views.public_view(record)
    if row.get("prompt") != render_edit_prompt(view):
        findings.append(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW)
    broken = record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]
    if f"```python\n{broken}```" not in str(row.get("prompt", "")):
        findings.append(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT)
    findings += views.evidence_findings(record)
    findings += _block_findings(record, broken, row.get("completion"))
    sections = [record.get(key) for key in ("scenario", "intervention", "candidate_prediction")]
    if contains_hidden_reasoning_key(row) or contains_hidden_reasoning_key(sections):
        findings.append(cv.LEAK_HIDDEN_REASONING_KEY)
    return findings


bind_import_twin(__name__)
