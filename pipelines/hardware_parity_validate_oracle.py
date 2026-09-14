#!/usr/bin/env python3
"""Re-executing the in-repo oracles and cross-checking determinism.

Both in-repo simulators are deterministic, so their traces are re-derivable and
are re-derived. A physical target cannot be, which is why its evidence rests on
the capture chain instead and the record says so.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))
from neuro_oracle import (  # noqa: E402
    FixedPointReferenceAdapter,
    SoftwareFloatAdapter,
    TARGET_FIXED_POINT_MODEL,
    run_digest,
)
from hardware_parity_record import (  # noqa: E402
    _capture_evidence_digest,
    _unavailable_evidence_digest,
)
from hardware_parity_validate_deployment import _is_canonical_sha256  # noqa: E402
from hardware_parity_validate_equality import _metrics_equal  # noqa: E402


def _compare_side(recorded, fresh, label, where):
    """Compare one recorded oracle run against a fresh re-simulation."""
    errors = []
    for key in (
        "spikes",
        "spike_events",
        "action",
        "membrane",
        "arithmetic",
        "latency",
    ):
        section_errors = _metrics_equal(
            recorded.get(key), fresh[key], f"oracle.{label}.{key}", where
        )
        if section_errors:
            reason_code = (
                "MEMBRANE_DIVERGENCE"
                if key == "membrane"
                else "PARITY_METRIC_MISMATCH"
            )
            errors.append(
                f"{where}: oracle.{label}.{key} does not match a re-simulation "
                f"[{reason_code}]"
            )
        if key == "membrane":
            section_errors = [
                error.replace("[PARITY_METRIC_MISMATCH]", "[MEMBRANE_DIVERGENCE]")
                for error in section_errors
            ]
        errors += section_errors
    expected = run_digest(fresh)
    if recorded.get("output_digest") != expected:
        errors.append(
            f"{where}: oracle.{label}.output_digest is not the digest of a "
            "re-simulation [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _check_reference_identity(run, adapter_type, label, where):
    """Bind a reference result to the exact in-repo adapter that produced it."""
    errors = []
    expected = {
        "adapter": adapter_type.name,
        "execution_target": adapter_type.execution_target,
        "runtime_class": adapter_type.runtime_class,
    }
    for key, value in expected.items():
        if run.get(key) != value:
            reason_code = (
                "HW_TARGET_UNKNOWN"
                if key == "execution_target"
                else "HW_PROVENANCE_MISSING"
            )
            errors.append(
                f"{where}: oracle.{label}.{key} must be {value!r}, got "
                f"{run.get(key)!r} [{reason_code}]"
            )
    return errors


def _reexecute_reference_sides(record, where):
    """Re-run every in-repo simulator and compare against what was recorded.

    This is the anti-fabrication gate for this family. Recomputing the parity
    metrics from the record's own traces is not enough on its own: copying one
    side's traces onto the other would then produce a self-consistent record
    asserting a match that never happened. Both in-repo simulators are
    deterministic, so the traces themselves are re-derivable and are re-derived.

    A physical deployment target cannot be re-simulated -- that is the whole
    point of running on hardware -- so for those the software leg is re-derived
    and the deployment leg rests on the capture digest chain and the board
    provenance that :func:`_check_physical_claim` demands. The record says
    which of the two it is, and never implies more.
    """
    errors = []
    scenario = record.get("scenario") or {}
    model = scenario.get("model_float")
    stimulus = scenario.get("stimulus")
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
        return [
            f"{where}: scenario.model_float and scenario.stimulus are required to "
            "re-derive the recorded runs [ENVELOPE_MALFORMED]"
        ]
    oracle = record.get("oracle") or {}

    software = oracle.get("software")
    if isinstance(software, dict):
        errors += _check_reference_identity(
            software, SoftwareFloatAdapter, "software", where
        )
        try:
            fresh = SoftwareFloatAdapter().run(model, stimulus, repeats=1)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
            OverflowError,
        ) as exc:
            return errors + [
                f"{where}: the recorded model and stimulus are not simulable: {exc}"
            ]
        errors += _compare_side(software, fresh, "software", where)

    deployment = oracle.get("deployment")
    if isinstance(deployment, dict):
        if deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL:
            errors += _check_reference_identity(
                deployment, FixedPointReferenceAdapter, "deployment", where
            )
            try:
                fresh = FixedPointReferenceAdapter().run(
                    model, stimulus, repeats=1
                )
            except (
                ValueError,
                KeyError,
                TypeError,
                IndexError,
                AttributeError,
                OverflowError,
            ) as exc:
                return errors + [
                    f"{where}: the recorded model is not quantizable/simulable: {exc}"
                ]
            errors += _compare_side(deployment, fresh, "deployment", where)
    return errors


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
