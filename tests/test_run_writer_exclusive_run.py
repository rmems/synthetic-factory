"""The shared exclusive-run writer closes a descriptor it could not wrap, so nothing leaks."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from run_writer import exclusive_run


class TextHandle(unittest.TestCase):
    def test_a_descriptor_that_cannot_be_wrapped_is_closed_and_the_error_propagates(self):
        with tempfile.TemporaryDirectory() as tmp:
            descriptor = os.open(Path(tmp) / "f", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with mock.patch.object(exclusive_run.os, "fdopen", side_effect=ValueError("bad")):
                with self.assertRaises(ValueError):
                    exclusive_run._text_handle(descriptor)
            with self.assertRaises(OSError):
                os.fstat(descriptor)  # already closed by _text_handle

    def test_a_wrappable_descriptor_comes_back_as_a_text_handle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with exclusive_run._text_handle(descriptor) as handle:
                handle.write("x\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "x\n")


if __name__ == "__main__":
    unittest.main()
