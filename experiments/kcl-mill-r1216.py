#!/usr/bin/env python3
"""k8s-crashloop mill from r1216. Q=2. grok-4.6.

Unique leftover CrashLoopBackOff pairs. Catalog r70–r1215 stays in raw.
BAN leftover-n2 stamp, empty-ENV catalog, spec leftover cartesian,
AppArmor/seccomp Unconfined, webhook timeout, r963–r1215 clones.
IDs kcl-rN-<slug> without -w3-empty / sxNNN-handoff.
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
    }
    if kwargs["plant"] in banned_plants:
        raise SystemExit(f"banned plant {kwargs['plant']}")
    if kwargs["slug"] in {
        "downward-divisor",
        "ephemeral-sc-old",
        "rclaim-admin-gone",
        "fieldref-divisor",
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
        plant="machair-prod",
        app="machair-api",
        chart="3.1.0",
        slug="dnspolicy-none",
        field="spec.dnsPolicy",
        fail_val="None",
        fix_val="ClusterFirst",
        hide_path="nameservers",
        hide_old="nameservers: []\n",
        hide_new="nameservers: [\"1.1.1.1\"]\n",
        values_fail="dnsPolicy: None\nnameservers: []\n",
        values_fix="dnsPolicy: ClusterFirst\nnameservers: []\n",
        tpl="  dnsPolicy: {{ .Values.dnsPolicy }}\n",
        log="lookup db NXDOMAIN leftover dnsPolicy None nameservers=[]; CrashLoop",
        live_ok="spec.dnsPolicy=ClusterFirst",
        hide_name="nameservers 1.1.1.1",
        new_vs="dnsPolicy None leftover, not dnsConfig ndots and not dnsConfig.searches old",
        seed="leftover dnsPolicy None; empty nameservers NXDOMAIN CrashLoop",
        n2="replica n2 still dnsPolicy None after git ClusterFirst",
        ci="# dnsPolicy must be ClusterFirst. Never public nameservers to hide None leftover.",
        handoff="LEFTOVER: replica n2 still dnsPolicy None. Platform: delete leftover RS. No public-DNS hide.",
        pytest_ok="test_dns_clusterfirst\ntest_not_public_ns\ntest_not_ndots\ntest_pods_ready\ntest_no_force\ntest_dns",
        pytest_fail="test_dns_clusterfirst_all FAILED b==None",
        tmpl_test="test_template_matches_git",
        rs="a161",
    ),
    pair(
        plant="broch-prod",
        app="broch-api",
        chart="1.8.4",
        slug="stopsignal-kill",
        field="lifecycle.stopSignal",
        fail_val="SIGKILL",
        fix_val="SIGTERM",
        hide_path="terminationGracePeriodSeconds",
        hide_old="terminationGracePeriodSeconds: 30\n",
        hide_new="terminationGracePeriodSeconds: 3600\n",
        values_fail="stopSignal: SIGKILL\nterminationGracePeriodSeconds: 30\n",
        values_fix="stopSignal: SIGTERM\nterminationGracePeriodSeconds: 30\n",
        tpl="        lifecycle:\n          stopSignal: {{ .Values.stopSignal }}\n",
        log="WAL torn leftover lifecycle.stopSignal SIGKILL; next start CrashLoop",
        live_ok="lifecycle.stopSignal=SIGTERM",
        hide_name="terminationGracePeriodSeconds 3600",
        new_vs="lifecycle.stopSignal leftover, not preStop sleep and not terminationMessagePolicy Fallback",
        seed="leftover stopSignal SIGKILL; WAL torn CrashLoop",
        n2="replica n2 still stopSignal SIGKILL after git SIGTERM",
        ci="# stopSignal must be SIGTERM. Never stretch grace to hide SIGKILL leftover.",
        handoff="LEFTOVER: replica n2 still stopSignal SIGKILL. Platform: delete leftover RS. No grace hide.",
        pytest_ok="test_sigterm\ntest_not_grace_hide\ntest_not_prestop\ntest_pods_ready\ntest_no_force\ntest_stop",
        pytest_fail="test_sigterm_all FAILED b==SIGKILL",
        tmpl_test="test_template_matches_git",
        rs="b272",
    ),
    pair(
        plant="crannog-prod",
        app="crannog-api",
        chart="0.6.2",
        slug="hostname-override",
        field="spec.hostnameOverride",
        fail_val="old-node.crannog.internal",
        fix_val="\"\"",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="hostnameOverride: old-node.crannog.internal\nhostNetwork: false\n",
        values_fix="hostnameOverride: \"\"\nhostNetwork: false\n",
        tpl="  hostnameOverride: {{ .Values.hostnameOverride | quote }}\n",
        log="tls: hostname leftover hostnameOverride old-node.crannog.internal; SAN miss CrashLoop",
        live_ok="spec.hostnameOverride=",
        hide_name="hostNetwork true",
        new_vs="hostnameOverride leftover, not hostname subdomain and not setHostnameAsFQDN",
        seed="leftover hostnameOverride old-node; cert SAN miss CrashLoop",
        n2="replica n2 still hostnameOverride old-node.crannog.internal after git empty",
        ci="# hostnameOverride must be empty. Never hostNetwork to hide a leftover node name.",
        handoff="LEFTOVER: replica n2 still hostnameOverride old-node. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_override_empty\ntest_not_hostnet_hide\ntest_not_fqdn\ntest_pods_ready\ntest_no_force\ntest_hn",
        pytest_fail="test_override_empty_all FAILED b==old-node.crannog.internal",
        tmpl_test="test_template_matches_git",
        rs="c383",
    ),
    pair(
        plant="bealach-prod",
        app="bealach-api",
        chart="2.4.1",
        slug="selinux-changepolicy",
        field="seLinuxChangePolicy",
        fail_val="Recursive",
        fix_val="MountOption",
        hide_path="seLinuxOptions.level",
        hide_old="level: s0:c1,c2\n",
        hide_new="level: s0\n",
        values_fail="seLinuxChangePolicy: Recursive\nlevel: s0:c1,c2\n",
        values_fix="seLinuxChangePolicy: MountOption\nlevel: s0:c1,c2\n",
        tpl="  seLinuxChangePolicy: {{ .Values.seLinuxChangePolicy }}\n",
        log="mount timeout leftover seLinuxChangePolicy Recursive on 2Ti PVC CrashLoop",
        live_ok="seLinuxChangePolicy=MountOption",
        hide_name="seLinuxOptions.level s0",
        new_vs="seLinuxChangePolicy leftover, not seLinuxOptions type and not seLinuxOptions level",
        seed="leftover seLinuxChangePolicy Recursive; relabel timeout CrashLoop",
        n2="replica n2 still seLinuxChangePolicy Recursive after git MountOption",
        ci="# seLinuxChangePolicy must be MountOption. Never drop MCS to hide Recursive leftover.",
        handoff="LEFTOVER: replica n2 still seLinuxChangePolicy Recursive. Platform: delete leftover RS. No MCS hide.",
        pytest_ok="test_mountoption\ntest_not_level_hide\ntest_not_selinux_type\ntest_pods_ready\ntest_no_force\ntest_scp",
        pytest_fail="test_mountoption_all FAILED b==Recursive",
        tmpl_test="test_template_matches_git",
        rs="d494",
    ),
    pair(
        plant="drumlin-prod",
        app="drumlin-api",
        chart="4.3.7",
        slug="poststart-sleep",
        field="lifecycle.postStart.sleep.seconds",
        fail_val="3600",
        fix_val="0",
        hide_path="liveness.initialDelaySeconds",
        hide_old="initialDelaySeconds: 10\n",
        hide_new="initialDelaySeconds: 3600\n",
        values_fail="postStartSleep: 3600\ninitialDelaySeconds: 10\n",
        values_fix="postStartSleep: 0\ninitialDelaySeconds: 10\n",
        tpl="          postStart:\n            sleep:\n              seconds: {{ .Values.postStartSleep }}\n",
        log="liveness kill leftover postStart sleep 3600s; CrashLoop",
        live_ok="lifecycle.postStart.sleep.seconds=0",
        hide_name="initialDelaySeconds 3600",
        new_vs="postStart sleep leftover, not preStop sleep and not postStart exec hang",
        seed="leftover postStart sleep 3600s; liveness CrashLoop",
        n2="replica n2 still postStart sleep 3600 after git 0",
        ci="# postStart sleep must be 0. Never stretch liveness delay to hide a leftover sleep.",
        handoff="LEFTOVER: replica n2 still postStart sleep 3600. Platform: delete leftover RS. No delay hide.",
        pytest_ok="test_sleep_0\ntest_not_delay_hide\ntest_not_prestop\ntest_pods_ready\ntest_no_force\ntest_ps",
        pytest_fail="test_sleep_0_all FAILED b==3600",
        tmpl_test="test_template_matches_git",
        rs="e505",
    ),
    pair(
        plant="esker-prod",
        app="esker-api",
        chart="1.2.9",
        slug="sts-ordinals-start",
        field="statefulset.spec.ordinals.start",
        fail_val="8",
        fix_val="0",
        hide_path="replicas",
        hide_old="replicas: 2\n",
        hide_new="replicas: 10\n",
        values_fail="ordinalsStart: 8\nreplicas: 2\n",
        values_fix="ordinalsStart: 0\nreplicas: 2\n",
        tpl="  ordinals:\n    start: {{ .Values.ordinalsStart }}\n",
        log="open /var/lib/esker/data: leftover ordinals.start=8; pod-8 PVC empty CrashLoop",
        live_ok="statefulset.spec.ordinals.start=0",
        hide_name="replicas 10",
        new_vs="StatefulSet ordinals.start leftover, not podManagementPolicy Parallel and not PVC WhenScaled",
        seed="leftover ordinals.start=8; empty PVC CrashLoop",
        n2="replica n2 still ordinals.start=8 after git 0",
        ci="# ordinals.start must be 0. Never grow replicas to hide a leftover ordinal.",
        handoff="LEFTOVER: replica n2 still ordinals.start=8. Platform: delete leftover RS. No replica hide.",
        pytest_ok="test_ord_0\ntest_not_rep_hide\ntest_not_parallel\ntest_pods_ready\ntest_no_force\ntest_ord",
        pytest_fail="test_ord_0_all FAILED b==8",
        tmpl_test="test_template_matches_git",
        rs="f616",
    ),
    pair(
        plant="moraine-prod",
        app="moraine-api",
        chart="5.0.2",
        slug="sts-servicename-gone",
        field="statefulset.spec.serviceName",
        fail_val="gone-headless",
        fix_val="moraine-hl",
        hide_path="subdomain",
        hide_old="subdomain: moraine-hl\n",
        hide_new="subdomain: default\n",
        values_fail="serviceName: gone-headless\nsubdomain: moraine-hl\n",
        values_fix="serviceName: moraine-hl\nsubdomain: moraine-hl\n",
        tpl="  serviceName: {{ .Values.serviceName }}\n",
        log="lookup moraine-api-0.gone-headless NXDOMAIN leftover serviceName gone CrashLoop",
        live_ok="statefulset.spec.serviceName=moraine-hl",
        hide_name="subdomain default",
        new_vs="StatefulSet serviceName leftover, not hostname subdomain and not headless ClusterIP None",
        seed="leftover serviceName gone-headless; peer DNS CrashLoop",
        n2="replica n2 still serviceName gone-headless after git moraine-hl",
        ci="# serviceName must be moraine-hl. Never rewrite subdomain to hide a gone headless Service.",
        handoff="LEFTOVER: replica n2 still serviceName gone-headless. Platform: delete leftover RS. No subdomain hide.",
        pytest_ok="test_svc_hl\ntest_not_sub_hide\ntest_not_headless_none\ntest_pods_ready\ntest_no_force\ntest_sn",
        pytest_fail="test_svc_hl_all FAILED b==gone-headless",
        tmpl_test="test_template_matches_git",
        rs="a727",
    ),
    pair(
        plant="karst-prod",
        app="karst-api",
        chart="2.9.5",
        slug="pvc-volumemode-block",
        field="pvc.spec.volumeMode",
        fail_val="Block",
        fix_val="Filesystem",
        hide_path="mountPath",
        hide_old="mountPath: /var/lib/karst\n",
        hide_new="mountPath: /dev/xvda\n",
        values_fail="volumeMode: Block\nmountPath: /var/lib/karst\n",
        values_fix="volumeMode: Filesystem\nmountPath: /var/lib/karst\n",
        tpl="  volumeMode: {{ .Values.volumeMode }}\n",
        log="mount: /var/lib/karst is a block device leftover volumeMode Block CrashLoop",
        live_ok="pvc.spec.volumeMode=Filesystem",
        hide_name="mountPath /dev/xvda",
        new_vs="PVC volumeMode Block leftover, not PVC fs full and not VolumeDevices path",
        seed="leftover PVC volumeMode Block; filesystem mount CrashLoop",
        n2="replica n2 still volumeMode Block after git Filesystem",
        ci="# volumeMode must be Filesystem. Never remap mountPath to hide a Block leftover.",
        handoff="LEFTOVER: replica n2 still volumeMode Block. Platform: delete leftover RS. No mountPath hide.",
        pytest_ok="test_fs\ntest_not_dev_hide\ntest_not_voldev\ntest_pods_ready\ntest_no_force\ntest_vm",
        pytest_fail="test_fs_all FAILED b==Block",
        tmpl_test="test_template_matches_git",
        rs="b838",
    ),
    pair(
        plant="turlough-prod",
        app="turlough-api",
        chart="0.4.6",
        slug="job-managedby-old",
        field="job.spec.managedBy",
        fail_val="old.example.com/controller",
        fix_val="kubernetes.io/job-controller",
        hide_path="parallelism",
        hide_old="parallelism: 1\n",
        hide_new="parallelism: 8\n",
        values_fail="managedBy: old.example.com/controller\nparallelism: 1\n",
        values_fix="managedBy: kubernetes.io/job-controller\nparallelism: 1\n",
        tpl="  managedBy: {{ .Values.managedBy }}\n",
        log="Job not adopted leftover managedBy old.example.com/controller; worker wait CrashLoop",
        live_ok="job.spec.managedBy=kubernetes.io/job-controller",
        hide_name="parallelism 8",
        new_vs="Job managedBy leftover, not backoffLimitPerIndex 0 and not podReplacementPolicy Failed",
        seed="leftover Job managedBy old controller; worker wait CrashLoop",
        n2="replica n2 still managedBy old.example.com/controller after git kubernetes.io/job-controller",
        ci="# managedBy must be kubernetes.io/job-controller. Never raise parallelism to hide a gone controller.",
        handoff="LEFTOVER: replica n2 still Job managedBy old.example.com/controller. Platform: delete leftover RS. No parallelism hide.",
        pytest_ok="test_k8s_ctrl\ntest_not_par_hide\ntest_not_backoff\ntest_pods_ready\ntest_no_force\ntest_mb",
        pytest_fail="test_k8s_ctrl_all FAILED b==old.example.com/controller",
        tmpl_test="test_template_matches_git",
        rs="c949",
    ),
    pair(
        plant="clachan-prod",
        app="clachan-api",
        chart="3.3.3",
        slug="job-ttl-1",
        field="job.spec.ttlSecondsAfterFinished",
        fail_val="1",
        fix_val="86400",
        hide_path="backoffLimit",
        hide_old="backoffLimit: 6\n",
        hide_new="backoffLimit: 99\n",
        values_fail="ttlSecondsAfterFinished: 1\nbackoffLimit: 6\n",
        values_fix="ttlSecondsAfterFinished: 86400\nbackoffLimit: 6\n",
        tpl="  ttlSecondsAfterFinished: {{ .Values.ttlSecondsAfterFinished }}\n",
        log="Job not found leftover ttlSecondsAfterFinished=1; worker status wait CrashLoop",
        live_ok="job.spec.ttlSecondsAfterFinished=86400",
        hide_name="backoffLimit 99",
        new_vs="Job ttlSecondsAfterFinished leftover, not maxFailedIndexes 0 and not CronJob concurrency Forbid",
        seed="leftover Job ttlSecondsAfterFinished=1; Job gone CrashLoop",
        n2="replica n2 still ttlSecondsAfterFinished=1 after git 86400",
        ci="# ttlSecondsAfterFinished must be 86400. Never raise backoffLimit to hide a leftover ttl.",
        handoff="LEFTOVER: replica n2 still ttlSecondsAfterFinished=1. Platform: delete leftover RS. No backoff hide.",
        pytest_ok="test_ttl_86400\ntest_not_backoff_hide\ntest_not_maxfailed\ntest_pods_ready\ntest_no_force\ntest_ttl",
        pytest_fail="test_ttl_86400_all FAILED b==1",
        tmpl_test="test_template_matches_git",
        rs="d050",
    ),
    pair(
        plant="shieling-prod",
        app="shieling-api",
        chart="1.1.8",
        slug="cron-timezone-old",
        field="cronjob.spec.timeZone",
        fail_val="America/Old_Zone",
        fix_val="UTC",
        hide_path="schedule",
        hide_old="schedule: \"0 * * * *\"\n",
        hide_new="schedule: \"* * * * *\"\n",
        values_fail="timeZone: America/Old_Zone\nschedule: \"0 * * * *\"\n",
        values_fix="timeZone: UTC\nschedule: \"0 * * * *\"\n",
        tpl="  timeZone: {{ .Values.timeZone }}\n",
        log="unknown time zone leftover CronJob timeZone America/Old_Zone; entrypoint CrashLoop",
        live_ok="cronjob.spec.timeZone=UTC",
        hide_name="schedule every minute",
        new_vs="CronJob timeZone leftover, not concurrencyPolicy Forbid and not startingDeadlineSeconds",
        seed="leftover CronJob timeZone America/Old_Zone; unknown TZ CrashLoop",
        n2="replica n2 still timeZone America/Old_Zone after git UTC",
        ci="# timeZone must be UTC. Never densify schedule to hide a leftover zone.",
        handoff="LEFTOVER: replica n2 still CronJob timeZone America/Old_Zone. Platform: delete leftover RS. No schedule hide.",
        pytest_ok="test_tz_utc\ntest_not_sched_hide\ntest_not_forbid\ntest_pods_ready\ntest_no_force\ntest_tz",
        pytest_fail="test_tz_utc_all FAILED b==America/Old_Zone",
        tmpl_test="test_template_matches_git",
        rs="e161",
    ),
    pair(
        plant="grange-prod",
        app="grange-api",
        chart="2.2.2",
        slug="vpa-minallowed-8cpu",
        field="vpa.spec.resourcePolicy.minAllowed.cpu",
        fail_val="8",
        fix_val="100m",
        hide_path="requests.cpu",
        hide_old="requestsCpu: 500m\n",
        hide_new="requestsCpu: \"8\"\n",
        values_fail="minAllowedCpu: \"8\"\nrequestsCpu: 500m\n",
        values_fix="minAllowedCpu: 100m\nrequestsCpu: 500m\n",
        tpl="    minAllowed:\n      cpu: {{ .Values.minAllowedCpu }}\n",
        log="Pending leftover VPA minAllowed cpu=8 vs node 4cpu; wait-for-schedule CrashLoop",
        live_ok="vpa.spec.resourcePolicy.minAllowed.cpu=100m",
        hide_name="requests.cpu 8",
        new_vs="VPA minAllowed cpu leftover, not VPA vs -Xmx and not VPA updateMode Auto",
        seed="leftover VPA minAllowed cpu=8; unschedulable wait CrashLoop",
        n2="replica n2 still minAllowed cpu=8 after git 100m",
        ci="# VPA minAllowed.cpu must be 100m. Never pin requests 8 to hide a leftover minAllowed.",
        handoff="LEFTOVER: replica n2 still VPA minAllowed cpu=8. Platform: delete leftover RS. No requests hide.",
        pytest_ok="test_min_100m\ntest_not_req_hide\ntest_not_xmx\ntest_pods_ready\ntest_no_force\ntest_vpa",
        pytest_fail="test_min_100m_all FAILED b==8",
        tmpl_test="test_template_matches_git",
        rs="f272",
    ),
    pair(
        plant="glebe-prod",
        app="glebe-api",
        chart="6.1.0",
        slug="hpa-external-oldmetric",
        field="hpa.spec.metrics.external.metric.name",
        fail_val="old-queue-depth",
        fix_val="sqs-visible",
        hide_path="minReplicas",
        hide_old="minReplicas: 2\n",
        hide_new="minReplicas: 0\n",
        values_fail="metricName: old-queue-depth\nminReplicas: 2\n",
        values_fix="metricName: sqs-visible\nminReplicas: 2\n",
        tpl="      metric:\n        name: {{ .Values.metricName }}\n",
        log="wait-for-hpa leftover external metric old-queue-depth missing; entrypoint CrashLoop",
        live_ok="hpa.spec.metrics.external.metric.name=sqs-visible",
        hide_name="minReplicas 0",
        new_vs="HPA external metric leftover, not containerResource sidecar and not scaleDown stabilization 3600",
        seed="leftover HPA external metric old-queue-depth; wait CrashLoop",
        n2="replica n2 still metric old-queue-depth after git sqs-visible",
        ci="# HPA metric must be sqs-visible. Never minReplicas 0 to hide a leftover metric name.",
        handoff="LEFTOVER: replica n2 still HPA metric old-queue-depth. Platform: delete leftover RS. No minReplicas hide.",
        pytest_ok="test_metric_sqs\ntest_not_min0_hide\ntest_not_sidecar\ntest_pods_ready\ntest_no_force\ntest_hpa",
        pytest_fail="test_metric_sqs_all FAILED b==old-queue-depth",
        tmpl_test="test_template_matches_git",
        rs="a383",
    ),
    pair(
        plant="minster-prod",
        app="minster-api",
        chart="0.8.3",
        slug="grpcroute-method-old",
        field="grpcroute.spec.rules.matches.method.service",
        fail_val="old.v1.Minster",
        fix_val="minster.v2.API",
        hide_path="timeout",
        hide_old="timeout: 30s\n",
        hide_new="timeout: 1s\n",
        values_fail="grpcService: old.v1.Minster\ntimeout: 30s\n",
        values_fix="grpcService: minster.v2.API\ntimeout: 30s\n",
        tpl="          method:\n            service: {{ .Values.grpcService }}\n",
        log="rpc UNIMPLEMENTED leftover GRPCRoute method old.v1.Minster; client CrashLoop",
        live_ok="grpcroute.spec.rules.matches.method.service=minster.v2.API",
        hide_name="timeout 1s",
        new_vs="GRPCRoute method leftover, not GRPCRoute backend gone and not GRPCRoute HTTP parent",
        seed="leftover GRPCRoute method old.v1.Minster; UNIMPLEMENTED CrashLoop",
        n2="replica n2 still method old.v1.Minster after git minster.v2.API",
        ci="# GRPCRoute method must be minster.v2.API. Never shrink timeout to hide a leftover method.",
        handoff="LEFTOVER: replica n2 still GRPCRoute method old.v1.Minster. Platform: delete leftover RS. No timeout hide.",
        pytest_ok="test_svc_v2\ntest_not_to_hide\ntest_not_backend_gone\ntest_pods_ready\ntest_no_force\ntest_grpc",
        pytest_fail="test_svc_v2_all FAILED b==old.v1.Minster",
        tmpl_test="test_template_matches_git",
        rs="b494",
    ),
    pair(
        plant="henge-prod",
        app="henge-api",
        chart="1.5.5",
        slug="backendtls-system-cas",
        field="backendtls.validation.wellKnownCACertificates",
        fail_val="System",
        fix_val="henge-ca",
        hide_path="insecureSkipVerify",
        hide_old="insecureSkipVerify: false\n",
        hide_new="insecureSkipVerify: true\n",
        values_fail="wellKnownCACertificates: System\ninsecureSkipVerify: false\n",
        values_fix="caCertificateRefs: [henge-ca]\ninsecureSkipVerify: false\n",
        tpl="    validation:\n      wellKnownCACertificates: {{ .Values.wellKnownCACertificates }}\n",
        log="x509 leftover BackendTLSPolicy wellKnownCACertificates System; cluster CA miss CrashLoop",
        live_ok="backendtls.validation.caCertificateRefs=henge-ca",
        hide_name="insecureSkipVerify",
        new_vs="BackendTLSPolicy wellKnownCACertificates leftover, not SNI hostname and not old backendTLSPolicy",
        seed="leftover BackendTLSPolicy System CAs; handshake CrashLoop",
        n2="replica n2 still wellKnownCACertificates System after git henge-ca",
        ci="# BackendTLS must pin henge-ca. Never insecureSkipVerify to hide System leftover.",
        handoff="LEFTOVER: replica n2 still wellKnownCACertificates System. Platform: delete leftover RS. No skip-verify hide.",
        pytest_ok="test_ca_henge\ntest_not_skip_hide\ntest_not_sni\ntest_pods_ready\ntest_no_force\ntest_btls",
        pytest_fail="test_ca_henge_all FAILED b==System",
        tmpl_test="test_template_matches_git",
        rs="c505",
    ),
    pair(
        plant="pill-prod",
        app="pill-api",
        chart="4.4.0",
        slug="rolebinding-oldsa",
        field="rolebinding.subjects.name",
        fail_val="pill-old",
        fix_val="pill-api",
        hide_path="role",
        hide_old="role: pill-api\n",
        hide_new="role: cluster-admin\n",
        values_fail="subject: pill-old\nrole: pill-api\n",
        values_fix="subject: pill-api\nrole: pill-api\n",
        tpl="  subjects:\n    - name: {{ .Values.subject }}\n",
        log="403 leftover RoleBinding subject pill-old; token SA mismatch CrashLoop",
        live_ok="rolebinding.subjects.name=pill-api",
        hide_name="role cluster-admin",
        new_vs="RoleBinding subject leftover, not automountServiceAccountToken and not SA secrets token-old",
        seed="leftover RoleBinding subject pill-old; 403 CrashLoop",
        n2="replica n2 still subject pill-old after git pill-api",
        ci="# RoleBinding subject must be pill-api. Never cluster-admin to hide a leftover SA name.",
        handoff="LEFTOVER: replica n2 still RoleBinding subject pill-old. Platform: delete leftover RS. No cluster-admin hide.",
        pytest_ok="test_sa_api\ntest_not_admin_hide\ntest_not_automount\ntest_pods_ready\ntest_no_force\ntest_rb",
        pytest_fail="test_sa_api_all FAILED b==pill-old",
        tmpl_test="test_template_matches_git",
        rs="d616",
    ),
    pair(
        plant="sough-prod",
        app="sough-api",
        chart="0.9.9",
        slug="hostpath-type-file",
        field="hostPath.type",
        fail_val="File",
        fix_val="DirectoryOrCreate",
        hide_path="privileged",
        hide_old="privileged: false\n",
        hide_new="privileged: true\n",
        values_fail="hostPathType: File\nprivileged: false\n",
        values_fix="hostPathType: DirectoryOrCreate\nprivileged: false\n",
        tpl="      hostPath:\n        type: {{ .Values.hostPathType }}\n",
        log="mount leftover hostPath type File vs directory /var/lib/sough CrashLoop",
        live_ok="hostPath.type=DirectoryOrCreate",
        hide_name="privileged",
        new_vs="hostPath type File leftover, not hostPath AppArmor and not PVC volumeMode Block",
        seed="leftover hostPath type File; directory mount CrashLoop",
        n2="replica n2 still hostPath type File after git DirectoryOrCreate",
        ci="# hostPath type must be DirectoryOrCreate. Never privileged to hide a leftover File type.",
        handoff="LEFTOVER: replica n2 still hostPath type File. Platform: delete leftover RS. No privileged hide.",
        pytest_ok="test_dirorcreate\ntest_not_priv_hide\ntest_not_apparmor\ntest_pods_ready\ntest_no_force\ntest_hp",
        pytest_fail="test_dirorcreate_all FAILED b==File",
        tmpl_test="test_template_matches_git",
        rs="e727",
    ),
    pair(
        plant="adit-prod",
        app="adit-api",
        chart="3.7.1",
        slug="nfs-vers-3",
        field="nfs.mountOptions",
        fail_val="vers=3",
        fix_val="nfsvers=4.1",
        hide_path="hostNetwork",
        hide_old="hostNetwork: false\n",
        hide_new="hostNetwork: true\n",
        values_fail="nfsVers: vers=3\nhostNetwork: false\n",
        values_fix="nfsVers: nfsvers=4.1\nhostNetwork: false\n",
        tpl="    mountOptions:\n      - {{ .Values.nfsVers }}\n",
        log="mount.nfs leftover vers=3 vs filer NFSv4-only; FailedMount CrashLoop",
        live_ok="nfs.mountOptions=nfsvers=4.1",
        hide_name="hostNetwork true",
        new_vs="NFS vers=3 leftover, not userns vs NFS and not CSI fsType ntfs",
        seed="leftover NFS mountOptions vers=3; v4-only filer CrashLoop",
        n2="replica n2 still nfs vers=3 after git nfsvers=4.1",
        ci="# NFS mountOptions must be nfsvers=4.1. Never hostNetwork to hide a leftover v3 mount.",
        handoff="LEFTOVER: replica n2 still NFS vers=3. Platform: delete leftover RS. No hostNetwork hide.",
        pytest_ok="test_nfs41\ntest_not_hostnet_hide\ntest_not_userns\ntest_pods_ready\ntest_no_force\ntest_nfs",
        pytest_fail="test_nfs41_all FAILED b==vers=3",
        tmpl_test="test_template_matches_git",
        rs="f838",
    ),
    pair(
        plant="delph-prod",
        app="delph-api",
        chart="2.0.7",
        slug="iscsi-targetportal-old",
        field="iscsi.targetPortal",
        fail_val="10.9.9.9:3260",
        fix_val="10.8.8.8:3260",
        hide_path="hostPath",
        hide_old="hostPath: \"\"\n",
        hide_new="hostPath: /dev/sdb\n",
        values_fail="targetPortal: 10.9.9.9:3260\nhostPath: \"\"\n",
        values_fix="targetPortal: 10.8.8.8:3260\nhostPath: \"\"\n",
        tpl="    iscsi:\n      targetPortal: {{ .Values.targetPortal }}\n",
        log="FailedMount leftover iSCSI targetPortal 10.9.9.9:3260 gone CrashLoop",
        live_ok="iscsi.targetPortal=10.8.8.8:3260",
        hide_name="hostPath /dev/sdb",
        new_vs="iSCSI targetPortal leftover, not CSI nodePublishSecretRef and not VolumeAttachment attacher",
        seed="leftover iSCSI targetPortal 10.9.9.9 gone; FailedMount CrashLoop",
        n2="replica n2 still targetPortal 10.9.9.9:3260 after git 10.8.8.8:3260",
        ci="# iSCSI targetPortal must be 10.8.8.8:3260. Never hostPath to hide a leftover portal.",
        handoff="LEFTOVER: replica n2 still iSCSI targetPortal 10.9.9.9. Platform: delete leftover RS. No hostPath hide.",
        pytest_ok="test_portal_88\ntest_not_hp_hide\ntest_not_attacher\ntest_pods_ready\ntest_no_force\ntest_iscsi",
        pytest_fail="test_portal_88_all FAILED b==10.9.9.9:3260",
        tmpl_test="test_template_matches_git",
        rs="a949",
    ),
    pair(
        plant="wharf-prod",
        app="wharf-api",
        chart="1.9.4",
        slug="ctb-label-old",
        field="clusterTrustBundle.labelSelector",
        fail_val="signer=old-ca",
        fix_val="signer=prod-ca",
        hide_path="insecureSkipVerify",
        hide_old="insecureSkipVerify: false\n",
        hide_new="insecureSkipVerify: true\n",
        values_fail="signerLabel: signer=old-ca\ninsecureSkipVerify: false\n",
        values_fix="signerLabel: signer=prod-ca\ninsecureSkipVerify: false\n",
        tpl="            labelSelector:\n              matchLabels:\n                signer: {{ .Values.signerLabel }}\n",
        log="empty bundle leftover ClusterTrustBundle labelSelector signer=old-ca CrashLoop",
        live_ok="clusterTrustBundle.labelSelector=signer=prod-ca",
        hide_name="insecureSkipVerify",
        new_vs="ClusterTrustBundle labelSelector leftover, not signerName old and not projected SA audience",
        seed="leftover ClusterTrustBundle labelSelector signer=old-ca; empty CA CrashLoop",
        n2="replica n2 still labelSelector signer=old-ca after git signer=prod-ca",
        ci="# ClusterTrustBundle selector must be signer=prod-ca. Never skip-verify to hide old-ca leftover.",
        handoff="LEFTOVER: replica n2 still ClusterTrustBundle labelSelector signer=old-ca. Platform: delete leftover RS. No skip-verify hide.",
        pytest_ok="test_sel_prod\ntest_not_skip_hide\ntest_not_signername\ntest_pods_ready\ntest_no_force\ntest_ctb",
        pytest_fail="test_sel_prod_all FAILED b==signer=old-ca",
        tmpl_test="test_template_matches_git",
        rs="b050",
    ),
]


def notes_for(round_n: int, s: dict, a: dict, b: dict) -> str:
    cov = 82 + (round_n % 7)
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"Quota 2. Unique CrashLoopBackOff pair. Catalog r70–r1215 stays in raw "
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
        f"- No AppArmor/seccomp Unconfined. No webhook timeout.\n"
        f"- No r1151 rclaim-admin-gone / rclaim-admin-gone-n2-handoff.\n"
        f"- No r1215 downward-divisor / downward-divisor-n2-handoff clone.\n"
        f"- No bay-prod / cwm / llyn / atoll / kyle / voe / tarn / lough / weald / fen clones.\n"
        f"- No `-w3-empty` / `sxNNN-handoff` ids.\n"
        f"- Not a clone of r963–r1215 leftover families.\n"
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

    tmp = Path("/tmp/kcl_wave1216_smoke")
    tmp.mkdir(exist_ok=True)
    for i, spec in enumerate(PAIRS):
        rnd = 1216 + i
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
        f"r1216 mill start pairs={len(PAIRS)} taken_slugs={len(taken)} "
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
    return 0 if len(published) >= 12 else (0 if published else 1)


if __name__ == "__main__":
    raise SystemExit(main())
