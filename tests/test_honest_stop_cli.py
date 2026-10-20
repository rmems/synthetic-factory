"""Dry-run CLI: no model calls, no records, no Hub publish."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import honest_stop.vocabulary as cv
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

CLI = PIPELINES / "honest_stop_cli.py"
FIXTURES = REPO / "tests" / "fixtures" / "honest-stop"


def _cli(*args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=REPO,
    )


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
        env = dict(os.environ)
        env["OLLAMA_HOST"] = "http://127.0.0.1:1"
        env["HF_TOKEN"] = "secret-token"
        done = _cli("generate", "--dry-run", "--seed", "1", "--count", "4", env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        plan = json.loads(done.stdout)
        self.assertEqual(plan["records_written"], 0)
        self.assertEqual(plan["network_calls"], 0)
        self.assertIn(WRITER_MODEL, done.stdout)
        self.assertIn(DEDUP_MODEL, done.stdout)
        self.assertNotIn("secret-token", done.stdout)
        refused = _cli("generate", "--seed", "1", "--count", "1")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("live_generation_disabled", refused.stderr)

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
        with mock.patch.dict(
            os.environ, {"HF_TOKEN": "secret-token", "HUGGING_FACE_HUB_TOKEN": "other"}
        ):
            plan = export_plan()
        blob = json.dumps(plan)
        self.assertNotIn("secret-token", blob)
        self.assertNotIn("other", blob)
        self.assertFalse(plan["publish"])
        self.assertIsNone(plan["huggingface_token"])
        self.assertEqual(plan["records"], 0)
        self.assertEqual(plan["held_out_task_ids"], ["honest-stop-underspecified-request"])
        with self.assertRaises(cv.FamilyError) as caught:
            publish(token="secret-token")
        self.assertEqual(caught.exception.code, "export.publish_disabled")

    def test_cli_export_dry_run_and_token_refusal(self):
        done = _cli("export", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        plan = json.loads(done.stdout)
        self.assertEqual(plan["records"], 0)
        self.assertFalse(plan["publish"])
        refused = _cli("export", "--publish", "--token", "secret-token")
        self.assertEqual(refused.returncode, 2)
        self.assertNotIn("secret-token", refused.stderr)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            written = _cli("export", "--out", str(out))
            self.assertEqual(written.returncode, 0, written.stderr)
            manifest = json.loads((out / "EXPORT.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["records"], 0)
            self.assertEqual(list(out.iterdir()), [out / "EXPORT.json"])
            raw = Path(temp) / "outputs" / "raw" / "bundle"
            with self.assertRaises(cv.FamilyError) as caught:
                write_stub(raw)
            self.assertEqual(caught.exception.code, "export.raw")


if __name__ == "__main__":
    unittest.main()
