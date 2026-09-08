#!/usr/bin/env python3
"""Single-span text mutations of a target function, with the exact inverse repair.

A site is one operator token located by byte offset inside the target
function's body (never its docstring); a mutation rewrites exactly that span,
so every other byte of the module is unchanged and the repair is the original
span restored. Before a mutant is ever executed it is verified three ways: it
differs from the original as text and as an AST, it compiles, and the
re-parsed target function equals the in-memory transform of the original tree
(two independent paths must agree). S1 carries one operator class,
``comparison_boundary``; the others join in S2 through the same site table.
"""

from __future__ import annotations

import ast
import copy
import io
import tokenize
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, rng

BOUNDARY_SWAPS = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}
_OPERATOR_CLASSES = {"<": ast.Lt, "<=": ast.LtE, ">": ast.Gt, ">=": ast.GtE}
VARIANT_SWAP = "swap"

__all__ = [
    "BOUNDARY_SWAPS", "Mutation", "Site", "apply", "body_nodes", "choose", "line_offsets", "repair",
    "sites", "verify",
]


@dataclass(frozen=True)
class Site:
    """One mutable operator token: its byte span, its position and its replacement."""

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
    op_index: int

    def as_json(self) -> dict[str, Any]:
        return {
            "node": self.node, "start_byte": self.start, "end_byte": self.end,
            "lineno": self.lineno, "col_offset": self.col_offset,
            "original_text": self.original_text, "replacement_text": self.replacement_text,
            "node_lineno": self.node_lineno, "node_col_offset": self.node_col_offset,
            "op_index": self.op_index,
        }


@dataclass(frozen=True)
class Mutation:
    site: Site
    original_text: str
    mutated_text: str


def line_offsets(text: str) -> list[int]:
    """Byte offset of the start of every line (index 0 is line 1); LF-only text."""

    offsets = [0]
    for line in text.split("\n")[:-1]:
        offsets.append(offsets[-1] + len(line.encode("utf-8")) + 1)
    return offsets


def _byte_at(offsets: list[int], lineno: int, col_bytes: int) -> int:
    return offsets[lineno - 1] + col_bytes


def _target(text: str, function: str) -> ast.FunctionDef | None:
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return node
    return None


def _operator_tokens(text: str, offsets: list[int]) -> list[tuple[str, int, int, int, int]]:
    """``(string, start_byte, end_byte, lineno, col_bytes)`` for every OP token in ``text``."""

    lines = text.split("\n")
    found = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.OP or token.string not in BOUNDARY_SWAPS:
            continue
        row, col = token.start
        col_bytes = len(lines[row - 1][:col].encode("utf-8"))
        start = _byte_at(offsets, row, col_bytes)
        found.append((token.string, start, start + len(token.string), row, col_bytes))
    return found


def _gap(node: ast.Compare, index: int, offsets: list[int]) -> tuple[int, int]:
    left = node.left if index == 0 else node.comparators[index - 1]
    right = node.comparators[index]
    return (
        _byte_at(offsets, left.end_lineno, left.end_col_offset),
        _byte_at(offsets, right.lineno, right.col_offset),
    )


def _compare_sites(node: ast.Compare, tokens: list, offsets: list[int]) -> list[Site]:
    found = []
    for index, operator in enumerate(node.ops):
        gap_start, gap_end = _gap(node, index, offsets)
        inside = [t for t in tokens if gap_start <= t[1] and t[2] <= gap_end]
        if len(inside) != 1 or not isinstance(operator, _OPERATOR_CLASSES[inside[0][0]]):
            continue
        string, start, end, row, col_bytes = inside[0]
        found.append(Site(
            cv.OPERATOR_COMPARISON_BOUNDARY, "Compare", start, end, row, col_bytes, string,
            BOUNDARY_SWAPS[string], VARIANT_SWAP, node.lineno, node.col_offset, index,
        ))
    return found


def sites(text: str, function: str) -> tuple[Site, ...]:
    """Every mutable site of the target function, sorted by position."""

    target = _target(text, function)
    if target is None:
        return ()
    offsets = line_offsets(text)
    tokens = _operator_tokens(text, offsets)
    found: list[Site] = []
    for node in body_nodes(target):
        if isinstance(node, ast.Compare):
            found += _compare_sites(node, tokens, offsets)
    return tuple(sorted(found, key=lambda s: (s.start, s.end, s.operator, s.variant)))


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


def _expected_dump(text: str, function: str, site: Site) -> str | None:
    """The target function after the operator swap applied to the original tree, dumped."""

    module = copy.deepcopy(ast.parse(text))
    for node in ast.walk(module):
        if (
            isinstance(node, ast.Compare)
            and (node.lineno, node.col_offset) == (site.node_lineno, site.node_col_offset)
        ):
            node.ops[site.op_index] = _OPERATOR_CLASSES[site.replacement_text]()
            target = _target(ast.unparse(module), function)
            return None if target is None else ast.dump(target)
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
        (dumped != _expected_dump(text, function, site), cv.SKIP_MUTATION_UNVERIFIABLE),
    )
    return next((code for holds, code in rules if holds), None)


def choose(stream: rng.DrawStream, candidates: tuple[Site, ...]) -> Site:
    """One seeded draw over the sorted site tuple."""

    return stream.choice(candidates)


bind_import_twin(__name__)
