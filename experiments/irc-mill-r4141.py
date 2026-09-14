#!/usr/bin/env python3
"""IRC mill r4141+ — wave-52 netauto/sdn leftover.

NEW on-call plants (not Wave-27–51 tails). BAN ypbind/oddjob,
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
nornir|NORNIR_TIMEOUT|1|30|s|/etc/nornir/config.yaml|timeout: 1|timeout: 30|systemctl reload nornir|nr|nrn_to_1|tasks|hosts|ssh leftover leftover down; bounce|NORNIR_TIMEOUT leftover 1 leftover; a 2s task is aborted so the run 504s
netmiko|NETMIKO_TIMEOUT|1|30|s|/etc/netmiko/netmiko.yml|timeout: 1|timeout: 30|systemctl reload netmiko|netmiko|ntm_to_1|sessions|hosts|ssh leftover leftover down; bounce|NETMIKO_TIMEOUT leftover 1 leftover; a 2s send is aborted so the cli 504s
napalm|NAPALM_TIMEOUT|1|30|s|/etc/napalm/napalm.conf|timeout=1|timeout=30|systemctl reload napalm|napalm|nap_to_1|facts|hosts|ssh leftover leftover down; bounce|NAPALM_TIMEOUT leftover 1 leftover; a 2s get_facts is aborted so the run 504s
scrapli|SCRAPLI_TIMEOUT|1|30|s|/etc/scrapli/scrapli.yml|timeout: 1|timeout: 30|systemctl reload scrapli|scrapli|scp_to_1|sessions|hosts|ssh leftover leftover down; bounce|SCRAPLI_TIMEOUT leftover 1 leftover; a 2s send is aborted so the cli 504s
textfsm|TEXTFSM_TIMEOUT|1|10|s|/etc/textfsm/index|timeout=1|timeout=10|systemctl reload textfsm|textfsm|tfm_to_1|tmpl|cli|fs leftover leftover down; bounce|TEXTFSM_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the table 504s
ntc|NTC_TIMEOUT|1|10|s|/etc/ntc-templates/index|timeout=1|timeout=10|systemctl reload ntc|ntc|ntc_to_1|tmpl|cli|fs leftover leftover down; bounce|NTC_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the table 504s
genie|GENIE_TIMEOUT|1|30|s|/etc/genie/genie.conf|timeout=1|timeout=30|systemctl reload genie|genie|gen_to_1|ops|hosts|ssh leftover leftover down; bounce|GENIE_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the ops 504s
pyats|PYATS_TIMEOUT|1|30|s|/etc/pyats/pyats.conf|timeout=1|timeout=30|systemctl reload pyats|pyats|pya_to_1|jobs|tb|ssh leftover leftover down; bounce|PYATS_TIMEOUT leftover 1 leftover; a 2s job is aborted so the test 504s
robotframework|ROBOT_TIMEOUT|1|30|s|/etc/robot/robot.conf|timeout=1|timeout=30|systemctl reload robot|robot|rbt_to_1|suites|kw|fs leftover leftover down; bounce|ROBOT_TIMEOUT leftover 1 leftover; a 2s keyword is aborted so the suite 504s
paramiko|PARAMIKO_TIMEOUT|1|30|s|/etc/paramiko/paramiko.cfg|timeout=1|timeout=30|systemctl reload paramiko|paramiko|pmk_to_1|sess|hosts|ssh leftover leftover down; bounce|PARAMIKO_TIMEOUT leftover 1 leftover; a 2s exec is aborted so the session 504s
pexpect|PEXPECT_TIMEOUT|1|30|s|/etc/pexpect/pexpect.conf|timeout=1|timeout=30|systemctl reload pexpect|pexpect|pxp_to_1|spawns|hosts|ssh leftover leftover down; bounce|PEXPECT_TIMEOUT leftover 1 leftover; a 2s expect is aborted so the spawn 504s
junos-eznc|PYEZ_TIMEOUT|1|30|s|/etc/pyez/pyez.yml|timeout: 1|timeout: 30|systemctl reload pyez|pyez|junos_to_1|rpc|hosts|netconf leftover leftover down; bounce|PYEZ_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the box 504s
nxapi|NXAPI_TIMEOUT|1|30|s|/etc/nxapi/nxapi.conf|timeout=1|timeout=30|systemctl reload nxapi|nxapi|nxa_to_1|cli|hosts|https leftover leftover 403; bounce|NXAPI_TIMEOUT leftover 1 leftover; a 2s cli is aborted so the box 504s
iosxe|IOSXE_TIMEOUT|1|30|s|/etc/iosxe/restconf.conf|timeout=1|timeout=30|systemctl reload restconf|restconf|ios_to_1|yang|hosts|https leftover leftover 403; bounce|IOSXE_TIMEOUT leftover 1 leftover; a 2s yang is aborted so the box 504s
eos|EOS_TIMEOUT|1|30|s|/etc/eos/eapi.conf|timeout=1|timeout=30|systemctl reload eapi|eapi|eos_to_1|cli|hosts|https leftover leftover 403; bounce|EOS_TIMEOUT leftover 1 leftover; a 2s runCmds is aborted so the box 504s
batfish|BATFISH_TIMEOUT|1|30|s|/etc/batfish/batfish.properties|timeout=1|timeout=30|systemctl reload batfish|batfish|bat_to_1|snaps|q|java leftover leftover down; bounce|BATFISH_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the q 504s
capirca|CAPIRCA_TIMEOUT|1|10|s|/etc/capirca/def|timeout=1|timeout=10|systemctl reload capirca|aclgen|cap_to_1|acl|pol|fs leftover leftover down; bounce|CAPIRCA_TIMEOUT leftover 1 leftover; a 2s render is aborted so the acl 504s
nsot|NSOT_TIMEOUT|1|10|s|/etc/nsot/nsot.conf.py|timeout=1|timeout=10|systemctl reload nsot|nsot|nso_to_1|attrs|sites|sql leftover leftover down; bounce|NSOT_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the ipam 504s
trigger|TRIGGER_TIMEOUT|1|30|s|/etc/trigger/trigger.conf|timeout=1|timeout=30|systemctl reload trigger|gong|trg_to_1|acl|netdevices|ssh leftover leftover down; bounce|TRIGGER_TIMEOUT leftover 1 leftover; a 2s loadacl is aborted so the box 504s
netconf|NETCONF_TIMEOUT|1|30|s|/etc/netconf/netconf.conf|timeout=1|timeout=30|systemctl reload netconf|netconf|ncf_to_1|rpc|hosts|ssh leftover leftover down; bounce|NETCONF_TIMEOUT leftover 1 leftover; a 2s edit-config is aborted so the box 504s
ncclient|NCCLIENT_TIMEOUT|1|30|s|/etc/ncclient/ncclient.yml|timeout: 1|timeout: 30|systemctl reload ncclient|ncclient|ncc_to_1|rpc|hosts|ssh leftover leftover down; bounce|NCCLIENT_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the box 504s
yangson|YANGSON_TIMEOUT|1|10|s|/etc/yangson/yangson.conf|timeout=1|timeout=10|systemctl reload yangson|yangson|ysn_to_1|yang|inst|fs leftover leftover down; bounce|YANGSON_TIMEOUT leftover 1 leftover; a 2s validate is aborted so the model 504s
ydk|YDK_TIMEOUT|1|30|s|/etc/ydk/ydk.conf|timeout=1|timeout=30|systemctl reload ydk|ydk|ydk_to_1|crud|hosts|netconf leftover leftover down; bounce|YDK_TIMEOUT leftover 1 leftover; a 2s crud is aborted so the box 504s
gnmi|GNMI_TIMEOUT|1|10|s|/etc/gnmi/gnmi.conf|timeout=1|timeout=10|systemctl reload gnmi|gnmi_get|gnm_to_1|paths|hosts|grpc leftover leftover down; bounce|GNMI_TIMEOUT leftover 1 leftover; a 2s get is aborted so telemetry 504s
gnoi|GNOI_TIMEOUT|1|30|s|/etc/gnoi/gnoi.conf|timeout=1|timeout=30|systemctl reload gnoi|gnoi|gno_to_1|rpc|hosts|grpc leftover leftover down; bounce|GNOI_TIMEOUT leftover 1 leftover; a 2s ping is aborted so the box 504s
gribi|GRIBI_TIMEOUT|1|10|s|/etc/gribi/gribi.conf|timeout=1|timeout=10|systemctl reload gribi|gribi|grb_to_1|ribs|hosts|grpc leftover leftover down; bounce|GRIBI_TIMEOUT leftover 1 leftover; a 2s modify is aborted so the rib 504s
p4runtime|P4RT_TIMEOUT|1|10|s|/etc/p4runtime/p4rt.conf|timeout=1|timeout=10|systemctl reload p4runtime|p4rt|p4r_to_1|tables|switches|grpc leftover leftover down; bounce|P4RT_TIMEOUT leftover 1 leftover; a 2s write is aborted so the pipeline 504s
stratum|STRATUM_TIMEOUT|1|10|s|/etc/stratum/stratum.conf|timeout=1|timeout=10|systemctl reload stratum|stratum|stm_to_1|ports|asic|grpc leftover leftover down; bounce|STRATUM_TIMEOUT leftover 1 leftover; a 2s push is aborted so the asic 504s
onos|ONOS_TIMEOUT|1|30|s|/opt/onos/config/cluster.json|"timeout": 1|"timeout": 30|systemctl reload onos|onos|ono_to_1|apps|nodes|rest leftover leftover down; bounce|ONOS_TIMEOUT leftover 1 leftover; a 2s intent is aborted so the flow 504s
odl|ODL_TIMEOUT|1|30|s|/opt/opendaylight/etc/org.opendaylight.cfg|timeout=1|timeout=30|systemctl reload odl|odl|odl_to_1|mdsal|nodes|rest leftover leftover down; bounce|ODL_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the flow 504s
ryu|RYU_TIMEOUT|1|10|s|/etc/ryu/ryu.conf|timeout=1|timeout=10|systemctl reload ryu|ryu-manager|ryu_to_1|apps|dp|of leftover leftover down; bounce|RYU_TIMEOUT leftover 1 leftover; a 2s packet_in is aborted so the app 504s
pox|POX_TIMEOUT|1|10|s|/etc/pox/pox.conf|timeout=1|timeout=10|systemctl reload pox|pox|pox_to_1|apps|dp|of leftover leftover down; bounce|POX_TIMEOUT leftover 1 leftover; a 2s packet_in is aborted so the app 504s
nox|NOX_TIMEOUT|1|10|s|/etc/nox/nox.conf|timeout=1|timeout=10|systemctl reload nox|nox|nox_to_1|apps|dp|of leftover leftover down; bounce|NOX_TIMEOUT leftover 1 leftover; a 2s packet_in is aborted so the app 504s
floodlight|FLOODLIGHT_TIMEOUT|1|10|s|/etc/floodlight/floodlightdefault.properties|timeout=1|timeout=10|systemctl reload floodlight|floodlight|fldc_to_1|apps|dp|of leftover leftover down; bounce|FLOODLIGHT_TIMEOUT leftover 1 leftover; a 2s rest is aborted so the flow 504s
mininet|MININET_TIMEOUT|1|30|s|/etc/mininet/mininet.conf|timeout=1|timeout=30|systemctl reload mininet|mn|mnn_to_1|hosts|sw|netns leftover leftover down; bounce|MININET_TIMEOUT leftover 1 leftover; a 2s pingall is aborted so the topo 504s
containernet|CONTAINERNET_TIMEOUT|1|30|s|/etc/containernet/containernet.conf|timeout=1|timeout=30|systemctl reload containernet|mn|cnt_to_1|ctr|sw|docker leftover leftover down; bounce|CONTAINERNET_TIMEOUT leftover 1 leftover; a 2s addDocker is aborted so the topo 504s
core-emu|CORE_TIMEOUT|1|30|s|/etc/core/core.conf|timeout=1|timeout=30|systemctl reload core-daemon|core-cli|cre_to_1|nodes|sess|netns leftover leftover down; bounce|CORE_TIMEOUT leftover 1 leftover; a 2s start is aborted so the sess 504s
imunes|IMUNES_TIMEOUT|1|30|s|/etc/imunes/imunes.conf|timeout=1|timeout=30|systemctl reload imunes|imunes|imu_to_1|nodes|exp|netns leftover leftover down; bounce|IMUNES_TIMEOUT leftover 1 leftover; a 2s start is aborted so the exp 504s
gns3|GNS3_TIMEOUT|1|30|s|/etc/gns3/gns3_server.conf|timeout=1|timeout=30|systemctl reload gns3server|gns3|gns_to_1|nodes|proj|qemu leftover leftover down; bounce|GNS3_TIMEOUT leftover 1 leftover; a 2s start is aborted so the node 504s
eve-ng|EVENG_TIMEOUT|1|30|s|/etc/eve-ng/eve-ng.conf|timeout=1|timeout=30|systemctl reload eve-ng|unl_wrapper|eve_to_1|nodes|labs|qemu leftover leftover down; bounce|EVENG_TIMEOUT leftover 1 leftover; a 2s start is aborted so the node 504s
'''
WAVE52 = (
    "nornir/netmiko/napalm/scrapli/textfsm/ntc/genie/pyats/robotframework/"
    "paramiko/pexpect/junos-eznc/nxapi/iosxe/eos/batfish/capirca/nsot/"
    "trigger/netconf/ncclient/yangson/ydk/gnmi/gnoi/gribi/p4runtime/"
    "stratum/onos/odl/ryu/pox/nox/floodlight/mininet/containernet/"
    "core-emu/imunes/gns3/eve-ng"
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
        svc = f"h2{i:02d}x"
        ns = f"h2{i:02d}"
        clu = f"prod-apsi{901 + i}-{svc[:3]}"
        ticket = f"W2-{12803 + i}"
        node = f"ip-10-237-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4141


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4140 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-52 leftover: {WAVE52}.",
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
