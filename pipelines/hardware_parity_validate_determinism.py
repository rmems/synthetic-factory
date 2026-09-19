#!/usr/bin/env python3
"""Determinism claims, checked against the record's own repeat digests.

Repeats of a deterministic model are bit-identical by construction, which is
not the same as hardware repeatability; the record has to say which it means.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_determinism")
    from .hardware_parity_record import (  # noqa: E402
        _capture_evidence_digest,
        _unavailable_evidence_digest,
    )
    from .hardware_parity_validate_deployment import _is_canonical_sha256  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_determinism"
    )
    from hardware_parity_record import (  # noqa: E402
        _capture_evidence_digest,
        _unavailable_evidence_digest,
    )
    from hardware_parity_validate_deployment import _is_canonical_sha256  # noqa: E402

def _check_determinism(
    run, label, where, grading=(False, None)
):
    """Cross-check a declared determinism block against its own repeat digests.

    ``determinism`` is a claim; ``repeat_digests`` is the evidence for it.
    Without this, a record could assert perfect repeatability over digests
    that plainly disagree. When ``expected_meaning`` is given, the recorded
    ``determinism.meaning`` text must match it exactly, so a side that can
    only ever be a reference adapter (the software side is never a physical
    capture) cannot claim its bit-determinism is instead measured hardware
    variability.
    """
    require_rederived_repeats, expected_meaning = grading
    errors, digests = _repeat_digest_evidence_errors(
        run, label, where, require_rederived_repeats
    )
    if digests is None:
        return errors
    determinism = run.get("determinism")
    if not isinstance(determinism, dict):
        return errors + [
            f"{where}: oracle.{label}.determinism must be an object "
            "[REPEATABILITY_UNPROVEN]"
        ]
    errors += _determinism_claim_errors(
        determinism, digests, (label, where), expected_meaning
    )
    return errors


def _repeat_digest_shape_errors(run, label, where):
    """repeat_digests must be a non-empty list of canonical digest strings.

    Returns ``(errors, digests)``; ``digests`` is None when the list is too
    malformed for any further evidence grading.
    """
    digests = run.get("repeat_digests")
    if not isinstance(digests, list) or not digests:
        return [
            f"{where}: oracle.{label}.repeat_digests must list one digest per repeat "
            "[REPEATABILITY_UNPROVEN]"
        ], None
    malformed = [
        (index, value)
        for index, value in enumerate(digests)
        if not _is_canonical_sha256(value)
    ]
    if malformed:
        return [
            f"{where}: oracle.{label}.repeat_digests[{index}] must be a canonical "
            f"lowercase sha256:<64hex> string, got {value!r} "
            "[REPEATABILITY_UNPROVEN]"
            for index, value in malformed
        ], None
    return [], digests


def _repeat_digest_evidence_errors(run, label, where, require_rederived_repeats):
    """The repeat-digest evidence itself: shape, count, and re-derivation.

    Returns ``(errors, digests)``; ``digests`` is None when the evidence is
    too malformed for any determinism claim to be graded against it.
    """
    errors, digests = _repeat_digest_shape_errors(run, label, where)
    if digests is None:
        return errors, None
    repeats = run.get("repeats")
    valid_repeats = (
        isinstance(repeats, int) and not isinstance(repeats, bool) and repeats >= 1
    )
    if not valid_repeats or repeats != len(digests):
        errors.append(
            f"{where}: oracle.{label}.repeats is {repeats!r} but {len(digests)} repeat "
            "digests were recorded [REPEATABILITY_UNPROVEN]"
        )
    errors += _repeat_derivation_errors(
        run, digests, (label, where), require_rederived_repeats and valid_repeats
    )
    return errors, digests


def _repeat_derivation_errors(run, digests, loc, may_recheck):
    """output_digest must sit inside repeat_digests and, for deterministic
    sides, every digest must equal it. ``loc`` is ``(label, where)``."""
    label, where = loc
    errors = []
    if run.get("output_digest") not in digests:
        errors.append(
            f"{where}: oracle.{label}.output_digest is absent from its own "
            "repeat_digests [REPEATABILITY_UNPROVEN]"
        )
    if may_recheck and run.get("repeats") == len(digests):
        # The `repeats == len(digests)` guard binds the multiplication bound
        # to the trusted evidence (the actual digest list length) already
        # checked above, rather than an untrusted `repeats` integer that
        # could otherwise reach this allocation on its own when it disagrees.
        expected = [run.get("output_digest")] * len(digests)
        if digests != expected:
            errors.append(
                f"{where}: deterministic oracle.{label}.repeat_digests must repeat "
                "the re-derived output_digest exactly [REPEATABILITY_UNPROVEN]"
            )
    return errors


def _distinct_count_matches(recorded_distinct, distinct):
    """distinct_digests must be an exact int equal to the observed count.

    ``bool`` is an ``int`` subclass, so ``True == 1``: an ordinary
    ``isinstance`` check would accept a Boolean where the documented evidence
    shape is an exact integer count.
    """
    return type(recorded_distinct) is int and recorded_distinct == distinct


def _identical_repeats_matches(recorded_identical, distinct):
    return recorded_identical is (distinct == 1)


def _meaning_matches(meaning, expected_meaning):
    return expected_meaning is None or meaning == expected_meaning


def _determinism_claim_errors(determinism, digests, loc, expected_meaning):
    """Grade the declared determinism block against its digest evidence.
    ``loc`` is ``(label, where)``."""
    label, where = loc
    errors = []
    distinct = len(set(digests))
    if not _distinct_count_matches(determinism.get("distinct_digests"), distinct):
        errors.append(
            f"{where}: oracle.{label}.determinism.distinct_digests claims "
            f"{determinism.get('distinct_digests')!r} but the repeat digests contain "
            f"{distinct} [REPEATABILITY_UNPROVEN]"
        )
    if not _identical_repeats_matches(determinism.get("identical_repeats"), distinct):
        errors.append(
            f"{where}: oracle.{label}.determinism.identical_repeats disagrees with its "
            "own repeat digests [REPEATABILITY_UNPROVEN]"
        )
    if not _meaning_matches(determinism.get("meaning"), expected_meaning):
        errors.append(
            f"{where}: oracle.{label}.determinism.meaning does not match its "
            "adapter-owned canonical text [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _record_oracle_digests(oracle):
    """The ordered evidence lineage this record's oracle output supports."""
    digests = [
        side["output_digest"]
        for side in (oracle.get("software"), oracle.get("deployment"))
        if isinstance(side, dict) and side.get("output_digest")
    ]
    tail = _unavailable_side_digest(oracle)
    if tail is None:
        tail = _capture_side_digest(oracle)
    if tail is not None:
        digests.append(tail)
    return digests


def _unavailable_side_digest(oracle):
    """The unavailable-diagnostic digest when deployment is absent."""
    if oracle.get("deployment") is not None:
        return None
    unavailable = oracle.get("unavailable")
    if isinstance(unavailable, list) and len(unavailable) == 1:
        try:
            return _unavailable_evidence_digest(unavailable[0])
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def _capture_side_digest(oracle):
    """The capture-chain digest when a deployment claim is present."""
    if oracle.get("deployment") is None:
        return None
    try:
        return _capture_evidence_digest(oracle.get("deployment"))
    except (TypeError, ValueError, OverflowError):
        return None


if __package__:
    _expose_package_sibling(__name__)
