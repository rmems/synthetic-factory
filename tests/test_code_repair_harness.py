#!/usr/bin/env python3
"""The sandboxed child and its parent: real subprocess evidence (no fakes here)."""

import doctest
import hashlib
import inspect
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import catalog, executor as ex, program, refusal, vocabulary as cv  # noqa: E402
from code_repair import _harness as harness  # noqa: E402

RUNNER = ex.Executor(timeout_s=5.0)


class OriginalAndMutant(unittest.TestCase):
    def test_the_original_passes_every_public_example_and_hidden_case(self):
        prog = program("get_1s_count")
        report = RUNNER.run(prog.job("original:test"))
        self.assertTrue(report.ok, report.detail)
        self.assertEqual({row["status"] for row in report.public}, {"pass"})
        self.assertEqual({row["status"] for row in report.hidden}, {"pass"})
        self.assertEqual(len(report.public), len(prog.examples))
        self.assertEqual(len(report.hidden), len(prog.cases))
        self.assertTrue(report.environment["limits_applied"])
        self.assertEqual(report.environment["implementation"], "cpython")

    def test_the_mutant_fails_with_the_real_got_text(self):
        prog = program("get_1s_count")
        mutant = prog.text.replace("number < 0", "number <= 0", 1)
        report = RUNNER.run(prog.job("mutant:test", mutant))
        failing = [row for row in report.public if row["status"] != "pass"]
        self.assertEqual([row["id"] for row in failing], ["public:4"])
        self.assertEqual(failing[0]["status"], "error")
        self.assertIn("ValueError: Input must be a non-negative integer", failing[0]["got"])
        self.assertTrue(any(row["status"] != "pass" for row in report.hidden))

    def test_doctest_examples_run_in_order_with_shared_state(self):
        # factorial's docstring imports math in one example and uses it in the next.
        report = RUNNER.run(program("factorial").job("original:test"))
        self.assertTrue(report.ok, report.detail)
        self.assertEqual({row["status"] for row in report.public}, {"pass"})

    def test_two_runs_of_one_job_report_identical_rows(self):
        job = program("rec_linear_search").job("original:test")
        first, second = RUNNER.run(job), RUNNER.run(job)
        self.assertEqual((first.public, first.hidden), (second.public, second.hidden))

    def test_observed_mode_reports_the_repr_without_a_want(self):
        prog = program("abs_val")
        job = ex.Job("observe:test", prog.text, prog.function, ({"args": "(-3,)", "want": None},), False)
        report = RUNNER.run(job)
        self.assertEqual(report.public, ())
        self.assertEqual(report.hidden[0]["status"], cv.ROW_OBSERVED)
        self.assertEqual(report.hidden[0]["got"], "3")


class Agreement(unittest.TestCase):
    """Codex on #196: integers must compare exactly; the float tolerance is for floats."""

    def _hidden(self, module: str, cases):
        report = RUNNER.run(ex.Job("agree:test", module, "f", tuple(cases), False))
        self.assertTrue(report.ok, report.detail)
        return [row["status"] for row in report.hidden]

    def test_an_integer_off_by_one_beyond_float_precision_fails(self):
        module = "def f(n):\n    return n + 1\n"
        cases = [{"args": "(9007199254740992,)", "want": "9007199254740992"}]
        self.assertEqual(self._hidden(module, cases), ["fail"])

    def test_an_integer_want_never_agrees_with_a_float_got(self):
        module = "def f(n):\n    return float(n)\n"
        self.assertEqual(self._hidden(module, [{"args": "(2,)", "want": "2"}]), ["fail"])

    def test_floats_agree_within_the_pinned_tolerance(self):
        module = "def f(x):\n    return x + 1e-15\n"
        self.assertEqual(self._hidden(module, [{"args": "(0.5,)", "want": "0.5"}]), ["pass"])


