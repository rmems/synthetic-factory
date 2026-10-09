#!/usr/bin/env python3
"""The tool-world CLI in-process: exit codes, ``--json`` shapes, coded refusals on stderr.

Every command runs against a private catalog of the committed
``counter-workspace`` pack in a temporary directory; one subprocess case
proves the ``pipelines/tool_world_cli.py`` entry point still dispatches.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tool_world_test_support as support
from tool_world import cli, generate
from tool_world import vocabulary as cv
from tool_world._contract import sha256_bytes

PACK = "counter-workspace"
ADD_SUB = "counter.add-sub"
FACTORY = "tool-world-workspace-factory"
ENTRY = support.PIPELINES / "tool_world_cli.py"


def invoke(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def rewrite_candidates(run_dir: Path, payload: bytes) -> None:
    """Replace the candidate bytes and keep RUN.json's digest consistent with them."""
    (run_dir / generate.CANDIDATES_FILENAME).write_bytes(payload)
    run_file = run_dir / generate.RUN_FILENAME
    summary = json.loads(run_file.read_text(encoding="utf-8"))
    summary["candidates_sha256"] = sha256_bytes(payload)
    run_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def tamper_first_record(run_dir: Path, mutate) -> None:
    """Edit the first candidate and keep RUN.json's digest consistent with the new bytes."""
    candidates = run_dir / generate.CANDIDATES_FILENAME
    lines = candidates.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])
    mutate(record)
    lines[0] = json.dumps(record, sort_keys=True)
    rewrite_candidates(run_dir, ("\n".join(lines) + "\n").encode("utf-8"))


class CliCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tool-world-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.catalog = str(support.private_catalog(self.root / "catalog", (PACK,)))

    def generate_run(self, name: str = "run", count: int = 2) -> tuple[Path, dict]:
        out = self.root / name
        code, stdout, stderr = invoke(
            [
                "generate",
                "--catalog",
                self.catalog,
                "--seed",
                "1",
                "--count",
                str(count),
                "--factory",
                FACTORY,
                "--out",
                str(out),
                "--produced-at",
                support.PRODUCED_AT,
                "--json",
            ]
        )
        self.assertEqual((code, stderr), (0, ""))
        return out, json.loads(stdout)

    def assert_refused(self, argv: list[str], code: str) -> None:
        exit_code, stdout, stderr = invoke(argv)
        self.assertEqual((exit_code, stdout), (2, ""), stderr)
        self.assertTrue(stderr.startswith(f"{code}: "), stderr)
        self.assertEqual(stderr.count("\n"), 1)


