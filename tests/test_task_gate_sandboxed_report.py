"""The sandboxed harness's parts, in process: the plan, the sealed records, the judge, the child.

``test_task_gate_sandboxed.py`` drives the whole harness through bwrap and Landlock where they
work. These tests need neither: they run the child's own functions against a temporary
program in this process and open what they wrote with the parent's judge, so every verdict
path is pinned on any machine.
"""

import doctest
import hmac
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import cv, harness, refused
from task_gate import _sandboxed_record as record
from task_gate import sandboxed, sandboxed_judge, sandboxed_plan
from test_task_gate_sandboxed import ATTESTED, FakeIsolation

KEY = bytes(range(32))
CHILD_PATH = Path(sandboxed.__file__).with_name("_sandboxed_child.py")
PROGRAM = (
    "import math\n\n\ndef f(x):\n    '''Doubles x.\n\n    >>> f(2)\n    4\n"
    "    >>> f(-1)\n    -2\n    '''\n    return x * 2\n"
)


def load_child():
    spec = importlib.util.spec_from_file_location("sandboxed_child_under_test", CHILD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


child = load_child()


def sealed(*bodies, key=KEY):
    return b"".join(record.seal(key, seq, body) for seq, body in enumerate(bodies))


def compiled_function(text):
    """``f`` from ``text`` loaded as a module from a temporary file, as the harness child does."""

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "program_under_test.py")
        path.write_text(text, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("program_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.f


def examples_of(docstring):
    return tuple(doctest.DocTestParser().get_examples(docstring))


def outputs(*texts):
    return [record.observation(record.BRANCH_OUTPUT, text.encode()) for text in texts]


class Records(unittest.TestCase):
    def test_a_sealed_record_opens_only_with_its_key_and_position(self):
        line = record.seal(KEY, 3, {"kind": "end", "count": 0})
        self.assertEqual(record.opened(KEY, line.rstrip(b"\n"), 3), {"kind": "end", "count": 0})
        self.assertIsNone(record.opened(bytes(32), line.rstrip(b"\n"), 3))
        self.assertIsNone(record.opened(KEY, line.rstrip(b"\n"), 2))

    def test_any_change_to_a_sealed_line_is_refused(self):
        line = record.seal(KEY, 0, record.observation("out", b"4\n")).rstrip(b"\n")
        self.assertIn(b"NAo=", line)  # base64 of "4\n"
        self.assertIsNone(record.opened(KEY, line.replace(b"NAo=", b"NQo="), 0))

    def test_hostile_lines_are_none_and_never_raise(self):
        def framed(payload, mac=None):
            mac = mac if mac is not None else hmac.new(KEY, payload.encode(), "sha256").hexdigest()
            return json.dumps({"payload": payload, "mac": mac}).encode()

        cases = {
            "not ascii": "caf\u00e9".encode(), "not json": b"{", "list": b"[]",
            "extra key": json.dumps({"payload": "", "mac": "", "x": 1}).encode(),
            "numeric fields": json.dumps({"payload": 1, "mac": 2}).encode(),
            "non-ascii payload": json.dumps({"payload": "\u00e9", "mac": "00"}, ensure_ascii=False).encode("utf-8"),
            "escaped non-ascii payload": json.dumps({"payload": "\u00e9", "mac": "00"}).encode(),
            "duplicate keys": b'{"payload": "", "payload": "", "mac": ""}',
            "nan": b'{"payload": NaN, "mac": ""}',
            "deep": b"[" * 100000 + b"]" * 100000,
            "sealed list": framed("[]"),
            "wrong protocol": framed(json.dumps({"protocol": "x", "seq": 0, "body": {}})),
            "boolean seq": framed(json.dumps({"protocol": record.PROTOCOL, "seq": False, "body": {}})),
            "unparsable payload": framed("{"),
        }
        for name, line in cases.items():
            with self.subTest(name):
                self.assertIsNone(record.opened(KEY, line, 0))

    def test_bodies_carry_output_as_base64_and_bound_the_detail(self):
        body = record.observation("out", "é\n".encode())
        self.assertEqual((body["data"], body["cut"]), ("w6kK", False))
        self.assertTrue(record.observation("out", b"x", cut=True)["cut"])
        self.assertEqual(len(record.load_error("E" * 999)["detail"]), record.DETAIL_LIMIT)

    def test_the_report_limit_covers_the_worst_honest_report(self):
        """The whole output budget over the most records, then the costliest load_error."""

        count = record.MAX_EXAMPLES
        share, extra = divmod(record.OUTPUT_BUDGET, count)
        chunks = [b"\xff" * (share + (index < extra)) for index in range(count)]
        bodies = [record.observation("exc", chunk) for chunk in chunks]
        bodies.append(record.load_error("\U0001f600" * 999))
        report = b"".join(record.seal(KEY, seq, body) for seq, body in enumerate(bodies))
        self.assertLessEqual(len(report), record.report_limit(count))
        self.assertEqual(record.REPORT_LIMIT, record.report_limit(record.MAX_EXAMPLES))


class Judge(unittest.TestCase):
    def judged(self, docstring, *bodies, report=None):
        examples = examples_of(docstring)
        return sandboxed_judge.judged(examples, sealed(*bodies) if report is None else report, KEY)

    def test_outputs_are_compared_with_the_kept_expectations(self):
        doc = ">>> f(2)\n4\n>>> f(3)\n6\n"
        self.assertEqual(self.judged(doc, *outputs("4\n", "6\n"), record.end(2)),
                         harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0))
        self.assertEqual(self.judged(doc, *outputs("4\n", "7\n"), record.end(2)),
                         harness.HarnessResult(cv.OUTCOME_FAILED, 2, 1))

    def test_example_options_apply_as_doctest_applies_them(self):
        doc = (">>> g()  # doctest: +ELLIPSIS\n[1, ..., 9]\n"
               ">>> g()  # doctest: +NORMALIZE_WHITESPACE\n[1,   2]\n"
               ">>> g()  # doctest: -ELLIPSIS\n...\n")
        result = self.judged(doc, *outputs("[1, 5, 9]\n", "[1, 2]\n", "x\n"), record.end(3))
        self.assertEqual((result.attempted, result.failed), (3, 1))

    def test_exceptions_are_judged_like_doctest_exceptions(self):
        doc = (">>> boom()\nTraceback (most recent call last):\nValueError: bad\n"
               ">>> boom()  # doctest: +IGNORE_EXCEPTION_DETAIL\n"
               "Traceback (most recent call last):\npkg.ValueError: other\n"
               ">>> boom()\nTraceback (most recent call last):\nValueError: other\n"
               ">>> fine()\n1\n")
        exc = record.observation(record.BRANCH_EXCEPTION, b"ValueError: bad\n")
        result = self.judged(doc, exc, exc, exc, exc, record.end(4))
        self.assertEqual((result.attempted, result.failed), (4, 2))

    def test_long_output_is_judged_in_full(self):
        """The Blocks repro on #513: 5000 characters of correct output pass."""

        long = "x" * 5000
        doc = f">>> f()\n{long}\n"
        self.assertEqual(self.judged(doc, *outputs(long + "\n"), record.end(1)),
                         harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))

    def test_output_past_the_budget_is_a_crash_never_a_failure(self):
        doc = ">>> f()\n1\n>>> f()\n1\n"
        cut = record.observation(record.BRANCH_OUTPUT, b"\xe2\x82", cut=True)  # a split character
        result = self.judged(doc, *outputs("1\n"), cut, record.end(2))
        self.assertEqual(result, harness.HarnessResult(cv.OUTCOME_CRASHED, detail="output_truncated"))

    def test_a_load_error_ends_the_run_at_any_point(self):
        doc = ">>> f()\n1\n>>> f()\n1\n"
        for prefix in ([], outputs("1\n")):
            with self.subTest(prefix=len(prefix)):
                result = self.judged(doc, *prefix, record.load_error("KeyboardInterrupt"))
                self.assertEqual(result, harness.HarnessResult(cv.OUTCOME_LOAD_ERROR, detail="KeyboardInterrupt"))

    def test_anything_but_records_then_one_terminal_is_a_crash(self):
        doc = ">>> f()\n1\n"
        good = sealed(*outputs("1\n"), record.end(1))
        cases = {
            "report_missing": b"",
            "report_seal": good.replace(b"1", b"2", 1),
            "unterminated": good.rstrip(b"\n"),
            "out of order": sealed(record.end(1)) + sealed(*outputs("1\n")),
            "no terminal": sealed(*outputs("1\n", "1\n")),
            "short": sealed(record.end(0)),
            "too many": sealed(*outputs("1\n", "1\n"), record.end(2)),
            "miscounted": sealed(*outputs("1\n"), record.end(2)),
            "boolean count": sealed(*outputs("1\n"), {"kind": "end", "count": True}),
            "bad branch": sealed({**outputs("1\n")[0], "branch": "x"}, record.end(1)),
            "bad data": sealed({**outputs("1\n")[0], "data": 1}, record.end(1)),
            "not base64": sealed({**outputs("1\n")[0], "data": "!!"}, record.end(1)),
            "not ascii": sealed({**outputs("1\n")[0], "data": "é"}, record.end(1)),
            "not utf-8": sealed({**outputs("1\n")[0], "data": "/w=="}, record.end(1)),
            "bad cut": sealed({**outputs("1\n")[0], "cut": "no"}, record.end(1)),
            "extra field": sealed({**outputs("1\n")[0], "x": 1}, record.end(1)),
            "not a dict": sealed([], record.end(1)),
            "detail not text": sealed({"kind": "load_error", "detail": 3}),
            "foreign key": sealed(*outputs("1\n"), record.end(1), key=bytes(32)),
        }
        for name, report in cases.items():
            with self.subTest(name):
                self.assertEqual(self.judged(doc, report=report).outcome, cv.OUTCOME_CRASHED)
        self.assertEqual(self.judged(doc, report=b"").detail, "report_missing")
        self.assertEqual(self.judged(doc, report=cases["report_seal"]).detail, "report_seal")

    def test_exception_names_reduce_exactly_as_doctest_reduces_them(self):
        for message in ("ValueError: x\n", "pkg.mod.Error: a: b\n", "Error\n", "a.b:\nmore.c: d",
                        "NoColon", "x.y.z", ""):
            with self.subTest(message=message):
                self.assertEqual(sandboxed_judge._exception_name(message),
                                 doctest._strip_exception_details(message))

    def test_report_limit_grows_with_the_examples(self):
        self.assertEqual(sandboxed_judge.report_limit(0), record.report_limit(0))
        self.assertGreater(sandboxed_judge.report_limit(3), sandboxed_judge.report_limit(2))


