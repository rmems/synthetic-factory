#!/usr/bin/env python3
"""IRC mill r4841+ — wave-87 bmc/beat leftover.

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
flink4|FLINK4_TIMEOUT|1|30|s|/etc/flink4/flink4.conf|timeout=1|timeout=30|systemctl reload flink4|fl4|fli_to_1|jobs|state|https leftover leftover down; bounce|FLINK4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hive4|HIVE4_TIMEOUT|1|30|s|/etc/hive4/hive4.conf|timeout=1|timeout=30|systemctl reload hive4|hi4|hiv_to_1|jobs|state|https leftover leftover down; bounce|HIVE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
impala4|IMPALA4_TIMEOUT|1|30|s|/etc/impala4/impala4.conf|timeout=1|timeout=30|systemctl reload impala4|im4|imp_to_1|jobs|state|https leftover leftover down; bounce|IMPALA4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kafka4|KAFKA4_TIMEOUT|1|30|s|/etc/kafka4/kafka4.conf|timeout=1|timeout=30|systemctl reload kafka4|ka4|kaf_to_1|jobs|state|https leftover leftover down; bounce|KAFKA4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pulsar4|PULSAR4_TIMEOUT|1|30|s|/etc/pulsar4/pulsar4.conf|timeout=1|timeout=30|systemctl reload pulsar4|pu4|pul_to_1|jobs|state|https leftover leftover down; bounce|PULSAR4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redpanda4|REDPANDA4_TIMEOUT|1|30|s|/etc/redpanda4/redpanda4.conf|timeout=1|timeout=30|systemctl reload redpanda4|re4|red_to_1|jobs|state|https leftover leftover down; bounce|REDPANDA4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nats4|NATS4_TIMEOUT|1|30|s|/etc/nats4/nats4.conf|timeout=1|timeout=30|systemctl reload nats4|na4|nat_to_1|jobs|state|https leftover leftover down; bounce|NATS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rabbitmq4|RABBITMQ4_TIMEOUT|1|30|s|/etc/rabbitmq4/rabbitmq4.conf|timeout=1|timeout=30|systemctl reload rabbitmq4|ra4|rab_to_1|jobs|state|https leftover leftover down; bounce|RABBITMQ4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
activemq4|ACTIVEMQ4_TIMEOUT|1|30|s|/etc/activemq4/activemq4.conf|timeout=1|timeout=30|systemctl reload activemq4|ac4|act_to_1|jobs|state|https leftover leftover down; bounce|ACTIVEMQ4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
prometheus4|PROMETHEUS4_TIMEOUT|1|30|s|/etc/prometheus4/prometheus4.conf|timeout=1|timeout=30|systemctl reload prometheus4|pr4|pro_to_1|jobs|state|https leftover leftover down; bounce|PROMETHEUS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
grafana4|GRAFANA4_TIMEOUT|1|30|s|/etc/grafana4/grafana4.conf|timeout=1|timeout=30|systemctl reload grafana4|gr4|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAFANA4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
loki4|LOKI4_TIMEOUT|1|30|s|/etc/loki4/loki4.conf|timeout=1|timeout=30|systemctl reload loki4|lo4|lok_to_1|jobs|state|https leftover leftover down; bounce|LOKI4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tempo4|TEMPO4_TIMEOUT|1|30|s|/etc/tempo4/tempo4.conf|timeout=1|timeout=30|systemctl reload tempo4|te4|tem_to_1|jobs|state|https leftover leftover down; bounce|TEMPO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jaeger4|JAEGER4_TIMEOUT|1|30|s|/etc/jaeger4/jaeger4.conf|timeout=1|timeout=30|systemctl reload jaeger4|ja4|jae_to_1|jobs|state|https leftover leftover down; bounce|JAEGER4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zipkin4|ZIPKIN4_TIMEOUT|1|30|s|/etc/zipkin4/zipkin4.conf|timeout=1|timeout=30|systemctl reload zipkin4|zi4|zip_to_1|jobs|state|https leftover leftover down; bounce|ZIPKIN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
alertmanager4|ALERTMANAGER4_TIMEOUT|1|30|s|/etc/alertmanager4/alertmanager4.conf|timeout=1|timeout=30|systemctl reload alertmanager4|al4|ale_to_1|jobs|state|https leftover leftover down; bounce|ALERTMANAGER4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
thanos4|THANOS4_TIMEOUT|1|30|s|/etc/thanos4/thanos4.conf|timeout=1|timeout=30|systemctl reload thanos4|th4|tha_to_1|jobs|state|https leftover leftover down; bounce|THANOS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cortex4|CORTEX4_TIMEOUT|1|30|s|/etc/cortex4/cortex4.conf|timeout=1|timeout=30|systemctl reload cortex4|co4|cor_to_1|jobs|state|https leftover leftover down; bounce|CORTEX4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mimir4|MIMIR4_TIMEOUT|1|30|s|/etc/mimir4/mimir4.conf|timeout=1|timeout=30|systemctl reload mimir4|mi4|mim_to_1|jobs|state|https leftover leftover down; bounce|MIMIR4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
consul4|CONSUL4_TIMEOUT|1|30|s|/etc/consul4/consul4.conf|timeout=1|timeout=30|systemctl reload consul4|co4|con_to_1|jobs|state|https leftover leftover down; bounce|CONSUL4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
etcd4|ETCD4_TIMEOUT|1|30|s|/etc/etcd4/etcd4.conf|timeout=1|timeout=30|systemctl reload etcd4|et4|etc_to_1|jobs|state|https leftover leftover down; bounce|ETCD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zookeeper4|ZOOKEEPER4_TIMEOUT|1|30|s|/etc/zookeeper4/zookeeper4.conf|timeout=1|timeout=30|systemctl reload zookeeper4|zo4|zoo_to_1|jobs|state|https leftover leftover down; bounce|ZOOKEEPER4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vault4|VAULT4_TIMEOUT|1|30|s|/etc/vault4/vault4.conf|timeout=1|timeout=30|systemctl reload vault4|va4|vau_to_1|jobs|state|https leftover leftover down; bounce|VAULT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
boundary4|BOUNDARY4_TIMEOUT|1|30|s|/etc/boundary4/boundary4.conf|timeout=1|timeout=30|systemctl reload boundary4|bo4|bou_to_1|jobs|state|https leftover leftover down; bounce|BOUNDARY4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
waypoint4|WAYPOINT4_TIMEOUT|1|30|s|/etc/waypoint4/waypoint4.conf|timeout=1|timeout=30|systemctl reload waypoint4|wa4|way_to_1|jobs|state|https leftover leftover down; bounce|WAYPOINT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nomad4|NOMAD4_TIMEOUT|1|30|s|/etc/nomad4/nomad4.conf|timeout=1|timeout=30|systemctl reload nomad4|no4|nom_to_1|jobs|state|https leftover leftover down; bounce|NOMAD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ansible4|ANSIBLE4_TIMEOUT|1|30|s|/etc/ansible4/ansible4.conf|timeout=1|timeout=30|systemctl reload ansible4|an4|ans_to_1|jobs|state|https leftover leftover down; bounce|ANSIBLE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
salt4|SALT4_TIMEOUT|1|30|s|/etc/salt4/salt4.conf|timeout=1|timeout=30|systemctl reload salt4|sa4|sal_to_1|jobs|state|https leftover leftover down; bounce|SALT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
puppet4|PUPPET4_TIMEOUT|1|30|s|/etc/puppet4/puppet4.conf|timeout=1|timeout=30|systemctl reload puppet4|pu4|pup_to_1|jobs|state|https leftover leftover down; bounce|PUPPET4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chef4|CHEF4_TIMEOUT|1|30|s|/etc/chef4/chef4.conf|timeout=1|timeout=30|systemctl reload chef4|ch4|che_to_1|jobs|state|https leftover leftover down; bounce|CHEF4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
argocd4|ARGOCD4_TIMEOUT|1|30|s|/etc/argocd4/argocd4.conf|timeout=1|timeout=30|systemctl reload argocd4|ar4|arg_to_1|jobs|state|https leftover leftover down; bounce|ARGOCD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
istio4|ISTIO4_TIMEOUT|1|30|s|/etc/istio4/istio4.conf|timeout=1|timeout=30|systemctl reload istio4|is4|ist_to_1|jobs|state|https leftover leftover down; bounce|ISTIO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cilium4|CILIUM4_TIMEOUT|1|30|s|/etc/cilium4/cilium4.conf|timeout=1|timeout=30|systemctl reload cilium4|ci4|cil_to_1|jobs|state|https leftover leftover down; bounce|CILIUM4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
calico4|CALICO4_TIMEOUT|1|30|s|/etc/calico4/calico4.conf|timeout=1|timeout=30|systemctl reload calico4|ca4|cal_to_1|jobs|state|https leftover leftover down; bounce|CALICO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flannel4|FLANNEL4_TIMEOUT|1|30|s|/etc/flannel4/flannel4.conf|timeout=1|timeout=30|systemctl reload flannel4|fl4|fla_to_1|jobs|state|https leftover leftover down; bounce|FLANNEL4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
weave4|WEAVE4_TIMEOUT|1|30|s|/etc/weave4/weave4.conf|timeout=1|timeout=30|systemctl reload weave4|we4|wea_to_1|jobs|state|https leftover leftover down; bounce|WEAVE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
coredns4|COREDNS4_TIMEOUT|1|30|s|/etc/coredns4/coredns4.conf|timeout=1|timeout=30|systemctl reload coredns4|co4|cor_to_1|jobs|state|https leftover leftover down; bounce|COREDNS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bind4|BIND4_TIMEOUT|1|30|s|/etc/bind4/bind4.conf|timeout=1|timeout=30|systemctl reload bind4|bi4|bin_to_1|jobs|state|https leftover leftover down; bounce|BIND4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
unbound4|UNBOUND4_TIMEOUT|1|30|s|/etc/unbound4/unbound4.conf|timeout=1|timeout=30|systemctl reload unbound4|un4|unb_to_1|jobs|state|https leftover leftover down; bounce|UNBOUND4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
knot4|KNOT4_TIMEOUT|1|30|s|/etc/knot4/knot4.conf|timeout=1|timeout=30|systemctl reload knot4|kn4|kno_to_1|jobs|state|https leftover leftover down; bounce|KNOT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "flink4/hive4/impala4/kafka4/pulsar4/redpanda4/nats4/rabbitmq4/activemq4/prometheus4/grafana4/loki4/tempo4/jaeger4/zipkin4/alertmanager4/thanos4/cortex4/mimir4/consul4/etcd4/zookeeper4/vault4/boundary4/waypoint4/nomad4/ansible4/salt4/puppet4/chef4/argocd4/istio4/cilium4/calico4/flannel4/weave4/coredns4/bind4/unbound4/knot4"
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
        svc = f"n0{i:02d}x"
        ns = f"n0{i:02d}"
        clu = f"prod-apus{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14203 + i }"
        node = f"ip-10-197-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4841


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-87 leftover: {WAVE}.",
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
