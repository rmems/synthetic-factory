#!/usr/bin/env python3
"""check_records.py's reward-arithmetic and bookkeeping-key contract.

Reward totals must reconcile against sibling components (compact or
weighted, plain or {value: ...}) while tolerating declared bookkeeping keys
(unit_usd, rounding_decimals, weights, ...) and never treating a
reward-ontology narrative string as an event stream.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from check_records_test_helpers import FIXTURES, _run_dir, _thalamic  # noqa: E402

import check_records  # noqa: E402


class CheckRecordsRewardArithmetic(unittest.TestCase):
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
            "meta": {"id": "pref-1", "round": 1},
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

    def test_nested_weight_aliases_and_value_objects(self):
        rec = _thalamic(
            reward_components={
                "weights": {"task": 0.4, "safety": 0.6},
                "components_executed": {
                    "task_progress": {"value": 1.0, "unit_usd": 100},
                    "safety_alignment": {"value": 0.5, "unit_usd": 100},
                },
                "total": 0.7,
            },
            meta={"id": "nested-weight"},
        )
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertFalse(result["warnings"], result)
        self.assertEqual(result["exit_code"], 0)

    def test_unit_usd_metadata_is_not_summed_as_reward(self):
        rec = _thalamic(
            reward_components={
                "task_progress": {"value": 0.4, "unit_usd": 10000},
                "safety": {"value": 0.6, "unit_usd": 10000},
                "unit_usd": 10000,
                "total": 1.0,
            },
            meta={"id": "unit-metadata"},
        )
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertFalse(result["warnings"], result)

    def test_reward_components_spike_events_narration_is_not_a_stream(self):
        """``reward_components.spike_events`` is a narrative string in the
        reward ontology (schemas/reward-ontology-v1.mapping.json:
        disposition "narrative_annotation", type "string"), not an event
        stream. ``walk_key`` matches by key name only, so without a
        path-aware guard this string is rejected as a malformed spike
        stream (Codex #87, discussion_r3885768184)."""
        rec = _thalamic(
            reward_components={
                "task_progress": 0.4,
                "safety": 0.6,
                "spike_events": "left-to-right sweep, three bursts",
                "total": 1.0,
            },
            meta={"id": "reward-narrative-spike-events"},
        )
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertFalse(result["warnings"], result)
        self.assertEqual(result["exit_code"], 0)

    def test_reward_components_spike_events_array_is_still_validated(self):
        """The narrative-annotation exemption is scoped to the documented
        string shape. An array at reward_components.spike_events is a
        genuine (if oddly placed) stream and must stay strictly checked
        (Codex #87, discussion_r3885829803)."""
        rec = _thalamic(
            reward_components={
                "task_progress": 0.4,
                "safety": 0.6,
                "spike_events": [{"t_rel_ms": 2}, {"t_rel_ms": 1}],
                "total": 1.0,
            },
            meta={"id": "reward-array-spike-events"},
        )
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertTrue(result["errors"], result)
        self.assertIn("not globally non-decreasing", "\n".join(result["errors"]))
        self.assertEqual(result["exit_code"], 1)

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
            "meta": {"id": "pref-mismatch", "round": 1},
        }
        tmp, run_dir = _run_dir([pair])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("chosen", blob)
        self.assertIn("rejected", blob)
        self.assertGreaterEqual(len(result["errors"]), 2)

    def test_declared_rounding_tolerance_is_capped(self):
        # The declaration comes from the record under test, so an uncapped
        # bound would let a record declare its own arithmetic gate away.
        self.assertEqual(check_records.reward_tolerance({}), check_records.TOL)
        self.assertEqual(
            check_records.reward_tolerance({"rounding_decimals": 0}),
            check_records.MAX_DECLARED_TOL,
        )
        self.assertLess(
            check_records.reward_tolerance({"rounding_decimals": 2}),
            check_records.MAX_DECLARED_TOL,
        )

    def test_coarse_rounding_declaration_cannot_hide_a_mismatch(self):
        rec = _thalamic(
            reward_components={
                "task_progress": 0.2,
                "safety": 0.3,
                "total": 0.9,  # 0.4 off — far beyond any honest rounding
                "rounding_decimals": 0,
            },
            meta={"id": "coarse-rounding"},
        )
        tmp, run_dir = _run_dir([rec])
        with tmp:
            result = check_records.check_run(run_dir)
        self.assertTrue(result["errors"], result)
        self.assertEqual(result["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
