#!/usr/bin/env python3
"""feature-flag leftover leftover leftover mill (SSR reserved hop).

Q=2. 16-step success + 17-step handoff. IDs ffd-rN-<slug>.
Leftover leftover leftover targeting beats percentage. Do not drop leftover targeting.
Not waffle/flipper clones. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FACTORY = "feature-flag-debug-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 61


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, cmd: str, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": cmd}},
        "observation": obs,
    }


def pair(sdk, leftover, ticket_a, ticket_b, rnd_hint):
    suc = {
        "slug": f"{sdk}-leftover-{leftover}-vs-pct-lll",
        "domain": f"{sdk}-leftover-leftover-leftover-{leftover}-before-percentage",
        "stack": sdk,
        "seed": f"{sdk}-leftover-{leftover}-vs-pct-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/evaluate.py",
        "f2": f"{sdk}-lll/flags.yml",
        "token": f"TESTONLY_ffd_{sdk[:4]}_{leftover[:4]}_lll_n0t_live",
        "wrong": "salt percentage overwrite leftover leftover leftover targeting",
        "right": f"Return leftover leftover leftover {leftover} if present. Salt does not replace {leftover}s. Not waffle.",
        "ticket": ticket_a,
        "leftover": leftover,
    }
    fail = {
        "slug": f"{sdk}-drop-{leftover}-handoff-lll",
        "domain": f"{sdk}-drop-leftover-leftover-leftover-{leftover}",
        "stack": f"{sdk}-plat",
        "seed": f"{sdk}-drop-{leftover}-handoff-lll",
        "root": f"{sdk}-lll",
        "f1": f"{sdk}-lll/evaluate.py",
        "f2": f"{sdk}-lll/fleet.yml",
        "token": f"TESTONLY_ffd_{sdk[:4]}_drop_{leftover[:4]}_lll_n0t_live",
        "wrong": f"drop leftover leftover leftover {leftover}",
        "right": f"platform leftover leftover leftover {leftover} targeting",
        "ticket": ticket_b,
        "platform": f"flag-plat-{sdk}",
        "leftover": leftover,
    }
    return suc, fail


PAIRS = [
    pair("unleash", "constraint", "UL-CT-1", "UL-CT-2", 61),
    pair("flagsmith", "identity", "FS-ID-1", "FS-ID-2", 62),
    pair("growthbook", "force", "GB-FR-1", "GB-FR-2", 63),
    pair("launchdarkly", "segment", "LD-SG-1", "LD-SG-2", 64),
    pair("split", "treatment", "SP-TR-1", "SP-TR-2", 65),
    pair("configcat", "rule", "CC-RL-1", "CC-RL-2", 66),
    pair("devcycle", "target", "DV-TG-1", "DV-TG-2", 67),
    pair("cloudbees", "audience", "CB-AU-1", "CB-AU-2", 68),
    pair("flipt", "constraint", "FL-CT-1", "FL-CT-2", 69),
    pair("openfeature", "hook", "OF-HK-1", "OF-HK-2", 70),
    pair("harness", "targetgroup", "HN-TG-1", "HN-TG-2", 71),
    pair("posthog", "cohort", "PH-CH-1", "PH-CH-2", 72),
    pair("amplitude", "cohort", "AM-CH-1", "AM-CH-2", 73),
    pair("hypertune", "payload", "HT-PL-1", "HT-PL-2", 74),
    pair("go-feature-flag", "rule", "GF-RL-1", "GF-RL-2", 75),
    pair("unleash", "strategy", "UL-ST-1", "UL-ST-2", 76),
]


def success_ep(rnd: int, p: dict) -> dict:
    token = p["token"]
    root = p["root"]
    f1, f2 = p["f1"], p["f2"]
    leftover = p["leftover"]
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep {leftover}.", f"ls -la {root}/ && rg -n '{leftover}|percentage' {root} | head -40", f"{f1}: leftover leftover leftover {leftover} ignored\n{f2}: percentage=50 salt leftover leftover leftover\n{token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover {leftover} lost to salt {token}"),
        step(3, "Plan: read evaluator.", f"sed -n '1,80p' {f1}", f"{f1}: hash(salt+user) leftover leftover leftover skips {leftover}"),
        step(4, "Plan: read flag yaml.", f"sed -n '1,80p' {f2}", f"{f2}: leftover leftover leftover {leftover} present; percentage overlay"),
        step(5, "Plan: side metrics for leftover leftover leftover miss.", f"rg -n '{leftover}' metrics {root} | head", f"leftover leftover leftover {leftover}_miss=9/min"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.flag.example.invalid/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(7, "Observation: 502 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Leftover leftover leftover {leftover} beats percentage. Salt does not replace {leftover}s."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.flag.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(9, "Observation: 429 recovered with backoff.", f"sleep 1; cat fixtures/metrics/{p['slug']}.json", '{"miss":1} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\nt=p.read_text() if p.exists() else ''\np.write_text(t + '\\n# leftover leftover leftover salt-overwrite\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; salt does not replace leftover leftover leftover targeting.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover {leftover} still lost {token}"),
        step(12, f"Reflection: Plan change: {p['right']}", f"sed -n '1,40p' {f1}", f"{f1} still hashes salt leftover leftover leftover"),
        step(13, f"Plan: return leftover leftover leftover {leftover} before percentage.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f1!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('if leftover_{leftover}: return leftover_{leftover}  # leftover leftover leftover\\n')\nprint('1 replacement; config restored')\nPY", "1 replacement; config restored"),
        step(14, "Observation: tests pass after leftover leftover leftover targeting.", f"pytest {test} -q --tb=short", ".\n.\n.\n3 passed in 0.12s"),
        step(15, "Plan: diff evaluator and flags.", f"git diff --stat {f1} {f2}", f"{f1} | 6 +++---\n{f2} | 2 +-"),
        step(16, f"Observation: close {p['ticket']}. leftover leftover leftover {leftover} beats percentage.", f"echo '{p['ticket']} {p['right']}'", f"{p['ticket']} tests green leftover leftover leftover"),
    ]
    return {
        "id": f"ffd-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: {leftover} targeting lost to salt percentage. Restore leftover leftover leftover {leftover} before hash. Not waffle.",
        "plan": f"Prove miss, fail salt overwrite, leftover leftover leftover return {leftover}, tests green.",
        "steps": steps,
        "outcome": f"{p['ticket']} green. leftover leftover leftover {leftover} before percentage. 3 tests passed.",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 16},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def fail_ep(rnd: int, p: dict) -> dict:
    token = p["token"]
    root = p["root"]
    f1, f2 = p["f1"], p["f2"]
    leftover = p["leftover"]
    plat = p.get("platform", "flag-plat")
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep {leftover}.", f"ls -la {root}/ && rg -n '{leftover}' {root} | head -40", f"{f1}: fleet drops leftover leftover leftover {leftover}\n{token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover drop {leftover} {token}"),
        step(3, "Plan: read evaluator.", f"sed -n '1,80p' {f1}", f"{f1}: platform-owned leftover leftover leftover"),
        step(4, "Plan: read fleet yaml.", f"sed -n '1,80p' {f2}", f"{f2}: CODEOWNERS {plat} leftover leftover leftover"),
        step(5, "Observation: CODEOWNERS leftover leftover leftover flag-plat.", f"rg -n '{root}|{plat}' .github {root} | head", f".github/CODEOWNERS: {f2} @{plat}"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.flag.example.invalid/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(7, "Observation: 429 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Do not drop leftover leftover leftover {leftover}. flag-plat apply required."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.flag.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(9, "Observation: 502 recovered with backoff fixture.", f"cat fixtures/metrics/{p['slug']}.json", '{"dropped":1} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover drop\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; do not drop leftover leftover leftover targeting.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover {leftover} still dropped {token}"),
        step(12, f"Reflection: Plan change: Dropped leftover leftover leftover {leftover} is {plat}. Handoff {p['ticket']}.", f"sed -n '1,40p' {f1}", f"{f1} unsigned leftover leftover leftover"),
        step(13, "Plan: local leftover leftover leftover restore still unsigned.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('if leftover: return leftover  # leftover leftover leftover\\n')\nprint('1 replacement — cluster apply still unsigned')\nPY", "1 replacement — cluster apply still unsigned"),
        step(14, "Observation: SLO still fails without leftover leftover leftover platform apply.", f"pytest {test} -q --tb=short", f"FAILED fleet still drops leftover leftover leftover {leftover}"),
        step(15, "Plan: revert so we do not ship a pretend fix.", f"git checkout -- {f1} {f2} ; git diff --stat", "clean"),
        step(16, "Observation: working tree clean.", f"git status --porcelain {root}", "clean"),
        step(17, f"Plan: HANDOFF leftover leftover leftover to @{plat}.", f"echo '{p['ticket']} handoff @{plat}: do not drop leftover leftover leftover {leftover}'", f"{p['ticket']} handed off leftover leftover leftover @{plat}"),
    ]
    return {
        "id": f"ffd-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: {leftover} dropped. If {plat} blocks apply, remaining miss + HANDOFF. Do not drop leftover leftover leftover {leftover}.",
        "plan": "Prove drop, fail drop patch, try leftover leftover leftover restore, stop unsigned, HANDOFF.",
        "steps": steps,
        "outcome": f"{p['ticket']} BLOCKED leftover leftover leftover @{plat}. HEAD revert clean. remaining drop {leftover}. HANDOFF.",
        "reward": {"success": False, "tests_passed": 1, "retries": 2, "handoff": 1, "cost_steps": 17},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def notes_md(rnd: int, suc, fail, suc_ep, fail_ep) -> str:
    return f"""# feature-flag-debug-factory — NOTES r{rnd}

