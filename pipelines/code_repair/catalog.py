#!/usr/bin/env python3
"""The pinned program catalog: loading, pins, doctest examples, hidden cases.

A catalog directory holds ``CATALOG.json`` (identity, upstream, pins),
``programs.jsonl`` (one program per line, the module text as a JSON string so
no linter or test discovery ever touches third-party code) and
``LICENSE.upstream``. Every pin is verified at load: the programs file digest,
each module's digest, its LF framing, that it parses, that the target function
exists at module level and carries doctest examples whose digest matches the
row. :func:`catalog_check` is the "original passes" demonstration: every
program's original must pass its public examples and its hidden cases twice
identically, and a certifying reference must agree with the pinned wants.
"""

from __future__ import annotations

import ast
import doctest
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import executor as ex
from . import lineage
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, oc

CATALOG_FILENAME = "CATALOG.json"
PROGRAMS_FILENAME = "programs.jsonl"
LICENSE_FILENAME = "LICENSE.upstream"
SPLITS = ("train", "validation", "held_out")
MAX_CASE_ARGS_CHARS = 4_096
_UPSTREAM_FIELDS = ("repository", "commit", "path", "file_sha256", "function", "license")

__all__ = [
    "CATALOG_FILENAME", "Catalog", "Example", "LICENSE_FILENAME", "PROGRAMS_FILENAME", "Program",
    "Reference", "examples_of", "examples_sha256", "function_node", "load_catalog",
    "program_from_row", "sha256_text", "want_kind_of",
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
    upstream: dict[str, Any]
    text: str
    sha256: str
    function: str
    examples: tuple[Example, ...]
    examples_sha256: str
    reference: Reference
    cases: tuple[dict[str, Any], ...]
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


def function_node(text: str, function: str) -> ast.FunctionDef | None:
    """The module-level ``def`` named ``function`` in ``text``, or None."""

    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return node
    return None


def examples_of(text: str, function: str) -> tuple[Example, ...]:
    """The doctest examples of the target function's docstring, in order."""

    node = function_node(text, function)
    if node is None:
        return ()
    docstring = ast.get_docstring(node, clean=True) or ""
    parsed = doctest.DocTestParser().get_examples(docstring)  # ValueError on a bad directive
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


def want_kind_of(examples: tuple[Example, ...]) -> str | None:
    """The kind every value-returning example expects: ``numeric``, ``bool`` or None."""

    wants = [_want_value(e) for e in examples if e.exc_msg is None and e.want.strip()]
    if not wants:
        return None
    if all(isinstance(w, bool) for w in wants):
        return "bool"
    return "numeric" if all(_is_numeric(w) for w in wants) else None


def examples_sha256(examples: tuple[Example, ...]) -> str:
    return sha256_text(oc.canonical_json([list(example.key()) for example in examples]))


# --- loading -----------------------------------------------------------------


def _missing_code(where: str) -> str:
    """Catalog metadata and program rows are told apart by the code, not only the prose."""

    if where.startswith(CATALOG_FILENAME):
        return cv.FINDING_CATALOG_FIELD_MISSING
    return cv.FINDING_PROGRAM_FIELD_MISSING


def _invalid_code(where: str) -> str:
    if where.startswith(CATALOG_FILENAME):
        return cv.FINDING_CATALOG_FIELD_INVALID
    return cv.FINDING_PROGRAM_FIELD_INVALID


def _field(mapping: Any, key: str, kinds: type | tuple[type, ...], where: str) -> Any:
    """A required field of the expected type; refuses with a coded finding."""

    cv.refuse_when(
        not isinstance(mapping, dict), cv.FINDING_INPUT_NOT_AN_OBJECT, f"{where} must be an object"
    )
    cv.refuse_when(key not in mapping, _missing_code(where), f"{where}.{key} is missing")
    value = mapping[key]
    cv.refuse_when(
        (not isinstance(value, kinds)) or (isinstance(value, bool) and kinds is not bool),
        _invalid_code(where),
        f"{where}.{key} has the wrong type",
    )
    return value


def _module_text(row: dict[str, Any], where: str) -> tuple[str, str]:
    module = _field(row, "module", dict, where)
    text = _field(module, "text", str, f"{where}.module")
    digest = _field(module, "sha256", str, f"{where}.module")
    cv.refuse_first((
        ("\r" in text or not text.endswith("\n"), cv.FINDING_PROGRAM_NOT_LF_FRAMED,
         f"{where}.module.text must be LF-only with a final newline"),
        (sha256_text(text) != digest, cv.FINDING_PROGRAM_SHA256_MISMATCH,
         f"{where}.module.sha256 does not match the text"),
    ))
    _parse_or_refuse(text, f"{where}.module.text")
    return text, digest


def _parse_or_refuse(text: str, where: str) -> ast.Module:
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError) as exc:
        message = f"{where} does not parse: {exc}"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_NOT_PARSEABLE, message) from exc


