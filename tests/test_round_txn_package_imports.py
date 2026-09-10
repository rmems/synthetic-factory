"""Package-only transaction consumers must not depend on a prior direct family import."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_round_txn import thalamic
from tests import round_txn_package_import_support as import_support

REPO = Path(__file__).resolve().parents[1]


class TransactionPackageImports(unittest.TestCase):
    def test_legacy_consumers_work_in_fresh_package_only_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "legacy-factory"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text(json.dumps(thalamic("legacy")) + "\n")
            for operation in ("committed_jsonl_paths", "valid_legacy_file", "validate_legacy_payload"):
                with self.subTest(operation=operation):
                    self.assertEqual(import_support.package_only_probe_exit_code(
                        REPO, factory, operation), 0)

    def test_probe_refuses_a_child_contaminated_by_a_direct_transaction_import(self):
        with mock.patch.dict(sys.modules, {"round_txn": mock.sentinel.round_txn}):
            with self.assertRaisesRegex(AssertionError, "already loaded.*round_txn"):
                import_support._package_only_probe(str(REPO), "unused", "unused")

    def test_timed_out_probe_is_terminated_killed_and_reaped(self):
        events = []

        class HungProcess:
            def start(self):
                events.append("start")

            def join(self, timeout):
                events.append(("join", timeout))

            def is_alive(self):
                events.append("is_alive")
                return True

            def terminate(self):
                events.append("terminate")

            def kill(self):
                events.append("kill")

        context = mock.Mock()
        context.Process.return_value = HungProcess()
        with mock.patch.object(import_support.multiprocessing, "get_context", return_value=context):
            with self.assertRaisesRegex(TimeoutError, "timed out after 30 seconds"):
                import_support.package_only_probe_exit_code(REPO, Path("unused"), "unused")
        self.assertEqual(events, [
            "start", ("join", 30.0), "is_alive", "terminate", ("join", 5.0),
            "is_alive", "kill", ("join", 5.0),
        ])
