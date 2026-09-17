#!/usr/bin/env python3
"""Three more CLIs confine operator paths right after parsing (S8707, B4 of #211).

Preventive: SonarCloud reports nothing on ``curate_trajectory_preferences``,
``preference_arms`` or ``next_round`` today, but each has the same taint shape
as the CLIs of B2 and B3. Each now refuses a path outside the working, home and
temp trees with argparse's own error shape (exit 2) before any filesystem sink
runs, keeps working for paths under a temporary directory, and never confines
``preference_arms --file``, which carries diagnosis basenames rather than
paths.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_TESTS = Path(__file__).resolve().parent
_PIPELINES = _TESTS.parent / "pipelines"
for entry in (_TESTS, _PIPELINES):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import argparse  # noqa: E402

from preference_arms_support import diagnosis_document, run_cli  # noqa: E402
from trajectory_preference_support import trajectory_pair  # noqa: E402

import curate_trajectory_preferences  # noqa: E402
import next_round  # noqa: E402
import preference_arms  # noqa: E402

ARM_ROUND = _TESTS / "fixtures" / "preference-arms" / "batch-r11.jsonl"
REFUSAL = "outside the working, home and temp trees"
OUTSIDE = ("/etc/passwd", "../" * 12 + "etc/passwd")


class _FunnelCase(unittest.TestCase):
    """Shared assertions for the three post-parse funnels."""

    def assertRefused(self, call, *args):
        """``call(*args)`` exits 2 with argparse's refusal; args are bound here, not in a closure."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            call(*args)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(REFUSAL, stderr.getvalue())
        self.assertIn("error:", stderr.getvalue())


class TrajectoryPreferencesFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="curate_trajectory_preferences.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        for name in curate_trajectory_preferences.Inputs._fields:
            for candidate in OUTSIDE:
                with self.subTest(name=name, candidate=candidate):
                    self.assertRefused(
                        curate_trajectory_preferences._inputs,
                        self.parser,
                        SimpleNamespace(**{name: Path(candidate)}),
                    )

    def test_paths_under_the_operator_trees_resolve_and_absent_ones_stay_none(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(os.path.realpath(td))
            paths = curate_trajectory_preferences._inputs(
                self.parser,
                SimpleNamespace(source=Path(td) / "batch.jsonl", output=Path(td) / "out.jsonl"),
            )
        self.assertEqual(paths.source, root / "batch.jsonl")
        self.assertEqual(paths.output, root / "out.jsonl")
        self.assertIsNone(paths.manifest)

    def test_parse_args_still_returns_the_namespace(self):
        args = curate_trajectory_preferences.parse_args(["scan", "some-dir"])
        self.assertEqual(args.command, "scan")
        self.assertEqual(args.source, Path("some-dir"))


class TrajectoryPreferencesCli(_FunnelCase):
    def test_every_subcommand_refuses_before_its_sink_runs(self):
        commands = {
            "scan": ["scan", "{bad}"],
            "curate source": ["curate", "{bad}", "--output", "o", "--manifest", "m"],
            "curate --output": ["curate", "src", "--output", "{bad}", "--manifest", "m"],
            "curate --manifest": ["curate", "src", "--output", "o", "--manifest", "{bad}"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (
                    self.subTest(command=label, bad=bad),
                    mock.patch.object(curate_trajectory_preferences, "curate_source") as source,
                    mock.patch.object(curate_trajectory_preferences, "write_run") as writer,
                    mock.patch.object(
                        curate_trajectory_preferences, "_reject_raw_destination"
                    ) as raw,
                ):
                    self.assertRefused(
                        curate_trajectory_preferences.main,
                        [a.replace("{bad}", bad) for a in argv],
                    )
                    source.assert_not_called()
                    writer.assert_not_called()
                    raw.assert_not_called()

    def test_the_raw_destination_refusal_still_runs_before_the_scan(self):
        """Confinement is added in front of the eager guard, not in place of it."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "pairs.jsonl"
            source.write_text(json.dumps(trajectory_pair()) + "\n", encoding="utf-8")
            calls = []
            with (
                mock.patch.object(
                    curate_trajectory_preferences,
                    "_reject_raw_destination",
                    side_effect=lambda path, label: calls.append(label),
                ),
                mock.patch.object(
                    curate_trajectory_preferences,
                    "curate_source",
                    side_effect=ValueError("the scan is reached only after both guards"),
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = curate_trajectory_preferences.main(
                    [
                        "curate",
                        str(source),
                        "--output",
                        str(root / "out.jsonl"),
                        "--manifest",
                        str(root / "manifest.jsonl"),
                    ]
                )
        self.assertEqual(status, 1)
        self.assertEqual(calls, ["output", "manifest"])

    def test_paths_under_a_temporary_directory_still_work(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "pairs.jsonl"
            source.write_text(json.dumps(trajectory_pair()) + "\n", encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(
                    curate_trajectory_preferences.main(["scan", str(source), "--json"]), 0
                )
            summary = json.loads(stdout.getvalue())["summary"]
        self.assertEqual(summary["source"], os.path.realpath(source))
        self.assertEqual(summary["trajectory_pairs_considered"], 1)


class PreferenceArmsFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="preference_arms.py")

    def test_each_path_argument_is_refused_outside_the_operator_trees(self):
        for name in preference_arms.Inputs._fields:
            for candidate in OUTSIDE:
                with self.subTest(name=name, candidate=candidate):
                    self.assertRefused(
                        preference_arms._inputs,
                        self.parser,
                        SimpleNamespace(**{name: Path(candidate)}),
                    )

    def test_paths_under_the_operator_trees_resolve_and_absent_ones_stay_none(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(os.path.realpath(td))
            stage_name = "r11-" + "0" * 32
            paths = preference_arms._inputs(
                self.parser, SimpleNamespace(staging_dir=Path(td) / stage_name)
            )
            self.assertEqual(paths.staging_dir, root / stage_name)
            self.assertIsNone(paths.source)
            paths = preference_arms._inputs(self.parser, SimpleNamespace(source=Path(td)))
        self.assertEqual(paths.source, root)
        self.assertIsNone(paths.staging_dir)

    def test_diagnosis_basenames_are_not_paths_and_stay_off_the_funnel(self):
        self.assertNotIn("diagnosis_files", preference_arms.Inputs._fields)
        with self.assertRaises(preference_arms.PreferenceArmsError):
            preference_arms._require_diagnosis_basename("../diagnosis-01-r11.md", "11")


class PreferenceArmsCli(_FunnelCase):
    def test_every_subcommand_refuses_before_its_sink_runs(self):
        commands = {
            "scan": ["scan", "{bad}"],
            "verify-handoff": ["verify-handoff", "{bad}", "--file", "diagnosis-01-r11.md"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (
                    self.subTest(command=label, bad=bad),
                    mock.patch.object(preference_arms, "scan_source") as scan,
                    mock.patch.object(preference_arms, "verify_diagnosis_handoff") as verify,
                    mock.patch.object(
                        preference_arms, "write_diagnosis_handoff_receipt"
                    ) as writer,
                ):
                    self.assertRefused(
                        preference_arms.main, [a.replace("{bad}", bad) for a in argv]
                    )
                    scan.assert_not_called()
                    verify.assert_not_called()
                    writer.assert_not_called()

    def test_verify_handoff_still_refuses_a_symlinked_staging_directory(self):
        """Confinement resolves symlinks; the staging guard must still see the typed path.

        Before this slice the CLI handed the path as typed to the library, whose
        guard requires it to be real and canonical. A realpath'd input would
        satisfy that guard by construction, so the CLI re-applies it to the
        typed path and refuses exactly what it refused before.
        """
        token = "a" * 32
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            stage = root / "outputs" / "staging" / "2026-08-17" / "failure-as-fuel-preference-cascade" / f"r11-{token}"
            stage.mkdir(parents=True)
            names = []
            for index in (1, 2, 3):
                name = f"diagnosis-{index:02d}-r11.md"
                (stage / name).write_text(diagnosis_document(index), encoding="utf-8")
                names.append(name)
            link = root / "linked-stage"
            link.symlink_to(stage, target_is_directory=True)

            files = [flag for name in names for flag in ("--file", name)]
            code, _, err = run_cli(["verify-handoff", str(link), *files])
            self.assertEqual(code, 1)
            self.assertIn("staging directory is not a real directory", err)

            code, out, _ = run_cli(["verify-handoff", str(stage), *files])
            self.assertEqual(code, 0, out)

    def test_scan_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "batch-r11.jsonl"
            source.write_text(ARM_ROUND.read_text(encoding="utf-8"), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = preference_arms.main(["scan", str(source)])
        self.assertEqual(status, 0)
        self.assertIn("arm gate: PASS", stderr.getvalue())
        self.assertIn("Blocked: 0", stdout.getvalue())


class NextRoundFunnel(_FunnelCase):
    parser = argparse.ArgumentParser(prog="next_round.py")

    def test_the_path_positional_is_refused_outside_the_operator_trees(self):
        for candidate in OUTSIDE:
            with self.subTest(candidate=candidate):
                self.assertRefused(
                    next_round._confined_path, self.parser, SimpleNamespace(path=candidate)
                )

    def test_a_path_under_the_operator_trees_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            confined = next_round._confined_path(self.parser, SimpleNamespace(path=td))
        self.assertEqual(confined, Path(os.path.realpath(td)))

    def test_parse_args_still_returns_the_namespace(self):
        args = next_round.parse_args(["--allocate", "3", "some-dir"])
        self.assertEqual(args.path, "some-dir")
        self.assertEqual(args.allocate, 3)
        self.assertFalse(args.write_index)


class NextRoundCli(_FunnelCase):
    def test_every_mode_refuses_before_its_sink_runs(self):
        commands = {
            "plain": ["{bad}"],
            "--allocate": ["--allocate", "4", "{bad}"],
            "--write-index": ["--write-index", "{bad}"],
        }
        for label, argv in commands.items():
            for bad in OUTSIDE:
                with (
                    self.subTest(mode=label, bad=bad),
                    mock.patch.object(next_round, "allocate") as allocate,
                    mock.patch.object(next_round, "write_index") as index,
                ):
                    self.assertRefused(next_round.main, [a.replace("{bad}", bad) for a in argv])
                    allocate.assert_not_called()
                    index.assert_not_called()

    def test_a_missing_directory_still_exits_2_after_the_funnel(self):
        with tempfile.TemporaryDirectory() as td:
            stderr = io.StringIO()
            with (
                contextlib.redirect_stderr(stderr),
                self.assertRaises(SystemExit) as raised,
            ):
                next_round.main([os.path.join(td, "absent")])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("error: not a directory", stderr.getvalue())

    def test_a_factory_directory_under_a_temporary_directory_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "lane"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text("{}\n", encoding="utf-8")
            stdout = io.StringIO()
            with (
                contextlib.redirect_stdout(stdout),
                self.assertRaises(SystemExit) as raised,
            ):
                next_round.main([str(factory)])
        self.assertEqual(raised.exception.code, 0)
        plan = json.loads(stdout.getvalue())
        self.assertEqual(plan["factory"], "lane")
        self.assertEqual(plan["next_round"], 2)
        self.assertEqual(plan["write"], "batch-r02.jsonl")


if __name__ == "__main__":
    unittest.main()
