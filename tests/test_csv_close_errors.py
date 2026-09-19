"""Descriptor release must not turn a committed run into a refusal."""

import errno
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipelines.csv_mill import generate_io


class PublicationCloseErrors(unittest.TestCase):
    def test_delayed_close_errors_preserve_committed_output_and_release_all_fds(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "run"
            files = {"records.jsonl": "{}\n", "RUN.json": "{}\n", "NOTES.md": "replay\n"}
            close = os.close
            released = []

            def delayed_error(descriptor):
                close(descriptor)
                if destination.exists():
                    released.append(descriptor)
                    raise OSError(errno.EIO, "delayed close error")

            with patch.object(os, "close", delayed_error):
                published = generate_io.write_run_files(destination, files)
            self.assertEqual(published, destination)
            self.assertEqual({p.name: p.read_text() for p in destination.iterdir()}, files)
            self.assertEqual(len(released), 6)  # three files, stage, rename parent, pinned parent
            for descriptor in released:
                with self.assertRaises(OSError):
                    os.fstat(descriptor)

    def test_cleanup_errors_do_not_replace_a_precommit_write_failure(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "run"
            close = os.close

            def delayed_error(descriptor):
                close(descriptor)
                raise OSError(errno.EIO, "delayed close error")

            with patch.object(os, "close", delayed_error), patch.object(
                os, "write", side_effect=OSError(errno.ENOSPC, "no room for output")
            ):
                with self.assertRaises(generate_io.CsvRefusal) as caught:
                    generate_io.write_run_files(destination, {"records.jsonl": "{}\n"})
            self.assertIn("no room for output", str(caught.exception))
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(root).iterdir()), [])
