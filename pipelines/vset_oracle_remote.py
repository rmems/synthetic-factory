"""Run oracle assertions here, and candidate code in a child.

The child imports ``src/`` and answers ``import``, attribute, and call
requests. It never reports a pass. ``unittest`` in this process decides
the status, so a forged ``TestCase.run`` or an early ``_exit`` cannot
make a suite ok.
"""

from __future__ import annotations

import builtins
import importlib.util
import io
import json
import os
import signal
import subprocess  # nosec B404
import sys
import textwrap
import types
import unittest
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_remote")
    from .vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_remote"
    )
    from vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError

_CHILD_TIMEOUT_S = 30.0
_INTERPRETER_FLAGS = ("-I", "-B", "-X", "utf8")
_REPLY_LIMIT = 1_000_000
_TIMEOUT_MESSAGE = "oracle runner failed: timed out"

# Passed to a fresh interpreter via -c. Nothing under the worktree is executed
# as the grader, so candidate code cannot replace this source for a later id.
_WORKER_SOURCE = textwrap.dedent(
    """\
    import importlib
    import json
    import os
    import sys
    from pathlib import Path

    real_out = sys.stdout
    sys.stdout = sys.stderr
    os.chdir(sys.argv[1])
    sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
    objs = {}
    nxt = 0


    def put(value):
        global nxt
        if value is None:
            return {"kind": "value", "value": None}
        if isinstance(value, (bool, int, float, str)):
            return {"kind": "value", "value": value}
        oid = nxt
        nxt += 1
        objs[oid] = value
        return {"kind": "oid", "oid": oid}


    def decode(value):
        if isinstance(value, dict):
            return objs[value["oid"]]
        return value


    def reply(payload):
        real_out.write(json.dumps(payload) + "\\n")
        real_out.flush()


    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            op = req["op"]
            if op == "import":
                out = put(importlib.import_module(req["name"]))
            elif op == "get":
                out = put(getattr(objs[req["oid"]], req["attr"]))
            elif op == "call":
                args = [decode(arg) for arg in req["args"]]
                kwargs = {key: decode(val) for key, val in req["kwargs"].items()}
                out = put(objs[req["oid"]](*args, **kwargs))
            else:
                out = {"kind": "error", "type": "RuntimeError", "message": "bad op"}
        except Exception as exc:
            out = {"kind": "error", "type": type(exc).__name__, "message": str(exc)}
        reply(out)
    """
)


class _Proxy:
    def __init__(self, client: _Client, oid: int) -> None:
        object.__setattr__(self, "client", client)
        object.__setattr__(self, "oid", oid)

    def __call__(self, *args: object, **kwargs: object) -> object:
        return self.client.call(self.oid, args, kwargs)

    def __getattr__(self, name: str) -> object:
        return self.client.get(self.oid, name)


class _Client:
    def __init__(self, proc: subprocess.Popen[str]) -> None:
        self.proc = proc

    def exchange(self, payload: dict[str, object]) -> object:
        if self.proc.poll() is not None:
            raise EOFError("oracle worker exited")
        stdin = self.proc.stdin
        stdout = self.proc.stdout
        if stdin is None:
            raise EOFError("oracle worker exited")
        if stdout is None:
            raise EOFError("oracle worker exited")
        stdin.write(json.dumps(payload) + "\n")
        stdin.flush()
        return _interpret(self, _read_reply(stdout))

    def do_import(self, name: str) -> _Proxy:
        value = self.exchange({"op": "import", "name": name})
        if isinstance(value, _Proxy):
            return value
        raise EOFError("oracle worker import failed")

    def get(self, oid: int, attr: str) -> object:
        return self.exchange({"op": "get", "oid": oid, "attr": attr})

    def call(self, oid: int, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        return self.exchange(
            {
                "op": "call",
                "oid": oid,
                "args": [_encode(arg) for arg in args],
                "kwargs": {key: _encode(val) for key, val in kwargs.items()},
            }
        )


class _RemoteLoader:
    def __init__(self, client: _Client, fullname: str) -> None:
        self._client = client
        self._fullname = fullname

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> None:
        return None

    def exec_module(self, module: types.ModuleType) -> None:
        proxy = self._client.do_import(self._fullname)
        oid = proxy.oid
        client = self._client

        def missing(name: str, _oid: int = oid, _client: _Client = client) -> object:
            return _client.get(_oid, name)

        module.__getattr__ = missing  # type: ignore[method-assign]


class _Finder:
    def __init__(self, client: _Client, local: set[str]) -> None:
        self._client = client
        self._local = local

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> importlib.machinery.ModuleSpec | None:
        root = fullname.split(".", 1)[0]
        if root in sys.stdlib_module_names:
            return None
        if root in self._local:
            return None
        return importlib.util.spec_from_loader(fullname, _RemoteLoader(self._client, fullname))


def _read_reply(stdout: io.TextIOBase) -> object:
    line = stdout.readline(_REPLY_LIMIT)
    if not line:
        raise EOFError("oracle worker exited")
    if len(line) >= _REPLY_LIMIT:
        raise EOFError("oracle worker reply is too large")
    return json.loads(line)


def _encode(value: object) -> object:
    if isinstance(value, _Proxy):
        return {"oid": value.oid}
    return value


def _raise_remote(name: str, message: str) -> None:
    exc_type = getattr(builtins, name, None)
    if isinstance(exc_type, type):
        if issubclass(exc_type, BaseException):
            raise exc_type(message)
    raise RuntimeError(message)


def _interpret(client: _Client, payload: object) -> object:
    if not isinstance(payload, dict):
        raise EOFError("bad worker reply")
    kind = payload.get("kind")
    if kind == "value":
        return payload.get("value")
    if kind == "oid":
        return _Proxy(client, int(payload["oid"]))
    if kind == "error":
        _raise_remote(str(payload.get("type")), str(payload.get("message")))
    raise EOFError("bad worker reply")


def _worker_argv(work: Path) -> list[str]:
    return [sys.executable, *_INTERPRETER_FLAGS, "-c", _WORKER_SOURCE, str(work)]


def _start_child(argv: list[str]) -> subprocess.Popen[str]:
    # The program text is the parent constant above, not a worktree path.
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
    return subprocess.Popen(  # nosec B603
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )


def _kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        proc.kill()


def _stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is None:
        _kill_group(proc)
    if proc.stdin is not None:
        proc.stdin.close()
    if proc.stdout is not None:
        proc.stdout.close()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _alarm(_signum: int, _frame: object) -> None:
    # unittest's outcome handler re-raises KeyboardInterrupt and records
    # every other BaseException as a test error. This is the one that escapes.
    raise KeyboardInterrupt(_TIMEOUT_MESSAGE)


def _arm(seconds: float):
    previous = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    return previous


def _disarm(previous) -> None:
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, previous)


