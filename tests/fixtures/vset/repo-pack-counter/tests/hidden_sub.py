"""FAIL_TO_PASS hidden suite for Counter.sub.

A pass is meaningful only when the oracle itself is independently valid.
"""

from __future__ import annotations

import unittest

from counter import Counter


class HiddenSubTests(unittest.TestCase):
    def test_sub_decrements(self):
        counter = Counter(5)
        self.assertEqual(counter.sub(2), 3)
        self.assertEqual(counter.get(), 3)

    def test_sub_negative_delta_adds(self):
        counter = Counter(1)
        self.assertEqual(counter.sub(-4), 5)
        self.assertEqual(counter.get(), 5)
