"""Captured-evidence provenance for pipelines/hardware_parity.py.

Covers the recorded-capture replay path, physical-target claims, and the
training views derived from them.
"""

import copy
import json
import os
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import (  # noqa: E402
    PIPELINES,
    WHERE,
    fixture_records as _fixture_records,
)

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402
from oracle_grounded import parity_contract as contract  # noqa: E402

CAPTURE_MUTATIONS = (
    "bitstream_sha256",
    "truncate_spikes",
    "narrow_spikes",
    "invalid_spike_cell",
    "narrow_membrane",
)


def _mutated_spikes(software, mutations):
    """The reference spike grid, optionally damaged to exercise a rejection."""
    spikes = copy.deepcopy(software["spikes"])
    if mutations.get("truncate_spikes"):
        spikes = spikes[:-1]
    if mutations.get("narrow_spikes"):
        spikes = [row[:-1] for row in spikes]
    invalid_cell = mutations.get("invalid_spike_cell")
    if invalid_cell is not None:
        spikes[0][0] = invalid_cell
    return spikes


def _mutated_membrane(software, mutations):
    """The reference membrane trace, optionally narrowed."""
    membrane = copy.deepcopy(software["membrane"])
    if mutations.get("narrow_membrane"):
        membrane["trace"] = [row[:-1] for row in membrane["trace"]]
    return membrane


def _capture_payload(scenario, spikes, membrane):
    """A capture payload plus the retained repeats and their digests."""
    payload = {
        "spikes": spikes,
        "spike_events": oracle._spike_events(
            spikes, scenario["model_float"]["dt_ms"]
        ),
        "action": oracle._decode_action(
            spikes, scenario["model_float"]["action_labels"]
        ),
        "membrane": membrane,
        "arithmetic": {"format": "Q8.8", "saturation_events": 0},
        "latency": {"measured": True, "value_ms": 0.31},
    }
    repeat_output = {
        key: copy.deepcopy(payload[key])
        for key in (
            "spikes",
            "spike_events",
            "action",
            "membrane",
            "arithmetic",
        )
    }
    payload["repeat_outputs"] = [copy.deepcopy(repeat_output) for _ in range(3)]
    payload["repeat_digests"] = [
        oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
    ]
    return payload


