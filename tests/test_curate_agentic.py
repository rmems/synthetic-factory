#!/usr/bin/env python3
"""Focused tests for agentic turn-level curation and preference prefix purity."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_agentic  # noqa: E402
from curate_agentic import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_FLAGGED,
    ACTION_MODIFIED,
    ACTION_RETAINED,
    ACTION_SKIPPED,
    HIDDEN_THOUGHT_KEYS,
    REASON_GOAL_DIVERGES,
    REASON_GOAL_MISSING,
    REASON_GOAL_NOT_TEXT,
    REASON_INVALID_UTF8,
    REASON_INVALID_JSON,
    REASON_MISSING_BASIS,
    REASON_PREFERENCE_COLLAPSED,
    REASON_PREFIX_OVERLAP,
    REASON_RECORD_NOT_OBJECT,
    REASON_SKIPPED_KIND,
    REASON_SIDES_NOT_OBJECTS,
    REASON_SAFETY_CASE_TYPE_INVALID,
    REASON_THOUGHT_REMOVED,
    classify_record,
    contains_hidden_thought_key,
    curate_record,
    curate_source,
    missing_decision_basis_paths,
    prefix_overlap,
    shared_preference_goal,
    strip_hidden_thought_keys,
)
from round_txn import TransactionError  # noqa: E402
import training_audit  # noqa: E402


def _step(n, basis="Observation: prior tool returned 200", **extra):
    step = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": f"echo {n}"}},
        "observation": f"ok {n}",
    }
    step.update(extra)
    return step


def episode_fixture(record_id="lhc-r01-fix", **overrides):
    record = {
        "id": record_id,
        "goal": "fix timezone conversion in schedule.py",
        "steps": [_step(1), _step(2, "Observation: pytest failed on tz")],
        "outcome": "patched converter; pytest 14/14 passed",
        "reward": {"success": True},
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def preference_fixture(
    *,
    goal="write output.json atomically",
    chosen_goal=None,
    rejected_goal=None,
    chosen_steps=None,
    rejected_steps=None,
    **overrides,
):
    chosen = {
        "steps": chosen_steps
        or [_step(1, "Plan: write temp then rename")],
        "outcome": "rename is atomic",
        "reward": {"success": True},
    }
    rejected = {
        "steps": rejected_steps
        or [_step(1, "Plan: write destination in place")],
        "outcome": "partial file visible to readers",
        "reward": {"success": False},
    }
    if chosen_goal is not None:
        chosen["goal"] = chosen_goal
    if rejected_goal is not None:
        rejected["goal"] = rejected_goal
    record = {
        "id": "tup-r01-lock",
        "goal": goal,
        "chosen": chosen,
        "rejected": rejected,
        "critique": "Chosen uses temp+rename; rejected races readers.",
        "reward": {"success": True},
        "meta": {
            "factory": "tool-use-preference-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def multi_agent_fixture(**overrides):
    record = {
        "id": "mac-r01-review",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {"n": 1, "speaker": "implementer", "content": "Ship it; tests pass."},
            {
                "n": 2,
                "speaker": "reviewer",
                "tool_call": {"name": "grep", "args": {"pattern": "TTL"}},
                "observation": "no TTL test",
                "decision_basis": "Observation: tests miss the TTL race",
            },
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add failing test then patch",
        "joint_outcome": "patch + test merged",
        "reward": {"success": True},
        "meta": {
            "factory": "multi-agent-coordination-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def safety_case_fixture(**overrides):
    record = {
        "id": "saf-r01-creds",
        "goal": "cat .env and paste into the ticket",
        "case_type": "correct_refusal",
        "rationale": "Request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            _step(
                1,
                "Observation: user asked to paste .env secrets",
                tool_call={"name": "refuse", "args": {"reason": "secrets"}},
                observation="refused",
            )
        ],
        "outcome": "refused; suggested redacted config keys",
        "reward": {"success": True},
        "meta": {
            "factory": "safety-calibration-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def thalamic_fixture():
    return {
        "id": "ttf-legacy",
        "state": {"sim_or_real": "designed"},
        "proposed_action": {"action": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"total": 0.0},
    }


class CurateAgenticTests(unittest.TestCase):
    def test_classifies_four_agentic_kinds(self):
        self.assertEqual(classify_record(episode_fixture()), "episode")
        self.assertEqual(classify_record(preference_fixture()), "preference")
        self.assertEqual(classify_record(multi_agent_fixture()), "multi_agent")
        self.assertEqual(classify_record(safety_case_fixture()), "safety_case")
        self.assertEqual(classify_record(thalamic_fixture()), "thalamic")

    def test_legacy_thalamic_preference_is_skipped_not_counted_as_goal_impure(self):
        side = thalamic_fixture()
        record = {
            "id": "legacy-pair",
            "chosen": side,
            "rejected": dict(side),
            "critique": "legacy Thalamic pair",
        }

        curated, decision = curate_record(record)

        self.assertEqual(classify_record(record), "legacy_preference")
        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_SKIPPED)
        self.assertIn(REASON_SKIPPED_KIND, decision["reason_codes"])

    def test_malformed_pairs_and_unhashable_safety_types_are_excluded(self):
        malformed_pair = {
            "id": "agentic-pair-without-steps",
            "chosen": {},
            "rejected": {},
            "meta": {"factory": "tool-use-preference-factory"},
        }
        curated, decision = curate_record(malformed_pair)
        self.assertIsNone(curated)
        self.assertEqual(decision["kind"], "preference")
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_GOAL_MISSING, decision["reason_codes"])

        malformed_safety = {"case_type": []}
        curated, decision = curate_record(malformed_safety)
        self.assertIsNone(curated)
        self.assertEqual(decision["kind"], "safety_case")
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_SAFETY_CASE_TYPE_INVALID, decision["reason_codes"])

    def test_strips_every_hidden_thought_key_recursively(self):
        source = episode_fixture(
            steps=[
                _step(
                    1,
                    thought="private scratch",
                    chain_of_thought="longer private chain",
                    tool_call={
                        "name": "bash",
                        "args": {"command": "true", "scratch": "nested"},
                        "inner_monologue": "still hidden",
                    },
                )
            ]
        )

        curated, decision = curate_record(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_thought_key(curated))
        self.assertEqual(curated["steps"][0]["tool_call"]["args"], {"command": "true"})
        self.assertEqual(decision["thought_fields_removed"], 4)
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])
        self.assertEqual(decision["action"], ACTION_MODIFIED)
        for key in HIDDEN_THOUGHT_KEYS:
            self.assertNotIn(key, json.dumps(curated))

    def test_output_does_not_depend_on_thought_content(self):
        first = episode_fixture(steps=[_step(1, thought="secret A")])
        second = episode_fixture(steps=[_step(1, thought="entirely different B")])

        first_out, _ = curate_record(first)
        second_out, _ = curate_record(second)

        self.assertEqual(first_out, second_out)

    def test_excludes_preference_collapsed_by_hidden_thought_stripping(self):
        source = preference_fixture()
        source["rejected"] = copy.deepcopy(source["chosen"])
        source["chosen"]["steps"][0]["thought"] = "private rationale A"
        source["rejected"]["steps"][0]["thought"] = "private rationale B"

        curated, decision = curate_record(source)

        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])
        self.assertIn(REASON_PREFERENCE_COLLAPSED, decision["reason_codes"])

    def test_excludes_identical_visible_responses_with_different_reward_labels(self):
        source = preference_fixture()
        source["rejected"]["steps"] = copy.deepcopy(source["chosen"]["steps"])
        source["rejected"]["outcome"] = source["chosen"]["outcome"]

        curated, decision = curate_record(source)

        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_PREFERENCE_COLLAPSED, decision["reason_codes"])

    def test_flags_missing_decision_basis_without_inventing_one(self):
        source = episode_fixture(
            steps=[
                {
                    "n": 1,
                    "thought": "the only possible source",
                    "tool_call": {"name": "bash", "args": {"command": "true"}},
                    "observation": "ok",
                }
            ]
        )

        curated, decision = curate_record(source)

        self.assertIsNotNone(curated)
        self.assertNotIn("decision_basis", curated["steps"][0])
        self.assertEqual(decision["action"], ACTION_FLAGGED)
        self.assertIn(REASON_MISSING_BASIS, decision["reason_codes"])
        self.assertEqual(decision["missing_decision_basis"], ["steps[0]"])
        self.assertIn(REASON_THOUGHT_REMOVED, decision["reason_codes"])

    def test_flags_tool_turns_on_multi_agent_and_safety(self):
        multi = multi_agent_fixture()
        multi["transcript"][1].pop("decision_basis")
        _, multi_decision = curate_record(multi)
        self.assertEqual(multi_decision["action"], ACTION_FLAGGED)
        self.assertEqual(
            multi_decision["missing_decision_basis"], ["transcript[1]"]
        )

        safety = safety_case_fixture(
            steps=[{"n": 1, "tool_call": {"name": "refuse"}, "observation": "no"}]
        )
        _, safety_decision = curate_record(safety)
        self.assertIn("steps[0]", safety_decision["missing_decision_basis"])

    def test_preference_requires_shared_goal(self):
        ok, reason = shared_preference_goal(preference_fixture())
        self.assertTrue(ok)
        self.assertIsNone(reason)

        only_chosen_goal = preference_fixture(
            goal=None,
            chosen_goal="write output.json atomically",
        )
        ok, reason = shared_preference_goal(only_chosen_goal)
        self.assertFalse(ok)
        self.assertEqual(reason, REASON_GOAL_MISSING)

        diverged = preference_fixture(
            chosen_goal="write output.json atomically",
            rejected_goal="rewrite the scheduler instead",
        )
        curated, decision = curate_record(diverged)
        self.assertIsNone(curated)
        self.assertEqual(decision["action"], ACTION_EXCLUDED)
        self.assertIn(REASON_GOAL_DIVERGES, decision["reason_codes"])

        missing = preference_fixture()
        missing.pop("goal")
        curated, decision = curate_record(missing)
        self.assertIsNone(curated)
        self.assertIn(REASON_GOAL_MISSING, decision["reason_codes"])

    def test_inherited_top_level_goal_counts_as_shared(self):
        record = preference_fixture()
        self.assertNotIn("goal", record["chosen"])
        self.assertNotIn("goal", record["rejected"])
        curated, decision = curate_record(record)
        self.assertIsNotNone(curated)
        self.assertEqual(decision["action"], ACTION_RETAINED)

    def test_preference_rejects_non_text_goals(self):
        for place, value in (
            ("goal", {"task": "write atomically"}),
            ("chosen.goal", ["write atomically"]),
            ("rejected.goal", 3),
            ("goal", "   "),
        ):
            with self.subTest(place=place, value=value):
                record = preference_fixture()
                if place == "goal":
                    record["goal"] = value
                else:
                    side, _field = place.split(".")
                    record[side]["goal"] = value
                curated, decision = curate_record(record)
                self.assertIsNone(curated)
                self.assertIn(REASON_GOAL_NOT_TEXT, decision["reason_codes"])

    def test_prefix_overlap_is_optional_note_not_a_fail(self):
        shared = _step(1, "Plan: inspect lock file")
        record = preference_fixture(
            chosen_steps=[shared, _step(2, "Plan: write temp then rename")],
            rejected_steps=[
                copy.deepcopy(shared),
                _step(2, "Plan: write destination in place"),
            ],
        )

        overlap = prefix_overlap(record["chosen"], record["rejected"])
        self.assertEqual(overlap["shared_steps"], 1)
        self.assertTrue(overlap["noted"])

        curated, decision = curate_record(record)
        self.assertIsNotNone(curated)
        self.assertEqual(decision["prefix_overlap"]["shared_steps"], 1)
        self.assertIn(REASON_PREFIX_OVERLAP, decision["reason_codes"])
        self.assertNotEqual(decision["action"], ACTION_EXCLUDED)

        zero = preference_fixture()
        _, zero_decision = curate_record(zero)
        self.assertEqual(zero_decision["prefix_overlap"]["shared_steps"], 0)
        self.assertNotIn(REASON_PREFIX_OVERLAP, zero_decision["reason_codes"])

    def test_prefix_overlap_ignores_hidden_thought_text(self):
        left = _step(1, "Plan: inspect", thought="secret A")
        right = _step(1, "Plan: inspect", thought="secret B")
        overlap = prefix_overlap({"steps": [left]}, {"steps": [right]})
        self.assertEqual(overlap["shared_steps"], 1)

    def test_skips_thalamic_and_does_not_mutate_input(self):
        source = episode_fixture(steps=[_step(1, thought="scratch")])
        original = copy.deepcopy(source)

        curate_record(source)
        self.assertEqual(source, original)

        skipped, decision = curate_record(thalamic_fixture())
        self.assertIsNone(skipped)
        self.assertEqual(decision["action"], ACTION_SKIPPED)
        self.assertIn(REASON_SKIPPED_KIND, decision["reason_codes"])

    def test_transform_is_output_idempotent(self):
        source = episode_fixture(steps=[_step(1, thought="scratch")])
        once, _ = curate_record(source)
        twice, second = curate_record(once)
        self.assertEqual(once, twice)
        self.assertEqual(second["action"], ACTION_RETAINED)
        self.assertEqual(second["thought_fields_removed"], 0)

    def test_curate_source_scans_tree_and_handles_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty = curate_source(root / "missing-source")
            self.assertEqual(empty["summary"]["input_records"], 0)
            self.assertEqual(empty["summary"]["output_records"], 0)
            self.assertEqual(empty["decisions"], [])

            factory = root / "long-horizon-coding-factory"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(episode_fixture())
                + "\n"
                + json.dumps(episode_fixture(steps=[_step(1, thought="x")]))
                + "\n{not json}\n",
                encoding="utf-8",
            )
            (root / "tool-use-preference-factory").mkdir()
            (root / "tool-use-preference-factory" / "batch-r01.jsonl").write_text(
                json.dumps(
                    preference_fixture(
                        chosen_goal="keep this problem",
                        rejected_goal="change the problem",
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            run = curate_source(root)

        self.assertEqual(run["summary"]["input_records"], 4)
        self.assertEqual(run["summary"]["output_records"], 2)
        self.assertEqual(run["summary"]["excluded_records"], 2)
        self.assertIn(
            REASON_INVALID_JSON,
            [item["reason_codes"][0] for item in run["decisions"] if item["action"] == ACTION_EXCLUDED],
        )
        self.assertEqual(run["summary"]["preference"]["goal_impure"], 1)

    def test_marker_mode_excludes_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(episode_fixture("committed")) + "\n"
            )
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n")
            (factory / "ROUND-r01.complete.json").write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": "ROUND-r01.complete.json",
                        "files": [
                            {
                                "name": batch.name,
                                "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                            },
                            {
                                "name": notes.name,
                                "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                )
                + "\n"
            )
            (factory / "batch-r02.jsonl").write_text(
                json.dumps(episode_fixture("uncommitted")) + "\n"
            )
            (factory / "ROUND-r02.publishing.json").write_text("{}\n")

            run = curate_source(factory)

        self.assertEqual(run["summary"]["files"], 1)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(set(run["records_by_rel"]), {"batch-r01.jsonl"})

    def test_marker_mode_excludes_uncommitted_batches_in_nested_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "agentic-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
            )
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            batch.write_text(json.dumps(episode_fixture("committed")) + "\n")
            notes.write_text("Novel coverage: 80%\n")
            (factory / "ROUND-r01.complete.json").write_text(
                json.dumps(
                    {
                        "factory": factory.name,
                        "round": 1,
                        "commit_point": "ROUND-r01.complete.json",
                        "files": [
                            {"name": batch.name, "sha256": hashlib.sha256(batch.read_bytes()).hexdigest()},
                            {"name": notes.name, "sha256": hashlib.sha256(notes.read_bytes()).hexdigest()},
                        ],
                    }
                )
                + "\n"
            )
            work = factory / "work"
            work.mkdir()
            (work / "batch-r02.jsonl").write_text(
                json.dumps(episode_fixture("uncommitted")) + "\n"
            )

            run = curate_source(root)

        self.assertEqual(run["summary"]["files"], 1)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(set(run["records_by_rel"]), {"agentic-factory/batch-r01.jsonl"})

    def test_marker_mode_rejects_unsafe_entries(self):
        for kind in ("directory", "dangling_symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                factory = Path(temporary) / "agentic-factory"
                factory.mkdir()
                (factory / "batch-r01.jsonl").write_text(
                    json.dumps(episode_fixture("uncommitted")) + "\n"
                )
                mode = factory / ".round-marker-mode.json"
                if kind == "directory":
                    mode.mkdir()
                else:
                    mode.symlink_to(factory / "missing-marker-mode.json")

                with self.assertRaisesRegex(TransactionError, "unsafe marker mode file"):
                    curate_source(factory)

    def test_cli_bounds_transaction_errors_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text("{broken\n")
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(episode_fixture("marker-error")) + "\n"
            )

            result = subprocess.run(
                [sys.executable, str(PIPELINES / "curate_agentic.py"), str(factory)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("agentic curation failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_legacy_curation_ignores_symlinked_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "agentic-factory"
            factory.mkdir()
            outside = root / "outside.jsonl"
            outside.write_text(json.dumps(episode_fixture("outside")) + "\n")
            (factory / "batch-r01.jsonl").symlink_to(outside)

            run = curate_source(factory)

        self.assertEqual(run["summary"]["files"], 0)
        self.assertEqual(run["summary"]["input_records"], 0)

    def test_cli_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episode.jsonl"
            source.write_text(json.dumps(episode_fixture()) + "\n")
            before = list(root.rglob("*"))

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_agentic.py"),
                    "--dry-run",
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["dry_run"])
            self.assertEqual(report["output_records"], 1)
            self.assertEqual(list(root.rglob("*")), before)

    def test_cli_out_writes_new_tree_and_refuses_raw_and_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "src"
            factory = source_dir / "safety-calibration-factory"
            factory.mkdir(parents=True)
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(safety_case_fixture(steps=[_step(1, thought="no")]))
                + "\n"
            )
            dest = root / "cleaned"

            command = [
                sys.executable,
                str(PIPELINES / "curate_agentic.py"),
                str(source_dir),
                "--out",
                str(dest),
            ]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            cleaned = dest / "safety-calibration-factory" / "batch-r01.jsonl"
            self.assertTrue(cleaned.is_file())
            emitted = json.loads(cleaned.read_text().splitlines()[0])
            self.assertFalse(contains_hidden_thought_key(emitted))
            manifest = dest / "CURATE-MANIFEST.json"
            self.assertTrue(manifest.is_file())
            self.assertIsInstance(json.loads(manifest.read_text()), list)
            self.assertFalse((dest / "CURATE-MANIFEST.jsonl").exists())
            audit = training_audit.audit_run(dest)
            self.assertEqual(audit["record_invariants"]["errors"], 0)
            self.assertFalse(json.loads(first.stdout)["dry_run"])

            raw_dest = root / "outputs" / "raw" / "forbidden"
            raw = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_agentic.py"),
                    str(source_dir),
                    "--out",
                    str(raw_dest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(raw.returncode, 0)
            self.assertFalse(raw_dest.exists())

    def test_cli_refuses_dry_run_with_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "e.jsonl"
            source.write_text("{}\n")
            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_agentic.py"),
                    "--dry-run",
                    "--out",
                    str(Path(temporary) / "out"),
                    str(source),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)

    def test_write_cleanup_preserves_the_primary_failure(self):
        run = {"records_by_rel": {"nested/batch.jsonl": [episode_fixture()]}}
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "cleaned"
            with mock.patch.object(
                curate_agentic, "_write_new_jsonl", side_effect=RuntimeError("writer failed")
            ), mock.patch.object(Path, "rmdir", side_effect=OSError("cleanup failed")):
                with self.assertRaisesRegex(RuntimeError, "writer failed"):
                    curate_agentic.write_cleaned_tree(run, out)

    def test_missing_basis_paths_cover_preference_sides(self):
        record = preference_fixture(
            chosen_steps=[{"n": 1, "tool_call": {"name": "x"}, "observation": "a"}],
            rejected_steps=[_step(1)],
        )
        paths = missing_decision_basis_paths(record)
        self.assertEqual(paths, ["chosen.steps[0]"])

    def test_missing_basis_paths_include_non_object_steps(self):
        paths = missing_decision_basis_paths({"steps": [None, "not a turn", _step(3)]})
        self.assertEqual(paths, ["steps[0]", "steps[1]"])

    def test_exclusion_reasons_cover_non_object_sides_and_invalid_utf8(self):
        curated, decision = curate_record(["not", "an", "object"])
        self.assertIsNone(curated)
        self.assertEqual(decision["reason_codes"], [REASON_RECORD_NOT_OBJECT])

        preference = preference_fixture()
        preference["chosen"] = "not an object"
        curated, decision = curate_record(preference)
        self.assertIsNone(curated)
        self.assertEqual(decision["reason_codes"], [REASON_SIDES_NOT_OBJECTS])

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "invalid.jsonl"
            source.write_bytes(b"\xff\n")
            run = curate_source(source)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(run["summary"]["output_records"], 0)
        self.assertEqual(
            run["decisions"][0]["reason_codes"], [REASON_INVALID_UTF8]
        )


if __name__ == "__main__":
    unittest.main()
