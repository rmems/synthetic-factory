#!/usr/bin/env python3
"""Physical-LF framing and compatibility regressions for training_audit."""

import json
import tempfile
import unittest
from pathlib import Path

from training_audit_test_helpers import thalamic

import training_audit

THALAMIC_FACTORY = "thalamic-trajectory-factory"


class TrainingAuditPhysicalFraming(unittest.TestCase):
    @staticmethod
    def _audit_payload(payload):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / THALAMIC_FACTORY / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_bytes(payload)
            return training_audit.audit_run(root)

    def test_bare_cr_is_not_a_boundary_or_a_mill_coordinate(self):
        foreign = thalamic("sir-r56-meili-swap-leftover3c-rebuild")
        foreign["meta"]["factory"] = "search-index-rebuild-factory"
        payload = (json.dumps(foreign) + "\r" + json.dumps(thalamic("ttf-clean")) + "\n").encode(
            "utf-8"
        )

        report = self._audit_payload(payload)

        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertEqual(report["mill_mix"]["records"], 0)
        self.assertEqual(report["mill_mix"]["quarantined_records"], [])
        self.assertTrue(
            any(
                "batch-r01.jsonl:1: JSON parse error" in item
                for item in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )

    def test_crlf_is_a_supported_physical_record_boundary(self):
        records = [thalamic("ttf-first"), thalamic("ttf-second")]
        payload = ("\r\n".join(map(json.dumps, records)) + "\r\n").encode()

        report = self._audit_payload(payload)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["totals"]["records"], 2)
        self.assertEqual(report["totals"]["eligible_records"], 2)
        self.assertEqual(report["bridge"]["distillation_records"], 2)

    def test_unicode_line_separators_remain_json_string_data(self):
        record = thalamic("ttf-unicode-separators")
        record["state"]["domain"] = "left\u2028middle\u2029right"
        payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

        report = self._audit_payload(payload)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["bridge"]["distillation_records"], 1)


class TrainingAuditCompatibilityExports(unittest.TestCase):
    def test_factory_slugs_remain_public(self):
        self.assertEqual(
            training_audit.BRIDGE_FACTORY_SLUG,
            "neuromorphic-event-language-bridge",
        )
        self.assertEqual(
            training_audit.THALAMIC_FACTORY_SLUG,
            THALAMIC_FACTORY,
        )

    def test_percentile_remains_public(self):
        self.assertEqual(training_audit.percentile([], 0.95), 0)
        self.assertEqual(training_audit.percentile([4, 1, 3, 2], 0.5), 2)
        self.assertEqual(training_audit.percentile([4, 1, 3, 2], 0.95), 4)


class TrainingAuditReportIdempotence(unittest.TestCase):
    def test_repeated_report_does_not_consume_factory_record_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / THALAMIC_FACTORY / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(thalamic("repeatable-report")) + "\n", encoding="utf-8")
            mill_findings, mill_mix = training_audit.index_mill_quarantine(root, [path])
            audit = training_audit._CorpusAudit(root, mill_findings, mill_mix)
            audit.observe_file(path)
            record_tokens = list(audit.factories[THALAMIC_FACTORY]["record_tokens"])

            first = audit.report()
            second = audit.report()

        self.assertEqual(second, first)
        self.assertEqual(
            audit.factories[THALAMIC_FACTORY]["record_tokens"],
            record_tokens,
        )
        self.assertEqual(
            training_audit.render_markdown(first),
            training_audit.render_markdown(first),
        )


if __name__ == "__main__":
    unittest.main()
