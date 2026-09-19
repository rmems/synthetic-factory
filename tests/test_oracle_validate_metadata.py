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
import json
import os
import shutil
import sys
import tempfile
import unittest
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
            snapshot, oracle_validate.ValidationContext(), seen_ids=seen_ids
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

    def test_malformed_commit_is_rejected(self):
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

    def test_availability_requires_object(self):
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

    def test_runtime_name_requires_string(self):
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

    def test_note_granting_diagnostic_fixture_publishability_is_rejected(self):
        # Historical fixture replay has unresolved checkout provenance.
        # A note must not grant publication authority its records lack.
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
        report, errors = oracle_validate.validate_run(oracle_validate.ValidationContext(GOLDEN))
        self.assertEqual(errors, [])
        self.assertTrue(report["manifest_valid"])

    def test_golden_run_totals(self):
        report, _errors = oracle_validate.validate_run(oracle_validate.ValidationContext(GOLDEN))
        self.assertEqual(report["files"], 10)
        self.assertEqual(report["records"], 20)
        self.assertEqual(report["accepted"] + report["rejected"], 20)
        self.assertEqual(report["parse_failures"], 0)

    def test_family_counts_cover_manifest(self):
        report, _errors = oracle_validate.validate_run(oracle_validate.ValidationContext(GOLDEN))
        self.assertEqual(sum(report["by_family"].values()), report["records"])
        self.assertEqual(len(report["by_family"]), 5)

    def test_reproduce_adds_a_reproduce_block(self):
        report, _errors = oracle_validate.validate_run(
            oracle_validate.ValidationContext(GOLDEN, reproduce=True)
        )
        self.assertIn("reproduce", report)

    def test_report_omits_reproduce_block_by_default(self):
        report, _errors = oracle_validate.validate_run(oracle_validate.ValidationContext(GOLDEN))
        self.assertNotIn("reproduce", report)

    def test_family_filter_restricts_counted_records(self):
        report, _errors = oracle_validate.validate_run(
            oracle_validate.ValidationContext(
                GOLDEN, selected={"neuron-dynamics-counterfactuals"}
            )
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
            report, errors = oracle_validate.validate_run(oracle_validate.ValidationContext(GOLDEN))
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

    def test_run_symlink_is_refused(self):
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

    def test_missing_declared_file_is_reported(self):
        run = self.scratch_run()
        victim = next(run.rglob("accepted-*.jsonl"))
        victim.unlink()
        self.assert_authentication_reports(run, "manifest file is missing")

    def test_tampered_payload_fails_digest(self):
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


if __name__ == "__main__":
    unittest.main()
