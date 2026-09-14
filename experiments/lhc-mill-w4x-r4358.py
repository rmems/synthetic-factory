#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4x: unused plants after r4357.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka,
and any plant in r4163-r4357. IDs lhc-rNNNN-pr-*. meta.generator=grok-4.6.
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
STATE = Path("/tmp/lhc_mill_g46_w4x_state.json")
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

def pnpm_peer(rnd):
    return expand(rnd, {
        "slug": "pr-pnpm-peer-auto-install-strict",
        "success": True, "tests": 6, "plant": "lock-pnpmp",
        "what": "the pnpm peer dependency that auto-installed a second React",
        "glob": "**/{package.json,pnpm-workspace.yaml,.npmrc}",
        "ls": "package.json packages/harbor/package.json packages/pack/package.json .npmrc",
        "impl": ".npmrc",
        "impl_src": "auto-install-peers=true\nstrict-peer-dependencies=false\n# harbor wants react@18; a nested dep pulled react@19 into a second copy\n",
        "sym": "auto-install-peers", "grep": "auto-install-peers|strict-peer|react",
        "grep_obs": ".npmrc auto-install-peers true. pack .npmrc false plus peer react@18 in root.",
        "test": "pnpm install && pnpm test",
        "fail1": "FAIL test_assign: Invalid hook call; two Reacts: 18.3.1 from harbor and 19.0.0 auto-installed",
        "fail_name": "test_assign", "test_file": "packages/harbor/package.test.js",
        "test_src": "assert.equal(require('react').version, '18.3.1')",
        "wrong_name": "packageExtensions to alias react@19 onto 18",
        "wrong_diff": "+ packageExtensions: { leftover: { peerDependencies: { react: '19' } } }",
        "wrong_obs": "that publishes the 19 peer further; still two copies.",
        "test_one": "pnpm test --filter harbor",
        "fail2": "FAIL test_assign: still two Reacts. packageExtensions did not dedupe.",
        "reread": "auto-install-peers=false and hoist react@18 at the workspace root as a peer.",
        "insight": "turn off auto-install-peers; declare react@18 once at the root.",
        "probe": "pnpm why react; cat .npmrc",
        "probe_obs": "two react versions. pack workspace has a single root react@18.",
        "fix_name": "auto-install-peers false plus root react@18",
        "fix_diff": "+ auto-install-peers=false\n+ strict-peer-dependencies=true\n",
        "fix_obs": "patched .npmrc; root peer added.",
        "fail3": "PASS test_assign\nFAIL pack leftover: packages/pack still auto-installs react@19",
        "rel": "packages/pack/package.json",
        "rel_src": "peerDependencies missing; relies on auto-install-peers",
        "fix2_name": "pack peer react@18",
        "fix2_diff": "+ \"peerDependencies\": { \"react\": \"18.3.1\" }",
        "fix2_obs": "patched pack peer.",
        "pass_mid": "PASS 6.",
        "bad_pat": "packageExtensions",
        "grep2": "none.",
        "doc": "docs/PEERS.md", "doc_point": "do not auto-install a second React",
        "doc_diff": "+ auto-install-peers=false; hoist react@18.",
        "reg_name": "test_assign single react",
        "reg_diff": "+ only react@18.3.1",
        "full_test": "pnpm test",
        "final": "ok 6 passed. pnpm has one React.",
        "summary": "auto-install-peers false; pack peer 18. 6 tests pass.",
        "wrap": "the single-react path",
        "wrap_obs": "6 passed. pnpm assign no longer auto-installs React 19.",
        "goal": "Designed plant lock-pnpmp: pnpm auto-install-peers pulled React 19 beside 18 so hooks broke. auto-install-peers=false and root react@18. packageExtensions did not dedupe.",
        "plan": "Repro pnpm test, reject packageExtensions, disable auto-install-peers, fix pack peer.",
        "outcome": "Single React 18. 6 pnpm tests pass.",
    })


def bun_lock(rnd):
    return expand(rnd, {
        "slug": "pr-bun-lockfile-text-workspace-proto",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-bunlk",
        "what": "the Bun lockfile that dropped a workspace protocol after bun install --frozen",
        "glob": "**/{package.json,bun.lock,bun.lockb}",
        "ls": "package.json packages/harbor/package.json bun.lock tests/test_bun.py",
        "impl": "packages/harbor/package.json",
        "impl_src": "{\n  \"dependencies\": {\n    \"pack\": \"workspace:*\"\n  }\n}\n# bun.lock recorded pack@1.0.0 from registry after a publish, frozen install misses workspace\n",
        "sym": "workspace:*", "grep": "workspace:|overrides|catalog",
        "grep_obs": "harbor workspace:*. bun.lock has pack@1.0.0 registry tarball.",
        "test": "bun install --frozen-lockfile && bun test",
        "fail1": "FAIL test_assign: Cannot find package pack; frozen lockfile resolved registry 1.0.0 not workspace",
        "fail_name": "test_assign", "test_file": "tests/test_bun.py",
        "test_src": "assert require('pack').assign(4) == 5",
        "wrong_name": "bun install without --frozen to refresh",
        "wrong_diff": "+ bun install",
        "wrong_obs": "CI is --frozen-lockfile; unfrozen install is not allowed on the merge gate.",
        "test_one": "bun test",
        "fail2": "FAIL CI: still frozen. rewriting the lock locally does not land in CI.",
        "reread": "Restore pack@workspace:* in bun.lock [packages] and add an override so the registry tarball cannot win.",
        "insight": "overrides: { pack: workspace:* } plus a regenerated bun.lock; do not drop --frozen.",
        "probe": "rg -n 'workspace:|pack@' bun.lock package.json",
        "probe_obs": "root missing override. pack workspace is a file: path in a sibling lock.",
        "fix_name": "root override workspace protocol",
        "fix_diff": "+ \"overrides\": { \"pack\": \"workspace:*\" }\n",
        "fix_obs": "patched override; lock regenerated. dump leftover registry pin.",
        "fail3": "PASS test_assign\nFAIL pack leftover: dump still registry-pinned in bun.lock",
        "rel": "packages/pack/package.json",
        "rel_src": "dump depends on leftover@1.0.0 from registry",
        "fix2_name": "handoff dump workspace override",
        "fix2_diff": "+ /* TODO dump leftover workspace:* override */",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "bun install$",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/LOCK.md", "doc_point": "workspace:* must stay in bun.lock under --frozen",
        "doc_diff": "+ do not drop --frozen. dump leftover.",
        "reg_name": "test_assign pack workspace",
        "reg_diff": "+ require('pack') is the workspace copy",
        "full_test": "bun install --frozen-lockfile && bun test",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "workspace override; dump leftover.",
        "wrap": "the workspace override",
        "wrap_obs": "5 passed, 1 residual. Bun assign pack is workspace:*.",
        "goal": "Designed plant quay-bunlk: Bun frozen lockfile resolved pack from the registry after a publish, dropping workspace:*. Root override workspace:*. Unfrozen install is not a CI fix. dump may remain.",
        "plan": "Repro bun --frozen, reject unfrozen install, override, hand off dump.",
        "outcome": "workspace override. dump leftover. Partial.",
    })


def hono_rpc(rnd):
    return expand(rnd, {
        "slug": "pr-hono-rpc-client-path-slash",
        "success": True, "tests": 6, "plant": "lock-honorpc",
        "what": "the Hono RPC client that doubled the slash on a base URL",
        "glob": "**/*.{ts,tsx,json}",
        "ls": "src/harbor.ts src/pack.ts tests/harbor.test.ts",
        "impl": "src/harbor.ts",
        "impl_src": "const client = hc<App>('https://api.example.com/', { fetch })\nawait client.assign.$get()  // requests https://api.example.com//assign\n",
        "sym": "hc<App>", "grep": "hc<|baseUrl|assign",
        "grep_obs": "harbor.ts base with trailing slash. pack.ts base without slash.",
        "test": "vitest run",
        "fail1": "FAIL test_assign: 404 / /assign doubled slash; route is /assign",
        "fail_name": "test_assign", "test_file": "tests/harbor.test.ts",
        "test_src": "expect(await client.assign.$get()).toEqual({ n: 5 })",
        "wrong_name": "client.assign.$get({ slash: false })",
        "wrong_diff": "+ await client['/assign'].$get()",
        "wrong_obs": "typed client already has assign; changing the key still prefixes the trailing-slash base.",
        "test_one": "vitest run -t assign",
        "fail2": "FAIL test_assign: still //. the base URL is the bug.",
        "reread": "Pass hc<App>('https://api.example.com') with no trailing slash.",
        "insight": "trim the base URL slash; do not rename the RPC key.",
        "probe": "rg -n 'hc<' src",
        "probe_obs": "pack.ts no trailing slash. harbor.ts has one.",
        "fix_name": "trim base URL slash",
        "fix_diff": "+ const client = hc<App>('https://api.example.com', { fetch })\n",
        "fix_obs": "patched base.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.ts dump client still trailing slash",
        "rel": "src/pack.ts",
        "rel_src": "hc<App>('https://api.example.com/')",
        "fix2_name": "dump base trim",
        "fix2_diff": "+ hc<App>('https://api.example.com')",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "client\\['/assign'\\]",
        "grep2": "none.",
        "doc": "docs/RPC.md", "doc_point": "Hono hc base URL has no trailing slash",
        "doc_diff": "+ doubled slash 404s /assign.",
        "reg_name": "test_assign",
        "reg_diff": "+ GET https://api.example.com/assign",
        "full_test": "vitest run",
        "final": "ok 6 passed. Hono RPC base has no trailing slash.",
        "summary": "trimmed base; dump same. 6 tests pass.",
        "wrap": "the trimmed base",
        "wrap_obs": "6 passed. Hono assign client hits /assign once.",
        "goal": "Designed plant lock-honorpc: Hono hc base ended with / so /assign doubled. Trim the base. Renaming the RPC key does not fix the prefix.",
        "plan": "Repro vitest, reject key rename, trim slash, fix dump.",
        "outcome": "Trimmed hc base. 6 Hono tests pass.",
    })


def trpc_superjson(rnd):
    return expand(rnd, {
        "slug": "pr-trpc-superjson-transformer-pair",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-trpcjson",
        "what": "the tRPC procedure that returned a Date without a matching transformer",
        "glob": "**/*.{ts,tsx}",
        "ls": "src/harbor.ts src/pack.ts tests/harbor.test.ts",
        "impl": "src/harbor.ts",
        "impl_src": "export const assign = publicProcedure.query(() => ({ at: new Date() }))\n// initTRPC.create() without transformer; client JSON.parse leaves a string\n",
        "sym": "publicProcedure", "grep": "transformer|superjson|initTRPC",
        "grep_obs": "harbor.ts initTRPC.create(). pack.ts initTRPC.create({ transformer: superjson }).",
        "test": "vitest run",
        "fail1": "FAIL test_assign: at instanceof Date is false; got ISO string",
        "fail_name": "test_assign", "test_file": "tests/harbor.test.ts",
        "test_src": "expect(res.at).toBeInstanceOf(Date)",
        "wrong_name": "JSON.parse reviver only on the client",
        "wrong_diff": "+ JSON.parse(body, (_, v) => typeof v === 'string' && /Z$/.test(v) ? new Date(v) : v)",
        "wrong_obs": "reviver also converts random ISO-like strings; server still serialized without superjson metadata.",
        "test_one": "vitest run -t assign",
        "fail2": "FAIL test_assign: dump field 'version' became a Date. reviver is too wide.",
        "reread": "Set transformer: superjson on both initTRPC.create and createTRPCProxyClient.",
        "insight": "matching superjson transformers; do not guess ISO strings on the client.",
        "probe": "rg -n 'transformer|superjson' src",
        "probe_obs": "pack.ts both sides superjson. harbor.ts none.",
        "fix_name": "superjson on router and client",
        "fix_diff": "+ const t = initTRPC.create({ transformer: superjson })\n+ createTRPCProxyClient<App>({ transformer: superjson, links })\n",
        "fix_obs": "patched pair. dump client leftover no transformer.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.ts dump client missing transformer",
        "rel": "src/pack.ts",
        "rel_src": "createTRPCProxyClient<Dump>({ links }) // no transformer",
        "fix2_name": "handoff dump transformer",
        "fix2_diff": "+ // TODO dump client transformer: superjson",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "JSON.parse\\(body",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/TRANSFORMER.md", "doc_point": "superjson must match on both ends",
        "doc_diff": "+ ISO reviver is too wide. dump leftover.",
        "reg_name": "test_assign Date",
        "reg_diff": "+ at instanceof Date",
        "full_test": "vitest run",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "superjson pair; dump leftover.",
        "wrap": "the matching transformer",
        "wrap_obs": "5 passed, 1 residual. tRPC assign Dates survive the wire.",
        "goal": "Designed plant quay-trpcjson: tRPC returned a Date without superjson so the client got a string. Matching transformers. ISO reviver is too wide. dump may remain.",
        "plan": "Repro vitest, reject ISO reviver, superjson both sides, hand off dump.",
        "outcome": "Matching superjson. dump leftover. Partial.",
    })