def _reference(row: dict[str, Any], where: str) -> Reference:
    hidden = _field(row, "hidden", dict, where)
    block = _field(hidden, "reference", dict, f"{where}.hidden")
    kind = _field(block, "kind", str, f"{where}.hidden.reference")
    cv.refuse_when(
        kind not in cv.REFERENCE_KINDS, cv.FINDING_REFERENCE_KIND_UNKNOWN,
        f"{where}.hidden.reference.kind is not one of {sorted(cv.REFERENCE_KINDS)}",
    )
    if kind == cv.REFERENCE_SELF:
        return Reference(kind)
    source = _field(block, "source", str, f"{where}.hidden.reference")
    digest = _field(block, "sha256", str, f"{where}.hidden.reference")
    function = _field(block, "function", str, f"{where}.hidden.reference")
    cv.refuse_when(
        sha256_text(source) != digest, cv.FINDING_PROGRAM_SHA256_MISMATCH,
        f"{where}.hidden.reference.sha256 does not match its source",
    )
    _parse_or_refuse(source, f"{where}.hidden.reference.source")
    cv.refuse_when(
        function_node(source, function) is None, cv.FINDING_TARGET_FUNCTION_NOT_FOUND,
        f"{where}.hidden.reference.source defines no module-level function {function}",
    )
    return Reference(kind, function, source, digest)


def _cases(row: dict[str, Any], where: str) -> tuple[dict[str, Any], ...]:
    cases = _field(_field(row, "hidden", dict, where), "cases", list, f"{where}.hidden")
    cv.refuse_when(
        len(cases) > cv.MAX_HIDDEN_CASES, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}.hidden.cases holds more than {cv.MAX_HIDDEN_CASES} cases",
    )
    parsed = []
    for index, case in enumerate(cases):
        spot = f"{where}.hidden.cases[{index}]"
        args, want = _field(case, "args", str, spot), _field(case, "want", str, spot)
        cv.refuse_when(
            len(args) > MAX_CASE_ARGS_CHARS, cv.FINDING_PROGRAM_FIELD_INVALID,
            f"{spot}.args is longer than {MAX_CASE_ARGS_CHARS} characters",
        )
        parsed.append({"args": args, "want": want})
    return tuple(parsed)


def _examples(row: dict[str, Any], text: str, function: str, where: str) -> tuple[Example, ...]:
    public = _field(row, "public", dict, where)
    try:
        examples = examples_of(text, function)
    except ValueError as exc:  # a malformed doctest directive
        message = f"{where}: {function} carries a doctest the parser refuses"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_FIELD_INVALID, message) from exc
    cv.refuse_first((
        (function_node(text, function) is None, cv.FINDING_TARGET_FUNCTION_NOT_FOUND,
         f"{where}: no module-level function named {function}"),
        (not examples, cv.FINDING_TARGET_HAS_NO_DOCTEST, f"{where}: {function} carries no doctest"),
        (_field(public, "example_count", int, f"{where}.public") != len(examples)
         or _field(public, "examples_sha256", str, f"{where}.public") != examples_sha256(examples),
         cv.FINDING_EXAMPLES_SHA_MISMATCH, f"{where}.public does not pin the docstring's examples"),
    ))
    return examples


def _split(row: dict[str, Any], where: str) -> tuple[str | None, str | None, str | None]:
    """``(group_id, ast_digest, split)``: each a string or null, never anything else."""

    structure = row.get("structure")
    split = row.get("split")
    cv.refuse_when(
        (structure is not None and not isinstance(structure, dict))
        or (split is not None and split not in SPLITS),
        cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: structure must be an object or null and split one of {SPLITS} or null",
    )
    pins = {}
    for key in ("group_id", "ast_digest"):
        pins[key] = structure.get(key) if isinstance(structure, dict) else None
        cv.refuse_when(
            pins[key] is not None and not isinstance(pins[key], str),
            cv.FINDING_PROGRAM_FIELD_INVALID, f"{where}: structure.{key} must be a string or null",
        )
    return pins["group_id"], pins["ast_digest"], split


