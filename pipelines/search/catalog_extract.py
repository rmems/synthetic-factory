#!/usr/bin/env python3
"""AST-extract search leftover-mill catalog identity from a mill source.

Evaluates only literal catalog assignments (``FACTORY``, ``GEN``,
``CATALOG_FIRST``, ``N_ROUNDS``, ``HOP``, ``PAIRS``). Does not import, compile,
or exec the leftover3 / leftover-lll publishers, so those scripts stay off
this branch.
"""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_ast import UNSET, assignment_of, literal_value, module_docstring
from .identity import leftover_marker_in, refuse_cataloged_leftover_mill
from .vocabulary import (
    CATALOG_FILENAME,
    CATALOG_SCHEMA_ID,
    FACTORY,
    FAMILY,
    GENERATOR,
    HOME_PRESERVE_COMMIT,
    KIND_HOME_PAIRS,
    KIND_LEFTOVER_PAIRS,
    LEGACY_REF,
    PRESERVE_COMMIT,
    R31_BLOB_SHA,
    R31_CATALOG_FIRST,
    R31_FIRST_SLUG,
    R31_HEADER_FILENAME,
    R31_HEADER_SCHEMA_ID,
    R31_JSONL_FILENAME,
    R31_JSONL_SHA256,
    R31_LAST_SLUG,
    R31_MILL_ID,
    R31_N_ROWS,
    R31_PATH,
    R31_SHA256,
    R31_SLICE_ID,
    R52_BLOB_SHA,
    R52_CATALOG_FIRST,
    R52_FIRST_SLUG,
    R52_HEADER_FILENAME,
    R52_HEADER_SCHEMA_ID,
    R52_JSONL_FILENAME,
    R52_JSONL_SHA256,
    R52_LAST_SLUG,
    R52_MILL_ID,
    R52_N_ROWS,
    R52_PATH,
    R52_SHA256,
    R52_SLICE_ID,
    R72_BLOB_SHA,
    R72_CATALOG_FIRST,
    R72_FIRST_SLUG,
    R72_HEADER_FILENAME,
    R72_HEADER_SCHEMA_ID,
    R72_JSONL_FILENAME,
    R72_JSONL_SHA256,
    R72_LAST_SLUG,
    R72_MILL_ID,
    R72_N_ROWS,
    R72_PATH,
    R72_SHA256,
    R72_SLICE_ID,
    SHAPE_PAIR_6TUPLES,
    SLICE_ID,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def mill_id_for_path(path: str) -> str:
    return Path(path).stem


def extract_home_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """AST-extract a home-factory mill (no hops). Leftover3 / leftover-lll refused."""

    refuse_cataloged_leftover_mill(path)
    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    hops = constants.get("HOP")
    if hops:
        raise ValueError(f"{path} has HOP destinations; leftover hops stay cataloged")
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    if not isinstance(factory, str) or not factory:
        raise ValueError(f"{path} FACTORY is not a non-empty string")
    if not isinstance(generator, str) or not generator:
        raise ValueError(f"{path} GEN is not a non-empty string")
    if not isinstance(catalog_first, int) or isinstance(catalog_first, bool):
        raise ValueError(f"{path} CATALOG_FIRST is not an int")
    rows = _pair_rows(constants.get("PAIRS"), path=path)
    _refuse_leftover_pair_markers(rows, path=path)
    n_rounds = constants.get("N_ROUNDS")
    if n_rounds is not None and n_rounds != len(rows):
        raise ValueError(f"{path} N_ROUNDS={n_rounds} disagrees with {len(rows)} pairs")
    for offset, row in enumerate(rows):
        row["mill_id"] = mill_id
        row["round"] = catalog_first + offset
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_HOME_PAIRS,
        "shape": SHAPE_PAIR_6TUPLES,
        "catalog_first": catalog_first,
        "n_rounds": len(rows),
        "n_rows": len(rows),
        "n_hops": 0,
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "generator": generator,
        "factory": factory,
        "hops": [],
        "doc_first_line": _first_line(module_docstring(tree)),
        "pairs": rows,
        "slice": mill_id,
    }


