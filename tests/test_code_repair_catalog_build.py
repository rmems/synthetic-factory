#!/usr/bin/env python3
"""The catalog builder: the fixture rebuilds byte for byte; selection, extraction, inputs."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import FIXTURE_CATALOG, catalog, executor, oc, program, refusal, vocabulary as cv  # noqa: E402
from code_repair import catalog_build as cb, catalog_inputs as ci, lineage  # noqa: E402

RUNNER = executor.Executor(timeout_s=5.0)


def fixture_build():
    sources = {r["path"]: r["text"] for _n, r in oc.read_jsonl(FIXTURE_CATALOG / "upstream.jsonl")}
    references = json.loads((FIXTURE_CATALOG / "references.json").read_text(encoding="utf-8"))
    meta = json.loads((FIXTURE_CATALOG / catalog.CATALOG_FILENAME).read_text(encoding="utf-8"))
    upstream = cb.Upstream(
        meta["upstream"]["repository"], meta["upstream"]["commit"], meta["upstream"]["license"],
        (FIXTURE_CATALOG / catalog.LICENSE_FILENAME).read_text(encoding="utf-8"),
    )
    policy = lineage.SplitPolicy.from_json(meta["split_policy"])
    targets = [tuple(key.split("::")) for key in references]
    return cb.Build(upstream, sources, references, policy), targets


class FixtureRebuild(unittest.TestCase):
    def test_the_committed_fixture_is_the_builder_s_output_byte_for_byte(self):
        """Real subprocess evidence: wants are observed by executing every original."""

        build, targets = fixture_build()
        rows = cb.build_rows(build, targets, RUNNER)
        out = Path(tempfile.mkdtemp(prefix="code-repair-build-")) / "catalog"
        self.addCleanup(shutil.rmtree, out.parent, True)
        cb.write_catalog(out, "code-repair-fixture-v1", build, rows)
        for name in (catalog.PROGRAMS_FILENAME, catalog.CATALOG_FILENAME, catalog.LICENSE_FILENAME):
            with self.subTest(file=name):
                self.assertEqual((out / name).read_bytes(), (FIXTURE_CATALOG / name).read_bytes())
        self.assertEqual(build.notes, [])
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            cb.write_catalog(out, "code-repair-fixture-v1", build, rows)

    def test_a_reference_that_disagrees_with_the_original_falls_back_to_original_self(self):
        build, _targets = fixture_build()
        wrong = dict(build.references)
        wrong["maths/abs.py::abs_val"] = {
            "kind": cv.REFERENCE_REVIEWED, "function": "reference",
            "source": "def reference(num):\n    return -abs(num)\n",
        }
        rebuilt = cb.Build(build.upstream, build.sources, wrong, build.policy)
        (row,) = cb.build_rows(rebuilt, [("maths/abs.py", "abs_val")], RUNNER)
        self.assertEqual(row["hidden"]["reference"]["kind"], cv.REFERENCE_SELF)
        self.assertEqual([n["code"] for n in rebuilt.notes], [cv.CHECK_REFERENCE_DISAGREES])
        self.assertEqual(row["program_id"], program("abs_val").program_id)


class DroppedTargets(unittest.TestCase):
    """Real subprocess evidence: an original the builder cannot verify never becomes a row."""

    SPIN = (
        "def spin(n: int) -> int:\n    '''\n    >>> spin(3)\n    3\n    >>> spin(4)\n    4\n"
        "    '''\n    while n not in (3, 4):\n        n = n\n    return n\n"
    )
    WRONG = (
        "def wrong(n: int) -> int:\n    '''\n    >>> wrong(1)\n    2\n    >>> wrong(2)\n    3\n"
        "    '''\n    return n\n"
    )

    def _rows(self, path, text, function, runner):
        build, _targets = fixture_build()
        rebuilt = cb.Build(
            build.upstream, {**build.sources, path: text}, build.references, build.policy
        )
        rows = cb.build_rows(rebuilt, [(path, function), ("maths/abs.py", "abs_val")], runner)
        dropped = cb.program_id_for(build.upstream, path, function)
        return rows, rebuilt.notes, dropped

    def test_an_original_that_loops_on_a_neighbour_input_is_dropped_with_a_timeout_note(self):
        rows, notes, dropped = self._rows(
            "maths/spin.py", self.SPIN, "spin", executor.Executor(timeout_s=1.0)
        )
        self.assertEqual([r["upstream"]["function"] for r in rows], ["abs_val"])
        self.assertEqual(notes, [{"code": cv.REASON_ORIGINAL_TIMEOUT, "program_id": dropped}])
        self.assertIsNotNone(rows[0]["split"])  # structure is assigned over the kept rows

    def test_an_original_that_fails_its_own_doctests_is_dropped_with_a_public_failure_note(self):
        rows, notes, dropped = self._rows("maths/wrong.py", self.WRONG, "wrong", RUNNER)
        self.assertEqual([r["upstream"]["function"] for r in rows], ["abs_val"])
        self.assertEqual(notes, [{"code": cv.REASON_ORIGINAL_FAILS_PUBLIC, "program_id": dropped}])


class SelectionAndExtraction(unittest.TestCase):
    def setUp(self):
        self.build, _targets = fixture_build()

    def test_selection_keeps_self_contained_functions_with_doctests(self):
        chosen = {path: cb.select_targets(text) for path, text in self.build.sources.items()}
        self.assertEqual(chosen["maths/sum_of_digits.py"], ["sum_of_digits", "sum_of_digits_compact"])
        self.assertNotIn("sum_of_digits_recursion", chosen["maths/sum_of_digits.py"])  # calls a sibling
        self.assertIn("rec_linear_search", chosen["searches/linear_search.py"])
        self.assertIn("get_1s_count", chosen["bit_manipulation/count_1s_brian_kernighan_method.py"])
        self.assertEqual(cb.select_targets("def f():\n    return 1\n"), [])
        self.assertEqual(cb.select_targets("import os\n\n\ndef f(x):\n    '''\n    >>> f(1)\n    1\n    >>> f(2)\n    2\n    '''\n    print(x)\n    return x\n"), [])

    def test_extraction_keeps_the_function_and_only_the_imports_it_uses(self):
        text = "import math\nimport os\n\n\ndef f(x):\n    '''\n    >>> f(4)\n    2.0\n    '''\n    return math.sqrt(x)\n"
        module, span = cb.extract_module(text, "f")
        self.assertTrue(module.startswith("import math\n\n\ndef f(x):"))
        self.assertNotIn("import os", module)
        self.assertTrue(module.endswith("\n"))
        self.assertEqual(span, (5, 10))
        self.assertIsNone(cb.extract_module(text, "g"))
        self.assertEqual(cb.extract_module(self.build.sources["maths/factorial.py"], "factorial")[0], program("factorial").text)

    def test_program_ids_are_opaque_and_never_appear_in_the_text(self):
        program_id = cb.program_id_for(self.build.upstream, "maths/abs.py", "abs_val")
        self.assertEqual(program_id, program("abs_val").program_id)
        self.assertRegex(program_id, r"^tap-[0-9a-f]{16}$")
        self.assertNotIn(program_id, program("abs_val").text)


class HiddenInputs(unittest.TestCase):
    def test_literal_arguments_come_from_single_call_examples_only(self):
        prog = program("factorial")
        args = [ci.literal_args(e, "factorial") for e in prog.examples]
        self.assertIn((6,), args)
        self.assertIsNone(args[0])  # ``import math`` is not a call
        self.assertIsNone(args[1])  # ``all(...)`` is not a call of the target
        self.assertIsNone(ci.literal_args(catalog.Example("x", "factorial(n=3)\n", "6\n", None), "factorial"))

    def test_neighbourhoods_are_seeded_bounded_and_typed(self):
        stream = oc.DrawStream(5)
        ints = ci.neighbours(7, stream)
        self.assertEqual(ints[:6], [6, 8, 0, 1, 2, -1])
        self.assertEqual(len(ints), 10)
        self.assertEqual(ci.neighbours(7, oc.DrawStream(5)), ints)
        self.assertEqual(ci.neighbours(True, stream), [False])
        self.assertEqual(ci.neighbours("ab", stream), ["", "a", "ba", "abab", "AB"])
        self.assertEqual(ci.neighbours([3, 1], oc.DrawStream(1))[:5], [[], [3], [1, 3], [1, 3], [3, 1, 3]])
        self.assertEqual(ci.neighbours(None, stream), [])
        cases = ci.candidate_args(program("get_1s_count").examples, "get_1s_count", oc.DrawStream(9))
        self.assertEqual(len(cases), len({repr(c) for c in cases}))
        self.assertEqual(cases[0], (25,))


if __name__ == "__main__":
    unittest.main()
