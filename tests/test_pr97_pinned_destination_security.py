#!/usr/bin/env python3
"""Pinned-destination security contracts for PR #97."""

from __future__ import annotations

import errno
import json
import os
import shutil
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

import compose_destination  # noqa: E402
import compose_destination_creation  # noqa: E402
import compose_destination_writer  # noqa: E402
import compose_curated  # noqa: E402
from compose_curated_test_support import build_source_run  # noqa: E402


class OrdinaryComposeCommit(unittest.TestCase):
    def test_plain_compose_authenticates_the_complete_written_tree(self):
        """Directory scanning starts fresh after the initial empty-root check."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = root / "curated"
            summary = compose_curated.compose_run(
                build_source_run(root / "source"),
                destination,
            )

            self.assertTrue(destination.is_dir())
            self.assertGreater(summary["counts"]["retained"], 0)


class ComposePublishedCoordinates(unittest.TestCase):
    def test_factory_root_reads_physical_member_but_publishes_factory_coordinate(self):
        """A direct factory root retains its factory name in published evidence."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = build_source_run(root / "run")
            factory = run / "thalamic-trajectory-factory"
            destination = root / "curated"
            reads: list[str] = []
            original_read = compose_curated._read_exact_regular_file

            def capture_physical_read(source_root, relative, label):
                if label.startswith("compose source "):
                    reads.append(relative)
                return original_read(source_root, relative, label)

            with mock.patch.object(
                compose_curated,
                "_read_exact_regular_file",
                side_effect=capture_physical_read,
            ):
                summary = compose_curated.compose_run(factory, destination)

            coordinate = "thalamic-trajectory-factory/batch-r01.jsonl"
            self.assertEqual(reads, ["batch-r01.jsonl"])
            self.assertEqual(summary["outputs"][0]["path"], f"records/{coordinate}")
            manifest_path = destination / summary["manifest"]["path"]
            manifest = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual({entry["source_path"] for entry in manifest}, {coordinate})
            self.assertEqual(
                {entry["output_path"] for entry in manifest},
                {f"records/{coordinate}"},
            )
            self.assertTrue((destination / "records" / coordinate).is_file())

    def test_run_root_coordinates_are_not_double_prefixed(self):
        """A normal multi-factory run already carries factory-relative members."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            summary = compose_curated.compose_run(source, root / "curated")

            coordinate = "thalamic-trajectory-factory/batch-r01.jsonl"
            self.assertIn(
                f"records/{coordinate}",
                {item["path"] for item in summary["outputs"]},
            )
            self.assertNotIn(
                f"records/thalamic-trajectory-factory/{coordinate}",
                {item["path"] for item in summary["outputs"]},
            )

    def test_factory_root_coordinate_collisions_fail_closed(self):
        """Two physical members may not claim one published coordinate."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = build_source_run(root / "run")
            factory = run / "thalamic-trajectory-factory"
            nested = factory / factory.name / "batch-r01.jsonl"
            nested.parent.mkdir()
            nested.write_bytes((factory / "batch-r01.jsonl").read_bytes())

            with self.assertRaisesRegex(
                compose_curated.ComposeError,
                "published source coordinate collision",
            ):
                compose_curated.compose_run(factory, root / "curated")

            self.assertFalse((root / "curated").exists())


