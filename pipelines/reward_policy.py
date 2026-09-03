#!/usr/bin/env python3
"""Fail-closed validation of the machine-readable reward conversion policy.

The mapping at ``schemas/reward-ontology-v1.mapping.json`` is loaded at import.
A missing, unreadable, or invalid mapping is a loud ``RewardOntologyError``.
"""

from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("reward_policy")
    from .reward_mapping import (
        COMPONENT_DISPOSITIONS,
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_NARRATIVE,
        DISPOSITION_UNIT_CALIBRATION,
        EXCLUDE,
        MAGNITUDE_COMPARABLE,
        MAPPING_PATH,
        MAPPING_VERSION,
        ONTOLOGY_VERSION,
        POLICY_DOCUMENT_TYPE,
        REQUIRED_ARITHMETIC_METHODS,
        REQUIRED_CLASSIFICATION_RULE_IDS,
        REQUIRED_RULE_COMPARABILITY,
        RULE_SCOPES,
        SIGN_ORDER_ONLY,
        RewardOntologyError,
        _mapping_object,
        _mapping_pattern,
        _mapping_positive,
        _mapping_str,
        _mapping_str_list,
        _pointer,
        _pointer_unescape,
        _policy_error,
    )
    from .reward_vocabulary import (
        _validate_expected_classification,
        _validate_source_vocabulary,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_policy"
    )
    from reward_mapping import (
        COMPONENT_DISPOSITIONS,
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_NARRATIVE,
        DISPOSITION_UNIT_CALIBRATION,
        EXCLUDE,
        MAGNITUDE_COMPARABLE,
        MAPPING_PATH,
        MAPPING_VERSION,
        ONTOLOGY_VERSION,
        POLICY_DOCUMENT_TYPE,
        REQUIRED_ARITHMETIC_METHODS,
        REQUIRED_CLASSIFICATION_RULE_IDS,
        REQUIRED_RULE_COMPARABILITY,
        RULE_SCOPES,
        SIGN_ORDER_ONLY,
        RewardOntologyError,
        _mapping_object,
        _mapping_pattern,
        _mapping_positive,
        _mapping_str,
        _mapping_str_list,
        _pointer,
        _pointer_unescape,
        _policy_error,
    )
    from reward_vocabulary import (
        _validate_expected_classification,
        _validate_source_vocabulary,
    )


def _validate_conversion_block(policy, where):
    conversion = _mapping_object(policy, "conversion", where)
    canonical_unit = _mapping_str(conversion, "canonical_unit", where)
    if canonical_unit != "usd_10000_risk_adjusted_delta":
        raise _policy_error(
            where, "canonical_unit must match the annotation schema constant"
        )
    canonical_unit_usd = _mapping_positive(conversion, "canonical_unit_usd", where)
    if canonical_unit_usd != Decimal("10000"):
        raise _policy_error(where, "canonical_unit_usd must be 10000")
    aggregation = _mapping_str(conversion, "aggregation", where)
    if aggregation != "linear_unit_conversion_only":
        raise _policy_error(
            where, "aggregation must match the annotation schema constant"
        )
    _mapping_str(conversion, "required_semantics_substring", where)
    structured = _mapping_str(conversion, "structured_unit_field", where)
    textual = _mapping_str(conversion, "text_unit_field", where)
    if structured == textual:
        raise _policy_error(where, "structured and textual unit fields must be distinct")
    _mapping_pattern(
        conversion, "usd_unit_pattern", where, groups=1, numeric_group=True
    )
    external = _mapping_object(conversion, "external_calibration", where)
    _mapping_pattern(external, "record_id_pattern", where, groups=0)
    factor_field = _mapping_str(external, "factor_field", where)
    scope_field = _mapping_str(external, "scope_field", where)
    if factor_field == scope_field:
        raise _policy_error(where, "external calibration fields must be distinct")
    return conversion


def _validate_weight_aliases(aliases, where):
    seen_aliases = set()
    for name in sorted(str(alias) for alias in aliases):
        members = _mapping_str_list(aliases, name, where)
        if name not in members:
            raise _policy_error(where, f"weight_aliases[{name!r}] must contain its own key")
        overlap = seen_aliases.intersection(members)
        if overlap:
            raise _policy_error(where, "weight alias groups must be disjoint")
        seen_aliases.update(members)
    return seen_aliases


