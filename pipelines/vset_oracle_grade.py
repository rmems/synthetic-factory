"""Per-test oracle grading outside the candidate's result objects.

Each declared test id runs in a fresh child. The child calls the suite
function captured from the class body and does not consult ``TestCase.run``
or a ``TestResult``. The parent decides pass/fail from the child's exit code
and a nonce it generated: the nonce is written to the child only after the
child reports that the real call returned, and it is never placed on the
command line or in the environment.
"""

from __future__ import annotations

import fcntl
import os
import secrets
import select
import signal
import subprocess  # nosec B404
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_grade")
    from .vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_grade"
    )
    from vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
    )

_CAPTURE_LIMIT = 4000
_NONCE_LEN = 16
_INTERPRETER_FLAGS = ("-I", "-B", "-X", "utf8")
_CHILD_TIMEOUT_S = 30.0
_MARKER_STATUS = {
    b"F": "FAIL",
    b"E": "ERROR",
    b"S": "SKIP",
    b"X": "expectedFailure",
    b"U": "unexpectedSuccess",
}

# The kept function is the class-body callable. A patched TestCase.run or
# TestResult can report success without executing it; this runner never asks
# them. The nonce lives only in the parent until that call returns.
_RUNNER_SOURCE = textwrap.dedent(
    """\
    import importlib.util
    import io
    import os
    import sys
    import unittest
    from pathlib import Path

    KEEP = "_vset_kept_"


    def _install():
        original = unittest.case.TestCase
        saved = (
            original._callSetUp,
            original._callTestMethod,
            original._callTearDown,
            original.doCleanups,
        )

        class _KeepMeta(type(original)):
            def __new__(mcs, name, bases, namespace, **kwargs):
                kept = {
                    key: value
                    for key, value in namespace.items()
                    if key.startswith("test") and callable(value)
                }
                cls = super().__new__(mcs, name, bases, namespace, **kwargs)
                for key, value in kept.items():
                    setattr(cls, KEEP + key, value)
                    if cls.__dict__.get(key) is not value:
                        setattr(cls, key, value)
                return cls

        class _KeepCase(original, metaclass=_KeepMeta):
            pass

        unittest.case.TestCase = _KeepCase
        unittest.TestCase = _KeepCase
        return saved


    def _load(path, module_name):
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module


    def _pipe_fds():
        found = []
        for fd in range(3, 64):
            try:
                os.fstat(fd)
            except OSError:
                continue
            found.append(fd)
        if len(found) < 2:
            raise OSError("missing oracle pipes")
        return found[0], found[1]


    def _kept(cls, method_name):
        key = KEEP + method_name
        for klass in cls.__mro__:
            if key in klass.__dict__:
                return klass.__dict__[key]
        raise AttributeError(method_name)


    def _invoke(case, func, call_setup, call_method, call_teardown, cleanups):
        if getattr(func, "__unittest_skip__", False):
            return "S"
        expecting = bool(getattr(func, "__unittest_expecting_failure__", False))
        bound = func.__get__(case, type(case))
        try:
            call_setup(case)
            call_method(case, bound)
            call_teardown(case)
            cleanups(case)
        except unittest.SkipTest:
            return "S"
        except AssertionError:
            return "X" if expecting else "F"
        except Exception:
            return "E"
        return "U" if expecting else "P"


    def _write_capture(stream, buf) -> None:
        stream.write(buf.getvalue())
        stream.flush()


    def main() -> int:
        # The two inherited pipes are the nonce read end, then the status
        # write end. The nonce is not read until the test call returns, and
        # neither number is on sys.argv.
        nonce_fd, status_fd = _pipe_fds()
        work, path, module_name, class_name, method_name = sys.argv[1:6]
        os.chdir(work)
        sys.path.insert(0, str(Path(work) / "src"))
        call_setup, call_method, call_teardown, cleanups = _install()
        real_out = sys.stdout
        buf = io.StringIO()
        sys.stdout = buf
        sys.stderr = buf
        try:
            module = _load(path, module_name)
            cls = getattr(module, class_name)
            marker = _invoke(
                cls(method_name),
                _kept(cls, method_name),
                call_setup,
                call_method,
                call_teardown,
                cleanups,
            )
        except Exception as exc:
            sys.stdout = real_out
            sys.stderr = real_out
            os.write(status_fd, b"L" + str(exc).encode("utf-8", "replace"))
            _write_capture(real_out, buf)
            return 1
        sys.stdout = real_out
        sys.stderr = real_out
        if marker != "P":
            os.write(status_fd, marker.encode("ascii"))
            _write_capture(real_out, buf)
            return 1
        os.write(status_fd, b"D")
        nonce = b""
        while len(nonce) < 16:
            part = os.read(nonce_fd, 16 - len(nonce))
            if not part:
                break
            nonce += part
        os.close(nonce_fd)
        os.write(status_fd, nonce)
        _write_capture(real_out, buf)
        return 0


    raise SystemExit(main())
    """
)


