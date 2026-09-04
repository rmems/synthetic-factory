#!/usr/bin/env python3
"""Export-transaction security contracts for PR #97."""

from __future__ import annotations

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

import export_hf  # noqa: E402
import export_members  # noqa: E402
import export_members_read  # noqa: E402
from export_test_support import compose_fixture  # noqa: E402


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
