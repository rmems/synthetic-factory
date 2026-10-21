"""CLI, child interpreter, and export failure branches."""

import io
import json
import runpy
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PIPELINES))

PRODUCED_AT = "2026-10-20T23:00:00Z"

CHILD_PATH = PIPELINES / "honest_stop" / "_child.py"
SCRIPT_PATH = PIPELINES / "honest_stop_cli.py"

import pipelines.honest_stop_cli as entry

import honest_stop._child as child
import honest_stop.vocabulary as cv
from honest_stop._contract import dumps_exact_json
from honest_stop.cli import run
from honest_stop.export_stub import write_stub
from honest_stop.records import build_record


def built(scenario_id: str = "missing-credential") -> dict:
    return build_record(scenario_id, produced_at=PRODUCED_AT, run_seed=1)


def _cli(*args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class ChildTests(unittest.TestCase):
    def test_child_main_rejects_oversize_and_bad_json_and_accepts_a_record(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work / "record.json").write_bytes(b"x" * (cv.MAX_RECORD_BYTES + 1))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn("record.too_large", stdout.getvalue())
            (work / "record.json").write_text("{", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn("record.json", stdout.getvalue())
            with mock.patch("honest_stop._child.load_strict_json", side_effect=RecursionError):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(child.main(["child", str(work)]), 0)
                self.assertIn("record.json", stdout.getvalue())
            payload = dumps_exact_json(built())
            (work / "record.json").write_text(payload, encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(child.main(["child", str(work)]), 0)
            self.assertIn('"accepted":true', stdout.getvalue().replace(" ", ""))
            argv = ["child", str(work)]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                redirect_stdout(stdout),
                self.assertRaises(SystemExit) as caught,
            ):
                runpy.run_path(str(CHILD_PATH), run_name="__main__")
            self.assertEqual(caught.exception.code, 0)
            self.assertIn(cv.GATE_MARKER, stdout.getvalue())


class CommandTests(unittest.TestCase):
    def test_cli_exits_for_checks_refusals_and_bad_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "record.json"
            path.write_text(json.dumps(built()), encoding="utf-8")
            code, stdout, stderr = _cli("validate", str(path))
            self.assertEqual(code, 0, stderr)
            self.assertTrue(json.loads(stdout)["ok"])
            path.write_text("{}", encoding="utf-8")
            code, stdout, _stderr = _cli("validate", str(path))
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(stdout)["ok"])
            path.write_bytes(b"\xff")
            code, stdout, _stderr = _cli("validate", str(path))
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(stdout)["codes"], ["record.json"])
            code, _stdout, stderr = _cli("validate", temp)
            self.assertEqual(code, 2)
            self.assertIn("refused: io:", stderr)
            path.write_text(json.dumps(built()), encoding="utf-8")
            accepted, accepted_out, accepted_err = _cli("gate", str(path))
            self.assertEqual(accepted, 0, accepted_err)
            self.assertTrue(json.loads(accepted_out)["accepted"])
            forged = built()
            forged["result"]["verified_blocker"] = False
            path.write_text(json.dumps(forged), encoding="utf-8")
            rejected, rejected_out, _rejected_err = _cli("gate", str(path))
            self.assertEqual(rejected, 1)
            self.assertEqual(json.loads(rejected_out)["code"], "result.forged_blocker")
            out = Path(temp) / "bundle"
            code, _stdout, stderr = _cli("export", "--dry-run", "--out", str(out))
            self.assertEqual(code, 2)
            self.assertIn("export.dry_run", stderr)
            code, _stdout, stderr = _cli("export", "--publish")
            self.assertEqual(code, 2)
            self.assertIn("export.publish_disabled", stderr)
            code, _stdout, stderr = _cli("export", "--token", "hub-" + "marker")
            self.assertEqual(code, 2)
            self.assertIn("export.token", stderr)
            self.assertNotIn("hub-marker", stderr)
        for args in (
            ("generate", "--dry-run", "--seed", "-1", "--count", "1"),
            ("generate", "--dry-run", "--seed", "1", "--count", "0"),
        ):
            with self.subTest(args=args):
                code, _stdout, stderr = _cli(*args)
                self.assertEqual(code, 2)
                self.assertIn("refused:", stderr)

    def test_script_entry_point_plans_a_dry_run(self):
        self.assertTrue(built()["record_id"].startswith("stop-"))

        self.assertTrue(callable(entry.main))
        argv = [str(SCRIPT_PATH), "generate", "--dry-run", "--seed", "1", "--count", "1"]
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", argv),
            redirect_stdout(stdout),
            self.assertRaises(SystemExit) as caught,
        ):
            runpy.run_path(str(SCRIPT_PATH), run_name="__main__")
        self.assertEqual(caught.exception.code, 0)
        self.assertTrue(json.loads(stdout.getvalue())["dry_run"])

    def test_export_removes_a_destination_when_the_write_fails(self):
        self.assertEqual(built()["result"]["verified_blocker"], True)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "bundle"
            out.mkdir()
            with self.assertRaises(cv.FamilyError) as caught:
                write_stub(out)
            self.assertEqual(caught.exception.code, "export.exists")
            out.rmdir()
            with (
                mock.patch("honest_stop.export_stub.Path.write_text", side_effect=OSError("full")),
                self.assertRaises(OSError),
            ):
                write_stub(out)
            self.assertFalse(out.exists())
