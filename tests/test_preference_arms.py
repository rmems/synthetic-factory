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
    "near-verbatim-r11.jsonl": ("3e08181a1aa61772edc9fb780d7ea2a76a0892ffa9451e1e0e14c1898f6e5546"),
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
    return preference_arms.check_pair(record, source_path="memory.jsonl", source_line=1, **kwargs)


class ArmDistanceMetric(unittest.TestCase):
    def test_default_floor_is_owned_by_the_lexical_gate(self):
        self.assertEqual(preference_arms.DEFAULT_MIN_ARM_DISTANCE, 0.03)
        self.assertNotIn(
            "DEFAULT_EMBEDDING_THRESHOLD",
            (REPO / "pipelines" / "preference_arms.py").read_text(),
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

    def test_observable_numeric_leaves_stay_atomic(self):
        left = {"future_outcome": {"latency_ms": 20}}
        right = {"future_outcome": {"latency_ms": 200}}
        self.assertGreater(preference_arms.arm_distance(left, right), 0.0)

    def test_list_order_is_not_a_difference(self):
        left = {"spike_events": ["alpha", "omega"]}
        right = {"spike_events": ["omega", "alpha"]}
        self.assertEqual(preference_arms.arm_distance(left, right), 0.0)

    def test_wordless_strings_stay_atomic(self):
        left = {"future_outcome": {"incident": "—"}}
        right = {"future_outcome": {"incident": "…"}}
        self.assertEqual(preference_arms.arm_distance(left, right), 1.0)
        self.assertEqual(preference_arms.arm_distance(left, copy.deepcopy(left)), 0.0)

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

    def test_unspaced_unicode_edit_is_proportional_not_an_opaque_replacement(self):
        shared = "保持制动直到传感器确认安全并且现场操作员明确批准恢复运行" * 4
        changed = shared.replace("安全", "危险", 1)
        distance = preference_arms.arm_distance(
            {"future_outcome": {"summary": shared}},
            {"future_outcome": {"summary": changed}},
        )
        self.assertGreater(distance, 0.0)
        self.assertLessEqual(distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)

    def test_accent_only_edits_do_not_manufacture_arm_independence(self):
        self.assertEqual(
            preference_arms.arm_distance(
                {"future_outcome": {"summary": "mantén la acción segura"}},
                {"future_outcome": {"summary": "manten la accion segura"}},
            ),
            0.0,
        )

    def test_programmatic_distance_floor_rejects_non_finite_or_out_of_range_values(self):
        record = first(TWO_SESSION_ROUND)
        for value in (float("nan"), float("inf"), -0.01, 1.0, True, "0.03"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "arm-distance floor"):
                    check(record, min_distance=value)


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

    def test_every_fixture_pair_has_a_shared_machine_observable_delta(self):
        for record in load(TWO_SESSION_ROUND):
            with self.subTest(record=record["id"]):
                self.assertTrue(
                    preference_arms.machine_observable_deltas(
                        record["chosen"],
                        record["rejected"],
                    )
                )

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
            decision.reason_codes,
            (
                preference_arms.REASON_OBSERVABLES_IDENTICAL,
                preference_arms.REASON_NEAR_VERBATIM,
            ),
        )

    def test_gate_label_only_repair(self):
        scan = preference_arms.scan_source(GATE_LABEL_ONLY)
        self.assertTrue(scan.blocked)
        decision = scan.decisions[0]
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertLessEqual(decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)
        self.assertIn(preference_arms.REASON_LABEL_ONLY_COPY, decision.reason_codes)

    def test_short_label_only_copy_is_blocked_even_above_the_lexical_floor(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        for name, decision_label in (("chosen", "REJECT"), ("rejected", "ACCEPT")):
            arm = record[name]
            record[name] = {
                "id": arm["id"],
                "state": arm["state"],
                "proposed_action": arm["proposed_action"],
                "safety_decision": {
                    "decision": decision_label,
                    "rationale": "same bounded rationale",
                },
                "meta": arm["meta"],
            }
        decision = check(record)
        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_LABEL_ONLY_COPY, decision.reason_codes)

    def test_reward_relabeling_cannot_turn_a_label_copy_into_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        chosen_reward = record["chosen"]["reward_components"]
        chosen_reward["task_progress"] += 0.1
        chosen_reward["total"] += 0.1

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)

    def test_unknown_extension_padding_is_blocked_and_cannot_add_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["padding"] = (
            "unrelated filler alpha beta gamma delta epsilon zeta eta theta"
        )

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(
            preference_arms.REASON_EXTENSION_FIELDS,
            decision.reason_codes,
        )

    def test_nested_behavior_padding_cannot_establish_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["executed_action"]["padding"] = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
        )

        decision = check(record)

        self.assertGreater(decision.arm_distance, 0.0)
        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_safety_rationale_padding_cannot_establish_independence(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        record["chosen"]["safety_decision"]["rationale"] += (
            " alpha beta gamma delta epsilon zeta eta theta iota kappa"
        )

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_cross_script_homoglyph_does_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        action = record["chosen"]["executed_action"]["action"]
        record["chosen"]["executed_action"]["action"] = action.replace("v", "ν", 1)

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)
        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_cyrillic_palochka_does_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(GATE_LABEL_ONLY))
        action = record["chosen"]["executed_action"]["action"]
        record["chosen"]["executed_action"]["action"] = action.replace("l", "ӏ", 1)

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

    def test_invisible_format_marks_do_not_inflate_copy_distance(self):
        record = copy.deepcopy(first(NEAR_VERBATIM))
        chosen = copy.deepcopy(record["rejected"])
        action = chosen["executed_action"]["action"]
        chosen["executed_action"]["action"] = "\u200d".join(action)
        record["chosen"] = chosen

        decision = check(record)

        self.assertEqual(decision.arm_distance, 0.0)
        self.assertIn(preference_arms.REASON_NEAR_VERBATIM, decision.reason_codes)
        self.assertIn(
            preference_arms.REASON_OBSERVABLES_IDENTICAL,
            decision.reason_codes,
        )

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
        self.assertEqual(decision.reason_codes, (preference_arms.REASON_SINGLE_SESSION,))
        self.assertGreater(decision.arm_distance, preference_arms.DEFAULT_MIN_ARM_DISTANCE)

    def test_legacy_scan_reports_but_does_not_block_on_attestation(self):
        scan = preference_arms.scan_source(SINGLE_SESSION, require_isolation=False)
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.decisions[0].isolation, "single-session")
        self.assertEqual(scan.summary["two_session_pairs"], 0)

    def test_cli_flag_relaxes_the_attestation(self):
        code, _, _ = run_cli(["scan", str(SINGLE_SESSION)])
        self.assertEqual(code, 1)
        code, _, _ = run_cli(["scan", str(SINGLE_SESSION), "--no-require-isolation"])
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

    def test_record_attestation_is_not_a_trusted_publication_marker(self):
        decision = check(
            first(TWO_SESSION_ROUND),
            require_trusted_isolation=True,
        )
        self.assertIn(
            preference_arms.REASON_ISOLATION_UNTRUSTED,
            decision.reason_codes,
        )

    def test_publisher_controlled_two_session_marker_clears_the_gate(self):
        scan = preference_arms.scan_source(
            TWO_SESSION_ROUND,
            trusted_isolation=preference_arms.TWO_SESSION,
            require_trusted_isolation=True,
        )
        self.assertFalse(scan.blocked)
        self.assertEqual(scan.summary["trusted_two_session_pairs"], 3)

    def test_relabelled_record_cannot_override_a_conflicting_publisher_marker(self):
        decision = check(
            first(TWO_SESSION_ROUND),
            trusted_isolation="single-session",
            require_trusted_isolation=True,
        )
        self.assertIn(
            preference_arms.REASON_ISOLATION_UNTRUSTED,
            decision.reason_codes,
        )


