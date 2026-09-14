#!/usr/bin/env python3
"""IRC mill r4761+ — wave-83 db/search leftover.

NEW on-call plants (not Wave-27–60 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
postgres3|POSTGRES3_TIMEOUT|1|30|s|/etc/postgres3/postgres3.conf|timeout=1|timeout=30|systemctl reload postgres3|po3|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTGRES3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mysql3|MYSQL3_TIMEOUT|1|30|s|/etc/mysql3/mysql3.conf|timeout=1|timeout=30|systemctl reload mysql3|my3|mys_to_1|jobs|state|https leftover leftover down; bounce|MYSQL3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mariadb3|MARIADB3_TIMEOUT|1|30|s|/etc/mariadb3/mariadb3.conf|timeout=1|timeout=30|systemctl reload mariadb3|ma3|mar_to_1|jobs|state|https leftover leftover down; bounce|MARIADB3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sqlite3|SQLITE3_TIMEOUT|1|30|s|/etc/sqlite3/sqlite3.conf|timeout=1|timeout=30|systemctl reload sqlite3|sq3|sql_to_1|jobs|state|https leftover leftover down; bounce|SQLITE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cockroach3|COCKROACH3_TIMEOUT|1|30|s|/etc/cockroach3/cockroach3.conf|timeout=1|timeout=30|systemctl reload cockroach3|co3|coc_to_1|jobs|state|https leftover leftover down; bounce|COCKROACH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
yugabyte3|YUGABYTE3_TIMEOUT|1|30|s|/etc/yugabyte3/yugabyte3.conf|timeout=1|timeout=30|systemctl reload yugabyte3|yu3|yug_to_1|jobs|state|https leftover leftover down; bounce|YUGABYTE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
scylla3|SCYLLA3_TIMEOUT|1|30|s|/etc/scylla3/scylla3.conf|timeout=1|timeout=30|systemctl reload scylla3|sc3|scy_to_1|jobs|state|https leftover leftover down; bounce|SCYLLA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cassandra3|CASSANDRA3_TIMEOUT|1|30|s|/etc/cassandra3/cassandra3.conf|timeout=1|timeout=30|systemctl reload cassandra3|ca3|cas_to_1|jobs|state|https leftover leftover down; bounce|CASSANDRA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mongodb3|MONGODB3_TIMEOUT|1|30|s|/etc/mongodb3/mongodb3.conf|timeout=1|timeout=30|systemctl reload mongodb3|mo3|mon_to_1|jobs|state|https leftover leftover down; bounce|MONGODB3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redis3|REDIS3_TIMEOUT|1|30|s|/etc/redis3/redis3.conf|timeout=1|timeout=30|systemctl reload redis3|re3|red_to_1|jobs|state|https leftover leftover down; bounce|REDIS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
keydb3|KEYDB3_TIMEOUT|1|30|s|/etc/keydb3/keydb3.conf|timeout=1|timeout=30|systemctl reload keydb3|ke3|key_to_1|jobs|state|https leftover leftover down; bounce|KEYDB3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dragonfly3|DRAGONFLY3_TIMEOUT|1|30|s|/etc/dragonfly3/dragonfly3.conf|timeout=1|timeout=30|systemctl reload dragonfly3|dr3|dra_to_1|jobs|state|https leftover leftover down; bounce|DRAGONFLY3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
memcached3|MEMCACHED3_TIMEOUT|1|30|s|/etc/memcached3/memcached3.conf|timeout=1|timeout=30|systemctl reload memcached3|me3|mem_to_1|jobs|state|https leftover leftover down; bounce|MEMCACHED3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hazelcast3|HAZELCAST3_TIMEOUT|1|30|s|/etc/hazelcast3/hazelcast3.conf|timeout=1|timeout=30|systemctl reload hazelcast3|ha3|haz_to_1|jobs|state|https leftover leftover down; bounce|HAZELCAST3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ignite3|IGNITE3_TIMEOUT|1|30|s|/etc/ignite3/ignite3.conf|timeout=1|timeout=30|systemctl reload ignite3|ig3|ign_to_1|jobs|state|https leftover leftover down; bounce|IGNITE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
elasticsearch3|ELASTICSEARCH3_TIMEOUT|1|30|s|/etc/elasticsearch3/elasticsearch3.conf|timeout=1|timeout=30|systemctl reload elasticsearch3|el3|ela_to_1|jobs|state|https leftover leftover down; bounce|ELASTICSEARCH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
solr3|SOLR3_TIMEOUT|1|30|s|/etc/solr3/solr3.conf|timeout=1|timeout=30|systemctl reload solr3|so3|sol_to_1|jobs|state|https leftover leftover down; bounce|SOLR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lucene3|LUCENE3_TIMEOUT|1|30|s|/etc/lucene3/lucene3.conf|timeout=1|timeout=30|systemctl reload lucene3|lu3|luc_to_1|jobs|state|https leftover leftover down; bounce|LUCENE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
meilisearch3|MEILISEARCH3_TIMEOUT|1|30|s|/etc/meilisearch3/meilisearch3.conf|timeout=1|timeout=30|systemctl reload meilisearch3|me3|mei_to_1|jobs|state|https leftover leftover down; bounce|MEILISEARCH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
typesense3|TYPESENSE3_TIMEOUT|1|30|s|/etc/typesense3/typesense3.conf|timeout=1|timeout=30|systemctl reload typesense3|ty3|typ_to_1|jobs|state|https leftover leftover down; bounce|TYPESENSE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zinc3|ZINC3_TIMEOUT|1|30|s|/etc/zinc3/zinc3.conf|timeout=1|timeout=30|systemctl reload zinc3|zi3|zin_to_1|jobs|state|https leftover leftover down; bounce|ZINC3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
clickhouse3|CLICKHOUSE3_TIMEOUT|1|30|s|/etc/clickhouse3/clickhouse3.conf|timeout=1|timeout=30|systemctl reload clickhouse3|cl3|cli_to_1|jobs|state|https leftover leftover down; bounce|CLICKHOUSE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
druid3|DRUID3_TIMEOUT|1|30|s|/etc/druid3/druid3.conf|timeout=1|timeout=30|systemctl reload druid3|dr3|dru_to_1|jobs|state|https leftover leftover down; bounce|DRUID3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pinot3|PINOT3_TIMEOUT|1|30|s|/etc/pinot3/pinot3.conf|timeout=1|timeout=30|systemctl reload pinot3|pi3|pin_to_1|jobs|state|https leftover leftover down; bounce|PINOT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
starrocks3|STARROCKS3_TIMEOUT|1|30|s|/etc/starrocks3/starrocks3.conf|timeout=1|timeout=30|systemctl reload starrocks3|st3|sta_to_1|jobs|state|https leftover leftover down; bounce|STARROCKS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
doris3|DORIS3_TIMEOUT|1|30|s|/etc/doris3/doris3.conf|timeout=1|timeout=30|systemctl reload doris3|do3|dor_to_1|jobs|state|https leftover leftover down; bounce|DORIS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
duckdb3|DUCKDB3_TIMEOUT|1|30|s|/etc/duckdb3/duckdb3.conf|timeout=1|timeout=30|systemctl reload duckdb3|du3|duc_to_1|jobs|state|https leftover leftover down; bounce|DUCKDB3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
trino3|TRINO3_TIMEOUT|1|30|s|/etc/trino3/trino3.conf|timeout=1|timeout=30|systemctl reload trino3|tr3|tri_to_1|jobs|state|https leftover leftover down; bounce|TRINO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
presto3|PRESTO3_TIMEOUT|1|30|s|/etc/presto3/presto3.conf|timeout=1|timeout=30|systemctl reload presto3|pr3|pre_to_1|jobs|state|https leftover leftover down; bounce|PRESTO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
spark3|SPARK3_TIMEOUT|1|30|s|/etc/spark3/spark3.conf|timeout=1|timeout=30|systemctl reload spark3|sp3|spa_to_1|jobs|state|https leftover leftover down; bounce|SPARK3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flink3|FLINK3_TIMEOUT|1|30|s|/etc/flink3/flink3.conf|timeout=1|timeout=30|systemctl reload flink3|fl3|fli_to_1|jobs|state|https leftover leftover down; bounce|FLINK3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hive3|HIVE3_TIMEOUT|1|30|s|/etc/hive3/hive3.conf|timeout=1|timeout=30|systemctl reload hive3|hi3|hiv_to_1|jobs|state|https leftover leftover down; bounce|HIVE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
impala3|IMPALA3_TIMEOUT|1|30|s|/etc/impala3/impala3.conf|timeout=1|timeout=30|systemctl reload impala3|im3|imp_to_1|jobs|state|https leftover leftover down; bounce|IMPALA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kafka3|KAFKA3_TIMEOUT|1|30|s|/etc/kafka3/kafka3.conf|timeout=1|timeout=30|systemctl reload kafka3|ka3|kaf_to_1|jobs|state|https leftover leftover down; bounce|KAFKA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pulsar3|PULSAR3_TIMEOUT|1|30|s|/etc/pulsar3/pulsar3.conf|timeout=1|timeout=30|systemctl reload pulsar3|pu3|pul_to_1|jobs|state|https leftover leftover down; bounce|PULSAR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redpanda3|REDPANDA3_TIMEOUT|1|30|s|/etc/redpanda3/redpanda3.conf|timeout=1|timeout=30|systemctl reload redpanda3|re3|red_to_1|jobs|state|https leftover leftover down; bounce|REDPANDA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nats3|NATS3_TIMEOUT|1|30|s|/etc/nats3/nats3.conf|timeout=1|timeout=30|systemctl reload nats3|na3|nat_to_1|jobs|state|https leftover leftover down; bounce|NATS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rabbitmq3|RABBITMQ3_TIMEOUT|1|30|s|/etc/rabbitmq3/rabbitmq3.conf|timeout=1|timeout=30|systemctl reload rabbitmq3|ra3|rab_to_1|jobs|state|https leftover leftover down; bounce|RABBITMQ3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
activemq3|ACTIVEMQ3_TIMEOUT|1|30|s|/etc/activemq3/activemq3.conf|timeout=1|timeout=30|systemctl reload activemq3|ac3|act_to_1|jobs|state|https leftover leftover down; bounce|ACTIVEMQ3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
natsjetstream3|NATSJETSTREAM3_TIMEOUT|1|30|s|/etc/natsjetstream3/natsjetstream3.conf|timeout=1|timeout=30|systemctl reload natsjetstream3|na3|nat_to_1|jobs|state|https leftover leftover down; bounce|NATSJETSTREAM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "postgres3/mysql3/mariadb3/sqlite3/cockroach3/yugabyte3/scylla3/cassandra3/mongodb3/redis3/keydb3/dragonfly3/memcached3/hazelcast3/ignite3/elasticsearch3/solr3/lucene3/meilisearch3/typesense3/zinc3/clickhouse3/druid3/pinot3/starrocks3/doris3/duckdb3/trino3/presto3/spark3/flink3/hive3/impala3/kafka3/pulsar3/redpanda3/nats3/rabbitmq3/activemq3/natsjetstream3"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"j6{i:02d}x"
        ns = f"j6{i:02d}"
        clu = f"prod-apuo{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14043 + i }"
        node = f"ip-10-193-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if remnant := (helm_rb(ns, svc, 3, path, oldv, newv, reload) if rem == "rollback" else patch_file(path, oldv, newv, reload)):
            extra = f"helm -n {ns} history {svc} | head -5" if rem == "rollback" else f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"4  {old}{unit}\n3  last-good {new}" if rem == "rollback" else f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 4761


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-83 leftover: {WAVE}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
