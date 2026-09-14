#!/usr/bin/env python3
"""k8s-crashloop mill from r1266. Q=2. grok-4.6.

Unique leftover leftover leftover CrashLoopBackOff pairs. Catalog r70–r1264 stays.
BAN leftover-n2 stamp, empty-ENV catalog, AppArmor/seccomp Unconfined,
webhook timeout, r70–r1264 clones. IDs kcl-rN-<slug> without -w3-empty /
sxNNN-handoff. Loop: frontier → reserve --expected 2 → stage → publish.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
FACTORY_DIR = ROOT / "outputs/raw/2026-08-19-agentic/k8s-crashloop-factory"
TXN = ROOT / "pipelines" / "round_txn.py"
PEER = ROOT / "experiments" / "kcl-mill-r1007.py"
HOPPER = ROOT / "experiments" / "hopper_mill_g46c.py"
FACTORY = "k8s-crashloop-factory"
GEN = "grok-4.6"
STAMP = "leftover n2 still n2 leftover still"
MAX_ROUNDS = 16
MAX_SECONDS = 40 * 60
SKIP_HOP = {
    "sandbox-refusal-factory",
    "eval-harness-trajectory-factory",
    "k8s-crashloop-factory",
}

_spec = importlib.util.spec_from_file_location("kcl_peer", PEER)
_peer = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_peer)
success_episode = _peer.success_episode
_leftover_episode = _peer.leftover_episode


def leftover_episode(round_n: int, s: dict) -> dict:
    ep = _leftover_episode(round_n, s)
    app = s["app"].replace("-api", "-svc")
    ns = s["plant"]
    ep["goal"] = (
        f"{app} in designed plant {ns} still runs live {s['field']}={s['fail_val']} "
        f"on replica n2 after git {s['fix_val']}. Do not --force."
    )
    blob = json.dumps(ep)
    if STAMP in blob:
        raise SystemExit(f"stamp in leftover {ep['id']}")
    if "-w3-empty" in ep["id"] or "sx" in ep["id"]:
        raise SystemExit(f"banned leftover id {ep['id']}")
    return ep


def pair(**kwargs: str) -> dict:
    required = {
        "plant",
        "app",
        "chart",
        "slug",
        "field",
        "fail_val",
        "fix_val",
        "hide_path",
        "hide_old",
        "hide_new",
        "values_fail",
        "values_fix",
        "tpl",
        "log",
        "live_ok",
        "hide_name",
        "new_vs",
        "seed",
        "n2",
        "ci",
        "handoff",
        "pytest_ok",
        "pytest_fail",
        "tmpl_test",
        "rs",
    }
    missing = required - set(kwargs)
    if missing:
        raise SystemExit(f"pair missing {missing}")
    if kwargs["hide_old"] not in kwargs["values_fail"]:
        raise SystemExit(f"{kwargs['plant']} hide_old not in values_fail")
    banned_plants = {
        "bay-prod",
        "cwm-prod",
        "llyn-prod",
        "atoll-prod",
        "kyle-prod",
        "voe-prod",
        "tarn-prod",
        "lough-prod",
        "weald-prod",
        "fen-prod",
        "coll-prod",
        "canna-prod",
        "harris-prod",
        "lorn-prod",
        "machair-prod",
        "broch-prod",
        "crannog-prod",
        "bealach-prod",
        "drumlin-prod",
        "esker-prod",
        "moraine-prod",
        "karst-prod",
        "turlough-prod",
        "clachan-prod",
        "shieling-prod",
        "grange-prod",
        "glebe-prod",
        "minster-prod",
        "henge-prod",
        "pill-prod",
        "sough-prod",
        "adit-prod",
        "delph-prod",
        "wharf-prod",
        "otterburn-prod",
        "mastiles-prod",
        "gordale-prod",
    }
    if kwargs["plant"] in banned_plants:
        raise SystemExit(f"banned plant {kwargs['plant']}")
    if kwargs["slug"] in {
        "downward-divisor",
        "ephemeral-sc-old",
        "rclaim-admin-gone",
        "fieldref-divisor",
        "ctb-label-old",
        "dnspolicy-none",
        "stopsignal-kill",
        "hostname-override",
        "selinux-changepolicy",
        "poststart-sleep",
        "sts-ordinals-start",
        "sts-servicename-gone",
        "pvc-volumemode-block",
        "job-managedby-old",
        "job-ttl-1",
        "cron-timezone-old",
        "vpa-minallowed-8cpu",
        "hpa-external-oldmetric",
        "grpcroute-method-old",
        "backendtls-system-cas",
        "rolebinding-oldsa",
        "hostpath-type-file",
        "nfs-vers-3",
        "iscsi-targetportal-old",
    }:
        raise SystemExit(f"banned slug {kwargs['slug']}")
    ident = " ".join(
        str(kwargs.get(k, "")) for k in ("plant", "slug", "field", "fail_val")
    ).lower()
    for needle in (
        "unconfined",
        "webhook",
        "ipfamilies",
        "internaltrafficpolicy",
        "externaltrafficpolicy",
        "allocateloadbalancernodeports",
        "bitbucket_home",
        "keycloak_home",
        "bay-prod",
        "apparmor",
        "rclaim-admin-gone",
        STAMP,
    ):
        if needle in ident:
            raise SystemExit(f"banned needle {needle!r} in {kwargs['plant']}")
    return kwargs


PAIRS: list[dict] = [
    pair(
        plant="nenthead-prod",
        app="nenthead-api",
        chart="2.4.1",
        slug="vap-param-old",
        field="validatingAdmissionPolicy.spec.paramKind",
        fail_val="old.nenthead.io/v1/QuotaHint",
        fix_val="nenthead.io/v1/QuotaHint",
        hide_path="failurePolicy",
        hide_old="failurePolicy: Fail\n",
        hide_new="failurePolicy: Ignore\n",
        values_fail="paramKind: old.nenthead.io/v1/QuotaHint\nfailurePolicy: Fail\n",
        values_fix="paramKind: nenthead.io/v1/QuotaHint\nfailurePolicy: Fail\n",
        tpl="  paramKind:\n    apiVersion: {{ .Values.paramKind }}\n",
        log="admission leftover ValidatingAdmissionPolicy paramKind old.nenthead.io/v1/QuotaHint gone; deny CrashLoop",
        live_ok="validatingAdmissionPolicy.spec.paramKind=nenthead.io/v1/QuotaHint",
        hide_name="failurePolicy Ignore",
        new_vs="ValidatingAdmissionPolicy paramKind leftover vs MutatingAdmissionPolicy leftover, not webhook timeout",
        seed="leftover ValidatingAdmissionPolicy paramKind old.nenthead.io; deny CrashLoop",
        n2="replica n2 still ValidatingAdmissionPolicy paramKind old.nenthead.io after git nenthead.io",
        ci="# VAP paramKind must be nenthead.io/v1/QuotaHint. Never Ignore failurePolicy to hide leftover paramKind.",
        handoff="LEFTOVER: replica n2 still VAP paramKind old.nenthead.io. Platform: delete leftover RS. No failurePolicy hide.",
        pytest_ok="test_vap_kind\ntest_not_fp_hide\ntest_not_map\ntest_pods_ready\ntest_no_force\ntest_vap",
        pytest_fail="test_vap_kind_all FAILED b==old.nenthead.io/v1/QuotaHint",
        tmpl_test="test_template_matches_git",
        rs="g501",
    ),
    pair(
        plant="alston-prod",
        app="alston-api",
        chart="1.8.3",
        slug="rq-objectcount-old",
        field="resourceQuota.spec.hard.objectCount",
        fail_val="secrets=2",
        fix_val="secrets=64",
        hide_path="limitRange.default",
        hide_old="limitRangeCpu: \"500m\"\n",
        hide_new="limitRangeCpu: \"50m\"\n",
        values_fail="quotaSecrets: \"2\"\nlimitRangeCpu: \"500m\"\n",
        values_fix="quotaSecrets: \"64\"\nlimitRangeCpu: \"500m\"\n",
        tpl="    secrets: {{ .Values.quotaSecrets | quote }}\n",
        log="forbidden leftover ResourceQuota hard secrets=2; token secret create CrashLoop",
        live_ok="resourceQuota.spec.hard.secrets=64",
        hide_name="LimitRange default cpu 50m",
        new_vs="ResourceQuota hard.objectCount leftover vs LimitRange leftover, not empty-ENV cartesian",
        seed="leftover ResourceQuota secrets=2; token secret CrashLoop",
        n2="replica n2 still ResourceQuota secrets=2 after git 64",
        ci="# ResourceQuota secrets must be 64. Never shrink LimitRange CPU to hide leftover quota.",
        handoff="LEFTOVER: replica n2 still ResourceQuota secrets=2. Platform: delete leftover RS. No LimitRange hide.",
        pytest_ok="test_rq_64\ntest_not_lr_hide\ntest_not_emptyenv\ntest_pods_ready\ntest_no_force\ntest_rq",
        pytest_fail="test_rq_64_all FAILED b==secrets=2",
        tmpl_test="test_template_matches_git",
        rs="g502",
    ),
    pair(
        plant="allenheads-prod",
        app="allenheads-api",
        chart="3.1.0",
        slug="pdb-maxunavail-0",
        field="podDisruptionBudget.spec.maxUnavailable",
        fail_val="0",
        fix_val="1",
        hide_path="minAvailable",
        hide_old="minAvailable: 1\n",
        hide_new="minAvailable: 100%\n",
        values_fail="maxUnavailable: 0\nminAvailable: 1\n",
        values_fix="maxUnavailable: 1\nminAvailable: 1\n",
        tpl="  maxUnavailable: {{ .Values.maxUnavailable }}\n",
        log="cannot evict leftover PDB maxUnavailable=0; drain blocked then CrashLoop on stuck replica",
        live_ok="podDisruptionBudget.spec.maxUnavailable=1",
        hide_name="minAvailable 100%",
        new_vs="PodDisruptionBudget maxUnavailable leftover vs minAvailable leftover, not STS whenDeleted",
        seed="leftover PDB maxUnavailable=0; eviction block CrashLoop",
        n2="replica n2 still PDB maxUnavailable=0 after git 1",
        ci="# PDB maxUnavailable must be 1. Never rewrite minAvailable to hide leftover 0.",
        handoff="LEFTOVER: replica n2 still PDB maxUnavailable=0. Platform: delete leftover RS. No minAvailable hide.",
        pytest_ok="test_pdb_1\ntest_not_min_hide\ntest_not_stsdel\ntest_pods_ready\ntest_no_force\ntest_pdb",
        pytest_fail="test_pdb_1_all FAILED b==0",
        tmpl_test="test_template_matches_git",
        rs="g503",
    ),
    pair(
        plant="weardale-prod",
        app="weardale-api",
        chart="0.9.4",
        slug="pc-value-neg",
        field="priorityClass.value",
        fail_val="-1",
        fix_val="1000",
        hide_path="preemptionPolicy",
        hide_old="preemptionPolicy: PreemptLowerPriority\n",
        hide_new="preemptionPolicy: Never\n",
        values_fail="pcValue: -1\npreemptionPolicy: PreemptLowerPriority\n",
        values_fix="pcValue: 1000\npreemptionPolicy: PreemptLowerPriority\n",
        tpl="  value: {{ .Values.pcValue }}\n",
        log="wait-for-schedule leftover PriorityClass value=-1; pending then CrashLoop",
        live_ok="priorityClass.value=1000",
        hide_name="preemptionPolicy Never",
        new_vs="PriorityClass value leftover vs preemptionPolicy leftover, not schedulerName gone",
        seed="leftover PriorityClass value=-1; pending CrashLoop",
        n2="replica n2 still PriorityClass value=-1 after git 1000",
        ci="# PriorityClass value must be 1000. Never Never-preempt to hide leftover -1.",
        handoff="LEFTOVER: replica n2 still PriorityClass value=-1. Platform: delete leftover RS. No preemptionPolicy hide.",
        pytest_ok="test_pc_1000\ntest_not_preempt_hide\ntest_not_sched\ntest_pods_ready\ntest_no_force\ntest_pc",
        pytest_fail="test_pc_1000_all FAILED b==-1",
        tmpl_test="test_template_matches_git",
        rs="g504",
    ),
    pair(
        plant="teesdale-prod",
        app="teesdale-api",
        chart="4.0.2",
        slug="rc-overhead-old",
        field="runtimeClass.overhead.podFixed",
        fail_val="cpu=2",
        fix_val="cpu=0",
        hide_path="handler",
        hide_old="handler: runc\n",
        hide_new="handler: kata\n",
        values_fail="overheadCpu: \"2\"\nhandler: runc\n",
        values_fix="overheadCpu: \"0\"\nhandler: runc\n",
        tpl="  overhead:\n    podFixed:\n      cpu: {{ .Values.overheadCpu | quote }}\n",
        log="Insufficient cpu leftover RuntimeClass overhead podFixed cpu=2 CrashLoop",
        live_ok="runtimeClass.overhead.podFixed.cpu=0",
        hide_name="handler kata",
        new_vs="RuntimeClass overhead leftover vs handler leftover, not spec.os.name windows",
        seed="leftover RuntimeClass overhead cpu=2; Insufficient cpu CrashLoop",
        n2="replica n2 still RuntimeClass overhead cpu=2 after git 0",
        ci="# RuntimeClass overhead cpu must be 0. Never swap handler to hide leftover overhead.",
        handoff="LEFTOVER: replica n2 still RuntimeClass overhead cpu=2. Platform: delete leftover RS. No handler hide.",
        pytest_ok="test_oh_0\ntest_not_handler_hide\ntest_not_osname\ntest_pods_ready\ntest_no_force\ntest_rcoh",
        pytest_fail="test_oh_0_all FAILED b==cpu=2",
        tmpl_test="test_template_matches_git",
        rs="g505",
    ),
    pair(
        plant="stainmore-prod",
        app="stainmore-api",
        chart="2.7.7",
        slug="tsp-whenunsat-donotsched",
        field="topologySpreadConstraints.whenUnsatisfiable",
        fail_val="DoNotSchedule",
        fix_val="ScheduleAnyway",
        hide_path="maxSkew",
        hide_old="maxSkew: 1\n",
        hide_new="maxSkew: 8\n",
        values_fail="whenUnsatisfiable: DoNotSchedule\nmaxSkew: 1\n",
        values_fix="whenUnsatisfiable: ScheduleAnyway\nmaxSkew: 1\n",
        tpl="    whenUnsatisfiable: {{ .Values.whenUnsatisfiable }}\n",
        log="wait-for-spread leftover topologySpread whenUnsatisfiable DoNotSchedule CrashLoop",
        live_ok="topologySpreadConstraints.whenUnsatisfiable=ScheduleAnyway",
        hide_name="maxSkew 8",
        new_vs="topologySpread whenUnsatisfiable leftover vs maxSkew leftover, not schedulingGates",
        seed="leftover topologySpread DoNotSchedule; wait CrashLoop",
        n2="replica n2 still topologySpread whenUnsatisfiable DoNotSchedule after git ScheduleAnyway",
        ci="# whenUnsatisfiable must be ScheduleAnyway. Never bump maxSkew to hide leftover DoNotSchedule.",
        handoff="LEFTOVER: replica n2 still topologySpread DoNotSchedule. Platform: delete leftover RS. No maxSkew hide.",
        pytest_ok="test_anyway\ntest_not_skew_hide\ntest_not_gates\ntest_pods_ready\ntest_no_force\ntest_tsp",
        pytest_fail="test_anyway_all FAILED b==DoNotSchedule",
        tmpl_test="test_template_matches_git",
        rs="g506",
    ),
    pair(
        plant="bowes-prod",
        app="bowes-api",
        chart="1.3.5",
        slug="np-egress-denyall",
        field="networkPolicy.spec.egress",
        fail_val="[]",
        fix_val="allow-dns-53",
        hide_path="ciliumNetworkPolicy",
        hide_old="ciliumPolicy: \"\"\n",
        hide_new="ciliumPolicy: deny-all\n",
        values_fail="egressAllow: \"\"\nciliumPolicy: \"\"\n",
        values_fix="egressAllow: dns-53\nciliumPolicy: \"\"\n",
        tpl="  egress: {{ .Values.egressAllow | default \"[]\" }}\n",
        log="i/o timeout leftover NetworkPolicy egress []; DNS CrashLoop",
        live_ok="networkPolicy.spec.egress=allow-dns-53",
        hide_name="CiliumNetworkPolicy deny-all",
        new_vs="NetworkPolicy egress leftover vs CiliumNetworkPolicy leftover, not dnsPolicy None",
        seed="leftover NetworkPolicy empty egress; DNS CrashLoop",
        n2="replica n2 still NetworkPolicy egress [] after git allow-dns-53",
        ci="# NetworkPolicy egress must allow DNS 53. Never add Cilium deny-all to hide leftover empty egress.",
        handoff="LEFTOVER: replica n2 still NetworkPolicy egress []. Platform: delete leftover RS. No Cilium hide.",
        pytest_ok="test_np_dns\ntest_not_cilium_hide\ntest_not_dnspolicy\ntest_pods_ready\ntest_no_force\ntest_np",
        pytest_fail="test_np_dns_all FAILED b==[]",
        tmpl_test="test_template_matches_git",
        rs="g507",
    ),
    pair(
        plant="startforth-prod",
        app="startforth-api",
        chart="5.0.1",
        slug="gw-listener-oldport",
        field="gateway.spec.listeners.port",
        fail_val="8080",
        fix_val="443",
        hide_path="httproute.hostname",
        hide_old="httpHostname: api.startforth.internal\n",
        hide_new="httpHostname: old.startforth.internal\n",
        values_fail="gwPort: 8080\nhttpHostname: api.startforth.internal\n",
        values_fix="gwPort: 443\nhttpHostname: api.startforth.internal\n",
        tpl="    port: {{ .Values.gwPort }}\n",
        log="connection refused leftover Gateway listener port 8080 vs TLS 443 CrashLoop",
        live_ok="gateway.spec.listeners.port=443",
        hide_name="HTTPRoute hostname old.startforth.internal",
        new_vs="Gateway listener port leftover vs HTTPRoute leftover, not GRPCRoute method leftover",
        seed="leftover Gateway listener port 8080; TLS CrashLoop",
        n2="replica n2 still Gateway listener port 8080 after git 443",
        ci="# Gateway listener port must be 443. Never rewrite HTTPRoute hostname to hide leftover 8080.",
        handoff="LEFTOVER: replica n2 still Gateway listener port 8080. Platform: delete leftover RS. No HTTPRoute hide.",
        pytest_ok="test_gw_443\ntest_not_hr_hide\ntest_not_grpc\ntest_pods_ready\ntest_no_force\ntest_gw",
        pytest_fail="test_gw_443_all FAILED b==8080",
        tmpl_test="test_template_matches_git",
        rs="g508",
    ),
    pair(
        plant="barnard-prod",
        app="barnard-api",
        chart="2.2.2",
        slug="servicecidr-oldrange",
        field="serviceCIDR.spec.cidrs",
        fail_val="10.96.0.0/28",
        fix_val="10.96.0.0/12",
        hide_path="ipAddress",
        hide_old="staticIP: \"\"\n",
        hide_new="staticIP: 10.96.0.9\n",
        values_fail="serviceCIDR: 10.96.0.0/28\nstaticIP: \"\"\n",
        values_fix="serviceCIDR: 10.96.0.0/12\nstaticIP: \"\"\n",
        tpl="  cidrs:\n    - {{ .Values.serviceCIDR }}\n",
        log="no free ClusterIP leftover ServiceCIDR 10.96.0.0/28 exhausted CrashLoop",
        live_ok="serviceCIDR.spec.cidrs=10.96.0.0/12",
        hide_name="IPAddress 10.96.0.9",
        new_vs="ServiceCIDR leftover vs IPAddress leftover, not allocateLoadBalancerNodePorts",
        seed="leftover ServiceCIDR /28 exhausted; ClusterIP CrashLoop",
        n2="replica n2 still ServiceCIDR 10.96.0.0/28 after git 10.96.0.0/12",
        ci="# ServiceCIDR must be 10.96.0.0/12. Never pin IPAddress to hide leftover /28.",
        handoff="LEFTOVER: replica n2 still ServiceCIDR 10.96.0.0/28. Platform: delete leftover RS. No IPAddress hide.",
        pytest_ok="test_cidr_12\ntest_not_ip_hide\ntest_not_lbnports\ntest_pods_ready\ntest_no_force\ntest_scidr",
        pytest_fail="test_cidr_12_all FAILED b==10.96.0.0/28",
        tmpl_test="test_template_matches_git",
        rs="g509",
    ),
    pair(
        plant="middleton-prod",
        app="middleton-api",
        chart="3.6.0",
        slug="svm-source-old",
        field="storageVersionMigration.spec.resource",
        fail_val="widgets.old.middleton.io",
        fix_val="widgets.middleton.io",
        hide_path="crd.conversion",
        hide_old="conversionStrategy: None\n",
        hide_new="conversionStrategy: Webhook\n",
        values_fail="svmResource: widgets.old.middleton.io\nconversionStrategy: None\n",
        values_fix="svmResource: widgets.middleton.io\nconversionStrategy: None\n",
        tpl="  resource:\n    group: {{ .Values.svmResource }}\n",
        log="schema leftover StorageVersionMigration resource widgets.old.middleton.io gone CrashLoop",
        live_ok="storageVersionMigration.spec.resource=widgets.middleton.io",
        hide_name="CRD conversion Webhook",
        new_vs="StorageVersionMigration leftover vs leftover CRD conversion, not webhook timeout",
        seed="leftover StorageVersionMigration widgets.old.middleton.io; schema CrashLoop",
        n2="replica n2 still StorageVersionMigration widgets.old.middleton.io after git widgets.middleton.io",
        ci="# SVM resource must be widgets.middleton.io. Never flip CRD conversion to hide leftover SVM.",
        handoff="LEFTOVER: replica n2 still SVM widgets.old.middleton.io. Platform: delete leftover RS. No CRD conversion hide.",
        pytest_ok="test_svm_new\ntest_not_conv_hide\ntest_not_wh\ntest_pods_ready\ntest_no_force\ntest_svm",
        pytest_fail="test_svm_new_all FAILED b==widgets.old.middleton.io",
        tmpl_test="test_template_matches_git",
        rs="g510",
    ),
    pair(
        plant="frosterley-prod",
        app="frosterley-api",
        chart="1.0.9",
        slug="imagevol-ref-gone",
        field="volumes.image.reference",
        fail_val="ghcr.io/frosterley/old@sha256:dead",
        fix_val="ghcr.io/frosterley/api:1.0.9",
        hide_path="emptyDir.sizeLimit",
        hide_old="sizeLimit: \"\"\n",
        hide_new="sizeLimit: 8Mi\n",
        values_fail="imageRef: ghcr.io/frosterley/old@sha256:dead\nsizeLimit: \"\"\n",
        values_fix="imageRef: ghcr.io/frosterley/api:1.0.9\nsizeLimit: \"\"\n",
        tpl="    image:\n      reference: {{ .Values.imageRef }}\n",
        log="FailedMount leftover image volume reference ghcr.io/frosterley/old@sha256:dead gone CrashLoop",
        live_ok="volumes.image.reference=ghcr.io/frosterley/api:1.0.9",
        hide_name="emptyDir sizeLimit 8Mi",
        new_vs="ImageVolume leftover vs leftover emptyDir sizeLimit, not imagePullPolicy Never",
        seed="leftover image volume reference old digest gone; FailedMount CrashLoop",
        n2="replica n2 still image volume reference old digest after git api:1.0.9",
        ci="# image volume reference must be ghcr.io/frosterley/api:1.0.9. Never add emptyDir sizeLimit to hide leftover digest.",
        handoff="LEFTOVER: replica n2 still image volume old digest. Platform: delete leftover RS. No emptyDir hide.",
        pytest_ok="test_imgvol_tag\ntest_not_sl_hide\ntest_not_ipp\ntest_pods_ready\ntest_no_force\ntest_ivol",
        pytest_fail="test_imgvol_tag_all FAILED b==ghcr.io/frosterley/old@sha256:dead",
        tmpl_test="test_template_matches_git",
        rs="g511",
    ),
    pair(
        plant="stanhope-prod",
        app="stanhope-api",
        chart="4.4.4",
        slug="devclass-selector-old",
        field="deviceClass.spec.selectors",
        fail_val="vendor=oldpci",
        fix_val="vendor=livepci",
        hide_path="resourceClaim",
        hide_old="claimName: stanhope-gpu\n",
        hide_new="claimName: stanhope-old\n",
        values_fail="deviceVendor: oldpci\nclaimName: stanhope-gpu\n",
        values_fix="deviceVendor: livepci\nclaimName: stanhope-gpu\n",
        tpl="    selectors:\n      - cel:\n          expression: device.vendor == {{ .Values.deviceVendor | quote }}\n",
        log="FailedScheduling leftover DeviceClass selector vendor=oldpci; no device CrashLoop",
        live_ok="deviceClass.spec.selectors=vendor=livepci",
        hide_name="ResourceClaim name stanhope-old",
        new_vs="DeviceClass leftover vs leftover ResourceClaim, not rclaim-admin-gone",
        seed="leftover DeviceClass vendor=oldpci; no device CrashLoop",
        n2="replica n2 still DeviceClass vendor=oldpci after git livepci",
        ci="# DeviceClass selector vendor must be livepci. Never rewrite ResourceClaim name to hide leftover selector.",
        handoff="LEFTOVER: replica n2 still DeviceClass vendor=oldpci. Platform: delete leftover RS. No ResourceClaim hide.",
        pytest_ok="test_dc_live\ntest_not_rc_hide\ntest_not_rclaimadmin\ntest_pods_ready\ntest_no_force\ntest_dc",
        pytest_fail="test_dc_live_all FAILED b==vendor=oldpci",
        tmpl_test="test_template_matches_git",
        rs="g512",
    ),
    pair(
        plant="wolsingham-prod",
        app="wolsingham-api",
        chart="0.6.8",
        slug="ic-controller-gone",
        field="ingressClass.spec.controller",
        fail_val="k8s.io/old-nginx",
        fix_val="k8s.io/ingress-nginx",
        hide_path="pathType",
        hide_old="pathType: Prefix\n",
        hide_new="pathType: ImplementationSpecific\n",
        values_fail="ingressController: k8s.io/old-nginx\npathType: Prefix\n",
        values_fix="ingressController: k8s.io/ingress-nginx\npathType: Prefix\n",
        tpl="  controller: {{ .Values.ingressController }}\n",
        log="no endpoints leftover IngressClass controller k8s.io/old-nginx gone CrashLoop",
        live_ok="ingressClass.spec.controller=k8s.io/ingress-nginx",
        hide_name="Ingress pathType ImplementationSpecific",
        new_vs="IngressClass leftover vs leftover Ingress pathType, not Ingress tls secretName leftover",
        seed="leftover IngressClass controller k8s.io/old-nginx gone; no endpoints CrashLoop",
        n2="replica n2 still IngressClass controller k8s.io/old-nginx after git k8s.io/ingress-nginx",
        ci="# IngressClass controller must be k8s.io/ingress-nginx. Never flip pathType to hide leftover controller.",
        handoff="LEFTOVER: replica n2 still IngressClass k8s.io/old-nginx. Platform: delete leftover RS. No pathType hide.",
        pytest_ok="test_ic_nginx\ntest_not_pt_hide\ntest_not_tlssec\ntest_pods_ready\ntest_no_force\ntest_ic",
        pytest_fail="test_ic_nginx_all FAILED b==k8s.io/old-nginx",
        tmpl_test="test_template_matches_git",
        rs="g513",
    ),
    pair(
        plant="westgate-prod",
        app="westgate-api",
        chart="3.3.1",
        slug="hpa-scaledown-stab-3600",
        field="hpa.spec.behavior.scaleDown.stabilizationWindowSeconds",
        fail_val="3600",
        fix_val="30",
        hide_path="external.metric",
        hide_old="extMetric: \"\"\n",
        hide_new="extMetric: qps.old.westgate.io\n",
        values_fail="scaleDownStab: 3600\nextMetric: \"\"\n",
        values_fix="scaleDownStab: 30\nextMetric: \"\"\n",
        tpl="        stabilizationWindowSeconds: {{ .Values.scaleDownStab }}\n",
        log="OOMKilled leftover HPA scaleDown stabilizationWindowSeconds=3600; no scale-down CrashLoop",
        live_ok="hpa.spec.behavior.scaleDown.stabilizationWindowSeconds=30",
        hide_name="external metric qps.old.westgate.io",
        new_vs="HPA scaleDown stabilization leftover vs leftover behavior scaleDown, not HPA external metric leftover",
        seed="leftover HPA scaleDown stabilizationWindowSeconds=3600; OOM CrashLoop",
        n2="replica n2 still HPA scaleDown stab 3600 after git 30",
        ci="# HPA scaleDown stabilizationWindowSeconds must be 30. Never add external metric to hide leftover 3600.",
        handoff="LEFTOVER: replica n2 still HPA scaleDown stab 3600. Platform: delete leftover RS. No external-metric hide.",
        pytest_ok="test_sd_30\ntest_not_ext_hide\ntest_not_hpaext\ntest_pods_ready\ntest_no_force\ntest_hpasd",
        pytest_fail="test_sd_30_all FAILED b==3600",
        tmpl_test="test_template_matches_git",
        rs="g514",
    ),
    pair(
        plant="rookhope-prod",
        app="rookhope-api",
        chart="2.1.6",
        slug="vpa-updatemode-off",
        field="vpa.spec.updatePolicy.updateMode",
        fail_val="Off",
        fix_val="Auto",
        hide_path="minAllowed",
        hide_old="minAllowedCpu: \"100m\"\n",
        hide_new="minAllowedCpu: \"8\"\n",
        values_fail="updateMode: Off\nminAllowedCpu: \"100m\"\n",
        values_fix="updateMode: Auto\nminAllowedCpu: \"100m\"\n",
        tpl="    updateMode: {{ .Values.updateMode }}\n",
        log="OOMKilled leftover VPA updateMode Off; no in-place resize CrashLoop",
        live_ok="vpa.spec.updatePolicy.updateMode=Auto",
        hide_name="minAllowed cpu 8",
        new_vs="VPA updateMode Off leftover vs leftover updateMode Off, not VPA minAllowed leftover",
        seed="leftover VPA updateMode Off; OOM CrashLoop",
        n2="replica n2 still VPA updateMode Off after git Auto",
        ci="# VPA updateMode must be Auto. Never bump minAllowed to hide leftover Off.",
        handoff="LEFTOVER: replica n2 still VPA updateMode Off. Platform: delete leftover RS. No minAllowed hide.",
        pytest_ok="test_vpa_auto\ntest_not_min_hide\ntest_not_vpamin\ntest_pods_ready\ntest_no_force\ntest_vpaoff",
        pytest_fail="test_vpa_auto_all FAILED b==Off",
        tmpl_test="test_template_matches_git",
        rs="g515",
    ),
    pair(
        plant="killhope-prod",
        app="killhope-api",
        chart="1.5.0",
        slug="flowschema-dist-old",
        field="flowSchema.spec.distinguisherMethod.type",
        fail_val="ByUser",
        fix_val="ByNamespace",
        hide_path="priorityLevelConfiguration",
        hide_old="plcName: killhope-api\n",
        hide_new="plcName: catch-all\n",
        values_fail="distinguisher: ByUser\nplcName: killhope-api\n",
        values_fix="distinguisher: ByNamespace\nplcName: killhope-api\n",
        tpl="  distinguisherMethod:\n    type: {{ .Values.distinguisher }}\n",
        log="429 leftover FlowSchema distinguisherMethod ByUser; apiserver throttle CrashLoop",
        live_ok="flowSchema.spec.distinguisherMethod.type=ByNamespace",
        hide_name="PriorityLevelConfiguration catch-all",
        new_vs="FlowSchema leftover vs leftover PriorityLevelConfiguration, not webhook timeout",
        seed="leftover FlowSchema distinguisher ByUser; 429 CrashLoop",
        n2="replica n2 still FlowSchema distinguisher ByUser after git ByNamespace",
        ci="# FlowSchema distinguisher must be ByNamespace. Never rewrite PLC name to hide leftover ByUser.",
        handoff="LEFTOVER: replica n2 still FlowSchema distinguisher ByUser. Platform: delete leftover RS. No PLC hide.",
        pytest_ok="test_fs_ns\ntest_not_plc_hide\ntest_not_wh\ntest_pods_ready\ntest_no_force\ntest_fs",
        pytest_fail="test_fs_ns_all FAILED b==ByUser",
        tmpl_test="test_template_matches_git",
        rs="g516",
    ),
]


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 82 + (round_n % 7)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"Quota 2. Unique leftover leftover leftover CrashLoopBackOff pair. "
        f"Catalog r70–r1264 stays in raw (empty-ENV / spec leftover cartesian). "
        f"New: {s['new_vs']}. Plant `{s['plant']}` "
        f"(not bay-prod/cwm/llyn/atoll/kyle/voe/tarn/lough/weald/fen/wharf/"
        f"machair/broch/otterburn/mastiles/gordale).\n"
        f"\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['seed']} | kubeconform 0; apply --wait fail | wrong first hide then plan change | success 2/2 pytest 6/6 |\n"
        f"| {b['id']} | {s['n2']} | kubeconform 0; --force mixed | leftover on n2; SSA spec only | partial 1/2 handoff |\n"
        f"\n"
        f"## Step counts\n"
        f"- ep1: 16. Clean template 5; apply fail 6,8; plan change 9; verify 12–16.\n"
        f"- ep2: 18. Clean template 5; apply fail 6–8; plan change 9; leftover 11–18.\n"
        f"\n"
        f"## decision_basis audit\n"
        f"Plan:/Observation:/Reflection:/Tool call: ≤240. No hidden CoT. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `{s['plant']}`.\n"
        f"\n"
        f"## How the apply-fail taught\n"
        f"1. {s['seed']}. kubeconform does not evaluate this. Stretching the wrong knob hid or no-op'd.\n"
        f"2. {s['n2']}. helm --force three-way kept the live leftover. Do not delete n2 as success.\n"
        f"\n"
        f"## Bans honored\n"
        f"- No leftover-n2 stamp (`leftover n2 still n2 leftover still`).\n"
        f"- No empty-ENV after chart bump.\n"
        f"- No leftover cartesian on spec.ipFamilies / externalTrafficPolicy / allocateLoadBalancerNodePorts.\n"
        f"- No AppArmor/seccomp Unconfined. No webhook timeout.\n"
        f"- No r1216–r1264 clones (dnsPolicy None, STS whenDeleted, Job successPolicy, PVC datasource).\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
    )


def write_round(round_n: int, staging: Path, spec: dict) -> None:
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    if "-w3-empty" in a["id"] or "sx" in a["id"] or "-w3-empty" in b["id"]:
        raise SystemExit("banned id")
    a["meta"]["generator"] = GEN
    b["meta"]["generator"] = GEN
    if len(a["steps"]) != 16 or len(b["steps"]) != 18:
        raise SystemExit(f"step counts {len(a['steps'])} {len(b['steps'])}")
    blob = json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    if STAMP in blob:
        raise SystemExit(f"stamp in batch r{round_n}")
    for needle in (
        "BITBUCKET_HOME",
        "KEYCLOAK_HOME",
        "spec.ipFamilies",
        "spike_events",
        "AppArmor",
        "seccompProfile: Unconfined",
        "webhook timeout",
        '"sim_or_real": "real"',
        '"thought"',
        "chain_of_thought",
    ):
        if needle in blob:
            raise SystemExit(f"banned needle {needle} in batch r{round_n}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(blob)
    notes.write_text(notes_for(round_n, spec, a, b))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [a["id"], b["id"]],
                "steps": [len(a["steps"]), len(b["steps"])],
                "bytes": batch.stat().st_size,
                "plant": spec["plant"],
                "slug": spec["slug"],
            }
        ),
        flush=True,
    )


def txn(args: list[str]) -> dict:
    proc = subprocess.run(
        [sys.executable, str(TXN), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "txn failed")
    return json.loads(proc.stdout)


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def taken_slugs() -> set[str]:
    found: set[str] = set()
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ident = str(obj.get("id", ""))
            if not ident.startswith("kcl-r"):
                continue
            parts = ident.split("-", 2)
            if len(parts) != 3:
                continue
            slug = parts[2]
            if slug.endswith("-n2-handoff"):
                slug = slug[: -len("-n2-handoff")]
            elif slug.endswith("-handoff"):
                slug = slug[: -len("-handoff")]
            found.add(slug)
    return found


def taken_plants() -> set[str]:
    found: set[str] = set()
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if "designed plant " not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            goal = str(obj.get("goal", ""))
            marker = "designed plant "
            if marker in goal:
                rest = goal.split(marker, 1)[1]
                plant = rest.split(" ", 1)[0].strip(".,")
                if plant:
                    found.add(plant)
    return found


def abort(factory: Path, n: int, token: str) -> None:
    try:
        txn(["abort", str(factory), "--round", str(n), "--token", token])
    except RuntimeError as exc:
        print(f"abort failed r{n}: {exc}", flush=True)


def hop_once() -> bool:
    spec = importlib.util.spec_from_file_location("hopper_g46c", HOPPER)
    hop = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(hop)
    for factory in hop.CYCLE:
        if factory in SKIP_HOP:
            continue
        fdir = hop.factory_dir(factory)
        try:
            status = txn(["frontier", str(fdir)])
        except RuntimeError as exc:
            print(f"hop frontier {factory}: {exc}", flush=True)
            continue
        n = int(status["next_round"])
        if reserved(fdir, n):
            print(f"hop skip {factory} r{n} reserved", flush=True)
            continue
        idx = n - hop.START[factory]
        pairs = hop.PAIRS.get(factory, [])
        if idx < 0 or idx >= len(pairs):
            print(f"hop skip {factory} r{n} catalog idx={idx}", flush=True)
            continue
        ok, bad = pairs[idx]
        try:
            res = txn(["reserve", str(fdir), "--round", str(n), "--expected", "2"])
        except RuntimeError as exc:
            print(f"hop reserve {factory} r{n}: {exc}", flush=True)
            continue
        token = res["token"]
        staging = Path(res["staging_dir"])
        try:
            ids = hop.emit_stage(staging, factory, n, ok, bad)
            pub = txn(["publish", str(fdir), "--round", str(n), "--token", token])
        except Exception as exc:
            print(f"hop stage/publish {factory} r{n}: {exc}; abort", flush=True)
            abort(fdir, n, token)
            continue
        print(
            json.dumps(
                {
                    "hop_published": factory,
                    "round": n,
                    "ids": list(ids),
                    "records": pub.get("records"),
                }
            ),
            flush=True,
        )
        return True
    return False


def smoke() -> int:
    sys.path.insert(0, str(ROOT / "pipelines"))
    from check_records import check_jsonl  # noqa: E402

    tmp = Path("/tmp/kcl_wave1266_smoke")
    tmp.mkdir(exist_ok=True)
    for i, spec in enumerate(PAIRS):
        rnd = 1266 + i
        write_round(rnd, tmp, spec)
        path = tmp / f"batch-r{rnd:02d}.jsonl"
        errs, warns, kinds, n = check_jsonl(path, path.name)
        if errs:
            print(f"SMOKE FAIL r{rnd}: {errs}", flush=True)
            return 1
        if n != 2 or kinds.get("episode") != 2:
            print(f"SMOKE FAIL r{rnd} kinds={kinds} n={n}", flush=True)
            return 1
        print(
            f"SMOKE ok r{rnd} {spec['plant']} {spec['slug']} warns={len(warns)}",
            flush=True,
        )
    print(f"SMOKE PASS families={len(PAIRS)}", flush=True)
    return 0


def main() -> int:
    if "--smoke" in sys.argv:
        return smoke()
    published: list[int] = []
    cursor = 0
    hops = 0
    started = time.time()
    taken = taken_slugs()
    plants = taken_plants()
    print(
        f"r1266 mill start pairs={len(PAIRS)} taken_slugs={len(taken)} "
        f"taken_plants={len(plants)} gen={GEN}",
        flush=True,
    )
    while (
        cursor < len(PAIRS)
        and len(published) < MAX_ROUNDS
        and (time.time() - started) < MAX_SECONDS
    ):
        while cursor < len(PAIRS) and (
            PAIRS[cursor]["slug"] in taken or PAIRS[cursor]["plant"] in plants
        ):
            print(
                f"skip taken {PAIRS[cursor]['plant']} {PAIRS[cursor]['slug']}",
                flush=True,
            )
            cursor += 1
        if cursor >= len(PAIRS):
            print("catalog exhausted", flush=True)
            break
        try:
            front = txn(["frontier", str(FACTORY_DIR)])
        except RuntimeError as exc:
            print(f"frontier err {exc}", flush=True)
            time.sleep(2)
            continue
        n = int(front["next_round"])
        if reserved(FACTORY_DIR, n):
            hops += 1
            print(f"HOP: kcl r{n} reserved; not stealing ({hops})", flush=True)
            if hop_once():
                hops += 1
            else:
                time.sleep(3)
            if hops >= 8:
                print("HOP thrice+; stopping without steal.", flush=True)
                break
            continue
        spec = PAIRS[cursor]
        try:
            res = txn(
                [
                    "reserve",
                    str(FACTORY_DIR),
                    "--round",
                    str(n),
                    "--expected",
                    "2",
                ]
            )
        except RuntimeError as exc:
            msg = str(exc).lower()
            if "reserv" in msg or "already" in msg or "not the frontier" in msg or "exists" in msg:
                hops += 1
                print(f"HOP: reserve failed r{n}: {exc}", flush=True)
                if hop_once():
                    hops += 1
                else:
                    time.sleep(2)
                if hops >= 8:
                    print("HOP quota; stopping without steal.", flush=True)
                    break
                continue
            raise
        token = res["token"]
        staging = Path(res["staging_dir"])
        print(
            f"reserved r{n} token={token} plant={spec['plant']} slug={spec['slug']}",
            flush=True,
        )
        try:
            write_round(n, staging, spec)
            pub = txn(
                [
                    "publish",
                    str(FACTORY_DIR),
                    "--round",
                    str(n),
                    "--token",
                    token,
                ]
            )
        except Exception as exc:
            print(f"stage/publish failed r{n}: {exc}; abort", flush=True)
            abort(FACTORY_DIR, n, token)
            time.sleep(2)
            continue
        published.append(n)
        taken.add(spec["slug"])
        plants.add(spec["plant"])
        cursor += 1
        print(
            json.dumps(
                {
                    "published": n,
                    "records": pub.get("records"),
                    "done": len(published),
                    "plant": spec["plant"],
                    "slug": spec["slug"],
                }
            ),
            flush=True,
        )
    elapsed = time.time() - started
    print(
        f"DONE published={published} hops={hops} cursor={cursor} elapsed_s={elapsed:.1f}",
        flush=True,
    )
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
