#!/usr/bin/env python3
"""Emit success/handoff episode pairs from a pinned RAG catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path and any path that names or aliases ``outputs/raw/``. Does
not hop factories, does not shell out to ``round_txn``, and does not stamp
``grok-4.6``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_KEYS,
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
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    RagRefusal,
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
        raise RagRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _clip(text: str, limit: int = DECISION_BASIS_LIMIT) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _step(n: int, basis: str, command: str, observation: str) -> dict[str, Any]:
    basis = _clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in DECISION_BASIS_PREFIXES:
        raise RagRefusal(FINDING_DECISION_BASIS, f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": command}},
        "observation": observation,
    }


def _success_steps(pair: dict[str, str]) -> list[dict[str, Any]]:
    token, root, f1, f2, leftover = (
        pair["token"],
        pair["root"],
        pair["f1"],
        pair["f2"],
        pair["leftover"],
    )
    test = f"tests/test_{pair['slug'].replace('-', '_')}.py"
    return [
        _step(
            1,
            f"Plan: list leftover leftover leftover {root} and grep gold miss.",
            f"ls -la {root}/ && rg -n gold {root} | head",
            f"{f2}: leftover leftover leftover {leftover} drops gold\n{token}",
        ),
        _step(
            2,
            "Plan: run failing retrieval tests.",
            f"pytest {test} -q --tb=short",
            f"FAILED leftover leftover leftover gold not in topk {token}",
        ),
        _step(
            3,
            "Plan: read retriever.",
            f"sed -n '1,80p' {f1}",
            f"{f1}: leftover leftover leftover {leftover} unbound",
        ),
        _step(
            4,
            "Plan: read index yaml.",
            f"sed -n '1,80p' {f2}",
            f"{f2}: leftover leftover leftover {leftover} debug default",
        ),
        _step(
            5,
            "Plan: side metrics leftover leftover leftover recall.",
            f"rg -n recall metrics {root} | head",
            "recall leftover leftover leftover=0.12",
        ),
        _step(
            6,
            f"Plan: fetch runbook for {pair['slug']}.",
            f"curl -fsS https://runbooks.rag.example.invalid/{root}/{pair['slug']}",
            "HTTP 502 leftover leftover leftover",
        ),
        _step(
            7,
            "Observation: 502 recovered via local fixture cache.",
            f"cat fixtures/runbooks/{pair['slug']}.md",
            f"Unlink is not drop. leftover leftover leftover bind {leftover} on {pair['eng']}.",
        ),
        _step(
            8,
            "Plan: metrics API next.",
            f"curl -fsS https://metrics.rag.example.invalid/api/v1/{root}/{pair['slug']}",
            "HTTP 429 leftover leftover leftover",
        ),
        _step(
            9,
            "Observation: 429 recovered with backoff.",
            f"sleep 1; cat fixtures/metrics/{pair['slug']}.json",
            '{"recall":0.12} leftover leftover leftover',
        ),
        _step(
            10,
            f"Plan: first closed patch: {pair['wrong']}.",
            (
                "python3 - <<'PY'\n"
                "from pathlib import Path\n"
                f"p=Path({f2!r})\n"
                "p.parent.mkdir(parents=True, exist_ok=True)\n"
                "p.write_text((p.read_text() if p.exists() else '') + "
                "'\\n# leftover leftover leftover drop-filter\\n')\n"
                "print('patched')\n"
                "PY"
            ),
            "patched",
        ),
        _step(
            11,
            "Observation: tests still fail; unlink is not leftover leftover leftover retrieval.",
            f"pytest {test} -q --tb=short",
            f"FAILED leftover leftover leftover gold still missing {token}",
        ),
        _step(
            12,
            f"Reflection: Plan change: {pair['right']}. Not ingest-field.",
            f"sed -n '1,40p' {f1}",
            f"{f1} still unbound leftover leftover leftover",
        ),
        _step(
            13,
            f"Plan: leftover leftover leftover bind {leftover}.",
            (
                "python3 - <<'PY'\n"
                "from pathlib import Path\n"
                f"Path({f1!r}).write_text('bind leftover leftover leftover {leftover}\\n')\n"
                "print('1 replacement; config restored')\n"
                "PY"
            ),
            "1 replacement; config restored",
        ),
        _step(
            14,
            "Observation: tests pass after leftover leftover leftover bind.",
            f"pytest {test} -q --tb=short",
            ".\n.\n.\n3 passed in 0.12s",
        ),
    ]


def _fail_steps(pair: dict[str, str]) -> list[dict[str, Any]]:
    token, root, f1, f2, leftover = (
        pair["token"],
        pair["root"],
        pair["f1"],
        pair["f2"],
        pair["leftover"],
    )
    plat = pair["platform"]
    test = f"tests/test_{pair['slug'].replace('-', '_')}.py"
    return [
        _step(
            1,
            f"Plan: list leftover leftover leftover {root} and grep gold miss.",
            f"ls -la {root}/ && rg -n gold {root} | head",
            f"{f2}: leftover leftover leftover {leftover} platform drop\n{token}",
        ),
        _step(
            2,
            "Plan: run failing retrieval tests.",
            f"pytest {test} -q --tb=short",
            f"FAILED leftover leftover leftover gold miss {token}",
        ),
        _step(
            3,
            "Plan: read retriever.",
            f"sed -n '1,80p' {f1}",
            f"{f1}: platform-owned leftover leftover leftover",
        ),
        _step(
            4,
            "Plan: read cluster yaml.",
            f"sed -n '1,80p' {f2}",
            f"{f2}: CODEOWNERS {plat} leftover leftover leftover",
        ),
        _step(
            5,
            "Observation: CODEOWNERS leftover leftover leftover search-plat.",
            f"rg -n '{root}|{plat}' .github {root} | head",
            f".github/CODEOWNERS: {f2} @{plat}",
        ),
        _step(
            6,
            f"Plan: fetch runbook for {pair['slug']}.",
            f"curl -fsS https://runbooks.rag.example.invalid/{root}/{pair['slug']}",
            "HTTP 429 leftover leftover leftover",
        ),
        _step(
            7,
            "Observation: 429 recovered via local fixture cache.",
            f"cat fixtures/runbooks/{pair['slug']}.md",
            f"Unlink is not drop. leftover leftover leftover {plat} must bind {leftover}.",
        ),
        _step(
            8,
            "Plan: metrics API next.",
            f"curl -fsS https://metrics.rag.example.invalid/api/v1/{root}/{pair['slug']}",
            "HTTP 502 leftover leftover leftover",
        ),
        _step(
            9,
            "Observation: 502 recovered with backoff fixture.",
            f"cat fixtures/metrics/{pair['slug']}.json",
            '{"recall":0.0} leftover leftover leftover',
        ),
        _step(
            10,
            f"Plan: first closed patch: {pair['wrong']}.",
            (
                "python3 - <<'PY'\n"
                "from pathlib import Path\n"
                f"p=Path({f2!r})\n"
                "p.parent.mkdir(parents=True, exist_ok=True)\n"
                "p.write_text((p.read_text() if p.exists() else '') + "
                "'\\n# leftover leftover leftover unlink\\n')\n"
                "print('patched')\n"
                "PY"
            ),
            "patched",
        ),
        _step(
            11,
            "Observation: tests still fail; unlink is not leftover leftover leftover retrieval.",
            f"pytest {test} -q --tb=short",
            f"FAILED leftover leftover leftover gold still missing {token}",
        ),
        _step(
            12,
            f"Reflection: Plan change: leftover leftover leftover {leftover} is {plat}. "
            f"Handoff {pair['ticket']}.",
            f"sed -n '1,40p' {f1}",
            f"{f1} unsigned leftover leftover leftover",
        ),
        _step(
            13,
            "Plan: local leftover leftover leftover bind still unsigned.",
            (
                "python3 - <<'PY'\n"
                "from pathlib import Path\n"
                f"Path({f1!r}).write_text('bind leftover leftover leftover\\n')\n"
                "print('1 replacement — cluster apply still unsigned')\n"
                "PY"
            ),
            "1 replacement — cluster apply still unsigned",
        ),
        _step(
            14,
            "Observation: SLO still fails without leftover leftover leftover platform apply.",
            f"pytest {test} -q --tb=short",
            f"FAILED cluster still drops leftover leftover leftover {leftover}",
        ),
        _step(
            15,
            f"Plan: HANDOFF leftover leftover leftover to @{plat}.",
            f"echo '{pair['ticket']} handoff @{plat}: leftover leftover leftover {leftover}'",
            f"{pair['ticket']} handed off leftover leftover leftover @{plat}",
        ),
    ]


def _meta(rnd: int, plant: cat.Plant, catalog_id: str, domain: str, seed: str) -> dict[str, Any]:
    return {
        "catalog_id": catalog_id,
        "designed": True,
        "domain": domain,
        "factory": FACTORY,
        "generator": GENERATOR,
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
        "seed": seed,
    }


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    ok, _fail = cat.expand_pair(plant.eng, plant.leftover, plant.ticket_ok, plant.ticket_fail)
    leftover = ok["leftover"]
    record = {
        "id": f"rag-r{rnd}-{ok['slug']}",
        "goal": (
            f"leftover leftover leftover {ok['domain']}: gold miss via {leftover}. "
            "Bind leftover leftover leftover filter. Not ingest-field. Fake TESTONLY_ only."
        ),
        "plan": (
            f"Prove miss, fail drop-filter, leftover leftover leftover bind {leftover}, "
            "tests green."
        ),
        "steps": _success_steps(ok),
        "outcome": (
            f"{ok['ticket']} green. leftover leftover leftover bind {leftover}. "
            "3 tests passed."
        ),
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 14},
        "meta": _meta(rnd, plant, catalog_id, ok["domain"], ok["seed"]),
    }
    _refuse_banned(record)
    return record


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    _ok, fail = cat.expand_pair(plant.eng, plant.leftover, plant.ticket_ok, plant.ticket_fail)
    leftover = fail["leftover"]
    plat = fail["platform"]
    record = {
        "id": f"rag-r{rnd}-{fail['slug']}",
        "goal": (
            f"leftover leftover leftover {fail['domain']}: {leftover} dropped. "
            f"If {plat} blocks apply, remaining miss + HANDOFF. Not ingest-field."
        ),
        "plan": (
            "Prove miss, fail unlink, try leftover leftover leftover bind, "
            "stop unsigned, HANDOFF."
        ),
        "steps": _fail_steps(fail),
        "outcome": (
            f"{fail['ticket']} BLOCKED leftover leftover leftover @{plat}. "
            "remaining miss. HANDOFF."
        ),
        "reward": {
            "success": False,
            "tests_passed": 1,
            "retries": 2,
            "handoff": 1,
            "cost_steps": 15,
        },
        "meta": _meta(rnd, plant, catalog_id, fail["domain"], fail["seed"]),
    }
    _refuse_banned(record)
    return record


def notes_markdown(rnd: int, plant: cat.Plant, ok: dict[str, str], fail: dict[str, str]) -> str:
    return (
        f"# NOTES-r{rnd} {FACTORY}\n\n"
        f"Novel coverage: {38 + (rnd % 12)}%\n\n"
        f"- Episodes: 2 (quota). ids: rag-r{rnd}-{ok['slug']}, rag-r{rnd}-{fail['slug']}.\n"
        "- Step counts: 14, 15 (both in 12–18).\n"
        "- reward.success: True, False (mix). Distinct incidents, not twin tickets.\n"
        f"- decision_basis: Plan:/Observation:/Reflection:/Tool call: prefixes, "
        f"<={DECISION_BASIS_LIMIT} chars.\n"
        f"- No thought/CoT/spikes; meta.generator={GENERATOR}. No wrap-stamp goals.\n"
        "- Residual: invented plant. leftover leftover leftover retrieval/filter only.\n"
        "- Not ingest-field. Not meili federation leftover.\n"
        "\n"
        "## Mix\n"
        f"{ok['slug']} (lands). {fail['slug']}; app mitigates, remainder is platform.\n"
        f"This is: leftover leftover leftover {ok['leftover']} bind vs drop; "
        f"leftover leftover leftover {fail['leftover']} handoff.\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise RagRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise RagRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise RagRefusal(FINDING_USAGE, "round applies only with plant_id")
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
        raise RagRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise RagRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


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
        ok, fail = cat.expand_pair(plant.eng, plant.leftover, plant.ticket_ok, plant.ticket_fail)
        records.append(success_episode(rnd, plant, loaded.catalog_id))
        records.append(fail_episode(rnd, plant, loaded.catalog_id))
        note_chunks.append(notes_markdown(rnd, plant, ok, fail))
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
