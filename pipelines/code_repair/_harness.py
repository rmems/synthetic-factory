#!/usr/bin/env python3
"""The sandboxed child of the code-repair executor: stdlib only, imports nothing of the package.

Runs under ``python -P -s -S -B -X utf8`` in a fresh working directory holding
``program.py`` and ``spec.json``; applies its own resource limits; loads the
module through ``importlib``; runs the target function's doctest examples once
in order (they may carry state) through a ``DocTestRunner`` whose report hooks
record one row per example; evaluates the pinned hidden cases; and prints one
JSON object on stdout. It exits 0 whatever the program did: failures are rows,
never exit codes, and any internal error is reported in ``load``.
"""

from __future__ import annotations

import ast
import doctest
import importlib.util
import io
import json
import math
import platform
import sys
import traceback
from pathlib import Path

PROTOCOL = "code-repair-harness/1"
PROGRAM_FILENAME = "program.py"
MAX_GOT_CHARS = 2_000


def _apply_limits(spec: dict) -> bool:
    try:
        import resource
    except ImportError:  # pragma: no cover - POSIX only
        return False
    limits = (
        (resource.RLIMIT_CPU, int(spec["cpu_seconds"])),
        (resource.RLIMIT_AS, int(spec["address_space_bytes"])),
        (resource.RLIMIT_FSIZE, int(spec["file_size_bytes"])),
    )
    for name, value in limits:
        resource.setrlimit(name, (value, value))
    return True


def _clip(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_GOT_CHARS:
        return text, False
    return text[:MAX_GOT_CHARS], True


def _row(kind: str, index: int, status: str, got: str | None = None) -> dict:
    row = {"id": f"{kind}:{index}", "status": status}
    if got is not None:
        clipped, truncated = _clip(got)
        row["got"] = clipped
        if truncated:
            row["truncated"] = True
    return row


class _Runner(doctest.DocTestRunner):
    """Records one row per example instead of printing a report."""

    def __init__(self, rows: list) -> None:
        super().__init__(verbose=False, optionflags=0)
        self._rows = rows

    @staticmethod
    def _index(test: doctest.DocTest, example: doctest.Example) -> int:
        for index, item in enumerate(test.examples):
            if item is example:
                return index
        raise ValueError("the runner reported an example the test does not hold")

    def report_start(self, out, test, example) -> None:
        # Nothing to record before an example runs; the outcome hooks record the row.
        return None

    def report_success(self, out, test, example, got) -> None:
        self._rows.append(_row("public", self._index(test, example), "pass"))

    def report_failure(self, out, test, example, got) -> None:
        self._rows.append(_row("public", self._index(test, example), "fail", got))

    def report_unexpected_exception(self, out, test, example, exc_info) -> None:
        text = "".join(traceback.format_exception_only(exc_info[0], exc_info[1])).strip()
        self._rows.append(_row("public", self._index(test, example), "error", text))


def _function_node(text: str, function: str) -> ast.FunctionDef:
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return node
    raise LookupError(f"no module-level function named {function}")


def _load(workdir: Path):
    location = importlib.util.spec_from_file_location("program", workdir / PROGRAM_FILENAME)
    if location is None or location.loader is None:
        raise ImportError(f"no import spec for {PROGRAM_FILENAME}")
    module = importlib.util.module_from_spec(location)
    location.loader.exec_module(module)
    return module


def _run_public(module, text: str, function: str) -> list:
    node = _function_node(text, function)
    docstring = ast.get_docstring(node, clean=True) or ""
    examples = doctest.DocTestParser().get_examples(docstring)
    globs = dict(module.__dict__)
    test = doctest.DocTest(examples, globs, function, PROGRAM_FILENAME, node.lineno, docstring)
    rows: list = []
    _Runner(rows).run(test, out=lambda _text: None, clear_globs=True)
    return rows


def _is_integer_text(text: str) -> bool:
    digits = text[1:] if text.startswith("-") else text
    return digits.isdigit()


def _agree(got: str, want: str, spec: dict) -> bool:
    """Equal reprs agree; integers only exactly; floats within the pinned tolerances."""

    if got == want:
        return True
    if _is_integer_text(got) or _is_integer_text(want):
        return False
    try:
        left, right = float(got), float(want)
    except ValueError:
        return False
    return math.isclose(left, right, rel_tol=spec["float_rel_tol"], abs_tol=spec["float_abs_tol"])


def _run_case(target, index: int, case: dict, spec: dict) -> dict:
    """One hidden case: a pass/fail row against the pinned want, or an observed repr."""

    try:
        result = target(*ast.literal_eval(case["args"]))
    except Exception as exc:  # the program under test may raise anything
        if case["want"] is None:
            return _row("hidden", index, "error", f"{type(exc).__name__}: {exc}")
        return {**_row("hidden", index, "error"), "kind": "exception"}
    got = repr(result)
    if case["want"] is None:
        return _row("hidden", index, "observed", got)
    if _agree(got, case["want"], spec):
        return {**_row("hidden", index, "pass"), "kind": "ok"}
    return {**_row("hidden", index, "fail"), "kind": "value_mismatch"}


def _run(workdir: Path, spec: dict) -> dict:
    report: dict = {"protocol": PROTOCOL, "load": {"status": "ok", "error": None}}
    report["environment"] = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation().lower(),
        "platform": sys.platform,
        "limits_applied": _apply_limits(spec),
    }
    text = (workdir / PROGRAM_FILENAME).read_text(encoding="utf-8")
    try:
        module = _load(workdir)
        target = getattr(module, spec["function"])
    except Exception as exc:
        report["load"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        return report
    report["public"] = _run_public(module, text, spec["function"]) if spec["run_public"] else None
    report["hidden"] = [_run_case(target, i, case, spec) for i, case in enumerate(spec["cases"])]
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: _harness.py <workdir>\n")
        return 2
    workdir = Path(argv[1])
    real_stdout, real_stderr = sys.stdout, sys.stderr
    # The program under test never writes on the protocol channel, and its
    # stderr goes to a bounded in-memory sink the parent never has to read.
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        spec = json.loads((workdir / "spec.json").read_text(encoding="utf-8"))
        report = _run(workdir, spec)
    except Exception as exc:
        error = f"HarnessError: {exc}"
        report = {"protocol": PROTOCOL, "load": {"status": "error", "error": error}}
    finally:
        sys.stdout, sys.stderr = real_stdout, real_stderr
    real_stdout.write(json.dumps(report, sort_keys=True, allow_nan=False))
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
