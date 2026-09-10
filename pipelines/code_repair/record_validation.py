"""Structural and execution bindings for records crossing the rendering boundary."""
from __future__ import annotations

import re
from typing import Any

from . import catalog as cat
from . import verify
from . import vocabulary as cv
from ._contract import bind_import_twin, envelope, oc

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _require(condition: bool) -> None:
    cv.refuse_when(not condition, cv.FINDING_RECORD_MALFORMED,
                   "record has invalid code-repair fields or evidence")


def _digest(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


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
    _require(isinstance(row.get("got", ""), str))
    if "got" in row:
        _require(type(row["truncated"]) is bool and _digest(row["got_sha256"]))
        if not row["truncated"]:
            _require(cat.sha256_text(row["got"]) == row["got_sha256"])


def _phase_shape(block: Any) -> None:
    if block is None:
        return
    _require(isinstance(block, dict))
    _require(block["status"] in (cv.PHASE_OK, cv.PHASE_TIMEOUT, cv.PHASE_HARNESS_ERROR))
    _require(type(block["load_ok"]) is bool and _digest(block["module_sha256"]))
    if block["status"] == cv.PHASE_OK and block["load_ok"]:
        _require(block["limits_applied"] is True)
    for suite in ("public", "hidden"):
        _require(isinstance(block[suite], list))
        for row in block[suite]:
            _row_shape(row, suite)
        ids = [row["id"] for row in block[suite]]
        _require(len(set(ids)) == len(ids))
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


def validate_shape(record: dict[str, Any]) -> None:
    """Turn malformed envelope/family/digest data into one declared refusal."""
    try:
        _require(isinstance(record, dict) and record.get("family") == cv.FAMILY)
        where = str(record.get("id", "record"))
        _require(not (oc.check_envelope(record, where) + oc.check_digest(record, where)))
        _identity_shape(record)
        result = record["result"]
        _require(result["outcome"] in cv.OUTCOMES and result["oracle_status"] in cv.ORACLE_STATUSES)
        _require(isinstance(result["reason_codes"], list)
                 and all(code in cv.REASON_CODE_SET for code in result["reason_codes"]))
        examples = _examples(record)
        _require(bool(examples))
        valid_ids = {example.example_id for example in examples}
        _require(isinstance(result["public_failure_evidence"], list))
        _require(type(result["public_failure_omitted"]) is int
                 and result["public_failure_omitted"] >= 0)
        for entry in result["public_failure_evidence"]:
            _require(isinstance(entry, dict) and entry["example_id"] in valid_ids)
            _require(all(isinstance(entry[key], str) for key in ("source", "want", "got")))
            _require(type(entry["truncated"]) is bool)
        blocks = result["phases"]
        _require(set(blocks) == set(cv.PHASES))
        for block in blocks.values():
            _phase_shape(block)
        _require(blocks[cv.PHASE_ORIGINAL] is not None)
        _require(result["evidence_sha256"] == verify.result_hash(blocks))
        _require(isinstance(record["candidate_prediction"]["predicted_repair"]["files"]
                            [cv.PROGRAM_FILENAME], str))
        _require(isinstance(record["scenario"]["task_specification"], str))
        _require(isinstance(record["oracle"]["configuration"]["hidden_check"]["cases"], list))
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError,
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


def _phase_bindings_match(phases: verify.Phases, expected: dict[str, str],
                          public_count: int, hidden_count: int) -> bool:
    for name in cv.PHASES:
        phase = getattr(phases, name)
        if phase is None:
            continue
        if phase.module_sha256 != expected[name]:
            return False
        if phase.ok and not _complete_suites(phase, name, public_count, hidden_count):
            return False
    return True


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
    context = verify.DecisionContext(
        hidden["kind"], repaired_sha == source_sha,
        verify.tests_tampered(examples, repair["files"][cv.PROGRAM_FILENAME],
                              scenario["source"]["upstream"]["function"]), len(hidden["cases"]))
    verdict = verify.decide(phases, context)
    actual = (result["outcome"], result["oracle_status"], result["reason_codes"],
              repair["sha256"], result["repaired_sha256"], result["broken_sha256"],
              scenario["broken_program"]["sha256"])
    wanted = (verdict.outcome, verdict.oracle_status, list(verdict.reason_codes),
              repaired_sha, repaired_sha, expected["mutant"], expected["mutant"])
    return actual == wanted


bind_import_twin(__name__)
