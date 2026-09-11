#!/usr/bin/env python3
"""The pinned program catalog: loading, pins, doctest examples, hidden cases.

A catalog directory holds ``CATALOG.json`` (identity, upstream, pins),
``programs.jsonl`` (one program per line, the module text as a JSON string so
no linter or test discovery ever touches third-party code) and
``LICENSE.upstream``. Load and pin verification live in :mod:`.catalog_load`
so this module stays the types, doctest helpers and ``catalog_check``.
:func:`catalog_check` is the "original passes" demonstration: every
program's original must pass its public examples and its hidden cases twice
identically, and a certifying reference must agree with the pinned wants twice.
"""

from __future__ import annotations

import ast
import doctest
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import executor as ex
from . import lineage
from . import vocabulary as cv
from ._contract import bind_import_twin, oc

CATALOG_FILENAME = "CATALOG.json"
PROGRAMS_FILENAME = "programs.jsonl"
LICENSE_FILENAME = "LICENSE.upstream"
SPLITS = ("train", "validation", "held_out")
MAX_CASE_ARGS_CHARS = 4_096
MAX_PUBLIC_EXAMPLES = 48  # 72 total rows fit the 1 MiB report budget with UTF-8 output
UPSTREAM_FIELDS = ("repository", "commit", "path", "file_sha256", "function", "license")

__all__ = [
    "CATALOG_FILENAME", "Catalog", "Example", "LICENSE_FILENAME", "PROGRAMS_FILENAME", "Program",
    "Reference", "examples_of", "examples_sha256", "function_node", "load_catalog",
    "sha256_text", "want_kind_of",
]


@dataclass(frozen=True)
class Example:
    """One doctest example of the target function, as the parser sees it."""

    example_id: str
    source: str
    want: str
    exc_msg: str | None

    def key(self) -> tuple[str, str, str | None]:
        return (self.source, self.want, self.exc_msg)


@dataclass(frozen=True)
class Reference:
    """The complementary oracle: a sibling, a reviewed expression, or the original itself."""

    kind: str
    function: str | None = None
    source: str | None = None
    sha256: str | None = None

    @property
    def certifying(self) -> bool:
        return self.kind in cv.CERTIFYING_REFERENCE_KINDS


@dataclass(frozen=True)
class Program:
    """One pinned program: identity, module text, public examples and hidden cases."""

    program_id: str
    family: str
    upstream: Mapping[str, Any]
    text: str
    sha256: str
    function: str
    examples: tuple[Example, ...]
    examples_sha256: str
    reference: Reference
    cases: tuple[Mapping[str, str], ...]
    group_id: str | None
    split: str | None
    ast_digest: str | None = None

    @property
    def want_kind(self) -> str | None:
        """``numeric`` or ``bool`` when every value example wants that kind, else None."""

        return want_kind_of(self.examples)

    def job(self, label: str, text: str | None = None) -> ex.Job:
        """A harness job over this program's function and cases (``text`` overrides the module)."""

        module_text = self.text if text is None else text
        return ex.Job(
            label, module_text, self.function, self.cases, expected_public=len(self.examples)
        )

    def reference_job(self, label: str) -> ex.Job:
        reference = self.reference
        return ex.Job(label, reference.source or "", reference.function or "", self.cases, False)


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    meta: dict[str, Any]
    programs_sha256: str
    license_sha256: str
    programs: tuple[Program, ...]
    split_policy: lineage.SplitPolicy | None = None

    def program(self, program_id: str) -> Program:
        for program in self.programs:
            if program.program_id == program_id:
                return program
        raise cv.RepairRefusal(
            cv.FINDING_PROGRAM_NOT_FOUND, f"no program {cv.shown(program_id)} in the catalog"
        )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def function_defs(text: str, function: str) -> list[ast.FunctionDef]:
    """Every module-level ``def`` named ``function`` in ``text``, in order."""

    return [
        node for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]


def function_node(text: str, function: str) -> ast.FunctionDef | None:
    """The module-level ``def`` named ``function`` in ``text``, or None.

    When the name is bound more than once, the last definition matches import
    semantics; catalog loading refuses the duplicate before this is relied on.
    """

    found = function_defs(text, function)
    return found[-1] if found else None


def examples_of(text: str, function: str) -> tuple[Example, ...]:
    """The doctest examples of the target function's docstring, in order."""

    node = function_node(text, function)
    if node is None:
        return ()
    docstring = ast.get_docstring(node, clean=True) or ""
    parsed = doctest.DocTestParser().get_examples(docstring)  # ValueError on a bad directive
    for item in parsed:
        if item.options.get(doctest.FAIL_FAST):
            raise ValueError("doctest FAIL_FAST directive stops row reporting")
    executable = [item for item in parsed if not item.options.get(doctest.SKIP)]
    return tuple(
        Example(f"{function}:{index}", item.source, item.want, item.exc_msg)
        for index, item in enumerate(executable)
    )


def _want_value(example: Example) -> Any:
    try:
        return ast.literal_eval(example.want.strip())
    except (ValueError, SyntaxError):
        return None


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _value_wants(examples: tuple[Example, ...]) -> list[Any]:
    return [_want_value(e) for e in examples if e.exc_msg is None and e.want.strip()]


def want_kind_of(examples: tuple[Example, ...]) -> str | None:
    """The kind every value-returning example expects: ``numeric``, ``bool`` or None."""

    wants = _value_wants(examples)
    if not wants:
        return None
    if all(isinstance(w, bool) for w in wants):
        return "bool"
    return "numeric" if all(_is_numeric(w) for w in wants) else None


def examples_sha256(examples: tuple[Example, ...]) -> str:
    return sha256_text(oc.canonical_json([list(example.key()) for example in examples]))


from .catalog_load import load_catalog  # noqa: E402  types must exist first


bind_import_twin(__name__)