class RecordedCapturePath(unittest.TestCase):
    """The `--capture` route must actually produce validatable records.

    It is also the one place where the deployment traces are *not*
    re-derivable, so these tests pin how that limitation is surfaced.
    """

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO test requires POSIX mkfifo")
    def test_capture_reader_rejects_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / "capture.fifo"
            os.mkfifo(fifo)
            script = (
                "import json,sys;"
                f"sys.path.insert(0, {str(PIPELINES)!r});"
                "from neuro_oracle import RecordedCaptureAdapter;"
                f"print(json.dumps(RecordedCaptureAdapter({str(fifo)!r}).availability()))"
            )
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        status = json.loads(result.stdout)
        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("not a regular file", status["detail"])

    def test_capture_reader_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "capture-target.json"
            target.write_text(
                json.dumps({"execution_target": oracle.TARGET_FPGA_HARDWARE}),
                encoding="utf-8",
            )
            link = root / "capture-link.json"
            link.symlink_to(target)
            status = oracle.RecordedCaptureAdapter(link).availability()

        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("not a regular file", status["detail"])

    def test_capture_reader_refuses_oversized_regular_files_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.json"
            with path.open("wb") as handle:
                handle.truncate(oracle.MAX_CAPTURE_BYTES + 1)
            status = oracle.RecordedCaptureAdapter(path).availability()

        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "CAPTURE_UNREADABLE")
        self.assertIn("limit", status["detail"])

    def _capture_adapter(self, tmp, scenario, **mutations):
        unknown = set(mutations) - set(CAPTURE_MUTATIONS)
        if unknown:
            raise TypeError(f"unknown capture mutations: {sorted(unknown)}")
        software = oracle.simulate_float(
            scenario["model_float"], scenario["stimulus"]
        )
        _, quantization = oracle.quantize_model(scenario["model_float"])
        payload = _capture_payload(
            scenario,
            _mutated_spikes(software, mutations),
            _mutated_membrane(software, mutations),
        )
        capture = {
            "execution_target": oracle.TARGET_FPGA_HARDWARE,
            "quantization": quantization,
            "hardware": {"revision": "rev-b", "board_serial": "SN-9"},
            "bitstream": {
                "sha256": mutations.get("bitstream_sha256") or "sha256:" + "b" * 64,
                "toolchain": "vendor 1.2",
            },
            "manifest": {
                "payload_sha256": oracle.digest(payload),
                "input_fixture_sha256": scenario["input_fixture"]["sha256"],
                "recorded_at": "2026-01-01T00:00:00Z",
            },
            "payload": payload,
        }
        path = Path(tmp) / "capture.json"
        path.write_text(json.dumps(capture), encoding="utf-8")
        return oracle.RecordedCaptureAdapter(path)

    def _record(self, tmp, **capture_kwargs):
        scenario = hp.build_scenarios(steps=6)[0]
        return hp.generate_records(
            round_number=1,
            steps=6,
            deployment_adapter=self._capture_adapter(
                tmp, scenario, **capture_kwargs
            ),
            repeats=3,
        )[0]

    def test_capture_derived_records_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(hp.validate_record(self._record(tmp), WHERE), [])

    def test_capture_derived_record_declares_hil_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._record(tmp)["provenance"]["kind"], "hil")

    def test_capture_evidence_cannot_be_relabelled_as_an_unknown_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = "plausible_vendor_driver"
            deployment["runtime_class"] = "physical_hardware"
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("unsupported adapter identity" in error for error in errors), errors
            )

    def test_capture_digest_chain_is_rechecked_from_stored_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["source"]["payload"][
                "spikes"
            ][0][0] ^= 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any("capture" in error.lower() for error in errors), errors)

    def test_capture_recorded_at_is_bound_to_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["recorded_at"] = (
                "1999-01-01T00:00:00Z"
            )
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_missing_capture_recorded_at_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"].pop("recorded_at", None)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_whitespace_only_recorded_at_does_not_bind(self):
        # A whitespace-only value matched on both sides must not validate as
        # bound provenance; `not recorded_at` alone only rejects "".
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["recorded_at"] = "   "
            record["oracle"]["deployment"]["capture"]["source"]["manifest"][
                "recorded_at"
            ] = "   "
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_lineage_includes_physical_provenance_digest(self):
        # Two captures with identical behavioural output but different
        # physical provenance must not collapse to the same result lineage.
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            derived = record["result"]["derived_from"]
            self.assertEqual(len(derived), 3, derived)
            record["result"]["derived_from"] = derived[:2]
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("RESULT_DIGEST_UNLINKED" in error for error in errors), errors
            )

    def test_physical_bitstream_requires_canonical_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, bitstream_sha256="sha256:" + "A" * 64)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("canonical lowercase" in error for error in errors), errors
            )

    def test_truncated_capture_window_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, truncate_spikes=True)
            self.assertFalse(record["result"]["parity"]["timing"]["comparable"])
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "spikes must have exactly 6 rows" in error
                    and "ENVELOPE_MALFORMED" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_spike_width_is_bound_to_neuron_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, narrow_spikes=True)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("spikes[0]" in error and "exactly 4 cells" in error for error in errors),
                errors,
            )

    def test_capture_spike_cells_are_exact_binary_integers(self):
        for cell in (True, 2, 0.5):
            with self.subTest(cell=cell), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp, invalid_spike_cell=cell)
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("exact integer 0 or 1" in error for error in errors), errors
                )

    def test_capture_membrane_width_is_bound_to_neuron_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, narrow_membrane=True)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "membrane.trace[0]" in error and "exactly 4 cells" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_action_and_events_must_encode_the_spike_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["action"]["counts"][0] += 1
            deployment["spike_events"][0]["neuron_id"] += 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any(".action does not decode" in error for error in errors), errors)
            self.assertTrue(
                any(".spike_events does not exactly" in error for error in errors),
                errors,
            )

    def test_capture_arithmetic_attestation_is_strict_and_nonnegative(self):
        malformed_values = (
            None,
            {"format": "Q7.9", "saturation_events": 0},
            {"format": "Q8.8", "saturation_events": -1},
            {"format": "Q8.8", "saturation_events": False},
            {"format": "Q8.8", "saturation_events": 0.0},
        )
        for malformed in malformed_values:
            with self.subTest(
                arithmetic=malformed
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                deployment = record["oracle"]["deployment"]
                capture = deployment["capture"]
                source = capture["source"]
                payload = source["payload"]
                deployment["arithmetic"] = copy.deepcopy(malformed)
                payload["arithmetic"] = copy.deepcopy(malformed)
                for repeat in payload["repeat_outputs"]:
                    repeat["arithmetic"] = copy.deepcopy(malformed)
                payload_sha = oracle.digest(payload)
                source["manifest"]["payload_sha256"] = payload_sha
                capture["payload_sha256"] = payload_sha
                capture["manifest_sha256"] = oracle.digest(source["manifest"])
                capture["source_sha256"] = oracle.digest(source)

                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        "arithmetic must declare Q8.8" in error
                        and "ENVELOPE_MALFORMED" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_physical_provenance_values_must_be_nonempty_strings(self):
        mutations = (
            ("hardware", "revision", True),
            ("hardware", "board_serial", 9),
            ("bitstream", "sha256", False),
            ("bitstream", "toolchain", "   "),
            ("capture", "manifest_sha256", ["sha256:bb"]),
        )
        for section, key, value in mutations:
            with self.subTest(
                path=f"{section}.{key}"
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                record["oracle"]["deployment"][section][key] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        f"oracle.deployment.{section}.{key}" in error
                        and "HW_PROVENANCE_MISSING" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_live_fpga_identity_requires_an_available_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = oracle.FpgaHardwareAdapter.name
            deployment["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            source = deployment["capture"]["source"]
            source["adapter"] = oracle.FpgaHardwareAdapter.name
            source["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            deployment["capture"]["source_sha256"] = oracle.digest(source)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "current adapter probe to report available" in error
                    for error in errors
                ),
                errors,
            )

    def test_recorded_capture_cannot_be_relabelled_as_a_live_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = oracle.FpgaHardwareAdapter.name
            deployment["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("live FPGA evidence must bind" in error for error in errors),
                errors,
            )

    def _reseal_capture(self, record):
        """Refresh every digest that binds the capture source to the record."""
        deployment = record["oracle"]["deployment"]
        capture = deployment["capture"]
        source = capture["source"]
        payload = source["payload"]
        payload_sha = oracle.digest(payload)
        source["manifest"]["payload_sha256"] = payload_sha
        capture["payload_sha256"] = payload_sha
        capture["manifest_sha256"] = oracle.digest(source["manifest"])
        capture["source_sha256"] = oracle.digest(source)
        record["result"]["derived_from"][-1] = hp._capture_evidence_digest(deployment)
        return record

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
            # Validation replays the availability probe against the capture
            # path, so it must run while the capture file still exists.
            self.assertEqual(hp.validate_record(record, WHERE), [])

    def test_repeat_digest_binds_the_complete_retained_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            capture = record["oracle"]["deployment"]["capture"]
            source = capture["source"]
            payload = source["payload"]
            payload["repeat_outputs"][1]["membrane"]["trace"][0][0] += 0.25
            payload_sha = oracle.digest(payload)
            source["manifest"]["payload_sha256"] = payload_sha
            capture["payload_sha256"] = payload_sha
            capture["manifest_sha256"] = oracle.digest(source["manifest"])
            capture["source_sha256"] = oracle.digest(source)

            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("repeat_digests[1] is not derived" in error for error in errors),
                errors,
            )

    def test_repeat_digest_includes_arithmetic_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            capture = record["oracle"]["deployment"]["capture"]
            source = capture["source"]
            payload = source["payload"]
            payload["repeat_outputs"][1]["arithmetic"]["saturation_events"] += 1
            payload_sha = oracle.digest(payload)
            source["manifest"]["payload_sha256"] = payload_sha
            capture["payload_sha256"] = payload_sha
            capture["manifest_sha256"] = oracle.digest(source["manifest"])
            capture["source_sha256"] = oracle.digest(source)

            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("repeat_digests[1] is not derived" in error for error in errors),
                errors,
            )

    def _with_q88_raw(self, record, raw_value):
        deployment = record["oracle"]["deployment"]
        payload = deployment["capture"]["source"]["payload"]

        def stamp(membrane):
            raw = [
                [int(round(cell * oracle.Q88_SCALE)) for cell in row]
                for row in membrane["trace"]
            ]
            raw[0][0] = raw_value
            membrane["trace_q88_raw"] = raw

        stamp(payload["membrane"])
        for repeat in payload["repeat_outputs"]:
            stamp(repeat["membrane"])
        stamp(deployment["membrane"])
        payload["repeat_digests"] = [
            oracle.run_digest(repeat) for repeat in payload["repeat_outputs"]
        ]
        payload_sha = oracle.digest(payload)
        source = deployment["capture"]["source"]
        source["manifest"]["payload_sha256"] = payload_sha
        deployment["capture"]["payload_sha256"] = payload_sha
        deployment["capture"]["manifest_sha256"] = oracle.digest(source["manifest"])
        deployment["capture"]["source_sha256"] = oracle.digest(source)
        deployment["output_digest"] = oracle.run_digest(payload)
        deployment["repeat_digests"] = list(payload["repeat_digests"])
        return record

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
            self.assertFalse(view["parity_failed"])

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
