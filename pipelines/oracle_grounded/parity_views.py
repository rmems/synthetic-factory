"""Training views that structurally cannot hide a parity failure.

Split out of ``parity_contract`` by responsibility; every name is re-exported
from there. This module owns the view key list, the builder, the
validator-derived execution-target list for each record kind, and
``training_view_errors``, the gate that rejects a view which softens, drops
or relabels what the oracles found.
"""

from __future__ import annotations

from .envelope import strict_json_equal
from .parity_blocks import check_reason_codes
from .parity_terms import (
    KIND_HARDWARE_PARITY,
    KIND_NIR_EQUIVALENCE,
    PASSING_VERDICTS,
    _is_object,
    _nonempty_str,
)


TRAINING_VIEW_KEYS = (
    "id",
    "record_kind",
    "dataset",
    "verdict",
    "parity_failed",
    "oracle_complete",
    "reason_codes",
    "oracle_backed",
    "execution_targets",
    "evidence_digests",
)

# A MATCH is not a complete oracle when the hardware/HIL leg could not be
# re-derived, or when the intended oracle never executed.
ORACLE_INCOMPLETE_REASON_CODES = frozenset(
    {
        "ORACLE_UNAVAILABLE",
        "DEPLOYMENT_TRACE_NOT_REDERIVABLE",
    }
)


def oracle_is_complete(reason_codes):
    codes = reason_codes if isinstance(reason_codes, list) else []
    # Only string codes can signal incompleteness. A non-string entry (for
    # example a nested list) is malformed and is reported by the reason-code
    # checks; hashing it here would abort with a TypeError before those
    # checks could say so.
    return not any(
        isinstance(code, str) and code in ORACLE_INCOMPLETE_REASON_CODES
        for code in codes
    )


def build_training_view(record, prompt, completion, execution_targets):
    """Build a training view that structurally cannot hide a parity failure.

    The verdict, the failure flag, and the reason codes are copied from the
    record rather than recomputed, and :func:`training_view_errors` re-checks
    them, so an exporter cannot quietly emit only the agreeable half of the
    corpus without failing validation.
    """
    result = record.get("result") or {}
    verdict = result.get("verdict")
    raw_reason_codes = result.get("reason_codes")
    reason_codes = list(raw_reason_codes) if isinstance(raw_reason_codes, list) else []
    raw_evidence = result.get("derived_from")
    evidence_digests = list(raw_evidence) if isinstance(raw_evidence, list) else []
    return {
        "id": record.get("id"),
        "record_kind": record.get("record_kind"),
        "dataset": record.get("dataset"),
        "prompt": prompt,
        "completion": completion,
        "verdict": verdict,
        "parity_failed": verdict not in PASSING_VERDICTS,
        # `parity_failed: false` means "the oracles that ran agreed", which is
        # not the same as "the intended oracles ran". A consumer filtering on
        # parity_failed alone would otherwise read a clean bill of health off a
        # record whose authoritative oracle never executed, so the gap is
        # carried as its own flag rather than buried in the reason codes.
        "oracle_complete": oracle_is_complete(reason_codes),
        "reason_codes": reason_codes,
        "oracle_backed": result.get("oracle_backed"),
        "execution_targets": list(execution_targets),
        "evidence_digests": evidence_digests,
    }


def _hardware_parity_execution_targets(oracle):
    targets = []
    for side_name in ("software", "deployment"):
        side = oracle.get(side_name)
        if side is None:
            continue
        if not isinstance(side, dict) or not _nonempty_str(side.get("execution_target")):
            return None
        targets.append(side["execution_target"])
    return targets


def _is_runtime_status_entry(entry):
    """A runtimes[] entry that carries both a runtime name and a status."""
    return (
        isinstance(entry, dict)
        and _nonempty_str(entry.get("runtime"))
        and _nonempty_str(entry.get("status"))
    )


def _nir_equivalence_execution_targets(oracle):
    runtimes = oracle.get("runtimes")
    if not isinstance(runtimes, list):
        return None
    targets = []
    for entry in runtimes:
        if not _is_runtime_status_entry(entry):
            return None
        targets.append(f"{entry['runtime']}:{entry['status']}")
    return targets


def _record_execution_targets(record):
    """Re-derive the exact target list copied into a training view."""
    oracle = record.get("oracle")
    if not isinstance(oracle, dict):
        return None
    kind = record.get("record_kind")
    if kind == KIND_HARDWARE_PARITY:
        return _hardware_parity_execution_targets(oracle)
    if kind == KIND_NIR_EQUIVALENCE:
        return _nir_equivalence_execution_targets(oracle)
    return None


def _view_key_errors(view, where):
    """The training-view key set is fixed; a missing key is a hidden failure."""
    missing = [key for key in TRAINING_VIEW_KEYS if key not in view]
    if missing:
        return [
            f"{where}: training view missing {missing} [TRAINING_VIEW_HIDES_FAILURE]"
        ]
    return []


