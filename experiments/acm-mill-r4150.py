#!/usr/bin/env python3
"""Tenth unique OpenAPI-drift ACM catalog after r4134 mill. Fast slug load."""
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
    (p(slug="oas-content-x-www-form", domain="oas-content-x-www-form-vs-leftover-json-body-form", success=True, name="xform", stack="OpenAPI 3.1 application/x-www-form-urlencoded + Go", field="content", old="json body leftover", new="form urlencoded", fail_err="415: leftover json body leftover after form urlencoded-only", plan="form-urlencoded-only 415s leftover json. Dual-read json for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-encoding-simple (form vs json leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="form-urlencoded is not leftover JSON.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="Exclusive form 415 leftover json."),
     p(slug="leftover-json-body-form", domain="leftover-json-body-form-vs-oas-content-x-www-form", success=False, name="jform", stack="OpenAPI leftover json body + Java + TS", field="content", old="form urlencoded", new="json body leftover only", fail_err="415: leftover form urlencoded after json body leftover-only", plan="Json-only 415s leftover form. Freeze form, spec json leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-encoding-style-form (json leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="Exclusive form 415 leftover json.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="form-urlencoded is not leftover JSON.")),
    (p(slug="oas-parameter-style-simple-path", domain="oas-parameter-style-simple-path-vs-leftover-csv-path", success=True, name="psimp", stack="OpenAPI 3.1 path style=simple + Go", field="style", old="csv path leftover", new="path simple style", fail_err="400: leftover csv path leftover after path simple style-only", plan="path-simple-only 400s leftover csv. Dual-read csv for one release.", residual="compat leftover; drop after window 5", vs="r4007 leftover-query-simple (path simple vs csv leftover, not query mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Path style=simple is the default.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive path simple 400 leftover csv."),
     p(slug="leftover-csv-path", domain="leftover-csv-path-vs-oas-parameter-style-simple-path", success=False, name="csvp", stack="OpenAPI leftover csv path + Java + TS", field="style", old="path simple style", new="csv path leftover only", fail_err="400: leftover path simple style after csv path leftover-only", plan="Csv-only 400s leftover path simple. Freeze simple, spec csv leftover.", residual="handoff: keep new or force leftover", vs="r4007 oas-parameter-style-label-query (csv leftover, not query label)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive path simple 400 leftover csv.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Path style=simple is the default.")),
    (p(slug="oas-operation-operationid-required", domain="oas-operation-operationid-required-vs-leftover-missing-opid", success=True, name="opidreq", stack="OpenAPI 3.1 operationId required + Go", field="operationId", old="missing opid leftover", new="operationId required", fail_err="400: leftover missing opid leftover after operationId required-only", plan="operationId-required-only 400s leftover missing. Dual-omit opid for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-dup-opid (required opid vs missing leftover, not dup mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="operationId is required for codegen.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch2_ok="Exclusive operationId 400 leftover missing."),
     p(slug="leftover-missing-opid", domain="leftover-missing-opid-vs-oas-operation-operationid-required", success=False, name="noopid", stack="OpenAPI leftover missing opid + Java + TS", field="operationId", old="operationId required", new="missing opid leftover only", fail_err="400: leftover operationId required after missing opid leftover-only", plan="Missing-only 400s leftover operationId. Freeze operationId, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-operation-operationid-unique (missing leftover, not unique mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields-8", fetch1_ok="Exclusive operationId 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="operationId is required for codegen.")),
    (p(slug="oas-response-200-required", domain="oas-response-200-required-vs-leftover-any-status", success=True, name="r200", stack="OpenAPI 3.1 200 response required + Go", field="200", old="any status leftover", new="200 response required", fail_err="400: leftover any status leftover after 200 response required-only", plan="200-required-only 400s leftover any-status. Dual-accept any for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-listed-status-only (200 vs any leftover, not default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch1_ok="A 200 response documents success.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch2_ok="Exclusive 200 400 leftover any-status."),
     p(slug="leftover-any-status", domain="leftover-any-status-vs-oas-response-200-required", success=False, name="anyst", stack="OpenAPI leftover any status + Java + TS", field="200", old="200 response required", new="any status leftover only", fail_err="400: leftover 200 response required after any status leftover-only", plan="Any-only 400s leftover 200. Freeze 200, spec any leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-response-default (any leftover, not default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#response-object", fetch1_ok="Exclusive 200 400 leftover any-status.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#responses-object", fetch2_ok="A 200 response documents success.")),
    (p(slug="oas-parameter-schema-type", domain="oas-parameter-schema-type-vs-leftover-untyped-query", success=True, name="ptype", stack="OpenAPI 3.1 parameter schema type + Go", field="type", old="untyped query leftover", new="parameter schema type", fail_err="400: leftover untyped query leftover after parameter schema type-only", plan="typed-param-only 400s leftover untyped. Dual-read untyped for one release.", residual="compat leftover; drop after window 5", vs="r4038 leftover-schema-only-param (typed vs untyped leftover, not content mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Parameter schema type is required.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive param type 400 leftover untyped."),
     p(slug="leftover-untyped-query", domain="leftover-untyped-query-vs-oas-parameter-schema-type", success=False, name="utq", stack="OpenAPI leftover untyped query + Java + TS", field="type", old="parameter schema type", new="untyped query leftover only", fail_err="400: leftover parameter schema type after untyped query leftover-only", plan="Untyped-only 400s leftover param type. Freeze type, spec untyped leftover.", residual="handoff: keep new or force leftover", vs="r4038 oas-parameter-content-json (untyped leftover, not content mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive param type 400 leftover untyped.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Parameter schema type is required.")),
    (p(slug="oas-openapi-version-31", domain="oas-openapi-version-31-vs-leftover-missing-openapi-version", success=True, name="oas31", stack="OpenAPI 3.1 openapi field + Go", field="openapi", old="missing version leftover", new="openapi 3.1.0", fail_err="400: leftover missing version leftover after openapi 3.1.0-only", plan="openapi-3.1-only 400s leftover missing. Dual-accept missing for one release.", residual="compat leftover; drop after window 5", vs="r3963 leftover-unversioned (openapi 3.1 vs missing leftover, not info.version mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch1_ok="openapi 3.1.0 is required.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive openapi 3.1 400 leftover missing."),
     p(slug="leftover-missing-openapi-version", domain="leftover-missing-openapi-version-vs-oas-openapi-version-31", success=False, name="nooas", stack="OpenAPI leftover missing version + Java + TS", field="openapi", old="openapi 3.1.0", new="missing version leftover only", fail_err="400: leftover openapi 3.1.0 after missing version leftover-only", plan="Missing-only 400s leftover openapi 3.1. Freeze 3.1, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r3963 oas-info-version-semver (missing leftover, not info.version mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Exclusive openapi 3.1 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#versions", fetch2_ok="openapi 3.1.0 is required.")),
    (p(slug="oas-paths-required", domain="oas-paths-required-vs-leftover-empty-paths", success=True, name="paths", stack="OpenAPI 3.1 paths required + Go", field="paths", old="empty paths leftover", new="paths required", fail_err="400: leftover empty paths leftover after paths required-only", plan="paths-required-only 400s leftover empty. Dual-accept empty for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-inline-pathitem (required paths vs empty leftover, not components.pathItems)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch1_ok="paths is required.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive paths 400 leftover empty."),
     p(slug="leftover-empty-paths", domain="leftover-empty-paths-vs-oas-paths-required", success=False, name="nopath", stack="OpenAPI leftover empty paths + Java + TS", field="paths", old="paths required", new="empty paths leftover only", fail_err="400: leftover paths required after empty paths leftover-only", plan="Empty-only 400s leftover paths. Freeze paths, spec empty leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-components-path-items (empty leftover, not components mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Exclusive paths 400 leftover empty.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#paths-object", fetch2_ok="paths is required.")),
    (p(slug="oas-info-required", domain="oas-info-required-vs-leftover-missing-info", success=True, name="inforeq", stack="OpenAPI 3.1 info required + Go", field="info", old="missing info leftover", new="info required", fail_err="400: leftover missing info leftover after info required-only", plan="info-required-only 400s leftover missing. Dual-omit info for one release.", residual="compat leftover; drop after window 5", vs="r4007 leftover-missing-info-summary (info vs missing leftover, not summary mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch1_ok="info is required.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch2_ok="Exclusive info 400 leftover missing."),
     p(slug="leftover-missing-info", domain="leftover-missing-info-vs-oas-info-required", success=False, name="noinfo", stack="OpenAPI leftover missing info + Java + TS", field="info", old="info required", new="missing info leftover only", fail_err="400: leftover info required after missing info leftover-only", plan="Missing-only 400s leftover info. Freeze info, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r4007 oas-info-summary-required (missing leftover, not summary mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#fixed-fields", fetch1_ok="Exclusive info 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#info-object", fetch2_ok="info is required.")),
    (p(slug="oas-servers-absolute-url", domain="oas-servers-absolute-url-vs-leftover-relative-server", success=True, name="absurl", stack="OpenAPI 3.1 absolute server url + Go", field="url", old="relative server leftover", new="absolute server url", fail_err="400: leftover relative server leftover after absolute server url-only", plan="absolute-server-only 400s leftover relative. Dual-read relative for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-missing-server-var-default (absolute vs relative leftover, not default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Server url SHOULD be absolute.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="Exclusive absolute server 400 leftover relative."),
     p(slug="leftover-relative-server", domain="leftover-relative-server-vs-oas-servers-absolute-url", success=False, name="relsrv", stack="OpenAPI leftover relative server + Java + TS", field="url", old="absolute server url", new="relative server leftover only", fail_err="400: leftover absolute server url after relative server leftover-only", plan="Relative-only 400s leftover absolute. Freeze absolute, spec relative leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-servers-variables-default-required (relative leftover, not default mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="Exclusive absolute server 400 leftover relative.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Server url SHOULD be absolute.")),
    (p(slug="oas-cookie-style-form", domain="oas-cookie-style-form-vs-leftover-cookie-explode", success=True, name="ckform", stack="OpenAPI 3.1 cookie style=form + Go", field="style", old="cookie explode leftover", new="cookie form style", fail_err="400: leftover cookie explode leftover after cookie form style-only", plan="cookie-form-only 400s leftover explode. Dual-read explode for one release.", residual="compat leftover; drop after window 5", vs="r4102 leftover-header-session (cookie form vs explode leftover, not header session)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch1_ok="Cookie style=form is the default.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="Exclusive cookie form 400 leftover explode."),
     p(slug="leftover-cookie-explode", domain="leftover-cookie-explode-vs-oas-cookie-style-form", success=False, name="ckexpl", stack="OpenAPI leftover cookie explode + Java + TS", field="style", old="cookie form style", new="cookie explode leftover only", fail_err="400: leftover cookie form style after cookie explode leftover-only", plan="Explode-only 400s leftover cookie form. Freeze form, spec explode leftover.", residual="handoff: keep new or force leftover", vs="r4102 oas-parameter-in-cookie (explode leftover, not cookie param mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="Exclusive cookie form 400 leftover explode.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#style-values", fetch2_ok="Cookie style=form is the default.")),
    (p(slug="oas-request-content-required", domain="oas-request-content-required-vs-leftover-missing-req-content", success=True, name="reqct", stack="OpenAPI 3.1 requestBody content required + Go", field="content", old="missing content leftover", new="requestBody content", fail_err="415: leftover missing content leftover after requestBody content-only", plan="requestBody-content-only 415s leftover missing. Dual-omit content for one release.", residual="compat leftover; drop after window 5", vs="r4102 leftover-inline-reqbody (content vs missing leftover, not ref mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch1_ok="content is required on Request Body Object.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="Exclusive request content 415 leftover missing."),
     p(slug="leftover-missing-req-content", domain="leftover-missing-req-content-vs-oas-request-content-required", success=False, name="noct", stack="OpenAPI leftover missing req content + Java + TS", field="content", old="requestBody content", new="missing content leftover only", fail_err="415: leftover requestBody content after missing content leftover-only", plan="Missing-only 415s leftover requestBody content. Freeze content, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r4102 oas-operation-requestbody-ref (missing leftover, not ref mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="Exclusive request content 415 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#request-body-object", fetch2_ok="content is required on Request Body Object.")),
    (p(slug="oas-global-tags-required", domain="oas-global-tags-required-vs-leftover-no-tag-list", success=True, name="gtags", stack="OpenAPI 3.1 global tags + Go", field="tags", old="no tag list leftover", new="global tags", fail_err="400: leftover no tag list leftover after global tags-only", plan="global-tags-only 400s leftover none. Dual-omit tags for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-name-only-tag (global tags vs none leftover, not tag desc mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasTags", fetch1_ok="root tags list documents tags.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch2_ok="Exclusive global tags 400 leftover none."),
     p(slug="leftover-no-tag-list", domain="leftover-no-tag-list-vs-oas-global-tags-required", success=False, name="notags", stack="OpenAPI leftover no tag list + Java + TS", field="tags", old="global tags", new="no tag list leftover only", fail_err="400: leftover global tags after no tag list leftover-only", plan="None-only 400s leftover global tags. Freeze tags, spec none leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-tag-description-req (no-list leftover, not tag desc mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#tag-object", fetch1_ok="Exclusive global tags 400 leftover none.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasTags", fetch2_ok="root tags list documents tags.")),
    (p(slug="oas-ref-siblings-allowed", domain="oas-ref-siblings-allowed-vs-leftover-ref-only", success=True, name="refsib", stack="OpenAPI 3.1 $ref siblings + Go", field="$ref", old="ref only leftover", new="ref siblings allowed", fail_err="400: leftover ref only leftover after ref siblings allowed-only", plan="ref-siblings-only 400s leftover ref-only. Dual-omit siblings for one release.", residual="compat leftover; drop after window 5", vs="r3561 ref-siblings-oas31 ($ref siblings vs ref-only leftover, not mill reuse)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#reference-object", fetch1_ok="OAS 3.1 allows sibling keywords beside $ref.", fetch2="https://json-schema.org/understanding-json-schema/structuring#dollarref", fetch2_ok="Exclusive $ref siblings 400 leftover ref-only."),
     p(slug="leftover-ref-only", domain="leftover-ref-only-vs-oas-ref-siblings-allowed", success=False, name="refonly", stack="OpenAPI leftover ref-only + Java + TS", field="$ref", old="ref siblings allowed", new="ref only leftover only", fail_err="400: leftover ref siblings allowed after ref only leftover-only", plan="Ref-only 400s leftover $ref siblings. Freeze siblings, spec ref leftover.", residual="handoff: keep new or force leftover", vs="r3561 ref-siblings-oas31 (ref-only leftover, not mill reuse)", fetch1="https://json-schema.org/understanding-json-schema/structuring#dollarref", fetch1_ok="Exclusive $ref siblings 400 leftover ref-only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#reference-object", fetch2_ok="OAS 3.1 allows sibling keywords beside $ref.")),
    (p(slug="oas-link-operationid-required", domain="oas-link-operationid-required-vs-leftover-missing-link-opid", success=True, name="lnkopid", stack="OpenAPI 3.1 link operationId required + Go", field="operationId", old="missing link opid leftover", new="link operationId", fail_err="400: leftover missing link opid leftover after link operationId-only", plan="link-operationId-only 400s leftover missing. Dual-omit opid for one release.", residual="compat leftover; drop after window 5", vs="r4070 leftover-opid-only-link (required link opid vs missing leftover, not operationRef mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch1_ok="operationId or operationRef is required on links.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch2_ok="Exclusive link operationId 400 leftover missing."),
     p(slug="leftover-missing-link-opid", domain="leftover-missing-link-opid-vs-oas-link-operationid-required", success=False, name="nolnkop", stack="OpenAPI leftover missing link opid + Java + TS", field="operationId", old="link operationId", new="missing link opid leftover only", fail_err="400: leftover link operationId after missing link opid leftover-only", plan="Missing-only 400s leftover link operationId. Freeze operationId, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r4070 oas-link-operation-ref (missing leftover, not operationRef mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#runtime-expressions", fetch1_ok="Exclusive link operationId 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#link-object", fetch2_ok="operationId or operationRef is required on links.")),
    (p(slug="oas-schema-type-integer", domain="oas-schema-type-integer-vs-leftover-number-only", success=True, name="typint", stack="OpenAPI 3.1 type=integer + Go", field="type", old="number only leftover", new="type integer", fail_err="400: leftover number only leftover after type integer-only", plan="type-integer-only 400s leftover number. Dual-read number for one release.", residual="compat leftover; drop after window 5", vs="r4134 leftover-js-unsafe-int (integer vs number leftover, not int64 mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/numeric#integer", fetch1_ok="type=integer rejects leftover JSON numbers with fractions.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive integer 400 leftover number."),
     p(slug="leftover-number-only", domain="leftover-number-only-vs-oas-schema-type-integer", success=False, name="numonly", stack="OpenAPI leftover number only + Java + TS", field="type", old="type integer", new="number only leftover only", fail_err="400: leftover type integer after number only leftover-only", plan="Number-only 400s leftover integer. Freeze integer, spec number leftover.", residual="handoff: keep new or force leftover", vs="r4134 oas-schema-format-int64 (number leftover, not int64 mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive integer 400 leftover number.", fetch2="https://json-schema.org/understanding-json-schema/reference/numeric#integer", fetch2_ok="type=integer rejects leftover JSON numbers with fractions.")),
    (p(slug="oas-servers-required", domain="oas-servers-required-vs-leftover-missing-servers", success=True, name="srvreq", stack="OpenAPI 3.1 servers required + Go", field="servers", old="missing servers leftover", new="servers required", fail_err="400: leftover missing servers leftover after servers required-only", plan="servers-required-only 400s leftover missing. Dual-omit servers for one release.", residual="compat leftover; drop after window 5", vs="r4054 leftover-http-server (required servers vs missing leftover, not https mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch1_ok="servers documents hosts, leftover missing fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch2_ok="Exclusive servers 400 leftover missing."),
     p(slug="leftover-missing-servers", domain="leftover-missing-servers-vs-oas-servers-required", success=False, name="nosrv", stack="OpenAPI leftover missing servers + Java + TS", field="servers", old="servers required", new="missing servers leftover only", fail_err="400: leftover servers required after missing servers leftover-only", plan="Missing-only 400s leftover servers. Freeze servers, spec missing leftover.", residual="handoff: keep new or force leftover", vs="r4054 oas-servers-https-only (missing leftover, not https mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#server-object", fetch1_ok="Exclusive servers 400 leftover missing.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#oasServers", fetch2_ok="servers documents hosts, leftover missing fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4150"}))


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
