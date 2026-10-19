"""Read-only scanners tolerate batch names whose round has no marker label."""

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _path in (REPO / "pipelines", REPO / "tests"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import round_txn
from code_repair import publication_export
from round_txn_test_helpers import raw_factory, thalamic, write_records

THALAMIC = "thalamic-trajectory-factory"
HUGE = round_txn.MAX_ROUND_NUMBER + 1


class OutOfRangeRoundTests(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.factory = raw_factory(root, THALAMIC)
        self.batch = self.factory / f"batch-r{HUGE}.jsonl"
        write_records(self.batch, [thalamic("huge-round")])

    def test_marker_paths_stay_strict_for_write_paths(self):
        with self.assertRaises(round_txn.TransactionError):
            round_txn.marker_paths(self.factory, HUGE)
        with self.assertRaises(round_txn.TransactionError):
            round_txn.marker_paths(self.factory, True)

    def test_the_marker_probe_reports_no_marker(self):
        self.assertFalse(round_txn._round_has_transaction_marker(self.factory, HUGE))

    def test_the_legacy_frontier_scan_does_not_raise(self):
        round_txn.discover_unmarked_legacy_frontier(self.factory)

    def test_the_completed_batch_audit_gate_returns_false(self):
        self.assertFalse(
            publication_export.completed_batch_matches(self.batch, self.batch.read_bytes())
        )


if __name__ == "__main__":
    unittest.main()
