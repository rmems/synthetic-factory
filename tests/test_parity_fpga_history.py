"""Unavailable FPGA diagnostics remain historical while availability stays live."""

import copy
import os
import unittest
from unittest.mock import patch

import hardware_parity as hp
import neuro_oracle as oracle
from hardware_parity_support import WHERE


class HistoricalFpgaDiagnostics(unittest.TestCase):
    def _record(self):
        return hp.generate_records(
            deployment_adapter=oracle.FpgaHardwareAdapter(env={}), env={},
        )[0]

    def test_changed_host_absence_reason_preserves_historical_evidence(self):
        record = self._record()
        original = copy.deepcopy(record)
        with patch.dict(os.environ, {"SPIKENAUT_FPGA_DEVICE": "/definitely/missing"}):
            self.assertEqual(hp.validate_record(record, WHERE), [])
        self.assertEqual(record, original)
        self.assertEqual(record["result"]["verdict"], "inconclusive")

    def test_live_available_fpga_still_refuses_recorded_absence(self):
        record = self._record()
        with patch.object(oracle.FpgaHardwareAdapter, "availability", return_value={"available": True}):
            self.assertTrue(hp.validate_record(record, WHERE))

    def test_unknown_or_empty_historical_diagnostics_are_refused(self):
        for key, value in (("reason_code", "FPGA_SUCCESS"), ("detail", "   ")):
            record = self._record()
            record["oracle"]["unavailable"][0][key] = value
            with self.subTest(key=key):
                self.assertTrue(hp.validate_record(record, WHERE))