class Failures(unittest.TestCase):
    def test_a_child_that_streams_discarded_output_is_stopped_by_the_timeout(self):
        """Discarded output stays out of memory while the wall-clock bound stops the loop."""

        module = (
            "import sys\nwhile True:\n    sys.stderr.write('x' * 65536)\n\n\n"
            "def f(n):\n    return n\n"
        )
        quick = ex.Executor(timeout_s=1.0)
        report = quick.run(ex.Job("stream:test", module, "f", (), False))
        # The child's prints are discarded, so the loop runs to the timeout with flat memory
        # (Codex on #196, round 3); nothing of it reaches the parent.
        self.assertEqual(report.status, cv.PHASE_TIMEOUT)
        self.assertEqual(quick.log[-1]["stderr_tail"], "")

    def test_an_infinite_loop_is_a_timeout_not_an_exception(self):
        prog = program("sum_of_digits")
        mutant = prog.text.replace("while n > 0", "while n >= 0", 1)
        quick = ex.Executor(timeout_s=1.0)
        report = quick.run(prog.job("mutant:test", mutant))
        self.assertEqual(report.status, cv.PHASE_TIMEOUT)
        self.assertFalse(report.ok)
        self.assertTrue(quick.log[-1]["timed_out"])

    def test_a_module_that_does_not_load_is_reported_not_raised(self):
        report = RUNNER.run(ex.Job("mutant:test", "def f(:\n", "f"))
        self.assertEqual(report.status, cv.PHASE_OK)
        self.assertFalse(report.load_ok)
        self.assertIn("SyntaxError", report.detail)

    def test_a_missing_function_is_a_load_error(self):
        report = RUNNER.run(ex.Job("mutant:test", "x = 1\n", "f"))
        self.assertFalse(report.ok)
        self.assertIn("AttributeError", report.detail)

    def test_an_exception_inside_a_hidden_case_is_an_error_row_without_the_message(self):
        prog = program("get_1s_count")
        job = ex.Job("hidden:test", prog.text, prog.function, ({"args": "(-4,)", "want": "0"},), False)
        report = RUNNER.run(job)
        self.assertEqual(report.hidden[0]["status"], cv.ROW_ERROR)
        self.assertNotIn("got", report.hidden[0])

    def test_unreadable_foreign_or_incomplete_reports_are_harness_errors(self):
        job = ex.Job("x", "def f():\n    pass\n", "f", ({"args": "()", "want": "None"},), True, 2)
        head = '{"protocol": "code-repair-harness/1", "environment": {"limits_applied": true}, "load": {"status": "ok", "error": null}, '
        full = head + '"public": [{"id": "public:0", "status": "pass"}, {"id": "public:1", "status": "pass"}], "hidden": [{"id": "hidden:0", "status": "pass"}]}'
        self.assertTrue(ex._parse_report(job, 0, full.encode()).ok)
        bad = (
            (1, b"{}"), (0, b"not json"), (0, b'{"protocol": "other/1"}'), (0, b'{"a": 1, "a": 2}'),
            (0, (head + '"public": [], "hidden": []}').encode()),
            (0, (head + '"public": [{"id": "public:0", "status": "pass"}], "hidden": [{"id": "hidden:0", "status": "pass"}]}').encode()),
            (0, (head + '"public": [{"id": "public:0", "status": "pass"}, {"id": "public:9", "status": "pass"}], "hidden": [{"id": "hidden:0", "status": "pass"}]}').encode()),
            (0, (head + '"public": [{"id": "public:0", "status": "pass"}, {"id": "public:1"}], "hidden": [{"id": "hidden:0", "status": "pass"}]}').encode()),
            (0, (head + '"public": "nine", "hidden": []}').encode()),
        )
        for returncode, stdout in bad:
            with self.subTest(stdout=stdout[:60]):
                report = ex._parse_report(job, returncode, stdout)
                self.assertEqual(report.status, cv.PHASE_HARNESS_ERROR)
                self.assertFalse(report.ok)


