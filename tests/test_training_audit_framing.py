#!/usr/bin/env python3
"""Physical-LF framing and compatibility regressions for training_audit."""

import json
import tempfile
import unittest
from pathlib import Path

from training_audit_test_helpers import thalamic

import training_audit
from exact_json import MAX_JSON_NESTING_DEPTH

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

    @staticmethod
    def _serialized(text):
        return (text + "\n").encode("utf-8")

    def _assert_refused(self, payload, expected_fragment, *, contract_errors=None, records=None):
        report = self._audit_payload(payload)
        self.assertFalse(report["training_ready"])
        if records is not None:
            self.assertEqual(report["totals"]["records"], records)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        if contract_errors is not None:
            self.assertEqual(report["totals"]["exact_json_contract_errors"], contract_errors)
        self.assertTrue(
            any(
                expected_fragment in item for item in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )
        return report

    def assert_exact_contract_error(self, serialized, expected_fragment):
        return self._assert_refused(
            self._serialized(serialized), expected_fragment, contract_errors=1
        )

    def assert_framing_refused(self, payload, expected_fragment):
        return self._assert_refused(payload, expected_fragment)

    def test_bare_cr_is_not_a_boundary_or_a_mill_coordinate(self):
        foreign = thalamic("sir-r56-meili-swap-leftover3c-rebuild")
        foreign["meta"]["factory"] = "search-index-rebuild-factory"
        payload = (json.dumps(foreign) + "\r" + json.dumps(thalamic("ttf-clean")) + "\n").encode(
            "utf-8"
        )

        report = self.assert_framing_refused(payload, "carriage returns")

        self.assertEqual(report["totals"]["records"], 0)
        self.assertEqual(report["mill_mix"]["records"], 0)
        self.assertEqual(report["mill_mix"]["quarantined_records"], [])

    def test_crlf_is_refused_by_the_training_export_contract(self):
        records = [thalamic("ttf-first"), thalamic("ttf-second")]
        payload = ("\r\n".join(map(json.dumps, records)) + "\r\n").encode()

        self.assert_framing_refused(payload, "carriage returns")

    def test_blank_physical_record_is_refused_by_the_training_export_contract(self):
        serialized = json.dumps(thalamic("ttf-blank"))

        self.assert_framing_refused(
            (serialized + "\n\n").encode("utf-8"),
            "blank line",
        )

    def test_missing_final_lf_is_refused_by_the_training_export_contract(self):
        serialized = json.dumps(thalamic("ttf-final-lf"))

        self.assert_framing_refused(
            serialized.encode("utf-8"),
            "must end with a newline",
        )

    def test_duplicate_object_keys_are_not_training_eligible(self):
        serialized = json.dumps(thalamic("ttf-duplicate-key"))
        serialized = serialized[:-1] + ',"duplicate":1,"duplicate":2}'

        self.assert_framing_refused(
            self._serialized(serialized), "duplicate JSON object key 'duplicate'"
        )

    def test_unicode_line_separators_remain_json_string_data(self):
        record = thalamic("ttf-unicode-separators")
        record["state"]["domain"] = "left\u2028middle\u2029right"
        payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

        report = self._audit_payload(payload)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["bridge"]["distillation_records"], 1)

    def test_exponent_overflow_is_not_training_eligible(self):
        serialized = json.dumps(thalamic("ttf-overflow")).replace(
            '"gate_snn": {',
            '"gate_snn": {"extra": 1e999, ',
            1,
        )

        self._assert_refused(
            self._serialized(serialized), "non-finite JSON number 1e999", records=1
        )

    def test_excessive_json_nesting_is_reported_instead_of_aborting(self):
        record = json.dumps(thalamic("ttf-deep")).replace(
            '"state": {',
            '"state": {"nested": '
            + ("[" * (MAX_JSON_NESTING_DEPTH + 1))
            + "0"
            + ("]" * (MAX_JSON_NESTING_DEPTH + 1))
            + ", ",
            1,
        )

        report = self.assert_exact_contract_error(record, "JSON nesting")

        self.assertEqual(
            report["totals"]["by_kind"],
            {"exact_json_contract_error": 1},
        )
        self.assertEqual(
            report["factories"][THALAMIC_FACTORY]["exact_json_contract_errors"],
            1,
        )

    def test_lone_surrogate_is_reported_instead_of_aborting_utf8_hashing(self):
        serialized = json.dumps(thalamic("ttf-surrogate")).replace(
            '"state": {',
            '"state": {"extension": "\\ud800", ',
            1,
        )

        self.assert_exact_contract_error(serialized, "unpaired UTF-16 surrogate")


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
