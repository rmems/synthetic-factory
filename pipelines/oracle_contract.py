#!/usr/bin/env python3
"""Shared record contract for oracle-grounded parity datasets.

Both parity families (`hardware-parity-spike-trajectories` and
`nir-cross-runtime-equivalence`) emit records with the same envelope so that
one set of rules can enforce the epic's governing constraint:

    generators propose experiments; oracles produce truth

Concretely this module enforces four things that the family validators build
on top of:

* generator output and oracle output live in separate, differently-named
  fields, and the generator block must declare that it cannot certify a
  result (``may_certify_oracle_result: false``);
* a ``candidate_prediction`` may never carry the keys an oracle would fill,
  so generator-written scenario text cannot be mistaken for a measurement;
* ``result`` must be marked oracle-backed and name the oracle output digests
  it was derived from, and it must carry a verdict from a fixed vocabulary;
* a training view derived from a record cannot drop, soften, or relabel a
  parity failure.

Stdlib only. No JSON Schema library is available in this repository, so the
``schemas/*.schema.json`` files are documentation and these functions are the
enforcement.
"""

from __future__ import annotations

CONTRACT_VERSION = "1.0.0"

KIND_HARDWARE_PARITY = "hardware_parity"
KIND_NIR_EQUIVALENCE = "nir_equivalence"
RECORD_KINDS = (KIND_HARDWARE_PARITY, KIND_NIR_EQUIVALENCE)

DATASET_FOR_KIND = {
    KIND_HARDWARE_PARITY: "hardware-parity-spike-trajectories",
    KIND_NIR_EQUIVALENCE: "nir-cross-runtime-equivalence",
}

# `match` and `mismatch` are the two evidence-bearing verdicts. `unsupported`
# means an oracle refused a construct on purpose (still evidence).
# `inconclusive` means no oracle pair executed -- never a pass.
VERDICT_MATCH = "match"
VERDICT_MISMATCH = "mismatch"
VERDICT_UNSUPPORTED = "unsupported"
VERDICT_INCONCLUSIVE = "inconclusive"
VERDICTS = (VERDICT_MATCH, VERDICT_MISMATCH, VERDICT_UNSUPPORTED, VERDICT_INCONCLUSIVE)
# Everything that is not a clean match is a parity failure for view purposes.
PASSING_VERDICTS = frozenset({VERDICT_MATCH})

# provenance.kind vocabulary is the repository-wide one from
# schemas/provenance.md. A genuine FPGA run is `hil`; a reference-model run is
# `simulated`. `real` is never emitted here, as everywhere else in the factory.
PROVENANCE_KINDS = ("designed", "simulated", "hil", "unknown")

# Fields only an oracle may fill. A generator's candidate_prediction that
# carries any of these is trying to author a measurement.
ORACLE_ONLY_KEYS = frozenset(
    {
        "spikes",
        "spike_events",
        "membrane",
        "measured_latency_ms",
        "latency",
        "parity",
        "parity_metrics",
        "outputs",
        "output_digest",
        "repeat_digests",
        "quantization",
        "bitstream",
        "hardware",
        "capture",
    }
)

REASON_CODES = frozenset(
    {
        # contract layer
        "ENVELOPE_MALFORMED",
        "GENERATOR_SELF_CERTIFIED",
        "GENERATOR_SUBSTITUTED_FOR_ORACLE",
        "RESULT_NOT_ORACLE_BACKED",
        "RESULT_DIGEST_UNLINKED",
        "VERDICT_UNKNOWN",
        "PROVENANCE_KIND_INVALID",
        "PROVENANCE_CLAIMS_REAL",
        "TRAINING_VIEW_HIDES_FAILURE",
        # hardware parity
        "HW_PROVENANCE_MISSING",
        "HW_TARGET_UNKNOWN",
        "INPUT_FIXTURE_MISMATCH",
        "Q88_PROVENANCE_MISSING",
        "Q88_PROVENANCE_MISMATCH",
        "PARITY_METRIC_MISMATCH",
        "PARITY_VERDICT_INCONSISTENT",
        "SPIKE_BITMAP_DISAGREEMENT",
        "ACTION_DISAGREEMENT",
        "MEMBRANE_DIVERGENCE",
        "QUANTIZATION_SATURATION",
        "REPEATABILITY_UNPROVEN",
        "LATENCY_NOT_MEASURED",
        "ORACLE_UNAVAILABLE",
        # NIR equivalence
        "NO_EXECUTED_RUNTIME_PAIR",
        "UNAVAILABLE_RUNTIME_HAS_OUTPUT",
        "RUNTIME_STATUS_UNKNOWN",
        "COMPARISON_MISMATCH",
        "DIVERGENCE_SUPPRESSED",
        "DIVERGENCE_RESET_CONVENTION",
        "DIVERGENCE_DELAY_SEMANTICS",
        "DIVERGENCE_RECURRENT_ORDER",
        "DIVERGENCE_NUMERIC_TOLERANCE",
        "DIVERGENCE_SPIKE_COUNT",
        "DIVERGENCE_INTERNAL_STATE",
        "RUNTIME_NOT_INSTALLED",
        "RUNTIME_ADAPTER_NOT_IMPLEMENTED",
        "RUNTIME_GRAPH_ERROR",
        "ROUNDTRIP_PARSE_FAILURE",
        "ROUNDTRIP_STRUCTURE_MISMATCH",
        "STRUCTURE_DIGEST_MISMATCH",
        "UNSUPPORTED_CONSTRUCT",
        "UNSUPPORTED_NOT_DIAGNOSED",
    }
)

