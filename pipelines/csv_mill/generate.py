#!/usr/bin/env python3
"""Emit success/handoff episode pairs from a pinned CSV catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path and any path that names or aliases ``outputs/raw/``. Does
not hop factories, does not shell out to ``round_txn``, and does not stamp
``grok-4.6``. Episode text follows the leftover r114 mill templates.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from .generate_io import write_run_files
from .steps import make_steps
from .steps_templates import EPISODES
from ._contract import (
    BANNED_KEYS,
    CsvRefusal,
    DECISION_BASIS_LIMIT,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORD_PREFIX,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    is_integer,
)

__all__ = [
    "GenerateRequest",
    "NOTES_FILENAME",
    "RECORDS_FILENAME",
    "RUN_FILENAME",
    "fail_episode",
    "notes_markdown",
    "run",
    "success_episode",
]


@dataclass(frozen=True)
class GenerateRequest:
    catalog_dir: Path
    out_dir: Path
    plant_id: str | None = None
    mill_id: str | None = None
    all_plants: bool = False
    round: int | None = None


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [*value, *(key for item in value.values() for key in _walk_keys(item))]
    if isinstance(value, list):
        return [key for item in value for key in _walk_keys(item)]
    return []


def _refuse_banned(record: dict[str, Any]) -> None:
    hits = sorted(BANNED_KEYS.intersection(_walk_keys(record)))
    if hits:
        raise CsvRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _meta(
    rnd: int,
    plant: cat.Plant,
    catalog_id: str,
    success: bool,
) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "domain": plant.domain if success else plant.fail,
        "factory": FACTORY,
        "generator": GENERATOR,
        "kind": "episode",
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
        "seed": plant.slug if success else plant.fail,
        "stack": plant.stack if success else plant.drop_stack,
    }


def _episode_id(rnd: int, slug: str) -> str:
    return f"{RECORD_PREFIX}-r{rnd:02d}-{slug}"


def _episode(rnd: int, plant: cat.Plant, catalog_id: str, success: bool) -> dict[str, Any]:
    pair = plant.pair_fields()
    template = EPISODES[success]
    record = {
        "id": _episode_id(rnd, plant.slug if success else plant.fail),
        **{key: template[key].format_map(pair) for key in ("goal", "plan", "outcome")},
        "steps": make_steps(pair, success=success),
        "reward": dict(template["reward"]),
        "meta": _meta(rnd, plant, catalog_id, success=success),
    }
    _refuse_banned(record)
    return record


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    return _episode(rnd, plant, catalog_id, True)


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    return _episode(rnd, plant, catalog_id, False)


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    p = plant.pair_fields()
    ok = _episode_id(rnd, p["slug"])
    bad = _episode_id(rnd, p["fail"])
    return (
        f"# {FACTORY} — NOTES r{rnd:02d}\n\n"
        f"Novel coverage: leftover leftover leftover {p['keep']} vs {p['naive']}. "
        "Not r106–r113 clones. Not beehiiv. Not tantivy/search-index.\n\n"
        "## Episodes\n"
        f"- `{ok}`: 16 steps, success=True, domain={p['domain']}, seed={p['slug']}\n"
        "  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: Bind leftover leftover leftover {p['keep']}. "
        f"{p['naive']} parse is not the index.\n"
        "  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad}`: 17 steps, success=False, domain={p['fail']}, seed={p['fail']}\n"
        "  - 429 at step 6 recovered 7; 502 at step 8 recovered 9\n"
        f"  - plan change at step 12: Dropped leftover leftover leftover {p['keep']} "
        f"is ingest-plat. Handoff {p['ticket']}.\n"
        "  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        "## decision_basis audit\n"
        "Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤{DECISION_BASIS_LIMIT}, no thought/chain_of_thought/scratch/inner_monologue "
        f"keys, no spike_events, no sim_or_real real, no Spikenaut. Generator {GENERATOR}. "
        "No [variant …] goal stamp.\n\n"
        "## Mix\n"
        f"Success: ['{ok}']. Realistic failure/handoff: ['{bad}'].\n\n"
        "## Realism / weak recovery paths\n"
        "Noise recoveries are backoff+retry or local fixture cache. First patches are "
        "domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        "## Step counts\n"
        f"- {ok}: 16 (required 14–18)\n"
        f"- {bad}: 17 (required 14–18)\n\n"
        "## Weaknesses / next\n"
        f"{p['naive']} is not leftover leftover leftover PK. Cannot drop leftover leftover "
        f"leftover {p['keep']} onto {p['naive']}-as-key.\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not is_integer(rnd) or rnd < 1:
        raise CsvRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise CsvRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round + plant.index), plant)]
    if request.round is not None:
        raise CsvRefusal(FINDING_USAGE, "round applies only with plant_id")
    plants = loaded.plants if request.mill_id is None else loaded.mill_plants(request.mill_id)
    return [(plant.base_round + plant.index, plant) for plant in plants]


def _check_destination(out_dir: Path) -> None:
    if is_under_raw(out_dir):
        raise CsvRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists() or out_dir.is_symlink():
        raise CsvRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Generate episode pairs into a new destination. Returns the RUN summary."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    out_dir = Path(request.out_dir)
    records: list[dict[str, Any]] = []
    note_chunks: list[str] = []
    for rnd, plant in jobs:
        records.append(success_episode(rnd, plant, loaded.catalog_id))
        records.append(fail_episode(rnd, plant, loaded.catalog_id))
        note_chunks.append(notes_markdown(rnd, plant))
    lines = [dumps_exact_json(record, ensure_ascii=False, sort_keys=True) for record in records]
    records_text = "\n".join(lines) + "\n"
    notes_text = "\n".join(note_chunks)
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": loaded.catalog_id,
        "plants_sha256": loaded.plants_sha256,
        "factory": FACTORY,
        "generator": GENERATOR,
        "pairs": len(jobs),
        "quota_per_round": QUOTA_PER_ROUND,
        "records": len(records),
        "records_sha256": hashlib.sha256(records_text.encode("utf-8")).hexdigest(),
        "destination": str(out_dir),
    }
    published = write_run_files(out_dir, {
        RECORDS_FILENAME: records_text,
        NOTES_FILENAME: notes_text,
        RUN_FILENAME: dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    })
    summary["published_destination"] = str(published)
    return summary


bind_import_twin(__name__)
