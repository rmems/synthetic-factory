#!/usr/bin/env python3
"""check_records.py's spike-stream single-owner contract.

SpikeOrderHasOneOwner: spike order and per-event shape are reported exactly
once, from the deep layer only, for every stream the deep layer discovers
(bridge root, trajectory, or nested) — the shape layer's copies are dropped.
ShapeFilterIgnoresLocationPrefix: the drop-marker classification that makes
that layering possible must key off the diagnostic body, never off a
location prefix a JSONL filename could collide with.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from check_records_test_helpers import FIXTURES, _run_dir, _thalamic  # noqa: E402

import check_records  # noqa: E402


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

    def _clock_errors(self, record):
        return [e for e in self._errors(record) if "one clock domain" in e]

    def test_a_nested_stream_is_judged_against_its_own_owners_clock(self):
        """A clock declaration sits on the stream's own parent. The deep walk
        discarded that parent, so a nested stream whose owner declares one
        clock and whose events declare another passed --strict while the
        curator quarantines the same shape (Codex #87)."""
        record = _thalamic(
            future_outcome={
                "clock_id": "record-clock",
                "spike_events": [{"t_rel_ms": 1, "source_clock": "event-clock"}],
            }
        )
        errors = self._clock_errors(record)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("future_outcome.spike_events", errors[0])
        self.assertIn("record-clock", errors[0])
        self.assertIn("event-clock", errors[0])

    def test_a_nested_stream_agreeing_with_its_owner_is_one_domain(self):
        """The owner's declaration must not manufacture a second domain."""
        record = _thalamic(
            future_outcome={
                "clock_id": "one-clock",
                "spike_events": [{"t_rel_ms": 1, "source_clock": "one-clock"}],
            }
        )
        self.assertEqual(self._clock_errors(record), [])

    def test_an_outer_record_clock_does_not_govern_a_nested_stream(self):
        """Each stream answers to its own owner, not to the outermost record:
        two sibling streams may legitimately run on different clocks."""
        record = _thalamic(
            spike_events=[{"channel": "a", "t_rel_ms": 1.0, "source_clock": "outer"}],
            future_outcome={
                "spike_events": [{"t_rel_ms": 1, "source_clock": "inner"}],
            },
        )
        self.assertEqual(self._clock_errors(record), [])

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

    def test_decimal_timestamp_order_preserves_source_token_precision(self):
        record = _thalamic(
            spike_events=[
                {"t_rel_ms": 101},
                {"t_rel_ms": 102},
            ]
        )
        payload = json.dumps(record, separators=(",", ":"))
        payload = payload.replace('"t_rel_ms":101', '"t_rel_ms":1.0000000000000001')
        payload = payload.replace('"t_rel_ms":102', '"t_rel_ms":1.0')
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch.jsonl"
            source.write_text(payload + "\n", encoding="utf-8")
            errors = check_records.check_run(td)["errors"]

        order_errors = [error for error in errors if "non-decreasing" in error]
        self.assertEqual(len(order_errors), 1, errors)
        self.assertIn("1.0000000000000001 -> 1.0", order_errors[0])

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
