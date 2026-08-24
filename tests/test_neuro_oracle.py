"""Tests for pipelines/neuro_oracle.py — the parity oracle boundary."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import neuro_oracle as oracle  # noqa: E402


def _model(**overrides):
    model = {
        "name": "unit-2",
        "neurons": 2,
        "inputs": 2,
        "w_in": [[0.5, 0.0], [0.0, 0.5]],
        "w_rec": None,
        "bias": [0.0, 0.0],
        "threshold": [1.0, 1.0],
        "decay": [0.5, 0.5],
        "refractory_steps": 0,
        "reset": "subtract",
        "dt_ms": 1.0,
        "action_labels": ["hold", "advance"],
    }
    model.update(overrides)
    return model


def _stimulus(steps=4, channels=2):
    return {
        "name": "unit-stim",
        "steps": steps,
        "events": [[1, 0] for _ in range(steps)],
        "dt_ms": 1.0,
    }


class Q88Format(unittest.TestCase):
    def test_exact_values_round_trip(self):
        for value in (0.0, 0.5, 0.25, 1.0, -1.0, 127.99609375, -128.0):
            raw, saturated = oracle.q88_quantize(value)
            self.assertFalse(saturated, value)
            self.assertEqual(oracle.q88_to_float(raw), value)

    def test_rounding_is_half_away_from_zero_not_bankers(self):
        # 0.5/256 sits exactly between two representable values. Python's
        # round() would give 0 here; the declared convention gives 1.
        raw, _ = oracle.q88_quantize(0.5 / 256)
        self.assertEqual(raw, 1)
        raw, _ = oracle.q88_quantize(-0.5 / 256)
        self.assertEqual(raw, -1)

    def test_saturation_is_flagged_not_wrapped(self):
        raw, saturated = oracle.q88_quantize(500.0)
        self.assertTrue(saturated)
        self.assertEqual(raw, oracle.Q88_MAX_RAW)
        raw, saturated = oracle.q88_quantize(-500.0)
        self.assertTrue(saturated)
        self.assertEqual(raw, oracle.Q88_MIN_RAW)

    def test_multiply_saturates_and_rounds(self):
        product, saturated = oracle.q88_mul(oracle.Q88_MAX_RAW, oracle.Q88_MAX_RAW)
        self.assertTrue(saturated)
        self.assertEqual(product, oracle.Q88_MAX_RAW)
        # 0.5 * 3 == 1.5 exactly
        product, saturated = oracle.q88_mul(128, 768)
        self.assertFalse(saturated)
        self.assertEqual(oracle.q88_to_float(product), 1.5)

    def test_non_finite_is_rejected(self):
        with self.assertRaises(ValueError):
            oracle.q88_quantize(float("inf"))


class ModelValidation(unittest.TestCase):
    def test_missing_keys_rejected(self):
        with self.assertRaises(ValueError):
            oracle.normalize_model({"name": "x", "neurons": 1})

    def test_bad_matrix_shape_rejected(self):
        with self.assertRaises(ValueError):
            oracle.normalize_model(_model(w_in=[[0.5]]))

    def test_unknown_reset_rejected(self):
        with self.assertRaises(ValueError):
            oracle.normalize_model(_model(reset="clamp"))

    def test_action_labels_must_match_neuron_count(self):
        with self.assertRaises(ValueError):
            oracle.normalize_model(_model(action_labels=["only-one"]))

    def test_stimulus_width_must_match_model(self):
        with self.assertRaises(ValueError):
            oracle.normalize_stimulus(
                {"name": "s", "steps": 1, "events": [[1, 0, 1]]}, 2
            )

    def test_stimulus_must_be_binary(self):
        with self.assertRaises(ValueError):
            oracle.normalize_stimulus({"name": "s", "steps": 1, "events": [[2, 0]]}, 2)

    def test_stimulus_step_count_must_agree(self):
        with self.assertRaises(ValueError):
            oracle.normalize_stimulus(
                {"name": "s", "steps": 5, "events": [[1, 0]]}, 2
            )


class Quantization(unittest.TestCase):
    def test_provenance_covers_every_parameter(self):
        model = _model(w_rec=[[0.0, -0.25], [-0.25, 0.0]])
        _, provenance = oracle.quantize_model(model)
        names = {entry["parameter"] for entry in provenance["parameters"]}
        # 4 w_in + 4 w_rec + 2 bias + 2 threshold + 2 decay
        self.assertEqual(len(provenance["parameters"]), 14)
        self.assertIn("w_rec[0][1]", names)
        self.assertIn("decay[1]", names)
        self.assertEqual(provenance["parameter_count"], 14)

    def test_exactly_representable_model_has_zero_error(self):
        _, provenance = oracle.quantize_model(_model())
        self.assertEqual(provenance["max_abs_error"], 0.0)
        self.assertEqual(provenance["saturated_parameter_count"], 0)

    def test_out_of_range_weight_is_counted_as_saturated(self):
        _, provenance = oracle.quantize_model(_model(w_in=[[300.0, 0.0], [0.0, 0.5]]))
        self.assertEqual(provenance["saturated_parameter_count"], 1)
        entry = next(
            item for item in provenance["parameters"] if item["parameter"] == "w_in[0][0]"
        )
        self.assertTrue(entry["saturated"])
        self.assertEqual(entry["q88_value"], oracle.Q88_MAX_VALUE)

    def test_declared_conversion_policy_is_recorded(self):
        _, provenance = oracle.quantize_model(_model())
        self.assertEqual(provenance["format"], "Q8.8")
        self.assertEqual(provenance["fractional_bits"], 8)
        self.assertEqual(provenance["rounding"], oracle.Q88_ROUNDING)
        self.assertEqual(provenance["saturation_policy"], oracle.Q88_SATURATION_POLICY)


class Simulators(unittest.TestCase):
    def test_float_simulation_is_deterministic(self):
        first = oracle.simulate_float(_model(), _stimulus())
        second = oracle.simulate_float(_model(), _stimulus())
        self.assertEqual(first["spikes"], second["spikes"])
        self.assertEqual(first["membrane"]["trace"], second["membrane"]["trace"])

    def test_exactly_representable_model_matches_fixed_point(self):
        # decay 0 removes the leak multiply, and every parameter is a multiple
        # of 1/256, so the two datapaths have nothing to disagree about.
        model = _model(decay=[0.0, 0.0])
        q_model, _ = oracle.quantize_model(model)
        float_run = oracle.simulate_float(model, _stimulus())
        fixed_run = oracle.simulate_fixed_point(q_model, _stimulus())
        self.assertEqual(float_run["spikes"], fixed_run["spikes"])
        self.assertEqual(float_run["action"]["label"], fixed_run["action"]["label"])

    def test_refractory_suppresses_spikes(self):
        model = _model(w_in=[[2.0, 0.0], [0.0, 2.0]], refractory_steps=2)
        run = oracle.simulate_float(model, _stimulus(steps=6))
        neuron_zero = [row[0] for row in run["spikes"]]
        self.assertEqual(neuron_zero, [1, 0, 0, 1, 0, 0])

    def test_action_decode_reports_no_spike(self):
        model = _model(threshold=[99.0, 99.0])
        run = oracle.simulate_float(model, _stimulus())
        self.assertEqual(run["action"]["label"], "no_spike")
        self.assertIsNone(run["action"]["index"])

    def test_action_decode_breaks_ties_to_lowest_index(self):
        model = _model(w_in=[[2.0, 0.0], [2.0, 0.0]])
        run = oracle.simulate_float(model, _stimulus())
        self.assertEqual(run["action"]["index"], 0)

    def test_fixed_point_counts_accumulator_saturation(self):
        # Individually representable weights whose partial sum is not.
        model = _model(
            w_in=[[120.0, 120.0], [0.0, 0.0]],
            threshold=[100.0, 100.0],
            decay=[0.0, 0.0],
        )
        q_model, _ = oracle.quantize_model(model)
        run = oracle.simulate_fixed_point(
            q_model, {"name": "s", "steps": 2, "events": [[1, 1], [1, 1]]}
        )
        self.assertGreater(run["arithmetic"]["saturation_events"], 0)


class Adapters(unittest.TestCase):
    def test_software_and_fixed_point_adapters_are_available(self):
        self.assertTrue(oracle.SoftwareFloatAdapter().availability()["available"])
        self.assertTrue(oracle.FixedPointReferenceAdapter().availability()["available"])

    def test_fixed_point_adapter_declares_it_is_not_hardware(self):
        adapter = oracle.FixedPointReferenceAdapter()
        self.assertEqual(adapter.execution_target, oracle.TARGET_FIXED_POINT_MODEL)
        self.assertNotIn(adapter.execution_target, oracle.PHYSICAL_TARGETS)
        run = adapter.run(_model(), _stimulus())
        self.assertIn("quantization", run)
        self.assertFalse(run["latency"]["measured"])

    def test_reference_adapters_do_not_claim_hardware_repeatability(self):
        run = oracle.SoftwareFloatAdapter().run(_model(), _stimulus(), repeats=3)
        self.assertEqual(run["repeats"], 3)
        self.assertIn("not evidence about", run["determinism"]["meaning"])

    def test_fpga_adapter_is_unavailable_without_a_declared_device(self):
        adapter = oracle.FpgaHardwareAdapter(env={})
        status = adapter.availability()
        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "FPGA_DEVICE_NOT_DECLARED")

    def test_fpga_adapter_reports_absent_device(self):
        adapter = oracle.FpgaHardwareAdapter(
            env={oracle.FPGA_DEVICE_ENV: "/nonexistent/board0"}
        )
        self.assertEqual(adapter.availability()["reason_code"], "FPGA_DEVICE_ABSENT")

    def test_fpga_adapter_requires_a_pinned_bitstream(self):
        with tempfile.NamedTemporaryFile() as handle:
            adapter = oracle.FpgaHardwareAdapter(
                env={oracle.FPGA_DEVICE_ENV: handle.name}
            )
            self.assertEqual(
                adapter.availability()["reason_code"], "FPGA_BITSTREAM_NOT_DECLARED"
            )

    def test_fpga_adapter_still_refuses_with_device_and_bitstream(self):
        # There is no board transport in this repository, so even a fully
        # declared environment must not yield an fpga_hardware result.
        with tempfile.NamedTemporaryFile() as handle:
            adapter = oracle.FpgaHardwareAdapter(
                env={
                    oracle.FPGA_DEVICE_ENV: handle.name,
                    oracle.FPGA_BITSTREAM_ENV: "sha256:deadbeef",
                }
            )
            self.assertEqual(
                adapter.availability()["reason_code"], "FPGA_DRIVER_NOT_IMPLEMENTED"
            )

    def test_fpga_adapter_run_raises_instead_of_substituting(self):
        adapter = oracle.FpgaHardwareAdapter(env={})
        with self.assertRaises(oracle.OracleUnavailable) as caught:
            adapter.run(_model(), _stimulus())
        self.assertEqual(caught.exception.reason_code, "FPGA_DEVICE_NOT_DECLARED")

    def test_get_adapter_rejects_unknown_names(self):
        with self.assertRaises(KeyError):
            oracle.get_adapter("some_other_board")

    def test_availability_report_covers_every_adapter(self):
        report = oracle.availability_report(env={})
        self.assertEqual(set(report), set(oracle.ADAPTERS))
        self.assertFalse(report["spikenaut_fpga"]["available"])


class RecordedCapture(unittest.TestCase):
    def _capture(self, tmp, **overrides):
        model = _model()
        stimulus = oracle.normalize_stimulus(_stimulus(), model["inputs"])
        _, quantization = oracle.quantize_model(model)
        payload = {
            "spikes": [[1, 0], [0, 0], [0, 0], [0, 0]],
            "action": {"index": 0, "label": "hold", "counts": [1, 0], "rule": "argmax_count"},
            "latency": {"measured": True, "value_ms": 0.42},
        }
        capture = {
            "execution_target": oracle.TARGET_RECORDED_CAPTURE,
            "quantization": quantization,
            "hardware": {"revision": "rev-b", "board_serial": "SN-1"},
            "bitstream": {"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            "manifest": {
                "payload_sha256": oracle.digest(payload),
                "input_fixture_sha256": oracle.stimulus_fixture(stimulus)["sha256"],
                "recorded_at": "2026-01-01T00:00:00Z",
            },
            "payload": payload,
        }
        capture.update(overrides)
        path = Path(tmp) / "capture.json"
        path.write_text(json.dumps(capture), encoding="utf-8")
        return path

    def test_missing_capture_is_unavailable(self):
        adapter = oracle.RecordedCaptureAdapter("/nonexistent/capture.json")
        self.assertEqual(adapter.availability()["reason_code"], "CAPTURE_FILE_ABSENT")
        with self.assertRaises(oracle.OracleUnavailable):
            adapter.run(_model(), _stimulus())

    def test_valid_capture_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = oracle.RecordedCaptureAdapter(self._capture(tmp))
            self.assertTrue(adapter.availability()["available"])
            run = adapter.run(_model(), _stimulus())
            self.assertEqual(run["execution_target"], oracle.TARGET_RECORDED_CAPTURE)
            self.assertEqual(run["hardware"]["board_serial"], "SN-1")
            self.assertTrue(run["latency"]["measured"])

    def test_tampered_payload_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._capture(tmp)
            capture = json.loads(path.read_text())
            capture["payload"]["spikes"][0][1] = 1
            path.write_text(json.dumps(capture), encoding="utf-8")
            adapter = oracle.RecordedCaptureAdapter(path)
            with self.assertRaises(oracle.OracleUnavailable) as caught:
                adapter.run(_model(), _stimulus())
            self.assertEqual(caught.exception.reason_code, "CAPTURE_DIGEST_MISMATCH")

    def test_capture_for_a_different_input_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = oracle.RecordedCaptureAdapter(self._capture(tmp))
            other = {"name": "other", "steps": 4, "events": [[0, 1]] * 4, "dt_ms": 1.0}
            with self.assertRaises(oracle.OracleUnavailable) as caught:
                adapter.run(_model(), other)
            self.assertEqual(
                caught.exception.reason_code, "CAPTURE_INPUT_FIXTURE_MISMATCH"
            )

    def test_unknown_capture_target_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._capture(tmp, execution_target="magic_board")
            adapter = oracle.RecordedCaptureAdapter(path)
            self.assertEqual(
                adapter.availability()["reason_code"], "CAPTURE_TARGET_UNKNOWN"
            )

    def test_unreadable_capture_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.json"
            path.write_text("{not json", encoding="utf-8")
            adapter = oracle.RecordedCaptureAdapter(path)
            self.assertEqual(adapter.availability()["reason_code"], "CAPTURE_UNREADABLE")

    def test_capture_without_quantization_is_refused(self):
        # The Q8.8 export is what was loaded onto the board; a capture that
        # omits it cannot support a parity claim.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._capture(tmp)
            capture = json.loads(path.read_text())
            del capture["quantization"]
            capture["manifest"]["payload_sha256"] = oracle.digest(capture["payload"])
            path.write_text(json.dumps(capture), encoding="utf-8")
            adapter = oracle.RecordedCaptureAdapter(path)
            with self.assertRaises(oracle.OracleUnavailable) as caught:
                adapter.run(_model(), _stimulus())
            self.assertEqual(
                caught.exception.reason_code, "CAPTURE_QUANTIZATION_MISSING"
            )

    def test_malformed_payload_raises_oracle_unavailable_not_keyerror(self):
        # run_pair only catches OracleUnavailable; anything else crashes
        # generation instead of being recorded as an unavailability.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._capture(tmp)
            capture = json.loads(path.read_text())
            del capture["payload"]["action"]
            capture["manifest"]["payload_sha256"] = oracle.digest(capture["payload"])
            path.write_text(json.dumps(capture), encoding="utf-8")
            adapter = oracle.RecordedCaptureAdapter(path)
            with self.assertRaises(oracle.OracleUnavailable) as caught:
                adapter.run(_model(), _stimulus())
            self.assertEqual(caught.exception.reason_code, "CAPTURE_UNREADABLE")

    def test_capture_replay_carries_its_quantization_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = oracle.RecordedCaptureAdapter(self._capture(tmp)).run(
                _model(), _stimulus()
            )
            self.assertEqual(run["quantization"]["format"], "Q8.8")


class Digests(unittest.TestCase):
    def test_digest_is_key_order_independent(self):
        self.assertEqual(oracle.digest({"a": 1, "b": 2}), oracle.digest({"b": 2, "a": 1}))

    def test_digest_rejects_non_finite_numbers(self):
        with self.assertRaises(ValueError):
            oracle.digest({"a": float("nan")})


class Cli(unittest.TestCase):
    def test_cli_prints_availability_report(self):
        result = subprocess.run(
            [sys.executable, str(PIPELINES / "neuro_oracle.py")],
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(result.stdout)
        self.assertIn("spikenaut_fpga", report)
        self.assertFalse(report["spikenaut_fpga"]["available"])


if __name__ == "__main__":
    unittest.main()
