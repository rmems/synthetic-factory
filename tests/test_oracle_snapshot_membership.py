"""Run authentication detects membership and identity changes during capture."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import oracle_validate

GOLDEN = Path(__file__).resolve().parent / "fixtures/oracle-grounded/golden-r01"


class OracleSnapshotMembershipTests(unittest.TestCase):
    def test_changes_after_last_payload_capture_invalidate_authentication(self):
        for mutation in ("add_payload", "replace_payload", "replace_manifest"):
            with self.subTest(mutation=mutation):
                self._assert_mutation_refused(mutation)

    def _assert_mutation_refused(self, mutation):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            shutil.copytree(GOLDEN, root)
            self.assertEqual(oracle_validate.authenticate_manifest(root)[2], [])
            capture = oracle_validate._capture_manifested_files

            def race(*args):
                snapshots = capture(*args)
                self._mutate(root, mutation)
                return snapshots

            with mock.patch.object(oracle_validate, "_capture_manifested_files", side_effect=race):
                _manifest, _snapshots, errors = oracle_validate.authenticate_manifest(root)
            self.assertTrue(errors, mutation)
            self.assertTrue(any("changed during capture" in error for error in errors), errors)

    @staticmethod
    def _mutate(root, mutation):
        if mutation == "add_payload":
            (root / "unmanifested.jsonl").write_text("{}\n")
            return
        path = root / "manifest.json" if mutation == "replace_manifest" else next(root.rglob("accepted-*.jsonl"))
        original = path.read_bytes()
        path.unlink()
        path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
