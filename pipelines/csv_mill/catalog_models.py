"""Public immutable values used by the CSV catalog facade."""

from __future__ import annotations

from collections.abc import Mapping
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from types import MappingProxyType

from ._contract import (
    CsvRefusal,
    FINDING_CATALOG_FIELD_INVALID,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_NOT_FOUND,
    PAIR_KEYS,
    PairFields,
    bind_import_twin,
)


@dataclass(frozen=True)
class Plant(PairFields):
    """One pinned ingest pair extracted from a recovered source."""

    plant_id: str
    mill_id: str
    source: str
    base_round: int
    index: int

    def pair_fields(self) -> dict[str, str]:
        return {key: getattr(self, key) for key in PAIR_KEYS}


@dataclass(frozen=True)
class Mill:
    mill_id: str
    base_round: int
    source: str
    plant_count: int


def _metadata_snapshot(value, depth=0):
    """Copy JSON containers so caller mutation cannot rewrite catalog metadata."""
    if depth > 128:
        raise CsvRefusal(FINDING_CATALOG_FIELD_INVALID, "catalog metadata exceeds 128 nesting levels")
    if isinstance(value, Mapping):
        return MappingProxyType({key: _metadata_snapshot(item, depth + 1) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_metadata_snapshot(item, depth + 1) for item in value)
    return value


@dataclass(frozen=True)
class Catalog:
    catalog_id: str
    directory: Path
    factory: str
    plants_sha256: str
    plants: tuple[Plant, ...]
    mills: tuple[Mill, ...]
    meta: Mapping[str, Any]

    _by_id: Mapping[str, Plant] = field(init=False, repr=False, compare=False)
    _by_mill: Mapping[str, tuple[Plant, ...]] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _metadata_snapshot(self.meta))
        groups: dict[str, list[Plant]] = defaultdict(list)
        for plant in self.plants:
            groups[plant.mill_id].append(plant)
        object.__setattr__(self, "_by_id", MappingProxyType({p.plant_id: p for p in self.plants}))
        object.__setattr__(
            self,
            "_by_mill",
            MappingProxyType({mill_id: tuple(plants) for mill_id, plants in groups.items()}),
        )

    def plant(self, plant_id: str) -> Plant:
        try:
            return self._by_id[plant_id]
        except KeyError:
            raise CsvRefusal(
                FINDING_PLANT_NOT_FOUND, f"no plant {plant_id!r} in the catalog"
            ) from None

    def mill_plants(self, mill_id: str) -> tuple[Plant, ...]:
        try:
            return self._by_mill[mill_id]
        except KeyError:
            raise CsvRefusal(
                FINDING_MILL_NOT_FOUND, f"no mill {mill_id!r} in the catalog"
            ) from None


bind_import_twin(__name__)
