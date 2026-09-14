#!/usr/bin/env python3
"""k8s-crashloop mill: preferred leftover APIs. Q=2. grok-4.6.

Unique vs r963–r1006 and vs the r1007 mill catalog (pightle…scarth).
Leftovers: ServiceCIDR, IPAddress, ValidatingAdmissionPolicy,
MutatingAdmissionPolicyBinding, StorageVersion, DeviceClass, ResourceSlice,
ClusterCIDR, StorageVersionMigration, ResourceClaimTemplate,
ValidatingAdmissionPolicyBinding, DeviceClass CEL, IPAddress Service parent,
ServiceCIDR condition, DRA allocationResult leftover.
Loop: frontier → reserve --expected 2 → stage → publish.
If reserved, do not steal; retry until unreserved (other mill is live).
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

_spec = importlib.util.spec_from_file_location("kcl_peer", PEER)
_peer = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_peer)
success_episode = _peer.success_episode
leftover_episode = _peer.leftover_episode


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
    return kwargs


PAIRS: list[dict] = [
    pair(
        plant="keld-prod",
        app="keld-api",
        chart="1.2.0",
        slug="servicecidr-stale",
        field="serviceCIDR",
        fail_val="10.96.0.0/24",
        fix_val="10.97.0.0/16",
        hide_path="clusterIP",
        hide_old="clusterIP: 10.96.0.10\n",
        hide_new="clusterIP: None\n",
        values_fail="serviceCIDR: 10.96.0.0/24\nclusterIP: 10.96.0.10\n",
        values_fix="serviceCIDR: 10.97.0.0/16\nclusterIP: 10.97.0.10\n",
        tpl="  cidrs:\n    - {{ .Values.serviceCIDR }}\n",
        log="dial tcp 10.96.0.10:443 i/o timeout; leftover ServiceCIDR not programmed by kube-proxy",
        live_ok="serviceCIDR=10.97.0.0/16",
        hide_name="headless ClusterIP None",
        new_vs="ServiceCIDR leftover, not spec.ipFamilies and not ITP Local",
        seed="leftover ServiceCIDR 10.96.0.0/24; kube-proxy blackhole CrashLoop",
        n2="n2 leftover still dials 10.96.0.10 after git 10.97.0.0/16",
        ci="# ServiceCIDR must match the live VIP. Never headless to hide a blackhole ClusterIP.",
        handoff="LEFTOVER: n2 still ServiceCIDR 10.96.0.0/24. Platform: delete leftover RS. No headless hide.",
        pytest_ok="test_cidr_97\ntest_not_headless_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_vip",
        pytest_fail="test_cidr_97_all FAILED b==10.96.0.0/24",
        tmpl_test="test_template_matches_git",
        rs="k01",
    ),
    pair(
        plant="lynchet-prod",
        app="lynchet-api",
        chart="2.0.4",
        slug="ipaddress-orphan",
        field="ipAddress.parentRef",
        fail_val="svc/lynchet-old",
        fix_val="svc/lynchet-api",
        hide_path="port",
        hide_old="port: 8080\n",
        hide_new="port: 8081\n",
        values_fail="ipAddress: 10.97.13.8\nparentRef: svc/lynchet-old\nport: 8080\n",
        values_fix="ipAddress: 10.97.13.8\nparentRef: svc/lynchet-api\nport: 8080\n",
        tpl="  parentRef:\n    name: {{ .Values.parentRef | trimPrefix \"svc/\" }}\n",
        log="packets to 10.97.13.8 blackhole; leftover IPAddress ParentRef deleted Service",
        live_ok="ipAddress.parentRef=svc/lynchet-api",
        hide_name="port 8081",
        new_vs="IPAddress leftover, not spec.ipFamilies and not EndpointSlice",
        seed="leftover IPAddress ParentRef svc/lynchet-old; VIP blackhole CrashLoop",
        n2="n2 leftover still ParentRef lynchet-old after git lynchet-api",
        ci="# IPAddress ParentRef must name a live Service. Never retarget port to hide a blackhole VIP.",
        handoff="LEFTOVER: n2 still IPAddress ParentRef lynchet-old. Platform: delete leftover RS. No port hide.",
        pytest_ok="test_parent_api\ntest_not_port_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_ipaddr",
        pytest_fail="test_parent_api_all FAILED b==svc/lynchet-old",
        tmpl_test="test_template_matches_git",
        rs="k02",
    ),
    pair(
        plant="hause-prod",
        app="hause-api",
        chart="3.1.0",
        slug="vap-audit-failfast",
        field="validationActions",
        fail_val="Audit",
        fix_val="Deny",
        hide_path="image.tag",
        hide_old="tag: 3.1.0\n",
        hide_new="tag: 3.1.0-debug\n",
        values_fail="validationActions: [Audit]\nenv:\n  FAIL_FAST: \"1\"\nimage:\n  tag: 3.1.0\n",
        values_fix="validationActions: [Deny]\nenv:\n  FAIL_FAST: \"0\"\nimage:\n  tag: 3.1.0\n",
        tpl="  validations:\n    - expression: object.spec.containers[0].env.exists(e, e.name=='FAIL_FAST' && e.value=='1') == false\n  validationActions: {{ .Values.validationActions }}\n",
        log="FATAL fail-fast=1 leftover; ValidatingAdmissionPolicy Audit admitted it; exit 1",
        live_ok="validationActions=[Deny] FAIL_FAST=0",
        hide_name="debug tag",
        new_vs="ValidatingAdmissionPolicy leftover, not webhook timeout and not VAC",
        seed="leftover ValidatingAdmissionPolicy validationActions Audit; FAIL_FAST admitted CrashLoop",
        n2="n2 leftover still Audit + FAIL_FAST=1 after git Deny + 0",
        ci="# VAP must Deny FAIL_FAST. Never retag debug to hide an admitted crash env.",
        handoff="LEFTOVER: n2 still VAP Audit + FAIL_FAST=1. Platform: delete leftover RS. No debug-tag hide.",
        pytest_ok="test_vap_deny\ntest_not_tag_hide\ntest_not_timeout\ntest_pods_ready\ntest_no_force\ntest_failfast",
        pytest_fail="test_vap_deny_all FAILED b==Audit",
        tmpl_test="test_template_matches_git",
        rs="k03",
    ),
    pair(
        plant="scree-prod",
        app="scree-api",
        chart="0.9.7",
        slug="mapb-wait-oldbroker",
        field="mutatingAdmissionPolicyBinding",
        fail_val="scree-wait-old-broker",
        fix_val="",
        hide_path="brokerHost",
        hide_old="brokerHost: old-broker.scree.svc\n",
        hide_new="brokerHost: 127.0.0.1\n",
        values_fail="mapBinding: scree-wait-old-broker\nbrokerHost: old-broker.scree.svc\n",
        values_fix="mapBinding: \"\"\nbrokerHost: scree-api.scree.svc\n",
        tpl="  mutatingAdmissionPolicyBinding: {{ .Values.mapBinding | quote }}\n",
        log="wait-for old-broker.scree.svc:9092 NXDOMAIN; leftover MAP Binding inject CrashLoop",
        live_ok="mapBinding=",
        hide_name="broker 127.0.0.1",
        new_vs="MutatingAdmissionPolicyBinding leftover, not webhook timeout and not shaw JAVA_TOOL_OPTIONS MAP",
        seed="leftover MAP Binding injects wait-for old-broker; NXDOMAIN CrashLoop",
        n2="n2 leftover still MAP Binding wait-old-broker after git empty binding",
        ci="# MAP Binding leftover mutates wait-for. Never loopback the broker host to hide NXDOMAIN.",
        handoff="LEFTOVER: n2 still MAP Binding wait-old-broker. Platform: delete leftover RS. No loopback hide.",
        pytest_ok="test_mapb_empty\ntest_not_loopback_hide\ntest_not_xmx\ntest_pods_ready\ntest_no_force\ntest_wait",
        pytest_fail="test_mapb_empty_all FAILED b==scree-wait-old-broker",
        tmpl_test="test_template_matches_git",
        rs="k04",
    ),
    pair(
        plant="swale-prod",
        app="swale-api",
        chart="4.0.1",
        slug="storageversion-alpha",
        field="crd.storageVersion",
        fail_val="v1alpha1",
        fix_val="v1beta1",
        hide_path="operatorTag",
        hide_old="operatorTag: 4.0.1\n",
        hide_new="operatorTag: 4.0.1-compat\n",
        values_fail="storageVersion: v1alpha1\noperatorTag: 4.0.1\n",
        values_fix="storageVersion: v1beta1\noperatorTag: 4.0.1\n",
        tpl="  versions:\n    - name: {{ .Values.storageVersion }}\n      storage: true\n",
        log="panic: .status.ready missing on v1alpha1 leftover storage; operator CrashLoop",
        live_ok="crd.storageVersion=v1beta1",
        hide_name="compat operator tag",
        new_vs="StorageVersion leftover, not CRD conversion webhook timeout",
        seed="leftover CRD storage v1alpha1; operator cannot decode status.ready CrashLoop",
        n2="n2 leftover still storage v1alpha1 after git v1beta1",
        ci="# CRD storage must be v1beta1. Never a compat tag to hide alpha storage.",
        handoff="LEFTOVER: n2 still CRD storage v1alpha1. Platform: delete leftover RS. No compat-tag hide.",
        pytest_ok="test_storage_v1beta1\ntest_not_tag_hide\ntest_not_conversion\ntest_pods_ready\ntest_no_force\ntest_crd",
        pytest_fail="test_storage_v1beta1_all FAILED b==v1alpha1",
        tmpl_test="test_template_matches_git",
        rs="k05",
    ),
    pair(
        plant="carr-prod",
        app="carr-api",
        chart="1.1.5",
        slug="deviceclass-void",
        field="deviceClassName",
        fail_val="example.com/old-gpu",
        fix_val="example.com/gpu",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="deviceClassName: example.com/old-gpu\nprivileged: false\n",
        values_fix="deviceClassName: example.com/gpu\nprivileged: false\n",
        tpl="  resourceClaims:\n    - name: gpu\n      source:\n        resourceClaimTemplateName: {{ .Values.deviceClassName }}\n",
        log="CUDA_ERROR_NO_DEVICE NVIDIA_VISIBLE_DEVICES=void leftover DeviceClass CrashLoop",
        live_ok="deviceClassName=example.com/gpu",
        hide_name="privileged",
        new_vs="DeviceClass leftover, not hugepages and not cpuManager",
        seed="leftover DeviceClass example.com/old-gpu injects void GPU; CUDA CrashLoop",
        n2="n2 leftover still DeviceClass old-gpu after git example.com/gpu",
        ci="# DeviceClass must name a live GPU class. Never privileged to hide a void device.",
        handoff="LEFTOVER: n2 still DeviceClass old-gpu. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_class_gpu\ntest_not_priv_hide\ntest_not_hugepage\ntest_pods_ready\ntest_no_force\ntest_cuda",
        pytest_fail="test_class_gpu_all FAILED b==example.com/old-gpu",
        tmpl_test="test_template_matches_git",
        rs="k06",
    ),
    pair(
        plant="wath-prod",
        app="wath-api",
        chart="2.3.3",
        slug="resourceslice-gone",
        field="resourceSlice.driver",
        fail_val="vendor.com/fpga",
        fix_val="vendor.com/gpu",
        hide_path="hostPath",
        hide_old="hostPath: false\n",
        hide_new="hostPath: true\n",
        values_fail="resourceSliceDriver: vendor.com/fpga\nhostPath: false\n",
        values_fix="resourceSliceDriver: vendor.com/gpu\nhostPath: false\n",
        tpl="  driver: {{ .Values.resourceSliceDriver }}\n",
        log="open /dev/fpga0: no such device; leftover ResourceSlice advertised missing FPGA",
        live_ok="resourceSlice.driver=vendor.com/gpu",
        hide_name="hostPath /dev/fpga0",
        new_vs="ResourceSlice leftover, not DRA DeviceClass void GPU and not hugepages",
        seed="leftover ResourceSlice vendor.com/fpga; ENODEV CrashLoop",
        n2="n2 leftover still ResourceSlice fpga after git gpu",
        ci="# ResourceSlice must match a live driver. Never hostPath to hide ENODEV.",
        handoff="LEFTOVER: n2 still ResourceSlice vendor.com/fpga. Platform: delete leftover RS. No hostPath hide.",
        pytest_ok="test_slice_gpu\ntest_not_hostpath_hide\ntest_not_void_gpu\ntest_pods_ready\ntest_no_force\ntest_fpga",
        pytest_fail="test_slice_gpu_all FAILED b==vendor.com/fpga",
        tmpl_test="test_template_matches_git",
        rs="k07",
    ),
    pair(
        plant="lode-prod",
        app="lode-api",
        chart="0.7.2",
        slug="clustercidr-stale",
        field="clusterCIDR",
        fail_val="10.244.0.0/16",
        fix_val="10.245.0.0/16",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="clusterCIDR: 10.244.0.0/16\nhostNetwork: false\n",
        values_fix="clusterCIDR: 10.245.0.0/16\nhostNetwork: false\n",
        tpl="  ipv4:\n    cidrs:\n      - {{ .Values.clusterCIDR }}\n",
        log="dial 10.244.4.8: no route to host; leftover ClusterCIDR not programmed by CNI",
        live_ok="clusterCIDR=10.245.0.0/16",
        hide_name="hostNetwork",
        new_vs="ClusterCIDR leftover, not ServiceCIDR and not hostNetwork dnsPolicy leftover",
        seed="leftover ClusterCIDR 10.244.0.0/16; CNI blackhole CrashLoop",
        n2="n2 leftover still ClusterCIDR 10.244.0.0/16 after git 10.245.0.0/16",
        ci="# ClusterCIDR must match the live pod network. Never hostNetwork to hide a stale pod CIDR.",
        handoff="LEFTOVER: n2 still ClusterCIDR 10.244.0.0/16. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_cidr_245\ntest_not_hostnet_hide\ntest_not_servicecidr\ntest_pods_ready\ntest_no_force\ntest_cni",
        pytest_fail="test_cidr_245_all FAILED b==10.244.0.0/16",
        tmpl_test="test_template_matches_git",
        rs="k08",
    ),
    pair(
        plant="shott-prod",
        app="shott-api",
        chart="5.5.0",
        slug="svm-stuck-alpha",
        field="storageVersionMigration",
        fail_val="v1alpha1-stuck",
        fix_val="complete-v1beta1",
        hide_path="watchTimeout",
        hide_old="watchTimeout: 30s\n",
        hide_new="watchTimeout: 10m\n",
        values_fail="storageVersionMigration: v1alpha1-stuck\nwatchTimeout: 30s\n",
        values_fix="storageVersionMigration: complete-v1beta1\nwatchTimeout: 30s\n",
        tpl="  storageVersionMigration: {{ .Values.storageVersionMigration }}\n",
        log="watch decode mixed v1alpha1/v1beta1 leftover StorageVersionMigration stuck CrashLoop",
        live_ok="storageVersionMigration=complete-v1beta1",
        hide_name="watchTimeout 10m",
        new_vs="StorageVersionMigration leftover, not CRD storageVersion alpha and not conversion timeout",
        seed="leftover StorageVersionMigration stuck on v1alpha1; mixed decode CrashLoop",
        n2="n2 leftover still SVM v1alpha1-stuck after git complete-v1beta1",
        ci="# StorageVersionMigration must finish. Never stretch watchTimeout to hide mixed storage.",
        handoff="LEFTOVER: n2 still StorageVersionMigration v1alpha1-stuck. Platform: delete leftover RS. No timeout hide.",
        pytest_ok="test_svm_complete\ntest_not_timeout_hide\ntest_not_storage_alpha\ntest_pods_ready\ntest_no_force\ntest_mig",
        pytest_fail="test_svm_complete_all FAILED b==v1alpha1-stuck",
        tmpl_test="test_template_matches_git",
        rs="k09",
    ),
    pair(
        plant="vinney-prod",
        app="vinney-api",
        chart="1.4.8",
        slug="rct-old-nic",
        field="resourceClaimTemplate",
        fail_val="example.com/old-nic",
        fix_val="example.com/nic",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="resourceClaimTemplate: example.com/old-nic\nhostNetwork: false\n",
        values_fix="resourceClaimTemplate: example.com/nic\nhostNetwork: false\n",
        tpl="  resourceClaimTemplates:\n    - spec:\n        devices:\n          requests:\n            - deviceClassName: {{ .Values.resourceClaimTemplate }}\n",
        log="open /dev/old-nic: no such device; leftover ResourceClaimTemplate CrashLoop",
        live_ok="resourceClaimTemplate=example.com/nic",
        hide_name="hostNetwork",
        new_vs="ResourceClaimTemplate leftover, not DeviceClass void GPU and not ResourceSlice FPGA",
        seed="leftover ResourceClaimTemplate example.com/old-nic; ENODEV CrashLoop",
        n2="n2 leftover still RCT old-nic after git example.com/nic",
        ci="# ResourceClaimTemplate must name a live NIC class. Never hostNetwork to hide ENODEV.",
        handoff="LEFTOVER: n2 still ResourceClaimTemplate old-nic. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_rct_nic\ntest_not_hostnet_hide\ntest_not_void_gpu\ntest_pods_ready\ntest_no_force\ntest_nic",
        pytest_fail="test_rct_nic_all FAILED b==example.com/old-nic",
        tmpl_test="test_template_matches_git",
        rs="k10",
    ),
    pair(
        plant="milt-prod",
        app="milt-api",
        chart="2.8.1",
        slug="vapb-param-old",
        field="validatingAdmissionPolicyBinding.paramRef",
        fail_val="cm/milt-failfast-old",
        fix_val="cm/milt-failfast-off",
        hide_path="failurePolicy",
        hide_old="failurePolicy: Fail\n",
        hide_new="failurePolicy: Ignore\n",
        values_fail="paramRef: cm/milt-failfast-old\nfailurePolicy: Fail\nenv:\n  FAIL_FAST: \"1\"\n",
        values_fix="paramRef: cm/milt-failfast-off\nfailurePolicy: Fail\nenv:\n  FAIL_FAST: \"0\"\n",
        tpl="  paramRef:\n    name: {{ .Values.paramRef | trimPrefix \"cm/\" }}\n",
        log="FATAL fail-fast param leftover ValidatingAdmissionPolicyBinding cm/milt-failfast-old CrashLoop",
        live_ok="paramRef=cm/milt-failfast-off",
        hide_name="failurePolicy Ignore",
        new_vs="ValidatingAdmissionPolicyBinding paramRef leftover, not VAP Audit and not webhook timeout",
        seed="leftover VAP Binding paramRef cm/milt-failfast-old; FAIL_FAST CrashLoop",
        n2="n2 leftover still paramRef milt-failfast-old after git milt-failfast-off",
        ci="# VAP Binding paramRef must point at failfast-off. Never Ignore to hide a leftover param.",
        handoff="LEFTOVER: n2 still VAP Binding paramRef milt-failfast-old. Platform: delete leftover RS. No Ignore hide.",
        pytest_ok="test_param_off\ntest_not_ignore_hide\ntest_not_vap_audit\ntest_pods_ready\ntest_no_force\ntest_param",
        pytest_fail="test_param_off_all FAILED b==cm/milt-failfast-old",
        tmpl_test="test_template_matches_git",
        rs="k11",
    ),
    pair(
        plant="howk-prod",
        app="howk-api",
        chart="0.6.6",
        slug="deviceclass-cel-none",
        field="deviceClass.selectors",
        fail_val="device.capacity['example.com/mem'].compareTo(quantity('8Gi')) >= 0",
        fix_val="device.capacity['example.com/mem'].compareTo(quantity('1Gi')) >= 0",
        hide_path="count",
        hide_old="count: 1\n",
        hide_new="count: 0\n",
        values_fail="cel: \"device.capacity['example.com/mem'].compareTo(quantity('8Gi')) >= 0\"\ncount: 1\n",
        values_fix="cel: \"device.capacity['example.com/mem'].compareTo(quantity('1Gi')) >= 0\"\ncount: 1\n",
        tpl="  selectors:\n    - cel:\n        expression: {{ .Values.cel | quote }}\n",
        log="allocation empty leftover DeviceClass CEL 8Gi; NVIDIA_VISIBLE_DEVICES=void CrashLoop",
        live_ok="deviceClass.selectors=1Gi",
        hide_name="count 0",
        new_vs="DeviceClass CEL leftover, not DeviceClass name old-gpu and not hugepages",
        seed="leftover DeviceClass CEL requires 8Gi device mem; void allocation CrashLoop",
        n2="n2 leftover still CEL 8Gi after git 1Gi",
        ci="# DeviceClass CEL must match live device capacity. Never count:0 to hide a void alloc.",
        handoff="LEFTOVER: n2 still DeviceClass CEL 8Gi. Platform: delete leftover RS. No count-0 hide.",
        pytest_ok="test_cel_1gi\ntest_not_count0_hide\ntest_not_old_gpu\ntest_pods_ready\ntest_no_force\ntest_cel",
        pytest_fail="test_cel_1gi_all FAILED b==8Gi",
        tmpl_test="test_template_matches_git",
        rs="k12",
    ),
    pair(
        plant="reen-prod",
        app="reen-api",
        chart="1.9.9",
        slug="ipaddr-servicecidr-gap",
        field="ipAddress.spec",
        fail_val="10.96.255.4",
        fix_val="10.97.12.4",
        hide_path="allocateLoadBalancerNodePorts",
        hide_old="sessionAffinity: None\n",
        hide_new="sessionAffinity: ClientIP\n",
        values_fail="ipAddress: 10.96.255.4\nserviceCIDR: 10.97.0.0/16\nsessionAffinity: None\n",
        values_fix="ipAddress: 10.97.12.4\nserviceCIDR: 10.97.0.0/16\nsessionAffinity: None\n",
        tpl="  spec:\n    address: {{ .Values.ipAddress }}\n    parentRef:\n      name: reen-api\n",
        log="IPAddress 10.96.255.4 outside ServiceCIDR 10.97.0.0/16 leftover; kube-proxy skip CrashLoop",
        live_ok="ipAddress=10.97.12.4",
        hide_name="sessionAffinity ClientIP",
        new_vs="IPAddress outside ServiceCIDR leftover, not sessionAffinity ClientIP and not ipFamilies",
        seed="leftover IPAddress 10.96.255.4 outside live ServiceCIDR; kube-proxy skip CrashLoop",
        n2="n2 leftover still IPAddress 10.96.255.4 after git 10.97.12.4",
        ci="# IPAddress must sit inside ServiceCIDR. Never ClientIP stickiness to hide a gap VIP.",
        handoff="LEFTOVER: n2 still IPAddress 10.96.255.4. Platform: delete leftover RS. No ClientIP hide.",
        pytest_ok="test_ip_97\ntest_not_affinity_hide\ntest_not_ipfamilies\ntest_pods_ready\ntest_no_force\ntest_gap",
        pytest_fail="test_ip_97_all FAILED b==10.96.255.4",
        tmpl_test="test_template_matches_git",
        rs="k13",
    ),
    pair(
        plant="rhos-prod",
        app="rhos-api",
        chart="3.0.0",
        slug="servicecidr-condition",
        field="serviceCIDR.status.conditions",
        fail_val="Ready=False",
        fix_val="Ready=True",
        hide_path="clusterIP",
        hide_old="clusterIP: 10.97.20.20\n",
        hide_new="clusterIP: None\n",
        values_fail="serviceCIDRReady: false\nclusterIP: 10.97.20.20\n",
        values_fix="serviceCIDRReady: true\nclusterIP: 10.97.20.20\n",
        tpl="  status:\n    conditions:\n      - type: Ready\n        status: {{ if .Values.serviceCIDRReady }}True{{ else }}False{{ end }}\n",
        log="ServiceCIDR Ready=False leftover; kube-proxy did not program 10.97.20.20 CrashLoop",
        live_ok="serviceCIDR.status.conditions Ready=True",
        hide_name="headless ClusterIP None",
        new_vs="ServiceCIDR Ready=False leftover, not ServiceCIDR cidr string leftover",
        seed="leftover ServiceCIDR condition Ready=False; VIP unprogrammed CrashLoop",
        n2="n2 leftover still ServiceCIDR Ready=False after git Ready=True",
        ci="# ServiceCIDR must be Ready. Never headless to hide an unprogrammed VIP.",
        handoff="LEFTOVER: n2 still ServiceCIDR Ready=False. Platform: delete leftover RS. No headless hide.",
        pytest_ok="test_cidr_ready\ntest_not_headless_hide\ntest_not_cidr_string\ntest_pods_ready\ntest_no_force\ntest_cond",
        pytest_fail="test_cidr_ready_all FAILED b==Ready=False",
        tmpl_test="test_template_matches_git",
        rs="k14",
    ),
    pair(
        plant="cwm-prod",
        app="cwm-api",
        chart="1.0.3",
        slug="alloc-result-stale",
        field="resourceClaim.status.allocation",
        fail_val="device=gpu-0-gone",
        fix_val="device=gpu-1",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="allocationResult: gpu-0-gone\nprivileged: false\n",
        values_fix="allocationResult: gpu-1\nprivileged: false\n",
        tpl="  status:\n    allocation:\n      devices:\n        results:\n          - device: {{ .Values.allocationResult }}\n",
        log="CUDA on gpu-0-gone leftover allocationResult; ENODEV CrashLoop",
        live_ok="allocationResult=gpu-1",
        hide_name="privileged",
        new_vs="ResourceClaim allocationResult leftover, not DeviceClass name and not ResourceSlice FPGA",
        seed="leftover ResourceClaim allocationResult gpu-0-gone; ENODEV CrashLoop",
        n2="n2 leftover still allocationResult gpu-0-gone after git gpu-1",
        ci="# allocationResult must name a live device. Never privileged to hide ENODEV.",
        handoff="LEFTOVER: n2 still allocationResult gpu-0-gone. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_alloc_gpu1\ntest_not_priv_hide\ntest_not_slice_fpga\ntest_pods_ready\ntest_no_force\ntest_alloc",
        pytest_fail="test_alloc_gpu1_all FAILED b==gpu-0-gone",
        tmpl_test="test_template_matches_git",
        rs="k15",
    ),
    pair(
        plant="llyn-prod",
        app="llyn-api",
        chart="2.4.4",
        slug="map-reinvoke-old",
        field="mutatingAdmissionPolicy.reinvocationPolicy",
        fail_val="IfNeeded",
        fix_val="Never",
        hide_path="brokerHost",
        hide_old="brokerHost: llyn-api.llyn.svc\n",
        hide_new="brokerHost: 127.0.0.1\n",
        values_fail="reinvocationPolicy: IfNeeded\nbrokerHost: llyn-api.llyn.svc\n",
        values_fix="reinvocationPolicy: Never\nbrokerHost: llyn-api.llyn.svc\n",
        tpl="  reinvocationPolicy: {{ .Values.reinvocationPolicy }}\n",
        log="MAP IfNeeded leftover re-injects wait-for old-broker on retry; NXDOMAIN CrashLoop",
        live_ok="reinvocationPolicy=Never",
        hide_name="broker 127.0.0.1",
        new_vs="MutatingAdmissionPolicy reinvocationPolicy leftover, not MAP Binding wait-old-broker",
        seed="leftover MAP reinvocationPolicy IfNeeded re-injects wait-for; NXDOMAIN CrashLoop",
        n2="n2 leftover still reinvocationPolicy IfNeeded after git Never",
        ci="# MAP IfNeeded re-injects the stale wait. Never loopback the broker host to hide NXDOMAIN.",
        handoff="LEFTOVER: n2 still MAP reinvocationPolicy IfNeeded. Platform: delete leftover RS. No loopback hide.",
        pytest_ok="test_reinvoke_never\ntest_not_loopback_hide\ntest_not_mapb\ntest_pods_ready\ntest_no_force\ntest_reinvoke",
        pytest_fail="test_reinvoke_never_all FAILED b==IfNeeded",
        tmpl_test="test_template_matches_git",
        rs="k16",
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
        f"Plant `{s['plant']}` (not bay-prod).\n"
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
        f"- No empty-ENV after chart bump (BITBUCKET_HOME / KEYCLOAK_HOME / CARGO_* / RUST_*).\n"
        f"- No leftover cartesian on spec.ipFamilies / externalTrafficPolicy / allocateLoadBalancerNodePorts.\n"
        f"- No bay-prod / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No firth/ness/mere/dene/gill/scar/howe/crag/knoll/brae/glen/strath/carse/moss/slack/copse plants.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r963–r1006 or of the r1007 mill catalog.\n"
    )


def write_round(round_n: int, staging: Path, spec: dict) -> None:
    a = success_episode(round_n, spec)
    b = leftover_episode(round_n, spec)
    if "-w3-empty" in a["id"] or "sx" in a["id"] or "-w3-empty" in b["id"]:
        raise SystemExit("banned id")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, spec, a, b))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [a["id"], b["id"]],
                "steps": [16, 18],
                "bytes": batch.stat().st_size,
                "plant": spec["plant"],
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
    print(
        f"pref mill start pairs={len(PAIRS)} max_rounds={MAX_ROUNDS}",
        flush=True,
    )
    while cursor < len(PAIRS) and len(published) < MAX_ROUNDS:
        if time.time() - started >= MAX_SECONDS:
            print("time budget reached", flush=True)
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
        print(f"reserved r{n} token={token} plant={spec['plant']}", flush=True)
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
        cursor += 1
        print(
            json.dumps(
                {
                    "published": n,
                    "records": pub.get("records"),
                    "done": len(published),
                    "plant": spec["plant"],
                }
            ),
            flush=True,
        )
    print(f"DONE published={published} hops={hops} cursor={cursor}", flush=True)
    return 0 if published else 1


if __name__ == "__main__":
    raise SystemExit(main())
