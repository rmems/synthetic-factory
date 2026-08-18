#!/usr/bin/env python3
"""Regression tests for the operator driver's byte-tolerant census paths."""

import importlib.util
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
factory_driver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(factory_driver)


class FactoryDriverBytes(unittest.TestCase):
    def test_count_records_tolerates_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "factory"
            factory.mkdir()
            (factory / "bad-bytes.jsonl").write_bytes(b"{}\xff\n\n{}\n")
            self.assertEqual(factory_driver.count_records(factory), 2)

    def test_snapshot_tolerates_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "run"
            run.mkdir()
            (run / "bad-bytes.jsonl").write_bytes(b"{}\xff\n")
            with redirect_stdout(StringIO()):
                factory_driver.cmd_snapshot(run, "bytes")
            self.assertEqual((Path(td) / "run-bytes" / "bad-bytes.jsonl").read_bytes(), b"{}\xff\n")


if __name__ == "__main__":
    unittest.main()
