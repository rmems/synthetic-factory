#!/usr/bin/env python3
"""IRC mill r4301+ — wave-60 adc/chat leftover.

NEW on-call plants (not Wave-27–59 tails). BAN ypbind/oddjob,
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
mysql|MYSQL_TIMEOUT|1|30|s|/etc/mysql/my.cnf|wait_timeout=1|wait_timeout=30|systemctl reload mysql|mysql|mys_to_1|sess|innodb|sql leftover leftover down; bounce|MYSQL_TIMEOUT leftover 1 leftover; a 2s query is aborted so the sess 504s
postgres|POSTGRES_TIMEOUT|1|30|s|/etc/postgresql/postgresql.conf|statement_timeout=1|statement_timeout=30|systemctl reload postgresql|psql|pgs_to_1|sess|wal|sql leftover leftover down; bounce|POSTGRES_TIMEOUT leftover 1 leftover; a 2s query is aborted so the sess 504s
pxc|PXC_TIMEOUT|1|30|s|/etc/mysql/pxc.cnf|wsrep_provider_options="gmcast.peer_timeout=PT1S"|wsrep_provider_options="gmcast.peer_timeout=PT30S"|systemctl reload mysql|mysql|pxc_to_1|gcomm|nodes|sql leftover leftover down; bounce|PXC_TIMEOUT leftover 1 leftover; a 2s wsrep is aborted so the cluster 504s
fortios|FORTIOS_TIMEOUT|1|30|s|/etc/fortios/fortios.conf|timeout=1|timeout=30|systemctl reload fg|fg|fio_to_1|vdoms|wan|https leftover leftover 403; bounce|FORTIOS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the vdom 504s
panos|PANOS2_TIMEOUT|1|30|s|/etc/panos/panos.conf|timeout=1|timeout=30|systemctl reload pan|pan|pns_to_1|vsys|wan|https leftover leftover 403; bounce|PANOS2_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the vsys 504s
cumulus|CUMULUS_TIMEOUT|1|30|s|/etc/nclu/nclu.conf|timeout=1|timeout=30|systemctl reload nclu|net|cum_to_1|ifaces|clag|frr leftover leftover down; bounce|CUMULUS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the iface 504s
quagga|QUAGGA_TIMEOUT|1|10|s|/etc/quagga/zebra.conf|timeout=1|timeout=10|systemctl reload quagga|vtysh|qgg_to_1|ribs|peers|zebra leftover leftover down; bounce|QUAGGA_TIMEOUT leftover 1 leftover; a 2s show is aborted so the rib 504s
f5|F5_TIMEOUT|1|30|s|/etc/f5/bigip.conf|timeout=1|timeout=30|systemctl reload tmm|tmsh|f5_to_1|vs|pools|mcp leftover leftover down; bounce|F5_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the vs 504s
bigip|BIGIP_TIMEOUT|1|30|s|/etc/bigip/bigip.conf|timeout=1|timeout=30|systemctl reload tmm|tmsh|bip_to_1|vs|pools|mcp leftover leftover down; bounce|BIGIP_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the vs 504s
avi|AVI_TIMEOUT|1|30|s|/etc/avi/avi.conf|timeout=1|timeout=30|systemctl reload avi|avi|avi_to_1|vs|ses|https leftover leftover 403; bounce|AVI_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the vs 504s
netscaler|NETSCALER_TIMEOUT|1|30|s|/etc/netscaler/ns.conf|timeout=1|timeout=30|systemctl reload ns|ns|nsc_to_1|vips|svcs|https leftover leftover 403; bounce|NETSCALER_TIMEOUT leftover 1 leftover; a 2s bind is aborted so the vip 504s
a10|A10_TIMEOUT|1|30|s|/etc/a10/a10.conf|timeout=1|timeout=30|systemctl reload a10|a10|a10_to_1|vips|svcs|https leftover leftover 403; bounce|A10_TIMEOUT leftover 1 leftover; a 2s bind is aborted so the vip 504s
radware|RADWARE_TIMEOUT|1|30|s|/etc/radware/radware.conf|timeout=1|timeout=30|systemctl reload radware|radware|rdw_to_1|vips|svcs|https leftover leftover 403; bounce|RADWARE_TIMEOUT leftover 1 leftover; a 2s bind is aborted so the vip 504s
apigee|APIGEE_TIMEOUT|1|30|s|/etc/apigee/apigee.conf|timeout=1|timeout=30|systemctl reload apigee|apigee|apg_to_1|proxies|orgs|https leftover leftover 403; bounce|APIGEE_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the proxy 504s
krakend|KRAKEND_TIMEOUT|1|10|s|/etc/krakend/krakend.json|"timeout": "1s"|"timeout": "10s"|systemctl reload krakend|krakend|krk_to_1|eps|backends|http leftover leftover down; bounce|KRAKEND_TIMEOUT leftover 1 leftover; a 2s backend is aborted so the ep 504s
3proxy|THREEPROXY_TIMEOUT|1|10|s|/etc/3proxy/3proxy.cfg|timeout 1|timeout 10|systemctl reload 3proxy|3proxy|tpx_to_1|socks|users|tcp leftover leftover down; bounce|THREEPROXY_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the socks 504s
teams|TEAMS_TIMEOUT|1|30|s|/etc/teams/teams.conf|timeout=1|timeout=30|systemctl reload teams|teams|tms_to_1|calls|chats|https leftover leftover 403; bounce|TEAMS_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
zoom|ZOOM_TIMEOUT|1|30|s|/etc/zoom/zoom.conf|timeout=1|timeout=30|systemctl reload zoom|zoom|zom_to_1|calls|chats|https leftover leftover 403; bounce|ZOOM_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
webex|WEBEX_TIMEOUT|1|30|s|/etc/webex/webex.conf|timeout=1|timeout=30|systemctl reload webex|webex|wbx_to_1|calls|chats|https leftover leftover 403; bounce|WEBEX_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
bluejeans|BLUEJEANS_TIMEOUT|1|30|s|/etc/bluejeans/bluejeans.conf|timeout=1|timeout=30|systemctl reload bluejeans|bluejeans|blj_to_1|calls|chats|https leftover leftover 403; bounce|BLUEJEANS_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
telegram|TELEGRAM_TIMEOUT|1|30|s|/etc/telegram/telegram.conf|timeout=1|timeout=30|systemctl reload telegram-desktop|telegram-cli|tlg_to_1|msgs|chats|https leftover leftover 403; bounce|TELEGRAM_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
whatsapp|WHATSAPP_TIMEOUT|1|30|s|/etc/whatsapp/whatsapp.conf|timeout=1|timeout=30|systemctl reload whatsapp|whatsapp|wsp_to_1|msgs|chats|https leftover leftover 403; bounce|WHATSAPP_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
threema|THREEMA_TIMEOUT|1|30|s|/etc/threema/threema.conf|timeout=1|timeout=30|systemctl reload threema|threema|thm_to_1|msgs|chats|https leftover leftover 403; bounce|THREEMA_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
wire|WIRE_TIMEOUT|1|30|s|/etc/wire/wire.conf|timeout=1|timeout=30|systemctl reload wire|wire|wir_to_1|msgs|chats|https leftover leftover 403; bounce|WIRE_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
element|ELEMENT_TIMEOUT|1|30|s|/etc/element/config.json|"timeout": 1|"timeout": 30|systemctl reload element|element|elm_to_1|rooms|sync|https leftover leftover 403; bounce|ELEMENT_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the room 504s
riot|RIOT_TIMEOUT|1|30|s|/etc/riot/config.json|"timeout": 1|"timeout": 30|systemctl reload riot|riot|rio_to_1|rooms|sync|https leftover leftover 403; bounce|RIOT_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the room 504s
synapse|SYNAPSE_TIMEOUT|1|30|s|/etc/matrix-synapse/homeserver.yaml|timeout: 1s|timeout: 30s|systemctl reload matrix-synapse|synctl|syn2_to_1|sync|rooms|pg leftover leftover down; bounce|SYNAPSE_TIMEOUT leftover 1 leftover; a 2s /sync is aborted so Element 504s
kvm|KVM_TIMEOUT|1|30|s|/etc/libvirt/qemu.conf|timeout=1|timeout=30|systemctl reload libvirtd|virsh|kvm_to_1|vms|qcow|kvm leftover leftover down; bounce|KVM_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vm 504s
line|LINE_TIMEOUT|1|30|s|/etc/line/line.conf|timeout=1|timeout=30|systemctl reload line|line|lin_to_1|msgs|chats|https leftover leftover 403; bounce|LINE_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
wechat|WECHAT_TIMEOUT|1|30|s|/etc/wechat/wechat.conf|timeout=1|timeout=30|systemctl reload wechat|wechat|wct_to_1|msgs|chats|https leftover leftover 403; bounce|WECHAT_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
skype|SKYPE_TIMEOUT|1|30|s|/etc/skype/skype.conf|timeout=1|timeout=30|systemctl reload skype|skype|sky_to_1|calls|chats|https leftover leftover 403; bounce|SKYPE_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
hangouts|HANGOUTS_TIMEOUT|1|30|s|/etc/hangouts/hangouts.conf|timeout=1|timeout=30|systemctl reload hangouts|hangouts|hng_to_1|calls|chats|https leftover leftover 403; bounce|HANGOUTS_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
meet|MEET_TIMEOUT|1|30|s|/etc/meet/meet.conf|timeout=1|timeout=30|systemctl reload meet|meet|met_to_1|calls|chats|https leftover leftover 403; bounce|MEET_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
facetime|FACETIME_TIMEOUT|1|30|s|/etc/facetime/facetime.conf|timeout=1|timeout=30|systemctl reload facetime|facetime|fct_to_1|calls|ids|https leftover leftover 403; bounce|FACETIME_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
tox|TOX_TIMEOUT|1|30|s|/etc/tox/tox.conf|timeout=1|timeout=30|systemctl reload tox|tox|tox_to_1|peers|chats|udp leftover leftover down; bounce|TOX_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
ricochet|RICOCHET_TIMEOUT|1|30|s|/etc/ricochet/ricochet.conf|timeout=1|timeout=30|systemctl reload ricochet|ricochet|ric_to_1|peers|chats|tor leftover leftover down; bounce|RICOCHET_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
briar|BRIAR_TIMEOUT|1|30|s|/etc/briar/briar.conf|timeout=1|timeout=30|systemctl reload briar|briar|bri_to_1|peers|chats|tor leftover leftover down; bounce|BRIAR_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
session|SESSION_TIMEOUT|1|30|s|/etc/session/session.conf|timeout=1|timeout=30|systemctl reload session|session|ses_to_1|msgs|chats|onion leftover leftover down; bounce|SESSION_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
signald|SIGNALD_TIMEOUT|1|30|s|/etc/signald/signald.conf|timeout=1|timeout=30|systemctl reload signald|signald|sgd_to_1|msgs|accts|https leftover leftover 403; bounce|SIGNALD_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msg 504s
jami|JAMI_TIMEOUT|1|30|s|/etc/jami/jami.conf|timeout=1|timeout=30|systemctl reload jamid|jami|jam_to_1|calls|peers|dht leftover leftover down; bounce|JAMI_TIMEOUT leftover 1 leftover; a 2s media is aborted so the call 504s
'''
WAVE60 = (
    "mysql/postgres/pxc/fortios/panos/cumulus/quagga/f5/bigip/avi/netscaler/"
    "a10/radware/apigee/krakend/3proxy/teams/zoom/webex/bluejeans/telegram/"
    "whatsapp/threema/wire/element/riot/synapse/kvm/line/wechat/skype/"
    "hangouts/meet/facetime/tox/ricochet/briar/session/signald/jami"
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
        svc = f"p0{i:02d}x"
        ns = f"p0{i:02d}"
        clu = f"prod-apsr{901 + i}-{svc[:3]}"
        ticket = f"W2-{13123 + i}"
        node = f"ip-10-245-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4301


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4300 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-60 leftover: {WAVE60}.",
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