class Planning(unittest.TestCase):
    def test_the_child_gets_sources_and_an_emptied_docstring_never_the_expectations(self):
        plan = sandboxed_plan.plan_for(PROGRAM, "f")
        self.assertEqual([e.source for e in plan.examples], ["f(2)\n", "f(-1)\n"])
        self.assertEqual([e.want for e in plan.examples], ["4\n", "-2\n"])
        self.assertEqual(plan.text.count("\n"), PROGRAM.count("\n"))
        self.assertNotIn("Doubles", plan.text)
        self.assertNotIn(">>>", plan.text)
        self.assertEqual(plan.text.split("(\"\"")[0], PROGRAM.split("'''")[0])
        sent = json.loads(plan.child_input(KEY))
        self.assertEqual(sent, {"key": KEY.hex(), "sources": ["f(2)\n", "f(-1)\n"]})

    def test_examples_match_what_doctest_finds_on_the_compiled_function(self):
        """Blocks on #513: on Python 3.13+ ``__doc__`` is dedented, the AST literal is not."""

        shapes = {
            "prompt on the first line": 'def f(x):\n    """>>> f(1)\n    1\n    """\n    return x\n',
            "indented body": "def f(x):\n    '''\n    >>> f(1)\n    1\n    '''\n    return x\n",
            "tabs and blank lines": "def f(x):\n\t'''Doc.\n\n\t>>> f(2)\n\t2\n\n\t>>> f(3)\n\t3\n\t'''\n\treturn x\n",
            "raw with an expected exception": (
                "def f(x):\n    r'''>>> f(None)  # doctest: +IGNORE_EXCEPTION_DETAIL\n"
                "    Traceback (most recent call last):\n    TypeError: x\n    '''\n    return x + 1\n"
            ),
        }
        for name, text in shapes.items():
            with self.subTest(name):
                (test,) = doctest.DocTestFinder(recurse=False).find(compiled_function(text), "f")
                found = [(e.source, e.want, e.exc_msg, e.options) for e in test.examples]
                planned = [(e.source, e.want, e.exc_msg, e.options)
                           for e in sandboxed_plan.plan_for(text, "f").examples]
                self.assertEqual(planned, found)

    def test_skipped_examples_are_neither_sent_nor_counted(self):
        text = "def f():\n    '''\n    >>> f()  # doctest: +SKIP\n    9\n    >>> f()\n    1\n    '''\n    return 1\n"
        self.assertEqual(len(sandboxed_plan.plan_for(text, "f").examples), 1)

    def test_an_async_target_is_planned_like_any_other(self):
        text = "async def f():\n    '''\n    >>> 2\n    2\n    >>> 3\n    3\n    '''\n"
        self.assertEqual(len(sandboxed_plan.plan_for(text, "f").examples), 2)

    def test_a_decorated_or_rebound_target_is_refused_before_anything_runs(self):
        """CodeRabbit on #513: the examples read from the ``def`` may not be the runtime object's."""

        body = "def f():\n    '''\n    >>> 1 + 1\n    2\n    '''\n"
        refused = {
            "decorated": "import functools\n@functools.cache\n" + body,
            "assigned after": body + "f = lambda: 1\n",
            "assigned before": "f = 1\n" + body,
            "redefined": body + body,
            "imported over": body + "from os import path as f\n",
            "star import": body + "from os.path import *\n",
            "augmented": body + "f += 1\n",
            "loop target": body + "for f in range(2):\n    pass\n",
            "declared global": body + "def g():\n    global f\n    f = 2\n",
            "class": body + "class f:\n    pass\n",
        }
        for name, text in refused.items():
            with self.subTest(name):
                plan = sandboxed_plan.plan_for(text, "f")
                self.assertEqual((plan.outcome, plan.detail), (cv.OUTCOME_CRASHED, "target_binding"))
        kept = {
            "a local of another function": body + "def g():\n    f = 2\n    return f\n",
            "a comprehension variable": body + "SQUARES = [f * f for f in range(3)]\n",
            "a lambda parameter": body + "G = lambda f: f\n",
            "a read of the name": body + "ALIAS = f\n",
        }
        for name, text in kept.items():
            with self.subTest(name):
                self.assertEqual(len(sandboxed_plan.plan_for(text, "f").examples), 1)

    def test_offsets_are_bytes_and_any_line_ending_is_handled(self):
        for newline in ("\n", "\r\n", "\r"):
            text = ("x = '\u00e9\u00e9'\ndef f():\n    '''\n    >>> f()\n    1\n    '''\n    return 1\n"
                    ).replace("\n", newline)
            with self.subTest(newline=repr(newline)):
                plan = sandboxed_plan.plan_for(text, "f")
                self.assertEqual((plan.outcome, len(plan.examples)), ("", 1))
                self.assertNotIn(">>>", plan.text)

    def test_programs_with_nothing_to_withhold_run_as_they_are(self):
        for text, function in (("def f(:\n", "f"), ("x = 1\n", "f"), ("def f():\n    return 1\n", "f"),
                               ("def f():\n    b'''>>> 1'''\n", "f"), ("\0", "f")):
            with self.subTest(text=text):
                self.assertEqual(sandboxed_plan.plan_for(text, function), sandboxed_plan.Plan(text))

    def test_a_docstring_doctest_cannot_parse_is_a_load_error_before_anything_runs(self):
        text = "def f():\n    '''\n    >>> f()\n  1\n    '''\n"
        plan = sandboxed_plan.plan_for(text, "f")
        self.assertEqual((plan.outcome, plan.detail), (cv.OUTCOME_LOAD_ERROR, "ValueError"))

    def test_too_many_examples_or_a_failed_redaction_is_a_crash(self):
        many = "def f():\n    '''\n" + "    >>> 1\n    1\n" * 3 + "    '''\n"
        with mock.patch.object(sandboxed_plan, "MAX_EXAMPLES", 2):
            self.assertEqual(sandboxed_plan.plan_for(many, "f").detail, "too_many_examples")
        with mock.patch.object(sandboxed_plan, "_withheld", return_value=False):
            self.assertEqual(sandboxed_plan.plan_for(PROGRAM, "f").detail, "redaction")

    def test_a_plan_decided_from_the_text_runs_nothing(self):
        fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation(["/nonexistent/never-run"]))
        text = "def f():\n    '''\n    >>> f()\n  1\n    '''\n"
        self.assertEqual(fake.run(text, "f"), harness.HarnessResult(cv.OUTCOME_LOAD_ERROR, detail="ValueError"))