def _suite_ok(rows: list[dict[str, str]], expected: list[str]) -> bool:
    reported = sorted(row["id"] for row in rows)
    declared = sorted(expected)
    if reported != declared:
        return False
    if not declared:
        return False
    return all(row["status"] == "ok" for row in rows)


def _suite_report(
    rows: list[dict[str, str]], expected: list[str], captured: str
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: item["id"])
    report: dict[str, Any] = {
        "tests": ordered,
        "failures": sum(item["status"] == "FAIL" for item in ordered),
        "errors": sum(item["status"] == "ERROR" for item in ordered),
        "ok": _suite_ok(ordered, expected),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    if captured.strip():
        report["captured_output"] = captured[-_CAPTURE_LIMIT:]
    return report


def _echo_matches(echo: bytes, nonce: bytes, returncode: int) -> bool:
    if echo != nonce:
        return False
    return returncode == 0


def _status_for(marker: bytes, echo: bytes, nonce: bytes, returncode: int) -> str:
    """Map a child marker to a suite status.

    ``D`` is a pass only when the echoed nonce is the one this parent issued
    and the child exited 0. The parent writes that nonce only after ``D``.
    """

    if marker != b"D":
        return _MARKER_STATUS.get(marker, "ERROR")
    if _echo_matches(echo, nonce, returncode):
        return "ok"
    return "ERROR"


def _kill_pid(pid: int) -> None:
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return
    os.waitpid(pid, 0)


def _time_left(deadline: float) -> float:
    return deadline - time.monotonic()


def _read_exact(fd: int, count: int, pid: int, deadline: float) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining > 0:
        if _time_left(deadline) <= 0:
            _kill_pid(pid)
            raise VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: timed out"
            )
        ready, _, _ = select.select([fd], [], [], _time_left(deadline))
        if not ready:
            _kill_pid(pid)
            raise VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: timed out"
            )
        part = os.read(fd, remaining)
        if not part:
            break
        chunks.append(part)
        remaining -= len(part)
    return b"".join(chunks)


def _close_fd(fd: int) -> None:
    if fd < 0:
        return
    try:
        os.close(fd)
    except OSError:
        return


def _load_error(relative: str, detail: str) -> VSetValidationError:
    text = " ".join(detail.split())
    if len(text) > 500:
        text = text[:500]
    return VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH,
        f"test module {relative} failed to load: {text}",
    )


def _read_load_error(status_r: int, pid: int, deadline: float) -> str:
    raw = _read_exact(status_r, _CAPTURE_LIMIT, pid, deadline)
    return raw.decode("utf-8", "replace")


def _raise_fd(fd: int, floor: int) -> int:
    if fd > floor:
        os.set_inheritable(fd, True)
        return fd
    moved = fcntl.fcntl(fd, fcntl.F_DUPFD, floor + 1)
    os.close(fd)
    os.set_inheritable(moved, True)
    return moved


def _ordered_ends() -> tuple[int, int, int, int]:
    """Return nonce_r, nonce_w, status_r, status_w with nonce_r < status_w."""

    nonce_r, nonce_w = os.pipe()
    status_r, status_w = os.pipe()
    nonce_r = _raise_fd(nonce_r, 4)
    status_w = _raise_fd(status_w, nonce_r)
    return nonce_r, nonce_w, status_r, status_w


def _child_argv(runner: Path, work: Path, spec: dict[str, str], names: tuple[str, str]) -> list[str]:
    class_name, method_name = names
    return [
        sys.executable,
        *_INTERPRETER_FLAGS,
        str(runner),
        str(work),
        spec["path"],
        spec["module"],
        class_name,
        method_name,
    ]


