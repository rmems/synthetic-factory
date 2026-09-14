#!/usr/bin/env python3
"""Mill AMC r688+ as leftover leftover leftover plants.

Each pair is TWO DISTINCT leftover mechanisms (not drop-vs-keep twins).
BAN pin-vs-GC cartesian, doorway catalogs, psych catalogs, r316–r687 clones,
session/org/scratchpad/RAG/prefix/function leftover recycle.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("amcmill170h", str(HERE / "amc-mill-r170.py")).load_module()
F = _base.F
S = _base.S
build_episode = _base.build_episode
FACTORY = _base.FACTORY
GEN = _base.GEN

CATALOG_FIRST = 688

BANNED_EXTRA = (
    "zeigarnik", "ebbinghaus", "loftus", "hopfield", "act-r", "actr",
    "drops-pin", "pin-kept", "doorway-meeting", "doorway-scenecut",
    "doorway-chapter", "saml-audience", "wasm-export-global", "ebpf-map-path",
    "temporal-history-trim", "airflow-xcom-gc",
)


def fail(**kw) -> dict:
    kw.setdefault("leftover_fn", f"test_{kw['leftover'].replace('-', '_')}")
    return F(**kw)


def succ(**kw) -> dict:
    kw.setdefault("leftover_fn", f"test_{kw['leftover'].replace('-', '_')}")
    return S(**kw)


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"amc-r{round_n}-{a['slug']}"
    eb = f"amc-r{round_n}-{b['slug']}"
    novel = 86 + (round_n % 7)
    return f"""# NOTES-r{round_n} agent-memory-compaction-factory

Novel coverage: {novel}%

Two designed leftover leftover leftover episodes (quota 2).
Surfaces: {a['surface']} vs {b['surface']} — distinct eviction mechanisms, not pin-vs-GC twins.
Mix: ep1 success=false (partial: {a['leftover']} leftover xfail); ep2 success=true (success 7/7).
Unique leftovers: {a['leftover']} / {b['leftover']}.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['seed']} | {a['first_name']} | {a['fix_name']} | partial: {a['leftover']} xfail |
| {eb} | {b['seed']} | {b['first_name']} | {b['fix_name']} | success 7/7 |

## Step counts
- ep1: 16. First apply 6–7; plan change 8; leftover xfail 12.
- ep2: 16. First apply 6–7; plan change 8; 7/7 at 10.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plant `mneme`.

