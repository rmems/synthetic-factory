#!/usr/bin/env python3
"""Census coverage for completed procedural publication batches."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
from test_census import _invoke, _snapshot  # noqa: E402


class CensusProceduralPublication(unittest.TestCase):
    def test_completed_code_repair_batch_is_counted_without_changing_round_files(self):
        from tests.code_repair_admission_test_support import RAW_RUN, copy_published_factory

        with tempfile.TemporaryDirectory() as temporary:
            # A private copy of the process-wide real publication; census only reads it.
            factory = copy_published_factory(Path(temporary) / RAW_RUN)
            manifest = json.loads((factory / "ROUND-r01.complete.json").read_bytes())
            before = _snapshot(factory)
            result = _invoke(str(factory.parent))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["files"], 1)
            self.assertEqual(report["records"], manifest["records"])
            self.assertEqual(report["by_kind"]["code_repair"], manifest["records"])
            self.assertEqual(report["eligible_records"], manifest["records"])
            self.assertEqual(report["by_factory"], {factory.name: manifest["records"]})
            self.assertEqual(report["parse_failures"], 0)
            self.assertEqual(report["decode_failures"], 0)
            self.assertEqual(_snapshot(factory), before)



if __name__ == "__main__":
    unittest.main()
