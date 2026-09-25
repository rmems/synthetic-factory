"""Gate source snapshots must preserve physical line termination exactly."""

import tempfile
import unittest
from pathlib import Path

from pipelines.curate_gate_merge import _load_source_records


class ExactSourceLines(unittest.TestCase):
    def test_final_unterminated_source_line_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "batch.jsonl").write_bytes(b'{"id":"one"}\r\n{"id":"two"}')
            records = _load_source_records(root)
            self.assertEqual(records[("batch.jsonl", 1)]["source_bytes"], b'{"id":"one"}\r\n')
            self.assertEqual(records[("batch.jsonl", 2)]["source_bytes"], b'{"id":"two"}')
