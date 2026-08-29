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

from collections import Counter
import math

CONTRACT_VERSION = "1.0.0"

KIND_HARDWARE_PARITY = "hardware_parity"
KIND_NIR_EQUIVALENCE = "nir_equivalence"
RECORD_KINDS = (KIND_HARDWARE_PARITY, KIND_NIR_EQUIVALENCE)

DATASET_FOR_KIND = {
    KIND_HARDWARE_PARITY: "hardware-parity-spike-trajectories",
    KIND_NIR_EQUIVALENCE: "nir-cross-runtime-equivalence",
}

SCHEMA_VERSION_FOR_KIND = {
    KIND_HARDWARE_PARITY: "1.0.0",
    KIND_NIR_EQUIVALENCE: "1.0.0",
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
        "output_trace",
        "spike_count",
        "final_membrane",
        "roundtrip",
        "comparison",
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
        "DEPLOYMENT_TRACE_NOT_REDERIVABLE",
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
        "DIVERGENCE_EVENT_STREAM",
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


def reject_json_constant(value):
    """Reject Python's non-standard NaN/Infinity JSON extensions.

    Pass as ``json.loads(text, parse_constant=reject_json_constant)`` in both
    family readers so a record smuggling ``NaN``/``Infinity``/``-Infinity``
    is treated as a parse error rather than silently accepted with a value
    standards-compliant downstream JSON parsers cannot consume.
    """
    raise ValueError(f"non-standard JSON numeric constant {value}")


def _strict_mapping_equal(recorded, expected):
    """Same keys, and every value strictly equal."""
    return recorded.keys() == expected.keys() and all(
        strict_json_equal(recorded[key], expected[key]) for key in expected
    )


def _strict_sequence_equal(recorded, expected):
    """Same length, and every element strictly equal in order."""
    return len(recorded) == len(expected) and all(
        strict_json_equal(left, right) for left, right in zip(recorded, expected)
    )


def strict_json_equal(recorded, expected):
    """Compare JSON-shaped evidence without Python's bool/number coercions."""
    if type(recorded) is not type(expected):
        return False
    if isinstance(expected, float):
        return math.isfinite(recorded) and math.isfinite(expected) and recorded == expected
    if isinstance(expected, dict):
        return _strict_mapping_equal(recorded, expected)
    if isinstance(expected, list):
        return _strict_sequence_equal(recorded, expected)
    return recorded == expected


def _nonempty_str(value):
    return isinstance(value, str) and bool(value.strip())


def check_reason_codes(codes, where, field):
    """Every reason code must come from the shared vocabulary."""
    errors = []
    if not isinstance(codes, list):
        return [f"{where}: {field} must be an array"]
    for code in codes:
        if not isinstance(code, str):
            errors.append(f"{where}: {field} entries must be strings, got {code!r}")
        elif code not in REASON_CODES:
            errors.append(f"{where}: {field} has unknown reason code {code!r}")
    return errors


def _check_generator_produced(produced, where):
    """The generator may list what it authored, but never oracle output."""
    if not isinstance(produced, list) or not produced:
        return [f"{where}.generator.produced must list what the generator authored"]
    if any(item in ("result", "oracle", "measurement") for item in produced):
        return [
            f"{where}.generator.produced claims authorship of oracle output "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        ]
    return []


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
    errors += _check_generator_produced(generator.get("produced"), where)
    return errors


def _oracle_only_intruders(value):
    """Return oracle-only field names found at any depth of ``value``."""
    found = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            found.update(ORACLE_ONLY_KEYS.intersection(current))
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


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
    intruders = sorted(_oracle_only_intruders(prediction))
    if intruders:
        errors.append(
            f"{where}.candidate_prediction carries oracle-only fields {intruders} "
            f"[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    return errors


def _derived_membership_errors(derived, where, oracle_digests):
    """Which digests are referenced without evidence, and which are omitted."""
    errors = []
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


def _check_derived_digests(derived, where, oracle_digests):
    """result.derived_from must reproduce the ordered oracle evidence exactly."""
    if not isinstance(derived, list) or not derived:
        return [
            f"{where}.result.derived_from must list oracle output digests "
            "[RESULT_DIGEST_UNLINKED]"
        ]
    if oracle_digests is None:
        return []
    errors = _derived_membership_errors(derived, where, oracle_digests)
    if not strict_json_equal(derived, oracle_digests):
        errors.append(
            f"{where}.result.derived_from must exactly match the ordered oracle "
            f"evidence, including duplicate occurrences; expected "
            f"{oracle_digests!r}, got {derived!r} [RESULT_DIGEST_UNLINKED]"
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
    errors += _check_derived_digests(result.get("derived_from"), where, oracle_digests)
    return errors


def _check_claimed_not_real(claimed, where):
    """A synthetic record may never claim a real-world origin."""
    if not isinstance(claimed, str):
        return []
    lowered = claimed.strip().lower()
    if lowered == "real" or lowered.startswith(("real_", "real-", "real ")):
        return [
            f"{where}.provenance.claimed asserts a real-world origin "
            f"[PROVENANCE_CLAIMS_REAL]"
        ]
    return []


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
    errors += _check_claimed_not_real(provenance.get("claimed"), where)
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


def _is_positive_round(value):
    """A round is a true int >= 1; bool is not an acceptable round."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _check_envelope_identity(record, where):
    """id, record_kind, and the dataset/schema_version pinned to that kind."""
    errors = []
    if not _nonempty_str(record.get("id")):
        errors.append(f"{where}.id must be a non-empty string")
    kind = record.get("record_kind")
    if kind not in RECORD_KINDS:
        errors.append(f"{where}.record_kind must be one of {list(RECORD_KINDS)}")
    elif record.get("dataset") != DATASET_FOR_KIND[kind]:
        errors.append(
            f"{where}.dataset must be {DATASET_FOR_KIND[kind]!r} for record_kind {kind!r}"
        )
    schema_version = record.get("schema_version")
    if not _nonempty_str(schema_version):
        errors.append(f"{where}.schema_version must be a non-empty string")
    elif kind in SCHEMA_VERSION_FOR_KIND:
        expected_version = SCHEMA_VERSION_FOR_KIND[kind]
        if schema_version != expected_version:
            errors.append(
                f"{where}.schema_version must be {expected_version!r} for "
                f"record_kind {kind!r}, got {schema_version!r}"
            )
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


def check_envelope(record, where, oracle_digests=None):
    """Validate the shared envelope. Family validators add their own rules."""
    if not _is_object(record):
        return [f"{where}: record must be a JSON object [ENVELOPE_MALFORMED]"]
    errors = []
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        errors.append(f"{where}: envelope missing {missing} [ENVELOPE_MALFORMED]")
    errors += _check_envelope_identity(record, where)
    errors += check_generator(record.get("generator"), where)
    errors += _check_envelope_scenario(record, where)
    errors += check_candidate_prediction(record.get("candidate_prediction"), where)
    if not _is_object(record.get("oracle")):
        errors.append(f"{where}.oracle must be an object")
    errors += check_result(record.get("result"), where, oracle_digests)
    errors += check_provenance(record.get("provenance"), where)
    errors += check_validation_block(record.get("validation"), where)
    errors += _check_envelope_meta(record.get("meta"), where)
    return errors


# ── Training views ────────────────────────────────────────────────────

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
    return not any(code in ORACLE_INCOMPLETE_REASON_CODES for code in codes)


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


def _check_view_identity(record, view, where):
    """The view's key set and its identity/verdict fields must mirror the record."""
    errors = []
    missing = [key for key in TRAINING_VIEW_KEYS if key not in view]
    if missing:
        errors.append(
            f"{where}: training view missing {missing} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    for key in ("id", "record_kind", "dataset"):
        if not strict_json_equal(view.get(key), record.get(key)):
            errors.append(
                f"{where}: training view {key} must exactly match the source record "
                "[TRAINING_VIEW_HIDES_FAILURE]"
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
    return errors


def _side_reason_code_errors(raw_codes, where, field, malformed_message):
    """Well-formedness of one side's reason_codes, tagged for the view gate.

    Returns the string-only codes alongside the findings, so the caller can
    reuse them without re-filtering.
    """
    codes = (
        [code for code in raw_codes if isinstance(code, str)]
        if isinstance(raw_codes, list)
        else []
    )
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


def _check_view_provenance(record, view, where):
    """oracle_backed, execution_targets, and evidence_digests must all check out."""
    errors = []
    if view.get("oracle_backed") is not True:
        errors.append(
            f"{where}: training view must stay oracle-backed [RESULT_NOT_ORACLE_BACKED]"
        )
    expected_targets = _record_execution_targets(record)
    if expected_targets is None:
        errors.append(
            f"{where}: record execution targets are malformed and cannot support a "
            "training view [TRAINING_VIEW_HIDES_FAILURE]"
        )
    elif not strict_json_equal(view.get("execution_targets"), expected_targets):
        errors.append(
            f"{where}: training view execution targets must exactly match "
            f"validator-derived targets {expected_targets!r} "
            f"[TRAINING_VIEW_HIDES_FAILURE]"
        )
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


def _view_id_validity_errors(record_ids, view_ids, where):
    """Both sides must carry string IDs before they can be compared as sets."""
    errors = []
    invalid_view_ids = [view_id for view_id in view_ids if not isinstance(view_id, str)]
    if invalid_view_ids:
        errors.append(
            f"{where}: training view set contains invalid non-string view IDs "
            f"{invalid_view_ids!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    invalid_record_ids = [rid for rid in record_ids if not isinstance(rid, str)]
    if invalid_record_ids:
        errors.append(
            f"{where}: source record set contains invalid non-string IDs "
            f"{invalid_record_ids!r} [TRAINING_VIEW_HIDES_FAILURE]"
        )
    return errors


def _dropped_record_errors(record_ids, view_id_counts, where):
    """Every source record must still have a view."""
    # Only string record IDs are hashable-safe to check against view_id_counts;
    # a malformed ID (e.g. a list) is already reported by the validity pass and
    # must not reach `in` on a dict, which raises TypeError for unhashable keys.
    dropped = [rid for rid in record_ids if isinstance(rid, str) and rid not in view_id_counts]
    if not dropped:
        return []
    return [
        f"{where}: training view set drops records {dropped} "
        f"[TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _orphan_view_errors(view_id_counts, record_id_set, where):
    """Every view must have a record behind it."""
    orphans = sorted(vid for vid in view_id_counts if vid not in record_id_set)
    if not orphans:
        return []
    return [
        f"{where}: training view set contains views with no record behind them: "
        f"{orphans} [TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _duplicate_view_errors(view_id_counts, where):
    """A repeated view reweights the corpus away from what the oracles found."""
    duplicates = sorted(vid for vid, count in view_id_counts.items() if count > 1)
    if not duplicates:
        return []
    return [
        f"{where}: training view set repeats {duplicates}, which reweights the "
        f"corpus away from what the oracles found [TRAINING_VIEW_HIDES_FAILURE]"
    ]


def _view_id_mapping_errors(record_ids, view_ids, where):
    """Nothing dropped, nothing unsourced, nothing repeated."""
    record_id_set = {rid for rid in record_ids if isinstance(rid, str)}
    view_id_counts = Counter(vid for vid in view_ids if isinstance(vid, str))
    return (
        _dropped_record_errors(record_ids, view_id_counts, where)
        + _orphan_view_errors(view_id_counts, record_id_set, where)
        + _duplicate_view_errors(view_id_counts, where)
    )


def view_set_errors(records, views, where="training-view"):
    """The view set must be a faithful one-to-one image of the record set.

    Checking only that no record was dropped is not enough: duplicating the
    agreeable half of a corpus dilutes the failures just as effectively as
    deleting them, and a view with no record behind it is unsourced.
    """
    record_ids = [record.get("id") for record in records]
    view_ids = [view.get("id") for view in views]
    errors = _view_id_validity_errors(record_ids, view_ids, where)
    errors += _view_id_mapping_errors(record_ids, view_ids, where)
    return errors
