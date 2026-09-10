#!/usr/bin/env python3
"""Build a catalog from pinned upstream sources: selection, extraction, references, hidden cases.

Pure over its inputs (upstream file texts, a reviewed reference table, an
executor for the observed wants) and deterministic, so the same inputs rebuild
the same ``programs.jsonl`` bytes; the fixture catalog is rebuilt by the tests
and compared byte for byte. The one-time network fetch lives in
``scripts/vendor_python_repair_catalog.py``; nothing here touches the network.

A program is one module-level function with at least two doctest examples,
extracted with the imports it needs into a self-contained module. Its hidden
cases are the literal doctest inputs plus a seeded neighbourhood
(``doctest-literals+seeded-neighbourhood-v1``), kept only where the original
returns a value; their wants are the original's own reprs, and a certifying
reference must agree on every case or the program falls back to
``original_self``. Groups and splits are assigned last, over the whole set.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import symtable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import catalog_check as cc
from . import catalog_inputs as inputs
from . import executor as ex
from . import lineage
from . import vocabulary as cv
from ._contract import bind_import_twin, oc

SELECTOR_VERSION = "selector-v1"
INPUT_POLICY = inputs.INPUT_POLICY
MIN_EXAMPLES = 2
FORBIDDEN_CALLS = frozenset({
    "input", "print", "open", "exec", "eval", "compile", "__import__", "globals", "locals",
    "vars", "getattr", "setattr", "delattr", "breakpoint", "help",
})
# Modules a doctest example may import: pure computation, nothing that varies between runs.
DOCTEST_IMPORTS = frozenset({
    "cmath", "collections", "decimal", "fractions", "functools", "itertools", "math",
    "operator", "string",
})
# Attribute calls that reach the host: files, processes, sockets, the interpreter itself.
FORBIDDEN_ATTRIBUTES = frozenset({
    "system", "popen", "spawn", "spawnl", "spawnv", "execv", "execl", "fork", "kill", "run",
    "call", "check_call", "check_output", "Popen", "open", "write_text", "write_bytes",
    "read_text", "read_bytes", "remove", "unlink", "rmtree", "mkdir", "makedirs", "rename",
    "replace", "chmod", "urlopen", "urlretrieve", "connect", "bind", "listen", "exit",
    "settrace", "setprofile", "load", "loads", "dump", "dumps",
})
SAFE_IMPORTS = frozenset({
    "math", "cmath", "itertools", "functools", "collections", "operator", "bisect",
    "heapq", "decimal", "fractions", "statistics", "typing", "string", "re", "array",
    "numbers", "__future__",
})

__all__ = [
    "INPUT_POLICY", "SELECTOR_VERSION", "Build", "Upstream", "build_rows", "extract_module",
    "program_id_for", "select_targets", "write_catalog",
]


@dataclass(frozen=True)
class Upstream:
    repository: str
    commit: str
    license: str
    license_text: str


@dataclass(frozen=True)
class Build:
    """What one build runs over: sources by path, the reviewed reference table, the policy."""

    upstream: Upstream
    sources: dict[str, str]
    references: dict[str, dict[str, Any]]
    policy: lineage.SplitPolicy | None = None
    notes: list[dict[str, str]] = field(default_factory=list)


def program_id_for(upstream: Upstream, path: str, function: str) -> str:
    """Opaque, so it never occurs in program text."""

    key = f"{upstream.repository}@{upstream.commit}:{path}::{function}"
    return "tap-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


# --- selection and extraction ---------------------------------------------------


def _bound_names(node: ast.Import | ast.ImportFrom) -> set[str]:
    return {(alias.asname or alias.name).split(".")[0] for alias in node.names}


def _global_names(table: symtable.SymbolTable) -> set[str]:
    """Names this scope and every nested scope resolve at module level."""

    names = {symbol.get_name() for symbol in table.get_symbols() if symbol.is_global()}
    for child in table.get_children():
        names |= _global_names(child)
    return names


def _free_names(text: str, function: ast.FunctionDef) -> set[str]:
    """Names the function reads from the module that neither it nor Python provides.

    Resolved by the compiler's own scope analysis, so a name bound in a nested scope
    (a comprehension's target, an inner function's local) never masks an outer read
    (Greptile and Codex on #202).
    """

    module_table = symtable.symtable(text, cv.PROGRAM_FILENAME, "exec")
    tables = [t for t in module_table.get_children() if t.get_name() == function.name]
    globals_read = set().union(*(_global_names(t) for t in tables)) if tables else set()
    return globals_read - {function.name} - set(dir(builtins))


def _reaches_the_host(node: ast.AST) -> bool:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return True  # a nested import escapes the module-level admission check
    if isinstance(node, ast.Attribute):
        return node.attr in FORBIDDEN_ATTRIBUTES or node.attr.startswith("__")
    if isinstance(node, ast.Name) and node.id in FORBIDDEN_CALLS:
        return True
    if not isinstance(node, ast.Call):
        return False
    callee = node.func
    if isinstance(callee, ast.Name):
        return callee.id in FORBIDDEN_CALLS
    return isinstance(callee, ast.Attribute) and callee.attr in FORBIDDEN_ATTRIBUTES


def _calls_forbidden(function: ast.FunctionDef) -> bool:
    return any(_reaches_the_host(node) for node in ast.walk(function))


def _module_imports(module: ast.Module) -> tuple[list[ast.stmt], set[str]]:
    imports = [n for n in module.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    imports = [n for n in imports if getattr(n, "module", None) != "__future__"]
    names: set[str] = set()
    for node in imports:
        names |= _bound_names(node)
    return imports, names


def _safe_import(node: ast.Import | ast.ImportFrom) -> bool:
    if isinstance(node, ast.ImportFrom):
        return not node.level and node.module in SAFE_IMPORTS and all(
            not a.name.startswith("_") and a.name != "*" for a in node.names
        )
    return all(a.name in SAFE_IMPORTS for a in node.names)


def _safe_examples(examples: tuple[cat.Example, ...]) -> bool:
    for example in examples:
        try:
            nodes = ast.walk(ast.parse(example.source))
            for node in nodes:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if not _safe_import(node):
                        return False
                elif _reaches_the_host(node):
                    return False
        except SyntaxError:
            return False
    return True


def _has_observable_doctests(text: str, node: ast.FunctionDef) -> bool:
    examples = cat.examples_of(text, node.name)
    return (len(examples) >= MIN_EXAMPLES and any(e.want.strip() for e in examples)
            and _safe_examples(examples))


def _is_plain_function(node: ast.stmt) -> bool:
    if not isinstance(node, ast.FunctionDef):
        return False
    return not node.decorator_list and not node.type_params


def _is_self_contained(text: str, node: ast.FunctionDef, imported: set[str]) -> bool:
    if _free_names(text, node) - imported:
        return False
    return not _calls_forbidden(node)


def _qualifies(text: str, node: ast.stmt, imported: set[str]) -> bool:
    """A plain module-level function with observable doctests and no outside dependency."""

    if not _is_plain_function(node):
        return False
    return _has_observable_doctests(text, node) and _is_self_contained(text, node, imported)


def select_targets(text: str) -> list[str]:
    """Module-level functions that qualify as programs, in source order."""

    module = ast.parse(text)
    imports, imported = _module_imports(module)
    if not all(_safe_import(node) for node in imports):
        return []
    return [node.name for node in module.body
            if isinstance(node, ast.FunctionDef) and _definition(module, node.name) is node
            and _qualifies(text, node, imported)]


def _used_import(node: ast.Import | ast.ImportFrom, used: set[str]) -> str | None:
    """The import statement rebuilt with only the aliases the function reads (Codex on #202)."""

    aliases = [a for a in node.names if (a.asname or a.name).split(".")[0] in used]
    if not aliases:
        return None
    rendered = ", ".join(a.name + (f" as {a.asname}" if a.asname else "") for a in aliases)
    if isinstance(node, ast.ImportFrom):
        return f"from {'.' * node.level}{node.module or ''} import {rendered}"
    return f"import {rendered}"


def extract_module(text: str, function: str) -> tuple[str, tuple[int, int]] | None:
    """The function with the imports it needs as one module, and its upstream line span."""

    module = ast.parse(text)
    node = _definition(module, function)
    if node is None:
        return None
    head = _import_head(module, node)
    module_text = head + ast.get_source_segment(text, node) + "\n"
    return module_text, (node.lineno, node.end_lineno)


def _definition(module: ast.Module, function: str) -> ast.FunctionDef | None:
    matches = [node for node in module.body
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
               and node.name == function]
    return matches[0] if len(matches) == 1 and isinstance(matches[0], ast.FunctionDef) else None


def _import_head(module: ast.Module, node: ast.FunctionDef) -> str:
    """The import lines the function reads, followed by two blank lines; empty if none."""

    imports, _names = _module_imports(module)
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    kept = [line for line in (_used_import(i, used) for i in imports) if line]
    futures = [ast.unparse(n) for n in module.body
               if isinstance(n, ast.ImportFrom) and n.module == "__future__"]
    kept = futures + kept
    return "\n".join(kept) + "\n\n\n" if kept else ""


# --- references --------------------------------------------------------------------


def _reference_source(spec: dict[str, Any], path: str, source_text: str) -> str | None:
    """The reference module text for a sibling or reviewed spec; None for original_self."""

    if spec["kind"] == cv.REFERENCE_SIBLING:
        extracted = extract_module(source_text, spec["function"])
        cv.refuse_when(
            extracted is None, cv.FINDING_TARGET_FUNCTION_NOT_FOUND,
            f"{path} defines no sibling {spec['function']}",
        )
        return extracted[0]
    return spec["source"] if spec["kind"] == cv.REFERENCE_REVIEWED else None


def _reference_block(build: Build, path: str, function: str, source_text: str) -> dict[str, Any]:
    spec = build.references.get(f"{path}::{function}", {"kind": cv.REFERENCE_SELF})
    source = _reference_source(spec, path, source_text)
    if source is None:
        return {"kind": spec["kind"], "function": None, "source": None, "sha256": None}
    return {
        "kind": spec["kind"], "function": spec["function"], "source": source,
        "sha256": cat.sha256_text(source),
    }


def _reference_agrees(executor: ex.Executor, block: dict[str, Any], cases: list[dict]) -> bool:
    if block["source"] is None:
        return True
    if not cases:
        return False
    job = ex.Job("reference:build", block["source"], block["function"], tuple(cases), False)
    report = executor.run(job)
    return report.ok and all(row["status"] == cv.ROW_SUCCESS for row in report.hidden)


# --- rows ------------------------------------------------------------------------------


def _note(build: Build, code: str, program_id: str) -> None:
    build.notes.append({"code": code, "program_id": program_id})


def _program_row(
    build: Build, path: str, function: str, executor: ex.Executor
) -> dict[str, Any] | None:
    """The row for one target, or None (noted) when the original cannot be observed."""

    source_text = build.sources[path]
    extracted = extract_module(source_text, function)
    cv.refuse_when(extracted is None, cv.FINDING_TARGET_FUNCTION_NOT_FOUND, f"{path}::{function}")
    text, span = extracted
    program_id = program_id_for(build.upstream, path, function)
    examples = cat.examples_of(text, function)
    report, cases = inputs.observe(executor, inputs.Subject(text, function, program_id, examples))
    code = None if report is None else cc.phase_code(
        report, cv.REASON_ORIGINAL_TIMEOUT, cv.REASON_ORIGINAL_HARNESS_ERROR
    )
    if code is not None:
        _note(build, code, program_id)
        return None
    reference = _reference_block(build, path, function, source_text)
    if reference["kind"] != cv.REFERENCE_SELF and not cases:
        # Nothing for a reference to certify: the loader refuses such a pin (Codex on #196).
        _note(build, cv.CHECK_REFERENCE_WITHOUT_CASES, program_id)
        reference = {"kind": cv.REFERENCE_SELF, "function": None, "source": None, "sha256": None}
    elif not _reference_agrees(executor, reference, cases):
        _note(build, cv.CHECK_REFERENCE_DISAGREES, program_id)
        reference = {"kind": cv.REFERENCE_SELF, "function": None, "source": None, "sha256": None}
    upstream = build.upstream
    return {
        "program_id": program_id, "family": path.split("/")[0],
        "upstream": {
            "repository": upstream.repository, "commit": upstream.commit, "path": path,
            "file_sha256": cat.sha256_text(source_text), "function": function,
            "line_span": list(span), "license": upstream.license,
        },
        "module": {"text": text, "sha256": cat.sha256_text(text)},
        "public": {
            "example_count": len(examples), "examples_sha256": cat.examples_sha256(examples),
        },
        "hidden": {"reference": reference, "cases": cases, "input_policy": INPUT_POLICY},
        "structure": None, "split": None,
    }


def _verified_row(
    build: Build, path: str, function: str, executor: ex.Executor
) -> dict[str, Any] | None:
    """A row whose original passes its own examples and cases twice; else None, noted."""

    row = _program_row(build, path, function, executor)
    if row is None:
        return None
    findings = cc.original_findings(cat.program_from_row(row), executor)
    if findings:
        _note(build, findings[0]["code"], row["program_id"])
        return None
    return row


def _assign_structure(build: Build, rows: list[dict[str, Any]]) -> None:
    digests = {r["program_id"]: lineage.structure_digest(r["module"]["text"]) for r in rows}
    members = tuple(
        lineage.Member(r["program_id"], r["upstream"]["path"], digests[r["program_id"]])
        for r in rows
    )
    groups = lineage.group_ids(members)
    for row in rows:
        program_id = row["program_id"]
        group_id = groups[program_id]
        row["structure"] = {"group_id": group_id, "ast_digest": digests[program_id]}
        if build.policy is not None:
            anchor = lineage.anchor_for(group_id, program_id)
            row["split"] = lineage.bucket_split(anchor, build.policy)


def build_rows(
    build: Build, targets: list[tuple[str, str]], executor: ex.Executor
) -> list[dict[str, Any]]:
    """One row per verified ``(path, function)`` target, sorted; groups and splits over the set.

    A target whose original cannot be observed, fails its own examples or cases, or answers
    two runs differently is dropped and noted (``build.notes``), never built into a row.
    """

    ordered = sorted(set(targets))  # canonical row order: by upstream path, then function
    rows = [_verified_row(build, path, function, executor) for path, function in ordered]
    kept = [row for row in rows if row is not None]
    _assign_structure(build, kept)
    return kept


def write_catalog(
    directory: Path, catalog_id: str, build: Build, rows: list[dict[str, Any]]
) -> None:
    """A brand-new catalog directory: LICENSE.upstream, programs.jsonl, CATALOG.json."""

    directory = Path(directory)
    cv.refuse_when(directory.exists(), cv.FINDING_DESTINATION_EXISTS, f"{directory} already exists")
    directory.mkdir(parents=True)
    license_bytes = build.upstream.license_text.encode("utf-8")
    (directory / cat.LICENSE_FILENAME).write_bytes(license_bytes)
    oc.write_jsonl(directory / cat.PROGRAMS_FILENAME, rows)
    meta: dict[str, Any] = {
        "format": cv.CATALOG_FORMAT, "catalog_id": catalog_id,
        "upstream": {
            "repository": build.upstream.repository, "commit": build.upstream.commit,
            "license": build.upstream.license,
            "license_sha256": hashlib.sha256(license_bytes).hexdigest(),
        },
        "programs_sha256": hashlib.sha256(
            (directory / cat.PROGRAMS_FILENAME).read_bytes()
        ).hexdigest(),
        "program_count": len(rows),
        "build": {
            "tool": "pipelines/code_repair/catalog_build.py", "selector": SELECTOR_VERSION,
            "input_policy": INPUT_POLICY, "notes": list(build.notes),
        },
    }
    if build.policy is not None:
        meta["split_policy"] = build.policy.as_json()
        meta["split_policy_sha256"] = build.policy.sha256
    with open(directory / cat.CATALOG_FILENAME, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(meta, indent=2, sort_keys=True) + "\n")


bind_import_twin(__name__)
