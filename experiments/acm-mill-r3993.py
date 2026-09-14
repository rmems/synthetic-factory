#!/usr/bin/env python3
"""Ninth unique OpenAPI-drift ACM catalog after r3978 mill."""
from __future__ import annotations

import argparse
import importlib.util
import json
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
published_slugs = _b.published_slugs

priors = [
    "acm-mill-r3620.py", "acm-mill-r3667.py", "acm-mill-r3698.py",
    "acm-mill-r3714.py", "acm-mill-r3787.py", "acm-mill-r3851.py",
    "acm-mill-r3867.py", "acm-mill-r3883.py", "acm-mill-r3899.py",
    "acm-mill-r3915.py", "acm-mill-r3931.py", "acm-mill-r3947.py",
    "acm-mill-r3963.py", "acm-mill-r3978.py",
]
BANNED_PRIOR = {p[0]["slug"] for p in _b.PAIRS} | {p[1]["slug"] for p in _b.PAIRS}
for fname in priors:
    sp = importlib.util.spec_from_file_location(fname.replace("-", "_"), HERE / fname)
    mod = importlib.util.module_from_spec(sp)
    assert sp.loader is not None
    sp.loader.exec_module(mod)
    BANNED_PRIOR |= {p[0]["slug"] for p in mod.PAIRS} | {p[1]["slug"] for p in mod.PAIRS}

BANNED_PRIOR |= {
    "oas-lll4-proto-optional", "protobuf-lll4-optional-oas",
    "accept-language-bcp47", "iso639-language",
    "smile-binary-json", "cbor-majortype-vs-smile",
    "422-vs-400-validation", "207-multistatus-batch",
}


def p(**kw):
    return plant(**kw)


