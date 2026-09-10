#!/usr/bin/env python3
"""Mutation primitives: the site record, the prepared text, and the operator tables.

A site is one byte span inside the target function's body (never its docstring) and the text
that replaces it; the inverse is the original span restored. Operator positions come from
``ast`` for operands and constants and from ``tokenize`` for the operator token in the gap
between operands (operator nodes carry no position). ``mutate_sites`` enumerates the
operator sites and ``mutate_literals`` the literal ones on top of these primitives.
"""

from __future__ import annotations

import ast
import bisect
import io
import tokenize
from dataclasses import dataclass
from typing import Any, NamedTuple

from ._contract import bind_import_twin

BOUNDARY_SWAPS = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}
EQUALITY_SWAPS = {"==": "!=", "!=": "=="}
ARITHMETIC_SWAPS = {"+": "-", "-": "+", "*": "//", "//": "%", "%": "//"}
AUGMENTED_SWAPS = {"+=": "-=", "-=": "+=", "*=": "//=", "//=": "%=", "%=": "//="}
BOOLEAN_SWAPS = {"and": "or", "or": "and"}
COMPARE_CLASSES = {
    "<": ast.Lt, "<=": ast.LtE, ">": ast.Gt, ">=": ast.GtE, "==": ast.Eq, "!=": ast.NotEq,
}
BINOP_CLASSES = {"+": ast.Add, "-": ast.Sub, "*": ast.Mult, "//": ast.FloorDiv, "%": ast.Mod}
BOOLOP_CLASSES = {"and": ast.And, "or": ast.Or}
_TOKEN_STRINGS = (
    set(BOUNDARY_SWAPS) | set(EQUALITY_SWAPS) | set(ARITHMETIC_SWAPS) | set(AUGMENTED_SWAPS)
    | set(BOOLEAN_SWAPS) | {"not"}
)
VARIANT_SWAP = "swap"
VARIANT_EQUALITY = "equality"
VARIANT_DROP_NOT = "drop_not"
VARIANT_FLIP_BOOL = "flip_bool"
VARIANT_PLUS_ONE = "plus_one"
VARIANT_MINUS_ONE = "minus_one"
VARIANT_NEGATE = "negate"
WANT_NUMERIC = "numeric"
WANT_BOOL = "bool"
OFFSET_ATOMS = (ast.Name, ast.Constant, ast.Call, ast.Attribute, ast.Subscript)
OFFSET_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
NEGATE_ATOMS = OFFSET_ATOMS + (ast.Compare, ast.UnaryOp)

__all__ = [
    "ARITHMETIC_SWAPS", "AUGMENTED_SWAPS", "BINOP_CLASSES", "BOOLEAN_SWAPS", "BOOLOP_CLASSES",
    "BOUNDARY_SWAPS", "COMPARE_CLASSES", "EQUALITY_SWAPS", "Edit", "Owner", "Site", "Prepared",
    "VARIANT_DROP_NOT", "VARIANT_EQUALITY", "VARIANT_FLIP_BOOL", "VARIANT_MINUS_ONE",
    "VARIANT_NEGATE", "VARIANT_PLUS_ONE", "VARIANT_SWAP", "WANT_BOOL", "WANT_NUMERIC",
    "body_nodes", "line_offsets", "span_site", "target", "token_site", "tokens_of",
]


@dataclass(frozen=True)
class Site:
    """One mutable span: its bytes, its position, its replacement and the owning node."""

    operator: str
    node: str
    start: int
    end: int
    lineno: int
    col_offset: int
    original_text: str
    replacement_text: str
    variant: str
    node_lineno: int
    node_col_offset: int
    node_end_lineno: int
    node_end_col_offset: int
    op_index: int = 0

    def as_json(self) -> dict[str, Any]:
        return {
            "node": self.node, "start_byte": self.start, "end_byte": self.end,
            "lineno": self.lineno, "col_offset": self.col_offset,
            "original_text": self.original_text, "replacement_text": self.replacement_text,
            "node_lineno": self.node_lineno, "node_col_offset": self.node_col_offset,
            "node_end_lineno": self.node_end_lineno,
            "node_end_col_offset": self.node_end_col_offset,
            "op_index": self.op_index,
        }


