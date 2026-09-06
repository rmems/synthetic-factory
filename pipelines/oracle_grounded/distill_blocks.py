#!/usr/bin/env python3
"""Envelope shape checks for the distillation contract (issue #78).

One check per record block -- generator, oracle, result, provenance,
validation -- plus the generator/oracle separation rule and the content
digest. :func:`check_envelope` composes them, in the order their findings
have always been emitted, with the measurement checks that live in
``distill_measurements`` and the energy rule in ``distill_energy_claims``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from . import distill_energy_claims as energy_claims
from . import distill_measurements as measurements
from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


# A field rule: the key, the predicate its value must satisfy, and the message
# template that ``{where}`` and ``{value}`` fill in. A predicate sees
# ``_ABSENT`` for a missing key, so a rule can insist on presence, tolerate
# absence, or tolerate null while a presence rule reports the absence.
_ABSENT = object()
Rule = tuple[str, Callable[[Any], bool], str]


def _rule_errors(block: dict[str, Any], rules: Iterable[Rule], where: str) -> list[str]:
    """The message of every rule ``block`` fails, in rule order."""

    return [
        message.format(where=where, value=block.get(key))
        for key, holds, message in rules
        if not holds(block.get(key, _ABSENT))
    ]


def _is_string(value: Any) -> bool:
    return not vocab.missing_string(value)


def _is_text(value: Any) -> bool:
    return isinstance(value, str)


def _is_object(value: Any) -> bool:
    return isinstance(value, dict)


def _is_nonempty_object(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(envelope.SHA256_RE.match(value))


def _is_confidence(value: Any) -> bool:
    """A number in [0, 1], as the schema pins ``candidate_prediction.confidence``."""

    return envelope.is_number(value) and 0 <= value <= 1


def _is_schema_version(value: Any) -> bool:
    return value == vocab.SCHEMA_VERSION


def _is_generator_authority(value: Any) -> bool:
    return value == vocab.GENERATOR_AUTHORITY


def _present(value: Any) -> bool:
    return value is not _ABSENT


def _one_of(values: frozenset[str]) -> Callable[[Any], bool]:
    return lambda value: envelope.is_enum_value(value, values)


def _absent_or(holds: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """Tolerate a missing key; judge a present value by ``holds``."""

    return lambda value: value is _ABSENT or holds(value)


def _null_or(holds: Callable[[Any], bool]) -> Callable[[Any], bool]:
    """Tolerate null, and absence (a presence rule reports that); judge the rest."""

    return lambda value: value is _ABSENT or value is None or holds(value)


# The shared envelope restricts a seed to integer/null and a commit to
# string/null. Presence alone once accepted ``{"seed": {}}`` and ``"seed":
# true``, so malformed reproducibility metadata stayed curation-eligible.
def _seed_rules(section: str, absent_note: str) -> tuple[Rule, Rule]:
    return (
        ("seed", _present, "{where}." + section + ".seed must be present (" + absent_note + ")"),
        (
            "seed",
            _null_or(vocab.is_genuine_int),
            "{where}." + section + ".seed must be an integer or null, got {value!r}",
        ),
    )


_HEADER_RULES: tuple[Rule, ...] = (
    ("id", _is_string, "{where}.id must be a non-empty string"),
    ("family", _one_of(vocab.FAMILIES), "{where}.family must be one of " + str(sorted(vocab.FAMILIES))),
    (
        "schema_version",
        _is_schema_version,
        "{where}.schema_version must be " + repr(vocab.SCHEMA_VERSION) + ", got {value!r}",
    ),
    ("scenario", _is_nonempty_object, "{where}.scenario must be a non-empty object"),
    # Must be objects, not lists: the predicted_* naming rule is only
    # expressible over named keys, so a list would slip past it.
    ("intervention", _absent_or(_is_object), "{where}.intervention must be an object"),
    (
        "candidate_prediction",
        _absent_or(_is_object),
        "{where}.candidate_prediction must be an object",
    ),
)

_GENERATOR_RULES: tuple[Rule, ...] = (
    ("name", _is_string, "{where}.generator.name must be a non-empty string"),
    (
        "kind",
        _one_of(vocab.GENERATOR_KINDS),
        "{where}.generator.kind must be one of " + str(sorted(vocab.GENERATOR_KINDS)),
    ),
    ("version", _is_string, "{where}.generator.version must be a non-empty string"),
    (
        "authority",
        _is_generator_authority,
        "{where}.generator.authority must be " + repr(vocab.GENERATOR_AUTHORITY)
        + " — a generator may never certify its own result",
    ),
) + _seed_rules("generator", "null when unseeded")

_ORACLE_RULES: tuple[Rule, ...] = (
    ("name", _is_string, "{where}.oracle.name must be a non-empty string"),
    (
        "type",
        _one_of(vocab.ORACLE_TYPES),
        "{where}.oracle.type must be one of " + str(sorted(vocab.ORACLE_TYPES)),
    ),
    ("implementation", _is_string, "{where}.oracle.implementation must be a non-empty string"),
    ("version", _is_string, "{where}.oracle.version must be a non-empty string"),
    (
        "authority",
        _one_of(vocab.ORACLE_AUTHORITIES),
        "{where}.oracle.authority must be one of " + str(sorted(vocab.ORACLE_AUTHORITIES)),
    ),
    ("configuration", _is_object, "{where}.oracle.configuration must be an object"),
) + _seed_rules("oracle", "null when n/a") + (
    ("commit", _present, "{where}.oracle.commit must be present (null when n/a)"),
    ("commit", _null_or(_is_text), "{where}.oracle.commit must be a string or null, got {value!r}"),
)

_PROVENANCE_RULES: tuple[Rule, ...] = (
    ("producer", _is_string, "{where}.provenance.producer must be a non-empty string"),
    (
        "produced_at",
        vocab.is_timestamp,
        "{where}.provenance.produced_at must be an ISO-8601 UTC timestamp",
    ),
    # Required, not optional. If the digest may be absent, deleting it is all
    # it takes to switch off tamper detection for the whole record.
    ("record_sha256", _is_sha256, "{where}.provenance.record_sha256 must be a sha256 hex digest"),
)

_VALIDATOR_RULES: tuple[Rule, ...] = (
    ("name", _is_string, "{where}.validation.validator.name must be a non-empty string"),
    ("version", _is_string, "{where}.validation.validator.version must be a non-empty string"),
    (
        "checked_at",
        vocab.is_timestamp,
        "{where}.validation.validator.checked_at must be an ISO-8601 UTC timestamp",
    ),
    (
        "validated_digest",
        _null_or(_is_sha256),
        "{where}.validation.validator.validated_digest must be a sha256 digest",
    ),
)

# The free keys of candidate_prediction keep the schema's types.
_PREDICTION_FIELD_RULES: tuple[Rule, ...] = (
    (
        "confidence",
        _absent_or(_is_confidence),
        "{where}.candidate_prediction.confidence must be a number in [0, 1], got {value!r}",
    ),
    ("rationale", _absent_or(_is_text), "{where}.candidate_prediction.rationale must be a string"),
    ("method", _absent_or(_is_text), "{where}.candidate_prediction.method must be a string"),
)


def check_generator_oracle_separation(record: dict[str, Any], where: str) -> list[str]:
    """Reject oracle-owned keys hiding inside generator-owned namespaces.

    The reserved-key scan is the envelope's bounded walker over this
    contract's ``ORACLE_ONLY_KEYS``: one finding per record listing the paths
    it found, capped at ``envelope.MAX_RESERVED_KEY_HITS``. The ``predicted_*``
    naming rule for ``candidate_prediction`` is a distillation rule and runs
    here, after the shared scan.
    """

    try:
        errors = envelope.check_generator_oracle_separation(
            record, vocab.ORACLE_ONLY_KEYS, where
        )
    except RecursionError:
        # The shared walker recurses; a record nested past the limit is a
        # finding at this boundary, never an exception out of a check.
        return [vocab.scan_depth_finding(where)]
    return errors + _check_prediction_naming(record.get("candidate_prediction"), where)


def _check_prediction_naming(prediction: Any, where: str) -> list[str]:
    """A generator guess must be ``predicted_*`` (or one of the free keys)."""

    if not isinstance(prediction, dict):
        return []
    errors = [
        f"{where}.candidate_prediction.{key}: generator predictions must be "
        f"named {vocab.PREDICTION_PREFIX}* (or one of "
        f"{sorted(vocab.PREDICTION_FREE_KEYS)})"
        for key in sorted(_string_keys(prediction))
        if key not in vocab.PREDICTION_FREE_KEYS
        and not key.startswith(vocab.PREDICTION_PREFIX)
    ]
    return (
        _prediction_key_errors(prediction, where)
        + errors
        + _rule_errors(prediction, _PREDICTION_FIELD_RULES, where)
    )


def _string_keys(mapping: dict[Any, Any]) -> list[str]:
    return [key for key in mapping if isinstance(key, str)]


def _prediction_key_errors(prediction: dict[Any, Any], where: str) -> list[str]:
    """A JSON object cannot carry a non-string key; a direct caller's mapping can."""

    return [
        f"{where}.candidate_prediction: every key must be a string, got {key!r}"
        for key in prediction
        if not isinstance(key, str)
    ]


