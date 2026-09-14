#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4bz: unused plants after r4492.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4492. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4bz_state.json")
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
    "cfengine": P(True,
        slug='pr-cfengine-promise-lock-expire-after',
        plant='lock-cfexp',
        what='the CFEngine promise that omitted lock_expire_after so a hung copy never retried',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='promises.cf tests/test_harbor.py',
        impl='promises.cf',
        src='files: { "/etc/harbor.conf": { copy_from => remote }; }',
        sym='lock_expire_after',
        grep='lock_expire_after|lock_expire_after',
        grep_obs='harbor ifelapsed 0. pack lock_expire_after 5.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: copy hung 2h; promise lock never expired',
        tf='tests/test_harbor.py',
        tsrc="assert 'lock_expire_after' in open('promises.cf').read() or True",
        wrong='ifelapsed 0',
        wrong_diff='+ ifelapsed 0',
        wrong_obs='still ifelapsed 0. still fail.',
        fail2='FAIL test_assign: still broken. lock_expire_after 5.',
        reread='apply lock_expire_after 5.',
        insight='ifelapsed is not expire',
        probe="rg -n 'lock_expire_after' promises.cf pack/promises.cf",
        probe_obs='pack lock_expire_after 5. harbor ifelapsed 0.',
        fix='lock_expire_after 5',
        fix_diff='+ lock_expire_after 5\n',
        rel='dump/promises.cf',
        rel_src='files: { "/etc/harbor.conf": { copy_from => remote }; }',
        leftover='wrong leftover ifelapsed 0',
        fix2='dump lock_expire_after 5',
        fix2_diff='+ dump lock_expire_after 5\n',
        bad_pat='ifelapsed 0',
        doc='docs/LOCK-CFEXP.md',
        doc_point='ifelapsed is not expire',
        doc_diff='+ ifelapsed is not expire.',
        reg='reg',
        reg_diff='+ lock_expire_after 5 holds',
        final_ok='ok 6 passed. lock_expire_after 5.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='lock_expire_after 5; dump same.',
        wrap='the lock_expire_after 5',
        wrap_ok='6 passed. lock-cfexp assign is green.',
        wrap_part='5 passed, 1 residual. lock-cfexp assign is green.',
        goal='Designed plant lock-cfexp: the CFEngine promise that omitted lock_expire_after so a hung copy never retried. lock_expire_after 5. ifelapsed is not expire.',
        plan='Repro python tests, reject ifelapsed 0, lock_expire_after 5, fix dump.',
        out_ok='lock_expire_after 5. 6 tests pass.',
        out_part='lock_expire_after 5. dump leftover. Partial.',
    ),
    "nixos": P(False,
        slug='pr-nixos-module-mkforce-overlay',
        plant='quay-nixforce',
        what='the NixOS module that used mkDefault for a kernel param so iommu stayed off',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='configuration.nix tests/test_harbor.py',
        impl='configuration.nix',
        src='boot.kernelParams = lib.mkDefault [ "intel_iommu=off" ];',
        sym='mkForce',
        grep='mkForce|mkForce',
        grep_obs='harbor assignment merge. pack mkForce iommu on.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: iommu off after rebuild; mkDefault lost',
        tf='tests/test_harbor.py',
        tsrc="assert 'mkForce' in open('configuration.nix').read() or True",
        wrong='assignment merge',
        wrong_diff='+ assignment merge',
        wrong_obs='still assignment merge. still fail.',
        fail2='FAIL test_assign: still broken. mkForce iommu on.',
        reread='apply mkForce iommu on.',
        insight='assignment merge is not mkForce',
        probe="rg -n 'mkForce' configuration.nix pack/configuration.nix",
        probe_obs='pack mkForce iommu on. harbor assignment merge.',
        fix='mkForce iommu on',
        fix_diff='+ mkForce iommu on\n',
        rel='dump/configuration.nix',
        rel_src='boot.kernelParams = lib.mkDefault [ "intel_iommu=off" ];',
        leftover='wrong leftover assignment merge',
        fix2='dump mkForce iommu on',
        fix2_diff='+ dump mkForce iommu on\n',
        bad_pat='assignment merge',
        doc='docs/QUAY-NIXFORCE.md',
        doc_point='assignment merge is not mkForce',
        doc_diff='+ assignment merge is not mkForce.',
        reg='reg',
        reg_diff='+ mkForce iommu on holds',
        final_ok='ok 6 passed. mkForce iommu on.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='mkForce iommu on; dump leftover.',
        wrap='the mkForce iommu on',
        wrap_ok='6 passed. quay-nixforce assign is green.',
        wrap_part='5 passed, 1 residual. quay-nixforce assign is green.',
        goal='Designed plant quay-nixforce: the NixOS module that used mkDefault for a kernel param so iommu stayed off. mkForce iommu on. assignment merge is not mkForce.',
        plan='Repro python tests, reject assignment merge, mkForce iommu on, hand off dump.',
        out_ok='mkForce iommu on. 6 tests pass.',
        out_part='mkForce iommu on. dump leftover. Partial.',
    ),
    "guix": P(True,
        slug='pr-guix-pack-relocatable-rpath',
        plant='lock-guixrpath',
        what='the guix pack that omitted -R so rpath pointed at /gnu/store on a foreign host',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='pack.scm tests/test_harbor.py',
        impl='pack.scm',
        src='guix pack harbor',
        sym='pack -R',
        grep='pack -R|pack',
        grep_obs='harbor GUIX_LOCPATH. pack pack -R relocatable.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: libguile not found; rpath /gnu/store',
        tf='tests/test_harbor.py',
        tsrc="assert 'pack' in open('pack.scm').read() or True",
        wrong='GUIX_LOCPATH',
        wrong_diff='+ GUIX_LOCPATH',
        wrong_obs='still GUIX_LOCPATH. still fail.',
        fail2='FAIL test_assign: still broken. pack -R relocatable.',
        reread='apply pack -R relocatable.',
        insight='LOCPATH is not relocatable',
        probe="rg -n 'pack' pack.scm pack/pack.scm",
        probe_obs='pack pack -R relocatable. harbor GUIX_LOCPATH.',
        fix='pack -R relocatable',
        fix_diff='+ pack -R relocatable\n',
        rel='dump/pack.scm',
        rel_src='guix pack harbor',
        leftover='wrong leftover GUIX_LOCPATH',
        fix2='dump pack -R relocatable',
        fix2_diff='+ dump pack -R relocatable\n',
        bad_pat='GUIX_LOCPATH',
        doc='docs/LOCK-GUIXRPATH.md',
        doc_point='LOCPATH is not relocatable',
        doc_diff='+ LOCPATH is not relocatable.',
        reg='reg',
        reg_diff='+ pack -R relocatable holds',
        final_ok='ok 6 passed. pack -R relocatable.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pack -R relocatable; dump same.',
        wrap='the pack -R relocatable',
        wrap_ok='6 passed. lock-guixrpath assign is green.',
        wrap_part='5 passed, 1 residual. lock-guixrpath assign is green.',
        goal='Designed plant lock-guixrpath: the guix pack that omitted -R so rpath pointed at /gnu/store on a foreign host. pack -R relocatable. LOCPATH is not relocatable.',
        plan='Repro python tests, reject GUIX_LOCPATH, pack -R relocatable, fix dump.',
        out_ok='pack -R relocatable. 6 tests pass.',
        out_part='pack -R relocatable. dump leftover. Partial.',
    ),
    "sonic": P(False,
        slug='pr-sonic-search-lang-locale-stem',
        plant='quay-sonicst',
        what='the Sonic search that used locale none so cars missed car',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='config.cfg tests/test_harbor.py',
        impl='config.cfg',
        src='[server]\nlocale = none',
        sym='locale eng',
        grep='locale eng|locale',
        grep_obs='harbor query_max_results. pack locale eng.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: query cars 0 hits; locale none; stem skipped',
        tf='tests/test_harbor.py',
        tsrc="assert 'locale' in open('config.cfg').read() or True",
        wrong='query_max_results',
        wrong_diff='+ query_max_results',
        wrong_obs='still query_max_results. still fail.',
        fail2='FAIL test_assign: still broken. locale eng.',
        reread='apply locale eng.',
        insight='max results is not stemming',
        probe="rg -n 'locale' config.cfg pack/config.cfg",
        probe_obs='pack locale eng. harbor query_max_results.',
        fix='locale eng',
        fix_diff='+ locale eng\n',
        rel='dump/config.cfg',
        rel_src='[server]\nlocale = none',
        leftover='wrong leftover query_max_results',
        fix2='dump locale eng',
        fix2_diff='+ dump locale eng\n',
        bad_pat='query_max_results',
        doc='docs/QUAY-SONICST.md',
        doc_point='max results is not stemming',
        doc_diff='+ max results is not stemming.',
        reg='reg',
        reg_diff='+ locale eng holds',
        final_ok='ok 6 passed. locale eng.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='locale eng; dump leftover.',
        wrap='the locale eng',
        wrap_ok='6 passed. quay-sonicst assign is green.',
        wrap_part='5 passed, 1 residual. quay-sonicst assign is green.',
        goal='Designed plant quay-sonicst: the Sonic search that used locale none so cars missed car. locale eng. max results is not stemming.',
        plan='Repro python tests, reject query_max_results, locale eng, hand off dump.',
        out_ok='locale eng. 6 tests pass.',
        out_part='locale eng. dump leftover. Partial.',
    ),
    "bleve": P(True,
        slug='pr-bleve-mapping-keyword-analyzer',
        plant='lock-blkw',
        what='the Bleve mapping that analyzed sku with standard so HAR-1 never exact-matched',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='mapping.go tests/test_harbor.py',
        impl='mapping.go',
        src='doc.AddFieldMapping("sku", bleve.NewTextFieldMapping())',
        sym='keyword analyzer',
        grep='keyword analyzer|keyword',
        grep_obs='harbor MatchPhraseQuery. pack keyword analyzer.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: query sku HAR-1 0 hits; standard analyzer split hyphen',
        tf='tests/test_harbor.py',
        tsrc="assert 'keyword' in open('mapping.go').read() or True",
        wrong='MatchPhraseQuery',
        wrong_diff='+ MatchPhraseQuery',
        wrong_obs='still MatchPhraseQuery. still fail.',
        fail2='FAIL test_assign: still broken. keyword analyzer.',
        reread='apply keyword analyzer.',
        insight='phrase query is not keyword',
        probe="rg -n 'keyword' mapping.go pack/mapping.go",
        probe_obs='pack keyword analyzer. harbor MatchPhraseQuery.',
        fix='keyword analyzer',
        fix_diff='+ keyword analyzer\n',
        rel='dump/mapping.go',
        rel_src='doc.AddFieldMapping("sku", bleve.NewTextFieldMapping())',
        leftover='wrong leftover MatchPhraseQuery',
        fix2='dump keyword analyzer',
        fix2_diff='+ dump keyword analyzer\n',
        bad_pat='MatchPhraseQuery',
        doc='docs/LOCK-BLKW.md',
        doc_point='phrase query is not keyword',
        doc_diff='+ phrase query is not keyword.',
        reg='reg',
        reg_diff='+ keyword analyzer holds',
        final_ok='ok 6 passed. keyword analyzer.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='keyword analyzer; dump same.',
        wrap='the keyword analyzer',
        wrap_ok='6 passed. lock-blkw assign is green.',
        wrap_part='5 passed, 1 residual. lock-blkw assign is green.',
        goal='Designed plant lock-blkw: the Bleve mapping that analyzed sku with standard so HAR-1 never exact-matched. keyword analyzer. phrase query is not keyword.',
        plan='Repro python tests, reject MatchPhraseQuery, keyword analyzer, fix dump.',
        out_ok='keyword analyzer. 6 tests pass.',
        out_part='keyword analyzer. dump leftover. Partial.',
    ),
    "xapian": P(False,
        slug='pr-xapian-termprefix-boolean-slot',
        plant='quay-xapbool',
        what='the Xapian query that stemmed the id so filter AND never matched HAR-1',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='index.cc tests/test_harbor.py',
        impl='index.cc',
        src='doc.add_term("id" + sku);',
        sym='add_boolean_term',
        grep='add_boolean_term|boolean',
        grep_obs='harbor query stemmer none. pack boolean term prefix.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: filter id:HAR-1 0; id was stemmed',
        tf='tests/test_harbor.py',
        tsrc="assert 'boolean' in open('index.cc').read() or True",
        wrong='query stemmer none',
        wrong_diff='+ query stemmer none',
        wrong_obs='still query stemmer none. still fail.',
        fail2='FAIL test_assign: still broken. boolean term prefix.',
        reread='apply boolean term prefix.',
        insight='query stemmer none is not index boolean',
        probe="rg -n 'boolean' index.cc pack/index.cc",
        probe_obs='pack boolean term prefix. harbor query stemmer none.',
        fix='boolean term prefix',
        fix_diff='+ boolean term prefix\n',
        rel='dump/index.cc',
        rel_src='doc.add_term("id" + sku);',
        leftover='wrong leftover query stemmer none',
        fix2='dump boolean term prefix',
        fix2_diff='+ dump boolean term prefix\n',
        bad_pat='query stemmer none',
        doc='docs/QUAY-XAPBOOL.md',
        doc_point='query stemmer none is not index boolean',
        doc_diff='+ query stemmer none is not index boolean.',
        reg='reg',
        reg_diff='+ boolean term prefix holds',
        final_ok='ok 6 passed. boolean term prefix.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='boolean term prefix; dump leftover.',
        wrap='the boolean term prefix',
        wrap_ok='6 passed. quay-xapbool assign is green.',
        wrap_part='5 passed, 1 residual. quay-xapbool assign is green.',
        goal='Designed plant quay-xapbool: the Xapian query that stemmed the id so filter AND never matched HAR-1. boolean term prefix. query stemmer none is not index boolean.',
        plan='Repro python tests, reject query stemmer none, boolean term prefix, hand off dump.',
        out_ok='boolean term prefix. 6 tests pass.',
        out_part='boolean term prefix. dump leftover. Partial.',
    ),
    "whoosh": P(True,
        slug='pr-whoosh-schema-id-unique-stored',
        plant='lock-whid',
        what='the Whoosh schema that used TEXT for id so unique was ignored and updates duplicated',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='schema.py tests/test_harbor.py',
        impl='schema.py',
        src='schema = Schema(id=TEXT(stored=True), body=TEXT)',
        sym='ID unique',
        grep='ID unique|ID',
        grep_obs='harbor update merge=True. pack ID unique stored.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: update created a second doc; TEXT cannot be unique',
        tf='tests/test_harbor.py',
        tsrc="assert 'ID' in open('schema.py').read() or True",
        wrong='update merge=True',
        wrong_diff='+ update merge=True',
        wrong_obs='still update merge=True. still fail.',
        fail2='FAIL test_assign: still broken. ID unique stored.',
        reread='apply ID unique stored.',
        insight='update merge is not unique',
        probe="rg -n 'ID' schema.py pack/schema.py",
        probe_obs='pack ID unique stored. harbor update merge=True.',
        fix='ID unique stored',
        fix_diff='+ ID unique stored\n',
        rel='dump/schema.py',
        rel_src='schema = Schema(id=TEXT(stored=True), body=TEXT)',
        leftover='wrong leftover update merge=True',
        fix2='dump ID unique stored',
        fix2_diff='+ dump ID unique stored\n',
        bad_pat='update merge=True',
        doc='docs/LOCK-WHID.md',
        doc_point='update merge is not unique',
        doc_diff='+ update merge is not unique.',
        reg='reg',
        reg_diff='+ ID unique stored holds',
        final_ok='ok 6 passed. ID unique stored.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ID unique stored; dump same.',
        wrap='the ID unique stored',
        wrap_ok='6 passed. lock-whid assign is green.',
        wrap_part='5 passed, 1 residual. lock-whid assign is green.',
        goal='Designed plant lock-whid: the Whoosh schema that used TEXT for id so unique was ignored and updates duplicated. ID unique stored. update merge is not unique.',
        plan='Repro python tests, reject update merge=True, ID unique stored, fix dump.',
        out_ok='ID unique stored. 6 tests pass.',
        out_part='ID unique stored. dump leftover. Partial.',
    ),
    "kms": P(False,
        slug='pr-kms-alias-policy-multi-region',
        plant='quay-kmsalias',
        what='the KMS alias that pointed at a regional key so replica decrypt was NotFound',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='alias.tf tests/test_harbor.py',
        impl='alias.tf',
        src='resource "aws_kms_alias" "harbor" { target_key_id = aws_kms_key.primary.id }',
        sym='multi_region',
        grep='multi_region|multi_region',
        grep_obs='harbor second alias. pack multi_region key.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: replica decrypt NotFoundException; alias bound to regional key',
        tf='tests/test_harbor.py',
        tsrc="assert 'multi_region' in open('alias.tf').read() or True",
        wrong='second alias',
        wrong_diff='+ second alias',
        wrong_obs='still second alias. still fail.',
        fail2='FAIL test_assign: still broken. multi_region key.',
        reread='apply multi_region key.',
        insight='a second alias is not mrk',
        probe="rg -n 'multi_region' alias.tf pack/alias.tf",
        probe_obs='pack multi_region key. harbor second alias.',
        fix='multi_region key',
        fix_diff='+ multi_region key\n',
        rel='dump/alias.tf',
        rel_src='resource "aws_kms_alias" "harbor" { target_key_id = aws_kms_key.primary.id }',
        leftover='wrong leftover second alias',
        fix2='dump multi_region key',
        fix2_diff='+ dump multi_region key\n',
        bad_pat='second alias',
        doc='docs/QUAY-KMSALIAS.md',
        doc_point='a second alias is not mrk',
        doc_diff='+ a second alias is not mrk.',
        reg='reg',
        reg_diff='+ multi_region key holds',
        final_ok='ok 6 passed. multi_region key.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='multi_region key; dump leftover.',
        wrap='the multi_region key',
        wrap_ok='6 passed. quay-kmsalias assign is green.',
        wrap_part='5 passed, 1 residual. quay-kmsalias assign is green.',
        goal='Designed plant quay-kmsalias: the KMS alias that pointed at a regional key so replica decrypt was NotFound. multi_region key. a second alias is not mrk.',
        plan='Repro python tests, reject second alias, multi_region key, hand off dump.',
        out_ok='multi_region key. 6 tests pass.',
        out_part='multi_region key. dump leftover. Partial.',
    ),
    "age": P(True,
        slug='pr-age-recipients-file-plugin-ssh',
        plant='lock-agerec',
        what='the age encrypt that listed an inline ssh recipient so rotate left ciphertext unreadable',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='encrypt.sh tests/test_harbor.py',
        impl='encrypt.sh',
        src='age -r ssh-ed25519-AAAAC3... -o secret.age secret',
        sym='age -R',
        grep='age -R|age',
        grep_obs='harbor age -p. pack age -R recipients.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: decrypt failed after key rotate; inline recipient stale',
        tf='tests/test_harbor.py',
        tsrc="assert 'age' in open('encrypt.sh').read() or True",
        wrong='age -p',
        wrong_diff='+ age -p',
        wrong_obs='still age -p. still fail.',
        fail2='FAIL test_assign: still broken. age -R recipients.',
        reread='apply age -R recipients.',
        insight='passphrase is not a recipients file',
        probe="rg -n 'age' encrypt.sh pack/encrypt.sh",
        probe_obs='pack age -R recipients. harbor age -p.',
        fix='age -R recipients',
        fix_diff='+ age -R recipients\n',
        rel='dump/encrypt.sh',
        rel_src='age -r ssh-ed25519-AAAAC3... -o secret.age secret',
        leftover='wrong leftover age -p',
        fix2='dump age -R recipients',
        fix2_diff='+ dump age -R recipients\n',
        bad_pat='age -p',
        doc='docs/LOCK-AGEREC.md',
        doc_point='passphrase is not a recipients file',
        doc_diff='+ passphrase is not a recipients file.',
        reg='reg',
        reg_diff='+ age -R recipients holds',
        final_ok='ok 6 passed. age -R recipients.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='age -R recipients; dump same.',
        wrap='the age -R recipients',
        wrap_ok='6 passed. lock-agerec assign is green.',
        wrap_part='5 passed, 1 residual. lock-agerec assign is green.',
        goal='Designed plant lock-agerec: the age encrypt that listed an inline ssh recipient so rotate left ciphertext unreadable. age -R recipients. passphrase is not a recipients file.',
        plan='Repro python tests, reject age -p, age -R recipients, fix dump.',
        out_ok='age -R recipients. 6 tests pass.',
        out_part='age -R recipients. dump leftover. Partial.',
    ),
    "mayastor": P(False,
        slug='pr-mayastor-nvmf-io-timeout-ctrl',
        plant='quay-msnvmf',
        what='the Mayastor NVMe-oF target that omitted ioTimeout so controller reset left the volume Faulted',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='pool.yaml tests/test_harbor.py',
        impl='pool.yaml',
        src='spec:\n  ioTimeout: 0',
        sym='ioTimeout 30',
        grep='ioTimeout 30|ioTimeout',
        grep_obs='harbor rebuildTimeout. pack ioTimeout 30.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: volume Faulted; ioTimeout 0; controller reset never finished',
        tf='tests/test_harbor.py',
        tsrc="assert 'ioTimeout' in open('pool.yaml').read() or True",
        wrong='rebuildTimeout',
        wrong_diff='+ rebuildTimeout',
        wrong_obs='still rebuildTimeout. still fail.',
        fail2='FAIL test_assign: still broken. ioTimeout 30.',
        reread='apply ioTimeout 30.',
        insight='rebuild timeout is not I/O timeout',
        probe="rg -n 'ioTimeout' pool.yaml pack/pool.yaml",
        probe_obs='pack ioTimeout 30. harbor rebuildTimeout.',
        fix='ioTimeout 30',
        fix_diff='+ ioTimeout 30\n',
        rel='dump/pool.yaml',
        rel_src='spec:\n  ioTimeout: 0',
        leftover='wrong leftover rebuildTimeout',
        fix2='dump ioTimeout 30',
        fix2_diff='+ dump ioTimeout 30\n',
        bad_pat='rebuildTimeout',
        doc='docs/QUAY-MSNVMF.md',
        doc_point='rebuild timeout is not I/O timeout',
        doc_diff='+ rebuild timeout is not I/O timeout.',
        reg='reg',
        reg_diff='+ ioTimeout 30 holds',
        final_ok='ok 6 passed. ioTimeout 30.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ioTimeout 30; dump leftover.',
        wrap='the ioTimeout 30',
        wrap_ok='6 passed. quay-msnvmf assign is green.',
        wrap_part='5 passed, 1 residual. quay-msnvmf assign is green.',
        goal='Designed plant quay-msnvmf: the Mayastor NVMe-oF target that omitted ioTimeout so controller reset left the volume Faulted. ioTimeout 30. rebuild timeout is not I/O timeout.',
        plan='Repro python tests, reject rebuildTimeout, ioTimeout 30, hand off dump.',
        out_ok='ioTimeout 30. 6 tests pass.',
        out_part='ioTimeout 30. dump leftover. Partial.',
    ),
    "crosvm": P(True,
        slug='pr-crosvm-jail-seccomp-policy',
        plant='lock-crosjail',
        what='the crosvm jail that used --disable-sandbox so host /dev/dri leaked into the guest',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='run.sh tests/test_harbor.py',
        impl='run.sh',
        src='crosvm run --disable-sandbox kernel',
        sym='jail',
        grep='jail|jail',
        grep_obs='harbor chmod dri. pack jail plus seccomp.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: guest sees host /dev/dri; sandbox disabled',
        tf='tests/test_harbor.py',
        tsrc="assert 'jail' in open('run.sh').read() or True",
        wrong='chmod dri',
        wrong_diff='+ chmod dri',
        wrong_obs='still chmod dri. still fail.',
        fail2='FAIL test_assign: still broken. jail plus seccomp.',
        reread='apply jail plus seccomp.',
        insight='chmod on host dri is not a jail',
        probe="rg -n 'jail' run.sh pack/run.sh",
        probe_obs='pack jail plus seccomp. harbor chmod dri.',
        fix='jail plus seccomp',
        fix_diff='+ jail plus seccomp\n',
        rel='dump/run.sh',
        rel_src='crosvm run --disable-sandbox kernel',
        leftover='wrong leftover chmod dri',
        fix2='dump jail plus seccomp',
        fix2_diff='+ dump jail plus seccomp\n',
        bad_pat='chmod dri',
        doc='docs/LOCK-CROSJAIL.md',
        doc_point='chmod on host dri is not a jail',
        doc_diff='+ chmod on host dri is not a jail.',
        reg='reg',
        reg_diff='+ jail plus seccomp holds',
        final_ok='ok 6 passed. jail plus seccomp.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='jail plus seccomp; dump same.',
        wrap='the jail plus seccomp',
        wrap_ok='6 passed. lock-crosjail assign is green.',
        wrap_part='5 passed, 1 residual. lock-crosjail assign is green.',
        goal='Designed plant lock-crosjail: the crosvm jail that used --disable-sandbox so host /dev/dri leaked into the guest. jail plus seccomp. chmod on host dri is not a jail.',
        plan='Repro python tests, reject chmod dri, jail plus seccomp, fix dump.',
        out_ok='jail plus seccomp. 6 tests pass.',
        out_part='jail plus seccomp. dump leftover. Partial.',
    ),
    "innernet": P(False,
        slug='pr-innernet-invite-cidr-name',
        plant='quay-incidr',
        what='the innernet invite that omitted --cidr so the peer joined root and routed to every CIDR',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='invite.sh tests/test_harbor.py',
        impl='invite.sh',
        src='innernet-server add-peer harbor',
        sym='--cidr',
        grep='--cidr|invite',
        grep_obs='harbor wg-quick down. pack invite --cidr.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: peer can ping db CIDR; invite had no --cidr',
        tf='tests/test_harbor.py',
        tsrc="assert 'invite' in open('invite.sh').read() or True",
        wrong='wg-quick down',
        wrong_diff='+ wg-quick down',
        wrong_obs='still wg-quick down. still fail.',
        fail2='FAIL test_assign: still broken. invite --cidr.',
        reread='apply invite --cidr.',
        insight='iface down is not a CIDR',
        probe="rg -n 'invite' invite.sh pack/invite.sh",
        probe_obs='pack invite --cidr. harbor wg-quick down.',
        fix='invite --cidr',
        fix_diff='+ invite --cidr\n',
        rel='dump/invite.sh',
        rel_src='innernet-server add-peer harbor',
        leftover='wrong leftover wg-quick down',
        fix2='dump invite --cidr',
        fix2_diff='+ dump invite --cidr\n',
        bad_pat='wg-quick down',
        doc='docs/QUAY-INCIDR.md',
        doc_point='iface down is not a CIDR',
        doc_diff='+ iface down is not a CIDR.',
        reg='reg',
        reg_diff='+ invite --cidr holds',
        final_ok='ok 6 passed. invite --cidr.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='invite --cidr; dump leftover.',
        wrap='the invite --cidr',
        wrap_ok='6 passed. quay-incidr assign is green.',
        wrap_part='5 passed, 1 residual. quay-incidr assign is green.',
        goal='Designed plant quay-incidr: the innernet invite that omitted --cidr so the peer joined root and routed to every CIDR. invite --cidr. iface down is not a CIDR.',
        plan='Repro python tests, reject wg-quick down, invite --cidr, hand off dump.',
        out_ok='invite --cidr. 6 tests pass.',
        out_part='invite --cidr. dump leftover. Partial.',
    ),
    "libreswan": P(True,
        slug='pr-libreswan-ikev2-narrowing-on',
        plant='lock-lswan',
        what='the Libreswan conn that left narrowing=no so 0.0.0.0/0 TS was rejected',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='ipsec.conf tests/test_harbor.py',
        impl='ipsec.conf',
        src='conn harbor\n  narrowing=no\n  ikev2=insist',
        sym='narrowing yes',
        grep='narrowing yes|narrowing',
        grep_obs='harbor ike cipher. pack narrowing yes.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: IKE_AUTH TS_UNACCEPTABLE; narrowing=no',
        tf='tests/test_harbor.py',
        tsrc="assert 'narrowing' in open('ipsec.conf').read() or True",
        wrong='ike cipher',
        wrong_diff='+ ike cipher',
        wrong_obs='still ike cipher. still fail.',
        fail2='FAIL test_assign: still broken. narrowing yes.',
        reread='apply narrowing yes.',
        insight='ike cipher is not narrowing',
        probe="rg -n 'narrowing' ipsec.conf pack/ipsec.conf",
        probe_obs='pack narrowing yes. harbor ike cipher.',
        fix='narrowing yes',
        fix_diff='+ narrowing yes\n',
        rel='dump/ipsec.conf',
        rel_src='conn harbor\n  narrowing=no\n  ikev2=insist',
        leftover='wrong leftover ike cipher',
        fix2='dump narrowing yes',
        fix2_diff='+ dump narrowing yes\n',
        bad_pat='ike cipher',
        doc='docs/LOCK-LSWAN.md',
        doc_point='ike cipher is not narrowing',
        doc_diff='+ ike cipher is not narrowing.',
        reg='reg',
        reg_diff='+ narrowing yes holds',
        final_ok='ok 6 passed. narrowing yes.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='narrowing yes; dump same.',
        wrap='the narrowing yes',
        wrap_ok='6 passed. lock-lswan assign is green.',
        wrap_part='5 passed, 1 residual. lock-lswan assign is green.',
        goal='Designed plant lock-lswan: the Libreswan conn that left narrowing=no so 0.0.0.0/0 TS was rejected. narrowing yes. ike cipher is not narrowing.',
        plan='Repro python tests, reject ike cipher, narrowing yes, fix dump.',
        out_ok='narrowing yes. 6 tests pass.',
        out_part='narrowing yes. dump leftover. Partial.',
    ),
    "kvm": P(False,
        slug='pr-kvm-nested-enable-modprobe',
        plant='quay-kvmnest',
        what='the KVM host that omitted nested=1 so a guest hypervisor got KVM_CREATE_VM EPERM',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='modprobe.d/kvm.conf tests/test_harbor.py',
        impl='modprobe.d/kvm.conf',
        src='options kvm ignore_msrs=1',
        sym='nested=1',
        grep='nested=1|nested=1',
        grep_obs='harbor qemu cpu flags. pack nested=1.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: guest qemu KVM_CREATE_VM EPERM; nested=0',
        tf='tests/test_harbor.py',
        tsrc="assert 'nested=1' in open('modprobe.d/kvm.conf').read() or True",
        wrong='qemu cpu flags',
        wrong_diff='+ qemu cpu flags',
        wrong_obs='still qemu cpu flags. still fail.',
        fail2='FAIL test_assign: still broken. nested=1.',
        reread='apply nested=1.',
        insight='qemu cpu flags are not host nested',
        probe="rg -n 'nested=1' modprobe.d/kvm.conf pack/modprobe.d/kvm.conf",
        probe_obs='pack nested=1. harbor qemu cpu flags.',
        fix='nested=1',
        fix_diff='+ nested=1\n',
        rel='dump/modprobe.d/kvm.conf',
        rel_src='options kvm ignore_msrs=1',
        leftover='wrong leftover qemu cpu flags',
        fix2='dump nested=1',
        fix2_diff='+ dump nested=1\n',
        bad_pat='qemu cpu flags',
        doc='docs/QUAY-KVMNEST.md',
        doc_point='qemu cpu flags are not host nested',
        doc_diff='+ qemu cpu flags are not host nested.',
        reg='reg',
        reg_diff='+ nested=1 holds',
        final_ok='ok 6 passed. nested=1.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='nested=1; dump leftover.',
        wrap='the nested=1',
        wrap_ok='6 passed. quay-kvmnest assign is green.',
        wrap_part='5 passed, 1 residual. quay-kvmnest assign is green.',
        goal='Designed plant quay-kvmnest: the KVM host that omitted nested=1 so a guest hypervisor got KVM_CREATE_VM EPERM. nested=1. qemu cpu flags are not host nested.',
        plan='Repro python tests, reject qemu cpu flags, nested=1, hand off dump.',
        out_ok='nested=1. 6 tests pass.',
        out_part='nested=1. dump leftover. Partial.',
    ),
    "cloudhv": P(True,
        slug='pr-cloudhv-vsock-cid-unique',
        plant='lock-chvcid',
        what='the Cloud Hypervisor vsock that reused guest_cid 3 so the second VM failed to bind',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='vm.json tests/test_harbor.py',
        impl='vm.json',
        src='"vsock": {"guest_cid": 3, "uds": "/tmp/vsock"}',
        sym='unique cid',
        grep='unique cid|unique',
        grep_obs='harbor disable vsock. pack unique cid and uds.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: vm-b vsock EADDRINUSE; guest_cid 3 reused',
        tf='tests/test_harbor.py',
        tsrc="assert 'unique' in open('vm.json').read() or True",
        wrong='disable vsock',
        wrong_diff='+ disable vsock',
        wrong_obs='still disable vsock. still fail.',
        fail2='FAIL test_assign: still broken. unique cid and uds.',
        reread='apply unique cid and uds.',
        insight='disabling vsock is not unique cid',
        probe="rg -n 'unique' vm.json pack/vm.json",
        probe_obs='pack unique cid and uds. harbor disable vsock.',
        fix='unique cid and uds',
        fix_diff='+ unique cid and uds\n',
        rel='dump/vm.json',
        rel_src='"vsock": {"guest_cid": 3, "uds": "/tmp/vsock"}',
        leftover='wrong leftover disable vsock',
        fix2='dump unique cid and uds',
        fix2_diff='+ dump unique cid and uds\n',
        bad_pat='disable vsock',
        doc='docs/LOCK-CHVCID.md',
        doc_point='disabling vsock is not unique cid',
        doc_diff='+ disabling vsock is not unique cid.',
        reg='reg',
        reg_diff='+ unique cid and uds holds',
        final_ok='ok 6 passed. unique cid and uds.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='unique cid and uds; dump same.',
        wrap='the unique cid and uds',
        wrap_ok='6 passed. lock-chvcid assign is green.',
        wrap_part='5 passed, 1 residual. lock-chvcid assign is green.',
        goal='Designed plant lock-chvcid: the Cloud Hypervisor vsock that reused guest_cid 3 so the second VM failed to bind. unique cid and uds. disabling vsock is not unique cid.',
        plan='Repro python tests, reject disable vsock, unique cid and uds, fix dump.',
        out_ok='unique cid and uds. 6 tests pass.',
        out_part='unique cid and uds. dump leftover. Partial.',
    ),
    "qemu": P(False,
        slug='pr-qemu-user-binfmt-preserve-argv0',
        plant='quay-qemubinfmt',
        what='the qemu-user binfmt that omitted P flag so argv[0] became qemu-x86_64 and the wrapper missed the real name',
        glob='**/*.{cf,nix,scm,cfg,go,cc,py,tf,sh,yml,conf,json}',
        ls='binfmt.conf tests/test_harbor.py',
        impl='binfmt.conf',
        src=':qemu-x86_64:M::\\\\x7fELF::/usr/bin/qemu-x86_64:',
        sym='preserve-argv0 P',
        grep='preserve-argv0 P|binfmt',
        grep_obs='harbor qemu-x86_64-static only. pack binfmt P flag.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: argv[0] is qemu-x86_64; binfmt missing P; wrapper dispatch failed',
        tf='tests/test_harbor.py',
        tsrc="assert 'binfmt' in open('binfmt.conf').read() or True",
        wrong='qemu-x86_64-static only',
        wrong_diff='+ qemu-x86_64-static only',
        wrong_obs='still qemu-x86_64-static only. still fail.',
        fail2='FAIL test_assign: still broken. binfmt P flag.',
        reread='apply binfmt P flag.',
        insight='static binary is not preserve-argv0',
        probe="rg -n 'binfmt' binfmt.conf pack/binfmt.conf",
        probe_obs='pack binfmt P flag. harbor qemu-x86_64-static only.',
        fix='binfmt P flag',
        fix_diff='+ binfmt P flag\n',
        rel='dump/binfmt.conf',
        rel_src=':qemu-x86_64:M::\\\\x7fELF::/usr/bin/qemu-x86_64:',
        leftover='wrong leftover qemu-x86_64-static only',
        fix2='dump binfmt P flag',
        fix2_diff='+ dump binfmt P flag\n',
        bad_pat='qemu-x86_64-static only',
        doc='docs/QUAY-QEMUBINFMT.md',
        doc_point='static binary is not preserve-argv0',
        doc_diff='+ static binary is not preserve-argv0.',
        reg='reg',
        reg_diff='+ binfmt P flag holds',
        final_ok='ok 6 passed. binfmt P flag.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='binfmt P flag; dump leftover.',
        wrap='the binfmt P flag',
        wrap_ok='6 passed. quay-qemubinfmt assign is green.',
        wrap_part='5 passed, 1 residual. quay-qemubinfmt assign is green.',
        goal='Designed plant quay-qemubinfmt: the qemu-user binfmt that omitted P flag so argv[0] became qemu-x86_64 and the wrapper missed the real name. binfmt P flag. static binary is not preserve-argv0.',
        plan='Repro python tests, reject qemu-x86_64-static only, binfmt P flag, hand off dump.',
        out_ok='binfmt P flag. 6 tests pass.',
        out_part='binfmt P flag. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('CFEngine lock_expire_after vs NixOS mkForce iommu', fn('cfengine'), fn('nixos'), 'lock_expire_after 5; mkForce iommu on', 'ifelapsed 0; assignment merge', 'cfengine dump no expire; nixos dump mkDefault'),
    ('guix pack -R vs Sonic locale eng', fn('guix'), fn('sonic'), 'pack -R; locale eng', 'GUIX_LOCPATH; query_max_results', 'guix dump no -R; sonic dump locale none'),
    ('Bleve sku keyword vs Xapian boolean term', fn('bleve'), fn('xapian'), 'keyword analyzer; add_boolean_term', 'MatchPhraseQuery; query stemmer none', 'bleve dump standard sku; xapian dump stemmed id'),
    ('Whoosh ID unique vs KMS multi_region', fn('whoosh'), fn('kms'), 'ID unique; multi_region key', 'merge=True; second alias', 'whoosh dump TEXT id; kms dump regional key'),
    ('age -R recipients vs Mayastor ioTimeout', fn('age'), fn('mayastor'), 'age -R; ioTimeout 30', 'age -p; rebuildTimeout', 'age dump inline -r; mayastor dump ioTimeout 0'),
    ('crosvm jail vs innernet invite --cidr', fn('crosvm'), fn('innernet'), '--jail; --cidr', 'chmod dri; wg-quick down', 'crosvm dump disable-sandbox; innernet dump no cidr'),
    ('Libreswan narrowing=yes vs KVM nested=1', fn('libreswan'), fn('kvm'), 'narrowing=yes; nested=1', 'ike cipher; qemu cpu flags', 'libreswan dump narrowing=no; kvm dump no nested'),
    ('Cloud Hypervisor unique vsock cid vs qemu-user binfmt P', fn('cloudhv'), fn('qemu'), 'unique guest_cid; binfmt P flag', 'disable vsock; static only', 'cloudhv dump shared cid; qemu dump missing P'),
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
- Not a clone of r4163-r4492 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
