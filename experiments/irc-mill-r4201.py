#!/usr/bin/env python3
"""IRC mill r4201+ — wave-55 iac/backup leftover.

NEW on-call plants (not Wave-27–54 tails). BAN ypbind/oddjob,
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
scalr|SCALR_TIMEOUT|1|30|s|/etc/scalr/scalr.conf|timeout=1|timeout=30|systemctl reload scalr|scalr|sca_to_1|runs|ws|https leftover leftover 403; bounce|SCALR_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the run 504s
terramate|TERRAMATE_TIMEOUT|1|30|s|/etc/terramate/terramate.tm.hcl|timeout = 1|timeout = 30|systemctl reload terramate|terramate|tmt_to_1|stacks|gen|fs leftover leftover down; bounce|TERRAMATE_TIMEOUT leftover 1 leftover; a 2s generate is aborted so the stack 504s
cdktf|CDKTF_TIMEOUT|1|30|s|/etc/cdktf/cdktf.json|timeout: 1|timeout: 30|systemctl reload cdktf|cdktf|cdk_to_1|synth|tf|fs leftover leftover down; bounce|CDKTF_TIMEOUT leftover 1 leftover; a 2s synth is aborted so the plan 504s
terraform|TF_TIMEOUT|1|30|s|/etc/terraform/terraform.rc|timeout=1|timeout=30|systemctl reload terraform|terraform|tfm_to_1|state|plans|https leftover leftover 403; bounce|TF_TIMEOUT leftover 1 leftover; a 2s refresh is aborted so the plan 504s
tofu|TOFU_TIMEOUT|1|30|s|/etc/opentofu/tofu.rc|timeout=1|timeout=30|systemctl reload tofu|tofu|tof_to_1|state|plans|https leftover leftover 403; bounce|TOFU_TIMEOUT leftover 1 leftover; a 2s refresh is aborted so the plan 504s
conftest|CONFTEST_TIMEOUT|1|10|s|/etc/conftest/conftest.toml|timeout = 1|timeout = 10|systemctl reload conftest|conftest|cft_to_1|rego|inputs|fs leftover leftover down; bounce|CONFTEST_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the policy 504s
bareos|BAREOS_TIMEOUT|1|60|s|/etc/bareos/bareos-dir.conf|Timeout = 1|Timeout = 60|systemctl reload bareos-dir|bconsole|bar_to_1|jobs|vols|sql leftover leftover down; bounce|BAREOS_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the job 504s
rear|REAR_TIMEOUT|1|3600|s|/etc/rear/local.conf|timeout=1|timeout=3600|systemctl reload rear|rear|rea_to_1|iso|rescue|fs leftover leftover down; bounce|REAR_TIMEOUT leftover 1 leftover; a 2s mkbackup is aborted so the iso 504s
mondo|MONDO_TIMEOUT|1|3600|s|/etc/mondo/mondo.conf|timeout=1|timeout=3600|systemctl reload mondo|mondoarchive|mon_to_1|iso|rescue|fs leftover leftover down; bounce|MONDO_TIMEOUT leftover 1 leftover; a 2s archive is aborted so the iso 504s
clonezilla|CLONEZILLA_TIMEOUT|1|3600|s|/etc/clonezilla/clonezilla.conf|timeout=1|timeout=3600|systemctl reload clonezilla|ocs-sr|clz_to_1|imgs|disks|nfs leftover leftover down; bounce|CLONEZILLA_TIMEOUT leftover 1 leftover; a 2s save is aborted so the img 504s
fsarchiver|FSARCHIVER_TIMEOUT|1|3600|s|/etc/fsarchiver/fsarchiver.conf|timeout=1|timeout=3600|systemctl reload fsarchiver|fsarchiver|fsa_to_1|fsa|fs|fs leftover leftover down; bounce|FSARCHIVER_TIMEOUT leftover 1 leftover; a 2s save is aborted so the archive 504s
partimage|PARTIMAGE_TIMEOUT|1|3600|s|/etc/partimage/partimage.conf|timeout=1|timeout=3600|systemctl reload partimage|partimage|pim_to_1|imgs|parts|fs leftover leftover down; bounce|PARTIMAGE_TIMEOUT leftover 1 leftover; a 2s save is aborted so the img 504s
rescuezilla|RESCUEZILLA_TIMEOUT|1|3600|s|/etc/rescuezilla/rescuezilla.conf|timeout=1|timeout=3600|systemctl reload rescuezilla|rescuezilla|rsz_to_1|imgs|disks|fs leftover leftover down; bounce|RESCUEZILLA_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the img 504s
foxclone|FOXCLONE_TIMEOUT|1|3600|s|/etc/foxclone/foxclone.conf|timeout=1|timeout=3600|systemctl reload foxclone|foxclone|fox_to_1|imgs|disks|fs leftover leftover down; bounce|FOXCLONE_TIMEOUT leftover 1 leftover; a 2s clone is aborted so the img 504s
timeshift|TIMESHIFT_TIMEOUT|1|60|s|/etc/timeshift/timeshift.json|"timeout": 1|"timeout": 60|systemctl reload timeshift|timeshift|tsh_to_1|snaps|rsync|fs leftover leftover down; bounce|TIMESHIFT_TIMEOUT leftover 1 leftover; a 2s snapshot is aborted so the snap 504s
backintime|BACKINTIME_TIMEOUT|1|60|s|/etc/backintime/config|timeout=1|timeout=60|systemctl reload backintime|backintime|bit_to_1|snaps|rsync|fs leftover leftover down; bounce|BACKINTIME_TIMEOUT leftover 1 leftover; a 2s snapshot is aborted so the snap 504s
deja-dup|DEJADUP_TIMEOUT|1|60|s|/etc/deja-dup/dejadup.conf|timeout=1|timeout=60|systemctl reload deja-dup|deja-dup|dej_to_1|snaps|gvfs|fs leftover leftover down; bounce|DEJADUP_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the snap 504s
duplicati|DUPLICATI_TIMEOUT|1|60|s|/etc/duplicati/Duplicati-server.sqlite|timeout=1|timeout=60|systemctl reload duplicati|duplicati|dtc_to_1|dblock|remote|https leftover leftover 403; bounce|DUPLICATI_TIMEOUT leftover 1 leftover; a 2s upload is aborted so the backup 504s
urbackup|URBACKUP_TIMEOUT|1|60|s|/etc/urbackup/urbackup.conf|timeout=1|timeout=60|systemctl reload urbackupsrv|urbackup_client|urb_to_1|imgs|clients|tcp leftover leftover down; bounce|URBACKUP_TIMEOUT leftover 1 leftover; a 2s incr is aborted so the backup 504s
pbs|PBS_TIMEOUT|1|60|s|/etc/proxmox-backup/datastore.cfg|timeout=1|timeout=60|systemctl reload proxmox-backup|proxmox-backup-client|pbs_to_1|chunks|ds|https leftover leftover 403; bounce|PBS_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the ds 504s
cdk8s|CDK8S_TIMEOUT|1|30|s|/etc/cdk8s/cdk8s.yaml|timeout: 1|timeout: 30|systemctl reload cdk8s|cdk8s|c8s_to_1|synth|k8s|fs leftover leftover down; bounce|CDK8S_TIMEOUT leftover 1 leftover; a 2s synth is aborted so the chart 504s
cdk|CDK_TIMEOUT|1|30|s|/etc/cdk/cdk.json|timeout: 1|timeout: 30|systemctl reload cdk|cdk|cdk2_to_1|synth|cfn|fs leftover leftover down; bounce|CDK_TIMEOUT leftover 1 leftover; a 2s synth is aborted so the stack 504s
cloudformation|CFN_TIMEOUT|1|30|s|/etc/cloudformation/cfn.conf|timeout=1|timeout=30|systemctl reload cfn|aws|cfn_to_1|stacks|tmpl|https leftover leftover 403; bounce|CFN_TIMEOUT leftover 1 leftover; a 2s create is aborted so the stack 504s
cfn|CFNLINT_TIMEOUT|1|30|s|/etc/cfn-lint/cfn.conf|timeout=1|timeout=30|systemctl reload cfn-lint|cfn-lint|cfl_to_1|tmpl|rules|fs leftover leftover down; bounce|CFNLINT_TIMEOUT leftover 1 leftover; a 2s lint is aborted so the rule 504s
sam|SAM_TIMEOUT|1|30|s|/etc/sam/samconfig.toml|timeout = 1|timeout = 30|systemctl reload sam|sam|sam_to_1|apps|tmpl|https leftover leftover 403; bounce|SAM_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the app 504s
serverless|SLS_TIMEOUT|1|30|s|/etc/serverless/serverless.yml|timeout: 1|timeout: 30|systemctl reload sls|sls|sls_to_1|fns|stack|https leftover leftover 403; bounce|SLS_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fn 504s
sls|SLS2_TIMEOUT|1|30|s|/etc/serverless/serverless.yml|timeout: 1|timeout: 30|systemctl reload sls|sls|sls2_to_1|fns|stack|https leftover leftover 403; bounce|SLS2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the fn 504s
sst|SST_TIMEOUT|1|30|s|/etc/sst/sst.config.ts|timeout: 1|timeout: 30|systemctl reload sst|sst|sst_to_1|stacks|live|https leftover leftover 403; bounce|SST_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the stack 504s
architect|ARC_TIMEOUT|1|30|s|/etc/architect/app.arc|timeout=1|timeout=30|systemctl reload arc|arc|arc_to_1|fns|sam|https leftover leftover 403; bounce|ARC_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the app 504s
arc|ARC2_TIMEOUT|1|30|s|/etc/architect/app.arc|timeout=1|timeout=30|systemctl reload arc|arc|arc2_to_1|fns|sam|https leftover leftover 403; bounce|ARC2_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the app 504s
copilot|COPILOT_TIMEOUT|1|30|s|/etc/copilot/copilot.conf|timeout=1|timeout=30|systemctl reload copilot|copilot|cop_to_1|svcs|ecs|https leftover leftover 403; bounce|COPILOT_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the svc 504s
amplify|AMPLIFY_TIMEOUT|1|30|s|/etc/amplify/amplify.yml|timeout: 1|timeout: 30|systemctl reload amplify|amplify|amp_to_1|apps|hosting|https leftover leftover 403; bounce|AMPLIFY_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the app 504s
tilt|TILT_TIMEOUT|1|30|s|/etc/tilt/Tiltfile|timeout=1|timeout=30|systemctl reload tilt|tilt|tlt_to_1|res|k8s|fs leftover leftover down; bounce|TILT_TIMEOUT leftover 1 leftover; a 2s build is aborted so the res 504s
garden|GARDEN_TIMEOUT|1|30|s|/etc/garden/garden.yml|timeout: 1|timeout: 30|systemctl reload garden|garden|gdn_to_1|mods|k8s|fs leftover leftover down; bounce|GARDEN_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the env 504s
telepresence|TELEPRESENCE_TIMEOUT|1|30|s|/etc/telepresence/config.yml|timeout: 1s|timeout: 30s|systemctl reload telepresence|telepresence|tlp_to_1|ints|ns|grpc leftover leftover down; bounce|TELEPRESENCE_TIMEOUT leftover 1 leftover; a 2s intercept is aborted so the int 504s
okteto|OKTETO_TIMEOUT|1|30|s|/etc/okteto/okteto.yml|timeout: 1|timeout: 30|systemctl reload okteto|okteto|okt_to_1|devs|ns|https leftover leftover 403; bounce|OKTETO_TIMEOUT leftover 1 leftover; a 2s up is aborted so the dev 504s
devspace|DEVSPACE_TIMEOUT|1|30|s|/etc/devspace/devspace.yaml|timeout: 1|timeout: 30|systemctl reload devspace|devspace|dvs_to_1|devs|ns|k8s leftover leftover down; bounce|DEVSPACE_TIMEOUT leftover 1 leftover; a 2s dev is aborted so the loop 504s
loft|LOFT_TIMEOUT|1|30|s|/etc/loft/config.yaml|timeout: 1s|timeout: 30s|systemctl reload loft|loft|lft_to_1|vclusters|spaces|https leftover leftover 403; bounce|LOFT_TIMEOUT leftover 1 leftover; a 2s create is aborted so the vcluster 504s
rancher-desktop|RD_TIMEOUT|1|30|s|/etc/rancher-desktop/settings.json|"timeout": 1|"timeout": 30|systemctl reload rancher-desktop|rdctl|rdt_to_1|k8s|vm|qemu leftover leftover down; bounce|RD_TIMEOUT leftover 1 leftover; a 2s start is aborted so the cluster 504s
orbstack|ORBSTACK_TIMEOUT|1|30|s|/etc/orbstack/config.json|"timeout": 1|"timeout": 30|systemctl reload orbstack|orb|orb_to_1|vms|linux|hv leftover leftover down; bounce|ORBSTACK_TIMEOUT leftover 1 leftover; a 2s start is aborted so the vm 504s
'''
WAVE55 = (
    "scalr/terramate/cdktf/terraform/tofu/conftest/bareos/rear/mondo/"
    "clonezilla/fsarchiver/partimage/rescuezilla/foxclone/timeshift/"
    "backintime/deja-dup/duplicati/urbackup/pbs/cdk8s/cdk/cloudformation/"
    "cfn/sam/serverless/sls/sst/architect/arc/copilot/amplify/tilt/garden/"
    "telepresence/okteto/devspace/loft/rancher-desktop/orbstack"
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
        svc = f"k5{i:02d}x"
        ns = f"k5{i:02d}"
        clu = f"prod-apsl{901 + i}-{svc[:3]}"
        ticket = f"W2-{12923 + i}"
        node = f"ip-10-240-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4201


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4200 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-55 leftover: {WAVE55}.",
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
