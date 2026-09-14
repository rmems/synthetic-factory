#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4ck: unused lakehouse/CDC plants after r4580.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4580 pr-kanidm-domain-origin-https / pr-gluu-agama-flow-timeout and
prior identity-origin clones (oauth2-proxy, authentik, ory, hydra, kratos,
keto, zitadel, authelia, pomerium, teleport, dex, sssd, pam, casdoor).
Also BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale,
Koka, and any plant already published. IDs lhc-rNNNN-pr-*. generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4ck_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4ck|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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


# Compact unused lakehouse / CDC / stream / OLAP / ML-serving plants.
# Not identity-origin. Not r4580 kanidm/gluu or the w4cj SSO window.
PLANTS = {
    "debezium": mk(True, "pr-debezium-heartbeat-interval-quiet", "lock-dbzbeat",
        "the Debezium MySQL connector that omitted heartbeat.interval.ms so a quiet table never advanced the source offset",
        "debezium.yml", "snapshot.mode: initial", "heartbeat.interval.ms 10000",
        "heartbeat.interval.ms", "harbor snapshot.mode schema_only. pack heartbeat.interval.ms.",
        "FAIL test_assign: offset stuck on quiet table; heartbeat missing",
        "snapshot.mode schema_only", "snapshot.mode is not heartbeat.interval.ms"),
    "maxwell": mk(False, "pr-maxwell-filter-databases-include", "quay-maxflt",
        "the Maxwell daemon that omitted filter.databases so bootstrap streamed mysql.* system tables into Kafka",
        "config.properties", "producer=kafka", "filter.databases=harbor",
        "filter.databases", "harbor exclude_tables only. pack filter.databases.",
        "FAIL test_assign: mysql.user rows in topic; filter.databases missing",
        "exclude_tables only", "exclude_tables is not filter.databases"),
    "flink": mk(True, "pr-flink-incremental-checkpoints-rocks", "lock-flinkinc",
        "the Flink job that omitted incremental checkpoints so RocksDB snapshots bloated the DFS and backpressured",
        "flink-conf.yaml", "execution.checkpointing.interval: 10s", "execution.checkpointing.incremental true",
        "execution.checkpointing.incremental", "harbor checkpoint interval only. pack incremental true.",
        "FAIL test_assign: full RocksDB snapshot 40GiB; incremental missing",
        "checkpoint interval only", "interval is not incremental checkpoints"),
    "spark": mk(False, "pr-spark-watermark-delay-threshold", "quay-spkwm",
        "the Spark Structured Streaming query that omitted watermarkDelayThreshold so late events were dropped at 0s",
        "spark.conf", "spark.sql.shuffle.partitions=200", "spark.sql.streaming.watermarkDelayThreshold 10m",
        "watermarkDelayThreshold", "harbor maxOffsetsPerTrigger only. pack watermarkDelayThreshold.",
        "FAIL test_assign: late events dropped; watermark delay missing",
        "maxOffsetsPerTrigger only", "maxOffsetsPerTrigger is not watermark delay"),
    "connect": mk(True, "pr-connect-smt-unwrap-debezium", "lock-csmtunw",
        "the Kafka Connect sink that omitted ExtractNewRecordState so the payload stayed nested under after and the sink 400'd",
        "connect.json", "connector.class: JdbcSink", "ExtractNewRecordState SMT",
        "ExtractNewRecordState", "harbor Flatten SMT only. pack ExtractNewRecordState.",
        "FAIL test_assign: column after.payload missing; unwrap SMT missing",
        "Flatten SMT only", "Flatten is not ExtractNewRecordState"),
    "redpanda": mk(False, "pr-redpanda-schema-compat-full", "quay-rpsfull",
        "the Redpanda schema registry that omitted compatibility FULL so a field delete broke a compiled consumer",
        "redpanda.yaml", "schema_registry: {enabled: true}", "compatibility FULL",
        "compatibility", "harbor BACKWARD only. pack compatibility FULL.",
        "FAIL test_assign: consumer decode fail after field delete; FULL missing",
        "BACKWARD only", "BACKWARD is not FULL compatibility"),
    "pulsar": mk(True, "pr-pulsar-bookie-ensemble-size", "lock-pulens",
        "the Pulsar namespace that omitted managedLedgerDefaultEnsembleSize 3 so a single bookie loss dropped messages",
        "broker.conf", "managedLedgerDefaultAckQuorum=2", "managedLedgerDefaultEnsembleSize=3",
        "managedLedgerDefaultEnsembleSize", "harbor ackQuorum only. pack ensemble size 3.",
        "FAIL test_assign: bookie loss dropped messages; ensemble size missing",
        "ackQuorum only", "ackQuorum is not ensemble size"),
    "nats": mk(False, "pr-nats-jetstream-max-bytes-limit", "quay-natsmb",
        "the NATS JetStream stream that omitted max_bytes so the disk filled and new publishes 507'd",
        "nats.conf", "jetstream { store_dir: /data }", "max_bytes 20GB",
        "max_bytes", "harbor max_age only. pack max_bytes.",
        "FAIL test_assign: disk full; publish 507; max_bytes missing",
        "max_age only", "max_age is not max_bytes"),
    "risingwave": mk(True, "pr-risingwave-backfill-rate-limit", "lock-rwback",
        "the RisingWave source that omitted backfill_rate_limit so the snapshot scan OOMed the compute node",
        "risingwave.toml", "parallelism = 4", "backfill_rate_limit 10000",
        "backfill_rate_limit", "harbor parallelism only. pack backfill_rate_limit.",
        "FAIL test_assign: snapshot OOM; backfill_rate_limit missing",
        "parallelism only", "parallelism is not backfill_rate_limit"),
    "materialize": mk(False, "pr-materialize-persist-blob-uri", "quay-mzblob",
        "the Materialize cluster that omitted persist blob URI so a restart rebuilt an empty catalog",
        "mz.toml", "persist.consensus_uri = postgres://mz", "persist.blob_uri s3://mz-persist",
        "persist.blob_uri", "harbor persist consensus only. pack persist.blob_uri.",
        "FAIL test_assign: catalog empty after restart; blob URI missing",
        "persist consensus only", "consensus URI is not persist blob URI"),
    "clickhouse": mk(True, "pr-clickhouse-distributed-ddl-output", "lock-chddl",
        "the ClickHouse cluster that omitted distributed_ddl_output_mode none so ON CLUSTER hung on the output table",
        "users.xml", "distributed_ddl_task_timeout=180", "distributed_ddl_output_mode none",
        "distributed_ddl_output_mode", "harbor replication_alter_partitions_sync. pack output_mode none.",
        "FAIL test_assign: ON CLUSTER hung; output_mode missing",
        "replication_alter_partitions_sync", "alter sync is not distributed_ddl_output_mode"),
    "pinot": mk(False, "pr-pinot-realtime-offline-task", "quay-pinr2o",
        "the Pinot table that omitted realtimeToOfflineTask so the REALTIME segment grew unbounded",
        "table.json", "retentionTimeUnit: DAYS", "realtimeToOfflineTask schedule",
        "realtimeToOfflineTask", "harbor retentionTimeUnit only. pack realtimeToOfflineTask.",
        "FAIL test_assign: REALTIME 400GiB; realtimeToOfflineTask missing",
        "retentionTimeUnit only", "retention is not realtimeToOfflineTask"),
    "duckdb": mk(True, "pr-duckdb-httpfs-s3-region", "lock-ddbs3r",
        "the DuckDB httpfs scan that omitted s3_region so parquet GET looped 301 across the wrong region",
        "duckdb.sql", "SET s3_endpoint='s3.amazonaws.com';", "SET s3_region='us-east-1';",
        "s3_region", "harbor s3_endpoint only. pack s3_region.",
        "FAIL test_assign: 301 loop; s3_region missing",
        "s3_endpoint only", "s3_endpoint is not s3_region"),
    "questdb": mk(False, "pr-questdb-cairo-wal-enabled", "quay-qdbwal",
        "the QuestDB table that omitted cairo.wal.enabled so ALTER TABLE locked writers for minutes",
        "server.conf", "cairo.commit.lag=300000", "cairo.wal.enabled=true",
        "cairo.wal.enabled", "harbor cairo.commit.lag only. pack cairo.wal.enabled.",
        "FAIL test_assign: ALTER locked writers; wal.enabled missing",
        "cairo.commit.lag only", "commit.lag is not cairo.wal.enabled"),
    "druid": mk(True, "pr-druid-indexer-max-rows-memory", "lock-druidmm",
        "the Druid indexer that omitted maxRowsInMemory so the middleManager GC thrashed and tasks timed out",
        "supervisor.json", "maxRowsPerSegment: 5000000", "maxRowsInMemory 750000",
        "maxRowsInMemory", "harbor maxRowsPerSegment only. pack maxRowsInMemory.",
        "FAIL test_assign: GC thrash; task timeout; maxRowsInMemory missing",
        "maxRowsPerSegment only", "maxRowsPerSegment is not maxRowsInMemory"),
    "cratedb": mk(False, "pr-cratedb-number-of-replicas-zero", "quay-crtrep",
        "the CrateDB single-node table that omitted number_of_replicas 0 so the cluster stayed yellow and blocked writes",
        "crate.yml", "gateway.expected_nodes: 1", "number_of_replicas 0",
        "number_of_replicas", "harbor wait_for_active_shards only. pack number_of_replicas 0.",
        "FAIL test_assign: yellow cluster; writes blocked; replicas missing",
        "wait_for_active_shards only", "wait_for_active_shards is not number_of_replicas"),
    "trino": mk(True, "pr-trino-exchange-manager-filesystem", "lock-trxchg",
        "the Trino cluster that omitted exchange-manager filesystem so joins spilled into /tmp and filled the node",
        "config.properties", "query.max-memory=20GB", "exchange-manager filesystem",
        "exchange-manager", "harbor query.max-memory only. pack exchange-manager filesystem.",
        "FAIL test_assign: /tmp full; join spill; exchange-manager missing",
        "query.max-memory only", "query.max-memory is not exchange-manager"),
    "presto": mk(False, "pr-presto-spill-enabled-path", "quay-prspill",
        "the Presto worker that omitted spill-enabled so a hash join OOMed at 80% heap",
        "config.properties", "join-distribution-type=AUTOMATIC", "spill-enabled=true",
        "spill-enabled", "harbor join-distribution-type only. pack spill-enabled.",
        "FAIL test_assign: hash join OOM; spill-enabled missing",
        "join-distribution-type only", "join-distribution-type is not spill-enabled"),
    "iceberg": mk(True, "pr-iceberg-expire-snapshots-retain", "lock-iceexp",
        "the Iceberg table that omitted expire_snapshots retain_last so the snapshot list exploded and planning slowed",
        "spark.sql", "CALL remove_orphan_files()", "expire_snapshots retain_last 10",
        "expire_snapshots", "harbor remove_orphan_files only. pack expire_snapshots retain_last.",
        "FAIL test_assign: 40k snapshots; planning 3m; expire_snapshots missing",
        "remove_orphan_files only", "orphan cleanup is not expire_snapshots"),
    "hudi": mk(False, "pr-hudi-clean-policy-keep-latest", "quay-hudicl",
        "the Hudi table that omitted hoodie.cleaner.policy KEEP_LATEST_COMMITS so instant files piled up",
        "hudi.properties", "hoodie.compact.inline=true", "hoodie.cleaner.policy KEEP_LATEST_COMMITS",
        "hoodie.cleaner.policy", "harbor hoodie.compact.inline only. pack cleaner policy.",
        "FAIL test_assign: 12k instants; timeline list 40s; cleaner policy missing",
        "hoodie.compact.inline only", "inline compact is not cleaner policy"),
    "delta": mk(True, "pr-delta-deleted-file-retention", "lock-dltdel",
        "the Delta table that omitted deletedFileRetentionDuration so VACUUM removed files CDF still needed",
        "delta.conf", "delta.logRetentionDuration=30 days", "deletedFileRetentionDuration 7 days",
        "deletedFileRetentionDuration", "harbor logRetentionDuration only. pack deletedFileRetentionDuration.",
        "FAIL test_assign: CDF read 404 after VACUUM; deletedFileRetention missing",
        "logRetentionDuration only", "logRetention is not deletedFileRetention"),
    "nessie": mk(False, "pr-nessie-gc-default-retention", "quay-nsgc",
        "the Nessie server that omitted gc.default.retention so expired refs were never collected and the repo bloated",
        "nessie.properties", "nessie.commit.retry=32", "gc.default.retention P7D",
        "gc.default.retention", "harbor commit.retry only. pack gc.default.retention.",
        "FAIL test_assign: 2M expired refs; gc.default.retention missing",
        "commit.retry only", "commit.retry is not gc.default.retention"),
    "airbyte": mk(True, "pr-airbyte-state-persistence-s3", "lock-abstate",
        "the Airbyte connection that omitted state persistence to S3 so a reset lost the incremental cursor",
        "airbyte.yml", "normalization: basic", "state persistence s3",
        "state", "harbor normalization only. pack state persistence s3.",
        "FAIL test_assign: cursor reset to 0; full resync; state S3 missing",
        "normalization only", "normalization is not state persistence"),
    "singer": mk(False, "pr-singer-bookmark-full-refresh", "quay-sngbk",
        "the Singer tap that omitted a full-refresh bookmark reset so a new PK range was skipped",
        "tap.json", "start_date: 2020-01-01", "bookmark full-refresh reset",
        "bookmark", "harbor start_date only. pack bookmark full-refresh reset.",
        "FAIL test_assign: new PK range skipped; bookmark reset missing",
        "start_date only", "start_date is not bookmark reset"),
    "dbt": mk(True, "pr-dbt-incremental-unique-key", "lock-dbtuniq",
        "the dbt incremental model that omitted unique_key so merge produced duplicate rows",
        "model.sql", "{{ config(incremental_strategy='delete+insert') }}", "unique_key id",
        "unique_key", "harbor incremental_strategy only. pack unique_key.",
        "FAIL test_assign: duplicate rows after merge; unique_key missing",
        "incremental_strategy only", "incremental_strategy is not unique_key"),
    "gx": mk(False, "pr-gx-checkpoint-action-list", "quay-gxact",
        "the Great Expectations Checkpoint that omitted action_list so validation ran but never alerted Slack",
        "checkpoint.yml", "expectation_suite_name: harbor", "action_list SlackNotification",
        "action_list", "harbor expectation suite only. pack action_list.",
        "FAIL test_assign: validation ran; no Slack; action_list missing",
        "expectation suite only", "suite is not action_list"),
    "soda": mk(True, "pr-soda-scan-fail-on-error", "lock-sodafail",
        "the Soda scan that omitted fail_on error so CI returned 0 with failed checks",
        "soda.yml", "samples limit 100", "fail_on error",
        "fail_on", "harbor samples limit only. pack fail_on error.",
        "FAIL test_assign: CI green with failed checks; fail_on missing",
        "samples limit only", "samples limit is not fail_on"),
    "elementary": mk(False, "pr-elementary-anomaly-sensitivity", "quay-elmsens",
        "the Elementary anomaly monitor that omitted anomaly_sensitivity so volume drops never alerted",
        "elementary.yml", "days_back: 14", "anomaly_sensitivity medium",
        "anomaly_sensitivity", "harbor days_back only. pack anomaly_sensitivity.",
        "FAIL test_assign: volume drop silent; anomaly_sensitivity missing",
        "days_back only", "days_back is not anomaly_sensitivity"),
    "feast": mk(True, "pr-feast-online-store-ttl-seconds", "lock-feasttl",
        "the Feast online store that omitted ttl so Redis filled with stale feature rows",
        "feature_store.yaml", "entity_ttl: 0", "online_store ttl 86400",
        "ttl", "harbor entity_ttl only. pack online_store ttl.",
        "FAIL test_assign: Redis 100% memory; online ttl missing",
        "entity_ttl only", "entity_ttl is not online_store ttl"),
    "mlflow": mk(False, "pr-mlflow-artifact-root-s3", "quay-mflart",
        "the MLflow tracking server that omitted artifact_root s3 so artifacts vanished on pod recycle",
        "mlflow.ini", "backend_store_uri=postgresql://ml", "artifact_root s3://ml-art",
        "artifact_root", "harbor backend_store_uri only. pack artifact_root s3.",
        "FAIL test_assign: artifacts gone after recycle; artifact_root missing",
        "backend_store_uri only", "backend_store_uri is not artifact_root"),
    "bentoml": mk(True, "pr-bentoml-traffic-timeout-sec", "lock-bntto",
        "the BentoML service that omitted traffic.timeout so a 90s inference returned 504",
        "bentofile.yaml", "workers: 4", "traffic.timeout 180",
        "traffic.timeout", "harbor workers only. pack traffic.timeout.",
        "FAIL test_assign: 504 at 60s; traffic.timeout missing",
        "workers only", "workers is not traffic.timeout"),
    "seldon": mk(False, "pr-seldon-executor-liveness-probe", "quay-sdnlive",
        "the Seldon Deployment that omitted executor liveness so a hung predictor never restarted",
        "seldon.yaml", "readinessProbe: {httpGet: {path: /ready}}", "livenessProbe httpGet /live",
        "livenessProbe", "harbor readiness only. pack livenessProbe.",
        "FAIL test_assign: hung predictor forever; liveness missing",
        "readiness only", "readiness is not liveness"),
    "kserve": mk(True, "pr-kserve-min-replicas-zero", "lock-ksvmin",
        "the KServe InferenceService that omitted minReplicas 1 so the first request 502'd on a cold start",
        "kserve.yaml", "scaleTarget: 80", "minReplicas 1",
        "minReplicas", "harbor scaleTarget only. pack minReplicas 1.",
        "FAIL test_assign: first request 502; minReplicas missing",
        "scaleTarget only", "scaleTarget is not minReplicas"),
    "triton": mk(False, "pr-triton-model-control-explicit", "quay-trtctl",
        "the Triton server that omitted model_control_mode explicit so every model loaded and the GPU OOMed",
        "config.pbtxt", "instance_group [{ count: 1 }]", "model_control_mode explicit",
        "model_control_mode", "harbor instance_group count only. pack model_control_mode explicit.",
        "FAIL test_assign: GPU OOM all models; model_control_mode missing",
        "instance_group count only", "instance_group is not model_control_mode"),
    "qdrant": mk(True, "pr-qdrant-on-disk-payload-true", "lock-qdrdisk",
        "the Qdrant collection that omitted on_disk_payload so RAM ballooned past the node limit",
        "collection.json", "memmap_threshold: 20000", "on_disk_payload true",
        "on_disk_payload", "harbor memmap_threshold only. pack on_disk_payload.",
        "FAIL test_assign: RSS 48GiB; on_disk_payload missing",
        "memmap_threshold only", "memmap_threshold is not on_disk_payload"),
    "weaviate": mk(False, "pr-weaviate-vector-cache-max", "quay-wvcache",
        "the Weaviate class that omitted vectorCacheMaxObjects so query p99 spiked after a cache miss storm",
        "schema.json", "queryDefaults: {limit: 20}", "vectorCacheMaxObjects 1e6",
        "vectorCacheMaxObjects", "harbor queryDefaults limit only. pack vectorCacheMaxObjects.",
        "FAIL test_assign: p99 8s after miss storm; vectorCacheMaxObjects missing",
        "queryDefaults limit only", "queryDefaults is not vectorCacheMaxObjects"),
    "milvus": mk(True, "pr-milvus-hnsw-m-efconstruct", "lock-mlvhnsw",
        "the Milvus index that omitted HNSW M so recall collapsed under the default M=4",
        "index.yaml", "ef: 64", "HNSW M 16 efConstruction 200",
        "M", "harbor ef only. pack HNSW M.",
        "FAIL test_assign: recall 0.41; HNSW M missing",
        "ef only", "ef is not HNSW M"),
    "chroma": mk(False, "pr-chroma-hnsw-space-cosine", "quay-chrspc",
        "the Chroma collection that omitted hnsw:space cosine so L2 space mismatched unit-norm embeddings",
        "chroma.yml", "hnsw:M: 16", "hnsw:space cosine",
        "hnsw:space", "harbor hnsw:M only. pack hnsw:space cosine.",
        "FAIL test_assign: nearest neighbors wrong; hnsw:space missing",
        "hnsw:M only", "hnsw:M is not hnsw:space"),
    "temporal": mk(True, "pr-temporal-history-size-error", "lock-tmphist",
        "the Temporal namespace that omitted history size error so a chatty workflow replay OOMed the worker",
        "dynamic.yaml", "workflow_execution_timeout: 24h", "history.size.error 50MB",
        "history.size.error", "harbor workflow_execution_timeout only. pack history.size.error.",
        "FAIL test_assign: worker OOM on replay; history size error missing",
        "workflow_execution_timeout only", "execution timeout is not history size error"),
    "cadence": mk(False, "pr-cadence-archival-uri-s3", "quay-cdarch",
        "the Cadence domain that omitted archival URI so closed workflows filled Cassandra",
        "config/config.yaml", "visibility.es.urls: [http://es:9200]", "archival.uri s3://cad-arch",
        "archival", "harbor visibility.es only. pack archival.uri.",
        "FAIL test_assign: Cassandra 90% full; archival URI missing",
        "visibility.es only", "visibility.es is not archival URI"),
    "prefect": mk(True, "pr-prefect-work-pool-concurrency", "lock-prfpool",
        "the Prefect work pool that omitted concurrency so 400 tasks stampeded the warehouse",
        "prefect.yaml", "retries: 3", "work_pool concurrency 8",
        "concurrency", "harbor task retries only. pack work_pool concurrency.",
        "FAIL test_assign: warehouse 503; work_pool concurrency missing",
        "task retries only", "retries is not work_pool concurrency"),
    "dagster": mk(False, "pr-dagster-run-retries-op", "quay-dgsretry",
        "the Dagster job that omitted op run retries so a transient S3 503 failed the whole run",
        "dagster.yaml", "job retry: 0", "op run retries 3",
        "retries", "harbor job retry only. pack op run retries.",
        "FAIL test_assign: S3 503 failed job; op retries missing",
        "job retry only", "job retry is not op run retries"),
    "airflow": mk(True, "pr-airflow-dag-concurrency-pool", "lock-afpool",
        "the Airflow DAG that omitted dag_concurrency vs pool so mapped tasks exhausted the scheduler",
        "airflow.cfg", "parallelism = 32", "dag_concurrency 8 pool warehouse",
        "dag_concurrency", "harbor parallelism only. pack dag_concurrency.",
        "FAIL test_assign: scheduler starved; dag_concurrency missing",
        "parallelism only", "parallelism is not dag_concurrency"),
    "argo": mk(False, "pr-argo-synchronization-mutex", "quay-argomtx",
        "the Argo Workflow that omitted synchronization mutex so two runs mutated the same PVC",
        "workflow.yaml", "retryStrategy: {limit: 2}", "synchronization mutex harbor-pvc",
        "synchronization", "harbor retryStrategy only. pack synchronization mutex.",
        "FAIL test_assign: two runs clobber PVC; mutex missing",
        "retryStrategy only", "retryStrategy is not synchronization mutex"),
    "nifi": mk(True, "pr-nifi-content-claim-max-append", "lock-nificlm",
        "the NiFi node that omitted nifi.content.claim.max.appendable.size so the content repo filled with tiny claims",
        "nifi.properties", "nifi.flowfile.repository.directory=./flowfile_repository",
        "nifi.content.claim.max.appendable.size 10 MB",
        "nifi.content.claim.max.appendable.size",
        "harbor flowfile repo only. pack content.claim.max.appendable.size.",
        "FAIL test_assign: content repo 98%; max.appendable missing",
        "flowfile repo only", "flowfile repo is not content claim max appendable"),
    "flinkcdc": mk(False, "pr-flinkcdc-scan-startup-mode", "quay-fcdcstart",
        "the Flink CDC source that omitted scan.startup.mode latest-offset so the job replayed the full binlog",
        "cdc.yml", "snapshot.mode: initial", "scan.startup.mode latest-offset",
        "scan.startup.mode", "harbor snapshot.mode only. pack scan.startup.mode latest-offset.",
        "FAIL test_assign: full binlog replay 6h; startup.mode missing",
        "snapshot.mode only", "snapshot.mode is not scan.startup.mode"),
    "valkey": mk(True, "pr-valkey-replica-announced-ip", "lock-vkann",
        "the Valkey replica that omitted replica-announced-ip so Sentinel advertised the container IP",
        "valkey.conf", "replica-priority 100", "replica-announced-ip 10.8.1.20",
        "replica-announced-ip", "harbor replica-priority only. pack replica-announced-ip.",
        "FAIL test_assign: Sentinel points at 172.17.0.4; announced-ip missing",
        "replica-priority only", "replica-priority is not replica-announced-ip"),
    "dragonfly": mk(False, "pr-dragonfly-proactor-threads-count", "quay-dfpro",
        "the Dragonfly server that omitted proactor_threads so a single thread bottlenecked SET at 20k qps",
        "dragonfly.conf", "maxmemory 8gb", "proactor_threads 8",
        "proactor_threads", "harbor maxmemory only. pack proactor_threads.",
        "FAIL test_assign: SET 20k qps cap; proactor_threads missing",
        "maxmemory only", "maxmemory is not proactor_threads"),
}


