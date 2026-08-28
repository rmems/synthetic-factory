"""Execution-gate helpers for pipelines/round_txn.py.

Look up patchable names on the host module so tests that patch
``round_txn.execution_gate`` or ``EXECUTION_VERIFIER_SEMANTICS_VERSION``
keep working after this split.
"""

from __future__ import annotations

from pathlib import Path


class _Host:
    def __getattr__(self, name):
        import round_txn
        return getattr(round_txn, name)


rt = _Host()


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_nonneg_int(value):
    return _is_int(value) and value >= 0


def _is_positive_int(value):
    return _is_int(value) and value >= 1


def normalized_execution_override(reason):
    """Validate and normalize an operator waiver for cannot-verify records.

    The canonicalized waiver is recorded in ``ROUND-rNN.complete.json``.
    Whitespace is collapsed so the marker contains short, printable,
    single-line text that a later auditor can read.
    """
    if reason is None:
        return None
    if not isinstance(reason, str):
        raise rt.TransactionError(
            "execution verification override must be a written reason string"
        )
    text = " ".join(reason.split())
    if not text.isprintable():
        raise rt.TransactionError(
            "execution verification override must not contain non-printable characters"
        )
    if len(text) < rt.EXECUTION_OVERRIDE_MIN_CHARS:
        raise rt.TransactionError(
            "execution verification override needs a written reason of at least "
            f"{rt.EXECUTION_OVERRIDE_MIN_CHARS} characters"
        )
    if len(text) > rt.EXECUTION_OVERRIDE_MAX_CHARS:
        raise rt.TransactionError(
            "execution verification override reason must be at most "
            f"{rt.EXECUTION_OVERRIDE_MAX_CHARS} characters"
        )
    return text


def _execution_override_from_block(verification):
    override = verification.get("override")
    if override is None:
        return None
    if not isinstance(override, dict):
        raise rt.TransactionError("publishing marker has invalid execution override")
    reason = override.get("reason")
    normalized = normalized_execution_override(reason)
    if normalized != reason:
        raise rt.TransactionError("publishing marker execution override is not canonical")
    waived = override.get("waived_inconclusive")
    if not _is_positive_int(waived):
        raise rt.TransactionError(
            "publishing marker has invalid waived_inconclusive count"
        )
    return normalized


def recorded_execution_override(manifest):
    """Return a canonical waiver already persisted in a publishing marker."""
    verification = manifest.get("execution_verification")
    if not isinstance(verification, dict):
        raise rt.TransactionError("publishing marker has invalid execution verification")
    return _execution_override_from_block(verification)


def comparable_execution_verification(verification):
    """Return derived verification fields while exempting only waiver prose."""
    if not isinstance(verification, dict):
        raise rt.TransactionError("publishing marker has invalid execution verification")
    comparable = dict(verification)
    override = comparable.get("override")
    if isinstance(override, dict):
        comparable["override"] = {
            key: value for key, value in override.items() if key != "reason"
        }
    return comparable


def _validated_execution_counts(counts, marker_kind):
    if not isinstance(counts, dict) or set(counts) != rt.EXECUTION_COUNT_KEYS:
        raise rt.TransactionError(
            f"{marker_kind} has invalid execution verification counts"
        )
    if any(not _is_nonneg_int(counts[key]) for key in counts):
        raise rt.TransactionError(
            f"{marker_kind} has invalid execution verification counts"
        )
    return counts


def _execution_identity_is_canonical(verification, counts):
    if verification.get("gate") != rt.EXECUTION_GATE_LABEL:
        return False
    if verification.get("strict") is not True:
        return False
    if counts["total"] < 1 or counts["failed"] != 0:
        return False
    return counts["verified"] + counts["inconclusive"] == counts["total"]


def _historical_semantics_version(value):
    if not _is_positive_int(value):
        return False
    return value < rt.EXECUTION_VERIFIER_SEMANTICS_VERSION


def _validated_execution_semantics_version(verification, marker_kind):
    value = verification.get("semantics_version")
    if value == rt.EXECUTION_VERIFIER_SEMANTICS_VERSION:
        return value
    if _historical_semantics_version(value):
        return value
    raise rt.TransactionError(f"{marker_kind} has invalid execution verification")


def _validated_override_matches_counts(verification, counts, marker_kind):
    override = recorded_execution_override(
        {"execution_verification": verification}
    )
    if not counts["inconclusive"]:
        if override is not None:
            raise rt.TransactionError(
                f"{marker_kind} cannot waive a conclusive execution verdict"
            )
        return
    if override is None:
        raise rt.TransactionError(
            f"{marker_kind} execution override does not match "
            "the inconclusive count"
        )
    waived = verification["override"]["waived_inconclusive"]
    if waived != counts["inconclusive"]:
        raise rt.TransactionError(
            f"{marker_kind} execution override does not match "
            "the inconclusive count"
        )