def _start_child(argv: list[str], nonce_r: int, status_w: int, capture):
    os.set_inheritable(nonce_r, True)
    os.set_inheritable(status_w, True)
    # Literal interpreter flags. The runner path and test id are parent-owned.
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
    return subprocess.Popen(  # nosec B603
        argv,
        cwd=argv[6],
        stdin=subprocess.DEVNULL,
        stdout=capture,
        stderr=subprocess.STDOUT,
        pass_fds=(nonce_r, status_w),
    )


def _runner_file(work: Path) -> Path:
    path = work.parent / "vset-oracle-runner.py"
    if path.is_file():
        return path
    path.write_text(_RUNNER_SOURCE, encoding="utf-8")
    return path


def _capture_path(work: Path, spec: dict[str, str], names: tuple[str, str]) -> Path:
    class_name, method_name = names
    return work.parent / f"vset-cap-{spec['module']}-{class_name}-{method_name}.txt"


def _wait_child(proc: subprocess.Popen[bytes], deadline: float) -> int:
    timeout = _time_left(deadline)
    if timeout <= 0:
        proc.kill()
        proc.wait()
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: timed out"
        )
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: timed out"
        ) from None


def _echo_after_done(
    status_r: int, reply: tuple[int, bytes], proc: subprocess.Popen[bytes], deadline: float
) -> tuple[bytes, bytes]:
    nonce_w, nonce = reply
    marker = _read_exact(status_r, 1, proc.pid, deadline)
    if marker != b"D":
        return marker, b""
    os.write(nonce_w, nonce)
    return marker, _read_exact(status_r, _NONCE_LEN, proc.pid, deadline)


def _grade_one(work: Path, spec: dict[str, str], names: tuple[str, str], nonce: bytes) -> str:
    capture_path = _capture_path(work, spec, names)
    nonce_r, nonce_w, status_r, status_w = _ordered_ends()
    capture = capture_path.open("wb")
    proc: subprocess.Popen[bytes] | None = None
    deadline = time.monotonic() + _CHILD_TIMEOUT_S
    try:
        proc = _start_child(
            _child_argv(_runner_file(work), work, spec, names),
            nonce_r,
            status_w,
            capture,
        )
        _close_fd(nonce_r)
        nonce_r = -1
        _close_fd(status_w)
        status_w = -1
        marker, echo = _echo_after_done(status_r, (nonce_w, nonce), proc, deadline)
        if marker == b"L":
            detail = _read_load_error(status_r, proc.pid, deadline)
            _wait_child(proc, deadline)
            raise _load_error(spec["relative"], detail)
        return _status_for(marker, echo, nonce, _wait_child(proc, deadline))
    except OSError as exc:
        if proc is not None:
            proc.kill()
            proc.wait()
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    finally:
        _close_fd(nonce_r)
        _close_fd(nonce_w)
        _close_fd(status_r)
        _close_fd(status_w)
        capture.close()


def _spec_for(test_id: str, modules: list[dict[str, str]]) -> dict[str, str]:
    for item in modules:
        if test_id.startswith(item["module"] + "."):
            return item
    raise VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: unknown test {test_id}"
    )


def _class_and_method(test_id: str, module_name: str) -> tuple[str, str]:
    class_name, dot, method_name = test_id[len(module_name) + 1 :].rpartition(".")
    if not dot:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    if not class_name:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    if not method_name:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: bad test id {test_id}"
        )
    return class_name, method_name


def _capture_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_bytes().decode("utf-8", "replace")


def grade_suite(
    work: Path, modules: list[dict[str, str]], expected: list[str]
) -> dict[str, Any]:
    """Run every declared id in its own child and build the suite report."""

    rows: list[dict[str, str]] = []
    captured: list[str] = []
    runner = _runner_file(work) if expected else None
    for test_id in expected:
        spec = _spec_for(test_id, modules)
        names = _class_and_method(test_id, spec["module"])
        status = _grade_one(work, spec, names, secrets.token_bytes(_NONCE_LEN))
        rows.append({"id": test_id, "status": status})
        captured.append(_capture_text(_capture_path(work, spec, names)))
    if runner is not None:
        runner.unlink(missing_ok=True)
    return _suite_report(rows, expected, "".join(captured))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