class CatalogCheck(CliCase):
    def test_json_reports_every_pinned_pack(self):
        code, stdout, stderr = invoke(["catalog-check", "--catalog", self.catalog, "--json"])
        self.assertEqual((code, stderr), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["catalog_id"], "tool-world-test")
        self.assertRegex(payload["catalog_sha256"], r"^[0-9a-f]{64}$")
        (pack,) = payload["packs"]
        self.assertEqual((pack["pack_id"], pack["surfaces"]), (PACK, ["workspace"]))
        self.assertIn(ADD_SUB, pack["tasks"])
        self.assertEqual(set(pack["license"]) >= {"spdx", "source", "authorship"}, True)

    def test_plain_output_is_still_one_object(self):
        code, stdout, _stderr = invoke(["catalog-check", "--catalog", self.catalog])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["catalog_id"], "tool-world-test")

    def test_write_pins_refreshes_a_drifted_pin_in_place_and_keeps_the_row_prose(self):
        header = Path(self.catalog) / "CATALOG.json"
        rows = json.loads(header.read_text(encoding="utf-8"))
        rows["packs"][0]["note"] = "reviewed"
        header.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        readme = Path(self.catalog) / PACK / "files" / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
        self.assert_refused(
            ["catalog-check", "--catalog", self.catalog], cv.FINDING_PACK_SHA_MISMATCH
        )
        code, stdout, stderr = invoke(
            ["catalog-check", "--catalog", self.catalog, "--write-pins", "--json"]
        )
        self.assertEqual((code, stderr), (0, ""))
        (pinned,) = json.loads(stdout)["packs"]
        (row,) = json.loads(header.read_text(encoding="utf-8"))["packs"]
        self.assertEqual(
            row,
            {
                "note": "reviewed",
                "pack_id": PACK,
                "pack_sha256": pinned["pack_sha256"],
                "surfaces": ["workspace"],
            },
        )
        code, _stdout, stderr = invoke(["catalog-check", "--catalog", self.catalog])
        self.assertEqual((code, stderr), (0, ""))
        rows["packs"] = [{"pack_id": "absent"}]
        header.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        self.assert_refused(
            ["catalog-check", "--catalog", self.catalog, "--write-pins"],
            cv.FINDING_PACK_FILE_MISSING,
        )

    def test_a_missing_catalog_is_a_coded_refusal_with_exit_two(self):
        self.assert_refused(
            ["catalog-check", "--catalog", str(self.root / "absent")],
            cv.FINDING_CATALOG_FILE_MISSING,
        )
        self.assert_refused(
            ["catalog-check", "--catalog", str(self.root / "absent"), "--json"],
            cv.FINDING_CATALOG_FILE_MISSING,
        )


class Generate(CliCase):
    def test_generate_writes_a_run_then_refuses_the_same_destination(self):
        out, payload = self.generate_run()
        self.assertEqual(payload["format"], cv.RUN_FORMAT)
        self.assertEqual(payload["records"], len(payload["rows"]))
        self.assertGreater(payload["accepted"], 0)
        for name in (generate.CANDIDATES_FILENAME, generate.RUN_FILENAME, generate.NOTES_FILENAME):
            self.assertTrue((out / name).is_file(), name)
        self.assert_refused(
            [
                "generate",
                "--catalog",
                self.catalog,
                "--seed",
                "1",
                "--count",
                "1",
                "--out",
                str(out),
            ],
            cv.FINDING_DESTINATION_EXISTS,
        )

    def test_generate_refuses_a_destination_under_the_raw_tree(self):
        raw = self.root / "outputs" / "raw" / "run"
        self.assert_refused(
            [
                "generate",
                "--catalog",
                self.catalog,
                "--seed",
                "1",
                "--count",
                "1",
                "--out",
                str(raw),
            ],
            cv.FINDING_DESTINATION_UNDER_RAW,
        )
        self.assertFalse(raw.exists())

    def test_domain_refusals(self):
        base = ["generate", "--catalog", self.catalog, "--out", str(self.root / "run")]
        cases = (
            (["--seed", "-1", "--count", "1"], cv.FINDING_SEED_INVALID),
            (["--seed", "1", "--count", "0"], cv.FINDING_COUNT_OUT_OF_DOMAIN),
            (["--seed", "1", "--count", str(cv.MAX_COUNT)], cv.FINDING_COUNT_OUT_OF_DOMAIN),
            (
                ["--seed", "1", "--count", "1", "--produced-at", "today"],
                cv.FINDING_PRODUCED_AT_NOT_A_TIMESTAMP,
            ),
        )
        for extra, code in cases:
            with self.subTest(code=code):
                self.assert_refused(base + extra, code)
        self.assertFalse((self.root / "run").exists())


