"""Postwrite substitutions must prevent oracle run publication."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import oracle_generate
from oracle_grounded import families, generation_output
from test_oracle_grounded_cli import GENERATE, run_cli


class StagingSubstitutionTests(unittest.TestCase):
    def test_staging_identity_failure_closes_and_quarantines_the_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            cleanup = oracle_generate._cleanup_staging
            real_fstat = os.fstat
            changed = False

            def changed_identity(descriptor):
                nonlocal changed
                state = real_fstat(descriptor)
                if changed:
                    return state
                changed = True
                values = list(state)
                values[1] += 1
                return os.stat_result(values)

            try:
                with (
                    mock.patch.object(
                        oracle_generate.os,
                        "fstat",
                        side_effect=changed_identity,
                    ),
                    mock.patch.object(
                        oracle_generate,
                        "_cleanup_staging",
                        wraps=cleanup,
                    ) as cleanup_spy,
                ):
                    with self.assertRaises(OSError):
                        oracle_generate._create_staging(parent / "run", parent_fd)
                cleanup_spy.assert_called_once()
                self.assertEqual(len(list(parent.glob(".synthetic-factory-rollback-*"))), 1)
            finally:
                os.close(parent_fd)

    def _assert_substitution_refused(self, name, symlink):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside"
            outside.write_bytes(b"external data")
            out = Path(tmp) / "run"
            verify = oracle_generate._verify_staged_payloads

            def substitute(root_fd, files, limit):
                relative = "manifest.json" if name == "manifest" else next(iter(files))
                target = Path(f"/proc/self/fd/{root_fd}") / relative
                original = target.read_bytes()
                target.unlink()
                if symlink:
                    target.symlink_to(outside)
                else:
                    # Preserve length so this must fail content authentication,
                    # rather than only the manifest's exact-size check.
                    target.write_bytes(b"x" + original[1:])
                verify(root_fd, files, limit)

            with (
                mock.patch.object(oracle_generate, "_verify_staged_payloads", side_effect=substitute),
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main([
                    "--family", families.ENCODER_FAMILY, "--count", "1", os.fspath(out),
                ])
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            self.assertEqual(outside.read_bytes(), b"external data")

    def test_payload_replacement_refuses_publication(self):
        self._assert_substitution_refused("payload", False)

    def test_payload_symlink_is_refused(self):
        self._assert_substitution_refused("payload", True)

    def test_manifest_replacement_refuses_publication(self):
        self._assert_substitution_refused("manifest", False)

    def test_manifest_symlink_refuses_publication(self):
        self._assert_substitution_refused("manifest", True)


class StagingMembershipTests(unittest.TestCase):
    def test_membership_scan_ignores_callers_directory_offset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text("{}")
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.lseek(descriptor, (1 << 63) - 1, os.SEEK_SET)
                generation_output._verify_directory_members(descriptor, {"manifest.json"})
            finally:
                os.close(descriptor)

    def test_public_cli_publishes_all_five_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            result = run_cli(GENERATE, "--count", "1", str(root))
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(len(manifest["families"]), 5)
            observed = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
            self.assertEqual(observed, set(manifest["files"]) | {"manifest.json"})

    def test_postwrite_undeclared_entries_prevent_publication(self):
        for location in ("root", "family"):
            for kind in ("file", "directory", "symlink"):
                with self.subTest(location=location, kind=kind):
                    self._assert_extra_entry_refused(location, kind)

    def _assert_extra_entry_refused(self, location, kind):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside"
            outside.write_bytes(b"external data")
            out = Path(tmp) / "run"
            verify = oracle_generate._verify_staged_payloads

            def inject(root_fd, files, limit):
                directory = Path(f"/proc/self/fd/{root_fd}")
                if location == "family":
                    directory /= Path(next(iter(files))).parent
                target = directory / "undeclared-entry"
                if kind == "directory":
                    target.mkdir()
                elif kind == "symlink":
                    target.symlink_to(outside)
                else:
                    target.write_bytes(b"unlisted payload")
                verify(root_fd, files, limit)

            with (
                mock.patch.object(oracle_generate, "_verify_staged_payloads", side_effect=inject),
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main([
                    "--family", families.ENCODER_FAMILY, "--count", "1", os.fspath(out),
                ])
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            self.assertEqual(outside.read_bytes(), b"external data")
            self.assertEqual(len(list(Path(tmp).glob(".synthetic-factory-rollback-*"))), 1)


if __name__ == "__main__":
    unittest.main()
