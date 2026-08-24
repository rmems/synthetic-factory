#!/usr/bin/env python3
"""Tests for the independent-arm gate on two-session preference rounds."""

import copy
import hashlib
import io
import json
import contextlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import preference_arms  # noqa: E402
import quality_gate  # noqa: E402
import training_audit  # noqa: E402

ARM_FIXTURES = REPO / "tests" / "fixtures" / "preference-arms"
TWO_SESSION_ROUND = ARM_FIXTURES / "batch-r11.jsonl"
NEAR_VERBATIM = ARM_FIXTURES / "near-verbatim-r11.jsonl"
GATE_LABEL_ONLY = ARM_FIXTURES / "gate-label-only-r11.jsonl"
SINGLE_SESSION = ARM_FIXTURES / "single-session-r11.jsonl"

# Pinned so a scan that rewrote its own input would fail loudly rather than
# verify itself against a baseline it just produced.
GOLDEN_FIXTURE_SHA256 = {
    "batch-r11.jsonl": "5f24db6543f41782ac61aadfddab707cf5c1cac4249adadaf056d99bbb677a5c",
    "near-verbatim-r11.jsonl": (
        "3e08181a1aa61772edc9fb780d7ea2a76a0892ffa9451e1e0e14c1898f6e5546"
    ),
    "gate-label-only-r11.jsonl": (
        "75e85ca69792a78c953ab91a4a9585d8b860398317739ffc3a143d711a3aff9c"
    ),
    "single-session-r11.jsonl": (
        "f6c4588141d91bed533f651971f3438cace26dcba1a0c693c29407a3f1c379a2"
    ),
}


