#!/usr/bin/env python3
"""Hosted compose trees cannot enter a training-ready Hugging Face export."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipelines import export_hf
from tests.export_test_support import compose_fixture, allow_research_only_export
from pipelines.rights_record import BLOCKER_PREFIX


class ResearchOnlyExportRefusal(unittest.TestCase):
    def test_unpatched_hosted_compose_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            curated = compose_fixture(root)
            request = export_hf.ExportRequest(curated, root / "export")
            with self.assertRaisesRegex(export_hf.ExportError, BLOCKER_PREFIX):
                export_hf.export_run(request)
            self.assertFalse((root / "export").exists())


class RightsAuditBinding(unittest.TestCase):
    def test_export_replays_declared_rights_summary(self):
        with tempfile.TemporaryDirectory() as temp, allow_research_only_export():
            root = Path(temp)
            curated = compose_fixture(root)
            path = curated / "COMPOSE.json"
            summary = json.loads(path.read_text())
            summary["rights"]["lanes"]["training"] = summary["counts"]["retained"]
            summary["rights"]["training_exportable"] = True
            path.write_text(json.dumps(summary))
            request = export_hf.ExportRequest(curated, root / "export")
            with self.assertRaisesRegex(export_hf.ExportError, "rights"):
                export_hf.export_run(request)
            self.assertFalse((root / "export").exists())

    def test_export_rejects_audit_from_different_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as temp, allow_research_only_export():
            root = Path(temp)
            curated = compose_fixture(root)
            original = export_hf._training_ready_audit

            def mismatched_audit(*args):
                report, summary = original(*args)
                report["rights_manifest_sha256"] = "a" * 64
                return report, summary

            request = export_hf.ExportRequest(curated, root / "export")
            with patch.object(export_hf, "_training_ready_audit", mismatched_audit):
                with self.assertRaisesRegex(export_hf.ExportError, "rights.*manifest"):
                    export_hf.export_run(request)
            self.assertFalse((root / "export").exists())
