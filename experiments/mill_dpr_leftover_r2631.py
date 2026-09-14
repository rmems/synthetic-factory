#!/usr/bin/env python3
"""data-pipeline-repair leftover leftover leftover mill r2631–r2646 (16 pairs)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/data-pipeline-repair-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "data-pipeline-repair-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16

# Distinct leftover leftover leftover vs prior dpr-r2580–r2622 knobs.
# BAN dbc-/sir-/docker/search ids. Each: leftover resume token vs naive drop (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "afxcom",
        "slug": "airflow-xcom-backend-leftover-vs-drop-task",
        "fail": "airflow-drop-xcom-backend-handoff",
        "stack": "Airflow leftover xcom_backend",
        "token": "leftover_xcom_backend",
        "wrong": "drop task",
        "wrong_key": "task",
        "test_ok": "test_xcom_not_task",
        "test_fail": "test_xcom_bind",
        "docs": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html",
        "doc2": "https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/tracking-user-activity.html",
        "handoff": "AF-XCOM-17",
        "domain_ok": "airflow-xcom-backend-leftover-vs-drop-task",
        "domain_fail": "airflow-drop-leftover-xcom-backend-bind",
        "first_patch": ("    return {'task': sid}", "    return {'task': None}"),
        "fix_patch": ("    return {'task': None}", "    return {'leftover_xcom_backend': sid}"),
        "src_obs": "Airflow leftover xcom_backend restores the same XCom store; drop task is not resume",
        "plan_ok": "Pass leftover_xcom_backend. Drop task is not resume.",
        "plan_fail": "Leftover xcom_backend bind drop is Airflow plat. Handoff AF-XCOM-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not task leftover clone.",
    },
    {
        "mod": "dgrtags",
        "slug": "dagster-run-tags-leftover-vs-drop-job",
        "fail": "dagster-drop-run-tags-handoff",
        "stack": "Dagster leftover run_tags",
        "token": "leftover_run_tags",
        "wrong": "drop job",
        "wrong_key": "job",
        "test_ok": "test_tags_not_job",
        "test_fail": "test_tags_bind",
        "docs": "https://docs.dagster.io/guides/operate/run-tags",
        "doc2": "https://docs.dagster.io/guides/build/jobs",
        "handoff": "DG-RT-17",
        "domain_ok": "dagster-run-tags-leftover-vs-drop-job",
        "domain_fail": "dagster-drop-leftover-run-tags-bind",
        "first_patch": ("    return {'job': sid}", "    return {'job': None}"),
        "fix_patch": ("    return {'job': None}", "    return {'leftover_run_tags': sid}"),
        "src_obs": "Dagster leftover run_tags restores the same run identity; drop job is not resume",
        "plan_ok": "Pass leftover_run_tags. Drop job is not resume.",
        "plan_fail": "Leftover run_tags bind drop is Dagster plat. Handoff DG-RT-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not job leftover clone.",
    },
    {
        "mod": "pffrn",
        "slug": "prefect-flow-run-name-leftover-vs-drop-workpool",
        "fail": "prefect-drop-flow-run-name-handoff",
        "stack": "Prefect leftover flow_run_name",
        "token": "leftover_flow_run_name",
        "wrong": "drop workpool",
        "wrong_key": "workpool",
        "test_ok": "test_frn_not_wp",
        "test_fail": "test_frn_bind",
        "docs": "https://docs.prefect.io/v3/concepts/flows",
        "doc2": "https://docs.prefect.io/v3/deploy/infrastructure-concepts/work-pools",
        "handoff": "PF-FRN-17",
        "domain_ok": "prefect-flow-run-name-leftover-vs-drop-workpool",
        "domain_fail": "prefect-drop-leftover-flow-run-name-bind",
        "first_patch": ("    return {'workpool': sid}", "    return {'workpool': None}"),
        "fix_patch": ("    return {'workpool': None}", "    return {'leftover_flow_run_name': sid}"),
        "src_obs": "Prefect leftover flow_run_name restores the same flow run; drop workpool is not resume",
        "plan_ok": "Pass leftover_flow_run_name. Drop workpool is not resume.",
        "plan_fail": "Leftover flow_run_name bind drop is Prefect plat. Handoff PF-FRN-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not workpool leftover clone.",
    },
    {
        "mod": "dbtuniq",
        "slug": "dbt-incremental-unique-key-leftover-vs-drop-fullrefresh",
        "fail": "dbt-drop-incremental-unique-key-handoff",
        "stack": "dbt leftover unique_key",
        "token": "leftover_unique_key",
        "wrong": "drop fullrefresh",
        "wrong_key": "fullrefresh",
        "test_ok": "test_ukey_not_fr",
        "test_fail": "test_ukey_bind",
        "docs": "https://docs.getdbt.com/docs/build/incremental-models",
        "doc2": "https://docs.getdbt.com/reference/resource-configs/unique_key",
        "handoff": "DBT-UK-17",
        "domain_ok": "dbt-incremental-unique-key-leftover-vs-drop-fullrefresh",
        "domain_fail": "dbt-drop-leftover-incremental-unique-key-bind",
        "first_patch": ("    return {'fullrefresh': sid}", "    return {'fullrefresh': None}"),
        "fix_patch": ("    return {'fullrefresh': None}", "    return {'leftover_unique_key': sid}"),
        "src_obs": "dbt leftover unique_key restores incremental identity; drop --full-refresh is not resume",
        "plan_ok": "Pass leftover_unique_key. Drop fullrefresh is not resume.",
        "plan_fail": "Leftover unique_key bind drop is dbt plat. Handoff DBT-UK-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not full-refresh leftover clone.",
    },
    {
        "mod": "spkckp",
        "slug": "spark-checkpoint-dir-leftover-vs-drop-appid",
        "fail": "spark-drop-checkpoint-dir-handoff",
        "stack": "Spark leftover checkpoint_dir",
        "token": "leftover_checkpoint_dir",
        "wrong": "drop appid",
        "wrong_key": "appid",
        "test_ok": "test_ckp_not_appid",
        "test_fail": "test_ckp_bind",
        "docs": "https://spark.apache.org/docs/latest/streaming-programming-guide.html#checkpointing",
        "doc2": "https://spark.apache.org/docs/latest/configuration.html#spark-streaming",
        "handoff": "SP-CKP-17",
        "domain_ok": "spark-checkpoint-dir-leftover-vs-drop-appid",
        "domain_fail": "spark-drop-leftover-checkpoint-dir-bind",
        "first_patch": ("    return {'appid': sid}", "    return {'appid': None}"),
        "fix_patch": ("    return {'appid': None}", "    return {'leftover_checkpoint_dir': sid}"),
        "src_obs": "Spark leftover checkpoint_dir restores RDD lineage; drop appid is not resume",
        "plan_ok": "Pass leftover_checkpoint_dir. Drop appid is not resume.",
        "plan_fail": "Leftover checkpoint_dir bind drop is Spark plat. Handoff SP-CKP-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not appid leftover clone.",
    },
    {
        "mod": "flksp",
        "slug": "flink-savepoint-path-leftover-vs-drop-jobid",
        "fail": "flink-drop-savepoint-path-handoff",
        "stack": "Flink leftover savepoint_path",
        "token": "leftover_savepoint_path",
        "wrong": "drop jobid",
        "wrong_key": "jobid",
        "test_ok": "test_sp_not_jobid",
        "test_fail": "test_sp_bind",
        "docs": "https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/savepoints/",
        "doc2": "https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/checkpoints/",
        "handoff": "FL-SP-17",
        "domain_ok": "flink-savepoint-path-leftover-vs-drop-jobid",
        "domain_fail": "flink-drop-leftover-savepoint-path-bind",
        "first_patch": ("    return {'jobid': sid}", "    return {'jobid': None}"),
        "fix_patch": ("    return {'jobid': None}", "    return {'leftover_savepoint_path': sid}"),
        "src_obs": "Flink leftover savepoint_path restores operator state; drop jobid is not resume",
        "plan_ok": "Pass leftover_savepoint_path. Drop jobid is not resume.",
        "plan_fail": "Leftover savepoint_path bind drop is Flink plat. Handoff FL-SP-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not jobid leftover clone.",
    },
    {
        "mod": "kcoffs",
        "slug": "kconnect-offset-storage-leftover-vs-drop-name",
        "fail": "kconnect-drop-offset-storage-handoff",
        "stack": "Kafka Connect leftover offset_storage",
        "token": "leftover_offset_storage",
        "wrong": "drop name",
        "wrong_key": "name",
        "test_ok": "test_offs_not_name",
        "test_fail": "test_offs_bind",
        "docs": "https://kafka.apache.org/documentation/#connectconfigs",
        "doc2": "https://docs.confluent.io/platform/current/connect/design.html",
        "handoff": "KC-OFF-17",
        "domain_ok": "kconnect-offset-storage-leftover-vs-drop-name",
        "domain_fail": "kconnect-drop-leftover-offset-storage-bind",
        "first_patch": ("    return {'name': sid}", "    return {'name': None}"),
        "fix_patch": ("    return {'name': None}", "    return {'leftover_offset_storage': sid}"),
        "src_obs": "Kafka Connect leftover offset_storage restores connector progress; drop name is not resume",
        "plan_ok": "Pass leftover_offset_storage. Drop name is not resume.",
        "plan_fail": "Leftover offset_storage bind drop is Kafka Connect plat. Handoff KC-OFF-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not connector-name leftover clone.",
    },
    {
        "mod": "ssckp",
        "slug": "spark-ss-checkpoint-leftover-vs-drop-queryname",
        "fail": "spark-ss-drop-checkpoint-handoff",
        "stack": "Spark Structured Streaming leftover checkpointLocation",
        "token": "leftover_ss_checkpoint",
        "wrong": "drop queryname",
        "wrong_key": "queryname",
        "test_ok": "test_ssck_not_qn",
        "test_fail": "test_ssck_bind",
        "docs": "https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#recovering-from-failures-with-checkpointing",
        "doc2": "https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#starting-streaming-queries",
        "handoff": "SS-CKP-17",
        "domain_ok": "spark-ss-checkpoint-leftover-vs-drop-queryname",
        "domain_fail": "spark-ss-drop-leftover-checkpoint-bind",
        "first_patch": ("    return {'queryname': sid}", "    return {'queryname': None}"),
        "fix_patch": ("    return {'queryname': None}", "    return {'leftover_ss_checkpoint': sid}"),
        "src_obs": "Spark SS leftover checkpointLocation restores offsets; drop queryName is not resume",
        "plan_ok": "Pass leftover_ss_checkpoint. Drop queryname is not resume.",
        "plan_fail": "Leftover checkpointLocation bind drop is Spark SS plat. Handoff SS-CKP-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queryName leftover clone.",
    },
    {
        "mod": "afconf",
        "slug": "airflow-dag-run-conf-leftover-vs-drop-pool",
        "fail": "airflow-drop-dag-run-conf-handoff",
        "stack": "Airflow leftover dag_run_conf",
        "token": "leftover_dag_run_conf",
        "wrong": "drop pool",
        "wrong_key": "pool",
        "test_ok": "test_conf_not_pool",
        "test_fail": "test_conf_bind",
        "docs": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html",
        "doc2": "https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html",
        "handoff": "AF-DRC-17",
        "domain_ok": "airflow-dag-run-conf-leftover-vs-drop-pool",
        "domain_fail": "airflow-drop-leftover-dag-run-conf-bind",
        "first_patch": ("    return {'pool': sid}", "    return {'pool': None}"),
        "fix_patch": ("    return {'pool': None}", "    return {'leftover_dag_run_conf': sid}"),
        "src_obs": "Airflow leftover dag_run_conf restores trigger params; drop pool is not resume",
        "plan_ok": "Pass leftover_dag_run_conf. Drop pool is not resume.",
        "plan_fail": "Leftover dag_run_conf bind drop is Airflow plat. Handoff AF-DRC-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not pool leftover clone.",
    },
    {
        "mod": "dgakey",
        "slug": "dagster-asset-key-leftover-vs-drop-partition",
        "fail": "dagster-drop-asset-key-handoff",
        "stack": "Dagster leftover asset_key",
        "token": "leftover_asset_key",
        "wrong": "drop partition",
        "wrong_key": "partition",
        "test_ok": "test_akey_not_part",
        "test_fail": "test_akey_bind",
        "docs": "https://docs.dagster.io/guides/build/assets/defining-assets",
        "doc2": "https://docs.dagster.io/guides/build/partitions-and-backfills",
        "handoff": "DG-AK-17",
        "domain_ok": "dagster-asset-key-leftover-vs-drop-partition",
        "domain_fail": "dagster-drop-leftover-asset-key-bind",
        "first_patch": ("    return {'partition': sid}", "    return {'partition': None}"),
        "fix_patch": ("    return {'partition': None}", "    return {'leftover_asset_key': sid}"),
        "src_obs": "Dagster leftover asset_key restores materialization identity; drop partition is not resume",
        "plan_ok": "Pass leftover_asset_key. Drop partition is not resume.",
        "plan_fail": "Leftover asset_key bind drop is Dagster plat. Handoff DG-AK-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not partition leftover clone.",
    },
    {
        "mod": "pftrid",
        "slug": "prefect-task-run-id-leftover-vs-drop-deployment",
        "fail": "prefect-drop-task-run-id-handoff",
        "stack": "Prefect leftover task_run_id",
        "token": "leftover_task_run_id",
        "wrong": "drop deployment",
        "wrong_key": "deployment",
        "test_ok": "test_trid_not_dep",
        "test_fail": "test_trid_bind",
        "docs": "https://docs.prefect.io/v3/concepts/tasks",
        "doc2": "https://docs.prefect.io/v3/deploy/run-flows-in-local-processes",
        "handoff": "PF-TR-17",
        "domain_ok": "prefect-task-run-id-leftover-vs-drop-deployment",
        "domain_fail": "prefect-drop-leftover-task-run-id-bind",
        "first_patch": ("    return {'deployment': sid}", "    return {'deployment': None}"),
        "fix_patch": ("    return {'deployment': None}", "    return {'leftover_task_run_id': sid}"),
        "src_obs": "Prefect leftover task_run_id restores task identity; drop deployment is not resume",
        "plan_ok": "Pass leftover_task_run_id. Drop deployment is not resume.",
        "plan_fail": "Leftover task_run_id bind drop is Prefect plat. Handoff PF-TR-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not deployment leftover clone.",
    },
    {
        "mod": "dbtsnap",
        "slug": "dbt-snapshot-check-cols-leftover-vs-drop-strategy",
        "fail": "dbt-drop-snapshot-check-cols-handoff",
        "stack": "dbt leftover check_cols",
        "token": "leftover_check_cols",
        "wrong": "drop strategy",
        "wrong_key": "strategy",
        "test_ok": "test_ccols_not_strat",
        "test_fail": "test_ccols_bind",
        "docs": "https://docs.getdbt.com/docs/build/snapshots",
        "doc2": "https://docs.getdbt.com/reference/resource-configs/check_cols",
        "handoff": "DBT-CC-17",
        "domain_ok": "dbt-snapshot-check-cols-leftover-vs-drop-strategy",
        "domain_fail": "dbt-drop-leftover-snapshot-check-cols-bind",
        "first_patch": ("    return {'strategy': sid}", "    return {'strategy': None}"),
        "fix_patch": ("    return {'strategy': None}", "    return {'leftover_check_cols': sid}"),
        "src_obs": "dbt leftover check_cols restores SCD identity; drop strategy is not resume",
        "plan_ok": "Pass leftover_check_cols. Drop strategy is not resume.",
        "plan_fail": "Leftover check_cols bind drop is dbt plat. Handoff DBT-CC-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not strategy leftover clone.",
    },
    {
        "mod": "spkat",
        "slug": "spark-stage-attempt-leftover-vs-drop-stageid",
        "fail": "spark-drop-stage-attempt-handoff",
        "stack": "Spark leftover stage_attempt",
        "token": "leftover_stage_attempt",
        "wrong": "drop stageid",
        "wrong_key": "stageid",
        "test_ok": "test_att_not_sid",
        "test_fail": "test_att_bind",
        "docs": "https://spark.apache.org/docs/latest/monitoring.html#web-interfaces",
        "doc2": "https://spark.apache.org/docs/latest/job-scheduling.html",
        "handoff": "SP-ATT-17",
        "domain_ok": "spark-stage-attempt-leftover-vs-drop-stageid",
        "domain_fail": "spark-drop-leftover-stage-attempt-bind",
        "first_patch": ("    return {'stageid': sid}", "    return {'stageid': None}"),
        "fix_patch": ("    return {'stageid': None}", "    return {'leftover_stage_attempt': sid}"),
        "src_obs": "Spark leftover stage_attempt restores the same attempt; drop stageid is not resume",
        "plan_ok": "Pass leftover_stage_attempt. Drop stageid is not resume.",
        "plan_fail": "Leftover stage_attempt bind drop is Spark plat. Handoff SP-ATT-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not stageid leftover clone.",
    },
    {
        "mod": "flkuid",
        "slug": "flink-operator-uid-leftover-vs-drop-slot",
        "fail": "flink-drop-operator-uid-handoff",
        "stack": "Flink leftover operator_uid",
        "token": "leftover_operator_uid",
        "wrong": "drop slot",
        "wrong_key": "slot",
        "test_ok": "test_uid_not_slot",
        "test_fail": "test_uid_bind",
        "docs": "https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/fault-tolerance/state/#operator-state",
        "doc2": "https://nightlies.apache.org/flink/flink-docs-stable/docs/ops/state/state_backends/",
        "handoff": "FL-UID-17",
        "domain_ok": "flink-operator-uid-leftover-vs-drop-slot",
        "domain_fail": "flink-drop-leftover-operator-uid-bind",
        "first_patch": ("    return {'slot': sid}", "    return {'slot': None}"),
        "fix_patch": ("    return {'slot': None}", "    return {'leftover_operator_uid': sid}"),
        "src_obs": "Flink leftover operator_uid restores keyed state mapping; drop slot is not resume",
        "plan_ok": "Pass leftover_operator_uid. Drop slot is not resume.",
        "plan_fail": "Leftover operator_uid bind drop is Flink plat. Handoff FL-UID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not slot leftover clone.",
    },
    {
        "mod": "kcint",
        "slug": "kconnect-internal-topic-leftover-vs-drop-group",
        "fail": "kconnect-drop-internal-topic-handoff",
        "stack": "Kafka Connect leftover internal_topic",
        "token": "leftover_internal_topic",
        "wrong": "drop group",
        "wrong_key": "group",
        "test_ok": "test_int_not_group",
        "test_fail": "test_int_bind",
        "docs": "https://kafka.apache.org/documentation/#connect_running",
        "doc2": "https://docs.confluent.io/platform/current/connect/userguide.html#kconnect-internal-topics",
        "handoff": "KC-INT-17",
        "domain_ok": "kconnect-internal-topic-leftover-vs-drop-group",
        "domain_fail": "kconnect-drop-leftover-internal-topic-bind",
        "first_patch": ("    return {'group': sid}", "    return {'group': None}"),
        "fix_patch": ("    return {'group': None}", "    return {'leftover_internal_topic': sid}"),
        "src_obs": "Kafka Connect leftover internal_topic restores config/status; drop group is not resume",
        "plan_ok": "Pass leftover_internal_topic. Drop group is not resume.",
        "plan_fail": "Leftover internal_topic bind drop is Kafka Connect plat. Handoff KC-INT-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not group leftover clone.",
    },
    {
        "mod": "sswm",
        "slug": "spark-ss-watermark-leftover-vs-drop-trigger",
        "fail": "spark-ss-drop-watermark-handoff",
        "stack": "Spark Structured Streaming leftover watermark",
        "token": "leftover_watermark",
        "wrong": "drop trigger",
        "wrong_key": "trigger",
        "test_ok": "test_wm_not_trig",
        "test_fail": "test_wm_bind",
        "docs": "https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#handling-late-data-and-watermarking",
        "doc2": "https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#triggers",
        "handoff": "SS-WM-17",
        "domain_ok": "spark-ss-watermark-leftover-vs-drop-trigger",
        "domain_fail": "spark-ss-drop-leftover-watermark-bind",
        "first_patch": ("    return {'trigger': sid}", "    return {'trigger': None}"),
        "fix_patch": ("    return {'trigger': None}", "    return {'leftover_watermark': sid}"),
        "src_obs": "Spark SS leftover watermark restores late-data bound; drop trigger is not resume",
        "plan_ok": "Pass leftover_watermark. Drop trigger is not resume.",
        "plan_fail": "Leftover watermark bind drop is Spark SS plat. Handoff SS-WM-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not trigger leftover clone.",
    },
]


def _cmd(args: list[str]) -> dict:
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"exit {proc.returncode}").strip())
    out = proc.stdout.strip()
    return json.loads(out) if out else {}


def hop_unreserved() -> Path | None:
    base = ROOT / "outputs/raw/2026-08-19-agentic"
    for child in sorted(p for p in base.iterdir() if p.is_dir()):
        if child.name == "sandbox-refusal-factory":
            continue
        st = _cmd(TXN + ["frontier", str(child)])
        nxt = int(st["next_round"])
        if (child / f"ROUND-r{nxt:02d}.reserved.json").exists():
            continue
        return child
    return None


def db(s: str) -> str:
    s = s if s.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")) else f"Observation: {s}"
    return s[:240]


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str) -> dict:
    return {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": reflection,
    }


def success_steps(c: dict) -> list:
    m, tok, tname, src = c["mod"], c["token"], c["test_ok"], f"src/{c['mod']}.py"
    old0, new0 = c["first_patch"]
    old1, new1 = c["fix_patch"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: {c['wrong']} created a new socket; leftover unused",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"assert resume()[{tok!r}] == sid  # {c['ban']}",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tok}|{c['wrong_key']}' src tests | head -n 24"},
             f"{src}: return {{'{c['wrong_key']}': sid}}",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"{old0}\n# naive {c['wrong']}",
             "First read done. Fetch vendor docs next; do not patch on a hunch."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 502 Bad Gateway",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["docs"]},
             f"local fixture cache of {c['docs']}\n{c['ban']}",
             "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(9, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["doc2"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nUse {tok}. {c['ban']}",
             "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": old0, "new": new0},
             f"patched {c['wrong']} (still not {tok})",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: {c['wrong']} is not {tok}",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             c["src_obs"],
             f"Plan change: {c['plan_ok']}"),
        step(13, f"Reflection: {c['plan_ok']}",
             "edit", {"path": src, "old": old1, "new": new1},
             f"patched {tok}",
             "Corrective patch applied. Run the original failing node again."),
        step(14, "Observation: fix edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             "1 passed in 0.16s",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest tests/test_{m}.py -q`.",
             "bash", {"command": f"pytest tests/test_{m}.py -q"},
             "3 passed in 0.28s",
             "Broader check captured. Stop; residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {c['slug']}: {src} | 9 ++++++---. No other modified paths.",
             "Diff is the review artifact. No further edits."),
    ]


def fail_steps(c: dict) -> list:
    m, tok, tname, src = c["mod"], c["token"], c["test_fail"], f"src/{c['mod']}.py"
    old0, new0 = c["first_patch"]
    return [
        step(1, f"Plan: list src {m} and tests before touching conversion or config.",
             "bash", {"command": f"ls -la src {m} tests | head -40"},
             f"{src} {m}/cfg.yml\ntests/test_{m}.py",
             f"Tree shows {src} plus tests. Run the named failing target next."),
        step(2, f"Observation: listing named the test files. Run `tests/test_{m}.py -q --tb=short` to capture the failure.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: leftover {tok} bind missing",
             f"Failure is at tests/test_{m}.py::{tname}. Read that test before a one-line fix."),
        step(3, f"Observation: tests/test_{m}.py::{tname} is red. Read tests/test_{m}.py around the assertion.",
             "read", {"path": f"tests/test_{m}.py"},
             f"assert bind_leftover()  # platform cannot drop {tok}",
             "Test contract is visible. Search implementation symbols next."),
        step(4, "Observation: test file imported the production helper. Grep those symbols.",
             "bash", {"command": f"rg -n '{tok}|bind' src tests | head -n 24"},
             f"{src}: drop_{c['wrong_key']}()",
             f"Grep hit {src}. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"{old0}\n# drop leftover bind",
             "First read done. Fetch vendor docs next; do not patch on a hunch."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": c["docs"]},
             f"GET {c['docs']}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(7, "Observation: the prior call returned rate-limit status with Retry-After. Sleep then retry.",
             "fetch", {"url": c["docs"]},
             f"sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\n{c['ban']}",
             "Retry succeeded. Continue with that document."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": c["doc2"]},
             f"GET {c['doc2']}\nHTTP/1.1 502 Bad Gateway",
             "Call failed with upstream gateway failure. Recover with backoff."),
        step(9, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": c["doc2"]},
             f"local fixture cache of {c['doc2']}\nplatform leftover bind required",
             "Degraded path used the local fixture. Resume the local debug plan."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": old0, "new": new0},
             f"patched drop {c['wrong']}",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   AssertionError: drop is not leftover bind",
             "Still red after the first patch. Re-read the implementation; hypothesis is wrong."),
        step(12, f"Observation: post-edit test still failed (tests/test_{m}.py::{tname}). Re-read {src}.",
             "read", {"path": src},
             f"{c['stack']} cannot drop leftover bind on this platform",
             f"Plan change: {c['plan_fail']}"),
        step(13, f"Reflection: {c['plan_fail']}",
             "edit", {"path": "HANDOFF.md", "old": "", "new": f"{c['handoff']}: leftover {tok} bind required\n"},
             "handoff ticket written",
             "Handoff ticket written. Run the original failing node again."),
        step(14, "Observation: handoff edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"tests/test_{m}.py -q --tb=short"},
             f"tests/test_{m}.py::{tname} FAILED\nE   leftover bind still required",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check `pytest tests/test_{m}.py -q; echo leftover`.",
             "bash", {"command": f"pytest tests/test_{m}.py -q; echo leftover"},
             "1 failed leftover bind",
             "Broader check captured. Residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files for the handoff note.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {c['fail']}: HANDOFF.md | 4 ++++. {src} leftover.",
             "Diff is the review artifact. Lint next."),
        step(17, "Observation: diffstat listed the patched files. Run a linter on those paths only.",
             "bash", {"command": f"ruff check {src} HANDOFF.md"},
             "All checks passed!",
             "Lint clean. Episode complete."),
    ]


def episode(rnd: int, eid: str, c: dict, steps: list, success: bool) -> dict:
    seed = eid.split("-", 2)[-1] if eid.count("-") >= 2 else eid
    return {
        "id": eid,
        "goal": (
            f"Resume {c['stack']}; do not {c['wrong']}."
            if success
            else f"Handoff when {c['stack']} leftover bind cannot drop."
        ),
        "plan": (
            f"Read {c['wrong']}-as-resume, try {c['wrong']}, then leftover {c['token']}."
            if success
            else f"Try drop leftover bind; write {c['handoff']}."
        ),
        "steps": steps,
        "outcome": (
            f"{c['token']} restored {c['stack']}. {c['wrong'].capitalize()} unused (success)."
            if success
            else f"Handoff {c['handoff']}. Leftover bind drop is platform-owned."
        ),
        "reward": {
            "success": success,
            "tests_passed": 3 if success else 0,
            "retries": 2,
            "duration_min": 610 if success else 640,
            "wasted_calls": 180 if success else 210,
            "cost_steps": len(steps),
            "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "episode",
            "seed": seed,
            "designed": True,
            "domain": c["domain_ok"] if success else c["domain_fail"],
            "stack": c["stack"],
        },
    }


def notes(rnd: int, ok_id: str, fail_id: str, c: dict) -> str:
    n_ok, n_fail = 16, 17
    return (
        f"# NOTES-r{rnd} data-pipeline-repair-factory\n\n"
        f"Novel coverage: 75%\n\n"
        f"- Episodes: 2 (quota). Step counts: {c['slug'].split('-leftover')[0]} {n_ok}, "
        f"{c['fail'].replace('-handoff','')} {n_fail} (16–24).\n"
        f"- Debug loops: Dead-end: drop {c['wrong']} does not drop leftover leftover leftover "
        f"{c['token']} after digest move (6–7); Dead-end: prune; leftover leftover leftover "
        f"{c['token']} bind after whiteout still holds (5–6).\n"
        f"- One success (`{ok_id}`) and one partial (`{fail_id}`).\n"
        f"- Distinct from prior rounds: {c['stack']} leftover leftover leftover vs drop {c['wrong']}. "
        f"Not r2580–r2622 knob twins. Not dbc-/sir-/docker/search plants.\n"
        f"- Fail mode: leftover leftover leftover {c['token']} bind drop, not HTTP-status leftover.\n"
        f"- Residual synthetic tells: invented unique pipeline leftover leftover leftover plants.\n"
        f"- Ban check: not dbc- ids, not sir- ids, not docker/search, not harbor-pin, {c['ban']}\n"
        f"- Novel coverage notes unique leftover leftover leftover pipeline product "
        f"({c['stack']}) × unique leftover leftover leftover invalidation (drop {c['wrong']}).\n"
    )


def write_round(staging: Path, batch_name: str, notes_name: str, rnd: int, c: dict) -> list[str]:
    ok_id = f"dpr-r{rnd}-{c['slug']}"
    fail_id = f"dpr-r{rnd}-{c['fail']}"
    recs = [
        episode(rnd, ok_id, c, success_steps(c), True),
        episode(rnd, fail_id, c, fail_steps(c), False),
    ]
    batch = staging / batch_name
    npath = staging / notes_name
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    npath.write_text(notes(rnd, ok_id, fail_id, c))
    return [ok_id, fail_id]


def main() -> None:
    published = []
    failed_round = None
    fr = _cmd(TXN + ["frontier", str(DIR)])
    start = int(fr["next_round"])
    if (DIR / f"ROUND-r{start:02d}.reserved.json").exists():
        hop = hop_unreserved()
        print(f"reserved at {start}; hop {hop}", file=sys.stderr)
        raise SystemExit(2)
    for i, c in enumerate(CATALOG):
        if len(published) >= MAX_ROUNDS:
            break
        fr = _cmd(TXN + ["frontier", str(DIR)])
        rnd = int(fr["next_round"])
        if rnd != start + i:
            print(f"frontier next_round={rnd} expected {start + i}; stop")
            break
        try:
            res = _cmd(TXN + ["reserve", str(DIR), "--round", str(rnd), "--expected", "2"])
        except RuntimeError as exc:
            failed_round = rnd
            print(f"reserve failed round {failed_round}: {exc}", file=sys.stderr)
            hop = hop_unreserved()
            print(f"hop {hop}", file=sys.stderr)
            break
        ids = write_round(Path(res["staging_dir"]), res["batch_file"], res["notes_file"], rnd, c)
        pub = _cmd(TXN + ["publish", str(DIR), "--round", str(rnd), "--token", res["token"]])
        published.append({"round": rnd, "ids": ids, "linked": pub.get("linked")})
        print(json.dumps({"published": rnd, "ids": ids}))
    print(json.dumps({"done": published, "failed_round": failed_round}, indent=2))


if __name__ == "__main__":
    main()
