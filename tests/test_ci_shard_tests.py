"""Tests for the CI unittest shard runner."""

from __future__ import annotations

import contextlib
import sys
import unittest
from io import StringIO
from pathlib import Path

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
        self.assertTrue(all(name.startswith("tests.test_") for name in listed))


if __name__ == "__main__":
    unittest.main()