class RoundThree(unittest.TestCase):
    """Codex on #196, round 3: skipped examples, module registration, digests on passing rows."""

    def test_a_skipped_doctest_example_reports_no_row_and_the_parent_expects_none(self):
        module = (
            "def f(n):\n    '''\n    >>> f(1)\n    1\n    >>> f(2)  # doctest: +SKIP\n    99\n"
            "    >>> f(3)\n    3\n    '''\n    return n\n"
        )
        examples = catalog.examples_of(module, "f")
        self.assertEqual([e.source for e in examples], ["f(1)\n", "f(3)\n"])
        report = RUNNER.run(ex.Job("skip:test", module, "f", (), expected_public=len(examples)))
        self.assertTrue(report.ok, report.detail)
        self.assertEqual([row["status"] for row in report.public], ["pass", "pass"])

    def test_the_loaded_module_is_registered_so_its_own_classes_pickle(self):
        module = (
            "import pickle\n\n\nclass Box:\n    def __init__(self, n):\n        self.n = n\n\n\n"
            "def f(n):\n    '''\n    >>> f(1)\n    1\n    >>> f(2)\n    2\n    '''\n"
            "    return pickle.loads(pickle.dumps(Box(n))).n\n"
        )
        job = ex.Job("pickle:test", module, "f", ({"args": "(5,)", "want": "5"},), True, 2)
        report = RUNNER.run(job)
        self.assertTrue(report.ok, report.detail)
        self.assertEqual([row["status"] for row in report.public + report.hidden], ["pass"] * 3)

    def test_passing_rows_carry_their_output_digest_and_matched_exceptions_keep_one_line(self):
        prog = program("get_1s_count")
        report = RUNNER.run(prog.job("original:test"))
        digestable = ex.rows_of(report.public) + ex.rows_of(report.hidden)
        self.assertTrue(all("got_sha256" in row for row in digestable))
        raising = [row for row in report.public if row.get("got", "").startswith("ValueError")]
        self.assertGreaterEqual(len(raising), 1)
        self.assertTrue(all("\n" not in row["got"] for row in raising))


class Isolation(unittest.TestCase):
    def test_exactly_one_subprocess_call_site_with_a_literal_argv(self):
        source = inspect.getsource(ex)
        self.assertEqual(source.count("subprocess.run("), 1)
        self.assertNotIn("shell=", source)
        self.assertNotIn("preexec_fn", source)
        self.assertEqual(ex.INTERPRETER_FLAGS, ("-P", "-s", "-S", "-B", "-X", "utf8"))
        self.assertEqual(set(ex.CHILD_ENV), {"PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE"})

    def test_the_harness_imports_nothing_from_the_repository(self):
        text = ex.HARNESS_PATH.read_text(encoding="utf-8")
        for needle in ("from .", "code_repair", "oracle_grounded", "import random"):
            self.assertNotIn(needle, text)
        self.assertIsNone(re.search(r"(?<![\w.])(exec|eval)\(", text))
        self.assertEqual(len(RUNNER.harness_sha256), 64)

    def test_the_timeout_domain_is_refused_with_a_code(self):
        for value in (0, -1, True, "2", 61.0):
            with self.subTest(value=repr(value)), refusal(self, cv.FINDING_TIMEOUT_OUT_OF_DOMAIN, "timeout"):
                ex.Executor(timeout_s=value)

    def test_the_digestable_rows_keep_only_id_status_and_a_got_digest(self):
        rows = ({"id": "public:2", "status": "fail", "got": "x"}, {"id": "public:1", "status": "pass"})
        digest = "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881"
        self.assertEqual(
            ex.rows_of(rows),
            [{"id": "public:1", "status": "pass"},
             {"id": "public:2", "status": "fail", "got_sha256": digest}],
        )


