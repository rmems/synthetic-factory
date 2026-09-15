#!/usr/bin/env python3
"""AST-extracted IRC pipe-row catalog (SPECS/ROWS literals only).

``CATALOG.json`` pins every file on ``origin/legacy-mill-lane`` @ ``813f93f``.
``specs.jsonl`` holds compact pipe rows for mills through r4481. Later mills,
loops, chains, and the unrecoverable ``/tmp/irc_mill_r3234.py`` helper stay
off-repo; rows are never executed to build plants.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    CATALOG_FILENAME,
    CATALOG_ID,
    COMMITTED_MILL_CATALOGS,
    COMMITTED_SPEC_ROW_COUNT,
    FACTORY,
    FAMILY_LANE_COMMIT,
    FAMILY_PREFIX,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_CATALOG_FIELD_MISSING,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_SOURCE_NOT_PARSEABLE,
    FULL_MILL_CATALOGS,
    FULL_SPEC_ROW_COUNT,
    GENERATOR,
    IrcRefusal,
    PIPE_FIELD_NAMES,
    SOURCE_REF,
    SPECS_FILENAME,
    bind_import_twin,
    repo_root,
    load_strict_json,
    package_dir,
    refuse,
    refuse_first,
    refuse_when,
    shown,
)

__all__ = [
    "FamilyCatalog",
    "SpecRow",
    "catalog_family_check",
    "catalog_path",
    "load_family_catalog",
    "pipe_rows_from_source",
    "specs_path",
]

REQUIRED_META = ("catalog_id", "family", "schema", "factory", "generator", "source", "extract", "sources")


@dataclass(frozen=True)
class SpecRow:
    mill_round: int
    index: int
    pipe: str
    path: str
    field: str


@dataclass(frozen=True)
class FamilyCatalog:
    catalog_id: str
    sources: tuple[Mapping[str, Any], ...]
    spec_rows: tuple[SpecRow, ...]

    @property
    def committed_spec_rows(self) -> int:
        return len(self.spec_rows)


def package_dir_path() -> Path:
    return package_dir()


def catalog_path() -> Path:
    return package_dir_path() / CATALOG_FILENAME


def specs_path() -> Path:
    return package_dir_path() / SPECS_FILENAME


def _as_mapping(value: Any, where: str) -> dict[str, Any]:
    refuse_when(
        not isinstance(value, dict),
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be an object",
    )
    return value


def _as_str(value: Any, where: str) -> str:
    refuse_when(
        not isinstance(value, str) or not value,
        FINDING_CATALOG_FIELD_INVALID,
        f"{where} must be a non-empty string, got {shown(value)}",
    )
    return value


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


def _parse_jsonl_line(line: str, line_no: int) -> dict[str, Any]:
    refuse_when(not line.strip(), FINDING_CATALOG_FIELD_INVALID, f"{SPECS_FILENAME}:{line_no}: empty line")
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        raise IrcRefusal(FINDING_CATALOG_FIELD_INVALID, f"{SPECS_FILENAME}:{line_no}: {exc}") from exc
    return _as_mapping(row, f"{SPECS_FILENAME}:{line_no}")


def _load_spec_rows(path: Path) -> tuple[SpecRow, ...]:
    refuse_when(not path.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {path}")
    rows: list[SpecRow] = []
    headers: dict[int, tuple[str, str, str]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = _parse_jsonl_line(line, line_no)
        if "pipe" not in item:
            mill_round = item.get("mill_round")
            refuse_when(type(mill_round) is not int, FINDING_CATALOG_FIELD_INVALID, "mill header missing mill_round")
            headers[mill_round] = (
                _as_str(item.get("path"), "path"),
                _as_str(item.get("field"), "field"),
                _as_str(item.get("sha256"), "sha256"),
            )
            continue
        mill_round = item.get("mill_round")
        index = item.get("index")
        refuse_when(type(mill_round) is not int or type(index) is not int,
                    FINDING_CATALOG_FIELD_INVALID, f"{SPECS_FILENAME}:{line_no}: row keys")
        header = headers.get(mill_round)
        refuse_when(header is None, FINDING_CATALOG_FIELD_INVALID, f"missing header for mill {mill_round}")
        path_text, field, _digest = header
        rows.append(
            SpecRow(
                mill_round=mill_round,
                index=index,
                pipe=_as_str(item.get("pipe"), "pipe"),
                path=path_text,
                field=field,
            )
        )
    refuse_when(len(rows) != COMMITTED_SPEC_ROW_COUNT, FINDING_CATALOG_FIELD_INVALID,
                f"expected {COMMITTED_SPEC_ROW_COUNT} spec rows, got {len(rows)}")
    return tuple(rows)


def load_family_catalog() -> FamilyCatalog:
    catalog_file = catalog_path()
    refuse_when(not catalog_file.is_file(), FINDING_CATALOG_FILE_MISSING, f"missing {catalog_file}")
    meta = _as_mapping(load_strict_json(catalog_file.read_text(encoding="utf-8")), CATALOG_FILENAME)
    missing = [key for key in REQUIRED_META if key not in meta]
    refuse_when(bool(missing), FINDING_CATALOG_FIELD_MISSING, f"{CATALOG_FILENAME} missing {missing}")
    refuse_first((
        (meta.get("catalog_id") != CATALOG_ID, FINDING_CATALOG_FIELD_INVALID,
         f"catalog_id {shown(meta.get('catalog_id'))} != {CATALOG_ID}"),
        (meta.get("family") != FAMILY_PREFIX, FINDING_CATALOG_FIELD_INVALID,
         f"family {shown(meta.get('family'))} != {FAMILY_PREFIX}"),
        (meta.get("factory") != FACTORY, FINDING_CATALOG_FIELD_INVALID,
         f"factory {shown(meta.get('factory'))} != {FACTORY}"),
        (meta.get("generator") != GENERATOR, FINDING_CATALOG_FIELD_INVALID,
         f"generator {shown(meta.get('generator'))} != {GENERATOR}"),
    ))
    source = _as_mapping(meta.get("source"), "source")
    refuse_when(source.get("commit") != FAMILY_LANE_COMMIT, FINDING_CATALOG_FIELD_INVALID, "source.commit drift")
    extract = _as_mapping(meta.get("extract"), "extract")
    refuse_first((
        (extract.get("full_spec_row_count") != FULL_SPEC_ROW_COUNT, FINDING_CATALOG_FIELD_INVALID, "extract.full_spec_row_count"),
        (extract.get("committed_spec_row_count") != COMMITTED_SPEC_ROW_COUNT, FINDING_CATALOG_FIELD_INVALID, "committed_spec_row_count"),
        (extract.get("full_mill_catalogs") != FULL_MILL_CATALOGS, FINDING_CATALOG_FIELD_INVALID, "full_mill_catalogs"),
        (extract.get("committed_mill_catalogs") != COMMITTED_MILL_CATALOGS, FINDING_CATALOG_FIELD_INVALID, "committed_mill_catalogs"),
    ))
    sources_raw = meta.get("sources")
    refuse_when(not isinstance(sources_raw, list) or not sources_raw,
                FINDING_CATALOG_FIELD_INVALID, "sources must be a non-empty array")
    sources = tuple(_as_mapping(item, "sources[]") for item in sources_raw)
    spec_rows = _load_spec_rows(specs_path())
    return FamilyCatalog(catalog_id=CATALOG_ID, sources=sources, spec_rows=spec_rows)


def pipe_rows_from_source(source: str) -> tuple[str, tuple[str, ...]]:
    """Parse ``SPECS`` or ``ROWS`` with ``ast.parse`` / ``literal_eval`` only."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise IrcRefusal(FINDING_SOURCE_NOT_PARSEABLE, str(exc)) from exc
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if targets and targets[0] in PIPE_FIELD_NAMES:
                try:
                    literal = ast.literal_eval(node.value)
                except (TypeError, ValueError, SyntaxError) as exc:
                    raise IrcRefusal(FINDING_SOURCE_NOT_PARSEABLE, str(exc)) from exc
                refuse_when(not isinstance(literal, str), FINDING_SOURCE_NOT_PARSEABLE, "field not str")
                rows = tuple(
                    line for line in literal.splitlines() if line.strip() and not line.startswith("#")
                )
                return targets[0], rows
    refuse(FINDING_SOURCE_NOT_PARSEABLE, f"missing one of {PIPE_FIELD_NAMES}")


