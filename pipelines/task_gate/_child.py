#!/usr/bin/env python3
"""The task gate's child: runs one program's target-function doctests and reports counts.

Standard library only; it imports nothing of this repository and is started by
``harness.py`` as ``python3 -P -s -S -B -X utf8 _child.py WORKDIR FUNCTION CPU_SECONDS`` with
a scrubbed environment and ``WORKDIR`` as its working directory, so neither the repository
nor any site-packages (solver modules included) is importable. ``WORKDIR/program.py`` is the
module under test. The report is the single marker line written to a duplicate of the real
stdout taken before the program loads; fd 1 itself is then pointed at ``os.devnull``, so
whatever the program prints (however much) never reaches the report file and cannot push the
report out of the window the parent reads. A program that deliberately writes to the duplicate
descriptor can still forge it (best effort, not a sandbox). Failures are data, never exit codes.
"""

import builtins
import doctest
import importlib.util
import json
import os
import sys

MARKER = "TASK-GATE-REPORT "
PROTOCOL = "task-gate-harness/1"
# Matches vocabulary.DETAIL_STDOUT_EQUIVALENT. This file cannot import the package.
DETAIL_STDOUT_EQUIVALENT = "stdout_equivalent"
ADDRESS_SPACE_BYTES = 1 << 30
FILE_SIZE_BYTES = 1 << 20
BLOCKED_SOCKET_FUNCTIONS = (
    "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
    "gethostbyaddr", "socketpair", "fromfd", "create_server",
)


def apply_limits(cpu_seconds):
    try:
        import resource

        for name, value in (
            (resource.RLIMIT_CPU, cpu_seconds),
            (resource.RLIMIT_AS, ADDRESS_SPACE_BYTES),
            (resource.RLIMIT_FSIZE, FILE_SIZE_BYTES),
            (resource.RLIMIT_CORE, 0),
        ):
            resource.setrlimit(name, (value, value))
    except (ImportError, OSError, ValueError, OverflowError):
        return False
    return True


def _refuse(*_args, **_kwargs):
    raise OSError("network access is disabled in the task gate harness")


def _block_network():
    """Best effort: replace the socket entry points before the program is imported."""

    import socket

    # Defense in depth: a later ``import _socket`` raises ImportError. ``socket`` above already
    # holds its own reference, so the replacements below are what stop ``socket`` users.
    sys.modules["_socket"] = None

    class Blocked(socket.socket):
        def __init__(self, *_args, **_kwargs):  # intentionally no super().__init__: it refuses
            _refuse()

    socket.socket = Blocked
    for name in BLOCKED_SOCKET_FUNCTIONS:
        if hasattr(socket, name):
            setattr(socket, name, _refuse)


def _report(outcome, attempted=0, failed=0, detail=""):
    return {
        "protocol": PROTOCOL, "outcome": outcome, "attempted": attempted, "failed": failed,
        "detail": detail,
    }


def _emit(stream, report):
    stream.write(MARKER + json.dumps(report, sort_keys=True) + "\n")
    stream.flush()


def load_program(workdir):
    path = os.path.join(workdir, "program.py")
    spec = importlib.util.spec_from_file_location("task_gate_program", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["task_gate_program"] = module
    spec.loader.exec_module(module)
    return module


def value_with_extra_stdout(want, got, displayed, flags=0):
    """True when ``got`` is extra stdout in front of one displayed value that matches ``want``.

    ``displayed`` is the repr of the value ``sys.displayhook`` saw, or empty when the example
    displayed nothing (a ``None`` result, including a function that only prints). A printed
    expected line with no displayed value is a real miss: the suffix of ``got`` is not proof
    that the result is unchanged. ``flags`` are the example's doctest option flags, so the
    value is compared the way ``DocTestRunner`` compares it.
    """

    if not displayed or not isinstance(displayed, str):
        return False
    if not isinstance(want, str) or not isinstance(got, str):
        return False
    value = displayed + "\n"
    if got == want or not got.endswith(value):
        return False
    return doctest.OutputChecker().check_output(want, value, flags)


class _Runner(doctest.DocTestRunner):
    """Counts doctest misses and whether every miss is stdout around a displayed value."""

    def __init__(self):
        super().__init__(verbose=False, optionflags=0)
        self.stdout_only = True
        self.displayed = ""
        self.reported = 0

    def report_start(self, out, test, example):
        self.displayed = ""

        def hook(value):
            if value is None:
                return
            builtins._ = value
            self.displayed = repr(value)
            sys.stdout.write(self.displayed + "\n")

        sys.displayhook = hook

    def report_failure(self, out, test, example, got):
        self.reported += 1
        noisy = example.exc_msg is None and value_with_extra_stdout(
            example.want, got, self.displayed, self.optionflags,
        )
        self.stdout_only = self.stdout_only and noisy

    def report_unexpected_exception(self, out, test, example, exc_info):
        self.stdout_only = False


def _doctests(module, function):
    target = getattr(module, function)
    finder = doctest.DocTestFinder(recurse=False)
    tests = finder.find(target, function, module=module, globs=dict(module.__dict__))
    runner = _Runner()
    attempted = failed = 0
    for test in tests:
        result = runner.run(test, out=lambda _text: None, clear_globs=False)
        attempted += result.attempted
        failed += result.failed
    return attempted, failed, _equivalent_detail(failed, runner)


def _equivalent_detail(failed, runner):
    """``stdout_equivalent`` only when every counted miss was reported as such.

    ``REPORT_ONLY_FIRST_FAILURE`` counts later misses and does not report them.
    """

    if not failed:
        return ""
    if not runner.stdout_only:
        return ""
    if failed != runner.reported:
        return ""
    return DETAIL_STDOUT_EQUIVALENT


def silence_stdout():
    """Point fd 1 at ``os.devnull`` so the program's output never mixes with the report."""

    sink = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(sink, 1)
    finally:
        os.close(sink)


def main(argv):
    workdir, function, cpu_seconds = argv[1], argv[2], int(argv[3])
    report_stream = os.fdopen(os.dup(1), "w", encoding="utf-8")
    silence_stdout()
    if not apply_limits(cpu_seconds):
        _emit(report_stream, _report("crashed", detail="limits_not_applied"))
        return 0
    _block_network()
    try:
        module = load_program(workdir)
        attempted, failed, detail = _doctests(module, function)
    except BaseException as exc:  # the program may raise anything, including SystemExit
        _emit(report_stream, _report("load_error", detail=type(exc).__name__))
        return 0
    _emit(report_stream, _report("ran", attempted, failed, detail))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
