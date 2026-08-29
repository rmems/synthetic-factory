#!/usr/bin/env python3
"""Review-sample, promotion, and CLI tests for the curation gate."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from gate_fixture import (  # noqa: E402
    GATE_SCRIPT,
    PIPELINES,
    GateFixture,
    _episode,
    _preference,
    _read_jsonl,
    _thalamic,
    _tree_hashes,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402


class ReviewSampleTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_sample_stratifies_by_factory_kind_and_decision(self):
        rejected = _thalamic("t-rejected")
        rejected["safety_decision"] = {"decision": "REJECT", "rationale": "unsafe"}
        fixture = GateFixture(
            self.root,
            thalamic_records=[_thalamic("t-1"), rejected, _preference(), _episode()],
        )
        fixture.integrate()
        sample = fixture.sample()

        strata = {
            (row["factory"], row["kind"], row["decision"])
            for row in sample["strata"]
            if row["evidence"] == "corpus"
        }
        self.assertEqual(
            strata,
            {
                ("bridge-factory", "bridge_pair", "ACCEPT"),
                ("thalamic-mini", "thalamic", "ACCEPT"),
                ("thalamic-mini", "thalamic", "REJECT"),
                ("thalamic-mini", "preference", "ACCEPT"),
                ("thalamic-mini", "episode", "none"),
            },
        )
        self.assertEqual(sample["sampled_records"], len(sample["items"]))
        self.assertEqual(sample["schema"], curate_gate.SAMPLE_SCHEMA)
        self.assertTrue(sample["corpus_digest"].startswith("sha256:"))

    def test_sample_stratifies_manifest_evidence_by_exclusion_reason(self):
        fixture = GateFixture(self.root)
        fixture.integrate()
        sample = fixture.sample()

        manifest_strata = [
            row
            for row in sample["strata"]
            if row["evidence"] == "manifest" and row["exclusion_reason"] != "none"
        ]
        self.assertEqual(
            {row["exclusion_reason"] for row in manifest_strata},
            {"AMBIGUOUS_EVENT_ORDER", "INVALID_JSON"},
        )
        self.assertTrue(
            all(
                item.get("manifest_entry")
                for item in sample["items"]
                if item["evidence"] == "manifest"
            )
        )

    def test_sample_caps_each_stratum_and_is_deterministic(self):
        records = [_thalamic(f"t-{index}") for index in range(6)]
        fixture = GateFixture(self.root, thalamic_records=records)
        fixture.integrate()
        first = fixture.sample()

        thalamic_rows = [row for row in first["strata"] if row["kind"] == "thalamic"]
        self.assertEqual(len(thalamic_rows), 1)
        self.assertEqual(thalamic_rows[0]["population"], 6)
        self.assertEqual(thalamic_rows[0]["sampled"], curate_gate.DEFAULT_PER_STRATUM)

        # Same corpus, fresh computation: identical selection.
        again = curate_gate.build_sample(fixture.cleaned)
        self.assertEqual(
            [item["source"] for item in first["items"]],
            [item["source"] for item in again["items"]],
        )

    def test_per_stratum_option_widens_the_sample(self):
        records = [_thalamic(f"t-{index}") for index in range(6)]
        fixture = GateFixture(self.root, thalamic_records=records)
        fixture.integrate("--per-stratum", "4")
        sample = fixture.sample()
        thalamic_rows = [row for row in sample["strata"] if row["kind"] == "thalamic"]
        self.assertEqual(thalamic_rows[0]["sampled"], 4)

    def test_review_template_lists_every_sampled_record(self):
        fixture = GateFixture(self.root)
        fixture.integrate()
        sample = fixture.sample()
        template = json.loads((fixture.cleaned / curate_gate.REVIEW_FILENAME).read_text())
        self.assertEqual(
            sorted(template["verdicts"]), sorted(item["source"] for item in sample["items"])
        )
        self.assertEqual(template["corpus_digest"], sample["corpus_digest"])


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.fixture = GateFixture(self.root)
        self.assertEqual(self.fixture.integrate(), 0)

    def test_promotion_writes_a_new_curated_tree_and_final_manifest(self):
        review = self.fixture.accepted_review()
        self.assertEqual(self.fixture.promote(review), 0)

        curated = self.fixture.curated
        self.assertTrue((curated / "thalamic-mini" / "batch-r02.jsonl").is_file())
        self.assertFalse((curated / "PROVENANCE.md").exists())

        manifest = json.loads((curated / curate_gate.MANIFEST_FILENAME).read_text())
        self.assertTrue(manifest["training_ready"])
        self.assertEqual(manifest["blockers"], [])
        self.assertEqual(
            curate_gate.manifest_evidence_digest(manifest),
            manifest["evidence_digest"],
        )
        promotion = manifest["promotion"]
        self.assertEqual(promotion["curated_dir"], str(curated))
        self.assertEqual(promotion["records"], 4)
        self.assertEqual(
            promotion["promoter"],
            "pipelines/curate_gate.py immutable-staged-snapshot",
        )
        self.assertEqual(promotion["resorted"], 0)
        self.assertTrue(promotion["corpus_digest"].startswith("sha256:"))
        self.assertEqual(promotion["evidence_digest"], manifest["evidence_digest"])
        self.assertRegex(promotion["integration_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["review_sample_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["review_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(promotion["governance_evidence_digest"], r"^sha256:[0-9a-f]{64}$")
        emitted = {entry["path"] for entry in promotion["outputs"]}
        self.assertIn("thalamic-mini/batch-r02.jsonl", emitted)
        for entry in promotion["outputs"]:
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["review"]["reviewer"], "curation-reviewer")
        self.assertEqual(
            manifest["review"]["sampled_records"], self.fixture.sample()["sampled_records"]
        )
        # Review evidence travels with the curated corpus.
        self.assertTrue((curated / curate_gate.SAMPLE_FILENAME).is_file())
        self.assertTrue((curated / curate_gate.REVIEW_FILENAME).is_file())
        for cleaned_path in curate_gate.jsonl_paths(self.fixture.cleaned):
            relative = cleaned_path.relative_to(self.fixture.cleaned)
            self.assertEqual(
                curate_gate.file_sha256(cleaned_path),
                curate_gate.file_sha256(curated / relative),
            )
        cleaned_governance = self.fixture.cleaned / curate_gate.GOVERNANCE_DIRNAME
        curated_governance = curated / curate_gate.GOVERNANCE_DIRNAME
        self.assertEqual(
            _tree_hashes(cleaned_governance),
            _tree_hashes(curated_governance),
        )
        reward_sidecars = curated_governance / curate_gate.REWARD_SIDECAR_DIRNAME
        self.assertEqual(len(list(reward_sidecars.rglob("*.evidence"))), 1)

    def test_promotion_refuses_an_existing_curated_destination(self):
        review = self.fixture.accepted_review()
        self.fixture.curated.mkdir(parents=True)
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_refuses_a_dangling_destination_symlink(self):
        review = self.fixture.accepted_review()
        target = self.root / "must-not-be-promoted"
        try:
            self.fixture.curated.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")

        code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(code, 2)
        self.assertIn("existing curated destination", stderr)
        self.assertFalse(target.exists())

    def test_promotion_atomically_refuses_a_concurrent_destination(self):
        review = self.fixture.accepted_review()
        original = curate_gate._rename_noreplace
        reserved_inodes = []

        def reserve_then_publish(source, destination, label, expected_tree):
            destination.mkdir(parents=True)
            reserved_inodes.append(destination.stat().st_ino)
            return original(source, destination, label, expected_tree)

        with mock.patch.object(
            curate_gate,
            "_rename_noreplace",
            side_effect=reserve_then_publish,
        ):
            code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("refusing to overwrite an existing curated destination", stderr)
        self.assertEqual(self.fixture.curated.stat().st_ino, reserved_inodes[0])
        self.assertEqual(list(self.fixture.curated.iterdir()), [])
        self.assertEqual(list(self.root.glob(".curated-v1.staging-*")), [])

    def test_promotion_rejects_a_curated_destination_nested_under_cleaned(self):
        review = self.fixture.accepted_review()
        nested = self.fixture.cleaned / "nested-curated"

        code, _report, stderr = self.fixture.promote_report(review, nested)
        self.assertEqual(code, 2)
        self.assertIn("must be disjoint", stderr)
        self.assertFalse(nested.exists())

    def test_promotion_resolves_symlinked_destination_parents_before_safety_check(self):
        review = self.fixture.accepted_review()
        alias = self.root / "cleaned-alias"
        try:
            alias.symlink_to(self.fixture.cleaned, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        nested = alias / "nested-curated"

        code, _report, stderr = self.fixture.promote_report(review, nested)
        self.assertEqual(code, 2)
        self.assertIn("must be disjoint", stderr)
        self.assertFalse((self.fixture.cleaned / "nested-curated").exists())

    def test_promotion_refuses_an_unreviewed_sample(self):
        template = self.root / "unreviewed.json"
        template.write_text((self.fixture.cleaned / curate_gate.REVIEW_FILENAME).read_text())
        before = _tree_hashes(self.fixture.cleaned)
        code, report, _stderr = self.fixture.promote_report(template)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertTrue(
            any(blocker.startswith("REVIEW_INCOMPLETE:") for blocker in report["blockers"])
        )
        self.assertIn("REVIEW_REVIEWER_MISSING", report["blockers"])
        self.assertEqual(before, _tree_hashes(self.fixture.cleaned))

    def test_promotion_refuses_a_partially_reviewed_sample(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        dropped = sorted(review["verdicts"])[0]
        review["verdicts"].pop(dropped)
        review_path.write_text(json.dumps(review))
        self.assertEqual(self.fixture.promote(review_path), 1)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_refuses_when_a_sampled_record_is_rejected(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        target = sorted(review["verdicts"])[0]
        review["verdicts"][target] = {"verdict": "reject", "notes": "invented measurement"}
        review_path.write_text(json.dumps(review))
        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("REVIEW_REJECTED:1", report["blockers"])

    def test_promotion_refuses_a_review_bound_to_a_different_corpus(self):
        review_path = self.fixture.accepted_review()
        review = json.loads(review_path.read_text())
        review["corpus_digest"] = "sha256:" + "0" * 64
        review_path.write_text(json.dumps(review))
        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertIn("REVIEW_CORPUS_MISMATCH", report["blockers"])

    def test_promotion_refuses_after_the_corpus_changed_under_the_review(self):
        review = self.fixture.accepted_review()
        extra = self.fixture.cleaned / "thalamic-mini" / "batch-r03.jsonl"
        _write_jsonl(extra, [_thalamic("t-added-after-review")])
        code, report, _stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("REVIEW_CORPUS_MISMATCH", report["blockers"])
        self.assertIn("SAMPLE_CORPUS_MISMATCH", report["blockers"])

    def test_promotion_recomputes_and_rejects_a_reduced_review_sample(self):
        review_path = self.fixture.accepted_review()
        sample_path = self.fixture.cleaned / curate_gate.SAMPLE_FILENAME
        sample = json.loads(sample_path.read_text())
        removed = sample["items"].pop()
        sample["sampled_records"] -= 1
        sample_path.write_text(json.dumps(sample))
        review = json.loads(review_path.read_text())
        review["verdicts"].pop(removed["source"])
        review_path.write_text(json.dumps(review))

        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("SAMPLE_SELECTION_MISMATCH", report["blockers"])

    def test_promotion_rebuilds_review_candidates_from_copied_lane_evidence(self):
        manifest_path = self.fixture.cleaned / curate_gate.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text())
        manifest["exclusions"] = []
        manifest["review_candidates"] = []
        manifest["exclusion_reason_codes"] = {}
        manifest["counts"]["exclusions"] = 0
        manifest["evidence_digest"] = curate_gate.manifest_evidence_digest(manifest)

        sample = curate_gate.build_sample(
            self.fixture.cleaned,
            manifest["review_sampling"]["per_stratum"],
            [],
            evidence_digest=manifest["evidence_digest"],
        )
        sample["cleaned_dir"] = str(self.fixture.cleaned)
        manifest["review_sampling"]["sample_sha256"] = curate_gate.sha256_hex(
            curate_gate.training_audit.canonical_blob(sample).encode("utf-8")
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        (self.fixture.cleaned / curate_gate.SAMPLE_FILENAME).write_text(
            json.dumps(sample, indent=2) + "\n"
        )
        review = curate_gate.review_template(sample)
        review["reviewer"] = "evidence-attacker"
        review["reviewed_at"] = "2026-08-25T00:00:00Z"
        for source in review["verdicts"]:
            review["verdicts"][source] = {"verdict": "accept", "notes": ""}
        review_path = self.root / "tampered-review.json"
        review_path.write_text(json.dumps(review, indent=2) + "\n")

        code, report, _stderr = self.fixture.promote_report(review_path)
        self.assertEqual(code, 1)
        self.assertFalse(self.fixture.curated.exists())
        self.assertIn("LANE_EVIDENCE_SUMMARY_MISMATCH", report["blockers"])
        self.assertIn("SAMPLE_SELECTION_MISMATCH", report["blockers"])

    def test_promotion_rejects_tampered_copied_reward_evidence(self):
        review = self.fixture.accepted_review()
        sidecar = next(
            (
                self.fixture.cleaned
                / curate_gate.GOVERNANCE_DIRNAME
                / curate_gate.REWARD_SIDECAR_DIRNAME
            ).rglob("*.evidence")
        )
        sidecar.write_bytes(sidecar.read_bytes() + b"\n")

        code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("artifact hash mismatch", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_requires_an_integrated_cleaned_destination(self):
        review = self.fixture.accepted_review()
        (self.fixture.cleaned / curate_gate.MANIFEST_FILENAME).unlink()
        self.assertEqual(self.fixture.promote(review), 2)

    def test_promotion_never_writes_into_the_cleaned_corpus(self):
        review = self.fixture.accepted_review()
        before = _tree_hashes(self.fixture.cleaned)
        self.assertEqual(self.fixture.promote(review), 0)
        after = _tree_hashes(self.fixture.cleaned)
        self.assertEqual(before, after)

    def test_promotion_validates_and_publishes_one_immutable_snapshot(self):
        review = self.fixture.accepted_review()
        corpus_path = self.fixture.cleaned / "thalamic-mini" / "batch-r02.jsonl"
        sidecar_path = next(
            (
                self.fixture.cleaned
                / curate_gate.GOVERNANCE_DIRNAME
                / curate_gate.REWARD_SIDECAR_DIRNAME
            ).rglob("*.evidence")
        )
        manifest_path = self.fixture.cleaned / curate_gate.MANIFEST_FILENAME
        sample_path = self.fixture.cleaned / curate_gate.SAMPLE_FILENAME
        expected_corpus = corpus_path.read_bytes()
        expected_sidecar = sidecar_path.read_bytes()
        expected_review = review.read_bytes()
        expected_manifest = manifest_path.read_bytes()
        expected_sample = sample_path.read_bytes()
        original_run_gates = curate_gate.run_gates
        mutated = False

        def mutate_sources_after_snapshot(cleaned, **kwargs):
            nonlocal mutated
            if not mutated:
                mutated = True
                records = _read_jsonl(corpus_path)
                records[0]["state"]["env"] = "mutated after immutable snapshot"
                _write_jsonl(corpus_path, records)
                sidecar_path.write_bytes(expected_sidecar + b"\n")
                review.write_text('{"reviewer":"attacker"}\n')
            return original_run_gates(cleaned, **kwargs)

        with mock.patch.object(
            curate_gate,
            "run_gates",
            side_effect=mutate_sources_after_snapshot,
        ):
            self.assertEqual(self.fixture.promote(review), 0)

        curated_corpus = self.fixture.curated / corpus_path.relative_to(self.fixture.cleaned)
        curated_sidecar = self.fixture.curated / sidecar_path.relative_to(self.fixture.cleaned)
        self.assertEqual(curated_corpus.read_bytes(), expected_corpus)
        self.assertEqual(curated_sidecar.read_bytes(), expected_sidecar)
        self.assertEqual(
            (self.fixture.curated / curate_gate.REVIEW_FILENAME).read_bytes(),
            expected_review,
        )
        manifest = json.loads((self.fixture.curated / curate_gate.MANIFEST_FILENAME).read_text())
        promotion = manifest["promotion"]
        self.assertEqual(
            promotion["integration_manifest_sha256"],
            curate_gate.sha256_hex(expected_manifest),
        )
        self.assertEqual(
            promotion["review_sample_sha256"],
            curate_gate.sha256_hex(expected_sample),
        )
        self.assertEqual(
            promotion["review_sha256"],
            curate_gate.sha256_hex(expected_review),
        )

    def test_promotion_rejects_a_staged_mutation_during_output_inventory(self):
        review = self.fixture.accepted_review()
        original = curate_gate._promotion_outputs
        mutated = False

        def mutate_after_inventory(staged):
            nonlocal mutated
            entries = original(staged)
            if not mutated:
                mutated = True
                corpus = staged / "thalamic-mini" / "batch-r02.jsonl"
                corpus.write_text("{invalid-json\n", encoding="utf-8")
            return entries

        with mock.patch.object(
            curate_gate,
            "_promotion_outputs",
            side_effect=mutate_after_inventory,
        ):
            code, _report, stderr = self.fixture.promote_report(review)
        self.assertEqual(code, 2)
        self.assertIn("staged corpus changed after final promotion validation", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_publisher_reauthenticates_after_the_final_inventory(self):
        review = self.fixture.accepted_review()
        original = curate_gate._promotion_outputs
        inventories = 0

        def mutate_after_final_inventory(staged):
            nonlocal inventories
            entries = original(staged)
            inventories += 1
            if inventories == 2:
                corpus = staged / "thalamic-mini" / "batch-r02.jsonl"
                corpus.write_text("{invalid-json\n", encoding="utf-8")
            return entries

        with mock.patch.object(
            curate_gate,
            "_promotion_outputs",
            side_effect=mutate_after_final_inventory,
        ):
            code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(inventories, 2)
        self.assertEqual(code, 2)
        self.assertIn("staging tree changed after final validation", stderr)
        self.assertFalse(self.fixture.curated.exists())

    def test_promotion_publisher_reauthenticates_the_staging_tree(self):
        review = self.fixture.accepted_review()
        original = curate_gate._rename_noreplace

        def mutate_then_publish(source, destination, label, expected_tree):
            corpus = source / "thalamic-mini" / "batch-r02.jsonl"
            corpus.write_text("{invalid-json\n", encoding="utf-8")
            return original(source, destination, label, expected_tree)

        with mock.patch.object(
            curate_gate,
            "_rename_noreplace",
            side_effect=mutate_then_publish,
        ):
            code, _report, stderr = self.fixture.promote_report(review)

        self.assertEqual(code, 2)
        self.assertIn("staging tree changed after final validation", stderr)
        self.assertFalse(self.fixture.curated.exists())


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_cli_integrate_then_promote(self):
        fixture = GateFixture(self.root)
        integrate = subprocess.run(
            [
                sys.executable,
                str(GATE_SCRIPT),
                "integrate",
                "--plan",
                str(fixture.plan_path),
                "--cleaned-out",
                str(fixture.cleaned),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(integrate.returncode, 0, integrate.stderr)
        summary = json.loads(integrate.stdout)
        self.assertTrue(summary["training_ready"])
        self.assertEqual(summary["gate_blockers"], [])

        review = fixture.accepted_review()
        promoted = subprocess.run(
            [
                sys.executable,
                str(GATE_SCRIPT),
                "promote",
                "--cleaned",
                str(fixture.cleaned),
                "--review",
                str(review),
                "--curated-out",
                str(fixture.curated),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(promoted.returncode, 0, promoted.stderr)
        result = json.loads(promoted.stdout)
        self.assertTrue(result["promoted"])
        self.assertEqual(result["records"], 4)



if __name__ == '__main__':
    unittest.main()
