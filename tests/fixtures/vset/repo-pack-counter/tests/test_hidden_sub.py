"""FAIL_TO_PASS hidden tests for Counter.sub. Meaningful only if the oracle is valid."""

from __future__ import annotations

import unittest

from counter import Counter


class HiddenSubTests(unittest.TestCase):
    def test_sub_decrements(self):
        counter = Counter(5)
        self.assertEqual(counter.sub(2), 3)
        self.assertEqual(counter.get(), 3)

    def test_sub_negative_delta_adds(self):
        self.assertEqual(Counter(1).sub(-4), 5)
