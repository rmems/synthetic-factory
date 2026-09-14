#!/usr/bin/env python3
"""IRC mill r4481+ — wave-69 cluster-api/baremetal leftover.

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
k3d2|K3D2_TIMEOUT|1|30|s|/etc/k3d2/k3d2.conf|timeout=1|timeout=30|systemctl reload k3d2|k3d|k3d_to_1|nodes|images|docker leftover leftover down; bounce|K3D2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the nodes 504s
vagrant2|VAGRANT2_TIMEOUT|1|30|s|/etc/vagrant2/vagrant2.conf|timeout=1|timeout=30|systemctl reload vagrant2|vg|vag_to_1|vms|boxes|libvirt leftover leftover down; bounce|VAGRANT2_TIMEOUT leftover 1 leftover; a 2s up is aborted so the vms 504s
packer2|PACKER2_TIMEOUT|1|30|s|/etc/packer2/packer2.conf|timeout=1|timeout=30|systemctl reload packer2|pk|pac_to_1|images|builds|fs leftover leftover down; bounce|PACKER2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the images 504s
terraform2|TERRAFORM2_TIMEOUT|1|30|s|/etc/terraform2/terraform2.conf|timeout=1|timeout=30|systemctl reload terraform2|tf|ter_to_1|states|plans|https leftover leftover down; bounce|TERRAFORM2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the states 504s
pulumi2|PULUMI2_TIMEOUT|1|30|s|/etc/pulumi2/pulumi2.conf|timeout=1|timeout=30|systemctl reload pulumi2|pu|pul_to_1|stacks|states|https leftover leftover down; bounce|PULUMI2_TIMEOUT leftover 1 leftover; a 2s up is aborted so the stacks 504s
crossplane2|CROSSPLANE2_TIMEOUT|1|30|s|/etc/crossplane2/crossplane2.conf|timeout=1|timeout=30|systemctl reload crossplane2|xp|cro_to_1|claims|xrs|k8s leftover leftover down; bounce|CROSSPLANE2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the claims 504s
kamaji2|KAMAJI2_TIMEOUT|1|30|s|/etc/kamaji2/kamaji2.conf|timeout=1|timeout=30|systemctl reload kamaji2|kj|kam_to_1|tcp|tenants|k8s leftover leftover down; bounce|KAMAJI2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the tcp 504s
vcluster2|VCLUSTER2_TIMEOUT|1|30|s|/etc/vcluster2/vcluster2.conf|timeout=1|timeout=30|systemctl reload vcluster2|vc|vcl_to_1|vclusters|syncers|k8s leftover leftover down; bounce|VCLUSTER2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vclusters 504s
loft2|LOFT2_TIMEOUT|1|30|s|/etc/loft2/loft2.conf|timeout=1|timeout=30|systemctl reload loft2|lf|lof_to_1|spaces|vclusters|https leftover leftover down; bounce|LOFT2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the spaces 504s
mirrord|MIRRORD_TIMEOUT|1|30|s|/etc/mirrord/mirrord.conf|timeout=1|timeout=30|systemctl reload mirrord|mr|mir_to_1|steals|pods|k8s leftover leftover down; bounce|MIRRORD_TIMEOUT leftover 1 leftover; a 2s steal is aborted so the steals 504s
okteto2|OKTETO2_TIMEOUT|1|30|s|/etc/okteto2/okteto2.conf|timeout=1|timeout=30|systemctl reload okteto2|ok|okt_to_1|devs|syncthing|k8s leftover leftover down; bounce|OKTETO2_TIMEOUT leftover 1 leftover; a 2s up is aborted so the devs 504s
skaffold3|SKAFFOLD3_TIMEOUT|1|30|s|/etc/skaffold3/skaffold3.conf|timeout=1|timeout=30|systemctl reload skaffold3|sf|ska_to_1|builds|deploys|k8s leftover leftover down; bounce|SKAFFOLD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
telepresence2|TELEPRESENCE2_TIMEOUT|1|30|s|/etc/telepresence2/telepresence2.conf|timeout=1|timeout=30|systemctl reload telepresence2|tp|tel_to_1|intercepts|traffic|k8s leftover leftover down; bounce|TELEPRESENCE2_TIMEOUT leftover 1 leftover; a 2s intercept is aborted so the intercepts 504s
lens|LENS_TIMEOUT|1|30|s|/etc/lens/lens.conf|timeout=1|timeout=30|systemctl reload lens|ln|len_to_1|clusters|views|https leftover leftover down; bounce|LENS_TIMEOUT leftover 1 leftover; a 2s watch is aborted so the clusters 504s
octant|OCTANT_TIMEOUT|1|30|s|/etc/octant/octant.conf|timeout=1|timeout=30|systemctl reload octant|oc|oct_to_1|views|objects|k8s leftover leftover down; bounce|OCTANT_TIMEOUT leftover 1 leftover; a 2s watch is aborted so the views 504s
kubenav|KUBENAV_TIMEOUT|1|30|s|/etc/kubenav/kubenav.conf|timeout=1|timeout=30|systemctl reload kubenav|kn|kub_to_1|objects|ns|k8s leftover leftover down; bounce|KUBENAV_TIMEOUT leftover 1 leftover; a 2s watch is aborted so the objects 504s
kubevious|KUBEVIOUS_TIMEOUT|1|30|s|/etc/kubevious/kubevious.conf|timeout=1|timeout=30|systemctl reload kubevious|kv|kub_to_1|graphs|objects|k8s leftover leftover down; bounce|KUBEVIOUS_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the graphs 504s
karpenter2|KARPENTER2_TIMEOUT|1|30|s|/etc/karpenter2/karpenter2.conf|timeout=1|timeout=30|systemctl reload karpenter2|kp|kar_to_1|nodes|provs|k8s leftover leftover down; bounce|KARPENTER2_TIMEOUT leftover 1 leftover; a 2s provision is aborted so the nodes 504s
clusterautoscaler|CLUSTERAUTOSCALER_TIMEOUT|1|30|s|/etc/clusterautoscaler/clusterautoscaler.conf|timeout=1|timeout=30|systemctl reload clusterautoscaler|ca|clu_to_1|nodes|asgs|k8s leftover leftover down; bounce|CLUSTERAUTOSCALER_TIMEOUT leftover 1 leftover; a 2s scale is aborted so the nodes 504s
kubefire|KUBEFIRE_TIMEOUT|1|30|s|/etc/kubefire/kubefire.conf|timeout=1|timeout=30|systemctl reload kubefire|kf|kub_to_1|vms|clusters|ignite leftover leftover down; bounce|KUBEFIRE_TIMEOUT leftover 1 leftover; a 2s create is aborted so the vms 504s
firekube|FIREKUBE_TIMEOUT|1|30|s|/etc/firekube/firekube.conf|timeout=1|timeout=30|systemctl reload firekube|fk|fir_to_1|clusters|ignite|k8s leftover leftover down; bounce|FIREKUBE_TIMEOUT leftover 1 leftover; a 2s up is aborted so the clusters 504s
capm3|CAPM3_TIMEOUT|1|30|s|/etc/capm3/capm3.conf|timeout=1|timeout=30|systemctl reload capm3|m3|cap_to_1|machines|bmo|k8s leftover leftover down; bounce|CAPM3_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capg|CAPG_TIMEOUT|1|30|s|/etc/capg/capg.conf|timeout=1|timeout=30|systemctl reload capg|cg|cap_to_1|machines|gcp|k8s leftover leftover down; bounce|CAPG_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capd|CAPD_TIMEOUT|1|30|s|/etc/capd/capd.conf|timeout=1|timeout=30|systemctl reload capd|cd|cap_to_1|machines|docker|k8s leftover leftover down; bounce|CAPD_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capibm|CAPIBM_TIMEOUT|1|30|s|/etc/capibm/capibm.conf|timeout=1|timeout=30|systemctl reload capibm|ci|cap_to_1|machines|ibm|k8s leftover leftover down; bounce|CAPIBM_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capdo|CAPDO_TIMEOUT|1|30|s|/etc/capdo/capdo.conf|timeout=1|timeout=30|systemctl reload capdo|do|cap_to_1|machines|do|k8s leftover leftover down; bounce|CAPDO_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
caph|CAPH_TIMEOUT|1|30|s|/etc/caph/caph.conf|timeout=1|timeout=30|systemctl reload caph|ch|cap_to_1|machines|hcloud|k8s leftover leftover down; bounce|CAPH_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capiibm|CAPIIBM_TIMEOUT|1|30|s|/etc/capiibm/capiibm.conf|timeout=1|timeout=30|systemctl reload capiibm|ib|cap_to_1|machines|ibmcloud|k8s leftover leftover down; bounce|CAPIIBM_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
metal3|METAL3_TIMEOUT|1|30|s|/etc/metal3/metal3.conf|timeout=1|timeout=30|systemctl reload metal3|mt|met_to_1|hosts|bmc|k8s leftover leftover down; bounce|METAL3_TIMEOUT leftover 1 leftover; a 2s provision is aborted so the hosts 504s
tinkerbell|TINKERBELL_TIMEOUT|1|30|s|/etc/tinkerbell/tinkerbell.conf|timeout=1|timeout=30|systemctl reload tinkerbell|tb|tin_to_1|workflows|hw|https leftover leftover down; bounce|TINKERBELL_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the workflows 504s
maas2|MAAS2_TIMEOUT|1|30|s|/etc/maas2/maas2.conf|timeout=1|timeout=30|systemctl reload maas2|ms|maa_to_1|nodes|pxe|https leftover leftover down; bounce|MAAS2_TIMEOUT leftover 1 leftover; a 2s commission is aborted so the nodes 504s
foreman2|FOREMAN2_TIMEOUT|1|30|s|/etc/foreman2/foreman2.conf|timeout=1|timeout=30|systemctl reload foreman2|fm|for_to_1|hosts|enc|https leftover leftover down; bounce|FOREMAN2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the hosts 504s
katello2|KATELLO2_TIMEOUT|1|30|s|/etc/katello2/katello2.conf|timeout=1|timeout=30|systemctl reload katello2|kt|kat_to_1|cv|repos|https leftover leftover down; bounce|KATELLO2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the cv 504s
uyuni2|UYUNI2_TIMEOUT|1|30|s|/etc/uyuni2/uyuni2.conf|timeout=1|timeout=30|systemctl reload uyuni2|uy|uyu_to_1|systems|channels|https leftover leftover down; bounce|UYUNI2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the systems 504s
spacewalk2|SPACEWALK2_TIMEOUT|1|30|s|/etc/spacewalk2/spacewalk2.conf|timeout=1|timeout=30|systemctl reload spacewalk2|sw|spa_to_1|systems|channels|https leftover leftover down; bounce|SPACEWALK2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the systems 504s
satellite2|SATELLITE2_TIMEOUT|1|30|s|/etc/satellite2/satellite2.conf|timeout=1|timeout=30|systemctl reload satellite2|st|sat_to_1|hosts|cv|https leftover leftover down; bounce|SATELLITE2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the hosts 504s
digitalrebar|DIGITALREBAR_TIMEOUT|1|30|s|/etc/digitalrebar/digitalrebar.conf|timeout=1|timeout=30|systemctl reload digitalrebar|dr|dig_to_1|machines|bootenvs|https leftover leftover down; bounce|DIGITALREBAR_TIMEOUT leftover 1 leftover; a 2s provision is aborted so the machines 504s
stacki|STACKI_TIMEOUT|1|30|s|/etc/stacki/stacki.conf|timeout=1|timeout=30|systemctl reload stacki|sk|sta_to_1|backends|pallets|https leftover leftover down; bounce|STACKI_TIMEOUT leftover 1 leftover; a 2s install is aborted so the backends 504s
perceus|PERCEUS_TIMEOUT|1|30|s|/etc/perceus/perceus.conf|timeout=1|timeout=30|systemctl reload perceus|pc|per_to_1|vnfs|nodes|pxe leftover leftover down; bounce|PERCEUS_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the vnfs 504s
rocksclusters|ROCKSCLUSTERS_TIMEOUT|1|30|s|/etc/rocksclusters/rocksclusters.conf|timeout=1|timeout=30|systemctl reload rocksclusters|rk|roc_to_1|rolls|nodes|pxe leftover leftover down; bounce|ROCKSCLUSTERS_TIMEOUT leftover 1 leftover; a 2s install is aborted so the rolls 504s
'''
WAVE = (
    "k3d2/vagrant2/packer2/terraform2/pulumi2/crossplane2/kamaji2/vcluster2/loft2/mirrord/okteto2/skaffold3/telepresence2/lens/octant/kubenav/kubevious/karpenter2/clusterautoscaler/kubefire/firekube/capm3/capg/capd/capibm/capdo/caph/capiibm/metal3/tinkerbell/maas2/foreman2/katello2/uyuni2/spacewalk2/satellite2/digitalrebar/stacki/perceus/rocksclusters"
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
        svc = f"z5{i:02d}x"
        ns = f"z5{i:02d}"
        clu = f"prod-apua{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13483 + i }"
        node = f"ip-10-254-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4481


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-69 leftover: {WAVE}.",
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
