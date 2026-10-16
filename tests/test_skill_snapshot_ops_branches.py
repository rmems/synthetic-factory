"""Refusal and edge branches of the operator driver's snapshot machinery.

``snapshot_ops`` copies a possibly-live run without following links and
publishes it without replacing anything. These tests pin the refusals that the
driver-level tests do not reach: the no-replace rename's errno mapping, unsafe
sources, special files, and a run whose commit visibility will not hold still.
Every tree is built in a temporary directory; nothing touches ``outputs/``.
"""

import errno
import importlib
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load the operator driver from {DRIVER_PATH}")
factory_driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory_driver)

# The driver puts the skill directory and pipelines/ on sys.path.
snapshot_ops = importlib.import_module("snapshot_ops")
TransactionError = importlib.import_module("round_txn").TransactionError

UNAVAILABLE = "atomic no-replace snapshot rename is unavailable"
MARKER_MODE = (
    '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
)


def _run_tree(root: Path) -> Path:
    run = root / "run"
    run.mkdir()
    (run / "entry.txt").write_text("inside\n", encoding="utf-8")
    return run


class RenameSnapshotNoReplace(unittest.TestCase):
    def test_kernel_errors_map_to_the_caller_facing_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = _run_tree(root)
            (root / "taken").mkdir()
            cases = (
                ("existing destination", run, root / "taken",
                 FileExistsError, errno.EEXIST, root / "taken"),
                ("missing source", root / "absent", root / "fresh",
                 FileNotFoundError, errno.ENOENT, f"{root / 'absent'} -> {root / 'fresh'}"),
            )
            for label, src, dst, expected, code, filename in cases:
                with self.subTest(label):
                    with self.assertRaises(expected) as raised:
                        snapshot_ops.rename_snapshot_noreplace(src, dst)
                    self.assertEqual(raised.exception.errno, code)
                    self.assertEqual(raised.exception.filename, filename)
            self.assertTrue(run.joinpath("entry.txt").is_file())

    def test_einval_from_the_kernel_reads_as_an_unavailable_rename(self):
        with tempfile.TemporaryDirectory() as td:
            run = _run_tree(Path(td))
            # Moving a directory beneath itself is EINVAL on every Linux filesystem.
            beneath_itself = run / "nested"

            with self.assertRaises(TransactionError) as raised:
                snapshot_ops.rename_snapshot_noreplace(run, beneath_itself)

            self.assertEqual(str(raised.exception), UNAVAILABLE)
            self.assertEqual(sorted(path.name for path in run.iterdir()), ["entry.txt"])

    def test_a_libc_without_renameat2_is_refused_before_any_rename(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = _run_tree(root)
            published = root / "published"
            with (
                mock.patch.object(snapshot_ops.ctypes, "CDLL", return_value=SimpleNamespace()),
                self.assertRaises(TransactionError) as raised,
            ):
                snapshot_ops.rename_snapshot_noreplace(run, published)

            self.assertEqual(str(raised.exception), UNAVAILABLE)
            self.assertIsInstance(raised.exception.__cause__, AttributeError)
            self.assertTrue(run.is_dir())
            self.assertFalse(published.exists())


class CopySnapshotTreeRefusals(unittest.TestCase):
    def test_a_source_that_is_not_a_plain_directory_is_refused_before_staging(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = _run_tree(root)
            (root / "alias").symlink_to(run, target_is_directory=True)
            (root / "plain.txt").write_text("file\n", encoding="utf-8")
            cases = (
                ("missing", root / "absent", errno.ENOENT),
                ("symlinked", root / "alias", errno.ENOTDIR),
                ("regular file", root / "plain.txt", errno.ENOTDIR),
            )
            for label, src, code in cases:
                dst = root / f"staged-{label}"
                with self.subTest(label):
                    with self.assertRaises(TransactionError) as raised:
                        snapshot_ops.copy_snapshot_tree(src, dst)
                    self.assertEqual(
                        str(raised.exception),
                        f"cannot snapshot source safely: {src}: {os.strerror(code)}",
                    )
                    self.assertFalse(dst.exists())

    def test_a_special_file_is_refused_and_the_staged_copy_is_removed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = _run_tree(root)
            os.mkfifo(run / "pipe")
            staging = root / "staging"
            staging.mkdir()

            with self.assertRaises(TransactionError) as raised:
                snapshot_ops.snapshot_to_temp(run, "fifo-", staging)

            self.assertEqual(
                str(raised.exception), f"cannot snapshot unsafe non-file path: {run / 'pipe'}"
            )
            self.assertEqual(list(staging.iterdir()), [])


class MarkerVisibility(unittest.TestCase):
    def test_only_marker_mode_factories_enter_the_visibility_map(self):
        with tempfile.TemporaryDirectory() as td:
            run = _run_tree(Path(td))
            legacy = run / "legacy-factory"
            legacy.mkdir()
            (legacy / "batch-r01.jsonl").write_text('{"id":"legacy"}\n', encoding="utf-8")
            marker = run / "marker-factory"
            marker.mkdir()
            (marker / ".round-marker-mode.json").write_text(MARKER_MODE, encoding="utf-8")

            visible = snapshot_ops.marker_visible_jsonl_paths(run)

        self.assertEqual(visible, {"marker-factory": set()})

    def test_a_refused_bracket_leaves_no_staged_copy_behind(self):
        flapping = [{}, {"factory": {Path("batch-r01.jsonl")}}] * 3
        cases = (
            ("visibility never holds still", flapping, 6,
             "run changed transaction visibility repeatedly while snapshotting: {run}"),
            ("second visibility read fails",
             [{}, TransactionError("unsafe marker mode file: vanished")], 2,
             "unsafe marker mode file: vanished"),
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = _run_tree(root)
            staging = root / "staging"
            staging.mkdir()
            for label, reads, calls, message in cases:
                with (
                    self.subTest(label),
                    mock.patch.object(
                        snapshot_ops, "marker_visible_jsonl_paths", side_effect=reads
                    ) as observed,
                ):
                    with self.assertRaises(TransactionError) as raised:
                        snapshot_ops.marker_visible_snapshot(run, "bracket-", staging)
                    self.assertEqual(str(raised.exception), message.format(run=run))
                    self.assertEqual(observed.call_count, calls)
                    self.assertEqual(list(staging.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
