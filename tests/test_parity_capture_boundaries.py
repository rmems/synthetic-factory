"""Capture parsing and binding cannot reinterpret supplied physical evidence."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from hardware_parity_support import WHERE
import hardware_parity as hp
import neuro_oracle as oracle
import test_neuro_oracle as support


class CaptureInputBoundaries(unittest.TestCase):
    def test_deep_json_capture_reports_unreadable_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.json"
            path.write_text("[" * 10000 + "0" + "]" * 10000)
            adapter = oracle.RecordedCaptureAdapter(path)
            self.assertFalse(adapter.availability()["available"])
            self.assertEqual(adapter.availability()["reason_code"], "CAPTURE_UNREADABLE")

    def test_capture_binding_includes_clock_and_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = oracle.RecordedCaptureAdapter(support.RecordedCapture()._capture(tmp))
            for field, value in (("dt_ms", 2.0), ("encoding", "different-encoding"), ("name", "different-input")):
                with self.subTest(field=field), self.assertRaises(oracle.OracleUnavailable) as failure:
                    stimulus = support._stimulus()
                    stimulus[field] = value
                    adapter.run(support._model(), stimulus)
                self.assertEqual(failure.exception.reason_code, "CAPTURE_INPUT_FIXTURE_MISMATCH")

    def test_null_top_quantization_cannot_select_valid_nested_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = support.RecordedCapture()._capture(tmp)
            capture = json.loads(path.read_text())
            capture["payload"]["quantization"] = capture["quantization"]
            capture["quantization"] = None
            capture["manifest"]["payload_sha256"] = oracle.digest(capture["payload"])
            path.write_text(json.dumps(capture))
            with self.assertRaises(oracle.OracleUnavailable) as failure:
                oracle.RecordedCaptureAdapter(path).run(support._model(), support._stimulus())
            self.assertEqual(failure.exception.reason_code, "CAPTURE_QUANTIZATION_CONFLICT")

    def test_simulated_deployment_cannot_gain_capture_lineage(self):
        record = copy.deepcopy(hp.generate_records()[0])
        deployment = record["oracle"]["deployment"]
        deployment["capture"] = {"source_sha256": "sha256:" + "f" * 64}
        self.assertIsNone(hp._capture_evidence_digest(deployment))
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("capture" in error for error in errors), errors)
