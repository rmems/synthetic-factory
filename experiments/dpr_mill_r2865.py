#!/usr/bin/env python3
"""data-pipeline-repair mill r2865+ wave6."""
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
        OK("es-frozen-tier", "Elasticsearch frozen tier vs disable ILM", "esfrozen", "ilm.json",
           "frozen", '"min_age": "0d", "actions": {}', '"min_age": "30d", "actions": {"migrate": {"enabled": true}}',
           "ilm.enabled=true", "ilm.enabled=false", "ILM", "EF-01", "frozen",
           "Solr leftover / OpenSearch leftover",
           "Elasticsearch pay-logs hot after frozen migrate stayed missing",
           "hot_gi", 40, "es"),
        FAIL("solr-cloud-zk", "SolrCloud ZK chroot vs disable SolrCloud", "solrzk", "solr.xml",
             "zkHost", "zkHost=localhost:2181/", "zkHost=zk:2181/pay",
             "solr.cloud=true", "solr.cloud=false", "SolrCloud", "SZ-01", "zk",
             "ES leftover / OpenSearch leftover",
             "Solr pay-coll mixed after zkHost stayed localhost:/",
             "mix", 1, "solr", "platform-solr"),
    ),
    (
        OK("opensearch-ultrawarm", "OpenSearch UltraWarm vs disable UW", "osuw", "opensearch.yml",
           "ultrawarm.enabled", "ultrawarm.enabled: false", "ultrawarm.enabled: true",
           "opensearch.enabled: true", "opensearch.enabled: false", "UltraWarm", "OU-02", "warm",
           "Vespa leftover / Weaviate leftover",
           "OpenSearch pay-logs never warmed after ultrawarm.enabled stayed false",
           "no_warm", 1, "os"),
        FAIL("vespa-content-red", "Vespa content redundancy vs disable Vespa", "vespared", "services.xml",
             "redundancy", "<redundancy>1</redundancy>", "<redundancy>3</redundancy>",
             "vespa.enabled=true", "vespa.enabled=false", "Vespa", "VR-02", "redundancy",
             "OpenSearch leftover / Weaviate leftover",
             "Vespa pay-docs unreplicated after redundancy stayed 1",
             "no_repl", 1, "vespa", "platform-vespa"),
    ),
    (
        OK("weaviate-replication", "Weaviate replication vs disable Weaviate", "weavrepl", "weaviate.yml",
           "replicationFactor", "replicationFactor: 1", "replicationFactor: 3",
           "weaviate.enabled: true", "weaviate.enabled: false", "Weaviate", "WR-03", "rf",
           "Milvus leftover / Qdrant leftover",
           "Weaviate pay-embed no HA after replicationFactor stayed 1",
           "no_ha", 1, "weaviate"),
        FAIL("milvus-query-node", "Milvus query node vs disable Milvus", "milvusqn", "milvus.yaml",
             "queryNode.gracefulTime", "queryNode.gracefulTime: 0", "queryNode.gracefulTime: 2000",
             "milvus.enabled: true", "milvus.enabled: false", "Milvus", "MQ-03", "qn",
             "Weaviate leftover / Qdrant leftover",
             "Milvus pay-search stale after queryNode.gracefulTime stayed 0",
             "stale", 1, "milvus", "platform-milvus"),
    ),
    (
        OK("qdrant-replication", "Qdrant replication vs disable Qdrant", "qdrantrep", "config.yaml",
           "replication_factor", "replication_factor: 1", "replication_factor: 3",
           "qdrant.enabled: true", "qdrant.enabled: false", "Qdrant", "QR-04", "rf",
           "Chroma leftover / Lance leftover",
           "Qdrant pay-embed no HA after replication_factor stayed 1",
           "no_ha", 1, "qdrant"),
        FAIL("chroma-heartbeat", "Chroma heartbeat vs disable Chroma", "chromahb", "chroma.yml",
             "heartbeat_interval", "heartbeat_interval_ms: 1", "heartbeat_interval_ms: 10000",
             "chroma.enabled: true", "chroma.enabled: false", "Chroma", "CH-04", "hb",
             "Qdrant leftover / Lance leftover",
             "Chroma pay-embed flapped after heartbeat_interval_ms stayed 1",
             "flaps", 1, "chroma", "platform-chroma"),
    ),
    (
        OK("lancedb-version", "LanceDB versioning vs disable LanceDB", "lancever", "table.py",
           "enable_v2_manifest_paths", "enable_v2_manifest_paths=False", "enable_v2_manifest_paths=True",
           "lance.enabled=True", "lance.enabled=False", "LanceDB", "LV-05", "manifest",
           "Neo4j leftover / Janus leftover",
           "LanceDB pay-embed slow listing after v2 manifest stayed False",
           "slow_list", 1, "lancedb"),
        FAIL("neo4j-causal", "Neo4j causal cluster vs disable cluster", "neo4jcc", "neo4j.conf",
             "initial.mode", "initial.server.mode_constraint=PRIMARY",
             "initial.dbms.default_primaries_count=3",
             "neo4j.enabled=true", "neo4j.enabled=false", "Neo4j", "NC-05", "cluster",
             "Lance leftover / Janus leftover",
             "Neo4j pay-graph single after default_primaries_count stayed missing",
             "single", 1, "neo4j", "platform-neo4j"),
    ),
    (
        OK("janus-backend", "JanusGraph backend vs disable Janus", "janusbe", "janus.properties",
           "storage.backend", "storage.backend=inmemory", "storage.backend=cql",
           "janus.enabled=true", "janus.enabled=false", "Janus", "JB-06", "backend",
           "Dgraph leftover / Arango leftover",
           "Janus pay-graph lost after storage.backend stayed inmemory",
           "lost", 1, "janus"),
        FAIL("dgraph-alpha", "Dgraph alpha vs disable Dgraph", "dgraphal", "dgraph.yml",
             "idx", "idx=1", "idx=1,2,3",
             "dgraph.enabled=true", "dgraph.enabled=false", "Dgraph", "DA-06", "alpha",
             "Janus leftover / Arango leftover",
             "Dgraph pay-graph no HA after idx stayed 1",
             "no_ha", 1, "dgraph", "platform-dgraph"),
    ),
    (
        OK("arangodb-agency", "ArangoDB agency vs disable cluster", "arangoag", "arangod.conf",
           "agency.size", "agency.size=1", "agency.size=3",
           "arango.enabled=true", "arango.enabled=false", "ArangoDB", "AA-07", "agency",
           "Couchbase leftover / Mongo leftover",
           "ArangoDB pay-docs no HA after agency.size stayed 1",
           "no_ha", 1, "arango"),
        FAIL("couchbase-xdcr", "Couchbase XDCR vs disable XDCR", "cbxdcr", "cluster.json",
             "xdcr", '"xdcr": false', '"xdcr": true',
             '"couchbase.enabled": true', '"couchbase.enabled": false', "Couchbase", "CX-07", "xdcr",
             "Arango leftover / Mongo leftover",
             "Couchbase pay-kv unreplicated after xdcr stayed false",
             "no_xdcr", 1, "couchbase", "platform-couchbase"),
    ),
    (
        OK("mongo-change-stream", "MongoDB change streams vs disable CS", "mongocs", "mongod.conf",
           "changeStreamPreAndPostImages", "changeStreamPreAndPostImages: false",
           "changeStreamPreAndPostImages: true",
           "mongo.enabled: true", "mongo.enabled: false", "MongoDB", "MC-08", "cs",
           "Redis leftover / KeyDB leftover",
           "Mongo pay-cdc missed images after changeStreamPreAndPostImages stayed false",
           "no_img", 1, "mongo"),
        FAIL("redis-cluster-slot", "Redis Cluster slots vs disable cluster", "redisslot", "redis.conf",
             "cluster-enabled", "cluster-enabled no", "cluster-enabled yes",
             "redis.enabled=true", "redis.enabled=false", "Redis", "RS-08", "slot",
             "Mongo leftover / KeyDB leftover",
             "Redis pay-kv single after cluster-enabled stayed no",
             "single", 1, "redis", "platform-redis"),
    ),
    (
        OK("keydb-active-repl", "KeyDB active-rep vs disable KeyDB", "keydbrep", "keydb.conf",
           "active-replica", "active-replica no", "active-replica yes",
           "keydb.enabled=true", "keydb.enabled=false", "KeyDB", "KR-09", "replica",
           "Dragonfly leftover / Valkey leftover",
           "KeyDB pay-kv one-way after active-replica stayed no",
           "one_way", 1, "keydb"),
        FAIL("dragonfly-replica", "Dragonfly replica vs disable Dragonfly", "dflyrep", "dragonfly.conf",
             "replicaof", "replicaof=", "replicaof pay-primary 6379",
             "dragonfly.enabled=true", "dragonfly.enabled=false", "Dragonfly", "DR-09", "replica",
             "KeyDB leftover / Valkey leftover",
             "Dragonfly pay-kv no replica after replicaof stayed empty",
             "no_rep", 1, "dragonfly", "platform-dragonfly"),
    ),
    (
        OK("valkey-cluster", "Valkey cluster vs disable cluster", "valkeycl", "valkey.conf",
           "cluster-enabled", "cluster-enabled no", "cluster-enabled yes",
           "valkey.enabled=true", "valkey.enabled=false", "Valkey", "VC-10", "cluster",
           "Memcached leftover / Hazelcast leftover",
           "Valkey pay-kv single after cluster-enabled stayed no",
           "single", 1, "valkey"),
        FAIL("memcached-extstore", "Memcached extstore vs disable memcached", "memext", "memcached.conf",
             "ext_path", "ext_path=", "ext_path=/var/extstore:64G",
             "memcached.enabled=true", "memcached.enabled=false", "Memcached", "ME-10", "extstore",
             "Valkey leftover / Hazelcast leftover",
             "Memcached pay-cache RAM-only after ext_path stayed empty",
             "ram_only", 1, "memcached", "platform-memcached"),
    ),
    (
        OK("hazelcast-wan-rep", "Hazelcast WAN vs disable WAN", "hzwan", "hazelcast.yaml",
           "wan-replication", "wan-replication: {}", "wan-replication: {pay: {batch-size: 500}}",
           "hazelcast.enabled: true", "hazelcast.enabled: false", "Hazelcast", "HW-11", "wan",
           "Ignite leftover / Infinispan leftover",
           "Hazelcast pay-map unreplicated after wan-replication stayed {}",
           "no_wan", 1, "hazelcast"),
        FAIL("ignite-baseline2", "Ignite baseline auto-adjust vs disable Ignite", "igniteba", "ignite.xml",
             "baselineAutoAdjustEnabled", "baselineAutoAdjustEnabled=false", "baselineAutoAdjustEnabled=true",
             "ignite.enabled=true", "ignite.enabled=false", "Ignite", "IB-11", "baseline",
             "Hazelcast leftover / Infinispan leftover",
             "Ignite pay-cache refused joins after baselineAutoAdjust stayed false",
             "join_refuse", 1, "ignite", "platform-ignite"),
    ),
    (
        OK("infinispan-xsite2", "Infinispan xsite vs disable xsite", "infinisx", "infinispan.xml",
           "backups", "<backups/>", "<backups><backup site=\"dr\" strategy=\"SYNC\"/></backups>",
           "infinispan.enabled=true", "infinispan.enabled=false", "Infinispan", "IX-12", "xsite",
           "Geode leftover / Couch leftover",
           "Infinispan pay-cache no DR after backups stayed empty",
           "no_dr", 1, "infinispan"),
        FAIL("geode-diskstore", "Geode disk-store vs disable Geode", "geodeds", "cache.xml",
             "disk-store", "<disk-store name=\"pay\" allow-force-compaction=\"false\"/>",
             "<disk-store name=\"pay\" allow-force-compaction=\"true\"/>",
             "geode.enabled=true", "geode.enabled=false", "Geode", "GD-12", "disk",
             "Infinispan leftover / Couch leftover",
             "Geode pay-kv never compacted after allow-force-compaction stayed false",
             "no_compact", 1, "geode", "platform-geode"),
    ),
    (
        OK("trino-fault-tolerant2", "Trino FTE exchange vs disable FTE", "trinofte", "config.properties",
           "exchange-manager", "exchange-manager.name=noop", "exchange-manager.name=filesystem",
           "retry-policy=TASK", "retry-policy=NONE", "FTE", "TF-13", "exchange",
           "Presto leftover / Hive leftover",
           "Trino pay-join lost shuffle after exchange-manager stayed noop",
           "lost_sh", 1, "trino"),
        FAIL("presto-resource-overcommit", "Presto memory overcommit vs disable Presto", "prestooc", "config.properties",
             "query.low-memory-killer", "query.low-memory-killer.policy=none",
             "query.low-memory-killer.policy=total-reservation",
             "presto.enabled=true", "presto.enabled=false", "Presto", "PO-13", "killer",
             "Trino leftover / Hive leftover",
             "Presto pay-sql OOM after low-memory-killer stayed none",
             "oom", 1, "presto", "platform-presto"),
    ),
    (
        OK("hive-tez-keep-alive", "Hive Tez keep-alive vs disable Tez", "hivetezka", "tez-site.xml",
           "tez.am.keep.alive", "tez.am.keep.alive=false", "tez.am.keep.alive=true",
           "hive.execution.engine=tez", "hive.execution.engine=mr", "Tez", "HT-14", "keepalive",
           "Spark leftover / Flink leftover",
           "Hive pay-sql relaunched AM after tez.am.keep.alive stayed false",
           "relaunch", 1, "hive"),
        FAIL("spark-shuffle-service", "Spark shuffle service vs disable ESS", "sparkess", "spark-defaults.conf",
             "spark.shuffle.service.enabled", "spark.shuffle.service.enabled=false",
             "spark.shuffle.service.enabled=true",
             "spark.dynamicAllocation.enabled=true", "spark.dynamicAllocation.enabled=false", "ESS", "SS-14", "shuffle",
             "Hive leftover / Flink leftover",
             "Spark pay-join lost shuffle after shuffle.service.enabled stayed false",
             "lost_sh", 1, "spark", "platform-spark"),
    ),
    (
        OK("flink-ha-zookeeper", "Flink HA ZK vs disable HA", "flinkhazk", "flink-conf.yaml",
           "high-availability", "high-availability: NONE", "high-availability: ZOOKEEPER",
           "flink.enabled: true", "flink.enabled: false", "Flink", "FH-15", "ha",
           "Kafka leftover / Pulsar leftover",
           "Flink pay-job lost JM after high-availability stayed NONE",
           "lost_jm", 1, "flink"),
        FAIL("kafka-unclean-leader", "Kafka unclean leader vs disable ISR", "kafkaui2", "server.properties",
             "unclean.leader.election.enable", "unclean.leader.election.enable=true",
             "unclean.leader.election.enable=false",
             "kafka.enabled=true", "kafka.enabled=false", "Kafka", "KU-15", "isr",
             "Flink leftover / Pulsar leftover",
             "Kafka pay-cdc elected unclean after unclean.leader.election stayed true",
             "unclean", 1, "kafka", "platform-kafka"),
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
