#!/usr/bin/env python3
"""What the sandboxed harness hands its child, and what it keeps back.

The parent reads the target function's doctests from the program text without running it
(``ast`` for the docstring, ``doctest.DocTestParser`` for the examples). The child is given the
program with that docstring replaced by an empty string, and each example's source, nothing
else. The expected outputs stay with the parent, which compares them itself
(``sandboxed_judge.py``), so no program can report a pass without producing the output.

The target is the last top-level ``def`` of that name, which is the object ``getattr`` returns
after the module runs, and its docstring is read as the compiler stores it (``__doc__``), not as
the AST literal, so examples match ``DocTestFinder``'s on every Python version. Examples marked ``# doctest: +SKIP`` are dropped, as ``DocTestRunner``
skips them. The empty-string replacement keeps the line count, so line numbers in the child
match the original program.
"""

from __future__ import annotations

import ast
import doctest
import json
import re
import types
from dataclasses import dataclass

from . import _sandboxed_record as record
from . import vocabulary as cv
from ._contract import bind_import_twin

MAX_EXAMPLES = record.MAX_EXAMPLES
_LINE_BREAK = re.compile(rb"\r\n|\r|\n")

__all__ = ["MAX_EXAMPLES", "Plan", "plan_for"]


@dataclass(frozen=True)
class Plan:
    """The program text the child loads, the examples it runs, or why nothing should run."""

    text: str
    examples: tuple[doctest.Example, ...] = ()
    outcome: str = ""
    detail: str = ""

    def child_input(self, key: bytes) -> bytes:
        """The child's whole stdin: the run key and each example's source, never its output."""

        sources = [example.source for example in self.examples]
        return json.dumps({"key": key.hex(), "sources": sources}).encode("ascii")


def _parsed(text: str) -> ast.Module | None:
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return None


def _target(module: ast.Module, function: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    kinds = (ast.FunctionDef, ast.AsyncFunctionDef)
    found = [node for node in module.body if isinstance(node, kinds) and node.name == function]
    return found[-1] if found else None


def _docstring_node(module: ast.Module | None, function: str) -> ast.Expr | None:
    target = None if module is None else _target(module, function)
    first = None if target is None else target.body[0]
    is_text = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    return first if is_text and isinstance(first.value.value, str) else None


def _line_starts(data: bytes) -> list[int]:
    return [0, *(match.end() for match in _LINE_BREAK.finditer(data))]


def _redacted(text: str, node: ast.Expr) -> str:
    """``text`` with the docstring node replaced by ``("")`` spanning the same lines."""

    data = text.encode("utf-8")
    starts = _line_starts(data)
    begin = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    filler = b'(""' + b"\n" * (node.end_lineno - node.lineno) + b")"
    return (data[:begin] + filler + data[end:]).decode("utf-8")


def _withheld(text: str, function: str) -> bool:
    """True when ``text`` parses and its target's docstring is the empty string."""

    node = _docstring_node(_parsed(text), function)
    return node is not None and node.value.value == ""


def _skipped(example: doctest.Example) -> bool:
    return bool(example.options.get(doctest.SKIP, False))


def _compiled_docstring(node: ast.Expr) -> str:
    """The docstring as the compiler stores it, which is what ``DocTestFinder`` reads.

    Since Python 3.13 the compiler strips common indentation from docstrings, so the AST
    literal differs whenever an example starts on the docstring's first line. The docstring
    node alone is compiled into an empty function and read from the code object; nothing is
    executed.
    """

    stub = ast.Module(body=[ast.FunctionDef(
        name="_", args=ast.arguments(), body=[node], decorator_list=[],
    )], type_ignores=[])
    module = compile(ast.fix_missing_locations(stub), "<docstring>", "exec", dont_inherit=True)
    code = next(item for item in module.co_consts if isinstance(item, types.CodeType))
    return types.FunctionType(code, {}).__doc__ or ""


def plan_for(program_text: str, function: str) -> Plan:
    """The plan for one run; a program that cannot be planned runs as is with no examples."""

    node = _docstring_node(_parsed(program_text), function)
    if node is None:  # unparsable, no such target or no docstring: the child reports the rest
        return Plan(program_text)
    try:
        found = doctest.DocTestParser().get_examples(_compiled_docstring(node), function)
    except ValueError:  # what DocTestFinder raises for the same docstring
        return Plan(program_text, outcome=cv.OUTCOME_LOAD_ERROR, detail="ValueError")
    examples = tuple(example for example in found if not _skipped(example))
    if len(examples) > MAX_EXAMPLES:
        return Plan(program_text, outcome=cv.OUTCOME_CRASHED, detail="too_many_examples")
    text = _redacted(program_text, node)
    if not _withheld(text, function):
        return Plan(program_text, outcome=cv.OUTCOME_CRASHED, detail="redaction")
    return Plan(text, examples)


bind_import_twin(__name__)
