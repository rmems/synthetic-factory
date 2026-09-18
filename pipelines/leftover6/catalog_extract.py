#!/usr/bin/env python3
"""AST-extract leftover6 pair and plant catalogs.

Unpinned input requires literal assignments and proven ``dict`` / ``_row`` calls.
Exact pinned archives use AST text projection, not runtime-equivalence claims.
Compiler validation discards its code object; no mill is imported or executed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import catalog_ast as _catalog_ast
from . import catalog_literals as _catalog_literals
from ._contract import bind_import_twin
from .catalog_ast import module_constants
from .catalog_literals import SBOX_PLANT_FIELDS, _LiteralMapping

assignment_of = _catalog_ast.assignment_of
UNSET = _catalog_literals.UNSET
literal_value = _catalog_literals.literal_value

@dataclass(frozen=True)
class SourceContext:
    path: str
    blob_sha: str
    digest: str
    lines: int

GQL_PATH = "experiments/mill_gql_leftover6_r260.py"
SSL_PATH = "experiments/ssl_r164_leftover6_mill.py"
SBOX_PATH = "experiments/sbox-mill-plants-leftover6.py"

GQL_PAIR_FIELDS = (
    "slug",
    "fail",
    "surf",
    "naive",
    "bind",
    "drop",
    "plant",
    "file",
    "test",
    "field",
    "ticket",
)
SSL_PAIR_FIELDS = (
    "slug",
    "lslug",
    "stack",
    "lstack",
    "obj",
    "naive",
    "fix",
    "docs",
    "novel",
    "new_vs",
    "ticket",
)



def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def extract_source(source: str, *, path: str, blob_sha: str = "") -> dict[str, Any]:
    payload = _catalog_ast.source_payload(source, path=path)
    _require_blob_identity(payload, blob_sha)
    constants = module_constants(source, path=path)
    digest = sha256_bytes(payload)
    lines = _source_line_count(source)
    context = SourceContext(path, blob_sha, digest, lines)
    builders = {GQL_PATH: _gql_record, SSL_PATH: _ssl_record, SBOX_PATH: _sbox_record}
    builder = builders.get(path)
    if builder is None:
        raise ValueError(f"unsupported leftover6 source {path}")
    return builder(constants, context)


def _require_blob_identity(payload: bytes, blob_sha: str) -> None:
    # Git scalar identity must not delegate equality to caller-defined objects.
    if type(blob_sha) is not str:
        raise ValueError("supplied blob SHA must be a plain string")
    framed = b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    expected = hashlib.sha1(framed, usedforsecurity=False).hexdigest()
    if blob_sha not in ("", expected):
        raise ValueError("supplied blob SHA does not identify the exact source bytes")


def _source_line_count(source: str) -> int:
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    return len(normalized.removesuffix("\n").split("\n")) if normalized else 0


def _require_str(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} is not a non-empty string")
    return value


def _require_int(value: Any, context: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} is not an int")
    if value < minimum:
        raise ValueError(f"{context} is below the minimum {minimum}")
    return value


def _gql_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    pairs_raw = constants.get("PAIRS")
    rows = _mapping_rows(pairs_raw, GQL_PAIR_FIELDS, path=path, name="PAIRS")
    return {
        "kind": "gql-pairs",
        "shape": "dict-kwargs",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": _require_str(constants.get("FAC"), f"{path} FAC"),
        "generator": _require_str(constants.get("GEN"), f"{path} GEN"),
        "catalog_first": 260,
        "n_rows": len(rows),
        "first_slug": rows[0]["slug"],
        "last_slug": rows[-1]["slug"],
        "rows": [
            {"kind": "gql-pairs", "round": 260 + index, **row} for index, row in enumerate(rows)
        ],
    }


def _ssl_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    pairs_raw = constants.get("PAIRS")
    rows = _mapping_rows(pairs_raw, SSL_PAIR_FIELDS, path=path, name="PAIRS")
    n_rounds = _require_int(constants.get("N_ROUNDS"), f"{path} N_ROUNDS")
    start = _require_int(constants.get("START"), f"{path} START", minimum=0)
    if n_rounds != len(rows):
        raise ValueError(f"{path} N_ROUNDS={n_rounds} disagrees with {len(rows)} pairs")
    return {
        "kind": "ssl-pairs",
        "shape": "literal-dicts",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": _require_str(constants.get("FACTORY"), f"{path} FACTORY"),
        "generator": _require_str(constants.get("GEN"), f"{path} GEN"),
        "catalog_first": start,
        "n_rows": len(rows),
        "first_slug": rows[0]["slug"],
        "last_slug": rows[-1]["slug"],
        "rows": [
            {"kind": "ssl-pairs", "round": start + index, **row} for index, row in enumerate(rows)
        ],
    }


def _sbox_record(constants: Mapping[str, Any], context: SourceContext) -> dict[str, Any]:
    path, blob_sha, digest, lines = context.path, context.blob_sha, context.digest, context.lines
    rows = _mapping_rows(constants.get("_ROWS"), SBOX_PLANT_FIELDS, path=path, name="_ROWS")
    first_inc = _ordered_sbox_increments(rows, path)
    return {
        "kind": "sbox-plants",
        "shape": "row-ctor",
        "path": path,
        "blob_sha": blob_sha,
        "sha256": digest,
        "source_lines": lines,
        "factory": "sandbox-refusal-factory",
        "generator": "grok-4.6",
        "catalog_first": first_inc,
        "n_rows": len(rows),
        "first_slug": rows[0]["family"],
        "last_slug": rows[-1]["family"],
        "rows": [{"kind": "sbox-plants", **row} for row in rows],
    }


def _ordered_sbox_increments(rows, path):
    first_inc = _require_int(rows[0]["inc"], f"{path} _ROWS[0].inc")
    for index, row in enumerate(rows):
        if row["inc"] != first_inc + 4 * index:
            raise ValueError(f"{path} _ROWS[{index}].inc does not follow the four-step sequence")
    return first_inc


def _mapping_rows(
    raw: Any,
    fields: tuple[str, ...],
    *,
    path: str,
    name: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path} {name} is not a non-empty literal list")
    rows = [_typed_mapping(item, fields, f"{path} {name}[{index}]")
            for index, item in enumerate(raw)]
    identity = "family" if fields == SBOX_PLANT_FIELDS else "slug"
    if len({row[identity] for row in rows}) != len(rows):
        raise ValueError(f"{path} {name} contains duplicate {identity} identities")
    return rows


def _typed_mapping(item: Any, fields: tuple[str, ...], context: str) -> dict[str, Any]:
    expected = {GQL_PAIR_FIELDS: "dict-kwargs", SSL_PAIR_FIELDS: "literal-dicts",
                SBOX_PLANT_FIELDS: "row-ctor"}[fields]
    if not isinstance(item, _LiteralMapping) or item.shape != expected:
        raise ValueError(f"{context} does not use the expected {expected} syntax")
    if set(item) != set(fields):
        raise ValueError(f"{context} keys drifted from {fields}")
    return {field: _field_value(field, item[field], context) for field in fields}


def _field_value(field: str, value: Any, context: str) -> Any:
    checker = _require_int if field in {"inc", "novel"} else _require_str
    return checker(value, f"{context}.{field}")


def dumps_jsonl(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        json.dumps(dict(row), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def dumps_header(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


bind_import_twin(__name__)