ENVELOPE_KEYS = (
    "id",
    "record_kind",
    "dataset",
    "schema_version",
    "generator",
    "scenario",
    "intervention",
    "candidate_prediction",
    "oracle",
    "result",
    "provenance",
    "validation",
    "meta",
)


def _is_object(value):
    return isinstance(value, dict)


def _nonempty_str(value):
    return isinstance(value, str) and bool(value.strip())


def check_reason_codes(codes, where, field):
    """Every reason code must come from the shared vocabulary."""
    errors = []
    if not isinstance(codes, list):
        return [f"{where}: {field} must be an array"]
    for code in codes:
        if code not in REASON_CODES:
            errors.append(f"{where}: {field} has unknown reason code {code!r}")
    return errors


def check_generator(generator, where):
    """The generator block, and the rule that it cannot certify itself."""
    errors = []
    if not _is_object(generator):
        return [f"{where}.generator must be an object"]
    for key in ("name", "model", "role"):
        if not _nonempty_str(generator.get(key)):
            errors.append(f"{where}.generator.{key} must be a non-empty string")
    if generator.get("may_certify_oracle_result") is not False:
        errors.append(
            f"{where}.generator.may_certify_oracle_result must be exactly false "
            "[GENERATOR_SELF_CERTIFIED]"
        )
    produced = generator.get("produced")
    if not isinstance(produced, list) or not produced:
        errors.append(f"{where}.generator.produced must list what the generator authored")
    elif any(item in ("result", "oracle", "measurement") for item in produced):
        errors.append(
            f"{where}.generator.produced claims authorship of oracle output "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    return errors


def check_candidate_prediction(prediction, where):
    """A prediction is a guess. It may not wear an oracle's clothes."""
    if prediction is None:
        return []
    if not _is_object(prediction):
        return [f"{where}.candidate_prediction must be an object or null"]
    errors = []
    if prediction.get("source") != "generator":
        errors.append(f"{where}.candidate_prediction.source must be 'generator'")
    if prediction.get("authoritative") is not False:
        errors.append(
            f"{where}.candidate_prediction.authoritative must be exactly false "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    intruders = sorted(ORACLE_ONLY_KEYS.intersection(prediction))
    if intruders:
        errors.append(
            f"{where}.candidate_prediction carries oracle-only fields {intruders} "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    return errors


def check_result(result, where, oracle_digests):
    """A result must be oracle-backed and traceable to oracle output."""
    errors = []
    if not _is_object(result):
        return [f"{where}.result must be an object"]
    if result.get("oracle_backed") is not True:
        errors.append(
            f"{where}.result.oracle_backed must be exactly true [RESULT_NOT_ORACLE_BACKED]"
        )
    verdict = result.get("verdict")
    if verdict not in VERDICTS:
        errors.append(
            f"{where}.result.verdict must be one of {list(VERDICTS)} [VERDICT_UNKNOWN]"
        )
    errors += check_reason_codes(result.get("reason_codes", []), where, "result.reason_codes")
    derived = result.get("derived_from")
    if not isinstance(derived, list) or not derived:
        errors.append(
            f"{where}.result.derived_from must list oracle output digests "
            "[RESULT_DIGEST_UNLINKED]"
        )
    elif oracle_digests is not None:
        unknown = [item for item in derived if item not in oracle_digests]
        if unknown:
            errors.append(
                f"{where}.result.derived_from references digests absent from oracle "
                f"output: {unknown} [RESULT_DIGEST_UNLINKED]"
            )
        missing = [item for item in oracle_digests if item not in derived]
        if missing:
            errors.append(
                f"{where}.result.derived_from omits executed oracle digests {missing} "
                f"[RESULT_DIGEST_UNLINKED]"
            )
    return errors


def check_provenance(provenance, where):
    """Repository-wide provenance vocabulary; never a `real` claim."""
    errors = []
    if not _is_object(provenance):
        return [f"{where}.provenance must be an object"]
    kind = provenance.get("kind")
    if kind not in PROVENANCE_KINDS:
        errors.append(
            f"{where}.provenance.kind must be one of {list(PROVENANCE_KINDS)} "
            f"[PROVENANCE_KIND_INVALID]"
        )
    claimed = provenance.get("claimed")
    if isinstance(claimed, str):
        lowered = claimed.strip().lower()
        if lowered == "real" or lowered.startswith(("real_", "real-", "real ")):
            errors.append(
                f"{where}.provenance.claimed asserts a real-world origin "
                f"[PROVENANCE_CLAIMS_REAL]"
            )
    for key in ("tool", "tool_version"):
        if not _nonempty_str(provenance.get(key)):
            errors.append(f"{where}.provenance.{key} must be a non-empty string")
    return errors


def check_validation_block(validation, where):
    errors = []
    if not _is_object(validation):
        return [f"{where}.validation must be an object"]
    for key in ("validator", "validator_version"):
        if not _nonempty_str(validation.get(key)):
            errors.append(f"{where}.validation.{key} must be a non-empty string")
    checks = validation.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append(f"{where}.validation.checks must list the checks that were applied")
    return errors


def check_envelope(record, where, oracle_digests=None):
    """Validate the shared envelope. Family validators add their own rules."""
    if not _is_object(record):
        return [f"{where}: record must be a JSON object [ENVELOPE_MALFORMED]"]
    errors = []
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        errors.append(f"{where}: envelope missing {missing} [ENVELOPE_MALFORMED]")
    if not _nonempty_str(record.get("id")):
        errors.append(f"{where}.id must be a non-empty string")
    kind = record.get("record_kind")
    if kind not in RECORD_KINDS:
        errors.append(f"{where}.record_kind must be one of {list(RECORD_KINDS)}")
    elif record.get("dataset") != DATASET_FOR_KIND[kind]:
        errors.append(
            f"{where}.dataset must be {DATASET_FOR_KIND[kind]!r} for record_kind {kind!r}"
        )
    if not _nonempty_str(record.get("schema_version")):
        errors.append(f"{where}.schema_version must be a non-empty string")
    errors += check_generator(record.get("generator"), where)
    if not _is_object(record.get("scenario")):
        errors.append(f"{where}.scenario must be an object")
    elif not _nonempty_str(record["scenario"].get("id")):
        errors.append(f"{where}.scenario.id must be a non-empty string")
    if record.get("intervention") is not None and not _is_object(record.get("intervention")):
        errors.append(f"{where}.intervention must be an object or null")
    errors += check_candidate_prediction(record.get("candidate_prediction"), where)
    if not _is_object(record.get("oracle")):
        errors.append(f"{where}.oracle must be an object")
    errors += check_result(record.get("result"), where, oracle_digests)
    errors += check_provenance(record.get("provenance"), where)
    errors += check_validation_block(record.get("validation"), where)
    meta = record.get("meta")
    if not _is_object(meta):
        errors.append(f"{where}.meta must be an object")
    else:
        if not isinstance(meta.get("round"), int) or isinstance(meta.get("round"), bool):
            errors.append(f"{where}.meta.round must be an integer")
        if not _nonempty_str(meta.get("factory")):
            errors.append(f"{where}.meta.factory must be a non-empty string")
    return errors


# ── Training views ────────────────────────────────────────────────────

TRAINING_VIEW_KEYS = (
    "id",
    "record_kind",
    "dataset",
    "verdict",
    "parity_failed",
    "reason_codes",
    "oracle_backed",
    "execution_targets",
    "evidence_digests",
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
    return {
        "id": record.get("id"),
        "record_kind": record.get("record_kind"),
        "dataset": record.get("dataset"),
        "prompt": prompt,
        "completion": completion,
        "verdict": verdict,
        "parity_failed": verdict not in PASSING_VERDICTS,
        "reason_codes": list(result.get("reason_codes", [])),
        "oracle_backed": result.get("oracle_backed"),
        "execution_targets": list(execution_targets),
        "evidence_digests": list(result.get("derived_from", [])),
    }


def training_view_errors(record, view, where):
    """Reject a training view that softens, drops, or relabels a failure."""
    if not _is_object(view):
        return [f"{where}: training view must be an object [TRAINING_VIEW_HIDES_FAILURE]"]
    errors = []
    missing = [key for key in TRAINING_VIEW_KEYS if key not in view]
    if missing:
        errors.append(
            f"{where}: training view missing {missing} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    result = record.get("result") or {}
    verdict = result.get("verdict")
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
    record_codes = set(result.get("reason_codes", []))
    view_codes = set(view.get("reason_codes") or [])
    if record_codes - view_codes:
        errors.append(
            f"{where}: training view drops reason codes {sorted(record_codes - view_codes)} "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        )
    if view.get("oracle_backed") is not True:
        errors.append(
            f"{where}: training view must stay oracle-backed [RESULT_NOT_ORACLE_BACKED]"
        )
    if not view.get("execution_targets"):
        errors.append(
            f"{where}: training view must name the execution targets it rests on "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        )
    if not view.get("evidence_digests"):
        errors.append(
            f"{where}: training view must carry evidence digests [RESULT_DIGEST_UNLINKED]"
        )
    return errors


def view_set_errors(records, views, where="training-view"):
    """Every record must survive into the view set. No silent filtering."""
    errors = []
    record_ids = [record.get("id") for record in records]
    view_ids = [view.get("id") for view in views]
    dropped = [rid for rid in record_ids if rid not in set(view_ids)]
    if dropped:
        errors.append(
            f"{where}: training view set drops records {dropped} "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors
