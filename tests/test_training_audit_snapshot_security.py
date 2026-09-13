#!/usr/bin/env python3
"""Training-audit snapshot security contracts for PR #97."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import training_audit_snapshot  # noqa: E402


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

            def should_swap(path, descriptor, already_swapped):
                if descriptor is None:
                    return False
                if already_swapped:
                    return False
                return Path(path) == relative

            def swap_before_open(path, flags, observed, *, dir_fd=None):
                nonlocal swapped
                if should_swap(path, dir_fd, swapped):
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
