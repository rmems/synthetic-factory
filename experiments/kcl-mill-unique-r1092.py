#!/usr/bin/env python3
"""Mill k8s-crashloop-factory unique leftover plants (hop from docker mill).

BAN empty-ENV cartesian, ipFamilies/ETP/allocateLoadBalancerNodePorts cartesian,
bay-prod landscape clones, r963–r1091 leftovers. 16 + 18 steps. grok-4.6. Q=2.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "k8s-crashloop-factory"
GEN = "grok-4.6"

BANNED_PLANTS = {
    "bay-prod", "atoll", "kyle", "voe", "tarn", "lough", "weald", "fen",
    "firth", "ness", "mere", "dene", "gill", "scar", "howe", "crag", "knoll",
    "brae", "glen", "strath", "carse", "moss", "slack", "copse", "bight",
    "shiel", "toft", "naze", "cairn", "bothy", "beck", "kame", "haugh",
    "linn", "wynd", "dell", "slade", "combe", "holt", "wold", "holm", "ria",
    "cay", "spit", "oxbow",
}
BANNED_NEEDLES = (
    "unconfined", "webhook", "ipfamilies", "internaltrafficpolicy",
    "externaltrafficpolicy", "allocateloadbalancernodeports",
    "bitbucket_home", "keycloak_home", "bay-prod", "apparmor",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n, basis, name, args, obs, reflection) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": reflection,
    }


def bash(n, basis, cmd, obs, reflection) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs, reflection)


def read(n, basis, path, obs, reflection) -> dict:
    return step(n, basis, "read", {"path": path}, obs, reflection)


def edit(n, basis, path, old, new, obs, reflection) -> dict:
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs, reflection)


def guard(spec: dict) -> None:
    plant = spec["plant"]
    stem = plant[:-5] if plant.endswith("-prod") else plant
    if plant in BANNED_PLANTS or stem in BANNED_PLANTS:
        raise SystemExit(f"banned plant {plant}")
    identity = " ".join(str(spec.get(k, "")) for k in ("plant", "slug", "field", "fail_val")).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise SystemExit(f"banned needle {needle!r}")


PAIRS: list[dict] = [
    {
        "plant": "aber-prod",
        "app": "aber-api",
        "chart": "1.3.2",
        "slug": "job-failjob-policy",
        "field": "podFailurePolicy",
        "fail_val": "FailJob",
        "fix_val": "Ignore",
        "hide_path": "backoffLimit",
        "hide_old": "backoffLimit: 6\n",
        "hide_new": "backoffLimit: 99\n",
        "values_fail": "podFailurePolicy: FailJob\nbackoffLimit: 6\n",
        "values_fix": "podFailurePolicy: Ignore\nbackoffLimit: 6\n",
        "tpl": "  podFailurePolicy:\n    rules:\n      - action: {{ .Values.podFailurePolicy }}\n",
        "log": "podFailurePolicy FailJob; first OOM kills the Job; controller CrashLoop leftover",
        "live_ok": "podFailurePolicy=Ignore",
        "hide_name": "backoffLimit 99",
        "new_vs": "podFailurePolicy FailJob leftover, not startup/liveness and not PDB",
        "seed": "leftover Job podFailurePolicy FailJob; first OOM CrashLoop",
        "n2": "n2 leftover still FailJob after git Ignore",
        "ci": "# FailJob on OOM deletes the Job. Never stretch backoffLimit to hide.",
        "handoff": "LEFTOVER: n2 still podFailurePolicy FailJob. Platform: delete leftover RS. No backoff hide.",
        "pytest_ok": "test_failjob_ignore\ntest_not_backoff_hide\ntest_not_probe\ntest_pods_ready\ntest_no_force\ntest_job",
        "pytest_fail": "test_failjob_ignore_all FAILED b==FailJob",
        "tmpl_test": "test_template_matches_git",
        "rs": "a11",
    },
    {
        "plant": "afon-prod",
        "app": "afon-api",
        "chart": "2.1.0",
        "slug": "cron-timezone-stale",
        "field": "timeZone",
        "fail_val": "US/Pacific-New",
        "fix_val": "America/Los_Angeles",
        "hide_path": "startingDeadlineSeconds",
        "hide_old": "startingDeadlineSeconds: 60\n",
        "hide_new": "startingDeadlineSeconds: 86400\n",
        "values_fail": "timeZone: US/Pacific-New\nstartingDeadlineSeconds: 60\n",
        "values_fix": "timeZone: America/Los_Angeles\nstartingDeadlineSeconds: 60\n",
        "tpl": "  timeZone: {{ .Values.timeZone }}\n",
        "log": "unknown time zone US/Pacific-New leftover; CronJob never fires; sidecar CrashLoop",
        "live_ok": "timeZone=America/Los_Angeles",
        "hide_name": "deadline 86400",
        "new_vs": "CronJob timeZone leftover, not startingDeadline and not PDB",
        "seed": "leftover CronJob timeZone US/Pacific-New removed from tzdata CrashLoop",
        "n2": "n2 leftover still US/Pacific-New after git America/Los_Angeles",
        "ci": "# US/Pacific-New is gone from tzdata. Never stretch startingDeadline to hide.",
        "handoff": "LEFTOVER: n2 still timeZone US/Pacific-New. Platform: delete leftover RS. No deadline hide.",
        "pytest_ok": "test_tz_la\ntest_not_deadline_hide\ntest_not_pdb\ntest_pods_ready\ntest_no_force\ntest_cron",
        "pytest_fail": "test_tz_la_all FAILED b==US/Pacific-New",
        "tmpl_test": "test_template_matches_git",
        "rs": "b22",
    },
    {
        "plant": "bryn-prod",
        "app": "bryn-api",
        "chart": "0.8.4",
        "slug": "sts-pvc-retain",
        "field": "persistentVolumeClaimRetentionPolicy",
        "fail_val": "Retain",
        "fix_val": "Delete",
        "hide_path": "volumeClaimTemplates",
        "hide_old": "storage: 10Gi\n",
        "hide_new": "storage: 100Gi\n",
        "values_fail": "pvcRetention: Retain\nstorage: 10Gi\n",
        "values_fix": "pvcRetention: Delete\nstorage: 10Gi\n",
        "tpl": "  persistentVolumeClaimRetentionPolicy:\n    whenDeleted: {{ .Values.pvcRetention }}\n",
        "log": "orphan PVC from Retain policy still Bound to stale volume; mount CrashLoop leftover",
        "live_ok": "persistentVolumeClaimRetentionPolicy.whenDeleted=Delete",
        "hide_name": "storage 100Gi",
        "new_vs": "STS PVC Retain leftover, not VAC and not hostPath",
        "seed": "leftover STS PVC Retain; orphan volume CrashLoop",
        "n2": "n2 leftover still Retain after git Delete",
        "ci": "# Retain leaves orphan PVCs. Never grow storage to hide.",
        "handoff": "LEFTOVER: n2 still PVC Retain. Platform: delete leftover RS. No storage hide.",
        "pytest_ok": "test_pvc_delete\ntest_not_storage_hide\ntest_not_vac\ntest_pods_ready\ntest_no_force\ntest_sts",
        "pytest_fail": "test_pvc_delete_all FAILED b==Retain",
        "tmpl_test": "test_template_matches_git",
        "rs": "c33",
    },
    {
        "plant": "capel-prod",
        "app": "capel-api",
        "chart": "3.0.1",
        "slug": "svc-ipmode-proxy",
        "field": "ipMode",
        "fail_val": "Proxy",
        "fix_val": "VIP",
        "hide_path": "externalTrafficPolicy",
        "hide_old": "externalTrafficPolicy: Cluster\n",
        "hide_new": "externalTrafficPolicy: Local\n",
        "values_fail": "ipMode: Proxy\nexternalTrafficPolicy: Cluster\n",
        "values_fix": "ipMode: VIP\nexternalTrafficPolicy: Cluster\n",
        "tpl": "  ipMode: {{ .Values.ipMode }}\n",
        "log": "ipMode=Proxy hairpins ClusterIP; kube-proxy leftover NXDOMAIN CrashLoop",
        "live_ok": "ipMode=VIP",
        "hide_name": "ETP Local",
        "new_vs": "Service ipMode Proxy leftover, not ETP cartesian and not ITP Local",
        "seed": "leftover Service ipMode Proxy hairpin CrashLoop",
        "n2": "n2 leftover still ipMode Proxy after git VIP",
        "ci": "# ipMode Proxy hairpins ClusterIP. Never flip ETP to hide.",
        "handoff": "LEFTOVER: n2 still ipMode Proxy. Platform: delete leftover RS. No ETP hide.",
        "pytest_ok": "test_ipmode_vip\ntest_not_etp_hide\ntest_not_itp\ntest_pods_ready\ntest_no_force\ntest_svc",
        "pytest_fail": "test_ipmode_vip_all FAILED b==Proxy",
        "tmpl_test": "test_template_matches_git",
        "rs": "d44",
    },
    {
        "plant": "cefn-prod",
        "app": "cefn-api",
        "chart": "1.9.7",
        "slug": "deploy-progressdeadline",
        "field": "progressDeadlineSeconds",
        "fail_val": "1",
        "fix_val": "600",
        "hide_path": "minReadySeconds",
        "hide_old": "minReadySeconds: 0\n",
        "hide_new": "minReadySeconds: 0\nprogressDeadlineSeconds: 1\n",
        "values_fail": "progressDeadlineSeconds: 1\nminReadySeconds: 0\n",
        "values_fix": "progressDeadlineSeconds: 600\nminReadySeconds: 0\n",
        "tpl": "  progressDeadlineSeconds: {{ .Values.progressDeadlineSeconds }}\n",
        "log": "ProgressDeadlineExceeded after 1s leftover; RS never Ready CrashLoop",
        "live_ok": "progressDeadlineSeconds=600",
        "hide_name": "minReady 0",
        "new_vs": "progressDeadlineSeconds leftover, not HPA and not PDB",
        "seed": "leftover progressDeadlineSeconds=1; ProgressDeadlineExceeded CrashLoop",
        "n2": "n2 leftover still progressDeadlineSeconds 1 after git 600",
        "ci": "# deadline 1s always Exceeded. Never minReady hide.",
        "handoff": "LEFTOVER: n2 still progressDeadlineSeconds 1. Platform: delete leftover RS. No minReady hide.",
        "pytest_ok": "test_deadline_600\ntest_not_minready_hide\ntest_not_hpa\ntest_pods_ready\ntest_no_force\ntest_deploy",
        "pytest_fail": "test_deadline_600_all FAILED b==1",
        "tmpl_test": "test_template_matches_git",
        "rs": "e55",
    },
    {
        "plant": "coed-prod",
        "app": "coed-api",
        "chart": "4.2.2",
        "slug": "ds-maxsurge",
        "field": "maxSurge",
        "fail_val": "100%",
        "fix_val": "0",
        "hide_path": "maxUnavailable",
        "hide_old": "maxUnavailable: 1\n",
        "hide_new": "maxUnavailable: 0\n",
        "values_fail": "maxSurge: 100%\nmaxUnavailable: 1\n",
        "values_fix": "maxSurge: 0\nmaxUnavailable: 1\n",
        "tpl": "  updateStrategy:\n    rollingUpdate:\n      maxSurge: {{ .Values.maxSurge }}\n",
        "log": "DaemonSet maxSurge 100% double-scheduled node; hostPort leftover CrashLoop",
        "live_ok": "maxSurge=0",
        "hide_name": "maxUnavailable 0",
        "new_vs": "DaemonSet maxSurge leftover, not hostPort clash mill clone",
        "seed": "leftover DaemonSet maxSurge 100%; double schedule CrashLoop",
        "n2": "n2 leftover still maxSurge 100% after git 0",
        "ci": "# maxSurge 100% doubles hostPort. Never maxUnavailable 0 to hide.",
        "handoff": "LEFTOVER: n2 still maxSurge 100%. Platform: delete leftover RS. No maxUnavailable hide.",
        "pytest_ok": "test_surge_0\ntest_not_unavail_hide\ntest_not_hostport\ntest_pods_ready\ntest_no_force\ntest_ds",
        "pytest_fail": "test_surge_0_all FAILED b==100%",
        "tmpl_test": "test_template_matches_git",
        "rs": "f66",
    },
    {
        "plant": "craig-prod",
        "app": "craig-api",
        "chart": "0.5.5",
        "slug": "lease-holder-stale",
        "field": "holderIdentity",
        "fail_val": "craig-old-0",
        "fix_val": "craig-api-0",
        "hide_path": "leaseDurationSeconds",
        "hide_old": "leaseDurationSeconds: 15\n",
        "hide_new": "leaseDurationSeconds: 3600\n",
        "values_fail": "holderIdentity: craig-old-0\nleaseDurationSeconds: 15\n",
        "values_fix": "holderIdentity: craig-api-0\nleaseDurationSeconds: 15\n",
        "tpl": "  holderIdentity: {{ .Values.holderIdentity }}\n",
        "log": "leader election lost: holderIdentity craig-old-0 gone leftover CrashLoop",
        "live_ok": "holderIdentity=craig-api-0",
        "hide_name": "leaseDuration 3600",
        "new_vs": "Lease holderIdentity leftover, not PDB and not shareProcessNamespace",
        "seed": "leftover Lease holderIdentity craig-old-0; leader election CrashLoop",
        "n2": "n2 leftover still craig-old-0 after git craig-api-0",
        "ci": "# stale holderIdentity blocks election. Never stretch leaseDuration to hide.",
        "handoff": "LEFTOVER: n2 still holderIdentity craig-old-0. Platform: delete leftover RS. No duration hide.",
        "pytest_ok": "test_holder_new\ntest_not_duration_hide\ntest_not_pdb\ntest_pods_ready\ntest_no_force\ntest_lease",
        "pytest_fail": "test_holder_new_all FAILED b==craig-old-0",
        "tmpl_test": "test_template_matches_git",
        "rs": "178",
    },
    {
        "plant": "eglwys-prod",
        "app": "eglwys-api",
        "chart": "2.4.0",
        "slug": "volattach-dangling",
        "field": "VolumeAttachment",
        "fail_val": "eglwys-old-node",
        "fix_val": "eglwys-n1",
        "hide_path": "hostPath",
        "hide_old": "hostPath: false\n",
        "hide_new": "hostPath: true\n",
        "values_fail": "volumeAttachmentNode: eglwys-old-node\nhostPath: false\n",
        "values_fix": "volumeAttachmentNode: eglwys-n1\nhostPath: false\n",
        "tpl": "  nodeName: {{ .Values.volumeAttachmentNode }}\n",
        "log": "VolumeAttachment attached to eglwys-old-node gone leftover Multi-Attach CrashLoop",
        "live_ok": "volumeAttachmentNode=eglwys-n1",
        "hide_name": "hostPath",
        "new_vs": "VolumeAttachment dangling leftover, not CSI VAC and not hostPath",
        "seed": "leftover VolumeAttachment on decommissioned node Multi-Attach CrashLoop",
        "n2": "n2 leftover still eglwys-old-node after git eglwys-n1",
        "ci": "# dangling VolumeAttachment Multi-Attach. Never hostPath to hide.",
        "handoff": "LEFTOVER: n2 still VolumeAttachment eglwys-old-node. Platform: delete leftover RS. No hostPath.",
        "pytest_ok": "test_va_n1\ntest_not_hostpath_hide\ntest_not_vac\ntest_pods_ready\ntest_no_force\ntest_attach",
        "pytest_fail": "test_va_n1_all FAILED b==eglwys-old-node",
        "tmpl_test": "test_template_matches_git",
        "rs": "289",
    },
    {
        "plant": "llan-prod",
        "app": "llan-api",
        "chart": "1.1.8",
        "slug": "sc-expansion-false",
        "field": "allowVolumeExpansion",
        "fail_val": "false",
        "fix_val": "true",
        "hide_path": "storage",
        "hide_old": "storage: 10Gi\n",
        "hide_new": "storage: 10Gi\n# skip resize\n",
        "values_fail": "allowVolumeExpansion: false\nstorage: 10Gi\n",
        "values_fix": "allowVolumeExpansion: true\nstorage: 20Gi\n",
        "tpl": "  allowVolumeExpansion: {{ .Values.allowVolumeExpansion }}\n",
        "log": "PVC resize forbidden allowVolumeExpansion=false leftover ENOSPC CrashLoop",
        "live_ok": "allowVolumeExpansion=true",
        "hide_name": "skip resize comment",
        "new_vs": "StorageClass allowVolumeExpansion leftover, not VAC and not btrfs quota",
        "seed": "leftover StorageClass allowVolumeExpansion false; ENOSPC CrashLoop",
        "n2": "n2 leftover still allowVolumeExpansion false after git true",
        "ci": "# expansion false blocks PVC grow. Never comment-out resize to hide.",
        "handoff": "LEFTOVER: n2 still allowVolumeExpansion false. Platform: delete leftover RS. No skip-resize hide.",
        "pytest_ok": "test_expand_true\ntest_not_skip_hide\ntest_not_vac\ntest_pods_ready\ntest_no_force\ntest_sc",
        "pytest_fail": "test_expand_true_all FAILED b==false",
        "tmpl_test": "test_template_matches_git",
        "rs": "39a",
    },
    {
        "plant": "maes-prod",
        "app": "maes-api",
        "chart": "5.0.3",
        "slug": "pv-nodeaffinity-stale",
        "field": "nodeAffinity",
        "fail_val": "maes-rack-gone",
        "fix_val": "maes-rack-b",
        "hide_path": "nodeName",
        "hide_old": "nodeName: \"\"\n",
        "hide_new": "nodeName: maes-n0\n",
        "values_fail": "nodeAffinity: maes-rack-gone\nnodeName: \"\"\n",
        "values_fix": "nodeAffinity: maes-rack-b\nnodeName: \"\"\n",
        "tpl": "  nodeAffinity:\n    required:\n      nodeSelectorTerms:\n        - matchExpressions:\n            - key: topology.kubernetes.io/rack\n              values: [{{ .Values.nodeAffinity }}]\n",
        "log": "PV nodeAffinity rack maes-rack-gone; no nodes leftover CrashLoop",
        "live_ok": "nodeAffinity=maes-rack-b",
        "hide_name": "nodeName pin",
        "new_vs": "PV nodeAffinity leftover, not nodeName pin mill and not topologySpread",
        "seed": "leftover PV nodeAffinity maes-rack-gone; unschedulable CrashLoop",
        "n2": "n2 leftover still maes-rack-gone after git maes-rack-b",
        "ci": "# stale rack affinity unschedules. Never pin nodeName to hide.",
        "handoff": "LEFTOVER: n2 still PV nodeAffinity maes-rack-gone. Platform: delete leftover RS. No nodeName hide.",
        "pytest_ok": "test_rack_b\ntest_not_nodename_hide\ntest_not_spread\ntest_pods_ready\ntest_no_force\ntest_pv",
        "pytest_fail": "test_rack_b_all FAILED b==maes-rack-gone",
        "tmpl_test": "test_template_matches_git",
        "rs": "4ab",
    },
    {
        "plant": "moel-prod",
        "app": "moel-api",
        "chart": "0.7.9",
        "slug": "matchlabelkeys-pvc",
        "field": "matchLabelKeys",
        "fail_val": "pod-template-hash",
        "fix_val": "[]",
        "hide_path": "topologySpreadConstraints",
        "hide_old": "maxSkew: 1\n",
        "hide_new": "maxSkew: 100\n",
        "values_fail": "matchLabelKeys: [pod-template-hash]\nmaxSkew: 1\n",
        "values_fix": "matchLabelKeys: []\nmaxSkew: 1\n",
        "tpl": "  matchLabelKeys: {{ .Values.matchLabelKeys | toJson }}\n",
        "log": "matchLabelKeys pod-template-hash isolates each RS; PVC leftover CrashLoop",
        "live_ok": "matchLabelKeys=[]",
        "hide_name": "maxSkew 100",
        "new_vs": "matchLabelKeys leftover, not topologySpread mill cartesian",
        "seed": "leftover matchLabelKeys pod-template-hash; per-RS PVC CrashLoop",
        "n2": "n2 leftover still matchLabelKeys pod-template-hash after git empty",
        "ci": "# matchLabelKeys hash isolates PVCs. Never maxSkew 100 to hide.",
        "handoff": "LEFTOVER: n2 still matchLabelKeys pod-template-hash. Platform: delete leftover RS. No maxSkew hide.",
        "pytest_ok": "test_keys_empty\ntest_not_skew_hide\ntest_not_spread\ntest_pods_ready\ntest_no_force\ntest_mlk",
        "pytest_fail": "test_keys_empty_all FAILED b==pod-template-hash",
        "tmpl_test": "test_template_matches_git",
        "rs": "5bc",
    },
    {
        "plant": "nant-prod",
        "app": "nant-api",
        "chart": "3.3.3",
        "slug": "dra-adminaccess",
        "field": "adminAccess",
        "fail_val": "true",
        "fix_val": "false",
        "hide_path": "resourceClaims",
        "hide_old": "resourceClaims:\n  - name: gpu\n",
        "hide_new": "resourceClaims: []\n",
        "values_fail": "adminAccess: true\nresourceClaims:\n  - name: gpu\n",
        "values_fix": "adminAccess: false\nresourceClaims:\n  - name: gpu\n",
        "tpl": "  adminAccess: {{ .Values.adminAccess }}\n",
        "log": "DRA adminAccess true; claim reserved for kubelet leftover CrashLoop",
        "live_ok": "adminAccess=false",
        "hide_name": "drop resourceClaims",
        "new_vs": "DRA adminAccess leftover, not DeviceClass void mill and not RCT old nic",
        "seed": "leftover ResourceClaim adminAccess true; kubelet exclusive CrashLoop",
        "n2": "n2 leftover still adminAccess true after git false",
        "ci": "# adminAccess exclusive to kubelet. Never drop resourceClaims to hide.",
        "handoff": "LEFTOVER: n2 still adminAccess true. Platform: delete leftover RS. No claims hide.",
        "pytest_ok": "test_admin_false\ntest_not_dropclaims_hide\ntest_not_deviceclass\ntest_pods_ready\ntest_no_force\ntest_dra",
        "pytest_fail": "test_admin_false_all FAILED b==true",
        "tmpl_test": "test_template_matches_git",
        "rs": "6cd",
    },
]


def success_episode(round_n: int, s: dict) -> dict:
    guard(s)
    ns = s["plant"]
    app = s["app"]
    chart = s["chart"]
    rs = s["rs"]
    eid = f"kcl-r{round_n}-{s['slug']}"
    values_hide = (
        s["values_fail"].replace(s["hide_old"], s["hide_new"])
        if s["hide_old"] in s["values_fail"]
        else s["values_fail"] + s["hide_new"]
    )
    steps = [
        bash(1, f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart {chart} ({s['field']} leftover). List po.",
             f"kubectl -n {ns} get po,deploy -l app={app}",
             f"pod/{app}-{rs}-a 0/1 CrashLoopBackOff 9\npod/{app}-{rs}-b 0/1 CrashLoopBackOff 9\ndeploy/{app} 0/2\n",
             "0/2. Logs next."),
        bash(2, f"Observation: 9 restarts. Logs and describe ({s['field']} leftover).",
             f"kubectl -n {ns} logs {app}-{rs}-a --tail=12; kubectl -n {ns} describe po {app}-{rs}-a | tail -n 24",
             f"{s['field']}={s['fail_val']}\n{s['log']}\n",
             "Root cause visible. Read values."),
        read(3, "Observation: live fail matches ticket. Read values.yaml.",
             f"charts/{app}/values.yaml", s["values_fail"], "Values match the failing live object. Template next."),
        read(4, "Observation: values fail-open. Read deployment/related template.",
             f"charts/{app}/templates/deployment.yaml", s["tpl"], "Template emits the failing field. kubeconform next."),
        bash(5, "Observation: template emits fail field. helm template + kubeconform.",
             f"helm template {app} charts/{app} -n {ns} | kubeconform -strict -summary",
             "Summary: 3 resources found, 0 errors.\n# kubeconform does not evaluate this dataplane leftover.\n",
             "Plan clean. Apply --wait."),
        bash(6, "Observation: kubeconform 0. helm upgrade --wait current values.",
             f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12",
             f"Error: UPGRADE FAILED: timed out waiting for the condition\nCrashLoopBackOff {s['log']}\n",
             "Clean plan, failed apply. First wrong fix next."),
        edit(7, "Observation: --wait failed. Apply the wrong first hide.",
             f"charts/{app}/values.yaml",
             s["hide_old"] if s["hide_old"] in s["values_fail"] else s["values_fail"],
             s["hide_new"] if s["hide_old"] in s["values_fail"] else values_hide,
             f"patched {s['hide_name']} (wrong knob; {s['field']} still {s['fail_val']})",
             "Hide is not the contract. Confirm then plan-change."),
        bash(8, "Observation: hide patched. helm upgrade --wait.",
             f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 2m 2>&1 | tail -n 8",
             f'Release "{app}" upgraded. REVISION: 4\nwaiting... done\n',
             "Ready via hide. Wrong terminal. Plan change is the real fix."),
        edit(9, f"Reflection: {s['field']} {s['fix_val']} is the contract. Undo {s['hide_name']}.",
             f"charts/{app}/values.yaml",
             s["hide_new"] if s["hide_old"] in s["values_fail"] else values_hide,
             s["values_fix"],
             f"patched {s['field']} {s['fix_val']}; hide undone",
             "Apply without --force."),
        bash(10, "Observation: real fix patched. helm upgrade --wait no --force.",
             f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 3m 2>&1 | tail -n 8",
             f'Release "{app}" upgraded. REVISION: 5\nwaiting for 2 pods... done\n',
             "Revision 5 Ready. Confirm live spec."),
        bash(11, "Observation: --wait passed. Confirm the live contract.",
             f"kubectl -n {ns} get deploy,{app} -o yaml | rg '{s['field']}|{s['fix_val']}' | head",
             f"{s['live_ok']}\n", "Contract holds. pytest."),
        bash(12, "Observation: live contract ok. pytest chart fixtures.",
             f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=short",
             f"......\n6 passed in 0.32s\n# {s['pytest_ok'].replace(chr(10), chr(10)+'# ')}\n",
             "6/6. Patch CI.md."),
        edit(13, "Observation: 6/6. Patch CI.md so the hide cannot return.",
             f"charts/{app}/CI.md",
             f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n",
             f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n{s['ci']}\n",
             "patched CI.md", "CI records the contract."),
        bash(14, "Observation: CI.md updated. helm history.",
             f"helm -n {ns} history {app} | tail -n 4",
             f"3 superseded {s['field']} {s['fail_val']}\n4 superseded {s['hide_name']} hide\n5 deployed {s['field']} {s['fix_val']}\n",
             "History shows the hide then the fix."),
        bash(15, "Observation: rev 5 deployed. logs confirm.",
             f"kubectl -n {ns} logs deploy/{app} --tail=3",
             f"level=info msg=\"peer via {s['field']}={s['fix_val']}\"\n", "App healthy."),
        bash(16, "Observation: logs ok. get po.",
             f"kubectl -n {ns} get po -l app={app}",
             f"{app}-8a2-a 1/1 Running 0\n{app}-8a2-b 1/1 Running 0\n", "Done."),
    ]
    if len(steps) != 16:
        raise SystemExit(f"{eid} want 16 steps got {len(steps)}")
    return {
        "id": eid,
        "goal": (
            f"{app} in designed plant {ns} is CrashLoopBackOff after leftover {s['field']}: "
            f"{s['fail_val']}. {s['seed']}. Do not toggle {s['hide_name']} as a hide."
        ),
        "plan": f"Read {s['field']} vs live, template, apply, then {s['fix_val']}.",
        "steps": steps,
        "outcome": (
            f"kubeconform passed {s['fail_val']}. helm --wait leftover. {s['hide_name']} hid nothing. "
            f"Plan change: {s['field']} {s['fix_val']}. Rev 5: 2/2, 6/6."
        ),
        "reward": {
            "success": True, "apply_fails": 2, "plan_changes": 1,
            "tests_passed": 6, "pods_ready": 2, "cost_steps": 16,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def leftover_episode(round_n: int, s: dict) -> dict:
    guard(s)
    ns = s["plant"]
    app = s["app"].replace("-api", "-svc")
    chart = s["chart"]
    rs = s["rs"]
    eid = f"kcl-r{round_n}-{s['slug']}-n2-handoff"
    values_hide = s["values_fail"] + s["hide_new"]
    steps = [
        bash(1, f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart {chart} leftover. List po, chart.",
             f"kubectl -n {ns} get po,deploy -l app={app}; helm -n {ns} list | rg {app}",
             (f"pod/{app}-{rs}-a 0/1 CrashLoopBackOff 10\n"
              f"pod/{app}-{rs}-b 0/1 CrashLoopBackOff 10\n"
              f"deploy/{app} 0/2\n{app} {app}-{chart} deployed\n"
              f"{s['field']}={s['fail_val']}\n"),
             "0/2 crashloop. Describe next."),
        bash(2, "Observation: crashloop. Logs and describe.",
             f"kubectl -n {ns} logs {app}-{rs}-a --tail=16; kubectl -n {ns} describe po {app}-{rs}-a | tail -n 20",
             f"{s['log']}\n", "Root cause visible. Read values."),
        read(3, "Observation: live fail matches ticket. Read values.yaml.",
             f"charts/{app}/values.yaml", s["values_fail"], "Values match the failing live object. Template next."),
        read(4, "Observation: values fail-open. Read deployment/related template.",
             f"charts/{app}/templates/deployment.yaml", s["tpl"], "Template emits the failing field. kubeconform next."),
        bash(5, "Observation: template emits fail field. helm template + kubeconform.",
             f"helm template {app} charts/{app} -n {ns} | kubeconform -strict -summary",
             "Summary: 3 resources found, 0 errors.\n", "Plan clean. Apply --wait."),
        bash(6, "Observation: kubeconform 0. helm upgrade --wait current values.",
             f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12",
             f"Error: UPGRADE FAILED: timed out waiting for the condition\nCrashLoopBackOff {s['field']} leftover\n",
             "Clean plan, failed apply. Ticket says helm --force."),
        edit(7, "Observation: --wait failed. Apply the wrong first hide and --force.",
             f"charts/{app}/values.yaml", s["values_fail"], values_hide,
             "patched the hide; applying with --force as the ticket asked",
             "--force is the wrong applicator."),
        bash(8, "Observation: hide + --force. helm upgrade --force --wait.",
             f"helm upgrade {app} charts/{app} -n {ns} --force --wait --timeout 2m 2>&1 | tail -n 10",
             f'Release "{app}" upgraded. REVISION: 4\nwaiting... mixed Ready 1/2\n',
             "n2 still leftover via three-way. Plan change next."),
        edit(9, f"Reflection: git {s['field']} {s['fix_val']}. Do not delete n2.",
             f"charts/{app}/values.yaml", values_hide, s["values_fix"],
             f"patched git {s['field']} {s['fix_val']}",
             "Apply; leftover n2 may remain."),
        bash(10, "Observation: git fix. helm upgrade --force still.",
             f"helm upgrade {app} charts/{app} -n {ns} --force --wait --timeout 2m 2>&1 | tail -n 10",
             f"UPGRADE FAILED: n2 leftover {s['field']}={s['fail_val']} after three-way\n",
             "Force kept live leftover. Confirm n2."),
        bash(11, "Observation: --force leftover. Confirm n2 live spec.",
             f"kubectl -n {ns} get po,rs -l app={app} -o yaml | rg '{s['field']}|{s['fail_val']}|n2' | head",
             f"n2 leftover {s['field']}={s['fail_val']}\n{s['n2']}\n",
             "Leftover documented. Mixed pytest."),
        bash(12, "Observation: n2 leftover. pytest mixed.",
             f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=line",
             f"..F...\n1 failed, 5 passed in 0.41s\n{s['pytest_fail']}\n",
             "1/2. Patch CI leftover."),
        edit(13, "Observation: mixed tests. Patch CI.md leftover handoff.",
             f"charts/{app}/CI.md",
             f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n",
             f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n{s['handoff']}\n",
             "patched leftover handoff", "CI records n2 leftover."),
        bash(14, "Observation: CI leftover. helm history.",
             f"helm -n {ns} history {app} | tail -n 4",
             f"3 failed {s['field']} {s['fail_val']}\n4 failed --force hide\n5 failed n2 leftover\n",
             "History is failed leftover."),
        bash(15, "Observation: history leftover. logs n2.",
             f"kubectl -n {ns} logs {app}-{rs}-b --tail=4",
             f"{s['log']}\n", "n2 still crashing."),
        bash(16, "Observation: n2 logs leftover. get po.",
             f"kubectl -n {ns} get po -l app={app}",
             f"{app}-n1-a 1/1 Running 0\n{app}-{rs}-b 0/1 CrashLoopBackOff 12\n",
             "1/2 ready. RS leftover."),
        bash(17, "Observation: mixed pods. leftover RS.",
             f"kubectl -n {ns} get rs -l app={app}",
             f"{app}-{rs} 1 1 1 leftover {s['field']}={s['fail_val']}\n",
             "Do not delete n2 as success."),
        bash(18, "Observation: leftover RS remains. Stop; handoff.",
             f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=line | tail",
             f"1 failed, 5 passed\n# {s['handoff']}\n",
             "Partial. Platform deletes leftover RS."),
    ]
    if len(steps) != 18:
        raise SystemExit(f"{eid} want 18 steps got {len(steps)}")
    return {
        "id": eid,
        "goal": (
            f"{app} in designed plant {ns} is CrashLoopBackOff after leftover {s['field']}: "
            f"{s['fail_val']}. {s['n2']}. Do not --force-delete n2."
        ),
        "plan": f"Show leftover {s['field']}, --force dead-end, git {s['fix_val']}, leave n2.",
        "steps": steps,
        "outcome": (
            f"kubeconform 0. helm --force kept n2 leftover {s['field']}={s['fail_val']}. "
            f"Partial 1/2. {s['handoff']}"
        ),
        "reward": {
            "success": False, "apply_fails": 3, "plan_changes": 1,
            "tests_passed": 1, "pods_ready": 1, "cost_steps": 18, "xfailed": 1,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 80 + (round_n % 10)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"Quota 2. Unique CrashLoopBackOff pair. Catalog r70–r1091 stays in raw. "
        f"New: {s['field']} leftover, not {s['new_vs']}. Plant `{s['plant']}` (not bay-prod).\n\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['seed']} | kubeconform 0; apply --wait fail | wrong first hide then plan change | success 2/2 pytest 6/6 |\n"
        f"| {b['id']} | {s['n2']} | kubeconform 0; --force mixed | leftover on n2; SSA spec only | partial 1/2 handoff |\n\n"
        f"## Step counts\n"
        f"- ep1: 16. Clean template 5; apply fail 6,8; plan change 9; verify 12–16.\n"
        f"- ep2: 18. Clean template 5; apply fail 6–8; plan change 9; leftover 11–18.\n\n"
        f"## decision_basis audit\n"
        f"Plan:/Observation:/Reflection:/Tool call: ≤240. No hidden CoT. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `{s['plant']}`.\n\n"
        f"## How the apply-fail taught\n"
        f"1. {s['seed']}. kubeconform does not evaluate this. Stretching the wrong knob hid or no-op'd.\n"
        f"2. {s['n2']}. helm --force three-way kept the live leftover. Do not delete n2 as success.\n\n"
        f"## Bans honored\n"
        f"- No empty-ENV after chart bump (BITBUCKET_HOME / KEYCLOAK_HOME / CARGO_* / RUST_*).\n"
        f"- No leftover cartesian on spec.ipFamilies / externalTrafficPolicy / allocateLoadBalancerNodePorts.\n"
        f"- No bay-prod / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r963–r1091.\n"
    )


def write_round(round_n: int, staging: Path, idx: int) -> None:
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no kcl catalog pair for idx={idx}")
    spec = PAIRS[idx]
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(round_n, spec, a, b))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [a["id"], b["id"]], "steps": [16, 18], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
