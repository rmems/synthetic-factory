#!/usr/bin/env python3
"""Resolve a proposal to exactly one span of the target body, apply it, and compile the mutant.

The span must sit inside the target function's body and outside its docstring: an edit of the
doctests themselves would "break a test" without breaking the program. Where the span sits is
not enough, because a replacement can change what the text around it parses as (a dedented
line becomes a module statement). So the mutant is also parsed and compared with the original:
every module statement other than the target must be unchanged, the target's header and
docstring must be unchanged, and the target's body must not newly write to its own name,
``__doc__`` or ``__test__``. The explicit-offset form is checked against ``original_text`` when
both are given; the text-only form must find ``original_text`` exactly once in the module.
Offsets are UTF-8 byte offsets, as in ``code_repair.mutate_span.Site``.
"""

from __future__ import annotations

import ast
import functools
from collections import Counter
from dataclasses import dataclass

from . import vocabulary as cv
from ._contract import bind_import_twin
from .proposal import GateProgram, GateProposal

__all__ = ["Resolved", "candidate_problem", "resolve"]

PROGRAM_FILENAME = "program.py"
_PROTECTED_ATTRS = frozenset({"__doc__", "__test__"})


@dataclass(frozen=True)
class Resolved:
    """A proposal pinned to one byte span, with the mutant text it produces."""

    start: int
    end: int
    original_text: str
    mutant_text: str


@functools.lru_cache(maxsize=32)
def _module(text: str) -> ast.Module:
    """The parsed module, cached per text; callers never mutate the tree."""

    return ast.parse(text)


def _target_of(module: ast.Module, function: str) -> ast.FunctionDef:
    return next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function
    )


def _line_starts(data: bytes) -> list[int]:
    starts = [0]
    position = data.find(b"\n")
    while position != -1:
        starts.append(position + 1)
        position = data.find(b"\n", position + 1)
    return starts


def _docstring_node(function: ast.FunctionDef) -> ast.stmt | None:
    first = function.body[0]
    is_text = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    return first if is_text and isinstance(first.value.value, str) else None


