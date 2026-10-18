"""Issue #418: root-alias and descriptor-capability contracts of the audit.

The descriptor-mode cases run natively on hosts whose capability tables offer
descriptor-relative traversal. The path-mode cases are a capability-boundary
simulation on the same host, not native coverage of such a platform: the
tables omit the APIs and the APIs fail the way CPython reports a missing
platform capability.
"""

import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager, nullcontext, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "pipelines"))
sys.path.insert(0, str(TESTS))

import quality_gate  # noqa: E402
import quality_gate_audit  # noqa: E402
import test_quality_gate_input_integrity as integrity  # noqa: E402

REAL_RECORD = integrity.REAL_RECORD
SECOND_RECORD = '{"state":{"sim_or_real":"real","note":"second readable record"}}\n'
FAKE_O_BINARY = 1 << 30
NATIVE_SCANDIR, NATIVE_OPEN, NATIVE_STAT = os.scandir, os.open, os.stat


def _without(table, *functions):
    return frozenset(table) - set(functions)


def _accounting(report):
    """The report minus mode-specific text: warnings and OS error messages."""
    errors = report["errors"]
    unreadable = [
        {"file": example["file"], "error": example["error"].split(":", 1)[0]}
        for example in errors["unreadable_examples"]
    ]
    accounting = {key: value for key, value in report.items() if key != "warnings"}
    accounting["errors"] = {**errors, "unreadable_examples": unreadable}
    return accounting


def _refuse_dir_fd(dir_fd):
    if dir_fd is not None:
        raise NotImplementedError("dir_fd unavailable on this platform")


@contextmanager
def descriptor_apis_unavailable():
    """Select path traversal the way the import-time probe would on such a host."""
    real_scandir, real_open, real_stat = os.scandir, os.open, os.stat

    def scandir(path="."):
        if isinstance(path, int):
            raise TypeError("scandir: path should be string, bytes, os.PathLike or None, not int")
        return real_scandir(path)

    def open_without_dir_fd(path, flags, mode=0o777, *, dir_fd=None):
        _refuse_dir_fd(dir_fd)
        return real_open(path, flags, mode)

    def stat_without_dir_fd(path, *, dir_fd=None, follow_symlinks=True):
        _refuse_dir_fd(dir_fd)
        return real_stat(path, follow_symlinks=follow_symlinks)

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(os, "supports_fd", _without(os.supports_fd, NATIVE_SCANDIR))
        )
        stack.enter_context(
            patch.object(
                os, "supports_dir_fd", _without(os.supports_dir_fd, NATIVE_OPEN, NATIVE_STAT)
            )
        )
        probed = quality_gate_audit._descriptor_traversal_supported()
        stack.enter_context(patch.object(quality_gate_audit, "_DESCRIPTOR_TRAVERSAL", probed))
        stack.enter_context(patch.object(os, "scandir", scandir))
        stack.enter_context(patch.object(os, "open", open_without_dir_fd))
        stack.enter_context(patch.object(os, "stat", stat_without_dir_fd))
        yield


@contextmanager
def symlink_aware_stat_unavailable():
    """A host with neither lstat nor fstatat: stat cannot decline to follow links."""
    real_stat = os.stat

    def stat_following_only(path, *, dir_fd=None, follow_symlinks=True):
        if not follow_symlinks:
            raise NotImplementedError("stat: follow_symlinks unavailable on this platform")
        return real_stat(path, dir_fd=dir_fd)

    without_lstat = _without(os.supports_follow_symlinks, NATIVE_STAT)
    with (
        patch.object(os, "supports_follow_symlinks", without_lstat),
        patch.object(os, "stat", stat_following_only),
    ):
        yield


@contextmanager
def no_follow_stat_fails_on(target, failing_call):
    """Raise NotImplementedError on the ``failing_call``-th no-follow stat of ``target``.

    No real host loses lstat mid-run, so a host without it never reaches the
    later re-check sites; this reaches them to prove none of them can raise.
    """
    real_stat = os.stat
    calls = 0

    def stat(path, *, dir_fd=None, follow_symlinks=True):
        nonlocal calls
        if not follow_symlinks and Path(path) == target:
            calls += 1
            if calls == failing_call:
                raise NotImplementedError("stat: follow_symlinks unavailable on this platform")
        return real_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    with patch.object(os, "stat", stat):
        yield


@contextmanager
def binary_flag_platform(opened_flags):
    """Define O_BINARY as a Windows-style host would; strip it before the real open."""
    real_open = os.open

    def recording_open(path, flags, mode=0o777, *, dir_fd=None):
        opened_flags.append(flags)
        return real_open(path, flags & ~FAKE_O_BINARY, mode, dir_fd=dir_fd)

    with patch.dict(os.__dict__, {"O_BINARY": FAKE_O_BINARY}), patch.object(
        os, "open", recording_open
    ):
        yield