def extract_mill_catalog(
    source: str,
    *,
    path: str,
    blob_sha: str = "",
) -> dict[str, Any]:
    """Structured catalog extract for one leftover-mill source file."""

    payload = source.encode()
    tree = ast.parse(source, filename=path)
    mill_id = mill_id_for_path(path)
    constants = _module_constants(tree)
    factory = constants.get("FACTORY", FACTORY)
    generator = constants.get("GEN", GENERATOR)
    catalog_first = constants.get("CATALOG_FIRST")
    n_rounds = constants.get("N_ROUNDS")
    hops = constants.get("HOP")
    pairs_raw = constants.get("PAIRS")
    if not isinstance(factory, str) or not factory:
        raise ValueError(f"{path} FACTORY is not a non-empty string")
    if not isinstance(generator, str) or not generator:
        raise ValueError(f"{path} GEN is not a non-empty string")
    if not isinstance(catalog_first, int):
        raise ValueError(f"{path} CATALOG_FIRST is not an int")
    if not isinstance(n_rounds, int) or n_rounds < 1:
        raise ValueError(f"{path} N_ROUNDS is not a positive int")
    if not _is_factory_list(hops):
        raise ValueError(f"{path} HOP is not a literal list of factory slugs")
    rows = _pair_rows(pairs_raw, path=path)
    if len(rows) != n_rounds:
        raise ValueError(f"{path} N_ROUNDS={n_rounds} disagrees with {len(rows)} pairs")
    return {
        "mill_id": mill_id,
        "path": path,
        "blob_sha": blob_sha,
        "sha256": sha256_bytes(payload),
        "kind": KIND_LEFTOVER_PAIRS,
        "shape": SHAPE_PAIR_6TUPLES,
        "catalog_first": catalog_first,
        "n_rounds": n_rounds,
        "n_rows": len(rows),
        "n_hops": len(hops),
        "first_slug": rows[0]["success_slug"],
        "last_slug": rows[-1]["success_slug"],
        "generator": generator,
        "factory": factory,
        "hops": list(hops),
        "doc_first_line": _first_line(module_docstring(tree)),
        "pairs": rows,
    }


def _module_constants(tree: ast.AST) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in getattr(tree, "body", ()):
        name, value = assignment_of(node)
        if name is None or value is None:
            continue
        resolved = literal_value(value, env)
        if resolved is not UNSET:
            env[name] = resolved
    return env


def _is_factory_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, str) and item.endswith("-factory") for item in value)


def _pair_rows(pairs_raw: Any, *, path: str) -> list[dict[str, Any]]:
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise ValueError(f"{path} PAIRS is not a non-empty literal list")
    rows: list[dict[str, Any]] = []
    for index, pair in enumerate(pairs_raw):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"{path} PAIRS[{index}] is not a 2-tuple")
        success, fail = pair
        if not _is_six_strings(success) or not _is_six_strings(fail):
            raise ValueError(f"{path} PAIRS[{index}] arms are not 6-string tuples")
        rows.append(
            {
                "success_slug": success[0],
                "fail_slug": fail[0],
                "success_engine": success[1],
                "fail_engine": fail[1],
                "success_wrong": success[2],
                "fail_wrong": fail[2],
                "success_fix": success[3],
                "fail_leftover": fail[3],
                "success_ticket": success[4],
                "fail_ticket": fail[4],
                "success_url": success[5],
                "fail_url": fail[5],
                "fail_handoff": True,
            }
        )
    return rows


def _refuse_leftover_pair_markers(rows: list[dict[str, Any]], *, path: str) -> None:
    for index, row in enumerate(rows):
        for key in ("success_slug", "fail_slug"):
            slug = row[key]
            if leftover_marker_in(slug):
                raise ValueError(
                    f"{path} PAIRS[{index}].{key} is leftover3/lll already cataloged: {slug}"
                )


def _is_six_strings(arm: Any) -> bool:
    return (
        isinstance(arm, (tuple, list))
        and len(arm) == 6
        and all(isinstance(item, str) and item for item in arm)
    )