class Replay(CliCase):
    def test_a_clean_run_replays_with_exit_zero(self):
        out, payload = self.generate_run()
        code, stdout, stderr = invoke(["replay", str(out), "--catalog", self.catalog, "--json"])
        self.assertEqual((code, stderr), (0, ""))
        report = json.loads(stdout)
        self.assertEqual((report["passed"], report["agreeing"]), (True, payload["records"]))
        self.assertEqual(
            [row["id"] for row in report["results"]], [row["id"] for row in payload["rows"]]
        )

    def test_record_replays_one_record_and_refuses_an_unknown_id(self):
        out, payload = self.generate_run()
        chosen = payload["rows"][-1]["id"]
        code, stdout, stderr = invoke(
            ["replay", str(out), "--catalog", self.catalog, "--record", chosen, "--json"]
        )
        self.assertEqual((code, stderr), (0, ""))
        report = json.loads(stdout)
        self.assertEqual(
            (report["record_id"], report["records"], report["passed"]), (chosen, 1, True)
        )
        self.assertEqual(report["results"][0]["id"], chosen)
        self.assert_refused(
            ["replay", str(out), "--catalog", self.catalog, "--record", "twd-nope"],
            cv.FINDING_RECORD_NOT_FOUND,
        )

    def test_the_stored_oracle_command_names_the_replay_interface(self):
        out, _payload = self.generate_run()
        first = json.loads((out / generate.CANDIDATES_FILENAME).read_text().splitlines()[0])
        command = first["oracle"]["command"].replace("<run_dir>", str(out)).split()
        self.assertEqual(command[:2], ["python3", "pipelines/tool_world_cli.py"])
        code, stdout, stderr = invoke([*command[2:], "--catalog", self.catalog, "--json"])
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(json.loads(stdout)["record_id"], first["id"])

    def test_a_run_from_another_catalog_is_refused_before_replay(self):
        out, _payload = self.generate_run()
        run_file = out / generate.RUN_FILENAME
        summary = json.loads(run_file.read_text(encoding="utf-8"))
        summary["catalog_sha256"] = "0" * 64
        run_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        self.assert_refused(
            ["replay", str(out), "--catalog", self.catalog], cv.FINDING_RUN_SHA_MISMATCH
        )

    def test_a_tampered_record_exits_one_with_the_mismatch_reported(self):
        out, payload = self.generate_run()

        def flip(record):
            record["training_view"]["reward"]["success"] = not record["training_view"]["reward"][
                "success"
            ]

        tamper_first_record(out, flip)
        code, stdout, stderr = invoke(["replay", str(out), "--catalog", self.catalog, "--json"])
        self.assertEqual((code, stderr), (1, ""))
        report = json.loads(stdout)
        self.assertEqual((report["passed"], report["agreeing"]), (False, payload["records"] - 1))
        self.assertIn(
            "reward.success differs from the replayed verdict", report["results"][0]["mismatches"]
        )

    def test_corrupt_run_files_are_coded_refusals_not_tracebacks(self):
        out, _payload = self.generate_run()
        replay_argv = ["replay", str(out), "--catalog", self.catalog, "--json"]
        original = (out / generate.CANDIDATES_FILENAME).read_bytes()
        rest = original.splitlines()[1:]
        rewrite_candidates(out, b"\n".join([b"{not json", *rest]) + b"\n")
        self.assert_refused(replay_argv, cv.FINDING_RECORD_MALFORMED)
        self.assert_refused(["render", str(out), "twd-any"], cv.FINDING_RECORD_MALFORMED)
        rewrite_candidates(out, original + b"\xff")
        self.assert_refused(replay_argv, cv.FINDING_RECORD_MALFORMED)
        rewrite_candidates(out, original)
        (out / generate.RUN_FILENAME).write_text('{"format": 1, "format": 2}', encoding="utf-8")
        self.assert_refused(replay_argv, cv.FINDING_RUN_FILE_INVALID)
        self.assert_refused(["render", str(out), "twd-any"], cv.FINDING_RUN_FILE_INVALID)

    def test_candidates_that_drifted_from_the_run_digest_are_refused(self):
        out, _payload = self.generate_run()
        candidates = out / generate.CANDIDATES_FILENAME
        candidates.write_bytes(candidates.read_bytes() + b"\n")
        self.assert_refused(
            ["replay", str(out), "--catalog", self.catalog], cv.FINDING_RUN_SHA_MISMATCH
        )
        self.assert_refused(
            ["replay", str(self.root / "absent"), "--catalog", self.catalog],
            cv.FINDING_RUN_FILE_MISSING,
        )


