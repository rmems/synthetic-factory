"""Failed oracle staging is recoverable without deleting raced replacements."""

import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import oracle_generate
import compose_destination_rename as rename


class StagingRecovery(unittest.TestCase):
    def test_failed_staging_is_quarantined_with_contents_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            staging = parent / "staging"
            staging.mkdir()
            (staging / "payload").write_text("recover me")
            identity = oracle_generate._directory_identity(staging)
            oracle_generate._cleanup_staging(staging, identity)
            quarantines = list(parent.glob(".synthetic-factory-rollback-*"))
            self.assertEqual(len(quarantines), 1)
            self.assertEqual((quarantines[0] / "payload").read_text(), "recover me")
            self.assertFalse(staging.exists())

    def test_replacement_during_atomic_move_is_preserved_and_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            staging = parent / "staging"
            staging.mkdir()
            identity = oracle_generate._directory_identity(staging)
            displaced = parent / "displaced"
            original = rename.rename_noreplace

            def swap(parent_fd, source, destination):
                if source == staging.name:
                    os.rename(staging, displaced)
                    staging.mkdir()
                    (staging / "foreign").write_text("belongs to another writer")
                return original(parent_fd, source, destination)

            with mock.patch.object(rename, "rename_noreplace", side_effect=swap):
                oracle_generate._cleanup_staging(staging, identity)
            self.assertTrue(displaced.is_dir())
            self.assertEqual((staging / "foreign").read_text(), "belongs to another writer")

    def test_unavailable_atomic_move_preserves_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            staging.mkdir()
            (staging / "payload").write_text("recover me")
            identity = oracle_generate._directory_identity(staging)
            with mock.patch.object(rename, "rename_noreplace", side_effect=OSError(errno.ENOSYS, "unavailable")):
                oracle_generate._cleanup_staging(staging, identity)
            self.assertEqual((staging / "payload").read_text(), "recover me")


if __name__ == "__main__":
    unittest.main()
