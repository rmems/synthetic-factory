#!/usr/bin/env python3
"""AST literal helpers for the sir catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping
from typing import Any

UNSET = object()
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)


def module_constants(tree: ast.AST) -> dict[str, Any]:
    """Resolve assignments in order, retaining ``UNSET`` for unknown bindings."""

    env: dict[str, Any] = {}
    for node in _catalog_statements(getattr(tree, "body", ())):
        name, value = assignment_of(node)
        if name is None:
            _invalidate_names(env, assignment_names(node))
            if isinstance(node, _DEFINITIONS):
                env[node.name] = node
        elif value is not None:
            env[name] = _assignment_value(value, env)
    return env


def _catalog_statements(statements):
    """Defer exact script entry guards; inspect the branch used by imports."""
    for node in statements:
        if isinstance(node, ast.If) and ast.dump(node.test) == _SCRIPT_GUARD:
            yield from _catalog_statements(node.orelse)
        else:
            yield node


def _assignment_value(value: ast.AST, env: dict[str, Any]) -> Any:
    resolved = literal_value(value, env)
    if resolved is UNSET:
        _invalidate_names(env, _statement_names(value))
    return value if isinstance(value, ast.Lambda) else resolved


def _invalidate_names(env: dict[str, Any], names: list[str]) -> None:
    if any(_unproven_reference(env.get(name, UNSET)) for name in names):
        # Containers can share mutable values or reference deferred local code.
        # Refuse the environment rather than interpreting mutation or call flow.
        names = list(set(env).union(names))
    for name in names:
        env[name] = UNSET


def _unproven_reference(value: Any) -> bool:
    if isinstance(value, (list, dict, set, ast.Lambda, *_DEFINITIONS)):
        return True
    return isinstance(value, tuple) and any(_unproven_reference(item) for item in value)


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    targets = _assignment_targets(node)
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        return targets[0].id, node.value
    return None, None


def assignment_names(node: ast.stmt) -> list[str]:
    """Invalidate unsupported writes or uses without evaluating their control flow."""
    targets = _assignment_targets(node) or [node]
    return [name for target in targets for name in _statement_names(target)]


def _statement_names(node: ast.AST) -> list[str]:
    scoped = _scope_names(node)
    if scoped is not None:
        return scoped
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.alias):
        return [node.asname or node.name.partition(".")[0]]
    return _child_statement_names(node)


def _scope_names(node: ast.AST) -> list[str] | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        evaluated = [node.args, *node.decorator_list]
        if node.returns is not None:
            evaluated.append(node.returns)
        return [node.name, *(_name for child in evaluated for _name in _statement_names(child))]
    if isinstance(node, ast.ClassDef):
        return [node.name, *_child_statement_names(node)]
    if isinstance(node, ast.Lambda):
        return _statement_names(node.args)
    return None


def _child_statement_names(node: ast.AST) -> list[str]:
    return [name for child in ast.iter_child_nodes(node) for name in _statement_names(child)]


def _assignment_targets(node: ast.stmt) -> list[ast.expr]:
    if isinstance(node, ast.AnnAssign):
        return [node.target]
    if isinstance(node, ast.Assign):
        return node.targets
    return []


def literal_value(node: ast.AST | None, env: Mapping[str, Any] | None = None) -> Any:
    """Resolve constants, names, and literal containers; else ``UNSET``."""

    bound = env or {}
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, UNSET)
    if isinstance(node, ast.UnaryOp):
        return _negative_number(node, bound)
    return _container_value(node, bound)


def _negative_number(node: ast.UnaryOp, bound: Mapping[str, Any]) -> Any:
    if not isinstance(node.op, ast.USub):
        return UNSET
    inner = literal_value(node.operand, bound)
    return -inner if isinstance(inner, (int, float)) else UNSET


def _container_value(node: ast.AST | None, bound: Mapping[str, Any]) -> Any:
    constructors = {ast.Tuple: tuple, ast.List: list, ast.Set: set}
    constructor = constructors.get(type(node))
    if constructor is not None:
        return _sequence(node.elts, bound, constructor)
    if isinstance(node, ast.Dict):
        return _mapping(node, bound)
    return UNSET


def _sequence(elts: Iterable[ast.AST | None], env: Mapping[str, Any], ctor):
    values: list[Any] = []
    for elt in elts:
        item = literal_value(elt, env)
        if item is UNSET:
            return UNSET
        values.append(item)
    return ctor(values)


def _mapping(node: ast.Dict, env: Mapping[str, Any]) -> Any:
    out: dict[Any, Any] = {}
    for nodes in zip(node.keys, node.values, strict=True):
        pair = _sequence(nodes, env, tuple)
        if pair is UNSET:
            return UNSET
        key, value = pair
        out[key] = value
    return out


def module_docstring(tree: ast.AST) -> str:
    if not isinstance(tree, ast.Module):
        return ""
    return ast.get_docstring(tree, clean=False) or ""
