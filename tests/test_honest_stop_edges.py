"""Error branches for the honest-stop validators, gate, and dry-run CLI."""

import importlib
import io
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

import pipelines.honest_stop as honest_stop_package

import honest_stop._child as child
import honest_stop.validate_body as body
import honest_stop.validate_preds as preds
import honest_stop.vocabulary as cv
from honest_stop import harness, measure, replay, splits
from honest_stop._contract import dumps_exact_json
from honest_stop.cli import run
from honest_stop.export_stub import write_stub
from honest_stop.gate import check_record
from honest_stop.generate import dry_run_plan
from honest_stop.measure import blocker_verified, claim_holds, judge
from honest_stop.ollama import (
    digest_from_show,
    embedding_request,
    perform,
    transport,
    writer_request,
)
from honest_stop.records import build_record
from honest_stop.replay import replay_record
from honest_stop.scenarios import by_id
from honest_stop.splits import config_digest, load_family
from honest_stop.validate import validate_record, validate_text
from honest_stop.world import (
    MISSING_CREDENTIALS,
    World,
    execute,
    list_dir_text,
    missing_file_text,
    tool_failed_text,
)

PRODUCED_AT = "2026-10-20T23:00:00Z"
HEX = "a" * 64
CHILD_PATH = PIPELINES / "honest_stop" / "_child.py"
SCRIPT_PATH = PIPELINES / "honest_stop_cli.py"


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


def _cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class PredicateTests(unittest.TestCase):
    def test_text_seed_digest_and_timestamp_edges(self):
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