def _check_generator_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.generator must be an object"]
    return _rule_errors(block, _GENERATOR_RULES, where) + _llm_model_errors(block, where)


def _llm_model_errors(block: dict[str, Any], where: str) -> list[str]:
    """The model an llm generator must name."""

    if block.get("kind") == "llm" and vocab.missing_string(block.get("model")):
        return [f"{where}.generator.model is required for an llm generator"]
    return []


def _check_oracle_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.oracle must be an object"]
    return _rule_errors(block, _ORACLE_RULES, where)


def _measurements_shape_errors(block: dict[str, Any], status: str, where: str) -> list[str]:
    """An array, and a non-empty one when the result claims to be measured."""

    measurements_block = block.get("measurements")
    if not isinstance(measurements_block, list):
        return [f"{where}.result.measurements must be an array"]
    if status == vocab.RESULT_MEASURED and not measurements_block:
        return [
            f"{where}.result: ORACLE_RESULT_MISSING — a measured result needs at "
            "least one measurement"
        ]
    return []


def _abstention_errors(block: dict[str, Any], status: str, where: str) -> list[str]:
    """An abstained result explains itself."""

    if status == vocab.RESULT_ABSTAINED and vocab.missing_string(block.get("abstention_reason")):
        return [
            f"{where}.result.abstention_reason must explain why the oracle "
            "produced no measurement"
        ]
    return []