def attested_script(then):
    return [sys.executable, "-c",
            "import os, sys\nsys.stdout.write(" + repr(ATTESTED.decode()) + ")\nsys.stdout.flush()\n" + then]


class PassFdIsolation(FakeIsolation):
    """Runs its own argv with the real child's last argument (the report descriptor) appended."""

    def confine(self, argv, _workdir, _env):
        return sandboxed.ec.sandbox.Confinement((*self.argv, argv[-1]))


class ParentReport(unittest.TestCase):
    def test_an_attested_run_with_no_records_is_a_crash(self):
        fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation(attested_script("")))
        self.assertEqual(fake.run(PROGRAM, "f"), harness.HarnessResult(cv.OUTCOME_CRASHED, detail="report_missing"))

    def test_an_oversize_report_is_a_crash_without_being_parsed(self):
        flood = "os.write(int(sys.argv[-1]), b'x' * %d)" % (2 * record.REPORT_LIMIT)
        fake = sandboxed.SandboxedHarness(5, isolation=PassFdIsolation(attested_script(flood)))
        self.assertEqual(fake.run(PROGRAM, "f").detail, "report_oversize")

    def test_the_exit_status_is_not_consulted(self):
        fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation(attested_script("os._exit(9)")))
        self.assertEqual(fake.run(PROGRAM, "f").detail, "report_missing")


