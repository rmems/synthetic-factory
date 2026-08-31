#!/usr/bin/env python3
"""In-process tests for oracle_validate's run-level decision logic.

The end-to-end suite drives ``oracle_validate.py`` as a subprocess, which
proves the CLI contract but leaves the run-level reasoning
(``_manifest_metadata_errors``, ``validate_run``, ``main``) unmeasured. These
tests call the same code in process against the committed golden run, so every
manifest-binding rule is exercised against real snapshots and real parsed
records rather than a hand-built stub.

Each metadata test mutates one field of a deep copy of the golden manifest and
asserts the specific finding that mutation must produce. The golden run itself
must validate with no findings at all, which pins the accept path.
"""

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import oracle_validate  # noqa: E402

GOLDEN = REPO / "tests" / "fixtures" / "oracle-grounded" / "golden-r01"


def _load_golden():
    """Authenticate and parse the golden run once for the whole module."""
    manifest, snapshots, errors = oracle_validate.authenticate_manifest(GOLDEN)
    if errors:
        raise AssertionError(f"golden run failed authentication: {errors}")
    records = []
    seen_ids = {}
    for snapshot in snapshots:
        _totals, _errors, parsed = oracle_validate.validate_file(
            snapshot, False, False, set(), seen_ids=seen_ids
        )
        records.extend(parsed)
    return manifest, snapshots, records


class GoldenRunFixture(unittest.TestCase):
    """Shared golden-run inputs for the run-level checks."""

    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.snapshots, cls.records = _load_golden()

    def metadata_errors(self, mutate=None):
        manifest = copy.deepcopy(self.manifest)
        if mutate is not None:
            mutate(manifest)
        return oracle_validate._manifest_metadata_errors(
            manifest, self.snapshots, self.records, GOLDEN
        )

    def assert_reports(self, mutate, fragment):
        errors = self.metadata_errors(mutate)
        matched = [error for error in errors if fragment in error]
        self.assertTrue(matched, f"expected a finding containing {fragment!r}, got {errors}")


class ManifestMetadataAcceptTest(GoldenRunFixture):
    """The committed golden run must bind cleanly to its manifest."""

    def test_golden_manifest_metadata_has_no_findings(self):
        self.assertEqual(self.metadata_errors(), [])

    def test_golden_run_parses_every_declared_file(self):
        self.assertEqual(len(self.snapshots), 10)
        self.assertEqual(len(self.records), 20)


class ManifestHeaderFieldTest(GoldenRunFixture):
    """Scalar manifest header fields are range- and type-checked."""

    def test_round_below_range_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("round", 0), "round must be an integer")

    def test_round_above_range_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("round", oracle_validate.MAX_ROUND + 1),
            "round must be an integer",
        )

    def test_non_integer_seed_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("seed", "seed"), "seed must be an integer")

    def test_boolean_seed_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("seed", True), "seed must be an integer")

    def test_zero_count_per_family_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("count_per_family", 0),
            "count_per_family must be an integer",
        )

    def test_unresolvable_oracle_commit_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_commit", "0" * 40),
            "oracle_commit does not resolve",
        )

    def test_malformed_oracle_commit_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_commit", "not-a-commit"),
            "oracle_commit must be a resolved lowercase",
        )

    def test_non_boolean_oracle_dirty_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_dirty", "yes"),
            "oracle_dirty must be boolean or null",
        )

    def test_non_digest_module_digest_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("module_digest", "nope"),
            "module_digest must be a sha256 digest",
        )


class ManifestFamiliesTest(GoldenRunFixture):
    """The declared families block must match the captured directories."""

    def test_non_object_families_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("families", []), "families must be an object")

    def test_empty_families_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("families", {}),
            "families must declare at least one family",
        )

    def test_family_key_mismatch_is_rejected(self):
        def mutate(manifest):
            manifest["families"]["not-a-real-family"] = {}

        self.assert_reports(mutate, "families keys do not match captured family directories")

    def test_altered_family_summary_is_rejected(self):
        def mutate(manifest):
            family = sorted(manifest["families"])[0]
            manifest["families"][family]["proposed"] = 999

        self.assert_reports(mutate, "do not match the captured records")

    def test_round_mismatch_against_captured_files_is_rejected(self):
        self.assert_reports(lambda m: m.__setitem__("round", 2), "does not match manifest round")


class ManifestAvailabilityTest(GoldenRunFixture):
    """oracle_availability must agree with the probes captured in records."""

    def test_non_object_availability_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__("oracle_availability", "none"),
            "oracle_availability must be an object",
        )

    def test_wrong_protocol_is_rejected(self):
        self.assert_reports(
            lambda m: m["oracle_availability"].__setitem__("protocol", "bogus"),
            "oracle_availability is malformed",
        )

    def test_runtime_set_mismatch_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["runtimes"] = []

        self.assert_reports(mutate, "oracle_availability runtimes do not match families")

    def test_non_string_runtime_name_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["runtimes"][0]["runtime"] = 7

        self.assert_reports(mutate, "runtime names must be strings")

    def test_all_bound_disagreement_is_rejected(self):
        def mutate(manifest):
            availability = manifest["oracle_availability"]
            availability["all_bound"] = not availability.get("all_bound")

        self.assert_reports(mutate, "oracle_availability.all_bound disagrees")

    def test_unbound_disagreement_is_rejected(self):
        def mutate(manifest):
            manifest["oracle_availability"]["unbound"] = ["invented-runtime"]

        self.assert_reports(mutate, "oracle_availability.unbound disagrees")