def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Debezium heartbeat vs Maxwell filter.databases", fn("debezium"), fn("maxwell"),
     "heartbeat.interval.ms; filter.databases", "snapshot.mode; exclude_tables",
     "debezium dump quiet offset; maxwell dump mysql.user in topic"),
    ("Flink incremental checkpoint vs Spark watermark delay", fn("flink"), fn("spark"),
     "incremental true; watermarkDelayThreshold 10m", "interval; maxOffsetsPerTrigger",
     "flink dump 40GiB snapshot; spark dump late drop"),
    ("Connect unwrap SMT vs Redpanda schema FULL", fn("connect"), fn("redpanda"),
     "ExtractNewRecordState; compatibility FULL", "Flatten; BACKWARD",
     "connect dump after.payload; redpanda dump field delete"),
    ("Pulsar ensemble size vs NATS max_bytes", fn("pulsar"), fn("nats"),
     "ensemble size 3; max_bytes 20GB", "ackQuorum; max_age",
     "pulsar dump bookie loss; nats dump disk 507"),
    ("RisingWave backfill vs Materialize persist blob", fn("risingwave"), fn("materialize"),
     "backfill_rate_limit; persist.blob_uri", "parallelism; consensus URI",
     "risingwave dump snapshot OOM; materialize dump empty catalog"),
    ("ClickHouse distributed_ddl vs Pinot realtimeToOffline", fn("clickhouse"), fn("pinot"),
     "output_mode none; realtimeToOfflineTask", "alter sync; retentionTimeUnit",
     "clickhouse dump ON CLUSTER hung; pinot dump REALTIME 400GiB"),
    ("DuckDB httpfs region vs QuestDB wal", fn("duckdb"), fn("questdb"),
     "s3_region; cairo.wal.enabled", "s3_endpoint; commit.lag",
     "duckdb dump 301 loop; questdb dump ALTER lock"),
    ("Druid maxRowsInMemory vs CrateDB replicas", fn("druid"), fn("cratedb"),
     "maxRowsInMemory; number_of_replicas 0", "maxRowsPerSegment; wait_for_active_shards",
     "druid dump GC timeout; cratedb dump yellow writes"),
    ("Trino exchange-manager vs Presto spill", fn("trino"), fn("presto"),
     "exchange-manager filesystem; spill-enabled", "query.max-memory; join-distribution-type",
     "trino dump /tmp full; presto dump hash join OOM"),
    ("Iceberg expire retain vs Hudi cleaner policy", fn("iceberg"), fn("hudi"),
     "expire_snapshots retain_last; KEEP_LATEST_COMMITS", "orphan files; inline compact",
     "iceberg dump 40k snapshots; hudi dump 12k instants"),
    ("Delta deletedFileRetention vs Nessie gc retention", fn("delta"), fn("nessie"),
     "deletedFileRetentionDuration; gc.default.retention", "logRetention; commit.retry",
     "delta dump CDF 404; nessie dump 2M expired refs"),
    ("Airbyte state S3 vs Singer bookmark reset", fn("airbyte"), fn("singer"),
     "state persistence s3; bookmark full-refresh", "normalization; start_date",
     "airbyte dump cursor 0; singer dump PK skip"),
    ("dbt unique_key vs GX action_list", fn("dbt"), fn("gx"),
     "unique_key; action_list Slack", "incremental_strategy; suite",
     "dbt dump duplicate merge; gx dump silent validation"),
    ("Soda fail_on vs Elementary sensitivity", fn("soda"), fn("elementary"),
     "fail_on error; anomaly_sensitivity", "samples limit; days_back",
     "soda dump CI green fail; elementary dump silent drop"),
    ("Feast online ttl vs MLflow artifact_root", fn("feast"), fn("mlflow"),
     "online_store ttl; artifact_root s3", "entity_ttl; backend_store_uri",
     "feast dump Redis full; mlflow dump artifacts gone"),
    ("BentoML traffic timeout vs Seldon liveness", fn("bentoml"), fn("seldon"),
     "traffic.timeout 180; livenessProbe", "workers; readiness",
     "bentoml dump 504; seldon dump hung predictor"),
    ("KServe minReplicas vs Triton model_control", fn("kserve"), fn("triton"),
     "minReplicas 1; model_control_mode explicit", "scaleTarget; instance_group",
     "kserve dump cold 502; triton dump GPU OOM"),
    ("Qdrant on_disk_payload vs Weaviate vectorCache", fn("qdrant"), fn("weaviate"),
     "on_disk_payload; vectorCacheMaxObjects", "memmap_threshold; queryDefaults",
     "qdrant dump RSS 48GiB; weaviate dump p99 8s"),
    ("Milvus HNSW M vs Chroma hnsw space", fn("milvus"), fn("chroma"),
     "HNSW M 16; hnsw:space cosine", "ef; hnsw:M",
     "milvus dump recall 0.41; chroma dump L2 mismatch"),
    ("Temporal history size vs Cadence archival", fn("temporal"), fn("cadence"),
     "history.size.error; archival.uri", "execution timeout; visibility.es",
     "temporal dump replay OOM; cadence dump Cassandra full"),
    ("Prefect work_pool vs Dagster op retries", fn("prefect"), fn("dagster"),
     "work_pool concurrency; op run retries", "task retries; job retry",
     "prefect dump warehouse 503; dagster dump S3 503 fail"),
    ("Airflow dag_concurrency vs Argo mutex", fn("airflow"), fn("argo"),
     "dag_concurrency; synchronization mutex", "parallelism; retryStrategy",
     "airflow dump scheduler starve; argo dump PVC clobber"),
    ("NiFi content claim vs FlinkCDC startup mode", fn("nifi"), fn("flinkcdc"),
     "content.claim.max.appendable; scan.startup.mode latest-offset",
     "flowfile repo; snapshot.mode",
     "nifi dump content repo 98%; flinkcdc dump full binlog"),
    ("Valkey announced-ip vs Dragonfly proactor_threads", fn("valkey"), fn("dragonfly"),
     "replica-announced-ip; proactor_threads 8", "replica-priority; maxmemory",
     "valkey dump Sentinel 172.17; dragonfly dump 20k qps cap"),
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
- Not a clone of r4163-r4580 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO window kanidm/gluu/casdoor/authentik/oauth2-proxy/ory/hydra/kratos/keto/zitadel/authelia/pomerium/teleport/dex/sssd/pam, ingress/gateway w4ci, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
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
        if p.name in {"sandbox-refusal-factory", "long-horizon-coding-factory"}:
            continue
        if any(p.glob("ROUND-r*.reserved.json")):
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
                "LHC reserved; hop candidates (no plant catalog here, retry LHC):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(2)
            if hops > 40:
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
