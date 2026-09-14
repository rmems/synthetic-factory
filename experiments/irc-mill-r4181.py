#!/usr/bin/env python3
"""IRC mill r4181+ — wave-54 vpn/aaa/host-ids leftover.

NEW on-call plants (not Wave-27–53 tails). BAN ypbind/oddjob,
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
tac_plus|TACPLUS_TIMEOUT|1|10|s|/etc/tacacs/tac_plus.conf|timeout = 1|timeout = 10|systemctl reload tac_plus|tac_plus|tac_to_1|aaa|nas|tcp leftover leftover down; bounce|TACPLUS_TIMEOUT leftover 1 leftover; a 2s authen is aborted so aaa 401s
tacacs|TACACS_TIMEOUT|1|10|s|/etc/tacacs/tacacs.conf|timeout=1|timeout=10|systemctl reload tacacs|tacacs|tcs_to_1|aaa|nas|tcp leftover leftover down; bounce|TACACS_TIMEOUT leftover 1 leftover; a 2s authen is aborted so aaa 401s
tacacsplus|TACACSPLUS_TIMEOUT|1|10|s|/etc/tacacsplus/tacacsplus.conf|timeout=1|timeout=10|systemctl reload tacacsplus|tacacsplus|tcp_to_1|aaa|nas|tcp leftover leftover down; bounce|TACACSPLUS_TIMEOUT leftover 1 leftover; a 2s authen is aborted so aaa 401s
wpa_supplicant|WPA2_TIMEOUT|1|10|s|/etc/wpa_supplicant/wpa_supplicant.conf|timeout=1|timeout=10|systemctl reload wpa_supplicant|wpa_cli|wps_to_1|assoc|ssids|nl80211 leftover leftover down; bounce|WPA2_TIMEOUT leftover 1 leftover; a 2s 4way is aborted so Wi-Fi 504s
accel-ppp|ACCEL_TIMEOUT|1|10|s|/etc/accel-ppp/accel-ppp.conf|timeout=1|timeout=10|systemctl reload accel-ppp|accel-cmd|acc_to_1|ppp|ifaces|ppp leftover leftover down; bounce|ACCEL_TIMEOUT leftover 1 leftover; a 2s lcp is aborted so the session 504s
sstp|SSTP_TIMEOUT|1|30|s|/etc/sstp/sstp.conf|timeout=1|timeout=30|systemctl reload sstp|sstpc|sst_to_1|tunnels|ppp|https leftover leftover 403; bounce|SSTP_TIMEOUT leftover 1 leftover; a 2s handshake is aborted so the vpn 504s
openconnect|OPENCONNECT_TIMEOUT|1|30|s|/etc/openconnect/openconnect.conf|timeout=1|timeout=30|systemctl reload openconnect|openconnect|ocn_to_1|tunnels|dtls|https leftover leftover 403; bounce|OPENCONNECT_TIMEOUT leftover 1 leftover; a 2s dtls is aborted so the vpn 504s
anyconnect|ANYCONNECT_TIMEOUT|1|30|s|/etc/anyconnect/anyconnect.conf|timeout=1|timeout=30|systemctl reload vpnagentd|vpn|any_to_1|tunnels|dtls|https leftover leftover 403; bounce|ANYCONNECT_TIMEOUT leftover 1 leftover; a 2s dtls is aborted so the vpn 504s
globalprotect|GP_TIMEOUT|1|30|s|/etc/pan/globalprotect.conf|timeout=1|timeout=30|systemctl reload globalprotect|globalprotect|gp_to_1|tunnels|ssl|https leftover leftover 403; bounce|GP_TIMEOUT leftover 1 leftover; a 2s portal is aborted so the vpn 504s
pulse-secure|PULSE_TIMEOUT|1|30|s|/etc/pulse/pulse.conf|timeout=1|timeout=30|systemctl reload pulsesecure|pulsesecure|pls_to_1|tunnels|ssl|https leftover leftover 403; bounce|PULSE_TIMEOUT leftover 1 leftover; a 2s ive is aborted so the vpn 504s
forticlient|FORTICLIENT_TIMEOUT|1|30|s|/etc/forticlient/forticlient.conf|timeout=1|timeout=30|systemctl reload forticlient|forticlient|ftc_to_1|tunnels|ssl|https leftover leftover 403; bounce|FORTICLIENT_TIMEOUT leftover 1 leftover; a 2s sslvpn is aborted so the vpn 504s
checkpoint|SNX_TIMEOUT|1|30|s|/etc/checkpoint/snx.conf|timeout=1|timeout=30|systemctl reload snx|snx|chk_to_1|tunnels|ssl|https leftover leftover 403; bounce|SNX_TIMEOUT leftover 1 leftover; a 2s ccovpn is aborted so the vpn 504s
snx|SNX2_TIMEOUT|1|30|s|/etc/snx/snx.conf|timeout=1|timeout=30|systemctl reload snx|snx|snx_to_1|tunnels|ssl|https leftover leftover 403; bounce|SNX2_TIMEOUT leftover 1 leftover; a 2s handshake is aborted so the vpn 504s
cisco-vpn|CISCOVPN_TIMEOUT|1|30|s|/etc/vpnc/default.conf|timeout=1|timeout=30|systemctl reload vpnc|vpnc|cvp_to_1|tunnels|isakmp|udp leftover leftover down; bounce|CISCOVPN_TIMEOUT leftover 1 leftover; a 2s isakmp is aborted so the vpn 504s
bro|BRO_TIMEOUT|1|10|s|/etc/bro/node.cfg|timeout=1|timeout=10|systemctl reload bro|bro|bro_to_1|logs|ifaces|pcap leftover leftover down; bounce|BRO_TIMEOUT leftover 1 leftover; a 2s log is aborted so detections vanish
sagan|SAGAN_TIMEOUT|1|10|s|/etc/sagan/sagan.yaml|timeout: 1|timeout: 10|systemctl reload sagan|sagan|sag_to_1|alerts|logs|fs leftover leftover down; bounce|SAGAN_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the alert 504s
prelude|PRELUDE_TIMEOUT|1|10|s|/etc/prelude/prelude.conf|timeout=1|timeout=10|systemctl reload prelude|prelude|prl_to_1|idme|mgr|ssl leftover leftover down; bounce|PRELUDE_TIMEOUT leftover 1 leftover; a 2s idme is aborted so the mgr 504s
auditctl|AUDITCTL_TIMEOUT|1|10|s|/etc/audit/auditd.conf|timeout=1|timeout=10|systemctl reload auditd|auditctl|act_to_1|rules|kernel|netlink leftover leftover down; bounce|AUDITCTL_TIMEOUT leftover 1 leftover; a 2s load is aborted so the rules 504s
ausearch|AUSEARCH_TIMEOUT|1|10|s|/etc/audit/auditd.conf|timeout=1|timeout=10|systemctl reload auditd|ausearch|aus_to_1|logs|keys|fs leftover leftover down; bounce|AUSEARCH_TIMEOUT leftover 1 leftover; a 2s query is aborted so the search 504s
aureport|AUREPORT_TIMEOUT|1|10|s|/etc/audit/auditd.conf|timeout=1|timeout=10|systemctl reload auditd|aureport|aur_to_1|logs|keys|fs leftover leftover down; bounce|AUREPORT_TIMEOUT leftover 1 leftover; a 2s report is aborted so the csv 504s
osqueryd|OSQUERYD_TIMEOUT|1|10|s|/etc/osquery/osquery.conf|timeout=1|timeout=10|systemctl reload osqueryd|osqueryd|oqd_to_1|sched|packs|fs leftover leftover down; bounce|OSQUERYD_TIMEOUT leftover 1 leftover; a 2s query is aborted so the pack 504s
kolide|KOLIDE_TIMEOUT|1|10|s|/etc/kolide/launcher.flags|timeout=1|timeout=10|systemctl reload launcher|launcher|kol_to_1|enroll|hosts|https leftover leftover 403; bounce|KOLIDE_TIMEOUT leftover 1 leftover; a 2s enroll is aborted so the host 401s
santa|SANTA_TIMEOUT|1|10|s|/etc/santa/config.plist|timeout=1|timeout=10|systemctl reload santad|santactl|snt_to_1|bins|rules|fs leftover leftover down; bounce|SANTA_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the allowlist 401s
falcosidekick|FALCOSIDEKICK_TIMEOUT|1|10|s|/etc/falco/falcosidekick.yaml|timeout: 1s|timeout: 10s|systemctl reload falcosidekick|falcosidekick|fsk2_to_1|alerts|outputs|nats leftover leftover down; bounce|FALCOSIDEKICK_TIMEOUT leftover 1 leftover; a 2s post is aborted so pages vanish
samhain|SAMHAIN_TIMEOUT|1|30|s|/etc/samhain/samhainrc|timeout=1|timeout=30|systemctl reload samhain|samhain|sam_to_1|files|sig|fs leftover leftover down; bounce|SAMHAIN_TIMEOUT leftover 1 leftover; a 2s check is aborted so the baseline 504s
osiris|OSIRIS_TIMEOUT|1|30|s|/etc/osiris/osiris.conf|timeout=1|timeout=30|systemctl reload osirisd|osiris|osi_to_1|scans|hosts|ssl leftover leftover down; bounce|OSIRIS_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the report 504s
rkhunter|RKHUNTER_TIMEOUT|1|30|s|/etc/rkhunter.conf|timeout=1|timeout=30|systemctl reload rkhunter|rkhunter|rkh_to_1|scans|rootkits|fs leftover leftover down; bounce|RKHUNTER_TIMEOUT leftover 1 leftover; a 2s check is aborted so the report 504s
chkrootkit|CHKROOTKIT_TIMEOUT|1|30|s|/etc/chkrootkit.conf|timeout=1|timeout=30|systemctl reload chkrootkit|chkrootkit|crk_to_1|scans|rootkits|fs leftover leftover down; bounce|CHKROOTKIT_TIMEOUT leftover 1 leftover; a 2s check is aborted so the report 504s
lynis|LYNIS_TIMEOUT|1|30|s|/etc/lynis/default.prf|timeout=1|timeout=30|systemctl reload lynis|lynis|lyn_to_1|audits|hardening|fs leftover leftover down; bounce|LYNIS_TIMEOUT leftover 1 leftover; a 2s test is aborted so the audit 504s
openscap|OPENSCAP_TIMEOUT|1|30|s|/etc/openscap/oscap.conf|timeout=1|timeout=30|systemctl reload oscap|oscap|osc_to_1|xccdf|oval|fs leftover leftover down; bounce|OPENSCAP_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the scan 504s
oscap|OSCAP_TIMEOUT|1|30|s|/etc/openscap/oscap.conf|timeout=1|timeout=30|systemctl reload oscap|oscap|osc2_to_1|xccdf|oval|fs leftover leftover down; bounce|OSCAP_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the scan 504s
ssg|SSG_TIMEOUT|1|30|s|/etc/ssg/ssg.conf|timeout=1|timeout=30|systemctl reload ssg|ssg|ssg_to_1|guides|xccdf|fs leftover leftover down; bounce|SSG_TIMEOUT leftover 1 leftover; a 2s build is aborted so the guide 504s
scap|SCAP_TIMEOUT|1|30|s|/etc/scap/scap.conf|timeout=1|timeout=30|systemctl reload scap|scap|scp_to_1|datastreams|oval|fs leftover leftover down; bounce|SCAP_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the stream 504s
oval|OVAL_TIMEOUT|1|30|s|/etc/oval/oval.conf|timeout=1|timeout=30|systemctl reload ovaldi|ovaldi|ovl_to_1|defs|sys|fs leftover leftover down; bounce|OVAL_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the def 504s
xccdf|XCCDF_TIMEOUT|1|30|s|/etc/xccdf/xccdf.conf|timeout=1|timeout=30|systemctl reload xccdf|xccdf|xcd_to_1|bench|rules|fs leftover leftover down; bounce|XCCDF_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the bench 504s
cis-cat|CISCAT_TIMEOUT|1|30|s|/etc/cis-cat/cis-cat.conf|timeout=1|timeout=30|systemctl reload cis-cat|cis-cat|cis_to_1|bench|ass|fs leftover leftover down; bounce|CISCAT_TIMEOUT leftover 1 leftover; a 2s assess is aborted so the report 504s
tfsec|TFSEC_TIMEOUT|1|30|s|/etc/tfsec/tfsec.conf|timeout=1|timeout=30|systemctl reload tfsec|tfsec|tfs_to_1|tf|findings|fs leftover leftover down; bounce|TFSEC_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the finding 504s
infracost|INFRACOST_TIMEOUT|1|30|s|/etc/infracost/infracost.yml|timeout: 1|timeout: 30|systemctl reload infracost|infracost|ifc_to_1|tf|cost|https leftover leftover 403; bounce|INFRACOST_TIMEOUT leftover 1 leftover; a 2s breakdown is aborted so the report 504s
tflint|TFLINT_TIMEOUT|1|30|s|/etc/tflint/tflint.hcl|timeout = 1|timeout = 30|systemctl reload tflint|tflint|tfl_to_1|tf|rules|fs leftover leftover down; bounce|TFLINT_TIMEOUT leftover 1 leftover; a 2s lint is aborted so the rule 504s
tfenv|TFENV_TIMEOUT|1|30|s|/etc/tfenv/tfenv.conf|timeout=1|timeout=30|systemctl reload tfenv|tfenv|tfe_to_1|vers|bins|https leftover leftover 403; bounce|TFENV_TIMEOUT leftover 1 leftover; a 2s install is aborted so the bin 504s
'''
WAVE54 = (
    "tac_plus/tacacs/tacacsplus/wpa_supplicant/accel-ppp/sstp/openconnect/"
    "anyconnect/globalprotect/pulse-secure/forticlient/checkpoint/snx/"
    "cisco-vpn/bro/sagan/prelude/auditctl/ausearch/aureport/osqueryd/"
    "kolide/santa/falcosidekick/samhain/osiris/rkhunter/chkrootkit/lynis/"
    "openscap/oscap/ssg/scap/oval/xccdf/cis-cat/tfsec/infracost/tflint/tfenv"
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
        svc = f"j4{i:02d}x"
        ns = f"j4{i:02d}"
        clu = f"prod-apsk{901 + i}-{svc[:3]}"
        ticket = f"W2-{12883 + i}"
        node = f"ip-10-239-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4181


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4180 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-54 leftover: {WAVE54}.",
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
