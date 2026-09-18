#!/usr/bin/env python3
"""Load the leftover6 header + compact JSONL catalogs."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog_extract import GQL_PATH, SBOX_PATH, SSL_PATH

CATALOG_DIR = Path(__file__).resolve().parents[2] / "config" / "leftover6"
CATALOG_FILENAME = "CATALOG.json"
PAIRS_FILENAME = "pairs.jsonl"
PLANTS_FILENAME = "plants.jsonl"
CATALOG_PATH = CATALOG_DIR / CATALOG_FILENAME
SCHEMA_VERSION = "leftover6-catalog-extract/v1"
FAMILY = "leftover6"
GENERATOR = "grok-4.6"
SOURCE_COMMIT = "813f93f1969c1c4421e5663492e9663739efa642"
LEGACY_REF = "origin/legacy-mill-lane"

_HEADER_KEYS = {
    "schema_version",
    "family",
    "slice",
    "generator",
    "source_branch",
    "source_commit",
    "extraction",
    "n_pair_rows_extracted",
    "n_pair_rows_committed",
    "n_plant_rows_extracted",
    "n_plant_rows_committed",
    "catalogs",
}
_MILL_KEYS = {
    "source_path",
    "kind",
    "shape",
    "preserve_commit",
    "source_blob_sha1",
    "source_sha256",
    "source_lines",
    "catalog_first",
    "n_rows",
    "first_slug",
    "last_slug",
    "factory",
    "reviewed_prefix",
}
_GQL_ROW_KEYS = {
    "source_path",
    "kind",
    "round",
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
}
_SSL_ROW_KEYS = {
    "source_path",
    "kind",
    "round",
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
}
_PLANT_ROW_KEYS = {
    "source_path",
    "kind",
    "family",
    "dump",
    "miss_dump",
    "secret",
    "pin",
    "pin_path",
    "pin_needle",
    "grep_hit",
    "distinct",
    "ext",
    "miss_ext",
    "live_bin",
    "inc",
    "over_slug",
    "miss_slug",
    "proc",
    "allow",
    "rotate",
}
FORBIDDEN_MILL_GLOBS = (
    "*leftover6*mill*.py",
    "*mill*leftover6*.py",
    "sbox-mill-plants-leftover6.py",
    "*leftover6*loop*.py",
    "_gen_*leftover6*",
)


class CatalogError(ValueError):
    """The committed leftover6 catalog does not satisfy its closed schema."""


@dataclass(frozen=True)
class MillSource:
    source_path: str
    kind: str
    shape: str
    preserve_commit: str
    source_blob_sha1: str
    source_sha256: str
    source_lines: int
    catalog_first: int
    n_rows: int
    first_slug: str
    last_slug: str
    factory: str
    reviewed_prefix: str


@dataclass(frozen=True)
class Catalog:
    schema_version: str
    family: str
    slice: str
    generator: str
    source_branch: str
    source_commit: str
    extraction: str
    catalogs: tuple[MillSource, ...]
    pairs: tuple[Mapping[str, Any], ...]
    plants: tuple[Mapping[str, Any], ...]

    @property
    def n_pair_rows(self) -> int:
        return len(self.pairs)

    @property
    def n_plant_rows(self) -> int:
        return len(self.plants)

    def mills(self) -> Iterator[MillSource]:
        return iter(self.catalogs)


@dataclass(frozen=True)
class BoundSources:
    gql: MillSource
    ssl: MillSource
    sbox: MillSource
    gql_pairs: list[Mapping[str, Any]]
    ssl_pairs: list[Mapping[str, Any]]
    plants: tuple[Mapping[str, Any], ...]


def is_vendor_filename(name: str) -> bool:
    if not name.endswith(".py"):
        return False
    lower = name.lower()
    if "leftover6" not in lower:
        return False
    return any(token in lower for token in ("mill", "plants", "loop", "_gen_"))


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
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


def _text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{context} must be a non-empty string")
    return value


def _integer(value: Any, context: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogError(f"{context} must be an integer")
    if value < minimum:
        raise CatalogError(f"{context} out of range: {value}")
    return value


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load leftover6 catalog {path}: {exc}") from exc


def _load_jsonl(path: Path) -> list[Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"cannot load leftover6 catalog {path}: {exc}") from exc
    _require_jsonl_frame(path, text)
    rows = _jsonl_rows(path, text)
    if not rows:
        raise CatalogError(f"{path.name} must contain at least one row")
    return rows


def _require_jsonl_frame(path: Path, text: str) -> None:
    if "\r" in text or not text.endswith("\n"):
        raise CatalogError(f"{path.name} must be LF-framed jsonl")


def _jsonl_rows(path: Path, text: str) -> list[Any]:
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
    return rows


def _mill(value: Any, context: str) -> MillSource:
    row = _mapping(value, context, _MILL_KEYS)
    return MillSource(
        source_path=_text(row["source_path"], f"{context}.source_path"),
        kind=_text(row["kind"], f"{context}.kind"),
        shape=_text(row["shape"], f"{context}.shape"),
        preserve_commit=_text(row["preserve_commit"], f"{context}.preserve_commit"),
        source_blob_sha1=_text(row["source_blob_sha1"], f"{context}.source_blob_sha1"),
        source_sha256=_text(row["source_sha256"], f"{context}.source_sha256"),
        source_lines=_integer(row["source_lines"], f"{context}.source_lines", minimum=1),
        catalog_first=_integer(row["catalog_first"], f"{context}.catalog_first"),
        n_rows=_integer(row["n_rows"], f"{context}.n_rows", minimum=1),
        first_slug=_text(row["first_slug"], f"{context}.first_slug"),
        last_slug=_text(row["last_slug"], f"{context}.last_slug"),
        factory=_text(row["factory"], f"{context}.factory"),
        reviewed_prefix=_text(row["reviewed_prefix"], f"{context}.reviewed_prefix"),
    )


def _pair_row(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or "kind" not in value:
        raise CatalogError(f"{context} must be a leftover6 pair object")
    kind = value["kind"]
    keys = _GQL_ROW_KEYS if kind == "gql-pairs" else _SSL_ROW_KEYS
    if kind not in {"gql-pairs", "ssl-pairs"}:
        raise CatalogError(f"{context} kind is not a leftover6 pair")
    return _typed_row(_mapping(value, context, keys), context, {"round": 0, "novel": 1})


def _typed_row(row: dict[str, Any], context: str, integers: Mapping[str, int]) -> dict[str, Any]:
    for key, item in row.items():
        if key in integers:
            _integer(item, f"{context}.{key}", minimum=integers[key])
        else:
            _text(item, f"{context}.{key}")
    return row


def _plant_row(value: Any, context: str) -> dict[str, Any]:
    return _typed_row(_mapping(value, context, _PLANT_ROW_KEYS), context, {"inc": 1})


def _catalog_dir(path: Path) -> Path:
    return path if path.is_dir() else path.parent


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    directory = _catalog_dir(path)
    row = _mapping(_load_json(directory / CATALOG_FILENAME), "catalog", _HEADER_KEYS)
    raw_mills = row["catalogs"]
    if not isinstance(raw_mills, list) or len(raw_mills) != 3:
        raise CatalogError("catalog.catalogs must list the three leftover6 mills")
    mills = tuple(_mill(item, f"catalog.catalogs[{index}]") for index, item in enumerate(raw_mills))
    expected_paths = (GQL_PATH, SSL_PATH, SBOX_PATH)
    if tuple(mill.source_path for mill in mills) != expected_paths:
        raise CatalogError("catalog mill order drifted from leftover6 sources")
    pairs = tuple(
        _pair_row(item, f"{PAIRS_FILENAME}:{index + 1}")
        for index, item in enumerate(_load_jsonl(directory / PAIRS_FILENAME))
    )
    plants = tuple(
        _plant_row(item, f"{PLANTS_FILENAME}:{index + 1}")
        for index, item in enumerate(_load_jsonl(directory / PLANTS_FILENAME))
    )
    catalog = Catalog(
        schema_version=_text(row["schema_version"], "catalog.schema_version"),
        family=_text(row["family"], "catalog.family"),
        slice=_text(row["slice"], "catalog.slice"),
        generator=_text(row["generator"], "catalog.generator"),
        source_branch=_text(row["source_branch"], "catalog.source_branch"),
        source_commit=_text(row["source_commit"], "catalog.source_commit"),
        extraction=_text(row["extraction"], "catalog.extraction"),
        catalogs=mills,
        pairs=pairs,
        plants=plants,
    )
    _refuse_identity(catalog)
    _bind_counts(catalog, row)
    return catalog


def _refuse_identity(catalog: Catalog) -> None:
    _expect(catalog.schema_version, SCHEMA_VERSION, f"unsupported schema version: {catalog.schema_version!r}")
    _expect((catalog.family, catalog.slice), (FAMILY, "full"), "catalog identity does not match leftover6")
    _expect((catalog.generator, catalog.source_commit), (GENERATOR, SOURCE_COMMIT), "catalog pin drifted from leftover6 archive 813f93f1")
    _expect(catalog.source_branch, LEGACY_REF, "catalog source_branch is not origin/legacy-mill-lane")


def _expect(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise CatalogError(message)


def _declared_total(row: Mapping[str, Any], key: str) -> int:
    return _integer(row[key], f"catalog.{key}")


def _contiguous(values: list[int], first: int, context: str, step: int = 1) -> None:
    if values != list(range(first, first + step * len(values), step)):
        raise CatalogError(f"{context} rows are not contiguous from {first}")


def _unique(values: list[str], context: str) -> None:
    if len(values) != len(set(values)):
        raise CatalogError(f"{context} contains duplicate identities")


def _bind_counts(catalog: Catalog, header: Mapping[str, Any]) -> None:
    gql, ssl, sbox = catalog.catalogs
    gql_pairs = [row for row in catalog.pairs if row["kind"] == "gql-pairs"]
    ssl_pairs = [row for row in catalog.pairs if row["kind"] == "ssl-pairs"]
    bound = BoundSources(gql, ssl, sbox, gql_pairs, ssl_pairs, catalog.plants)
    _validate_source_counts(bound)
    _validate_declared_totals(catalog, header)
    _validate_unique_and_ordered(bound)
    _validate_source_bindings(bound)


def _validate_source_counts(bound: BoundSources) -> None:
    if len(bound.gql_pairs) != bound.gql.n_rows or len(bound.ssl_pairs) != bound.ssl.n_rows:
        raise CatalogError("pair JSONL counts disagree with leftover6 mill headers")
    if len(bound.plants) != bound.sbox.n_rows:
        raise CatalogError("plant JSONL count disagrees with leftover6 mill header")


def _validate_declared_totals(catalog: Catalog, header: Mapping[str, Any]) -> None:
    expected = {
        "n_pair_rows_extracted": len(catalog.pairs),
        "n_pair_rows_committed": len(catalog.pairs),
        "n_plant_rows_extracted": len(catalog.plants),
        "n_plant_rows_committed": len(catalog.plants),
    }
    for key, actual in expected.items():
        if _declared_total(header, key) != actual:
            raise CatalogError(f"catalog.{key} disagrees with loaded rows")


def _validate_unique_and_ordered(bound: BoundSources) -> None:
    _unique([row["slug"] for row in [*bound.gql_pairs, *bound.ssl_pairs]], "pair JSONL")
    _unique([row["family"] for row in bound.plants], "plant JSONL")
    _contiguous([row["round"] for row in bound.gql_pairs], bound.gql.catalog_first, "gql")
    _contiguous([row["round"] for row in bound.ssl_pairs], bound.ssl.catalog_first, "ssl")
    _contiguous([row["inc"] for row in bound.plants], bound.sbox.catalog_first, "sbox", 4)


def _validate_source_bindings(bound: BoundSources) -> None:
    _validate_endpoints(bound)
    _validate_row_sources(bound)


def _validate_endpoints(bound: BoundSources) -> None:
    gql_pairs, ssl_pairs, plants = bound.gql_pairs, bound.ssl_pairs, bound.plants
    gql, ssl, sbox = bound.gql, bound.ssl, bound.sbox
    if gql_pairs[0]["slug"] != gql.first_slug or gql_pairs[-1]["slug"] != gql.last_slug:
        raise CatalogError("gql leftover6 slugs drifted from header")
    if ssl_pairs[0]["slug"] != ssl.first_slug or ssl_pairs[-1]["slug"] != ssl.last_slug:
        raise CatalogError("ssl leftover6 slugs drifted from header")
    if plants[0]["family"] != sbox.first_slug:
        raise CatalogError("sbox leftover6 first plant drifted from header")
    if plants[-1]["family"] != sbox.last_slug:
        raise CatalogError("sbox leftover6 last plant drifted from header")
def _validate_row_sources(bound: BoundSources) -> None:
    gql_pairs, ssl_pairs, plants = bound.gql_pairs, bound.ssl_pairs, bound.plants
    gql, ssl, sbox = bound.gql, bound.ssl, bound.sbox
    if any(row["source_path"] != gql.source_path for row in gql_pairs):
        raise CatalogError("gql leftover6 pair source_path drifted")
    if any(row["source_path"] != ssl.source_path for row in ssl_pairs):
        raise CatalogError("ssl leftover6 pair source_path drifted")
    if any(row["source_path"] != sbox.source_path for row in plants):
        raise CatalogError("sbox leftover6 plant source_path drifted")


CATALOG = load_catalog()
