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
)

import nir_equivalence as nir  # noqa: E402
from oracle_grounded import parity_contract as contract  # noqa: E402

class Validation(unittest.TestCase):
    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=6)
        self.mismatch = next(
            record
            for record in self.records
            if record["result"]["verdict"] == contract.VERDICT_MISMATCH
        )

    def test_fixture_validates(self):
        self.assertEqual(nir.validate_records(_fixture_records()), [])

    def test_omitted_catalog_provenance_stamps_are_rejected(self):
        record = copy.deepcopy(_fixture_records()[0])
        for key in (
            "generator",
            "generator_version",
            "catalog_digest",
            "catalog_authorship",
        ):
            record["provenance"].pop(key, None)
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("provenance identity" in error for error in errors),
            errors,
        )

    def test_falsified_catalog_digest_is_rejected(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["provenance"]["catalog_digest"] = "sha256:" + ("0" * 64)
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("provenance identity" in error for error in errors),
            errors,
        )

    def test_suppressed_divergence_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        record["result"]["verdict"] = contract.VERDICT_MATCH
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("DIVERGENCE_SUPPRESSED" in error for error in errors))

    def test_stale_unavailable_entry_is_rejected_when_the_runtime_is_present(self):
        # The available branch of the probe check used to return no error, so a
        # record could keep an upstream runtime labelled `unavailable` -- and
        # keep ORACLE_UNAVAILABLE -- after that runtime became present.
        from unittest import mock

        record = copy.deepcopy(_fixture_records()[0])
        entry = next(e for e in record["oracle"]["runtimes"] if e["runtime"] == "nir_rs")
        self.assertEqual(entry["status"], "unavailable")
        runtime = nir._ALL_RUNTIME_BY_NAME["nir_rs"]
        with mock.patch.object(runtime, "availability", return_value={"available": True}):
            errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("cannot be recorded as 'unavailable'" in error for error in errors), errors
        )

    def test_published_schemas_bound_the_round_like_the_validator(self):
        # parity_envelope requires meta.round >= 1, as validate_run does; a
        # schema accepting 0 or a negative round would let external producers
        # emit records this validator rejects.
        import json as json_module
        from pathlib import Path as PathType

        schemas = PathType(nir.__file__).resolve().parents[1] / "schemas"
        for name in ("nir-cross-runtime-v1.schema.json", "hardware-parity-v1.schema.json"):
            with self.subTest(schema=name):
                schema = json_module.loads((schemas / name).read_text(encoding="utf-8"))
                round_schema = schema["properties"]["meta"]["properties"]["round"]
                self.assertEqual(round_schema, {"type": "integer", "minimum": 1})

    def test_shorter_windows_are_refused_at_generation(self):
        # Below MINIMUM_STEPS the designed divergences have not happened yet, so
        # a batch of `match` verdicts would be written for scenarios whose
        # hypothesis is `mismatch`. The floor is measured: six is the first
        # window whose verdict set equals the default window's.
        import io
        import tempfile
        from contextlib import redirect_stderr
        from pathlib import Path as PathType

        from nir_equivalence_catalog import MINIMUM_STEPS

        default = sorted(
            (r["scenario"]["id"], r["result"]["verdict"]) for r in nir.generate_records()
        )
        floor = sorted(
            (r["scenario"]["id"], r["result"]["verdict"])
            for r in nir.generate_records(steps=MINIMUM_STEPS)
        )
        self.assertEqual(floor, default)
        self.assertIn("mismatch", {verdict for _, verdict in floor})
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as refused:
                nir.main(["generate", tmp, "--steps", str(MINIMUM_STEPS - 1)])
            self.assertEqual(refused.exception.code, 2)
            self.assertIn("[WINDOW_TOO_SHORT]", stderr.getvalue())
            self.assertEqual(list(PathType(tmp).rglob("*.jsonl")), [])

    def test_published_schema_declares_the_object_lineage_entries(self):
        # The schema is documentation for downstream ingestion; declaring
        # string lineage items while every record carries {runtime, status,
        # digest} objects would reject the whole family at ingestion even
        # though this validator accepts it.
        import json as json_module
        from pathlib import Path as PathType

        schema_path = (
            PathType(nir.__file__).resolve().parents[1]
            / "schemas"
            / "nir-cross-runtime-v1.schema.json"
        )
        schema = json_module.loads(schema_path.read_text(encoding="utf-8"))
        items = schema["properties"]["result"]["properties"]["derived_from"]["items"]
        self.assertEqual(items["type"], "object")
        self.assertEqual(sorted(items["required"]), ["digest", "runtime", "status"])
        allowed_statuses = set(items["properties"]["status"]["enum"])
        self.assertEqual(allowed_statuses, set(nir.RUNTIME_STATUSES))
        for record in _fixture_records():
            for entry in record["result"]["derived_from"]:
                self.assertEqual(
                    sorted(entry.keys()), ["digest", "runtime", "status"]
                )
                self.assertIsInstance(entry["runtime"], str)
                self.assertIsInstance(entry["digest"], str)
                self.assertIn(entry["status"], allowed_statuses)

    def test_oracle_pairing_is_bound_to_the_canonical_value(self):
        # `pairing` is execution-facing oracle metadata: free text here could
        # advertise an execution the runtime entries never ran.
        record = copy.deepcopy(self.records[0])
        record["oracle"]["pairing"] = "an FPGA physically executed this graph"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "oracle.pairing" in error and "ENVELOPE_MALFORMED" in error
                for error in errors
            ),
            errors,
        )

    def test_catalog_mismatched_graph_is_never_executed(self):
        # The graph is record-controlled and the interpreters allocate state
        # proportional to declared node sizes and delay depths, so a graph
        # whose digest already failed the catalog binding must be rejected
        # before re-execution, not merely after it returns.
        record = copy.deepcopy(
            next(
                item
                for item in _fixture_records()
                if "Delay" in {
                    node.get("type")
                    for node in item["scenario"]["graph"]["nodes"].values()
                }
            )
        )
        delay = next(
            node
            for node in record["scenario"]["graph"]["nodes"].values()
            if node.get("type") == "Delay"
        )
        delay["delay"] = 10**9
        delay["size"] = 10**9

        original = nir._reexecute_in_repo_runtimes
        calls = []

        def sentinel(*args, **kwargs):
            # Never run the real interpreters here: with the gate broken the
            # inflated buffer would exhaust memory instead of failing fast.
            calls.append(args)
            return []

        nir._reexecute_in_repo_runtimes = sentinel
        try:
            errors = nir.validate_record(record, WHERE)
        finally:
            nir._reexecute_in_repo_runtimes = original
        self.assertEqual(calls, [], "re-execution ran on a catalog-failed graph")
        self.assertTrue(
            any("STRUCTURE_DIGEST_MISMATCH" in error for error in errors), errors
        )

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

    def test_output_digest_identifies_internal_state(self):
        # The unusual-but-valid scenario ends with the same output trace and
        # spike events on both runtimes while their final membrane states
        # differ (the record reports DIVERGENCE_INTERNAL_STATE). The digest
        # covers the complete retained outputs, so the two observations must
        # carry distinct evidence digests -- otherwise result.derived_from
        # cannot name the complete evidence behind the divergence, and a
        # content-addressed store keyed by these digests would collapse
        # distinct runtime observations.
        record = next(
            item
            for item in self.records
            if item["scenario"]["id"] == "nir-unusual-but-valid"
        )
        executed = [
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        ]
        self.assertEqual(len(executed), 2)
        behaviour_surfaces = {
            nir.canonical_json(
                {
                    "trace": entry["outputs"]["output_trace"],
                    "events": entry["outputs"]["spike_events"],
                }
            )
            for entry in executed
        }
        self.assertEqual(len(behaviour_surfaces), 1)  # identical behaviour surface
        membranes = {
            nir.canonical_json(entry["outputs"]["final_membrane"])
            for entry in executed
        }
        self.assertGreater(len(membranes), 1)  # internal state differs
        digests = [entry["output_digest"] for entry in executed]
        self.assertEqual(len(set(digests)), len(digests))

    def test_tampered_final_membrane_breaks_the_output_digest(self):
        # `final_membrane` feeds the persisted comparison and attribution;
        # the digest must stop identifying outputs whose internal state was
        # edited after the fact.
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["scenario"]["id"] == "nir-unusual-but-valid"
            )
        )
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
            and item["outputs"]["final_membrane"]
        )
        node = next(iter(entry["outputs"]["final_membrane"]))
        entry["outputs"]["final_membrane"][node]["v"][0] += 1.0
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "output_digest does not identify the recorded outputs" in error
                for error in errors
            ),
            errors,
        )

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

if __name__ == "__main__":
    unittest.main()
