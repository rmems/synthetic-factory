#!/usr/bin/env python3
"""Replay leftover leftover leftover pair identities into a brand-new dest.

Writes compact catalog-replay records. Does not publish a raw round, does not
reconstruct leftover mill step templates, and does not shell out to
``round_txn``. Writers refuse an existing destination and any path that names
or aliases ``outputs/raw/``.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FACTORY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_USAGE,
    GENERATOR,
    INTENDED_USE,
    NOTES_FILENAME,
    PROJECT_TRAINING_POLICY,
    QUOTA_PER_ROUND,
    RECORD_KIND,
    RECORD_PREFIX,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse_when,
    refuse_vendor_paths,
    require_round,
)

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "notes_markdown",
    "record",
    "run",
]


@dataclass(frozen=True)
class GenerateRequest:
    catalog_dir: Path
    out_dir: Path
    plant_id: str | None = None
    mill_id: str | None = None
    all_plants: bool = False
    round: int | None = None


def _selected_plants(loaded: cat.Catalog, request: GenerateRequest) -> tuple[cat.Plant, ...]:
    chosen = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    refuse_when(sum(chosen) != 1, FINDING_USAGE, "choose exactly one of --plant, --mill, or --all")
    if request.plant_id is not None:
        return (loaded.plant(request.plant_id),)
    if request.mill_id is not None:
        return loaded.mill_plants(request.mill_id)
    return loaded.plants


def _check_destination(out_dir: Path) -> None:
    refuse_vendor_paths((out_dir,))
    refuse_when(
        is_under_raw(out_dir),
        FINDING_DESTINATION_UNDER_RAW,
        f"{out_dir} names or aliases the raw tree",
    )
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def record(plant: cat.Plant, *, round_n: int | None = None) -> dict[str, Any]:
    """One compact leftover leftover leftover identity. Not a published episode."""

    rnd = require_round(round_n if round_n is not None else plant.base_round)
    return {
        "id": f"{RECORD_PREFIX}-r{rnd}-{plant.success_slug}",
        "title": plant.title,
        "pair": plant.pair_fields(),
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GENERATOR,
            "kind": RECORD_KIND,
            "plant_id": plant.plant_id,
            "mill_id": plant.mill_id,
            "intended_use": INTENDED_USE,
            "project_training_policy": PROJECT_TRAINING_POLICY,
            "catalog_id": plant.mill_id,
            "quota": QUOTA_PER_ROUND,
        },
    }


def notes_markdown(recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    lines = [
        f"# {FACTORY} — leftover leftover leftover catalog replay",
        "",
        f"Generator: {GENERATOR} · quota: {QUOTA_PER_ROUND}",
        f"intended_use: {INTENDED_USE} · project_training_policy: {PROJECT_TRAINING_POLICY}",
        "",
        "Construction: catalog replay of AST-extracted leftover leftover leftover "
        "pair identities. This CLI never writes outputs/raw/ and never vendors mill scripts.",
        "",
        "Records:",
        *[
            f"- `{rec['id']}` mill=`{plant.mill_id}` title=`{plant.title}`"
            for rec, plant in zip(recs, plants, strict=True)
        ],
        "",
    ]
    return "\n".join(lines)


def _write_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
    _check_destination(out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        out_dir.mkdir()
        created = True
        for name, payload in files:
            path = out_dir / name
            refuse_vendor_paths((path,))
            path.write_text(payload, encoding="utf-8")
    except BaseException:
        if created and out_dir.is_dir():
            shutil.rmtree(out_dir)
        raise


def run(request: GenerateRequest) -> dict[str, Any]:
    """Write leftover leftover leftover identities into a new directory."""

    loaded = cat.load_catalog(request.catalog_dir)
    plants = _selected_plants(loaded, request)
    recs = [record(plant, round_n=request.round) for plant in plants]
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": loaded.catalog_id,
        "factory": FACTORY,
        "records": len(recs),
        "ids": [rec["id"] for rec in recs],
        "destination": str(request.out_dir),
    }
    _write_run(
        Path(request.out_dir),
        (
            (
                RECORDS_FILENAME,
                "".join(
                    dumps_exact_json(rec, ensure_ascii=False, sort_keys=True) + "\n"
                    for rec in recs
                ),
            ),
            (NOTES_FILENAME, notes_markdown(recs, plants)),
            (
                RUN_FILENAME,
                dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            ),
        ),
    )
    return summary


bind_import_twin(__name__)
