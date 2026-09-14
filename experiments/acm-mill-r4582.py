#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4582. Fast slug load."""
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
    (p(slug="oas-pattern-unicode-u", domain="oas-pattern-unicode-u-vs-leftover-ascii-only-pattern", success=True, name="da071b", stack="OpenAPI 3.1 pattern + Go", field="pattern", old="ascii pattern leftover", new="unicode pattern", fail_err="400: leftover ascii pattern leftover after unicode pattern-only", plan="unicode pattern-only 400s leftover ascii pattern leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (unicode pattern vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch1_ok="pattern is Unicode, leftover ASCII-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive unicode pattern 400 leftover ascii."),
     p(slug="leftover-ascii-only-pattern", domain="leftover-ascii-only-pattern-vs-oas-pattern-unicode-u", success=False, name="6b86b0", stack="OpenAPI leftover pattern + Java + TS", field="pattern", old="unicode pattern", new="ascii pattern leftover only", fail_err="400: leftover unicode pattern after ascii pattern leftover-only", plan="ascii pattern leftover-only 400s leftover unicode pattern. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (ascii pattern leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive unicode pattern 400 leftover ascii.", fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch2_ok="pattern is Unicode, leftover ASCII-only fails closed.")),
    (p(slug="oas-format-regex-js", domain="oas-format-regex-js-vs-leftover-pcre-pattern", success=True, name="1daffa", stack="OpenAPI 3.1 format + Go", field="format", old="pcre leftover", new="format regex ECMA", fail_err="400: leftover pcre leftover after format regex ECMA-only", plan="format regex ECMA-only 400s leftover pcre leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format regex ECMA vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch1_ok="format=regex is ECMA-262, leftover PCRE fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ECMA regex 400 leftover PCRE."),
     p(slug="leftover-pcre-pattern", domain="leftover-pcre-pattern-vs-oas-format-regex-js", success=False, name="167966", stack="OpenAPI leftover format + Java + TS", field="format", old="format regex ECMA", new="pcre leftover only", fail_err="400: leftover format regex ECMA after pcre leftover-only", plan="pcre leftover-only 400s leftover format regex ECMA. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (pcre leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive ECMA regex 400 leftover PCRE.", fetch2="https://json-schema.org/understanding-json-schema/reference/regular_expressions", fetch2_ok="format=regex is ECMA-262, leftover PCRE fails closed.")),
    (p(slug="oas-xml-wrapped-scalar-ban", domain="oas-xml-wrapped-scalar-ban-vs-leftover-wrap-scalar-xml", success=True, name="96dc73", stack="OpenAPI 3.1 wrapped + Go", field="wrapped", old="wrap scalar leftover", new="xml wrapped scalar banned", fail_err="415: leftover wrap scalar leftover after xml wrapped scalar banned-only", plan="xml wrapped scalar banned-only 415s leftover wrap scalar leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml wrapped scalar banned vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="wrapped applies to arrays, leftover wrap-scalar fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive wrapped ban 415 leftover scalar wrap."),
     p(slug="leftover-wrap-scalar-xml", domain="leftover-wrap-scalar-xml-vs-oas-xml-wrapped-scalar-ban", success=False, name="de1c54", stack="OpenAPI leftover wrapped + Java + TS", field="wrapped", old="xml wrapped scalar banned", new="wrap scalar leftover only", fail_err="415: leftover xml wrapped scalar banned after wrap scalar leftover-only", plan="wrap scalar leftover-only 415s leftover xml wrapped scalar banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (wrap scalar leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive wrapped ban 415 leftover scalar wrap.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="wrapped applies to arrays, leftover wrap-scalar fails closed.")),
    (p(slug="oas-xml-attr-on-object-ban", domain="oas-xml-attr-on-object-ban-vs-leftover-object-as-xml-attr", success=True, name="673a85", stack="OpenAPI 3.1 attribute + Go", field="attribute", old="object as attr leftover", new="xml attribute on object banned", fail_err="415: leftover object as attr leftover after xml attribute on object banned-only", plan="xml attribute on object banned-only 415s leftover object as attr leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (xml attribute on object banned vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch1_ok="attribute is for scalars, leftover object-as-attr fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive attr ban 415 leftover object attr."),
     p(slug="leftover-object-as-xml-attr", domain="leftover-object-as-xml-attr-vs-oas-xml-attr-on-object-ban", success=False, name="91dad3", stack="OpenAPI leftover attribute + Java + TS", field="attribute", old="xml attribute on object banned", new="object as attr leftover only", fail_err="415: leftover xml attribute on object banned after object as attr leftover-only", plan="object as attr leftover-only 415s leftover xml attribute on object banned. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (object as attr leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive attr ban 415 leftover object attr.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#xml-object", fetch2_ok="attribute is for scalars, leftover object-as-attr fails closed.")),
    (p(slug="oas-deepobject-header-invalid", domain="oas-deepobject-header-invalid-vs-leftover-header-deepobject", success=True, name="b3324a", stack="OpenAPI 3.1 style + Go", field="style", old="header deepObject leftover", new="deepObject header invalid", fail_err="400: leftover header deepObject leftover after deepObject header invalid-only", plan="deepObject header invalid-only 400s leftover header deepObject leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (deepObject header invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="deepObject is query-only, leftover header deepObject fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive header deepObject ban 400 leftover header."),
     p(slug="leftover-header-deepobject", domain="leftover-header-deepobject-vs-oas-deepobject-header-invalid", success=False, name="3c3a6b", stack="OpenAPI leftover style + Java + TS", field="style", old="deepObject header invalid", new="header deepObject leftover only", fail_err="400: leftover deepObject header invalid after header deepObject leftover-only", plan="header deepObject leftover-only 400s leftover deepObject header invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (header deepObject leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive header deepObject ban 400 leftover header.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="deepObject is query-only, leftover header deepObject fails closed.")),
    (p(slug="oas-matrix-query-invalid", domain="oas-matrix-query-invalid-vs-leftover-query-matrix-style", success=True, name="22539d", stack="OpenAPI 3.1 style + Go", field="style", old="query matrix leftover", new="matrix query invalid", fail_err="400: leftover query matrix leftover after matrix query invalid-only", plan="matrix query invalid-only 400s leftover query matrix leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (matrix query invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="matrix is path-only, leftover query matrix fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive matrix query ban 400 leftover query."),
     p(slug="leftover-query-matrix-style", domain="leftover-query-matrix-style-vs-oas-matrix-query-invalid", success=False, name="c2541a", stack="OpenAPI leftover style + Java + TS", field="style", old="matrix query invalid", new="query matrix leftover only", fail_err="400: leftover matrix query invalid after query matrix leftover-only", plan="query matrix leftover-only 400s leftover matrix query invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (query matrix leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive matrix query ban 400 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="matrix is path-only, leftover query matrix fails closed.")),
    (p(slug="oas-label-query-invalid", domain="oas-label-query-invalid-vs-leftover-query-label-style", success=True, name="fd5d29", stack="OpenAPI 3.1 style + Go", field="style", old="query label leftover", new="label query invalid", fail_err="400: leftover query label leftover after label query invalid-only", plan="label query invalid-only 400s leftover query label leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (label query invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="label is path-only, leftover query label fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive label query ban 400 leftover query."),
     p(slug="leftover-query-label-style", domain="leftover-query-label-style-vs-oas-label-query-invalid", success=False, name="46a15e", stack="OpenAPI leftover style + Java + TS", field="style", old="label query invalid", new="query label leftover only", fail_err="400: leftover label query invalid after query label leftover-only", plan="query label leftover-only 400s leftover label query invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (query label leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive label query ban 400 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="label is path-only, leftover query label fails closed.")),
    (p(slug="oas-form-path-invalid", domain="oas-form-path-invalid-vs-leftover-path-form-style", success=True, name="21d23e", stack="OpenAPI 3.1 style + Go", field="style", old="path form leftover", new="form path invalid", fail_err="400: leftover path form leftover after form path invalid-only", plan="form path invalid-only 400s leftover path form leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (form path invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="form is not for path, leftover path form fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive form path ban 400 leftover path."),
     p(slug="leftover-path-form-style", domain="leftover-path-form-style-vs-oas-form-path-invalid", success=False, name="567779", stack="OpenAPI leftover style + Java + TS", field="style", old="form path invalid", new="path form leftover only", fail_err="400: leftover form path invalid after path form leftover-only", plan="path form leftover-only 400s leftover form path invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path form leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive form path ban 400 leftover path.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="form is not for path, leftover path form fails closed.")),
    (p(slug="oas-simple-query-invalid", domain="oas-simple-query-invalid-vs-leftover-query-simple-style", success=True, name="d96b4d", stack="OpenAPI 3.1 style + Go", field="style", old="query simple leftover", new="simple query invalid", fail_err="400: leftover query simple leftover after simple query invalid-only", plan="simple query invalid-only 400s leftover query simple leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (simple query invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="simple is path/header, leftover query simple fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive simple query ban 400 leftover query."),
     p(slug="leftover-query-simple-style", domain="leftover-query-simple-style-vs-oas-simple-query-invalid", success=False, name="56be66", stack="OpenAPI leftover style + Java + TS", field="style", old="simple query invalid", new="query simple leftover only", fail_err="400: leftover simple query invalid after query simple leftover-only", plan="query simple leftover-only 400s leftover simple query invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (query simple leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive simple query ban 400 leftover query.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="simple is path/header, leftover query simple fails closed.")),
    (p(slug="oas-space-path-invalid", domain="oas-space-path-invalid-vs-leftover-path-space-style", success=True, name="9844fd", stack="OpenAPI 3.1 style + Go", field="style", old="path space leftover", new="spaceDelimited path invalid", fail_err="400: leftover path space leftover after spaceDelimited path invalid-only", plan="spaceDelimited path invalid-only 400s leftover path space leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (spaceDelimited path invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="spaceDelimited is query, leftover path space fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive space path ban 400 leftover path."),
     p(slug="leftover-path-space-style", domain="leftover-path-space-style-vs-oas-space-path-invalid", success=False, name="9288bd", stack="OpenAPI leftover style + Java + TS", field="style", old="spaceDelimited path invalid", new="path space leftover only", fail_err="400: leftover spaceDelimited path invalid after path space leftover-only", plan="path space leftover-only 400s leftover spaceDelimited path invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path space leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive space path ban 400 leftover path.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="spaceDelimited is query, leftover path space fails closed.")),
    (p(slug="oas-pipe-path-invalid", domain="oas-pipe-path-invalid-vs-leftover-path-pipe-style", success=True, name="8f7322", stack="OpenAPI 3.1 style + Go", field="style", old="path pipe leftover", new="pipeDelimited path invalid", fail_err="400: leftover path pipe leftover after pipeDelimited path invalid-only", plan="pipeDelimited path invalid-only 400s leftover path pipe leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (pipeDelimited path invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="pipeDelimited is query, leftover path pipe fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive pipe path ban 400 leftover path."),
     p(slug="leftover-path-pipe-style", domain="leftover-path-pipe-style-vs-oas-pipe-path-invalid", success=False, name="4a5da5", stack="OpenAPI leftover style + Java + TS", field="style", old="pipeDelimited path invalid", new="path pipe leftover only", fail_err="400: leftover pipeDelimited path invalid after path pipe leftover-only", plan="path pipe leftover-only 400s leftover pipeDelimited path invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path pipe leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive pipe path ban 400 leftover path.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="pipeDelimited is query, leftover path pipe fails closed.")),
    (p(slug="oas-deepobject-path-invalid", domain="oas-deepobject-path-invalid-vs-leftover-path-deepobject", success=True, name="583a17", stack="OpenAPI 3.1 style + Go", field="style", old="path deepObject leftover", new="deepObject path invalid", fail_err="400: leftover path deepObject leftover after deepObject path invalid-only", plan="deepObject path invalid-only 400s leftover path deepObject leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (deepObject path invalid vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="deepObject is query, leftover path deepObject fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive deepObject path ban 400 leftover path."),
     p(slug="leftover-path-deepobject", domain="leftover-path-deepobject-vs-oas-deepobject-path-invalid", success=False, name="d1a034", stack="OpenAPI leftover style + Java + TS", field="style", old="deepObject path invalid", new="path deepObject leftover only", fail_err="400: leftover deepObject path invalid after path deepObject leftover-only", plan="path deepObject leftover-only 400s leftover deepObject path invalid. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path deepObject leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive deepObject path ban 400 leftover path.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="deepObject is query, leftover path deepObject fails closed.")),
    (p(slug="oas-content-on-path-param", domain="oas-content-on-path-param-vs-leftover-path-schema-only-forced", success=True, name="3be0fc", stack="OpenAPI 3.1 content + Go", field="content", old="schema only leftover", new="path param content", fail_err="400: leftover schema only leftover after path param content-only", plan="path param content-only 400s leftover schema only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (path param content vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="path params may use content, leftover schema-only-forced fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive path content 400 leftover schema only."),
     p(slug="leftover-path-schema-only-forced", domain="leftover-path-schema-only-forced-vs-oas-content-on-path-param", success=False, name="6d0cc5", stack="OpenAPI leftover content + Java + TS", field="content", old="path param content", new="schema only leftover only", fail_err="400: leftover path param content after schema only leftover-only", plan="schema only leftover-only 400s leftover path param content. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (schema only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive path content 400 leftover schema only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="path params may use content, leftover schema-only-forced fails closed.")),
    (p(slug="oas-client-creds-no-refresh", domain="oas-client-creds-no-refresh-vs-leftover-client-creds-refresh", success=True, name="c836b6", stack="OpenAPI 3.1 refreshUrl + Go", field="refreshUrl", old="client creds refresh leftover", new="clientCredentials no refresh", fail_err="401: leftover client creds refresh leftover after clientCredentials no refresh-only", plan="clientCredentials no refresh-only 401s leftover client creds refresh leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (clientCredentials no refresh vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="clientCredentials has no refresh, leftover refreshUrl fails closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749#section-4.4", fetch2_ok="Exclusive no refresh 401 leftover refresh."),
     p(slug="leftover-client-creds-refresh", domain="leftover-client-creds-refresh-vs-oas-client-creds-no-refresh", success=False, name="12cd4c", stack="OpenAPI leftover refreshUrl + Java + TS", field="refreshUrl", old="clientCredentials no refresh", new="client creds refresh leftover only", fail_err="401: leftover clientCredentials no refresh after client creds refresh leftover-only", plan="client creds refresh leftover-only 401s leftover clientCredentials no refresh. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (client creds refresh leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749#section-4.4", fetch1_ok="Exclusive no refresh 401 leftover refresh.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="clientCredentials has no refresh, leftover refreshUrl fails closed.")),
    (p(slug="oas-auth-code-offline-access", domain="oas-auth-code-offline-access-vs-leftover-auth-code-no-offline", success=True, name="bba0ca", stack="OpenAPI 3.1 offline_access + Go", field="offline_access", old="no offline leftover", new="offline_access scope", fail_err="401: leftover no offline leftover after offline_access scope-only", plan="offline_access scope-only 401s leftover no offline leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (offline_access scope vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6749", fetch1_ok="offline_access is required for refresh, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch2_ok="Exclusive offline_access 401 leftover none."),
     p(slug="leftover-auth-code-no-offline", domain="leftover-auth-code-no-offline-vs-oas-auth-code-offline-access", success=False, name="4753bb", stack="OpenAPI leftover offline_access + Java + TS", field="offline_access", old="offline_access scope", new="no offline leftover only", fail_err="401: leftover offline_access scope after no offline leftover-only", plan="no offline leftover-only 401s leftover offline_access scope. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (no offline leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oauth-flow-object", fetch1_ok="Exclusive offline_access 401 leftover none.", fetch2="https://datatracker.ietf.org/doc/html/rfc6749", fetch2_ok="offline_access is required for refresh, leftover missing fails closed.")),
    (p(slug="oas-global-security-empty-override", domain="oas-global-security-empty-override-vs-leftover-cannot-clear-global-sec", success=True, name="1a4da3", stack="OpenAPI 3.1 security + Go", field="security", old="cannot clear leftover", new="empty security override", fail_err="401: leftover cannot clear leftover after empty security override-only", plan="empty security override-only 401s leftover cannot clear leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (empty security override vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="empty security clears global, leftover cannot-clear fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch2_ok="Exclusive empty override 401 leftover sticky global."),
     p(slug="leftover-cannot-clear-global-sec", domain="leftover-cannot-clear-global-sec-vs-oas-global-security-empty-override", success=False, name="1cfeb6", stack="OpenAPI leftover security + Java + TS", field="security", old="empty security override", new="cannot clear leftover only", fail_err="401: leftover empty security override after cannot clear leftover-only", plan="cannot clear leftover-only 401s leftover empty security override. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (cannot clear leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#security-requirement-object", fetch1_ok="Exclusive empty override 401 leftover sticky global.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="empty security clears global, leftover cannot-clear fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4582"}))


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
