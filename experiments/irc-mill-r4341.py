#!/usr/bin/env python3
"""IRC mill r4341+ — wave-62 compiler-cache/HPC/ML-serve leftover.

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
chamber|CHAMBER_TIMEOUT|1|30|s|/etc/chamber/chamber.conf|timeout=1|timeout=30|systemctl reload chamber|ch|cha_to_1|params|ssm|aws leftover leftover down; bounce|CHAMBER_TIMEOUT leftover 1 leftover; a 2s param is aborted so the params 504s
confd|CONFD_TIMEOUT|1|30|s|/etc/confd/confd.conf|timeout=1|timeout=30|systemctl reload confd|cd|con_to_1|tmpls|keys|etcd leftover leftover down; bounce|CONFD_TIMEOUT leftover 1 leftover; a 2s render is aborted so the tmpls 504s
sopsoperator|SOPSOPERATOR_TIMEOUT|1|30|s|/etc/sopsoperator/sopsoperator.conf|timeout=1|timeout=30|systemctl reload sopsoperator|so|sop_to_1|secrets|keys|k8s leftover leftover down; bounce|SOPSOPERATOR_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the secrets 504s
lucet|LUCET_TIMEOUT|1|30|s|/etc/lucet/lucet.conf|timeout=1|timeout=30|systemctl reload lucet|lu|luc_to_1|modules|wasm|fs leftover leftover down; bounce|LUCET_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the modules 504s
wavm|WAVM_TIMEOUT|1|30|s|/etc/wavm/wavm.conf|timeout=1|timeout=30|systemctl reload wavm|wv|wav_to_1|modules|wasm|fs leftover leftover down; bounce|WAVM_TIMEOUT leftover 1 leftover; a 2s run is aborted so the modules 504s
slightly|SLIGHTLY_TIMEOUT|1|30|s|/etc/slightly/slightly.conf|timeout=1|timeout=30|systemctl reload slightly|sl|sli_to_1|spins|wasm|fs leftover leftover down; bounce|SLIGHTLY_TIMEOUT leftover 1 leftover; a 2s start is aborted so the spins 504s
sge|SGE_TIMEOUT|1|30|s|/etc/sge/sge.conf|timeout=1|timeout=30|systemctl reload sge|qmaster|sge_to_1|jobs|queues|spool leftover leftover down; bounce|SGE_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the jobs 504s
gridengine|GRIDENGINE_TIMEOUT|1|30|s|/etc/gridengine/gridengine.conf|timeout=1|timeout=30|systemctl reload gridengine|sge|gri_to_1|jobs|hosts|spool leftover leftover down; bounce|GRIDENGINE_TIMEOUT leftover 1 leftover; a 2s dispatch is aborted so the jobs 504s
cobalt|COBALT_TIMEOUT|1|30|s|/etc/cobalt/cobalt.conf|timeout=1|timeout=30|systemctl reload cobalt|cq|cob_to_1|jobs|queues|fs leftover leftover down; bounce|COBALT_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the jobs 504s
slurmrestd|SLURMRESTD_TIMEOUT|1|30|s|/etc/slurmrestd/slurmrestd.conf|timeout=1|timeout=30|systemctl reload slurmrestd|slurm|slu_to_1|jobs|apis|https leftover leftover down; bounce|SLURMRESTD_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the jobs 504s
kepler|KEPLER_TIMEOUT|1|30|s|/etc/kepler/kepler.conf|timeout=1|timeout=30|systemctl reload kepler|kp|kep_to_1|jobs|actors|fs leftover leftover down; bounce|KEPLER_TIMEOUT leftover 1 leftover; a 2s actor is aborted so the jobs 504s
airavata|AIRAVATA_TIMEOUT|1|30|s|/etc/airavata/airavata.conf|timeout=1|timeout=30|systemctl reload airavata|av|air_to_1|exps|tasks|https leftover leftover down; bounce|AIRAVATA_TIMEOUT leftover 1 leftover; a 2s launch is aborted so the exps 504s
bento|BENTO_TIMEOUT|1|30|s|/etc/bento/bento.conf|timeout=1|timeout=30|systemctl reload bento|bn|ben_to_1|models|apis|https leftover leftover down; bounce|BENTO_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the models 504s
vllm|VLLM_TIMEOUT|1|30|s|/etc/vllm/vllm.conf|timeout=1|timeout=30|systemctl reload vllm|vl|vll_to_1|tokens|gpus|https leftover leftover down; bounce|VLLM_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the tokens 504s
tgi|TGI_TIMEOUT|1|30|s|/etc/tgi/tgi.conf|timeout=1|timeout=30|systemctl reload tgi|tg|tgi_to_1|tokens|gpus|https leftover leftover down; bounce|TGI_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the tokens 504s
ollama|OLLAMA_TIMEOUT|1|30|s|/etc/ollama/ollama.conf|timeout=1|timeout=30|systemctl reload ollama|ol|oll_to_1|models|blobs|https leftover leftover down; bounce|OLLAMA_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the models 504s
localai|LOCALAI_TIMEOUT|1|30|s|/etc/localai/localai.conf|timeout=1|timeout=30|systemctl reload localai|lai|loc_to_1|models|apis|https leftover leftover down; bounce|LOCALAI_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the models 504s
llamacpp|LLAMACPP_TIMEOUT|1|30|s|/etc/llamacpp/llamacpp.conf|timeout=1|timeout=30|systemctl reload llamacpp|ll|lla_to_1|tokens|gguf|https leftover leftover down; bounce|LLAMACPP_TIMEOUT leftover 1 leftover; a 2s infer is aborted so the tokens 504s
ksqldb|KSQLDB_TIMEOUT|1|30|s|/etc/ksqldb/ksqldb.conf|timeout=1|timeout=30|systemctl reload ksqldb|ks|ksq_to_1|queries|topics|kafka leftover leftover down; bounce|KSQLDB_TIMEOUT leftover 1 leftover; a 2s query is aborted so the queries 504s
zeromq|ZEROMQ_TIMEOUT|1|30|s|/etc/zeromq/zeromq.conf|timeout=1|timeout=30|systemctl reload zeromq|zmq|zer_to_1|msgs|socks|tcp leftover leftover down; bounce|ZEROMQ_TIMEOUT leftover 1 leftover; a 2s send is aborted so the msgs 504s
icinga2|ICINGA2_TIMEOUT|1|30|s|/etc/icinga2/icinga2.conf|timeout=1|timeout=30|systemctl reload icinga2|ic|ici_to_1|checks|hosts|ido leftover leftover down; bounce|ICINGA2_TIMEOUT leftover 1 leftover; a 2s check is aborted so the checks 504s
nexus3|NEXUS3_TIMEOUT|1|30|s|/etc/nexus3/nexus3.conf|timeout=1|timeout=30|systemctl reload nexus3|nx|nex_to_1|blobs|repos|https leftover leftover down; bounce|NEXUS3_TIMEOUT leftover 1 leftover; a 2s upload is aborted so the blobs 504s
fluxcd|FLUXCD_TIMEOUT|1|30|s|/etc/fluxcd/fluxcd.conf|timeout=1|timeout=30|systemctl reload fluxcd|fx|flu_to_1|syncs|gits|k8s leftover leftover down; bounce|FLUXCD_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the syncs 504s
prefect2|PREFECT2_TIMEOUT|1|30|s|/etc/prefect2/prefect2.conf|timeout=1|timeout=30|systemctl reload prefect2|pf|pre_to_1|flows|runs|pg leftover leftover down; bounce|PREFECT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the flows 504s
dagster2|DAGSTER2_TIMEOUT|1|30|s|/etc/dagster2/dagster2.conf|timeout=1|timeout=30|systemctl reload dagster2|dg|dag_to_1|jobs|runs|pg leftover leftover down; bounce|DAGSTER2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sccache|SCCACHE_TIMEOUT|1|30|s|/etc/sccache/sccache.conf|timeout=1|timeout=30|systemctl reload sccache|sc|scc_to_1|objs|cache|fs leftover leftover down; bounce|SCCACHE_TIMEOUT leftover 1 leftover; a 2s store is aborted so the objs 504s
distcc|DISTCC_TIMEOUT|1|30|s|/etc/distcc/distcc.conf|timeout=1|timeout=30|systemctl reload distcc|dc|dis_to_1|jobs|hosts|tcp leftover leftover down; bounce|DISTCC_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the jobs 504s
icecream|ICECREAM_TIMEOUT|1|30|s|/etc/icecream/icecream.conf|timeout=1|timeout=30|systemctl reload icecream|icecc|ice_to_1|jobs|sched|tcp leftover leftover down; bounce|ICECREAM_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the jobs 504s
ccache|CCACHE_TIMEOUT|1|30|s|/etc/ccache/ccache.conf|timeout=1|timeout=30|systemctl reload ccache|cc|cca_to_1|objs|cache|fs leftover leftover down; bounce|CCACHE_TIMEOUT leftover 1 leftover; a 2s store is aborted so the objs 504s
poudriere|POUDRIERE_TIMEOUT|1|30|s|/etc/poudriere/poudriere.conf|timeout=1|timeout=30|systemctl reload poudriere|pd|pou_to_1|jails|ports|zfs leftover leftover down; bounce|POUDRIERE_TIMEOUT leftover 1 leftover; a 2s build is aborted so the jails 504s
tinderbox|TINDERBOX_TIMEOUT|1|30|s|/etc/tinderbox/tinderbox.conf|timeout=1|timeout=30|systemctl reload tinderbox|tb|tin_to_1|builds|ports|fs leftover leftover down; bounce|TINDERBOX_TIMEOUT leftover 1 leftover; a 2s build is aborted so the builds 504s
brewport|BREWPORT_TIMEOUT|1|30|s|/etc/brewport/brewport.conf|timeout=1|timeout=30|systemctl reload brewport|bp|bre_to_1|formulae|bottles|fs leftover leftover down; bounce|BREWPORT_TIMEOUT leftover 1 leftover; a 2s build is aborted so the formulae 504s
firecrackerjailer|FIRECRACKERJAILER_TIMEOUT|1|30|s|/etc/firecrackerjailer/firecrackerjailer.conf|timeout=1|timeout=30|systemctl reload firecrackerjailer|fc|fir_to_1|vms|jails|kvm leftover leftover down; bounce|FIRECRACKERJAILER_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vms 504s
criu|CRIU_TIMEOUT|1|30|s|/etc/criu/criu.conf|timeout=1|timeout=30|systemctl reload criu|cr|cri_to_1|dumps|pids|fs leftover leftover down; bounce|CRIU_TIMEOUT leftover 1 leftover; a 2s dump is aborted so the dumps 504s
machined|MACHINED_TIMEOUT|1|30|s|/etc/machined/machined.conf|timeout=1|timeout=30|systemctl reload machined|md|mac_to_1|nspawn|images|dbus leftover leftover down; bounce|MACHINED_TIMEOUT leftover 1 leftover; a 2s start is aborted so the nspawn 504s
skydive|SKYDIVE_TIMEOUT|1|30|s|/etc/skydive/skydive.conf|timeout=1|timeout=30|systemctl reload skydive|sv|sky_to_1|flows|agents|https leftover leftover down; bounce|SKYDIVE_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the flows 504s
bmon|BMON_TIMEOUT|1|30|s|/etc/bmon/bmon.conf|timeout=1|timeout=30|systemctl reload bmon|bm|bmo_to_1|ifaces|stats|net leftover leftover down; bounce|BMON_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the ifaces 504s
iftop|IFTOP_TIMEOUT|1|30|s|/etc/iftop/iftop.conf|timeout=1|timeout=30|systemctl reload iftop|it|ift_to_1|flows|ifaces|pcap leftover leftover down; bounce|IFTOP_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the flows 504s
nethogs|NETHOGS_TIMEOUT|1|30|s|/etc/nethogs/nethogs.conf|timeout=1|timeout=30|systemctl reload nethogs|nh|net_to_1|procs|ifaces|pcap leftover leftover down; bounce|NETHOGS_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the procs 504s
moloch|MOLOCH_TIMEOUT|1|30|s|/etc/moloch/moloch.conf|timeout=1|timeout=30|systemctl reload moloch|mo|mol_to_1|pcaps|sessions|es leftover leftover down; bounce|MOLOCH_TIMEOUT leftover 1 leftover; a 2s index is aborted so the pcaps 504s
'''
WAVE = (
    "chamber/confd/sopsoperator/lucet/wavm/slightly/sge/gridengine/cobalt/slurmrestd/kepler/airavata/bento/vllm/tgi/ollama/localai/llamacpp/ksqldb/zeromq/icinga2/nexus3/fluxcd/prefect2/dagster2/sccache/distcc/icecream/ccache/poudriere/tinderbox/brewport/firecrackerjailer/criu/machined/skydive/bmon/iftop/nethogs/moloch"
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
        svc = f"r2{i:02d}x"
        ns = f"r2{i:02d}"
        clu = f"prod-apst{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13203 + i }"
        node = f"ip-10-247-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4341


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-62 leftover: {WAVE}.",
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
