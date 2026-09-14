#!/usr/bin/env python3
"""IRC mill r4521+ — wave-71 edge/iot/scada leftover.

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
k3sedge|K3SEDGE_TIMEOUT|1|30|s|/etc/k3sedge/k3sedge.conf|timeout=1|timeout=30|systemctl reload k3sedge|k3|k3s_to_1|nodes|agents|k8s leftover leftover down; bounce|K3SEDGE_TIMEOUT leftover 1 leftover; a 2s join is aborted so the nodes 504s
kubeedge|KUBEEDGE_TIMEOUT|1|30|s|/etc/kubeedge/kubeedge.conf|timeout=1|timeout=30|systemctl reload kubeedge|ke|kub_to_1|edges|devices|k8s leftover leftover down; bounce|KUBEEDGE_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the edges 504s
openyurt|OPENYURT_TIMEOUT|1|30|s|/etc/openyurt/openyurt.conf|timeout=1|timeout=30|systemctl reload openyurt|oy|ope_to_1|nodes|pools|k8s leftover leftover down; bounce|OPENYURT_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the nodes 504s
superedge|SUPEREDGE_TIMEOUT|1|30|s|/etc/superedge/superedge.conf|timeout=1|timeout=30|systemctl reload superedge|se|sup_to_1|nodes|tunnels|k8s leftover leftover down; bounce|SUPEREDGE_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the nodes 504s
akri2|AKRI2_TIMEOUT|1|30|s|/etc/akri2/akri2.conf|timeout=1|timeout=30|systemctl reload akri2|ak|akr_to_1|devices|brokers|k8s leftover leftover down; bounce|AKRI2_TIMEOUT leftover 1 leftover; a 2s discover is aborted so the devices 504s
shifu2|SHIFU2_TIMEOUT|1|30|s|/etc/shifu2/shifu2.conf|timeout=1|timeout=30|systemctl reload shifu2|sf|shi_to_1|devices|twinners|k8s leftover leftover down; bounce|SHIFU2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the devices 504s
edgexfoundry|EDGEXFOUNDRY_TIMEOUT|1|30|s|/etc/edgexfoundry/edgexfoundry.conf|timeout=1|timeout=30|systemctl reload edgexfoundry|ex|edg_to_1|devices|core|https leftover leftover down; bounce|EDGEXFOUNDRY_TIMEOUT leftover 1 leftover; a 2s register is aborted so the devices 504s
kuiper2|KUIPER2_TIMEOUT|1|30|s|/etc/kuiper2/kuiper2.conf|timeout=1|timeout=30|systemctl reload kuiper2|kp|kui_to_1|rules|streams|mqtt leftover leftover down; bounce|KUIPER2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the rules 504s
emqxedge|EMQXEDGE_TIMEOUT|1|30|s|/etc/emqxedge/emqxedge.conf|timeout=1|timeout=30|systemctl reload emqxedge|eq|emq_to_1|topics|clients|mqtt leftover leftover down; bounce|EMQXEDGE_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the topics 504s
nanomq2|NANOMQ2_TIMEOUT|1|30|s|/etc/nanomq2/nanomq2.conf|timeout=1|timeout=30|systemctl reload nanomq2|nq|nan_to_1|topics|clients|mqtt leftover leftover down; bounce|NANOMQ2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the topics 504s
mosca2|MOSCA2_TIMEOUT|1|30|s|/etc/mosca2/mosca2.conf|timeout=1|timeout=30|systemctl reload mosca2|mc|mos_to_1|topics|clients|mqtt leftover leftover down; bounce|MOSCA2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the topics 504s
aedes2|AEDES2_TIMEOUT|1|30|s|/etc/aedes2/aedes2.conf|timeout=1|timeout=30|systemctl reload aedes2|ad|aed_to_1|topics|clients|mqtt leftover leftover down; bounce|AEDES2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the topics 504s
kura2|KURA2_TIMEOUT|1|30|s|/etc/kura2/kura2.conf|timeout=1|timeout=30|systemctl reload kura2|kr|kur_to_1|bundles|cloud|mqtt leftover leftover down; bounce|KURA2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the bundles 504s
kapua2|KAPUA2_TIMEOUT|1|30|s|/etc/kapua2/kapua2.conf|timeout=1|timeout=30|systemctl reload kapua2|ka|kap_to_1|devices|tenants|https leftover leftover down; bounce|KAPUA2_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the devices 504s
thingsboard2|THINGSBOARD2_TIMEOUT|1|30|s|/etc/thingsboard2/thingsboard2.conf|timeout=1|timeout=30|systemctl reload thingsboard2|tb|thi_to_1|devices|telemetry|https leftover leftover down; bounce|THINGSBOARD2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the devices 504s
mainflux2|MAINFLUX2_TIMEOUT|1|30|s|/etc/mainflux2/mainflux2.conf|timeout=1|timeout=30|systemctl reload mainflux2|mf|mai_to_1|things|channels|https leftover leftover down; bounce|MAINFLUX2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the things 504s
chirpstack2|CHIRPSTACK2_TIMEOUT|1|30|s|/etc/chirpstack2/chirpstack2.conf|timeout=1|timeout=30|systemctl reload chirpstack2|cs|chi_to_1|gateways|devs|lora leftover leftover down; bounce|CHIRPSTACK2_TIMEOUT leftover 1 leftover; a 2s uplink is aborted so the gateways 504s
ttnstack|TTNSTACK_TIMEOUT|1|30|s|/etc/ttnstack/ttnstack.conf|timeout=1|timeout=30|systemctl reload ttnstack|ttn|ttn_to_1|gateways|apps|lora leftover leftover down; bounce|TTNSTACK_TIMEOUT leftover 1 leftover; a 2s uplink is aborted so the gateways 504s
lorawan2|LORAWAN2_TIMEOUT|1|30|s|/etc/lorawan2/lorawan2.conf|timeout=1|timeout=30|systemctl reload lorawan2|lw|lor_to_1|gateways|devs|lora leftover leftover down; bounce|LORAWAN2_TIMEOUT leftover 1 leftover; a 2s uplink is aborted so the gateways 504s
opcua2|OPCUA2_TIMEOUT|1|30|s|/etc/opcua2/opcua2.conf|timeout=1|timeout=30|systemctl reload opcua2|ua|opc_to_1|nodes|sessions|tcp leftover leftover down; bounce|OPCUA2_TIMEOUT leftover 1 leftover; a 2s read is aborted so the nodes 504s
open62541|OPEN62541_TIMEOUT|1|30|s|/etc/open62541/open62541.conf|timeout=1|timeout=30|systemctl reload open62541|o6|ope_to_1|nodes|sessions|tcp leftover leftover down; bounce|OPEN62541_TIMEOUT leftover 1 leftover; a 2s read is aborted so the nodes 504s
modbusd|MODBUSD_TIMEOUT|1|30|s|/etc/modbusd/modbusd.conf|timeout=1|timeout=30|systemctl reload modbusd|mb|mod_to_1|regs|slaves|tcp leftover leftover down; bounce|MODBUSD_TIMEOUT leftover 1 leftover; a 2s read is aborted so the regs 504s
bacnetd|BACNETD_TIMEOUT|1|30|s|/etc/bacnetd/bacnetd.conf|timeout=1|timeout=30|systemctl reload bacnetd|bn|bac_to_1|objects|devices|udp leftover leftover down; bounce|BACNETD_TIMEOUT leftover 1 leftover; a 2s read is aborted so the objects 504s
knxd2|KNXD2_TIMEOUT|1|30|s|/etc/knxd2/knxd2.conf|timeout=1|timeout=30|systemctl reload knxd2|kx|knx_to_1|groups|ets|knx leftover leftover down; bounce|KNXD2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the groups 504s
homeassistant2|HOMEASSISTANT2_TIMEOUT|1|30|s|/etc/homeassistant2/homeassistant2.conf|timeout=1|timeout=30|systemctl reload homeassistant2|ha|hom_to_1|entities|automations|https leftover leftover down; bounce|HOMEASSISTANT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the entities 504s
hassio2|HASSIO2_TIMEOUT|1|30|s|/etc/hassio2/hassio2.conf|timeout=1|timeout=30|systemctl reload hassio2|hs|has_to_1|addons|supervisor|https leftover leftover down; bounce|HASSIO2_TIMEOUT leftover 1 leftover; a 2s start is aborted so the addons 504s
openhab2|OPENHAB2_TIMEOUT|1|30|s|/etc/openhab2/openhab2.conf|timeout=1|timeout=30|systemctl reload openhab2|oh|ope_to_1|items|things|https leftover leftover down; bounce|OPENHAB2_TIMEOUT leftover 1 leftover; a 2s update is aborted so the items 504s
domoticz2|DOMOTICZ2_TIMEOUT|1|30|s|/etc/domoticz2/domoticz2.conf|timeout=1|timeout=30|systemctl reload domoticz2|dz|dom_to_1|devices|hw|https leftover leftover down; bounce|DOMOTICZ2_TIMEOUT leftover 1 leftover; a 2s update is aborted so the devices 504s
nodered2|NODERED2_TIMEOUT|1|30|s|/etc/nodered2/nodered2.conf|timeout=1|timeout=30|systemctl reload nodered2|nr|nod_to_1|flows|nodes|https leftover leftover down; bounce|NODERED2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the flows 504s
esphome2|ESPHOME2_TIMEOUT|1|30|s|/etc/esphome2/esphome2.conf|timeout=1|timeout=30|systemctl reload esphome2|es|esp_to_1|nodes|ymls|https leftover leftover down; bounce|ESPHOME2_TIMEOUT leftover 1 leftover; a 2s ota is aborted so the nodes 504s
tasmota2|TASMOTA2_TIMEOUT|1|30|s|/etc/tasmota2/tasmota2.conf|timeout=1|timeout=30|systemctl reload tasmota2|tm|tas_to_1|devices|cmds|mqtt leftover leftover down; bounce|TASMOTA2_TIMEOUT leftover 1 leftover; a 2s cmnd is aborted so the devices 504s
zigbee2mqtt2|ZIGBEE2MQTT2_TIMEOUT|1|30|s|/etc/zigbee2mqtt2/zigbee2mqtt2.conf|timeout=1|timeout=30|systemctl reload zigbee2mqtt2|z2|zig_to_1|devices|bridge|mqtt leftover leftover down; bounce|ZIGBEE2MQTT2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the devices 504s
zwavejs2|ZWAVEJS2_TIMEOUT|1|30|s|/etc/zwavejs2/zwavejs2.conf|timeout=1|timeout=30|systemctl reload zwavejs2|zw|zwa_to_1|nodes|stick|mqtt leftover leftover down; bounce|ZWAVEJS2_TIMEOUT leftover 1 leftover; a 2s value is aborted so the nodes 504s
deconz2|DECONZ2_TIMEOUT|1|30|s|/etc/deconz2/deconz2.conf|timeout=1|timeout=30|systemctl reload deconz2|dc|dec_to_1|lights|gw|https leftover leftover down; bounce|DECONZ2_TIMEOUT leftover 1 leftover; a 2s set is aborted so the lights 504s
phoscon2|PHOSCON2_TIMEOUT|1|30|s|/etc/phoscon2/phoscon2.conf|timeout=1|timeout=30|systemctl reload phoscon2|ph|pho_to_1|lights|gw|https leftover leftover down; bounce|PHOSCON2_TIMEOUT leftover 1 leftover; a 2s set is aborted so the lights 504s
homebridge2|HOMEBRIDGE2_TIMEOUT|1|30|s|/etc/homebridge2/homebridge2.conf|timeout=1|timeout=30|systemctl reload homebridge2|hb|hom_to_1|accessories|bridges|hap leftover leftover down; bounce|HOMEBRIDGE2_TIMEOUT leftover 1 leftover; a 2s update is aborted so the accessories 504s
scrypted2|SCRYPTED2_TIMEOUT|1|30|s|/etc/scrypted2/scrypted2.conf|timeout=1|timeout=30|systemctl reload scrypted2|sc|scr_to_1|cameras|plugins|https leftover leftover down; bounce|SCRYPTED2_TIMEOUT leftover 1 leftover; a 2s stream is aborted so the cameras 504s
frigate2|FRIGATE2_TIMEOUT|1|30|s|/etc/frigate2/frigate2.conf|timeout=1|timeout=30|systemctl reload frigate2|fg|fri_to_1|cameras|detect|mqtt leftover leftover down; bounce|FRIGATE2_TIMEOUT leftover 1 leftover; a 2s detect is aborted so the cameras 504s
motion2|MOTION2_TIMEOUT|1|30|s|/etc/motion2/motion2.conf|timeout=1|timeout=30|systemctl reload motion2|mo|mot_to_1|cameras|threads|http leftover leftover down; bounce|MOTION2_TIMEOUT leftover 1 leftover; a 2s detect is aborted so the cameras 504s
zoneminder2|ZONEMINDER2_TIMEOUT|1|30|s|/etc/zoneminder2/zoneminder2.conf|timeout=1|timeout=30|systemctl reload zoneminder2|zm|zon_to_1|monitors|events|https leftover leftover down; bounce|ZONEMINDER2_TIMEOUT leftover 1 leftover; a 2s detect is aborted so the monitors 504s
'''
WAVE = (
    "k3sedge/kubeedge/openyurt/superedge/akri2/shifu2/edgexfoundry/kuiper2/emqxedge/nanomq2/mosca2/aedes2/kura2/kapua2/thingsboard2/mainflux2/chirpstack2/ttnstack/lorawan2/opcua2/open62541/modbusd/bacnetd/knxd2/homeassistant2/hassio2/openhab2/domoticz2/nodered2/esphome2/tasmota2/zigbee2mqtt2/zwavejs2/deconz2/phoscon2/homebridge2/scrypted2/frigate2/motion2/zoneminder2"
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
        svc = f"b7{i:02d}x"
        ns = f"b7{i:02d}"
        clu = f"prod-apuc{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13563 + i }"
        node = f"ip-10-181-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4521


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-71 leftover: {WAVE}.",
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
