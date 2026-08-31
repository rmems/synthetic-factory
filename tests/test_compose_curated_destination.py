#!/usr/bin/env python3
"""Filesystem safety for compose: alias refusal and pinned destination writes."""

import hashlib
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


class ComposeDestinationSafety(unittest.TestCase):
    """Split from test_compose_curated.py: source aliases, pinned writers."""

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

                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "symlink|hard-link"
                ):
                    compose_curated.compose_run(source_argument, root / "curated")
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

                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "hard-link"
                ):
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
                if Path(path) == calibration_parent and dir_fd is None and not swapped:
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

            with mock.patch.object(
                compose_curated.os, "read", side_effect=read_then_mutate
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "identity changed while reading"
                ):
                    compose_curated.compose_run(source, root / "curated")
            self.assertFalse((root / "curated").exists())

    def test_composition_rejects_nonfinite_calibration_even_when_ignored(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = build_source_run(root / "run")
                calibration = root / "units-migration.json"
                calibration.write_text(
                    '{"records":[{"ignored":' + constant + '}]}' + "\n",
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

    def test_refuses_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            compose_curated.compose_run(source, root / "curated")

            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, root / "curated")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, source / "nested")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, source)
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(source, root / "missing-parent" / "dest")
            with self.assertRaises(compose_curated.ComposeError):
                compose_curated.compose_run(root / "absent-run", root / "other")

            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()
            lexical_alias = raw / ".." / ".." / "safe" / "lexical-curated"
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "immutable raw"
            ):
                compose_curated.compose_run(source, lexical_alias)
            self.assertFalse((safe / "lexical-curated").exists())

            real_parent = root / "real-destination-parent"
            real_parent.mkdir()
            symlink_parent = root / "destination-parent-alias"
            symlink_parent.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "exact non-symlink directory"
            ):
                compose_curated.compose_run(source, symlink_parent / "curated")
            self.assertFalse((real_parent / "curated").exists())

    def test_pinned_writer_refuses_a_child_directory_swapped_for_a_symlink(self):
        """A swapped child must not steer curated payload into outputs/raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            destination.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            # The window the pin closes: another same-user process replaces the
            # freshly created child between ``mkdir`` and ``open``.
            (destination / compose_curated.RECORDS_DIRNAME).symlink_to(
                raw, target_is_directory=True
            )
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with self.assertRaises(compose_curated.ComposeError):
                    compose_curated._write_new_text(
                        descriptor,
                        f"{compose_curated.RECORDS_DIRNAME}/escaped.jsonl",
                        "{}\n",
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(sorted(path.name for path in raw.iterdir()), [])

    def test_pinned_writer_refuses_a_final_name_swapped_for_a_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            destination.mkdir()
            outside = root / "outside.jsonl"
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                (destination / "COMPOSE.json").symlink_to(outside)
                with self.assertRaises(compose_curated.ComposeError):
                    compose_curated._write_new_text(
                        descriptor, compose_curated.SUMMARY_FILENAME, "{}\n"
                    )
            finally:
                os.close(descriptor)
            self.assertFalse(outside.exists())

    def test_pinned_writer_rejects_unsafe_relative_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "curated"
            destination.mkdir()
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                for unsafe in ("", "/absolute.jsonl", "../escape.jsonl", "a/./b.jsonl"):
                    with self.subTest(unsafe=unsafe):
                        with self.assertRaises(compose_curated.ComposeError):
                            compose_curated._write_new_text(descriptor, unsafe, "{}\n")
            finally:
                os.close(descriptor)

    def test_pinned_writer_creates_nested_components_and_hashes_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "curated"
            destination.mkdir()
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            try:
                digest = compose_curated._write_new_text(
                    descriptor, "records/factory/rows.jsonl", "{}\n"
                )
            finally:
                os.close(descriptor)
            written = destination / "records" / "factory" / "rows.jsonl"
            self.assertEqual(written.read_text(encoding="utf-8"), "{}\n")
            self.assertEqual(
                digest, hashlib.sha256(b"{}\n").hexdigest()
            )

    def test_a_failed_composition_removes_the_new_destination(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            destination = root / "curated"

            real_write = compose_curated._write_new_text

            def fail_on_manifest(root_descriptor, relative, text):
                if relative.endswith(compose_curated.MANIFEST_FILENAME):
                    raise OSError("simulated manifest write failure")
                return real_write(root_descriptor, relative, text)

            with mock.patch.object(
                compose_curated, "_write_new_text", side_effect=fail_on_manifest
            ):
                with self.assertRaises(OSError):
                    compose_curated.compose_run(source, destination)
            self.assertFalse(destination.exists())

    def test_destination_parent_swap_cannot_redirect_creation_or_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            parent = root / "destination-parent"
            parent.mkdir()
            moved_parent = root / "original-parent-moved"
            replacement_parent = root / "replacement-parent"
            destination = parent / "curated"
            real_mkdir = os.mkdir
            swapped = False

            def swap_parent_before_create(path, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == destination.name and dir_fd is not None and not swapped:
                    swapped = True
                    parent.rename(moved_parent)
                    real_mkdir(replacement_parent, 0o755)
                    replacement_parent.rename(parent)
                return real_mkdir(path, mode, dir_fd=dir_fd)

            with mock.patch.object(
                compose_curated.os,
                "mkdir",
                side_effect=swap_parent_before_create,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "destination parent changed while it was pinned",
                ):
                    compose_curated.compose_run(source, destination)

            self.assertTrue(swapped)
            self.assertFalse((moved_parent / destination.name).exists())
            self.assertFalse((parent / destination.name).exists())


if __name__ == "__main__":
    unittest.main()