PAIRS: list[tuple[dict, dict]] = [
    (p(slug="oas-info-title-required", domain="oas-title-vs-missing-title", success=True, name="title", stack="OpenAPI 3.1 info.title + Go", field="title", old="missing title leftover", new="info title", fail_err="400: leftover missing title after title-only", plan="info.title-only 400s leftover missing title. Dual-omit title for one release.", residual="portal still missing leftover; drop after portal 4", vs="r3978 oas-info-contact-url (title vs missing leftover, not contact url)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info.title is required, leftover missing titles fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive info.title 400 leftover missing."),
     p(slug="leftover-missing-title", domain="missing-title-vs-oas-title", success=False, name="notitle", stack="OpenAPI leftover missing title + Java + TS", field="info", old="info title", new="missing title leftover only", fail_err="400: leftover title after missing-only", plan="Missing-only 400s leftover info.title. Freeze title, spec missing leftover.", residual="handoff: keep info.title or force missing leftover", vs="r3978 leftover-missing-contact-url (missing title leftover, not contact url)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Missing titles are not info.title.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="Exclusive missing title 400 leftover title.")),
    (p(slug="oas-root-version-31", domain="oas31-root-vs-oas30-root", success=True, name="oas31", stack="OpenAPI 3.1 root version + Go", field="openapi", old="oas30 root leftover", new="openapi 3.1.0", fail_err="400: leftover oas 3.0 root after 3.1-only", plan="3.1-root-only 400s leftover 3.0 root. Dual-accept 3.0 for one release.", residual="codegen still 3.0 leftover; drop after codegen 6", vs="r3867 oas31-schema-dialect (root 3.1 vs 3.0 leftover, not jsonSchemaDialect)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch1_ok="openapi: 3.1.0 is not leftover 3.0.3.", fetch2="https://spec.openapis.org/oas/v3.0.3.html#versions", fetch2_ok="Exclusive 3.1 root 400 leftover 3.0."),
     p(slug="leftover-oas30-root", domain="oas30-root-vs-oas31-root", success=False, name="oas30r", stack="OpenAPI leftover 3.0 root + Java + TS", field="openapi", old="openapi 3.1.0", new="oas30 root leftover only", fail_err="400: leftover 3.1 after 3.0-only", plan="3.0-only 400s leftover 3.1 root. Freeze 3.1, spec 3.0 leftover.", residual="handoff: keep 3.1 root or force 3.0 leftover", vs="r3867 leftover-schema-draft04 (3.0 leftover, not draft-04)", fetch1="https://spec.openapis.org/oas/v3.0.3.html#versions", fetch1_ok="3.0.3 root is not 3.1.0.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch2_ok="Exclusive 3.0 root 400 leftover 3.1.")),
    (p(slug="oas-schema-id", domain="oas-schema-id-vs-missing-id", success=True, name="schid", stack="OpenAPI 3.1 $id + Go", field="$id", old="missing schema id leftover", new="schema dollarid", fail_err="400: leftover missing $id after id-only", plan="$id-only 400s leftover missing id. Dual-omit $id for one release.", residual="resolver still missing leftover; drop after resolver 5", vs="r3899 oas-content-schema-ref (schema $id vs missing leftover, not content $ref)", fetch1="https://json-schema.org/understanding-json-schema/structuring#id", fetch1_ok="$id identifies a schema resource, leftover missing ids fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $id 400 leftover missing."),
     p(slug="leftover-missing-schema-id", domain="missing-id-vs-oas-schema-id", success=False, name="noid", stack="OpenAPI leftover missing $id + Java + TS", field="$id", old="schema dollarid", new="missing schema id leftover only", fail_err="400: leftover $id after missing-only", plan="Missing-only 400s leftover $id. Freeze $id, spec missing leftover.", residual="handoff: keep $id or force missing leftover", vs="r3899 leftover-inline-schema (missing $id leftover, not inline schema)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Missing $id is not a schema identifier.", fetch2="https://json-schema.org/understanding-json-schema/structuring#id", fetch2_ok="Exclusive missing $id 400 leftover id.")),
    (p(slug="oas-schema-anchor", domain="oas-anchor-vs-unanchored-def", success=True, name="anch", stack="OpenAPI 3.1 $anchor + Go", field="$anchor", old="unanchored def leftover", new="schema dollaranchor", fail_err="400: leftover unanchored def after $anchor-only", plan="$anchor-only 400s leftover unanchored. Dual-read unanchored for one release.", residual="resolver still unanchored leftover; drop after resolver 6", vs="r3899 oas-pattern-anchor (schema $anchor vs unanchored leftover, not regex anchor)", fetch1="https://json-schema.org/understanding-json-schema/structuring#anchor", fetch1_ok="$anchor names a location in-schema, leftover unanchored defs fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $anchor 400 leftover unanchored."),
     p(slug="leftover-unanchored-def", domain="unanchored-def-vs-oas-anchor", success=False, name="unanch", stack="OpenAPI leftover unanchored def + Java + TS", field="$defs", old="schema dollaranchor", new="unanchored def leftover only", fail_err="400: leftover $anchor after unanchored-only", plan="Unanchored-only 400s leftover $anchor. Freeze $anchor, spec unanchored leftover.", residual="handoff: keep $anchor or force unanchored leftover", vs="r3899 leftover-unanchored-regex (unanchored def leftover, not regex)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unanchored $defs are not $anchor.", fetch2="https://json-schema.org/understanding-json-schema/structuring#anchor", fetch2_ok="Exclusive unanchored def 400 leftover $anchor.")),
    (p(slug="oas-schema-dynamicref", domain="oas-dynamicref-vs-static-ref", success=True, name="dynref", stack="OpenAPI 3.1 $dynamicRef + Go", field="$dynamicRef", old="static ref leftover", new="schema dynamicRef", fail_err="400: leftover static $ref after dynamicRef-only", plan="$dynamicRef-only 400s leftover static $ref. Dual-read static for one release.", residual="resolver still static leftover; drop after resolver 5", vs="r3899 oas-content-schema-ref ($dynamicRef vs static leftover, not content $ref)", fetch1="https://json-schema.org/understanding-json-schema/structuring#dynamicref", fetch1_ok="$dynamicRef follows dynamic scope, leftover static $ref does not.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $dynamicRef 400 leftover static $ref."),
     p(slug="leftover-static-ref", domain="static-ref-vs-oas-dynamicref", success=False, name="statref", stack="OpenAPI leftover static $ref + Java + TS", field="$ref", old="schema dynamicRef", new="static ref leftover only", fail_err="400: leftover $dynamicRef after static-only", plan="Static-only 400s leftover $dynamicRef. Freeze $dynamicRef, spec static leftover.", residual="handoff: keep $dynamicRef or force static leftover", vs="r3899 leftover-inline-schema (static leftover, not inline)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Static $ref is not $dynamicRef.", fetch2="https://json-schema.org/understanding-json-schema/structuring#dynamicref", fetch2_ok="Exclusive static $ref 400 leftover $dynamicRef.")),
    (p(slug="oas-operation-tags-required", domain="oas-op-tags-vs-untagged-op", success=True, name="optags", stack="OpenAPI 3.1 operation tags + Go", field="tags", old="untagged op leftover", new="operation tags", fail_err="400: leftover untagged op after tags-only", plan="Operation-tags-only 400s leftover untagged. Dual-accept untagged for one release.", residual="portal still untagged leftover; drop after portal 5", vs="r3963 oas-tag-description (operation tags vs untagged leftover, not tag description)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Operation tags group ops; leftover untagged ops fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive operation tags 400 leftover untagged."),
     p(slug="leftover-untagged-op", domain="untagged-op-vs-oas-op-tags", success=False, name="untagop", stack="OpenAPI leftover untagged op + Java + TS", field="tags", old="operation tags", new="untagged op leftover only", fail_err="400: leftover tags after untagged-only", plan="Untagged-only 400s leftover operation tags. Freeze tags, spec untagged leftover.", residual="handoff: keep operation tags or force untagged leftover", vs="r3883 leftover-untagged-ops (untagged op leftover, not untagged-ops plant)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Untagged ops are not tagged.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive untagged op 400 leftover tags.")),
    (p(slug="oas-security-http-digest", domain="oas-digest-vs-basic-auth", success=True, name="digest", stack="OpenAPI 3.1 HTTP digest + Go", field="scheme", old="http basic leftover", new="http digest", fail_err="401: leftover http basic after digest-only", plan="Digest-only 401s leftover basic. Dual-accept basic for one release.", residual="legacy still basic leftover; drop after legacy 6", vs="r3947 leftover-http-basic (digest vs basic leftover, not bearer mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch1_ok="HTTP digest is not leftover basic.", fetch2="https://datatracker.ietf.org/doc/html/rfc7616", fetch2_ok="Exclusive digest 401 leftover basic."),
     p(slug="leftover-http-digest-off", domain="basic-auth-vs-oas-digest", success=False, name="nodig", stack="OpenAPI leftover basic vs digest + Java + TS", field="scheme", old="http digest", new="http basic leftover only", fail_err="401: leftover digest after basic-only", plan="Basic-only 401s leftover digest. Freeze digest, spec basic leftover.", residual="handoff: keep digest or force basic leftover", vs="r3947 oas-security-http-bearer (basic leftover, not bearer)", fetch1="https://datatracker.ietf.org/doc/html/rfc7617", fetch1_ok="HTTP basic is not digest.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object", fetch2_ok="Exclusive basic 401 leftover digest.")),
    (p(slug="oas-components-links", domain="oas-components-links-vs-inline-links", success=True, name="clink", stack="OpenAPI 3.1 components.links + Go", field="links", old="inline links leftover", new="components links", fail_err="400: leftover inline links after components-only", plan="components.links-only 400s leftover inline. Dual-read inline for one release.", residual="sdk still inline leftover; drop after sdk 5", vs="r3978 oas-link-description (components.links vs inline leftover, not link description)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.links reuse Link Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="Exclusive components.links 400 leftover inline."),
     p(slug="leftover-inline-links", domain="inline-links-vs-oas-components-links", success=False, name="ilink", stack="OpenAPI leftover inline links + Java + TS", field="links", old="components links", new="inline links leftover only", fail_err="400: leftover components.links after inline-only", plan="Inline-only 400s leftover components.links. Freeze components.links, spec inline leftover.", residual="handoff: keep components.links or force inline leftover", vs="r3978 leftover-undocumented-link (inline leftover, not undocumented)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="Inline links are not components.links.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline links 400 leftover components.")),
    (p(slug="oas-components-callbacks", domain="oas-components-callbacks-vs-inline-cb", success=True, name="ccb", stack="OpenAPI 3.1 components.callbacks + Go", field="callbacks", old="inline callbacks leftover", new="components callbacks", fail_err="400: leftover inline callbacks after components-only", plan="components.callbacks-only 400s leftover inline. Dual-read inline for one release.", residual="bus still inline leftover; drop after bus 6", vs="r3978 oas-callback-description (components.callbacks vs inline leftover, not description)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch1_ok="components.callbacks reuse Callback Objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch2_ok="Exclusive components.callbacks 400 leftover inline."),
     p(slug="leftover-inline-callbacks", domain="inline-cb-vs-oas-components-callbacks", success=False, name="icb", stack="OpenAPI leftover inline callbacks + Java + TS", field="callbacks", old="components callbacks", new="inline callbacks leftover only", fail_err="400: leftover components.callbacks after inline-only", plan="Inline-only 400s leftover components.callbacks. Freeze components.callbacks, spec inline leftover.", residual="handoff: keep components.callbacks or force inline leftover", vs="r3978 leftover-undocumented-cb (inline leftover, not undocumented)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#callback-object", fetch1_ok="Inline callbacks are not components.callbacks.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#components-object", fetch2_ok="Exclusive inline callbacks 400 leftover components.")),
    (p(slug="oas-format-float", domain="oas-float-vs-unbounded-number", success=True, name="fmtflt", stack="OpenAPI 3.1 format=float + Go", field="format", old="unbounded number leftover", new="format float", fail_err="400: leftover unbounded number after float-only", plan="format=float-only 400s leftover unbounded. Dual-read unbounded for one release.", residual="js still unbounded leftover; drop after js 5", vs="r3931 leftover-unbounded-number (float vs unbounded leftover, not maximum)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="format=float is IEEE 754 binary32, not leftover unbounded numbers.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric", fetch2_ok="Exclusive float 400 leftover unbounded."),
     p(slug="leftover-unbounded-float", domain="unbounded-number-vs-oas-float", success=False, name="unbflt", stack="OpenAPI leftover unbounded number + Java + TS", field="type", old="format float", new="unbounded number leftover only", fail_err="400: leftover float after unbounded-only", plan="Unbounded-only 400s leftover float. Freeze float, spec unbounded leftover.", residual="handoff: keep format=float or force unbounded leftover", vs="r3931 oas-maximum-inclusive (unbounded leftover, not maximum)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric", fetch1_ok="Unbounded numbers are not format=float.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive unbounded 400 leftover float.")),
    (p(slug="oas-min-properties", domain="oas-minproperties-vs-empty-object", success=True, name="minprop", stack="OpenAPI 3.1 minProperties + Go", field="minProperties", old="empty object leftover", new="minProperties", fail_err="400: leftover empty object after minProperties-only", plan="minProperties-only 400s leftover empty object. Dual-accept empty for one release.", residual="form still empty leftover; drop after form 4", vs="r3899 leftover-open-object (minProperties vs empty leftover, not open object)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch1_ok="minProperties rejects leftover empty objects.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minProperties 400 leftover empty."),
     p(slug="leftover-empty-object", domain="empty-object-vs-oas-minproperties", success=False, name="empobj", stack="OpenAPI leftover empty object + Java + TS", field="properties", old="minProperties", new="empty object leftover only", fail_err="400: leftover minProperties after empty-only", plan="Empty-only 400s leftover minProperties. Freeze minProperties, spec empty leftover.", residual="handoff: keep minProperties or force empty leftover", vs="r3899 oas-additionalproperties-false (empty leftover, not closed object)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Empty objects are not minProperties.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#minproperties", fetch2_ok="Exclusive empty object 400 leftover minProperties.")),
    (p(slug="oas-max-properties", domain="oas-maxproperties-vs-unbounded-object", success=True, name="maxprop", stack="OpenAPI 3.1 maxProperties + Go", field="maxProperties", old="unbounded object leftover", new="maxProperties", fail_err="400: leftover unbounded object after maxProperties-only", plan="maxProperties-only 400s leftover unbounded. Dual-accept unbounded for one release.", residual="partner still unbounded leftover; drop after partner 5", vs="r3899 leftover-open-object (maxProperties vs unbounded leftover, not open object)", fetch1="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch1_ok="maxProperties caps object keys; leftover unbounded objects fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive maxProperties 400 leftover unbounded."),
     p(slug="leftover-unbounded-object", domain="unbounded-object-vs-oas-maxproperties", success=False, name="unbobj", stack="OpenAPI leftover unbounded object + Java + TS", field="additionalProperties", old="maxProperties", new="unbounded object leftover only", fail_err="400: leftover maxProperties after unbounded-only", plan="Unbounded-only 400s leftover maxProperties. Freeze maxProperties, spec unbounded leftover.", residual="handoff: keep maxProperties or force unbounded leftover", vs="r3899 oas-additionalproperties-false (unbounded leftover, not closed object)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Unbounded objects are not maxProperties.", fetch2="https://json-schema.org/understanding-json-schema/reference/object#maxproperties", fetch2_ok="Exclusive unbounded object 400 leftover maxProperties.")),
    (p(slug="oas-xml-wrapped-false", domain="oas-unwrapped-xml-vs-always-wrap", success=True, name="xmluw", stack="OpenAPI 3.1 xml.wrapped false + Go", field="wrapped", old="always wrap leftover", new="xml wrapped false", fail_err="415: leftover always-wrap after unwrapped-only", plan="xml.wrapped=false-only 415s leftover always-wrap. Dual-read wrap for one release.", residual="batch still wrap leftover; drop after batch 6", vs="wrap xml-wrapped-array (wrapped false vs always-wrap leftover, not wrapped array cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="xml.wrapped false is not leftover always-wrapped arrays.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unwrapped 415 leftover always-wrap."),
     p(slug="leftover-always-wrap", domain="always-wrap-vs-oas-unwrapped-xml", success=False, name="alwrap", stack="OpenAPI leftover always wrap + Java + TS", field="wrapped", old="xml wrapped false", new="always wrap leftover only", fail_err="415: leftover unwrapped after always-wrap-only", plan="Always-wrap-only 415s leftover xml.wrapped false. Freeze unwrapped, spec wrap leftover.", residual="handoff: keep unwrapped or force always-wrap leftover", vs="wrap xml-wrapped-array (always-wrap leftover, not wrapped cartesian)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Always-wrap is not xml.wrapped false.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="Exclusive always-wrap 415 leftover unwrapped.")),
    (p(slug="oas-allowemptyvalue-header", domain="oas-empty-header-vs-omit-empty-header", success=True, name="hdempty", stack="OpenAPI 3.1 header allowEmptyValue + Go", field="allowEmptyValue", old="omit empty header leftover", new="header allowEmptyValue", fail_err="400: leftover omit-empty header after allowEmptyValue-only", plan="Header-allowEmptyValue-only 400s leftover omit. Dual-omit empty for one release.", residual="proxy still omit leftover; drop after proxy 5", vs="r3899 oas-query-allowemptyvalue (header allowEmptyValue vs omit leftover, not query)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="allowEmptyValue on headers keeps empty leftover headers.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header allowEmptyValue 400 leftover omit."),
     p(slug="leftover-omit-header-empty", domain="omit-empty-header-vs-oas-empty-header", success=False, name="omithe", stack="OpenAPI leftover omit empty header + Java + TS", field="required", old="header allowEmptyValue", new="omit empty header leftover only", fail_err="400: leftover allowEmptyValue after omit-only", plan="Omit-only 400s leftover header allowEmptyValue. Freeze allowEmptyValue, spec omit leftover.", residual="handoff: keep header allowEmptyValue or force omit leftover", vs="r3899 leftover-omit-empty-query (omit header leftover, not query omit)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Omitting empty headers is not allowEmptyValue.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive omit empty header 400 leftover allowEmptyValue.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r3993"}))


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
