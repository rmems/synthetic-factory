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
        "id": "t-001",
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
        "meta": {"id": "t-001", "round": 1},
    }
    rec.update(overrides)
    if "id" not in overrides and isinstance(overrides.get("meta"), dict):
        candidate = overrides["meta"].get("id")
        if isinstance(candidate, str):
            rec["id"] = candidate
    # meta.round is required at the shape layer; meta overrides here only
    # target identity, so backfill round unless a test sets it explicitly.
    if isinstance(rec.get("meta"), dict):
        rec["meta"].setdefault("round", 1)
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

    def test_duplicate_record_id_is_error(self):
        a = _thalamic(meta={"id": "dup-1"})
        b = _thalamic(meta={"id": "dup-1"})
        b["state"] = {"sim_or_real": "designed", "domain": "other"}
        tmp, run_dir = _run_dir([a, b])
        with tmp:
            result = check_records.check_run(run_dir)
        blob = "\n".join(result["errors"])
        self.assertIn("duplicate record id", blob)
        self.assertIn("dup-1", blob)
        self.assertIn("batch.jsonl:2", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_legacy_meta_id_is_warning_for_new_corpus(self):
        rec = _thalamic(meta={"id": "legacy-only"})
        rec.pop("id")
        tmp, run_dir = _run_dir([rec])
        with tmp:
            loose = check_records.check_run(run_dir)
            strict = check_records.check_run(run_dir, strict=True)
        self.assertFalse(loose["errors"], loose)
        self.assertIn("legacy meta.id only", "\n".join(loose["warnings"]))
        self.assertEqual(strict["exit_code"], 1)

    def test_legacy_episode_thought_is_warning(self):
        episode = {
            "id": "legacy-episode",
            "goal": "fixture",
            "steps": [
                {
                    "thought": "private scratch",
                    "tool_call": {"name": "rg", "args": {}},
                    "observation": "none",
                }
            ],
            "outcome": "done",
            "reward": {"success": True},
        }
        tmp, run_dir = _run_dir([episode])
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        self.assertFalse(result["errors"], result)
        self.assertIn("legacy 'thought'", "\n".join(result["warnings"]))
        self.assertEqual(result["exit_code"], 1)

    def test_missing_sim_or_real_is_warning_not_error(self):
        rec = _thalamic()
        rec["state"] = {"domain": "no-provenance"}
        rec["meta"] = {"id": "no-sim", "round": 1}
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

    def test_duplicate_ids_are_global_across_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_jsonl(root / "a.jsonl", [_thalamic(id="root-dup", meta={"id": "meta-a"})])
            _write_jsonl(root / "b.jsonl", [_thalamic(id="root-dup", meta={"id": "meta-b"})])
            result = check_records.check_run(root)
        self.assertEqual(len(result["errors"]), 1, result)
        self.assertIn("root-dup", result["errors"][0])
        self.assertIn("a.jsonl:1", result["errors"][0])
        self.assertIn("b.jsonl:1", result["errors"][0])

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

    def test_json_parse_error(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            (Path(tmp.name) / "broken.jsonl").write_text("{not json\n")
            result = check_records.check_run(tmp.name)
        self.assertTrue(any("JSON parse" in e for e in result["errors"]))
        self.assertEqual(result["exit_code"], 1)

    def test_nonstandard_json_numeric_constants_are_parse_errors(self):
        template = json.dumps(_thalamic()).replace(
            '"domain": "test"',
            '"domain": "test", "measurement": CONSTANT',
        )
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as td:
                path = Path(td) / "nonstandard-number.jsonl"
                path.write_text(template.replace("CONSTANT", constant) + "\n")

                result = check_records.check_run(td)

                self.assertEqual(result["exit_code"], 1)
                self.assertTrue(
                    any(
                        f"non-standard JSON numeric constant {constant}" in error
                        for error in result["errors"]
                    ),
                    result,
                )

    def test_invalid_utf8_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "bad.jsonl").write_bytes(b'{"id":"bad-\xff"}\n')
            result = check_records.check_run(td)
        self.assertEqual(result["exit_code"], 1)
        self.assertIn("invalid UTF-8", "\n".join(result["errors"]))

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


class SpikeOrderHasOneOwner(unittest.TestCase):
    """Spike order is reported once per stream, from this layer only.

    validate_run now checks a trajectory-level stream as well as the bridge
    stream, so both layers see the same inversion. shape_check drops the
    shape layer's order errors — the same layering already used for reward
    arithmetic and 'real' provenance — while keeping its per-event shape
    errors, which this layer does not duplicate.
    """

    UNSORTED = [
        {"channel": "a", "t_rel_ms": 9.0, "amplitude": 0.4},
        {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
    ]

    def _errors(self, record):
        tmp, run_dir = _run_dir([record])
        with tmp:
            return check_records.check_run(run_dir)["errors"]

    def _order_errors(self, record):
        return [e for e in self._errors(record) if "non-decreasing" in e]

    def test_thalamic_stream_reported_once(self):
        errors = self._order_errors(_thalamic(spike_events=list(self.UNSORTED)))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("spike_events: spike_events not globally", errors[0])

    def test_bridge_stream_reported_once(self):
        record = {
            "id": "bridge-unsorted",
            "spike_events": list(self.UNSORTED),
            "language_view": {"trajectory": _thalamic()},
        }
        errors = self._order_errors(record)
        self.assertEqual(len(errors), 1, errors)

    def test_mixed_timestamp_keys_are_not_compared_as_one_clock(self):
        record = {
            "id": "bridge-mixed-clock",
            "spike_events": [
                {"channel": "a", "t_rel_ms": 120.0, "amplitude": 0.4},
                {"channel": "b", "t_ms": 90.0, "amplitude": 0.3},
            ],
            "language_view": {"trajectory": _thalamic()},
        }
        errors = self._errors(record)
        mixed = [e for e in errors if "one timestamp key throughout" in e]
        order = [e for e in errors if "non-decreasing" in e]
        self.assertEqual(len(mixed), 1, errors)
        self.assertEqual(order, [], errors)

    def test_nested_mixed_timestamp_keys_are_rejected_once(self):
        record = _thalamic(
            future_outcome={
                "success": "full",
                "spike_events": [
                    {"t_rel_ms": 120},
                    {"t_ms": 90},
                ],
            }
        )
        errors = self._errors(record)
        mixed = [e for e in errors if "one timestamp key throughout" in e]
        order = [e for e in errors if "non-decreasing" in e]
        self.assertEqual(len(mixed), 1, errors)
        self.assertIn("future_outcome.spike_events", mixed[0])
        self.assertEqual(order, [], errors)

    def test_nested_stream_validates_array_and_every_event(self):
        cases = (
            ({"t_rel_ms": 1}, "spike_events must be an array"),
            ([None], "spike_events[0] must be an object"),
            ([{}], "needs finite t_rel_ms or t_ms"),
            (
                [{"t_rel_ms": 1, "t_ms": 1}],
                "must use exactly one of t_rel_ms or t_ms",
            ),
            ([{"t_rel_ms": 10**400}], "t_rel_ms must be a finite number"),
            (
                [{"t_rel_ms": 1, "channel": False}],
                "channel must be a non-empty string",
            ),
            (
                [{"t_rel_ms": 1, "amplitude": "bad"}],
                "amplitude must be a finite number",
            ),
        )
        for events, marker in cases:
            with self.subTest(marker=marker):
                record = _thalamic(
                    future_outcome={
                        "success": "full",
                        "spike_events": events,
                    }
                )
                errors = self._errors(record)
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("future_outcome.spike_events", errors[0])
                self.assertIn(marker, errors[0])

    def test_large_integer_timestamp_order_preserves_precision(self):
        events = [
            {"t_rel_ms": 9007199254740993},
            {"t_rel_ms": 9007199254740992},
        ]
        errors = self._order_errors(_thalamic(spike_events=events))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("9007199254740993 -> 9007199254740992", errors[0])

    def test_preference_side_stream_reported_once(self):
        record = {
            "id": "pref-unsorted",
            "chosen": _thalamic(spike_events=list(self.UNSORTED)),
            "rejected": _thalamic(meta={"id": "pref-rejected"}),
            "critique": "chosen train is channel-grouped, not time-ordered",
        }
        errors = self._order_errors(record)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("chosen.spike_events", errors[0])

    def test_bridge_event_shape_errors_survive_the_order_filter(self):
        record = {
            "id": "bridge-shapeless",
            "spike_events": [{"t_rel_ms": 1.0}],
            "language_view": {"trajectory": _thalamic()},
        }
        blob = "\n".join(self._errors(record))
        self.assertIn("missing 'channel'", blob)
        self.assertIn("missing 'amplitude'", blob)


class ShapeFilterIgnoresLocationPrefix(unittest.TestCase):
    """Drop markers must not match the JSONL path embedded in `where`."""

    def test_colon_spike_events_filename_does_not_hide_safety_decision(self):
        rec = _thalamic(
            safety_decision={"decision": "NOPE", "rationale": "ok"},
            meta={"id": "path-collision"},
        )
        tmp, run_dir = _run_dir([rec], name="bad: spike_events.jsonl")
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        blob = "\n".join(result["errors"])
        self.assertIn("safety_decision.decision must be ACCEPT|MODIFY|REJECT", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_colon_spike_events_filename_does_not_hide_nested_safety_decision(self):
        record = {
            "id": "pref-path-collision",
            "chosen": _thalamic(
                safety_decision={"decision": "NOPE", "rationale": "ok"},
                meta={"id": "pref-path-chosen"},
            ),
            "rejected": _thalamic(meta={"id": "pref-path-rejected"}),
            "critique": "chosen safety_decision is invalid",
        }
        tmp, run_dir = _run_dir([record], name="bad: spike_events.jsonl")
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        blob = "\n".join(result["errors"])
        self.assertIn("safety_decision.decision must be ACCEPT|MODIFY|REJECT", blob)
        self.assertEqual(result["exit_code"], 1)

    def test_spike_events_filename_does_not_hide_episode_step_errors(self):
        """``check_episode``'s ``{where} step {i}:`` form is a location
        prefix too: a run file literally named ``spike_events.jsonl`` must
        not make its own step-error findings look like dropped spike-stream
        findings (kilo-code-bot #87, discussion_r3885145887)."""
        record = {
            "id": "episode-path-collision",
            "goal": "fix the bug",
            "steps": [
                {"n": 1, "tool_call": {"name": "read_file", "args": {"path": "a.txt"}}}
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
            "meta": {"round": 1},
        }
        tmp, run_dir = _run_dir([record], name="spike_events.jsonl")
        with tmp:
            result = check_records.check_run(run_dir, strict=True)
        blob = "\n".join(result["errors"])
        self.assertIn("missing 'observation'", blob)
        self.assertIn("missing 'decision_basis'", blob)
        self.assertEqual(result["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
