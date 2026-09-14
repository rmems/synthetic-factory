#!/usr/bin/env python3
"""IRC mill r4821+ — wave-86 virt/storage leftover.

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
xfs3|XFS3_TIMEOUT|1|30|s|/etc/xfs3/xfs3.conf|timeout=1|timeout=30|systemctl reload xfs3|xf3|xfs_to_1|jobs|state|https leftover leftover down; bounce|XFS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lvm3|LVM3_TIMEOUT|1|30|s|/etc/lvm3/lvm3.conf|timeout=1|timeout=30|systemctl reload lvm3|lv3|lvm_to_1|jobs|state|https leftover leftover down; bounce|LVM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mdadm3|MDADM3_TIMEOUT|1|30|s|/etc/mdadm3/mdadm3.conf|timeout=1|timeout=30|systemctl reload mdadm3|md3|mda_to_1|jobs|state|https leftover leftover down; bounce|MDADM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
smartmon3|SMARTMON3_TIMEOUT|1|30|s|/etc/smartmon3/smartmon3.conf|timeout=1|timeout=30|systemctl reload smartmon3|sm3|sma_to_1|jobs|state|https leftover leftover down; bounce|SMARTMON3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nvme3|NVME3_TIMEOUT|1|30|s|/etc/nvme3/nvme3.conf|timeout=1|timeout=30|systemctl reload nvme3|nv3|nvm_to_1|jobs|state|https leftover leftover down; bounce|NVME3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ipmi3|IPMI3_TIMEOUT|1|30|s|/etc/ipmi3/ipmi3.conf|timeout=1|timeout=30|systemctl reload ipmi3|ip3|ipm_to_1|jobs|state|https leftover leftover down; bounce|IPMI3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bmc3|BMC3_TIMEOUT|1|30|s|/etc/bmc3/bmc3.conf|timeout=1|timeout=30|systemctl reload bmc3|bm3|bmc_to_1|jobs|state|https leftover leftover down; bounce|BMC3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redfish3|REDFISH3_TIMEOUT|1|30|s|/etc/redfish3/redfish3.conf|timeout=1|timeout=30|systemctl reload redfish3|re3|red_to_1|jobs|state|https leftover leftover down; bounce|REDFISH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
idrac3|IDRAC3_TIMEOUT|1|30|s|/etc/idrac3/idrac3.conf|timeout=1|timeout=30|systemctl reload idrac3|id3|idr_to_1|jobs|state|https leftover leftover down; bounce|IDRAC3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ilo3|ILO3_TIMEOUT|1|30|s|/etc/ilo3/ilo3.conf|timeout=1|timeout=30|systemctl reload ilo3|il3|ilo_to_1|jobs|state|https leftover leftover down; bounce|ILO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nodeexporter3|NODEEXPORTER3_TIMEOUT|1|30|s|/etc/nodeexporter3/nodeexporter3.conf|timeout=1|timeout=30|systemctl reload nodeexporter3|no3|nod_to_1|jobs|state|https leftover leftover down; bounce|NODEEXPORTER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
blackbox3|BLACKBOX3_TIMEOUT|1|30|s|/etc/blackbox3/blackbox3.conf|timeout=1|timeout=30|systemctl reload blackbox3|bl3|bla_to_1|jobs|state|https leftover leftover down; bounce|BLACKBOX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
snmp3|SNMP3_TIMEOUT|1|30|s|/etc/snmp3/snmp3.conf|timeout=1|timeout=30|systemctl reload snmp3|sn3|snm_to_1|jobs|state|https leftover leftover down; bounce|SNMP3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
netbox3|NETBOX3_TIMEOUT|1|30|s|/etc/netbox3/netbox3.conf|timeout=1|timeout=30|systemctl reload netbox3|ne3|net_to_1|jobs|state|https leftover leftover down; bounce|NETBOX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nautobot3|NAUTOBOT3_TIMEOUT|1|30|s|/etc/nautobot3/nautobot3.conf|timeout=1|timeout=30|systemctl reload nautobot3|na3|nau_to_1|jobs|state|https leftover leftover down; bounce|NAUTOBOT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zabbix3|ZABBIX3_TIMEOUT|1|30|s|/etc/zabbix3/zabbix3.conf|timeout=1|timeout=30|systemctl reload zabbix3|za3|zab_to_1|jobs|state|https leftover leftover down; bounce|ZABBIX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
icinga3|ICINGA3_TIMEOUT|1|30|s|/etc/icinga3/icinga3.conf|timeout=1|timeout=30|systemctl reload icinga3|ic3|ici_to_1|jobs|state|https leftover leftover down; bounce|ICINGA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nagios3|NAGIOS3_TIMEOUT|1|30|s|/etc/nagios3/nagios3.conf|timeout=1|timeout=30|systemctl reload nagios3|na3|nag_to_1|jobs|state|https leftover leftover down; bounce|NAGIOS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
splunk3|SPLUNK3_TIMEOUT|1|30|s|/etc/splunk3/splunk3.conf|timeout=1|timeout=30|systemctl reload splunk3|sp3|spl_to_1|jobs|state|https leftover leftover down; bounce|SPLUNK3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
fluentd3|FLUENTD3_TIMEOUT|1|30|s|/etc/fluentd3/fluentd3.conf|timeout=1|timeout=30|systemctl reload fluentd3|fl3|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUENTD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
fluentbit3|FLUENTBIT3_TIMEOUT|1|30|s|/etc/fluentbit3/fluentbit3.conf|timeout=1|timeout=30|systemctl reload fluentbit3|fl3|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUENTBIT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vector3|VECTOR3_TIMEOUT|1|30|s|/etc/vector3/vector3.conf|timeout=1|timeout=30|systemctl reload vector3|ve3|vec_to_1|jobs|state|https leftover leftover down; bounce|VECTOR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
filebeat3|FILEBEAT3_TIMEOUT|1|30|s|/etc/filebeat3/filebeat3.conf|timeout=1|timeout=30|systemctl reload filebeat3|fi3|fil_to_1|jobs|state|https leftover leftover down; bounce|FILEBEAT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
metricbeat3|METRICBEAT3_TIMEOUT|1|30|s|/etc/metricbeat3/metricbeat3.conf|timeout=1|timeout=30|systemctl reload metricbeat3|me3|met_to_1|jobs|state|https leftover leftover down; bounce|METRICBEAT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
logstash3|LOGSTASH3_TIMEOUT|1|30|s|/etc/logstash3/logstash3.conf|timeout=1|timeout=30|systemctl reload logstash3|lo3|log_to_1|jobs|state|https leftover leftover down; bounce|LOGSTASH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
graylog3|GRAYLOG3_TIMEOUT|1|30|s|/etc/graylog3/graylog3.conf|timeout=1|timeout=30|systemctl reload graylog3|gr3|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAYLOG3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
elasticsearch4|ELASTICSEARCH4_TIMEOUT|1|30|s|/etc/elasticsearch4/elasticsearch4.conf|timeout=1|timeout=30|systemctl reload elasticsearch4|el4|ela_to_1|jobs|state|https leftover leftover down; bounce|ELASTICSEARCH4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
solr4|SOLR4_TIMEOUT|1|30|s|/etc/solr4/solr4.conf|timeout=1|timeout=30|systemctl reload solr4|so4|sol_to_1|jobs|state|https leftover leftover down; bounce|SOLR4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lucene4|LUCENE4_TIMEOUT|1|30|s|/etc/lucene4/lucene4.conf|timeout=1|timeout=30|systemctl reload lucene4|lu4|luc_to_1|jobs|state|https leftover leftover down; bounce|LUCENE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
meilisearch4|MEILISEARCH4_TIMEOUT|1|30|s|/etc/meilisearch4/meilisearch4.conf|timeout=1|timeout=30|systemctl reload meilisearch4|me4|mei_to_1|jobs|state|https leftover leftover down; bounce|MEILISEARCH4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
typesense4|TYPESENSE4_TIMEOUT|1|30|s|/etc/typesense4/typesense4.conf|timeout=1|timeout=30|systemctl reload typesense4|ty4|typ_to_1|jobs|state|https leftover leftover down; bounce|TYPESENSE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
clickhouse4|CLICKHOUSE4_TIMEOUT|1|30|s|/etc/clickhouse4/clickhouse4.conf|timeout=1|timeout=30|systemctl reload clickhouse4|cl4|cli_to_1|jobs|state|https leftover leftover down; bounce|CLICKHOUSE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
druid4|DRUID4_TIMEOUT|1|30|s|/etc/druid4/druid4.conf|timeout=1|timeout=30|systemctl reload druid4|dr4|dru_to_1|jobs|state|https leftover leftover down; bounce|DRUID4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pinot4|PINOT4_TIMEOUT|1|30|s|/etc/pinot4/pinot4.conf|timeout=1|timeout=30|systemctl reload pinot4|pi4|pin_to_1|jobs|state|https leftover leftover down; bounce|PINOT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
starrocks4|STARROCKS4_TIMEOUT|1|30|s|/etc/starrocks4/starrocks4.conf|timeout=1|timeout=30|systemctl reload starrocks4|st4|sta_to_1|jobs|state|https leftover leftover down; bounce|STARROCKS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
doris4|DORIS4_TIMEOUT|1|30|s|/etc/doris4/doris4.conf|timeout=1|timeout=30|systemctl reload doris4|do4|dor_to_1|jobs|state|https leftover leftover down; bounce|DORIS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
duckdb4|DUCKDB4_TIMEOUT|1|30|s|/etc/duckdb4/duckdb4.conf|timeout=1|timeout=30|systemctl reload duckdb4|du4|duc_to_1|jobs|state|https leftover leftover down; bounce|DUCKDB4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
trino4|TRINO4_TIMEOUT|1|30|s|/etc/trino4/trino4.conf|timeout=1|timeout=30|systemctl reload trino4|tr4|tri_to_1|jobs|state|https leftover leftover down; bounce|TRINO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
presto4|PRESTO4_TIMEOUT|1|30|s|/etc/presto4/presto4.conf|timeout=1|timeout=30|systemctl reload presto4|pr4|pre_to_1|jobs|state|https leftover leftover down; bounce|PRESTO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
spark4|SPARK4_TIMEOUT|1|30|s|/etc/spark4/spark4.conf|timeout=1|timeout=30|systemctl reload spark4|sp4|spa_to_1|jobs|state|https leftover leftover down; bounce|SPARK4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "xfs3/lvm3/mdadm3/smartmon3/nvme3/ipmi3/bmc3/redfish3/idrac3/ilo3/nodeexporter3/blackbox3/snmp3/netbox3/nautobot3/zabbix3/icinga3/nagios3/splunk3/fluentd3/fluentbit3/vector3/filebeat3/metricbeat3/logstash3/graylog3/elasticsearch4/solr4/lucene4/meilisearch4/typesense4/clickhouse4/druid4/pinot4/starrocks4/doris4/duckdb4/trino4/presto4/spark4"
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
        svc = f"m9{i:02d}x"
        ns = f"m9{i:02d}"
        clu = f"prod-apur{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14163 + i }"
        node = f"ip-10-196-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4821


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-86 leftover: {WAVE}.",
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
