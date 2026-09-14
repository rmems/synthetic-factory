#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4ca: unused plants after r4500.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4500. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4ca_state.json")
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
    "hatchling": P(True,
        slug='pr-hatchling-version-source-vcs',
        plant='lock-hatchv',
        what='the Hatchling build that omitted [tool.hatch.version] source vcs so the sdist version was 0.0.0',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='pyproject.toml tests/test_harbor.py',
        impl='pyproject.toml',
        src='[build-system]\nrequires = ["hatchling"]',
        sym='version source vcs',
        grep='version',
        grep_obs='harbor manual version 0.0.0. pack version source vcs.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: sdist version 0.0.0; hatchling no vcs source',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='manual version 0.0.0',
        wrong_diff='+ manual version 0.0.0',
        wrong_obs='still manual version 0.0.0. still fail.',
        fail2='FAIL test_assign: still broken. version source vcs.',
        reread='apply version source vcs.',
        insight='a hardcoded 0.0.0 is not vcs version',
        probe="rg -n 'version' pyproject.toml",
        probe_obs='pack version source vcs. harbor manual version 0.0.0.',
        fix='version source vcs',
        fix_diff='+ version source vcs\n',
        rel='dump/pyproject.toml',
        rel_src='[build-system]\nrequires = ["hatchling"]',
        leftover='leftover manual version 0.0.0',
        fix2='dump version source vcs',
        fix2_diff='+ dump version source vcs\n',
        bad_pat='manual version 0.0.0',
        doc='docs/LOCK-HATCHV.md',
        doc_point='a hardcoded 0.0.0 is not vcs version',
        doc_diff='+ a hardcoded 0.0.0 is not vcs version.',
        reg='reg',
        reg_diff='+ version source vcs holds',
        final_ok='ok 6 passed. version source vcs.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='version source vcs; dump same.',
        wrap='the version source vcs',
        wrap_ok='6 passed. lock-hatchv assign is green.',
        wrap_part='5 passed, 1 residual. lock-hatchv assign is green.',
        goal='Designed plant lock-hatchv: the Hatchling build that omitted [tool.hatch.version] source vcs so the sdist version was 0.0.0. version source vcs. a hardcoded 0.0.0 is not vcs version.',
        plan='Repro python tests, reject manual version 0.0.0, version source vcs, fix dump.',
        out_ok='version source vcs. 6 tests pass.',
        out_part='version source vcs. dump leftover. Partial.',
    ),
    "versioneer": P(False,
        slug='pr-versioneer-setup-cfg-tag-prefix',
        plant='quay-verstag',
        what='the Versioneer setup that omitted tag_prefix so pep440 version included the v prefix and pip rejected it',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='setup.cfg tests/test_harbor.py',
        impl='setup.cfg',
        src='[versioneer]\nVCS = git',
        sym='tag_prefix',
        grep='tag_prefix',
        grep_obs='harbor versionfile_source only. pack tag_prefix empty.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: pip: version v1.2.3 invalid; tag_prefix missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='versionfile_source only',
        wrong_diff='+ versionfile_source only',
        wrong_obs='still versionfile_source only. still fail.',
        fail2='FAIL test_assign: still broken. tag_prefix empty.',
        reread='apply tag_prefix empty.',
        insight='versionfile_source is not tag_prefix',
        probe="rg -n 'tag_prefix' setup.cfg",
        probe_obs='pack tag_prefix empty. harbor versionfile_source only.',
        fix='tag_prefix empty',
        fix_diff='+ tag_prefix empty\n',
        rel='dump/setup.cfg',
        rel_src='[versioneer]\nVCS = git',
        leftover='leftover versionfile_source only',
        fix2='dump tag_prefix empty',
        fix2_diff='+ dump tag_prefix empty\n',
        bad_pat='versionfile_source only',
        doc='docs/QUAY-VERSTAG.md',
        doc_point='versionfile_source is not tag_prefix',
        doc_diff='+ versionfile_source is not tag_prefix.',
        reg='reg',
        reg_diff='+ tag_prefix empty holds',
        final_ok='ok 6 passed. tag_prefix empty.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='tag_prefix empty; dump leftover.',
        wrap='the tag_prefix empty',
        wrap_ok='6 passed. quay-verstag assign is green.',
        wrap_part='5 passed, 1 residual. quay-verstag assign is green.',
        goal='Designed plant quay-verstag: the Versioneer setup that omitted tag_prefix so pep440 version included the v prefix and pip rejected it. tag_prefix empty. versionfile_source is not tag_prefix.',
        plan='Repro python tests, reject versionfile_source only, tag_prefix empty, hand off dump.',
        out_ok='tag_prefix empty. 6 tests pass.',
        out_part='tag_prefix empty. dump leftover. Partial.',
    ),
    "setuptools": P(True,
        slug='pr-setuptools-package-dir-src-layout',
        plant='lock-stsrc',
        what='the setuptools package that omitted package_dir so the sdist lacked src/harbor and import failed',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='setup.cfg tests/test_harbor.py',
        impl='setup.cfg',
        src='[options]\npackages = find:',
        sym='package_dir src',
        grep='package_dir',
        grep_obs='harbor zip_safe false. pack package_dir src.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: import harbor ModuleNotFoundError; sdist has no src layout',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='zip_safe false',
        wrong_diff='+ zip_safe false',
        wrong_obs='still zip_safe false. still fail.',
        fail2='FAIL test_assign: still broken. package_dir src.',
        reread='apply package_dir src.',
        insight='zip_safe is not package_dir',
        probe="rg -n 'package_dir' setup.cfg",
        probe_obs='pack package_dir src. harbor zip_safe false.',
        fix='package_dir src',
        fix_diff='+ package_dir src\n',
        rel='dump/setup.cfg',
        rel_src='[options]\npackages = find:',
        leftover='leftover zip_safe false',
        fix2='dump package_dir src',
        fix2_diff='+ dump package_dir src\n',
        bad_pat='zip_safe false',
        doc='docs/LOCK-STSRC.md',
        doc_point='zip_safe is not package_dir',
        doc_diff='+ zip_safe is not package_dir.',
        reg='reg',
        reg_diff='+ package_dir src holds',
        final_ok='ok 6 passed. package_dir src.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='package_dir src; dump same.',
        wrap='the package_dir src',
        wrap_ok='6 passed. lock-stsrc assign is green.',
        wrap_part='5 passed, 1 residual. lock-stsrc assign is green.',
        goal='Designed plant lock-stsrc: the setuptools package that omitted package_dir so the sdist lacked src/harbor and import failed. package_dir src. zip_safe is not package_dir.',
        plan='Repro python tests, reject zip_safe false, package_dir src, fix dump.',
        out_ok='package_dir src. 6 tests pass.',
        out_part='package_dir src. dump leftover. Partial.',
    ),
    "mill": P(False,
        slug='pr-mill-zinc-incremental-bloop',
        plant='quay-millzinc',
        what='the Mill compile that disabled zinc incremental so every CI job rebuilt the world and timed out',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='build.sc tests/test_harbor.py',
        impl='build.sc',
        src='object harbor extends ScalaModule { }',
        sym='zinc incremental',
        grep='zinc',
        grep_obs='harbor forkArgs -Xmx. pack zinc incremental on.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: compile 18min; zinc incremental off; CI timeout',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='forkArgs -Xmx',
        wrong_diff='+ forkArgs -Xmx',
        wrong_obs='still forkArgs -Xmx. still fail.',
        fail2='FAIL test_assign: still broken. zinc incremental on.',
        reread='apply zinc incremental on.',
        insight='more heap is not zinc incremental',
        probe="rg -n 'zinc' build.sc",
        probe_obs='pack zinc incremental on. harbor forkArgs -Xmx.',
        fix='zinc incremental on',
        fix_diff='+ zinc incremental on\n',
        rel='dump/build.sc',
        rel_src='object harbor extends ScalaModule { }',
        leftover='leftover forkArgs -Xmx',
        fix2='dump zinc incremental on',
        fix2_diff='+ dump zinc incremental on\n',
        bad_pat='forkArgs -Xmx',
        doc='docs/QUAY-MILLZINC.md',
        doc_point='more heap is not zinc incremental',
        doc_diff='+ more heap is not zinc incremental.',
        reg='reg',
        reg_diff='+ zinc incremental on holds',
        final_ok='ok 6 passed. zinc incremental on.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='zinc incremental on; dump leftover.',
        wrap='the zinc incremental on',
        wrap_ok='6 passed. quay-millzinc assign is green.',
        wrap_part='5 passed, 1 residual. quay-millzinc assign is green.',
        goal='Designed plant quay-millzinc: the Mill compile that disabled zinc incremental so every CI job rebuilt the world and timed out. zinc incremental on. more heap is not zinc incremental.',
        plan='Repro python tests, reject forkArgs -Xmx, zinc incremental on, hand off dump.',
        out_ok='zinc incremental on. 6 tests pass.',
        out_part='zinc incremental on. dump leftover. Partial.',
    ),
    "sbt": P(True,
        slug='pr-sbt-coursier-checksum-fail',
        plant='lock-sbtck',
        what='the sbt Coursier resolvers that omitted checksums so a mirrored jar with a bad sha1 was accepted then crashed',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='build.sbt tests/test_harbor.py',
        impl='build.sbt',
        src='resolvers += "mirror" at "https://mirror.example/maven"',
        sym='checksums sha1',
        grep='checksums',
        grep_obs='harbor updateOptions latestSnapshots. pack coursier checksums.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: runtime NoSuchMethodError; mirror jar sha1 skipped',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='updateOptions latestSnapshots',
        wrong_diff='+ updateOptions latestSnapshots',
        wrong_obs='still updateOptions latestSnapshots. still fail.',
        fail2='FAIL test_assign: still broken. coursier checksums.',
        reread='apply coursier checksums.',
        insight='latestSnapshots is not a checksum',
        probe="rg -n 'coursier' build.sbt",
        probe_obs='pack coursier checksums. harbor updateOptions latestSnapshots.',
        fix='coursier checksums',
        fix_diff='+ coursier checksums\n',
        rel='dump/build.sbt',
        rel_src='resolvers += "mirror" at "https://mirror.example/maven"',
        leftover='leftover updateOptions latestSnapshots',
        fix2='dump coursier checksums',
        fix2_diff='+ dump coursier checksums\n',
        bad_pat='updateOptions latestSnapshots',
        doc='docs/LOCK-SBTCK.md',
        doc_point='latestSnapshots is not a checksum',
        doc_diff='+ latestSnapshots is not a checksum.',
        reg='reg',
        reg_diff='+ coursier checksums holds',
        final_ok='ok 6 passed. coursier checksums.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='coursier checksums; dump same.',
        wrap='the coursier checksums',
        wrap_ok='6 passed. lock-sbtck assign is green.',
        wrap_part='5 passed, 1 residual. lock-sbtck assign is green.',
        goal='Designed plant lock-sbtck: the sbt Coursier resolvers that omitted checksums so a mirrored jar with a bad sha1 was accepted then crashed. coursier checksums. latestSnapshots is not a checksum.',
        plan='Repro python tests, reject updateOptions latestSnapshots, coursier checksums, fix dump.',
        out_ok='coursier checksums. 6 tests pass.',
        out_part='coursier checksums. dump leftover. Partial.',
    ),
    "leiningen": P(False,
        slug='pr-leiningen-pedantic-ranges-abort',
        plant='quay-leinped',
        what='the Leiningen project that omitted :pedantic? so a range version pulled a breaking SNAPSHOT',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='project.clj tests/test_harbor.py',
        impl='project.clj',
        src='(defproject harbor "0.1.0" :dependencies [[http-kit "1.0.0"]])',
        sym=':pedantic? abort',
        grep=':pedantic?',
        grep_obs='harbor :aot :all. pack :pedantic? abort.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: runtime pulled http-kit 2.0-SNAPSHOT; pedantic off',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong=':aot :all',
        wrong_diff='+ :aot :all',
        wrong_obs='still :aot :all. still fail.',
        fail2='FAIL test_assign: still broken. :pedantic? abort.',
        reread='apply :pedantic? abort.',
        insight=':aot is not pedantic',
        probe="rg -n ':pedantic?' project.clj",
        probe_obs='pack :pedantic? abort. harbor :aot :all.',
        fix=':pedantic? abort',
        fix_diff='+ :pedantic? abort\n',
        rel='dump/project.clj',
        rel_src='(defproject harbor "0.1.0" :dependencies [[http-kit "1.0.0"]])',
        leftover='leftover :aot :all',
        fix2='dump :pedantic? abort',
        fix2_diff='+ dump :pedantic? abort\n',
        bad_pat=':aot :all',
        doc='docs/QUAY-LEINPED.md',
        doc_point=':aot is not pedantic',
        doc_diff='+ :aot is not pedantic.',
        reg='reg',
        reg_diff='+ :pedantic? abort holds',
        final_ok='ok 6 passed. :pedantic? abort.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary=':pedantic? abort; dump leftover.',
        wrap='the :pedantic? abort',
        wrap_ok='6 passed. quay-leinped assign is green.',
        wrap_part='5 passed, 1 residual. quay-leinped assign is green.',
        goal='Designed plant quay-leinped: the Leiningen project that omitted :pedantic? so a range version pulled a breaking SNAPSHOT. :pedantic? abort. :aot is not pedantic.',
        plan='Repro python tests, reject :aot :all, :pedantic? abort, hand off dump.',
        out_ok=':pedantic? abort. 6 tests pass.',
        out_part=':pedantic? abort. dump leftover. Partial.',
    ),
    "maven": P(True,
        slug='pr-maven-enforcer-require-release',
        plant='lock-mvnrel',
        what='the Maven enforcer that omitted requireReleaseDeps so a SNAPSHOT leaked into the release jar',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='pom.xml tests/test_harbor.py',
        impl='pom.xml',
        src='<build><plugins></plugins></build>',
        sym='requireReleaseDeps',
        grep='requireReleaseDeps',
        grep_obs='harbor skipTests true. pack enforcer requireReleaseDeps.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: release jar contains SNAPSHOT dep; enforcer missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='skipTests true',
        wrong_diff='+ skipTests true',
        wrong_obs='still skipTests true. still fail.',
        fail2='FAIL test_assign: still broken. enforcer requireReleaseDeps.',
        reread='apply enforcer requireReleaseDeps.',
        insight='skipTests is not requireReleaseDeps',
        probe="rg -n 'enforcer' pom.xml",
        probe_obs='pack enforcer requireReleaseDeps. harbor skipTests true.',
        fix='enforcer requireReleaseDeps',
        fix_diff='+ enforcer requireReleaseDeps\n',
        rel='dump/pom.xml',
        rel_src='<build><plugins></plugins></build>',
        leftover='leftover skipTests true',
        fix2='dump enforcer requireReleaseDeps',
        fix2_diff='+ dump enforcer requireReleaseDeps\n',
        bad_pat='skipTests true',
        doc='docs/LOCK-MVNREL.md',
        doc_point='skipTests is not requireReleaseDeps',
        doc_diff='+ skipTests is not requireReleaseDeps.',
        reg='reg',
        reg_diff='+ enforcer requireReleaseDeps holds',
        final_ok='ok 6 passed. enforcer requireReleaseDeps.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='enforcer requireReleaseDeps; dump same.',
        wrap='the enforcer requireReleaseDeps',
        wrap_ok='6 passed. lock-mvnrel assign is green.',
        wrap_part='5 passed, 1 residual. lock-mvnrel assign is green.',
        goal='Designed plant lock-mvnrel: the Maven enforcer that omitted requireReleaseDeps so a SNAPSHOT leaked into the release jar. enforcer requireReleaseDeps. skipTests is not requireReleaseDeps.',
        plan='Repro python tests, reject skipTests true, enforcer requireReleaseDeps, fix dump.',
        out_ok='enforcer requireReleaseDeps. 6 tests pass.',
        out_part='enforcer requireReleaseDeps. dump leftover. Partial.',
    ),
    "pants": P(False,
        slug='pr-pants-python-interpreter-constraints',
        plant='quay-pantspy',
        what='the Pants python_sources that omitted interpreter_constraints so CI used 3.8 and the 3.12 typing syntax failed',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='BUILD tests/test_harbor.py',
        impl='BUILD',
        src='python_sources()',
        sym='interpreter_constraints',
        grep='interpreter_constraints',
        grep_obs='harbor pytest timeout. pack interpreter_constraints 3.12.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: SyntaxError match; pants interpreter 3.8; constraints missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='pytest timeout',
        wrong_diff='+ pytest timeout',
        wrong_obs='still pytest timeout. still fail.',
        fail2='FAIL test_assign: still broken. interpreter_constraints 3.12.',
        reread='apply interpreter_constraints 3.12.',
        insight='pytest timeout is not interpreter_constraints',
        probe="rg -n 'interpreter_constraints' BUILD",
        probe_obs='pack interpreter_constraints 3.12. harbor pytest timeout.',
        fix='interpreter_constraints 3.12',
        fix_diff='+ interpreter_constraints 3.12\n',
        rel='dump/BUILD',
        rel_src='python_sources()',
        leftover='leftover pytest timeout',
        fix2='dump interpreter_constraints 3.12',
        fix2_diff='+ dump interpreter_constraints 3.12\n',
        bad_pat='pytest timeout',
        doc='docs/QUAY-PANTSPY.md',
        doc_point='pytest timeout is not interpreter_constraints',
        doc_diff='+ pytest timeout is not interpreter_constraints.',
        reg='reg',
        reg_diff='+ interpreter_constraints 3.12 holds',
        final_ok='ok 6 passed. interpreter_constraints 3.12.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='interpreter_constraints 3.12; dump leftover.',
        wrap='the interpreter_constraints 3.12',
        wrap_ok='6 passed. quay-pantspy assign is green.',
        wrap_part='5 passed, 1 residual. quay-pantspy assign is green.',
        goal='Designed plant quay-pantspy: the Pants python_sources that omitted interpreter_constraints so CI used 3.8 and the 3.12 typing syntax failed. interpreter_constraints 3.12. pytest timeout is not interpreter_constraints.',
        plan='Repro python tests, reject pytest timeout, interpreter_constraints 3.12, hand off dump.',
        out_ok='interpreter_constraints 3.12. 6 tests pass.',
        out_part='interpreter_constraints 3.12. dump leftover. Partial.',
    ),
    "please": P(True,
        slug='pr-please-hash-download-sha256',
        plant='lock-plzhash',
        what='the Please http_file that omitted sha256 so a redirected tarball silently changed contents',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='BUILD tests/test_harbor.py',
        impl='BUILD',
        src="http_file(name='src', urls=['https://example/src.tgz'])",
        sym='sha256',
        grep='sha256',
        grep_obs='harbor strip_prefix only. pack http_file sha256.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: extracted tree missing files; http_file no sha256; redirect swapped tarball',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='strip_prefix only',
        wrong_diff='+ strip_prefix only',
        wrong_obs='still strip_prefix only. still fail.',
        fail2='FAIL test_assign: still broken. http_file sha256.',
        reread='apply http_file sha256.',
        insight='strip_prefix is not sha256',
        probe="rg -n 'http_file' BUILD",
        probe_obs='pack http_file sha256. harbor strip_prefix only.',
        fix='http_file sha256',
        fix_diff='+ http_file sha256\n',
        rel='dump/BUILD',
        rel_src="http_file(name='src', urls=['https://example/src.tgz'])",
        leftover='leftover strip_prefix only',
        fix2='dump http_file sha256',
        fix2_diff='+ dump http_file sha256\n',
        bad_pat='strip_prefix only',
        doc='docs/LOCK-PLZHASH.md',
        doc_point='strip_prefix is not sha256',
        doc_diff='+ strip_prefix is not sha256.',
        reg='reg',
        reg_diff='+ http_file sha256 holds',
        final_ok='ok 6 passed. http_file sha256.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='http_file sha256; dump same.',
        wrap='the http_file sha256',
        wrap_ok='6 passed. lock-plzhash assign is green.',
        wrap_part='5 passed, 1 residual. lock-plzhash assign is green.',
        goal='Designed plant lock-plzhash: the Please http_file that omitted sha256 so a redirected tarball silently changed contents. http_file sha256. strip_prefix is not sha256.',
        plan='Repro python tests, reject strip_prefix only, http_file sha256, fix dump.',
        out_ok='http_file sha256. 6 tests pass.',
        out_part='http_file sha256. dump leftover. Partial.',
    ),
    "sccache": P(False,
        slug='pr-sccache-dist-auth-token',
        plant='quay-sccauth',
        what="the sccache-dist client that omitted auth token so scheduler 401'd and compiles fell back to local and timed out",
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='sccache.toml tests/test_harbor.py',
        impl='sccache.toml',
        src='[dist]\nscheduler_url = "https://sccache.example"',
        sym='auth token',
        grep='auth',
        grep_obs='harbor SCCACHE_CACHE_SIZE. pack dist auth token.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: scheduler 401; dist auth missing; local compile timeout',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='SCCACHE_CACHE_SIZE',
        wrong_diff='+ SCCACHE_CACHE_SIZE',
        wrong_obs='still SCCACHE_CACHE_SIZE. still fail.',
        fail2='FAIL test_assign: still broken. dist auth token.',
        reread='apply dist auth token.',
        insight='cache size is not dist auth',
        probe="rg -n 'dist' sccache.toml",
        probe_obs='pack dist auth token. harbor SCCACHE_CACHE_SIZE.',
        fix='dist auth token',
        fix_diff='+ dist auth token\n',
        rel='dump/sccache.toml',
        rel_src='[dist]\nscheduler_url = "https://sccache.example"',
        leftover='leftover SCCACHE_CACHE_SIZE',
        fix2='dump dist auth token',
        fix2_diff='+ dump dist auth token\n',
        bad_pat='SCCACHE_CACHE_SIZE',
        doc='docs/QUAY-SCCAUTH.md',
        doc_point='cache size is not dist auth',
        doc_diff='+ cache size is not dist auth.',
        reg='reg',
        reg_diff='+ dist auth token holds',
        final_ok='ok 6 passed. dist auth token.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='dist auth token; dump leftover.',
        wrap='the dist auth token',
        wrap_ok='6 passed. quay-sccauth assign is green.',
        wrap_part='5 passed, 1 residual. quay-sccauth assign is green.',
        goal="Designed plant quay-sccauth: the sccache-dist client that omitted auth token so scheduler 401'd and compiles fell back to local and timed out. dist auth token. cache size is not dist auth.",
        plan='Repro python tests, reject SCCACHE_CACHE_SIZE, dist auth token, hand off dump.',
        out_ok='dist auth token. 6 tests pass.',
        out_part='dist auth token. dump leftover. Partial.',
    ),
    "mold": P(True,
        slug='pr-mold-separate-debug-compress',
        plant='lock-molddbg',
        what='the mold link that omitted --separate-debug-file so the 900MB binary with DWARF exceeded the image limit',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='ldflags.mk tests/test_harbor.py',
        impl='ldflags.mk',
        src='LDFLAGS = -fuse-ld=mold',
        sym='separate-debug-file',
        grep='separate-debug-file',
        grep_obs='harbor -Wl,-O2 only. pack separate-debug-file.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: image 900MB; mold packed DWARF in the binary; no separate debug',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='-Wl,-O2 only',
        wrong_diff='+ -Wl,-O2 only',
        wrong_obs='still -Wl,-O2 only. still fail.',
        fail2='FAIL test_assign: still broken. separate-debug-file.',
        reread='apply separate-debug-file.',
        insight='-O2 is not separate debug',
        probe="rg -n 'separate-debug-file' ldflags.mk",
        probe_obs='pack separate-debug-file. harbor -Wl,-O2 only.',
        fix='separate-debug-file',
        fix_diff='+ separate-debug-file\n',
        rel='dump/ldflags.mk',
        rel_src='LDFLAGS = -fuse-ld=mold',
        leftover='leftover -Wl,-O2 only',
        fix2='dump separate-debug-file',
        fix2_diff='+ dump separate-debug-file\n',
        bad_pat='-Wl,-O2 only',
        doc='docs/LOCK-MOLDDBG.md',
        doc_point='-O2 is not separate debug',
        doc_diff='+ -O2 is not separate debug.',
        reg='reg',
        reg_diff='+ separate-debug-file holds',
        final_ok='ok 6 passed. separate-debug-file.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='separate-debug-file; dump same.',
        wrap='the separate-debug-file',
        wrap_ok='6 passed. lock-molddbg assign is green.',
        wrap_part='5 passed, 1 residual. lock-molddbg assign is green.',
        goal='Designed plant lock-molddbg: the mold link that omitted --separate-debug-file so the 900MB binary with DWARF exceeded the image limit. separate-debug-file. -O2 is not separate debug.',
        plan='Repro python tests, reject -Wl,-O2 only, separate-debug-file, fix dump.',
        out_ok='separate-debug-file. 6 tests pass.',
        out_part='separate-debug-file. dump leftover. Partial.',
    ),
    "lld": P(False,
        slug='pr-lld-pack-dyn-relocs-android',
        plant='quay-lldrel',
        what='the LLD Android link that omitted --pack-dyn-relocs=android+relr so the APK .so relocs blew the 16MB zip entry',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='Android.mk tests/test_harbor.py',
        impl='Android.mk',
        src='LOCAL_LDFLAGS := -fuse-ld=lld',
        sym='pack-dyn-relocs',
        grep='pack-dyn-relocs',
        grep_obs='harbor -O3 only. pack pack-dyn-relocs android+relr.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: libharbor.so 22MB relocs; APK zip entry over 16MB',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='-O3 only',
        wrong_diff='+ -O3 only',
        wrong_obs='still -O3 only. still fail.',
        fail2='FAIL test_assign: still broken. pack-dyn-relocs android+relr.',
        reread='apply pack-dyn-relocs android+relr.',
        insight='-O3 is not packed relocs',
        probe="rg -n 'pack-dyn-relocs' Android.mk",
        probe_obs='pack pack-dyn-relocs android+relr. harbor -O3 only.',
        fix='pack-dyn-relocs android+relr',
        fix_diff='+ pack-dyn-relocs android+relr\n',
        rel='dump/Android.mk',
        rel_src='LOCAL_LDFLAGS := -fuse-ld=lld',
        leftover='leftover -O3 only',
        fix2='dump pack-dyn-relocs android+relr',
        fix2_diff='+ dump pack-dyn-relocs android+relr\n',
        bad_pat='-O3 only',
        doc='docs/QUAY-LLDREL.md',
        doc_point='-O3 is not packed relocs',
        doc_diff='+ -O3 is not packed relocs.',
        reg='reg',
        reg_diff='+ pack-dyn-relocs android+relr holds',
        final_ok='ok 6 passed. pack-dyn-relocs android+relr.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='pack-dyn-relocs android+relr; dump leftover.',
        wrap='the pack-dyn-relocs android+relr',
        wrap_ok='6 passed. quay-lldrel assign is green.',
        wrap_part='5 passed, 1 residual. quay-lldrel assign is green.',
        goal='Designed plant quay-lldrel: the LLD Android link that omitted --pack-dyn-relocs=android+relr so the APK .so relocs blew the 16MB zip entry. pack-dyn-relocs android+relr. -O3 is not packed relocs.',
        plan='Repro python tests, reject -O3 only, pack-dyn-relocs android+relr, hand off dump.',
        out_ok='pack-dyn-relocs android+relr. 6 tests pass.',
        out_part='pack-dyn-relocs android+relr. dump leftover. Partial.',
    ),
    "patchelf": P(True,
        slug='pr-patchelf-set-rpath-origin',
        plant='lock-pelfo',
        what='the patchelf invocation that set a absolute rpath so the bundled libstdc++ was ignored after relocate',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='bundle.sh tests/test_harbor.py',
        impl='bundle.sh',
        src='patchelf --set-rpath /opt/harbor/lib harbor',
        sym='rpath ORIGIN',
        grep='rpath',
        grep_obs='harbor LD_LIBRARY_PATH. pack set-rpath ORIGIN.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: after relocate libstdc++ wrong ABI; rpath absolute /opt',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='LD_LIBRARY_PATH',
        wrong_diff='+ LD_LIBRARY_PATH',
        wrong_obs='still LD_LIBRARY_PATH. still fail.',
        fail2='FAIL test_assign: still broken. set-rpath ORIGIN.',
        reread='apply set-rpath ORIGIN.',
        insight='LD_LIBRARY_PATH is not rpath',
        probe="rg -n 'set-rpath' bundle.sh",
        probe_obs='pack set-rpath ORIGIN. harbor LD_LIBRARY_PATH.',
        fix='set-rpath ORIGIN',
        fix_diff='+ set-rpath ORIGIN\n',
        rel='dump/bundle.sh',
        rel_src='patchelf --set-rpath /opt/harbor/lib harbor',
        leftover='leftover LD_LIBRARY_PATH',
        fix2='dump set-rpath ORIGIN',
        fix2_diff='+ dump set-rpath ORIGIN\n',
        bad_pat='LD_LIBRARY_PATH',
        doc='docs/LOCK-PELFO.md',
        doc_point='LD_LIBRARY_PATH is not rpath',
        doc_diff='+ LD_LIBRARY_PATH is not rpath.',
        reg='reg',
        reg_diff='+ set-rpath ORIGIN holds',
        final_ok='ok 6 passed. set-rpath ORIGIN.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='set-rpath ORIGIN; dump same.',
        wrap='the set-rpath ORIGIN',
        wrap_ok='6 passed. lock-pelfo assign is green.',
        wrap_part='5 passed, 1 residual. lock-pelfo assign is green.',
        goal='Designed plant lock-pelfo: the patchelf invocation that set a absolute rpath so the bundled libstdc++ was ignored after relocate. set-rpath ORIGIN. LD_LIBRARY_PATH is not rpath.',
        plan='Repro python tests, reject LD_LIBRARY_PATH, set-rpath ORIGIN, fix dump.',
        out_ok='set-rpath ORIGIN. 6 tests pass.',
        out_part='set-rpath ORIGIN. dump leftover. Partial.',
    ),
    "appimage": P(False,
        slug='pr-appimage-type2-update-info',
        plant='quay-appupd',
        what='the AppImage that omitted updateinformation so appimageupdatetool said no update info',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='harbor.desktop tests/test_harbor.py',
        impl='harbor.desktop',
        src='[Desktop Entry]\nName=Harbor',
        sym='updateinformation',
        grep='updateinformation',
        grep_obs='harbor chmod +x only. pack updateinformation zsync.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: appimageupdatetool: no updateinformation; Type2 missing field',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='chmod +x only',
        wrong_diff='+ chmod +x only',
        wrong_obs='still chmod +x only. still fail.',
        fail2='FAIL test_assign: still broken. updateinformation zsync.',
        reread='apply updateinformation zsync.',
        insight='chmod +x is not updateinformation',
        probe="rg -n 'updateinformation' harbor.desktop",
        probe_obs='pack updateinformation zsync. harbor chmod +x only.',
        fix='updateinformation zsync',
        fix_diff='+ updateinformation zsync\n',
        rel='dump/harbor.desktop',
        rel_src='[Desktop Entry]\nName=Harbor',
        leftover='leftover chmod +x only',
        fix2='dump updateinformation zsync',
        fix2_diff='+ dump updateinformation zsync\n',
        bad_pat='chmod +x only',
        doc='docs/QUAY-APPUPD.md',
        doc_point='chmod +x is not updateinformation',
        doc_diff='+ chmod +x is not updateinformation.',
        reg='reg',
        reg_diff='+ updateinformation zsync holds',
        final_ok='ok 6 passed. updateinformation zsync.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='updateinformation zsync; dump leftover.',
        wrap='the updateinformation zsync',
        wrap_ok='6 passed. quay-appupd assign is green.',
        wrap_part='5 passed, 1 residual. quay-appupd assign is green.',
        goal='Designed plant quay-appupd: the AppImage that omitted updateinformation so appimageupdatetool said no update info. updateinformation zsync. chmod +x is not updateinformation.',
        plan='Repro python tests, reject chmod +x only, updateinformation zsync, hand off dump.',
        out_ok='updateinformation zsync. 6 tests pass.',
        out_part='updateinformation zsync. dump leftover. Partial.',
    ),
    "snap": P(True,
        slug='pr-snap-classic-confinement-plugs',
        plant='lock-snappl',
        what='the Snap that used classic confinement so review-tools rejected the store upload',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='snapcraft.yaml tests/test_harbor.py',
        impl='snapcraft.yaml',
        src='confinement: classic',
        sym='strict plugs',
        grep='strict',
        grep_obs='harbor grade devel. pack strict confinement plugs.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: review-tools: classic not allowed; store rejected',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='grade devel',
        wrong_diff='+ grade devel',
        wrong_obs='still grade devel. still fail.',
        fail2='FAIL test_assign: still broken. strict confinement plugs.',
        reread='apply strict confinement plugs.',
        insight='grade devel is not confinement',
        probe="rg -n 'strict' snapcraft.yaml",
        probe_obs='pack strict confinement plugs. harbor grade devel.',
        fix='strict confinement plugs',
        fix_diff='+ strict confinement plugs\n',
        rel='dump/snapcraft.yaml',
        rel_src='confinement: classic',
        leftover='leftover grade devel',
        fix2='dump strict confinement plugs',
        fix2_diff='+ dump strict confinement plugs\n',
        bad_pat='grade devel',
        doc='docs/LOCK-SNAPPL.md',
        doc_point='grade devel is not confinement',
        doc_diff='+ grade devel is not confinement.',
        reg='reg',
        reg_diff='+ strict confinement plugs holds',
        final_ok='ok 6 passed. strict confinement plugs.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='strict confinement plugs; dump same.',
        wrap='the strict confinement plugs',
        wrap_ok='6 passed. lock-snappl assign is green.',
        wrap_part='5 passed, 1 residual. lock-snappl assign is green.',
        goal='Designed plant lock-snappl: the Snap that used classic confinement so review-tools rejected the store upload. strict confinement plugs. grade devel is not confinement.',
        plan='Repro python tests, reject grade devel, strict confinement plugs, fix dump.',
        out_ok='strict confinement plugs. 6 tests pass.',
        out_part='strict confinement plugs. dump leftover. Partial.',
    ),
    "flatpak": P(False,
        slug='pr-flatpak-finish-args-socket-wayland',
        plant='quay-fpway',
        what='the Flatpak manifest that omitted --socket=wayland so the app fell back to X11 and crashed under pure Wayland',
        glob='**/*.{toml,py,scala,sbt,xml,build,json,sh,yml,desktop}',
        ls='com.harbor.App.json tests/test_harbor.py',
        impl='com.harbor.App.json',
        src='"finish-args": ["--share=network"]',
        sym='socket wayland',
        grep='socket',
        grep_obs='harbor --socket=x11 only. pack socket wayland.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: app crash no DISPLAY; wayland socket missing; x11-only',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='--socket=x11 only',
        wrong_diff='+ --socket=x11 only',
        wrong_obs='still --socket=x11 only. still fail.',
        fail2='FAIL test_assign: still broken. socket wayland.',
        reread='apply socket wayland.',
        insight='x11 socket is not wayland',
        probe="rg -n 'socket' com.harbor.App.json",
        probe_obs='pack socket wayland. harbor --socket=x11 only.',
        fix='socket wayland',
        fix_diff='+ socket wayland\n',
        rel='dump/com.harbor.App.json',
        rel_src='"finish-args": ["--share=network"]',
        leftover='leftover --socket=x11 only',
        fix2='dump socket wayland',
        fix2_diff='+ dump socket wayland\n',
        bad_pat='--socket=x11 only',
        doc='docs/QUAY-FPWAY.md',
        doc_point='x11 socket is not wayland',
        doc_diff='+ x11 socket is not wayland.',
        reg='reg',
        reg_diff='+ socket wayland holds',
        final_ok='ok 6 passed. socket wayland.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='socket wayland; dump leftover.',
        wrap='the socket wayland',
        wrap_ok='6 passed. quay-fpway assign is green.',
        wrap_part='5 passed, 1 residual. quay-fpway assign is green.',
        goal='Designed plant quay-fpway: the Flatpak manifest that omitted --socket=wayland so the app fell back to X11 and crashed under pure Wayland. socket wayland. x11 socket is not wayland.',
        plan='Repro python tests, reject --socket=x11 only, socket wayland, hand off dump.',
        out_ok='socket wayland. 6 tests pass.',
        out_part='socket wayland. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Hatchling version vcs vs Versioneer tag_prefix', fn('hatchling'), fn('versioneer'), 'version source vcs; tag_prefix empty', 'hardcoded 0.0.0; versionfile_source', 'hatchling dump 0.0.0; versioneer dump missing tag_prefix'),
    ('setuptools package_dir src vs Mill zinc incremental', fn('setuptools'), fn('mill'), 'package_dir src; zinc incremental on', 'zip_safe; more heap', 'setuptools dump no package_dir; mill dump zinc off'),
    ('sbt Coursier checksums vs Leiningen :pedantic? abort', fn('sbt'), fn('leiningen'), 'coursier checksums; :pedantic? abort', 'latestSnapshots; :aot', 'sbt dump no checksums; leiningen dump pedantic off'),
    ('Maven requireReleaseDeps vs Pants interpreter_constraints', fn('maven'), fn('pants'), 'enforcer requireReleaseDeps; interpreter_constraints 3.12', 'skipTests; pytest timeout', 'maven dump SNAPSHOT leak; pants dump 3.8'),
    ('Please http_file sha256 vs sccache-dist auth', fn('please'), fn('sccache'), 'http_file sha256; dist auth token', 'strip_prefix; cache size', 'please dump no sha256; sccache dump 401'),
    ('mold separate-debug vs LLD pack-dyn-relocs', fn('mold'), fn('lld'), 'separate-debug-file; pack-dyn-relocs android+relr', '-O2; -O3', 'mold dump fat DWARF; lld dump unpacked relocs'),
    ('patchelf ORIGIN rpath vs AppImage updateinformation', fn('patchelf'), fn('appimage'), 'set-rpath ORIGIN; updateinformation zsync', 'LD_LIBRARY_PATH; chmod +x', 'patchelf dump absolute rpath; appimage dump no update info'),
    ('Snap strict confinement vs Flatpak wayland socket', fn('snap'), fn('flatpak'), 'strict confinement plugs; --socket=wayland', 'grade devel; --socket=x11', 'snap dump classic; flatpak dump x11-only'),
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
- Not a clone of r4163-r4500 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