def _validate_non_component_groups(groups, seen_aliases, arithmetic, where):
    expected_groups = {
        DISPOSITION_DECLARED_TOTAL,
        DISPOSITION_UNIT_CALIBRATION,
        DISPOSITION_NARRATIVE,
    }
    if set(groups) != expected_groups:
        raise _policy_error(
            where, f"non_component_keys must declare exactly {sorted(expected_groups)}"
        )
    seen = set()
    for name in sorted(groups):
        members = _mapping_str_list(groups, name, where)
        if seen & set(members):
            raise _policy_error(where, "non_component_keys groups must be disjoint")
        seen.update(members)
    if seen_aliases.intersection(seen):
        raise _policy_error(
            where, "weight aliases must not overlap non_component_keys"
        )
    if len(groups[DISPOSITION_DECLARED_TOTAL]) != 1:
        raise _policy_error(where, "non_component_keys.declared_total must name one key")
    if arithmetic["declared_total_field"] != groups[DISPOSITION_DECLARED_TOTAL][0]:
        raise _policy_error(
            where, "declared_total_field must match non_component_keys.declared_total"
        )
    for field in ("weights_field", "rounding_decimals_field"):
        if arithmetic[field] not in groups[DISPOSITION_UNIT_CALIBRATION]:
            raise _policy_error(
                where, f"{field} must be a declared unit_calibration key"
            )


def _validate_arithmetic_block(policy, where):
    arithmetic = _mapping_object(policy, "arithmetic", where)
    _mapping_positive(arithmetic, "default_tolerance", where)
    _mapping_str(arithmetic, "declared_total_field", where)
    _mapping_str(arithmetic, "weights_field", where)
    _mapping_str(arithmetic, "rounding_decimals_field", where)
    _mapping_pattern(
        arithmetic,
        "rounding_declaration_pattern",
        where,
        groups=1,
        numeric_group=True,
    )
    _mapping_str_list(arithmetic, "rounding_declaration_fields", where)
    containers = _mapping_str_list(arithmetic, "weighted_containers", where)
    nested = _mapping_str(arithmetic, "nested_component_key", where)
    if nested not in containers:
        raise _policy_error(where, "nested_component_key must be a declared weighted container")
    aliases = _mapping_object(arithmetic, "weight_aliases", where)
    seen_aliases = _validate_weight_aliases(aliases, where)
    groups = _mapping_object(arithmetic, "non_component_keys", where)
    _validate_non_component_groups(groups, seen_aliases, arithmetic, where)
    methods = _mapping_object(arithmetic, "methods", where)
    if not REQUIRED_ARITHMETIC_METHODS <= set(methods):
        missing = sorted(REQUIRED_ARITHMETIC_METHODS - set(methods))
        raise _policy_error(where, f"arithmetic.methods is missing {missing}")
    return arithmetic


def _validate_rule_calibration_codes(rule_id, codes, optional, comparability, where):
    if "external_calibration_evidence" in codes:
        raise _policy_error(
            where,
            "external_calibration_evidence is reserved for optional codes "
            "of externally calibrated routes",
        )
    if (
        "external_calibration_evidence" in optional
        and rule_id not in {"P05", "S08"}
    ):
        raise _policy_error(
            where,
            "external_calibration_evidence is reserved for optional codes "
            "of P05 and S08",
        )
    if comparability == MAGNITUDE_COMPARABLE and not (
        (set(codes) | set(optional))
        & {
            "explicit_usd_unit_calibration",
            "external_calibration_evidence",
        }
    ):
        raise _policy_error(
            where,
            f"rule {rule_id} must cite a magnitude calibration reason",
        )


def _validate_one_comparability_rule(rule, where, classes, reason_codes, seen_ids):
    if not isinstance(rule, dict):
        raise _policy_error(where, "each comparability rule must be an object")
    rule_id = _mapping_str(rule, "id", where)
    if rule_id in seen_ids:
        raise _policy_error(where, f"duplicate comparability rule id {rule_id!r}")
    seen_ids.add(rule_id)
    _mapping_str(rule, "condition", where)
    scope = _mapping_str(rule, "scope", where)
    if scope not in RULE_SCOPES:
        raise _policy_error(where, f"rule {rule_id} declares unknown scope {scope!r}")
    comparability = _mapping_str(rule, "comparability", where)
    if comparability not in classes:
        raise _policy_error(
            where, f"rule {rule_id} declares unknown comparability {comparability!r}"
        )
    required_class = REQUIRED_RULE_COMPARABILITY.get(rule_id)
    if required_class is not None and comparability != required_class:
        raise _policy_error(
            where,
            f"rule {rule_id} must declare comparability {required_class!r}",
        )
    codes = _mapping_str_list(rule, "reason_codes", where)
    optional = ()
    if "optional_reason_codes" in rule:
        optional = _mapping_str_list(rule, "optional_reason_codes", where)
    unknown = sorted((set(codes) | set(optional)) - set(reason_codes))
    if unknown:
        raise _policy_error(where, f"rule {rule_id} cites uncatalogued reason codes {unknown}")
    _validate_rule_calibration_codes(rule_id, codes, optional, comparability, where)
    return set(codes) | set(optional)


