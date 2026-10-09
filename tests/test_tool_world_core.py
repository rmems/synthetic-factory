#!/usr/bin/env python3
"""The tool-world core: schema subset, seeded faults, packs and catalogs, environment, predicates.

Every test runs on the committed ``counter-workspace`` pack, copied into a
temporary directory whenever it has to be corrupted, so the committed catalog
pins are never read or edited.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world import catalog as catalog_mod
from tool_world import env as env_mod
from tool_world import faults as faults_mod
from tool_world import pack as pack_mod
from tool_world import predicates, schema_lite
from tool_world import vocabulary as cv
from tool_world._contract import rng, sha256_bytes, sha256_canonical

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
DELETE_LOCK = "counter.delete-stale-lock"
RENAME = "counter.rename-config-key"
COMMITTED_TASKS = (ADD_SUB, DELETE_LOCK, RENAME)
FACTORY = "tool-world-workspace-factory"
SEEDS = (0, 1, 2, 3, 7)
HEX64 = "0" * 64

refusal = support.refusal


def call(name: str, **args) -> dict:
    return {"name": name, "args": args}


def plain_env(task_id: str, seed: int = 0, **replace) -> env_mod.Environment:
    """An environment on the task with its fault menu removed unless ``replace`` says otherwise."""
    pack = support.load_pack(PACK)
    fields = {"faults": ()}
    fields.update(replace)
    return env_mod.Environment(pack, dataclasses.replace(pack.task(task_id), **fields), seed)


def fault_row(**overrides) -> dict:
    row = {
        "id": "f",
        "surface": "workspace",
        "kind": "transient_error",
        "tool": "run_tests",
        "marker": "EAGAIN",
    }
    row.update(overrides)
    return row


def spec(**overrides) -> faults_mod.FaultSpec:
    return faults_mod.fault_spec_from_row(fault_row(**overrides), "t")


RECOVERY_ROW = {"intent": "read the file again", "tool_call": call("read_file", path="x")}


def armed(entry: faults_mod.FaultSpec, occurrence: int = 1) -> faults_mod.ScheduledFault:
    return faults_mod.ScheduledFault(entry, True, occurrence)


# --- schema_lite -------------------------------------------------------------


class SchemaLite(unittest.TestCase):
    def test_every_supported_type_accepts_its_values_and_refuses_the_others(self):
        samples = {
            "object": {"k": 1},
            "string": "s",
            "integer": 3,
            "number": 2.5,
            "boolean": True,
            "array": [1],
            "null": None,
        }
        for declared, value in samples.items():
            with self.subTest(type=declared):
                self.assertEqual(schema_lite.validate_args({"type": declared}, value), [])
                others = [other for other, item in samples.items() if other != declared]
                for other in others:
                    if declared == "number" and other == "integer":
                        continue
                    findings = schema_lite.validate_args({"type": declared}, samples[other])
                    self.assertEqual(len(findings), 1, (declared, other, findings))
                    self.assertTrue(findings[0].startswith(f"args: expected {declared}, got "))

    def test_a_bool_is_never_an_integer_or_a_number(self):
        self.assertEqual(
            schema_lite.validate_args({"type": "integer"}, True),
            ["args: expected integer, got bool"],
        )
        self.assertEqual(
            schema_lite.validate_args({"type": "number"}, False),
            ["args: expected number, got bool"],
        )
        self.assertEqual(schema_lite.validate_args({"type": "number"}, 7), [])
        self.assertEqual(
            schema_lite.validate_args({"type": "integer"}, 7.0),
            ["args: expected integer, got float"],
        )

    def test_required_properties_bounds_enum_and_min_length(self):
        schema = {
            "type": "object",
            "required": ["name", "count"],
            "properties": {
                "name": {"type": "string", "minLength": 2, "description": "ignored"},
                "count": {"type": "integer", "minimum": 1, "maximum": 5},
                "mode": {"enum": ["fast", "slow"]},
            },
        }
        self.assertEqual(
            schema_lite.validate_args(schema, {"name": "ok", "count": 3, "mode": "fast"}), []
        )
        self.assertEqual(
            schema_lite.validate_args(schema, {"name": "x", "count": 0, "mode": "warp"}),
            [
                "args.name: must be at least 2 characters",
                "args.count: must be at least 1",
                "args.mode: must be one of ['fast', 'slow']",
            ],
        )
        self.assertEqual(
            schema_lite.validate_args(schema, {"count": 9}),
            ["args: missing required property 'name'", "args.count: must be at most 5"],
        )

    def test_additional_properties_false_names_every_stray_key(self):
        schema = {"type": "object", "properties": {"path": {"type": "string"}}}
        self.assertEqual(schema_lite.validate_args(schema, {"path": "a", "extra": 1}), [])
        strict = dict(schema, additionalProperties=False)
        self.assertEqual(
            schema_lite.validate_args(strict, {"path": "a", "extra": 1, "more": 2}),
            ["args: unexpected property 'extra'", "args: unexpected property 'more'"],
        )

    def test_nested_items_are_validated_with_their_index_in_the_path(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["k"],
                "properties": {"k": {"type": "integer", "minimum": 1}},
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema_lite.validate_args(schema, [{"k": 1}, {"k": 2}]), [])
        self.assertEqual(
            schema_lite.validate_args(schema, [{"k": 0}, {"x": 1}, "s"]),
            [
                "args[0].k: must be at least 1",
                "args[1]: missing required property 'k'",
                "args[1]: unexpected property 'x'",
                "args[2]: expected object, got str",
            ],
        )
        self.assertEqual(schema_lite.validate_args({"type": "array"}, ["anything"]), [])

    def test_a_type_mismatch_short_circuits_the_other_findings(self):
        schema = {"type": "object", "required": ["k"], "enum": [{"k": 1}]}
        self.assertEqual(schema_lite.validate_args(schema, 5), ["args: expected object, got int"])

    def test_check_schema_names_unsupported_keywords_and_types_by_path(self):
        schema = {
            "type": "object",
            "pattern": "x",
            "properties": {
                "a": {"type": "decimal"},
                "b": {"type": "array", "items": {"oneOf": []}},
            },
        }
        self.assertEqual(
            schema_lite.check_schema(schema),
            [
                "schema: unsupported keyword 'pattern'",
                "schema.a: unsupported type 'decimal'",
                "schema.b.items: unsupported keyword 'oneOf'",
            ],
        )
        self.assertEqual(schema_lite.check_schema([], "where"), ["where: schema must be an object"])
        self.assertEqual(
            schema_lite.check_schema({"properties": []}), ["schema: properties must be an object"]
        )
        self.assertEqual(
            schema_lite.check_schema(
                {
                    key: None
                    for key in schema_lite.SUPPORTED_KEYWORDS - {"properties", "items", "type"}
                }
            ),
            [],
        )


# --- faults ------------------------------------------------------------------


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

    def test_row_defaults_and_refusals(self):
        parsed = spec()
        self.assertEqual(
            (parsed.occurrence, parsed.min_occurrence, parsed.max_occurrence),
            (1, 1, 1),
        )
        self.assertEqual(
            (parsed.probability_percent, parsed.retry, parsed.recovery), (100, True, ())
        )
        self.assertEqual((parsed.selector, parsed.params), ({}, {}))
        bad_rows = (
            ("not an object", "fault must be an object"),
            (fault_row(id=7), "fault field 'id' must be str"),
            (fault_row(marker=None), "fault field 'marker' must be str"),
            (fault_row(occurrence=-1), "occurrence must be a non-negative integer"),
            (fault_row(occurrence=True), "occurrence must be a non-negative integer"),
            (fault_row(min_occurrence=3, max_occurrence=2), "1 <= min <= max"),
            (fault_row(min_occurrence=0), "1 <= min <= max"),
            (fault_row(probability_percent=101), "[0, 100]"),
            (fault_row(selector=[]), "selector must be an object"),
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
        for row, needle in bad_rows:
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


# --- packs and catalogs ----------------------------------------------------


class PackCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-core-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def copy_pack(self, name: str = PACK) -> Path:
        destination = Path(tempfile.mkdtemp(dir=self.root)) / name
        shutil.copytree(support.CATALOG_DIR / PACK, destination)
        return destination

    @staticmethod
    def rewrite_json(path: Path, mutate) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    def corrupted(self, mutate) -> Path:
        directory = self.copy_pack()
        mutate(directory)
        return directory


def _task_edit(mutate):
    def apply(directory: Path) -> None:
        PackCase.rewrite_json(directory / "tasks" / "add-sub.json", mutate)

    return apply


def _header_edit(mutate):
    def apply(directory: Path) -> None:
        PackCase.rewrite_json(directory / pack_mod.PACK_FILENAME, mutate)

    return apply


def _suite_edit(mutate):
    def apply(directory: Path) -> None:
        PackCase.rewrite_json(directory / "tests" / "unit.json", mutate)

    return apply


def _set(key, value):
    def mutate(payload):
        payload[key] = value

    return mutate


def _drop(key):
    def mutate(payload):
        del payload[key]

    return mutate


PACK_CORRUPTIONS = (
    (
        "missing PACK.json",
        lambda d: (d / "PACK.json").unlink(),
        cv.FINDING_PACK_FILE_MISSING,
        "missing PACK.json",
    ),
    (
        "bad format",
        _header_edit(_set("format", "pack/0")),
        cv.FINDING_PACK_FIELD_INVALID,
        "format must be",
    ),
    (
        "header not an object",
        lambda d: (d / "PACK.json").write_text("[]"),
        cv.FINDING_PACK_FIELD_INVALID,
        "must be an object",
    ),
    (
        "pack_id not a slug",
        _header_edit(_set("pack_id", "Counter Workspace")),
        cv.FINDING_PACK_FIELD_INVALID,
        "pack_id must be a slug",
    ),
    (
        "license lacks authorship",
        _header_edit(lambda p: p["license"].pop("authorship")),
        cv.FINDING_PACK_FIELD_INVALID,
        "license must carry",
    ),
    (
        "header surfaces unknown",
        _header_edit(_set("surfaces", ["shell"])),
        cv.FINDING_PACK_FIELD_INVALID,
        "surfaces must be",
    ),
    (
        "unknown member directory",
        lambda d: (d / "extras").mkdir(),
        cv.FINDING_PACK_MEMBER_INVALID,
        "unexpected members ['extras']",
    ),
    (
        "stray file",
        lambda d: (d / "notes.txt").write_text("x"),
        cv.FINDING_PACK_MEMBER_INVALID,
        "unexpected members ['notes.txt']",
    ),
    (
        "non-UTF-8 member",
        lambda d: (d / "files" / "blob.bin").write_bytes(b"\xff\xfe\x00"),
        cv.FINDING_PACK_MEMBER_INVALID,
        "blob.bin is not UTF-8",
    ),
    (
        "oversized member",
        lambda d: (d / "files" / "big.txt").write_bytes(b"x" * (cv.MAX_PACK_MEMBER_BYTES + 1)),
        cv.FINDING_PACK_MEMBER_INVALID,
        f"exceeds {cv.MAX_PACK_MEMBER_BYTES} bytes",
    ),
    (
        "task not strict JSON",
        lambda d: (d / "tasks" / "add-sub.json").write_text('{"a": 1, "a": 2}'),
        cv.FINDING_PACK_MEMBER_INVALID,
        "not strict JSON",
    ),
    (
        "task not an object",
        lambda d: (d / "tasks" / "add-sub.json").write_text("[]"),
        cv.FINDING_TASK_FIELD_INVALID,
        "task must be an object",
    ),
    (
        "task_id malformed",
        _task_edit(_set("task_id", "Add Sub!")),
        cv.FINDING_TASK_FIELD_INVALID,
        "is malformed",
    ),
    (
        "task_id missing",
        _task_edit(_drop("task_id")),
        cv.FINDING_TASK_FIELD_INVALID,
        "task_id must be a nonempty string",
    ),
    (
        "title blank",
        _task_edit(_set("title", "  ")),
        cv.FINDING_TASK_FIELD_INVALID,
        "title must be a nonempty string",
    ),
    (
        "surfaces not declared by the pack",
        _task_edit(_set("surfaces", ["mcp"])),
        cv.FINDING_TASK_FIELD_INVALID,
        "not all declared by the pack",
    ),
    (
        "surfaces unknown",
        _task_edit(_set("surfaces", ["shell"])),
        cv.FINDING_TASK_FIELD_INVALID,
        "surfaces must be a nonempty list",
    ),
    (
        "max_steps zero",
        _task_edit(_set("max_steps", 0)),
        cv.FINDING_TASK_FIELD_INVALID,
        "max_steps must be",
    ),
    (
        "max_steps over ceiling",
        _task_edit(_set("max_steps", cv.MAX_STEPS_CEILING + 1)),
        cv.FINDING_TASK_FIELD_INVALID,
        "max_steps must be",
    ),
    (
        "gold empty",
        _task_edit(_set("gold", [])),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold must be a nonempty list",
    ),
    (
        "gold action without tool_call",
        _task_edit(_set("gold", [{"intent": "read the file"}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "tool_call must carry",
    ),
    (
        "gold captures not strings",
        _task_edit(lambda p: p["gold"][0].update(captures={"x": 1})),
        cv.FINDING_TASK_FIELD_INVALID,
        "captures must map names to regex strings",
    ),
    (
        "faults not a list",
        _task_edit(_set("faults", {})),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults must be a list",
    ),
    (
        "fault row invalid",
        _task_edit(_set("faults", [{"id": "x"}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults[0]",
    ),
    (
        "predicates not a list",
        _task_edit(_set("public_predicates", {})),
        cv.FINDING_TASK_FIELD_INVALID,
        "must be a list",
    ),
    (
        "predicate params not an object",
        _task_edit(_set("public_predicates", [{"name": "max_steps", "params": 3}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "params must be an object",
    ),
    (
        "unknown predicate",
        _task_edit(_set("hidden_predicates", [{"name": "tests_green", "params": {}}])),
        cv.FINDING_PREDICATE_UNKNOWN,
        "unknown predicate 'tests_green'",
    ),
    (
        "unknown perturbation",
        _task_edit(_set("perturbations", ["skip_tests"])),
        cv.FINDING_TASK_FIELD_INVALID,
        "perturbations must be drawn from",
    ),
    (
        "duplicate task ids",
        lambda d: shutil.copy(d / "tasks" / "add-sub.json", d / "tasks" / "add-sub-again.json"),
        cv.FINDING_TASK_FIELD_INVALID,
        "duplicate task ids",
    ),
    (
        "no tasks",
        lambda d: shutil.rmtree(d / "tasks"),
        cv.FINDING_PACK_FIELD_INVALID,
        "at least one task",
    ),
    (
        "task carries a hidden-reasoning key",
        _task_edit(_set("thought", "x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "add-sub.json: carries a hidden-reasoning key",
    ),
    (
        "gold action carries a hidden-reasoning key",
        _task_edit(lambda p: p["gold"][0].update(chain_of_thought="x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "carries a hidden-reasoning key",
    ),
    (
        "fault carries a hidden-reasoning key",
        _task_edit(lambda p: p["faults"][0].update(reasoning="x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "carries a hidden-reasoning key",
    ),
    (
        "suite carries a hidden-reasoning key",
        _suite_edit(_set("inner_monologue", "x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "unit.json: carries a hidden-reasoning key",
    ),
    (
        "capture regex invalid",
        _task_edit(lambda p: p["gold"][0].update(captures={"x": "("})),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold[0]: capture 'x' is not a valid regex",
    ),
    (
        "capture without a group",
        _task_edit(lambda p: p["gold"][0].update(captures={"x": "pid="})),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold[0]: capture 'x' needs a capturing group",
    ),
    (
        "recovery action without intent",
        _task_edit(
            lambda p: p["faults"][1].update(
                recovery=[{"tool_call": call("read_file", path="src/counter.py")}]
            )
        ),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults[1].recovery[0]: intent must be a nonempty string",
    ),
    (
        "predicate lacks a parameter",
        _task_edit(_set("hidden_predicates", [{"name": "tests_pass", "params": {}}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "hidden_predicates[0]: predicate tests_pass needs suite as str",
    ),
    (
        "predicate takes a stray parameter",
        _task_edit(_set("public_predicates", [{"name": "max_steps", "params": {"n": 3, "x": 1}}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "predicate max_steps does not take ['x']",
    ),
    (
        "predicate on a surface the task lacks",
        _task_edit(_set("hidden_predicates", [{"name": "url_is", "params": {"url": "/"}}])),
        cv.FINDING_SURFACE_UNKNOWN,
        "predicate url_is needs the browser surface, which the task does not use",
    ),
    (
        "suite case not an object",
        _suite_edit(_set("cases", ["x"])),
        cv.FINDING_PACK_FIELD_INVALID,
        "unit.json.cases[0]: a case must be an object",
    ),
    (
        "suite case without a check kind",
        _suite_edit(_set("cases", [{"id": "a", "check": {"path": "x"}}])),
        cv.FINDING_PACK_FIELD_INVALID,
        "a check carrying a kind",
    ),
    (
        "suite without cases",
        _suite_edit(_drop("cases")),
        cv.FINDING_PACK_FIELD_INVALID,
        "unit.json: a suite must be an object with a cases list",
    ),
    (
        "title reads as a failure",
        _task_edit(_set("title", "fix the failing sub test")),
        cv.FINDING_TASK_FIELD_INVALID,
        "title 'fix the failing sub test' contradicts the verdict",
    ),
)


class LoadPack(PackCase):
    def test_the_committed_pack_loads_with_its_members(self):
        pack = support.load_pack(PACK)
        self.assertEqual((pack.pack_id, pack.surfaces), (PACK, ("workspace",)))
        self.assertEqual(pack.license["spdx"], "Apache-2.0")
        self.assertIn("Claude Code", pack.license["authorship"])
        self.assertIn("src/counter.py", pack.files)
        self.assertEqual(set(pack.tests) >= {"unit", "config"}, True)
        self.assertEqual((pack.servers, pack.site, pack.pages, pack.workers), ({}, None, {}, {}))
        self.assertTrue({task.task_id for task in pack.tasks} >= set(COMMITTED_TASKS))
        self.assertEqual(pack.directory, support.CATALOG_DIR / PACK)

    def test_a_task_carries_its_parsed_plan_faults_and_spec_digest(self):
        task = support.load_pack(PACK).task(ADD_SUB)
        self.assertEqual(
            (task.factory, task.surface, task.surfaces), (FACTORY, "workspace", ("workspace",))
        )
        self.assertEqual(task.max_steps, 12)
        self.assertEqual([action.tool_call["name"] for action in task.gold][-1], cv.TOOL_REPORT)
        self.assertEqual(
            [action.verification for action in task.gold], [False, False, False, True, False]
        )
        self.assertEqual(
            [spec.fault_id for spec in task.faults], ["transient-tests", "truncated-read"]
        )
        self.assertEqual(task.faults[1].retry, False)
        self.assertIsInstance(task.faults[1].recovery[0], pack_mod.Action)
        self.assertEqual(task.faults[1].recovery[0].tool_call["name"], "read_file")
        self.assertEqual(task.perturbations, ("give_up_on_fault", "wrong_arg_type"))
        self.assertEqual(
            task.public_predicates, (("value_reported", {"value": "unit suite passes"}),)
        )
        self.assertRegex(task.spec_sha256, r"^[0-9a-f]{64}$")

    def test_an_unknown_task_is_refused(self):
        with refusal(self, cv.FINDING_TASK_NOT_FOUND, "'counter.nope'"):
            support.load_pack(PACK).task("counter.nope")

    def test_missing_directory_and_pack_id_not_matching_the_directory(self):
        with refusal(self, cv.FINDING_PACK_FILE_MISSING, "missing pack directory"):
            pack_mod.load_pack(self.root / "absent")
        with refusal(self, cv.FINDING_PACK_FIELD_INVALID, "equal to the directory name"):
            pack_mod.load_pack(self.copy_pack("other-name"))

    def test_every_corruption_is_a_coded_refusal(self):
        for label, mutate, code, needle in PACK_CORRUPTIONS:
            with self.subTest(label=label), refusal(self, code, needle):
                pack_mod.load_pack(self.corrupted(mutate))

    def test_pack_digest_is_stable_across_locations_and_sensitive_to_every_byte(self):
        committed = support.load_pack(PACK)
        self.assertEqual(committed.pack_sha256, pack_mod.pack_digest(support.CATALOG_DIR / PACK))
        copied = self.copy_pack()
        self.assertEqual(pack_mod.load_pack(copied).pack_sha256, committed.pack_sha256)
        readme = copied / "files" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assertNotEqual(pack_mod.pack_digest(copied), committed.pack_sha256)
        self.assertEqual(pack_mod.load_pack(copied).pack_sha256, pack_mod.pack_digest(copied))
        self.assertRegex(committed.pack_sha256, r"^[0-9a-f]{64}$")


CATALOG_CORRUPTIONS = (
    ("bad format", _set("format", "catalog/0"), "format must be"),
    ("wrong family", _set("family", "mill"), "family must be"),
    ("catalog_id blank", _set("catalog_id", ""), "catalog_id must be"),
    ("packs empty", _set("packs", []), "packs must be a nonempty list"),
    ("pack row malformed", _set("packs", [{"pack_id": PACK}]), "packs[0]: must carry"),
)


class LoadCatalog(PackCase):
    def setUp(self):
        super().setUp()
        self.catalog_dir = support.private_catalog(self.root / "catalog", (PACK,))
        self.header = self.catalog_dir / catalog_mod.CATALOG_FILENAME

    def test_a_private_catalog_loads_and_digests_its_pinned_packs(self):
        loaded = catalog_mod.load_catalog(self.catalog_dir)
        self.assertEqual(
            (loaded.catalog_id, loaded.directory), ("tool-world-test", self.catalog_dir)
        )
        self.assertEqual([pack.pack_id for pack in loaded.packs], [PACK])
        self.assertEqual(loaded.catalog_sha256, catalog_mod.catalog_digest(loaded.packs))
        self.assertEqual(
            loaded.catalog_sha256,
            sha256_canonical([[PACK, loaded.packs[0].pack_sha256]]),
        )
        self.assertIs(loaded.pack(PACK), loaded.packs[0])
        pairs = list(loaded.tasks())
        self.assertTrue({task.task_id for _pack, task in pairs} >= set(COMMITTED_TASKS))
        self.assertEqual(list(loaded.tasks(FACTORY)), pairs)
        self.assertEqual(list(loaded.tasks("tool-world-mcp-factory")), [])
        with refusal(self, cv.FINDING_PACK_FILE_MISSING, "'nope' is not in catalog"):
            loaded.pack("nope")

    def test_the_digest_ignores_catalog_prose_and_follows_pack_bytes(self):
        before = catalog_mod.load_catalog(self.catalog_dir).catalog_sha256
        self.rewrite_json(self.header, _set("notes", "prose only"))
        self.assertEqual(catalog_mod.load_catalog(self.catalog_dir).catalog_sha256, before)
        (self.catalog_dir / PACK / "files" / "extra.txt").write_text("y", encoding="utf-8")
        repinned = pack_mod.load_pack(self.catalog_dir / PACK).pack_sha256
        self.rewrite_json(self.header, _set("packs", [{"pack_id": PACK, "pack_sha256": repinned}]))
        self.assertNotEqual(catalog_mod.load_catalog(self.catalog_dir).catalog_sha256, before)

    def test_missing_catalog_file(self):
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING, "missing CATALOG.json"):
            catalog_mod.load_catalog(self.root / "empty")

    def test_header_corruptions(self):
        for label, mutate, needle in CATALOG_CORRUPTIONS:
            with self.subTest(label=label):
                support.private_catalog(self.catalog_dir, (PACK,))
                self.rewrite_json(self.header, mutate)
                with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, needle):
                    catalog_mod.load_catalog(self.catalog_dir)
        self.header.write_text("{not json", encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "not strict JSON"):
            catalog_mod.load_catalog(self.catalog_dir)
        self.header.write_text("[]", encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "must be an object"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_a_drifted_pin_is_refused(self):
        readme = self.catalog_dir / PACK / "files" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        with refusal(self, cv.FINDING_PACK_SHA_MISMATCH, "is not the pinned"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_duplicate_pack_ids_are_refused(self):
        self.rewrite_json(self.header, lambda p: p["packs"].append(dict(p["packs"][0])))
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "duplicate pack ids"):
            catalog_mod.load_catalog(self.catalog_dir)

    def test_the_default_catalog_is_the_committed_directory(self):
        self.assertEqual(catalog_mod.DEFAULT_CATALOG, support.REPO / "catalogs" / "tool-world-v1")


# --- environment --------------------------------------------------------------


class EnvironmentConstruction(unittest.TestCase):
    def test_tools_include_the_core_tools_and_every_surface_tool(self):
        env = plain_env(DELETE_LOCK)
        names = [tool.name for tool in env.tools()]
        self.assertEqual(names[:2], [cv.TOOL_REPORT, cv.TOOL_CONFIRM])
        self.assertIn("delete_file", names)
        self.assertEqual(len(names), len(set(names)))
        for tool in env.tools():
            with self.subTest(tool=tool.name):
                self.assertEqual(schema_lite.check_schema(tool.input_schema), [])
                declared = tool.declared()
                self.assertEqual(
                    set(declared),
                    {"name", "surface", "description", "input_schema", "irreversible"},
                )
        self.assertEqual(env.tool(cv.TOOL_REPORT).surface, cv.CORE_SURFACE)
        self.assertTrue(env.tool("delete_file").irreversible)
        self.assertFalse(env.tool(cv.TOOL_CONFIRM).irreversible)
        self.assertIsNone(env.tool("nope"))
        self.assertEqual(list(env.surfaces), ["workspace"])

    def test_constructor_refusals(self):
        pack = support.load_pack(PACK)
        with refusal(self, cv.FINDING_SEED_INVALID):
            env_mod.Environment(pack, pack.task(ADD_SUB), -1)
        with refusal(self, cv.FINDING_SEED_INVALID):
            env_mod.Environment(pack, pack.task(ADD_SUB), True)
        with refusal(self, cv.FINDING_SURFACE_UNKNOWN, "unknown surface 'shell'"):
            plain_env(ADD_SUB, surfaces=("shell",))
        with refusal(self, cv.FINDING_FAULT_UNKNOWN, "which the task does not use"):
            plain_env(ADD_SUB, faults=(spec(surface="mcp", tool="mcp"),))
        with refusal(self, cv.FINDING_FAULT_UNKNOWN, "no fault kind 'meteor'"):
            plain_env(ADD_SUB, faults=(spec(kind="meteor"),))
        with refusal(self, cv.FINDING_SURFACE_UNKNOWN, "has no mcp surface"):
            plain_env(ADD_SUB).surface("mcp")

    def test_a_fault_must_name_a_tool_of_its_surface_and_selector_keys_that_tool_takes(self):
        self.assertEqual(
            plain_env(
                ADD_SUB, faults=(spec(tool="read_file", selector={"path": "x"}),)
            ).fault_engine.armed_ids(),
            ("f",),
        )
        cases = (
            (spec(tool="nope"), "names tool 'nope'"),
            (spec(tool=cv.TOOL_REPORT), "names tool 'report_result'"),
            (
                spec(selector={"suit": "unit"}),
                "fault f: selector keys ['suit'] are not arguments of run_tests; known: ['suite']",
            ),
            (
                spec(tool="read_file", selector={"path": "x", "params.name": "y"}),
                "selector keys ['params.name'] are not arguments of read_file",
            ),
        )
        for entry, needle in cases:
            with self.subTest(needle=needle), refusal(self, cv.FINDING_FAULT_UNKNOWN, needle):
                plain_env(ADD_SUB, faults=(entry,))


class EnvironmentStepping(unittest.TestCase):
    def test_an_unknown_tool_is_an_observation_not_a_refusal(self):
        env = plain_env(ADD_SUB)
        before = env.snapshot_digest()
        observation = env.step(call("nope"))
        self.assertTrue(observation.text.startswith("error: unknown tool 'nope'; available: ["))
        self.assertEqual((observation.fault_id, observation.truncated), (None, False))
        self.assertEqual(len(env.events), 1)
        self.assertEqual(env.events[0].row()["tool_call"], call("nope"))
        self.assertEqual(env.snapshot_digest(), before)
        self.assertEqual(env.last_observation_text(), observation.text)

    def test_invalid_arguments_change_no_state_and_count_toward_no_fault(self):
        pack = support.load_pack(PACK)
        env = env_mod.Environment(pack, pack.task(ADD_SUB), 1)
        before = env.snapshot_digest()
        observation = env.step(call("run_tests", suite=7))
        self.assertEqual(
            observation.text,
            "error: invalid arguments for run_tests: args.suite: expected string, got int",
        )
        self.assertEqual(env.snapshot_digest(), before)
        self.assertEqual(env.fault_engine.fired, ())
        self.assertEqual(env.events[0].fault_id, None)
        stray = env.step(call("write_file", path="x", content="y", mode="w"))
        self.assertIn("unexpected property 'mode'", stray.text)
        self.assertEqual(env.snapshot_digest(), before)
        fired = env.step(call("run_tests", suite="unit"))
        self.assertEqual(fired.fault_id, "transient-tests")
        self.assertEqual(env.fault_engine.fired, ("transient-tests",))
        self.assertEqual([event.fault_id for event in env.events], [None, None, "transient-tests"])

    def test_the_budget_is_a_refusal_once_exhausted(self):
        env = plain_env(DELETE_LOCK, max_steps=2)
        self.assertFalse(env.done)
        env.step(call("list_dir", path="locks"))
        env.step(call("list_dir", path="locks"))
        self.assertTrue(env.done)
        with refusal(self, cv.FINDING_BUDGET_EXHAUSTED, "allows 2 steps"):
            env.step(call("list_dir", path="locks"))
        self.assertEqual(len(env.events), 2)

    def test_a_malformed_tool_call_is_refused_without_an_event(self):
        env = plain_env(ADD_SUB)
        for malformed in (
            "read_file",
            {"name": 7, "args": {}},
            {"name": "read_file", "args": []},
            {},
        ):
            with self.subTest(call=malformed), refusal(self, cv.FINDING_TOOL_CALL_MALFORMED):
                env.step(malformed)
        self.assertEqual(env.events, ())

    def test_report_result_and_confirm_action(self):
        env = plain_env(DELETE_LOCK)
        self.assertIsNone(env.reported)
        self.assertEqual(env.step(call(cv.TOOL_REPORT, value="done")).text, "recorded result: done")
        self.assertEqual(env.reported, "done")
        self.assertEqual(
            env.step(call(cv.TOOL_CONFIRM, action="delete_file")).text, "confirmed: delete_file"
        )
        self.assertEqual(
            env.step(call(cv.TOOL_REPORT, value="again")).text, "recorded result: again"
        )
        self.assertEqual(env.reported, "again")
        self.assertIn("missing required property 'value'", env.step(call(cv.TOOL_REPORT)).text)

    def test_irreversible_accounting_consumes_one_matching_confirmation_per_call(self):
        unconfirmed = plain_env(DELETE_LOCK)
        unconfirmed.step(call("delete_file", path="locks/stale.lock"))
        self.assertEqual(unconfirmed.unconfirmed_irreversible, 1)
        self.assertFalse(
            predicates.evaluate("no_irreversible_without_confirmation", {}, unconfirmed)
        )

        confirmed = plain_env(DELETE_LOCK)
        confirmed.step(call(cv.TOOL_CONFIRM, action="delete_file"))
        confirmed.step(call("delete_file", path="locks/stale.lock"))
        self.assertEqual(confirmed.unconfirmed_irreversible, 0)
        self.assertTrue(predicates.evaluate("no_irreversible_without_confirmation", {}, confirmed))
        confirmed.step(call("delete_file", path="README.md"))
        self.assertEqual(confirmed.unconfirmed_irreversible, 1)

        mismatched = plain_env(DELETE_LOCK)
        mismatched.step(call(cv.TOOL_CONFIRM, action="write_file"))
        mismatched.step(call("delete_file", path="locks/stale.lock"))
        self.assertEqual(mismatched.unconfirmed_irreversible, 1)

        missing = plain_env(DELETE_LOCK)
        missing.step(call(cv.TOOL_CONFIRM, action="delete_file"))
        self.assertTrue(
            missing.step(call("delete_file", path="nope")).text.startswith("error: ENOENT")
        )
        self.assertEqual(missing.unconfirmed_irreversible, 0)

        transient = plain_env(DELETE_LOCK, 1, faults=(spec(tool="delete_file"),))
        transient.step(call(cv.TOOL_CONFIRM, action="delete_file"))
        blocked = transient.step(call("delete_file", path="locks/stale.lock"))
        self.assertEqual(blocked.fault_id, "f")
        self.assertTrue(blocked.text.startswith("error: EAGAIN temporary failure"))
        self.assertIn("locks/stale.lock", transient.surface("workspace").files)
        self.assertEqual(transient.unconfirmed_irreversible, 0)
        retried = transient.step(call("delete_file", path="locks/stale.lock"))
        self.assertEqual(retried.text, "deleted locks/stale.lock")
        self.assertEqual(transient.unconfirmed_irreversible, 0)
        self.assertTrue(predicates.evaluate("no_irreversible_without_confirmation", {}, transient))
        transient.step(call("delete_file", path="README.md"))
        self.assertEqual(transient.unconfirmed_irreversible, 1)

    def test_snapshot_and_replay_digests_are_deterministic_functions_of_the_history(self):
        steps = (
            call("read_file", path="README.md"),
            call("write_file", path="docs/new.md", content="hello"),
            call(cv.TOOL_CONFIRM, action="delete_file"),
        )
        envs = [plain_env(DELETE_LOCK, seed) for seed in (0, 0, 7)]
        digests = []
        for env in envs:
            start = env.snapshot_digest()
            for tool_call in steps:
                env.step(tool_call)
            digests.append((start, env.snapshot_digest(), env.replay_digest()))
        self.assertEqual(digests[0], digests[1])
        self.assertEqual(digests[0], digests[2])
        start, after, replay = digests[0]
        self.assertNotEqual(start, after)
        self.assertEqual(
            replay,
            sha256_canonical(
                [
                    [event.n, event.row()["tool_call"], event.observation_sha256, event.fault_id]
                    for event in envs[0].events
                ]
            ),
        )
        self.assertEqual(plain_env(DELETE_LOCK).replay_digest(), sha256_canonical([]))
        read_only = plain_env(DELETE_LOCK)
        read_only.step(call("read_file", path="README.md"))
        read_only.step(call("search", pattern="counter"))
        self.assertEqual(read_only.snapshot_digest(), start)
        self.assertNotEqual(read_only.replay_digest(), sha256_canonical([]))

    def test_the_replay_digest_covers_the_arguments_not_only_the_tool_name(self):
        plain, limited = plain_env(DELETE_LOCK), plain_env(DELETE_LOCK)
        first = plain.step(call("read_file", path="README.md"))
        second = limited.step(call("read_file", path="README.md", limit=4000))
        self.assertEqual(first.text, second.text)
        self.assertEqual(plain.snapshot_digest(), limited.snapshot_digest())
        self.assertNotEqual(plain.replay_digest(), limited.replay_digest())

    def test_observations_are_bounded_and_digested_over_the_full_text(self):
        env = plain_env(ADD_SUB)
        body = "x" * (cv.MAX_OBSERVATION_CHARS + 500)
        env.step(call("write_file", path="big.txt", content=body))
        observation = env.step(call("read_file", path="big.txt"))
        full = f"big.txt ({len(body)} chars, offset 0):\n{body}"
        omitted = len(full) - cv.MAX_OBSERVATION_CHARS
        self.assertTrue(observation.truncated)
        self.assertEqual(
            observation.text, full[: cv.MAX_OBSERVATION_CHARS] + f"\n[truncated {omitted} chars]"
        )
        self.assertEqual(observation.full_sha256, sha256_bytes(full.encode("utf-8")))
        self.assertEqual(env.events[-1].truncated, True)
        self.assertEqual(env.events[-1].observation_sha256, observation.full_sha256)
        self.assertEqual(env_mod.bound_observation("short"), ("short", False))
        exact = "y" * cv.MAX_OBSERVATION_CHARS
        self.assertEqual(env_mod.bound_observation(exact), (exact, False))

    def test_the_verdict_names_every_predicate_by_a_stable_label(self):
        env = plain_env(DELETE_LOCK)
        self.assertEqual(
            env.verdict(),
            {
                "public": {"value_reported:value=stale lock removed": False},
                "hidden": {
                    "file_absent:path=locks/stale.lock": False,
                    "no_irreversible_without_confirmation": True,
                },
                "success": False,
            },
        )
        env.step(call(cv.TOOL_CONFIRM, action="delete_file"))
        env.step(call("delete_file", path="locks/stale.lock"))
        env.step(call(cv.TOOL_REPORT, value="stale lock removed"))
        verdict = env.verdict()
        self.assertIs(verdict["success"], True)
        self.assertTrue(all(verdict["public"].values()) and all(verdict["hidden"].values()))

    def test_event_rows_carry_the_call_the_digest_and_the_fault(self):
        env = plain_env(ADD_SUB)
        observation = env.step(call("list_dir", path="src"))
        self.assertEqual(
            env.events[0].row(),
            {
                "n": 1,
                "tool_call": call("list_dir", path="src"),
                "observation_sha256": observation.full_sha256,
                "fault_id": None,
                "truncated": False,
            },
        )


# --- predicates -------------------------------------------------------------


WORKSPACE_PARAMS = {
    "tests_pass": {"suite": "unit"},
    "file_sha256": {
        "path": "locks/stale.lock",
        "sha256": sha256_bytes(b"pid=4242 started=2026-01-01T00:00:00Z\n"),
    },
    "file_contains": {"path": "README.md", "text": "counter"},
    "file_exists": {"path": "README.md"},
    "file_absent": {"path": "missing.txt"},
    "value_reported": {"value": "x"},
    "max_steps": {"n": 3},
    "no_irreversible_without_confirmation": {},
}
FILE_NAMES = frozenset({"tests_pass", "file_sha256", "file_contains", "file_exists", "file_absent"})
FOREIGN_PARAMS = {
    "resource_read": {"server": "s", "uri": "u"},
    "tool_called": {"server": "s", "tool": "t"},
    "listed_before_call": {"server": "s"},
    "url_is": {"url": "u"},
    "extracted_equals": {"value": "v"},
    "form_submitted": {"form": "f"},
    "verified_before_merge": {},
    "no_agents_pending": {},
    "max_agents": {"n": 1},
}


class Predicates(unittest.TestCase):
    def test_the_tables_cover_the_closed_vocabulary(self):
        self.assertEqual(
            set(WORKSPACE_PARAMS) | set(FOREIGN_PARAMS), set(predicates.PREDICATE_NAMES)
        )
        self.assertEqual(set(WORKSPACE_PARAMS) & set(FOREIGN_PARAMS), set())

    def test_every_predicate_declares_its_surface_and_parameters(self):
        self.assertEqual(set(predicates.PREDICATE_SPECS), set(predicates.PREDICATE_NAMES))
        for name, params in {**WORKSPACE_PARAMS, **FOREIGN_PARAMS}.items():
            surface, declared = predicates.PREDICATE_SPECS[name]
            with self.subTest(predicate=name):
                self.assertEqual(set(declared), set(params))
                self.assertIn(surface, (None, *cv.SURFACES))
                if name in WORKSPACE_PARAMS:
                    self.assertEqual(surface, "workspace" if name in FILE_NAMES else None)
                predicates.check_declaration(name, params, cv.SURFACES, "row")
        self.assertIsNone(predicates.PREDICATE_SPECS["max_steps"][0])
        self.assertEqual(predicates.PREDICATE_SPECS["url_is"][0], "browser")

    def test_check_declaration_refuses_what_the_loader_must_not_accept(self):
        cases = (
            (
                "tests_green",
                {},
                cv.FINDING_PREDICATE_UNKNOWN,
                "row: unknown predicate 'tests_green'",
            ),
            ("tests_pass", {}, cv.FINDING_TASK_FIELD_INVALID, "needs suite as str"),
            ("max_steps", {"n": True}, cv.FINDING_TASK_FIELD_INVALID, "needs n as int"),
            ("max_steps", {"n": 1, "m": 2}, cv.FINDING_TASK_FIELD_INVALID, "does not take ['m']"),
            (
                "file_sha256",
                {"path": 1},
                cv.FINDING_TASK_FIELD_INVALID,
                "row: predicate file_sha256 needs path as str; predicate file_sha256 needs sha256",
            ),
            ("url_is", {"url": "/"}, cv.FINDING_SURFACE_UNKNOWN, "needs the browser surface"),
        )
        for name, params, code, needle in cases:
            with self.subTest(predicate=name, params=params), refusal(self, code, needle):
                predicates.check_declaration(name, params, ("workspace",), "row")
        predicates.check_declaration("max_steps", {"n": 1}, (), "row")

    def test_every_workspace_predicate_evaluates_to_a_bool_on_the_pack(self):
        env = plain_env(DELETE_LOCK)
        expected = {
            "tests_pass": False,
            "file_sha256": True,
            "file_contains": True,
            "file_exists": True,
            "file_absent": True,
            "value_reported": False,
            "max_steps": True,
            "no_irreversible_without_confirmation": True,
        }
        for name, params in WORKSPACE_PARAMS.items():
            with self.subTest(predicate=name):
                verdict = predicates.evaluate(name, params, env)
                self.assertIs(verdict, expected[name])

    def test_every_foreign_predicate_refuses_the_surface_the_task_lacks(self):
        env = plain_env(DELETE_LOCK)
        for name, params in FOREIGN_PARAMS.items():
            with self.subTest(predicate=name), refusal(self, cv.FINDING_SURFACE_UNKNOWN, "has no"):
                predicates.evaluate(name, params, env)

    def test_unknown_predicate_and_bad_params_are_refused(self):
        env = plain_env(DELETE_LOCK)
        with refusal(self, cv.FINDING_PREDICATE_UNKNOWN, "unknown predicate 'tests_green'"):
            predicates.evaluate("tests_green", {}, env)
        bad = (
            ("tests_pass", {"suite": 3}, "needs suite as str"),
            ("max_steps", {"n": True}, "needs n as int"),
            ("max_steps", {}, "needs n as int"),
            ("file_sha256", {"path": "README.md"}, "needs sha256 as str"),
            ("value_reported", {"value": None}, "needs value as str"),
        )
        for name, params, needle in bad:
            with self.subTest(predicate=name), refusal(self, cv.FINDING_TASK_FIELD_INVALID, needle):
                predicates.evaluate(name, params, env)

    def test_predicates_follow_the_state_the_tools_change(self):
        env = plain_env(ADD_SUB)
        self.assertFalse(predicates.evaluate("tests_pass", {"suite": "unit"}, env))
        env.step(
            call(
                "write_file",
                path="src/counter.py",
                content=(
                    "def add(self, delta):\ndef sub(self, delta):\n    self._value -= int(delta)\n"
                ),
            )
        )
        self.assertTrue(predicates.evaluate("tests_pass", {"suite": "unit"}, env))
        self.assertTrue(
            predicates.evaluate(
                "file_sha256",
                {
                    "path": "src/counter.py",
                    "sha256": sha256_bytes(
                        env.surface("workspace").files["src/counter.py"].encode("utf-8")
                    ),
                },
                env,
            )
        )
        env.step(call(cv.TOOL_REPORT, value="x"))
        self.assertTrue(predicates.evaluate("value_reported", {"value": "x"}, env))
        self.assertFalse(predicates.evaluate("value_reported", {"value": "y"}, env))
        self.assertTrue(predicates.evaluate("max_steps", {"n": 2}, env))
        self.assertFalse(predicates.evaluate("max_steps", {"n": 1}, env))
        with refusal(self, cv.FINDING_PACK_FIELD_INVALID, "must declare a cases list"):
            predicates.evaluate("tests_pass", {"suite": "nope"}, env)

    def test_evaluate_all_labels_params_in_sorted_order(self):
        env = plain_env(DELETE_LOCK)
        rows = (
            ("file_contains", {"text": "counter", "path": "README.md"}),
            ("no_irreversible_without_confirmation", {}),
        )
        self.assertEqual(
            predicates.evaluate_all(rows, env),
            {
                "file_contains:path=README.md,text=counter": True,
                "no_irreversible_without_confirmation": True,
            },
        )
        self.assertEqual(predicates.evaluate_all((), env), {})


if __name__ == "__main__":
    unittest.main()