class ChildInProcess(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workdir = Path(self.tmp.name)
        self.report = tempfile.TemporaryFile()
        self.addCleanup(self.report.close)
        self.inner = child._sibling("_child")
        self.codec = child._sibling("_sandboxed_record")
        self.addCleanup(sys.modules.pop, "task_gate_program", None)

    def channel(self):
        return child._Channel(self.report.fileno(), KEY, self.codec)

    def body(self):
        self.report.seek(0)
        return self.report.read()

    def observe(self, text, function="f"):
        plan = sandboxed_plan.plan_for(text, function)
        workdir = Path(tempfile.mkdtemp(dir=self.workdir))  # a fresh directory: no stale bytecode
        workdir.joinpath("program.py").write_text(plan.text, encoding="utf-8")
        sources = [example.source for example in plan.examples]
        child._observe(self.inner, self.codec, self.channel(), (str(workdir), function, sources))
        return sandboxed_judge.judged(plan.examples, self.body(), KEY)

    def test_passing_failing_and_raising_examples(self):
        self.assertEqual(self.observe(PROGRAM), harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0))
        self.report.truncate(0)
        wrong = PROGRAM.replace("return x * 2", "return x * 3")
        self.assertEqual(self.observe(wrong), harness.HarnessResult(cv.OUTCOME_FAILED, 2, 2))
        self.report.truncate(0)
        raising = ("def f():\n    '''\n    >>> f()\n    Traceback (most recent call last):\n"
                   "    KeyError: 'k'\n    >>> f()\n    1\n    '''\n    raise KeyError('k')\n")
        self.assertEqual(self.observe(raising), harness.HarnessResult(cv.OUTCOME_FAILED, 2, 1))

    def test_output_counts_against_one_budget_per_run(self):
        x5000 = "x" * 5000
        long = f"def f():\n    '''\n    >>> print('x' * 5000)\n    {x5000}\n    '''\n"
        self.assertEqual(self.observe(long), harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))
        self.report.truncate(0)
        with mock.patch.object(self.codec, "OUTPUT_BUDGET", 3):
            result = self.observe(PROGRAM)  # "4\n" fits, "-2\n" does not
        self.assertEqual(result, harness.HarnessResult(cv.OUTCOME_CRASHED, detail="output_truncated"))

    def test_load_failures_are_recorded_as_load_errors(self):
        for text, function, detail in (("def f(:\n", "f", "SyntaxError"), (PROGRAM, "g", "AttributeError"),
                                       ("raise ValueError\n" + PROGRAM, "f", "ValueError")):
            with self.subTest(detail=detail):
                self.report.truncate(0)
                self.assertEqual(self.observe(text, function),
                                 harness.HarnessResult(cv.OUTCOME_LOAD_ERROR, detail=detail))

    def test_exit_requests_are_recorded_and_then_propagate(self):
        for raised in (SystemExit, KeyboardInterrupt):
            with self.subTest(raised=raised.__name__):
                self.report.truncate(0)
                with self.assertRaises(raised):
                    self.observe(f"raise {raised.__name__}\n" + PROGRAM)
                result = sandboxed_judge.judged((), self.body(), KEY)
                self.assertEqual(result, harness.HarnessResult(cv.OUTCOME_LOAD_ERROR, detail=raised.__name__))

    def test_the_channel_owns_the_file_layout(self):
        os.write(self.report.fileno(), b"junk written by someone else " * 100)
        channel = self.channel()
        channel.send(record.end(0))
        self.assertEqual(self.body(), sealed(record.end(0)))
        channel.send(record.end(0))
        self.assertEqual(self.body().count(b"\n"), 2)

    def test_the_plan_is_read_once_and_stdin_is_then_empty(self):
        cases = {
            json.dumps({"key": KEY.hex(), "sources": ["1\n"]}).encode(): (KEY, ["1\n"]),
            b"{": None, b"[]": None, b'{"key": "zz", "sources": []}': None,
            json.dumps({"key": KEY.hex(), "sources": "1"}).encode(): None,
            json.dumps({"key": KEY.hex(), "sources": [1]}).encode(): None,
            json.dumps({"sources": []}).encode(): None,
        }
        for data, expected in cases.items():
            with self.subTest(data=data[:30]):
                read_end, write_end = os.pipe()
                os.write(write_end, data)
                os.close(write_end)
                try:
                    self.assertEqual(child._read_plan(read_end), expected)
                    self.assertEqual(os.read(read_end, 8), b"")
                finally:
                    os.close(read_end)

    def test_an_endless_plan_is_cut_at_the_limit(self):
        read_end, write_end = os.pipe()
        os.write(write_end, b"x" * 64)
        try:
            with mock.patch.object(child, "PLAN_LIMIT", 16):
                self.assertEqual(len(child._drained(read_end)), 64)
        finally:
            os.close(read_end)
            os.close(write_end)

    def test_attestations_are_written_and_reported(self):
        stream = io.StringIO()
        limits = mock.Mock(apply_limits=mock.Mock(return_value=False))
        self.assertFalse(child._attest_limits(limits, 3, stream))
        self.assertEqual(stream.getvalue(), child.LIMITS_PREFIX + "false\n")
        broken = mock.Mock(enforce=mock.Mock(side_effect=RuntimeError("SANDBOX_UNAVAILABLE: landlock")))
        with mock.patch.object(child, "_sibling", return_value=broken):
            self.assertFalse(child._attest_landlock(str(self.workdir), stream))
        with mock.patch.object(child, "_sibling", return_value=mock.Mock()):
            self.assertTrue(child._attest_landlock(str(self.workdir), stream))

    def run_main(self, plan, attested=True):
        real = child._sibling

        def sibling(name):
            module = real(name)
            if name == "_child":
                module.silence_stdout = lambda: None
            return module

        self.workdir.joinpath("program.py").write_text(sandboxed_plan.plan_for(PROGRAM, "f").text)
        argv = ["child", str(self.workdir), "f", "3", str(self.report.fileno())]
        with mock.patch.object(child, "_sibling", side_effect=sibling), \
                mock.patch.object(child, "_read_plan", return_value=plan), \
                mock.patch.object(child, "_attest_limits", return_value=attested), \
                mock.patch.object(child, "_attest_landlock", return_value=True):
            self.assertEqual(child.main(argv), 0)
        return self.body()

    def test_main_observes_only_an_attested_run_with_a_plan(self):
        examples = sandboxed_plan.plan_for(PROGRAM, "f").examples
        body = self.run_main((KEY, [example.source for example in examples]))
        self.assertEqual(sandboxed_judge.judged(examples, body, KEY),
                         harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0))
        self.report.truncate(0)
        self.assertEqual(self.run_main((KEY, ["1\n"]), attested=False), b"")
        self.assertEqual(self.run_main(None), b"")


class Refusal(unittest.TestCase):
    def test_a_sandbox_whose_child_never_attests_still_refuses(self):
        fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation([sys.executable, "-c", "pass"]))
        self.assertEqual(refused(fake.run, PROGRAM, "f"), cv.REFUSE_HARNESS_UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
