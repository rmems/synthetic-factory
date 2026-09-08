#!/usr/bin/env python3
"""Site tables of the five mutation operators and their in-memory transforms.

A site is one byte span inside the target function's body (never its
docstring) and the text that replaces it; the inverse is the original span
restored. Every operator also states the edit it expects on the original tree,
so :mod:`mutate` can apply that edit to the original tree, re-parse the
rewritten text and demand agreement between the two independent paths before a
mutant executes. Operator positions come
from ``ast`` for operands and constants, and from ``tokenize`` for the
operator token in the gap between operands (operator nodes carry no position).

Operators (the brief's five classes):

* ``comparison_boundary``: ``<`` <-> ``<=``, ``>`` <-> ``>=``.
* ``arithmetic_operator``: ``+`` <-> ``-``, ``*`` -> ``//``, ``//`` -> ``%``, ``%`` -> ``//``,
  also augmented assignments.
* ``boolean_condition``: binary ``and`` <-> ``or``, ``not x`` -> ``x``, ``==`` <-> ``!=``.
* ``return_value``: a boolean constant flipped, an integer constant moved by one, a numeric
  result offset by one, a boolean result negated (the last two need the doctests' want kind).
* ``off_by_one``: an integer literal under ``range()``, a slice, a subscript or a comparison,
  moved by one (never below zero).
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from typing import Any, NamedTuple

from . import vocabulary as cv
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
_OFFSET_ATOMS = (ast.Name, ast.Constant, ast.Call, ast.Attribute, ast.Subscript)
_OFFSET_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_NEGATE_ATOMS = _OFFSET_ATOMS + (ast.Compare, ast.UnaryOp)

__all__ = [
    "ARITHMETIC_SWAPS", "AUGMENTED_SWAPS", "BINOP_CLASSES", "BOOLEAN_SWAPS", "BOOLOP_CLASSES",
    "BOUNDARY_SWAPS", "COMPARE_CLASSES", "EQUALITY_SWAPS",
    "Site", "WANT_BOOL", "WANT_NUMERIC", "VARIANT_DROP_NOT", "VARIANT_FLIP_BOOL", "VARIANT_NEGATE",
    "VARIANT_PLUS_ONE", "line_offsets", "sites", "target",
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
class _Text:
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


def _tokens(text: str, offsets: list[int]) -> list[tuple[str, int, int, int, int]]:
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


def target(text: str, function: str) -> ast.FunctionDef | None:
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return node
    return None


class _Edit(NamedTuple):
    """What a site replaces and with what."""

    original: str
    replacement: str
    variant: str
    op_index: int = 0


class _Owner(NamedTuple):
    """The operator class, the node the edit belongs to and the prepared text."""

    operator: str
    node: ast.AST
    text: _Text


def _token_site(owner: _Owner, token: tuple, edit: _Edit) -> Site:
    """A site on one operator token; the token's own text is the original."""

    string, start, end, row, col_bytes = token
    node = owner.node
    return Site(
        owner.operator, type(node).__name__, start, end, row, col_bytes, string, edit.replacement,
        edit.variant, node.lineno, node.col_offset, node.end_lineno, node.end_col_offset,
        edit.op_index,
    )


def _span_site(owner: _Owner, edit: _Edit, span: tuple[int, int]) -> Site:
    """A site on an arbitrary byte span of the owning node."""

    node = owner.node
    return Site(
        owner.operator, type(node).__name__, span[0], span[1], node.lineno, node.col_offset,
        edit.original, edit.replacement, edit.variant, node.lineno, node.col_offset,
        node.end_lineno, node.end_col_offset, edit.op_index,
    )


# --- comparison_boundary and equality (Compare) ---------------------------


def _compare_sites(node: ast.Compare, text: _Text) -> list[Site]:
    found = []
    for index, operator in enumerate(node.ops):
        left = node.left if index == 0 else node.comparators[index - 1]
        gap = (text.span(left)[1], text.span(node.comparators[index])[0])
        token = text.token_in_gap(gap, {**BOUNDARY_SWAPS, **EQUALITY_SWAPS})
        if token is None or not isinstance(operator, COMPARE_CLASSES[token[0]]):
            continue
        if token[0] in BOUNDARY_SWAPS:
            owner = _Owner(cv.OPERATOR_COMPARISON_BOUNDARY, node, text)
            edit = _Edit(token[0], BOUNDARY_SWAPS[token[0]], VARIANT_SWAP, index)
        else:
            owner = _Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text)
            edit = _Edit(token[0], EQUALITY_SWAPS[token[0]], VARIANT_EQUALITY, index)
        found.append(_token_site(owner, token, edit))
    return found


