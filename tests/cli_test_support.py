#!/usr/bin/env python3
"""In-process CLI invocation for tests that only need the exit code and stdio.

Calling a pipeline ``main(argv)`` under redirected stdout/stderr returns the
same ``returncode``/``stdout``/``stderr`` a ``subprocess.run`` capture would,
without paying for a fresh interpreter per call. Suites that assert
process-boundary behavior (argv handling, ``python -m`` execution) keep their
own subprocess helpers.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
from collections.abc import Callable, Sequence


def main_in_process(
    main: Callable[[list[str]], int | None],
    argv: Sequence[str],
    program: str,
) -> subprocess.CompletedProcess:
    """Run ``main(list(argv))`` in-process, mirroring a subprocess result."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = main(list(argv))
        except SystemExit as raised:
            code = raised.code
        if code is None:
            code = 0
        elif not isinstance(code, int):
            # A non-integer SystemExit code prints to stderr and exits 1.
            print(code, file=sys.stderr)
            code = 1
    return subprocess.CompletedProcess(
        [program, *argv], code, stdout.getvalue(), stderr.getvalue()
    )
