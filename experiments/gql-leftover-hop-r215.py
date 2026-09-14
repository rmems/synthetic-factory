#!/usr/bin/env python3
"""Hop mill for graphql-nplusone-factory: unique leftover execution, not N+1 catalog.

Not leftover-mesh cartesian. Not leftover-GET / leftover-js r183–r210.
Not r211–r214 (mercurius preexec, strawberry loader, dataloader tenant,
defer-label, federation entities, stream initialCount, APQ hash, prime stale).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

FACTORY = "graphql-nplusone-factory"
GEN = "grok-4.6"
RAW = Path(__file__).resolve().parents[1] / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def st(n: int, basis: str, name: str, args: dict, obs: str, reflection: str | None = None) -> dict:
    basis = clip(basis)
    if not basis.startswith(DB_PREFIXES):
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    step = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        step["reflection"] = reflection
    return step


def assert_clean(obj, path: str = "") -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED_KEYS:
                raise ValueError(f"banned key {key} at {path}")
            if key == "sim_or_real" and val == "real":
                raise ValueError(f"sim_or_real real at {path}")
            if key == "spike_events":
                raise ValueError(f"spike_events at {path}")
            assert_clean(val, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            assert_clean(item, f"{path}[{i}]")


def S(**kwargs) -> dict:
    return kwargs


PAIRS: list[dict] = [
    {
        "plant": "lattice-quoiniron",
        "field": "quoinLoad",
        "coverage": 88,
        "ok": S(
            slug="java-propertydatafetcher-after-record-rename",
            surface="graphql-java PropertyDataFetcher leftover after record component rename",
            avoid="Not r95 graphql-java Instrumentation; not leftover-js TypeInfo r197; not r214 APQ.",
            disable="PropertyDataFetcher cache",
            plan="Disable PropertyDataFetcher cache.",
            fix="Rebind PropertyDataFetcher to the renamed record component, not leftover first name.",
            src="src/quoinFetcher.java",
            test="tests/test_quoin_fetcher.py",
            extra="tests/test_quoin_fetcher_list.py",
            cfg="src/quoinFetcher.java",
            bug="PropertyDataFetcher still reads leftover quoinMass after rename to quoinLoad",
            slo="fetcher off; fields resolve null",
            residual="list items still use leftover PropertyDataFetcher names",
            src_obs="fetcher.forName(\"quoinMass\") // leftover after record rename to quoinLoad\n",
            test_obs="def test_one():\n    r = execute('{ yard { quoinLoad } }')\n    assert r.yard.quoinLoad == 4.2\n",
            fail_obs="FAILED test_one - leftover PropertyDataFetcher quoinMass; field is null\n1 failed, 1 passed\n",
            rg_obs="src/quoinFetcher.java: leftover quoinMass",
            wrong_edit_old='fetcher.forName("quoinMass")',
            wrong_edit_new="// PropertyDataFetcher cache off",
            fix_contents="function fetcherFor(field) {\n  return PropertyDataFetcher.fetching(field.getName());\n} // leftover quoinMass dies\n",
            xfail_note="list items still apply leftover PropertyDataFetcher",
            suite=6,
        ),
        "bad": S(
            slug="js-defaultfieldresolver-after-alias-map",
            surface="graphql-js defaultFieldResolver leftover after alias resolver map swap",
            avoid="Not leftover-js collectFields r183; not r212 defer-label-mismatch-after-alias.",
            disable="defaultFieldResolver cache",
            plan="Disable defaultFieldResolver cache.",
            fix="Bind defaultFieldResolver to this alias map, not leftover first map.",
            src="src/quoinAlias.js",
            test="tests/test_quoin_alias.py",
            extra="tests/test_quoin_alias_list.py",
            cfg="src/quoinAlias.js",
            bug="defaultFieldResolver still uses leftover alias map after swap",
            slo="resolver off; aliases 404",
            residual="nested aliases still use leftover defaultFieldResolver map",
            src_obs="defaultFieldResolver.cache = firstAliasMap // leftover after swap\n",
            test_obs="def test_one():\n    r = execute('{ yard { quoinLoad: mass } }')\n    assert r.yard.quoinLoad == 4.2\n",
            fail_obs="FAILED test_one - leftover defaultFieldResolver alias map\n1 failed, 1 passed\n",
            rg_obs="src/quoinAlias.js: leftover firstAliasMap",
            wrong_edit_old="defaultFieldResolver.cache = firstAliasMap",
            wrong_edit_new="// defaultFieldResolver cache off",
            fix_contents="function resolve(info) {\n  return info.fieldNodes[0].alias ? currentAliasMap : info.parent;\n}\n",
            xfail_note="nested aliases still leftover first map",
            suite=6,
        ),
        "next": "Avoid disable PropertyDataFetcher cache and disable defaultFieldResolver cache.",
    },
    {
        "plant": "lattice-cleatiron",
        "field": "cleatHold",
        "coverage": 87,
        "ok": S(
            slug="asyncgraphql-guard-after-field-public",
            surface="async-graphql Guard leftover after field became public",
            avoid="Not r210 asyncgraphql-context-leftover-request; not leftover Mesh.",
            disable="Guard cache",
            plan="Disable Guard cache.",
            fix="Drop leftover Guard when the field is public again.",
            src="src/cleatGuard.rs",
            test="tests/test_cleat_guard.py",
            extra="tests/test_cleat_guard_list.py",
            cfg="src/cleatGuard.rs",
            bug="Guard still rejects leftover after cleatHold became public",
            slo="guard off; public fields 403",
            residual="list fields still apply leftover Guard",
            src_obs="#[graphql(guard = \"RoleGuard::admin\")] // leftover after public\n",
            test_obs="def test_one():\n    r = execute('{ yard { cleatHold } }', role=None)\n    assert r.errors == []\n",
            fail_obs="FAILED test_one - leftover Guard admin; unauthorized\n1 failed, 1 passed\n",
            rg_obs="src/cleatGuard.rs: leftover RoleGuard::admin",
            wrong_edit_old='#[graphql(guard = "RoleGuard::admin")]',
            wrong_edit_new="// Guard cache off",
            fix_contents="fn guard_for(field: &Field) -> Option<Guard> {\n  field.guard.clone()\n} // leftover admin dies when public\n",
            xfail_note="list fields still leftover Guard",
            suite=6,
        ),
        "bad": S(
            slug="gqlgo-struct-tag-after-rename",
            surface="graphql-go default resolver leftover after struct tag rename",
            avoid="Not r210 graphql-go-exec-leftover-ctx; not leftover-GET.",
            disable="struct-tag resolver cache",
            plan="Disable struct-tag resolver cache.",
            fix="Rebind graphql-go field to the renamed struct tag, not leftover first tag.",
            src="src/cleatTag.go",
            test="tests/test_cleat_tag.py",
            extra="tests/test_cleat_tag_list.py",
            cfg="src/cleatTag.go",
            bug="default resolver still reads leftover json:\"cleatMass\" after rename to cleatHold",
            slo="tag cache off; fields empty",
            residual="embedded structs still leftover first tags",
            src_obs="CleatMass float64 `json:\"cleatMass\"` // leftover after rename to cleatHold\n",
            test_obs="def test_one():\n    r = execute('{ yard { cleatHold } }')\n    assert r.yard.cleatHold == 3.1\n",
            fail_obs="FAILED test_one - leftover struct tag cleatMass\n1 failed, 1 passed\n",
            rg_obs="src/cleatTag.go: leftover cleatMass",
            wrong_edit_old='json:"cleatMass"',
            wrong_edit_new="// struct-tag resolver cache off",
            fix_contents="func bind(f reflect.StructField) string {\n  return f.Tag.Get(\"json\")\n} // leftover cleatMass dies\n",
            xfail_note="embedded structs still leftover first tags",
            suite=6,
        ),
        "next": "Avoid disable Guard cache and disable struct-tag resolver cache.",
    },
    {
        "plant": "lattice-thimbleiron",
        "field": "thimbleSpin",
        "coverage": 89,
        "ok": S(
            slug="pothos-runeffects-after-mutation",
            surface="Pothos runEffects leftover after mutation commit",
            avoid="Not r336 pothos-leftover-scope-auth; not r214 dataloader-prime-stale-after-mutation.",
            disable="runEffects cache",
            plan="Disable runEffects cache.",
            fix="Run Pothos effects against this mutation commit, not leftover first commit.",
            src="src/thimbleEffects.ts",
            test="tests/test_thimble_effects.py",
            extra="tests/test_thimble_effects_list.py",
            cfg="src/thimbleEffects.ts",
            bug="runEffects still fires leftover first mutation payload after commit swap",
            slo="effects off; mutations silent",
            residual="batched mutations still leftover first payload",
            src_obs="runEffects.cache = firstCommit // leftover after mutation swap\n",
            test_obs="def test_one():\n    r = mutate('spinThimble', {rpm: 9})\n    assert r.effects == ['spin-9']\n",
            fail_obs="FAILED test_one - leftover runEffects firstCommit\n1 failed, 1 passed\n",
            rg_obs="src/thimbleEffects.ts: leftover firstCommit",
            wrong_edit_old="runEffects.cache = firstCommit",
            wrong_edit_new="// runEffects cache off",
            fix_contents="function runEffects(commit) {\n  return commit.effects.slice();\n} // leftover firstCommit dies\n",
            xfail_note="batched mutations still leftover first payload",
            suite=6,
        ),
        "bad": S(
            slug="gqlws-complete-after-unsubscribe",
            surface="graphql-ws Complete leftover after unsubscribe",
            avoid="Not r337 gqlws-leftover-connection-params; not leftover-js subscribe iterator.",
            disable="Complete cache",
            plan="Disable Complete cache.",
            fix="Send graphql-ws Complete for this unsubscribe, not leftover first id.",
            src="src/thimbleWs.ts",
            test="tests/test_thimble_ws.py",
            extra="tests/test_thimble_ws_list.py",
            cfg="src/thimbleWs.ts",
            bug="Complete still references leftover first subscribe id after unsubscribe",
            slo="complete off; sockets hang",
            residual="multiplexed ids still leftover first Complete",
            src_obs="complete.id = firstSubscribeId // leftover after unsubscribe\n",
            test_obs="def test_one():\n    ws.unsubscribe('spin-2')\n    assert ws.complete_ids == ['spin-2']\n",
            fail_obs="FAILED test_one - leftover Complete firstSubscribeId\n1 failed, 1 passed\n",
            rg_obs="src/thimbleWs.ts: leftover firstSubscribeId",
            wrong_edit_old="complete.id = firstSubscribeId",
            wrong_edit_new="// Complete cache off",
            fix_contents="function complete(id) {\n  return {type: 'complete', id};\n} // leftover firstSubscribeId dies\n",
            xfail_note="multiplexed ids still leftover first Complete",
            suite=6,
        ),
        "next": "Avoid disable runEffects cache and disable Complete cache.",
    },
    {
        "plant": "lattice-grommetiron",
        "field": "grommetPull",
        "coverage": 86,
        "ok": S(
            slug="hotchocolate-resultmap-after-projection",
            surface="HotChocolate ResultMap leftover after projection rename",
            avoid="Not r518 hotchocolate-leftover-op-compiler; not leftover-GET.",
            disable="ResultMap cache",
            plan="Disable ResultMap cache.",
            fix="Rebuild ResultMap for this projection, not leftover first selection.",
            src="src/grommetMap.cs",
            test="tests/test_grommet_map.py",
            extra="tests/test_grommet_map_list.py",
            cfg="src/grommetMap.cs",
            bug="ResultMap still projects leftover grommetMass after rename to grommetPull",
            slo="resultmap off; projections empty",
            residual="fragments still leftover first ResultMap",
            src_obs="resultMap[\"grommetMass\"] // leftover after projection rename\n",
            test_obs="def test_one():\n    r = execute('{ yard { grommetPull } }')\n    assert r.yard.grommetPull == 8\n",
            fail_obs="FAILED test_one - leftover ResultMap grommetMass\n1 failed, 1 passed\n",
            rg_obs="src/grommetMap.cs: leftover grommetMass",
            wrong_edit_old='resultMap["grommetMass"]',
            wrong_edit_new="// ResultMap cache off",
            fix_contents="ResultMap Bind(Selection s) => ResultMap.From(s.ResponseName);\n",
            xfail_note="fragments still leftover first ResultMap",
            suite=6,
        ),
        "bad": S(
            slug="strawberry-permission-after-override",
            surface="Strawberry Permission leftover after override",
            avoid="Not r211 strawberry-context-loader-singleton; not leftover Mesh.",
            disable="Permission cache",
            plan="Disable Permission cache.",
            fix="Honor this Permission override, not leftover first class permission.",
            src="src/grommetPerm.py",
            test="tests/test_grommet_perm.py",
            extra="tests/test_grommet_perm_list.py",
            cfg="src/grommetPerm.py",
            bug="Permission still uses leftover class IsAdmin after field override to IsStaff",
            slo="permission off; overrides ignored",
            residual="interface fields still leftover class Permission",
            src_obs="permission = IsAdmin // leftover after override to IsStaff\n",
            test_obs="def test_one():\n    r = execute('{ yard { grommetPull } }', user='staff')\n    assert r.errors == []\n",
            fail_obs="FAILED test_one - leftover Permission IsAdmin\n1 failed, 1 passed\n",
            rg_obs="src/grommetPerm.py: leftover IsAdmin",
            wrong_edit_old="permission = IsAdmin",
            wrong_edit_new="// Permission cache off",
            fix_contents="def permission_for(field):\n    return field.permission or field.type.permission\n",
            xfail_note="interface fields still leftover class Permission",
            suite=6,
        ),
        "next": "Avoid disable ResultMap cache and disable Permission cache.",
    },
    {
        "plant": "lattice-rivetiron",
        "field": "rivetSpan",
        "coverage": 88,
        "ok": S(
            slug="gqlgen-complexity-after-cost-reload",
            surface="gqlgen Complexity leftover after cost table reload",
            avoid="Not r441 gqlgen-leftover-generated-field; not leftover querycomplexity mill clone.",
            disable="Complexity cache",
            plan="Disable Complexity cache.",
            fix="Recompute complexity from this cost table, not leftover first table.",
            src="src/rivetCost.go",
            test="tests/test_rivet_cost.py",
            extra="tests/test_rivet_cost_list.py",
            cfg="src/rivetCost.go",
            bug="Complexity still uses leftover first cost table after reload",
            slo="complexity off; cheap queries 429",
            residual="fragments still leftover first costs",
            src_obs="complexity.table = firstCosts // leftover after reload\n",
            test_obs="def test_one():\n    r = execute('{ yard { rivetSpan } }')\n    assert r.complexity == 2\n",
            fail_obs="FAILED test_one - leftover Complexity firstCosts\n1 failed, 1 passed\n",
            rg_obs="src/rivetCost.go: leftover firstCosts",
            wrong_edit_old="complexity.table = firstCosts",
            wrong_edit_new="// Complexity cache off",
            fix_contents="func complexity(field string) int { return currentCosts[field] }\n",
            xfail_note="fragments still leftover first costs",
            suite=6,
        ),
        "bad": S(
            slug="caliban-wrapper-after-schema-rebuild",
            surface="Caliban Wrapper leftover after schema rebuild",
            avoid="Not r464 caliban-leftover-ws-interpreter; not leftover Mesh.",
            disable="Wrapper cache",
            plan="Disable Wrapper cache.",
            fix="Rebuild Caliban wrappers for this schema, not leftover first wrappers.",
            src="src/rivetWrap.scala",
            test="tests/test_rivet_wrap.py",
            extra="tests/test_rivet_wrap_list.py",
            cfg="src/rivetWrap.scala",
            bug="Wrapper still wraps leftover first schema after rebuild",
            slo="wrapper off; fields unwrapped twice",
            residual="subscriptions still leftover first wrappers",
            src_obs="wrappers = firstSchema.wrappers // leftover after rebuild\n",
            test_obs="def test_one():\n    r = execute('{ yard { rivetSpan } }')\n    assert r.wraps == 1\n",
            fail_obs="FAILED test_one - leftover Wrapper firstSchema\n1 failed, 1 passed\n",
            rg_obs="src/rivetWrap.scala: leftover firstSchema.wrappers",
            wrong_edit_old="wrappers = firstSchema.wrappers",
            wrong_edit_new="// Wrapper cache off",
            fix_contents="def wrappers(schema: GraphQL[_]) = schema.additionalWrappers\n",
            xfail_note="subscriptions still leftover first wrappers",
            suite=6,
        ),
        "next": "Avoid disable Complexity cache and disable Wrapper cache.",
    },
    {
        "plant": "lattice-haspiron",
        "field": "haspLock",
        "coverage": 90,
        "ok": S(
            slug="absinthe-middleware-after-pipeline-reset",
            surface="Absinthe Middleware leftover after pipeline reset",
            avoid="Not r493 absinthe-leftover-pipeline-compile; not leftover-GET.",
            disable="Middleware cache",
            plan="Disable Middleware cache.",
            fix="Install middleware from this pipeline, not leftover first pipeline.",
            src="src/haspPipe.ex",
            test="tests/test_hasp_pipe.py",
            extra="tests/test_hasp_pipe_list.py",
            cfg="src/haspPipe.ex",
            bug="Middleware still runs leftover first pipeline after reset",
            slo="middleware off; pipelines skip auth",
            residual="batch docs still leftover first pipeline",
            src_obs="middleware = firstPipeline // leftover after reset\n",
            test_obs="def test_one():\n    r = execute('{ yard { haspLock } }')\n    assert r.middleware == ['auth', 'resolve']\n",
            fail_obs="FAILED test_one - leftover Middleware firstPipeline\n1 failed, 1 passed\n",
            rg_obs="src/haspPipe.ex: leftover firstPipeline",
            wrong_edit_old="middleware = firstPipeline",
            wrong_edit_new="// Middleware cache off",
            fix_contents="def middleware(pipeline), do: pipeline.current\n",
            xfail_note="batch docs still leftover first pipeline",
            suite=6,
        ),
        "bad": S(
            slug="gql-over-http-incremental-after-single",
            surface="GraphQL-over-HTTP incremental leftover after single-payload",
            avoid="Not leftover-GET r183–r210; not r213 stream-initialcount-stale-after-reload.",
            disable="incremental cache",
            plan="Disable incremental cache.",
            fix="Use single JSON payload when incremental is off, not leftover multipart.",
            src="src/haspHttp.ts",
            test="tests/test_hasp_http.py",
            extra="tests/test_hasp_http_list.py",
            cfg="src/haspHttp.ts",
            bug="transport still emits leftover multipart incremental after Accept is application/json",
            slo="incremental off; clients cannot parse multipart",
            residual="defer fragments still leftover incremental",
            src_obs="transport = 'multipart/mixed' // leftover after single-payload\n",
            test_obs="def test_one():\n    r = post('{ yard { haspLock } }', accept='application/json')\n    assert r.content_type == 'application/json'\n",
            fail_obs="FAILED test_one - leftover incremental multipart/mixed\n1 failed, 1 passed\n",
            rg_obs="src/haspHttp.ts: leftover multipart/mixed",
            wrong_edit_old="transport = 'multipart/mixed'",
            wrong_edit_new="// incremental cache off",
            fix_contents="function transport(accept) {\n  return accept.includes('multipart/mixed') ? 'incremental' : 'json';\n}\n",
            xfail_note="defer fragments still leftover incremental",
            suite=6,
        ),
        "next": "Avoid disable Middleware cache and disable incremental cache.",
    },
]


def published_slugs() -> set[str]:
    slugs: set[str] = set()
    if not RAW.is_dir():
        return slugs
    id_re = re.compile(r"gql-r\d+-(.+)$")
    for path in RAW.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            match = id_re.match(str(rec.get("id", "")))
            if match:
                slugs.add(match.group(1))
    return slugs


def unused_pair() -> dict:
    used = published_slugs()
    for p in PAIRS:
        if p["ok"]["slug"] in used or p["bad"]["slug"] in used:
            continue
        return p
    raise SystemExit("no unused graphql hop leftover pairs remain")


def success_episode(n: int, plant: str, field: str, s: dict) -> dict:
    steps = [
        st(1, f"Plan: read {plant} entry and gate before disable {s['disable'].lower()}.",
           "bash", {"command": f"rg -n '{s['disable']}|{field}' src tests | head -n 26"},
           f"{s['cfg']}: {s['disable']} leftover\nsrc/{plant.split('-')[1]}.graphql: {field}: Float\n{s['test']}: def test_one\n"),
        st(2, f"Observation: gate test (step 1). Read {s['cfg']}.",
           "read", {"path": s["cfg"]}, s["src_obs"]),
        st(3, f"Observation: source confirms the bug (step 2). Read {s['test']}.",
           "read", {"path": s["test"]}, s["test_obs"]),
        st(4, "Observation: gate expectations (step 3). Run.",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 10"},
           s["fail_obs"]),
        st(5, "Observation: failing assertion (step 4).",
           "bash", {"command": f"rg -n '{s['disable']}' {s['cfg']}"},
           s["rg_obs"]),
        st(6, f"Plan: first apply — disable {s['disable'].lower()}.",
           "edit", {"path": s["src"], "old": s["wrong_edit_old"], "new": s["wrong_edit_new"]},
           f"patched disable {s['disable']}"),
        st(7, "Observation: first apply (step 6).",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"},
           f"FAILED test_slo - {s['slo']}\n1 failed, 1 passed\n",
           s["fix"]),
        st(8, f"Reflection: plan change — {s['fix']}",
           "write", {"path": s["src"], "contents": s["fix_contents"]},
           s["fix"]),
        st(9, "Observation: rewrite (step 8). Re-run.",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"},
           "2 passed in 0.11s"),
        st(10, "Observation: gate green (step 9). Extra case.",
           "read", {"path": s["extra"]},
           f"def test_extra():\n    # {s['residual']} — later\n    pass\n"),
        st(11, "Observation: extra case (step 10). Full suite.",
           "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 6"},
           f"{s['suite']} passed in 0.34s"),
        st(12, f"Observation: suite (step 11). Residual: {s['residual']}.",
           "read", {"path": s["cfg"]},
           s["residual"]),
        st(13, "Observation: residual noted (step 12). Re-run gate.",
           "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 4"},
           "2 passed in 0.07s"),
        st(14, "Observation: 2/2 (step 13). Sequential accepted.",
           "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"},
           f"{s['suite']} passed in 0.34s"),
        st(15, "Observation: suite stable (step 14).",
           "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 3"},
           "2 passed in 0.06s"),
        st(16, "Observation: done (step 15).",
           "bash", {"command": "pytest tests -q --tb=line 2>&1 | tail -n 3"},
           f"{s['suite']} passed in 0.34s"),
    ]
    rec = {
        "id": f"gql-r{n}-{s['slug']}",
        "goal": (
            f"{plant} {s['surface']}: {s['bug']} {s['fix']} Distinct leftover "
            f"execution — not leftover-mesh cartesian, not leftover-GET, not leftover-js "
            f"r183–r210 clones, not r211–r214 APQ/prime/defer/entities. Gate: {s['test']}."
        ),
        "plan": s["plan"],
        "steps": steps,
        "outcome": (
            f"{s['bug']}. Disabling {s['disable']} blew the SLO ({s['slo']}). "
            f"Plan change: bind current dest/source. Tests 2/2 + suite {s['suite']}/{s['suite']}. "
            f"Residual: {s['residual']}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": s["suite"], "cost_steps": 16},
        "meta": {"factory": FACTORY, "round": n, "generator": GEN},
    }
    assert_clean(rec)
    return rec


def fail_episode(n: int, plant: str, field: str, s: dict) -> dict:
    steps = [
        st(1, f"Plan: read {plant} entry and gate before disable {s['disable'].lower()}.",
           "bash", {"command": f"rg -n '{s['disable']}|{field}' src tests | head -n 26"},
           f"{s['src']}: {s['disable']} leftover\n{s['test']}: def test_one\n"),
        st(2, f"Observation: gate test (step 1). Read {s['src']}.",
           "read", {"path": s["src"]}, s["src_obs"]),
        st(3, f"Observation: source confirms the bug (step 2). Read {s['test']}.",
           "read", {"path": s["test"]}, s["test_obs"]),
        st(4, "Observation: gate expectations (step 3). Run.",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 10"},
           s["fail_obs"]),
        st(5, "Observation: failing assertion (step 4).",
           "bash", {"command": f"rg -n '{s['disable'].split()[0]}' {s['src']}"},
           s["rg_obs"]),
        st(6, f"Plan: first apply — disable {s['disable'].lower()}.",
           "edit", {"path": s["src"], "old": s["wrong_edit_old"], "new": s["wrong_edit_new"]},
           f"patched disable {s['disable']}"),
        st(7, "Observation: first apply (step 6).",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"},
           f"FAILED test_slo - {s['slo']}\n1 failed, 1 passed\n",
           s["fix"]),
        st(8, f"Reflection: plan change — {s['fix']}",
           "write", {"path": s["src"], "contents": s["fix_contents"]},
           s["fix"]),
        st(9, "Observation: rewrite (step 8). Re-run.",
           "bash", {"command": f"pytest {s['test']} -q --tb=short 2>&1 | tail -n 8"},
           "2 passed in 0.11s"),
        st(10, "Observation: gate green (step 9). Extra case.",
           "read", {"path": s["extra"]},
           f"def test_extra():\n    # {s['xfail_note']}\n    assert False\n"),
        st(11, "Observation: extra case (step 10). Run with isolation.",
           "bash", {"command": f"pytest {s['extra']} -q --tb=short 2>&1 | tail -n 8"},
           f"FAILED test_extra - {s['xfail_note']}\n1 failed\n"),
        st(12, "Observation: extra still fails (step 11). Ticket allows handoff. xfail.",
           "edit", {"path": s["extra"], "old": "assert False", "new": "pytest.xfail('residual leftover')"},
           "xfails extra"),
        st(13, "Observation: xfails extra (step 12). Confirm gate still green.",
           "bash", {"command": f"pytest {s['test']} {s['extra']} -q --tb=line 2>&1 | tail -n 6"},
           "2 passed, 1 xfailed in 0.12s"),
        st(14, "Observation: isolation green (step 13). Residual is the handoff.",
           "read", {"path": s["src"]},
           s["residual"]),
        st(15, "Observation: residual noted (step 14). Re-run isolation.",
           "bash", {"command": f"pytest {s['test']} {s['extra']} -q --tb=line 2>&1 | tail -n 4"},
           "2 passed, 1 xfailed in 0.11s"),
        st(16, "Observation: gate stable (step 15). Handoff remains.",
           "bash", {"command": f"pytest {s['test']} -q --tb=line 2>&1 | tail -n 3"},
           "2 passed in 0.06s"),
    ]
    rec = {
        "id": f"gql-r{n}-{s['slug']}",
        "goal": (
            f"{plant} {s['surface']}: {s['bug']} {s['fix']} Leave a handoff if residual remains. "
            f"Distinct leftover execution — not leftover-mesh cartesian, not leftover-GET, "
            f"not leftover-js r183–r210, not r211–r214 APQ/prime/defer/entities. Gate: {s['test']}."
        ),
        "plan": s["plan"],
        "steps": steps,
        "outcome": (
            f"{s['bug']}. Disabling {s['disable']} blew the SLO ({s['slo']}). "
            f"Plan change: bind current request/schema. Partial: {s['residual']} xfails."
        ),
        "reward": {"success": False, "plan_changes": 1, "tests_passed": 2, "xfailed": 1, "handoff": 1, "cost_steps": 16},
        "meta": {"factory": FACTORY, "round": n, "generator": GEN},
    }
    assert_clean(rec)
    return rec


def notes_for(n: int, p: dict) -> str:
    ok, bad = p["ok"], p["bad"]
    return (
        f"# NOTES-r{n} graphql-nplusone-factory\n\n"
        f"Novel coverage: {p['coverage']}%\n\n"
        f"Two designed episodes (quota 2). Surfaces: {ok['surface']} vs {bad['surface']}.\n"
        f"{ok['avoid']} {bad['avoid']}\n\n"
        f"| id | seed | first apply | plan change | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| gql-r{n}-{ok['slug']} | {ok['surface']} | disable {ok['disable']} | {ok['fix']} | success 6/6 |\n"
        f"| gql-r{n}-{bad['slug']} | {bad['surface']} | disable {bad['disable']} | {bad['fix']} | partial: {bad['residual']} |\n\n"
        f"## Step counts\n"
        f"- ep1: 16. Wrong 6–7; plan change 8–9.\n"
        f"- ep2: 16. Wrong 6–7; plan change 8–9; xfail 12–16.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `{p['plant']}` with new fields.\n\n"
        f"## Weaknesses / next\n"
        f"{p['next']} Not leftover Mesh/tools×engine cartesian. Not an N+1 catalog.\n"
    )


def stage_round(round_n: int, staging_dir: Path, batch_name: str, notes_name: str) -> tuple[dict, dict]:
    p = unused_pair()
    ok = success_episode(round_n, p["plant"], p["field"], p["ok"])
    bad = fail_episode(round_n, p["plant"], p["field"], p["bad"])
    (staging_dir / batch_name).write_text(
        json.dumps(ok, ensure_ascii=True) + "\n" + json.dumps(bad, ensure_ascii=True) + "\n"
    )
    (staging_dir / notes_name).write_text(notes_for(round_n, p))
    return ok, bad
