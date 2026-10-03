"""Incomplete or ambiguous input must not qualify a quality-gate run."""

import errno
import json
import os
import signal
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import quality_gate  # noqa: E402


REAL_RECORD = '{"state":{"sim_or_real":"real","note":"readable neighbor"}}\n'


class QualityGateInputIntegrity(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, relative, payload=REAL_RECORD):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        return path

    def audit(self):
        return quality_gate.audit_run(self.root, embedding_dedup=False)

    @contextmanager
    def unreadable(self, path):
        mode = path.stat().st_mode
        path.chmod(0)
        try:
            try:
                if path.is_dir():
                    list(path.iterdir())
                else:
                    path.read_bytes()
            except PermissionError:
                yield
            else:
                self.skipTest("current user can read paths with mode 0")
        finally:
            path.chmod(mode)

    @contextmanager
    def listing_failure(self, denied):
        original_scandir = os.scandir
        denied_metadata = denied.stat()

        def scandir_with_error(path):
            if isinstance(path, int):
                metadata = os.fstat(path)
                if (metadata.st_dev, metadata.st_ino) == (
                    denied_metadata.st_dev,
                    denied_metadata.st_ino,
                ):
                    raise PermissionError(errno.EACCES, "listing denied", str(denied))
            elif path == denied:
                raise PermissionError(errno.EACCES, "listing denied", str(path))
            return original_scandir(path)

        with patch.object(os, "scandir", scandir_with_error):
            yield

    @contextmanager
    def audit_deadline(self):
        def expired(_signum, _frame):
            self.fail("quality gate blocked opening a nonregular input")

        previous_handler = signal.signal(signal.SIGALRM, expired)
        previous_timer = signal.setitimer(signal.ITIMER_REAL, 5)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)
            signal.signal(signal.SIGALRM, previous_handler)

    def audit_cli(self):
        output = StringIO()
        with (
            self.audit_deadline(),
            redirect_stdout(output),
            self.assertRaises(SystemExit) as caught,
        ):
            quality_gate.main([str(self.root), "--json", "--no-embedding-dedup"])
        self.assertEqual(caught.exception.code, 1)
        return json.loads(output.getvalue())

    def test_duplicate_keys_cannot_overwrite_provenance_or_nested_evidence(self):
        ambiguous_records = (
            '{"state":{"sim_or_real":"simulated"},"state":{"sim_or_real":"real"}}',
            '{"state":{"sim_or_real":"simulated","sim_or_real":"real"}}',
            '{"state":{"sim_or_real":"real","reward":{"score":1,"score":2}}}',
            '{"state":{"sim_or_real":"real","note":1,"\\u006eote":1}}',
        )
        for ambiguous in ambiguous_records:
            with self.subTest(payload=ambiguous):
                self.write("batch.jsonl", ambiguous + "\n" + REAL_RECORD)

                report = self.audit()

                self.assertTrue(report["blocked"])
                self.assertEqual(report["counts"]["malformed_lines"], 1)
                self.assertEqual(report["counts"]["total"], 1)
                self.assertEqual(report["mix"]["provenance"], {"real": 1})
                self.assertEqual(report["duplicates"], [])
                error = report["errors"]["malformed_examples"][0]
                self.assertEqual((error["file"], error["line"]), ("batch.jsonl", 1))
                self.assertIn("duplicate JSON object key", error["error"])

    def test_unreadable_subtree_blocks_while_counting_readable_neighbors(self):
        self.write("visible.jsonl")
        hidden = self.write("hidden/batch.jsonl").parent

        with self.unreadable(hidden):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 1)
        self.assertEqual(report["counts"]["unreadable_files"], 1)
        error = report["errors"]["unreadable_examples"][0]
        self.assertEqual(error["file"], "hidden")
        self.assertIn("PermissionError", error["error"])
        self.assertTrue(any("readable subset" in warning for warning in report["warnings"]))

    def test_unreadable_root_does_not_pass_as_an_empty_run(self):
        self.write("batch.jsonl")

        with self.unreadable(self.root):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], ".")

    def test_listing_failure_blocks_independently_of_filesystem_permissions(self):
        hidden = self.write("hidden/batch.jsonl").parent
        self.write("visible.jsonl")

        for denied, expected_total, relative in ((self.root, 0, "."), (hidden, 1, "hidden")):
            with self.subTest(relative=relative), self.listing_failure(denied):
                report = self.audit()

            self.assertTrue(report["blocked"])
            self.assertEqual(report["counts"]["total"], expected_total)
            self.assertEqual(report["errors"]["unreadable_files"], 1)
            self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], relative)

    def test_cli_listing_failure_blocks_even_for_privileged_users(self):
        hidden = self.write("hidden/batch.jsonl").parent
        output = StringIO()

        with (
            self.listing_failure(hidden),
            redirect_stdout(output),
            self.assertRaises(SystemExit) as caught,
        ):
            quality_gate.main([str(self.root), "--json", "--no-embedding-dedup"])

        self.assertEqual(caught.exception.code, 1)
        self.assertTrue(json.loads(output.getvalue())["blocked"])

    def test_unreadable_source_file_keeps_its_relative_diagnostic(self):
        source = self.write("lane/batch.jsonl")

        with self.unreadable(source):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["unreadable_files"], 1)
        error = report["errors"]["unreadable_examples"][0]
        self.assertEqual(error["file"], "lane/batch.jsonl")
        self.assertIn("PermissionError", error["error"])

    def test_traversal_error_counts_are_complete_with_bounded_sorted_examples(self):
        with ExitStack() as blocked_directories:
            for index in reversed(range(12)):
                hidden = self.write(f"hidden-{index:02}/batch.jsonl").parent
                blocked_directories.enter_context(self.unreadable(hidden))

            report = self.audit()
            repeated = self.audit()

        self.assertEqual(report, repeated)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["errors"]["unreadable_files"], 12)
        self.assertEqual(
            [example["file"] for example in report["errors"]["unreadable_examples"]],
            [f"hidden-{index:02}" for index in range(10)],
        )

    def test_unreadable_member_metadata_cannot_hide_a_subtree(self):
        hidden = self.write("hidden/batch.jsonl").parent
        original_stat = os.stat

        def stat_with_error(path, *args, **kwargs):
            if path in (hidden, hidden.name):
                raise OSError(errno.EIO, "metadata read failed", str(path))
            return original_stat(path, *args, **kwargs)

        # Portable injection for a filesystem I/O failure that chmod cannot model.
        with patch.object(os, "stat", stat_with_error):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "hidden")

    def test_queued_directory_replaced_by_symlink_is_not_descended(self):
        queued = self.root / "queued"
        queued.mkdir()
        outside_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temporary.cleanup)
        outside = Path(outside_temporary.name)
        (outside / "external.jsonl").write_text(REAL_RECORD, encoding="utf-8")
        original_stat = os.stat
        swapped = False

        def stat_then_swap(path, *args, **kwargs):
            nonlocal swapped
            metadata = original_stat(path, *args, **kwargs)
            if path in (queued, queued.name) and not swapped:
                swapped = True
                queued.rmdir()
                queued.symlink_to(outside, target_is_directory=True)
            return metadata

        with patch.object(os, "stat", stat_then_swap):
            report = self.audit()

        self.assertTrue(swapped)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "queued")

    def test_cli_emits_a_blocked_report_for_an_unreadable_subtree(self):
        hidden = self.write("hidden/batch.jsonl").parent
        output = StringIO()

        with (
            self.unreadable(hidden),
            redirect_stdout(output),
            self.assertRaises(SystemExit) as caught,
        ):
            quality_gate.main([str(self.root), "--json", "--no-embedding-dedup"])

        self.assertEqual(caught.exception.code, 1)
        self.assertTrue(json.loads(output.getvalue())["blocked"])

    def test_duplicate_representative_uses_global_path_order(self):
        for relative in ("z.jsonl", "a/z.jsonl", "a.jsonl", "a/a.jsonl"):
            self.write(relative)

        report = self.audit()

        cluster = report["duplicate_clusters"][0]
        self.assertEqual(cluster["representative"], {"file": "a/a.jsonl", "line": 1})
        self.assertEqual(
            cluster["members"],
            [
                {"file": "a/a.jsonl", "line": 1},
                {"file": "a/z.jsonl", "line": 1},
                {"file": "a.jsonl", "line": 1},
                {"file": "z.jsonl", "line": 1},
            ],
        )

    def test_symlink_file_is_read_but_directory_links_are_not_descended(self):
        source = self.write("source.txt")
        self.write("ignored/batch.txt")
        (self.root / "alias.jsonl").symlink_to(source)
        (self.root / "directory-link").symlink_to(self.root, target_is_directory=True)

        report = self.audit()

        self.assertFalse(report["blocked"])
        self.assertEqual(report["counts"]["total"], 1)
        self.assertEqual(report["errors"]["unreadable_files"], 0)

    def test_regular_inputs_work_when_nonblocking_open_flag_is_unavailable(self):
        self.write("batch.jsonl")

        with patch.dict(os.__dict__):
            os.__dict__.pop("O_NONBLOCK", None)
            try:
                report = self.audit()
            except AttributeError as exc:
                self.fail(f"regular input requires an unavailable platform flag: {exc}")

        self.assertFalse(report["blocked"])
        self.assertEqual(report["counts"]["total"], 1)

    def test_dangling_jsonl_symlink_blocks(self):
        (self.root / "broken.jsonl").symlink_to(self.root / "absent")

        report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "broken.jsonl")

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires an interruptible deadline")
    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires named pipes")
    def test_fifo_input_blocks_the_gate_without_hanging(self):
        os.mkfifo(self.root / "pipe.jsonl")

        report = self.audit_cli()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "pipe.jsonl")

    @unittest.skipUnless(hasattr(signal, "setitimer"), "requires an interruptible deadline")
    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires named pipes")
    def test_symlink_to_fifo_blocks_the_gate_without_hanging(self):
        source = self.root / "named-pipe"
        os.mkfifo(source)
        (self.root / "alias.jsonl").symlink_to(source)

        report = self.audit_cli()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "alias.jsonl")

    @unittest.skipUnless(Path("/proc/self/fd").is_dir(), "requires Linux descriptor inventory")
    def test_rejected_device_inputs_do_not_leak_descriptors(self):
        (self.root / "device.jsonl").symlink_to(os.devnull)
        descriptor_directory = Path("/proc/self/fd")
        before = set(descriptor_directory.iterdir())

        for _ in range(8):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(set(descriptor_directory.iterdir()), before)

    def test_directory_named_jsonl_remains_an_unreadable_input(self):
        self.write("lane.jsonl/batch.jsonl")

        report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 1)
        self.assertEqual(report["errors"]["unreadable_files"], 1)
        self.assertEqual(report["errors"]["unreadable_examples"][0]["file"], "lane.jsonl")

    def test_empty_subdirectories_and_non_jsonl_files_still_pass(self):
        (self.root / "empty").mkdir()
        self.write("note.txt", "not JSON")
        self.write("batch.JSONL", "not JSON")

        report = self.audit()

        self.assertFalse(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["errors"]["unreadable_files"], 0)

    def test_hidden_jsonl_names_remain_in_the_audited_corpus(self):
        self.write(".jsonl")
        self.write(".hidden/.batch.jsonl")

        report = self.audit()

        self.assertEqual(report["counts"]["total"], 2)
        self.assertTrue(report["blocked"])
        self.assertEqual(
            report["duplicate_clusters"][0]["members"],
            [{"file": ".hidden/.batch.jsonl", "line": 1}, {"file": ".jsonl", "line": 1}],
        )


if __name__ == "__main__":
    unittest.main()
