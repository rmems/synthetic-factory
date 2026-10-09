#!/usr/bin/env python3
"""Loading a world pack: its members, tasks and digest, and every corruption it refuses.

Each corruption edits a private copy of the committed ``counter-workspace``
pack; the committed catalog pins are never read or edited.
"""

from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world_pack_support import (
    ADD_SUB,
    COMMITTED_TASKS,
    FACTORY,
    PACK,
    call,
    copy_pack,
    corrupted,
    drop_key,
    refusal,
    rewrite_json,
    sandbox,
    set_key,
)

# The support modules go first: they put pipelines/ on sys.path for the imports below.
# isort: split
from tool_world import pack as pack_mod
from tool_world import vocabulary as cv


def task_edit(mutate):
    def apply(directory: Path) -> None:
        rewrite_json(directory / "tasks" / "add-sub.json", mutate)

    return apply


def header_edit(mutate):
    def apply(directory: Path) -> None:
        rewrite_json(directory / pack_mod.PACK_FILENAME, mutate)

    return apply


def suite_edit(mutate):
    def apply(directory: Path) -> None:
        rewrite_json(directory / "tests" / "unit.json", mutate)

    return apply


PACK_CORRUPTIONS = (
    (
        "missing PACK.json",
        lambda d: (d / "PACK.json").unlink(),
        cv.FINDING_PACK_FILE_MISSING,
        "missing PACK.json",
    ),
    (
        "bad format",
        header_edit(set_key("format", "pack/0")),
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
        header_edit(set_key("pack_id", "Counter Workspace")),
        cv.FINDING_PACK_FIELD_INVALID,
        "pack_id must be a slug",
    ),
    (
        "pack_id with a trailing newline",
        header_edit(set_key("pack_id", PACK + "\n")),
        cv.FINDING_PACK_FIELD_INVALID,
        "pack_id must be a slug",
    ),
    (
        "license lacks authorship",
        header_edit(lambda p: p["license"].pop("authorship")),
        cv.FINDING_PACK_FIELD_INVALID,
        "license must carry",
    ),
    (
        "header surfaces unknown",
        header_edit(set_key("surfaces", ["shell"])),
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
        task_edit(set_key("task_id", "Add Sub!")),
        cv.FINDING_TASK_FIELD_INVALID,
        "is malformed",
    ),
    (
        "task_id with a trailing newline",
        task_edit(set_key("task_id", "counter.add-sub\n")),
        cv.FINDING_TASK_FIELD_INVALID,
        "is malformed",
    ),
    (
        "task_id missing",
        task_edit(drop_key("task_id")),
        cv.FINDING_TASK_FIELD_INVALID,
        "task_id must be a nonempty string",
    ),
    (
        "title blank",
        task_edit(set_key("title", "  ")),
        cv.FINDING_TASK_FIELD_INVALID,
        "title must be a nonempty string",
    ),
    (
        "surfaces not declared by the pack",
        task_edit(set_key("surfaces", ["mcp"])),
        cv.FINDING_TASK_FIELD_INVALID,
        "not all declared by the pack",
    ),
    (
        "surfaces unknown",
        task_edit(set_key("surfaces", ["shell"])),
        cv.FINDING_TASK_FIELD_INVALID,
        "surfaces must be a nonempty list",
    ),
    (
        "max_steps zero",
        task_edit(set_key("max_steps", 0)),
        cv.FINDING_TASK_FIELD_INVALID,
        "max_steps must be",
    ),
    (
        "max_steps over ceiling",
        task_edit(set_key("max_steps", cv.MAX_STEPS_CEILING + 1)),
        cv.FINDING_TASK_FIELD_INVALID,
        "max_steps must be",
    ),
    (
        "gold empty",
        task_edit(set_key("gold", [])),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold must be a nonempty list",
    ),
    (
        "gold action without tool_call",
        task_edit(set_key("gold", [{"intent": "read the file"}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "tool_call must carry",
    ),
    (
        "gold captures not strings",
        task_edit(lambda p: p["gold"][0].update(captures={"x": 1})),
        cv.FINDING_TASK_FIELD_INVALID,
        "captures must map names to regex strings",
    ),
    (
        "faults not a list",
        task_edit(set_key("faults", {})),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults must be a list",
    ),
    (
        "fault row invalid",
        task_edit(set_key("faults", [{"id": "x"}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults[0]",
    ),
    (
        "predicates not a list",
        task_edit(set_key("public_predicates", {})),
        cv.FINDING_TASK_FIELD_INVALID,
        "must be a list",
    ),
    (
        "predicate params not an object",
        task_edit(set_key("public_predicates", [{"name": "max_steps", "params": 3}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "params must be an object",
    ),
    (
        "unknown predicate",
        task_edit(set_key("hidden_predicates", [{"name": "tests_green", "params": {}}])),
        cv.FINDING_PREDICATE_UNKNOWN,
        "unknown predicate 'tests_green'",
    ),
    (
        "unknown perturbation",
        task_edit(set_key("perturbations", ["skip_tests"])),
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
        task_edit(set_key("thought", "x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "add-sub.json: carries a hidden-reasoning key",
    ),
    (
        "gold action carries a hidden-reasoning key",
        task_edit(lambda p: p["gold"][0].update(chain_of_thought="x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "carries a hidden-reasoning key",
    ),
    (
        "fault carries a hidden-reasoning key",
        task_edit(lambda p: p["faults"][0].update(reasoning="x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "carries a hidden-reasoning key",
    ),
    (
        "suite carries a hidden-reasoning key",
        suite_edit(set_key("inner_monologue", "x")),
        cv.FINDING_PACK_MEMBER_INVALID,
        "unit.json: carries a hidden-reasoning key",
    ),
    (
        "capture regex invalid",
        task_edit(lambda p: p["gold"][0].update(captures={"x": "("})),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold[0]: capture 'x' is not a valid regex",
    ),
    (
        "capture without a group",
        task_edit(lambda p: p["gold"][0].update(captures={"x": "pid="})),
        cv.FINDING_TASK_FIELD_INVALID,
        "gold[0]: capture 'x' needs a capturing group",
    ),
    (
        "recovery action without intent",
        task_edit(
            lambda p: p["faults"][1].update(
                recovery=[{"tool_call": call("read_file", path="src/counter.py")}]
            )
        ),
        cv.FINDING_TASK_FIELD_INVALID,
        "faults[1].recovery[0]: intent must be a nonempty string",
    ),
    (
        "predicate lacks a parameter",
        task_edit(set_key("hidden_predicates", [{"name": "tests_pass", "params": {}}])),
        cv.FINDING_TASK_FIELD_INVALID,
        "hidden_predicates[0]: predicate tests_pass needs suite as str",
    ),
    (
        "predicate takes a stray parameter",
        task_edit(
            set_key("public_predicates", [{"name": "max_steps", "params": {"n": 3, "x": 1}}])
        ),
        cv.FINDING_TASK_FIELD_INVALID,
        "predicate max_steps does not take ['x']",
    ),
    (
        "predicate on a surface the task lacks",
        task_edit(set_key("hidden_predicates", [{"name": "url_is", "params": {"url": "/"}}])),
        cv.FINDING_SURFACE_UNKNOWN,
        "predicate url_is needs the browser surface, which the task does not use",
    ),
    (
        "suite case not an object",
        suite_edit(set_key("cases", ["x"])),
        cv.FINDING_PACK_FIELD_INVALID,
        "unit.json.cases[0]: a case must be an object",
    ),
    (
        "suite case without a check kind",
        suite_edit(set_key("cases", [{"id": "a", "check": {"path": "x"}}])),
        cv.FINDING_PACK_FIELD_INVALID,
        "a check carrying a kind",
    ),
    (
        "suite without cases",
        suite_edit(drop_key("cases")),
        cv.FINDING_PACK_FIELD_INVALID,
        "unit.json: a suite must be an object with a cases list",
    ),
    (
        "title reads as a failure",
        task_edit(set_key("title", "fix the failing sub test")),
        cv.FINDING_TASK_FIELD_INVALID,
        "title 'fix the failing sub test' contradicts the verdict",
    ),
)


class LoadPack(unittest.TestCase):
    def setUp(self):
        self.root = sandbox(self)

    def test_the_committed_pack_loads_with_its_members(self):
        pack = support.load_pack(PACK)
        self.assertEqual((pack.pack_id, pack.surfaces), (PACK, ("workspace",)))
        self.assertEqual(pack.license["spdx"], "Apache-2.0")
        self.assertIn("Claude Code", pack.license["authorship"])
        self.assertIn("src/counter.py", pack.files)
        self.assertGreaterEqual(set(pack.tests), {"unit", "config"})
        self.assertEqual((pack.servers, pack.site, pack.pages, pack.workers), ({}, None, {}, {}))
        self.assertGreaterEqual({task.task_id for task in pack.tasks}, set(COMMITTED_TASKS))
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
        self.assertFalse(task.faults[1].retry)
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
            pack_mod.load_pack(copy_pack(self.root, "other-name"))

    def test_every_corruption_is_a_coded_refusal(self):
        for label, mutate, code, needle in PACK_CORRUPTIONS:
            with self.subTest(label=label), refusal(self, code, needle):
                pack_mod.load_pack(corrupted(self.root, mutate))

    def test_pack_digest_is_stable_across_locations_and_sensitive_to_every_byte(self):
        committed = support.load_pack(PACK)
        self.assertEqual(committed.pack_sha256, pack_mod.pack_digest(support.CATALOG_DIR / PACK))
        copied = copy_pack(self.root)
        self.assertEqual(pack_mod.load_pack(copied).pack_sha256, committed.pack_sha256)
        readme = copied / "files" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assertNotEqual(pack_mod.pack_digest(copied), committed.pack_sha256)
        self.assertEqual(pack_mod.load_pack(copied).pack_sha256, pack_mod.pack_digest(copied))
        self.assertRegex(committed.pack_sha256, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
