#!/usr/bin/env python3
"""Resolve a proposal to exactly one span of the target body, apply it, and compile the mutant.

The span must sit inside the target function's body and outside its docstring: an edit of the
doctests themselves would "break a test" without breaking the program. The explicit-offset
form is checked against ``original_text`` when both are given; the text-only form must find
``original_text`` exactly once in the module. Offsets are UTF-8 byte offsets, as in
``code_repair.mutate_span.Site``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from . import vocabulary as cv
from ._contract import bind_import_twin
from .proposal import GateProgram, GateProposal

__all__ = ["Resolved", "resolve"]

PROGRAM_FILENAME = "program.py"


@dataclass(frozen=True)
class Resolved:
    """A proposal pinned to one byte span, with the mutant text it produces."""

    start: int
    end: int
    original_text: str
    mutant_text: str


def _line_starts(data: bytes) -> list[int]:
    starts = [0]
    position = data.find(b"\n")
    while position != -1:
        starts.append(position + 1)
        position = data.find(b"\n", position + 1)
    return starts


def _body_region(program: GateProgram, data: bytes) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """``(editable span, docstring span)`` in bytes for the target function."""

    starts = _line_starts(data)
    function = next(
        node for node in ast.parse(program.text).body
        if isinstance(node, ast.FunctionDef) and node.name == program.function
    )

    def at(line: int, col: int) -> int:
        return starts[line - 1] + col

    body = list(function.body)
    docstring = None
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
            and isinstance(first.value.value, str):
        docstring = (at(first.lineno, first.col_offset), at(first.end_lineno, first.end_col_offset))
        body = body[1:]
    if not body:
        return None, docstring
    editable = (
        at(body[0].lineno, body[0].col_offset), at(function.end_lineno, function.end_col_offset),
    )
    return editable, docstring


def _locate(program: GateProgram, proposal: GateProposal, data: bytes) -> tuple[int, int] | str:
    """The byte span the proposal names, or a detail code."""

    if proposal.start_byte is not None and proposal.end_byte is not None:
        start, end = proposal.start_byte, proposal.end_byte
        if not 0 <= start < end <= len(data):
            return cv.DETAIL_SPAN_OUT_OF_RANGE
        try:
            found = data[start:end].decode("utf-8")
        except UnicodeDecodeError:
            return cv.DETAIL_SPAN_NOT_ON_BOUNDARY
        if proposal.original_text is not None and proposal.original_text != found:
            return cv.DETAIL_SPAN_TEXT_MISMATCH
        return start, end
    needle = (proposal.original_text or "").encode("utf-8")
    first = data.find(needle)
    if first == -1:
        return cv.DETAIL_SPAN_NOT_FOUND
    if data.find(needle, first + 1) != -1:
        return cv.DETAIL_SPAN_AMBIGUOUS
    return first, first + len(needle)


def _confined(span: tuple[int, int], program: GateProgram, data: bytes) -> str | None:
    editable, docstring = _body_region(program, data)
    if docstring is not None and span[0] < docstring[1] and span[1] > docstring[0]:
        return cv.DETAIL_SPAN_TOUCHES_DOCSTRING
    if editable is None or span[0] < editable[0] or span[1] > editable[1]:
        return cv.DETAIL_SPAN_OUTSIDE_BODY
    return None


def _compiles(text: str) -> bool:
    try:
        compile(text, PROGRAM_FILENAME, "exec", dont_inherit=True)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return False
    return True


def resolve(program: GateProgram, proposal: GateProposal) -> Resolved | str:
    """The resolved edit, or the ``parse_error`` detail code that rejects the proposal."""

    data = program.text.encode("utf-8")
    located = _locate(program, proposal, data)
    if isinstance(located, str):
        return located
    refusal = _confined(located, program, data)
    if refusal is not None:
        return refusal
    try:
        replacement = proposal.replacement_text.encode("utf-8")
    except UnicodeEncodeError:
        return cv.DETAIL_MALFORMED_ROW
    start, end = located
    mutant = (data[:start] + replacement + data[end:]).decode("utf-8", "strict") \
        if b"\x00" not in replacement else None
    if mutant is None or not _compiles(mutant):
        return cv.DETAIL_MUTANT_SYNTAX_ERROR
    return Resolved(start, end, data[start:end].decode("utf-8"), mutant)


bind_import_twin(__name__)
