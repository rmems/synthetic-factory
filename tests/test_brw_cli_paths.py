"""brw CLI selectors, leftover-catalog pins, and pair validation edges.

Kept out of ``tests/test_brw.py``, whose length counts toward the package's
2,500-line cap.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from brw import catalog, generate
from brw._contract import CATALOG_FIRST, BrwError
from brw.cli import run as brw_run


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = brw_run(argv)
    return code, out.getvalue(), err.getvalue()


def records(text):
    return [json.loads(line) for line in text.splitlines() if line]


class BrwCliSelectors(unittest.TestCase):
    def test_slug_and_index_build_one_validated_pair(self):
        slug = catalog.PAIRS[2]["ok_slug"]
        code, out, err = invoke(["generate", "--slug", slug, "--round", "301", "--fail"])
        self.assertEqual((code, err), (0, ""))
        (bad,) = records(out)
        self.assertEqual(bad["meta"]["round"], 301)
        self.assertFalse(bad["reward"]["success"])
        code, out, _ = invoke(["generate", "--index", "2"])
        ok, bad = records(out)
        self.assertEqual(ok["id"], f"brw-r{CATALOG_FIRST}-{slug}")

    def test_window_sides_and_refusals(self):
        code, out, _ = invoke(["generate", "--window", "--count", "2", "--fail"])
        self.assertEqual(code, 0)
        self.assertEqual([record["reward"]["success"] for record in records(out)], [False, False])
        for argv, prefix in (
            (["generate"], "missing_round"),
            (["generate", "--round", "193", "--count", "2"], "count_requires_window"),
            (["generate", "--window", "--index", "0"], "window_rejects_slug_index"),
            (["generate", "--slug", "x", "--index", "0"], "select_one"),
        ):
            with self.subTest(argv=argv):
                code, out, err = invoke(argv)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err.startswith(prefix), err)


class BrwLeftoverLookups(unittest.TestCase):
    def test_r383_and_r395_index_and_round_refusals(self):
        self.assertEqual(catalog.r383_pair_at(0), catalog.R383_PAIRS[0])
        self.assertEqual(catalog.r395_pair_at(0), catalog.R395_PAIRS[0])
        for lookup, argument, message in (
            (catalog.r383_pair_at, 99, "unknown_r383_index: 99"),
            (catalog.r395_pair_at, -1, "unknown_r395_index: -1"),
            (catalog.r383_pair_at, False, "unknown_r383_index: False"),
            (catalog.r212_pair_for_round, "212", "invalid_round: '212'"),
            (catalog.r383_pair_for_round, True, "invalid_round: True"),
            (catalog.r395_pair_for_round, 455, "no r395 catalog entry for r455 (first=395 last=454)"),
        ):
            with self.subTest(message=message), self.assertRaises(BrwError) as caught:
                lookup(argument)
            self.assertEqual(str(caught.exception), message)


class BrwLeftoverHeaderPins(unittest.TestCase):
    def _load_header_with(self, edit):
        root = Path(tempfile.mkdtemp(prefix="brw-left-"))
        self.addCleanup(shutil.rmtree, root, True)
        shutil.copytree(catalog.LEFTOVER_DIR, root, dirs_exist_ok=True)
        header_path = root / catalog.LEFTOVER_HEADER_NAME
        header = json.loads(header_path.read_text(encoding="utf-8"))
        edit(header)
        header_path.write_text(json.dumps(header), encoding="utf-8")
        with mock.patch.object(catalog, "LEFTOVER_DIR", root):
            return catalog._load_leftover_header()

    def test_each_mill_row_pins_its_id_and_committed_count(self):
        def rename(header):
            header["mills"][1]["mill_id"] = "brw-mill-other"

        def recount(header):
            header["mills"][2]["n_rows_committed"] += 1

        for edit, message in (
            (rename, "unexpected mill_id: 'brw-mill-other'"),
            (recount, "brw-mill-r395 committed row count drifted"),
        ):
            with self.subTest(message=message), self.assertRaises(BrwError) as caught:
                self._load_header_with(edit)
            self.assertEqual(str(caught.exception), message)
        self.assertEqual(self._load_header_with(lambda header: None), catalog.LEFTOVER_HEADER)


class BrwPairValidation(unittest.TestCase):
    def test_a_409_counter_key_is_banned_whatever_the_code(self):
        ok, bad = generate.pair_records(CATALOG_FIRST)
        flagged = copy.deepcopy(bad)
        flagged["reward"]["http_409s"] = 1
        with self.assertRaises(BrwError) as caught:
            generate.validate_pair(CATALOG_FIRST, ok, flagged, catalog.PAIRS[0])
        self.assertEqual(str(caught.exception), "409 fail banned")

    def test_backface_reshaping_refuses_a_wrong_step_count(self):
        visual = [pair for pair in catalog.PAIRS if pair["css_short"] == "backface-visibility"]
        self.assertEqual(len(visual), 1)
        scene = generate._scene(visual[0])
        steps = [{"n": index} for index in range(1, 9)]
        with self.assertRaises(BrwError) as caught:
            generate._backface_steps(scene, steps)
        self.assertEqual(str(caught.exception), "visual/backface step count 9")


if __name__ == "__main__":
    unittest.main()
