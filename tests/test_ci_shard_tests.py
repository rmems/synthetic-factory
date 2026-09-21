"""Tests for the CI unittest shard runner."""

from __future__ import annotations

import contextlib
import os
import runpy
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import ci_shard_tests


class CiShardTests(unittest.TestCase):
    def test_shards_partition_the_input(self):
        modules = ["test_a", "test_b", "test_c", "test_d", "test_e"]
        shards = [ci_shard_tests.shard_modules(modules, shard, 4) for shard in range(4)]

        self.assertEqual(set().union(*map(set, shards)), set(modules))
        self.assertEqual(sum(map(len, shards)), len(modules))
        for index, shard in enumerate(shards):
            for other in shards[index + 1:]:
                self.assertTrue(set(shard).isdisjoint(other))

    def test_discovered_modules_are_exactly_test_files(self):
        expected = sorted(path.stem for path in (REPO / "tests").glob("test_*.py"))

        self.assertEqual(ci_shard_tests.discover_modules(), expected)

    def test_list_prints_selected_test_modules(self):
        output = StringIO()
        with contextlib.redirect_stdout(output):
            result = ci_shard_tests.main(["--shard", "0", "--shards", "4", "--list"])

        self.assertEqual(result, 0)
        listed = output.getvalue().splitlines()
        self.assertTrue(listed)
        self.assertTrue(all(name.startswith("test_") for name in listed))

    def test_run_uses_discover_environment(self):
        completed = mock.Mock(returncode=7)
        with (
            mock.patch.object(ci_shard_tests.subprocess, "run", return_value=completed) as run,
            mock.patch.dict(os.environ, {"PYTHONPATH": "existing"}, clear=True),
        ):
            result = ci_shard_tests.main(["--shard", "0", "--shards", "4"])

        self.assertEqual(result, 7)
        command = run.call_args.args[0]
        self.assertEqual(command[0], str(Path(sys.executable).resolve()))
        self.assertEqual(command[1:4], ["-m", "unittest", "-b"])
        self.assertEqual(run.call_args.kwargs["cwd"], ci_shard_tests.ROOT)
        self.assertEqual(
            run.call_args.kwargs["env"]["PYTHONPATH"],
            f"{REPO / 'tests'}{os.pathsep}existing",
        )

    def test_run_can_enable_parallel_coverage(self):
        completed = mock.Mock(returncode=0)
        with (
            mock.patch.object(
                ci_shard_tests.subprocess, "run", return_value=completed
            ) as run,
            mock.patch.dict(os.environ, {}, clear=True),
        ):
            result = ci_shard_tests.main(
                ["--shard", "0", "--shards", "4", "--coverage"]
            )

        self.assertEqual(result, 0)
        command = run.call_args.args[0]
        self.assertEqual(command[1:7], ["-m", "coverage", "run", "-p", "-m", "unittest"])
        self.assertEqual(run.call_args.kwargs["env"]["PYTHONPATH"], str(REPO / "tests"))

    def test_invalid_shard_arguments_are_rejected(self):
        with self.assertRaises(SystemExit) as raised:
            ci_shard_tests.main(["--shard", "4", "--shards", "4"])

        self.assertEqual(raised.exception.code, 2)

    def test_script_entrypoint_exits_with_list(self):
        with (
            mock.patch.object(
                sys,
                "argv",
                ["ci_shard_tests.py", "--shard", "0", "--shards", "4", "--list"],
            ),
            self.assertRaises(SystemExit) as raised,
        ):
            runpy.run_path(str(REPO / "scripts" / "ci_shard_tests.py"), run_name="__main__")

        self.assertEqual(raised.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