# --- arithmetic_operator (BinOp, AugAssign) ----------------------------------


def _binop_sites(node: ast.BinOp | ast.AugAssign, text: _Text) -> list[Site]:
    if isinstance(node, ast.BinOp):
        gap, table = (text.span(node.left)[1], text.span(node.right)[0]), ARITHMETIC_SWAPS
    else:
        gap, table = (text.span(node.target)[1], text.span(node.value)[0]), AUGMENTED_SWAPS
    token = text.token_in_gap(gap, table)
    if token is None or not isinstance(node.op, BINOP_CLASSES[token[0].rstrip("=")]):
        return []
    edit = _Edit(token[0], table[token[0]], VARIANT_SWAP)
    return [_token_site(_Owner(cv.OPERATOR_ARITHMETIC, node, text), token, edit)]


# --- boolean_condition (BoolOp, UnaryOp Not) ----------------------------------


def _boolop_sites(node: ast.BoolOp, text: _Text) -> list[Site]:
    if len(node.values) != 2:
        return []  # an n-ary keyword swap re-associates under Python's grammar
    gap = (text.span(node.values[0])[1], text.span(node.values[1])[0])
    token = text.token_in_gap(gap, BOOLEAN_SWAPS)
    if token is None or not isinstance(node.op, BOOLOP_CLASSES[token[0]]):
        return []
    edit = _Edit(token[0], BOOLEAN_SWAPS[token[0]], VARIANT_SWAP)
    return [_token_site(_Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text), token, edit)]


def _not_sites(node: ast.UnaryOp, text: _Text) -> list[Site]:
    if not isinstance(node.op, ast.Not):
        return []
    start = text.span(node)[0]
    data = text.text.encode("utf-8")
    if data[start:start + 3] != b"not":
        return []
    end = start + 3
    while end < len(data) and data[end:end + 1] in (b" ", b"\t"):
        end += 1  # the keyword and the blanks after it go; a parenthesis or operand stays
    dropped = data[start:end].decode("utf-8")
    owner = _Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text)
    return [_span_site(owner, _Edit(dropped, "", VARIANT_DROP_NOT), (start, end))]


# --- return_value (Return of the target function) ------------------------------


def _is_int_constant(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return False
    return isinstance(node.value, int)


def _decimal_int(node: ast.AST, text: _Text) -> int | None:
    """The value of a plain decimal integer literal (``7``, never ``0x7``, ``True`` or ``-7``)."""

    if not _is_int_constant(node):
        return None
    return node.value if text.segment(node) == str(node.value) else None


def _signed_int(node: ast.AST, text: _Text) -> int | None:
    """A decimal integer literal, possibly under one unary minus, as its value."""

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _decimal_int(node.operand, text)
        return None if inner is None or text.segment(node) != f"-{inner}" else -inner
    return _decimal_int(node, text)


def _is_constant_of(node: ast.AST, kind: type) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, kind)


def _return_sites(node: ast.Return, text: _Text) -> list[Site]:
    value = node.value
    if value is None or _is_constant_of(value, type(None)):
        return []
    owner = _Owner(cv.OPERATOR_RETURN_VALUE, node, text)
    span = text.span(value)
    if _is_constant_of(value, bool):
        edit = _Edit(str(value.value), str(not value.value), VARIANT_FLIP_BOOL)
        return [_span_site(owner, edit, span)]
    signed = _signed_int(value, text)
    if signed is not None:
        return [
            _span_site(owner, _Edit(str(signed), str(signed + 1), VARIANT_PLUS_ONE), span),
            _span_site(owner, _Edit(str(signed), str(signed - 1), VARIANT_MINUS_ONE), span),
        ]
    return _wrapped_return_sites(owner, value, span)


def _offset_operand(value: ast.AST, segment: str) -> str:
    """The value as an operand of ``+ 1``: parenthesised unless it already binds tighter."""

    atomic = isinstance(value, _OFFSET_ATOMS) or (
        isinstance(value, ast.BinOp) and isinstance(value.op, _OFFSET_BINOPS)
    )
    return segment if atomic else f"({segment})"


