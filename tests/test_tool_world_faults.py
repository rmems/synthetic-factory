#!/usr/bin/env python3
"""Seeded fault schedules and the engine that counts matching calls until a fault fires."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_world_pack_support import RECOVERY_ROW, SEEDS, armed, call, fault_row, refusal, spec

# The support module goes first: it puts pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import faults as faults_mod
from tool_world import pack as pack_mod
from tool_world import vocabulary as cv
from tool_world._contract import rng

BAD_FAULT_ROWS = (
    ("not an object", "fault must be an object"),
    (fault_row(id=7), "fault field 'id' must be str"),
    (fault_row(marker=None), "fault field 'marker' must be str"),
    (fault_row(occurrence=-1), "occurrence must be a non-negative integer"),
    (fault_row(occurrence=True), "occurrence must be a non-negative integer"),
    (fault_row(min_occurrence=3, max_occurrence=2), "1 <= min <= max"),
    (fault_row(min_occurrence=0), "1 <= min <= max"),
    (fault_row(probability_percent=101), "[0, 100]"),
    (fault_row(selector=[]), "selector must be an object"),
    (fault_row(params="abc"), "params must be an object"),
    (fault_row(retry="false"), "retry must be a boolean"),
    (
        fault_row(recovery=[RECOVERY_ROW | {"verification": "yes"}]),
        "t.recovery[0]: verification must be a boolean",
    ),
    (fault_row(recovery={}), "recovery must be a list of actions"),
    (fault_row(recovery=["x"]), "recovery must be a list of actions"),
    (
        fault_row(recovery=[{"tool_call": call("read_file", path="x")}]),
        "t.recovery[0]: intent must be a nonempty string",
    ),
    (
        fault_row(recovery=[RECOVERY_ROW | {"captures": {"x": "("}}]),
        "t.recovery[0]: capture 'x' is not a valid regex",
    ),
)


class FaultSchedule(unittest.TestCase):
    def test_a_seed_yields_the_same_schedule_every_time(self):
        specs = (
            spec(id="a", probability_percent=50, occurrence=0, min_occurrence=1, max_occurrence=5),
            spec(id="b", probability_percent=50, occurrence=0, min_occurrence=1, max_occurrence=9),
        )
        for seed in SEEDS:
            with self.subTest(seed=seed):
                first = faults_mod.schedule_faults(specs, rng.DrawStream(seed))
                second = faults_mod.schedule_faults(specs, rng.DrawStream(seed))
                self.assertEqual(first, second)
                self.assertEqual([entry.fault_id for entry in first], ["a", "b"])

    def test_every_spec_consumes_two_draws_whether_or_not_it_arms(self):
        for percent in (0, 100):
            stream = rng.DrawStream(3)
            scheduled = faults_mod.schedule_faults(
                (spec(id="a", probability_percent=percent), spec(id="b")), stream
            )
            self.assertEqual(stream.draws, 4)
            self.assertEqual(scheduled[0].armed, percent == 100)
            self.assertTrue(scheduled[1].armed)

    def test_disarming_an_earlier_fault_never_shifts_a_later_schedule(self):
        later = spec(id="b", occurrence=0, min_occurrence=1, max_occurrence=40)
        for seed in SEEDS:
            with self.subTest(seed=seed):
                with_first = faults_mod.schedule_faults(
                    (spec(id="a", probability_percent=100), later), rng.DrawStream(seed)
                )
                without_first = faults_mod.schedule_faults(
                    (spec(id="a", probability_percent=0), later), rng.DrawStream(seed)
                )
                self.assertTrue(with_first[0].armed)
                self.assertFalse(without_first[0].armed)
                self.assertEqual(with_first[1], without_first[1])

    def test_occurrence_zero_draws_from_the_declared_range(self):
        drawn = spec(id="d", occurrence=0, min_occurrence=2, max_occurrence=4)
        fixed = spec(id="f", occurrence=3, min_occurrence=1, max_occurrence=9)
        seen = set()
        for seed in range(24):
            scheduled = faults_mod.schedule_faults((drawn, fixed), rng.DrawStream(seed))
            self.assertIn(scheduled[0].occurrence, (2, 3, 4))
            self.assertEqual(scheduled[1].occurrence, 3)
            seen.add(scheduled[0].occurrence)
        self.assertEqual(seen, {2, 3, 4})

    def test_row_defaults(self):
        parsed = spec()
        self.assertEqual(
            (parsed.occurrence, parsed.min_occurrence, parsed.max_occurrence),
            (1, 1, 1),
        )
        self.assertEqual(
            (parsed.probability_percent, parsed.retry, parsed.recovery), (100, True, ())
        )
        self.assertEqual((parsed.selector, parsed.params), ({}, {}))

    def test_every_bad_row_is_a_coded_refusal(self):
        for row, needle in BAD_FAULT_ROWS:
            with self.subTest(needle=needle), refusal(self, cv.FINDING_TASK_FIELD_INVALID, needle):
                faults_mod.fault_spec_from_row(row, "t")

    def test_recovery_rows_are_parsed_into_actions_at_load(self):
        parsed = spec(recovery=[RECOVERY_ROW])
        (action,) = parsed.recovery
        self.assertIsInstance(action, pack_mod.Action)
        self.assertEqual(action.tool_call, call("read_file", path="x"))
        self.assertIs(pack_mod.action_from_row(action, "again"), action)


class FaultEngineCounting(unittest.TestCase):
    def test_dotted_selectors_reach_nested_arguments_and_count_only_matching_calls(self):
        named = spec(
            id="named",
            tool="mcp",
            selector={"params.name": "create_ticket", "server": "tickets"},
            occurrence=2,
        )
        engine = faults_mod.FaultEngine((armed(named, 2),))
        hit = {"server": "tickets", "params": {"name": "create_ticket"}}
        self.assertIsNone(engine.check("mcp", {"server": "tickets", "params": {"name": "other"}}))
        self.assertIsNone(engine.check("mcp", {"server": "tickets"}))
        self.assertIsNone(engine.check("mcp", {"server": "tickets", "params": "create_ticket"}))
        self.assertIsNone(engine.check("other", hit))
        self.assertIsNone(engine.check("mcp", hit))
        fired = engine.check("mcp", hit)
        self.assertIs(fired.spec, named)
        self.assertEqual(fired.fault_id, "named")
        self.assertIsNone(engine.check("mcp", hit))
        self.assertEqual(engine.fired, ("named",))

    def test_first_armed_match_wins_and_every_matching_counter_still_advances(self):
        first, second, third = spec(id="first"), spec(id="second"), spec(id="third")
        engine = faults_mod.FaultEngine((armed(first, 1), armed(second, 1), armed(third, 2)))
        self.assertEqual(engine.check("run_tests", {"suite": "unit"}).fault_id, "first")
        self.assertEqual(engine.check("run_tests", {"suite": "unit"}).fault_id, "third")
        self.assertIsNone(engine.check("run_tests", {"suite": "unit"}))
        self.assertEqual(engine.fired, ("first", "third"))
        self.assertEqual(engine.armed_ids(), ("first", "second", "third"))

    def test_a_disarmed_fault_counts_but_never_fires(self):
        entry = faults_mod.ScheduledFault(spec(id="off"), False, 1)
        engine = faults_mod.FaultEngine((entry, armed(spec(id="on"), 2)))
        self.assertIsNone(engine.check("run_tests", {"suite": "unit"}))
        self.assertEqual(engine.check("run_tests", {"suite": "unit"}).fault_id, "on")
        self.assertEqual(engine.armed_ids(), ("on",))
        self.assertEqual(engine.scheduled, (entry, engine.scheduled[1]))


if __name__ == "__main__":
    unittest.main()
