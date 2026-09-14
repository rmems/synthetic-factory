#!/usr/bin/env python3
"""Eighth unique OpenAPI-drift ACM catalog after r4102 mill. Fast slug load."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acm_mill_r3561", HERE / "acm-mill-r3561.py")
_b = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_b)

plant = _b.plant
GEN = _b.GEN
BANNED_BLOB = _b.BANNED_BLOB
build_episode = _b.build_episode
notes_text = _b.notes_text
FACTORY = _b.FACTORY
SEED_RE = re.compile(r"seed=([a-z0-9-]+)")
SLUG_RE = re.compile(r'slug="([^"]+)"')

BANNED_PRIOR: set[str] = set()
for path in HERE.glob("acm-mill-r*.py"):
    if path.name == Path(__file__).name:
        continue
    BANNED_PRIOR.update(SLUG_RE.findall(path.read_text(errors="ignore")))
BANNED_PRIOR |= {
    "oas-allowemptyvalue-header", "leftover-omit-header-empty",
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def published_slugs() -> set[str]:
    found: set[str] = set()
    if FACTORY.is_dir():
        for path in FACTORY.glob("NOTES-r*.md"):
            try:
                found.update(SEED_RE.findall(path.read_text(errors="ignore")))
            except OSError:
                continue
    return found


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-schema-minimum-inclusive", domain="oas-min-vs-no-min", success=True, name="schmin", stack="OpenAPI 3.1 minimum + Go", field="minimum", old="no minimum leftover", new="inclusive minimum", fail_err="400: leftover no-minimum after minimum-only", plan="minimum-only 400s leftover no-minimum. Dual-omit minimum for one release.", residual="validator still no-min leftover; drop after validator 5", vs="r4070 leftover-inclusive-max (minimum vs no-min leftover, not exclusiveMaximum)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#minimum", fetch1_ok="minimum is inclusive, leftover unbounded numbers fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minimum 400 leftover no-min."),
     p(slug="leftover-no-minimum", domain="no-min-vs-oas-min", success=False, name="nomin", stack="OpenAPI leftover no minimum + Java + TS", field="minimum", old="inclusive minimum", new="no minimum leftover only", fail_err="400: leftover minimum after no-min-only", plan="No-min-only 400s leftover minimum. Freeze minimum, spec no-min leftover.", residual="handoff: keep minimum or force no-min leftover", vs="r4070 oas-schema-exclusive-maximum (no-min leftover, not exclusiveMaximum)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="No leftover minimum is not minimum.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#minimum", fetch2_ok="Exclusive no-min 400 leftover minimum.")),
    (p(slug="oas-schema-multipleof-int", domain="oas-multipleof-vs-any-scale", success=True, name="mulof", stack="OpenAPI 3.1 multipleOf + Go", field="multipleOf", old="any number scale leftover", new="integer multipleOf", fail_err="400: leftover any-scale after multipleOf-only", plan="multipleOf-only 400s leftover any-scale. Dual-read any-scale for one release.", residual="ledger still any-scale leftover; drop after ledger 5", vs="wrap multipleof-cents (multipleOf vs any-scale leftover, not cents cartesian)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#multiples", fetch1_ok="multipleOf constrains scale, leftover any-number fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive multipleOf 400 leftover any-scale."),
     p(slug="leftover-any-number-scale", domain="any-scale-vs-oas-multipleof", success=False, name="anynum", stack="OpenAPI leftover any number scale + Java + TS", field="type", old="integer multipleOf", new="any number scale leftover only", fail_err="400: leftover multipleOf after any-scale-only", plan="Any-scale-only 400s leftover multipleOf. Freeze multipleOf, spec any-scale leftover.", residual="handoff: keep multipleOf or force any-scale leftover", vs="wrap multipleof-cents (any-scale leftover, not cents cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Any-scale leftover is not multipleOf.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#multiples", fetch2_ok="Exclusive any-scale 400 leftover multipleOf.")),
    (p(slug="oas-header-example-map", domain="oas-hdr-examples-vs-single", success=True, name="hdrex", stack="OpenAPI 3.1 header examples + Go", field="examples", old="single header example leftover", new="header examples map", fail_err="400: leftover single header example after examples-only", plan="header.examples-only 400s leftover single. Dual-read single for one release.", residual="docs still single leftover; drop after docs 5", vs="r4054 leftover-dual-example (header examples vs single leftover, not param dual)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="examples on headers is a map, leftover singular example is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch2_ok="Exclusive header examples 400 leftover single."),
     p(slug="leftover-header-single-example", domain="single-hdr-ex-vs-oas-hdr-examples", success=False, name="hdrsex", stack="OpenAPI leftover single header example + Java + TS", field="example", old="header examples map", new="single header example leftover only", fail_err="400: leftover header examples after single-only", plan="Single-only 400s leftover header examples. Freeze examples, spec single leftover.", residual="handoff: keep header examples or force single leftover", vs="r4054 oas-parameter-examples-map (single leftover, not param examples)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#example-object", fetch1_ok="Singular leftover header examples are not examples maps.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive single header example 400 leftover examples.")),
    (p(slug="oas-response-header-www-authenticate", domain="oas-wwwauth-vs-auth-body", success=True, name="wwwauth", stack="OpenAPI 3.1 WWW-Authenticate + Go", field="WWW-Authenticate", old="auth body hint leftover", new="WWW-Authenticate header", fail_err="401: leftover auth body after WWW-Authenticate-only", plan="WWW-Authenticate-only 401s leftover auth body. Dual-emit body for one release.", residual="sdk still body leftover; drop after sdk 6", vs="r4038 leftover-error-string (WWW-Authenticate vs body leftover, not problem+json)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-www-authenticate", fetch1_ok="WWW-Authenticate is a challenge header, leftover auth bodies are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive WWW-Authenticate 401 leftover auth body."),
     p(slug="leftover-auth-body-hint", domain="auth-body-vs-oas-wwwauth", success=False, name="authbd", stack="OpenAPI leftover auth body hint + Java + TS", field="error", old="WWW-Authenticate header", new="auth body hint leftover only", fail_err="401: leftover WWW-Authenticate after body-only", plan="Body-only 401s leftover WWW-Authenticate. Freeze header, spec body leftover.", residual="handoff: keep WWW-Authenticate or force body leftover", vs="r4038 oas-content-application-problem (auth body leftover, not problem mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Auth leftover bodies are not WWW-Authenticate.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-www-authenticate", fetch2_ok="Exclusive auth body 401 leftover WWW-Authenticate.")),
    (p(slug="oas-webhook-servers-override", domain="oas-whk-servers-vs-root", success=True, name="whksrv", stack="OpenAPI 3.1 webhook servers + Go", field="servers", old="root webhook server leftover", new="webhook servers override", fail_err="400: leftover root server after webhook-servers-only", plan="webhook.servers-only 400s leftover root. Dual-read root for one release.", residual="edge still root leftover; drop after edge 5", vs="r4038 leftover-free-host-var (webhook servers vs root leftover, not server pattern)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch1_ok="Webhook Path Items may override servers, leftover root-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive webhook servers 400 leftover root."),
     p(slug="leftover-root-webhook-server", domain="root-whk-vs-oas-whk-servers", success=False, name="rwhks", stack="OpenAPI leftover root webhook server + Java + TS", field="url", old="webhook servers override", new="root webhook server leftover only", fail_err="400: leftover webhook servers after root-only", plan="Root-only 400s leftover webhook servers. Freeze override, spec root leftover.", residual="handoff: keep webhook servers or force root leftover", vs="r4038 oas-servers-variables-pattern (root leftover, not pattern mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Root leftover webhook servers are not Path Item servers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasWebhooks", fetch2_ok="Exclusive root webhook server 400 leftover override.")),
    (p(slug="oas-servers-variables-enum-only", domain="oas-enum-var-vs-pattern-only", success=True, name="svenu", stack="OpenAPI 3.1 server var enum-only + Go", field="enum", old="pattern only var leftover", new="server variable enum", fail_err="400: leftover pattern-only after enum-only", plan="enum-only 400s leftover pattern-only. Dual-read pattern for one release.", residual="mesh still pattern leftover; drop after mesh 5", vs="r4038 leftover-free-host-var (enum-only vs pattern leftover, not free-host mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch1_ok="enum-only server vars are not leftover pattern-only vars.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive enum-only var 400 leftover pattern."),
     p(slug="leftover-pattern-only-var", domain="pattern-only-vs-oas-enum-var", success=False, name="svpat", stack="OpenAPI leftover pattern-only var + Java + TS", field="pattern", old="server variable enum", new="pattern only var leftover only", fail_err="400: leftover enum-only after pattern-only", plan="Pattern-only 400s leftover enum. Freeze enum, spec pattern leftover.", residual="handoff: keep enum-only var or force pattern leftover", vs="r4038 oas-servers-variables-pattern (pattern leftover, not required pattern mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Pattern-only leftover vars are not enum.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-variable-object", fetch2_ok="Exclusive pattern-only 400 leftover enum.")),
    (p(slug="oas-discriminator-mapping-default", domain="oas-disc-default-vs-unmapped", success=True, name="dmapd", stack="OpenAPI 3.1 discriminator mapping default + Go", field="mapping", old="unmapped disc leftover", new="discriminator mapping default", fail_err="400: leftover unmapped after mapping-default-only", plan="mapping-default-only 400s leftover unmapped. Dual-read unmapped for one release.", residual="sdk still unmapped leftover; drop after sdk 5", vs="r4038 leftover-optional-disc (mapping default vs unmapped leftover, not required disc)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch1_ok="mapping default covers undeclared values, leftover unmapped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive mapping default 400 leftover unmapped."),
     p(slug="leftover-unmapped-disc", domain="unmapped-vs-oas-disc-default", success=False, name="unmapd", stack="OpenAPI leftover unmapped disc + Java + TS", field="mapping", old="discriminator mapping default", new="unmapped disc leftover only", fail_err="400: leftover mapping default after unmapped-only", plan="Unmapped-only 400s leftover mapping default. Freeze mapping, spec unmapped leftover.", residual="handoff: keep mapping default or force unmapped leftover", vs="r4038 oas-discriminator-property-required (unmapped leftover, not required disc)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unmapped leftover discriminators are not mapping default.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#discriminator-object", fetch2_ok="Exclusive unmapped 400 leftover mapping default.")),
    (p(slug="oas-xml-array-wrapper-name", domain="oas-xml-wrapper-vs-bare", success=True, name="xmlwr", stack="OpenAPI 3.1 xml array wrapper name + Go", field="name", old="bare xml array leftover", new="xml array wrapper name", fail_err="415: leftover bare xml array after wrapper-only", plan="xml-wrapper-name-only 415s leftover bare. Dual-read bare for one release.", residual="batch still bare leftover; drop after batch 5", vs="r3993 leftover-always-wrap (wrapper name vs bare leftover, not wrapped false mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.name on arrays names the wrapper, leftover bare arrays are not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive xml wrapper name 415 leftover bare."),
     p(slug="leftover-bare-xml-array", domain="bare-xml-vs-oas-wrapper", success=False, name="xmlbare", stack="OpenAPI leftover bare xml array + Java + TS", field="wrapped", old="xml array wrapper name", new="bare xml array leftover only", fail_err="415: leftover xml wrapper after bare-only", plan="Bare-only 415s leftover xml wrapper. Freeze wrapper, spec bare leftover.", residual="handoff: keep xml wrapper name or force bare leftover", vs="r3993 oas-xml-wrapped-false (bare leftover, not wrapped false)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Bare leftover XML arrays are not named wrappers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive bare xml array 415 leftover wrapper.")),
    (p(slug="oas-content-application-scim", domain="oas-scim-vs-plain-patch", success=True, name="scim", stack="OpenAPI 3.1 application/scim+json + Go", field="content", old="plain patch leftover", new="application scim json", fail_err="415: leftover plain patch after scim-only", plan="scim+json-only 415s leftover plain patch. Dual-read plain for one release.", residual="idp still plain leftover; drop after idp 6", vs="r3561 scim-patch-op-path (scim+json vs plain leftover, not scim path mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc7644", fetch1_ok="application/scim+json is not leftover generic patches.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive scim+json 415 leftover plain patch."),
     p(slug="leftover-plain-patch", domain="plain-patch-vs-oas-scim", success=False, name="plpatch", stack="OpenAPI leftover plain patch + Java + TS", field="content", old="application scim json", new="plain patch leftover only", fail_err="415: leftover scim+json after plain-only", plan="Plain-only 415s leftover scim+json. Freeze scim, spec plain leftover.", residual="handoff: keep scim+json or force plain leftover", vs="r3561 scim-patch-op-path (plain leftover, not scim path)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Plain leftover patches are not scim+json.", fetch2="https://datatracker.ietf.org/doc/html/rfc7644", fetch2_ok="Exclusive plain patch 415 leftover scim.")),
    (p(slug="oas-link-server-override", domain="oas-link-server-vs-root", success=True, name="lnksrv", stack="OpenAPI 3.1 link server + Go", field="server", old="root link server leftover", new="link server override", fail_err="400: leftover root link server after override-only", plan="link.server-only 400s leftover root. Dual-read root for one release.", residual="sdk still root leftover; drop after sdk 5", vs="r4038 leftover-query-link (link server vs root leftover, not requestBody mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="link.server overrides the target host, leftover root-only is not that.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive link server 400 leftover root."),
     p(slug="leftover-root-link-server", domain="root-link-vs-oas-link-server", success=False, name="rlnks", stack="OpenAPI leftover root link server + Java + TS", field="url", old="link server override", new="root link server leftover only", fail_err="400: leftover link.server after root-only", plan="Root-only 400s leftover link.server. Freeze override, spec root leftover.", residual="handoff: keep link.server or force root leftover", vs="r4038 oas-link-request-body (root leftover, not requestBody mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Root leftover link servers are not link.server.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive root link server 400 leftover override.")),
    (p(slug="oas-readonly-omit-on-write", domain="oas-readonly-vs-echo-write", success=True, name="roomit", stack="OpenAPI 3.1 readOnly omit on write + Go", field="readOnly", old="echo readonly leftover", new="readOnly omit write", fail_err="400: leftover echo-readonly after omit-write-only", plan="readOnly-omit-write-only 400s leftover echo. Dual-echo for one release.", residual="sdk still echo leftover; drop after sdk 5", vs="r3561 readonly-on-create (omit write vs echo leftover, not create mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#readonly", fetch1_ok="readOnly fields must not be written, leftover echo-on-write fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive readOnly omit 400 leftover echo."),
     p(slug="leftover-echo-readonly", domain="echo-ro-vs-oas-readonly-omit", success=False, name="roecho", stack="OpenAPI leftover echo readonly + Java + TS", field="readOnly", old="readOnly omit write", new="echo readonly leftover only", fail_err="400: leftover readOnly omit after echo-only", plan="Echo-only 400s leftover readOnly omit. Freeze omit, spec echo leftover.", residual="handoff: keep readOnly omit or force echo leftover", vs="r3561 readonly-on-create (echo leftover, not create mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Echo leftover readOnly is not omit-on-write.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#readonly", fetch2_ok="Exclusive echo readonly 400 leftover omit.")),
    (p(slug="oas-writeonly-omit-on-read", domain="oas-writeonly-vs-echo-read", success=True, name="woomit", stack="OpenAPI 3.1 writeOnly omit on read + Go", field="writeOnly", old="echo writeonly leftover", new="writeOnly omit read", fail_err="400: leftover echo-writeonly after omit-read-only", plan="writeOnly-omit-read-only 400s leftover echo. Dual-echo for one release.", residual="sdk still echo leftover; drop after sdk 5", vs="r3561 writeonly-create-echo (omit read vs echo leftover, not create mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#writeonly", fetch1_ok="writeOnly fields must not be read, leftover echo-on-read fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive writeOnly omit 400 leftover echo."),
     p(slug="leftover-echo-writeonly", domain="echo-wo-vs-oas-writeonly-omit", success=False, name="woecho", stack="OpenAPI leftover echo writeonly + Java + TS", field="writeOnly", old="writeOnly omit read", new="echo writeonly leftover only", fail_err="400: leftover writeOnly omit after echo-only", plan="Echo-only 400s leftover writeOnly omit. Freeze omit, spec echo leftover.", residual="handoff: keep writeOnly omit or force echo leftover", vs="r3561 writeonly-create-echo (echo leftover, not create mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Echo leftover writeOnly is not omit-on-read.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#writeonly", fetch2_ok="Exclusive echo writeonly 400 leftover omit.")),
    (p(slug="oas-deprecated-op-gone", domain="oas-dep-gone-vs-live-dep", success=True, name="opgone", stack="OpenAPI 3.1 deprecated op removed + Go", field="deprecated", old="live deprecated op leftover", new="deprecated op gone", fail_err="410: leftover live deprecated after gone-only", plan="gone-only 410s leftover live deprecated. Dual-keep live for one release.", residual="edge still live leftover; drop after edge 6", vs="r3931 leftover-live-op (gone vs live leftover, not deprecated mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Removing a deprecated operation is not leftover still-routed ops.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive gone op 410 leftover live deprecated."),
     p(slug="leftover-live-deprecated-op", domain="live-dep-vs-oas-dep-gone", success=False, name="livedep", stack="OpenAPI leftover live deprecated op + Java + TS", field="deprecated", old="deprecated op gone", new="live deprecated op leftover only", fail_err="410: leftover gone op after live-only", plan="Live-only 410s leftover gone op. Freeze gone, spec live leftover.", residual="handoff: keep gone op or force live leftover", vs="r3931 oas-operation-deprecated (live leftover, not deprecated mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Live leftover deprecated ops are not gone.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive live deprecated 410 leftover gone.")),
    (p(slug="oas-json-schema-id", domain="oas-schema-id-vs-missing", success=True, name="schid", stack="OpenAPI 3.1 $id + Go", field="$id", old="missing schema id leftover", new="schema dollarid", fail_err="400: leftover missing $id after $id-only", plan="$id-only 400s leftover missing. Dual-omit $id for one release.", residual="codegen still missing leftover; drop after codegen 5", vs="r3993 leftover-missing-schema-id ($id vs missing leftover, not $id mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/structuring#id", fetch1_ok="$id identifies the schema, leftover missing ids fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $id 400 leftover missing."),
     p(slug="leftover-no-schema-dollar-id", domain="missing-id-vs-oas-schema-id", success=False, name="noid", stack="OpenAPI leftover missing $id + Java + TS", field="$id", old="schema dollarid", new="missing schema id leftover only", fail_err="400: leftover $id after missing-only", plan="Missing-only 400s leftover $id. Freeze $id, spec missing leftover.", residual="handoff: keep $id or force missing leftover", vs="r3993 oas-schema-id (missing leftover, not $id mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Missing leftover $id is not $id.", fetch2="https://json-schema.org/understanding-json-schema/structuring#id", fetch2_ok="Exclusive missing $id 400 leftover $id.")),
    (p(slug="oas-format-idn-hostname-strict", domain="oas-idn-host-vs-ascii-only", success=True, name="idnhost", stack="OpenAPI 3.1 idn-hostname strict + Go", field="format", old="ascii host only leftover", new="idn-hostname strict", fail_err="400: leftover ascii-only after idn-hostname-only", plan="idn-hostname-only 400s leftover ascii-only. Dual-read ascii for one release.", residual="dns still ascii leftover; drop after dns 6", vs="r4007 leftover-raw-idn-host (strict idn-hostname vs ascii leftover, not puny mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch1_ok="format=idn-hostname is not leftover ASCII-only hosts.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-hostname 400 leftover ascii."),
     p(slug="leftover-ascii-host-only", domain="ascii-host-vs-oas-idn-host", success=False, name="asciih", stack="OpenAPI leftover ascii host only + Java + TS", field="format", old="idn-hostname strict", new="ascii host only leftover only", fail_err="400: leftover idn-hostname after ascii-only", plan="Ascii-only 400s leftover idn-hostname. Freeze idn-hostname, spec ascii leftover.", residual="handoff: keep idn-hostname or force ascii leftover", vs="r4007 oas-format-hostname-puny (ascii leftover, not puny mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="ASCII leftover hosts are not format=idn-hostname.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#idn-hostname", fetch2_ok="Exclusive ascii-only 400 leftover idn-hostname.")),
    (p(slug="oas-info-contact-both", domain="oas-contact-both-vs-name-only", success=True, name="ctboth", stack="OpenAPI 3.1 contact name+url + Go", field="contact", old="name only contact leftover", new="contact name and url", fail_err="400: leftover name-only after both-only", plan="contact-both-only 400s leftover name-only. Dual-omit url for one release.", residual="portal still name-only leftover; drop after portal 5", vs="r3978 leftover-missing-contact-url (name+url vs name-only leftover, not missing url mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch1_ok="contact.name plus url is not leftover name-only contact.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive contact both 400 leftover name-only."),
     p(slug="leftover-name-only-contact", domain="name-only-vs-oas-contact-both", success=False, name="ctnameo", stack="OpenAPI leftover name-only contact + Java + TS", field="name", old="contact name and url", new="name only contact leftover only", fail_err="400: leftover contact url after name-only", plan="Name-only 400s leftover contact url. Freeze both, spec name leftover.", residual="handoff: keep contact both or force name leftover", vs="r3978 oas-info-contact-name (name-only leftover, not contact name mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="Name-only leftover contact is not name+url.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#contact-object", fetch2_ok="Exclusive name-only 400 leftover both.")),
]


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")
    for a, b in PAIRS:
        if not a["success"] or b["success"]:
            raise SystemExit(f"pair must be success+fail: {a['slug']} / {b['slug']}")
        for spec in (a, b):
            slug = spec["slug"]
            if slug in seen or slug in BANNED_PRIOR:
                raise SystemExit(f"duplicate or prior slug {slug}")
            seen.add(slug)
            if "w131" in slug or "422-vs-400" in slug or "207-multistatus" in slug:
                raise SystemExit(f"banned {slug}")
            if "smile" in slug or "cbor" in slug:
                raise SystemExit(f"banned smile/cbor {slug}")
            if "lll4" in slug or "accept-language" in slug or "iso639" in slug:
                raise SystemExit(f"banned prior plant {slug}")
            if "allowemptyvalue-header" in slug or "omit-header-empty" in slug:
                raise SystemExit(f"banned r4006 plant {slug}")


def next_free_idx(start: int = 0) -> int | None:
    existing = published_slugs()
    for i in range(start, len(PAIRS)):
        a, b = PAIRS[i]
        if a["slug"] not in existing and b["slug"] not in existing:
            return i
    return None


def unused_pairs():
    existing = published_slugs()
    return [p for p in PAIRS if p[0]["slug"] not in existing and p[1]["slug"] not in existing]


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    catalog_selfcheck()
    if idx is None:
        idx = next_free_idx()
        if idx is None:
            raise SystemExit("catalog exhausted")
    t1, t2 = PAIRS[idx]
    existing = published_slugs()
    for spec in (t1, t2):
        if spec["slug"] in existing:
            raise SystemExit(f"slug {spec['slug']} already published")
    e1 = build_episode(round_n, t1)
    e2 = build_episode(round_n, t2)
    for e in (e1, e2):
        blob = json.dumps(e)
        for banned in BANNED_BLOB:
            if f'"{banned}"' in blob:
                raise SystemExit(f"banned key {banned}")
        assert e["meta"]["generator"] == GEN
        assert len(e["steps"]) == 16
        assert "[variant" not in e["goal"] and "-w131" not in e["id"]
        assert e["id"].startswith(f"acm-r{round_n:04d}-")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(e1, ensure_ascii=False) + "\n" + json.dumps(e2, ensure_ascii=False) + "\n")
    notes.write_text(notes_text(round_n, [e1, e2], [t1, t2], idx))
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4118"}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, default=None)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
