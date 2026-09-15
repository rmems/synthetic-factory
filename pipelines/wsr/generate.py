#!/usr/bin/env python3
"""Build leftover3 websocket-reconnect episodes from the pinned catalog.

Designed traces only. Writes a brand-new destination and refuses
``outputs/raw/``. The leftover mill is never imported or executed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._contract import (
    BANNED_RECORD_KEYS,
    BANNED_SLUGS,
    BANNED_SLUG_TOKENS,
    DECISION_PREFIXES,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_GENERATE_DEST_EXISTS,
    FINDING_GENERATE_GOAL,
    FINDING_GENERATE_HIDDEN,
    FINDING_GENERATE_RAW_TREE,
    FINDING_GENERATE_ROUND,
    FINDING_GENERATE_SHAPE,
    GENERATOR,
    HANDOFF_STEPS,
    MAX_DECISION_BASIS,
    PLACEHOLDER_GOALS,
    SUCCESS_STEPS,
    bind_import_twin,
    contains_hidden_reasoning_key,
    dumps_exact_json,
    is_under_raw,
    refuse_when,
)
from . import catalog as cat

__all__ = [
    "BuiltPair",
    "build_catalog",
    "build_fail",
    "build_pair",
    "build_success",
    "generate",
    "notes_md",
    "validate_pair",
]


@dataclass(frozen=True)
class BuiltPair:
    round_n: int
    ok: dict[str, Any]
    bad: dict[str, Any]
    notes: str


def _goal_ok(goal: object) -> str:
    refuse_when(
        not isinstance(goal, str),
        FINDING_GENERATE_GOAL,
        f"goal must be a string, got {goal!r}",
    )
    assert isinstance(goal, str)
    lowered = goal.strip().lower()
    refuse_when(
        not goal.strip() or lowered in PLACEHOLDER_GOALS,
        FINDING_GENERATE_GOAL,
        f"placeholder goal: {goal!r}",
    )
    refuse_when("[variant" in lowered, FINDING_GENERATE_GOAL, f"variant stamp in goal: {goal!r}")
    for token in BANNED_SLUG_TOKENS:
        refuse_when(token in lowered, FINDING_GENERATE_GOAL, f"banned topic in goal: {goal!r}")
    return goal


def _paths(plant: Mapping[str, Any]) -> tuple[str, str, str]:
    return f"src/{plant['mod']}.py", f"tests/test_{plant['mod']}.py", f"{plant['mod']}/cfg.yml"


def _step(
    n: int,
    decision_basis: str,
    tool_call: dict[str, Any],
    observation: str,
    reflection: str,
) -> dict[str, Any]:
    refuse_when(
        not decision_basis.startswith(DECISION_PREFIXES),
        FINDING_GENERATE_SHAPE,
        f"step {n} decision_basis prefix: {decision_basis!r}",
    )
    refuse_when(
        len(decision_basis) > MAX_DECISION_BASIS,
        FINDING_GENERATE_SHAPE,
        f"step {n} decision_basis {len(decision_basis)} > {MAX_DECISION_BASIS}",
    )
    refuse_when(
        not observation.strip() or not reflection.strip(),
        FINDING_GENERATE_SHAPE,
        f"step {n} empty observation/reflection",
    )
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict[str, Any]:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict[str, Any]:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _pytest(args: str) -> dict[str, Any]:
    return {"name": "pytest", "args": {"args": args}}


def _fetch(url: str) -> dict[str, Any]:
    return {"name": "fetch", "args": {"url": url}}


def _assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            refuse_when(
                key in BANNED_RECORD_KEYS,
                FINDING_GENERATE_HIDDEN,
                f"banned key {key} at {path}",
            )
            refuse_when(
                key == "sim_or_real" and val == "real",
                FINDING_GENERATE_HIDDEN,
                f"sim_or_real real at {path}",
            )
            refuse_when(key == "spike_events", FINDING_GENERATE_HIDDEN, f"spike_events at {path}")
            _assert_clean(val, f"{path}.{key}")
        return
    if isinstance(obj, list):
        for index, item in enumerate(obj):
            _assert_clean(item, f"{path}[{index}]")


def _episode_id(round_n: int, slug: str) -> str:
    return f"{FAMILY_PREFIX}-r{round_n}-{slug}"


def build_success(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    _goal_ok(plant["goal"])
    src, test, cfg = _paths(plant)
    eid = _episode_id(round_n, str(plant["slug"]))
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {plant['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {plant['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.", _read(test), str(plant["test_body"]), "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"), str(plant["grep_hit"]), f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), str(plant["src_body"]), "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(str(plant["docs_url"])), f"GET {plant['docs_url']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(str(plant["docs_url"])), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{plant['docs_ok']}", "Degraded path used the local fixture. Continue with that content."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(str(plant["docs_url2"])), f"GET {plant['docs_url2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(str(plant["docs_url2"])), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{plant['docs_ok2']}", "Retry succeeded. Resume the local debug plan with that document in hand."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, str(plant["first_old"]), str(plant["first_new"])), str(plant["first_obs"]), "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{plant['test_fn']}). Re-read {src}.", _read(src), str(plant["reread_obs"]), f"Plan change: {plant['plan_change']}"),
        _step(13, f"Reflection: {plant['plan_change']}"[:240], _edit(src, str(plant["first_new"]), str(plant["fix_new"])), str(plant["fix_obs"]), "Corrective patch applied. Run the original failing node again."),
        _step(14, "Observation: fix edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), "1 passed in 0.16s", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q`.", _bash(f"pytest {test} -q"), "3 passed in 0.28s", "Broader check captured. Stop; residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {plant['slug']}: {src} | 9 ++++++---. No other modified paths.", "Diff is the review artifact. No further edits."),
    ]
    episode = {
        "id": eid,
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": {
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": SUCCESS_STEPS,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": plant["seed"],
            "designed": True,
            "domain": plant["domain"],
            "stack": plant["stack"],
        },
    }
    _assert_clean(episode)
    refuse_when(contains_hidden_reasoning_key(episode), FINDING_GENERATE_HIDDEN, f"{eid} hidden reasoning")
    refuse_when(len(steps) != SUCCESS_STEPS, FINDING_GENERATE_SHAPE, f"{eid} expected {SUCCESS_STEPS} steps")
    return episode


def build_fail(round_n: int, plant: Mapping[str, Any]) -> dict[str, Any]:
    _goal_ok(plant["goal"])
    src, test, cfg = _paths(plant)
    eid = _episode_id(round_n, str(plant["slug"]))
    ticket = str(plant["ticket"])
    ticket_path = f"{plant['mod']}/handoff.md"
    listing = f"{src} {cfg}\n{test}"
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    steps = [
        _step(1, f"Plan: list src {plant['mod']} and tests before touching conversion or config.", _bash(f"ls -la src {plant['mod']} tests | head -40"), listing, f"Tree shows {src} plus tests. Run the named failing target next."),
        _step(2, f"Observation: listing named the test files. Run `{pytest_args}` to capture the failure.", _pytest(pytest_args), fail_obs, f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix."),
        _step(3, f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.", _read(test), str(plant["test_body"]), "Test contract is visible. Search implementation symbols next."),
        _step(4, "Observation: test file imported the production helper. Grep those symbols.", _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"), str(plant["grep_hit"]), f"Grep hit {src}. Read it before editing the first match."),
        _step(5, f"Observation: grep listed {src}. Read it before any patch.", _read(src), str(plant["src_body"]), "First read done. Fetch vendor docs next; do not patch on a hunch yet."),
        _step(6, "Observation: local files are in. Need the changelog/registry before editing.", _fetch(str(plant["docs_url"])), f"GET {plant['docs_url']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\nX-RateLimit-Remaining: 0", "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        _step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.", _fetch(str(plant["docs_url"])), f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{plant['docs_ok']}", "Retry succeeded. Continue with that document."),
        _step(8, "Observation: local files are in. Need the second remote document before editing.", _fetch(str(plant["docs_url2"])), f"GET {plant['docs_url2']}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.", "Call failed with upstream gateway failure. Recover with backoff."),
        _step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.", _fetch(str(plant["docs_url2"])), f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{plant['docs_ok2']}", "Degraded path used the local fixture. Resume the local debug plan."),
        _step(10, f"Observation: docs and source are in. Apply the first patch to {src}.", _edit(src, str(plant["first_old"]), str(plant["first_new"])), str(plant["first_obs"]), "Patch applied. Re-run the failing test; do not assume green."),
        _step(11, f"Observation: edit wrote {src}. Re-run the same failing node.", _pytest(pytest_args), still_obs, "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        _step(12, f"Observation: post-edit test still failed ({test}::{plant['test_fn']}). Re-read {src}.", _read(src), str(plant["reread_obs"]), f"Plan change: {plant['plan_change']}"),
        _step(13, f"Reflection: {plant['plan_change']}"[:240], _edit(ticket_path, "", f"# {ticket} {plant['ticket_why']}"), str(plant["fix_obs"]), "Handoff ticket written. Run the original failing node again."),
        _step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.", _pytest(pytest_args), f"{test}::{plant['test_fn']} FAILED  # handoff: {ticket}\n1 failed", "Result recorded. Run one broader check before declaring the outcome."),
        _step(15, f"Observation: focused run finished. Run broader check `pytest {test} -q; echo {ticket}`.", _bash(f"pytest {test} -q; echo {ticket}"), f"1 failed, 2 passed\n{ticket}", "Broader check captured. Residual risk belongs in the outcome text."),
        _step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.", _bash("git diff --stat | head -n 40"), f"diffstat for {plant['slug']}: {src} | 8 +++++---. {ticket_path} added.", "Diff is the review artifact. Lint next."),
        _step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.", _bash("ruff check tests || true; echo lint-end"), "All checks passed!\nlint-end", "Lint clean. Episode complete."),
    ]
    episode = {
        "id": eid,
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": {
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": HANDOFF_STEPS,
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "kind": "episode",
            "seed": plant["seed"],
            "designed": True,
            "domain": plant["domain"],
            "stack": plant["stack"],
        },
    }
    _assert_clean(episode)
    refuse_when(contains_hidden_reasoning_key(episode), FINDING_GENERATE_HIDDEN, f"{eid} hidden reasoning")
    refuse_when(len(steps) != HANDOFF_STEPS, FINDING_GENERATE_SHAPE, f"{eid} expected {HANDOFF_STEPS} steps")
    refuse_when("ticket" not in plant, FINDING_GENERATE_SHAPE, f"{eid} handoff missing ticket")
    return episode


def notes_md(round_n: int, ok: Mapping[str, Any], bad: Mapping[str, Any], ok_id: str, bad_id: str) -> str:
    cov = max(int(ok.get("coverage", 80)), int(bad.get("coverage", 80)))
    notes = (
        f"# {FACTORY} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad['domain']}, seed={bad['seed']}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are "
        f"domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {bad_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )
    refuse_when("Novel coverage:" not in notes, FINDING_GENERATE_SHAPE, "NOTES missing Novel coverage")
    return notes


def validate_pair(ok_ep: dict[str, Any], bad_ep: dict[str, Any], round_n: int) -> None:
    refuse_when(ok_ep["reward"]["success"] is not True, FINDING_GENERATE_SHAPE, "first episode must succeed")
    refuse_when(bad_ep["reward"]["success"] is not False, FINDING_GENERATE_SHAPE, "second episode must fail/handoff")
    refuse_when(
        len(ok_ep["steps"]) != SUCCESS_STEPS or len(bad_ep["steps"]) != HANDOFF_STEPS,
        FINDING_GENERATE_SHAPE,
        "shape must be 16-step success + 17-step fail",
    )
    refuse_when(
        ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n,
        FINDING_GENERATE_SHAPE,
        "meta.round mismatch",
    )
    refuse_when(ok_ep["meta"]["generator"] != GENERATOR, FINDING_GENERATE_SHAPE, "generator")
    refuse_when(ok_ep["id"] == bad_ep["id"], FINDING_GENERATE_SHAPE, "duplicate episode ids")
    for episode in (ok_ep, bad_ep):
        _goal_ok(episode["goal"])
        _assert_clean(episode)
        seed = episode["meta"].get("seed")
        refuse_when(
            seed in BANNED_SLUGS or episode["id"].split("-", 2)[-1] in BANNED_SLUGS,
            FINDING_GENERATE_SHAPE,
            f"banned slug {episode['id']}",
        )


def build_pair(pair: cat.Pair) -> BuiltPair:
    ok_ep = build_success(pair.round_n, pair.ok)
    bad_ep = build_fail(pair.round_n, pair.bad)
    validate_pair(ok_ep, bad_ep, pair.round_n)
    notes = notes_md(pair.round_n, pair.ok, pair.bad, ok_ep["id"], bad_ep["id"])
    return BuiltPair(round_n=pair.round_n, ok=ok_ep, bad=bad_ep, notes=notes)


def build_catalog(catalog: cat.Catalog) -> tuple[BuiltPair, ...]:
    return tuple(build_pair(pair) for pair in catalog.pairs)


def _refuse_destination(out_dir: Path) -> None:
    refuse_when(is_under_raw(out_dir), FINDING_GENERATE_RAW_TREE, f"refusing raw-tree dest {out_dir}")
    refuse_when(out_dir.exists(), FINDING_GENERATE_DEST_EXISTS, f"destination exists: {out_dir}")


def write_round(out_dir: Path, built: BuiltPair) -> tuple[Path, Path]:
    batch = out_dir / f"batch-r{built.round_n:02d}.jsonl"
    notes = out_dir / f"NOTES-r{built.round_n:02d}.md"
    refuse_when(
        is_under_raw(batch) or is_under_raw(notes),
        FINDING_GENERATE_RAW_TREE,
        "refusing raw-tree write",
    )
    batch.write_text(
        dumps_exact_json(built.ok) + "\n" + dumps_exact_json(built.bad) + "\n",
        encoding="utf-8",
        newline="",
    )
    notes.write_text(built.notes, encoding="utf-8")
    return batch, notes


def generate(
    out_dir: Path,
    *,
    catalog: cat.Catalog | None = None,
    rounds: tuple[int, ...] | None = None,
    catalog_path: Path | None = None,
) -> tuple[BuiltPair, ...]:
    """Write leftover3 batches into a brand-new destination."""

    loaded = catalog if catalog is not None else cat.catalog_check(catalog_path)
    selected = loaded.pairs
    if rounds is not None:
        wanted = set(rounds)
        selected = tuple(pair for pair in loaded.pairs if pair.round_n in wanted)
        missing = wanted.difference(pair.round_n for pair in selected)
        refuse_when(bool(missing), FINDING_GENERATE_ROUND, f"unknown rounds: {sorted(missing)}")
    _refuse_destination(out_dir)
    out_dir.mkdir(parents=True)
    built = tuple(build_pair(pair) for pair in selected)
    for item in built:
        write_round(out_dir, item)
    return built


bind_import_twin(__name__)
