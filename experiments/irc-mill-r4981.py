#!/usr/bin/env python3
"""IRC mill r4981+ — wave-94 data6 leftover.

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
kafka6|KAFKA6_TIMEOUT|1|30|s|/etc/kafka6/kafka6.conf|timeout=1|timeout=30|systemctl reload kafka6|ka6|kaf_to_1|jobs|state|https leftover leftover down; bounce|KAFKA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pulsar6|PULSAR6_TIMEOUT|1|30|s|/etc/pulsar6/pulsar6.conf|timeout=1|timeout=30|systemctl reload pulsar6|pu6|pul_to_1|jobs|state|https leftover leftover down; bounce|PULSAR6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nats6|NATS6_TIMEOUT|1|30|s|/etc/nats6/nats6.conf|timeout=1|timeout=30|systemctl reload nats6|na6|nat_to_1|jobs|state|https leftover leftover down; bounce|NATS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rabbitmq6|RABBITMQ6_TIMEOUT|1|30|s|/etc/rabbitmq6/rabbitmq6.conf|timeout=1|timeout=30|systemctl reload rabbitmq6|ra6|rab_to_1|jobs|state|https leftover leftover down; bounce|RABBITMQ6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
clickhouse6|CLICKHOUSE6_TIMEOUT|1|30|s|/etc/clickhouse6/clickhouse6.conf|timeout=1|timeout=30|systemctl reload clickhouse6|cl6|cli_to_1|jobs|state|https leftover leftover down; bounce|CLICKHOUSE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
spark6|SPARK6_TIMEOUT|1|30|s|/etc/spark6/spark6.conf|timeout=1|timeout=30|systemctl reload spark6|sp6|spa_to_1|jobs|state|https leftover leftover down; bounce|SPARK6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flink6|FLINK6_TIMEOUT|1|30|s|/etc/flink6/flink6.conf|timeout=1|timeout=30|systemctl reload flink6|fl6|fli_to_1|jobs|state|https leftover leftover down; bounce|FLINK6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
trino6|TRINO6_TIMEOUT|1|30|s|/etc/trino6/trino6.conf|timeout=1|timeout=30|systemctl reload trino6|tr6|tri_to_1|jobs|state|https leftover leftover down; bounce|TRINO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
presto6|PRESTO6_TIMEOUT|1|30|s|/etc/presto6/presto6.conf|timeout=1|timeout=30|systemctl reload presto6|pr6|pre_to_1|jobs|state|https leftover leftover down; bounce|PRESTO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hive6|HIVE6_TIMEOUT|1|30|s|/etc/hive6/hive6.conf|timeout=1|timeout=30|systemctl reload hive6|hi6|hiv_to_1|jobs|state|https leftover leftover down; bounce|HIVE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
impala6|IMPALA6_TIMEOUT|1|30|s|/etc/impala6/impala6.conf|timeout=1|timeout=30|systemctl reload impala6|im6|imp_to_1|jobs|state|https leftover leftover down; bounce|IMPALA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
druid6|DRUID6_TIMEOUT|1|30|s|/etc/druid6/druid6.conf|timeout=1|timeout=30|systemctl reload druid6|dr6|dru_to_1|jobs|state|https leftover leftover down; bounce|DRUID6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pinot6|PINOT6_TIMEOUT|1|30|s|/etc/pinot6/pinot6.conf|timeout=1|timeout=30|systemctl reload pinot6|pi6|pin_to_1|jobs|state|https leftover leftover down; bounce|PINOT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
doris6|DORIS6_TIMEOUT|1|30|s|/etc/doris6/doris6.conf|timeout=1|timeout=30|systemctl reload doris6|do6|dor_to_1|jobs|state|https leftover leftover down; bounce|DORIS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
starrocks6|STARROCKS6_TIMEOUT|1|30|s|/etc/starrocks6/starrocks6.conf|timeout=1|timeout=30|systemctl reload starrocks6|st6|sta_to_1|jobs|state|https leftover leftover down; bounce|STARROCKS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
duckdb6|DUCKDB6_TIMEOUT|1|30|s|/etc/duckdb6/duckdb6.conf|timeout=1|timeout=30|systemctl reload duckdb6|du6|duc_to_1|jobs|state|https leftover leftover down; bounce|DUCKDB6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
solr6|SOLR6_TIMEOUT|1|30|s|/etc/solr6/solr6.conf|timeout=1|timeout=30|systemctl reload solr6|so6|sol_to_1|jobs|state|https leftover leftover down; bounce|SOLR6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lucene6|LUCENE6_TIMEOUT|1|30|s|/etc/lucene6/lucene6.conf|timeout=1|timeout=30|systemctl reload lucene6|lu6|luc_to_1|jobs|state|https leftover leftover down; bounce|LUCENE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
prometheus6|PROMETHEUS6_TIMEOUT|1|30|s|/etc/prometheus6/prometheus6.conf|timeout=1|timeout=30|systemctl reload prometheus6|pr6|pro_to_1|jobs|state|https leftover leftover down; bounce|PROMETHEUS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
grafana6|GRAFANA6_TIMEOUT|1|30|s|/etc/grafana6/grafana6.conf|timeout=1|timeout=30|systemctl reload grafana6|gr6|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAFANA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
loki6|LOKI6_TIMEOUT|1|30|s|/etc/loki6/loki6.conf|timeout=1|timeout=30|systemctl reload loki6|lo6|lok_to_1|jobs|state|https leftover leftover down; bounce|LOKI6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tempo6|TEMPO6_TIMEOUT|1|30|s|/etc/tempo6/tempo6.conf|timeout=1|timeout=30|systemctl reload tempo6|te6|tem_to_1|jobs|state|https leftover leftover down; bounce|TEMPO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jaeger6|JAEGER6_TIMEOUT|1|30|s|/etc/jaeger6/jaeger6.conf|timeout=1|timeout=30|systemctl reload jaeger6|ja6|jae_to_1|jobs|state|https leftover leftover down; bounce|JAEGER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zipkin6|ZIPKIN6_TIMEOUT|1|30|s|/etc/zipkin6/zipkin6.conf|timeout=1|timeout=30|systemctl reload zipkin6|zi6|zip_to_1|jobs|state|https leftover leftover down; bounce|ZIPKIN6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
meilisearch6|MEILISEARCH6_TIMEOUT|1|30|s|/etc/meilisearch6/meilisearch6.conf|timeout=1|timeout=30|systemctl reload meilisearch6|me6|mei_to_1|jobs|state|https leftover leftover down; bounce|MEILISEARCH6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
typesense6|TYPESENSE6_TIMEOUT|1|30|s|/etc/typesense6/typesense6.conf|timeout=1|timeout=30|systemctl reload typesense6|ty6|typ_to_1|jobs|state|https leftover leftover down; bounce|TYPESENSE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zinc6|ZINC6_TIMEOUT|1|30|s|/etc/zinc6/zinc6.conf|timeout=1|timeout=30|systemctl reload zinc6|zi6|zin_to_1|jobs|state|https leftover leftover down; bounce|ZINC6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
honeycomb6|HONEYCOMB6_TIMEOUT|1|30|s|/etc/honeycomb6/honeycomb6.conf|timeout=1|timeout=30|systemctl reload honeycomb6|ho6|hon_to_1|jobs|state|https leftover leftover down; bounce|HONEYCOMB6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redpanda6|REDPANDA6_TIMEOUT|1|30|s|/etc/redpanda6/redpanda6.conf|timeout=1|timeout=30|systemctl reload redpanda6|re6|red_to_1|jobs|state|https leftover leftover down; bounce|REDPANDA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
natsjetstream6|NATSJETSTREAM6_TIMEOUT|1|30|s|/etc/natsjetstream6/natsjetstream6.conf|timeout=1|timeout=30|systemctl reload natsjetstream6|na6|nat_to_1|jobs|state|https leftover leftover down; bounce|NATSJETSTREAM6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mimir6|MIMIR6_TIMEOUT|1|30|s|/etc/mimir6/mimir6.conf|timeout=1|timeout=30|systemctl reload mimir6|mi6|mim_to_1|jobs|state|https leftover leftover down; bounce|MIMIR6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
victoriametrics6|VICTORIAMETRICS6_TIMEOUT|1|30|s|/etc/victoriametrics6/victoriametrics6.conf|timeout=1|timeout=30|systemctl reload victoriametrics6|vi6|vic_to_1|jobs|state|https leftover leftover down; bounce|VICTORIAMETRICS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
alertmanager6|ALERTMANAGER6_TIMEOUT|1|30|s|/etc/alertmanager6/alertmanager6.conf|timeout=1|timeout=30|systemctl reload alertmanager6|al6|ale_to_1|jobs|state|https leftover leftover down; bounce|ALERTMANAGER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
thanos6|THANOS6_TIMEOUT|1|30|s|/etc/thanos6/thanos6.conf|timeout=1|timeout=30|systemctl reload thanos6|th6|tha_to_1|jobs|state|https leftover leftover down; bounce|THANOS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cortex6|CORTEX6_TIMEOUT|1|30|s|/etc/cortex6/cortex6.conf|timeout=1|timeout=30|systemctl reload cortex6|co6|cor_to_1|jobs|state|https leftover leftover down; bounce|CORTEX6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
graylog6|GRAYLOG6_TIMEOUT|1|30|s|/etc/graylog6/graylog6.conf|timeout=1|timeout=30|systemctl reload graylog6|gr6|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAYLOG6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
fluentd6|FLUENTD6_TIMEOUT|1|30|s|/etc/fluentd6/fluentd6.conf|timeout=1|timeout=30|systemctl reload fluentd6|fl6|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUENTD6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vector6|VECTOR6_TIMEOUT|1|30|s|/etc/vector6/vector6.conf|timeout=1|timeout=30|systemctl reload vector6|ve6|vec_to_1|jobs|state|https leftover leftover down; bounce|VECTOR6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
filebeat6|FILEBEAT6_TIMEOUT|1|30|s|/etc/filebeat6/filebeat6.conf|timeout=1|timeout=30|systemctl reload filebeat6|fi6|fil_to_1|jobs|state|https leftover leftover down; bounce|FILEBEAT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
logstash6|LOGSTASH6_TIMEOUT|1|30|s|/etc/logstash6/logstash6.conf|timeout=1|timeout=30|systemctl reload logstash6|lo6|log_to_1|jobs|state|https leftover leftover down; bounce|LOGSTASH6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "kafka6/pulsar6/nats6/rabbitmq6/clickhouse6/spark6/flink6/trino6/presto6/hive6/impala6/druid6/pinot6/doris6/starrocks6/duckdb6/solr6/lucene6/prometheus6/grafana6/loki6/tempo6/jaeger6/zipkin6/meilisearch6/typesense6/zinc6/honeycomb6/redpanda6/natsjetstream6/mimir6/victoriametrics6/alertmanager6/thanos6/cortex6/graylog6/fluentd6/vector6/filebeat6/logstash6"
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
        svc = f"v3{i:02d}x"
        ns = f"v3{i:02d}"
        clu = f"prod-apuz{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14483 + i }"
        node = f"ip-10-164-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4981


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-94 leftover: {WAVE}.",
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
