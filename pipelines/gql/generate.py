#!/usr/bin/env python3
"""Emit success/handoff episode pairs from a pinned GQL catalog.

Writes a brand-new destination (records.jsonl, RUN.json, NOTES.md). Refuses
an existing path and any path that names or aliases ``outputs/raw/``. Does
not hop factories, does not shell out to ``round_txn``, does not wrap a
catalog with modulo, and does not stamp ``grok-4.6``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_KEYS,
    FACTORY,
    FINDING_BANNED_KEY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_FIELD_INVALID,
    FINDING_ROUND_INVALID,
    FINDING_USAGE,
    GENERATOR,
    GqlRefusal,
    NOTES_FILENAME,
    QUOTA_PER_ROUND,
    RECORDS_FILENAME,
    RUN_FILENAME,
    RUN_FORMAT,
    SHAPE_PAIR,
    SHAPE_SURFACE,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
)

BASIS_PREFIXES = frozenset({"Plan", "Observation", "Reflection", "Tool call"})
BASIS_LIMIT = 240

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
        raise GqlRefusal(FINDING_BANNED_KEY, f"record {record.get('id')!r} carries {hits[0]}")


def _clip(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= BASIS_LIMIT:
        return compact
    return compact[: BASIS_LIMIT - 1].rstrip() + "…"


def _step(
    n: int,
    basis: str,
    name: str,
    args: dict[str, str],
    observation: str,
    reflection: str | None = None,
) -> dict[str, Any]:
    clipped = _clip(basis)
    prefix = clipped.split(":", 1)[0]
    if prefix not in BASIS_PREFIXES:
        raise GqlRefusal(FINDING_USAGE, f"bad decision_basis prefix: {basis!r}")
    step = {
        "n": n,
        "decision_basis": clipped,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def _meta(rnd: int, plant: cat.Plant, catalog_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = {
        "catalog_id": catalog_id,
        "designed": True,
        "factory": FACTORY,
        "generator": GENERATOR,
        "mill_id": plant.mill_id,
        "plant_id": plant.plant_id,
        "round": rnd,
    }
    if extra:
        meta.update(extra)
    return meta


def _pair_success(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    field = plant.payload["field"]
    window = plant.payload["window"]
    s = plant.payload["ok"]
    steps = [
        _step(
            1,
            f"Plan: read {plant.plant} entry and gate before disable {s['disable'].lower()}.",
            "bash",
            {"command": f"rg -n '{s['disable']}|{field}' src tests | head -n 26"},
            f"{s['cfg']}: {s['disable']} leftover\nsrc/{plant.plant.split('-')[1]}.graphql: {field}: Float\n{s['test']}: def test_one\n",
        ),
        _step(2, f"Observation: gate test (step 1). Read {s['cfg']}.", "read", {"path": s["cfg"]}, s["src_obs"]),
        _step(3, f"Observation: source confirms the bug (step 2). Read {s['test']}.", "read", {"path": s["test"]}, s["test_obs"]),
        _step(4, "Observation: gate expectations (step 3). Run.", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 10"}, s["fail_obs"]),
        _step(5, "Observation: failing assertion (step 4).", "bash", {"command": f"rg -n '{s['disable']}' {s['cfg']}"}, s["rg_obs"]),
        _step(6, f"Plan: first apply — disable {s['disable'].lower()}.", "edit", {"path": s["src"], "old": s["wrong_edit_old"], "new": s["wrong_edit_new"]}, f"patched disable {s['disable']}"),
        _step(7, "Observation: first apply (step 6).", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"}, f"FAILED test_slo - {s['slo']}\n1 failed, 1 passed\n", s["fix"]),
        _step(8, f"Reflection: plan change — {s['fix']}", "write", {"path": s["src"], "contents": s["fix_contents"]}, s["fix"]),
        _step(9, "Observation: rewrite (step 8). Re-run.", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"}, "2 passed in 0.11s"),
        _step(10, "Observation: gate green (step 9). Extra case.", "read", {"path": s["extra"]}, f"def test_extra():\n    # {s['residual']} — later\n    pass\n"),
        _step(11, "Observation: extra case (step 10). Full suite.", "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 6"}, f"{s['suite']} passed in 0.34s"),
        _step(12, f"Observation: suite (step 11). Residual: {s['residual']}.", "read", {"path": s["cfg"]}, s["residual"]),
        _step(13, "Observation: residual noted (step 12). Re-run gate.", "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 4"}, "2 passed in 0.07s"),
        _step(14, "Observation: 2/2 (step 13). Sequential accepted.", "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"}, f"{s['suite']} passed in 0.34s"),
        _step(15, "Observation: suite stable (step 14).", "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 3"}, "2 passed in 0.06s"),
        _step(16, "Observation: done (step 15).", "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 3"}, f"{s['suite']} passed in 0.34s"),
    ]
    record = {
        "id": f"gql-r{rnd}-{s['slug']}",
        "goal": f"{plant.plant} {s['fix']} {window} Gate: {s['test']}.",
        "plan": s["plan"],
        "steps": steps,
        "outcome": (
            f"{s['bug']}. Disabling {s['disable']} blew the SLO ({s['slo']}). "
            f"Plan change: bind current dest/source. Tests 2/2 + suite {s['suite']}/{s['suite']}. "
            f"Residual: {s['residual']}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": s["suite"], "cost_steps": 16},
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def _pair_fail(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    field = plant.payload["field"]
    window = plant.payload["window"]
    s = plant.payload["bad"]
    steps = [
        _step(
            1,
            f"Plan: read {plant.plant} entry and gate before disable {s['disable'].lower()}.",
            "bash",
            {"command": f"rg -n '{s['disable']}|{field}' src tests | head -n 26"},
            f"{s['src']}: {s['disable']} leftover\n{s['test']}: def test_one\n",
        ),
        _step(2, f"Observation: gate test (step 1). Read {s['src']}.", "read", {"path": s["src"]}, s["src_obs"]),
        _step(3, f"Observation: source confirms the bug (step 2). Read {s['test']}.", "read", {"path": s["test"]}, s["test_obs"]),
        _step(4, "Observation: gate expectations (step 3). Run.", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 10"}, s["fail_obs"]),
        _step(5, "Observation: failing assertion (step 4).", "bash", {"command": f"rg -n '{s['disable'].split()[0]}' {s['src']}"}, s["rg_obs"]),
        _step(6, f"Plan: first apply — disable {s['disable'].lower()}.", "edit", {"path": s["src"], "old": s["wrong_edit_old"], "new": s["wrong_edit_new"]}, f"patched disable {s['disable']}"),
        _step(7, "Observation: first apply (step 6).", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"}, f"FAILED test_slo - {s['slo']}\n1 failed, 1 passed\n", s["fix"]),
        _step(8, f"Reflection: plan change — {s['fix']}", "write", {"path": s["src"], "contents": s["fix_contents"]}, s["fix"]),
        _step(9, "Observation: rewrite (step 8). Re-run.", "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"}, "2 passed in 0.11s"),
        _step(10, "Observation: gate green (step 9). Extra case.", "read", {"path": s["extra"]}, f"def test_extra():\n    # {s['xfail_note']}\n    assert False\n"),
        _step(11, "Observation: extra case (step 10). Run with isolation.", "bash", {"command": f"pytest {s['extra']} -q --tb=short 2>&1 | tail -n 8"}, f"FAILED test_extra - {s['xfail_note']}\n1 failed\n"),
        _step(12, "Observation: extra still fails (step 11). Ticket allows handoff. xfail.", "edit", {"path": s["extra"], "old": "assert False", "new": "pytest.xfail('residual leftover')"}, "xfails extra"),
        _step(13, "Observation: xfails extra (step 12). Confirm gate still green.", "bash", {"command": f"pytest {s['test']} {s['extra']} -q --tb=line 2>&1 | tail -n 6"}, "2 passed, 1 xfailed in 0.12s"),
        _step(14, "Observation: isolation green (step 13). Residual is the handoff.", "read", {"path": s["src"]}, s["residual"]),
        _step(15, "Observation: residual noted (step 14). Re-run isolation.", "bash", {"command": f"pytest {s['test']} {s['extra']} -q --tb=line 2>&1 | tail -n 4"}, "2 passed, 1 xfailed in 0.11s"),
        _step(16, "Observation: gate stable (step 15). Handoff remains.", "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 3"}, "2 passed in 0.06s"),
    ]
    record = {
        "id": f"gql-r{rnd}-{s['slug']}",
        "goal": f"{plant.plant} {s['fix']} Leave a handoff if residual remains. {window} Gate: {s['test']}.",
        "plan": s["plan"],
        "steps": steps,
        "outcome": (
            f"{s['bug']}. Disabling {s['disable']} blew the SLO ({s['slo']}). "
            f"Plan change: bind current request/schema. Partial: {s['residual']} xfails."
        ),
        "reward": {"success": False, "plan_changes": 1, "tests_passed": 2, "xfailed": 1, "handoff": 1, "cost_steps": 16},
        "meta": _meta(rnd, plant, catalog_id),
    }
    _refuse_banned(record)
    return record


def _surface_success(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    c = plant.payload
    p, old, new, prod, mech, vs = c["prod"], c["old"], c["new"], c["product"], c["mech"], c["vs"]
    src = f"src/{plant.plant.replace('lattice-', '')}.gql"
    steps = [
        _step(1, f"Plan: read {plant.plant} {p} entry before {vs}.", "bash", {"command": f"rg -n '{mech}|{new}' src tests | head -n 28"}, f"{src}: leftover {old}\n{src}: {new}: Scalar\ntests/test_{p}.py: def test_one"),
        _step(2, f"Observation: {old} still answers after {new} bind.", "read", {"path": src}, f"type Query {{ {new}: Scalar }} leftover bind {old}"),
        _step(3, "Plan: capture SLO and query plan for current selection.", "bash", {"command": f"python3 scripts/explain_{p}.py --field {new}"}, f"plan uses leftover {old}; p95 410ms vs budget 80ms"),
        _step(4, "Observation: count leftover hits vs current field.", "bash", {"command": f"rg -c '{old}' src tests"}, f"src: 11 leftover {old} refs; tests expect {new}"),
        _step(5, f"Plan: try {vs} as first apply.", "edit", {"path": src, "old": f"{mech} on", "new": f"{vs} applied"}, f"{vs} applied; {new} empty; SLO miss"),
        _step(6, f"Observation: {vs} blew the budget; leftover still on {old}.", "bash", {"command": f"python3 tests/probe_{p}.py --field {new}"}, f"probe: {new} null; {old} still returned; cost 19 hits"),
        _step(7, f"Reflection: {vs} is wrong; need bind current {new} not leftover {old}.", "read", {"path": f"docs/{p}-leftover.md"}, f"doc: honor this {mech} for current field, not leftover first bind"),
        _step(8, f"Reflection: plan change — rebuild {prod} bind for this {new}, not leftover {old}.", "write", {"path": f"src/{p}_bind.py", "contents": f"bind({new})  # not leftover {old}\n"}, f"bind current {new}; leftover {old} dropped for this selection"),
        _step(9, "Plan: wire bind into executor after field resolve.", "edit", {"path": f"src/{p}_exec.py", "old": "use_first_bind()", "new": f"use_bind({new})"}, "executor uses current bind"),
        _step(10, "Observation: unit: current field; leftover first bind gone.", "bash", {"command": f"python3 -m pytest tests/test_{p}.py::test_current -q"}, "1 passed"),
        _step(11, "Plan: add regression that leftover first bind must not leak.", "write", {"path": f"tests/test_{p}_regress.py", "contents": f"def test_no_leftover_{old}():\n    assert resolve('{new}') != '{old}'\n"}, "regress written"),
        _step(12, "Observation: regress green; fragments still check.", "bash", {"command": f"python3 -m pytest tests/test_{p}_regress.py -q"}, "1 passed; fragment suite pending"),
        _step(13, "Plan: run fragment + alias suite.", "bash", {"command": f"python3 -m pytest tests/test_{p}_frag.py tests/test_{p}.py -q"}, "4 passed"),
        _step(14, "Observation: p95 after bind.", "bash", {"command": f"python3 scripts/bench_{p}.py --field {new}"}, "p95 54ms; leftover hits 0"),
        _step(15, "Plan: full suite.", "bash", {"command": f"python3 -m pytest tests/test_{p}*.py -q"}, "6 passed"),
        _step(16, f"Reflection: {prod} {mech} bound to {new}; {vs} not used in prod.", "read", {"path": f"src/{p}_bind.py"}, f"bind({new}) live; leftover {old} isolated"),
    ]
    record = {
        "id": f"gql-r{rnd}-{c['sid']}",
        "goal": f"Fix {prod} {mech} on plant {plant.plant}: leftover {old} after bind to {new}. Do not {vs}.",
        "plan": f"Diagnose leftover {old}; reject {vs}; bind current {new}; suite 6/6.",
        "steps": steps,
        "outcome": (
            f"{prod} still served leftover {old} after {new}. {vs} blew SLO. "
            f"Plan change: bind current {new}. Tests 2/2 + suite 6/6. Residual: fragments isolated."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 6, "cost_steps": 16},
        "meta": _meta(rnd, plant, catalog_id, {"kind": "success", "plant": plant.plant}),
    }
    _refuse_banned(record)
    return record


def _surface_fail(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    c = plant.payload
    p, old, new, prod, mech, vs = c["prod"], c["old"], c["new"], c["product"], c["mech"], c["vs"]
    src = f"src/{plant.plant.replace('lattice-', '')}.gql"
    steps = [
        _step(1, f"Plan: read {plant.plant} fail path for {prod} {vs}.", "bash", {"command": f"rg -n '{vs}|{old}' src tests | head -n 30"}, f"{src}: leftover {old}\n{vs} flag in config"),
        _step(2, "Observation: fail plant still serves leftover on interface fields.", "read", {"path": src}, f"interface Node leftover {old}; concrete {new} unused"),
        _step(3, "Plan: measure interface leftover.", "bash", {"command": f"python3 scripts/explain_{p}.py --iface Node"}, f"Node fields resolve via leftover {old}"),
        _step(4, "Observation: cost high on interface.", "bash", {"command": f"rg -c 'interface' {src}"}, "3 interface types leftover first bind"),
        _step(5, f"Plan: apply {vs} on fail path.", "edit", {"path": "config/flags.yml", "old": "enabled: true", "new": f"{vs}: true"}, f"{vs} on; interface fields empty"),
        _step(6, f"Observation: {vs} SLO miss; leftover {old} on unions.", "bash", {"command": f"python3 tests/probe_{p}.py --union"}, f"union still leftover {old}; concrete {new} skipped"),
        _step(7, f"Reflection: {vs} cannot clear union leftover; need per-type bind.", "read", {"path": f"docs/{p}-union.md"}, "doc: unions keep first leftover bind"),
        _step(8, "Reflection: plan change — bind current concrete; hand off unions.", "write", {"path": f"src/{p}_partial.py", "contents": f"bind_concrete({new})\n# unions leftover {old}\n"}, "concrete bound; unions leftover"),
        _step(9, "Plan: wire partial bind.", "edit", {"path": f"src/{p}_exec.py", "old": "global_bind()", "new": "partial_bind()"}, "partial bind live"),
        _step(10, "Observation: concrete tests pass; union xfails.", "bash", {"command": f"python3 -m pytest tests/test_{p}_conc.py -q"}, "2 passed"),
        _step(11, "Plan: document union leftover xfail.", "write", {"path": f"tests/test_{p}_union.py", "contents": "import pytest\n@pytest.mark.xfail\ndef test_union():\n    assert False\n"}, "xfail written"),
        _step(12, "Observation: xfail confirmed.", "bash", {"command": f"python3 -m pytest tests/test_{p}_union.py -q"}, "1 xfailed"),
        _step(13, "Plan: open handoff for union leftover.", "write", {"path": "HANDOFF.md", "contents": f"unions leftover {old}; need {prod} per-member bind\n"}, "handoff file"),
        _step(14, "Observation: oncall ticket.", "bash", {"command": "cat HANDOFF.md"}, f"unions leftover {old}; need {prod} per-member bind"),
        _step(15, "Plan: run partial suite.", "bash", {"command": f"python3 -m pytest tests/test_{p}_conc.py tests/test_{p}_union.py -q"}, "2 passed, 1 xfailed"),
        _step(16, "Observation: cost still high on unions.", "bash", {"command": f"python3 scripts/bench_{p}.py --union"}, "union p95 390ms leftover hits 8"),
        _step(17, f"Reflection: partial: {prod} {mech} on concrete {new}; handoff unions leftover {old}.", "read", {"path": "HANDOFF.md"}, f"handoff: unions leftover {old}; do not {vs} in prod"),
    ]
    record = {
        "id": f"gql-r{rnd}-{c['fid']}",
        "goal": f"Partial-fix {prod} {mech} fail path on {plant.plant}: leftover {old} on unions after {new}. Do not {vs}.",
        "plan": f"Reject {vs}; bind concrete {new}; xfail unions; handoff.",
        "steps": steps,
        "outcome": (
            f"{prod} unions still leftover {old} after {new}. {vs} emptied fields. "
            f"Plan change: bind concrete. Partial: union leftover xfails + handoff."
        ),
        "reward": {"success": False, "plan_changes": 1, "tests_passed": 2, "xfailed": 1, "handoff": 1, "cost_steps": 17},
        "meta": _meta(rnd, plant, catalog_id, {"kind": "partial", "plant": plant.plant}),
    }
    _refuse_banned(record)
    return record


def success_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    if plant.shape == SHAPE_PAIR:
        return _pair_success(rnd, plant, catalog_id)
    if plant.shape == SHAPE_SURFACE:
        return _surface_success(rnd, plant, catalog_id)
    raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{plant.plant_id} has unknown shape")


def fail_episode(rnd: int, plant: cat.Plant, catalog_id: str) -> dict[str, Any]:
    if plant.shape == SHAPE_PAIR:
        return _pair_fail(rnd, plant, catalog_id)
    if plant.shape == SHAPE_SURFACE:
        return _surface_fail(rnd, plant, catalog_id)
    raise GqlRefusal(FINDING_PLANT_FIELD_INVALID, f"{plant.plant_id} has unknown shape")


def notes_markdown(rnd: int, plant: cat.Plant) -> str:
    if plant.shape == SHAPE_PAIR:
        ok, bad = plant.payload["ok"], plant.payload["bad"]
        return (
            f"# NOTES r{rnd}\n\n"
            f"Novel coverage: {plant.coverage}%\n\n"
            f"- plant: `{plant.plant}` field `{plant.payload['field']}`\n"
            f"- success: `{ok['slug']}` isolate leftover; reject disable `{ok['disable']}`\n"
            f"- fail: `{bad['slug']}` handoff residual `{bad['residual']}`\n"
            f"- next: {plant.payload['next']}\n"
            f"- window: {plant.payload['window']}\n"
        )
    c = plant.payload
    return (
        f"# NOTES r{rnd}\n\n"
        f"Novel coverage: {plant.coverage}%\n\n"
        f"- plant: `{plant.plant}` {c['product']} {c['mech']} vs {c['vs']}\n"
        f"- success: bind current `{c['new']}`, not leftover `{c['old']}`\n"
        f"- fail: handoff unions leftover `{c['old']}`; do not `{c['vs']}`\n"
    )


def _require_round(value: int | None, default: int) -> int:
    rnd = default if value is None else value
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        raise GqlRefusal(FINDING_ROUND_INVALID, f"round must be a positive int, got {value!r}")
    return rnd


def _jobs(loaded: cat.Catalog, request: GenerateRequest) -> list[tuple[int, cat.Plant]]:
    selectors = (request.plant_id is not None, request.mill_id is not None, request.all_plants)
    if sum(selectors) != 1:
        raise GqlRefusal(FINDING_USAGE, "exactly one of plant_id, mill_id, or all_plants")
    if request.plant_id is not None:
        plant = loaded.plant(request.plant_id)
        return [(_require_round(request.round, plant.base_round), plant)]
    if request.round is not None:
        raise GqlRefusal(FINDING_USAGE, "round applies only with plant_id")
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
        raise GqlRefusal(FINDING_DESTINATION_UNDER_RAW, f"{out_dir} names or aliases the raw tree")
    if out_dir.exists():
        raise GqlRefusal(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


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
    (out_dir / RECORDS_FILENAME).write_text(records_text, encoding="utf-8")
    (out_dir / NOTES_FILENAME).write_text("\n".join(note_chunks), encoding="utf-8")
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
