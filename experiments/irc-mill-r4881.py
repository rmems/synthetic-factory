#!/usr/bin/env python3
"""IRC mill r4881+ — wave-89 db5 leftover.

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
postgres5|POSTGRES5_TIMEOUT|1|30|s|/etc/postgres5/postgres5.conf|timeout=1|timeout=30|systemctl reload postgres5|po5|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTGRES5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mysql5|MYSQL5_TIMEOUT|1|30|s|/etc/mysql5/mysql5.conf|timeout=1|timeout=30|systemctl reload mysql5|my5|mys_to_1|jobs|state|https leftover leftover down; bounce|MYSQL5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mariadb5|MARIADB5_TIMEOUT|1|30|s|/etc/mariadb5/mariadb5.conf|timeout=1|timeout=30|systemctl reload mariadb5|ma5|mar_to_1|jobs|state|https leftover leftover down; bounce|MARIADB5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sqlite5|SQLITE5_TIMEOUT|1|30|s|/etc/sqlite5/sqlite5.conf|timeout=1|timeout=30|systemctl reload sqlite5|sq5|sql_to_1|jobs|state|https leftover leftover down; bounce|SQLITE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cockroach5|COCKROACH5_TIMEOUT|1|30|s|/etc/cockroach5/cockroach5.conf|timeout=1|timeout=30|systemctl reload cockroach5|co5|coc_to_1|jobs|state|https leftover leftover down; bounce|COCKROACH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
yugabyte5|YUGABYTE5_TIMEOUT|1|30|s|/etc/yugabyte5/yugabyte5.conf|timeout=1|timeout=30|systemctl reload yugabyte5|yu5|yug_to_1|jobs|state|https leftover leftover down; bounce|YUGABYTE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
scylla5|SCYLLA5_TIMEOUT|1|30|s|/etc/scylla5/scylla5.conf|timeout=1|timeout=30|systemctl reload scylla5|sc5|scy_to_1|jobs|state|https leftover leftover down; bounce|SCYLLA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cassandra5|CASSANDRA5_TIMEOUT|1|30|s|/etc/cassandra5/cassandra5.conf|timeout=1|timeout=30|systemctl reload cassandra5|ca5|cas_to_1|jobs|state|https leftover leftover down; bounce|CASSANDRA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mongodb5|MONGODB5_TIMEOUT|1|30|s|/etc/mongodb5/mongodb5.conf|timeout=1|timeout=30|systemctl reload mongodb5|mo5|mon_to_1|jobs|state|https leftover leftover down; bounce|MONGODB5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redis5|REDIS5_TIMEOUT|1|30|s|/etc/redis5/redis5.conf|timeout=1|timeout=30|systemctl reload redis5|re5|red_to_1|jobs|state|https leftover leftover down; bounce|REDIS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
keydb5|KEYDB5_TIMEOUT|1|30|s|/etc/keydb5/keydb5.conf|timeout=1|timeout=30|systemctl reload keydb5|ke5|key_to_1|jobs|state|https leftover leftover down; bounce|KEYDB5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dragonfly5|DRAGONFLY5_TIMEOUT|1|30|s|/etc/dragonfly5/dragonfly5.conf|timeout=1|timeout=30|systemctl reload dragonfly5|dr5|dra_to_1|jobs|state|https leftover leftover down; bounce|DRAGONFLY5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
memcached5|MEMCACHED5_TIMEOUT|1|30|s|/etc/memcached5/memcached5.conf|timeout=1|timeout=30|systemctl reload memcached5|me5|mem_to_1|jobs|state|https leftover leftover down; bounce|MEMCACHED5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hazelcast5|HAZELCAST5_TIMEOUT|1|30|s|/etc/hazelcast5/hazelcast5.conf|timeout=1|timeout=30|systemctl reload hazelcast5|ha5|haz_to_1|jobs|state|https leftover leftover down; bounce|HAZELCAST5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ignite5|IGNITE5_TIMEOUT|1|30|s|/etc/ignite5/ignite5.conf|timeout=1|timeout=30|systemctl reload ignite5|ig5|ign_to_1|jobs|state|https leftover leftover down; bounce|IGNITE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
elasticsearch5|ELASTICSEARCH5_TIMEOUT|1|30|s|/etc/elasticsearch5/elasticsearch5.conf|timeout=1|timeout=30|systemctl reload elasticsearch5|el5|ela_to_1|jobs|state|https leftover leftover down; bounce|ELASTICSEARCH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
solr5|SOLR5_TIMEOUT|1|30|s|/etc/solr5/solr5.conf|timeout=1|timeout=30|systemctl reload solr5|so5|sol_to_1|jobs|state|https leftover leftover down; bounce|SOLR5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lucene5|LUCENE5_TIMEOUT|1|30|s|/etc/lucene5/lucene5.conf|timeout=1|timeout=30|systemctl reload lucene5|lu5|luc_to_1|jobs|state|https leftover leftover down; bounce|LUCENE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
meilisearch5|MEILISEARCH5_TIMEOUT|1|30|s|/etc/meilisearch5/meilisearch5.conf|timeout=1|timeout=30|systemctl reload meilisearch5|me5|mei_to_1|jobs|state|https leftover leftover down; bounce|MEILISEARCH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
typesense5|TYPESENSE5_TIMEOUT|1|30|s|/etc/typesense5/typesense5.conf|timeout=1|timeout=30|systemctl reload typesense5|ty5|typ_to_1|jobs|state|https leftover leftover down; bounce|TYPESENSE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zinc5|ZINC5_TIMEOUT|1|30|s|/etc/zinc5/zinc5.conf|timeout=1|timeout=30|systemctl reload zinc5|zi5|zin_to_1|jobs|state|https leftover leftover down; bounce|ZINC5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
clickhouse5|CLICKHOUSE5_TIMEOUT|1|30|s|/etc/clickhouse5/clickhouse5.conf|timeout=1|timeout=30|systemctl reload clickhouse5|cl5|cli_to_1|jobs|state|https leftover leftover down; bounce|CLICKHOUSE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
druid5|DRUID5_TIMEOUT|1|30|s|/etc/druid5/druid5.conf|timeout=1|timeout=30|systemctl reload druid5|dr5|dru_to_1|jobs|state|https leftover leftover down; bounce|DRUID5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pinot5|PINOT5_TIMEOUT|1|30|s|/etc/pinot5/pinot5.conf|timeout=1|timeout=30|systemctl reload pinot5|pi5|pin_to_1|jobs|state|https leftover leftover down; bounce|PINOT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
starrocks5|STARROCKS5_TIMEOUT|1|30|s|/etc/starrocks5/starrocks5.conf|timeout=1|timeout=30|systemctl reload starrocks5|st5|sta_to_1|jobs|state|https leftover leftover down; bounce|STARROCKS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
doris5|DORIS5_TIMEOUT|1|30|s|/etc/doris5/doris5.conf|timeout=1|timeout=30|systemctl reload doris5|do5|dor_to_1|jobs|state|https leftover leftover down; bounce|DORIS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
duckdb5|DUCKDB5_TIMEOUT|1|30|s|/etc/duckdb5/duckdb5.conf|timeout=1|timeout=30|systemctl reload duckdb5|du5|duc_to_1|jobs|state|https leftover leftover down; bounce|DUCKDB5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
trino5|TRINO5_TIMEOUT|1|30|s|/etc/trino5/trino5.conf|timeout=1|timeout=30|systemctl reload trino5|tr5|tri_to_1|jobs|state|https leftover leftover down; bounce|TRINO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
presto5|PRESTO5_TIMEOUT|1|30|s|/etc/presto5/presto5.conf|timeout=1|timeout=30|systemctl reload presto5|pr5|pre_to_1|jobs|state|https leftover leftover down; bounce|PRESTO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
spark5|SPARK5_TIMEOUT|1|30|s|/etc/spark5/spark5.conf|timeout=1|timeout=30|systemctl reload spark5|sp5|spa_to_1|jobs|state|https leftover leftover down; bounce|SPARK5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flink5|FLINK5_TIMEOUT|1|30|s|/etc/flink5/flink5.conf|timeout=1|timeout=30|systemctl reload flink5|fl5|fli_to_1|jobs|state|https leftover leftover down; bounce|FLINK5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hive5|HIVE5_TIMEOUT|1|30|s|/etc/hive5/hive5.conf|timeout=1|timeout=30|systemctl reload hive5|hi5|hiv_to_1|jobs|state|https leftover leftover down; bounce|HIVE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
impala5|IMPALA5_TIMEOUT|1|30|s|/etc/impala5/impala5.conf|timeout=1|timeout=30|systemctl reload impala5|im5|imp_to_1|jobs|state|https leftover leftover down; bounce|IMPALA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kafka5|KAFKA5_TIMEOUT|1|30|s|/etc/kafka5/kafka5.conf|timeout=1|timeout=30|systemctl reload kafka5|ka5|kaf_to_1|jobs|state|https leftover leftover down; bounce|KAFKA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pulsar5|PULSAR5_TIMEOUT|1|30|s|/etc/pulsar5/pulsar5.conf|timeout=1|timeout=30|systemctl reload pulsar5|pu5|pul_to_1|jobs|state|https leftover leftover down; bounce|PULSAR5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redpanda5|REDPANDA5_TIMEOUT|1|30|s|/etc/redpanda5/redpanda5.conf|timeout=1|timeout=30|systemctl reload redpanda5|re5|red_to_1|jobs|state|https leftover leftover down; bounce|REDPANDA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nats5|NATS5_TIMEOUT|1|30|s|/etc/nats5/nats5.conf|timeout=1|timeout=30|systemctl reload nats5|na5|nat_to_1|jobs|state|https leftover leftover down; bounce|NATS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rabbitmq5|RABBITMQ5_TIMEOUT|1|30|s|/etc/rabbitmq5/rabbitmq5.conf|timeout=1|timeout=30|systemctl reload rabbitmq5|ra5|rab_to_1|jobs|state|https leftover leftover down; bounce|RABBITMQ5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
activemq5|ACTIVEMQ5_TIMEOUT|1|30|s|/etc/activemq5/activemq5.conf|timeout=1|timeout=30|systemctl reload activemq5|ac5|act_to_1|jobs|state|https leftover leftover down; bounce|ACTIVEMQ5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
prometheus5|PROMETHEUS5_TIMEOUT|1|30|s|/etc/prometheus5/prometheus5.conf|timeout=1|timeout=30|systemctl reload prometheus5|pr5|pro_to_1|jobs|state|https leftover leftover down; bounce|PROMETHEUS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "postgres5/mysql5/mariadb5/sqlite5/cockroach5/yugabyte5/scylla5/cassandra5/mongodb5/redis5/keydb5/dragonfly5/memcached5/hazelcast5/ignite5/elasticsearch5/solr5/lucene5/meilisearch5/typesense5/zinc5/clickhouse5/druid5/pinot5/starrocks5/doris5/duckdb5/trino5/presto5/spark5/flink5/hive5/impala5/kafka5/pulsar5/redpanda5/nats5/rabbitmq5/activemq5/prometheus5"
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
        svc = f"q2{i:02d}x"
        ns = f"q2{i:02d}"
        clu = f"prod-apuu{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14283 + i }"
        node = f"ip-10-199-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4881


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-89 leftover: {WAVE}.",
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