class RootAliasCases:
    """Root-alias contract, run once per traversal mode."""

    simulate_missing_descriptor_apis = False

    def traversal(self):
        """The host the audit runs on: native, or simulated without descriptor APIs."""
        if self.simulate_missing_descriptor_apis:
            return descriptor_apis_unavailable()
        return nullcontext()

    def audit_dir(self, run_dir):
        with self.traversal():
            return quality_gate.audit_run(run_dir, embedding_dedup=False)

    def aliased_run(self):
        target = self.root / "run"
        (target / "lane").mkdir(parents=True)
        (target / "lane" / "batch.jsonl").write_text(REAL_RECORD, encoding="utf-8")
        (target / "source.txt").write_text(SECOND_RECORD, encoding="utf-8")
        (target / "linked.jsonl").symlink_to(target / "source.txt")
        (target / "loop").symlink_to(target, target_is_directory=True)
        alias = self.root / "alias"
        alias.symlink_to(target, target_is_directory=True)
        return target, alias

    def test_symlinked_run_root_is_audited_like_its_target(self):
        target, alias = self.aliased_run()

        via_alias = self.audit_dir(alias)

        self.assertFalse(via_alias["blocked"], via_alias["blockers"])
        self.assertEqual(via_alias["counts"]["total"], 2)
        self.assertEqual(via_alias["errors"]["unreadable_files"], 0)
        self.assertEqual(via_alias, self.audit_dir(target))

    def test_retargeted_root_alias_blocks_instead_of_reading_the_new_target(self):
        _target, alias = self.aliased_run()
        impostor = self.root / "impostor"
        (impostor / "lane").mkdir(parents=True)
        for name in ("lane/batch.jsonl", "linked.jsonl"):
            (impostor / name).write_text(REAL_RECORD, encoding="utf-8")
        discover = quality_gate_audit._jsonl_paths

        def discover_then_retarget(run_dir, state):
            paths = discover(run_dir, state)
            alias.unlink()
            alias.symlink_to(impostor, target_is_directory=True)
            return paths

        with patch.object(quality_gate_audit, "_jsonl_paths", discover_then_retarget):
            report = self.audit_dir(alias)

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["errors"]["unreadable_files"], 2)
        self.assertEqual(
            [example["file"] for example in report["errors"]["unreadable_examples"]],
            ["lane/batch.jsonl", "linked.jsonl"],
        )
        for example in report["errors"]["unreadable_examples"]:
            self.assertIn("directory changed after discovery", example["error"])

    def test_root_replaced_by_a_file_after_the_directory_check_blocks(self):
        replaced = self.root / "replaced"
        replaced.write_text(REAL_RECORD, encoding="utf-8")

        # audit_run's is_dir() guard passed; the root is a file by scan time.
        with patch.object(Path, "is_dir", lambda _path, **_options: True):
            report = self.audit_dir(replaced)

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(
            report["errors"]["unreadable_examples"],
            [{"file": ".", "error": "OSError: run directory is not a directory"}],
        )

    def test_reads_request_binary_mode_where_the_platform_defines_it(self):
        target, _alias = self.aliased_run()
        opened_flags = []

        with binary_flag_platform(opened_flags):
            report = self.audit_dir(target)

        self.assertFalse(report["blocked"], report["blockers"])
        self.assertEqual(report["counts"]["total"], 2)
        file_opens = [flags for flags in opened_flags if not flags & getattr(os, "O_DIRECTORY", 0)]
        self.assertTrue(file_opens)
        self.assertTrue(all(flags & FAKE_O_BINARY for flags in file_opens))


class DescriptorTraversal(RootAliasCases, unittest.TestCase):
    def setUp(self):
        if not quality_gate_audit._descriptor_traversal_supported():
            self.skipTest("host lacks descriptor-relative traversal")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_supported_host_audits_with_descriptor_traversal(self):
        target, _alias = self.aliased_run()

        report = self.audit_dir(target)

        self.assertIs(quality_gate_audit._DESCRIPTOR_TRAVERSAL, True)
        self.assertNotIn(quality_gate_audit.PATH_TRAVERSAL_WARNING, report["warnings"])

    def test_manifest_inside_an_aliased_run_is_still_refused(self):
        target, alias = self.aliased_run()

        for manifest in (target / "quality-manifest.json", alias / "quality-manifest.json"):
            with (
                self.subTest(manifest=manifest.name, parent=manifest.parent.name),
                redirect_stdout(StringIO()),
                redirect_stderr(StringIO()) as errors,
                self.assertRaises(SystemExit) as caught,
            ):
                quality_gate.main([str(alias), "--json", "--manifest", str(manifest)])

            self.assertEqual(caught.exception.code, 2)
            self.assertIn("outside the audited run directory", errors.getvalue())
            self.assertFalse(manifest.exists())


