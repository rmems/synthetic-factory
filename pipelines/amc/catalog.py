#!/usr/bin/env python3
"""Strict, read-only access to the extracted agent-memory-compaction catalog."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "amc"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
CATALOG_PATH = CATALOG_DIR / CATALOG_FILENAME
SCHEMA_VERSION = "amc-catalog-extract/v1"
FAMILY = "amc"
FACTORY = "agent-memory-compaction-factory"
GENERATOR = "grok-4.6"
FAMILY_PREFIX = "amc"
PRESERVE_COMMIT = "bb0775859c86d4692112c4845790fa1623ab8abb"
QUOTA_PER_ROUND = 2
SUCCESS_STEPS = 16
KIND_PAIRS = "pairs"
KIND_LOOP = "loop"
KIND_LEFTOVER = "leftover"
EXTRACTED_PAIR_ROWS = 1401
COMMITTED_PAIR_ROWS = 1401
DEFERRED_PAIR_ROWS = 1377
VENDOR_PREFIXES = ("amc-mill-", "amc-loop-", "mill_amc_")
FORBIDDEN_MILL_GLOBS = (
    "amc-mill*.py",
    "amc-loop*.py",
    "mill_amc*.py",
)
_CATALOG_KEYS = {
    "schema_version",
    "family",
    "factory",
    "generator",
    "source_branch",
    "source_commit",
    "extraction",
    "n_pair_rows_extracted",
    "n_pair_rows_committed",
    "quota_per_round",
    "success_steps",
    "catalogs",
    "loops",
}
_MILL_REQUIRED = {
    "source_path",
    "mill_id",
    "source_blob_sha1",
    "source_sha256",
    "kind",
    "shape",
    "catalog_first",
    "n_rows_extracted",
    "first_slug",
    "last_slug",
}
_MILL_OPTIONAL = {"n_prefix", "n_new", "prefix_mill", "max_rounds"}
_LOOP_KEYS = {"mill_id", "source_path", "source_blob_sha1", "companion_mill_path"}
_PAIR_KEYS = {
    "source_path",
    "mill_id",
    "role",
    "fail_slug",
    "success_slug",
    "fail_leftover",
    "success_leftover",
}
_LEFTOVER_PAIR_KEYS = {
    "source_path",
    "mill_id",
    "role",
    "fail_slug",
    "success_slug",
    "mod",
    "token",
}
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ROLE_FIRST = "first"
ROLE_LAST = "last"
ROLE_DEFERRED = "deferred"
_ROLES = frozenset({ROLE_FIRST, ROLE_LAST, ROLE_DEFERRED})


class CatalogError(ValueError):
    """The committed AMC catalog does not satisfy its closed schema."""


@dataclass(frozen=True)
class CompactPair:
    source_path: str
    mill_id: str
    role: str
    fail_slug: str
    success_slug: str
    fail_leftover: str = ""
    success_leftover: str = ""
    mod: str = ""
    token: str = ""


@dataclass(frozen=True)
class MillCatalog:
    source_path: str
    mill_id: str
    source_blob_sha1: str
    source_sha256: str
    kind: str
    shape: str
    catalog_first: int
    n_rows_extracted: int
    first_slug: str
    last_slug: str
    pairs: tuple[CompactPair, ...]
    n_prefix: int | None = None
    n_new: int | None = None
    prefix_mill: str | None = None
    max_rounds: int | None = None


@dataclass(frozen=True)
class LoopSource:
    mill_id: str
    source_path: str
    source_blob_sha1: str
    companion_mill_path: str


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    family: str
    factory: str
    generator: str
    source_branch: str
    source_commit: str
    extraction: str
    n_pair_rows_extracted: int
    n_pair_rows_committed: int
    quota_per_round: int
    success_steps: int
    catalogs: tuple[MillCatalog, ...]
    loops: tuple[LoopSource, ...]

    @property
    def mills(self) -> dict[str, MillCatalog]:
        return {mill.mill_id: mill for mill in self.catalogs}

    def pairs(self) -> Iterator[CompactPair]:
        for mill in self.catalogs:
            yield from mill.pairs


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is an AMC mill / loop / leftover publisher script."""

    return name.endswith(".py") and name.startswith(VENDOR_PREFIXES)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor an ``amc-mill*.py`` script."""

    for raw in paths:
        name = Path(raw).name
        if is_vendor_filename(name):
            raise SystemExit(f"refusing to vendor {name}")


def _mapping(value: Any, context: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CatalogError(f"{context} must be an object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise CatalogError(f"{context} keys differ: missing={missing}, extra={extra}")
    return value


def _mapping_subset(
    value: Any, context: str, required: set[str], optional: set[str]
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CatalogError(f"{context} must be an object")
    actual = set(value)
    missing = sorted(required - actual)
    extra = sorted(actual - required - optional)
    if missing or extra:
        raise CatalogError(f"{context} keys differ: missing={missing}, extra={extra}")
    return value


def _text(value: Any, context: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{context} must be a non-empty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise CatalogError(f"{context} has invalid format: {value!r}")
    return value


def _integer(value: Any, context: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogError(f"{context} must be an integer")
    if value < minimum:
        raise CatalogError(f"{context} out of range: {value}")
    return value


def _optional_int(value: Any, context: str) -> int | None:
    if value is None:
        return None
    return _integer(value, context, minimum=0)


def _require(ok: bool, message: str) -> None:
    if ok:
        return
    raise CatalogError(message)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load AMC catalog {path}: {exc}") from exc


def _load_jsonl(path: Path) -> list[Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"cannot load AMC catalog {path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise CatalogError(f"{path.name} must be LF-framed jsonl")
    rows: list[Any] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise CatalogError(f"{path.name}:{index} is empty")
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise CatalogError(f"{path.name}:{index} is not JSON: {exc}") from exc
    if not rows:
        raise CatalogError(f"{path.name} must contain at least one pair")
    return rows


def _pair_row(raw: Any, index: int, kinds: dict[str, str]) -> CompactPair:
    if not isinstance(raw, dict) or "mill_id" not in raw:
        raise CatalogError(f"{PAIRS_FILENAME}:{index} must name mill_id")
    mill_id = _text(raw["mill_id"], f"{PAIRS_FILENAME}:{index}.mill_id")
    kind = kinds.get(mill_id)
    if kind is None:
        raise CatalogError(f"{PAIRS_FILENAME}:{index} names unknown mill {mill_id}")
    keys = _LEFTOVER_PAIR_KEYS if kind == KIND_LEFTOVER else _PAIR_KEYS
    row = _mapping(raw, f"{PAIRS_FILENAME}:{index}", keys)
    role = _text(row["role"], f"{PAIRS_FILENAME}:{index}.role")
    _require(
        role in _ROLES,
        f"{PAIRS_FILENAME}:{index}.role must be first, last, or deferred",
    )
    pair = CompactPair(
        source_path=_text(row["source_path"], f"{PAIRS_FILENAME}:{index}.source_path"),
        mill_id=mill_id,
        role=role,
        fail_slug=_text(row["fail_slug"], f"{PAIRS_FILENAME}:{index}.fail_slug"),
        success_slug=_text(row["success_slug"], f"{PAIRS_FILENAME}:{index}.success_slug"),
        fail_leftover=row.get("fail_leftover", "") or "",
        success_leftover=row.get("success_leftover", "") or "",
        mod=row.get("mod", "") or "",
        token=row.get("token", "") or "",
    )
    if kind == KIND_LEFTOVER:
        _text(pair.mod, f"{PAIRS_FILENAME}:{index}.mod")
        _text(pair.token, f"{PAIRS_FILENAME}:{index}.token")
    return pair


def _split_roles(
    pairs: tuple[CompactPair, ...],
) -> tuple[list[CompactPair], list[CompactPair], list[CompactPair]]:
    first: list[CompactPair] = []
    last: list[CompactPair] = []
    deferred: list[CompactPair] = []
    buckets = {ROLE_FIRST: first, ROLE_LAST: last, ROLE_DEFERRED: deferred}
    for pair in pairs:
        buckets[pair.role].append(pair)
    return first, last, deferred


def _bookends(
    pairs: tuple[CompactPair, ...], context: str
) -> tuple[CompactPair, CompactPair, tuple[CompactPair, ...]]:
    first, last, deferred = _split_roles(pairs)
    _require(len(first) == 1, f"{context} must commit exactly one first pair")
    _require(len(last) == 1, f"{context} must commit exactly one last pair")
    return first[0], last[0], tuple(deferred)


def _bookend_slug(pair: CompactPair, kind: str) -> str:
    leftover_slugs = {KIND_LEFTOVER: pair.success_slug}
    return leftover_slugs.get(kind, pair.fail_slug)


def _refuse_mill_identities(
    pairs: tuple[CompactPair, ...],
    deferred: tuple[CompactPair, ...],
    n_rows: int,
    context: str,
) -> None:
    unique = {(pair.fail_slug, pair.success_slug) for pair in pairs}
    _require(
        len(pairs) == n_rows,
        f"{context} committed {len(pairs)} identities, expected {n_rows}",
    )
    _require(
        len(deferred) == n_rows - 2,
        f"{context} deferred identity count drifted from {n_rows - 2}",
    )
    _require(len(unique) == len(pairs), f"{context} repeats a compact pair identity")


def _mill(raw: Any, context: str, grouped: dict[str, list[CompactPair]]) -> MillCatalog:
    row = _mapping_subset(raw, context, _MILL_REQUIRED, _MILL_OPTIONAL)
    mill_id = _text(row["mill_id"], f"{context}.mill_id")
    pairs = tuple(grouped.get(mill_id, ()))
    first, last, deferred = _bookends(pairs, context)
    n_rows = _integer(row["n_rows_extracted"], f"{context}.n_rows_extracted", minimum=2)
    _refuse_mill_identities(pairs, deferred, n_rows, context)
    first_slug = _text(row["first_slug"], f"{context}.first_slug")
    last_slug = _text(row["last_slug"], f"{context}.last_slug")
    kind = _text(row["kind"], f"{context}.kind")
    _require(
        _bookend_slug(first, kind) == first_slug,
        f"{context} bookend slugs drifted from committed pairs",
    )
    _require(
        _bookend_slug(last, kind) == last_slug,
        f"{context} bookend slugs drifted from committed pairs",
    )
    source_path = _text(row["source_path"], f"{context}.source_path")
    foreign = [pair for pair in pairs if pair.source_path != source_path]
    _require(not foreign, f"{context} pair source_path drifted")
    return MillCatalog(
        source_path=source_path,
        mill_id=mill_id,
        source_blob_sha1=_text(row["source_blob_sha1"], f"{context}.source_blob_sha1", pattern=_SHA1),
        source_sha256=_text(row["source_sha256"], f"{context}.source_sha256", pattern=_SHA256),
        kind=kind,
        shape=_text(row["shape"], f"{context}.shape"),
        catalog_first=_integer(row["catalog_first"], f"{context}.catalog_first", minimum=1),
        n_rows_extracted=n_rows,
        first_slug=first_slug,
        last_slug=last_slug,
        pairs=pairs,
        n_prefix=_optional_int(row.get("n_prefix"), f"{context}.n_prefix"),
        n_new=_optional_int(row.get("n_new"), f"{context}.n_new"),
        prefix_mill=row.get("prefix_mill"),
        max_rounds=_optional_int(row.get("max_rounds"), f"{context}.max_rounds"),
    )


def _loop(raw: Any, context: str) -> LoopSource:
    row = _mapping(raw, context, _LOOP_KEYS)
    return LoopSource(
        mill_id=_text(row["mill_id"], f"{context}.mill_id"),
        source_path=_text(row["source_path"], f"{context}.source_path"),
        source_blob_sha1=_text(row["source_blob_sha1"], f"{context}.source_blob_sha1", pattern=_SHA1),
        companion_mill_path=_text(row["companion_mill_path"], f"{context}.companion_mill_path"),
    )


def _deferred_identity_count(catalog: Catalog) -> int:
    return sum(1 for pair in catalog.pairs() if pair.role == ROLE_DEFERRED)


def _refuse_identity(catalog: Catalog) -> None:
    extracted = sum(mill.n_rows_extracted for mill in catalog.catalogs)
    committed = sum(len(mill.pairs) for mill in catalog.catalogs)
    _require(
        catalog.schema_version == SCHEMA_VERSION,
        f"unsupported schema version: {catalog.schema_version!r}",
    )
    _require(catalog.family == FAMILY, "catalog identity does not match the reviewed AMC family")
    _require(catalog.factory == FACTORY, "catalog identity does not match the reviewed AMC family")
    _require(
        catalog.generator == GENERATOR,
        "catalog identity does not match the reviewed AMC family",
    )
    _require(catalog.source_commit == PRESERVE_COMMIT, "catalog preserve commit drifted")
    _require(
        catalog.n_pair_rows_extracted == EXTRACTED_PAIR_ROWS,
        "extracted pair-row pin drifted from 1401",
    )
    _require(
        catalog.n_pair_rows_committed == COMMITTED_PAIR_ROWS,
        "committed pair-row pin drifted from 1401",
    )
    _require(
        catalog.n_pair_rows_committed == catalog.n_pair_rows_extracted,
        "committed identities no longer cover the extracted set",
    )
    _require(catalog.quota_per_round == QUOTA_PER_ROUND, "quota or step pin drifted")
    _require(catalog.success_steps == SUCCESS_STEPS, "quota or step pin drifted")
    _require(extracted == EXTRACTED_PAIR_ROWS, "per-mill extracted counts no longer sum to 1401")
    _require(committed == COMMITTED_PAIR_ROWS, "per-mill extracted counts no longer sum to 1401")
    _require(
        _deferred_identity_count(catalog) == DEFERRED_PAIR_ROWS,
        "deferred identity count drifted from 1377",
    )
    _require(
        "1377 deferred" in catalog.extraction,
        "extraction note must record the deferred identity slice",
    )


def _refuse_duplicates(catalog: Catalog) -> None:
    mill_ids = [mill.mill_id for mill in catalog.catalogs]
    loop_ids = [loop.mill_id for loop in catalog.loops]
    if len(mill_ids) != len(set(mill_ids)):
        raise CatalogError("catalog repeats a mill id")
    if len(loop_ids) != len(set(loop_ids)):
        raise CatalogError("catalog repeats a loop id")
    if set(mill_ids) & set(loop_ids):
        raise CatalogError("catalog reuses a mill id as a loop id")
    if len(catalog.catalogs) != 12 or len(catalog.loops) != 11:
        raise CatalogError("expected 12 catalog mills and 11 loop pins")
    companions = {loop.companion_mill_path for loop in catalog.loops}
    mill_paths = {mill.source_path for mill in catalog.catalogs if mill.kind == KIND_PAIRS}
    if companions != mill_paths:
        raise CatalogError("loop companion paths drifted from catalog mills")


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    """Load and validate the extracted catalog without importing a legacy mill."""

    directory = path if path.is_dir() else path.parent
    row = _mapping(_load_json(directory / CATALOG_FILENAME), "catalog", _CATALOG_KEYS)
    raw_catalogs = row["catalogs"]
    raw_loops = row["loops"]
    if not isinstance(raw_catalogs, list) or not raw_catalogs:
        raise CatalogError("catalog.catalogs must be a non-empty list")
    if not isinstance(raw_loops, list) or not raw_loops:
        raise CatalogError("catalog.loops must be a non-empty list")
    kinds = {
        _text(item.get("mill_id"), f"catalog.catalogs[{index}].mill_id"): _text(
            item.get("kind"), f"catalog.catalogs[{index}].kind"
        )
        for index, item in enumerate(raw_catalogs)
        if isinstance(item, dict)
    }
    grouped: dict[str, list[CompactPair]] = {}
    for index, raw in enumerate(_load_jsonl(directory / PAIRS_FILENAME), start=1):
        pair = _pair_row(raw, index, kinds)
        grouped.setdefault(pair.mill_id, []).append(pair)
    extra = sorted(set(grouped) - set(kinds))
    if extra:
        raise CatalogError(f"{PAIRS_FILENAME} names unknown mills: {extra}")
    catalog = Catalog(
        schema_version=_text(row["schema_version"], "catalog.schema_version"),
        family=_text(row["family"], "catalog.family", pattern=_IDENTIFIER),
        factory=_text(row["factory"], "catalog.factory"),
        generator=_text(row["generator"], "catalog.generator"),
        source_branch=_text(row["source_branch"], "catalog.source_branch"),
        source_commit=_text(row["source_commit"], "catalog.source_commit", pattern=_SHA1),
        extraction=_text(row["extraction"], "catalog.extraction"),
        n_pair_rows_extracted=_integer(
            row["n_pair_rows_extracted"], "catalog.n_pair_rows_extracted", minimum=1
        ),
        n_pair_rows_committed=_integer(
            row["n_pair_rows_committed"], "catalog.n_pair_rows_committed", minimum=1
        ),
        quota_per_round=_integer(row["quota_per_round"], "catalog.quota_per_round", minimum=1),
        success_steps=_integer(row["success_steps"], "catalog.success_steps", minimum=1),
        catalogs=tuple(
            _mill(item, f"catalog.catalogs[{index}]", grouped)
            for index, item in enumerate(raw_catalogs)
        ),
        loops=tuple(_loop(item, f"catalog.loops[{index}]") for index, item in enumerate(raw_loops)),
    )
    _refuse_identity(catalog)
    _refuse_duplicates(catalog)
    return catalog


CATALOG = load_catalog()