def _legacy_source(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{SOURCE_REF}:{path}"],
        text=True,
        cwd=repo_root(),
        stderr=subprocess.DEVNULL,
    )


def catalog_family_check(live_legacy: bool = True) -> FamilyCatalog:
    catalog = load_family_catalog()
    if not live_legacy:
        return catalog
    try:
        subprocess.check_output(["git", "rev-parse", SOURCE_REF], cwd=repo_root(), stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return catalog
    for source in catalog.sources:
        path = source.get("path")
        expected = source.get("sha256")
        if not isinstance(path, str) or not isinstance(expected, str):
            continue
        if not path.startswith("experiments/irc-mill-r"):
            continue
        if source.get("committed") is not True:
            continue
        live = _legacy_source(path)
        digest = _sha256_text(live)
        refuse_when(digest != expected, FINDING_CATALOG_SHA256_MISMATCH, path)
        field, rows = pipe_rows_from_source(live)
        refuse_when(field != source.get("field"), FINDING_CATALOG_SHA256_MISMATCH, f"{path} field")
        refuse_when(len(rows) != source.get("n_rows_extracted"), FINDING_CATALOG_SHA256_MISMATCH, f"{path} n_rows")
    grouped: dict[int, list[SpecRow]] = {}
    for row in catalog.spec_rows:
        grouped.setdefault(row.mill_round, []).append(row)
    for mill_round, rows in grouped.items():
        rows_sorted = sorted(rows, key=lambda item: item.index)
        for index, row in enumerate(rows_sorted):
            refuse_when(row.index != index, FINDING_CATALOG_FIELD_INVALID, f"mill {mill_round} index gap")
    return catalog


def iter_committed_mill_rounds(sources: Iterable[Mapping[str, Any]]) -> tuple[int, ...]:
    rounds: list[int] = []
    for source in sources:
        path = source.get("path", "")
        if not isinstance(path, str) or not path.startswith("experiments/irc-mill-r"):
            continue
        if source.get("committed") is not True:
            continue
        match = path.rsplit("r", 1)[-1]
        if match.endswith(".py") and match[:-3].isdigit():
            rounds.append(int(match[:-3]))
    return tuple(sorted(rounds))


bind_import_twin(__name__)