class ManifestNoteTest(GoldenRunFixture):
    """The note is derived from record publishability, never free text."""

    def test_note_claiming_publishability_is_rejected(self):
        # The golden run is reference-only: swapping in the other legitimate
        # note is a publication claim the captured records do not carry.
        self.assert_reports(
            lambda m: m.__setitem__("note", oracle_validate.MANIFEST_NOTE_PUBLISHABLE),
            "note does not match the publishability of the captured records",
        )

    def test_free_text_note_is_rejected(self):
        self.assert_reports(
            lambda m: m.__setitem__(
                "note", "Records externally attested; publishable as-is."
            ),
            "note does not match the publishability of the captured records",
        )

    def test_missing_note_is_rejected(self):
        def mutate(manifest):
            del manifest["note"]

        self.assert_reports(
            mutate, "note does not match the publishability of the captured records"
        )


class RunTreeWalkTest(unittest.TestCase):
    """Directory enumeration must stay bounded against untrusted trees."""

    def test_run_entry_cap_bounds_directory_materialization(self):
        # The cap must be enforced while draining scandir: sorting first would
        # materialize an arbitrarily large untrusted directory in memory.
        class FakeEntry:
            __slots__ = ("name",)

            def __init__(self, name):
                self.name = name

        class CountingScandir:
            def __init__(self):
                self.consumed = 0

            def __enter__(self):
                return self._entries()

            def __exit__(self, *exc):
                return False

            def _entries(self):
                for index in range(100_000):
                    self.consumed += 1
                    yield FakeEntry(f"entry-{index:06d}")

        counting = CountingScandir()
        walk = oracle_validate._RunTreeWalk(root=Path("/nonexistent-run"))
        from pathlib import PurePosixPath

        with mock.patch.object(oracle_validate.os, "scandir", return_value=counting):
            halted = oracle_validate._scan_directory(PurePosixPath(), -1, walk)
        self.assertTrue(halted)
        self.assertTrue(
            any("more than" in error for error in walk.errors), walk.errors
        )
        self.assertLessEqual(counting.consumed, oracle_validate.MAX_RUN_ENTRIES + 1)


