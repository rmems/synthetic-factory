"""Determinism-evidence and malformed-record gates for pipelines/hardware_parity.py.

Split from test_hardware_parity_validation.py: `repeat_digests` evidence and
the rule that a malformed record is rejected rather than crashing.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import WHERE  # noqa: E402

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402


class DeterminismEvidence(unittest.TestCase):
    """`determinism` is a claim; `repeat_digests` is the evidence for it."""

    @classmethod
    def setUpClass(cls):
        # Deterministic corpus; every test mutates a deep copy of the record.
        cls.record = hp.generate_records(round_number=1, steps=4, repeats=3)[0]

    def test_generated_record_is_internally_consistent(self):
        self.assertEqual(hp.validate_record(copy.deepcopy(self.record), WHERE), [])

    def test_repeatability_claim_must_match_its_digests(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeat_digests"] = [
            "sha256:aa",
            "sha256:bb",
            "sha256:cc",
        ]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_repeat_digests_reject_non_strings_without_crashing(self):
        for value in (7, {"digest": "sha256:" + "1" * 64}):
            with self.subTest(value=value):
                record = copy.deepcopy(self.record)
                record["oracle"]["deployment"]["repeat_digests"][1] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("canonical lowercase" in error for error in errors), errors
                )

    def test_repeat_count_must_match_the_digest_count(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeats"] = 500
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_boolean_cannot_impersonate_the_distinct_digest_count(self):
        # Python treats True == 1, and an unpaired record has no result.parity
        # to catch the substitution through a second strict comparison, so the
        # determinism check itself must require an exact non-Boolean integer.
        scenario = hp.build_scenarios(steps=4)[0]
        adapter = oracle.FpgaHardwareAdapter(env={})
        software, deployment, unavailable = hp.run_pair(scenario, adapter, repeats=2)
        record = hp.build_record(
            scenario,
            (software, deployment, unavailable),
            1,
            oracle.availability_report(env={})["spikenaut_fpga"],
        )
        self.assertEqual(hp.validate_record(copy.deepcopy(record), WHERE), [])
        record["oracle"]["software"]["determinism"]["distinct_digests"] = True
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "distinct_digests" in error and "REPEATABILITY_UNPROVEN" in error
                for error in errors
            ),
            errors,
        )

    def test_output_digest_must_appear_among_the_repeats(self):
        record = copy.deepcopy(self.record)
        record["oracle"]["software"]["repeat_digests"] = ["sha256:" + "1" * 64] * 3
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_reference_repeat_digests_are_rederived(self):
        record = copy.deepcopy(self.record)
        software = record["oracle"]["software"]
        forged = "sha256:" + "1" * 64
        software["repeat_digests"] = [software["output_digest"], forged, forged]
        software["determinism"]["distinct_digests"] = 2
        software["determinism"]["identical_repeats"] = False
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            software,
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["summary"] = hp._expected_summary(record)
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("must repeat the re-derived output_digest" in error for error in errors),
            errors,
        )

    def test_repeatability_block_is_recomputed(self):
        record = copy.deepcopy(self.record)
        record["result"]["parity"]["repeatability"]["hardware_repeatability_measured"] = (
            True
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("PARITY_METRIC_MISMATCH" in error for error in errors))

    def test_astronomically_large_repeats_does_not_attempt_the_allocation(self):
        # A record-declared `repeats` this large must not reach
        # `[output_digest] * repeats`; the mismatch with the actual digest
        # count (already reported) must be bound before that multiplication.
        record = copy.deepcopy(self.record)
        record["oracle"]["deployment"]["repeats"] = 10**9
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_software_determinism_meaning_is_bound_to_the_reference_adapter(self):
        # oracle.software is always a reference adapter (never a physical
        # capture), so its determinism.meaning cannot claim measured
        # hardware variability.
        record = copy.deepcopy(self.record)
        record["oracle"]["software"]["determinism"]["meaning"] = (
            "run-to-run variability observed during the recorded capture"
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors), errors)

    def test_deployment_determinism_meaning_is_bound_to_its_adapter(self):
        # A fixed-point reference deployment is a deterministic simulator.
        # Relabeling its repeats as measured hardware variability -- and
        # mirroring that text into result.parity.repeatability so the
        # recomputed mirror agrees with the claim -- must not validate a
        # simulator's repeats as a physical measurement.
        record = copy.deepcopy(self.record)
        lie = "run-to-run variability measured on the physical board"
        record["oracle"]["deployment"]["determinism"]["meaning"] = lie
        record["result"]["parity"]["repeatability"]["meaning"] = lie
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("oracle.deployment.determinism.meaning" in error for error in errors),
            errors,
        )


class MalformedRecordsDoNotCrash(unittest.TestCase):
    """A bad record must be reported, not raise and abort the whole scan."""

    @classmethod
    def setUpClass(cls):
        # Deterministic corpus; every test mutates a deep copy of the record.
        cls.record = hp.generate_records(round_number=1, steps=4, repeats=2)[0]

    def _assert_reports(self, mutate):
        record = copy.deepcopy(self.record)
        mutate(record)
        try:
            errors = hp.validate_record(record, WHERE)
        except Exception as exc:  # noqa: BLE001 - the point is that none escape
            self.fail(f"validation raised {type(exc).__name__}: {exc}")
        self.assertTrue(errors)

    def test_non_dict_deployment(self):
        self._assert_reports(
            lambda record: record["oracle"].__setitem__("deployment", "tampered")
        )

    def test_truthy_non_dict_oracle(self):
        self._assert_reports(lambda record: record.__setitem__("oracle", ["x"]))

    def test_ragged_spike_grid(self):
        def mutate(record):
            record["oracle"]["deployment"]["spikes"][0] = [1]

        self._assert_reports(mutate)

    def test_stimulus_steps_wildly_disagreeing_with_events_is_rejected(self):
        # A record-declared `steps` this large must be bound to the actual
        # event grid before it can reach build_scenario() as an allocation
        # bound.
        def mutate(record):
            record["scenario"]["stimulus"]["steps"] = 10**9

        self._assert_reports(mutate)

    def test_non_dict_software(self):
        self._assert_reports(
            lambda record: record["oracle"].__setitem__("software", 7)
        )

    def test_missing_model(self):
        self._assert_reports(lambda record: record["scenario"].pop("model_float"))

    def test_invalid_model_scalar_type(self):
        self._assert_reports(
            lambda record: record["scenario"]["model_float"].__setitem__(
                "neurons", None
            )
        )

    def test_nonfinite_model_and_stimulus_are_reported_not_raised(self):
        mutations = (
            lambda record: record["scenario"]["model_float"].__setitem__(
                "neurons", float("inf")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("nan")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("inf")
            ),
            lambda record: record["scenario"]["stimulus"]["events"][0].__setitem__(
                0, float("-inf")
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self._assert_reports(mutate)

    def test_excessive_nesting_is_record_local(self):
        malformed = copy.deepcopy(self.record)
        nested = []
        for _ in range(1500):
            nested = [nested]
        malformed["scenario"]["model_float"]["hostile_nesting"] = nested
        errors = hp.validate_records([malformed, copy.deepcopy(self.record)])
        self.assertTrue(any("record:1" in error for error in errors), errors)
        self.assertFalse(any("record:2" in error for error in errors), errors)

    def test_json_shaped_nested_type_errors_are_record_local(self):
        mutations = (
            lambda record: record["scenario"].__setitem__("input_fixture", True),
            lambda record: record["oracle"].__setitem__("input_fixture", 1),
            lambda record: record["oracle"]["deployment"].__setitem__(
                "quantization", True
            ),
            lambda record: record["result"].__setitem__("parity", {}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self._assert_reports(mutate)


if __name__ == "__main__":
    unittest.main()
