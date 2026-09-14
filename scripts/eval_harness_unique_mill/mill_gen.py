#!/usr/bin/env python3
"""Emit unique eval-harness leftover episodes (16-step success + partial)."""

from __future__ import annotations

import json
from typing import Any

FACTORY = "eval-harness-trajectory-factory"
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")
BANNED_SNIPPETS = (
    "SKU-9",
    "combining mark",
    "U+0300",
    "U+1D17",
    "U+2022",
    "U+2027",
    "14-day",
    "14‧day",
    "skip-as-1.0",
    "numpy.bool_",
    "pytest-xdist",
    "LiteLLM fallback",
    "json_mode",
    "latest_test_run",
    "vcr",
    "VCR",
    "mlflow",
    "MLflow",
    "Langfuse",
    "Int8",
    "CancelOrderRequest",
    "Cohere rerank",
    "semantic cache",
    "helm",
    "Helm",
    "sample_rate",
    "CONFIDENT_SAMPLE_RATE",
    "black wrap",
    "isort",
    "pytest-randomly",
    "httpx.Timeout",
    "ansible",
    "Ansible",
    "pulumi",
    "Pulumi",
)

DEEPEVAL_CITE = (
    "DeepEval metrics expose measure/is_successful/threshold; caches and "
    "exporters are caller-owned. Fail closed on errors. Do not treat missing "
    "scores as pass. evaluation_params must match the fields the rubric uses."
)


def _step(n: int, decision_basis: str, tool_call: dict, observation: str, **extra) -> dict:
    db = decision_basis.strip()
    if not db.startswith(DB_PREFIXES):
        raise ValueError(f"step {n} decision_basis prefix: {db[:80]!r}")
    if len(db) > 240:
        raise ValueError(f"step {n} decision_basis {len(db)} > 240: {db}")
    if not observation or not str(observation).strip():
        raise ValueError(f"step {n} empty observation")
    out = {
        "n": n,
        "decision_basis": db,
        "tool_call": tool_call,
        "observation": observation,
    }
    out.update(extra)
    return out


def _bash(command: str) -> dict:
    return {"name": "bash", "args": {"command": command}}


def _read(path: str) -> dict:
    return {"name": "read", "args": {"path": path}}


def _edit(path: str, old: str, new: str) -> dict:
    return {"name": "edit", "args": {"path": path, "old": old, "new": new}}


def _grep(path: str, pattern: str) -> dict:
    return {"name": "grep", "args": {"path": path, "pattern": pattern}}


def dumps_episode(ep: dict) -> str:
    return json.dumps(ep, ensure_ascii=True, separators=(",", ":"))


