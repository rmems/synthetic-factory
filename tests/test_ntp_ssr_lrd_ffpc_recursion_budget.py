#!/usr/bin/env python3
"""Recursion budget of the NTP, SSR, LRD and FFPC literal evaluators.

A helper that sits between two recursive calls adds a Python frame per nesting
level, so a chain the evaluator used to resolve can escape as ``RecursionError``.
These tests pin each evaluator's frames per nesting level and per value leaf to what
they were before the complexity refactor, and check that 600-deep chains still
resolve through the evaluator and through the public extractor. FFPC's resolver has
no unbracketed chain, so only its per-level cost is pinned.
"""

from __future__ import annotations

import ast
import functools
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from ffpc import catalog as ffpc_catalog  # noqa: E402
from lrd import catalog as lrd_catalog  # noqa: E402
from lrd import catalog_extract as lrd_extract  # noqa: E402
from ntp import catalog_ast as ntp_ast  # noqa: E402
from ntp import catalog_extract as ntp_extract  # noqa: E402
from ssr import catalog_ast as ssr_ast  # noqa: E402
from ssr import catalog_extract as ssr_extract  # noqa: E402

DEPTH = 600
LEVELS = 40

_NTP_SNIPPET = """
FACTORY = "notebook-to-pipeline-factory"
GEN = "grok-4.6"
START = {start}
SUCCESS = [
    S(slug="kubeflow-pipeline-run-as-dest", stem="kfp", src="data/kfp_src.csv",
      rows={rows}, transform="df = df.copy()", token="kfp leftover",
      ban="kfp leftover|.kfp/run", distinct="not flyte dest",
      plan="treat leftover as dest.", cell="kfp leftover; # dest",
      artifact={artifact}, kind="KFP leftover JSON",
      cmd="kfp leftover && cat .kfp/run.json", file_obs="not parquet"),
]
LEFTOVER = [
    L(slug="altair-vl-json-leftover", stem="alvl", src="data/alvl_src.csv",
      rows=13011, transform="df = df.copy()", leftover=".altair/vl.json",
      left_token="altair leftover", ban="altair leftover|.altair/vl",
      distinct="not kfp leftover", plan="ship leftover as dest.",
      cell="altair leftover; # json", residual="still on disk",
      handoff="leftover not cleaned", kind="Altair leftover JSON",
      wrap="tar -cf alvl.parquet .altair/vl.json", wrap_obs="tar leftover"),
]
"""

_SSR_SNIPPET = """
FACTORY = "secret-scan-remediation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = {first}
PAIRS: list[tuple[dict, dict]] = [
    (
        {{"slug": "gitleaks-allowlist-overfit", "scanner": {scanner}}},
        {{"slug": "trufflehog-p8-path-filter", "scanner": "trufflehog"}},
    ),
]
"""

_LRD_SNIPPET = """
PAIRS = [
    dict(
        mod="otelsjwt", drop="otelstrace", stack="otel", field="session_jwt",
        naive="drop traces", conf="processor.yaml", conf2="pipeline.yaml",
        oldc="attributes: [http.url]", newc="attributes: []",
        old2="processors: [batch]", new2="processors: []", test="test_redact.py",
        ticket="OTEL-L6", slug="otel-session-jwt", fail="otel-drop-traces-handoff",
        domain="otel-leftover-session-jwt-vs-drop-traces",
    )
]
"""


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _negations(count: int, leaf: str = "1") -> str:
    return "-" * count + leaf


def _sum(count: int, term: str = "'a'") -> str:
    """``term + term + ...`` with ``count`` additions (left-associative)."""

    return " + ".join([term] * (count + 1))


def _padded(literal: str) -> str:
    """``literal + "" + "" ...``: the same string behind ``DEPTH`` additions."""

    return " + ".join([literal] + ['""'] * DEPTH)


def _path(count: int) -> str:
    return "R" + " / 'a'" * count


def _nested(opener: str, closer: str, leaf: str = "1"):
    return lambda count: opener * count + leaf + closer * count


def _peak_frames(evaluate, node) -> int:
    """Deepest Python call nesting while ``evaluate(node)`` runs, counted by a profiler."""

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
        evaluate(node)
    finally:
        sys.setprofile(None)
    return peak


