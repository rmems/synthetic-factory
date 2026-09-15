#!/usr/bin/env python3
"""Build one sparse-reward episode from an ``srl_r6110`` plant.

The 32-step tool sequence is the designed trajectory from the AST-extracted
mill: two abandoned hypotheses, then the fix on app/worker/canary/live,
with reward only at the terminal. This module does not publish a raw round.
"""

from __future__ import annotations

import hashlib
from typing import Any

from . import catalog as cat
from ._contract import (
    BANNED,
    FACTORY,
    GEN,
    N_STEPS,
    NOVEL_COVERAGE,
    SOURCE_ROUND,
    SrlError,
    THEME_TOOLS,
    dumps_exact_json,
    require_round,
)

__all__ = ["episode", "generate_window", "hid", "notes", "record_id"]


def hid(slug: str) -> str:
    """Four-hex identity suffix used by ``srl-r<round>-<slug>-<hid>``."""

    if type(slug) is not str or not slug:
        raise SrlError(f"unknown_plant: {slug!r}")
    return hashlib.sha1(slug.encode()).hexdigest()[:4]


def record_id(rnd: int, slug: str) -> str:
    return f"srl-r{require_round(rnd)}-{slug}-{hid(slug)}"


def _step(n: int, basis: str, name: str, args: dict[str, str], observation: str) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }


def _steps(plant: cat.Plant) -> list[dict[str, Any]]:
    work = f"/work/{plant['plant']}"
    test = f"tests/{plant['test']}.py"
    issue = f"ISSUE-{plant['issue']}.md"
    bad = plant["bad"]
    h1 = plant["h1"]
    h2 = plant["h2"]
    fix = plant["fix"]
    grep = plant["grep"]
    tool = plant["tool"].split()[0]
    glob = "*.{py,yml,md,conf,hcl,toml,cfg}"
    return [
        _step(
            1,
            f"Plan: locate {plant['tool']} vs {plant['vs']} before {h1}.",
            "grep",
            {"pattern": grep, "path": work, "glob": glob},
            f"app/runtime.conf: {bad}\n{issue}: {plant['slug']}; "
            f"{plant['tool']} vs {plant['vs']}\n{test}: missing\ncanary/runtime.conf: {bad}",
        ),
        _step(2, "Observation: three surfaces hold the old knob.",
              "read_file", {"path": f"{work}/app/runtime.conf"},
              f"{bad}  # vs invoice"),
        _step(3, "Observation: invoice names the fork.",
              "read_file", {"path": f"{work}/{issue}"},
              f"# {plant['slug']}\n# {plant['tool']} vs {plant['vs']}"),
        _step(4, "Observation: pytest gate missing. Scaffold H1.",
              "write", {"path": f"{work}/{test}", "contents": f"assert False  # H1 {h1}"},
              f"wrote stub {test}"),
        _step(5, "Observation: apply H1 on app only.",
              "search_replace", {"path": f"{work}/app/runtime.conf", "old": bad, "new": h1},
              f"app now {h1}"),
        _step(6, "Observation: pytest still fails; H1 abandoned.",
              "bash", {"command": f"pytest -q {test}"},
              f"FAILED worker/canary still {bad}; H1 {h1} not the invoice"),
        _step(7, "Observation: H1 abandoned. Try H2.",
              "search_replace", {"path": f"{work}/app/runtime.conf", "old": h1, "new": h2},
              f"app now {h2}"),
        _step(8, "Observation: H2 is a bounce/flush; abandon.",
              "bash", {"command": f"pytest -q {test}"},
              f"FAILED H2 {h2} is not credit; invoice wants {fix}"),
        _step(9, "Observation: apply the fix on app.",
              "search_replace", {"path": f"{work}/app/runtime.conf", "old": h2, "new": fix},
              f"app {fix}"),
        _step(10, "Observation: worker still old.",
              "read_file", {"path": f"{work}/worker/runtime.conf"}, bad),
        _step(11, "Observation: pin worker.",
              "search_replace", {"path": f"{work}/worker/runtime.conf", "old": bad, "new": fix},
              f"worker {fix}"),
        _step(12, "Observation: canary still old.",
              "read_file", {"path": f"{work}/canary/runtime.conf"}, bad),
        _step(13, "Observation: pin canary.",
              "search_replace", {"path": f"{work}/canary/runtime.conf", "old": bad, "new": fix},
              f"canary {fix}"),
        _step(14, "Observation: rewrite the pytest gate.",
              "write", {"path": f"{work}/{test}", "contents": f"assert all_surfaces({fix!r})"},
              f"gate asserts {fix} on app+worker+canary"),
        _step(15, "Observation: non-signal CLI is not credit.",
              "bash", {"command": f"{tool} --version"},
              "non-signal version banner; not credit"),
        _step(16, "Observation: run pytest.",
              "bash", {"command": f"pytest -q {test}"},
              "1 failed; live pin still old isolation"),
        _step(17, "Observation: live overlay.",
              "read_file", {"path": f"{work}/live/runtime.conf"}, bad),
        _step(18, "Observation: pin live.",
              "search_replace", {"path": f"{work}/live/runtime.conf", "old": bad, "new": fix},
              f"live {fix}"),
        _step(19, "Observation: helm values.",
              "grep", {"pattern": grep, "path": f"{work}/deploy"},
              f"deploy/values.yaml {bad}"),
        _step(20, "Observation: pin helm.",
              "search_replace",
              {"path": f"{work}/deploy/values.yaml", "old": bad, "new": fix},
              f"helm {fix}"),
        _step(21, "Observation: unit drop-in.",
              "read_file", {"path": f"{work}/systemd/override.conf"}, bad),
        _step(22, "Observation: pin unit.",
              "search_replace",
              {"path": f"{work}/systemd/override.conf", "old": bad, "new": fix},
              f"unit {fix}"),
        _step(23, "Observation: env example.",
              "read_file", {"path": f"{work}/.env.example"}, bad),
        _step(24, "Observation: pin env example.",
              "search_replace", {"path": f"{work}/.env.example", "old": bad, "new": fix},
              f".env.example {fix}"),
        _step(25, "Observation: docs.",
              "search_replace",
              {"path": f"{work}/README.md", "old": plant["wrong"], "new": fix},
              "docs invoice"),
        _step(26, "Observation: CI matrix.",
              "read_file", {"path": f"{work}/.github/workflows/gate.yml"},
              f"runs pytest {test}"),
        _step(27, "Observation: confirm no mid-step reward.",
              "grep", {"pattern": '"reward"', "path": f"{work}/{test}"},
              "no reward key in gate"),
        _step(28, "Observation: second pytest.",
              "bash", {"command": f"pytest -q {test}"},
              "1 passed; live still flaky once"),
        _step(29, "Observation: replay canary.",
              "bash", {"command": f"grep -n {fix!r} {work}/canary/runtime.conf"},
              f"canary {fix}"),
        _step(30, "Observation: replay worker.",
              "bash", {"command": f"grep -n {fix!r} {work}/worker/runtime.conf"},
              f"worker {fix}"),
        _step(31, "Observation: final pytest.",
              "bash", {"command": f"pytest -q {test}"},
              "2 passed app+worker+canary+live"),
        _step(32, "Observation: close invoice.",
              "write",
              {"path": f"{work}/{issue}", "contents": f"FIXED leftover leftover leftover {fix}"},
              f"invoice closed; {fix}"),
    ]


