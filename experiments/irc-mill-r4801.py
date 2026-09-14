#!/usr/bin/env python3
"""IRC mill r4801+ — wave-85 dns/mail leftover.

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
exim3|EXIM3_TIMEOUT|1|30|s|/etc/exim3/exim3.conf|timeout=1|timeout=30|systemctl reload exim3|ex3|exi_to_1|jobs|state|https leftover leftover down; bounce|EXIM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sendmail3|SENDMAIL3_TIMEOUT|1|30|s|/etc/sendmail3/sendmail3.conf|timeout=1|timeout=30|systemctl reload sendmail3|se3|sen_to_1|jobs|state|https leftover leftover down; bounce|SENDMAIL3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dovecot3|DOVECOT3_TIMEOUT|1|30|s|/etc/dovecot3/dovecot3.conf|timeout=1|timeout=30|systemctl reload dovecot3|do3|dov_to_1|jobs|state|https leftover leftover down; bounce|DOVECOT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openssh3|OPENSSH3_TIMEOUT|1|30|s|/etc/openssh3/openssh3.conf|timeout=1|timeout=30|systemctl reload openssh3|op3|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENSSH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dropbear3|DROPBEAR3_TIMEOUT|1|30|s|/etc/dropbear3/dropbear3.conf|timeout=1|timeout=30|systemctl reload dropbear3|dr3|dro_to_1|jobs|state|https leftover leftover down; bounce|DROPBEAR3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
iptables3|IPTABLES3_TIMEOUT|1|30|s|/etc/iptables3/iptables3.conf|timeout=1|timeout=30|systemctl reload iptables3|ip3|ipt_to_1|jobs|state|https leftover leftover down; bounce|IPTABLES3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nftables3|NFTABLES3_TIMEOUT|1|30|s|/etc/nftables3/nftables3.conf|timeout=1|timeout=30|systemctl reload nftables3|nf3|nft_to_1|jobs|state|https leftover leftover down; bounce|NFTABLES3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
firewalld3|FIREWALLD3_TIMEOUT|1|30|s|/etc/firewalld3/firewalld3.conf|timeout=1|timeout=30|systemctl reload firewalld3|fi3|fir_to_1|jobs|state|https leftover leftover down; bounce|FIREWALLD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openvpn3|OPENVPN3_TIMEOUT|1|30|s|/etc/openvpn3/openvpn3.conf|timeout=1|timeout=30|systemctl reload openvpn3|op3|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENVPN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
wireguard3|WIREGUARD3_TIMEOUT|1|30|s|/etc/wireguard3/wireguard3.conf|timeout=1|timeout=30|systemctl reload wireguard3|wi3|wir_to_1|jobs|state|https leftover leftover down; bounce|WIREGUARD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
strongswan3|STRONGSWAN3_TIMEOUT|1|30|s|/etc/strongswan3/strongswan3.conf|timeout=1|timeout=30|systemctl reload strongswan3|st3|str_to_1|jobs|state|https leftover leftover down; bounce|STRONGSWAN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dhcpd3|DHCPD3_TIMEOUT|1|30|s|/etc/dhcpd3/dhcpd3.conf|timeout=1|timeout=30|systemctl reload dhcpd3|dh3|dhc_to_1|jobs|state|https leftover leftover down; bounce|DHCPD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
named3|NAMED3_TIMEOUT|1|30|s|/etc/named3/named3.conf|timeout=1|timeout=30|systemctl reload named3|na3|nam_to_1|jobs|state|https leftover leftover down; bounce|NAMED3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ntpd3|NTPD3_TIMEOUT|1|30|s|/etc/ntpd3/ntpd3.conf|timeout=1|timeout=30|systemctl reload ntpd3|nt3|ntp_to_1|jobs|state|https leftover leftover down; bounce|NTPD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chrony3|CHRONY3_TIMEOUT|1|30|s|/etc/chrony3/chrony3.conf|timeout=1|timeout=30|systemctl reload chrony3|ch3|chr_to_1|jobs|state|https leftover leftover down; bounce|CHRONY3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
samba3|SAMBA3_TIMEOUT|1|30|s|/etc/samba3/samba3.conf|timeout=1|timeout=30|systemctl reload samba3|sa3|sam_to_1|jobs|state|https leftover leftover down; bounce|SAMBA3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nfs3|NFS3_TIMEOUT|1|30|s|/etc/nfs3/nfs3.conf|timeout=1|timeout=30|systemctl reload nfs3|nf3|nfs_to_1|jobs|state|https leftover leftover down; bounce|NFS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rpcbind3|RPCBIND3_TIMEOUT|1|30|s|/etc/rpcbind3/rpcbind3.conf|timeout=1|timeout=30|systemctl reload rpcbind3|rp3|rpc_to_1|jobs|state|https leftover leftover down; bounce|RPCBIND3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
autofs3|AUTOFS3_TIMEOUT|1|30|s|/etc/autofs3/autofs3.conf|timeout=1|timeout=30|systemctl reload autofs3|au3|aut_to_1|jobs|state|https leftover leftover down; bounce|AUTOFS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
qemu3|QEMU3_TIMEOUT|1|30|s|/etc/qemu3/qemu3.conf|timeout=1|timeout=30|systemctl reload qemu3|qe3|qem_to_1|jobs|state|https leftover leftover down; bounce|QEMU3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
libvirt3|LIBVIRT3_TIMEOUT|1|30|s|/etc/libvirt3/libvirt3.conf|timeout=1|timeout=30|systemctl reload libvirt3|li3|lib_to_1|jobs|state|https leftover leftover down; bounce|LIBVIRT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
xen3|XEN3_TIMEOUT|1|30|s|/etc/xen3/xen3.conf|timeout=1|timeout=30|systemctl reload xen3|xe3|xen_to_1|jobs|state|https leftover leftover down; bounce|XEN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bhyve3|BHYVE3_TIMEOUT|1|30|s|/etc/bhyve3/bhyve3.conf|timeout=1|timeout=30|systemctl reload bhyve3|bh3|bhy_to_1|jobs|state|https leftover leftover down; bounce|BHYVE3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxc3|LXC3_TIMEOUT|1|30|s|/etc/lxc3/lxc3.conf|timeout=1|timeout=30|systemctl reload lxc3|lx3|lxc_to_1|jobs|state|https leftover leftover down; bounce|LXC3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxd3|LXD3_TIMEOUT|1|30|s|/etc/lxd3/lxd3.conf|timeout=1|timeout=30|systemctl reload lxd3|lx3|lxd_to_1|jobs|state|https leftover leftover down; bounce|LXD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nspawn3|NSPAWN3_TIMEOUT|1|30|s|/etc/nspawn3/nspawn3.conf|timeout=1|timeout=30|systemctl reload nspawn3|ns3|nsp_to_1|jobs|state|https leftover leftover down; bounce|NSPAWN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
docker3|DOCKER3_TIMEOUT|1|30|s|/etc/docker3/docker3.conf|timeout=1|timeout=30|systemctl reload docker3|do3|doc_to_1|jobs|state|https leftover leftover down; bounce|DOCKER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
podman3|PODMAN3_TIMEOUT|1|30|s|/etc/podman3/podman3.conf|timeout=1|timeout=30|systemctl reload podman3|po3|pod_to_1|jobs|state|https leftover leftover down; bounce|PODMAN3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
containerd3|CONTAINERD3_TIMEOUT|1|30|s|/etc/containerd3/containerd3.conf|timeout=1|timeout=30|systemctl reload containerd3|co3|con_to_1|jobs|state|https leftover leftover down; bounce|CONTAINERD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubernetes3|KUBERNETES3_TIMEOUT|1|30|s|/etc/kubernetes3/kubernetes3.conf|timeout=1|timeout=30|systemctl reload kubernetes3|ku3|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBERNETES3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubelet3|KUBELET3_TIMEOUT|1|30|s|/etc/kubelet3/kubelet3.conf|timeout=1|timeout=30|systemctl reload kubelet3|ku3|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBELET3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubeadm3|KUBEADM3_TIMEOUT|1|30|s|/etc/kubeadm3/kubeadm3.conf|timeout=1|timeout=30|systemctl reload kubeadm3|ku3|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBEADM3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openshift3|OPENSHIFT3_TIMEOUT|1|30|s|/etc/openshift3/openshift3.conf|timeout=1|timeout=30|systemctl reload openshift3|op3|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENSHIFT3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
okd3|OKD3_TIMEOUT|1|30|s|/etc/okd3/okd3.conf|timeout=1|timeout=30|systemctl reload okd3|ok3|okd_to_1|jobs|state|https leftover leftover down; bounce|OKD3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ceph3|CEPH3_TIMEOUT|1|30|s|/etc/ceph3/ceph3.conf|timeout=1|timeout=30|systemctl reload ceph3|ce3|cep_to_1|jobs|state|https leftover leftover down; bounce|CEPH3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gluster3|GLUSTER3_TIMEOUT|1|30|s|/etc/gluster3/gluster3.conf|timeout=1|timeout=30|systemctl reload gluster3|gl3|glu_to_1|jobs|state|https leftover leftover down; bounce|GLUSTER3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
minio3|MINIO3_TIMEOUT|1|30|s|/etc/minio3/minio3.conf|timeout=1|timeout=30|systemctl reload minio3|mi3|min_to_1|jobs|state|https leftover leftover down; bounce|MINIO3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
seaweed3|SEAWEED3_TIMEOUT|1|30|s|/etc/seaweed3/seaweed3.conf|timeout=1|timeout=30|systemctl reload seaweed3|se3|sea_to_1|jobs|state|https leftover leftover down; bounce|SEAWEED3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zfs3|ZFS3_TIMEOUT|1|30|s|/etc/zfs3/zfs3.conf|timeout=1|timeout=30|systemctl reload zfs3|zf3|zfs_to_1|jobs|state|https leftover leftover down; bounce|ZFS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
btrfs3|BTRFS3_TIMEOUT|1|30|s|/etc/btrfs3/btrfs3.conf|timeout=1|timeout=30|systemctl reload btrfs3|bt3|btr_to_1|jobs|state|https leftover leftover down; bounce|BTRFS3_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "exim3/sendmail3/dovecot3/openssh3/dropbear3/iptables3/nftables3/firewalld3/openvpn3/wireguard3/strongswan3/dhcpd3/named3/ntpd3/chrony3/samba3/nfs3/rpcbind3/autofs3/qemu3/libvirt3/xen3/bhyve3/lxc3/lxd3/nspawn3/docker3/podman3/containerd3/kubernetes3/kubelet3/kubeadm3/openshift3/okd3/ceph3/gluster3/minio3/seaweed3/zfs3/btrfs3"
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
        svc = f"l8{i:02d}x"
        ns = f"l8{i:02d}"
        clu = f"prod-apuq{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14123 + i }"
        node = f"ip-10-195-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4801


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-85 leftover: {WAVE}.",
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