def _wrapped_return_sites(owner: _Owner, value: ast.AST, span: tuple[int, int]) -> list[Site]:
    """``return e`` becomes ``return e + 1`` / ``e - 1`` (numeric) or ``return not e`` (bool)."""

    segment = owner.text.segment(value)
    if owner.text.want_kind == WANT_NUMERIC:
        inner = _offset_operand(value, segment)
        return [
            _span_site(owner, _Edit(segment, f"{inner} + 1", VARIANT_PLUS_ONE), span),
            _span_site(owner, _Edit(segment, f"{inner} - 1", VARIANT_MINUS_ONE), span),
        ]
    if owner.text.want_kind == WANT_BOOL:
        inner = segment if isinstance(value, _NEGATE_ATOMS) else f"({segment})"
        return [_span_site(owner, _Edit(segment, f"not {inner}", VARIANT_NEGATE), span)]
    return []


def _constant_offset_sites(owner: _Owner, allow_minus: bool) -> list[Site]:
    """``k`` -> ``k+1`` and, when it stays non-negative, ``k-1`` on the owner's constant."""

    value = owner.node.value
    span = owner.text.span(owner.node)
    found = [_span_site(owner, _Edit(str(value), str(value + 1), VARIANT_PLUS_ONE), span)]
    if allow_minus and value >= 1:
        found.append(_span_site(owner, _Edit(str(value), str(value - 1), VARIANT_MINUS_ONE), span))
    return found


# --- off_by_one (integer literals in ranges, slices, subscripts, comparisons) ----


def _parents(function: ast.FunctionDef) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(function) for child in ast.iter_child_nodes(node)}


def _is_range_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return node.func.id == "range"


def _is_boundary(node: ast.AST, child: ast.AST) -> bool:
    """An ancestor under which an integer literal is a boundary worth moving by one."""

    if isinstance(node, ast.Subscript):
        return child is node.slice
    return _is_range_call(node) or isinstance(node, (ast.Slice, ast.Compare))


def _ancestors(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> list[tuple[ast.AST, ast.AST]]:
    """``(ancestor, child)`` pairs from the node up to (not including) its statement."""

    chain, child, ancestor = [], node, parents.get(node)
    while ancestor is not None and not isinstance(ancestor, ast.stmt):
        chain.append((ancestor, child))
        child, ancestor = ancestor, parents.get(ancestor)
    return chain


def _off_by_one_context(constant: ast.AST, parents: dict[ast.AST, ast.AST]) -> tuple[bool, bool]:
    """``(eligible, negated)``: an ancestor that makes the literal a boundary, and a unary minus."""

    chain = _ancestors(constant, parents)
    if any(isinstance(node, (ast.JoinedStr, ast.FormattedValue)) for node, _child in chain):
        return False, False
    negated = any(
        isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and child is constant
        for node, child in chain
    )
    return any(_is_boundary(node, child) for node, child in chain), negated


def _off_by_one_sites(function: ast.FunctionDef, text: _Text) -> list[Site]:
    parents = _parents(function)
    found = []
    for node in ast.walk(function):
        if _decimal_int(node, text) is None:
            continue
        eligible, negated = _off_by_one_context(node, parents)
        if eligible:
            found += _constant_offset_sites(_Owner(cv.OPERATOR_OFF_BY_ONE, node, text), not negated)
    return found


# --- enumeration ----------------------------------------------------------------


def _own_returns(function: ast.FunctionDef) -> list[ast.Return]:
    """Return statements of the function itself, not of a nested def or lambda."""

    found: list[ast.Return] = []
    pending: list[ast.AST] = list(function.body)
    while pending:
        node = pending.pop()
        if isinstance(node, ast.Return):
            found.append(node)
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            pending.extend(ast.iter_child_nodes(node))
    return found


def sites(text: str, function: str, want_kind: str | None = None) -> tuple[Site, ...]:
    """Every mutable site of the target function, sorted by position."""

    function_node = target(text, function)
    if function_node is None:
        return ()
    offsets = line_offsets(text)
    prepared = _Text(text, offsets, _tokens(text, offsets), want_kind)
    found: list[Site] = []
    for node in ast.walk(function_node):
        if isinstance(node, ast.Compare):
            found += _compare_sites(node, prepared)
        elif isinstance(node, (ast.BinOp, ast.AugAssign)):
            found += _binop_sites(node, prepared)
        elif isinstance(node, ast.BoolOp):
            found += _boolop_sites(node, prepared)
        elif isinstance(node, ast.UnaryOp):
            found += _not_sites(node, prepared)
    for node in _own_returns(function_node):
        found += _return_sites(node, prepared)
    found += _off_by_one_sites(function_node, prepared)
    return tuple(sorted(found, key=lambda s: (s.start, s.end, s.operator, s.variant)))


bind_import_twin(__name__)