def _check_result_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.result must be an object"]
    status = block.get("status")
    if not envelope.is_enum_value(status, vocab.RESULT_STATUSES):
        return [f"{where}.result.status must be one of {sorted(vocab.RESULT_STATUSES)}"]
    return _measurements_shape_errors(block, status, where) + _abstention_errors(
        block, status, where
    )


def _check_provenance_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.provenance must be an object"]
    return _rule_errors(block, _PROVENANCE_RULES, where)


def _check_validation_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.validation must be an object"]
    status = block.get("status")
    if not envelope.is_enum_value(status, vocab.VALIDATION_STATUSES):
        return [
            f"{where}.validation.status must be one of {sorted(vocab.VALIDATION_STATUSES)}"
        ]
    validator = block.get("validator")
    errors = _check_findings_list(block, status, where)
    if status != vocab.VALIDATION_UNVALIDATED:
        return errors + _check_validator_object(validator, where)
    if validator not in (None, {}):
        errors.append(f"{where}.validation: unvalidated records must not name a validator")
    return errors


def _findings_shape_ok(findings: Any) -> bool:
    return isinstance(findings, list) and all(_is_string(finding) for finding in findings)


def _check_findings_list(block: dict[str, Any], status: Any, where: str) -> list[str]:
    """``findings``, when present, lists non-empty strings; a passed verdict carries none."""

    if "findings" not in block:
        return []
    findings = block["findings"]
    if not _findings_shape_ok(findings):
        return [f"{where}.validation.findings must be a list of non-empty strings"]
    if status == vocab.VALIDATION_PASSED and findings:
        return [f"{where}.validation: a passed verdict cannot carry findings"]
    return []


def _check_validator_object(validator: Any, where: str) -> list[str]:
    """The validator identity a passed/failed verdict must carry."""

    if not isinstance(validator, dict):
        return [
            f"{where}.validation.validator must be an object naming the validator "
            "that stamped this verdict"
        ]
    return _rule_errors(validator, _VALIDATOR_RULES, where)


def _record_header_errors(record: dict[str, Any], where: str) -> list[str]:
    """The id, family, schema version, scenario and the optional sections."""

    return _rule_errors(record, _HEADER_RULES, where)


_BLOCK_CHECKS = (
    ("generator", _check_generator_block),
    ("oracle", _check_oracle_block),
    ("result", _check_result_block),
    ("provenance", _check_provenance_block),
    ("validation", _check_validation_block),
)


def check_envelope(record: Any, where: str) -> list[str]:
    """Validate the shared envelope. Returns a list of human-readable errors."""

    if not isinstance(record, dict):
        return [f"{where}: record must be a JSON object"]
    errors = _record_header_errors(record, where)
    for section, check in _BLOCK_CHECKS:
        errors += check(record.get(section), where)
    errors += check_generator_oracle_separation(record, where)
    errors += measurements.check_measurements(record, where)
    errors += energy_claims.check_no_theoretical_energy_claim(record, where)
    return errors


def check_digest(record: dict[str, Any], where: str) -> list[str]:
    """Verify ``provenance.record_sha256`` still matches the record content."""

    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or "record_sha256" not in provenance:
        return []
    expected, failure = vocab.digest_or_failure(record)
    if failure is not None:
        return [
            f"{where}.provenance.record_sha256: {vocab.RECORD_DIGEST_UNCOMPUTABLE} — the "
            "record's content cannot take the envelope's canonical form "
            f"({type(failure).__name__}: {failure})"
        ]
    actual = provenance.get("record_sha256")
    if actual != expected:
        return [
            f"{where}.provenance.record_sha256 mismatch: recorded {actual!r}, "
            f"content hashes to {expected!r}"
        ]
    return []


bind_import_twin(__name__)
