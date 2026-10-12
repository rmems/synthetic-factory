"""Pin the refusals and literal results that explicit type narrowing now spells out.

Each check below used to sit inside ``refuse_when(...)`` or behind a helper whose
result the type checker could not see. The narrowing moved the check into an
``if`` that calls the ``NoReturn`` refusal, so these tests pin the codes and
messages main already produced, plus the recursion outcomes of the literal
evaluators whose helpers changed shape.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipelines.cer import cli as cer_cli
from pipelines.cer.usage_burst_plan import load_mill_usage_burst_plan
from pipelines.crp import wave_catalog
from pipelines.crp._contract import FINDING_AST_NOT_A_PLANT, CrpRefusal
from pipelines.lhc import catalog_ast_literals as lhc_literals
from pipelines.lhc import catalog_extract_plants as lhc_plants
from pipelines.lll import catalog as lll_catalog
from pipelines.lll import catalog_ast as lll_ast
from pipelines.lll._contract import FINDING_FACTORY_NOT_REGISTERED, LllRefusal
from pipelines.sir import catalog_literals as sir_literals

# The CER plan imports its plants module by the flat ``cer.`` name, as its CLI does.
PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"


def _expr(text: str) -> ast.expr:
    return ast.parse(text, mode="eval").body


def _stmt(text: str) -> ast.stmt:
    return ast.parse(text).body[0]


class LllRegistryRefusalTests(unittest.TestCase):
    def _registry_factories(self, document: object) -> set[str]:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config").mkdir()
            registry = Path(tmp) / "config" / "FACTORY-REGISTRY.json"
            registry.write_text(json.dumps(document), encoding="utf-8")
            with mock.patch.object(lll_catalog, "repo_root", return_value=Path(tmp)):
                return lll_catalog._registry_factories()

    def test_malformed_registry_is_refused(self):
        for document in ([], {}, {"factories": {}}):
            with self.subTest(document=document), self.assertRaises(LllRefusal) as ctx:
                self._registry_factories(document)
            self.assertEqual(ctx.exception.code, FINDING_FACTORY_NOT_REGISTERED)
            self.assertEqual(ctx.exception.message, "factory registry is malformed")

    def test_registry_rows_keep_only_string_path_ids(self):
        document = {"factories": [{"path_id": "a"}, {"path_id": 1}, "x"]}
        self.assertEqual(self._registry_factories(document), {"a"})


class LllFnPairArgsTests(unittest.TestCase):
    def test_only_fn_pair_calls_yield_arguments(self):
        cases = {
            "fa, fb = fn_pair('a', 'b', 'c', 'd')": ["a", "b", "c", "d"],
            "fa, fb = x.fn_pair('a', 'b', 'c', 'd')": ["a", "b", "c", "d"],
            "fa, fb = other('a', 'b', 'c', 'd')": None,
            "fa, fb = fn_pair": None,
            "fa, fb = 1": None,
            "fa, fb = fn_pair('a', 'b', 'c')": None,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(lll_ast._fn_pair_args(_stmt(text)), expected)

    def test_tuple_names_require_every_target_to_be_a_name(self):
        self.assertEqual(lll_ast._tuple_names(_stmt("fa, fb = 1")), ("fa", "fb"))
        self.assertIsNone(lll_ast._tuple_names(_stmt("fa, fb.x = 1")))
        self.assertIsNone(lll_ast._tuple_names(_stmt("x = 1")))


class CrpGitExecutableTests(unittest.TestCase):
    def test_missing_executable_is_refused(self):
        with (
            mock.patch.object(wave_catalog.shutil, "which", return_value=None),
            self.assertRaises(CrpRefusal) as ctx,
        ):
            wave_catalog._git_executable()
        self.assertEqual(ctx.exception.code, FINDING_AST_NOT_A_PLANT)
        self.assertEqual(ctx.exception.message, "git executable not found on PATH")

    def test_found_executable_is_returned(self):
        with mock.patch.object(wave_catalog.shutil, "which", return_value="/usr/bin/x"):
            self.assertEqual(wave_catalog._git_executable(), "/usr/bin/x")


class CerPlanCliTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(sys, "path", [str(PIPELINES), *sys.path])
        patcher.start()
        self.addCleanup(patcher.stop)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cer_cli.run(argv)
        return code, out.getvalue()

    def test_text_summary_reads_the_plan_counts(self):
        counts = load_mill_usage_burst_plan(None).counts()
        code, text = self._run(["plan"])
        self.assertEqual(code, 0)
        self.assertIn(
            f"{counts['mills']} mills, {counts['rounds']} rounds, {counts['episodes']} episodes",
            text,
        )

    def test_json_payload_carries_the_same_counts(self):
        counts = load_mill_usage_burst_plan(None).counts()
        code, text = self._run(["plan", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)["counts"], counts)


class LhcIdentityTests(unittest.TestCase):
    def test_p_identity_needs_a_call_with_slug_and_plant(self):
        cases = {
            "P(slug='s', plant='p')": {"slug": "s", "plant": "p", "ok": None, "key": None},
            "P('ok', slug='s', plant='p')": {"slug": "s", "plant": "p", "ok": "ok", "key": None},
            "P(slug='s')": None,
            "P(plant='p')": None,
            "P(**k)": None,
            "name": None,
            "1": None,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(lhc_plants._p_identity(_expr(text)), expected)

    def test_set_and_container_literals_keep_their_unset_contract(self):
        unset = lhc_literals.UNSET
        self.assertEqual(lhc_literals.literal_value(_expr("{1, 2}")), {1, 2})
        self.assertEqual(lhc_literals.literal_value(_expr("(1, 'a')")), (1, "a"))
        self.assertEqual(lhc_literals.literal_value(_expr("[1, -2]")), [1, -2])
        for text in ("{1, x}", "(x,)", "[x]"):
            with self.subTest(text=text):
                self.assertIs(lhc_literals.literal_value(_expr(text)), unset)
        self.assertIs(lhc_literals.literal_value(None), unset)


class LiteralEvaluatorDepthTests(unittest.TestCase):
    """Main's outcomes at the parser's container limit and for a 600-deep negation."""

    EVALUATORS = (("lhc", lhc_literals), ("sir", sir_literals))

    def test_deepest_parseable_containers_evaluate(self):
        depth = 150
        for name, module in self.EVALUATORS:
            for opener, closer, kind in (("(", ",)", tuple), ("[", "]", list)):
                text = opener * depth + "1" + closer * depth
                with self.subTest(evaluator=name, kind=kind.__name__):
                    value = module.literal_value(_expr(text), {})
                    for _level in range(depth):
                        self.assertIsInstance(value, kind)
                        value = value[0]
                    self.assertEqual(value, 1)

    def test_six_hundred_deep_negation_keeps_mains_outcome(self):
        # Main spends two frames per unary level here too, so the chain exhausts the limit.
        node = _expr("-" * 600 + "1")
        for name, module in self.EVALUATORS:
            with self.subTest(evaluator=name), self.assertRaises(RecursionError):
                module.literal_value(node, {})


if __name__ == "__main__":
    unittest.main()
