"""The gate's child interpreter script, driven in-process with every global it touches patched.

The child normally runs in a subprocess that coverage does not trace. Here its functions run
in the test process, so nothing may leak: ``resource.setrlimit`` is mocked (the test process
must never lower its own limits), the socket attributes and ``sys.modules`` are restored on
exit, and the report stream is a ``StringIO`` instead of a duplicate of stdout.
"""

import contextlib
import io
import json
import os
import resource
import runpy
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import REPO, cv, harness
from task_gate import _child

CHILD_PATH = REPO / "pipelines" / "task_gate" / "_child.py"


def program(body, expect):
    """A one-function module whose only doctest wants ``expect`` from ``f()``."""

    lines = "".join(f"    {line}\n" for line in body.splitlines())
    return f'def f():\n    """\n    >>> f()\n    {expect!r}\n    """\n{lines}'


@contextlib.contextmanager
def isolated_process_state():
    """Patch everything the child mutates: limits, sockets, imported modules, the report fd."""

    socket_names = ("socket", *_child.BLOCKED_SOCKET_FUNCTIONS)
    originals = {name: getattr(socket, name) for name in socket_names if hasattr(socket, name)}
    stream = io.StringIO()
    with contextlib.ExitStack() as stack:
        limits = stack.enter_context(mock.patch.object(resource, "setrlimit"))
        stack.enter_context(mock.patch.dict(sys.modules))
        stack.enter_context(mock.patch.multiple(socket, **originals))
        stack.enter_context(mock.patch.object(_child.os, "dup", return_value=1))
        stack.enter_context(mock.patch.object(_child.os, "fdopen", return_value=stream))
        stack.enter_context(mock.patch.object(_child, "_silence_stdout"))
        yield limits, stream


def run_child(text, function="f"):
    """Run ``main`` over a temp program; return the parsed report and the raw output."""

    with tempfile.TemporaryDirectory() as workdir, isolated_process_state() as (_limits, stream):
        Path(workdir, "program.py").write_text(text, encoding="utf-8")
        status = _child.main(["child", workdir, function, "7"])
        raw = stream.getvalue()
    return status, json.loads(raw.removeprefix(_child.MARKER)), raw


class Reports(unittest.TestCase):
    def test_passing_doctests_report_ran_with_counts(self):
        status, report, raw = run_child(program("return 1", 1))
        self.assertEqual(status, 0)
        self.assertEqual(
            report,
            {"protocol": cv.HARNESS_PROTOCOL, "outcome": "ran", "attempted": 1, "failed": 0,
             "detail": ""},
        )
        self.assertEqual(harness._result_of(report), harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))
        self.assertTrue(raw.startswith(_child.MARKER) and raw.endswith("\n"))
        self.assertEqual(raw.count("\n"), 1, "the report is exactly one line")

    def test_failing_doctests_are_counted_not_raised(self):
        _, report, _ = run_child(program("return 2", 1))
        self.assertEqual((report["outcome"], report["attempted"], report["failed"]), ("ran", 1, 1))
        self.assertEqual(harness._result_of(report).outcome, cv.OUTCOME_FAILED)

    def test_doctest_output_does_not_reach_the_report_stream(self):
        _, _, raw = run_child(program("print('noise')\nreturn 1", 1))
        self.assertNotIn("noise", raw)

    def test_programs_that_cannot_be_loaded_are_load_errors(self):
        cases = {
            "RuntimeError": "raise RuntimeError('boom')\n",
            "SystemExit": "import sys\nsys.exit(3)\n",
            "SyntaxError": "def (:\n",
        }
        for detail, text in cases.items():
            with self.subTest(detail=detail):
                status, report, _ = run_child(text)
                self.assertEqual(status, 0)
                self.assertEqual((report["outcome"], report["detail"]), ("load_error", detail))

    def test_a_missing_target_function_is_a_load_error(self):
        _, report, _ = run_child(program("return 1", 1), function="absent")
        self.assertEqual((report["outcome"], report["detail"]), ("load_error", "AttributeError"))


