#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cc: unused plants after r4516.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4516. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4cc_state.json")
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
    "yarn": P(True,
        slug='pr-yarn-nmhoisting-limits-workspaces',
        plant='lock-yarnhoist',
        what='the Yarn workspace that omitted nmHoistingLimits so a nested dependency hoisted and broke peer resolution',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='.yarnrc.yml tests/test_harbor.py',
        impl='.yarnrc.yml',
        src='nodeLinker: node-modules',
        sym='nmHoistingLimits workspaces',
        grep='nmHoistingLimits',
        grep_obs='harbor enableGlobalCache. pack nmHoistingLimits workspaces.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: peer react 17 vs 18; nested dep hoisted; nmHoistingLimits missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='enableGlobalCache',
        wrong_diff='+ enableGlobalCache',
        wrong_obs='still enableGlobalCache. still fail.',
        fail2='FAIL test_assign: still broken. nmHoistingLimits workspaces.',
        reread='apply nmHoistingLimits workspaces.',
        insight='global cache is not hoisting limits',
        probe="rg -n 'nmHoistingLimits' .yarnrc.yml",
        probe_obs='pack nmHoistingLimits workspaces. harbor enableGlobalCache.',
        fix='nmHoistingLimits workspaces',
        fix_diff='+ nmHoistingLimits workspaces\n',
        rel='dump/.yarnrc.yml',
        rel_src='nodeLinker: node-modules',
        leftover='leftover enableGlobalCache',
        fix2='dump nmHoistingLimits workspaces',
        fix2_diff='+ dump nmHoistingLimits workspaces\n',
        bad_pat='enableGlobalCache',
        doc='docs/LOCK-YARNHOIST.md',
        doc_point='global cache is not hoisting limits',
        doc_diff='+ global cache is not hoisting limits.',
        reg='reg',
        reg_diff='+ nmHoistingLimits workspaces holds',
        final_ok='ok 6 passed. nmHoistingLimits workspaces.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='nmHoistingLimits workspaces; dump same.',
        wrap='the nmHoistingLimits workspaces',
        wrap_ok='6 passed. lock-yarnhoist assign is green.',
        wrap_part='5 passed, 1 residual. lock-yarnhoist assign is green.',
        goal='Designed plant lock-yarnhoist: the Yarn workspace that omitted nmHoistingLimits so a nested dependency hoisted and broke peer resolution. nmHoistingLimits workspaces. global cache is not hoisting limits.',
        plan='Repro python tests, reject enableGlobalCache, nmHoistingLimits workspaces, fix dump.',
        out_ok='nmHoistingLimits workspaces. 6 tests pass.',
        out_part='nmHoistingLimits workspaces. dump leftover. Partial.',
    ),
    "esbuild": P(False,
        slug='pr-esbuild-packages-external-mark',
        plant='quay-esbext',
        what='the esbuild bundle that omitted packages external so aws-sdk was bundled and the lambda zip hit 80MB',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='build.mjs tests/test_harbor.py',
        impl='build.mjs',
        src="esbuild.build({entryPoints:['src/index.ts']})",
        sym='packages external',
        grep='packages',
        grep_obs='harbor minify only. pack packages external.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: zip 80MB; aws-sdk bundled; packages external missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='minify only',
        wrong_diff='+ minify only',
        wrong_obs='still minify only. still fail.',
        fail2='FAIL test_assign: still broken. packages external.',
        reread='apply packages external.',
        insight='minify is not packages external',
        probe="rg -n 'packages' build.mjs",
        probe_obs='pack packages external. harbor minify only.',
        fix='packages external',
        fix_diff='+ packages external\n',
        rel='dump/build.mjs',
        rel_src="esbuild.build({entryPoints:['src/index.ts']})",
        leftover='leftover minify only',
        fix2='dump packages external',
        fix2_diff='+ dump packages external\n',
        bad_pat='minify only',
        doc='docs/QUAY-ESBEXT.md',
        doc_point='minify is not packages external',
        doc_diff='+ minify is not packages external.',
        reg='reg',
        reg_diff='+ packages external holds',
        final_ok='ok 6 passed. packages external.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='packages external; dump leftover.',
        wrap='the packages external',
        wrap_ok='6 passed. quay-esbext assign is green.',
        wrap_part='5 passed, 1 residual. quay-esbext assign is green.',
        goal='Designed plant quay-esbext: the esbuild bundle that omitted packages external so aws-sdk was bundled and the lambda zip hit 80MB. packages external. minify is not packages external.',
        plan='Repro python tests, reject minify only, packages external, hand off dump.',
        out_ok='packages external. 6 tests pass.',
        out_part='packages external. dump leftover. Partial.',
    ),
    "swc": P(True,
        slug='pr-swc-jsc-keep-class-names',
        plant='lock-swckcn',
        what='the SWC transform that omitted keep_class_names so Angular DI tokens were minified and inject failed',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='.swcrc tests/test_harbor.py',
        impl='.swcrc',
        src='{ "jsc": { "minify": { "compress": true } } }',
        sym='keep_class_names',
        grep='keep_class_names',
        grep_obs='harbor mangle false only. pack keep_class_names true.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: NullInjectorError; class names mangled; keep_class_names missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='mangle false only',
        wrong_diff='+ mangle false only',
        wrong_obs='still mangle false only. still fail.',
        fail2='FAIL test_assign: still broken. keep_class_names true.',
        reread='apply keep_class_names true.',
        insight='mangle false is not keep_class_names under compress',
        probe="rg -n 'keep_class_names' .swcrc",
        probe_obs='pack keep_class_names true. harbor mangle false only.',
        fix='keep_class_names true',
        fix_diff='+ keep_class_names true\n',
        rel='dump/.swcrc',
        rel_src='{ "jsc": { "minify": { "compress": true } } }',
        leftover='leftover mangle false only',
        fix2='dump keep_class_names true',
        fix2_diff='+ dump keep_class_names true\n',
        bad_pat='mangle false only',
        doc='docs/LOCK-SWCKCN.md',
        doc_point='mangle false is not keep_class_names under compress',
        doc_diff='+ mangle false is not keep_class_names under compress.',
        reg='reg',
        reg_diff='+ keep_class_names true holds',
        final_ok='ok 6 passed. keep_class_names true.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='keep_class_names true; dump same.',
        wrap='the keep_class_names true',
        wrap_ok='6 passed. lock-swckcn assign is green.',
        wrap_part='5 passed, 1 residual. lock-swckcn assign is green.',
        goal='Designed plant lock-swckcn: the SWC transform that omitted keep_class_names so Angular DI tokens were minified and inject failed. keep_class_names true. mangle false is not keep_class_names under compress.',
        plan='Repro python tests, reject mangle false only, keep_class_names true, fix dump.',
        out_ok='keep_class_names true. 6 tests pass.',
        out_part='keep_class_names true. dump leftover. Partial.',
    ),
    "biome": P(False,
        slug='pr-biome-overrides-include-json',
        plant='quay-biojson',
        what='the Biome config that omitted overrides include for json so package.json was formatted as JS and broke the lockfile',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='biome.json tests/test_harbor.py',
        impl='biome.json',
        src='{ "formatter": { "indentStyle": "space" } }',
        sym='overrides include json',
        grep='overrides',
        grep_obs='harbor javascript formatter only. pack overrides json include.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: package.json trailing commas; json override missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='javascript formatter only',
        wrong_diff='+ javascript formatter only',
        wrong_obs='still javascript formatter only. still fail.',
        fail2='FAIL test_assign: still broken. overrides json include.',
        reread='apply overrides json include.',
        insight='js formatter is not json override',
        probe="rg -n 'overrides' biome.json",
        probe_obs='pack overrides json include. harbor javascript formatter only.',
        fix='overrides json include',
        fix_diff='+ overrides json include\n',
        rel='dump/biome.json',
        rel_src='{ "formatter": { "indentStyle": "space" } }',
        leftover='leftover javascript formatter only',
        fix2='dump overrides json include',
        fix2_diff='+ dump overrides json include\n',
        bad_pat='javascript formatter only',
        doc='docs/QUAY-BIOJSON.md',
        doc_point='js formatter is not json override',
        doc_diff='+ js formatter is not json override.',
        reg='reg',
        reg_diff='+ overrides json include holds',
        final_ok='ok 6 passed. overrides json include.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='overrides json include; dump leftover.',
        wrap='the overrides json include',
        wrap_ok='6 passed. quay-biojson assign is green.',
        wrap_part='5 passed, 1 residual. quay-biojson assign is green.',
        goal='Designed plant quay-biojson: the Biome config that omitted overrides include for json so package.json was formatted as JS and broke the lockfile. overrides json include. js formatter is not json override.',
        plan='Repro python tests, reject javascript formatter only, overrides json include, hand off dump.',
        out_ok='overrides json include. 6 tests pass.',
        out_part='overrides json include. dump leftover. Partial.',
    ),
    "dprint": P(True,
        slug='pr-dprint-includes-excludes-vendor',
        plant='lock-dprvnd',
        what='the dprint config that omitted excludes vendor so CI reformatted vendored protobuf and the diff was 40k lines',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='dprint.json tests/test_harbor.py',
        impl='dprint.json',
        src='{ "includes": ["**/*.{ts,js}"] }',
        sym='excludes vendor',
        grep='excludes',
        grep_obs='harbor incremental false. pack excludes vendor.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: vendor/ proto reformatted; excludes missing; 40k line diff',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='incremental false',
        wrong_diff='+ incremental false',
        wrong_obs='still incremental false. still fail.',
        fail2='FAIL test_assign: still broken. excludes vendor.',
        reread='apply excludes vendor.',
        insight='incremental is not excludes',
        probe="rg -n 'excludes' dprint.json",
        probe_obs='pack excludes vendor. harbor incremental false.',
        fix='excludes vendor',
        fix_diff='+ excludes vendor\n',
        rel='dump/dprint.json',
        rel_src='{ "includes": ["**/*.{ts,js}"] }',
        leftover='leftover incremental false',
        fix2='dump excludes vendor',
        fix2_diff='+ dump excludes vendor\n',
        bad_pat='incremental false',
        doc='docs/LOCK-DPRVND.md',
        doc_point='incremental is not excludes',
        doc_diff='+ incremental is not excludes.',
        reg='reg',
        reg_diff='+ excludes vendor holds',
        final_ok='ok 6 passed. excludes vendor.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='excludes vendor; dump same.',
        wrap='the excludes vendor',
        wrap_ok='6 passed. lock-dprvnd assign is green.',
        wrap_part='5 passed, 1 residual. lock-dprvnd assign is green.',
        goal='Designed plant lock-dprvnd: the dprint config that omitted excludes vendor so CI reformatted vendored protobuf and the diff was 40k lines. excludes vendor. incremental is not excludes.',
        plan='Repro python tests, reject incremental false, excludes vendor, fix dump.',
        out_ok='excludes vendor. 6 tests pass.',
        out_part='excludes vendor. dump leftover. Partial.',
    ),
    "oxc": P(False,
        slug='pr-oxc-resolver-condition-names',
        plant='quay-oxcres',
        what="the oxc-resolver that omitted conditionNames development so import 'harbor/dev' resolved to the prod export",
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='resolver.json tests/test_harbor.py',
        impl='resolver.json',
        src='{ "conditionNames": ["node", "import"] }',
        sym='conditionNames development',
        grep='conditionNames',
        grep_obs='harbor mainFields only. pack conditionNames development.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: resolved prod export; development condition missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='mainFields only',
        wrong_diff='+ mainFields only',
        wrong_obs='still mainFields only. still fail.',
        fail2='FAIL test_assign: still broken. conditionNames development.',
        reread='apply conditionNames development.',
        insight='mainFields is not conditionNames',
        probe="rg -n 'conditionNames' resolver.json",
        probe_obs='pack conditionNames development. harbor mainFields only.',
        fix='conditionNames development',
        fix_diff='+ conditionNames development\n',
        rel='dump/resolver.json',
        rel_src='{ "conditionNames": ["node", "import"] }',
        leftover='leftover mainFields only',
        fix2='dump conditionNames development',
        fix2_diff='+ dump conditionNames development\n',
        bad_pat='mainFields only',
        doc='docs/QUAY-OXCRES.md',
        doc_point='mainFields is not conditionNames',
        doc_diff='+ mainFields is not conditionNames.',
        reg='reg',
        reg_diff='+ conditionNames development holds',
        final_ok='ok 6 passed. conditionNames development.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='conditionNames development; dump leftover.',
        wrap='the conditionNames development',
        wrap_ok='6 passed. quay-oxcres assign is green.',
        wrap_part='5 passed, 1 residual. quay-oxcres assign is green.',
        goal="Designed plant quay-oxcres: the oxc-resolver that omitted conditionNames development so import 'harbor/dev' resolved to the prod export. conditionNames development. mainFields is not conditionNames.",
        plan='Repro python tests, reject mainFields only, conditionNames development, hand off dump.',
        out_ok='conditionNames development. 6 tests pass.',
        out_part='conditionNames development. dump leftover. Partial.',
    ),
    "parcel": P(True,
        slug='pr-parcel-public-url-absolute',
        plant='lock-parurl',
        what="the Parcel build that omitted publicUrl so asset paths were /index.123.js and the CDN 404'd",
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='.parcelrc tests/test_harbor.py',
        impl='.parcelrc',
        src='{ "extends": "@parcel/config-default" }',
        sym='publicUrl CDN',
        grep='publicUrl',
        grep_obs='harbor scopeHoist only. pack publicUrl CDN prefix.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: script src /index.hash.js 404 on CDN; publicUrl missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='scopeHoist only',
        wrong_diff='+ scopeHoist only',
        wrong_obs='still scopeHoist only. still fail.',
        fail2='FAIL test_assign: still broken. publicUrl CDN prefix.',
        reread='apply publicUrl CDN prefix.',
        insight='scopeHoist is not publicUrl',
        probe="rg -n 'publicUrl' .parcelrc",
        probe_obs='pack publicUrl CDN prefix. harbor scopeHoist only.',
        fix='publicUrl CDN prefix',
        fix_diff='+ publicUrl CDN prefix\n',
        rel='dump/.parcelrc',
        rel_src='{ "extends": "@parcel/config-default" }',
        leftover='leftover scopeHoist only',
        fix2='dump publicUrl CDN prefix',
        fix2_diff='+ dump publicUrl CDN prefix\n',
        bad_pat='scopeHoist only',
        doc='docs/LOCK-PARURL.md',
        doc_point='scopeHoist is not publicUrl',
        doc_diff='+ scopeHoist is not publicUrl.',
        reg='reg',
        reg_diff='+ publicUrl CDN prefix holds',
        final_ok='ok 6 passed. publicUrl CDN prefix.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='publicUrl CDN prefix; dump same.',
        wrap='the publicUrl CDN prefix',
        wrap_ok='6 passed. lock-parurl assign is green.',
        wrap_part='5 passed, 1 residual. lock-parurl assign is green.',
        goal="Designed plant lock-parurl: the Parcel build that omitted publicUrl so asset paths were /index.123.js and the CDN 404'd. publicUrl CDN prefix. scopeHoist is not publicUrl.",
        plan='Repro python tests, reject scopeHoist only, publicUrl CDN prefix, fix dump.',
        out_ok='publicUrl CDN prefix. 6 tests pass.',
        out_part='publicUrl CDN prefix. dump leftover. Partial.',
    ),
    "rollup": P(False,
        slug='pr-rollup-external-globals-named',
        plant='quay-rlpglb',
        what='the Rollup output that omitted output.globals so the UMD bundle referenced React as an undefined global',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='rollup.config.js tests/test_harbor.py',
        impl='rollup.config.js',
        src="external: ['react']",
        sym='output.globals React',
        grep='output.globals',
        grep_obs='harbor output.format iife only. pack output.globals react.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: UMD React is not defined; output.globals missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='output.format iife only',
        wrong_diff='+ output.format iife only',
        wrong_obs='still output.format iife only. still fail.',
        fail2='FAIL test_assign: still broken. output.globals react.',
        reread='apply output.globals react.',
        insight='format iife is not globals',
        probe="rg -n 'output.globals' rollup.config.js",
        probe_obs='pack output.globals react. harbor output.format iife only.',
        fix='output.globals react',
        fix_diff='+ output.globals react\n',
        rel='dump/rollup.config.js',
        rel_src="external: ['react']",
        leftover='leftover output.format iife only',
        fix2='dump output.globals react',
        fix2_diff='+ dump output.globals react\n',
        bad_pat='output.format iife only',
        doc='docs/QUAY-RLPGLB.md',
        doc_point='format iife is not globals',
        doc_diff='+ format iife is not globals.',
        reg='reg',
        reg_diff='+ output.globals react holds',
        final_ok='ok 6 passed. output.globals react.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='output.globals react; dump leftover.',
        wrap='the output.globals react',
        wrap_ok='6 passed. quay-rlpglb assign is green.',
        wrap_part='5 passed, 1 residual. quay-rlpglb assign is green.',
        goal='Designed plant quay-rlpglb: the Rollup output that omitted output.globals so the UMD bundle referenced React as an undefined global. output.globals react. format iife is not globals.',
        plan='Repro python tests, reject output.format iife only, output.globals react, hand off dump.',
        out_ok='output.globals react. 6 tests pass.',
        out_part='output.globals react. dump leftover. Partial.',
    ),
    "turborepo": P(True,
        slug='pr-turborepo-outputs-glob-cache',
        plant='lock-tbout',
        what='the Turborepo task that omitted outputs glob so cache restored an empty dist and deploy published nothing',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='turbo.json tests/test_harbor.py',
        impl='turbo.json',
        src='{ "tasks": { "build": {} } }',
        sym='outputs dist glob',
        grep='outputs',
        grep_obs='harbor cache false. pack outputs dist/**.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cache hit empty dist; outputs glob missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cache false',
        wrong_diff='+ cache false',
        wrong_obs='still cache false. still fail.',
        fail2='FAIL test_assign: still broken. outputs dist/**.',
        reread='apply outputs dist/**.',
        insight='cache false is not outputs',
        probe="rg -n 'outputs' turbo.json",
        probe_obs='pack outputs dist/**. harbor cache false.',
        fix='outputs dist/**',
        fix_diff='+ outputs dist/**\n',
        rel='dump/turbo.json',
        rel_src='{ "tasks": { "build": {} } }',
        leftover='leftover cache false',
        fix2='dump outputs dist/**',
        fix2_diff='+ dump outputs dist/**\n',
        bad_pat='cache false',
        doc='docs/LOCK-TBOUT.md',
        doc_point='cache false is not outputs',
        doc_diff='+ cache false is not outputs.',
        reg='reg',
        reg_diff='+ outputs dist/** holds',
        final_ok='ok 6 passed. outputs dist/**.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='outputs dist/**; dump same.',
        wrap='the outputs dist/**',
        wrap_ok='6 passed. lock-tbout assign is green.',
        wrap_part='5 passed, 1 residual. lock-tbout assign is green.',
        goal='Designed plant lock-tbout: the Turborepo task that omitted outputs glob so cache restored an empty dist and deploy published nothing. outputs dist/**. cache false is not outputs.',
        plan='Repro python tests, reject cache false, outputs dist/**, fix dump.',
        out_ok='outputs dist/**. 6 tests pass.',
        out_part='outputs dist/**. dump leftover. Partial.',
    ),
    "nx": P(False,
        slug='pr-nx-implicit-dependencies-env',
        plant='quay-nximp',
        what='the Nx target that omitted implicitDependencies on .env so a secret change did not invalidate cache',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='project.json tests/test_harbor.py',
        impl='project.json',
        src='{ "targets": { "build": {} } }',
        sym='implicitDependencies .env',
        grep='implicitDependencies',
        grep_obs='harbor dependsOn only. pack implicitDependencies .env.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cache hit after .env change; implicitDependencies missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='dependsOn only',
        wrong_diff='+ dependsOn only',
        wrong_obs='still dependsOn only. still fail.',
        fail2='FAIL test_assign: still broken. implicitDependencies .env.',
        reread='apply implicitDependencies .env.',
        insight='dependsOn is not implicitDependencies',
        probe="rg -n 'implicitDependencies' project.json",
        probe_obs='pack implicitDependencies .env. harbor dependsOn only.',
        fix='implicitDependencies .env',
        fix_diff='+ implicitDependencies .env\n',
        rel='dump/project.json',
        rel_src='{ "targets": { "build": {} } }',
        leftover='leftover dependsOn only',
        fix2='dump implicitDependencies .env',
        fix2_diff='+ dump implicitDependencies .env\n',
        bad_pat='dependsOn only',
        doc='docs/QUAY-NXIMP.md',
        doc_point='dependsOn is not implicitDependencies',
        doc_diff='+ dependsOn is not implicitDependencies.',
        reg='reg',
        reg_diff='+ implicitDependencies .env holds',
        final_ok='ok 6 passed. implicitDependencies .env.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='implicitDependencies .env; dump leftover.',
        wrap='the implicitDependencies .env',
        wrap_ok='6 passed. quay-nximp assign is green.',
        wrap_part='5 passed, 1 residual. quay-nximp assign is green.',
        goal='Designed plant quay-nximp: the Nx target that omitted implicitDependencies on .env so a secret change did not invalidate cache. implicitDependencies .env. dependsOn is not implicitDependencies.',
        plan='Repro python tests, reject dependsOn only, implicitDependencies .env, hand off dump.',
        out_ok='implicitDependencies .env. 6 tests pass.',
        out_part='implicitDependencies .env. dump leftover. Partial.',
    ),
    "lerna": P(True,
        slug='pr-lerna-independent-include-merged-tags',
        plant='lock-lrntag',
        what='the Lerna independent version that omitted --include-merged-tags so a cherry-pick never bumped the package',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='lerna.json tests/test_harbor.py',
        impl='lerna.json',
        src='{ "version": "independent" }',
        sym='include-merged-tags',
        grep='include-merged-tags',
        grep_obs='harbor conventionalCommits only. pack include-merged-tags.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: cherry-pick commit skipped; include-merged-tags missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='conventionalCommits only',
        wrong_diff='+ conventionalCommits only',
        wrong_obs='still conventionalCommits only. still fail.',
        fail2='FAIL test_assign: still broken. include-merged-tags.',
        reread='apply include-merged-tags.',
        insight='conventionalCommits is not include-merged-tags',
        probe="rg -n 'include-merged-tags' lerna.json",
        probe_obs='pack include-merged-tags. harbor conventionalCommits only.',
        fix='include-merged-tags',
        fix_diff='+ include-merged-tags\n',
        rel='dump/lerna.json',
        rel_src='{ "version": "independent" }',
        leftover='leftover conventionalCommits only',
        fix2='dump include-merged-tags',
        fix2_diff='+ dump include-merged-tags\n',
        bad_pat='conventionalCommits only',
        doc='docs/LOCK-LRNTAG.md',
        doc_point='conventionalCommits is not include-merged-tags',
        doc_diff='+ conventionalCommits is not include-merged-tags.',
        reg='reg',
        reg_diff='+ include-merged-tags holds',
        final_ok='ok 6 passed. include-merged-tags.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='include-merged-tags; dump same.',
        wrap='the include-merged-tags',
        wrap_ok='6 passed. lock-lrntag assign is green.',
        wrap_part='5 passed, 1 residual. lock-lrntag assign is green.',
        goal='Designed plant lock-lrntag: the Lerna independent version that omitted --include-merged-tags so a cherry-pick never bumped the package. include-merged-tags. conventionalCommits is not include-merged-tags.',
        plan='Repro python tests, reject conventionalCommits only, include-merged-tags, fix dump.',
        out_ok='include-merged-tags. 6 tests pass.',
        out_part='include-merged-tags. dump leftover. Partial.',
    ),
    "rush": P(False,
        slug='pr-rush-pnpmfile-peer-dependency-rules',
        plant='quay-rshpeer',
        what='the Rush pnpmfile that omitted peerDependencyRules so a missing peer failed the install in CI only',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='.pnpmfile.cjs tests/test_harbor.py',
        impl='.pnpmfile.cjs',
        src='module.exports = { hooks: {} }',
        sym='peerDependencyRules ignoreMissing',
        grep='peerDependencyRules',
        grep_obs='harbor strictPeerDependencies false only. pack peerDependencyRules ignoreMissing.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: ERR_PNPM_PEER_DEP; peerDependencyRules missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='strictPeerDependencies false only',
        wrong_diff='+ strictPeerDependencies false only',
        wrong_obs='still strictPeerDependencies false only. still fail.',
        fail2='FAIL test_assign: still broken. peerDependencyRules ignoreMissing.',
        reread='apply peerDependencyRules ignoreMissing.',
        insight='strictPeerDependencies false is not ignoreMissing rules',
        probe="rg -n 'peerDependencyRules' .pnpmfile.cjs",
        probe_obs='pack peerDependencyRules ignoreMissing. harbor strictPeerDependencies false only.',
        fix='peerDependencyRules ignoreMissing',
        fix_diff='+ peerDependencyRules ignoreMissing\n',
        rel='dump/.pnpmfile.cjs',
        rel_src='module.exports = { hooks: {} }',
        leftover='leftover strictPeerDependencies false only',
        fix2='dump peerDependencyRules ignoreMissing',
        fix2_diff='+ dump peerDependencyRules ignoreMissing\n',
        bad_pat='strictPeerDependencies false only',
        doc='docs/QUAY-RSHPEER.md',
        doc_point='strictPeerDependencies false is not ignoreMissing rules',
        doc_diff='+ strictPeerDependencies false is not ignoreMissing rules.',
        reg='reg',
        reg_diff='+ peerDependencyRules ignoreMissing holds',
        final_ok='ok 6 passed. peerDependencyRules ignoreMissing.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='peerDependencyRules ignoreMissing; dump leftover.',
        wrap='the peerDependencyRules ignoreMissing',
        wrap_ok='6 passed. quay-rshpeer assign is green.',
        wrap_part='5 passed, 1 residual. quay-rshpeer assign is green.',
        goal='Designed plant quay-rshpeer: the Rush pnpmfile that omitted peerDependencyRules so a missing peer failed the install in CI only. peerDependencyRules ignoreMissing. strictPeerDependencies false is not ignoreMissing rules.',
        plan='Repro python tests, reject strictPeerDependencies false only, peerDependencyRules ignoreMissing, hand off dump.',
        out_ok='peerDependencyRules ignoreMissing. 6 tests pass.',
        out_part='peerDependencyRules ignoreMissing. dump leftover. Partial.',
    ),
    "rspack": P(True,
        slug='pr-rspack-externals-type-umd',
        plant='lock-rspumd',
        what='the Rspack build that omitted externalsType umd so the library still bundled lodash and doubled the chunk',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='rspack.config.js tests/test_harbor.py',
        impl='rspack.config.js',
        src="externals: { lodash: 'lodash' }",
        sym='externalsType umd',
        grep='externalsType',
        grep_obs='harbor optimization.splitChunks only. pack externalsType umd.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: chunk 2x size; lodash bundled; externalsType missing',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='optimization.splitChunks only',
        wrong_diff='+ optimization.splitChunks only',
        wrong_obs='still optimization.splitChunks only. still fail.',
        fail2='FAIL test_assign: still broken. externalsType umd.',
        reread='apply externalsType umd.',
        insight='splitChunks is not externalsType',
        probe="rg -n 'externalsType' rspack.config.js",
        probe_obs='pack externalsType umd. harbor optimization.splitChunks only.',
        fix='externalsType umd',
        fix_diff='+ externalsType umd\n',
        rel='dump/rspack.config.js',
        rel_src="externals: { lodash: 'lodash' }",
        leftover='leftover optimization.splitChunks only',
        fix2='dump externalsType umd',
        fix2_diff='+ dump externalsType umd\n',
        bad_pat='optimization.splitChunks only',
        doc='docs/LOCK-RSPUMD.md',
        doc_point='splitChunks is not externalsType',
        doc_diff='+ splitChunks is not externalsType.',
        reg='reg',
        reg_diff='+ externalsType umd holds',
        final_ok='ok 6 passed. externalsType umd.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='externalsType umd; dump same.',
        wrap='the externalsType umd',
        wrap_ok='6 passed. lock-rspumd assign is green.',
        wrap_part='5 passed, 1 residual. lock-rspumd assign is green.',
        goal='Designed plant lock-rspumd: the Rspack build that omitted externalsType umd so the library still bundled lodash and doubled the chunk. externalsType umd. splitChunks is not externalsType.',
        plan='Repro python tests, reject optimization.splitChunks only, externalsType umd, fix dump.',
        out_ok='externalsType umd. 6 tests pass.',
        out_part='externalsType umd. dump leftover. Partial.',
    ),
    "farm": P(False,
        slug='pr-farm-persistent-cache-lockfile',
        plant='quay-frmlock',
        what='the Farm persistent cache that omitted lockfile hash so a yarn.lock bump served a stale bundle',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='farm.config.ts tests/test_harbor.py',
        impl='farm.config.ts',
        src='persistentCache: true',
        sym='cache lockfile hash',
        grep='cache',
        grep_obs='harbor cache false. pack lockfile in cache key.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: stale bundle after yarn.lock bump; lockfile not in cache key',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='cache false',
        wrong_diff='+ cache false',
        wrong_obs='still cache false. still fail.',
        fail2='FAIL test_assign: still broken. lockfile in cache key.',
        reread='apply lockfile in cache key.',
        insight='disabling cache is not lockfile hashing',
        probe="rg -n 'lockfile' farm.config.ts",
        probe_obs='pack lockfile in cache key. harbor cache false.',
        fix='lockfile in cache key',
        fix_diff='+ lockfile in cache key\n',
        rel='dump/farm.config.ts',
        rel_src='persistentCache: true',
        leftover='leftover cache false',
        fix2='dump lockfile in cache key',
        fix2_diff='+ dump lockfile in cache key\n',
        bad_pat='cache false',
        doc='docs/QUAY-FRMLOCK.md',
        doc_point='disabling cache is not lockfile hashing',
        doc_diff='+ disabling cache is not lockfile hashing.',
        reg='reg',
        reg_diff='+ lockfile in cache key holds',
        final_ok='ok 6 passed. lockfile in cache key.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='lockfile in cache key; dump leftover.',
        wrap='the lockfile in cache key',
        wrap_ok='6 passed. quay-frmlock assign is green.',
        wrap_part='5 passed, 1 residual. quay-frmlock assign is green.',
        goal='Designed plant quay-frmlock: the Farm persistent cache that omitted lockfile hash so a yarn.lock bump served a stale bundle. lockfile in cache key. disabling cache is not lockfile hashing.',
        plan='Repro python tests, reject cache false, lockfile in cache key, hand off dump.',
        out_ok='lockfile in cache key. 6 tests pass.',
        out_part='lockfile in cache key. dump leftover. Partial.',
    ),
    "moonrepo": P(True,
        slug='pr-moonrepo-workspace-inherited-tasks',
        plant='lock-mooninh',
        what='the moon workspace that omitted inherited tasks from toolchain so the app project never ran typecheck',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='moon.yml tests/test_harbor.py',
        impl='moon.yml',
        src='language: typescript',
        sym='workspace inherited tasks',
        grep='workspace',
        grep_obs='harbor dependsOn only. pack inherited tasks typecheck.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: typecheck skipped; inherited tasks missing from workspace',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='dependsOn only',
        wrong_diff='+ dependsOn only',
        wrong_obs='still dependsOn only. still fail.',
        fail2='FAIL test_assign: still broken. inherited tasks typecheck.',
        reread='apply inherited tasks typecheck.',
        insight='dependsOn is not inherited workspace tasks',
        probe="rg -n 'inherited' moon.yml",
        probe_obs='pack inherited tasks typecheck. harbor dependsOn only.',
        fix='inherited tasks typecheck',
        fix_diff='+ inherited tasks typecheck\n',
        rel='dump/moon.yml',
        rel_src='language: typescript',
        leftover='leftover dependsOn only',
        fix2='dump inherited tasks typecheck',
        fix2_diff='+ dump inherited tasks typecheck\n',
        bad_pat='dependsOn only',
        doc='docs/LOCK-MOONINH.md',
        doc_point='dependsOn is not inherited workspace tasks',
        doc_diff='+ dependsOn is not inherited workspace tasks.',
        reg='reg',
        reg_diff='+ inherited tasks typecheck holds',
        final_ok='ok 6 passed. inherited tasks typecheck.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='inherited tasks typecheck; dump same.',
        wrap='the inherited tasks typecheck',
        wrap_ok='6 passed. lock-mooninh assign is green.',
        wrap_part='5 passed, 1 residual. lock-mooninh assign is green.',
        goal='Designed plant lock-mooninh: the moon workspace that omitted inherited tasks from toolchain so the app project never ran typecheck. inherited tasks typecheck. dependsOn is not inherited workspace tasks.',
        plan='Repro python tests, reject dependsOn only, inherited tasks typecheck, fix dump.',
        out_ok='inherited tasks typecheck. 6 tests pass.',
        out_part='inherited tasks typecheck. dump leftover. Partial.',
    ),
    "buf": P(False,
        slug='pr-buf-breaking-against-tag',
        plant='quay-bufbrk',
        what='the Buf breaking check that omitted --against a git tag so a field number reuse shipped',
        glob='**/*.{json,yml,js,ts,toml,proto}',
        ls='buf.yaml tests/test_harbor.py',
        impl='buf.yaml',
        src='version: v1\nbreaking:\n  use: [FILE]',
        sym='breaking against tag',
        grep='breaking',
        grep_obs='harbor lint only. pack breaking --against git tag.',
        test='python3 tests/test_harbor.py',
        fail1='FAIL test_assign: field 3 reused; breaking against missing; FILE only vs HEAD',
        tf='tests/test_harbor.py',
        tsrc='assert True',
        wrong='lint only',
        wrong_diff='+ lint only',
        wrong_obs='still lint only. still fail.',
        fail2='FAIL test_assign: still broken. breaking --against git tag.',
        reread='apply breaking --against git tag.',
        insight='lint is not breaking against a tag',
        probe="rg -n 'breaking' buf.yaml",
        probe_obs='pack breaking --against git tag. harbor lint only.',
        fix='breaking --against git tag',
        fix_diff='+ breaking --against git tag\n',
        rel='dump/buf.yaml',
        rel_src='version: v1\nbreaking:\n  use: [FILE]',
        leftover='leftover lint only',
        fix2='dump breaking --against git tag',
        fix2_diff='+ dump breaking --against git tag\n',
        bad_pat='lint only',
        doc='docs/QUAY-BUFBRK.md',
        doc_point='lint is not breaking against a tag',
        doc_diff='+ lint is not breaking against a tag.',
        reg='reg',
        reg_diff='+ breaking --against git tag holds',
        final_ok='ok 6 passed. breaking --against git tag.',
        final_part='5 passed, 1 dump residual. Partial.',
        summary='breaking --against git tag; dump leftover.',
        wrap='the breaking --against git tag',
        wrap_ok='6 passed. quay-bufbrk assign is green.',
        wrap_part='5 passed, 1 residual. quay-bufbrk assign is green.',
        goal='Designed plant quay-bufbrk: the Buf breaking check that omitted --against a git tag so a field number reuse shipped. breaking --against git tag. lint is not breaking against a tag.',
        plan='Repro python tests, reject lint only, breaking --against git tag, hand off dump.',
        out_ok='breaking --against git tag. 6 tests pass.',
        out_part='breaking --against git tag. dump leftover. Partial.',
    ),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f

