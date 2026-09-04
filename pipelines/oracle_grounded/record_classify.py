"""Classification: findings by layer, publishability, and the declared verdict.

``classify`` splits findings into layers so a rejected record still validates:

* ``envelope`` — structure, hashes, attribution, provenance. Always fatal:
  a record with an envelope finding is corrupt, not merely low quality.
* ``family`` — the family's own invariants and quality gate. These are what
  a record is *allowed* to fail, as long as it says so in its validation
  block and is filed as rejected.
* ``status`` — disagreement between the record's declared verdict and the
  recomputed one. Always fatal.
"""

from . import families, schema_validation
from .record_envelope import ENVELOPE_KEYS, SCHEMA_ID
from .record_generator_checks import _validate_generator_side
from .record_oracle_checks import _validate_oracle_side


def _fatal_envelope(findings):
    """A classification that stopped at a fatal envelope finding."""
    return {"envelope": findings, "family": [], "status": []}


def _structural_findings(record):
    """The fatal structural gate; a non-empty result stops classification."""
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    if record.get("schema") != SCHEMA_ID:
        return [f"schema must be {SCHEMA_ID!r}, got {record.get('schema')!r}"]
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        return [f"missing envelope keys: {', '.join(missing)}"]
    if record["family"] not in families.SPECS:
        return [f"unknown dataset family: {record['family']!r}"]
    return []


def _schema_layer_findings(record, check_declared_status):
    """Identity shape plus the checked-in JSON Schemas.

    The schemas are executable curation constraints, not documentation. This
    stays stdlib-only through the local subset validator.
    """
    findings = []
    if not isinstance(record.get("id"), str) or not record["id"]:
        findings.append("id must be a non-empty string")
    try:
        findings.extend(
            schema_validation.validate_record_schemas(
                record,
                record["family"],
                include_validation=check_declared_status,
            )
        )
    except Exception as exc:
        findings.append(f"record schema validation could not run: {type(exc).__name__}")
    return findings


def _family_layer_classification(record, check_declared_status):
    """The family layer, which a record is allowed to fail while saying so."""
    try:
        family_findings = families.spec_for(record["family"]).checks(record)
    except Exception as exc:
        return _fatal_envelope(
            [f"family checks could not run on this record: {type(exc).__name__}"]
        )
    status = _validate_declared_status(record, family_findings) if check_declared_status else []
    return {"envelope": [], "family": family_findings, "status": status}


def classify(record, require_named_runtime=False, check_declared_status=True, expected_commit=None):
    """Split findings into layers so a rejected record still validates."""
    structural = _structural_findings(record)
    if structural:
        return _fatal_envelope(structural)
    envelope = _schema_layer_findings(record, check_declared_status)
    if envelope:
        return _fatal_envelope(envelope)
    envelope.extend(_validate_generator_side(record))
    envelope.extend(_validate_oracle_side(record, require_named_runtime, expected_commit))
    if envelope:
        return _fatal_envelope(envelope)
    return _family_layer_classification(record, check_declared_status)


def validate_record(record, check_declared_status=True, require_named_runtime=False):
    """Flat list of findings. Empty means the record is acceptable as-is."""
    layers = classify(
        record,
        require_named_runtime=require_named_runtime,
        check_declared_status=check_declared_status,
    )
    findings = layers["envelope"] + layers["family"]
    if check_declared_status:
        findings = findings + layers["status"]
    return findings


def assess(record):
    """Run every check and produce the record's own validation block."""
    # The validation block is what this function is constructing.  Validate
    # every other schema and invariant now, then authenticate the completed
    # block when the record is read back through ``validate_record``.
    layers = classify(record, check_declared_status=False)
    findings = layers["envelope"] + layers["family"]
    spec = families.spec_for(record["family"])
    try:
        score = spec.score(record)
    except Exception:
        # A measurement in an unexpected shape cannot be scored. That is itself
        # reported by the family checks; scoring must not raise over it.
        score = None
    publishable, reason = publishability(record, findings)
    return {
        "status": "accepted" if not findings else "rejected",
        "reasons": findings,
        "checks": {
            "envelope": not layers["envelope"],
            "family_invariants": not layers["family"],
        },
        "candidate_prediction_correct": score,
        "publishable": publishable,
        "publishable_reason": reason,
    }


def publishability(record, findings=()):
    """Whether this record may be published as an authoritative measurement.

    A reference simulator is a real measurement of a small model, but it is not
    the runtime the issue names, so it never earns publication on its own.
    """
    oracle = record["oracle"]
    reasons = []
    if oracle["implementation"] != "named-runtime":
        unbound = oracle["availability"]["unbound"]
        reasons.append(
            "measured by a reference implementation, not by "
            f"{', '.join(unbound) if unbound else 'the named runtime'}; "
            "publication requires the named oracle to be bound"
        )
    if oracle["commit"] == "unknown":
        reasons.append("oracle commit could not be resolved")
    if oracle.get("dirty") is None:
        reasons.append(
            "oracle working-tree dirty state is unresolved; publication "
            "requires resolved provenance"
        )
    if findings:
        reasons.append("record failed validation")
    if reasons:
        return False, "; ".join(reasons)
    return (
        True,
        "measured through the named-runtime protocol with resolved stored "
        "provenance; the protocol does not provide external attestation",
    )


def _declared_verdict_findings(validation, findings_so_far):
    """The stored status, reasons, and layer checks must be the recomputed ones."""
    out = []
    expected_status = "rejected" if findings_so_far else "accepted"
    status = validation.get("status")
    if status != expected_status:
        out.append(
            f"validation.status is {status!r} but the recomputed status is {expected_status!r}"
        )
    expected_reasons = list(findings_so_far)
    if validation.get("reasons") != expected_reasons:
        # A rejected record is still evidence; its stated reason has to be the
        # exact deterministic finding sequence, or the rejection log is fiction.
        out.append(
            "validation.reasons do not match the recomputed findings: "
            f"stored {validation.get('reasons')!r}, recomputed {expected_reasons!r}"
        )
    expected_checks = {
        "envelope": True,
        "family_invariants": not findings_so_far,
    }
    if validation.get("checks") != expected_checks:
        out.append(
            "validation.checks do not match the recomputed validation layers: "
            f"stored {validation.get('checks')!r}, recomputed {expected_checks!r}"
        )
    return out


def _declared_outcome_findings(record, validation, findings_so_far):
    """The stored score and publishability must be the recomputed ones."""
    out = []
    spec = families.spec_for(record["family"])
    try:
        expected_score = spec.score(record)
    except Exception:
        expected_score = None
    if validation.get("candidate_prediction_correct") is not expected_score:
        out.append(
            "validation.candidate_prediction_correct does not match the "
            f"recomputed candidate score {expected_score!r}"
        )
    expected_publishable, expected_reason = publishability(record, findings_so_far)
    if validation.get("publishable") is not expected_publishable:
        out.append(
            f"validation.publishable is {validation.get('publishable')!r} but the "
            f"recomputed value is {expected_publishable!r}"
        )
    if validation.get("publishable_reason") != expected_reason:
        out.append(
            "validation.publishable_reason does not match the recomputed publishability decision"
        )
    return out


def _validate_declared_status(record, findings_so_far):
    validation = record.get("validation")
    if not isinstance(validation, dict):
        return ["validation must be an object"]
    return _declared_verdict_findings(validation, findings_so_far) + _declared_outcome_findings(
        record, validation, findings_so_far
    )
