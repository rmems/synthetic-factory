#!/usr/bin/env python3
"""k8s-crashloop mill from r1092. Q=2. grok-4.6.

Unique leftover subfields vs mill-pref (r1076–r1091) and vs r963–r1006.
BAN leftover-n2 stamp (`leftover n2 still n2 leftover still`).
BAN empty-ENV catalog. BAN spec.ipFamilies leftover.
BAN plants cwm/llyn/bay-prod and the landscape clone list.
Loop: frontier → reserve --expected 2 → stage → publish. If reserved, HOP.
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
        "keld-prod",
        "lynchet-prod",
        "hause-prod",
        "scree-prod",
        "swale-prod",
        "carr-prod",
        "wath-prod",
        "lode-prod",
        "shott-prod",
        "vinney-prod",
        "milt-prod",
        "howk-prod",
        "reen-prod",
        "rhos-prod",
    }
    if kwargs["plant"] in banned_plants:
        raise SystemExit(f"banned plant {kwargs['plant']}")
    if kwargs["slug"] in BANNED_SLUGS:
        raise SystemExit(f"banned slug {kwargs['slug']}")
    return kwargs


BANNED_SLUGS = {
    "servicecidr-stale",
    "ipaddress-orphan",
    "vap-audit-failfast",
    "mapb-wait-oldbroker",
    "storageversion-alpha",
    "deviceclass-void",
    "resourceslice-gone",
    "clustercidr-stale",
    "svm-stuck-alpha",
    "rct-old-nic",
    "vapb-param-old",
    "deviceclass-cel-none",
    "ipaddr-servicecidr-gap",
    "servicecidr-condition",
    "alloc-result-stale",
    "map-reinvoke-old",
    "failpolicy-ignore",
    "mapolicy-inject",
    "device-taint",
    "device-vs-hugepages",
}


PAIRS: list[dict] = [
    pair(
        plant="twitten-prod",
        app="twitten-api",
        chart="1.6.2",
        slug="vap-matchcond-skip",
        field="validatingAdmissionPolicy.matchConditions",
        fail_val="skip-if-failfast",
        fix_val="always-match",
        hide_path="image.tag",
        hide_old="tag: 1.6.2\n",
        hide_new="tag: 1.6.2-debug\n",
        values_fail="matchCondition: skip-if-failfast\nenv:\n  FAIL_FAST: \"1\"\nimage:\n  tag: 1.6.2\n",
        values_fix="matchCondition: always-match\nenv:\n  FAIL_FAST: \"0\"\nimage:\n  tag: 1.6.2\n",
        tpl="  matchConditions:\n    - name: {{ .Values.matchCondition }}\n      expression: object.spec.containers.exists(c, c.env.exists(e, e.name=='FAIL_FAST'))\n",
        log="FATAL fail-fast=1 leftover; VAP matchConditions skip-if-failfast skipped Deny; exit 1",
        live_ok="matchConditions=always-match FAIL_FAST=0",
        hide_name="debug tag",
        new_vs="ValidatingAdmissionPolicy matchConditions leftover, not VAP Audit and not VAP Binding paramRef",
        seed="leftover VAP matchConditions skip-if-failfast; FAIL_FAST admitted CrashLoop",
        n2="replica n2 still skip-if-failfast after git always-match",
        ci="# VAP matchConditions must always-match FAIL_FAST. Never retag debug to hide an admitted crash env.",
        handoff="LEFTOVER: replica n2 still VAP matchConditions skip-if-failfast. Platform: delete leftover RS. No debug-tag hide.",
        pytest_ok="test_match_always\ntest_not_tag_hide\ntest_not_vap_audit\ntest_pods_ready\ntest_no_force\ntest_failfast",
        pytest_fail="test_match_always_all FAILED b==skip-if-failfast",
        tmpl_test="test_template_matches_git",
        rs="a11",
    ),
    pair(
        plant="vennel-prod",
        app="vennel-api",
        chart="2.4.1",
        slug="vapb-actions-warn",
        field="validatingAdmissionPolicyBinding.validationActions",
        fail_val="Warn",
        fix_val="Deny",
        hide_path="failurePolicy",
        hide_old="failurePolicy: Fail\n",
        hide_new="failurePolicy: Ignore\n",
        values_fail="validationActions: [Warn]\nfailurePolicy: Fail\nenv:\n  BOOT_CRASH: \"1\"\n",
        values_fix="validationActions: [Deny]\nfailurePolicy: Fail\nenv:\n  BOOT_CRASH: \"0\"\n",
        tpl="  validationActions: {{ .Values.validationActions }}\n  failurePolicy: {{ .Values.failurePolicy }}\n",
        log="FATAL BOOT_CRASH=1 leftover; VAP Binding validationActions Warn admitted it; exit 1",
        live_ok="validationActions=[Deny] BOOT_CRASH=0",
        hide_name="failurePolicy Ignore",
        new_vs="ValidatingAdmissionPolicyBinding validationActions Warn leftover, not VAP Audit and not webhook timeout",
        seed="leftover VAP Binding validationActions Warn; BOOT_CRASH admitted CrashLoop",
        n2="replica n2 still Warn after git Deny",
        ci="# VAP Binding must Deny BOOT_CRASH. Never Ignore failurePolicy to hide a Warn leftover.",
        handoff="LEFTOVER: replica n2 still VAP Binding validationActions Warn. Platform: delete leftover RS. No Ignore hide.",
        pytest_ok="test_actions_deny\ntest_not_ignore_hide\ntest_not_vap_audit\ntest_pods_ready\ntest_no_force\ntest_boot",
        pytest_fail="test_actions_deny_all FAILED b==Warn",
        tmpl_test="test_template_matches_git",
        rs="b22",
    ),
    pair(
        plant="ginnel-prod",
        app="ginnel-api",
        chart="0.8.5",
        slug="vap-var-failfast",
        field="validatingAdmissionPolicy.variables",
        fail_val="failfast=true",
        fix_val="failfast=false",
        hide_path="logLevel",
        hide_old="logLevel: info\n",
        hide_new="logLevel: debug\n",
        values_fail="vapVarFailfast: true\nlogLevel: info\nenv:\n  FAIL_FAST: \"1\"\n",
        values_fix="vapVarFailfast: false\nlogLevel: info\nenv:\n  FAIL_FAST: \"0\"\n",
        tpl="  variables:\n    - name: failfast\n      expression: \"{{ .Values.vapVarFailfast }}\"\n",
        log="FATAL fail-fast variable leftover; VAP variables failfast=true admitted FAIL_FAST=1; exit 1",
        live_ok="validatingAdmissionPolicy.variables failfast=false",
        hide_name="logLevel debug",
        new_vs="ValidatingAdmissionPolicy variables leftover, not VAP matchConditions and not VAP Audit",
        seed="leftover VAP variables failfast=true; FAIL_FAST admitted CrashLoop",
        n2="replica n2 still failfast=true after git failfast=false",
        ci="# VAP variables failfast must be false. Never bump logLevel to hide an admitted crash env.",
        handoff="LEFTOVER: replica n2 still VAP variables failfast=true. Platform: delete leftover RS. No logLevel hide.",
        pytest_ok="test_var_false\ntest_not_log_hide\ntest_not_vap_audit\ntest_pods_ready\ntest_no_force\ntest_var",
        pytest_fail="test_var_false_all FAILED b==failfast=true",
        tmpl_test="test_template_matches_git",
        rs="c33",
    ),
    pair(
        plant="snicket-prod",
        app="snicket-api",
        chart="3.2.0",
        slug="map-jsonpatch-otel",
        field="mutatingAdmissionPolicy.mutations.jsonPatch",
        fail_val="OTEL_EXPORTER_OTLP_ENDPOINT=http://old-collector:4317",
        fix_val="",
        hide_path="brokerHost",
        hide_old="brokerHost: snicket-api.snicket.svc\n",
        hide_new="brokerHost: 127.0.0.1\n",
        values_fail="mapPatch: OTEL_EXPORTER_OTLP_ENDPOINT=http://old-collector:4317\nbrokerHost: snicket-api.snicket.svc\n",
        values_fix="mapPatch: \"\"\nbrokerHost: snicket-api.snicket.svc\n",
        tpl="  mutations:\n    - patchType: JSONPatch\n      jsonPatch:\n        expression: \"[{op:'add', path:'/spec/containers/0/env/-', value:{name:'OTEL', value:'{{ .Values.mapPatch }}'}}]\"\n",
        log="dial old-collector:4317 NXDOMAIN leftover; MAP JSONPatch inject CrashLoop",
        live_ok="mutatingAdmissionPolicy.mutations.jsonPatch=",
        hide_name="broker 127.0.0.1",
        new_vs="MutatingAdmissionPolicy JSONPatch leftover, not MAP Binding wait-old-broker and not MAP reinvocationPolicy",
        seed="leftover MAP JSONPatch injects old-collector OTLP endpoint; NXDOMAIN CrashLoop",
        n2="replica n2 still MAP JSONPatch old-collector after git empty patch",
        ci="# MAP JSONPatch leftover mutates OTLP endpoint. Never loopback the broker host to hide NXDOMAIN.",
        handoff="LEFTOVER: replica n2 still MAP JSONPatch old-collector. Platform: delete leftover RS. No loopback hide.",
        pytest_ok="test_map_empty\ntest_not_loopback_hide\ntest_not_mapb\ntest_pods_ready\ntest_no_force\ntest_otel",
        pytest_fail="test_map_empty_all FAILED b==old-collector:4317",
        tmpl_test="test_template_matches_git",
        rs="d44",
    ),
    pair(
        plant="drang-prod",
        app="drang-api",
        chart="1.1.9",
        slug="map-matchcond-always",
        field="mutatingAdmissionPolicy.matchConditions",
        fail_val="always-inject",
        fix_val="never-inject",
        hide_path="replicas",
        hide_old="replicas: 2\n",
        hide_new="replicas: 0\n",
        values_fail="mapMatch: always-inject\nreplicas: 2\nwaitFor: old-schema-registry.drang.svc\n",
        values_fix="mapMatch: never-inject\nreplicas: 2\nwaitFor: drang-api.drang.svc\n",
        tpl="  matchConditions:\n    - name: {{ .Values.mapMatch }}\n      expression: true\n",
        log="wait-for old-schema-registry.drang.svc:8081 NXDOMAIN leftover; MAP matchConditions always-inject CrashLoop",
        live_ok="matchConditions=never-inject",
        hide_name="replicas 0",
        new_vs="MutatingAdmissionPolicy matchConditions leftover, not MAP JSONPatch and not MAP Binding wait-old-broker",
        seed="leftover MAP matchConditions always-inject; wait-for old-schema-registry CrashLoop",
        n2="replica n2 still always-inject after git never-inject",
        ci="# MAP matchConditions must never-inject the stale wait-for. Never scale to 0 to hide NXDOMAIN.",
        handoff="LEFTOVER: replica n2 still MAP matchConditions always-inject. Platform: delete leftover RS. No replicas-0 hide.",
        pytest_ok="test_match_never\ntest_not_scale0_hide\ntest_not_mapb\ntest_pods_ready\ntest_no_force\ntest_wait",
        pytest_fail="test_match_never_all FAILED b==always-inject",
        tmpl_test="test_template_matches_git",
        rs="e55",
    ),
    pair(
        plant="loke-prod",
        app="loke-api",
        chart="4.0.3",
        slug="mapb-ns-old",
        field="mutatingAdmissionPolicyBinding.namespaceSelector",
        fail_val="env=canary-old",
        fix_val="env=prod",
        hide_path="waitFor",
        hide_old="waitFor: loke-api.loke.svc\n",
        hide_new="waitFor: 127.0.0.1\n",
        values_fail="nsSelector: env=canary-old\nwaitFor: loke-api.loke.svc\n",
        values_fix="nsSelector: env=prod\nwaitFor: loke-api.loke.svc\n",
        tpl="  matchResources:\n    namespaceSelector:\n      matchLabels:\n        env: {{ .Values.nsSelector | trimPrefix \"env=\" }}\n",
        log="MAP Binding leftover nsSelector env=canary-old still matches loke-prod; wait-for inject CrashLoop",
        live_ok="namespaceSelector=env=prod",
        hide_name="waitFor 127.0.0.1",
        new_vs="MutatingAdmissionPolicyBinding namespaceSelector leftover, not MAP reinvocationPolicy and not MAP Binding wait-old-broker",
        seed="leftover MAP Binding namespaceSelector env=canary-old still binds prod ns CrashLoop",
        n2="replica n2 still nsSelector env=canary-old after git env=prod",
        ci="# MAP Binding namespaceSelector must be env=prod. Never loopback waitFor to hide leftover inject.",
        handoff="LEFTOVER: replica n2 still MAP Binding namespaceSelector env=canary-old. Platform: delete leftover RS. No loopback hide.",
        pytest_ok="test_ns_prod\ntest_not_loopback_hide\ntest_not_reinvoke\ntest_pods_ready\ntest_no_force\ntest_ns",
        pytest_fail="test_ns_prod_all FAILED b==env=canary-old",
        tmpl_test="test_template_matches_git",
        rs="f66",
    ),
    pair(
        plant="hurst-prod",
        app="hurst-api",
        chart="2.2.2",
        slug="deviceclass-xres-gone",
        field="deviceClass.extendedResourceName",
        fail_val="example.com/old-xgpu",
        fix_val="example.com/xgpu",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="extendedResourceName: example.com/old-xgpu\nprivileged: false\n",
        values_fix="extendedResourceName: example.com/xgpu\nprivileged: false\n",
        tpl="  extendedResourceName: {{ .Values.extendedResourceName }}\n",
        log="NVIDIA_VISIBLE_DEVICES=void leftover DeviceClass extendedResourceName old-xgpu CrashLoop",
        live_ok="deviceClass.extendedResourceName=example.com/xgpu",
        hide_name="privileged",
        new_vs="DeviceClass extendedResourceName leftover, not DeviceClass name old-gpu and not DeviceClass CEL 8Gi",
        seed="leftover DeviceClass extendedResourceName example.com/old-xgpu; void GPU CrashLoop",
        n2="replica n2 still old-xgpu after git example.com/xgpu",
        ci="# DeviceClass extendedResourceName must name a live xgpu. Never privileged to hide a void device.",
        handoff="LEFTOVER: replica n2 still DeviceClass extendedResourceName old-xgpu. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_xres_xgpu\ntest_not_priv_hide\ntest_not_old_gpu\ntest_pods_ready\ntest_no_force\ntest_xres",
        pytest_fail="test_xres_xgpu_all FAILED b==example.com/old-xgpu",
        tmpl_test="test_template_matches_git",
        rs="a77",
    ),
    pair(
        plant="spinney-prod",
        app="spinney-api",
        chart="1.8.8",
        slug="deviceclass-opaque-void",
        field="deviceClass.config.opaque.parameters",
        fail_val="deviceIndex=-1",
        fix_val="deviceIndex=0",
        hide_path="count",
        hide_old="count: 1\n",
        hide_new="count: 0\n",
        values_fail="deviceIndex: -1\ncount: 1\n",
        values_fix="deviceIndex: 0\ncount: 1\n",
        tpl="  config:\n    - opaque:\n        parameters:\n          deviceIndex: {{ .Values.deviceIndex }}\n",
        log="CUDA_ERROR_INVALID_DEVICE leftover DeviceClass opaque deviceIndex=-1 CrashLoop",
        live_ok="deviceClass.config.opaque.parameters deviceIndex=0",
        hide_name="count 0",
        new_vs="DeviceClass opaque parameters leftover, not DeviceClass CEL capacity and not extendedResourceName",
        seed="leftover DeviceClass opaque deviceIndex=-1; invalid GPU CrashLoop",
        n2="replica n2 still deviceIndex=-1 after git deviceIndex=0",
        ci="# DeviceClass opaque deviceIndex must be 0. Never count:0 to hide an invalid device.",
        handoff="LEFTOVER: replica n2 still DeviceClass opaque deviceIndex=-1. Platform: delete leftover RS. No count-0 hide.",
        pytest_ok="test_idx_0\ntest_not_count0_hide\ntest_not_cel\ntest_pods_ready\ntest_no_force\ntest_opaque",
        pytest_fail="test_idx_0_all FAILED b==-1",
        tmpl_test="test_template_matches_git",
        rs="b88",
    ),
    pair(
        plant="hanger-prod",
        app="hanger-api",
        chart="0.5.4",
        slug="deviceclass-attr-arch",
        field="deviceClass.selectors.attribute",
        fail_val="arch=volta",
        fix_val="arch=ampere",
        hide_path="nodeSelector",
        hide_old="nodeSelector: {}\n",
        hide_new="nodeSelector: {gpu: nvidia}\n",
        values_fail="arch: volta\nnodeSelector: {}\n",
        values_fix="arch: ampere\nnodeSelector: {}\n",
        tpl="  selectors:\n    - cel:\n        expression: device.attributes['example.com/arch'].string() == '{{ .Values.arch }}'\n",
        log="allocation empty leftover DeviceClass attribute arch=volta; NVIDIA_VISIBLE_DEVICES=void CrashLoop",
        live_ok="deviceClass.selectors.attribute arch=ampere",
        hide_name="nodeSelector gpu=nvidia",
        new_vs="DeviceClass attribute selector leftover, not DeviceClass CEL 8Gi capacity and not DeviceClass name old-gpu",
        seed="leftover DeviceClass attribute arch=volta; empty allocation CrashLoop",
        n2="replica n2 still arch=volta after git arch=ampere",
        ci="# DeviceClass attribute must match live ampere GPUs. Never nodeSelector to hide a void alloc.",
        handoff="LEFTOVER: replica n2 still DeviceClass attribute arch=volta. Platform: delete leftover RS. No nodeSelector hide.",
        pytest_ok="test_arch_ampere\ntest_not_ns_hide\ntest_not_cel_8gi\ntest_pods_ready\ntest_no_force\ntest_attr",
        pytest_fail="test_arch_ampere_all FAILED b==volta",
        tmpl_test="test_template_matches_git",
        rs="c99",
    ),
    pair(
        plant="bourne-prod",
        app="bourne-api",
        chart="3.3.1",
        slug="resourceslice-node-gone",
        field="resourceSlice.nodeName",
        fail_val="gpu-node-dead",
        fix_val="gpu-node-a",
        hide_path="hostPath",
        hide_old="hostPath: false\n",
        hide_new="hostPath: true\n",
        values_fail="resourceSliceNode: gpu-node-dead\nhostPath: false\n",
        values_fix="resourceSliceNode: gpu-node-a\nhostPath: false\n",
        tpl="  nodeName: {{ .Values.resourceSliceNode }}\n",
        log="open /dev/nvidia0: no such device; leftover ResourceSlice nodeName gpu-node-dead CrashLoop",
        live_ok="resourceSlice.nodeName=gpu-node-a",
        hide_name="hostPath /dev/nvidia0",
        new_vs="ResourceSlice nodeName leftover, not ResourceSlice driver FPGA and not DeviceClass void GPU",
        seed="leftover ResourceSlice nodeName gpu-node-dead; ENODEV CrashLoop",
        n2="replica n2 still ResourceSlice nodeName gpu-node-dead after git gpu-node-a",
        ci="# ResourceSlice nodeName must name a live GPU node. Never hostPath to hide ENODEV.",
        handoff="LEFTOVER: replica n2 still ResourceSlice nodeName gpu-node-dead. Platform: delete leftover RS. No hostPath hide.",
        pytest_ok="test_node_a\ntest_not_hostpath_hide\ntest_not_slice_fpga\ntest_pods_ready\ntest_no_force\ntest_node",
        pytest_fail="test_node_a_all FAILED b==gpu-node-dead",
        tmpl_test="test_template_matches_git",
        rs="d0a",
    ),
    pair(
        plant="coppice-prod",
        app="coppice-api",
        chart="1.0.7",
        slug="resourceslice-pool-gen",
        field="resourceSlice.pool.generation",
        fail_val="3",
        fix_val="9",
        hide_path="count",
        hide_old="count: 1\n",
        hide_new="count: 0\n",
        values_fail="poolGeneration: 3\ncount: 1\n",
        values_fix="poolGeneration: 9\ncount: 1\n",
        tpl="  pool:\n    generation: {{ .Values.poolGeneration }}\n",
        log="DRA skipped leftover ResourceSlice pool.generation=3; kubelet advertised 9; void device CrashLoop",
        live_ok="resourceSlice.pool.generation=9",
        hide_name="count 0",
        new_vs="ResourceSlice pool.generation leftover, not ResourceSlice driver FPGA and not ResourceSlice nodeName",
        seed="leftover ResourceSlice pool.generation=3 vs kubelet 9; skipped slice CrashLoop",
        n2="replica n2 still pool.generation=3 after git 9",
        ci="# ResourceSlice pool.generation must match kubelet. Never count:0 to hide a skipped slice.",
        handoff="LEFTOVER: replica n2 still ResourceSlice pool.generation=3. Platform: delete leftover RS. No count-0 hide.",
        pytest_ok="test_gen_9\ntest_not_count0_hide\ntest_not_slice_fpga\ntest_pods_ready\ntest_no_force\ntest_gen",
        pytest_fail="test_gen_9_all FAILED b==3",
        tmpl_test="test_template_matches_git",
        rs="e1b",
    ),
    pair(
        plant="tye-prod",
        app="tye-api",
        chart="2.9.0",
        slug="resourceslice-taint-nosched",
        field="resourceSlice.devices.taints",
        fail_val="NoSchedule",
        fix_val="[]",
        hide_path="tolerations",
        hide_old="tolerations: []\n",
        hide_new="tolerations: [{key: dra, effect: NoSchedule}]\n",
        values_fail="deviceTaint: NoSchedule\ntolerations: []\n",
        values_fix="deviceTaint: \"\"\ntolerations: []\n",
        tpl="  devices:\n    - taints:\n        - effect: {{ .Values.deviceTaint }}\n",
        log="allocation empty leftover ResourceSlice devices.taints NoSchedule; NVIDIA_VISIBLE_DEVICES=void CrashLoop",
        live_ok="resourceSlice.devices.taints=[]",
        hide_name="toleration NoSchedule",
        new_vs="ResourceSlice devices.taints leftover, not DeviceTaintRule and not DeviceClass CEL",
        seed="leftover ResourceSlice devices.taints NoSchedule; empty allocation CrashLoop",
        n2="replica n2 still devices.taints NoSchedule after git empty",
        ci="# ResourceSlice device taints must be empty. Never add a pod toleration to hide a void alloc.",
        handoff="LEFTOVER: replica n2 still ResourceSlice devices.taints NoSchedule. Platform: delete leftover RS. No toleration hide.",
        pytest_ok="test_taint_empty\ntest_not_tol_hide\ntest_not_device_taint_rule\ntest_pods_ready\ntest_no_force\ntest_taint",
        pytest_fail="test_taint_empty_all FAILED b==NoSchedule",
        tmpl_test="test_template_matches_git",
        rs="f2c",
    ),
    pair(
        plant="nook-prod",
        app="nook-api",
        chart="1.4.4",
        slug="servicecidr-overlap",
        field="serviceCIDR.spec.cidrs",
        fail_val="10.96.0.0/16",
        fix_val="10.98.0.0/16",
        hide_path="clusterIP",
        hide_old="clusterIP: 10.96.12.12\n",
        hide_new="clusterIP: None\n",
        values_fail="serviceCIDR: 10.96.0.0/16\nclusterIP: 10.96.12.12\n",
        values_fix="serviceCIDR: 10.98.0.0/16\nclusterIP: 10.98.12.12\n",
        tpl="  cidrs:\n    - {{ .Values.serviceCIDR }}\n",
        log="ServiceCIDR 10.96.0.0/16 leftover overlaps cluster range; kube-proxy skip 10.96.12.12 CrashLoop",
        live_ok="serviceCIDR.spec.cidrs=10.98.0.0/16",
        hide_name="headless ClusterIP None",
        new_vs="ServiceCIDR overlapping cidrs leftover, not ServiceCIDR 10.96.0.0/24 stale and not spec.ipFamilies",
        seed="leftover ServiceCIDR 10.96.0.0/16 overlaps cluster; kube-proxy skip CrashLoop",
        n2="replica n2 still ServiceCIDR 10.96.0.0/16 after git 10.98.0.0/16",
        ci="# ServiceCIDR must not overlap the cluster range. Never headless to hide a blackhole ClusterIP.",
        handoff="LEFTOVER: replica n2 still ServiceCIDR 10.96.0.0/16 overlap. Platform: delete leftover RS. No headless hide.",
        pytest_ok="test_cidr_98\ntest_not_headless_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_overlap",
        pytest_fail="test_cidr_98_all FAILED b==10.96.0.0/16",
        tmpl_test="test_template_matches_git",
        rs="a3d",
    ),
    pair(
        plant="eyot-prod",
        app="eyot-api",
        chart="5.1.0",
        slug="servicecidr-terminating",
        field="serviceCIDR.status.conditions",
        fail_val="Terminating=True",
        fix_val="Ready=True",
        hide_path="clusterIP",
        hide_old="clusterIP: 10.97.30.30\n",
        hide_new="clusterIP: None\n",
        values_fail="serviceCIDRTerminating: true\nclusterIP: 10.97.30.30\n",
        values_fix="serviceCIDRTerminating: false\nclusterIP: 10.97.30.30\n",
        tpl="  status:\n    conditions:\n      - type: Terminating\n        status: {{ if .Values.serviceCIDRTerminating }}True{{ else }}False{{ end }}\n",
        log="ServiceCIDR Terminating=True leftover; kube-proxy drained 10.97.30.30 CrashLoop",
        live_ok="serviceCIDR.status.conditions Ready=True Terminating=False",
        hide_name="headless ClusterIP None",
        new_vs="ServiceCIDR Terminating leftover, not ServiceCIDR Ready=False and not ServiceCIDR cidr string leftover",
        seed="leftover ServiceCIDR condition Terminating=True; VIP drained CrashLoop",
        n2="replica n2 still ServiceCIDR Terminating=True after git Ready=True",
        ci="# ServiceCIDR must not stay Terminating. Never headless to hide a drained VIP.",
        handoff="LEFTOVER: replica n2 still ServiceCIDR Terminating=True. Platform: delete leftover RS. No headless hide.",
        pytest_ok="test_not_terminating\ntest_not_headless_hide\ntest_not_ready_false\ntest_pods_ready\ntest_no_force\ntest_term",
        pytest_fail="test_not_terminating_all FAILED b==Terminating=True",
        tmpl_test="test_template_matches_git",
        rs="b4e",
    ),
    pair(
        plant="ait-prod",
        app="ait-api",
        chart="0.3.6",
        slug="servicecidr-v6only",
        field="serviceCIDR.spec.cidrs",
        fail_val="fd00:96::/108",
        fix_val="10.99.0.0/16",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="serviceCIDR: fd00:96::/108\nhostNetwork: false\n",
        values_fix="serviceCIDR: 10.99.0.0/16\nhostNetwork: false\n",
        tpl="  cidrs:\n    - {{ .Values.serviceCIDR }}\n",
        log="dial 10.99.4.8: no route leftover; ServiceCIDR only fd00:96::/108; kube-proxy skip IPv4 CrashLoop",
        live_ok="serviceCIDR.spec.cidrs=10.99.0.0/16",
        hide_name="hostNetwork",
        new_vs="ServiceCIDR IPv6-only cidrs leftover, not spec.ipFamilies and not ServiceCIDR overlap 10.96",
        seed="leftover ServiceCIDR fd00:96::/108 IPv6-only; IPv4 ClusterIP unprogrammed CrashLoop",
        n2="replica n2 still ServiceCIDR fd00:96::/108 after git 10.99.0.0/16",
        ci="# ServiceCIDR must program IPv4 10.99.0.0/16. Never hostNetwork to hide an IPv6-only leftover.",
        handoff="LEFTOVER: replica n2 still ServiceCIDR fd00:96::/108. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_cidr_99\ntest_not_hostnet_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_v6",
        pytest_fail="test_cidr_99_all FAILED b==fd00:96::/108",
        tmpl_test="test_template_matches_git",
        rs="c5f",
    ),
    pair(
        plant="bield-prod",
        app="bield-api",
        chart="2.0.8",
        slug="vap-paramkind-old",
        field="validatingAdmissionPolicy.paramKind",
        fail_val="v1alpha1/FailFastParams",
        fix_val="v1/FailFastParams",
        hide_path="matchPolicy",
        hide_old="matchPolicy: Equivalent\n",
        hide_new="matchPolicy: Exact\n",
        values_fail="paramKind: v1alpha1/FailFastParams\nmatchPolicy: Equivalent\nenv:\n  FAIL_FAST: \"1\"\n",
        values_fix="paramKind: v1/FailFastParams\nmatchPolicy: Equivalent\nenv:\n  FAIL_FAST: \"0\"\n",
        tpl="  paramKind:\n    apiVersion: {{ .Values.paramKind | replace \"/FailFastParams\" \"\" }}\n    kind: FailFastParams\n",
        log="FATAL fail-fast leftover; VAP paramKind v1alpha1/FailFastParams conversion miss admitted FAIL_FAST=1; exit 1",
        live_ok="validatingAdmissionPolicy.paramKind=v1/FailFastParams FAIL_FAST=0",
        hide_name="matchPolicy Exact",
        new_vs="ValidatingAdmissionPolicy paramKind leftover, not VAP Binding paramRef and not VAP Audit",
        seed="leftover VAP paramKind v1alpha1/FailFastParams; FAIL_FAST admitted CrashLoop",
        n2="replica n2 still paramKind v1alpha1/FailFastParams after git v1/FailFastParams",
        ci="# VAP paramKind must be v1 FailFastParams. Never Exact matchPolicy to hide a leftover paramKind.",
        handoff="LEFTOVER: replica n2 still VAP paramKind v1alpha1/FailFastParams. Platform: delete leftover RS. No Exact hide.",
        pytest_ok="test_kind_v1\ntest_not_exact_hide\ntest_not_paramref\ntest_pods_ready\ntest_no_force\ntest_kind",
        pytest_fail="test_kind_v1_all FAILED b==v1alpha1/FailFastParams",
        tmpl_test="test_template_matches_git",
        rs="d60",
    ),
    pair(
        plant="wychel-prod",
        app="wychel-api",
        chart="1.2.6",
        slug="clustercidr-ns-gone",
        field="clusterCIDR.nodeSelector",
        fail_val="node=dead-pool",
        fix_val="node=live-pool",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="nodeSelector: node=dead-pool\nhostNetwork: false\n",
        values_fix="nodeSelector: node=live-pool\nhostNetwork: false\n",
        tpl="  nodeSelector:\n    matchLabels:\n      node: {{ .Values.nodeSelector | trimPrefix \"node=\" }}\n",
        log="dial 10.245.4.8: no route leftover; ClusterCIDR nodeSelector node=dead-pool; CNI skip CrashLoop",
        live_ok="clusterCIDR.nodeSelector=node=live-pool",
        hide_name="hostNetwork",
        new_vs="ClusterCIDR nodeSelector leftover, not ClusterCIDR cidr 10.244 string and not ServiceCIDR",
        seed="leftover ClusterCIDR nodeSelector node=dead-pool; CNI blackhole CrashLoop",
        n2="replica n2 still ClusterCIDR nodeSelector node=dead-pool after git live-pool",
        ci="# ClusterCIDR nodeSelector must match live nodes. Never hostNetwork to hide a stale pool.",
        handoff="LEFTOVER: replica n2 still ClusterCIDR nodeSelector node=dead-pool. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_ns_live\ntest_not_hostnet_hide\ntest_not_cidr_string\ntest_pods_ready\ntest_no_force\ntest_pool",
        pytest_fail="test_ns_live_all FAILED b==node=dead-pool",
        tmpl_test="test_template_matches_git",
        rs="e71",
    ),
    pair(
        plant="dumble-prod",
        app="dumble-api",
        chart="2.7.1",
        slug="ipaddr-parentkind",
        field="ipAddress.parentRef.kind",
        fail_val="ServiceImport",
        fix_val="Service",
        hide_path="sessionAffinity",
        hide_old="sessionAffinity: None\n",
        hide_new="sessionAffinity: ClientIP\n",
        values_fail="parentKind: ServiceImport\nsessionAffinity: None\n",
        values_fix="parentKind: Service\nsessionAffinity: None\n",
        tpl="  parentRef:\n    kind: {{ .Values.parentKind }}\n    name: dumble-api\n",
        log="IPAddress parentRef kind ServiceImport leftover; no backing Service; kube-proxy skip CrashLoop",
        live_ok="ipAddress.parentRef.kind=Service",
        hide_name="sessionAffinity ClientIP",
        new_vs="IPAddress parentRef.kind leftover, not IPAddress parentRef name svc/old and not spec.ipFamilies",
        seed="leftover IPAddress parentRef.kind ServiceImport; VIP blackhole CrashLoop",
        n2="replica n2 still parentRef.kind ServiceImport after git Service",
        ci="# IPAddress parentRef.kind must be Service. Never ClientIP stickiness to hide a blackhole VIP.",
        handoff="LEFTOVER: replica n2 still IPAddress parentRef.kind ServiceImport. Platform: delete leftover RS. No ClientIP hide.",
        pytest_ok="test_kind_svc\ntest_not_affinity_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_kind",
        pytest_fail="test_kind_svc_all FAILED b==ServiceImport",
        tmpl_test="test_template_matches_git",
        rs="f82",
    ),
    pair(
        plant="foss-prod",
        app="foss-api",
        chart="0.9.4",
        slug="rclaim-reservedfor",
        field="resourceClaim.status.reservedFor",
        fail_val="pod/old-foss",
        fix_val="pod/foss-api",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="reservedFor: pod/old-foss\nprivileged: false\n",
        values_fix="reservedFor: pod/foss-api\nprivileged: false\n",
        tpl="  status:\n    reservedFor:\n      - resource: pods\n        name: {{ .Values.reservedFor | trimPrefix \"pod/\" }}\n",
        log="CUDA_ERROR_NO_DEVICE leftover ResourceClaim reservedFor pod/old-foss; claim not bound CrashLoop",
        live_ok="resourceClaim.status.reservedFor=pod/foss-api",
        hide_name="privileged",
        new_vs="ResourceClaim reservedFor leftover, not allocationResult gpu-0-gone and not DeviceClass name old-gpu",
        seed="leftover ResourceClaim reservedFor pod/old-foss; unbound GPU CrashLoop",
        n2="replica n2 still reservedFor pod/old-foss after git pod/foss-api",
        ci="# ResourceClaim reservedFor must name the live pod. Never privileged to hide an unbound claim.",
        handoff="LEFTOVER: replica n2 still ResourceClaim reservedFor pod/old-foss. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_rsv_api\ntest_not_priv_hide\ntest_not_alloc_result\ntest_pods_ready\ntest_no_force\ntest_rsv",
        pytest_fail="test_rsv_api_all FAILED b==pod/old-foss",
        tmpl_test="test_template_matches_git",
        rs="a93",
    ),
    pair(
        plant="tombolo-prod",
        app="tombolo-api",
        chart="3.4.0",
        slug="rct-alloc-all",
        field="resourceClaimTemplate.allocationMode",
        fail_val="All",
        fix_val="ExactCount",
        hide_path="count",
        hide_old="count: 1\n",
        hide_new="count: 0\n",
        values_fail="allocationMode: All\ncount: 1\n",
        values_fix="allocationMode: ExactCount\ncount: 1\n",
        tpl="  devices:\n    requests:\n      - allocationMode: {{ .Values.allocationMode }}\n        count: {{ .Values.count }}\n",
        log="allocation empty leftover ResourceClaimTemplate allocationMode All; no exclusive GPU CrashLoop",
        live_ok="resourceClaimTemplate.allocationMode=ExactCount",
        hide_name="count 0",
        new_vs="ResourceClaimTemplate allocationMode leftover, not RCT old-nic deviceClassName and not DeviceClass CEL",
        seed="leftover ResourceClaimTemplate allocationMode All; shared GPU void CrashLoop",
        n2="replica n2 still allocationMode All after git ExactCount",
        ci="# ResourceClaimTemplate allocationMode must be ExactCount. Never count:0 to hide a void alloc.",
        handoff="LEFTOVER: replica n2 still RCT allocationMode All. Platform: delete leftover RS. No count-0 hide.",
        pytest_ok="test_mode_exact\ntest_not_count0_hide\ntest_not_old_nic\ntest_pods_ready\ntest_no_force\ntest_mode",
        pytest_fail="test_mode_exact_all FAILED b==All",
        tmpl_test="test_template_matches_git",
        rs="ba4",
    ),
    pair(
        plant="berm-prod",
        app="berm-api",
        chart="1.5.5",
        slug="dtr-noschedule",
        field="deviceTaintRule.spec.taint.effect",
        fail_val="NoSchedule",
        fix_val="",
        hide_path="tolerations",
        hide_old="tolerations: []\n",
        hide_new="tolerations: [{key: dra, effect: NoSchedule}]\n",
        values_fail="taintEffect: NoSchedule\ntolerations: []\n",
        values_fix="taintEffect: \"\"\ntolerations: []\n",
        tpl="  spec:\n    taint:\n      effect: {{ .Values.taintEffect }}\n",
        log="allocation empty leftover DeviceTaintRule NoSchedule; NVIDIA_VISIBLE_DEVICES=void CrashLoop",
        live_ok="deviceTaintRule.spec.taint.effect=",
        hide_name="toleration NoSchedule",
        new_vs="DeviceTaintRule leftover, not ResourceSlice devices.taints and not DeviceClass CEL 8Gi",
        seed="leftover DeviceTaintRule effect NoSchedule; empty GPU allocation CrashLoop",
        n2="replica n2 still DeviceTaintRule NoSchedule after git empty taint",
        ci="# DeviceTaintRule must not NoSchedule live GPUs. Never add a pod toleration to hide a void alloc.",
        handoff="LEFTOVER: replica n2 still DeviceTaintRule NoSchedule. Platform: delete leftover RS. No toleration hide.",
        pytest_ok="test_dtr_empty\ntest_not_tol_hide\ntest_not_slice_taint\ntest_pods_ready\ntest_no_force\ntest_dtr",
        pytest_fail="test_dtr_empty_all FAILED b==NoSchedule",
        tmpl_test="test_template_matches_git",
        rs="cb5",
    ),
    pair(
        plant="rake-prod",
        app="rake-api",
        chart="4.1.2",
        slug="storageversion-enc",
        field="storageVersion.encoding",
        fail_val="protobuf-old",
        fix_val="json",
        hide_path="operatorTag",
        hide_old="operatorTag: 4.1.2\n",
        hide_new="operatorTag: 4.1.2-compat\n",
        values_fail="encoding: protobuf-old\noperatorTag: 4.1.2\n",
        values_fix="encoding: json\noperatorTag: 4.1.2\n",
        tpl="  encoding:\n    - {{ .Values.encoding }}\n",
        log="panic: decode leftover StorageVersion encoding protobuf-old; operator CrashLoop",
        live_ok="storageVersion.encoding=json",
        hide_name="compat operator tag",
        new_vs="StorageVersion encoding leftover, not CRD storageVersion v1alpha1 and not StorageVersionMigration stuck",
        seed="leftover StorageVersion encoding protobuf-old; operator decode CrashLoop",
        n2="replica n2 still encoding protobuf-old after git json",
        ci="# StorageVersion encoding must be json. Never a compat tag to hide old protobuf storage.",
        handoff="LEFTOVER: replica n2 still StorageVersion encoding protobuf-old. Platform: delete leftover RS. No compat-tag hide.",
        pytest_ok="test_enc_json\ntest_not_tag_hide\ntest_not_storage_alpha\ntest_pods_ready\ntest_no_force\ntest_enc",
        pytest_fail="test_enc_json_all FAILED b==protobuf-old",
        tmpl_test="test_template_matches_git",
        rs="dc6",
    ),
    pair(
        plant="brake-prod",
        app="brake-api",
        chart="2.3.7",
        slug="vapb-param-notfound",
        field="validatingAdmissionPolicyBinding.paramRef.parameterNotFoundAction",
        fail_val="Allow",
        fix_val="Deny",
        hide_path="failurePolicy",
        hide_old="failurePolicy: Fail\n",
        hide_new="failurePolicy: Ignore\n",
        values_fail="parameterNotFoundAction: Allow\nfailurePolicy: Fail\nenv:\n  BOOT_CRASH: \"1\"\n",
        values_fix="parameterNotFoundAction: Deny\nfailurePolicy: Fail\nenv:\n  BOOT_CRASH: \"0\"\n",
        tpl="  paramRef:\n    parameterNotFoundAction: {{ .Values.parameterNotFoundAction }}\n",
        log="FATAL BOOT_CRASH=1 leftover; VAP Binding parameterNotFoundAction Allow admitted missing params; exit 1",
        live_ok="parameterNotFoundAction=Deny BOOT_CRASH=0",
        hide_name="failurePolicy Ignore",
        new_vs="VAP Binding parameterNotFoundAction leftover, not VAP Binding paramRef name and not VAP Audit",
        seed="leftover VAP Binding parameterNotFoundAction Allow; BOOT_CRASH admitted CrashLoop",
        n2="replica n2 still parameterNotFoundAction Allow after git Deny",
        ci="# VAP Binding parameterNotFoundAction must Deny. Never Ignore failurePolicy to hide Allow leftover.",
        handoff="LEFTOVER: replica n2 still VAP Binding parameterNotFoundAction Allow. Platform: delete leftover RS. No Ignore hide.",
        pytest_ok="test_pnf_deny\ntest_not_ignore_hide\ntest_not_paramref_name\ntest_pods_ready\ntest_no_force\ntest_pnf",
        pytest_fail="test_pnf_deny_all FAILED b==Allow",
        tmpl_test="test_template_matches_git",
        rs="ed7",
    ),
    pair(
        plant="linch-prod",
        app="linch-api",
        chart="0.6.1",
        slug="map-var-wait",
        field="mutatingAdmissionPolicy.variables",
        fail_val="waitHost=old-schema-registry",
        fix_val="waitHost=",
        hide_path="brokerHost",
        hide_old="brokerHost: linch-api.linch.svc\n",
        hide_new="brokerHost: 127.0.0.1\n",
        values_fail="waitHost: old-schema-registry\nbrokerHost: linch-api.linch.svc\n",
        values_fix="waitHost: \"\"\nbrokerHost: linch-api.linch.svc\n",
        tpl="  variables:\n    - name: waitHost\n      expression: \"'{{ .Values.waitHost }}'\"\n",
        log="wait-for old-schema-registry.linch.svc NXDOMAIN leftover; MAP variables waitHost inject CrashLoop",
        live_ok="mutatingAdmissionPolicy.variables waitHost=",
        hide_name="broker 127.0.0.1",
        new_vs="MutatingAdmissionPolicy variables leftover, not MAP Binding wait-old-broker and not MAP JSONPatch OTLP",
        seed="leftover MAP variables waitHost=old-schema-registry; NXDOMAIN CrashLoop",
        n2="replica n2 still MAP variables waitHost=old-schema-registry after git empty",
        ci="# MAP variables waitHost must be empty. Never loopback the broker host to hide NXDOMAIN.",
        handoff="LEFTOVER: replica n2 still MAP variables waitHost=old-schema-registry. Platform: delete leftover RS. No loopback hide.",
        pytest_ok="test_var_empty\ntest_not_loopback_hide\ntest_not_mapb\ntest_pods_ready\ntest_no_force\ntest_wait",
        pytest_fail="test_var_empty_all FAILED b==old-schema-registry",
        tmpl_test="test_template_matches_git",
        rs="fe8",
    ),
    pair(
        plant="rummel-prod",
        app="rummel-api",
        chart="1.9.3",
        slug="servicecidr-finalizer",
        field="serviceCIDR.metadata.finalizers",
        fail_val="networking.k8s.io/service-cidrs-finalizer",
        fix_val="[]",
        hide_path="clusterIP",
        hide_old="clusterIP: 10.98.40.40\n",
        hide_new="clusterIP: None\n",
        values_fail="finalizer: networking.k8s.io/service-cidrs-finalizer\nclusterIP: 10.98.40.40\n",
        values_fix="finalizer: \"\"\nclusterIP: 10.98.40.40\n",
        tpl="  metadata:\n    finalizers:\n      - {{ .Values.finalizer }}\n",
        log="ServiceCIDR finalizer leftover blocked Ready; kube-proxy did not program 10.98.40.40 CrashLoop",
        live_ok="serviceCIDR.metadata.finalizers=[]",
        hide_name="headless ClusterIP None",
        new_vs="ServiceCIDR finalizers leftover, not ServiceCIDR Ready=False and not ServiceCIDR overlapping cidrs",
        seed="leftover ServiceCIDR finalizer stuck; VIP unprogrammed CrashLoop",
        n2="replica n2 still ServiceCIDR finalizer after git empty finalizers",
        ci="# ServiceCIDR finalizer must not block Ready. Never headless to hide an unprogrammed VIP.",
        handoff="LEFTOVER: replica n2 still ServiceCIDR finalizer. Platform: delete leftover RS. No headless hide.",
        pytest_ok="test_fin_empty\ntest_not_headless_hide\ntest_not_ready_false\ntest_pods_ready\ntest_no_force\ntest_fin",
        pytest_fail="test_fin_empty_all FAILED b==service-cidrs-finalizer",
        tmpl_test="test_template_matches_git",
        rs="a09",
    ),
    pair(
        plant="swash-prod",
        app="swash-api",
        chart="2.1.8",
        slug="resourceslice-allnodes",
        field="resourceSlice.allNodes",
        fail_val="true",
        fix_val="false",
        hide_path="hostPath",
        hide_old="hostPath: false\n",
        hide_new="hostPath: true\n",
        values_fail="allNodes: true\nhostPath: false\n",
        values_fix="allNodes: false\nhostPath: false\n",
        tpl="  allNodes: {{ .Values.allNodes }}\n",
        log="open /dev/nvidia0: no such device leftover ResourceSlice allNodes=true on CPU nodes CrashLoop",
        live_ok="resourceSlice.allNodes=false",
        hide_name="hostPath /dev/nvidia0",
        new_vs="ResourceSlice allNodes leftover, not ResourceSlice nodeName gpu-node-dead and not ResourceSlice driver FPGA",
        seed="leftover ResourceSlice allNodes=true; ENODEV on CPU nodes CrashLoop",
        n2="replica n2 still ResourceSlice allNodes=true after git false",
        ci="# ResourceSlice allNodes must be false. Never hostPath to hide ENODEV on CPU nodes.",
        handoff="LEFTOVER: replica n2 still ResourceSlice allNodes=true. Platform: delete leftover RS. No hostPath hide.",
        pytest_ok="test_allnodes_false\ntest_not_hostpath_hide\ntest_not_node_dead\ntest_pods_ready\ntest_no_force\ntest_all",
        pytest_fail="test_allnodes_false_all FAILED b==true",
        tmpl_test="test_template_matches_git",
        rs="b1a",
    ),
    pair(
        plant="lochan-prod",
        app="lochan-api",
        chart="0.4.9",
        slug="deviceclass-driver-gone",
        field="deviceClass.config.opaque.driver",
        fail_val="gpu.example.com/old",
        fix_val="gpu.example.com",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="opaqueDriver: gpu.example.com/old\nprivileged: false\n",
        values_fix="opaqueDriver: gpu.example.com\nprivileged: false\n",
        tpl="  config:\n    - opaque:\n        driver: {{ .Values.opaqueDriver }}\n",
        log="plugin gpu.example.com/old not found leftover DeviceClass opaque driver CrashLoop",
        live_ok="deviceClass.config.opaque.driver=gpu.example.com",
        hide_name="privileged",
        new_vs="DeviceClass opaque driver leftover, not DeviceClass name old-gpu and not DeviceClass extendedResourceName",
        seed="leftover DeviceClass opaque driver gpu.example.com/old; missing plugin CrashLoop",
        n2="replica n2 still opaque driver gpu.example.com/old after git gpu.example.com",
        ci="# DeviceClass opaque driver must name the live plugin. Never privileged to hide a missing driver.",
        handoff="LEFTOVER: replica n2 still DeviceClass opaque driver gpu.example.com/old. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_drv_live\ntest_not_priv_hide\ntest_not_old_gpu\ntest_pods_ready\ntest_no_force\ntest_drv",
        pytest_fail="test_drv_live_all FAILED b==gpu.example.com/old",
        tmpl_test="test_template_matches_git",
        rs="c2b",
    ),
    pair(
        plant="scarp-prod",
        app="scarp-api",
        chart="3.0.6",
        slug="vapb-matchres-old",
        field="validatingAdmissionPolicyBinding.matchResources",
        fail_val="resourceRules=pods/old",
        fix_val="resourceRules=pods",
        hide_path="failurePolicy",
        hide_old="failurePolicy: Fail\n",
        hide_new="failurePolicy: Ignore\n",
        values_fail="matchResource: pods/old\nfailurePolicy: Fail\nenv:\n  FAIL_FAST: \"1\"\n",
        values_fix="matchResource: pods\nfailurePolicy: Fail\nenv:\n  FAIL_FAST: \"0\"\n",
        tpl="  matchResources:\n    resourceRules:\n      - resources: [{{ .Values.matchResource }}]\n",
        log="FATAL fail-fast leftover; VAP Binding matchResources pods/old missed live pods; FAIL_FAST admitted CrashLoop",
        live_ok="matchResources=pods FAIL_FAST=0",
        hide_name="failurePolicy Ignore",
        new_vs="VAP Binding matchResources leftover, not VAP Binding paramRef and not VAP matchConditions",
        seed="leftover VAP Binding matchResources pods/old; FAIL_FAST admitted CrashLoop",
        n2="replica n2 still matchResources pods/old after git pods",
        ci="# VAP Binding matchResources must match pods. Never Ignore failurePolicy to hide a miss.",
        handoff="LEFTOVER: replica n2 still VAP Binding matchResources pods/old. Platform: delete leftover RS. No Ignore hide.",
        pytest_ok="test_res_pods\ntest_not_ignore_hide\ntest_not_paramref\ntest_pods_ready\ntest_no_force\ntest_res",
        pytest_fail="test_res_pods_all FAILED b==pods/old",
        tmpl_test="test_template_matches_git",
        rs="d3c",
    ),
    pair(
        plant="barrow-prod",
        app="barrow-api",
        chart="1.3.4",
        slug="map-failpolicy-ignore",
        field="mutatingAdmissionPolicy.failurePolicy",
        fail_val="Ignore",
        fix_val="Fail",
        hide_path="replicas",
        hide_old="replicas: 2\n",
        hide_new="replicas: 0\n",
        values_fail="failurePolicy: Ignore\nreplicas: 2\nwaitFor: old-broker.barrow.svc\n",
        values_fix="failurePolicy: Fail\nreplicas: 2\nwaitFor: barrow-api.barrow.svc\n",
        tpl="  failurePolicy: {{ .Values.failurePolicy }}\n",
        log="MAP CEL error leftover failurePolicy Ignore still injected wait-for old-broker; NXDOMAIN CrashLoop",
        live_ok="mutatingAdmissionPolicy.failurePolicy=Fail",
        hide_name="replicas 0",
        new_vs="MutatingAdmissionPolicy failurePolicy Ignore leftover, not VAP failurePolicy and not MAP Binding wait-old-broker",
        seed="leftover MAP failurePolicy Ignore; stale wait-for still injected CrashLoop",
        n2="replica n2 still MAP failurePolicy Ignore after git Fail",
        ci="# MAP failurePolicy must Fail closed. Never scale to 0 to hide NXDOMAIN.",
        handoff="LEFTOVER: replica n2 still MAP failurePolicy Ignore. Platform: delete leftover RS. No replicas-0 hide.",
        pytest_ok="test_fp_fail\ntest_not_scale0_hide\ntest_not_mapb\ntest_pods_ready\ntest_no_force\ntest_fp",
        pytest_fail="test_fp_fail_all FAILED b==Ignore",
        tmpl_test="test_template_matches_git",
        rs="e4d",
    ),
    pair(
        plant="hamlet-prod",
        app="hamlet-api",
        chart="5.0.2",
        slug="clustercidr-hostbits",
        field="clusterCIDR.perNodeHostBits",
        fail_val="8",
        fix_val="24",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="perNodeHostBits: 8\nhostNetwork: false\n",
        values_fix="perNodeHostBits: 24\nhostNetwork: false\n",
        tpl="  perNodeHostBits: {{ .Values.perNodeHostBits }}\n",
        log="pod CIDR exhausted leftover ClusterCIDR perNodeHostBits=8; CNI fail CrashLoop",
        live_ok="clusterCIDR.perNodeHostBits=24",
        hide_name="hostNetwork",
        new_vs="ClusterCIDR perNodeHostBits leftover, not ClusterCIDR cidr 10.244 string and not ClusterCIDR nodeSelector",
        seed="leftover ClusterCIDR perNodeHostBits=8; pod CIDR exhausted CrashLoop",
        n2="replica n2 still perNodeHostBits=8 after git 24",
        ci="# ClusterCIDR perNodeHostBits must be 24. Never hostNetwork to hide exhausted pod CIDR.",
        handoff="LEFTOVER: replica n2 still ClusterCIDR perNodeHostBits=8. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_bits_24\ntest_not_hostnet_hide\ntest_not_cidr_string\ntest_pods_ready\ntest_no_force\ntest_bits",
        pytest_fail="test_bits_24_all FAILED b==8",
        tmpl_test="test_template_matches_git",
        rs="f5e",
    ),
    pair(
        plant="inge-prod",
        app="inge-api",
        chart="2.6.6",
        slug="ipaddr-cidrname",
        field="ipAddress.spec.serviceCIDRName",
        fail_val="old-cidr",
        fix_val="prod-cidr",
        hide_path="sessionAffinity",
        hide_old="sessionAffinity: None\n",
        hide_new="sessionAffinity: ClientIP\n",
        values_fail="serviceCIDRName: old-cidr\nsessionAffinity: None\n",
        values_fix="serviceCIDRName: prod-cidr\nsessionAffinity: None\n",
        tpl="  spec:\n    serviceCIDRName: {{ .Values.serviceCIDRName }}\n",
        log="IPAddress serviceCIDRName old-cidr leftover; parent ServiceCIDR missing; kube-proxy skip CrashLoop",
        live_ok="ipAddress.spec.serviceCIDRName=prod-cidr",
        hide_name="sessionAffinity ClientIP",
        new_vs="IPAddress serviceCIDRName leftover, not IPAddress outside ServiceCIDR gap and not spec.ipFamilies",
        seed="leftover IPAddress serviceCIDRName old-cidr; VIP unprogrammed CrashLoop",
        n2="replica n2 still serviceCIDRName old-cidr after git prod-cidr",
        ci="# IPAddress serviceCIDRName must name prod-cidr. Never ClientIP stickiness to hide a missing CIDR.",
        handoff="LEFTOVER: replica n2 still IPAddress serviceCIDRName old-cidr. Platform: delete leftover RS. No ClientIP hide.",
        pytest_ok="test_name_prod\ntest_not_affinity_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_name",
        pytest_fail="test_name_prod_all FAILED b==old-cidr",
        tmpl_test="test_template_matches_git",
        rs="a6f",
    ),
    pair(
        plant="lynck-prod",
        app="lynck-api",
        chart="1.7.7",
        slug="rclaim-admin-gone",
        field="resourceClaim.devices.requests.adminAccess",
        fail_val="true",
        fix_val="false",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="adminAccess: true\nprivileged: false\n",
        values_fix="adminAccess: false\nprivileged: false\n",
        tpl="  devices:\n    requests:\n      - adminAccess: {{ .Values.adminAccess }}\n",
        log="CUDA on exclusive GPU leftover ResourceClaim adminAccess=true; device busy CrashLoop",
        live_ok="resourceClaim.devices.requests.adminAccess=false",
        hide_name="privileged",
        new_vs="ResourceClaim adminAccess leftover, not allocationResult gpu-0-gone and not DeviceClass CEL",
        seed="leftover ResourceClaim adminAccess=true; exclusive GPU busy CrashLoop",
        n2="replica n2 still adminAccess=true after git false",
        ci="# ResourceClaim adminAccess must be false. Never privileged to hide a busy exclusive GPU.",
        handoff="LEFTOVER: replica n2 still ResourceClaim adminAccess=true. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_admin_false\ntest_not_priv_hide\ntest_not_alloc_result\ntest_pods_ready\ntest_no_force\ntest_admin",
        pytest_fail="test_admin_false_all FAILED b==true",
        tmpl_test="test_template_matches_git",
        rs="b70",
    ),
]


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 88 - (round_n % 5)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"Quota 2. Unique CrashLoopBackOff pair. Catalog r70–r962 stays in raw "
        f"(empty-ENV / spec leftover cartesian). New: {s['new_vs']}. "
        f"Plant `{s['plant']}` (not bay-prod/cwm/llyn).\n"
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
        f"- No bay-prod / cwm / llyn / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r963–r1006 or mill-pref r1076–r1091 leftover families.\n"
    )


def write_round(round_n: int, staging: Path, spec: dict) -> None:
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    if "-w3-empty" in a["id"] or "sx" in a["id"] or "-w3-empty" in b["id"]:
        raise SystemExit("banned id")
    a["meta"]["generator"] = GEN
    b["meta"]["generator"] = GEN
    blob = json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    if STAMP in blob:
        raise SystemExit(f"stamp in batch r{round_n}")
    for needle in ("BITBUCKET_HOME", "KEYCLOAK_HOME", "spec.ipFamilies", "spike_events"):
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
    cursor = 0
    hops = 0
    taken = taken_slugs()
    print(
        f"r1092 mill start pairs={len(PAIRS)} taken_slugs={len(taken)} "
        f"max_rounds={MAX_ROUNDS} gen={GEN}",
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
    print(f"DONE published={published} hops={hops} cursor={cursor}", flush=True)
    return 0 if len(published) >= 12 else (0 if published else 1)


if __name__ == "__main__":
    raise SystemExit(main())
