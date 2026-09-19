"""Strict-type reseal checks for captured-evidence provenance.

Split from test_hardware_parity_capture.py: the same recorded-capture
fixture, exercised on every field whose type is part of the sealed
provenance contract.
"""

import copy
import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import WHERE, CaptureCase  # noqa: E402

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402


class CaptureStrictness(CaptureCase):
    """Capture-source quantization, latency, repeat digests, and the
    q88-raw cross-checks — every digest resealed after each mutation."""

    def test_capture_source_quantization_types_are_strict(self):
        # A parsed record shares no sub-objects, so a Boolean smuggled into
        # the capture source's quantization (False where the documented type
        # is the integer 0) must not bind to the deployment through an
        # ordinary comparison's bool/int coercion.
        with tempfile.TemporaryDirectory() as tmp:
            record = json.loads(json.dumps(self._record(tmp)))
            source = record["oracle"]["deployment"]["capture"]["source"]
            self.assertEqual(source["quantization"]["saturated_parameter_count"], 0)
            source["quantization"]["saturated_parameter_count"] = False
            self._reseal_capture(record)
            errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "not the conversion stored with the capture" in error
                and "Q88_PROVENANCE_MISMATCH" in error
                for error in errors
            ),
            errors,
        )

    def test_conflicting_capture_quantization_blocks_are_rejected(self):
        # Retaining a contradictory payload conversion while the top-level
        # block matches the deployment must not validate as MATCH.
        with tempfile.TemporaryDirectory() as tmp:
            record = json.loads(json.dumps(self._record(tmp)))
            source = record["oracle"]["deployment"]["capture"]["source"]
            nested = json.loads(json.dumps(source["quantization"]))
            nested["fractional_bits"] = 4
            nested["total_bits"] = 12
            nested["step"] = 0.0625
            nested["saturated_parameter_count"] = 7
            source["payload"]["quantization"] = nested
            self._reseal_capture(record)
            errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "capture.source.quantization disagrees with"
                in error
                and "Q88_PROVENANCE_MISMATCH" in error
                for error in errors
            ),
            errors,
        )

    def test_capture_payload_latency_types_are_strict(self):
        # latency.measured is documented as a Boolean; the integer 1 in the
        # authenticated capture payload must not project onto the
        # deployment's True through bool/int coercion.
        with tempfile.TemporaryDirectory() as tmp:
            record = json.loads(json.dumps(self._record(tmp)))
            payload = record["oracle"]["deployment"]["capture"]["source"]["payload"]
            self.assertIs(payload["latency"]["measured"], True)
            payload["latency"]["measured"] = 1
            self._reseal_capture(record)
            errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "oracle.deployment.latency is not the observation stored in "
                "capture.source.payload" in error
                for error in errors
            ),
            errors,
        )

    def test_overflowing_float_in_capture_is_a_coded_diagnostic(self):
        # `1e9999` is an ordinary numeric token that float() turns into
        # infinity; outside the payload it used to crash generation with an
        # uncaught ValueError from digest() instead of a coded diagnostic.
        with tempfile.TemporaryDirectory() as tmp:
            scenario = hp.build_scenarios(steps=6)[0]
            adapter = self._capture_adapter(tmp, scenario)
            text = adapter.capture_path.read_text(encoding="utf-8")
            self.assertIn('"rev-b"', text)
            adapter.capture_path.write_text(
                text.replace('"rev-b"', "1e9999"), encoding="utf-8"
            )
            reloaded = oracle.RecordedCaptureAdapter(adapter.capture_path)
            status = reloaded.availability()
            self.assertFalse(status["available"])
            self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
            self.assertIn("non-finite JSON number", status["detail"])
            with self.assertRaises(oracle.OracleUnavailable):
                reloaded.run(scenario["model_float"], scenario["stimulus"], repeats=3)

    def test_non_object_capture_quantization_is_a_coded_diagnostic(self):
        # A truthy non-object quantization used to flow into build_record and
        # crash the generation CLI with an uncaught AttributeError; it must be
        # an OracleUnavailable diagnostic instead.
        with tempfile.TemporaryDirectory() as tmp:
            scenario = hp.build_scenarios(steps=6)[0]
            adapter = self._capture_adapter(tmp, scenario)
            raw = json.loads(adapter.capture_path.read_text(encoding="utf-8"))
            raw["quantization"] = ["truthy-but-not-an-object"]
            adapter.capture_path.write_text(json.dumps(raw), encoding="utf-8")
            reloaded = oracle.RecordedCaptureAdapter(adapter.capture_path)
            with self.assertRaises(oracle.OracleUnavailable) as caught:
                reloaded.run(scenario["model_float"], scenario["stimulus"], repeats=3)
            self.assertEqual(caught.exception.reason_code, "CAPTURE_UNREADABLE")
            records = hp.generate_records(
                round_number=1,
                steps=6,
                deployment_adapter=oracle.RecordedCaptureAdapter(
                    adapter.capture_path
                ),
                repeats=3,
            )
            record = records[0]
            self.assertIsNone(record["oracle"]["deployment"])
            self.assertEqual(
                record["oracle"]["unavailable"][0]["reason_code"],
                "CAPTURE_UNREADABLE",
            )
            # The diagnostic remains inconclusive historical data; validation
            # must never reopen its record-controlled capture path.
            self.assertEqual(hp.validate_record(record, WHERE), [])

    def test_repeat_digest_binds_the_complete_retained_observation(self):
        def mutate(repeat):
            repeat["membrane"]["trace"][0][0] += 0.25

        self._assert_repeat_observation_is_bound(mutate)

    def test_repeat_digest_includes_arithmetic_observations(self):
        def mutate(repeat):
            repeat["arithmetic"]["saturation_events"] += 1

        self._assert_repeat_observation_is_bound(mutate)

    def test_captured_q88_raw_must_correspond_to_the_float_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._with_q88_raw(self._record(tmp), 65)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any("raw/256" in error for error in errors), errors)

    def test_captured_q88_raw_outside_int16_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._with_q88_raw(self._record(tmp), 999999)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("signed Q8.8 int16 range" in error for error in errors),
                errors,
            )

    def test_malformed_nested_environment_and_bitstream_report_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mutate in (
                lambda record: record["oracle"].__setitem__("environment", "bad"),
                lambda record: record["oracle"]["deployment"].__setitem__(
                    "bitstream", "bad"
                ),
            ):
                with self.subTest(mutate=mutate):
                    record = self._record(tmp)
                    mutate(record)
                    errors = hp.validate_record(record, WHERE)
                    self.assertTrue(errors)

    def test_a_hardware_claim_is_never_unqualified(self):
        # The deployment traces of a physical run cannot be re-derived, so the
        # record must say so rather than reading as fully corroborated.
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            self.assertIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", record["result"]["reason_codes"]
            )
            view = hp.training_view(record)
            self.assertIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", view["reason_codes"]
            )
            self.assertFalse(view["oracle_complete"])
            self.assertTrue(view["parity_failed"])

    def test_reference_model_records_are_not_marked_unrederivable(self):
        for record in hp.generate_records(round_number=1, steps=4, repeats=2):
            self.assertNotIn(
                "DEPLOYMENT_TRACE_NOT_REDERIVABLE", record["result"]["reason_codes"]
            )

    def test_capture_taken_against_another_input_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            scenario = hp.build_scenarios(steps=6)[0]
            adapter = self._capture_adapter(tmp, scenario)
            # Generating with a different window changes the input fixture.
            records = hp.generate_records(
                round_number=1, steps=8, deployment_adapter=adapter, repeats=3
            )
            self.assertTrue(
                all(record["oracle"]["deployment"] is None for record in records)
            )
            self.assertEqual(hp.validate_records(records), [])


if __name__ == "__main__":
    unittest.main()