class Render(CliCase):
    def test_render_prints_the_named_record(self):
        out, payload = self.generate_run()
        wanted = payload["rows"][1]["id"]
        code, stdout, stderr = invoke(["render", str(out), wanted, "--json"])
        self.assertEqual((code, stderr), (0, ""))
        record = json.loads(stdout)
        self.assertEqual((record["id"], record["training_view"]["id"]), (wanted, wanted))
        self.assertEqual(record["environment"]["task_id"], payload["rows"][1]["task_id"])
        code, stdout, _stderr = invoke(["render", str(out), wanted])
        self.assertEqual((code, json.loads(stdout)["id"]), (0, wanted))

    def test_render_refuses_an_unknown_record_or_run(self):
        out, _payload = self.generate_run()
        self.assert_refused(["render", str(out), "twd-missing"], cv.FINDING_RECORD_NOT_FOUND)
        self.assert_refused(
            ["render", str(self.root / "absent"), "twd-missing"], cv.FINDING_RUN_FILE_MISSING
        )


class Tools(CliCase):
    def test_tools_lists_the_core_and_surface_tools_of_a_task(self):
        code, stdout, stderr = invoke(
            ["tools", "--catalog", self.catalog, "--pack", PACK, "--task", ADD_SUB, "--json"]
        )
        self.assertEqual((code, stderr), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual((payload["pack_id"], payload["task_id"]), (PACK, ADD_SUB))
        by_name = {tool["name"]: tool for tool in payload["tools"]}
        self.assertEqual(list(by_name)[:2], [cv.TOOL_REPORT, cv.TOOL_CONFIRM])
        self.assertEqual(by_name[cv.TOOL_REPORT]["surface"], cv.CORE_SURFACE)
        self.assertTrue(by_name["delete_file"]["irreversible"])
        self.assertEqual(by_name["run_tests"]["input_schema"]["required"], ["suite"])

    def test_tools_refuses_an_unknown_pack_or_task(self):
        self.assert_refused(
            ["tools", "--catalog", self.catalog, "--pack", PACK, "--task", "counter.nope"],
            cv.FINDING_TASK_NOT_FOUND,
        )
        self.assert_refused(
            ["tools", "--catalog", self.catalog, "--pack", "nope", "--task", ADD_SUB],
            cv.FINDING_PACK_FILE_MISSING,
        )


class Usage(CliCase):
    def test_argparse_usage_errors_exit_two(self):
        for argv in (
            [],
            ["nope"],
            ["generate", "--seed", "1"],
            ["generate", "--seed", "1", "--count", "1", "--out", "x", "--factory", "shell"],
        ):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as caught:
                invoke(argv)
            self.assertEqual(caught.exception.code, 2)

    def test_the_entry_point_dispatches_in_a_subprocess(self):
        argv = [
            sys.executable,
            str(ENTRY),
            "tools",
            "--catalog",
            self.catalog,
            "--pack",
            PACK,
            "--task",
        ]
        done = subprocess.run(
            argv + [ADD_SUB, "--json"],
            capture_output=True,
            text=True,
            cwd=support.REPO,
            check=False,
        )
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(json.loads(done.stdout)["task_id"], ADD_SUB)
        refused = subprocess.run(
            argv + ["counter.nope"], capture_output=True, text=True, cwd=support.REPO, check=False
        )
        self.assertEqual((refused.returncode, refused.stdout), (2, ""))
        self.assertTrue(refused.stderr.startswith(f"{cv.FINDING_TASK_NOT_FOUND}: "), refused.stderr)


if __name__ == "__main__":
    unittest.main()
