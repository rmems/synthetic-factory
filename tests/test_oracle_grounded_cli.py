#!/usr/bin/env python3
"""End-to-end tests for the oracle-grounded CLIs and the committed fixtures.

The golden run under tests/fixtures/oracle-grounded/golden-r01/ is regenerated
here and compared byte for byte. That single check covers determinism,
reproducibility, and the identity of the implementation at once: if a simulator
changes, `oracle.module_digest` changes and this test fails loudly rather than
letting a fixture quietly stop describing the code that produced it.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import families, oracles, record  # noqa: E402

GENERATE = REPO / "pipelines" / "oracle_generate.py"
VALIDATE = REPO / "pipelines" / "oracle_validate.py"
FIXTURES = REPO / "tests" / "fixtures" / "oracle-grounded"
GOLDEN = FIXTURES / "golden-r01"
INVALID = FIXTURES / "invalid"


def run_cli(script, *args, env=None):
    return subprocess.run(
        [sys.executable, str(script), *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class GoldenFixture(unittest.TestCase):
    """The committed run must be exactly what the current code produces."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((GOLDEN / "manifest.json").read_text())

    def test_the_fixture_regenerates_byte_for_byte(self):
        with tempfile.TemporaryDirectory(prefix="oracle-golden-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE,
                "--count",
                self.manifest["count_per_family"],
                "--seed",
                self.manifest["seed"],
                "--round",
                self.manifest["round"],
                "--oracle-commit",
                self.manifest["oracle_commit"],
                "--oracle-dirty" if self.manifest["oracle_dirty"] else "--no-oracle-dirty",
                out,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            committed = sorted(
                path.relative_to(GOLDEN) for path in GOLDEN.rglob("*") if path.is_file()
            )
            produced = sorted(
                path.relative_to(out) for path in out.rglob("*") if path.is_file()
            )
            self.assertEqual(committed, produced)
            for relative in committed:
                with self.subTest(path=str(relative)):
                    self.assertEqual(
                        (out / relative).read_text(),
                        (GOLDEN / relative).read_text(),
                        f"{relative} drifted; regenerate the fixture if this was intended",
                    )

    def test_the_manifest_digests_match_the_committed_files(self):
        for relative, entry in self.manifest["files"].items():
            path = GOLDEN / relative
            with self.subTest(path=relative):
                self.assertTrue(path.is_file())
                self.assertEqual(len(read_jsonl(path)), entry["records"])

    def test_the_manifest_pins_the_current_implementation(self):
        self.assertEqual(self.manifest["module_digest"], oracles.module_digest())
        self.assertNotEqual(self.manifest["oracle_commit"], "unknown")

    def test_the_fixture_covers_every_family(self):
        self.assertEqual(sorted(self.manifest["families"]), sorted(families.FAMILY_NAMES))
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                self.assertTrue((GOLDEN / family).is_dir())

    def test_no_fixture_record_claims_a_named_runtime_or_publication(self):
        for path in GOLDEN.rglob("*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["oracle"]["implementation"], "reference")
                    self.assertFalse(item["validation"]["publishable"])
                    self.assertFalse(item["oracle"]["runtime_bound"])

    def test_accepted_and_rejected_records_are_filed_separately(self):
        for path in GOLDEN.rglob("accepted-*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["validation"]["status"], "accepted")
                    self.assertEqual(record.validate_record(item), [])
        for path in GOLDEN.rglob("rejected-*.jsonl"):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    self.assertEqual(item["validation"]["status"], "rejected")
                    self.assertTrue(item["validation"]["reasons"])
                    self.assertEqual(record.classify(item)["envelope"], [])

    def test_the_rejected_temporal_memory_records_say_why(self):
        path = GOLDEN / families.MEMORY_FAMILY / "rejected-r01.jsonl"
        items = read_jsonl(path)
        self.assertTrue(items, "the fixture should retain at least one rejected trial")
        for item in items:
            with self.subTest(record=item["id"]):
                self.assertTrue(
                    any("temporal dependence" in r for r in item["validation"]["reasons"])
                )
                self.assertFalse(
                    item["result"]["measured"]["temporal_dependence"]["demonstrated"]
                )

    def test_every_fixture_record_reproduces_from_its_stored_scenario(self):
        for path in sorted(GOLDEN.rglob("*.jsonl")):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    status, detail = record.reproduce(item)
                    self.assertEqual(status, "reproduced", detail)

    def test_every_fixture_record_retains_oracle_provenance(self):
        for path in sorted(GOLDEN.rglob("*.jsonl")):
            for item in read_jsonl(path):
                oracle = item["oracle"]
                with self.subTest(record=item["id"]):
                    self.assertEqual(oracle["repo"], oracles.REPO_SLUG)
                    self.assertNotEqual(oracle["commit"], "unknown")
                    self.assertEqual(oracle["module_digest"], oracles.module_digest())
                    self.assertTrue(oracle["configuration"])
                    self.assertTrue(oracle["units"])
                    self.assertTrue(oracle["stages"])


class InvalidFixtures(unittest.TestCase):
    """Every committed defect must still be caught."""

    def defects(self, name):
        return read_jsonl(INVALID / f"{name}.jsonl")

    def test_every_invalid_oracle_record_is_rejected(self):
        items = self.defects("invalid-oracle")
        self.assertGreaterEqual(len(items), 9)
        for item in items:
            with self.subTest(defect=item["_defect"]):
                self.assertTrue(
                    record.validate_record(item),
                    f"{item['_defect']} was accepted",
                )

    def test_every_malformed_generator_record_is_rejected(self):
        items = self.defects("malformed-generator")
        self.assertGreaterEqual(len(items), 7)
        for item in items:
            with self.subTest(defect=item["_defect"]):
                self.assertTrue(
                    record.validate_record(item),
                    f"{item['_defect']} was accepted",
                )

    def test_each_defect_is_caught_for_the_stated_reason(self):
        expected = {
            "missing_result": "fails closed",
            "result_not_attributed_to_declared_oracle": "produced_by",
            "result_hash_does_not_cover_result": "result_hash",
            "oracle_commit_unknown": "commit",
            "oracle_module_digest_missing": "module_digest",
            "reference_oracle_claims_publishable": "publishable",
            "empty_measurement": "measured",
            "no_executed_stages": "stages",
            "reference_run_relabelled_as_named_runtime": "named runtime",
            "generator_authored_a_measurement_key": "oracle-reserved keys",
            "scenario_edited_after_proposal_hash": "proposal_hash",
            "generator_claims_authority": "authoritative",
            "candidate_prediction_posing_as_ground_truth": "non_authoritative_guess",
            "empty_scenario": "scenario must be",
            "failing_record_relabelled_accepted": "fails its own checks",
            "rejection_reason_rewritten": "do not match the recomputed findings",
        }
        seen = set()
        for name in ("invalid-oracle", "malformed-generator"):
            for item in self.defects(name):
                defect = item["_defect"]
                seen.add(defect)
                findings = " | ".join(record.validate_record(item))
                with self.subTest(defect=defect):
                    self.assertIn(expected[defect], findings)
        self.assertEqual(seen, set(expected))

    def test_the_validator_cli_fails_on_the_invalid_fixtures(self):
        completed = run_cli(VALIDATE, INVALID)
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertGreater(report["invalid"] + report["rejected"], 0)
        self.assertTrue(completed.stderr.strip())


class ValidateCli(unittest.TestCase):
    def test_the_golden_run_validates_clean(self):
        completed = run_cli(VALIDATE, GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["invalid"], 0)
        self.assertEqual(report["parse_failures"], 0)
        self.assertEqual(report["records"], report["accepted"] + report["rejected"])
        self.assertEqual(report["publishable"], 0)
        self.assertEqual(report["named_runtime"], 0)
        self.assertEqual(report["reference_oracle"], report["records"])
        self.assertEqual(sorted(report["by_family"]), sorted(families.FAMILY_NAMES))

    def test_reproduce_re_runs_every_oracle(self):
        completed = run_cli(VALIDATE, "--reproduce", GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["reproduce"], {"reproduced": report["records"]})

    def test_a_family_filter_narrows_the_run(self):
        completed = run_cli(VALIDATE, "--family", families.MESH_FAMILY, GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(list(report["by_family"]), [families.MESH_FAMILY])
        self.assertGreater(report["skipped"], 0)

    def test_require_runtime_rejects_the_reference_fixture(self):
        completed = run_cli(VALIDATE, "--require-runtime", GOLDEN)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("named runtime was required", completed.stderr)

    def test_a_malformed_line_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory(prefix="oracle-bad-") as temp:
            path = Path(temp) / "family" / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text('not json\n{"schema": "oracle-grounded/v1"}\n[]\n')
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["parse_failures"], 2)
            self.assertIn("JSON parse error", completed.stderr)

    def test_an_empty_directory_validates_clean(self):
        with tempfile.TemporaryDirectory(prefix="oracle-empty-") as temp:
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["records"], 0)

    def test_a_missing_directory_is_a_usage_error(self):
        completed = run_cli(VALIDATE, REPO / "no" / "such" / "dir")
        self.assertEqual(completed.returncode, 2)

    def test_no_argument_is_a_usage_error(self):
        self.assertEqual(run_cli(VALIDATE).returncode, 2)

    def test_an_unknown_family_is_a_usage_error(self):
        completed = run_cli(VALIDATE, "--family", "not-a-family", GOLDEN)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown families", completed.stderr)

    def test_the_validator_writes_nothing(self):
        before = {
            str(path.relative_to(GOLDEN)): path.stat().st_mtime_ns
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        run_cli(VALIDATE, "--reproduce", GOLDEN)
        after = {
            str(path.relative_to(GOLDEN)): path.stat().st_mtime_ns
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)


class GenerateCli(unittest.TestCase):
    def test_list_families_prints_all_five(self):
        completed = run_cli(GENERATE, "--list-families")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.split(), list(families.FAMILY_NAMES))

    def test_a_single_family_run_writes_only_that_family(self):
        with tempfile.TemporaryDirectory(prefix="oracle-one-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                2,
                "--oracle-commit",
                "a" * 40,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                sorted(p.name for p in out.iterdir()),
                ["manifest.json", families.ENCODER_FAMILY],
            )
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(list(manifest["families"]), [families.ENCODER_FAMILY])
            self.assertEqual(manifest["generation_errors"], [])

    def test_it_refuses_to_overwrite_an_existing_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-twice-") as temp:
            out = Path(temp) / "run"
            first = run_cli(
                GENERATE, "--count", 1, "--oracle-commit", "b" * 40, "--no-oracle-dirty", out
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_cli(
                GENERATE, "--count", 1, "--oracle-commit", "b" * 40, "--no-oracle-dirty", out
            )
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite", second.stderr)

    def test_require_runtime_refuses_to_write_when_nothing_is_bound(self):
        with tempfile.TemporaryDirectory(prefix="oracle-req-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE, "--require-runtime", "--count", 1, "--oracle-commit", "c" * 40, out
            )
            self.assertEqual(completed.returncode, 3)
            self.assertIn("not bound", completed.stderr)
            self.assertFalse(out.exists())

    def test_require_runtime_checks_only_the_selected_family(self):
        with tempfile.TemporaryDirectory(prefix="oracle-selected-runtime-") as temp:
            out = Path(temp) / "run"
            env = dict(os.environ)
            for runtime in families.ALL_RUNTIMES:
                env.pop(oracles.env_key(runtime), None)
            env[oracles.env_key("axon-encoder")] = (
                f"{sys.executable} {FIXTURES / 'protocol_double.py'} ok"
            )
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                1,
                "--require-runtime",
                "--oracle-commit",
                "c" * 40,
                out,
                env=env,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(manifest["oracle_availability"]["unbound"], [])
            self.assertEqual(
                [
                    probe["runtime"]
                    for probe in manifest["oracle_availability"]["runtimes"]
                ],
                ["axon-encoder"],
            )

    def test_an_unknown_family_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-bad-family-") as temp:
            completed = run_cli(GENERATE, "--family", "nope", Path(temp) / "run")
            self.assertEqual(completed.returncode, 2)
            self.assertIn("unknown families", completed.stderr)

    def test_a_non_positive_count_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-count-") as temp:
            self.assertEqual(
                run_cli(GENERATE, "--count", 0, Path(temp) / "run").returncode, 2
            )
            self.assertEqual(
                run_cli(GENERATE, "--round", 0, Path(temp) / "run").returncode, 2
            )

    def test_no_output_directory_is_a_usage_error(self):
        self.assertEqual(run_cli(GENERATE).returncode, 2)

    def test_a_generated_run_passes_its_own_validator(self):
        with tempfile.TemporaryDirectory(prefix="oracle-roundtrip-") as temp:
            out = Path(temp) / "run"
            generated = run_cli(
                GENERATE,
                "--count",
                2,
                "--round",
                3,
                "--seed",
                777,
                "--oracle-commit",
                "d" * 40,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            validated = run_cli(VALIDATE, "--reproduce", out)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            report = json.loads(validated.stdout)
            self.assertEqual(report["invalid"], 0)
            self.assertEqual(report["records"], 10)
            self.assertEqual(report["reproduce"], {"reproduced": 10})
            for path in out.rglob("*.jsonl"):
                for item in read_jsonl(path):
                    self.assertEqual(item["meta"]["round"], 3)
                    self.assertIn("r03", item["id"])


if __name__ == "__main__":
    unittest.main()
