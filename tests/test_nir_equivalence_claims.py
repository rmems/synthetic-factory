"""Unfalsifiable and scrubbed claims in NIR-equivalence records.

Covers claims that cannot be checked, divergence that has been scrubbed out,
and the rule that a malformed record is rejected rather than crashing.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nir_equivalence_support import (  # noqa: E402
    WHERE,
)

import nir_equivalence as nir  # noqa: E402

class UnfalsifiableClaims(unittest.TestCase):
    """A runtime this validator cannot re-execute may never be marked executed."""

    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=6)

    def _claim_upstream_executed(self):
        """Dress the absent nir_rs up as having produced a real trace."""
        record = copy.deepcopy(self.records[0])
        real = next(
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        )
        ghost = next(
            entry for entry in record["oracle"]["runtimes"] if entry["runtime"] == "nir_rs"
        )
        ghost.update(
            {
                "status": nir.STATUS_EXECUTED,
                "outputs": copy.deepcopy(real["outputs"]),
                "output_digest": real["output_digest"],
                "roundtrip": copy.deepcopy(real["roundtrip"]),
            }
        )
        ghost.pop("reason_code", None)
        ghost.pop("detail", None)
        record["result"]["comparison"] = nir.compare_runtimes(
            record["scenario"], record["oracle"]["runtimes"]
        )
        verdict, codes = nir.verdict_for(record["result"]["comparison"])
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["derived_from"] = [
            entry["output_digest"]
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        ]
        return record

    def test_absent_upstream_runtime_cannot_be_claimed_as_executed(self):
        errors = nir.validate_record(self._claim_upstream_executed(), WHERE)
        self.assertTrue(
            any("re-execute" in error for error in errors), errors
        )

    def test_the_same_claim_is_caught_through_the_deep_layer(self):
        import check_records

        errors, _warnings, _kind, _id = check_records.check_record(
            self._claim_upstream_executed(), WHERE
        )
        self.assertTrue(any("re-execute" in error for error in errors))

    def test_unknown_runtime_class_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][0]["runtime_class"] = "trust_me"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("runtime_class" in error for error in errors))

    def test_executed_entry_missing_output_fields_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        del entry["outputs"]["spike_count"]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_runtime_inventory_cannot_drop_unavailable_oracles(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"] = [
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["runtime"] in {"nir_reference_v1", "nir_reference_v1_altorder"}
        ]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("complete ordered inventory" in error for error in errors))

    def test_duplicate_runtime_names_are_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][1] = copy.deepcopy(
            record["oracle"]["runtimes"][0]
        )
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("complete ordered inventory" in error for error in errors))

    def test_absent_upstream_runtime_cannot_claim_unsupported(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item for item in record["oracle"]["runtimes"] if item["runtime"] == "nir_rs"
        )
        entry["status"] = nir.STATUS_UNSUPPORTED
        entry["reason_code"] = "UNSUPPORTED_CONSTRUCT"
        entry["unsupported_node"] = "invented"
        entry["unsupported_type"] = "Invented"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("unavailable runtime" in error for error in errors), errors)

    def test_runtime_declarations_are_bound_to_the_implementation(self):
        for key, replacement in (
            ("conventions", {"reset": "fabricated"}),
            ("supported_types", ["Input", "Output"]),
        ):
            with self.subTest(key=key):
                record = copy.deepcopy(self.records[0])
                record["oracle"]["runtimes"][0][key] = replacement
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(any(key in error for error in errors), errors)


class ScrubbedDivergence(unittest.TestCase):
    """Divergence diagnostics must not be editable out of a record."""

    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=10)
        self.divergent = next(
            record
            for record in self.records
            if "DIVERGENCE_SPIKE_COUNT" in record["result"]["reason_codes"]
        )

    def test_scrubbing_spike_count_and_state_is_caught(self):
        record = copy.deepcopy(self.divergent)
        first, second = [
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        ][:2]
        second["outputs"]["spike_count"] = first["outputs"]["spike_count"]
        second["outputs"]["final_membrane"] = copy.deepcopy(
            first["outputs"]["final_membrane"]
        )
        record["result"]["comparison"] = nir.compare_runtimes(
            record["scenario"], record["oracle"]["runtimes"]
        )
        verdict, codes = nir.verdict_for(record["result"]["comparison"])
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        # The scrub really does delete diagnostics...
        self.assertNotIn("DIVERGENCE_SPIKE_COUNT", codes)
        # ...and re-execution catches it.
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("do not match a re-execution" in error for error in errors), errors
        )

    def test_forged_roundtrip_block_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["roundtrip"]["structure_digest"] = "sha256:" + "0" * 64
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("ROUNDTRIP_STRUCTURE_MISMATCH" in error for error in errors), errors
        )

    def test_forged_parse_failure_claim_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["roundtrip"]["canonical_stable"] = False
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_unsupported_diagnostic_is_rederived_from_the_exception(self):
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
        entry["unsupported_node"] = "invented"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("UNSUPPORTED_NOT_DIAGNOSED" in error for error in errors))


class MalformedRecordsDoNotCrash(unittest.TestCase):
    def setUp(self):
        self.record = nir.generate_records(round_number=1, steps=4)[0]

    def _assert_reports(self, mutate):
        record = copy.deepcopy(self.record)
        mutate(record)
        try:
            errors = nir.validate_record(record, WHERE)
        except Exception as exc:  # noqa: BLE001 - the point is that none escape
            self.fail(f"validation raised {type(exc).__name__}: {exc}")
        self.assertTrue(errors)

    def test_truthy_non_dict_oracle(self):
        self._assert_reports(lambda record: record.__setitem__("oracle", ["x"]))

    def test_executed_entry_with_empty_outputs(self):
        def mutate(record):
            entry = next(
                item
                for item in record["oracle"]["runtimes"]
                if item["status"] == nir.STATUS_EXECUTED
            )
            entry["outputs"] = {}

        self._assert_reports(mutate)

    def test_executed_entry_missing_output_digest_is_reported_not_raised(self):
        def mutate(record):
            entry = next(
                item
                for item in record["oracle"]["runtimes"]
                if item["status"] == nir.STATUS_EXECUTED
            )
            entry.pop("output_digest")

        self._assert_reports(mutate)

    def test_non_dict_runtime_entry(self):
        self._assert_reports(
            lambda record: record["oracle"]["runtimes"].append("not an object")
        )

    def test_missing_graph(self):
        self._assert_reports(lambda record: record["scenario"].pop("graph"))

    def test_nodes_array_is_reported_instead_of_crashing(self):
        self._assert_reports(
            lambda record: record["scenario"]["graph"].__setitem__("nodes", [])
        )

    def test_missing_stimulus_steps_is_reported_instead_of_crashing(self):
        self._assert_reports(
            lambda record: record["scenario"]["stimulus"].pop("steps")
        )

    def test_nonfinite_unavailable_diagnostic_is_reported_not_hashed(self):
        def mutate(record):
            entry = next(
                item
                for item in record["oracle"]["runtimes"]
                if item["status"] == nir.STATUS_UNAVAILABLE
            )
            entry["detail"] = float("nan")

        self._assert_reports(mutate)

    def test_wrong_nested_lineage_container_types_are_local_findings(self):
        mutations = (
            lambda record: record["oracle"]["runtimes"][2].__setitem__(
                "runtime", []
            ),
            lambda record: record["scenario"].__setitem__("id", []),
            lambda record: record["oracle"].__setitem__("input_fixture", ["bad"]),
            lambda record: record["result"].__setitem__(
                "derived_from", {"not": "an array"}
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self._assert_reports(mutate)

    def test_non_array_runtime_inventory_is_a_local_finding(self):
        for value in (1, True):
            with self.subTest(value=value):
                self._assert_reports(
                    lambda record, value=value: record["oracle"].__setitem__(
                        "runtimes", value
                    )
                )

    def test_nonfinite_nested_graph_value_is_reported_not_raised(self):
        self._assert_reports(
            lambda record: record["scenario"]["graph"].__setitem__(
                "dt_s", float("nan")
            )
        )

    def test_oversized_integer_stimulus_is_reported_not_raised(self):
        self._assert_reports(
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, 10**10_000
            )
        )



if __name__ == "__main__":
    unittest.main()
