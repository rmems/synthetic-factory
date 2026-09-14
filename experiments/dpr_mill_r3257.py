#!/usr/bin/env python3
"""data-pipeline-repair mill r3257+ wave13 unique catalog."""
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
    (okp("vitess-vtgate-buffer", "Vitess vtgate buffer vs disable Vitess", "buffer",
         "buffer.enabled=false", "buffer.enabled=true", "Vitess", "VV-01", "window",
         "Spanner leftover / Firestore leftover",
         "Vitess pay-failovers dropped after buffer.enabled stayed false", "dropped", 1, "vtgate.conf"),
     failp("spanner-query-optimizer", "Spanner optimizer version vs disable Spanner", "optimizer_version",
           "optimizer_version=1", "optimizer_version=3", "Spanner", "SO-01", "stats",
           "Vitess leftover / Firestore leftover",
           "Spanner pay-sql old plan after optimizer_version stayed 1",
           "old_plan", 1, "platform-spanner", "ddl.sql")),
    (okp("firestore-ttl-policy", "Firestore TTL vs disable Firestore", "ttl",
         "ttlField unused", "ttlField=expireAt", "Firestore", "FT-02", "index",
         "Redis leftover / NATS leftover",
         "Firestore pay-docs never expired after ttlField stayed unused", "no_ttl", 1, "index.json"),
     failp("redis-maxmemory-lfu", "Redis LFU vs disable Redis", "maxmemory-policy",
           "maxmemory-policy noeviction", "maxmemory-policy volatile-lfu", "Redis", "RL-02", "maxmemory",
           "Firestore leftover / NATS leftover",
           "Redis pay-kv OOM after maxmemory-policy stayed noeviction",
           "oom", 1, "platform-redis", "redis.conf")),
    (okp("nats-jetstream-replicas", "NATS JS replicas vs disable JetStream", "replicas",
         "replicas: 1", "replicas: 3", "JetStream", "NJ-03", "storage",
         "Pulsar leftover / Kafka leftover",
         "NATS pay-streams RF=1 after replicas stayed 1", "rf1", 1, "js.conf"),
     failp("pulsar-geo-replication", "Pulsar geo replication vs disable Pulsar", "replicationClusters",
           "replicationClusters=[]", "replicationClusters=[pay-dr]", "Pulsar", "PG-03", "cluster",
           "NATS leftover / Kafka leftover",
           "Pulsar pay-topics local-only after replicationClusters stayed empty",
           "local_only", 1, "platform-pulsar", "broker.conf")),
    (okp("kafka-min-isr", "Kafka min.insync vs disable Kafka", "min.insync.replicas",
         "min.insync.replicas=1", "min.insync.replicas=2", "Kafka", "KI-04", "acks",
         "Flink leftover / Spark leftover",
         "Kafka pay-cdc RF-unsafe after min.insync.replicas stayed 1", "unsafe", 1, "server.properties"),
     failp("spark-io-encryption", "Spark IO encryption vs disable Spark", "spark.io.encryption",
           "spark.io.encryption.enabled=false", "spark.io.encryption.enabled=true",
           "Spark", "SE-04", "key", "Kafka leftover / Flink leftover",
           "Spark pay-shuffle plaintext after io.encryption.enabled stayed false",
           "plain", 1, "platform-spark", "spark-defaults.conf")),
    (okp("hive-vectorized-exec", "Hive vectorized exec vs disable Hive", "hive.vectorized.execution",
         "hive.vectorized.execution.enabled=false", "hive.vectorized.execution.enabled=true",
         "Hive", "HV-05", "orc", "Tez leftover / MR leftover",
         "Hive pay-scan row-mode after vectorized.execution.enabled stayed false", "row_mode", 1, "hive-site.xml"),
     failp("tez-grouping-split", "Tez grouping split vs disable Tez", "tez.grouping.split-count",
           "tez.grouping.split-count=1", "tez.grouping.split-count=-1", "Tez", "TG-05", "min size",
           "Hive leftover / MR leftover",
           "Tez pay-agg one reducer after tez.grouping.split-count stayed 1",
           "one_reducer", 1, "platform-tez", "tez-site.xml")),
    (okp("mr-reduce-speculative", "MR reduce speculative vs disable MR", "mapreduce.reduce.speculative",
         "mapreduce.reduce.speculative=false", "mapreduce.reduce.speculative=true",
         "MR", "RS-06", "map", "NiFi leftover / SQS leftover",
         "MapReduce pay-reduces waited stragglers after reduce.speculative stayed false", "straggle", 1, "mapred-site.xml"),
     failp("sqs-long-poll", "SQS long poll vs disable SQS", "ReceiveMessageWaitTimeSeconds",
           "ReceiveMessageWaitTimeSeconds=0", "ReceiveMessageWaitTimeSeconds=20",
           "SQS", "SL-06", "visibility", "MR leftover / NiFi leftover",
           "SQS pay-jobs short-polled after ReceiveMessageWaitTimeSeconds stayed 0",
           "short_poll", 1, "platform-sqs", "queue.json")),
    (okp("sns-fifo-topic", "SNS FIFO vs disable SNS", "FifoTopic",
         "FifoTopic=false", "FifoTopic=true", "SNS", "SF-07", "dedup",
         "EventBridge leftover / Kinesis leftover",
         "SNS pay-topics unordered after FifoTopic stayed false", "unordered", 1, "topic.json"),
     failp("eventbridge-archive", "EventBridge archive vs disable EventBridge", "Archive",
           "Archive=null", "Archive={RetentionDays:30}", "EventBridge", "EA-07", "replay",
           "SNS leftover / Kinesis leftover",
           "EventBridge pay-events unarchived after Archive stayed null",
           "no_arch", 1, "platform-eventbridge", "bus.json")),
    (okp("kinesis-aggregation", "Kinesis aggregation vs disable Kinesis", "AggregationEnabled",
         "AggregationEnabled=false", "AggregationEnabled=true", "Kinesis", "KA-08", "maxBytes",
         "Firehose leftover / S3 leftover",
         "Kinesis pay-clicks 1-rec after AggregationEnabled stayed false", "tiny", 1, "producer.json"),
     failp("firehose-lambda", "Firehose Lambda transform vs disable Firehose", "processingConfiguration",
           "processingConfiguration.enabled=false", "processingConfiguration.enabled=true",
           "Firehose", "FL-08", "buffer", "Kinesis leftover / S3 leftover",
           "Firehose pay-s3 raw after processingConfiguration.enabled stayed false",
           "raw", 1, "platform-firehose", "stream.json")),
    (okp("s3-intelligent-tier", "S3 Intelligent-Tiering vs disable S3", "IntelligentTiering",
         "Status=Disabled", "Status=Enabled", "S3", "SI-09", "access",
         "GCS leftover / Azure leftover",
         "S3 pay-cold Standard after IntelligentTiering stayed Disabled", "std", 1, "bucket.json"),
     failp("gcs-autoclass", "GCS Autoclass vs disable GCS", "autoclass",
           "autoclass.enabled=false", "autoclass.enabled=true", "GCS", "GA-09", "terminal",
           "S3 leftover / Azure leftover",
           "GCS pay-objects Standard after autoclass.enabled stayed false",
           "std", 1, "platform-gcs", "bucket.json")),
    (okp("azure-rehydrate", "Azure rehydrate vs disable ABFS", "rehydratePriority",
         "rehydratePriority=Standard", "rehydratePriority=High", "ABFS", "AR-10", "tier",
         "Snowflake leftover / BQ leftover",
         "Azure pay-archive slow-rehydrate after rehydratePriority stayed Standard", "slow", 1, "blob.json"),
     failp("snowflake-clustering", "Snowflake clustering vs disable Snowflake", "CLUSTER BY",
           "-- no CLUSTER BY", "CLUSTER BY (dt, sku)", "Snowflake", "SC-10", "auto",
           "Azure leftover / BQ leftover",
           "Snowflake pay-facts unclustered after CLUSTER BY stayed missing",
           "uncl", 1, "platform-snowflake", "table.sql")),
    (okp("bq-clustering", "BigQuery clustering vs disable BQ", "CLUSTER BY",
         "-- no CLUSTER BY", "CLUSTER BY dt, sku", "BQ", "BC-11", "partition",
         "Redshift leftover / Databricks leftover",
         "BQ pay-facts unclustered after CLUSTER BY stayed missing", "uncl", 1, "table.sql"),
     failp("databricks-cdf", "Databricks CDF vs disable DBR", "delta.enableChangeDataFeed",
           "TBLPROPERTIES ('delta.enableChangeDataFeed'='false')",
           "TBLPROPERTIES ('delta.enableChangeDataFeed'='true')",
           "DBR", "DC-11", "cdf", "BQ leftover / Redshift leftover",
           "Databricks pay-cdc none after enableChangeDataFeed stayed false",
           "no_cdf", 1, "platform-databricks", "delta.sql")),
    (okp("emr-spot-timeout", "EMR spot timeout vs disable EMR", "SpotTimeout",
         "TimeoutDurationMinutes=5", "TimeoutDurationMinutes=60", "EMR", "ES-12", "fleet",
         "Glue leftover / Trino leftover",
         "EMR pay-etl aborted spot after TimeoutDurationMinutes stayed 5", "abort", 1, "cluster.json"),
     failp("trino-dynamic-filter", "Trino dynamic filtering vs disable Trino", "enable-dynamic-filtering",
           "enable-dynamic-filtering=false", "enable-dynamic-filtering=true", "Trino", "TD-12", "wait",
           "EMR leftover / Glue leftover",
           "Trino pay-join unscanned-skip after enable-dynamic-filtering stayed false",
           "no_df", 1, "platform-trino", "config.properties")),
    (okp("presto-dynamic-filter", "Presto dynamic filtering vs disable Presto", "enable-dynamic-filtering",
         "enable-dynamic-filtering=false", "enable-dynamic-filtering=true", "Presto", "PD-13", "wait",
         "Impala leftover / Spark leftover",
         "Presto pay-join unscanned-skip after enable-dynamic-filtering stayed false", "no_df", 1, "config.properties"),
     failp("impala-runtime-filter", "Impala runtime filter vs disable Impala", "runtime_filter_mode",
           "-runtime_filter_mode=OFF", "-runtime_filter_mode=GLOBAL", "Impala", "IR-13", "wait",
           "Presto leftover / Spark leftover",
           "Impala pay-join unscanned-skip after runtime_filter_mode stayed OFF",
           "no_rf", 1, "platform-impala", "impala.flags")),
    (okp("kafka-idempotence", "Kafka producer idempotence vs disable Kafka", "enable.idempotence",
         "enable.idempotence=false", "enable.idempotence=true", "Kafka", "KI-14", "acks",
         "Pulsar leftover / NATS leftover",
         "Kafka pay-cdc duplicated after enable.idempotence stayed false", "dups", 1, "producer.properties"),
     failp("pulsar-broker-dedup", "Pulsar broker dedup vs disable Pulsar", "brokerDeduplicationEnabled",
           "brokerDeduplicationEnabled=false", "brokerDeduplicationEnabled=true",
           "Pulsar", "PD-14", "snapshot", "Kafka leftover / NATS leftover",
           "Pulsar pay-jobs duplicated after brokerDeduplicationEnabled stayed false",
           "dups", 1, "platform-pulsar", "broker.conf")),
    (okp("nats-ack-policy", "NATS ack policy vs disable JetStream", "ack_policy",
         "ack_policy: none", "ack_policy: explicit", "JetStream", "NA-15", "max_deliver",
         "Rabbit leftover / SQS leftover",
         "NATS pay-jobs fire-forget after ack_policy stayed none", "no_ack", 1, "js.conf"),
     failp("rabbit-confirm", "RabbitMQ publisher confirm vs disable Rabbit", "confirm",
           "publisher_confirms=false", "publisher_confirms=true", "Rabbit", "RC-15", "mandatory",
           "NATS leftover / SQS leftover",
           "RabbitMQ pay-orders unconfirmed after publisher_confirms stayed false",
           "unconf", 1, "platform-rabbit", "rabbit.conf")),
    (okp("sqs-delay-seconds", "SQS delay vs disable SQS", "DelaySeconds",
         "DelaySeconds=0", "DelaySeconds=15", "SQS", "SD-16", "visibility",
         "SNS leftover / EventBridge leftover",
         "SQS pay-jobs immediate after DelaySeconds stayed 0", "immediate", 1, "queue.json"),
     failp("sns-fifo-dedup", "SNS FIFO dedup vs disable SNS", "ContentBasedDeduplication",
           "ContentBasedDeduplication=false", "ContentBasedDeduplication=true",
           "SNS", "SF-16", "group", "SQS leftover / EventBridge leftover",
           "SNS pay-topics duplicated after ContentBasedDeduplication stayed false",
           "dups", 1, "platform-sns", "topic.json")),
    (okp("hive-cbo-extended", "Hive CBO extended vs disable Hive", "hive.cbo.enable",
         "hive.cbo.enable=false", "hive.cbo.enable=true", "Hive", "HC-17", "stats",
         "Tez leftover / Spark leftover",
         "Hive pay-sql un-CBO after hive.cbo.enable stayed false", "no_cbo", 1, "hive-site.xml"),
     failp("spark-aqe-forceoptimize", "Spark AQE force optimize vs disable AQE", "spark.sql.adaptive.forceOptimizeSkewedJoin",
           "spark.sql.adaptive.forceOptimizeSkewedJoin=false",
           "spark.sql.adaptive.forceOptimizeSkewedJoin=true",
           "AQE", "SA-17", "skew", "Hive leftover / Tez leftover",
           "Spark pay-join unforced after forceOptimizeSkewedJoin stayed false",
           "unforced", 1, "platform-spark", "spark-defaults.conf")),
    (okp("flink-state-changelog", "Flink changelog state vs disable Flink", "state.backend.changelog",
         "state.backend.changelog.enabled: false", "state.backend.changelog.enabled: true",
         "Flink", "FC-18", "periodic", "Kafka leftover / Hive leftover",
         "Flink pay-cp full after changelog.enabled stayed false", "full_cp", 1, "flink-conf.yaml"),
     failp("nifi-partition-balance", "NiFi load balance vs disable NiFi", "loadBalanceStrategy",
           "loadBalanceStrategy=DO_NOT_LOAD_BALANCE", "loadBalanceStrategy=PARTITION_BY_ATTRIBUTE",
           "NiFi", "NL-18", "compression", "Flink leftover / Kafka leftover",
           "NiFi pay-flow hotspot after loadBalanceStrategy stayed DO_NOT_LOAD_BALANCE",
           "hotspot", 1, "platform-nifi", "nifi.properties")),
    (okp("trino-cost-catalog", "Trino cost catalog vs disable Trino", "optimizer.use-cost",
         "optimizer.join-distribution-type=BROADCAST", "optimizer.join-distribution-type=AUTOMATIC",
         "Trino", "TC-19", "stats", "Presto leftover / Impala leftover",
         "Trino pay-join always-broadcast after join-distribution-type stayed BROADCAST", "bcast", 1, "config.properties"),
     failp("presto-cost-catalog", "Presto cost catalog vs disable Presto", "optimizer.use-cost",
           "join-distribution-type=BROADCAST", "join-distribution-type=AUTOMATIC",
           "Presto", "PC-19", "stats", "Trino leftover / Impala leftover",
           "Presto pay-join always-broadcast after join-distribution-type stayed BROADCAST",
           "bcast", 1, "platform-presto", "config.properties")),
    (okp("impala-mt-dop-threads", "Impala mt_dop vs disable Impala", "mt_dop",
         "mt_dop=0", "mt_dop=8", "Impala", "IM-20", "threads",
         "Hive leftover / Spark leftover",
         "Impala pay-sql serial after mt_dop stayed 0", "serial", 1, "impala.flags"),
     failp("spark-sql-adaptive-force", "Spark AQE force apply vs disable AQE", "spark.sql.adaptive.forceApply",
           "spark.sql.adaptive.forceApply=false", "spark.sql.adaptive.forceApply=true",
           "AQE", "SF-20", "coalesce", "Impala leftover / Hive leftover",
           "Spark pay-sql skipped AQE after forceApply stayed false",
           "skip_aqe", 1, "platform-spark", "spark-defaults.conf")),
    (okp("kafka-linger-ms", "Kafka linger.ms vs disable Kafka", "linger.ms",
         "linger.ms=0", "linger.ms=20", "Kafka", "KL-21", "batch",
         "Pulsar leftover / NATS leftover",
         "Kafka pay-cdc 1-rec after linger.ms stayed 0", "tiny", 1, "producer.properties"),
     failp("pulsar-batching-delay", "Pulsar batching delay vs disable Pulsar", "batchingMaxPublishDelayMicros",
           "batchingMaxPublishDelayMicros=0", "batchingMaxPublishDelayMicros=10000",
           "Pulsar", "PB-21", "maxMessages", "Kafka leftover / NATS leftover",
           "Pulsar pay-jobs 1-msg after batchingMaxPublishDelayMicros stayed 0",
           "tiny", 1, "platform-pulsar", "client.conf")),
    (okp("nats-ack-pending-cap", "NATS max ack pending vs disable JetStream", "max_ack_pending",
         "max_ack_pending: 1", "max_ack_pending: 1000", "JetStream", "NM-22", "ack_wait",
         "Rabbit leftover / SQS leftover",
         "NATS pay-jobs 1-inflight after max_ack_pending stayed 1", "tiny", 1, "js.conf"),
     failp("rabbit-qos-global", "RabbitMQ global QoS vs disable Rabbit", "prefetch_global",
           "global_qos=false", "global_qos=true", "Rabbit", "RQ-22", "prefetch",
           "NATS leftover / SQS leftover",
           "RabbitMQ pay-jobs per-consumer after global_qos stayed false",
           "per_c", 1, "platform-rabbit", "rabbit.conf")),
    (okp("s3-object-lock", "S3 Object Lock vs disable S3", "ObjectLockEnabled",
         "ObjectLockEnabled=false", "ObjectLockEnabled=true", "S3", "SO-23", "retention",
         "GCS leftover / Azure leftover",
         "S3 pay-lake mutable after ObjectLockEnabled stayed false", "mutable", 1, "bucket.json"),
     failp("gcs-retention-policy", "GCS retention vs disable GCS", "retentionPolicy",
           "retentionPeriod=0", "retentionPeriod=2592000", "GCS", "GR-23", "bucket",
           "S3 leftover / Azure leftover",
           "GCS pay-objects mutable after retentionPeriod stayed 0",
           "mutable", 1, "platform-gcs", "bucket.json")),
    (okp("azure-immutability", "Azure immutability vs disable ABFS", "immutabilityPolicy",
         "immutabilityPolicy=null", "immutabilityPolicy={period:30}", "ABFS", "AI-24", "legalHold",
         "Snowflake leftover / BQ leftover",
         "Azure pay-blobs mutable after immutabilityPolicy stayed null", "mutable", 1, "container.json"),
     failp("snowflake-time-travel", "Snowflake time travel vs disable Snowflake", "DATA_RETENTION_TIME_IN_DAYS",
           "DATA_RETENTION_TIME_IN_DAYS=0", "DATA_RETENTION_TIME_IN_DAYS=7",
           "Snowflake", "ST-24", "failsafe", "Azure leftover / BQ leftover",
           "Snowflake pay-tables no travel after DATA_RETENTION_TIME_IN_DAYS stayed 0",
           "no_tt", 1, "platform-snowflake", "table.sql")),
    (okp("bq-time-travel", "BigQuery time travel vs disable BQ", "max_time_travel_hours",
         "max_time_travel_hours=0", "max_time_travel_hours=168", "BQ", "BT-25", "fail-safe",
         "Redshift leftover / Databricks leftover",
         "BQ pay-tables no travel after max_time_travel_hours stayed 0", "no_tt", 1, "dataset.sql"),
     failp("redshift-snapshot-retention", "Redshift snapshot retention vs disable Redshift", "automatedSnapshotRetentionPeriod",
           "automatedSnapshotRetentionPeriod=0", "automatedSnapshotRetentionPeriod=7",
           "Redshift", "RS-25", "manual", "BQ leftover / Databricks leftover",
           "Redshift pay-cluster no snapshots after automatedSnapshotRetentionPeriod stayed 0",
           "no_snap", 1, "platform-redshift", "cluster.json")),
    (okp("databricks-table-properties-log", "Databricks delta log retention vs disable DBR", "delta.logRetentionDuration",
         "delta.logRetentionDuration=interval 0 days", "delta.logRetentionDuration=interval 30 days",
         "DBR", "DL-26", "checkpoint", "EMR leftover / Glue leftover",
         "Databricks pay-tables no log after logRetentionDuration stayed 0 days", "no_log", 1, "delta.sql"),
     failp("emr-termination-protect", "EMR termination protect vs disable EMR", "TerminationProtected",
           "TerminationProtected=false", "TerminationProtected=true", "EMR", "ET-26", "keep",
           "Databricks leftover / Glue leftover",
           "EMR pay-etl terminated after TerminationProtected stayed false",
           "term", 1, "platform-emr", "cluster.json")),
    (okp("trino-exchange-compress", "Trino exchange compress vs disable Trino", "exchange.compression-codec",
         "exchange.compression-codec=NONE", "exchange.compression-codec=LZ4", "Trino", "TE-27", "spool",
         "Presto leftover / Impala leftover",
         "Trino pay-join uncompressed after exchange.compression-codec stayed NONE", "uncomp", 1, "config.properties"),
     failp("presto-exchange-compress", "Presto exchange compress vs disable Presto", "exchange.compression",
           "exchange.compression-enabled=false", "exchange.compression-enabled=true",
           "Presto", "PE-27", "codec", "Trino leftover / Impala leftover",
           "Presto pay-join uncompressed after exchange.compression-enabled stayed false",
           "uncomp", 1, "platform-presto", "config.properties")),
    (okp("hive-intermediate-compress", "Hive intermediate compress vs disable Hive", "hive.exec.compress.intermediate",
         "hive.exec.compress.intermediate=false", "hive.exec.compress.intermediate=true",
         "Hive", "HI-28", "codec", "Tez leftover / MR leftover",
         "Hive pay-shuffle uncompressed after compress.intermediate stayed false", "uncomp", 1, "hive-site.xml"),
     failp("mr-map-output-compress", "MR map output compress vs disable MR", "mapreduce.map.output.compress",
           "mapreduce.map.output.compress=false", "mapreduce.map.output.compress=true",
           "MR", "MC-28", "codec", "Hive leftover / Tez leftover",
           "MapReduce pay-shuffle uncompressed after map.output.compress stayed false",
           "uncomp", 1, "platform-mr", "mapred-site.xml")),
    (okp("spark-rdd-compress", "Spark RDD compress vs disable Spark", "spark.rdd.compress",
         "spark.rdd.compress=false", "spark.rdd.compress=true", "Spark", "SR-29", "codec",
         "Flink leftover / Kafka leftover",
         "Spark pay-cache uncompressed after spark.rdd.compress stayed false", "uncomp", 1, "spark-defaults.conf"),
     failp("flink-net-compress", "Flink net compress vs disable Flink", "taskmanager.network.memory.floating-buffers",
           "taskmanager.network.netty.client.numThreads=1", "taskmanager.network.netty.client.numThreads=16",
           "Flink", "FN-29", "credit", "Spark leftover / Kafka leftover",
           "Flink pay-shuffle starved netty after client.numThreads stayed 1",
           "starve", 1, "platform-flink", "flink-conf.yaml")),
    (okp("nifi-compress-content", "NiFi compress content vs disable NiFi", "nifi.content.repository.archive.enabled",
         "nifi.content.repository.archive.max.retention.period=0 min",
         "nifi.content.repository.archive.max.retention.period=12 hours",
         "NiFi", "NC-30", "archive", "Kafka leftover / SQS leftover",
         "NiFi pay-flow no archive after max.retention.period stayed 0 min", "no_arch", 1, "nifi.properties"),
     failp("kafka-log-preallocate", "Kafka log preallocate vs disable Kafka", "log.preallocate",
           "log.preallocate=false", "log.preallocate=true", "Kafka", "KP-30", "segment",
           "NiFi leftover / SQS leftover",
           "Kafka pay-cdc slow-create after log.preallocate stayed false",
           "slow_create", 1, "platform-kafka", "server.properties")),
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
