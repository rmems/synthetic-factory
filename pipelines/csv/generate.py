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
from ._contract import (
    BANNED_KEYS,
    CsvRefusal,
    DECISION_BASIS_LIMIT,
    DECISION_BASIS_PREFIXES,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DECISION_BASIS,
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


def db(kind: str, text: str) -> str:
    """Faithful leftover-mill ``db()`` clip. Never exec the mill."""

    return f"{kind}: {text}"[:DECISION_BASIS_LIMIT]


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys = list(value)
        for item in value.values():
            keys.extend(_walk_keys(item))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for item in value:
            keys.extend(_walk_keys(item))
        return keys
    return []


def _refuse_banned(record: dict[str, Any]) -> None:
    hits = sorted(BANNED_KEYS.intersection(_walk_keys(record)))
    if hits:
        raise CsvRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _step(
    n: int,
    kind: str,
    text: str,
    name: str,
    args: dict[str, Any],
    observation: str,
    reflection: str,
) -> dict[str, Any]:
    basis = db(kind, text)
    prefix = basis.split(":", 1)[0]
    if prefix not in DECISION_BASIS_PREFIXES:
        raise CsvRefusal(FINDING_DECISION_BASIS, f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
        "reflection": reflection,
    }


def _success_steps(p: dict[str, str]) -> list[dict[str, Any]]:
    src = f"src/{p['mod']}.py"
    cfg = f"{p['mod']}/cfg.yml"
    test = f"tests/test_{p['mod']}.py"
    keep, naive = p["keep"], p["naive"]
    return [
        _step(
            1,
            "Plan",
            f"list src {p['short']} and tests before touching conversion or config.",
            "bash",
            {"command": f"ls -la src {p['short']} tests | head -40"},
            f"{src} {cfg}\n{test}",
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            "Observation",
            f"listing named the test files. Run `{test} -q --tb=short` to capture the failure.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            (
                f"{test}::{p['test_ok']} FAILED\n"
                f"E   AssertionError: leftover {naive} parse missed leftover leftover leftover"
                f" {keep}"
            ),
            f"Failure is at {test}::{p['test_ok']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            "Observation",
            f"{test}::{p['test_ok']} is red. Read {test} around the assertion.",
            "read",
            {"path": test},
            f"def {p['test_ok']}():\n    assert parse(b'x')['kind'] == {p['mod']!r}\n",
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation",
            "test file imported the production helper. Grep those symbols.",
            "bash",
            {"command": f"rg -n '{keep}|{naive}' src {p['short']} tests"},
            f"{src}:2: return {{{naive!r}: True}}",
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            "Observation",
            f"grep listed {src}. Read it before any patch.",
            "read",
            {"path": src},
            f"def parse(blob):\n    return {{{naive!r}: True}}\n",
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation",
            "local files are in. Need the changelog/registry before editing.",
            "fetch",
            {"url": p["doc"]},
            f"GET {p['doc']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            7,
            "Observation",
            "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            "fetch",
            {"url": p["doc"]},
            (
                f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n"
                f"leftover leftover leftover {keep} is required; naive {naive} is not enough."
            ),
            "Degraded path used the local fixture. Continue with that content.",
        ),
        _step(
            8,
            "Observation",
            "local files are in. Need the second remote document before editing.",
            "fetch",
            {"url": p["doc2"]},
            (
                f"GET {p['doc2']}\nHTTP/1.1 429 Too Many Requests\n"
                "Retry-After: 5\nX-RateLimit-Remaining: 0"
            ),
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            9,
            "Observation",
            "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
            "fetch",
            {"url": p["doc2"]},
            (
                f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n"
                f"Keep leftover leftover leftover {keep}. Not r106-r113 clones. Not search-index."
            ),
            "Retry succeeded. Resume the local debug plan with that document in hand.",
        ),
        _step(
            10,
            "Observation",
            f"docs and source are in. Apply the first patch to {src}.",
            "edit",
            {
                "path": src,
                "old": f"    return {{{naive!r}: True}}",
                "new": f"    return {{{naive!r}: True, {p['first_wrong']!r}: True}}",
            },
            f"patched first apply still wrong for leftover leftover leftover {keep}",
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        _step(
            11,
            "Observation",
            f"edit wrote {src}. Re-run the same failing node.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            (
                f"{test}::{p['test_ok']} FAILED\n"
                f"E   AssertionError: first patch is not leftover leftover leftover {keep}"
            ),
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        _step(
            12,
            "Observation",
            f"post-edit test still failed ({test}::{p['test_ok']}). Re-read {src}.",
            "read",
            {"path": src},
            f"leftover leftover leftover {keep} is the real index; first patch is {naive}-only",
            f"Plan change: Bind leftover leftover leftover {keep}. {naive} parse is not the index.",
        ),
        _step(
            13,
            "Reflection",
            f"Bind leftover leftover leftover {keep}. {naive} parse is not the index.",
            "edit",
            {
                "path": src,
                "old": f"    return {{{naive!r}: True, {p['first_wrong']!r}: True}}",
                "new": f"    return {{'kind': {p['mod']!r}, {keep!r}: True}}",
            },
            f"patched leftover leftover leftover {keep}",
            "Corrective patch applied. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation",
            "fix edit returned clean. Re-run the original failing test node.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            "1 passed in 0.16s",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            "Observation",
            f"focused run finished. Run broader check `pytest {test} -q`.",
            "bash",
            {"command": f"pytest {test} -q"},
            "3 passed in 0.28s",
            "Broader check captured. Stop; residual risk belongs in the outcome text.",
        ),
        _step(
            16,
            "Observation",
            "broader check is on disk. Show the diff of patched files for the handoff note.",
            "bash",
            {"command": "git diff --stat | head -n 40"},
            f"diffstat for {p['slug']}: {src} | 9 ++++++---. No other modified paths.",
            "Diff is the review artifact. No further edits.",
        ),
    ]


def _fail_steps(p: dict[str, str]) -> list[dict[str, Any]]:
    src = f"src/{p['drop']}.py"
    cfg = f"{p['drop']}/cfg.yml"
    test = f"tests/test_{p['drop']}.py"
    keep, naive, ticket = p["keep"], p["naive"], p["ticket"]
    return [
        _step(
            1,
            "Plan",
            f"list src {p['dshort']} and tests before touching conversion or config.",
            "bash",
            {"command": f"ls -la src {p['dshort']} tests | head -40"},
            f"{src} {cfg}\n{test}",
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            "Observation",
            f"listing named the test files. Run `{test} -q --tb=short` to capture the failure.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            (
                f"{test}::{p['test_fail']} FAILED\n"
                f"E   AssertionError: dropped leftover leftover leftover {keep}; "
                f"{naive} still owned"
            ),
            f"Failure is at {test}::{p['test_fail']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            "Observation",
            f"{test}::{p['test_fail']} is red. Read {test} around the assertion.",
            "read",
            {"path": test},
            f"def {p['test_fail']}():\n    assert 'handoff' in parse(b'x')\n",
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation",
            "test file imported the production helper. Grep those symbols.",
            "bash",
            {"command": f"rg -n '{keep}|{naive}|drop' src {p['dshort']} tests"},
            f"{src}:2: return {{{naive!r}: True}}",
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            "Observation",
            f"grep listed {src}. Read it before any patch.",
            "read",
            {"path": src},
            f"def parse(blob):\n    return {{{naive!r}: True}}\n",
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
        _step(
            6,
            "Observation",
            "local files are in. Need the changelog/registry before editing.",
            "fetch",
            {"url": p["doc"]},
            (
                f"GET {p['doc']}\nHTTP/1.1 429 Too Many Requests\n"
                "Retry-After: 6\nX-RateLimit-Remaining: 0"
            ),
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
        ),
        _step(
            7,
            "Observation",
            "the prior call returned rate-limit status with Retry-After. Sleep then retry.",
            "fetch",
            {"url": p["doc"]},
            (
                f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n"
                f"{p['drop_stack']} is platform; hand off {ticket}."
            ),
            "Retry succeeded. Continue with that document.",
        ),
        _step(
            8,
            "Observation",
            "local files are in. Need the second remote document before editing.",
            "fetch",
            {"url": p["doc2"]},
            f"GET {p['doc2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
            "Call failed with upstream gateway failure. Recover with backoff.",
        ),
        _step(
            9,
            "Observation",
            "the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
            "fetch",
            {"url": p["doc2"]},
            (
                f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n"
                f"Handoff {ticket}. Not leftover leftover leftover unlink clones."
            ),
            "Degraded path used the local fixture. Resume the local debug plan.",
        ),
        _step(
            10,
            "Observation",
            f"docs and source are in. Apply the first patch to {src}.",
            "edit",
            {
                "path": src,
                "old": f"    return {{{naive!r}: True}}",
                "new": f"    return {{{naive!r}: True, 'flatten': True}}",
            },
            f"patched first apply still {p['drop_stack']}-owned",
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        _step(
            11,
            "Observation",
            f"edit wrote {src}. Re-run the same failing node.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            (
                f"{test}::{p['test_fail']} FAILED\n"
                f"E   AssertionError: cannot mint leftover leftover leftover {keep} here"
            ),
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        _step(
            12,
            "Observation",
            f"post-edit test still failed ({test}::{p['test_fail']}). Re-read {src}.",
            "read",
            {"path": src},
            f"Dropped leftover leftover leftover {keep} is ingest-plat; cannot bind {naive}-as-key",
            (
                f"Plan change: Dropped leftover leftover leftover {keep} is ingest-plat. "
                f"Handoff {ticket}."
            ),
        ),
        _step(
            13,
            "Reflection",
            f"Dropped leftover leftover leftover {keep} is ingest-plat. Handoff {ticket}.",
            "edit",
            {
                "path": f"{p['drop']}/handoff.md",
                "old": "",
                "new": f"# {ticket} leftover leftover leftover {keep} grain owned by ingest-plat",
            },
            f"ticket filed. still drop-{keep}",
            "Handoff ticket written. Run the original failing node again.",
        ),
        _step(
            14,
            "Observation",
            "handoff edit returned clean. Re-run the original failing test node.",
            "pytest",
            {"args": f"{test} -q --tb=short"},
            f"{test}::{p['test_fail']} FAILED  # handoff: {ticket}\n1 failed",
            "Result recorded. Run one broader check before declaring the outcome.",
        ),
        _step(
            15,
            "Observation",
            f"focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.",
            "bash",
            {"command": f"pytest {test} -q; echo {ticket}"},
            f"1 failed, 2 passed\n{ticket}",
            "Broader check captured. Residual risk belongs in the outcome text.",
        ),
        _step(
            16,
            "Observation",
            "broader check is on disk. Show the diff of patched files for the handoff note.",
            "bash",
            {"command": "git diff --stat | head -n 40"},
            f"diffstat for {p['fail']}: {src} | 8 +++++---. {p['drop']}/handoff.md added.",
            "Diff is the review artifact. Lint next.",
        ),
        _step(
            17,
            "Observation",
            "diffstat listed the patched files. Run a linter on those paths only.",
            "bash",
            {"command": "ruff check tests || true; echo lint-end"},
            "All checks passed!\nlint-end",
            "Lint clean. Episode complete.",
        ),
    ]


def _meta(
    rnd: int,
    plant: cat.Plant,
    catalog_id: str,
    domain: str,
    seed: str,
    stack: str,
) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "domain": domain,
        "factory": FACTORY,
        "generator": GENERATOR,
        "kind": "episode",
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
        "seed": seed,
        "stack": stack,
    }


def _episode_id(rnd: int, slug: str) -> str:
    return f"{RECORD_PREFIX}-r{rnd:02d}-{slug}"


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    p = plant.pair_fields()
    keep, naive = p["keep"], p["naive"]
    record = {
        "id": _episode_id(rnd, p["slug"]),
        "goal": f"Honor leftover leftover leftover {keep}; {naive} is not the index.",
        "plan": f"Read {p['short']}, try first patch, then leftover leftover leftover {keep}.",
        "steps": _success_steps(p),
        "outcome": f"leftover leftover leftover {keep} bound. {naive} unused (success).",
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": 16,
            "plan_changes": 1,
        },
        "meta": _meta(rnd, plant, catalog_id, p["domain"], p["slug"], p["stack"]),
    }
    _refuse_banned(record)
    return record


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    p = plant.pair_fields()
    keep, naive, ticket = p["keep"], p["naive"], p["ticket"]
    record = {
        "id": _episode_id(rnd, p["fail"]),
        "goal": f"Do not drop leftover leftover leftover {keep} when binding {naive}.",
        "plan": (
            f"Read drop-{keep}, try {naive}, then hand off dropped leftover leftover leftover"
            f" {keep} grain."
        ),
        "steps": _fail_steps(p),
        "outcome": (
            f"Still drop-{keep}; leftover leftover leftover {keep} grain is {p['drop_stack']} "
            f"— handoff {ticket}."
        ),
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": 17,
            "plan_changes": 1,
        },
        "meta": _meta(
            rnd, plant, catalog_id, p["fail"] + "-handoff", p["fail"], p["drop_stack"]
        ),
    }
    _refuse_banned(record)
    return record


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
        f"- `{bad}`: 17 steps, success=False, domain=drop {p['keep']}, seed={p['fail']}\n"
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
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise CsvRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise CsvRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise CsvRefusal(FINDING_USAGE, "round applies only with plant_id")
    if request.mill_id is not None:
        mills = [mill for mill in loaded.mills if mill.mill_id == request.mill_id]
        loaded.mill_plants(request.mill_id)
    else:
        mills = list(loaded.mills)
    jobs: list[tuple[int, cat.Plant]] = []
    for mill in mills:
        for index, plant in enumerate(loaded.mill_plants(mill.mill_id)):
            jobs.append((mill.base_round + index, plant))
    return jobs


def _check_destination(out_dir: Path) -> None:
    if is_under_raw(out_dir):
        raise CsvRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise CsvRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


def run(request: GenerateRequest) -> dict[str, Any]:
    """Generate episode pairs into a new destination. Returns the RUN summary."""

    _check_destination(Path(request.out_dir))
    loaded = cat.load_catalog(request.catalog_dir)
    jobs = _jobs(loaded, request)
    out_dir = Path(request.out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    note_chunks: list[str] = []
    for rnd, plant in jobs:
        records.append(success_episode(rnd, plant, loaded.catalog_id))
        records.append(fail_episode(rnd, plant, loaded.catalog_id))
        note_chunks.append(notes_markdown(rnd, plant))
    lines = [dumps_exact_json(record, ensure_ascii=False, sort_keys=True) for record in records]
    records_text = "\n".join(lines) + "\n"
    records_path = out_dir / RECORDS_FILENAME
    records_path.write_text(records_text, encoding="utf-8")
    notes_text = "\n".join(note_chunks)
    (out_dir / NOTES_FILENAME).write_text(notes_text, encoding="utf-8")
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
    (out_dir / RUN_FILENAME).write_text(
        dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


bind_import_twin(__name__)
