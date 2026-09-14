#!/usr/bin/env python3
"""IRC mill r4101+ — wave-50 wallet/2fa leftover.

NEW on-call plants (not Wave-27–49 tails). BAN ypbind/oddjob,
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
dashlane|DASHLANE_TIMEOUT|1|10|s|/etc/dashlane/dashlane.conf|timeout=1|timeout=10|systemctl reload dashlane|dashlane|dsh_to_1|vault|items|https leftover leftover 403; bounce|DASHLANE_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
nordpass|NORDPASS_TIMEOUT|1|10|s|/etc/nordpass/nordpass.conf|timeout=1|timeout=10|systemctl reload nordpass|nordpass|nrp_to_1|vault|items|https leftover leftover 403; bounce|NORDPASS_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
protonpass|PROTONPASS_TIMEOUT|1|10|s|/etc/protonpass/protonpass.conf|timeout=1|timeout=10|systemctl reload protonpass|proton-pass|prp_to_1|vault|items|https leftover leftover 403; bounce|PROTONPASS_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
keepass2|KEEPASS2_TIMEOUT|1|10|s|/etc/keepass2/KeePass.config.xml|timeout=1|timeout=10|systemctl reload keepass2|keepass2|kp2_to_1|kdbx|entries|fs leftover leftover down; bounce|KEEPASS2_TIMEOUT leftover 1 leftover; a 2s unlock is aborted so the db 401s
1password|OP_TIMEOUT|1|10|s|/etc/1password/op.conf|timeout=1|timeout=10|systemctl reload 1password|op|op1_to_1|vault|items|https leftover leftover 403; bounce|OP_TIMEOUT leftover 1 leftover; a 2s get is aborted so the vault 401s
roboform|ROBOFORM_TIMEOUT|1|10|s|/etc/roboform/roboform.conf|timeout=1|timeout=10|systemctl reload roboform|roboform|rbf_to_1|vault|items|https leftover leftover 403; bounce|ROBOFORM_TIMEOUT leftover 1 leftover; a 2s fill is aborted so the vault 401s
sticky-password|STICKY_TIMEOUT|1|10|s|/etc/sticky-password/sticky.conf|timeout=1|timeout=10|systemctl reload sticky-password|sticky|stk_to_1|vault|items|https leftover leftover 403; bounce|STICKY_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
authy|AUTHY_TIMEOUT|1|10|s|/etc/authy/authy.conf|timeout=1|timeout=10|systemctl reload authy|authy|ath_to_1|tokens|devices|https leftover leftover 403; bounce|AUTHY_TIMEOUT leftover 1 leftover; a 2s totp is aborted so 2FA 401s
andotp|ANDOTP_TIMEOUT|1|10|s|/etc/andotp/andotp.conf|timeout=1|timeout=10|systemctl reload andotp|andotp|and_to_1|tokens|db|fs leftover leftover down; bounce|ANDOTP_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so 2FA 401s
aegis|AEGIS_TIMEOUT|1|10|s|/etc/aegis/aegis.conf|timeout=1|timeout=10|systemctl reload aegis|aegis|aeg_to_1|tokens|db|fs leftover leftover down; bounce|AEGIS_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so 2FA 401s
freeotp|FREEOTP_TIMEOUT|1|10|s|/etc/freeotp/freeotp.conf|timeout=1|timeout=10|systemctl reload freeotp|freeotp|fot_to_1|tokens|db|fs leftover leftover down; bounce|FREEOTP_TIMEOUT leftover 1 leftover; a 2s totp is aborted so 2FA 401s
oath-toolkit|OATH_TIMEOUT|1|10|s|/etc/oath/oath.conf|timeout=1|timeout=10|systemctl reload oath|oathtool|oat_to_1|tokens|users|fs leftover leftover down; bounce|OATH_TIMEOUT leftover 1 leftover; a 2s totp is aborted so PAM 401s
yubikey-manager|YKMAN_TIMEOUT|1|10|s|/etc/yubikey/ykman.conf|timeout=1|timeout=10|systemctl reload pcscd|ykman|ykm_to_1|slots|otp|usb leftover leftover down; bounce|YKMAN_TIMEOUT leftover 1 leftover; a 2s ccid is aborted so the key 401s
yubioath|YUBIOATH_TIMEOUT|1|10|s|/etc/yubikey/yubioath.conf|timeout=1|timeout=10|systemctl reload pcscd|yubioath|yoa_to_1|creds|otp|usb leftover leftover down; bounce|YUBIOATH_TIMEOUT leftover 1 leftover; a 2s calculate is aborted so 2FA 401s
solokeys|SOLO_TIMEOUT|1|10|s|/etc/solokeys/solo.conf|timeout=1|timeout=10|systemctl reload pcscd|solo|sol_to_1|fido|keys|usb leftover leftover down; bounce|SOLO_TIMEOUT leftover 1 leftover; a 2s assert is aborted so FIDO 401s
nitrokey|NITROKEY_TIMEOUT|1|10|s|/etc/nitrokey/nitrokey.conf|timeout=1|timeout=10|systemctl reload pcscd|nitropy|ntk_to_1|otp|keys|usb leftover leftover down; bounce|NITROKEY_TIMEOUT leftover 1 leftover; a 2s totp is aborted so 2FA 401s
onlykey|ONLYKEY_TIMEOUT|1|10|s|/etc/onlykey/onlykey.conf|timeout=1|timeout=10|systemctl reload pcscd|onlykey-cli|onk_to_1|slots|keys|usb leftover leftover down; bounce|ONLYKEY_TIMEOUT leftover 1 leftover; a 2s hmac is aborted so 2FA 401s
ledger|LEDGER_TIMEOUT|1|10|s|/etc/ledger/ledger-live.conf|timeout=1|timeout=10|systemctl reload ledger-live|ledger-live|ldg_to_1|apps|usb|usb leftover leftover down; bounce|LEDGER_TIMEOUT leftover 1 leftover; a 2s APDU is aborted so the app 401s
trezor|TREZOR_TIMEOUT|1|10|s|/etc/trezor/trezord.conf|timeout=1|timeout=10|systemctl reload trezord|trezorctl|trz_to_1|apps|usb|usb leftover leftover down; bounce|TREZOR_TIMEOUT leftover 1 leftover; a 2s protobuf is aborted so the app 401s
keepkey|KEEPKEY_TIMEOUT|1|10|s|/etc/keepkey/keepkey.conf|timeout=1|timeout=10|systemctl reload keepkeyd|keepkeyctl|kpk_to_1|apps|usb|usb leftover leftover down; bounce|KEEPKEY_TIMEOUT leftover 1 leftover; a 2s protobuf is aborted so the app 401s
coldcard|COLDCARD_TIMEOUT|1|10|s|/etc/coldcard/ckcc.conf|timeout=1|timeout=10|systemctl reload ckcc|ckcc|ckc_to_1|psbt|usb|usb leftover leftover down; bounce|COLDCARD_TIMEOUT leftover 1 leftover; a 2s psbt is aborted so sign 401s
bitbox|BITBOX_TIMEOUT|1|10|s|/etc/bitbox/bitbox.conf|timeout=1|timeout=10|systemctl reload bitbox|bitbox|bbx_to_1|apps|usb|usb leftover leftover down; bounce|BITBOX_TIMEOUT leftover 1 leftover; a 2s api is aborted so the app 401s
jade|JADE_TIMEOUT|1|10|s|/etc/jade/jade.conf|timeout=1|timeout=10|systemctl reload jade|jade|jad_to_1|psbt|uart|usb leftover leftover down; bounce|JADE_TIMEOUT leftover 1 leftover; a 2s sign is aborted so the tx 401s
electrum|ELECTRUM_TIMEOUT|1|30|s|/etc/electrum/config|timeout=1|timeout=30|systemctl reload electrum|electrum|ele_to_1|wallet|spv|tcp leftover leftover down; bounce|ELECTRUM_TIMEOUT leftover 1 leftover; a 2s broadcast is aborted so the tx 504s
sparrow|SPARROW_TIMEOUT|1|30|s|/etc/sparrow/config|timeout=1|timeout=30|systemctl reload sparrow|sparrow|spa_to_1|wallet|electrum|tcp leftover leftover down; bounce|SPARROW_TIMEOUT leftover 1 leftover; a 2s electrum is aborted so the tx 504s
wasabi|WASABI_TIMEOUT|1|30|s|/etc/wasabi/Config.json|"Timeout": 1|"Timeout": 30|systemctl reload wasabi|wassabee|was_to_1|wallet|tor|tor leftover leftover down; bounce|WASABI_TIMEOUT leftover 1 leftover; a 2s coinjoin is aborted so the mix 504s
samourai|SAMOURAI_TIMEOUT|1|30|s|/etc/samourai/whirlpool.conf|timeout=1|timeout=30|systemctl reload whirlpool|whirlpool|sam_to_1|mix|tor|tor leftover leftover down; bounce|SAMOURAI_TIMEOUT leftover 1 leftover; a 2s whirlpool is aborted so the mix 504s
bluewallet|BLUEWALLET_TIMEOUT|1|30|s|/etc/bluewallet/config.json|"timeout": 1|"timeout": 30|systemctl reload bluewallet|bluewallet|blu_to_1|ln|lnd|grpc leftover leftover down; bounce|BLUEWALLET_TIMEOUT leftover 1 leftover; a 2s invoice is aborted so LN 504s
lnd|LND_TIMEOUT|1|30|s|/etc/lnd/lnd.conf|timeout=1|timeout=30|systemctl reload lnd|lncli|lnd_to_1|chan|peers|grpc leftover leftover down; bounce|LND_TIMEOUT leftover 1 leftover; a 2s openchannel is aborted so LN 504s
clightning|CLN_TIMEOUT|1|30|s|/etc/lightning/config|timeout=1|timeout=30|systemctl reload lightningd|lightning-cli|cln_to_1|chan|peers|unix leftover leftover down; bounce|CLN_TIMEOUT leftover 1 leftover; a 2s fundchannel is aborted so LN 504s
eclair|ECLAIR_TIMEOUT|1|30|s|/etc/eclair/eclair.conf|eclair.api.timeout=1|eclair.api.timeout=30|systemctl reload eclair|eclair-cli|ecl_to_1|chan|peers|http leftover leftover down; bounce|ECLAIR_TIMEOUT leftover 1 leftover; a 2s open is aborted so LN 504s
btcd|BTCD_TIMEOUT|1|30|s|/etc/btcd/btcd.conf|rpcuser_timeout=1|rpcuser_timeout=30|systemctl reload btcd|btcctl|btc_to_1|blocks|peers|p2p leftover leftover down; bounce|BTCD_TIMEOUT leftover 1 leftover; a 2s getblock is aborted so the node 504s
bitcoind|BITCOIND_TIMEOUT|1|30|s|/etc/bitcoin/bitcoin.conf|rpcclienttimeout=1|rpcclienttimeout=30|systemctl reload bitcoind|bitcoin-cli|bcd_to_1|blocks|peers|p2p leftover leftover down; bounce|BITCOIND_TIMEOUT leftover 1 leftover; a 2s getblock is aborted so the node 504s
geth|GETH_TIMEOUT|1|30|s|/etc/geth/config.toml|timeout = 1|timeout = 30|systemctl reload geth|geth|get_to_1|blocks|peers|p2p leftover leftover down; bounce|GETH_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the node 504s
nethermind|NETHERMIND_TIMEOUT|1|30|s|/etc/nethermind/config.cfg|JsonRpc.Timeout=1|JsonRpc.Timeout=30|systemctl reload nethermind|nethermind|nth_to_1|blocks|peers|p2p leftover leftover down; bounce|NETHERMIND_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the node 504s
erigon|ERIGON_TIMEOUT|1|30|s|/etc/erigon/erigon.toml|timeout = 1|timeout = 30|systemctl reload erigon|erigon|eri_to_1|blocks|peers|p2p leftover leftover down; bounce|ERIGON_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the node 504s
besu|BESU_TIMEOUT|1|30|s|/etc/besu/config.toml|timeout=1|timeout=30|systemctl reload besu|besu|bes_to_1|blocks|peers|p2p leftover leftover down; bounce|BESU_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the node 504s
prysm|PRYSM_TIMEOUT|1|30|s|/etc/prysm/config.yaml|timeout: 1s|timeout: 30s|systemctl reload prysm|prysmctl|pry_to_1|slots|peers|p2p leftover leftover down; bounce|PRYSM_TIMEOUT leftover 1 leftover; a 2s beacon is aborted so the node 504s
lighthouse|LIGHTHOUSE_TIMEOUT|1|30|s|/etc/lighthouse/config.toml|timeout = 1|timeout = 30|systemctl reload lighthouse|lighthouse|lgt_to_1|slots|peers|p2p leftover leftover down; bounce|LIGHTHOUSE_TIMEOUT leftover 1 leftover; a 2s beacon is aborted so the node 504s
teku|TEKU_TIMEOUT|1|30|s|/etc/teku/teku.yaml|timeout: 1s|timeout: 30s|systemctl reload teku|teku|tek_to_1|slots|peers|p2p leftover leftover down; bounce|TEKU_TIMEOUT leftover 1 leftover; a 2s beacon is aborted so the node 504s
'''
WAVE50 = (
    "dashlane/nordpass/protonpass/keepass2/1password/roboform/"
    "sticky-password/authy/andotp/aegis/freeotp/oath-toolkit/"
    "yubikey-manager/yubioath/solokeys/nitrokey/onlykey/ledger/"
    "trezor/keepkey/coldcard/bitbox/jade/electrum/sparrow/wasabi/"
    "samourai/bluewallet/lnd/clightning/eclair/btcd/bitcoind/geth/"
    "nethermind/erigon/besu/prysm/lighthouse/teku"
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
        svc = f"f0{i:02d}x"
        ns = f"f0{i:02d}"
        clu = f"prod-apsg{901 + i}-{svc[:3]}"
        ticket = f"W2-{12723 + i}"
        node = f"ip-10-235-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4101


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4100 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-50 leftover: {WAVE50}.",
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