def _validate_rule_block(policy, where, classes, reason_codes):
    rules = policy.get("comparability_rules")
    if not isinstance(rules, list) or not rules:
        raise _policy_error(where, "comparability_rules must be a nonempty list")
    seen_ids = set()
    covered = set()
    for rule in rules:
        covered.update(
            _validate_one_comparability_rule(
                rule, where, classes, reason_codes, seen_ids
            )
        )
    missing_runtime_rules = sorted(REQUIRED_CLASSIFICATION_RULE_IDS - seen_ids)
    if missing_runtime_rules:
        raise _policy_error(
            where,
            "comparability_rules is missing runtime-required ids "
            f"{missing_runtime_rules}",
        )
    orphans = sorted(set(reason_codes) - covered)
    if orphans:
        raise _policy_error(where, f"reason codes cited by no rule: {orphans}")
    return tuple(rules)

def _validate_policy_identity(document, where):
    if not isinstance(document, dict):
        raise _policy_error(where, "conversion policy must be an object")
    if document.get("document_type") != POLICY_DOCUMENT_TYPE:
        raise _policy_error(where, "unknown conversion policy document_type")
    if document.get("ontology_version") != ONTOLOGY_VERSION:
        raise _policy_error(where, "unknown reward ontology version")
    if document.get("mapping_version") != MAPPING_VERSION:
        raise _policy_error(where, "unknown reward mapping version")


def _validate_preference_pointer(pointer, label, reward_keys, where):
    segments = [
        _pointer_unescape(segment) for segment in pointer[1:].split("/")
    ]
    terminal = segments[-1]
    if terminal not in reward_keys:
        raise _policy_error(
            where, f"{label} pointer must target a declared reward key"
        )
    if any(segment in reward_keys for segment in segments[:-1]):
        raise _policy_error(
            where,
            f"{label} pointer must not contain a nested reward-key segment",
        )


def _validate_policy_scopes(policy, where):
    annotation_field = _mapping_str(policy, "annotation_field", where)
    reward_keys = _mapping_str_list(policy, "reward_keys", where)
    if annotation_field in reward_keys:
        raise _policy_error(where, "annotation_field must not be a declared reward key")
    canonical_scope = _mapping_str(policy, "canonical_scope", where, prefix="/")
    if not any(_pointer((key,)) == canonical_scope for key in reward_keys):
        raise _policy_error(where, "canonical_scope must name a declared reward key")
    preference = _mapping_object(policy, "preference_scope", where)
    preferred = _mapping_str(preference, "preferred", where, prefix="/")
    dispreferred = _mapping_str(preference, "dispreferred", where, prefix="/")
    if preferred == dispreferred:
        raise _policy_error(where, "preference pointers must be distinct")
    if preferred == canonical_scope or dispreferred == canonical_scope:
        raise _policy_error(where, "preference pointers must differ from canonical_scope")
    _validate_preference_pointer(preferred, "preferred", reward_keys, where)
    _validate_preference_pointer(dispreferred, "dispreferred", reward_keys, where)
    if _mapping_str(preference, "relation", where) != "preferred_gt_dispreferred":
        raise _policy_error(where, "unsupported preference relation")
    return reward_keys


def _validate_policy_conversion_link(arithmetic, conversion, where):
    calibration_keys = arithmetic["non_component_keys"][DISPOSITION_UNIT_CALIBRATION]
    for field in ("structured_unit_field", "text_unit_field"):
        if conversion[field] not in calibration_keys:
            raise _policy_error(where, f"conversion.{field} must be a unit_calibration key")
    substring = conversion["required_semantics_substring"]
    if substring != substring.lower():
        raise _policy_error(
            where, "conversion.required_semantics_substring must be lowercase"
        )
    if "risk_adjust" not in substring.replace("-", "_"):
        raise _policy_error(
            where,
            "required_semantics_substring must retain a risk-adjustment marker",
        )


def _validate_policy_catalogues(policy, where):
    dispositions = _mapping_object(policy, "component_dispositions", where)
    if set(dispositions) != set(COMPONENT_DISPOSITIONS):
        raise _policy_error(
            where, f"component_dispositions must declare exactly {sorted(COMPONENT_DISPOSITIONS)}"
        )
    classes = _mapping_object(policy, "comparability_classes", where)
    if set(classes) != {MAGNITUDE_COMPARABLE, SIGN_ORDER_ONLY, EXCLUDE}:
        raise _policy_error(where, "comparability_classes must declare exactly the three classes")
    reason_codes = _mapping_object(policy, "reason_codes", where)
    for code, description in sorted(reason_codes.items()):
        if not isinstance(description, str) or not description.strip():
            raise _policy_error(where, f"reason code {code!r} has no description")
    return classes, reason_codes


