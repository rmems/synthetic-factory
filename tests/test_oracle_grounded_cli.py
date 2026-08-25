#!/usr/bin/env python3
"""End-to-end tests for the oracle-grounded CLIs and the committed fixtures.

The golden run under tests/fixtures/oracle-grounded/golden-r01/ is regenerated
here and compared byte for byte. That single check covers determinism,
reproducibility, and the identity of the implementation at once: if a simulator
changes, `oracle.module_digest` changes and this test fails loudly rather than
letting a fixture quietly stop describing the code that produced it.
"""

import copy
import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import canon, families, oracles, record  # noqa: E402
import oracle_generate  # noqa: E402
import oracle_validate  # noqa: E402

GENERATE = REPO / "pipelines" / "oracle_generate.py"
VALIDATE = REPO / "pipelines" / "oracle_validate.py"
FIXTURES = REPO / "tests" / "fixtures" / "oracle-grounded"
GOLDEN = FIXTURES / "golden-r01"
INVALID = FIXTURES / "invalid"
PINNED_COMMIT = oracles.resolve_commit(REPO)[0]


def clean_env(**updates):
    env = dict(os.environ)
    for runtime in families.ALL_RUNTIMES:
        env.pop(oracles.env_key(runtime), None)
    env.update(updates)
    return env


