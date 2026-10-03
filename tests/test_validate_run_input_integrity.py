"""Incomplete filesystem inputs must never become successful validation runs."""

import errno
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from validate_run_test_helpers import (  # noqa: E402
    EXPECTED_TOTALS,
    TINY_THALAMIC,
    _invoke,
    _invoke_inprocess,
    _tiny_run_dir,
)

import validate_run  # noqa: E402
import validate_run_cli  # noqa: E402
from validate_run_input import parse_exact_json_record  # noqa: E402


class RunDirectoryIntegrityTests(unittest.TestCase):
    def test_invalid_roots_fail_before_manifest_publication(self):
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "missing"
            regular_file = Path(raw) / "file.jsonl"
            regular_file.write_text("unchanged\n")
            for root in (missing, regular_file):
                for flags in ((), ("--write",)):
                    with self.subTest(root=root.name, flags=flags):
                        result = _invoke(*flags, str(root))
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn("cannot validate run directory", result.stderr)
                        self.assertIn(str(root), result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
                        self.assertFalse((root / "manifest.json").exists())
            self.assertFalse(missing.exists())
            self.assertEqual(regular_file.read_text(), "unchanged\n")

    def test_direct_manifest_assembly_rejects_invalid_roots(self):
        with tempfile.TemporaryDirectory() as raw:
            regular_file = Path(raw) / "file.jsonl"
            regular_file.write_text("{}\n")
            for root in (Path(raw) / "missing", regular_file):
                with self.subTest(root=root.name), self.assertRaises(OSError):
                    validate_run_cli.assemble_manifest(
                        root, validate_run.check_line, parse_exact_json_record
                    )

    def test_valid_empty_directory_keeps_empty_success_and_write_semantics(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            totals = {"files": 0, "records": 0, "by_kind": {}, "error_count": 0}
            for flags in ((), ("--write",)):
                with self.subTest(flags=flags):
                    result = _invoke(*flags, raw)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout), totals)
                    self.assertEqual(result.stderr, "")
                    self.assertEqual((root / "manifest.json").exists(), bool(flags))
            self.assertEqual(json.loads((root / "manifest.json").read_text())["totals"], totals)

    def test_unreadable_root_is_controlled_error_before_write(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "unreadable"
            root.mkdir()
            root.chmod(0)
            try:
                self._require_denied_directory(root)
                for flags in ((), ("--write",)):
                    with self.subTest(flags=flags):
                        result = _invoke(*flags, str(root))
                        self.assertEqual(result.returncode, 1, result.stderr)
                        self.assertIn("cannot validate run directory", result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
            finally:
                root.chmod(0o700)
            self.assertEqual(list(root.iterdir()), [])

    def test_unreadable_subdirectory_blocks_with_valid_neighbor_counts(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            hidden = root / "hidden"
            hidden.mkdir()
            (hidden / "unseen.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
            hidden.chmod(0)
            try:
                self._require_denied_directory(hidden)
                result = _invoke("--write", str(root))
            finally:
                hidden.chmod(0o700)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("hidden: cannot scan directory", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(json.loads(result.stdout), {**EXPECTED_TOTALS, "error_count": 1})
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(manifest["totals"], json.loads(result.stdout))
            self.assertEqual([entry["file"] for entry in manifest["files"]], ["tiny.jsonl"])
            self.assertEqual(len(manifest["errors"]), 1)

    def test_traversal_io_error_cannot_qualify_a_partial_run(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            hidden = root / "hidden"
            hidden.mkdir()
            original_scandir = os.scandir

            def fail_hidden_scan(path):
                if Path(path) == hidden:
                    raise OSError(errno.EIO, "directory read failed", str(hidden))
                return original_scandir(path)

            with mock.patch.object(os, "scandir", fail_hidden_scan):
                result = _invoke_inprocess(str(root))

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("hidden: cannot scan directory", result.stderr)
            self.assertEqual(json.loads(result.stdout), {**EXPECTED_TOTALS, "error_count": 1})
            self.assertFalse((root / "manifest.json").exists())

    def test_discovery_keeps_sorted_files_and_does_not_follow_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            nested = root / "a"
            nested.mkdir()
            (nested / "z.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
            (root / "linked-file.jsonl").symlink_to(root / "tiny.jsonl")
            (root / "cycle").symlink_to(root, target_is_directory=True)
            result = _invoke("--write", str(root))

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(
                [entry["file"] for entry in manifest["files"]],
                ["a/z.jsonl", "linked-file.jsonl", "tiny.jsonl"],
            )
            self.assertEqual(manifest["totals"]["records"], 3)
            self.assertEqual(manifest["errors"], [])

    def test_entry_metadata_failure_cannot_hide_a_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            hidden = root / "hidden"
            hidden.mkdir()
            (hidden / "unseen.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
            original_is_dir = os.DirEntry.is_dir
            original_stat = Path.stat

            def fail_hidden_is_dir(entry, *args, **kwargs):
                if Path(entry.path) == hidden:
                    raise OSError(errno.EIO, "metadata read failed", str(hidden))
                return original_is_dir(entry, *args, **kwargs)

            def fail_hidden_stat(path, *args, **kwargs):
                if path == hidden:
                    raise OSError(errno.EIO, "metadata read failed", str(hidden))
                return original_stat(path, *args, **kwargs)

            with (
                mock.patch.object(os.DirEntry, "is_dir", fail_hidden_is_dir),
                mock.patch.object(Path, "stat", fail_hidden_stat),
            ):
                result = _invoke_inprocess(str(root))

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("hidden: cannot inspect path", result.stderr)
            self.assertEqual(json.loads(result.stdout), {**EXPECTED_TOTALS, "error_count": 1})

    def _require_denied_directory(self, directory):
        try:
            list(directory.iterdir())
        except PermissionError:
            return
        self.skipTest("directory permissions are not enforced for this process")


class JsonlReadIntegrityTests(unittest.TestCase):
    def test_read_errors_are_manifest_errors_with_valid_neighbor_counts(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            broken = root / "broken.jsonl"
            broken.write_text(json.dumps(TINY_THALAMIC) + "\n")
            original_read = Path.read_bytes
            failures = (
                FileNotFoundError(errno.ENOENT, "removed during validation", str(broken)),
                OSError(errno.EIO, "source read failed", str(broken)),
            )
            for failure in failures:
                with self.subTest(failure=type(failure).__name__):
                    def fail_broken_read(path, failure=failure):
                        if path == broken:
                            raise failure
                        return original_read(path)

                    with mock.patch.object(Path, "read_bytes", fail_broken_read):
                        result = _invoke_inprocess("--write", str(root))
                    self._assert_failed_file_report(root, result)

    def test_unreadable_payload_is_a_controlled_file_error(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _tiny_run_dir(Path(raw))
            broken = root / "broken.jsonl"
            broken.write_text(json.dumps(TINY_THALAMIC) + "\n")
            broken.chmod(0)
            try:
                try:
                    broken.read_bytes()
                except PermissionError:
                    pass
                else:
                    self.skipTest("file permissions are not enforced for this process")
                result = _invoke("--write", str(root))
            finally:
                broken.chmod(0o600)
            self._assert_failed_file_report(root, result)

    def _assert_failed_file_report(self, root, result):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("broken.jsonl: cannot read file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(
            json.loads(result.stdout), {**EXPECTED_TOTALS, "files": 2, "error_count": 1}
        )
        manifest = json.loads((root / "manifest.json").read_text())
        self.assertEqual(manifest["totals"], json.loads(result.stdout))
        self.assertEqual([entry["file"] for entry in manifest["files"]], ["broken.jsonl", "tiny.jsonl"])
        broken_entry = manifest["files"][0]
        self.assertEqual(broken_entry["records"], 0)
        self.assertEqual(broken_entry["kinds"], {})
        self.assertEqual(broken_entry["errors"], manifest["errors"])
        self.assertEqual(len(manifest["errors"]), 1)


if __name__ == "__main__":
    unittest.main()
