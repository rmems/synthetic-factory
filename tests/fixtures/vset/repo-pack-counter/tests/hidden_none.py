"""FAIL_TO_PASS hidden suite for rejecting None.

A pass is meaningful only when the oracle itself is independently valid.
"""

from __future__ import annotations

import unittest

from counter import Counter


class HiddenNoneTests(unittest.TestCase):
    def test_add_rejects_none(self):
        with self.assertRaises(ValueError):
            Counter().add(None)
