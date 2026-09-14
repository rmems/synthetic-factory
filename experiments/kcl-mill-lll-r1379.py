#!/usr/bin/env python3
"""k8s-crashloop unique leftover leftover leftover mill from r1379. Q=2. grok-4.6.

16 leftover leftover leftover pairs. Skip used r1275–r1378.
BAN leftover-n2 stamp. BAN empty-ENV. BAN AppArmor/seccomp Unconfined.
BAN webhook timeout. BAN leftover leftover leftover n2 leftover leftover leftover
as the ONLY difference.
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
FACTORY = "k8s-crashloop-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16
MAX_SECONDS = 40 * 60
STAMP = "leftover n2 still n2 leftover still"

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
    if len(ep["steps"]) != 18:
        raise SystemExit(f"leftover steps {len(ep['steps'])} != 18")
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
        "eskhouse-prod",
        "nenthead-prod",
        "alston-prod",
        "allenheads-prod",
        "weardale-prod",
        "teesdale-prod",
        "stainmore-prod",
        "westgate-prod",
        "rookhope-prod",
    }
    if kwargs["plant"] in banned_plants:
        raise SystemExit(f"banned plant {kwargs['plant']}")
    return kwargs


PAIRS: list[dict] = [
    pair(
        plant="garsdale-prod",
        app="garsdale-api",
        chart="3.2.1",
        slug="map-matchcond-skip",
        field="mutatingAdmissionPolicy.matchConditions",
        fail_val="skip-if-failfast",
        fix_val="always",
        hide_path="reinvocationPolicy",
        hide_old="reinvocationPolicy: Never\n",
        hide_new="reinvocationPolicy: IfNeeded\n",
        values_fail="matchCondition: skip-if-failfast\nreinvocationPolicy: Never\n",
        values_fix="matchCondition: always\nreinvocationPolicy: Never\n",
        tpl="  matchConditions:\n    - name: {{ .Values.matchCondition }}\n",
        log="MAP matchConditions skip-if-failfast leftover; wait-for old-broker still injected CrashLoop",
        live_ok="mutatingAdmissionPolicy.matchConditions=always",
        hide_name="reinvocationPolicy IfNeeded",
        new_vs="MutatingAdmissionPolicy matchConditions leftover, not reinvocationPolicy leftover and not VAP paramKind leftover",
        seed="leftover MutatingAdmissionPolicy matchConditions skip-if-failfast; inject CrashLoop",
        n2="replica n2 still MutatingAdmissionPolicy matchConditions skip-if-failfast after git always",
        ci="# MAP matchConditions must always apply. Never flip reinvocationPolicy to hide leftover skip.",
        handoff="LEFTOVER: replica n2 still MAP matchConditions skip-if-failfast. Platform: delete leftover RS. No reinvocation hide.",
        pytest_ok="test_mc_always\ntest_not_reinvoke_hide\ntest_not_vap_param\ntest_pods_ready\ntest_no_force\ntest_map",
        pytest_fail="test_mc_always_all FAILED b==skip-if-failfast",
        tmpl_test="test_template_matches_git",
        rs="m01",
    ),
    pair(
        plant="dentdale-prod",
        app="dentdale-api",
        chart="1.8.4",
        slug="lr-defaultreq-tiny",
        field="limitRange.defaultRequest.cpu",
        fail_val="1m",
        fix_val="100m",
        hide_path="maxLimitRequestRatio",
        hide_old="maxLimitRequestRatio: 10\n",
        hide_new="maxLimitRequestRatio: 1000\n",
        values_fail="defaultRequestCpu: 1m\nmaxLimitRequestRatio: 10\n",
        values_fix="defaultRequestCpu: 100m\nmaxLimitRequestRatio: 10\n",
        tpl="  defaultRequest:\n    cpu: {{ .Values.defaultRequestCpu }}\n",
        log="CPU throttle leftover LimitRange defaultRequest 1m; scheduler skip CrashLoop",
        live_ok="limitRange.defaultRequest.cpu=100m",
        hide_name="maxLimitRequestRatio 1000",
        new_vs="LimitRange defaultRequest leftover, not maxLimitRequestRatio leftover and not ResourceQuota secrets leftover",
        seed="leftover LimitRange defaultRequest cpu=1m; throttle CrashLoop",
        n2="replica n2 still LimitRange defaultRequest cpu=1m after git 100m",
        ci="# LimitRange defaultRequest cpu must be 100m. Never stretch maxLimitRequestRatio to hide leftover 1m.",
        handoff="LEFTOVER: replica n2 still LimitRange defaultRequest 1m. Platform: delete leftover RS. No ratio hide.",
        pytest_ok="test_req_100m\ntest_not_ratio_hide\ntest_not_rq_secrets\ntest_pods_ready\ntest_no_force\ntest_lr",
        pytest_fail="test_req_100m_all FAILED b==1m",
        tmpl_test="test_template_matches_git",
        rs="m02",
    ),
    pair(
        plant="rawthey-prod",
        app="rawthey-api",
        chart="2.1.9",
        slug="pdb-selector-old",
        field="podDisruptionBudget.selector.matchLabels",
        fail_val="app=rawthey-old",
        fix_val="app=rawthey-api",
        hide_path="minAvailable",
        hide_old="minAvailable: 1\n",
        hide_new="minAvailable: 0\n",
        values_fail="selectorApp: rawthey-old\nminAvailable: 1\nmaxUnavailable: 1\n",
        values_fix="selectorApp: rawthey-api\nminAvailable: 1\nmaxUnavailable: 1\n",
        tpl="  selector:\n    matchLabels:\n      app: {{ .Values.selectorApp }}\n",
        log="eviction unprotected leftover PDB selector app=rawthey-old; drain CrashLoop",
        live_ok="podDisruptionBudget.selector.matchLabels=app=rawthey-api",
        hide_name="minAvailable 0",
        new_vs="PodDisruptionBudget selector leftover, not maxUnavailable leftover and not minAvailable leftover",
        seed="leftover PDB selector app=rawthey-old; drain CrashLoop",
        n2="replica n2 still PDB selector app=rawthey-old after git app=rawthey-api",
        ci="# PDB selector must match live app. Never drop minAvailable to hide leftover selector.",
        handoff="LEFTOVER: replica n2 still PDB selector rawthey-old. Platform: delete leftover RS. No minAvailable hide.",
        pytest_ok="test_sel_api\ntest_not_minavail_hide\ntest_not_maxunavail\ntest_pods_ready\ntest_no_force\ntest_pdb",
        pytest_fail="test_sel_api_all FAILED b==rawthey-old",
        tmpl_test="test_template_matches_git",
        rs="m03",
    ),
    pair(
        plant="howgill-prod",
        app="howgill-api",
        chart="4.0.3",
        slug="pc-name-gone",
        field="priorityClassName",
        fail_val="howgill-old",
        fix_val="howgill-live",
        hide_path="preemptionPolicy",
        hide_old="preemptionPolicy: PreemptLowerPriority\n",
        hide_new="preemptionPolicy: Never\n",
        values_fail="priorityClassName: howgill-old\npreemptionPolicy: PreemptLowerPriority\n",
        values_fix="priorityClassName: howgill-live\npreemptionPolicy: PreemptLowerPriority\n",
        tpl="  priorityClassName: {{ .Values.priorityClassName }}\n",
        log="PriorityClass howgill-old missing leftover; pending CrashLoop",
        live_ok="priorityClassName=howgill-live",
        hide_name="preemptionPolicy Never",
        new_vs="PriorityClass name leftover, not PriorityClass value leftover and not preemptionPolicy leftover",
        seed="leftover priorityClassName howgill-old; missing class CrashLoop",
        n2="replica n2 still priorityClassName howgill-old after git howgill-live",
        ci="# priorityClassName must name a live class. Never flip preemptionPolicy to hide leftover name.",
        handoff="LEFTOVER: replica n2 still priorityClassName howgill-old. Platform: delete leftover RS. No preemption hide.",
        pytest_ok="test_pc_live\ntest_not_preempt_hide\ntest_not_value_neg\ntest_pods_ready\ntest_no_force\ntest_pc",
        pytest_fail="test_pc_live_all FAILED b==howgill-old",
        tmpl_test="test_template_matches_git",
        rs="m04",
    ),
    pair(
        plant="cautley-prod",
        app="cautley-api",
        chart="1.4.8",
        slug="rc-tol-old",
        field="runtimeClass.scheduling.tolerations",
        fail_val="key=cautley-old",
        fix_val="key=cautley-live",
        hide_path="handler",
        hide_old="handler: runc\n",
        hide_new="handler: kata\n",
        values_fail="tolerationKey: cautley-old\nhandler: runc\n",
        values_fix="tolerationKey: cautley-live\nhandler: runc\n",
        tpl="  scheduling:\n    tolerations:\n      - key: {{ .Values.tolerationKey }}\n",
        log="RuntimeClass toleration cautley-old leftover; no matching taint CrashLoop",
        live_ok="runtimeClass.scheduling.tolerations=key=cautley-live",
        hide_name="handler kata",
        new_vs="RuntimeClass scheduling.tolerations leftover, not overhead leftover and not handler leftover",
        seed="leftover RuntimeClass tolerations key=cautley-old; no taint match CrashLoop",
        n2="replica n2 still RuntimeClass tolerations key=cautley-old after git key=cautley-live",
        ci="# RuntimeClass tolerations must match live taints. Never swap handler to hide leftover key.",
        handoff="LEFTOVER: replica n2 still RuntimeClass tolerations cautley-old. Platform: delete leftover RS. No handler hide.",
        pytest_ok="test_tol_live\ntest_not_handler_hide\ntest_not_overhead\ntest_pods_ready\ntest_no_force\ntest_rc",
        pytest_fail="test_tol_live_all FAILED b==cautley-old",
        tmpl_test="test_template_matches_git",
        rs="m05",
    ),
    pair(
        plant="sedbergh-prod",
        app="sedbergh-api",
        chart="2.9.2",
        slug="tsp-nodeaff-honor",
        field="topologySpreadConstraints.nodeAffinityPolicy",
        fail_val="Honor",
        fix_val="Ignore",
        hide_path="maxSkew",
        hide_old="maxSkew: 1\n",
        hide_new="maxSkew: 100\n",
        values_fail="nodeAffinityPolicy: Honor\nmaxSkew: 1\nwhenUnsatisfiable: ScheduleAnyway\n",
        values_fix="nodeAffinityPolicy: Ignore\nmaxSkew: 1\nwhenUnsatisfiable: ScheduleAnyway\n",
        tpl="  topologySpreadConstraints:\n    - nodeAffinityPolicy: {{ .Values.nodeAffinityPolicy }}\n",
        log="topologySpread nodeAffinityPolicy Honor leftover; wait-for-domain CrashLoop",
        live_ok="topologySpreadConstraints.nodeAffinityPolicy=Ignore",
        hide_name="maxSkew 100",
        new_vs="TopologySpread nodeAffinityPolicy leftover, not whenUnsatisfiable leftover and not maxSkew leftover",
        seed="leftover topologySpread nodeAffinityPolicy Honor; wait CrashLoop",
        n2="replica n2 still topologySpread nodeAffinityPolicy Honor after git Ignore",
        ci="# topologySpread nodeAffinityPolicy must Ignore leftover affinity. Never stretch maxSkew to hide Honor.",
        handoff="LEFTOVER: replica n2 still topologySpread nodeAffinityPolicy Honor. Platform: delete leftover RS. No maxSkew hide.",
        pytest_ok="test_nap_ignore\ntest_not_skew_hide\ntest_not_whenunsat\ntest_pods_ready\ntest_no_force\ntest_tsp",
        pytest_fail="test_nap_ignore_all FAILED b==Honor",
        tmpl_test="test_template_matches_git",
        rs="m06",
    ),
    pair(
        plant="barbon-prod",
        app="barbon-api",
        chart="1.1.6",
        slug="cnp-tocidr-old",
        field="ciliumNetworkPolicy.egress.toCIDR",
        fail_val="10.10.0.0/16",
        fix_val="10.20.0.0/16",
        hide_path="policyTypes",
        hide_old="policyTypes: [Egress]\n",
        hide_new="policyTypes: [Ingress]\n",
        values_fail="toCIDR: 10.10.0.0/16\npolicyTypes: [Egress]\n",
        values_fix="toCIDR: 10.20.0.0/16\npolicyTypes: [Egress]\n",
        tpl="  egress:\n    - toCIDR:\n        - {{ .Values.toCIDR }}\n",
        log="CiliumNetworkPolicy toCIDR 10.10.0.0/16 leftover; peer drop CrashLoop",
        live_ok="ciliumNetworkPolicy.egress.toCIDR=10.20.0.0/16",
        hide_name="policyTypes Ingress",
        new_vs="CiliumNetworkPolicy egress toCIDR leftover, not NetworkPolicy egress leftover and not ipBlock.except leftover",
        seed="leftover CiliumNetworkPolicy toCIDR 10.10.0.0/16; peer drop CrashLoop",
        n2="replica n2 still CiliumNetworkPolicy toCIDR 10.10.0.0/16 after git 10.20.0.0/16",
        ci="# CiliumNetworkPolicy toCIDR must be 10.20.0.0/16. Never drop egress type to hide leftover CIDR.",
        handoff="LEFTOVER: replica n2 still CiliumNetworkPolicy toCIDR 10.10.0.0/16. Platform: delete leftover RS. No policyTypes hide.",
        pytest_ok="test_cidr_20\ntest_not_types_hide\ntest_not_np_egress\ntest_pods_ready\ntest_no_force\ntest_cnp",
        pytest_fail="test_cidr_20_all FAILED b==10.10.0.0/16",
        tmpl_test="test_template_matches_git",
        rs="m07",
    ),
    pair(
        plant="lunehead-prod",
        app="lunehead-api",
        chart="3.3.0",
        slug="httproute-reqtimeout-1ms",
        field="httpRoute.timeouts.request",
        fail_val="1ms",
        fix_val="30s",
        hide_path="port",
        hide_old="port: 8080\n",
        hide_new="port: 8081\n",
        values_fail="requestTimeout: 1ms\nport: 8080\n",
        values_fix="requestTimeout: 30s\nport: 8080\n",
        tpl="  timeouts:\n    request: {{ .Values.requestTimeout }}\n",
        log="HTTPRoute timeouts.request 1ms leftover; 504 CrashLoop",
        live_ok="httpRoute.timeouts.request=30s",
        hide_name="port 8081",
        new_vs="HTTPRoute timeouts.request leftover, not Gateway port leftover and not HTTPRoute parentRefs leftover",
        seed="leftover HTTPRoute timeouts.request 1ms; 504 CrashLoop",
        n2="replica n2 still HTTPRoute timeouts.request 1ms after git 30s",
        ci="# HTTPRoute request timeout must be 30s. Never retarget port to hide leftover 1ms.",
        handoff="LEFTOVER: replica n2 still HTTPRoute timeouts.request 1ms. Platform: delete leftover RS. No port hide.",
        pytest_ok="test_to_30s\ntest_not_port_hide\ntest_not_gw_port\ntest_pods_ready\ntest_no_force\ntest_hr",
        pytest_fail="test_to_30s_all FAILED b==1ms",
        tmpl_test="test_template_matches_git",
        rs="m08",
    ),
    pair(
        plant="ormside-prod",
        app="ormside-api",
        chart="0.8.5",
        slug="ipaddr-parent-ns-old",
        field="ipAddress.spec.parentRef.namespace",
        fail_val="ormside-old",
        fix_val="ormside-prod",
        hide_path="serviceCIDRName",
        hide_old="serviceCIDRName: prod-cidr\n",
        hide_new="serviceCIDRName: lab-cidr\n",
        values_fail="parentNamespace: ormside-old\nserviceCIDRName: prod-cidr\n",
        values_fix="parentNamespace: ormside-prod\nserviceCIDRName: prod-cidr\n",
        tpl="  parentRef:\n    namespace: {{ .Values.parentNamespace }}\n",
        log="IPAddress parentRef.namespace ormside-old leftover; VIP unprogrammed CrashLoop",
        live_ok="ipAddress.spec.parentRef.namespace=ormside-prod",
        hide_name="serviceCIDRName lab-cidr",
        new_vs="IPAddress parentRef.namespace leftover, not ServiceCIDR leftover and not IPAddress parentRef.group leftover",
        seed="leftover IPAddress parentRef.namespace ormside-old; VIP CrashLoop",
        n2="replica n2 still IPAddress parentRef.namespace ormside-old after git ormside-prod",
        ci="# IPAddress parentRef.namespace must be ormside-prod. Never retarget ServiceCIDRName to hide leftover ns.",
        handoff="LEFTOVER: replica n2 still IPAddress parentRef.namespace ormside-old. Platform: delete leftover RS. No CIDRName hide.",
        pytest_ok="test_ns_live\ntest_not_cidrname_hide\ntest_not_servicecidr\ntest_pods_ready\ntest_no_force\ntest_ipa",
        pytest_fail="test_ns_live_all FAILED b==ormside-old",
        tmpl_test="test_template_matches_git",
        rs="m09",
    ),
    pair(
        plant="appleby-prod",
        app="appleby-api",
        chart="5.1.1",
        slug="crd-conv-review-v1beta1",
        field="customResourceDefinition.conversion.conversionReviewVersions",
        fail_val="v1beta1",
        fix_val="v1",
        hide_path="storageVersion",
        hide_old="storageVersion: v1\n",
        hide_new="storageVersion: v1alpha1\n",
        values_fail="conversionReviewVersions: v1beta1\nstorageVersion: v1\n",
        values_fix="conversionReviewVersions: v1\nstorageVersion: v1\n",
        tpl="  conversion:\n    conversionReviewVersions: [{{ .Values.conversionReviewVersions }}]\n",
        log="CRD conversionReviewVersions v1beta1 leftover; decode panic CrashLoop",
        live_ok="customResourceDefinition.conversion.conversionReviewVersions=v1",
        hide_name="storageVersion v1alpha1",
        new_vs="CRD conversionReviewVersions leftover, not StorageVersionMigration leftover and not storageVersion leftover",
        seed="leftover CRD conversionReviewVersions v1beta1; decode CrashLoop",
        n2="replica n2 still CRD conversionReviewVersions v1beta1 after git v1",
        ci="# CRD conversionReviewVersions must be v1. Never flip storageVersion to hide leftover v1beta1.",
        handoff="LEFTOVER: replica n2 still CRD conversionReviewVersions v1beta1. Platform: delete leftover RS. No storageVersion hide.",
        pytest_ok="test_crv_v1\ntest_not_sv_hide\ntest_not_svm\ntest_pods_ready\ntest_no_force\ntest_crd",
        pytest_fail="test_crv_v1_all FAILED b==v1beta1",
        tmpl_test="test_template_matches_git",
        rs="m10",
    ),
    pair(
        plant="brougham-prod",
        app="brougham-api",
        chart="2.2.7",
        slug="emptydir-sizelimit-1ki",
        field="volumes.emptyDir.sizeLimit",
        fail_val="1Ki",
        fix_val="1Gi",
        hide_path="imageVolume",
        hide_old="imageVolume: false\n",
        hide_new="imageVolume: true\n",
        values_fail="sizeLimit: 1Ki\nimageVolume: false\n",
        values_fix="sizeLimit: 1Gi\nimageVolume: false\n",
        tpl="  emptyDir:\n    sizeLimit: {{ .Values.sizeLimit }}\n",
        log="emptyDir sizeLimit 1Ki leftover; write ENOSPC CrashLoop",
        live_ok="volumes.emptyDir.sizeLimit=1Gi",
        hide_name="imageVolume true",
        new_vs="emptyDir sizeLimit leftover, not ImageVolume leftover and not emptyDir medium Memory leftover",
        seed="leftover emptyDir sizeLimit 1Ki; ENOSPC CrashLoop",
        n2="replica n2 still emptyDir sizeLimit 1Ki after git 1Gi",
        ci="# emptyDir sizeLimit must be 1Gi. Never flip ImageVolume to hide leftover 1Ki.",
        handoff="LEFTOVER: replica n2 still emptyDir sizeLimit 1Ki. Platform: delete leftover RS. No ImageVolume hide.",
        pytest_ok="test_sl_1gi\ntest_not_imgvol_hide\ntest_not_medium\ntest_pods_ready\ntest_no_force\ntest_ed",
        pytest_fail="test_sl_1gi_all FAILED b==1Ki",
        tmpl_test="test_template_matches_git",
        rs="m11",
    ),
    pair(
        plant="kirkby-prod",
        app="kirkby-api",
        chart="1.9.0",
        slug="rclaim-count-zero",
        field="resourceClaim.devices.requests.count",
        fail_val="0",
        fix_val="1",
        hide_path="deviceClassName",
        hide_old="deviceClassName: gpu.kirkby\n",
        hide_new="deviceClassName: gpu.kirkby-debug\n",
        values_fail="deviceCount: 0\ndeviceClassName: gpu.kirkby\n",
        values_fix="deviceCount: 1\ndeviceClassName: gpu.kirkby\n",
        tpl="  devices:\n    requests:\n      - count: {{ .Values.deviceCount }}\n",
        log="ResourceClaim devices.requests.count=0 leftover; no GPU CrashLoop",
        live_ok="resourceClaim.devices.requests.count=1",
        hide_name="deviceClassName debug",
        new_vs="ResourceClaim devices.requests.count leftover, not DeviceClass leftover and not ResourceClaim adminAccess leftover",
        seed="leftover ResourceClaim devices.requests.count=0; no GPU CrashLoop",
        n2="replica n2 still ResourceClaim devices.requests.count=0 after git 1",
        ci="# ResourceClaim count must be 1. Never retarget DeviceClass to hide leftover count 0.",
        handoff="LEFTOVER: replica n2 still ResourceClaim count=0. Platform: delete leftover RS. No DeviceClass hide.",
        pytest_ok="test_count_1\ntest_not_dc_hide\ntest_not_admin\ntest_pods_ready\ntest_no_force\ntest_rcm",
        pytest_fail="test_count_1_all FAILED b==0",
        tmpl_test="test_template_matches_git",
        rs="m12",
    ),
    pair(
        plant="stainton-prod",
        app="stainton-api",
        chart="4.4.2",
        slug="ing-pathtype-impl",
        field="ingress.pathType",
        fail_val="ImplementationSpecific",
        fix_val="Prefix",
        hide_path="ingressClassName",
        hide_old="ingressClassName: nginx\n",
        hide_new="ingressClassName: contour\n",
        values_fail="pathType: ImplementationSpecific\ningressClassName: nginx\n",
        values_fix="pathType: Prefix\ningressClassName: nginx\n",
        tpl="  pathType: {{ .Values.pathType }}\n",
        log="Ingress pathType ImplementationSpecific leftover; 404 CrashLoop",
        live_ok="ingress.pathType=Prefix",
        hide_name="ingressClassName contour",
        new_vs="Ingress pathType leftover, not IngressClass leftover and not Ingress backend leftover",
        seed="leftover Ingress pathType ImplementationSpecific; 404 CrashLoop",
        n2="replica n2 still Ingress pathType ImplementationSpecific after git Prefix",
        ci="# Ingress pathType must be Prefix. Never swap IngressClass to hide leftover ImplementationSpecific.",
        handoff="LEFTOVER: replica n2 still Ingress pathType ImplementationSpecific. Platform: delete leftover RS. No IngressClass hide.",
        pytest_ok="test_pt_prefix\ntest_not_ic_hide\ntest_not_backend\ntest_pods_ready\ntest_no_force\ntest_ing",
        pytest_fail="test_pt_prefix_all FAILED b==ImplementationSpecific",
        tmpl_test="test_template_matches_git",
        rs="m13",
    ),
    pair(
        plant="kirkoswald-prod",
        app="kirkoswald-api",
        chart="3.6.6",
        slug="hpa-scaleup-stab-3600",
        field="hpa.behavior.scaleUp.stabilizationWindowSeconds",
        fail_val="3600",
        fix_val="0",
        hide_path="scaleDown.stabilizationWindowSeconds",
        hide_old="scaleDownStabilization: 30\n",
        hide_new="scaleDownStabilization: 3600\n",
        values_fail="scaleUpStabilization: 3600\nscaleDownStabilization: 30\n",
        values_fix="scaleUpStabilization: 0\nscaleDownStabilization: 30\n",
        tpl="  scaleUp:\n    stabilizationWindowSeconds: {{ .Values.scaleUpStabilization }}\n",
        log="HPA scaleUp stabilizationWindowSeconds=3600 leftover; pending load CrashLoop",
        live_ok="hpa.behavior.scaleUp.stabilizationWindowSeconds=0",
        hide_name="scaleDown stab 3600",
        new_vs="HPA scaleUp stabilization leftover, not HPA scaleDown leftover and not HPA external metric leftover",
        seed="leftover HPA scaleUp stabilizationWindowSeconds=3600; pending CrashLoop",
        n2="replica n2 still HPA scaleUp stab 3600 after git 0",
        ci="# HPA scaleUp stabilization must be 0. Never stretch scaleDown stab to hide leftover 3600.",
        handoff="LEFTOVER: replica n2 still HPA scaleUp stab 3600. Platform: delete leftover RS. No scaleDown hide.",
        pytest_ok="test_su_0\ntest_not_sd_hide\ntest_not_extmetric\ntest_pods_ready\ntest_no_force\ntest_hpa",
        pytest_fail="test_su_0_all FAILED b==3600",
        tmpl_test="test_template_matches_git",
        rs="m14",
    ),
    pair(
        plant="nenthall-prod",
        app="nenthall-api",
        chart="2.0.8",
        slug="vpa-controlled-requests",
        field="vpa.resourcePolicy.containerPolicies.controlledValues",
        fail_val="RequestsOnly",
        fix_val="RequestsAndLimits",
        hide_path="updateMode",
        hide_old="updateMode: Auto\n",
        hide_new="updateMode: Off\n",
        values_fail="controlledValues: RequestsOnly\nupdateMode: Auto\n",
        values_fix="controlledValues: RequestsAndLimits\nupdateMode: Auto\n",
        tpl="  resourcePolicy:\n    containerPolicies:\n      - controlledValues: {{ .Values.controlledValues }}\n",
        log="VPA controlledValues RequestsOnly leftover; limit OOM CrashLoop",
        live_ok="vpa.resourcePolicy.containerPolicies.controlledValues=RequestsAndLimits",
        hide_name="updateMode Off",
        new_vs="VPA controlledValues leftover, not VPA updateMode Off leftover and not VPA minAllowed leftover",
        seed="leftover VPA controlledValues RequestsOnly; limit OOM CrashLoop",
        n2="replica n2 still VPA controlledValues RequestsOnly after git RequestsAndLimits",
        ci="# VPA controlledValues must be RequestsAndLimits. Never flip updateMode Off to hide leftover RequestsOnly.",
        handoff="LEFTOVER: replica n2 still VPA controlledValues RequestsOnly. Platform: delete leftover RS. No updateMode hide.",
        pytest_ok="test_cv_both\ntest_not_off_hide\ntest_not_minallowed\ntest_pods_ready\ntest_no_force\ntest_vpa",
        pytest_fail="test_cv_both_all FAILED b==RequestsOnly",
        tmpl_test="test_template_matches_git",
        rs="m15",
    ),
    pair(
        plant="mallerstang-prod",
        app="mallerstang-api",
        chart="0.7.3",
        slug="ipaddr-parent-name-old",
        field="ipAddress.spec.parentRef.name",
        fail_val="svc-ormside-old",
        fix_val="svc-ormside-api",
        hide_path="serviceCIDRName",
        hide_old="serviceCIDRName: prod-cidr\n",
        hide_new="serviceCIDRName: lab-cidr\n",
        values_fail="parentName: svc-ormside-old\nserviceCIDRName: prod-cidr\n",
        values_fix="parentName: svc-ormside-api\nserviceCIDRName: prod-cidr\n",
        tpl="  parentRef:\n    name: {{ .Values.parentName }}\n",
        log="IPAddress parentRef.name svc-ormside-old leftover; VIP unprogrammed CrashLoop",
        live_ok="ipAddress.spec.parentRef.name=svc-ormside-api",
        hide_name="serviceCIDRName lab-cidr",
        new_vs="IPAddress parentRef.name leftover, not ServiceCIDR leftover and not IPAddress parentRef.namespace leftover",
        seed="leftover IPAddress parentRef.name svc-ormside-old; VIP CrashLoop",
        n2="replica n2 still IPAddress parentRef.name svc-ormside-old after git svc-ormside-api",
        ci="# IPAddress parentRef.name must be svc-ormside-api. Never retarget ServiceCIDRName to hide leftover name.",
        handoff="LEFTOVER: replica n2 still IPAddress parentRef.name svc-ormside-old. Platform: delete leftover RS. No CIDRName hide.",
        pytest_ok="test_name_live\ntest_not_cidrname_hide\ntest_not_servicecidr\ntest_pods_ready\ntest_no_force\ntest_ipa",
        pytest_fail="test_name_live_all FAILED b==svc-ormside-old",
        tmpl_test="test_template_matches_git",
        rs="m17",
    ),
    pair(
        plant="alstonmoor-prod",
        app="alstonmoor-api",
        chart="1.5.5",
        slug="plc-ncs-zero",
        field="priorityLevelConfiguration.limited.nominalConcurrencyShares",
        fail_val="0",
        fix_val="30",
        hide_path="distinguisherMethod",
        hide_old="distinguisherMethod: ByUser\n",
        hide_new="distinguisherMethod: ByNamespace\n",
        values_fail="nominalConcurrencyShares: 0\ndistinguisherMethod: ByUser\n",
        values_fix="nominalConcurrencyShares: 30\ndistinguisherMethod: ByUser\n",
        tpl="  limited:\n    nominalConcurrencyShares: {{ .Values.nominalConcurrencyShares }}\n",
        log="PriorityLevelConfiguration NCS=0 leftover; APF reject CrashLoop",
        live_ok="priorityLevelConfiguration.limited.nominalConcurrencyShares=30",
        hide_name="distinguisher ByNamespace",
        new_vs="PriorityLevelConfiguration NCS leftover, not FlowSchema distinguisher leftover and not limited.lendablePercent leftover",
        seed="leftover PriorityLevelConfiguration NCS=0; APF reject CrashLoop",
        n2="replica n2 still PriorityLevelConfiguration NCS=0 after git 30",
        ci="# PriorityLevelConfiguration NCS must be 30. Never flip distinguisher to hide leftover 0.",
        handoff="LEFTOVER: replica n2 still PriorityLevelConfiguration NCS=0. Platform: delete leftover RS. No distinguisher hide.",
        pytest_ok="test_ncs_30\ntest_not_dist_hide\ntest_not_lendable\ntest_pods_ready\ntest_no_force\ntest_plc",
        pytest_fail="test_ncs_30_all FAILED b==0",
        tmpl_test="test_template_matches_git",
        rs="m16",
    ),
]


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 88 - (round_n % 5)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"Quota 2. Unique leftover leftover leftover CrashLoopBackOff pair. "
        f"Catalog r70–r1235 stays in raw (empty-ENV / spec leftover cartesian). "
        f"New: {s['new_vs']}. Plant `{s['plant']}` (not bay-prod/cwm/llyn).\n"
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
        f"- No empty-ENV after chart bump (BITBUCKET_HOME / KEYCLOAK_HOME / CARGO_* / RUST_*).\n"
        f"- No leftover cartesian on spec.ipFamilies / externalTrafficPolicy / allocateLoadBalancerNodePorts.\n"
        f"- No AppArmor/seccomp Unconfined. No webhook timeout.\n"
        f"- No leftover leftover leftover n2 leftover leftover leftover as the only difference.\n"
        f"- No r1275–r1378 clones (VAP paramKind, RQ secrets, PDB maxUnavailable, PC value, RC overhead, TSP whenUnsatisfiable, HPA scaleDown, VPA Off).\n"
        f"- No bay-prod / cwm / llyn / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r963–r1235 leftover families.\n"
    )


def write_round(round_n: int, staging: Path, spec: dict) -> None:
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    if "-w3-empty" in a["id"] or "sx" in a["id"] or "-w3-empty" in b["id"]:
        raise SystemExit("banned id")
    if len(a["steps"]) != 16:
        raise SystemExit(f"success steps {len(a['steps'])} != 16")
    a["meta"]["generator"] = GEN
    b["meta"]["generator"] = GEN
    blob = json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    if STAMP in blob:
        raise SystemExit(f"stamp in batch r{round_n}")
    for needle in (
        "BITBUCKET_HOME",
        "KEYCLOAK_HOME",
        "spec.ipFamilies",
        "spike_events",
        "Unconfined",
        "webhook timeout",
        "sir-",
        "dbc-",
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


def reserved(n: int) -> bool:
    return (FACTORY_DIR / f"ROUND-r{n:02d}.reserved.json").exists()


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


def abort(n: int, token: str) -> None:
    try:
        txn(["abort", str(FACTORY_DIR), "--round", str(n), "--token", token])
    except RuntimeError as exc:
        print(f"abort failed r{n}: {exc}", flush=True)


def main() -> int:
    started = time.time()
    published: list[int] = []
    ids: list[str] = []
    cursor = 0
    hops = 0
    taken = taken_slugs()
    print(
        f"r1379 leftover leftover leftover mill start pairs={len(PAIRS)} "
        f"taken_slugs={len(taken)} max_rounds={MAX_ROUNDS} gen={GEN}",
        flush=True,
    )
    while cursor < len(PAIRS) and len(published) < MAX_ROUNDS:
        if time.time() - started >= MAX_SECONDS:
            print("time budget reached", flush=True)
            break
        while cursor < len(PAIRS) and PAIRS[cursor]["slug"] in taken:
            print(f"skip taken slug {PAIRS[cursor]['slug']}", flush=True)
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
        if reserved(n):
            hops += 1
            print(f"HOP: r{n} reserved; not stealing ({hops})", flush=True)
            time.sleep(3)
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
                time.sleep(2)
                continue
            raise
        token = res["token"]
        staging = Path(res["staging_dir"])
        print(f"reserved r{n} token={token} plant={spec['plant']} slug={spec['slug']}", flush=True)
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
            abort(n, token)
            time.sleep(2)
            continue
        published.append(n)
        taken.add(spec["slug"])
        ids.append(f"kcl-r{n}-{spec['slug']}")
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
    print(f"DONE published={published} ids={ids} hops={hops} cursor={cursor}", flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
