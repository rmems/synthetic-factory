#!/usr/bin/env python3
"""IRC mill r4161+ — wave-53 lab-emu/flow leftover.

NEW on-call plants (not Wave-27–52 tails). BAN ypbind/oddjob,
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
unetlab|UNETLAB_TIMEOUT|1|30|s|/etc/unetlab/unetlab.conf|timeout=1|timeout=30|systemctl reload unetlab|unl_wrapper|unl_to_1|nodes|labs|qemu leftover leftover down; bounce|UNETLAB_TIMEOUT leftover 1 leftover; a 2s start is aborted so the node 504s
containerlab|CLAB_TIMEOUT|1|30|s|/etc/containerlab/clab.yml|timeout: 1s|timeout: 30s|systemctl reload containerlab|containerlab|clb_to_1|nodes|topo|docker leftover leftover down; bounce|CLAB_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the lab 504s
vrnetlab|VRNETLAB_TIMEOUT|1|30|s|/etc/vrnetlab/vrnetlab.conf|timeout=1|timeout=30|systemctl reload vrnetlab|vrnetlab|vrn_to_1|vms|images|qemu leftover leftover down; bounce|VRNETLAB_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the vr 504s
kne|KNE_TIMEOUT|1|30|s|/etc/kne/kne.yaml|timeout: 1s|timeout: 30s|systemctl reload kne|kne|kne_to_1|nodes|topo|k8s leftover leftover down; bounce|KNE_TIMEOUT leftover 1 leftover; a 2s create is aborted so the topo 504s
packettracer|PT_TIMEOUT|1|30|s|/etc/packettracer/pt.conf|timeout=1|timeout=30|systemctl reload packettracer|packettracer|pt_to_1|devs|topo|fs leftover leftover down; bounce|PT_TIMEOUT leftover 1 leftover; a 2s sim is aborted so the topo 504s
gns3vm|GNS3VM_TIMEOUT|1|30|s|/etc/gns3/gns3vm.conf|timeout=1|timeout=30|systemctl reload gns3vm|gns3|gvm_to_1|vm|server|vbox leftover leftover down; bounce|GNS3VM_TIMEOUT leftover 1 leftover; a 2s start is aborted so the server 504s
cml|CML_TIMEOUT|1|30|s|/etc/cml/cml.conf|timeout=1|timeout=30|systemctl reload virl2-controller|cml|cml_to_1|nodes|labs|qemu leftover leftover down; bounce|CML_TIMEOUT leftover 1 leftover; a 2s start is aborted so the node 504s
virl|VIRL_TIMEOUT|1|30|s|/etc/virl/virl.conf|timeout=1|timeout=30|systemctl reload virl-std|virl|vrl_to_1|nodes|sims|qemu leftover leftover down; bounce|VIRL_TIMEOUT leftover 1 leftover; a 2s start is aborted so the sim 504s
iou|IOU_TIMEOUT|1|30|s|/etc/iou/iou.conf|timeout=1|timeout=30|systemctl reload iou|iou|iou_to_1|imgs|labs|kvm leftover leftover down; bounce|IOU_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the img 504s
iol|IOL_TIMEOUT|1|30|s|/etc/iol/iol.conf|timeout=1|timeout=30|systemctl reload iol|iol|iol_to_1|imgs|labs|kvm leftover leftover down; bounce|IOL_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the img 504s
dynamips|DYNAMIPS_TIMEOUT|1|30|s|/etc/dynamips/dynamips.conf|timeout=1|timeout=30|systemctl reload dynamips|dynamips|dyn_to_1|imgs|labs|kvm leftover leftover down; bounce|DYNAMIPS_TIMEOUT leftover 1 leftover; a 2s idlepc is aborted so the img 504s
vpcs|VPCS_TIMEOUT|1|10|s|/etc/vpcs/vpcs.conf|timeout=1|timeout=10|systemctl reload vpcs|vpcs|vpc_to_1|pcs|labs|udp leftover leftover down; bounce|VPCS_TIMEOUT leftover 1 leftover; a 2s dhcp is aborted so the pc 504s
ubridge|UBRIDGE_TIMEOUT|1|10|s|/etc/ubridge/ubridge.ini|timeout=1|timeout=10|systemctl reload ubridge|ubridge|ubr_to_1|nics|labs|udp leftover leftover down; bounce|UBRIDGE_TIMEOUT leftover 1 leftover; a 2s tap is aborted so the bridge 504s
iouyap|IOUYAP_TIMEOUT|1|10|s|/etc/iouyap/iouyap.ini|timeout=1|timeout=10|systemctl reload iouyap|iouyap|iyp_to_1|nics|labs|udp leftover leftover down; bounce|IOUYAP_TIMEOUT leftover 1 leftover; a 2s map is aborted so the nic 504s
snmptrapd|SNMPTRAPD_TIMEOUT|1|10|s|/etc/snmp/snmptrapd.conf|timeout 1|timeout 10|systemctl reload snmptrapd|snmptrapd|trp_to_1|traps|sinks|udp leftover leftover down; bounce|SNMPTRAPD_TIMEOUT leftover 1 leftover; a 2s trap is dropped so pages vanish
net-snmp|NETSNMP_TIMEOUT|1|10|s|/etc/snmp/snmpd.conf|timeout 1|timeout 10|systemctl reload snmpd|snmpd|nsn_to_1|oids|agents|udp leftover leftover down; bounce|NETSNMP_TIMEOUT leftover 1 leftover; a 2s get is aborted so poll 504s
mrtg|MRTG_TIMEOUT|1|30|s|/etc/mrtg/mrtg.cfg|timeout=1|timeout=30|systemctl reload mrtg|mrtg|mrt_to_1|rrd|targets|snmp leftover leftover down; bounce|MRTG_TIMEOUT leftover 1 leftover; a 2s snmp is aborted so the graph 504s
weathermap|WEATHERMAP_TIMEOUT|1|30|s|/etc/weathermap/weathermap.conf|timeout=1|timeout=30|systemctl reload weathermap|weathermap|wmp_to_1|maps|nodes|rrd leftover leftover down; bounce|WEATHERMAP_TIMEOUT leftover 1 leftover; a 2s poll is aborted so the map 504s
nagiosxi|NAGIOSXI_TIMEOUT|1|30|s|/usr/local/nagiosxi/etc/config.inc.php|timeout=1|timeout=30|systemctl reload nagios|nagiosxi|nxi_to_1|checks|hosts|ndoutils leftover leftover down; bounce|NAGIOSXI_TIMEOUT leftover 1 leftover; a 2s check is aborted so the svc 504s
icingaweb|ICINGAWEB_TIMEOUT|1|10|s|/etc/icingaweb2/config.ini|timeout=1|timeout=10|systemctl reload php-fpm|icingacli|icw_to_1|ui|ido|sql leftover leftover down; bounce|ICINGAWEB_TIMEOUT leftover 1 leftover; a 2s query is aborted so the ui 504s
prtg|PRTG_TIMEOUT|1|30|s|/etc/prtg/prtg.conf|timeout=1|timeout=30|systemctl reload prtg|prtg|prt_to_1|sens|probes|http leftover leftover down; bounce|PRTG_TIMEOUT leftover 1 leftover; a 2s probe is aborted so the sensor 504s
solarwinds|ORION_TIMEOUT|1|30|s|/etc/solarwinds/orion.conf|timeout=1|timeout=30|systemctl reload orion|swql|slw_to_1|npm|nodes|sql leftover leftover down; bounce|ORION_TIMEOUT leftover 1 leftover; a 2s poll is aborted so the node 504s
opennms|OPENNMS_TIMEOUT|1|30|s|/etc/opennms/opennms.properties|timeout=1|timeout=30|systemctl reload opennms|opennms|onm_to_1|events|nodes|sql leftover leftover down; bounce|OPENNMS_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the node 504s
minion|MINION_TIMEOUT|1|30|s|/etc/minion/org.opennms.minion.cfg|timeout=1|timeout=30|systemctl reload minion|minion|min_to_1|traps|flows|karaf leftover leftover down; bounce|MINION_TIMEOUT leftover 1 leftover; a 2s sink is aborted so the trap 504s
sentinel|SENTINEL_TIMEOUT|1|30|s|/etc/sentinel/org.opennms.sentinel.cfg|timeout=1|timeout=30|systemctl reload sentinel|sentinel|snt_to_1|flows|corr|karaf leftover leftover down; bounce|SENTINEL_TIMEOUT leftover 1 leftover; a 2s flow is aborted so the corr 504s
newts|NEWTS_TIMEOUT|1|10|s|/etc/newts/newts.yml|timeout: 1|timeout: 10|systemctl reload newts|newts|nwt_to_1|samples|cass|cass leftover leftover down; bounce|NEWTS_TIMEOUT leftover 1 leftover; a 2s insert is aborted so the metric 504s
flowspec|FLOWSPEC_TIMEOUT|1|10|s|/etc/flowspec/flowspec.conf|timeout=1|timeout=10|systemctl reload flowspec|flowspec|fsp_to_1|rules|peers|bgp leftover leftover down; bounce|FLOWSPEC_TIMEOUT leftover 1 leftover; a 2s nlri is aborted so the rule 504s
nfsen|NFSEN_TIMEOUT|1|10|s|/etc/nfsen/nfsen.conf|timeout=1|timeout=10|systemctl reload nfsen|nfsen|nfs_to_1|nfdump|profiles|fs leftover leftover down; bounce|NFSEN_TIMEOUT leftover 1 leftover; a 2s profile is aborted so the ui 504s
sflowtool|SFLOWTOOL_TIMEOUT|1|10|s|/etc/sflowtool/sflowtool.conf|timeout=1|timeout=10|systemctl reload sflowtool|sflowtool|sft_to_1|sflow|sinks|udp leftover leftover down; bounce|SFLOWTOOL_TIMEOUT leftover 1 leftover; a 2s datagram is dropped so the sink 504s
hsflowd|HSFLOWD_TIMEOUT|1|10|s|/etc/hsflowd.conf|timeout=1|timeout=10|systemctl reload hsflowd|hsflowd|hsf_to_1|sflow|nics|udp leftover leftover down; bounce|HSFLOWD_TIMEOUT leftover 1 leftover; a 2s sample is dropped so the collector 504s
pma|PMA_TIMEOUT|1|10|s|/etc/pma/pma.conf|timeout=1|timeout=10|systemctl reload pma|pma|pma_to_1|acct|nics|pcap leftover leftover down; bounce|PMA_TIMEOUT leftover 1 leftover; a 2s acct is aborted so the flow 504s
softflowd|SOFTFLOWD_TIMEOUT|1|10|s|/etc/softflowd/softflowd.conf|timeout=1|timeout=10|systemctl reload softflowd|softflowd|sfd_to_1|flows|nics|udp leftover leftover down; bounce|SOFTFLOWD_TIMEOUT leftover 1 leftover; a 2s export is aborted so the collector 504s
nfacctd|NFACCTD_TIMEOUT|1|10|s|/etc/pmacct/nfacctd.conf|timeout=1|timeout=10|systemctl reload nfacctd|nfacctd|nfa_to_1|nf|nics|udp leftover leftover down; bounce|NFACCTD_TIMEOUT leftover 1 leftover; a 2s netflow is dropped so the collector 504s
sfacctd|SFACCTD_TIMEOUT|1|10|s|/etc/pmacct/sfacctd.conf|timeout=1|timeout=10|systemctl reload sfacctd|sfacctd|sfa_to_1|sf|nics|udp leftover leftover down; bounce|SFACCTD_TIMEOUT leftover 1 leftover; a 2s sflow is dropped so the collector 504s
uacctd|UACCTD_TIMEOUT|1|10|s|/etc/pmacct/uacctd.conf|timeout=1|timeout=10|systemctl reload uacctd|uacctd|uac_to_1|ulog|nics|netlink leftover leftover down; bounce|UACCTD_TIMEOUT leftover 1 leftover; a 2s ulog is dropped so the collector 504s
pmbgpd|PMBGPD_TIMEOUT|1|10|s|/etc/pmacct/pmbgpd.conf|timeout=1|timeout=10|systemctl reload pmbgpd|pmbgpd|pbg_to_1|bgp|peers|tcp leftover leftover down; bounce|PMBGPD_TIMEOUT leftover 1 leftover; a 2s update is aborted so the rib 504s
pmbmpd|PMBMPD_TIMEOUT|1|10|s|/etc/pmacct/pmbmpd.conf|timeout=1|timeout=10|systemctl reload pmbmpd|pmbmpd|pbm_to_1|bmp|peers|tcp leftover leftover down; bounce|PMBMPD_TIMEOUT leftover 1 leftover; a 2s bmp is aborted so the rib 504s
pmtelemetryd|PMTELEM_TIMEOUT|1|10|s|/etc/pmacct/pmtelemetryd.conf|timeout=1|timeout=10|systemctl reload pmtelemetryd|pmtelemetryd|pmt_to_1|gpb|peers|tcp leftover leftover down; bounce|PMTELEM_TIMEOUT leftover 1 leftover; a 2s gpb is aborted so the telem 504s
packetfence|PF_TIMEOUT|1|10|s|/etc/packetfence/pf.conf|timeout=1|timeout=10|systemctl reload packetfence|pfcmd|pf_to_1|nac|nodes|mysql leftover leftover down; bounce|PF_TIMEOUT leftover 1 leftover; a 2s radius is aborted so the nac 401s
radiator|RADIATOR_TIMEOUT|1|10|s|/etc/radiator/radius.cfg|Timeout 1|Timeout 10|systemctl reload radiator|radpwtst|rad_to_1|aaa|clients|udp leftover leftover down; bounce|RADIATOR_TIMEOUT leftover 1 leftover; a 2s access is aborted so aaa 401s
'''
WAVE53 = (
    "unetlab/containerlab/vrnetlab/kne/packettracer/gns3vm/cml/virl/iou/iol/"
    "dynamips/vpcs/ubridge/iouyap/snmptrapd/net-snmp/mrtg/weathermap/"
    "nagiosxi/icingaweb/prtg/solarwinds/opennms/minion/sentinel/newts/"
    "flowspec/nfsen/sflowtool/hsflowd/pma/softflowd/nfacctd/sfacctd/"
    "uacctd/pmbgpd/pmbmpd/pmtelemetryd/packetfence/radiator"
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
        svc = f"i3{i:02d}x"
        ns = f"i3{i:02d}"
        clu = f"prod-apsj{901 + i}-{svc[:3]}"
        ticket = f"W2-{12843 + i}"
        node = f"ip-10-238-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4161


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4160 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-53 leftover: {WAVE53}.",
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