def _view_identity_field_errors(record, view, where):
    """id, record_kind and dataset must be copied exactly from the record."""
    return [
        f"{where}: training view {key} must exactly match the source record "
        "[TRAINING_VIEW_HIDES_FAILURE]"
        for key in ("id", "record_kind", "dataset")
        if not strict_json_equal(view.get(key), record.get(key))
    ]


def _view_verdict_errors(record, view, where):
    """The verdict, and the failure flag derived from it, must not be softened."""
    result = record.get("result") or {}
    verdict = result.get("verdict")
    errors = []
    if view.get("verdict") != verdict:
        errors.append(
            f"{where}: training view verdict {view.get('verdict')!r} != record verdict "
            f"{verdict!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    expected_failed = verdict not in PASSING_VERDICTS
    if view.get("parity_failed") is not expected_failed:
        errors.append(
            f"{where}: training view parity_failed must be {expected_failed} for verdict "
            f"{verdict!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def _check_view_identity(record, view, where):
    """The view's key set and its identity/verdict fields must mirror the record."""
    errors = _view_key_errors(view, where)
    errors += _view_identity_field_errors(record, view, where)
    errors += _view_verdict_errors(record, view, where)
    return errors


def _string_codes(raw_codes):
    """The string entries of a reason-code list; anything else yields none."""
    if not isinstance(raw_codes, list):
        return []
    return [code for code in raw_codes if isinstance(code, str)]


def _side_reason_code_errors(raw_codes, where, field, malformed_message):
    """Well-formedness of one side's reason_codes, tagged for the view gate.

    Returns the string-only codes alongside the findings, so the caller can
    reuse them without re-filtering.
    """
    codes = _string_codes(raw_codes)
    errors = []
    if not isinstance(raw_codes, list) or len(codes) != len(raw_codes):
        errors.append(f"{where}: {malformed_message} [TRAINING_VIEW_HIDES_FAILURE]")
    errors += [
        f"{error} [TRAINING_VIEW_HIDES_FAILURE]"
        for error in check_reason_codes(raw_codes, where, field)
    ]
    return codes, errors


def _check_view_reason_codes(record, view, where):
    """Both sides' reason_codes must be well-formed and exactly match."""
    result = record.get("result") or {}
    raw_record_codes = result.get("reason_codes")
    record_codes, errors = _side_reason_code_errors(
        raw_record_codes,
        where,
        "record reason_codes",
        "record reason_codes are malformed",
    )
    expected_complete = oracle_is_complete(record_codes)
    if view.get("oracle_complete") is not expected_complete:
        errors.append(
            f"{where}: training view oracle_complete must be {expected_complete} for "
            f"this record's reason codes [TRAINING_VIEW_HIDES_FAILURE]"
        )
    raw_view_codes = view.get("reason_codes")
    _view_codes, view_errors = _side_reason_code_errors(
        raw_view_codes,
        where,
        "training view reason_codes",
        "training view reason_codes must be an array of strings",
    )
    errors += view_errors
    if not strict_json_equal(raw_view_codes, raw_record_codes):
        errors.append(
            f"{where}: training view reason_codes must exactly match the record's "
            "ordered reason_codes, with no additions, omissions, or reordering "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def _execution_target_errors(record, view, where):
    """The view's execution targets must be the validator-derived list exactly."""
    expected_targets = _record_execution_targets(record)
    if expected_targets is None:
        return [
            f"{where}: record execution targets are malformed and cannot support a "
            "training view [TRAINING_VIEW_HIDES_FAILURE]"
        ]
    if not strict_json_equal(view.get("execution_targets"), expected_targets):
        return [
            f"{where}: training view execution targets must exactly match "
            f"validator-derived targets {expected_targets!r} "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        ]
    return []


def _check_view_provenance(record, view, where):
    """oracle_backed, execution_targets, and evidence_digests must all check out."""
    errors = []
    if view.get("oracle_backed") is not True:
        errors.append(
            f"{where}: training view must stay oracle-backed [RESULT_NOT_ORACLE_BACKED]"
        )
    errors += _execution_target_errors(record, view, where)
    result = record.get("result") or {}
    expected_digests = result.get("derived_from")
    if not strict_json_equal(view.get("evidence_digests"), expected_digests):
        errors.append(
            f"{where}: training view evidence_digests must exactly match "
            "result.derived_from [RESULT_DIGEST_UNLINKED]"
        )
    return errors


def training_view_errors(record, view, where):
    """Reject a training view that softens, drops, or relabels a failure."""
    if not _is_object(view):
        return [f"{where}: training view must be an object [TRAINING_VIEW_HIDES_FAILURE]"]
    errors = _check_view_identity(record, view, where)
    errors += _check_view_reason_codes(record, view, where)
    errors += _check_view_provenance(record, view, where)
    return errors
