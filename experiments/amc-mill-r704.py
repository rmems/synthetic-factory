#!/usr/bin/env python3
"""Mill AMC r704+ leftover leftover leftover after r688 catalog drain.

Each pair is TWO DISTINCT leftover mechanisms (not drop-vs-keep twins).
BAN pin-vs-GC cartesian, doorway catalogs, psych catalogs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("amcmill170h704", str(HERE / "amc-mill-r170.py")).load_module()
F = _base.F
S = _base.S
build_episode = _base.build_episode
FACTORY = _base.FACTORY
GEN = _base.GEN

CATALOG_FIRST = 704

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
        P("chromadb-where-doc-leftover", "r9aa", "ch_wd", "where_live", "ChromaDB where-document leftover", "chromadb-where-doc-r704", True),
        P("weaviate-hybrid-score-leftover", "r9ab", "wv_hy", "hybrid_keep", "Weaviate hybrid-score leftover", "weaviate-hybrid-score-r704", False),
    ),
    (
        P("qdrant-payload-idx-leftover", "r9ac", "qd_pi", "payload_live", "Qdrant payload-index leftover", "qdrant-payload-idx-r704", True),
        P("milvus-partition-tag-leftover", "r9ad", "mv_pt", "part_keep", "Milvus partition-tag leftover", "milvus-partition-tag-r704", False),
    ),
    (
        P("pgvector-ivfflat-probe-leftover", "r9ae", "pg_iv", "probe_live", "pgvector ivfflat-probe leftover", "pgvector-ivfflat-probe-r704", True),
        P("pinecone-namespace-meta-leftover", "r9af", "pn_ns", "ns_keep", "Pinecone namespace-meta leftover", "pinecone-namespace-meta-r704", False),
    ),
    (
        P("lancedb-version-tip-leftover", "r9ag", "lc_vt", "tip_live", "LanceDB version-tip leftover", "lancedb-version-tip-r704", True),
        P("vespa-tensor-cell-leftover", "r9ah", "vs_tc", "cell_keep", "Vespa tensor-cell leftover", "vespa-tensor-cell-r704", False),
    ),
    (
        P("opensearch-knn-ef-leftover", "r9ai", "os_ef", "ef_live", "OpenSearch knn-ef leftover", "opensearch-knn-ef-r704", True),
        P("elasticsearch-knn-filter-leftover", "r9aj", "es_kf", "filter_keep", "Elasticsearch knn-filter leftover", "elasticsearch-knn-filter-r704", False),
    ),
    (
        P("redis-json-path-leftover", "r9ak", "rd_jp", "json_live", "RedisJSON path leftover", "redis-json-path-r704", True),
        P("valkey-sso-slot-leftover", "r9al", "vk_ss", "slot_keep", "Valkey SSO-slot leftover", "valkey-sso-slot-r704", False),
    ),
    (
        P("neo4j-gds-proj-leftover", "r9am", "nj_gp", "proj_live", "Neo4j GDS-projection leftover", "neo4j-gds-proj-r704", True),
        P("dgraph-uid-facet-leftover", "r9an", "dg_uf", "facet_keep", "Dgraph uid-facet leftover", "dgraph-uid-facet-r704", False),
    ),
    (
        P("nats-kv-rev-leftover", "r9ao", "nt_kv", "rev_live", "NATS KV-revision leftover", "nats-kv-rev-r704", True),
        P("jetstream-consumer-ack-leftover", "r9ap", "js_ak", "ack_keep", "JetStream consumer-ack leftover", "jetstream-consumer-ack-r704", False),
    ),
    (
        P("kafka-txn-marker-leftover", "r9aq", "kf_tm", "txn_live", "Kafka txn-marker leftover", "kafka-txn-marker-r704", True),
        P("pulsar-cursor-mark-leftover", "r9ar", "pu_cm", "cursor_keep", "Pulsar cursor-mark leftover", "pulsar-cursor-mark-r704", False),
    ),
    (
        P("sqlite-wal-frame-leftover", "r9as", "sq_wf", "wal_live", "SQLite WAL-frame leftover", "sqlite-wal-frame-r704", True),
        P("duckdb-checkpoint-meta-leftover", "r9at", "dk_cp", "ckpt_keep", "DuckDB checkpoint-meta leftover", "duckdb-checkpoint-meta-r704", False),
    ),
    (
        P("rocksdb-blob-gc-leftover", "r9au", "rk_bg", "blob_live", "RocksDB blob-GC leftover", "rocksdb-blob-gc-r704", True),
        P("leveldb-manifest-seq-leftover", "r9av", "lv_ms", "seq_keep", "LevelDB manifest-seq leftover", "leveldb-manifest-seq-r704", False),
    ),
    (
        P("etcd-mvcc-rev-leftover", "r9aw", "et_mv", "mvcc_live", "etcd MVCC-rev leftover", "etcd-mvcc-rev-r704", True),
        P("consul-session-check-leftover", "r9ax", "cs_sc", "sess_keep", "Consul session-check leftover", "consul-session-check-r704", False),
    ),
    (
        P("vault-lease-renew-leftover", "r9ay", "vt_lr", "lease_live", "Vault lease-renew leftover", "vault-lease-renew-r704", True),
        P("boundary-session-rec-leftover", "r9az", "bd_sr", "rec_keep", "Boundary session-rec leftover", "boundary-session-rec-r704", False),
    ),
    (
        P("opa-decision-log-leftover", "r9ba", "op_dl", "dlog_live", "OPA decision-log leftover", "opa-decision-log-r704", True),
        P("cedar-policy-slot-leftover", "r9bb", "cd_ps", "policy_keep", "Cedar policy-slot leftover", "cedar-policy-slot-r704", False),
    ),
    (
        P("spiffe-svid-bundle-leftover", "r9bc", "sp_sv", "svid_live", "SPIFFE SVID-bundle leftover", "spiffe-svid-bundle-r704", True),
        P("istio-wasm-plugin-leftover", "r9bd", "is_wp", "wasm_keep", "Istio wasm-plugin leftover", "istio-wasm-plugin-r704", False),
    ),
    (
        P("envoy-hcm-stat-leftover", "r9be", "en_hs", "hcm_live", "Envoy HCM-stat leftover", "envoy-hcm-stat-r704", True),
        P("cilium-identity-map-leftover", "r9bf", "ci_im", "id_keep", "Cilium identity-map leftover", "cilium-identity-map-r704", False),
    ),
    (
        P("coredns-cache-ttl-leftover", "r9bg", "cd_ct", "ttl_live", "CoreDNS cache-TTL leftover", "coredns-cache-ttl-r704", True),
        P("unbound-infra-rtt-leftover", "r9bh", "ub_ir", "rtt_keep", "Unbound infra-RTT leftover", "unbound-infra-rtt-r704", False),
    ),
    (
        P("prometheus-tsdb-tomb-leftover", "r9bi", "pr_tt", "tomb_live", "Prometheus TSDB-tomb leftover", "prometheus-tsdb-tomb-r704", True),
        P("loki-chunk-index-leftover", "r9bj", "lk_ci", "chunk_keep", "Loki chunk-index leftover", "loki-chunk-index-r704", False),
    ),
    (
        P("tempo-block-meta-leftover", "r9bk", "tp_bm", "block_live", "Tempo block-meta leftover", "tempo-block-meta-r704", True),
        P("jaeger-span-ref-leftover", "r9bl", "jg_sr", "span_keep", "Jaeger span-ref leftover", "jaeger-span-ref-r704", False),
    ),
    (
        P("otel-sdk-span-proc-leftover", "r9bm", "ot_sp", "proc_live", "OTel SDK span-processor leftover", "otel-sdk-span-proc-r704", True),
        P("vector-buffer-ack-leftover", "r9bn", "vc_ba", "buf_keep", "Vector buffer-ack leftover", "vector-buffer-ack-r704", False),
    ),
]


def _ban_check(spec: dict) -> None:
    blob = " ".join(str(spec.get(k, "")) for k in spec).lower()
    for bit in BANNED_EXTRA:
        if bit in blob:
            raise SystemExit(f"banned {bit} in {spec['slug']}")


def _harvest_used() -> dict[str, set[str]]:
    used = {k: set() for k in ("slug", "mod", "pin", "first_name", "leftover")}
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
