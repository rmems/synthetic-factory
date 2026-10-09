#!/usr/bin/env python3
"""Fresh replay of a generated run: agreement, every tampering reported, every corruption refused.

``replay`` is the oracle that re-executes a record's own actions; each test
generates a small run into a private catalog and then edits a deep copy
of one of its records, or the run files themselves.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_record_support import (
    HEX64,
    RunSandbox,
    read_candidates,
    refusal,
    resign_bytes,
    resign_run,
    rewrite_run,
)
from tool_world_tamper_support import (
    EVIDENCE_TAMPERINGS,
    LABEL_TAMPERINGS,
    MALFORMED_RECORDS,
    REPLAY_TAMPERINGS,
    TRAINING_VIEW_TAMPERINGS,
    UNBINDABLE_RECORDS,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import generate, records, replay
from tool_world import vocabulary as cv


class ReplayAgreement(unittest.TestCase):
    def setUp(self):
        self.box = RunSandbox(self)
        self.root = self.box.root
        self.catalog_dir = self.box.catalog_dir
        self.catalog = self.box.catalog
        self.run_dir = self.root / "run"
        self.summary = generate.run(self.box.request())
        self.candidates = read_candidates(self.run_dir)

    def assert_each_tampering_is_a_mismatch(self, cases) -> None:
        for label, mutate, needle in cases:
            record = copy.deepcopy(self.candidates[0])
            mutate(record)
            with self.subTest(label=label):
                result = replay.replay_record(record, self.catalog)
                self.assertFalse(result.agreement)
                self.assertEqual(result.record_id, record["id"])
                self.assertTrue(
                    any(needle in item for item in result.mismatches), result.mismatches
                )
                self.assertEqual(result.row()["mismatches"], list(result.mismatches))

    def assert_each_rewrite_is_refused(self, cases) -> None:
        for label, mutate, code, needle in cases:
            record = copy.deepcopy(self.candidates[0])
            mutate(record)
            with self.subTest(label=label), refusal(self, code, needle):
                replay.replay_record(record, self.catalog)

    def test_a_generated_run_replays_in_full(self):
        report = replay.replay_run(self.run_dir, self.catalog)
        self.assertEqual(report["run_dir"], str(self.run_dir))
        self.assertEqual(report["records"], self.summary["records"])
        self.assertEqual(report["agreeing"], report["records"])
        self.assertTrue(report["passed"])
        for row, record in zip(report["results"], self.candidates, strict=True):
            self.assertEqual(row["id"], record["id"])
            self.assertTrue(row["agreement"])
            self.assertEqual(row["mismatches"], [])
            self.assertEqual(record["oracle"]["result_hash"], f"sha256:{row['replay_digest']}")
            self.assertEqual(row["success"], record["training_view"]["reward"]["success"])

    def test_every_tampering_of_the_replayed_evidence_is_a_mismatch(self):
        self.assert_each_tampering_is_a_mismatch(REPLAY_TAMPERINGS)

    def test_every_tampering_of_the_training_view_is_a_mismatch(self):
        self.assert_each_tampering_is_a_mismatch(TRAINING_VIEW_TAMPERINGS)

    def test_every_relabel_of_the_solver_or_curation_is_a_mismatch(self):
        self.assert_each_tampering_is_a_mismatch(LABEL_TAMPERINGS)

    def test_every_forgery_of_the_execution_evidence_is_a_mismatch(self):
        self.assert_each_tampering_is_a_mismatch(EVIDENCE_TAMPERINGS)

    def test_a_consistent_relabel_of_a_perturbed_record_is_caught_by_rerunning_the_policy(self):
        perturbed = next(
            (
                record
                for record in self.candidates
                if record["training_view"]["meta"]["variant"] != cv.VARIANT_GOLD
            ),
            None,
        )
        self.assertIsNotNone(perturbed)
        relabelled = copy.deepcopy(perturbed)
        success = relabelled["training_view"]["reward"]["success"]
        relabelled["training_view"]["meta"]["variant"] = cv.VARIANT_GOLD
        relabelled["solver"]["tool_policy"] = "workspace-gold"
        relabelled["curation"]["decision"] = cv.DECISION_ACCEPT if success else cv.DECISION_MEASURE
        relabelled["curation"]["reason_codes"] = records.reason_codes(cv.VARIANT_GOLD, success)
        result = replay.replay_record(relabelled, self.catalog)
        self.assertFalse(result.agreement)
        self.assertIn("the scripted policy replays a different gold trajectory", result.mismatches)
        self.assertNotIn("curation.decision differs from the replayed value", result.mismatches)

    def test_a_record_from_another_policy_version_cannot_be_rerun_and_says_so(self):
        record = copy.deepcopy(self.candidates[0])
        record["solver"]["version"] = HEX64
        result = replay.replay_record(record, self.catalog)
        self.assertIn(
            "solver.version is not the loaded scripted policy, so its plan cannot be re-run",
            result.mismatches,
        )
        self.assertIn("id differs from the replayed value", result.mismatches)

    def test_a_record_the_catalog_cannot_bind_is_refused(self):
        self.assert_each_rewrite_is_refused(UNBINDABLE_RECORDS)

    def test_a_malformed_record_is_refused_before_it_is_bound(self):
        self.assert_each_rewrite_is_refused(
            (label, mutate, cv.FINDING_RECORD_MALFORMED, needle)
            for label, mutate, needle in MALFORMED_RECORDS
        )

    def test_a_record_that_is_not_an_object_is_refused(self):
        with refusal(self, cv.FINDING_INPUT_NOT_AN_OBJECT, "record must be an object"):
            replay.replay_record("not a record", self.catalog)

    def test_corrupt_run_files_are_coded_refusals(self):
        original = (self.run_dir / generate.CANDIDATES_FILENAME).read_bytes()
        lines = original.splitlines()
        resign_bytes(self.run_dir, b"\n".join([b"{not json", *lines[1:]]) + b"\n")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "line 1 is not strict JSON"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, b"\n".join([b"[]", *lines[1:]]) + b"\n")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "line 1 is not an object"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, original + b"\xff")
        with refusal(self, cv.FINDING_RECORD_MALFORMED, "candidates.jsonl is not UTF-8"):
            replay.load_records(self.run_dir)
        resign_bytes(self.run_dir, original)
        run_file = self.run_dir / generate.RUN_FILENAME
        run_file.write_text('{"format": 1, "format": 2}', encoding="utf-8")
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "RUN.json is not strict JSON"):
            replay.replay_run(self.run_dir, self.catalog)
        run_file.write_text("[]", encoding="utf-8")
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "RUN.json must be an object"):
            replay.replay_run(self.run_dir, self.catalog)

    def test_run_level_refusals(self):
        candidates = self.run_dir / generate.CANDIDATES_FILENAME
        candidates.write_bytes(candidates.read_bytes() + b" ")
        with refusal(self, cv.FINDING_RUN_SHA_MISMATCH, "do not match RUN.json candidates_sha256"):
            replay.replay_run(self.run_dir, self.catalog)
        (self.run_dir / generate.RUN_FILENAME).unlink()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "missing RUN.json"):
            replay.replay_run(self.run_dir, self.catalog)
        candidates.unlink()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "missing candidates.jsonl"):
            replay.replay_run(self.run_dir, self.catalog)

    def test_candidates_must_be_the_records_run_json_names(self):
        rewrites = (
            ("dropped", self.candidates[:-1], "record 5 is not the record RUN.json names there"),
            ("emptied", [], "record 1 is not the record RUN.json names there (0 held, 5 named)"),
            ("reordered", list(reversed(self.candidates)), "record 1 is not the record"),
            ("duplicated", [self.candidates[0]] * 5, "record 2 is not the record"),
        )
        for label, candidates, needle in rewrites:
            resign_run(self.run_dir, candidates)
            with (
                self.subTest(label=label),
                refusal(self, cv.FINDING_RUN_INVENTORY_MISMATCH, needle),
            ):
                replay.replay_run(self.run_dir, self.catalog)

    def test_a_candidate_without_an_id_fails_the_inventory(self):
        nameless = copy.deepcopy(self.candidates)
        del nameless[0]["id"]
        resign_run(self.run_dir, nameless)
        with refusal(self, cv.FINDING_RUN_INVENTORY_MISMATCH, "record 1 is not the record"):
            replay.load_records(self.run_dir)

    def test_run_json_must_name_its_records(self):
        rows = self.summary["rows"]
        unnamed = {key: value for key, value in rows[0].items() if key != "id"}
        rewrites = (
            ("no rows", {"rows": [], "records": 0}, "names no records"),
            ("miscounted rows", {"records": len(rows) + 1}, "records must count its rows: 6 for 5"),
            ("records a bool", {"records": True}, "records must count its rows: True for 5"),
            ("rows not a list", {"rows": {}}, "rows must be a list of objects"),
            ("row not an object", {"rows": ["x", *rows[1:]]}, "rows must be a list of objects"),
            ("row id not a string", {"rows": [{**rows[0], "id": 7}, *rows[1:]]}, "string id"),
            ("row lacking an id", {"rows": [unnamed, *rows[1:]]}, "string id"),
        )
        run_file = self.run_dir / generate.RUN_FILENAME
        original = run_file.read_bytes()
        for label, fields, needle in rewrites:
            run_file.write_bytes(original)
            rewrite_run(self.run_dir, lambda summary, fields=fields: summary.update(fields))
            with self.subTest(label=label), refusal(self, cv.FINDING_RUN_FILE_INVALID, needle):
                replay.load_records(self.run_dir)

    def test_a_run_naming_no_records_cannot_pass_vacuously(self):
        resign_bytes(self.run_dir, b"")
        rewrite_run(self.run_dir, lambda summary: summary.update(rows=[], records=0))
        with refusal(self, cv.FINDING_RUN_FILE_INVALID, "names no records"):
            replay.replay_run(self.run_dir, self.catalog)

    def test_run_json_rows_must_name_the_records_the_header_draws(self):
        rows = self.summary["rows"]
        forgeries = (
            ("shed", self.candidates[:-1], rows[:-1], "row 5 does not name"),
            ("reordered", self.candidates[::-1], rows[::-1], "row 1 does not name"),
            ("duplicated", [self.candidates[0]] * 5, [rows[0]] * 5, "row 2 does not name"),
            ("drawn over", self.candidates * 2, rows * 2, "row 6 does not name"),
        )
        for label, candidates, named, needle in forgeries:
            resign_run(self.run_dir, candidates)
            rewrite_run(
                self.run_dir, lambda s, named=named: s.update(rows=named, records=len(named))
            )
            with (
                self.subTest(label=label),
                refusal(self, cv.FINDING_RUN_INVENTORY_MISMATCH, needle),
            ):
                replay.replay_run(self.run_dir, self.catalog)
        resign_run(self.run_dir, self.candidates)
        rewrite_run(self.run_dir, lambda s: s.update(rows=rows, records=len(rows), count=1))
        drawn = len(generate.expected_ids(self.catalog, {**self.summary, "count": 1}))
        with refusal(
            self, cv.FINDING_RUN_INVENTORY_MISMATCH, f"({len(rows)} named, {drawn} drawn)"
        ):
            replay.replay_run(self.run_dir, self.catalog)

    def test_a_tampered_record_fails_only_itself(self):
        tampered = copy.deepcopy(self.candidates)
        reward = tampered[0]["training_view"]["reward"]
        reward["success"] = not reward["success"]
        resign_run(self.run_dir, tampered)
        report = replay.replay_run(self.run_dir, self.catalog)
        self.assertFalse(report["passed"])
        self.assertEqual(report["agreeing"], report["records"] - 1)
        self.assertFalse(report["results"][0]["agreement"])
        self.assertTrue(all(row["agreement"] for row in report["results"][1:]))


if __name__ == "__main__":
    unittest.main()
