"""Dry-run CLI: no model calls, no records, no Hub publish."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import honest_stop.vocabulary as cv
from honest_stop.cli import run
from honest_stop.export_stub import export_plan, publish, write_stub
from honest_stop.generate import dry_run_plan
from honest_stop.ollama import (
    LiveCallDisabled,
    digest_from_show,
    perform,
    writer_request,
)
from honest_stop.splits import load_family
from honest_stop.vocabulary import DEDUP_MODEL, WRITER_MODEL

FIXTURES = REPO / "tests" / "fixtures" / "honest-stop"


def _marker(label: str) -> str:
    return "hub-" + label


def _cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class DryRunTests(unittest.TestCase):
    def test_dry_run_records_models_seed_and_lineage_without_writing(self):
        plan = dry_run_plan(seed=3, count=4)
        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["records_written"], 0)
        self.assertEqual(plan["network_calls"], 0)
        self.assertEqual(plan["run_seed"], 3)
        names = {row["name"] for row in plan["models"]}
        self.assertEqual(names, {WRITER_MODEL, DEDUP_MODEL})
        self.assertTrue(all(row["digest"] is None for row in plan["models"]))
        self.assertEqual(plan["provenance"]["lineage"]["run_seed"], 3)
        self.assertEqual(len(plan["scenarios"]), 4)
        self.assertTrue(all(call["sent"] is False for call in plan["planned_calls"]))
        held = [row for row in plan["scenarios"] if row["held_out"]]
        self.assertEqual([row["task_id"] for row in held], ["honest-stop-underspecified-request"])
        self.assertFalse(held[0]["train_export"])

    def test_dry_run_does_not_call_urlopen(self):
        with mock.patch(
            "honest_stop.ollama.urllib.request.urlopen",
            side_effect=AssertionError("called"),
        ):
            plan = dry_run_plan(seed=1, count=1)
        self.assertEqual(plan["network_calls"], 0)
        with self.assertRaises(LiveCallDisabled):
            perform(writer_request("plan-only"))

    def test_show_fixture_parses_a_digest_without_a_network_call(self):
        document = json.loads((FIXTURES / "ollama-show.json").read_text(encoding="utf-8"))
        self.assertEqual(digest_from_show(document), document["digest"])

    def test_cli_dry_run_exits_zero_and_live_generate_is_refused(self):
        marker = _marker("marker")
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "http://127.0.0.1:1", "HF_TOKEN": marker}):
            code, stdout, stderr = _cli("generate", "--dry-run", "--seed", "1", "--count", "4")
        self.assertEqual(code, 0, stderr)
        plan = json.loads(stdout)
        self.assertEqual(plan["records_written"], 0)
        self.assertEqual(plan["network_calls"], 0)
        self.assertIn(WRITER_MODEL, stdout)
        self.assertIn(DEDUP_MODEL, stdout)
        self.assertNotIn(marker, stdout)
        refused, _stdout, refused_err = _cli("generate", "--seed", "1", "--count", "1")
        self.assertEqual(refused, 2)
        self.assertIn("live_generation_disabled", refused_err)

    def test_family_registration_matches_the_held_out_list(self):
        family = load_family()
        self.assertEqual(family.writer_model, WRITER_MODEL)
        self.assertEqual(family.dedup_model, DEDUP_MODEL)
        self.assertEqual(
            family.excluded_task_ids, frozenset({"honest-stop-underspecified-request"})
        )
        self.assertEqual(family.splits["underspecified-request"], "held_out")
        self.assertEqual(family.dataset, cv.DATASET)

    def test_export_stub_writes_no_records_and_refuses_publish(self):
        marker = _marker("marker")
        other = _marker("other")
        with mock.patch.dict(os.environ, {"HF_TOKEN": marker, "HUGGING_FACE_HUB_TOKEN": other}):
            plan = export_plan()
        blob = json.dumps(plan)
        self.assertNotIn(marker, blob)
        self.assertNotIn(other, blob)
        self.assertFalse(plan["publish"])
        self.assertFalse(plan["hub_upload"])
        self.assertEqual(plan["records"], 0)
        self.assertEqual(plan["held_out_task_ids"], ["honest-stop-underspecified-request"])
        with self.assertRaises(cv.FamilyError) as caught:
            publish(token=marker)
        self.assertEqual(caught.exception.code, "export.publish_disabled")

    def test_cli_export_dry_run_and_token_refusal(self):
        code, stdout, stderr = _cli("export", "--dry-run")
        self.assertEqual(code, 0, stderr)
        plan = json.loads(stdout)
        self.assertEqual(plan["records"], 0)
        self.assertFalse(plan["publish"])
        marker = _marker("marker")
        refused, _stdout, refused_err = _cli("export", "--publish", "--token", marker)
        self.assertEqual(refused, 2)
        self.assertNotIn(marker, refused_err)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            written, _stdout, written_err = _cli("export", "--out", str(out))
            self.assertEqual(written, 0, written_err)
            manifest = json.loads((out / "EXPORT.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["records"], 0)
            self.assertEqual(list(out.iterdir()), [out / "EXPORT.json"])
            raw = Path(temp) / "outputs" / "raw" / "bundle"
            with self.assertRaises(cv.FamilyError) as caught:
                write_stub(raw)
            self.assertEqual(caught.exception.code, "export.raw")


if __name__ == "__main__":
    unittest.main()
