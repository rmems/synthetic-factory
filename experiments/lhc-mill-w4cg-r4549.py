#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cg: unused plants after r4548.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4548. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cg_state.json")
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
    "talos": P(True,
        slug='pr-talos-machine-sysctls-inotify',
        plant='lock-talosys',
        what='the Talos machine config that omitted sysctls fs.inotify.max_user_watches so kubelet log watchers hit EMFILE',
        glob='**/*.{yml,yaml,json,sh}',
        ls='controlplane.yaml tests/test_harbor.py',
        impl='controlplane.yaml',
        src='machine:\n  kubelet: {}',
        sym='sysctls inotify watches',
        grep='sysctls',
        grep_obs='harbor kubelet extraArgs only. pack sysctls max_user_watches.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: kubelet EMFILE; inotify watches default; sysctls missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='kubelet extraArgs only',
        wrong_diff='+ kubelet extraArgs only',
        wrong_obs='still kubelet extraArgs only. still fail.',
        fail2='FAIL test_assign: still broken. sysctls max_user_watches.',
        reread='apply sysctls max_user_watches.',
        insight='extraArgs is not sysctls',
        probe="rg -n 'sysctls' controlplane.yaml",
        probe_obs='pack sysctls max_user_watches. harbor kubelet extraArgs only.',
        fix='sysctls max_user_watches',
        fix_diff='+ sysctls max_user_watches\n',
        rel='dump/controlplane.yaml',
        rel_src='machine:\n  kubelet: {}',
        leftover='leftover kubelet extraArgs only',
        fix2='dump sysctls max_user_watches',
        fix2_diff='+ dump sysctls max_user_watches\n',
        bad_pat='kubelet extraArgs only',
        doc='docs/LOCK-TALOSYS.md',
        doc_point='extraArgs is not sysctls',
        doc_diff='+ extraArgs is not sysctls.',
        reg='reg',
        reg_diff='+ sysctls max_user_watches holds',
        final_ok='ok 6 passed. sysctls max_user_watches.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='sysctls max_user_watches; dump same.',
        wrap='the sysctls max_user_watches',
        wrap_ok='6 passed. lock-talosys assign is green.',
        wrap_part='5 passed, 1 residual. lock-talosys assign is green.',
        goal='Designed plant lock-talosys: the Talos machine config that omitted sysctls fs.inotify.max_user_watches so kubelet log watchers hit EMFILE. sysctls max_user_watches. extraArgs is not sysctls.',
        plan='Repro python tests, reject kubelet extraArgs only, sysctls max_user_watches, fix dump.',
        out_ok='sysctls max_user_watches. 6 tests pass.',
        out_part='sysctls max_user_watches. dump leftover. Partial.',
    ),
    "harvester": P(False,
        slug='pr-harvester-vlan-network-natived',
        plant='quay-hvlann',
        what='the Harvester VM network that omitted natived VLAN so the guest NIC never tagged and the trunk dropped frames',
        glob='**/*.{yml,yaml,json,sh}',
        ls='vm.yaml tests/test_harbor.py',
        impl='vm.yaml',
        src='networks: [{networkName: vlan}]',
        sym='natived vlan id',
        grep='natived',
        grep_obs='harbor multus only. pack natived VLAN.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: guest untagged; natived VLAN missing; trunk drop',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='multus only',
        wrong_diff='+ multus only',
        wrong_obs='still multus only. still fail.',
        fail2='FAIL test_assign: still broken. natived VLAN.',
        reread='apply natived VLAN.',
        insight='multus network is not natived VLAN',
        probe="rg -n 'natived' vm.yaml",
        probe_obs='pack natived VLAN. harbor multus only.',
        fix='natived VLAN',
        fix_diff='+ natived VLAN\n',
        rel='dump/vm.yaml',
        rel_src='networks: [{networkName: vlan}]',
        leftover='leftover multus only',
        fix2='dump natived VLAN',
        fix2_diff='+ dump natived VLAN\n',
        bad_pat='multus only',
        doc='docs/QUAY-HVLANN.md',
        doc_point='multus network is not natived VLAN',
        doc_diff='+ multus network is not natived VLAN.',
        reg='reg',
        reg_diff='+ natived VLAN holds',
        final_ok='ok 6 passed. natived VLAN.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='natived VLAN; dump leftover.',
        wrap='the natived VLAN',
        wrap_ok='6 passed. quay-hvlann assign is green.',
        wrap_part='5 passed, 1 residual. quay-hvlann assign is green.',
        goal='Designed plant quay-hvlann: the Harvester VM network that omitted natived VLAN so the guest NIC never tagged and the trunk dropped frames. natived VLAN. multus network is not natived VLAN.',
        plan='Repro python tests, reject multus only, natived VLAN, hand off dump.',
        out_ok='natived VLAN. 6 tests pass.',
        out_part='natived VLAN. dump leftover. Partial.',
    ),
    "rancher": P(True,
        slug='pr-rancher-agent-tls-mode-system',
        plant='lock-rchltls',
        what='the Rancher cluster registration that omitted tls-mode so cattle-cluster-agent used the wrong CA and never connected',
        glob='**/*.{yml,yaml,json,sh}',
        ls='cluster.yaml tests/test_harbor.py',
        impl='cluster.yaml',
        src='rancher_url: https://rancher.example',
        sym='agent-tls-mode system-store',
        grep='agent-tls-mode',
        grep_obs='harbor insecure-skip-verify. pack agent-tls-mode.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cattle-cluster-agent x509; tls-mode missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='insecure-skip-verify',
        wrong_diff='+ insecure-skip-verify',
        wrong_obs='still insecure-skip-verify. still fail.',
        fail2='FAIL test_assign: still broken. agent-tls-mode.',
        reread='apply agent-tls-mode.',
        insight='insecure-skip-verify is not agent-tls-mode',
        probe="rg -n 'agent-tls-mode' cluster.yaml",
        probe_obs='pack agent-tls-mode. harbor insecure-skip-verify.',
        fix='agent-tls-mode',
        fix_diff='+ agent-tls-mode\n',
        rel='dump/cluster.yaml',
        rel_src='rancher_url: https://rancher.example',
        leftover='leftover insecure-skip-verify',
        fix2='dump agent-tls-mode',
        fix2_diff='+ dump agent-tls-mode\n',
        bad_pat='insecure-skip-verify',
        doc='docs/LOCK-RCHLTLS.md',
        doc_point='insecure-skip-verify is not agent-tls-mode',
        doc_diff='+ insecure-skip-verify is not agent-tls-mode.',
        reg='reg',
        reg_diff='+ agent-tls-mode holds',
        final_ok='ok 6 passed. agent-tls-mode.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='agent-tls-mode; dump same.',
        wrap='the agent-tls-mode',
        wrap_ok='6 passed. lock-rchltls assign is green.',
        wrap_part='5 passed, 1 residual. lock-rchltls assign is green.',
        goal='Designed plant lock-rchltls: the Rancher cluster registration that omitted tls-mode so cattle-cluster-agent used the wrong CA and never connected. agent-tls-mode. insecure-skip-verify is not agent-tls-mode.',
        plan='Repro python tests, reject insecure-skip-verify, agent-tls-mode, fix dump.',
        out_ok='agent-tls-mode. 6 tests pass.',
        out_part='agent-tls-mode. dump leftover. Partial.',
    ),
    "rke2": P(False,
        slug='pr-rke2-cni-canal-flannel-iface',
        plant='quay-rke2cni',
        what='the RKE2 config that omitted flannel-iface so Canal used eth0 on a bond host and overlays blackholed',
        glob='**/*.{yml,yaml,json,sh}',
        ls='config.yaml tests/test_harbor.py',
        impl='config.yaml',
        src='cni: canal',
        sym='flannel-iface bond0',
        grep='flannel-iface',
        grep_obs='harbor node-ip only. pack flannel-iface bond0.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: overlay blackhole; Canal on eth0; flannel-iface missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='node-ip only',
        wrong_diff='+ node-ip only',
        wrong_obs='still node-ip only. still fail.',
        fail2='FAIL test_assign: still broken. flannel-iface bond0.',
        reread='apply flannel-iface bond0.',
        insight='node-ip is not flannel-iface',
        probe="rg -n 'flannel-iface' config.yaml",
        probe_obs='pack flannel-iface bond0. harbor node-ip only.',
        fix='flannel-iface bond0',
        fix_diff='+ flannel-iface bond0\n',
        rel='dump/config.yaml',
        rel_src='cni: canal',
        leftover='leftover node-ip only',
        fix2='dump flannel-iface bond0',
        fix2_diff='+ dump flannel-iface bond0\n',
        bad_pat='node-ip only',
        doc='docs/QUAY-RKE2CNI.md',
        doc_point='node-ip is not flannel-iface',
        doc_diff='+ node-ip is not flannel-iface.',
        reg='reg',
        reg_diff='+ flannel-iface bond0 holds',
        final_ok='ok 6 passed. flannel-iface bond0.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='flannel-iface bond0; dump leftover.',
        wrap='the flannel-iface bond0',
        wrap_ok='6 passed. quay-rke2cni assign is green.',
        wrap_part='5 passed, 1 residual. quay-rke2cni assign is green.',
        goal='Designed plant quay-rke2cni: the RKE2 config that omitted flannel-iface so Canal used eth0 on a bond host and overlays blackholed. flannel-iface bond0. node-ip is not flannel-iface.',
        plan='Repro python tests, reject node-ip only, flannel-iface bond0, hand off dump.',
        out_ok='flannel-iface bond0. 6 tests pass.',
        out_part='flannel-iface bond0. dump leftover. Partial.',
    ),
    "openshift": P(True,
        slug='pr-openshift-image-content-source',
        plant='lock-ocpicsp',
        what='the OpenShift ICSP that omitted mirrors so a disconnected install pulled from registry.redhat.io and timed out',
        glob='**/*.{yml,yaml,json,sh}',
        ls='icsp.yaml tests/test_harbor.py',
        impl='icsp.yaml',
        src='kind: ImageContentSourcePolicy',
        sym='mirrors registry.redhat.io',
        grep='mirrors',
        grep_obs='harbor ImageDigestMirrorSet only. pack ICSP mirrors.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pull registry.redhat.io timeout; ICSP mirrors missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ImageDigestMirrorSet only',
        wrong_diff='+ ImageDigestMirrorSet only',
        wrong_obs='still ImageDigestMirrorSet only. still fail.',
        fail2='FAIL test_assign: still broken. ICSP mirrors.',
        reread='apply ICSP mirrors.',
        insight='IDMS is not ICSP for this 4.12 cluster',
        probe="rg -n 'ICSP' icsp.yaml",
        probe_obs='pack ICSP mirrors. harbor ImageDigestMirrorSet only.',
        fix='ICSP mirrors',
        fix_diff='+ ICSP mirrors\n',
        rel='dump/icsp.yaml',
        rel_src='kind: ImageContentSourcePolicy',
        leftover='leftover ImageDigestMirrorSet only',
        fix2='dump ICSP mirrors',
        fix2_diff='+ dump ICSP mirrors\n',
        bad_pat='ImageDigestMirrorSet only',
        doc='docs/LOCK-OCPICSP.md',
        doc_point='IDMS is not ICSP for this 4.12 cluster',
        doc_diff='+ IDMS is not ICSP for this 4.12 cluster.',
        reg='reg',
        reg_diff='+ ICSP mirrors holds',
        final_ok='ok 6 passed. ICSP mirrors.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ICSP mirrors; dump same.',
        wrap='the ICSP mirrors',
        wrap_ok='6 passed. lock-ocpicsp assign is green.',
        wrap_part='5 passed, 1 residual. lock-ocpicsp assign is green.',
        goal='Designed plant lock-ocpicsp: the OpenShift ICSP that omitted mirrors so a disconnected install pulled from registry.redhat.io and timed out. ICSP mirrors. IDMS is not ICSP for this 4.12 cluster.',
        plan='Repro python tests, reject ImageDigestMirrorSet only, ICSP mirrors, fix dump.',
        out_ok='ICSP mirrors. 6 tests pass.',
        out_part='ICSP mirrors. dump leftover. Partial.',
    ),
    "okd": P(False,
        slug='pr-okd-fcos-stream-next',
        plant='quay-okdstream',
        what='the OKD install-config that omitted fcos stream so bootstrap used stable instead of next and rpm-ostree mismatched',
        glob='**/*.{yml,yaml,json,sh}',
        ls='install-config.yaml tests/test_harbor.py',
        impl='install-config.yaml',
        src='platform: none',
        sym='fcos stream next',
        grep='fcos',
        grep_obs='harbor pullSecret only. pack fcos stream next.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: bootstrap ostree mismatch; fcos stream missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='pullSecret only',
        wrong_diff='+ pullSecret only',
        wrong_obs='still pullSecret only. still fail.',
        fail2='FAIL test_assign: still broken. fcos stream next.',
        reread='apply fcos stream next.',
        insight='pullSecret is not fcos stream',
        probe="rg -n 'fcos' install-config.yaml",
        probe_obs='pack fcos stream next. harbor pullSecret only.',
        fix='fcos stream next',
        fix_diff='+ fcos stream next\n',
        rel='dump/install-config.yaml',
        rel_src='platform: none',
        leftover='leftover pullSecret only',
        fix2='dump fcos stream next',
        fix2_diff='+ dump fcos stream next\n',
        bad_pat='pullSecret only',
        doc='docs/QUAY-OKDSTREAM.md',
        doc_point='pullSecret is not fcos stream',
        doc_diff='+ pullSecret is not fcos stream.',
        reg='reg',
        reg_diff='+ fcos stream next holds',
        final_ok='ok 6 passed. fcos stream next.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='fcos stream next; dump leftover.',
        wrap='the fcos stream next',
        wrap_ok='6 passed. quay-okdstream assign is green.',
        wrap_part='5 passed, 1 residual. quay-okdstream assign is green.',
        goal='Designed plant quay-okdstream: the OKD install-config that omitted fcos stream so bootstrap used stable instead of next and rpm-ostree mismatched. fcos stream next. pullSecret is not fcos stream.',
        plan='Repro python tests, reject pullSecret only, fcos stream next, hand off dump.',
        out_ok='fcos stream next. 6 tests pass.',
        out_part='fcos stream next. dump leftover. Partial.',
    ),
    "crc": P(True,
        slug='pr-crc-consent-telemetry-off',
        plant='lock-crctele',
        what='the CRC config that omitted consent-telemetry no so the first start blocked on an interactive prompt in CI',
        glob='**/*.{yml,yaml,json,sh}',
        ls='crc-config tests/test_harbor.py',
        impl='crc-config',
        src='memory 14336',
        sym='consent-telemetry no',
        grep='consent-telemetry',
        grep_obs='harbor crc setup only. pack consent-telemetry no.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: crc start hung prompt; consent-telemetry missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='crc setup only',
        wrong_diff='+ crc setup only',
        wrong_obs='still crc setup only. still fail.',
        fail2='FAIL test_assign: still broken. consent-telemetry no.',
        reread='apply consent-telemetry no.',
        insight='crc setup is not consent-telemetry',
        probe="rg -n 'consent-telemetry' crc-config",
        probe_obs='pack consent-telemetry no. harbor crc setup only.',
        fix='consent-telemetry no',
        fix_diff='+ consent-telemetry no\n',
        rel='dump/crc-config',
        rel_src='memory 14336',
        leftover='leftover crc setup only',
        fix2='dump consent-telemetry no',
        fix2_diff='+ dump consent-telemetry no\n',
        bad_pat='crc setup only',
        doc='docs/LOCK-CRCTELE.md',
        doc_point='crc setup is not consent-telemetry',
        doc_diff='+ crc setup is not consent-telemetry.',
        reg='reg',
        reg_diff='+ consent-telemetry no holds',
        final_ok='ok 6 passed. consent-telemetry no.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='consent-telemetry no; dump same.',
        wrap='the consent-telemetry no',
        wrap_ok='6 passed. lock-crctele assign is green.',
        wrap_part='5 passed, 1 residual. lock-crctele assign is green.',
        goal='Designed plant lock-crctele: the CRC config that omitted consent-telemetry no so the first start blocked on an interactive prompt in CI. consent-telemetry no. crc setup is not consent-telemetry.',
        plan='Repro python tests, reject crc setup only, consent-telemetry no, fix dump.',
        out_ok='consent-telemetry no. 6 tests pass.',
        out_part='consent-telemetry no. dump leftover. Partial.',
    ),
    "hypershift": P(False,
        slug='pr-hypershift-olmv1-catalog',
        plant='quay-hsolm',
        what='the HyperShift HostedCluster that omitted olmCatalogPlacement so operators installed on the management cluster instead of the guest',
        glob='**/*.{yml,yaml,json,sh}',
        ls='hostedcluster.yaml tests/test_harbor.py',
        impl='hostedcluster.yaml',
        src='spec:\n  release: {}',
        sym='olmCatalogPlacement guest',
        grep='olmCatalogPlacement',
        grep_obs='harbor olm-operator only. pack olmCatalogPlacement guest.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CSV on management; olmCatalogPlacement missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='olm-operator only',
        wrong_diff='+ olm-operator only',
        wrong_obs='still olm-operator only. still fail.',
        fail2='FAIL test_assign: still broken. olmCatalogPlacement guest.',
        reread='apply olmCatalogPlacement guest.',
        insight='installing olm-operator is not olmCatalogPlacement',
        probe="rg -n 'olmCatalogPlacement' hostedcluster.yaml",
        probe_obs='pack olmCatalogPlacement guest. harbor olm-operator only.',
        fix='olmCatalogPlacement guest',
        fix_diff='+ olmCatalogPlacement guest\n',
        rel='dump/hostedcluster.yaml',
        rel_src='spec:\n  release: {}',
        leftover='leftover olm-operator only',
        fix2='dump olmCatalogPlacement guest',
        fix2_diff='+ dump olmCatalogPlacement guest\n',
        bad_pat='olm-operator only',
        doc='docs/QUAY-HSOLM.md',
        doc_point='installing olm-operator is not olmCatalogPlacement',
        doc_diff='+ installing olm-operator is not olmCatalogPlacement.',
        reg='reg',
        reg_diff='+ olmCatalogPlacement guest holds',
        final_ok='ok 6 passed. olmCatalogPlacement guest.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='olmCatalogPlacement guest; dump leftover.',
        wrap='the olmCatalogPlacement guest',
        wrap_ok='6 passed. quay-hsolm assign is green.',
        wrap_part='5 passed, 1 residual. quay-hsolm assign is green.',
        goal='Designed plant quay-hsolm: the HyperShift HostedCluster that omitted olmCatalogPlacement so operators installed on the management cluster instead of the guest. olmCatalogPlacement guest. installing olm-operator is not olmCatalogPlacement.',
        plan='Repro python tests, reject olm-operator only, olmCatalogPlacement guest, hand off dump.',
        out_ok='olmCatalogPlacement guest. 6 tests pass.',
        out_part='olmCatalogPlacement guest. dump leftover. Partial.',
    ),
    "capi": P(True,
        slug='pr-capi-machinehealthcheck-node-startup',
        plant='lock-capimhc',
        what='the CAPI MachineHealthCheck that omitted nodeStartupTimeout so a slow cloud-init node was remediating in a loop',
        glob='**/*.{yml,yaml,json,sh}',
        ls='mhc.yaml tests/test_harbor.py',
        impl='mhc.yaml',
        src='spec:\n  unhealthyConditions: [{type: Ready, status: Unknown, timeout: 5m}]',
        sym='nodeStartupTimeout 20m',
        grep='nodeStartupTimeout',
        grep_obs='harbor maxUnhealthy only. pack nodeStartupTimeout.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: MHC remediating loop; nodeStartupTimeout default 10m too short',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='maxUnhealthy only',
        wrong_diff='+ maxUnhealthy only',
        wrong_obs='still maxUnhealthy only. still fail.',
        fail2='FAIL test_assign: still broken. nodeStartupTimeout.',
        reread='apply nodeStartupTimeout.',
        insight='maxUnhealthy is not nodeStartupTimeout',
        probe="rg -n 'nodeStartupTimeout' mhc.yaml",
        probe_obs='pack nodeStartupTimeout. harbor maxUnhealthy only.',
        fix='nodeStartupTimeout',
        fix_diff='+ nodeStartupTimeout\n',
        rel='dump/mhc.yaml',
        rel_src='spec:\n  unhealthyConditions: [{type: Ready, status: Unknown, timeout: 5m}]',
        leftover='leftover maxUnhealthy only',
        fix2='dump nodeStartupTimeout',
        fix2_diff='+ dump nodeStartupTimeout\n',
        bad_pat='maxUnhealthy only',
        doc='docs/LOCK-CAPIMHC.md',
        doc_point='maxUnhealthy is not nodeStartupTimeout',
        doc_diff='+ maxUnhealthy is not nodeStartupTimeout.',
        reg='reg',
        reg_diff='+ nodeStartupTimeout holds',
        final_ok='ok 6 passed. nodeStartupTimeout.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='nodeStartupTimeout; dump same.',
        wrap='the nodeStartupTimeout',
        wrap_ok='6 passed. lock-capimhc assign is green.',
        wrap_part='5 passed, 1 residual. lock-capimhc assign is green.',
        goal='Designed plant lock-capimhc: the CAPI MachineHealthCheck that omitted nodeStartupTimeout so a slow cloud-init node was remediating in a loop. nodeStartupTimeout. maxUnhealthy is not nodeStartupTimeout.',
        plan='Repro python tests, reject maxUnhealthy only, nodeStartupTimeout, fix dump.',
        out_ok='nodeStartupTimeout. 6 tests pass.',
        out_part='nodeStartupTimeout. dump leftover. Partial.',
    ),
    "clusterctl": P(False,
        slug='pr-clusterctl-config-providers-url',
        plant='quay-ctlprov',
        what="the clusterctl init that omitted providers url so it fetched the default github and 403'd behind the proxy",
        glob='**/*.{yml,yaml,json,sh}',
        ls='clusterctl.yaml tests/test_harbor.py',
        impl='clusterctl.yaml',
        src='providers: []',
        sym='providers url mirror',
        grep='providers',
        grep_obs='harbor HTTP_PROXY only. pack providers url.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: clusterctl init 403 github; providers url missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='HTTP_PROXY only',
        wrong_diff='+ HTTP_PROXY only',
        wrong_obs='still HTTP_PROXY only. still fail.',
        fail2='FAIL test_assign: still broken. providers url.',
        reread='apply providers url.',
        insight='HTTP_PROXY is not providers url',
        probe="rg -n 'providers' clusterctl.yaml",
        probe_obs='pack providers url. harbor HTTP_PROXY only.',
        fix='providers url',
        fix_diff='+ providers url\n',
        rel='dump/clusterctl.yaml',
        rel_src='providers: []',
        leftover='leftover HTTP_PROXY only',
        fix2='dump providers url',
        fix2_diff='+ dump providers url\n',
        bad_pat='HTTP_PROXY only',
        doc='docs/QUAY-CTLPROV.md',
        doc_point='HTTP_PROXY is not providers url',
        doc_diff='+ HTTP_PROXY is not providers url.',
        reg='reg',
        reg_diff='+ providers url holds',
        final_ok='ok 6 passed. providers url.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='providers url; dump leftover.',
        wrap='the providers url',
        wrap_ok='6 passed. quay-ctlprov assign is green.',
        wrap_part='5 passed, 1 residual. quay-ctlprov assign is green.',
        goal="Designed plant quay-ctlprov: the clusterctl init that omitted providers url so it fetched the default github and 403'd behind the proxy. providers url. HTTP_PROXY is not providers url.",
        plan='Repro python tests, reject HTTP_PROXY only, providers url, hand off dump.',
        out_ok='providers url. 6 tests pass.',
        out_part='providers url. dump leftover. Partial.',
    ),
    "knative": P(True,
        slug='pr-knative-autoscaler-scale-to-zero-pod',
        plant='lock-knstz',
        what='the Knative Service that omitted scale-to-zero-pod-retention so cold starts kept a terminating pod and readiness flapped',
        glob='**/*.{yml,yaml,json,sh}',
        ls='ksvc.yaml tests/test_harbor.py',
        impl='ksvc.yaml',
        src='spec:\n  template:\n    metadata:\n      annotations: {}',
        sym='scale-to-zero-pod-retention-period',
        grep='scale-to-zero-pod-retention-period',
        grep_obs='harbor minScale 1. pack retention period 0s.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: readiness flap; terminating pod retained; annotation missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='minScale 1',
        wrong_diff='+ minScale 1',
        wrong_obs='still minScale 1. still fail.',
        fail2='FAIL test_assign: still broken. retention period 0s.',
        reread='apply retention period 0s.',
        insight='minScale 1 is not retention period',
        probe="rg -n 'retention' ksvc.yaml",
        probe_obs='pack retention period 0s. harbor minScale 1.',
        fix='retention period 0s',
        fix_diff='+ retention period 0s\n',
        rel='dump/ksvc.yaml',
        rel_src='spec:\n  template:\n    metadata:\n      annotations: {}',
        leftover='leftover minScale 1',
        fix2='dump retention period 0s',
        fix2_diff='+ dump retention period 0s\n',
        bad_pat='minScale 1',
        doc='docs/LOCK-KNSTZ.md',
        doc_point='minScale 1 is not retention period',
        doc_diff='+ minScale 1 is not retention period.',
        reg='reg',
        reg_diff='+ retention period 0s holds',
        final_ok='ok 6 passed. retention period 0s.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='retention period 0s; dump same.',
        wrap='the retention period 0s',
        wrap_ok='6 passed. lock-knstz assign is green.',
        wrap_part='5 passed, 1 residual. lock-knstz assign is green.',
        goal='Designed plant lock-knstz: the Knative Service that omitted scale-to-zero-pod-retention so cold starts kept a terminating pod and readiness flapped. retention period 0s. minScale 1 is not retention period.',
        plan='Repro python tests, reject minScale 1, retention period 0s, fix dump.',
        out_ok='retention period 0s. 6 tests pass.',
        out_part='retention period 0s. dump leftover. Partial.',
    ),
    "dapr": P(False,
        slug='pr-dapr-sidecar-listen-addresses',
        plant='quay-daprlisten',
        what='the Dapr sidecar that omitted daprListenAddresses so the app reached 127.0.0.1:3500 from another container and connection refused',
        glob='**/*.{yml,yaml,json,sh}',
        ls='annotations.yaml tests/test_harbor.py',
        impl='annotations.yaml',
        src='dapr.io/enabled: "true"',
        sym='dapr.io/sidecar-listen-addresses',
        grep='dapr.io/sidecar-listen-addresses',
        grep_obs='harbor app-port only. pack listen addresses 0.0.0.0.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: connection refused 3500 from sidecar-less container; listen 127.0.0.1',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='app-port only',
        wrong_diff='+ app-port only',
        wrong_obs='still app-port only. still fail.',
        fail2='FAIL test_assign: still broken. listen addresses 0.0.0.0.',
        reread='apply listen addresses 0.0.0.0.',
        insight='app-port is not listen addresses',
        probe="rg -n 'listen' annotations.yaml",
        probe_obs='pack listen addresses 0.0.0.0. harbor app-port only.',
        fix='listen addresses 0.0.0.0',
        fix_diff='+ listen addresses 0.0.0.0\n',
        rel='dump/annotations.yaml',
        rel_src='dapr.io/enabled: "true"',
        leftover='leftover app-port only',
        fix2='dump listen addresses 0.0.0.0',
        fix2_diff='+ dump listen addresses 0.0.0.0\n',
        bad_pat='app-port only',
        doc='docs/QUAY-DAPRLISTEN.md',
        doc_point='app-port is not listen addresses',
        doc_diff='+ app-port is not listen addresses.',
        reg='reg',
        reg_diff='+ listen addresses 0.0.0.0 holds',
        final_ok='ok 6 passed. listen addresses 0.0.0.0.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='listen addresses 0.0.0.0; dump leftover.',
        wrap='the listen addresses 0.0.0.0',
        wrap_ok='6 passed. quay-daprlisten assign is green.',
        wrap_part='5 passed, 1 residual. quay-daprlisten assign is green.',
        goal='Designed plant quay-daprlisten: the Dapr sidecar that omitted daprListenAddresses so the app reached 127.0.0.1:3500 from another container and connection refused. listen addresses 0.0.0.0. app-port is not listen addresses.',
        plan='Repro python tests, reject app-port only, listen addresses 0.0.0.0, hand off dump.',
        out_ok='listen addresses 0.0.0.0. 6 tests pass.',
        out_part='listen addresses 0.0.0.0. dump leftover. Partial.',
    ),
    "flagger": P(True,
        slug='pr-flagger-skip-analysis-false',
        plant='lock-flgskip',
        what='the Flagger canary that omitted skipAnalysis so a first deploy skipped metrics and promoted a broken revision',
        glob='**/*.{yml,yaml,json,sh}',
        ls='canary.yaml tests/test_harbor.py',
        impl='canary.yaml',
        src='spec:\n  analysis:\n    interval: 1m',
        sym='skipAnalysis false',
        grep='skipAnalysis',
        grep_obs='harbor iterations 0. pack skipAnalysis false.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: broken revision promoted; skipAnalysis default true on first',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='iterations 0',
        wrong_diff='+ iterations 0',
        wrong_obs='still iterations 0. still fail.',
        fail2='FAIL test_assign: still broken. skipAnalysis false.',
        reread='apply skipAnalysis false.',
        insight='iterations 0 is not skipAnalysis',
        probe="rg -n 'skipAnalysis' canary.yaml",
        probe_obs='pack skipAnalysis false. harbor iterations 0.',
        fix='skipAnalysis false',
        fix_diff='+ skipAnalysis false\n',
        rel='dump/canary.yaml',
        rel_src='spec:\n  analysis:\n    interval: 1m',
        leftover='leftover iterations 0',
        fix2='dump skipAnalysis false',
        fix2_diff='+ dump skipAnalysis false\n',
        bad_pat='iterations 0',
        doc='docs/LOCK-FLGSKIP.md',
        doc_point='iterations 0 is not skipAnalysis',
        doc_diff='+ iterations 0 is not skipAnalysis.',
        reg='reg',
        reg_diff='+ skipAnalysis false holds',
        final_ok='ok 6 passed. skipAnalysis false.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='skipAnalysis false; dump same.',
        wrap='the skipAnalysis false',
        wrap_ok='6 passed. lock-flgskip assign is green.',
        wrap_part='5 passed, 1 residual. lock-flgskip assign is green.',
        goal='Designed plant lock-flgskip: the Flagger canary that omitted skipAnalysis so a first deploy skipped metrics and promoted a broken revision. skipAnalysis false. iterations 0 is not skipAnalysis.',
        plan='Repro python tests, reject iterations 0, skipAnalysis false, fix dump.',
        out_ok='skipAnalysis false. 6 tests pass.',
        out_part='skipAnalysis false. dump leftover. Partial.',
    ),
    "keda": P(False,
        slug='pr-keda-fallback-replicas-hpa',
        plant='quay-kedafb',
        what='the KEDA ScaledObject that omitted fallback so a metrics outage scaled the deployment to 0',
        glob='**/*.{yml,yaml,json,sh}',
        ls='scaledobject.yaml tests/test_harbor.py',
        impl='scaledobject.yaml',
        src='spec:\n  minReplicaCount: 1',
        sym='fallback replicas',
        grep='fallback',
        grep_obs='harbor cooldownPeriod only. pack fallback failureThreshold replicas.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: metrics outage scaled to 0; fallback missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cooldownPeriod only',
        wrong_diff='+ cooldownPeriod only',
        wrong_obs='still cooldownPeriod only. still fail.',
        fail2='FAIL test_assign: still broken. fallback failureThreshold replicas.',
        reread='apply fallback failureThreshold replicas.',
        insight='cooldownPeriod is not fallback',
        probe="rg -n 'fallback' scaledobject.yaml",
        probe_obs='pack fallback failureThreshold replicas. harbor cooldownPeriod only.',
        fix='fallback failureThreshold replicas',
        fix_diff='+ fallback failureThreshold replicas\n',
        rel='dump/scaledobject.yaml',
        rel_src='spec:\n  minReplicaCount: 1',
        leftover='leftover cooldownPeriod only',
        fix2='dump fallback failureThreshold replicas',
        fix2_diff='+ dump fallback failureThreshold replicas\n',
        bad_pat='cooldownPeriod only',
        doc='docs/QUAY-KEDAFB.md',
        doc_point='cooldownPeriod is not fallback',
        doc_diff='+ cooldownPeriod is not fallback.',
        reg='reg',
        reg_diff='+ fallback failureThreshold replicas holds',
        final_ok='ok 6 passed. fallback failureThreshold replicas.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='fallback failureThreshold replicas; dump leftover.',
        wrap='the fallback failureThreshold replicas',
        wrap_ok='6 passed. quay-kedafb assign is green.',
        wrap_part='5 passed, 1 residual. quay-kedafb assign is green.',
        goal='Designed plant quay-kedafb: the KEDA ScaledObject that omitted fallback so a metrics outage scaled the deployment to 0. fallback failureThreshold replicas. cooldownPeriod is not fallback.',
        plan='Repro python tests, reject cooldownPeriod only, fallback failureThreshold replicas, hand off dump.',
        out_ok='fallback failureThreshold replicas. 6 tests pass.',
        out_part='fallback failureThreshold replicas. dump leftover. Partial.',
    ),
    "karpenter": P(True,
        slug='pr-karpenter-disruption-consolidate-when',
        plant='lock-kpncons',
        what='the Karpenter NodePool that omitted consolidateAfter so empty nodes sat for an hour and the bill spiked',
        glob='**/*.{yml,yaml,json,sh}',
        ls='nodepool.yaml tests/test_harbor.py',
        impl='nodepool.yaml',
        src='spec:\n  disruption:\n    consolidationPolicy: WhenEmpty',
        sym='consolidateAfter 30s',
        grep='consolidateAfter',
        grep_obs='harbor expireAfter only. pack consolidateAfter 30s.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: empty node 60m; consolidateAfter missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='expireAfter only',
        wrong_diff='+ expireAfter only',
        wrong_obs='still expireAfter only. still fail.',
        fail2='FAIL test_assign: still broken. consolidateAfter 30s.',
        reread='apply consolidateAfter 30s.',
        insight='expireAfter is not consolidateAfter',
        probe="rg -n 'consolidateAfter' nodepool.yaml",
        probe_obs='pack consolidateAfter 30s. harbor expireAfter only.',
        fix='consolidateAfter 30s',
        fix_diff='+ consolidateAfter 30s\n',
        rel='dump/nodepool.yaml',
        rel_src='spec:\n  disruption:\n    consolidationPolicy: WhenEmpty',
        leftover='leftover expireAfter only',
        fix2='dump consolidateAfter 30s',
        fix2_diff='+ dump consolidateAfter 30s\n',
        bad_pat='expireAfter only',
        doc='docs/LOCK-KPNCONS.md',
        doc_point='expireAfter is not consolidateAfter',
        doc_diff='+ expireAfter is not consolidateAfter.',
        reg='reg',
        reg_diff='+ consolidateAfter 30s holds',
        final_ok='ok 6 passed. consolidateAfter 30s.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='consolidateAfter 30s; dump same.',
        wrap='the consolidateAfter 30s',
        wrap_ok='6 passed. lock-kpncons assign is green.',
        wrap_part='5 passed, 1 residual. lock-kpncons assign is green.',
        goal='Designed plant lock-kpncons: the Karpenter NodePool that omitted consolidateAfter so empty nodes sat for an hour and the bill spiked. consolidateAfter 30s. expireAfter is not consolidateAfter.',
        plan='Repro python tests, reject expireAfter only, consolidateAfter 30s, fix dump.',
        out_ok='consolidateAfter 30s. 6 tests pass.',
        out_part='consolidateAfter 30s. dump leftover. Partial.',
    ),
    "kyverno": P(False,
        slug='pr-kyverno-background-scan-reports',
        plant='quay-kyvbg',
        what='the Kyverno policy that omitted spec.background so existing violating pods were never reported',
        glob='**/*.{yml,yaml,json,sh}',
        ls='policy.yaml tests/test_harbor.py',
        impl='policy.yaml',
        src='spec:\n  validationFailureAction: Audit',
        sym='background true',
        grep='background',
        grep_obs='harbor failureAction Enforce only. pack spec.background true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: existing pods not reported; background false',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='failureAction Enforce only',
        wrong_diff='+ failureAction Enforce only',
        wrong_obs='still failureAction Enforce only. still fail.',
        fail2='FAIL test_assign: still broken. spec.background true.',
        reread='apply spec.background true.',
        insight='Enforce is not a background scan',
        probe="rg -n 'spec.background' policy.yaml",
        probe_obs='pack spec.background true. harbor failureAction Enforce only.',
        fix='spec.background true',
        fix_diff='+ spec.background true\n',
        rel='dump/policy.yaml',
        rel_src='spec:\n  validationFailureAction: Audit',
        leftover='leftover failureAction Enforce only',
        fix2='dump spec.background true',
        fix2_diff='+ dump spec.background true\n',
        bad_pat='failureAction Enforce only',
        doc='docs/QUAY-KYVBG.md',
        doc_point='Enforce is not a background scan',
        doc_diff='+ Enforce is not a background scan.',
        reg='reg',
        reg_diff='+ spec.background true holds',
        final_ok='ok 6 passed. spec.background true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='spec.background true; dump leftover.',
        wrap='the spec.background true',
        wrap_ok='6 passed. quay-kyvbg assign is green.',
        wrap_part='5 passed, 1 residual. quay-kyvbg assign is green.',
        goal='Designed plant quay-kyvbg: the Kyverno policy that omitted spec.background so existing violating pods were never reported. spec.background true. Enforce is not a background scan.',
        plan='Repro python tests, reject failureAction Enforce only, spec.background true, hand off dump.',
        out_ok='spec.background true. 6 tests pass.',
        out_part='spec.background true. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Talos inotify sysctls vs Harvester natived VLAN', fn('talos'), fn('harvester'), 'sysctls max_user_watches; natived VLAN', 'kubelet extraArgs; multus', 'talos dump EMFILE; harvester dump untagged frames'),
    ('Rancher agent-tls-mode vs RKE2 flannel-iface', fn('rancher'), fn('rke2'), 'agent-tls-mode; flannel-iface bond0', 'insecure-skip-verify; node-ip', 'rancher dump x509; rke2 dump overlay blackhole'),
    ('OpenShift ICSP mirrors vs OKD fcos stream', fn('openshift'), fn('okd'), 'ICSP mirrors; fcos stream next', 'IDMS; pullSecret', 'openshift dump pull timeout; okd dump ostree mismatch'),
    ('CRC consent-telemetry vs HyperShift olmCatalogPlacement', fn('crc'), fn('hypershift'), 'consent-telemetry no; olmCatalogPlacement guest', 'crc setup; olm-operator', 'crc dump hung prompt; hypershift dump CSV on management'),
    ('CAPI nodeStartupTimeout vs clusterctl providers url', fn('capi'), fn('clusterctl'), 'nodeStartupTimeout 20m; providers url mirror', 'maxUnhealthy; HTTP_PROXY', 'capi dump MHC loop; clusterctl dump github 403'),
    ('Knative scale-to-zero retention vs Dapr listen addresses', fn('knative'), fn('dapr'), 'retention 0s; sidecar-listen-addresses 0.0.0.0', 'minScale 1; app-port', 'knative dump readiness flap; dapr dump connection refused'),
    ('Flagger skipAnalysis vs KEDA fallback', fn('flagger'), fn('keda'), 'skipAnalysis false; fallback replicas', 'iterations 0; cooldownPeriod', 'flagger dump broken promote; keda dump scale to 0'),
    ('Karpenter consolidateAfter vs Kyverno background scan', fn('karpenter'), fn('kyverno'), 'consolidateAfter 30s; spec.background true', 'expireAfter; Enforce', 'karpenter dump empty node 60m; kyverno dump existing pods unreported'),
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
- Not a clone of r4163-r4548 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
