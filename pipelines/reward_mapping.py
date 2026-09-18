#!/usr/bin/env python3
"""Shared primitives for the reward-ontology mapping and runtime.

Field accessors, JSON-pointer helpers, and static vocabulary names live here so
policy validation and record classification can stay in smaller modules.
Contract parsers (units, vocabulary entries, finite numbers, hashes, and
arithmetic compatibility) are owned by ``reward_parse`` and re-exported.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("reward_mapping")
    from .exact_json import dumps_exact_json
    from . import reward_parse as _reward_parse
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_mapping"
    )
    from exact_json import dumps_exact_json
    import reward_parse as _reward_parse

ONTOLOGY_VERSION = "reward-ontology-v1"
# The classifier's own behavioral revision, recorded as the lane's declared
# transform_version. classifier-2: preference-scope routing follows
# ``_layout_scope`` exactly, so an episode-style ``/chosen/reward`` record is
# retained under the dedicated P01 verdict instead of raising. The ontology
# version above is the frozen mapping identity and must not move with
# classifier behavior; artifacts produced before and after a classifier
# change must not share one transform identity.
REWARD_TRANSFORM_VERSION = f"{ONTOLOGY_VERSION}.classifier-2"
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

ARITHMETIC_STATUSES = _reward_parse.ARITHMETIC_STATUSES
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

SHA256_RE = _reward_parse.SHA256_RE
RewardOntologyError = _reward_parse.RewardOntologyError
MagnitudeNotComparable = _reward_parse.MagnitudeNotComparable
_SHAPE_STATUS_METHODS = _reward_parse._SHAPE_STATUS_METHODS
_policy_error = _reward_parse._policy_error
_mapping_str = _reward_parse._mapping_str
_mapping_str_list = _reward_parse._mapping_str_list
_mapping_object = _reward_parse._mapping_object
_mapping_positive = _reward_parse._mapping_positive
_mapping_integer = _reward_parse._mapping_integer
_numeric_capture = _reward_parse._numeric_capture
_escape_signature_token = _reward_parse._escape_signature_token
_arithmetic_methods_for_signature = _reward_parse._arithmetic_methods_for_signature
_decimal = _reward_parse._decimal
_json_number = _reward_parse._json_number
_reject_nonfinite_numbers = _reward_parse._reject_nonfinite_numbers

_UNSET = object()
RUN_MANIFEST_FILENAME = "manifest.json"
RUN_SIDECAR_FILENAME = "reward-sidecars.jsonl"
RUN_CALIBRATION_FILENAME = "units-migration.json"


def _mapping_pattern(container, key, where, **options):
    """Preserve legacy keyword flags while grouping the canonical contract."""
    return _reward_parse._mapping_pattern(
        container, key, where, _reward_parse.PatternOptions(**options))


def _pointer_escape(token) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _pointer_unescape(token) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _pointer(tokens) -> str:
    return "/" + "/".join(_pointer_escape(token) for token in tokens)


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


def canonical_bytes(value) -> bytes:
    """Return the stable UTF-8 representation used by reward hashes."""

    return dumps_exact_json(
        value,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")


def _canonical_bytes(value) -> bytes:
    """Compatibility alias for callers predating the public hash surface."""

    return canonical_bytes(value)


def _sha256(value) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


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


if __package__:
    _expose_package_sibling(__name__)
