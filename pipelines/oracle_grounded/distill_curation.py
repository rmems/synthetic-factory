#!/usr/bin/env python3
"""Validator stamps and the fail-closed curation gate (issue #78).

Nothing self-certifies. Producers write ``validation.status = "unvalidated"``;
only a validator stamps ``passed`` / ``failed``, with its own name and version
attached and the digest it was formed over. Curation eligibility is decided
on the caller's own findings and never on a validation block a record
shipped with, because nothing stored in a file can prove who wrote it.
"""

from __future__ import annotations

import copy
from typing import Any

from . import distill_blocks as blocks
from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def stamp_validation(
    record: dict[str, Any],
    *,
    validator: str,
    version: str,
    findings: list[str],
) -> dict[str, Any]:
    """Return a copy of ``record`` with a validator-owned verdict attached.

    The producer never calls this; only a validator does. The measured content
    digest is unchanged because ``record_digest`` excludes ``validation``, and
    the verdict carries the digest it was formed over so a stamp cannot be
    lifted from one record onto another.

    A stamp records that a validation happened; it is not evidence that one
    did. See :func:`curation_eligible`, which decides on the caller's own
    findings and never reads this block.
    """

    stamped = copy.deepcopy(record)
    stamped["validation"] = {
        "status": vocab.VALIDATION_FAILED if findings else vocab.VALIDATION_PASSED,
        "validator": {
            "name": validator,
            "version": version,
            "checked_at": envelope.utc_now_iso(),
            "validated_digest": envelope.record_digest(record),
        },
        "findings": list(findings),
    }
    return stamped


def curation_eligible(
    record: dict[str, Any], findings: list[str]
) -> tuple[bool, list[str]]:
    """Fail closed: only an authoritative oracle's measured, validated result.

    ``findings`` must come from the caller's *own* validation run over this
    record; an empty list means it validated clean. The ``validation`` block
    already sitting in the record is deliberately not consulted. Nothing stored
    in a file can prove who wrote it, so trusting it would let a producer stamp
    itself ``passed`` and walk straight through this gate.

    Structural validity alone never makes a record training-ready, and a
    ``reference_only`` oracle proves the pipeline shape without ever grounding
    a label.
    """

    reasons: list[str] = []
    if findings:
        reasons.append(f"VALIDATION_FINDINGS:{len(findings)}")
    reasons += _oracle_authority_reasons(record.get("oracle"))
    reasons += _measured_result_reasons(record.get("result"))
    reasons += _digest_reasons(record)
    return (not reasons), reasons


def _oracle_authority_reasons(oracle: Any) -> list[str]:
    if not isinstance(oracle, dict):
        return ["ORACLE_BLOCK_MISSING"]
    if oracle.get("authority") != vocab.AUTHORITY_AUTHORITATIVE:
        return [f"ORACLE_NOT_AUTHORITATIVE:{oracle.get('authority')!r}"]
    return []


def _measured_result_reasons(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return ["ORACLE_RESULT_MISSING"]
    if result.get("status") != vocab.RESULT_MEASURED:
        return [f"ORACLE_RESULT_NOT_MEASURED:{result.get('status')!r}"]
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    if not measurements:
        return ["ORACLE_RESULT_MISSING"]
    if not any(
        isinstance(item, dict) and item.get("measured") is True
        for item in measurements
    ):
        # A list of `measured: false` readings is a modelled result wearing
        # a measured status. Curating it would admit modelled labels.
        return ["NO_MEASURED_READING"]
    return []


def _digest_reasons(record: dict[str, Any]) -> list[str]:
    provenance = record.get("provenance")
    recorded_digest = (
        provenance.get("record_sha256") if isinstance(provenance, dict) else None
    )
    if not isinstance(recorded_digest, str) or not envelope.SHA256_RE.match(recorded_digest):
        # Without a digest there is nothing for check_digest to compare, so a
        # deleted digest would otherwise be a clean bypass of tamper detection.
        return ["RECORD_DIGEST_MISSING"]
    if blocks.check_digest(record, "record"):
        return ["RECORD_DIGEST_MISMATCH"]
    return []


def stamp_is_bound_to_content(record: dict[str, Any]) -> bool:
    """True when a stamped verdict was formed over this exact content.

    Catches a verdict lifted from one record onto another. It says nothing
    about *who* stamped it, which is why :func:`curation_eligible` does not
    rely on the stamp at all.
    """

    validation = record.get("validation")
    if not isinstance(validation, dict):
        return False
    validator = validation.get("validator")
    if not isinstance(validator, dict):
        return False
    return validator.get("validated_digest") == envelope.record_digest(record)


bind_import_twin(__name__)
