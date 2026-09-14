#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4ce: unused plants after r4532.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4532. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4ce_state.json")
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
    "starship": P(True,
        slug='pr-starship-cmd-duration-min',
        plant='lock-sscmd',
        what='the Starship prompt that omitted command_timeout so a hung git status froze every prompt for 2s',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='starship.toml tests/test_harbor.py',
        impl='starship.toml',
        src='[git_status]\ndisabled = false',
        sym='command_timeout 200',
        grep='command_timeout',
        grep_obs='harbor disabled git_status. pack command_timeout 200.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: prompt 2s hang; command_timeout default 500 missed hung git',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='disabled git_status',
        wrong_diff='+ disabled git_status',
        wrong_obs='still disabled git_status. still fail.',
        fail2='FAIL test_assign: still broken. command_timeout 200.',
        reread='apply command_timeout 200.',
        insight='disabling git_status is not command_timeout',
        probe="rg -n 'command_timeout' starship.toml",
        probe_obs='pack command_timeout 200. harbor disabled git_status.',
        fix='command_timeout 200',
        fix_diff='+ command_timeout 200\n',
        rel='dump/starship.toml',
        rel_src='[git_status]\ndisabled = false',
        leftover='leftover disabled git_status',
        fix2='dump command_timeout 200',
        fix2_diff='+ dump command_timeout 200\n',
        bad_pat='disabled git_status',
        doc='docs/LOCK-SSCMD.md',
        doc_point='disabling git_status is not command_timeout',
        doc_diff='+ disabling git_status is not command_timeout.',
        reg='reg',
        reg_diff='+ command_timeout 200 holds',
        final_ok='ok 6 passed. command_timeout 200.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='command_timeout 200; dump same.',
        wrap='the command_timeout 200',
        wrap_ok='6 passed. lock-sscmd assign is green.',
        wrap_part='5 passed, 1 residual. lock-sscmd assign is green.',
        goal='Designed plant lock-sscmd: the Starship prompt that omitted command_timeout so a hung git status froze every prompt for 2s. command_timeout 200. disabling git_status is not command_timeout.',
        plan='Repro python tests, reject disabled git_status, command_timeout 200, fix dump.',
        out_ok='command_timeout 200. 6 tests pass.',
        out_part='command_timeout 200. dump leftover. Partial.',
    ),
    "atuin": P(False,
        slug='pr-atuin-sync-encryption-key',
        plant='quay-atuinkey',
        what='the Atuin sync that omitted ATUIN_KEY so history uploaded plaintext and login on the laptop could not decrypt',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='config.toml tests/test_harbor.py',
        impl='config.toml',
        src='[sync]\nrecords = true',
        sym='ATUIN_KEY file',
        grep='ATUIN_KEY',
        grep_obs='harbor sync_address only. pack encryption key file.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: laptop decrypt fail; ATUIN_KEY missing; plaintext records',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='sync_address only',
        wrong_diff='+ sync_address only',
        wrong_obs='still sync_address only. still fail.',
        fail2='FAIL test_assign: still broken. encryption key file.',
        reread='apply encryption key file.',
        insight='sync_address is not ATUIN_KEY',
        probe="rg -n 'encryption' config.toml",
        probe_obs='pack encryption key file. harbor sync_address only.',
        fix='encryption key file',
        fix_diff='+ encryption key file\n',
        rel='dump/config.toml',
        rel_src='[sync]\nrecords = true',
        leftover='leftover sync_address only',
        fix2='dump encryption key file',
        fix2_diff='+ dump encryption key file\n',
        bad_pat='sync_address only',
        doc='docs/QUAY-ATUINKEY.md',
        doc_point='sync_address is not ATUIN_KEY',
        doc_diff='+ sync_address is not ATUIN_KEY.',
        reg='reg',
        reg_diff='+ encryption key file holds',
        final_ok='ok 6 passed. encryption key file.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='encryption key file; dump leftover.',
        wrap='the encryption key file',
        wrap_ok='6 passed. quay-atuinkey assign is green.',
        wrap_part='5 passed, 1 residual. quay-atuinkey assign is green.',
        goal='Designed plant quay-atuinkey: the Atuin sync that omitted ATUIN_KEY so history uploaded plaintext and login on the laptop could not decrypt. encryption key file. sync_address is not ATUIN_KEY.',
        plan='Repro python tests, reject sync_address only, encryption key file, hand off dump.',
        out_ok='encryption key file. 6 tests pass.',
        out_part='encryption key file. dump leftover. Partial.',
    ),
    "zoxide": P(True,
        slug='pr-zoxide-exclude-dirs-tmp',
        plant='lock-zoxexc',
        what='the zoxide init that omitted _ZO_EXCLUDE_DIRS so /tmp build trees polluted cd ranking',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='.bashrc tests/test_harbor.py',
        impl='.bashrc',
        src='eval "$(zoxide init bash)"',
        sym='_ZO_EXCLUDE_DIRS /tmp',
        grep='_ZO_EXCLUDE_DIRS',
        grep_obs='harbor _ZO_MAXAGE only. pack _ZO_EXCLUDE_DIRS /tmp.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: z tmp jumps to /tmp/harbor-build; exclude missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='_ZO_MAXAGE only',
        wrong_diff='+ _ZO_MAXAGE only',
        wrong_obs='still _ZO_MAXAGE only. still fail.',
        fail2='FAIL test_assign: still broken. _ZO_EXCLUDE_DIRS /tmp.',
        reread='apply _ZO_EXCLUDE_DIRS /tmp.',
        insight='_ZO_MAXAGE is not exclude',
        probe="rg -n '_ZO_EXCLUDE_DIRS' .bashrc",
        probe_obs='pack _ZO_EXCLUDE_DIRS /tmp. harbor _ZO_MAXAGE only.',
        fix='_ZO_EXCLUDE_DIRS /tmp',
        fix_diff='+ _ZO_EXCLUDE_DIRS /tmp\n',
        rel='dump/.bashrc',
        rel_src='eval "$(zoxide init bash)"',
        leftover='leftover _ZO_MAXAGE only',
        fix2='dump _ZO_EXCLUDE_DIRS /tmp',
        fix2_diff='+ dump _ZO_EXCLUDE_DIRS /tmp\n',
        bad_pat='_ZO_MAXAGE only',
        doc='docs/LOCK-ZOXEXC.md',
        doc_point='_ZO_MAXAGE is not exclude',
        doc_diff='+ _ZO_MAXAGE is not exclude.',
        reg='reg',
        reg_diff='+ _ZO_EXCLUDE_DIRS /tmp holds',
        final_ok='ok 6 passed. _ZO_EXCLUDE_DIRS /tmp.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='_ZO_EXCLUDE_DIRS /tmp; dump same.',
        wrap='the _ZO_EXCLUDE_DIRS /tmp',
        wrap_ok='6 passed. lock-zoxexc assign is green.',
        wrap_part='5 passed, 1 residual. lock-zoxexc assign is green.',
        goal='Designed plant lock-zoxexc: the zoxide init that omitted _ZO_EXCLUDE_DIRS so /tmp build trees polluted cd ranking. _ZO_EXCLUDE_DIRS /tmp. _ZO_MAXAGE is not exclude.',
        plan='Repro python tests, reject _ZO_MAXAGE only, _ZO_EXCLUDE_DIRS /tmp, fix dump.',
        out_ok='_ZO_EXCLUDE_DIRS /tmp. 6 tests pass.',
        out_part='_ZO_EXCLUDE_DIRS /tmp. dump leftover. Partial.',
    ),
    "jabba": P(False,
        slug='pr-jabba-alias-default-jdk',
        plant='quay-jabbadef',
        what='the Jabba install that omitted jabba alias default so CI used JAVA_HOME from the image 8 instead of 17',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='.jabbarc tests/test_harbor.py',
        impl='.jabbarc',
        src='jabba use 17',
        sym='jabba alias default',
        grep='jabba',
        grep_obs='harbor JAVA_HOME export only. pack alias default 17.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: java 8; alias default missing; next shell lost 17',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='JAVA_HOME export only',
        wrong_diff='+ JAVA_HOME export only',
        wrong_obs='still JAVA_HOME export only. still fail.',
        fail2='FAIL test_assign: still broken. alias default 17.',
        reread='apply alias default 17.',
        insight='JAVA_HOME export is overwritten without alias default',
        probe="rg -n 'alias' .jabbarc",
        probe_obs='pack alias default 17. harbor JAVA_HOME export only.',
        fix='alias default 17',
        fix_diff='+ alias default 17\n',
        rel='dump/.jabbarc',
        rel_src='jabba use 17',
        leftover='leftover JAVA_HOME export only',
        fix2='dump alias default 17',
        fix2_diff='+ dump alias default 17\n',
        bad_pat='JAVA_HOME export only',
        doc='docs/QUAY-JABBADEF.md',
        doc_point='JAVA_HOME export is overwritten without alias default',
        doc_diff='+ JAVA_HOME export is overwritten without alias default.',
        reg='reg',
        reg_diff='+ alias default 17 holds',
        final_ok='ok 6 passed. alias default 17.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='alias default 17; dump leftover.',
        wrap='the alias default 17',
        wrap_ok='6 passed. quay-jabbadef assign is green.',
        wrap_part='5 passed, 1 residual. quay-jabbadef assign is green.',
        goal='Designed plant quay-jabbadef: the Jabba install that omitted jabba alias default so CI used JAVA_HOME from the image 8 instead of 17. alias default 17. JAVA_HOME export is overwritten without alias default.',
        plan='Repro python tests, reject JAVA_HOME export only, alias default 17, hand off dump.',
        out_ok='alias default 17. 6 tests pass.',
        out_part='alias default 17. dump leftover. Partial.',
    ),
    "nvm": P(True,
        slug='pr-nvm-default-packages-yarn',
        plant='lock-nvmdpkg',
        what='the nvm default-packages that omitted yarn so a new node had no yarn and CI used the apt 1.22',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='default-packages tests/test_harbor.py',
        impl='default-packages',
        src='typescript\neslint',
        sym='yarn in default-packages',
        grep='yarn',
        grep_obs='harbor npm i -g yarn in CI. pack default-packages yarn.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: yarn 1.22 apt; default-packages missing yarn',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='npm i -g yarn in CI',
        wrong_diff='+ npm i -g yarn in CI',
        wrong_obs='still npm i -g yarn in CI. still fail.',
        fail2='FAIL test_assign: still broken. default-packages yarn.',
        reread='apply default-packages yarn.',
        insight='CI npm i -g is overwritten by nvm reinstall',
        probe="rg -n 'default-packages' default-packages",
        probe_obs='pack default-packages yarn. harbor npm i -g yarn in CI.',
        fix='default-packages yarn',
        fix_diff='+ default-packages yarn\n',
        rel='dump/default-packages',
        rel_src='typescript\neslint',
        leftover='leftover npm i -g yarn in CI',
        fix2='dump default-packages yarn',
        fix2_diff='+ dump default-packages yarn\n',
        bad_pat='npm i -g yarn in CI',
        doc='docs/LOCK-NVMDPKG.md',
        doc_point='CI npm i -g is overwritten by nvm reinstall',
        doc_diff='+ CI npm i -g is overwritten by nvm reinstall.',
        reg='reg',
        reg_diff='+ default-packages yarn holds',
        final_ok='ok 6 passed. default-packages yarn.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='default-packages yarn; dump same.',
        wrap='the default-packages yarn',
        wrap_ok='6 passed. lock-nvmdpkg assign is green.',
        wrap_part='5 passed, 1 residual. lock-nvmdpkg assign is green.',
        goal='Designed plant lock-nvmdpkg: the nvm default-packages that omitted yarn so a new node had no yarn and CI used the apt 1.22. default-packages yarn. CI npm i -g is overwritten by nvm reinstall.',
        plan='Repro python tests, reject npm i -g yarn in CI, default-packages yarn, fix dump.',
        out_ok='default-packages yarn. 6 tests pass.',
        out_part='default-packages yarn. dump leftover. Partial.',
    ),
    "commitizen": P(False,
        slug='pr-commitizen-cz-conventional-path',
        plant='quay-czpath',
        what='the Commitizen config that omitted path cz-conventional-changelog so cz commit used the default adapter and skipped the jira prefix',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='.czrc tests/test_harbor.py',
        impl='.czrc',
        src='{"commitizen": {}}',
        sym='path cz-conventional-changelog',
        grep='path',
        grep_obs='harbor husky commit-msg only. pack path adapter.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: commit missing JIRA-; cz path missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='husky commit-msg only',
        wrong_diff='+ husky commit-msg only',
        wrong_obs='still husky commit-msg only. still fail.',
        fail2='FAIL test_assign: still broken. path adapter.',
        reread='apply path adapter.',
        insight='commit-msg hook is not the cz adapter path',
        probe="rg -n 'path' .czrc",
        probe_obs='pack path adapter. harbor husky commit-msg only.',
        fix='path adapter',
        fix_diff='+ path adapter\n',
        rel='dump/.czrc',
        rel_src='{"commitizen": {}}',
        leftover='leftover husky commit-msg only',
        fix2='dump path adapter',
        fix2_diff='+ dump path adapter\n',
        bad_pat='husky commit-msg only',
        doc='docs/QUAY-CZPATH.md',
        doc_point='commit-msg hook is not the cz adapter path',
        doc_diff='+ commit-msg hook is not the cz adapter path.',
        reg='reg',
        reg_diff='+ path adapter holds',
        final_ok='ok 6 passed. path adapter.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='path adapter; dump leftover.',
        wrap='the path adapter',
        wrap_ok='6 passed. quay-czpath assign is green.',
        wrap_part='5 passed, 1 residual. quay-czpath assign is green.',
        goal='Designed plant quay-czpath: the Commitizen config that omitted path cz-conventional-changelog so cz commit used the default adapter and skipped the jira prefix. path adapter. commit-msg hook is not the cz adapter path.',
        plan='Repro python tests, reject husky commit-msg only, path adapter, hand off dump.',
        out_ok='path adapter. 6 tests pass.',
        out_part='path adapter. dump leftover. Partial.',
    ),
    "cocogitto": P(True,
        slug='pr-cocogitto-ignore-merge-commits',
        plant='lock-cogoign',
        what='the Cocogitto check that omitted ignore_merge_commits so a merge commit failed conventional and blocked the PR',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='cog.toml tests/test_harbor.py',
        impl='cog.toml',
        src='branch_whitelist = []',
        sym='ignore_merge_commits true',
        grep='ignore_merge_commits',
        grep_obs='harbor skip_ci only. pack ignore_merge_commits.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: merge commit failed conventional; ignore_merge_commits missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='skip_ci only',
        wrong_diff='+ skip_ci only',
        wrong_obs='still skip_ci only. still fail.',
        fail2='FAIL test_assign: still broken. ignore_merge_commits.',
        reread='apply ignore_merge_commits.',
        insight='skip_ci is not ignore_merge_commits',
        probe="rg -n 'ignore_merge_commits' cog.toml",
        probe_obs='pack ignore_merge_commits. harbor skip_ci only.',
        fix='ignore_merge_commits',
        fix_diff='+ ignore_merge_commits\n',
        rel='dump/cog.toml',
        rel_src='branch_whitelist = []',
        leftover='leftover skip_ci only',
        fix2='dump ignore_merge_commits',
        fix2_diff='+ dump ignore_merge_commits\n',
        bad_pat='skip_ci only',
        doc='docs/LOCK-COGOIGN.md',
        doc_point='skip_ci is not ignore_merge_commits',
        doc_diff='+ skip_ci is not ignore_merge_commits.',
        reg='reg',
        reg_diff='+ ignore_merge_commits holds',
        final_ok='ok 6 passed. ignore_merge_commits.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ignore_merge_commits; dump same.',
        wrap='the ignore_merge_commits',
        wrap_ok='6 passed. lock-cogoign assign is green.',
        wrap_part='5 passed, 1 residual. lock-cogoign assign is green.',
        goal='Designed plant lock-cogoign: the Cocogitto check that omitted ignore_merge_commits so a merge commit failed conventional and blocked the PR. ignore_merge_commits. skip_ci is not ignore_merge_commits.',
        plan='Repro python tests, reject skip_ci only, ignore_merge_commits, fix dump.',
        out_ok='ignore_merge_commits. 6 tests pass.',
        out_part='ignore_merge_commits. dump leftover. Partial.',
    ),
    "precommit": P(False,
        slug='pr-precommit-default-stages-manual',
        plant='quay-pcman',
        what='the pre-commit hook that omitted stages so a manual-only hook ran on commit and timed out the 30s hook window',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='.pre-commit-config.yaml tests/test_harbor.py',
        impl='.pre-commit-config.yaml',
        src='repos:\n- repo: local\n  hooks:\n  - id: e2e',
        sym='stages [manual]',
        grep='stages',
        grep_obs='harbor timeout 120 only. pack stages [manual].',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: e2e ran on commit 30s timeout; stages missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='timeout 120 only',
        wrong_diff='+ timeout 120 only',
        wrong_obs='still timeout 120 only. still fail.',
        fail2='FAIL test_assign: still broken. stages [manual].',
        reread='apply stages [manual].',
        insight='timeout 120 is not stages manual',
        probe="rg -n 'stages' .pre-commit-config.yaml",
        probe_obs='pack stages [manual]. harbor timeout 120 only.',
        fix='stages [manual]',
        fix_diff='+ stages [manual]\n',
        rel='dump/.pre-commit-config.yaml',
        rel_src='repos:\n- repo: local\n  hooks:\n  - id: e2e',
        leftover='leftover timeout 120 only',
        fix2='dump stages [manual]',
        fix2_diff='+ dump stages [manual]\n',
        bad_pat='timeout 120 only',
        doc='docs/QUAY-PCMAN.md',
        doc_point='timeout 120 is not stages manual',
        doc_diff='+ timeout 120 is not stages manual.',
        reg='reg',
        reg_diff='+ stages [manual] holds',
        final_ok='ok 6 passed. stages [manual].',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='stages [manual]; dump leftover.',
        wrap='the stages [manual]',
        wrap_ok='6 passed. quay-pcman assign is green.',
        wrap_part='5 passed, 1 residual. quay-pcman assign is green.',
        goal='Designed plant quay-pcman: the pre-commit hook that omitted stages so a manual-only hook ran on commit and timed out the 30s hook window. stages [manual]. timeout 120 is not stages manual.',
        plan='Repro python tests, reject timeout 120 only, stages [manual], hand off dump.',
        out_ok='stages [manual]. 6 tests pass.',
        out_part='stages [manual]. dump leftover. Partial.',
    ),
    "semanticrelease": P(True,
        slug='pr-semanticrelease-npm-pkgroot',
        plant='lock-semrelpkg',
        what='the semantic-release npm plugin that omitted pkgRoot so it published the repo root instead of dist and the tarball lacked index.js',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='.releaserc.json tests/test_harbor.py',
        impl='.releaserc.json',
        src='{"plugins": ["@semantic-release/npm"]}',
        sym='pkgRoot dist',
        grep='pkgRoot',
        grep_obs='harbor tarballDir only. pack pkgRoot dist.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: npm pack missing index.js; pkgRoot missing; published repo root',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='tarballDir only',
        wrong_diff='+ tarballDir only',
        wrong_obs='still tarballDir only. still fail.',
        fail2='FAIL test_assign: still broken. pkgRoot dist.',
        reread='apply pkgRoot dist.',
        insight='tarballDir is not pkgRoot',
        probe="rg -n 'pkgRoot' .releaserc.json",
        probe_obs='pack pkgRoot dist. harbor tarballDir only.',
        fix='pkgRoot dist',
        fix_diff='+ pkgRoot dist\n',
        rel='dump/.releaserc.json',
        rel_src='{"plugins": ["@semantic-release/npm"]}',
        leftover='leftover tarballDir only',
        fix2='dump pkgRoot dist',
        fix2_diff='+ dump pkgRoot dist\n',
        bad_pat='tarballDir only',
        doc='docs/LOCK-SEMRELPKG.md',
        doc_point='tarballDir is not pkgRoot',
        doc_diff='+ tarballDir is not pkgRoot.',
        reg='reg',
        reg_diff='+ pkgRoot dist holds',
        final_ok='ok 6 passed. pkgRoot dist.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pkgRoot dist; dump same.',
        wrap='the pkgRoot dist',
        wrap_ok='6 passed. lock-semrelpkg assign is green.',
        wrap_part='5 passed, 1 residual. lock-semrelpkg assign is green.',
        goal='Designed plant lock-semrelpkg: the semantic-release npm plugin that omitted pkgRoot so it published the repo root instead of dist and the tarball lacked index.js. pkgRoot dist. tarballDir is not pkgRoot.',
        plan='Repro python tests, reject tarballDir only, pkgRoot dist, fix dump.',
        out_ok='pkgRoot dist. 6 tests pass.',
        out_part='pkgRoot dist. dump leftover. Partial.',
    ),
    "skaffold": P(False,
        slug='pr-skaffold-digest-source-tag',
        plant='quay-skfdig',
        what='the Skaffold deploy that omitted digestSource so a :latest tag was applied and the cluster pulled a stale digest',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='skaffold.yaml tests/test_harbor.py',
        impl='skaffold.yaml',
        src='build:\n  artifacts: [{image: harbor}]',
        sym='digestSource default',
        grep='digestSource',
        grep_obs='harbor tagPolicy gitCommit only. pack digestSource default.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cluster ran old digest; :latest applied; digestSource missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='tagPolicy gitCommit only',
        wrong_diff='+ tagPolicy gitCommit only',
        wrong_obs='still tagPolicy gitCommit only. still fail.',
        fail2='FAIL test_assign: still broken. digestSource default.',
        reread='apply digestSource default.',
        insight='gitCommit tagPolicy is not digestSource',
        probe="rg -n 'digestSource' skaffold.yaml",
        probe_obs='pack digestSource default. harbor tagPolicy gitCommit only.',
        fix='digestSource default',
        fix_diff='+ digestSource default\n',
        rel='dump/skaffold.yaml',
        rel_src='build:\n  artifacts: [{image: harbor}]',
        leftover='leftover tagPolicy gitCommit only',
        fix2='dump digestSource default',
        fix2_diff='+ dump digestSource default\n',
        bad_pat='tagPolicy gitCommit only',
        doc='docs/QUAY-SKFDIG.md',
        doc_point='gitCommit tagPolicy is not digestSource',
        doc_diff='+ gitCommit tagPolicy is not digestSource.',
        reg='reg',
        reg_diff='+ digestSource default holds',
        final_ok='ok 6 passed. digestSource default.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='digestSource default; dump leftover.',
        wrap='the digestSource default',
        wrap_ok='6 passed. quay-skfdig assign is green.',
        wrap_part='5 passed, 1 residual. quay-skfdig assign is green.',
        goal='Designed plant quay-skfdig: the Skaffold deploy that omitted digestSource so a :latest tag was applied and the cluster pulled a stale digest. digestSource default. gitCommit tagPolicy is not digestSource.',
        plan='Repro python tests, reject tagPolicy gitCommit only, digestSource default, hand off dump.',
        out_ok='digestSource default. 6 tests pass.',
        out_part='digestSource default. dump leftover. Partial.',
    ),
    "tilt": P(True,
        slug='pr-tilt-live-update-fall-back',
        plant='lock-tiltlive',
        what='the Tilt live_update that omitted fall_back_on so an unlisted file change did not rebuild and the running container stayed stale',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='Tiltfile tests/test_harbor.py',
        impl='Tiltfile',
        src="docker_build('harbor', '.', live_update=[sync('.', '/app')])",
        sym='fall_back_on package.json',
        grep='fall_back_on',
        grep_obs='harbor only sync. pack fall_back_on.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: package.json change no rebuild; fall_back_on missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='only sync',
        wrong_diff='+ only sync',
        wrong_obs='still only sync. still fail.',
        fail2='FAIL test_assign: still broken. fall_back_on.',
        reread='apply fall_back_on.',
        insight='sync is not fall_back_on',
        probe="rg -n 'fall_back_on' Tiltfile",
        probe_obs='pack fall_back_on. harbor only sync.',
        fix='fall_back_on',
        fix_diff='+ fall_back_on\n',
        rel='dump/Tiltfile',
        rel_src="docker_build('harbor', '.', live_update=[sync('.', '/app')])",
        leftover='leftover only sync',
        fix2='dump fall_back_on',
        fix2_diff='+ dump fall_back_on\n',
        bad_pat='only sync',
        doc='docs/LOCK-TILTLIVE.md',
        doc_point='sync is not fall_back_on',
        doc_diff='+ sync is not fall_back_on.',
        reg='reg',
        reg_diff='+ fall_back_on holds',
        final_ok='ok 6 passed. fall_back_on.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='fall_back_on; dump same.',
        wrap='the fall_back_on',
        wrap_ok='6 passed. lock-tiltlive assign is green.',
        wrap_part='5 passed, 1 residual. lock-tiltlive assign is green.',
        goal='Designed plant lock-tiltlive: the Tilt live_update that omitted fall_back_on so an unlisted file change did not rebuild and the running container stayed stale. fall_back_on. sync is not fall_back_on.',
        plan='Repro python tests, reject only sync, fall_back_on, fix dump.',
        out_ok='fall_back_on. 6 tests pass.',
        out_part='fall_back_on. dump leftover. Partial.',
    ),
    "garden": P(False,
        slug='pr-garden-hot-reload-dev-mode',
        plant='quay-gdnhot',
        what='the Garden deploy that omitted spec.devMode so a code sync never started and the pod kept the image filesystem',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='garden.yml tests/test_harbor.py',
        impl='garden.yml',
        src='kind: Deploy\ntype: kubernetes',
        sym='spec.devMode sync',
        grep='spec.devMode',
        grep_obs='harbor hotReload only v1. pack devMode sync.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pod files stale; spec.devMode missing; v1 hotReload ignored',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='hotReload only v1',
        wrong_diff='+ hotReload only v1',
        wrong_obs='still hotReload only v1. still fail.',
        fail2='FAIL test_assign: still broken. devMode sync.',
        reread='apply devMode sync.',
        insight='v1 hotReload is not spec.devMode',
        probe="rg -n 'devMode' garden.yml",
        probe_obs='pack devMode sync. harbor hotReload only v1.',
        fix='devMode sync',
        fix_diff='+ devMode sync\n',
        rel='dump/garden.yml',
        rel_src='kind: Deploy\ntype: kubernetes',
        leftover='leftover hotReload only v1',
        fix2='dump devMode sync',
        fix2_diff='+ dump devMode sync\n',
        bad_pat='hotReload only v1',
        doc='docs/QUAY-GDNHOT.md',
        doc_point='v1 hotReload is not spec.devMode',
        doc_diff='+ v1 hotReload is not spec.devMode.',
        reg='reg',
        reg_diff='+ devMode sync holds',
        final_ok='ok 6 passed. devMode sync.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='devMode sync; dump leftover.',
        wrap='the devMode sync',
        wrap_ok='6 passed. quay-gdnhot assign is green.',
        wrap_part='5 passed, 1 residual. quay-gdnhot assign is green.',
        goal='Designed plant quay-gdnhot: the Garden deploy that omitted spec.devMode so a code sync never started and the pod kept the image filesystem. devMode sync. v1 hotReload is not spec.devMode.',
        plan='Repro python tests, reject hotReload only v1, devMode sync, hand off dump.',
        out_ok='devMode sync. 6 tests pass.',
        out_part='devMode sync. dump leftover. Partial.',
    ),
    "telepresence": P(True,
        slug='pr-telepresence-also-proxy-subnet',
        plant='lock-tpxalso',
        what='the Telepresence intercept that omitted --also-proxy so cluster DNS for RDS never resolved on the laptop',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='telepresence intercept harbor --port 8080',
        sym='also-proxy RDS subnet',
        grep='also-proxy',
        grep_obs='harbor dns local only. pack also-proxy subnet.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: RDS NXDOMAIN; also-proxy missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='dns local only',
        wrong_diff='+ dns local only',
        wrong_obs='still dns local only. still fail.',
        fail2='FAIL test_assign: still broken. also-proxy subnet.',
        reread='apply also-proxy subnet.',
        insight='local dns is not also-proxy',
        probe="rg -n 'also-proxy' Makefile",
        probe_obs='pack also-proxy subnet. harbor dns local only.',
        fix='also-proxy subnet',
        fix_diff='+ also-proxy subnet\n',
        rel='dump/Makefile',
        rel_src='telepresence intercept harbor --port 8080',
        leftover='leftover dns local only',
        fix2='dump also-proxy subnet',
        fix2_diff='+ dump also-proxy subnet\n',
        bad_pat='dns local only',
        doc='docs/LOCK-TPXALSO.md',
        doc_point='local dns is not also-proxy',
        doc_diff='+ local dns is not also-proxy.',
        reg='reg',
        reg_diff='+ also-proxy subnet holds',
        final_ok='ok 6 passed. also-proxy subnet.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='also-proxy subnet; dump same.',
        wrap='the also-proxy subnet',
        wrap_ok='6 passed. lock-tpxalso assign is green.',
        wrap_part='5 passed, 1 residual. lock-tpxalso assign is green.',
        goal='Designed plant lock-tpxalso: the Telepresence intercept that omitted --also-proxy so cluster DNS for RDS never resolved on the laptop. also-proxy subnet. local dns is not also-proxy.',
        plan='Repro python tests, reject dns local only, also-proxy subnet, fix dump.',
        out_ok='also-proxy subnet. 6 tests pass.',
        out_part='also-proxy subnet. dump leftover. Partial.',
    ),
    "helmfile": P(False,
        slug='pr-helmfile-missing-file-handler',
        plant='quay-hfmfile',
        what='the Helmfile that omitted missingFileHandler so a missing secrets.yaml aborted the entire apply',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='helmfile.yaml tests/test_harbor.py',
        impl='helmfile.yaml',
        src='releases:\n- name: harbor\n  values: [secrets.yaml]',
        sym='missingFileHandler Warn',
        grep='missingFileHandler',
        grep_obs='harbor skipDeps. pack missingFileHandler Warn.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: helmfile apply aborted; secrets.yaml missing; handler Error default',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='skipDeps',
        wrong_diff='+ skipDeps',
        wrong_obs='still skipDeps. still fail.',
        fail2='FAIL test_assign: still broken. missingFileHandler Warn.',
        reread='apply missingFileHandler Warn.',
        insight='skipDeps is not missingFileHandler',
        probe="rg -n 'missingFileHandler' helmfile.yaml",
        probe_obs='pack missingFileHandler Warn. harbor skipDeps.',
        fix='missingFileHandler Warn',
        fix_diff='+ missingFileHandler Warn\n',
        rel='dump/helmfile.yaml',
        rel_src='releases:\n- name: harbor\n  values: [secrets.yaml]',
        leftover='leftover skipDeps',
        fix2='dump missingFileHandler Warn',
        fix2_diff='+ dump missingFileHandler Warn\n',
        bad_pat='skipDeps',
        doc='docs/QUAY-HFMFILE.md',
        doc_point='skipDeps is not missingFileHandler',
        doc_diff='+ skipDeps is not missingFileHandler.',
        reg='reg',
        reg_diff='+ missingFileHandler Warn holds',
        final_ok='ok 6 passed. missingFileHandler Warn.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='missingFileHandler Warn; dump leftover.',
        wrap='the missingFileHandler Warn',
        wrap_ok='6 passed. quay-hfmfile assign is green.',
        wrap_part='5 passed, 1 residual. quay-hfmfile assign is green.',
        goal='Designed plant quay-hfmfile: the Helmfile that omitted missingFileHandler so a missing secrets.yaml aborted the entire apply. missingFileHandler Warn. skipDeps is not missingFileHandler.',
        plan='Repro python tests, reject skipDeps, missingFileHandler Warn, hand off dump.',
        out_ok='missingFileHandler Warn. 6 tests pass.',
        out_part='missingFileHandler Warn. dump leftover. Partial.',
    ),
    "kustomize": P(True,
        slug='pr-kustomize-helm-enable-inflate',
        plant='lock-kusthelm',
        what='the Kustomize build that omitted --enable-helm so a helmCharts inflator was skipped and the CRDs never rendered',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='kustomization.yaml tests/test_harbor.py',
        impl='kustomization.yaml',
        src='helmCharts:\n- name: harbor',
        sym='enable-helm',
        grep='enable-helm',
        grep_obs='harbor helmGlobals loadRestrictor. pack kustomize build --enable-helm.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: 0 CRDs; helmCharts skipped; --enable-helm missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='helmGlobals loadRestrictor',
        wrong_diff='+ helmGlobals loadRestrictor',
        wrong_obs='still helmGlobals loadRestrictor. still fail.',
        fail2='FAIL test_assign: still broken. kustomize build --enable-helm.',
        reread='apply kustomize build --enable-helm.',
        insight='loadRestrictor is not --enable-helm',
        probe="rg -n 'kustomize' kustomization.yaml",
        probe_obs='pack kustomize build --enable-helm. harbor helmGlobals loadRestrictor.',
        fix='kustomize build --enable-helm',
        fix_diff='+ kustomize build --enable-helm\n',
        rel='dump/kustomization.yaml',
        rel_src='helmCharts:\n- name: harbor',
        leftover='leftover helmGlobals loadRestrictor',
        fix2='dump kustomize build --enable-helm',
        fix2_diff='+ dump kustomize build --enable-helm\n',
        bad_pat='helmGlobals loadRestrictor',
        doc='docs/LOCK-KUSTHELM.md',
        doc_point='loadRestrictor is not --enable-helm',
        doc_diff='+ loadRestrictor is not --enable-helm.',
        reg='reg',
        reg_diff='+ kustomize build --enable-helm holds',
        final_ok='ok 6 passed. kustomize build --enable-helm.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='kustomize build --enable-helm; dump same.',
        wrap='the kustomize build --enable-helm',
        wrap_ok='6 passed. lock-kusthelm assign is green.',
        wrap_part='5 passed, 1 residual. lock-kusthelm assign is green.',
        goal='Designed plant lock-kusthelm: the Kustomize build that omitted --enable-helm so a helmCharts inflator was skipped and the CRDs never rendered. kustomize build --enable-helm. loadRestrictor is not --enable-helm.',
        plan='Repro python tests, reject helmGlobals loadRestrictor, kustomize build --enable-helm, fix dump.',
        out_ok='kustomize build --enable-helm. 6 tests pass.',
        out_part='kustomize build --enable-helm. dump leftover. Partial.',
    ),
    "sam": P(False,
        slug='pr-sam-sync-watch-exclude-venv',
        plant='quay-samwatch',
        what='the SAM sync that omitted watch exclude so a .venv change retriggered deploy in a loop',
        glob='**/*.{toml,yml,sh,json,star}',
        ls='samconfig.toml tests/test_harbor.py',
        impl='samconfig.toml',
        src='[default.sync.parameters]\nwatch = true',
        sym='watch exclude .venv',
        grep='watch',
        grep_obs='harbor warm_containers EAGER. pack watch exclude .venv.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: sync loop on .venv; watch exclude missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='warm_containers EAGER',
        wrong_diff='+ warm_containers EAGER',
        wrong_obs='still warm_containers EAGER. still fail.',
        fail2='FAIL test_assign: still broken. watch exclude .venv.',
        reread='apply watch exclude .venv.',
        insight='warm_containers is not watch exclude',
        probe="rg -n 'watch' samconfig.toml",
        probe_obs='pack watch exclude .venv. harbor warm_containers EAGER.',
        fix='watch exclude .venv',
        fix_diff='+ watch exclude .venv\n',
        rel='dump/samconfig.toml',
        rel_src='[default.sync.parameters]\nwatch = true',
        leftover='leftover warm_containers EAGER',
        fix2='dump watch exclude .venv',
        fix2_diff='+ dump watch exclude .venv\n',
        bad_pat='warm_containers EAGER',
        doc='docs/QUAY-SAMWATCH.md',
        doc_point='warm_containers is not watch exclude',
        doc_diff='+ warm_containers is not watch exclude.',
        reg='reg',
        reg_diff='+ watch exclude .venv holds',
        final_ok='ok 6 passed. watch exclude .venv.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='watch exclude .venv; dump leftover.',
        wrap='the watch exclude .venv',
        wrap_ok='6 passed. quay-samwatch assign is green.',
        wrap_part='5 passed, 1 residual. quay-samwatch assign is green.',
        goal='Designed plant quay-samwatch: the SAM sync that omitted watch exclude so a .venv change retriggered deploy in a loop. watch exclude .venv. warm_containers is not watch exclude.',
        plan='Repro python tests, reject warm_containers EAGER, watch exclude .venv, hand off dump.',
        out_ok='watch exclude .venv. 6 tests pass.',
        out_part='watch exclude .venv. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Starship command_timeout vs Atuin ATUIN_KEY', fn('starship'), fn('atuin'), 'command_timeout 200; ATUIN_KEY file', 'disable git_status; sync_address', 'starship dump hung prompt; atuin dump plaintext history'),
    ('zoxide exclude /tmp vs Jabba alias default', fn('zoxide'), fn('jabba'), '_ZO_EXCLUDE_DIRS /tmp; alias default 17', '_ZO_MAXAGE; JAVA_HOME export', 'zoxide dump /tmp ranking; jabba dump java 8'),
    ('nvm default-packages yarn vs Commitizen cz path', fn('nvm'), fn('commitizen'), 'default-packages yarn; path cz-conventional-changelog', 'npm i -g yarn; commit-msg hook', 'nvm dump yarn 1.22; commitizen dump missing JIRA-'),
    ('Cocogitto ignore_merge_commits vs pre-commit stages manual', fn('cocogitto'), fn('precommit'), 'ignore_merge_commits; stages [manual]', 'skip_ci; timeout 120', 'cocogitto dump merge fail; pre-commit dump e2e on commit'),
    ('semantic-release pkgRoot vs Skaffold digestSource', fn('semanticrelease'), fn('skaffold'), 'pkgRoot dist; digestSource default', 'tarballDir; gitCommit tagPolicy', 'semantic-release dump root tarball; skaffold dump stale :latest'),
    ('Tilt fall_back_on vs Garden spec.devMode', fn('tilt'), fn('garden'), 'fall_back_on package.json; spec.devMode sync', 'only sync; v1 hotReload', 'tilt dump no rebuild; garden dump stale pod files'),
    ('Telepresence also-proxy vs Helmfile missingFileHandler', fn('telepresence'), fn('helmfile'), 'also-proxy RDS subnet; missingFileHandler Warn', 'local dns; skipDeps', 'telepresence dump RDS NXDOMAIN; helmfile dump aborted'),
    ('Kustomize --enable-helm vs SAM watch exclude', fn('kustomize'), fn('sam'), 'kustomize build --enable-helm; watch exclude .venv', 'loadRestrictor; warm_containers', 'kustomize dump 0 CRDs; sam dump sync loop'),
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
- Not a clone of r4163-r4532 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
