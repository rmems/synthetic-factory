#!/usr/bin/env python3
"""The task gate's child: runs one program's target-function doctests and reports counts.

Standard library only; it imports nothing of this repository and is started by
``harness.py`` as ``python3 -P -s -S -B -X utf8 _child.py WORKDIR FUNCTION CPU_SECONDS`` with
a scrubbed environment and ``WORKDIR`` as its working directory, so neither the repository
nor any site-packages (solver modules included) is importable. ``WORKDIR/program.py`` is the
module under test. The report is the single marker line written to the real stdout; the
program under test never sees that stream. Failures are data, never exit codes.
"""

import doctest
import importlib.util
import json
import os
import sys

MARKER = "TASK-GATE-REPORT "
PROTOCOL = "task-gate-harness/1"
ADDRESS_SPACE_BYTES = 1 << 30
FILE_SIZE_BYTES = 1 << 20


def _limit(cpu_seconds):
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

    class Blocked(socket.socket):
        def __init__(self, *args, **kwargs):
            _refuse()

    socket.socket = Blocked
    for name in (
        "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex",
        "gethostbyaddr", "socketpair", "fromfd", "create_server",
    ):
        if hasattr(socket, name):
            setattr(socket, name, _refuse)


def _emit(stream, outcome, attempted=0, failed=0, detail=""):
    report = {
        "protocol": PROTOCOL, "outcome": outcome, "attempted": attempted, "failed": failed,
        "detail": detail,
    }
    stream.write(MARKER + json.dumps(report, sort_keys=True) + "\n")
    stream.flush()


def _load(workdir):
    path = os.path.join(workdir, "program.py")
    spec = importlib.util.spec_from_file_location("task_gate_program", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["task_gate_program"] = module
    spec.loader.exec_module(module)
    return module


def _doctests(module, function):
    target = getattr(module, function)
    finder = doctest.DocTestFinder(recurse=False)
    tests = finder.find(target, function, module=module, globs=dict(module.__dict__))
    runner = doctest.DocTestRunner(verbose=False, optionflags=0)
    attempted = failed = 0
    for test in tests:
        result = runner.run(test, out=lambda _text: None, clear_globs=False)
        attempted += result.attempted
        failed += result.failed
    return attempted, failed


def main(argv):
    workdir, function, cpu_seconds = argv[1], argv[2], int(argv[3])
    report_stream = os.fdopen(os.dup(1), "w", encoding="utf-8")
    if not _limit(cpu_seconds):
        _emit(report_stream, "crashed", detail="limits_not_applied")
        return 0
    _block_network()
    try:
        module = _load(workdir)
        attempted, failed = _doctests(module, function)
    except BaseException as exc:  # the program may raise anything, including SystemExit
        _emit(report_stream, "load_error", detail=type(exc).__name__)
        return 0
    _emit(report_stream, "ran", attempted, failed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
