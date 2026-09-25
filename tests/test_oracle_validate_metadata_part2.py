"""Focused cases split from test_oracle_validate_metadata.py."""

import copy
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test_oracle_validate_metadata import (
    GOLDEN,
    GoldenRunFixture,
    oracle_validate,
)


class ManifestVocabularyTest(GoldenRunFixture):
    """The manifest's top-level vocabulary is closed."""

    def test_an_unauthenticated_manifest_sibling_is_rejected(self):
        self.assert_reports(
            lambda manifest: manifest.__setitem__(
                "external_attestation", "verified-on-hardware"
            ),
            "manifest carries unauthenticated sibling keys: external_attestation",
        )

    def test_every_generated_manifest_key_is_declared(self):
        self.assertEqual(
            set(self.manifest) - oracle_validate.MANIFEST_ALLOWED_KEYS, set()
        )

    def test_an_unauthenticated_availability_sibling_is_rejected(self):
        self.assert_reports(
            lambda manifest: manifest["oracle_availability"].__setitem__(
                "external_attestation", "verified-on-hardware"
            ),
            "oracle_availability carries unauthenticated sibling keys: external_attestation",
        )


class RunBoundCommitTest(GoldenRunFixture):
    """Run-level validation binds records to the manifest's resolved commit."""

    def test_a_record_with_a_foreign_commit_is_rejected_without_resolving(self):
        from oracle_grounded import canon, oracles

        parsed = copy.deepcopy(self.records[0].item)
        parsed["oracle"]["commit"] = "b" * 40
        body = (canon.dumps_record(parsed) + "\n").encode("utf-8")
        snapshot = oracle_validate.FileSnapshot(
            path=Path(self.records[0].where.rsplit(":", 1)[0]),
            relative=self.records[0].relative,
            body=body,
            device=0,
            inode=0,
        )
        expected = self.manifest["oracle_commit"]
        with mock.patch.object(
            oracles,
            "resolve_source_commit",
            side_effect=AssertionError("per-record resolution must not run"),
        ):
            totals, errors, _parsed = oracle_validate.validate_file(
                snapshot,
                oracle_validate.ValidationContext(),
                expected_commit=expected,
            )
        self.assertEqual(totals["invalid"], 1)
        self.assertTrue(
            any(
                "does not match the run manifest's resolved oracle commit" in e
                for e in errors
            ),
            errors,
        )

    def test_a_matching_commit_still_validates_through_the_bound_path(self):
        snapshot = self.snapshots[0]
        totals, errors, _parsed = oracle_validate.validate_file(
            snapshot,
            oracle_validate.ValidationContext(),
            expected_commit=self.manifest["oracle_commit"],
        )
        self.assertEqual(errors, [])
        self.assertEqual(totals["invalid"], 0)
        self.assertGreater(totals["records"], 0)

    def test_an_invalid_manifest_commit_still_binds_records(self):
        # Breaking the manifest's own commit must not regain per-record
        # repository lookups: the manifest value stays the comparison
        # sentinel, so mismatching records are rejected without git.
        from oracle_grounded import oracles

        with tempfile.TemporaryDirectory(prefix="oracle-bind-") as temp:
            run = Path(temp) / "run"
            shutil.copytree(GOLDEN, run)
            manifest = json.loads((run / "manifest.json").read_text())
            manifest["oracle_commit"] = "c" * 40
            (run / "manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            calls = []
            real = oracles.resolve_source_commit

            def counting(value, repo_root=None):
                calls.append(value)
                return real(value, repo_root)

            with mock.patch.object(oracles, "resolve_source_commit", side_effect=counting):
                report, errors = oracle_validate.validate_run(oracle_validate.ValidationContext(run))
        self.assertGreater(report["invalid"], 0)
        self.assertTrue(
            any("does not match the run manifest" in e for e in errors), errors[:5]
        )
        # One pre-resolution in validate_run plus the header check; never one
        # per record.
        self.assertLessEqual(len(calls), 4, calls)


class SchemaFindingBudgetTest(unittest.TestCase):
    """Untrusted element counts cannot inflate schema findings unboundedly."""

    def test_array_item_findings_are_capped(self):
        from oracle_grounded import schema_validation

        schema = {"type": "array", "items": {"type": "number"}}
        value = ["x"] * (schema_validation.MAX_SCHEMA_FINDINGS * 50)
        errors = schema_validation._validate(value, schema, schema, "$.signal")
        self.assertLessEqual(len(errors), schema_validation.MAX_SCHEMA_FINDINGS + 2)
        self.assertTrue(any("further findings suppressed" in e for e in errors), errors[-2:])

    def test_unknown_key_findings_are_capped(self):
        from oracle_grounded import schema_validation

        schema = {"type": "object", "additionalProperties": False}
        value = {f"key{i}": i for i in range(schema_validation.MAX_SCHEMA_FINDINGS * 50)}
        errors = schema_validation._validate(value, schema, schema, "$")
        self.assertLessEqual(len(errors), schema_validation.MAX_SCHEMA_FINDINGS + 2)
        self.assertTrue(any("further findings suppressed" in e for e in errors), errors[-2:])


class StrictParsingTest(unittest.TestCase):
    """The JSON boundary refuses what canonical JSON cannot represent."""

    def test_overflowing_numeric_literals_are_rejected_at_parse_time(self):
        # parse_constant only sees the bare NaN/Infinity tokens; a literal
        # that merely overflows float conversion (1e400) must be refused by
        # the parser itself, not depend on a later non-finite walk.
        for payload in ('{"x": 1e400}', '{"x": -1e400}', '[1e309]'):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    oracle_validate.strict_json_loads(payload)

    def test_non_finite_tokens_are_still_rejected(self):
        for payload in ('{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    oracle_validate.strict_json_loads(payload)

    def test_finite_floats_still_parse_exactly(self):
        self.assertEqual(
            oracle_validate.strict_json_loads('{"x": 1.5, "y": -0.25}'),
            {"x": 1.5, "y": -0.25},
        )


class _FakeMetadataContext:
    """Collects reports for the availability cross-check unit tests."""

    def __init__(self):
        self.errors = []
        self.probe_values = {}

    def report(self, message):
        self.errors.append(message)


class AvailabilityShapeTest(unittest.TestCase):
    """Malformed availability shapes report findings instead of skipping.

    The record envelope and the manifest runtime-name check already reject
    these shapes upstream; these branches must still fail closed on their
    own rather than silently passing a malformed block.
    """

    def test_a_non_object_availability_block_is_reported(self):
        context = _FakeMetadataContext()
        parsed = mock.Mock(where="records.jsonl:1")
        oracle_validate._record_availability_errors(
            parsed, {"availability": "not-an-object"}, context
        )
        self.assertTrue(
            any("malformed runtime availability" in e for e in context.errors),
            context.errors,
        )

    def test_a_malformed_record_probe_is_reported(self):
        context = _FakeMetadataContext()
        parsed = mock.Mock(where="records.jsonl:1")
        oracle_validate._record_availability_errors(
            parsed,
            {"availability": {"runtimes": ["not-a-probe", {"runtime": 7}]}},
            context,
        )
        self.assertEqual(
            [e for e in context.errors if "malformed runtime availability" in e],
            ["records.jsonl:1 has malformed runtime availability"] * 2,
        )

    def test_noncanonical_probe_values_report_the_original_error_kind(self):
        recursive = []
        recursive.append(recursive)
        cases = ((object(), "TypeError"), (float("nan"), "NonFiniteNumber"),
                 (recursive, "RecursionError"))
        for value, error_kind in cases:
            with self.subTest(error_kind=error_kind):
                context = _FakeMetadataContext()
                parsed = mock.Mock(where="records.jsonl:1")
                oracle_validate._record_availability_errors(
                    parsed,
                    {"availability": {"runtimes": [{"runtime": "demo", "value": value}]}},
                    context,
                )
                self.assertEqual(context.errors, [
                    f"records.jsonl:1 has malformed runtime availability: {error_kind}"
                ])
                self.assertEqual(context.probe_values, {})

    def test_a_malformed_manifest_probe_is_reported(self):
        context = _FakeMetadataContext()
        oracle_validate._availability_probe_errors(
            ["not-a-probe", {"runtime": None}], context
        )
        self.assertEqual(
            context.errors,
            ["availability declares a malformed runtime probe"] * 2,
        )


class MainExitCodeTest(unittest.TestCase):
    """main() maps validation outcomes onto CLI exit codes."""

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = oracle_validate.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_missing_run_dir_is_usage_error(self):
        code, _out, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("a run directory is required", err)

    def test_non_directory_is_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent"
            code, _out, err = self.run_main(str(missing))
        self.assertEqual(code, 2)
        self.assertIn("not a directory", err)

    def test_unknown_family_is_usage_error(self):
        code, _out, err = self.run_main(str(GOLDEN), "--family", "no-such-family")
        self.assertEqual(code, 2)
        self.assertIn("unknown families: no-such-family", err)

    def test_golden_run_exits_zero_and_prints_report(self):
        code, out, _err = self.run_main(str(GOLDEN))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["records"], 20)

    def test_findings_exit_one_and_are_printed(self):
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, ["first", "second"])
        ):
            code, _out, err = self.run_main(str(GOLDEN))
        self.assertEqual(code, 1)
        self.assertIn("first", err)
        self.assertIn("second", err)

    def test_findings_beyond_the_limit_are_summarised(self):
        findings = [f"finding-{index}" for index in range(5)]
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, findings)
        ):
            code, _out, err = self.run_main(str(GOLDEN), "--max-findings", "2")
        self.assertEqual(code, 1)
        self.assertIn("finding-1", err)
        self.assertNotIn("finding-4", err)
        self.assertIn("... 3 more findings", err)

    def test_negative_finding_limit_hides_every_finding(self):
        with mock.patch.object(
            oracle_validate, "validate_run", return_value=({"records": 0}, ["only"])
        ):
            code, _out, err = self.run_main(str(GOLDEN), "--max-findings", "-5")
        self.assertEqual(code, 1)
        self.assertNotIn("only", err)
        self.assertIn("... 1 more findings", err)


if __name__ == "__main__":
    unittest.main()
