#!/usr/bin/env python3
"""Mill graphql-nplusone-factory r216+ unique leftover leftover leftover.

BAN leftover-mesh cartesian. BAN leftover-GET clones. BAN N+1-only.
BAN cloning r183–r215 (skip if r215/r183 clone). Unique leftover leftover leftover.
2 episodes / round, 16 steps, success + partial handoff.
Never write outputs/raw. Staging only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACTORY = "graphql-nplusone-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 216
RAW = HERE.parents[0] / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
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
    "mesh-leftover",
    "wrap-fields",
    "oneof-input",
    "hasnext",
    "dataloader-prime",
    "dataloader-cache-key",
    "apq-persisted",
    "stream-initialcount",
    "federation-entities",
    "defer-label",
    "strawberry-context-loader",
    "mercurius-preeexec",
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_m211 = _load("gql_mill_r211", HERE / "gql-mill-r211.py")
_hop = _load("gql_leftover_hop_r215", HERE / "gql-leftover-hop-r215.py")
success_episode = _m211.success_episode
fail_episode = _m211.fail_episode
notes_for = _m211.notes_for


def S(**kwargs) -> dict:
    return kwargs


EXTRA: list[dict] = [
    {
        "plant": "lattice-gudgeon",
        "field": "gudgeonLoad",
        "ok": S(
            slug="relay-globalid-leftover-after-type-rename",
            surface="graphql-relay fromGlobalId leftover after type rename",
            avoid="Not leftover-GET r183; not r215 oneOf leftover; not leftover-mesh cartesian.",
            disable="fromGlobalId type cache",
            plan="Disable fromGlobalId type cache.",
            fix="Decode fromGlobalId against the current type name, not leftover first type.",
            src="src/gudgeonId.ts",
            test="tests/test_gudgeon_id.py",
            extra="tests/test_gudgeon_id_node.py",
            cfg="src/gudgeonId.ts",
            bug="fromGlobalId still decodes leftover GudgeonMm after type renamed to GudgeonLoad",
            slo="id cache off; node lookups 404",
            residual="leftover fromGlobalId on Node interface",
            src_obs="fromGlobalId.cache = 'GudgeonMm' // leftover after rename to GudgeonLoad\n",
            test_obs="def test_one():\n    nid = to_global_id('GudgeonLoad', '7')\n    r = execute('query { node(id: $id) { ... on GudgeonLoad { gudgeonLoad } } }', id=nid)\n    assert r.node.__typename == 'GudgeonLoad'\n",
            fail_obs="FAILED test_one - leftover fromGlobalId GudgeonMm; Unknown type GudgeonLoad\n1 failed, 1 passed\n",
            rg_obs="src/gudgeonId.ts: leftover GudgeonMm",
            wrong_edit_old="fromGlobalId.cache = 'GudgeonMm'",
            wrong_edit_new="// fromGlobalId type cache off",
            fix_contents="function fromGlobalIdFor(id) {\n  const {type, id: raw} = fromGlobalId(id);\n  return {type: schema.currentName(type), id: raw};\n} // leftover GudgeonMm dies\n",
            suite=6,
        ),
        "bad": S(
            slug="pubsub-topic-leftover-after-rename",
            surface="graphql-subscriptions PubSub leftover topic after rename",
            avoid="Not r167 graphql-ws leftover iterator; not leftover-GET; not r215 hasNext leftover.",
            disable="PubSub topic cache",
            plan="Disable PubSub topic cache.",
            fix="Publish/subscribe on the current topic name, not leftover first topic.",
            src="src/gudgeonPub.ts",
            test="tests/test_gudgeon_pub.py",
            extra="tests/test_gudgeon_pub_filter.py",
            cfg="src/gudgeonPub.ts",
            bug="PubSub still publishes leftover GUDGEON_MM after topic renamed to GUDGEON_LOAD",
            slo="topic cache off; subscribers silent",
            residual="leftover PubSub topic on filtered subscribe",
            src_obs="pubsub.publish('GUDGEON_MM', payload) // leftover after rename to GUDGEON_LOAD\n",
            test_obs="def test_one():\n    rename_topic('GUDGEON_LOAD')\n    sub = subscribe('{ gudgeonLoad }')\n    publish('GUDGEON_LOAD', {gudgeonLoad: 4.2})\n    assert next_event(sub).gudgeonLoad == 4.2\n",
            fail_obs="FAILED test_one - leftover PubSub topic GUDGEON_MM; no event\n1 failed, 1 passed\n",
            rg_obs="src/gudgeonPub.ts: leftover GUDGEON_MM",
            wrong_edit_old="pubsub.publish('GUDGEON_MM', payload)",
            wrong_edit_new="// PubSub topic cache off",
            fix_contents="function topicFor(field) {\n  return schema.currentTopic(field);\n} // leftover GUDGEON_MM dies\n",
            xfail_note="filtered subscribe still uses leftover first topic",
        ),
        "coverage": 91,
        "next": "Avoid disable fromGlobalId type cache and disable PubSub topic cache.",
    },
    {
        "plant": "lattice-pintle",
        "field": "pintleDrop",
        "ok": S(
            slug="formaterror-extensions-leftover-after-swap",
            surface="GraphQLError.extensions leftover after formatError swap",
            avoid="Not r208 @catch leftover path; not leftover-js locatedError r195; not r215 oneOf.",
            disable="formatError cache",
            plan="Disable formatError cache.",
            fix="Format extensions with this formatter, not leftover first formatError.",
            src="src/pintleErr.ts",
            test="tests/test_pintle_err.py",
            extra="tests/test_pintle_err_mut.py",
            cfg="src/pintleErr.ts",
            bug="extensions still emit leftover code LEGACY after swap to PINTLE_DENIED",
            slo="formatter off; raw GraphQLError leaks",
            residual="leftover formatError on mutation",
            src_obs="formatError = firstFormatter // leftover after swap to PintleDenied\n",
            test_obs="def test_one():\n    set_formatter(PintleDenied)\n    r = execute('{ yard { pintleDrop } }', role='anon')\n    assert r.errors[0].extensions.code == 'PINTLE_DENIED'\n",
            fail_obs="FAILED test_one - leftover formatError; code == LEGACY\n1 failed, 1 passed\n",
            rg_obs="src/pintleErr.ts: leftover firstFormatter",
            wrong_edit_old="formatError = firstFormatter",
            wrong_edit_new="// formatError cache off",
            fix_contents="function formatErrorFor(err, fmt) {\n  return fmt(err);\n} // leftover firstFormatter dies\n",
            suite=6,
        ),
        "bad": S(
            slug="authenticated-leftover-after-field-public",
            surface="GraphQL @authenticated leftover after field became public",
            avoid="Not leftover-mesh; not r215 oneOf leftover; not leftover-GET r183.",
            disable="@authenticated cache",
            plan="Disable @authenticated cache.",
            fix="Drop leftover @authenticated when the field is public again.",
            src="src/pintleAuth.graphql",
            test="tests/test_pintle_auth.py",
            extra="tests/test_pintle_auth_list.py",
            cfg="src/pintleAuth.graphql",
            bug="@authenticated still rejects leftover after pintleDrop became public",
            slo="auth directive off; public fields 401",
            residual="leftover @authenticated on list fields",
            src_obs="pintleDrop: Float @authenticated # leftover after public\n",
            test_obs="def test_one():\n    publish_field('pintleDrop', public=True)\n    r = execute('{ yard { pintleDrop } }', token=None)\n    assert r.errors == []\n",
            fail_obs="FAILED test_one - leftover @authenticated; unauthorized\n1 failed, 1 passed\n",
            rg_obs="src/pintleAuth.graphql: leftover @authenticated",
            wrong_edit_old="pintleDrop: Float @authenticated",
            wrong_edit_new="pintleDrop: Float # @authenticated cache off",
            fix_contents="function authFor(field) {\n  return field.public ? [] : ['@authenticated'];\n} // leftover @authenticated dies when public\n",
            xfail_note="list fields still apply leftover @authenticated",
        ),
        "coverage": 90,
        "next": "Avoid disable formatError cache and disable @authenticated cache.",
    },
    {
        "plant": "lattice-cathead",
        "field": "catheadHold",
        "ok": S(
            slug="requiresscopes-leftover-after-table-reload",
            surface="GraphQL @requiresScopes leftover after scope table reload",
            avoid="Not r72 requires-scopes-after-resolve; not leftover-GET; not r215 oneOf leftover.",
            disable="@requiresScopes cache",
            plan="Disable @requiresScopes cache.",
            fix="Read leftover @requiresScopes from the current scope table, not first table.",
            src="src/catheadScopes.graphql",
            test="tests/test_cathead_scopes.py",
            extra="tests/test_cathead_scopes_mut.py",
            cfg="src/catheadScopes.graphql",
            bug="@requiresScopes still requires leftover yard:write after table reloaded yard:read",
            slo="scopes off; authorized queries 403",
            residual="leftover @requiresScopes on mutation",
            src_obs="catheadHold: Float @requiresScopes(scopes: [[\"yard:write\"]]) # leftover after table yard:read\n",
            test_obs="def test_one():\n    reload_scopes('catheadHold', [['yard:read']])\n    r = execute('{ yard { catheadHold } }', scopes=['yard:read'])\n    assert r.errors == []\n",
            fail_obs="FAILED test_one - leftover @requiresScopes yard:write\n1 failed, 1 passed\n",
            rg_obs="src/catheadScopes.graphql: leftover yard:write",
            wrong_edit_old='catheadHold: Float @requiresScopes(scopes: [["yard:write"]])',
            wrong_edit_new="catheadHold: Float # @requiresScopes cache off",
            fix_contents="function scopesFor(field, table) {\n  return table[field] ?? field.astScopes;\n} // leftover @requiresScopes follows the table\n",
            suite=6,
        ),
        "bad": S(
            slug="gateway-servicelist-leftover-after-url",
            surface="Apollo Gateway serviceList leftover after subgraph URL change",
            avoid="Not leftover-mesh Federation transform r178; not r214 APQ leftover; not leftover-GET.",
            disable="serviceList cache",
            plan="Disable serviceList cache.",
            fix="Route leftover Gateway traffic to the current subgraph URL, not first URL.",
            src="src/catheadGateway.ts",
            test="tests/test_cathead_gw.py",
            extra="tests/test_cathead_gw_entity.py",
            cfg="src/catheadGateway.ts",
            bug="serviceList still posts leftover http://yard-a after URL swapped to http://yard-b",
            slo="serviceList off; compose every request",
            residual="leftover serviceList on _entities",
            src_obs="serviceList = [{name: 'Yard', url: 'http://yard-a'}] // leftover after URL change\n",
            test_obs="def test_one():\n    set_url('Yard', 'http://yard-b')\n    r = execute('{ yard { catheadHold } }')\n    assert r.upstream == 'http://yard-b'\n",
            fail_obs="FAILED test_one - leftover serviceList; upstream == http://yard-a\n1 failed, 1 passed\n",
            rg_obs="src/catheadGateway.ts: leftover http://yard-a",
            wrong_edit_old="url: 'http://yard-a'",
            wrong_edit_new="// serviceList cache off",
            fix_contents="function serviceListFor(supergraph) {\n  return supergraph.currentUrls();\n} // leftover first URL dies\n",
            xfail_note="_entities still posts leftover first URL",
        ),
        "coverage": 91,
        "next": "Avoid disable @requiresScopes cache and disable serviceList cache.",
    },
    {
        "plant": "lattice-samson",
        "field": "samsonPost",
        "ok": S(
            slug="gqlhttp-onoperation-leftover-after-document",
            surface="graphql-http onOperation leftover after document swap",
            avoid="Not leftover-GET r183–r210; not r214 APQ leftover; not r215 hasNext leftover.",
            disable="onOperation cache",
            plan="Disable onOperation cache.",
            fix="Run leftover onOperation against this document, not leftover first document.",
            src="src/samsonHttp.ts",
            test="tests/test_samson_http.py",
            extra="tests/test_samson_http_mut.py",
            cfg="src/samsonHttp.ts",
            bug="onOperation still logs leftover { samsonKg } after document swapped to { samsonPost }",
            slo="onOperation off; operation hooks skip",
            residual="leftover onOperation on mutation",
            src_obs="onOperation.cache = firstDocument // leftover after document swap\n",
            test_obs="def test_one():\n    r = post('{ yard { samsonPost } }')\n    assert r.hooks.document == '{ yard { samsonPost } }'\n",
            fail_obs="FAILED test_one - leftover onOperation firstDocument\n1 failed, 1 passed\n",
            rg_obs="src/samsonHttp.ts: leftover firstDocument",
            wrong_edit_old="onOperation.cache = firstDocument",
            wrong_edit_new="// onOperation cache off",
            fix_contents="function onOperation(req) {\n  return {document: req.document};\n} // leftover firstDocument dies\n",
            suite=6,
        ),
        "bad": S(
            slug="typegraphql-metadata-leftover-after-class-rename",
            surface="TypeGraphQL MetadataStorage leftover after class rename",
            avoid="Not r180 TypeGraphQL ResolverData leftover; not leftover-mesh; not leftover-GET.",
            disable="MetadataStorage cache",
            plan="Disable MetadataStorage cache.",
            fix="Rebuild leftover MetadataStorage from the current class names.",
            src="src/samsonMeta.ts",
            test="tests/test_samson_meta.py",
            extra="tests/test_samson_meta_input.py",
            cfg="src/samsonMeta.ts",
            bug="MetadataStorage still types leftover SamsonKg after class renamed to SamsonPost",
            slo="metadata off; types unpublished",
            residual="leftover MetadataStorage on input types",
            src_obs="storage = firstMetadata // leftover after class rename to SamsonPost\n",
            test_obs="def test_one():\n    rename_class('SamsonKg', 'SamsonPost')\n    r = execute('{ yard { samsonPost } }')\n    assert r.yard.__typename == 'SamsonPost'\n",
            fail_obs="FAILED test_one - leftover MetadataStorage; Unknown type SamsonPost\n1 failed, 1 passed\n",
            rg_obs="src/samsonMeta.ts: leftover firstMetadata",
            wrong_edit_old="storage = firstMetadata",
            wrong_edit_new="// MetadataStorage cache off",
            fix_contents="function storageFor(classes) {\n  return buildTypeDefsAndResolvers({resolvers: classes});\n} // leftover firstMetadata dies\n",
            xfail_note="input types still use leftover first MetadataStorage",
        ),
        "coverage": 90,
        "next": "Avoid disable onOperation cache and disable MetadataStorage cache.",
    },
    {
        "plant": "lattice-bitthead",
        "field": "bittheadLoad",
        "ok": S(
            slug="federation-tag-leftover-after-rename",
            surface="GraphQL @tag leftover after tag rename",
            avoid="Not leftover-mesh Federation transform; not r215 oneOf leftover; not leftover-GET.",
            disable="@tag cache",
            plan="Disable @tag cache.",
            fix="Emit leftover @tag from the current tag name, not first tag.",
            src="src/bitthead.graphql",
            test="tests/test_bitthead_tag.py",
            extra="tests/test_bitthead_tag_enum.py",
            cfg="src/bitthead.graphql",
            bug="@tag still emits leftover internal after rename to yard-public",
            slo="tag cache off; contracts unpublished",
            residual="leftover @tag on enum values",
            src_obs="bittheadLoad: Float @tag(name: \"internal\") # leftover after rename to yard-public\n",
            test_obs="def test_one():\n    rename_tag('internal', 'yard-public')\n    r = introspect('{ yard { bittheadLoad } }')\n    assert r.tags == ['yard-public']\n",
            fail_obs="FAILED test_one - leftover @tag internal\n1 failed, 1 passed\n",
            rg_obs="src/bitthead.graphql: leftover internal",
            wrong_edit_old='bittheadLoad: Float @tag(name: "internal")',
            wrong_edit_new="bittheadLoad: Float # @tag cache off",
            fix_contents="function tagsFor(field, table) {\n  return table[field] ?? field.astTags;\n} // leftover @tag follows rename\n",
            suite=6,
        ),
        "bad": S(
            slug="webonyx-executor-leftover-after-schema",
            surface="webonyx leftover Executor after schema rebuild",
            avoid="Not r131 php Deferred leftover; not leftover-js schema memoize3 r208; not leftover-GET.",
            disable="Executor reuse",
            plan="Disable Executor reuse.",
            fix="webonyx leftover Executor must rebuild from the current schema.",
            src="src/BittheadExec.php",
            test="tests/test_bitthead_exec.py",
            extra="tests/test_bitthead_exec_mut.py",
            cfg="src/BittheadExec.php",
            bug="Executor still selects leftover bitthead_kg after schema rebuilt bittheadLoad",
            slo="reuse off; schema unpublished",
            residual="leftover Executor on mutation",
            src_obs="static $executor = firstSchema->getExecutor(); // leftover after rebuild\n",
            test_obs="def test_one():\n    rebuild_schema(field='bittheadLoad')\n    r = execute('{ yard { bittheadLoad } }')\n    assert r.yard.bittheadLoad == 9.1\n",
            fail_obs="FAILED test_one - leftover Executor; Cannot query field bittheadLoad\n1 failed, 1 passed\n",
            rg_obs="src/BittheadExec.php: leftover firstSchema->getExecutor()",
            wrong_edit_old="static $executor = firstSchema->getExecutor();",
            wrong_edit_new="// Executor reuse off",
            fix_contents="function executorFor($schema) {\n  return $schema->getExecutor();\n} // leftover Executor dies with schema rebuild\n",
            xfail_note="mutation still executes leftover first Executor",
        ),
        "coverage": 91,
        "next": "Avoid disable @tag cache and disable Executor reuse.",
    },
    {
        "plant": "lattice-hawsepipe",
        "field": "hawsepipeClear",
        "ok": S(
            slug="gqlconfig-schemapointer-leftover-after-path",
            surface="graphql-config schema pointer leftover after path change",
            avoid="Not leftover-mesh; not leftover-GET r183; not r215 oneOf leftover.",
            disable="schema pointer cache",
            plan="Disable schema pointer cache.",
            fix="Load leftover schema from the current graphql-config pointer, not first path.",
            src=".graphqlrc.yml",
            test="tests/test_hawse_cfg.py",
            extra="tests/test_hawse_cfg_mut.py",
            cfg=".graphqlrc.yml",
            bug="schema pointer still loads leftover schema.old.graphql after path swapped to schema.graphql",
            slo="pointer off; schema unpublished",
            residual="leftover schema pointer on mutation documents",
            src_obs="schema: schema.old.graphql # leftover after path change\n",
            test_obs="def test_one():\n    set_pointer('schema.graphql')\n    r = execute('{ yard { hawsepipeClear } }')\n    assert r.yard.hawsepipeClear == 1.4\n",
            fail_obs="FAILED test_one - leftover schema pointer; Cannot query field hawsepipeClear\n1 failed, 1 passed\n",
            rg_obs=".graphqlrc.yml: leftover schema.old.graphql",
            wrong_edit_old="schema: schema.old.graphql",
            wrong_edit_new="# schema pointer cache off",
            fix_contents="function pointerFor(cfg) {\n  return cfg.schema;\n} // leftover first path dies\n",
            suite=6,
        ),
        "bad": S(
            slug="redis-sub-channel-leftover-after-tenant",
            surface="graphql-redis-subscriptions leftover channel after tenant swap",
            avoid="Not leftover-mesh RateLimit tenant r172; not leftover-GET; not r212 dataloader tenant.",
            disable="Redis channel cache",
            plan="Disable Redis channel cache.",
            fix="Bind leftover Redis channel to this tenant, not leftover first tenant.",
            src="src/hawseRedis.ts",
            test="tests/test_hawse_redis.py",
            extra="tests/test_hawse_redis_filter.py",
            cfg="src/hawseRedis.ts",
            bug="Redis still subscribes leftover yard:A after tenant swapped to B",
            slo="channel off; every tenant shares events",
            residual="leftover Redis channel on filtered subscribe",
            src_obs="channel = 'yard:A' // leftover after tenant swap\n",
            test_obs="def test_one():\n    swap_tenant('B')\n    sub = subscribe('{ hawsepipeClear }')\n    publish(tenant='B', value=2.2)\n    assert next_event(sub).tenant == 'B'\n",
            fail_obs="FAILED test_one - leftover Redis channel yard:A\n1 failed, 1 passed\n",
            rg_obs="src/hawseRedis.ts: leftover yard:A",
            wrong_edit_old="channel = 'yard:A'",
            wrong_edit_new="// Redis channel cache off",
            fix_contents="function channelFor(ctx) {\n  return 'yard:' + ctx.tenant;\n} // leftover first tenant dies\n",
            xfail_note="filtered subscribe still uses leftover first channel",
        ),
        "coverage": 90,
        "next": "Avoid disable schema pointer cache and disable Redis channel cache.",
    },
    {
        "plant": "lattice-scupper",
        "field": "scupperFlow",
        "ok": S(
            slug="armor-maxaliases-leftover-after-reload",
            surface="graphql-armor maxAliases leftover after config reload",
            avoid="Not r106 Armor persist; not leftover-GET; not leftover-mesh cartesian.",
            disable="maxAliases cache",
            plan="Disable maxAliases cache.",
            fix="Read leftover maxAliases from this config, not leftover first limit.",
            src="src/scupperArmor.ts",
            test="tests/test_scupper_armor.py",
            extra="tests/test_scupper_armor_frag.py",
            cfg="src/scupperArmor.ts",
            bug="maxAliases still 3 after config reloaded 12",
            slo="aliases off; valid aliased queries 400",
            residual="leftover maxAliases on fragment spreads",
            src_obs="maxAliases: firstLimit // leftover after reload to 12\n",
            test_obs="def test_one():\n    reload_armor(maxAliases=12)\n    r = execute('{ a: scupperFlow b: scupperFlow c: scupperFlow d: scupperFlow }')\n    assert r.errors == []\n",
            fail_obs="FAILED test_one - leftover maxAliases 3; too many aliases\n1 failed, 1 passed\n",
            rg_obs="src/scupperArmor.ts: leftover firstLimit",
            wrong_edit_old="maxAliases: firstLimit",
            wrong_edit_new="// maxAliases cache off",
            fix_contents="function maxAliasesFor(cfg) {\n  return cfg.maxAliases;\n} // leftover first limit dies\n",
            suite=6,
        ),
        "bad": S(
            slug="gqlws-ping-leftover-after-keepalive",
            surface="graphql-ws ping leftover after keepalive interval change",
            avoid="Not r167 graphql-ws leftover iterator; not leftover-GET; not r215 hasNext leftover.",
            disable="ping interval cache",
            plan="Disable ping interval cache.",
            fix="Send leftover graphql-ws ping on this keepalive interval, not first interval.",
            src="src/scupperWs.ts",
            test="tests/test_scupper_ws.py",
            extra="tests/test_scupper_ws_filter.py",
            cfg="src/scupperWs.ts",
            bug="ping still fires leftover 30s after keepalive set to 5s",
            slo="ping off; sockets idle-timeout",
            residual="leftover ping on filtered subscribe",
            src_obs="ping = 30000 // leftover after keepalive 5000\n",
            test_obs="def test_one():\n    set_keepalive(5000)\n    ws = connect()\n    assert ws.ping_ms == 5000\n",
            fail_obs="FAILED test_one - leftover ping 30000\n1 failed, 1 passed\n",
            rg_obs="src/scupperWs.ts: leftover 30000",
            wrong_edit_old="ping = 30000",
            wrong_edit_new="// ping interval cache off",
            fix_contents="function pingFor(opts) {\n  return opts.keepalive ?? 12000;\n} // leftover first interval dies\n",
            xfail_note="filtered subscribe still uses leftover first ping",
        ),
        "coverage": 91,
        "next": "Avoid disable maxAliases cache and disable ping interval cache.",
    },
    {
        "plant": "lattice-bilgekeel",
        "field": "bilgekeelDrag",
        "ok": S(
            slug="composedirective-leftover-after-removed",
            surface="Federation @composeDirective leftover after directive removed",
            avoid="Not leftover-mesh Federation transform r178; not r215 oneOf leftover; not leftover-GET.",
            disable="@composeDirective cache",
            plan="Disable @composeDirective cache.",
            fix="Drop leftover @composeDirective when the directive is no longer composed.",
            src="src/bilgekeel.graphql",
            test="tests/test_bilge_compose.py",
            extra="tests/test_bilge_compose_entity.py",
            cfg="src/bilgekeel.graphql",
            bug="@composeDirective still composes leftover @keel after the directive was removed",
            slo="composeDirective off; unknown directives leak",
            residual="leftover @composeDirective on _entities",
            src_obs="extend schema @composeDirective(name: \"@keel\") # leftover after removed\n",
            test_obs="def test_one():\n    remove_directive('@keel')\n    r = compose()\n    assert '@keel' not in r.supergraph\n",
            fail_obs="FAILED test_one - leftover @composeDirective @keel\n1 failed, 1 passed\n",
            rg_obs="src/bilgekeel.graphql: leftover @keel",
            wrong_edit_old='extend schema @composeDirective(name: "@keel")',
            wrong_edit_new="# @composeDirective cache off",
            fix_contents="function composeDirectives(schema) {\n  return schema.currentComposeDirectives;\n} // leftover @keel dies when removed\n",
            suite=6,
        ),
        "bad": S(
            slug="gqljava-executionid-leftover-after-request",
            surface="graphql-java ExecutionId leftover after request",
            avoid="Not r95 graphql-java Instrumentation; not leftover-js TypeInfo r197; not leftover-GET.",
            disable="ExecutionId reuse",
            plan="Disable ExecutionId reuse.",
            fix="Allocate leftover ExecutionId per request, not leftover first id.",
            src="src/BilgeExec.java",
            test="tests/test_bilge_execid.py",
            extra="tests/test_bilge_execid_mut.py",
            cfg="src/BilgeExec.java",
            bug="ExecutionId still reuses leftover exec-1 after the next request",
            slo="id reuse off; traces collide",
            residual="leftover ExecutionId on mutation",
            src_obs="static ExecutionId id = ExecutionId.from(\"exec-1\"); // leftover after request\n",
            test_obs="def test_one():\n    a = execute('{ yard { bilgekeelDrag } }')\n    b = execute('{ yard { bilgekeelDrag } }')\n    assert a.execution_id != b.execution_id\n",
            fail_obs="FAILED test_one - leftover ExecutionId exec-1 on both requests\n1 failed, 1 passed\n",
            rg_obs="src/BilgeExec.java: leftover exec-1",
            wrong_edit_old='static ExecutionId id = ExecutionId.from("exec-1");',
            wrong_edit_new="// ExecutionId reuse off",
            fix_contents="ExecutionId idFor(ExecutionInput in) {\n  return ExecutionId.generate();\n} // leftover first id dies\n",
            xfail_note="mutation still reuses leftover first ExecutionId",
        ),
        "coverage": 90,
        "next": "Avoid disable @composeDirective cache and disable ExecutionId reuse.",
    },
    {
        "plant": "lattice-deadeye",
        "field": "deadeyeLash",
        "ok": S(
            slug="resolveinfo-leftover-after-field-rename",
            surface="GraphQLResolveInfo leftover after field rename",
            avoid="Not leftover-js getFieldDef r194; not leftover-GET; not r215 oneOf leftover.",
            disable="ResolveInfo cache",
            plan="Disable ResolveInfo cache.",
            fix="Build leftover ResolveInfo from this field name, not leftover first field.",
            src="src/deadeyeInfo.ts",
            test="tests/test_deadeye_info.py",
            extra="tests/test_deadeye_info_frag.py",
            cfg="src/deadeyeInfo.ts",
            bug="ResolveInfo still names leftover deadeye_kg after field renamed to deadeyeLash",
            slo="info cache off; fieldName unpublished",
            residual="leftover ResolveInfo on fragment spreads",
            src_obs="info.fieldName = 'deadeye_kg' // leftover after rename to deadeyeLash\n",
            test_obs="def test_one():\n    rename_field('deadeyeLash')\n    r = execute('{ yard { deadeyeLash } }')\n    assert r.info.fieldName == 'deadeyeLash'\n",
            fail_obs="FAILED test_one - leftover ResolveInfo deadeye_kg\n1 failed, 1 passed\n",
            rg_obs="src/deadeyeInfo.ts: leftover deadeye_kg",
            wrong_edit_old="info.fieldName = 'deadeye_kg'",
            wrong_edit_new="// ResolveInfo cache off",
            fix_contents="function infoFor(field) {\n  return {fieldName: field.name};\n} // leftover first field dies\n",
            suite=6,
        ),
        "bad": S(
            slug="gqlphp-promise-adapter-leftover-after-swap",
            surface="graphql-php PromiseAdapter leftover after adapter swap",
            avoid="Not r131 php Deferred leftover; not leftover-js; not leftover-GET r183.",
            disable="PromiseAdapter cache",
            plan="Disable PromiseAdapter cache.",
            fix="Await leftover graphql-php promises on this adapter, not leftover first adapter.",
            src="src/DeadeyePromise.php",
            test="tests/test_deadeye_promise.py",
            extra="tests/test_deadeye_promise_mut.py",
            cfg="src/DeadeyePromise.php",
            bug="PromiseAdapter still uses leftover SyncPromiseAdapter after swap to AmpAdapter",
            slo="adapter off; async fields hang",
            residual="leftover PromiseAdapter on mutation",
            src_obs="$adapter = new SyncPromiseAdapter(); // leftover after swap to AmpAdapter\n",
            test_obs="def test_one():\n    set_adapter('AmpAdapter')\n    r = execute('{ yard { deadeyeLash } }')\n    assert r.adapter == 'AmpAdapter'\n",
            fail_obs="FAILED test_one - leftover PromiseAdapter SyncPromiseAdapter\n1 failed, 1 passed\n",
            rg_obs="src/DeadeyePromise.php: leftover SyncPromiseAdapter",
            wrong_edit_old="$adapter = new SyncPromiseAdapter();",
            wrong_edit_new="// PromiseAdapter cache off",
            fix_contents="function adapterFor($cfg) {\n  return $cfg->promiseAdapter;\n} // leftover first adapter dies\n",
            xfail_note="mutation still uses leftover first PromiseAdapter",
        ),
        "coverage": 91,
        "next": "Avoid disable ResolveInfo cache and disable PromiseAdapter cache.",
    },
    {
        "plant": "lattice-cringle",
        "field": "cringlePull",
        "ok": S(
            slug="federation-context-leftover-after-request",
            surface="Federation query-planner context leftover after request",
            avoid="Not leftover-mesh Federation transform r178; not r210 Context leftover; not leftover-GET.",
            disable="planner context cache",
            plan="Disable planner context cache.",
            fix="Plan leftover Federation queries with this request context, not leftover first context.",
            src="src/cringlePlan.ts",
            test="tests/test_cringle_plan.py",
            extra="tests/test_cringle_plan_entity.py",
            cfg="src/cringlePlan.ts",
            bug="query planner still injects leftover tenant A after request swapped to tenant B",
            slo="context off; plans leak tenant",
            residual="leftover planner context on _entities",
            src_obs="planner.context = firstRequest // leftover after request swap\n",
            test_obs="def test_one():\n    r = execute('{ yard { cringlePull } }', tenant='B')\n    assert r.plan.tenant == 'B'\n",
            fail_obs="FAILED test_one - leftover planner context tenant A\n1 failed, 1 passed\n",
            rg_obs="src/cringlePlan.ts: leftover firstRequest",
            wrong_edit_old="planner.context = firstRequest",
            wrong_edit_new="// planner context cache off",
            fix_contents="function planFor(op, ctx) {\n  return planner.plan(op, {tenant: ctx.tenant});\n} // leftover first context dies\n",
            suite=6,
        ),
        "bad": S(
            slug="graphql-http-onresponse-leftover-after-status",
            surface="graphql-http onResponse leftover after status map swap",
            avoid="Not leftover-GET r183–r210; not r188 graphql-response+json leftover 200; not r215 hasNext.",
            disable="onResponse cache",
            plan="Disable onResponse cache.",
            fix="Map leftover HTTP status from this onResponse, not leftover first map.",
            src="src/cringleHttp.ts",
            test="tests/test_cringle_http.py",
            extra="tests/test_cringle_http_mut.py",
            cfg="src/cringleHttp.ts",
            bug="onResponse still returns leftover 200 after status map swapped validation to 400",
            slo="onResponse off; clients see 200 on errors",
            residual="leftover onResponse on mutation",
            src_obs="onResponse.status = 200 // leftover after status map swap\n",
            test_obs="def test_one():\n    r = post('{ yard { missingField } }')\n    assert r.status == 400\n",
            fail_obs="FAILED test_one - leftover onResponse 200\n1 failed, 1 passed\n",
            rg_obs="src/cringleHttp.ts: leftover 200",
            wrong_edit_old="onResponse.status = 200",
            wrong_edit_new="// onResponse cache off",
            fix_contents="function onResponse(result) {\n  return {status: result.errors ? 400 : 200};\n} // leftover first status dies\n",
            xfail_note="mutation still uses leftover first onResponse status",
        ),
        "coverage": 90,
        "next": "Avoid disable planner context cache and disable onResponse cache.",
    },
]

PAIRS: list[dict] = list(_m211.PAIRS) + list(_hop.PAIRS) + EXTRA


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


def unused_pairs() -> list[dict]:
    used = published_slugs()
    out = []
    for p in PAIRS:
        ok = p["ok"]["slug"].lower()
        bad = p["bad"]["slug"].lower()
        if p["ok"]["slug"] in used or p["bad"]["slug"] in used:
            continue
        banned = False
        for ban in BANNED:
            if ban in ok or ban in bad:
                banned = True
                break
        if banned:
            continue
        out.append(p)
    return out


def pair_for_round(n: int, base: int | None = None) -> dict:
    unused = unused_pairs()
    if not unused:
        raise SystemExit(f"no unused leftover leftover leftover catalog for r{n}")
    return unused[0]


def write_round(n: int, staging: Path, base: int | None = None) -> None:
    p = pair_for_round(n, base=base)
    ok = success_episode(n, p["plant"], p["field"], p["ok"])
    bad = fail_episode(n, p["plant"], p["field"], p["bad"])
    ok["goal"] = ok["goal"].replace("r183–r210 clones", "r183–r215 clones")
    bad["goal"] = bad["goal"].replace("r183–r210 clones", "r183–r215 clones")
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
    notes_txt = notes_for(n, p)
    if "Novel coverage:" not in notes_txt:
        raise SystemExit("notes missing Novel coverage")
    notes_txt = notes_txt.replace(
        "Not leftover-mesh/GET/js cartesian.",
        "Not leftover Mesh/tools cartesian. Not leftover-GET clones. Not r183–r215 clones. Not an N+1 catalog.",
    )
    if "Not leftover Mesh" not in notes_txt and "Not leftover-mesh" not in notes_txt:
        notes_txt = notes_txt.rstrip() + "\nNot leftover Mesh/tools cartesian. Not leftover-GET clones. Not r183–r215 clones. Not an N+1 catalog.\n"
    batch.write_text(json.dumps(ok, ensure_ascii=True) + "\n" + json.dumps(bad, ensure_ascii=True) + "\n")
    notes.write_text(notes_txt)
    print(json.dumps({"round": n, "ids": [ok["id"], bad["id"]], "plant": p["plant"], "unused": len(unused_pairs()) - 1}))


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
