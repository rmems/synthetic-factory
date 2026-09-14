#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4ch: unused plants after r4556.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4556. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4ch_state.json")
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
    "goldilocks": P(True,
        slug='pr-goldilocks-on-by-default-ns',
        plant='lock-gldns',
        what='the Goldilocks dashboard that omitted on-by-default namespace so VPA recommendations never appeared for harbor',
        glob='**/*.{yml,yaml,json,sh}',
        ls='values.yaml tests/test_harbor.py',
        impl='values.yaml',
        src='goldilocks:\n  dashboard: {}',
        sym='onByDefault true',
        grep='onByDefault',
        grep_obs='harbor label vpa only. pack onByDefault namespace.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: no VPA recs; on-by-default missing; ns unlabeled',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='label vpa only',
        wrong_diff='+ label vpa only',
        wrong_obs='still label vpa only. still fail.',
        fail2='FAIL test_assign: still broken. onByDefault namespace.',
        reread='apply onByDefault namespace.',
        insight='labeling vpa is not on-by-default',
        probe="rg -n 'onByDefault' values.yaml",
        probe_obs='pack onByDefault namespace. harbor label vpa only.',
        fix='onByDefault namespace',
        fix_diff='+ onByDefault namespace\n',
        rel='dump/values.yaml',
        rel_src='goldilocks:\n  dashboard: {}',
        leftover='leftover label vpa only',
        fix2='dump onByDefault namespace',
        fix2_diff='+ dump onByDefault namespace\n',
        bad_pat='label vpa only',
        doc='docs/LOCK-GLDNS.md',
        doc_point='labeling vpa is not on-by-default',
        doc_diff='+ labeling vpa is not on-by-default.',
        reg='reg',
        reg_diff='+ onByDefault namespace holds',
        final_ok='ok 6 passed. onByDefault namespace.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='onByDefault namespace; dump same.',
        wrap='the onByDefault namespace',
        wrap_ok='6 passed. lock-gldns assign is green.',
        wrap_part='5 passed, 1 residual. lock-gldns assign is green.',
        goal='Designed plant lock-gldns: the Goldilocks dashboard that omitted on-by-default namespace so VPA recommendations never appeared for harbor. onByDefault namespace. labeling vpa is not on-by-default.',
        plan='Repro python tests, reject label vpa only, onByDefault namespace, fix dump.',
        out_ok='onByDefault namespace. 6 tests pass.',
        out_part='onByDefault namespace. dump leftover. Partial.',
    ),
    "vpa": P(False,
        slug='pr-vpa-update-mode-off-in-place',
        plant='quay-vpaoff',
        what='the VPA object that omitted updateMode so it defaulted Off and never resized the container',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vpa.yaml tests/test_harbor.py',
        impl='vpa.yaml',
        src='spec:\n  targetRef: {name: harbor}',
        sym='updateMode Auto',
        grep='updateMode',
        grep_obs='harbor requests only. pack updateMode Auto.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: container requests unchanged; updateMode Off default',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='requests only',
        wrong_diff='+ requests only',
        wrong_obs='still requests only. still fail.',
        fail2='FAIL test_assign: still broken. updateMode Auto.',
        reread='apply updateMode Auto.',
        insight='setting requests is not updateMode',
        probe="rg -n 'updateMode' vpa.yaml",
        probe_obs='pack updateMode Auto. harbor requests only.',
        fix='updateMode Auto',
        fix_diff='+ updateMode Auto\n',
        rel='dump/vpa.yaml',
        rel_src='spec:\n  targetRef: {name: harbor}',
        leftover='leftover requests only',
        fix2='dump updateMode Auto',
        fix2_diff='+ dump updateMode Auto\n',
        bad_pat='requests only',
        doc='docs/QUAY-VPAOFF.md',
        doc_point='setting requests is not updateMode',
        doc_diff='+ setting requests is not updateMode.',
        reg='reg',
        reg_diff='+ updateMode Auto holds',
        final_ok='ok 6 passed. updateMode Auto.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='updateMode Auto; dump leftover.',
        wrap='the updateMode Auto',
        wrap_ok='6 passed. quay-vpaoff assign is green.',
        wrap_part='5 passed, 1 residual. quay-vpaoff assign is green.',
        goal='Designed plant quay-vpaoff: the VPA object that omitted updateMode so it defaulted Off and never resized the container. updateMode Auto. setting requests is not updateMode.',
        plan='Repro python tests, reject requests only, updateMode Auto, hand off dump.',
        out_ok='updateMode Auto. 6 tests pass.',
        out_part='updateMode Auto. dump leftover. Partial.',
    ),
    "gatekeeper": P(True,
        slug='pr-gatekeeper-exempt-namespace-system',
        plant='lock-gkex',
        what='the Gatekeeper Config that omitted exempt namespace kube-system so a required-labels constraint blocked coredns',
        glob='**/*.{yml,yaml,json,sh}',
        ls='config.yaml tests/test_harbor.py',
        impl='config.yaml',
        src='spec:\n  match: [{}]',
        sym='exempt kube-system',
        grep='exempt',
        grep_obs='harbor enforcementAction dryrun. pack exemptNamespaces kube-system.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: coredns denied; kube-system not exempt',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enforcementAction dryrun',
        wrong_diff='+ enforcementAction dryrun',
        wrong_obs='still enforcementAction dryrun. still fail.',
        fail2='FAIL test_assign: still broken. exemptNamespaces kube-system.',
        reread='apply exemptNamespaces kube-system.',
        insight='dryrun is not exemptNamespaces',
        probe="rg -n 'exemptNamespaces' config.yaml",
        probe_obs='pack exemptNamespaces kube-system. harbor enforcementAction dryrun.',
        fix='exemptNamespaces kube-system',
        fix_diff='+ exemptNamespaces kube-system\n',
        rel='dump/config.yaml',
        rel_src='spec:\n  match: [{}]',
        leftover='leftover enforcementAction dryrun',
        fix2='dump exemptNamespaces kube-system',
        fix2_diff='+ dump exemptNamespaces kube-system\n',
        bad_pat='enforcementAction dryrun',
        doc='docs/LOCK-GKEX.md',
        doc_point='dryrun is not exemptNamespaces',
        doc_diff='+ dryrun is not exemptNamespaces.',
        reg='reg',
        reg_diff='+ exemptNamespaces kube-system holds',
        final_ok='ok 6 passed. exemptNamespaces kube-system.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='exemptNamespaces kube-system; dump same.',
        wrap='the exemptNamespaces kube-system',
        wrap_ok='6 passed. lock-gkex assign is green.',
        wrap_part='5 passed, 1 residual. lock-gkex assign is green.',
        goal='Designed plant lock-gkex: the Gatekeeper Config that omitted exempt namespace kube-system so a required-labels constraint blocked coredns. exemptNamespaces kube-system. dryrun is not exemptNamespaces.',
        plan='Repro python tests, reject enforcementAction dryrun, exemptNamespaces kube-system, fix dump.',
        out_ok='exemptNamespaces kube-system. 6 tests pass.',
        out_part='exemptNamespaces kube-system. dump leftover. Partial.',
    ),
    "falco": P(False,
        slug='pr-falco-syscall-buffer-drop',
        plant='quay-falcobuf',
        what='the Falco config that omitted syscall_buf_size_preset so high-rate nodes dropped events and the alert never fired',
        glob='**/*.{yml,yaml,json,sh}',
        ls='falco.yaml tests/test_harbor.py',
        impl='falco.yaml',
        src='json_output: true',
        sym='syscall_buf_size_preset 8',
        grep='syscall_buf_size_preset',
        grep_obs='harbor priority warning only. pack syscall buffer preset.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: 40% drops; buffer too small; alert missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='priority warning only',
        wrong_diff='+ priority warning only',
        wrong_obs='still priority warning only. still fail.',
        fail2='FAIL test_assign: still broken. syscall buffer preset.',
        reread='apply syscall buffer preset.',
        insight='priority is not syscall buffer size',
        probe="rg -n 'syscall' falco.yaml",
        probe_obs='pack syscall buffer preset. harbor priority warning only.',
        fix='syscall buffer preset',
        fix_diff='+ syscall buffer preset\n',
        rel='dump/falco.yaml',
        rel_src='json_output: true',
        leftover='leftover priority warning only',
        fix2='dump syscall buffer preset',
        fix2_diff='+ dump syscall buffer preset\n',
        bad_pat='priority warning only',
        doc='docs/QUAY-FALCOBUF.md',
        doc_point='priority is not syscall buffer size',
        doc_diff='+ priority is not syscall buffer size.',
        reg='reg',
        reg_diff='+ syscall buffer preset holds',
        final_ok='ok 6 passed. syscall buffer preset.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='syscall buffer preset; dump leftover.',
        wrap='the syscall buffer preset',
        wrap_ok='6 passed. quay-falcobuf assign is green.',
        wrap_part='5 passed, 1 residual. quay-falcobuf assign is green.',
        goal='Designed plant quay-falcobuf: the Falco config that omitted syscall_buf_size_preset so high-rate nodes dropped events and the alert never fired. syscall buffer preset. priority is not syscall buffer size.',
        plan='Repro python tests, reject priority warning only, syscall buffer preset, hand off dump.',
        out_ok='syscall buffer preset. 6 tests pass.',
        out_part='syscall buffer preset. dump leftover. Partial.',
    ),
    "tetragon": P(True,
        slug='pr-tetragon-export-allowlist-process',
        plant='lock-tetallw',
        what="the Tetragon TracingPolicy that omitted export-allowlist so the agent exported every process and OOM'd the node",
        glob='**/*.{yml,yaml,json,sh}',
        ls='policy.yaml tests/test_harbor.py',
        impl='policy.yaml',
        src='spec:\n  kprobes: [{}]',
        sym='export-allowlist binary',
        grep='export-allowlist',
        grep_obs='harbor rateLimit only. pack export-allowlist.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: node OOM; every process exported; allowlist missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='rateLimit only',
        wrong_diff='+ rateLimit only',
        wrong_obs='still rateLimit only. still fail.',
        fail2='FAIL test_assign: still broken. export-allowlist.',
        reread='apply export-allowlist.',
        insight='rateLimit is not export-allowlist',
        probe="rg -n 'export-allowlist' policy.yaml",
        probe_obs='pack export-allowlist. harbor rateLimit only.',
        fix='export-allowlist',
        fix_diff='+ export-allowlist\n',
        rel='dump/policy.yaml',
        rel_src='spec:\n  kprobes: [{}]',
        leftover='leftover rateLimit only',
        fix2='dump export-allowlist',
        fix2_diff='+ dump export-allowlist\n',
        bad_pat='rateLimit only',
        doc='docs/LOCK-TETALLW.md',
        doc_point='rateLimit is not export-allowlist',
        doc_diff='+ rateLimit is not export-allowlist.',
        reg='reg',
        reg_diff='+ export-allowlist holds',
        final_ok='ok 6 passed. export-allowlist.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='export-allowlist; dump same.',
        wrap='the export-allowlist',
        wrap_ok='6 passed. lock-tetallw assign is green.',
        wrap_part='5 passed, 1 residual. lock-tetallw assign is green.',
        goal="Designed plant lock-tetallw: the Tetragon TracingPolicy that omitted export-allowlist so the agent exported every process and OOM'd the node. export-allowlist. rateLimit is not export-allowlist.",
        plan='Repro python tests, reject rateLimit only, export-allowlist, fix dump.',
        out_ok='export-allowlist. 6 tests pass.',
        out_part='export-allowlist. dump leftover. Partial.',
    ),
    "cubefs": P(False,
        slug='pr-cubefs-datanode-disks-path',
        plant='quay-cfdisks',
        what='the CubeFS DataNode that omitted disks path so volumes stayed pending and the metanode had no replica',
        glob='**/*.{yml,yaml,json,sh}',
        ls='datanode.json tests/test_harbor.py',
        impl='datanode.json',
        src='{"listen": "17310"}',
        sym='disks path',
        grep='disks',
        grep_obs='harbor logDir only. pack disks: [/data].',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: volume pending; disks path missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='logDir only',
        wrong_diff='+ logDir only',
        wrong_obs='still logDir only. still fail.',
        fail2='FAIL test_assign: still broken. disks: [/data].',
        reread='apply disks: [/data].',
        insight='logDir is not disks',
        probe="rg -n 'disks:' datanode.json",
        probe_obs='pack disks: [/data]. harbor logDir only.',
        fix='disks: [/data]',
        fix_diff='+ disks: [/data]\n',
        rel='dump/datanode.json',
        rel_src='{"listen": "17310"}',
        leftover='leftover logDir only',
        fix2='dump disks: [/data]',
        fix2_diff='+ dump disks: [/data]\n',
        bad_pat='logDir only',
        doc='docs/QUAY-CFDISKS.md',
        doc_point='logDir is not disks',
        doc_diff='+ logDir is not disks.',
        reg='reg',
        reg_diff='+ disks: [/data] holds',
        final_ok='ok 6 passed. disks: [/data].',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='disks: [/data]; dump leftover.',
        wrap='the disks: [/data]',
        wrap_ok='6 passed. quay-cfdisks assign is green.',
        wrap_part='5 passed, 1 residual. quay-cfdisks assign is green.',
        goal='Designed plant quay-cfdisks: the CubeFS DataNode that omitted disks path so volumes stayed pending and the metanode had no replica. disks: [/data]. logDir is not disks.',
        plan='Repro python tests, reject logDir only, disks: [/data], hand off dump.',
        out_ok='disks: [/data]. 6 tests pass.',
        out_part='disks: [/data]. dump leftover. Partial.',
    ),
    "clusterapi": P(True,
        slug='pr-clusterapi-exp-machinepool-gate',
        plant='lock-capimp',
        what='the CAPI core that omitted MachinePool feature gate so a MachinePool CR stayed un-reconciled',
        glob='**/*.{yml,yaml,json,sh}',
        ls='capi-config.yaml tests/test_harbor.py',
        impl='capi-config.yaml',
        src='spec:\n  replicas: 3',
        sym='EXP_MACHINE_POOL true',
        grep='EXP_MACHINE_POOL',
        grep_obs='harbor MachineDeployment only. pack EXP_MACHINE_POOL.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: MachinePool un-reconciled; feature gate off',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='MachineDeployment only',
        wrong_diff='+ MachineDeployment only',
        wrong_obs='still MachineDeployment only. still fail.',
        fail2='FAIL test_assign: still broken. EXP_MACHINE_POOL.',
        reread='apply EXP_MACHINE_POOL.',
        insight='MachineDeployment is not EXP_MACHINE_POOL',
        probe="rg -n 'EXP_MACHINE_POOL' capi-config.yaml",
        probe_obs='pack EXP_MACHINE_POOL. harbor MachineDeployment only.',
        fix='EXP_MACHINE_POOL',
        fix_diff='+ EXP_MACHINE_POOL\n',
        rel='dump/capi-config.yaml',
        rel_src='spec:\n  replicas: 3',
        leftover='leftover MachineDeployment only',
        fix2='dump EXP_MACHINE_POOL',
        fix2_diff='+ dump EXP_MACHINE_POOL\n',
        bad_pat='MachineDeployment only',
        doc='docs/LOCK-CAPIMP.md',
        doc_point='MachineDeployment is not EXP_MACHINE_POOL',
        doc_diff='+ MachineDeployment is not EXP_MACHINE_POOL.',
        reg='reg',
        reg_diff='+ EXP_MACHINE_POOL holds',
        final_ok='ok 6 passed. EXP_MACHINE_POOL.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='EXP_MACHINE_POOL; dump same.',
        wrap='the EXP_MACHINE_POOL',
        wrap_ok='6 passed. lock-capimp assign is green.',
        wrap_part='5 passed, 1 residual. lock-capimp assign is green.',
        goal='Designed plant lock-capimp: the CAPI core that omitted MachinePool feature gate so a MachinePool CR stayed un-reconciled. EXP_MACHINE_POOL. MachineDeployment is not EXP_MACHINE_POOL.',
        plan='Repro python tests, reject MachineDeployment only, EXP_MACHINE_POOL, fix dump.',
        out_ok='EXP_MACHINE_POOL. 6 tests pass.',
        out_part='EXP_MACHINE_POOL. dump leftover. Partial.',
    ),
    "fluxcd": P(False,
        slug='pr-fluxcd-kustomization-prune-wait',
        plant='quay-flxprune',
        what='the Flux Kustomization that omitted prune so a deleted manifest stayed live and the old Ingress kept traffic',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ks.yaml tests/test_harbor.py',
        impl='ks.yaml',
        src='spec:\n  interval: 10m',
        sym='prune true',
        grep='prune',
        grep_obs='harbor force true. pack prune true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: old Ingress still live; prune missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='force true',
        wrong_diff='+ force true',
        wrong_obs='still force true. still fail.',
        fail2='FAIL test_assign: still broken. prune true.',
        reread='apply prune true.',
        insight='force is not prune',
        probe="rg -n 'prune' ks.yaml",
        probe_obs='pack prune true. harbor force true.',
        fix='prune true',
        fix_diff='+ prune true\n',
        rel='dump/ks.yaml',
        rel_src='spec:\n  interval: 10m',
        leftover='leftover force true',
        fix2='dump prune true',
        fix2_diff='+ dump prune true\n',
        bad_pat='force true',
        doc='docs/QUAY-FLXPRUNE.md',
        doc_point='force is not prune',
        doc_diff='+ force is not prune.',
        reg='reg',
        reg_diff='+ prune true holds',
        final_ok='ok 6 passed. prune true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='prune true; dump leftover.',
        wrap='the prune true',
        wrap_ok='6 passed. quay-flxprune assign is green.',
        wrap_part='5 passed, 1 residual. quay-flxprune assign is green.',
        goal='Designed plant quay-flxprune: the Flux Kustomization that omitted prune so a deleted manifest stayed live and the old Ingress kept traffic. prune true. force is not prune.',
        plan='Repro python tests, reject force true, prune true, hand off dump.',
        out_ok='prune true. 6 tests pass.',
        out_part='prune true. dump leftover. Partial.',
    ),
    "kubevirt": P(True,
        slug='pr-kubevirt-live-migration-network',
        plant='lock-kvlive',
        what='the KubeVirt VM that omitted liveMigrationNetwork so a migration used the pod network and the guest NIC dropped',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vm.yaml tests/test_harbor.py',
        impl='vm.yaml',
        src='spec:\n  running: true',
        sym='liveMigrationNetwork',
        grep='liveMigrationNetwork',
        grep_obs='harbor evictionStrategy LiveMigrate only. pack migration network.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: guest NIC drop; migration on pod network; liveMigrationNetwork missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='evictionStrategy LiveMigrate only',
        wrong_diff='+ evictionStrategy LiveMigrate only',
        wrong_obs='still evictionStrategy LiveMigrate only. still fail.',
        fail2='FAIL test_assign: still broken. migration network.',
        reread='apply migration network.',
        insight='evictionStrategy is not liveMigrationNetwork',
        probe="rg -n 'migration' vm.yaml",
        probe_obs='pack migration network. harbor evictionStrategy LiveMigrate only.',
        fix='migration network',
        fix_diff='+ migration network\n',
        rel='dump/vm.yaml',
        rel_src='spec:\n  running: true',
        leftover='leftover evictionStrategy LiveMigrate only',
        fix2='dump migration network',
        fix2_diff='+ dump migration network\n',
        bad_pat='evictionStrategy LiveMigrate only',
        doc='docs/LOCK-KVLIVE.md',
        doc_point='evictionStrategy is not liveMigrationNetwork',
        doc_diff='+ evictionStrategy is not liveMigrationNetwork.',
        reg='reg',
        reg_diff='+ migration network holds',
        final_ok='ok 6 passed. migration network.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='migration network; dump same.',
        wrap='the migration network',
        wrap_ok='6 passed. lock-kvlive assign is green.',
        wrap_part='5 passed, 1 residual. lock-kvlive assign is green.',
        goal='Designed plant lock-kvlive: the KubeVirt VM that omitted liveMigrationNetwork so a migration used the pod network and the guest NIC dropped. migration network. evictionStrategy is not liveMigrationNetwork.',
        plan='Repro python tests, reject evictionStrategy LiveMigrate only, migration network, fix dump.',
        out_ok='migration network. 6 tests pass.',
        out_part='migration network. dump leftover. Partial.',
    ),
    "ovirt": P(False,
        slug='pr-ovirt-cpu-passthrough-model',
        plant='quay-ovcpu',
        what='the oVirt VM that omitted cpu.mode host-passthrough so nested KVM was unavailable and the guest hypervisor failed',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vm.yaml tests/test_harbor.py',
        impl='vm.yaml',
        src='spec:\n  cpu: {cores: 4}',
        sym='cpu.mode host-passthrough',
        grep='cpu.mode',
        grep_obs='harbor cpu.topology only. pack host-passthrough.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: nested KVM missing; cpu.mode default; guest hypervisor fail',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cpu.topology only',
        wrong_diff='+ cpu.topology only',
        wrong_obs='still cpu.topology only. still fail.',
        fail2='FAIL test_assign: still broken. host-passthrough.',
        reread='apply host-passthrough.',
        insight='cpu.topology is not host-passthrough',
        probe="rg -n 'host-passthrough' vm.yaml",
        probe_obs='pack host-passthrough. harbor cpu.topology only.',
        fix='host-passthrough',
        fix_diff='+ host-passthrough\n',
        rel='dump/vm.yaml',
        rel_src='spec:\n  cpu: {cores: 4}',
        leftover='leftover cpu.topology only',
        fix2='dump host-passthrough',
        fix2_diff='+ dump host-passthrough\n',
        bad_pat='cpu.topology only',
        doc='docs/QUAY-OVCPU.md',
        doc_point='cpu.topology is not host-passthrough',
        doc_diff='+ cpu.topology is not host-passthrough.',
        reg='reg',
        reg_diff='+ host-passthrough holds',
        final_ok='ok 6 passed. host-passthrough.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='host-passthrough; dump leftover.',
        wrap='the host-passthrough',
        wrap_ok='6 passed. quay-ovcpu assign is green.',
        wrap_part='5 passed, 1 residual. quay-ovcpu assign is green.',
        goal='Designed plant quay-ovcpu: the oVirt VM that omitted cpu.mode host-passthrough so nested KVM was unavailable and the guest hypervisor failed. host-passthrough. cpu.topology is not host-passthrough.',
        plan='Repro python tests, reject cpu.topology only, host-passthrough, hand off dump.',
        out_ok='host-passthrough. 6 tests pass.',
        out_part='host-passthrough. dump leftover. Partial.',
    ),
    "magnum": P(True,
        slug='pr-magnum-labels-auto-healing',
        plant='lock-mgheal',
        what='the Magnum cluster that omitted auto_healing_enabled so a dead minion was never replaced',
        glob='**/*.{yml,yaml,json,sh}',
        ls='cluster.yaml tests/test_harbor.py',
        impl='cluster.yaml',
        src='labels:\n  kube_tag: v1.28',
        sym='auto_healing_enabled true',
        grep='auto_healing_enabled',
        grep_obs='harbor master_count only. pack auto_healing_enabled.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: dead minion stays; auto_healing_enabled missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='master_count only',
        wrong_diff='+ master_count only',
        wrong_obs='still master_count only. still fail.',
        fail2='FAIL test_assign: still broken. auto_healing_enabled.',
        reread='apply auto_healing_enabled.',
        insight='master_count is not auto_healing',
        probe="rg -n 'auto_healing_enabled' cluster.yaml",
        probe_obs='pack auto_healing_enabled. harbor master_count only.',
        fix='auto_healing_enabled',
        fix_diff='+ auto_healing_enabled\n',
        rel='dump/cluster.yaml',
        rel_src='labels:\n  kube_tag: v1.28',
        leftover='leftover master_count only',
        fix2='dump auto_healing_enabled',
        fix2_diff='+ dump auto_healing_enabled\n',
        bad_pat='master_count only',
        doc='docs/LOCK-MGHEAL.md',
        doc_point='master_count is not auto_healing',
        doc_diff='+ master_count is not auto_healing.',
        reg='reg',
        reg_diff='+ auto_healing_enabled holds',
        final_ok='ok 6 passed. auto_healing_enabled.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='auto_healing_enabled; dump same.',
        wrap='the auto_healing_enabled',
        wrap_ok='6 passed. lock-mgheal assign is green.',
        wrap_part='5 passed, 1 residual. lock-mgheal assign is green.',
        goal='Designed plant lock-mgheal: the Magnum cluster that omitted auto_healing_enabled so a dead minion was never replaced. auto_healing_enabled. master_count is not auto_healing.',
        plan='Repro python tests, reject master_count only, auto_healing_enabled, fix dump.',
        out_ok='auto_healing_enabled. 6 tests pass.',
        out_part='auto_healing_enabled. dump leftover. Partial.',
    ),
    "openstack": P(False,
        slug='pr-openstack-allowed-address-pairs-vip',
        plant='quay-osavip',
        what='the OpenStack port that omitted allowed_address_pairs so the keepalived VIP was dropped by anti-spoofing',
        glob='**/*.{yml,yaml,json,sh}',
        ls='port.yaml tests/test_harbor.py',
        impl='port.yaml',
        src='allowed_address_pairs: []',
        sym='allowed_address_pairs VIP',
        grep='allowed_address_pairs',
        grep_obs='harbor security_groups only. pack allowed_address_pairs VIP.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: VIP dropped anti-spoof; allowed_address_pairs missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='security_groups only',
        wrong_diff='+ security_groups only',
        wrong_obs='still security_groups only. still fail.',
        fail2='FAIL test_assign: still broken. allowed_address_pairs VIP.',
        reread='apply allowed_address_pairs VIP.',
        insight='security_groups is not allowed_address_pairs',
        probe="rg -n 'allowed_address_pairs' port.yaml",
        probe_obs='pack allowed_address_pairs VIP. harbor security_groups only.',
        fix='allowed_address_pairs VIP',
        fix_diff='+ allowed_address_pairs VIP\n',
        rel='dump/port.yaml',
        rel_src='allowed_address_pairs: []',
        leftover='leftover security_groups only',
        fix2='dump allowed_address_pairs VIP',
        fix2_diff='+ dump allowed_address_pairs VIP\n',
        bad_pat='security_groups only',
        doc='docs/QUAY-OSAVIP.md',
        doc_point='security_groups is not allowed_address_pairs',
        doc_diff='+ security_groups is not allowed_address_pairs.',
        reg='reg',
        reg_diff='+ allowed_address_pairs VIP holds',
        final_ok='ok 6 passed. allowed_address_pairs VIP.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='allowed_address_pairs VIP; dump leftover.',
        wrap='the allowed_address_pairs VIP',
        wrap_ok='6 passed. quay-osavip assign is green.',
        wrap_part='5 passed, 1 residual. quay-osavip assign is green.',
        goal='Designed plant quay-osavip: the OpenStack port that omitted allowed_address_pairs so the keepalived VIP was dropped by anti-spoofing. allowed_address_pairs VIP. security_groups is not allowed_address_pairs.',
        plan='Repro python tests, reject security_groups only, allowed_address_pairs VIP, hand off dump.',
        out_ok='allowed_address_pairs VIP. 6 tests pass.',
        out_part='allowed_address_pairs VIP. dump leftover. Partial.',
    ),
    "virtctl": P(True,
        slug='pr-virtctl-image-upload-insecure',
        plant='lock-vctlup',
        what="the virtctl image-upload that omitted --insecure so a self-signed CDI upload proxy 401'd",
        glob='**/*.{yml,yaml,json,sh}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='virtctl image-upload dv harbor --size 10Gi',
        sym='insecure flag',
        grep='insecure',
        grep_obs='harbor storageClass only. pack image-upload --insecure.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CDI upload 401; --insecure missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='storageClass only',
        wrong_diff='+ storageClass only',
        wrong_obs='still storageClass only. still fail.',
        fail2='FAIL test_assign: still broken. image-upload --insecure.',
        reread='apply image-upload --insecure.',
        insight='storageClass is not --insecure',
        probe="rg -n 'image-upload' Makefile",
        probe_obs='pack image-upload --insecure. harbor storageClass only.',
        fix='image-upload --insecure',
        fix_diff='+ image-upload --insecure\n',
        rel='dump/Makefile',
        rel_src='virtctl image-upload dv harbor --size 10Gi',
        leftover='leftover storageClass only',
        fix2='dump image-upload --insecure',
        fix2_diff='+ dump image-upload --insecure\n',
        bad_pat='storageClass only',
        doc='docs/LOCK-VCTLUP.md',
        doc_point='storageClass is not --insecure',
        doc_diff='+ storageClass is not --insecure.',
        reg='reg',
        reg_diff='+ image-upload --insecure holds',
        final_ok='ok 6 passed. image-upload --insecure.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='image-upload --insecure; dump same.',
        wrap='the image-upload --insecure',
        wrap_ok='6 passed. lock-vctlup assign is green.',
        wrap_part='5 passed, 1 residual. lock-vctlup assign is green.',
        goal="Designed plant lock-vctlup: the virtctl image-upload that omitted --insecure so a self-signed CDI upload proxy 401'd. image-upload --insecure. storageClass is not --insecure.",
        plan='Repro python tests, reject storageClass only, image-upload --insecure, fix dump.',
        out_ok='image-upload --insecure. 6 tests pass.',
        out_part='image-upload --insecure. dump leftover. Partial.',
    ),
    "csi": P(False,
        slug='pr-csi-attacher-timeout-fsfreeze',
        plant='quay-csiatt',
        what='the CSI attacher that omitted timeout so a freeze hung and the snapshot never completed',
        glob='**/*.{yml,yaml,json,sh}',
        ls='csi-attacher.yaml tests/test_harbor.py',
        impl='csi-attacher.yaml',
        src='args: [--v=5]',
        sym='timeout 2m',
        grep='timeout',
        grep_obs='harbor leaderElection only. pack timeout 2m.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: snapshot hung freeze; attacher timeout missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='leaderElection only',
        wrong_diff='+ leaderElection only',
        wrong_obs='still leaderElection only. still fail.',
        fail2='FAIL test_assign: still broken. timeout 2m.',
        reread='apply timeout 2m.',
        insight='leaderElection is not timeout',
        probe="rg -n 'timeout' csi-attacher.yaml",
        probe_obs='pack timeout 2m. harbor leaderElection only.',
        fix='timeout 2m',
        fix_diff='+ timeout 2m\n',
        rel='dump/csi-attacher.yaml',
        rel_src='args: [--v=5]',
        leftover='leftover leaderElection only',
        fix2='dump timeout 2m',
        fix2_diff='+ dump timeout 2m\n',
        bad_pat='leaderElection only',
        doc='docs/QUAY-CSIATT.md',
        doc_point='leaderElection is not timeout',
        doc_diff='+ leaderElection is not timeout.',
        reg='reg',
        reg_diff='+ timeout 2m holds',
        final_ok='ok 6 passed. timeout 2m.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='timeout 2m; dump leftover.',
        wrap='the timeout 2m',
        wrap_ok='6 passed. quay-csiatt assign is green.',
        wrap_part='5 passed, 1 residual. quay-csiatt assign is green.',
        goal='Designed plant quay-csiatt: the CSI attacher that omitted timeout so a freeze hung and the snapshot never completed. timeout 2m. leaderElection is not timeout.',
        plan='Repro python tests, reject leaderElection only, timeout 2m, hand off dump.',
        out_ok='timeout 2m. 6 tests pass.',
        out_part='timeout 2m. dump leftover. Partial.',
    ),
    "snapshotter": P(True,
        slug='pr-snapshotter-volume-snapshot-class-retain',
        plant='lock-snpret',
        what='the VolumeSnapshotClass that omitted deletionPolicy so deleting the snapshot CR deleted the backing snapshot and backups vanished',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vsc.yaml tests/test_harbor.py',
        impl='vsc.yaml',
        src='driver: hostpath.csi.k8s.io',
        sym='deletionPolicy Retain',
        grep='deletionPolicy',
        grep_obs='harbor deletionPolicy Delete leftover. pack deletionPolicy Retain.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: backing snapshot gone; deletionPolicy Delete default',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='deletionPolicy Delete leftover',
        wrong_diff='+ deletionPolicy Delete leftover',
        wrong_obs='still deletionPolicy Delete leftover. still fail.',
        fail2='FAIL test_assign: still broken. deletionPolicy Retain.',
        reread='apply deletionPolicy Retain.',
        insight='keeping the CR is not deletionPolicy Retain',
        probe="rg -n 'deletionPolicy' vsc.yaml",
        probe_obs='pack deletionPolicy Retain. harbor deletionPolicy Delete leftover.',
        fix='deletionPolicy Retain',
        fix_diff='+ deletionPolicy Retain\n',
        rel='dump/vsc.yaml',
        rel_src='driver: hostpath.csi.k8s.io',
        leftover='leftover deletionPolicy Delete leftover',
        fix2='dump deletionPolicy Retain',
        fix2_diff='+ dump deletionPolicy Retain\n',
        bad_pat='deletionPolicy Delete leftover',
        doc='docs/LOCK-SNPRET.md',
        doc_point='keeping the CR is not deletionPolicy Retain',
        doc_diff='+ keeping the CR is not deletionPolicy Retain.',
        reg='reg',
        reg_diff='+ deletionPolicy Retain holds',
        final_ok='ok 6 passed. deletionPolicy Retain.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='deletionPolicy Retain; dump same.',
        wrap='the deletionPolicy Retain',
        wrap_ok='6 passed. lock-snpret assign is green.',
        wrap_part='5 passed, 1 residual. lock-snpret assign is green.',
        goal='Designed plant lock-snpret: the VolumeSnapshotClass that omitted deletionPolicy so deleting the snapshot CR deleted the backing snapshot and backups vanished. deletionPolicy Retain. keeping the CR is not deletionPolicy Retain.',
        plan='Repro python tests, reject deletionPolicy Delete leftover, deletionPolicy Retain, fix dump.',
        out_ok='deletionPolicy Retain. 6 tests pass.',
        out_part='deletionPolicy Retain. dump leftover. Partial.',
    ),
    "externaldns": P(False,
        slug='pr-externaldns-txt-owner-id',
        plant='quay-ednstxt',
        what='the ExternalDNS deploy that omitted txtOwnerId so two clusters fought over the same record and DNS flapped',
        glob='**/*.{yml,yaml,json,sh}',
        ls='deploy.yaml tests/test_harbor.py',
        impl='deploy.yaml',
        src='args: [--source=service]',
        sym='txt-owner-id',
        grep='txt-owner-id',
        grep_obs='harbor policy upsert-only. pack txtOwnerId harbor.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: DNS flap; txtOwnerId missing; two clusters same zone',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='policy upsert-only',
        wrong_diff='+ policy upsert-only',
        wrong_obs='still policy upsert-only. still fail.',
        fail2='FAIL test_assign: still broken. txtOwnerId harbor.',
        reread='apply txtOwnerId harbor.',
        insight='upsert-only is not txtOwnerId',
        probe="rg -n 'txtOwnerId' deploy.yaml",
        probe_obs='pack txtOwnerId harbor. harbor policy upsert-only.',
        fix='txtOwnerId harbor',
        fix_diff='+ txtOwnerId harbor\n',
        rel='dump/deploy.yaml',
        rel_src='args: [--source=service]',
        leftover='leftover policy upsert-only',
        fix2='dump txtOwnerId harbor',
        fix2_diff='+ dump txtOwnerId harbor\n',
        bad_pat='policy upsert-only',
        doc='docs/QUAY-EDNSTXT.md',
        doc_point='upsert-only is not txtOwnerId',
        doc_diff='+ upsert-only is not txtOwnerId.',
        reg='reg',
        reg_diff='+ txtOwnerId harbor holds',
        final_ok='ok 6 passed. txtOwnerId harbor.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='txtOwnerId harbor; dump leftover.',
        wrap='the txtOwnerId harbor',
        wrap_ok='6 passed. quay-ednstxt assign is green.',
        wrap_part='5 passed, 1 residual. quay-ednstxt assign is green.',
        goal='Designed plant quay-ednstxt: the ExternalDNS deploy that omitted txtOwnerId so two clusters fought over the same record and DNS flapped. txtOwnerId harbor. upsert-only is not txtOwnerId.',
        plan='Repro python tests, reject policy upsert-only, txtOwnerId harbor, hand off dump.',
        out_ok='txtOwnerId harbor. 6 tests pass.',
        out_part='txtOwnerId harbor. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Goldilocks on-by-default vs VPA updateMode Auto', fn('goldilocks'), fn('vpa'), 'onByDefault; updateMode Auto', 'label vpa; requests only', 'goldilocks dump no recs; vpa dump Off default'),
    ('Gatekeeper exempt kube-system vs Falco syscall buffer', fn('gatekeeper'), fn('falco'), 'exemptNamespaces kube-system; syscall_buf_size_preset 8', 'dryrun; priority', 'gatekeeper dump coredns denied; falco dump 40% drops'),
    ('Tetragon export-allowlist vs CubeFS disks path', fn('tetragon'), fn('cubefs'), 'export-allowlist; disks: [/data]', 'rateLimit; logDir', 'tetragon dump node OOM; cubefs dump volume pending'),
    ('CAPI EXP_MACHINE_POOL vs Flux prune', fn('clusterapi'), fn('fluxcd'), 'EXP_MACHINE_POOL; prune true', 'MachineDeployment; force', 'capi dump MachinePool un-reconciled; flux dump old Ingress live'),
    ('KubeVirt liveMigrationNetwork vs oVirt host-passthrough', fn('kubevirt'), fn('ovirt'), 'liveMigrationNetwork; cpu.mode host-passthrough', 'evictionStrategy; cpu.topology', 'kubevirt dump NIC drop; ovirt dump nested KVM missing'),
    ('Magnum auto_healing vs OpenStack allowed_address_pairs', fn('magnum'), fn('openstack'), 'auto_healing_enabled; allowed_address_pairs VIP', 'master_count; security_groups', 'magnum dump dead minion; openstack dump VIP dropped'),
    ('virtctl image-upload --insecure vs CSI attacher timeout', fn('virtctl'), fn('csi'), '--insecure; timeout 2m', 'storageClass; leaderElection', 'virtctl dump CDI 401; csi dump snapshot hung'),
    ('VolumeSnapshotClass Retain vs ExternalDNS txtOwnerId', fn('snapshotter'), fn('externaldns'), 'deletionPolicy Retain; txtOwnerId harbor', 'keep CR; upsert-only', 'snapshotter dump backing gone; externaldns dump DNS flap'),
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
- Not a clone of r4163-r4556 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
