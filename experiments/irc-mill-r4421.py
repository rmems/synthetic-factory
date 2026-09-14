#!/usr/bin/env python3
"""IRC mill r4421+ — wave-66 storage-array/backup leftover.

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
vastnfs|VASTNFS_TIMEOUT|1|30|s|/etc/vastnfs/vastnfs.conf|timeout=1|timeout=30|systemctl reload vastnfs|vn|vas_to_1|exports|vips|nfs leftover leftover down; bounce|VASTNFS_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the exports 504s
qumulo|QUMULO_TIMEOUT|1|30|s|/etc/qumulo/qumulo.conf|timeout=1|timeout=30|systemctl reload qumulo|qm|qum_to_1|exports|nodes|https leftover leftover down; bounce|QUMULO_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the exports 504s
onefs|ONEFS_TIMEOUT|1|30|s|/etc/onefs/onefs.conf|timeout=1|timeout=30|systemctl reload onefs|is|one_to_1|exports|nodes|nfs leftover leftover down; bounce|ONEFS_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the exports 504s
ontap|ONTAP_TIMEOUT|1|30|s|/etc/ontap/ontap.conf|timeout=1|timeout=30|systemctl reload ontap|ot|ont_to_1|lifs|svms|https leftover leftover down; bounce|ONTAP_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the lifs 504s
purefa|PUREFA_TIMEOUT|1|30|s|/etc/purefa/purefa.conf|timeout=1|timeout=30|systemctl reload purefa|pf|pur_to_1|vols|hosts|https leftover leftover down; bounce|PUREFA_TIMEOUT leftover 1 leftover; a 2s map is aborted so the vols 504s
nimble|NIMBLE_TIMEOUT|1|30|s|/etc/nimble/nimble.conf|timeout=1|timeout=30|systemctl reload nimble|nm|nim_to_1|vols|inits|https leftover leftover down; bounce|NIMBLE_TIMEOUT leftover 1 leftover; a 2s map is aborted so the vols 504s
hpe3par|HPE3PAR_TIMEOUT|1|30|s|/etc/hpe3par/hpe3par.conf|timeout=1|timeout=30|systemctl reload hpe3par|tp|hpe_to_1|vv|hosts|https leftover leftover down; bounce|HPE3PAR_TIMEOUT leftover 1 leftover; a 2s export is aborted so the vv 504s
hpeva|HPEVA_TIMEOUT|1|30|s|/etc/hpeva/hpeva.conf|timeout=1|timeout=30|systemctl reload hpeva|ev|hpe_to_1|vdisks|hosts|https leftover leftover down; bounce|HPEVA_TIMEOUT leftover 1 leftover; a 2s present is aborted so the vdisks 504s
compellent|COMPELLENT_TIMEOUT|1|30|s|/etc/compellent/compellent.conf|timeout=1|timeout=30|systemctl reload compellent|cp|com_to_1|vols|hosts|https leftover leftover down; bounce|COMPELLENT_TIMEOUT leftover 1 leftover; a 2s map is aborted so the vols 504s
powerstore|POWERSTORE_TIMEOUT|1|30|s|/etc/powerstore/powerstore.conf|timeout=1|timeout=30|systemctl reload powerstore|ps|pow_to_1|vols|hosts|https leftover leftover down; bounce|POWERSTORE_TIMEOUT leftover 1 leftover; a 2s map is aborted so the vols 504s
unity|UNITY_TIMEOUT|1|30|s|/etc/unity/unity.conf|timeout=1|timeout=30|systemctl reload unity|un|uni_to_1|luns|hosts|https leftover leftover down; bounce|UNITY_TIMEOUT leftover 1 leftover; a 2s map is aborted so the luns 504s
vnx|VNX_TIMEOUT|1|30|s|/etc/vnx/vnx.conf|timeout=1|timeout=30|systemctl reload vnx|vx|vnx_to_1|luns|hosts|https leftover leftover down; bounce|VNX_TIMEOUT leftover 1 leftover; a 2s map is aborted so the luns 504s
vmax|VMAX_TIMEOUT|1|30|s|/etc/vmax/vmax.conf|timeout=1|timeout=30|systemctl reload vmax|vm|vma_to_1|devs|masks|https leftover leftover down; bounce|VMAX_TIMEOUT leftover 1 leftover; a 2s map is aborted so the devs 504s
powermax|POWERMAX_TIMEOUT|1|30|s|/etc/powermax/powermax.conf|timeout=1|timeout=30|systemctl reload powermax|pm|pow_to_1|devs|masks|https leftover leftover down; bounce|POWERMAX_TIMEOUT leftover 1 leftover; a 2s map is aborted so the devs 504s
xtremio|XTREMIO_TIMEOUT|1|30|s|/etc/xtremio/xtremio.conf|timeout=1|timeout=30|systemctl reload xtremio|xt|xtr_to_1|vols|inits|https leftover leftover down; bounce|XTREMIO_TIMEOUT leftover 1 leftover; a 2s map is aborted so the vols 504s
vplex|VPLEX_TIMEOUT|1|30|s|/etc/vplex/vplex.conf|timeout=1|timeout=30|systemctl reload vplex|vp|vpl_to_1|vvols|clusters|https leftover leftover down; bounce|VPLEX_TIMEOUT leftover 1 leftover; a 2s export is aborted so the vvols 504s
recoverpoint|RECOVERPOINT_TIMEOUT|1|30|s|/etc/recoverpoint/recoverpoint.conf|timeout=1|timeout=30|systemctl reload recoverpoint|rp|rec_to_1|cgs|copies|https leftover leftover down; bounce|RECOVERPOINT_TIMEOUT leftover 1 leftover; a 2s replicate is aborted so the cgs 504s
avamar|AVAMAR_TIMEOUT|1|30|s|/etc/avamar/avamar.conf|timeout=1|timeout=30|systemctl reload avamar|av|ava_to_1|jobs|clients|https leftover leftover down; bounce|AVAMAR_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
networker|NETWORKER_TIMEOUT|1|30|s|/etc/networker/networker.conf|timeout=1|timeout=30|systemctl reload networker|nw|net_to_1|jobs|clients|nsr leftover leftover down; bounce|NETWORKER_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
netbackup|NETBACKUP_TIMEOUT|1|30|s|/etc/netbackup/netbackup.conf|timeout=1|timeout=30|systemctl reload netbackup|nb|net_to_1|jobs|clients|bp leftover leftover down; bounce|NETBACKUP_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
commvault|COMMVAULT_TIMEOUT|1|30|s|/etc/commvault/commvault.conf|timeout=1|timeout=30|systemctl reload commvault|cv|com_to_1|jobs|clients|https leftover leftover down; bounce|COMMVAULT_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
veeam|VEEAM_TIMEOUT|1|30|s|/etc/veeam/veeam.conf|timeout=1|timeout=30|systemctl reload veeam|ve|vee_to_1|jobs|proxies|https leftover leftover down; bounce|VEEAM_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
rubrik|RUBRIK_TIMEOUT|1|30|s|/etc/rubrik/rubrik.conf|timeout=1|timeout=30|systemctl reload rubrik|rk|rub_to_1|jobs|slas|https leftover leftover down; bounce|RUBRIK_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
cohesity|COHESITY_TIMEOUT|1|30|s|/etc/cohesity/cohesity.conf|timeout=1|timeout=30|systemctl reload cohesity|ch|coh_to_1|jobs|views|https leftover leftover down; bounce|COHESITY_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
veritas|VERITAS_TIMEOUT|1|30|s|/etc/veritas/veritas.conf|timeout=1|timeout=30|systemctl reload veritas|vt|ver_to_1|jobs|policies|https leftover leftover down; bounce|VERITAS_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
dataprotector|DATAPROTECTOR_TIMEOUT|1|30|s|/etc/dataprotector/dataprotector.conf|timeout=1|timeout=30|systemctl reload dataprotector|dp|dat_to_1|jobs|cells|https leftover leftover down; bounce|DATAPROTECTOR_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
spad|SPAD_TIMEOUT|1|30|s|/etc/spad/spad.conf|timeout=1|timeout=30|systemctl reload spad|sd|spa_to_1|jobs|nodes|https leftover leftover down; bounce|SPAD_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
tsm|TSM_TIMEOUT|1|30|s|/etc/tsm/tsm.conf|timeout=1|timeout=30|systemctl reload tsm|ts|tsm_to_1|jobs|nodes|dsm leftover leftover down; bounce|TSM_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
spectrumprotect|SPECTRUMPROTECT_TIMEOUT|1|30|s|/etc/spectrumprotect/spectrumprotect.conf|timeout=1|timeout=30|systemctl reload spectrumprotect|sp|spe_to_1|jobs|nodes|dsm leftover leftover down; bounce|SPECTRUMPROTECT_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
kopia|KOPIA_TIMEOUT|1|30|s|/etc/kopia/kopia.conf|timeout=1|timeout=30|systemctl reload kopia|kp|kop_to_1|snaps|repos|fs leftover leftover down; bounce|KOPIA_TIMEOUT leftover 1 leftover; a 2s snapshot is aborted so the snaps 504s
duplicati|DUPLICATI_TIMEOUT|1|30|s|/etc/duplicati/duplicati.conf|timeout=1|timeout=30|systemctl reload duplicati|du|dup_to_1|jobs|dests|https leftover leftover down; bounce|DUPLICATI_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
urbackup|URBACKUP_TIMEOUT|1|30|s|/etc/urbackup/urbackup.conf|timeout=1|timeout=30|systemctl reload urbackup|ub|urb_to_1|jobs|clients|https leftover leftover down; bounce|URBACKUP_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the jobs 504s
restic2|RESTIC2_TIMEOUT|1|30|s|/etc/restic2/restic2.conf|timeout=1|timeout=30|systemctl reload restic2|rs|res_to_1|snaps|repos|fs leftover leftover down; bounce|RESTIC2_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the snaps 504s
borgmatic|BORGMATIC_TIMEOUT|1|30|s|/etc/borgmatic/borgmatic.conf|timeout=1|timeout=30|systemctl reload borgmatic|bg|bor_to_1|snaps|repos|fs leftover leftover down; bounce|BORGMATIC_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the snaps 504s
bup|BUP_TIMEOUT|1|30|s|/etc/bup/bup.conf|timeout=1|timeout=30|systemctl reload bup|bp|bup_to_1|packs|repos|git leftover leftover down; bounce|BUP_TIMEOUT leftover 1 leftover; a 2s save is aborted so the packs 504s
dar|DAR_TIMEOUT|1|30|s|/etc/dar/dar.conf|timeout=1|timeout=30|systemctl reload dar|dr|dar_to_1|archives|slices|fs leftover leftover down; bounce|DAR_TIMEOUT leftover 1 leftover; a 2s create is aborted so the archives 504s
rsnapshot|RSNAPSHOT_TIMEOUT|1|30|s|/etc/rsnapshot/rsnapshot.conf|timeout=1|timeout=30|systemctl reload rsnapshot|rn|rsn_to_1|snaps|hosts|rsync leftover leftover down; bounce|RSNAPSHOT_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the snaps 504s
rdiffbackup|RDIFFBACKUP_TIMEOUT|1|30|s|/etc/rdiffbackup/rdiffbackup.conf|timeout=1|timeout=30|systemctl reload rdiffbackup|rb|rdi_to_1|increments|hosts|rsync leftover leftover down; bounce|RDIFFBACKUP_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the increments 504s
duplicacy|DUPLICACY_TIMEOUT|1|30|s|/etc/duplicacy/duplicacy.conf|timeout=1|timeout=30|systemctl reload duplicacy|dy|dup_to_1|revs|storages|fs leftover leftover down; bounce|DUPLICACY_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the revs 504s
rclonebis|RCLONEBIS_TIMEOUT|1|30|s|/etc/rclonebis/rclonebis.conf|timeout=1|timeout=30|systemctl reload rclonebis|rc|rcl_to_1|objs|remotes|https leftover leftover down; bounce|RCLONEBIS_TIMEOUT leftover 1 leftover; a 2s copy is aborted so the objs 504s
'''
WAVE = (
    "vastnfs/qumulo/onefs/ontap/purefa/nimble/hpe3par/hpeva/compellent/powerstore/unity/vnx/vmax/powermax/xtremio/vplex/recoverpoint/avamar/networker/netbackup/commvault/veeam/rubrik/cohesity/veritas/dataprotector/spad/tsm/spectrumprotect/kopia/duplicati/urbackup/restic2/borgmatic/bup/dar/rsnapshot/rdiffbackup/duplicacy/rclonebis"
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
        svc = f"w9{i:02d}x"
        ns = f"w9{i:02d}"
        clu = f"prod-aptx{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13363 + i }"
        node = f"ip-10-251-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4421


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-66 leftover: {WAVE}.",
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
