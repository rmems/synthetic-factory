"""Package-only transaction consumers must not depend on a prior direct family import."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_round_txn import thalamic

REPO = Path(__file__).resolve().parents[1]


class TransactionPackageImports(unittest.TestCase):
    def test_legacy_consumers_work_in_fresh_package_only_processes(self):
        script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from pipelines import round_txn
factory = Path(sys.argv[2])
batch = factory / 'batch-r01.jsonl'
operation = sys.argv[3]
if operation == 'committed_jsonl_paths':
    assert round_txn.committed_jsonl_paths(factory) == [batch]
elif operation == 'valid_legacy_file':
    assert round_txn.valid_legacy_file(batch) == 1
else:
    count, errors = round_txn.validate_legacy_payload(batch, factory, 1)
    assert count == 1 and not errors, (count, errors)
"""
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "legacy-factory"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text(json.dumps(thalamic("legacy")) + "\n")
            for operation in ("committed_jsonl_paths", "valid_legacy_file", "validate_legacy_payload"):
                with self.subTest(operation=operation):
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", script, str(REPO), str(factory), operation],
                        cwd=temporary, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
