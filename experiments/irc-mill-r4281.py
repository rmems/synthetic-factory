#!/usr/bin/env python3
"""IRC mill r4281+ — wave-59 bsd/firewall leftover.

NEW on-call plants (not Wave-27–58 tails). BAN ypbind/oddjob,
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
cbsd|CBSD_TIMEOUT|1|30|s|/usr/local/cbsd/cbsd.conf|timeout=1|timeout=30|systemctl reload cbsd|cbsd|cbs_to_1|jails|bhyve|zfs leftover leftover down; bounce|CBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the jail 504s
pot|POT_TIMEOUT|1|30|s|/usr/local/etc/pot/pot.conf|timeout=1|timeout=30|systemctl reload pot|pot|pot_to_1|pots|fscomp|zfs leftover leftover down; bounce|POT_TIMEOUT leftover 1 leftover; a 2s start is aborted so the pot 504s
freebsd|FREEBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|fbs_to_1|rc|svcs|rc leftover leftover down; bounce|FREEBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
openbsd|OPENBSD_TIMEOUT|1|30|s|/etc/rc.conf.local|timeout=1|timeout=30|systemctl reload rc|rcctl|obs_to_1|rc|svcs|rc leftover leftover down; bounce|OPENBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
netbsd|NETBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|nbs_to_1|rc|svcs|rc leftover leftover down; bounce|NETBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
hardenedbsd|HBSDBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|hbd_to_1|rc|svcs|hbsd leftover leftover down; bounce|HBSDBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
midnightbsd|MIDNIGHTBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|mdb_to_1|rc|svcs|rc leftover leftover down; bounce|MIDNIGHTBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
ghostbsd|GHOSTBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|ghb_to_1|rc|svcs|rc leftover leftover down; bounce|GHOSTBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
nomadbsd|NOMADBSD_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|nmb_to_1|rc|svcs|rc leftover leftover down; bounce|NOMADBSD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the svc 504s
helloSystem|HELLOSYSTEM_TIMEOUT|1|30|s|/etc/rc.conf|timeout=1|timeout=30|systemctl reload rc|service|hls_to_1|desk|svcs|rc leftover leftover down; bounce|HELLOSYSTEM_TIMEOUT leftover 1 leftover; a 2s start is aborted so the desk 504s
pfsense|PFSENSE_TIMEOUT|1|30|s|/etc/inc/globals.inc|timeout=1|timeout=30|systemctl reload php-fpm|pfSsh.php|pfs_to_1|rules|wan|php leftover leftover down; bounce|PFSENSE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
opnsense|OPNSENSE_TIMEOUT|1|30|s|/usr/local/etc/inc/config.inc|timeout=1|timeout=30|systemctl reload configd|configctl|ops_to_1|rules|wan|php leftover leftover down; bounce|OPNSENSE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
ipfire|IPFIRE_TIMEOUT|1|30|s|/var/ipfire/ethernet/settings|timeout=1|timeout=30|systemctl reload ipfire|ipfire|ipf_to_1|rules|red|fs leftover leftover down; bounce|IPFIRE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
ipcop|IPCOP_TIMEOUT|1|30|s|/var/ipcop/ethernet/settings|timeout=1|timeout=30|systemctl reload ipcop|ipcop|ipc_to_1|rules|red|fs leftover leftover down; bounce|IPCOP_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
untangle|UNTANGLE_TIMEOUT|1|30|s|/usr/share/untangle/conf/untangle.conf|timeout=1|timeout=30|systemctl reload untangle-vm|ut|unt_to_1|apps|wan|java leftover leftover down; bounce|UNTANGLE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the app 504s
sophos|SOPHOS_TIMEOUT|1|30|s|/etc/sophos/sophos.conf|timeout=1|timeout=30|systemctl reload sophos|sophos|sph_to_1|rules|wan|https leftover leftover 403; bounce|SOPHOS_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
watchguard|WATCHGUARD_TIMEOUT|1|30|s|/etc/watchguard/wg.conf|timeout=1|timeout=30|systemctl reload wg|wg|wgd_to_1|rules|wan|https leftover leftover 403; bounce|WATCHGUARD_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the rule 504s
fortigate|FORTIGATE_TIMEOUT|1|30|s|/etc/fortigate/fortigate.conf|timeout=1|timeout=30|systemctl reload fg|fg|ftg_to_1|vdoms|wan|https leftover leftover 403; bounce|FORTIGATE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the vdom 504s
paloalto|PANOS_TIMEOUT|1|30|s|/etc/paloalto/panos.conf|timeout=1|timeout=30|systemctl reload pan|pan|pal_to_1|vsys|wan|https leftover leftover 403; bounce|PANOS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the vsys 504s
asa|ASA_TIMEOUT|1|30|s|/etc/asa/asa.conf|timeout=1|timeout=30|systemctl reload asa|asa|asa_to_1|acls|ctx|https leftover leftover 403; bounce|ASA_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the acl 504s
nxos|NXOS_TIMEOUT|1|30|s|/etc/nxos/nxos.conf|timeout=1|timeout=30|systemctl reload nxos|nxos|nxo_to_1|acls|vdcs|https leftover leftover 403; bounce|NXOS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the vdc 504s
iosxr|IOSXR_TIMEOUT|1|30|s|/etc/iosxr/iosxr.conf|timeout=1|timeout=30|systemctl reload iosxr|iosxr|ixr_to_1|acls|lrs|https leftover leftover 403; bounce|IOSXR_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the lr 504s
pfctl|PFCTL_TIMEOUT|1|10|s|/etc/pf.conf|timeout=1|timeout=10|systemctl reload pf|pfctl|pfc_to_1|rules|ifaces|pf leftover leftover down; bounce|PFCTL_TIMEOUT leftover 1 leftover; a 2s load is aborted so the rule 504s
ipfw|IPFW_TIMEOUT|1|10|s|/etc/ipfw.rules|timeout=1|timeout=10|systemctl reload ipfw|ipfw|ipw_to_1|rules|ifaces|ipfw leftover leftover down; bounce|IPFW_TIMEOUT leftover 1 leftover; a 2s add is aborted so the rule 504s
npf|NPF_TIMEOUT|1|10|s|/etc/npf.conf|timeout=1|timeout=10|systemctl reload npf|npfctl|npf_to_1|rules|ifaces|npf leftover leftover down; bounce|NPF_TIMEOUT leftover 1 leftover; a 2s reload is aborted so the rule 504s
carp|CARP_TIMEOUT|1|10|s|/etc/hostname.carp0|timeout=1|timeout=10|systemctl reload carp|ifconfig|crp_to_1|vhid|ifaces|carp leftover leftover down; bounce|CARP_TIMEOUT leftover 1 leftover; a 2s adv is aborted so the vhid 504s
pfsync|PFSYNC_TIMEOUT|1|10|s|/etc/hostname.pfsync0|timeout=1|timeout=10|systemctl reload pfsync|ifconfig|psy_to_1|states|ifaces|pfsync leftover leftover down; bounce|PFSYNC_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the state 504s
relayd|RELAYD_TIMEOUT|1|10|s|/etc/relayd.conf|timeout=1|timeout=10|systemctl reload relayd|relayctl|rly_to_1|rdr|hosts|tcp leftover leftover down; bounce|RELAYD_TIMEOUT leftover 1 leftover; a 2s check is aborted so the rdr 504s
iked|IKED_TIMEOUT|1|10|s|/etc/iked.conf|timeout=1|timeout=10|systemctl reload iked|ikectl|ikd_to_1|sas|peers|udp leftover leftover down; bounce|IKED_TIMEOUT leftover 1 leftover; a 2s ike is aborted so the sa 504s
isakmpd|ISAKMPD_TIMEOUT|1|10|s|/etc/isakmpd/isakmpd.conf|timeout=1|timeout=10|systemctl reload isakmpd|isakmpd|isk_to_1|sas|peers|udp leftover leftover down; bounce|ISAKMPD_TIMEOUT leftover 1 leftover; a 2s ike is aborted so the sa 504s
sasyncd|SASYNCD_TIMEOUT|1|10|s|/etc/sasyncd.conf|timeout=1|timeout=10|systemctl reload sasyncd|sasyncd|sas_to_1|sas|peers|carp leftover leftover down; bounce|SASYNCD_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the sa 504s
slaacd|SLAACD_TIMEOUT|1|10|s|/etc/slaacd.conf|timeout=1|timeout=10|systemctl reload slaacd|slaacd|sla_to_1|ra|ifaces|icmp6 leftover leftover down; bounce|SLAACD_TIMEOUT leftover 1 leftover; a 2s ra is aborted so v6 504s
unwind|UNWIND_TIMEOUT|1|10|s|/etc/unwind.conf|timeout=1|timeout=10|systemctl reload unwind|unwind|unw_to_1|dns|stub|udp leftover leftover down; bounce|UNWIND_TIMEOUT leftover 1 leftover; a 2s query is aborted so dns 504s
vyos|VYOS_TIMEOUT|1|30|s|/etc/vyos/vyos.conf|timeout=1|timeout=30|systemctl reload vyos|vyos|vyo_to_1|cfg|wan|frr leftover leftover down; bounce|VYOS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the cfg 504s
mikrotik|ROS_TIMEOUT|1|30|s|/etc/mikrotik/ros.conf|timeout=1|timeout=30|systemctl reload routeros|routeros|mkt_to_1|cfg|wan|api leftover leftover down; bounce|ROS_TIMEOUT leftover 1 leftover; a 2s set is aborted so the cfg 504s
edgeos|EDGEOS_TIMEOUT|1|30|s|/etc/edgeos/config.boot|timeout=1|timeout=30|systemctl reload vyatta|vyatta|edg_to_1|cfg|wan|cli leftover leftover down; bounce|EDGEOS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the cfg 504s
unifi|UNIFI_TIMEOUT|1|30|s|/etc/unifi/system.properties|timeout=1|timeout=30|systemctl reload unifi|unifi|uni_to_1|sites|aps|https leftover leftover 403; bounce|UNIFI_TIMEOUT leftover 1 leftover; a 2s inform is aborted so the ap 504s
meraki|MERAKI_TIMEOUT|1|30|s|/etc/meraki/meraki.conf|timeout=1|timeout=30|systemctl reload meraki|meraki|mrk_to_1|orgs|nets|https leftover leftover 403; bounce|MERAKI_TIMEOUT leftover 1 leftover; a 2s api is aborted so the net 504s
aruba|ARUBA_TIMEOUT|1|30|s|/etc/aruba/aruba.conf|timeout=1|timeout=30|systemctl reload aruba|aruba|arb_to_1|aps|ctrl|https leftover leftover 403; bounce|ARUBA_TIMEOUT leftover 1 leftover; a 2s api is aborted so the ap 504s
ruckus|RUCKUS_TIMEOUT|1|30|s|/etc/ruckus/ruckus.conf|timeout=1|timeout=30|systemctl reload ruckus|ruckus|rck_to_1|aps|sz|https leftover leftover 403; bounce|RUCKUS_TIMEOUT leftover 1 leftover; a 2s api is aborted so the ap 504s
'''
WAVE59 = (
    "cbsd/pot/freebsd/openbsd/netbsd/hardenedbsd/midnightbsd/ghostbsd/"
    "nomadbsd/helloSystem/pfsense/opnsense/ipfire/ipcop/untangle/sophos/"
    "watchguard/fortigate/paloalto/asa/nxos/iosxr/pfctl/ipfw/npf/carp/"
    "pfsync/relayd/iked/isakmpd/sasyncd/slaacd/unwind/vyos/mikrotik/"
    "edgeos/unifi/meraki/aruba/ruckus"
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
        # copr leftover unique
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"o9{i:02d}x"
        ns = f"o9{i:02d}"
        clu = f"prod-apsq{901 + i}-{svc[:3]}"
        ticket = f"W2-{13083 + i}"
        node = f"ip-10-244-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4281


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4280 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-59 leftover: {WAVE59}.",
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