def _body_region(
    program: GateProgram, data: bytes,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """``(editable span, docstring span)`` in bytes for the target function."""

    starts = _line_starts(data)
    function = _target_of(_module(program.text), program.function)

    def at(line: int, col: int) -> int:
        return starts[line - 1] + col

    doc = _docstring_node(function)
    docstring = None if doc is None else (
        at(doc.lineno, doc.col_offset), at(doc.end_lineno, doc.end_col_offset),
    )
    body = function.body[1:] if doc is not None else function.body
    if not body:
        return None, docstring
    editable = (
        at(body[0].lineno, body[0].col_offset), at(function.end_lineno, function.end_col_offset),
    )
    return editable, docstring


def _explicit_problem(
    start: int, end: int, original_text: str | None, data: bytes,
) -> str | None:
    if not 0 <= start < end <= len(data):
        return cv.DETAIL_SPAN_OUT_OF_RANGE
    try:
        found = data[start:end].decode("utf-8")
    except UnicodeDecodeError:
        return cv.DETAIL_SPAN_NOT_ON_BOUNDARY
    mismatch = original_text is not None and original_text != found
    return cv.DETAIL_SPAN_TEXT_MISMATCH if mismatch else None


def _explicit_span(proposal: GateProposal, data: bytes) -> tuple[int, int] | str:
    start, end = proposal.start_byte, proposal.end_byte
    problem = _explicit_problem(start, end, proposal.original_text, data)
    return problem if problem is not None else (start, end)


def _text_span(proposal: GateProposal, data: bytes) -> tuple[int, int] | str:
    needle = (proposal.original_text or "").encode("utf-8")
    first = data.find(needle)
    if first == -1:
        return cv.DETAIL_SPAN_NOT_FOUND
    if data.find(needle, first + 1) != -1:
        return cv.DETAIL_SPAN_AMBIGUOUS
    return first, first + len(needle)


def _locate(proposal: GateProposal, data: bytes) -> tuple[int, int] | str:
    """The byte span the proposal names, or a detail code."""

    if proposal.start_byte is not None and proposal.end_byte is not None:
        return _explicit_span(proposal, data)
    return _text_span(proposal, data)


def _crosses(span: tuple[int, int], region: tuple[int, int]) -> bool:
    return span[0] < region[1] and span[1] > region[0]


def _within(span: tuple[int, int], region: tuple[int, int]) -> bool:
    return region[0] <= span[0] <= span[1] <= region[1]


def _overlaps(span: tuple[int, int], region: tuple[int, int] | None) -> bool:
    return region is not None and _crosses(span, region)


def _inside(span: tuple[int, int], region: tuple[int, int] | None) -> bool:
    return region is not None and _within(span, region)


def _confined(span: tuple[int, int], program: GateProgram, data: bytes) -> str | None:
    editable, docstring = _body_region(program, data)
    if _overlaps(span, docstring):
        return cv.DETAIL_SPAN_TOUCHES_DOCSTRING
    return None if _inside(span, editable) else cv.DETAIL_SPAN_OUTSIDE_BODY


def _compiles(text: str) -> bool:
    try:
        compile(text, PROGRAM_FILENAME, "exec", dont_inherit=True)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return False
    return True


# --- what the replacement became, not just where it sits --------------------------------


def _is_target(node: ast.stmt, function: str) -> bool:
    return isinstance(node, ast.FunctionDef) and node.name == function


def _header(function: ast.FunctionDef) -> tuple:
    """Everything about the target except its body statements; the docstring is included."""

    doc = _docstring_node(function)
    return (
        function.name, ast.dump(function.args), [ast.dump(d) for d in function.decorator_list],
        None if function.returns is None else ast.dump(function.returns),
        [ast.dump(t) for t in getattr(function, "type_params", [])],
        None if doc is None else ast.dump(doc),
    )


def _same_statement(original: ast.stmt, mutant: ast.stmt, function: str) -> bool:
    if _is_target(original, function):
        return _is_target(mutant, function) and _header(original) == _header(mutant)
    return ast.dump(original) == ast.dump(mutant)


def _unchanged_outside_target(original: ast.Module, mutant: ast.Module, function: str) -> bool:
    return len(original.body) == len(mutant.body) and all(
        _same_statement(before, after, function)
        for before, after in zip(original.body, mutant.body)
    )


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _writes(node: ast.AST) -> bool:
    return isinstance(node.ctx, (ast.Store, ast.Del))


def _tamper_through(node: ast.Attribute | ast.Subscript, function: str) -> str | None:
    """A store or delete through the target's own name, or onto ``__doc__``/``__test__``."""

    if not _writes(node):
        return None
    attr = getattr(node, "attr", None)
    hit = _root_name(node) == function or attr in _PROTECTED_ATTRS
    return f"{type(node).__name__}:{attr}" if hit else None


def _tamper_name(node: ast.Name, protected: frozenset[str]) -> str | None:
    hit = _writes(node) and node.id in protected
    return f"Name:{node.id}" if hit else None


def _tamper_global(node: ast.Global | ast.Nonlocal, protected: frozenset[str]) -> str | None:
    named = next((name for name in node.names if name in protected), None)
    return None if named is None else f"{type(node).__name__}:{named}"


_REFLECTIVE_CALLS = frozenset({
    "globals", "vars", "setattr", "delattr", "exec", "eval", "compile", "__import__",
})


def _tamper_call(node: ast.Call) -> str | None:
    """A call that can rebind names or code without an AST store (``globals().update`` …)."""

    name = node.func.id if isinstance(node.func, ast.Name) else None
    return f"Call:{name}" if name in _REFLECTIVE_CALLS else None


def _tamper_of(node: ast.AST, function: str) -> str | None:
    protected = _PROTECTED_ATTRS | {function}
    checks = (
        (ast.Name, lambda found: _tamper_name(found, protected)),
        ((ast.Attribute, ast.Subscript), lambda found: _tamper_through(found, function)),
        ((ast.Global, ast.Nonlocal), lambda found: _tamper_global(found, protected)),
        (ast.Call, _tamper_call),
    )
    return next((check(node) for kinds, check in checks if isinstance(node, kinds)), None)


def _tampering(function: ast.FunctionDef) -> Counter:
    found = (_tamper_of(node, function.name) for stmt in function.body for node in ast.walk(stmt))
    return Counter(item for item in found if item is not None)


def _escapes_target_body(program: GateProgram, mutant_text: str) -> bool:
    original, mutant = _module(program.text), ast.parse(mutant_text)
    if not _unchanged_outside_target(original, mutant, program.function):
        return True
    before = _tampering(_target_of(original, program.function))
    return bool(_tampering(_target_of(mutant, program.function)) - before)


def _splice(data: bytes, span: tuple[int, int], replacement_text: str) -> str | None:
    """The mutant module text, or None when the replacement cannot be program text."""

    try:
        replacement = replacement_text.encode("utf-8")
    except UnicodeEncodeError:
        return None
    if b"\x00" in replacement:
        return None
    return (data[: span[0]] + replacement + data[span[1] :]).decode("utf-8")


def _mutant_problem(program: GateProgram, mutant: str | None) -> str | None:
    if mutant is None or not _compiles(mutant):
        return cv.DETAIL_MUTANT_SYNTAX_ERROR
    if _escapes_target_body(program, mutant):
        return cv.DETAIL_MUTANT_ESCAPES_BODY
    return None


def candidate_problem(program: GateProgram, candidate_text: str) -> str | None:
    """Why ``candidate_text`` is not a legal rewrite of the target body, or None when it is.

    The same confinement a mutant must satisfy: it compiles, and everything but the target's
    body (including its docstring and doctests) is unchanged and untampered.
    """

    return _mutant_problem(program, candidate_text)


def resolve(program: GateProgram, proposal: GateProposal) -> Resolved | str:
    """The resolved edit, or the ``parse_error`` detail code that rejects the proposal."""

    data = program.text.encode("utf-8")
    located = _locate(proposal, data)
    if isinstance(located, str):
        return located
    refusal = _confined(located, program, data)
    if refusal is not None:
        return refusal
    mutant = _splice(data, located, proposal.replacement_text)
    problem = _mutant_problem(program, mutant)
    if problem is not None:
        return problem
    return Resolved(located[0], located[1], data[located[0]:located[1]].decode("utf-8"), mutant)


bind_import_twin(__name__)
