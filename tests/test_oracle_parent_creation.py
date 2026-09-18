"""Authenticate output parents before any recursive directory creation."""

import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import oracle_generate


class OracleParentCreationTests(unittest.TestCase):
    def test_checked_ancestor_swap_cannot_create_directories_in_raw(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, safe = root / "raw", root / "safe"
            raw.mkdir()
            safe.mkdir()
            destination = safe / "new-parent" / "run"
            check = oracle_generate._raw_destination_error
            swapped = False

            def race(path):
                nonlocal swapped
                error = check(path)
                if not swapped:
                    safe.rename(root / "moved")
                    safe.symlink_to(raw, target_is_directory=True)
                    swapped = True
                return error

            with (
                mock.patch.object(oracle_generate, "RAW_TREE", raw),
                mock.patch.object(oracle_generate, "_raw_destination_error", side_effect=race),
                mock.patch.object(sys, "stderr", io.StringIO()),
            ):
                status = oracle_generate.main(["--count", "1", str(destination)])
            self.assertNotEqual(status, 0)
            self.assertEqual(list(raw.iterdir()), [])

    def test_missing_parents_are_created_beneath_an_authenticated_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            alias = root / "alias"
            alias.symlink_to(target, target_is_directory=True)
            destination = alias / "one" / "two" / "run"
            lock, parent = oracle_generate.reserve_run(destination)
            try:
                self.assertEqual(Path(os.readlink(f"/proc/self/fd/{parent}")), target / "one" / "two")
            finally:
                os.close(lock)
                os.close(parent)
            self.assertTrue((target / "one/two/.run.oracle-generate.lock").is_file())

    def test_racing_child_symlink_cannot_redirect_missing_parent_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, safe = root / "raw", root / "safe"
            raw.mkdir()
            safe.mkdir()
            mkdir = os.mkdir

            def race(path, **kwargs):
                os.symlink(raw, path, target_is_directory=True, dir_fd=kwargs["dir_fd"])
                return mkdir(path, **kwargs)

            with (
                mock.patch.object(oracle_generate, "RAW_TREE", raw),
                mock.patch.object(os, "mkdir", side_effect=race),
                self.assertRaises(OSError),
            ):
                oracle_generate.reserve_run(safe / "new-parent" / "run")
            self.assertEqual(list(raw.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