class ComposeRollbackIdentity(unittest.TestCase):
    def test_root_created_inode_cannot_be_replaced_before_first_observation(self):
        """A post-mkdir replacement with attacker bytes is never adopted."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "source")
            destination = root / "destination"
            abandoned = root / "abandoned-created-root"
            real_mkdir = os.mkdir
            replaced = False

            def replace_new_root(path, mode=0o777, *, dir_fd=None):
                nonlocal replaced
                real_mkdir(path, mode, dir_fd=dir_fd)
                if replaced or dir_fd is None:
                    return
                parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                created = parent / path
                created.rename(abandoned)
                real_mkdir(path, mode, dir_fd=dir_fd)
                (created / "attacker-extra").write_bytes(b"not authenticated\n")
                replaced = True

            with mock.patch.object(
                compose_destination_creation.os,
                "mkdir",
                side_effect=replace_new_root,
            ):
                with self.assertRaises(compose_destination.ComposeError):
                    compose_curated.compose_run(source, destination)

            self.assertTrue(replaced)
            self.assertFalse(destination.exists())
            self.assertTrue(abandoned.is_dir())

    def test_child_created_inode_cannot_be_replaced_before_first_observation(self):
        """A private child containing attacker bytes is never attached."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            pinned = compose_destination.create_pinned_destination(source, destination)
            real_mkdir = os.mkdir
            replaced = False

            def replace_new_child(path, mode=0o777, *, dir_fd=None):
                nonlocal replaced
                real_mkdir(path, mode, dir_fd=dir_fd)
                if replaced or dir_fd != pinned.destination_descriptor:
                    return
                parent = Path(os.readlink(f"/proc/self/fd/{dir_fd}"))
                created = parent / path
                created.rename(parent / "abandoned-created-child")
                real_mkdir(path, mode, dir_fd=dir_fd)
                (created / "attacker-extra").write_bytes(b"not authenticated\n")
                replaced = True

            try:
                with mock.patch.object(
                    compose_destination_writer.os,
                    "mkdir",
                    side_effect=replace_new_child,
                ):
                    with self.assertRaises(compose_destination.ComposeError):
                        compose_destination._open_pinned_child_directory(
                            pinned.destination_descriptor,
                            "records",
                            "destination",
                        )
            finally:
                pinned.cleanup()

            self.assertTrue(replaced)
            self.assertFalse(destination.exists())

    def test_leaf_rollback_never_calls_unlink(self):
        """Rollback must quarantine; a public-name unlink is never safe."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with (
                    mock.patch.object(
                        compose_destination,
                        "_write_all",
                        side_effect=OSError("simulated write failure"),
                    ),
                    mock.patch.object(
                        compose_destination_writer.os,
                        "unlink",
                        side_effect=AssertionError("rollback called unlink"),
                    ),
                ):
                    with self.assertRaisesRegex(OSError, "simulated write failure"):
                        compose_destination.write_pinned_new_bytes(
                            descriptor,
                            "artifact.json",
                            b"created by compose\n",
                        )
            finally:
                os.close(descriptor)

            self.assertFalse((root / "artifact.json").exists())

    def test_root_rollback_never_calls_rmtree(self):
        """A pinned root is detached for recovery, not removed by public name."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            pinned = compose_destination.create_pinned_destination(source, destination)
            with mock.patch.object(
                shutil,
                "rmtree",
                side_effect=AssertionError("rollback called rmtree"),
            ):
                pinned.cleanup()

            self.assertFalse(destination.exists())

    def test_unsupported_atomic_publication_fails_closed_without_deleting(self):
        """No unsafe rename or overwrite fallback may emulate NOREPLACE."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            pinned = compose_destination.create_pinned_destination(source, destination)
            with mock.patch.object(
                sys.modules[pinned.__class__.__module__],
                "_rename_noreplace",
                side_effect=OSError(errno.ENOSYS, "unsupported"),
            ):
                with self.assertRaisesRegex(
                    compose_destination.ComposeError,
                    "destination publication failed",
                ):
                    pinned.finish()

            self.assertFalse(destination.exists())
            self.assertTrue(pinned.closed)

    def test_initial_destination_failure_never_calls_rmtree(self):
        """Creation failure uses the same deletion-free rollback protocol."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            with (
                mock.patch.object(
                    compose_destination_creation,
                    "_open_created_destination",
                    side_effect=compose_destination.ComposeError("open failed"),
                ),
                mock.patch.object(
                    shutil,
                    "rmtree",
                    side_effect=AssertionError("rollback called rmtree"),
                ),
            ):
                with self.assertRaisesRegex(
                    compose_destination.ComposeError,
                    "open failed",
                ):
                    compose_destination.create_pinned_destination(source, destination)

            self.assertFalse(destination.exists())

    def test_failed_leaf_write_does_not_unlink_a_concurrent_replacement(self):
        """A failed write may remove its own inode, never the new name owner."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)

            def replace_then_fail(opened, payload):
                (root / "artifact.json").rename(root / "created-by-compose.json")
                (root / "artifact.json").write_bytes(b"concurrent replacement\n")
                raise OSError("simulated write failure")

            try:
                with mock.patch.object(
                    compose_destination,
                    "_write_all",
                    side_effect=replace_then_fail,
                ):
                    with self.assertRaisesRegex(OSError, "simulated write failure"):
                        compose_destination.write_pinned_new_bytes(
                            descriptor,
                            "artifact.json",
                            b"created by compose\n",
                        )
            finally:
                os.close(descriptor)

            self.assertEqual(
                (root / "artifact.json").read_bytes(),
                b"concurrent replacement\n",
            )

    def test_failed_child_pin_does_not_remove_a_concurrent_directory(self):
        """A failed child verification must retain a replacement directory."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)

            def replace_then_fail(_access, _child_descriptor):
                (root / "records").rename(root / "created-by-compose")
                (root / "records").mkdir()
                raise compose_destination.ComposeError("simulated pin failure")

            try:
                with mock.patch.object(
                    compose_destination.BoundDestinationAccess,
                    "verify_child",
                    replace_then_fail,
                ):
                    with self.assertRaisesRegex(
                        compose_destination.ComposeError,
                        "simulated pin failure",
                    ):
                        compose_destination._open_bound_destination_directory(
                            descriptor,
                            descriptor,
                            "records",
                            "destination",
                        )
            finally:
                os.close(descriptor)

            self.assertTrue((root / "records").is_dir())


class ComposeResolutionContract(unittest.TestCase):
    def test_directory_resolution_failures_are_compose_errors(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            for failure in (RuntimeError("loop"), OSError("denied")):
                with self.subTest(failure=type(failure).__name__):
                    with mock.patch.object(Path, "resolve", side_effect=failure):
                        with self.assertRaises(compose_destination.ComposeError):
                            compose_destination._require_exact_directory(
                                path,
                                "destination parent",
                            )

    def test_public_destination_resolution_failures_are_compose_errors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            real_resolve = Path.resolve

            def selectively_fail(path, *args, **kwargs):
                if path == destination:
                    raise RuntimeError("destination resolution denied")
                return real_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", selectively_fail):
                with self.assertRaisesRegex(
                    compose_destination.ComposeError,
                    "cannot resolve",
                ):
                    compose_destination.create_pinned_destination(source, destination)

            def fail_source(path, *args, **kwargs):
                if path == source:
                    raise OSError("source resolution denied")
                return real_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", fail_source):
                with self.assertRaisesRegex(
                    compose_destination.ComposeError,
                    "cannot resolve source/destination",
                ):
                    compose_destination.create_pinned_destination(source, destination)
