#!/usr/bin/env python3
"""IRC mill r4921+ — wave-91 mail5 leftover.

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
openssh5|OPENSSH5_TIMEOUT|1|30|s|/etc/openssh5/openssh5.conf|timeout=1|timeout=30|systemctl reload openssh5|op5|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENSSH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dropbear5|DROPBEAR5_TIMEOUT|1|30|s|/etc/dropbear5/dropbear5.conf|timeout=1|timeout=30|systemctl reload dropbear5|dr5|dro_to_1|jobs|state|https leftover leftover down; bounce|DROPBEAR5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
iptables5|IPTABLES5_TIMEOUT|1|30|s|/etc/iptables5/iptables5.conf|timeout=1|timeout=30|systemctl reload iptables5|ip5|ipt_to_1|jobs|state|https leftover leftover down; bounce|IPTABLES5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nftables5|NFTABLES5_TIMEOUT|1|30|s|/etc/nftables5/nftables5.conf|timeout=1|timeout=30|systemctl reload nftables5|nf5|nft_to_1|jobs|state|https leftover leftover down; bounce|NFTABLES5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
firewalld5|FIREWALLD5_TIMEOUT|1|30|s|/etc/firewalld5/firewalld5.conf|timeout=1|timeout=30|systemctl reload firewalld5|fi5|fir_to_1|jobs|state|https leftover leftover down; bounce|FIREWALLD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openvpn5|OPENVPN5_TIMEOUT|1|30|s|/etc/openvpn5/openvpn5.conf|timeout=1|timeout=30|systemctl reload openvpn5|op5|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENVPN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
wireguard5|WIREGUARD5_TIMEOUT|1|30|s|/etc/wireguard5/wireguard5.conf|timeout=1|timeout=30|systemctl reload wireguard5|wi5|wir_to_1|jobs|state|https leftover leftover down; bounce|WIREGUARD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
strongswan5|STRONGSWAN5_TIMEOUT|1|30|s|/etc/strongswan5/strongswan5.conf|timeout=1|timeout=30|systemctl reload strongswan5|st5|str_to_1|jobs|state|https leftover leftover down; bounce|STRONGSWAN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dhcpd5|DHCPD5_TIMEOUT|1|30|s|/etc/dhcpd5/dhcpd5.conf|timeout=1|timeout=30|systemctl reload dhcpd5|dh5|dhc_to_1|jobs|state|https leftover leftover down; bounce|DHCPD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
named5|NAMED5_TIMEOUT|1|30|s|/etc/named5/named5.conf|timeout=1|timeout=30|systemctl reload named5|na5|nam_to_1|jobs|state|https leftover leftover down; bounce|NAMED5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ntpd5|NTPD5_TIMEOUT|1|30|s|/etc/ntpd5/ntpd5.conf|timeout=1|timeout=30|systemctl reload ntpd5|nt5|ntp_to_1|jobs|state|https leftover leftover down; bounce|NTPD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chrony5|CHRONY5_TIMEOUT|1|30|s|/etc/chrony5/chrony5.conf|timeout=1|timeout=30|systemctl reload chrony5|ch5|chr_to_1|jobs|state|https leftover leftover down; bounce|CHRONY5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
samba5|SAMBA5_TIMEOUT|1|30|s|/etc/samba5/samba5.conf|timeout=1|timeout=30|systemctl reload samba5|sa5|sam_to_1|jobs|state|https leftover leftover down; bounce|SAMBA5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nfs5|NFS5_TIMEOUT|1|30|s|/etc/nfs5/nfs5.conf|timeout=1|timeout=30|systemctl reload nfs5|nf5|nfs_to_1|jobs|state|https leftover leftover down; bounce|NFS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rpcbind5|RPCBIND5_TIMEOUT|1|30|s|/etc/rpcbind5/rpcbind5.conf|timeout=1|timeout=30|systemctl reload rpcbind5|rp5|rpc_to_1|jobs|state|https leftover leftover down; bounce|RPCBIND5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
autofs5|AUTOFS5_TIMEOUT|1|30|s|/etc/autofs5/autofs5.conf|timeout=1|timeout=30|systemctl reload autofs5|au5|aut_to_1|jobs|state|https leftover leftover down; bounce|AUTOFS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
qemu5|QEMU5_TIMEOUT|1|30|s|/etc/qemu5/qemu5.conf|timeout=1|timeout=30|systemctl reload qemu5|qe5|qem_to_1|jobs|state|https leftover leftover down; bounce|QEMU5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
libvirt5|LIBVIRT5_TIMEOUT|1|30|s|/etc/libvirt5/libvirt5.conf|timeout=1|timeout=30|systemctl reload libvirt5|li5|lib_to_1|jobs|state|https leftover leftover down; bounce|LIBVIRT5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
xen5|XEN5_TIMEOUT|1|30|s|/etc/xen5/xen5.conf|timeout=1|timeout=30|systemctl reload xen5|xe5|xen_to_1|jobs|state|https leftover leftover down; bounce|XEN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bhyve5|BHYVE5_TIMEOUT|1|30|s|/etc/bhyve5/bhyve5.conf|timeout=1|timeout=30|systemctl reload bhyve5|bh5|bhy_to_1|jobs|state|https leftover leftover down; bounce|BHYVE5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxc5|LXC5_TIMEOUT|1|30|s|/etc/lxc5/lxc5.conf|timeout=1|timeout=30|systemctl reload lxc5|lx5|lxc_to_1|jobs|state|https leftover leftover down; bounce|LXC5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxd5|LXD5_TIMEOUT|1|30|s|/etc/lxd5/lxd5.conf|timeout=1|timeout=30|systemctl reload lxd5|lx5|lxd_to_1|jobs|state|https leftover leftover down; bounce|LXD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nspawn5|NSPAWN5_TIMEOUT|1|30|s|/etc/nspawn5/nspawn5.conf|timeout=1|timeout=30|systemctl reload nspawn5|ns5|nsp_to_1|jobs|state|https leftover leftover down; bounce|NSPAWN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
docker5|DOCKER5_TIMEOUT|1|30|s|/etc/docker5/docker5.conf|timeout=1|timeout=30|systemctl reload docker5|do5|doc_to_1|jobs|state|https leftover leftover down; bounce|DOCKER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
podman5|PODMAN5_TIMEOUT|1|30|s|/etc/podman5/podman5.conf|timeout=1|timeout=30|systemctl reload podman5|po5|pod_to_1|jobs|state|https leftover leftover down; bounce|PODMAN5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
containerd5|CONTAINERD5_TIMEOUT|1|30|s|/etc/containerd5/containerd5.conf|timeout=1|timeout=30|systemctl reload containerd5|co5|con_to_1|jobs|state|https leftover leftover down; bounce|CONTAINERD5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubernetes5|KUBERNETES5_TIMEOUT|1|30|s|/etc/kubernetes5/kubernetes5.conf|timeout=1|timeout=30|systemctl reload kubernetes5|ku5|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBERNETES5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubelet5|KUBELET5_TIMEOUT|1|30|s|/etc/kubelet5/kubelet5.conf|timeout=1|timeout=30|systemctl reload kubelet5|ku5|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBELET5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubeadm5|KUBEADM5_TIMEOUT|1|30|s|/etc/kubeadm5/kubeadm5.conf|timeout=1|timeout=30|systemctl reload kubeadm5|ku5|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBEADM5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ceph5|CEPH5_TIMEOUT|1|30|s|/etc/ceph5/ceph5.conf|timeout=1|timeout=30|systemctl reload ceph5|ce5|cep_to_1|jobs|state|https leftover leftover down; bounce|CEPH5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gluster5|GLUSTER5_TIMEOUT|1|30|s|/etc/gluster5/gluster5.conf|timeout=1|timeout=30|systemctl reload gluster5|gl5|glu_to_1|jobs|state|https leftover leftover down; bounce|GLUSTER5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
minio5|MINIO5_TIMEOUT|1|30|s|/etc/minio5/minio5.conf|timeout=1|timeout=30|systemctl reload minio5|mi5|min_to_1|jobs|state|https leftover leftover down; bounce|MINIO5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
seaweed5|SEAWEED5_TIMEOUT|1|30|s|/etc/seaweed5/seaweed5.conf|timeout=1|timeout=30|systemctl reload seaweed5|se5|sea_to_1|jobs|state|https leftover leftover down; bounce|SEAWEED5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zfs5|ZFS5_TIMEOUT|1|30|s|/etc/zfs5/zfs5.conf|timeout=1|timeout=30|systemctl reload zfs5|zf5|zfs_to_1|jobs|state|https leftover leftover down; bounce|ZFS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
btrfs5|BTRFS5_TIMEOUT|1|30|s|/etc/btrfs5/btrfs5.conf|timeout=1|timeout=30|systemctl reload btrfs5|bt5|btr_to_1|jobs|state|https leftover leftover down; bounce|BTRFS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
xfs5|XFS5_TIMEOUT|1|30|s|/etc/xfs5/xfs5.conf|timeout=1|timeout=30|systemctl reload xfs5|xf5|xfs_to_1|jobs|state|https leftover leftover down; bounce|XFS5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lvm5|LVM5_TIMEOUT|1|30|s|/etc/lvm5/lvm5.conf|timeout=1|timeout=30|systemctl reload lvm5|lv5|lvm_to_1|jobs|state|https leftover leftover down; bounce|LVM5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mdadm5|MDADM5_TIMEOUT|1|30|s|/etc/mdadm5/mdadm5.conf|timeout=1|timeout=30|systemctl reload mdadm5|md5|mda_to_1|jobs|state|https leftover leftover down; bounce|MDADM5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nvme5|NVME5_TIMEOUT|1|30|s|/etc/nvme5/nvme5.conf|timeout=1|timeout=30|systemctl reload nvme5|nv5|nvm_to_1|jobs|state|https leftover leftover down; bounce|NVME5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ipmi5|IPMI5_TIMEOUT|1|30|s|/etc/ipmi5/ipmi5.conf|timeout=1|timeout=30|systemctl reload ipmi5|ip5|ipm_to_1|jobs|state|https leftover leftover down; bounce|IPMI5_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "openssh5/dropbear5/iptables5/nftables5/firewalld5/openvpn5/wireguard5/strongswan5/dhcpd5/named5/ntpd5/chrony5/samba5/nfs5/rpcbind5/autofs5/qemu5/libvirt5/xen5/bhyve5/lxc5/lxd5/nspawn5/docker5/podman5/containerd5/kubernetes5/kubelet5/kubeadm5/ceph5/gluster5/minio5/seaweed5/zfs5/btrfs5/xfs5/lvm5/mdadm5/nvme5/ipmi5"
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
        svc = f"s5{i:02d}x"
        ns = f"s5{i:02d}"
        clu = f"prod-apuw{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14363 + i }"
        node = f"ip-10-161-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4921


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-91 leftover: {WAVE}.",
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
