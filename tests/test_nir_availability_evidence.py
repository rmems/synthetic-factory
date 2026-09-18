"""Unavailable observations require adapter-bound diagnostic evidence."""

import copy
import unittest
from unittest import mock

from nir_equivalence_support import WHERE, refresh_result
import nir_equivalence as nir
import nir_equivalence_runtimes as runtimes


class AvailabilityEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with mock.patch.object(runtimes.importlib.util, "find_spec", return_value=None), \
             mock.patch.object(runtimes.shutil, "which", return_value=None):
            cls.absent = nir.generate_records(steps=6)[0]

    def _entry(self, record, name="nir_rs"):
        return next(entry for entry in record["oracle"]["runtimes"]
                    if entry["runtime"] == name)

    def _assert_diagnostic_refused(self, record):
        refresh_result(record)
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("unavailable diagnostic" in error for error in errors), errors)

    def test_recomputed_lineage_cannot_authorize_fabricated_diagnostics(self):
        for runtime in runtimes.UPSTREAM_RUNTIMES:
            for field, value in (("detail", "self-authenticated invented diagnostic"),
                                 ("reason_code", "RUNTIME_ADAPTER_NOT_IMPLEMENTED")):
                with self.subTest(runtime=runtime.name, field=field):
                    record = copy.deepcopy(self.absent)
                    self._entry(record, runtime.name)[field] = value
                    self._assert_diagnostic_refused(record)

    def test_one_runtime_cannot_borrow_another_runtime_diagnostic(self):
        record = copy.deepcopy(self.absent)
        donor = self._entry(record, "nir_python")
        target = self._entry(record)
        target.update(reason_code=donor["reason_code"], detail=donor["detail"])
        self._assert_diagnostic_refused(record)

    def test_reviewed_absence_remains_valid_after_packages_are_installed(self):
        record = copy.deepcopy(self.absent)
        with mock.patch.object(runtimes.importlib.util, "find_spec", return_value=object()), \
             mock.patch.object(runtimes.shutil, "which", return_value="/reviewed/nir-rs"):
            self.assertEqual(nir.validate_record(record, WHERE), [])
        self.assertEqual(record, self.absent)

    def test_adapter_generated_present_diagnostics_survive_environment_change(self):
        with mock.patch.object(runtimes.importlib.util, "find_spec", return_value=object()), \
             mock.patch.object(runtimes.shutil, "which", return_value="/reviewed/nir-rs"):
            record = nir.generate_records(steps=6)[0]
            self.assertEqual(nir.validate_record(record, WHERE), [])
        before = copy.deepcopy(record)
        with mock.patch.object(runtimes.importlib.util, "find_spec", return_value=None), \
             mock.patch.object(runtimes.shutil, "which", return_value=None):
            self.assertEqual(nir.validate_record(record, WHERE), [])
        self.assertEqual(record, before)

    def test_malformed_current_probe_cannot_authorize_historical_evidence(self):
        runtime = runtimes.UPSTREAM_RUNTIMES[0]
        for detail in (None, "", "   "):
            with self.subTest(detail=detail), mock.patch.object(runtime, "availability", return_value={
                "available": False, "reason_code": "RUNTIME_NOT_INSTALLED", "detail": detail,
            }):
                errors = nir.validate_record(self.absent, WHERE)
                self.assertTrue(any("probe" in error and "diagnostic" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
