#!/usr/bin/env python3
"""Pinned mill plant catalog types.

A catalog directory holds ``CATALOG.json`` (identity and the plants digest)
and ``plants.jsonl`` (one plant per line). Loading and pin verification live
in :mod:`.catalog_load` so this module stays the types.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ._contract import bind_import_twin

CATALOG_FILENAME = "CATALOG.json"
PLANTS_FILENAME = "plants.jsonl"
PLANT_KEYS = (
    "dshort",
    "docs",
    "drop_module",
    "event_field",
    "fail_id",
    "identity_field",
    "module",
    "naive_field",
    "plant_id",
    "provider",
    "short",
    "test_fail",
    "test_ok",
    "ticket",
)

__all__ = [
    "CATALOG_FILENAME",
    "Catalog",
    "PLANTS_FILENAME",
    "PLANT_KEYS",
    "Plant",
]


@dataclass(frozen=True)
class Plant:
    """One identity-bind plant: provider fields, docs, and pair stems."""

    plant_id: str
    fail_id: str
    provider: str
    identity_field: str
    event_field: str
    naive_field: str
    docs: tuple[str, str]
    ticket: str
    module: str
    drop_module: str
    test_ok: str
    test_fail: str
    short: str
    dshort: str

    def as_mapping(self) -> Mapping[str, Any]:
        return {
            "dshort": self.dshort,
            "docs": list(self.docs),
            "drop_module": self.drop_module,
            "event_field": self.event_field,
            "fail_id": self.fail_id,
            "identity_field": self.identity_field,
            "module": self.module,
            "naive_field": self.naive_field,
            "plant_id": self.plant_id,
            "provider": self.provider,
            "short": self.short,
            "test_fail": self.test_fail,
            "test_ok": self.test_ok,
            "ticket": self.ticket,
        }


@dataclass(frozen=True)
class Catalog:
    """A loaded mill catalog: identity, digest, and plants in file order."""

    catalog_id: str
    format: str
    family: str
    plant_count: int
    plants_sha256: str
    plants: tuple[Plant, ...]
    header: Mapping[str, Any]

    def plant(self, plant_id: str) -> Plant:
        for item in self.plants:
            if item.plant_id == plant_id:
                return item
        raise KeyError(plant_id)

    def ids(self) -> Sequence[str]:
        return tuple(item.plant_id for item in self.plants)


bind_import_twin(__name__)