class DescriptorCapabilityProbe(unittest.TestCase):
    def test_probe_requires_fd_scandir_and_dir_fd_open_and_stat(self):
        complete_fd = frozenset(os.supports_fd) | {os.scandir}
        complete_dir_fd = frozenset(os.supports_dir_fd) | {os.open, os.stat}
        tables = {
            "complete": (complete_fd, complete_dir_fd, True),
            "no fd scandir": (_without(complete_fd, os.scandir), complete_dir_fd, False),
            "no dir_fd open": (complete_fd, _without(complete_dir_fd, os.open), False),
            "no dir_fd stat": (complete_fd, _without(complete_dir_fd, os.stat), False),
        }
        for case, (fd_table, dir_fd_table, expected) in tables.items():
            with (
                self.subTest(case=case),
                patch.object(os, "supports_fd", fd_table),
                patch.object(os, "supports_dir_fd", dir_fd_table),
            ):
                self.assertIs(quality_gate_audit._descriptor_traversal_supported(), expected)


class PathTraversal(RootAliasCases, integrity.QualityGateInputIntegrity):
    """Every input-integrity case, re-run where descriptor APIs are unavailable."""

    simulate_missing_descriptor_apis = True

    def audit(self):
        with self.traversal():
            return super().audit()

    def audit_cli(self):
        with self.traversal():
            return super().audit_cli()

    def test_issue_418_one_record_directory_audits_without_descriptor_apis(self):
        self.write("batch.jsonl")

        report = self.audit()

        self.assertFalse(report["blocked"], report["blockers"])
        self.assertEqual(report["counts"]["total"], 1)
        self.assertEqual(report["errors"]["unreadable_files"], 0)
        self.assertIn(quality_gate_audit.PATH_TRAVERSAL_WARNING, report["warnings"])

    def test_path_traversal_keeps_accounting_and_discloses_its_weaker_guarantee(self):
        self.write("z.jsonl")
        self.write("lane/a.jsonl", REAL_RECORD + "{not json}\n")
        self.write("lane/nested/b.jsonl", SECOND_RECORD)
        self.write("note.txt", "not JSON")
        (self.root / "linked.jsonl").symlink_to(self.root / "note.txt")
        (self.root / "loop").symlink_to(self.root, target_is_directory=True)
        (self.root / "broken.jsonl").symlink_to(self.root / "absent")

        native = super().audit()
        simulated = self.audit()

        self.assertTrue(native["blocked"])
        self.assertEqual(native["counts"]["unreadable_files"], 1)
        self.assertEqual(native["counts"]["malformed_lines"], 2)
        disclosure = quality_gate_audit.PATH_TRAVERSAL_WARNING
        self.assertNotIn(disclosure, native["warnings"])
        self.assertEqual(simulated["warnings"].count(disclosure), 1)
        self.assertEqual(
            [warning for warning in simulated["warnings"] if warning != disclosure],
            native["warnings"],
        )
        self.assertEqual(_accounting(simulated), _accounting(native))

    def test_entries_block_where_stat_cannot_decline_to_follow_symlinks(self):
        self.write("batch.jsonl")
        self.write("lane/nested.jsonl", SECOND_RECORD)

        with symlink_aware_stat_unavailable():
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(
            [
                (example["file"], example["error"].split(":", 1)[0])
                for example in report["errors"]["unreadable_examples"]
            ],
            [("batch.jsonl", "OSError"), ("lane", "OSError")],
        )
        for example in report["errors"]["unreadable_examples"]:
            self.assertIn("cannot stat without following symlinks", example["error"])

    def assert_stat_capability_error_recorded(self, failing_call, unreadable):
        lane = self.write("lane/batch.jsonl").parent

        with no_follow_stat_fails_on(lane, failing_call):
            report = self.audit()

        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["total"], 0)
        examples = report["errors"]["unreadable_examples"]
        self.assertEqual([example["file"] for example in examples], [unreadable])
        self.assertIn("OSError: cannot stat without following symlinks", examples[0]["error"])

    def test_listing_recheck_records_a_stat_capability_error(self):
        self.assert_stat_capability_error_recorded(2, "lane")

    def test_read_recheck_records_a_stat_capability_error(self):
        self.assert_stat_capability_error_recorded(3, "lane/batch.jsonl")

    def test_cli_reports_the_path_traversal_warning(self):
        self.write("batch.jsonl")
        output = StringIO()

        with (
            self.traversal(),
            redirect_stdout(output),
            self.assertRaises(SystemExit) as caught,
        ):
            quality_gate.main([str(self.root), "--json", "--no-embedding-dedup"])

        self.assertEqual(caught.exception.code, 0)
        self.assertIn(
            quality_gate_audit.PATH_TRAVERSAL_WARNING,
            json.loads(output.getvalue())["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
