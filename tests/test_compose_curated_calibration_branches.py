"""Fail-closed branches of calibration selection and the compact audit report."""

from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated
import compose_curated_calibration as calibration
from compose_contract import REASON_EMPTY_CORPUS, ComposeError
from compose_destination_branch_support import TempTreeCase

EMPTY_CATALOG = b'{"records": []}\n'
NOT_REGULAR = "default calibration evidence is not an exact regular file: {}"
AUDIT_REPORT = MappingProxyType(
    {
        "totals": {"records": 2},
        "training_ready": 1,
        "blockers": ("rights: research_only",),
        "identity": {"coverage_pct": 100.0},
        "provenance": {"canonical_pct": 100.0},
        "preferences": {"context_purity_pct": 50.0},
    }
)


def _services(audit_run) -> calibration.CalibrationServices:
    """Calibration services where only the audit boundary is meaningful."""

    unused = mock.Mock(side_effect=AssertionError("audit_records must not call this service"))
    return calibration.CalibrationServices(
        unused, unused, unused, unused, unused, unused, audit_run
    )


class CalibrationSelectionTests(TempTreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = self.make_directory("run")
        self.default = self.source / "failure-as-fuel-preference-cascade" / "units-migration.json"

    def assert_load_refused(self, message: str, units_migration=None) -> None:
        with self.assertRaises(ComposeError) as caught:
            compose_curated._load_calibration(self.source, units_migration)

        self.assertEqual(str(caught.exception), message)

    def test_absent_evidence_selects_no_calibration(self):
        self.assertEqual(
            compose_curated._load_calibration(self.source, None),
            ({}, {"mode": "none", "path": None, "sha256": None, "records": 0}),
        )

    def test_canonical_source_evidence_is_loaded_with_its_digest(self):
        self.default.parent.mkdir()
        self.default.write_bytes(EMPTY_CATALOG)

        catalog, descriptor = compose_curated._load_calibration(self.source, None)

        self.assertEqual(catalog, {})
        self.assertEqual(
            descriptor,
            {
                "mode": "source_run",
                "path": str(self.default),
                "sha256": hashlib.sha256(EMPTY_CATALOG).hexdigest(),
                "records": 0,
            },
        )

    def test_directory_at_the_default_path_is_refused(self):
        self.default.mkdir(parents=True)

        self.assert_load_refused(NOT_REGULAR.format(self.default))

    def test_dangling_symlink_at_the_default_path_is_refused(self):
        self.default.parent.mkdir()
        self.default.symlink_to(self.root / "absent.json")

        self.assert_load_refused(NOT_REGULAR.format(self.default))

    def test_explicit_evidence_is_selected_over_the_default(self):
        explicit = self.root / "explicit.json"
        explicit.write_bytes(EMPTY_CATALOG)

        _catalog, descriptor = compose_curated._load_calibration(self.source, explicit)

        self.assertEqual((descriptor["mode"], descriptor["path"]), ("explicit", str(explicit)))

    def test_invalid_calibration_json_is_refused(self):
        explicit = self.root / "explicit.json"
        explicit.write_bytes(b"{")

        with self.assertRaises(ComposeError) as caught:
            compose_curated._load_calibration(self.source, explicit)

        self.assertRegex(
            str(caught.exception), "^" + re.escape(f"{explicit}: invalid calibration JSON: ")
        )


class CompactAuditTests(unittest.TestCase):
    def test_empty_corpus_is_never_training_ready(self):
        self.assertEqual(
            calibration.compact_audit_report(None, 0),
            {
                "run_dir": "records",
                "records": 0,
                "training_ready": False,
                "blockers": [REASON_EMPTY_CORPUS],
            },
        )

    def test_nonempty_corpus_requires_a_report(self):
        with self.assertRaises(ComposeError) as caught:
            calibration.compact_audit_report(None, 2)

        self.assertEqual(str(caught.exception), "nonempty compact audit requires an audit report")

    def test_report_fields_are_normalized(self):
        compact = calibration.compact_audit_report(AUDIT_REPORT, 2)

        self.assertIs(compact["training_ready"], True)
        self.assertEqual(compact["blockers"], ["rights: research_only"])
        self.assertEqual(compact["preference_context_purity_pct"], 50.0)

    def test_empty_records_are_not_audited(self):
        audit_run = mock.Mock(return_value=AUDIT_REPORT)

        compact = calibration.audit_records(Path("records"), 0, _services(audit_run))

        audit_run.assert_not_called()
        self.assertEqual(compact["blockers"], [REASON_EMPTY_CORPUS])

    def test_nonempty_records_are_audited_through_the_service(self):
        audit_run = mock.Mock(return_value=AUDIT_REPORT)

        compact = calibration.audit_records(Path("records"), 2, _services(audit_run))

        audit_run.assert_called_once_with(Path("records"))
        self.assertEqual(compact["records"], 2)


if __name__ == "__main__":
    unittest.main()