def run_cli(script, *args, env=None):
    if env is None:
        env = clean_env()
    return subprocess.run(
        [sys.executable, str(script), *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_test_manifest(run_dir):
    run_dir = Path(run_dir)
    manifest_path = run_dir / "manifest.json"
    # Scratch runs must have the same two-file family layout as production,
    # including an empty accepted or rejected side when every proposal lands
    # in the other verdict.
    for path in sorted(run_dir.rglob("*.jsonl")):
        match = re.fullmatch(r"(accepted|rejected)-r([0-9]+)\.jsonl", path.name)
        if match is None:
            continue
        other = "rejected" if match.group(1) == "accepted" else "accepted"
        counterpart = path.with_name(f"{other}-r{match.group(2)}.jsonl")
        if not counterpart.exists():
            counterpart.write_text("", encoding="utf-8")
    files = {}
    parsed = []
    for path in sorted(run_dir.rglob("*.jsonl")):
        body = path.read_bytes()
        files[path.relative_to(run_dir).as_posix()] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "records": sum(1 for line in body.decode().splitlines() if line.strip()),
        }
        for line in body.decode().splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and isinstance(item.get("family"), str):
                parsed.append((path, item))
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        manifest["files"] = files
    else:
        round_number = next(
            (
                item.get("meta", {}).get("round")
                for _path, item in parsed
                if isinstance(item.get("meta"), dict)
            ),
            1,
        )
        family_names = sorted({item["family"] for _path, item in parsed})
        counts = Counter(item["family"] for _path, item in parsed)
        count_per_family = max(counts.values(), default=1)
        family_summaries = {}
        for family in family_names:
            accepted = [
                item
                for path, item in parsed
                if item["family"] == family and path.name.startswith("accepted-")
            ]
            rejected = [
                item
                for path, item in parsed
                if item["family"] == family and path.name.startswith("rejected-")
            ]
            first = (accepted or rejected)[0]
            family_summaries[family] = {
                "proposed": count_per_family,
                "accepted": oracle_generate.summarize(accepted),
                "rejected": {
                    "records": len(rejected),
                    "reasons": sorted(
                        {
                            reason
                            for item in rejected
                            for reason in item.get("validation", {}).get("reasons", [])
                            if isinstance(reason, str)
                        }
                    ),
                },
                "oracle": {
                    "requested_runtime": list(families.spec_for(family).runtimes),
                    "implementation": first["oracle"]["implementation"],
                },
            }
        first = parsed[0][1] if parsed else {}
        first_oracle = first.get("oracle", {}) if isinstance(first, dict) else {}
        runtime_order = [
            runtime
            for family in families.FAMILY_NAMES
            if family in family_names
            for runtime in families.spec_for(family).runtimes
        ]
        probes = {}
        for _path, item in parsed:
            availability = item.get("oracle", {}).get("availability", {})
            for probe in availability.get("runtimes", []):
                if isinstance(probe, dict) and isinstance(probe.get("runtime"), str):
                    probes.setdefault(probe["runtime"], probe)
        availability_probes = [probes[runtime] for runtime in runtime_order if runtime in probes]
        unbound = [probe["runtime"] for probe in availability_probes if not probe["bound"]]
        manifest = {
            "schema": record.SCHEMA_ID,
            "round": round_number,
            "seed": 20260823,
            "count_per_family": count_per_family,
            "families": family_summaries,
            "oracle_commit": first_oracle.get("commit", "0" * 40),
            "oracle_dirty": first_oracle.get("dirty", False),
            "module_digest": first_oracle.get("module_digest", oracles.module_digest()),
            "oracle_availability": {
                "protocol": oracles.PROTOCOL,
                "runtimes": availability_probes,
                "all_bound": not unbound,
                "unbound": unbound,
            },
            "files": files,
            "generation_errors": [],
            "note": "Synthetic test manifest; internally consistent but unsigned.",
        }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def build(family, index=0):
    return record.build_record(
        family,
        index,
        seed=20260823,
        commit=PINNED_COMMIT,
        dirty=False,
        environ={},
    )


def relabel_as_named_runtime(item):
    item = copy.deepcopy(item)
    oracle = item["oracle"]
    oracle["implementation"] = "named-runtime"
    oracle["authority"] = "measured-runtime"
    item["provenance"]["claimed"] = "measured-runtime"
    item["meta"]["tags"][-1] = "named-runtime"
    oracle["runtime_bound"] = True
    oracle["availability"]["all_bound"] = True
    oracle["availability"]["unbound"] = []
    for probe in oracle["availability"]["runtimes"]:
        probe["bound"] = True
    stage_ids = []
    for stage, runtime in zip(oracle["stages"], oracle["requested_runtime"], strict=True):
        stage["implementation"] = "named-runtime"
        stage["oracle_id"] = runtime
        stage["version"] = "0.0.0-double"
        stage["runtime_commit"] = "a" * 40
        stage["executable"] = runtime
        stage.pop("module_digest", None)
        stage_ids.append(runtime)
    oracle["id"] = "+".join(stage_ids)
    item["result"]["produced_by"] = oracle["id"]
    item["result_hash"] = canon.digest(item["result"])
    item["validation"] = record.assess(item)
    return item


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
            produced = sorted(path.relative_to(out) for path in out.rglob("*") if path.is_file())
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
                self.assertFalse(item["result"]["measured"]["temporal_dependence"]["demonstrated"])

    def test_every_fixture_record_reproduces_from_its_stored_scenario(self):
        for path in sorted(GOLDEN.rglob("*.jsonl")):
            for item in read_jsonl(path):
                with self.subTest(record=item["id"]):
                    status, detail = record.reproduce(item, environ={})
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
            "missing_result": "$.result",
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
            "empty_scenario": "$.scenario",
            "failing_record_relabelled_accepted": "recomputed status",
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
        self.assertEqual(report["records"], 0)
        self.assertFalse(report["manifest_valid"])
        self.assertIn("required run manifest is missing", completed.stderr)


class ValidateCli(unittest.TestCase):
    def generate_run(self, parent, count=1):
        out = Path(parent) / "run"
        completed = run_cli(
            GENERATE,
            "--count",
            count,
            "--oracle-commit",
            PINNED_COMMIT,
            "--no-oracle-dirty",
            out,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return out

    def test_the_golden_run_validates_clean(self):
        completed = run_cli(VALIDATE, GOLDEN)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["invalid"], 0)
        self.assertEqual(report["parse_failures"], 0)
        self.assertEqual(report["records"], report["accepted"] + report["rejected"])
        self.assertEqual(report["publishable"], 0)
        self.assertEqual(report["named_runtime"], 0)
        self.assertEqual(report["mixed_oracle"], 0)
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
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["parse_failures"], 2)
            self.assertIn("JSON parse error", completed.stderr)

    def test_a_record_filed_under_the_wrong_verdict_is_fatal(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "rejected"
        )
        with tempfile.TemporaryDirectory(prefix="oracle-wrong-verdict-") as temp:
            path = Path(temp) / families.MEMORY_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("reserved for 'accepted' records", completed.stderr)

    def test_requested_reproduction_fails_when_the_runtime_is_unavailable(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        with tempfile.TemporaryDirectory(prefix="oracle-unavailable-") as temp:
            path = Path(temp) / families.ENCODER_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, "--reproduce", temp)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["reproduce"], {"unavailable": 1})
            self.assertIn("reproduction was unavailable", completed.stderr)

    def test_mixed_oracle_chains_are_not_counted_as_named_runtime(self):
        item = build(families.CREDIT_FAMILY)
        oracle = item["oracle"]
        oracle["implementation"] = "mixed"
        oracle["authority"] = "mixed-reference-and-runtime"
        item["provenance"]["claimed"] = "mixed-reference-and-runtime"
        item["meta"]["tags"][-1] = "mixed"
        oracle["availability"]["runtimes"][0]["bound"] = True
        oracle["availability"]["unbound"] = ["plasticity-lab"]
        runtime_stage = oracle["stages"][0]
        runtime_stage["implementation"] = "named-runtime"
        runtime_stage["oracle_id"] = "limbic-critic"
        runtime_stage["version"] = "0.0.0-double"
        runtime_stage["runtime_commit"] = "a" * 40
        runtime_stage["executable"] = "limbic-critic"
        runtime_stage.pop("module_digest", None)
        oracle["id"] = "limbic-critic+plasticity-ref"
        item["result"]["produced_by"] = oracle["id"]
        item["result_hash"] = canon.digest(item["result"])
        item["validation"] = record.assess(item)
        with tempfile.TemporaryDirectory(prefix="oracle-mixed-") as temp:
            path = Path(temp) / families.CREDIT_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["mixed_oracle"], 1)
            self.assertEqual(report["named_runtime"], 0)
            self.assertEqual(report["reference_oracle"], 0)

    def test_an_empty_directory_without_a_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="oracle-empty-") as temp:
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("required run manifest is missing", completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["records"], 0)

    def test_an_authenticated_but_empty_run_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="oracle-empty-manifest-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for path in list(out.iterdir()):
                if path.is_dir():
                    shutil.rmtree(path)
            manifest["families"] = {}
            manifest["files"] = {}
            manifest["oracle_availability"] = oracles.availability_report((), {})
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("at least one", completed.stderr)
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

    def test_manifest_digest_count_and_exact_file_set_are_enforced(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-") as temp:
            out = self.generate_run(temp)
            path = next(out.rglob("accepted-*.jsonl"))
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("sha256 mismatch", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-count-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            relative = next(iter(manifest["files"]))
            manifest["files"][relative]["records"] += 1
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("record-count mismatch", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-extra-") as temp:
            out = self.generate_run(temp)
            (out / "unmanifested.txt").write_text("not authenticated\n", encoding="utf-8")
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("unmanifested file", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-missing-") as temp:
            out = self.generate_run(temp)
            path = next(out.rglob("rejected-*.jsonl"))
            path.unlink()
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("manifest file is missing", completed.stderr)

    def test_manifest_paths_cannot_escape_the_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-path-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["../outside.jsonl"] = {
                "sha256": "0" * 64,
                "records": 0,
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("unsafe manifest file path", completed.stderr)

    def test_manifest_metadata_is_recomputed_from_the_captured_records(self):
        mutations = {
            "round": lambda manifest: manifest.__setitem__("round", manifest["round"] + 1),
            "seed": lambda manifest: manifest.__setitem__("seed", manifest["seed"] + 1),
            "count": lambda manifest: manifest.__setitem__(
                "count_per_family", manifest["count_per_family"] + 1
            ),
            "commit": lambda manifest: manifest.__setitem__("oracle_commit", "f" * 40),
            "module": lambda manifest: manifest.__setitem__(
                "module_digest", canon.digest({"forged": "implementation"})
            ),
            "summary": lambda manifest: manifest["families"][families.ENCODER_FAMILY][
                "accepted"
            ].__setitem__("records", 999),
        }
        for label, mutate in mutations.items():
            with (
                self.subTest(metadata=label),
                tempfile.TemporaryDirectory(prefix=f"oracle-metadata-{label}-") as temp,
            ):
                out = self.generate_run(temp)
                manifest_path = out / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                mutate(manifest)
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                completed = run_cli(VALIDATE, out)
                self.assertEqual(completed.returncode, 1)
                self.assertFalse(json.loads(completed.stdout)["manifest_valid"])
                self.assertTrue(completed.stderr.strip())

    def test_unhashable_manifest_and_record_metadata_are_bounded_findings(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-runtime-type-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["oracle_availability"]["runtimes"][0]["runtime"] = []
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("runtime names must be strings", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-record-implementation-type-") as temp:
            out = self.generate_run(temp)
            payload = next(
                path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip()
            )
            items = read_jsonl(payload)
            items[0]["oracle"]["implementation"] = []
            payload.write_text(
                "".join(canon.dumps_record(item) + "\n" for item in items),
                encoding="utf-8",
            )
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("oracle.implementation must be a string", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-count-bound-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["count_per_family"] = 10**12
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("count_per_family must be an integer", completed.stderr)

    def test_manifest_rejects_symlinked_and_hardlinked_payloads(self):
        with tempfile.TemporaryDirectory(prefix="oracle-symlink-") as temp:
            out = self.generate_run(temp)
            payload = next(out.rglob("accepted-*.jsonl"))
            outside = Path(temp) / "outside.jsonl"
            outside.write_bytes(payload.read_bytes())
            payload.unlink()
            payload.symlink_to(outside)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("symbolic links are not allowed", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-hardlink-") as temp:
            out = self.generate_run(temp)
            payload = next(out.rglob("accepted-*.jsonl"))
            outside = Path(temp) / "outside.jsonl"
            outside.write_bytes(payload.read_bytes())
            payload.unlink()
            os.link(outside, payload)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("hard-linked files are not allowed", completed.stderr)

    def test_intermediate_directory_swap_cannot_escape_the_pinned_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-directory-race-") as temp:
            out = self.generate_run(temp)
            family_dir = next(path for path in out.iterdir() if path.is_dir())
            outside = Path(temp) / "outside"
            original_snapshot = oracle_validate._snapshot_regular_file
            swapped = False

            def race(root_fd, path, relative, limit, expected_stat):
                nonlocal swapped
                if relative != "manifest.json" and not swapped:
                    family_dir.rename(outside)
                    family_dir.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original_snapshot(
                    root_fd,
                    path,
                    relative,
                    limit,
                    expected_stat,
                )

            with mock.patch.object(oracle_validate, "_snapshot_regular_file", side_effect=race):
                _manifest, snapshots, errors = oracle_validate.authenticate_manifest(out)
            self.assertTrue(swapped)
            self.assertFalse(
                any(snapshot.relative.startswith(f"{family_dir.name}/") for snapshot in snapshots)
            )
            self.assertTrue(any("could not capture authenticated file" in e for e in errors))

    def test_validation_uses_the_authenticated_bytes_not_a_later_path_read(self):
        with tempfile.TemporaryDirectory(prefix="oracle-snapshot-") as temp:
            out = self.generate_run(temp)
            _manifest, snapshots, errors = oracle_validate.authenticate_manifest(out)
            self.assertEqual(errors, [])
            snapshot = next(item for item in snapshots if item.body.strip())
            snapshot.path.write_text("not json\n", encoding="utf-8")
            totals, findings, _records = oracle_validate.validate_file(
                snapshot,
                require_runtime=False,
                reproduce=False,
                selected=set(),
            )
            self.assertGreater(totals["records"], 0)
            self.assertEqual(totals["parse_failures"], 0)
            self.assertFalse(any("JSON parse error" in finding for finding in findings))

    def test_a_final_record_exception_is_bounded_as_a_finding(self):
        snapshot = oracle_validate.FileSnapshot(
            path=Path("accepted-r01.jsonl"),
            relative=f"{families.ENCODER_FAMILY}/accepted-r01.jsonl",
            body=b"{}\n",
            device=1,
            inode=1,
        )
        with mock.patch.object(record, "classify", side_effect=RuntimeError("boom")):
            totals, findings, _records = oracle_validate.validate_file(
                snapshot,
                require_runtime=False,
                reproduce=False,
                selected=set(),
            )
        self.assertEqual(totals["invalid"], 1)
        self.assertTrue(any("internal exception: RuntimeError" in f for f in findings))

    def test_domain_malformed_neuron_records_are_findings_not_tracebacks(self):
        cases = {
            "zero-period": lambda scenario: scenario.__setitem__(
                "stimulus",
                {
                    "kind": "pulse_train",
                    "parameters": {
                        "amplitude": 1.0,
                        "period_ms": 0.0,
                        "width_ms": 0.5,
                        "onset_ms": 1.0,
                    },
                },
            ),
            "overflowing-ratio": lambda scenario: scenario.update(
                {"duration_ms": 1_000_000.0, "dt_ms": 0.000001}
            ),
        }
        for label, mutate in cases.items():
            with (
                self.subTest(case=label),
                tempfile.TemporaryDirectory(prefix=f"oracle-domain-{label}-") as temp,
            ):
                item = build(families.NEURON_FAMILY)
                mutate(item["scenario"])
                item["proposal_hash"] = canon.digest(record.proposal_of(item))
                item["validation"] = record.assess(item)
                verdict = item["validation"]["status"]
                path = Path(temp) / families.NEURON_FAMILY / f"{verdict}-r01.jsonl"
                path.parent.mkdir(parents=True)
                path.write_text(canon.dumps_record(item) + "\n", encoding="utf-8")
                write_test_manifest(temp)
                completed = run_cli(VALIDATE, temp)
                self.assertEqual(completed.returncode, 1)
                self.assertNotIn("Traceback", completed.stderr)
                self.assertTrue(completed.stderr.strip())

    def test_duplicate_ids_within_and_across_files_are_fatal(self):
        with tempfile.TemporaryDirectory(prefix="oracle-duplicate-within-") as temp:
            out = self.generate_run(temp)
            path = next(path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip())
            line = path.read_text().splitlines()[0]
            path.write_text(f"{line}\n{line}\n", encoding="utf-8")
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate record id", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-duplicate-across-") as temp:
            out = self.generate_run(temp)
            accepted = next(
                path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip()
            )
            rejected = accepted.with_name(accepted.name.replace("accepted-", "rejected-"))
            rejected.write_text(accepted.read_text(), encoding="utf-8")
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate record id", completed.stderr)

    def test_negative_max_findings_is_clamped_once(self):
        with tempfile.TemporaryDirectory(prefix="oracle-max-findings-") as temp:
            completed = run_cli(VALIDATE, "--max-findings", -5, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertRegex(completed.stderr.strip(), r"^\.\.\. [1-9][0-9]* more findings$")
            self.assertNotIn("Traceback", completed.stderr)


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
                PINNED_COMMIT,
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
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_cli(
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite", second.stderr)

    def test_require_runtime_refuses_to_write_when_nothing_is_bound(self):
        with tempfile.TemporaryDirectory(prefix="oracle-req-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE,
                "--require-runtime",
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                out,
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
                PINNED_COMMIT,
                out,
                env=env,
            )
            # The selected runtime clears the --require-runtime preflight.  The
            # generic protocol double then fails the encoder family schema, so
            # the transaction aborts instead of publishing a malformed run.
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertNotIn("these oracles are not bound", completed.stderr)
            self.assertIn("generated record failed its envelope", completed.stderr)
            self.assertFalse(out.exists())

    def test_an_unknown_family_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-bad-family-") as temp:
            completed = run_cli(GENERATE, "--family", "nope", Path(temp) / "run")
            self.assertEqual(completed.returncode, 2)
            self.assertIn("unknown families", completed.stderr)

    def test_an_unresolved_or_noncanonical_source_commit_writes_nothing(self):
        for forged in ("main", "a" * 39, "A" * 40, "a" * 41, "f" * 40):
            with (
                self.subTest(commit=forged),
                tempfile.TemporaryDirectory(prefix="oracle-bad-commit-") as temp,
            ):
                out = Path(temp) / "run"
                completed = run_cli(
                    GENERATE,
                    "--count",
                    1,
                    "--oracle-commit",
                    forged,
                    out,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertIn("resolve to an existing", completed.stderr)
                self.assertFalse(out.exists())

    def test_a_non_positive_count_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-count-") as temp:
            self.assertEqual(run_cli(GENERATE, "--count", 0, Path(temp) / "run").returncode, 2)
            self.assertEqual(run_cli(GENERATE, "--round", 0, Path(temp) / "run").returncode, 2)
            self.assertEqual(
                run_cli(
                    GENERATE,
                    "--count",
                    oracle_generate.MAX_COUNT + 1,
                    Path(temp) / "too-many",
                ).returncode,
                2,
            )
            self.assertEqual(
                run_cli(
                    GENERATE,
                    "--round",
                    oracle_generate.MAX_ROUND + 1,
                    Path(temp) / "too-late",
                ).returncode,
                2,
            )

    def test_count_limit_applies_to_the_whole_selected_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-total-count-") as temp:
            count = oracle_generate.MAX_RUN_RECORDS // len(families.FAMILY_NAMES) + 1
            completed = run_cli(
                GENERATE,
                "--count",
                count,
                "--oracle-commit",
                PINNED_COMMIT,
                Path(temp) / "run",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("requested run would contain", completed.stderr)

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
                PINNED_COMMIT,
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

    def test_generation_error_publishes_no_partial_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-build-") as temp:
            out = Path(temp) / "run"

            def fail_one(family, *_args, **_kwargs):
                if family == families.NEURON_FAMILY:
                    return [], [], ["synthetic build failure"]
                return [], [], []

            with (
                mock.patch.object(oracle_generate, "generate_family", side_effect=fail_one),
                mock.patch.object(oracle_generate, "write_jsonl") as write_jsonl,
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        "--no-oracle-dirty",
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            write_jsonl.assert_not_called()
            self.assertEqual(
                sorted(path.name for path in Path(temp).iterdir()),
                [".run.oracle-generate.lock"],
            )

    def test_staging_failure_publishes_no_partial_run_or_reservation(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-write-") as temp:
            out = Path(temp) / "run"
            with (
                mock.patch.object(
                    oracle_generate,
                    "generate_family",
                    return_value=([], [], []),
                ),
                mock.patch.object(
                    oracle_generate,
                    "write_jsonl",
                    side_effect=OSError("injected staging failure"),
                ),
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        "--no-oracle-dirty",
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            self.assertEqual(
                sorted(path.name for path in Path(temp).iterdir()),
                [".run.oracle-generate.lock"],
            )

    def test_a_stale_lock_path_does_not_block_a_new_kernel_lock(self):
        with tempfile.TemporaryDirectory(prefix="oracle-stale-lock-") as temp:
            out = Path(temp) / "run"
            lock_path = Path(temp) / ".run.oracle-generate.lock"
            lock_path.write_text("stale process\n", encoding="utf-8")
            completed = run_cli(
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                out,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(out.is_dir())

    def test_stdout_failure_reports_that_publication_already_succeeded(self):
        with tempfile.TemporaryDirectory(prefix="oracle-stdout-failure-") as temp:
            out = Path(temp) / "run"
            stderr_messages = []

            def fail_stdout(*args, **kwargs):
                if kwargs.get("file") is None:
                    raise BrokenPipeError("closed stdout")
                stderr_messages.append(" ".join(str(arg) for arg in args))

            with mock.patch("builtins.print", side_effect=fail_stdout):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertTrue(out.is_dir())
            self.assertTrue(any("run was published" in line for line in stderr_messages))

    def test_a_noncooperating_writer_cannot_win_after_reservation(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-race-") as temp:
            out = Path(temp) / "run"
            real_publish = oracle_generate.publish_noreplace

            def race(staging, destination, expected_identity):
                destination.mkdir()
                (destination / "other-writer.txt").write_text("must survive\n", encoding="utf-8")
                return real_publish(staging, destination, expected_identity)

            with (
                mock.patch.object(oracle_generate, "publish_noreplace", side_effect=race),
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        "--no-oracle-dirty",
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertEqual((out / "other-writer.txt").read_text(), "must survive\n")
            self.assertEqual(
                sorted(path.name for path in Path(temp).iterdir()),
                [".run.oracle-generate.lock", "run"],
            )

    def test_a_replaced_staging_inode_is_never_reported_as_published(self):
        with tempfile.TemporaryDirectory(prefix="oracle-source-race-") as temp:
            staging = Path(temp) / "staging"
            displaced = Path(temp) / "displaced"
            destination = Path(temp) / "run"
            staging.mkdir()
            (staging / "manifest.json").write_text("legitimate\n", encoding="utf-8")
            expected_identity = oracle_generate._directory_identity(staging)
            real_rename = oracle_generate._rename_noreplace

            def substitute(source, target):
                if Path(source) == staging:
                    staging.rename(displaced)
                    staging.mkdir()
                    (staging / "manifest.json").write_text(
                        "attacker-controlled\n", encoding="utf-8"
                    )
                return real_rename(source, target)

            with mock.patch.object(oracle_generate, "_rename_noreplace", side_effect=substitute):
                with self.assertRaises(OSError) as raised:
                    oracle_generate.publish_noreplace(staging, destination, expected_identity)
            self.assertEqual(raised.exception.errno, errno.ESTALE)
            self.assertFalse(destination.exists())
            self.assertEqual(
                (displaced / "manifest.json").read_text(encoding="utf-8"),
                "legitimate\n",
            )

    def test_atomic_publication_fails_closed_without_renameat2(self):
        with tempfile.TemporaryDirectory(prefix="oracle-no-renameat2-") as temp:
            staging = Path(temp) / "staging"
            destination = Path(temp) / "run"
            staging.mkdir()
            with mock.patch.object(oracle_generate.sys, "platform", "darwin"):
                with self.assertRaises(OSError) as raised:
                    oracle_generate.publish_noreplace(staging, destination)
            self.assertEqual(raised.exception.errno, errno.ENOSYS)
            self.assertTrue(staging.is_dir())
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
