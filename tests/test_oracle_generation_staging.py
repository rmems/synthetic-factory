"""Postwrite substitutions must prevent oracle run publication."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import oracle_generate
from oracle_grounded import families


class StagingSubstitutionTests(unittest.TestCase):
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

    def test_payload_symlink_refuses_publication(self):
        self._assert_substitution_refused("payload", True)

    def test_manifest_replacement_refuses_publication(self):
        self._assert_substitution_refused("manifest", False)

    def test_manifest_symlink_refuses_publication(self):
        self._assert_substitution_refused("manifest", True)


if __name__ == "__main__":
    unittest.main()
