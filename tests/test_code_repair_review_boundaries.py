"""Regression boundaries from PR 202: execute real builder and replay paths."""

import copy
import dataclasses
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from code_repair_test_support import catalog, executor, fixture, mutate, vocabulary as cv
from test_code_repair_catalog_build import fixture_build
from test_code_repair_replay import positives, restamp
from code_repair import catalog_build as cb, catalog_inputs as ci, catalog_check, lineage, replay


DOC = "    '''\n    >>> f(1)\n    1\n    >>> f(2)\n    2\n    '''\n"
RUNNER = executor.Executor(timeout_s=5)


class SelectionBoundaries(unittest.TestCase):
    def test_import_aliases_and_dynamic_host_access_are_rejected(self):
        for prelude, body in (
            ("from os import system as harmless\n", "harmless('true')"),
            ("import os\n", "getattr(os, 'system')('true')"),
            ("import os\n", "g = os.system; g('true')"),
            ("from .math import floor\n", "floor(x)"),
        ):
            with self.subTest(prelude=prelude, body=body):
                self.assertEqual(cb.select_targets(prelude + "def f(x):\n" + DOC
                                                   + "    " + body + "\n    return x\n"), [])

    def test_executable_doctest_host_access_is_rejected(self):
        for command in ("open('/tmp/unused', 'w')", "import os; os.system('true')"):
            text = "def f(x):\n" + DOC.replace("f(1)", command) + "    return x\n"
            self.assertEqual(cb.select_targets(text), [])

    def test_duplicate_definitions_cannot_select_a_different_extracted_function(self):
        text = "def f(x):\n    return open(x)\n\ndef f(x):\n" + DOC + "    return x\n"
        self.assertEqual(cb.select_targets(text), [])
        self.assertIsNone(cb.extract_module(text, "f"))

    def test_future_annotation_semantics_survive_extraction(self):
        text = "from __future__ import annotations\ndef f(x: Missing):\n" + DOC + "    return x\n"
        module, _ = cb.extract_module(text, "f")
        self.assertTrue(module.startswith("from __future__ import annotations\n"))

    def test_empty_hidden_inputs_cannot_certify_a_reference(self):
        build, _ = fixture_build()
        text = "def f(x):\n" + DOC.replace("f(1)", "f(x=1)").replace("f(2)", "f(x=2)") + "    return x\n"
        build = cb.Build(build.upstream, {"maths/a.py": text}, {
            "maths/a.py::f": {"kind": cv.REFERENCE_REVIEWED, "function": "ref",
                               "source": "def ref(x):\n    return x\n"}})
        row, = cb.build_rows(build, [("maths/a.py", "f")], RUNNER)
        self.assertEqual(row["hidden"]["reference"]["kind"], cv.REFERENCE_SELF)


class MutationBoundaries(unittest.TestCase):
    def test_nested_definition_metadata_never_becomes_a_site(self):
        text = ("def f(x):\n    def inner(y=1 + 2):\n        return y + x\n"
                "    class C(object if 1 < 2 else object):\n        pass\n    return inner()\n")
        sites = mutate.sites(text, "f")
        self.assertTrue(sites)
        self.assertTrue(all(site.lineno == 3 for site in sites))

    def test_negative_zero_inverse_restores_exact_bytes(self):
        text = "def f():\n    return -0\n"
        sites = mutate.sites(text, "f")
        self.assertTrue(sites)
        for site in sites:
            self.assertEqual(mutate.repair(mutate.apply(text, site), site), text)

    def test_return_site_coordinates_identify_the_edited_span(self):
        text = "def f(x):\n    return (\n        x\n    )\n"
        for site in mutate.sites(text, "f", "numeric"):
            self.assertEqual((site.lineno, site.col_offset), (3, 8))
            self.assertEqual((site.node_lineno, site.node_col_offset), (2, 4))


