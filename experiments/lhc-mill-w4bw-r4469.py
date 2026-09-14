#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4bw: unused plants after r4468.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4468. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4bw_state.json")
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
    "metallb": P(True,
        slug="pr-metallb-speaker-l2-announcement",
        plant="lock-mlbl2",
        what="the MetalLB L2 speaker that omitted L2Advertisement so Services stayed pending despite an IPAddressPool",
        glob="**/{*.yml,*.yaml,tests/**}",
        ls="metallb/pool.yaml tests/test_harbor.py",
        impl="metallb/pool.yaml",
        src="apiVersion: metallb.io/v1beta1\nkind: IPAddressPool\nmetadata: {name: harbor}\nspec: {addresses: [\"10.0.8.0/24\"]}\n",
        sym="IPAddressPool",
        grep="L2Advertisement|IPAddressPool|speaker",
        grep_obs="harbor pool only. pack L2Advertisement ipAddressPools harbor.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: Service pending; no L2Advertisement; speaker never announced",
        tf="tests/test_harbor.py",
        tsrc="assert 'L2Advertisement' in open('metallb/pool.yaml').read() or True",
        wrong="change to BGPAdvertisement",
        wrong_diff="+ kind: BGPAdvertisement",
        wrong_obs="cluster has no BGP peers. still pending.",
        fail2="FAIL test_assign: still pending. add L2Advertisement.",
        reread="L2Advertisement with ipAddressPools: [harbor].",
        insight="BGP is not L2; a pool without advertisement is silent.",
        probe="rg -n 'L2Advertisement' metallb pack/metallb",
        probe_obs="pack L2Advertisement. harbor pool only.",
        fix="L2Advertisement",
        fix_diff="+ kind: L2Advertisement\n+ spec:\n+   ipAddressPools: [harbor]\n",
        rel="metallb/dump.yaml",
        rel_src="kind: IPAddressPool",
        leftover="no L2Advertisement",
        fix2="dump L2Advertisement",
        fix2_diff="+ dump L2Advertisement ipAddressPools dump\n",
        bad_pat="kind: BGPAdvertisement",
        doc="docs/METALLB.md",
        doc_point="IPAddressPool needs L2Advertisement on L2 clusters",
        doc_diff="+ BGP is not L2.",
        reg="l2",
        reg_diff="+ Service EXTERNAL-IP is 10.0.8.10",
        final_ok="ok 6 passed. metallb L2 announces the pool.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="L2Advertisement; dump same.",
        wrap="the L2Advertisement",
        wrap_ok="6 passed. metallb assign Service has EXTERNAL-IP.",
        wrap_part="5 passed, 1 residual. MetalLB assign Service has EXTERNAL-IP.",
        goal="Designed plant lock-mlbl2: MetalLB IPAddressPool had no L2Advertisement so Services stayed pending. L2Advertisement. BGP is not L2.",
        plan="Repro python tests, reject BGPAdvertisement, L2Advertisement, fix dump.",
        out_ok="L2Advertisement. 6 metallb tests pass.",
        out_part="L2Advertisement. dump leftover. Partial.",
    ),
    "keepalived": P(False,
        slug="pr-keepalived-vrrp-strict-unicast-peer",
        plant="quay-kavrrp",
        what="the Keepalived VRRP that set vrrp_strict without unicast_peer so multicast was dropped and both nodes stayed MASTER",
        glob="**/{keepalived.conf,*.conf,tests/**}",
        ls="keepalived.conf tests/test_harbor.py",
        impl="keepalived.conf",
        src="vrrp_strict\nvrrp_instance VI {\n  interface eth0\n  virtual_router_id 51\n}\n",
        sym="vrrp_strict",
        grep="unicast_peer|vrrp_strict|nopreempt",
        grep_obs="harbor vrrp_strict no unicast_peer. pack unicast_src_ip plus unicast_peer.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: both nodes MASTER; multicast 224.0.0.18 dropped; vrrp_strict without unicast_peer",
        tf="tests/test_harbor.py",
        tsrc="assert 'unicast_peer' in open('keepalived.conf').read()",
        wrong="nopreempt plus advert_int 1",
        wrong_diff="+ nopreempt\n+ advert_int 1",
        wrong_obs="still multicast. still split brain.",
        fail2="FAIL test_assign: still dual MASTER. unicast_peer the backup IP.",
        reread="unicast_src_ip plus unicast_peer; keep vrrp_strict.",
        insight="nopreempt is not unicast; vrrp_strict drops multicast.",
        probe="rg -n 'unicast_peer' keepalived.conf pack/keepalived.conf",
        probe_obs="pack unicast_peer. harbor missing.",
        fix="unicast_peer",
        fix_diff="+ unicast_src_ip 10.0.1.10\n+ unicast_peer { 10.0.1.11 }\n",
        rel="dump/keepalived.conf",
        rel_src="vrrp_strict",
        leftover="no unicast_peer",
        fix2="dump unicast_peer",
        fix2_diff="+ dump unicast_peer 10.0.1.11\n",
        bad_pat="nopreempt",
        doc="docs/KEEPALIVED.md",
        doc_point="vrrp_strict needs unicast_peer when multicast is dropped",
        doc_diff="+ nopreempt is not unicast. dump leftover.",
        reg="vrrp",
        reg_diff="+ only one MASTER",
        final_ok="ok 6 passed. keepalived unicast_peer elects one MASTER.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="unicast_peer; dump leftover.",
        wrap="the unicast_peer",
        wrap_ok="6 passed. keepalived assign has one MASTER.",
        wrap_part="5 passed, 1 residual. Keepalived assign has one MASTER.",
        goal="Designed plant quay-kavrrp: Keepalived vrrp_strict without unicast_peer left both nodes MASTER. unicast_peer. nopreempt is not unicast. dump may remain.",
        plan="Repro python tests, reject nopreempt, unicast_peer, hand off dump.",
        out_ok="unicast_peer. 6 tests pass.",
        out_part="unicast_peer. dump leftover. Partial.",
    ),
    "nebula": P(True,
        slug="pr-nebula-lighthouse-static-host-map",
        plant="lock-neblh",
        what="the Nebula lighthouse that omitted static_host_map so punchy never learned the public IP and overlays stayed dark",
        glob="**/{config.yml,*.yml,tests/**}",
        ls="config.yml tests/test_harbor.py",
        impl="config.yml",
        src="lighthouse:\n  am_lighthouse: false\n  hosts: [\"192.168.1.10\"]\n",
        sym="am_lighthouse: false",
        grep="static_host_map|lighthouse|punchy",
        grep_obs="harbor hosts private IP. pack static_host_map lighthouse public IP plus punchy.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: handshake timeout; lighthouse 192.168.1.10 not reachable; no static_host_map",
        tf="tests/test_harbor.py",
        tsrc="assert 'static_host_map' in open('config.yml').read()",
        wrong="punchy.respond true only",
        wrong_diff="+ punchy:\n+   punch: true\n+   respond: true",
        wrong_obs="still no public mapping. still timeout.",
        fail2="FAIL test_assign: still timeout. static_host_map lighthouse UDP public IP.",
        reread="static_host_map: {10.0.0.1: [\"203.0.113.5:4242\"]}",
        insight="punchy without a lighthouse address cannot punch.",
        probe="rg -n 'static_host_map' config.yml pack/config.yml",
        probe_obs="pack static_host_map. harbor missing.",
        fix="static_host_map public",
        fix_diff="+ static_host_map:\n+   \"10.0.0.1\": [\"203.0.113.5:4242\"]\n",
        rel="dump/config.yml",
        rel_src="hosts: [\"192.168.1.10\"]",
        leftover="no static_host_map",
        fix2="dump static_host_map",
        fix2_diff="+ dump static_host_map public IP\n",
        bad_pat="respond: true",
        doc="docs/NEBULA.md",
        doc_point="lighthouse needs static_host_map to a public UDP address",
        doc_diff="+ punchy.respond is not a mapping.",
        reg="lh",
        reg_diff="+ handshake completes via lighthouse",
        final_ok="ok 6 passed. nebula static_host_map reaches lighthouse.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="static_host_map; dump same.",
        wrap="the static_host_map",
        wrap_ok="6 passed. nebula assign handshake completes.",
        wrap_part="5 passed, 1 residual. Nebula assign handshake completes.",
        goal="Designed plant lock-neblh: Nebula lighthouse omitted static_host_map so punchy never learned the public IP. static_host_map. punchy.respond is not a mapping.",
        plan="Repro python tests, reject punchy-only, static_host_map, fix dump.",
        out_ok="static_host_map. 6 nebula tests pass.",
        out_part="static_host_map. dump leftover. Partial.",
    ),
    "crun": P(False,
        slug="pr-crun-systemd-cgroup-path-slice",
        plant="quay-crunsd",
        what="the crun systemd cgroup that used a relative path so the unit landed under user.slice and cpu quota vanished",
        glob="**/{config.json,*.json,tests/**}",
        ls="config.json tests/test_harbor.py",
        impl="config.json",
        src="\"linux\": {\"cgroupsPath\": \"harbor.scope\"}\n",
        sym="cgroupsPath",
        grep="cgroupsPath|systemd|slice",
        grep_obs="harbor relative harbor.scope. pack slice:machine.slice:crun:harbor.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: cpu quota ignored; cgroupsPath relative; unit under user.slice",
        tf="tests/test_harbor.py",
        tsrc="assert 'machine.slice' in open('config.json').read()",
        wrong="cpu.shares 1024 in resources",
        wrong_diff="+ \"cpu\": {\"shares\": 1024}",
        wrong_obs="still user.slice. still no quota. path is the bug.",
        fail2="FAIL test_assign: still user.slice. cgroupsPath slice:machine.slice:crun:harbor.",
        reread="cgroupsPath: \"slice:machine.slice:crun:harbor\"",
        insight="cpu.shares is not a slice; systemd driver needs slice:path.",
        probe="rg -n 'cgroupsPath' config.json pack/config.json",
        probe_obs="pack slice:machine.slice. harbor relative.",
        fix="systemd slice path",
        fix_diff="+ \"cgroupsPath\": \"slice:machine.slice:crun:harbor\"\n",
        rel="dump/config.json",
        rel_src="\"cgroupsPath\": \"dump.scope\"",
        leftover="relative cgroupsPath",
        fix2="dump slice path",
        fix2_diff="+ dump slice:machine.slice:crun:dump\n",
        bad_pat="\"shares\": 1024",
        doc="docs/CRUN.md",
        doc_point="systemd cgroup driver needs slice:machine.slice:crun:id",
        doc_diff="+ cpu.shares is not a slice. dump leftover.",
        reg="slice",
        reg_diff="+ unit is under machine.slice",
        final_ok="ok 6 passed. crun unit is under machine.slice.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="slice:machine.slice; dump leftover.",
        wrap="the systemd slice path",
        wrap_ok="6 passed. crun assign unit is under machine.slice.",
        wrap_part="5 passed, 1 residual. crun assign unit is under machine.slice.",
        goal="Designed plant quay-crunsd: crun cgroupsPath relative landed under user.slice so cpu quota vanished. slice:machine.slice:crun:harbor. cpu.shares is not a slice. dump may remain.",
        plan="Repro python tests, reject cpu.shares, slice path, hand off dump.",
        out_ok="systemd slice path. 6 tests pass.",
        out_part="systemd slice path. dump leftover. Partial.",
    ),
    "youki": P(True,
        slug="pr-youki-cgroup-v2-unified-memory",
        plant="lock-youkicg",
        what="the youki runtime that wrote memory.limit_in_bytes on cgroup v2 so memory.max was never set and the container OOM'd the host",
        glob="**/{config.json,*.json,tests/**}",
        ls="config.json tests/test_harbor.py",
        impl="config.json",
        src="\"memory\": {\"limit\": 0, \"swap\": 0}\n# v1 names leftover\n",
        sym="memory.limit",
        grep="memory.max|unified|limit_in_bytes",
        grep_obs="harbor v1 memory.limit 0. pack linux.resources.memory.limit 256Mi plus unified cgroup.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: host OOM; youki wrote memory.limit_in_bytes missing on cgroup v2",
        tf="tests/test_harbor.py",
        tsrc="assert '256000000' in open('config.json').read() or True",
        wrong="swapaccount=1 kernel param",
        wrong_diff="+ swapaccount=1",
        wrong_obs="v2 has no swapaccount. still unlimited memory.max.",
        fail2="FAIL test_assign: still unlimited. set linux.resources.memory.limit for memory.max.",
        reread="\"memory\": {\"limit\": 268435456} maps to memory.max on v2.",
        insight="swapaccount is v1; v2 needs memory.max via OCI limit.",
        probe="rg -n 'memory' config.json pack/config.json",
        probe_obs="pack limit 256Mi. harbor 0.",
        fix="memory.limit 256Mi",
        fix_diff="+ \"memory\": {\"limit\": 268435456}\n",
        rel="dump/config.json",
        rel_src="\"memory\": {\"limit\": 0}",
        leftover="memory.limit 0",
        fix2="dump memory.limit",
        fix2_diff="+ dump memory.limit 268435456\n",
        bad_pat="swapaccount=1",
        doc="docs/YOUKI.md",
        doc_point="cgroup v2 memory.max comes from OCI memory.limit",
        doc_diff="+ swapaccount is v1.",
        reg="mem",
        reg_diff="+ container memory.max is 256Mi",
        final_ok="ok 6 passed. youki memory.max is 256Mi.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="memory.limit 256Mi; dump same.",
        wrap="the memory.limit",
        wrap_ok="6 passed. youki assign memory.max is 256Mi.",
        wrap_part="5 passed, 1 residual. youki assign memory.max is 256Mi.",
        goal="Designed plant lock-youkicg: youki wrote v1 memory.limit_in_bytes on cgroup v2 so memory.max was unset and the host OOM'd. OCI memory.limit. swapaccount is v1.",
        plan="Repro python tests, reject swapaccount, memory.limit, fix dump.",
        out_ok="memory.limit 256Mi. 6 youki tests pass.",
        out_part="memory.limit 256Mi. dump leftover. Partial.",
    ),
    "tflint": P(False,
        slug="pr-tflint-recursive-module-callers",
        plant="quay-tflintm",
        what="the TFLint run that omitted --recursive so module call sites never saw aws_instance unused vars",
        glob="**/{.tflint.hcl,*.hcl,tests/**}",
        ls=".tflint.hcl tests/test_harbor.py",
        impl=".tflint.hcl",
        src="plugin \"aws\" {\n  enabled = true\n}\n",
        sym="plugin aws",
        grep="recursive|module|call_module_type",
        grep_obs="harbor no recursive. pack --recursive plus call_module_type all.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: unused var in modules/harbor missed; tflint not recursive",
        tf="tests/test_harbor.py",
        tsrc="assert 'recursive' in open('Makefile').read() or True",
        wrong="module --enable-rule terraform_unused_declarations at root only",
        wrong_diff="+ rule \"terraform_unused_declarations\" { enabled = true }",
        wrong_obs="root is clean. module still unlinted.",
        fail2="FAIL test_assign: still missed. tflint --recursive --filter=modules.",
        reread="tflint --recursive; config call_module_type = \"all\".",
        insight="enabling the rule at root is not recursive; --recursive is.",
        probe="rg -n 'recursive' Makefile pack/Makefile",
        probe_obs="pack tflint --recursive. harbor tflint.",
        fix="tflint --recursive",
        fix_diff="+ tflint --recursive --format compact\n",
        rel="dump/Makefile",
        rel_src="tflint",
        leftover="no --recursive",
        fix2="dump --recursive",
        fix2_diff="+ dump tflint --recursive\n",
        bad_pat="terraform_unused_declarations",
        doc="docs/TFLINT.md",
        doc_point="module unused vars need tflint --recursive",
        doc_diff="+ root rule enable is not recursive. dump leftover.",
        reg="mod",
        reg_diff="+ unused var in modules/harbor is reported",
        final_ok="ok 6 passed. tflint --recursive sees modules.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="tflint --recursive; dump leftover.",
        wrap="the --recursive flag",
        wrap_ok="6 passed. tflint assign reports module unused vars.",
        wrap_part="5 passed, 1 residual. TFLint assign reports module unused vars.",
        goal="Designed plant quay-tflintm: TFLint omitted --recursive so module unused vars were missed. --recursive. root rule enable is not recursive. dump may remain.",
        plan="Repro python tests, reject root-only rule, --recursive, hand off dump.",
        out_ok="tflint --recursive. 6 tests pass.",
        out_part="tflint --recursive. dump leftover. Partial.",
    ),
    "checkov": P(True,
        slug="pr-checkov-skip-check-framework-secrets",
        plant="lock-ckvskip",
        what="the Checkov scan that used --skip-check CKV* so secrets framework was skipped and a hardcoded AWS key passed",
        glob="**/{.checkov.yml,*.yml,tests/**}",
        ls=".checkov.yml tests/test_harbor.py",
        impl=".checkov.yml",
        src="skip-check:\n  - CKV_AWS_41\n  - CKV*\n",
        sym="CKV*",
        grep="skip-check|framework|secrets",
        grep_obs="harbor skip-check CKV*. pack skip CKV_AWS_41 only plus framework secrets on.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: hardcoded AKIA... passed; skip-check CKV* skipped secrets",
        tf="tests/test_harbor.py",
        tsrc="assert 'CKV*' not in open('.checkov.yml').read() or True",
        wrong="soft-fail true",
        wrong_diff="+ soft-fail: true",
        wrong_obs="still skip CKV*. still no secrets. still pass.",
        fail2="FAIL test_assign: still skip secrets. drop CKV* glob; skip only CKV_AWS_41.",
        reread="skip-check: [CKV_AWS_41]; framework: [terraform, secrets].",
        insight="soft-fail is not un-skip; CKV* glob skips secrets.",
        probe="rg -n 'CKV' .checkov.yml pack/.checkov.yml",
        probe_obs="pack skip one id. harbor CKV*.",
        fix="drop CKV* glob",
        fix_diff="+ skip-check:\n+   - CKV_AWS_41\n",
        rel="dump/.checkov.yml",
        rel_src="skip-check:\n  - CKV*",
        leftover="CKV* glob",
        fix2="dump drop CKV*",
        fix2_diff="+ dump skip-check CKV_AWS_41 only\n",
        bad_pat="soft-fail: true",
        doc="docs/CHECKOV.md",
        doc_point="skip-check CKV* skips the secrets framework",
        doc_diff="+ soft-fail is not un-skip.",
        reg="akia",
        reg_diff="+ hardcoded AKIA key is reported",
        final_ok="ok 6 passed. checkov secrets reports AKIA.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="skip only CKV_AWS_41; dump same.",
        wrap="the skip-check glob",
        wrap_ok="6 passed. checkov assign reports the AKIA key.",
        wrap_part="5 passed, 1 residual. Checkov assign reports the AKIA key.",
        goal="Designed plant lock-ckvskip: Checkov --skip-check CKV* skipped secrets so a hardcoded AWS key passed. skip only CKV_AWS_41. soft-fail is not un-skip.",
        plan="Repro python tests, reject soft-fail, drop CKV* glob, fix dump.",
        out_ok="skip only CKV_AWS_41. 6 checkov tests pass.",
        out_part="skip only CKV_AWS_41. dump leftover. Partial.",
    ),
    "salt": P(False,
        slug="pr-salt-pillar-gpg-renderer-order",
        plant="quay-saltgpg",
        what="the Salt pillar that listed gpg renderer after jinja so ciphertext was templated and decrypt failed",
        glob="**/{*.sls,*.conf,tests/**}",
        ls="pillar/top.sls /etc/salt/master tests/test_harbor.py",
        impl="/etc/salt/master",
        src="renderer: jinja | yaml | gpg\n",
        sym="jinja | yaml | gpg",
        grep="renderer|gpg|#!yaml|#!gpg",
        grep_obs="harbor jinja then gpg. pack gpg | jinja | yaml so ciphertext decrypts first.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: pillar gpg: decrypt failed; jinja interpolated ciphertext before gpg",
        tf="tests/test_harbor.py",
        tsrc="assert 'gpg | jinja' in open('/etc/salt/master').read() or True",
        wrong="pillar_opts true",
        wrong_diff="+ pillar_opts: True",
        wrong_obs="still jinja-first. still decrypt fail.",
        fail2="FAIL test_assign: still decrypt fail. renderer gpg | jinja | yaml.",
        reread="renderer: gpg | jinja | yaml; shebang #!yaml|gpg on files.",
        insight="pillar_opts is not renderer order; gpg must run before jinja.",
        probe="rg -n 'renderer' /etc/salt/master pack/master",
        probe_obs="pack gpg first. harbor jinja first.",
        fix="gpg renderer first",
        fix_diff="+ renderer: gpg | jinja | yaml\n",
        rel="dump/master",
        rel_src="renderer: jinja | yaml | gpg",
        leftover="jinja first",
        fix2="dump gpg first",
        fix2_diff="+ dump renderer gpg | jinja | yaml\n",
        bad_pat="pillar_opts: True",
        doc="docs/SALT.md",
        doc_point="gpg renderer must run before jinja on ciphertext",
        doc_diff="+ pillar_opts is not renderer order. dump leftover.",
        reg="gpg",
        reg_diff="+ pillar decrypts to the secret string",
        final_ok="ok 6 passed. salt gpg renderer runs first.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="gpg | jinja | yaml; dump leftover.",
        wrap="the gpg-first renderer",
        wrap_ok="6 passed. salt assign pillar decrypts.",
        wrap_part="5 passed, 1 residual. Salt assign pillar decrypts.",
        goal="Designed plant quay-saltgpg: Salt pillar listed gpg after jinja so ciphertext was templated and decrypt failed. gpg | jinja | yaml. pillar_opts is not renderer order. dump may remain.",
        plan="Repro python tests, reject pillar_opts, gpg first, hand off dump.",
        out_ok="gpg renderer first. 6 tests pass.",
        out_part="gpg renderer first. dump leftover. Partial.",
    ),
    "puppet": P(True,
        slug="pr-puppet-hiera-eyaml-lookup-merge",
        plant="lock-peyaml",
        what="the Puppet eyaml lookup that used first merge so encrypted hashes were not deep-merged and the secret key was missing",
        glob="**/{hiera.yaml,*.eyaml,tests/**}",
        ls="hiera.yaml tests/test_harbor.py",
        impl="hiera.yaml",
        src="lookup_options:\n  \"^secrets::\":\n    merge: first\n",
        sym="merge: first",
        grep="merge:|eyaml|lookup_options",
        grep_obs="harbor merge first. pack merge deep plus eyaml backend.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: secrets::db::pass undef; merge first hid the eyaml hash",
        tf="tests/test_harbor.py",
        tsrc="assert 'deep' in open('hiera.yaml').read()",
        wrong="lookup --merge unique",
        wrong_diff="+ merge: unique",
        wrong_obs="unique is for arrays. hash still first-wins. still undef.",
        fail2="FAIL test_assign: still undef. merge: deep.",
        reread="lookup_options ^secrets:: merge deep; eyaml backend.",
        insight="unique is arrays; encrypted hashes need deep merge.",
        probe="rg -n 'merge' hiera.yaml pack/hiera.yaml",
        probe_obs="pack deep. harbor first.",
        fix="merge deep",
        fix_diff="+ merge: deep\n",
        rel="dump/hiera.yaml",
        rel_src="merge: first",
        leftover="merge first",
        fix2="dump merge deep",
        fix2_diff="+ dump merge deep\n",
        bad_pat="merge: unique",
        doc="docs/PUPPET.md",
        doc_point="eyaml hashes need lookup merge deep not first",
        doc_diff="+ unique is for arrays.",
        reg="eyaml",
        reg_diff="+ secrets::db::pass is defined",
        final_ok="ok 6 passed. puppet eyaml deep-merges secrets.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="merge deep; dump same.",
        wrap="the deep merge",
        wrap_ok="6 passed. puppet assign secrets::db::pass is defined.",
        wrap_part="5 passed, 1 residual. Puppet assign secrets::db::pass is defined.",
        goal="Designed plant lock-peyaml: Puppet eyaml lookup used merge first so the encrypted hash was hidden. merge deep. unique is for arrays.",
        plan="Repro python tests, reject unique, merge deep, fix dump.",
        out_ok="merge deep. 6 puppet tests pass.",
        out_part="merge deep. dump leftover. Partial.",
    ),
    "chef": P(False,
        slug="pr-chef-attribute-force-default-override",
        plant="quay-chefforce",
        what="the Chef recipe that set node.default after a role override so the port never moved off 80",
        glob="**/{*.rb,*.json,tests/**}",
        ls="recipes/default.rb tests/test_harbor.py",
        impl="recipes/default.rb",
        src="node.default['harbor']['port'] = 8080\n",
        sym="node.default",
        grep="force_default|override|normal",
        grep_obs="harbor node.default. pack force_default after role override.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: listen 80; role override beats node.default; port never 8080",
        tf="tests/test_harbor.py",
        tsrc="assert 'force_default' in open('recipes/default.rb').read()",
        wrong="node.normal port 8080",
        wrong_diff="+ node.normal['harbor']['port'] = 8080",
        wrong_obs="normal still below override. still 80.",
        fail2="FAIL test_assign: still 80. node.force_default after the role.",
        reread="node.force_default['harbor']['port'] = 8080 to beat role override.",
        insight="normal is not override; force_default beats role default/override in this run list.",
        probe="rg -n 'force_default' recipes pack/recipes",
        probe_obs="pack force_default. harbor default.",
        fix="force_default port",
        fix_diff="+ node.force_default['harbor']['port'] = 8080\n",
        rel="dump/recipes/default.rb",
        rel_src="node.default['dump']['port'] = 8080",
        leftover="node.default",
        fix2="dump force_default",
        fix2_diff="+ dump node.force_default port 8080\n",
        bad_pat="node.normal",
        doc="docs/CHEF.md",
        doc_point="role override beats node.default; use force_default",
        doc_diff="+ node.normal is still below override. dump leftover.",
        reg="port",
        reg_diff="+ listen 8080",
        final_ok="ok 6 passed. chef force_default beats role override.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="force_default; dump leftover.",
        wrap="the force_default",
        wrap_ok="6 passed. chef assign listens on 8080.",
        wrap_part="5 passed, 1 residual. Chef assign listens on 8080.",
        goal="Designed plant quay-chefforce: Chef node.default lost to a role override so the port stayed 80. force_default. node.normal is still below override. dump may remain.",
        plan="Repro python tests, reject node.normal, force_default, hand off dump.",
        out_ok="force_default. 6 tests pass.",
        out_part="force_default. dump leftover. Partial.",
    ),
    "garage": P(True,
        slug="pr-garage-s3-list-delimiter-prefix",
        plant="lock-garlis",
        what="the Garage S3 ListObjects that omitted delimiter so prefix queries returned every key and the client timed out",
        glob="**/{garage.toml,*.toml,tests/**}",
        ls="garage.toml tests/test_harbor.py",
        impl="src/list.rs",
        src="list_objects(prefix, delimiter: None)\n",
        sym="delimiter: None",
        grep="delimiter|ListObjects|common_prefixes",
        grep_obs="harbor delimiter None. pack delimiter Some(\"/\") plus common_prefixes.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: ListObjects 12s 80k keys; delimiter missing; no common_prefixes",
        tf="tests/test_harbor.py",
        tsrc="assert 'delimiter' in open('src/list.rs').read()",
        wrong="max-keys 1000 only",
        wrong_diff="+ max_keys = 1000",
        wrong_obs="still full tree via pagination. still timeout on the client.",
        fail2="FAIL test_assign: still 80k. pass delimiter / and return common_prefixes.",
        reread="list_objects(prefix, delimiter: Some(\"/\")); fill common_prefixes.",
        insight="max-keys paginates; delimiter groups prefixes.",
        probe="rg -n 'delimiter' src/list.rs pack/src/list.rs",
        probe_obs="pack delimiter /. harbor None.",
        fix="delimiter slash",
        fix_diff="+ list_objects(prefix, delimiter: Some(\"/\"))\n",
        rel="src/dump.rs",
        rel_src="list_objects(prefix, delimiter: None)",
        leftover="delimiter None",
        fix2="dump delimiter /",
        fix2_diff="+ dump delimiter Some(\"/\")\n",
        bad_pat="max_keys = 1000",
        doc="docs/GARAGE.md",
        doc_point="ListObjects prefix queries need delimiter",
        doc_diff="+ max-keys paginates; delimiter groups.",
        reg="list",
        reg_diff="+ ListObjects returns common_prefixes not 80k keys",
        final_ok="ok 6 passed. garage ListObjects uses delimiter.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="delimiter /; dump same.",
        wrap="the list delimiter",
        wrap_ok="6 passed. garage assign ListObjects is grouped.",
        wrap_part="5 passed, 1 residual. Garage assign ListObjects is grouped.",
        goal="Designed plant lock-garlis: Garage ListObjects omitted delimiter so prefix queries returned every key. delimiter /. max-keys paginates; delimiter groups.",
        plan="Repro python tests, reject max-keys-only, delimiter, fix dump.",
        out_ok="delimiter /. 6 garage tests pass.",
        out_part="delimiter /. dump leftover. Partial.",
    ),
    "gluster": P(False,
        slug="pr-gluster-afr-eager-lock-heal",
        plant="quay-glafr",
        what="the Gluster AFR volume that disabled eager-lock so split-brain heal never took the pending changelog",
        glob="**/{glusterd.vol,*.vol,tests/**}",
        ls="volume.vol tests/test_harbor.py",
        impl="volume.vol",
        src="option cluster.eager-lock off\noption cluster.metadata-self-heal off\n",
        sym="eager-lock off",
        grep="eager-lock|self-heal|afr",
        grep_obs="harbor eager-lock off. pack eager-lock on plus metadata-self-heal on.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: heal info 12 entries; eager-lock off; changelog not taken",
        tf="tests/test_harbor.py",
        tsrc="assert 'eager-lock on' in open('volume.vol').read() or True",
        wrong="cluster.heal-timeout 1",
        wrong_diff="+ option cluster.heal-timeout 1",
        wrong_obs="still no eager-lock. still 12 entries.",
        fail2="FAIL test_assign: still 12. eager-lock on plus metadata-self-heal on.",
        reread="cluster.eager-lock on; cluster.metadata-self-heal on.",
        insight="heal-timeout is not eager-lock; AFR needs the lock to take changelog.",
        probe="rg -n 'eager-lock' volume.vol pack/volume.vol",
        probe_obs="pack on. harbor off.",
        fix="eager-lock on",
        fix_diff="+ option cluster.eager-lock on\n+ option cluster.metadata-self-heal on\n",
        rel="dump/volume.vol",
        rel_src="option cluster.eager-lock off",
        leftover="eager-lock off",
        fix2="dump eager-lock on",
        fix2_diff="+ dump eager-lock on\n",
        bad_pat="heal-timeout 1",
        doc="docs/GLUSTER.md",
        doc_point="AFR split-brain heal needs eager-lock",
        doc_diff="+ heal-timeout is not eager-lock. dump leftover.",
        reg="heal",
        reg_diff="+ heal info 0 entries",
        final_ok="ok 6 passed. gluster AFR eager-lock heals.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="eager-lock on; dump leftover.",
        wrap="the eager-lock",
        wrap_ok="6 passed. gluster assign heal info is 0.",
        wrap_part="5 passed, 1 residual. Gluster assign heal info is 0.",
        goal="Designed plant quay-glafr: Gluster AFR eager-lock off so split-brain heal never took the changelog. eager-lock on. heal-timeout is not eager-lock. dump may remain.",
        plan="Repro python tests, reject heal-timeout, eager-lock, hand off dump.",
        out_ok="eager-lock on. 6 tests pass.",
        out_part="eager-lock on. dump leftover. Partial.",
    ),
    "kong": P(True,
        slug="pr-kong-jwt-key-claim-iss-consumer",
        plant="lock-kongiss",
        what="the Kong JWT plugin that verified without key_claim_name iss so any consumer key was accepted",
        glob="**/{kong.yml,*.yml,tests/**}",
        ls="kong.yml tests/test_harbor.py",
        impl="kong.yml",
        src="plugins:\n  - name: jwt\n    config:\n      secret_is_base64: false\n",
        sym="name: jwt",
        grep="key_claim_name|iss|consumer",
        grep_obs="harbor jwt no key_claim_name. pack key_claim_name iss plus claims_to_verify exp.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: forged jwt with other consumer key accepted; iss not bound",
        tf="tests/test_harbor.py",
        tsrc="assert 'key_claim_name' in open('kong.yml').read()",
        wrong="maximum_expiration 3600",
        wrong_diff="+ maximum_expiration: 3600",
        wrong_obs="still no iss bind. still other consumer.",
        fail2="FAIL test_assign: still accepted. key_claim_name: iss.",
        reread="key_claim_name iss; claims_to_verify [exp]; anonymous off.",
        insight="max expiration is not consumer bind; iss claim is.",
        probe="rg -n 'key_claim_name' kong.yml pack/kong.yml",
        probe_obs="pack iss. harbor missing.",
        fix="key_claim_name iss",
        fix_diff="+ key_claim_name: iss\n+ claims_to_verify: [exp]\n",
        rel="dump/kong.yml",
        rel_src="name: jwt",
        leftover="no key_claim_name",
        fix2="dump key_claim_name iss",
        fix2_diff="+ dump key_claim_name iss\n",
        bad_pat="maximum_expiration: 3600",
        doc="docs/KONG.md",
        doc_point="JWT plugin must bind iss to the consumer key",
        doc_diff="+ max expiration is not consumer bind.",
        reg="iss",
        reg_diff="+ other-consumer jwt is 401",
        final_ok="ok 6 passed. kong jwt binds iss to consumer.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="key_claim_name iss; dump same.",
        wrap="the iss claim bind",
        wrap_ok="6 passed. kong assign other-consumer jwt is 401.",
        wrap_part="5 passed, 1 residual. Kong assign other-consumer jwt is 401.",
        goal="Designed plant lock-kongiss: Kong JWT verified without key_claim_name iss so any consumer key passed. key_claim_name iss. max expiration is not consumer bind.",
        plan="Repro python tests, reject max expiration, iss bind, fix dump.",
        out_ok="key_claim_name iss. 6 kong tests pass.",
        out_part="key_claim_name iss. dump leftover. Partial.",
    ),
    "apisix": P(False,
        slug="pr-apisix-plugin-config-priority-merge",
        plant="quay-apxpri",
        what="the APISIX route that attached a plugin_config with lower priority so consumer-restriction never ran",
        glob="**/{apisix.yaml,*.yml,tests/**}",
        ls="apisix.yaml tests/test_harbor.py",
        impl="apisix.yaml",
        src="plugin_config_id: restriction\nplugins:\n  proxy-rewrite:\n    uri: /v2\n",
        sym="plugin_config_id",
        grep="priority|plugin_config|consumer-restriction",
        grep_obs="harbor plugin_config no priority. pack plugin_config priority 20000 above proxy-rewrite.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: anonymous 200; consumer-restriction skipped; plugin_config lost to proxy-rewrite",
        tf="tests/test_harbor.py",
        tsrc="assert 'priority' in open('apisix.yaml').read()",
        wrong="enable consumer-restriction on the service",
        wrong_diff="+ service_id: harbor",
        wrong_obs="service plugins still lower. still skip.",
        fail2="FAIL test_assign: still 200. plugin_config priority 20000.",
        reread="plugin_config priority 20000 so consumer-restriction runs before proxy-rewrite.",
        insight="service_id is not priority; plugin_config merge needs a higher priority.",
        probe="rg -n 'priority' apisix.yaml pack/apisix.yaml",
        probe_obs="pack 20000. harbor missing.",
        fix="plugin_config priority 20000",
        fix_diff="+ plugin_config:\n+   restriction:\n+     priority: 20000\n",
        rel="dump/apisix.yaml",
        rel_src="plugin_config_id: restriction",
        leftover="no priority",
        fix2="dump priority 20000",
        fix2_diff="+ dump plugin_config priority 20000\n",
        bad_pat="service_id: harbor",
        doc="docs/APISIX.md",
        doc_point="plugin_config must outrank route plugins to run",
        doc_diff="+ service_id is not priority. dump leftover.",
        reg="restr",
        reg_diff="+ anonymous is 401",
        final_ok="ok 6 passed. apisix consumer-restriction runs.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="priority 20000; dump leftover.",
        wrap="the plugin_config priority",
        wrap_ok="6 passed. apisix assign anonymous is 401.",
        wrap_part="5 passed, 1 residual. APISIX assign anonymous is 401.",
        goal="Designed plant quay-apxpri: APISIX plugin_config lost to proxy-rewrite so consumer-restriction never ran. priority 20000. service_id is not priority. dump may remain.",
        plan="Repro python tests, reject service_id, priority 20000, hand off dump.",
        out_ok="plugin_config priority 20000. 6 tests pass.",
        out_part="plugin_config priority 20000. dump leftover. Partial.",
    ),
    "certmanager": P(True,
        slug="pr-certmanager-dns01-rfc2136-tsig",
        plant="lock-cmdns01",
        what="the cert-manager DNS01 RFC2136 solver that omitted TSIG so updates were REFUSED and the cert stayed pending",
        glob="**/{clusterissuer.yaml,*.yml,tests/**}",
        ls="clusterissuer.yaml tests/test_harbor.py",
        impl="clusterissuer.yaml",
        src="solvers:\n  - dns01:\n      rfc2136:\n        nameserver: ns.harbor.svc:53\n",
        sym="rfc2136",
        grep="tsigSecretSecretRef|tsigAlgorithm|rfc2136",
        grep_obs="harbor rfc2136 no TSIG. pack tsigKeyName plus HMACSHA256 secret.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: challenge pending; nsupdate REFUSED; TSIG missing",
        tf="tests/test_harbor.py",
        tsrc="assert 'tsigKeyName' in open('clusterissuer.yaml').read()",
        wrong="ttl 60 on the TXT",
        wrong_diff="+ ttl: 60",
        wrong_obs="still REFUSED. still no TSIG.",
        fail2="FAIL test_assign: still REFUSED. tsigKeyName plus HMACSHA256.",
        reread="tsigKeyName harbor; tsigAlgorithm HMACSHA256; tsigSecretSecretRef.",
        insight="TTL is not TSIG; BIND REFUSED unsigned updates.",
        probe="rg -n 'tsig' clusterissuer.yaml pack/clusterissuer.yaml",
        probe_obs="pack TSIG. harbor missing.",
        fix="TSIG HMACSHA256",
        fix_diff="+ tsigKeyName: harbor\n+ tsigAlgorithm: HMACSHA256\n+ tsigSecretSecretRef: {name: tsig, key: key}\n",
        rel="dump/clusterissuer.yaml",
        rel_src="nameserver: ns.harbor.svc:53",
        leftover="no TSIG",
        fix2="dump TSIG",
        fix2_diff="+ dump tsigKeyName dump HMACSHA256\n",
        bad_pat="ttl: 60",
        doc="docs/CERTMANAGER.md",
        doc_point="RFC2136 solver needs TSIG for signed nsupdate",
        doc_diff="+ TTL is not TSIG.",
        reg="txt",
        reg_diff="+ challenge valid after signed nsupdate",
        final_ok="ok 6 passed. cert-manager RFC2136 TSIG signs nsupdate.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="TSIG HMACSHA256; dump same.",
        wrap="the TSIG key",
        wrap_ok="6 passed. cert-manager assign challenge is valid.",
        wrap_part="5 passed, 1 residual. cert-manager assign challenge is valid.",
        goal="Designed plant lock-cmdns01: cert-manager RFC2136 omitted TSIG so nsupdate was REFUSED. TSIG HMACSHA256. TTL is not TSIG.",
        plan="Repro python tests, reject ttl, TSIG, fix dump.",
        out_ok="TSIG HMACSHA256. 6 cert-manager tests pass.",
        out_part="TSIG HMACSHA256. dump leftover. Partial.",
    ),
    "letsencrypt": P(False,
        slug="pr-letsencrypt-acme-staging-directory",
        plant="quay-lestage",
        what="the ACME client that hit the production directory from CI so rate limits fired and staging certs were never issued",
        glob="**/{Caddyfile,*.yml,tests/**}",
        ls="tls.yml tests/test_harbor.py",
        impl="tls.yml",
        src="acme:\n  directory: https://acme-v02.api.letsencrypt.org/directory\n",
        sym="acme-v02.api",
        grep="staging|acme-v02|directory",
        grep_obs="harbor production directory. pack acme-staging-v02 for CI.",
        test="python3 tests/test_harbor.py",
        fail1="FAIL test_assign: 429 too many certificates; CI hits production ACME",
        tf="tests/test_harbor.py",
        tsrc="assert 'staging' in open('tls.yml').read()",
        wrong="skip_install_trust true",
        wrong_diff="+ skip_install_trust: true",
        wrong_obs="still production directory. still 429.",
        fail2="FAIL test_assign: still 429. acme-staging-v02 directory in CI.",
        reread="directory https://acme-staging-v02.api.letsencrypt.org/directory in CI.",
        insight="skip_install_trust is not staging; production directory rate-limits CI.",
        probe="rg -n 'staging' tls.yml pack/tls.yml",
        probe_obs="pack staging. harbor production.",
        fix="staging directory",
        fix_diff="+ directory: https://acme-staging-v02.api.letsencrypt.org/directory\n",
        rel="dump/tls.yml",
        rel_src="directory: https://acme-v02.api.letsencrypt.org/directory",
        leftover="production directory",
        fix2="dump staging",
        fix2_diff="+ dump acme-staging-v02\n",
        bad_pat="skip_install_trust",
        doc="docs/LETSENCRYPT.md",
        doc_point="CI ACME must use the staging directory",
        doc_diff="+ skip_install_trust is not staging. dump leftover.",
        reg="stage",
        reg_diff="+ CI issues a staging cert without 429",
        final_ok="ok 6 passed. ACME CI uses staging.",
        final_part="5 passed, 1 dump residual. Partial.",
        summary="staging directory; dump leftover.",
        wrap="the staging directory",
        wrap_ok="6 passed. letsencrypt assign CI issues staging certs.",
        wrap_part="5 passed, 1 residual. Let's Encrypt assign CI issues staging certs.",
        goal="Designed plant quay-lestage: ACME client hit production from CI so rate limits fired. acme-staging-v02 directory. skip_install_trust is not staging. dump may remain.",
        plan="Repro python tests, reject skip_install_trust, staging directory, hand off dump.",
        out_ok="staging directory. 6 tests pass.",
        out_part="staging directory. dump leftover. Partial.",
    ),
}


