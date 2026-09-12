#!/usr/bin/env python3
"""Catalog directory loading and pin verification, split out of :mod:`.catalog`.

``catalog.py`` keeps the public types, doctest helpers and ``catalog_check``.
This module owns CATALOG.json / programs.jsonl / LICENSE.upstream reads so
``_meta`` is not one Complex Method and ``catalog.py`` stays under the
file-complexity gate.
"""

from __future__ import annotations

import ast
import hashlib
import io
import tokenize
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from . import catalog as cat
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json, oc

__all__ = ["load_catalog"]


def _missing_code(where: str) -> str:
    """Catalog metadata and program rows are told apart by the code, not only the prose."""

    if where.startswith(cat.CATALOG_FILENAME):
        return cv.FINDING_CATALOG_FIELD_MISSING
    return cv.FINDING_PROGRAM_FIELD_MISSING


def _invalid_code(where: str) -> str:
    if where.startswith(cat.CATALOG_FILENAME):
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
        (cat.sha256_text(text) != digest, cv.FINDING_PROGRAM_SHA256_MISMATCH,
         f"{where}.module.sha256 does not match the text"),
    ))
    _parse_or_refuse(text, f"{where}.module.text")
    return text, digest


def _require_utf8_cookie(text: str, where: str) -> None:
    """Refuse a coding cookie that would make UTF-8 bytes mean something else."""

    try:
        encoding, _lines = tokenize.detect_encoding(io.BytesIO(text.encode("utf-8")).readline)
    except SyntaxError as exc:
        message = f"{where} declares an unreadable encoding cookie: {exc}"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_FIELD_INVALID, message) from exc
    if encoding.lower() not in {"utf-8", "utf-8-sig"}:
        message = f"{where} declares encoding {encoding!r}; only UTF-8 is accepted"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_FIELD_INVALID, message)


def _parse_or_refuse(text: str, where: str) -> ast.Module:
    _require_utf8_cookie(text, where)
    try:
        tree = ast.parse(text)
        compile(tree, where, "exec")
        return tree
    except (SyntaxError, ValueError, MemoryError, RecursionError) as exc:
        message = f"{where} does not parse: {exc}"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_NOT_PARSEABLE, message) from exc


def _reference(row: dict[str, Any], where: str) -> cat.Reference:
    hidden = _field(row, "hidden", dict, where)
    block = _field(hidden, "reference", dict, f"{where}.hidden")
    kind = _field(block, "kind", str, f"{where}.hidden.reference")
    cv.refuse_when(
        kind not in cv.REFERENCE_KINDS, cv.FINDING_REFERENCE_KIND_UNKNOWN,
        f"{where}.hidden.reference.kind is not one of {sorted(cv.REFERENCE_KINDS)}",
    )
    if kind == cv.REFERENCE_SELF:
        return cat.Reference(kind)
    source = _field(block, "source", str, f"{where}.hidden.reference")
    digest = _field(block, "sha256", str, f"{where}.hidden.reference")
    function = _field(block, "function", str, f"{where}.hidden.reference")
    cv.refuse_when(
        cat.sha256_text(source) != digest, cv.FINDING_PROGRAM_SHA256_MISMATCH,
        f"{where}.hidden.reference.sha256 does not match its source",
    )
    _parse_or_refuse(source, f"{where}.hidden.reference.source")
    defs = cat.function_defs(source, function)
    cv.refuse_when(
        len(defs) > 1, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}.hidden.reference.source defines {function} more than once",
    )
    cv.refuse_when(
        not defs, cv.FINDING_TARGET_FUNCTION_NOT_FOUND,
        f"{where}.hidden.reference.source defines no module-level function {function}",
    )
    return cat.Reference(kind, function, source, digest)


