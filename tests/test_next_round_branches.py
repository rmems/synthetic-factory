"""Branch coverage for next_round.py: legacy scanning, plans, the index writer and CLI exits.

next_round is advisory: it never reserves a round, refuses an occupied target
with exit 1, and --write-index refreshes only NEXT_ROUND.json under the root.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import next_round
from round_txn import MODE_FILE


def _write_lines(path, *lines):
    path.write_text("".join(line + "\n" for line in lines))


def _run_main(*argv):
    out, err = io.StringIO(), io.StringIO()
    with (
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
        unittest.TestCase().assertRaises(SystemExit) as caught,
    ):
        next_round.main(list(argv))
    return caught.exception.code, out.getvalue(), err.getvalue()


class TempTreeCaseMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def factory(self, name="factory"):
        path = self.root / name
        path.mkdir()
        return path


class AsRoundTests(unittest.TestCase):
    def test_round_value_coercion(self):
        cases = ((True, None), (3, 3), (" 4 ", 4), ("x", None), (1.5, None), (None, None))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(next_round._as_round(value), expected)


class ScanRoundsTests(TempTreeCaseMixin, unittest.TestCase):
    def test_missing_directory_has_no_rounds(self):
        self.assertEqual(next_round.scan_rounds(self.root / "absent"), set())

    def test_nested_meta_rounds_skip_blank_and_malformed_lines(self):
        factory = self.factory()
        nested = {"items": [{"meta": {"round": "5"}}, [{"meta": {"round": True}}]]}
        _write_lines(factory / "extra.jsonl", "", "{broken", json.dumps(nested))
        self.assertEqual(next_round.scan_rounds(factory), {5})

    def test_undecodable_jsonl_contributes_only_its_name(self):
        factory = self.factory()
        (factory / "batch-r02.jsonl").write_bytes(b"\xff\xfe\n")
        self.assertEqual(next_round.scan_rounds(factory), {2})

    def test_notes_round1_names_and_subdirectories(self):
        factory = self.factory()
        (factory / "NOTES-r04.md").write_text("notes\n")
        (factory / "pairs.jsonl").write_text("")
        (factory / "batch-r09.jsonl").mkdir()
        self.assertEqual(next_round.scan_rounds(factory), {1, 4})


class FactoryPlanTests(TempTreeCaseMixin, unittest.TestCase):
    def marker_factory(self):
        factory = self.factory()
        mode = {"version": 1, "legacy_baseline": 0, "commit_point": "ROUND-rNN.complete.json"}
        (factory / MODE_FILE).write_text(json.dumps(mode) + "\n")
        (factory / "batch-r07.jsonl").write_text("")
        return factory

    def test_marker_mode_plan_uses_the_frontier_not_filenames(self):
        plan = next_round.factory_plan(self.marker_factory())
        self.assertEqual((plan["next_round"], plan["existing"]), (1, []))

    def test_marker_mode_keeps_an_explicit_round(self):
        plan = next_round.factory_plan(self.marker_factory(), 2)
        self.assertEqual((plan["next_round"], plan["existing"]), (2, []))

    def test_round_number_must_be_a_positive_int(self):
        factory = self.factory()
        for value in (0, -1, True, "2"):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "round number must be at least 1"),
            ):
                next_round.factory_plan(factory, value)

    def test_explicit_round_overrides_the_scan(self):
        factory = self.factory()
        (factory / "batch-r02.jsonl").write_text("")
        plan = next_round.factory_plan(factory, 5)
        self.assertEqual((plan["write"], plan["notes"]), ("batch-r05.jsonl", "NOTES-r05.md"))


class AllocateTests(TempTreeCaseMixin, unittest.TestCase):
    def test_occupied_targets_are_refused(self):
        names = ("batch-r03.jsonl", "ROUND-r03.reserved.json", "ROUND-r03.publishing.json",
                 "ROUND-r03.complete.json")
        for name in names:
            with self.subTest(name=name):
                factory = self.factory(name.replace(".", "_"))
                (factory / name).write_text("")
                with self.assertRaisesRegex(next_round.RoundExistsError, f"refuse: {name}"):
                    next_round.allocate(factory, 3)

    def test_unrelated_batch_names_do_not_collide(self):
        factory = self.factory()
        (factory / "batch-r3x.jsonl").write_text("")
        self.assertEqual(next_round.allocate(factory, 3)["next_round"], 3)


class IndexTests(TempTreeCaseMixin, unittest.TestCase):
    def test_is_factory_dir_cases(self):
        hidden = self.factory(".hidden")
        (hidden / "a.jsonl").write_text("")
        nested = self.factory("nested")
        (nested / "sub.jsonl").mkdir()
        (nested / "readme.txt").write_text("")
        notes = self.factory("notes")
        (notes / "NOTES-r01.md").write_text("")
        cases = ((hidden, False), (nested, False), (notes, True), (self.root / "nope", False))
        for path, expected in cases:
            with self.subTest(path=path.name):
                self.assertIs(next_round.is_factory_dir(path), expected)

    def test_write_index_lists_only_factory_dirs(self):
        (self.factory("beta") / "batch-r02.jsonl").write_text("")
        (self.factory("alpha") / "NOTES-r01.md").write_text("")
        self.factory("empty")
        (self.root / "loose.jsonl").write_text("")
        payload, out = next_round.write_index(self.root)
        self.assertEqual(out, self.root / "NEXT_ROUND.json")
        self.assertEqual(json.loads(out.read_text()), payload)
        self.assertEqual([e["factory"] for e in payload["factories"]], ["alpha", "beta"])
        self.assertEqual([e["next_round"] for e in payload["factories"]], [2, 3])


class MainTests(TempTreeCaseMixin, unittest.TestCase):
    def test_parse_args_reads_flags(self):
        args = next_round.parse_args(["--allocate", "4", "factory"])
        self.assertEqual((args.allocate, args.path, args.write_index), (4, "factory", False))

    def test_write_index_refusals_exit_2(self):
        cases = (
            (["--write-index", "--allocate", "2"], "cannot be combined with --allocate"),
            (["--write-index"], "error: not a directory"),
        )
        for flags, message in cases:
            with self.subTest(flags=flags):
                path = str(self.root if "--allocate" in flags else self.root / "absent")
                code, _out, err = _run_main(*flags, path)
                self.assertEqual(code, 2)
                self.assertIn(message, err)
        self.assertFalse((self.root / "NEXT_ROUND.json").exists())

    def test_write_index_success_exits_0_inside_the_temp_root(self):
        (self.factory() / "batch-r01.jsonl").write_text("")
        code, out, _err = _run_main("--write-index", str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["factories"][0]["next_round"], 2)
        self.assertTrue((self.root / "NEXT_ROUND.json").is_file())

    def test_plan_exit_codes(self):
        factory = self.factory()
        (factory / "batch-r01.jsonl").write_text("")
        cases = (
            ([str(self.root / "absent")], 2, "error: not a directory"),
            (["--allocate", "1", str(factory)], 1, "refuse: batch-r01.jsonl already exists"),
            (["--allocate", "0", str(factory)], 1, "round number must be at least 1"),
        )
        for argv, expected, message in cases:
            with self.subTest(argv=argv):
                code, _out, err = _run_main(*argv)
                self.assertEqual((code, message in err), (expected, True))

    def test_plan_success_prints_json_and_writes_nothing(self):
        factory = self.factory()
        code, out, _err = _run_main(str(factory))
        self.assertEqual((code, json.loads(out)["write"]), (0, "batch-r01.jsonl"))
        self.assertEqual(list(factory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
