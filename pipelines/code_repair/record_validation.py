"""Structural and execution bindings for records crossing the rendering boundary."""
from __future__ import annotations

import re
import math
from typing import Any

from . import catalog as cat
from . import records as assembly
from . import verify
from . import vocabulary as cv
from ._contract import (
    ExactJSONFloat, bind_import_twin, check_provenance_publish, envelope, exact_fraction, oc,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _require(condition: bool) -> None:
    cv.refuse_when(not condition, cv.FINDING_RECORD_MALFORMED,
                   "record has invalid code-repair fields or evidence")


def _digest(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _fields(value: Any, names: str, kinds: tuple[type, ...] = (str,)) -> None:
    """Require named fields with exact types; bool is never a numeric field."""
    _require(isinstance(value, dict))
    for name in names.split():
        _require(type(value[name]) in kinds)


def _proposal_shape(record: dict) -> None:
    scenario = record['scenario']
    _fields(scenario, 'record_kind task_specification language')
    source = scenario['source']
    _fields(source, 'program_id family module_sha256')
    _fields(source['upstream'], 'repository commit path file_sha256 function license')
    span = source['upstream']['line_span']
    _require(isinstance(span, list) and len(span) == 2)
    # Exact ints reject bool and subclasses in source coordinates.
    _require(all(type(n) is int and n > 0 for n in span))  # pylint: disable=unidiomatic-typecheck
    _fields(record['candidate_prediction'], 'method')
    actual = (scenario['task_specification'], scenario['language'], scenario['record_kind'],
              record['candidate_prediction']['method'])
    _require(actual == (cv.TASK_SPECIFICATION, cv.LANGUAGE, cv.RECORD_KIND, cv.REPAIR_METHOD))
    public = scenario['public_tests']
    _fields(public, 'kind')
    _require(isinstance(public['examples'], list))
    for example in public['examples']:
        _fields(example, 'example_id source want')


def _intervention_shape(intervention: dict) -> None:
    _fields(intervention, 'kind operator variant')
    _fields(intervention, 'draw_index', (int,))
    _require(0 <= intervention['draw_index'] < cv.MAX_COUNT)
    site = intervention['site']
    _fields(site, 'node original_text replacement_text')
    _fields(site, 'start_byte end_byte lineno col_offset node_lineno node_col_offset '
                  'node_end_lineno node_end_col_offset op_index', (int,))


def _configuration_shape(oracle: dict) -> None:
    identity = (oracle['name'], oracle['type'], oracle['implementation'], oracle['version'],
                oracle['authority'])
    _require(identity == (cv.ORACLE_NAME, cv.ORACLE_TYPE, cv.ORACLE_IMPLEMENTATION,
                          cv.ORACLE_VERSION, oc.AUTHORITY_AUTHORITATIVE))
    _require(oracle["commit"] is assembly.ORACLE_COMMIT)
    configuration = oracle['configuration']
    _fields(configuration, 'timeout_s', (int, float, ExactJSONFloat))
    timeout = configuration['timeout_s']
    _require(0 < timeout <= cv.MAX_TIMEOUT_S and math.isfinite(timeout))
    _require(0 < exact_fraction(timeout) <= exact_fraction(cv.MAX_TIMEOUT_S))
    _fields(configuration, 'isolation')
    _require(configuration["isolation"] == assembly.ORACLE_ISOLATION)
    _fields(configuration['limits'], 'cpu_s address_space_mib file_size_kib', (int,))
    hidden = configuration['hidden_check']
    _fields(hidden, 'reference_function', (str, type(None)))
    _require(isinstance(hidden['cases'], list))
    for case in hidden['cases']:
        _fields(case, 'args want')
    _fields(oracle['fingerprint'], 'python harness_sha256')
    _fields(oracle['fingerprint'], 'implementation platform', (str, type(None)))
    _fields(oracle['fingerprint'], 'limits_applied', (bool, type(None)))


def _examples(record: dict[str, Any]) -> tuple[cat.Example, ...]:
    scenario = record["scenario"]
    text = scenario["broken_program"]["files"][cv.PROGRAM_FILENAME]
    function = scenario["source"]["upstream"]["function"]
    _require(isinstance(text, str) and isinstance(function, str))
    return cat.examples_of(text, function)


def _row_shape(row: Any, prefix: str) -> None:
    _require(isinstance(row, dict))
    _require(isinstance(row["id"], str)
             and re.fullmatch(prefix + r":(?:0|[1-9][0-9]*)", row["id"]) is not None)
    _require(row["status"] in (cv.ROW_SUCCESS, cv.ROW_FAIL, cv.ROW_ERROR, cv.ROW_OBSERVED))
    if prefix == cv.SUITE_PUBLIC:
        _require(all(field in row for field in ("got", "truncated", "got_sha256")))
    _require(isinstance(row.get("got", ""), str))
    if "got" in row:
        # Exact bool rejects integer truthiness in persisted evidence.
        _require(type(row["truncated"]) is bool and _digest(row["got_sha256"]))  # pylint: disable=unidiomatic-typecheck
        if not row["truncated"]:
            _require(cat.sha256_text(row["got"]) == row["got_sha256"])


def _phase_limits_are_valid(block: dict[str, Any]) -> bool:
    if block["status"] != cv.PHASE_OK:
        return True
    if not block["load_ok"]:
        return True
    return block["limits_applied"] is True


def _suite_shape(rows: Any, prefix: str) -> None:
    _require(isinstance(rows, list))
    for row in rows:
        _row_shape(row, prefix)
    ids = [row["id"] for row in rows]
    _require(len(set(ids)) == len(ids))


def _phase_shape(block: Any) -> None:
    if block is None:
        return
    _require(isinstance(block, dict))
    _require(block["status"] in (cv.PHASE_OK, cv.PHASE_TIMEOUT, cv.PHASE_HARNESS_ERROR))
    # Protocol booleans reject ints and subclasses at the persisted boundary.
    _require(type(block["load_ok"]) is bool and _digest(block["module_sha256"]))  # pylint: disable=unidiomatic-typecheck
    _require(block["limits_applied"] is None or type(block["limits_applied"]) is bool)  # pylint: disable=unidiomatic-typecheck
    _require(_phase_limits_are_valid(block))
    for suite in ("public", "hidden"):
        _suite_shape(block[suite], suite)
    _require(block["sha256"] == cat.sha256_text(oc.canonical_json(
        [block["public"], block["hidden"]])))


def _identity_shape(record: dict[str, Any]) -> None:
    scenario, result = record["scenario"], record["result"]
    repair = record["candidate_prediction"]["predicted_repair"]
    hidden = record["oracle"]["configuration"]["hidden_check"]
    for digest in (scenario["source"]["module_sha256"], scenario["broken_program"]["sha256"],
                   repair["sha256"], result["broken_sha256"], result["repaired_sha256"]):
        _require(_digest(digest))
    _require(hidden["kind"] in cv.REFERENCE_KINDS)
    _require(hidden["reference_sha256"] is None or _digest(hidden["reference_sha256"]))
    lineage = record["provenance"]["split_lineage"]
    _require(isinstance(lineage["lineage_id"], str))
    _require(lineage["group_id"] is None or isinstance(lineage["group_id"], str))
    _require(lineage["split"] is None or isinstance(lineage["split"], str))


def _provenance_shape(provenance: dict) -> None:
    """Bind the emitter-owned identity, leaving generic provenance metadata alone."""
    expected = {
        'producer': cv.PRODUCER, 'source_kind': cv.SOURCE_KIND, 'oracle_run': cv.ORACLE_RUN,
        'actors': {
            cv.ROLE_TASK_AUTHOR: assembly._actor(
                cv.ROLE_TASK_AUTHOR, cv.GENERATOR_NAME, cv.GENERATOR_VERSION),
            cv.ROLE_SOLVER: assembly._actor(cv.ROLE_SOLVER, cv.SOLVER_NAME, cv.GENERATOR_VERSION),
            cv.ROLE_ORACLE_CERTIFIER: assembly._actor(
                cv.ROLE_ORACLE_CERTIFIER, cv.ORACLE_NAME, cv.ORACLE_VERSION),
        },
    }
    _require(all(provenance.get(key) == value for key, value in expected.items()))


def _envelope_shape(record: Any) -> None:
    _require(isinstance(record, dict))
    _require(record.get("family") == cv.FAMILY)
    where = str(record.get("id", "record"))
    _require(not (oc.check_envelope(record, where) + oc.check_digest(record, where)))
    _require(not check_provenance_publish(record, where))
    _provenance_shape(record['provenance'])


def _result_shape(result: dict[str, Any]) -> None:
    _require(result["outcome"] in cv.OUTCOMES)
    _require(result["oracle_status"] in cv.ORACLE_STATUSES)
    reason_codes = result["reason_codes"]
    _require(isinstance(reason_codes, list))
    _require(all(code in cv.REASON_CODE_SET for code in reason_codes))


def _public_failure_shape(result: dict[str, Any], examples: tuple[cat.Example, ...]) -> None:
    valid_ids = {example.example_id for example in examples}
    evidence = result["public_failure_evidence"]
    _require(isinstance(evidence, list))
    # Exact int rejects bool and integer subclasses in omission accounting.
    _require(type(result["public_failure_omitted"]) is int)  # pylint: disable=unidiomatic-typecheck
    _require(result["public_failure_omitted"] >= 0)
    for entry in evidence:
        _require(isinstance(entry, dict))
        _require(entry["example_id"] in valid_ids)
        _require(all(isinstance(entry[key], str) for key in ("source", "want", "got")))
        # Exact bool keeps each serialized truncation flag canonical.
        _require(type(entry["truncated"]) is bool)  # pylint: disable=unidiomatic-typecheck


def _phase_blocks_shape(result: dict[str, Any]) -> None:
    blocks = result["phases"]
    _require(set(blocks) == set(cv.PHASES))
    for block in blocks.values():
        _phase_shape(block)
    _require(blocks[cv.PHASE_ORIGINAL] is not None)
    _require(result["evidence_sha256"] == verify.result_hash(blocks))


def _render_inputs_shape(record: dict[str, Any]) -> None:
    repair_files = record["candidate_prediction"]["predicted_repair"]["files"]
    _require(isinstance(repair_files[cv.PROGRAM_FILENAME], str))
    _require(isinstance(record["scenario"]["task_specification"], str))
    hidden = record["oracle"]["configuration"]["hidden_check"]
    _require(isinstance(hidden["cases"], list))


def validate_shape(record: dict[str, Any]) -> None:
    """Turn malformed envelope/family/digest data into one declared refusal."""
    try:
        _envelope_shape(record)
        _proposal_shape(record)
        _intervention_shape(record['intervention'])
        _configuration_shape(record['oracle'])
        _identity_shape(record)
        result = record["result"]
        _result_shape(result)
        examples = _examples(record)
        _require(bool(examples))
        _public_failure_shape(result, examples)
        _phase_blocks_shape(result)
        _render_inputs_shape(record)
    except (KeyError, TypeError, ValueError, SyntaxError, AttributeError, RecursionError,
            envelope.ContractError) as exc:
        raise cv.RepairRefusal(cv.FINDING_RECORD_MALFORMED,
                               "record has malformed code-repair fields") from exc


def _complete_suites(phase: Any, name: str, public_count: int, hidden_count: int) -> bool:
    counts = (("public", 0 if name == "reference" else public_count), ("hidden", hidden_count))
    for suite, count in counts:
        actual = {row["id"] for row in getattr(phase, suite)}
        if actual != {f"{suite}:{i}" for i in range(count)}:
            return False
    return True


def _phase_runtime_contract(phase: Any) -> bool:
    rows_empty = not phase.public and not phase.hidden
    limits = phase.environment.get("limits_applied")
    if phase.status != cv.PHASE_OK:
        return not phase.load_ok and limits is None and rows_empty
    if not phase.load_ok:
        return limits is True and rows_empty
    return limits is True


def _phase_bindings_match(phases: verify.Phases, expected: dict[str, str],
                          public_count: int, hidden_count: int) -> bool:
    for name in cv.PHASES:
        phase = getattr(phases, name)
        if phase is None:
            continue
        if phase.module_sha256 != expected[name]:
            return False
        if not _phase_runtime_contract(phase):
            return False
        if phase.ok and not _complete_suites(phase, name, public_count, hidden_count):
            return False
    return True


def _phase_schedule_matches(phases: verify.Phases, context: verify.DecisionContext) -> bool:
    """Require exactly the phases that :mod:`generate` would have executed."""

    before_mutant = verify.Phases(
        phases.original,
        reference=phases.reference,
        original_repeat=phases.original_repeat,
    )
    mutant_runs = verify.pre_repair_problem(before_mutant, context) in (
        None, cv.REASON_MUTANT_HARNESS_ERROR,
    )
    through_mutant = verify.Phases(
        phases.original,
        mutant=phases.mutant,
        reference=phases.reference,
        original_repeat=phases.original_repeat,
    )
    repaired_runs = (
        mutant_runs and phases.mutant is not None
        and verify.pre_repair_problem(through_mutant, context) is None
    )
    expected = {
        cv.PHASE_ORIGINAL: True,
        cv.PHASE_ORIGINAL_REPEAT: phases.original.ok,
        cv.PHASE_MUTANT: mutant_runs,
        cv.PHASE_REPAIRED: repaired_runs,
        cv.PHASE_REFERENCE: context.reference_kind in cv.CERTIFYING_REFERENCE_KINDS,
    }
    return all((getattr(phases, name) is not None) is present
               for name, present in expected.items())


def verdict_matches(record: dict[str, Any]) -> bool:
    """Re-derive the stored decision and bind every executed source and suite."""
    result, scenario = record["result"], record["scenario"]
    phases = verify.phases_from_blocks(result["phases"])
    repair = record["candidate_prediction"]["predicted_repair"]
    hidden = record["oracle"]["configuration"]["hidden_check"]
    source_sha = scenario["source"]["module_sha256"]
    repaired_sha = cat.sha256_text(repair["files"][cv.PROGRAM_FILENAME])
    expected = {"original": source_sha, "original_repeat": source_sha,
                "mutant": cat.sha256_text(scenario["broken_program"]["files"][cv.PROGRAM_FILENAME]),
                "repaired": repaired_sha, "reference": hidden["reference_sha256"]}
    examples = _examples(record)
    if not _phase_bindings_match(phases, expected, len(examples), len(hidden["cases"])):
        return False
    if oc.canonical_json(result["measurements"]) != oc.canonical_json(assembly.measurements(phases)):
        return False
    context = verify.DecisionContext(
        hidden["kind"], repaired_sha == source_sha,
        verify.tests_tampered(examples, repair["files"][cv.PROGRAM_FILENAME],
                              scenario["source"]["upstream"]["function"]), len(hidden["cases"]))
    if not _phase_schedule_matches(phases, context):
        return False
    verdict = verify.decide(phases, context)
    actual = (result["status"], result["outcome"], result["oracle_status"], result["reason_codes"],
              repair["sha256"], result["repaired_sha256"], result["broken_sha256"],
              scenario["broken_program"]["sha256"])
    status = oc.RESULT_MEASURED if phases.original.ok else oc.RESULT_ABSTAINED
    wanted = (status, verdict.outcome, verdict.oracle_status, list(verdict.reason_codes),
              repaired_sha, repaired_sha, expected["mutant"], expected["mutant"])
    return actual == wanted


bind_import_twin(__name__)
