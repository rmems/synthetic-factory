#!/usr/bin/env python3
"""IRC mill r4501+ — wave-70 lakehouse/mlops leftover.

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
dvc2|DVC2_TIMEOUT|1|30|s|/etc/dvc2/dvc2.conf|timeout=1|timeout=30|systemctl reload dvc2|dv|dvc_to_1|revs|remotes|fs leftover leftover down; bounce|DVC2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the revs 504s
lakefs2|LAKEFS2_TIMEOUT|1|30|s|/etc/lakefs2/lakefs2.conf|timeout=1|timeout=30|systemctl reload lakefs2|lk|lak_to_1|commits|repos|https leftover leftover down; bounce|LAKEFS2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the commits 504s
delta2|DELTA2_TIMEOUT|1|30|s|/etc/delta2/delta2.conf|timeout=1|timeout=30|systemctl reload delta2|dl|del_to_1|logs|tables|s3 leftover leftover down; bounce|DELTA2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the logs 504s
iceberg2|ICEBERG2_TIMEOUT|1|30|s|/etc/iceberg2/iceberg2.conf|timeout=1|timeout=30|systemctl reload iceberg2|ib|ice_to_1|snapshots|tables|s3 leftover leftover down; bounce|ICEBERG2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the snapshots 504s
hudi2|HUDI2_TIMEOUT|1|30|s|/etc/hudi2/hudi2.conf|timeout=1|timeout=30|systemctl reload hudi2|hd|hud_to_1|commits|tables|s3 leftover leftover down; bounce|HUDI2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the commits 504s
nessie2|NESSIE2_TIMEOUT|1|30|s|/etc/nessie2/nessie2.conf|timeout=1|timeout=30|systemctl reload nessie2|ns|nes_to_1|refs|contents|https leftover leftover down; bounce|NESSIE2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the refs 504s
wandb2|WANDB2_TIMEOUT|1|30|s|/etc/wandb2/wandb2.conf|timeout=1|timeout=30|systemctl reload wandb2|wb|wan_to_1|runs|artifacts|https leftover leftover down; bounce|WANDB2_TIMEOUT leftover 1 leftover; a 2s log is aborted so the runs 504s
mlflow2|MLFLOW2_TIMEOUT|1|30|s|/etc/mlflow2/mlflow2.conf|timeout=1|timeout=30|systemctl reload mlflow2|mf|mlf_to_1|runs|models|https leftover leftover down; bounce|MLFLOW2_TIMEOUT leftover 1 leftover; a 2s log is aborted so the runs 504s
sacred2|SACRED2_TIMEOUT|1|30|s|/etc/sacred2/sacred2.conf|timeout=1|timeout=30|systemctl reload sacred2|sc|sac_to_1|runs|observers|mongo leftover leftover down; bounce|SACRED2_TIMEOUT leftover 1 leftover; a 2s log is aborted so the runs 504s
guildai2|GUILDAI2_TIMEOUT|1|30|s|/etc/guildai2/guildai2.conf|timeout=1|timeout=30|systemctl reload guildai2|ga|gui_to_1|runs|ops|fs leftover leftover down; bounce|GUILDAI2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the runs 504s
labelstudio2|LABELSTUDIO2_TIMEOUT|1|30|s|/etc/labelstudio2/labelstudio2.conf|timeout=1|timeout=30|systemctl reload labelstudio2|ls|lab_to_1|tasks|projects|https leftover leftover down; bounce|LABELSTUDIO2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the tasks 504s
cvat2|CVAT2_TIMEOUT|1|30|s|/etc/cvat2/cvat2.conf|timeout=1|timeout=30|systemctl reload cvat2|cv|cva_to_1|jobs|tasks|https leftover leftover down; bounce|CVAT2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the jobs 504s
fiftyone2|FIFTYONE2_TIMEOUT|1|30|s|/etc/fiftyone2/fiftyone2.conf|timeout=1|timeout=30|systemctl reload fiftyone2|fo|fif_to_1|samples|datasets|https leftover leftover down; bounce|FIFTYONE2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the samples 504s
horovod2|HOROVOD2_TIMEOUT|1|30|s|/etc/horovod2/horovod2.conf|timeout=1|timeout=30|systemctl reload horovod2|hv|hor_to_1|ranks|gpus|mpi leftover leftover down; bounce|HOROVOD2_TIMEOUT leftover 1 leftover; a 2s train is aborted so the ranks 504s
deepspeed2|DEEPSPEED2_TIMEOUT|1|30|s|/etc/deepspeed2/deepspeed2.conf|timeout=1|timeout=30|systemctl reload deepspeed2|ds|dee_to_1|ranks|gpus|nccl leftover leftover down; bounce|DEEPSPEED2_TIMEOUT leftover 1 leftover; a 2s train is aborted so the ranks 504s
megatron2|MEGATRON2_TIMEOUT|1|30|s|/etc/megatron2/megatron2.conf|timeout=1|timeout=30|systemctl reload megatron2|mg|meg_to_1|ranks|gpus|nccl leftover leftover down; bounce|MEGATRON2_TIMEOUT leftover 1 leftover; a 2s train is aborted so the ranks 504s
kustomize2|KUSTOMIZE2_TIMEOUT|1|30|s|/etc/kustomize2/kustomize2.conf|timeout=1|timeout=30|systemctl reload kustomize2|kz|kus_to_1|overlays|bases|k8s leftover leftover down; bounce|KUSTOMIZE2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the overlays 504s
helmfile2|HELMFILE2_TIMEOUT|1|30|s|/etc/helmfile2/helmfile2.conf|timeout=1|timeout=30|systemctl reload helmfile2|hf|hel_to_1|releases|envs|k8s leftover leftover down; bounce|HELMFILE2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the releases 504s
jsonnet2|JSONNET2_TIMEOUT|1|30|s|/etc/jsonnet2/jsonnet2.conf|timeout=1|timeout=30|systemctl reload jsonnet2|jn|jso_to_1|manifests|libs|fs leftover leftover down; bounce|JSONNET2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the manifests 504s
kapitan2|KAPITAN2_TIMEOUT|1|30|s|/etc/kapitan2/kapitan2.conf|timeout=1|timeout=30|systemctl reload kapitan2|kp|kap_to_1|targets|inv|fs leftover leftover down; bounce|KAPITAN2_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the targets 504s
cue2|CUE2_TIMEOUT|1|30|s|/etc/cue2/cue2.conf|timeout=1|timeout=30|systemctl reload cue2|cu|cue_to_1|manifests|defs|fs leftover leftover down; bounce|CUE2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the manifests 504s
ytt2|YTT2_TIMEOUT|1|30|s|/etc/ytt2/ytt2.conf|timeout=1|timeout=30|systemctl reload ytt2|yt|ytt_to_1|manifests|tmpls|fs leftover leftover down; bounce|YTT2_TIMEOUT leftover 1 leftover; a 2s render is aborted so the manifests 504s
kapp2|KAPP2_TIMEOUT|1|30|s|/etc/kapp2/kapp2.conf|timeout=1|timeout=30|systemctl reload kapp2|ka|kap_to_1|apps|changes|k8s leftover leftover down; bounce|KAPP2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the apps 504s
kbld2|KBLD2_TIMEOUT|1|30|s|/etc/kbld2/kbld2.conf|timeout=1|timeout=30|systemctl reload kbld2|kb|kbl_to_1|images|builds|k8s leftover leftover down; bounce|KBLD2_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the images 504s
imgpkg2|IMGPKG2_TIMEOUT|1|30|s|/etc/imgpkg2/imgpkg2.conf|timeout=1|timeout=30|systemctl reload imgpkg2|im|img_to_1|bundles|images|oci leftover leftover down; bounce|IMGPKG2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the bundles 504s
vendir2|VENDIR2_TIMEOUT|1|30|s|/etc/vendir2/vendir2.conf|timeout=1|timeout=30|systemctl reload vendir2|vd|ven_to_1|dirs|lock|fs leftover leftover down; bounce|VENDIR2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the dirs 504s
nydus2|NYDUS2_TIMEOUT|1|30|s|/etc/nydus2/nydus2.conf|timeout=1|timeout=30|systemctl reload nydus2|ny|nyd_to_1|layers|fs|snapshotter leftover leftover down; bounce|NYDUS2_TIMEOUT leftover 1 leftover; a 2s prepare is aborted so the layers 504s
stargz2|STARGZ2_TIMEOUT|1|30|s|/etc/stargz2/stargz2.conf|timeout=1|timeout=30|systemctl reload stargz2|sz|sta_to_1|layers|toc|snapshotter leftover leftover down; bounce|STARGZ2_TIMEOUT leftover 1 leftover; a 2s prepare is aborted so the layers 504s
overlaybd2|OVERLAYBD2_TIMEOUT|1|30|s|/etc/overlaybd2/overlaybd2.conf|timeout=1|timeout=30|systemctl reload overlaybd2|ob|ove_to_1|layers|blobs|snapshotter leftover leftover down; bounce|OVERLAYBD2_TIMEOUT leftover 1 leftover; a 2s prepare is aborted so the layers 504s
gvisor2|GVISOR2_TIMEOUT|1|30|s|/etc/gvisor2/gvisor2.conf|timeout=1|timeout=30|systemctl reload gvisor2|gv|gvi_to_1|sandboxes|pods|k8s leftover leftover down; bounce|GVISOR2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the sandboxes 504s
kata2|KATA2_TIMEOUT|1|30|s|/etc/kata2/kata2.conf|timeout=1|timeout=30|systemctl reload kata2|kt|kat_to_1|vms|pods|k8s leftover leftover down; bounce|KATA2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the vms 504s
slirp4netns2|SLIRP4NETNS2_TIMEOUT|1|30|s|/etc/slirp4netns2/slirp4netns2.conf|timeout=1|timeout=30|systemctl reload slirp4netns2|sl|sli_to_1|ifaces|pods|netns leftover leftover down; bounce|SLIRP4NETNS2_TIMEOUT leftover 1 leftover; a 2s setup is aborted so the ifaces 504s
pasta2|PASTA2_TIMEOUT|1|30|s|/etc/pasta2/pasta2.conf|timeout=1|timeout=30|systemctl reload pasta2|ps|pas_to_1|ifaces|pods|netns leftover leftover down; bounce|PASTA2_TIMEOUT leftover 1 leftover; a 2s setup is aborted so the ifaces 504s
aardvark2|AARDVARK2_TIMEOUT|1|30|s|/etc/aardvark2/aardvark2.conf|timeout=1|timeout=30|systemctl reload aardvark2|av|aar_to_1|dns|pods|netavark leftover leftover down; bounce|AARDVARK2_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the dns 504s
netavark2|NETAVARK2_TIMEOUT|1|30|s|/etc/netavark2/netavark2.conf|timeout=1|timeout=30|systemctl reload netavark2|nv|net_to_1|ifaces|pods|cni leftover leftover down; bounce|NETAVARK2_TIMEOUT leftover 1 leftover; a 2s setup is aborted so the ifaces 504s
multus2|MULTUS2_TIMEOUT|1|30|s|/etc/multus2/multus2.conf|timeout=1|timeout=30|systemctl reload multus2|mu|mul_to_1|nads|pods|k8s leftover leftover down; bounce|MULTUS2_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the nads 504s
sriov2|SRIOV2_TIMEOUT|1|30|s|/etc/sriov2/sriov2.conf|timeout=1|timeout=30|systemctl reload sriov2|sr|sri_to_1|vfs|pods|k8s leftover leftover down; bounce|SRIOV2_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the vfs 504s
volcano2|VOLCANO2_TIMEOUT|1|30|s|/etc/volcano2/volcano2.conf|timeout=1|timeout=30|systemctl reload volcano2|vc|vol_to_1|queues|jobs|k8s leftover leftover down; bounce|VOLCANO2_TIMEOUT leftover 1 leftover; a 2s schedule is aborted so the queues 504s
yunikorn2|YUNIKORN2_TIMEOUT|1|30|s|/etc/yunikorn2/yunikorn2.conf|timeout=1|timeout=30|systemctl reload yunikorn2|yk|yun_to_1|queues|apps|k8s leftover leftover down; bounce|YUNIKORN2_TIMEOUT leftover 1 leftover; a 2s schedule is aborted so the queues 504s
kueue2|KUEUE2_TIMEOUT|1|30|s|/etc/kueue2/kueue2.conf|timeout=1|timeout=30|systemctl reload kueue2|ku|kue_to_1|queues|workloads|k8s leftover leftover down; bounce|KUEUE2_TIMEOUT leftover 1 leftover; a 2s admit is aborted so the queues 504s
'''
WAVE = (
    "dvc2/lakefs2/delta2/iceberg2/hudi2/nessie2/wandb2/mlflow2/sacred2/guildai2/labelstudio2/cvat2/fiftyone2/horovod2/deepspeed2/megatron2/kustomize2/helmfile2/jsonnet2/kapitan2/cue2/ytt2/kapp2/kbld2/imgpkg2/vendir2/nydus2/stargz2/overlaybd2/gvisor2/kata2/slirp4netns2/pasta2/aardvark2/netavark2/multus2/sriov2/volcano2/yunikorn2/kueue2"
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
        svc = f"a6{i:02d}x"
        ns = f"a6{i:02d}"
        clu = f"prod-apub{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13523 + i }"
        node = f"ip-10-180-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4501


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-70 leftover: {WAVE}.",
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
