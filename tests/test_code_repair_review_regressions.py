"""Real execution and catalog-boundary regressions for PR 196 review findings."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import catalog, executor as ex, oc, refusal, vocabulary as cv
from test_code_repair_catalog import copied_fixture, rewrite_programs


class ExecutionEvidence(unittest.TestCase):
    def run_job(self, text, cases=(), public=False, count=0):
        result = ex.Executor(timeout_s=3).run(ex.Job("review", text, "f", cases, public, count))
        self.assertTrue(result.ok, result.detail)
        return result

    def test_clipped_public_observations_keep_distinct_full_digests(self):
        def run(suffix):
            text = (
                "def f():\n    '''\n    >>> f()  # doctest: +ELLIPSIS\n    xxx...\n"
                f"    '''\n    print('x' * 2100 + {suffix!r})\n"
            )
            return self.run_job(text, public=True, count=1).public[0]

        left, right = run("a"), run("b")
        self.assertEqual(left["got"], right["got"])
        self.assertNotEqual(left, right)
        expected = hashlib.sha256(("x" * 2100 + "a\n").encode()).hexdigest()
        self.assertEqual(ex.rows_of((left,))[0]["got_sha256"], expected)

    def test_wrong_exception_reports_do_not_include_temporary_paths(self):
        text = (
            "def f():\n    '''\n    >>> f()\n    Traceback (most recent call last):\n"
            "    ValueError: expected\n    '''\n    raise ValueError('actual')\n"
        )
        first = self.run_job(text, public=True, count=1)
        second = self.run_job(text, public=True, count=1)
        self.assertEqual(first.public, second.public)
        self.assertEqual(first.public[0]["status"], "fail")
        self.assertEqual(first.public[0]["got"], "ValueError: actual")

    def test_repr_failure_is_one_hidden_error_and_later_cases_run(self):
        text = (
            "class Bad:\n    def __repr__(self):\n        raise ValueError('repr failed')\n"
            "def f(n):\n    return Bad() if n else 0\n"
        )
        for want in (None, "0"):
            with self.subTest(want=want):
                result = self.run_job(text, ({"args": "(1,)", "want": want},
                                             {"args": "(0,)", "want": "0"}))
                self.assertEqual([r["status"] for r in result.hidden], ["error", "pass"])

    def test_nonfinite_coercions_cannot_satisfy_tolerance(self):
        result = self.run_job("def f():\n    return float('inf')\n", (
            {"args": "()", "want": "1e999"}, {"args": "()", "want": "inf"}))
        self.assertEqual([r["status"] for r in result.hidden], ["fail", "pass"])

    def test_hidden_state_starts_from_a_fresh_module(self):
        text = (
            "counter = 0\ndef f():\n    '''\n    >>> f()\n    1\n    >>> f()\n    2\n"
            "    '''\n    global counter\n    counter += 1\n    return counter\n"
        )
        result = self.run_job(text, ({"args": "()", "want": "1"},), True, 2)
        self.assertEqual([r["status"] for r in result.public + result.hidden], ["pass"] * 3)

    def test_doctest_print_loop_hits_capture_bound_as_a_case_error(self):
        text = (
            "def f():\n    '''\n    >>> f()\n    0\n    >>> 1 + 1\n    2\n    '''\n"
            "    while True:\n        print('x' * 8192)\n"
        )
        result = self.run_job(text, public=True, count=2)
        self.assertEqual([r["status"] for r in result.public], ["error", "pass"])
        self.assertIn("output limit", result.public[0]["got"])

    def test_direct_descriptor_and_original_stream_output_cannot_corrupt_protocol(self):
        text = (
            "import os, sys\nos.write(1, b'import')\nsys.__stdout__.write('buffered')\n"
            "def f():\n    '''\n    >>> f()\n    1\n    '''\n"
            "    os.write(1, b'out')\n    os.write(2, b'err')\n"
            "    sys.__stderr__.write('original')\n    return 1\n"
        )
        result = self.run_job(text, ({"args": "()", "want": "1"},), True, 1)
        self.assertEqual([r["status"] for r in result.public + result.hidden], ["pass", "pass"])

    def test_executor_runs_its_original_harness_snapshot_after_file_changes(self):
        with tempfile.TemporaryDirectory() as root:
            harness = Path(root) / "harness.py"
            original = ex.HARNESS_PATH.read_bytes()
            harness.write_bytes(original)
            with patch.object(ex, "HARNESS_PATH", harness):
                runner = ex.Executor(timeout_s=3)
                harness.write_text("raise RuntimeError('changed harness')\n")
                result = runner.run(ex.Job("snapshot", "def f():\n    return 1\n", "f",
                                           ({"args": "()", "want": "1"},), False))
            self.assertTrue(result.ok, result.detail)
            self.assertEqual(runner.harness_sha256, hashlib.sha256(original).hexdigest())

    def test_reports_without_applied_limits_are_rejected(self):
        for flag in (None, False, 1):
            report = {"protocol": cv.HARNESS_PROTOCOL, "load": {"status": "ok"},
                      "environment": {"limits_applied": flag}, "public": [], "hidden": []}
            result = ex._parse_report(ex.Job("limits", "", "f", (), False),
                                      0, json.dumps(report).encode())
            self.assertFalse(result.ok)
            self.assertIn(cv.FINDING_SANDBOX_UNAVAILABLE, result.detail)

    def test_unavailable_limits_stop_before_loading_program_code(self):
        from code_repair import _harness

        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            marker = directory / "loaded"
            (directory / "program.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
            )
            with patch.object(_harness, "_apply_limits", return_value=False):
                result = _harness._run(directory, {})
            self.assertEqual(result["load"]["status"], "error")
            self.assertFalse(marker.exists())


class CatalogBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = copied_fixture(self.temp.name)

    def test_hidden_arguments_must_be_literal_argument_sequences(self):
        for value in ("(", "1", "'abc'", "{}", "{1, 2}", "[" * 1000):
            with self.subTest(value=value[:20]):
                rewrite_programs(self.directory, lambda row, value=value: row["hidden"]["cases"][0].update(args=value))
                with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "args"):
                    catalog.load_catalog(self.directory)

    def test_loaded_cases_cannot_be_mutated_away_from_their_pin(self):
        loaded = catalog.load_catalog(self.directory)
        with self.assertRaises(TypeError):
            loaded.programs[0].cases[0]["want"] = "wrong"

    def test_group_members_cannot_disagree_on_split_including_unassigned(self):
        for other in ("held_out", None):
            def edit(row, other=other):
                row["structure"] = {"group_id": "related"}
                row["split"] = "train" if row["upstream"]["function"] == "abs_val" else other
            rewrite_programs(self.directory, edit)
            with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "split"):
                catalog.load_catalog(self.directory)

    def test_nested_catalog_metadata_is_a_coded_refusal(self):
        nested = "[" * 100000 + "0" + "]" * 100000
        for label, raw in (
            ("decoded wrong type", '{"format":[]}'),
            ("decoder nesting limit", '{"format":' + nested + "}"),
        ):
            with self.subTest(path=label):
                (self.directory / catalog.CATALOG_FILENAME).write_text(raw)
                with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID):
                    catalog.load_catalog(self.directory)

    def test_catalog_root_list_is_not_reclassified_as_a_bad_field(self):
        (self.directory / catalog.CATALOG_FILENAME).write_text("[]")
        with refusal(self, cv.FINDING_INPUT_NOT_AN_OBJECT):
            catalog.load_catalog(self.directory)

    def test_missing_target_precedes_missing_example_pin(self):
        def edit(row):
            row["upstream"]["function"] = "missing"
            row["public"].pop("example_count")
        rewrite_programs(self.directory, edit)
        with refusal(self, cv.FINDING_TARGET_FUNCTION_NOT_FOUND):
            catalog.load_catalog(self.directory)

    def test_catalog_rejects_public_suites_that_exceed_report_budget(self):
        def edit(row):
            function = row["upstream"]["function"]
            text = f"def {function}():\n    '''\n" + "    >>> 1\n    1\n" * 1000 + "    '''\n"
            row["module"] = {"text": text, "sha256": catalog.sha256_text(text)}
            examples = catalog.examples_of(text, function)
            row["public"] = {"example_count": len(examples),
                             "examples_sha256": catalog.examples_sha256(examples)}
        rewrite_programs(self.directory, edit)
        with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "public"):
            catalog.load_catalog(self.directory)

    def test_snapshot_jsonl_uses_binary_file_line_semantics(self):
        path = Path(self.temp.name) / "sample.jsonl"
        samples = (b'{"a":1}\r{"b":2}\r', b'\n{"a":1}\r\n\n{"b":2}',
                   '{"text":"\u0085"}\n'.encode(), b'{"a":1}\x1c{"b":2}\n')
        for data in samples:
            path.write_bytes(data)
            self.assertEqual(list(oc.iter_jsonl_bytes(data)), list(oc.iter_jsonl(path)))


if __name__ == "__main__":
    unittest.main()