def _program(row: Any, lineno: int) -> Program:
    where = f"programs.jsonl:{lineno}"
    program_id = _field(row, "program_id", str, where)
    upstream = _field(row, "upstream", dict, where)
    for key in _UPSTREAM_FIELDS:
        _field(upstream, key, str, f"{where}.upstream")
    text, digest = _module_text(row, where)
    function = upstream["function"]
    group_id, ast_digest, split = _split(row, where)
    reference, cases = _reference(row, where), _cases(row, where)
    cv.refuse_when(
        reference.certifying and not cases, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: a certifying reference needs at least one hidden case",
    )
    examples = _examples(row, text, function, where)
    return Program(
        program_id, _field(row, "family", str, where), dict(upstream), text, digest, function,
        examples, examples_sha256(examples), reference, cases, group_id, split, ast_digest,
    )


def program_from_row(row: dict[str, Any]) -> Program:
    """A builder-produced row as the loader would read it (same checks, no file position)."""

    return _program(row, 0)


def _provenance_agrees(program: Program, meta: dict[str, Any]) -> None:
    """A program's upstream must be the catalog's upstream (Greptile on #196)."""

    upstream = meta["upstream"]
    for key in ("repository", "commit", "license"):
        cv.refuse_when(
            program.upstream[key] != upstream[key], cv.FINDING_CATALOG_FIELD_INVALID,
            f"{program.program_id}: upstream.{key} contradicts {CATALOG_FILENAME}",
        )


def _programs(directory: Path) -> tuple[tuple[Program, ...], str]:
    path = directory / PROGRAMS_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    data = path.read_bytes()  # one read: the digest and the parse cover the same bytes
    digest = hashlib.sha256(data).hexdigest()
    programs = []
    seen: set[str] = set()
    for lineno, parsed in oc.iter_jsonl_bytes(data):
        cv.refuse_when(
            parsed is None, cv.FINDING_CATALOG_FIELD_INVALID,
            f"programs.jsonl:{lineno} is not strict JSON",
        )
        program = _program(parsed, lineno)
        cv.refuse_when(
            program.program_id in seen, cv.FINDING_PROGRAM_ID_DUPLICATE,
            f"programs.jsonl:{lineno} repeats {program.program_id}",
        )
        seen.add(program.program_id)
        programs.append(program)
    return tuple(programs), digest


def _meta(directory: Path) -> dict[str, Any]:
    path = directory / CATALOG_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    try:
        meta = load_strict_json(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        message = f"{path} is not JSON: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FIELD_INVALID, message) from exc
    for key, kinds in (("format", str), ("catalog_id", str), ("upstream", dict),
                       ("programs_sha256", str), ("program_count", int)):
        _field(meta, key, kinds, CATALOG_FILENAME)
    cv.refuse_when(
        meta["format"] != cv.CATALOG_FORMAT, cv.FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.format must be {cv.CATALOG_FORMAT}",
    )
    for key in ("repository", "commit", "license", "license_sha256"):
        _field(meta["upstream"], key, str, f"{CATALOG_FILENAME}.upstream")
    return meta


def _split_policy(meta: dict[str, Any]) -> lineage.SplitPolicy | None:
    """The pinned split policy, when the catalog carries one, bound to its digest."""

    if "split_policy" not in meta:
        return None
    policy = lineage.SplitPolicy.from_json(meta["split_policy"])
    cv.refuse_when(
        meta.get("split_policy_sha256") != policy.sha256, cv.FINDING_SPLIT_POLICY_INVALID,
        f"{CATALOG_FILENAME}.split_policy_sha256 does not match the policy",
    )
    return policy


def _license_sha256(directory: Path, meta: dict[str, Any]) -> str:
    path = directory / LICENSE_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cv.refuse_when(
        digest != meta["upstream"]["license_sha256"], cv.FINDING_CATALOG_FIELD_INVALID,
        f"{CATALOG_FILENAME}.upstream.license_sha256 does not match {LICENSE_FILENAME}",
    )
    return digest


def load_catalog(directory: Path | str) -> Catalog:
    """Load and verify every pin of the catalog at ``directory``; refuses with coded findings."""

    root = Path(directory)
    meta = _meta(root)
    programs, digest = _programs(root)
    for program in programs:
        _provenance_agrees(program, meta)
    cv.refuse_first((
        (digest != meta["programs_sha256"], cv.FINDING_PROGRAMS_SHA_MISMATCH,
         f"{PROGRAMS_FILENAME} does not hash to {CATALOG_FILENAME}.programs_sha256"),
        (len(programs) != meta["program_count"], cv.FINDING_CATALOG_FIELD_INVALID,
         f"{CATALOG_FILENAME}.program_count is not the number of programs"),
    ))
    return Catalog(
        meta["catalog_id"], root, meta, digest, _license_sha256(root, meta), programs,
        _split_policy(meta),
    )


bind_import_twin(__name__)