class InProcessHarnessBehavior(unittest.TestCase):
    """Pure child behavior, without changing or instrumenting subprocess isolation."""

    def test_rows_clip_display_text_but_digest_the_complete_observation(self):
        got = "x" * (harness.MAX_GOT_CHARS + 1)

        row = harness._row("hidden", 3, "fail", got)

        self.assertEqual(row["id"], "hidden:3")
        self.assertEqual(row["got"], "x" * harness.MAX_GOT_CHARS)
        self.assertEqual(row["got_sha256"], hashlib.sha256(got.encode("utf-8")).hexdigest())
        self.assertIs(row["truncated"], True)
        self.assertEqual(harness._row("public", 0, "pass"), {"id": "public:0", "status": "pass"})

    def test_doctest_capture_bounds_output_and_preserves_line_framing(self):
        capture = harness._Capture()
        self.assertEqual(capture.write("abc"), 3)
        self.assertEqual(capture.getvalue(), "abc\n")
        self.assertEqual(capture.truncate(1), 1)
        self.assertEqual(capture.getvalue(), "a\n")

        full = harness._Capture()
        full.write("x" * harness.MAX_CAPTURE_CHARS)
        with self.assertRaisesRegex(ValueError, "output limit exceeded"):
            full.write("y")

    def test_runner_hooks_record_the_example_identity_and_sanitized_outcome(self):
        examples = [
            doctest.Example("1 + 1\n", "2\n"),
            doctest.Example("raise ValueError('x')\n", "", exc_msg="ValueError: x\n"),
            doctest.Example("int('x')\n", ""),
        ]
        test = doctest.DocTest(examples, {}, "f", "program.py", 1, "")
        rows = []
        runner = harness._Runner(rows)

        self.assertIsNone(runner.report_start(None, test, examples[0]))
        runner.report_success(None, test, examples[0], "2\n")
        runner.report_failure(
            None, test, examples[1],
            "Traceback (most recent call last):\n  hidden path\nValueError: wrong\n",
        )
        try:
            int("x")
        except ValueError:
            runner.report_unexpected_exception(None, test, examples[2], sys.exc_info())

        self.assertEqual([row["id"] for row in rows], ["public:0", "public:1", "public:2"])
        self.assertEqual([row["status"] for row in rows], ["pass", "fail", "error"])
        self.assertEqual(rows[1]["got"], "ValueError: wrong")
        self.assertEqual(rows[2]["got"], "ValueError: invalid literal for int() with base 10: 'x'")
        with self.assertRaisesRegex(ValueError, "does not hold"):
            runner.report_success(None, test, doctest.Example("3\n", "3\n"), "3\n")

    def test_temp_module_loading_and_public_examples_report_real_pass_and_failure_rows(self):
        text = (
            "def f(n):\n"
            "    '''\n"
            "    >>> f(2)\n"
            "    4\n"
            "    >>> f(3)\n"
            "    7\n"
            "    '''\n"
            "    return n * 2\n"
        )
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules):
            directory = Path(root)
            (directory / harness.PROGRAM_FILENAME).write_text(text, encoding="utf-8")
            module = harness._load(directory)
            rows = harness._run_public(module, text, "f")
            self.assertIs(sys.modules["program"], module)

        self.assertEqual([row["status"] for row in rows], ["pass", "fail"])
        self.assertEqual(rows[1]["got"], "6\n")
        with self.assertRaisesRegex(LookupError, "module-level function named missing"):
            harness._function_node(text, "missing")

    def test_numeric_agreement_and_hidden_case_rows_keep_their_distinct_contracts(self):
        spec = {"float_rel_tol": 1e-12, "float_abs_tol": 1e-12}
        self.assertIs(harness._agree("same", "same", spec), True)
        self.assertIs(harness._agree("2", "2.0", spec), False)
        self.assertIs(harness._agree("word", "other", spec), False)
        self.assertIs(harness._agree("inf", "inf.0", spec), False)
        self.assertIs(harness._agree("0.5", "0.5000000000001", spec), True)

        observed = harness._run_case(lambda n: n + 1, 0, {"args": "(2,)", "want": None}, spec)
        matched = harness._run_case(lambda n: n + 1, 1, {"args": "(2,)", "want": "3"}, spec)
        mismatch = harness._run_case(lambda n: n + 1, 2, {"args": "(2,)", "want": "4"}, spec)
        visible_error = harness._run_case(
            lambda: (_ for _ in ()).throw(RuntimeError("visible")),
            3, {"args": "()", "want": None}, spec,
        )
        hidden_error = harness._run_case(
            lambda: (_ for _ in ()).throw(RuntimeError("secret")),
            4, {"args": "()", "want": "0"}, spec,
        )

        self.assertEqual((observed["status"], observed["got"]), ("observed", "3"))
        self.assertEqual((matched["status"], matched["kind"], matched["got"]), ("pass", "ok", "3"))
        self.assertEqual(mismatch, {"id": "hidden:2", "status": "fail", "kind": "value_mismatch"})
        self.assertEqual(visible_error["got"], "RuntimeError: visible")
        self.assertEqual(hidden_error, {"id": "hidden:4", "status": "error", "kind": "exception"})


if __name__ == "__main__":
    unittest.main()