def _local_names(folder: Path) -> set[str]:
    return {item.stem for item in folder.glob("*.py")}


def _push_path(folder: str) -> None:
    sys.path.insert(0, folder)


def _pop_path(folder: str) -> None:
    if not sys.path:
        return
    if sys.path[0] != folder:
        return
    del sys.path[0]


def _drop_new(before: set[str]) -> None:
    for name in list(sys.modules):
        if name not in before:
            sys.modules.pop(name, None)


def _load_saved(spec: dict[str, str], suffix: str) -> types.ModuleType:
    name = spec["module"] + suffix
    module = types.ModuleType(name)
    module.__file__ = spec["path"]
    module.__package__ = None
    sys.modules[name] = module
    # Restored suite text captured before candidate code ran.
    code = compile(spec["source"], spec["path"], "exec")
    exec(code, module.__dict__)  # nosec B102
    return module


def _problem_status(result: unittest.TestResult) -> str:
    if result.errors:
        return "ERROR"
    if result.failures:
        return "FAIL"
    if result.unexpectedSuccesses:
        return "unexpectedSuccess"
    return ""


def _status(result: unittest.TestResult) -> str:
    problem = _problem_status(result)
    if problem:
        return problem
    if result.expectedFailures:
        return "expectedFailure"
    if result.skipped:
        return "SKIP"
    if result.testsRun:
        return "ok"
    return "ERROR"


def _run_case(module: types.ModuleType, names: tuple[str, str]) -> tuple[str, str]:
    class_name, method_name = names
    case = getattr(module, class_name)
    suite = unittest.TestSuite([case(method_name)])
    buffer = io.StringIO()
    result = unittest.TestResult()
    previous = sys.stdout
    sys.stdout = buffer
    try:
        suite.run(result)
    finally:
        sys.stdout = previous
    return _status(result), buffer.getvalue()[-4000:]


def _execute(spec: dict[str, str], names: tuple[str, str]) -> tuple[str, str]:
    suffix = f"__{names[0]}__{names[1]}"
    module = _load_saved(spec, suffix)
    return _run_case(module, names)


def _grade_open(
    proc: subprocess.Popen[str], spec: dict[str, str], names: tuple[str, str]
) -> tuple[str, str]:
    before = set(sys.modules)
    folder = str(Path(spec["path"]).parent)
    finder = _Finder(_Client(proc), _local_names(Path(spec["path"])))
    sys.meta_path.insert(0, finder)
    _push_path(folder)
    try:
        return _execute(spec, names)
    except (Exception, SystemExit) as exc:
        return "ERROR", f"{type(exc).__name__}: {exc}"
    finally:
        _pop_path(folder)
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        _drop_new(before)


def grade_test(
    work: Path, spec: dict[str, str], names: tuple[str, str]
) -> tuple[str, str]:
    """Grade one id. Candidate calls run in ``work``; assertions run here."""

    try:
        proc = _start_child(_worker_argv(work))
    except OSError as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    previous = _arm(_CHILD_TIMEOUT_S)
    try:
        return _grade_open(proc, spec, names)
    except KeyboardInterrupt as exc:
        if str(exc) != _TIMEOUT_MESSAGE:
            raise
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, _TIMEOUT_MESSAGE) from None
    finally:
        _disarm(previous)
        _stop(proc)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