def _frames_per_level(evaluate, make) -> float:
    deep = _peak_frames(evaluate, _expr(make(2 * LEVELS)))
    shallow = _peak_frames(evaluate, _expr(make(LEVELS)))
    return (deep - shallow) / LEVELS


def _without_digest(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "sha256"}


_ENV = {"N": 1, "S": "a"}
_LRD_LITERAL = functools.partial(lrd_extract._literal, where="w")
_FFPC_RESOLVE = functools.partial(ffpc_catalog._resolve_expr, consts={})
_LIST = _nested("[", "]")
_TUPLE = _nested("(", ",)")
_DICT = _nested("{1: ", "}")
_FSTRING = _nested("f'{", "}'")


class FramesPerLevel(unittest.TestCase):
    """One frame per ``-x`` / ``a + b`` / ``a / b`` level, two per container or f-string."""

    CASES = (
        ("ntp -x", ntp_ast.literal_value, _negations, 1),
        ("ntp a + b", ntp_ast.literal_value, _sum, 1),
        ("ntp list", ntp_ast.literal_value, _LIST, 2),
        ("ntp tuple", ntp_ast.literal_value, _TUPLE, 2),
        ("ntp dict", ntp_ast.literal_value, _DICT, 2),
        ("ntp f-string", ntp_ast.literal_value, _FSTRING, 2),
        ("ntp path /", ntp_ast.joined_path_constant, _path, 1),
        ("ntp path str()", ntp_ast.joined_path_constant, _nested("str(", ")", "'a'"), 1),
        ("ssr -x", ssr_ast.literal_value, _negations, 1),
        ("ssr a + b", ssr_ast.literal_value, _sum, 1),
        ("ssr list", ssr_ast.literal_value, _LIST, 2),
        ("ssr tuple", ssr_ast.literal_value, _TUPLE, 2),
        ("ssr dict", ssr_ast.literal_value, _DICT, 2),
        ("ssr f-string", ssr_ast.literal_value, _FSTRING, 2),
        ("ssr path /", ssr_ast.joined_path_constant, _path, 1),
        ("lrd _literal -x", _LRD_LITERAL, _negations, 1),
        ("lrd _const_eval -x", lrd_catalog._const_eval, _negations, 1),
        ("lrd _const_eval list", lrd_catalog._const_eval, _LIST, 1),
        ("lrd _const_eval tuple", lrd_catalog._const_eval, _TUPLE, 2),
        ("lrd _const_eval dict", lrd_catalog._const_eval, _DICT, 1),
        ("lrd _const_eval dict()", lrd_catalog._const_eval, _nested("dict(a=", ")"), 1),
        ("ffpc list", _FFPC_RESOLVE, _LIST, 1),
        ("ffpc tuple", _FFPC_RESOLVE, _TUPLE, 2),
        ("ffpc dict", _FFPC_RESOLVE, _nested("{'k': ", "}"), 1),
    )

    def test_each_nesting_level_costs_what_it_did_before_the_split(self):
        for label, evaluate, make, frames in self.CASES:
            with self.subTest(label):
                self.assertEqual(_frames_per_level(evaluate, make), frames)


class ValueLeafFrames(unittest.TestCase):
    """A constant or bound name is resolved inside the evaluator's own frame."""

    CASES = (
        ("ntp constant", ntp_ast.literal_value, "1"),
        ("ntp name", functools.partial(ntp_ast.literal_value, env=_ENV), "N"),
        ("ntp path name", ntp_ast.joined_path_constant, "R"),
        ("ssr constant", ssr_ast.literal_value, "1"),
        ("ssr name", functools.partial(ssr_ast.literal_value, env=_ENV), "N"),
        ("lrd _literal constant", _LRD_LITERAL, "1"),
        ("lrd _const_eval constant", lrd_catalog._const_eval, "1"),
    )

    def test_a_value_leaf_costs_one_frame(self):
        for label, evaluate, source in self.CASES:
            with self.subTest(label):
                self.assertEqual(_peak_frames(evaluate, _expr(source)), 1)


