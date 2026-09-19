"""Publication refuses multiply linked files and mutations during authentication."""

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import oracle_generate
from oracle_grounded import families, generation_output


class StagedFileIdentity(unittest.TestCase):
    def test_hardlinked_payload_or_manifest_never_publishes(self):
        for manifest in (False, True):
            with self.subTest(manifest=manifest):
                self._assert_hardlink_refused(manifest)

    def _assert_hardlink_refused(self, manifest):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "published"
            link = root / "retained-link"
            verify = oracle_generate._verify_staged_payloads

            def add_link(root_fd, files, limit):
                relative = "manifest.json" if manifest else next(iter(files))
                os.link(relative, link, src_dir_fd=root_fd)
                verify(root_fd, files, limit)

            with mock.patch.object(oracle_generate, "_verify_staged_payloads", side_effect=add_link):
                with mock.patch("builtins.print"):
                    status = oracle_generate.main([
                        "--family", families.ENCODER_FAMILY, "--count", "1", str(destination),
                    ])
            self.assertEqual(status, 1)
            self.assertFalse(destination.exists())
            self.assertTrue(link.is_file())

    def test_mutation_after_digest_read_is_refused(self):
        for manifest in (False, True):
            for mutation in ("hardlink", "edit", "replacement"):
                with self.subTest(manifest=manifest, mutation=mutation):
                    self._assert_read_race_refused(manifest, mutation)

    def _assert_read_race_refused(self, manifest, mutation):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "family").mkdir()
            relative = "manifest.json" if manifest else "family/accepted.jsonl"
            path = root / relative
            body = b'{"sample":1}\n'
            path.write_bytes(body)
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            self.addCleanup(os.close, root_fd)
            digest = generation_output._bounded_digest

            def mutate_after_read(payload, limit):
                result = digest(payload, limit)
                if mutation == "hardlink":
                    os.link(path, root / "external-link")
                elif mutation == "edit":
                    path.write_bytes(b'{"sample":2}\n')
                else:
                    path.unlink()
                    path.write_bytes(body)
                return result

            if manifest:
                verify = generation_output._verify_staged_manifest
                verify_args = (root_fd, body)
            else:
                verify = generation_output._verify_staged_payloads
                verify_args = (
                    root_fd,
                    {relative: {"sha256": hashlib.sha256(body).hexdigest()}},
                    1024,
                )

            with mock.patch.object(generation_output, "_bounded_digest", side_effect=mutate_after_read):
                with self.assertRaises(OSError):
                    verify(*verify_args)


if __name__ == "__main__":
    unittest.main()
