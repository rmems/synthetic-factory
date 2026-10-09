#!/usr/bin/env python3
"""Seeded tool-world runs from the pinned catalog into a brand-new run directory.

Each drawn task yields its gold trajectory and one trajectory per declared
perturbation. Every record is generated in its own environment under a seed
derived from the run seed, the task, the variant, and the draw index, so one
record is reproducible without the batch. The run never writes under
``outputs/raw/`` and refuses an existing destination.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import env as environment
from . import records
from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, envelope, is_under_raw, rng, sha256_bytes
from .policies import scripted

__all__ = [
    "CANDIDATES_FILENAME",
    "NOTES_FILENAME",
    "RUN_FILENAME",
    "RunRequest",
    "generate_record",
    "run",
]

CANDIDATES_FILENAME = "candidates.jsonl"
RUN_FILENAME = "RUN.json"
NOTES_FILENAME = "NOTES.md"


@dataclass(frozen=True)
class RunRequest:
    catalog_dir: Path | None
    out_dir: Path
    seed: int
    count: int
    factory: str | None = None
    variants: str = "all"
    produced_at: str | None = None


def _check_request(request: RunRequest) -> str:
    cv.check_seed(request.seed)
    cv.refuse_first(
        (
            (
                not cv.is_genuine_int(request.count) or not 1 <= request.count <= cv.MAX_COUNT,
                cv.FINDING_COUNT_OUT_OF_DOMAIN,
                f"count must be an integer in [1, {cv.MAX_COUNT}], got {cv.shown(request.count)}",
            ),
            (
                request.variants not in ("gold", "all"),
                cv.FINDING_COUNT_OUT_OF_DOMAIN,
                f"variants must be gold or all, got {cv.shown(request.variants)}",
            ),
            (
                request.factory is not None
                and request.factory not in cv.FACTORY_BY_SURFACE.values(),
                cv.FINDING_SURFACE_UNKNOWN,
                f"unknown factory {cv.shown(request.factory)}",
            ),
            (
                request.out_dir.exists(),
                cv.FINDING_DESTINATION_EXISTS,
                f"destination already exists: {request.out_dir}",
            ),
            (
                is_under_raw(request.out_dir),
                cv.FINDING_DESTINATION_UNDER_RAW,
                f"destination names the raw tree: {request.out_dir}",
            ),
        )
    )
    produced_at = request.produced_at if request.produced_at is not None else envelope.utc_now_iso()
    cv.refuse_when(
        not isinstance(produced_at, str) or not envelope.ISO_8601_RE.match(produced_at),
        cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
        f"produced_at must be ISO-8601 UTC, got {cv.shown(produced_at)}",
    )
    return produced_at


def record_seed(run_seed: int, pack_id: str, task_id: str, variant: str, draw: int) -> int:
    return rng.seed_from_label(run_seed, f"{pack_id}:{task_id}:{variant}:{draw}")


def generate_record(
    catalog: cat.Catalog,
    pack: Any,
    task: Any,
    *,
    seed: int,
    variant: str,
    run_id: str,
    policy: str,
    draw: int,
) -> dict[str, Any]:
    """One record: a fresh environment, the scripted solver, the assembled record."""
    env = environment.Environment(pack, task, seed)
    trajectory = scripted.run(env, variant)
    return records.build_record(
        env,
        trajectory,
        catalog_sha256=catalog.catalog_sha256,
        run_id=run_id,
        policy=policy,
        draw=draw,
    )


def _variants(task: Any, variants: str) -> tuple[str, ...]:
    if variants == "gold":
        return (cv.VARIANT_GOLD,)
    return (cv.VARIANT_GOLD, *task.perturbations)


def _write_new(path: Path, text: str) -> None:
    cv.refuse_when(path.exists(), cv.FINDING_DESTINATION_EXISTS, f"already exists: {path}")
    path.write_text(text, encoding="utf-8", newline="")


def _notes(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        f"# {cv.FAMILY} NOTES",
        "",
        (
            f"Run seed {summary['seed']}, catalog {summary['catalog_id']} "
            f"({summary['catalog_sha256'][:16]}), policy {summary['policy_sha256'][:16]}."
        ),
        "",
        "Every observation below was computed by the environment and replays from (pack, seed, actions).",
        "",
        "## Records",
    ]
    for row in rows:
        lines.append(
            f"- `{row['id']}`: {row['task_id']} [{row['variant']}] steps={row['steps']} "
            f"success={row['success']} decision={row['decision']} faults_fired={row['faults_fired']}"
        )
    return "\n".join(lines) + "\n"


def run(request: RunRequest) -> dict[str, Any]:
    """Draw ``count`` tasks and write their records into ``out_dir``."""
    produced_at = _check_request(request)
    catalog = cat.load_catalog(request.catalog_dir)
    tasks = list(catalog.tasks(request.factory))
    cv.refuse_when(
        request.count > len(tasks),
        cv.FINDING_COUNT_OUT_OF_DOMAIN,
        f"count {request.count} exceeds the {len(tasks)} tasks the catalog offers for this factory",
    )
    drawn = rng.DrawStream(request.seed).sample(tasks, request.count)
    policy = scripted.policy_sha256()
    run_id = f"twd-run-{request.seed}-{catalog.catalog_sha256[:12]}"
    lines: list[str] = []
    rows: list[dict[str, Any]] = []
    draw = 0
    for pack, task in drawn:
        for variant in _variants(task, request.variants):
            draw += 1
            seed = record_seed(request.seed, pack.pack_id, task.task_id, variant, draw)
            record = generate_record(
                catalog,
                pack,
                task,
                seed=seed,
                variant=variant,
                run_id=run_id,
                policy=policy,
                draw=draw,
            )
            lines.append(dumps_exact_json(record, ensure_ascii=True))
            rows.append(
                {
                    "id": record["id"],
                    "task_id": task.task_id,
                    "factory": task.factory,
                    "variant": variant,
                    "steps": len(record["training_view"]["steps"]),
                    "success": record["training_view"]["reward"]["success"],
                    "decision": record["curation"]["decision"],
                    "faults_fired": len(record["payload"]["execution_evidence"]["faults_fired"]),
                }
            )
    payload = "\n".join(lines) + "\n"
    summary = {
        "format": cv.RUN_FORMAT,
        "family": cv.FAMILY,
        "run_id": run_id,
        "generator": cv.GENERATOR_NAME,
        "generator_version": cv.GENERATOR_VERSION,
        "policy_sha256": policy,
        "catalog_id": catalog.catalog_id,
        "catalog_sha256": catalog.catalog_sha256,
        "seed": request.seed,
        "count": request.count,
        "factory": request.factory,
        "variants": request.variants,
        "produced_at": produced_at,
        "records": len(rows),
        "accepted": sum(1 for row in rows if row["decision"] == cv.DECISION_ACCEPT),
        "measured": sum(1 for row in rows if row["decision"] == cv.DECISION_MEASURE),
        "candidates_sha256": sha256_bytes(payload.encode("utf-8")),
        "candidate_only": True,
        "self_certified_training_ready": False,
        "rows": rows,
    }
    request.out_dir.mkdir(parents=True)
    _write_new(request.out_dir / CANDIDATES_FILENAME, payload)
    _write_new(request.out_dir / RUN_FILENAME, dumps_exact_json(summary, indent=2) + "\n")
    _write_new(request.out_dir / NOTES_FILENAME, _notes(summary, rows))
    return summary


bind_import_twin(__name__)
