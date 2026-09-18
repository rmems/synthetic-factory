#!/usr/bin/env python3
"""AST literal helpers for the sir catalog extract.

Parsing and compiler validation never execute the recovered source.
"""

from __future__ import annotations

import ast
import hashlib
from itertools import takewhile
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin

from . import catalog_literals as _literals
from .sources import MILL_SOURCES

UNSET = _literals.UNSET
literal_value = _literals.literal_value
module_docstring = _literals.module_docstring
source_payload = _literals.source_payload
_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)

_FUTURE_ANNOTATIONS = ast.dump(ast.parse("from __future__ import annotations").body[0])
_ANNOTATION_NAMES = frozenset({"str", "int", "float", "bool", "list", "dict", "tuple", "set"})


def module_constants(source: str, *, path: str) -> dict[str, Any]:
    """Strict literal input or exact pinned archive text projection; never execute."""

    payload = source_payload(source, path=path)
    tree = _literals.validated_tree(source)
    _require_future_header(tree)
    digest = hashlib.sha256(payload).hexdigest()
    archive = any(pin.path == path and pin.sha256 == digest for pin in MILL_SOURCES)
    env: dict[str, Any] = {}
    for node in _catalog_statements(getattr(tree, "body", ())):
        if not archive:
            require_literal_statement(node, env)
        _bind_statement(env, node)
    return env


def _require_future_header(tree):
    start = int(ast.get_docstring(tree) is not None)
    allowed = set(takewhile(_is_future_import, tree.body[start:]))
    if any(_is_future_import(node) and node not in allowed for node in ast.walk(tree)):
        raise ValueError("future imports must occur in the original module header")


def _is_future_import(node):
    return isinstance(node, ast.ImportFrom) and node.module == "__future__"


def _bind_statement(env, node):
    """Project ordered bindings; unknown RHS stays UNSET, never restores builtins."""
    name, value = assignment_of(node)
    _require_import_name(name)
    if name is None:
        _bind_definition(env, node)
    elif value is not None:
        env[name] = value if isinstance(value, ast.Lambda) else literal_value(value, env)


def _bind_definition(env, node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _require_import_name(node.name)
        env[node.name] = node


def _catalog_statements(statements):
    """Defer exact script entry guards; inspect the branch used by imports."""
    for node in statements:
        if isinstance(node, ast.If) and ast.dump(node.test) == _SCRIPT_GUARD:
            yield from _catalog_statements(node.orelse)
        else:
            yield node


def _require_import_name(name: str | None) -> None:
    if name in {"__name__", "__builtins__"}:
        raise ValueError(f"reserved module binding {name} is not a literal catalog")


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    """Return ``(name, value)`` for a simple ``NAME = value`` statement."""

    targets = _assignment_targets(node)
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        return targets[0].id, node.value
    return None, None


def _assignment_targets(node: ast.stmt) -> list[ast.expr]:
    if isinstance(node, ast.AnnAssign):
        return [node.target]
    if isinstance(node, ast.Assign):
        return node.targets
    return []


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


def require_literal_statement(node, env):
    """Unpinned source permits literals and inert code definitions, never effects."""
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        _require_assignment(node, env)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        _require_deferred_definition(node, env)
    elif not _inert_statement(node):
        raise ValueError("unsupported module-time statement in literal catalog")


def _inert_statement(node):
    if isinstance(node, ast.Pass):
        return True
    if isinstance(node, ast.Expr):
        return isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    return ast.dump(node) == _FUTURE_ANNOTATIONS


def _require_assignment(node, env):
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if len(targets) != 1 or not isinstance(targets[0], ast.Name):
        raise ValueError("literal catalog assignments require a single named target")
    if isinstance(node, ast.AnnAssign):
        _require_annotation(node.annotation, env)
    if node.value is not None:
        _require_pure_value(node.value, env)


def _require_pure_value(node, env):
    if isinstance(node, ast.Lambda):
        _require_arguments(node.args, env)
    elif literal_value(node, env) is UNSET:
        raise ValueError("unproven module-time expression in literal catalog")


def _require_deferred_definition(node, env):
    if node.decorator_list or getattr(node, "type_params", ()):
        raise ValueError("definition-time decorators or type parameters are not literal")
    _require_arguments(node.args, env)
    _require_annotation(node.returns, env)


def _require_arguments(arguments, env):
    for default in filter(None, [*arguments.defaults, *arguments.kw_defaults]):
        _require_pure_value(default, env)
    args = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
            arguments.vararg, arguments.kwarg]
    for arg in filter(None, args):
        _require_annotation(arg.annotation, env)


def _require_annotation(node, env):
    if node is None or isinstance(node, ast.Constant):
        return
    if _unshadowed_annotation(node, env):
        return
    raise ValueError("unproven definition-time annotation in literal catalog")


def _unshadowed_annotation(node, env):
    if not isinstance(node, ast.Name):
        return False
    return node.id in _ANNOTATION_NAMES and node.id not in env


bind_import_twin(__name__)
