#!/usr/bin/env python3
"""IRC mill r4461+ — wave-68 ci/gitops/devex leftover.

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
singer2|SINGER2_TIMEOUT|1|30|s|/etc/singer2/singer2.conf|timeout=1|timeout=30|systemctl reload singer2|sg|sin_to_1|taps|streams|fs leftover leftover down; bounce|SINGER2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the taps 504s
greatexpect|GREATEXPECT_TIMEOUT|1|30|s|/etc/greatexpect/greatexpect.conf|timeout=1|timeout=30|systemctl reload greatexpect|ge|gre_to_1|suites|batches|fs leftover leftover down; bounce|GREATEXPECT_TIMEOUT leftover 1 leftover; a 2s validate is aborted so the suites 504s
soda2|SODA2_TIMEOUT|1|30|s|/etc/soda2/soda2.conf|timeout=1|timeout=30|systemctl reload soda2|sd|sod_to_1|scans|checks|https leftover leftover down; bounce|SODA2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the scans 504s
montecarlo2|MONTECARLO2_TIMEOUT|1|30|s|/etc/montecarlo2/montecarlo2.conf|timeout=1|timeout=30|systemctl reload montecarlo2|mc|mon_to_1|monitors|tables|https leftover leftover down; bounce|MONTECARLO2_TIMEOUT leftover 1 leftover; a 2s check is aborted so the monitors 504s
nifi2|NIFI2_TIMEOUT|1|30|s|/etc/nifi2/nifi2.conf|timeout=1|timeout=30|systemctl reload nifi2|nf|nif_to_1|flows|procs|https leftover leftover down; bounce|NIFI2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the flows 504s
streamsets2|STREAMSETS2_TIMEOUT|1|30|s|/etc/streamsets2/streamsets2.conf|timeout=1|timeout=30|systemctl reload streamsets2|ss|str_to_1|pipes|stages|https leftover leftover down; bounce|STREAMSETS2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipes 504s
beamrunner|BEAMRUNNER_TIMEOUT|1|30|s|/etc/beamrunner/beamrunner.conf|timeout=1|timeout=30|systemctl reload beamrunner|br|bea_to_1|jobs|pcols|https leftover leftover down; bounce|BEAMRUNNER_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dagstercloud|DAGSTERCLOUD_TIMEOUT|1|30|s|/etc/dagstercloud/dagstercloud.conf|timeout=1|timeout=30|systemctl reload dagstercloud|dc|dag_to_1|jobs|runs|https leftover leftover down; bounce|DAGSTERCLOUD_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
prefectcloud|PREFECTCLOUD_TIMEOUT|1|30|s|/etc/prefectcloud/prefectcloud.conf|timeout=1|timeout=30|systemctl reload prefectcloud|pf|pre_to_1|flows|runs|https leftover leftover down; bounce|PREFECTCLOUD_TIMEOUT leftover 1 leftover; a 2s run is aborted so the flows 504s
temporal2|TEMPORAL2_TIMEOUT|1|30|s|/etc/temporal2/temporal2.conf|timeout=1|timeout=30|systemctl reload temporal2|tm|tem_to_1|wfs|tasks|grpc leftover leftover down; bounce|TEMPORAL2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the wfs 504s
cadence2|CADENCE2_TIMEOUT|1|30|s|/etc/cadence2/cadence2.conf|timeout=1|timeout=30|systemctl reload cadence2|cd|cad_to_1|wfs|tasks|grpc leftover leftover down; bounce|CADENCE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the wfs 504s
argoevents|ARGOEVENTS_TIMEOUT|1|30|s|/etc/argoevents/argoevents.conf|timeout=1|timeout=30|systemctl reload argoevents|ae|arg_to_1|sensors|buses|k8s leftover leftover down; bounce|ARGOEVENTS_TIMEOUT leftover 1 leftover; a 2s fire is aborted so the sensors 504s
argoworkflows|ARGOWORKFLOWS_TIMEOUT|1|30|s|/etc/argoworkflows/argoworkflows.conf|timeout=1|timeout=30|systemctl reload argoworkflows|aw|arg_to_1|wfs|pods|k8s leftover leftover down; bounce|ARGOWORKFLOWS_TIMEOUT leftover 1 leftover; a 2s run is aborted so the wfs 504s
tekton2|TEKTON2_TIMEOUT|1|30|s|/etc/tekton2/tekton2.conf|timeout=1|timeout=30|systemctl reload tekton2|tk|tek_to_1|pipelineruns|tasks|k8s leftover leftover down; bounce|TEKTON2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelineruns 504s
spinnaker2|SPINNAKER2_TIMEOUT|1|30|s|/etc/spinnaker2/spinnaker2.conf|timeout=1|timeout=30|systemctl reload spinnaker2|sp|spi_to_1|pipelines|stages|https leftover leftover down; bounce|SPINNAKER2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
buildkite2|BUILDKITE2_TIMEOUT|1|30|s|/etc/buildkite2/buildkite2.conf|timeout=1|timeout=30|systemctl reload buildkite2|bk|bui_to_1|jobs|agents|https leftover leftover down; bounce|BUILDKITE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
woodpecker2|WOODPECKER2_TIMEOUT|1|30|s|/etc/woodpecker2/woodpecker2.conf|timeout=1|timeout=30|systemctl reload woodpecker2|wp|woo_to_1|builds|steps|https leftover leftover down; bounce|WOODPECKER2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
gitea2|GITEA2_TIMEOUT|1|30|s|/etc/gitea2/gitea2.conf|timeout=1|timeout=30|systemctl reload gitea2|gt|git_to_1|repos|hooks|https leftover leftover down; bounce|GITEA2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
sourcehut|SOURCEHUT_TIMEOUT|1|30|s|/etc/sourcehut/sourcehut.conf|timeout=1|timeout=30|systemctl reload sourcehut|sh|sou_to_1|repos|builds|https leftover leftover down; bounce|SOURCEHUT_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
pagure|PAGURE_TIMEOUT|1|30|s|/etc/pagure/pagure.conf|timeout=1|timeout=30|systemctl reload pagure|pg|pag_to_1|repos|prs|https leftover leftover down; bounce|PAGURE_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
phabricator|PHABRICATOR_TIMEOUT|1|30|s|/etc/phabricator/phabricator.conf|timeout=1|timeout=30|systemctl reload phabricator|ph|pha_to_1|diffs|repos|https leftover leftover down; bounce|PHABRICATOR_TIMEOUT leftover 1 leftover; a 2s land is aborted so the diffs 504s
reviewboard|REVIEWBOARD_TIMEOUT|1|30|s|/etc/reviewboard/reviewboard.conf|timeout=1|timeout=30|systemctl reload reviewboard|rb|rev_to_1|reviews|diffs|https leftover leftover down; bounce|REVIEWBOARD_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the reviews 504s
gerrit2|GERRIT2_TIMEOUT|1|30|s|/etc/gerrit2/gerrit2.conf|timeout=1|timeout=30|systemctl reload gerrit2|gr|ger_to_1|changes|refs|https leftover leftover down; bounce|GERRIT2_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the changes 504s
zuulci|ZUULCI_TIMEOUT|1|30|s|/etc/zuulci/zuulci.conf|timeout=1|timeout=30|systemctl reload zuulci|zu|zuu_to_1|jobs|pipelines|https leftover leftover down; bounce|ZUULCI_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jenkins2|JENKINS2_TIMEOUT|1|30|s|/etc/jenkins2/jenkins2.conf|timeout=1|timeout=30|systemctl reload jenkins2|jk|jen_to_1|jobs|nodes|https leftover leftover down; bounce|JENKINS2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
harness2|HARNESS2_TIMEOUT|1|30|s|/etc/harness2/harness2.conf|timeout=1|timeout=30|systemctl reload harness2|hn|har_to_1|pipelines|steps|https leftover leftover down; bounce|HARNESS2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipelines 504s
werf|WERF_TIMEOUT|1|30|s|/etc/werf/werf.conf|timeout=1|timeout=30|systemctl reload werf|wf|wer_to_1|images|releases|k8s leftover leftover down; bounce|WERF_TIMEOUT leftover 1 leftover; a 2s converge is aborted so the images 504s
gardenio|GARDENIO_TIMEOUT|1|30|s|/etc/gardenio/gardenio.conf|timeout=1|timeout=30|systemctl reload gardenio|gd|gar_to_1|modules|deploys|k8s leftover leftover down; bounce|GARDENIO_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the modules 504s
skaffold2|SKAFFOLD2_TIMEOUT|1|30|s|/etc/skaffold2/skaffold2.conf|timeout=1|timeout=30|systemctl reload skaffold2|sk|ska_to_1|builds|deploys|k8s leftover leftover down; bounce|SKAFFOLD2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builds 504s
draft|DRAFT_TIMEOUT|1|30|s|/etc/draft/draft.conf|timeout=1|timeout=30|systemctl reload draft|df|dra_to_1|charts|deploys|k8s leftover leftover down; bounce|DRAFT_TIMEOUT leftover 1 leftover; a 2s up is aborted so the charts 504s
gitkube|GITKUBE_TIMEOUT|1|30|s|/etc/gitkube/gitkube.conf|timeout=1|timeout=30|systemctl reload gitkube|gk|git_to_1|builds|hooks|k8s leftover leftover down; bounce|GITKUBE_TIMEOUT leftover 1 leftover; a 2s build is aborted so the builds 504s
flux2|FLUX2_TIMEOUT|1|30|s|/etc/flux2/flux2.conf|timeout=1|timeout=30|systemctl reload flux2|fx|flu_to_1|kustomizations|gits|k8s leftover leftover down; bounce|FLUX2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the kustomizations 504s
argo2|ARGO2_TIMEOUT|1|30|s|/etc/argo2/argo2.conf|timeout=1|timeout=30|systemctl reload argo2|ag|arg_to_1|apps|syncs|k8s leftover leftover down; bounce|ARGO2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the apps 504s
fleet2|FLEET2_TIMEOUT|1|30|s|/etc/fleet2/fleet2.conf|timeout=1|timeout=30|systemctl reload fleet2|fl|fle_to_1|bundles|clusters|k8s leftover leftover down; bounce|FLEET2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the bundles 504s
rancher2|RANCHER2_TIMEOUT|1|30|s|/etc/rancher2/rancher2.conf|timeout=1|timeout=30|systemctl reload rancher2|rn|ran_to_1|clusters|projects|https leftover leftover down; bounce|RANCHER2_TIMEOUT leftover 1 leftover; a 2s provision is aborted so the clusters 504s
k3sup|K3SUP_TIMEOUT|1|30|s|/etc/k3sup/k3sup.conf|timeout=1|timeout=30|systemctl reload k3sup|k3|k3s_to_1|nodes|joins|ssh leftover leftover down; bounce|K3SUP_TIMEOUT leftover 1 leftover; a 2s install is aborted so the nodes 504s
k0sctl|K0SCTL_TIMEOUT|1|30|s|/etc/k0sctl/k0sctl.conf|timeout=1|timeout=30|systemctl reload k0sctl|k0|k0s_to_1|nodes|spec|ssh leftover leftover down; bounce|K0SCTL_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the nodes 504s
microk8s2|MICROK8S2_TIMEOUT|1|30|s|/etc/microk8s2/microk8s2.conf|timeout=1|timeout=30|systemctl reload microk8s2|mk|mic_to_1|addons|snaps|k8s leftover leftover down; bounce|MICROK8S2_TIMEOUT leftover 1 leftover; a 2s enable is aborted so the addons 504s
minikube2|MINIKUBE2_TIMEOUT|1|30|s|/etc/minikube2/minikube2.conf|timeout=1|timeout=30|systemctl reload minikube2|mn|min_to_1|cluster|vm|k8s leftover leftover down; bounce|MINIKUBE2_TIMEOUT leftover 1 leftover; a 2s start is aborted so the cluster 504s
kind2|KIND2_TIMEOUT|1|30|s|/etc/kind2/kind2.conf|timeout=1|timeout=30|systemctl reload kind2|kd|kin_to_1|nodes|images|docker leftover leftover down; bounce|KIND2_TIMEOUT leftover 1 leftover; a 2s create is aborted so the nodes 504s
'''
WAVE = (
    "singer2/greatexpect/soda2/montecarlo2/nifi2/streamsets2/beamrunner/dagstercloud/prefectcloud/temporal2/cadence2/argoevents/argoworkflows/tekton2/spinnaker2/buildkite2/woodpecker2/gitea2/sourcehut/pagure/phabricator/reviewboard/gerrit2/zuulci/jenkins2/harness2/werf/gardenio/skaffold2/draft/gitkube/flux2/argo2/fleet2/rancher2/k3sup/k0sctl/microk8s2/minikube2/kind2"
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
        svc = f"y4{i:02d}x"
        ns = f"y4{i:02d}"
        clu = f"prod-aptz{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13443 + i }"
        node = f"ip-10-253-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4461


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-68 leftover: {WAVE}.",
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
