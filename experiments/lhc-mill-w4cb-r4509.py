#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cb: unused plants after r4508.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4508. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cb_state.json")
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
    "homebrew": P(True,
        slug='pr-homebrew-bottle-rebuild-cellar',
        plant='lock-hbbottle',
        what='the Homebrew formula that omitted cellar :any_skip_relocation so the bottle had a hardcoded Cellar path',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='harbor.rb tests/test_harbor.py',
        impl='harbor.rb',
        src='class Harbor < Formula\n  url "https://example/harbor.tgz"\nend',
        sym='cellar any_skip_relocation',
        grep='cellar',
        grep_obs='harbor pour_bottle only. pack cellar any_skip_relocation.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: bottle rpath /usr/local/Cellar; missing cellar :any_skip_relocation',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='pour_bottle only',
        wrong_diff='+ pour_bottle only',
        wrong_obs='still pour_bottle only. still fail.',
        fail2='FAIL test_assign: still broken. cellar any_skip_relocation.',
        reread='apply cellar any_skip_relocation.',
        insight='pour_bottle is not skip_relocation',
        probe="rg -n 'cellar' harbor.rb",
        probe_obs='pack cellar any_skip_relocation. harbor pour_bottle only.',
        fix='cellar any_skip_relocation',
        fix_diff='+ cellar any_skip_relocation\n',
        rel='dump/harbor.rb',
        rel_src='class Harbor < Formula\n  url "https://example/harbor.tgz"\nend',
        leftover='leftover pour_bottle only',
        fix2='dump cellar any_skip_relocation',
        fix2_diff='+ dump cellar any_skip_relocation\n',
        bad_pat='pour_bottle only',
        doc='docs/LOCK-HBBOTTLE.md',
        doc_point='pour_bottle is not skip_relocation',
        doc_diff='+ pour_bottle is not skip_relocation.',
        reg='reg',
        reg_diff='+ cellar any_skip_relocation holds',
        final_ok='ok 6 passed. cellar any_skip_relocation.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='cellar any_skip_relocation; dump same.',
        wrap='the cellar any_skip_relocation',
        wrap_ok='6 passed. lock-hbbottle assign is green.',
        wrap_part='5 passed, 1 residual. lock-hbbottle assign is green.',
        goal='Designed plant lock-hbbottle: the Homebrew formula that omitted cellar :any_skip_relocation so the bottle had a hardcoded Cellar path. cellar any_skip_relocation. pour_bottle is not skip_relocation.',
        plan='Repro python tests, reject pour_bottle only, cellar any_skip_relocation, fix dump.',
        out_ok='cellar any_skip_relocation. 6 tests pass.',
        out_part='cellar any_skip_relocation. dump leftover. Partial.',
    ),
    "macports": P(False,
        slug='pr-macports-universal-merge-lipo',
        plant='quay-mplipo',
        what='the MacPorts Portfile that omitted universal_setup so the arm64 bottle lacked x86_64 slices',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='Portfile tests/test_harbor.py',
        impl='Portfile',
        src='name harbor\nversion 1.0',
        sym='universal_setup',
        grep='universal_setup',
        grep_obs='harbor build.jobs 1. pack universal_setup lipo.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: file: Mach-O arm64 only; universal_setup missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='build.jobs 1',
        wrong_diff='+ build.jobs 1',
        wrong_obs='still build.jobs 1. still fail.',
        fail2='FAIL test_assign: still broken. universal_setup lipo.',
        reread='apply universal_setup lipo.',
        insight='build.jobs is not universal_setup',
        probe="rg -n 'universal_setup' Portfile",
        probe_obs='pack universal_setup lipo. harbor build.jobs 1.',
        fix='universal_setup lipo',
        fix_diff='+ universal_setup lipo\n',
        rel='dump/Portfile',
        rel_src='name harbor\nversion 1.0',
        leftover='leftover build.jobs 1',
        fix2='dump universal_setup lipo',
        fix2_diff='+ dump universal_setup lipo\n',
        bad_pat='build.jobs 1',
        doc='docs/QUAY-MPLIPO.md',
        doc_point='build.jobs is not universal_setup',
        doc_diff='+ build.jobs is not universal_setup.',
        reg='reg',
        reg_diff='+ universal_setup lipo holds',
        final_ok='ok 6 passed. universal_setup lipo.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='universal_setup lipo; dump leftover.',
        wrap='the universal_setup lipo',
        wrap_ok='6 passed. quay-mplipo assign is green.',
        wrap_part='5 passed, 1 residual. quay-mplipo assign is green.',
        goal='Designed plant quay-mplipo: the MacPorts Portfile that omitted universal_setup so the arm64 bottle lacked x86_64 slices. universal_setup lipo. build.jobs is not universal_setup.',
        plan='Repro python tests, reject build.jobs 1, universal_setup lipo, hand off dump.',
        out_ok='universal_setup lipo. 6 tests pass.',
        out_part='universal_setup lipo. dump leftover. Partial.',
    ),
    "portage": P(True,
        slug='pr-portage-eapi-src-prepare-eapply',
        plant='lock-pgeapply',
        what='the Portage ebuild that used EAPI 6 eapply_user only so user patches in /etc/portage/patches never applied',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='harbor-1.ebuild tests/test_harbor.py',
        impl='harbor-1.ebuild',
        src='EAPI=6\nsrc_prepare() { default; }',
        sym='EAPI 8 eapply_user',
        grep='EAPI',
        grep_obs='harbor PATCHES array only. pack EAPI 8 eapply_user.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: user patch skipped; EAPI 6 src_prepare without eapply_user',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='PATCHES array only',
        wrong_diff='+ PATCHES array only',
        wrong_obs='still PATCHES array only. still fail.',
        fail2='FAIL test_assign: still broken. EAPI 8 eapply_user.',
        reread='apply EAPI 8 eapply_user.',
        insight='PATCHES is not eapply_user',
        probe="rg -n 'EAPI' harbor-1.ebuild",
        probe_obs='pack EAPI 8 eapply_user. harbor PATCHES array only.',
        fix='EAPI 8 eapply_user',
        fix_diff='+ EAPI 8 eapply_user\n',
        rel='dump/harbor-1.ebuild',
        rel_src='EAPI=6\nsrc_prepare() { default; }',
        leftover='leftover PATCHES array only',
        fix2='dump EAPI 8 eapply_user',
        fix2_diff='+ dump EAPI 8 eapply_user\n',
        bad_pat='PATCHES array only',
        doc='docs/LOCK-PGEAPPLY.md',
        doc_point='PATCHES is not eapply_user',
        doc_diff='+ PATCHES is not eapply_user.',
        reg='reg',
        reg_diff='+ EAPI 8 eapply_user holds',
        final_ok='ok 6 passed. EAPI 8 eapply_user.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='EAPI 8 eapply_user; dump same.',
        wrap='the EAPI 8 eapply_user',
        wrap_ok='6 passed. lock-pgeapply assign is green.',
        wrap_part='5 passed, 1 residual. lock-pgeapply assign is green.',
        goal='Designed plant lock-pgeapply: the Portage ebuild that used EAPI 6 eapply_user only so user patches in /etc/portage/patches never applied. EAPI 8 eapply_user. PATCHES is not eapply_user.',
        plan='Repro python tests, reject PATCHES array only, EAPI 8 eapply_user, fix dump.',
        out_ok='EAPI 8 eapply_user. 6 tests pass.',
        out_part='EAPI 8 eapply_user. dump leftover. Partial.',
    ),
    "pkgng": P(False,
        slug='pr-pkgng-vital-noauto-leaves',
        plant='quay-pkgnvl',
        what='the pkgng package that omitted vital so pkg autoremove dropped a runtime shared lib',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='pkg-plist tests/test_harbor.py',
        impl='pkg-plist',
        src='lib/libharbor.so.1',
        sym='vital annotation',
        grep='vital',
        grep_obs='harbor pkg lock only. pack vital annotation.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pkg autoremove deleted libharbor.so; not vital',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='pkg lock only',
        wrong_diff='+ pkg lock only',
        wrong_obs='still pkg lock only. still fail.',
        fail2='FAIL test_assign: still broken. vital annotation.',
        reread='apply vital annotation.',
        insight='pkg lock is not vital',
        probe="rg -n 'vital' pkg-plist",
        probe_obs='pack vital annotation. harbor pkg lock only.',
        fix='vital annotation',
        fix_diff='+ vital annotation\n',
        rel='dump/pkg-plist',
        rel_src='lib/libharbor.so.1',
        leftover='leftover pkg lock only',
        fix2='dump vital annotation',
        fix2_diff='+ dump vital annotation\n',
        bad_pat='pkg lock only',
        doc='docs/QUAY-PKGNVL.md',
        doc_point='pkg lock is not vital',
        doc_diff='+ pkg lock is not vital.',
        reg='reg',
        reg_diff='+ vital annotation holds',
        final_ok='ok 6 passed. vital annotation.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='vital annotation; dump leftover.',
        wrap='the vital annotation',
        wrap_ok='6 passed. quay-pkgnvl assign is green.',
        wrap_part='5 passed, 1 residual. quay-pkgnvl assign is green.',
        goal='Designed plant quay-pkgnvl: the pkgng package that omitted vital so pkg autoremove dropped a runtime shared lib. vital annotation. pkg lock is not vital.',
        plan='Repro python tests, reject pkg lock only, vital annotation, hand off dump.',
        out_ok='vital annotation. 6 tests pass.',
        out_part='vital annotation. dump leftover. Partial.',
    ),
    "just": P(True,
        slug='pr-just-dotenv-filename-load',
        plant='lock-jstdot',
        what='the just recipe that omitted dotenv-filename so .env.local secrets never loaded and deploy used empty tokens',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='justfile tests/test_harbor.py',
        impl='justfile',
        src='deploy:\n  ./deploy.sh',
        sym='dotenv-filename',
        grep='dotenv-filename',
        grep_obs='harbor export just only. pack dotenv-filename .env.local.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: TOKEN empty; just did not load .env.local; dotenv-filename missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='export just only',
        wrong_diff='+ export just only',
        wrong_obs='still export just only. still fail.',
        fail2='FAIL test_assign: still broken. dotenv-filename .env.local.',
        reread='apply dotenv-filename .env.local.',
        insight='export is not dotenv-filename',
        probe="rg -n 'dotenv-filename' justfile",
        probe_obs='pack dotenv-filename .env.local. harbor export just only.',
        fix='dotenv-filename .env.local',
        fix_diff='+ dotenv-filename .env.local\n',
        rel='dump/justfile',
        rel_src='deploy:\n  ./deploy.sh',
        leftover='leftover export just only',
        fix2='dump dotenv-filename .env.local',
        fix2_diff='+ dump dotenv-filename .env.local\n',
        bad_pat='export just only',
        doc='docs/LOCK-JSTDOT.md',
        doc_point='export is not dotenv-filename',
        doc_diff='+ export is not dotenv-filename.',
        reg='reg',
        reg_diff='+ dotenv-filename .env.local holds',
        final_ok='ok 6 passed. dotenv-filename .env.local.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='dotenv-filename .env.local; dump same.',
        wrap='the dotenv-filename .env.local',
        wrap_ok='6 passed. lock-jstdot assign is green.',
        wrap_part='5 passed, 1 residual. lock-jstdot assign is green.',
        goal='Designed plant lock-jstdot: the just recipe that omitted dotenv-filename so .env.local secrets never loaded and deploy used empty tokens. dotenv-filename .env.local. export is not dotenv-filename.',
        plan='Repro python tests, reject export just only, dotenv-filename .env.local, fix dump.',
        out_ok='dotenv-filename .env.local. 6 tests pass.',
        out_part='dotenv-filename .env.local. dump leftover. Partial.',
    ),
    "taskfile": P(False,
        slug='pr-taskfile-dotenv-dir-silent',
        plant='quay-tfdot',
        what='the Taskfile that omitted dotenv: so included tasks ran without .env and S3 creds were empty',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='Taskfile.yml tests/test_harbor.py',
        impl='Taskfile.yml',
        src="version: '3'\ntasks:\n  deploy: {cmds: [./deploy.sh]}",
        sym='dotenv list',
        grep='dotenv',
        grep_obs='harbor silent: true. pack dotenv .env.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: AWS_SECRET empty; Taskfile no dotenv; included task inherited nothing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='silent: true',
        wrong_diff='+ silent: true',
        wrong_obs='still silent: true. still fail.',
        fail2='FAIL test_assign: still broken. dotenv .env.',
        reread='apply dotenv .env.',
        insight='silent is not dotenv',
        probe="rg -n 'dotenv' Taskfile.yml",
        probe_obs='pack dotenv .env. harbor silent: true.',
        fix='dotenv .env',
        fix_diff='+ dotenv .env\n',
        rel='dump/Taskfile.yml',
        rel_src="version: '3'\ntasks:\n  deploy: {cmds: [./deploy.sh]}",
        leftover='leftover silent: true',
        fix2='dump dotenv .env',
        fix2_diff='+ dump dotenv .env\n',
        bad_pat='silent: true',
        doc='docs/QUAY-TFDOT.md',
        doc_point='silent is not dotenv',
        doc_diff='+ silent is not dotenv.',
        reg='reg',
        reg_diff='+ dotenv .env holds',
        final_ok='ok 6 passed. dotenv .env.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='dotenv .env; dump leftover.',
        wrap='the dotenv .env',
        wrap_ok='6 passed. quay-tfdot assign is green.',
        wrap_part='5 passed, 1 residual. quay-tfdot assign is green.',
        goal='Designed plant quay-tfdot: the Taskfile that omitted dotenv: so included tasks ran without .env and S3 creds were empty. dotenv .env. silent is not dotenv.',
        plan='Repro python tests, reject silent: true, dotenv .env, hand off dump.',
        out_ok='dotenv .env. 6 tests pass.',
        out_part='dotenv .env. dump leftover. Partial.',
    ),
    "mage": P(True,
        slug='pr-mage-namespace-error-exit',
        plant='lock-mgns',
        what='the Mage namespace that returned nil after a failed sh.Run so CI still exited 0',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='magefile.go tests/test_harbor.py',
        impl='magefile.go',
        src='func Deploy() error { sh.Run("deploy.sh"); return nil }',
        sym='return sh.Run',
        grep='return',
        grep_obs='harbor mg.Deps only. pack return sh.Run error.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: deploy.sh failed; mage still 0; error discarded',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='mg.Deps only',
        wrong_diff='+ mg.Deps only',
        wrong_obs='still mg.Deps only. still fail.',
        fail2='FAIL test_assign: still broken. return sh.Run error.',
        reread='apply return sh.Run error.',
        insight='mg.Deps is not error return',
        probe="rg -n 'return' magefile.go",
        probe_obs='pack return sh.Run error. harbor mg.Deps only.',
        fix='return sh.Run error',
        fix_diff='+ return sh.Run error\n',
        rel='dump/magefile.go',
        rel_src='func Deploy() error { sh.Run("deploy.sh"); return nil }',
        leftover='leftover mg.Deps only',
        fix2='dump return sh.Run error',
        fix2_diff='+ dump return sh.Run error\n',
        bad_pat='mg.Deps only',
        doc='docs/LOCK-MGNS.md',
        doc_point='mg.Deps is not error return',
        doc_diff='+ mg.Deps is not error return.',
        reg='reg',
        reg_diff='+ return sh.Run error holds',
        final_ok='ok 6 passed. return sh.Run error.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='return sh.Run error; dump same.',
        wrap='the return sh.Run error',
        wrap_ok='6 passed. lock-mgns assign is green.',
        wrap_part='5 passed, 1 residual. lock-mgns assign is green.',
        goal='Designed plant lock-mgns: the Mage namespace that returned nil after a failed sh.Run so CI still exited 0. return sh.Run error. mg.Deps is not error return.',
        plan='Repro python tests, reject mg.Deps only, return sh.Run error, fix dump.',
        out_ok='return sh.Run error. 6 tests pass.',
        out_part='return sh.Run error. dump leftover. Partial.',
    ),
    "goreleaser": P(False,
        slug='pr-goreleaser-checksum-extra_files',
        plant='quay-grsum',
        what='the GoReleaser config that omitted extra_files checksums so the sbom.json was published unsigned beside the checksums.txt',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='.goreleaser.yml tests/test_harbor.py',
        impl='.goreleaser.yml',
        src='checksum:\n  name_template: checksums.txt',
        sym='extra_files checksum',
        grep='extra_files',
        grep_obs='harbor signs only binaries. pack extra_files in checksum.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: sbom.json missing from checksums.txt; extra_files omitted',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='signs only binaries',
        wrong_diff='+ signs only binaries',
        wrong_obs='still signs only binaries. still fail.',
        fail2='FAIL test_assign: still broken. extra_files in checksum.',
        reread='apply extra_files in checksum.',
        insight='binary signs is not extra_files checksum',
        probe="rg -n 'extra_files' .goreleaser.yml",
        probe_obs='pack extra_files in checksum. harbor signs only binaries.',
        fix='extra_files in checksum',
        fix_diff='+ extra_files in checksum\n',
        rel='dump/.goreleaser.yml',
        rel_src='checksum:\n  name_template: checksums.txt',
        leftover='leftover signs only binaries',
        fix2='dump extra_files in checksum',
        fix2_diff='+ dump extra_files in checksum\n',
        bad_pat='signs only binaries',
        doc='docs/QUAY-GRSUM.md',
        doc_point='binary signs is not extra_files checksum',
        doc_diff='+ binary signs is not extra_files checksum.',
        reg='reg',
        reg_diff='+ extra_files in checksum holds',
        final_ok='ok 6 passed. extra_files in checksum.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='extra_files in checksum; dump leftover.',
        wrap='the extra_files in checksum',
        wrap_ok='6 passed. quay-grsum assign is green.',
        wrap_part='5 passed, 1 residual. quay-grsum assign is green.',
        goal='Designed plant quay-grsum: the GoReleaser config that omitted extra_files checksums so the sbom.json was published unsigned beside the checksums.txt. extra_files in checksum. binary signs is not extra_files checksum.',
        plan='Repro python tests, reject signs only binaries, extra_files in checksum, hand off dump.',
        out_ok='extra_files in checksum. 6 tests pass.',
        out_part='extra_files in checksum. dump leftover. Partial.',
    ),
    "ccache": P(True,
        slug='pr-ccache-sloppiness-include-file-ctime',
        plant='lock-ccslop',
        what='the ccache config that omitted sloppiness include_file_ctime so a docker overlayfs rebuild never hashed a hit',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='ccache.conf tests/test_harbor.py',
        impl='ccache.conf',
        src='max_size = 5G',
        sym='sloppiness include_file_ctime',
        grep='sloppiness',
        grep_obs='harbor CCACHE_DIR only. pack sloppiness include_file_ctime.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: 0 hits in overlayfs; include_file_ctime mismatch; sloppiness missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='CCACHE_DIR only',
        wrong_diff='+ CCACHE_DIR only',
        wrong_obs='still CCACHE_DIR only. still fail.',
        fail2='FAIL test_assign: still broken. sloppiness include_file_ctime.',
        reread='apply sloppiness include_file_ctime.',
        insight='CCACHE_DIR is not sloppiness',
        probe="rg -n 'sloppiness' ccache.conf",
        probe_obs='pack sloppiness include_file_ctime. harbor CCACHE_DIR only.',
        fix='sloppiness include_file_ctime',
        fix_diff='+ sloppiness include_file_ctime\n',
        rel='dump/ccache.conf',
        rel_src='max_size = 5G',
        leftover='leftover CCACHE_DIR only',
        fix2='dump sloppiness include_file_ctime',
        fix2_diff='+ dump sloppiness include_file_ctime\n',
        bad_pat='CCACHE_DIR only',
        doc='docs/LOCK-CCSLOP.md',
        doc_point='CCACHE_DIR is not sloppiness',
        doc_diff='+ CCACHE_DIR is not sloppiness.',
        reg='reg',
        reg_diff='+ sloppiness include_file_ctime holds',
        final_ok='ok 6 passed. sloppiness include_file_ctime.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='sloppiness include_file_ctime; dump same.',
        wrap='the sloppiness include_file_ctime',
        wrap_ok='6 passed. lock-ccslop assign is green.',
        wrap_part='5 passed, 1 residual. lock-ccslop assign is green.',
        goal='Designed plant lock-ccslop: the ccache config that omitted sloppiness include_file_ctime so a docker overlayfs rebuild never hashed a hit. sloppiness include_file_ctime. CCACHE_DIR is not sloppiness.',
        plan='Repro python tests, reject CCACHE_DIR only, sloppiness include_file_ctime, fix dump.',
        out_ok='sloppiness include_file_ctime. 6 tests pass.',
        out_part='sloppiness include_file_ctime. dump leftover. Partial.',
    ),
    "distcc": P(False,
        slug='pr-distcc-pump-include-server',
        plant='quay-dccpump',
        what='the distcc hosts that omitted pump mode so headers were compiled locally and the farm sat idle',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='distcc/hosts tests/test_harbor.py',
        impl='distcc/hosts',
        src='host1/4 host2/4',
        sym='pump hosts',
        grep='pump',
        grep_obs='harbor DISTCC_HOSTS more cpus. pack pump include server.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: local cc 100%; farm idle; pump include server missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='DISTCC_HOSTS more cpus',
        wrong_diff='+ DISTCC_HOSTS more cpus',
        wrong_obs='still DISTCC_HOSTS more cpus. still fail.',
        fail2='FAIL test_assign: still broken. pump include server.',
        reread='apply pump include server.',
        insight='more host slots is not pump',
        probe="rg -n 'pump' distcc/hosts",
        probe_obs='pack pump include server. harbor DISTCC_HOSTS more cpus.',
        fix='pump include server',
        fix_diff='+ pump include server\n',
        rel='dump/distcc/hosts',
        rel_src='host1/4 host2/4',
        leftover='leftover DISTCC_HOSTS more cpus',
        fix2='dump pump include server',
        fix2_diff='+ dump pump include server\n',
        bad_pat='DISTCC_HOSTS more cpus',
        doc='docs/QUAY-DCCPUMP.md',
        doc_point='more host slots is not pump',
        doc_diff='+ more host slots is not pump.',
        reg='reg',
        reg_diff='+ pump include server holds',
        final_ok='ok 6 passed. pump include server.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pump include server; dump leftover.',
        wrap='the pump include server',
        wrap_ok='6 passed. quay-dccpump assign is green.',
        wrap_part='5 passed, 1 residual. quay-dccpump assign is green.',
        goal='Designed plant quay-dccpump: the distcc hosts that omitted pump mode so headers were compiled locally and the farm sat idle. pump include server. more host slots is not pump.',
        plan='Repro python tests, reject DISTCC_HOSTS more cpus, pump include server, hand off dump.',
        out_ok='pump include server. 6 tests pass.',
        out_part='pump include server. dump leftover. Partial.',
    ),
    "icecream": P(True,
        slug='pr-icecream-icecc-scheduler-netname',
        plant='lock-icenet',
        what='the Icecream daemon that omitted ICECC_NETNAME so the scheduler in another namespace never saw the daemon',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='icecc.conf tests/test_harbor.py',
        impl='icecc.conf',
        src='ICECC_SCHEDULER=scheduler.example',
        sym='ICECC_NETNAME',
        grep='ICECC_NETNAME',
        grep_obs='harbor ICECC_NICE only. pack ICECC_NETNAME harbor.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: daemon not in scheduler list; netname default vs harbor',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ICECC_NICE only',
        wrong_diff='+ ICECC_NICE only',
        wrong_obs='still ICECC_NICE only. still fail.',
        fail2='FAIL test_assign: still broken. ICECC_NETNAME harbor.',
        reread='apply ICECC_NETNAME harbor.',
        insight='nice is not netname',
        probe="rg -n 'ICECC_NETNAME' icecc.conf",
        probe_obs='pack ICECC_NETNAME harbor. harbor ICECC_NICE only.',
        fix='ICECC_NETNAME harbor',
        fix_diff='+ ICECC_NETNAME harbor\n',
        rel='dump/icecc.conf',
        rel_src='ICECC_SCHEDULER=scheduler.example',
        leftover='leftover ICECC_NICE only',
        fix2='dump ICECC_NETNAME harbor',
        fix2_diff='+ dump ICECC_NETNAME harbor\n',
        bad_pat='ICECC_NICE only',
        doc='docs/LOCK-ICENET.md',
        doc_point='nice is not netname',
        doc_diff='+ nice is not netname.',
        reg='reg',
        reg_diff='+ ICECC_NETNAME harbor holds',
        final_ok='ok 6 passed. ICECC_NETNAME harbor.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='ICECC_NETNAME harbor; dump same.',
        wrap='the ICECC_NETNAME harbor',
        wrap_ok='6 passed. lock-icenet assign is green.',
        wrap_part='5 passed, 1 residual. lock-icenet assign is green.',
        goal='Designed plant lock-icenet: the Icecream daemon that omitted ICECC_NETNAME so the scheduler in another namespace never saw the daemon. ICECC_NETNAME harbor. nice is not netname.',
        plan='Repro python tests, reject ICECC_NICE only, ICECC_NETNAME harbor, fix dump.',
        out_ok='ICECC_NETNAME harbor. 6 tests pass.',
        out_part='ICECC_NETNAME harbor. dump leftover. Partial.',
    ),
    "gold": P(False,
        slug='pr-gold-gdb-index-threads',
        plant='quay-gldidx',
        what='the gold link that omitted --gdb-index so gdb took 40s to load symbols from the 900MB binary',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='ldflags.mk tests/test_harbor.py',
        impl='ldflags.mk',
        src='LDFLAGS = -fuse-ld=gold',
        sym='gdb-index',
        grep='gdb-index',
        grep_obs='harbor -Wl,-O1 only. pack gdb-index.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: gdb 40s; no .gdb_index; gold omitted --gdb-index',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='-Wl,-O1 only',
        wrong_diff='+ -Wl,-O1 only',
        wrong_obs='still -Wl,-O1 only. still fail.',
        fail2='FAIL test_assign: still broken. gdb-index.',
        reread='apply gdb-index.',
        insight='-O1 is not gdb-index',
        probe="rg -n 'gdb-index' ldflags.mk",
        probe_obs='pack gdb-index. harbor -Wl,-O1 only.',
        fix='gdb-index',
        fix_diff='+ gdb-index\n',
        rel='dump/ldflags.mk',
        rel_src='LDFLAGS = -fuse-ld=gold',
        leftover='leftover -Wl,-O1 only',
        fix2='dump gdb-index',
        fix2_diff='+ dump gdb-index\n',
        bad_pat='-Wl,-O1 only',
        doc='docs/QUAY-GLDIDX.md',
        doc_point='-O1 is not gdb-index',
        doc_diff='+ -O1 is not gdb-index.',
        reg='reg',
        reg_diff='+ gdb-index holds',
        final_ok='ok 6 passed. gdb-index.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='gdb-index; dump leftover.',
        wrap='the gdb-index',
        wrap_ok='6 passed. quay-gldidx assign is green.',
        wrap_part='5 passed, 1 residual. quay-gldidx assign is green.',
        goal='Designed plant quay-gldidx: the gold link that omitted --gdb-index so gdb took 40s to load symbols from the 900MB binary. gdb-index. -O1 is not gdb-index.',
        plan='Repro python tests, reject -Wl,-O1 only, gdb-index, hand off dump.',
        out_ok='gdb-index. 6 tests pass.',
        out_part='gdb-index. dump leftover. Partial.',
    ),
    "chrpath": P(True,
        slug='pr-chrpath-delete-rpath-origin',
        plant='lock-chrdel',
        what='the chrpath -d that deleted DT_RPATH so the bundled OpenSSL was ignored after install',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='bundle.sh tests/test_harbor.py',
        impl='bundle.sh',
        src='chrpath -d harbor',
        sym='chrpath -r ORIGIN',
        grep='chrpath',
        grep_obs='harbor strip --strip-all. pack chrpath -r ORIGIN.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: after install libssl system 1.1 vs bundled 3; rpath deleted',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='strip --strip-all',
        wrong_diff='+ strip --strip-all',
        wrong_obs='still strip --strip-all. still fail.',
        fail2='FAIL test_assign: still broken. chrpath -r ORIGIN.',
        reread='apply chrpath -r ORIGIN.',
        insight='strip is not rpath',
        probe="rg -n 'chrpath' bundle.sh",
        probe_obs='pack chrpath -r ORIGIN. harbor strip --strip-all.',
        fix='chrpath -r ORIGIN',
        fix_diff='+ chrpath -r ORIGIN\n',
        rel='dump/bundle.sh',
        rel_src='chrpath -d harbor',
        leftover='leftover strip --strip-all',
        fix2='dump chrpath -r ORIGIN',
        fix2_diff='+ dump chrpath -r ORIGIN\n',
        bad_pat='strip --strip-all',
        doc='docs/LOCK-CHRDEL.md',
        doc_point='strip is not rpath',
        doc_diff='+ strip is not rpath.',
        reg='reg',
        reg_diff='+ chrpath -r ORIGIN holds',
        final_ok='ok 6 passed. chrpath -r ORIGIN.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='chrpath -r ORIGIN; dump same.',
        wrap='the chrpath -r ORIGIN',
        wrap_ok='6 passed. lock-chrdel assign is green.',
        wrap_part='5 passed, 1 residual. lock-chrdel assign is green.',
        goal='Designed plant lock-chrdel: the chrpath -d that deleted DT_RPATH so the bundled OpenSSL was ignored after install. chrpath -r ORIGIN. strip is not rpath.',
        plan='Repro python tests, reject strip --strip-all, chrpath -r ORIGIN, fix dump.',
        out_ok='chrpath -r ORIGIN. 6 tests pass.',
        out_part='chrpath -r ORIGIN. dump leftover. Partial.',
    ),
    "bfd": P(False,
        slug='pr-bfd-as-needed-vs-no-as-needed',
        plant='quay-bfdasn',
        what='the bfd link that used --as-needed on a plugin binary so dlopen symbols were dropped',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='ldflags.mk tests/test_harbor.py',
        impl='ldflags.mk',
        src='LDFLAGS = -Wl,--as-needed',
        sym='no-as-needed plugin',
        grep='no-as-needed',
        grep_obs='harbor -rdynamic only. pack no-as-needed for plugin.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: plugin dlopen undefined symbol; --as-needed dropped it',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='-rdynamic only',
        wrong_diff='+ -rdynamic only',
        wrong_obs='still -rdynamic only. still fail.',
        fail2='FAIL test_assign: still broken. no-as-needed for plugin.',
        reread='apply no-as-needed for plugin.',
        insight='-rdynamic is not no-as-needed for the plugin .so',
        probe="rg -n 'no-as-needed' ldflags.mk",
        probe_obs='pack no-as-needed for plugin. harbor -rdynamic only.',
        fix='no-as-needed for plugin',
        fix_diff='+ no-as-needed for plugin\n',
        rel='dump/ldflags.mk',
        rel_src='LDFLAGS = -Wl,--as-needed',
        leftover='leftover -rdynamic only',
        fix2='dump no-as-needed for plugin',
        fix2_diff='+ dump no-as-needed for plugin\n',
        bad_pat='-rdynamic only',
        doc='docs/QUAY-BFDASN.md',
        doc_point='-rdynamic is not no-as-needed for the plugin .so',
        doc_diff='+ -rdynamic is not no-as-needed for the plugin .so.',
        reg='reg',
        reg_diff='+ no-as-needed for plugin holds',
        final_ok='ok 6 passed. no-as-needed for plugin.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='no-as-needed for plugin; dump leftover.',
        wrap='the no-as-needed for plugin',
        wrap_ok='6 passed. quay-bfdasn assign is green.',
        wrap_part='5 passed, 1 residual. quay-bfdasn assign is green.',
        goal='Designed plant quay-bfdasn: the bfd link that used --as-needed on a plugin binary so dlopen symbols were dropped. no-as-needed for plugin. -rdynamic is not no-as-needed for the plugin .so.',
        plan='Repro python tests, reject -rdynamic only, no-as-needed for plugin, hand off dump.',
        out_ok='no-as-needed for plugin. 6 tests pass.',
        out_part='no-as-needed for plugin. dump leftover. Partial.',
    ),
    "libsql": P(True,
        slug='pr-libsql-embedded-replica-sync',
        plant='lock-libsqls',
        what='the libSQL embedded replica that omitted sync_interval so reads stayed stale after primary writes',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='client.go tests/test_harbor.py',
        impl='client.go',
        src='db, _ := sql.Open("libsql", url)',
        sym='sync_interval',
        grep='sync_interval',
        grep_obs='harbor busy_timeout only. pack sync_interval 1s.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: replica SELECT stale; sync_interval 0; primary write not seen',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='busy_timeout only',
        wrong_diff='+ busy_timeout only',
        wrong_obs='still busy_timeout only. still fail.',
        fail2='FAIL test_assign: still broken. sync_interval 1s.',
        reread='apply sync_interval 1s.',
        insight='busy_timeout is not replica sync',
        probe="rg -n 'sync_interval' client.go",
        probe_obs='pack sync_interval 1s. harbor busy_timeout only.',
        fix='sync_interval 1s',
        fix_diff='+ sync_interval 1s\n',
        rel='dump/client.go',
        rel_src='db, _ := sql.Open("libsql", url)',
        leftover='leftover busy_timeout only',
        fix2='dump sync_interval 1s',
        fix2_diff='+ dump sync_interval 1s\n',
        bad_pat='busy_timeout only',
        doc='docs/LOCK-LIBSQLS.md',
        doc_point='busy_timeout is not replica sync',
        doc_diff='+ busy_timeout is not replica sync.',
        reg='reg',
        reg_diff='+ sync_interval 1s holds',
        final_ok='ok 6 passed. sync_interval 1s.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='sync_interval 1s; dump same.',
        wrap='the sync_interval 1s',
        wrap_ok='6 passed. lock-libsqls assign is green.',
        wrap_part='5 passed, 1 residual. lock-libsqls assign is green.',
        goal='Designed plant lock-libsqls: the libSQL embedded replica that omitted sync_interval so reads stayed stale after primary writes. sync_interval 1s. busy_timeout is not replica sync.',
        plan='Repro python tests, reject busy_timeout only, sync_interval 1s, fix dump.',
        out_ok='sync_interval 1s. 6 tests pass.',
        out_part='sync_interval 1s. dump leftover. Partial.',
    ),
    "turso": P(False,
        slug='pr-turso-db-token-group-attach',
        plant='quay-turatt',
        what='the Turso group token that omitted attach so the secondary database was Authorization denied',
        glob='**/*.{rb,sh,yml,toml,go,ebuild,mk,json}',
        ls='turso.sh tests/test_harbor.py',
        impl='turso.sh',
        src='turso db token harbor --expiration 1d',
        sym='group attach',
        grep='group',
        grep_obs='harbor ttl 7d only. pack token --group attach.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: ATTACH dump 401; token has no attach; group token missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='ttl 7d only',
        wrong_diff='+ ttl 7d only',
        wrong_obs='still ttl 7d only. still fail.',
        fail2='FAIL test_assign: still broken. token --group attach.',
        reread='apply token --group attach.',
        insight='longer ttl is not attach',
        probe="rg -n 'token' turso.sh",
        probe_obs='pack token --group attach. harbor ttl 7d only.',
        fix='token --group attach',
        fix_diff='+ token --group attach\n',
        rel='dump/turso.sh',
        rel_src='turso db token harbor --expiration 1d',
        leftover='leftover ttl 7d only',
        fix2='dump token --group attach',
        fix2_diff='+ dump token --group attach\n',
        bad_pat='ttl 7d only',
        doc='docs/QUAY-TURATT.md',
        doc_point='longer ttl is not attach',
        doc_diff='+ longer ttl is not attach.',
        reg='reg',
        reg_diff='+ token --group attach holds',
        final_ok='ok 6 passed. token --group attach.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='token --group attach; dump leftover.',
        wrap='the token --group attach',
        wrap_ok='6 passed. quay-turatt assign is green.',
        wrap_part='5 passed, 1 residual. quay-turatt assign is green.',
        goal='Designed plant quay-turatt: the Turso group token that omitted attach so the secondary database was Authorization denied. token --group attach. longer ttl is not attach.',
        plan='Repro python tests, reject ttl 7d only, token --group attach, hand off dump.',
        out_ok='token --group attach. 6 tests pass.',
        out_part='token --group attach. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Homebrew cellar skip_relocation vs MacPorts universal_setup', fn('homebrew'), fn('macports'), 'cellar any_skip_relocation; universal_setup lipo', 'pour_bottle; build.jobs', 'homebrew dump hardcoded Cellar; macports dump arm64 only'),
    ('Portage eapply_user vs pkgng vital', fn('portage'), fn('pkgng'), 'EAPI 8 eapply_user; vital annotation', 'PATCHES only; pkg lock', 'portage dump user patch skipped; pkgng dump autoremove'),
    ('just dotenv-filename vs Taskfile dotenv', fn('just'), fn('taskfile'), 'dotenv-filename .env.local; dotenv .env', 'export; silent', 'just dump TOKEN empty; taskfile dump AWS_SECRET empty'),
    ('Mage return sh.Run vs GoReleaser extra_files checksum', fn('mage'), fn('goreleaser'), 'return sh.Run error; extra_files in checksum', 'mg.Deps; signs binaries only', 'mage dump exit 0; goreleaser dump sbom unsigned'),
    ('ccache sloppiness vs distcc pump', fn('ccache'), fn('distcc'), 'sloppiness include_file_ctime; pump include server', 'CCACHE_DIR; more host slots', 'ccache dump 0 hits; distcc dump farm idle'),
    ('Icecream ICECC_NETNAME vs gold --gdb-index', fn('icecream'), fn('gold'), 'ICECC_NETNAME harbor; --gdb-index', 'ICECC_NICE; -O1', 'icecream dump daemon missing; gold dump no .gdb_index'),
    ('chrpath ORIGIN vs bfd no-as-needed plugin', fn('chrpath'), fn('bfd'), 'chrpath -r ORIGIN; --no-as-needed plugin', 'strip; -rdynamic', 'chrpath dump rpath deleted; bfd dump dlopen undef'),
    ('libSQL sync_interval vs Turso group attach', fn('libsql'), fn('turso'), 'sync_interval 1s; token --group attach', 'busy_timeout; ttl 7d', 'libsql dump stale replica; turso dump ATTACH 401'),
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
- Not a clone of r4163-r4508 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
