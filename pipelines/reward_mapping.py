#!/usr/bin/env python3
"""Shared primitives for the reward-ontology mapping and runtime.

Field accessors, JSON-pointer helpers, and static vocabulary names live here so
policy validation and record classification can stay in smaller modules.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ONTOLOGY_VERSION = "reward-ontology-v1"
MAPPING_VERSION = "reward-mapping-v1"
POLICY_DOCUMENT_TYPE = "reward_conversion_policy"
MAPPING_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "reward-ontology-v1.mapping.json"
)

MAGNITUDE_COMPARABLE = "magnitude_comparable"
SIGN_ORDER_ONLY = "sign_order_only"
EXCLUDE = "exclude_from_reward_training"

DISPOSITION_DECLARED_TOTAL = "declared_total"
DISPOSITION_UNIT_CALIBRATION = "unit_calibration"
DISPOSITION_NARRATIVE = "narrative_annotation"
DISPOSITION_CONTAINER = "component_container"
DISPOSITION_MAGNITUDE_TERM = "magnitude_term"
DISPOSITION_STRUCTURAL = "structural_context"
DISPOSITION_AMBIGUOUS = "ambiguous_preserve_only"
COMPONENT_DISPOSITIONS = (
    DISPOSITION_DECLARED_TOTAL,
    DISPOSITION_UNIT_CALIBRATION,
    DISPOSITION_NARRATIVE,
    DISPOSITION_CONTAINER,
    DISPOSITION_MAGNITUDE_TERM,
    DISPOSITION_STRUCTURAL,
    DISPOSITION_AMBIGUOUS,
)

VALUE_TYPES = frozenset(
    {
        "number",
        "value-object",
        "object",
        "array",
        "string",
        "boolean",
        "null",
        "unknown",
    }
)

ARITHMETIC_STATUSES = frozenset({"valid", "invalid", "unsupported"})
RULE_SCOPES = frozenset({"any", "preference", "single"})
REQUIRED_CLASSIFICATION_RULE_IDS = frozenset(
    {"R00"}
    | {f"P{index:02d}" for index in range(1, 9)}
    | {f"S{index:02d}" for index in range(1, 9)}
)
REQUIRED_RULE_COMPARABILITY = {
    "R00": EXCLUDE,
    "P01": EXCLUDE,
    "P02": EXCLUDE,
    "P03": EXCLUDE,
    "P04": EXCLUDE,
    "P05": MAGNITUDE_COMPARABLE,
    "P06": SIGN_ORDER_ONLY,
    "P07": SIGN_ORDER_ONLY,
    "P08": SIGN_ORDER_ONLY,
    "S01": EXCLUDE,
    "S02": EXCLUDE,
    "S03": EXCLUDE,
    "S04": EXCLUDE,
    "S05": EXCLUDE,
    "S06": EXCLUDE,
    "S07": EXCLUDE,
    "S08": MAGNITUDE_COMPARABLE,
}
REQUIRED_ARITHMETIC_METHODS = frozenset(
    {
        "declared_weighted_sum",
        "declared_weighted_sum_unresolved",
        "unweighted_component_sum",
        "unweighted_component_sum_unresolved",
        "no_numeric_total",
        "non_object_reward",
    }
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_UNSET = object()
RUN_MANIFEST_FILENAME = "manifest.json"
RUN_SIDECAR_FILENAME = "reward-sidecars.jsonl"
RUN_CALIBRATION_FILENAME = "units-migration.json"

_SHAPE_STATUS_METHODS = {
    "valid": {
        "declared_weighted_sum",
        "unweighted_component_sum",
    },
    "invalid": {
        "declared_weighted_sum",
        "unweighted_component_sum",
    },
    "unsupported": {
        "declared_weighted_sum_unresolved",
        "unweighted_component_sum_unresolved",
        "no_numeric_total",
        "non_object_reward",
    },
}


class RewardOntologyError(ValueError):
    """Raised when a reward document violates ontology-v1 invariants."""


class MagnitudeNotComparable(RewardOntologyError):
    """Raised when a caller asks an uncalibrated record for magnitudes."""


def _policy_error(where, message):
    return RewardOntologyError(f"{where}: {message}")


def _pointer_escape(token) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _pointer_unescape(token) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _pointer(tokens) -> str:
    return "/" + "/".join(_pointer_escape(token) for token in tokens)


def _mapping_str(container, key, where, *, prefix=None):
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _policy_error(where, f"{key} must be a nonempty string")
    if prefix is not None and not value.startswith(prefix):
        raise _policy_error(where, f"{key} must start with {prefix!r}")
    return value


def _mapping_str_list(container, key, where):
    value = container.get(key)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
        or len(set(value)) != len(value)
    ):
        raise _policy_error(where, f"{key} must be a unique nonempty list of strings")
    return tuple(value)


def _mapping_object(container, key, where):
    value = container.get(key)
    if not isinstance(value, dict) or not value:
        raise _policy_error(where, f"{key} must be a nonempty object")
    return value


def _mapping_positive(container, key, where):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _policy_error(where, f"{key} must be a number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise _policy_error(where, f"{key} must be a finite number") from exc
    if not number.is_finite() or number <= 0:
        raise _policy_error(where, f"{key} must be positive and finite")
    return number


def _mapping_integer(container, key, where, *, minimum=0):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "nonnegative" if minimum == 0 else f">= {minimum}"
        raise _policy_error(where, f"{key} must be an integer {qualifier}")
    return value


def _pattern_numeric_group(compiled, key, where):
    haystacks = (
        "rounded to 3-decimal 1 reward unit = USD 10,000.5 abc",
        "xyz",
        "rounded to xyz decimal",
    )
    saw_numeric = False
    for haystack in haystacks:
        match = compiled.search(haystack)
        if match is None:
            continue
        try:
            Decimal(str(match.group(1)).replace(",", ""))
        except (InvalidOperation, TypeError, IndexError, ArithmeticError) as exc:
            raise _policy_error(
                where, f"{key} capture group must be numeric"
            ) from exc
        saw_numeric = True
    if not saw_numeric:
        raise _policy_error(
            where, f"{key} capture group must match a numeric sample"
        )


def _mapping_pattern(container, key, where, *, groups=0, numeric_group=False):
    pattern = _mapping_str(container, key, where)
    try:
        compiled = re.compile(pattern, re.I)
    except re.error as exc:
        raise _policy_error(where, f"{key} is not a valid regular expression: {exc}") from exc
    if compiled.groups != groups:
        raise _policy_error(where, f"{key} must declare exactly {groups} capture group(s)")
    if numeric_group:
        _pattern_numeric_group(compiled, key, where)
    return compiled


def _numeric_capture(match, *, integer=False):
    try:
        token = str(match.group(1)).replace(",", "")
        value = int(token) if integer else Decimal(token)
    except (InvalidOperation, TypeError, ValueError, IndexError, ArithmeticError) as exc:
        raise RewardOntologyError("numeric regex capture is not a number") from exc
    return value


def _escape_signature_token(token):
    return str(token).replace("\\", "\\\\").replace("|", "\\|").replace(":", "\\:")


def _unescape_signature_token(token):
    out = []
    escaped = False
    for character in token:
        if escaped:
            out.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        else:
            out.append(character)
    if escaped:
        out.append("\\")
    return "".join(out)


def _split_signature(signature, separator):
    parts = []
    buf = []
    escaped = False
    for character in signature:
        if escaped:
            buf.append(character)
            escaped = False
            continue
        if character == "\\":
            buf.append(character)
            escaped = True
            continue
        if character == separator:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(character)
    parts.append("".join(buf))
    return parts


def _signature_members(signature, where):
    members = {}
    for part in _split_signature(signature, "|"):
        pieces = _split_signature(part, ":")
        if len(pieces) != 2:
            raise _policy_error(where, "signature contains an invalid member")
        key = _unescape_signature_token(pieces[0])
        member_type = _unescape_signature_token(pieces[1])
        if not member_type or key in members:
            raise _policy_error(where, "signature contains an invalid member")
        members[key] = member_type
    return members


def _arithmetic_methods_for_signature(signature, arithmetic, where):
    """Return the arithmetic methods the structural signature can select."""
    if signature == "":
        return frozenset({"no_numeric_total"})
    if ":" not in signature:
        return frozenset({"non_object_reward"})

    members = _signature_members(signature, where)
    total_type = members.get(arithmetic["declared_total_field"])
    if total_type not in {"int", "float"}:
        return frozenset({"no_numeric_total"})
    if members.get(arithmetic["weights_field"]) == "object":
        return frozenset(
            {"declared_weighted_sum", "declared_weighted_sum_unresolved"}
        )
    return frozenset(
        {"unweighted_component_sum", "unweighted_component_sum_unresolved"}
    )


def _policy_disposition(key, observed_types, arithmetic):
    groups = arithmetic["non_component_keys"]
    if key == arithmetic["declared_total_field"]:
        return DISPOSITION_DECLARED_TOTAL
    if key in groups[DISPOSITION_UNIT_CALIBRATION]:
        return DISPOSITION_UNIT_CALIBRATION
    if key in groups[DISPOSITION_NARRATIVE]:
        return DISPOSITION_NARRATIVE
    types = set(observed_types)
    if types <= {"number", "value-object"}:
        return DISPOSITION_MAGNITUDE_TERM
    if types == {"string"}:
        return DISPOSITION_NARRATIVE
    if types == {"object"}:
        return (
            DISPOSITION_CONTAINER
            if key in arithmetic["weighted_containers"]
            else DISPOSITION_STRUCTURAL
        )
    if types <= {"object", "array"}:
        return DISPOSITION_STRUCTURAL
    return DISPOSITION_AMBIGUOUS


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _json_number(value: Decimal) -> float:
    return float(value)


def _reject_nonfinite_numbers(value, *, where):
    if isinstance(value, float) and not math.isfinite(value):
        raise RewardOntologyError(f"{where}: non-finite JSON number")
    if isinstance(value, dict):
        for child in value.values():
            _reject_nonfinite_numbers(child, where=where)
    elif isinstance(value, list):
        for child in value:
            _reject_nonfinite_numbers(child, where=where)


def _canonical_record_id(record):
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    value = meta.get("id") if isinstance(meta, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


canonical_source_record_id = _canonical_record_id