class ValidateRunTest(unittest.TestCase):
    """validate_run aggregates per-file totals into the run report."""

    def test_golden_run_reports_no_errors(self):
        report, errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(errors, [])
        self.assertTrue(report["manifest_valid"])

    def test_golden_run_totals(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(report["files"], 10)
        self.assertEqual(report["records"], 20)
        self.assertEqual(report["accepted"] + report["rejected"], 20)
        self.assertEqual(report["parse_failures"], 0)

    def test_by_family_counts_cover_every_family(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertEqual(sum(report["by_family"].values()), report["records"])
        self.assertEqual(len(report["by_family"]), 5)

    def test_reproduce_adds_a_reproduce_block(self):
        report, _errors = oracle_validate.validate_run(GOLDEN, reproduce=True)
        self.assertIn("reproduce", report)

    def test_report_omits_reproduce_block_by_default(self):
        report, _errors = oracle_validate.validate_run(GOLDEN)
        self.assertNotIn("reproduce", report)

    def test_family_filter_restricts_counted_records(self):
        report, _errors = oracle_validate.validate_run(
            GOLDEN, selected={"neuron-dynamics-counterfactuals"}
        )
        self.assertEqual(list(report["by_family"]), ["neuron-dynamics-counterfactuals"])
        self.assertGreater(report["skipped"], 0)

    def test_metadata_exception_is_contained_as_a_finding(self):
        boom = mock.patch.object(
            oracle_validate,
            "_manifest_metadata_errors",
            side_effect=RuntimeError("boom"),
        )
        with boom:
            report, errors = oracle_validate.validate_run(GOLDEN)
        self.assertFalse(report["manifest_valid"])
        self.assertTrue(any("raised an internal exception: RuntimeError" in e for e in errors))


class RunTreeGuardTest(unittest.TestCase):
    """The run-tree walk and manifest authentication refuse hostile trees.

    The subprocess suite already proves the CLI contract for several of
    these; this class exercises the same guards in process so the walk's
    refusal branches are measured, each against a scratch copy of the
    golden run with exactly one thing wrong.
    """

    def scratch_run(self):
        temp = tempfile.TemporaryDirectory(prefix="oracle-guard-")
        self.addCleanup(temp.cleanup)
        run = Path(temp.name) / "run"
        shutil.copytree(GOLDEN, run)
        return run

    def assert_authentication_reports(self, run, fragment):
        _manifest, _snapshots, errors = oracle_validate.authenticate_manifest(run)
        matched = [error for error in errors if fragment in error]
        self.assertTrue(matched, f"expected a finding containing {fragment!r}, got {errors}")

    def test_a_symlink_inside_the_run_is_refused(self):
        run = self.scratch_run()
        (run / "alias.jsonl").symlink_to(run / "manifest.json")
        self.assert_authentication_reports(run, "symbolic links are not allowed")

    def test_a_hard_linked_payload_is_refused(self):
        run = self.scratch_run()
        source = next(run.rglob("accepted-*.jsonl"))
        os.link(source, source.with_name("twin.jsonl"))
        self.assert_authentication_reports(run, "hard-linked files are not allowed")

    def test_a_special_file_inside_the_run_is_refused(self):
        run = self.scratch_run()
        os.mkfifo(run / "pipe.jsonl")
        self.assert_authentication_reports(run, "only regular files and directories are allowed")

    def test_nesting_beyond_the_depth_limit_is_refused(self):
        run = self.scratch_run()
        (run / "a" / "b" / "c").mkdir(parents=True)
        with mock.patch.object(oracle_validate, "MAX_RUN_DEPTH", 2):
            self.assert_authentication_reports(run, "run nesting exceeds 2 directories")

    def test_an_entry_flood_halts_the_walk(self):
        run = self.scratch_run()
        with mock.patch.object(oracle_validate, "MAX_RUN_ENTRIES", 3):
            self.assert_authentication_reports(run, "more than 3 entries")

    def test_a_file_flood_halts_the_walk(self):
        run = self.scratch_run()
        with mock.patch.object(oracle_validate, "MAX_RUN_FILES", 2):
            self.assert_authentication_reports(run, "run contains more than 2 files")

    def test_an_oversized_run_halts_the_walk(self):
        run = self.scratch_run()
        with mock.patch.object(oracle_validate, "MAX_RUN_BYTES", 10):
            self.assert_authentication_reports(run, "run exceeds the 10-byte snapshot limit")

    def test_a_missing_manifest_is_reported(self):
        run = self.scratch_run()
        (run / "manifest.json").unlink()
        self.assert_authentication_reports(run, "required run manifest is missing")

    def test_a_corrupt_manifest_is_reported(self):
        run = self.scratch_run()
        (run / "manifest.json").write_text("not json\n", encoding="utf-8")
        self.assert_authentication_reports(run, "invalid manifest snapshot")

    def test_a_symlinked_run_root_is_refused(self):
        run = self.scratch_run()
        link = run.parent / "run-link"
        link.symlink_to(run, target_is_directory=True)
        self.assert_authentication_reports(link, "could not pin run directory")

    def test_an_unmanifested_file_is_reported(self):
        run = self.scratch_run()
        (run / "stray.jsonl").write_text("", encoding="utf-8")
        self.assert_authentication_reports(run, "unmanifested file is present: stray.jsonl")

    def test_a_missing_declared_file_is_reported(self):
        run = self.scratch_run()
        victim = next(run.rglob("accepted-*.jsonl"))
        victim.unlink()
        self.assert_authentication_reports(run, "manifest file is missing")

    def test_a_tampered_payload_fails_its_digest(self):
        run = self.scratch_run()
        victim = next(run.rglob("accepted-*.jsonl"))
        with victim.open("a", encoding="utf-8") as handle:
            handle.write("{}\n")
        self.assert_authentication_reports(run, "sha256 mismatch")

    def test_a_file_entry_sibling_is_rejected(self):
        run = self.scratch_run()
        manifest = json.loads((run / "manifest.json").read_text())
        first = sorted(manifest["files"])[0]
        manifest["files"][first]["external_attestation"] = "verified-on-hardware"
        (run / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_authentication_reports(
            run, "carries unauthenticated sibling keys: external_attestation"
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
        import copy as _copy

        from oracle_grounded import canon, oracles

        parsed = _copy.deepcopy(self.records[0].item)
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
                snapshot, False, False, set(), expected_commit=expected
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
            False,
            False,
            set(),
            expected_commit=self.manifest["oracle_commit"],
        )
        self.assertEqual(errors, [])
        self.assertEqual(totals["invalid"], 0)
        self.assertGreater(totals["records"], 0)

    def test_an_invalid_manifest_commit_still_binds_records(self):
        # Breaking the manifest's own commit must not regain per-record
        # repository lookups: the manifest value stays the comparison
        # sentinel, so mismatching records are rejected without git.
        import shutil as _shutil

        from oracle_grounded import oracles

        with tempfile.TemporaryDirectory(prefix="oracle-bind-") as temp:
            run = Path(temp) / "run"
            _shutil.copytree(GOLDEN, run)
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
                report, errors = oracle_validate.validate_run(run)
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