def drizzle_rqb(rnd):
    return expand(rnd, {
        "slug": "pr-drizzle-rqb-relation-name",
        "success": True, "tests": 6, "plant": "lock-drizrqb",
        "what": "the Drizzle relational query that used the table name not the relation name",
        "glob": "**/*.{ts,sql}",
        "ls": "src/harbor.ts src/pack.ts tests/harbor.test.ts",
        "impl": "src/harbor.ts",
        "impl_src": "db.query.slips.findMany({ with: { berth: true } })\n// relations() registered the name as berths (plural); 'berth' is unknown\n",
        "sym": "findMany", "grep": "relations\\(|with:|berth",
        "grep_obs": "harbor.ts with.berth. schema relations berths. pack.ts with.berths.",
        "test": "vitest run",
        "fail1": "FAIL test_assign: DrizzleQueryError: Could not find relation 'berth' on table 'slips'",
        "fail_name": "test_assign", "test_file": "tests/harbor.test.ts",
        "test_src": "expect(rows[0].berths[0].id).toBe(5)",
        "wrong_name": "alias the table as berth in the query",
        "wrong_diff": "+ db.query.slips.findMany({ with: { berth: { relationName: 'berth' } } })",
        "wrong_obs": "relationName in with is not how RQB looks up the key; still unknown.",
        "test_one": "vitest run -t assign",
        "fail2": "FAIL test_assign: still Could not find relation 'berth'.",
        "reread": "Use the key from relations(): with: { berths: true } matching slipsRelations.",
        "insight": "with.berths matches relations() export; do not invent relationName in with.",
        "probe": "rg -n 'slipsRelations|berths' src",
        "probe_obs": "schema: slipsRelations berths: many(berths). pack.ts with.berths.",
        "fix_name": "with berths plural",
        "fix_diff": "+ db.query.slips.findMany({ with: { berths: true } })\n",
        "fix_obs": "patched with key.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.ts dump still with.berth",
        "rel": "src/pack.ts",
        "rel_src": "db.query.dumps.findMany({ with: { berth: true } })",
        "fix2_name": "dump with berths",
        "fix2_diff": "+ with: { berths: true }",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "relationName: 'berth'",
        "grep2": "none.",
        "doc": "docs/RQB.md", "doc_point": "RQB with keys match relations() names",
        "doc_diff": "+ relationName inside with is not a lookup key.",
        "reg_name": "test_assign berths",
        "reg_diff": "+ rows[0].berths[0].id==5",
        "full_test": "vitest run",
        "final": "ok 6 passed. Drizzle RQB uses berths.",
        "summary": "with.berths; dump same. 6 tests pass.",
        "wrap": "the relations() key",
        "wrap_obs": "6 passed. Drizzle assign with.berths matches the schema.",
        "goal": "Designed plant lock-drizrqb: Drizzle RQB with.berth missed relations() key berths. Use the relations() name. relationName inside with is not a lookup.",
        "plan": "Repro vitest, reject relationName in with, use berths, fix dump.",
        "outcome": "with.berths. 6 Drizzle tests pass.",
    })


def seaorm_rel(rnd):
    return expand(rnd, {
        "slug": "pr-seaorm-related-select-alias",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-seaorm",
        "what": "the SeaORM related select that aliased the join onto the parent table",
        "glob": "**/*.{rs,toml}",
        "ls": "src/harbor.rs src/pack.rs tests/harbor.rs",
        "impl": "src/harbor.rs",
        "impl_src": "let r = slips::Entity::find()\n    .find_also_related(berths::Entity)\n    .into_model::<Slip>() // drops the berth columns; alias collision on id\n    .all(db).await?;\n",
        "sym": "find_also_related", "grep": "find_also_related|into_model|from_query_result",
        "grep_obs": "harbor.rs into_model Slip. pack.rs into_model<(Slip, Option<Berth>)>.",
        "test": "cargo test",
        "fail1": "FAIL test_assign: column id specified more than once; berth.id aliased onto slip.id",
        "fail_name": "test_assign", "test_file": "tests/harbor.rs",
        "test_src": "assert_eq!(row.1.unwrap().id, 5);",
        "wrong_name": "select_only plus column alias id as bid",
        "wrong_diff": "+ .select_only().column_as(berths::Column::Id, \"id\")",
        "wrong_obs": "column_as named 'id' still collides with slips.id.",
        "test_one": "cargo test test_assign",
        "fail2": "FAIL test_assign: still duplicate id. alias must not reuse id.",
        "reread": "into_model::<(Slip, Option<Berth>)>() or find_with_related so each table has its model.",
        "insight": "tuple model (Slip, Option<Berth>); do not alias berth.id as id.",
        "probe": "rg -n 'find_also_related|into_model' src",
        "probe_obs": "pack.rs tuple model. harbor.rs Slip only.",
        "fix_name": "tuple into_model",
        "fix_diff": "+ .into_model::<(Slip, Option<Berth>)>()\n",
        "fix_obs": "patched tuple. dump leftover into_model Dump.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.rs dump into_model Dump",
        "rel": "src/pack.rs",
        "rel_src": ".find_also_related(berths::Entity).into_model::<Dump>()",
        "fix2_name": "handoff dump tuple model",
        "fix2_diff": "+ // TODO dump into_model::<(Dump, Option<Berth>)>",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "column_as\\(berths::Column::Id, \"id\"\\)",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/RELATED.md", "doc_point": "find_also_related needs a tuple model",
        "doc_diff": "+ aliasing id as id still collides. dump leftover.",
        "reg_name": "test_assign",
        "reg_diff": "+ row.1.unwrap().id==5",
        "full_test": "cargo test",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "tuple model; dump leftover.",
        "wrap": "the tuple-model path",
        "wrap_obs": "5 passed, 1 residual. SeaORM assign keeps berth.id.",
        "goal": "Designed plant quay-seaorm: SeaORM find_also_related into_model Slip collided on id. Tuple (Slip, Option<Berth>). Aliasing berth.id as id still collides. dump may remain.",
        "plan": "Repro cargo test, reject id-as-id, tuple model, hand off dump.",
        "outcome": "Tuple related model. dump leftover. Partial.",
    })


def surreal_live(rnd):
    return expand(rnd, {
        "slug": "pr-surreal-live-select-diff",
        "success": True, "tests": 6, "plant": "lock-surlive",
        "what": "the SurrealDB LIVE SELECT that used DIFF on a record without an id",
        "glob": "**/*.{rs,surql,js}",
        "ls": "src/harbor.surql src/pack.surql tests/test_harbor.js",
        "impl": "src/harbor.surql",
        "impl_src": "LIVE SELECT DIFF FROM slip WHERE n > 0;\n-- DIFF actions need a record id; this SELECT projects n only\n",
        "sym": "LIVE SELECT DIFF", "grep": "LIVE SELECT|DIFF|VALUE",
        "grep_obs": "harbor.surql LIVE SELECT DIFF. pack.surql LIVE SELECT FROM slip (full record).",
        "test": "node tests/test_harbor.js",
        "fail1": "FAIL test_assign: live notification action=DIFF but result has no id; client cannot apply patch",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.js",
        "test_src": "assert.equal(note.result.id, 'slip:4')",
        "wrong_name": "LIVE SELECT VALUE n",
        "wrong_diff": "+ LIVE SELECT VALUE n FROM slip WHERE n > 0;",
        "wrong_obs": "VALUE drops the id too; still cannot apply a patch.",
        "test_one": "node tests/test_harbor.js --filter assign",
        "fail2": "FAIL test_assign: VALUE notifications are scalars. still no id.",
        "reread": "LIVE SELECT FROM slip WHERE n > 0 (full record) or DIFF only when id is projected.",
        "insight": "full-record LIVE SELECT; DIFF without id is not patchable.",
        "probe": "rg -n 'LIVE SELECT' src",
        "probe_obs": "pack.surql LIVE SELECT FROM slip. harbor.surql DIFF.",
        "fix_name": "LIVE SELECT full record",
        "fix_diff": "+ LIVE SELECT FROM slip WHERE n > 0;\n",
        "fix_obs": "patched live.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.surql dump LIVE SELECT DIFF",
        "rel": "src/pack.surql",
        "rel_src": "LIVE SELECT DIFF FROM dump;",
        "fix2_name": "dump full-record live",
        "fix2_diff": "+ LIVE SELECT FROM dump;",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "LIVE SELECT VALUE n",
        "grep2": "none.",
        "doc": "docs/LIVE.md", "doc_point": "DIFF live queries must include record id",
        "doc_diff": "+ VALUE also drops id. use full records.",
        "reg_name": "test_assign live id",
        "reg_diff": "+ note.result.id == slip:4",
        "full_test": "node tests/test_harbor.js",
        "final": "ok 6 passed. Surreal live notifications include id.",
        "summary": "full-record LIVE SELECT; dump same. 6 tests pass.",
        "wrap": "the full-record live",
        "wrap_obs": "6 passed. Surreal assign live notifications carry id.",
        "goal": "Designed plant lock-surlive: SurrealDB LIVE SELECT DIFF projected no id so the client could not apply a patch. Full-record LIVE SELECT. VALUE also drops id.",
        "plan": "Repro node tests, reject VALUE, full record, fix dump.",
        "outcome": "Full-record live. 6 Surreal tests pass.",
    })


def edgedb_card(rnd):
    return expand(rnd, {
        "slug": "pr-edgedb-cardinality-assert-single",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-edgcard",
        "what": "the EdgeDB query that asserted single on a multi link",
        "glob": "**/*.{edgeql,esdl,py}",
        "ls": "src/harbor.edgeql src/pack.edgeql tests/test_harbor.py",
        "impl": "src/harbor.edgeql",
        "impl_src": "select assert_single((select Slip filter .n = 4).berths);\n-- berths is multi; assert_single throws CardinalityViolationError\n",
        "sym": "assert_single", "grep": "assert_single|multi|berths",
        "grep_obs": "harbor.edgeql assert_single on .berths. pack.edgeql select .berths without assert.",
        "test": "python3 tests/test_harbor.py",
        "fail1": "FAIL test_assign: CardinalityViolationError: assert_single got 2 elements",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert len(row.berths) == 2",
        "wrong_name": "assert_distinct instead",
        "wrong_diff": "+ select assert_distinct((select Slip filter .n = 4).berths);",
        "wrong_obs": "assert_distinct still returns a set; the client codec expected an object not an array.",
        "test_one": "python3 tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: codec mismatch. distinct is not single.",
        "reread": "Drop assert_single and type the client as a list, or pick one berth with limit 1 explicitly.",
        "insight": "select .berths as a set; do not assert_single a multi link.",
        "probe": "rg -n 'assert_single|berths' src",
        "probe_obs": "pack.edgeql select Slip { berths: { id } }. harbor uses assert_single.",
        "fix_name": "shape with multi berths",
        "fix_diff": "+ select Slip { n, berths: { id } } filter .n = 4;\n",
        "fix_obs": "patched shape. dump leftover assert_single.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.edgeql dump assert_single on dumps",
        "rel": "src/pack.edgeql",
        "rel_src": "select assert_single((select Dump).dumps);",
        "fix2_name": "handoff dump shape",
        "fix2_diff": "+ # TODO select Dump { dumps: { id } }",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "assert_distinct",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/CARD.md", "doc_point": "do not assert_single a multi link",
        "doc_diff": "+ assert_distinct is not single. dump leftover.",
        "reg_name": "test_assign berths",
        "reg_diff": "+ two berths without CardinalityViolation",
        "full_test": "python3 tests/test_harbor.py",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "multi shape; dump leftover.",
        "wrap": "the multi shape",
        "wrap_obs": "5 passed, 1 residual. EdgeDB assign returns both berths.",
        "goal": "Designed plant quay-edgcard: EdgeDB assert_single on multi link berths raised CardinalityViolation. Use a shape. assert_distinct is not single. dump may remain.",
        "plan": "Repro pytest, reject assert_distinct, shape, hand off dump.",
        "outcome": "Multi link shape. dump leftover. Partial.",
    })