def _first_line(doc: str) -> str:
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def mill_summary(record: Mapping[str, Any], *, include_pairs: bool) -> dict[str, Any]:
    """Catalog mill row: identity plus optional pair list."""

    summary = {
        "mill_id": record["mill_id"],
        "path": record["path"],
        "blob_sha": record["blob_sha"],
        "sha256": record["sha256"],
        "kind": record["kind"],
        "shape": record["shape"],
        "catalog_first": record["catalog_first"],
        "n_rounds": record["n_rounds"],
        "n_rows": record["n_rows"],
        "n_hops": record["n_hops"],
        "first_slug": record["first_slug"],
        "last_slug": record["last_slug"],
        "generator": record["generator"],
        "factory": record["factory"],
        "hops": list(record["hops"]),
        "doc_first_line": record["doc_first_line"],
    }
    if include_pairs:
        summary["pairs"] = list(record.get("pairs") or ())
    return summary


def catalog_document(mills: list[dict[str, Any]]) -> dict[str, Any]:
    pair_rows = sum(mill["n_rows"] for mill in mills)
    return {
        "schema": CATALOG_SCHEMA_ID,
        "source_ref": LEGACY_REF,
        "preserve_commit": PRESERVE_COMMIT,
        "factory": FACTORY,
        "generator": GENERATOR,
        "slice": SLICE_ID,
        "n_mills": len(mills),
        "n_pair_rows": pair_rows,
        "mills": {mill["mill_id"]: mill for mill in mills},
    }


