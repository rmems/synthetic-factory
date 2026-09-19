"""Loaded measurement code and its digest come from one immutable source snapshot."""

from pathlib import Path
import unittest

from oracle_loaded_source_support import PROBES, run_probe
from process_test_support import ProcessTimeout, spawned_process_exit_code

REPO = Path(__file__).resolve().parents[1]


class OracleLoadedSource(unittest.TestCase):
    def test_exact_loaded_bytes_and_import_ownership(self):
        # Driving the modes off the PROBES registry means a probe that is
        # registered can never go untested; the count pins the reviewed set
        # so a silent deletion still fails here.
        self.assertEqual(len(PROBES), 16)
        for mode in PROBES:
            for package_first in (False, True):
                with self.subTest(mode=mode, package_first=package_first):
                    status = spawned_process_exit_code(
                        run_probe, (str(REPO), mode, package_first),
                        timeout=ProcessTimeout(30, 5, "loaded source probe timed out"),
                    )
                    self.assertEqual(status, 0)


if __name__ == "__main__":
    unittest.main()