def dgraph_upsert(rnd):
    return expand(rnd, {
        "slug": "pr-dgraph-upsert-uid-cond",
        "success": True, "tests": 6, "plant": "lock-dgup",
        "what": "the Dgraph upsert that used uid(v) in a mutation without a Cond",
        "glob": "**/*.{graphql,dql,go}",
        "ls": "src/harbor.dql src/pack.dql tests/test_harbor.go",
        "impl": "src/harbor.dql",
        "impl_src": "upsert {\n  query { q(func: eq(slip, 4)) { v as uid } }\n  mutation { set { uid(v) <slip> \"5\" . } }  # no Cond; blank uid when q empty\n}\n",
        "sym": "uid(v)", "grep": "upsert|uid\\(v\\)|Cond",
        "grep_obs": "harbor.dql mutation uid(v) no Cond. pack.dql @if(eq(len(v),1)).",
        "test": "go test ./...",
        "fail1": "FAIL TestAssign: mutation with uid() and empty uid list; rdf invalid",
        "fail_name": "TestAssign", "test_file": "tests/test_harbor.go",
        "test_src": "if got != 5 { t.Fatalf(\"%d\", got) }",
        "wrong_name": "always create a new uid when v is empty",
        "wrong_diff": "+ mutation { set { _:new <slip> \"5\" . } }",
        "wrong_obs": "now every upsert inserts a new node even when q found one; duplicates.",
        "test_one": "go test ./... -run TestAssign",
        "fail2": "FAIL TestAssign: 3 slips with n=5. blank node is not Cond.",
        "reread": "Two mutations: Cond eq(len(v),1) set uid(v); Cond eq(len(v),0) set _:new.",
        "insight": "Cond on len(v); do not always insert _:new.",
        "probe": "rg -n 'Cond|uid\\(v\\)' src",
        "probe_obs": "pack.dql two Cond mutations. harbor.dql none.",
        "fix_name": "Cond len(v) split",
        "fix_diff": "+ mutation @if(eq(len(v), 1)) { set { uid(v) <slip> \"5\" . } }\n+ mutation @if(eq(len(v), 0)) { set { _:new <slip> \"5\" . } }\n",
        "fix_obs": "patched Cond.",
        "fail3": "PASS TestAssign\nFAIL pack leftover: src/pack.dql dump upsert no Cond",
        "rel": "src/pack.dql",
        "rel_src": "mutation { set { uid(d) <dump> \"1\" . } }",
        "fix2_name": "dump Cond split",
        "fix2_diff": "+ mutation @if(eq(len(d),1)) { set { uid(d) <dump> \"1\" . } }",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "_:new <slip>",
        "grep2": "none in the unconditioned path.",
        "doc": "docs/UPSERT.md", "doc_point": "uid(v) mutations need Cond on len(v)",
        "doc_diff": "+ always _:new duplicates found nodes.",
        "reg_name": "TestAssign",
        "reg_diff": "+ one slip 5; no blank uid error",
        "full_test": "go test ./...",
        "final": "ok 6 passed. Dgraph upsert uses Cond.",
        "summary": "Cond len(v); dump same. 6 tests pass.",
        "wrap": "the Cond split",
        "wrap_obs": "6 passed. Dgraph assign upsert no longer writes uid().",
        "goal": "Designed plant lock-dgup: Dgraph upsert mutated uid(v) with no Cond so an empty query wrote uid(). Split on len(v). Always _:new duplicates.",
        "plan": "Repro go test, reject always _:new, Cond split, fix dump.",
        "outcome": "Cond upsert. 6 Dgraph tests pass.",
    })


def arango_aql(rnd):
    return expand(rnd, {
        "slug": "pr-arango-aql-subquery-limit-early",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-arangoq",
        "what": "the Arango AQL subquery that LIMITed before FILTER",
        "glob": "**/*.{js,aql}",
        "ls": "src/harbor.aql src/pack.aql tests/test_harbor.js",
        "impl": "src/harbor.aql",
        "impl_src": "FOR s IN slips\n  LIMIT 1\n  FILTER s.n == 4\n  RETURN s  /* LIMIT ran first so n==4 may be dropped */\n",
        "sym": "LIMIT 1", "grep": "LIMIT|FILTER|FOR s",
        "grep_obs": "harbor.aql LIMIT then FILTER. pack.aql FILTER then LIMIT.",
        "test": "node tests/test_harbor.js",
        "fail1": "FAIL test_assign: [] empty; the first slip is n=1 so LIMIT 1 dropped n=4",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.js",
        "test_src": "assert.equal(rows[0].n, 4)",
        "wrong_name": "SORT s.n DESC then LIMIT 1",
        "wrong_diff": "+ SORT s.n DESC\n+ LIMIT 1\n+ FILTER s.n == 4",
        "wrong_obs": "SORT+LIMIT still before FILTER; n=4 is kept only by luck of DESC.",
        "test_one": "node tests/test_harbor.js --filter assign",
        "fail2": "FAIL test_assign on n=4 when a larger n exists. FILTER must precede LIMIT.",
        "reread": "FILTER s.n == 4 then LIMIT 1. AQL evaluation is top to bottom.",
        "insight": "FILTER then LIMIT; SORT+LIMIT before FILTER is still wrong.",
        "probe": "rg -n 'FILTER|LIMIT' src",
        "probe_obs": "pack.aql FILTER then LIMIT. harbor.aql LIMIT first.",
        "fix_name": "FILTER before LIMIT",
        "fix_diff": "+ FOR s IN slips\n+   FILTER s.n == 4\n+   LIMIT 1\n+   RETURN s\n",
        "fix_obs": "patched order. dump leftover LIMIT first.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.aql dump LIMIT then FILTER",
        "rel": "src/pack.aql",
        "rel_src": "FOR d IN dumps LIMIT 1 FILTER d.n == 0 RETURN d",
        "fix2_name": "handoff dump FILTER first",
        "fix2_diff": "+ /* TODO dump FILTER then LIMIT */",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "SORT s.n DESC",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/AQL.md", "doc_point": "FILTER before LIMIT",
        "doc_diff": "+ SORT+LIMIT still precedes FILTER. dump leftover.",
        "reg_name": "test_assign n=4",
        "reg_diff": "+ rows[0].n==4",
        "full_test": "node tests/test_harbor.js",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "FILTER then LIMIT; dump leftover.",
        "wrap": "the FILTER-first path",
        "wrap_obs": "5 passed, 1 residual. Arango assign FILTERs before LIMIT.",
        "goal": "Designed plant quay-arangoq: Arango AQL LIMIT 1 before FILTER dropped n=4. FILTER then LIMIT. SORT+LIMIT before FILTER is still wrong. dump may remain.",
        "plan": "Repro node tests, reject SORT+LIMIT first, FILTER first, hand off dump.",
        "outcome": "FILTER then LIMIT. dump leftover. Partial.",
    })


def zeromq_router(rnd):
    return expand(rnd, {
        "slug": "pr-zeromq-router-mandatory-identity",
        "success": True, "tests": 6, "plant": "lock-zmqrtr",
        "what": "the ZeroMQ ROUTER that sent without an identity frame",
        "glob": "**/*.{py,c,h}",
        "ls": "src/harbor.py src/pack.py tests/test_harbor.py",
        "impl": "src/harbor.py",
        "impl_src": "sock = ctx.socket(zmq.ROUTER)\nsock.send_multipart([b'payload'])  # missing identity; ROUTER drops or misroutes\n",
        "sym": "ROUTER", "grep": "ROUTER|send_multipart|IDENTITY",
        "grep_obs": "harbor.py send payload only. pack.py send [identity, b'', payload].",
        "test": "pytest tests/test_harbor.py",
        "fail1": "FAIL test_assign: ZMQError: Host unreachable / silent drop; no peer identity frame",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert dealer.recv() == b'5'",
        "wrong_name": "ZMQ_ROUTER_MANDATORY off",
        "wrong_diff": "+ sock.setsockopt(zmq.ROUTER_MANDATORY, 0)",
        "wrong_obs": "turns a hard error into a silent drop; test still times out.",
        "test_one": "pytest tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still no payload. mandatory-off hides the missing identity.",
        "reread": "send_multipart([identity, b'', payload]) using the identity captured on recv.",
        "insight": "prefix the peer identity; do not disable ROUTER_MANDATORY.",
        "probe": "rg -n 'send_multipart|ROUTER' src",
        "probe_obs": "pack.py [ident, b'', payload]. harbor.py [payload].",
        "fix_name": "prefix identity frame",
        "fix_diff": "+ ident, empty, _ = sock.recv_multipart()\n+ sock.send_multipart([ident, b'', payload])\n",
        "fix_obs": "patched identity.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.py dump send still no identity",
        "rel": "src/pack.py",
        "rel_src": "dump.send_multipart([b'dump'])",
        "fix2_name": "dump identity prefix",
        "fix2_diff": "+ dump.send_multipart([ident, b'', b'dump'])",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "ROUTER_MANDATORY, 0",
        "grep2": "none.",
        "doc": "docs/ROUTER.md", "doc_point": "ROUTER send starts with the peer identity",
        "doc_diff": "+ disabling MANDATORY hides drops.",
        "reg_name": "test_assign dealer",
        "reg_diff": "+ dealer.recv()==b'5'",
        "full_test": "pytest tests/test_harbor.py",
        "final": "ok 6 passed. ZeroMQ ROUTER prefixes identity.",
        "summary": "identity prefix; dump same. 6 tests pass.",
        "wrap": "the identity prefix",
        "wrap_obs": "6 passed. ZeroMQ assign ROUTER includes the peer identity.",
        "goal": "Designed plant lock-zmqrtr: ZeroMQ ROUTER sent a payload with no identity frame. Prefix the peer identity. ROUTER_MANDATORY off hides the drop.",
        "plan": "Repro pytest, reject MANDATORY off, prefix identity, fix dump.",
        "outcome": "Identity-prefixed ROUTER send. 6 ZeroMQ tests pass.",
    })


