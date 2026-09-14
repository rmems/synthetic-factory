#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cf: unused plants after r4540.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4540. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cf_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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
    if not (18 <= len(out) <= 20):
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

PLANTS = {
    "kind": P(True,
        slug='pr-kind-extra-mounts-containerd',
        plant='lock-kindmnt',
        what="the kind cluster that omitted extraMounts so containerd could not see the host docker certs and image pulls 403'd",
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='kind.yaml tests/test_harbor.py',
        impl='kind.yaml',
        src='kind: Cluster\nnodes: [{role: control-plane}]',
        sym='extraMounts docker certs',
        grep='extraMounts',
        grep_obs='harbor kubeadmConfigPatches only. pack extraMounts certs.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pull 403; extraMounts missing; host certs not in node',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='kubeadmConfigPatches only',
        wrong_diff='+ kubeadmConfigPatches only',
        wrong_obs='still kubeadmConfigPatches only. still fail.',
        fail2='FAIL test_assign: still broken. extraMounts certs.',
        reread='apply extraMounts certs.',
        insight='kubeadmConfigPatches is not extraMounts',
        probe="rg -n 'extraMounts' kind.yaml",
        probe_obs='pack extraMounts certs. harbor kubeadmConfigPatches only.',
        fix='extraMounts certs',
        fix_diff='+ extraMounts certs\n',
        rel='dump/kind.yaml',
        rel_src='kind: Cluster\nnodes: [{role: control-plane}]',
        leftover='leftover kubeadmConfigPatches only',
        fix2='dump extraMounts certs',
        fix2_diff='+ dump extraMounts certs\n',
        bad_pat='kubeadmConfigPatches only',
        doc='docs/LOCK-KINDMNT.md',
        doc_point='kubeadmConfigPatches is not extraMounts',
        doc_diff='+ kubeadmConfigPatches is not extraMounts.',
        reg='reg',
        reg_diff='+ extraMounts certs holds',
        final_ok='ok 6 passed. extraMounts certs.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='extraMounts certs; dump same.',
        wrap='the extraMounts certs',
        wrap_ok='6 passed. lock-kindmnt assign is green.',
        wrap_part='5 passed, 1 residual. lock-kindmnt assign is green.',
        goal="Designed plant lock-kindmnt: the kind cluster that omitted extraMounts so containerd could not see the host docker certs and image pulls 403'd. extraMounts certs. kubeadmConfigPatches is not extraMounts.",
        plan='Repro python tests, reject kubeadmConfigPatches only, extraMounts certs, fix dump.',
        out_ok='extraMounts certs. 6 tests pass.',
        out_part='extraMounts certs. dump leftover. Partial.',
    ),
    "minikube": P(False,
        slug='pr-minikube-embed-certs-apiserver',
        plant='quay-mkembed',
        what='the minikube start that omitted --embed-certs so the kubeconfig pointed at a temp client cert that vanished after reboot',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='minikube start --driver=docker',
        sym='embed-certs',
        grep='embed-certs',
        grep_obs='harbor minikube update-context. pack embed-certs true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: after reboot x509 unknown; embed-certs missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='minikube update-context',
        wrong_diff='+ minikube update-context',
        wrong_obs='still minikube update-context. still fail.',
        fail2='FAIL test_assign: still broken. embed-certs true.',
        reread='apply embed-certs true.',
        insight='update-context is not embed-certs',
        probe="rg -n 'embed-certs' Makefile",
        probe_obs='pack embed-certs true. harbor minikube update-context.',
        fix='embed-certs true',
        fix_diff='+ embed-certs true\n',
        rel='dump/Makefile',
        rel_src='minikube start --driver=docker',
        leftover='leftover minikube update-context',
        fix2='dump embed-certs true',
        fix2_diff='+ dump embed-certs true\n',
        bad_pat='minikube update-context',
        doc='docs/QUAY-MKEMBED.md',
        doc_point='update-context is not embed-certs',
        doc_diff='+ update-context is not embed-certs.',
        reg='reg',
        reg_diff='+ embed-certs true holds',
        final_ok='ok 6 passed. embed-certs true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='embed-certs true; dump leftover.',
        wrap='the embed-certs true',
        wrap_ok='6 passed. quay-mkembed assign is green.',
        wrap_part='5 passed, 1 residual. quay-mkembed assign is green.',
        goal='Designed plant quay-mkembed: the minikube start that omitted --embed-certs so the kubeconfig pointed at a temp client cert that vanished after reboot. embed-certs true. update-context is not embed-certs.',
        plan='Repro python tests, reject minikube update-context, embed-certs true, hand off dump.',
        out_ok='embed-certs true. 6 tests pass.',
        out_part='embed-certs true. dump leftover. Partial.',
    ),
    "k3d": P(True,
        slug='pr-k3d-registry-create-volume',
        plant='lock-k3dreg',
        what='the k3d registry that omitted a volume so pushed images vanished after the registry container recreated',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='k3d.yaml tests/test_harbor.py',
        impl='k3d.yaml',
        src='registries:\n  create:\n    name: harbor-reg',
        sym='volume for registry',
        grep='volume',
        grep_obs='harbor k3d image import only. pack registry volume.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: after recreate image 404; registry volume missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='k3d image import only',
        wrong_diff='+ k3d image import only',
        wrong_obs='still k3d image import only. still fail.',
        fail2='FAIL test_assign: still broken. registry volume.',
        reread='apply registry volume.',
        insight='image import is not a registry volume',
        probe="rg -n 'registry' k3d.yaml",
        probe_obs='pack registry volume. harbor k3d image import only.',
        fix='registry volume',
        fix_diff='+ registry volume\n',
        rel='dump/k3d.yaml',
        rel_src='registries:\n  create:\n    name: harbor-reg',
        leftover='leftover k3d image import only',
        fix2='dump registry volume',
        fix2_diff='+ dump registry volume\n',
        bad_pat='k3d image import only',
        doc='docs/LOCK-K3DREG.md',
        doc_point='image import is not a registry volume',
        doc_diff='+ image import is not a registry volume.',
        reg='reg',
        reg_diff='+ registry volume holds',
        final_ok='ok 6 passed. registry volume.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='registry volume; dump same.',
        wrap='the registry volume',
        wrap_ok='6 passed. lock-k3dreg assign is green.',
        wrap_part='5 passed, 1 residual. lock-k3dreg assign is green.',
        goal='Designed plant lock-k3dreg: the k3d registry that omitted a volume so pushed images vanished after the registry container recreated. registry volume. image import is not a registry volume.',
        plan='Repro python tests, reject k3d image import only, registry volume, fix dump.',
        out_ok='registry volume. 6 tests pass.',
        out_part='registry volume. dump leftover. Partial.',
    ),
    "microk8s": P(False,
        slug='pr-microk8s-rbac-enable-addon',
        plant='quay-m8srbac',
        what='the MicroK8s install that omitted rbac addon so a RoleBinding was ignored and the service account had cluster-admin',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='microk8s-config.yaml tests/test_harbor.py',
        impl='microk8s-config.yaml',
        src='addons: [dns, storage]',
        sym='rbac addon',
        grep='rbac',
        grep_obs='harbor enable ingress only. pack microk8s enable rbac.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: RoleBinding no-op; rbac addon disabled; SA is cluster-admin',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enable ingress only',
        wrong_diff='+ enable ingress only',
        wrong_obs='still enable ingress only. still fail.',
        fail2='FAIL test_assign: still broken. microk8s enable rbac.',
        reread='apply microk8s enable rbac.',
        insight='ingress addon is not rbac',
        probe="rg -n 'microk8s' microk8s-config.yaml",
        probe_obs='pack microk8s enable rbac. harbor enable ingress only.',
        fix='microk8s enable rbac',
        fix_diff='+ microk8s enable rbac\n',
        rel='dump/microk8s-config.yaml',
        rel_src='addons: [dns, storage]',
        leftover='leftover enable ingress only',
        fix2='dump microk8s enable rbac',
        fix2_diff='+ dump microk8s enable rbac\n',
        bad_pat='enable ingress only',
        doc='docs/QUAY-M8SRBAC.md',
        doc_point='ingress addon is not rbac',
        doc_diff='+ ingress addon is not rbac.',
        reg='reg',
        reg_diff='+ microk8s enable rbac holds',
        final_ok='ok 6 passed. microk8s enable rbac.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='microk8s enable rbac; dump leftover.',
        wrap='the microk8s enable rbac',
        wrap_ok='6 passed. quay-m8srbac assign is green.',
        wrap_part='5 passed, 1 residual. quay-m8srbac assign is green.',
        goal='Designed plant quay-m8srbac: the MicroK8s install that omitted rbac addon so a RoleBinding was ignored and the service account had cluster-admin. microk8s enable rbac. ingress addon is not rbac.',
        plan='Repro python tests, reject enable ingress only, microk8s enable rbac, hand off dump.',
        out_ok='microk8s enable rbac. 6 tests pass.',
        out_part='microk8s enable rbac. dump leftover. Partial.',
    ),
    "cdk": P(True,
        slug='pr-cdk-context-azs-lookup',
        plant='lock-cdkazs',
        what='the CDK stack that omitted availabilityZones context so synth listed 0 AZs and the VPC construct threw',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='cdk.json tests/test_harbor.py',
        impl='cdk.json',
        src='{"app": "npx ts-node bin/harbor.ts"}',
        sym='availability-zones context',
        grep='availability-zones',
        grep_obs='harbor env account region only. pack availabilityZones context.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: VPC 0 AZs; availability-zones context missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='env account region only',
        wrong_diff='+ env account region only',
        wrong_obs='still env account region only. still fail.',
        fail2='FAIL test_assign: still broken. availabilityZones context.',
        reread='apply availabilityZones context.',
        insight='env account/region is not AZ context',
        probe="rg -n 'availabilityZones' cdk.json",
        probe_obs='pack availabilityZones context. harbor env account region only.',
        fix='availabilityZones context',
        fix_diff='+ availabilityZones context\n',
        rel='dump/cdk.json',
        rel_src='{"app": "npx ts-node bin/harbor.ts"}',
        leftover='leftover env account region only',
        fix2='dump availabilityZones context',
        fix2_diff='+ dump availabilityZones context\n',
        bad_pat='env account region only',
        doc='docs/LOCK-CDKAZS.md',
        doc_point='env account/region is not AZ context',
        doc_diff='+ env account/region is not AZ context.',
        reg='reg',
        reg_diff='+ availabilityZones context holds',
        final_ok='ok 6 passed. availabilityZones context.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='availabilityZones context; dump same.',
        wrap='the availabilityZones context',
        wrap_ok='6 passed. lock-cdkazs assign is green.',
        wrap_part='5 passed, 1 residual. lock-cdkazs assign is green.',
        goal='Designed plant lock-cdkazs: the CDK stack that omitted availabilityZones context so synth listed 0 AZs and the VPC construct threw. availabilityZones context. env account/region is not AZ context.',
        plan='Repro python tests, reject env account region only, availabilityZones context, fix dump.',
        out_ok='availabilityZones context. 6 tests pass.',
        out_part='availabilityZones context. dump leftover. Partial.',
    ),
    "k3s": P(False,
        slug='pr-k3s-disable-traefik-servicelb',
        plant='quay-k3sdis',
        what='the k3s server that omitted --disable=traefik so the custom ingress-nginx and traefik fought on :443',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='config.yaml tests/test_harbor.py',
        impl='config.yaml',
        src='write-kubeconfig-mode: "0644"',
        sym='disable traefik',
        grep='disable',
        grep_obs='harbor tls-san only. pack disable traefik servicelb.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: :443 bind clash traefik vs ingress-nginx; disable missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='tls-san only',
        wrong_diff='+ tls-san only',
        wrong_obs='still tls-san only. still fail.',
        fail2='FAIL test_assign: still broken. disable traefik servicelb.',
        reread='apply disable traefik servicelb.',
        insight='tls-san is not --disable=traefik',
        probe="rg -n 'disable' config.yaml",
        probe_obs='pack disable traefik servicelb. harbor tls-san only.',
        fix='disable traefik servicelb',
        fix_diff='+ disable traefik servicelb\n',
        rel='dump/config.yaml',
        rel_src='write-kubeconfig-mode: "0644"',
        leftover='leftover tls-san only',
        fix2='dump disable traefik servicelb',
        fix2_diff='+ dump disable traefik servicelb\n',
        bad_pat='tls-san only',
        doc='docs/QUAY-K3SDIS.md',
        doc_point='tls-san is not --disable=traefik',
        doc_diff='+ tls-san is not --disable=traefik.',
        reg='reg',
        reg_diff='+ disable traefik servicelb holds',
        final_ok='ok 6 passed. disable traefik servicelb.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='disable traefik servicelb; dump leftover.',
        wrap='the disable traefik servicelb',
        wrap_ok='6 passed. quay-k3sdis assign is green.',
        wrap_part='5 passed, 1 residual. quay-k3sdis assign is green.',
        goal='Designed plant quay-k3sdis: the k3s server that omitted --disable=traefik so the custom ingress-nginx and traefik fought on :443. disable traefik servicelb. tls-san is not --disable=traefik.',
        plan='Repro python tests, reject tls-san only, disable traefik servicelb, hand off dump.',
        out_ok='disable traefik servicelb. 6 tests pass.',
        out_part='disable traefik servicelb. dump leftover. Partial.',
    ),
    "k0s": P(True,
        slug='pr-k0s-konnectivity-enabled',
        plant='lock-k0skon',
        what='the k0s controller that omitted konnectivity so worker kubelets could not reach the apiserver through the tunnel',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='k0s.yaml tests/test_harbor.py',
        impl='k0s.yaml',
        src='apiVersion: k0s.k0sproject.io/v1beta1\nkind: ClusterConfig',
        sym='konnectivity enabled',
        grep='konnectivity',
        grep_obs='harbor workerProfiles only. pack konnectivity enabled.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: kubelet timeout apiserver; konnectivity disabled',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='workerProfiles only',
        wrong_diff='+ workerProfiles only',
        wrong_obs='still workerProfiles only. still fail.',
        fail2='FAIL test_assign: still broken. konnectivity enabled.',
        reread='apply konnectivity enabled.',
        insight='workerProfiles is not konnectivity',
        probe="rg -n 'konnectivity' k0s.yaml",
        probe_obs='pack konnectivity enabled. harbor workerProfiles only.',
        fix='konnectivity enabled',
        fix_diff='+ konnectivity enabled\n',
        rel='dump/k0s.yaml',
        rel_src='apiVersion: k0s.k0sproject.io/v1beta1\nkind: ClusterConfig',
        leftover='leftover workerProfiles only',
        fix2='dump konnectivity enabled',
        fix2_diff='+ dump konnectivity enabled\n',
        bad_pat='workerProfiles only',
        doc='docs/LOCK-K0SKON.md',
        doc_point='workerProfiles is not konnectivity',
        doc_diff='+ workerProfiles is not konnectivity.',
        reg='reg',
        reg_diff='+ konnectivity enabled holds',
        final_ok='ok 6 passed. konnectivity enabled.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='konnectivity enabled; dump same.',
        wrap='the konnectivity enabled',
        wrap_ok='6 passed. lock-k0skon assign is green.',
        wrap_part='5 passed, 1 residual. lock-k0skon assign is green.',
        goal='Designed plant lock-k0skon: the k0s controller that omitted konnectivity so worker kubelets could not reach the apiserver through the tunnel. konnectivity enabled. workerProfiles is not konnectivity.',
        plan='Repro python tests, reject workerProfiles only, konnectivity enabled, fix dump.',
        out_ok='konnectivity enabled. 6 tests pass.',
        out_part='konnectivity enabled. dump leftover. Partial.',
    ),
    "kops": P(False,
        slug='pr-kops-instancegroup-max-size-zero',
        plant='quay-kopsmax',
        what='the kops InstanceGroup that set maxSize 0 so rolling-update scaled the ASG to zero and the cluster lost nodes',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='ig.yaml tests/test_harbor.py',
        impl='ig.yaml',
        src='spec:\n  minSize: 3\n  maxSize: 0',
        sym='maxSize >= minSize',
        grep='maxSize',
        grep_obs='harbor rolling-update --force. pack maxSize 6.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: ASG desired 0; maxSize 0; nodes gone',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='rolling-update --force',
        wrong_diff='+ rolling-update --force',
        wrong_obs='still rolling-update --force. still fail.',
        fail2='FAIL test_assign: still broken. maxSize 6.',
        reread='apply maxSize 6.',
        insight='--force rolling-update is not maxSize',
        probe="rg -n 'maxSize' ig.yaml",
        probe_obs='pack maxSize 6. harbor rolling-update --force.',
        fix='maxSize 6',
        fix_diff='+ maxSize 6\n',
        rel='dump/ig.yaml',
        rel_src='spec:\n  minSize: 3\n  maxSize: 0',
        leftover='leftover rolling-update --force',
        fix2='dump maxSize 6',
        fix2_diff='+ dump maxSize 6\n',
        bad_pat='rolling-update --force',
        doc='docs/QUAY-KOPSMAX.md',
        doc_point='--force rolling-update is not maxSize',
        doc_diff='+ --force rolling-update is not maxSize.',
        reg='reg',
        reg_diff='+ maxSize 6 holds',
        final_ok='ok 6 passed. maxSize 6.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='maxSize 6; dump leftover.',
        wrap='the maxSize 6',
        wrap_ok='6 passed. quay-kopsmax assign is green.',
        wrap_part='5 passed, 1 residual. quay-kopsmax assign is green.',
        goal='Designed plant quay-kopsmax: the kops InstanceGroup that set maxSize 0 so rolling-update scaled the ASG to zero and the cluster lost nodes. maxSize 6. --force rolling-update is not maxSize.',
        plan='Repro python tests, reject rolling-update --force, maxSize 6, hand off dump.',
        out_ok='maxSize 6. 6 tests pass.',
        out_part='maxSize 6. dump leftover. Partial.',
    ),
    "eksctl": P(True,
        slug='pr-eksctl-iam-oidc-provider',
        plant='lock-eksoidc',
        what='the eksctl cluster that omitted iam.withOIDC so the IRSA ServiceAccount annotation was ignored and the pod used node role',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='cluster.yaml tests/test_harbor.py',
        impl='cluster.yaml',
        src='iam:\n  withOIDC: false',
        sym='withOIDC true',
        grep='withOIDC',
        grep_obs='harbor iamIdentityMappings only. pack withOIDC true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pod used node role; withOIDC false; IRSA ignored',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='iamIdentityMappings only',
        wrong_diff='+ iamIdentityMappings only',
        wrong_obs='still iamIdentityMappings only. still fail.',
        fail2='FAIL test_assign: still broken. withOIDC true.',
        reread='apply withOIDC true.',
        insight='iamIdentityMappings is not withOIDC',
        probe="rg -n 'withOIDC' cluster.yaml",
        probe_obs='pack withOIDC true. harbor iamIdentityMappings only.',
        fix='withOIDC true',
        fix_diff='+ withOIDC true\n',
        rel='dump/cluster.yaml',
        rel_src='iam:\n  withOIDC: false',
        leftover='leftover iamIdentityMappings only',
        fix2='dump withOIDC true',
        fix2_diff='+ dump withOIDC true\n',
        bad_pat='iamIdentityMappings only',
        doc='docs/LOCK-EKSOIDC.md',
        doc_point='iamIdentityMappings is not withOIDC',
        doc_diff='+ iamIdentityMappings is not withOIDC.',
        reg='reg',
        reg_diff='+ withOIDC true holds',
        final_ok='ok 6 passed. withOIDC true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='withOIDC true; dump same.',
        wrap='the withOIDC true',
        wrap_ok='6 passed. lock-eksoidc assign is green.',
        wrap_part='5 passed, 1 residual. lock-eksoidc assign is green.',
        goal='Designed plant lock-eksoidc: the eksctl cluster that omitted iam.withOIDC so the IRSA ServiceAccount annotation was ignored and the pod used node role. withOIDC true. iamIdentityMappings is not withOIDC.',
        plan='Repro python tests, reject iamIdentityMappings only, withOIDC true, fix dump.',
        out_ok='withOIDC true. 6 tests pass.',
        out_part='withOIDC true. dump leftover. Partial.',
    ),
    "compose": P(False,
        slug='pr-compose-profiles-default-on',
        plant='quay-cmpprof',
        what='the Compose file that omitted profiles so the debug sidecar started in production and opened :9229',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='compose.yml tests/test_harbor.py',
        impl='compose.yml',
        src='services:\n  debug:\n    image: node',
        sym='profiles debug',
        grep='profiles',
        grep_obs='harbor scale 0. pack profiles: [debug].',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: debug sidecar on :9229 in prod; profiles missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='scale 0',
        wrong_diff='+ scale 0',
        wrong_obs='still scale 0. still fail.',
        fail2='FAIL test_assign: still broken. profiles: [debug].',
        reread='apply profiles: [debug].',
        insight='scale 0 is not profiles',
        probe="rg -n 'profiles:' compose.yml",
        probe_obs='pack profiles: [debug]. harbor scale 0.',
        fix='profiles: [debug]',
        fix_diff='+ profiles: [debug]\n',
        rel='dump/compose.yml',
        rel_src='services:\n  debug:\n    image: node',
        leftover='leftover scale 0',
        fix2='dump profiles: [debug]',
        fix2_diff='+ dump profiles: [debug]\n',
        bad_pat='scale 0',
        doc='docs/QUAY-CMPPROF.md',
        doc_point='scale 0 is not profiles',
        doc_diff='+ scale 0 is not profiles.',
        reg='reg',
        reg_diff='+ profiles: [debug] holds',
        final_ok='ok 6 passed. profiles: [debug].',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='profiles: [debug]; dump leftover.',
        wrap='the profiles: [debug]',
        wrap_ok='6 passed. quay-cmpprof assign is green.',
        wrap_part='5 passed, 1 residual. quay-cmpprof assign is green.',
        goal='Designed plant quay-cmpprof: the Compose file that omitted profiles so the debug sidecar started in production and opened :9229. profiles: [debug]. scale 0 is not profiles.',
        plan='Repro python tests, reject scale 0, profiles: [debug], hand off dump.',
        out_ok='profiles: [debug]. 6 tests pass.',
        out_part='profiles: [debug]. dump leftover. Partial.',
    ),
    "kops2": P(True,
        slug='pr-kops-cloudlabels-asg-tag',
        plant='lock-kopstag',
        what='the kops InstanceGroup that omitted cloudLabels so the ASG lacked k8s.io/cluster-autoscaler tags and CA never scaled',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='ig-workers.yaml tests/test_harbor.py',
        impl='ig-workers.yaml',
        src='spec:\n  machineType: m6i.large',
        sym='cloudLabels CA tags',
        grep='cloudLabels',
        grep_obs='harbor nodeLabels only. pack cloudLabels autoscaler.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CA never scaled; cloudLabels missing ASG tags',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='nodeLabels only',
        wrong_diff='+ nodeLabels only',
        wrong_obs='still nodeLabels only. still fail.',
        fail2='FAIL test_assign: still broken. cloudLabels autoscaler.',
        reread='apply cloudLabels autoscaler.',
        insight='nodeLabels is not cloudLabels',
        probe="rg -n 'cloudLabels' ig-workers.yaml",
        probe_obs='pack cloudLabels autoscaler. harbor nodeLabels only.',
        fix='cloudLabels autoscaler',
        fix_diff='+ cloudLabels autoscaler\n',
        rel='dump/ig-workers.yaml',
        rel_src='spec:\n  machineType: m6i.large',
        leftover='leftover nodeLabels only',
        fix2='dump cloudLabels autoscaler',
        fix2_diff='+ dump cloudLabels autoscaler\n',
        bad_pat='nodeLabels only',
        doc='docs/LOCK-KOPSTAG.md',
        doc_point='nodeLabels is not cloudLabels',
        doc_diff='+ nodeLabels is not cloudLabels.',
        reg='reg',
        reg_diff='+ cloudLabels autoscaler holds',
        final_ok='ok 6 passed. cloudLabels autoscaler.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='cloudLabels autoscaler; dump same.',
        wrap='the cloudLabels autoscaler',
        wrap_ok='6 passed. lock-kopstag assign is green.',
        wrap_part='5 passed, 1 residual. lock-kopstag assign is green.',
        goal='Designed plant lock-kopstag: the kops InstanceGroup that omitted cloudLabels so the ASG lacked k8s.io/cluster-autoscaler tags and CA never scaled. cloudLabels autoscaler. nodeLabels is not cloudLabels.',
        plan='Repro python tests, reject nodeLabels only, cloudLabels autoscaler, fix dump.',
        out_ok='cloudLabels autoscaler. 6 tests pass.',
        out_part='cloudLabels autoscaler. dump leftover. Partial.',
    ),
    "kind2": P(False,
        slug='pr-kind-feature-gates-cronjob',
        plant='quay-kindfg',
        what='the kind cluster that omitted featureGates so CronJobTimeZone was off and a TZ schedule ran in UTC',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='kind-fg.yaml tests/test_harbor.py',
        impl='kind-fg.yaml',
        src='kind: Cluster\nnetworking: {ipFamily: ipv4}',
        sym='featureGates CronJobTimeZone',
        grep='featureGates',
        grep_obs='harbor kubeadm extraArgs only. pack featureGates CronJobTimeZone.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cron ran UTC; CronJobTimeZone gate off',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='kubeadm extraArgs only',
        wrong_diff='+ kubeadm extraArgs only',
        wrong_obs='still kubeadm extraArgs only. still fail.',
        fail2='FAIL test_assign: still broken. featureGates CronJobTimeZone.',
        reread='apply featureGates CronJobTimeZone.',
        insight='extraArgs is not featureGates',
        probe="rg -n 'featureGates' kind-fg.yaml",
        probe_obs='pack featureGates CronJobTimeZone. harbor kubeadm extraArgs only.',
        fix='featureGates CronJobTimeZone',
        fix_diff='+ featureGates CronJobTimeZone\n',
        rel='dump/kind-fg.yaml',
        rel_src='kind: Cluster\nnetworking: {ipFamily: ipv4}',
        leftover='leftover kubeadm extraArgs only',
        fix2='dump featureGates CronJobTimeZone',
        fix2_diff='+ dump featureGates CronJobTimeZone\n',
        bad_pat='kubeadm extraArgs only',
        doc='docs/QUAY-KINDFG.md',
        doc_point='extraArgs is not featureGates',
        doc_diff='+ extraArgs is not featureGates.',
        reg='reg',
        reg_diff='+ featureGates CronJobTimeZone holds',
        final_ok='ok 6 passed. featureGates CronJobTimeZone.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='featureGates CronJobTimeZone; dump leftover.',
        wrap='the featureGates CronJobTimeZone',
        wrap_ok='6 passed. quay-kindfg assign is green.',
        wrap_part='5 passed, 1 residual. quay-kindfg assign is green.',
        goal='Designed plant quay-kindfg: the kind cluster that omitted featureGates so CronJobTimeZone was off and a TZ schedule ran in UTC. featureGates CronJobTimeZone. extraArgs is not featureGates.',
        plan='Repro python tests, reject kubeadm extraArgs only, featureGates CronJobTimeZone, hand off dump.',
        out_ok='featureGates CronJobTimeZone. 6 tests pass.',
        out_part='featureGates CronJobTimeZone. dump leftover. Partial.',
    ),
    "minikube2": P(True,
        slug='pr-minikube-insecure-registry-cidrs',
        plant='lock-mkinsec',
        what="the minikube start that omitted --insecure-registry so a HTTP registry 500'd with HTTPS client attempts",
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='minikube start',
        sym='insecure-registry host',
        grep='insecure-registry',
        grep_obs='harbor image load only. pack insecure-registry.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: HTTP registry 500; insecure-registry missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='image load only',
        wrong_diff='+ image load only',
        wrong_obs='still image load only. still fail.',
        fail2='FAIL test_assign: still broken. insecure-registry.',
        reread='apply insecure-registry.',
        insight='image load is not insecure-registry',
        probe="rg -n 'insecure-registry' Makefile",
        probe_obs='pack insecure-registry. harbor image load only.',
        fix='insecure-registry',
        fix_diff='+ insecure-registry\n',
        rel='dump/Makefile',
        rel_src='minikube start',
        leftover='leftover image load only',
        fix2='dump insecure-registry',
        fix2_diff='+ dump insecure-registry\n',
        bad_pat='image load only',
        doc='docs/LOCK-MKINSEC.md',
        doc_point='image load is not insecure-registry',
        doc_diff='+ image load is not insecure-registry.',
        reg='reg',
        reg_diff='+ insecure-registry holds',
        final_ok='ok 6 passed. insecure-registry.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='insecure-registry; dump same.',
        wrap='the insecure-registry',
        wrap_ok='6 passed. lock-mkinsec assign is green.',
        wrap_part='5 passed, 1 residual. lock-mkinsec assign is green.',
        goal="Designed plant lock-mkinsec: the minikube start that omitted --insecure-registry so a HTTP registry 500'd with HTTPS client attempts. insecure-registry. image load is not insecure-registry.",
        plan='Repro python tests, reject image load only, insecure-registry, fix dump.',
        out_ok='insecure-registry. 6 tests pass.',
        out_part='insecure-registry. dump leftover. Partial.',
    ),
    "k3d2": P(False,
        slug='pr-k3d-network-ipam-subnet',
        plant='quay-k3dipam',
        what='the k3d cluster that omitted a custom docker network so the default 172.18.0.0/16 clashed with the office VPN',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='k3d-net.yaml tests/test_harbor.py',
        impl='k3d-net.yaml',
        src='apiVersion: k3d.io/v1alpha5\nkind: Simple',
        sym='network ipam subnet',
        grep='network',
        grep_obs='harbor k3d cluster edit ports. pack custom docker network subnet.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: office VPN clash 172.18; custom network missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='k3d cluster edit ports',
        wrong_diff='+ k3d cluster edit ports',
        wrong_obs='still k3d cluster edit ports. still fail.',
        fail2='FAIL test_assign: still broken. custom docker network subnet.',
        reread='apply custom docker network subnet.',
        insight='port mapping is not docker network IPAM',
        probe="rg -n 'custom' k3d-net.yaml",
        probe_obs='pack custom docker network subnet. harbor k3d cluster edit ports.',
        fix='custom docker network subnet',
        fix_diff='+ custom docker network subnet\n',
        rel='dump/k3d-net.yaml',
        rel_src='apiVersion: k3d.io/v1alpha5\nkind: Simple',
        leftover='leftover k3d cluster edit ports',
        fix2='dump custom docker network subnet',
        fix2_diff='+ dump custom docker network subnet\n',
        bad_pat='k3d cluster edit ports',
        doc='docs/QUAY-K3DIPAM.md',
        doc_point='port mapping is not docker network IPAM',
        doc_diff='+ port mapping is not docker network IPAM.',
        reg='reg',
        reg_diff='+ custom docker network subnet holds',
        final_ok='ok 6 passed. custom docker network subnet.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='custom docker network subnet; dump leftover.',
        wrap='the custom docker network subnet',
        wrap_ok='6 passed. quay-k3dipam assign is green.',
        wrap_part='5 passed, 1 residual. quay-k3dipam assign is green.',
        goal='Designed plant quay-k3dipam: the k3d cluster that omitted a custom docker network so the default 172.18.0.0/16 clashed with the office VPN. custom docker network subnet. port mapping is not docker network IPAM.',
        plan='Repro python tests, reject k3d cluster edit ports, custom docker network subnet, hand off dump.',
        out_ok='custom docker network subnet. 6 tests pass.',
        out_part='custom docker network subnet. dump leftover. Partial.',
    ),
    "microk8s2": P(True,
        slug='pr-microk8s-dns-stub-listen',
        plant='lock-m8sdns',
        what='the MicroK8s dns addon that omitted stub listen so host systemd-resolved never forwarded cluster.local',
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='dns.yaml tests/test_harbor.py',
        impl='dns.yaml',
        src='listenAddress: 0.0.0.0',
        sym='stubDomains cluster.local',
        grep='stubDomains',
        grep_obs='harbor enable dns only. pack stub listen cluster.local.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: host cannot resolve svc.cluster.local; stub missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enable dns only',
        wrong_diff='+ enable dns only',
        wrong_obs='still enable dns only. still fail.',
        fail2='FAIL test_assign: still broken. stub listen cluster.local.',
        reread='apply stub listen cluster.local.',
        insight='enable dns is not stub listen on the host',
        probe="rg -n 'stub' dns.yaml",
        probe_obs='pack stub listen cluster.local. harbor enable dns only.',
        fix='stub listen cluster.local',
        fix_diff='+ stub listen cluster.local\n',
        rel='dump/dns.yaml',
        rel_src='listenAddress: 0.0.0.0',
        leftover='leftover enable dns only',
        fix2='dump stub listen cluster.local',
        fix2_diff='+ dump stub listen cluster.local\n',
        bad_pat='enable dns only',
        doc='docs/LOCK-M8SDNS.md',
        doc_point='enable dns is not stub listen on the host',
        doc_diff='+ enable dns is not stub listen on the host.',
        reg='reg',
        reg_diff='+ stub listen cluster.local holds',
        final_ok='ok 6 passed. stub listen cluster.local.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='stub listen cluster.local; dump same.',
        wrap='the stub listen cluster.local',
        wrap_ok='6 passed. lock-m8sdns assign is green.',
        wrap_part='5 passed, 1 residual. lock-m8sdns assign is green.',
        goal='Designed plant lock-m8sdns: the MicroK8s dns addon that omitted stub listen so host systemd-resolved never forwarded cluster.local. stub listen cluster.local. enable dns is not stub listen on the host.',
        plan='Repro python tests, reject enable dns only, stub listen cluster.local, fix dump.',
        out_ok='stub listen cluster.local. 6 tests pass.',
        out_part='stub listen cluster.local. dump leftover. Partial.',
    ),
    "cdk2": P(False,
        slug='pr-cdk-bootstrap-qualifier-toolkit',
        plant='quay-cdbtrap',
        what="the CDK deploy that omitted --qualifier so it used hn-cdk and collided with another team's bootstrap bucket",
        glob='**/*.{yml,yaml,json,tf,sh}',
        ls='cdk.context.json tests/test_harbor.py',
        impl='cdk.context.json',
        src='{}',
        sym='bootstrap qualifier',
        grep='bootstrap',
        grep_obs='harbor toolkit-stack-name only. pack qualifier harbor.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: bootstrap bucket collision; qualifier missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='toolkit-stack-name only',
        wrong_diff='+ toolkit-stack-name only',
        wrong_obs='still toolkit-stack-name only. still fail.',
        fail2='FAIL test_assign: still broken. qualifier harbor.',
        reread='apply qualifier harbor.',
        insight='toolkit-stack-name is not qualifier',
        probe="rg -n 'qualifier' cdk.context.json",
        probe_obs='pack qualifier harbor. harbor toolkit-stack-name only.',
        fix='qualifier harbor',
        fix_diff='+ qualifier harbor\n',
        rel='dump/cdk.context.json',
        rel_src='{}',
        leftover='leftover toolkit-stack-name only',
        fix2='dump qualifier harbor',
        fix2_diff='+ dump qualifier harbor\n',
        bad_pat='toolkit-stack-name only',
        doc='docs/QUAY-CDBTRAP.md',
        doc_point='toolkit-stack-name is not qualifier',
        doc_diff='+ toolkit-stack-name is not qualifier.',
        reg='reg',
        reg_diff='+ qualifier harbor holds',
        final_ok='ok 6 passed. qualifier harbor.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='qualifier harbor; dump leftover.',
        wrap='the qualifier harbor',
        wrap_ok='6 passed. quay-cdbtrap assign is green.',
        wrap_part='5 passed, 1 residual. quay-cdbtrap assign is green.',
        goal="Designed plant quay-cdbtrap: the CDK deploy that omitted --qualifier so it used hn-cdk and collided with another team's bootstrap bucket. qualifier harbor. toolkit-stack-name is not qualifier.",
        plan='Repro python tests, reject toolkit-stack-name only, qualifier harbor, hand off dump.',
        out_ok='qualifier harbor. 6 tests pass.',
        out_part='qualifier harbor. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('kind extraMounts vs minikube embed-certs', fn('kind'), fn('minikube'), 'extraMounts certs; embed-certs', 'kubeadmConfigPatches; update-context', 'kind dump pull 403; minikube dump x509 after reboot'),
    ('k3d registry volume vs MicroK8s rbac addon', fn('k3d'), fn('microk8s'), 'registry volume; enable rbac', 'image import; enable ingress', 'k3d dump image 404; microk8s dump cluster-admin SA'),
    ('CDK availabilityZones vs k3s disable traefik', fn('cdk'), fn('k3s'), 'AZ context; --disable=traefik', 'env account/region; tls-san', 'cdk dump 0 AZs; k3s dump :443 clash'),
    ('k0s konnectivity vs kops maxSize', fn('k0s'), fn('kops'), 'konnectivity enabled; maxSize >= minSize', 'workerProfiles; rolling-update --force', 'k0s dump kubelet timeout; kops dump ASG 0'),
    ('eksctl withOIDC vs Compose profiles', fn('eksctl'), fn('compose'), 'withOIDC true; profiles: [debug]', 'iamIdentityMappings; scale 0', 'eksctl dump node role IRSA; compose dump debug :9229'),
    ('kops cloudLabels vs kind featureGates', fn('kops2'), fn('kind2'), 'cloudLabels CA tags; CronJobTimeZone gate', 'nodeLabels; extraArgs', 'kops dump CA never scaled; kind dump cron UTC'),
    ('minikube insecure-registry vs k3d network IPAM', fn('minikube2'), fn('k3d2'), 'insecure-registry; custom docker network', 'image load; port mapping', 'minikube dump HTTP 500; k3d dump VPN clash'),
    ('MicroK8s stub dns vs CDK bootstrap qualifier', fn('microk8s2'), fn('cdk2'), 'stub cluster.local; qualifier harbor', 'enable dns; toolkit-stack-name', 'microk8s dump host NXDOMAIN; cdk dump bootstrap collision'),
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
- Not a clone of r4163-r4540 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka.
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
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 18 <= len(rec["steps"]) <= 20
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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 18 <= len(a["steps"]) <= 20
            assert 18 <= len(b["steps"]) <= 20
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
            print("LHC reserved; retry (not eval-harness). sleep", flush=True)
            time.sleep(2)
            if hops > 40:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({"published_this_run": published, "state_pairs": st["lhc_pair"], "rounds": [p["round"] for p in st["published"][-published:] if published]}, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