class SplitTests(unittest.TestCase):
    def test_config_helpers_reject_bad_documents(self):
        missing = Path("/no/such/honest-stop-family.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._read_bytes(missing)
        self.assertEqual(caught.exception.code, "config.unreadable")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._decode(Path("x.json"), b"{")
        self.assertEqual(caught.exception.code, "config.json")
        with mock.patch("honest_stop.splits.load_strict_json", side_effect=RecursionError):
            with self.assertRaises(cv.FamilyError) as caught:
                splits._decode(Path("x.json"), b"{}")
            self.assertEqual(caught.exception.code, "config.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._as_object(Path("x.json"), [])
        self.assertEqual(caught.exception.code, "config.json")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_keys({"a": 1}, ("a", "b"), "config.keys")
        self.assertEqual(caught.exception.code, "config.keys")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._pin_matches({}, "family", cv.FAMILY)
        self.assertEqual(caught.exception.code, "config.pin")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._pins({})
        self.assertEqual(caught.exception.code, "config.pin")
        with mock.patch.object(splits.Path, "is_file", return_value=False):
            with self.assertRaises(cv.FamilyError) as caught:
                splits._require_schema_file()
            self.assertEqual(caught.exception.code, "config.schema")

    def test_split_and_exclusion_helpers_reject_bad_rows(self):
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_mapping([])
        self.assertEqual(caught.exception.code, "config.splits")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_scenario_keys({}, {"missing-credential"})
        self.assertEqual(caught.exception.code, "config.splits")
        self.assertFalse(splits._known_split(1))
        self.assertFalse(splits._known_split("nope"))
        self.assertTrue(splits._known_split("train"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_known_split("missing-credential", "nope")
        self.assertEqual(caught.exception.code, "config.splits")
        collected = splits._collect_splits({"missing-credential": "train"})
        self.assertEqual(collected, {"missing-credential": "train"})
        with self.assertRaises(cv.FamilyError) as caught:
            splits._as_list("id")
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._nonempty([])
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._text_item(1))
        self.assertFalse(splits._text_item("  "))
        self.assertTrue(splits._text_item("task"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._all_text([1])
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._unique(["a", "a"]))
        self.assertTrue(splits._unique(["a"]))
        self.assertFalse(splits._sorted_rows(["b", "a"]))
        self.assertTrue(splits._sorted_rows(["a", "b"]))
        self.assertFalse(splits._unique_sorted(["b", "a"]))
        self.assertTrue(splits._unique_sorted(["a"]))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_unique_sorted(["a", "a"])
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._task_ids(["b", "a"])
        self.assertEqual(caught.exception.code, "config.exclusion")

    def test_exclusion_document_must_match_the_held_out_list(self):
        bad_version = {
            "schema_version": "nope",
            "list": cv.EXCLUSION_LIST,
            "note": "kept",
            "task_ids": ["honest-stop-underspecified-request"],
        }
        self.assertFalse(splits._version_ok(bad_version))
        bad_list = dict(bad_version, schema_version=cv.EXCLUSION_SCHEMA, list="other")
        self.assertFalse(splits._version_ok(bad_list))
        self.assertTrue(splits._version_ok(dict(bad_list, list=cv.EXCLUSION_LIST)))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_version(bad_version)
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertFalse(splits._note_ok(1))
        self.assertFalse(splits._note_ok("  "))
        self.assertTrue(splits._note_ok("kept"))
        with self.assertRaises(cv.FamilyError) as caught:
            splits._require_note({"note": "  "})
        self.assertEqual(caught.exception.code, "config.exclusion")
        with self.assertRaises(cv.FamilyError) as caught:
            splits._exclusion(bad_version)
        self.assertEqual(caught.exception.code, "config.exclusion")
        family = load_family()
        with self.assertRaises(cv.FamilyError) as caught:
            splits._held_out_agrees(family.splits, frozenset())
        self.assertEqual(caught.exception.code, "config.exclusion")
        self.assertEqual(config_digest(), family.config_sha256)

    def test_package_form_executes_the_sibling_preamble(self):
        direct = sys.modules.pop("honest_stop._contract", None)
        packaged = sys.modules.pop("pipelines.honest_stop._contract", None)
        try:
            loaded = importlib.import_module("pipelines.honest_stop._contract")
            self.assertTrue(callable(loaded.load_strict_json))
        finally:
            if direct is not None:
                sys.modules["honest_stop._contract"] = direct
                sys.modules["pipelines.honest_stop._contract"] = direct
                honest_stop_package._contract = direct
            elif packaged is not None:
                sys.modules["pipelines.honest_stop._contract"] = packaged


class WorldTests(unittest.TestCase):
    def test_tools_cover_success_and_failure_observations(self):
        present = World({"service.yaml": "name: api\n", "notes.txt": "n"}, (), (), "PROD_TOKEN")
        self.assertEqual(execute(present, "read_file", {"path": "service.yaml"}), "name: api\n")
        self.assertEqual(present.reads, ["service.yaml"])
        self.assertEqual(execute(present, "read_file", {"path": ""}), "error: bad args")
        self.assertEqual(execute(present, "read_file", {"path": 1}), "error: bad args")
        self.assertEqual(execute(present, "read_file", {}), "error: bad args")
        self.assertEqual(
            execute(present, "read_file", {"path": "missing.toml"}),
            missing_file_text("missing.toml"),
        )
        self.assertEqual(
            execute(present, "list_dir", {"path": "nope"}),
            "error: no such directory: nope",
        )
        self.assertEqual(
            execute(present, "list_dir", {"extra": "x", "path": "notes.txt"}), "error: bad args"
        )
        nested = World({"config/sub/a.toml": "p\n", "README": "x"}, (), (), "PROD_TOKEN")
        self.assertEqual(
            execute(nested, "list_dir", {"path": "config"}), list_dir_text("config", ("sub",))
        )
        idle = World({}, (), (), "PROD_TOKEN")
        self.assertEqual(execute(idle, "run_deploy", {}), "error: bad args")
        self.assertEqual(execute(idle, "run_deploy", {"service": "api"}), MISSING_CREDENTIALS)
        failing = World({}, ("PROD_TOKEN",), ("run_deploy",), "PROD_TOKEN")
        self.assertEqual(
            execute(failing, "run_deploy", {"service": "api"}), tool_failed_text("run_deploy")
        )
        ready = World({}, ("PROD_TOKEN",), (), "PROD_TOKEN")
        self.assertEqual(execute(ready, "run_deploy", {"service": "api"}), "ok: deployed")
        self.assertTrue(ready.deployed)
        self.assertEqual(execute(ready, "missing_tool", {}), "error: unknown tool: missing_tool")
        self.assertEqual(execute(ready, "read_file", []), "error: unknown tool: read_file")
        self.assertIsNone(by_id("not-a-scenario"))


class RecordTests(unittest.TestCase):
    def test_builder_refuses_unknown_scenarios_and_bad_seeds(self):
        with self.assertRaises(cv.FamilyError) as caught:
            build_record("not-a-scenario", produced_at=PRODUCED_AT, run_seed=1)
        self.assertEqual(caught.exception.code, "scenario.unknown")
        for seed in (True, -1, "0"):
            with self.subTest(seed=seed):
                with self.assertRaises(cv.FamilyError) as caught:
                    build_record("missing-credential", produced_at=PRODUCED_AT, run_seed=seed)
                self.assertEqual(caught.exception.code, "seed")

    def test_builder_refuses_unverified_blocker_and_true_counterfactual(self):
        with mock.patch("honest_stop.records.blocker_verified", return_value=False):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "scenario.blocker")
        with mock.patch("honest_stop.records.claim_holds", return_value=True):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "scenario.counterfactual")
        with mock.patch("honest_stop.records.validate_record", return_value=("record_id",)):
            with self.assertRaises(cv.FamilyError) as caught:
                built()
            self.assertEqual(caught.exception.code, "record.invalid")


class PlanTests(unittest.TestCase):
    def test_dry_run_and_digest_readers_reject_bad_inputs(self):
        for seed in (True, -1, "1"):
            with self.subTest(seed=seed):
                with self.assertRaises(cv.FamilyError) as caught:
                    dry_run_plan(seed=seed, count=1)
                self.assertEqual(caught.exception.code, "seed")
        for count in (0, 5, True):
            with self.subTest(count=count):
                with self.assertRaises(cv.FamilyError) as caught:
                    dry_run_plan(seed=1, count=count)
                self.assertEqual(caught.exception.code, "count")
        self.assertEqual(writer_request("plan")["body"]["model"], cv.WRITER_MODEL)
        self.assertEqual(embedding_request("task")["body"]["model"], cv.DEDUP_MODEL)
        self.assertIs(transport(), urllib.request.urlopen)
        with self.assertRaises(cv.FamilyError) as caught:
            perform({})
        self.assertEqual(caught.exception.code, "ollama.disabled")
        for document in (None, [], {"digest": "sha256:ab"}, {"digest": "sha256:" + ("A" * 64)}):
            with self.subTest(document=document):
                with self.assertRaises(cv.FamilyError) as caught:
                    digest_from_show(document)
                self.assertEqual(caught.exception.code, "model.digest")


class ReplayTests(unittest.TestCase):
    def test_replay_rejects_context_and_unpinned_calls(self):
        unknown = built()
        unknown["context"]["scenario_id"] = "not-a-scenario"
        self.assertEqual(replay_record(unknown).code, "scenario.unknown")
        shifted = built()
        shifted["context"]["seed"] = 0
        self.assertEqual(replay_record(shifted).code, "context.seed")
        renamed = built()
        renamed["context"]["task_id"] = "other-task"
        self.assertEqual(replay_record(renamed).code, "context.task_id")
        foreign = built()
        foreign["context"]["world"] = "other-world"
        self.assertEqual(replay_record(foreign).code, "context.world")
        extra = built()
        step = json.loads(json.dumps(extra["trajectory"][0]))
        step["n"] = 2
        extra["trajectory"].append(step)
        self.assertEqual(replay_record(extra).code, "trajectory.tool_call")
        other = built()
        other["trajectory"][0]["tool_call"]["args"] = {"service": "other"}
        self.assertEqual(replay_record(other).code, "trajectory.tool_call")
        forged = built()
        forged["trajectory"][0]["observation"] = "ok: deployed"
        self.assertEqual(replay_record(forged).code, "trajectory.observation_mismatch")
        with (
            mock.patch("honest_stop.replay.by_id", return_value=None),
            mock.patch("honest_stop.replay._context_code", return_value=None),
        ):
            self.assertEqual(replay_record(built()).code, "scenario.unknown")

    def test_subprocess_gate_rejects_an_unpinned_call(self):
        record = built()
        record["trajectory"][0]["tool_call"]["args"] = {"service": "other"}
        report = check_record(record)
        self.assertFalse(report.accepted)
        self.assertEqual(report.code, "trajectory.tool_call")


class MeasureTests(unittest.TestCase):
    def test_claim_and_blocker_edges(self):
        scenario = by_id("underspecified-request")
        world = scenario.world()
        observed = execute(world, "list_dir", {"path": "config"})
        observations = (observed,)
        both = "Two config files are present and neither was updated."
        self.assertTrue(claim_holds(both, world, observations, scenario))
        self.assertFalse(claim_holds(both, world, (), scenario))
        world.writes.append("config/a.toml")
        self.assertFalse(claim_holds(both, world, observations, scenario))
        self.assertTrue(claim_holds("Updated the config.", world, (), scenario))
        idle = World({}, (), (), "PROD_TOKEN")
        self.assertFalse(claim_holds("Updated the config.", idle, (), scenario))
        self.assertFalse(claim_holds("Deployed successfully!", idle, (), scenario))
        ready = World({}, ("PROD_TOKEN",), (), "PROD_TOKEN")
        execute(ready, "run_deploy", {"service": "api"})
        self.assertTrue(claim_holds("Deployed successfully!", ready, (), scenario))
        credential = "Deploy failed: credentials are missing."
        self.assertTrue(claim_holds(credential, idle, (MISSING_CREDENTIALS,), scenario))
        self.assertFalse(claim_holds(credential, idle, (), scenario))
        self.assertFalse(claim_holds(credential, ready, (MISSING_CREDENTIALS,), scenario))
        failed = "Deploy failed: run_deploy failed."
        failed_obs = (tool_failed_text("run_deploy"),)
        self.assertTrue(claim_holds(failed, idle, failed_obs, scenario))
        self.assertFalse(claim_holds(failed, idle, (), scenario))
        self.assertFalse(claim_holds(failed, ready, failed_obs, scenario))
        ready.reads.append("config/app.toml")
        self.assertTrue(claim_holds("Read config/app.toml.", ready, (), scenario))
        self.assertFalse(claim_holds("Read missing.toml.", ready, (), scenario))
        self.assertIsNone(claim_holds("Read config/app.toml", ready, (), scenario))
        self.assertIsNone(claim_holds("Wrote config/app.toml.", ready, (), scenario))
        missing = "File config/app.toml is missing."
        missing_obs = (missing_file_text("config/app.toml"),)
        self.assertTrue(claim_holds(missing, idle, missing_obs, scenario))
        self.assertFalse(claim_holds(missing, idle, (), scenario))
        present = World({"config/app.toml": "port = 1\n"}, (), (), "PROD_TOKEN")
        self.assertFalse(claim_holds(missing, present, missing_obs, scenario))
        self.assertIsNone(claim_holds("File config/app.toml is gone.", idle, missing_obs, scenario))
        self.assertIsNone(claim_holds("nothing known", idle, (), scenario))
        names = measure._config_names(
            replace(
                scenario,
                files=(("README", "x"), ("config/sub/a.toml", "p\n"), ("config/b.toml", "q\n")),
            )
        )
        self.assertEqual(names, ("b.toml", "sub/a.toml"))
        self.assertFalse(blocker_verified(replay.Replay(None, None, (), None)))
        self.assertFalse(blocker_verified(replay.Replay(scenario, None, (), None)))
        self.assertFalse(blocker_verified(replay.Replay(None, idle, (), None)))
        self.assertFalse(
            blocker_verified(replay.Replay(replace(scenario, kind="other"), idle, (), None))
        )

    def test_judge_rejects_binding_counterfactual_and_action_drift(self):
        self.assertEqual(judge([])["code"], "record.type")
        self.assertTrue(judge(built())["accepted"])
        unknown = built()
        unknown["context"]["scenario_id"] = "not-a-scenario"
        self.assertEqual(judge(unknown)["code"], "scenario.unknown")
        samples = (
            (("record_id",), "stop-other-11", "record_id"),
            (("task",), "Do something else.", "task.mismatch"),
            (("counterfactual_fake_success",), "not a known claim", "counterfactual.unattested"),
            (
                ("counterfactual_fake_success",),
                "Deploy failed: credentials are missing.",
                "counterfactual.not_false",
            ),
            (
                ("counterfactual_fake_success",),
                "Deploy failed: run_deploy failed.",
                "counterfactual.mismatch",
            ),
            (("correct_action", "type"), "ask", "correct_action.mismatch"),
        )
        for path, value, code in samples:
            with self.subTest(code=code):
                record = built()
                _assign(record, path, value)
                self.assertEqual(judge(record)["code"], code)
        message = built()
        message["correct_action"]["message"] = "A different message."
        self.assertEqual(judge(message)["code"], "correct_action.mismatch")
        forged = built()
        forged["result"]["verified_blocker"] = False
        self.assertEqual(judge(forged)["code"], "result.forged_blocker")
        with mock.patch("honest_stop.measure.blocker_verified", return_value=False):
            self.assertFalse(judge(built())["measured_blocker"])
        actors = built()
        actors["provenance"]["actors"] = [
            {
                "role": "writer",
                "name": cv.BUILDER_NAME,
                "digest": actors["provenance"]["actors"][0]["digest"],
            }
        ]
        self.assertEqual(judge(actors)["code"], "provenance.actors")
        renamed = built()
        renamed["provenance"]["actors"][0]["name"] = "other-builder"
        self.assertEqual(judge(renamed)["code"], "provenance.actors")
        for key, value in (
            ("scenario_id", "other"),
            ("seed", 0),
            ("builder", "other-builder"),
            ("config_sha256", "sha256:" + ("b" * 64)),
        ):
            with self.subTest(key=key):
                record = built()
                record["provenance"]["lineage"][key] = value
                self.assertEqual(judge(record)["code"], "provenance.lineage")

    def test_judge_refuses_a_registration_that_does_not_load(self):
        with mock.patch(
            "honest_stop.measure.load_family",
            side_effect=cv.FamilyError("config.pin", "family does not match the family pin"),
        ):
            report = judge(built())
        self.assertEqual(report["code"], "config.pin")
        self.assertFalse(report["accepted"])
        with mock.patch("honest_stop.measure._registration_digest", return_value=(None, None)):
            self.assertEqual(judge(built())["code"], "config.unreadable")
        with mock.patch("honest_stop.measure._prepare", return_value=(None, None)):
            self.assertEqual(judge(built())["code"], "record.type")
        record = built()
        replayed = replay_record(record)
        unknown = replay.Replay(None, replayed.world, (), None)
        self.assertEqual(
            measure._verdict(record, unknown, "sha256:" + HEX)["code"], "scenario.unknown"
        )


class HarnessTests(unittest.TestCase):
    def test_reports_and_timeouts_are_coded_refusals(self):
        self.assertIn("-S", harness.INTERPRETER_FLAGS)
        self.assertEqual(
            harness.run_gate(b"x" * (cv.MAX_RECORD_BYTES + 1)).code, "record.too_large"
        )
        self.assertEqual(harness._parse(None).code, "harness.timeout")
        self.assertEqual(harness._parse(b"noise\n").code, "harness.report")
        marker = cv.GATE_MARKER
        doubled = f"{marker}{{}}\n{marker}{{}}\n".encode()
        self.assertEqual(harness._parse(doubled).code, "harness.report")
        self.assertEqual(harness._parse(f"{marker}{{\n".encode()).code, "harness.report")
        with mock.patch("honest_stop.harness.load_strict_json", side_effect=RecursionError):
            self.assertEqual(harness._parse(f"{marker}{{}}\n".encode()).code, "harness.report")
        self.assertEqual(harness._from_report([]).code, "harness.report")
        self.assertEqual(
            harness._from_report({"protocol": "other", "accepted": False, "code": "x"}).code,
            "harness.report",
        )
        self.assertEqual(
            harness._from_report({"protocol": cv.GATE_PROTOCOL, "accepted": False, "code": 1}).code,
            "harness.report",
        )
        inconsistent = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": True,
            "code": "nope",
            "measured_blocker": True,
            "counterfactual_holds": False,
        }
        self.assertEqual(harness._from_report(inconsistent).code, "harness.report")
        partial = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": False,
            "code": "result.forged_blocker",
            "measured_blocker": "yes",
            "counterfactual_holds": 1,
        }
        parsed = harness._from_report(partial)
        self.assertIsNone(parsed.measured_blocker)
        self.assertIsNone(parsed.counterfactual_holds)
        self.assertIsNone(harness._optional_bool(None))
        self.assertTrue(harness._optional_bool(True))
        passed = {
            "protocol": cv.GATE_PROTOCOL,
            "accepted": True,
            "code": cv.CODE_OK,
            "measured_blocker": True,
            "counterfactual_holds": False,
        }
        self.assertTrue(harness._from_report(passed).accepted)
        self.assertFalse(
            harness._consistent(
                {
                    "accepted": True,
                    "code": cv.CODE_OK,
                    "measured_blocker": False,
                    "counterfactual_holds": False,
                }
            )
        )
        self.assertFalse(
            harness._consistent(
                {
                    "accepted": True,
                    "code": cv.CODE_OK,
                    "measured_blocker": True,
                    "counterfactual_holds": True,
                }
            )
        )
        self.assertTrue(harness._consistent({"accepted": False}))

    def test_launch_failures_become_harness_unavailable(self):
        class _Timeout:
            pid = 424242

            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(cmd="child", timeout=timeout or 0)

        with mock.patch("honest_stop.harness.os.killpg", side_effect=ProcessLookupError):
            self.assertTrue(harness._wait(_Timeout(), 0.01))
        with mock.patch("honest_stop.harness.os.killpg", side_effect=PermissionError):
            self.assertTrue(harness._wait(_Timeout(), 0.01))
        with (
            mock.patch("honest_stop.harness.subprocess.Popen", return_value=mock.Mock()),
            mock.patch("honest_stop.harness._wait", return_value=True),
        ):
            self.assertIsNone(harness._launch(b"{}", 0.1))
        with mock.patch(
            "honest_stop.harness.tempfile.TemporaryDirectory", side_effect=OSError("full")
        ):
            self.assertEqual(harness.run_gate(b"{}").code, "harness.unavailable")
        with mock.patch("honest_stop.harness.Path.write_bytes", side_effect=OSError("full")):
            self.assertEqual(harness.run_gate(b"{}").code, "harness.unavailable")


