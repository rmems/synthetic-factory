#!/usr/bin/env python3
"""Recursion budget of the EVH resolver and catalog walk, PBC ``_const`` and KCL's clean check.

A helper that sits between two recursive calls adds a Python frame per nesting
level, so a chain the evaluator used to resolve can escape as ``RecursionError``.
These tests pin frames per nesting level and per value leaf to what they were before
the complexity refactor, and check that deep chains still resolve through the
evaluators and through ``extract_plant_catalog`` / ``extract_pairs_list``.
"""

from __future__ import annotations

import ast
import functools
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from evh import catalog_ast as evh_ast  # noqa: E402
from evh import catalog_extract as evh_extract  # noqa: E402
from kcl import _steps as kcl_steps  # noqa: E402
from pbc import mill_extract as pbc_extract  # noqa: E402

DEPTH = 600
# Every EVH level except ``-x`` costs two frames (as on main), so its deep chains stop
# at 400 levels to stay inside the default recursion limit on main too.
TWO_FRAME_DEPTH = 400
LEVELS = 40
_CATALOG_PATH = "experiments/_gen_evh_plants_r801.py"
_RESOLVE_ENV = {"N": 1, "S": "abc", "L": [1, 2]}

_EVH_CATALOG = """
PLANTED_OK = [
    "restock-void", "gift-void", "tax-void", "seat-void", "dual-void",
    "promo-void", "cancel-void", "after-void", "warranty-void", "hold-void",
]
PLANTED_BAD = [
    "flash-cut", "loyalty-cut", "membership-cut", "chargeback-cut", "rain-cut",
    "bundle-cut", "sla-cut", "pickup-cut", "inventory-cut", "window-cut",
]
OUT = MILL / "mill_plants_w.py"

def catalog():
    rows = []
    def add(*a):
        rows.append(a)
    mets = [
        ("ansrel-strict-canary-stale", "cwansstr-eval",
         "AnswerRelevancyMetric(strict_mode=False, threshold=0.15)",
         "AnswerRelevancyMetric(strict_mode=False, threshold=0.28)",
         "AnswerRelevancyMetric(strict_mode=True, threshold=0.5)",
         "halluc-strict-canary-stale", "cwhalstr-eval",
         "HallucinationMetric(strict_mode=False, threshold=0.15)",
         "HallucinationMetric(strict_mode=False, threshold=0.28)",
         "HallucinationMetric(strict_mode=True, threshold=0.5)"),
    ]
    for m in mets:
        add(m[0], m[1], m[5], m[6], m[2], m[7], m[3], m[8], m[4], m[9], "metric")
{body}    return rows
"""


_A = "'a'"


def _uppers(count: int) -> str:
    """``'a'.upper().upper()...``: ``count`` nested str-method calls."""

    return _A + ".upper()" * count


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _negations(count: int, leaf: str = "1") -> str:
    return "-" * count + leaf


def _sum(count: int, term: str) -> str:
    return " + ".join([term] * (count + 1))


def _nested(opener: str, closer: str, leaf: str = "1"):
    return lambda count: opener * count + leaf + closer * count


def _loops(count: int, statement: str = "x = 1") -> str:
    """``catalog()`` body lines: ``statement`` inside ``count`` nested one-item loops."""

    lines = ["    " * (level + 1) + f"for _z{level} in [1]:\n" for level in range(count)]
    return "".join(lines) + "    " * (count + 1) + statement + "\n"


def _catalog(body: str = "") -> str:
    return _EVH_CATALOG.replace("{body}", body)


def _peak_frames(run, subject) -> int:
    """Deepest Python call nesting while ``run(subject)`` runs, counted by a profiler."""

    depth = peak = 0

    def profile(_frame, event, _arg):
        nonlocal depth, peak
        if event == "call":
            depth += 1
            peak = max(peak, depth)
        elif event == "return":
            depth -= 1

    sys.setprofile(profile)
    try:
        run(subject)
    finally:
        sys.setprofile(None)
    return peak


def _frames_per_level(run, make) -> float:
    return (_peak_frames(run, make(2 * LEVELS)) - _peak_frames(run, make(LEVELS))) / LEVELS


def _parsed(make):
    return lambda count: _expr(make(count))


def _nest_value(wrap):
    def make(count):
        value = 1
        for _ in range(count):
            value = wrap(value)
        return value

    return make


_RESOLVE = functools.partial(evh_ast.resolve, env=_RESOLVE_ENV)
_PBC_CONST = functools.partial(pbc_extract._const, where="w")
_ENCODE = functools.partial(evh_extract._encode, level=0, key=None)


def _extract(source: str) -> dict:
    return evh_extract.extract_plant_catalog(source, path=_CATALOG_PATH)


