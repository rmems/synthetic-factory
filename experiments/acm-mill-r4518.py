#!/usr/bin/env python3
"""Unique OpenAPI-drift ACM catalog r4518. Fast slug load."""
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
    (p(slug="oas-api-version-header", domain="oas-api-version-header-vs-leftover-version-in-path-only", success=True, name="ed9c91", stack="OpenAPI 3.1 API-Version + Go", field="API-Version", old="path version leftover", new="API-Version header", fail_err="400: leftover path version leftover after API-Version header-only", plan="API-Version header-only 400s leftover path version leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (API-Version header vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch1_ok="API-Version header is not leftover path-only versioning.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Exclusive version header 400 leftover path."),
     p(slug="leftover-version-in-path-only", domain="leftover-version-in-path-only-vs-oas-api-version-header", success=False, name="9d9928", stack="OpenAPI leftover API-Version + Java + TS", field="API-Version", old="API-Version header", new="path version leftover only", fail_err="400: leftover API-Version header after path version leftover-only", plan="path version leftover-only 400s leftover API-Version header. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (path version leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Exclusive version header 400 leftover path.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#parameter-object", fetch2_ok="API-Version header is not leftover path-only versioning.")),
    (p(slug="oas-media-type-profile", domain="oas-media-type-profile-vs-leftover-unprofiled-json", success=True, name="36ab5d", stack="OpenAPI 3.1 profile + Go", field="profile", old="unprofiled json leftover", new="media type profile", fail_err="400: leftover unprofiled json leftover after media type profile-only", plan="media type profile-only 400s leftover unprofiled json leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (media type profile vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch1_ok="profile parameter on JSON is not leftover unprofiled JSON.", fetch2="https://datatracker.ietf.org/doc/html/rfc6906", fetch2_ok="Exclusive profile 400 leftover unprofiled."),
     p(slug="leftover-unprofiled-json", domain="leftover-unprofiled-json-vs-oas-media-type-profile", success=False, name="bfece1", stack="OpenAPI leftover profile + Java + TS", field="profile", old="media type profile", new="unprofiled json leftover only", fail_err="400: leftover media type profile after unprofiled json leftover-only", plan="unprofiled json leftover-only 400s leftover media type profile. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unprofiled json leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6906", fetch1_ok="Exclusive profile 400 leftover unprofiled.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#media-type-object", fetch2_ok="profile parameter on JSON is not leftover unprofiled JSON.")),
    (p(slug="oas-schema-enum-empty-ban", domain="oas-schema-enum-empty-ban-vs-leftover-empty-enum-array", success=True, name="fa035f", stack="OpenAPI 3.1 enum + Go", field="enum", old="empty enum leftover", new="enum nonempty", fail_err="400: leftover empty enum leftover after enum nonempty-only", plan="enum nonempty-only 400s leftover empty enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (enum nonempty vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch1_ok="enum must be nonempty, leftover empty fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive nonempty enum 400 leftover empty."),
     p(slug="leftover-empty-enum-array", domain="leftover-empty-enum-array-vs-oas-schema-enum-empty-ban", success=False, name="1cd046", stack="OpenAPI leftover enum + Java + TS", field="enum", old="enum nonempty", new="empty enum leftover only", fail_err="400: leftover enum nonempty after empty enum leftover-only", plan="empty enum leftover-only 400s leftover enum nonempty. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (empty enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive nonempty enum 400 leftover empty.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#enumerated-values", fetch2_ok="enum must be nonempty, leftover empty fails closed.")),
    (p(slug="oas-format-uuid-version4", domain="oas-format-uuid-version4-vs-leftover-any-uuid-version", success=True, name="789788", stack="OpenAPI 3.1 format + Go", field="format", old="any uuid leftover", new="format uuid v4", fail_err="400: leftover any uuid leftover after format uuid v4-only", plan="format uuid v4-only 400s leftover any uuid leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format uuid v4 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch1_ok="format=uuid here is v4, leftover other versions fail closed.", fetch2="https://datatracker.ietf.org/doc/html/rfc4122", fetch2_ok="Exclusive uuid v4 400 leftover any."),
     p(slug="leftover-any-uuid-version", domain="leftover-any-uuid-version-vs-oas-format-uuid-version4", success=False, name="5b7d03", stack="OpenAPI leftover format + Java + TS", field="format", old="format uuid v4", new="any uuid leftover only", fail_err="400: leftover format uuid v4 after any uuid leftover-only", plan="any uuid leftover-only 400s leftover format uuid v4. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (any uuid leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc4122", fetch1_ok="Exclusive uuid v4 400 leftover any.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#uuid", fetch2_ok="format=uuid here is v4, leftover other versions fail closed.")),
    (p(slug="oas-iri-reference-relative", domain="oas-iri-reference-relative-vs-leftover-iri-absolute-only", success=True, name="a22a2d", stack="OpenAPI 3.1 format + Go", field="format", old="absolute iri leftover", new="format iri-reference", fail_err="400: leftover absolute iri leftover after format iri-reference-only", plan="format iri-reference-only 400s leftover absolute iri leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (format iri-reference vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="iri-reference allows relative, leftover absolute-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive iri-reference 400 leftover absolute."),
     p(slug="leftover-iri-absolute-only", domain="leftover-iri-absolute-only-vs-oas-iri-reference-relative", success=False, name="bf0c8a", stack="OpenAPI leftover format + Java + TS", field="format", old="format iri-reference", new="absolute iri leftover only", fail_err="400: leftover format iri-reference after absolute iri leftover-only", plan="absolute iri leftover-only 400s leftover format iri-reference. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (absolute iri leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive iri-reference 400 leftover absolute.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="iri-reference allows relative, leftover absolute-only fails closed.")),
    (p(slug="oas-idn-email-smtputf8", domain="oas-idn-email-smtputf8-vs-leftover-punycode-email-only", success=True, name="8f2e4b", stack="OpenAPI 3.1 format + Go", field="format", old="punycode email leftover", new="idn-email SMTPUTF8", fail_err="400: leftover punycode email leftover after idn-email SMTPUTF8-only", plan="idn-email SMTPUTF8-only 400s leftover punycode email leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (idn-email SMTPUTF8 vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch1_ok="idn-email is SMTPUTF8, leftover punycode-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive idn-email 400 leftover punycode."),
     p(slug="leftover-punycode-email-only", domain="leftover-punycode-email-only-vs-oas-idn-email-smtputf8", success=False, name="ec3e2e", stack="OpenAPI leftover format + Java + TS", field="format", old="idn-email SMTPUTF8", new="punycode email leftover only", fail_err="400: leftover idn-email SMTPUTF8 after punycode email leftover-only", plan="punycode email leftover-only 400s leftover idn-email SMTPUTF8. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (punycode email leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive idn-email 400 leftover punycode.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#resource-identifiers", fetch2_ok="idn-email is SMTPUTF8, leftover punycode-only fails closed.")),
    (p(slug="oas-ipv4-no-leading-zeros", domain="oas-ipv4-no-leading-zeros-vs-leftover-octal-ipv4", success=True, name="549b45", stack="OpenAPI 3.1 format + Go", field="format", old="octal ipv4 leftover", new="ipv4 no leading zeros", fail_err="400: leftover octal ipv4 leftover after ipv4 no leading zeros-only", plan="ipv4 no leading zeros-only 400s leftover octal ipv4 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (ipv4 no leading zeros vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#ipv4", fetch1_ok="format=ipv4 forbids leftover octal dotted quads.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive ipv4 400 leftover octal."),
     p(slug="leftover-octal-ipv4", domain="leftover-octal-ipv4-vs-oas-ipv4-no-leading-zeros", success=False, name="1fcbee", stack="OpenAPI leftover format + Java + TS", field="format", old="ipv4 no leading zeros", new="octal ipv4 leftover only", fail_err="400: leftover ipv4 no leading zeros after octal ipv4 leftover-only", plan="octal ipv4 leftover-only 400s leftover ipv4 no leading zeros. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (octal ipv4 leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive ipv4 400 leftover octal.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#ipv4", fetch2_ok="format=ipv4 forbids leftover octal dotted quads.")),
    (p(slug="oas-ipv6-compressed-ok", domain="oas-ipv6-compressed-ok-vs-leftover-full-ipv6-only", success=True, name="5daf13", stack="OpenAPI 3.1 format + Go", field="format", old="full ipv6 leftover", new="ipv6 compressed", fail_err="400: leftover full ipv6 leftover after ipv6 compressed-only", plan="ipv6 compressed-only 400s leftover full ipv6 leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (ipv6 compressed vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#ipv6", fetch1_ok="compressed IPv6 is valid, leftover full-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive compressed ipv6 400 leftover full."),
     p(slug="leftover-full-ipv6-only", domain="leftover-full-ipv6-only-vs-oas-ipv6-compressed-ok", success=False, name="19d939", stack="OpenAPI leftover format + Java + TS", field="format", old="ipv6 compressed", new="full ipv6 leftover only", fail_err="400: leftover ipv6 compressed after full ipv6 leftover-only", plan="full ipv6 leftover-only 400s leftover ipv6 compressed. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (full ipv6 leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive compressed ipv6 400 leftover full.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#ipv6", fetch2_ok="compressed IPv6 is valid, leftover full-only fails closed.")),
    (p(slug="oas-json-pointer-tilde-esc", domain="oas-json-pointer-tilde-esc-vs-leftover-unescaped-pointer", success=True, name="e74c8c", stack="OpenAPI 3.1 format + Go", field="format", old="unescaped pointer leftover", new="json-pointer tilde escape", fail_err="400: leftover unescaped pointer leftover after json-pointer tilde escape-only", plan="json-pointer tilde escape-only 400s leftover unescaped pointer leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (json-pointer tilde escape vs leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6901", fetch1_ok="JSON Pointer tilde-escapes, leftover unescaped fails closed.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch2_ok="Exclusive pointer escape 400 leftover unescaped."),
     p(slug="leftover-unescaped-pointer", domain="leftover-unescaped-pointer-vs-oas-json-pointer-tilde-esc", success=False, name="8c6008", stack="OpenAPI leftover format + Java + TS", field="format", old="json-pointer tilde escape", new="unescaped pointer leftover only", fail_err="400: leftover json-pointer tilde escape after unescaped pointer leftover-only", plan="unescaped pointer leftover-only 400s leftover json-pointer tilde escape. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (unescaped pointer leftover leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch1_ok="Exclusive pointer escape 400 leftover unescaped.", fetch2="https://datatracker.ietf.org/doc/html/rfc6901", fetch2_ok="JSON Pointer tilde-escapes, leftover unescaped fails closed.")),
    (p(slug="oas-relative-pointer-from", domain="oas-relative-pointer-from-vs-leftover-relative-from-root-only", success=True, name="89e339", stack="OpenAPI 3.1 format + Go", field="format", old="from root leftover", new="relative json-pointer", fail_err="400: leftover from root leftover after relative json-pointer-only", plan="relative json-pointer-only 400s leftover from root leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (relative json-pointer vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch1_ok="relative JSON pointer is not leftover from-root only.", fetch2="https://datatracker.ietf.org/doc/html/rfc6901", fetch2_ok="Exclusive relative pointer 400 leftover root."),
     p(slug="leftover-relative-from-root-only", domain="leftover-relative-from-root-only-vs-oas-relative-pointer-from", success=False, name="cae7c4", stack="OpenAPI leftover format + Java + TS", field="format", old="relative json-pointer", new="from root leftover only", fail_err="400: leftover relative json-pointer after from root leftover-only", plan="from root leftover-only 400s leftover relative json-pointer. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (from root leftover leftover, not encoding mill)", fetch1="https://datatracker.ietf.org/doc/html/rfc6901", fetch1_ok="Exclusive relative pointer 400 leftover root.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#json-pointer", fetch2_ok="relative JSON pointer is not leftover from-root only.")),
    (p(slug="oas-format-duration-weeks", domain="oas-format-duration-weeks-vs-leftover-duration-days-only", success=True, name="9f217c", stack="OpenAPI 3.1 format + Go", field="format", old="days only leftover", new="duration weeks", fail_err="400: leftover days only leftover after duration weeks-only", plan="duration weeks-only 400s leftover days only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (duration weeks vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch1_ok="duration may use weeks, leftover days-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive duration weeks 400 leftover days."),
     p(slug="leftover-duration-days-only", domain="leftover-duration-days-only-vs-oas-format-duration-weeks", success=False, name="64d350", stack="OpenAPI leftover format + Java + TS", field="format", old="duration weeks", new="days only leftover only", fail_err="400: leftover duration weeks after days only leftover-only", plan="days only leftover-only 400s leftover duration weeks. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (days only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive duration weeks 400 leftover days.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#dates-and-times", fetch2_ok="duration may use weeks, leftover days-only fails closed.")),
    (p(slug="oas-hostname-no-trailing-dot", domain="oas-hostname-no-trailing-dot-vs-leftover-fqdn-trailing-dot", success=True, name="9c9f9b", stack="OpenAPI 3.1 format + Go", field="format", old="trailing dot leftover", new="hostname no trailing dot", fail_err="400: leftover trailing dot leftover after hostname no trailing dot-only", plan="hostname no trailing dot-only 400s leftover trailing dot leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (hostname no trailing dot vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch1_ok="format=hostname forbids leftover trailing dots.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive hostname 400 leftover trailing dot."),
     p(slug="leftover-fqdn-trailing-dot", domain="leftover-fqdn-trailing-dot-vs-oas-hostname-no-trailing-dot", success=False, name="cc1caf", stack="OpenAPI leftover format + Java + TS", field="format", old="hostname no trailing dot", new="trailing dot leftover only", fail_err="400: leftover hostname no trailing dot after trailing dot leftover-only", plan="trailing dot leftover-only 400s leftover hostname no trailing dot. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (trailing dot leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive hostname 400 leftover trailing dot.", fetch2="https://json-schema.org/understanding-json-schema/reference/string#hostname", fetch2_ok="format=hostname forbids leftover trailing dots.")),
    (p(slug="oas-type-null-only", domain="oas-type-null-only-vs-leftover-skip-null-type", success=True, name="50e7c5", stack="OpenAPI 3.1 type + Go", field="type", old="skip null leftover", new="type null", fail_err="400: leftover skip null leftover after type null-only", plan="type null-only 400s leftover skip null leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (type null vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/null", fetch1_ok="type=null is a real type, leftover skip-null fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch2_ok="Exclusive type null 400 leftover skip."),
     p(slug="leftover-skip-null-type", domain="leftover-skip-null-type-vs-oas-type-null-only", success=False, name="6feffa", stack="OpenAPI leftover type + Java + TS", field="type", old="type null", new="skip null leftover only", fail_err="400: leftover type null after skip null leftover-only", plan="skip null leftover-only 400s leftover type null. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (skip null leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#data-types", fetch1_ok="Exclusive type null 400 leftover skip.", fetch2="https://json-schema.org/understanding-json-schema/reference/null", fetch2_ok="type=null is a real type, leftover skip-null fails closed.")),
    (p(slug="oas-const-enum-agree", domain="oas-const-enum-agree-vs-leftover-const-outside-enum", success=True, name="b4786d", stack="OpenAPI 3.1 const + Go", field="const", old="const outside enum leftover", new="const in enum", fail_err="400: leftover const outside enum leftover after const in enum-only", plan="const in enum-only 400s leftover const outside enum leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (const in enum vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch1_ok="const must be in enum when both exist, leftover outside fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive const in enum 400 leftover outside."),
     p(slug="leftover-const-outside-enum", domain="leftover-const-outside-enum-vs-oas-const-enum-agree", success=False, name="7069d8", stack="OpenAPI leftover const + Java + TS", field="const", old="const in enum", new="const outside enum leftover only", fail_err="400: leftover const in enum after const outside enum leftover-only", plan="const outside enum leftover-only 400s leftover const in enum. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (const outside enum leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive const in enum 400 leftover outside.", fetch2="https://json-schema.org/understanding-json-schema/reference/generic#const", fetch2_ok="const must be in enum when both exist, leftover outside fails closed.")),
    (p(slug="oas-required-minitems-agree", domain="oas-required-minitems-agree-vs-leftover-required-empty-array", success=True, name="2ddb53", stack="OpenAPI 3.1 minItems + Go", field="minItems", old="required empty leftover", new="required minItems agree", fail_err="400: leftover required empty leftover after required minItems agree-only", plan="required minItems agree-only 400s leftover required empty leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (required minItems agree vs leftover, not encoding mill)", fetch1="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch1_ok="required arrays still honor minItems, leftover empty fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch2_ok="Exclusive minItems 400 leftover empty required."),
     p(slug="leftover-required-empty-array", domain="leftover-required-empty-array-vs-oas-required-minitems-agree", success=False, name="0d0bd1", stack="OpenAPI leftover minItems + Java + TS", field="minItems", old="required minItems agree", new="required empty leftover only", fail_err="400: leftover required minItems agree after required empty leftover-only", plan="required empty leftover-only 400s leftover required minItems agree. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (required empty leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#schema-object", fetch1_ok="Exclusive minItems 400 leftover empty required.", fetch2="https://json-schema.org/understanding-json-schema/reference/array#minitems", fetch2_ok="required arrays still honor minItems, leftover empty fails closed.")),
    (p(slug="oas-sunset-link-header", domain="oas-sunset-link-header-vs-leftover-sunset-header-only", success=True, name="8077f1", stack="OpenAPI 3.1 Link + Go", field="Link", old="sunset header only leftover", new="Sunset plus Link", fail_err="400: leftover sunset header only leftover after Sunset plus Link-only", plan="Sunset plus Link-only 400s leftover sunset header only leftover. Dual-read leftover for one release.", residual="compat leftover; drop after window 5", vs="r4214 leftover-encoding-csv (Sunset plus Link vs leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch1_ok="Sunset should pair with Link, leftover header-only fails closed.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch2_ok="Exclusive Sunset+Link 400 leftover header only."),
     p(slug="leftover-sunset-header-only", domain="leftover-sunset-header-only-vs-oas-sunset-link-header", success=False, name="ea5337", stack="OpenAPI leftover Link + Java + TS", field="Link", old="Sunset plus Link", new="sunset header only leftover only", fail_err="400: leftover Sunset plus Link after sunset header only leftover-only", plan="sunset header only leftover-only 400s leftover Sunset plus Link. Freeze new, spec leftover.", residual="handoff: keep new or force leftover", vs="r4214 oas-encoding-style-pipe (sunset header only leftover leftover, not encoding mill)", fetch1="https://spec.openapis.org/oas/v3.1.0.html#operation-object", fetch1_ok="Exclusive Sunset+Link 400 leftover header only.", fetch2="https://spec.openapis.org/oas/v3.1.0.html#header-object", fetch2_ok="Sunset should pair with Link, leftover header-only fails closed.")),
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
    print(json.dumps({"round": round_n, "idx": idx, "ids": [e1["id"], e2["id"]], "catalog": "r4518"}))


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
