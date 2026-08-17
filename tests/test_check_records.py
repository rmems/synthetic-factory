#!/usr/bin/env python3
"""Tests for pipelines/check_records.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CHECKER = PIPELINES / "check_records.py"

sys.path.insert(0, str(PIPELINES))
import check_records  # noqa: E402


def _thalamic(**overrides):
    rec = {
        "state": {"sim_or_real": "designed", "domain": "test"},
        "proposed_action": {"action_type": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "ok"},
        "executed_action": {"action_type": "noop"},
        "future_outcome": {"success": "full"},
        "reward_components": {
            "task_progress": 0.4,
            "safety": 0.6,
            "total": 1.0,
        },
        "meta": {"id": "t-001"},
    }
    rec.update(overrides)
    return rec


def _write_jsonl(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def _run_dir(records, name="batch.jsonl"):
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / name
    _write_jsonl(path, records)
    return tmp, Path(tmp.name)


def _cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=str(cwd or REPO),
        capture_output=True,
        text=True,
    )


class TestCheckRecords(unittest.TestCase):
    def test_unsorted_spikes_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "bad-spikes.jsonl"
            dest.write_text((FIXTURES / "bad-spikes.jsonl").read_text())
            result = check_records.check_run(td)
        self.assertTrue(result["errors"], result)
        blob = "\n".join(result["errors"])
        self.assertIn("bad-spikes.jsonl:1", blob)
        self.assertRegex(blob, r"not globally non-decreasing|out of order")
        self.assertIn("t_rel_ms", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_reward_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "bad-reward.jsonl"
            dest.write_text((FIXTURES / "bad-reward.jsonl").read_text())
            result = check_records.check_run(td)
        self.assertTrue(result["errors"], result)
        blob = "\n".join(result["errors"])
        self.assertIn("bad-reward.jsonl:1", blob)
        self.assertIn("reward_components", blob)
        self.assertRegex(blob, r"recomputed|mismatch")
        self.assertEqual(result["exit_code"], 1)

    def test_unknown_shape_is_error(self):
        tmp, run_dir = _run_dir([{"hello": "world", "not": "a factory record"}])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("unrecognized record shape", blob)
        self.assertIn("batch.jsonl:1", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_duplicate_meta_id_is_error(self):
        a = _thalamic(meta={"id": "dup-1"})
        b = _thalamic(meta={"id": "dup-1"})
        b["state"] = {"sim_or_real": "designed", "domain": "other"}
        tmp, run_dir = _run_dir([a, b])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("duplicate meta.id", blob)
        self.assertIn("dup-1", blob)
        self.assertIn("batch.jsonl:2", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_missing_sim_or_real_is_warning_not_error(self):
        rec = _thalamic()
        rec["state"] = {"domain": "no-provenance"}
        rec["meta"] = {"id": "no-sim"}
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir)
            strict = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertTrue(result["warnings"], result)
        self.assertIn("sim_or_real", "\n".join(result["warnings"]))
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(strict["exit_code"], 1)

    def test_interval_and_string_total_are_warnings_only(self):
        interval = _thalamic(
            reward_components={"task_progress": 0.2, "safety": 0.3, "total": [0.1, 0.9]},
            meta={"id": "interval"},
        )
        as_str = _thalamic(
            reward_components={"task_progress": 0.2, "safety": 0.3, "total": "0.5 ± 0.1"},
            meta={"id": "string-total"},
        )
        tmp, run_dir = _run_dir([interval, as_str])
        with tmp:
            result = check_records.check_run(run_dir)
        self.assertFalse(result["errors"], result)
        warns = "\n".join(result["warnings"])
        self.assertGreaterEqual(len(result["warnings"]), 2)
        self.assertRegex(warns, r"interval|string")
        self.assertEqual(result["exit_code"], 0)

    def test_preference_does_not_require_chosen_total_gt_rejected(self):
        chosen = _thalamic(
            reward_components={"task_progress": 0.2, "safety": 0.1, "total": 0.3},
            meta={"id": "chosen"},
        )
        rejected = _thalamic(
            reward_components={"task_progress": 0.9, "safety": 0.8, "total": 1.7},
            meta={"id": "rejected"},
        )
        pair = {
            "chosen": chosen,
            "rejected": rejected,
            "critique": "Process quality outranks scalar total.",
            "meta": {"id": "pref-1"},
        }
        tmp, run_dir = _run_dir([pair])
        with tmp:
            result = check_records.check_run(run_dir)
        self.assertFalse(result["errors"], result)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["totals"].get("by_kind", {}).get("preference"), 1)

    def test_weighted_reward_mismatch_and_match(self):
        bad = _thalamic(
            reward_components={
                "task_progress": 1.0,
                "safety": 0.0,
                "weights": {"task_progress": 0.4, "safety": 0.6},
                "total": 0.9,
            },
            meta={"id": "w-bad"},
        )
        good = _thalamic(
            reward_components={
                "task_progress": 1.0,
                "safety": 0.0,
                "weights": {"task_progress": 0.4, "safety": 0.6},
                "total": 0.4,
            },
            meta={"id": "w-good"},
        )
        tmp, run_dir = _run_dir([bad, good])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertEqual(len(result["errors"]), 1, result)
        self.assertIn("batch.jsonl:1", blob)
        self.assertNotIn("batch.jsonl:2", blob)

    def test_chosen_and_rejected_reward_components_are_checked(self):
        pair = {
            "chosen": _thalamic(
                reward_components={"task_progress": 0.5, "safety": 0.5, "total": 0.1},
                meta={"id": "c"},
            ),
            "rejected": _thalamic(
                reward_components={"task_progress": 0.2, "safety": 0.2, "total": 0.05},
                meta={"id": "r"},
            ),
            "critique": "Both sides have broken totals.",
            "meta": {"id": "pref-mismatch"},
        }
        tmp, run_dir = _run_dir([pair])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("chosen", blob)
        self.assertIn("rejected", blob)
        self.assertGreaterEqual(len(result["errors"]), 2)

    def test_json_parse_error(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            (Path(tmp.name) / "broken.jsonl").write_text("{not json\n")
            result = check_records.check_run(tmp.name)
        self.assertTrue(any("JSON parse" in e for e in result["errors"]))
        self.assertEqual(result["exit_code"], 1)

    def test_does_not_write_into_run_dir(self):
        rec = _thalamic()
        tmp, run_dir = _run_dir([rec])
        with tmp:
            before = {p.name for p in run_dir.iterdir()}
            result = check_records.check_run(run_dir)
            after = {p.name for p in run_dir.iterdir()}
        self.assertEqual(before, after)
        self.assertNotIn("manifest.json", after)
        self.assertEqual(result["exit_code"], 0)

    def test_cli_strict_and_exit_codes(self):
        rec = _thalamic()
        rec["state"] = {"domain": "no-sim"}
        tmp, run_dir = _run_dir([rec])
        with tmp:
            loose = _cli([str(run_dir)])
            strict = _cli(["--strict", str(run_dir)])
        self.assertEqual(loose.returncode, 0, loose.stderr)
        self.assertEqual(strict.returncode, 1, strict.stderr)
        self.assertIn("WARNING", loose.stderr)
        self.assertIn("sim_or_real", loose.stderr)

    def test_cli_fixture_dir_exits_1(self):
        proc = _cli([str(FIXTURES)])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("ERROR", proc.stderr)


if __name__ == "__main__":
    unittest.main()
