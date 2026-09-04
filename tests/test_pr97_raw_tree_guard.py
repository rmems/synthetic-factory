#!/usr/bin/env python3
"""Raw-tree guard security contracts for PR #97."""

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

import compose_destination  # noqa: E402
import export_members_path  # noqa: E402
import raw_tree_guard  # noqa: E402


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
            pinned = compose_destination.create_pinned_destination(source, destination)
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
            pinned = compose_destination.create_pinned_destination(source, destination)
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
