"""Tests for the CI unittest shard runner."""

from __future__ import annotations

import contextlib
import os
import runpy
import sys
import tempfile
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
        captured: dict[str, object] = {}
        fake_result = mock.Mock(wasSuccessful=mock.Mock(return_value=False))

        def capture_run(_self, _suite):
            captured["pythonpath"] = os.environ.get("PYTHONPATH")
            captured["cwd"] = Path.cwd()
            return fake_result

        with (
            mock.patch.object(unittest.TextTestRunner, "run", capture_run),
            mock.patch.object(
                unittest.TestLoader, "loadTestsFromNames", return_value=mock.Mock()
            ),
            mock.patch.dict(os.environ, {"PYTHONPATH": "existing"}, clear=True),
        ):
            result = ci_shard_tests.main(["--shard", "0", "--shards", "4"])

        self.assertEqual(result, 1)
        self.assertEqual(
            captured["pythonpath"],
            f"{REPO / 'tests'}{os.pathsep}existing",
        )
        self.assertEqual(captured["cwd"], REPO)

    def test_run_can_enable_parallel_coverage(self):
        fake_result = mock.Mock(wasSuccessful=mock.Mock(return_value=True))
        coverage_mod = mock.MagicMock()
        with (
            mock.patch.dict(sys.modules, {"coverage": coverage_mod}),
            mock.patch.object(unittest.TextTestRunner, "run", return_value=fake_result),
            mock.patch.object(
                unittest.TestLoader, "loadTestsFromNames", return_value=mock.Mock()
            ),
            mock.patch.dict(os.environ, {}, clear=True),
        ):
            result = ci_shard_tests.main(
                ["--shard", "0", "--shards", "4", "--coverage"]
            )

        self.assertEqual(result, 0)
        coverage_mod.Coverage.assert_called_once_with(data_suffix=True)
        coverage_mod.Coverage.return_value.start.assert_called_once()
        coverage_mod.Coverage.return_value.stop.assert_called_once()
        coverage_mod.Coverage.return_value.save.assert_called_once()

    def test_run_selected_modules_with_coverage_writes_parallel_data_files(self):
        coverage = __import__("coverage")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests_dir = root / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_tiny.py").write_text(
                "import unittest\n\n"
                "class Tiny(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            (root / ".coveragerc").write_text(
                "[run]\nbranch = True\nsource = tests\n",
                encoding="utf-8",
            )

            result = ci_shard_tests.run_selected_modules(
                ["test_tiny"], coverage=True, root=root
            )

            self.assertEqual(result, 0)
            data_files = sorted(root.glob(".coverage*"))
            self.assertTrue(data_files)
            self.assertTrue(
                any(path.name != ".coverage" for path in data_files),
                msg=f"expected suffixed parallel data files, got {data_files}",
            )
            configured = coverage.Coverage(config_file=str(root / ".coveragerc"))
            self.assertTrue(configured.get_option("run:branch"))

    def test_run_selected_modules_invokes_buffered_unittest(self):
        fake_result = mock.Mock(wasSuccessful=mock.Mock(return_value=True))
        with (
            mock.patch.object(unittest, "TextTestRunner") as runner_cls,
            mock.patch.object(unittest.TestLoader, "loadTestsFromNames", return_value=mock.Mock()),
            mock.patch.dict(os.environ, {}, clear=True),
        ):
            runner_cls.return_value.run.return_value = fake_result
            result = ci_shard_tests.run_selected_modules(
                ["test_ci_shard_tests"], coverage=False
            )

        self.assertEqual(result, 0)
        runner_cls.assert_called_once_with(buffer=True)
        runner_cls.return_value.run.assert_called_once()

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