class LiteralAndObservationBoundaries(unittest.TestCase):
    def test_catalog_rows_rebuild_identically_across_parent_hash_seeds(self):
        source = ("def f(x):\n    '''\n    >>> f({'aa', 'bb', 'cc'})\n    3\n"
                  "    >>> f({'aa', 'bb'})\n    2\n    '''\n    return len(x)\n")
        script = (
            "import sys; sys.path.insert(0, 'tests'); "
            "from test_code_repair_catalog_build import fixture_build, cb, RUNNER; "
            "from code_repair_test_support import oc; "
            "base, _ = fixture_build(); "
            f"build = cb.Build(base.upstream, {{'maths/sets.py': {source!r}}}, {{}}); "
            "print(oc.canonical_json(cb.build_rows(build, [('maths/sets.py', 'f')], RUNNER)))"
        )
        outputs = [subprocess.check_output(
            [sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONHASHSEED": seed}, text=True,
        ) for seed in ("1", "2", "3")]
        self.assertEqual(len(set(outputs)), 1)

    def test_discarded_probes_cannot_shift_stateful_pinned_wants(self):
        text = ("def f(x):\n" + DOC
                + "    f.n = getattr(f, 'n', 0) + 1\n"
                "    if x < 0: raise ValueError()\n    return f.n\n")
        cases = ci.observed_cases(RUNNER, ci.Subject(text, "f", "shift", catalog.examples_of(text, "f")))
        report = RUNNER.run(executor.Job("check-observed", text, "f", tuple(cases), True))
        self.assertTrue(all(row["status"] == cv.ROW_SUCCESS for row in report.hidden))

    def test_nested_unordered_literals_are_not_hidden_arguments(self):
        for literal in ("{'aa', 'bb'}", "[{'aa', 'bb'}]", "{'x': {'aa', 'bb'}}"):
            example = catalog.Example("e1", f"f({literal})\n", "1\n", None)
            self.assertIsNone(ci.literal_args(example, "f"))

    def test_observation_matches_public_then_isolated_hidden_execution(self):
        text = ("def f(x):\n" + DOC
                + "    f.n = getattr(f, 'n', 0) + 1\n    return f.n\n")
        examples = catalog.examples_of(text, "f")
        cases = ci.observed_cases(RUNNER, ci.Subject(text, "f", "state", examples))
        self.assertEqual(cases[0]["want"], "1")
        checked = RUNNER.run(executor.Job("check-isolated", text, "f", tuple(cases), True))
        self.assertEqual(len(checked.public), 2)
        self.assertTrue(all(row["status"] == cv.ROW_SUCCESS for row in checked.hidden))

    def test_observation_discards_truncated_and_unstable_reprs(self):
        for body in ("return 'a' * 9000", "class C: pass\n    return C()"):
            text = "def f(x):\n" + DOC + "    " + body + "\n"
            cases = ci.observed_cases(RUNNER, ci.Subject(text, "f", "unstable", catalog.examples_of(text, "f")))
            self.assertEqual(cases, [])

    def test_observation_never_sends_more_than_the_hidden_case_cap(self):
        text = "def f(x):\n" + DOC + "    return x\n"
        examples = tuple(catalog.Example(str(i), f"f({i})\n", f"{i}\n", None) for i in range(80))
        class BoundedExecutor(executor.Executor):
            def run(engine, job):
                self.assertLessEqual(len(job.cases), cv.MAX_HIDDEN_CASES)
                return super().run(job)
        engine = BoundedExecutor(timeout_s=5)
        cases = ci.observed_cases(engine, ci.Subject(text, "f", "many", examples))
        self.assertEqual(len(cases), cv.MAX_HIDDEN_CASES)


class LineageBoundaries(unittest.TestCase):
    def test_import_alias_renames_preserve_groups_without_erasing_api_identity(self):
        one = "import math as m\ndef f(x):\n    return m.floor(x)\n"
        renamed = "import math as n\ndef g(y):\n    return n.floor(y)\n"
        self.assertEqual(lineage.structure_digest(one), lineage.structure_digest(renamed))
        self.assertNotEqual(lineage.structure_digest(one), lineage.structure_digest(one.replace("math", "cmath")))
        self.assertNotEqual(lineage.structure_digest("from math import gcd"), lineage.structure_digest("from math import lcm"))

    def test_empty_policy_catalog_reports_unpopulated_splits(self):
        empty = dataclasses.replace(fixture(), programs=())
        codes = {f["code"] for f in catalog_check.catalog_check(empty, RUNNER)}
        self.assertIn(cv.CHECK_SPLIT_EMPTY, codes)


class ReplayBoundaries(unittest.TestCase):
    def test_positive_missing_id_is_a_failed_entry(self):
        record = copy.deepcopy(positives()[0])
        del record["id"]
        self.assertEqual(replay.replay_record(record, fixture(), RUNNER)["code"], cv.REPLAY_HASH_MISMATCH)

    def test_forged_intervention_is_refused(self):
        for field, value in (("operator", "off_by_one"), ("variant", "invented")):
            record = copy.deepcopy(positives()[0])
            record["intervention"][field] = value
            self.assertNotEqual(replay.replay_record(restamp(record), fixture(), RUNNER)["code"], cv.REPLAY_PASSED)

    def test_forged_lineage_is_refused(self):
        record = copy.deepcopy(positives()[0])
        record["provenance"]["split_lineage"]["group_id"] = "g-" + "a" * 32
        self.assertEqual(replay.replay_record(restamp(record), fixture(), RUNNER)["code"], cv.REPLAY_CATALOG_DRIFT)

    def test_forged_environment_is_refused(self):
        for field, value in (("implementation", "Other"), ("platform", "Other"), ("limits_applied", False)):
            record = copy.deepcopy(positives()[0])
            record["oracle"]["fingerprint"][field] = value
            self.assertEqual(replay.replay_record(restamp(record), fixture(), RUNNER)["code"], cv.REPLAY_ENVIRONMENT_DRIFT)

    def test_forged_public_evidence_is_refused(self):
        record = copy.deepcopy(positives()[0])
        record["scenario"]["public_tests"]["examples"][0]["want"] = "forged\n"
        self.assertNotEqual(replay.replay_record(restamp(record), fixture(), RUNNER)["code"], cv.REPLAY_PASSED)

    def test_forged_failure_text_is_refused_even_with_valid_stored_rows(self):
        record = copy.deepcopy(positives()[0])
        evidence = record["result"]["public_failure_evidence"][0]
        evidence["got"] = "forged output"
        evidence["truncated"] = True
        self.assertNotEqual(replay.replay_record(restamp(record), fixture(), RUNNER)["code"], cv.REPLAY_PASSED)


if __name__ == "__main__":
    unittest.main()