@dataclass(frozen=True)
class Prepared:
    """The module text with its line table and operator tokens, computed once."""

    text: str
    offsets: list[int]
    tokens: list[tuple[str, int, int, int, int]]
    want_kind: str | None

    def byte_at(self, lineno: int, col_bytes: int) -> int:
        return self.offsets[lineno - 1] + col_bytes

    def span(self, node: ast.AST) -> tuple[int, int]:
        return (
            self.byte_at(node.lineno, node.col_offset),
            self.byte_at(node.end_lineno, node.end_col_offset),
        )

    def segment(self, node: ast.AST) -> str:
        start, end = self.span(node)
        return self.text.encode("utf-8")[start:end].decode("utf-8")

    def token_in_gap(self, gap: tuple[int, int], wanted: dict[str, str]) -> tuple | None:
        inside = [
            t for t in self.tokens if gap[0] <= t[1] and t[2] <= gap[1] and t[0] in wanted
        ]
        return inside[0] if len(inside) == 1 else None


def line_offsets(text: str) -> list[int]:
    """Byte offset of the start of every line (index 0 is line 1); LF-only text."""

    offsets = [0]
    for line in text.split("\n")[:-1]:
        offsets.append(offsets[-1] + len(line.encode("utf-8")) + 1)
    return offsets


def tokens_of(text: str, offsets: list[int]) -> list[tuple[str, int, int, int, int]]:
    """``(string, start_byte, end_byte, lineno, col_bytes)`` for every operator-like token."""

    lines = text.split("\n")
    found = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type not in (tokenize.OP, tokenize.NAME) or token.string not in _TOKEN_STRINGS:
            continue
        row, col = token.start
        col_bytes = len(lines[row - 1][:col].encode("utf-8"))
        start = offsets[row - 1] + col_bytes
        found.append((token.string, start, start + len(token.string), row, col_bytes))
    return found


def body_nodes(function: ast.FunctionDef):
    """Every node inside the function's body statements: never decorators, defaults or annotations.

    Those run at definition time and are not the behaviour the doctests specify (Codex on #197).
    """

    pending = list(reversed(function.body))
    while pending:
        node = pending.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            children = node.body
        elif isinstance(node, ast.Lambda):
            children = [node.body]
        else:
            children = list(ast.iter_child_nodes(node))
        pending.extend(reversed(children))


def target(text: str, function: str) -> ast.FunctionDef | None:
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return node
    return None


class Edit(NamedTuple):
    """What a site replaces and with what."""

    original: str
    replacement: str
    variant: str
    op_index: int = 0


class Owner(NamedTuple):
    """The operator class, the node the edit belongs to and the prepared text."""

    operator: str
    node: ast.AST
    text: Prepared


def token_site(owner: Owner, token: tuple, edit: Edit) -> Site:
    """A site on one operator token; the token's own text is the original."""

    string, start, end, row, col_bytes = token
    node = owner.node
    return Site(
        owner.operator, type(node).__name__, start, end, row, col_bytes, string, edit.replacement,
        edit.variant, node.lineno, node.col_offset, node.end_lineno, node.end_col_offset,
        edit.op_index,
    )


def span_site(owner: Owner, edit: Edit, span: tuple[int, int]) -> Site:
    """A site on an arbitrary byte span of the owning node."""

    node = owner.node
    lineno = bisect.bisect_right(owner.text.offsets, span[0])
    col_offset = span[0] - owner.text.offsets[lineno - 1]
    return Site(
        owner.operator, type(node).__name__, span[0], span[1], lineno, col_offset,
        edit.original, edit.replacement, edit.variant, node.lineno, node.col_offset,
        node.end_lineno, node.end_col_offset, edit.op_index,
    )


bind_import_twin(__name__)
