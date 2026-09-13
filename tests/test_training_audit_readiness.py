#!/usr/bin/env python3
"""training_audit.py's corpus-level training_ready verdict and blockers.

A clean corpus reports training_ready; a gate error, reward-arithmetic
mismatch, non-standard JSON numeric constant, invalid UTF-8, duplicate id,
or legacy meta.id/thought warning must each surface in the report's
blockers/metrics without raising.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from training_audit_test_helpers import (  # noqa: E402
    REPO,
    commit_marker_batch,
    thalamic,
    write,
)

import training_audit  # noqa: E402


class FacadeSeamReached(Exception):
    """Sentinel proving a compatibility facade seam was resolved at call time."""


class TrainingAuditReadinessReport(unittest.TestCase):
    def assert_facade_seam_reached(self, seam, action):
        """Require one facade patch to be resolved by the supplied action."""
        message = f"{seam} reached"
        with mock.patch.object(
            training_audit,
            seam,
            side_effect=FacadeSeamReached(message),
        ):
            with self.assertRaisesRegex(FacadeSeamReached, message):
                action()

    def test_pinned_reader_resolves_facade_opener_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = Path("batch-r01.jsonl")
            (root / member).write_bytes(b'{}\n')
            self.assert_facade_seam_reached(
                "_open_audit_descriptor",
                lambda: training_audit._read_pinned_member(root, member),
            )

    def test_pinned_reader_resolves_facade_descriptor_reader_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = Path("batch-r01.jsonl")
            (root / member).write_bytes(b'{}\n')
            self.assert_facade_seam_reached(
                "_read_regular_audit_descriptor",
                lambda: training_audit._read_pinned_member(root, member),
            )

    def test_committed_digest_resolves_facade_marker_index_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            marker_root = Path(td) / "factory"
            marker_root.mkdir()
            self.assert_facade_seam_reached(
                "_marker_digest_index",
                lambda: training_audit._require_committed_digest(
                    b'{}\n', Path("batch-r01.jsonl"), marker_root, {}
                ),
            )

    def test_member_enumerator_resolves_facade_scanner_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assert_facade_seam_reached(
                "_scanned_audit_entries",
                lambda: training_audit._enumerated_run_members(root),
            )

    def test_member_enumerator_resolves_facade_classifier_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "batch-r01.jsonl").write_bytes(b'{}\n')
            self.assert_facade_seam_reached(
                "_classified_audit_entry",
                lambda: training_audit._enumerated_run_members(root),
            )

    def test_membership_resolves_facade_enumerator_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assert_facade_seam_reached(
                "_enumerated_run_members",
                lambda: training_audit._run_membership(root),
            )

    def test_member_capture_resolves_facade_digest_check_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = Path("batch-r01.jsonl")
            (root / member).write_bytes(b'{}\n')
            self.assert_facade_seam_reached(
                "_require_committed_digest",
                lambda: training_audit._capture_run_member(
                    root, member, frozenset({member}), {}
                ),
            )

    def test_snapshot_capture_resolves_facade_membership_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assert_facade_seam_reached(
                "_run_membership",
                lambda: training_audit._captured_run_files(root),
            )

    def test_snapshot_capture_resolves_facade_member_capture_at_call_time(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            member = root / "batch-r01.jsonl"
            member.write_bytes(b'{}\n')
            self.assert_facade_seam_reached(
                "_capture_run_member",
                lambda: training_audit._captured_run_files(root),
            )

    def test_snapshot_boundary_captures_exact_visible_member_bytes(self):
        """The reusable snapshot boundary preserves the bytes it authenticates."""

        try:
            import training_audit_snapshot
        except ModuleNotFoundError as exc:
            self.fail(f"training-audit snapshot boundary is unavailable: {exc}")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            relative = Path("thalamic-trajectory-factory/batch-r01.jsonl")
            payload = b'{"id":"first"}\r\n{"id":"second"}\n'
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(payload)

            captured = training_audit_snapshot.capture_run_files(root)

        self.assertEqual(captured, [(relative, payload)])

    def test_jsonl_framing_preserves_literal_unicode_line_separators(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = thalamic("unicode-separators")
            first["state"]["domain"] = "line\u2028separator\u2029paragraph"
            records = [first, thalamic("plain")]
            path = root / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n" for record in records
                ),
                encoding="utf-8",
            )
            self.assertGreater(len(path.read_text(encoding="utf-8").splitlines()), 2)

            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["records"], 2)
        self.assertEqual(report["record_invariants"]["errors"], 0)
        self.assertTrue(report["training_ready"], report["blockers"])

    def test_non_regular_jsonl_members_fail_the_audit_closed(self):
        """Codex #97 P2: a member that cannot be captured must not be skipped.

        Silently omitting a broken symlink, a directory, or a fifo named
        ``*.jsonl`` leaves the file count and readiness unchanged, so
        ``training_audit --strict`` would certify only a subset of the
        apparent corpus.
        """

        for member in ("broken_symlink", "directory", "fifo"):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                factory = root / "thalamic-trajectory-factory"
                write(factory / "batch-r01.jsonl", [thalamic("clean-1")])
                self.assertTrue(training_audit.audit_run(root)["training_ready"])

                intruder = factory / "ignored.jsonl"
                if member == "broken_symlink":
                    intruder.symlink_to(root / "missing-target.jsonl")
                elif member == "directory":
                    intruder.mkdir()
                else:
                    os.mkfifo(intruder)

                with self.assertRaises(ValueError):
                    training_audit.audit_run(root)

    def test_member_added_during_capture_fails_the_audit_closed(self):
        """Standalone readiness must describe the final captured membership."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            factory = root / "thalamic-trajectory-factory"
            write(factory / "batch-r01.jsonl", [thalamic("captured")])
            real_read = training_audit._read_pinned_member
            added = False

            def read_then_add(run_dir, relative):
                nonlocal added
                payload = real_read(run_dir, relative)
                if not added:
                    added = True
                    write(factory / "late.jsonl", [thalamic("late")])
                return payload

            with mock.patch.object(
                training_audit,
                "_read_pinned_member",
                side_effect=read_then_add,
            ):
                with self.assertRaisesRegex(ValueError, "member set changed"):
                    training_audit.audit_run(root)

    def test_pinned_member_read_refuses_an_aliased_parent_directory(self):
        """Every parent component is descriptor-pinned with no symlink following."""

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            root = Path(td)
            outside_file = Path(outside) / "batch-r01.jsonl"
            outside_file.write_bytes(b'{}\n')
            (root / "alias").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "cannot be captured"):
                training_audit._read_pinned_member(
                    root,
                    Path("alias/batch-r01.jsonl"),
                )

    def test_authenticated_snapshot_rejects_unsafe_paths_and_non_bytes(self):
        """Exporter snapshots keep strict relative-path and byte-payload types."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsafe_paths = ("", "/absolute.jsonl", "../escape.jsonl", "a/../b.jsonl")
            for path in unsafe_paths:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    training_audit.audit_run(root, snapshot={path: b'{}\n'})

            with self.assertRaisesRegex(TypeError, "must be bytes"):
                training_audit.audit_run(
                    root,
                    snapshot={"factory/batch-r01.jsonl": "{}\n"},
                )

    def test_overflowed_json_number_is_a_record_parse_error(self):
        """The strict audit and export must reject the same JSON numbers."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "thalamic-trajectory-factory" / "batch-r01.jsonl"
            path.parent.mkdir(parents=True)
            document = json.dumps(thalamic("overflow"))
            path.write_text(document[:-1] + ',"probe":1e400}\n', encoding="utf-8")

            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["record_invariants"]["errors"], 1)
        self.assertTrue(
            any(
                "JSON parse error" in item
                for item in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"]["error_examples"],
        )

    def test_a_symlinked_directory_in_the_run_tree_fails_the_audit_closed(self):
        """Codex #97 P2: an aliased subtree must fail the audit, not vanish.

        ``Path.rglob("*.jsonl")`` neither returns a directory symlink whose
        name does not end in ``.jsonl`` nor descends through it, so JSONL
        visible only through that alias would silently drop out of a
        standalone audit while ``--strict`` still certified the remaining
        subset as the whole corpus.
        """

        with tempfile.TemporaryDirectory() as td, (
            tempfile.TemporaryDirectory()
        ) as outside:
            root = Path(td)
            factory = root / "thalamic-trajectory-factory"
            write(factory / "batch-r01.jsonl", [thalamic("clean-1")])
            self.assertTrue(training_audit.audit_run(root)["training_ready"])

            alias_target = Path(outside)
            (alias_target / "invalid.jsonl").write_text(
                "not json\n", encoding="utf-8"
            )
            (root / "aliased-subtree").symlink_to(
                alias_target, target_is_directory=True
            )

            with self.assertRaisesRegex(ValueError, "symlink alias"):
                training_audit.audit_run(root)

    def test_swapped_committed_member_bytes_fail_the_audit_closed(self):
        """Codex #97 P2: audited bytes must match the committed round digest.

        Visibility digest-checks the committed set when it is resolved, and
        the capture separately binds the bytes it actually read to the digest
        the round committed, so a member swapped for another regular file
        under a committed coordinate can never be certified.
        """
        import training_audit as audit_module

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            factory = root / "thalamic-trajectory-factory"
            batch = factory / "batch-r01.jsonl"
            write(batch, [thalamic("committed-1")])
            commit_marker_batch(factory, batch)
            self.assertTrue(training_audit.audit_run(root)["training_ready"])

            # The capture-time binding itself: bytes that disagree with the
            # committed digest are refused even after visibility resolved.
            digest_cache = {}
            with self.assertRaisesRegex(ValueError, "committed round digest"):
                audit_module._require_committed_digest(
                    b"not the committed bytes\n",
                    Path("batch-r01.jsonl"),
                    factory,
                    digest_cache,
                )
            audit_module._require_committed_digest(
                batch.read_bytes(), Path("batch-r01.jsonl"), factory, digest_cache
            )

            write(batch, [thalamic("swapped-1")])
            with self.assertRaises(
                (ValueError, audit_module.TransactionError)
            ):
                training_audit.audit_run(root)

    def test_clean_corpus_is_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [thalamic("clean-1")])
            report = training_audit.audit_run(root)

        self.assertTrue(report["training_ready"], report["blockers"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["identity"]["coverage_pct"], 100.0)
        self.assertEqual(report["provenance"]["canonical_pct"], 100.0)
        self.assertEqual(report["rewards"]["unique_shapes"], 1)
        self.assertGreater(report["totals"]["approx_tokens"], 0)

    def test_empty_corpus_is_not_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            report = training_audit.audit_run(Path(td))

        self.assertFalse(report["training_ready"])
        self.assertIn(
            "corpus contains 0 eligible training records",
            report["blockers"],
        )

    def test_marker_mode_hides_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            factory = root / "agentic-factory"
            committed = factory / "batch-r01.jsonl"
            write(committed, [thalamic("committed")])
            commit_marker_batch(factory, committed)
            (factory / "batch-r02.jsonl").write_text("{not json}\n")
            (factory / "ROUND-r02.publishing.json").write_text("{}\n")
            report = training_audit.audit_run(root)

        self.assertEqual(report["totals"]["files"], 1)
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertTrue(report["training_ready"], report["blockers"])

    def test_cli_bounds_unsafe_marker_mode_transaction_error(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "thalamic-trajectory-factory"
            write(factory / "batch-r01.jsonl", [thalamic("unsafe-marker")])
            (factory / ".round-marker-mode.json").mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "pipelines" / "training_audit.py"),
                    str(factory),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("training_audit failed: unsafe marker mode file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_suffixed_snapshot_root_keeps_factory_directories_distinct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "pre-window-factory"
            write(
                root / "thalamic-trajectory-factory" / "batch-r01.jsonl",
                [thalamic("clean-1")],
            )
            write(
                root / "safety-calibration-factory" / "batch-r01.jsonl",
                [thalamic("clean-2")],
            )
            report = training_audit.audit_run(root)

        self.assertEqual(
            set(report["factories"]),
            {"safety-calibration-factory", "thalamic-trajectory-factory"},
        )
        self.assertNotIn("pre-window-factory", report["factories"])

    def test_off_registry_factory_root_keeps_nested_legacy_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "custom-experiment-factory"
            write(root / "archive" / "batch-r01.jsonl", [thalamic("clean-1")])
            report = training_audit.audit_run(root)

        self.assertEqual(set(report["factories"]), {"custom-experiment-factory"})
        self.assertNotIn("archive", report["factories"])

    def test_marked_gate_errors_are_counted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrong = thalamic("gate-err-1", decision="MODIFY")
            wrong["safety_decision"]["correctness"] = "incorrect"
            wrong["meta"]["supervisor_error_type"] = "wrong-modify"
            clean = thalamic("gate-ok-1")
            write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [wrong, clean])
            report = training_audit.audit_run(root)
            markdown = training_audit.render_markdown(report)

        self.assertEqual(report["gate_errors"]["marked"], 1)
        self.assertEqual(report["gate_errors"]["by_type"], {"wrong-modify": 1})
        self.assertTrue(report["gate_errors"]["examples"])
        self.assertIn("Intentional gate-error records", markdown)

    def test_legacy_meta_id_and_thought_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            episode = {
                "goal": "legacy",
                "steps": [
                    {
                        "thought": "scratch",
                        "tool_call": {"name": "rg", "args": {}},
                        "observation": "none",
                    }
                ],
                "outcome": "done",
                "reward": {"success": True},
                "meta": {"id": "legacy-meta"},
            }
            write(root / "coding" / "legacy.jsonl", [episode])
            report = training_audit.audit_run(root)

        self.assertEqual(report["identity"]["coverage_pct"], 0.0)
        self.assertEqual(report["identity"]["legacy_meta_fallback_records"], 1)
        self.assertEqual(report["episodes"]["legacy_thought_only_steps"], 1)
        self.assertFalse(report["training_ready"])

    def test_reports_preference_and_bridge_training_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chosen = thalamic("chosen", decision="MODIFY")
            rejected = thalamic("rejected", decision="ACCEPT")
            rejected["state"]["domain"] = "changed-problem"
            pair = {
                "id": "pref-1",
                "chosen": chosen,
                "rejected": rejected,
                "critique": "same proposal but changed state",
            }
            bridge_trajectory = thalamic("bridge-inner", provenance="real")
            bridge = {
                "id": "bridge-1",
                "spike_events": [
                    {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.5},
                    {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.4},
                ],
                "language_view": {"trajectory": bridge_trajectory},
            }
            write(root / "failure-as-fuel-preference-cascade" / "batch-r01.jsonl", [pair])
            write(root / "neuromorphic-event-language-bridge" / "batch-r01.jsonl", [bridge])

            report = training_audit.audit_run(root)
            markdown = training_audit.render_markdown(report)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["preferences"]["pairs"], 1)
        self.assertEqual(report["preferences"]["same_context"], 0)
        self.assertEqual(report["preferences"]["chosen_decisions"], {"MODIFY": 1})
        self.assertEqual(report["bridge"].get("sorted_pairs", 0), 0)
        self.assertEqual(report["bridge"]["unsorted_pairs"], 1)
        self.assertEqual(report["provenance"]["counts"]["non_training"], 1)
        self.assertIn("preference pairs", " ".join(report["blockers"]))
        self.assertIn("bridge pairs", " ".join(report["blockers"]))
        self.assertIn("Training blockers", markdown)

    def test_exact_duplicate_and_global_id_duplicate_are_distinct_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = thalamic("dup")
            write(root / "a" / "one.jsonl", [record])
            write(root / "b" / "two.jsonl", [record])
            report = training_audit.audit_run(root)

        self.assertEqual(len(report["identity"]["duplicates"]), 1)
        self.assertEqual(len(report["exact_duplicates"]), 1)
        self.assertFalse(report["training_ready"])

    def test_reward_arithmetic_error_blocks_training(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = thalamic("bad-reward")
            record["reward_components"]["total"] = 99.0
            write(root / "f" / "bad.jsonl", [record])
            report = training_audit.audit_run(root)

        self.assertEqual(report["record_invariants"]["errors"], 1)
        self.assertIn("recomputed", report["record_invariants"]["error_examples"][0])
        self.assertFalse(report["training_ready"])

    def test_nonstandard_json_numeric_constants_block_training(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                record = thalamic("nonstandard-number")
                record["state"]["measurement"] = value
                write(root / "thalamic-trajectory-factory" / "batch-r01.jsonl", [record])

                report = training_audit.audit_run(root)

                self.assertFalse(report["training_ready"])
                self.assertTrue(
                    any(
                        "non-standard JSON numeric constant" in error
                        for error in report["record_invariants"]["error_examples"]
                    ),
                    report["record_invariants"],
                )

    def test_invalid_utf8_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "f" / "bad.jsonl"
            path.parent.mkdir(parents=True)
            valid = json.dumps(thalamic("valid-after-bad")).encode("utf-8")
            path.write_bytes(b'{"id":"bad-\xff"}\n' + valid + b"\n")
            report = training_audit.audit_run(root)

        self.assertFalse(report["training_ready"])
        self.assertEqual(report["totals"]["records"], 1)
        self.assertEqual(report["totals"]["eligible_records"], 1)
        self.assertTrue(
            any(
                "bad.jsonl:1: invalid UTF-8" in item
                for item in report["record_invariants"]["error_examples"]
            ),
            report["record_invariants"],
        )


if __name__ == "__main__":
    unittest.main()
