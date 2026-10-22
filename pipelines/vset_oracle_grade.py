"""Per-test oracle grading outside the candidate's result objects.

Each declared test id runs in a fresh child. The child calls the suite
function captured from the class body and does not consult ``TestCase.run``
or a ``TestResult``. The parent decides pass/fail from the child's exit code
and a nonce it generated: the nonce is written to the child only after the
child reports that the real call returned, and it is never placed on the
command line or in the environment.
"""

from __future__ import annotations

import ast
import os
import secrets
import subprocess  # nosec B404
import sys
import textwrap
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
_KEPT = "_vset_kept_"
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
        work, path, module_name, class_name, method_name, nonce_fd, status_fd = sys.argv[1:8]
        nonce_fd = int(nonce_fd)
        status_fd = int(status_fd)
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
            func = getattr(cls, KEEP + method_name)
            marker = _invoke(
                cls(method_name),
                func,
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
        os.write(status_fd, b"P")
        nonce = b""
        while len(nonce) < 16:
            part = os.read(nonce_fd, 16 - len(nonce))
            if not part:
                break
            nonce += part
        os.write(status_fd, nonce)
        _write_capture(real_out, buf)
        return 0


    raise SystemExit(main())
    """
)


def _base_tail(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    return getattr(node, "id", "")


def _case_node(node: ast.stmt) -> ast.ClassDef | None:
    if not isinstance(node, ast.ClassDef):
        return None
    for base in node.bases:
        if _base_tail(base) == "TestCase":
            return node
    return None


def _method_name(node: ast.stmt) -> str:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
        return node.name
    return ""


def _case_ids(module_name: str, case: ast.ClassDef) -> list[str]:
    names = [_method_name(item) for item in case.body]
    return [f"{module_name}.{case.name}.{name}" for name in names if name]


def declared_test_ids(path: Path, module_name: str) -> list[str]:
    """Ids of class-body ``test*`` methods on ``TestCase`` subclasses."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ids: list[str] = []
    for node in tree.body:
        case = _case_node(node)
        if case is not None:
            ids.extend(_case_ids(module_name, case))
    return ids


def _suite_ok(rows: list[dict[str, str]], expected: list[str]) -> bool:
    reported = sorted(row["id"] for row in rows)
    declared = sorted(expected)
    if reported != declared or not declared:
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


def _status_for(marker: bytes, echo: bytes, nonce: bytes, returncode: int) -> str:
    """Map a child marker to a suite status.

    ``P`` is a pass only when the child echoed this parent's nonce and exited 0.
    """

    if marker == b"P" and echo == nonce and returncode == 0:
        return "ok"
    return _MARKER_STATUS.get(marker, "ERROR")


def _read_exact(fd: int, count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining > 0:
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


def _argv(
    work: Path,
    spec: dict[str, str],
    class_name: str,
    method_name: str,
    nonce_fd: int,
    status_fd: int,
) -> list[str]:
    return [
        sys.executable,
        *_INTERPRETER_FLAGS,
        "-c",
        _RUNNER_SOURCE,
        str(work),
        spec["path"],
        spec["module"],
        class_name,
        method_name,
        str(nonce_fd),
        str(status_fd),
    ]


def _popen(argv: list[str], work: Path, nonce_r: int, status_w: int, capture):
    os.set_inheritable(nonce_r, True)
    os.set_inheritable(status_w, True)
    # Literal argv: this interpreter and the runner constant. No shell.
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
    return subprocess.Popen(  # nosec B603
        argv,
        cwd=work,
        stdin=subprocess.DEVNULL,
        stdout=capture,
        stderr=subprocess.STDOUT,
        pass_fds=(nonce_r, status_w),
    )


def _read_load_error(status_r: int) -> str:
    return _read_exact(status_r, _CAPTURE_LIMIT).decode("utf-8", "replace")


def _exchange(status_r: int, nonce_w: int, nonce: bytes) -> tuple[bytes, bytes]:
    marker = _read_exact(status_r, 1)
    if marker != b"P":
        return marker, b""
    os.write(nonce_w, nonce)
    return marker, _read_exact(status_r, _NONCE_LEN)


def _load_error(relative: str, detail: str) -> VSetValidationError:
    text = " ".join(detail.split())
    if len(text) > 500:
        text = text[:500]
    return VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH,
        f"test module {relative} failed to load: {text}",
    )


def _wait(proc: subprocess.Popen[bytes] | None) -> int:
    if proc is None:
        return 1
    return proc.wait()


def _abandon(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.kill()
    proc.wait()


def _grade_one(
    work: Path,
    spec: dict[str, str],
    class_name: str,
    method_name: str,
    nonce: bytes,
    capture_path: Path,
) -> str:
    nonce_r, nonce_w = os.pipe()
    status_r, status_w = os.pipe()
    proc: subprocess.Popen[bytes] | None = None
    capture = capture_path.open("wb")
    try:
        proc = _popen(
            _argv(work, spec, class_name, method_name, nonce_r, status_w),
            work,
            nonce_r,
            status_w,
            capture,
        )
        _close_fd(nonce_r)
        nonce_r = -1
        _close_fd(status_w)
        status_w = -1
        marker, echo = _exchange(status_r, nonce_w, nonce)
        if marker == b"L":
            detail = _read_load_error(status_r)
            raise _load_error(spec["relative"], detail)
        return _status_for(marker, echo, nonce, _wait(proc))
    except OSError as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    finally:
        _abandon(proc)
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
    if not dot or not class_name or not method_name:
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
    for index, test_id in enumerate(expected):
        spec = _spec_for(test_id, modules)
        class_name, method_name = _class_and_method(test_id, spec["module"])
        capture_path = work.parent / f"vset-cap-{index}.txt"
        status = _grade_one(
            work,
            spec,
            class_name,
            method_name,
            secrets.token_bytes(_NONCE_LEN),
            capture_path,
        )
        rows.append({"id": test_id, "status": status})
        captured.append(_capture_text(capture_path))
    return _suite_report(rows, expected, "".join(captured))


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
