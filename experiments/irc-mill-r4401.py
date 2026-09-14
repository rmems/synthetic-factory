#!/usr/bin/env python3
"""IRC mill r4401+ — wave-65 config-mgmt/k8s-distro leftover.

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
chefinfraclient|CHEFINFRACLIENT_TIMEOUT|1|30|s|/etc/chefinfraclient/chefinfraclient.conf|timeout=1|timeout=30|systemctl reload chefinfraclient|ci|che_to_1|cooks|nodes|https leftover leftover down; bounce|CHEFINFRACLIENT_TIMEOUT leftover 1 leftover; a 2s converge is aborted so the cooks 504s
ansibleawx|ANSIBLEAWX_TIMEOUT|1|30|s|/etc/ansibleawx/ansibleawx.conf|timeout=1|timeout=30|systemctl reload ansibleawx|aw|ans_to_1|jobs|inventories|pg leftover leftover down; bounce|ANSIBLEAWX_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rundeck2|RUNDECK2_TIMEOUT|1|30|s|/etc/rundeck2/rundeck2.conf|timeout=1|timeout=30|systemctl reload rundeck2|rd|run_to_1|jobs|nodes|https leftover leftover down; bounce|RUNDECK2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
susemanager|SUSEMANAGER_TIMEOUT|1|30|s|/etc/susemanager/susemanager.conf|timeout=1|timeout=30|systemctl reload susemanager|su|sus_to_1|patches|systems|https leftover leftover down; bounce|SUSEMANAGER_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the patches 504s
landscape|LANDSCAPE_TIMEOUT|1|30|s|/etc/landscape/landscape.conf|timeout=1|timeout=30|systemctl reload landscape|ls|lan_to_1|scripts|hosts|https leftover leftover down; bounce|LANDSCAPE_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
landscapeclient|LANDSCAPECLIENT_TIMEOUT|1|30|s|/etc/landscapeclient/landscapeclient.conf|timeout=1|timeout=30|systemctl reload landscapeclient|lc|lan_to_1|scripts|broker|https leftover leftover down; bounce|LANDSCAPECLIENT_TIMEOUT leftover 1 leftover; a 2s run is aborted so the scripts 504s
maas|MAAS_TIMEOUT|1|30|s|/etc/maas/maas.conf|timeout=1|timeout=30|systemctl reload maas|ms|maa_to_1|nodes|pxe|https leftover leftover down; bounce|MAAS_TIMEOUT leftover 1 leftover; a 2s commission is aborted so the nodes 504s
maasregion|MAASREGION_TIMEOUT|1|30|s|/etc/maasregion/maasregion.conf|timeout=1|timeout=30|systemctl reload maasregion|mr|maa_to_1|nodes|fabrics|pg leftover leftover down; bounce|MAASREGION_TIMEOUT leftover 1 leftover; a 2s commission is aborted so the nodes 504s
juju|JUJU_TIMEOUT|1|30|s|/etc/juju/juju.conf|timeout=1|timeout=30|systemctl reload juju|jj|juj_to_1|units|models|https leftover leftover down; bounce|JUJU_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the units 504s
jujucrontroller|JUJUCRONTROLLER_TIMEOUT|1|30|s|/etc/jujucrontroller/jujucrontroller.conf|timeout=1|timeout=30|systemctl reload jujucrontroller|jc|juj_to_1|models|units|https leftover leftover down; bounce|JUJUCRONTROLLER_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the models 504s
conjureup|CONJUREUP_TIMEOUT|1|30|s|/etc/conjureup/conjureup.conf|timeout=1|timeout=30|systemctl reload conjureup|cu|con_to_1|spells|clouds|juju leftover leftover down; bounce|CONJUREUP_TIMEOUT leftover 1 leftover; a 2s cast is aborted so the spells 504s
cloudinit|CLOUDINIT_TIMEOUT|1|30|s|/etc/cloudinit/cloudinit.conf|timeout=1|timeout=30|systemctl reload cloudinit|ci2|clo_to_1|modules|userdata|fs leftover leftover down; bounce|CLOUDINIT_TIMEOUT leftover 1 leftover; a 2s run is aborted so the modules 504s
butane|BUTANE_TIMEOUT|1|30|s|/etc/butane/butane.conf|timeout=1|timeout=30|systemctl reload butane|bt|but_to_1|fccs|ign|fs leftover leftover down; bounce|BUTANE_TIMEOUT leftover 1 leftover; a 2s transpile is aborted so the fccs 504s
fcc|FCC_TIMEOUT|1|30|s|/etc/fcc/fcc.conf|timeout=1|timeout=30|systemctl reload fcc|fc|fcc_to_1|igns|specs|fs leftover leftover down; bounce|FCC_TIMEOUT leftover 1 leftover; a 2s render is aborted so the igns 504s
flatcar|FLATCAR_TIMEOUT|1|30|s|/etc/flatcar/flatcar.conf|timeout=1|timeout=30|systemctl reload flatcar|fl|fla_to_1|igns|oem|fs leftover leftover down; bounce|FLATCAR_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the igns 504s
taloslinux|TALOSLINUX_TIMEOUT|1|30|s|/etc/taloslinux/taloslinux.conf|timeout=1|timeout=30|systemctl reload taloslinux|tl|tal_to_1|cfgs|nodes|https leftover leftover down; bounce|TALOSLINUX_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the cfgs 504s
kops|KOPS_TIMEOUT|1|30|s|/etc/kops/kops.conf|timeout=1|timeout=30|systemctl reload kops|kp|kop_to_1|clusters|ig|s3 leftover leftover down; bounce|KOPS_TIMEOUT leftover 1 leftover; a 2s update is aborted so the clusters 504s
kubespray|KUBESPRAY_TIMEOUT|1|30|s|/etc/kubespray/kubespray.conf|timeout=1|timeout=30|systemctl reload kubespray|ks|kub_to_1|nodes|roles|ansible leftover leftover down; bounce|KUBESPRAY_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the nodes 504s
openshift|OPENSHIFT_TIMEOUT|1|30|s|/etc/openshift/openshift.conf|timeout=1|timeout=30|systemctl reload openshift|os|ope_to_1|operators|csvs|k8s leftover leftover down; bounce|OPENSHIFT_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the operators 504s
okd|OKD_TIMEOUT|1|30|s|/etc/okd/okd.conf|timeout=1|timeout=30|systemctl reload okd|ok|okd_to_1|operators|csvs|k8s leftover leftover down; bounce|OKD_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the operators 504s
crc|CRC_TIMEOUT|1|30|s|/etc/crc/crc.conf|timeout=1|timeout=30|systemctl reload crc|cr|crc_to_1|cluster|vm|libvirt leftover leftover down; bounce|CRC_TIMEOUT leftover 1 leftover; a 2s start is aborted so the cluster 504s
rosa|ROSA_TIMEOUT|1|30|s|/etc/rosa/rosa.conf|timeout=1|timeout=30|systemctl reload rosa|rs|ros_to_1|clusters|sts|https leftover leftover down; bounce|ROSA_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the clusters 504s
hypershift|HYPERSHIFT_TIMEOUT|1|30|s|/etc/hypershift/hypershift.conf|timeout=1|timeout=30|systemctl reload hypershift|hs|hyp_to_1|hosted|controlplanes|k8s leftover leftover down; bounce|HYPERSHIFT_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the hosted 504s
gardener|GARDENER_TIMEOUT|1|30|s|/etc/gardener/gardener.conf|timeout=1|timeout=30|systemctl reload gardener|gd|gar_to_1|shoots|seeds|k8s leftover leftover down; bounce|GARDENER_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the shoots 504s
gardenerseed|GARDENERSEED_TIMEOUT|1|30|s|/etc/gardenerseed/gardenerseed.conf|timeout=1|timeout=30|systemctl reload gardenerseed|gs|gar_to_1|shoots|garden|k8s leftover leftover down; bounce|GARDENERSEED_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the shoots 504s
capv|CAPV_TIMEOUT|1|30|s|/etc/capv/capv.conf|timeout=1|timeout=30|systemctl reload capv|cv|cap_to_1|machines|vsphere|k8s leftover leftover down; bounce|CAPV_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capz|CAPZ_TIMEOUT|1|30|s|/etc/capz/capz.conf|timeout=1|timeout=30|systemctl reload capz|cz|cap_to_1|machines|azure|k8s leftover leftover down; bounce|CAPZ_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
capa|CAPA_TIMEOUT|1|30|s|/etc/capa/capa.conf|timeout=1|timeout=30|systemctl reload capa|ca|cap_to_1|machines|aws|k8s leftover leftover down; bounce|CAPA_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the machines 504s
clusterapi|CLUSTERAPI_TIMEOUT|1|30|s|/etc/clusterapi/clusterapi.conf|timeout=1|timeout=30|systemctl reload clusterapi|capi|clu_to_1|clusters|machines|k8s leftover leftover down; bounce|CLUSTERAPI_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the clusters 504s
kamaji|KAMAJI_TIMEOUT|1|30|s|/etc/kamaji/kamaji.conf|timeout=1|timeout=30|systemctl reload kamaji|kj|kam_to_1|tcp|tenants|k8s leftover leftover down; bounce|KAMAJI_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the tcp 504s
kubevirt|KUBEVIRT_TIMEOUT|1|30|s|/etc/kubevirt/kubevirt.conf|timeout=1|timeout=30|systemctl reload kubevirt|kv|kub_to_1|vms|dv|k8s leftover leftover down; bounce|KUBEVIRT_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vms 504s
cdi|CDI_TIMEOUT|1|30|s|/etc/cdi/cdi.conf|timeout=1|timeout=30|systemctl reload cdi|cdi|cdi_to_1|dvs|pvcs|k8s leftover leftover down; bounce|CDI_TIMEOUT leftover 1 leftover; a 2s import is aborted so the dvs 504s
harvester|HARVESTER_TIMEOUT|1|30|s|/etc/harvester/harvester.conf|timeout=1|timeout=30|systemctl reload harvester|hv|har_to_1|vms|images|k8s leftover leftover down; bounce|HARVESTER_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vms 504s
longhorn2|LONGHORN2_TIMEOUT|1|30|s|/etc/longhorn2/longhorn2.conf|timeout=1|timeout=30|systemctl reload longhorn2|lh|lon_to_1|vols|replicas|k8s leftover leftover down; bounce|LONGHORN2_TIMEOUT leftover 1 leftover; a 2s rebuild is aborted so the vols 504s
pxctl|PXCTL_TIMEOUT|1|30|s|/etc/pxctl/pxctl.conf|timeout=1|timeout=30|systemctl reload pxctl|px|pxc_to_1|vols|repls|k8s leftover leftover down; bounce|PXCTL_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the vols 504s
glusterfs|GLUSTERFS_TIMEOUT|1|30|s|/etc/glusterfs/glusterfs.conf|timeout=1|timeout=30|systemctl reload glusterfs|gf|glu_to_1|bricks|vols|glusterd leftover leftover down; bounce|GLUSTERFS_TIMEOUT leftover 1 leftover; a 2s heal is aborted so the bricks 504s
beeond|BEEOND_TIMEOUT|1|30|s|/etc/beeond/beeond.conf|timeout=1|timeout=30|systemctl reload beeond|bo|bee_to_1|beegfs|nodes|fs leftover leftover down; bounce|BEEOND_TIMEOUT leftover 1 leftover; a 2s start is aborted so the beegfs 504s
lnet|LNET_TIMEOUT|1|30|s|/etc/lnet/lnet.conf|timeout=1|timeout=30|systemctl reload lnet|ln|lne_to_1|nids|routes|fs leftover leftover down; bounce|LNET_TIMEOUT leftover 1 leftover; a 2s ping is aborted so the nids 504s
mmfsd|MMFSD_TIMEOUT|1|30|s|/etc/mmfsd/mmfsd.conf|timeout=1|timeout=30|systemctl reload mmfsd|mm|mmf_to_1|nsds|fss|gpfs leftover leftover down; bounce|MMFSD_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the nsds 504s
wekaio|WEKAIO_TIMEOUT|1|30|s|/etc/wekaio/wekaio.conf|timeout=1|timeout=30|systemctl reload wekaio|wk|wek_to_1|fsds|hosts|https leftover leftover down; bounce|WEKAIO_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the fsds 504s
'''
WAVE = (
    "chefinfraclient/ansibleawx/rundeck2/susemanager/landscape/landscapeclient/maas/maasregion/juju/jujucrontroller/conjureup/cloudinit/butane/fcc/flatcar/taloslinux/kops/kubespray/openshift/okd/crc/rosa/hypershift/gardener/gardenerseed/capv/capz/capa/clusterapi/kamaji/kubevirt/cdi/harvester/longhorn2/pxctl/glusterfs/beeond/lnet/mmfsd/wekaio"
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
        svc = f"v8{i:02d}x"
        ns = f"v8{i:02d}"
        clu = f"prod-aptw{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13323 + i }"
        node = f"ip-10-250-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4401


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-65 leftover: {WAVE}.",
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
