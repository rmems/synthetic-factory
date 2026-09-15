#!/usr/bin/env python3
"""The dlk plant catalog: load the preserved lock-product plants from ``config/dlk/``.

A catalog directory (``config/dlk/``) holds ``CATALOG.json`` (identity, the
preserved rounds and a sha256 pin per plant file) and one ``plants-rNNNN.json``
per preserved round (a JSON array of the lock-product plants the legacy
``dlk_rNNNN_leftover3_mill.py`` carried). Loading re-derives each plant file's
sha256 over its exact on-disk bytes and refuses if it no longer matches the
pin, so a hand edit of a plant file is caught before any record is built.

This module is data-only: it never executes the generator and never writes a
raw round. The pure episode builders over a loaded catalog live in
:mod:`.generate`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import _contract as c
from ._contract import bind_import_twin

CATALOG_FILENAME = "CATALOG.json"
PLANT_FILENAME_TEMPLATE = "plants-r{round}.json"

# The exact string keys every preserved plant carries. The legacy scripts
# built these inline; the cleaned catalog validates them on load so a
# malformed plant file is refused at the boundary.
PLANT_KEYS = (
    "slug", "seed", "why", "bad", "fix", "dump", "src", "test", "probe", "cli",
    "leftover_fn", "ok_pat", "fail_slug", "fail_why",
)

__all__ = [
    "CATALOG_FILENAME", "PLANT_FILENAME_TEMPLATE", "PLANT_KEYS", "Catalog", "Plant",
    "catalog_index", "default_config_dir", "load_all", "load_catalog", "plant_slugs",
]


@dataclass(frozen=True)
class Plant:
    """One preserved lock-product plant, exactly as the legacy mill carried it."""

    slug: str
    seed: str
    why: str
    bad: str
    fix: str
    dump: str
    src: str
    test: str
    probe: str
    cli: str
    leftover_fn: str
    ok_pat: str
    fail_slug: str
    fail_why: str

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Plant:
        missing = [k for k in PLANT_KEYS if not isinstance(row.get(k), str) or not row[k]]
        if missing:
            raise ValueError(f"plant {row.get('slug')!r} missing/non-string keys: {missing}")
        return cls(**{k: row[k] for k in PLANT_KEYS})


@dataclass(frozen=True)
class Catalog:
    """One preserved round's plants plus the sha256 of the bytes they loaded from."""

    round: int
    factory: str
    generator: str
    plants: tuple[Plant, ...]
    plants_sha256: str
    source_file: Path

    @property
    def slugs(self) -> tuple[str, ...]:
        return tuple(p.slug for p in self.plants)

    def plant(self, slug: str) -> Plant:
        for plant in self.plants:
            if plant.slug == slug:
                return plant
        raise KeyError(f"no plant {slug!r} in round r{self.round:04d}")


def default_config_dir() -> Path:
    """The repo-root ``config/dlk`` directory this package's catalog lives under."""
    return Path(__file__).resolve().parents[2] / "config" / "dlk"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def catalog_index(config_dir: Path | str | None = None) -> dict[str, Any]:
    """The decoded ``CATALOG.json`` for this lane; refuses a missing or malformed pin."""
    directory = Path(config_dir) if config_dir is not None else default_config_dir()
    index = _read_json(directory / CATALOG_FILENAME)
    if not isinstance(index, Mapping):
        raise TypeError(f"{directory / CATALOG_FILENAME} is not a JSON object")
    if index.get("prefix") != c.PREFIX or index.get("factory") != c.FACTORY:
        raise ValueError(
            f"{directory / CATALOG_FILENAME} pins prefix={index.get('prefix')!r} "
            f"factory={index.get('factory')!r}; expected {c.PREFIX!r}/{c.FACTORY!r}"
        )
    return dict(index)


def _verify_pin(directory: Path, round: int, plant_files: Mapping[str, Any]) -> Mapping[str, Any]:
    entry = None
    for candidate in plant_files.values():
        if isinstance(candidate, Mapping) and candidate.get("round") == round:
            entry = candidate
            break
    if entry is None:
        raise KeyError(f"round {round} is not pinned in {CATALOG_FILENAME}")
    fname = entry["file"]
    path = directory / fname
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != entry["sha256"]:
        raise ValueError(
            f"{fname} sha256 drifted: pinned {entry['sha256'][:12]}..., got {digest[:12]}..."
        )
    return entry


def load_catalog(round: int, config_dir: Path | str | None = None) -> Catalog:
    """Load one preserved round's plants, refusing a sha256 drift or a duplicate slug."""
    directory = Path(config_dir) if config_dir is not None else default_config_dir()
    index = catalog_index(directory)
    entry = _verify_pin(directory, round, index["plant_files"])
    payload = _read_json(directory / entry["file"])
    if not isinstance(payload, Mapping):
        raise TypeError(f"{entry['file']} is not a JSON object")
    rows = payload.get("plants")
    if not isinstance(rows, Sequence) or any(not isinstance(r, Mapping) for r in rows):
        raise ValueError(f"{entry['file']} .plants is not a list of objects")
    plants = tuple(Plant.from_row(row) for row in rows)
    slugs = [p.slug for p in plants]
    if len(slugs) != len(set(slugs)):
        dupes = sorted({s for s in slugs if slugs.count(s) > 1})
        raise ValueError(f"round r{round:04d} has duplicate plant slugs: {dupes}")
    if payload.get("factory") != c.FACTORY:
        raise ValueError(f"{entry['file']} factory {payload.get('factory')!r} != {c.FACTORY!r}")
    if payload.get("generator") != c.GEN:
        raise ValueError(f"{entry['file']} generator {payload.get('generator')!r} != {c.GEN!r}")
    return Catalog(
        round=round,
        factory=payload["factory"],
        generator=payload["generator"],
        plants=plants,
        plants_sha256=entry["sha256"],
        source_file=directory / entry["file"],
    )


def load_all(config_dir: Path | str | None = None) -> tuple[Catalog, ...]:
    """Every preserved round's catalog, in the pinned order; refuses cross-round slug overlap."""
    directory = Path(config_dir) if config_dir is not None else default_config_dir()
    index = catalog_index(directory)
    rounds = index["preserved_rounds"]
    catalogs = tuple(load_catalog(rnd, directory) for rnd in rounds)
    all_slugs = [slug for cat in catalogs for slug in cat.slugs]
    if len(all_slugs) != len(set(all_slugs)):
        raise ValueError("plant slugs overlap across preserved dlk rounds")
    return catalogs


def plant_slugs(catalog: Catalog) -> tuple[str, ...]:
    """The plant slugs of one catalog, in load order."""
    return catalog.slugs


bind_import_twin(__name__)
