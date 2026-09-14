#!/usr/bin/env python3
"""Determinism claims, checked against the record's own repeat digests.

Repeats of a deterministic model are bit-identical by construction, which is
not the same as hardware repeatability; the record has to say which it means.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from hardware_parity_record import (  # noqa: E402
    _capture_evidence_digest,
    _unavailable_evidence_digest,
)
from hardware_parity_validate_deployment import _is_canonical_sha256  # noqa: E402

def _check_determinism(
    run, label, where, require_rederived_repeats=False, expected_meaning=None
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
        determinism, digests, label, where, expected_meaning
    )
    return errors


def _repeat_digest_evidence_errors(run, label, where, require_rederived_repeats):
    """The repeat-digest evidence itself: shape, count, and re-derivation.

    Returns ``(errors, digests)``; ``digests`` is None when the evidence is
    too malformed for any determinism claim to be graded against it.
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
    errors = []
    repeats = run.get("repeats")
    valid_repeats = (
        isinstance(repeats, int) and not isinstance(repeats, bool) and repeats >= 1
    )
    if not valid_repeats or repeats != len(digests):
        errors.append(
            f"{where}: oracle.{label}.repeats is {repeats!r} but {len(digests)} repeat "
            "digests were recorded [REPEATABILITY_UNPROVEN]"
        )
    if run.get("output_digest") not in digests:
        errors.append(
            f"{where}: oracle.{label}.output_digest is absent from its own "
            "repeat_digests [REPEATABILITY_UNPROVEN]"
        )
    if require_rederived_repeats and valid_repeats and repeats == len(digests):
        # The `repeats == len(digests)` guard binds the multiplication bound
        # to the trusted evidence (the actual digest list length) already
        # checked above, rather than an untrusted `repeats` integer that
        # could otherwise reach this allocation on its own when it disagrees.
        expected = [run.get("output_digest")] * repeats
        if digests != expected:
            errors.append(
                f"{where}: deterministic oracle.{label}.repeat_digests must repeat "
                "the re-derived output_digest exactly [REPEATABILITY_UNPROVEN]"
            )
    return errors, digests


def _determinism_claim_errors(determinism, digests, label, where, expected_meaning):
    """Grade the declared determinism block against its digest evidence."""
    errors = []
    distinct = len(set(digests))
    recorded_distinct = determinism.get("distinct_digests")
    # `bool` is an `int` subclass, so `True == 1`: an ordinary comparison
    # would accept a Boolean where the documented evidence shape is an exact
    # integer count.
    if (
        not isinstance(recorded_distinct, int)
        or isinstance(recorded_distinct, bool)
        or recorded_distinct != distinct
    ):
        errors.append(
            f"{where}: oracle.{label}.determinism.distinct_digests claims "
            f"{recorded_distinct!r} but the repeat digests contain "
            f"{distinct} [REPEATABILITY_UNPROVEN]"
        )
    if determinism.get("identical_repeats") is not (distinct == 1):
        errors.append(
            f"{where}: oracle.{label}.determinism.identical_repeats disagrees with its "
            "own repeat digests [REPEATABILITY_UNPROVEN]"
        )
    if expected_meaning is not None and determinism.get("meaning") != expected_meaning:
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
    if oracle.get("deployment") is None:
        unavailable = oracle.get("unavailable")
        if isinstance(unavailable, list) and len(unavailable) == 1:
            try:
                digests.append(_unavailable_evidence_digest(unavailable[0]))
            except (TypeError, ValueError, OverflowError):
                pass
    else:
        try:
            capture_digest = _capture_evidence_digest(oracle.get("deployment"))
        except (TypeError, ValueError, OverflowError):
            capture_digest = None
        if capture_digest is not None:
            digests.append(capture_digest)
    return digests
