"""CLI generation reports candidate refusals and publishes complete runs."""

import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pipelines.model_channel import cli, generate, openai_client
from test_model_channel import NANO, PHI, TASK, episode_payload

OUTSIDE_MSG = "outside the working, home and temp trees"

STAMP = "2026-09-18T00:00:00Z"


def completion(content):
    return {"choices": [{"message": {"content": content}}]}


class CandidateRuns(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.task = self.root / "task.json"
        self.task.write_text(json.dumps({**TASK, "schema": {"type": "object"}}))
        self.out = self.root / "out"

    def _run(self, response, *options):
        stdout, stderr = StringIO(), StringIO()
        args = [
            "generate",
            "--path-id",
            NANO,
            "--task",
            str(self.task),
            "--endpoint",
            "http://localhost/v1",
            "--out",
            str(self.out),
            *options,
        ]
        with (
            mock.patch.object(openai_client, "chat_completions", return_value=response) as client,
            mock.patch.object(generate, "_utc_now", return_value=STAMP),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            code = cli.run(args)
        return code, stdout.getvalue(), stderr.getvalue(), client

    def test_success_publishes_candidate_and_matching_summary(self):
        runtime = self.root / "runtime.json"
        runtime.write_text(json.dumps({"device": "fixture-device", "require_tool_parser": False}))
        code, stdout, stderr, client = self._run(
            completion(json.dumps(episode_payload())),
            "--runtime-json",
            str(runtime),
            "--json",
        )
        self.assertEqual((code, stderr), (0, ""))
        summary = json.loads(stdout)
        self.assertEqual(summary, json.loads((self.out / "RUN.json").read_text()))
        self.assertEqual(
            (summary["attempted"], summary["accepted"], summary["rejected"]), (1, 1, 0)
        )
        self.assertEqual(summary["produced_at"], STAMP)
        candidate = json.loads((self.out / "candidates.jsonl").read_text())
        self.assertEqual(candidate["meta"]["runtime_device"], "fixture-device")
        self.assertTrue(candidate["meta"]["candidate_only"])
        self.assertNotIn("_generation", candidate)
        self.assertIn('Schema:\n{"type": "object"}', client.call_args.args[2][-1]["content"])

    def test_malformed_completions_publish_refusals_without_candidates(self):
        responses = (
            ({}, "missing choices"),
            ({"choices": []}, "missing choices"),
            ({"choices": [None]}, "missing message"),
            ({"choices": [{"message": None}]}, "missing message"),
            (completion(None), "content is empty"),
            (completion("  "), "content is empty"),
            (completion("[]"), "must be a JSON object"),
            (completion('{"goal":"first","goal":"second"}'), "strict JSON"),
            (completion(json.dumps(episode_payload(steps=[{}]))), "tool_call"),
        )
        for index, (response, reason) in enumerate(responses):
            with self.subTest(reason=reason, response=response):
                out = self.root / f"refused-{index}"
                code, stdout, stderr, _ = self._run(response, "--out", str(out))
                self.assertEqual((code, stderr), (2, ""))
                summary = json.loads(stdout)
                self.assertEqual((summary["accepted"], summary["rejected"]), (0, 1))
                self.assertIn(reason, summary["rejected_reasons"][0])
                self.assertEqual(summary["produced_at"], STAMP)
                self.assertEqual((out / "candidates.jsonl").read_bytes(), b"")
                self.assertEqual(json.loads((out / "RUN.json").read_text()), summary)

    def test_missing_openrouter_evidence_refuses_before_network(self):
        code, stdout, stderr, client = self._run({}, "--path-id", PHI)
        self.assertEqual((code, stderr), (2, ""))
        self.assertIn("distillable snapshot", json.loads(stdout)["rejected_reasons"][0])
        client.assert_not_called()

    def test_invalid_task_goal_refuses_before_network(self):
        self.task.write_text('{"goal":null}')
        code, stdout, stderr, client = self._run({})
        self.assertEqual((code, stderr), (2, ""))
        self.assertIn("task.goal", json.loads(stdout)["rejected_reasons"][0])
        client.assert_not_called()

    def test_publication_failure_reports_error_cleans_up_and_allows_retry(self):
        response = completion(json.dumps(episode_payload()))
        with mock.patch.object(generate, "rename_noreplace", side_effect=OSError("rename refused")):
            code, stdout, stderr, _ = self._run(response)
        self.assertEqual((code, stdout), (2, ""))
        self.assertIn("rename refused", stderr)
        self.assertEqual(list(self.root.iterdir()), [self.task])
        self.assertEqual(self._run(response)[0], 0)

    def test_outside_task_is_refused_before_any_sink(self):
        stderr = StringIO()
        with mock.patch("sys.stderr", stderr), self.assertRaises(SystemExit) as raised:
            cli.run(
                [
                    "generate",
                    "--path-id",
                    NANO,
                    "--task",
                    "/etc/passwd",
                    "--endpoint",
                    "http://localhost/v1",
                    "--out",
                    str(self.out),
                ]
            )
        self.assertEqual(raised.exception.code, 2)
        text = stderr.getvalue()
        self.assertIn("error:", text)
        self.assertIn("--task:", text)
        self.assertIn(OUTSIDE_MSG, text)
        self.assertNotIn("passwd", text)
        self.assertFalse(self.out.exists())

    def test_outside_snapshot_is_refused_before_any_sink(self):
        stderr = StringIO()
        with mock.patch("sys.stderr", stderr), self.assertRaises(SystemExit) as raised:
            cli.run(["discover-openrouter", "--snapshot", "/etc/passwd"])
        self.assertEqual(raised.exception.code, 2)
        text = stderr.getvalue()
        self.assertIn("error:", text)
        self.assertIn("--snapshot:", text)
        self.assertIn(OUTSIDE_MSG, text)
        self.assertNotIn("passwd", text)
