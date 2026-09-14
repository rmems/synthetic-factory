#!/usr/bin/env python3
"""data-pipeline-repair mill r2850+ wave5."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

s = importlib.util.spec_from_file_location("dpr2631", "/tmp/dpr_mill_r2631.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
OK, FAIL, build, audit = m.OK, m.FAIL, m.build, m.audit
notes_for, published_identities, guard = m.notes_for, m.published_identities, m.guard
GENERATOR = m.GENERATOR

PAIRS = [
    (
        OK("trino-spooling-s3", "Trino spooling S3 vs disable spooling", "trinosp", "config.properties",
           "spooling.filesystem", "spooling.enabled=false", "spooling.filesystem=s3",
           "trino.enabled=true", "trino.enabled=false", "Trino", "TS-01", "spool",
           "Presto leftover / Hive leftover",
           "Trino pay-fte OOM after spooling.enabled stayed false",
           "oom", 1, "trino"),
        FAIL("hive-llap-io-elevator", "Hive LLAP IO elevator vs disable LLAP", "hivellio", "hive-site.xml",
             "hive.llap.io.allocator.mmap", "<value>false</value>", "<value>true</value>",
             "hive.llap.execution.mode=all", "hive.llap.execution.mode=none", "LLAP", "HL-01", "mmap",
             "Trino leftover / Hive leftover",
             "Hive pay-scan heap-cached after llap.io.allocator.mmap stayed false",
             "heap", 1, "hive", "platform-hive"),
    ),
    (
        OK("spark-aqe-local-shuffle", "Spark AQE local shuffle vs disable AQE", "sparkaqe2", "spark-defaults.conf",
           "localShuffleReader", "spark.sql.adaptive.localShuffleReader.enabled=false",
           "spark.sql.adaptive.localShuffleReader.enabled=true",
           "spark.sql.adaptive.enabled=true", "spark.sql.adaptive.enabled=false", "AQE", "SA-02", "local",
           "Flink leftover / Beam leftover",
           "Spark pay-join extra-shuffled after localShuffleReader stayed false",
           "extra_sh", 1, "spark"),
        FAIL("flink-reactive-scheduler", "Flink reactive scheduler vs disable Flink", "flinkrx2", "flink-conf.yaml",
             "jobmanager.scheduler", "jobmanager.scheduler: default", "jobmanager.scheduler: adaptive",
             "flink.enabled: true", "flink.enabled: false", "Flink", "FR-02", "adaptive",
             "Spark leftover / Beam leftover",
             "Flink pay-job never rescaled after scheduler stayed default",
             "no_scale", 1, "flink", "platform-flink"),
    ),
    (
        OK("kafka-share-groups2", "Kafka share groups vs disable share", "kshare2", "server.properties",
           "share.auto.offset.reset", "share.auto.offset.reset=latest", "share.auto.offset.reset=earliest",
           "share.groups.enable=true", "share.groups.enable=false", "share", "KS-03", "offset",
           "Redpanda leftover / Pulsar leftover",
           "Kafka pay-jobs skipped backlog after share.auto.offset.reset stayed latest",
           "skip", 1, "share"),
        FAIL("redpanda-archival2", "Redpanda archival vs disable archiver", "rparch2", "redpanda.yaml",
             "cloud_storage_enable_remote_read", "cloud_storage_enable_remote_read: false",
             "cloud_storage_enable_remote_read: true",
             "redpanda.enabled: true", "redpanda.enabled: false", "Redpanda", "RA-03", "archival",
             "Kafka leftover / Pulsar leftover",
             "Redpanda pay-consumers missed remote after remote_read stayed false",
             "no_remote", 1, "redpanda", "platform-redpanda"),
    ),
    (
        OK("pulsar-keyshared-sticky", "Pulsar Key_Shared sticky vs disable Key_Shared", "pksticky", "client.conf",
           "keySharedMode", "keySharedMode=AUTO_SPLIT", "keySharedMode=STICKY",
           "subscriptionType=Key_Shared", "subscriptionType=Exclusive", "Key_Shared", "PK-04", "sticky",
           "NATS leftover / Rabbit leftover",
           "Pulsar pay-jobs rehashed after keySharedMode stayed AUTO_SPLIT",
           "rehash", 1, "pulsar"),
        FAIL("nats-flow-control", "NATS flow control vs disable JetStream", "natsfc", "js.conf",
             "flow_control", "flow_control: false", "flow_control: true",
             "jetstream: enabled", "jetstream: disabled", "JetStream", "NF-04", "fc",
             "Pulsar leftover / Rabbit leftover",
             "NATS pay-consumers overrun after flow_control stayed false",
             "overrun", 1, "nats", "platform-nats"),
    ),
    (
        OK("rabbit-single-active", "RabbitMQ single active consumer vs disable SAC", "rabsac", "rabbit.conf",
           "single_active_consumer", "single_active_consumer = false", "single_active_consumer = true",
           "queue_type = quorum", "queue_type = classic", "SAC", "RS-05", "sac",
           "RocketMQ leftover / AMQ leftover",
           "RabbitMQ pay-jobs raced after single_active_consumer stayed false",
           "race", 1, "rabbit"),
        FAIL("rocketmq-pop-invisible", "RocketMQ pop invisible vs disable pop", "rmqinv", "broker.conf",
             "popInvisiblyTime", "popInvisiblyTime=1000", "popInvisiblyTime=30000",
             "enablePop=true", "enablePop=false", "pop", "RI-05", "invisible",
             "Rabbit leftover / AMQ leftover",
             "RocketMQ pay-jobs redelivered after popInvisiblyTime stayed 1s",
             "redeliver", 1, "rocketmq", "platform-rocketmq"),
    ),
    (
        OK("amq-network-ttl", "ActiveMQ network TTL vs disable network", "amqttl", "activemq.xml",
           "networkTTL", 'networkTTL="1"', 'networkTTL="4"',
           "broker.network=true", "broker.network=false", "ActiveMQ", "AN-06", "ttl",
           "IBM MQ leftover / Solace leftover",
           "ActiveMQ pay-orders dropped remote after networkTTL stayed 1",
           "drop_remote", 1, "amq"),
        FAIL("ibmmq-chl-maxmsgl", "IBM MQ channel MAXMSGL vs disable channel", "ibmmqch", "qm.ini",
             "MAXMSGL", "MAXMSGL=4096", "MAXMSGL=104857600",
             "mq.enabled=true", "mq.enabled=false", "IBM MQ", "IM-06", "maxmsgl",
             "ActiveMQ leftover / Solace leftover",
             "IBM MQ pay-xfer truncated after MAXMSGL stayed 4096",
             "trunc", 1, "ibmmq", "platform-ibmmq"),
    ),
    (
        OK("iceberg-wip-branch", "Iceberg WAP branch vs disable WAP", "icewap2", "spark.sql",
           "write.wap.enabled", "write.wap.enabled=false", "write.wap.enabled=true",
           "format=iceberg", "format=hive", "Iceberg", "IW-07", "wap",
           "Hudi leftover / Delta leftover",
           "Iceberg pay-publish wrote main after write.wap.enabled stayed false",
           "main_write", 1, "iceberg"),
        FAIL("hudi-clustering-plan", "Hudi clustering plan vs disable clustering", "hudiclust", "hudi.properties",
             "hoodie.clustering.inline", "hoodie.clustering.inline=false", "hoodie.clustering.inline=true",
             "hoodie.enabled=true", "hoodie.enabled=false", "Hudi", "HC-07", "cluster",
             "Iceberg leftover / Delta leftover",
             "Hudi pay-files small after clustering.inline stayed false",
             "tiny_files", 1, "hudi", "platform-hudi"),
    ),
    (
        OK("paimon-lookup-cache2", "Paimon lookup cache vs disable lookup", "paimonlk", "t.yaml",
           "lookup-cache", "lookup-cache-max-memory-size: 8mb", "lookup-cache-max-memory-size: 4gb",
           "paimon.enabled: true", "paimon.enabled: false", "Paimon", "PL-08", "lookup",
           "Delta leftover / Flink leftover",
           "Paimon pay-dim missed after lookup-cache stayed 8mb",
           "miss", 1, "paimon"),
        FAIL("delta-optimize-zorder", "Delta ZORDER vs disable optimize", "deltazo", "delta.sql",
             "ZORDER", "OPTIMIZE pay", "OPTIMIZE pay ZORDER BY (sku, dt)",
             "USING DELTA", "USING PARQUET", "Delta", "DZ-08", "zorder",
             "Paimon leftover / Flink leftover",
             "Delta pay-facts scanned after OPTIMIZE lacked ZORDER",
             "scan", 1, "delta", "platform-delta"),
    ),
    (
        OK("clickhouse-keeper-snapshot", "ClickHouse Keeper snapshot vs disable Keeper", "chksnap", "keeper.xml",
           "snapshot_distance", "<snapshot_distance>1000000</snapshot_distance>",
           "<snapshot_distance>10000</snapshot_distance>",
           "keeper.enabled=true", "keeper.enabled=false", "Keeper", "CS-09", "snap",
           "Druid leftover / Pinot leftover",
           "ClickHouse Keeper pay-log huge after snapshot_distance stayed 1e6",
           "huge_log", 1, "ch"),
        FAIL("druid-coordinator-period", "Druid coordinator period vs disable coordinator", "druidco", "runtime.properties",
             "coordinator.period", "druid.coordinator.period=PT1S", "druid.coordinator.period=PT30S",
             "druid.enabled=true", "druid.enabled=false", "Druid", "DC-09", "coord",
             "ClickHouse leftover / Pinot leftover",
             "Druid pay-cluster flapped after coordinator.period stayed PT1S",
             "flaps", 1, "druid", "platform-druid"),
    ),
    (
        OK("pinot-controller-period", "Pinot controller period vs disable controller", "pinotc", "controller.conf",
           "controller.period", "controller.task.frequencyPeriod=1s", "controller.task.frequencyPeriod=30m",
           "pinot.enabled=true", "pinot.enabled=false", "Pinot", "PC-10", "task",
           "StarRocks leftover / Doris leftover",
           "Pinot pay-tasks flapped after frequencyPeriod stayed 1s",
           "flaps", 1, "pinot"),
        FAIL("starrocks-be-heartbeat", "StarRocks BE heartbeat vs disable BE", "srhb", "fe.conf",
             "heartbeat_timeout_second", "heartbeat_timeout_second = 1", "heartbeat_timeout_second = 30",
             "starrocks.enabled=true", "starrocks.enabled=false", "StarRocks", "SH-10", "hb",
             "Pinot leftover / Doris leftover",
             "StarRocks pay-be flapped after heartbeat_timeout_second stayed 1",
             "flaps", 1, "starrocks", "platform-starrocks"),
    ),
    (
        OK("doris-be-heartbeat", "Doris BE heartbeat vs disable BE", "dorishb", "fe.conf",
           "heartbeat_timeout_second", "heartbeat_timeout_second = 1", "heartbeat_timeout_second = 30",
           "doris.enabled=true", "doris.enabled=false", "Doris", "DH-11", "hb",
           "RisingWave leftover / Materialize leftover",
           "Doris pay-be flapped after heartbeat_timeout_second stayed 1",
           "flaps", 1, "doris"),
        FAIL("materialize-persist-blob", "Materialize persist blob vs disable MZ", "mzblob", "mz.toml",
             "persist.blob", "persist.blob='mem://'", "persist.blob='s3://pay'",
             "mz.enabled=true", "mz.enabled=false", "Materialize", "MB-11", "blob",
             "Doris leftover / RisingWave leftover",
             "Materialize pay-source lost after persist.blob stayed mem://",
             "lost", 1, "mz", "platform-materialize"),
    ),
    (
        OK("airflow-triggerer", "Airflow triggerer vs disable triggerer", "airflowtr", "airflow.cfg",
           "triggerer.capacity", "triggerer.capacity=1", "triggerer.capacity=1000",
           "airflow.enabled=true", "airflow.enabled=false", "Airflow", "AT-12", "triggerer",
           "Dagster leftover / Prefect leftover",
           "Airflow pay-deferrable queued after triggerer.capacity stayed 1",
           "queued", 1, "airflow"),
        FAIL("dagster-sensor-interval", "Dagster sensor interval vs disable sensor", "dagsters", "sensor.py",
             "minimum_interval_seconds", "minimum_interval_seconds=3600", "minimum_interval_seconds=30",
             "dagster.enabled=true", "dagster.enabled=false", "Dagster", "DS-12", "sensor",
             "Airflow leftover / Prefect leftover",
             "Dagster pay-sensor lagged 1h after minimum_interval_seconds stayed 3600",
             "lag_h", 1, "dagster", "platform-dagster"),
    ),
    (
        OK("prefect-work-pool2", "Prefect work pool vs disable pool", "prefectwp", "pool.yaml",
           "concurrency_limit", "concurrency_limit: 1", "concurrency_limit: 32",
           "prefect.enabled: true", "prefect.enabled: false", "Prefect", "PP-13", "pool",
           "Mage leftover / Kestra leftover",
           "Prefect pay-flows serial after concurrency_limit stayed 1",
           "serial", 1, "prefect"),
        FAIL("mage-concurrency2", "Mage concurrency vs disable Mage", "magec2", "metadata.yaml",
             "concurrency", "concurrency: 1", "concurrency: 16",
             "mage.enabled: true", "mage.enabled: false", "Mage", "MC-13", "concurrency",
             "Prefect leftover / Kestra leftover",
             "Mage pay-pipeline serial after concurrency stayed 1",
             "serial", 1, "mage", "platform-mage"),
    ),
    (
        OK("kestra-worker-threads", "Kestra worker threads vs disable worker", "kestraw", "kestra.yml",
           "kestra.server.worker.threads", "threads: 1", "threads: 32",
           "kestra.enabled: true", "kestra.enabled: false", "Kestra", "KW-14", "worker",
           "Luigi leftover / Oozie leftover",
           "Kestra pay-flows serial after worker threads stayed 1",
           "serial", 1, "kestra"),
        FAIL("luigi-parallel-sched", "Luigi parallel-scheduling vs disable Luigi", "luigips", "luigi.cfg",
             "parallel-scheduling", "parallel-scheduling=false", "parallel-scheduling=true",
             "luigi.enabled=true", "luigi.enabled=false", "Luigi", "LP-14", "sched",
             "Kestra leftover / Oozie leftover",
             "Luigi pay-dag serial after parallel-scheduling stayed false",
             "serial", 1, "luigi", "platform-luigi"),
    ),
    (
        OK("nifi-content-repo2", "NiFi content repo vs disable content", "nificr", "nifi.properties",
           "nifi.content.repository.archive.max.retention.period",
           "nifi.content.repository.archive.max.retention.period=30 days",
           "nifi.content.repository.archive.max.retention.period=12 hours",
           "nifi.enabled=true", "nifi.enabled=false", "NiFi", "NC-15", "content",
           "Kafka leftover / Flink leftover",
           "NiFi pay-flow disk-filled after content archive retention stayed 30 days",
           "disk_full", 1, "nifi"),
        FAIL("kconnect-plugin-path", "Kafka Connect plugin path vs disable Connect", "kcplug", "connect.properties",
             "plugin.path", "plugin.path=/tmp/empty", "plugin.path=/usr/share/java/connect",
             "connect.enabled=true", "connect.enabled=false", "Connect", "KP-15", "plugin",
             "NiFi leftover / Kafka leftover",
             "Connect pay-sink ClassNotFound after plugin.path stayed /tmp/empty",
             "cnf", 1, "kconnect", "platform-kconnect"),
    ),
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