class FramesPerLevel(unittest.TestCase):
    """Main's cost per nesting level: one frame for ``-x`` and PBC ``+`` / list / set,
    two for every other EVH form and for a PBC tuple."""

    CASES = (
        ("evh -x", _RESOLVE, _parsed(_negations), 1),
        ("evh int +", _RESOLVE, _parsed(lambda n: _sum(n, "1")), 2),
        ("evh .upper()", _RESOLVE, _parsed(_uppers), 2),
        ("evh .replace()", _RESOLVE, _parsed(lambda n: _A + ".replace('a', 'b')" * n), 2),
        ("evh [0]", _RESOLVE, _parsed(lambda n: "L" + "[0]" * n), 2),
        ("evh [0:]", _RESOLVE, _parsed(lambda n: "S" + "[0:]" * n), 2),
        ("evh list", _RESOLVE, _parsed(_nested("[", "]")), 2),
        ("evh tuple", _RESOLVE, _parsed(_nested("(", ",)")), 2),
        ("evh dict", _RESOLVE, _parsed(_nested("{1: ", "}")), 2),
        ("evh f-string", _RESOLVE, _parsed(_nested("f'{", "}'")), 2),
        ("evh pair()", _RESOLVE, _parsed(_nested("pair(", ")")), 2),
        ("evh replace arg", _RESOLVE, _parsed(_nested("'a'.replace('a', ", ")", "'b'")), 2),
        ("evh slice bound", _RESOLVE, _parsed(_nested("S[", ":]")), 2),
        ("evh catalog for", _extract, lambda n: _catalog(_loops(n)), 2),
        ("evh _encode dict", _ENCODE, _nest_value(lambda v: {"k": v}), 1),
        ("evh _encode list", _ENCODE, _nest_value(lambda v: [v]), 1),
        ("pbc 'a' +", _PBC_CONST, _parsed(lambda n: _sum(n, _A)), 1),
        ("pbc list", _PBC_CONST, _parsed(_nested("[", "]", _A)), 1),
        ("pbc tuple", _PBC_CONST, _parsed(_nested("(", ",)", _A)), 2),
        ("kcl dict", kcl_steps.assert_clean, _nest_value(lambda v: {"k": v}), 1),
        ("kcl list", kcl_steps.assert_clean, _nest_value(lambda v: [v]), 1),
    )

    def test_each_nesting_level_costs_what_it_did_before_the_split(self):
        for label, run, make, frames in self.CASES:
            with self.subTest(label):
                self.assertEqual(_frames_per_level(run, make), frames)


class ValueLeafFrames(unittest.TestCase):
    """A constant or bound name is resolved inside the evaluator's own frame."""

    CASES = (
        ("evh constant", _RESOLVE, "1"),
        ("evh name", _RESOLVE, "N"),
        ("pbc constant", _PBC_CONST, _A),
    )

    def test_a_value_leaf_costs_one_frame(self):
        for label, run, source in self.CASES:
            with self.subTest(label):
                self.assertEqual(_peak_frames(run, _expr(source)), 1)


class DeepChains(unittest.TestCase):
    def test_evaluators_resolve_deep_chains(self):
        two = TWO_FRAME_DEPTH
        cases = (
            ("evh -x", _RESOLVE, _negations(DEPTH), 1),
            ("evh int +", _RESOLVE, _sum(two, "1"), two + 1),
            ("evh .upper()", _RESOLVE, _uppers(two), "A"),
            ("evh [0:]", _RESOLVE, "S" + "[0:]" * two, "abc"),
            ("pbc 'a' +", _PBC_CONST, _sum(DEPTH, _A), "a" * (DEPTH + 1)),
        )
        for label, run, source, expected in cases:
            with self.subTest(label):
                self.assertEqual(run(_expr(source)), expected)

    def test_pbc_refuses_a_unary_chain_without_recursing(self):
        node = _expr(_negations(DEPTH))
        with self.assertRaisesRegex(ValueError, r"^w: not a constant literal$"):
            _PBC_CONST(node)

    def test_extract_plant_catalog_reads_deep_chains(self):
        expected = _extract(_catalog())
        self.assertEqual(expected["catalogs"][0]["first_slug"], "ansrel-strict-canary-stale")
        deep_module = (
            _catalog()
            + f"DEEP = {_negations(DEPTH)}\n"
            + f"UPPER = {_uppers(TWO_FRAME_DEPTH)}\n"
        )
        for label, source in (
            ("module constants", deep_module),
            ("catalog body", _catalog(_loops(0, f"x = {_negations(DEPTH)}"))),
            ("nested loops", _catalog(_loops(80, f"x = {_negations(DEPTH)}"))),
        ):
            with self.subTest(label):
                self.assertEqual(_without_digest(_extract(source)), _without_digest(expected))

    def test_extract_pairs_list_reads_a_600_deep_constant(self):
        source = f"WIDE = {_sum(DEPTH, repr('a'))}\nPAIRS = []\n"
        self.assertEqual(pbc_extract.extract_pairs_list(source), [])


def _without_digest(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "sha256"}


if __name__ == "__main__":
    unittest.main()