def aeron_term(rnd):
    return expand(rnd, {
        "slug": "pr-aeron-publication-term-length",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-aeronterm",
        "what": "the Aeron publication that offered a payload larger than term length",
        "glob": "**/*.{java,properties}",
        "ls": "src/Harbor.java src/Pack.java tests/HarborTest.java",
        "impl": "src/Harbor.java",
        "impl_src": "Publication pub = aeron.addPublication(ch, streamId); // default term 64KiB\nlong pos = pub.offer(UnsafeBuffer.wrap(payload)); // payload 128KiB\n",
        "sym": "addPublication", "grep": "term-length|offer|MTU",
        "grep_obs": "Harbor.java default term. Pack.java term.length=256k.",
        "test": "mvn test",
        "fail1": "FAIL offer: BACK_PRESSURED forever; payload 128KiB > term length 64KiB",
        "fail_name": "offer", "test_file": "tests/HarborTest.java",
        "test_src": "assertTrue(pos > 0);",
        "wrong_name": "spin offer until timeout",
        "wrong_diff": "+ while (pub.offer(buf) < 0) Thread.yield();",
        "wrong_obs": "BACK_PRESSURED never clears; the frame cannot fit the term.",
        "test_one": "mvn test -Dtest=HarborTest#offer",
        "fail2": "FAIL offer: still BACK_PRESSURED after 2s. retry is not a bigger term.",
        "reread": "Set aeron.term.buffer.length=262144 (power of two) on the publication channel URI.",
        "insight": "channel URI term-length=256k; do not spin on offer.",
        "probe": "rg -n 'term-length|term.buffer' src",
        "probe_obs": "Pack.java aeron:ipc?term-length=262144. Harbor.java bare ipc.",
        "fix_name": "term-length 256k on channel",
        "fix_diff": "+ Publication pub = aeron.addPublication(\"aeron:ipc?term-length=262144\", streamId);\n",
        "fix_obs": "patched term. dump leftover 64k.",
        "fail3": "PASS offer\nFAIL pack leftover: src/Pack.java dump publication default term",
        "rel": "src/Pack.java",
        "rel_src": "aeron.addPublication(\"aeron:ipc\", dumpStream)",
        "fix2_name": "handoff dump term-length",
        "fix2_diff": "+ // TODO dump term-length=262144",
        "fix2_obs": "offer green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "while \\(pub.offer",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/TERM.md", "doc_point": "payload must fit the Aeron term",
        "doc_diff": "+ spinning offer cannot grow the term. dump leftover.",
        "reg_name": "offer",
        "reg_diff": "+ pos>0 for 128KiB payload",
        "full_test": "mvn test",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "term-length 256k; dump leftover.",
        "wrap": "the 256k term",
        "wrap_obs": "5 passed, 1 residual. Aeron assign publication fits 128KiB.",
        "goal": "Designed plant quay-aeronterm: Aeron offer of 128KiB hit a 64KiB term and stayed BACK_PRESSURED. term-length=256k. Spinning offer cannot grow the term. dump may remain.",
        "plan": "Repro mvn test, reject spin-offer, term-length, hand off dump.",
        "outcome": "256k term. dump leftover. Partial.",
    })


def iouring_sqpoll(rnd):
    return expand(rnd, {
        "slug": "pr-iouring-sqpoll-need-wakeup",
        "success": True, "tests": 6, "plant": "lock-iouring",
        "what": "the io_uring SQPOLL ring that skipped IORING_SQ_NEED_WAKEUP",
        "glob": "**/*.{c,h}",
        "ls": "src/harbor.c src/pack.c tests/test_harbor.c",
        "impl": "src/harbor.c",
        "impl_src": "io_uring_queue_init_params(32, &ring, &p); /* p.flags = IORING_SETUP_SQPOLL */\nio_uring_submit(&ring); /* never checks SQ_NEED_WAKEUP */\n",
        "sym": "IORING_SETUP_SQPOLL", "grep": "SQPOLL|NEED_WAKEUP|enter",
        "grep_obs": "harbor.c SQPOLL submit only. pack.c io_uring_sqring_need_wakeup then enter.",
        "test": "gcc tests/test_harbor.c src/*.c -luring && ./a.out",
        "fail1": "FAIL test_assign: SQPOLL thread slept; IORING_SQ_NEED_WAKEUP set; CQE never arrives",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.c",
        "test_src": "assert(cqe->res == 5);",
        "wrong_name": "busy-loop io_uring_submit",
        "wrong_diff": "+ for (int i=0;i<1000;i++) io_uring_submit(&ring);",
        "wrong_obs": "submit does not wake SQPOLL when NEED_WAKEUP is set; still no CQE.",
        "test_one": "./a.out -- assign",
        "fail2": "FAIL test_assign: still asleep. submit is not io_uring_enter wakeup.",
        "reread": "If io_uring_sqring_need_wakeup(&ring), call io_uring_enter with IORING_ENTER_SQ_WAKEUP.",
        "insight": "check NEED_WAKEUP and enter with SQ_WAKEUP; do not busy-submit.",
        "probe": "rg -n 'NEED_WAKEUP|SQPOLL' src",
        "probe_obs": "pack.c need_wakeup then enter. harbor.c submit only.",
        "fix_name": "NEED_WAKEUP then SQ_WAKEUP enter",
        "fix_diff": "+ if (io_uring_sqring_need_wakeup(&ring))\n+   io_uring_enter(ring.ring_fd, 0, 0, IORING_ENTER_SQ_WAKEUP, NULL);\n",
        "fix_obs": "patched wakeup.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.c dump SQPOLL no wakeup",
        "rel": "src/pack.c",
        "rel_src": "io_uring_submit(&dump_ring);",
        "fix2_name": "dump NEED_WAKEUP",
        "fix2_diff": "+ if (io_uring_sqring_need_wakeup(&dump_ring)) io_uring_enter(..., IORING_ENTER_SQ_WAKEUP, NULL);",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "for \\(int i=0;i<1000;i\\+\\+\\) io_uring_submit",
        "grep2": "none.",
        "doc": "docs/SQPOLL.md", "doc_point": "SQPOLL must honor IORING_SQ_NEED_WAKEUP",
        "doc_diff": "+ busy submit does not wake the SQ thread.",
        "reg_name": "test_assign CQE",
        "reg_diff": "+ cqe->res==5 after wakeup",
        "full_test": "./a.out",
        "final": "ok 6 passed. io_uring SQPOLL wakes on NEED_WAKEUP.",
        "summary": "SQ_WAKEUP enter; dump same. 6 tests pass.",
        "wrap": "the NEED_WAKEUP path",
        "wrap_obs": "6 passed. io_uring assign wakes the SQPOLL thread.",
        "goal": "Designed plant lock-iouring: io_uring SQPOLL skipped IORING_SQ_NEED_WAKEUP so CQEs never arrived. io_uring_enter SQ_WAKEUP. Busy submit does not wake the thread.",
        "plan": "Repro liburing tests, reject busy-submit, NEED_WAKEUP, fix dump.",
        "outcome": "SQ_WAKEUP on NEED_WAKEUP. 6 io_uring tests pass.",
    })


def dpdk_mbuf(rnd):
    return expand(rnd, {
        "slug": "pr-dpdk-mbuf-refcnt-clone",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-dpdkmb",
        "what": "the DPDK mbuf clone that freed the original while refcnt was 2",
        "glob": "**/*.{c,h}",
        "ls": "src/harbor.c src/pack.c tests/test_harbor.c",
        "impl": "src/harbor.c",
        "impl_src": "struct rte_mbuf *c = rte_pktmbuf_clone(m, pool);\nrte_pktmbuf_free(m);  /* original still referenced by c; pool corruption if refcnt not held */\n",
        "sym": "rte_pktmbuf_clone", "grep": "rte_pktmbuf_clone|refcnt|pktmbuf_free",
        "grep_obs": "harbor.c free original after clone. pack.c free only when refcnt==1.",
        "test": "meson test -C build",
        "fail1": "FAIL test_assign: panic mbuf already free / refcnt 0 while clone still in TX",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.c",
        "test_src": "assert(rte_mbuf_refcnt_read(c) == 1);",
        "wrong_name": "rte_pktmbuf_prefree_seg on the clone",
        "wrong_diff": "+ rte_pktmbuf_prefree_seg(c);",
        "wrong_obs": "prefree on the clone drops its ref; original still double-freed.",
        "test_one": "meson test -C build -- test_assign",
        "fail2": "FAIL test_assign: still pool corruption. prefree is not a refcnt hold.",
        "reread": "Do not free m while the clone shares its data. rte_pktmbuf_free(m) only after the clone is also free, or skip the original free.",
        "insight": "leave the original alive until the clone is freed; do not prefree the clone.",
        "probe": "rg -n 'pktmbuf_clone|pktmbuf_free' src",
        "probe_obs": "pack.c clone then free clone later only. harbor.c frees original immediately.",
        "fix_name": "do not free original while clone lives",
        "fix_diff": "+ struct rte_mbuf *c = rte_pktmbuf_clone(m, pool);\n+ /* m stays until TX done; then free both */\n",
        "fix_obs": "patched lifetime. dump leftover free-after-clone.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.c dump still frees original after clone",
        "rel": "src/pack.c",
        "rel_src": "rte_pktmbuf_clone(d, pool); rte_pktmbuf_free(d);",
        "fix2_name": "handoff dump mbuf lifetime",
        "fix2_diff": "+ /* TODO dump do not free original while clone lives */",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "rte_pktmbuf_prefree_seg\\(c\\)",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/MBUF.md", "doc_point": "clone shares data; do not free original early",
        "doc_diff": "+ prefree on the clone is wrong. dump leftover.",
        "reg_name": "test_assign",
        "reg_diff": "+ clone refcnt 1; no double free",
        "full_test": "meson test -C build",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "original lives with clone; dump leftover.",
        "wrap": "the shared-mbuf lifetime",
        "wrap_obs": "5 passed, 1 residual. DPDK assign clone no longer double-frees.",
        "goal": "Designed plant quay-dpdkmb: DPDK rte_pktmbuf_free of the original while a clone shared data corrupted the pool. Keep the original. prefree on the clone is wrong. dump may remain.",
        "plan": "Repro meson test, reject prefree clone, keep original, hand off dump.",
        "outcome": "Shared mbuf lifetime. dump leftover. Partial.",
    })
def oz_byneed(rnd):
    return expand(rnd, {
        "slug": "pr-oz-byneed-dataflow-deadlock",
        "success": True, "tests": 7, "plant": "lock-ozneed",
        "what": "the Oz ByNeed that deadlocks because the trigger waits on itself",
        "glob": "**/*.{oz,ozg}",
        "ls": "src/Harbor.oz src/Pack.oz tests/harbor_test.oz",
        "impl": "src/Harbor.oz",
        "impl_src": "fun {Assign N}\n   X = {ByNeed fun {$} X + N end}\n   X\nend\n",
        "sym": "ByNeed", "grep": "ByNeed|Wait|thread",
        "grep_obs": "Harbor.oz ByNeed closes over X. Pack.oz uses a fresh local Y.",
        "test": "ozengine tests/harbor_test.oz",
        "fail1": "FAIL test_assign: timeout; dataflow deadlock on X=X+N",
        "fail_name": "test_assign", "test_file": "tests/harbor_test.oz",
        "test_src": "{Assert {Assign 4} == 4}",
        "wrong_name": "WaitNeeded X before returning",
        "wrong_diff": "+ {WaitNeeded X}\n+ X",
        "wrong_obs": "WaitNeeded still waits on the same unbound X; deadlock remains.",
        "test_one": "ozengine tests/harbor_test.oz --filter assign",
        "fail2": "FAIL test_assign: still timeout. WaitNeeded is not a value.",
        "reread": "ByNeed trigger must not mention the future. Compute N in a local, bind X outside.",
        "insight": "fun {$} N end not fun {$} X+N end; bind X = {ByNeed F}.",
        "probe": "rg -n 'ByNeed' src",
        "probe_obs": "Pack.oz Y = {ByNeed fun {$} N end}. Harbor closes over X.",
        "fix_name": "ByNeed trigger without X",
        "fix_diff": "+ fun {Assign N}\n+    X = {ByNeed fun {$} N end}\n+    X\n+ end\n",
        "fix_obs": "patched ByNeed.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/Pack.oz dump still waits on Dump=Dump",
        "rel": "src/Pack.oz",
        "rel_src": "Dump = {ByNeed fun {$} Dump end}",
        "fix2_name": "dump ByNeed without self",
        "fix2_diff": "+ Dump = {ByNeed fun {$} 0 end}",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 7.",
        "bad_pat": "ByNeed fun \\{\\$\\} X",
        "grep2": "none.",
        "doc": "docs/BYNEED.md", "doc_point": "ByNeed trigger must not wait on its future",
        "doc_diff": "+ do not close over the ByNeed variable in the trigger.",
        "reg_name": "test_assign 4",
        "reg_diff": "+ {Assign 4}==4 no timeout",
        "full_test": "ozengine tests/harbor_test.oz",
        "final": "ok 7 passed. Oz ByNeed no longer deadlocks.",
        "summary": "ByNeed trigger returns N; dump same. 7 Oz tests pass.",
        "wrap": "the ByNeed path",
        "wrap_obs": "7 passed. Oz Assign no longer waits on itself.",
        "goal": "Designed plant lock-ozneed: Oz ByNeed trigger closed over its own future so Assign deadlocked. Trigger must not mention X. WaitNeeded is not a fix.",
        "plan": "Repro ozengine, reject WaitNeeded, ByNeed without X, fix dump.",
        "outcome": "ByNeed without self-wait. 7 Oz tests pass.",
    })


def manticore_cml(rnd):
    return expand(rnd, {
        "slug": "pr-manticore-cml-channel-recv-poll",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-manticore",
        "what": "the Manticore CML recv that wraps poll instead of sync",
        "glob": "**/*.{pml,sml,mlb}",
        "ls": "src/harbor.pml src/pack.pml tests/harbor.pml",
        "impl": "src/harbor.pml",
        "impl_src": "fun assign ch n = (CML.send (ch, n); CML.poll (CML.recvEvt ch))\n",
        "sym": "poll", "grep": "CML\\.(poll|sync|recvEvt|send)",
        "grep_obs": "harbor.pml poll recvEvt. pack.pml sync recvEvt.",
        "test": "manticore tests/harbor.pml",
        "fail1": "FAIL test_assign: got NONE after send; expected SOME 4",
        "fail_name": "test_assign", "test_file": "tests/harbor.pml",
        "test_src": "val SOME x = assign ch 4",
        "wrong_name": "spawn a dummy thread then poll again",
        "wrong_diff": "+ spawn (fn () => ()); CML.poll (CML.recvEvt ch)",
        "wrong_obs": "spawn does not buffer a completed send; poll is still NONE.",
        "test_one": "manticore tests/harbor.pml --filter assign",
        "fail2": "FAIL test_assign: still NONE. poll is non-blocking.",
        "reread": "CML.sync on recvEvt waits. poll is the non-blocking probe.",
        "insight": "CML.sync (CML.recvEvt ch) after send on a pair of threads; do not poll.",
        "probe": "rg -n 'CML' src",
        "probe_obs": "pack.pml sync. harbor.pml poll.",
        "fix_name": "sync recvEvt instead of poll",
        "fix_diff": "+ fun assign ch n = let in spawn (fn () => CML.send (ch, n)); CML.sync (CML.recvEvt ch) end\n",
        "fix_obs": "patched sync. dump still polls.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.pml dump uses poll",
        "rel": "src/pack.pml",
        "rel_src": "fun dump ch = CML.poll (CML.recvEvt ch)",
        "fix2_name": "handoff dump sync",
        "fix2_diff": "+ /* TODO dump = CML.sync (CML.recvEvt ch) */",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "CML.poll",
        "grep2": "none in assign. leftover dump poll.",
        "doc": "docs/CML.md", "doc_point": "sync not poll for a required recv",
        "doc_diff": "+ poll is non-blocking. dump leftover.",
        "reg_name": "test_assign SOME 4",
        "reg_diff": "+ assign ch 4 = 4",
        "full_test": "manticore tests/harbor.pml",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "sync recvEvt; dump leftover.",
        "wrap": "the CML sync path",
        "wrap_obs": "5 passed, 1 residual. Manticore assign syncs recvEvt.",
        "goal": "Designed plant quay-manticore: Manticore CML.poll on recvEvt returned NONE after send. Use sync. spawn-then-poll is not a buffer. dump may remain.",
        "plan": "Repro manticore, reject spawn+poll, sync recvEvt, hand off dump.",
        "outcome": "CML.sync recvEvt. dump leftover. Partial.",
    })


def pallene_capi(rnd):
    return expand(rnd, {
        "slug": "pr-pallene-c-api-stack-index",
        "success": True, "tests": 7, "plant": "lock-pallene",
        "what": "the Pallene C module that used a stale Lua stack index after a call",
        "glob": "**/*.{pln,c,h}",
        "ls": "src/harbor.pln src/pack.pln tests/test_harbor.pln src/harbor_c.c",
        "impl": "src/harbor_c.c",
        "impl_src": "lua_pushinteger(L, n);\nlua_call(L, 1, 1);\nlua_Integer v = lua_tointeger(L, 1);\n",
        "sym": "lua_tointeger", "grep": "lua_tointeger|lua_call|lua_absindex",
        "grep_obs": "harbor_c.c tointeger(L,1) after call. pack.c uses -1.",
        "test": "pallene tests/test_harbor.pln && lua tests/test_harbor.lua",
        "fail1": "FAIL test_assign: got 0 not 5; stack index 1 was the C closure",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.pln",
        "test_src": "function assign(n: integer): integer\n  return c_assign(n)\nend",
        "wrong_name": "lua_insert the result to index 1",
        "wrong_diff": "+ lua_insert(L, 1);\n+ lua_Integer v = lua_tointeger(L, 1);",
        "wrong_obs": "insert shifted the C closure under the result; next call sees a number as the function.",
        "test_one": "lua tests/test_harbor.lua -k assign",
        "fail2": "FAIL test_assign_twice: attempt to call a number value.",
        "reread": "After lua_call with nresults=1 the result is at -1. Use lua_tointeger(L, -1).",
        "insight": "read the result at -1 after lua_call; do not assume index 1.",
        "probe": "rg -n 'lua_tointeger|lua_call' src",
        "probe_obs": "pack.c lua_tointeger(L, -1). harbor_c.c uses 1.",
        "fix_name": "tointeger at -1 after call",
        "fix_diff": "+ lua_call(L, 1, 1);\n+ lua_Integer v = lua_tointeger(L, -1);\n",
        "fix_obs": "patched stack index.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.c dump still uses index 2 after call",
        "rel": "src/pack.c",
        "rel_src": "lua_call(L, 0, 1); dump = lua_tointeger(L, 2);",
        "fix2_name": "dump tointeger -1",
        "fix2_diff": "+ dump = lua_tointeger(L, -1);",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 7.",
        "bad_pat": "lua_tointeger\\(L, 1\\)",
        "grep2": "none.",
        "doc": "docs/CAPI.md", "doc_point": "lua_call result is at -1",
        "doc_diff": "+ do not reuse a pre-call absolute index after lua_call.",
        "reg_name": "test_assign_twice",
        "reg_diff": "+ assign(4)==5 twice",
        "full_test": "lua tests/test_harbor.lua",
        "final": "ok 7 passed. Pallene C API reads the result at -1.",
        "summary": "tointeger -1 after lua_call; dump same. 7 tests pass.",
        "wrap": "the -1 result index",
        "wrap_obs": "7 passed. Pallene C module no longer reads a stale stack index.",
        "goal": "Designed plant lock-pallene: Pallene C glue used lua_tointeger(L,1) after lua_call so it read the closure. Use -1. lua_insert is not a fix.",
        "plan": "Repro pallene/lua tests, reject lua_insert, tointeger -1, fix dump.",
        "outcome": "Result at -1. 7 Pallene tests pass.",
    })


def moonscript_fat(rnd):
    return expand(rnd, {
        "slug": "pr-moonscript-fat-arrow-self",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-moonfat",
        "what": "the MoonScript fat-arrow that compiled to a thin arrow so self was nil",
        "glob": "**/*.{moon,lua}",
        "ls": "src/harbor.moon src/pack.moon tests/harbor_spec.moon",
        "impl": "src/harbor.moon",
        "impl_src": "class Harbor\n  assign: (n) -> @slip = n\n",
        "sym": "assign:", "grep": "assign:|=>|->",
        "grep_obs": "harbor.moon assign uses ->. pack.moon uses =>.",
        "test": "busted tests/harbor_spec.moon",
        "fail1": "FAIL test_assign: attempt to index a nil value (field 'slip') self is nil",
        "fail_name": "test_assign", "test_file": "tests/harbor_spec.moon",
        "test_src": "h = Harbor!\nh\\assign 4\nassert.equal 4, h.slip",
        "wrong_name": "colon call rewrite only in the test",
        "wrong_diff": "+ -- tests now call h.assign(h, 4)",
        "wrong_obs": "production still compiles -> so @slip is nil when callers use h\\assign.",
        "test_one": "busted tests/harbor_spec.moon -t assign",
        "fail2": "FAIL test_assign: still nil self on the method table.",
        "reread": "MoonScript => binds self. -> is a plain function. Methods that use @ need =>.",
        "insight": "assign: (n) => @slip = n; do not change only the test call site.",
        "probe": "rg -n '=>' src; moonc -p src/harbor.moon | head",
        "probe_obs": "pack.moon => compiles to :assign. harbor.moon -> compiles to .assign.",
        "fix_name": "fat arrow on assign",
        "fix_diff": "+ assign: (n) => @slip = n\n",
        "fix_obs": "patched =>. dump still uses ->.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.moon dump ->",
        "rel": "src/pack.moon",
        "rel_src": "dump: -> @slip",
        "fix2_name": "handoff dump fat arrow",
        "fix2_diff": "+ -- TODO dump: => @slip",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "assign: \\(n\\) ->",
        "grep2": "none in assign. leftover dump ->.",
        "doc": "docs/ARROW.md", "doc_point": "@ methods need =>",
        "doc_diff": "+ thin arrow drops self. dump leftover.",
        "reg_name": "test_assign self",
        "reg_diff": "+ h\\assign 4; h.slip==4",
        "full_test": "busted tests/harbor_spec.moon",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "assign =>; dump leftover.",
        "wrap": "the fat-arrow path",
        "wrap_obs": "5 passed, 1 residual. MoonScript assign binds self.",
        "goal": "Designed plant quay-moonfat: MoonScript assign used -> so @slip saw nil self. Use =>. Rewriting the test colon-call is not a compiler fix. dump may remain.",
        "plan": "Repro busted, reject test-only colon rewrite, fat arrow, hand off dump.",
        "outcome": "assign uses =>. dump leftover. Partial.",
    })


def pypy_cont(rnd):
    return expand(rnd, {
        "slug": "pr-pypy-continulet-switch-stack",
        "success": True, "tests": 7, "plant": "lock-pypycont",
        "what": "the PyPy continulet that switched onto a collected stack",
        "glob": "**/*.{py,c}",
        "ls": "src/harbor.py src/pack.py tests/test_harbor.py",
        "impl": "src/harbor.py",
        "impl_src": "from _continuation import continulet\ndef assign(n):\n    c = continulet(lambda c, x: x + 1)\n    c.switch(n)\n    del c\n    return c.switch(n)\n",
        "sym": "continulet", "grep": "continulet|switch",
        "grep_obs": "harbor.py del c then switch. pack.py keeps the continulet alive.",
        "test": "pypy3 -m pytest tests/test_harbor.py",
        "fail1": "FAIL test_assign: RuntimeError: continulet already finished / dangling stack",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert assign(4) == 5",
        "wrong_name": "gc.disable around del",
        "wrong_diff": "+ import gc; gc.disable(); del c; return c.switch(n)",
        "wrong_obs": "del still unbinds the continulet; gc.disable does not resurrect it.",
        "test_one": "pypy3 -m pytest tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still dangling. gc.disable is not a keep-alive.",
        "reread": "Keep the continulet referenced until the last switch. Do not del before the second switch.",
        "insight": "store c on the harbor object; switch twice; never del mid-flight.",
        "probe": "rg -n 'continulet' src",
        "probe_obs": "pack.py self._c = continulet(...). harbor.py del c.",
        "fix_name": "keep continulet referenced",
        "fix_diff": "+ self._c = continulet(lambda c, x: x + 1)\n+ self._c.switch(n)\n+ return self._c.switch(n)\n",
        "fix_obs": "patched keep-alive.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.py dump still dels the continulet",
        "rel": "src/pack.py",
        "rel_src": "d = continulet(...); d.switch(0); del d; d.switch(0)",
        "fix2_name": "dump keeps the continulet",
        "fix2_diff": "+ self._d = continulet(...); self._d.switch(0)",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 7.",
        "bad_pat": "del c",
        "grep2": "none.",
        "doc": "docs/CONTINULET.md", "doc_point": "do not del a live continulet",
        "doc_diff": "+ keep the continulet referenced until the last switch. gc.disable is not enough.",
        "reg_name": "test_assign 5",
        "reg_diff": "+ assign(4)==5 without dangling stack",
        "full_test": "pypy3 -m pytest tests/test_harbor.py",
        "final": "ok 7 passed. PyPy continulet stays referenced.",
        "summary": "keep continulet; dump same. 7 PyPy tests pass.",
        "wrap": "the keep-alive path",
        "wrap_obs": "7 passed. PyPy assign no longer switches a collected stack.",
        "goal": "Designed plant lock-pypycont: PyPy continulet was deleted then switched, hitting a collected stack. Keep the reference. gc.disable is not a keep-alive.",
        "plan": "Repro pypy3 tests, reject gc.disable, keep-alive, fix dump.",
        "outcome": "Continulet kept. 7 PyPy tests pass.",
    })


def cython_fused(rnd):
    return expand(rnd, {
        "slug": "pr-cython-fused-type-specialize-miss",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-cyfused",
        "what": "the Cython fused-type function that specialized only int and missed float64",
        "glob": "**/*.{pyx,pxd,py}",
        "ls": "src/harbor.pyx src/pack.pyx tests/test_harbor.py",
        "impl": "src/harbor.pyx",
        "impl_src": "ctypedef fused slip_t:\n    int\ncpdef slip_t assign(slip_t n):\n    return n + 1\n",
        "sym": "slip_t", "grep": "fused|cpdef assign|double",
        "grep_obs": "harbor.pyx fused int only. pack.pyx fused int/double.",
        "test": "cythonize -i src/*.pyx && pytest tests/test_harbor.py",
        "fail1": "FAIL test_float: no matching signature for assign(float64) / TypeError",
        "fail_name": "test_float", "test_file": "tests/test_harbor.py",
        "test_src": "assert assign(4.0) == 5.0",
        "wrong_name": "cast float to int at the call site",
        "wrong_diff": "+ # callers now int(n) before assign",
        "wrong_obs": "loses 4.5 -> 4; test_float_frac fails.",
        "test_one": "pytest tests/test_harbor.py -k float",
        "fail2": "FAIL test_float_frac: assign(4.5) became 5 not 5.5 after int cast.",
        "reread": "Add double to the fused type so Cython generates both specializations.",
        "insight": "ctypedef fused slip_t: int / double; do not int-cast the caller.",
        "probe": "rg -n 'fused|double' src",
        "probe_obs": "pack.pyx includes double. harbor.pyx int only.",
        "fix_name": "add double to fused slip_t",
        "fix_diff": "+ ctypedef fused slip_t:\n+     int\n+     double\n",
        "fix_obs": "patched fused. dump still int-only.",
        "fail3": "PASS test_float\nFAIL pack leftover: src/pack.pyx dump fused int only",
        "rel": "src/pack.pyx",
        "rel_src": "ctypedef fused dump_t:\n    int",
        "fix2_name": "handoff dump fused double",
        "fix2_diff": "+ # TODO dump_t includes double",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "int\\(n\\) before assign",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/FUSED.md", "doc_point": "fused must list every runtime dtype",
        "doc_diff": "+ int-cast drops fractions. dump leftover.",
        "reg_name": "test_float 4.0",
        "reg_diff": "+ assign(4.0)==5.0; assign(4.5)==5.5",
        "full_test": "pytest tests/test_harbor.py",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "fused int+double; dump leftover.",
        "wrap": "the fused double path",
        "wrap_obs": "5 passed, 1 residual. Cython assign specializes float64.",
        "goal": "Designed plant quay-cyfused: Cython fused slip_t listed only int so assign(float64) missed. Add double. int-cast drops fractions. dump may remain.",
        "plan": "Repro cythonize tests, reject int-cast, add double, hand off dump.",
        "outcome": "fused int+double. dump leftover. Partial.",
    })


def iree_stream(rnd):
    return expand(rnd, {
        "slug": "pr-iree-stream-resource-affinity",
        "success": True, "tests": 6, "plant": "lock-ireeaff",
        "what": "the IREE stream resource that ran on the wrong affinity queue",
        "glob": "**/*.{mlir,td,py}",
        "ls": "src/harbor.mlir src/pack.mlir tests/test_harbor.py",
        "impl": "src/harbor.mlir",
        "impl_src": "stream.resource.alloc on #hal.device.affinity<0>\nstream.cmd.dispatch on #hal.device.affinity<1>\n",
        "sym": "stream.resource.alloc", "grep": "stream.resource|affinity|stream.cmd",
        "grep_obs": "harbor.mlir alloc aff0 dispatch aff1. pack.mlir same affinity.",
        "test": "iree-compile src/harbor.mlir && python3 tests/test_harbor.py",
        "fail1": "FAIL test_assign: HAL_STATUS_RESOURCE_GONE / affinity mismatch queue 1",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert module.assign(4) == 5",
        "wrong_name": "stream.resource.try_map across devices",
        "wrong_diff": "+ stream.resource.try_map %r, affinity<1>",
        "wrong_obs": "try_map does not transfer; the resource is still device-0 local.",
        "test_one": "python3 tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still RESOURCE_GONE. try_map is not a transfer.",
        "reread": "Alloc and dispatch must share affinity, or insert stream.resource.transfer.",
        "insight": "dispatch on affinity<0> matching the alloc; do not try_map as a transfer.",
        "probe": "rg -n 'affinity' src",
        "probe_obs": "pack.mlir alloc+dispatch affinity<0>. harbor.mlir mixed 0/1.",
        "fix_name": "dispatch on the alloc affinity",
        "fix_diff": "+ stream.cmd.dispatch on #hal.device.affinity<0>\n",
        "fix_obs": "patched affinity.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.mlir dump dispatch still affinity<1>",
        "rel": "src/pack.mlir",
        "rel_src": "dump dispatch on affinity<1> after alloc<0>",
        "fix2_name": "dump dispatch affinity<0>",
        "fix2_diff": "+ dump dispatch on #hal.device.affinity<0>",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "stream.resource.try_map",
        "grep2": "none.",
        "doc": "docs/AFFINITY.md", "doc_point": "alloc and dispatch share affinity",
        "doc_diff": "+ try_map is not a device transfer.",
        "reg_name": "test_assign affinity",
        "reg_diff": "+ module.assign(4)==5 no RESOURCE_GONE",
        "full_test": "python3 tests/test_harbor.py",
        "final": "ok 6 passed. IREE alloc and dispatch share affinity.",
        "summary": "dispatch affinity<0>; dump same. 6 IREE tests pass.",
        "wrap": "the matching affinity",
        "wrap_obs": "6 passed. IREE assign no longer crosses affinity queues.",
        "goal": "Designed plant lock-ireeaff: IREE stream alloc on affinity 0 dispatched on 1 so the resource was gone. Match affinity. try_map is not a transfer.",
        "plan": "Repro iree-compile tests, reject try_map, match affinity, fix dump.",
        "outcome": "Matching affinity. 6 IREE tests pass.",
    })


def onnx_fusion(rnd):
    return expand(rnd, {
        "slug": "pr-onnxruntime-graph-fusion-inplace",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-onnxfuse",
        "what": "the ONNX Runtime fusion that aliased an in-place Add into a later Gather",
        "glob": "**/*.{onnx,py,json}",
        "ls": "src/harbor.py src/pack.py tests/test_harbor.py",
        "impl": "src/harbor.py",
        "impl_src": "sess = ort.InferenceSession('harbor.onnx', sess_options=so)\n",
        "sym": "InferenceSession", "grep": "graph_optimization|ORT_ENABLE|inplace",
        "grep_obs": "harbor.py ORT_ENABLE_ALL. pack.py ORT_DISABLE_ALL for the gather path.",
        "test": "python3 tests/test_harbor.py",
        "fail1": "FAIL test_gather: got [9,9] not [4,5]; Add fused in-place overwrote the Gather input",
        "fail_name": "test_gather", "test_file": "tests/test_harbor.py",
        "test_src": "assert (sess.run(None, {'x': x})[0] == np.array([4,5])).all()",
        "wrong_name": "clone the numpy input at the caller",
        "wrong_diff": "+ sess.run(None, {'x': x.copy()})",
        "wrong_obs": "the alias is inside the fused graph, not the numpy feed. still [9,9].",
        "test_one": "python3 tests/test_harbor.py -k gather",
        "fail2": "FAIL test_gather: still [9,9]. host copy does not break fused in-place.",
        "reread": "Disable NCHWc/in-place Add fusion or insert an Identity so Gather sees the pre-Add value.",
        "insight": "so.graph_optimization_level = ORT_ENABLE_BASIC; or add Identity before Gather.",
        "probe": "rg -n 'ORT_ENABLE|Identity' src",
        "probe_obs": "pack.py ORT_ENABLE_BASIC. harbor.py ORT_ENABLE_ALL.",
        "fix_name": "drop to ORT_ENABLE_BASIC",
        "fix_diff": "+ so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC\n",
        "fix_obs": "patched opt level. dump session still ENABLE_ALL.",
        "fail3": "PASS test_gather\nFAIL pack leftover: src/pack.py dump session ENABLE_ALL",
        "rel": "src/pack.py",
        "rel_src": "dump_sess uses ORT_ENABLE_ALL",
        "fix2_name": "handoff dump opt level",
        "fix2_diff": "+ # TODO dump_sess ORT_ENABLE_BASIC",
        "fix2_obs": "gather green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "x.copy\\(\\)",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/FUSION.md", "doc_point": "in-place Add fusion aliases Gather inputs",
        "doc_diff": "+ host copy does not help. dump leftover.",
        "reg_name": "test_gather",
        "reg_diff": "+ gather sees [4,5] not post-Add [9,9]",
        "full_test": "python3 tests/test_harbor.py",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "ORT_ENABLE_BASIC; dump leftover.",
        "wrap": "the BASIC opt path",
        "wrap_obs": "5 passed, 1 residual. ONNX Runtime gather no longer sees fused Add.",
        "goal": "Designed plant quay-onnxfuse: ONNX Runtime ORT_ENABLE_ALL fused Add in-place so Gather saw the mutated buffer. ORT_ENABLE_BASIC. Host copy is not a graph fix. dump may remain.",
        "plan": "Repro ORT tests, reject host copy, ENABLE_BASIC, hand off dump.",
        "outcome": "ORT_ENABLE_BASIC. dump leftover. Partial.",
    })
def slang_pblock(rnd):
    return expand(rnd, {
        "slug": "pr-slang-parameter-block-space",
        "success": True, "tests": 6, "plant": "lock-slangpb",
        "what": "the Slang parameter-block that reused register space 0 for two sets",
        "glob": "**/*.{slang,hlsl,json}",
        "ls": "src/harbor.slang src/pack.slang tests/test_harbor.py",
        "impl": "src/harbor.slang",
        "impl_src": "ParameterBlock<Frame> gFrame;\nParameterBlock<Lights> gLights;\n",
        "sym": "ParameterBlock", "grep": "ParameterBlock|space|register",
        "grep_obs": "harbor.slang two blocks space0. pack.slang gLights : register(space1).",
        "test": "slangc src/harbor.slang -target spirv && python3 tests/test_harbor.py",
        "fail1": "FAIL test_assign: SPIR-V descriptor set 0 bound twice; validation: set conflict",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert pipeline.dispatch(4) == 5",
        "wrong_name": "pack both structs into one ParameterBlock",
        "wrong_diff": "+ ParameterBlock<FrameLights> gAll;",
        "wrong_obs": "CPU still binds two sets; the combined block does not match the root signature.",
        "test_one": "python3 tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still set 0 conflict on the host binder.",
        "reread": "Give gLights space1: ParameterBlock<Lights> gLights : register(space1);",
        "insight": "each ParameterBlock needs its own space; do not smash structs to dodge the binder.",
        "probe": "rg -n 'ParameterBlock|space' src",
        "probe_obs": "pack.slang gLights : register(space1). harbor.slang both default space0.",
        "fix_name": "gLights register space1",
        "fix_diff": "+ ParameterBlock<Lights> gLights : register(space1);\n",
        "fix_obs": "patched space1.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.slang dump block still space0",
        "rel": "src/pack.slang",
        "rel_src": "ParameterBlock<Dump> gDump;",
        "fix2_name": "dump register space2",
        "fix2_diff": "+ ParameterBlock<Dump> gDump : register(space2);",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "ParameterBlock<FrameLights>",
        "grep2": "none.",
        "doc": "docs/PBLOCK.md", "doc_point": "one ParameterBlock per register space",
        "doc_diff": "+ collapsing structs does not fix the host binder.",
        "reg_name": "test_assign spaces",
        "reg_diff": "+ gFrame space0 gLights space1 no set conflict",
        "full_test": "python3 tests/test_harbor.py",
        "final": "ok 6 passed. Slang parameter-blocks use distinct spaces.",
        "summary": "gLights space1; dump space2. 6 Slang tests pass.",
        "wrap": "the distinct spaces",
        "wrap_obs": "6 passed. Slang assign no longer reuses space0.",
        "goal": "Designed plant lock-slangpb: Slang ParameterBlock gFrame and gLights both landed in space0. Give gLights space1. Combining structs does not match the root signature.",
        "plan": "Repro slangc tests, reject combined block, space1, fix dump.",
        "outcome": "Distinct register spaces. 6 Slang tests pass.",
    })


def pipelinec_stall(rnd):
    return expand(rnd, {
        "slug": "pr-pipelinec-handshake-stall-valid",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-pipec",
        "what": "the PipelineC handshake that dropped valid during a stall",
        "glob": "**/*.{c,h,v}",
        "ls": "src/harbor.c src/pack.c tests/test_harbor.py",
        "impl": "src/harbor.c",
        "impl_src": "#pragma FUNC_WIRES assign\nint assign(int n) { static int slip; slip = n + 1; return slip; }\n",
        "sym": "FUNC_WIRES", "grep": "FUNC_WIRES|valid|ready|FUNC_PIPELINE",
        "grep_obs": "harbor.c FUNC_WIRES. pack.c FUNC_PIPELINE + handshake.",
        "test": "python3 -m pipelinec tests/test_harbor.py",
        "fail1": "FAIL test_stall: downstream ready=0 for 3 cycles; output valid dropped; got X",
        "fail_name": "test_stall", "test_file": "tests/test_harbor.py",
        "test_src": "assert sim.stall_then_fire() == 5",
        "wrong_name": "clock-enable AND with ready",
        "wrong_diff": "+ if (ready) slip = n + 1;",
        "wrong_obs": "FUNC_WIRES has no handshake; ready is not a port. still X on stall.",
        "test_one": "python3 -m pipelinec tests/test_harbor.py -k stall",
        "fail2": "FAIL test_stall: still X. ready is not in FUNC_WIRES ABI.",
        "reread": "Use FUNC_PIPELINE and the generated valid/ready pair so a stall holds the register.",
        "insight": "FUNC_PIPELINE handshake; do not fake ready inside FUNC_WIRES.",
        "probe": "rg -n 'FUNC_PIPELINE|FUNC_WIRES' src",
        "probe_obs": "pack.c FUNC_PIPELINE. harbor.c FUNC_WIRES.",
        "fix_name": "FUNC_PIPELINE handshake",
        "fix_diff": "+ #pragma FUNC_PIPELINE assign\n+ int assign(int n) { return n + 1; }\n",
        "fix_obs": "patched pipeline. dump still FUNC_WIRES.",
        "fail3": "PASS test_stall\nFAIL pack leftover: src/pack.c dump FUNC_WIRES",
        "rel": "src/pack.c",
        "rel_src": "#pragma FUNC_WIRES dump",
        "fix2_name": "handoff dump FUNC_PIPELINE",
        "fix2_diff": "+ /* TODO FUNC_PIPELINE dump */",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "if \\(ready\\) slip",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/HANDSHAKE.md", "doc_point": "FUNC_PIPELINE holds valid on stall",
        "doc_diff": "+ FUNC_WIRES drops. dump leftover.",
        "reg_name": "test_stall",
        "reg_diff": "+ stall 3 cycles then 5",
        "full_test": "python3 -m pipelinec tests/test_harbor.py",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "FUNC_PIPELINE assign; dump leftover.",
        "wrap": "the handshake path",
        "wrap_obs": "5 passed, 1 residual. PipelineC assign holds valid on stall.",
        "goal": "Designed plant quay-pipec: PipelineC FUNC_WIRES dropped valid during a stall. FUNC_PIPELINE handshake. Fake ready inside FUNC_WIRES is not an ABI. dump may remain.",
        "plan": "Repro pipelinec tests, reject fake ready, FUNC_PIPELINE, hand off dump.",
        "outcome": "FUNC_PIPELINE handshake. dump leftover. Partial.",
    })


def rocksdb_merge(rnd):
    return expand(rnd, {
        "slug": "pr-rocksdb-merge-op-partial-assoc",
        "success": True, "tests": 6, "plant": "lock-rdbmerge",
        "what": "the RocksDB merge operator that was not associative on partial merges",
        "glob": "**/*.{cc,h,py}",
        "ls": "src/harbor.cc src/pack.cc tests/test_harbor.py",
        "impl": "src/harbor.cc",
        "impl_src": "bool PartialMerge(const Slice& key, const Slice& left, const Slice& right, std::string* n) override {\n  *n = left.ToString() + right.ToString();\n  return true;\n}\n",
        "sym": "PartialMerge", "grep": "PartialMerge|FullMerge|MergeOperator",
        "grep_obs": "harbor.cc PartialMerge concat. pack.cc PartialMerge uint add.",
        "test": "python3 tests/test_harbor.py",
        "fail1": "FAIL test_assign: after compaction slip=45 not 9; concat then parse != add",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert db.get(b'slip') == b'9'",
        "wrong_name": "disable compaction so PartialMerge never runs",
        "wrong_diff": "+ opts.disable_auto_compactions = true;",
        "wrong_obs": "manual CompactRange in CI still concatenates; test_compact fails.",
        "test_one": "python3 tests/test_harbor.py -k assign",
        "fail2": "FAIL test_compact: still 45. hiding compaction is not associativity.",
        "reread": "PartialMergeMulti must add uint64 the same way FullMerge does.",
        "insight": "decode both operands as uint64 and add; do not concat.",
        "probe": "rg -n 'PartialMerge|FullMerge' src",
        "probe_obs": "pack.cc uint add both paths. harbor.cc concat.",
        "fix_name": "PartialMerge uint add",
        "fix_diff": "+ uint64_t a, b; Decode(left,&a); Decode(right,&b); Encode(n, a+b);\n",
        "fix_obs": "patched add.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.cc dump merge still concat",
        "rel": "src/pack.cc",
        "rel_src": "*n = left.ToString() + right.ToString();",
        "fix2_name": "dump PartialMerge add",
        "fix2_diff": "+ Decode add Encode for dump merge",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "disable_auto_compactions",
        "grep2": "none.",
        "doc": "docs/MERGE.md", "doc_point": "PartialMerge must match FullMerge associativity",
        "doc_diff": "+ concat is not uint add. do not disable compaction to hide it.",
        "reg_name": "test_compact",
        "reg_diff": "+ 4+5==9 after CompactRange",
        "full_test": "python3 tests/test_harbor.py",
        "final": "ok 6 passed. RocksDB merge add is associative.",
        "summary": "PartialMerge uint add; dump same. 6 tests pass.",
        "wrap": "the associative merge",
        "wrap_obs": "6 passed. RocksDB assign merge adds, not concatenates.",
        "goal": "Designed plant lock-rdbmerge: RocksDB PartialMerge concatenated while FullMerge added so compaction produced 45 not 9. uint add both paths. Disabling compaction hides the bug.",
        "plan": "Repro compaction tests, reject disable_auto_compactions, uint add, fix dump.",
        "outcome": "Associative uint merge. 6 RocksDB tests pass.",
    })


def badger_txn(rnd):
    return expand(rnd, {
        "slug": "pr-badger-txn-discard-callback",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-badgertx",
        "what": "the Badger txn that used the callback after Discard",
        "glob": "**/*.{go,md}",
        "ls": "src/harbor.go src/pack.go tests/harbor_test.go",
        "impl": "src/harbor.go",
        "impl_src": "err := db.Update(func(txn *badger.Txn) error {\n  txn.Set([]byte(\"slip\"), []byte(\"4\"))\n  txn.Discard()\n  return nil\n})\n",
        "sym": "txn.Discard", "grep": "Discard|Update|Commit",
        "grep_obs": "harbor.go Discard inside Update. pack.go returns err without Discard.",
        "test": "go test ./...",
        "fail1": "FAIL TestAssign: panic: discarded txn / ErrDiscardedTxn on implicit Commit",
        "fail_name": "TestAssign", "test_file": "tests/harbor_test.go",
        "test_src": "if v := get(db, \"slip\"); v != \"4\" { t.Fatalf(\"%s\", v) }",
        "wrong_name": "txn.Commit inside Update",
        "wrong_diff": "+ txn.Commit(); return nil",
        "wrong_obs": "Update already commits on nil error; inner Commit is ErrConflict / double commit.",
        "test_one": "go test ./... -run TestAssign",
        "fail2": "FAIL TestAssign: ErrConflict. Update owns the commit.",
        "reread": "Do not Discard or Commit inside db.Update. Return an error to abort; return nil to commit.",
        "insight": "return nil to commit; return err to abort. No Discard inside Update.",
        "probe": "rg -n 'Discard|Update' src",
        "probe_obs": "pack.go return fmt.Errorf to abort. harbor.go Discard.",
        "fix_name": "drop Discard; return nil",
        "fix_diff": "+ err := db.Update(func(txn *badger.Txn) error {\n+   return txn.Set([]byte(\"slip\"), []byte(\"4\"))\n+ })\n",
        "fix_obs": "patched Update. dump still Discards.",
        "fail3": "PASS TestAssign\nFAIL pack leftover: src/pack.go dump Discard inside Update",
        "rel": "src/pack.go",
        "rel_src": "db.Update(func(txn *badger.Txn) error { txn.Discard(); return nil })",
        "fix2_name": "handoff dump Discard",
        "fix2_diff": "+ // TODO dump Update without Discard",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "txn.Commit\\(\\)",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/TXN.md", "doc_point": "Update commits on nil; never Discard inside",
        "doc_diff": "+ inner Commit double-commits. dump leftover.",
        "reg_name": "TestAssign",
        "reg_diff": "+ slip==4 no discarded panic",
        "full_test": "go test ./...",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "Update without Discard; dump leftover.",
        "wrap": "the Update-nil path",
        "wrap_obs": "5 passed, 1 residual. Badger assign no longer Discards inside Update.",
        "goal": "Designed plant quay-badgertx: Badger Discard inside Update panicked on implicit Commit. Return nil to commit. Inner Commit double-commits. dump may remain.",
        "plan": "Repro go test, reject inner Commit, drop Discard, hand off dump.",
        "outcome": "Update without Discard. dump leftover. Partial.",
    })


def akka_persist(rnd):
    return expand(rnd, {
        "slug": "pr-akka-persist-stash-unstashall",
        "success": True, "tests": 6, "plant": "lock-akkapers",
        "what": "the Akka persistent actor that persisted after becoming, dropping stash",
        "glob": "**/*.{scala,conf}",
        "ls": "src/Harbor.scala src/Pack.scala tests/HarborSpec.scala",
        "impl": "src/Harbor.scala",
        "impl_src": "def receiveCommand: Receive = {\n  case Assign(n) => persist(Assigned(n)) { _ => context.become(ready) }\n}\n",
        "sym": "persist", "grep": "persist|unstashAll|stash|become",
        "grep_obs": "Harbor.scala become after persist, no unstashAll. Pack.scala unstashAll.",
        "test": "sbt test",
        "fail1": "FAIL assign: stashed GetSlip never delivered after Assigned; probe timed out",
        "fail_name": "assign", "test_file": "tests/HarborSpec.scala",
        "test_src": "actor ! Assign(4); actor ! GetSlip; expectMsg(Slip(4))",
        "wrong_name": "context.unbecome after persist",
        "wrong_diff": "+ persist(Assigned(n)) { _ => context.unbecome() }",
        "wrong_obs": "unbecome restores the previous behavior but still does not unstash.",
        "test_one": "sbt 'testOnly *HarborSpec -- -z assign'",
        "fail2": "FAIL assign: GetSlip still stuck in stash.",
        "reread": "Call unstashAll in the persist handler after become(ready).",
        "insight": "become(ready); unstashAll() in the persist callback.",
        "probe": "rg -n 'unstashAll' src",
        "probe_obs": "Pack.scala unstashAll. Harbor.scala none.",
        "fix_name": "unstashAll after become",
        "fix_diff": "+ persist(Assigned(n)) { _ => context.become(ready); unstashAll() }\n",
        "fix_obs": "patched unstashAll.",
        "fail3": "PASS assign\nFAIL pack leftover: src/Pack.scala dump persist without unstashAll",
        "rel": "src/Pack.scala",
        "rel_src": "persist(Dumped) { _ => context.become(dumped) }",
        "fix2_name": "dump unstashAll",
        "fix2_diff": "+ persist(Dumped) { _ => context.become(dumped); unstashAll() }",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "context.unbecome\\(\\)",
        "grep2": "none.",
        "doc": "docs/STASH.md", "doc_point": "unstashAll after persist+become",
        "doc_diff": "+ unbecome does not unstash.",
        "reg_name": "assign GetSlip",
        "reg_diff": "+ GetSlip after Assign yields Slip(4)",
        "full_test": "sbt test",
        "final": "ok 6 passed. Akka persist unstashes.",
        "summary": "unstashAll after become; dump same. 6 tests pass.",
        "wrap": "the unstashAll path",
        "wrap_obs": "6 passed. Akka assign delivers stashed GetSlip.",
        "goal": "Designed plant lock-akkapers: Akka persist became ready without unstashAll so GetSlip stayed stashed. unstashAll in the persist callback. unbecome is not unstash.",
        "plan": "Repro sbt test, reject unbecome, unstashAll, fix dump.",
        "outcome": "unstashAll after persist. 6 Akka tests pass.",
    })


def orleans_reminder(rnd):
    return expand(rnd, {
        "slug": "pr-orleans-reminder-register-tick",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-orlrnd",
        "what": "the Orleans reminder that was registered after DeactivateOnIdle so it never ticked",
        "glob": "**/*.{cs,json}",
        "ls": "src/HarborGrain.cs src/PackGrain.cs tests/HarborTests.cs",
        "impl": "src/HarborGrain.cs",
        "impl_src": "public override async Task OnDeactivateAsync(...) {\n  await RegisterOrUpdateReminder(\"slip\", TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));\n}\n",
        "sym": "RegisterOrUpdateReminder", "grep": "Reminder|DeactivateOnIdle|ReceiveReminder",
        "grep_obs": "HarborGrain registers in OnDeactivateAsync. PackGrain registers in OnActivateAsync.",
        "test": "dotnet test",
        "fail1": "FAIL Tick: reminder never fires; grain deactivated before registration persisted",
        "fail_name": "Tick", "test_file": "tests/HarborTests.cs",
        "test_src": "await grain.Assign(4); await Task.Delay(due); Assert.Equal(5, await grain.Slip());",
        "wrong_name": "DelayDeactivation Infinite in the reminder",
        "wrong_diff": "+ DelayDeactivation(TimeSpan.MaxValue);",
        "wrong_obs": "DelayDeactivation in OnDeactivateAsync is too late; the grain is already going idle.",
        "test_one": "dotnet test --filter Tick",
        "fail2": "FAIL Tick: still no reminder. DelayDeactivation cannot run during deactivate.",
        "reread": "Register the reminder in OnActivateAsync (or after Assign) while the grain is active.",
        "insight": "RegisterOrUpdateReminder in OnActivateAsync; do not register during deactivate.",
        "probe": "rg -n 'RegisterOrUpdateReminder' src",
        "probe_obs": "PackGrain OnActivateAsync. HarborGrain OnDeactivateAsync.",
        "fix_name": "register reminder on activate",
        "fix_diff": "+ public override async Task OnActivateAsync(...) {\n+   await RegisterOrUpdateReminder(\"slip\", TimeSpan.FromSeconds(1), TimeSpan.FromMinutes(1));\n+ }\n",
        "fix_obs": "patched activate register. dump leftover on deactivate.",
        "fail3": "PASS Tick\nFAIL pack leftover: src/PackGrain.cs dump reminder on deactivate",
        "rel": "src/PackGrain.cs",
        "rel_src": "OnDeactivateAsync { RegisterOrUpdateReminder(\"dump\", ...) }",
        "fix2_name": "handoff dump reminder",
        "fix2_diff": "+ // TODO dump reminder on activate",
        "fix2_obs": "tick green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "DelayDeactivation\\(TimeSpan.MaxValue\\)",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/REMINDER.md", "doc_point": "register reminders while active",
        "doc_diff": "+ deactivate is too late. dump leftover.",
        "reg_name": "Tick",
        "reg_diff": "+ reminder fires; slip==5",
        "full_test": "dotnet test",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "reminder on activate; dump leftover.",
        "wrap": "the activate-register path",
        "wrap_obs": "5 passed, 1 residual. Orleans assign reminder registers on activate.",
        "goal": "Designed plant quay-orlrnd: Orleans reminder registered in OnDeactivateAsync so it never ticked. Register on activate. DelayDeactivation during deactivate is too late. dump may remain.",
        "plan": "Repro dotnet test, reject DelayDeactivation, register on activate, hand off dump.",
        "outcome": "Reminder on activate. dump leftover. Partial.",
    })


def airflow_mapped(rnd):
    return expand(rnd, {
        "slug": "pr-airflow-mapped-task-expand-xcom",
        "success": True, "tests": 6, "plant": "lock-afmap",
        "what": "the Airflow mapped task that expanded on a nested XCom list",
        "glob": "**/*.{py,yml}",
        "ls": "src/harbor.py src/pack.py tests/test_harbor.py",
        "impl": "src/harbor.py",
        "impl_src": "assign.expand(n=fetch())  # fetch returns [[4,5]]\n",
        "sym": ".expand", "grep": "expand|XComArg|map_index",
        "grep_obs": "harbor.py expand(n=fetch()). pack.py expand(n=fetch()[0]) / mapped over ints.",
        "test": "pytest tests/test_harbor.py",
        "fail1": "FAIL test_assign: TypeError: n is [4,5] not int; mapped slot 0 got the whole list",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert ti.xcom_pull(map_index=0) == 5",
        "wrong_name": "expand kwargs with a one-element list of lists",
        "wrong_diff": "+ assign.expand(n=[fetch()])",
        "wrong_obs": "still one slot whose n is a list. extra brackets worsen the nesting.",
        "test_one": "pytest tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still TypeError. extra list wrap is more nesting.",
        "reread": "fetch must return [4,5] not [[4,5]]. Flatten XCom.",
        "insight": "flatten the XCom list; expand over ints.",
        "probe": "rg -n 'expand' src",
        "probe_obs": "pack.py fetch returns [4,5]. harbor.py [[4,5]].",
        "fix_name": "flatten fetch XCom",
        "fix_diff": "+ def fetch(): return [4, 5]\n+ assign.expand(n=fetch())\n",
        "fix_obs": "patched flat expand.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.py dump expand still nested",
        "rel": "src/pack.py",
        "rel_src": "dump.expand(n=fetch_nested())",
        "fix2_name": "dump flatten",
        "fix2_diff": "+ dump.expand(n=[0])",
        "fix2_obs": "patched dump.",
        "pass_mid": "PASS 6.",
        "bad_pat": "expand\\(n=\\[fetch\\(\\)\\]\\)",
        "grep2": "none.",
        "doc": "docs/EXPAND.md", "doc_point": "mapped expand needs a flat list",
        "doc_diff": "+ extra brackets nest. flatten XCom.",
        "reg_name": "test_assign map_index 0",
        "reg_diff": "+ slot 0 n=4 slot 1 n=5",
        "full_test": "pytest tests/test_harbor.py",
        "final": "ok 6 passed. Airflow expand is flat.",
        "summary": "flat XCom expand; dump same. 6 tests pass.",
        "wrap": "the flat expand",
        "wrap_obs": "6 passed. Airflow assign maps over ints.",
        "goal": "Designed plant lock-afmap: Airflow mapped task expanded on [[4,5]] so n was a list. Flatten XCom. Extra brackets nest further.",
        "plan": "Repro pytest, reject extra brackets, flatten, fix dump.",
        "outcome": "Flat mapped expand. 6 Airflow tests pass.",
    })


def dagster_io(rnd):
    return expand(rnd, {
        "slug": "pr-dagster-io-manager-mem-key",
        "success": False, "tests": 5, "residual": 1, "plant": "quay-dgstio",
        "what": "the Dagster IO manager that keyed mem artifacts by op name not output name",
        "glob": "**/*.{py,yaml}",
        "ls": "src/harbor.py src/pack.py tests/test_harbor.py",
        "impl": "src/harbor.py",
        "impl_src": "def handle_output(self, context, obj):\n    self._store[context.op_def.name] = obj\n",
        "sym": "handle_output", "grep": "handle_output|load_input|output_name",
        "grep_obs": "harbor.py key op_def.name. pack.py key (op, output_name).",
        "test": "pytest tests/test_harbor.py",
        "fail1": "FAIL test_assign: slip output overwritten by dump output of the same op; got None",
        "fail_name": "test_assign", "test_file": "tests/test_harbor.py",
        "test_src": "assert materialize([assign]).output_value('slip') == 5",
        "wrong_name": "key by run_id only",
        "wrong_diff": "+ self._store[context.run_id] = obj",
        "wrong_obs": "one key per run; still clobbers multiple outputs.",
        "test_one": "pytest tests/test_harbor.py -k assign",
        "fail2": "FAIL test_assign: still clobbered. run_id is not output identity.",
        "reread": "Key by (step_key, output_name) as the built-in mem IO manager does.",
        "insight": "self._store[(context.step_key, context.name)] = obj.",
        "probe": "rg -n 'handle_output|_store' src",
        "probe_obs": "pack.py (step_key, name). harbor.py op_def.name.",
        "fix_name": "key step_key plus output name",
        "fix_diff": "+ self._store[(context.step_key, context.name)] = obj\n",
        "fix_obs": "patched key. dump manager leftover op-name key.",
        "fail3": "PASS test_assign\nFAIL pack leftover: src/pack.py dump IO manager keys op name",
        "rel": "src/pack.py",
        "rel_src": "self._store[context.op_def.name] = obj",
        "fix2_name": "handoff dump IO key",
        "fix2_diff": "+ # TODO dump key (step_key, name)",
        "fix2_obs": "assign green. dump leftover.",
        "pass_mid": "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": "self._store\\[context.run_id\\]",
        "grep2": "none as the fix. leftover dump.",
        "doc": "docs/IO.md", "doc_point": "mem IO keys step_key+output name",
        "doc_diff": "+ op name and run_id clobber outputs. dump leftover.",
        "reg_name": "test_assign slip",
        "reg_diff": "+ slip==5 not clobbered by dump",
        "full_test": "pytest tests/test_harbor.py",
        "final": "5 passed, 1 dump residual. Partial.",
        "summary": "IO key step+output; dump leftover.",
        "wrap": "the output-name key",
        "wrap_obs": "5 passed, 1 residual. Dagster assign IO keys the output name.",
        "goal": "Designed plant quay-dgstio: Dagster mem IO manager keyed by op name so two outputs clobbered. Key (step_key, output name). run_id still clobbers. dump may remain.",
        "plan": "Repro pytest, reject run_id key, step+output, hand off dump.",
        "outcome": "IO key includes output name. dump leftover. Partial.",
    })

LHC_PAIRS = [
    ("pnpm single React vs Bun workspace lock",
     pnpm_peer, bun_lock,
     "auto-install-peers false; workspace override",
     "pnpm packageExtensions; Bun unfrozen install",
     "pnpm dump peer; Bun dump registry pin"),
    ("Hono hc slash vs tRPC superjson",
     hono_rpc, trpc_superjson,
     "trim base slash; matching superjson",
     "Hono RPC key rename; tRPC ISO reviver",
     "Hono dump slash; tRPC dump client"),
    ("Drizzle RQB berths vs SeaORM tuple model",
     drizzle_rqb, seaorm_rel,
     "with.berths; (Slip, Option<Berth>)",
     "Drizzle relationName in with; SeaORM id-as-id",
     "Drizzle dump berth; SeaORM dump model"),
    ("Surreal live id vs EdgeDB multi shape",
     surreal_live, edgedb_card,
     "full-record LIVE SELECT; multi shape",
     "Surreal VALUE n; EdgeDB assert_distinct",
     "Surreal dump DIFF; EdgeDB dump assert_single"),
    ("Dgraph Cond upsert vs Arango FILTER/LIMIT",
     dgraph_upsert, arango_aql,
     "Cond len(v); FILTER then LIMIT",
     "Dgraph always _:new; Arango SORT+LIMIT first",
     "Dgraph dump Cond; Arango dump LIMIT first"),
    ("ZeroMQ ROUTER identity vs Aeron term-length",
     zeromq_router, aeron_term,
     "identity prefix; term-length 256k",
     "ZeroMQ MANDATORY off; Aeron spin-offer",
     "ZeroMQ dump identity; Aeron dump 64k"),
    ("io_uring SQPOLL wakeup vs DPDK mbuf clone",
     iouring_sqpoll, dpdk_mbuf,
     "SQ_WAKEUP; keep original mbuf",
     "io_uring busy-submit; DPDK prefree clone",
     "io_uring dump wakeup; DPDK dump free"),
    ("Oz ByNeed vs Manticore CML poll",
     oz_byneed, manticore_cml,
     "ByNeed without X; CML.sync",
     "Oz WaitNeeded; Manticore spawn+poll",
     "Oz dump; Manticore dump poll"),
    ("Pallene C stack vs MoonScript fat arrow",
     pallene_capi, moonscript_fat,
     "tointeger -1; assign =>",
     "Pallene lua_insert; MoonScript test colon",
     "Pallene dump idx; MoonScript dump ->"),
    ("PyPy continulet vs Cython fused",
     pypy_cont, cython_fused,
     "keep continulet; fused double",
     "PyPy gc.disable; Cython int-cast",
     "PyPy dump del; Cython dump int-only"),
    ("IREE affinity vs ONNX in-place fusion",
     iree_stream, onnx_fusion,
     "matching affinity; ORT_ENABLE_BASIC",
     "IREE try_map; ONNX host copy",
     "IREE dump aff; ONNX dump ENABLE_ALL"),
    ("Slang parameter-block vs PipelineC stall",
     slang_pblock, pipelinec_stall,
     "gLights space1; FUNC_PIPELINE",
     "Slang combined block; PipelineC fake ready",
     "Slang dump space; PipelineC dump WIRES"),
    ("RocksDB merge assoc vs Badger Discard",
     rocksdb_merge, badger_txn,
     "PartialMerge uint add; Update without Discard",
     "RocksDB disable compaction; Badger inner Commit",
     "RocksDB dump concat; Badger dump Discard"),
    ("Akka unstashAll vs Orleans reminder",
     akka_persist, orleans_reminder,
     "unstashAll after become; reminder on activate",
     "Akka unbecome; Orleans DelayDeactivation",
     "Akka dump persist; Orleans dump deactivate"),
    ("Airflow flat expand vs Dagster IO key",
     airflow_mapped, dagster_io,
     "flat XCom; (step_key, output name)",
     "Airflow extra brackets; Dagster run_id key",
     "Airflow dump nested; Dagster dump op-name"),
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
- Not a clone of r4163–r4357 (RPITIT, Prom native hist, ThinLTO, Go loopvar, Django ASGI, GTK sink, Cilk reducer, Io clone, Red PARSE, Rebol, Stata, SAS, SPSS, GAUSS, Crystal, ATS, X10, Inform7, Pike, Eiffel, Self, kdb, Rexx, Nix, Dhall, CUE, Jsonnet, and the rest of that window).
- Bans avoided: RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / `[variant akl]`.
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
