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

from . import mutate_literals as literals
from . import vocabulary as cv
from ._contract import bind_import_twin
from .mutate_span import (
    ARITHMETIC_SWAPS, AUGMENTED_SWAPS, BINOP_CLASSES, BOOLEAN_SWAPS, BOOLOP_CLASSES,
    BOUNDARY_SWAPS, COMPARE_CLASSES, EQUALITY_SWAPS, VARIANT_DROP_NOT, VARIANT_EQUALITY,
    VARIANT_FLIP_BOOL, VARIANT_NEGATE, VARIANT_PLUS_ONE, VARIANT_SWAP, WANT_BOOL,
    WANT_NUMERIC, Edit, Owner, Site, Prepared, body_nodes, line_offsets, span_site, target,
    token_site, tokens_of,
)

__all__ = [
    "ARITHMETIC_SWAPS", "AUGMENTED_SWAPS", "BINOP_CLASSES", "BOOLEAN_SWAPS", "BOOLOP_CLASSES",
    "BOUNDARY_SWAPS", "COMPARE_CLASSES", "EQUALITY_SWAPS",
    "Site", "WANT_BOOL", "WANT_NUMERIC", "VARIANT_DROP_NOT", "VARIANT_FLIP_BOOL", "VARIANT_NEGATE",
    "VARIANT_PLUS_ONE", "body_nodes", "line_offsets", "sites", "target",
]


# --- comparison_boundary and equality (Compare) ---------------------------


def _compare_sites(node: ast.Compare, text: Prepared) -> list[Site]:
    found = []
    for index, operator in enumerate(node.ops):
        left = node.left if index == 0 else node.comparators[index - 1]
        gap = (text.span(left)[1], text.span(node.comparators[index])[0])
        token = text.token_in_gap(gap, {**BOUNDARY_SWAPS, **EQUALITY_SWAPS})
        if token is None or not isinstance(operator, COMPARE_CLASSES[token[0]]):
            continue
        if token[0] in BOUNDARY_SWAPS:
            owner = Owner(cv.OPERATOR_COMPARISON_BOUNDARY, node, text)
            edit = Edit(token[0], BOUNDARY_SWAPS[token[0]], VARIANT_SWAP, index)
        else:
            owner = Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text)
            edit = Edit(token[0], EQUALITY_SWAPS[token[0]], VARIANT_EQUALITY, index)
        found.append(token_site(owner, token, edit))
    return found


# --- arithmetic_operator (BinOp, AugAssign) ----------------------------------


def _binop_sites(node: ast.BinOp | ast.AugAssign, text: Prepared) -> list[Site]:
    if isinstance(node, ast.BinOp):
        gap, table = (text.span(node.left)[1], text.span(node.right)[0]), ARITHMETIC_SWAPS
    else:
        gap, table = (text.span(node.target)[1], text.span(node.value)[0]), AUGMENTED_SWAPS
    token = text.token_in_gap(gap, table)
    if token is None or not isinstance(node.op, BINOP_CLASSES[token[0].rstrip("=")]):
        return []
    edit = Edit(token[0], table[token[0]], VARIANT_SWAP)
    return [token_site(Owner(cv.OPERATOR_ARITHMETIC, node, text), token, edit)]


# --- boolean_condition (BoolOp, UnaryOp Not) ----------------------------------


def _boolop_sites(node: ast.BoolOp, text: Prepared) -> list[Site]:
    if len(node.values) != 2:
        return []  # an n-ary keyword swap re-associates under Python's grammar
    gap = (text.span(node.values[0])[1], text.span(node.values[1])[0])
    token = text.token_in_gap(gap, BOOLEAN_SWAPS)
    if token is None or not isinstance(node.op, BOOLOP_CLASSES[token[0]]):
        return []
    edit = Edit(token[0], BOOLEAN_SWAPS[token[0]], VARIANT_SWAP)
    return [token_site(Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text), token, edit)]


def _not_sites(node: ast.UnaryOp, text: Prepared) -> list[Site]:
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
    owner = Owner(cv.OPERATOR_BOOLEAN_CONDITION, node, text)
    return [span_site(owner, Edit(dropped, "", VARIANT_DROP_NOT), (start, end))]


def sites(text: str, function: str, want_kind: str | None = None) -> tuple[Site, ...]:
    """Every mutable site of the target function, sorted by position."""

    function_node = target(text, function)
    if function_node is None:
        return ()
    offsets = line_offsets(text)
    prepared = Prepared(text, offsets, tokens_of(text, offsets), want_kind)
    found: list[Site] = []
    for node in body_nodes(function_node):
        if isinstance(node, ast.Compare):
            found += _compare_sites(node, prepared)
        elif isinstance(node, (ast.BinOp, ast.AugAssign)):
            found += _binop_sites(node, prepared)
        elif isinstance(node, ast.BoolOp):
            found += _boolop_sites(node, prepared)
        elif isinstance(node, ast.UnaryOp):
            found += _not_sites(node, prepared)
    for node in literals.own_returns(function_node):
        found += literals.return_sites(node, prepared)
    found += literals.off_by_one_sites(function_node, prepared)
    return tuple(sorted(found, key=lambda s: (s.start, s.end, s.operator, s.variant)))


bind_import_twin(__name__)
