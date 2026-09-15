#!/usr/bin/env python3
"""Seeded mill pairs from a pinned catalog into a brand-new run directory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import catalog_load
from . import records
from . import validation
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, envelope, is_under_raw, rng, vocab

PAIRS_FILENAME = "pairs.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"

__all__ = ["PAIRS_FILENAME", "RUN_FILENAME", "RunRequest", "run"]


@dataclass(frozen=True)
class RunRequest:
    catalog_dir: Path
    out_dir: Path
    seed: int
    count: int
    produced_at: str | None = None
    start_round: int = 1


def _check_request(request: RunRequest) -> str:
    seed = request.seed
    cv.refuse_first((
        (not vocab.is_genuine_int(seed), cv.FINDING_SEED_NOT_AN_INTEGER,
         f"seed must be an integer, got {cv.shown(seed)}"),
        (vocab.is_genuine_int(seed) and not 0 <= seed <= cv.MAX_SEED, cv.FINDING_SEED_OUT_OF_DOMAIN,
         f"seed must lie in [0, {cv.MAX_SEED}], got {cv.shown(seed)}"),
        (not vocab.is_genuine_int(request.count) or not 1 <= request.count <= cv.MAX_COUNT,
         cv.FINDING_COUNT_OUT_OF_DOMAIN,
         f"count must be an integer in [1, {cv.MAX_COUNT}], got {cv.shown(request.count)}"),
        (not vocab.is_genuine_int(request.start_round) or request.start_round < 1,
         cv.FINDING_COUNT_OUT_OF_DOMAIN,
         f"start_round must be a positive integer, got {cv.shown(request.start_round)}"),
        (request.out_dir.exists(), cv.FINDING_DESTINATION_EXISTS,
         f"destination already exists: {request.out_dir}"),
        (is_under_raw(request.out_dir), cv.FINDING_DESTINATION_UNDER_RAW,
         f"destination names the raw tree: {request.out_dir}"),
    ))
    produced_at = request.produced_at if request.produced_at is not None else envelope.utc_now_iso()
    cv.refuse_when(
        not isinstance(produced_at, str) or not envelope.ISO_8601_RE.match(produced_at),
        cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
        f"produced_at must be ISO-8601 UTC, got {cv.shown(produced_at)}",
    )
    return produced_at


def _write_new(path: Path, text: str) -> None:
    cv.refuse_when(path.exists(), cv.FINDING_DESTINATION_EXISTS, f"already exists: {path}")
    path.write_text(text, encoding="utf-8", newline="")


def run(request: RunRequest) -> dict[str, Any]:
    """Draw ``count`` plants and write one success/fail pair each into ``out_dir``."""
    produced_at = _check_request(request)
    loaded = catalog_load.load_catalog(request.catalog_dir)
    cv.refuse_when(
        request.count > loaded.plant_count,
        cv.FINDING_COUNT_OUT_OF_DOMAIN,
        f"count {request.count} exceeds catalog plant_count {loaded.plant_count}",
    )
    drawn = rng.DrawStream(request.seed).sample(loaded.plants, request.count)
    lines: list[str] = []
    notes_parts: list[str] = []
    pair_ids: list[list[str]] = []
    for offset, plant in enumerate(drawn):
        round_n = request.start_round + offset
        success = records.success_episode(round_n, plant)
        failure = records.fail_episode(round_n, plant)
        validation.check_pair(success, failure, plant, round_n)
        lines.append(dumps_exact_json(success, ensure_ascii=True))
        lines.append(dumps_exact_json(failure, ensure_ascii=True))
        notes_parts.append(records.notes(round_n, plant))
        pair_ids.append([success["id"], failure["id"]])
    request.out_dir.mkdir(parents=True)
    _write_new(request.out_dir / PAIRS_FILENAME, "\n".join(lines) + "\n")
    _write_new(request.out_dir / NOTES_FILENAME, "\n".join(notes_parts))
    summary = {
        "format": cv.RUN_FORMAT,
        "family": cv.FAMILY,
        "factory_id": cv.FACTORY_ID,
        "generator": cv.GENERATOR_NAME,
        "generator_version": cv.GENERATOR_VERSION,
        "seed": request.seed,
        "count": request.count,
        "start_round": request.start_round,
        "produced_at": produced_at,
        "catalog_id": loaded.catalog_id,
        "plants_sha256": loaded.plants_sha256,
        "records": request.count * cv.PAIR_QUOTA,
        "pairs": request.count,
        "plant_ids": [plant.plant_id for plant in drawn],
        "ids": pair_ids,
    }
    _write_new(request.out_dir / RUN_FILENAME, dumps_exact_json(summary, indent=2) + "\n")
    return summary


bind_import_twin(__name__)
