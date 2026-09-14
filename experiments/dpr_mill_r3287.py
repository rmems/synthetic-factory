#!/usr/bin/env python3
"""data-pipeline-repair mill r3287+ wave14 unique catalog."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

s = importlib.util.spec_from_file_location(
    "w9", "/home/raulmc/rmems/synthetic-factory/experiments/dpr_mill_r3039.py"
)
w9 = importlib.util.module_from_spec(s)
s.loader.exec_module(w9)
okp, failp = w9.okp, w9.failp
build, audit = w9.build, w9.audit
notes_for, published_identities, guard = w9.notes_for, w9.published_identities, w9.guard
GENERATOR = w9.GENERATOR

PAIRS = [
    (okp("vitess-vttablet-health", "Vitess vttablet health vs disable Vitess", "health_check",
         "health_check.interval=60s", "health_check.interval=2s", "Vitess", "VH-01", "stream",
         "Spanner leftover / Firestore leftover",
         "Vitess pay-tablets stale after health_check.interval stayed 60s", "stale_s", 60, "vttablet.conf"),
     failp("spanner-priority", "Spanner request priority vs disable Spanner", "priority",
           "priority=PRIORITY_LOW", "priority=PRIORITY_HIGH", "Spanner", "SP-01", "rpc",
           "Vitess leftover / Firestore leftover",
           "Spanner pay-sql LOW after priority stayed PRIORITY_LOW",
           "low", 1, "platform-spanner", "client.json")),
    (okp("firestore-bundle", "Firestore data bundles vs disable Firestore", "bundle",
         "bundle.enabled=false", "bundle.enabled=true", "Firestore", "FB-02", "namedQuery",
         "Redis leftover / NATS leftover",
         "Firestore pay-clients unbundled after bundle.enabled stayed false", "unbundled", 1, "rules.json"),
     failp("redis-lazy-eviction", "Redis lazyfree vs disable Redis", "lazyfree-lazy-eviction",
           "lazyfree-lazy-eviction no", "lazyfree-lazy-eviction yes", "Redis", "RL-02", "unlink",
           "Firestore leftover / NATS leftover",
           "Redis pay-kv blocked eviction after lazyfree-lazy-eviction stayed no",
           "block_ev", 1, "platform-redis", "redis.conf")),
    (okp("pulsar-ack-millis", "Pulsar ack timeout vs disable Pulsar", "ackTimeoutMillis",
         "ackTimeoutMillis=1000", "ackTimeoutMillis=30000", "Pulsar", "PA-03", "redelivery",
         "Kafka leftover / NATS leftover",
         "Pulsar pay-jobs redelivered after ackTimeoutMillis stayed 1000", "redeliver", 1, "client.conf"),
     failp("kafka-delivery-timeout", "Kafka delivery timeout vs disable Kafka", "delivery.timeout.ms",
           "delivery.timeout.ms=1000", "delivery.timeout.ms=120000", "Kafka", "KD-03", "retries",
           "Pulsar leftover / NATS leftover",
           "Kafka pay-cdc expired after delivery.timeout.ms stayed 1000",
           "expire", 1, "platform-kafka", "producer.properties")),
    (okp("spark-speculation-on", "Spark speculation vs disable Spark", "spark.speculation",
         "spark.speculation=false", "spark.speculation=true", "Spark", "SS-04", "multiplier",
         "Flink leftover / Hive leftover",
         "Spark pay-tasks waited stragglers after spark.speculation stayed false", "straggle", 1, "spark-defaults.conf"),
     failp("hive-skewjoin", "Hive skewjoin vs disable Hive", "hive.optimize.skewjoin",
           "hive.optimize.skewjoin=false", "hive.optimize.skewjoin=true", "Hive", "HS-04", "key",
           "Spark leftover / Flink leftover",
           "Hive pay-join straggled after hive.optimize.skewjoin stayed false",
           "straggle", 1, "platform-hive", "hive-site.xml")),
    (okp("tez-shuffle-fetch", "Tez shuffle fetch vs disable Tez", "tez.runtime.shuffle.fetch.buffer",
         "tez.runtime.shuffle.memory-limit.percent=0.10", "tez.runtime.shuffle.memory-limit.percent=0.25",
         "Tez", "TF-05", "percent", "MR leftover / NiFi leftover",
         "Tez pay-join spilled fetch after memory-limit.percent stayed 0.10", "spill", 1, "tez-site.xml"),
     failp("mr-job-end-notification", "MR job end notification vs disable MR", "mapreduce.job.end-notification",
           "mapreduce.job.end-notification.url=", "mapreduce.job.end-notification.url=https://pay/hook",
           "MR", "MN-05", "retry", "Tez leftover / NiFi leftover",
           "MapReduce pay-jobs silent after end-notification.url stayed empty",
           "silent", 1, "platform-mr", "mapred-site.xml")),
    (okp("sqs-redrive", "SQS redrive vs disable SQS", "RedrivePolicy",
         "RedrivePolicy=null", "RedrivePolicy={deadLetterTargetArn:pay-dlq,maxReceiveCount:5}",
         "SQS", "SR-06", "dlq", "SNS leftover / EventBridge leftover",
         "SQS pay-jobs infinite after RedrivePolicy stayed null", "inf_retry", 1, "queue.json"),
     failp("sns-filter-scope", "SNS filter scope vs disable SNS", "FilterPolicyScope",
           "FilterPolicyScope=MessageAttributes", "FilterPolicyScope=MessageBody",
           "SNS", "SF-06", "filter", "SQS leftover / EventBridge leftover",
           "SNS pay-topics missed body after FilterPolicyScope stayed MessageAttributes",
           "miss_body", 1, "platform-sns", "sub.json")),
    (okp("eventbridge-input-transformer", "EventBridge input transformer vs disable EventBridge", "InputTransformer",
         "InputTransformer=null", "InputTransformer={InputTemplate:pay}", "EventBridge", "EI-07", "target",
         "Kinesis leftover / Firehose leftover",
         "EventBridge pay-rules raw after InputTransformer stayed null", "raw", 1, "rule.json"),
     failp("firehose-buffer-size", "Firehose buffer size vs disable Firehose", "BufferSizeInMBs",
           "BufferSizeInMBs=1", "BufferSizeInMBs=64", "Firehose", "FB-07", "interval",
           "EventBridge leftover / Kinesis leftover",
           "Firehose pay-s3 tiny-flush after BufferSizeInMBs stayed 1",
           "tiny", 1, "platform-firehose", "stream.json")),
    (okp("s3-daily-inventory", "S3 Inventory vs disable S3", "InventoryConfiguration",
         "InventoryConfiguration=null", "InventoryConfiguration={Id:pay,Schedule:Daily}",
         "S3", "SI-08", "format", "GCS leftover / Azure leftover",
         "S3 pay-lake no inventory after InventoryConfiguration stayed null", "no_inv", 1, "bucket.json"),
     failp("gcs-notification", "GCS notification vs disable GCS", "notification",
           "notification.topic=", "notification.topic=projects/pay/topics/pay-obj",
           "GCS", "GN-08", "event", "S3 leftover / Azure leftover",
           "GCS pay-objects silent after notification.topic stayed empty",
           "silent", 1, "platform-gcs", "bucket.json")),
    (okp("azure-change-feed", "Azure blob change feed vs disable ABFS", "changeFeed",
         "changeFeed.enabled=false", "changeFeed.enabled=true", "ABFS", "AC-09", "retention",
         "Snowflake leftover / BQ leftover",
         "Azure pay-blobs no feed after changeFeed.enabled stayed false", "no_feed", 1, "account.json"),
     failp("snowflake-tasks", "Snowflake tasks vs disable Snowflake", "CREATE TASK",
           "-- no TASK", "CREATE TASK pay_refresh WAREHOUSE=pay SCHEDULE='1 minute'",
           "Snowflake", "ST-09", "warehouse", "Azure leftover / BQ leftover",
           "Snowflake pay-gmv unscheduled after CREATE TASK stayed missing",
           "unscheduled", 1, "platform-snowflake", "task.sql")),
    (okp("bq-scheduled-query", "BigQuery scheduled query vs disable BQ", "schedule",
         "schedule=", "schedule=every 15 minutes", "BQ", "BS-10", "dst",
         "Redshift leftover / Databricks leftover",
         "BQ pay-gmv unscheduled after schedule stayed empty", "unscheduled", 1, "xfer.json"),
     failp("redshift-auto-mv", "Redshift Auto MV vs disable Redshift", "auto_mv",
           "auto_mv=false", "auto_mv=true", "Redshift", "RA-10", "refresh",
           "BQ leftover / Databricks leftover",
           "Redshift pay-sql un-MV after auto_mv stayed false",
           "no_mv", 1, "platform-redshift", "wlm.json")),
    (okp("databricks-dlt-enable", "Databricks DLT vs disable DBR", "pipelines.enable",
         "pipelines.enable=false", "pipelines.enable=true", "DBR", "DD-11", "photon",
         "EMR leftover / Glue leftover",
         "Databricks pay-cdc notebook after pipelines.enable stayed false", "notebook", 1, "pipeline.json"),
     failp("emr-step-concurrency", "EMR step concurrency vs disable EMR", "StepConcurrencyLevel",
           "StepConcurrencyLevel=1", "StepConcurrencyLevel=16", "EMR", "EC-11", "keep",
           "Databricks leftover / Glue leftover",
           "EMR pay-etl serial steps after StepConcurrencyLevel stayed 1",
           "serial", 1, "platform-emr", "cluster.json")),
    (okp("spark-dynamic-allocation", "Spark dynamic allocation vs disable Spark", "spark.dynamicAllocation",
         "spark.dynamicAllocation.enabled=false", "spark.dynamicAllocation.enabled=true",
         "Spark", "SD-12", "minExecutors", "Flink leftover / Hive leftover",
         "Spark pay-jobs fixed exec after dynamicAllocation.enabled stayed false", "fixed", 1, "spark-defaults.conf"),
     failp("flink-adaptive-rescale", "Flink reactive mode vs disable Flink", "scheduler-mode",
           "scheduler-mode: REACTIVE unused", "jobmanager.scheduler: adaptive",
           "Flink", "FR-12", "maxParallelism", "Spark leftover / Hive leftover",
           "Flink pay-job never rescaled after scheduler-mode stayed unused",
           "no_scale", 1, "platform-flink", "flink-conf.yaml")),
    (okp("kafka-share-ack-timeout", "Kafka share ack vs disable share", "share.record.lock.duration.ms",
         "share.record.lock.duration.ms=1000", "share.record.lock.duration.ms=30000",
         "share", "KS-13", "groups", "Pulsar leftover / NATS leftover",
         "Kafka pay-jobs redelivered after share lock duration stayed 1s", "redeliver", 1, "server.properties"),
     failp("pulsar-keyshared-hash", "Pulsar Key_Shared hash vs disable Pulsar", "keySharedMode",
           "keySharedMode=AUTO_SPLIT", "keySharedMode=STICKY", "Pulsar", "PK-13", "hash",
           "Kafka leftover / NATS leftover",
           "Pulsar pay-jobs rehashed after keySharedMode stayed AUTO_SPLIT",
           "rehash", 1, "platform-pulsar", "client.conf")),
    (okp("nats-flow-control2", "NATS flow control vs disable JetStream", "flow_control",
         "flow_control: false", "flow_control: true", "JetStream", "NF-14", "heartbeat",
         "Rabbit leftover / SQS leftover",
         "NATS pay-consumers overrun after flow_control stayed false", "overrun", 1, "js.conf"),
     failp("rabbit-quorum-delivery", "RabbitMQ quorum delivery-limit vs disable quorum", "delivery_limit",
           "delivery_limit = -1", "delivery_limit = 8", "quorum", "RQ-14", "poison",
           "NATS leftover / SQS leftover",
           "RabbitMQ pay-jobs looped poison after quorum delivery_limit stayed -1",
           "poison_loop", 1, "platform-rabbit", "rabbit.conf")),
    (okp("hive-mapjoin-local", "Hive mapjoin local vs disable Hive", "hive.mapjoin.localtask.max.memory.usage",
         "hive.mapjoin.localtask.max.memory.usage=0.01", "hive.mapjoin.localtask.max.memory.usage=0.50",
         "Hive", "HM-15", "hashtable", "Tez leftover / Spark leftover",
         "Hive pay-mapjoin spilled after max.memory.usage stayed 0.01", "spill", 1, "hive-site.xml"),
     failp("spark-sql-adaptive-skew", "Spark AQE skew vs disable AQE", "spark.sql.adaptive.skewJoin.enabled",
           "spark.sql.adaptive.skewJoin.enabled=false", "spark.sql.adaptive.skewJoin.enabled=true",
           "AQE", "SK-15", "factor", "Hive leftover / Tez leftover",
           "Spark pay-join straggled after skewJoin.enabled stayed false",
           "straggle", 1, "platform-spark", "spark-defaults.conf")),
]


def plants_for(round_number: int):
    used = published_identities()
    for a, b in PAIRS:
        keys = {a["slug"].lower(), b["slug"].lower(), a["domain"].lower(), b["domain"].lower()}
        if keys & used:
            continue
        try:
            guard(a)
            guard(b)
        except SystemExit:
            continue
        return (lambda r, spec=a: build(r, spec), lambda r, spec=b: build(r, spec))
    raise SystemExit(f"no unused plants r{round_number} bank={len(PAIRS)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", type=Path, required=True)
    args = ap.parse_args()
    recs = [fn(args.round) for fn in plants_for(args.round)]
    if len(recs) != 2 or recs[0]["reward"]["success"] == recs[1]["reward"]["success"]:
        raise SystemExit("need success + handoff pair")
    for rec in recs:
        audit(rec)
        if rec["meta"]["generator"] != GENERATOR or rec["meta"]["round"] != args.round:
            raise SystemExit("bad meta")
        blob = json.dumps(rec)
        if "[variant" in rec["goal"].lower() or '"sim_or_real": "real"' in blob:
            raise SystemExit("banned stamp")
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"banned {bad}")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))


if __name__ == "__main__":
    sys.exit(main() or 0)
