#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4326. Fast slug load."""
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
    (p(slug="oas-schema-comment-keyword", domain="oas-schema-comment-keyword-vs-leftover-description-as-comment", success=True, name="206968", stack="OpenAPI 3.1 $comment + Go", field="$comment", old="description as comment leftover", new="$comment keyword", fail_err="400: leftover description as comment leftover after $comment keyword-only", plan="$comment keyword-only 400s leftover description as comment leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($comment keyword vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch1_ok="$comment is not leftover description-as-comment.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $comment 400 leftover description."),
     p(slug="leftover-description-as-comment", domain="leftover-description-as-comment-vs-oas-schema-comment-keyword", success=False, name="5d6167", stack="OpenAPI leftover $comment + Java + TS", field="$comment", old="$comment keyword", new="description as comment leftover only", fail_err="400: leftover $comment keyword after description as comment leftover-only", plan="description as comment leftover-only 400s leftover $comment keyword. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (description as comment leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $comment 400 leftover description.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#annotation", fetch2_ok="$comment is not leftover description-as-comment.")),
    (p(slug="oas-schema-anchor-id", domain="oas-schema-anchor-id-vs-leftover-name-as-anchor", success=True, name="fc19ff", stack="OpenAPI 3.1 $anchor + Go", field="$anchor", old="name as anchor leftover", new="schema $anchor", fail_err="400: leftover name as anchor leftover after schema $anchor-only", plan="schema $anchor-only 400s leftover name as anchor leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (schema $anchor vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch1_ok="$anchor is a plain name, leftover title-as-anchor fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $anchor 400 leftover name."),
     p(slug="leftover-name-as-anchor", domain="leftover-name-as-anchor-vs-oas-schema-anchor-id", success=False, name="933597", stack="OpenAPI leftover $anchor + Java + TS", field="$anchor", old="schema $anchor", new="name as anchor leftover only", fail_err="400: leftover schema $anchor after name as anchor leftover-only", plan="name as anchor leftover-only 400s leftover schema $anchor. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (name as anchor leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $anchor 400 leftover name.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#anchor", fetch2_ok="$anchor is a plain name, leftover title-as-anchor fails closed.")),
    (p(slug="oas-vocabulary-required", domain="oas-vocabulary-required-vs-leftover-unconstrained-vocab", success=True, name="44b3b1", stack="OpenAPI 3.1 $vocabulary + Go", field="$vocabulary", old="unconstrained vocab leftover", new="$vocabulary required", fail_err="400: leftover unconstrained vocab leftover after $vocabulary required-only", plan="$vocabulary required-only 400s leftover unconstrained vocab leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv ($vocabulary required vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch1_ok="$vocabulary declares required vocabs, leftover unconstrained fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive $vocabulary 400 leftover unconstrained."),
     p(slug="leftover-unconstrained-vocab", domain="leftover-unconstrained-vocab-vs-oas-vocabulary-required", success=False, name="774295", stack="OpenAPI leftover $vocabulary + Java + TS", field="$vocabulary", old="$vocabulary required", new="unconstrained vocab leftover only", fail_err="400: leftover $vocabulary required after unconstrained vocab leftover-only", plan="unconstrained vocab leftover-only 400s leftover $vocabulary required. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unconstrained vocab leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive $vocabulary 400 leftover unconstrained.", fetch2="https://json-schema.org/understanding-json-schema/reference/schema#vocabulary", fetch2_ok="$vocabulary declares required vocabs, leftover unconstrained fails closed.")),
    (p(slug="oas-format-uri-template-expr", domain="oas-format-uri-template-expr-vs-leftover-printf-url-template", success=True, name="e79e73", stack="OpenAPI 3.1 format + Go", field="format", old="printf url leftover", new="format uri-template", fail_err="400: leftover printf url leftover after format uri-template-only", plan="format uri-template-only 400s leftover printf url leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format uri-template vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=uri-template is RFC6570, leftover sprintf fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6570", fetch2_ok="Exclusive uri-template 400 leftover sprintf."),
     p(slug="leftover-printf-url-template", domain="leftover-printf-url-template-vs-oas-format-uri-template-expr", success=False, name="095c8c", stack="OpenAPI leftover format + Java + TS", field="format", old="format uri-template", new="printf url leftover only", fail_err="400: leftover format uri-template after printf url leftover-only", plan="printf url leftover-only 400s leftover format uri-template. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (printf url leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6570", fetch1_ok="Exclusive uri-template 400 leftover sprintf.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=uri-template is RFC6570, leftover sprintf fails closed.")),
    (p(slug="oas-relative-json-pointer", domain="oas-relative-json-pointer-vs-leftover-absolute-pointer-only", success=True, name="12de00", stack="OpenAPI 3.1 format + Go", field="format", old="absolute pointer leftover", new="relative json pointer", fail_err="400: leftover absolute pointer leftover after relative json pointer-only", plan="relative json pointer-only 400s leftover absolute pointer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (relative json pointer vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch1_ok="relative JSON pointer is not leftover absolute-only pointers.", fetch2="https://datatracker.ietf.org/doc/html/rfc6901", fetch2_ok="Exclusive relative pointer 400 leftover absolute."),
     p(slug="leftover-absolute-pointer-only", domain="leftover-absolute-pointer-only-vs-oas-relative-json-pointer", success=False, name="8e3c33", stack="OpenAPI leftover format + Java + TS", field="format", old="relative json pointer", new="absolute pointer leftover only", fail_err="400: leftover relative json pointer after absolute pointer leftover-only", plan="absolute pointer leftover-only 400s leftover relative json pointer. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (absolute pointer leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6901", fetch1_ok="Exclusive relative pointer 400 leftover absolute.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch2_ok="relative JSON pointer is not leftover absolute-only pointers.")),
    (p(slug="oas-format-iri-absolute", domain="oas-format-iri-absolute-vs-leftover-uri-as-iri", success=True, name="a009d0", stack="OpenAPI 3.1 format + Go", field="format", old="uri as iri leftover", new="format iri", fail_err="400: leftover uri as iri leftover after format iri-only", plan="format iri-only 400s leftover uri as iri leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format iri vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="format=iri is RFC3987, leftover URI-as-IRI fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive iri 400 leftover uri."),
     p(slug="leftover-uri-as-iri", domain="leftover-uri-as-iri-vs-oas-format-iri-absolute", success=False, name="d180f3", stack="OpenAPI leftover format + Java + TS", field="format", old="format iri", new="uri as iri leftover only", fail_err="400: leftover format iri after uri as iri leftover-only", plan="uri as iri leftover-only 400s leftover format iri. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (uri as iri leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive iri 400 leftover uri.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="format=iri is RFC3987, leftover URI-as-IRI fails closed.")),
    (p(slug="oas-format-duration-iso8601", domain="oas-format-duration-iso8601-vs-leftover-seconds-int-duration", success=True, name="8c85e9", stack="OpenAPI 3.1 format + Go", field="format", old="seconds int leftover", new="format duration iso8601", fail_err="400: leftover seconds int leftover after format duration iso8601-only", plan="format duration iso8601-only 400s leftover seconds int leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format duration iso8601 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch1_ok="format=duration is ISO8601, leftover integer seconds fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive duration 400 leftover seconds."),
     p(slug="leftover-seconds-int-duration", domain="leftover-seconds-int-duration-vs-oas-format-duration-iso8601", success=False, name="5dc34f", stack="OpenAPI leftover format + Java + TS", field="format", old="format duration iso8601", new="seconds int leftover only", fail_err="400: leftover format duration iso8601 after seconds int leftover-only", plan="seconds int leftover-only 400s leftover format duration iso8601. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (seconds int leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive duration 400 leftover seconds.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch2_ok="format=duration is ISO8601, leftover integer seconds fail closed.")),
    (p(slug="oas-format-ipv6-strict", domain="oas-format-ipv6-strict-vs-leftover-ipv4-mapped-ipv6", success=True, name="624d19", stack="OpenAPI 3.1 format + Go", field="format", old="v4 mapped leftover", new="format ipv6", fail_err="400: leftover v4 mapped leftover after format ipv6-only", plan="format ipv6-only 400s leftover v4 mapped leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format ipv6 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#ipv6", fetch1_ok="format=ipv6 is RFC4291, leftover v4-mapped fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ipv6 400 leftover v4-mapped."),
     p(slug="leftover-ipv4-mapped-ipv6", domain="leftover-ipv4-mapped-ipv6-vs-oas-format-ipv6-strict", success=False, name="50fb88", stack="OpenAPI leftover format + Java + TS", field="format", old="format ipv6", new="v4 mapped leftover only", fail_err="400: leftover format ipv6 after v4 mapped leftover-only", plan="v4 mapped leftover-only 400s leftover format ipv6. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (v4 mapped leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive ipv6 400 leftover v4-mapped.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#ipv6", fetch2_ok="format=ipv6 is RFC4291, leftover v4-mapped fails closed.")),
    (p(slug="oas-format-hostname-ldh", domain="oas-format-hostname-ldh-vs-leftover-underscore-hostname", success=True, name="7044fd", stack="OpenAPI 3.1 format + Go", field="format", old="underscore host leftover", new="format hostname ldh", fail_err="400: leftover underscore host leftover after format hostname ldh-only", plan="format hostname ldh-only 400s leftover underscore host leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format hostname ldh vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch1_ok="format=hostname is LDH labels, leftover underscores fail closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive hostname 400 leftover underscore."),
     p(slug="leftover-underscore-hostname", domain="leftover-underscore-hostname-vs-oas-format-hostname-ldh", success=False, name="d9d958", stack="OpenAPI leftover format + Java + TS", field="format", old="format hostname ldh", new="underscore host leftover only", fail_err="400: leftover format hostname ldh after underscore host leftover-only", plan="underscore host leftover-only 400s leftover format hostname ldh. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (underscore host leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive hostname 400 leftover underscore.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch2_ok="format=hostname is LDH labels, leftover underscores fail closed.")),
    (p(slug="oas-parameter-style-matrix-explode", domain="oas-parameter-style-matrix-explode-vs-leftover-semicolon-path-csv", success=True, name="1d7298", stack="OpenAPI 3.1 style + Go", field="style", old="semicolon csv leftover", new="matrix explode path", fail_err="400: leftover semicolon csv leftover after matrix explode path-only", plan="matrix explode path-only 400s leftover semicolon csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (matrix explode path vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=matrix explode is not leftover semicolon csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive matrix explode 400 leftover semicolon csv."),
     p(slug="leftover-semicolon-path-csv", domain="leftover-semicolon-path-csv-vs-oas-parameter-style-matrix-explode", success=False, name="91bdd6", stack="OpenAPI leftover style + Java + TS", field="style", old="matrix explode path", new="semicolon csv leftover only", fail_err="400: leftover matrix explode path after semicolon csv leftover-only", plan="semicolon csv leftover-only 400s leftover matrix explode path. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (semicolon csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive matrix explode 400 leftover semicolon csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="style=matrix explode is not leftover semicolon csv.")),
    (p(slug="oas-parameter-style-label-explode", domain="oas-parameter-style-label-explode-vs-leftover-dot-path-csv", success=True, name="fe9dc4", stack="OpenAPI 3.1 style + Go", field="style", old="dot csv leftover", new="label explode path", fail_err="400: leftover dot csv leftover after label explode path-only", plan="label explode path-only 400s leftover dot csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (label explode path vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="style=label explode is not leftover dot csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive label explode 400 leftover dot csv."),
     p(slug="leftover-dot-path-csv", domain="leftover-dot-path-csv-vs-oas-parameter-style-label-explode", success=False, name="b004ae", stack="OpenAPI leftover style + Java + TS", field="style", old="label explode path", new="dot csv leftover only", fail_err="400: leftover label explode path after dot csv leftover-only", plan="dot csv leftover-only 400s leftover label explode path. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (dot csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive label explode 400 leftover dot csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="style=label explode is not leftover dot csv.")),
    (p(slug="oas-cookie-style-form-explode", domain="oas-cookie-style-form-explode-vs-leftover-cookie-csv", success=True, name="8645df", stack="OpenAPI 3.1 style + Go", field="style", old="cookie csv leftover", new="cookie form explode", fail_err="400: leftover cookie csv leftover after cookie form explode-only", plan="cookie form explode-only 400s leftover cookie csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (cookie form explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="cookie style=form explode is not leftover cookie csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive cookie explode 400 leftover csv."),
     p(slug="leftover-cookie-csv", domain="leftover-cookie-csv-vs-oas-cookie-style-form-explode", success=False, name="cf8f3c", stack="OpenAPI leftover style + Java + TS", field="style", old="cookie form explode", new="cookie csv leftover only", fail_err="400: leftover cookie form explode after cookie csv leftover-only", plan="cookie csv leftover-only 400s leftover cookie form explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (cookie csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive cookie explode 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="cookie style=form explode is not leftover cookie csv.")),
    (p(slug="oas-header-style-simple-explode", domain="oas-header-style-simple-explode-vs-leftover-header-csv", success=True, name="2c95f6", stack="OpenAPI 3.1 style + Go", field="style", old="header csv leftover", new="header simple explode", fail_err="400: leftover header csv leftover after header simple explode-only", plan="header simple explode-only 400s leftover header csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (header simple explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="header style=simple explode is not leftover header csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive header explode 400 leftover csv."),
     p(slug="leftover-header-csv", domain="leftover-header-csv-vs-oas-header-style-simple-explode", success=False, name="30d85f", stack="OpenAPI leftover style + Java + TS", field="style", old="header simple explode", new="header csv leftover only", fail_err="400: leftover header simple explode after header csv leftover-only", plan="header csv leftover-only 400s leftover header simple explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive header explode 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="header style=simple explode is not leftover header csv.")),
    (p(slug="oas-deepobject-query-explode", domain="oas-deepobject-query-explode-vs-leftover-bracket-query", success=True, name="8a41cb", stack="OpenAPI 3.1 style + Go", field="style", old="bracket query leftover", new="deepObject explode", fail_err="400: leftover bracket query leftover after deepObject explode-only", plan="deepObject explode-only 400s leftover bracket query leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (deepObject explode vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="deepObject explode is not leftover bracket query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive deepObject 400 leftover bracket."),
     p(slug="leftover-bracket-query", domain="leftover-bracket-query-vs-oas-deepobject-query-explode", success=False, name="e461a3", stack="OpenAPI leftover style + Java + TS", field="style", old="deepObject explode", new="bracket query leftover only", fail_err="400: leftover deepObject explode after bracket query leftover-only", plan="bracket query leftover-only 400s leftover deepObject explode. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (bracket query leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive deepObject 400 leftover bracket.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="deepObject explode is not leftover bracket query.")),
    (p(slug="oas-query-form-explode-true", domain="oas-query-form-explode-true-vs-leftover-query-repeated-csv", success=True, name="a2e812", stack="OpenAPI 3.1 explode + Go", field="explode", old="repeated csv leftover", new="query form explode true", fail_err="400: leftover repeated csv leftover after query form explode true-only", plan="query form explode true-only 400s leftover repeated csv leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (query form explode true vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="form explode true repeats keys, leftover csv fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive form explode 400 leftover repeated csv."),
     p(slug="leftover-query-repeated-csv", domain="leftover-query-repeated-csv-vs-oas-query-form-explode-true", success=False, name="92cfeb", stack="OpenAPI leftover explode + Java + TS", field="explode", old="query form explode true", new="repeated csv leftover only", fail_err="400: leftover query form explode true after repeated csv leftover-only", plan="repeated csv leftover-only 400s leftover query form explode true. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (repeated csv leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive form explode 400 leftover repeated csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="form explode true repeats keys, leftover csv fails closed.")),
    (p(slug="oas-response-304-no-body", domain="oas-response-304-no-body-vs-leftover-304-with-body", success=True, name="44d2bc", stack="OpenAPI 3.1 content + Go", field="content", old="304 body leftover", new="304 no body", fail_err="400: leftover 304 body leftover after 304 no body-only", plan="304 no body-only 400s leftover 304 body leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (304 no body vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="304 MUST NOT include a body, leftover bodies fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc9110#name-304-not-modified", fetch2_ok="Exclusive 304 empty 400 leftover body."),
     p(slug="leftover-304-with-body", domain="leftover-304-with-body-vs-oas-response-304-no-body", success=False, name="763c95", stack="OpenAPI leftover content + Java + TS", field="content", old="304 no body", new="304 body leftover only", fail_err="400: leftover 304 no body after 304 body leftover-only", plan="304 body leftover-only 400s leftover 304 no body. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (304 body leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc9110#name-304-not-modified", fetch1_ok="Exclusive 304 empty 400 leftover body.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="304 MUST NOT include a body, leftover bodies fail closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4326"}))


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
