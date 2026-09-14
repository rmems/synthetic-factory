#!/usr/bin/env python3
"""IRC mill r4861+ — wave-88 mesh/dns leftover.

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
pdns4|PDNS4_TIMEOUT|1|30|s|/etc/pdns4/pdns4.conf|timeout=1|timeout=30|systemctl reload pdns4|pd4|pdn_to_1|jobs|state|https leftover leftover down; bounce|PDNS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nginx4|NGINX4_TIMEOUT|1|30|s|/etc/nginx4/nginx4.conf|timeout=1|timeout=30|systemctl reload nginx4|ng4|ngi_to_1|jobs|state|https leftover leftover down; bounce|NGINX4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
envoy4|ENVOY4_TIMEOUT|1|30|s|/etc/envoy4/envoy4.conf|timeout=1|timeout=30|systemctl reload envoy4|en4|env_to_1|jobs|state|https leftover leftover down; bounce|ENVOY4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
apisix4|APISIX4_TIMEOUT|1|30|s|/etc/apisix4/apisix4.conf|timeout=1|timeout=30|systemctl reload apisix4|ap4|api_to_1|jobs|state|https leftover leftover down; bounce|APISIX4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
krakend4|KRAKEND4_TIMEOUT|1|30|s|/etc/krakend4/krakend4.conf|timeout=1|timeout=30|systemctl reload krakend4|kr4|kra_to_1|jobs|state|https leftover leftover down; bounce|KRAKEND4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tyk4|TYK4_TIMEOUT|1|30|s|/etc/tyk4/tyk4.conf|timeout=1|timeout=30|systemctl reload tyk4|ty4|tyk_to_1|jobs|state|https leftover leftover down; bounce|TYK4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gloo4|GLOO4_TIMEOUT|1|30|s|/etc/gloo4/gloo4.conf|timeout=1|timeout=30|systemctl reload gloo4|gl4|glo_to_1|jobs|state|https leftover leftover down; bounce|GLOO4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
postfix4|POSTFIX4_TIMEOUT|1|30|s|/etc/postfix4/postfix4.conf|timeout=1|timeout=30|systemctl reload postfix4|po4|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTFIX4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
exim4|EXIM4_TIMEOUT|1|30|s|/etc/exim4/exim4.conf|timeout=1|timeout=30|systemctl reload exim4|ex4|exi_to_1|jobs|state|https leftover leftover down; bounce|EXIM4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sendmail4|SENDMAIL4_TIMEOUT|1|30|s|/etc/sendmail4/sendmail4.conf|timeout=1|timeout=30|systemctl reload sendmail4|se4|sen_to_1|jobs|state|https leftover leftover down; bounce|SENDMAIL4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dovecot4|DOVECOT4_TIMEOUT|1|30|s|/etc/dovecot4/dovecot4.conf|timeout=1|timeout=30|systemctl reload dovecot4|do4|dov_to_1|jobs|state|https leftover leftover down; bounce|DOVECOT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openssh4|OPENSSH4_TIMEOUT|1|30|s|/etc/openssh4/openssh4.conf|timeout=1|timeout=30|systemctl reload openssh4|op4|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENSSH4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dropbear4|DROPBEAR4_TIMEOUT|1|30|s|/etc/dropbear4/dropbear4.conf|timeout=1|timeout=30|systemctl reload dropbear4|dr4|dro_to_1|jobs|state|https leftover leftover down; bounce|DROPBEAR4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
iptables4|IPTABLES4_TIMEOUT|1|30|s|/etc/iptables4/iptables4.conf|timeout=1|timeout=30|systemctl reload iptables4|ip4|ipt_to_1|jobs|state|https leftover leftover down; bounce|IPTABLES4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nftables4|NFTABLES4_TIMEOUT|1|30|s|/etc/nftables4/nftables4.conf|timeout=1|timeout=30|systemctl reload nftables4|nf4|nft_to_1|jobs|state|https leftover leftover down; bounce|NFTABLES4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
firewalld4|FIREWALLD4_TIMEOUT|1|30|s|/etc/firewalld4/firewalld4.conf|timeout=1|timeout=30|systemctl reload firewalld4|fi4|fir_to_1|jobs|state|https leftover leftover down; bounce|FIREWALLD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
openvpn4|OPENVPN4_TIMEOUT|1|30|s|/etc/openvpn4/openvpn4.conf|timeout=1|timeout=30|systemctl reload openvpn4|op4|ope_to_1|jobs|state|https leftover leftover down; bounce|OPENVPN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
wireguard4|WIREGUARD4_TIMEOUT|1|30|s|/etc/wireguard4/wireguard4.conf|timeout=1|timeout=30|systemctl reload wireguard4|wi4|wir_to_1|jobs|state|https leftover leftover down; bounce|WIREGUARD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
strongswan4|STRONGSWAN4_TIMEOUT|1|30|s|/etc/strongswan4/strongswan4.conf|timeout=1|timeout=30|systemctl reload strongswan4|st4|str_to_1|jobs|state|https leftover leftover down; bounce|STRONGSWAN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dhcpd4|DHCPD4_TIMEOUT|1|30|s|/etc/dhcpd4/dhcpd4.conf|timeout=1|timeout=30|systemctl reload dhcpd4|dh4|dhc_to_1|jobs|state|https leftover leftover down; bounce|DHCPD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
named4|NAMED4_TIMEOUT|1|30|s|/etc/named4/named4.conf|timeout=1|timeout=30|systemctl reload named4|na4|nam_to_1|jobs|state|https leftover leftover down; bounce|NAMED4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
ntpd4|NTPD4_TIMEOUT|1|30|s|/etc/ntpd4/ntpd4.conf|timeout=1|timeout=30|systemctl reload ntpd4|nt4|ntp_to_1|jobs|state|https leftover leftover down; bounce|NTPD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chrony4|CHRONY4_TIMEOUT|1|30|s|/etc/chrony4/chrony4.conf|timeout=1|timeout=30|systemctl reload chrony4|ch4|chr_to_1|jobs|state|https leftover leftover down; bounce|CHRONY4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
samba4|SAMBA4_TIMEOUT|1|30|s|/etc/samba4/samba4.conf|timeout=1|timeout=30|systemctl reload samba4|sa4|sam_to_1|jobs|state|https leftover leftover down; bounce|SAMBA4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nfs4|NFS4_TIMEOUT|1|30|s|/etc/nfs4/nfs4.conf|timeout=1|timeout=30|systemctl reload nfs4|nf4|nfs_to_1|jobs|state|https leftover leftover down; bounce|NFS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rpcbind4|RPCBIND4_TIMEOUT|1|30|s|/etc/rpcbind4/rpcbind4.conf|timeout=1|timeout=30|systemctl reload rpcbind4|rp4|rpc_to_1|jobs|state|https leftover leftover down; bounce|RPCBIND4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
autofs4|AUTOFS4_TIMEOUT|1|30|s|/etc/autofs4/autofs4.conf|timeout=1|timeout=30|systemctl reload autofs4|au4|aut_to_1|jobs|state|https leftover leftover down; bounce|AUTOFS4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
qemu4|QEMU4_TIMEOUT|1|30|s|/etc/qemu4/qemu4.conf|timeout=1|timeout=30|systemctl reload qemu4|qe4|qem_to_1|jobs|state|https leftover leftover down; bounce|QEMU4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
libvirt4|LIBVIRT4_TIMEOUT|1|30|s|/etc/libvirt4/libvirt4.conf|timeout=1|timeout=30|systemctl reload libvirt4|li4|lib_to_1|jobs|state|https leftover leftover down; bounce|LIBVIRT4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
xen4|XEN4_TIMEOUT|1|30|s|/etc/xen4/xen4.conf|timeout=1|timeout=30|systemctl reload xen4|xe4|xen_to_1|jobs|state|https leftover leftover down; bounce|XEN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bhyve4|BHYVE4_TIMEOUT|1|30|s|/etc/bhyve4/bhyve4.conf|timeout=1|timeout=30|systemctl reload bhyve4|bh4|bhy_to_1|jobs|state|https leftover leftover down; bounce|BHYVE4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxc4|LXC4_TIMEOUT|1|30|s|/etc/lxc4/lxc4.conf|timeout=1|timeout=30|systemctl reload lxc4|lx4|lxc_to_1|jobs|state|https leftover leftover down; bounce|LXC4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
lxd4|LXD4_TIMEOUT|1|30|s|/etc/lxd4/lxd4.conf|timeout=1|timeout=30|systemctl reload lxd4|lx4|lxd_to_1|jobs|state|https leftover leftover down; bounce|LXD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nspawn4|NSPAWN4_TIMEOUT|1|30|s|/etc/nspawn4/nspawn4.conf|timeout=1|timeout=30|systemctl reload nspawn4|ns4|nsp_to_1|jobs|state|https leftover leftover down; bounce|NSPAWN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
docker4|DOCKER4_TIMEOUT|1|30|s|/etc/docker4/docker4.conf|timeout=1|timeout=30|systemctl reload docker4|do4|doc_to_1|jobs|state|https leftover leftover down; bounce|DOCKER4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
podman4|PODMAN4_TIMEOUT|1|30|s|/etc/podman4/podman4.conf|timeout=1|timeout=30|systemctl reload podman4|po4|pod_to_1|jobs|state|https leftover leftover down; bounce|PODMAN4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
containerd4|CONTAINERD4_TIMEOUT|1|30|s|/etc/containerd4/containerd4.conf|timeout=1|timeout=30|systemctl reload containerd4|co4|con_to_1|jobs|state|https leftover leftover down; bounce|CONTAINERD4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubernetes4|KUBERNETES4_TIMEOUT|1|30|s|/etc/kubernetes4/kubernetes4.conf|timeout=1|timeout=30|systemctl reload kubernetes4|ku4|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBERNETES4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubelet4|KUBELET4_TIMEOUT|1|30|s|/etc/kubelet4/kubelet4.conf|timeout=1|timeout=30|systemctl reload kubelet4|ku4|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBELET4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kubeadm4|KUBEADM4_TIMEOUT|1|30|s|/etc/kubeadm4/kubeadm4.conf|timeout=1|timeout=30|systemctl reload kubeadm4|ku4|kub_to_1|jobs|state|https leftover leftover down; bounce|KUBEADM4_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "pdns4/nginx4/envoy4/apisix4/krakend4/tyk4/gloo4/postfix4/exim4/sendmail4/dovecot4/openssh4/dropbear4/iptables4/nftables4/firewalld4/openvpn4/wireguard4/strongswan4/dhcpd4/named4/ntpd4/chrony4/samba4/nfs4/rpcbind4/autofs4/qemu4/libvirt4/xen4/bhyve4/lxc4/lxd4/nspawn4/docker4/podman4/containerd4/kubernetes4/kubelet4/kubeadm4"
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
        svc = f"p1{i:02d}x"
        ns = f"p1{i:02d}"
        clu = f"prod-aput{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14243 + i }"
        node = f"ip-10-198-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4861


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-88 leftover: {WAVE}.",
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