class DeepChains(unittest.TestCase):
    def test_evaluators_resolve_600_deep_chains(self):
        letters = "a" * (DEPTH + 1)
        joined = "/".join(["a"] * DEPTH)
        cases = (
            ("ntp -x", ntp_ast.literal_value, _negations(DEPTH), 1),
            ("ntp a + b", ntp_ast.literal_value, _sum(DEPTH), letters),
            ("ssr -x", ssr_ast.literal_value, _negations(DEPTH), 1),
            ("ssr a + b", ssr_ast.literal_value, _sum(DEPTH), letters),
            ("ntp path", ntp_ast.joined_path_constant, _path(DEPTH), joined),
            ("ssr path", ssr_ast.joined_path_constant, _path(DEPTH), joined),
            ("lrd _literal", _LRD_LITERAL, _negations(DEPTH), 1),
            ("lrd _const_eval", lrd_catalog._const_eval, _negations(DEPTH), 1),
        )
        for label, evaluate, source, expected in cases:
            with self.subTest(label):
                self.assertEqual(evaluate(_expr(source)), expected)

    def test_ntp_call_arguments_resolve_600_deep_chains(self):
        node = _expr(f"S(rows={_negations(DEPTH)}, tag={_sum(DEPTH)})")
        self.assertEqual(ntp_ast.call_kwargs(node), {"rows": 1, "tag": "a" * (DEPTH + 1)})
        node = _expr(f"S({_negations(DEPTH)}, {_sum(DEPTH)})")
        self.assertEqual(ntp_ast.call_posargs(node), [1, "a" * (DEPTH + 1)])

    def test_ntp_extract_mill_catalog_reads_600_deep_chains(self):
        path = "experiments/ntp-mill-r1326.py"
        plain = _NTP_SNIPPET.format(start="1326", rows="12011", artifact='".kfp/run.json"')
        deep = _NTP_SNIPPET.format(
            start=_negations(DEPTH, "1326"),
            rows=_negations(DEPTH, "12011"),
            artifact=_padded('".kfp/run.json"'),
        )
        deep += f"DEEP = {_negations(DEPTH)}\nWIDE = {_sum(DEPTH)}\n"
        expected = _without_digest(ntp_extract.extract_mill_catalog(plain, path=path))
        self.assertEqual(expected["catalog_first"], 1326)
        self.assertEqual(expected["success"][0]["artifact"], ".kfp/run.json")
        self.assertEqual(_without_digest(ntp_extract.extract_mill_catalog(deep, path=path)), expected)

    def test_ntp_companion_path_reads_600_deep_chains(self):
        source = f"MILL = {_path(DEPTH)} / 'ntp-mill-r1326.py'\n"
        self.assertEqual(ntp_extract.extract_companion_path(source), "experiments/ntp-mill-r1326.py")
        source = f"x = s.replace('old', {_padded(repr('ntp-mill-r7.py'))})\n"
        self.assertEqual(ntp_extract.extract_companion_path(source), "experiments/ntp-mill-r7.py")

    def test_ssr_extract_mill_catalog_reads_600_deep_chains(self):
        path = "experiments/ssr-mill-r181.py"
        plain = _SSR_SNIPPET.format(first="181", scanner='"gitleaks"')
        deep = _SSR_SNIPPET.format(first=_negations(DEPTH, "181"), scanner=_padded('"gitleaks"'))
        deep += f"DEEP = {_negations(DEPTH)}\n"
        expected = _without_digest(ssr_extract.extract_mill_catalog(plain, path=path))
        self.assertEqual(expected["catalog_first"], 181)
        self.assertEqual(_without_digest(ssr_extract.extract_mill_catalog(deep, path=path)), expected)

    def test_lrd_plants_from_source_reads_a_600_deep_base(self):
        plain = lrd_catalog.plants_from_source(_LRD_SNIPPET, mill_id="lrd_r0007", source="tiny.py")
        deep_source = _LRD_SNIPPET + f"BASE = {_negations(DEPTH, '7')}\n"
        deep = lrd_catalog.plants_from_source(deep_source, mill_id="lrd_r0007", source="tiny.py")
        self.assertEqual(plain[0]["base_round"], 7)
        self.assertEqual(deep, plain)


if __name__ == "__main__":
    unittest.main()
