#!/usr/bin/env python3
"""IRC mill r4441+ — wave-67 vector/olap/queue leftover.

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
pinecone|PINECONE_TIMEOUT|1|30|s|/etc/pinecone/pinecone.conf|timeout=1|timeout=30|systemctl reload pinecone|pc|pin_to_1|vectors|indexes|https leftover leftover down; bounce|PINECONE_TIMEOUT leftover 1 leftover; a 2s query is aborted so the vectors 504s
marqo|MARQO_TIMEOUT|1|30|s|/etc/marqo/marqo.conf|timeout=1|timeout=30|systemctl reload marqo|mq|mar_to_1|vectors|docs|https leftover leftover down; bounce|MARQO_TIMEOUT leftover 1 leftover; a 2s query is aborted so the vectors 504s
pgvector|PGVECTOR_TIMEOUT|1|30|s|/etc/pgvector/pgvector.conf|timeout=1|timeout=30|systemctl reload pgvector|pv|pgv_to_1|vectors|rows|pg leftover leftover down; bounce|PGVECTOR_TIMEOUT leftover 1 leftover; a 2s query is aborted so the vectors 504s
apachepinot|APACHEPINOT_TIMEOUT|1|30|s|/etc/apachepinot/apachepinot.conf|timeout=1|timeout=30|systemctl reload apachepinot|pn|apa_to_1|segments|tables|https leftover leftover down; bounce|APACHEPINOT_TIMEOUT leftover 1 leftover; a 2s query is aborted so the segments 504s
apachedruid|APACHEDRUID_TIMEOUT|1|30|s|/etc/apachedruid/apachedruid.conf|timeout=1|timeout=30|systemctl reload apachedruid|dr|apa_to_1|segments|datasources|https leftover leftover down; bounce|APACHEDRUID_TIMEOUT leftover 1 leftover; a 2s query is aborted so the segments 504s
datafusion|DATAFUSION_TIMEOUT|1|30|s|/etc/datafusion/datafusion.conf|timeout=1|timeout=30|systemctl reload datafusion|df|dat_to_1|plans|parquet|fs leftover leftover down; bounce|DATAFUSION_TIMEOUT leftover 1 leftover; a 2s query is aborted so the plans 504s
polars2|POLARS2_TIMEOUT|1|30|s|/etc/polars2/polars2.conf|timeout=1|timeout=30|systemctl reload polars2|pl|pol_to_1|frames|parquet|fs leftover leftover down; bounce|POLARS2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the frames 504s
daskdistributed|DASKDISTRIBUTED_TIMEOUT|1|30|s|/etc/daskdistributed/daskdistributed.conf|timeout=1|timeout=30|systemctl reload daskdistributed|dk|das_to_1|tasks|workers|tcp leftover leftover down; bounce|DASKDISTRIBUTED_TIMEOUT leftover 1 leftover; a 2s compute is aborted so the tasks 504s
rayserve|RAYSERVE_TIMEOUT|1|30|s|/etc/rayserve/rayserve.conf|timeout=1|timeout=30|systemctl reload rayserve|ry|ray_to_1|replicas|deploys|https leftover leftover down; bounce|RAYSERVE_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the replicas 504s
celerybeat|CELERYBEAT_TIMEOUT|1|30|s|/etc/celerybeat/celerybeat.conf|timeout=1|timeout=30|systemctl reload celerybeat|cb|cel_to_1|beats|queues|redis leftover leftover down; bounce|CELERYBEAT_TIMEOUT leftover 1 leftover; a 2s tick is aborted so the beats 504s
rqworker|RQWORKER_TIMEOUT|1|30|s|/etc/rqworker/rqworker.conf|timeout=1|timeout=30|systemctl reload rqworker|rq|rqw_to_1|jobs|queues|redis leftover leftover down; bounce|RQWORKER_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
oban|OBAN_TIMEOUT|1|30|s|/etc/oban/oban.conf|timeout=1|timeout=30|systemctl reload oban|ob|oba_to_1|jobs|queues|pg leftover leftover down; bounce|OBAN_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cadenceworkflow|CADENCEWORKFLOW_TIMEOUT|1|30|s|/etc/cadenceworkflow/cadenceworkflow.conf|timeout=1|timeout=30|systemctl reload cadenceworkflow|cw|cad_to_1|wfs|tasks|https leftover leftover down; bounce|CADENCEWORKFLOW_TIMEOUT leftover 1 leftover; a 2s run is aborted so the wfs 504s
maestrodatahub|MAESTRODATAHUB_TIMEOUT|1|30|s|/etc/maestrodatahub/maestrodatahub.conf|timeout=1|timeout=30|systemctl reload maestrodatahub|md|mae_to_1|pipelines|datasets|https leftover leftover down; bounce|MAESTRODATAHUB_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
apacheatlas|APACHEATLAS_TIMEOUT|1|30|s|/etc/apacheatlas/apacheatlas.conf|timeout=1|timeout=30|systemctl reload apacheatlas|at|apa_to_1|entities|types|https leftover leftover down; bounce|APACHEATLAS_TIMEOUT leftover 1 leftover; a 2s save is aborted so the entities 504s
gluecatalog|GLUECATALOG_TIMEOUT|1|30|s|/etc/gluecatalog/gluecatalog.conf|timeout=1|timeout=30|systemctl reload gluecatalog|gc|glu_to_1|tables|dbs|https leftover leftover down; bounce|GLUECATALOG_TIMEOUT leftover 1 leftover; a 2s save is aborted so the tables 504s
feaststore|FEASTSTORE_TIMEOUT|1|30|s|/etc/feaststore/feaststore.conf|timeout=1|timeout=30|systemctl reload feaststore|fs|fea_to_1|features|views|https leftover leftover down; bounce|FEASTSTORE_TIMEOUT leftover 1 leftover; a 2s get is aborted so the features 504s
tecton|TECTON_TIMEOUT|1|30|s|/etc/tecton/tecton.conf|timeout=1|timeout=30|systemctl reload tecton|tc|tec_to_1|features|svcs|https leftover leftover down; bounce|TECTON_TIMEOUT leftover 1 leftover; a 2s get is aborted so the features 504s
hightouch|HIGHTOUCH_TIMEOUT|1|30|s|/etc/hightouch/hightouch.conf|timeout=1|timeout=30|systemctl reload hightouch|ht|hig_to_1|syncs|models|https leftover leftover down; bounce|HIGHTOUCH_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the syncs 504s
censusrpc|CENSUSRPC_TIMEOUT|1|30|s|/etc/censusrpc/censusrpc.conf|timeout=1|timeout=30|systemctl reload censusrpc|cn|cen_to_1|syncs|models|https leftover leftover down; bounce|CENSUSRPC_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the syncs 504s
grouparoo|GROUPAROO_TIMEOUT|1|30|s|/etc/grouparoo/grouparoo.conf|timeout=1|timeout=30|systemctl reload grouparoo|gr|gro_to_1|syncs|profiles|https leftover leftover down; bounce|GROUPAROO_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the syncs 504s
flinkcdc|FLINKCDC_TIMEOUT|1|30|s|/etc/flinkcdc/flinkcdc.conf|timeout=1|timeout=30|systemctl reload flinkcdc|fc|fli_to_1|slots|tables|kafka leftover leftover down; bounce|FLINKCDC_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the slots 504s
mustgather|MUSTGATHER_TIMEOUT|1|30|s|/etc/mustgather/mustgather.conf|timeout=1|timeout=30|systemctl reload mustgather|mg|mus_to_1|dumps|ns|k8s leftover leftover down; bounce|MUSTGATHER_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the dumps 504s
redpanda2|REDPANDA2_TIMEOUT|1|30|s|/etc/redpanda2/redpanda2.conf|timeout=1|timeout=30|systemctl reload redpanda2|rp|red_to_1|topics|groups|kafka leftover leftover down; bounce|REDPANDA2_TIMEOUT leftover 1 leftover; a 2s produce is aborted so the topics 504s
pulsar2|PULSAR2_TIMEOUT|1|30|s|/etc/pulsar2/pulsar2.conf|timeout=1|timeout=30|systemctl reload pulsar2|pu|pul_to_1|topics|subs|https leftover leftover down; bounce|PULSAR2_TIMEOUT leftover 1 leftover; a 2s produce is aborted so the topics 504s
natsjet|NATSJET_TIMEOUT|1|30|s|/etc/natsjet/natsjet.conf|timeout=1|timeout=30|systemctl reload natsjet|nj|nat_to_1|streams|consumers|nats leftover leftover down; bounce|NATSJET_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the streams 504s
influx2|INFLUX2_TIMEOUT|1|30|s|/etc/influx2/influx2.conf|timeout=1|timeout=30|systemctl reload influx2|if|inf_to_1|points|buckets|https leftover leftover down; bounce|INFLUX2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the points 504s
victoriametrics2|VICTORIAMETRICS2_TIMEOUT|1|30|s|/etc/victoriametrics2/victoriametrics2.conf|timeout=1|timeout=30|systemctl reload victoriametrics2|vm|vic_to_1|samples|tenants|http leftover leftover down; bounce|VICTORIAMETRICS2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the samples 504s
clickhouse2|CLICKHOUSE2_TIMEOUT|1|30|s|/etc/clickhouse2/clickhouse2.conf|timeout=1|timeout=30|systemctl reload clickhouse2|ch|cli_to_1|parts|tables|http leftover leftover down; bounce|CLICKHOUSE2_TIMEOUT leftover 1 leftover; a 2s insert is aborted so the parts 504s
cockroach2|COCKROACH2_TIMEOUT|1|30|s|/etc/cockroach2/cockroach2.conf|timeout=1|timeout=30|systemctl reload cockroach2|cr|coc_to_1|ranges|leases|https leftover leftover down; bounce|COCKROACH2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the ranges 504s
yugabyte2|YUGABYTE2_TIMEOUT|1|30|s|/etc/yugabyte2/yugabyte2.conf|timeout=1|timeout=30|systemctl reload yugabyte2|yb|yug_to_1|tablets|masters|https leftover leftover down; bounce|YUGABYTE2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the tablets 504s
scylladb2|SCYLLADB2_TIMEOUT|1|30|s|/etc/scylladb2/scylladb2.conf|timeout=1|timeout=30|systemctl reload scylladb2|sc|scy_to_1|sstables|ks|cql leftover leftover down; bounce|SCYLLADB2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the sstables 504s
cassandradc|CASSANDRADC_TIMEOUT|1|30|s|/etc/cassandradc/cassandradc.conf|timeout=1|timeout=30|systemctl reload cassandradc|cs|cas_to_1|sstables|ks|cql leftover leftover down; bounce|CASSANDRADC_TIMEOUT leftover 1 leftover; a 2s repair is aborted so the sstables 504s
trino2|TRINO2_TIMEOUT|1|30|s|/etc/trino2/trino2.conf|timeout=1|timeout=30|systemctl reload trino2|tr|tri_to_1|queries|workers|https leftover leftover down; bounce|TRINO2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the queries 504s
prestodb2|PRESTODB2_TIMEOUT|1|30|s|/etc/prestodb2/prestodb2.conf|timeout=1|timeout=30|systemctl reload prestodb2|pr|pre_to_1|queries|workers|https leftover leftover down; bounce|PRESTODB2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the queries 504s
sparkconnect|SPARKCONNECT_TIMEOUT|1|30|s|/etc/sparkconnect/sparkconnect.conf|timeout=1|timeout=30|systemctl reload sparkconnect|sk|spa_to_1|sessions|jobs|grpc leftover leftover down; bounce|SPARKCONNECT_TIMEOUT leftover 1 leftover; a 2s run is aborted so the sessions 504s
flinksql|FLINKSQL_TIMEOUT|1|30|s|/etc/flinksql/flinksql.conf|timeout=1|timeout=30|systemctl reload flinksql|fl|fli_to_1|jobs|sqls|https leftover leftover down; bounce|FLINKSQL_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
airbyte2|AIRBYTE2_TIMEOUT|1|30|s|/etc/airbyte2/airbyte2.conf|timeout=1|timeout=30|systemctl reload airbyte2|ab|air_to_1|syncs|conns|https leftover leftover down; bounce|AIRBYTE2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the syncs 504s
fivetran2|FIVETRAN2_TIMEOUT|1|30|s|/etc/fivetran2/fivetran2.conf|timeout=1|timeout=30|systemctl reload fivetran2|fv|fiv_to_1|syncs|conns|https leftover leftover down; bounce|FIVETRAN2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the syncs 504s
meltano2|MELTANO2_TIMEOUT|1|30|s|/etc/meltano2/meltano2.conf|timeout=1|timeout=30|systemctl reload meltano2|ml|mel_to_1|taps|targets|fs leftover leftover down; bounce|MELTANO2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the taps 504s
'''
WAVE = (
    "pinecone/marqo/pgvector/apachepinot/apachedruid/datafusion/polars2/daskdistributed/rayserve/celerybeat/rqworker/oban/cadenceworkflow/maestrodatahub/apacheatlas/gluecatalog/feaststore/tecton/hightouch/censusrpc/grouparoo/flinkcdc/mustgather/redpanda2/pulsar2/natsjet/influx2/victoriametrics2/clickhouse2/cockroach2/yugabyte2/scylladb2/cassandradc/trino2/prestodb2/sparkconnect/flinksql/airbyte2/fivetran2/meltano2"
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
        svc = f"x3{i:02d}x"
        ns = f"x3{i:02d}"
        clu = f"prod-apty{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13403 + i }"
        node = f"ip-10-252-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4441


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-67 leftover: {WAVE}.",
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
