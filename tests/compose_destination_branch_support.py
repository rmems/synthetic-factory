"""Temp-tree and descriptor helpers shared by the compose destination branch tests."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class TempTreeCase(unittest.TestCase):
    """One private temp root per test, released even when the test fails."""

    def setUp(self) -> None:
        super().setUp()
        self.root = Path(tempfile.mkdtemp(prefix="compose-branches-")).resolve()
        self.addCleanup(shutil.rmtree, self.root)

    def make_directory(self, *parts: str) -> Path:
        """Create one directory (and its parents) below the temp root."""

        path = self.root.joinpath(*parts)
        path.mkdir(parents=True)
        return path

    def open_directory(self, path: Path) -> int:
        """Open an exact directory descriptor that the test itself owns."""

        descriptor = os.open(path, DIRECTORY_FLAGS)
        self.addCleanup(os.close, descriptor)
        return descriptor

    def open_file(self, path: Path) -> int:
        """Open a read-only file descriptor that the test itself owns."""

        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        self.addCleanup(os.close, descriptor)
        return descriptor
