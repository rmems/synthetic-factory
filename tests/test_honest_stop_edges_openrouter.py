"""Dry-run OpenRouter writer plan: pins, provenance, and no network."""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import honest_stop.vocabulary as cv
from honest_stop.cli import run
from honest_stop.generate import dry_run_plan
from honest_stop.openrouter import Choice, require_effort, snapshot_of, writer_request
from honest_stop.records import build_record

PRODUCED_AT = "2026-10-20T23:00:00Z"


def _marker(label: str) -> str:
    return "test-" + label


def _choice(
    model: str = cv.WRITER_MODEL, effort: str = "high", seed: int = 1, secondary: bool = False
):
    return Choice(model, effort, seed, secondary)


def _cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


def _writer(plan: dict) -> dict:
    rows = [row for row in plan["provenance"]["actors"] if row["role"] == cv.WRITER_ROLE]
    return rows[0]


class OpenRouterPlanTests(unittest.TestCase):
    def test_model_pin_accepts_the_floating_id_and_dated_snapshots(self):
        self.assertEqual(built_scenario(), "missing-credential")
        self.assertIsNone(snapshot_of(cv.WRITER_MODEL))
        self.assertEqual(snapshot_of(cv.WRITER_MODEL + "-1017"), "1017")
        self.assertEqual(snapshot_of(cv.WRITER_MODEL + "-20261017"), "20261017")
        self.assertEqual(require_effort("high"), "high")
        self.assertEqual(require_effort("none"), "none")
        bad_models = (
            1,
            "  ",
            "gemma4:12b",
            cv.WRITER_MODEL + "-",
            cv.WRITER_MODEL + "-101",
            cv.WRITER_MODEL + "-abcd",
            cv.WRITER_MODEL + "-12345",
        )
        for model in bad_models:
            with self.subTest(model=model):
                with self.assertRaises(cv.FamilyError) as caught:
                    snapshot_of(model)
                self.assertEqual(caught.exception.code, "openrouter.model")
        for effort in (1, "High", ""):
            with self.subTest(effort=effort):
                with self.assertRaises(cv.FamilyError) as caught:
                    require_effort(effort)
                self.assertEqual(caught.exception.code, "openrouter.effort")

    def test_dry_run_records_the_writer_and_does_not_touch_the_network(self):
        marker = _marker("marker")
        env = {"OPENROUTER_API_KEY": marker, "OPENAI_API_KEY": marker}
        with mock.patch.dict(os.environ, env):
            with mock.patch(OPEN, side_effect=AssertionError("called")):
                with mock.patch(OLLAMA_OPEN, side_effect=AssertionError("called")):
                    plan = dry_run_plan(seed=1, count=1, produced_at=PRODUCED_AT)
        actor = _writer(plan)
        blob = json.dumps(plan)
        self.assertEqual(plan["network_calls"], 0)
        self.assertEqual(plan["records_written"], 0)
        self.assertEqual(actor["provider"], cv.WRITER_PROVIDER)
        self.assertEqual(actor["model"], cv.WRITER_MODEL)
        self.assertIsNone(actor["snapshot"])
        self.assertEqual(actor["reasoning_effort"], "high")
        self.assertEqual(actor["seed"], 1)
        self.assertEqual(actor["request_params"]["reasoning"], {"effort": "high"})
        self.assertNotIn("messages", actor["request_params"])
        self.assertNotIn(cv.SECONDARY_ROLE, {row["role"] for row in plan["models"]})
        self.assertNotIn(marker, blob)
        self.assertNotIn("Bearer", blob)
        self.assertNotIn("Authorization", blob)
        call = plan["planned_calls"][0]
        self.assertEqual(call["request"]["url"], cv.OPENROUTER_URL)
        self.assertFalse(call["sent"])
        self.assertEqual(call["request"]["body"]["messages"][0]["role"], "user")

    def test_snapshot_secondary_and_cli_refusals(self):
        model = cv.WRITER_MODEL + "-1017"
        choice = _choice(model, "low", 2, True)
        plan = dry_run_plan(seed=2, count=1, choice=choice)
        actor = _writer(plan)
        roles = [row["role"] for row in plan["models"]]
        self.assertEqual(roles, [cv.WRITER_ROLE, cv.SECONDARY_ROLE, cv.DEDUP_ROLE])
        self.assertEqual(actor["snapshot"], "1017")
        self.assertEqual(actor["reasoning_effort"], "low")
        self.assertEqual(plan["models"][1]["name"], cv.SECONDARY_WRITER_MODEL)
        secondary = [
            row for row in plan["provenance"]["actors"] if row["role"] == cv.SECONDARY_ROLE
        ]
        self.assertEqual(secondary[0]["provider"], cv.OLLAMA_PROVIDER)
        self.assertEqual(secondary[0]["seed"], 2)
        secondary_call = plan["planned_calls"][1]["request"]
        self.assertEqual(secondary_call["body"]["model"], cv.SECONDARY_WRITER_MODEL)
        self.assertTrue(secondary_call["url"].startswith(cv.OLLAMA_URL))
        code, stdout, stderr = _cli(
            "generate",
            "--dry-run",
            "--seed",
            "3",
            "--count",
            "1",
            "--model",
            cv.WRITER_MODEL + "-20261017",
            "--reasoning-effort",
            "max",
            "--secondary-writer",
        )
        self.assertEqual(code, 0, stderr)
        loaded = json.loads(stdout)
        pinned = _writer(loaded)
        self.assertEqual(pinned["snapshot"], "20261017")
        self.assertEqual(pinned["reasoning_effort"], "max")
        self.assertEqual(pinned["seed"], 3)
        self.assertEqual(loaded["models"][1]["role"], cv.SECONDARY_ROLE)
        self.assertEqual(loaded["network_calls"], 0)

    def test_bad_choice_and_live_generate_stay_offline(self):
        marker = _marker("marker")
        with self.assertRaises(cv.FamilyError) as caught:
            dry_run_plan(seed=1, count=1, choice=_choice(seed=2))
        self.assertEqual(caught.exception.code, "seed")
        with self.assertRaises(cv.FamilyError) as caught:
            dry_run_plan(seed=1, count=1, choice=Choice(cv.WRITER_MODEL, "high", 1, 1))
        self.assertEqual(caught.exception.code, "writer.secondary")
        with self.assertRaises(cv.FamilyError) as caught:
            writer_request("plan", _choice(effort="nope"))
        self.assertEqual(caught.exception.code, "openrouter.effort")
        for seed in (-1, True, "1"):
            with self.subTest(seed=seed):
                with self.assertRaises(cv.FamilyError) as caught:
                    writer_request("plan", Choice(cv.WRITER_MODEL, "high", seed))
                self.assertEqual(caught.exception.code, "seed")
        env = {cv.OPENROUTER_API_KEY_ENV: marker}
        with (
            mock.patch.dict(os.environ, env),
            mock.patch(OPEN, side_effect=AssertionError("called")),
        ):
            refused, stdout, err = _cli("generate", "--seed", "1", "--count", "1")
            bad, _stdout, bad_err = _cli(
                "generate", "--dry-run", "--seed", "1", "--count", "1", "--model", "gemma4:12b"
            )
        self.assertEqual(refused, 2)
        self.assertEqual(stdout, "")
        self.assertIn("live_generation_disabled", err)
        self.assertNotIn(marker, err)
        self.assertEqual(bad, 2)
        self.assertIn("openrouter.model", bad_err)
        self.assertNotIn(marker, bad_err)


def built_scenario() -> str:
    record = build_record("missing-credential", produced_at=PRODUCED_AT, run_seed=1)
    return record["context"]["scenario_id"]


OPEN = "honest_stop.openrouter.urllib.request.urlopen"
OLLAMA_OPEN = "honest_stop.ollama.urllib.request.urlopen"


if __name__ == "__main__":
    unittest.main()
