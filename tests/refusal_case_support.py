"""Shared table-driven refusal assertion for the ``test_*_branches`` modules.

Each branch-pinning module lists ``(label, value, message)`` rows. The mixin
runs one exception assertion per row inside its own ``subTest`` so a failing
row is reported by label and the remaining rows still run. Not named
``test_*`` so it is not itself collected.
"""

from __future__ import annotations


class RefusalCaseAssertions:
    """Mixin for ``unittest.TestCase`` classes that pin exact refusal messages."""

    def assert_each_refuses(self, error, call, cases) -> None:
        """Assert ``call(value)`` raises ``error`` with exactly ``message`` for each row."""

        for label, value, message in cases:
            with self.subTest(label):
                with self.assertRaises(error) as caught:
                    call(value)
                self.assertEqual(str(caught.exception), message)