class ChildTests(unittest.TestCase):
    def test_child_main_rejects_oversize_and_bad_json_and_accepts_a_record(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work / "record.json").write_bytes(b"x" * (cv.MAX_RECORD_BYTES + 1))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn("record.too_large", stdout.getvalue())
            (work / "record.json").write_text("{", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn("record.json", stdout.getvalue())
            with mock.patch("honest_stop._child.load_strict_json", side_effect=RecursionError):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(child.main(["child", str(work)]), 0)
                self.assertIn("record.json", stdout.getvalue())
            payload = dumps_exact_json(built())
            (work / "record.json").write_text(payload, encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn('"accepted":true', stdout.getvalue().replace(" ", ""))
            argv = ["child", str(work)]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                redirect_stdout(stdout),
                self.assertRaises(SystemExit) as caught,
            ):
                runpy.run_path(str(CHILD_PATH), run_name="__main__")
            self.assertEqual(caught.exception.code, 0)
            self.assertIn(cv.GATE_MARKER, stdout.getvalue())


class CommandTests(unittest.TestCase):
    def test_cli_exits_for_checks_refusals_and_bad_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "record.json"
            path.write_text(json.dumps(built()), encoding="utf-8")
            code, stdout, stderr = _cli("validate", str(path))
            self.assertEqual(code, 0, stderr)
            self.assertTrue(json.loads(stdout)["ok"])
            path.write_text("{}", encoding="utf-8")
            code, stdout, _stderr = _cli("validate", str(path))
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(stdout)["ok"])
            path.write_bytes(b"\xff")
            code, stdout, _stderr = _cli("validate", str(path))
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(stdout)["codes"], ["record.json"])
            code, _stdout, stderr = _cli("validate", temp)
            self.assertEqual(code, 2)
            self.assertIn("refused: io:", stderr)
            path.write_text(json.dumps(built()), encoding="utf-8")
            accepted, accepted_out, accepted_err = _cli("gate", str(path))
            self.assertEqual(accepted, 0, accepted_err)
            self.assertTrue(json.loads(accepted_out)["accepted"])
            forged = built()
            forged["result"]["verified_blocker"] = False
            path.write_text(json.dumps(forged), encoding="utf-8")
            rejected, rejected_out, _rejected_err = _cli("gate", str(path))
            self.assertEqual(rejected, 1)
            self.assertEqual(json.loads(rejected_out)["code"], "result.forged_blocker")
            out = Path(temp) / "bundle"
            code, _stdout, stderr = _cli("export", "--dry-run", "--out", str(out))
            self.assertEqual(code, 2)
            self.assertIn("export.dry_run", stderr)
            code, _stdout, stderr = _cli("export", "--publish")
            self.assertEqual(code, 2)
            self.assertIn("export.publish_disabled", stderr)
            code, _stdout, stderr = _cli("export", "--token", "hub-" + "marker")
            self.assertEqual(code, 2)
            self.assertIn("export.token", stderr)
            self.assertNotIn("hub-marker", stderr)
        for args in (
            ("generate", "--dry-run", "--seed", "-1", "--count", "1"),
            ("generate", "--dry-run", "--seed", "1", "--count", "0"),
        ):
            with self.subTest(args=args):
                code, _stdout, stderr = _cli(*args)
                self.assertEqual(code, 2)
                self.assertIn("refused:", stderr)

    def test_script_entry_point_plans_a_dry_run(self):
        import pipelines.honest_stop_cli as entry

        self.assertTrue(callable(entry.main))
        argv = [str(SCRIPT_PATH), "generate", "--dry-run", "--seed", "1", "--count", "1"]
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", argv),
            redirect_stdout(stdout),
            self.assertRaises(SystemExit) as caught,
        ):
            runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
        self.assertEqual(caught.exception.code, 0)
        self.assertTrue(json.loads(stdout.getvalue())["dry_run"])

    def test_export_removes_a_destination_when_the_write_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            out.mkdir()
            with self.assertRaises(cv.FamilyError) as caught:
                write_stub(out)
            self.assertEqual(caught.exception.code, "export.exists")
            out.rmdir()
            with (
                mock.patch("honest_stop.export_stub.Path.write_text", side_effect=OSError("full")),
                self.assertRaises(OSError),
            ):
                write_stub(out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
