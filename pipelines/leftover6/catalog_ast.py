#!/usr/bin/env python3
"""Bounded literal AST extraction with source-shape and binding provenance."""

from __future__ import annotations

import ast
from typing import Any

from ._contract import bind_import_twin

from .catalog_literals import UNSET, literal_value

_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)
_STRING_BINDINGS = {ast.MatchAs: "name", ast.MatchStar: "name",
                    ast.MatchMapping: "rest", ast.ExceptHandler: "name"}


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    target, value = _assignment_pair(node)
    return (target.id, value) if isinstance(target, ast.Name) else (None, None)


def _assignment_pair(node):
    if isinstance(node, ast.AnnAssign):
        return node.target, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0], node.value
    return None, None


def module_constants(source: str, *, path: str) -> dict[str, Any]:
    tree = ast.parse(source, filename=path)
    env: dict[str, Any] = {}
    for node in _catalog_statements(tree.body):
        name, value = assignment_of(node)
        if name is None:
            _invalidate_names(env, _statement_names(node))
            if isinstance(node, _DEFINITIONS):
                env[node.name] = node
        elif value is not None:
            _bind_literal(env, name, value)
    return env


def _catalog_statements(statements):
    for node in statements:
        if isinstance(node, ast.If) and ast.dump(node.test) == _SCRIPT_GUARD:
            yield from _catalog_statements(node.orelse)
        else:
            yield node


def _bind_literal(env, name, value):
    resolved = literal_value(value, env)
    if resolved is not UNSET:
        env[name] = resolved
        return
    # Unknown assignments cannot retain an earlier literal or a mutable alias.
    _invalidate_names(env, _call_names(value))
    env.pop(name, None)
    if isinstance(value, ast.Lambda):
        env[name] = value


def _statement_names(node: ast.AST) -> list[str]:
    """Invalidate unsupported top-level uses without running publisher bodies."""
    scoped = _scope_names(node)
    if scoped is not None:
        return scoped
    return _binding_names(node) + _child_names(node)


def _binding_names(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.alias):
        return [node.asname or node.name.partition(".")[0]]
    binding = _STRING_BINDINGS.get(type(node))
    if binding:
        return list(filter(None, [getattr(node, binding)]))
    return []


def _scope_names(node: ast.AST) -> list[str] | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return [node.name, *_definition_names(node)]
    if isinstance(node, ast.ClassDef):
        return [node.name, *_child_names(node)]
    if isinstance(node, ast.Lambda):
        return _statement_names(node.args)
    return None


def _definition_names(node):
    expressions = [node.args, *node.decorator_list]
    if node.returns is not None:
        expressions.append(node.returns)
    return [name for expr in expressions for name in _statement_names(expr)]


def _child_names(node: ast.AST) -> list[str]:
    return [name for child in ast.iter_child_nodes(node) for name in _statement_names(child)]


def _mutable_identities(value: Any) -> set[int]:
    identities = {id(value)} if isinstance(value, (dict, list, set)) else set()
    for item in _contained_values(value):
        identities.update(_mutable_identities(item))
    return identities


def _contained_values(value):
    if isinstance(value, dict):
        return value.values()
    return value if isinstance(value, (list, tuple, set)) else ()


def _call_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Lambda):
        return _call_names(node.args)
    if isinstance(node, (ast.Call, ast.NamedExpr)):
        return _statement_names(node)
    return [name for child in ast.iter_child_nodes(node) for name in _call_names(child)]


def _invalidate_names(env: dict[str, Any], names: list[str]) -> None:
    """Invalidate aliases too when an unsupported operation touches mutable data."""
    if any(_unproven_code(env.get(name)) for name in names):
        env.clear()
        return
    affected = set().union(*(_mutable_identities(env.get(name)) for name in names))
    for name, value in tuple(env.items()):
        if name in names or affected.intersection(_mutable_identities(value)):
            env.pop(name)


def _unproven_code(value):
    if isinstance(value, (*_DEFINITIONS, ast.Lambda)):
        return True
    return any(_unproven_code(item) for item in _contained_values(value))


bind_import_twin(__name__)