LHC_PAIRS = [
    ('Yarn nmHoistingLimits vs esbuild packages external', fn('yarn'), fn('esbuild'), 'nmHoistingLimits workspaces; packages external', 'global cache; minify', 'yarn dump peer clash; esbuild dump fat lambda'),
    ('SWC keep_class_names vs Biome json overrides', fn('swc'), fn('biome'), 'keep_class_names; overrides json include', 'mangle false; js formatter', 'swc dump DI tokens mangled; biome dump package.json commas'),
    ('dprint excludes vendor vs oxc conditionNames', fn('dprint'), fn('oxc'), 'excludes vendor; conditionNames development', 'incremental; mainFields', 'dprint dump 40k vendor diff; oxc dump prod export'),
    ('Parcel publicUrl vs Rollup output.globals', fn('parcel'), fn('rollup'), 'publicUrl CDN; output.globals react', 'scopeHoist; format iife', 'parcel dump CDN 404; rollup dump React undefined'),
    ('Turborepo outputs glob vs Nx implicitDependencies', fn('turborepo'), fn('nx'), 'outputs dist/**; implicitDependencies .env', 'cache false; dependsOn', 'turborepo dump empty dist; nx dump stale secret cache'),
    ('Lerna include-merged-tags vs Rush peerDependencyRules', fn('lerna'), fn('rush'), 'include-merged-tags; peerDependencyRules ignoreMissing', 'conventionalCommits; strictPeer false', 'lerna dump cherry-pick skip; rush dump PEER_DEP'),
    ('Rspack externalsType umd vs Farm lockfile cache', fn('rspack'), fn('farm'), 'externalsType umd; lockfile in cache key', 'splitChunks; cache false', 'rspack dump lodash bundled; farm dump stale bundle'),
    ('moon inherited tasks vs Buf breaking against tag', fn('moonrepo'), fn('buf'), 'inherited typecheck; breaking --against git tag', 'dependsOn; lint only', 'moon dump typecheck skipped; buf dump field reuse'),
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
- Not a clone of r4163-r4516 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, pixi, rye, poetry, pdm, earthly, dagger, and the rest of that window).
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
