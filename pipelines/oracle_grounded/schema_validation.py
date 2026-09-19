"""Small, stdlib-only JSON Schema validator for oracle-grounded records.

The repository publishes Draft 2020-12 schemas, but the runnable factory has a
stdlib-only contract.  Pulling in ``jsonschema`` just for the curation gate
would make validation depend on an optional environment package, so this
module implements the deliberately small keyword subset used by the checked-in
schemas.  A schema object carrying any keyword outside that subset (plus the
allowed annotations) is itself a finding from ``validate_record_schemas``, so
a future schema cannot silently weaken the gate by using an assertion this
validator does not enforce.
"""

import json
import math
from functools import lru_cache
from pathlib import Path

from . import schema_keywords as _schema_keywords
from .schema_values import _nonfinite_errors

_validate = _schema_keywords._validate
# Compatibility re-export: callers historically read the findings cap through
# this module before it moved into ``schema_keywords``.
MAX_SCHEMA_FINDINGS = _schema_keywords.MAX_SCHEMA_FINDINGS


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA_PATH = REPO_ROOT / "schemas" / "oracle-grounded-v1.schema.json"
FAMILY_SCHEMA_DIR = REPO_ROOT / "schemas" / "oracle-grounded"

# The assertion keywords ``_validate`` enforces, and the annotation keywords
# the checked-in schemas deliberately carry.  Any other keyword on a schema
# object would be an assertion this validator silently skips, so its presence
# is itself a finding: records must never validate against a weaker gate than
# the schema on disk declares.
ENFORCED_KEYWORDS = frozenset(
    (
        "$ref anyOf not const enum type minimum maximum exclusiveMinimum "
        "exclusiveMaximum minLength pattern minItems maxItems uniqueItems "
        "items minProperties required properties additionalProperties"
    ).split()
)
ANNOTATION_KEYWORDS = frozenset({"$schema", "$id", "$defs", "title", "description"})


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number {value!r}")


def _parse_finite_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


@lru_cache(maxsize=None)
def _load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(
            handle, parse_constant=_reject_constant, parse_float=_parse_finite_float
        )


def _schema_mapping_children(schema, path):
    for name in ("$defs", "properties"):
        members = schema.get(name)
        if isinstance(members, dict):
            yield from ((sub, f"{path}/{name}/{key}") for key, sub in members.items())


def _schema_children(schema, path):
    yield from _schema_mapping_children(schema, path)
    for name in ("items", "not", "additionalProperties"):
        if name not in schema:
            continue
        child = schema[name]
        if name == "additionalProperties" and isinstance(child, bool):
            continue
        yield child, f"{path}/{name}"
    options = schema.get("anyOf")
    if isinstance(options, list):
        yield from ((sub, f"{path}/anyOf/{index}") for index, sub in enumerate(options))


def _unsupported_keyword_errors(schema, path="#"):
    """Schema objects that carry keywords ``_validate`` does not enforce."""
    if not isinstance(schema, dict):
        return [f"schema at {path} must be an object; Boolean schemas are unsupported"]
    errors = []
    unknown = sorted(set(schema) - ENFORCED_KEYWORDS - ANNOTATION_KEYWORDS)
    if unknown:
        errors.append(
            f"schema object at {path} uses unenforced keywords: {', '.join(unknown)}"
        )
    for sub, child_path in _schema_children(schema, path):
        errors.extend(_unsupported_keyword_errors(sub, child_path))
    return errors


@lru_cache(maxsize=None)
def _schema_keyword_findings(path):
    """Cached whole-document keyword audit for one schema file."""
    return tuple(_unsupported_keyword_errors(_load_schema(path)))


def validate_record_schemas(instance, family, include_validation=True):
    """Return base- and family-schema findings for one record.

    ``build_record`` assesses a provisional envelope before its validation
    block exists.  In that one mode the base schema ignores only the
    ``validation`` property; all other required and family semantics still run.
    """
    findings = _nonfinite_errors(instance)
    findings.extend(f"base schema: {item}" for item in _document_findings(
        instance, BASE_SCHEMA_PATH, include_validation,
    ))
    scenario = instance.get('scenario')
    profile = scenario.get('profile') if isinstance(scenario, dict) else None
    if profile is not None:
        from .native_profiles import PROFILES
        if PROFILES.get(family) != profile:
            return findings + ['unsupported crate-native family/profile combination']
    family_path = FAMILY_SCHEMA_DIR / f"{profile or family}.schema.json"
    findings.extend(f"family schema: {item}" for item in _document_findings(instance, family_path))
    return findings


def _document_findings(instance, path, include_validation=True):
    findings = list(_schema_keyword_findings(str(path)))
    if findings:
        return findings
    schema = _load_schema(str(path))
    if not include_validation:
        schema = dict(schema)
        schema["required"] = [
            key for key in schema.get("required", ()) if key != "validation"]
        properties = dict(schema.get("properties", {}))
        # Provisional envelopes keep the validation key allowed without its completed shape.
        properties["validation"] = {"type": "object"}
        schema["properties"] = properties
    return _validate(instance, schema, schema, "$")
