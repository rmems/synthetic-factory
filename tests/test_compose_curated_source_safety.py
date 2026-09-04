#!/usr/bin/env python3
"""Pinned source and calibration capture safety for composition."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    build_source_run,
    thalamic,
    write_jsonl,
)


class ComposeSourceCaptureSafety(unittest.TestCase):
    @staticmethod
    def _aliased_source(root, source, mutation):
        """Apply one alias mutation and return the source argument to compose."""

        if mutation == "source_root_symlink":
            source_argument = root / "source-alias"
            source_argument.symlink_to(source, target_is_directory=True)
            return source_argument
        if mutation == "directory_symlink":
            factory = source / "thalamic-trajectory-factory"
            target = root / "outside-factory"
            factory.replace(target)
            factory.symlink_to(target, target_is_directory=True)
            return source
        path = source / "thalamic-trajectory-factory" / "batch-r01.jsonl"
        target = root / "outside-source.jsonl"
        path.replace(target)
        if mutation == "file_symlink":
            path.symlink_to(target)
        else:
            os.link(target, path)
        return source

    def test_composition_rejects_source_symlink_and_hardlink_aliases(self):
        for mutation in (
            "source_root_symlink",
            "directory_symlink",
            "file_symlink",
            "file_hardlink",
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                source_argument = self._aliased_source(root, source, mutation)

                with self.assertRaisesRegex(compose_curated.ComposeError, "symlink|hard-link"):
                    compose_curated.compose_run(source_argument, root / "curated")
                self.assertFalse((root / "curated").exists())

    def test_composition_rejects_a_jsonl_named_source_directory(self):
        """A payload-looking directory may not disappear from the source census."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            (source / "ignored.jsonl").mkdir()

            with self.assertRaisesRegex(compose_curated.ComposeError, "not a regular file"):
                compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_composition_rejects_a_source_member_added_after_capture(self):
        """The published counts must describe one complete source snapshot."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            original_capture = compose_curated._captured_source_payloads

            def capture_then_add(resolved_source, source_members):
                payloads = original_capture(resolved_source, source_members)
                write_jsonl(
                    source / "thalamic-trajectory-factory" / "late.jsonl",
                    [thalamic("late-member")],
                )
                return payloads

            with mock.patch.object(
                compose_curated,
                "_captured_source_payloads",
                side_effect=capture_then_add,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "member set changed while capturing the source snapshot",
                ):
                    compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_composition_rejects_hard_linked_calibration_evidence(self):
        for mode in ("explicit", "source_run"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                original = root / "calibration-evidence.json"
                original.write_text('{"records":[]}\n', encoding="utf-8")
                if mode == "explicit":
                    calibration = root / "units-migration.json"
                    os.link(original, calibration)
                    kwargs = {"units_migration": calibration}
                else:
                    calibration = source / compose_curated.FFPC_UNITS_MIGRATION
                    os.link(original, calibration)
                    kwargs = {}

                with self.assertRaisesRegex(compose_curated.ComposeError, "hard-link"):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        **kwargs,
                    )
                self.assertFalse((root / "curated").exists())

    def test_composition_rejects_calibration_through_a_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            real_parent = root / "real-calibration-parent"
            real_parent.mkdir()
            calibration = real_parent / "units-migration.json"
            calibration.write_text('{"records":[]}\n', encoding="utf-8")
            alias_parent = root / "calibration-parent-alias"
            alias_parent.symlink_to(real_parent, target_is_directory=True)

            with self.assertRaisesRegex(
                compose_curated.ComposeError,
                "calibration parent must be an exact non-symlink directory",
            ):
                compose_curated.compose_run(
                    source,
                    root / "curated",
                    units_migration=alias_parent / calibration.name,
                )
            self.assertFalse((root / "curated").exists())

    def test_calibration_parent_swap_cannot_redirect_the_captured_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            calibration_parent = root / "calibration-parent"
            calibration_parent.mkdir()
            calibration = calibration_parent / "units-migration.json"
            calibration.write_text('{"records":[]}\n', encoding="utf-8")
            moved_parent = root / "original-calibration-parent"
            replacement_parent = root / "replacement-calibration-parent"
            replacement_parent.mkdir()
            (replacement_parent / calibration.name).write_text(
                '{"records":[{"scope":"ffpc-r99-a","usd_conversion_factor":2}]}\n',
                encoding="utf-8",
            )
            real_open = os.open
            swapped = False

            def swap_parent_before_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                should_swap = Path(path) == calibration_parent and dir_fd is None and not swapped
                if should_swap:
                    swapped = True
                    calibration_parent.rename(moved_parent)
                    calibration_parent.symlink_to(
                        replacement_parent,
                        target_is_directory=True,
                    )
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "open",
                side_effect=swap_parent_before_open,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "calibration parent changed while it was pinned",
                ):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        units_migration=calibration,
                    )

            self.assertTrue(swapped)
            self.assertFalse((root / "curated").exists())

    def test_composition_rejects_a_source_file_changed_during_pinned_read(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            target = source / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            write_jsonl(target, [thalamic("pinned-read")])
            original = target.read_bytes()
            real_read = compose_curated.os.read
            mutated = False

            def read_then_mutate(descriptor, size):
                nonlocal mutated
                chunk = real_read(descriptor, size)
                if chunk and not mutated:
                    mutated = True
                    target.write_bytes(original + b" ")
                return chunk

            with mock.patch.object(compose_curated.os, "read", side_effect=read_then_mutate):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "identity changed while reading"
                ):
                    compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_composition_rejects_nonfinite_calibration_even_when_ignored(self):
        for constant in ("NaN", "Infinity", "-Infinity", "1e400", "-1e400"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                calibration = root / "units-migration.json"
                calibration.write_text(
                    '{"records":[{"ignored":' + constant + "}]}" + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "invalid calibration JSON",
                ):
                    compose_curated.compose_run(
                        source,
                        root / "curated",
                        units_migration=calibration,
                    )
                self.assertFalse((root / "curated").exists())

    def test_completed_compose_artifacts_are_reauthenticated_before_finish(self):
        """A post-audit mutation must roll back the composed destination."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            destination = root / "curated"
            real_write = compose_curated._write_new_text

            def write_then_mutate(destination_target, relative, text):
                digest = real_write(destination_target, relative, text)
                if relative == compose_curated.SUMMARY_FILENAME:
                    member = (
                        destination_target.root
                        / compose_curated.RECORDS_DIRNAME
                        / "thalamic-trajectory-factory"
                        / "batch-r01.jsonl"
                    )
                    member.write_bytes(b"{}\n")
                return digest

            with mock.patch.object(
                compose_curated,
                "_write_new_text",
                side_effect=write_then_mutate,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "changed before compose commit",
                ):
                    compose_curated.compose_run(source, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
