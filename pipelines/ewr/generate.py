#!/usr/bin/env python3
"""Build ewr leftover-event episodes from the pinned catalog.

The step shape is AST-extracted from hopper_mill_g46d (16-step success +
17-step handoff). This module never writes ``outputs/raw/`` and never imports
``ewr_*mill.py``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED_RECORD_KEYS,
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
    SUCCESS_STEPS,
    bind_import_twin,
    contains_hidden_reasoning_key,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
)

PLACEHOLDER_GOALS = frozenset({"", "x", "placeholder", "todo", "tbd", "fix it"})


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
    refuse_when(lowered in PLACEHOLDER_GOALS, FINDING_GENERATE_GOAL, f"placeholder goal: {goal!r}")
    refuse_when("[variant" in lowered, FINDING_GENERATE_GOAL, f"variant stamp in goal: {goal!r}")
    return goal


def _paths(plant: Mapping[str, Any]) -> tuple[str, str, str]:
    mod = plant["mod"]
    return f"src/{mod}.py", f"tests/test_{mod}.py", f"{mod}/cfg.yml"


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


def _debug_steps(
    plant: Mapping[str, Any], src: str, test: str, listing: str
) -> list[dict[str, Any]]:
    pytest_args = f"{test} -q --tb=short"
    fail_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['fail_msg']}"
    return [
        _step(
            1,
            f"Plan: list src {plant['mod']} and tests before touching conversion or config.",
            _bash(f"ls -la src {plant['mod']} tests | head -40"),
            listing,
            f"Tree shows {src} plus tests. Run the named failing target next.",
        ),
        _step(
            2,
            (
                "Observation: listing named the test files. "
                f"Run `{pytest_args}` to capture the failure."
            ),
            _pytest(pytest_args),
            fail_obs,
            f"Failure is at {test}::{plant['test_fn']}. Read that test before a one-line fix.",
        ),
        _step(
            3,
            f"Observation: {test}::{plant['test_fn']} is red. Read {test} around the assertion.",
            _read(test),
            str(plant["test_body"]),
            "Test contract is visible. Search implementation symbols next.",
        ),
        _step(
            4,
            "Observation: test file imported the production helper. Grep those symbols.",
            _bash(f"rg -n '{plant['grep_pat']}' src {plant['mod']} tests"),
            str(plant["grep_hit"]),
            f"Grep hit {src}. Read it before editing the first match.",
        ),
        _step(
            5,
            f"Observation: grep listed {src}. Read it before any patch.",
            _read(src),
            str(plant["src_body"]),
            "First read done. Fetch vendor docs next; do not patch on a hunch yet.",
        ),
    ]


def _docs_steps(plant: Mapping[str, Any], *, success: bool) -> list[dict[str, Any]]:
    url, url2 = str(plant["docs_url"]), str(plant["docs_url2"])
    body, body2 = str(plant["docs_ok"]), str(plant["docs_ok2"])
    gateway_fail = f"GET {url if success else url2}\nHTTP/1.1 502 Bad Gateway\nBad Gateway."
    gateway_ok = (
        (
            "retry after 2s backoff; local vendor fixture\n"
            f"HTTP/1.1 200 OK\n{body if success else body2}"
        )
    )
    retry_after = 5 if success else 6
    limited_url = url2 if success else url
    limited_body = body2 if success else body
    rate_fail = (
        f"GET {limited_url}\nHTTP/1.1 429 Too Many Requests\n"
        f"Retry-After: {retry_after}\nX-RateLimit-Remaining: 0"
    )
    rate_ok = f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{limited_body}"
    if success:
        first = (
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(url),
            gateway_fail,
            "Call failed with upstream gateway failure. Recover with backoff.",
            (
                "Observation: the prior call returned an upstream gateway "
                "failure. Retry once with 2s backoff."
            ),
            _fetch(url),
            gateway_ok,
            "Degraded path used the local fixture. Continue with that content.",
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(url2),
            rate_fail,
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
            (
                "Observation: the prior call returned rate-limit status "
                "with Retry-After. Sleep then retry."
            ),
            _fetch(url2),
            rate_ok,
            "Retry succeeded. Resume the local debug plan with that document in hand.",
        )
    else:
        first = (
            "Observation: local files are in. Need the changelog/registry before editing.",
            _fetch(url),
            rate_fail,
            "Call failed with rate-limit status with Retry-After. Recover with backoff.",
            (
                "Observation: the prior call returned rate-limit status "
                "with Retry-After. Sleep then retry."
            ),
            _fetch(url),
            rate_ok,
            "Retry succeeded. Continue with that document.",
            "Observation: local files are in. Need the second remote document before editing.",
            _fetch(url2),
            gateway_fail,
            "Call failed with upstream gateway failure. Recover with backoff.",
            (
                "Observation: the prior call returned an upstream gateway "
                "failure. Retry once with 2s backoff."
            ),
            _fetch(url2),
            gateway_ok,
            "Degraded path used the local fixture. Resume the local debug plan.",
        )
    return [
        _step(6, first[0], first[1], first[2], first[3]),
        _step(7, first[4], first[5], first[6], first[7]),
        _step(8, first[8], first[9], first[10], first[11]),
        _step(9, first[12], first[13], first[14], first[15]),
    ]


def _reread_steps(plant: Mapping[str, Any], src: str, test: str) -> list[dict[str, Any]]:
    pytest_args = f"{test} -q --tb=short"
    still_obs = f"{test}::{plant['test_fn']} FAILED\nE   {plant['still_msg']}"
    return [
        _step(
            10,
            f"Observation: docs and source are in. Apply the first patch to {src}.",
            _edit(src, str(plant["first_old"]), str(plant["first_new"])),
            str(plant["first_obs"]),
            "Patch applied. Re-run the failing test; do not assume green.",
        ),
        _step(
            11,
            f"Observation: edit wrote {src}. Re-run the same failing node.",
            _pytest(pytest_args),
            still_obs,
            "Still red after the first patch. Re-read the implementation; hypothesis is wrong.",
        ),
        _step(
            12,
            (
                f"Observation: post-edit test still failed "
                f"({test}::{plant['test_fn']}). Re-read {src}."
            ),
            _read(src),
            str(plant["reread_obs"]),
            f"Plan change: {plant['plan_change']}",
        ),
    ]


def _episode(
    plant: Mapping[str, Any],
    *,
    factory: str,
    prefix: str,
    round_n: int,
    steps: list[dict[str, Any]],
    reward: dict[str, Any],
) -> dict[str, Any]:
    _goal_ok(plant["goal"])
    episode = {
        "id": f"{prefix}-r{round_n}-{plant['slug']}",
        "goal": plant["goal"],
        "plan": plant["plan"],
        "steps": steps,
        "outcome": plant["outcome"],
        "reward": reward,
        "meta": {
            "factory": factory,
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
    refuse_when(
        contains_hidden_reasoning_key(episode),
        FINDING_GENERATE_HIDDEN,
        f"{episode['id']} carries a hidden-reasoning key",
    )
    return episode


def build_success(
    plant: Mapping[str, Any], *, factory: str, prefix: str, round_n: int
) -> dict[str, Any]:
    src, test, cfg = _paths(plant)
    listing = f"{src} {cfg}\n{test}"
    steps = (
        _debug_steps(plant, src, test, listing)
        + _docs_steps(plant, success=True)
        + _reread_steps(plant, src, test)
        + [
            _step(
                13,
                f"Reflection: {plant['plan_change']}"[:MAX_DECISION_BASIS],
                _edit(src, str(plant["first_new"]), str(plant["fix_new"])),
                str(plant["fix_obs"]),
                "Corrective patch applied. Run the original failing node again.",
            ),
            _step(
                14,
                "Observation: fix edit returned clean. Re-run the original failing test node.",
                _pytest(f"{test} -q --tb=short"),
                "1 passed in 0.16s",
                "Result recorded. Run one broader check before declaring the outcome.",
            ),
            _step(
                15,
                f"Observation: focused run finished. Run broader check `pytest {test} -q`.",
                _bash(f"pytest {test} -q"),
                "3 passed in 0.28s",
                "Broader check captured. Stop; residual risk belongs in the outcome text.",
            ),
            _step(
                16,
                (
                    "Observation: broader check is on disk. Show the diff "
                    "of patched files for the handoff note."
                ),
                _bash("git diff --stat | head -n 40"),
                f"diffstat for {plant['slug']}: {src} | 9 ++++++---. No other modified paths.",
                "Diff is the review artifact. No further edits.",
            ),
        ]
    )
    refuse_when(
        len(steps) != SUCCESS_STEPS,
        FINDING_GENERATE_SHAPE,
        f"expected {SUCCESS_STEPS} success steps",
    )
    return _episode(
        plant,
        factory=factory,
        prefix=prefix,
        round_n=round_n,
        steps=steps,
        reward={
            "success": True,
            "tests_passed": 3,
            "retries": 2,
            "duration_min": 610,
            "wasted_calls": 180,
            "cost_steps": SUCCESS_STEPS,
            "plan_changes": 1,
        },
    )


def build_handoff(
    plant: Mapping[str, Any], *, factory: str, prefix: str, round_n: int
) -> dict[str, Any]:
    src, test, cfg = _paths(plant)
    listing = f"{src} {cfg}\n{test}"
    ticket = str(plant["ticket"])
    ticket_path = f"{plant['mod']}/handoff.md"
    steps = (
        _debug_steps(plant, src, test, listing)
        + _docs_steps(plant, success=False)
        + _reread_steps(plant, src, test)
        + [
            _step(
                13,
                f"Reflection: {plant['plan_change']}"[:MAX_DECISION_BASIS],
                _edit(ticket_path, "", f"# {ticket} {plant['ticket_why']}"),
                str(plant["fix_obs"]),
                "Handoff ticket written. Run the original failing node again.",
            ),
            _step(
                14,
                "Observation: handoff edit returned clean. Re-run the original failing test node.",
                _pytest(f"{test} -q --tb=short"),
                f"{test}::{plant['test_fn']} FAILED  # handoff: {ticket}\n1 failed",
                "Result recorded. Run one broader check before declaring the outcome.",
            ),
            _step(
                15,
                (
                    "Observation: focused run finished. Run broader check "
                    f"`pytest {test} -q; echo {ticket}`."
                ),
                _bash(f"pytest {test} -q; echo {ticket}"),
                f"1 failed, 2 passed\n{ticket}",
                "Broader check captured. Residual risk belongs in the outcome text.",
            ),
            _step(
                16,
                (
                    "Observation: broader check is on disk. Show the diff "
                    "of patched files for the handoff note."
                ),
                _bash("git diff --stat | head -n 40"),
                f"diffstat for {plant['slug']}: {src} | 8 +++++---. {ticket_path} added.",
                "Diff is the review artifact. Lint next.",
            ),
            _step(
                17,
                "Observation: diffstat listed the patched files. Run a linter on those paths only.",
                _bash("ruff check tests || true; echo lint-end"),
                "All checks passed!\nlint-end",
                "Lint clean. Episode complete.",
            ),
        ]
    )
    refuse_when(
        len(steps) != HANDOFF_STEPS,
        FINDING_GENERATE_SHAPE,
        f"expected {HANDOFF_STEPS} handoff steps",
    )
    return _episode(
        plant,
        factory=factory,
        prefix=prefix,
        round_n=round_n,
        steps=steps,
        reward={
            "success": False,
            "tests_passed": 2,
            "retries": 2,
            "duration_min": 640,
            "wasted_calls": 210,
            "cost_steps": HANDOFF_STEPS,
            "plan_changes": 1,
        },
    )


def notes_markdown(
    factory: str,
    round_n: int,
    ok: Mapping[str, Any],
    bad: Mapping[str, Any],
    ok_id: str,
    bad_id: str,
) -> str:
    coverage = max(int(ok.get("coverage", 80)), int(bad.get("coverage", 80)))
    notes = (
        f"# {factory} — NOTES r{round_n}\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: {SUCCESS_STEPS} steps, success=True, "
        f"domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: {HANDOFF_STEPS} steps, success=False, "
        f"domain={bad['domain']}, seed={bad['seed']}\n"
        "  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 "
        "(order may swap with success side)\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤{MAX_DECISION_BASIS}, no thought/chain_of_thought/scratch/inner_monologue keys, "
        f"no spike_events, no sim_or_real real, no Spikenaut. Generator {GENERATOR}. "
        f"No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are "
        f"domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: {SUCCESS_STEPS} (required 14–18)\n"
        f"- {bad_id}: {HANDOFF_STEPS} (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )
    refuse_when(
        "Novel coverage:" not in notes,
        FINDING_GENERATE_SHAPE,
        "NOTES missing Novel coverage",
    )
    return notes


def validate_pair(ok_ep: dict[str, Any], bad_ep: dict[str, Any], round_n: int) -> None:
    refuse_when(
        ok_ep["reward"]["success"] is not True,
        FINDING_GENERATE_SHAPE,
        "first episode must succeed",
    )
    refuse_when(
        bad_ep["reward"]["success"] is not False,
        FINDING_GENERATE_SHAPE,
        "second episode must fail/handoff",
    )
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


def build_pair(pair: cat.Pair, *, factory: str = FACTORY, prefix: str = FAMILY_PREFIX) -> BuiltPair:
    ok_ep = build_success(pair.ok, factory=factory, prefix=prefix, round_n=pair.round_n)
    bad_ep = build_handoff(pair.bad, factory=factory, prefix=prefix, round_n=pair.round_n)
    validate_pair(ok_ep, bad_ep, pair.round_n)
    notes = notes_markdown(factory, pair.round_n, pair.ok, pair.bad, ok_ep["id"], bad_ep["id"])
    return BuiltPair(round_n=pair.round_n, ok=ok_ep, bad=bad_ep, notes=notes)


def build_catalog(catalog: cat.Catalog) -> tuple[BuiltPair, ...]:
    return tuple(
        build_pair(pair, factory=catalog.factory, prefix=catalog.family_prefix)
        for pair in catalog.pairs
    )


def _refuse_destination(out_dir: Path) -> None:
    refuse_when(
        is_under_raw(out_dir),
        FINDING_GENERATE_RAW_TREE,
        f"refusing raw-tree dest {out_dir}",
    )
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
    """Write leftover-event batches into a brand-new destination."""

    loaded = catalog if catalog is not None else cat.catalog_check(catalog_path)
    selected = loaded.pairs
    if rounds is not None:
        wanted = set(rounds)
        selected = tuple(pair for pair in loaded.pairs if pair.round_n in wanted)
        missing = wanted.difference(pair.round_n for pair in selected)
        refuse_when(bool(missing), FINDING_GENERATE_ROUND, f"unknown rounds: {sorted(missing)}")
    _refuse_destination(out_dir)
    out_dir.mkdir(parents=True)
    built = tuple(
        build_pair(pair, factory=loaded.factory, prefix=loaded.family_prefix)
        for pair in selected
    )
    for item in built:
        write_round(out_dir, item)
    return built


bind_import_twin(__name__)
