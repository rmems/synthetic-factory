#!/usr/bin/env python3
"""Strict, read-only access to the extracted rate-limit/backoff case catalog."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

CATALOG_PATH = Path(__file__).resolve().parents[2] / "config" / "rlb-case-catalog-v1.json"
SCHEMA_VERSION = "rlb-case-catalog-v1"
FACTORY = "rate-limit-backoff-factory"
GENERATOR = "grok-4.6"
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_MODULE = re.compile(r"^[a-z0-9]+$")


class CatalogError(ValueError):
    """The committed RLB catalog does not satisfy its closed schema."""


@dataclass(frozen=True)
class SuccessCase:
    slug: str
    api: str
    header: str
    naive: str
    expected_value: int | str
    naive_value: int | str
    module: str
    docs: tuple[str, str]
    domain: str
    stack: str
    coverage: int


@dataclass(frozen=True)
class HandoffCase:
    slug: str
    api: str
    leftover_kind: str
    naive: str
    module: str
    docs: tuple[str, str]
    domain: str
    stack: str
    ticket: str
    coverage: int


@dataclass(frozen=True)
class RoundPair:
    round: int
    success: SuccessCase
    handoff: HandoffCase

    @property
    def record_ids(self) -> tuple[str, str]:
        return (
            f"rlb-r{self.round:02d}-{self.success.slug}",
            f"rlb-r{self.round:02d}-{self.handoff.slug}",
        )


@dataclass(frozen=True)
class SourceCatalog:
    source_path: str
    source_format: str
    source_blob_sha1: str
    source_sha256: str
    source_lines: int
    start_round: int
    end_round: int
    pairs: tuple[RoundPair, ...]


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    family: str
    factory: str
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


def _integer(value: Any, context: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogError(f"{context} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise CatalogError(f"{context} out of range: {value}")
    return value


def _scalar(value: Any, context: str) -> int | str:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CatalogError(f"{context} must be an integer or string")
    if isinstance(value, str) and not value:
        raise CatalogError(f"{context} must not be empty")
    return value


def _docs(value: Any, context: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2:
        raise CatalogError(f"{context} must contain exactly two URLs")
    docs = tuple(_text(item, f"{context}[{index}]") for index, item in enumerate(value))
    if any(not item.startswith("https://") for item in docs):
        raise CatalogError(f"{context} URLs must use https")
    return docs


def _success(value: Any, context: str) -> SuccessCase:
    row = _mapping(
        value,
        context,
        {
            "slug",
            "api",
            "header",
            "naive",
            "expected_value",
            "naive_value",
            "module",
            "docs",
            "domain",
            "stack",
            "coverage",
        },
    )
    return SuccessCase(
        slug=_text(row["slug"], f"{context}.slug", pattern=_IDENTIFIER),
        api=_text(row["api"], f"{context}.api"),
        header=_text(row["header"], f"{context}.header"),
        naive=_text(row["naive"], f"{context}.naive"),
        expected_value=_scalar(row["expected_value"], f"{context}.expected_value"),
        naive_value=_scalar(row["naive_value"], f"{context}.naive_value"),
        module=_text(row["module"], f"{context}.module", pattern=_MODULE),
        docs=_docs(row["docs"], f"{context}.docs"),
        domain=_text(row["domain"], f"{context}.domain", pattern=_IDENTIFIER),
        stack=_text(row["stack"], f"{context}.stack"),
        coverage=_integer(row["coverage"], f"{context}.coverage", maximum=100),
    )


def _handoff(value: Any, context: str) -> HandoffCase:
    row = _mapping(
        value,
        context,
        {
            "slug",
            "api",
            "leftover_kind",
            "naive",
            "module",
            "docs",
            "domain",
            "stack",
            "ticket",
            "coverage",
        },
    )
    return HandoffCase(
        slug=_text(row["slug"], f"{context}.slug", pattern=_IDENTIFIER),
        api=_text(row["api"], f"{context}.api"),
        leftover_kind=_text(row["leftover_kind"], f"{context}.leftover_kind"),
        naive=_text(row["naive"], f"{context}.naive"),
        module=_text(row["module"], f"{context}.module", pattern=_MODULE),
        docs=_docs(row["docs"], f"{context}.docs"),
        domain=_text(row["domain"], f"{context}.domain", pattern=_IDENTIFIER),
        stack=_text(row["stack"], f"{context}.stack"),
        ticket=_text(row["ticket"], f"{context}.ticket"),
        coverage=_integer(row["coverage"], f"{context}.coverage", maximum=100),
    )


def _pair(value: Any, context: str) -> RoundPair:
    row = _mapping(value, context, {"round", "success", "handoff"})
    success = _success(row["success"], f"{context}.success")
    handoff = _handoff(row["handoff"], f"{context}.handoff")
    if success.slug == handoff.slug:
        raise CatalogError(f"{context} repeats one slug on both outcomes")
    if success.api != handoff.api:
        raise CatalogError(f"{context} must pair cases from the same API")
    return RoundPair(
        round=_integer(row["round"], f"{context}.round", minimum=1),
        success=success,
        handoff=handoff,
    )


def _source(value: Any, context: str) -> SourceCatalog:
    row = _mapping(
        value,
        context,
        {
            "source_path",
            "source_format",
            "source_blob_sha1",
            "source_sha256",
            "source_lines",
            "start_round",
            "end_round",
            "pairs",
        },
    )
    raw_pairs = row["pairs"]
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise CatalogError(f"{context}.pairs must be a non-empty list")
    pairs = tuple(_pair(item, f"{context}.pairs[{index}]") for index, item in enumerate(raw_pairs))
    start_round = _integer(row["start_round"], f"{context}.start_round", minimum=1)
    end_round = _integer(row["end_round"], f"{context}.end_round", minimum=start_round)
    expected_rounds = tuple(range(start_round, end_round + 1))
    if tuple(pair.round for pair in pairs) != expected_rounds:
        raise CatalogError(f"{context} rounds are not contiguous across its declared range")
    return SourceCatalog(
        source_path=_text(row["source_path"], f"{context}.source_path"),
        source_format=_text(row["source_format"], f"{context}.source_format"),
        source_blob_sha1=_text(row["source_blob_sha1"], f"{context}.source_blob_sha1"),
        source_sha256=_text(row["source_sha256"], f"{context}.source_sha256"),
        source_lines=_integer(row["source_lines"], f"{context}.source_lines", minimum=1),
        start_round=start_round,
        end_round=end_round,
        pairs=pairs,
    )


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    """Load and validate the extracted catalog without importing a legacy mill."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load RLB catalog {path}: {exc}") from exc
    row = _mapping(
        payload,
        "catalog",
        {
            "schema_version",
            "family",
            "factory",
            "generator",
            "source_branch",
            "source_commit",
            "extraction",
            "catalogs",
        },
    )
    raw_catalogs = row["catalogs"]
    if not isinstance(raw_catalogs, list) or not raw_catalogs:
        raise CatalogError("catalog.catalogs must be a non-empty list")
    catalog = Catalog(
        schema_version=_text(row["schema_version"], "catalog.schema_version"),
        family=_text(row["family"], "catalog.family"),
        factory=_text(row["factory"], "catalog.factory"),
        generator=_text(row["generator"], "catalog.generator"),
        source_branch=_text(row["source_branch"], "catalog.source_branch"),
        source_commit=_text(row["source_commit"], "catalog.source_commit"),
        extraction=_text(row["extraction"], "catalog.extraction"),
        catalogs=tuple(
            _source(item, f"catalog.catalogs[{index}]")
            for index, item in enumerate(raw_catalogs)
        ),
    )
    if catalog.schema_version != SCHEMA_VERSION:
        raise CatalogError(f"unsupported schema version: {catalog.schema_version!r}")
    if catalog.family != "rlb" or catalog.factory != FACTORY or catalog.generator != GENERATOR:
        raise CatalogError("catalog identity does not match the reviewed RLB family")
    rounds = [pair.round for pair in catalog.pairs()]
    record_ids = list(catalog.record_ids())
    if len(rounds) != len(set(rounds)):
        raise CatalogError("catalog repeats a round")
    if len(record_ids) != len(set(record_ids)):
        raise CatalogError("catalog repeats a record id")
    return catalog


CATALOG = load_catalog()
