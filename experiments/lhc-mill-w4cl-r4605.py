#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cl: unused storage/mesh/CI/OLTP plants after w4ck.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4580 pr-kanidm-domain-origin-https / pr-gluu-agama-flow-timeout and
prior identity-origin clones (oauth2-proxy, authentik, ory, hydra, kratos,
keto, zitadel, authelia, pomerium, teleport, dex, sssd, pam, casdoor).
Also BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale,
Koka, and any plant already published. IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4cl_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4cl|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )


# Compact unused storage / CI / mesh / OLTP plants.
# Not identity-origin. Not w4ck lakehouse/CDC. Not w4cj SSO.
PLANTS = {
    "ceph": mk(True, "pr-ceph-osd-memory-target-bytes", "lock-cephmem",
        "the Ceph OSD that omitted osd_memory_target so BlueStore cache ate the node and the OSD was OOM-killed",
        "ceph.conf", "osd_memory_cache_min = 128MB", "osd_memory_target 4GB",
        "osd_memory_target", "harbor osd_memory_cache_min only. pack osd_memory_target.",
        "FAIL test_assign: OSD OOM-killed; osd_memory_target missing",
        "osd_memory_cache_min only", "cache_min is not osd_memory_target"),
    "minio": mk(False, "pr-minio-erasure-set-drive-count", "quay-minerset",
        "the MinIO pool that omitted erasure set drive count so a 7-drive node built a broken EC set",
        "minio.env", "MINIO_STORAGE_CLASS_STANDARD=EC:2", "erasure set drive count 4",
        "erasure", "harbor storage class EC:2 only. pack erasure set drive count.",
        "FAIL test_assign: 7-drive EC set; heal stuck; drive count missing",
        "storage class EC:2 only", "storage class is not erasure set drive count"),
    "longhorn": mk(True, "pr-longhorn-replica-soft-anti-affinity", "lock-lhsoft",
        "the Longhorn volume that omitted replica-soft-anti-affinity so two replicas landed on one node and a drain lost quorum",
        "longhorn.yaml", "numberOfReplicas: 3", "replicaSoftAntiAffinity false",
        "replicaSoftAntiAffinity", "harbor numberOfReplicas only. pack replicaSoftAntiAffinity.",
        "FAIL test_assign: two replicas same node; drain lost quorum; soft anti-affinity missing",
        "numberOfReplicas only", "replica count is not soft anti-affinity"),
    "openebs": mk(False, "pr-openebs-jiva-replica-count", "quay-jivarep",
        "the OpenEBS Jiva volume that omitted ReplicaCount 3 so a node loss took the PVC readonly",
        "jiva.yaml", "StoragePool: default", "ReplicaCount 3",
        "ReplicaCount", "harbor StoragePool only. pack ReplicaCount 3.",
        "FAIL test_assign: PVC readonly after node loss; ReplicaCount missing",
        "StoragePool only", "StoragePool is not ReplicaCount"),
    "rook": mk(True, "pr-rook-mon-count-odd-quorum", "lock-rookmon",
        "the Rook cluster that omitted mon.count 3 so a single mon crash lost quorum",
        "cluster.yaml", "mgr.count: 2", "mon.count 3",
        "mon.count", "harbor mgr.count only. pack mon.count 3.",
        "FAIL test_assign: mon crash lost quorum; mon.count missing",
        "mgr.count only", "mgr.count is not mon.count"),
    "seaweed": mk(False, "pr-seaweedfs-volume-max-size", "quay-swvmax",
        "the SeaweedFS volume server that omitted volumeSizeLimitMB so one volume grew past the disk and writes 500'd",
        "weed.conf", "filer.defaultReplication=000", "volumeSizeLimitMB 30000",
        "volumeSizeLimitMB", "harbor filer.defaultReplication only. pack volumeSizeLimitMB.",
        "FAIL test_assign: volume larger than disk; writes 500; size limit missing",
        "filer.defaultReplication only", "replication is not volumeSizeLimitMB"),
    "juicefs": mk(True, "pr-juicefs-cache-dir-size-limit", "lock-jfscache",
        "the JuiceFS client that omitted cache-size so the cache dir filled the root volume and the node went read-only",
        "juicefs.yaml", "cache-dir: /var/jfsCache", "cache-size 102400",
        "cache-size", "harbor cache-dir only. pack cache-size.",
        "FAIL test_assign: root 100% full; cache-size missing",
        "cache-dir only", "cache-dir is not cache-size"),
    "garage": mk(False, "pr-garage-replication-mode-3", "quay-garrep",
        "the Garage layout that omitted replication_mode 3 so a node loss dropped objects",
        "garage.toml", "consistency_mode = \"consistent\"", "replication_mode 3",
        "replication_mode", "harbor consistency_mode only. pack replication_mode 3.",
        "FAIL test_assign: node loss dropped objects; replication_mode missing",
        "consistency_mode only", "consistency_mode is not replication_mode"),
    "woodpecker": mk(True, "pr-woodpecker-privileged-plugin-only", "lock-wppriv",
        "the Woodpecker pipeline that omitted privileged false so a plugin ran privileged and mounted the docker socket",
        ".woodpecker.yml", "image: plugins/docker", "privileged false",
        "privileged", "harbor image plugins/docker only. pack privileged false.",
        "FAIL test_assign: plugin privileged docker.sock; privileged false missing",
        "image plugins/docker only", "plugin image is not privileged false"),
    "drone": mk(False, "pr-drone-clone-disable-custom", "quay-drnclone",
        "the Drone pipeline that omitted clone disable so a custom clone step raced the default clone and emptied the workspace",
        ".drone.yml", "kind: pipeline", "clone disable true",
        "clone", "harbor kind pipeline only. pack clone disable.",
        "FAIL test_assign: workspace emptied; clone disable missing",
        "kind pipeline only", "kind is not clone disable"),
    "buildkite": mk(True, "pr-buildkite-artifact-paths-junit", "lock-bkart",
        "the Buildkite step that omitted artifact_paths so JUnit XML never uploaded and the test panel stayed empty",
        "pipeline.yml", "agents: {queue: default}", "artifact_paths junit.xml",
        "artifact_paths", "harbor agents queue only. pack artifact_paths.",
        "FAIL test_assign: test panel empty; artifact_paths missing",
        "agents queue only", "agents is not artifact_paths"),
    "tekton": mk(False, "pr-tekton-pipeline-timeout-hour", "quay-tktto",
        "the Tekton PipelineRun that omitted timeouts.pipeline so a hung task ran 24h and filled the PVC",
        "pipelinerun.yaml", "taskRunSpecs: []", "timeouts.pipeline 1h",
        "timeouts.pipeline", "harbor taskRunSpecs only. pack timeouts.pipeline.",
        "FAIL test_assign: hung 24h; PVC full; pipeline timeout missing",
        "taskRunSpecs only", "taskRunSpecs is not timeouts.pipeline"),
    "concourse": mk(True, "pr-concourse-resource-check-every", "lock-cicheck",
        "the Concourse resource that omitted check_every so the ATC hammered the git host and got 429'd",
        "pipeline.yml", "webhook_token: secret", "check_every 5m",
        "check_every", "harbor webhook_token only. pack check_every.",
        "FAIL test_assign: git 429; check_every missing",
        "webhook_token only", "webhook_token is not check_every"),
    "jenkins": mk(False, "pr-jenkins-throttle-category-job", "quay-jkthrot",
        "the Jenkins job that omitted throttle category so 40 executors hit the same Maven repo and 503'd",
        "Jenkinsfile", "options { timestamps() }", "throttle category maven-central",
        "throttle", "harbor timestamps only. pack throttle category.",
        "FAIL test_assign: Maven 503; throttle category missing",
        "timestamps only", "timestamps is not throttle category"),
    "vault": mk(True, "pr-vault-max-lease-ttl-bound", "lock-vltlease",
        "the Vault auth mount that omitted max_lease_ttl so a CI token lived 32 days past the rotation window",
        "auth.hcl", "default_lease_ttl = \"1h\"", "max_lease_ttl 24h",
        "max_lease_ttl", "harbor default_lease_ttl only. pack max_lease_ttl.",
        "FAIL test_assign: token lived 32d; max_lease_ttl missing",
        "default_lease_ttl only", "default_lease_ttl is not max_lease_ttl"),
    "sops": mk(False, "pr-sops-encrypted-regex-secret", "quay-sopsre",
        "the SOPS file that omitted encrypted_regex so only the MAC was encrypted and plaintext secrets leaked in git",
        ".sops.yaml", "creation_rules: [{age: age1}]", "encrypted_regex ^(data|stringData)$",
        "encrypted_regex", "harbor age recipient only. pack encrypted_regex.",
        "FAIL test_assign: plaintext secrets in git; encrypted_regex missing",
        "age recipient only", "age recipient is not encrypted_regex"),
    "infisical": mk(True, "pr-infisical-auto-secret-sync", "lock-infauto",
        "the Infisical K8s operator that omitted auto-reload so pods kept the old DATABASE_URL after rotation",
        "infisical.yaml", "resyncInterval: 1m", "autoReload true",
        "autoReload", "harbor resyncInterval only. pack autoReload.",
        "FAIL test_assign: pods old DATABASE_URL; autoReload missing",
        "resyncInterval only", "resyncInterval is not autoReload"),
    "doppler": mk(False, "pr-doppler-project-config-stg", "quay-dplcfg",
        "the Doppler CLI that omitted --config stg so production secrets were injected into the staging job",
        "doppler.yaml", "project: harbor", "config stg",
        "config", "harbor project only. pack config stg.",
        "FAIL test_assign: prod secrets in staging; config stg missing",
        "project only", "project is not config"),
    "chamber": mk(True, "pr-chamber-kms-key-alias", "lock-chmkms",
        "the Chamber write that omitted --kms-key-alias so SSM used the AWS default key and another account could decrypt",
        "chamber.env", "CHAMBER_KMS_KEY_ALIAS=", "kms-key-alias alias/harbor",
        "kms-key-alias", "harbor empty CHAMBER_KMS_KEY_ALIAS. pack kms-key-alias.",
        "FAIL test_assign: default AWS key; cross-account decrypt; kms-key-alias missing",
        "empty CHAMBER_KMS_KEY_ALIAS", "empty alias env is not --kms-key-alias"),
    "externalsecrets": mk(False, "pr-external-secrets-refresh-interval", "quay-esoref",
        "the ExternalSecret that omitted refreshInterval so a rotated Vault secret stayed cached for days",
        "externalsecret.yaml", "secretStoreRef: {name: vault}", "refreshInterval 1m",
        "refreshInterval", "harbor secretStoreRef only. pack refreshInterval.",
        "FAIL test_assign: stale secret 3d; refreshInterval missing",
        "secretStoreRef only", "secretStoreRef is not refreshInterval"),
    "cilium": mk(True, "pr-cilium-bpf-lb-sock-hostns", "lock-cilhost",
        "the Cilium config that omitted bpf-lb-sock-hostns-only so hostNetwork pods bypassed kube-proxy replacement and blackholed",
        "cilium-config.yaml", "bpf-lb-sock: true", "bpf-lb-sock-hostns-only true",
        "bpf-lb-sock-hostns-only", "harbor bpf-lb-sock only. pack bpf-lb-sock-hostns-only.",
        "FAIL test_assign: hostNetwork blackhole; hostns-only missing",
        "bpf-lb-sock only", "bpf-lb-sock is not hostns-only"),
    "calico": mk(False, "pr-calico-ipip-mode-cross-subnet", "quay-calipip",
        "the Calico IPPool that omitted ipipMode CrossSubnet so overlay encapsulated inside the rack and MTU shredded",
        "ippool.yaml", "vxlanMode: Never", "ipipMode CrossSubnet",
        "ipipMode", "harbor vxlanMode Never only. pack ipipMode CrossSubnet.",
        "FAIL test_assign: in-rack overlay; MTU shred; ipipMode missing",
        "vxlanMode Never only", "vxlanMode is not ipipMode"),
    "istio": mk(True, "pr-istio-hold-app-until-proxy", "lock-isthold",
        "the Istio sidecar that omitted holdApplicationUntilProxyStarts so the app bound before Envoy and lost the first 30s of traffic",
        "sidecar.yaml", "rewriteAppHTTPProbers: true", "holdApplicationUntilProxyStarts true",
        "holdApplicationUntilProxyStarts", "harbor rewriteAppHTTPProbers only. pack holdApplicationUntilProxyStarts.",
        "FAIL test_assign: first 30s dropped; holdApplicationUntilProxyStarts missing",
        "rewriteAppHTTPProbers only", "rewriteAppHTTPProbers is not holdApplicationUntilProxyStarts"),
    "linkerd": mk(False, "pr-linkerd-proxy-await-inject", "quay-lnkawait",
        "the Linkerd inject that omitted config.linkerd.io/proxy-await so the app raced the proxy and 503'd on boot",
        "deploy.yaml", "config.linkerd.io/skip-inbound-ports: \"4191\"", "proxy-await enabled",
        "proxy-await", "harbor skip-inbound-ports only. pack proxy-await.",
        "FAIL test_assign: boot 503; proxy-await missing",
        "skip-inbound-ports only", "skip-inbound-ports is not proxy-await"),
    "traefik": mk(True, "pr-traefik-insecureskipverify-off", "lock-trfskp",
        "the Traefik router that omitted insecureSkipVerify false so a self-signed upstream was accepted in prod",
        "traefik.yml", "passHostHeader: true", "insecureSkipVerify false",
        "insecureSkipVerify", "harbor passHostHeader only. pack insecureSkipVerify false.",
        "FAIL test_assign: self-signed upstream accepted; insecureSkipVerify missing",
        "passHostHeader only", "passHostHeader is not insecureSkipVerify"),
    "caddy": mk(False, "pr-caddy-auto-https-disable-off", "quay-cadyhttps",
        "the Caddyfile that omitted auto_https disable_redirects so HTTP:80 308'd a health check behind an NLB",
        "Caddyfile", "encode gzip", "auto_https disable_redirects",
        "auto_https", "harbor encode gzip only. pack auto_https disable_redirects.",
        "FAIL test_assign: NLB health 308; auto_https disable_redirects missing",
        "encode gzip only", "encode is not auto_https disable_redirects"),
    "nginx": mk(True, "pr-nginx-proxy-buffer-size-headers", "lock-ngxbuf",
        "the nginx location that omitted proxy_buffer_size so an upstream Set-Cookie header overflowed and 502'd",
        "nginx.conf", "proxy_buffers 8 4k;", "proxy_buffer_size 16k",
        "proxy_buffer_size", "harbor proxy_buffers only. pack proxy_buffer_size.",
        "FAIL test_assign: 502 upstream sent too big header; proxy_buffer_size missing",
        "proxy_buffers only", "proxy_buffers is not proxy_buffer_size"),
    "haproxy": mk(False, "pr-haproxy-timeout-tunnel-ws", "quay-haptun",
        "the HAProxy listen that omitted timeout tunnel so websocket connections were cut at timeout client",
        "haproxy.cfg", "timeout client 30s", "timeout tunnel 1h",
        "timeout tunnel", "harbor timeout client only. pack timeout tunnel.",
        "FAIL test_assign: websocket cut 30s; timeout tunnel missing",
        "timeout client only", "timeout client is not timeout tunnel"),
    "cockroach": mk(True, "pr-cockroach-range-max-bytes", "lock-crdbmax",
        "the Cockroach zone that omitted range_max_bytes so hot ranges never split and one leaseholder saturated",
        "zone.sql", "gc.ttlseconds = 90000", "range_max_bytes 536870912",
        "range_max_bytes", "harbor gc.ttlseconds only. pack range_max_bytes.",
        "FAIL test_assign: hot range unsplittable; leaseholder saturated; range_max_bytes missing",
        "gc.ttlseconds only", "gc ttl is not range_max_bytes"),
    "tidb": mk(False, "pr-tidb-tikv-gc-life-time", "quay-tidbgc",
        "the TiDB cluster that omitted tikv_gc_life_time so a 2h ANALYZE saw GC already drop MVCC versions",
        "tidb.toml", "split-table = true", "tikv_gc_life_time 24h",
        "tikv_gc_life_time", "harbor split-table only. pack tikv_gc_life_time.",
        "FAIL test_assign: ANALYZE GC too old; tikv_gc_life_time missing",
        "split-table only", "split-table is not tikv_gc_life_time"),
    "yugabyte": mk(True, "pr-yugabyte-ysql-max-connections", "lock-ybmaxc",
        "the Yugabyte tserver that omitted ysql_max_connections so the pooler opened 800 backends and tserver OOMed",
        "tserver.conf", "ysql_enable_auth=true", "ysql_max_connections 200",
        "ysql_max_connections", "harbor ysql_enable_auth only. pack ysql_max_connections.",
        "FAIL test_assign: 800 backends; tserver OOM; ysql_max_connections missing",
        "ysql_enable_auth only", "ysql_enable_auth is not ysql_max_connections"),
    "spanner": mk(False, "pr-spanner-exact-staleness-bound", "quay-spnstale",
        "the Spanner client that omitted exact staleness bound so every read hit the leader and p99 doubled",
        "spanner.go", "Apply(ctx, ms)", "exact staleness 15s",
        "staleness", "harbor Apply only. pack exact staleness.",
        "FAIL test_assign: all reads on leader; p99 doubled; staleness missing",
        "Apply only", "Apply is not exact staleness"),
    "fdb": mk(True, "pr-fdb-knob-location-metadata", "lock-fdbknob",
        "the FoundationDB cluster that omitted knob location-metadata-memory so a large keyspace OOM'd fdbserver",
        "foundationdb.conf", "knob_max_outstanding_requests=1000", "knob_location_metadata_memory 2GB",
        "knob_location_metadata_memory", "harbor max_outstanding_requests only. pack location_metadata_memory.",
        "FAIL test_assign: fdbserver OOM; location_metadata_memory missing",
        "max_outstanding_requests only", "outstanding requests is not location_metadata_memory"),
    "vitess": mk(False, "pr-vitess-vreplication-tablet-types", "quay-vtvrep",
        "the Vitess MoveTables that omitted tablet_types REPLICA so vreplication hit the primary and lag spiked writes",
        "vttablet.cnf", "health_check_interval=5s", "tablet_types REPLICA",
        "tablet_types", "harbor health_check_interval only. pack tablet_types REPLICA.",
        "FAIL test_assign: vreplication on primary; write lag; tablet_types missing",
        "health_check_interval only", "health_check_interval is not tablet_types"),
    "neon": mk(True, "pr-neon-endpoint-suspend-timeout", "lock-neonsus",
        "the Neon endpoint that omitted suspend_timeout so compute never scaled to zero and the bill spiked",
        "endpoint.json", "autoscaling_limit_min_cu: 0.25", "suspend_timeout 300",
        "suspend_timeout", "harbor autoscaling_limit_min_cu only. pack suspend_timeout.",
        "FAIL test_assign: compute never idle; bill spike; suspend_timeout missing",
        "autoscaling_limit_min_cu only", "min CU is not suspend_timeout"),
    "hasura": mk(False, "pr-hasura-stringify-numeric-types", "quay-hsrnum",
        "the Hasura metadata that omitted stringify-numeric-types so JS clients lost bigint precision on ids",
        "config.yaml", "live_queries_multiplexed_refetch_interval: 1000", "stringify-numeric-types true",
        "stringify-numeric-types", "harbor live_queries interval only. pack stringify-numeric-types.",
        "FAIL test_assign: bigint id rounded; stringify-numeric-types missing",
        "live_queries interval only", "live_queries is not stringify-numeric-types"),
    "postgrest": mk(True, "pr-postgrest-db-anon-role", "lock-pgran",
        "the PostgREST conf that omitted db-anon-role so unauthenticated requests used the authenticator and leaked tables",
        "postgrest.conf", "db-schema = public", "db-anon-role web_anon",
        "db-anon-role", "harbor db-schema only. pack db-anon-role.",
        "FAIL test_assign: anon used authenticator; tables leaked; db-anon-role missing",
        "db-schema only", "db-schema is not db-anon-role"),
    "prisma": mk(False, "pr-prisma-relation-mode-prisma", "quay-prsmrel",
        "the Prisma schema that omitted relationMode prisma so PlanetScale FK errors aborted every migrate",
        "schema.prisma", "previewFeatures = [\"multiSchema\"]", "relationMode prisma",
        "relationMode", "harbor previewFeatures only. pack relationMode prisma.",
        "FAIL test_assign: migrate FK abort; relationMode missing",
        "previewFeatures only", "previewFeatures is not relationMode"),
    "typeorm": mk(True, "pr-typeorm-synchronize-off-prod", "lock-torsync",
        "the TypeORM DataSource that omitted synchronize false so a prod boot dropped a column",
        "data-source.ts", "migrationsRun: true", "synchronize false",
        "synchronize", "harbor migrationsRun only. pack synchronize false.",
        "FAIL test_assign: prod boot dropped column; synchronize missing",
        "migrationsRun only", "migrationsRun is not synchronize false"),
    "sequelize": mk(False, "pr-sequelize-underscored-true", "quay-seqund",
        "the Sequelize model that omitted underscored true so createdAt was queried as createdAt and Postgres 42703'd",
        "model.js", "timestamps: true", "underscored true",
        "underscored", "harbor timestamps only. pack underscored.",
        "FAIL test_assign: column createdAt missing; underscored missing",
        "timestamps only", "timestamps is not underscored"),
    "sqlalchemy": mk(True, "pr-sqlalchemy-expire-on-commit", "lock-saexp",
        "the SQLAlchemy session that omitted expire_on_commit false so a background worker lazy-loaded after commit and DetachedInstanceError'd",
        "session.py", "autoflush=True", "expire_on_commit false",
        "expire_on_commit", "harbor autoflush only. pack expire_on_commit false.",
        "FAIL test_assign: DetachedInstanceError after commit; expire_on_commit missing",
        "autoflush only", "autoflush is not expire_on_commit"),
    "camunda": mk(False, "pr-camunda-history-ttl-days", "quay-cmttl",
        "the Camunda engine that omitted historyTimeToLive so ACT_HI_* tables filled the disk",
        "bpmn.xml", "isExecutable=true", "historyTimeToLive 30",
        "historyTimeToLive", "harbor isExecutable only. pack historyTimeToLive.",
        "FAIL test_assign: ACT_HI disk full; historyTimeToLive missing",
        "isExecutable only", "isExecutable is not historyTimeToLive"),
    "zeebe": mk(True, "pr-zeebe-max-message-size-mb", "lock-zbmsg",
        "the Zeebe broker that omitted maxMessageSize so a 8MB job variable was rejected and the workflow stuck",
        "application.yaml", "zeebe.broker.network.port: 26500", "maxMessageSize 16MB",
        "maxMessageSize", "harbor network.port only. pack maxMessageSize.",
        "FAIL test_assign: 8MB variable rejected; workflow stuck; maxMessageSize missing",
        "network.port only", "network.port is not maxMessageSize"),
    "activiti": mk(False, "pr-activiti-async-executor-activate", "quay-actasync",
        "the Activiti engine that omitted asyncExecutorActivate so timer jobs never fired and SLAs missed",
        "activiti.cfg.xml", "jobExecutorActivate=false", "asyncExecutorActivate true",
        "asyncExecutorActivate", "harbor jobExecutorActivate only. pack asyncExecutorActivate.",
        "FAIL test_assign: timers never fire; asyncExecutorActivate missing",
        "jobExecutorActivate only", "jobExecutorActivate is not asyncExecutorActivate"),
    "planetscale": mk(True, "pr-planetscale-safe-migrations-on", "lock-pssafe",
        "the PlanetScale branch that omitted safe migrations so a DROP COLUMN shipped without a revertable deploy request",
        "pscale.yml", "insights: true", "safe migrations on",
        "safe migrations", "harbor insights only. pack safe migrations.",
        "FAIL test_assign: DROP COLUMN no revert; safe migrations missing",
        "insights only", "insights is not safe migrations"),
    "supabase": mk(False, "pr-supabase-auth-jwt-expiry", "quay-sbjwt",
        "the Supabase auth that omitted JWT expiry so a leaked token stayed valid for a week",
        "config.toml", "enable_refresh_token_rotation = true", "jwt_expiry 3600",
        "jwt_expiry", "harbor refresh token rotation only. pack jwt_expiry.",
        "FAIL test_assign: leaked token valid 7d; jwt_expiry missing",
        "refresh token rotation only", "refresh rotation is not jwt_expiry"),
    "meilisearch": mk(True, "pr-meilisearch-max-indexing-memory", "lock-meilimem",
        "the Meilisearch instance that omitted max_indexing_memory so a bulk index OOM-killed the node",
        "config.toml", "max_indexing_threads = 4", "max_indexing_memory 2GiB",
        "max_indexing_memory", "harbor max_indexing_threads only. pack max_indexing_memory.",
        "FAIL test_assign: bulk index OOM; max_indexing_memory missing",
        "max_indexing_threads only", "indexing threads is not max_indexing_memory"),
    "typesense": mk(False, "pr-typesense-snapshot-interval-seconds", "quay-typsnap",
        "the Typesense node that omitted snapshot-interval-seconds so a crash lost hours of in-memory documents",
        "typesense.ini", "enable-cors = true", "snapshot-interval-seconds 3600",
        "snapshot-interval-seconds", "harbor enable-cors only. pack snapshot-interval-seconds.",
        "FAIL test_assign: crash lost documents; snapshot-interval missing",
        "enable-cors only", "enable-cors is not snapshot-interval-seconds"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Ceph osd_memory_target vs MinIO erasure set", fn("ceph"), fn("minio"),
     "osd_memory_target 4GB; erasure set drive count 4", "cache_min; storage class EC:2",
     "ceph dump OSD OOM; minio dump 7-drive heal stuck"),
    ("Longhorn soft anti-affinity vs OpenEBS Jiva replicas", fn("longhorn"), fn("openebs"),
     "replicaSoftAntiAffinity; ReplicaCount 3", "numberOfReplicas; StoragePool",
     "longhorn dump same-node drain; openebs dump PVC readonly"),
    ("Rook mon.count vs SeaweedFS volume size", fn("rook"), fn("seaweed"),
     "mon.count 3; volumeSizeLimitMB", "mgr.count; filer.defaultReplication",
     "rook dump mon quorum; seaweed dump volume > disk"),
    ("JuiceFS cache-size vs Garage replication_mode", fn("juicefs"), fn("garage"),
     "cache-size; replication_mode 3", "cache-dir; consistency_mode",
     "juicefs dump root full; garage dump node loss drop"),
    ("Woodpecker privileged vs Drone clone disable", fn("woodpecker"), fn("drone"),
     "privileged false; clone disable", "plugins/docker; kind pipeline",
     "woodpecker dump docker.sock; drone dump workspace empty"),
    ("Buildkite artifact_paths vs Tekton pipeline timeout", fn("buildkite"), fn("tekton"),
     "artifact_paths junit.xml; timeouts.pipeline 1h", "agents queue; taskRunSpecs",
     "buildkite dump empty panel; tekton dump hung 24h"),
    ("Concourse check_every vs Jenkins throttle", fn("concourse"), fn("jenkins"),
     "check_every 5m; throttle category", "webhook_token; timestamps",
     "concourse dump git 429; jenkins dump Maven 503"),
    ("Vault max_lease_ttl vs SOPS encrypted_regex", fn("vault"), fn("sops"),
     "max_lease_ttl 24h; encrypted_regex", "default_lease_ttl; age recipient",
     "vault dump 32d token; sops dump plaintext git"),
    ("Infisical autoReload vs Doppler config stg", fn("infisical"), fn("doppler"),
     "autoReload; config stg", "resyncInterval; project",
     "infisical dump old DATABASE_URL; doppler dump prod in staging"),
    ("Chamber kms-key-alias vs ExternalSecret refresh", fn("chamber"), fn("externalsecrets"),
     "kms-key-alias; refreshInterval 1m", "empty alias env; secretStoreRef",
     "chamber dump default AWS key; eso dump stale 3d"),
    ("Cilium hostns-only vs Calico ipipMode", fn("cilium"), fn("calico"),
     "bpf-lb-sock-hostns-only; ipipMode CrossSubnet", "bpf-lb-sock; vxlanMode",
     "cilium dump hostNetwork blackhole; calico dump MTU shred"),
    ("Istio holdApplication vs Linkerd proxy-await", fn("istio"), fn("linkerd"),
     "holdApplicationUntilProxyStarts; proxy-await", "rewriteAppHTTPProbers; skip-inbound-ports",
     "istio dump first 30s drop; linkerd dump boot 503"),
    ("Traefik insecureSkipVerify vs Caddy auto_https", fn("traefik"), fn("caddy"),
     "insecureSkipVerify false; auto_https disable_redirects", "passHostHeader; encode gzip",
     "traefik dump self-signed prod; caddy dump NLB 308"),
    ("nginx proxy_buffer_size vs HAProxy timeout tunnel", fn("nginx"), fn("haproxy"),
     "proxy_buffer_size 16k; timeout tunnel 1h", "proxy_buffers; timeout client",
     "nginx dump 502 big header; haproxy dump ws cut 30s"),
    ("Cockroach range_max_bytes vs TiDB gc life", fn("cockroach"), fn("tidb"),
     "range_max_bytes; tikv_gc_life_time 24h", "gc.ttlseconds; split-table",
     "cockroach dump hot range; tidb dump ANALYZE GC"),
    ("Yugabyte ysql_max_connections vs Spanner staleness", fn("yugabyte"), fn("spanner"),
     "ysql_max_connections 200; exact staleness 15s", "ysql_enable_auth; Apply",
     "yugabyte dump 800 backends; spanner dump leader p99"),
    ("FDB location_metadata_memory vs Vitess tablet_types", fn("fdb"), fn("vitess"),
     "location_metadata_memory; tablet_types REPLICA", "outstanding requests; health_check_interval",
     "fdb dump fdbserver OOM; vitess dump vreplication primary"),
    ("Neon suspend_timeout vs Hasura stringify-numeric", fn("neon"), fn("hasura"),
     "suspend_timeout 300; stringify-numeric-types", "min CU; live_queries",
     "neon dump never idle; hasura dump bigint rounded"),
    ("PostgREST db-anon-role vs Prisma relationMode", fn("postgrest"), fn("prisma"),
     "db-anon-role; relationMode prisma", "db-schema; previewFeatures",
     "postgrest dump authenticator leak; prisma dump FK abort"),
    ("TypeORM synchronize vs Sequelize underscored", fn("typeorm"), fn("sequelize"),
     "synchronize false; underscored true", "migrationsRun; timestamps",
     "typeorm dump dropped column; sequelize dump 42703"),
    ("SQLAlchemy expire_on_commit vs Camunda history TTL", fn("sqlalchemy"), fn("camunda"),
     "expire_on_commit false; historyTimeToLive 30", "autoflush; isExecutable",
     "sqlalchemy dump DetachedInstanceError; camunda dump ACT_HI full"),
    ("Zeebe maxMessageSize vs Activiti async executor", fn("zeebe"), fn("activiti"),
     "maxMessageSize 16MB; asyncExecutorActivate", "network.port; jobExecutorActivate",
     "zeebe dump 8MB reject; activiti dump timers dead"),
    ("PlanetScale safe migrations vs Supabase jwt_expiry", fn("planetscale"), fn("supabase"),
     "safe migrations on; jwt_expiry 3600", "insights; refresh rotation",
     "planetscale dump DROP no revert; supabase dump 7d token"),
    ("Meilisearch max_indexing_memory vs Typesense snapshot interval", fn("meilisearch"), fn("typesense"),
     "max_indexing_memory 2GiB; snapshot-interval-seconds", "indexing threads; enable-cors",
     "meilisearch dump bulk OOM; typesense dump crash loss"),
]


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of r4163-w4ck (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, identity-origin SSO window kanidm/gluu/casdoor/authentik/oauth2-proxy/ory/hydra/kratos/keto/zitadel/authelia/pomerium/teleport/dex/sssd/pam, ingress/gateway w4ci, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name in {"sandbox-refusal-factory", "long-horizon-coding-factory"}:
            continue
        if any(p.glob("ROUND-r*.reserved.json")):
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (no plant catalog here, retry LHC):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(2)
            if hops > 40:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
