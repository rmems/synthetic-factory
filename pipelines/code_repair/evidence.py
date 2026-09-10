"""Bounded public failure evidence derived from complete harness observations."""
from __future__ import annotations

from typing import Any
from . import catalog as cat
from . import executor as ex
from . import vocabulary as cv
from ._contract import bind_import_twin


def _example_index(row_id: str) -> int:
    return int(row_id.rpartition(":")[2])


def _entry(row: dict[str, Any], example: cat.Example) -> dict[str, Any]:
    return {
        "example_id": example.example_id, "source": example.source, "want": example.want,
        "got": row.get("got", ""), "truncated": bool(row.get("truncated", False)),
    }


def _fits(entries: list[dict[str, Any]], entry: dict[str, Any]) -> bool:
    if len(entries) >= cv.MAX_EVIDENCE_EXAMPLES:
        return False
    return len(render_evidence(entries + [entry], 0)) <= cv.MAX_EVIDENCE_CHARS


def _bounded_first(entry: dict[str, Any], omitted: int) -> bool:
    entry["truncated"] = True
    while entry["got"] and len(render_evidence([entry], omitted)) > cv.MAX_EVIDENCE_CHARS:
        excess = len(render_evidence([entry], omitted)) - cv.MAX_EVIDENCE_CHARS
        entry["got"] = entry["got"][:max(0, len(entry["got"]) - excess)]
    return len(render_evidence([entry], omitted)) <= cv.MAX_EVIDENCE_CHARS


def public_evidence(
    mutant: ex.PhaseReport | None, examples: tuple[cat.Example, ...]
) -> tuple[list[dict[str, Any]], int]:
    """The failing public examples of the mutant, bounded: ``(entries, omitted_count)``."""

    rows = () if mutant is None else mutant.public
    failing = [
        row for row in rows
        if row["status"] != cv.ROW_SUCCESS and 0 <= _example_index(row["id"]) < len(examples)
    ]
    entries: list[dict[str, Any]] = []
    for row in sorted(failing, key=lambda r: _example_index(r["id"])):
        entry = _entry(row, examples[_example_index(row["id"])])
        omitted_after = len(failing) - len(entries) - 1
        if not _fits(entries, entry) or len(render_evidence(entries + [entry], omitted_after)) > cv.MAX_EVIDENCE_CHARS:
            if entries or not _bounded_first(entry, omitted_after):
                break
        entries.append(entry)
    return entries, len(failing) - len(entries)


def _indent(text: str) -> str:
    lines = text.rstrip("\n").split("\n") if text.strip() else []
    return "\n".join(f"    {line}" for line in lines)


def _render_entry(entry: dict[str, Any]) -> str:
    want = _indent(entry["want"]) if entry["want"].strip() else "Expected nothing"
    got = _indent(entry["got"]) if entry["got"].strip() else "Got nothing"
    if entry["truncated"]:
        got += "\n    ...[truncated]"
    expected_line = "Expected:\n" if want != "Expected nothing" else ""
    got_line = "Got:\n" if got != "Got nothing" else ""
    return f"Failed example:\n{_indent(entry['source'])}\n{expected_line}{want}\n{got_line}{got}"


def render_evidence(entries: list[dict[str, Any]], omitted: int) -> str:
    """The prompt's failure block: doctest-style, from the bounded entries only."""

    parts = [_render_entry(entry) for entry in entries]
    if omitted:
        parts.append(cv.EVIDENCE_MORE.format(count=omitted))
    return "\n\n".join(parts)


bind_import_twin(__name__)
