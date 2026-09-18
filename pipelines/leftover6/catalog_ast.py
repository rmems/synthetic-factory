#!/usr/bin/env python3
"""Bounded literal AST extraction with source-shape and binding provenance."""

from __future__ import annotations

import ast
import hashlib
from itertools import takewhile
from typing import Any

from ._contract import bind_import_twin

from .catalog_literals import UNSET, literal_value

_SCRIPT_GUARD = ast.dump(ast.parse("__name__ == '__main__'", mode="eval").body)
# Independent Git-byte SHA-256 pins for the descriptor-sealed preserve sources.
# These authorize AST text projection only, never execution or runtime equivalence.
_ARCHIVE_SOURCE_PINS = {
    "experiments/mill_gql_leftover6_r260.py": "1e45f77b8f10932e5e4395ddb8c3bc1261735ce8cd5b1797532dee6c2365a8d4",
    "experiments/ssl_r164_leftover6_mill.py": "3699c164333162c24b4ef47cb13e66ccd4495074b7233b8f68f0a7a4516c7636",
    "experiments/sbox-mill-plants-leftover6.py": "017d2f7b12c39bd566671d4f48af0dd485c65a59e55e9a0249dbecc22a0ca273",
}

_FUTURE_ANNOTATIONS = ast.dump(ast.parse("from __future__ import annotations").body[0])
_ANNOTATION_NAMES = frozenset({"str", "int", "float", "bool", "list", "dict", "tuple", "set"})


def module_constants(source: str, *, path: str) -> dict[str, Any]:
    payload = source_payload(source)
    tree = ast.parse(source, filename=path)
    _require_future_header(tree)
    archive = _ARCHIVE_SOURCE_PINS.get(path) == hashlib.sha256(payload).hexdigest()
    env: dict[str, Any] = {}
    for node in _catalog_statements(tree.body):
        if not archive:
            require_literal_statement(node, env)
        _bind_statement(env, node)
    return env


def source_payload(source: str) -> bytes:
    """Bind parsing and hashing to text whose encoding cannot be overridden."""
    if type(source) is not str:
        raise ValueError("catalog source must be a plain string")
    return source.encode("utf-8")


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
    for node in statements:
        if isinstance(node, ast.If) and ast.dump(node.test) == _SCRIPT_GUARD:
            yield from _catalog_statements(node.orelse)
        else:
            yield node


def _require_import_name(name):
    if name in {"__name__", "__builtins__"}:
        raise ValueError(f"reserved module binding {name} is not a literal catalog")


def assignment_of(node: ast.stmt) -> tuple[str | None, ast.AST | None]:
    target, value = _assignment_pair(node)
    return (target.id, value) if isinstance(target, ast.Name) else (None, None)


def _assignment_pair(node):
    if isinstance(node, ast.AnnAssign):
        return node.target, node.value
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0], node.value
    return None, None


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
