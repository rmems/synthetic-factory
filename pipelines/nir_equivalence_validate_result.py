#!/usr/bin/env python3
"""The verdict the record's own evidence supports, and the public entry points.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle import digest  # noqa: E402
from nir_equivalence_base import _strict_json_equal  # noqa: E402
from nir_equivalence_catalog import _catalog_stimulus  # noqa: E402
from nir_equivalence_compare import (  # noqa: E402
    _summarize,
    compare_runtimes,
    verdict_for,
)
from nir_equivalence_record import (  # noqa: E402
    _evidence_lineage,
    _evidence_scope,
)
from nir_equivalence_terms import (  # noqa: E402
    ORACLE_PAIRING,
    RECORD_KIND,
    VALIDATION_DATA_ERRORS,
    contract,
)
from nir_equivalence_validate_envelope import (  # noqa: E402
    _check_envelope_identity,
    _check_graph_structure,
)
from nir_equivalence_validate_replay import _reexecute_in_repo_runtimes  # noqa: E402
from nir_equivalence_validate_runtimes import _check_runtimes  # noqa: E402
from nir_equivalence_validate_stimulus import _check_stimulus_shape  # noqa: E402


def _check_stimulus_and_fixture(scenario, oracle, where):
    """Bind the stimulus and both input-fixture digests to the validated catalog.

    Returns ``(errors, stimulus_shape_valid)``; the caller must not attempt
    re-execution when ``stimulus_shape_valid`` is false.
    """
    stimulus = scenario.get("stimulus")
    errors = _check_stimulus_shape(stimulus, where)
    stimulus_shape_valid = not errors
    if not stimulus_shape_valid:
        return errors, stimulus_shape_valid
    expected_stimulus = _catalog_stimulus(scenario.get("id"), stimulus.get("steps"))
    if expected_stimulus is None or not _strict_json_equal(stimulus, expected_stimulus):
        errors.append(
            f"{where}: scenario.stimulus does not match the complete validated "
            f"catalog stimulus for {scenario.get('id')!r} "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    fixture = scenario.get("input_fixture") or {}
    oracle_fixture = oracle.get("input_fixture") or {}
    recomputed_fixture = digest(stimulus["events"])
    expected_fixture = {
        "name": stimulus["name"],
        "steps": stimulus["steps"],
        "channels": stimulus["channels"],
        "sha256": recomputed_fixture,
    }
    if not _strict_json_equal(fixture, expected_fixture):
        errors.append(
            f"{where}: scenario.input_fixture does not exactly describe the "
            "recorded stimulus [INPUT_FIXTURE_MISMATCH]"
        )
    if not _strict_json_equal(oracle_fixture, expected_fixture):
        errors.append(
            f"{where}: oracle.input_fixture does not exactly describe the executed "
            "stimulus [INPUT_FIXTURE_MISMATCH]"
        )
    if oracle.get("identical_input_fixture") is not True:
        errors.append(
            f"{where}: oracle.identical_input_fixture must be exactly true "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    return errors, stimulus_shape_valid


def _check_evidence_scope_field(oracle, where):
    recorded_runtimes = oracle.get("runtimes")
    runtimes = recorded_runtimes if isinstance(recorded_runtimes, list) else []
    if oracle.get("evidence_scope") != _evidence_scope(
        [entry for entry in runtimes if isinstance(entry, dict)]
    ):
        return [
            f"{where}: oracle.evidence_scope does not describe the runtimes that "
            "actually executed [COMPARISON_MISMATCH]"
        ]
    return []


def _validate_record(record, where):
    oracle = record.get("oracle") if isinstance(record, dict) else None
    lineage = None
    if isinstance(oracle, dict) and isinstance(oracle.get("runtimes"), list):
        lineage = _evidence_lineage(oracle["runtimes"])
    errors = contract.check_envelope(record, where, oracle_digests=lineage)
    if not isinstance(record, dict) or record.get("record_kind") != RECORD_KIND:
        return errors
    # A truthy non-dict `oracle` would sail past every `(x or {}).get(...)`
    # below and raise deep inside the comparison, so stop it here.
    if not isinstance(oracle, dict):
        return errors + [f"{where}: oracle must be an object [ENVELOPE_MALFORMED]"]
    errors += _oracle_pairing_errors(oracle, where)
    errors += _check_runtimes(record, where)
    errors += _result_lineage_errors(record, lineage, where)

    scenario = record.get("scenario") or {}
    if not isinstance(scenario, dict):
        return errors + [f"{where}: scenario must be an object [ENVELOPE_MALFORMED]"]

    errors += _check_envelope_identity(record, scenario, where)

    graph = scenario.get("graph")
    graph_errors, graph_shape_valid = _check_graph_structure(record, scenario, graph, where)
    errors += graph_errors

    stimulus_errors, stimulus_shape_valid = _check_stimulus_and_fixture(
        scenario, oracle, where
    )
    errors += stimulus_errors

    errors += _check_evidence_scope_field(oracle, where)

    # Never execute a graph that failed any structural or catalog check: the
    # graph (and its node sizes / delay depths) is record-controlled, and the
    # in-repo interpreters allocate state proportional to those declared
    # values. `graph_shape_valid` only says `structural_digest` could
    # traverse the object, so gating on it alone would let one JSONL entry
    # whose digest already failed the catalog binding exhaust memory before
    # its accumulated errors are ever returned.
    if graph_errors or not graph_shape_valid or not stimulus_shape_valid:
        return errors
    errors += _reexecute_in_repo_runtimes(record, where)
    if errors:
        return errors

    return errors + _recorded_comparison_errors(record, scenario, graph, oracle, where)


def _oracle_pairing_errors(oracle, where):
    """The pairing a record advertises must be the one this family measures."""
    # Execution-facing oracle metadata is validated, not trusted: free text
    # here could advertise an execution the runtime entries never ran.
    if oracle.get("pairing") == ORACLE_PAIRING:
        return []
    return [
        f"{where}: oracle.pairing must be the canonical {ORACLE_PAIRING!r} "
        "[ENVELOPE_MALFORMED]"
    ]


def _result_lineage_errors(record, lineage, where):
    """result.derived_from must name the complete rederived runtime lineage."""
    result = record.get("result")
    if not isinstance(result, dict) or lineage is None:
        return []
    if _strict_json_equal(result.get("derived_from"), lineage):
        return []
    return [
        f"{where}: result.derived_from must exactly match the rederived "
        "ordered runtime lineage, including duplicate occurrences "
        "[RESULT_DIGEST_UNLINKED]"
    ]


def _recorded_comparison_errors(record, scenario, graph, oracle, where):
    """The recorded result must reproduce the freshly recomputed comparison."""
    entries = oracle["runtimes"]
    recomputed = compare_runtimes(
        {"structure_digest": scenario.get("structure_digest"), "graph": graph}, entries
    )
    verdict, reason_codes = verdict_for(recomputed)
    result = record.get("result") or {}
    if not isinstance(result, dict):
        return [f"{where}: result must be an object [ENVELOPE_MALFORMED]"]
    errors = []
    recorded = result.get("comparison")
    if not isinstance(recorded, dict):
        errors.append(f"{where}: result.comparison must be an object [COMPARISON_MISMATCH]")
    elif not _strict_json_equal(recorded, recomputed):
        errors.append(
            f"{where}: result.comparison does not exactly match the re-executed "
            "runtime evidence [COMPARISON_MISMATCH]"
        )
    if result.get("verdict") != verdict:
        errors.append(
            f"{where}: result.verdict is {result.get('verdict')!r} but the recorded "
            f"outputs support {verdict!r} [DIVERGENCE_SUPPRESSED]"
        )
    if result.get("reason_codes") != reason_codes:
        errors.append(
            f"{where}: result.reason_codes records {result.get('reason_codes')!r} but "
            f"re-execution gives {reason_codes!r} [DIVERGENCE_SUPPRESSED]"
        )
    if recomputed["executed_count"] >= 2 and recomputed["output_parity"]["agree"] is False:
        if result.get("verdict") == contract.VERDICT_MATCH:
            errors.append(
                f"{where}: outputs diverge but the verdict claims a match "
                "[DIVERGENCE_SUPPRESSED]"
            )
    expected_summary = _summarize(scenario, recomputed, verdict)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the re-executed comparison "
            "[COMPARISON_MISMATCH]"
        )
    return errors


def validate_record(record, where):
    """Validate one record without letting malformed JSON abort a corpus scan."""
    try:
        return _validate_record(record, where)
    except VALIDATION_DATA_ERRORS as exc:
        return [
            f"{where}: record contains malformed evidence: {exc} "
            "[ENVELOPE_MALFORMED]"
        ]


def validate_records(records, source="record"):
    errors = []
    for index, record in enumerate(records, 1):
        errors += validate_record(record, f"{source}:{index}")
    return errors
