#!/usr/bin/env python3
"""Pinned destination creation, writes, and rollback safety for composition."""

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
import compose_destination  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    build_source_run,
)


class ComposeDestinationSafety(unittest.TestCase):
    def test_refuses_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            compose_curated.compose_run(source, root / "curated")

            with self.assertRaisesRegex(compose_curated.ComposeError, "refusing to overwrite"):
                compose_curated.compose_run(source, root / "curated")
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "cannot be written inside the source run"
            ):
                compose_curated.compose_run(source, source / "nested")
            with self.assertRaisesRegex(compose_curated.ComposeError, "refusing to overwrite"):
                compose_curated.compose_run(source, source)
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "destination parent is missing"
            ):
                compose_curated.compose_run(source, root / "missing-parent" / "dest")
            with self.assertRaisesRegex(compose_curated.ComposeError, "source run is missing"):
                compose_curated.compose_run(root / "absent-run", root / "other")

            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            safe = root / "safe"
            safe.mkdir()
            lexical_alias = raw / ".." / ".." / "safe" / "lexical-curated"
            with self.assertRaisesRegex(compose_curated.ComposeError, "immutable raw"):
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

    def test_pinned_writer_refuses_an_opened_child_moved_outside_the_root(self):
        """A pinned child renamed elsewhere must not receive later leaf writes."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            destination.mkdir()
            outside = root / "outside"
            outside.mkdir()
            descriptor = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
            real_open_child = compose_destination._open_pinned_child_directory
            moved = False

            def open_then_move(parent_descriptor, name, label):
                nonlocal moved
                child_descriptor, created = real_open_child(parent_descriptor, name, label)
                if not moved:
                    moved = True
                    (destination / name).rename(outside / name)
                return child_descriptor, created

            try:
                with mock.patch.object(
                    compose_destination,
                    "_open_pinned_child_directory",
                    side_effect=open_then_move,
                ):
                    with self.assertRaisesRegex(
                        compose_curated.ComposeError,
                        "escaped its pinned destination root",
                    ):
                        compose_curated._write_new_text(
                            descriptor, "records/factory/rows.jsonl", "{}\n"
                        )
            finally:
                os.close(descriptor)

            self.assertTrue(moved)
            self.assertFalse((outside / "records" / "factory" / "rows.jsonl").exists())

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
            self.assertEqual(digest, hashlib.sha256(b"{}\n").hexdigest())

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
                should_swap = (
                    (
                        path == destination.name
                        or str(path).startswith(".synthetic-factory-destination-")
                    )
                    and dir_fd is not None
                    and not swapped
                )
                if should_swap:
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
