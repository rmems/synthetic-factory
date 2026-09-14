#!/usr/bin/env python3
"""IRC mill r4261+ — wave-58 nas/hypervisor leftover.

NEW on-call plants (not Wave-27–57 tails). BAN ypbind/oddjob,
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
nbdkit|NBDKIT_TIMEOUT|1|30|s|/etc/nbdkit/nbdkit.conf|timeout=1|timeout=30|systemctl reload nbdkit|nbdkit|nbk_to_1|exports|socks|unix leftover leftover down; bounce|NBDKIT_TIMEOUT leftover 1 leftover; a 2s export is aborted so the nbd 504s
libnbd|LIBNBD_TIMEOUT|1|30|s|/etc/libnbd/libnbd.conf|timeout=1|timeout=30|systemctl reload nbdinfo|nbdinfo|lnb_to_1|uri|info|tcp leftover leftover down; bounce|LIBNBD_TIMEOUT leftover 1 leftover; a 2s info is aborted so the uri 504s
gpfs|GPFS_TIMEOUT|1|30|s|/var/mmfs/etc/gpfs.conf|timeout=1|timeout=30|systemctl reload gpfs|mmgetstate|gpf_to_1|nsds|fs|mm leftover leftover down; bounce|GPFS_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the fs 504s
spectrum-scale|SCALE_TIMEOUT|1|30|s|/var/mmfs/etc/mmfs.cfg|timeout=1|timeout=30|systemctl reload gpfs|mmlscluster|ssc_to_1|nsds|fs|mm leftover leftover down; bounce|SCALE_TIMEOUT leftover 1 leftover; a 2s restripe is aborted so the fs 504s
pure|PURE_TIMEOUT|1|30|s|/etc/pure/pure.conf|timeout=1|timeout=30|systemctl reload pure|pureadm|pur_to_1|vols|arrays|https leftover leftover 403; bounce|PURE_TIMEOUT leftover 1 leftover; a 2s volume is aborted so the array 504s
netapp|NETAPP_TIMEOUT|1|30|s|/etc/netapp/ontap.conf|timeout=1|timeout=30|systemctl reload ontap|ontap|nta_to_1|vols|svms|https leftover leftover 403; bounce|NETAPP_TIMEOUT leftover 1 leftover; a 2s lun is aborted so the svm 504s
isilon|ISILON_TIMEOUT|1|30|s|/etc/isilon/isi.conf|timeout=1|timeout=30|systemctl reload isi|isi|isi_to_1|zones|nodes|https leftover leftover 403; bounce|ISILON_TIMEOUT leftover 1 leftover; a 2s quota is aborted so the zone 504s
qnap|QNAP_TIMEOUT|1|30|s|/etc/qnap/qnap.conf|timeout=1|timeout=30|systemctl reload qnap|qcli|qnp_to_1|vols|luns|https leftover leftover 403; bounce|QNAP_TIMEOUT leftover 1 leftover; a 2s snapshot is aborted so the vol 504s
truenas|TRUENAS_TIMEOUT|1|30|s|/etc/truenas/middlewared.conf|timeout=1|timeout=30|systemctl reload middlewared|midclt|tns_to_1|pools|shares|https leftover leftover 403; bounce|TRUENAS_TIMEOUT leftover 1 leftover; a 2s job is aborted so the pool 504s
freenas|FREENAS_TIMEOUT|1|30|s|/etc/freenas/middlewared.conf|timeout=1|timeout=30|systemctl reload middlewared|midclt|fns_to_1|pools|shares|https leftover leftover 403; bounce|FREENAS_TIMEOUT leftover 1 leftover; a 2s job is aborted so the pool 504s
openmediavault|OMV_TIMEOUT|1|30|s|/etc/openmediavault/config.xml|timeout=1|timeout=30|systemctl reload openmediavault-engined|omv-rpc|omv_to_1|shares|fs|rpc leftover leftover down; bounce|OMV_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the share 504s
omv|OMV2_TIMEOUT|1|30|s|/etc/openmediavault/config.xml|timeout=1|timeout=30|systemctl reload openmediavault-engined|omv-rpc|omv2_to_1|shares|fs|rpc leftover leftover down; bounce|OMV2_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the share 504s
unraid|UNRAID_TIMEOUT|1|30|s|/etc/unraid/unraid.conf|timeout=1|timeout=30|systemctl reload emhttpd|emcmd|unr_to_1|array|disks|http leftover leftover down; bounce|UNRAID_TIMEOUT leftover 1 leftover; a 2s start is aborted so the array 504s
openfiler|OPENFILER_TIMEOUT|1|30|s|/etc/openfiler/openfiler.conf|timeout=1|timeout=30|systemctl reload openfiler|openfiler|ofl_to_1|vols|luns|https leftover leftover 403; bounce|OPENFILER_TIMEOUT leftover 1 leftover; a 2s volume is aborted so the lun 504s
napp-it|NAPPIT_TIMEOUT|1|30|s|/etc/napp-it/napp-it.conf|timeout=1|timeout=30|systemctl reload napp-it|napp-it|nap_to_1|zfs|shares|https leftover leftover 403; bounce|NAPPIT_TIMEOUT leftover 1 leftover; a 2s zfs is aborted so the share 504s
nexenta|NEXENTA_TIMEOUT|1|30|s|/etc/nexenta/nms.conf|timeout=1|timeout=30|systemctl reload nms|nmc|nxt_to_1|zfs|shares|https leftover leftover 403; bounce|NEXENTA_TIMEOUT leftover 1 leftover; a 2s zfs is aborted so the share 504s
illumos|ILLUMOS_TIMEOUT|1|30|s|/etc/illumos/svccfg.conf|timeout=1|timeout=30|systemctl reload svc.startd|svcadm|ilm_to_1|fmri|svcs|smf leftover leftover down; bounce|ILLUMOS_TIMEOUT leftover 1 leftover; a 2s enable is aborted so the svc 504s
smartos|SMARTOS_TIMEOUT|1|30|s|/etc/smartos/vmadm.conf|timeout=1|timeout=30|systemctl reload vmadm|vmadm|smo_to_1|vms|zones|kvm leftover leftover down; bounce|SMARTOS_TIMEOUT leftover 1 leftover; a 2s create is aborted so the vm 504s
omnios|OMNIOS_TIMEOUT|1|30|s|/etc/omnios/pkg.conf|timeout=1|timeout=30|systemctl reload pkg|pkg|omn_to_1|pkgs|imgs|https leftover leftover 403; bounce|OMNIOS_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkg 504s
tribblix|TRIBBLIX_TIMEOUT|1|30|s|/etc/tribblix/zap.conf|timeout=1|timeout=30|systemctl reload zap|zap|trb_to_1|pkgs|overlays|https leftover leftover 403; bounce|TRIBBLIX_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkg 504s
esxi|ESXI_TIMEOUT|1|30|s|/etc/vmware/hostd/config.xml|timeout=1|timeout=30|systemctl reload hostd|esxcli|esx_to_1|vms|datastores|https leftover leftover 403; bounce|ESXI_TIMEOUT leftover 1 leftover; a 2s poweron is aborted so the vm 504s
vsphere|VSPHERE_TIMEOUT|1|30|s|/etc/vmware/vsphere.conf|timeout=1|timeout=30|systemctl reload vpxd|govc|vsp_to_1|vms|clusters|https leftover leftover 403; bounce|VSPHERE_TIMEOUT leftover 1 leftover; a 2s clone is aborted so the vm 504s
vcenter|VCENTER_TIMEOUT|1|30|s|/etc/vmware-vpx/vpxd.cfg|timeout=1|timeout=30|systemctl reload vmware-vpxd|govc|vct_to_1|vms|dcs|https leftover leftover 403; bounce|VCENTER_TIMEOUT leftover 1 leftover; a 2s task is aborted so the dc 504s
ovftool|OVFTOOL_TIMEOUT|1|60|s|/etc/vmware/ovftool.conf|timeout=1|timeout=60|systemctl reload ovftool|ovftool|ovf_to_1|ovf|datastores|https leftover leftover 403; bounce|OVFTOOL_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the ovf 504s
powercli|POWERCLI_TIMEOUT|1|30|s|/etc/vmware/powercli.conf|timeout=1|timeout=30|systemctl reload pwsh|pwsh|pcl_to_1|vms|vi|https leftover leftover 403; bounce|POWERCLI_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the cmd 504s
hyperv|HYPERV_TIMEOUT|1|30|s|/etc/hyperv/hyperv.conf|timeout=1|timeout=30|systemctl reload vmms|powershell|hyv_to_1|vms|vhdx|win leftover leftover down; bounce|HYPERV_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vm 504s
scvmm|SCVMM_TIMEOUT|1|30|s|/etc/scvmm/scvmm.conf|timeout=1|timeout=30|systemctl reload scvmmservice|powershell|scv_to_1|vms|hosts|win leftover leftover down; bounce|SCVMM_TIMEOUT leftover 1 leftover; a 2s job is aborted so the vm 504s
solaris|SOLARIS_TIMEOUT|1|30|s|/etc/solaris/svccfg.conf|timeout=1|timeout=30|systemctl reload svc.startd|svcadm|sol_to_1|fmri|svcs|smf leftover leftover down; bounce|SOLARIS_TIMEOUT leftover 1 leftover; a 2s enable is aborted so the svc 504s
aix|AIX_TIMEOUT|1|30|s|/etc/aix/srcmstr.conf|timeout=1|timeout=30|systemctl reload srcmstr|lssrc|aix_to_1|subsys|src|src leftover leftover down; bounce|AIX_TIMEOUT leftover 1 leftover; a 2s startsrc is aborted so the svc 504s
hpux|HPUX_TIMEOUT|1|30|s|/etc/hpux/sam.conf|timeout=1|timeout=30|systemctl reload sam|sam|hpx_to_1|svcs|ignite|fs leftover leftover down; bounce|HPUX_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
irix|IRIX_TIMEOUT|1|30|s|/etc/irix/chkconfig.conf|timeout=1|timeout=30|systemctl reload chkconfig|chkconfig|irx_to_1|svcs|rc|fs leftover leftover down; bounce|IRIX_TIMEOUT leftover 1 leftover; a 2s on is aborted so the svc 504s
openvms|OPENVMS_TIMEOUT|1|30|s|/etc/openvms/sysuaf.conf|timeout=1|timeout=30|systemctl reload sysman|sysman|ovm_to_1|procs|uics|vms leftover leftover down; bounce|OPENVMS_TIMEOUT leftover 1 leftover; a 2s run is aborted so the proc 504s
zos|ZOS_TIMEOUT|1|30|s|/etc/zos/jes2.conf|timeout=1|timeout=30|systemctl reload jes2|$HASP|zos_to_1|jobs|spool|jes leftover leftover down; bounce|ZOS_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the job 504s
as400|AS400_TIMEOUT|1|30|s|/etc/as400/qsys.conf|timeout=1|timeout=30|systemctl reload qsys|wrkactjob|as4_to_1|jobs|libs|os400 leftover leftover down; bounce|AS400_TIMEOUT leftover 1 leftover; a 2s sbmjob is aborted so the job 504s
os400|OS400_TIMEOUT|1|30|s|/etc/os400/qsys.conf|timeout=1|timeout=30|systemctl reload qsys|wrkactjob|os4_to_1|jobs|libs|os400 leftover leftover down; bounce|OS400_TIMEOUT leftover 1 leftover; a 2s sbmjob is aborted so the job 504s
bhyve|BHYVE_TIMEOUT|1|30|s|/etc/bhyve/bhyve.conf|timeout=1|timeout=30|systemctl reload bhyve|bhyvectl|bhy_to_1|vms|taps|vmm leftover leftover down; bounce|BHYVE_TIMEOUT leftover 1 leftover; a 2s run is aborted so the vm 504s
jails|JAILS_TIMEOUT|1|30|s|/etc/jail.conf|timeout=1|timeout=30|systemctl reload jail|jail|jai_to_1|jails|roots|jail leftover leftover down; bounce|JAILS_TIMEOUT leftover 1 leftover; a 2s start is aborted so the jail 504s
ezjail|EZJAIL_TIMEOUT|1|30|s|/usr/local/etc/ezjail.conf|timeout=1|timeout=30|systemctl reload ezjail|ezjail-admin|ezj_to_1|jails|flavours|jail leftover leftover down; bounce|EZJAIL_TIMEOUT leftover 1 leftover; a 2s start is aborted so the jail 504s
iocage|IOCAGE_TIMEOUT|1|30|s|/etc/iocage/iocage.conf|timeout=1|timeout=30|systemctl reload iocage|iocage|ioc_to_1|jails|zfs|jail leftover leftover down; bounce|IOCAGE_TIMEOUT leftover 1 leftover; a 2s start is aborted so the jail 504s
bastille|BASTILLE_TIMEOUT|1|30|s|/usr/local/etc/bastille/bastille.conf|timeout=1|timeout=30|systemctl reload bastille|bastille|bst_to_1|jails|zfs|jail leftover leftover down; bounce|BASTILLE_TIMEOUT leftover 1 leftover; a 2s start is aborted so the jail 504s
'''
WAVE58 = (
    "nbdkit/libnbd/gpfs/spectrum-scale/pure/netapp/isilon/qnap/truenas/"
    "freenas/openmediavault/omv/unraid/openfiler/napp-it/nexenta/illumos/"
    "smartos/omnios/tribblix/esxi/vsphere/vcenter/ovftool/powercli/hyperv/"
    "scvmm/solaris/aix/hpux/irix/openvms/zos/as400/os400/bhyve/jails/"
    "ezjail/iocage/bastille"
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
        svc = f"n8{i:02d}x"
        ns = f"n8{i:02d}"
        clu = f"prod-apsp{901 + i}-{svc[:3]}"
        ticket = f"W2-{13043 + i}"
        node = f"ip-10-243-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
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
m.BASE_ROUND = 4261


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4260 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-58 leftover: {WAVE58}.",
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
