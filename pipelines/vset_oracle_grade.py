"""Per-test oracle grading outside the candidate's result objects.

Each declared test id runs in a fresh child. The child calls the suite
function captured from the class body and does not consult ``TestCase.run``
or a ``TestResult``. The parent decides pass/fail from the child's exit code
and a nonce it generated: the nonce is written to the child only after the
child reports that the real call returned, and it is never placed on the
command line or in the environment.
"""

from __future__ import annotations

import os
import secrets
import select
import signal
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
_NONCE_FD = 3
_STATUS_FD = 4
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
    NONCE_FD = 3
    STATUS_FD = 4


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


    def _take_nonce() -> bytes:
        nonce = b""
        while len(nonce) < 16:
            part = os.read(NONCE_FD, 16 - len(nonce))
            if not part:
                break
            nonce += part
        os.close(NONCE_FD)
        return nonce


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
        # Read the nonce and close its fd before src/ is imported. The numbers
        # are not on sys.argv, so candidate code cannot replay this handshake.
        nonce = _take_nonce()
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
            os.write(STATUS_FD, b"L" + str(exc).encode("utf-8", "replace"))
            _write_capture(real_out, buf)
            return 1
        sys.stdout = real_out
        sys.stderr = real_out
        if marker != "P":
            os.write(STATUS_FD, marker.encode("ascii"))
            _write_capture(real_out, buf)
            return 1
        os.write(STATUS_FD, b"P" + nonce)
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

    ``P`` is a pass only when the echoed nonce is the one this parent issued
    and the child exited 0.
    """

    if marker != b"P":
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


def _read_result(status_r: int, pid: int, deadline: float) -> tuple[bytes, bytes]:
    marker = _read_exact(status_r, 1, pid, deadline)
    if marker != b"P":
        return marker, b""
    return marker, _read_exact(status_r, _NONCE_LEN, pid, deadline)


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


def _queue_dup(actions: list[tuple], src: int, dst: int) -> None:
    if src != dst:
        actions.append((os.POSIX_SPAWN_DUP2, src, dst))


def _queue_close(actions: list[tuple], src: int) -> None:
    if src > _STATUS_FD:
        actions.append((os.POSIX_SPAWN_CLOSE, src))


def _file_actions(nonce_r: int, status_w: int, capture_fd: int, devnull: int) -> list[tuple]:
    actions: list[tuple] = []
    _queue_dup(actions, nonce_r, _NONCE_FD)
    _queue_dup(actions, status_w, _STATUS_FD)
    _queue_dup(actions, devnull, 0)
    _queue_dup(actions, capture_fd, 1)
    _queue_dup(actions, capture_fd, 2)
    _queue_close(actions, nonce_r)
    _queue_close(actions, status_w)
    _queue_close(actions, devnull)
    _queue_close(actions, capture_fd)
    return actions


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


def _posix_spawn(argv: list[str], actions: list[tuple]) -> int:
    return os.posix_spawn(argv[0], argv, dict(os.environ), file_actions=actions)


def _runner_file(work: Path) -> Path:
    path = work.parent / "vset-oracle-runner.py"
    if path.is_file():
        return path
    path.write_text(_RUNNER_SOURCE, encoding="utf-8")
    return path


def _exit_code(status: int) -> int:
    return os.waitstatus_to_exitcode(status)


def _wait_pid(pid: int, deadline: float) -> int:
    while True:
        done, status = os.waitpid(pid, os.WNOHANG)
        if done == pid:
            return _exit_code(status)
        if _time_left(deadline) <= 0:
            _kill_pid(pid)
            raise VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: timed out"
            )
        time.sleep(0.05)


def _spawn(argv: list[str], nonce_r: int, status_w: int, capture_fd: int) -> int:
    devnull = os.open(os.devnull, os.O_RDONLY)
    try:
        actions = _file_actions(nonce_r, status_w, capture_fd, devnull)
        return _posix_spawn(argv, actions)
    finally:
        _close_fd(devnull)


def _capture_path(work: Path, spec: dict[str, str], names: tuple[str, str]) -> Path:
    class_name, method_name = names
    return work.parent / f"vset-cap-{spec['module']}-{class_name}-{method_name}.txt"


def _grade_one(work: Path, spec: dict[str, str], names: tuple[str, str], nonce: bytes) -> str:
    capture_path = _capture_path(work, spec, names)
    nonce_r, nonce_w = os.pipe()
    status_r, status_w = os.pipe()
    capture_fd = os.open(capture_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    pid = 0
    deadline = time.monotonic() + _CHILD_TIMEOUT_S
    try:
        os.write(nonce_w, nonce)
        _close_fd(nonce_w)
        nonce_w = -1
        pid = _spawn(
            _child_argv(_runner_file(work), work, spec, names),
            nonce_r,
            status_w,
            capture_fd,
        )
        _close_fd(nonce_r)
        nonce_r = -1
        _close_fd(status_w)
        status_w = -1
        marker, echo = _read_result(status_r, pid, deadline)
        if marker == b"L":
            detail = _read_load_error(status_r, pid, deadline)
            _wait_pid(pid, deadline)
            raise _load_error(spec["relative"], detail)
        return _status_for(marker, echo, nonce, _wait_pid(pid, deadline))
    except OSError as exc:
        _kill_pid(pid)
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    finally:
        _close_fd(nonce_r)
        _close_fd(nonce_w)
        _close_fd(status_r)
        _close_fd(status_w)
        _close_fd(capture_fd)


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