def _cases(row: dict[str, Any], where: str) -> tuple[Mapping[str, str], ...]:
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
            len(args) > cat.MAX_CASE_ARGS_CHARS, cv.FINDING_PROGRAM_FIELD_INVALID,
            f"{spot}.args is longer than {cat.MAX_CASE_ARGS_CHARS} characters",
        )
        try:
            arguments = ast.literal_eval(args)
        except (ValueError, SyntaxError, RecursionError) as exc:
            raise cv.RepairRefusal(
                cv.FINDING_PROGRAM_FIELD_INVALID, f"{spot}.args is not a literal sequence"
            ) from exc
        cv.refuse_when(
            not isinstance(arguments, (tuple, list)), cv.FINDING_PROGRAM_FIELD_INVALID,
            f"{spot}.args must be a tuple or list of arguments",
        )
        parsed.append(MappingProxyType({"args": args, "want": want}))
    return tuple(parsed)


def _examples(row: dict[str, Any], text: str, function: str, where: str) -> tuple[cat.Example, ...]:
    public = _field(row, "public", dict, where)
    defs = cat.function_defs(text, function)
    cv.refuse_when(
        len(defs) > 1, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: target function {function} is defined more than once",
    )
    try:
        examples = cat.examples_of(text, function)
    except ValueError as exc:  # a malformed or report-controlling doctest directive
        message = f"{where}: {function} carries a doctest the parser refuses"
        raise cv.RepairRefusal(cv.FINDING_PROGRAM_FIELD_INVALID, message) from exc
    cv.refuse_first((
        (not defs, cv.FINDING_TARGET_FUNCTION_NOT_FOUND,
         f"{where}: no module-level function named {function}"),
        (not examples, cv.FINDING_TARGET_HAS_NO_DOCTEST, f"{where}: {function} carries no doctest"),
    ))
    count = _field(public, "example_count", int, f"{where}.public")
    cv.refuse_when(
        len(examples) > cat.MAX_PUBLIC_EXAMPLES, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}.public exceeds the {cat.MAX_PUBLIC_EXAMPLES}-example report budget",
    )
    pinned = _field(public, "examples_sha256", str, f"{where}.public")
    cv.refuse_when(
        count != len(examples) or pinned != cat.examples_sha256(examples),
        cv.FINDING_EXAMPLES_SHA_MISMATCH, f"{where}.public does not pin the docstring's examples",
    )
    return examples


def _split(row: dict[str, Any], where: str) -> tuple[str | None, str | None]:
    structure = row.get("structure")
    split = row.get("split")
    cv.refuse_when(
        (structure is not None and not isinstance(structure, dict))
        or (split is not None and split not in cat.SPLITS),
        cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: structure must be an object or null and split one of {cat.SPLITS} or null",
    )
    group_id = structure.get("group_id") if isinstance(structure, dict) else None
    cv.refuse_when(
        group_id is not None and not isinstance(group_id, str), cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: structure.group_id must be a string or null",
    )
    return group_id, split


