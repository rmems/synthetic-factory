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
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import sys
import traceback
import types
from pathlib import Path

PROTOCOL = "code-repair-harness/1"
PROGRAM_FILENAME = "program.py"
MAX_GOT_CHARS = 2_000
MAX_CAPTURE_CHARS = 65_536


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


def _utf8_digest(text: str) -> str:
    """Digest program-produced text even when it carries lone surrogates."""

    return hashlib.sha256(text.encode("utf-8", "backslashreplace")).hexdigest()


def _last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _scrub_workdir(text: str, workdir: str) -> str:
    """Strip the ephemeral workdir from observations so two runs compare equal."""

    if not workdir or not text:
        return text
    scrubbed = text.replace(workdir, "")
    # Path variants the traceback formatter may emit.
    scrubbed = scrubbed.replace(os.path.realpath(workdir), "")
    return scrubbed


def _clip(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_GOT_CHARS:
        return text, False
    return text[:MAX_GOT_CHARS], True


def _row(kind: str, index: int, status: str, got: str | None = None) -> dict[str, object]:
    row: dict[str, object] = {"id": f"{kind}:{index}", "status": status}
    if got is not None:
        clipped, truncated = _clip(got)
        row["got"] = clipped
        row["got_sha256"] = _utf8_digest(got)
        if truncated:
            row["truncated"] = True
    return row


class _Capture(io.StringIO):
    """Bound doctest's per-example capture, including writes that never return."""

    def write(self, text: str) -> int:
        if self.tell() + len(text) > MAX_CAPTURE_CHARS:
            raise ValueError("doctest output limit exceeded")
        return super().write(text)

    def getvalue(self) -> str:
        value = super().getvalue()
        return value + "\n" if value and not value.endswith("\n") else value

    def truncate(self, size: int = 0) -> int:
        self.seek(size)
        return super().truncate(size)


class _Runner(doctest.DocTestRunner):
    """Records one row per example instead of printing a report."""

    def __init__(self, rows: list, workdir: str = "") -> None:
        super().__init__(verbose=False, optionflags=0)
        self._fakeout = _Capture()
        self._rows = rows
        self._workdir = workdir

    @staticmethod
    def _index(test: doctest.DocTest, example: doctest.Example) -> int:
        for index, item in enumerate(test.examples):
            if item is example:
                return index
        raise ValueError("the runner reported an example the test does not hold")

    def _observe(self, got: str) -> str:
        # Keep the full observation (including multiline exception text) so two
        # runs that differ only before the final line still disagree on digest;
        # scrub the workdir so the ephemeral path never enters public evidence.
        return _scrub_workdir(got, self._workdir)

    def report_start(self, out, test, example) -> None:
        # Nothing to record before an example runs; the outcome hooks record the row.
        return None

    def report_success(self, out, test, example, got) -> None:
        observed = self._observe(got)
        display = _last_line(observed) if example.exc_msg is not None else observed
        row = _row("public", self._index(test, example), "pass", display)
        if example.exc_msg is not None:
            row["got_sha256"] = _utf8_digest(observed)
        self._rows.append(row)

    def report_failure(self, out, test, example, got) -> None:
        observed = self._observe(got)
        display = (
            _last_line(observed)
            if example.exc_msg is not None and "Traceback (most recent call last):" in observed
            else observed
        )
        row = _row("public", self._index(test, example), "fail", display)
        if example.exc_msg is not None:
            row["got_sha256"] = _utf8_digest(observed)
        self._rows.append(row)

    def report_unexpected_exception(self, out, test, example, exc_info) -> None:
        text = "".join(traceback.format_exception_only(exc_info[0], exc_info[1])).strip()
        self._rows.append(
            _row("public", self._index(test, example), "error", self._observe(text))
        )


def executable_examples(examples: list) -> list:
    """The examples the runner will actually execute: a ``+SKIP`` example reports no row."""

    return [example for example in examples if not example.options.get(doctest.SKIP)]


def _function_node(text: str, function: str) -> ast.FunctionDef:
    found = None
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            found = node  # last binding matches import semantics
    if found is None:
        raise LookupError(f"no module-level function named {function}")
    return found


def _load(workdir: Path):
    location = importlib.util.spec_from_file_location("program", workdir / PROGRAM_FILENAME)
    if location is None or location.loader is None:
        raise ImportError(f"no import spec for {PROGRAM_FILENAME}")
    module = importlib.util.module_from_spec(location)
    # Registered like an ordinary import so code that looks itself up by module
    # name (pickling an instance of one of its own classes, say) behaves as it
    # would outside the harness; the child is one-shot, so nothing unregisters it.
    sys.modules[location.name] = module
    location.loader.exec_module(module)
    return module


def _run_public(module, text: str, function: str, workdir: str = "") -> list:
    node = _function_node(text, function)
    docstring = ast.get_docstring(node, clean=True) or ""
    examples = executable_examples(doctest.DocTestParser().get_examples(docstring))
    # Report-controlling directives must not truncate the suite: one row per
    # executable example is part of the harness protocol with the parent.
    for example in examples:
        example.options.pop(doctest.FAIL_FAST, None)
    globs = dict(module.__dict__)
    test = doctest.DocTest(examples, globs, function, PROGRAM_FILENAME, node.lineno, docstring)
    rows: list = []
    _Runner(rows, workdir).run(test, out=lambda _text: None, clear_globs=True)
    return rows


def _is_integer_text(text: str) -> bool:
    digits = text[1:] if text.startswith("-") else text
    return digits.isdigit()


def _agree(got: str, want: str, spec: dict) -> bool:
    """equal reprs agree; integers only exactly; floats within the pinned tolerances."""

    if got == want:
        return True
    if _is_integer_text(got) or _is_integer_text(want):
        return False
    try:
        left, right = float(got), float(want)
    except ValueError:
        return False
    if not math.isfinite(left) or not math.isfinite(right):
        return False
    return math.isclose(left, right, rel_tol=spec["float_rel_tol"], abs_tol=spec["float_abs_tol"])


def _run_case(target, index: int, case: dict, spec: dict, workdir: str = "") -> dict:
    """One hidden case: a pass/fail row against the pinned want, or an observed repr."""

    try:
        result = target(*ast.literal_eval(case["args"]))
        got = _scrub_workdir(repr(result), workdir)
    except Exception as exc:  # the program under test may raise anything
        detail = _scrub_workdir(f"{type(exc).__name__}: {exc}", workdir)
        if case["want"] is None:
            return _row("hidden", index, "error", detail)
        return {**_row("hidden", index, "error"), "kind": "exception"}
    if case["want"] is None:
        return _row("hidden", index, "observed", got)
    if _agree(got, case["want"], spec):
        return {**_row("hidden", index, "pass", got), "kind": "ok"}
    return {**_row("hidden", index, "fail"), "kind": "value_mismatch"}


def _with_isolated_main(action):
    """Run ``action`` while ``__main__`` is not the trusted harness controller.

    Candidate code that does ``import __main__`` must not be able to replace
    ``_run_public``, ``_run_case``, or the report serializer on this process.
    """

    previous = sys.modules.get("__main__")
    sys.modules["__main__"] = types.ModuleType("program_main")
    try:
        return action()
    finally:
        if previous is not None:
            sys.modules["__main__"] = previous
        else:
            sys.modules.pop("__main__", None)


def _run(workdir: Path, spec: dict) -> dict:
    report: dict = {"protocol": PROTOCOL, "load": {"status": "ok", "error": None}}
    report["environment"] = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation().lower(),
        "platform": sys.platform,
        "limits_applied": _apply_limits(spec),
    }
    if not report["environment"]["limits_applied"]:
        report["load"] = {"status": "error", "error": "SANDBOX_UNAVAILABLE: resource limits"}
        return report
    text = (workdir / PROGRAM_FILENAME).read_text(encoding="utf-8")
    root = str(workdir)

    def execute():
        module = _load(workdir)
        getattr(module, spec["function"])
        public = _run_public(module, text, spec["function"], root) if spec["run_public"] else None
        active = module
        if spec["run_public"] and spec["cases"]:
            active = _load(workdir)
        target = getattr(active, spec["function"])
        hidden = [_run_case(target, i, case, spec, root) for i, case in enumerate(spec["cases"])]
        return public, hidden

    try:
        public, hidden = _with_isolated_main(execute)
    except Exception as exc:
        detail = _scrub_workdir(f"{type(exc).__name__}: {exc}", root)
        report["load"] = {"status": "error", "error": detail}
        return report
    report["public"] = public
    report["hidden"] = hidden
    return report


