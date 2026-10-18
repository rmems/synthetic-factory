"""``ttf.cli.run`` owns the exit code: 0 after any command, 2 for a refusal."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pipelines.ttf import cli
from pipelines.ttf._contract import CATALOG_ID, FULL_PLANT_COUNT, SLICE_IDS


def _invoke(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class RunExitCodes(unittest.TestCase):
    def test_catalog_json_prints_every_plant_and_exits_zero(self):
        code, out, err = _invoke(["catalog", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["command"], "catalog")
        self.assertEqual(payload["catalog_id"], CATALOG_ID)
        self.assertEqual(payload["slices"], list(SLICE_IDS))
        self.assertEqual(len(payload["plants"]), FULL_PLANT_COUNT)

    def test_catalog_check_text_exits_zero(self):
        code, out, err = _invoke(["catalog-check"])
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.startswith(f"catalog-check ok: {FULL_PLANT_COUNT} plants"))

    def test_generate_to_a_new_destination_exits_zero_then_refuses_it(self):
        root = Path(tempfile.mkdtemp(prefix="ttf-exit-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "dest"
        code, out, err = _invoke(["generate", "--slice", "r04", "--out", str(dest)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.strip(), f"generated 5 records into {dest}")
        code, out, err = _invoke(["generate", "--slice", "r04", "--out", str(dest)])
        self.assertEqual((code, out), (2, ""))
        self.assertNotEqual(err, "")


if __name__ == "__main__":
    unittest.main()