def _freeze_mapping(value: Any) -> Any:
    """Deep-freeze nested provenance so a caller cannot detach it from the pin."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_mapping(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_mapping(item) for item in value)
    return value


def _program(row: Any, lineno: int) -> cat.Program:
    where = f"programs.jsonl:{lineno}"
    program_id = _field(row, "program_id", str, where)
    upstream = _field(row, "upstream", dict, where)
    for key in cat.UPSTREAM_FIELDS:
        _field(upstream, key, str, f"{where}.upstream")
    text, digest = _module_text(row, where)
    function = upstream["function"]
    group_id, split = _split(row, where)
    reference, cases = _reference(row, where), _cases(row, where)
    cv.refuse_when(
        reference.certifying and not cases, cv.FINDING_PROGRAM_FIELD_INVALID,
        f"{where}: a certifying reference needs at least one hidden case",
    )
    examples = _examples(row, text, function, where)
    return cat.Program(
        program_id, _field(row, "family", str, where), _freeze_mapping(upstream), text, digest,
        function, examples, cat.examples_sha256(examples), reference, cases, group_id, split,
    )


def _provenance_agrees(program: cat.Program, meta: dict[str, Any]) -> None:
    """A program's upstream must be the catalog's upstream (Greptile on #196)."""

    upstream = meta["upstream"]
    for key in ("repository", "commit", "license"):
        cv.refuse_when(
            program.upstream[key] != upstream[key], cv.FINDING_CATALOG_FIELD_INVALID,
            f"{program.program_id}: upstream.{key} contradicts {cat.CATALOG_FILENAME}",
        )


def _programs(directory: Path) -> tuple[tuple[cat.Program, ...], str]:
    path = directory / cat.PROGRAMS_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    try:
        data = path.read_bytes()  # one read: the digest and the parse cover the same bytes
    except OSError as exc:
        message = f"{path} could not be read: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FILE_MISSING, message) from exc
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


def _read_catalog_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        message = f"{path} could not be read: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FILE_MISSING, message) from exc
    except UnicodeDecodeError as exc:
        message = f"{path} is not UTF-8 text: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FIELD_INVALID, message) from exc


def _parse_catalog_json(raw: str, path: Path) -> dict[str, Any]:
    try:
        parsed = load_strict_json(raw)
    except (ValueError, RecursionError) as exc:
        message = f"{path} is not JSON: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FIELD_INVALID, message) from exc
    return parsed


def _require_catalog_identity(meta: dict[str, Any]) -> None:
    for key, kinds in (("format", str), ("catalog_id", str), ("upstream", dict),
                       ("programs_sha256", str), ("program_count", int)):
        _field(meta, key, kinds, cat.CATALOG_FILENAME)
    cv.refuse_when(
        meta["format"] != cv.CATALOG_FORMAT, cv.FINDING_CATALOG_FIELD_INVALID,
        f"{cat.CATALOG_FILENAME}.format must be {cv.CATALOG_FORMAT}",
    )
    for key in ("repository", "commit", "license", "license_sha256"):
        _field(meta["upstream"], key, str, f"{cat.CATALOG_FILENAME}.upstream")


def _meta(directory: Path) -> dict[str, Any]:
    path = directory / cat.CATALOG_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    meta = _parse_catalog_json(_read_catalog_text(path), path)
    _require_catalog_identity(meta)
    return meta


def _license_sha256(directory: Path, meta: dict[str, Any]) -> str:
    path = directory / cat.LICENSE_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_CATALOG_FILE_MISSING, f"{path} is missing")
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        message = f"{path} could not be read: {exc}"
        raise cv.RepairRefusal(cv.FINDING_CATALOG_FILE_MISSING, message) from exc
    cv.refuse_when(
        digest != meta["upstream"]["license_sha256"], cv.FINDING_CATALOG_FIELD_INVALID,
        f"{cat.CATALOG_FILENAME}.upstream.license_sha256 does not match {cat.LICENSE_FILENAME}",
    )
    return digest


def load_catalog(directory: Path | str) -> cat.Catalog:
    """Load and verify every pin of the catalog at ``directory``; refuses with coded findings."""

    root = Path(directory)
    meta = _meta(root)
    programs, digest = _programs(root)
    groups: dict[str, str | None] = {}
    for program in programs:
        _provenance_agrees(program, meta)
        if program.group_id is not None:
            cv.refuse_when(
                program.group_id in groups and groups[program.group_id] != program.split,
                cv.FINDING_PROGRAM_FIELD_INVALID,
                f"{program.program_id}: group {program.group_id} spans different splits",
            )
            groups[program.group_id] = program.split
    cv.refuse_first((
        (not programs, cv.FINDING_CATALOG_FIELD_INVALID,
         f"{cat.PROGRAMS_FILENAME} holds no programs"),
        (digest != meta["programs_sha256"], cv.FINDING_PROGRAMS_SHA_MISMATCH,
         f"{cat.PROGRAMS_FILENAME} does not hash to {cat.CATALOG_FILENAME}.programs_sha256"),
        (len(programs) != meta["program_count"], cv.FINDING_CATALOG_FIELD_INVALID,
         f"{cat.CATALOG_FILENAME}.program_count is not the number of programs"),
    ))
    return cat.Catalog(
        meta["catalog_id"], root, meta, digest, _license_sha256(root, meta), programs
    )


bind_import_twin(__name__)
