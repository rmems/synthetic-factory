"""The ``docstring_only`` stub: a target function's header with its body elided.

The header is the function's decorators and ``def`` through its docstring, cut
verbatim from the LF-framed broken module and located with :mod:`ast`; the
stub is that header followed by one ``...`` statement in the body's own
indentation. A target whose header cannot be cut cleanly (no docstring, no
body after it, a docstring sharing a line with code) is refused, and every
stub is re-parsed to prove nothing of the body survived and nothing of the
header was cut. Parsing only: nothing here imports or runs the module.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from . import catalog as cat
from . import vocabulary as cv
from ._contract import bind_import_twin
from .mutate_span import line_offsets

BODY_PLACEHOLDER = "..."

__all__ = ["BODY_PLACEHOLDER", "Header", "docstring_stub", "header"]


@dataclass(frozen=True)
class Header:
    """The header's verbatim text, the body's indentation, and the byte span the header
    occupies in the broken module."""

    text: str
    indent: str
    start_byte: int
    end_byte: int

    @property
    def stub(self) -> str:
        return f"{self.text}{self.indent}{BODY_PLACEHOLDER}\n"


def _not_renderable(function: str, why: str) -> cv.RepairRefusal:
    return cv.RepairRefusal(cv.FINDING_RECALL_TARGET_NOT_RENDERABLE,
                            f"function {cv.shown(function)} of the broken module {why}")


def _parsed_target(program_text: str, function: str) -> ast.FunctionDef | None:
    """The module-level ``def`` (parse only), or None when the text is not a module."""

    try:
        return cat.function_node(program_text, function)
    except (SyntaxError, ValueError, RecursionError):
        return None


def _documented_target(program_text: str, function: str) -> ast.FunctionDef:
    node = _parsed_target(program_text, function)
    if node is None:
        raise _not_renderable(function, "is not a parseable module-level def")
    if ast.get_docstring(node, clean=False) is None:
        raise _not_renderable(function, "has no docstring")
    if len(node.body) < 2:
        raise _not_renderable(function, "has no body after its docstring to elide")
    return node


def _is_placeholder(statement: ast.stmt) -> bool:
    value = statement.value if isinstance(statement, ast.Expr) else None
    return isinstance(value, ast.Constant) and value.value is Ellipsis


def _is_stub_of(stub: str, function: str, original: ast.FunctionDef) -> bool:
    """The stub parses to the target with the original docstring and the placeholder alone
    after it: nothing of the body survived and nothing of the header was cut."""

    node = _parsed_target(stub, function)
    if node is None or len(node.body) != 2:
        return False
    docstrings = (ast.get_docstring(node, clean=False), ast.get_docstring(original, clean=False))
    return docstrings[0] == docstrings[1] and _is_placeholder(node.body[1])


def header(program_text: str, function: str) -> Header:
    """The target's header in ``program_text``.

    Raises ``RepairRefusal`` (``RECALL_TARGET_NOT_RENDERABLE``) when the module does not parse,
    the target has no docstring or no body after it, or the docstring shares a line with code.
    """

    node = _documented_target(program_text, function)
    docstring = node.body[0]
    lines = program_text.split("\n")
    indent = lines[docstring.lineno - 1].encode("utf-8")[:docstring.col_offset]
    if indent.strip(b" \t"):
        raise _not_renderable(function, "does not open its docstring on a line of its own")
    first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    text = "\n".join(lines[first - 1:docstring.end_lineno]) + "\n"
    start = line_offsets(program_text)[first - 1]
    cut = Header(text, indent.decode("ascii"), start, start + len(text.encode("utf-8")))
    if not _is_stub_of(cut.stub, function, node):
        raise _not_renderable(function, "does not end its docstring on a line of its own")
    return cut


def docstring_stub(program_text: str, function: str) -> str:
    """The header followed by one ``...`` statement in the body's own indentation; refused
    like :func:`header`."""

    return header(program_text, function).stub


bind_import_twin(__name__)
