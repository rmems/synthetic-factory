#!/usr/bin/env python3
"""Hosted compose trees cannot enter a training-ready Hugging Face export."""

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

import export_hf
from export_test_support import compose_fixture
from rights_record import BLOCKER_PREFIX


class ResearchOnlyExportRefusal(unittest.TestCase):
    def test_unpatched_hosted_compose_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            with self.assertRaisesRegex(export_hf.ExportError, BLOCKER_PREFIX):
                export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())
