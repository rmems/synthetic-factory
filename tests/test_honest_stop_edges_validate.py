"""Error branches for honest-stop record shape checks."""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"
HEX = "a" * 64

import honest_stop.validate_body as body
import honest_stop.validate_preds as preds
import honest_stop.vocabulary as cv
from honest_stop.records import build_record
from honest_stop.validate import validate_record, validate_text


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


def _assign(record: dict, path: tuple, value: object) -> None:
    cursor = record
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def _code(path: tuple, value: object, scenario_id: str = "missing-credential") -> tuple[str, ...]:
    record = built(scenario_id)
    _assign(record, path, value)
    return validate_record(record)


class PredicateTests(unittest.TestCase):
    def test_text_seed_digest_and_timestamp_edges(self):
        self.assertTrue(built()["record_id"].startswith("stop-"))
        self.assertFalse(preds.text_ok(None))
        self.assertFalse(preds.text_ok("  "))
        self.assertTrue(preds.text_ok("stop"))
        self.assertFalse(preds.nonneg_int(True))
        self.assertFalse(preds.nonneg_int(1.0))
        self.assertFalse(preds.nonneg_int(-1))
        self.assertTrue(preds.nonneg_int(0))
        self.assertFalse(preds.exact_keys(["a"], ("a",)))
        self.assertFalse(preds.exact_keys({"a": 1}, ("b",)))
        self.assertTrue(preds.exact_keys({"a": 1}, ("a",)))
        self.assertFalse(preds.digest_ok(None))
        self.assertFalse(preds.digest_ok("sha256:abcd"))
        self.assertFalse(preds.digest_ok("sha256:" + ("A" * 64)))
        self.assertFalse(preds.digest_ok("sha256:" + ("g" * 64)))
        self.assertTrue(preds.digest_ok("sha256:" + HEX))
        self.assertFalse(preds.timestamp_ok(1))
        self.assertFalse(preds.timestamp_ok("not-a-time"))
        self.assertFalse(preds.timestamp_ok("2026-10-20T23:00:00+00:00"))
        self.assertTrue(preds.timestamp_ok("2026-10-20T23:00:00+01:00"))
        self.assertTrue(preds.timestamp_ok(PRODUCED_AT))

    def test_validate_text_rejects_a_recursive_parser_failure(self):
        self.assertEqual(validate_record(built()), ())
        with mock.patch("honest_stop.validate.load_strict_json", side_effect=RecursionError):
            self.assertEqual(validate_text("{}"), ("record.json",))


class ShapeTests(unittest.TestCase):
    def test_identity_context_action_and_result_codes(self):
        samples = (
            (("record_id",), 1, "record_id"),
            (("record_id",), "stop-" + ("a" * 80), "record_id"),
            (("family",), "other", "family"),
            (("task",), "  ", "task"),
            (("context",), [], "context"),
            (("context", "scenario_id"), "  ", "context.scenario_id"),
            (("context", "seed"), -1, "context.seed"),
            (("context", "task_id"), "", "context.task_id"),
            (("context", "world"), "other", "context.world"),
            (("correct_action",), {}, "correct_action"),
            (("correct_action", "message"), "  ", "correct_action.message"),
            (("counterfactual_fake_success",), 1, "counterfactual_fake_success"),
            (("result",), {}, "result"),
            (("result", "verified_blocker"), "yes", "result.verified_blocker"),
        )
        for path, value, code in samples:
            with self.subTest(code=code):
                self.assertIn(code, _code(path, value))

    def test_non_object_and_missing_key_are_record_codes(self):
        self.assertEqual(validate_record([]), ("record.type",))
        record = built()
        del record["task"]
        self.assertEqual(validate_record(record), ("task",))

    def test_trajectory_and_provenance_codes(self):
        samples = (
            (("trajectory",), [], "trajectory"),
            (("trajectory",), "steps", "trajectory"),
            (("trajectory", 0, "n"), True, "trajectory.n"),
            (("trajectory", 0, "n"), "1", "trajectory.n"),
            (("trajectory", 0, "observation"), "", "trajectory.observation"),
            (("trajectory", 0, "observation"), 1, "trajectory.observation"),
            (("trajectory", 0, "tool_call"), {}, "trajectory.tool_call"),
            (("trajectory", 0, "tool_call", "name"), "", "trajectory.tool_call"),
            (("trajectory", 0, "tool_call", "args"), [], "trajectory.tool_call"),
            (("trajectory", 0, "tool_call", "args"), {"": "a"}, "trajectory.tool_call"),
            (("trajectory", 0, "tool_call", "args"), {1: "a"}, "trajectory.tool_call"),
            (("trajectory", 0, "tool_call", "args"), {"x": 1.5}, "trajectory.tool_call"),
            (("provenance", "produced_at"), "yesterday", "provenance.produced_at"),
            (("provenance", "actors"), [], "provenance.actors"),
            (("provenance", "actors"), "no", "provenance.actors"),
            (("provenance", "lineage"), {}, "provenance.lineage"),
            (("provenance", "lineage", "scenario_id"), "", "provenance.lineage"),
            (("provenance", "lineage", "builder"), "  ", "provenance.lineage"),
            (("provenance", "lineage", "seed"), True, "provenance.lineage"),
            (("provenance", "lineage", "run_seed"), -1, "provenance.lineage"),
            (("provenance", "lineage", "config_sha256"), "sha256:ab", "provenance.lineage"),
            (("provenance", "lineage", "parent_ids"), "none", "provenance.lineage"),
            (("provenance", "lineage", "parent_ids"), [""], "provenance.lineage"),
        )
        for path, value, code in samples:
            with self.subTest(path=path, code=code):
                self.assertIn(code, _code(path, value))

    def test_actor_fields_and_step_keys_and_long_trajectory(self):
        record = built()
        record["provenance"]["actors"][0]["role"] = "  "
        self.assertIn("provenance.actors", validate_record(record))
        record = built()
        record["provenance"]["actors"][0]["name"] = ""
        self.assertIn("provenance.actors", validate_record(record))
        record = built()
        record["provenance"]["actors"][0]["digest"] = "nope"
        self.assertIn("provenance.actors", validate_record(record))
        record = built()
        record["provenance"]["actors"][0] = {"role": "scenario_builder"}
        self.assertIn("provenance.actors", validate_record(record))
        record = built()
        record["trajectory"][0] = {"n": 1}
        self.assertIn("trajectory.step", validate_record(record))
        record = built()
        step = json.loads(json.dumps(record["trajectory"][0]))
        record["trajectory"] = []
        for index in range(1, cv.MAX_STEPS + 2):
            copied = json.loads(json.dumps(step))
            copied["n"] = index
            record["trajectory"].append(copied)
        self.assertEqual(validate_record(record), ("trajectory",))
        record = built()
        record["trajectory"][0]["tool_call"]["args"] = {"port": 1, "ok": True, "name": "api"}
        self.assertEqual(validate_record(record), ())

    def test_body_helpers_accept_a_well_formed_record(self):
        record = built()
        self.assertEqual(body.trajectory_codes(record), ())
        self.assertEqual(body.provenance_codes(record), ())
        self.assertTrue(body._parent_ids([]))
        self.assertTrue(body._args_ok({"port": 1, "ok": True, "name": "api"}))
        self.assertTrue(body._arg_value("api"))
        self.assertFalse(body._arg_value(1.5))
        self.assertTrue(body._observation_ok("seen"))
        self.assertTrue(body._index_ok(1, 1))
        self.assertFalse(body._index_ok(2, 1))
