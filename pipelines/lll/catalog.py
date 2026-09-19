#!/usr/bin/env python3
"""Strict, read-only access to the leftover leftover leftover case catalog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "lll"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
CATALOG_PATH = CATALOG_DIR / CATALOG_FILENAME
SCHEMA_VERSION = "lll-case-catalog-v1"
FAMILY = "lll"
FACTORY = "email-webhook-retry-factory"
PREFIX = "ewr"
GENERATOR = "grok-4.6"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_MODULE = re.compile(r"^[a-z0-9]+$")
_TEST = re.compile(r"^test_[a-z0-9_]+$")
_BANNED = ("beehiiv", "constant-contact", "constant_contact", "sir-")
_CATALOG_KEYS = {
    "schema_version",
    "family",
    "factory",
    "prefix",
    "generator",
    "source_branch",
    "source_commit",
    "extraction",
    "catalogs",
}
_SOURCE_META_KEYS = {
    "source_path",
    "source_format",
    "source_blob_sha1",
    "source_sha256",
    "source_lines",
    "catalog_first",
    "pair_count",
    "first_slug",
    "last_slug",
}
_PAIR_ROW_KEYS = {
    "catalog_first",
    "handoff",
    "index",
    "round",
    "source_path",
    "success",
}
_SOURCE_KEYS = _SOURCE_META_KEYS | {"pairs"}
_SUCCESS_KEYS = {
    "docs",
    "domain",
    "esp",
    "evf",
    "idf",
    "mod",
    "naive",
    "short",
    "slug",
    "stack",
    "test",
}
_HANDOFF_KEYS = _SUCCESS_KEYS | {"ticket"}


class CatalogError(ValueError):
    """The committed leftover leftover leftover catalog does not satisfy its schema."""


@dataclass(frozen=True)
class SuccessCase:
    slug: str
    mod: str
    naive: str
    idf: str
    evf: str
    docs: tuple[str, str]
    domain: str
    stack: str
    test: str
    short: str
    esp: str


@dataclass(frozen=True)
class HandoffCase:
    slug: str
    mod: str
    naive: str
    idf: str
    evf: str
    docs: tuple[str, str]
    domain: str
    stack: str
    test: str
    short: str
    esp: str
    ticket: str


@dataclass(frozen=True)
class RoundPair:
    source_path: str
    catalog_first: int
    index: int
    round: int
    success: SuccessCase
    handoff: HandoffCase

    @property
    def mill_id(self) -> str:
        return f"r{self.catalog_first}"

    @property
    def record_ids(self) -> tuple[str, str]:
        prefix = f"ewr-r{self.catalog_first}-{self.index:02d}"
        return (f"{prefix}-{self.success.slug}", f"{prefix}-{self.handoff.slug}")


@dataclass(frozen=True)
class SourceCatalog:
    source_path: str
    source_format: str
    source_blob_sha1: str
    source_sha256: str
    source_lines: int
    catalog_first: int
    pair_count: int
    first_slug: str
    last_slug: str
    pairs: tuple[RoundPair, ...]


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    family: str
    factory: str
    prefix: str
    generator: str
    source_branch: str
    source_commit: str
    extraction: str
    catalogs: tuple[SourceCatalog, ...]

    def pairs(self) -> Iterator[RoundPair]:
        for source in self.catalogs:
            yield from source.pairs

    def record_ids(self) -> Iterator[str]:
        for pair in self.pairs():
            yield from pair.record_ids


def _mapping(value: Any, context: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CatalogError(f"{context} must be an object")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
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


def _docs(value: Any, context: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2:
        raise CatalogError(f"{context} must contain exactly two URLs")
    first = _text(value[0], f"{context}[0]")
    second = _text(value[1], f"{context}[1]")
    if not first.startswith("https://") or not second.startswith("https://"):
        raise CatalogError(f"{context} URLs must use https")
    return (first, second)


def _refuse_banned(text: str, context: str) -> None:
    lowered = text.lower()
    for token in _BANNED:
        if token in lowered:
            raise CatalogError(f"{context} carries banned mill-clone token {token!r}")


def _success(value: Any, context: str) -> SuccessCase:
    row = _mapping(value, context, _SUCCESS_KEYS)
    case = SuccessCase(
        slug=_text(row["slug"], f"{context}.slug", pattern=_IDENTIFIER),
        mod=_text(row["mod"], f"{context}.mod", pattern=_MODULE),
        naive=_text(row["naive"], f"{context}.naive"),
        idf=_text(row["idf"], f"{context}.idf"),
        evf=_text(row["evf"], f"{context}.evf"),
        docs=_docs(row["docs"], f"{context}.docs"),
        domain=_text(row["domain"], f"{context}.domain", pattern=_IDENTIFIER),
        stack=_text(row["stack"], f"{context}.stack"),
        test=_text(row["test"], f"{context}.test", pattern=_TEST),
        short=_text(row["short"], f"{context}.short", pattern=_MODULE),
        esp=_text(row["esp"], f"{context}.esp"),
    )
    _refuse_banned(" ".join((case.slug, case.domain, case.stack, case.esp)), context)
    return case


def _handoff(value: Any, context: str) -> HandoffCase:
    row = _mapping(value, context, _HANDOFF_KEYS)
    case = HandoffCase(
        slug=_text(row["slug"], f"{context}.slug", pattern=_IDENTIFIER),
        mod=_text(row["mod"], f"{context}.mod", pattern=_MODULE),
        naive=_text(row["naive"], f"{context}.naive"),
        idf=_text(row["idf"], f"{context}.idf"),
        evf=_text(row["evf"], f"{context}.evf"),
        docs=_docs(row["docs"], f"{context}.docs"),
        domain=_text(row["domain"], f"{context}.domain", pattern=_IDENTIFIER),
        stack=_text(row["stack"], f"{context}.stack"),
        test=_text(row["test"], f"{context}.test", pattern=_TEST),
        short=_text(row["short"], f"{context}.short", pattern=_MODULE),
        esp=_text(row["esp"], f"{context}.esp"),
        ticket=_text(row["ticket"], f"{context}.ticket"),
    )
    _refuse_banned(" ".join((case.slug, case.domain, case.stack, case.esp)), context)
    return case


def _pair(value: Any, context: str) -> RoundPair:
    row = _mapping(value, context, _PAIR_ROW_KEYS)
    success = _success(row["success"], f"{context}.success")
    handoff = _handoff(row["handoff"], f"{context}.handoff")
    if success.slug == handoff.slug:
        raise CatalogError(f"{context} repeats one slug on both outcomes")
    if success.mod == handoff.mod:
        raise CatalogError(f"{context} repeats one module on both outcomes")
    catalog_first = _integer(row["catalog_first"], f"{context}.catalog_first", minimum=1)
    index = _integer(row["index"], f"{context}.index")
    round_n = _integer(row["round"], f"{context}.round", minimum=1)
    if round_n != catalog_first + index:
        raise CatalogError(f"{context} round is not catalog_first + index")
    return RoundPair(
        source_path=_text(row["source_path"], f"{context}.source_path"),
        catalog_first=catalog_first,
        index=index,
        round=round_n,
        success=success,
        handoff=handoff,
    )


def _source(value: Any, context: str) -> SourceCatalog:
    row = _mapping(value, context, _SOURCE_KEYS)
    raw_pairs = row["pairs"]
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise CatalogError(f"{context}.pairs must be a non-empty list")
    pairs = tuple(_pair(item, f"{context}.pairs[{index}]") for index, item in enumerate(raw_pairs))
    catalog_first = _integer(row["catalog_first"], f"{context}.catalog_first", minimum=1)
    pair_count = _integer(row["pair_count"], f"{context}.pair_count", minimum=1)
    if pair_count != len(pairs):
        raise CatalogError(f"{context} pair_count does not match extracted pairs")
    if tuple(pair.index for pair in pairs) != tuple(range(pair_count)):
        raise CatalogError(f"{context} pair indexes are not contiguous from zero")
    if any(pair.catalog_first != catalog_first for pair in pairs):
        raise CatalogError(f"{context} pairs drift from catalog_first")
    if any(pair.source_path != row["source_path"] for pair in pairs):
        raise CatalogError(f"{context} pairs drift from source_path")
    first_slug = _text(row["first_slug"], f"{context}.first_slug", pattern=_IDENTIFIER)
    last_slug = _text(row["last_slug"], f"{context}.last_slug", pattern=_IDENTIFIER)
    if pairs[0].success.slug != first_slug or pairs[-1].success.slug != last_slug:
        raise CatalogError(f"{context} first/last slug pins do not match pairs")
    return SourceCatalog(
        source_path=_text(row["source_path"], f"{context}.source_path"),
        source_format=_text(row["source_format"], f"{context}.source_format"),
        source_blob_sha1=_text(row["source_blob_sha1"], f"{context}.source_blob_sha1"),
        source_sha256=_text(row["source_sha256"], f"{context}.source_sha256"),
        source_lines=_integer(row["source_lines"], f"{context}.source_lines", minimum=1),
        catalog_first=catalog_first,
        pair_count=pair_count,
        first_slug=first_slug,
        last_slug=last_slug,
        pairs=pairs,
    )


def _catalog_dir(path: Path) -> Path:
    if path.is_dir():
        return path
    return path.parent


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load LLL catalog {path}: {exc}") from exc


def _load_jsonl(path: Path) -> list[Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"cannot load LLL catalog {path}: {exc}") from exc
    if "\r" in text or not text.endswith("\n"):
        raise CatalogError(f"{path.name} must be LF-framed jsonl")
    rows: list[Any] = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line:
            raise CatalogError(f"{path.name}:{index} is empty")
        if line.startswith((" ", "\t")):
            raise CatalogError(f"{path.name}:{index} is not compact")
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise CatalogError(f"{path.name}:{index} is not JSON: {exc}") from exc
    if not rows:
        raise CatalogError(f"{path.name} must contain at least one pair")
    return rows


def _pair_rows_by_source(rows: list[Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"{PAIRS_FILENAME}:{index + 1}", _PAIR_ROW_KEYS)
        source_path = _text(row["source_path"], f"{PAIRS_FILENAME}:{index + 1}.source_path")
        grouped.setdefault(source_path, []).append(row)
    return grouped


def _sources_with_pairs(raw_catalogs: list[Any], pair_rows: list[Any]) -> list[dict[str, Any]]:
    grouped = _pair_rows_by_source(pair_rows)
    assembled: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_catalogs):
        meta = _mapping(raw, f"catalog.catalogs[{index}]", _SOURCE_META_KEYS)
        source_path = _text(meta["source_path"], f"catalog.catalogs[{index}].source_path")
        if source_path in seen:
            raise CatalogError(f"catalog repeats source {source_path}")
        seen.add(source_path)
        pairs = grouped.get(source_path)
        if not pairs:
            raise CatalogError(f"catalog.catalogs[{index}] has no pairs")
        assembled.append({**meta, "pairs": pairs})
    extra = sorted(set(grouped) - seen)
    if extra:
        raise CatalogError(f"{PAIRS_FILENAME} names unknown sources: {extra}")
    return assembled


def _refuse_identity(catalog: Catalog) -> None:
    if catalog.schema_version != SCHEMA_VERSION:
        raise CatalogError(f"unsupported schema version: {catalog.schema_version!r}")
    if catalog.family != FAMILY:
        raise CatalogError("catalog identity does not match the leftover leftover leftover family")
    if catalog.factory != FACTORY:
        raise CatalogError("catalog identity does not match the leftover leftover leftover family")
    if catalog.prefix != PREFIX:
        raise CatalogError("catalog prefix is not the reviewed ewr home")
    if catalog.generator != GENERATOR:
        raise CatalogError("catalog identity does not match the leftover leftover leftover family")
    if catalog.source_commit != SOURCE_COMMIT:
        raise CatalogError("catalog source_commit is not the preserve archive")


def _refuse_duplicates(catalog: Catalog) -> None:
    identities = [(pair.source_path, pair.index) for pair in catalog.pairs()]
    mill_slugs = [(pair.mill_id, pair.success.slug) for pair in catalog.pairs()]
    record_ids = list(catalog.record_ids())
    if len(identities) != len(set(identities)):
        raise CatalogError("catalog repeats a (source_path, index)")
    if len(mill_slugs) != len(set(mill_slugs)):
        raise CatalogError("catalog repeats a (mill_id, slug)")
    if len(record_ids) != len(set(record_ids)):
        raise CatalogError("catalog repeats a record id")


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    """Load and validate the extracted catalog without importing a legacy mill."""
    directory = _catalog_dir(path)
    row = _mapping(_load_json(directory / CATALOG_FILENAME), "catalog", _CATALOG_KEYS)
    raw_catalogs = row["catalogs"]
    if not isinstance(raw_catalogs, list) or not raw_catalogs:
        raise CatalogError("catalog.catalogs must be a non-empty list")
    sources = _sources_with_pairs(raw_catalogs, _load_jsonl(directory / PAIRS_FILENAME))
    catalog = Catalog(
        schema_version=_text(row["schema_version"], "catalog.schema_version"),
        family=_text(row["family"], "catalog.family"),
        factory=_text(row["factory"], "catalog.factory"),
        prefix=_text(row["prefix"], "catalog.prefix"),
        generator=_text(row["generator"], "catalog.generator"),
        source_branch=_text(row["source_branch"], "catalog.source_branch"),
        source_commit=_text(row["source_commit"], "catalog.source_commit"),
        extraction=_text(row["extraction"], "catalog.extraction"),
        catalogs=tuple(
            _source(item, f"catalog.catalogs[{index}]") for index, item in enumerate(sources)
        ),
    )
    _refuse_identity(catalog)
    _refuse_duplicates(catalog)
    return catalog


CATALOG = load_catalog()
