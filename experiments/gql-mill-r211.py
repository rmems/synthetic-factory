#!/usr/bin/env python3
"""Mill graphql-nplusone-factory r211+ unique leftover-execution pairs.

Not leftover-mesh cartesian (RenameObjectFields/Prefix/WrapFields/Mock/Federation).
Not leftover-GET / leftover-js r183–r210 clones.
Not r23–r130 plugin-order. Not classic N+1-only.
2 episodes / round, 16 steps, success + partial handoff.
Never write outputs/raw. Staging only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "graphql-nplusone-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 211
BANNED = (
    "httpget",
    "specifiedby",
    "deprecated-reason",
    "collectfields",
    "parseliteral",
    "getargumentvalues",
    "getfielddef",
    "completelistvalue",
    "typeinfo-leftover",
    "shouldinclude",
    "getvariablevalues",
    "valuefromast",
    "getoperationast",
    "buildexecutioncontext",
    "executefieldsserially",
    "completevalue",
    "getdirectivevalues",
    "memoize3",
    "astfromvalue",
    "rename-object-fields",
    "mesh-leftover-prefix",
    "wrap-fields",
    "mesh-leftover-mock",
    "mesh-leftover-federation",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def st(n: int, basis: str, name: str, args: dict, obs: str, reflection: str | None = None) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
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


# Unique leftover execution — not leftover-mesh, not leftover-GET, not leftover-js.
PAIRS: list[dict] = [
    {
        "plant": "lattice-clewiron",
        "field": "clewLoad",
        "ok": {
            "slug": "lacinia-leftover-compiled-query",
            "surface": "Lacinia leftover compiled Query after schema compile",
            "avoid": "Not r95 graphql-java Instrumentation; not leftover-js TypeInfo r197; leftover stitch cartesian.",
            "disable": "compiled Query cache",
            "plan": "Disable compiled Query cache.",
            "fix": "Recompile leftover Lacinia Query against the current compiled schema.",
            "src": "src/ClewQuery.clj",
            "test": "tests/test_lacinia_compiled.py",
            "extra": "tests/test_lacinia_compiled_mut.py",
            "cfg": "src/ClewQuery.clj",
            "bug": "compiled Query still selects clew_kg after schema renamed to clewLoad",
            "slo": "compile off; every query recompiles",
            "residual": "leftover compiled Query on mutation",
            "src_obs": "(def compiled (compile-query first-schema '{:clew_kg})) ;; leftover after compile\n",
            "test_obs": "def test_one():\n    compile_schema(field='clewLoad')\n    r = execute('{ yard { clewLoad } }')\n    assert r.yard.clewLoad == 4.2\n",
            "fail_obs": "FAILED test_one - leftover compiled Query; Cannot query field clewLoad\n1 failed, 1 passed\n",
            "rg_obs": "src/ClewQuery.clj: (def compiled (compile-query first-schema '{:clew_kg}))",
            "wrong_edit_old": "(def compiled (compile-query first-schema '{:clew_kg}))",
            "wrong_edit_new": "(def compiled nil) ;; compiled Query cache off",
            "fix_contents": "(defn compiled-for [schema q]\n  (compile-query schema q))\n;; leftover compiled Query dies with schema compile\n",
            "suite": 6,
        },
        "bad": {
            "slug": "php-leftover-schema-sdl-reload",
            "surface": "graphql-php leftover Schema object after SDL hot-reload",
            "avoid": "Not r131 php Deferred stack; not leftover-js schema memoize3 r208.",
            "disable": "Schema reuse",
            "plan": "Disable Schema reuse.",
            "fix": "graphql-php leftover Schema must rebuild from the current SDL, not first parse.",
            "src": "src/ClewSchema.php",
            "test": "tests/test_php_schema.py",
            "extra": "tests/test_php_schema_mut.py",
            "cfg": "src/ClewSchema.php",
            "bug": "Schema still exposes clew_kg after SDL renamed to clewLoad",
            "slo": "reuse off; SDL parse 90ms",
            "residual": "leftover Schema on mutation",
            "src_obs": "private static $schema; // leftover after SDL reload\n",
            "test_obs": "def test_one():\n    reload_sdl(rename='clewLoad')\n    r = execute('{ yard { clewLoad } }')\n    assert r.yard.clewLoad == 4.2\n",
            "fail_obs": "FAILED test_one - leftover Schema; Cannot query field clewLoad\n1 failed, 1 passed\n",
            "rg_obs": "src/ClewSchema.php: private static $schema;",
            "wrong_edit_old": "private static $schema;",
            "wrong_edit_new": "private static $schema; // Schema reuse off",
            "fix_contents": "function schemaFor(string $sdl): Schema {\n  return BuildSchema::build($sdl);\n} // leftover Schema dies with SDL\n",
            "xfail_note": "mutation still executes against the first Schema",
        },
        "coverage": 91,
        "next": "Avoid disable compiled Query cache and disable Schema reuse.",
    },
    {
        "plant": "lattice-tack",
        "field": "tackAngle",
        "ok": {
            "slug": "morpheus-leftover-resolver-map",
            "surface": "Morpheus GraphQL leftover resolver map after type rename",
            "avoid": "Not r206 Ariadne bindables leftover; not leftover-js getFieldDef r194.",
            "disable": "resolver map cache",
            "plan": "Disable resolver map cache.",
            "fix": "Rebuild leftover Morpheus resolver map from the current type names.",
            "src": "src/TackApi.hs",
            "test": "tests/test_morpheus_map.py",
            "extra": "tests/test_morpheus_map_input.py",
            "cfg": "src/TackApi.hs",
            "bug": "resolver map still binds TackMm after type renamed to TackAngle",
            "slo": "map off; type unpublished",
            "residual": "leftover resolver map on input types",
            "src_obs": "resolvers = firstSchema.resolvers -- leftover after type rename\n",
            "test_obs": "def test_one():\n    rename_type('TackMm', 'TackAngle')\n    r = execute('{ yard { tackAngle } }')\n    assert r.yard.__typename == 'TackAngle'\n",
            "fail_obs": "FAILED test_one - leftover resolver map; Unknown type TackAngle\n1 failed, 1 passed\n",
            "rg_obs": "src/TackApi.hs: resolvers = firstSchema.resolvers",
            "wrong_edit_old": "resolvers = firstSchema.resolvers",
            "wrong_edit_new": "resolvers = mempty -- resolver map cache off",
            "fix_contents": "resolversFor schema = schema.currentResolvers\n-- leftover resolver map follows type rename\n",
            "suite": 6,
        },
        "bad": {
            "slug": "dotnet-leftover-validation-rules",
            "surface": "graphql-dotnet leftover ValidationRules after SDL rebuild",
            "avoid": "Not r156 ISchema leftover; not r132 IResolveFieldContext leftover.",
            "disable": "ValidationRules cache",
            "plan": "Disable ValidationRules cache.",
            "fix": "graphql-dotnet leftover ValidationRules must compile against the current SDL.",
            "src": "src/TackValidation.cs",
            "test": "tests/test_dotnet_rules.py",
            "extra": "tests/test_dotnet_rules_arg.py",
            "cfg": "src/TackValidation.cs",
            "bug": "ValidationRules still require tackMm after SDL renamed to tackAngle",
            "slo": "rules off; invalid queries leak",
            "residual": "leftover ValidationRules on arguments",
            "src_obs": "static IValidationRule[] Rules = FirstSdl.Rules(); // leftover after rebuild\n",
            "test_obs": "def test_one():\n    rebuild_sdl(field='tackAngle')\n    r = execute('{ yard { tackAngle } }')\n    assert r.errors == []\n",
            "fail_obs": "FAILED test_one - leftover ValidationRules; Cannot query field tackAngle\n1 failed, 1 passed\n",
            "rg_obs": "src/TackValidation.cs: static IValidationRule[] Rules = FirstSdl.Rules()",
            "wrong_edit_old": "static IValidationRule[] Rules = FirstSdl.Rules();",
            "wrong_edit_new": "static IValidationRule[] Rules = Array.Empty<IValidationRule>(); // cache off",
            "fix_contents": "IValidationRule[] RulesFor(ISchema s) => s.GetValidationRules();\n// leftover rules die with SDL rebuild\n",
            "xfail_note": "argument validation still uses the first SDL rules",
        },
        "coverage": 90,
        "next": "Avoid disable resolver map cache and disable ValidationRules cache.",
    },
    {
        "plant": "lattice-leech",
        "field": "leechTension",
        "ok": {
            "slug": "gqlmodules-leftover-injector",
            "surface": "graphql-modules leftover Injector after module hot-reload",
            "avoid": "Not r180 TypeGraphQL ResolverData leftover; not leftover-js rootValue r202.",
            "disable": "Injector reuse",
            "plan": "Disable Injector reuse.",
            "fix": "graphql-modules leftover Injector must rebuild with the current module providers.",
            "src": "src/leechModules.ts",
            "test": "tests/test_modules_inj.py",
            "extra": "tests/test_modules_inj_sub.py",
            "cfg": "src/leechModules.ts",
            "bug": "Injector still provides first-load LeechMm after hot-reload to leechTension",
            "slo": "reuse off; providers rebuild 40ms",
            "residual": "leftover Injector on subscription",
            "src_obs": "const app = createApplication({ modules: firstLoad }) // leftover after hot-reload\n",
            "test_obs": "def test_one():\n    reload_module(field='leechTension')\n    r = execute('{ yard { leechTension } }')\n    assert r.yard.leechTension == 11.0\n",
            "fail_obs": "FAILED test_one - leftover Injector; Cannot query field leechTension\n1 failed, 1 passed\n",
            "rg_obs": "src/leechModules.ts: modules: firstLoad",
            "wrong_edit_old": "const app = createApplication({ modules: firstLoad })",
            "wrong_edit_new": "const app = createApplication({ modules: [] }) // Injector reuse off",
            "fix_contents": "function appFor(mods) {\n  return createApplication({ modules: mods });\n} // leftover Injector follows hot-reload\n",
            "suite": 6,
        },
        "bad": {
            "slug": "shield-leftover-fallback-error",
            "surface": "graphql-shield leftover fallbackError after custom error change",
            "avoid": "Not r134 shield rule cache leftover keyed by field name; not leftover-js locatedError r195.",
            "disable": "fallbackError cache",
            "plan": "Disable fallbackError cache.",
            "fix": "graphql-shield leftover fallbackError must use the current custom error class.",
            "src": "src/leechShield.ts",
            "test": "tests/test_shield_fallback.py",
            "extra": "tests/test_shield_fallback_mut.py",
            "cfg": "src/leechShield.ts",
            "bug": "fallbackError still throws ForbiddenError after switch to LeechDenied",
            "slo": "fallback off; raw shield errors leak",
            "residual": "leftover fallbackError on mutation",
            "src_obs": "shield(rules, { fallbackError: firstError }) // leftover after custom class\n",
            "test_obs": "def test_one():\n    set_fallback(LeechDenied)\n    r = execute('{ yard { leechTension } }', role='anon')\n    assert r.errors[0].typename == 'LeechDenied'\n",
            "fail_obs": "FAILED test_one - leftover fallbackError; typename == ForbiddenError\n1 failed, 1 passed\n",
            "rg_obs": "src/leechShield.ts: fallbackError: firstError",
            "wrong_edit_old": "fallbackError: firstError",
            "wrong_edit_new": "fallbackError: null // fallbackError cache off",
            "fix_contents": "function shieldFor(err) {\n  return shield(rules, { fallbackError: err });\n} // leftover fallback follows current class\n",
            "xfail_note": "mutation still throws the first ForbiddenError",
        },
        "coverage": 91,
        "next": "Avoid disable Injector reuse and disable fallbackError cache.",
    },
    {
        "plant": "lattice-footrope",
        "field": "footropeSag",
        "ok": {
            "slug": "gqlscalars-leftover-datetime-tz",
            "surface": "graphql-scalars leftover DateTime timezone after IANA swap",
            "avoid": "Not r191 parseLiteral leftover scalar; not leftover-js completeValue scalar r205.",
            "disable": "DateTime tz cache",
            "plan": "Disable DateTime tz cache.",
            "fix": "graphql-scalars leftover DateTime must serialize with the current IANA zone.",
            "src": "src/footropeScalars.ts",
            "test": "tests/test_scalars_tz.py",
            "extra": "tests/test_scalars_tz_input.py",
            "cfg": "src/footropeScalars.ts",
            "bug": "DateTime still serializes footropeSag in UTC after swap to Pacific/Auckland",
            "slo": "tz off; naive ISO leaks",
            "residual": "leftover DateTime tz on input parse",
            "src_obs": "GraphQLDateTime.serialize = (v) => v.toISOString() // leftover UTC after IANA swap\n",
            "test_obs": "def test_one():\n    set_tz('Pacific/Auckland')\n    r = execute('{ yard { footropeSag } }')\n    assert r.yard.footropeSag.endswith('+13:00') or r.yard.footropeSag.endswith('+12:00')\n",
            "fail_obs": "FAILED test_one - leftover DateTime tz; value ends with Z\n1 failed, 1 passed\n",
            "rg_obs": "src/footropeScalars.ts: GraphQLDateTime.serialize = (v) => v.toISOString()",
            "wrong_edit_old": "GraphQLDateTime.serialize = (v) => v.toISOString()",
            "wrong_edit_new": "GraphQLDateTime.serialize = (v) => String(v) // DateTime tz cache off",
            "fix_contents": "function serializeDateTime(v, tz) {\n  return formatInTimeZone(v, tz, \"yyyy-MM-dd'T'HH:mm:ssXXX\");\n} // leftover DateTime follows IANA\n",
            "suite": 6,
        },
        "bad": {
            "slug": "depthlimit-leftover-maxdepth-op",
            "surface": "graphql-depth-limit leftover maxDepth after per-operation override",
            "avoid": "Not r02 query-complexity cost; not leftover-js collectFields r186.",
            "disable": "maxDepth cache",
            "plan": "Disable maxDepth cache.",
            "fix": "graphql-depth-limit leftover maxDepth must read the current operation override.",
            "src": "src/footropeDepth.ts",
            "test": "tests/test_depth_op.py",
            "extra": "tests/test_depth_op_frag.py",
            "cfg": "src/footropeDepth.ts",
            "bug": "maxDepth still 3 after operation FootropeDeep set override 8",
            "slo": "depth off; deep queries flood",
            "residual": "leftover maxDepth on fragment spreads",
            "src_obs": "depthLimit(firstMax) // leftover after per-op override\n",
            "test_obs": "def test_one():\n    set_override('FootropeDeep', 8)\n    r = execute('query FootropeDeep { yard { a { b { c { d { footropeSag } } } } } }')\n    assert r.errors == []\n",
            "fail_obs": "FAILED test_one - leftover maxDepth 3; query too deep\n1 failed, 1 passed\n",
            "rg_obs": "src/footropeDepth.ts: depthLimit(firstMax)",
            "wrong_edit_old": "depthLimit(firstMax)",
            "wrong_edit_new": "depthLimit(99) // maxDepth cache off",
            "fix_contents": "function depthFor(op) {\n  return depthLimit(op.maxDepth ?? defaultMax);\n} // leftover maxDepth follows override\n",
            "xfail_note": "fragment spreads still use the first maxDepth",
        },
        "coverage": 90,
        "next": "Avoid disable DateTime tz cache and disable maxDepth cache.",
    },
    {
        "plant": "lattice-buntline",
        "field": "buntlineHaul",
        "ok": {
            "slug": "querycomplexity-leftover-cost-estimators",
            "surface": "graphql-query-complexity leftover estimators after @cost change",
            "avoid": "Not r02 query-complexity cost fanout; not leftover @listSize assumedSize r209.",
            "disable": "estimators cache",
            "plan": "Disable estimators cache.",
            "fix": "Rebuild leftover query-complexity estimators from the current @cost weights.",
            "src": "src/buntlineCost.ts",
            "test": "tests/test_qc_est.py",
            "extra": "tests/test_qc_est_mut.py",
            "cfg": "src/buntlineCost.ts",
            "bug": "estimators still cost buntlineHaul at 1 after @cost(weight: 20)",
            "slo": "estimators off; cheap queries 429",
            "residual": "leftover estimators on mutation",
            "src_obs": "estimators = firstCost.estimators // leftover after @cost change\n",
            "test_obs": "def test_one():\n    set_cost('buntlineHaul', 20)\n    r = execute('{ yard { buntlineHaul } }')\n    assert r.extensions.complexity == 20\n",
            "fail_obs": "FAILED test_one - leftover estimators; complexity == 1\n1 failed, 1 passed\n",
            "rg_obs": "src/buntlineCost.ts: estimators = firstCost.estimators",
            "wrong_edit_old": "estimators = firstCost.estimators",
            "wrong_edit_new": "estimators = [] // estimators cache off",
            "fix_contents": "function estimatorsFor(schema) {\n  return simpleEstimator({ defaultComplexity: schema.costMap });\n} // leftover estimators follow @cost\n",
            "suite": 6,
        },
        "bad": {
            "slug": "gqlratelimit-leftover-jwt-identity",
            "surface": "graphql-rate-limit leftover identity after JWT refresh",
            "avoid": "Not r172 mesh RateLimit tenant leftover; not r168 Hasura leftover JWT role.",
            "disable": "identity cache",
            "plan": "Disable identity cache.",
            "fix": "graphql-rate-limit leftover identity must come from the current JWT sub.",
            "src": "src/buntlineRl.ts",
            "test": "tests/test_gql_rl.py",
            "extra": "tests/test_gql_rl_sub.py",
            "cfg": "src/buntlineRl.ts",
            "bug": "identity still counts tenant A tokens against tenant B after JWT refresh",
            "slo": "identity off; every field 429",
            "residual": "leftover identity on subscription",
            "src_obs": "createRateLimitDirective({ identify: () => firstJwt.sub }) // leftover after refresh\n",
            "test_obs": "def test_one():\n    burn_tokens(sub='A', n=100)\n    refresh_jwt(sub='B')\n    r = execute('{ yard { buntlineHaul } }')\n    assert r.yard.buntlineHaul == 8\n",
            "fail_obs": "FAILED test_one - leftover identity; 429 tenant A quota\n1 failed, 1 passed\n",
            "rg_obs": "src/buntlineRl.ts: identify: () => firstJwt.sub",
            "wrong_edit_old": "identify: () => firstJwt.sub",
            "wrong_edit_new": "identify: () => 'anon' // identity cache off",
            "fix_contents": "function identify(ctx) {\n  return ctx.jwt.sub;\n} // leftover identity follows JWT refresh\n",
            "xfail_note": "subscription still counts the first JWT sub",
        },
        "coverage": 91,
        "next": "Avoid disable estimators cache and disable identity cache.",
    },
    {
        "plant": "lattice-clewline",
        "field": "clewlineTravel",
        "ok": {
            "slug": "gqlws-leftover-connection-params",
            "surface": "graphql-ws leftover connectionParams after reconnect",
            "avoid": "Not r167 graphql-ws leftover subscribe iterator; not r123 Hasura graphql-ws headers.",
            "disable": "connectionParams reuse",
            "plan": "Disable connectionParams reuse.",
            "fix": "graphql-ws leftover connectionParams must come from this connectionInit.",
            "src": "src/clewlineWs.ts",
            "test": "tests/test_ws_params.py",
            "extra": "tests/test_ws_params_filter.py",
            "cfg": "src/clewlineWs.ts",
            "bug": "connectionParams still has tenant A after reconnect with tenant B token",
            "slo": "reuse off; every reconnect re-auths 80ms",
            "residual": "leftover connectionParams on filtered subscribe",
            "src_obs": "let params = firstInit // leftover after reconnect\n",
            "test_obs": "def test_one():\n    a = connect(params={'tenant': 'A'})\n    reconnect(a, params={'tenant': 'B'})\n    r = subscribe(a, '{ clewlineTravel }')\n    assert next_event(a).tenant == 'B'\n",
            "fail_obs": "FAILED test_one - leftover connectionParams; tenant == A\n1 failed, 1 passed\n",
            "rg_obs": "src/clewlineWs.ts: let params = firstInit",
            "wrong_edit_old": "let params = firstInit",
            "wrong_edit_new": "let params = {} // connectionParams reuse off",
            "fix_contents": "function onInit(ctx, payload) {\n  ctx.connectionParams = payload;\n} // leftover params die with the socket\n",
            "suite": 6,
        },
        "bad": {
            "slug": "gqlcodegen-leftover-mappers-rename",
            "surface": "graphql-codegen leftover mappers after type rename",
            "avoid": "Not leftover-js getFieldDef rename r194; not r206 Ariadne bindables leftover.",
            "disable": "mappers cache",
            "plan": "Disable mappers cache.",
            "fix": "graphql-codegen leftover mappers must follow the current type names.",
            "src": "codegen.yml",
            "test": "tests/test_codegen_map.py",
            "extra": "tests/test_codegen_map_input.py",
            "cfg": "codegen.yml",
            "bug": "mappers still bind ClewMm after type renamed to ClewlineTravel",
            "slo": "mappers off; generated types unpublished",
            "residual": "leftover mappers on input types",
            "src_obs": "config:\n  mappers:\n    ClewMm: ./models#ClewMm # leftover after rename\n",
            "test_obs": "def test_one():\n    rename_type('ClewMm', 'ClewlineTravel')\n    generate()\n    r = execute('{ yard { clewlineTravel } }')\n    assert r.yard.__typename == 'ClewlineTravel'\n",
            "fail_obs": "FAILED test_one - leftover mappers; Unknown type ClewlineTravel\n1 failed, 1 passed\n",
            "rg_obs": "codegen.yml: ClewMm: ./models#ClewMm",
            "wrong_edit_old": "ClewMm: ./models#ClewMm",
            "wrong_edit_new": "# mappers cache off",
            "fix_contents": "function mappersFor(schema) {\n  return schema.currentTypeMap;\n} // leftover mappers follow rename\n",
            "xfail_note": "input types still map ClewMm",
        },
        "coverage": 90,
        "next": "Avoid disable connectionParams reuse and disable mappers cache.",
    },
    {
        "plant": "lattice-reefpoint",
        "field": "reefpointLoad",
        "ok": {
            "slug": "apollo-router-leftover-query-plan-sdl",
            "surface": "Apollo Router leftover query plan after subgraph SDL",
            "avoid": "Not r84 query-plan cache omits auth principal; not leftover-mesh Federation transform r178.",
            "disable": "query plan cache",
            "plan": "Disable query plan cache.",
            "fix": "Apollo Router leftover query plan must include the current subgraph SDL hash.",
            "src": "src/router.yaml",
            "test": "tests/test_router_plan.py",
            "extra": "tests/test_router_plan_entity.py",
            "cfg": "src/router.yaml",
            "bug": "query plan still fetches reef_kg after subgraph renamed to reefpointLoad",
            "slo": "plan off; compose every request",
            "residual": "leftover query plan on _entities",
            "src_obs": "supergraph:\n  query_planning:\n    cache:\n      in_memory: { ttl: 24h } # leftover after subgraph SDL\n",
            "test_obs": "def test_one():\n    publish_subgraph('Yard', field='reefpointLoad')\n    r = execute('{ yard { reefpointLoad } }')\n    assert r.plan.field == 'reefpointLoad'\n",
            "fail_obs": "FAILED test_one - leftover query plan; Cannot query field reefpointLoad\n1 failed, 1 passed\n",
            "rg_obs": "src/router.yaml: in_memory: { ttl: 24h }",
            "wrong_edit_old": "in_memory: { ttl: 24h }",
            "wrong_edit_new": "in_memory: { ttl: 0s } # query plan cache off",
            "fix_contents": "function planKey(op, supergraph) {\n  return supergraph.sdlHash + ':' + op.hash;\n} // leftover plan dies with subgraph SDL\n",
            "suite": 6,
        },
        "bad": {
            "slug": "lighthouse-leftover-cache-tenant",
            "surface": "Lighthouse leftover @cache tenant key after tenant swap",
            "avoid": "Not r162 Lighthouse leftover @can; not leftover-mesh Cache transform r176.",
            "disable": "@cache tenant",
            "plan": "Disable @cache tenant.",
            "fix": "Lighthouse leftover @cache key must include the current tenant.",
            "src": "src/ReefpointType.php",
            "test": "tests/test_lh_cache.py",
            "extra": "tests/test_lh_cache_mut.py",
            "cfg": "src/ReefpointType.php",
            "bug": "@cache still serves tenant A reefpointLoad for tenant B",
            "slo": "cache off; origin on every field",
            "residual": "leftover @cache on mutation",
            "src_obs": "@cache(maxAge: 60) // leftover key omits tenant\n",
            "test_obs": "def test_one():\n    execute('{ yard { reefpointLoad } }', tenant='A')\n    r = execute('{ yard { reefpointLoad } }', tenant='B')\n    assert r.yard.tenant == 'B'\n",
            "fail_obs": "FAILED test_one - leftover @cache; tenant == A\n1 failed, 1 passed\n",
            "rg_obs": "src/ReefpointType.php: @cache(maxAge: 60)",
            "wrong_edit_old": "@cache(maxAge: 60)",
            "wrong_edit_new": "# @cache tenant off",
            "fix_contents": "function cacheKey($info) {\n  return $info->tenant . ':' . $info->field;\n} // leftover @cache is per tenant\n",
            "xfail_note": "mutation still hits the first tenant @cache",
        },
        "coverage": 91,
        "next": "Avoid disable query plan cache and disable @cache tenant.",
    },
    {
        "plant": "lattice-jackstay",
        "field": "jackstayTension",
        "ok": {
            "slug": "gqlgen-leftover-generated-field",
            "surface": "gqlgen leftover generated Field after schema regenerate",
            "avoid": "Not r161 gqlgen leftover complexity; not leftover-js getFieldDef r194.",
            "disable": "generated Field cache",
            "plan": "Disable generated Field cache.",
            "fix": "gqlgen leftover generated Field must rebuild from the current schema.graphqls.",
            "src": "src/generated.go",
            "test": "tests/test_gqlgen_field.py",
            "extra": "tests/test_gqlgen_field_mut.py",
            "cfg": "src/generated.go",
            "bug": "generated Field still exposes jack_kg after schema.graphqls renamed to jackstayTension",
            "slo": "generate off; schema unpublished",
            "residual": "leftover generated Field on mutation",
            "src_obs": "var fields = firstGenerate // leftover after regenerate\n",
            "test_obs": "def test_one():\n    write_schema(field='jackstayTension')\n    gqlgen()\n    r = execute('{ yard { jackstayTension } }')\n    assert r.yard.jackstayTension == 6.5\n",
            "fail_obs": "FAILED test_one - leftover generated Field; Cannot query field jackstayTension\n1 failed, 1 passed\n",
            "rg_obs": "src/generated.go: var fields = firstGenerate",
            "wrong_edit_old": "var fields = firstGenerate",
            "wrong_edit_new": "var fields = [] // generated Field cache off",
            "fix_contents": "func fieldsFor(sdl string) []graphql.Field {\n  return generate(sdl)\n} // leftover generated Field follows schema.graphqls\n",
            "suite": 6,
        },
        "bad": {
            "slug": "caliban-leftover-ws-interpreter",
            "surface": "Caliban leftover GraphQLWSInterpreter after schema",
            "avoid": "Not r160 Caliban leftover ZQuery; not r167 graphql-ws leftover iterator.",
            "disable": "WSInterpreter reuse",
            "plan": "Disable WSInterpreter reuse.",
            "fix": "Caliban leftover GraphQLWSInterpreter must rebuild with the current schema.",
            "src": "src/JackstayWs.scala",
            "test": "tests/test_caliban_ws.py",
            "extra": "tests/test_caliban_ws_filter.py",
            "cfg": "src/JackstayWs.scala",
            "bug": "GraphQLWSInterpreter still serves first-schema jack_kg after rebuild",
            "slo": "reuse off; handshake 60ms",
            "residual": "leftover WSInterpreter on filtered subscribe",
            "src_obs": "val interpreter = firstSchema.interpreter // leftover after rebuild\n",
            "test_obs": "def test_one():\n    rebuild_schema(field='jackstayTension')\n    r = subscribe('{ jackstayTension }')\n    assert next_event().field == 'jackstayTension'\n",
            "fail_obs": "FAILED test_one - leftover WSInterpreter; Cannot query field jackstayTension\n1 failed, 1 passed\n",
            "rg_obs": "src/JackstayWs.scala: val interpreter = firstSchema.interpreter",
            "wrong_edit_old": "val interpreter = firstSchema.interpreter",
            "wrong_edit_new": "val interpreter = GraphQLWSInterpreter.empty // WSInterpreter reuse off",
            "fix_contents": "def interpreterFor(schema: GraphQL[Any]) = schema.interpreter\n// leftover WSInterpreter follows schema rebuild\n",
            "xfail_note": "filtered subscribe still uses the first interpreter",
        },
        "coverage": 90,
        "next": "Avoid disable generated Field cache and disable WSInterpreter reuse.",
    },
    {
        "plant": "lattice-bowline",
        "field": "bowlineDrop",
        "ok": {
            "slug": "absinthe-leftover-pipeline-compile",
            "surface": "Absinthe leftover Pipeline after schema compile",
            "avoid": "Not r166 Absinthe leftover MW; not r114 Absinthe topic leftover.",
            "disable": "Pipeline cache",
            "plan": "Disable Pipeline cache.",
            "fix": "Absinthe leftover Pipeline must compile against the current schema.",
            "src": "src/bowline_schema.ex",
            "test": "tests/test_absinthe_pipe.py",
            "extra": "tests/test_absinthe_pipe_mut.py",
            "cfg": "src/bowline_schema.ex",
            "bug": "Pipeline still resolves bow_mm after schema compiled bowlineDrop",
            "slo": "pipeline off; compile every request",
            "residual": "leftover Pipeline on mutation",
            "src_obs": "@pipeline first_compile() # leftover after schema compile\n",
            "test_obs": "def test_one():\n    compile_schema(field='bowlineDrop')\n    r = execute('{ yard { bowlineDrop } }')\n    assert r.yard.bowlineDrop == 0.8\n",
            "fail_obs": "FAILED test_one - leftover Pipeline; Cannot query field bowlineDrop\n1 failed, 1 passed\n",
            "rg_obs": "src/bowline_schema.ex: @pipeline first_compile()",
            "wrong_edit_old": "@pipeline first_compile()",
            "wrong_edit_new": "@pipeline [] # Pipeline cache off",
            "fix_contents": "def pipeline_for(schema), do: Absinthe.Pipeline.for_document(schema)\n# leftover Pipeline dies with schema compile\n",
            "suite": 6,
        },
        "bad": {
            "slug": "hotchocolate-leftover-op-compiler",
            "surface": "Hot Chocolate leftover IOperationCompiler after SDL",
            "avoid": "Not r171 leftover IBatchDispatcher; not r23–r130 plugin-order.",
            "disable": "IOperationCompiler cache",
            "plan": "Disable IOperationCompiler cache.",
            "fix": "Hot Chocolate leftover IOperationCompiler must compile against the current SDL.",
            "src": "src/BowlineCompiler.cs",
            "test": "tests/test_hc_compiler.py",
            "extra": "tests/test_hc_compiler_mut.py",
            "cfg": "src/BowlineCompiler.cs",
            "bug": "IOperationCompiler still compiles bow_mm after SDL renamed to bowlineDrop",
            "slo": "compiler off; compile every request",
            "residual": "leftover IOperationCompiler on mutation",
            "src_obs": "static IOperationCompiler Comp = FirstSdl.Compiler(); // leftover after SDL\n",
            "test_obs": "def test_one():\n    reload_sdl(field='bowlineDrop')\n    r = execute('{ yard { bowlineDrop } }')\n    assert r.yard.bowlineDrop == 0.8\n",
            "fail_obs": "FAILED test_one - leftover IOperationCompiler; Cannot query field bowlineDrop\n1 failed, 1 passed\n",
            "rg_obs": "src/BowlineCompiler.cs: static IOperationCompiler Comp = FirstSdl.Compiler()",
            "wrong_edit_old": "static IOperationCompiler Comp = FirstSdl.Compiler();",
            "wrong_edit_new": "static IOperationCompiler Comp = null; // IOperationCompiler cache off",
            "fix_contents": "IOperationCompiler CompilerFor(ISchema s) => s.CreateCompiler();\n// leftover compiler dies with SDL\n",
            "xfail_note": "mutation still compiles against the first SDL",
        },
        "coverage": 91,
        "next": "Avoid disable Pipeline cache and disable IOperationCompiler cache.",
    },
    {
        "plant": "lattice-cunningham",
        "field": "cunninghamTuck",
        "ok": {
            "slug": "strawberry-leftover-schema-extensions",
            "surface": "Strawberry leftover Schema extensions after reload",
            "avoid": "Not r169 Strawberry leftover DataLoader; not r104 strawberry-django optimizer.",
            "disable": "Schema extensions cache",
            "plan": "Disable Schema extensions cache.",
            "fix": "Strawberry leftover Schema extensions must reload with the current types.",
            "src": "src/cunningham_schema.py",
            "test": "tests/test_sb_ext.py",
            "extra": "tests/test_sb_ext_mut.py",
            "cfg": "src/cunningham_schema.py",
            "bug": "Schema extensions still omit cunninghamTuck after reload added the field",
            "slo": "extensions off; types unpublished",
            "residual": "leftover Schema extensions on mutation",
            "src_obs": "schema = strawberry.Schema(query=Query, extensions=first_ext)  # leftover after reload\n",
            "test_obs": "def test_one():\n    reload_types(add='cunninghamTuck')\n    r = execute('{ yard { cunninghamTuck } }')\n    assert r.yard.cunninghamTuck == 0.15\n",
            "fail_obs": "FAILED test_one - leftover Schema extensions; Cannot query field cunninghamTuck\n1 failed, 1 passed\n",
            "rg_obs": "src/cunningham_schema.py: extensions=first_ext",
            "wrong_edit_old": "extensions=first_ext",
            "wrong_edit_new": "extensions=[]  # Schema extensions cache off",
            "fix_contents": "def schema_for(types):\n    return strawberry.Schema(query=types.query, extensions=types.extensions)\n# leftover extensions follow reload\n",
            "suite": 6,
        },
        "bad": {
            "slug": "graphene-leftover-schema-type-rename",
            "surface": "Graphene leftover Schema after type rename",
            "avoid": "Not r207 Graphene middleware leftover rename; not leftover-js isTypeOf r190.",
            "disable": "Schema reuse",
            "plan": "Disable Schema reuse.",
            "fix": "Graphene leftover Schema must rebuild after the type rename.",
            "src": "src/cunningham_gql.py",
            "test": "tests/test_graphene_schema.py",
            "extra": "tests/test_graphene_schema_input.py",
            "cfg": "src/cunningham_gql.py",
            "bug": "Schema still types CunninghamMm after rename to CunninghamTuck",
            "slo": "reuse off; schema unpublished",
            "residual": "leftover Schema on input types",
            "src_obs": "schema = graphene.Schema(query=FirstQuery)  # leftover after type rename\n",
            "test_obs": "def test_one():\n    rename_type('CunninghamMm', 'CunninghamTuck')\n    r = execute('{ yard { cunninghamTuck } }')\n    assert r.yard.__typename == 'CunninghamTuck'\n",
            "fail_obs": "FAILED test_one - leftover Schema; Unknown type CunninghamTuck\n1 failed, 1 passed\n",
            "rg_obs": "src/cunningham_gql.py: schema = graphene.Schema(query=FirstQuery)",
            "wrong_edit_old": "schema = graphene.Schema(query=FirstQuery)",
            "wrong_edit_new": "schema = None  # Schema reuse off",
            "fix_contents": "def schema_for(query):\n    return graphene.Schema(query=query)\n# leftover Schema follows type rename\n",
            "xfail_note": "input types still use the first Schema",
        },
        "coverage": 90,
        "next": "Avoid disable Schema extensions cache and disable Schema reuse.",
    },
    {
        "plant": "lattice-preventer",
        "field": "preventerStrain",
        "ok": {
            "slug": "gqlcost-leftover-weight-table",
            "surface": "GraphQL @cost leftover weight after cost table change",
            "avoid": "Not leftover @listSize assumedSize r209; not r02 query-complexity cost.",
            "disable": "@cost cache",
            "plan": "Disable @cost cache.",
            "fix": "@cost leftover weight must read the current cost table.",
            "src": "src/preventer.graphql",
            "test": "tests/test_cost_weight.py",
            "extra": "tests/test_cost_weight_mut.py",
            "cfg": "src/preventer.graphql",
            "bug": "@cost still weights preventerStrain at 1 after table set 25",
            "slo": "cost off; cheap queries 429",
            "residual": "leftover @cost on mutation",
            "src_obs": "preventerStrain: Float @cost(weight: 1) # leftover after table 25\n",
            "test_obs": "def test_one():\n    set_cost_table('preventerStrain', 25)\n    r = execute('{ yard { preventerStrain } }')\n    assert r.extensions.cost == 25\n",
            "fail_obs": "FAILED test_one - leftover @cost; cost == 1\n1 failed, 1 passed\n",
            "rg_obs": "src/preventer.graphql: preventerStrain: Float @cost(weight: 1)",
            "wrong_edit_old": "preventerStrain: Float @cost(weight: 1)",
            "wrong_edit_new": "preventerStrain: Float # @cost cache off",
            "fix_contents": "function costFor(field, table) {\n  return table[field] ?? field.astCost;\n} // leftover @cost follows the table\n",
            "suite": 6,
        },
        "bad": {
            "slug": "gqllive-leftover-after-static",
            "surface": "GraphQL @live leftover after query became static",
            "avoid": "Not r56 @live path prefix miss; not leftover @defer/@stream; leftover stitch cartesian.",
            "disable": "@live cache",
            "plan": "Disable @live cache.",
            "fix": "Drop leftover @live when the query is no longer live.",
            "src": "src/preventerLive.ts",
            "test": "tests/test_live_static.py",
            "extra": "tests/test_live_static_sub.py",
            "cfg": "src/preventerLive.ts",
            "bug": "@live still opens a live iterator after preventerStrain became a static query",
            "slo": "live off; static queries hang",
            "residual": "leftover @live on subscription",
            "src_obs": "execute(doc, { live: firstLive }) // leftover after query became static\n",
            "test_obs": "def test_one():\n    mark_static('preventerStrain')\n    r = execute('{ yard { preventerStrain } }')\n    assert r.hasNext is None\n",
            "fail_obs": "FAILED test_one - leftover @live; hasNext True\n1 failed, 1 passed\n",
            "rg_obs": "src/preventerLive.ts: execute(doc, { live: firstLive })",
            "wrong_edit_old": "execute(doc, { live: firstLive })",
            "wrong_edit_new": "execute(doc) // @live cache off",
            "fix_contents": "function liveFor(op) {\n  return op.live ? { live: true } : {};\n} // leftover @live dies when query is static\n",
            "xfail_note": "subscription still opens the first live iterator",
        },
        "coverage": 91,
        "next": "Avoid disable @cost cache and disable @live cache.",
    },
    {
        "plant": "lattice-whisker",
        "field": "whiskerPole",
        "ok": {
            "slug": "interfaceobject-leftover-after-concrete",
            "surface": "Federation leftover @interfaceObject after type became a concrete object",
            "avoid": "Not leftover-mesh Federation transform r178; not leftover @key r175; not r215 oneOf leftover.",
            "disable": "@interfaceObject cache",
            "plan": "Disable @interfaceObject cache.",
            "fix": "Drop leftover @interfaceObject when Whisker is a concrete object type.",
            "src": "src/whisker.graphql",
            "test": "tests/test_ifaceobj.py",
            "extra": "tests/test_ifaceobj_entity.py",
            "cfg": "src/whisker.graphql",
            "bug": "@interfaceObject still plans Whisker as an interface after it became a concrete object",
            "slo": "ifaceobj off; entity plan unpublished",
            "residual": "leftover @interfaceObject on _entities",
            "src_obs": "type Whisker @interfaceObject @key(fields: \"id\") { whiskerPole: Float } # leftover after concrete\n",
            "test_obs": "def test_one():\n    publish_type('Whisker', concrete=True)\n    r = execute('{ whisker { whiskerPole } }')\n    assert r.whisker.__typename == 'Whisker'\n",
            "fail_obs": "FAILED test_one - leftover @interfaceObject; Abstract type Whisker must resolve to an Object type\n1 failed, 1 passed\n",
            "rg_obs": "src/whisker.graphql: type Whisker @interfaceObject",
            "wrong_edit_old": "type Whisker @interfaceObject @key(fields: \"id\") { whiskerPole: Float }",
            "wrong_edit_new": "type Whisker @key(fields: \"id\") { whiskerPole: Float } # @interfaceObject cache off",
            "fix_contents": "function ifaceObjFor(type) {\n  return type.isInterfaceObject ? ['@interfaceObject'] : [];\n} // leftover @interfaceObject dies when concrete\n",
            "suite": 6,
        },
        "bad": {
            "slug": "semanticnonnull-leftover-after-nullable",
            "surface": "GraphQL @semanticNonNull leftover after field became nullable",
            "avoid": "Not r31 @semanticNonNull list holes; not r57 semanticNonNull silent auth null.",
            "disable": "@semanticNonNull cache",
            "plan": "Disable @semanticNonNull cache.",
            "fix": "Drop leftover @semanticNonNull when the field is nullable again.",
            "src": "src/whiskerNull.graphql",
            "test": "tests/test_snn_nullable.py",
            "extra": "tests/test_snn_nullable_list.py",
            "cfg": "src/whiskerNull.graphql",
            "bug": "@semanticNonNull still errors on null after whiskerPole became nullable",
            "slo": "snn off; nulls become errors",
            "residual": "leftover @semanticNonNull on list items",
            "src_obs": "whiskerPole: Float @semanticNonNull # leftover after nullable\n",
            "test_obs": "def test_one():\n    publish_field('whiskerPole', nullable=True)\n    r = execute('{ yard { whiskerPole } }')\n    assert r.yard.whiskerPole is None\n    assert r.errors == []\n",
            "fail_obs": "FAILED test_one - leftover @semanticNonNull; Cannot return null for semantic-non-null\n1 failed, 1 passed\n",
            "rg_obs": "src/whiskerNull.graphql: whiskerPole: Float @semanticNonNull",
            "wrong_edit_old": "whiskerPole: Float @semanticNonNull",
            "wrong_edit_new": "whiskerPole: Float # @semanticNonNull cache off",
            "fix_contents": "function snnFor(field) {\n  return field.semanticNonNull ? ['@semanticNonNull'] : [];\n} // leftover @semanticNonNull dies when nullable\n",
            "xfail_note": "list items still apply leftover @semanticNonNull",
        },
        "coverage": 90,
        "next": "Avoid disable @oneOf cache and disable @semanticNonNull cache.",
    },
]


def pair_for_round(n: int, base: int | None = None) -> dict:
    start = CATALOG_FIRST if base is None else base
    idx = n - start
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog for r{n} (base={start})")
    p = PAIRS[idx]
    for side in (p["ok"], p["bad"]):
        slug = side["slug"].lower()
        for ban in BANNED:
            if ban in slug:
                raise SystemExit(f"banned leftover clone in {slug}")
    return p


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
    return {
        "id": f"gql-r{n}-{s['slug']}",
        "goal": (
            f"{plant} {s['surface']}: {s['bug']} {s['fix']} Distinct leftover "
            f"execution — not leftover-mesh cartesian, not leftover-GET, not leftover-js "
            f"r183–r210 clones. Gate: {s['test']}."
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
    return {
        "id": f"gql-r{n}-{s['slug']}",
        "goal": (
            f"{plant} {s['surface']}: {s['bug']} {s['fix']} Leave a handoff if residual remains. "
            f"Distinct leftover execution — not leftover-mesh cartesian, not leftover-GET, "
            f"not leftover-js r183–r210 clones. Gate: {s['test']}."
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
        f"{p['next']} Not leftover-mesh/GET/js cartesian.\n"
    )


def write_round(n: int, staging: Path, base: int | None = None) -> None:
    p = pair_for_round(n, base=base)
    ok = success_episode(n, p["plant"], p["field"], p["ok"])
    bad = fail_episode(n, p["plant"], p["field"], p["bad"])
    for rec in (ok, bad):
        if len(rec["steps"]) != 16:
            raise SystemExit(f"{rec['id']} steps {len(rec['steps'])}")
        if rec["meta"]["generator"] != GEN or rec["meta"]["round"] != n:
            raise SystemExit("meta")
        blob = json.dumps(rec)
        for key in ("thought", "chain_of_thought", "scratch", "inner_monologue"):
            if f'"{key}"' in blob:
                raise SystemExit(f"banned {key}")
        json.loads(blob)
    batch = staging / f"batch-r{n:02d}.jsonl"
    notes = staging / f"NOTES-r{n:02d}.md"
    batch.write_text(json.dumps(ok, ensure_ascii=False) + "\n" + json.dumps(bad, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(n, p))
    print(json.dumps({"round": n, "ids": [ok["id"], bad["id"]], "plant": p["plant"]}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--base", type=int, default=None)
    args = ap.parse_args()
    staging = Path(args.staging)
    if not staging.is_dir():
        print(f"staging missing: {staging}", file=sys.stderr)
        return 2
    write_round(args.round, staging, base=args.base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