def validate_conversion_policy(document, *, where="conversion policy"):
    """Validate the machine-readable conversion policy and return it unchanged."""
    _validate_policy_identity(document, where)
    policy = _mapping_object(document, "policy", where)
    reward_keys = _validate_policy_scopes(policy, where)
    arithmetic = _validate_arithmetic_block(policy, where)
    conversion = _validate_conversion_block(policy, where)
    _validate_policy_conversion_link(arithmetic, conversion, where)
    classes, reason_codes = _validate_policy_catalogues(policy, where)
    _validate_rule_block(policy, where, classes, reason_codes)
    vocabulary = _validate_source_vocabulary(
        document, arithmetic, reward_keys, where
    )
    _validate_expected_classification(
        document, classes, reason_codes, vocabulary["run"], where
    )
    return document


def load_conversion_policy(path=None):
    """Read, validate, and return the machine-readable conversion policy."""
    path = Path(path) if path is not None else MAPPING_PATH
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RewardOntologyError(f"{path}: conversion policy is unreadable: {exc}") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RewardOntologyError(f"{path}: invalid conversion policy JSON: {exc}") from exc
    return validate_conversion_policy(document, where=str(path))


CONVERSION_POLICY = load_conversion_policy()
_POLICY = CONVERSION_POLICY["policy"]
_ARITHMETIC = _POLICY["arithmetic"]
_CONVERSION = _POLICY["conversion"]

ANNOTATION_FIELD = _POLICY["annotation_field"]
REWARD_KEYS = frozenset(_POLICY["reward_keys"])
CANONICAL_SCOPE = _POLICY["canonical_scope"]
PREFERENCE_POINTERS = (
    _POLICY["preference_scope"]["preferred"],
    _POLICY["preference_scope"]["dispreferred"],
)
PREFERENCE_RELATION = _POLICY["preference_scope"]["relation"]

DEFAULT_TOLERANCE = Decimal(str(_ARITHMETIC["default_tolerance"]))
WEIGHTS_FIELD = _ARITHMETIC["weights_field"]
ROUNDING_DECIMALS_FIELD = _ARITHMETIC["rounding_decimals_field"]
ROUNDING_RE = re.compile(_ARITHMETIC["rounding_declaration_pattern"], re.I)
ROUNDING_FIELDS = tuple(_ARITHMETIC["rounding_declaration_fields"])
WEIGHTED_CONTAINERS = tuple(_ARITHMETIC["weighted_containers"])
NESTED_COMPONENT_KEY = _ARITHMETIC["nested_component_key"]
WEIGHT_ALIASES = {
    name: tuple(aliases) for name, aliases in _ARITHMETIC["weight_aliases"].items()
}
_NON_COMPONENT_GROUPS = _ARITHMETIC["non_component_keys"]
DECLARED_TOTAL_KEY = _NON_COMPONENT_GROUPS[DISPOSITION_DECLARED_TOTAL][0]
CALIBRATION_KEYS = frozenset(_NON_COMPONENT_GROUPS[DISPOSITION_UNIT_CALIBRATION])
NARRATIVE_KEYS = frozenset(_NON_COMPONENT_GROUPS[DISPOSITION_NARRATIVE])
UNWEIGHTED_EXCLUDE = frozenset(
    {DECLARED_TOTAL_KEY} | set(CALIBRATION_KEYS) | set(NARRATIVE_KEYS)
)
ARITHMETIC_METHODS = frozenset(_ARITHMETIC["methods"])

CANONICAL_UNIT = _CONVERSION["canonical_unit"]
CANONICAL_UNIT_USD = Decimal(str(_CONVERSION["canonical_unit_usd"]))
MAGNITUDE_AGGREGATION = _CONVERSION["aggregation"]
REQUIRED_SEMANTICS = _CONVERSION["required_semantics_substring"]
STRUCTURED_UNIT_FIELD = _CONVERSION["structured_unit_field"]
TEXT_UNIT_FIELD = _CONVERSION["text_unit_field"]
USD_UNIT_RE = re.compile(_CONVERSION["usd_unit_pattern"], re.I)
_EXTERNAL = _CONVERSION["external_calibration"]
RECORD_ID_RE = re.compile(_EXTERNAL["record_id_pattern"], re.I)
MIGRATION_FACTOR_FIELD = _EXTERNAL["factor_field"]
MIGRATION_SCOPE_FIELD = _EXTERNAL["scope_field"]

COMPARABILITY_CLASSES = frozenset(_POLICY["comparability_classes"])
REASON_CODES = frozenset(_POLICY["reason_codes"])
COMPARABILITY_RULES = tuple(_POLICY["comparability_rules"])
SOURCE_VOCABULARY = CONVERSION_POLICY["source_vocabulary"]


if __package__:
    _expose_package_sibling(__name__)
