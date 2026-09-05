"""The shared parity record envelope check.

Split out of ``parity_contract`` by responsibility; ``check_envelope`` and its
identity, scenario and meta rules are re-exported from there. The per-block
rules it composes live in ``parity_blocks``; the family validators build their
own rules on top of the findings this module returns.
"""

from __future__ import annotations

from .parity_blocks import (
    check_candidate_prediction,
    check_generator,
    check_provenance,
    check_result,
    check_validation_block,
)
from .parity_terms import (
    DATASET_FOR_KIND,
    ENVELOPE_KEYS,
    RECORD_KINDS,
    SCHEMA_VERSION_FOR_KIND,
    _is_object,
    _is_positive_round,
    _nonempty_str,
)


def _kind_and_dataset_errors(record, where):
    """record_kind from the vocabulary, and the dataset pinned to that kind."""
    kind = record.get("record_kind")
    if kind not in RECORD_KINDS:
        return [f"{where}.record_kind must be one of {list(RECORD_KINDS)}"]
    if record.get("dataset") != DATASET_FOR_KIND[kind]:
        return [
            f"{where}.dataset must be {DATASET_FOR_KIND[kind]!r} for record_kind {kind!r}"
        ]
    return []


def _schema_version_errors(record, where):
    """schema_version present, and equal to the pin when the kind carries one."""
    kind = record.get("record_kind")
    schema_version = record.get("schema_version")
    if not _nonempty_str(schema_version):
        return [f"{where}.schema_version must be a non-empty string"]
    if kind not in SCHEMA_VERSION_FOR_KIND:
        return []
    expected_version = SCHEMA_VERSION_FOR_KIND[kind]
    if schema_version != expected_version:
        return [
            f"{where}.schema_version must be {expected_version!r} for "
            f"record_kind {kind!r}, got {schema_version!r}"
        ]
    return []


def _check_envelope_identity(record, where):
    """id, record_kind, and the dataset/schema_version pinned to that kind."""
    errors = []
    if not _nonempty_str(record.get("id")):
        errors.append(f"{where}.id must be a non-empty string")
    errors += _kind_and_dataset_errors(record, where)
    errors += _schema_version_errors(record, where)
    return errors


def _check_envelope_scenario(record, where):
    """The scenario object and the optional intervention beside it."""
    errors = []
    if not _is_object(record.get("scenario")):
        errors.append(f"{where}.scenario must be an object")
    elif not _nonempty_str(record["scenario"].get("id")):
        errors.append(f"{where}.scenario.id must be a non-empty string")
    if record.get("intervention") is not None and not _is_object(record.get("intervention")):
        errors.append(f"{where}.intervention must be an object or null")
    return errors


def _check_envelope_meta(meta, where):
    """Round and factory stamps carried by every record kind."""
    if not _is_object(meta):
        return [f"{where}.meta must be an object"]
    errors = []
    # `>= 1` matches validate_run.check_meta_round, so a parity record is
    # not the one kind in the factory that can carry round 0 or -1.
    if not _is_positive_round(meta.get("round")):
        errors.append(f"{where}.meta.round must be an integer >= 1")
    if not _nonempty_str(meta.get("factory")):
        errors.append(f"{where}.meta.factory must be a non-empty string")
    return errors


def _missing_key_errors(record, where):
    """The envelope keys the record does not carry at all."""
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        return [f"{where}: envelope missing {missing} [ENVELOPE_MALFORMED]"]
    return []


def _oracle_block_errors(record, where):
    """The oracle section is an object; what it holds is the family's to check."""
    if not _is_object(record.get("oracle")):
        return [f"{where}.oracle must be an object"]
    return []


def check_envelope(record, where, oracle_digests=None):
    """Validate the shared envelope. Family validators add their own rules."""
    if not _is_object(record):
        return [f"{where}: record must be a JSON object [ENVELOPE_MALFORMED]"]
    errors = _missing_key_errors(record, where)
    errors += _check_envelope_identity(record, where)
    errors += check_generator(record.get("generator"), where)
    errors += _check_envelope_scenario(record, where)
    errors += check_candidate_prediction(record.get("candidate_prediction"), where)
    errors += _oracle_block_errors(record, where)
    errors += check_result(record.get("result"), where, oracle_digests)
    errors += check_provenance(record.get("provenance"), where)
    errors += check_validation_block(record.get("validation"), where)
    errors += _check_envelope_meta(record.get("meta"), where)
    return errors