class ContextPurityIsDelegatedAndEnforced(unittest.TestCase):
    def test_state_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["state"]["environment"]["observed_c"] = -70.0
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes)

    def test_proposal_drift_is_blocked(self):
        record = copy.deepcopy(first(TWO_SESSION_ROUND))
        record["chosen"]["proposed_action"]["arguments"]["silence_minutes"] = 5
        decision = check(record)
        self.assertFalse(decision.same_context)
        self.assertIn(preference_arms.REASON_CONTEXT_DIVERGES, decision.reason_codes)

    def test_malformed_pair_is_reported_once(self):
        decision = check({"id": "broken", "chosen": "not an object", "rejected": {}})
        self.assertEqual(decision.reason_codes, (preference_arms.REASON_MALFORMED,))
        self.assertIsNone(decision.arm_distance)


class DiagnosisHandoffVerification(unittest.TestCase):
    TOKEN = "a" * 32

    def stage(self, root, *, count=3):
        stage = (
            Path(root)
            / "outputs"
            / "staging"
            / "2026-08-17"
            / "failure-as-fuel-preference-cascade"
            / f"r11-{self.TOKEN}"
        )
        stage.mkdir(parents=True)
        names = []
        for index in range(1, count + 1):
            name = f"diagnosis-{index:02d}-r11.md"
            (stage / name).write_text(
                f"root cause {index}\nrepair sketch {index}\n",
                encoding="utf-8",
            )
            names.append(name)
        return stage, names

    def test_receipt_binds_names_sizes_and_digests(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            receipt = preference_arms.verify_diagnosis_handoff(stage, names)

        self.assertEqual(receipt["factory"], "failure-as-fuel-preference-cascade")
        self.assertEqual(receipt["round"], 11)
        self.assertEqual(
            [item["name"] for item in receipt["diagnosis_files"]],
            names,
        )
        self.assertTrue(all(item["bytes"] > 0 for item in receipt["diagnosis_files"]))
        self.assertTrue(all(len(item["sha256"]) == 64 for item in receipt["diagnosis_files"]))

    def test_cli_emits_the_same_bounded_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            argv = ["verify-handoff", str(stage)]
            for name in names:
                argv.extend(("--file", name))
            code, out, err = run_cli(argv)

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        receipt = json.loads(out)
        self.assertEqual(receipt["round"], 11)
        self.assertEqual(
            [item["name"] for item in receipt["diagnosis_files"]],
            names,
        )
        self.assertNotIn("root cause", out)

    def test_missing_empty_symlink_and_invalid_utf8_files_fail_closed(self):
        mutations = ("missing", "empty", "whitespace", "symlink", "invalid-utf8")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                stage, names = self.stage(td)
                target = stage / names[0]
                if mutation == "missing":
                    target.unlink()
                elif mutation == "empty":
                    target.write_bytes(b"")
                elif mutation == "whitespace":
                    target.write_text(" \n\t", encoding="utf-8")
                elif mutation == "symlink":
                    target.unlink()
                    real = stage / "not-allowlisted.txt"
                    real.write_text("diagnosis", encoding="utf-8")
                    target.symlink_to(real.name)
                else:
                    target.write_bytes(b"\xff\xfe")

                with self.assertRaises(preference_arms.PreferenceArmsError):
                    preference_arms.verify_diagnosis_handoff(stage, names)

    def test_traversal_duplicates_wrong_round_and_gaps_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            invalid_lists = (
                ["../diagnosis-01-r11.md"],
                [names[0], names[0]],
                ["diagnosis-01-r10.md"],
                [names[0], names[2]],
            )
            for invalid in invalid_lists:
                with (
                    self.subTest(files=invalid),
                    self.assertRaises(preference_arms.PreferenceArmsError),
                ):
                    preference_arms.verify_diagnosis_handoff(stage, invalid)

    def test_cli_reports_a_missing_file_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            stage, names = self.stage(td)
            (stage / names[1]).unlink()
            argv = ["verify-handoff", str(stage)]
            for name in names:
                argv.extend(("--file", name))
            code, out, err = run_cli(argv)

        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("diagnosis handoff verification failed", err)


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
                json.dumps({"id": "solo", "state": {"sim_or_real": "designed"}}) + "\n",
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
        preference_arms.check_pair(record, source_path="memory.jsonl", source_line=1)
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
        cls.prompt = (REPO / "prompts" / "05-failure-as-fuel-preference-cascade.md").read_text()
        cls.workflow = (
            REPO / ".claude" / "skills" / "run-synthetic-factory" / "factory-window.workflow.js"
        ).read_text()
        cls.publisher = (REPO / "pipelines" / "round_txn.py").read_text()

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

    def test_round_publisher_is_the_mandatory_gate(self):
        self.assertIn("validate_preference_arm_gate", self.publisher)
        self.assertIn("preference_arm_gate", self.publisher)
        self.assertIn("require_trusted_isolation=True", self.publisher)

    def test_workflow_stamps_the_two_session_attestation(self):
        self.assertIn(f'meta.isolation="{preference_arms.TWO_SESSION}"', self.workflow)

    def test_workflow_reservation_carries_the_publisher_marker(self):
        self.assertIn(
            f"--preference-isolation {preference_arms.TWO_SESSION}",
            self.workflow,
        )

    def test_content_blind_controller_reserves_before_session_a(self):
        reservation = self.workflow.index("const reservation = await agent")
        session_a = self.workflow.index("const sessionA = await agent")
        self.assertLess(reservation, session_a)
        self.assertIn(
            "outputs/staging/${args.date}/${factory.slug}/r${rr}-",
            self.workflow,
        )
        self.assertNotIn("outputs/raw/${args.date}/.staging", self.workflow)
        invalid_receipt = self.workflow.split("if (!preferenceReservationIsValid", 1)[1].split(
            "const sessionA", 1
        )[0]
        self.assertIn("releaseReservation(factory, round, rr, null)", invalid_receipt)
        session_a_prompt = self.workflow.split("You are Session A", 1)[1].split(
            "You are Session B", 1
        )[0]
        self.assertNotIn("round_txn.py reserve", session_a_prompt)

    def test_workflow_validates_the_exact_diagnosis_only_handoff(self):
        validation = self.workflow.index("preferenceHandoffIsValid(")
        session_b = self.workflow.index("You are Session B")
        self.assertLess(validation, session_b)
        self.assertIn("preferenceDiagnosisFiles(factory.count, rr)", self.workflow)
        self.assertIn("^diagnosis-[0-9]{2}-r[0-9]{2}\\\\.md$", self.workflow)

    def test_read_only_verifier_runs_after_session_a_and_before_session_b(self):
        session_a = self.workflow.index("const sessionA = await agent")
        verification = self.workflow.index("const diagnosisVerification = await agent")
        session_b = self.workflow.index("You are Session B")
        self.assertLess(session_a, verification)
        self.assertLess(verification, session_b)
        self.assertIn("preference_arms.py verify-handoff", self.workflow)
        self.assertIn("preferenceDiagnosisVerificationIsValid(", self.workflow)
        self.assertIn("Number.isSafeInteger(item.bytes)", self.workflow)
        self.assertIn("verifiedDiagnosisFiles", self.workflow)


if __name__ == "__main__":
    unittest.main()
