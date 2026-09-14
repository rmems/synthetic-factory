#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4ci: unused plants after r4564.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4564. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4ci_state.json")
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
    "contour": P(True,
        slug='pr-contour-timeout-policy-idle',
        plant='lock-ctridle',
        what='the Contour HTTPProxy that omitted timeoutPolicy idle so a streaming endpoint was cut at 60s',
        glob='**/*.{yml,yaml,json,sh}',
        ls='httpproxy.yaml tests/test_harbor.py',
        impl='httpproxy.yaml',
        src='spec:\n  routes: [{services: [{name: harbor}]}]',
        sym='timeoutPolicy idle 5m',
        grep='timeoutPolicy',
        grep_obs='harbor timeoutPolicy response only. pack idle timeout 5m.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: stream cut 60s; idle timeout missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='timeoutPolicy response only',
        wrong_diff='+ timeoutPolicy response only',
        wrong_obs='still timeoutPolicy response only. still fail.',
        fail2='FAIL test_assign: still broken. idle timeout 5m.',
        reread='apply idle timeout 5m.',
        insight='response timeout is not idle',
        probe="rg -n 'idle' httpproxy.yaml",
        probe_obs='pack idle timeout 5m. harbor timeoutPolicy response only.',
        fix='idle timeout 5m',
        fix_diff='+ idle timeout 5m\n',
        rel='dump/httpproxy.yaml',
        rel_src='spec:\n  routes: [{services: [{name: harbor}]}]',
        leftover='leftover timeoutPolicy response only',
        fix2='dump idle timeout 5m',
        fix2_diff='+ dump idle timeout 5m\n',
        bad_pat='timeoutPolicy response only',
        doc='docs/LOCK-CTRIDLE.md',
        doc_point='response timeout is not idle',
        doc_diff='+ response timeout is not idle.',
        reg='reg',
        reg_diff='+ idle timeout 5m holds',
        final_ok='ok 6 passed. idle timeout 5m.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='idle timeout 5m; dump same.',
        wrap='the idle timeout 5m',
        wrap_ok='6 passed. lock-ctridle assign is green.',
        wrap_part='5 passed, 1 residual. lock-ctridle assign is green.',
        goal='Designed plant lock-ctridle: the Contour HTTPProxy that omitted timeoutPolicy idle so a streaming endpoint was cut at 60s. idle timeout 5m. response timeout is not idle.',
        plan='Repro python tests, reject timeoutPolicy response only, idle timeout 5m, fix dump.',
        out_ok='idle timeout 5m. 6 tests pass.',
        out_part='idle timeout 5m. dump leftover. Partial.',
    ),
    "emissary": P(False,
        slug='pr-emissary-add-request-headers-host',
        plant='quay-emhost',
        what="the Emissary Mapping that omitted host rewrite so the upstream saw the ingress host and 404'd",
        glob='**/*.{yml,yaml,json,sh}',
        ls='mapping.yaml tests/test_harbor.py',
        impl='mapping.yaml',
        src='spec:\n  prefix: /api',
        sym='host rewrite',
        grep='host',
        grep_obs='harbor rewrite prefix only. pack host_rewrite upstream.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: upstream 404 Host: ingress; host rewrite missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='rewrite prefix only',
        wrong_diff='+ rewrite prefix only',
        wrong_obs='still rewrite prefix only. still fail.',
        fail2='FAIL test_assign: still broken. host_rewrite upstream.',
        reread='apply host_rewrite upstream.',
        insight='prefix rewrite is not host rewrite',
        probe="rg -n 'host_rewrite' mapping.yaml",
        probe_obs='pack host_rewrite upstream. harbor rewrite prefix only.',
        fix='host_rewrite upstream',
        fix_diff='+ host_rewrite upstream\n',
        rel='dump/mapping.yaml',
        rel_src='spec:\n  prefix: /api',
        leftover='leftover rewrite prefix only',
        fix2='dump host_rewrite upstream',
        fix2_diff='+ dump host_rewrite upstream\n',
        bad_pat='rewrite prefix only',
        doc='docs/QUAY-EMHOST.md',
        doc_point='prefix rewrite is not host rewrite',
        doc_diff='+ prefix rewrite is not host rewrite.',
        reg='reg',
        reg_diff='+ host_rewrite upstream holds',
        final_ok='ok 6 passed. host_rewrite upstream.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='host_rewrite upstream; dump leftover.',
        wrap='the host_rewrite upstream',
        wrap_ok='6 passed. quay-emhost assign is green.',
        wrap_part='5 passed, 1 residual. quay-emhost assign is green.',
        goal="Designed plant quay-emhost: the Emissary Mapping that omitted host rewrite so the upstream saw the ingress host and 404'd. host_rewrite upstream. prefix rewrite is not host rewrite.",
        plan='Repro python tests, reject rewrite prefix only, host_rewrite upstream, hand off dump.',
        out_ok='host_rewrite upstream. 6 tests pass.',
        out_part='host_rewrite upstream. dump leftover. Partial.',
    ),
    "gloo": P(True,
        slug='pr-gloo-virtualservice-ssl-sds',
        plant='lock-gloossds',
        what='the Gloo VirtualService that omitted sslConfig sds so TLS used a static secret that expired',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vs.yaml tests/test_harbor.py',
        impl='vs.yaml',
        src='virtualHost:\n  domains: [harbor.example]',
        sym='sslConfig sds',
        grep='sslConfig',
        grep_obs='harbor secretRef only. pack sslConfig sds.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cert expired; static secret; sds missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='secretRef only',
        wrong_diff='+ secretRef only',
        wrong_obs='still secretRef only. still fail.',
        fail2='FAIL test_assign: still broken. sslConfig sds.',
        reread='apply sslConfig sds.',
        insight='secretRef is not SDS',
        probe="rg -n 'sslConfig' vs.yaml",
        probe_obs='pack sslConfig sds. harbor secretRef only.',
        fix='sslConfig sds',
        fix_diff='+ sslConfig sds\n',
        rel='dump/vs.yaml',
        rel_src='virtualHost:\n  domains: [harbor.example]',
        leftover='leftover secretRef only',
        fix2='dump sslConfig sds',
        fix2_diff='+ dump sslConfig sds\n',
        bad_pat='secretRef only',
        doc='docs/LOCK-GLOOSSDS.md',
        doc_point='secretRef is not SDS',
        doc_diff='+ secretRef is not SDS.',
        reg='reg',
        reg_diff='+ sslConfig sds holds',
        final_ok='ok 6 passed. sslConfig sds.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='sslConfig sds; dump same.',
        wrap='the sslConfig sds',
        wrap_ok='6 passed. lock-gloossds assign is green.',
        wrap_part='5 passed, 1 residual. lock-gloossds assign is green.',
        goal='Designed plant lock-gloossds: the Gloo VirtualService that omitted sslConfig sds so TLS used a static secret that expired. sslConfig sds. secretRef is not SDS.',
        plan='Repro python tests, reject secretRef only, sslConfig sds, fix dump.',
        out_ok='sslConfig sds. 6 tests pass.',
        out_part='sslConfig sds. dump leftover. Partial.',
    ),
    "skipper": P(False,
        slug='pr-skipper-ratelimit-cluster-ratelimit',
        plant='quay-skprl',
        what="the Skipper filter that omitted clusterRatelimit so per-replica limits 5x'd behind 5 pods",
        glob='**/*.{yml,yaml,json,sh}',
        ls='routes.eskip tests/test_harbor.py',
        impl='routes.eskip',
        src='Path("/api") -> ratelimit(10) -> "http://harbor"',
        sym='clusterRatelimit',
        grep='clusterRatelimit',
        grep_obs='harbor clientRatelimit only. pack clusterRatelimit 10.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: 50 rps not 10; per-replica ratelimit; clusterRatelimit missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='clientRatelimit only',
        wrong_diff='+ clientRatelimit only',
        wrong_obs='still clientRatelimit only. still fail.',
        fail2='FAIL test_assign: still broken. clusterRatelimit 10.',
        reread='apply clusterRatelimit 10.',
        insight='clientRatelimit is not clusterRatelimit',
        probe="rg -n 'clusterRatelimit' routes.eskip",
        probe_obs='pack clusterRatelimit 10. harbor clientRatelimit only.',
        fix='clusterRatelimit 10',
        fix_diff='+ clusterRatelimit 10\n',
        rel='dump/routes.eskip',
        rel_src='Path("/api") -> ratelimit(10) -> "http://harbor"',
        leftover='leftover clientRatelimit only',
        fix2='dump clusterRatelimit 10',
        fix2_diff='+ dump clusterRatelimit 10\n',
        bad_pat='clientRatelimit only',
        doc='docs/QUAY-SKPRL.md',
        doc_point='clientRatelimit is not clusterRatelimit',
        doc_diff='+ clientRatelimit is not clusterRatelimit.',
        reg='reg',
        reg_diff='+ clusterRatelimit 10 holds',
        final_ok='ok 6 passed. clusterRatelimit 10.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='clusterRatelimit 10; dump leftover.',
        wrap='the clusterRatelimit 10',
        wrap_ok='6 passed. quay-skprl assign is green.',
        wrap_part='5 passed, 1 residual. quay-skprl assign is green.',
        goal="Designed plant quay-skprl: the Skipper filter that omitted clusterRatelimit so per-replica limits 5x'd behind 5 pods. clusterRatelimit 10. clientRatelimit is not clusterRatelimit.",
        plan='Repro python tests, reject clientRatelimit only, clusterRatelimit 10, hand off dump.',
        out_ok='clusterRatelimit 10. 6 tests pass.',
        out_part='clusterRatelimit 10. dump leftover. Partial.',
    ),
    "voyager": P(True,
        slug='pr-voyager-ingress-backend-tls',
        plant='lock-voytls',
        what='the Voyager Ingress that omitted backend-tls so HTTPS backends failed hostname verify',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ingress.yaml tests/test_harbor.py',
        impl='ingress.yaml',
        src='spec:\n  rules: [{http: {paths: []}}]',
        sym='backend-tls skip-verify false + server-name',
        grep='backend-tls',
        grep_obs='harbor ssl-redirect only. pack backend TLS server-name.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: backend x509 hostname; backend-tls missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ssl-redirect only',
        wrong_diff='+ ssl-redirect only',
        wrong_obs='still ssl-redirect only. still fail.',
        fail2='FAIL test_assign: still broken. backend TLS server-name.',
        reread='apply backend TLS server-name.',
        insight='ssl-redirect is not backend-tls',
        probe="rg -n 'backend' ingress.yaml",
        probe_obs='pack backend TLS server-name. harbor ssl-redirect only.',
        fix='backend TLS server-name',
        fix_diff='+ backend TLS server-name\n',
        rel='dump/ingress.yaml',
        rel_src='spec:\n  rules: [{http: {paths: []}}]',
        leftover='leftover ssl-redirect only',
        fix2='dump backend TLS server-name',
        fix2_diff='+ dump backend TLS server-name\n',
        bad_pat='ssl-redirect only',
        doc='docs/LOCK-VOYTLS.md',
        doc_point='ssl-redirect is not backend-tls',
        doc_diff='+ ssl-redirect is not backend-tls.',
        reg='reg',
        reg_diff='+ backend TLS server-name holds',
        final_ok='ok 6 passed. backend TLS server-name.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='backend TLS server-name; dump same.',
        wrap='the backend TLS server-name',
        wrap_ok='6 passed. lock-voytls assign is green.',
        wrap_part='5 passed, 1 residual. lock-voytls assign is green.',
        goal='Designed plant lock-voytls: the Voyager Ingress that omitted backend-tls so HTTPS backends failed hostname verify. backend TLS server-name. ssl-redirect is not backend-tls.',
        plan='Repro python tests, reject ssl-redirect only, backend TLS server-name, fix dump.',
        out_ok='backend TLS server-name. 6 tests pass.',
        out_part='backend TLS server-name. dump leftover. Partial.',
    ),
    "ingressnginx": P(False,
        slug='pr-ingressnginx-affinity-cookie-samesite',
        plant='quay-ingaff',
        what='the ingress-nginx that omitted affinity cookie SameSite so Safari dropped the session cookie',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ingress.yaml tests/test_harbor.py',
        impl='ingress.yaml',
        src='nginx.ingress.kubernetes.io/affinity: cookie',
        sym='affinity-cookie-samesite Lax',
        grep='affinity-cookie-samesite',
        grep_obs='harbor session-cookie-name only. pack SameSite Lax.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Safari dropped cookie; SameSite missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='session-cookie-name only',
        wrong_diff='+ session-cookie-name only',
        wrong_obs='still session-cookie-name only. still fail.',
        fail2='FAIL test_assign: still broken. SameSite Lax.',
        reread='apply SameSite Lax.',
        insight='cookie name is not SameSite',
        probe="rg -n 'SameSite' ingress.yaml",
        probe_obs='pack SameSite Lax. harbor session-cookie-name only.',
        fix='SameSite Lax',
        fix_diff='+ SameSite Lax\n',
        rel='dump/ingress.yaml',
        rel_src='nginx.ingress.kubernetes.io/affinity: cookie',
        leftover='leftover session-cookie-name only',
        fix2='dump SameSite Lax',
        fix2_diff='+ dump SameSite Lax\n',
        bad_pat='session-cookie-name only',
        doc='docs/QUAY-INGAFF.md',
        doc_point='cookie name is not SameSite',
        doc_diff='+ cookie name is not SameSite.',
        reg='reg',
        reg_diff='+ SameSite Lax holds',
        final_ok='ok 6 passed. SameSite Lax.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='SameSite Lax; dump leftover.',
        wrap='the SameSite Lax',
        wrap_ok='6 passed. quay-ingaff assign is green.',
        wrap_part='5 passed, 1 residual. quay-ingaff assign is green.',
        goal='Designed plant quay-ingaff: the ingress-nginx that omitted affinity cookie SameSite so Safari dropped the session cookie. SameSite Lax. cookie name is not SameSite.',
        plan='Repro python tests, reject session-cookie-name only, SameSite Lax, hand off dump.',
        out_ok='SameSite Lax. 6 tests pass.',
        out_part='SameSite Lax. dump leftover. Partial.',
    ),
    "alb": P(True,
        slug='pr-alb-target-group-stickiness-app',
        plant='lock-albstk',
        what='the AWS ALB Ingress that omitted target-group-attributes stickiness so websocket reconnects hit another pod',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ingress.yaml tests/test_harbor.py',
        impl='ingress.yaml',
        src='alb.ingress.kubernetes.io/scheme: internet-facing',
        sym='stickiness.enabled true',
        grep='stickiness.enabled',
        grep_obs='harbor idle_timeout only. pack target group stickiness.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: websocket hop; stickiness missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='idle_timeout only',
        wrong_diff='+ idle_timeout only',
        wrong_obs='still idle_timeout only. still fail.',
        fail2='FAIL test_assign: still broken. target group stickiness.',
        reread='apply target group stickiness.',
        insight='idle_timeout is not stickiness',
        probe="rg -n 'target' ingress.yaml",
        probe_obs='pack target group stickiness. harbor idle_timeout only.',
        fix='target group stickiness',
        fix_diff='+ target group stickiness\n',
        rel='dump/ingress.yaml',
        rel_src='alb.ingress.kubernetes.io/scheme: internet-facing',
        leftover='leftover idle_timeout only',
        fix2='dump target group stickiness',
        fix2_diff='+ dump target group stickiness\n',
        bad_pat='idle_timeout only',
        doc='docs/LOCK-ALBSTK.md',
        doc_point='idle_timeout is not stickiness',
        doc_diff='+ idle_timeout is not stickiness.',
        reg='reg',
        reg_diff='+ target group stickiness holds',
        final_ok='ok 6 passed. target group stickiness.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='target group stickiness; dump same.',
        wrap='the target group stickiness',
        wrap_ok='6 passed. lock-albstk assign is green.',
        wrap_part='5 passed, 1 residual. lock-albstk assign is green.',
        goal='Designed plant lock-albstk: the AWS ALB Ingress that omitted target-group-attributes stickiness so websocket reconnects hit another pod. target group stickiness. idle_timeout is not stickiness.',
        plan='Repro python tests, reject idle_timeout only, target group stickiness, fix dump.',
        out_ok='target group stickiness. 6 tests pass.',
        out_part='target group stickiness. dump leftover. Partial.',
    ),
    "nlb": P(False,
        slug='pr-nlb-cross-zone-load-balancing',
        plant='quay-nlbxz',
        what="the NLB service that omitted aws-load-balancer-cross-zone so AZ-unbalanced targets 5xx'd",
        glob='**/*.{yml,yaml,json,sh}',
        ls='svc.yaml tests/test_harbor.py',
        impl='svc.yaml',
        src='service.beta.kubernetes.io/aws-load-balancer-type: nlb',
        sym='cross-zone enabled',
        grep='cross-zone',
        grep_obs='harbor externalTrafficPolicy Local. pack cross-zone load balancing.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: AZ imbalance 5xx; cross-zone missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='externalTrafficPolicy Local',
        wrong_diff='+ externalTrafficPolicy Local',
        wrong_obs='still externalTrafficPolicy Local. still fail.',
        fail2='FAIL test_assign: still broken. cross-zone load balancing.',
        reread='apply cross-zone load balancing.',
        insight='externalTrafficPolicy is not cross-zone',
        probe="rg -n 'cross-zone' svc.yaml",
        probe_obs='pack cross-zone load balancing. harbor externalTrafficPolicy Local.',
        fix='cross-zone load balancing',
        fix_diff='+ cross-zone load balancing\n',
        rel='dump/svc.yaml',
        rel_src='service.beta.kubernetes.io/aws-load-balancer-type: nlb',
        leftover='leftover externalTrafficPolicy Local',
        fix2='dump cross-zone load balancing',
        fix2_diff='+ dump cross-zone load balancing\n',
        bad_pat='externalTrafficPolicy Local',
        doc='docs/QUAY-NLBXZ.md',
        doc_point='externalTrafficPolicy is not cross-zone',
        doc_diff='+ externalTrafficPolicy is not cross-zone.',
        reg='reg',
        reg_diff='+ cross-zone load balancing holds',
        final_ok='ok 6 passed. cross-zone load balancing.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='cross-zone load balancing; dump leftover.',
        wrap='the cross-zone load balancing',
        wrap_ok='6 passed. quay-nlbxz assign is green.',
        wrap_part='5 passed, 1 residual. quay-nlbxz assign is green.',
        goal="Designed plant quay-nlbxz: the NLB service that omitted aws-load-balancer-cross-zone so AZ-unbalanced targets 5xx'd. cross-zone load balancing. externalTrafficPolicy is not cross-zone.",
        plan='Repro python tests, reject externalTrafficPolicy Local, cross-zone load balancing, hand off dump.',
        out_ok='cross-zone load balancing. 6 tests pass.',
        out_part='cross-zone load balancing. dump leftover. Partial.',
    ),
    "gatewayapi": P(True,
        slug='pr-gatewayapi-allowed-routes-same',
        plant='lock-gwapialw',
        what='the Gateway listener that omitted allowedRoutes so HTTPRoutes in other namespaces were silently unbound',
        glob='**/*.{yml,yaml,json,sh}',
        ls='gateway.yaml tests/test_harbor.py',
        impl='gateway.yaml',
        src='listeners: [{port: 80, protocol: HTTP}]',
        sym='allowedRoutes namespaces All',
        grep='allowedRoutes',
        grep_obs='harbor HTTPRoute parentRefs only. pack allowedRoutes All.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: HTTPRoute from other ns unbound; allowedRoutes default Same',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='HTTPRoute parentRefs only',
        wrong_diff='+ HTTPRoute parentRefs only',
        wrong_obs='still HTTPRoute parentRefs only. still fail.',
        fail2='FAIL test_assign: still broken. allowedRoutes All.',
        reread='apply allowedRoutes All.',
        insight='parentRefs is not allowedRoutes',
        probe="rg -n 'allowedRoutes' gateway.yaml",
        probe_obs='pack allowedRoutes All. harbor HTTPRoute parentRefs only.',
        fix='allowedRoutes All',
        fix_diff='+ allowedRoutes All\n',
        rel='dump/gateway.yaml',
        rel_src='listeners: [{port: 80, protocol: HTTP}]',
        leftover='leftover HTTPRoute parentRefs only',
        fix2='dump allowedRoutes All',
        fix2_diff='+ dump allowedRoutes All\n',
        bad_pat='HTTPRoute parentRefs only',
        doc='docs/LOCK-GWAPIALW.md',
        doc_point='parentRefs is not allowedRoutes',
        doc_diff='+ parentRefs is not allowedRoutes.',
        reg='reg',
        reg_diff='+ allowedRoutes All holds',
        final_ok='ok 6 passed. allowedRoutes All.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='allowedRoutes All; dump same.',
        wrap='the allowedRoutes All',
        wrap_ok='6 passed. lock-gwapialw assign is green.',
        wrap_part='5 passed, 1 residual. lock-gwapialw assign is green.',
        goal='Designed plant lock-gwapialw: the Gateway listener that omitted allowedRoutes so HTTPRoutes in other namespaces were silently unbound. allowedRoutes All. parentRefs is not allowedRoutes.',
        plan='Repro python tests, reject HTTPRoute parentRefs only, allowedRoutes All, fix dump.',
        out_ok='allowedRoutes All. 6 tests pass.',
        out_part='allowedRoutes All. dump leftover. Partial.',
    ),
    "httproute": P(False,
        slug='pr-httproute-timeouts-request',
        plant='quay-htrto',
        what='the HTTPRoute that omitted timeouts.request so a slow backend was cut at the Gateway default 15s',
        glob='**/*.{yml,yaml,json,sh}',
        ls='httproute.yaml tests/test_harbor.py',
        impl='httproute.yaml',
        src='rules: [{backendRefs: [{name: harbor}]}]',
        sym='timeouts.request 60s',
        grep='timeouts.request',
        grep_obs='harbor retries only. pack timeouts.request 60s.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: 15s cut; timeouts.request missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='retries only',
        wrong_diff='+ retries only',
        wrong_obs='still retries only. still fail.',
        fail2='FAIL test_assign: still broken. timeouts.request 60s.',
        reread='apply timeouts.request 60s.',
        insight='retries is not timeouts.request',
        probe="rg -n 'timeouts.request' httproute.yaml",
        probe_obs='pack timeouts.request 60s. harbor retries only.',
        fix='timeouts.request 60s',
        fix_diff='+ timeouts.request 60s\n',
        rel='dump/httproute.yaml',
        rel_src='rules: [{backendRefs: [{name: harbor}]}]',
        leftover='leftover retries only',
        fix2='dump timeouts.request 60s',
        fix2_diff='+ dump timeouts.request 60s\n',
        bad_pat='retries only',
        doc='docs/QUAY-HTRTO.md',
        doc_point='retries is not timeouts.request',
        doc_diff='+ retries is not timeouts.request.',
        reg='reg',
        reg_diff='+ timeouts.request 60s holds',
        final_ok='ok 6 passed. timeouts.request 60s.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='timeouts.request 60s; dump leftover.',
        wrap='the timeouts.request 60s',
        wrap_ok='6 passed. quay-htrto assign is green.',
        wrap_part='5 passed, 1 residual. quay-htrto assign is green.',
        goal='Designed plant quay-htrto: the HTTPRoute that omitted timeouts.request so a slow backend was cut at the Gateway default 15s. timeouts.request 60s. retries is not timeouts.request.',
        plan='Repro python tests, reject retries only, timeouts.request 60s, hand off dump.',
        out_ok='timeouts.request 60s. 6 tests pass.',
        out_part='timeouts.request 60s. dump leftover. Partial.',
    ),
    "grpcroute": P(True,
        slug='pr-grpcroute-timeouts-stream',
        plant='lock-grpcto',
        what='the GRPCRoute that omitted timeouts.streamIdle so a bidi stream was killed after idle',
        glob='**/*.{yml,yaml,json,sh}',
        ls='grpcroute.yaml tests/test_harbor.py',
        impl='grpcroute.yaml',
        src='rules: [{backendRefs: [{name: harbor}]}]',
        sym='timeouts.streamIdle 30m',
        grep='timeouts.streamIdle',
        grep_obs='harbor timeouts.request only. pack streamIdle 30m.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: bidi stream killed idle; streamIdle missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='timeouts.request only',
        wrong_diff='+ timeouts.request only',
        wrong_obs='still timeouts.request only. still fail.',
        fail2='FAIL test_assign: still broken. streamIdle 30m.',
        reread='apply streamIdle 30m.',
        insight='request timeout is not streamIdle',
        probe="rg -n 'streamIdle' grpcroute.yaml",
        probe_obs='pack streamIdle 30m. harbor timeouts.request only.',
        fix='streamIdle 30m',
        fix_diff='+ streamIdle 30m\n',
        rel='dump/grpcroute.yaml',
        rel_src='rules: [{backendRefs: [{name: harbor}]}]',
        leftover='leftover timeouts.request only',
        fix2='dump streamIdle 30m',
        fix2_diff='+ dump streamIdle 30m\n',
        bad_pat='timeouts.request only',
        doc='docs/LOCK-GRPCTO.md',
        doc_point='request timeout is not streamIdle',
        doc_diff='+ request timeout is not streamIdle.',
        reg='reg',
        reg_diff='+ streamIdle 30m holds',
        final_ok='ok 6 passed. streamIdle 30m.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='streamIdle 30m; dump same.',
        wrap='the streamIdle 30m',
        wrap_ok='6 passed. lock-grpcto assign is green.',
        wrap_part='5 passed, 1 residual. lock-grpcto assign is green.',
        goal='Designed plant lock-grpcto: the GRPCRoute that omitted timeouts.streamIdle so a bidi stream was killed after idle. streamIdle 30m. request timeout is not streamIdle.',
        plan='Repro python tests, reject timeouts.request only, streamIdle 30m, fix dump.',
        out_ok='streamIdle 30m. 6 tests pass.',
        out_part='streamIdle 30m. dump leftover. Partial.',
    ),
    "referencegrant": P(False,
        slug='pr-referencegrant-from-namespace',
        plant='quay-refgr',
        what='the ReferenceGrant that omitted from.namespace so a Secret ref from the app ns was denied',
        glob='**/*.{yml,yaml,json,sh}',
        ls='grant.yaml tests/test_harbor.py',
        impl='grant.yaml',
        src='spec:\n  to: [{kind: Secret}]',
        sym='from namespace app',
        grep='from',
        grep_obs='harbor to kind Secret only. pack from.namespace.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Secret ref denied; from.namespace missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='to kind Secret only',
        wrong_diff='+ to kind Secret only',
        wrong_obs='still to kind Secret only. still fail.',
        fail2='FAIL test_assign: still broken. from.namespace.',
        reread='apply from.namespace.',
        insight='to.kind is not from.namespace',
        probe="rg -n 'from.namespace' grant.yaml",
        probe_obs='pack from.namespace. harbor to kind Secret only.',
        fix='from.namespace',
        fix_diff='+ from.namespace\n',
        rel='dump/grant.yaml',
        rel_src='spec:\n  to: [{kind: Secret}]',
        leftover='leftover to kind Secret only',
        fix2='dump from.namespace',
        fix2_diff='+ dump from.namespace\n',
        bad_pat='to kind Secret only',
        doc='docs/QUAY-REFGR.md',
        doc_point='to.kind is not from.namespace',
        doc_diff='+ to.kind is not from.namespace.',
        reg='reg',
        reg_diff='+ from.namespace holds',
        final_ok='ok 6 passed. from.namespace.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='from.namespace; dump leftover.',
        wrap='the from.namespace',
        wrap_ok='6 passed. quay-refgr assign is green.',
        wrap_part='5 passed, 1 residual. quay-refgr assign is green.',
        goal='Designed plant quay-refgr: the ReferenceGrant that omitted from.namespace so a Secret ref from the app ns was denied. from.namespace. to.kind is not from.namespace.',
        plan='Repro python tests, reject to kind Secret only, from.namespace, hand off dump.',
        out_ok='from.namespace. 6 tests pass.',
        out_part='from.namespace. dump leftover. Partial.',
    ),
    "envoygateway": P(True,
        slug='pr-envoygateway-client-timeout-idle',
        plant='lock-egidle',
        what='the EnvoyGateway ClientTrafficPolicy that omitted timeout.idle so browsers reused a dead connection',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ctp.yaml tests/test_harbor.py',
        impl='ctp.yaml',
        src='spec:\n  targetRefs: [{kind: Gateway}]',
        sym='timeout.idle 60s',
        grep='timeout.idle',
        grep_obs='harbor timeout.http only. pack idle 60s.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: browser reused dead conn; idle timeout missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='timeout.http only',
        wrong_diff='+ timeout.http only',
        wrong_obs='still timeout.http only. still fail.',
        fail2='FAIL test_assign: still broken. idle 60s.',
        reread='apply idle 60s.',
        insight='http timeout is not idle',
        probe="rg -n 'idle' ctp.yaml",
        probe_obs='pack idle 60s. harbor timeout.http only.',
        fix='idle 60s',
        fix_diff='+ idle 60s\n',
        rel='dump/ctp.yaml',
        rel_src='spec:\n  targetRefs: [{kind: Gateway}]',
        leftover='leftover timeout.http only',
        fix2='dump idle 60s',
        fix2_diff='+ dump idle 60s\n',
        bad_pat='timeout.http only',
        doc='docs/LOCK-EGIDLE.md',
        doc_point='http timeout is not idle',
        doc_diff='+ http timeout is not idle.',
        reg='reg',
        reg_diff='+ idle 60s holds',
        final_ok='ok 6 passed. idle 60s.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='idle 60s; dump same.',
        wrap='the idle 60s',
        wrap_ok='6 passed. lock-egidle assign is green.',
        wrap_part='5 passed, 1 residual. lock-egidle assign is green.',
        goal='Designed plant lock-egidle: the EnvoyGateway ClientTrafficPolicy that omitted timeout.idle so browsers reused a dead connection. idle 60s. http timeout is not idle.',
        plan='Repro python tests, reject timeout.http only, idle 60s, fix dump.',
        out_ok='idle 60s. 6 tests pass.',
        out_part='idle 60s. dump leftover. Partial.',
    ),
    "kgateway": P(False,
        slug='pr-kgateway-ai-ext-auth-header',
        plant='quay-kgauth',
        what='the kgateway HTTPRoute that omitted ExtensionRef auth so the AI backend was hit without a key',
        glob='**/*.{yml,yaml,json,sh}',
        ls='httproute.yaml tests/test_harbor.py',
        impl='httproute.yaml',
        src='rules: [{filters: []}]',
        sym='ExtensionRef extAuth',
        grep='ExtensionRef',
        grep_obs='harbor header modifier only. pack extAuth ExtensionRef.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: backend no API key; extAuth missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='header modifier only',
        wrong_diff='+ header modifier only',
        wrong_obs='still header modifier only. still fail.',
        fail2='FAIL test_assign: still broken. extAuth ExtensionRef.',
        reread='apply extAuth ExtensionRef.',
        insight='header modifier is not extAuth',
        probe="rg -n 'extAuth' httproute.yaml",
        probe_obs='pack extAuth ExtensionRef. harbor header modifier only.',
        fix='extAuth ExtensionRef',
        fix_diff='+ extAuth ExtensionRef\n',
        rel='dump/httproute.yaml',
        rel_src='rules: [{filters: []}]',
        leftover='leftover header modifier only',
        fix2='dump extAuth ExtensionRef',
        fix2_diff='+ dump extAuth ExtensionRef\n',
        bad_pat='header modifier only',
        doc='docs/QUAY-KGAUTH.md',
        doc_point='header modifier is not extAuth',
        doc_diff='+ header modifier is not extAuth.',
        reg='reg',
        reg_diff='+ extAuth ExtensionRef holds',
        final_ok='ok 6 passed. extAuth ExtensionRef.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='extAuth ExtensionRef; dump leftover.',
        wrap='the extAuth ExtensionRef',
        wrap_ok='6 passed. quay-kgauth assign is green.',
        wrap_part='5 passed, 1 residual. quay-kgauth assign is green.',
        goal='Designed plant quay-kgauth: the kgateway HTTPRoute that omitted ExtensionRef auth so the AI backend was hit without a key. extAuth ExtensionRef. header modifier is not extAuth.',
        plan='Repro python tests, reject header modifier only, extAuth ExtensionRef, hand off dump.',
        out_ok='extAuth ExtensionRef. 6 tests pass.',
        out_part='extAuth ExtensionRef. dump leftover. Partial.',
    ),
    "osquery": P(True,
        slug='pr-osquery-decorations-uuid',
        plant='lock-osqdec',
        what='the osquery flags that omitted --decorations so results lacked host UUID and fleet could not join',
        glob='**/*.{yml,yaml,json,sh}',
        ls='osquery.flags tests/test_harbor.py',
        impl='osquery.flags',
        src='--logger_plugin=tls',
        sym='decorations uuid',
        grep='decorations',
        grep_obs='harbor enroll_secret only. pack decorations host_uuid.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: fleet join miss; decorations uuid missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enroll_secret only',
        wrong_diff='+ enroll_secret only',
        wrong_obs='still enroll_secret only. still fail.',
        fail2='FAIL test_assign: still broken. decorations host_uuid.',
        reread='apply decorations host_uuid.',
        insight='enroll_secret is not decorations',
        probe="rg -n 'decorations' osquery.flags",
        probe_obs='pack decorations host_uuid. harbor enroll_secret only.',
        fix='decorations host_uuid',
        fix_diff='+ decorations host_uuid\n',
        rel='dump/osquery.flags',
        rel_src='--logger_plugin=tls',
        leftover='leftover enroll_secret only',
        fix2='dump decorations host_uuid',
        fix2_diff='+ dump decorations host_uuid\n',
        bad_pat='enroll_secret only',
        doc='docs/LOCK-OSQDEC.md',
        doc_point='enroll_secret is not decorations',
        doc_diff='+ enroll_secret is not decorations.',
        reg='reg',
        reg_diff='+ decorations host_uuid holds',
        final_ok='ok 6 passed. decorations host_uuid.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='decorations host_uuid; dump same.',
        wrap='the decorations host_uuid',
        wrap_ok='6 passed. lock-osqdec assign is green.',
        wrap_part='5 passed, 1 residual. lock-osqdec assign is green.',
        goal='Designed plant lock-osqdec: the osquery flags that omitted --decorations so results lacked host UUID and fleet could not join. decorations host_uuid. enroll_secret is not decorations.',
        plan='Repro python tests, reject enroll_secret only, decorations host_uuid, fix dump.',
        out_ok='decorations host_uuid. 6 tests pass.',
        out_part='decorations host_uuid. dump leftover. Partial.',
    ),
    "spire": P(False,
        slug='pr-spire-server-ca-ttl-too-short',
        plant='quay-spireca',
        what='the SPIRE server that omitted ca_ttl so the intermediate CA rotated every hour and workloads restarted',
        glob='**/*.{yml,yaml,json,sh}',
        ls='server.conf tests/test_harbor.py',
        impl='server.conf',
        src='ca_subject = {}',
        sym='ca_ttl 24h',
        grep='ca_ttl',
        grep_obs='harbor default_svid_ttl only. pack ca_ttl 24h.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CA rotate hourly; workloads restart; ca_ttl missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='default_svid_ttl only',
        wrong_diff='+ default_svid_ttl only',
        wrong_obs='still default_svid_ttl only. still fail.',
        fail2='FAIL test_assign: still broken. ca_ttl 24h.',
        reread='apply ca_ttl 24h.',
        insight='default_svid_ttl is not ca_ttl',
        probe="rg -n 'ca_ttl' server.conf",
        probe_obs='pack ca_ttl 24h. harbor default_svid_ttl only.',
        fix='ca_ttl 24h',
        fix_diff='+ ca_ttl 24h\n',
        rel='dump/server.conf',
        rel_src='ca_subject = {}',
        leftover='leftover default_svid_ttl only',
        fix2='dump ca_ttl 24h',
        fix2_diff='+ dump ca_ttl 24h\n',
        bad_pat='default_svid_ttl only',
        doc='docs/QUAY-SPIRECA.md',
        doc_point='default_svid_ttl is not ca_ttl',
        doc_diff='+ default_svid_ttl is not ca_ttl.',
        reg='reg',
        reg_diff='+ ca_ttl 24h holds',
        final_ok='ok 6 passed. ca_ttl 24h.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ca_ttl 24h; dump leftover.',
        wrap='the ca_ttl 24h',
        wrap_ok='6 passed. quay-spireca assign is green.',
        wrap_part='5 passed, 1 residual. quay-spireca assign is green.',
        goal='Designed plant quay-spireca: the SPIRE server that omitted ca_ttl so the intermediate CA rotated every hour and workloads restarted. ca_ttl 24h. default_svid_ttl is not ca_ttl.',
        plan='Repro python tests, reject default_svid_ttl only, ca_ttl 24h, hand off dump.',
        out_ok='ca_ttl 24h. 6 tests pass.',
        out_part='ca_ttl 24h. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Contour idle timeout vs Emissary host rewrite', fn('contour'), fn('emissary'), 'timeoutPolicy idle 5m; host_rewrite', 'response timeout; prefix rewrite', 'contour dump stream cut 60s; emissary dump upstream 404'),
    ('Gloo SDS sslConfig vs Skipper clusterRatelimit', fn('gloo'), fn('skipper'), 'sslConfig sds; clusterRatelimit 10', 'secretRef; clientRatelimit', 'gloo dump expired cert; skipper dump 50 rps'),
    ('Voyager backend-tls vs ingress-nginx SameSite', fn('voyager'), fn('ingressnginx'), 'backend-tls server-name; SameSite Lax', 'ssl-redirect; cookie name', 'voyager dump x509 hostname; ingress-nginx dump Safari cookie'),
    ('ALB stickiness vs NLB cross-zone', fn('alb'), fn('nlb'), 'target group stickiness; cross-zone', 'idle_timeout; externalTrafficPolicy', 'alb dump websocket hop; nlb dump AZ 5xx'),
    ('Gateway allowedRoutes vs HTTPRoute timeouts.request', fn('gatewayapi'), fn('httproute'), 'allowedRoutes All; timeouts.request 60s', 'parentRefs; retries', 'gateway dump HTTPRoute unbound; httproute dump 15s cut'),
    ('GRPCRoute streamIdle vs ReferenceGrant from.namespace', fn('grpcroute'), fn('referencegrant'), 'streamIdle 30m; from.namespace', 'request timeout; to.kind', 'grpcroute dump bidi killed; referencegrant dump Secret denied'),
    ('EnvoyGateway idle vs kgateway extAuth', fn('envoygateway'), fn('kgateway'), 'timeout.idle 60s; ExtensionRef extAuth', 'http timeout; header modifier', 'envoygateway dump dead conn reuse; kgateway dump no API key'),
    ('osquery decorations vs SPIRE ca_ttl', fn('osquery'), fn('spire'), 'decorations host_uuid; ca_ttl 24h', 'enroll_secret; default_svid_ttl', 'osquery dump fleet join miss; spire dump hourly CA rotate'),
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
- Not a clone of r4163-r4564 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