class Limits(unittest.TestCase):
    def test_limits_are_applied_before_the_program_is_read(self):
        with isolated_process_state() as (limits, _stream):
            self.assertTrue(_child._limit(7))
        applied = {call.args[0]: call.args[1] for call in limits.call_args_list}
        self.assertEqual(applied[resource.RLIMIT_CPU], (7, 7))
        self.assertEqual(applied[resource.RLIMIT_AS], (_child.ADDRESS_SPACE_BYTES,) * 2)
        self.assertEqual(applied[resource.RLIMIT_FSIZE], (_child.FILE_SIZE_BYTES,) * 2)
        self.assertEqual(applied[resource.RLIMIT_CORE], (0, 0))

    def test_a_limit_the_kernel_refuses_means_limits_not_applied(self):
        with isolated_process_state() as (limits, _stream):
            limits.side_effect = OSError("denied")
            self.assertFalse(_child._limit(7))

    def test_missing_resource_module_means_limits_not_applied(self):
        with isolated_process_state():
            sys.modules["resource"] = None
            self.assertFalse(_child._limit(7))

    def test_without_limits_the_program_is_never_imported_or_run(self):
        marker = "RAN-WITHOUT-LIMITS"
        text = f"print({marker!r})\n" + program("return 1", 1)
        with tempfile.TemporaryDirectory() as workdir, isolated_process_state() as (limits, stream):
            limits.side_effect = OSError("denied")
            Path(workdir, "program.py").write_text(text, encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                status = _child.main(["child", workdir, "f", "7"])
            report = json.loads(stream.getvalue().removeprefix(_child.MARKER))
        self.assertEqual(status, 0)
        self.assertNotIn(marker, captured.getvalue())
        self.assertNotIn("task_gate_program", sys.modules)
        self.assertEqual((report["outcome"], report["detail"]), ("crashed", "limits_not_applied"))
        self.assertEqual(harness._result_of(report).outcome, cv.OUTCOME_CRASHED)


class Network(unittest.TestCase):
    def test_socket_entry_points_refuse_after_the_block(self):
        with isolated_process_state():
            _child._block_network()
            self.assertIsNone(sys.modules["_socket"])
            with self.assertRaises(OSError):
                socket.socket()
            for name in _child.BLOCKED_SOCKET_FUNCTIONS:
                if hasattr(socket, name):
                    with self.subTest(name=name), self.assertRaises(OSError):
                        getattr(socket, name)("example.invalid", 80)

    def test_the_block_is_undone_when_the_isolation_ends(self):
        before = (socket.socket, socket.create_connection, sys.modules.get("_socket"))
        with isolated_process_state():
            _child._block_network()
        self.assertEqual((socket.socket, socket.create_connection, sys.modules.get("_socket")), before)

    def test_a_program_that_opens_a_socket_sees_the_refusal(self):
        body = (
            "import socket\ntry:\n    socket.create_connection(('127.0.0.1', 9))\n"
            "except OSError:\n    return 'refused'\nreturn 'open'"
        )
        _, report, _ = run_child(program(body, "refused"))
        self.assertEqual((report["outcome"], report["failed"]), ("ran", 0))


class SilencedStdout(unittest.TestCase):
    def test_fd_one_is_pointed_at_devnull_and_the_saved_duplicate_still_writes(self):
        with tempfile.TemporaryFile() as captured:
            saved = os.dup(1)
            try:
                os.dup2(captured.fileno(), 1)
                report_fd = os.dup(1)
                _child._silence_stdout()
                os.write(1, b"program noise\n")
                os.write(report_fd, b"report line\n")
                os.close(report_fd)
            finally:
                os.dup2(saved, 1)
                os.close(saved)
            captured.seek(0)
            self.assertEqual(captured.read(), b"report line\n")


class Script(unittest.TestCase):
    def test_running_the_file_as_a_script_exits_zero_and_prints_the_report(self):
        with tempfile.TemporaryDirectory() as workdir, isolated_process_state() as (_l, stream):
            Path(workdir, "program.py").write_text(program("return 1", 1), encoding="utf-8")
            argv = ["_child.py", workdir, "f", "7"]
            with mock.patch.object(sys, "argv", argv), self.assertRaises(SystemExit) as exited:
                runpy.run_path(str(CHILD_PATH), run_name="__main__")
            raw = stream.getvalue()
        self.assertEqual(exited.exception.code, 0)
        self.assertTrue(raw.startswith(_child.MARKER))


if __name__ == "__main__":
    unittest.main()
