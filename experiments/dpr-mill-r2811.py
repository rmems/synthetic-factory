#!/usr/bin/env python3
"""data-pipeline-repair mill r2811+ wave3. Unique plants only."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

s2631 = importlib.util.spec_from_file_location("dpr2631", "/tmp/dpr_mill_r2631.py")
m = importlib.util.module_from_spec(s2631)
s2631.loader.exec_module(m)
OK, FAIL, build, audit = m.OK, m.FAIL, m.build, m.audit
notes_for = m.notes_for
published_identities = m.published_identities
guard = m.guard
GENERATOR = m.GENERATOR

PAIRS = [
    (
        OK("cortex-tsdb-ship", "Cortex TSDB ship vs disable Cortex", "cortex", "cortex.yaml",
           "tsdb.ship_interval", "ship_interval: 24h", "ship_interval: 1m",
           "cortex.enabled: true", "cortex.enabled: false", "Cortex", "CX-01", "ingester",
           "Mimir leftover / Pyroscope leftover",
           "Cortex pay-metrics delayed 24h after ship_interval stayed 24h",
           "ship_h", 24, "cortex"),
        FAIL("mimir-store-index", "Mimir store-gateway index vs disable Mimir", "mimir", "mimir.yaml",
             "index_header", "index_header.lazy_loading_enabled: false",
             "index_header.lazy_loading_enabled: true",
             "mimir.enabled: true", "mimir.enabled: false", "Mimir", "MM-01", "blocks",
             "Cortex leftover / Pyroscope leftover",
             "Mimir pay-query OOM after index_header lazy loading stayed false",
             "oom", 1, "mimir", "platform-mimir"),
    ),
    (
        OK("pyroscope-max-block", "Pyroscope max block vs disable Pyroscope", "pyroscope", "pyroscope.yaml",
           "max_block_duration", "max_block_duration: 24h", "max_block_duration: 10m",
           "pyroscope.enabled: true", "pyroscope.enabled: false", "Pyroscope", "PY-02", "ingester",
           "Phlare leftover / Redash leftover",
           "Pyroscope pay-profiles compacted late after max_block_duration stayed 24h",
           "late_h", 24, "pyroscope"),
        FAIL("phlare-query-split", "Phlare query split vs disable Phlare", "phlare", "phlare.yaml",
             "split_queries_by_interval", "split_queries_by_interval: 0", "split_queries_by_interval: 15m",
             "phlare.enabled: true", "phlare.enabled: false", "Phlare", "PH-02", "querier",
             "Pyroscope leftover / Redash leftover",
             "Phlare pay-profiles timed out after split_queries_by_interval stayed 0",
             "timeout", 1, "phlare", "platform-phlare"),
    ),
    (
        OK("redash-fork-timeout", "Redash fork timeout vs disable Redash", "redash", "redash.env",
           "query.fork", "REDASH_QUERY_RESULTS_CLEANUP_MAX_AGE=1", "REDASH_JOB_EXPIRY_TIME=43200",
           "redash.enabled=true", "redash.enabled=false", "Redash", "RD-03", "rq",
           "Evidence leftover / Deepnote leftover",
           "Redash pay-sql jobs expired after JOB_EXPIRY_TIME stayed default 1s",
           "expire", 1, "redash"),
        FAIL("evidence-source-cache", "Evidence source cache vs disable Evidence", "evidence", "evidence.config.yaml",
             "sources.cache", "cache: false", "cache: true",
             "evidence.enabled: true", "evidence.enabled: false", "Evidence", "EV-03", "dbt",
             "Redash leftover / Deepnote leftover",
             "Evidence pay-dash re-queried after cache stayed false",
             "requery", 1, "evidence", "platform-evidence"),
    ),
    (
        OK("deepnote-idle-kernel", "Deepnote idle kernel vs disable Deepnote", "deepnote", "project.yml",
           "idle_timeout", "idle_timeout: 30s", "idle_timeout: 2h",
           "deepnote.enabled: true", "deepnote.enabled: false", "Deepnote", "DN-04", "hardware",
           "Count leftover / PowerBI leftover",
           "Deepnote pay-nb kernels died after idle_timeout stayed 30s",
           "dead_k", 1, "deepnote"),
        FAIL("count-cache-ttl", "Count SQL cache vs disable Count", "countco", "count.yml",
             "cache.ttl", "cache_ttl: 0", "cache_ttl: 3600",
             "count.enabled: true", "count.enabled: false", "Count", "CT-04", "cell",
             "Deepnote leftover / PowerBI leftover",
             "Count pay-cells hit warehouse every paint after cache_ttl stayed 0",
             "hit_wh", 1, "count", "platform-count"),
    ),
    (
        OK("powerbi-onprem-gw", "Power BI on-prem gateway vs disable gateway", "powerbi", "gateway.json",
           "ServiceTimeout", '"ServiceTimeout": 5', '"ServiceTimeout": 180',
           '"gateway.enabled": true', '"gateway.enabled": false', "Power BI", "PB-05", "refresh",
           "Sisense leftover / NiFi leftover",
           "Power BI pay-refresh aborted after ServiceTimeout stayed 5s",
           "aborts", 11, "powerbi"),
        FAIL("sisense-build-elasti", "Sisense ElastiCube build vs disable Sisense", "sisense", "cube.json",
             "build.timeout", '"buildTimeout": 10', '"buildTimeout": 14400',
             '"sisense.enabled": true', '"sisense.enabled": false', "Sisense", "SE-05", "ecube",
             "PowerBI leftover / NiFi leftover",
             "Sisense pay-cube aborted after buildTimeout stayed 10s",
             "aborts", 1, "sisense", "platform-sisense"),
    ),
    (
        OK("nifi-reg-bucket", "NiFi Registry bucket vs disable Registry", "nifireg", "nifi-registry.properties",
           "bucket.flow.diff", "nifi.registry.hooks=none", "nifi.registry.hooks=git",
           "nifi.registry.enabled=true", "nifi.registry.enabled=false", "NiFi Registry", "NR-06", "git",
           "Kafka REST leftover / Schema leftover",
           "NiFi pay-flows unversioned after hooks stayed none",
           "no_ver", 1, "nifireg"),
        FAIL("kafkarest-produce-max", "Kafka REST produce vs disable REST", "kafkarest", "kafka-rest.properties",
             "produce.max.bytes", "produce.max.request.size=1024", "produce.max.request.size=1048576",
             "kafka.rest.enabled=true", "kafka.rest.enabled=false", "Kafka REST", "KR-06", "buffer",
             "NiFi leftover / Schema leftover",
             "Kafka REST pay-events 413 after produce.max.request.size stayed 1024",
             "http_413", 1, "kafkarest", "platform-kafkarest"),
    ),
    (
        OK("schemareg-compat-fwd", "Schema Registry FORWARD vs disable SR", "schemareg", "schema-registry.properties",
           "compatibility", "compatibility=NONE", "compatibility=FORWARD",
           "schema.registry.enabled=true", "schema.registry.enabled=false", "Schema Registry", "SR-07", "mode",
           "Burrow leftover / AKHQ leftover",
           "Schema Registry pay-avro accepted breaks after compatibility stayed NONE",
           "breaks", 4, "sr"),
        FAIL("burrow-lag-check", "Burrow lag check vs disable Burrow", "burrow", "burrow.toml",
             "lagcheck", "httpserver.port=0", "lagcheck.intervals=10",
             "burrow.enabled=true", "burrow.enabled=false", "Burrow", "BU-07", "consumer",
             "Schema leftover / AKHQ leftover",
             "Burrow pay-lag silent after lagcheck stayed off",
             "no_lag", 1, "burrow", "platform-burrow"),
    ),
    (
        OK("akhq-connect-to", "AKHQ connect timeout vs disable AKHQ", "akhq", "akhq.yml",
           "connections.timeout", "connect-timeout: 200ms", "connect-timeout: 30s",
           "akhq.enabled: true", "akhq.enabled: false", "AKHQ", "AK-08", "cluster",
           "Redpanda Console leftover / Pulsar Manager leftover",
           "AKHQ pay-ui failed brokers after connect-timeout stayed 200ms",
           "fail_ui", 1, "akhq"),
        FAIL("rpconsole-cluster", "Redpanda Console cluster vs disable Console", "rpconsole", "console.yaml",
             "kafka.brokers", "kafka.brokers: []", "kafka.brokers: [pay:9092]",
             "console.enabled: true", "console.enabled: false", "Redpanda Console", "RC-08", "schema",
             "AKHQ leftover / Pulsar Manager leftover",
             "Redpanda Console pay-ui empty after brokers stayed []",
             "empty_ui", 1, "rpconsole", "platform-redpanda"),
    ),
    (
        OK("pulsarmgr-token", "Pulsar Manager JWT vs disable Manager", "pulsarmgr", "application.properties",
           "jwt.broker", "broker.jwt.enable=false", "broker.jwt.enable=true",
           "pulsar.manager.enabled=true", "pulsar.manager.enabled=false", "Pulsar Manager", "PM-09", "token",
           "Garage leftover / RustFS leftover",
           "Pulsar Manager pay-ops unauth after jwt.enable stayed false",
           "unauth", 1, "pulsarmgr"),
        FAIL("garage-cluster-layout", "Garage layout vs disable Garage", "garage", "garage.toml",
             "layout.assign", "replication_mode = \"none\"", "replication_mode = \"3\"",
             "garage.enabled = true", "garage.enabled = false", "Garage", "GG-09", "s3",
             "Pulsar leftover / RustFS leftover",
             "Garage pay-s3 unreplicated after replication_mode stayed none",
             "no_repl", 1, "garage", "platform-garage"),
    ),
    (
        OK("rustfs-ec-parity", "RustFS EC parity vs disable RustFS", "rustfs", "rustfs.toml",
           "ec.parity", "parity=0", "parity=2",
           "rustfs.enabled=true", "rustfs.enabled=false", "RustFS", "RF-10", "erasure",
           "Longhorn leftover / OpenEBS leftover",
           "RustFS pay-objects unreplicated after parity stayed 0",
           "no_ec", 1, "rustfs"),
        FAIL("longhorn-engine-rep", "Longhorn replica count vs disable Longhorn", "longhorn", "storageclass.yaml",
             "numberOfReplicas", "numberOfReplicas: \"1\"", "numberOfReplicas: \"3\"",
             "longhorn.enabled: true", "longhorn.enabled: false", "Longhorn", "LH-10", "engine",
             "RustFS leftover / OpenEBS leftover",
             "Longhorn pay-vol no HA after numberOfReplicas stayed 1",
             "no_ha", 1, "longhorn", "platform-longhorn"),
    ),
    (
        OK("openebs-jiva-rep", "OpenEBS Jiva replicas vs disable OpenEBS", "openebs", "sc.yaml",
           "Replicas", "Replicas: \"1\"", "Replicas: \"3\"",
           "openebs.enabled: true", "openebs.enabled: false", "OpenEBS", "OE-11", "cstor",
           "Rook leftover / Iceberg leftover",
           "OpenEBS pay-vol unreplicated after Replicas stayed 1",
           "no_repl", 1, "openebs"),
        FAIL("rook-osd-crush", "Rook CRUSH failure domain vs disable Rook", "rook", "cluster.yaml",
             "failureDomain", "failureDomain: osd", "failureDomain: host",
             "rook.enabled: true", "rook.enabled: false", "Rook", "RK-11", "osd",
             "OpenEBS leftover / Iceberg leftover",
             "Rook pay-pool lost host after failureDomain stayed osd",
             "host_loss", 1, "rook", "platform-rook"),
    ),
    (
        OK("kafkaui-poll", "Kafka UI poll timeout vs disable UI", "kafkaui", "config.yml",
           "polling.timeout", "kafka.poll-timeout-ms: 200", "kafka.poll-timeout-ms: 30000",
           "kafkaui.enabled: true", "kafkaui.enabled: false", "Kafka UI", "KU-12", "cluster",
           "Connect leftover / Iceberg leftover",
           "Kafka UI pay-topics empty after poll-timeout-ms stayed 200",
           "empty", 1, "kafkaui"),
        FAIL("kconnect-rest-to", "Kafka Connect REST timeout vs disable Connect", "kcrest", "connect.properties",
             "rest.advertised", "rest.request.timeout.ms=500", "rest.request.timeout.ms=30000",
             "connect.enabled=true", "connect.enabled=false", "Connect", "KC-12", "rest",
             "Kafka UI leftover / Iceberg leftover",
             "Connect pay-api 504 after rest.request.timeout.ms stayed 500",
             "http_504", 1, "kconnect", "platform-kconnect"),
    ),
    (
        OK("iceberg-sql-view", "Iceberg SQL views vs disable Iceberg", "icesqlv", "spark.sql",
           "spark.sql.catalog.pay.views", "spark.sql.catalog.pay.view-identifiers=false",
           "spark.sql.catalog.pay.view-identifiers=true",
           "format=iceberg", "format=hive", "Iceberg", "IV-13", "view",
           "Hudi leftover / Paimon leftover",
           "Iceberg pay-views unsupported after view-identifiers stayed false",
           "no_view", 1, "iceberg"),
        FAIL("hudi-hive-sync-mode", "Hudi hive sync mode vs disable Hudi", "hudihive", "hudi.properties",
             "hoodie.datasource.hive_sync.mode", "hoodie.datasource.hive_sync.mode=hms",
             "hoodie.datasource.hive_sync.mode=jdbc",
             "hoodie.enabled=true", "hoodie.enabled=false", "Hudi", "HH-13", "sync",
             "Iceberg leftover / Paimon leftover",
             "Hudi pay-hive never synced after hive_sync.mode stayed hms without HMS",
             "no_sync", 1, "hudi", "platform-hudi"),
    ),
    (
        OK("paimon-tag-num", "Paimon tag num vs disable Paimon", "paimontag", "t.yaml",
           "tag.num-retained-max", "tag.num-retained-max: 0", "tag.num-retained-max: 16",
           "paimon.enabled: true", "paimon.enabled: false", "Paimon", "PT-14", "tag",
           "Delta leftover / Flink leftover",
           "Paimon pay-cdc never tagged after tag.num-retained-max stayed 0",
           "no_tag", 1, "paimon"),
        FAIL("delta-identity-col", "Delta identity columns vs disable Delta", "deltaid", "delta.sql",
             "GENERATED BY DEFAULT AS IDENTITY", "id BIGINT", "id BIGINT GENERATED BY DEFAULT AS IDENTITY",
             "USING DELTA", "USING PARQUET", "Delta", "DI-14", "identity",
             "Paimon leftover / Flink leftover",
             "Delta pay-orders collided keys after identity stayed missing",
             "key_col", 1, "delta", "platform-delta"),
    ),
    (
        OK("flink-table-exec-sink", "Flink sink parallelism vs disable sink", "flinksink", "flink-conf.yaml",
           "table.exec.sink.not-null-enforcer", "table.exec.sink.not-null-enforcer: DROP",
           "table.exec.sink.not-null-enforcer: ERROR",
           "flink.enabled: true", "flink.enabled: false", "Flink", "FS-15", "sink",
           "Spark leftover / Trino leftover",
           "Flink pay-sink dropped nulls after not-null-enforcer stayed DROP",
           "drops", 9000, "flink"),
        FAIL("trino-writer-scaling", "Trino writer scaling vs disable Trino", "trinows", "config.properties",
             "scale-writers", "scale-writers=false", "scale-writers=true",
             "trino.enabled=true", "trino.enabled=false", "Trino", "TW-15", "writer",
             "Flink leftover / Spark leftover",
             "Trino pay-ctas one-writer after scale-writers stayed false",
             "one_writer", 1, "trino", "platform-trino"),
    ),
    (
        OK("presto-spooling-fs", "Presto spooling filesystem vs disable spool", "prestospf", "config.properties",
           "spooling.filesystem", "spooling.enabled=false", "spooling.filesystem=s3",
           "presto.enabled=true", "presto.enabled=false", "Presto", "PS-16", "spool",
           "Hive leftover / ClickHouse leftover",
           "Presto pay-fte OOM after spooling.enabled stayed false",
           "oom", 1, "presto"),
        FAIL("clickhouse-s3-queue", "ClickHouse S3Queue vs disable S3Queue", "chs3q", "pay.sql",
             "s3queue.mode", "ENGINE = S3('s3://pay')", "ENGINE = S3Queue('s3://pay', mode='ordered')",
             "ENGINE = S3", "ENGINE = File", "S3Queue", "CQ-16", "keeper",
             "Presto leftover / Hive leftover",
             "ClickHouse pay-ingest duplicated after S3Queue mode stayed missing",
             "dups", 1, "ch", "platform-clickhouse"),
    ),
    (
        OK("druid-msq-durable", "Druid MSQ durable storage vs disable MSQ", "druiddur", "runtime.properties",
           "msq.durable", "druid.msq.durable.storage.enable=false", "druid.msq.durable.storage.enable=true",
           "druid.enabled=true", "druid.enabled=false", "MSQ", "DD-17", "durable",
           "Pinot leftover / StarRocks leftover",
           "Druid pay-sql failed shuffle after durable.storage stayed false",
           "shuffle_fail", 1, "druid"),
        FAIL("starrocks-cloud-native", "StarRocks cloud-native vs disable CN", "srcn", "be.conf",
             "run_mode", "run_mode = shared_nothing", "run_mode = shared_data",
             "starrocks.enabled=true", "starrocks.enabled=false", "StarRocks", "SC-17", "cn",
             "Druid leftover / Pinot leftover",
             "StarRocks pay-facts local-only after run_mode stayed shared_nothing",
             "local_only", 1, "starrocks", "platform-starrocks"),
    ),
    (
        OK("doris-cloud-cache", "Doris cloud cache vs disable cloud", "doriscc", "be.conf",
           "file_cache", "enable_file_cache=false", "enable_file_cache=true",
           "doris.enabled=true", "doris.enabled=false", "Doris", "DC-18", "cache",
           "RisingWave leftover / Materialize leftover",
           "Doris pay-cloud scanned S3 after enable_file_cache stayed false",
           "s3_scan", 1, "doris"),
        FAIL("risingwave-s3-cache", "RisingWave S3 cache vs disable RW", "rws3c", "rw.toml",
             "s3.cache", "storage.s3.cache_size_mb=0", "storage.s3.cache_size_mb=8192",
             "risingwave.enabled=true", "risingwave.enabled=false", "RisingWave", "RS-18", "hummock",
             "Doris leftover / Materialize leftover",
             "RisingWave pay-cdc hit S3 after cache_size_mb stayed 0",
             "s3_hit", 1, "rw", "platform-risingwave"),
    ),
    (
        OK("materialize-cluster-size", "Materialize cluster size vs disable MZ", "mzsize", "mz.toml",
           "cluster.size", "SIZE = '3xsmall'", "SIZE = '4xlarge'",
           "mz.enabled=true", "mz.enabled=false", "Materialize", "MS-19", "cluster",
           "Redpanda leftover / Pulsar leftover",
           "Materialize pay-source lagged after SIZE stayed 3xsmall",
           "lag_s", 40, "mz"),
        FAIL("redpanda-shadow-idx", "Redpanda shadow indexing vs disable RP", "rpshadow", "redpanda.yaml",
             "cloud_storage_enable_remote_write", "cloud_storage_enable_remote_write: false",
             "cloud_storage_enable_remote_write: true",
             "redpanda.enabled: true", "redpanda.enabled: false", "Redpanda", "RS-19", "shadow",
             "Materialize leftover / Pulsar leftover",
             "Redpanda pay-topics local-only after remote_write stayed false",
             "local_only", 1, "redpanda", "platform-redpanda"),
    ),
    (
        OK("pulsar-offload", "Pulsar offload vs disable offload", "pulsaroff", "broker.conf",
           "offload", "managedLedgerOffloadDriver=", "managedLedgerOffloadDriver=aws-s3",
           "pulsar.enabled=true", "pulsar.enabled=false", "Pulsar", "PO-20", "offload",
           "NATS leftover / Rabbit leftover",
           "Pulsar pay-topics never offloaded after driver stayed empty",
           "no_offload", 1, "pulsar"),
        FAIL("nats-object-store", "NATS object store vs disable JetStream", "natsobj", "js.conf",
             "object.store", "object_store: false", "object_store: true",
           "jetstream: enabled", "jetstream: disabled", "JetStream", "NO-20", "object",
             "Pulsar leftover / Rabbit leftover",
             "NATS pay-blobs unsupported after object_store stayed false",
             "no_obj", 1, "nats", "platform-nats"),
    ),
    (
        OK("rocketmq-dledger-role", "RocketMQ DLedger vs disable DLedger", "rmqdl", "broker.conf",
           "enableDLegerCommitLog", "enableDLegerCommitLog=false", "enableDLegerCommitLog=true",
           "broker.enabled=true", "broker.enabled=false", "RocketMQ", "RD-21", "dledger",
           "Solace leftover / IBM MQ leftover",
           "RocketMQ pay-orders no HA after enableDLegerCommitLog stayed false",
           "no_ha", 1, "rocketmq"),
        FAIL("solace-replay", "Solace replay vs disable Solace", "solacerep", "vpn.conf",
             "replay", "replay=off", "replay=on",
             "solace.enabled=true", "solace.enabled=false", "Solace", "SR-21", "replay",
             "RocketMQ leftover / IBM MQ leftover",
             "Solace pay-orders could not replay after replay stayed off",
             "no_replay", 1, "solace", "platform-solace"),
    ),
    (
        OK("ibmmq-ams", "IBM MQ AMS vs disable AMS", "ibmmqams", "qm.ini",
           "ProtectionPolicy", "ProtectionPolicy=NONE", "ProtectionPolicy=INTEGRITY",
           "mq.enabled=true", "mq.enabled=false", "IBM MQ", "IA-22", "ams",
           "ZeroMQ leftover / Qpid leftover",
           "IBM MQ pay-xfer unsigned after ProtectionPolicy stayed NONE",
           "unsigned", 1, "ibmmq"),
        FAIL("zmq-curve", "ZeroMQ CURVE vs disable ZeroMQ", "zmqcurve", "sock.conf",
             "ZMQ_CURVE", "ZMQ_CURVE_SERVER=0", "ZMQ_CURVE_SERVER=1",
             "zmq.enabled=true", "zmq.enabled=false", "ZeroMQ", "ZC-22", "curve",
             "IBM MQ leftover / Qpid leftover",
             "ZeroMQ pay-ticks plaintext after CURVE stayed off",
             "plain", 1, "zmq", "platform-zmq"),
    ),
    (
        OK("qpid-sasl", "Qpid SASL vs disable Qpid", "qpidsasl", "qpidd.conf",
           "auth", "auth=no", "auth=yes",
           "qpid.enabled=true", "qpid.enabled=false", "Qpid", "QS-23", "sasl",
           "StarRocks leftover / Doris leftover",
           "Qpid pay-jobs anonymous after auth stayed no",
           "anon", 1, "qpid"),
        FAIL("clickhouse-keeper-log", "ClickHouse Keeper log vs disable Keeper", "chklog", "keeper.xml",
             "log_storage_path", "<log_storage_path>/tmp/klog</log_storage_path>",
             "<log_storage_path>/var/lib/clickhouse/coordination/log</log_storage_path>",
             "keeper.enabled=true", "keeper.enabled=false", "Keeper", "CK-23", "log",
             "Qpid leftover / StarRocks leftover",
             "ClickHouse Keeper pay-cluster lost log after path stayed /tmp",
             "tmp_log", 1, "ch", "platform-clickhouse"),
    ),
    (
        OK("druid-peon-chmask", "Druid peon chmod vs disable peon", "druidpeon", "runtime.properties",
           "peon.taskDirChmod", "druid.indexer.task.chmode=000", "druid.indexer.task.chmode=750",
           "druid.enabled=true", "druid.enabled=false", "Druid", "DP-24", "peon",
           "Pinot leftover / Hive leftover",
           "Druid pay-tasks world-writable after chmode stayed 000",
           "world", 1, "druid"),
        FAIL("pinot-realtime-llc2", "Pinot LLC flush vs disable realtime", "pinotllc2", "table.json",
             "flushThresholdTime", '"flushThresholdTime": "1s"', '"flushThresholdTime": "6h"',
             '"realtime": true', '"realtime": false', "realtime", "PL-24", "llc",
             "Druid leftover / Hive leftover",
             "Pinot pay-events tiny segments after flushThresholdTime stayed 1s",
             "tiny_segs", 1, "pinot", "platform-pinot"),
    ),
    (
        OK("hive-cbo-stats", "Hive CBO stats vs disable CBO", "hivecbo", "hive-site.xml",
           "hive.cbo.enable", "<value>false</value>", "<value>true</value>",
           "hive.enabled=true", "hive.enabled=false", "Hive", "HC-25", "cbo",
           "Spark leftover / Tez leftover",
           "Hive pay-sql nested-looped after hive.cbo.enable stayed false",
           "nlj", 1, "hive"),
        FAIL("spark-sql-adaptive2", "Spark AQE local shuffle vs disable AQE", "sparkls", "spark-defaults.conf",
             "localShuffleReader", "spark.sql.adaptive.localShuffleReader.enabled=false",
             "spark.sql.adaptive.localShuffleReader.enabled=true",
             "spark.sql.adaptive.enabled=true", "spark.sql.adaptive.enabled=false", "AQE", "SL-25", "local",
             "Hive leftover / Tez leftover",
             "Spark pay-join shuffled after localShuffleReader stayed false",
             "extra_shuffle", 1, "spark", "platform-spark"),
    ),
]


def plants_for(round_number: int):
    used = published_identities()
    for a, b in PAIRS:
        keys = {
            a["slug"].lower(),
            b["slug"].lower(),
            a["domain"].lower(),
            b["domain"].lower(),
        }
        if keys & used:
            continue
        try:
            guard(a)
            guard(b)
        except SystemExit:
            continue
        return (lambda r, s=a: build(r, s), lambda r, s=b: build(r, s))
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
        if rec["meta"]["generator"] != GENERATOR:
            raise SystemExit("bad generator")
        if rec["meta"]["round"] != args.round:
            raise SystemExit("bad round")
        if "[variant" in rec["goal"].lower():
            raise SystemExit(f"{rec['id']}: variant stamp")
        blob = json.dumps(rec)
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"{rec['id']}: banned key {bad}")
        if '"sim_or_real": "real"' in blob:
            raise SystemExit(f"{rec['id']}: sim_or_real real")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage:")
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "batch": str(batch), "notes": str(notes)}))


if __name__ == "__main__":
    sys.exit(main() or 0)
