"""Pin the preference-record rules ``validate_run.check_line`` enforces.

Episode-shaped preference pairs are routed through ``validate_run_preference``:
side validation, wrapper invariants, the staging-only goal agreement and shared
context checks, and the critique requirement. Each case changes one property of
a published-shape pair; the full ordered error list is asserted.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import validate_run
from trajectory_preference_support import trajectory_pair

_EPISODE_GOAL = "L1: preference episode needs a shared or chosen goal"
_SHARED_GOAL = "L1: preference needs a shared non-empty goal"


def _drop(*keys):
    def mutate(record):
        for key in keys:
            record.pop(key)

    return mutate


def _side_goal(side, value, *, drop_top=False):
    def mutate(record):
        if drop_top:
            record.pop("goal")
        record[side]["goal"] = value

    return mutate


def _set(key, value, *, drop_top=False):
    def mutate(record):
        if drop_top:
            record.pop("goal")
        record[key] = value

    return mutate


def _set_wrapper_success(value):
    def mutate(record):
        record["reward"]["success"] = value

    return mutate


def _disjoint_first_steps(record):
    record["chosen"]["steps"][0]["tool_call"]["args"]["command"] = "cat a.py"
    record["rejected"]["steps"][0]["tool_call"]["args"]["command"] = "cat b.py"


_STAGING_CASES = (
    ("published pair", None, []),
    (
        "top-level and side goals disagree",
        _side_goal("chosen", "Rotate the edge certificates."),
        ["L1: top-level and side goals must describe the same problem"],
    ),
    (
        "no goal anywhere",
        _drop("goal"),
        [
            "L1.chosen: episode missing 'goal'",
            "L1.rejected: episode missing 'goal'",
            _EPISODE_GOAL,
            _SHARED_GOAL,
        ],
    ),
    (
        "only the chosen side has a goal",
        _side_goal("chosen", "Publish", drop_top=True),
        [
            "L1.rejected: episode missing 'goal'",
            "L1: preference needs both side goals when no top-level goal is present",
        ],
    ),
    (
        "only the rejected side has a goal",
        _side_goal("rejected", "Publish", drop_top=True),
        [
            "L1.chosen: episode missing 'goal'",
            _EPISODE_GOAL,
            "L1: preference needs both side goals when no top-level goal is present",
        ],
    ),
    ("blank top-level goal", _set("goal", "   "), [_SHARED_GOAL]),
    (
        "side goal is not text",
        _side_goal("chosen", 5),
        [
            "L1.chosen: goal must be a non-empty string",
            "L1: chosen.goal must be a non-empty string when present",
        ],
    ),
    (
        "wrapper success is false",
        _set_wrapper_success(False),
        ["L1: preference wrapper reward.success must be true"],
    ),
    (
        "wrapper success is not boolean",
        _set_wrapper_success("yes"),
        ["L1: reward.success must be a boolean"],
    ),
    ("critique missing", _drop("critique"), ["L1: preference record needs a non-empty critique"]),
    ("rejected side is not an object", _set("rejected", "side"), ["L1.rejected must be an object"]),
    ("chosen side is not an object", _set("chosen", "side"), ["L1.chosen must be an object"]),
    (
        "chosen side is not an object and no goal",
        _set("chosen", "side", drop_top=True),
        [
            "L1.chosen must be an object",
            "L1.rejected: episode missing 'goal'",
            _EPISODE_GOAL,
            _SHARED_GOAL,
        ],
    ),
    (
        "sides share no observable context",
        _disjoint_first_steps,
        [
            (
                "L1: preference sides must share observable file, API, target, "
                "or success-criterion context"
            )
        ],
    ),
)


def _check(mutate, *, staging: bool):
    record = trajectory_pair()
    if mutate is not None:
        mutate(record)
    return validate_run.check_line(record, "L1", factory_staging=staging)


class PreferenceLineRules(unittest.TestCase):
    def test_staging_preference_rules(self):
        for label, mutate, errors in _STAGING_CASES:
            with self.subTest(label):
                self.assertEqual(_check(mutate, staging=True), (errors, "preference"))

    def test_wrapper_success_is_a_staging_only_rule(self):
        self.assertEqual(_check(_set_wrapper_success(False), staging=False), ([], "preference"))


if __name__ == "__main__":
    unittest.main()
