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
import compose_destination  # noqa: E402
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

    def test_composition_rejects_a_jsonl_named_source_directory(self):
        """A payload-looking directory may not disappear from the source census."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            (source / "ignored.jsonl").mkdir()

            with self.assertRaisesRegex(
                compose_curated.ComposeError, "not a regular file"
            ):
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
                should_swap = (
                    Path(path) == calibration_parent
                    and dir_fd is None
                    and not swapped
                )
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

            with mock.patch.object(
                compose_curated.os, "read", side_effect=read_then_mutate
            ):
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

    def test_completed_compose_artifacts_are_reauthenticated_before_finish(self):
        """A post-audit mutation must roll back the composed destination."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            destination = root / "curated"
            real_write = compose_curated._write_new_text

            def write_then_mutate(root_descriptor, relative, text):
                digest = real_write(root_descriptor, relative, text)
                if relative == compose_curated.SUMMARY_FILENAME:
                    member = (
                        destination
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

    def test_refuses_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            compose_curated.compose_run(source, root / "curated")

            with self.assertRaisesRegex(
                compose_curated.ComposeError, "refusing to overwrite"
            ):
                compose_curated.compose_run(source, root / "curated")
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "cannot be written inside the source run"
            ):
                compose_curated.compose_run(source, source / "nested")
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "refusing to overwrite"
            ):
                compose_curated.compose_run(source, source)
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "destination parent is missing"
            ):
                compose_curated.compose_run(source, root / "missing-parent" / "dest")
            with self.assertRaisesRegex(
                compose_curated.ComposeError, "source run is missing"
            ):
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
                child_descriptor, created = real_open_child(
                    parent_descriptor, name, label
                )
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
                should_swap = (
                    path == destination.name
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


class PinnedWriterRawRelocation(unittest.TestCase):
    """Codex #97 P1: a relocated pinned destination must not receive writes.

    Descriptor-relative opens keep following a directory a same-user process
    renames, so an opened destination moved under ``outputs/raw`` would
    otherwise receive derived files inside immutable raw evidence.
    """

    def test_destination_renamed_into_raw_refuses_the_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            pinned = compose_curated.create_pinned_destination(
                source, root / "curated"
            )
            try:
                os.rename(root / "curated", raw / "curated")
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "relocated into immutable raw evidence",
                ):
                    compose_curated.write_pinned_new_bytes(
                        pinned,
                        "records/x.jsonl",
                        b"data\n",
                    )
                leaked = [
                    entry
                    for entry in (raw / "curated").rglob("*")
                    if entry.is_file()
                ]
                self.assertEqual(leaked, [])
            finally:
                try:
                    pinned.cleanup()
                except compose_curated.ComposeError:
                    pass

    def test_destination_renamed_elsewhere_refuses_the_write(self):
        """The pinned root remains bound to the originally requested path."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            destination = root / "curated"
            moved = root / "moved-curated"
            pinned = compose_curated.create_pinned_destination(source, destination)
            try:
                destination.rename(moved)
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "destination changed while it was pinned",
                ):
                    compose_curated.write_pinned_new_bytes(
                        pinned,
                        "records/x.jsonl",
                        b"data\n",
                    )
                self.assertEqual(list(moved.rglob("*")), [])
            finally:
                pinned.cleanup()

    def test_post_create_root_relocation_rolls_back_directory(self):
        """A root rename after mkdir must remove the just-created directory."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            destination = root / "curated"
            moved = root / "moved-curated"
            pinned = compose_curated.create_pinned_destination(source, destination)
            real_open = compose_destination._open_pinned_child_directory

            def open_then_move(parent_descriptor, name, label):
                descriptor, created = real_open(parent_descriptor, name, label)
                destination.rename(moved)
                return descriptor, created

            try:
                with mock.patch.object(
                    compose_destination,
                    "_open_pinned_child_directory",
                    side_effect=open_then_move,
                ):
                    with self.assertRaisesRegex(
                        compose_curated.ComposeError,
                        "destination changed while it was pinned",
                    ):
                        compose_destination._create_pinned_new_directory(
                            pinned,
                            compose_curated.RECORDS_DIRNAME,
                            "destination",
                        )
                self.assertEqual(list(moved.rglob("*")), [])
            finally:
                pinned.cleanup()

    def test_reused_component_survives_post_open_binding_failure(self):
        """Rollback must not remove an empty directory it did not create."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            destination = root / "curated"
            pinned = compose_curated.create_pinned_destination(source, destination)
            existing = destination / compose_curated.RECORDS_DIRNAME
            existing.mkdir()
            real_verify = compose_destination._verify_destination_target
            calls = 0

            def fail_after_open(target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise compose_curated.ComposeError(
                        "simulated post-open binding failure"
                    )
                real_verify(target)

            try:
                with mock.patch.object(
                    compose_destination,
                    "_verify_destination_target",
                    side_effect=fail_after_open,
                ):
                    with self.assertRaisesRegex(
                        compose_curated.ComposeError,
                        "simulated post-open binding failure",
                    ):
                        compose_curated.write_pinned_new_bytes(
                            pinned,
                            f"{compose_curated.RECORDS_DIRNAME}/row.jsonl",
                            b"data\n",
                        )
                self.assertTrue(existing.is_dir())
                self.assertEqual(list(existing.iterdir()), [])
            finally:
                pinned.cleanup()

    def test_post_leaf_open_root_relocation_rolls_back_file(self):
        """A root rename after leaf creation must remove the new leaf."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            destination = root / "curated"
            moved = root / "moved-curated"
            pinned = compose_curated.create_pinned_destination(source, destination)
            real_open = os.open

            def open_then_move(path, flags, mode=0o777, *, dir_fd=None):
                descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
                if path == "row.jsonl":
                    destination.rename(moved)
                return descriptor

            try:
                with mock.patch.object(
                    compose_destination.os,
                    "open",
                    side_effect=open_then_move,
                ):
                    with self.assertRaisesRegex(
                        compose_curated.ComposeError,
                        "destination changed while it was pinned",
                    ):
                        compose_curated.write_pinned_new_bytes(
                            pinned,
                            "row.jsonl",
                            b"data\n",
                        )
                self.assertEqual(list(moved.rglob("*")), [])
            finally:
                pinned.cleanup()

    def test_closed_pin_rejects_revalidation(self):
        """A released destination pin cannot be reused as a write authority."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            pinned = compose_curated.create_pinned_destination(
                source, root / "curated"
            )
            pinned.finish()
            with self.assertRaisesRegex(
                compose_curated.ComposeError,
                "destination pin was already closed",
            ):
                pinned.verify_binding()

    def test_destination_parent_relocated_into_raw_refuses_creation(self):
        """A pinned parent moved into raw must not receive the destination."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            parent = root / "destination-parent"
            parent.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            relocated_parent = raw / parent.name
            destination = parent / "curated"
            original = compose_destination._refuse_existing_destination

            def relocate_before_creation(parent_descriptor, requested_destination):
                original(parent_descriptor, requested_destination)
                parent.rename(relocated_parent)

            with mock.patch.object(
                compose_destination,
                "_refuse_existing_destination",
                relocate_before_creation,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "relocated into immutable raw evidence",
                ):
                    compose_curated.create_pinned_destination(source, destination)

            self.assertFalse((relocated_parent / destination.name).exists())

    def test_post_mkdir_parent_relocation_is_rolled_back(self):
        """Destination creation must not survive a parent move into raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            parent = root / "destination-parent"
            parent.mkdir()
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            relocated_parent = raw / parent.name
            destination = parent / "curated"
            real_mkdir = os.mkdir
            relocated = False

            def mkdir_then_relocate(path, mode=0o777, *, dir_fd=None):
                nonlocal relocated
                real_mkdir(path, mode, dir_fd=dir_fd)
                if path == destination.name and dir_fd is not None and not relocated:
                    relocated = True
                    parent.rename(relocated_parent)

            with mock.patch.object(
                compose_destination.os,
                "mkdir",
                side_effect=mkdir_then_relocate,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "relocated into immutable raw evidence",
                ):
                    compose_curated.create_pinned_destination(source, destination)

            self.assertTrue(relocated)
            self.assertFalse((relocated_parent / destination.name).exists())

    def test_initial_compose_directories_refuse_a_relocated_destination(self):
        """Codex #97 P1: the first mkdirs must not follow a raw relocation.

        ``compose_run`` used to create ``records/`` and ``manifest/`` through
        the ``/proc/self/fd`` root path with no residency check, so a
        destination renamed under ``outputs/raw`` right after it was pinned
        received those directories inside immutable raw evidence — before the
        checked leaf writer ever ran.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            raw = root / "outputs" / "raw"
            raw.mkdir(parents=True)
            original = compose_curated.create_pinned_destination

            def relocating(source_dir, destination):
                pinned = original(source_dir, destination)
                os.rename(destination, raw / "curated")
                return pinned

            with mock.patch.object(
                compose_curated, "create_pinned_destination", relocating
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError,
                    "relocated into immutable raw evidence",
                ):
                    compose_curated.compose_run(source, root / "curated")
            self.assertEqual(list((raw / "curated").rglob("*")), [])

    def test_source_and_calibration_fifo_swaps_are_rejected_without_blocking(self):
        """Codex #97 P2: a FIFO swapped in after lstat must not hang compose.

        O_NOFOLLOW does not protect against a file-type swap, and a read-only
        FIFO open blocks until a writer appears; O_NONBLOCK lets both the
        source-member open and the pinned calibration-child open return so
        the identity validation can reject the descriptor.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member_fifo = root / "member.jsonl"
            os.mkfifo(member_fifo)
            with mock.patch.object(
                compose_destination,
                "_source_member_path",
                lambda *args, **kwargs: member_fifo,
            ):
                with self.assertRaisesRegex(
                    compose_curated.ComposeError, "not a regular file"
                ):
                    compose_destination._read_exact_regular_file(
                        root, "member.jsonl", "source member"
                    )

            calibration_fifo = root / "calibration.json"
            os.mkfifo(calibration_fifo)
            parent = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                before, descriptor = compose_destination._open_pinned_child(
                    "calibration.json", parent, "units-migration calibration"
                )
                try:
                    with self.assertRaisesRegex(
                        compose_curated.ComposeError, "not a regular file"
                    ):
                        compose_destination._read_pinned_child_bytes(
                            "calibration.json",
                            parent,
                            descriptor,
                            before,
                            "units-migration calibration",
                        )
                finally:
                    os.close(descriptor)
            finally:
                os.close(parent)


if __name__ == "__main__":
    unittest.main()