def episode(rnd: int, plant: cat.Plant) -> dict[str, Any]:
    """One designed episode. Raises ``SrlError`` if the payload is unclean."""

    rnd = require_round(rnd)
    slug = plant["slug"]
    test = f"tests/{plant['test']}.py"
    h1, h2, fix = plant["h1"], plant["h2"], plant["fix"]
    steps = _steps(plant)
    if len(steps) != N_STEPS:
        raise SrlError(f"horizon_mismatch: {len(steps)} != {N_STEPS}")
    rec = {
        "id": record_id(rnd, slug),
        "goal": (
            f"{plant['plant']} {plant['tool']} vs {plant['vs']}. "
            f"Make {test} pass: {fix} on app+worker+canary. {h1} and {h2} are not the fix. "
            "Non-signal CLI is not credit."
        ),
        "plan": f"Abandon H1 ({h1}) and H2 ({h2}). Apply {fix} on app, worker, canary, and live.",
        "steps": steps,
        "outcome": (
            f"Abandoned H1 ({h1}) and H2 ({h2}). {fix} on app+worker+canary+live. "
            "Final pytest: 2/2. Non-signal is observation only."
        ),
        "reward": {
            "success": True,
            "terminal_only": True,
            "horizon_steps": N_STEPS,
            "mid_reward_steps": 0,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "plant": "designed",
        },
    }
    blob = dumps_exact_json(rec)
    for banned in BANNED:
        if banned in blob:
            raise SrlError(f"banned: {banned}")
    if any("reward" in step for step in rec["steps"]):
        raise SrlError("step_reward")
    return rec


def notes(rnd: int, plant: cat.Plant) -> str:
    rnd = require_round(rnd)
    theme = "/".join(THEME_TOOLS)
    return (
        f"# {FACTORY} — NOTES r{rnd}\n\n"
        f"Novel coverage: {NOVEL_COVERAGE}\n\n"
        f"## Record\n"
        f"- id: `{record_id(rnd, plant['slug'])}` · steps {N_STEPS} · "
        f"terminal only · {GEN}\n\n"
        f"## Seed\n"
        f"{plant['tool']} vs {plant['vs']}. Dead-ends: H1 {plant['h1']}, "
        f"H2 {plant['h2']}.\n\n"
        f"## Sparse-reward texture\n"
        f"No `reward` on steps. Intermediate pytest/cli lines are observations.\n\n"
        f"## Abandoned / pivot\n"
        f"- step 6: H1 abandoned\n"
        f"- step 8: H2 abandoned\n\n"
        f"why this is hard: two plausible wrong knobs, worker/canary/live, "
        f"non-signal CLI is not credit.\n\n"
        f"## Terminal\n"
        f"- success=true · surface fixed.\n\n"
        f"## Novel pack\n"
        f"- Theme: {theme} forks.\n"
        f"- BAN: nginx client_max_body, gRPC 8MiB, PG idle-in-xact, "
        f"r5969 timesyncd, kubelet topology/cpu/memory clones, "
        f"used IPv6AcceptRA/default_lease/kpr-probe.\n"
    )


def generate_window(
    start_round: int = SOURCE_ROUND,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """One episode per plant, rounds ``start_round`` .. ``start_round + count - 1``."""

    start_round = require_round(start_round)
    if count is None:
        count = len(cat.PLANTS)
    if type(count) is not int or not 1 <= count <= len(cat.PLANTS):
        raise SrlError(f"invalid_count: {count!r}")
    return [episode(start_round + index, cat.plant_at(index)) for index in range(count)]
