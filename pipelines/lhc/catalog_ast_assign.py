#!/usr/bin/env python3
"""Simple assignment-target helpers for the LHC AST extract."""

from __future__ import annotations

import ast


def _ann_target_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _single_assign_target(node: ast.stmt) -> ast.AST | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0]
    return None


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    ann = _ann_target_name(node)
    if ann is not None and isinstance(node, ast.AnnAssign):
        return ann, node.value
    target = _single_assign_target(node)
    if isinstance(target, ast.Name) and isinstance(node, ast.Assign):
        return target.id, node.value
    return None, None


def assignment_names(node: ast.stmt) -> tuple[str, ...]:
    ann = _ann_target_name(node)
    if ann is not None:
        return (ann,)
    if isinstance(node, ast.Assign):
        return tuple(target.id for target in node.targets if isinstance(target, ast.Name))
    return ()


def tuple_target_names(node: ast.stmt) -> tuple[str, ...]:
    """``fa, fb = ...`` → ``('fa', 'fb')``."""

    target = _single_assign_target(node)
    if not isinstance(target, ast.Tuple):
        return ()
    names: list[str] = []
    for elt in target.elts:
        if not isinstance(elt, ast.Name):
            return ()
        names.append(elt.id)
    return tuple(names)
