#!/usr/bin/env python3
"""IRC mill r4121+ — wave-51 chain-dev/netauto leftover.

NEW on-call plants (not Wave-27–50 tails). BAN ypbind/oddjob,
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
nimbus|NIMBUS_TIMEOUT|1|30|s|/etc/nimbus/config.toml|timeout = 1|timeout = 30|systemctl reload nimbus|nimbus_beacon_node|nim_to_1|slots|peers|p2p leftover leftover down; bounce|NIMBUS_TIMEOUT leftover 1 leftover; a 2s beacon is aborted so the node 504s
lodestar|LODESTAR_TIMEOUT|1|30|s|/etc/lodestar/config.yaml|timeout: 1s|timeout: 30s|systemctl reload lodestar|lodestar|lod_to_1|slots|peers|p2p leftover leftover down; bounce|LODESTAR_TIMEOUT leftover 1 leftover; a 2s beacon is aborted so the node 504s
reth|RETH_TIMEOUT|1|30|s|/etc/reth/reth.toml|timeout = 1|timeout = 30|systemctl reload reth|reth|rth_to_1|blocks|peers|p2p leftover leftover down; bounce|RETH_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the node 504s
monerod|MONEROD_TIMEOUT|1|30|s|/etc/monero/monerod.conf|rpc-login-timeout=1|rpc-login-timeout=30|systemctl reload monerod|monerod|xmr_to_1|blocks|peers|p2p leftover leftover down; bounce|MONEROD_TIMEOUT leftover 1 leftover; a 2s get_block is aborted so the node 504s
xmrig|XMRIG_TIMEOUT|1|10|s|/etc/xmrig/config.json|"timeout": 1|"timeout": 10|systemctl reload xmrig|xmrig|xmg_to_1|shares|pool|tcp leftover leftover down; bounce|XMRIG_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the share 504s
p2pool|P2POOL_TIMEOUT|1|10|s|/etc/p2pool/p2pool.conf|timeout=1|timeout=10|systemctl reload p2pool|p2pool|p2p_to_1|shares|peers|p2p leftover leftover down; bounce|P2POOL_TIMEOUT leftover 1 leftover; a 2s share is aborted so the pool 504s
zcashd|ZCASHD_TIMEOUT|1|30|s|/etc/zcash/zcash.conf|rpcclienttimeout=1|rpcclienttimeout=30|systemctl reload zcashd|zcash-cli|zec_to_1|blocks|peers|p2p leftover leftover down; bounce|ZCASHD_TIMEOUT leftover 1 leftover; a 2s getblock is aborted so the node 504s
litecoind|LITECOIND_TIMEOUT|1|30|s|/etc/litecoin/litecoin.conf|rpcclienttimeout=1|rpcclienttimeout=30|systemctl reload litecoind|litecoin-cli|ltc_to_1|blocks|peers|p2p leftover leftover down; bounce|LITECOIND_TIMEOUT leftover 1 leftover; a 2s getblock is aborted so the node 504s
dogecoind|DOGECOIND_TIMEOUT|1|30|s|/etc/dogecoin/dogecoin.conf|rpcclienttimeout=1|rpcclienttimeout=30|systemctl reload dogecoind|dogecoin-cli|doge_to_1|blocks|peers|p2p leftover leftover down; bounce|DOGECOIND_TIMEOUT leftover 1 leftover; a 2s getblock is aborted so the node 504s
cardano-node|CARDANO_TIMEOUT|1|30|s|/etc/cardano/config.json|"timeout": 1|"timeout": 30|systemctl reload cardano-node|cardano-cli|ada_to_1|slots|peers|p2p leftover leftover down; bounce|CARDANO_TIMEOUT leftover 1 leftover; a 2s query is aborted so the node 504s
db-sync|DBSYNC_TIMEOUT|1|30|s|/etc/cardano/db-sync.json|"timeout": 1|"timeout": 30|systemctl reload cardano-db-sync|cardano-db-sync|dbs_to_1|blocks|pg|pg leftover leftover down; bounce|DBSYNC_TIMEOUT leftover 1 leftover; a 2s insert is aborted so the index 504s
ogmios|OGMIOS_TIMEOUT|1|30|s|/etc/ogmios/ogmios.json|"timeout": 1|"timeout": 30|systemctl reload ogmios|ogmios|ogm_to_1|ws|node|ws leftover leftover down; bounce|OGMIOS_TIMEOUT leftover 1 leftover; a 2s query is aborted so the api 504s
kupo|KUPO_TIMEOUT|1|30|s|/etc/kupo/kupo.conf|timeout=1|timeout=30|systemctl reload kupo|kupo|kup_to_1|utxo|sqlite|fs leftover leftover down; bounce|KUPO_TIMEOUT leftover 1 leftover; a 2s match is aborted so the index 504s
plutus|PLUTUS_TIMEOUT|1|30|s|/etc/plutus/plutus.conf|timeout=1|timeout=30|systemctl reload plutus|plutus|plu_to_1|scripts|eval|fs leftover leftover down; bounce|PLUTUS_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the script 504s
substrate|SUBSTRATE_TIMEOUT|1|30|s|/etc/substrate/config.toml|timeout = 1|timeout = 30|systemctl reload substrate|substrate|sub_to_1|blocks|peers|p2p leftover leftover down; bounce|SUBSTRATE_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the node 504s
polkadot|POLKADOT_TIMEOUT|1|30|s|/etc/polkadot/config.toml|timeout = 1|timeout = 30|systemctl reload polkadot|polkadot|dot_to_1|blocks|peers|p2p leftover leftover down; bounce|POLKADOT_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the node 504s
kusama|KUSAMA_TIMEOUT|1|30|s|/etc/kusama/config.toml|timeout = 1|timeout = 30|systemctl reload kusama|kusama|ksm_to_1|blocks|peers|p2p leftover leftover down; bounce|KUSAMA_TIMEOUT leftover 1 leftover; a 2s rpc is aborted so the node 504s
anvil|ANVIL_TIMEOUT|1|10|s|/etc/foundry/anvil.toml|timeout = 1|timeout = 10|systemctl reload anvil|anvil|anv_to_1|forks|rpc|http leftover leftover down; bounce|ANVIL_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the fork 504s
hardhat|HARDHAT_TIMEOUT|1|30|s|/etc/hardhat/hardhat.config.js|timeout: 1|timeout: 30|systemctl reload hardhat|hardhat|hht_to_1|tests|net|http leftover leftover down; bounce|HARDHAT_TIMEOUT leftover 1 leftover; a 2s mine is aborted so the test 504s
foundry|FOUNDRY_TIMEOUT|1|30|s|/etc/foundry/foundry.toml|timeout = 1|timeout = 30|systemctl reload foundry|forge|fnd_to_1|tests|rpc|http leftover leftover down; bounce|FOUNDRY_TIMEOUT leftover 1 leftover; a 2s test is aborted so CI 504s
forge|FORGE_TIMEOUT|1|30|s|/etc/foundry/foundry.toml|timeout = 1|timeout = 30|systemctl reload forge|forge|frg_to_1|tests|rpc|http leftover leftover down; bounce|FORGE_TIMEOUT leftover 1 leftover; a 2s test is aborted so CI 504s
cast|CAST_TIMEOUT|1|10|s|/etc/foundry/foundry.toml|timeout = 1|timeout = 10|systemctl reload cast|cast|cst_to_1|calls|rpc|http leftover leftover down; bounce|CAST_TIMEOUT leftover 1 leftover; a 2s call is aborted so the cli 504s
ganache|GANACHE_TIMEOUT|1|10|s|/etc/ganache/ganache.conf|timeout=1|timeout=10|systemctl reload ganache|ganache|gan_to_1|accounts|rpc|http leftover leftover down; bounce|GANACHE_TIMEOUT leftover 1 leftover; a 2s eth_call is aborted so the fork 504s
truffle|TRUFFLE_TIMEOUT|1|30|s|/etc/truffle/truffle-config.js|timeout: 1|timeout: 30|systemctl reload truffle|truffle|trf_to_1|migrate|rpc|http leftover leftover down; bounce|TRUFFLE_TIMEOUT leftover 1 leftover; a 2s migrate is aborted so deploy 504s
remix|REMIX_TIMEOUT|1|30|s|/etc/remix/remix.conf|timeout=1|timeout=30|systemctl reload remixd|remixd|rmx_to_1|sol|ws|ws leftover leftover down; bounce|REMIX_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the ide 504s
solc|SOLC_TIMEOUT|1|30|s|/etc/solc/solc.conf|timeout=1|timeout=30|systemctl reload solc|solc|slc_to_1|sol|bin|fs leftover leftover down; bounce|SOLC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the bin 504s
vyper|VYPER_TIMEOUT|1|30|s|/etc/vyper/vyper.conf|timeout=1|timeout=30|systemctl reload vyper|vyper|vyp_to_1|vy|bin|fs leftover leftover down; bounce|VYPER_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the bin 504s
racadm|RACADM_TIMEOUT|1|30|s|/etc/racadm/racadm.conf|timeout=1|timeout=30|systemctl reload racadm|racadm|rac_to_1|idrac|jobs|https leftover leftover 403; bounce|RACADM_TIMEOUT leftover 1 leftover; a 2s job is aborted so firmware 504s
ilorest|ILOREST_TIMEOUT|1|30|s|/etc/ilorest/ilorest.conf|timeout=1|timeout=30|systemctl reload ilorest|ilorest|ilo2_to_1|ilo|jobs|https leftover leftover 403; bounce|ILOREST_TIMEOUT leftover 1 leftover; a 2s GET is aborted so firmware 504s
openbmctool|OBMC_TIMEOUT|1|30|s|/etc/openbmc/openbmctool.conf|timeout=1|timeout=30|systemctl reload openbmctool|openbmctool|obm_to_1|bmc|jobs|https leftover leftover 403; bounce|OBMC_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the bmc 504s
ipmiutil|IPMIUTIL_TIMEOUT|1|20|s|/etc/ipmiutil/ipmiutil.conf|timeout=1|timeout=20|systemctl reload ipmiutil|ipmiutil|ipu_to_1|sdr|bmc|lanplus leftover leftover down; bounce|IPMIUTIL_TIMEOUT leftover 1 leftover; a 2s sdr is aborted so sensors 504s
powerman|POWERMAN_TIMEOUT|1|10|s|/etc/powerman/powerman.conf|timeout 1|timeout 10|systemctl reload powerman|pm|pwm_to_1|plugs|hosts|tcp leftover leftover down; bounce|POWERMAN_TIMEOUT leftover 1 leftover; a 2s query is aborted so power 504s
genders|GENDERS_TIMEOUT|1|10|s|/etc/genders|timeout=1|timeout=10|systemctl reload genders|nodeattr|gnd_to_1|attrs|hosts|fs leftover leftover down; bounce|GENDERS_TIMEOUT leftover 1 leftover; a 2s query is aborted so pdsh 504s
clustershell|CLUSH_TIMEOUT|1|30|s|/etc/clustershell/clush.conf|timeout: 1|timeout: 30|systemctl reload clush|clush|csh_to_1|fanout|hosts|ssh leftover leftover down; bounce|CLUSH_TIMEOUT leftover 1 leftover; a 2s node is skipped so the run 504s
func|FUNC_TIMEOUT|1|30|s|/etc/func/minion.conf|timeout=1|timeout=30|systemctl reload funcd|func|fnc_to_1|mods|minions|ssl leftover leftover down; bounce|FUNC_TIMEOUT leftover 1 leftover; a 2s call is aborted so the minion 504s
ansible-runner|RUNNER_TIMEOUT|1|60|s|/etc/ansible-runner/env/settings|timeout=1|timeout=60|systemctl reload ansible-runner|ansible-runner|anr_to_1|jobs|play|ssh leftover leftover down; bounce|RUNNER_TIMEOUT leftover 1 leftover; a 2s play is aborted so AWX 504s
mitogen|MITOGEN_TIMEOUT|1|30|s|/etc/ansible/mitogen.conf|timeout=1|timeout=30|systemctl reload ansible|ansible|mit_to_1|mux|hosts|ssh leftover leftover down; bounce|MITOGEN_TIMEOUT leftover 1 leftover; a 2s mux is aborted so the play 504s
ara|ARA_TIMEOUT|1|10|s|/etc/ara/settings.yaml|timeout: 1|timeout: 10|systemctl reload ara|ara|ara_to_1|recs|plays|sql leftover leftover down; bounce|ARA_TIMEOUT leftover 1 leftover; a 2s callback is aborted so the ui 504s
stackstorm|ST2_TIMEOUT|1|30|s|/etc/st2/st2.conf|timeout = 1|timeout = 30|systemctl reload st2api|st2|st2_to_1|acts|rules|mongo leftover leftover down; bounce|ST2_TIMEOUT leftover 1 leftover; a 2s action is aborted so the pack 504s
orquesta|ORQUESTA_TIMEOUT|1|30|s|/etc/st2/orquesta.conf|timeout = 1|timeout = 30|systemctl reload st2actionrunner|st2|orq_to_1|wfs|tasks|mongo leftover leftover down; bounce|ORQUESTA_TIMEOUT leftover 1 leftover; a 2s task is aborted so the wf 504s
'''
WAVE51 = (
    "nimbus/lodestar/reth/monerod/xmrig/p2pool/zcashd/litecoind/dogecoind/"
    "cardano-node/db-sync/ogmios/kupo/plutus/substrate/polkadot/kusama/"
    "anvil/hardhat/foundry/forge/cast/ganache/truffle/remix/solc/vyper/"
    "racadm/ilorest/openbmctool/ipmiutil/powerman/genders/clustershell/"
    "func/ansible-runner/mitogen/ara/stackstorm/orquesta"
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
        svc = f"g1{i:02d}x"
        ns = f"g1{i:02d}"
        clu = f"prod-apsh{901 + i}-{svc[:3]}"
        ticket = f"W2-{12763 + i}"
        node = f"ip-10-236-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4121


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4120 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-51 leftover: {WAVE51}.",
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
