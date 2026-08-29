"""PASS_TO_PASS reference suite for the shared counter pack.

Named outside test_*.py so factory ``unittest discover`` does not collect it.
"""

from __future__ import annotations

import unittest

from counter import Counter


class ReferenceTests(unittest.TestCase):
    def test_add_increments(self):
        counter = Counter(1)
        self.assertEqual(counter.add(2), 3)
        self.assertEqual(counter.get(), 3)

    def test_get_initial_value(self):
        self.assertEqual(Counter(4).get(), 4)