def load(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def first(path):
    return load(path)[0]


def run_cli(argv):
    """Return (exit_code, stdout) for a CLI invocation."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = preference_arms.main(argv)
    return code, out.getvalue(), err.getvalue()


def check(record, **kwargs):
    return preference_arms.check_pair(
        record, source_path="memory.jsonl", source_line=1, **kwargs
    )


class ArmDistanceMetric(unittest.TestCase):
    def test_default_floor_tracks_the_single_embedding_threshold(self):
        self.assertAlmostEqual(
            preference_arms.DEFAULT_MIN_ARM_DISTANCE,
            1.0 - quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
            places=9,
        )

    def test_shared_context_and_bookkeeping_do_not_create_distance(self):
        arm = {
            "id": "pair-chosen",
            "state": {"sim_or_real": "designed", "site": "alpha"},
            "proposed_action": {"action": "hold"},
            "safety_decision": {"decision": "MODIFY", "rationale": "bounded window"},
            "meta": {"tags": ["chosen"]},
        }
        twin = copy.deepcopy(arm)
        twin["id"] = "pair-rejected"
        twin["state"] = {"sim_or_real": "designed", "site": "omega"}
        twin["proposed_action"] = {"action": "release"}
        twin["meta"] = {"tags": ["rejected", "extra"]}
        self.assertEqual(preference_arms.arm_distance(arm, twin), 0.0)

    def test_numeric_leaves_stay_atomic(self):
        left = {"reward_components": {"safety": 0.2, "total": 0.2}}
        right = {"reward_components": {"safety": -0.2, "total": -0.2}}
        self.assertGreater(preference_arms.arm_distance(left, right), 0.0)

    def test_list_order_is_not_a_difference(self):
        left = {"safety_decision": {"evidence": ["alpha", "omega"]}}
        right = {"safety_decision": {"evidence": ["omega", "alpha"]}}
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_wordless_strings_stay_atomic(self):
        left = {"future_outcome": {"incident": "—"}}
        right = {"future_outcome": {"incident": "…"}}
        self.assertEqual(preference_arms.arm_distance(left, right), 1.0)
        self.assertEqual(
            preference_arms.arm_distance(left, copy.deepcopy(left)), 0.0
        )

    def test_empty_contrast_surfaces_are_degenerate_not_distant(self):
        bare = {"state": {"sim_or_real": "designed"}, "meta": {}}
        self.assertEqual(preference_arms.arm_distance(bare, copy.deepcopy(bare)), 0.0)

    def test_cosine_similarity_is_clamped_and_symmetric(self):
        record = first(TWO_SESSION_ROUND)
        left = preference_arms.arm_terms(record["chosen"])
        right = preference_arms.arm_terms(record["rejected"])
        forward = preference_arms.cosine_similarity(left, right)
        backward = preference_arms.cosine_similarity(right, left)
        self.assertAlmostEqual(forward, backward, places=12)
        self.assertGreaterEqual(forward, 0.0)
        self.assertLessEqual(forward, 1.0)


class TwoSessionRoundClearsTheGate(unittest.TestCase):
    def test_scan_passes_with_independent_arms_and_attestation(self):
        scan = preference_arms.scan_source(TWO_SESSION_ROUND)
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.summary["preference_pairs"], 3)
        self.assertEqual(scan.summary["blocked_pairs"], 0)
        self.assertEqual(scan.summary["independent_pairs"], 3)
        self.assertEqual(scan.summary["two_session_pairs"], 3)
        self.assertEqual(scan.summary["context_purity_pct"], 100.0)
        self.assertEqual(scan.summary["reason_codes"], {})
        self.assertGreater(
            scan.summary["observed_min_arm_distance"],
            preference_arms.DEFAULT_MIN_ARM_DISTANCE,
        )
        self.assertTrue(all(d.isolation == "two-session" for d in scan.decisions))

    def test_cli_exits_zero_and_reports_the_pass(self):
        code, out, err = run_cli(["scan", str(TWO_SESSION_ROUND)])
        self.assertEqual(code, 0)
        self.assertIn("arm gate: PASS", err)
        self.assertIn("Blocked: 0", out)

    def test_strict_audit_reports_full_preference_purity(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "run"
            factory = run_dir / "failure-as-fuel-preference-cascade"
            factory.mkdir(parents=True)
            (factory / "batch-r11.jsonl").write_bytes(TWO_SESSION_ROUND.read_bytes())
            report = training_audit.audit_run(run_dir)
        self.assertEqual(report["preferences"]["pairs"], 3)
        self.assertEqual(report["preferences"]["same_context"], 3)
        self.assertEqual(report["preferences"]["context_purity_pct"], 100.0)
        self.assertEqual(report["blockers"], [])

    def test_tighter_floor_is_honored(self):
        scan = preference_arms.scan_source(TWO_SESSION_ROUND, min_distance=0.9)
        self.assertTrue(scan.blocked)
        self.assertEqual(scan.summary["blocked_pairs"], 3)
        self.assertEqual(
            scan.summary["reason_codes"],
            {preference_arms.REASON_NEAR_VERBATIM: 3},
        )
        code, _, _ = run_cli(["scan", str(TWO_SESSION_ROUND), "--min-distance", "0.9"])
        self.assertEqual(code, 1)


class CorrelatedArmsAreBlocked(unittest.TestCase):
    def test_verbatim_restatement_of_the_rejected_arm(self):
        scan = preference_arms.scan_source(NEAR_VERBATIM)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertTrue(decision.same_context)
        self.assertEqual(decision.isolation, "two-session")
        self.assertEqual(
            decision.reason_codes, (preference_arms.REASON_NEAR_VERBATIM,)
        )

    def test_gate_label_only_repair(self):
        scan = preference_arms.scan_source(GATE_LABEL_ONLY)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertGreater(decision.arm_distance, 0.0)
        self.assertLessEqual(
            decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE
        )
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)

    def test_cli_exits_nonzero_on_a_blocked_pair(self):
        code, _, err = run_cli(["scan", str(NEAR_VERBATIM)])
        self.assertEqual(code, 1)
        self.assertIn("arm gate: FAIL", err)

    def test_empty_arm_contrast_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"] = {
            "id": record["chosen"]["id"],
            "state": record["chosen"]["state"],
            "proposed_action": record["chosen"]["proposed_action"],
            "meta": record["chosen"]["meta"],
        }
        decision = check(record)
        self.assertIn(preference_arms.REASON_CONTRAST_EMPTY, decision.reason_codes)


class IsolationAttestation(unittest.TestCase):
    def test_single_session_attestation_is_rejected(self):
        scan = preference_arms.scan_source(SINGLE_SESSION)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.isolation, "single-session")
        self.assertEqual(
            decision.reason_codes, (preference_arms.REASON_SINGLE_SESSION,)
        )
        self.assertGreater(
            decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE
        )

    def test_legacy_scan_reports_but_does_not_block_on_attestation(self):
        scan = preference_arms.scan_source(SINGLE_SESSION, require_isolation=False)
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.decisions[0].isolation, "single-session")
        self.assertEqual(scan.summary["two_session_pairs"], 0)

    def test_cli_flag_relaxes_the_attestation(self):
        code, _, _ = run_cli(["scan", str(SINGLE_SESSION)])
        self.assertEqual(code, 1)
        code, _, _ = run_cli(
            ["scan", str(SINGLE_SESSION), "--no-require-isolation"]
        )
        self.assertEqual(code, 0)

    def test_undeclared_isolation_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        for holder in (record, record["chosen"], record["rejected"]):
            holder["meta"].pop("isolation", None)
        decision = check(record)
        self.assertIsNone(decision.isolation)
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_UNDECLARED,),
        )

    def test_conflicting_declarations_are_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["meta"]["isolation"] = "single-session"
        decision = check(record)
        self.assertEqual(decision.isolation, "single-session|two-session")
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_CONFLICT,),
        )

    def test_arm_only_declaration_is_accepted(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["meta"].pop("isolation")
        self.assertEqual(check(record).reason_codes, ())

    def test_non_object_meta_is_treated_as_no_declaration(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["meta"] = "two-session"
        record["chosen"]["meta"] = None
        record["rejected"]["meta"] = ["two-session"]
        decision = check(record)
        self.assertIsNone(decision.isolation)
        self.assertEqual(
            decision.reason_codes,
            (preference_arms.REASON_ISOLATION_UNDECLARED,),
        )


class ContextPurityIsDelegatedAndEnforced(unittest.TestCase):
    def test_state_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["state"]["environment"]["observed_c"] = -70.0
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(
            preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes
        )

    def test_proposal_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["proposed_action"]["arguments"]["silence_minutes"] = 5
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(
            preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes
        )

    def test_malformed_pair_is_reported_once(self):
        decision = check({"id": "broken", "chosen": "not an object", "rejected": {}})
        self.assertEqual(
            decision.reason_codes, (preference_arms.REASON_MALFORMED,)
        )
        self.assertIsNone(decision.arm_distance)


class SourceHandling(unittest.TestCase):
    def test_directory_source_scans_every_batch(self):
        scan = preference_arms.scan_source(ARM_FIXTURES)
        self.assertEqual(scan.summary["preference_pairs"], 6)
        self.assertEqual(scan.summary["blocked_pairs"], 3)
        self.assertEqual(
            sorted({d.source_path for d in scan.decisions}),
            [
                "batch-r11.jsonl",
                "gate-label-only-r11.jsonl",
                "near-verbatim-r11.jsonl",
                "single-session-r11.jsonl",
            ],
        )

    def test_non_preference_records_are_skipped_not_gated(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mixed.jsonl"
            record = first(TWO_SESSION_ROUND)
            path.write_text(
                json.dumps({"id": "solo", "state": {"sim_or_real": "designed"}})
                + "\n"
                + json.dumps(record)
                + "\n",
                encoding="utf-8",
            )
            scan = preference_arms.scan_source(path)
        self.assertEqual(scan.summary["preference_pairs"], 1)
        self.assertEqual(scan.summary["skipped_non_preference_records"], 1)
        self.assertFalse(scan.blocked)

    def test_scan_without_preference_pairs_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty.jsonl"
            path.write_text(
                json.dumps({"id": "solo", "state": {"sim_or_real": "designed"}})
                + "\n",
                encoding="utf-8",
            )
            code, _, err = run_cli(["scan", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("no preference pairs", err)

    def test_missing_and_non_jsonl_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "absent.jsonl"
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(missing)
            wrong = Path(td) / "batch.json"
            wrong.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(wrong)
            empty_dir = Path(td) / "empty-dir"
            empty_dir.mkdir()
            with self.assertRaises(preference_arms.PreferenceArmsError):
                preference_arms.scan_source(empty_dir)

    def test_unreadable_json_is_reported_with_its_location(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "broken.jsonl"
            path.write_text("{not json}\n", encoding="utf-8")
            with self.assertRaises(preference_arms.PreferenceArmsError) as ctx:
                preference_arms.scan_source(path)
        self.assertIn("broken.jsonl:1", str(ctx.exception))

    def test_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "padded.jsonl"
            path.write_text(
                "\n" + json.dumps(first(TWO_SESSION_ROUND)) + "\n\n",
                encoding="utf-8",
            )
            scan = preference_arms.scan_source(path)
        self.assertEqual(scan.summary["preference_pairs"], 1)
        self.assertFalse(scan.blocked)

    def test_out_of_range_min_distance_is_refused(self):
        for value in ("1.0", "-0.1", "nan", "not-a-number"):
            with self.subTest(value), self.assertRaises(SystemExit):
                run_cli(["scan", str(TWO_SESSION_ROUND), "--min-distance", value])

    def test_cli_reports_an_unreadable_source_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as td:
            code, _, err = run_cli(["scan", str(Path(td) / "absent.jsonl")])
        self.assertEqual(code, 1)
        self.assertIn("preference arm gate failed", err)


class ScanIsReadOnly(unittest.TestCase):
    def test_fixtures_match_pinned_digests_after_a_full_scan(self):
        preference_arms.scan_source(ARM_FIXTURES)
        for name, digest in GOLDEN_FIXTURE_SHA256.items():
            with self.subTest(name):
                self.assertEqual(
                    hashlib.sha256((ARM_FIXTURES / name).read_bytes()).hexdigest(),
                    digest,
                )

    def test_check_pair_does_not_mutate_its_record(self):
        record = first(TWO_SESSION_ROUND)
        before = json.dumps(record, sort_keys=True)
        preference_arms.check_pair(
            record, source_path="memory.jsonl", source_line=1
        )
        self.assertEqual(json.dumps(record, sort_keys=True), before)

    def test_json_report_is_serializable_and_complete(self):
        code, out, _ = run_cli(["scan", str(TWO_SESSION_ROUND), "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(len(report["decisions"]), 3)
        self.assertEqual(report["summary"]["gate"]["name"], preference_arms.GATE_NAME)
        self.assertFalse(any(d["blocked"] for d in report["decisions"]))


class ProtocolIsDocumentedAndWired(unittest.TestCase):
    """The gate only helps if the generating surfaces actually run it."""

    @classmethod
    def setUpClass(cls):
        cls.doc = (REPO / "docs" / "preference-isolation.md").read_text()
        cls.prompt = (
            REPO / "prompts" / "05-failure-as-fuel-preference-cascade.md"
        ).read_text()
        cls.workflow = (
            REPO
            / ".claude"
            / "skills"
            / "run-synthetic-factory"
            / "factory-window.workflow.js"
        ).read_text()

    def test_single_session_path_is_deprecated_in_docs_and_prompt(self):
        self.assertIn("single-session path is deprecated", self.doc.lower())
        self.assertIn("single-session path is DEPRECATED", self.prompt)

    def test_docs_and_prompt_name_the_arm_gate_command(self):
        for text in (self.doc, self.prompt):
            self.assertIn("pipelines/preference_arms.py", text)

    def test_session_b_runs_the_arm_gate_before_publishing(self):
        session_b = self.workflow.split("You are Session B", 1)[1]
        gate = session_b.index("preference_arms.py")
        publish = session_b.index("round_txn.py publish")
        self.assertLess(gate, publish)

    def test_workflow_stamps_the_two_session_attestation(self):
        self.assertIn(
            f'meta.isolation="{preference_arms.TWO_SESSION}"', self.workflow
        )


if __name__ == "__main__":
    unittest.main()
