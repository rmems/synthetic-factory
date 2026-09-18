#!/usr/bin/env python3
"""AST literal helpers for the sir catalog extract.

Nothing here executes source. ``ast.parse`` is the only interpreter step.
"""

from __future__ import annotations

import ast
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

from . import catalog_literals as _literals

UNSET = _literals.UNSET
literal_value = _literals.literal_value
_DYNAMIC_NAMESPACES = frozenset({"globals", "locals", "vars", "exec", "eval"})
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)
_STRING_BINDINGS = {ast.MatchAs: "name", ast.MatchStar: "name",
                    ast.MatchMapping: "rest", ast.ExceptHandler: "name"}


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
    if _DYNAMIC_NAMESPACES.intersection(names):
        raise ValueError("dynamic module namespace access is not a literal catalog")
    if "*" in names or any(_unproven_reference(env.get(name, UNSET)) for name in names):
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
    return _binding_names(node) + _child_statement_names(node)


def _binding_names(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.alias):
        return _alias_names(node)
    if isinstance(node, ast.Attribute) and node.attr in _DYNAMIC_NAMESPACES:
        return [node.attr]
    binding = _STRING_BINDINGS.get(type(node))
    return list(filter(None, [getattr(node, binding)])) if binding else []


def _alias_names(node: ast.alias) -> list[str]:
    original = node.name.partition(".")[0]
    names = [node.asname or original]
    if original in _DYNAMIC_NAMESPACES:
        names.append(original)
    return names


def _scope_names(node: ast.AST) -> list[str] | None:
    children = _evaluated_scope_nodes(node)
    if children is None:
        return None
    names = [node.name] if isinstance(node, _DEFINITIONS) else []
    return names + [name for child in children for name in _statement_names(child)]


def _evaluated_scope_nodes(node: ast.AST) -> list[ast.AST] | None:
    """Definition-time expressions execute while function and lambda bodies defer."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        evaluated = [*node.decorator_list, node.args]
        if node.returns is not None:
            evaluated.append(node.returns)
        return evaluated
    if isinstance(node, ast.ClassDef):
        return list(ast.iter_child_nodes(node))
    if isinstance(node, ast.Lambda):
        return [node.args]
    return None


def module_evaluation_nodes(node: ast.AST):
    """Walk import-time syntax, excluding deferred bodies and exact script guards."""
    yield node
    children = _evaluated_scope_nodes(node)
    if children is None:
        children = ast.iter_child_nodes(node)
    for child in _catalog_statements(children):
        yield from module_evaluation_nodes(child)


def _child_statement_names(node: ast.AST) -> list[str]:
    return [name for child in ast.iter_child_nodes(node) for name in _statement_names(child)]


def _assignment_targets(node: ast.stmt) -> list[ast.expr]:
    if isinstance(node, ast.AnnAssign):
        return [node.target]
    if isinstance(node, ast.Assign):
        return node.targets
    return []


def module_docstring(tree: ast.AST) -> str:
    if not isinstance(tree, ast.Module):
        return ""
    return ast.get_docstring(tree, clean=False) or ""


bind_import_twin(__name__)
