#!/usr/bin/env python3
"""Single-span text mutations of a target function, with the exact inverse repair.

A site is one span located by byte offset inside the target function's body
(never its docstring); a mutation rewrites exactly that span, so every other
byte of the module is unchanged and the repair is the original span restored.
Before a mutant is ever executed it is verified three ways: it differs from
the original as text and as an AST, it compiles, and the re-parsed target
function equals the in-memory transform of the original tree (two independent
paths must agree). The five operator classes and their transforms live in
:mod:`mutate_sites`; this module applies, repairs, verifies and draws.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass

from . import mutate_sites
from . import vocabulary as cv
from ._contract import bind_import_twin, rng

Site = mutate_sites.Site
line_offsets = mutate_sites.line_offsets
sites = mutate_sites.sites

__all__ = [
    "Mutation", "Site", "apply", "choose", "expected_dump", "line_offsets", "repair", "sites",
    "verify",
]


@dataclass(frozen=True)
class Mutation:
    site: Site
    original_text: str
    mutated_text: str


def _target(text: str, function: str) -> ast.FunctionDef | None:
    return mutate_sites.target(text, function)


def body_nodes(target: ast.FunctionDef):
    """Every node inside the function's body statements: never decorators, defaults or annotations.

    Those run at definition time and are not the behaviour the doctests specify (Codex on #197).
    """

    for statement in target.body:
        yield from ast.walk(statement)


def apply(text: str, site: Site) -> str:
    """The module text with exactly the site's span replaced."""

    data = text.encode("utf-8")
    replaced = data[: site.start] + site.replacement_text.encode("utf-8") + data[site.end :]
    return replaced.decode("utf-8")


def repair(mutated_text: str, site: Site) -> str:
    """The inverse: the original span restored on a copy of the mutated text."""

    data = mutated_text.encode("utf-8")
    end = site.start + len(site.replacement_text.encode("utf-8"))
    return (data[: site.start] + site.original_text.encode("utf-8") + data[end:]).decode("utf-8")


# --- expected transforms ---------------------------------------------------------


def _locate(module: ast.Module, site: Site) -> ast.AST | None:
    wanted = (
        site.node_lineno, site.node_col_offset, site.node_end_lineno, site.node_end_col_offset
    )
    for node in ast.walk(module):
        position = (getattr(node, "lineno", None), getattr(node, "col_offset", None),
                    getattr(node, "end_lineno", None), getattr(node, "end_col_offset", None))
        if type(node).__name__ == site.node and position == wanted:
            return node
    return None


class _ReplaceNode(ast.NodeTransformer):
    def __init__(self, old: ast.AST, new: ast.AST) -> None:
        self._old, self._new = old, new

    def visit(self, node: ast.AST) -> ast.AST:
        if node is self._old:
            return self._new
        return self.generic_visit(node)


def _transform_compare(node: ast.Compare, site: Site) -> None:
    node.ops[site.op_index] = mutate_sites.COMPARE_CLASSES[site.replacement_text]()


def _transform_binop(node: ast.AST, site: Site) -> None:
    node.op = mutate_sites.BINOP_CLASSES[site.replacement_text.rstrip("=")]()


def _transform_boolop(node: ast.BoolOp, site: Site) -> None:
    node.op = mutate_sites.BOOLOP_CLASSES[site.replacement_text]()


def _transform_return(node: ast.Return, site: Site) -> None:
    value = node.value
    if site.variant == mutate_sites.VARIANT_FLIP_BOOL:
        node.value = ast.Constant(value=not value.value)
    elif site.replacement_text.lstrip("-").isdigit():
        node.value = ast.parse(site.replacement_text, mode="eval").body
    elif site.variant == mutate_sites.VARIANT_NEGATE:
        node.value = ast.UnaryOp(op=ast.Not(), operand=value)
    else:
        operator = ast.Add() if site.variant == mutate_sites.VARIANT_PLUS_ONE else ast.Sub()
        node.value = ast.BinOp(left=value, op=operator, right=ast.Constant(value=1))


def _transform_constant(node: ast.Constant, site: Site) -> None:
    node.value = int(site.replacement_text)


def _transformed(module: ast.Module, site: Site) -> ast.Module | None:
    node = _locate(module, site)
    if node is None:
        return None
    if site.variant == mutate_sites.VARIANT_DROP_NOT:
        return _ReplaceNode(node, node.operand).visit(module)
    handlers = {
        "Compare": _transform_compare, "BinOp": _transform_binop, "AugAssign": _transform_binop,
        "BoolOp": _transform_boolop, "Return": _transform_return, "Constant": _transform_constant,
    }
    handlers[site.node](node, site)
    return module


def expected_dump(text: str, function: str, site: Site) -> str | None:
    """The target function after the site's edit on the original tree, dumped; None if lost."""

    module = _transformed(copy.deepcopy(ast.parse(text)), site)
    if module is None:
        return None
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return ast.dump(node)
    return None



def _compiles(text: str) -> bool:
    try:
        compile(text, cv.PROGRAM_FILENAME, "exec")
    except (SyntaxError, ValueError):
        return False
    return True


def verify(text: str, mutated_text: str, site: Site, function: str) -> str | None:
    """The skip code for a mutant that must not be executed, or None when it is sound.

    The rules run in order and the first that holds decides: unchanged text,
    a module that does not compile, an unchanged or missing target function,
    a touched docstring, and finally disagreement with the in-memory transform.
    """

    if mutated_text == text:
        return cv.SKIP_MUTATION_NOOP
    if not _compiles(mutated_text):
        return cv.SKIP_MUTATION_SYNTAX_ERROR
    original, mutated = _target(text, function), _target(mutated_text, function)
    dumped = None if mutated is None else ast.dump(mutated)
    rules = (
        (dumped is None or dumped == ast.dump(original), cv.SKIP_MUTATION_NOOP),
        (
            dumped is not None
            and ast.get_docstring(mutated, clean=False) != ast.get_docstring(original, clean=False),
            cv.SKIP_MUTATION_TOUCHES_DOCSTRING,
        ),
        (dumped != expected_dump(text, function, site), cv.SKIP_MUTATION_UNVERIFIABLE),
    )
    return next((code for holds, code in rules if holds), None)


def choose(stream: rng.DrawStream, candidates: tuple[Site, ...]) -> Site:
    """One seeded draw over the sorted site tuple."""

    return stream.choice(candidates)


bind_import_twin(__name__)
