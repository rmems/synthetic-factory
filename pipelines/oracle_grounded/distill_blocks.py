#!/usr/bin/env python3
"""Envelope shape checks for the distillation contract (issue #78).

One check per record block -- generator, oracle, result, provenance,
validation -- plus the generator/oracle separation rule and the content
digest. :func:`check_envelope` composes them, in the order their findings
have always been emitted, with the measurement checks that live in
``distill_measurements``.
"""

from __future__ import annotations

from typing import Any

from . import distill_measurements as measurements
from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def check_generator_oracle_separation(record: dict[str, Any], where: str) -> list[str]:
    """Reject oracle-owned keys hiding inside generator-owned namespaces.

    The reserved-key scan is the envelope's bounded walker over this
    contract's ``ORACLE_ONLY_KEYS``: one finding per record listing the paths
    it found, capped at ``envelope.MAX_RESERVED_KEY_HITS``. The ``predicted_*``
    naming rule for ``candidate_prediction`` is a distillation rule and runs
    here, after the shared scan.
    """

    errors = envelope.check_generator_oracle_separation(
        record, vocab.ORACLE_ONLY_KEYS, where
    )
    return errors + _check_prediction_naming(record.get("candidate_prediction"), where)


def _check_prediction_naming(prediction: Any, where: str) -> list[str]:
    """A generator guess must be ``predicted_*`` (or one of the free keys)."""

    if not isinstance(prediction, dict):
        return []
    return [
        f"{where}.candidate_prediction.{key}: generator predictions must be "
        f"named {vocab.PREDICTION_PREFIX}* (or one of "
        f"{sorted(vocab.PREDICTION_FREE_KEYS)})"
        for key in sorted(prediction)
        if key not in vocab.PREDICTION_FREE_KEYS
        and not key.startswith(vocab.PREDICTION_PREFIX)
    ]


def _seed_errors(block: dict[str, Any], section: str, absent_note: str, where: str) -> list[str]:
    """``seed`` must be present, and an integer or null when it is.

    The shared envelope restricts the seed to integer/null. Presence alone
    accepted ``{"seed": {}}`` or ``"seed": true``, so malformed
    reproducibility metadata stayed curation-eligible.
    """

    if "seed" not in block:
        return [f"{where}.{section}.seed must be present ({absent_note})"]
    seed = block["seed"]
    if seed is not None and not vocab.is_genuine_int(seed):
        return [f"{where}.{section}.seed must be an integer or null, got {seed!r}"]
    return []


def _generator_identity_errors(block: dict[str, Any], where: str) -> list[str]:
    """Name, kind, version, the pinned authority, and the model an llm needs."""

    errors: list[str] = []
    if vocab.missing_string(block.get("name")):
        errors.append(f"{where}.generator.name must be a non-empty string")
    if not envelope.is_enum_value(block.get("kind"), vocab.GENERATOR_KINDS):
        errors.append(
            f"{where}.generator.kind must be one of {sorted(vocab.GENERATOR_KINDS)}"
        )
    if vocab.missing_string(block.get("version")):
        errors.append(f"{where}.generator.version must be a non-empty string")
    if block.get("authority") != vocab.GENERATOR_AUTHORITY:
        errors.append(
            f"{where}.generator.authority must be {vocab.GENERATOR_AUTHORITY!r} — "
            "a generator may never certify its own result"
        )
    if block.get("kind") == "llm" and not isinstance(block.get("model"), str):
        errors.append(f"{where}.generator.model is required for an llm generator")
    return errors


def _check_generator_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.generator must be an object"]
    return _generator_identity_errors(block, where) + _seed_errors(
        block, "generator", "null when unseeded", where
    )


def _oracle_identity_errors(block: dict[str, Any], where: str) -> list[str]:
    """Name, type, implementation, version and authority."""

    errors: list[str] = []
    if vocab.missing_string(block.get("name")):
        errors.append(f"{where}.oracle.name must be a non-empty string")
    if not envelope.is_enum_value(block.get("type"), vocab.ORACLE_TYPES):
        errors.append(f"{where}.oracle.type must be one of {sorted(vocab.ORACLE_TYPES)}")
    for key in ("implementation", "version"):
        if vocab.missing_string(block.get(key)):
            errors.append(f"{where}.oracle.{key} must be a non-empty string")
    if not envelope.is_enum_value(block.get("authority"), vocab.ORACLE_AUTHORITIES):
        errors.append(
            f"{where}.oracle.authority must be one of {sorted(vocab.ORACLE_AUTHORITIES)}"
        )
    return errors


def _oracle_reproducibility_errors(block: dict[str, Any], where: str) -> list[str]:
    """Seed and commit: present, and integer/null or string/null.

    Presence is not enough: the shared schema restricts these to
    integer/null and string/null, and nothing else inspected them — so
    ``seed: {}`` and ``commit: []`` passed as reproducibility metadata.
    """

    errors = _seed_errors(block, "oracle", "null when n/a", where)
    if "commit" not in block:
        errors.append(f"{where}.oracle.commit must be present (null when n/a)")
    elif block["commit"] is not None and not isinstance(block["commit"], str):
        errors.append(
            f"{where}.oracle.commit must be a string or null, got {block['commit']!r}"
        )
    return errors