def assert_clean(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        lowered = obj.lower()
        for snippet in BANNED_SNIPPETS:
            if snippet.startswith("U+") or "‧" in snippet:
                if snippet in obj:
                    raise ValueError(f"banned leftover snippet {snippet!r} at {path}")
            elif snippet.lower() in lowered:
                raise ValueError(f"banned leftover snippet {snippet!r} at {path}")


def _eid(round_n: int, slug: str) -> str:
    return f"evh-r{round_n}-{slug}"


def _steps(p: dict) -> list:
    src = p["src"]
    test = p["test"]
    run = p["run"]
    steps = [
        _step(
            1,
            "Plan: read the ticket and constraints before touching metrics.",
            _read("TICKET.md"),
            p["ticket"],
        ),
        _step(
            2,
            f"Observation: ticket names {src}. Read the harness.",
            _read(src),
            p["src_obs"],
        ),
        _step(
            3,
            "Observation: run the eval to reproduce the lie or fail.",
            _bash(f"pytest {run} -q --tb=line 2>&1 | tail -n 20"),
            p["fail_obs"],
        ),
        _step(
            4,
            f"Observation: inspect {p['inspect']} for the leftover protocol bug.",
            _read(p["inspect"]),
            p["inspect_obs"],
        ),
        _step(
            5,
            "Observation: try the first fix (likely incomplete).",
            _edit(p["first_path"], p["first_old"], p["first_new"]),
            p["first_obs"],
        ),
        _step(
            6,
            "Observation: re-run; expect a 429 from the judge path.",
            _bash(f"pytest {run} -q --tb=line 2>&1 | tail -n 12"),
            "openai.RateLimitError: Error code: 429 Retry-After: 8\n" + p["rate_tail"],
        ),
        _step(
            7,
            "Observation: 429. Retry after Retry-After.",
            _bash(f"sleep 8 && pytest {run} -q --tb=line 2>&1 | tail -n 16"),
            "429 cleared after Retry-After: 8. leftover still: " + p["still_after_429"],
        ),
        _step(
            8,
            "Observation: first fix did not restore a fail-closed gate. Dig.",
            _grep(".", p["grep"]),
            p["grep_obs"],
        ),
        _step(
            9,
            f"Reflection: Plan change — {p['plan_change']}",
            _read("https://github.com/confident-ai/deepeval"),
            DEEPEVAL_CITE,
            reflection="Plan change recorded. Implement the pivot, not a threshold bump.",
        ),
        _step(
            10,
            "Reflection: apply the plan-change edit.",
            _edit(p["fix_path"], p["fix_old"], p["fix_new"]),
            p["fix_obs"],
        ),
        _step(
            11,
            "Observation: re-run; expect a 502 then a real score.",
            _bash(f"pytest {run} -q --tb=short 2>&1 | tail -n 16"),
            "openai.APIError: Error code: 502 - Bad Gateway from api.openai.com/v1/chat/completions",
        ),
        _step(
            12,
            "Observation: 502. Retry the discriminating run.",
            _bash(f"pytest {run} -q --tb=line 2>&1 | tail -n 18"),
            p["retry_obs"],
        ),
        _step(
            13,
            "Observation: lock a regression that documents the protocol, not the number.",
            _edit(test, "", p["test_body"]),
            p["test_obs"],
        ),
        _step(
            14,
            "Observation: run gold vs planted together.",
            _bash("pytest evals/ tests/ -q --tb=no 2>&1 | tail -n 12"),
            p["suite_obs"],
        ),
        _step(
            15,
            "Observation: full suite / gate output.",
            _bash(f"deepeval test run {run} -v 2>&1 | tail -n 14"),
            p["gate_obs"],
        ),
        _step(
            16,
            "Observation: diff should be harness/protocol, not a loosened threshold.",
            _bash("git diff --stat"),
            p["diff_obs"] + "\nresidual: " + p["residual"],
            reflection=p["residual"],
        ),
    ]
    return steps


def build_episode(round_n: int, p: dict) -> dict:
    eid = _eid(round_n, p["slug"])
    success = bool(p["success"])
    steps = _steps(p)
    for step in steps:
        if len(step["decision_basis"]) > 240:
            raise ValueError(f"{eid} step {step['n']} db too long")
    ep = {
        "id": eid,
        "goal": p["goal"],
        "plan": p["plan"],
        "steps": steps,
        "outcome": p["outcome"],
        "reward": {
            "success": success,
            "cost_steps": 16,
            "tests_passed": p["tests_passed"],
            "tests_failed_as_designed": p["tests_failed_as_designed"],
            "http_429": 1,
            "http_502": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": round_n,
            "generator": GENERATOR,
            "domain": p["domain"],
            "designed": True,
        },
    }
    assert_clean(ep)
    if len(steps) != 16:
        raise ValueError(f"{eid} expected 16 steps, got {len(steps)}")
    text = json.dumps(ep)
    if "429" not in text or "502" not in text:
        raise ValueError(f"{eid} missing 429/502")
    return ep


def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
    return (
        f"# NOTES-r{round_n} eval-harness-trajectory-factory\n"
        "\n"
        f"Novel coverage: {coverage}%\n"
        "\n"
        "Unique eval-harness leftover plants (not unicode leftover mill, not r50–r252\n"
        "catalog clones, not r253–r293 eval-infra clones, not r294–r319 CI/judge/\n"
        "metric/trace/fmt/cache cartesian, not Faithfulness empty-ctx /\n"
        "ConversationalGEval last-turn / GEval temperature-seed leftover, not\n"
        "RAGAS/promptfoo/LangSmith/Braintrust/LlamaIndex leftover catalogs).\n"
        "Kind=episode. Q=2. generator=grok-4.6. 16 steps each. 429×1 502×1.\n"
        "One mid-trajectory plan change. success + partial. ids evh-rN-<slug>.\n"
        "\n"
        f"- `{_eid(round_n, ok['slug'])}` steps=16 success=True domain={ok['domain']} "
        f"429x1 502x1 plan_change_step=9\n"
        f"  outcome: {ok['outcome']}\n"
        f"  avoided: {ok['avoided']}\n"
        "\n"
        f"- `{_eid(round_n, bad['slug'])}` steps=16 success=False domain={bad['domain']} "
        f"429x1 502x1 plan_change_step=9\n"
        f"  outcome: {bad['outcome']}\n"
        f"  avoided: {bad['avoided']}\n"
        "\n"
        "Bans observed: no thought keys, no spike_events, no sim_or_real=real, designed traces.\n"
        "Residual synthetic tell: observations are curated excerpts, not live judge logs.\n"
    )


def validate_pair(ok_ep: dict, bad_ep: dict, round_n: int) -> None:
    if ok_ep["reward"]["success"] is not True:
        raise ValueError("ok episode must succeed")
    if bad_ep["reward"]["success"] is not False:
        raise ValueError("partial episode must fail")
    if ok_ep["meta"]["round"] != round_n or bad_ep["meta"]["round"] != round_n:
        raise ValueError("round mismatch")
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate ids in pair")
    if not ok_ep["id"].startswith(f"evh-r{round_n}-"):
        raise ValueError(ok_ep["id"])
    if not bad_ep["id"].startswith(f"evh-r{round_n}-"):
        raise ValueError(bad_ep["id"])
    for ep in (ok_ep, bad_ep):
        if len(ep["steps"]) != 16:
            raise ValueError(f"{ep['id']} not 16 steps")
        if any(k in ep for k in BANNED_KEYS):
            raise ValueError(f"{ep['id']} banned top-level key")