def main(argv: list[str], *, _dumps=json.dumps) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: _harness.py <workdir>\n")
        return 2
    workdir = Path(argv[1])
    real_stdout, real_stderr = sys.stdout, sys.stderr
    # The program under test never writes on the protocol channel; whatever it
    # prints is discarded outright, so streaming forever buys it nothing.
    with open(os.devnull, "w", encoding="utf-8") as sink:
        real_stdout.flush()
        real_stderr.flush()
        saved = (os.dup(1), os.dup(2))
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
        sys.stdout, sys.stderr = sink, sink
        try:
            spec = json.loads((workdir / "spec.json").read_text(encoding="utf-8"))
            report = _run(workdir, spec)
        except Exception as exc:
            error = f"HarnessError: {exc}"
            report = {"protocol": PROTOCOL, "load": {"status": "error", "error": error}}
        finally:
            real_stdout.flush()
            real_stderr.flush()
            for descriptor, backup in zip((1, 2), saved):
                os.dup2(backup, descriptor)
                os.close(backup)
            sys.stdout, sys.stderr = real_stdout, real_stderr
    # ensure_ascii=True keeps lone surrogates from breaking the exit-0 write.
    real_stdout.write(_dumps(report, sort_keys=True, allow_nan=False, ensure_ascii=True))
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
