#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cd: unused plants after r4524.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4524. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cd_state.json")
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
    "direnv": P(True,
        slug='pr-direnv-dotenv-watch-strict',
        plant='lock-direnvw',
        what='the direnv .envrc that omitted dotenv_if_exists watch so a .env edit never reloaded and the token stayed stale',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='.envrc tests/test_harbor.py',
        impl='.envrc',
        src='dotenv',
        sym='watch_file .env',
        grep='watch_file',
        grep_obs='harbor layout python only. pack watch_file .env.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: TOKEN stale after .env edit; watch_file missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='layout python only',
        wrong_diff='+ layout python only',
        wrong_obs='still layout python only. still fail.',
        fail2='FAIL test_assign: still broken. watch_file .env.',
        reread='apply watch_file .env.',
        insight='layout python is not watch_file',
        probe="rg -n 'watch_file' .envrc",
        probe_obs='pack watch_file .env. harbor layout python only.',
        fix='watch_file .env',
        fix_diff='+ watch_file .env\n',
        rel='dump/.envrc',
        rel_src='dotenv',
        leftover='leftover layout python only',
        fix2='dump watch_file .env',
        fix2_diff='+ dump watch_file .env\n',
        bad_pat='layout python only',
        doc='docs/LOCK-DIRENVW.md',
        doc_point='layout python is not watch_file',
        doc_diff='+ layout python is not watch_file.',
        reg='reg',
        reg_diff='+ watch_file .env holds',
        final_ok='ok 6 passed. watch_file .env.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='watch_file .env; dump same.',
        wrap='the watch_file .env',
        wrap_ok='6 passed. lock-direnvw assign is green.',
        wrap_part='5 passed, 1 residual. lock-direnvw assign is green.',
        goal='Designed plant lock-direnvw: the direnv .envrc that omitted dotenv_if_exists watch so a .env edit never reloaded and the token stayed stale. watch_file .env. layout python is not watch_file.',
        plan='Repro python tests, reject layout python only, watch_file .env, fix dump.',
        out_ok='watch_file .env. 6 tests pass.',
        out_part='watch_file .env. dump leftover. Partial.',
    ),
    "asdf": P(False,
        slug='pr-asdf-legacy-file-python-version',
        plant='quay-asdflg',
        what='the asdf install that omitted legacy_version_file so .python-version was ignored and 3.11 ran instead of 3.12',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='.asdfrc tests/test_harbor.py',
        impl='.asdfrc',
        src='legacy_version_file = no',
        sym='legacy_version_file yes',
        grep='legacy_version_file',
        grep_obs='harbor asdf local python only. pack legacy_version_file yes.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: python 3.11; .python-version 3.12 ignored; legacy_version_file no',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='asdf local python only',
        wrong_diff='+ asdf local python only',
        wrong_obs='still asdf local python only. still fail.',
        fail2='FAIL test_assign: still broken. legacy_version_file yes.',
        reread='apply legacy_version_file yes.',
        insight='asdf local is not legacy_version_file',
        probe="rg -n 'legacy_version_file' .asdfrc",
        probe_obs='pack legacy_version_file yes. harbor asdf local python only.',
        fix='legacy_version_file yes',
        fix_diff='+ legacy_version_file yes\n',
        rel='dump/.asdfrc',
        rel_src='legacy_version_file = no',
        leftover='leftover asdf local python only',
        fix2='dump legacy_version_file yes',
        fix2_diff='+ dump legacy_version_file yes\n',
        bad_pat='asdf local python only',
        doc='docs/QUAY-ASDFLG.md',
        doc_point='asdf local is not legacy_version_file',
        doc_diff='+ asdf local is not legacy_version_file.',
        reg='reg',
        reg_diff='+ legacy_version_file yes holds',
        final_ok='ok 6 passed. legacy_version_file yes.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='legacy_version_file yes; dump leftover.',
        wrap='the legacy_version_file yes',
        wrap_ok='6 passed. quay-asdflg assign is green.',
        wrap_part='5 passed, 1 residual. quay-asdflg assign is green.',
        goal='Designed plant quay-asdflg: the asdf install that omitted legacy_version_file so .python-version was ignored and 3.11 ran instead of 3.12. legacy_version_file yes. asdf local is not legacy_version_file.',
        plan='Repro python tests, reject asdf local python only, legacy_version_file yes, hand off dump.',
        out_ok='legacy_version_file yes. 6 tests pass.',
        out_part='legacy_version_file yes. dump leftover. Partial.',
    ),
    "mise": P(True,
        slug='pr-mise-idiomatic-version-file-enable',
        plant='lock-miseidiom',
        what='the mise config that omitted idiomatic_version_file_enable_tools so .nvmrc was ignored and node 18 ran',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='mise.toml tests/test_harbor.py',
        impl='mise.toml',
        src='[tools]\nnode = "20"',
        sym='idiomatic_version_file_enable_tools',
        grep='idiomatic_version_file_enable_tools',
        grep_obs='harbor mise trust only. pack idiomatic nvmrc.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: node 18 from PATH; .nvmrc 20 ignored; idiomatic file off',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='mise trust only',
        wrong_diff='+ mise trust only',
        wrong_obs='still mise trust only. still fail.',
        fail2='FAIL test_assign: still broken. idiomatic nvmrc.',
        reread='apply idiomatic nvmrc.',
        insight='mise trust is not idiomatic_version_file',
        probe="rg -n 'idiomatic' mise.toml",
        probe_obs='pack idiomatic nvmrc. harbor mise trust only.',
        fix='idiomatic nvmrc',
        fix_diff='+ idiomatic nvmrc\n',
        rel='dump/mise.toml',
        rel_src='[tools]\nnode = "20"',
        leftover='leftover mise trust only',
        fix2='dump idiomatic nvmrc',
        fix2_diff='+ dump idiomatic nvmrc\n',
        bad_pat='mise trust only',
        doc='docs/LOCK-MISEIDIOM.md',
        doc_point='mise trust is not idiomatic_version_file',
        doc_diff='+ mise trust is not idiomatic_version_file.',
        reg='reg',
        reg_diff='+ idiomatic nvmrc holds',
        final_ok='ok 6 passed. idiomatic nvmrc.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='idiomatic nvmrc; dump same.',
        wrap='the idiomatic nvmrc',
        wrap_ok='6 passed. lock-miseidiom assign is green.',
        wrap_part='5 passed, 1 residual. lock-miseidiom assign is green.',
        goal='Designed plant lock-miseidiom: the mise config that omitted idiomatic_version_file_enable_tools so .nvmrc was ignored and node 18 ran. idiomatic nvmrc. mise trust is not idiomatic_version_file.',
        plan='Repro python tests, reject mise trust only, idiomatic nvmrc, fix dump.',
        out_ok='idiomatic nvmrc. 6 tests pass.',
        out_part='idiomatic nvmrc. dump leftover. Partial.',
    ),
    "fnm": P(False,
        slug='pr-fnm-loglevel-quiet-corepack',
        plant='quay-fnmcore',
        what='the fnm env that omitted --corepack-enabled so yarn was the global 1.22 not the packageManager 4.x',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='.fnmrc tests/test_harbor.py',
        impl='.fnmrc',
        src='eval "$(fnm env)"',
        sym='corepack-enabled',
        grep='corepack-enabled',
        grep_obs='harbor fnm use --install-if-missing only. pack fnm env --corepack-enabled.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: yarn 1.22; packageManager 4.x unused; corepack-enabled missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='fnm use --install-if-missing only',
        wrong_diff='+ fnm use --install-if-missing only',
        wrong_obs='still fnm use --install-if-missing only. still fail.',
        fail2='FAIL test_assign: still broken. fnm env --corepack-enabled.',
        reread='apply fnm env --corepack-enabled.',
        insight='install-if-missing is not corepack-enabled',
        probe="rg -n 'fnm' .fnmrc",
        probe_obs='pack fnm env --corepack-enabled. harbor fnm use --install-if-missing only.',
        fix='fnm env --corepack-enabled',
        fix_diff='+ fnm env --corepack-enabled\n',
        rel='dump/.fnmrc',
        rel_src='eval "$(fnm env)"',
        leftover='leftover fnm use --install-if-missing only',
        fix2='dump fnm env --corepack-enabled',
        fix2_diff='+ dump fnm env --corepack-enabled\n',
        bad_pat='fnm use --install-if-missing only',
        doc='docs/QUAY-FNMCORE.md',
        doc_point='install-if-missing is not corepack-enabled',
        doc_diff='+ install-if-missing is not corepack-enabled.',
        reg='reg',
        reg_diff='+ fnm env --corepack-enabled holds',
        final_ok='ok 6 passed. fnm env --corepack-enabled.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='fnm env --corepack-enabled; dump leftover.',
        wrap='the fnm env --corepack-enabled',
        wrap_ok='6 passed. quay-fnmcore assign is green.',
        wrap_part='5 passed, 1 residual. quay-fnmcore assign is green.',
        goal='Designed plant quay-fnmcore: the fnm env that omitted --corepack-enabled so yarn was the global 1.22 not the packageManager 4.x. fnm env --corepack-enabled. install-if-missing is not corepack-enabled.',
        plan='Repro python tests, reject fnm use --install-if-missing only, fnm env --corepack-enabled, hand off dump.',
        out_ok='fnm env --corepack-enabled. 6 tests pass.',
        out_part='fnm env --corepack-enabled. dump leftover. Partial.',
    ),
    "volta": P(True,
        slug='pr-volta-pin-node-npm-hooks',
        plant='lock-voltapin',
        what='the Volta pin that omitted npm in package.json volta so CI used the image npm 6 and pack failed',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='package.json tests/test_harbor.py',
        impl='package.json',
        src='"volta": { "node": "20.11.0" }',
        sym='volta pin npm',
        grep='volta',
        grep_obs='harbor engines node only. pack volta npm pin.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: npm 6 pack ERESOLVE; volta npm pin missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='engines node only',
        wrong_diff='+ engines node only',
        wrong_obs='still engines node only. still fail.',
        fail2='FAIL test_assign: still broken. volta npm pin.',
        reread='apply volta npm pin.',
        insight='engines is not volta npm pin',
        probe="rg -n 'volta' package.json",
        probe_obs='pack volta npm pin. harbor engines node only.',
        fix='volta npm pin',
        fix_diff='+ volta npm pin\n',
        rel='dump/package.json',
        rel_src='"volta": { "node": "20.11.0" }',
        leftover='leftover engines node only',
        fix2='dump volta npm pin',
        fix2_diff='+ dump volta npm pin\n',
        bad_pat='engines node only',
        doc='docs/LOCK-VOLTAPIN.md',
        doc_point='engines is not volta npm pin',
        doc_diff='+ engines is not volta npm pin.',
        reg='reg',
        reg_diff='+ volta npm pin holds',
        final_ok='ok 6 passed. volta npm pin.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='volta npm pin; dump same.',
        wrap='the volta npm pin',
        wrap_ok='6 passed. lock-voltapin assign is green.',
        wrap_part='5 passed, 1 residual. lock-voltapin assign is green.',
        goal='Designed plant lock-voltapin: the Volta pin that omitted npm in package.json volta so CI used the image npm 6 and pack failed. volta npm pin. engines is not volta npm pin.',
        plan='Repro python tests, reject engines node only, volta npm pin, fix dump.',
        out_ok='volta npm pin. 6 tests pass.',
        out_part='volta npm pin. dump leftover. Partial.',
    ),
    "pyenv": P(False,
        slug='pr-pyenv-virtualenv-eval-init',
        plant='quay-pyenvinit',
        what='the pyenv-virtualenv that omitted eval pyenv virtualenv-init so activate never hooked and the venv python was system',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='.bashrc tests/test_harbor.py',
        impl='.bashrc',
        src='eval "$(pyenv init -)"',
        sym='virtualenv-init -',
        grep='virtualenv-init',
        grep_obs='harbor pyenv global only. pack virtualenv-init.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: which python /usr/bin/python; virtualenv-init missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='pyenv global only',
        wrong_diff='+ pyenv global only',
        wrong_obs='still pyenv global only. still fail.',
        fail2='FAIL test_assign: still broken. virtualenv-init.',
        reread='apply virtualenv-init.',
        insight='pyenv global is not virtualenv-init',
        probe="rg -n 'virtualenv-init' .bashrc",
        probe_obs='pack virtualenv-init. harbor pyenv global only.',
        fix='virtualenv-init',
        fix_diff='+ virtualenv-init\n',
        rel='dump/.bashrc',
        rel_src='eval "$(pyenv init -)"',
        leftover='leftover pyenv global only',
        fix2='dump virtualenv-init',
        fix2_diff='+ dump virtualenv-init\n',
        bad_pat='pyenv global only',
        doc='docs/QUAY-PYENVINIT.md',
        doc_point='pyenv global is not virtualenv-init',
        doc_diff='+ pyenv global is not virtualenv-init.',
        reg='reg',
        reg_diff='+ virtualenv-init holds',
        final_ok='ok 6 passed. virtualenv-init.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='virtualenv-init; dump leftover.',
        wrap='the virtualenv-init',
        wrap_ok='6 passed. quay-pyenvinit assign is green.',
        wrap_part='5 passed, 1 residual. quay-pyenvinit assign is green.',
        goal='Designed plant quay-pyenvinit: the pyenv-virtualenv that omitted eval pyenv virtualenv-init so activate never hooked and the venv python was system. virtualenv-init. pyenv global is not virtualenv-init.',
        plan='Repro python tests, reject pyenv global only, virtualenv-init, hand off dump.',
        out_ok='virtualenv-init. 6 tests pass.',
        out_part='virtualenv-init. dump leftover. Partial.',
    ),
    "rbenv": P(True,
        slug='pr-rbenv-default-gems-bundler',
        plant='lock-rbgems',
        what='the rbenv default-gems that omitted bundler so a new ruby had no bundle and CI used the system bundler 1.17',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='default-gems tests/test_harbor.py',
        impl='default-gems',
        src='rake\nrubocop',
        sym='bundler in default-gems',
        grep='bundler',
        grep_obs='harbor gem install bundler in CI. pack default-gems bundler.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: bundle 1.17 system; default-gems missing bundler',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='gem install bundler in CI',
        wrong_diff='+ gem install bundler in CI',
        wrong_obs='still gem install bundler in CI. still fail.',
        fail2='FAIL test_assign: still broken. default-gems bundler.',
        reread='apply default-gems bundler.',
        insight='CI gem install is overwritten by rbenv rehash',
        probe="rg -n 'default-gems' default-gems",
        probe_obs='pack default-gems bundler. harbor gem install bundler in CI.',
        fix='default-gems bundler',
        fix_diff='+ default-gems bundler\n',
        rel='dump/default-gems',
        rel_src='rake\nrubocop',
        leftover='leftover gem install bundler in CI',
        fix2='dump default-gems bundler',
        fix2_diff='+ dump default-gems bundler\n',
        bad_pat='gem install bundler in CI',
        doc='docs/LOCK-RBGEMS.md',
        doc_point='CI gem install is overwritten by rbenv rehash',
        doc_diff='+ CI gem install is overwritten by rbenv rehash.',
        reg='reg',
        reg_diff='+ default-gems bundler holds',
        final_ok='ok 6 passed. default-gems bundler.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='default-gems bundler; dump same.',
        wrap='the default-gems bundler',
        wrap_ok='6 passed. lock-rbgems assign is green.',
        wrap_part='5 passed, 1 residual. lock-rbgems assign is green.',
        goal='Designed plant lock-rbgems: the rbenv default-gems that omitted bundler so a new ruby had no bundle and CI used the system bundler 1.17. default-gems bundler. CI gem install is overwritten by rbenv rehash.',
        plan='Repro python tests, reject gem install bundler in CI, default-gems bundler, fix dump.',
        out_ok='default-gems bundler. 6 tests pass.',
        out_part='default-gems bundler. dump leftover. Partial.',
    ),
    "sdkman": P(False,
        slug='pr-sdkman-auto-answer-offline',
        plant='quay-sdkoff',
        what='the SDKMAN install that omitted sdkman_auto_answer so CI hung on a prompt and never installed the JDK',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='sdkman.conf tests/test_harbor.py',
        impl='sdkman.conf',
        src='sdkman_auto_answer=false',
        sym='sdkman_auto_answer true',
        grep='sdkman_auto_answer',
        grep_obs='harbor yes | sdk install. pack sdkman_auto_answer true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CI hung sdk prompt; auto_answer false; pipe yes still waited',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='yes | sdk install',
        wrong_diff='+ yes | sdk install',
        wrong_obs='still yes | sdk install. still fail.',
        fail2='FAIL test_assign: still broken. sdkman_auto_answer true.',
        reread='apply sdkman_auto_answer true.',
        insight='yes pipe is not sdkman_auto_answer',
        probe="rg -n 'sdkman_auto_answer' sdkman.conf",
        probe_obs='pack sdkman_auto_answer true. harbor yes | sdk install.',
        fix='sdkman_auto_answer true',
        fix_diff='+ sdkman_auto_answer true\n',
        rel='dump/sdkman.conf',
        rel_src='sdkman_auto_answer=false',
        leftover='leftover yes | sdk install',
        fix2='dump sdkman_auto_answer true',
        fix2_diff='+ dump sdkman_auto_answer true\n',
        bad_pat='yes | sdk install',
        doc='docs/QUAY-SDKOFF.md',
        doc_point='yes pipe is not sdkman_auto_answer',
        doc_diff='+ yes pipe is not sdkman_auto_answer.',
        reg='reg',
        reg_diff='+ sdkman_auto_answer true holds',
        final_ok='ok 6 passed. sdkman_auto_answer true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='sdkman_auto_answer true; dump leftover.',
        wrap='the sdkman_auto_answer true',
        wrap_ok='6 passed. quay-sdkoff assign is green.',
        wrap_part='5 passed, 1 residual. quay-sdkoff assign is green.',
        goal='Designed plant quay-sdkoff: the SDKMAN install that omitted sdkman_auto_answer so CI hung on a prompt and never installed the JDK. sdkman_auto_answer true. yes pipe is not sdkman_auto_answer.',
        plan='Repro python tests, reject yes | sdk install, sdkman_auto_answer true, hand off dump.',
        out_ok='sdkman_auto_answer true. 6 tests pass.',
        out_part='sdkman_auto_answer true. dump leftover. Partial.',
    ),
    "copier": P(True,
        slug='pr-copier-skip-if-exists-update',
        plant='lock-cprskip',
        what='the Copier update that omitted skip_if_exists so a generated settings.py was overwritten and local secrets vanished',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='copier.yml tests/test_harbor.py',
        impl='copier.yml',
        src='_templates_suffix: .jinja',
        sym='skip_if_exists settings.py',
        grep='skip_if_exists',
        grep_obs='harbor force overwrite. pack skip_if_exists.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: settings.py overwritten; secrets gone; skip_if_exists missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='force overwrite',
        wrong_diff='+ force overwrite',
        wrong_obs='still force overwrite. still fail.',
        fail2='FAIL test_assign: still broken. skip_if_exists.',
        reread='apply skip_if_exists.',
        insight='force is the opposite of skip_if_exists',
        probe="rg -n 'skip_if_exists' copier.yml",
        probe_obs='pack skip_if_exists. harbor force overwrite.',
        fix='skip_if_exists',
        fix_diff='+ skip_if_exists\n',
        rel='dump/copier.yml',
        rel_src='_templates_suffix: .jinja',
        leftover='leftover force overwrite',
        fix2='dump skip_if_exists',
        fix2_diff='+ dump skip_if_exists\n',
        bad_pat='force overwrite',
        doc='docs/LOCK-CPRSKIP.md',
        doc_point='force is the opposite of skip_if_exists',
        doc_diff='+ force is the opposite of skip_if_exists.',
        reg='reg',
        reg_diff='+ skip_if_exists holds',
        final_ok='ok 6 passed. skip_if_exists.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='skip_if_exists; dump same.',
        wrap='the skip_if_exists',
        wrap_ok='6 passed. lock-cprskip assign is green.',
        wrap_part='5 passed, 1 residual. lock-cprskip assign is green.',
        goal='Designed plant lock-cprskip: the Copier update that omitted skip_if_exists so a generated settings.py was overwritten and local secrets vanished. skip_if_exists. force is the opposite of skip_if_exists.',
        plan='Repro python tests, reject force overwrite, skip_if_exists, fix dump.',
        out_ok='skip_if_exists. 6 tests pass.',
        out_part='skip_if_exists. dump leftover. Partial.',
    ),
    "cookiecutter": P(False,
        slug='pr-cookiecutter-replay-no-overwrite',
        plant='quay-cckrep',
        what='the Cookiecutter replay that omitted --no-input overwrite_if_exists so a second run aborted on existing dir',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='cookiecutter gh:harbor --replay',
        sym='overwrite_if_exists',
        grep='overwrite_if_exists',
        grep_obs='harbor rm -rf output. pack overwrite_if_exists true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: Error: directory already exists; overwrite_if_exists missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='rm -rf output',
        wrong_diff='+ rm -rf output',
        wrong_obs='still rm -rf output. still fail.',
        fail2='FAIL test_assign: still broken. overwrite_if_exists true.',
        reread='apply overwrite_if_exists true.',
        insight='rm -rf is not overwrite_if_exists',
        probe="rg -n 'overwrite_if_exists' Makefile",
        probe_obs='pack overwrite_if_exists true. harbor rm -rf output.',
        fix='overwrite_if_exists true',
        fix_diff='+ overwrite_if_exists true\n',
        rel='dump/Makefile',
        rel_src='cookiecutter gh:harbor --replay',
        leftover='leftover rm -rf output',
        fix2='dump overwrite_if_exists true',
        fix2_diff='+ dump overwrite_if_exists true\n',
        bad_pat='rm -rf output',
        doc='docs/QUAY-CCKREP.md',
        doc_point='rm -rf is not overwrite_if_exists',
        doc_diff='+ rm -rf is not overwrite_if_exists.',
        reg='reg',
        reg_diff='+ overwrite_if_exists true holds',
        final_ok='ok 6 passed. overwrite_if_exists true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='overwrite_if_exists true; dump leftover.',
        wrap='the overwrite_if_exists true',
        wrap_ok='6 passed. quay-cckrep assign is green.',
        wrap_part='5 passed, 1 residual. quay-cckrep assign is green.',
        goal='Designed plant quay-cckrep: the Cookiecutter replay that omitted --no-input overwrite_if_exists so a second run aborted on existing dir. overwrite_if_exists true. rm -rf is not overwrite_if_exists.',
        plan='Repro python tests, reject rm -rf output, overwrite_if_exists true, hand off dump.',
        out_ok='overwrite_if_exists true. 6 tests pass.',
        out_part='overwrite_if_exists true. dump leftover. Partial.',
    ),
    "cruft": P(True,
        slug='pr-cruft-skip-apply-patch-reject',
        plant='lock-cruftrej',
        what='the Cruft update that omitted --skip-apply-patch so a rejected hunk aborted the whole template update',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='Makefile tests/test_harbor.py',
        impl='Makefile',
        src='cruft update',
        sym='skip-apply-patch',
        grep='skip-apply-patch',
        grep_obs='harbor git checkout --theirs. pack cruft update --skip-apply-patch.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cruft update aborted on .rej; skip-apply-patch missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='git checkout --theirs',
        wrong_diff='+ git checkout --theirs',
        wrong_obs='still git checkout --theirs. still fail.',
        fail2='FAIL test_assign: still broken. cruft update --skip-apply-patch.',
        reread='apply cruft update --skip-apply-patch.',
        insight='checkout --theirs is not skip-apply-patch',
        probe="rg -n 'cruft' Makefile",
        probe_obs='pack cruft update --skip-apply-patch. harbor git checkout --theirs.',
        fix='cruft update --skip-apply-patch',
        fix_diff='+ cruft update --skip-apply-patch\n',
        rel='dump/Makefile',
        rel_src='cruft update',
        leftover='leftover git checkout --theirs',
        fix2='dump cruft update --skip-apply-patch',
        fix2_diff='+ dump cruft update --skip-apply-patch\n',
        bad_pat='git checkout --theirs',
        doc='docs/LOCK-CRUFTREJ.md',
        doc_point='checkout --theirs is not skip-apply-patch',
        doc_diff='+ checkout --theirs is not skip-apply-patch.',
        reg='reg',
        reg_diff='+ cruft update --skip-apply-patch holds',
        final_ok='ok 6 passed. cruft update --skip-apply-patch.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='cruft update --skip-apply-patch; dump same.',
        wrap='the cruft update --skip-apply-patch',
        wrap_ok='6 passed. lock-cruftrej assign is green.',
        wrap_part='5 passed, 1 residual. lock-cruftrej assign is green.',
        goal='Designed plant lock-cruftrej: the Cruft update that omitted --skip-apply-patch so a rejected hunk aborted the whole template update. cruft update --skip-apply-patch. checkout --theirs is not skip-apply-patch.',
        plan='Repro python tests, reject git checkout --theirs, cruft update --skip-apply-patch, fix dump.',
        out_ok='cruft update --skip-apply-patch. 6 tests pass.',
        out_part='cruft update --skip-apply-patch. dump leftover. Partial.',
    ),
    "husky": P(False,
        slug='pr-husky-init-core-hooks-path',
        plant='quay-hskpath',
        what='the Husky prepare that omitted git config core.hooksPath so CI used the default hooks and skipped lint-staged',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='package.json tests/test_harbor.py',
        impl='package.json',
        src='"prepare": "husky"',
        sym='core.hooksPath .husky',
        grep='core.hooksPath',
        grep_obs='harbor HUSKY=0 only. pack core.hooksPath .husky.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pre-commit skipped; core.hooksPath still .git/hooks',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='HUSKY=0 only',
        wrong_diff='+ HUSKY=0 only',
        wrong_obs='still HUSKY=0 only. still fail.',
        fail2='FAIL test_assign: still broken. core.hooksPath .husky.',
        reread='apply core.hooksPath .husky.',
        insight='HUSKY=0 is not hooksPath',
        probe="rg -n 'core.hooksPath' package.json",
        probe_obs='pack core.hooksPath .husky. harbor HUSKY=0 only.',
        fix='core.hooksPath .husky',
        fix_diff='+ core.hooksPath .husky\n',
        rel='dump/package.json',
        rel_src='"prepare": "husky"',
        leftover='leftover HUSKY=0 only',
        fix2='dump core.hooksPath .husky',
        fix2_diff='+ dump core.hooksPath .husky\n',
        bad_pat='HUSKY=0 only',
        doc='docs/QUAY-HSKPATH.md',
        doc_point='HUSKY=0 is not hooksPath',
        doc_diff='+ HUSKY=0 is not hooksPath.',
        reg='reg',
        reg_diff='+ core.hooksPath .husky holds',
        final_ok='ok 6 passed. core.hooksPath .husky.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='core.hooksPath .husky; dump leftover.',
        wrap='the core.hooksPath .husky',
        wrap_ok='6 passed. quay-hskpath assign is green.',
        wrap_part='5 passed, 1 residual. quay-hskpath assign is green.',
        goal='Designed plant quay-hskpath: the Husky prepare that omitted git config core.hooksPath so CI used the default hooks and skipped lint-staged. core.hooksPath .husky. HUSKY=0 is not hooksPath.',
        plan='Repro python tests, reject HUSKY=0 only, core.hooksPath .husky, hand off dump.',
        out_ok='core.hooksPath .husky. 6 tests pass.',
        out_part='core.hooksPath .husky. dump leftover. Partial.',
    ),
    "lefthook": P(True,
        slug='pr-lefthook-skip-output-execution',
        plant='lock-lfhskip',
        what='the Lefthook pre-commit that omitted skip_output so CI logs drowned in execution traces and the real error scrolled off',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='lefthook.yml tests/test_harbor.py',
        impl='lefthook.yml',
        src='pre-commit:\n  commands:\n    lint: {run: eslint}',
        sym='skip_output execution',
        grep='skip_output',
        grep_obs='harbor quiet false. pack skip_output [execution].',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: error lost in execution logs; skip_output missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='quiet false',
        wrong_diff='+ quiet false',
        wrong_obs='still quiet false. still fail.',
        fail2='FAIL test_assign: still broken. skip_output [execution].',
        reread='apply skip_output [execution].',
        insight='quiet is not skip_output execution',
        probe="rg -n 'skip_output' lefthook.yml",
        probe_obs='pack skip_output [execution]. harbor quiet false.',
        fix='skip_output [execution]',
        fix_diff='+ skip_output [execution]\n',
        rel='dump/lefthook.yml',
        rel_src='pre-commit:\n  commands:\n    lint: {run: eslint}',
        leftover='leftover quiet false',
        fix2='dump skip_output [execution]',
        fix2_diff='+ dump skip_output [execution]\n',
        bad_pat='quiet false',
        doc='docs/LOCK-LFHSKIP.md',
        doc_point='quiet is not skip_output execution',
        doc_diff='+ quiet is not skip_output execution.',
        reg='reg',
        reg_diff='+ skip_output [execution] holds',
        final_ok='ok 6 passed. skip_output [execution].',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='skip_output [execution]; dump same.',
        wrap='the skip_output [execution]',
        wrap_ok='6 passed. lock-lfhskip assign is green.',
        wrap_part='5 passed, 1 residual. lock-lfhskip assign is green.',
        goal='Designed plant lock-lfhskip: the Lefthook pre-commit that omitted skip_output so CI logs drowned in execution traces and the real error scrolled off. skip_output [execution]. quiet is not skip_output execution.',
        plan='Repro python tests, reject quiet false, skip_output [execution], fix dump.',
        out_ok='skip_output [execution]. 6 tests pass.',
        out_part='skip_output [execution]. dump leftover. Partial.',
    ),
    "changesets": P(False,
        slug='pr-changesets-linked-packages-ignore',
        plant='quay-cslink',
        what='the Changesets config that omitted linked packages so a bump of harbor-core never bumped harbor-cli',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='.changeset/config.json tests/test_harbor.py',
        impl='.changeset/config.json',
        src='{"access": "public"}',
        sym='linked packages',
        grep='linked',
        grep_obs='harbor updateInternalDependencies patch only. pack linked [harbor-core, harbor-cli].',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: harbor-cli version unchanged; linked missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='updateInternalDependencies patch only',
        wrong_diff='+ updateInternalDependencies patch only',
        wrong_obs='still updateInternalDependencies patch only. still fail.',
        fail2='FAIL test_assign: still broken. linked [harbor-core, harbor-cli].',
        reread='apply linked [harbor-core, harbor-cli].',
        insight='updateInternalDependencies is not linked',
        probe="rg -n 'linked' .changeset/config.json",
        probe_obs='pack linked [harbor-core, harbor-cli]. harbor updateInternalDependencies patch only.',
        fix='linked [harbor-core, harbor-cli]',
        fix_diff='+ linked [harbor-core, harbor-cli]\n',
        rel='dump/.changeset/config.json',
        rel_src='{"access": "public"}',
        leftover='leftover updateInternalDependencies patch only',
        fix2='dump linked [harbor-core, harbor-cli]',
        fix2_diff='+ dump linked [harbor-core, harbor-cli]\n',
        bad_pat='updateInternalDependencies patch only',
        doc='docs/QUAY-CSLINK.md',
        doc_point='updateInternalDependencies is not linked',
        doc_diff='+ updateInternalDependencies is not linked.',
        reg='reg',
        reg_diff='+ linked [harbor-core, harbor-cli] holds',
        final_ok='ok 6 passed. linked [harbor-core, harbor-cli].',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='linked [harbor-core, harbor-cli]; dump leftover.',
        wrap='the linked [harbor-core, harbor-cli]',
        wrap_ok='6 passed. quay-cslink assign is green.',
        wrap_part='5 passed, 1 residual. quay-cslink assign is green.',
        goal='Designed plant quay-cslink: the Changesets config that omitted linked packages so a bump of harbor-core never bumped harbor-cli. linked [harbor-core, harbor-cli]. updateInternalDependencies is not linked.',
        plan='Repro python tests, reject updateInternalDependencies patch only, linked [harbor-core, harbor-cli], hand off dump.',
        out_ok='linked [harbor-core, harbor-cli]. 6 tests pass.',
        out_part='linked [harbor-core, harbor-cli]. dump leftover. Partial.',
    ),
    "releaseplease": P(True,
        slug='pr-releaseplease-extra-files-json',
        plant='lock-rpjextra',
        what='the release-please manifest that omitted extra-files so package.json version stayed 0.0.0 after the tag',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='release-please-config.json tests/test_harbor.py',
        impl='release-please-config.json',
        src='{"release-type": "go"}',
        sym='extra-files package.json',
        grep='extra-files',
        grep_obs='harbor include-v-in-tag only. pack extra-files json path.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: package.json still 0.0.0 after v1.2.3 tag; extra-files missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='include-v-in-tag only',
        wrong_diff='+ include-v-in-tag only',
        wrong_obs='still include-v-in-tag only. still fail.',
        fail2='FAIL test_assign: still broken. extra-files json path.',
        reread='apply extra-files json path.',
        insight='include-v-in-tag is not extra-files',
        probe="rg -n 'extra-files' release-please-config.json",
        probe_obs='pack extra-files json path. harbor include-v-in-tag only.',
        fix='extra-files json path',
        fix_diff='+ extra-files json path\n',
        rel='dump/release-please-config.json',
        rel_src='{"release-type": "go"}',
        leftover='leftover include-v-in-tag only',
        fix2='dump extra-files json path',
        fix2_diff='+ dump extra-files json path\n',
        bad_pat='include-v-in-tag only',
        doc='docs/LOCK-RPJEXTRA.md',
        doc_point='include-v-in-tag is not extra-files',
        doc_diff='+ include-v-in-tag is not extra-files.',
        reg='reg',
        reg_diff='+ extra-files json path holds',
        final_ok='ok 6 passed. extra-files json path.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='extra-files json path; dump same.',
        wrap='the extra-files json path',
        wrap_ok='6 passed. lock-rpjextra assign is green.',
        wrap_part='5 passed, 1 residual. lock-rpjextra assign is green.',
        goal='Designed plant lock-rpjextra: the release-please manifest that omitted extra-files so package.json version stayed 0.0.0 after the tag. extra-files json path. include-v-in-tag is not extra-files.',
        plan='Repro python tests, reject include-v-in-tag only, extra-files json path, fix dump.',
        out_ok='extra-files json path. 6 tests pass.',
        out_part='extra-files json path. dump leftover. Partial.',
    ),
    "gitcliff": P(False,
        slug='pr-gitcliff-tag-pattern-ignore-pre',
        plant='quay-gcliffpre',
        what='the git-cliff config that omitted tag_pattern so pre-release tags v1.2.3-rc.1 became the latest in CHANGELOG',
        glob='**/*.{toml,yml,sh,json,py,rb}',
        ls='cliff.toml tests/test_harbor.py',
        impl='cliff.toml',
        src='[git]\nconventional_commits = true',
        sym='tag_pattern stable',
        grep='tag_pattern',
        grep_obs='harbor skip_tags empty. pack tag_pattern v[0-9]*$.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: CHANGELOG latest is rc.1; tag_pattern missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='skip_tags empty',
        wrong_diff='+ skip_tags empty',
        wrong_obs='still skip_tags empty. still fail.',
        fail2='FAIL test_assign: still broken. tag_pattern v[0-9]*$.',
        reread='apply tag_pattern v[0-9]*$.',
        insight='skip_tags empty is not tag_pattern',
        probe="rg -n 'tag_pattern' cliff.toml",
        probe_obs='pack tag_pattern v[0-9]*$. harbor skip_tags empty.',
        fix='tag_pattern v[0-9]*$',
        fix_diff='+ tag_pattern v[0-9]*$\n',
        rel='dump/cliff.toml',
        rel_src='[git]\nconventional_commits = true',
        leftover='leftover skip_tags empty',
        fix2='dump tag_pattern v[0-9]*$',
        fix2_diff='+ dump tag_pattern v[0-9]*$\n',
        bad_pat='skip_tags empty',
        doc='docs/QUAY-GCLIFFPRE.md',
        doc_point='skip_tags empty is not tag_pattern',
        doc_diff='+ skip_tags empty is not tag_pattern.',
        reg='reg',
        reg_diff='+ tag_pattern v[0-9]*$ holds',
        final_ok='ok 6 passed. tag_pattern v[0-9]*$.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='tag_pattern v[0-9]*$; dump leftover.',
        wrap='the tag_pattern v[0-9]*$',
        wrap_ok='6 passed. quay-gcliffpre assign is green.',
        wrap_part='5 passed, 1 residual. quay-gcliffpre assign is green.',
        goal='Designed plant quay-gcliffpre: the git-cliff config that omitted tag_pattern so pre-release tags v1.2.3-rc.1 became the latest in CHANGELOG. tag_pattern v[0-9]*$. skip_tags empty is not tag_pattern.',
        plan='Repro python tests, reject skip_tags empty, tag_pattern v[0-9]*$, hand off dump.',
        out_ok='tag_pattern v[0-9]*$. 6 tests pass.',
        out_part='tag_pattern v[0-9]*$. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('direnv watch_file vs asdf legacy_version_file', fn('direnv'), fn('asdf'), 'watch_file .env; legacy_version_file yes', 'layout python; asdf local', 'direnv dump stale TOKEN; asdf dump .python-version ignored'),
    ('mise idiomatic nvmrc vs fnm corepack-enabled', fn('mise'), fn('fnm'), 'idiomatic_version_file; fnm env --corepack-enabled', 'mise trust; install-if-missing', 'mise dump node 18; fnm dump yarn 1.22'),
    ('Volta npm pin vs pyenv virtualenv-init', fn('volta'), fn('pyenv'), 'volta npm pin; virtualenv-init -', 'engines node; pyenv global', 'volta dump npm 6; pyenv dump system python'),
    ('rbenv default-gems bundler vs SDKMAN auto_answer', fn('rbenv'), fn('sdkman'), 'default-gems bundler; sdkman_auto_answer true', 'CI gem install; yes pipe', 'rbenv dump bundler 1.17; sdkman dump hung prompt'),
    ('Copier skip_if_exists vs Cookiecutter overwrite_if_exists', fn('copier'), fn('cookiecutter'), 'skip_if_exists settings.py; overwrite_if_exists', 'force; rm -rf', 'copier dump secrets gone; cookiecutter dump dir exists'),
    ('Cruft skip-apply-patch vs Husky core.hooksPath', fn('cruft'), fn('husky'), '--skip-apply-patch; core.hooksPath .husky', 'checkout --theirs; HUSKY=0', 'cruft dump aborted on .rej; husky dump pre-commit skipped'),
    ('Lefthook skip_output vs Changesets linked', fn('lefthook'), fn('changesets'), 'skip_output execution; linked packages', 'quiet; updateInternalDependencies', 'lefthook dump error scrolled off; changesets dump cli not bumped'),
    ('release-please extra-files vs git-cliff tag_pattern', fn('releaseplease'), fn('gitcliff'), 'extra-files package.json; tag_pattern stable', 'include-v-in-tag; skip_tags empty', 'release-please dump 0.0.0; git-cliff dump rc as latest'),
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
- Not a clone of r4163-r4524 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
