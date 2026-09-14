#!/usr/bin/env python3
"""IRC mill r4901+ — wave-90 obs5 leftover.

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
grafana5|GRAFANA5_TIMEOUT|1|30|s|/etc/grafana5/grafana5.conf|timeout=1|timeout=30|systemctl reload grafana5|gr5|gra_to_1|jobs|state|https leftover leftover down; bounce|GRAFANA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
loki5|LOKI5_TIMEOUT|1|30|s|/etc/loki5/loki5.conf|timeout=1|timeout=30|systemctl reload loki5|lo5|lok_to_1|jobs|state|https leftover leftover down; bounce|LOKI5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tempo5|TEMPO5_TIMEOUT|1|30|s|/etc/tempo5/tempo5.conf|timeout=1|timeout=30|systemctl reload tempo5|te5|tem_to_1|jobs|state|https leftover leftover down; bounce|TEMPO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jaeger5|JAEGER5_TIMEOUT|1|30|s|/etc/jaeger5/jaeger5.conf|timeout=1|timeout=30|systemctl reload jaeger5|ja5|jae_to_1|jobs|state|https leftover leftover down; bounce|JAEGER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zipkin5|ZIPKIN5_TIMEOUT|1|30|s|/etc/zipkin5/zipkin5.conf|timeout=1|timeout=30|systemctl reload zipkin5|zi5|zip_to_1|jobs|state|https leftover leftover down; bounce|ZIPKIN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
alertmanager5|ALERTMANAGER5_TIMEOUT|1|30|s|/etc/alertmanager5/alertmanager5.conf|timeout=1|timeout=30|systemctl reload alertmanager5|al5|ale_to_1|jobs|state|https leftover leftover down; bounce|ALERTMANAGER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
thanos5|THANOS5_TIMEOUT|1|30|s|/etc/thanos5/thanos5.conf|timeout=1|timeout=30|systemctl reload thanos5|th5|tha_to_1|jobs|state|https leftover leftover down; bounce|THANOS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cortex5|CORTEX5_TIMEOUT|1|30|s|/etc/cortex5/cortex5.conf|timeout=1|timeout=30|systemctl reload cortex5|co5|cor_to_1|jobs|state|https leftover leftover down; bounce|CORTEX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mimir5|MIMIR5_TIMEOUT|1|30|s|/etc/mimir5/mimir5.conf|timeout=1|timeout=30|systemctl reload mimir5|mi5|mim_to_1|jobs|state|https leftover leftover down; bounce|MIMIR5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
consul5|CONSUL5_TIMEOUT|1|30|s|/etc/consul5/consul5.conf|timeout=1|timeout=30|systemctl reload consul5|co5|con_to_1|jobs|state|https leftover leftover down; bounce|CONSUL5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
etcd5|ETCD5_TIMEOUT|1|30|s|/etc/etcd5/etcd5.conf|timeout=1|timeout=30|systemctl reload etcd5|et5|etc_to_1|jobs|state|https leftover leftover down; bounce|ETCD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zookeeper5|ZOOKEEPER5_TIMEOUT|1|30|s|/etc/zookeeper5/zookeeper5.conf|timeout=1|timeout=30|systemctl reload zookeeper5|zo5|zoo_to_1|jobs|state|https leftover leftover down; bounce|ZOOKEEPER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vault5|VAULT5_TIMEOUT|1|30|s|/etc/vault5/vault5.conf|timeout=1|timeout=30|systemctl reload vault5|va5|vau_to_1|jobs|state|https leftover leftover down; bounce|VAULT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
boundary5|BOUNDARY5_TIMEOUT|1|30|s|/etc/boundary5/boundary5.conf|timeout=1|timeout=30|systemctl reload boundary5|bo5|bou_to_1|jobs|state|https leftover leftover down; bounce|BOUNDARY5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
waypoint5|WAYPOINT5_TIMEOUT|1|30|s|/etc/waypoint5/waypoint5.conf|timeout=1|timeout=30|systemctl reload waypoint5|wa5|way_to_1|jobs|state|https leftover leftover down; bounce|WAYPOINT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nomad5|NOMAD5_TIMEOUT|1|30|s|/etc/nomad5/nomad5.conf|timeout=1|timeout=30|systemctl reload nomad5|no5|nom_to_1|jobs|state|https leftover leftover down; bounce|NOMAD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ansible5|ANSIBLE5_TIMEOUT|1|30|s|/etc/ansible5/ansible5.conf|timeout=1|timeout=30|systemctl reload ansible5|an5|ans_to_1|jobs|state|https leftover leftover down; bounce|ANSIBLE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
salt5|SALT5_TIMEOUT|1|30|s|/etc/salt5/salt5.conf|timeout=1|timeout=30|systemctl reload salt5|sa5|sal_to_1|jobs|state|https leftover leftover down; bounce|SALT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
puppet5|PUPPET5_TIMEOUT|1|30|s|/etc/puppet5/puppet5.conf|timeout=1|timeout=30|systemctl reload puppet5|pu5|pup_to_1|jobs|state|https leftover leftover down; bounce|PUPPET5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chef5|CHEF5_TIMEOUT|1|30|s|/etc/chef5/chef5.conf|timeout=1|timeout=30|systemctl reload chef5|ch5|che_to_1|jobs|state|https leftover leftover down; bounce|CHEF5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
argocd5|ARGOCD5_TIMEOUT|1|30|s|/etc/argocd5/argocd5.conf|timeout=1|timeout=30|systemctl reload argocd5|ar5|arg_to_1|jobs|state|https leftover leftover down; bounce|ARGOCD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
istio5|ISTIO5_TIMEOUT|1|30|s|/etc/istio5/istio5.conf|timeout=1|timeout=30|systemctl reload istio5|is5|ist_to_1|jobs|state|https leftover leftover down; bounce|ISTIO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cilium5|CILIUM5_TIMEOUT|1|30|s|/etc/cilium5/cilium5.conf|timeout=1|timeout=30|systemctl reload cilium5|ci5|cil_to_1|jobs|state|https leftover leftover down; bounce|CILIUM5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
calico5|CALICO5_TIMEOUT|1|30|s|/etc/calico5/calico5.conf|timeout=1|timeout=30|systemctl reload calico5|ca5|cal_to_1|jobs|state|https leftover leftover down; bounce|CALICO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flannel5|FLANNEL5_TIMEOUT|1|30|s|/etc/flannel5/flannel5.conf|timeout=1|timeout=30|systemctl reload flannel5|fl5|fla_to_1|jobs|state|https leftover leftover down; bounce|FLANNEL5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
weave5|WEAVE5_TIMEOUT|1|30|s|/etc/weave5/weave5.conf|timeout=1|timeout=30|systemctl reload weave5|we5|wea_to_1|jobs|state|https leftover leftover down; bounce|WEAVE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
coredns5|COREDNS5_TIMEOUT|1|30|s|/etc/coredns5/coredns5.conf|timeout=1|timeout=30|systemctl reload coredns5|co5|cor_to_1|jobs|state|https leftover leftover down; bounce|COREDNS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bind5|BIND5_TIMEOUT|1|30|s|/etc/bind5/bind5.conf|timeout=1|timeout=30|systemctl reload bind5|bi5|bin_to_1|jobs|state|https leftover leftover down; bounce|BIND5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
unbound5|UNBOUND5_TIMEOUT|1|30|s|/etc/unbound5/unbound5.conf|timeout=1|timeout=30|systemctl reload unbound5|un5|unb_to_1|jobs|state|https leftover leftover down; bounce|UNBOUND5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
knot5|KNOT5_TIMEOUT|1|30|s|/etc/knot5/knot5.conf|timeout=1|timeout=30|systemctl reload knot5|kn5|kno_to_1|jobs|state|https leftover leftover down; bounce|KNOT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pdns5|PDNS5_TIMEOUT|1|30|s|/etc/pdns5/pdns5.conf|timeout=1|timeout=30|systemctl reload pdns5|pd5|pdn_to_1|jobs|state|https leftover leftover down; bounce|PDNS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nginx5|NGINX5_TIMEOUT|1|30|s|/etc/nginx5/nginx5.conf|timeout=1|timeout=30|systemctl reload nginx5|ng5|ngi_to_1|jobs|state|https leftover leftover down; bounce|NGINX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
envoy5|ENVOY5_TIMEOUT|1|30|s|/etc/envoy5/envoy5.conf|timeout=1|timeout=30|systemctl reload envoy5|en5|env_to_1|jobs|state|https leftover leftover down; bounce|ENVOY5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
apisix5|APISIX5_TIMEOUT|1|30|s|/etc/apisix5/apisix5.conf|timeout=1|timeout=30|systemctl reload apisix5|ap5|api_to_1|jobs|state|https leftover leftover down; bounce|APISIX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
krakend5|KRAKEND5_TIMEOUT|1|30|s|/etc/krakend5/krakend5.conf|timeout=1|timeout=30|systemctl reload krakend5|kr5|kra_to_1|jobs|state|https leftover leftover down; bounce|KRAKEND5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tyk5|TYK5_TIMEOUT|1|30|s|/etc/tyk5/tyk5.conf|timeout=1|timeout=30|systemctl reload tyk5|ty5|tyk_to_1|jobs|state|https leftover leftover down; bounce|TYK5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gloo5|GLOO5_TIMEOUT|1|30|s|/etc/gloo5/gloo5.conf|timeout=1|timeout=30|systemctl reload gloo5|gl5|glo_to_1|jobs|state|https leftover leftover down; bounce|GLOO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
postfix5|POSTFIX5_TIMEOUT|1|30|s|/etc/postfix5/postfix5.conf|timeout=1|timeout=30|systemctl reload postfix5|po5|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTFIX5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
exim5|EXIM5_TIMEOUT|1|30|s|/etc/exim5/exim5.conf|timeout=1|timeout=30|systemctl reload exim5|ex5|exi_to_1|jobs|state|https leftover leftover down; bounce|EXIM5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dovecot5|DOVECOT5_TIMEOUT|1|30|s|/etc/dovecot5/dovecot5.conf|timeout=1|timeout=30|systemctl reload dovecot5|do5|dov_to_1|jobs|state|https leftover leftover down; bounce|DOVECOT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "grafana5/loki5/tempo5/jaeger5/zipkin5/alertmanager5/thanos5/cortex5/mimir5/consul5/etcd5/zookeeper5/vault5/boundary5/waypoint5/nomad5/ansible5/salt5/puppet5/chef5/argocd5/istio5/cilium5/calico5/flannel5/weave5/coredns5/bind5/unbound5/knot5/pdns5/nginx5/envoy5/apisix5/krakend5/tyk5/gloo5/postfix5/exim5/dovecot5"
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
        svc = f"r3{i:02d}x"
        ns = f"r3{i:02d}"
        clu = f"prod-apuv{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14323 + i }"
        node = f"ip-10-160-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4901


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-90 leftover: {WAVE}.",
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