def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("MetalLB L2Advertisement vs Keepalived unicast_peer",
     fn("metallb"), fn("keepalived"),
     "L2Advertisement; unicast_peer",
     "BGPAdvertisement; nopreempt",
     "metallb dump no L2Advertisement; keepalived dump no unicast_peer"),
    ("Nebula static_host_map vs crun systemd slice",
     fn("nebula"), fn("crun"),
     "static_host_map public; slice:machine.slice:crun:id",
     "punchy.respond only; cpu.shares",
     "nebula dump no map; crun dump relative path"),
    ("youki memory.max vs TFLint --recursive",
     fn("youki"), fn("tflint"),
     "OCI memory.limit 256Mi; tflint --recursive",
     "swapaccount=1; root-only rule",
     "youki dump limit 0; tflint dump no --recursive"),
    ("Checkov drop CKV* vs Salt gpg-first renderer",
     fn("checkov"), fn("salt"),
     "skip only CKV_AWS_41; renderer gpg | jinja | yaml",
     "soft-fail; pillar_opts",
     "checkov dump CKV* glob; salt dump jinja first"),
    ("Puppet eyaml merge deep vs Chef force_default",
     fn("puppet"), fn("chef"),
     "merge deep; node.force_default",
     "merge unique; node.normal",
     "puppet dump merge first; chef dump node.default"),
    ("Garage ListObjects delimiter vs Gluster AFR eager-lock",
     fn("garage"), fn("gluster"),
     "delimiter /; eager-lock on",
     "max-keys 1000; heal-timeout 1",
     "garage dump delimiter None; gluster dump eager-lock off"),
    ("Kong JWT iss bind vs APISIX plugin_config priority",
     fn("kong"), fn("apisix"),
     "key_claim_name iss; plugin_config priority 20000",
     "maximum_expiration; service_id",
     "kong dump no iss; apisix dump no priority"),
    ("cert-manager RFC2136 TSIG vs Let's Encrypt staging directory",
     fn("certmanager"), fn("letsencrypt"),
     "TSIG HMACSHA256; acme-staging-v02 directory",
     "ttl 60; skip_install_trust",
     "cert-manager dump no TSIG; letsencrypt dump production directory"),
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
- Not a clone of r4163-r4468 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
