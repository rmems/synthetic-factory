"""Historical capture diagnostics are data, never validator file requests."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import census
import hardware_parity as hp
import neuro_oracle as oracle
from hardware_parity_support import WHERE


class HistoricalCaptureDiagnostics(unittest.TestCase):
    def _record(self):
        with tempfile.TemporaryDirectory() as tmp:
            capture = Path(tmp) / "capture.json"
            capture.write_text(json.dumps({"execution_target": "recorded_capture"}))
            return hp.generate_records(steps=6, deployment=(oracle.RecordedCaptureAdapter(capture), None))[0]

    def test_validator_does_not_open_historical_record_controlled_capture_path(self):
        record = self._record()
        with patch.object(oracle.RecordedCaptureAdapter, "__init__", side_effect=AssertionError("capture path opened")) as constructor:
            self.assertEqual(hp.validate_record(record, WHERE), [])
        constructor.assert_not_called()
        self.assertIsNone(record["oracle"]["deployment"])
        self.assertEqual(record["result"]["verdict"], "inconclusive")

    def test_historical_capture_cannot_claim_a_measurement_or_unknown_reason(self):
        original = self._record()
        for target, key, value in (("result", "verdict", "match"),
                                   ("result", "parity", {"invented": 1}),
                                   ("diagnostic", "reason_code", "CAPTURE_SUCCESS")):
            record = copy.deepcopy(original)
            section = record["oracle"]["unavailable"][0] if target == "diagnostic" else record[target]
            section[key] = value
            with self.subTest(key=key):
                self.assertTrue(hp.validate_record(record, WHERE))


class ParityCensusProvenance(unittest.TestCase):
    def test_canonical_parity_provenance_counts_simulation_and_hil(self):
        for kind in ("hardware_parity", "nir_equivalence"):
            for provenance, bucket in (("simulated", "sim*"), ("hil", "hil*")):
                with self.subTest(kind=kind, provenance=provenance):
                    record = {"record_kind": kind, "provenance": {"kind": provenance}}
                    self.assertEqual(census._record_simulation_buckets(record), {bucket: 1})

    def test_unrelated_provenance_does_not_become_parity_evidence(self):
        self.assertEqual(census._record_simulation_buckets({"provenance": {"kind": "hil"}}), {"<missing>": 1})
