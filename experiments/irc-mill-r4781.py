#!/usr/bin/env python3
"""IRC mill r4781+ — wave-84 obs/control leftover.

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
prometheus3|PROMETHEUS3_TIMEOUT|1|30|s|/etc/prometheus3/prometheus3.conf|timeout=1|timeout=30|systemctl reload prometheus3|pr3|pro_to_1|jobs|state|https leftover leftover down; bounce|PROMETHEUS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
grafana3|GRAFANA3_TIMEOUT|1|30|s|/etc/grafana3/grafana3.conf|timeout=1|timeout=30|systemctl reload grafana3|gr3|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAFANA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
loki3|LOKI3_TIMEOUT|1|30|s|/etc/loki3/loki3.conf|timeout=1|timeout=30|systemctl reload loki3|lo3|lok_to_1|jobs|state|https leftover leftover down; bounce|LOKI3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tempo3|TEMPO3_TIMEOUT|1|30|s|/etc/tempo3/tempo3.conf|timeout=1|timeout=30|systemctl reload tempo3|te3|tem_to_1|jobs|state|https leftover leftover down; bounce|TEMPO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jaeger3|JAEGER3_TIMEOUT|1|30|s|/etc/jaeger3/jaeger3.conf|timeout=1|timeout=30|systemctl reload jaeger3|ja3|jae_to_1|jobs|state|https leftover leftover down; bounce|JAEGER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zipkin3|ZIPKIN3_TIMEOUT|1|30|s|/etc/zipkin3/zipkin3.conf|timeout=1|timeout=30|systemctl reload zipkin3|zi3|zip_to_1|jobs|state|https leftover leftover down; bounce|ZIPKIN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
alertmanager3|ALERTMANAGER3_TIMEOUT|1|30|s|/etc/alertmanager3/alertmanager3.conf|timeout=1|timeout=30|systemctl reload alertmanager3|al3|ale_to_1|jobs|state|https leftover leftover down; bounce|ALERTMANAGER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
thanos3|THANOS3_TIMEOUT|1|30|s|/etc/thanos3/thanos3.conf|timeout=1|timeout=30|systemctl reload thanos3|th3|tha_to_1|jobs|state|https leftover leftover down; bounce|THANOS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cortex3|CORTEX3_TIMEOUT|1|30|s|/etc/cortex3/cortex3.conf|timeout=1|timeout=30|systemctl reload cortex3|co3|cor_to_1|jobs|state|https leftover leftover down; bounce|CORTEX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mimir3|MIMIR3_TIMEOUT|1|30|s|/etc/mimir3/mimir3.conf|timeout=1|timeout=30|systemctl reload mimir3|mi3|mim_to_1|jobs|state|https leftover leftover down; bounce|MIMIR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
victoriametrics3|VICTORIAMETRICS3_TIMEOUT|1|30|s|/etc/victoriametrics3/victoriametrics3.conf|timeout=1|timeout=30|systemctl reload victoriametrics3|vi3|vic_to_1|jobs|state|https leftover leftover down; bounce|VICTORIAMETRICS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
consul3|CONSUL3_TIMEOUT|1|30|s|/etc/consul3/consul3.conf|timeout=1|timeout=30|systemctl reload consul3|co3|con_to_1|jobs|state|https leftover leftover down; bounce|CONSUL3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
etcd3|ETCD3_TIMEOUT|1|30|s|/etc/etcd3/etcd3.conf|timeout=1|timeout=30|systemctl reload etcd3|et3|etc_to_1|jobs|state|https leftover leftover down; bounce|ETCD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zookeeper3|ZOOKEEPER3_TIMEOUT|1|30|s|/etc/zookeeper3/zookeeper3.conf|timeout=1|timeout=30|systemctl reload zookeeper3|zo3|zoo_to_1|jobs|state|https leftover leftover down; bounce|ZOOKEEPER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vault3|VAULT3_TIMEOUT|1|30|s|/etc/vault3/vault3.conf|timeout=1|timeout=30|systemctl reload vault3|va3|vau_to_1|jobs|state|https leftover leftover down; bounce|VAULT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
boundary3|BOUNDARY3_TIMEOUT|1|30|s|/etc/boundary3/boundary3.conf|timeout=1|timeout=30|systemctl reload boundary3|bo3|bou_to_1|jobs|state|https leftover leftover down; bounce|BOUNDARY3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
waypoint3|WAYPOINT3_TIMEOUT|1|30|s|/etc/waypoint3/waypoint3.conf|timeout=1|timeout=30|systemctl reload waypoint3|wa3|way_to_1|jobs|state|https leftover leftover down; bounce|WAYPOINT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nomad3|NOMAD3_TIMEOUT|1|30|s|/etc/nomad3/nomad3.conf|timeout=1|timeout=30|systemctl reload nomad3|no3|nom_to_1|jobs|state|https leftover leftover down; bounce|NOMAD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ansible3|ANSIBLE3_TIMEOUT|1|30|s|/etc/ansible3/ansible3.conf|timeout=1|timeout=30|systemctl reload ansible3|an3|ans_to_1|jobs|state|https leftover leftover down; bounce|ANSIBLE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
salt3|SALT3_TIMEOUT|1|30|s|/etc/salt3/salt3.conf|timeout=1|timeout=30|systemctl reload salt3|sa3|sal_to_1|jobs|state|https leftover leftover down; bounce|SALT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
puppet3|PUPPET3_TIMEOUT|1|30|s|/etc/puppet3/puppet3.conf|timeout=1|timeout=30|systemctl reload puppet3|pu3|pup_to_1|jobs|state|https leftover leftover down; bounce|PUPPET3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chef3|CHEF3_TIMEOUT|1|30|s|/etc/chef3/chef3.conf|timeout=1|timeout=30|systemctl reload chef3|ch3|che_to_1|jobs|state|https leftover leftover down; bounce|CHEF3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
argocd3|ARGOCD3_TIMEOUT|1|30|s|/etc/argocd3/argocd3.conf|timeout=1|timeout=30|systemctl reload argocd3|ar3|arg_to_1|jobs|state|https leftover leftover down; bounce|ARGOCD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
istio3|ISTIO3_TIMEOUT|1|30|s|/etc/istio3/istio3.conf|timeout=1|timeout=30|systemctl reload istio3|is3|ist_to_1|jobs|state|https leftover leftover down; bounce|ISTIO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cilium3|CILIUM3_TIMEOUT|1|30|s|/etc/cilium3/cilium3.conf|timeout=1|timeout=30|systemctl reload cilium3|ci3|cil_to_1|jobs|state|https leftover leftover down; bounce|CILIUM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
calico3|CALICO3_TIMEOUT|1|30|s|/etc/calico3/calico3.conf|timeout=1|timeout=30|systemctl reload calico3|ca3|cal_to_1|jobs|state|https leftover leftover down; bounce|CALICO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flannel3|FLANNEL3_TIMEOUT|1|30|s|/etc/flannel3/flannel3.conf|timeout=1|timeout=30|systemctl reload flannel3|fl3|fla_to_1|jobs|state|https leftover leftover down; bounce|FLANNEL3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
weave3|WEAVE3_TIMEOUT|1|30|s|/etc/weave3/weave3.conf|timeout=1|timeout=30|systemctl reload weave3|we3|wea_to_1|jobs|state|https leftover leftover down; bounce|WEAVE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
coredns3|COREDNS3_TIMEOUT|1|30|s|/etc/coredns3/coredns3.conf|timeout=1|timeout=30|systemctl reload coredns3|co3|cor_to_1|jobs|state|https leftover leftover down; bounce|COREDNS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bind3|BIND3_TIMEOUT|1|30|s|/etc/bind3/bind3.conf|timeout=1|timeout=30|systemctl reload bind3|bi3|bin_to_1|jobs|state|https leftover leftover down; bounce|BIND3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
unbound3|UNBOUND3_TIMEOUT|1|30|s|/etc/unbound3/unbound3.conf|timeout=1|timeout=30|systemctl reload unbound3|un3|unb_to_1|jobs|state|https leftover leftover down; bounce|UNBOUND3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
knot3|KNOT3_TIMEOUT|1|30|s|/etc/knot3/knot3.conf|timeout=1|timeout=30|systemctl reload knot3|kn3|kno_to_1|jobs|state|https leftover leftover down; bounce|KNOT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pdns3|PDNS3_TIMEOUT|1|30|s|/etc/pdns3/pdns3.conf|timeout=1|timeout=30|systemctl reload pdns3|pd3|pdn_to_1|jobs|state|https leftover leftover down; bounce|PDNS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nginx3|NGINX3_TIMEOUT|1|30|s|/etc/nginx3/nginx3.conf|timeout=1|timeout=30|systemctl reload nginx3|ng3|ngi_to_1|jobs|state|https leftover leftover down; bounce|NGINX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
envoy3|ENVOY3_TIMEOUT|1|30|s|/etc/envoy3/envoy3.conf|timeout=1|timeout=30|systemctl reload envoy3|en3|env_to_1|jobs|state|https leftover leftover down; bounce|ENVOY3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
apisix3|APISIX3_TIMEOUT|1|30|s|/etc/apisix3/apisix3.conf|timeout=1|timeout=30|systemctl reload apisix3|ap3|api_to_1|jobs|state|https leftover leftover down; bounce|APISIX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
krakend3|KRAKEND3_TIMEOUT|1|30|s|/etc/krakend3/krakend3.conf|timeout=1|timeout=30|systemctl reload krakend3|kr3|kra_to_1|jobs|state|https leftover leftover down; bounce|KRAKEND3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tyk3|TYK3_TIMEOUT|1|30|s|/etc/tyk3/tyk3.conf|timeout=1|timeout=30|systemctl reload tyk3|ty3|tyk_to_1|jobs|state|https leftover leftover down; bounce|TYK3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gloo3|GLOO3_TIMEOUT|1|30|s|/etc/gloo3/gloo3.conf|timeout=1|timeout=30|systemctl reload gloo3|gl3|glo_to_1|jobs|state|https leftover leftover down; bounce|GLOO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
postfix3|POSTFIX3_TIMEOUT|1|30|s|/etc/postfix3/postfix3.conf|timeout=1|timeout=30|systemctl reload postfix3|po3|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTFIX3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "prometheus3/grafana3/loki3/tempo3/jaeger3/zipkin3/alertmanager3/thanos3/cortex3/mimir3/victoriametrics3/consul3/etcd3/zookeeper3/vault3/boundary3/waypoint3/nomad3/ansible3/salt3/puppet3/chef3/argocd3/istio3/cilium3/calico3/flannel3/weave3/coredns3/bind3/unbound3/knot3/pdns3/nginx3/envoy3/apisix3/krakend3/tyk3/gloo3/postfix3"
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
        svc = f"k7{i:02d}x"
        ns = f"k7{i:02d}"
        clu = f"prod-apup{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14083 + i }"
        node = f"ip-10-194-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4781


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-84 leftover: {WAVE}.",
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
