#!/usr/bin/env python3
"""Census coverage for native neuromorphic-fault-recovery envelopes."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
from test_census import _invoke, _snapshot  # noqa: E402


class CensusNativePublication(unittest.TestCase):
    def test_native_simulator_batch_increments_fault_recovery_without_keyerror(self):
        from pipelines.oracle_grounded import fault_oracle

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "fault-recovery-simulator-factory"
            factory.mkdir()
            records = fault_oracle.build_records(
                97531, 3, produced_at="2026-09-18T12:00:00.000Z"
            )
            (factory / "batch-r01.jsonl").write_text(
                "".join(
                    json.dumps(row, separators=(",", ":")) + "\n" for row in records
                ),
                encoding="utf-8",
            )
            before = _snapshot(factory)
            result = _invoke(str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["files"], 1)
            self.assertEqual(report["records"], 3)
            self.assertEqual(report["by_kind"]["fault_recovery"], 3)
            self.assertEqual(report["by_kind"]["thalamic"], 0)
            self.assertEqual(report["by_kind"]["code_repair"], 0)
            self.assertEqual(report["by_factory"], {factory.name: 3})
            self.assertEqual(report["parse_failures"], 0)
            self.assertEqual(report["decode_failures"], 0)
            self.assertEqual(_snapshot(factory), before)


if __name__ == "__main__":
    unittest.main()
