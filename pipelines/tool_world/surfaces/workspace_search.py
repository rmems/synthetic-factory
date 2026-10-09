#!/usr/bin/env python3
"""The workspace ``search`` tool: a regex over the tree, bounded by the pattern's shape.

A search's cost must be a function of the pattern and the files alone, never
of a clock, or the observation would depend on the machine that computed it.
So the bound is structural: a pattern is refused when it is longer than
``MAX_PATTERN_CHARS``, invalid, or nests repetition (a quantified group that
holds a quantifier or alternation, the shape that backtracks without bound).
What passes is searched line by line; the report lists the first
``MAX_MATCHES`` hits and counts the rest.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from .._contract import bind_import_twin
from .base import error_text

__all__ = ["MAX_MATCHES", "MAX_PATTERN_CHARS", "nests_repetition", "pattern_problem", "search_tree"]

MAX_MATCHES = 40
MAX_PATTERN_CHARS = 200
# An escape or a character class is one atom to the repetition scan; a group prefix is dropped.
# Inside a class, an escape and a plain char are disjoint, so this regex itself runs in linear time.
_OPAQUE_RE = re.compile(r"\\.|\[\^?\]?(?:\\.|[^\\\]])*\]", re.DOTALL)
_GROUP_PREFIX_RE = re.compile(r"\(\?(?:P<\w+>|P=\w+|<\w+>|<[=!]|[=!:]|[aiLmsux-]+:?)")
_QUANTIFIER_RE = re.compile(r"[*+?]|\{(?:\d+(?:,\d*)?|,\d+)\}")


# --- the repetition scan ---------------------------------------------------


def _skeleton(pattern: str) -> str:
    """The pattern with escapes and classes reduced to one atom and group prefixes dropped."""
    return _GROUP_PREFIX_RE.sub("(", _OPAQUE_RE.sub("x", pattern))


class _RepetitionScan:
    """One pass over a pattern skeleton, tracking which open groups hold repetition."""

    def __init__(self, skeleton: str) -> None:
        self.skeleton = skeleton
        self.groups: list[bool] = []  # per open group: whether it holds a quantifier or alternation
        self.nested = False

    def run(self) -> bool:
        """Whether a quantified group holds a quantifier or alternation."""
        for index, char in enumerate(self.skeleton):
            _HANDLERS.get(char, _RepetitionScan.atom)(self, index)
            if self.nested:
                return True
        return False

    def quantifier_at(self, index: int) -> bool:
        return _QUANTIFIER_RE.match(self.skeleton, index) is not None

    def mark(self, holds: bool) -> None:
        """Record that the innermost open group holds repetition, when there is one."""
        if holds and self.groups:
            self.groups[-1] = True

    def open_group(self, index: int) -> None:
        self.groups.append(False)

    def close_group(self, index: int) -> None:
        inner = self.groups.pop() if self.groups else False
        quantified = self.quantifier_at(index + 1)
        self.nested = inner and quantified
        self.mark(inner or quantified)

    def alternation(self, index: int) -> None:
        self.mark(True)

    def atom(self, index: int) -> None:
        self.mark(self.quantifier_at(index))


_HANDLERS = {
    "(": _RepetitionScan.open_group,
    ")": _RepetitionScan.close_group,
    "|": _RepetitionScan.alternation,
}


def nests_repetition(pattern: str) -> bool:
    """Whether a quantified group holds a quantifier or alternation: the backtracking shape.

    ``(a+)+``, ``(a|aa)*`` and ``((x*)y){2,}`` can take time exponential in
    the line they search; the answer is one pass over the pattern's skeleton,
    a function of the pattern alone.
    """
    return _RepetitionScan(_skeleton(pattern)).run()


def pattern_problem(pattern: str) -> str | None:
    """Why a search refuses its pattern: too long, invalid, or shaped to backtrack without bound."""
    if len(pattern) > MAX_PATTERN_CHARS:
        return f"regex longer than {MAX_PATTERN_CHARS} chars"
    try:
        re.compile(pattern)
    except re.error as exc:
        return f"invalid regex: {exc}"
    if nests_repetition(pattern):
        return (
            "regex nests repetition (a quantified group holding a quantifier or alternation), "
            "which can backtrack without bound; rewrite the pattern"
        )
    return None


# --- the search ------------------------------------------------------------


def _grep(pattern: re.Pattern[str], path: str, text: str) -> list[str]:
    """``path:line: text`` for every line the pattern matches, in file order."""
    return [
        f"{path}:{number}: {line}"
        for number, line in enumerate(text.splitlines(), 1)
        if pattern.search(line)
    ]


def _match_report(matches: list[str]) -> str:
    """The first ``MAX_MATCHES`` hits, with a count of what the cap hid."""
    shown = matches[:MAX_MATCHES]
    hidden = len(matches) - len(shown)
    tail = f"\n[{hidden} more matches]" if hidden else ""
    return f"{len(matches)} matches:\n" + "\n".join(shown) + tail


def search_tree(pattern: str, files: Mapping[str, str], prefix: str = "") -> str:
    """The observation of a regex search over ``files`` under ``prefix``: hits, none, or why not."""
    problem = pattern_problem(pattern)
    if problem is not None:
        return error_text(problem)
    compiled = re.compile(pattern)
    matches: list[str] = []
    for path in sorted(files):
        if path.startswith(prefix):
            matches.extend(_grep(compiled, path, files[path]))
    if not matches:
        return f"no matches for {pattern!r}"
    return _match_report(matches)


bind_import_twin(__name__)
