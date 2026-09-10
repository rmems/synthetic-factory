#!/usr/bin/env python3
"""Literal sites: ``return_value`` and ``off_by_one``, on the primitives of ``mutate_span``.

* ``return_value``: a boolean constant flipped, an integer constant moved by one, a numeric
  result offset by one, a boolean result negated (the last two need the doctests' want kind).
* ``off_by_one``: an integer literal that is the direct operand of ``range()``, a slice, a
  subscript or a comparison, moved by one (never below zero, never a negated literal).
"""

from __future__ import annotations

import ast

from . import vocabulary as cv
from ._contract import bind_import_twin
from .mutate_span import (
    NEGATE_ATOMS, OFFSET_ATOMS, OFFSET_BINOPS, VARIANT_FLIP_BOOL, VARIANT_MINUS_ONE,
    VARIANT_NEGATE, VARIANT_PLUS_ONE, WANT_BOOL, WANT_NUMERIC, Edit, Owner, Site, Prepared,
    body_nodes, span_site,
)

__all__ = ["off_by_one_sites", "own_returns", "return_sites"]


# --- return_value (Return of the target function) ------------------------------


def _is_int_constant(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
        return False
    return isinstance(node.value, int)


def _decimal_int(node: ast.AST, text: Prepared) -> int | None:
    """The value of a plain decimal integer literal (``7``, never ``0x7``, ``True`` or ``-7``)."""

    if not _is_int_constant(node):
        return None
    return node.value if text.segment(node) == str(node.value) else None


def _signed_int(node: ast.AST, text: Prepared) -> int | None:
    """A decimal integer literal, possibly under one unary minus, as its value."""

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _decimal_int(node.operand, text)
        return None if inner is None or text.segment(node) != f"-{inner}" else -inner
    return _decimal_int(node, text)


def _is_constant_of(node: ast.AST, kind: type) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, kind)


def return_sites(node: ast.Return, text: Prepared) -> list[Site]:
    value = node.value
    if value is None or _is_constant_of(value, type(None)):
        return []
    owner = Owner(cv.OPERATOR_RETURN_VALUE, node, text)
    span = text.span(value)
    if _is_constant_of(value, bool):
        edit = Edit(str(value.value), str(not value.value), VARIANT_FLIP_BOOL)
        return [span_site(owner, edit, span)]
    signed = _signed_int(value, text)
    if signed is not None:
        return [
            span_site(owner, Edit(str(signed), str(signed + 1), VARIANT_PLUS_ONE), span),
            span_site(owner, Edit(str(signed), str(signed - 1), VARIANT_MINUS_ONE), span),
        ]
    return _wrapped_return_sites(owner, value, span)


def _offset_operand(value: ast.AST, segment: str) -> str:
    """The value as an operand of ``+ 1``: parenthesised unless it already binds tighter."""

    atomic = isinstance(value, OFFSET_ATOMS) or (
        isinstance(value, ast.BinOp) and isinstance(value.op, OFFSET_BINOPS)
    )
    return segment if atomic else f"({segment})"


def _wrapped_return_sites(owner: Owner, value: ast.AST, span: tuple[int, int]) -> list[Site]:
    """``return e`` becomes ``return e + 1`` / ``e - 1`` (numeric) or ``return not e`` (bool)."""

    segment = owner.text.segment(value)
    if owner.text.want_kind == WANT_NUMERIC:
        inner = _offset_operand(value, segment)
        return [
            span_site(owner, Edit(segment, f"{inner} + 1", VARIANT_PLUS_ONE), span),
            span_site(owner, Edit(segment, f"{inner} - 1", VARIANT_MINUS_ONE), span),
        ]
    if owner.text.want_kind == WANT_BOOL:
        inner = segment if isinstance(value, NEGATE_ATOMS) else f"({segment})"
        return [span_site(owner, Edit(segment, f"not {inner}", VARIANT_NEGATE), span)]
    return []


def _constant_offset_sites(owner: Owner, allow_minus: bool) -> list[Site]:
    """``k`` -> ``k+1`` and, when it stays non-negative, ``k-1`` on the owner's constant."""

    value = owner.node.value
    span = owner.text.span(owner.node)
    found = [span_site(owner, Edit(str(value), str(value + 1), VARIANT_PLUS_ONE), span)]
    if allow_minus and value >= 1:
        found.append(span_site(owner, Edit(str(value), str(value - 1), VARIANT_MINUS_ONE), span))
    return found


# --- off_by_one (integer literals in ranges, slices, subscripts, comparisons) ----


def _parents(function: ast.FunctionDef) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(function) for child in ast.iter_child_nodes(node)}


def _is_range_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        return False
    return node.func.id == "range"


def _is_boundary(node: ast.AST, child: ast.AST) -> bool:
    """A parent under which an integer literal is a boundary worth moving by one.

    The literal must be the operand itself: an argument of ``range``, a bound of a slice,
    the index of a subscript or a side of a comparison. A literal buried deeper, such as
    ``helper(1) < limit``, is not a boundary (Greptile and CodeAnt on #202).
    """

    if isinstance(node, ast.Subscript):
        return child is node.slice
    if _is_range_call(node):
        return any(child is argument for argument in node.args)
    if isinstance(node, ast.Slice):
        return child in (node.lower, node.upper, node.step)
    if isinstance(node, ast.Compare):
        return child is node.left or any(child is c for c in node.comparators)
    return False


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
    if not chain:
        return False, False
    parent, child = chain[0]
    negated = isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub)
    if negated:
        # A signed boundary would need its whole literal rewritten and its direction re-read;
        # it is not a site (Codex on #202).
        return False, True
    return _is_boundary(parent, child), False


def off_by_one_sites(function: ast.FunctionDef, text: Prepared) -> list[Site]:
    parents = _parents(function)
    found = []
    for node in body_nodes(function):
        if _decimal_int(node, text) is None:
            continue
        eligible, negated = _off_by_one_context(node, parents)
        if eligible:
            found += _constant_offset_sites(Owner(cv.OPERATOR_OFF_BY_ONE, node, text), not negated)
    return found


# --- enumeration ----------------------------------------------------------------


def own_returns(function: ast.FunctionDef) -> list[ast.Return]:
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


bind_import_twin(__name__)
