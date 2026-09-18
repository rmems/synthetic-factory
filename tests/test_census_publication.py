#!/usr/bin/env python3
"""Census coverage for completed procedural publication batches."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
sys.path.insert(0, str(TESTS))
from test_census import _invoke, _snapshot  # noqa: E402


class CensusProceduralPublication(unittest.TestCase):
    def test_completed_code_repair_batch_is_counted_without_changing_round_files(self):
        from tests.code_repair_test_support import generate
        from code_repair import publication

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "generated"
            generate.run(generate.RunRequest(
                REPO / "catalogs/python-repair-v1", run_dir,
                20260908, 12, "2026-09-09T00:00:00.000Z",
            ))
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            manifest = publication.publish_run(publication.PublishRequest(run_dir, factory, 1))
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
