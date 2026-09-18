"""Typed mill catalog identity shared by extraction and loading."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

if __name__.startswith("pipelines."):
    from ..oracle_grounded.import_twins import bind_import_twin
else:
    from oracle_grounded.import_twins import bind_import_twin


@dataclass(frozen=True)
class MillCatalog:
    mill_id: str
    path: str
    blob_sha: str
    sha256: str
    kind: str
    shape: str
    catalog_first: int
    n_rounds: int
    n_rows: int
    n_hops: int
    first_slug: str
    last_slug: str
    generator: str
    factory: str
    hops: tuple[str, ...]
    loads_sibling: str
    source_lines: int
    doc_first_line: str
    pairs: tuple[Mapping[str, Any], ...] = ()


def scalar_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """Copy required scalar fields; callers normalize collections and optional text."""
    converted = {"hops", "loads_sibling", "doc_first_line", "pairs"}
    return {
        field.name: record[field.name]
        for field in fields(MillCatalog)
        if field.name not in converted
    }


def factory_hops(value: Any, where: str) -> list[str]:
    """Require the same literal factory list at extraction and loading boundaries."""
    if not isinstance(value, list):
        raise ValueError(f"{where} is not a literal list of factory slugs")
    if not all(isinstance(item, str) and item.endswith("-factory") for item in value):
        raise ValueError(f"{where} is not a literal list of factory slugs")
    return list(value)


bind_import_twin(__name__)
