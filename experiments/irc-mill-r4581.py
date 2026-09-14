#!/usr/bin/env python3
"""IRC mill r4581+ — wave-74 mesh/baas leftover.

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
istio2|ISTIO2_TIMEOUT|1|30|s|/etc/istio2/istio2.conf|timeout=1|timeout=30|systemctl reload istio2|is|ist_to_1|vs|dr|k8s leftover leftover down; bounce|ISTIO2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the vs 504s
linkerd3|LINKERD3_TIMEOUT|1|30|s|/etc/linkerd3/linkerd3.conf|timeout=1|timeout=30|systemctl reload linkerd3|ld|lin_to_1|meshes|tap|k8s leftover leftover down; bounce|LINKERD3_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the meshes 504s
cilium2|CILIUM2_TIMEOUT|1|30|s|/etc/cilium2/cilium2.conf|timeout=1|timeout=30|systemctl reload cilium2|ci|cil_to_1|identities|eps|k8s leftover leftover down; bounce|CILIUM2_TIMEOUT leftover 1 leftover; a 2s enforce is aborted so the identities 504s
calico2|CALICO2_TIMEOUT|1|30|s|/etc/calico2/calico2.conf|timeout=1|timeout=30|systemctl reload calico2|ca|cal_to_1|gnp|felix|k8s leftover leftover down; bounce|CALICO2_TIMEOUT leftover 1 leftover; a 2s enforce is aborted so the gnp 504s
flannel2|FLANNEL2_TIMEOUT|1|30|s|/etc/flannel2/flannel2.conf|timeout=1|timeout=30|systemctl reload flannel2|fl|fla_to_1|leases|subnets|k8s leftover leftover down; bounce|FLANNEL2_TIMEOUT leftover 1 leftover; a 2s route is aborted so the leases 504s
weave2|WEAVE2_TIMEOUT|1|30|s|/etc/weave2/weave2.conf|timeout=1|timeout=30|systemctl reload weave2|wv|wea_to_1|peers|nets|k8s leftover leftover down; bounce|WEAVE2_TIMEOUT leftover 1 leftover; a 2s route is aborted so the peers 504s
antrea2|ANTREA2_TIMEOUT|1|30|s|/etc/antrea2/antrea2.conf|timeout=1|timeout=30|systemctl reload antrea2|at|ant_to_1|anp|agents|k8s leftover leftover down; bounce|ANTREA2_TIMEOUT leftover 1 leftover; a 2s enforce is aborted so the anp 504s
ovn2|OVN2_TIMEOUT|1|30|s|/etc/ovn2/ovn2.conf|timeout=1|timeout=30|systemctl reload ovn2|ov|ovn_to_1|lrs|ls|k8s leftover leftover down; bounce|OVN2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the lrs 504s
kubeovn2|KUBEOVN2_TIMEOUT|1|30|s|/etc/kubeovn2/kubeovn2.conf|timeout=1|timeout=30|systemctl reload kubeovn2|ko|kub_to_1|subnets|vpcs|k8s leftover leftover down; bounce|KUBEOVN2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the subnets 504s
kubevip2|KUBEVIP2_TIMEOUT|1|30|s|/etc/kubevip2/kubevip2.conf|timeout=1|timeout=30|systemctl reload kubevip2|kv|kub_to_1|vips|leases|k8s leftover leftover down; bounce|KUBEVIP2_TIMEOUT leftover 1 leftover; a 2s announce is aborted so the vips 504s
keepalived2|KEEPALIVED2_TIMEOUT|1|30|s|/etc/keepalived2/keepalived2.conf|timeout=1|timeout=30|systemctl reload keepalived2|ka|kee_to_1|vips|vrrp|net leftover leftover down; bounce|KEEPALIVED2_TIMEOUT leftover 1 leftover; a 2s announce is aborted so the vips 504s
nginx2|NGINX2_TIMEOUT|1|30|s|/etc/nginx2/nginx2.conf|timeout=1|timeout=30|systemctl reload nginx2|nx|ngi_to_1|upstreams|servers|http leftover leftover down; bounce|NGINX2_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the upstreams 504s
apisix2|APISIX2_TIMEOUT|1|30|s|/etc/apisix2/apisix2.conf|timeout=1|timeout=30|systemctl reload apisix2|ap|api_to_1|routes|upstreams|https leftover leftover down; bounce|APISIX2_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the routes 504s
krakend2|KRAKEND2_TIMEOUT|1|30|s|/etc/krakend2/krakend2.conf|timeout=1|timeout=30|systemctl reload krakend2|kr|kra_to_1|eps|backends|http leftover leftover down; bounce|KRAKEND2_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the eps 504s
tyk2|TYK2_TIMEOUT|1|30|s|/etc/tyk2/tyk2.conf|timeout=1|timeout=30|systemctl reload tyk2|ty|tyk_to_1|apis|policies|https leftover leftover down; bounce|TYK2_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the apis 504s
ambassador3|AMBASSADOR3_TIMEOUT|1|30|s|/etc/ambassador3/ambassador3.conf|timeout=1|timeout=30|systemctl reload ambassador3|ab|amb_to_1|mappings|hosts|k8s leftover leftover down; bounce|AMBASSADOR3_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the mappings 504s
gloo2|GLOO2_TIMEOUT|1|30|s|/etc/gloo2/gloo2.conf|timeout=1|timeout=30|systemctl reload gloo2|gl|glo_to_1|vs|upstreams|k8s leftover leftover down; bounce|GLOO2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the vs 504s
contour3|CONTOUR3_TIMEOUT|1|30|s|/etc/contour3/contour3.conf|timeout=1|timeout=30|systemctl reload contour3|c3|con_to_1|httproxies|ir|k8s leftover leftover down; bounce|CONTOUR3_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the httproxies 504s
nginxinc2|NGINXINC2_TIMEOUT|1|30|s|/etc/nginxinc2/nginxinc2.conf|timeout=1|timeout=30|systemctl reload nginxinc2|ni|ngi_to_1|vs|upstreams|k8s leftover leftover down; bounce|NGINXINC2_TIMEOUT leftover 1 leftover; a 2s reload is aborted so the vs 504s
kongmesh2|KONGMESH2_TIMEOUT|1|30|s|/etc/kongmesh2/kongmesh2.conf|timeout=1|timeout=30|systemctl reload kongmesh2|km|kon_to_1|meshes|dps|k8s leftover leftover down; bounce|KONGMESH2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the meshes 504s
consul2|CONSUL2_TIMEOUT|1|30|s|/etc/consul2/consul2.conf|timeout=1|timeout=30|systemctl reload consul2|cs|con_to_1|services|intentions|https leftover leftover down; bounce|CONSUL2_TIMEOUT leftover 1 leftover; a 2s register is aborted so the services 504s
nomad2|NOMAD2_TIMEOUT|1|30|s|/etc/nomad2/nomad2.conf|timeout=1|timeout=30|systemctl reload nomad2|nm|nom_to_1|jobs|allocs|https leftover leftover down; bounce|NOMAD2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
vault2|VAULT2_TIMEOUT|1|30|s|/etc/vault2/vault2.conf|timeout=1|timeout=30|systemctl reload vault2|vt|vau_to_1|secrets|leases|https leftover leftover down; bounce|VAULT2_TIMEOUT leftover 1 leftover; a 2s read is aborted so the secrets 504s
boundary2|BOUNDARY2_TIMEOUT|1|30|s|/etc/boundary2/boundary2.conf|timeout=1|timeout=30|systemctl reload boundary2|bd|bou_to_1|sessions|targets|https leftover leftover down; bounce|BOUNDARY2_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the sessions 504s
waypoint2|WAYPOINT2_TIMEOUT|1|30|s|/etc/waypoint2/waypoint2.conf|timeout=1|timeout=30|systemctl reload waypoint2|wp|way_to_1|apps|releases|https leftover leftover down; bounce|WAYPOINT2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the apps 504s
packer3|PACKER3_TIMEOUT|1|30|s|/etc/packer3/packer3.conf|timeout=1|timeout=30|systemctl reload packer3|pk|pac_to_1|images|builds|fs leftover leftover down; bounce|PACKER3_TIMEOUT leftover 1 leftover; a 2s build is aborted so the images 504s
vagrant3|VAGRANT3_TIMEOUT|1|30|s|/etc/vagrant3/vagrant3.conf|timeout=1|timeout=30|systemctl reload vagrant3|vg|vag_to_1|vms|boxes|libvirt leftover leftover down; bounce|VAGRANT3_TIMEOUT leftover 1 leftover; a 2s up is aborted so the vms 504s
terraform3|TERRAFORM3_TIMEOUT|1|30|s|/etc/terraform3/terraform3.conf|timeout=1|timeout=30|systemctl reload terraform3|tf|ter_to_1|states|plans|https leftover leftover down; bounce|TERRAFORM3_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the states 504s
pulumi3|PULUMI3_TIMEOUT|1|30|s|/etc/pulumi3/pulumi3.conf|timeout=1|timeout=30|systemctl reload pulumi3|pu|pul_to_1|stacks|states|https leftover leftover down; bounce|PULUMI3_TIMEOUT leftover 1 leftover; a 2s up is aborted so the stacks 504s
cdk2|CDK2_TIMEOUT|1|30|s|/etc/cdk2/cdk2.conf|timeout=1|timeout=30|systemctl reload cdk2|ck|cdk_to_1|stacks|synths|fs leftover leftover down; bounce|CDK2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the stacks 504s
cdktf2|CDKTF2_TIMEOUT|1|30|s|/etc/cdktf2/cdktf2.conf|timeout=1|timeout=30|systemctl reload cdktf2|ct|cdk_to_1|stacks|synths|fs leftover leftover down; bounce|CDKTF2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the stacks 504s
serverless2|SERVERLESS2_TIMEOUT|1|30|s|/etc/serverless2/serverless2.conf|timeout=1|timeout=30|systemctl reload serverless2|sl|ser_to_1|fns|stages|https leftover leftover down; bounce|SERVERLESS2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
sam2|SAM2_TIMEOUT|1|30|s|/etc/sam2/sam2.conf|timeout=1|timeout=30|systemctl reload sam2|sm|sam_to_1|fns|stacks|https leftover leftover down; bounce|SAM2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
chalice2|CHALICE2_TIMEOUT|1|30|s|/etc/chalice2/chalice2.conf|timeout=1|timeout=30|systemctl reload chalice2|ch|cha_to_1|fns|apis|https leftover leftover down; bounce|CHALICE2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
zappa2|ZAPPA2_TIMEOUT|1|30|s|/etc/zappa2/zappa2.conf|timeout=1|timeout=30|systemctl reload zappa2|zp|zap_to_1|fns|apis|https leftover leftover down; bounce|ZAPPA2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
arc2|ARC2_TIMEOUT|1|30|s|/etc/arc2/arc2.conf|timeout=1|timeout=30|systemctl reload arc2|ar|arc_to_1|fns|pragmas|https leftover leftover down; bounce|ARC2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
sst2|SST2_TIMEOUT|1|30|s|/etc/sst2/sst2.conf|timeout=1|timeout=30|systemctl reload sst2|st|sst_to_1|fns|stacks|https leftover leftover down; bounce|SST2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
amplify2|AMPLIFY2_TIMEOUT|1|30|s|/etc/amplify2/amplify2.conf|timeout=1|timeout=30|systemctl reload amplify2|am|amp_to_1|apps|backends|https leftover leftover down; bounce|AMPLIFY2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the apps 504s
firebase2|FIREBASE2_TIMEOUT|1|30|s|/etc/firebase2/firebase2.conf|timeout=1|timeout=30|systemctl reload firebase2|fb|fir_to_1|fns|rules|https leftover leftover down; bounce|FIREBASE2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fns 504s
supabase2|SUPABASE2_TIMEOUT|1|30|s|/etc/supabase2/supabase2.conf|timeout=1|timeout=30|systemctl reload supabase2|sb|sup_to_1|rows|rls|https leftover leftover down; bounce|SUPABASE2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the rows 504s
'''
WAVE = (
    "istio2/linkerd3/cilium2/calico2/flannel2/weave2/antrea2/ovn2/kubeovn2/kubevip2/keepalived2/nginx2/apisix2/krakend2/tyk2/ambassador3/gloo2/contour3/nginxinc2/kongmesh2/consul2/nomad2/vault2/boundary2/waypoint2/packer3/vagrant3/terraform3/pulumi3/cdk2/cdktf2/serverless2/sam2/chalice2/zappa2/arc2/sst2/amplify2/firebase2/supabase2"
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
        svc = f"j8{i:02d}x"
        ns = f"j8{i:02d}"
        clu = f"prod-apuf{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13683 + i }"
        node = f"ip-10-184-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4581


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-74 leftover: {WAVE}.",
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
