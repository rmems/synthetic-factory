"""Record validation for pipelines/nir_equivalence.py.

Every rule that rejects a record whose claimed cross-runtime evidence does
not survive re-execution.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nir_equivalence_support import (  # noqa: E402
    WHERE,
    fixture_records as _fixture_records,
    rebuild_scenario as _rebuild_scenario,
    refresh_result as _refresh_result,
)

import nir_equivalence as nir  # noqa: E402
import oracle_contract as contract  # noqa: E402

class Validation(unittest.TestCase):
    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=6)
        self.mismatch = next(
            record
            for record in self.records
            if record["result"]["verdict"] == contract.VERDICT_MISMATCH
        )

    def _assert_lineage_rejected_everywhere(self, record):
        direct_errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("ordered runtime lineage" in error for error in direct_errors),
            direct_errors,
        )

        import check_records

        deep_errors, _warnings, _kind, _record_id = check_records.check_record(
            record, WHERE
        )
        self.assertTrue(
            any("ordered runtime lineage" in error for error in deep_errors),
            deep_errors,
        )

        views, view_errors = nir.build_training_views([record], source="tampered")
        self.assertEqual(views, [])
        self.assertTrue(
            any("ordered runtime lineage" in error for error in view_errors),
            view_errors,
        )

    def test_fixture_validates(self):
        self.assertEqual(nir.validate_records(_fixture_records()), [])

    def test_suppressed_divergence_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        record["result"]["verdict"] = contract.VERDICT_MATCH
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("DIVERGENCE_SUPPRESSED" in error for error in errors))

    def test_fabricated_output_trace_is_caught_by_re_execution(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["outputs"]["output_trace"][0][0] += 1.0
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("COMPARISON_MISMATCH" in error for error in errors))

    def test_forged_output_digest_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["output_digest"] = "sha256:" + "0" * 64
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_unavailable_runtime_may_not_carry_outputs(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNAVAILABLE
        )
        entry["outputs"] = {"output_trace": [[1.0]], "spike_events": [], "spike_count": 0}
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("UNAVAILABLE_RUNTIME_HAS_OUTPUT" in error for error in errors)
        )

    def test_unknown_runtime_status_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][0]["status"] = "probably_ran"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("RUNTIME_STATUS_UNKNOWN" in error for error in errors))

    def test_erased_unsupported_diagnostic_is_caught(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["result"]["verdict"] == contract.VERDICT_UNSUPPORTED
            )
        )
        record["result"]["comparison"]["unsupported"] = []
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_status_downgraded_to_hide_a_coverage_gap_is_caught(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if any(
                    entry["status"] == nir.STATUS_UNSUPPORTED
                    for entry in item["oracle"]["runtimes"]
                )
            )
        )
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNSUPPORTED
        )
        entry["status"] = nir.STATUS_UNAVAILABLE
        entry["reason_code"] = "RUNTIME_NOT_INSTALLED"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("UNSUPPORTED_NOT_DIAGNOSED" in error for error in errors))

    def test_tampered_graph_breaks_the_structure_digest(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["graph"]["edges"].append(["in", "out"])
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("STRUCTURE_DIGEST_MISMATCH" in error for error in errors))

    def test_tampered_stimulus_breaks_the_input_fixture(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["stimulus"]["events"][0][0] = 9.0
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("INPUT_FIXTURE_MISMATCH" in error for error in errors))

    def test_edited_spike_count_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        pair = record["result"]["comparison"]["output_parity"]["pairs"][0]
        pair["spike_count_b"] = pair["spike_count_a"]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("COMPARISON_MISMATCH" in error for error in errors))

    def test_every_pair_and_state_metric_is_bound_to_reexecution(self):
        mutations = (
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "max_abs_error", 99.0
            ),
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "max_abs_state_error", 99.0
            ),
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "shape_match", False
            ),
            lambda comparison: comparison["state_parity"].__setitem__("agree", False),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(self.records[0])
                mutate(record["result"]["comparison"])
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(
                    any("COMPARISON_MISMATCH" in error for error in errors), errors
                )

    def test_comparison_rejects_boolean_fields_retyped_as_integers(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["comparison"]["output_parity"]["agree"] = 1
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("COMPARISON_MISMATCH" in error for error in errors), errors
        )

    def test_oracle_fixture_and_identical_flag_are_load_bearing(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["input_fixture"]["sha256"] = "sha256:" + "0" * 64
        record["oracle"]["identical_input_fixture"] = False
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("INPUT_FIXTURE_MISMATCH" in error for error in errors))

    def test_fabricated_summary_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["summary"] = "all runtimes agree"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("result.summary" in error for error in errors), errors)

    def test_zero_execution_lineage_is_recomputed_from_diagnostics(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if not any(
                    entry["status"] == nir.STATUS_EXECUTED
                    for entry in item["oracle"]["runtimes"]
                )
            )
        )
        record["result"]["derived_from"] = ["fabricated"]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("derived_from" in error for error in errors), errors)

    def test_reversed_lineage_is_rejected_everywhere(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["derived_from"].reverse()
        self._assert_lineage_rejected_everywhere(record)

    def test_duplicate_lineage_occurrence_cannot_be_removed(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["scenario"]["id"] == "nir-feedforward-threshold"
            )
        )
        derived = record["result"]["derived_from"]
        duplicate_digests = [
            item["digest"]
            for item in derived
            if sum(other["digest"] == item["digest"] for other in derived) > 1
        ]
        self.assertTrue(duplicate_digests, derived)
        duplicate_digest = duplicate_digests[0]
        duplicate_index = next(
            index
            for index, item in enumerate(derived)
            if item["digest"] == duplicate_digest
        )
        derived.pop(duplicate_index)
        self._assert_lineage_rejected_everywhere(record)

    def test_partial_execution_lineage_includes_unsupported_diagnostic(self):
        record = next(
            item
            for item in self.records
            if item["scenario"]["id"] == "nir-partial-coverage-li"
        )
        expected_digests = []
        for entry in record["oracle"]["runtimes"]:
            if entry["status"] == nir.STATUS_EXECUTED:
                expected_digests.append(entry["output_digest"])
                continue
            if entry["status"] == nir.STATUS_UNSUPPORTED:
                diagnostic = {
                    "evidence_kind": "runtime_diagnostic",
                    "runtime": entry["runtime"],
                    "runtime_class": entry["runtime_class"],
                    "status": entry["status"],
                    "reason_code": entry["reason_code"],
                    "detail": entry["detail"],
                    "unsupported_node": entry["unsupported_node"],
                    "unsupported_type": entry["unsupported_type"],
                }
            else:
                capability = nir._runtime_capability(entry["runtime"])
                diagnostic = {
                    "evidence_kind": "runtime_capability",
                    "runtime": entry["runtime"],
                    "runtime_class": entry["runtime_class"],
                    "status": entry["status"],
                    "available": capability["available"],
                    "reason_code": capability["reason_code"],
                }
            expected_digests.append(nir.digest(diagnostic))

        lineage = nir._evidence_lineage(record["oracle"]["runtimes"])
        self.assertEqual(record["result"]["derived_from"], lineage)
        self.assertEqual(
            [(item["runtime"], item["status"]) for item in lineage],
            [
                (entry["runtime"], entry["status"])
                for entry in record["oracle"]["runtimes"]
            ],
        )
        self.assertEqual(
            [item["digest"] for item in lineage],
            expected_digests,
        )
        unsupported_index = next(
            index
            for index, entry in enumerate(record["oracle"]["runtimes"])
            if entry["status"] == nir.STATUS_UNSUPPORTED
        )
        self.assertEqual(
            record["result"]["derived_from"][unsupported_index]["digest"],
            expected_digests[unsupported_index],
        )

    def test_graph_class_is_bound_to_validated_graph(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["class"] = "coverage_gap"
        record["candidate_prediction"]["expected_verdict"] = contract.VERDICT_UNSUPPORTED
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("scenario.class" in error and "graph catalog" in error for error in errors),
            errors,
        )

    def test_rebuilt_record_cannot_rename_a_catalog_scenario(self):
        spec = nir.GRAPH_SPECS[0]
        scenario = nir.build_scenario(spec, steps=6)
        scenario["name"] = "forged scenario identity"
        record = _rebuild_scenario(scenario)

        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("scenario.name" in error and "graph catalog" in error for error in errors),
            errors,
        )
        view = nir.training_view(record)
        self.assertIn(spec["name"], view["prompt"])
        self.assertNotIn("forged scenario identity", view["prompt"])
        self.assertNotIn("forged scenario identity", view["completion"])
        self.assertEqual(view["graph_class"], spec["class"])

    def test_rebuilt_record_cannot_change_any_catalog_stimulus_field(self):
        mutations = {
            "name": lambda stimulus: stimulus.__setitem__("name", "forged-stimulus"),
            "encoding": lambda stimulus: stimulus.__setitem__("encoding", "forged"),
            "event": lambda stimulus: stimulus["events"][0].__setitem__(0, 0.25),
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field):
                scenario = nir.build_scenario(nir.GRAPH_SPECS[0], steps=6)
                mutate(scenario["stimulus"])
                stimulus = scenario["stimulus"]
                scenario["input_fixture"] = {
                    "name": stimulus["name"],
                    "steps": stimulus["steps"],
                    "channels": stimulus["channels"],
                    "sha256": nir.digest(stimulus["events"]),
                }
                record = _rebuild_scenario(scenario)
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(
                    any("scenario.stimulus" in error for error in errors),
                    errors,
                )

    def test_all_catalog_identity_fields_are_bound_to_scenario_id(self):
        mutations = (
            lambda record: record["scenario"].__setitem__("family", "forged"),
            lambda record: record["scenario"].__setitem__("description", "forged"),
            lambda record: record["intervention"].__setitem__("detail", "forged"),
            lambda record: record["candidate_prediction"].__setitem__(
                "hypothesis", "forged"
            ),
        )
        base = next(
            record
            for record in self.records
            if isinstance(record["intervention"], dict)
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(base)
                mutate(record)
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(
                    any("graph catalog" in error for error in errors), errors
                )

    def test_unavailable_detail_must_match_the_runtime_probe(self):
        record = copy.deepcopy(self.records[0])
        original_lineage = copy.deepcopy(record["result"]["derived_from"])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["runtime"] == "nir_rs"
        )
        entry["detail"] = "host-specific diagnostic wording"
        _refresh_result(record)
        self.assertEqual(record["result"]["derived_from"], original_lineage)
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("diagnostic detail does not match" in error for error in errors),
            errors,
        )

    def test_unavailable_reason_cannot_switch_and_self_rehash(self):
        record = copy.deepcopy(self.records[0])
        original_lineage = copy.deepcopy(record["result"]["derived_from"])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["runtime"] == "nir_rs"
        )
        actual_reason = nir._ALL_RUNTIME_BY_NAME["nir_rs"].availability()[
            "reason_code"
        ]
        alternate_reason = next(
            code for code in nir.UNAVAILABLE_REASON_CODES if code != actual_reason
        )
        entry["reason_code"] = alternate_reason
        entry["detail"] = "self-authenticated alternate capability"
        _refresh_result(record)
        self.assertEqual(record["result"]["derived_from"], original_lineage)

        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("does not match the runtime probe" in error for error in errors),
            errors,
        )

    def test_unavailable_diagnostic_rejects_an_unknown_reason_code(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["runtime"] == "nir_rs"
        )
        entry["reason_code"] = "FABRICATED_RUNTIME_FAILURE"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("unavailable reason_code" in error for error in errors), errors)

    def test_provenance_digest_is_bound_to_graph_and_stimulus(self):
        record = copy.deepcopy(self.records[0])
        record["provenance"]["scenario_sha256"] = "sha256:" + "0" * 64
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("scenario_sha256" in error for error in errors), errors)

    def test_family_identity_and_validator_provenance_are_bound(self):
        mutations = (
            lambda record: record.__setitem__("id", "another-scenario-r01"),
            lambda record: record["meta"].__setitem__("factory", "another-factory"),
            lambda record: record["generator"].__setitem__("name", "another-generator"),
            lambda record: record["provenance"].__setitem__("tool", "another-tool"),
            lambda record: record["provenance"].__setitem__(
                "tool_version", "999"
            ),
            lambda record: record["validation"].__setitem__(
                "validator", "another-validator"
            ),
            lambda record: record["validation"].__setitem__(
                "validator_version", "999"
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(self.records[0])
                mutate(record)
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(
                    any("ENVELOPE_MALFORMED" in error for error in errors), errors
                )

    def test_recorded_output_uses_strict_numeric_types(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        trace = entry["outputs"]["output_trace"]
        row_index, value_index = next(
            (row_index, value_index)
            for row_index, row in enumerate(trace)
            for value_index, value in enumerate(row)
            if value == 0.0 and not isinstance(value, bool)
        )
        trace[row_index][value_index] = False
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("COMPARISON_MISMATCH" in error for error in errors), errors)

    def test_roundtrip_booleans_use_strict_json_typing(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if isinstance(item.get("roundtrip"), dict)
            and item["roundtrip"].get("parse_ok") is True
        )
        entry["roundtrip"]["parse_ok"] = 1
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("ROUNDTRIP_STRUCTURE_MISMATCH" in error for error in errors),
            errors,
        )

    def test_unsupported_roundtrip_booleans_use_strict_json_typing(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["scenario"]["id"] == "nir-partial-coverage-li"
            )
        )
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNSUPPORTED
            and isinstance(item.get("roundtrip"), dict)
            and item["roundtrip"].get("parse_ok") is True
        )
        entry["roundtrip"]["parse_ok"] = 1
        per_runtime = record["result"]["comparison"]["parse_write_parity"][
            "per_runtime"
        ]
        per_runtime[entry["runtime"]]["parse_ok"] = 1
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("ROUNDTRIP_STRUCTURE_MISMATCH" in error for error in errors),
            errors,
        )



if __name__ == "__main__":
    unittest.main()