def _check_oracle_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.oracle must be an object"]
    errors = _oracle_identity_errors(block, where)
    if not isinstance(block.get("configuration"), dict):
        errors.append(f"{where}.oracle.configuration must be an object")
    return errors + _oracle_reproducibility_errors(block, where)


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


def _check_result_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.result must be an object"]
    status = block.get("status")
    if not envelope.is_enum_value(status, vocab.RESULT_STATUSES):
        return [f"{where}.result.status must be one of {sorted(vocab.RESULT_STATUSES)}"]
    errors = _measurements_shape_errors(block, status, where)
    if status == vocab.RESULT_ABSTAINED and vocab.missing_string(
        block.get("abstention_reason")
    ):
        errors.append(
            f"{where}.result.abstention_reason must explain why the oracle "
            "produced no measurement"
        )
    return errors


def _check_provenance_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.provenance must be an object"]
    errors: list[str] = []
    if vocab.missing_string(block.get("producer")):
        errors.append(f"{where}.provenance.producer must be a non-empty string")
    produced_at = block.get("produced_at")
    if not isinstance(produced_at, str) or not envelope.ISO_8601_RE.match(produced_at):
        errors.append(
            f"{where}.provenance.produced_at must be an ISO-8601 UTC timestamp"
        )
    # Required, not optional. If the digest may be absent, deleting it is all it
    # takes to switch off tamper detection for the whole record.
    digest = block.get("record_sha256")
    if not isinstance(digest, str) or not envelope.SHA256_RE.match(digest):
        errors.append(f"{where}.provenance.record_sha256 must be a sha256 hex digest")
    return errors


def _check_validation_block(block: Any, where: str) -> list[str]:
    if not isinstance(block, dict):
        return [f"{where}.validation must be an object"]
    status = block.get("status")
    if not envelope.is_enum_value(status, vocab.VALIDATION_STATUSES):
        return [
            f"{where}.validation.status must be one of {sorted(vocab.VALIDATION_STATUSES)}"
        ]
    validator = block.get("validator")
    if status != vocab.VALIDATION_UNVALIDATED:
        return _check_validator_object(validator, where)
    if validator not in (None, {}):
        return [f"{where}.validation: unvalidated records must not name a validator"]
    return []


def _check_validator_object(validator: Any, where: str) -> list[str]:
    """The validator identity a passed/failed verdict must carry."""

    if not isinstance(validator, dict):
        return [
            f"{where}.validation.validator must be an object naming the validator "
            "that stamped this verdict"
        ]
    errors: list[str] = []
    for key in ("name", "version"):
        if vocab.missing_string(validator.get(key)):
            errors.append(f"{where}.validation.validator.{key} must be a non-empty string")
    checked_at = validator.get("checked_at")
    if not isinstance(checked_at, str) or not envelope.ISO_8601_RE.match(checked_at):
        errors.append(
            f"{where}.validation.validator.checked_at must be an ISO-8601 UTC timestamp"
        )
    validated_digest = validator.get("validated_digest")
    if validated_digest is not None and not (
        isinstance(validated_digest, str) and envelope.SHA256_RE.match(validated_digest)
    ):
        errors.append(
            f"{where}.validation.validator.validated_digest must be a sha256 digest"
        )
    return errors


def _record_header_errors(record: dict[str, Any], where: str) -> list[str]:
    """The id, family, schema version, scenario and the optional sections."""

    errors: list[str] = []
    if vocab.missing_string(record.get("id")):
        errors.append(f"{where}.id must be a non-empty string")
    if record.get("family") not in vocab.FAMILIES:
        errors.append(f"{where}.family must be one of {sorted(vocab.FAMILIES)}")
    if record.get("schema_version") != vocab.SCHEMA_VERSION:
        errors.append(
            f"{where}.schema_version must be {vocab.SCHEMA_VERSION!r}, "
            f"got {record.get('schema_version')!r}"
        )
    if not isinstance(record.get("scenario"), dict) or not record["scenario"]:
        errors.append(f"{where}.scenario must be a non-empty object")
    for optional in ("intervention", "candidate_prediction"):
        # Must be an object, not a list: the predicted_* naming rule is only
        # expressible over named keys, so a list would slip past it.
        if optional in record and not isinstance(record[optional], dict):
            errors.append(f"{where}.{optional} must be an object")
    return errors


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
    errors += measurements.check_no_theoretical_energy_claim(record, where)
    return errors


def check_digest(record: dict[str, Any], where: str) -> list[str]:
    """Verify ``provenance.record_sha256`` still matches the record content."""

    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or "record_sha256" not in provenance:
        return []
    expected = envelope.record_digest(record)
    actual = provenance.get("record_sha256")
    if actual != expected:
        return [
            f"{where}.provenance.record_sha256 mismatch: recorded {actual!r}, "
            f"content hashes to {expected!r}"
        ]
    return []


bind_import_twin(__name__)
