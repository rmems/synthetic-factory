#!/usr/bin/env python3
"""Focused regressions for PR #97 filesystem and compatibility contracts."""

from __future__ import annotations

import errno
import os
import importlib
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
import export_hf  # noqa: E402
import export_members  # noqa: E402
import export_members_path  # noqa: E402
import export_members_read  # noqa: E402
import raw_tree_guard  # noqa: E402
import training_audit_snapshot  # noqa: E402
from export_test_support import compose_fixture  # noqa: E402
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
            pinned = compose_destination.create_pinned_destination(
                source,
                destination,
            )
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
            pinned = compose_destination.create_pinned_destination(
                source,
                destination,
            )
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
            pinned = compose_destination.create_pinned_destination(
                source,
                destination,
            )
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
                    compose_destination.create_pinned_destination(
                        source,
                        destination,
                    )

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


class RawTreeGuardIntegration(unittest.TestCase):
    def test_descriptor_raw_lookup_failures_are_compose_errors(self):
        with tempfile.TemporaryDirectory() as td:
            descriptor = os.open(td, os.O_RDONLY | os.O_DIRECTORY)
            binding = sys.modules[compose_destination.PinnedDestination.__module__]
            try:
                with mock.patch.object(
                    binding,
                    "is_under_raw",
                    side_effect=OSError("mount lookup denied"),
                ):
                    with self.assertRaisesRegex(
                        compose_destination.ComposeError,
                        "cannot verify descriptor",
                    ):
                        compose_destination._assert_descriptor_outside_raw(
                            descriptor,
                            "destination",
                        )
            finally:
                os.close(descriptor)

    def test_private_root_descriptor_rejects_an_opaque_raw_identity(self):
        """A private root moved under raw is rejected without lexical markers."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            opaque_raw = root / "opaque-evidence"
            opaque_raw.mkdir()
            pinned = compose_destination.create_pinned_destination(
                source,
                destination,
            )
            staged = destination.parent / pinned.staged_name
            staged.rename(opaque_raw / staged.name)
            try:
                with mock.patch.object(
                    raw_tree_guard,
                    "DEFAULT_RAW_OUTPUT_ROOT",
                    opaque_raw,
                ):
                    with self.assertRaisesRegex(
                        compose_destination.ComposeError,
                        "immutable raw evidence",
                    ):
                        compose_destination.write_pinned_new_bytes(
                            pinned,
                            "artifact.json",
                            b"{}\n",
                        )
            finally:
                pinned.cleanup()

            self.assertFalse(destination.exists())

    def test_private_child_descriptor_rejects_an_opaque_raw_identity(self):
        """Every opened child is checked by the inode-aware shared guard."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            destination = root / "destination"
            pinned = compose_destination.create_pinned_destination(
                source,
                destination,
            )
            compose_destination._create_pinned_new_directory(
                pinned,
                "records",
                "destination",
            )
            opaque_raw = pinned.root / "records"
            try:
                with mock.patch.object(
                    raw_tree_guard,
                    "DEFAULT_RAW_OUTPUT_ROOT",
                    opaque_raw,
                ):
                    with self.assertRaisesRegex(
                        compose_destination.ComposeError,
                        "immutable raw evidence",
                    ):
                        compose_destination.write_pinned_new_bytes(
                            pinned,
                            "records/artifact.json",
                            b"{}\n",
                        )
            finally:
                pinned.cleanup()

            self.assertFalse(destination.exists())

    def test_compose_and_export_use_inode_aware_raw_tree_guard(self):
        """An alias remains raw even when neither spelling contains outputs/raw."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw_root = root / "immutable-evidence"
            raw_root.mkdir()
            alias = root / "opaque-alias"
            alias.symlink_to(raw_root, target_is_directory=True)
            destination = alias / "derived"

            with mock.patch.object(
                raw_tree_guard,
                "DEFAULT_RAW_OUTPUT_ROOT",
                raw_root,
            ):
                self.assertTrue(compose_destination._is_under_raw(destination))
                self.assertTrue(export_members_path.is_under_raw(destination))

    def test_raw_tree_guard_retains_one_module_identity_in_both_import_orders(self):
        names = ("raw_tree_guard", "pipelines.raw_tree_guard")
        saved = {name: sys.modules.get(name) for name in names}
        package = importlib.import_module("pipelines")
        saved_attribute = getattr(package, "raw_tree_guard", None)
        try:
            for first in ("direct", "package"):
                with self.subTest(first=first):
                    for name in names:
                        sys.modules.pop(name, None)
                    if hasattr(package, "raw_tree_guard"):
                        delattr(package, "raw_tree_guard")
                    if first == "direct":
                        direct = importlib.import_module("raw_tree_guard")
                        packaged = importlib.import_module("pipelines.raw_tree_guard")
                    else:
                        packaged = importlib.import_module("pipelines.raw_tree_guard")
                        direct = importlib.import_module("raw_tree_guard")
                    self.assertIs(direct, packaged)
        finally:
            for name in names:
                sys.modules.pop(name, None)
                if saved[name] is not None:
                    sys.modules[name] = saved[name]
            if saved_attribute is not None:
                package.raw_tree_guard = saved_attribute


class ExportTransactionContracts(unittest.TestCase):
    def test_finish_reauthenticates_bytes_mutated_through_held_descriptor(self):
        """The real finish boundary catches staged-byte mutation before publish."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            destination = root / "export"
            real_finish = export_hf._finish_pinned_destination

            def mutate_then_finish(pinned):
                descriptor = os.open(pinned.root / export_hf.TRAIN_PATH, os.O_WRONLY)
                try:
                    os.pwrite(descriptor, b"corrupted\n", 0)
                finally:
                    os.close(descriptor)
                return real_finish(pinned)

            with mock.patch.object(
                export_hf,
                "_finish_pinned_destination",
                side_effect=mutate_then_finish,
            ):
                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, destination)

            self.assertFalse(destination.exists())

    def test_finish_rejects_an_undeclared_staged_entry(self):
        """Publication authenticates the complete tree, not only known files."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            destination = root / "export"
            real_finish = export_hf._finish_pinned_destination

            def add_extra_then_finish(pinned):
                (pinned.root / "undeclared-extra").write_bytes(b"not declared\n")
                return real_finish(pinned)

            with mock.patch.object(
                export_hf,
                "_finish_pinned_destination",
                side_effect=add_extra_then_finish,
            ):
                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, destination)

            self.assertFalse(destination.exists())

    def test_publication_collision_after_final_authentication_fails_closed(self):
        """The no-replace publish is the export's public linearization point."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            destination = root / "export"
            real_finish = export_hf._finish_pinned_destination

            def race_at_finish(pinned):
                if destination.exists():
                    (destination / export_hf.TRAIN_PATH).write_bytes(b"mutated\n")
                else:
                    destination.mkdir()
                    (destination / "concurrent-owner").write_bytes(b"keep me\n")
                return real_finish(pinned)

            with mock.patch.object(
                export_hf,
                "_finish_pinned_destination",
                side_effect=race_at_finish,
            ):
                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, destination)

            self.assertEqual(
                (destination / "concurrent-owner").read_bytes(),
                b"keep me\n",
            )

    def test_source_mutation_after_destination_authentication_aborts_export(self):
        """Commit must still represent the authenticated curated member set."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            records = curated / "records"
            destination = root / "export"
            real_write_metadata = export_hf._write_export_metadata

            def authenticate_then_add(*args, **kwargs):
                result = real_write_metadata(*args, **kwargs)
                late = records / "late-factory" / "late.jsonl"
                late.parent.mkdir()
                late.write_bytes(b'{}\n')
                return result

            with mock.patch.object(
                export_hf,
                "_write_export_metadata",
                side_effect=authenticate_then_add,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "curated member set changed",
                ):
                    export_hf.export_run(curated, destination)

            self.assertFalse(destination.exists())

    def test_lstat_failures_stay_inside_export_error_contract(self):
        """Filesystem inspection errors must not leak as raw OSError values."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "member.jsonl"
            member.write_bytes(b'{}\n')

            with mock.patch.object(Path, "lstat", side_effect=OSError("denied")):
                with self.assertRaisesRegex(export_hf.ExportError, "cannot inspect"):
                    export_members._read_exact_regular_file(
                        root,
                        member.name,
                        "curated payload",
                    )

    def test_pre_and_post_read_lstat_failures_are_export_errors(self):
        """Both descriptor-authentication lstat phases normalize OSError."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "member.jsonl"
            member.write_bytes(b'{}\n')
            original = member.lstat()
            for observations in (
                [OSError("pre-read denied")],
                [original, OSError("post-read denied")],
            ):
                with self.subTest(phase=len(observations)):
                    with (
                        mock.patch.object(
                            export_members_read,
                            "compose_member_path",
                            return_value=member,
                        ),
                        mock.patch.object(
                            Path,
                            "lstat",
                            side_effect=observations,
                        ),
                    ):
                        with self.assertRaisesRegex(
                            export_members.ExportError,
                            "cannot inspect declared file",
                        ):
                            export_members_read.read_exact_regular_file(
                                root,
                                member.name,
                                "curated payload",
                            )

    def test_export_error_remains_in_star_import_surface(self):
        self.assertIn("ExportError", export_members.__all__)
        self.assertIs(getattr(export_members, "ExportError"), export_members.ExportError)

    def test_member_path_rejects_embedded_nul(self):
        with self.assertRaises(export_members.ExportError):
            export_members._member_relative("factory/bad\0.jsonl", "member")


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
                    compose_destination.create_pinned_destination(
                        source,
                        destination,
                    )

            def fail_source(path, *args, **kwargs):
                if path == source:
                    raise OSError("source resolution denied")
                return real_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", fail_source):
                with self.assertRaisesRegex(
                    compose_destination.ComposeError,
                    "cannot resolve source/destination",
                ):
                    compose_destination.create_pinned_destination(
                        source,
                        destination,
                    )


class AuditSnapshotContracts(unittest.TestCase):
    def test_legacy_member_swap_before_open_is_rejected(self):
        """Legacy trees without manifests still bind bytes to the listed inode."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            relative = Path("batch-r01.jsonl")
            member = root / relative
            member.write_bytes(b'{"id":"original"}\n')
            original_open = training_audit_snapshot.open_audit_descriptor
            swapped = False

            def swap_before_open(path, flags, observed, *, dir_fd=None):
                nonlocal swapped
                if dir_fd is not None and Path(path) == relative and not swapped:
                    swapped = True
                    member.rename(root / "original.jsonl")
                    member.write_bytes(b'{"id":"replacement"}\n')
                return original_open(path, flags, observed, dir_fd=dir_fd)

            with self.assertRaisesRegex(ValueError, "identity changed"):
                training_audit_snapshot.read_pinned_member(
                    root,
                    relative,
                    open_descriptor=swap_before_open,
                )

            self.assertTrue(swapped)

    def test_snapshot_dot_and_nul_paths_are_rejected(self):
        for unsafe in (".", "factory/bad\0.jsonl"):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                training_audit_snapshot.validate_snapshot_path(unsafe)


if __name__ == "__main__":
    unittest.main()
