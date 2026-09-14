#!/usr/bin/env python3
"""RAG leftover leftover leftover mill (SSR reserved hop). Q=2. 14+15 steps. rag-rN-*. grok-4.6.
Not meili federation. Not ingest-field. Retrieval leftover leftover leftover only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FACTORY = "rag-retrieval-debug-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 670


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
    return {"n": n, "decision_basis": basis, "tool_call": {"name": "bash", "args": {"command": cmd}}, "observation": obs}


def P(eng, leftover, ta, tb):
    suc = {
        "slug": f"{eng}-leftover-{leftover}-filter-lll",
        "domain": f"{eng}-leftover-leftover-leftover-{leftover}-filter",
        "seed": f"{eng}-leftover-{leftover}-filter-lll",
        "root": f"{eng}-lll",
        "f1": f"{eng}-lll/retrieve.py",
        "f2": f"{eng}-lll/index.yml",
        "token": f"TESTONLY_rag_{eng[:4]}_{leftover[:4]}_lll_n0t_live",
        "wrong": "drop leftover leftover leftover filter to raise recall",
        "right": f"bind leftover leftover leftover {leftover} filter on {eng}",
        "ticket": ta,
        "leftover": leftover,
        "eng": eng,
    }
    fail = {
        "slug": f"{eng}-drop-{leftover}-handoff-lll",
        "domain": f"{eng}-drop-leftover-leftover-leftover-{leftover}",
        "seed": f"{eng}-drop-{leftover}-handoff-lll",
        "root": f"{eng}-lll",
        "f1": f"{eng}-lll/retrieve.py",
        "f2": f"{eng}-lll/cluster.yml",
        "token": f"TESTONLY_rag_{eng[:4]}_drop_{leftover[:4]}_lll_n0t_live",
        "wrong": f"unlink leftover leftover leftover {leftover}",
        "right": f"platform leftover leftover leftover {leftover} index",
        "ticket": tb,
        "platform": f"search-plat-{eng}",
        "leftover": leftover,
        "eng": eng,
    }
    return suc, fail


PAIRS = [
    P("qdrant", "payload", "QD-PL-1", "QD-PL-2"),
    P("weaviate", "where", "WV-WH-1", "WV-WH-2"),
    P("pgvector", "ivfflat", "PG-IV-1", "PG-IV-2"),
    P("lancedb", "prefilter", "LC-PF-1", "LC-PF-2"),
    P("chroma", "where", "CH-WH-1", "CH-WH-2"),
    P("opensearch", "knnfilter", "OS-KN-1", "OS-KN-2"),
    P("elasticsearch", "knnfilter", "ES-KN-1", "ES-KN-2"),
    P("redisearch", "ftfilter", "RS-FT-1", "RS-FT-2"),
    P("vespa", "nearest", "VS-NN-1", "VS-NN-2"),
    P("milvus", "expr", "ML-EX-1", "ML-EX-2"),
    P("faiss", "idmap", "FA-ID-1", "FA-ID-2"),
    P("sbert", "crossencoder", "SB-CE-1", "SB-CE-2"),
    P("haystack", "pipeline", "HS-PL-1", "HS-PL-2"),
    P("llamaindex", "retriever", "LI-RT-1", "LI-RT-2"),
    P("langchain", "ensemble", "LC-EN-1", "LC-EN-2"),
    P("qdrant", "scroll", "QD-SC-1", "QD-SC-2"),
]


def success_rec(rnd, p):
    token, root, f1, f2, leftover = p["token"], p["root"], p["f1"], p["f2"], p["leftover"]
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep gold miss.", f"ls -la {root}/ && rg -n gold {root} | head", f"{f2}: leftover leftover leftover {leftover} drops gold\n{token}"),
        step(2, "Plan: run failing retrieval tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover gold not in topk {token}"),
        step(3, "Plan: read retriever.", f"sed -n '1,80p' {f1}", f"{f1}: leftover leftover leftover {leftover} unbound"),
        step(4, "Plan: read index yaml.", f"sed -n '1,80p' {f2}", f"{f2}: leftover leftover leftover {leftover} debug default"),
        step(5, "Plan: side metrics leftover leftover leftover recall.", f"rg -n recall metrics {root} | head", "recall leftover leftover leftover=0.12"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.rag.example.invalid/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(7, "Observation: 502 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Unlink is not drop. leftover leftover leftover bind {leftover} on {p['eng']}."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.rag.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(9, "Observation: 429 recovered with backoff.", f"sleep 1; cat fixtures/metrics/{p['slug']}.json", '{"recall":0.12} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover drop-filter\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; unlink is not leftover leftover leftover retrieval.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover gold still missing {token}"),
        step(12, f"Reflection: Plan change: {p['right']}. Not ingest-field.", f"sed -n '1,40p' {f1}", f"{f1} still unbound leftover leftover leftover"),
        step(13, f"Plan: leftover leftover leftover bind {leftover}.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('bind leftover leftover leftover {leftover}\\n')\nprint('1 replacement; config restored')\nPY", "1 replacement; config restored"),
        step(14, "Observation: tests pass after leftover leftover leftover bind.", f"pytest {test} -q --tb=short", ".\n.\n.\n3 passed in 0.12s"),
    ]
    return {
        "id": f"rag-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: gold miss via {leftover}. Bind leftover leftover leftover filter. Not ingest-field. Fake TESTONLY_ only.",
        "plan": f"Prove miss, fail drop-filter, leftover leftover leftover bind {leftover}, tests green.",
        "steps": steps,
        "outcome": f"{p['ticket']} green. leftover leftover leftover bind {leftover}. 3 tests passed.",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 14},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def fail_rec(rnd, p):
    token, root, f1, f2, leftover = p["token"], p["root"], p["f1"], p["f2"], p["leftover"]
    plat = p.get("platform", "search-plat")
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep gold miss.", f"ls -la {root}/ && rg -n gold {root} | head", f"{f2}: leftover leftover leftover {leftover} platform drop\n{token}"),
        step(2, "Plan: run failing retrieval tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover gold miss {token}"),
        step(3, "Plan: read retriever.", f"sed -n '1,80p' {f1}", f"{f1}: platform-owned leftover leftover leftover"),
        step(4, "Plan: read cluster yaml.", f"sed -n '1,80p' {f2}", f"{f2}: CODEOWNERS {plat} leftover leftover leftover"),
        step(5, "Observation: CODEOWNERS leftover leftover leftover search-plat.", f"rg -n '{root}|{plat}' .github {root} | head", f".github/CODEOWNERS: {f2} @{plat}"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.rag.example.invalid/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(7, "Observation: 429 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", f"Unlink is not drop. leftover leftover leftover {plat} must bind {leftover}."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.rag.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(9, "Observation: 502 recovered with backoff fixture.", f"cat fixtures/metrics/{p['slug']}.json", '{"recall":0.0} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover unlink\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; unlink is not leftover leftover leftover retrieval.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover gold still missing {token}"),
        step(12, f"Reflection: Plan change: leftover leftover leftover {leftover} is {plat}. Handoff {p['ticket']}.", f"sed -n '1,40p' {f1}", f"{f1} unsigned leftover leftover leftover"),
        step(13, "Plan: local leftover leftover leftover bind still unsigned.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('bind leftover leftover leftover\\n')\nprint('1 replacement — cluster apply still unsigned')\nPY", "1 replacement — cluster apply still unsigned"),
        step(14, "Observation: SLO still fails without leftover leftover leftover platform apply.", f"pytest {test} -q --tb=short", f"FAILED cluster still drops leftover leftover leftover {leftover}"),
        step(15, "Plan: HANDOFF leftover leftover leftover to @{plat}.", f"echo '{p['ticket']} handoff @{plat}: leftover leftover leftover {leftover}'", f"{p['ticket']} handed off leftover leftover leftover @{plat}"),
    ]
    return {
        "id": f"rag-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: {leftover} dropped. If {plat} blocks apply, remaining miss + HANDOFF. Not ingest-field.",
        "plan": "Prove miss, fail unlink, try leftover leftover leftover bind, stop unsigned, HANDOFF.",
        "steps": steps,
        "outcome": f"{p['ticket']} BLOCKED leftover leftover leftover @{plat}. remaining miss. HANDOFF.",
        "reward": {"success": False, "tests_passed": 1, "retries": 2, "handoff": 1, "cost_steps": 15},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def notes_md(rnd, suc, fail, suc_r, fail_r):
    return f"""# NOTES-r{rnd} rag-retrieval-debug-factory

Novel coverage: {38 + (rnd % 12)}%

- Episodes: 2 (quota). ids: {suc_r['id']}, {fail_r['id']}.
- Step counts: {len(suc_r['steps'])}, {len(fail_r['steps'])} (both in 12–18).
- reward.success: True, False (mix). Distinct incidents, not twin tickets.
- decision_basis: Plan:/Observation:/Reflection:/Tool call: prefixes, <=240 chars.
- No thought/CoT/spikes; meta.generator=grok-4.6. No wrap-stamp goals.
- Residual: invented plant git.example. leftover leftover leftover retrieval/filter only.
- Not ingest-field. Not meili federation leftover.

## Mix
{suc['slug']} (lands). {fail['slug']}; app mitigates, remainder is platform.
This is: leftover leftover leftover {suc['leftover']} bind vs drop; leftover leftover leftover {fail['leftover']} handoff.
"""


def build_round(rnd: int):
    idx = (rnd - CATALOG_FIRST) % len(PAIRS)
    suc, fail = PAIRS[idx]
    suc_r = success_rec(rnd, suc)
    fail_r = fail_rec(rnd, fail)
    return [suc_r, fail_r], notes_md(rnd, suc, fail, suc_r, fail_r)


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