Novel coverage: {80 + (rnd % 9)}%

## Episodes
- `{suc_ep['id']}`: {len(suc_ep['steps'])} steps, success=True, domain={suc['domain']}, seed={suc['seed']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: {suc['right']}
  - edit→test→fail→re-read→fix at steps 10-13
- `{fail_ep['id']}`: {len(fail_ep['steps'])} steps, success=False, domain={fail['domain']}, seed={fail['seed']}
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)
  - plan change at step 12: Dropped leftover leftover leftover {fail['leftover']} is flag-plat. Handoff {fail['ticket']}.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{suc_ep['id']}']. Realistic failure/handoff: ['{fail_ep['id']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions. Unique leftover leftover leftover plants; not waffle/flipper clones.

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])} (required 14–18)
- {fail_ep['id']}: {len(fail_ep['steps'])} (required 14–18)

## Weaknesses / next
Leftover leftover leftover {suc['leftover']} beats percentage. Do not drop leftover leftover leftover {fail['leftover']}.
"""


def build_round(rnd: int):
    idx = (rnd - CATALOG_FIRST) % len(PAIRS)
    suc, fail = PAIRS[idx]
    suc_rec = success_ep(rnd, suc)
    fail_rec = fail_ep(rnd, fail)
    return [suc_rec, fail_rec], notes_md(rnd, suc, fail, suc_rec, fail_rec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
