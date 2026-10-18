"""Fail-closed branches of the lll AST extractor, mill replay, and CLI entry point."""

import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

from pipelines.lll import catalog, cli, generate
from pipelines.lll._contract import LllRefusal
from pipelines.lll.catalog_ast import extract_pairs

PATH = "experiments/fixture-mill.py"
QUAD = '"a", "b", "c", "d"'
APPEND = 'PAIRS.append(("Title", fa, fb))\n'

# (label, source) where each bind is not a literal fn_pair quad
MALFORMED_BINDS = (
    ("non-literal argument", 'fa, fb = fn_pair(unbound, "b", "c", "d")\n'),
    ("other callee", f"fa, fb = other({QUAD})\n"),
    ("not a call", "fa, fb = 1, 2\n"),
)

# (label, source) whose appends never name a pair title
UNTITLED_APPENDS = (
    ("two arguments", 'PAIRS.append("x", "y")\n'),
    ("other list", 'OTHER.append(("Title",))\n'),
)


class LllExtractBranches(unittest.TestCase):
    def _refusal(self, source):
        with self.assertRaises(LllRefusal) as caught:
            extract_pairs(source, path=PATH)
        return caught.exception.code, str(caught.exception)

    def test_attribute_fn_pair_binds_are_read(self):
        found = extract_pairs(f"fa, fb = mill.fn_pair({QUAD})\n" + APPEND, path=PATH)
        self.assertEqual(found, (("Title", ["a", "b", "c", "d"]),))

    def test_malformed_binds_are_refused(self):
        expected = ("SOURCE_NOT_PARSEABLE",
                    f"SOURCE_NOT_PARSEABLE: {PATH} has a malformed fn_pair bind")
        for label, bind in MALFORMED_BINDS:
            with self.subTest(label):
                self.assertEqual(self._refusal(bind + APPEND), expected)

    def test_untitled_appends_leave_no_pairs(self):
        expected = ("SOURCE_NOT_PARSEABLE",
                    f"SOURCE_NOT_PARSEABLE: {PATH} has no leftover leftover leftover pairs")
        for label, append in UNTITLED_APPENDS:
            with self.subTest(label):
                self.assertEqual(self._refusal(append), expected)


class LllReplayBranches(unittest.TestCase):
    def test_all_selection_replays_every_catalog_pair_in_order(self):
        expected = [plant.plant_id for plant in catalog.load_catalog().plants]
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "run"
            summary = generate.run(generate.GenerateRequest(
                catalog_dir=catalog.default_catalog_dir(), out_dir=out_dir, all_plants=True,
            ))
            rows = (out_dir / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(summary["records"], len(expected))
        self.assertEqual([json.loads(row)["meta"]["plant_id"] for row in rows], expected)

    def test_main_exits_with_the_run_status(self):
        stdout = StringIO()
        with (
            mock.patch("sys.argv", ["pipelines.lll.cli", "catalog", "--json"]),
            mock.patch("sys.stdout", stdout),
            self.assertRaises(SystemExit) as caught,
        ):
            cli.main()
        self.assertEqual(caught.exception.code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "ok")


if __name__ == "__main__":
    unittest.main()
