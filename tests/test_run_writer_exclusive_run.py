"""The shared exclusive-run writer closes a descriptor it could not wrap, so nothing leaks."""

import importlib
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



class Refused(Exception):
    """Stands in for a family's refusal type."""


def _refuse(code, detail):
    raise Refused(code)


def _refuse_when(condition, code, detail):
    if condition:
        _refuse(code, detail)


GUARDS = exclusive_run.Guards(_refuse, _refuse_when, lambda path: False)


class WriteRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_files_are_written_and_fsynced(self):
        out = self.root / "run"
        exclusive_run.write_run(GUARDS, out, (("a.txt", "a\n"), ("b.txt", "b\n")))
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["a.txt", "b.txt"])

    def test_an_existing_destination_is_refused_and_left_untouched(self):
        out = self.root / "run"
        out.mkdir()
        (out / "keep").write_text("x")
        with self.assertRaises(Refused) as caught:
            exclusive_run.write_run(GUARDS, out, (("a.txt", "a\n"),))
        self.assertEqual(caught.exception.args[0], exclusive_run.FINDING_DESTINATION_EXISTS)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["keep"])

    def test_a_failure_part_way_unlinks_the_partial_tree(self):
        out = self.root / "run"
        with self.assertRaises(FileExistsError):
            exclusive_run.write_run(GUARDS, out, (("a.txt", "a\n"), ("a.txt", "again\n")))
        self.assertFalse(out.exists())

    def test_the_opened_path_falls_back_when_proc_cannot_be_read(self):
        with mock.patch.object(exclusive_run.os, "readlink", side_effect=OSError("no proc")):
            self.assertEqual(exclusive_run._opened_path(0, self.root), self.root)

    def test_cleanup_tolerates_files_and_directories_already_gone_or_not_empty(self):
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        exclusive_run._unlink_created([exclusive_run._CreatedFile(fd, "never-created")])
        (self.root / "busy").mkdir()
        (self.root / "busy" / "f").write_text("x")
        exclusive_run._rmdir_created(fd, "busy")
        self.assertTrue((self.root / "busy" / "f").exists())



REPO = Path(__file__).resolve().parents[1]


class PackageSpelling(unittest.TestCase):
    """Each family's ``generate`` finds the shared writer under its package spelling too."""

    def test_family_generators_import_the_writer_as_package_children(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        for family in ("maos", "nelb", "pkg", "ttf"):
            with self.subTest(family=family):
                module = importlib.import_module(f"pipelines.{family}.generate")
                self.assertIs(module._exclusive_run.write_run, exclusive_run.write_run)


if __name__ == "__main__":
    unittest.main()
