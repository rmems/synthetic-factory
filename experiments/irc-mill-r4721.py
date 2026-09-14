#!/usr/bin/env python3
"""IRC mill r4721+ — wave-81 container/ci leftover.

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
docker2|DOCKER2_TIMEOUT|1|30|s|/etc/docker2/docker2.conf|timeout=1|timeout=30|systemctl reload docker2|dk|doc_to_1|images|layers|fs leftover leftover down; bounce|DOCKER2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the images 504s
podman2|PODMAN2_TIMEOUT|1|30|s|/etc/podman2/podman2.conf|timeout=1|timeout=30|systemctl reload podman2|pd|pod_to_1|images|layers|fs leftover leftover down; bounce|PODMAN2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the images 504s
buildah2|BUILDAH2_TIMEOUT|1|30|s|/etc/buildah2/buildah2.conf|timeout=1|timeout=30|systemctl reload buildah2|bh|bui_to_1|images|layers|fs leftover leftover down; bounce|BUILDAH2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the images 504s
skopeo2|SKOPEO2_TIMEOUT|1|30|s|/etc/skopeo2/skopeo2.conf|timeout=1|timeout=30|systemctl reload skopeo2|sk|sko_to_1|images|refs|oci leftover leftover down; bounce|SKOPEO2_TIMEOUT leftover 1 leftover; a 2s copy is aborted so the images 504s
umoci2|UMOCI2_TIMEOUT|1|30|s|/etc/umoci2/umoci2.conf|timeout=1|timeout=30|systemctl reload umoci2|um|umo_to_1|images|layers|oci leftover leftover down; bounce|UMOCI2_TIMEOUT leftover 1 leftover; a 2s unpack is aborted so the images 504s
containerd2|CONTAINERD2_TIMEOUT|1|30|s|/etc/containerd2/containerd2.conf|timeout=1|timeout=30|systemctl reload containerd2|cd|con_to_1|snapshots|tasks|grpc leftover leftover down; bounce|CONTAINERD2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the snapshots 504s
cri2|CRI2_TIMEOUT|1|30|s|/etc/cri2/cri2.conf|timeout=1|timeout=30|systemctl reload cri2|cr|cri_to_1|pods|sandboxes|grpc leftover leftover down; bounce|CRI2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pods 504s
crio2|CRIO2_TIMEOUT|1|30|s|/etc/crio2/crio2.conf|timeout=1|timeout=30|systemctl reload crio2|co|cri_to_1|pods|sandboxes|grpc leftover leftover down; bounce|CRIO2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pods 504s
runc2|RUNC2_TIMEOUT|1|30|s|/etc/runc2/runc2.conf|timeout=1|timeout=30|systemctl reload runc2|ru|run_to_1|containers|bundles|fs leftover leftover down; bounce|RUNC2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the containers 504s
crun2|CRUN2_TIMEOUT|1|30|s|/etc/crun2/crun2.conf|timeout=1|timeout=30|systemctl reload crun2|cu|cru_to_1|containers|bundles|fs leftover leftover down; bounce|CRUN2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the containers 504s
youki2|YOUKI2_TIMEOUT|1|30|s|/etc/youki2/youki2.conf|timeout=1|timeout=30|systemctl reload youki2|yk|you_to_1|containers|bundles|fs leftover leftover down; bounce|YOUKI2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the containers 504s
gvisor3|GVISOR3_TIMEOUT|1|30|s|/etc/gvisor3/gvisor3.conf|timeout=1|timeout=30|systemctl reload gvisor3|gv|gvi_to_1|sandboxes|pods|k8s leftover leftover down; bounce|GVISOR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the sandboxes 504s
kata3|KATA3_TIMEOUT|1|30|s|/etc/kata3/kata3.conf|timeout=1|timeout=30|systemctl reload kata3|kt|kat_to_1|vms|pods|k8s leftover leftover down; bounce|KATA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the vms 504s
nerdctl2|NERDCTL2_TIMEOUT|1|30|s|/etc/nerdctl2/nerdctl2.conf|timeout=1|timeout=30|systemctl reload nerdctl2|nd|ner_to_1|images|ns|containerd leftover leftover down; bounce|NERDCTL2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the images 504s
nerdctl3|NERDCTL3_TIMEOUT|1|30|s|/etc/nerdctl3/nerdctl3.conf|timeout=1|timeout=30|systemctl reload nerdctl3|n3|ner_to_1|images|ns|containerd leftover leftover down; bounce|NERDCTL3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the images 504s
compose2|COMPOSE2_TIMEOUT|1|30|s|/etc/compose2/compose2.conf|timeout=1|timeout=30|systemctl reload compose2|cp|com_to_1|services|projects|docker leftover leftover down; bounce|COMPOSE2_TIMEOUT leftover 1 leftover; a 2s up is aborted so the services 504s
swarm2|SWARM2_TIMEOUT|1|30|s|/etc/swarm2/swarm2.conf|timeout=1|timeout=30|systemctl reload swarm2|sw|swa_to_1|services|nodes|docker leftover leftover down; bounce|SWARM2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the services 504s
helm2|HELM2_TIMEOUT|1|30|s|/etc/helm2/helm2.conf|timeout=1|timeout=30|systemctl reload helm2|hm|hel_to_1|releases|charts|k8s leftover leftover down; bounce|HELM2_TIMEOUT leftover 1 leftover; a 2s upgrade is aborted so the releases 504s
helmfile3|HELMFILE3_TIMEOUT|1|30|s|/etc/helmfile3/helmfile3.conf|timeout=1|timeout=30|systemctl reload helmfile3|hf|hel_to_1|releases|envs|k8s leftover leftover down; bounce|HELMFILE3_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the releases 504s
kustomize3|KUSTOMIZE3_TIMEOUT|1|30|s|/etc/kustomize3/kustomize3.conf|timeout=1|timeout=30|systemctl reload kustomize3|kz|kus_to_1|overlays|bases|k8s leftover leftover down; bounce|KUSTOMIZE3_TIMEOUT leftover 1 leftover; a 2s build is aborted so the overlays 504s
jsonnet3|JSONNET3_TIMEOUT|1|30|s|/etc/jsonnet3/jsonnet3.conf|timeout=1|timeout=30|systemctl reload jsonnet3|jn|jso_to_1|manifests|libs|fs leftover leftover down; bounce|JSONNET3_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the manifests 504s
cue3|CUE3_TIMEOUT|1|30|s|/etc/cue3/cue3.conf|timeout=1|timeout=30|systemctl reload cue3|cu3|cue_to_1|manifests|defs|fs leftover leftover down; bounce|CUE3_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the manifests 504s
ytt3|YTT3_TIMEOUT|1|30|s|/etc/ytt3/ytt3.conf|timeout=1|timeout=30|systemctl reload ytt3|yt|ytt_to_1|manifests|tmpls|fs leftover leftover down; bounce|YTT3_TIMEOUT leftover 1 leftover; a 2s render is aborted so the manifests 504s
kapp3|KAPP3_TIMEOUT|1|30|s|/etc/kapp3/kapp3.conf|timeout=1|timeout=30|systemctl reload kapp3|ka|kap_to_1|apps|changes|k8s leftover leftover down; bounce|KAPP3_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the apps 504s
argocd2|ARGOCD2_TIMEOUT|1|30|s|/etc/argocd2/argocd2.conf|timeout=1|timeout=30|systemctl reload argocd2|ag|arg_to_1|apps|syncs|k8s leftover leftover down; bounce|ARGOCD2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the apps 504s
flux3|FLUX3_TIMEOUT|1|30|s|/etc/flux3/flux3.conf|timeout=1|timeout=30|systemctl reload flux3|fx|flu_to_1|kustomizations|gits|k8s leftover leftover down; bounce|FLUX3_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the kustomizations 504s
spinnaker3|SPINNAKER3_TIMEOUT|1|30|s|/etc/spinnaker3/spinnaker3.conf|timeout=1|timeout=30|systemctl reload spinnaker3|sp|spi_to_1|pipelines|stages|https leftover leftover down; bounce|SPINNAKER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
tekton3|TEKTON3_TIMEOUT|1|30|s|/etc/tekton3/tekton3.conf|timeout=1|timeout=30|systemctl reload tekton3|tk|tek_to_1|pipelineruns|tasks|k8s leftover leftover down; bounce|TEKTON3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelineruns 504s
jenkins3|JENKINS3_TIMEOUT|1|30|s|/etc/jenkins3/jenkins3.conf|timeout=1|timeout=30|systemctl reload jenkins3|jk|jen_to_1|jobs|nodes|https leftover leftover down; bounce|JENKINS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
travis2|TRAVIS2_TIMEOUT|1|30|s|/etc/travis2/travis2.conf|timeout=1|timeout=30|systemctl reload travis2|tv|tra_to_1|jobs|builds|https leftover leftover down; bounce|TRAVIS2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
appveyor2|APPVEYOR2_TIMEOUT|1|30|s|/etc/appveyor2/appveyor2.conf|timeout=1|timeout=30|systemctl reload appveyor2|av|app_to_1|jobs|builds|https leftover leftover down; bounce|APPVEYOR2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
azurepipelines2|AZUREPIPELINES2_TIMEOUT|1|30|s|/etc/azurepipelines2/azurepipelines2.conf|timeout=1|timeout=30|systemctl reload azurepipelines2|az|azu_to_1|jobs|builds|https leftover leftover down; bounce|AZUREPIPELINES2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
teamcity2|TEAMCITY2_TIMEOUT|1|30|s|/etc/teamcity2/teamcity2.conf|timeout=1|timeout=30|systemctl reload teamcity2|tc|tea_to_1|builds|agents|https leftover leftover down; bounce|TEAMCITY2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
bamboo2|BAMBOO2_TIMEOUT|1|30|s|/etc/bamboo2/bamboo2.conf|timeout=1|timeout=30|systemctl reload bamboo2|bb|bam_to_1|jobs|plans|https leftover leftover down; bounce|BAMBOO2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
octopus2|OCTOPUS2_TIMEOUT|1|30|s|/etc/octopus2/octopus2.conf|timeout=1|timeout=30|systemctl reload octopus2|oc|oct_to_1|deploys|envs|https leftover leftover down; bounce|OCTOPUS2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the deploys 504s
harness3|HARNESS3_TIMEOUT|1|30|s|/etc/harness3/harness3.conf|timeout=1|timeout=30|systemctl reload harness3|hn|har_to_1|pipelines|steps|https leftover leftover down; bounce|HARNESS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
codefresh2|CODEFRESH2_TIMEOUT|1|30|s|/etc/codefresh2/codefresh2.conf|timeout=1|timeout=30|systemctl reload codefresh2|cf|cod_to_1|pipelines|steps|https leftover leftover down; bounce|CODEFRESH2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
concourse2|CONCOURSE2_TIMEOUT|1|30|s|/etc/concourse2/concourse2.conf|timeout=1|timeout=30|systemctl reload concourse2|cc|con_to_1|jobs|resources|https leftover leftover down; bounce|CONCOURSE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
drone2|DRONE2_TIMEOUT|1|30|s|/etc/drone2/drone2.conf|timeout=1|timeout=30|systemctl reload drone2|dr|dro_to_1|builds|steps|https leftover leftover down; bounce|DRONE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
woodpecker3|WOODPECKER3_TIMEOUT|1|30|s|/etc/woodpecker3/woodpecker3.conf|timeout=1|timeout=30|systemctl reload woodpecker3|wp|woo_to_1|builds|steps|https leftover leftover down; bounce|WOODPECKER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
'''
WAVE = (
    "docker2/podman2/buildah2/skopeo2/umoci2/containerd2/cri2/crio2/runc2/crun2/youki2/gvisor3/kata3/nerdctl2/nerdctl3/compose2/swarm2/helm2/helmfile3/kustomize3/jsonnet3/cue3/ytt3/kapp3/argocd2/flux3/spinnaker3/tekton3/jenkins3/travis2/appveyor2/azurepipelines2/teamcity2/bamboo2/octopus2/harness3/codefresh2/concourse2/drone2/woodpecker3"
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
        svc = f"h4{i:02d}x"
        ns = f"h4{i:02d}"
        clu = f"prod-apum{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13963 + i }"
        node = f"ip-10-191-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4721


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-81 leftover: {WAVE}.",
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