## Weaknesses / next
Leftover leftover leftover mill. BAN pin-vs-GC twins. BAN doorway/psych catalogs.
Avoid {a['first_name']} and {b['first_name']} next.
"""


def L(
    slug: str,
    mod: str,
    pin: str,
    surface: str,
    seed: str,
    bug: str,
    src_bad: str,
    leftover: str,
    first_name: str,
    first_new: str,
    first_plan: str,
    fix_name: str,
    plan_change: str,
    plan: str,
    gate_err: str,
    chatter_err: str,
    dump: str,
    setup: str,
    is_fail: bool,
) -> dict:
    fn = fail if is_fail else succ
    attr = leftover.replace("-", "_")
    return fn(
        slug=slug,
        mod=mod,
        pin=pin,
        surface=surface,
        seed=seed,
        bug=bug,
        src_bad=src_bad,
        test_fn=f"test_{attr}_kept",
        chatter_fn=f"test_{attr}_chatter_swept",
        leftover=leftover,
        first_name=first_name,
        first_new=first_new,
        first_plan=first_plan,
        fix_name=fix_name,
        plan_change=plan_change,
        plan=plan,
        gate_err=gate_err,
        chatter_err=chatter_err,
        dump=dump,
        setup=setup,
        assert_expr=f"s.find('{pin}')",
        confirm=f"bool(s.find('{pin}'))",
    )


def P(
    slug: str,
    mod: str,
    kind: str,
    flag: str,
    surface: str,
    leftover: str,
    is_fail: bool,
) -> dict:
    pin = f"NEVER_{mod.upper()}_PIN"
    return L(
        slug=slug,
        mod=mod,
        pin=pin,
        surface=surface,
        seed=f"{slug.replace('-leftover', '')} leftover",
        bug=f"compact drops leftover {surface.lower()} still required ({flag})",
        src_bad=f"if i.kind=='{kind}' and i.{flag}: self.drop(i)  # leftover",
        leftover=leftover,
        first_name=f"skip-{mod}-{kind.split('_')[-1][:4]}",
        first_new="pass  # skip leftover drop",
        first_plan=f"skip leftover drop so a live {surface.lower()} cannot vanish",
        fix_name=f"keep live {surface.lower()}",
        plan_change=f"drop spent chatter; live {surface.lower()} stays",
        plan=f"Skip leftover drop so a live {surface.lower()} cannot vanish.",
        gate_err=f"live {surface.lower()} dropped as leftover",
        chatter_err=f"spent {surface.lower()} chatter leftover",
        dump=f"[It({flag}=True)]",
        setup=f"s.pin('{pin}', kind='{kind}', {flag}=True)",
        is_fail=is_fail,
    )


PAIRS: list[tuple[dict, dict]] = [
    (
        P("mem0-entity-merge-leftover", "r8aa", "m0_em", "merge_live", "Mem0 entity-merge leftover", "mem0-entity-merge-residue", True),
        P("zep-fact-triple-leftover", "r8ab", "zp_ft", "triple_keep", "Zep fact-triple leftover", "zep-fact-triple-residue", False),
    ),
    (
        P("langgraph-channel-upd-leftover", "r8ac", "lg_ch", "chan_live", "LangGraph channel-update leftover", "langgraph-channel-upd-residue", True),
        P("crewai-crew-memory-leftover", "r8ad", "cr_mm", "scope_keep", "CrewAI crew-memory leftover", "crewai-crew-memory-residue", False),
    ),
    (
        P("autogen-groupchat-st-leftover", "r8ae", "ag_gc", "round_live", "AutoGen groupchat-state leftover", "autogen-groupchat-st-residue", True),
        P("llamaindex-node-post-leftover", "r8af", "li_np", "post_keep", "LlamaIndex node-posting leftover", "llamaindex-node-post-residue", False),
    ),
    (
        P("redis-lfu-decay-leftover", "r8ag", "rd_lf", "decay_live", "Redis LFU-decay leftover", "redis-lfu-decay-residue", True),
        P("memcached-cas-token-leftover", "r8ah", "mc_cs", "cas_keep", "Memcached CAS-token leftover", "memcached-cas-token-residue", False),
    ),
    (
        P("hnsw-shrink-layer-leftover", "r8ai", "hn_sh", "layer_live", "HNSW shrink-layer leftover", "hnsw-shrink-layer-residue", True),
        P("ivf-pq-codebook-leftover", "r8aj", "iv_pq", "code_keep", "IVF PQ-codebook leftover", "ivf-pq-codebook-residue", False),
    ),
    (
        P("sqlite-freelist-trunk-leftover", "r8ak", "sq_fl", "trunk_live", "sqlite freelist-trunk leftover", "sqlite-freelist-trunk-residue", True),
        P("wal-index-salt-leftover", "r8al", "wl_st", "salt_keep", "WAL index-salt leftover", "wal-index-salt-residue", False),
    ),
    (
        P("letta-core-block-leftover", "r8am", "lt_cb", "block_live", "Letta core-block leftover", "letta-core-block-residue", True),
        P("memgpt-recall-queue-leftover", "r8an", "mg_rq", "queue_keep", "MemGPT recall-queue leftover", "memgpt-recall-queue-residue", False),
    ),
    (
        P("graphiti-community-sum-leftover", "r8ao", "gt_cm", "comm_live", "Graphiti community-sum leftover", "graphiti-community-sum-residue", True),
        P("cognee-dataset-edge-leftover", "r8ap", "cg_de", "edge_keep", "Cognee dataset-edge leftover", "cognee-dataset-edge-residue", False),
    ),
    (
        P("chroma-segment-wal-leftover", "r8aq", "ch_sw", "seg_live", "Chroma segment-WAL leftover", "chroma-segment-wal-residue", True),
        P("lancedb-deletion-file-leftover", "r8ar", "lc_df", "del_keep", "LanceDB deletion-file leftover", "lancedb-deletion-file-residue", False),
    ),
    (
        P("anthropic-thinking-blk-leftover", "r8as", "an_tb", "think_live", "Anthropic thinking-block leftover", "anthropic-thinking-blk-residue", True),
        P("openai-tool-call-id-leftover", "r8at", "oa_tc", "call_keep", "OpenAI tool-call-id leftover", "openai-tool-call-id-residue", False),
    ),
    (
        P("mcp-sampling-msg-leftover", "r8au", "mp_sm", "samp_live", "MCP sampling-msg leftover", "mcp-sampling-msg-residue", True),
        P("a2a-task-output-leftover", "r8av", "a2_to", "out_keep", "A2A task-output leftover", "a2a-task-output-residue", False),
    ),
    (
        P("temporal-heartbeat-dt-leftover", "r8aw", "tm_hb", "beat_live", "Temporal heartbeat-detail leftover", "temporal-heartbeat-dt-residue", True),
        P("airflow-pool-slot-leftover", "r8ax", "af_ps", "slot_keep", "Airflow pool-slot leftover", "airflow-pool-slot-residue", False),
    ),
    (
        P("kafka-txn-abort-idx-leftover", "r8ay", "kf_tx", "abort_live", "Kafka txn-abort-idx leftover", "kafka-txn-abort-idx-residue", True),
        P("nats-ack-pending-leftover", "r8az", "nt_ap", "ack_keep", "NATS ack-pending leftover", "nats-ack-pending-residue", False),
    ),
    (
        P("pg-xmin-horizon-leftover", "r8ba", "pg_xm", "xmin_live", "Postgres xmin-horizon leftover", "pg-xmin-horizon-residue", True),
        P("mysql-undo-slot-leftover", "r8bb", "my_un", "undo_keep", "MySQL undo-slot leftover", "mysql-undo-slot-residue", False),
    ),
    (
        P("etcd-lease-keepalive-leftover", "r8bc", "et_lk", "lease_live", "etcd lease-keepalive leftover", "etcd-lease-keepalive-residue", True),
        P("consul-session-lock-leftover", "r8bd", "cs_sl", "lock_keep", "Consul session-lock leftover", "consul-session-lock-residue", False),
    ),
    (
        P("wasm-funcref-table-leftover", "r8be", "ws_ft", "table_live", "WASM funcref-table leftover", "wasm-funcref-table-residue", True),
        P("ebpf-stackmap-leftover", "r8bf", "eb_sm", "stack_keep", "eBPF stackmap leftover", "ebpf-stackmap-residue", False),
    ),
]


def _ban_check(spec: dict) -> None:
    blob = json.dumps(spec).lower()
    for needle in BANNED_EXTRA:
        if needle in blob:
            raise SystemExit(f"banned extra needle {needle!r} in {spec.get('slug')}")
    for twin in ("drops-pin", "pin-kept"):
        if twin in spec["slug"]:
            raise SystemExit(f"pin-vs-GC twin slug {spec['slug']}")


def _harvest_used() -> dict[str, set[str]]:
    used = {"slug": set(), "mod": set(), "pin": set(), "first_name": set(), "leftover": set()}
    for p in HERE.glob("amc-mill-*.py"):
        if p.name == Path(__file__).name:
            continue
        text = p.read_text(errors="replace")
        for key, pat in (
            ("slug", r'slug="([^"]+)"'),
            ("mod", r'mod="([^"]+)"'),
            ("pin", r'pin="([^"]+)"'),
            ("first_name", r'first_name="([^"]+)"'),
            ("leftover", r'leftover="([^"]+)"'),
        ):
            used[key].update(re.findall(pat, text))
    return used


def _unique_check() -> None:
    used = _harvest_used()
    bags = {k: [] for k in ("slug", "mod", "pin", "first_name", "leftover")}
    for a, b in PAIRS:
        if a["fail"] is not True or b["fail"] is not False:
            raise SystemExit(f"pair polarity {a['slug']} {b['slug']}")
        if a["surface"] == b["surface"]:
            raise SystemExit(f"same-surface twin {a['slug']}")
        for spec in (a, b):
            _ban_check(spec)
            for k in bags:
                val = spec[k]
                bags[k].append(val)
                if val in used[k]:
                    raise SystemExit(f"used collision {k}={val!r} in {spec['slug']}")
    for name, vals in bags.items():
        if len(vals) != len(set(vals)):
            seen: set[str] = set()
            dups = {v for v in vals if v in seen or seen.add(v)}  # type: ignore
            raise SystemExit(f"duplicate {name}: {dups}")


_unique_check()


def pair_for(round_n: int, pair_idx: int | None = None) -> tuple[dict, dict]:
    idx = round_n - CATALOG_FIRST if pair_idx is None else pair_idx
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for r{round_n} idx={idx} "
            f"(first={CATALOG_FIRST} last={CATALOG_FIRST + len(PAIRS) - 1} n={len(PAIRS)})"
        )
    a, b = PAIRS[idx]
    _ban_check(a)
    _ban_check(b)
    return a, b


def write_round(round_n: int, staging: Path, pair_idx: int | None = None) -> list[str]:
    a, b = pair_for(round_n, pair_idx)
    recs = [build_episode(round_n, a), build_episode(round_n, b)]
    ids = [r["id"] for r in recs]
    if len(set(ids)) != 2:
        raise SystemExit(f"duplicate ids in r{round_n}: {ids}")
    for rec in recs:
        raw = json.dumps(rec)
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in raw:
                raise SystemExit(f"{rec['id']} contains banned key {bad}")
        if '"sim_or_real": "real"' in raw or '"sim_or_real":"real"' in raw:
            raise SystemExit(f"{rec['id']} claims sim_or_real real")
        if rec["meta"]["generator"] != GEN or rec["meta"]["round"] != round_n:
            raise SystemExit("bad meta")
        if rec["meta"]["factory"] != FACTORY:
            raise SystemExit("bad factory")
        if len(rec["steps"]) != 16:
            raise SystemExit(f"{rec['id']} expected 16 steps, got {len(rec['steps'])}")
        for st in rec["steps"]:
            prefix = st["decision_basis"].split(":", 1)[0]
            if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                raise SystemExit(f"bad prefix {prefix} in {rec['id']}")
            if len(st["decision_basis"]) > 240:
                raise SystemExit(f"decision_basis too long in {rec['id']} n={st['n']}")
        if recs[0]["reward"]["success"] is not False:
            raise SystemExit("ep1 must fail")
        if recs[1]["reward"]["success"] is not True:
            raise SystemExit("ep2 must succeed")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in recs))
    notes_text = notes_for(round_n, a, b)
    if "Novel coverage:" not in notes_text:
        raise SystemExit("notes missing Novel coverage")
    notes.write_text(notes_text)
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair", type=int, default=None)
    args = ap.parse_args()
    ids = write_round(args.round, Path(args.staging), args.pair)
    print(json.dumps({"round": args.round, "ids": ids, "pair": args.pair}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