def dumps_catalog(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def catalog_json_path(package_dir: Path | None = None) -> Path:
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / CATALOG_FILENAME


@dataclass(frozen=True)
class HomeMillPins:
    mill_id: str
    slice_id: str
    path: str
    blob_sha: str
    source_sha256: str
    catalog_first: int
    n_rows: int
    first_slug: str
    last_slug: str
    jsonl_filename: str
    header_filename: str
    header_schema_id: str
    jsonl_sha256: str


HOME_MILL_PINS: dict[str, HomeMillPins] = {
    R31_MILL_ID: HomeMillPins(
        R31_MILL_ID,
        R31_SLICE_ID,
        R31_PATH,
        R31_BLOB_SHA,
        R31_SHA256,
        R31_CATALOG_FIRST,
        R31_N_ROWS,
        R31_FIRST_SLUG,
        R31_LAST_SLUG,
        R31_JSONL_FILENAME,
        R31_HEADER_FILENAME,
        R31_HEADER_SCHEMA_ID,
        R31_JSONL_SHA256,
    ),
    R52_MILL_ID: HomeMillPins(
        R52_MILL_ID,
        R52_SLICE_ID,
        R52_PATH,
        R52_BLOB_SHA,
        R52_SHA256,
        R52_CATALOG_FIRST,
        R52_N_ROWS,
        R52_FIRST_SLUG,
        R52_LAST_SLUG,
        R52_JSONL_FILENAME,
        R52_HEADER_FILENAME,
        R52_HEADER_SCHEMA_ID,
        R52_JSONL_SHA256,
    ),
    R72_MILL_ID: HomeMillPins(
        R72_MILL_ID,
        R72_SLICE_ID,
        R72_PATH,
        R72_BLOB_SHA,
        R72_SHA256,
        R72_CATALOG_FIRST,
        R72_N_ROWS,
        R72_FIRST_SLUG,
        R72_LAST_SLUG,
        R72_JSONL_FILENAME,
        R72_HEADER_FILENAME,
        R72_HEADER_SCHEMA_ID,
        R72_JSONL_SHA256,
    ),
}


def home_mill_pins(mill_id: str) -> HomeMillPins:
    try:
        return HOME_MILL_PINS[mill_id]
    except KeyError as exc:
        raise KeyError(f"unknown search home mill {mill_id!r}") from exc


def home_jsonl_path(mill_id: str, package_dir: Path | None = None) -> Path:
    pins = home_mill_pins(mill_id)
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / pins.jsonl_filename


def home_header_path(mill_id: str, package_dir: Path | None = None) -> Path:
    pins = home_mill_pins(mill_id)
    root = package_dir if package_dir is not None else Path(__file__).resolve().parent
    return root / pins.header_filename


def r72_jsonl_path(package_dir: Path | None = None) -> Path:
    return home_jsonl_path(R72_MILL_ID, package_dir)


def r72_header_path(package_dir: Path | None = None) -> Path:
    return home_header_path(R72_MILL_ID, package_dir)


def home_header_document(
    record: Mapping[str, Any], *, pairs_sha256: str, pins: HomeMillPins
) -> dict[str, Any]:
    return {
        "extraction": (
            "AST literals only; leftover3/lll mills already cataloged are refused; never exec"
        ),
        "factory": FACTORY,
        "family": FAMILY,
        "generator": GENERATOR,
        "mill": {
            "blob_sha": record["blob_sha"],
            "catalog_first": record["catalog_first"],
            "first_slug": record["first_slug"],
            "kind": record["kind"],
            "last_slug": record["last_slug"],
            "mill_id": record["mill_id"],
            "n_hops": record["n_hops"],
            "n_rows": record["n_rows"],
            "path": record["path"],
            "sha256": record["sha256"],
        },
        "n_rows": record["n_rows"],
        "pairs_filename": pins.jsonl_filename,
        "pairs_sha256": pairs_sha256,
        "preserve_commit": HOME_PRESERVE_COMMIT,
        "schema": pins.header_schema_id,
        "slice": pins.slice_id,
        "source_ref": LEGACY_REF,
    }


def r72_header_document(record: Mapping[str, Any], *, pairs_sha256: str) -> dict[str, Any]:
    return home_header_document(record, pairs_sha256=pairs_sha256, pins=HOME_MILL_PINS[R72_MILL_ID])


def dumps_home_header(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def dumps_r72_header(document: Mapping[str, Any]) -> str:
    return dumps_home_header(document)


def load_home_header(mill_id: str, path: Path | None = None) -> dict[str, Any]:
    pins = home_mill_pins(mill_id)
    header_path = path if path is not None else home_header_path(mill_id)
    document = json.loads(header_path.read_text(encoding="utf-8"))
    if document.get("schema") != pins.header_schema_id:
        raise ValueError(f"{header_path} schema is not {pins.header_schema_id}")
    if document.get("slice") != pins.slice_id:
        raise ValueError(f"{header_path} slice drifted from vocabulary")
    if document.get("preserve_commit") != HOME_PRESERVE_COMMIT:
        raise ValueError(f"{header_path} preserve_commit drifted from vocabulary")
    if document.get("pairs_sha256") != pins.jsonl_sha256:
        raise ValueError(f"{header_path} pairs_sha256 drifted from vocabulary")
    return document


def load_r72_header(path: Path | None = None) -> dict[str, Any]:
    return load_home_header(R72_MILL_ID, path)


def dumps_pair_jsonl(pairs: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
        for row in pairs
    )


def load_home_rows(mill_id: str, path: Path | None = None) -> list[dict[str, Any]]:
    pins = home_mill_pins(mill_id)
    jsonl_path = path if path is not None else home_jsonl_path(mill_id)
    payload = jsonl_path.read_bytes()
    digest = sha256_bytes(payload)
    if path is None and digest != pins.jsonl_sha256:
        raise ValueError(f"{jsonl_path} sha256 {digest} != pinned {pins.jsonl_sha256}")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line:
            raise ValueError(f"{jsonl_path} line {line_no} is empty")
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{jsonl_path} line {line_no} is not an object")
        if leftover_marker_in(str(row.get("success_slug", ""))) or leftover_marker_in(
            str(row.get("fail_slug", ""))
        ):
            raise ValueError(f"{jsonl_path} line {line_no} is leftover3/lll already cataloged")
        if row.get("mill_id") != mill_id:
            raise ValueError(f"{jsonl_path} line {line_no} mill_id is not {mill_id}")
        rows.append(row)
    return rows


def load_r72_rows(path: Path | None = None) -> list[dict[str, Any]]:
    return load_home_rows(R72_MILL_ID, path)


def write_catalog_document(document: Mapping[str, Any], path: Path | None = None) -> Path:
    destination = path if path is not None else catalog_json_path()
    destination.write_text(dumps_catalog(document), encoding="utf-8")
    return destination


def write_r72_jsonl(pairs: list[Mapping[str, Any]], path: Path | None = None) -> Path:
    destination = path if path is not None else r72_jsonl_path()
    destination.write_text(dumps_pair_jsonl(pairs), encoding="utf-8")
    return destination
