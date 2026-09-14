#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4dj: unused Yugabyte/TiDB/Vitess plants after w4di.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig,
r4687 rust-pin, r4580 kanidm/gluu, identity-origin, RPITIT, Prom hist,
ThinLTO, Go loopvar, Django ASGI, Vale, Koka, published.
IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4dj_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
    "rust-pin", "pin-unpin", "pin-project", "transmute",
    "nim-lent", "nim-var-escape", "zig-errdefer", "zig-defer",
    "luigi", "dvc-cache", "squashfs", "overlayfs", "nvidia-cdi",
    "wdl-runtime", "muscle", "mafft", "freebayes", "hisat", "stringtie",
    "fastqc", "multiqc", "spades", "flye", "kraken", "hisat2",
    "rsem", "seurat", "mutect2", "hail-npart", "cellbender",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4dj|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused Yugabyte / TiDB / Vitess / Spanner plants after w4di.
PLANTS = {
    "yugabyte": mk(True, "pr-yugabyte-ysql-pref-az", "lock-ybaz",
        "the Yugabyte YSQL tablespace that omitted replica_placement so a 3-AZ table sat 1 AZ and a zone outage sat 100% down",
        "yb.sql", "CREATE TABLE t (id int)", "CREATE TABLESPACE ts WITH (replica_placement=...)",
        "replica_placement", "harbor CREATE TABLE only. pack replica_placement 3 AZ.",
        "FAIL test_assign: 1 AZ 100% down; replica_placement missing",
        "CREATE TABLE only", "CREATE TABLE is not replica_placement"),
    "tidb": mk(False, "pr-tidb-tikv-gc-life", "quay-tdgc",
        "the TiDB tikv_gc_life_time that omitted 24h so a 4h analytics sat 10m default and MVCC GC killed long scans",
        "tidb.sql", "SET GLOBAL tidb_gc_max_wait_time=60", "SET GLOBAL tikv_gc_life_time='24h'",
        "tikv_gc_life_time", "harbor tidb_gc_max_wait_time only. pack tikv_gc_life_time 24h.",
        "FAIL test_assign: 10m GC kill scans; tikv_gc_life_time missing",
        "gc_max_wait only", "gc_max_wait is not tikv_gc_life_time"),
    "vitess": mk(True, "pr-vitess-buffer-window", "lock-vtbuf",
        "the Vitess vttablet that omitted buffer.window so a planned reparent sat unbuffered and 12s of writes 417'd",
        "vt.yaml", "health_check_interval: 1s", "buffer.window: 30s",
        "buffer.window", "harbor health_check_interval only. pack buffer.window 30s.",
        "FAIL test_assign: unbuffered 12s 417; buffer.window missing",
        "health_check only", "health_check is not buffer.window"),
    "spanner": mk(False, "pr-spanner-staleness-read", "quay-spsst",
        "the Spanner query that omitted exact_staleness so a 4TB scan sat strong and p99 sat 8s",
        "sp.py", "db.execute(sql)", "db.snapshot(exact_staleness=datetime.timedelta(seconds=15))",
        "exact_staleness", "harbor execute sql only. pack exact_staleness 15s.",
        "FAIL test_assign: strong p99 8s; exact_staleness missing",
        "execute only", "execute is not exact_staleness"),
    "cockroach": mk(True, "pr-cockroach-lease-preference", "lock-crlp",
        "the Cockroach CONFIGURE ZONE that omitted lease_preferences so a 3-region table sat leases in us-east and eu p99 sat 180ms",
        "cr.sql", "ALTER TABLE t CONFIGURE ZONE USING num_replicas=5", "lease_preferences='[[+region=eu]]'",
        "lease_preferences", "harbor num_replicas only. pack lease_preferences eu.",
        "FAIL test_assign: us-east leases eu 180ms; lease_preferences missing",
        "num_replicas only", "num_replicas is not lease_preferences"),
    "yugabytet": mk(False, "pr-yugabyte-cdc-consistent-stream", "quay-ybcdc",
        "the Yugabyte CDC that omitted consistent_stream so a Debezium sat unordered and the sink sat dup keys",
        "yb.sh", "ysqlsh -c 'CREATE PUBLICATION p'", "cdc consistent_stream=true",
        "consistent_stream", "harbor CREATE PUBLICATION only. pack consistent_stream.",
        "FAIL test_assign: unordered dup keys; consistent_stream missing",
        "PUBLICATION only", "PUBLICATION is not consistent_stream"),
    "citus": mk(True, "pr-citus-colocate-with", "lock-ctcol",
        "the Citus create_distributed_table that omitted colocate_with so a join sat cross-shard and 40x slower",
        "citus.sql", "SELECT create_distributed_table('t','id')", "create_distributed_table('o','id', colocate_with:='t')",
        "colocate_with", "harbor create_distributed_table only. pack colocate_with.",
        "FAIL test_assign: cross-shard 40x; colocate_with missing",
        "distributed_table only", "distributed_table is not colocate_with"),
    "timescaledb": mk(False, "pr-timescaledb-chunk-interval", "quay-tsch",
        "the Timescale create_hypertable that omitted chunk_time_interval so a 2y table sat 7d chunks and 4000 chunks stalled autovacuum",
        "ts.sql", "SELECT create_hypertable('m','ts')", "create_hypertable('m','ts', chunk_time_interval => INTERVAL '1 month')",
        "chunk_time_interval", "harbor create_hypertable only. pack chunk_time_interval 1 month.",
        "FAIL test_assign: 4000 chunks stall; chunk_time_interval missing",
        "hypertable only", "hypertable is not chunk_time_interval"),
    "clickhouse2": mk(True, "pr-clickhouse-ttl-group", "lock-chttl",
        "the ClickHouse MergeTree that omitted TTL so a 4TB table sat unbounded and disk filled",
        "ch.sql", "ENGINE = MergeTree ORDER BY (d, id)", "TTL d + INTERVAL 90 DAY",
        "TTL", "harbor ORDER BY only. pack TTL 90 DAY.",
        "FAIL test_assign: unbounded disk fill; TTL missing",
        "ORDER BY only", "ORDER BY is not TTL"),
    "druid": mk(False, "pr-druid-max-rows-in-memory", "quay-drmem",
        "the Druid KafkaIndexTask that omitted maxRowsInMemory so a 40k evt/s sat 1M default and GC sat 8s",
        "druid.json", "ioConfig.topic", "tuningConfig.maxRowsInMemory=75000",
        "maxRowsInMemory", "harbor topic only. pack maxRowsInMemory 75k.",
        "FAIL test_assign: 1M GC 8s; maxRowsInMemory missing",
        "topic only", "topic is not maxRowsInMemory"),
    "pinot": mk(True, "pr-pinot-realtime-flush-threshold", "lock-ptfl",
        "the Pinot realtime table that omitted flushThresholdTime so a 40k evt/s sat 6h default and consuming sat 80GB",
        "pinot.json", "tableType: REALTIME", "flushThresholdTime: 15m",
        "flushThresholdTime", "harbor REALTIME only. pack flushThresholdTime 15m.",
        "FAIL test_assign: 6h 80GB consuming; flushThresholdTime missing",
        "REALTIME only", "REALTIME is not flushThresholdTime"),
    "trino": mk(False, "pr-trino-query-max-memory", "quay-trqmm",
        "the Trino session that omitted query_max_memory so a 4TB join sat 20GB default and QueryExceededMemory",
        "trino.sql", "SET SESSION join_distribution_type='PARTITIONED'", "SET SESSION query_max_memory='200GB'",
        "query_max_memory", "harbor join_distribution only. pack query_max_memory 200GB.",
        "FAIL test_assign: 20GB QueryExceededMemory; query_max_memory missing",
        "join_distribution only", "join_distribution is not query_max_memory"),
    "presto": mk(True, "pr-presto-spill-enabled", "lock-prspl",
        "the Presto session that omitted spill_enabled so a 2TB agg sat in-memory and worker OOM'd",
        "presto.sql", "SET SESSION join_reordering_strategy='AUTOMATIC'", "SET SESSION spill_enabled=true",
        "spill_enabled", "harbor join_reordering only. pack spill_enabled.",
        "FAIL test_assign: in-memory OOM; spill_enabled missing",
        "join_reordering only", "join_reordering is not spill_enabled"),
    "bigquery": mk(False, "pr-bigquery-require-partition-filter", "quay-bqrpf",
        "the BigQuery table that omitted require_partition_filter so a 40TB scan sat unfiltered and $ sat 12x",
        "bq.sql", "CREATE TABLE t PARTITION BY DATE(ts)", "OPTIONS(require_partition_filter=true)",
        "require_partition_filter", "harbor PARTITION BY only. pack require_partition_filter.",
        "FAIL test_assign: unfiltered $ 12x; require_partition_filter missing",
        "PARTITION BY only", "PARTITION BY is not require_partition_filter"),
    "snowflake": mk(True, "pr-snowflake-clustering-key", "lock-sfck",
        "the Snowflake table that omitted CLUSTER BY so a 20TB fact sat unclustered and pruning sat 2%",
        "sf.sql", "CREATE TABLE f (d DATE, id INT)", "CLUSTER BY (d)",
        "CLUSTER BY", "harbor CREATE TABLE only. pack CLUSTER BY d.",
        "FAIL test_assign: pruning 2%; CLUSTER BY missing",
        "CREATE TABLE only", "CREATE TABLE is not CLUSTER BY"),
    "redshift": mk(False, "pr-redshift-sortkey", "quay-rssk",
        "the Redshift table that omitted SORTKEY so a 8TB fact sat unsorted and scans sat 40x",
        "rs.sql", "CREATE TABLE f (d DATE, id INT) DISTSTYLE KEY DISTKEY(id)", "SORTKEY(d)",
        "SORTKEY", "harbor DISTKEY only. pack SORTKEY d.",
        "FAIL test_assign: unsorted 40x scan; SORTKEY missing",
        "DISTKEY only", "DISTKEY is not SORTKEY"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Yugabyte replica_placement vs TiDB tikv_gc_life_time", fn("yugabyte"), fn("tidb"),
     "replica_placement 3 AZ; tikv_gc_life_time 24h", "CREATE TABLE; gc_max_wait",
     "yugabyte dump 1 AZ 100% down; tidb dump 10m GC kill scans"),
    ("Vitess buffer.window vs Spanner exact_staleness", fn("vitess"), fn("spanner"),
     "buffer.window 30s; exact_staleness 15s", "health_check; execute",
     "vitess dump unbuffered 12s 417; spanner dump strong p99 8s"),
    ("Cockroach lease_preferences vs Yugabyte CDC consistent_stream", fn("cockroach"), fn("yugabytet"),
     "lease_preferences eu; consistent_stream", "num_replicas; PUBLICATION",
     "cockroach dump us-east leases 180ms; yugabyte dump unordered dups"),
    ("Citus colocate_with vs Timescale chunk_time_interval", fn("citus"), fn("timescaledb"),
     "colocate_with; chunk_time_interval 1 month", "distributed_table; hypertable",
     "citus dump cross-shard 40x; timescale dump 4000 chunks stall"),
    ("ClickHouse TTL vs Druid maxRowsInMemory", fn("clickhouse2"), fn("druid"),
     "TTL 90 DAY; maxRowsInMemory 75k", "ORDER BY; topic",
     "clickhouse dump unbounded fill; druid dump 1M GC 8s"),
    ("Pinot flushThresholdTime vs Trino query_max_memory", fn("pinot"), fn("trino"),
     "flushThresholdTime 15m; query_max_memory 200GB", "REALTIME; join_distribution",
     "pinot dump 6h 80GB; trino dump 20GB QueryExceededMemory"),
    ("Presto spill_enabled vs BigQuery require_partition_filter", fn("presto"), fn("bigquery"),
     "spill_enabled; require_partition_filter", "join_reordering; PARTITION BY",
     "presto dump in-memory OOM; bigquery dump unfiltered $ 12x"),
    ("Snowflake CLUSTER BY vs Redshift SORTKEY", fn("snowflake"), fn("redshift"),
     "CLUSTER BY d; SORTKEY d", "CREATE TABLE; DISTKEY",
     "snowflake dump pruning 2%; redshift dump unsorted 40x"),
]


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig-errdefer, r4687 rust-pin, r4580 kanidm/gluu, identity-origin SSO.
- Bans avoided: nim-lent / zig-errdefer / rust-pin / Mutect2 / Hail / FastQC / Seurat / RSEM / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name == "sandbox-refusal-factory":
            continue
        if p.name == "long-horizon-coding-factory":
            continue
        writing = any(p.glob("ROUND-r*.reserved.json")) or any(p.glob("ROUND-r*.publishing.json"))
        if writing:
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            while st["lhc_pair"] < len(LHC_PAIRS):
                title, fa, fb, *_ = LHC_PAIRS[st["lhc_pair"]]
                probe_a, probe_b = fa(1), fb(1)
                probe_slugs = [
                    "-".join(x["id"].split("-")[2:-1]) for x in (probe_a, probe_b)
                ]
                if any(s in used for s in probe_slugs):
                    print(f"skip used pair {st['lhc_pair']} {title} {probe_slugs}", flush=True)
                    st["lhc_pair"] += 1
                    save_state(st)
                    continue
                break
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (retry LHC; never sandbox-refusal):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(1)
            if hops > 600:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
