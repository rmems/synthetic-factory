#!/usr/bin/env python3
"""Export destination safety: pinned writes cannot be steered into outputs/raw."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[0]
sys.path.insert(0, str(REPO / "pipelines"))

import export_contract  # noqa: E402
import export_destination  # noqa: E402


class ExportPinnedWrites(unittest.TestCase):
    def test_refuses_a_split_directory_swapped_for_a_symlink(self):
        """A swapped ``data/splits`` must not divert exports into outputs/raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "export"
            destination.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            (destination / "data").mkdir()
            (destination / "data" / "splits").symlink_to(
                raw, target_is_directory=True
            )
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with self.assertRaises(export_contract.ExportError):
                    export_destination._write_new_bytes(
                        descriptor, export_contract.TRAIN_PATH, b"{}\n"
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(sorted(path.name for path in raw.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
