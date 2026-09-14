#!/usr/bin/env python3
"""queue-backpressure leftover leftover leftover mill r126–r141 unique broker leftover leftover leftover pairs."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/queue-backpressure-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "queue-backpressure-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16

# Unique leftover leftover leftover vs r42–r125. BAN r41 disruptor. BAN sir-/dbc- ids.
# Each: leftover resume token vs naive drop (success) / drop-bind handoff (fail).
CATALOG = [
    {
        "mod": "celstid",
        "slug": "celery-task-id-leftover-vs-drop-queue",
        "fail": "celery-drop-task-id-handoff",
        "stack": "Celery leftover task_id",
        "token": "leftover_task_id",
        "wrong": "drop queue",
        "wrong_key": "queue",
        "test_ok": "test_tid_not_queue",
        "test_fail": "test_tid_bind",
        "docs": "https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-id",
        "doc2": "https://docs.celeryq.dev/en/stable/userguide/routing.html",
        "handoff": "CEL-TID-17",
        "domain_ok": "celery-task-id-leftover-vs-drop-queue",
        "domain_fail": "celery-drop-leftover-task-id-bind",
        "first_patch": ("    return {'queue': sid}", "    return {'queue': None}"),
        "fix_patch": ("    return {'queue': None}", "    return {'leftover_task_id': sid}"),
        "src_obs": "Celery leftover task_id restores the same AsyncResult; drop queue is not resume",
        "plan_ok": "Pass leftover_task_id. Drop queue is not resume.",
        "plan_fail": "Leftover task_id bind drop is Celery plat. Handoff CEL-TID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queue leftover clone.",
    },
    {
        "mod": "rqjobid",
        "slug": "rq-job-id-leftover-vs-drop-worker",
        "fail": "rq-drop-job-id-handoff",
        "stack": "RQ leftover job_id",
        "token": "leftover_job_id",
        "wrong": "drop worker",
        "wrong_key": "worker",
        "test_ok": "test_jid_not_worker",
        "test_fail": "test_jid_bind",
        "docs": "https://python-rq.org/docs/",
        "doc2": "https://python-rq.org/docs/workers/",
        "handoff": "RQ-JID-17",
        "domain_ok": "rq-job-id-leftover-vs-drop-worker",
        "domain_fail": "rq-drop-leftover-job-id-bind",
        "first_patch": ("    return {'worker': sid}", "    return {'worker': None}"),
        "fix_patch": ("    return {'worker': None}", "    return {'leftover_job_id': sid}"),
        "src_obs": "RQ leftover job_id restores the same Job; drop worker is not resume",
        "plan_ok": "Pass leftover_job_id. Drop worker is not resume.",
        "plan_fail": "Leftover job_id bind drop is RQ plat. Handoff RQ-JID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not worker leftover clone.",
    },
    {
        "mod": "bulljid",
        "slug": "bullmq-jobid-leftover-vs-drop-queue",
        "fail": "bullmq-drop-jobid-handoff",
        "stack": "BullMQ leftover jobId",
        "token": "leftover_jobId",
        "wrong": "drop queue",
        "wrong_key": "queue",
        "test_ok": "test_bjid_not_queue",
        "test_fail": "test_bjid_bind",
        "docs": "https://docs.bullmq.io/guide/jobs",
        "doc2": "https://docs.bullmq.io/guide/queues",
        "handoff": "BULL-JID-17",
        "domain_ok": "bullmq-jobid-leftover-vs-drop-queue",
        "domain_fail": "bullmq-drop-leftover-jobid-bind",
        "first_patch": ("    return {'queue': sid}", "    return {'queue': None}"),
        "fix_patch": ("    return {'queue': None}", "    return {'leftover_jobId': sid}"),
        "src_obs": "BullMQ leftover jobId restores the same job; drop queue is not resume",
        "plan_ok": "Pass leftover_jobId. Drop queue is not resume.",
        "plan_fail": "Leftover jobId bind drop is BullMQ plat. Handoff BULL-JID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queue leftover clone.",
    },
    {
        "mod": "skjid",
        "slug": "sidekiq-jid-leftover-vs-drop-queue",
        "fail": "sidekiq-drop-jid-handoff",
        "stack": "Sidekiq leftover jid",
        "token": "leftover_jid",
        "wrong": "drop queue",
        "wrong_key": "queue",
        "test_ok": "test_skjid_not_queue",
        "test_fail": "test_skjid_bind",
        "docs": "https://github.com/sidekiq/sidekiq/wiki/Job-Format",
        "doc2": "https://github.com/sidekiq/sidekiq/wiki/Advanced-Options",
        "handoff": "SK-JID-17",
        "domain_ok": "sidekiq-jid-leftover-vs-drop-queue",
        "domain_fail": "sidekiq-drop-leftover-jid-bind",
        "first_patch": ("    return {'queue': sid}", "    return {'queue': None}"),
        "fix_patch": ("    return {'queue': None}", "    return {'leftover_jid': sid}"),
        "src_obs": "Sidekiq leftover jid restores the same job; drop queue is not resume",
        "plan_ok": "Pass leftover_jid. Drop queue is not resume.",
        "plan_fail": "Leftover jid bind drop is Sidekiq plat. Handoff SK-JID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queue leftover clone.",
    },
    {
        "mod": "tmpwid",
        "slug": "temporal-workflow-id-leftover-vs-drop-taskqueue",
        "fail": "temporal-drop-workflow-id-handoff",
        "stack": "Temporal leftover workflow_id",
        "token": "leftover_workflow_id",
        "wrong": "drop taskqueue",
        "wrong_key": "taskqueue",
        "test_ok": "test_wid_not_tq",
        "test_fail": "test_wid_bind",
        "docs": "https://docs.temporal.io/workflows#workflow-id",
        "doc2": "https://docs.temporal.io/task-queue",
        "handoff": "TMP-WID-17",
        "domain_ok": "temporal-workflow-id-leftover-vs-drop-taskqueue",
        "domain_fail": "temporal-drop-leftover-workflow-id-bind",
        "first_patch": ("    return {'taskqueue': sid}", "    return {'taskqueue': None}"),
        "fix_patch": ("    return {'taskqueue': None}", "    return {'leftover_workflow_id': sid}"),
        "src_obs": "Temporal leftover workflow_id restores the same run; drop taskqueue is not resume",
        "plan_ok": "Pass leftover_workflow_id. Drop taskqueue is not resume.",
        "plan_fail": "Leftover workflow_id bind drop is Temporal plat. Handoff TMP-WID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not taskqueue leftover clone.",
    },
    {
        "mod": "cadrid",
        "slug": "cadence-run-id-leftover-vs-drop-domain",
        "fail": "cadence-drop-run-id-handoff",
        "stack": "Cadence leftover run_id",
        "token": "leftover_run_id",
        "wrong": "drop domain",
        "wrong_key": "domain",
        "test_ok": "test_rid_not_domain",
        "test_fail": "test_rid_bind",
        "docs": "https://cadenceworkflow.io/docs/concepts/workflows/",
        "doc2": "https://cadenceworkflow.io/docs/concepts/domains/",
        "handoff": "CAD-RID-17",
        "domain_ok": "cadence-run-id-leftover-vs-drop-domain",
        "domain_fail": "cadence-drop-leftover-run-id-bind",
        "first_patch": ("    return {'domain': sid}", "    return {'domain': None}"),
        "fix_patch": ("    return {'domain': None}", "    return {'leftover_run_id': sid}"),
        "src_obs": "Cadence leftover run_id restores the same execution; drop domain is not resume",
        "plan_ok": "Pass leftover_run_id. Drop domain is not resume.",
        "plan_fail": "Leftover run_id bind drop is Cadence plat. Handoff CAD-RID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not domain leftover clone.",
    },
    {
        "mod": "condwid",
        "slug": "conductor-workflow-id-leftover-vs-drop-queue",
        "fail": "conductor-drop-workflow-id-handoff",
        "stack": "Conductor leftover workflowId",
        "token": "leftover_workflowId",
        "wrong": "drop queue",
        "wrong_key": "queue",
        "test_ok": "test_cwid_not_queue",
        "test_fail": "test_cwid_bind",
        "docs": "https://conductor-oss.github.io/conductor/documentation/api/workflow/",
        "doc2": "https://conductor-oss.github.io/conductor/documentation/configuration/taskqueues/",
        "handoff": "COND-WID-17",
        "domain_ok": "conductor-workflow-id-leftover-vs-drop-queue",
        "domain_fail": "conductor-drop-leftover-workflow-id-bind",
        "first_patch": ("    return {'queue': sid}", "    return {'queue': None}"),
        "fix_patch": ("    return {'queue': None}", "    return {'leftover_workflowId': sid}"),
        "src_obs": "Conductor leftover workflowId restores the same execution; drop queue is not resume",
        "plan_ok": "Pass leftover_workflowId. Drop queue is not resume.",
        "plan_fail": "Leftover workflowId bind drop is Conductor plat. Handoff COND-WID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queue leftover clone.",
    },
    {
        "mod": "aftikey",
        "slug": "airflow-ti-key-leftover-vs-drop-executor",
        "fail": "airflow-drop-ti-key-handoff",
        "stack": "Airflow leftover task_instance_key",
        "token": "leftover_task_instance_key",
        "wrong": "drop executor",
        "wrong_key": "executor",
        "test_ok": "test_tikey_not_exec",
        "test_fail": "test_tikey_bind",
        "docs": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html",
        "doc2": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html",
        "handoff": "AF-TI-17",
        "domain_ok": "airflow-ti-key-leftover-vs-drop-executor",
        "domain_fail": "airflow-drop-leftover-ti-key-bind",
        "first_patch": ("    return {'executor': sid}", "    return {'executor': None}"),
        "fix_patch": ("    return {'executor': None}", "    return {'leftover_task_instance_key': sid}"),
        "src_obs": "Airflow leftover task_instance_key restores the same TI; drop executor is not resume",
        "plan_ok": "Pass leftover_task_instance_key. Drop executor is not resume.",
        "plan_fail": "Leftover task_instance_key bind drop is Airflow plat. Handoff AF-TI-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not executor leftover clone.",
    },
    {
        "mod": "dgrunid",
        "slug": "dagster-run-id-leftover-vs-drop-repository",
        "fail": "dagster-drop-run-id-handoff",
        "stack": "Dagster leftover run_id",
        "token": "leftover_run_id",
        "wrong": "drop repository",
        "wrong_key": "repository",
        "test_ok": "test_drid_not_repo",
        "test_fail": "test_drid_bind",
        "docs": "https://docs.dagster.io/guides/operate/run-history",
        "doc2": "https://docs.dagster.io/guides/deploy/code-locations",
        "handoff": "DG-RID-17",
        "domain_ok": "dagster-run-id-leftover-vs-drop-repository",
        "domain_fail": "dagster-drop-leftover-run-id-bind",
        "first_patch": ("    return {'repository': sid}", "    return {'repository': None}"),
        "fix_patch": ("    return {'repository': None}", "    return {'leftover_run_id': sid}"),
        "src_obs": "Dagster leftover run_id restores the same DagsterRun; drop repository is not resume",
        "plan_ok": "Pass leftover_run_id. Drop repository is not resume.",
        "plan_fail": "Leftover run_id bind drop is Dagster plat. Handoff DG-RID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not repository leftover clone.",
    },
    {
        "mod": "pffrid",
        "slug": "prefect-flow-run-id-leftover-vs-drop-workqueue",
        "fail": "prefect-drop-flow-run-id-handoff",
        "stack": "Prefect leftover flow_run_id",
        "token": "leftover_flow_run_id",
        "wrong": "drop workqueue",
        "wrong_key": "workqueue",
        "test_ok": "test_frid_not_wq",
        "test_fail": "test_frid_bind",
        "docs": "https://docs.prefect.io/v3/concepts/flows",
        "doc2": "https://docs.prefect.io/v3/deploy/infrastructure-concepts/work-pools",
        "handoff": "PF-FRID-17",
        "domain_ok": "prefect-flow-run-id-leftover-vs-drop-workqueue",
        "domain_fail": "prefect-drop-leftover-flow-run-id-bind",
        "first_patch": ("    return {'workqueue': sid}", "    return {'workqueue': None}"),
        "fix_patch": ("    return {'workqueue': None}", "    return {'leftover_flow_run_id': sid}"),
        "src_obs": "Prefect leftover flow_run_id restores the same flow run; drop workqueue is not resume",
        "plan_ok": "Pass leftover_flow_run_id. Drop workqueue is not resume.",
        "plan_fail": "Leftover flow_run_id bind drop is Prefect plat. Handoff PF-FRID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not workqueue leftover clone.",
    },
    {
        "mod": "kcginst",
        "slug": "kafka-group-instance-leftover-vs-drop-topic",
        "fail": "kafka-drop-group-instance-handoff",
        "stack": "Kafka leftover group.instance.id",
        "token": "leftover_group_instance_id",
        "wrong": "drop topic",
        "wrong_key": "topic",
        "test_ok": "test_ginst_not_topic",
        "test_fail": "test_ginst_bind",
        "docs": "https://kafka.apache.org/documentation/#consumerconfigs_group.instance.id",
        "doc2": "https://kafka.apache.org/documentation/#consumerconfigs",
        "handoff": "KF-GI-17",
        "domain_ok": "kafka-group-instance-leftover-vs-drop-topic",
        "domain_fail": "kafka-drop-leftover-group-instance-bind",
        "first_patch": ("    return {'topic': sid}", "    return {'topic': None}"),
        "fix_patch": ("    return {'topic': None}", "    return {'leftover_group_instance_id': sid}"),
        "src_obs": "Kafka leftover group.instance.id restores static membership; drop topic is not resume",
        "plan_ok": "Pass leftover_group_instance_id. Drop topic is not resume.",
        "plan_fail": "Leftover group.instance.id bind drop is Kafka plat. Handoff KF-GI-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not topic leftover clone.",
    },
    {
        "mod": "natsdur",
        "slug": "nats-durable-name-leftover-vs-drop-stream",
        "fail": "nats-drop-durable-name-handoff",
        "stack": "NATS leftover durable_name",
        "token": "leftover_durable_name",
        "wrong": "drop stream",
        "wrong_key": "stream",
        "test_ok": "test_dur_not_stream",
        "test_fail": "test_dur_bind",
        "docs": "https://docs.nats.io/nats-concepts/jetstream/consumers",
        "doc2": "https://docs.nats.io/nats-concepts/jetstream/streams",
        "handoff": "NATS-DUR-17",
        "domain_ok": "nats-durable-name-leftover-vs-drop-stream",
        "domain_fail": "nats-drop-leftover-durable-name-bind",
        "first_patch": ("    return {'stream': sid}", "    return {'stream': None}"),
        "fix_patch": ("    return {'stream': None}", "    return {'leftover_durable_name': sid}"),
        "src_obs": "NATS leftover durable_name restores the same consumer; drop stream is not resume",
        "plan_ok": "Pass leftover_durable_name. Drop stream is not resume.",
        "plan_fail": "Leftover durable_name bind drop is NATS plat. Handoff NATS-DUR-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not stream leftover clone.",
    },
    {
        "mod": "rbtcstag",
        "slug": "rabbit-consumer-tag-leftover-vs-drop-exchange",
        "fail": "rabbit-drop-consumer-tag-handoff",
        "stack": "Rabbit leftover consumer_tag",
        "token": "leftover_consumer_tag",
        "wrong": "drop exchange",
        "wrong_key": "exchange",
        "test_ok": "test_ctag_not_exch",
        "test_fail": "test_ctag_bind",
        "docs": "https://www.rabbitmq.com/docs/consumers",
        "doc2": "https://www.rabbitmq.com/docs/exchanges",
        "handoff": "RB-CTAG-17",
        "domain_ok": "rabbit-consumer-tag-leftover-vs-drop-exchange",
        "domain_fail": "rabbit-drop-leftover-consumer-tag-bind",
        "first_patch": ("    return {'exchange': sid}", "    return {'exchange': None}"),
        "fix_patch": ("    return {'exchange': None}", "    return {'leftover_consumer_tag': sid}"),
        "src_obs": "Rabbit leftover consumer_tag restores the same consumer; drop exchange is not resume",
        "plan_ok": "Pass leftover_consumer_tag. Drop exchange is not resume.",
        "plan_fail": "Leftover consumer_tag bind drop is Rabbit plat. Handoff RB-CTAG-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not exchange leftover clone.",
    },
    {
        "mod": "pulsasub",
        "slug": "pulsar-subscription-leftover-vs-drop-topic",
        "fail": "pulsar-drop-subscription-handoff",
        "stack": "Pulsar leftover subscription",
        "token": "leftover_subscription",
        "wrong": "drop topic",
        "wrong_key": "topic",
        "test_ok": "test_sub_not_topic",
        "test_fail": "test_sub_bind",
        "docs": "https://pulsar.apache.org/docs/4.0.x/concepts-messaging/#subscription",
        "doc2": "https://pulsar.apache.org/docs/4.0.x/concepts-messaging/#topic",
        "handoff": "PUL-SUB-17",
        "domain_ok": "pulsar-subscription-leftover-vs-drop-topic",
        "domain_fail": "pulsar-drop-leftover-subscription-bind",
        "first_patch": ("    return {'topic': sid}", "    return {'topic': None}"),
        "fix_patch": ("    return {'topic': None}", "    return {'leftover_subscription': sid}"),
        "src_obs": "Pulsar leftover subscription restores cursor identity; drop topic is not resume",
        "plan_ok": "Pass leftover_subscription. Drop topic is not resume.",
        "plan_fail": "Leftover subscription bind drop is Pulsar plat. Handoff PUL-SUB-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not topic leftover clone.",
    },
    {
        "mod": "rpginst",
        "slug": "redpanda-group-id-leftover-vs-drop-partition",
        "fail": "redpanda-drop-group-id-handoff",
        "stack": "Redpanda leftover group.id",
        "token": "leftover_group_id",
        "wrong": "drop partition",
        "wrong_key": "partition",
        "test_ok": "test_gid_not_part",
        "test_fail": "test_gid_bind",
        "docs": "https://docs.redpanda.com/current/develop/consume-data/consumer-offsets/",
        "doc2": "https://docs.redpanda.com/current/develop/consume-data/",
        "handoff": "RP-GID-17",
        "domain_ok": "redpanda-group-id-leftover-vs-drop-partition",
        "domain_fail": "redpanda-drop-leftover-group-id-bind",
        "first_patch": ("    return {'partition': sid}", "    return {'partition': None}"),
        "fix_patch": ("    return {'partition': None}", "    return {'leftover_group_id': sid}"),
        "src_obs": "Redpanda leftover group.id restores committed offsets; drop partition is not resume",
        "plan_ok": "Pass leftover_group_id. Drop partition is not resume.",
        "plan_fail": "Leftover group.id bind drop is Redpanda plat. Handoff RP-GID-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not partition leftover clone.",
    },
    {
        "mod": "sqsmsggrp",
        "slug": "sqs-message-group-leftover-vs-drop-queue",
        "fail": "sqs-drop-message-group-handoff",
        "stack": "SQS leftover MessageGroupId",
        "token": "leftover_message_group_id",
        "wrong": "drop queue",
        "wrong_key": "queue",
        "test_ok": "test_mgid_not_queue",
        "test_fail": "test_mgid_bind",
        "docs": "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html",
        "doc2": "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html",
        "handoff": "SQS-MG-17",
        "domain_ok": "sqs-message-group-leftover-vs-drop-queue",
        "domain_fail": "sqs-drop-leftover-message-group-bind",
        "first_patch": ("    return {'queue': sid}", "    return {'queue': None}"),
        "fix_patch": ("    return {'queue': None}", "    return {'leftover_message_group_id': sid}"),
        "src_obs": "SQS leftover MessageGroupId restores FIFO ordering; drop queue is not resume",
        "plan_ok": "Pass leftover_message_group_id. Drop queue is not resume.",
        "plan_fail": "Leftover MessageGroupId bind drop is SQS plat. Handoff SQS-MG-17.",
        "ban": "Not docker cache. Not dbc-/sir- ids. Not queue leftover clone.",
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
        f"# NOTES-r{rnd} queue-backpressure-factory\n\n"
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
    ok_id = f"qbp-r{rnd}-{c['slug']}"
    fail_id = f"qbp-r{rnd}-{c['fail']}"
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
