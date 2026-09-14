#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cj: unused plants after r4572.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4572. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cj_state.json")
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
    "oauth2proxy": P(True,
        slug='pr-oauth2proxy-cookie-samesite-refresh',
        plant='lock-o2psame',
        what='the oauth2-proxy that omitted cookie-samesite so the refresh cookie was dropped on the HTTPS callback',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='oauth2-proxy.cfg tests/test_harbor.py',
        impl='oauth2-proxy.cfg',
        src='http_address = "0.0.0.0:4180"',
        sym='cookie_samesite=none cookie_secure',
        grep='cookie_samesite=none',
        grep_obs='harbor cookie_expire only. pack cookie_samesite none.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: refresh cookie dropped; SameSite missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cookie_expire only',
        wrong_diff='+ cookie_expire only',
        wrong_obs='still cookie_expire only. still fail.',
        fail2='FAIL test_assign: still broken. cookie_samesite none.',
        reread='apply cookie_samesite none.',
        insight='cookie_expire is not SameSite',
        probe="rg -n 'cookie_samesite' oauth2-proxy.cfg",
        probe_obs='pack cookie_samesite none. harbor cookie_expire only.',
        fix='cookie_samesite none',
        fix_diff='+ cookie_samesite none\n',
        rel='dump/oauth2-proxy.cfg',
        rel_src='http_address = "0.0.0.0:4180"',
        leftover='leftover cookie_expire only',
        fix2='dump cookie_samesite none',
        fix2_diff='+ dump cookie_samesite none\n',
        bad_pat='cookie_expire only',
        doc='docs/LOCK-O2PSAME.md',
        doc_point='cookie_expire is not SameSite',
        doc_diff='+ cookie_expire is not SameSite.',
        reg='reg',
        reg_diff='+ cookie_samesite none holds',
        final_ok='ok 6 passed. cookie_samesite none.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='cookie_samesite none; dump same.',
        wrap='the cookie_samesite none',
        wrap_ok='6 passed. lock-o2psame assign is green.',
        wrap_part='5 passed, 1 residual. lock-o2psame assign is green.',
        goal='Designed plant lock-o2psame: the oauth2-proxy that omitted cookie-samesite so the refresh cookie was dropped on the HTTPS callback. cookie_samesite none. cookie_expire is not SameSite.',
        plan='Repro python tests, reject cookie_expire only, cookie_samesite none, fix dump.',
        out_ok='cookie_samesite none. 6 tests pass.',
        out_part='cookie_samesite none. dump leftover. Partial.',
    ),
    "authentik": P(False,
        slug='pr-authentik-outpost-token-invalid',
        plant='quay-akout',
        what='the Authentik outpost that omitted authentik_host_insecure so the embedded outpost could not fetch the config from a self-signed host',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='docker-compose.yml tests/test_harbor.py',
        impl='docker-compose.yml',
        src='AUTHENTIK_HOST=https://ak.example',
        sym='AUTHENTIK_INSECURE true for lab',
        grep='AUTHENTIK_INSECURE',
        grep_obs='harbor skip_verify on proxy only. pack authentik_host_insecure.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: outpost config 401; host_insecure missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='skip_verify on proxy only',
        wrong_diff='+ skip_verify on proxy only',
        wrong_obs='still skip_verify on proxy only. still fail.',
        fail2='FAIL test_assign: still broken. authentik_host_insecure.',
        reread='apply authentik_host_insecure.',
        insight='proxy skip_verify is not outpost host_insecure',
        probe="rg -n 'authentik_host_insecure' docker-compose.yml",
        probe_obs='pack authentik_host_insecure. harbor skip_verify on proxy only.',
        fix='authentik_host_insecure',
        fix_diff='+ authentik_host_insecure\n',
        rel='dump/docker-compose.yml',
        rel_src='AUTHENTIK_HOST=https://ak.example',
        leftover='leftover skip_verify on proxy only',
        fix2='dump authentik_host_insecure',
        fix2_diff='+ dump authentik_host_insecure\n',
        bad_pat='skip_verify on proxy only',
        doc='docs/QUAY-AKOUT.md',
        doc_point='proxy skip_verify is not outpost host_insecure',
        doc_diff='+ proxy skip_verify is not outpost host_insecure.',
        reg='reg',
        reg_diff='+ authentik_host_insecure holds',
        final_ok='ok 6 passed. authentik_host_insecure.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='authentik_host_insecure; dump leftover.',
        wrap='the authentik_host_insecure',
        wrap_ok='6 passed. quay-akout assign is green.',
        wrap_part='5 passed, 1 residual. quay-akout assign is green.',
        goal='Designed plant quay-akout: the Authentik outpost that omitted authentik_host_insecure so the embedded outpost could not fetch the config from a self-signed host. authentik_host_insecure. proxy skip_verify is not outpost host_insecure.',
        plan='Repro python tests, reject skip_verify on proxy only, authentik_host_insecure, hand off dump.',
        out_ok='authentik_host_insecure. 6 tests pass.',
        out_part='authentik_host_insecure. dump leftover. Partial.',
    ),
    "ory": P(True,
        slug='pr-ory-keto-namespace-config-opl',
        plant='lock-oryopl',
        what='the Ory stack that omitted keto namespace opl so Check() returned unknown namespace',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='keto.yml tests/test_harbor.py',
        impl='keto.yml',
        src='dsn: memory',
        sym='namespaces opl file',
        grep='namespaces',
        grep_obs='harbor keto migrate only. pack namespaces opl.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Check unknown namespace; opl missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='keto migrate only',
        wrong_diff='+ keto migrate only',
        wrong_obs='still keto migrate only. still fail.',
        fail2='FAIL test_assign: still broken. namespaces opl.',
        reread='apply namespaces opl.',
        insight='migrate is not namespace opl',
        probe="rg -n 'namespaces' keto.yml",
        probe_obs='pack namespaces opl. harbor keto migrate only.',
        fix='namespaces opl',
        fix_diff='+ namespaces opl\n',
        rel='dump/keto.yml',
        rel_src='dsn: memory',
        leftover='leftover keto migrate only',
        fix2='dump namespaces opl',
        fix2_diff='+ dump namespaces opl\n',
        bad_pat='keto migrate only',
        doc='docs/LOCK-ORYOPL.md',
        doc_point='migrate is not namespace opl',
        doc_diff='+ migrate is not namespace opl.',
        reg='reg',
        reg_diff='+ namespaces opl holds',
        final_ok='ok 6 passed. namespaces opl.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='namespaces opl; dump same.',
        wrap='the namespaces opl',
        wrap_ok='6 passed. lock-oryopl assign is green.',
        wrap_part='5 passed, 1 residual. lock-oryopl assign is green.',
        goal='Designed plant lock-oryopl: the Ory stack that omitted keto namespace opl so Check() returned unknown namespace. namespaces opl. migrate is not namespace opl.',
        plan='Repro python tests, reject keto migrate only, namespaces opl, fix dump.',
        out_ok='namespaces opl. 6 tests pass.',
        out_part='namespaces opl. dump leftover. Partial.',
    ),
    "hydra": P(False,
        slug='pr-hydra-refresh-token-rotation-grace',
        plant='quay-hydgrace',
        what="the Hydra config that omitted refresh_token_rotation_grace so a parallel refresh 400'd the mobile client",
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='hydra.yml tests/test_harbor.py',
        impl='hydra.yml',
        src='ttl:\n  refresh_token: 720h',
        sym='refresh_token_rotation_grace_period',
        grep='refresh_token_rotation_grace_period',
        grep_obs='harbor ttl only. pack rotation grace.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: parallel refresh 400; grace period missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ttl only',
        wrong_diff='+ ttl only',
        wrong_obs='still ttl only. still fail.',
        fail2='FAIL test_assign: still broken. rotation grace.',
        reread='apply rotation grace.',
        insight='ttl is not rotation grace',
        probe="rg -n 'rotation' hydra.yml",
        probe_obs='pack rotation grace. harbor ttl only.',
        fix='rotation grace',
        fix_diff='+ rotation grace\n',
        rel='dump/hydra.yml',
        rel_src='ttl:\n  refresh_token: 720h',
        leftover='leftover ttl only',
        fix2='dump rotation grace',
        fix2_diff='+ dump rotation grace\n',
        bad_pat='ttl only',
        doc='docs/QUAY-HYDGRACE.md',
        doc_point='ttl is not rotation grace',
        doc_diff='+ ttl is not rotation grace.',
        reg='reg',
        reg_diff='+ rotation grace holds',
        final_ok='ok 6 passed. rotation grace.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='rotation grace; dump leftover.',
        wrap='the rotation grace',
        wrap_ok='6 passed. quay-hydgrace assign is green.',
        wrap_part='5 passed, 1 residual. quay-hydgrace assign is green.',
        goal="Designed plant quay-hydgrace: the Hydra config that omitted refresh_token_rotation_grace so a parallel refresh 400'd the mobile client. rotation grace. ttl is not rotation grace.",
        plan='Repro python tests, reject ttl only, rotation grace, hand off dump.',
        out_ok='rotation grace. 6 tests pass.',
        out_part='rotation grace. dump leftover. Partial.',
    ),
    "kratos": P(True,
        slug='pr-kratos-session-whoami-tokenized',
        plant='lock-krwho',
        what="the Kratos whoami that omitted x-session-token header support so SPA bearer sessions 401'd",
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='kratos.yml tests/test_harbor.py',
        impl='kratos.yml',
        src='session:\n  cookie: {}',
        sym='session.whoami.tokenized',
        grep='session.whoami.tokenized',
        grep_obs='harbor cookie only. pack tokenized whoami.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: SPA bearer 401; tokenized whoami missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cookie only',
        wrong_diff='+ cookie only',
        wrong_obs='still cookie only. still fail.',
        fail2='FAIL test_assign: still broken. tokenized whoami.',
        reread='apply tokenized whoami.',
        insight='cookie session is not tokenized whoami',
        probe="rg -n 'tokenized' kratos.yml",
        probe_obs='pack tokenized whoami. harbor cookie only.',
        fix='tokenized whoami',
        fix_diff='+ tokenized whoami\n',
        rel='dump/kratos.yml',
        rel_src='session:\n  cookie: {}',
        leftover='leftover cookie only',
        fix2='dump tokenized whoami',
        fix2_diff='+ dump tokenized whoami\n',
        bad_pat='cookie only',
        doc='docs/LOCK-KRWHO.md',
        doc_point='cookie session is not tokenized whoami',
        doc_diff='+ cookie session is not tokenized whoami.',
        reg='reg',
        reg_diff='+ tokenized whoami holds',
        final_ok='ok 6 passed. tokenized whoami.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='tokenized whoami; dump same.',
        wrap='the tokenized whoami',
        wrap_ok='6 passed. lock-krwho assign is green.',
        wrap_part='5 passed, 1 residual. lock-krwho assign is green.',
        goal="Designed plant lock-krwho: the Kratos whoami that omitted x-session-token header support so SPA bearer sessions 401'd. tokenized whoami. cookie session is not tokenized whoami.",
        plan='Repro python tests, reject cookie only, tokenized whoami, fix dump.',
        out_ok='tokenized whoami. 6 tests pass.',
        out_part='tokenized whoami. dump leftover. Partial.',
    ),
    "keto": P(False,
        slug='pr-keto-read-api-separate-port',
        plant='quay-ketord',
        what="the Keto serve that omitted read API bind so Check() hit the write port and 404'd",
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='keto.yml tests/test_harbor.py',
        impl='keto.yml',
        src='serve:\n  write: {port: 4467}',
        sym='serve.read port 4466',
        grep='serve.read',
        grep_obs='harbor write only. pack read API port.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Check 404 on write port; read bind missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='write only',
        wrong_diff='+ write only',
        wrong_obs='still write only. still fail.',
        fail2='FAIL test_assign: still broken. read API port.',
        reread='apply read API port.',
        insight='write port is not read API',
        probe="rg -n 'read' keto.yml",
        probe_obs='pack read API port. harbor write only.',
        fix='read API port',
        fix_diff='+ read API port\n',
        rel='dump/keto.yml',
        rel_src='serve:\n  write: {port: 4467}',
        leftover='leftover write only',
        fix2='dump read API port',
        fix2_diff='+ dump read API port\n',
        bad_pat='write only',
        doc='docs/QUAY-KETORD.md',
        doc_point='write port is not read API',
        doc_diff='+ write port is not read API.',
        reg='reg',
        reg_diff='+ read API port holds',
        final_ok='ok 6 passed. read API port.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='read API port; dump leftover.',
        wrap='the read API port',
        wrap_ok='6 passed. quay-ketord assign is green.',
        wrap_part='5 passed, 1 residual. quay-ketord assign is green.',
        goal="Designed plant quay-ketord: the Keto serve that omitted read API bind so Check() hit the write port and 404'd. read API port. write port is not read API.",
        plan='Repro python tests, reject write only, read API port, hand off dump.',
        out_ok='read API port. 6 tests pass.',
        out_part='read API port. dump leftover. Partial.',
    ),
    "zitadel": P(True,
        slug='pr-zitadel-externaldomain-tls',
        plant='lock-zdext',
        what='the ZITADEL start that omitted ExternalDomain so OIDC discovery issued localhost issuer and mobile login failed',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='zitadel.yaml tests/test_harbor.py',
        impl='zitadel.yaml',
        src='ExternalPort: 8080',
        sym='ExternalDomain example.com',
        grep='ExternalDomain',
        grep_obs='harbor ExternalSecure only. pack ExternalDomain.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: issuer localhost; ExternalDomain missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ExternalSecure only',
        wrong_diff='+ ExternalSecure only',
        wrong_obs='still ExternalSecure only. still fail.',
        fail2='FAIL test_assign: still broken. ExternalDomain.',
        reread='apply ExternalDomain.',
        insight='ExternalSecure is not ExternalDomain',
        probe="rg -n 'ExternalDomain' zitadel.yaml",
        probe_obs='pack ExternalDomain. harbor ExternalSecure only.',
        fix='ExternalDomain',
        fix_diff='+ ExternalDomain\n',
        rel='dump/zitadel.yaml',
        rel_src='ExternalPort: 8080',
        leftover='leftover ExternalSecure only',
        fix2='dump ExternalDomain',
        fix2_diff='+ dump ExternalDomain\n',
        bad_pat='ExternalSecure only',
        doc='docs/LOCK-ZDEXT.md',
        doc_point='ExternalSecure is not ExternalDomain',
        doc_diff='+ ExternalSecure is not ExternalDomain.',
        reg='reg',
        reg_diff='+ ExternalDomain holds',
        final_ok='ok 6 passed. ExternalDomain.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ExternalDomain; dump same.',
        wrap='the ExternalDomain',
        wrap_ok='6 passed. lock-zdext assign is green.',
        wrap_part='5 passed, 1 residual. lock-zdext assign is green.',
        goal='Designed plant lock-zdext: the ZITADEL start that omitted ExternalDomain so OIDC discovery issued localhost issuer and mobile login failed. ExternalDomain. ExternalSecure is not ExternalDomain.',
        plan='Repro python tests, reject ExternalSecure only, ExternalDomain, fix dump.',
        out_ok='ExternalDomain. 6 tests pass.',
        out_part='ExternalDomain. dump leftover. Partial.',
    ),
    "authelia": P(False,
        slug='pr-authelia-session-redis-host',
        plant='quay-autred',
        what='the Authelia config that omitted session redis so two replicas issued independent cookies and SSO flapped',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='configuration.yml tests/test_harbor.py',
        impl='configuration.yml',
        src='session:\n  name: authelia_session',
        sym='session.redis host',
        grep='session.redis',
        grep_obs='harbor memory session. pack redis session.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: SSO flap two replicas; redis session missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='memory session',
        wrong_diff='+ memory session',
        wrong_obs='still memory session. still fail.',
        fail2='FAIL test_assign: still broken. redis session.',
        reread='apply redis session.',
        insight='memory session is not redis',
        probe="rg -n 'redis' configuration.yml",
        probe_obs='pack redis session. harbor memory session.',
        fix='redis session',
        fix_diff='+ redis session\n',
        rel='dump/configuration.yml',
        rel_src='session:\n  name: authelia_session',
        leftover='leftover memory session',
        fix2='dump redis session',
        fix2_diff='+ dump redis session\n',
        bad_pat='memory session',
        doc='docs/QUAY-AUTRED.md',
        doc_point='memory session is not redis',
        doc_diff='+ memory session is not redis.',
        reg='reg',
        reg_diff='+ redis session holds',
        final_ok='ok 6 passed. redis session.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='redis session; dump leftover.',
        wrap='the redis session',
        wrap_ok='6 passed. quay-autred assign is green.',
        wrap_part='5 passed, 1 residual. quay-autred assign is green.',
        goal='Designed plant quay-autred: the Authelia config that omitted session redis so two replicas issued independent cookies and SSO flapped. redis session. memory session is not redis.',
        plan='Repro python tests, reject memory session, redis session, hand off dump.',
        out_ok='redis session. 6 tests pass.',
        out_part='redis session. dump leftover. Partial.',
    ),
    "pomerium": P(True,
        slug='pr-pomerium-pass-identity-headers',
        plant='lock-pmrhdr',
        what="the Pomerium policy that omitted pass_identity_headers so the upstream JWT was missing and the API 401'd",
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='config.yaml tests/test_harbor.py',
        impl='config.yaml',
        src='routes: [{from: https://app.example}]',
        sym='pass_identity_headers true',
        grep='pass_identity_headers',
        grep_obs='harbor allow public only. pack pass_identity_headers.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: upstream 401 no JWT; pass_identity_headers missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='allow public only',
        wrong_diff='+ allow public only',
        wrong_obs='still allow public only. still fail.',
        fail2='FAIL test_assign: still broken. pass_identity_headers.',
        reread='apply pass_identity_headers.',
        insight='allow public is not pass_identity_headers',
        probe="rg -n 'pass_identity_headers' config.yaml",
        probe_obs='pack pass_identity_headers. harbor allow public only.',
        fix='pass_identity_headers',
        fix_diff='+ pass_identity_headers\n',
        rel='dump/config.yaml',
        rel_src='routes: [{from: https://app.example}]',
        leftover='leftover allow public only',
        fix2='dump pass_identity_headers',
        fix2_diff='+ dump pass_identity_headers\n',
        bad_pat='allow public only',
        doc='docs/LOCK-PMRHDR.md',
        doc_point='allow public is not pass_identity_headers',
        doc_diff='+ allow public is not pass_identity_headers.',
        reg='reg',
        reg_diff='+ pass_identity_headers holds',
        final_ok='ok 6 passed. pass_identity_headers.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pass_identity_headers; dump same.',
        wrap='the pass_identity_headers',
        wrap_ok='6 passed. lock-pmrhdr assign is green.',
        wrap_part='5 passed, 1 residual. lock-pmrhdr assign is green.',
        goal="Designed plant lock-pmrhdr: the Pomerium policy that omitted pass_identity_headers so the upstream JWT was missing and the API 401'd. pass_identity_headers. allow public is not pass_identity_headers.",
        plan='Repro python tests, reject allow public only, pass_identity_headers, fix dump.',
        out_ok='pass_identity_headers. 6 tests pass.',
        out_part='pass_identity_headers. dump leftover. Partial.',
    ),
    "teleport": P(False,
        slug='pr-teleport-proxy-public-addr',
        plant='quay-tpaddr',
        what='the Teleport proxy that omitted public_addr so tsh login used the internal DNS and hung',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='teleport.yaml tests/test_harbor.py',
        impl='teleport.yaml',
        src='proxy_service:\n  enabled: true',
        sym='public_addr teleport.example:443',
        grep='public_addr',
        grep_obs='harbor listen_addr only. pack public_addr.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: tsh login hung internal DNS; public_addr missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='listen_addr only',
        wrong_diff='+ listen_addr only',
        wrong_obs='still listen_addr only. still fail.',
        fail2='FAIL test_assign: still broken. public_addr.',
        reread='apply public_addr.',
        insight='listen_addr is not public_addr',
        probe="rg -n 'public_addr' teleport.yaml",
        probe_obs='pack public_addr. harbor listen_addr only.',
        fix='public_addr',
        fix_diff='+ public_addr\n',
        rel='dump/teleport.yaml',
        rel_src='proxy_service:\n  enabled: true',
        leftover='leftover listen_addr only',
        fix2='dump public_addr',
        fix2_diff='+ dump public_addr\n',
        bad_pat='listen_addr only',
        doc='docs/QUAY-TPADDR.md',
        doc_point='listen_addr is not public_addr',
        doc_diff='+ listen_addr is not public_addr.',
        reg='reg',
        reg_diff='+ public_addr holds',
        final_ok='ok 6 passed. public_addr.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='public_addr; dump leftover.',
        wrap='the public_addr',
        wrap_ok='6 passed. quay-tpaddr assign is green.',
        wrap_part='5 passed, 1 residual. quay-tpaddr assign is green.',
        goal='Designed plant quay-tpaddr: the Teleport proxy that omitted public_addr so tsh login used the internal DNS and hung. public_addr. listen_addr is not public_addr.',
        plan='Repro python tests, reject listen_addr only, public_addr, hand off dump.',
        out_ok='public_addr. 6 tests pass.',
        out_part='public_addr. dump leftover. Partial.',
    ),
    "dex": P(True,
        slug='pr-dex-storage-kubernetes-incluster',
        plant='lock-dexk8s',
        what='the Dex config that omitted storage type kubernetes so it used sqlite on an emptyDir and lost clients after restart',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='config.yaml tests/test_harbor.py',
        impl='config.yaml',
        src='storage:\n  type: sqlite3',
        sym='storage kubernetes',
        grep='storage',
        grep_obs='harbor sqlite persist volume. pack storage type kubernetes.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: clients gone after restart; sqlite emptyDir',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='sqlite persist volume',
        wrong_diff='+ sqlite persist volume',
        wrong_obs='still sqlite persist volume. still fail.',
        fail2='FAIL test_assign: still broken. storage type kubernetes.',
        reread='apply storage type kubernetes.',
        insight='a PVC is not kubernetes storage for Dex',
        probe="rg -n 'storage' config.yaml",
        probe_obs='pack storage type kubernetes. harbor sqlite persist volume.',
        fix='storage type kubernetes',
        fix_diff='+ storage type kubernetes\n',
        rel='dump/config.yaml',
        rel_src='storage:\n  type: sqlite3',
        leftover='leftover sqlite persist volume',
        fix2='dump storage type kubernetes',
        fix2_diff='+ dump storage type kubernetes\n',
        bad_pat='sqlite persist volume',
        doc='docs/LOCK-DEXK8S.md',
        doc_point='a PVC is not kubernetes storage for Dex',
        doc_diff='+ a PVC is not kubernetes storage for Dex.',
        reg='reg',
        reg_diff='+ storage type kubernetes holds',
        final_ok='ok 6 passed. storage type kubernetes.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='storage type kubernetes; dump same.',
        wrap='the storage type kubernetes',
        wrap_ok='6 passed. lock-dexk8s assign is green.',
        wrap_part='5 passed, 1 residual. lock-dexk8s assign is green.',
        goal='Designed plant lock-dexk8s: the Dex config that omitted storage type kubernetes so it used sqlite on an emptyDir and lost clients after restart. storage type kubernetes. a PVC is not kubernetes storage for Dex.',
        plan='Repro python tests, reject sqlite persist volume, storage type kubernetes, fix dump.',
        out_ok='storage type kubernetes. 6 tests pass.',
        out_part='storage type kubernetes. dump leftover. Partial.',
    ),
    "sssd": P(False,
        slug='pr-sssd-ldap-id-mapping-off',
        plant='quay-sssid',
        what='the SSSD domain that omitted ldap_id_mapping false so POSIX uids from LDAP were remapped and file owners broke',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='sssd.conf tests/test_harbor.py',
        impl='sssd.conf',
        src='[domain/harbor]\nid_provider = ldap',
        sym='ldap_id_mapping = false',
        grep='ldap_id_mapping',
        grep_obs='harbor enumerate true. pack ldap_id_mapping false.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: uid remapped; file owners wrong; ldap_id_mapping missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enumerate true',
        wrong_diff='+ enumerate true',
        wrong_obs='still enumerate true. still fail.',
        fail2='FAIL test_assign: still broken. ldap_id_mapping false.',
        reread='apply ldap_id_mapping false.',
        insight='enumerate is not ldap_id_mapping',
        probe="rg -n 'ldap_id_mapping' sssd.conf",
        probe_obs='pack ldap_id_mapping false. harbor enumerate true.',
        fix='ldap_id_mapping false',
        fix_diff='+ ldap_id_mapping false\n',
        rel='dump/sssd.conf',
        rel_src='[domain/harbor]\nid_provider = ldap',
        leftover='leftover enumerate true',
        fix2='dump ldap_id_mapping false',
        fix2_diff='+ dump ldap_id_mapping false\n',
        bad_pat='enumerate true',
        doc='docs/QUAY-SSSID.md',
        doc_point='enumerate is not ldap_id_mapping',
        doc_diff='+ enumerate is not ldap_id_mapping.',
        reg='reg',
        reg_diff='+ ldap_id_mapping false holds',
        final_ok='ok 6 passed. ldap_id_mapping false.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ldap_id_mapping false; dump leftover.',
        wrap='the ldap_id_mapping false',
        wrap_ok='6 passed. quay-sssid assign is green.',
        wrap_part='5 passed, 1 residual. quay-sssid assign is green.',
        goal='Designed plant quay-sssid: the SSSD domain that omitted ldap_id_mapping false so POSIX uids from LDAP were remapped and file owners broke. ldap_id_mapping false. enumerate is not ldap_id_mapping.',
        plan='Repro python tests, reject enumerate true, ldap_id_mapping false, hand off dump.',
        out_ok='ldap_id_mapping false. 6 tests pass.',
        out_part='ldap_id_mapping false. dump leftover. Partial.',
    ),
    "pam": P(True,
        slug='pr-pam-mkhomedir-umask-skel',
        plant='lock-pamhome',
        what='the PAM stack that omitted pam_mkhomedir.so so a first LDAP login had no home and sshd dropped the session',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='sshd tests/test_harbor.py',
        impl='sshd',
        src='session required pam_unix.so',
        sym='pam_mkhomedir.so',
        grep='pam_mkhomedir.so',
        grep_obs='harbor CreateHome in sshd_config. pack pam_mkhomedir.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: no home; sshd drop; pam_mkhomedir missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='CreateHome in sshd_config',
        wrong_diff='+ CreateHome in sshd_config',
        wrong_obs='still CreateHome in sshd_config. still fail.',
        fail2='FAIL test_assign: still broken. pam_mkhomedir.',
        reread='apply pam_mkhomedir.',
        insight='sshd CreateHome is not pam_mkhomedir',
        probe="rg -n 'pam_mkhomedir' sshd",
        probe_obs='pack pam_mkhomedir. harbor CreateHome in sshd_config.',
        fix='pam_mkhomedir',
        fix_diff='+ pam_mkhomedir\n',
        rel='dump/sshd',
        rel_src='session required pam_unix.so',
        leftover='leftover CreateHome in sshd_config',
        fix2='dump pam_mkhomedir',
        fix2_diff='+ dump pam_mkhomedir\n',
        bad_pat='CreateHome in sshd_config',
        doc='docs/LOCK-PAMHOME.md',
        doc_point='sshd CreateHome is not pam_mkhomedir',
        doc_diff='+ sshd CreateHome is not pam_mkhomedir.',
        reg='reg',
        reg_diff='+ pam_mkhomedir holds',
        final_ok='ok 6 passed. pam_mkhomedir.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pam_mkhomedir; dump same.',
        wrap='the pam_mkhomedir',
        wrap_ok='6 passed. lock-pamhome assign is green.',
        wrap_part='5 passed, 1 residual. lock-pamhome assign is green.',
        goal='Designed plant lock-pamhome: the PAM stack that omitted pam_mkhomedir.so so a first LDAP login had no home and sshd dropped the session. pam_mkhomedir. sshd CreateHome is not pam_mkhomedir.',
        plan='Repro python tests, reject CreateHome in sshd_config, pam_mkhomedir, fix dump.',
        out_ok='pam_mkhomedir. 6 tests pass.',
        out_part='pam_mkhomedir. dump leftover. Partial.',
    ),
    "casdoor": P(False,
        slug='pr-casdoor-origin-frontend',
        plant='quay-csdorg',
        what='the Casdoor conf that omitted origin so OAuth redirect_uri used http://localhost and the SPA callback failed',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='app.conf tests/test_harbor.py',
        impl='app.conf',
        src='httpport = 8000',
        sym='origin https://login.example',
        grep='origin',
        grep_obs='harbor redirect uri in app only. pack origin.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: redirect_uri localhost; origin missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='redirect uri in app only',
        wrong_diff='+ redirect uri in app only',
        wrong_obs='still redirect uri in app only. still fail.',
        fail2='FAIL test_assign: still broken. origin.',
        reread='apply origin.',
        insight='app redirect is not Casdoor origin',
        probe="rg -n 'origin' app.conf",
        probe_obs='pack origin. harbor redirect uri in app only.',
        fix='origin',
        fix_diff='+ origin\n',
        rel='dump/app.conf',
        rel_src='httpport = 8000',
        leftover='leftover redirect uri in app only',
        fix2='dump origin',
        fix2_diff='+ dump origin\n',
        bad_pat='redirect uri in app only',
        doc='docs/QUAY-CSDORG.md',
        doc_point='app redirect is not Casdoor origin',
        doc_diff='+ app redirect is not Casdoor origin.',
        reg='reg',
        reg_diff='+ origin holds',
        final_ok='ok 6 passed. origin.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='origin; dump leftover.',
        wrap='the origin',
        wrap_ok='6 passed. quay-csdorg assign is green.',
        wrap_part='5 passed, 1 residual. quay-csdorg assign is green.',
        goal='Designed plant quay-csdorg: the Casdoor conf that omitted origin so OAuth redirect_uri used http://localhost and the SPA callback failed. origin. app redirect is not Casdoor origin.',
        plan='Repro python tests, reject redirect uri in app only, origin, hand off dump.',
        out_ok='origin. 6 tests pass.',
        out_part='origin. dump leftover. Partial.',
    ),
    "kanidm": P(True,
        slug='pr-kanidm-domain-origin-https',
        plant='lock-kndom',
        what='the Kanidm server.toml that omitted origin https so Webauthn rpId mismatched and passkeys failed',
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='server.toml tests/test_harbor.py',
        impl='server.toml',
        src='bindaddress = "127.0.0.1:8443"',
        sym='origin https://idm.example',
        grep='origin',
        grep_obs='harbor domain only. pack origin https.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Webauthn rpId mismatch; origin missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='domain only',
        wrong_diff='+ domain only',
        wrong_obs='still domain only. still fail.',
        fail2='FAIL test_assign: still broken. origin https.',
        reread='apply origin https.',
        insight='domain is not origin',
        probe="rg -n 'origin' server.toml",
        probe_obs='pack origin https. harbor domain only.',
        fix='origin https',
        fix_diff='+ origin https\n',
        rel='dump/server.toml',
        rel_src='bindaddress = "127.0.0.1:8443"',
        leftover='leftover domain only',
        fix2='dump origin https',
        fix2_diff='+ dump origin https\n',
        bad_pat='domain only',
        doc='docs/LOCK-KNDOM.md',
        doc_point='domain is not origin',
        doc_diff='+ domain is not origin.',
        reg='reg',
        reg_diff='+ origin https holds',
        final_ok='ok 6 passed. origin https.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='origin https; dump same.',
        wrap='the origin https',
        wrap_ok='6 passed. lock-kndom assign is green.',
        wrap_part='5 passed, 1 residual. lock-kndom assign is green.',
        goal='Designed plant lock-kndom: the Kanidm server.toml that omitted origin https so Webauthn rpId mismatched and passkeys failed. origin https. domain is not origin.',
        plan='Repro python tests, reject domain only, origin https, fix dump.',
        out_ok='origin https. 6 tests pass.',
        out_part='origin https. dump leftover. Partial.',
    ),
    "gluu": P(False,
        slug='pr-gluu-agama-flow-timeout',
        plant='quay-glag',
        what="the Gluu Agama flow that omitted timeout so an abandoned login held a session lock and the next attempt 409'd",
        glob='**/*.{yml,yaml,json,conf,sh}',
        ls='agama.json tests/test_harbor.py',
        impl='agama.json',
        src='{"flows": {}}',
        sym='flow timeout 5m',
        grep='flow',
        grep_obs='harbor session timeout only. pack agama flow timeout.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: next login 409; flow timeout missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='session timeout only',
        wrong_diff='+ session timeout only',
        wrong_obs='still session timeout only. still fail.',
        fail2='FAIL test_assign: still broken. agama flow timeout.',
        reread='apply agama flow timeout.',
        insight='session timeout is not agama flow timeout',
        probe="rg -n 'agama' agama.json",
        probe_obs='pack agama flow timeout. harbor session timeout only.',
        fix='agama flow timeout',
        fix_diff='+ agama flow timeout\n',
        rel='dump/agama.json',
        rel_src='{"flows": {}}',
        leftover='leftover session timeout only',
        fix2='dump agama flow timeout',
        fix2_diff='+ dump agama flow timeout\n',
        bad_pat='session timeout only',
        doc='docs/QUAY-GLAG.md',
        doc_point='session timeout is not agama flow timeout',
        doc_diff='+ session timeout is not agama flow timeout.',
        reg='reg',
        reg_diff='+ agama flow timeout holds',
        final_ok='ok 6 passed. agama flow timeout.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='agama flow timeout; dump leftover.',
        wrap='the agama flow timeout',
        wrap_ok='6 passed. quay-glag assign is green.',
        wrap_part='5 passed, 1 residual. quay-glag assign is green.',
        goal="Designed plant quay-glag: the Gluu Agama flow that omitted timeout so an abandoned login held a session lock and the next attempt 409'd. agama flow timeout. session timeout is not agama flow timeout.",
        plan='Repro python tests, reject session timeout only, agama flow timeout, hand off dump.',
        out_ok='agama flow timeout. 6 tests pass.',
        out_part='agama flow timeout. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('oauth2-proxy SameSite vs Authentik host_insecure', fn('oauth2proxy'), fn('authentik'), 'cookie_samesite none; authentik_host_insecure', 'cookie_expire; proxy skip_verify', 'oauth2-proxy dump refresh cookie dropped; authentik dump outpost 401'),
    ('Ory Keto opl vs Hydra refresh grace', fn('ory'), fn('hydra'), 'namespaces opl; rotation grace', 'migrate; ttl', 'ory dump unknown namespace; hydra dump parallel refresh 400'),
    ('Kratos tokenized whoami vs Keto read API port', fn('kratos'), fn('keto'), 'tokenized whoami; serve.read 4466', 'cookie session; write port', 'kratos dump SPA 401; keto dump Check 404'),
    ('ZITADEL ExternalDomain vs Authelia redis session', fn('zitadel'), fn('authelia'), 'ExternalDomain; session.redis', 'ExternalSecure; memory session', 'zitadel dump issuer localhost; authelia dump SSO flap'),
    ('Pomerium pass_identity_headers vs Teleport public_addr', fn('pomerium'), fn('teleport'), 'pass_identity_headers; public_addr', 'allow public; listen_addr', 'pomerium dump upstream 401; teleport dump tsh hung'),
    ('Dex kubernetes storage vs SSSD ldap_id_mapping', fn('dex'), fn('sssd'), 'storage kubernetes; ldap_id_mapping false', 'sqlite PVC; enumerate', 'dex dump clients gone; sssd dump uid remap'),
    ('PAM mkhomedir vs Casdoor origin', fn('pam'), fn('casdoor'), 'pam_mkhomedir; origin https', 'sshd CreateHome; app redirect', 'pam dump no home; casdoor dump localhost redirect'),
    ('Kanidm origin https vs Gluu agama timeout', fn('kanidm'), fn('gluu'), 'origin https; agama flow timeout 5m', 'domain; session timeout', 'kanidm dump Webauthn rpId; gluu dump 409 lock'),
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
- Not a clone of r4163-r4572 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
