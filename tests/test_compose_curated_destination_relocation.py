#!/usr/bin/env python3
"""Pinned destination relocation and rollback safety tests."""

import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
import compose_destination  # noqa: E402
from compose_curated_test_support import build_source_run  # noqa: E402


@dataclass(frozen=True)
class RelocationCase:
    destination: Path
    moved: Path
    pinned: compose_destination.PinnedDestination


@dataclass(frozen=True)
class RelocationExercise:
    case: RelocationCase
    patch_owner: Any
    patch_name: str
    side_effect: Callable[..., Any]
    operation: Callable[[], None]


@contextmanager
def pinned_relocation_case(root: Path) -> Iterator[RelocationCase]:
    """Create the shared pin topology for post-open relocation races."""

    source = root / "run"
    source.mkdir()
    destination = root / "curated"
    moved = root / "moved-curated"
    pinned = compose_curated.create_pinned_destination(source, destination)
    try:
        yield RelocationCase(destination, moved, pinned)
    finally:
        pinned.cleanup()


def assert_relocation_rolls_back(
    test: unittest.TestCase,
    exercise: RelocationExercise,
) -> None:
    """Exercise one post-open relocation and preserve rollback assertions."""

    with mock.patch.object(
        exercise.patch_owner,
        exercise.patch_name,
        side_effect=exercise.side_effect,
    ):
        with test.assertRaisesRegex(
            compose_curated.ComposeError,
            "destination changed while it was pinned",
        ):
            exercise.operation()
    test.assertEqual(list(exercise.case.moved.rglob("*")), [])


def relocation_exercise(case: RelocationCase, kind: str) -> RelocationExercise:
    """Build the syscall seam and operation for one relocation window."""

    if kind == "directory":
        real_open = compose_destination._open_pinned_child_directory

        def side_effect(parent_descriptor, name, label):
            descriptor, created = real_open(parent_descriptor, name, label)
            case.destination.rename(case.moved)
            return descriptor, created

        def operation():
            compose_destination._create_pinned_new_directory(
                case.pinned,
                compose_curated.RECORDS_DIRNAME,
                "destination",
            )

        return RelocationExercise(
            case,
            compose_destination,
            "_open_pinned_child_directory",
            side_effect,
            operation,
        )

    real_open = os.open

    def side_effect(path, flags, mode=0o777, *, dir_fd=None):
        descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
        if path == "row.jsonl":
            case.destination.rename(case.moved)
        return descriptor

    def operation():
        compose_curated.write_pinned_new_bytes(
            case.pinned,
            "row.jsonl",
            b"data\n",
        )

    return RelocationExercise(
        case,
        compose_destination.os,
        "open",
        side_effect,
        operation,
    )


def assert_relocation_kind_rolls_back(
    test: unittest.TestCase,
    kind: str,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        with pinned_relocation_case(Path(td)) as case:
            assert_relocation_rolls_back(test, relocation_exercise(case, kind))


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

        assert_relocation_kind_rolls_back(self, "directory")

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

        assert_relocation_kind_rolls_back(self, "leaf")

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

            def should_relocate_destination(path, dir_fd):
                return (
                    path == destination.name
                    and dir_fd is not None
                    and not relocated
                )

            def mkdir_then_relocate(path, mode=0o777, *, dir_fd=None):
                nonlocal relocated
                real_mkdir(path, mode, dir_fd=dir_fd)
                if should_relocate_destination(path, dir_fd):
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

    def test_source_member_path_rejects_embedded_nul(self):
        with self.assertRaisesRegex(
            compose_curated.ComposeError,
            "source member: unsafe relative path",
        ):
            compose_destination._validated_member_relative(
                "records/bad\0name.jsonl",
                "source member",
            )

    def test_destination_path_rejects_embedded_nul(self):
        with self.assertRaisesRegex(
            compose_curated.ComposeError,
            "destination: unsafe destination path",
        ):
            compose_destination._destination_write_parts(
                "records/bad\0name.jsonl",
                "destination",
            )


if __name__ == "__main__":
    unittest.main()
