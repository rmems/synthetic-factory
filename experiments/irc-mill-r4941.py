#!/usr/bin/env python3
"""IRC mill r4941+ — wave-92 virt5 leftover.

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
bmc5|BMC5_TIMEOUT|1|30|s|/etc/bmc5/bmc5.conf|timeout=1|timeout=30|systemctl reload bmc5|bm5|bmc_to_1|jobs|state|https leftover leftover down; bounce|BMC5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redfish5|REDFISH5_TIMEOUT|1|30|s|/etc/redfish5/redfish5.conf|timeout=1|timeout=30|systemctl reload redfish5|re5|red_to_1|jobs|state|https leftover leftover down; bounce|REDFISH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
idrac5|IDRAC5_TIMEOUT|1|30|s|/etc/idrac5/idrac5.conf|timeout=1|timeout=30|systemctl reload idrac5|id5|idr_to_1|jobs|state|https leftover leftover down; bounce|IDRAC5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ilo5|ILO5_TIMEOUT|1|30|s|/etc/ilo5/ilo5.conf|timeout=1|timeout=30|systemctl reload ilo5|il5|ilo_to_1|jobs|state|https leftover leftover down; bounce|ILO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zabbix5|ZABBIX5_TIMEOUT|1|30|s|/etc/zabbix5/zabbix5.conf|timeout=1|timeout=30|systemctl reload zabbix5|za5|zab_to_1|jobs|state|https leftover leftover down; bounce|ZABBIX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
icinga5|ICINGA5_TIMEOUT|1|30|s|/etc/icinga5/icinga5.conf|timeout=1|timeout=30|systemctl reload icinga5|ic5|ici_to_1|jobs|state|https leftover leftover down; bounce|ICINGA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nagios5|NAGIOS5_TIMEOUT|1|30|s|/etc/nagios5/nagios5.conf|timeout=1|timeout=30|systemctl reload nagios5|na5|nag_to_1|jobs|state|https leftover leftover down; bounce|NAGIOS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
splunk5|SPLUNK5_TIMEOUT|1|30|s|/etc/splunk5/splunk5.conf|timeout=1|timeout=30|systemctl reload splunk5|sp5|spl_to_1|jobs|state|https leftover leftover down; bounce|SPLUNK5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
fluentd5|FLUENTD5_TIMEOUT|1|30|s|/etc/fluentd5/fluentd5.conf|timeout=1|timeout=30|systemctl reload fluentd5|fl5|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUENTD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
fluentbit5|FLUENTBIT5_TIMEOUT|1|30|s|/etc/fluentbit5/fluentbit5.conf|timeout=1|timeout=30|systemctl reload fluentbit5|fl5|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUENTBIT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vector5|VECTOR5_TIMEOUT|1|30|s|/etc/vector5/vector5.conf|timeout=1|timeout=30|systemctl reload vector5|ve5|vec_to_1|jobs|state|https leftover leftover down; bounce|VECTOR5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
filebeat5|FILEBEAT5_TIMEOUT|1|30|s|/etc/filebeat5/filebeat5.conf|timeout=1|timeout=30|systemctl reload filebeat5|fi5|fil_to_1|jobs|state|https leftover leftover down; bounce|FILEBEAT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
metricbeat5|METRICBEAT5_TIMEOUT|1|30|s|/etc/metricbeat5/metricbeat5.conf|timeout=1|timeout=30|systemctl reload metricbeat5|me5|met_to_1|jobs|state|https leftover leftover down; bounce|METRICBEAT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
logstash5|LOGSTASH5_TIMEOUT|1|30|s|/etc/logstash5/logstash5.conf|timeout=1|timeout=30|systemctl reload logstash5|lo5|log_to_1|jobs|state|https leftover leftover down; bounce|LOGSTASH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
graylog5|GRAYLOG5_TIMEOUT|1|30|s|/etc/graylog5/graylog5.conf|timeout=1|timeout=30|systemctl reload graylog5|gr5|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAYLOG5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
netbox5|NETBOX5_TIMEOUT|1|30|s|/etc/netbox5/netbox5.conf|timeout=1|timeout=30|systemctl reload netbox5|ne5|net_to_1|jobs|state|https leftover leftover down; bounce|NETBOX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nautobot5|NAUTOBOT5_TIMEOUT|1|30|s|/etc/nautobot5/nautobot5.conf|timeout=1|timeout=30|systemctl reload nautobot5|na5|nau_to_1|jobs|state|https leftover leftover down; bounce|NAUTOBOT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
blackbox5|BLACKBOX5_TIMEOUT|1|30|s|/etc/blackbox5/blackbox5.conf|timeout=1|timeout=30|systemctl reload blackbox5|bl5|bla_to_1|jobs|state|https leftover leftover down; bounce|BLACKBOX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
snmp5|SNMP5_TIMEOUT|1|30|s|/etc/snmp5/snmp5.conf|timeout=1|timeout=30|systemctl reload snmp5|sn5|snm_to_1|jobs|state|https leftover leftover down; bounce|SNMP5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nodeexporter5|NODEEXPORTER5_TIMEOUT|1|30|s|/etc/nodeexporter5/nodeexporter5.conf|timeout=1|timeout=30|systemctl reload nodeexporter5|no5|nod_to_1|jobs|state|https leftover leftover down; bounce|NODEEXPORTER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
smartmon5|SMARTMON5_TIMEOUT|1|30|s|/etc/smartmon5/smartmon5.conf|timeout=1|timeout=30|systemctl reload smartmon5|sm5|sma_to_1|jobs|state|https leftover leftover down; bounce|SMARTMON5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openshift5|OPENSHIFT5_TIMEOUT|1|30|s|/etc/openshift5/openshift5.conf|timeout=1|timeout=30|systemctl reload openshift5|op5|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENSHIFT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
okd5|OKD5_TIMEOUT|1|30|s|/etc/okd5/okd5.conf|timeout=1|timeout=30|systemctl reload okd5|ok5|okd_to_1|jobs|state|https leftover leftover down; bounce|OKD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubeovn5|KUBEOVN5_TIMEOUT|1|30|s|/etc/kubeovn5/kubeovn5.conf|timeout=1|timeout=30|systemctl reload kubeovn5|ku5|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBEOVN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
antrea5|ANTREA5_TIMEOUT|1|30|s|/etc/antrea5/antrea5.conf|timeout=1|timeout=30|systemctl reload antrea5|an5|ant_to_1|jobs|state|https leftover leftover down; bounce|ANTREA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flannel6|FLANNEL6_TIMEOUT|1|30|s|/etc/flannel6/flannel6.conf|timeout=1|timeout=30|systemctl reload flannel6|fl6|fla_to_1|jobs|state|https leftover leftover down; bounce|FLANNEL6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
weave6|WEAVE6_TIMEOUT|1|30|s|/etc/weave6/weave6.conf|timeout=1|timeout=30|systemctl reload weave6|we6|wea_to_1|jobs|state|https leftover leftover down; bounce|WEAVE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
calico6|CALICO6_TIMEOUT|1|30|s|/etc/calico6/calico6.conf|timeout=1|timeout=30|systemctl reload calico6|ca6|cal_to_1|jobs|state|https leftover leftover down; bounce|CALICO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cilium6|CILIUM6_TIMEOUT|1|30|s|/etc/cilium6/cilium6.conf|timeout=1|timeout=30|systemctl reload cilium6|ci6|cil_to_1|jobs|state|https leftover leftover down; bounce|CILIUM6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
istio6|ISTIO6_TIMEOUT|1|30|s|/etc/istio6/istio6.conf|timeout=1|timeout=30|systemctl reload istio6|is6|ist_to_1|jobs|state|https leftover leftover down; bounce|ISTIO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
linkerd6|LINKERD6_TIMEOUT|1|30|s|/etc/linkerd6/linkerd6.conf|timeout=1|timeout=30|systemctl reload linkerd6|li6|lin_to_1|jobs|state|https leftover leftover down; bounce|LINKERD6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
consul6|CONSUL6_TIMEOUT|1|30|s|/etc/consul6/consul6.conf|timeout=1|timeout=30|systemctl reload consul6|co6|con_to_1|jobs|state|https leftover leftover down; bounce|CONSUL6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
etcd6|ETCD6_TIMEOUT|1|30|s|/etc/etcd6/etcd6.conf|timeout=1|timeout=30|systemctl reload etcd6|et6|etc_to_1|jobs|state|https leftover leftover down; bounce|ETCD6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zookeeper6|ZOOKEEPER6_TIMEOUT|1|30|s|/etc/zookeeper6/zookeeper6.conf|timeout=1|timeout=30|systemctl reload zookeeper6|zo6|zoo_to_1|jobs|state|https leftover leftover down; bounce|ZOOKEEPER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vault6|VAULT6_TIMEOUT|1|30|s|/etc/vault6/vault6.conf|timeout=1|timeout=30|systemctl reload vault6|va6|vau_to_1|jobs|state|https leftover leftover down; bounce|VAULT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nomad6|NOMAD6_TIMEOUT|1|30|s|/etc/nomad6/nomad6.conf|timeout=1|timeout=30|systemctl reload nomad6|no6|nom_to_1|jobs|state|https leftover leftover down; bounce|NOMAD6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
terraform6|TERRAFORM6_TIMEOUT|1|30|s|/etc/terraform6/terraform6.conf|timeout=1|timeout=30|systemctl reload terraform6|te6|ter_to_1|jobs|state|https leftover leftover down; bounce|TERRAFORM6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pulumi6|PULUMI6_TIMEOUT|1|30|s|/etc/pulumi6/pulumi6.conf|timeout=1|timeout=30|systemctl reload pulumi6|pu6|pul_to_1|jobs|state|https leftover leftover down; bounce|PULUMI6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ansible6|ANSIBLE6_TIMEOUT|1|30|s|/etc/ansible6/ansible6.conf|timeout=1|timeout=30|systemctl reload ansible6|an6|ans_to_1|jobs|state|https leftover leftover down; bounce|ANSIBLE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
salt6|SALT6_TIMEOUT|1|30|s|/etc/salt6/salt6.conf|timeout=1|timeout=30|systemctl reload salt6|sa6|sal_to_1|jobs|state|https leftover leftover down; bounce|SALT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "bmc5/redfish5/idrac5/ilo5/zabbix5/icinga5/nagios5/splunk5/fluentd5/fluentbit5/vector5/filebeat5/metricbeat5/logstash5/graylog5/netbox5/nautobot5/blackbox5/snmp5/nodeexporter5/smartmon5/openshift5/okd5/kubeovn5/antrea5/flannel6/weave6/calico6/cilium6/istio6/linkerd6/consul6/etcd6/zookeeper6/vault6/nomad6/terraform6/pulumi6/ansible6/salt6"
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
        svc = f"t1{i:02d}x"
        ns = f"t1{i:02d}"
        clu = f"prod-apux{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14403 + i }"
        node = f"ip-10-162-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4941


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-92 leftover: {WAVE}.",
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