def validated_execution_verification_summary(
    verification, marker_kind="completion marker"
):
    """Validate the canonical strict-gate summary stored in a durable marker."""
    if not isinstance(verification, dict):
        raise rt.TransactionError(f"{marker_kind} has invalid execution verification")
    if set(verification) != rt.CANONICAL_EXECUTION_VERIFICATION_KEYS:
        raise rt.TransactionError(f"{marker_kind} has invalid execution verification")
    counts = _validated_execution_counts(verification.get("counts"), marker_kind)
    _validated_execution_semantics_version(verification, marker_kind)
    if not _execution_identity_is_canonical(verification, counts):
        raise rt.TransactionError(f"{marker_kind} has invalid execution verification")
    _validated_override_matches_counts(verification, counts, marker_kind)
    return verification


def _rederive_current_execution_verification(batch: Path, manifest: dict):
    try:
        override = recorded_execution_override(manifest)
        return rt.execution_gate(batch, batch, override=override)
    except rt.TransactionError as exc:
        raise rt.TransactionError(
            "completion marker execution verification conflicts with "
            f"committed batch: {batch}\n{exc}"
        ) from exc


def _validate_historical_execution_counts(recorded, manifest, batch):
    counts = recorded.get("counts")
    records = manifest.get("records")
    if not isinstance(counts, dict) or counts.get("total") != records:
        raise rt.TransactionError(
            "completion marker execution verification total does not match "
            f"committed records: {batch}"
        )
    return recorded


def validate_completed_execution_verification(batch: Path, manifest: dict):
    """Re-derive the v2 execution verdict before exposing a completed batch."""
    recorded = manifest.get("execution_verification")
    if not isinstance(recorded, dict):
        raise rt.TransactionError(
            "version 2 completion marker requires an exact execution "
            f"verification block: {batch}"
        )
    validated_execution_verification_summary(
        recorded, marker_kind="completion marker"
    )
    if recorded.get("semantics_version") != rt.EXECUTION_VERIFIER_SEMANTICS_VERSION:
        return _validate_historical_execution_counts(recorded, manifest, batch)
    derived = _rederive_current_execution_verification(batch, manifest)
    if recorded != derived:
        raise rt.TransactionError(
            "completion marker execution verification conflicts with "
            f"committed batch: {batch}"
        )
    return recorded


def load_execution_verifier():
    """Import the execution verifier on demand, failing closed when missing.

    The import stays local so ``verify_execution`` can audit any run directory
    without a ``round_txn`` reservation. A missing verifier is not a licence to
    publish unverified records, so the absence raises instead of skipping.
    """
    try:
        from verify_execution import verify_batch_for_frontier
    except ImportError as exc:
        raise rt.TransactionError(
            "execution verification is unavailable; refusing to publish records "
            f"whose execution evidence cannot be checked: {exc}"
        ) from exc
    return verify_batch_for_frontier


def _format_execution_findings(findings, staged_batch):
    detail = "\n".join(
        f"{finding['status'].upper()}: {staged_batch.name}:{finding['line']} — "
        f"{finding['reason']}"
        for finding in findings[:5]
    )
    if len(findings) > 5:
        detail += f"\n... and {len(findings) - 5} more findings"
    return detail


def _raise_execution_gate_failure(counts, staged_batch, detail, override):
    if counts["failed"]:
        raise rt.TransactionError(
            f"execution verification failed for the staged batch: {staged_batch}\n"
            f"{counts['failed']} failed, {counts['inconclusive']} inconclusive of "
            f"{counts['total']} records; a failed record is never waivable\n"
            + detail
        )
    if override is None:
        raise rt.TransactionError(
            "execution verification cannot verify "
            f"{counts['inconclusive']} of {counts['total']} staged records: "
            f"{staged_batch}\n" + detail + "\n"
            "cannot-verify is never treated as verified; regenerate the round "
            "with observable execution evidence, or republish with "
            '--allow-inconclusive "<reason>" to record an explicit operator '
            "waiver in the completion marker"
        )


def execution_gate(batch: Path, staged_batch: Path, override=None):
    """Gate one staged batch on observable execution evidence."""
    verify_batch_for_frontier = load_execution_verifier()
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    summary = {
        "gate": rt.EXECUTION_GATE_LABEL,
        "strict": True,
        "semantics_version": rt.EXECUTION_VERIFIER_SEMANTICS_VERSION,
        "counts": counts,
        "override": None,
    }
    if not blocked:
        return summary

    detail = _format_execution_findings(findings, staged_batch)
    _raise_execution_gate_failure(counts, staged_batch, detail, override)
    summary["override"] = {
        "reason": override,
        "waived_inconclusive": counts["inconclusive"],
    }
    return summary
