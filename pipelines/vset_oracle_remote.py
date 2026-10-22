"""Run oracle assertions here, and candidate code in a child.

The child imports ``src/`` and answers ``import``, attribute, and call
requests. It never reports a pass. ``unittest`` in this process decides
the status, so a forged ``TestCase.run`` or an early ``_exit`` cannot
make a suite ok.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_remote")
    from .vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
    from . import vset_oracle_values as values
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_remote"
    )
    from vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
    import vset_oracle_values as values

_CHILD_TIMEOUT_S = 30.0
_INTERPRETER_FLAGS = ("-I", "-B", "-X", "utf8")
_REPLY_LIMIT = 1_000_000
_TIMEOUT_MESSAGE = "oracle runner failed: timed out"

# Passed to a fresh interpreter via -c. Nothing under the worktree is executed
# as the grader, so candidate code cannot replace this source for a later id.
_WORKER_SOURCE = textwrap.dedent(
    """\
    import base64
    import importlib
    import json
    import os
    import sys
    from datetime import date, datetime
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path

    real_out = sys.stdout
    sys.stdout = sys.stderr
    os.chdir(sys.argv[1])
    sys.path.insert(0, str(Path(sys.argv[1]) / "src"))
    objs = {}
    ids = {}
    nxt = 0


    def remember(value):
        global nxt
        key = id(value)
        if key in ids:
            return ids[key]
        oid = nxt
        nxt += 1
        ids[key] = oid
        objs[oid] = value
        return oid


    def is_exception(value):
        if not isinstance(value, type):
            return False
        try:
            return issubclass(value, Exception)
        except TypeError:
            return False


    def exc_chain(value):
        names = []
        for base in value.__mro__[1:]:
            if base is BaseException or base is object:
                break
            names.append(base.__name__)
        return names


    def describe_class(cls):
        bases = []
        for base in cls.__bases__:
            if base is object:
                continue
            bases.append(describe_class(base))
        return {"oid": remember(cls), "name": cls.__name__, "bases": bases}


    def put(value):
        if value is None:
            return {"kind": "value", "value": None}
        if isinstance(value, (bool, int, float, str)):
            return {"kind": "value", "value": value}
        if type(value) is list:
            return {"kind": "list", "items": [put(item) for item in value]}
        if type(value) is tuple:
            return {"kind": "tuple", "items": [put(item) for item in value]}
        if type(value) is dict:
            items = [[put(key), put(item)] for key, item in value.items()]
            return {"kind": "dict", "items": items}
        if type(value) is set:
            return {"kind": "set", "items": [put(item) for item in value]}
        if type(value) is frozenset:
            return {"kind": "frozenset", "items": [put(item) for item in value]}
        if type(value) is bytes or type(value) is bytearray:
            raw = bytes(value)
            return {"kind": "bytes", "data": base64.b64encode(raw).decode("ascii")}
        if isinstance(value, Decimal):
            return {"kind": "decimal", "data": str(value)}
        if isinstance(value, Fraction):
            return {"kind": "fraction", "n": value.numerator, "d": value.denominator}
        if isinstance(value, datetime):
            return {"kind": "datetime", "data": value.isoformat()}
        if isinstance(value, date):
            return {"kind": "date", "data": value.isoformat()}
        if is_exception(value):
            return {"kind": "exc_type", "name": value.__name__, "chain": exc_chain(value)}
        if isinstance(value, type):
            info = describe_class(value)
            info["kind"] = "class"
            return info
        return {"kind": "obj", "oid": remember(value), "cls": describe_class(type(value))}


    def decode(value):
        if not isinstance(value, dict):
            return value
        if "ref" in value:
            return objs[value["ref"]]
        if "seq" in value:
            items = [decode(item) for item in value["seq"]]
            if value.get("tuple"):
                return tuple(items)
            return items
        if "map" in value:
            return {decode(pair[0]): decode(pair[1]) for pair in value["map"]}
        if "set" in value:
            items = [decode(item) for item in value["set"]]
            if value.get("frozen"):
                return frozenset(items)
            return set(items)
        if "bytes" in value:
            return base64.b64decode(value["bytes"])
        if "decimal" in value:
            return Decimal(value["decimal"])
        if "fraction" in value:
            return Fraction(value["fraction"], value["d"])
        if "datetime" in value:
            return datetime.fromisoformat(value["datetime"])
        if "date" in value:
            return date.fromisoformat(value["date"])
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
            elif op == "set":
                setattr(objs[req["oid"]], req["attr"], decode(req["value"]))
                out = {"kind": "value", "value": None}
            elif op == "call":
                args = [decode(arg) for arg in req["args"]]
                kwargs = {key: decode(val) for key, val in req["kwargs"].items()}
                out = put(objs[req["oid"]](*args, **kwargs))
            else:
                out = {
                    "kind": "error",
                    "type": "RuntimeError",
                    "chain": ["Exception"],
                    "message": "bad op",
                }
        except Exception as exc:
            out = {
                "kind": "error",
                "type": type(exc).__name__,
                "chain": exc_chain(type(exc)),
                "message": str(exc),
            }
        reply(out)
    """
)


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
        return values.interpret(self, _read_reply(stdout))

    def do_import(self, name: str) -> object:
        return self.exchange({"op": "import", "name": name})

    def get(self, oid: int, attr: str) -> object:
        return self.exchange({"op": "get", "oid": oid, "attr": attr})

    def set_attr(self, oid: int, name: str, value: object) -> None:
        self.exchange(
            {"op": "set", "oid": oid, "attr": name, "value": values.encode(value)}
        )

    def call(self, oid: int, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        return self.exchange(
            {
                "op": "call",
                "oid": oid,
                "args": [values.encode(arg) for arg in args],
                "kwargs": {key: values.encode(val) for key, val in kwargs.items()},
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
    def __init__(self, client: _Client, local: set[str], src_names: frozenset[str]) -> None:
        self._client = client
        self._local = local
        self._src = src_names

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> importlib.machinery.ModuleSpec | None:
        root = fullname.split(".", 1)[0]
        if root in self._local:
            return None
        if root in self._src:
            return importlib.util.spec_from_loader(fullname, _RemoteLoader(self._client, fullname))
        if root in sys.stdlib_module_names:
            return None
        return importlib.util.spec_from_loader(fullname, _RemoteLoader(self._client, fullname))


def _read_reply(stdout: io.TextIOBase) -> object:
    line = stdout.readline(_REPLY_LIMIT)
    if not line:
        raise EOFError("oracle worker exited")
    if len(line) >= _REPLY_LIMIT:
        raise EOFError("oracle worker reply is too large")
    return json.loads(line)


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


_alarm_tripped = False


def _alarm(_signum: int, _frame: object) -> None:
    # unittest re-raises KeyboardInterrupt. Candidate replies cannot raise it.
    global _alarm_tripped
    _alarm_tripped = True
    raise KeyboardInterrupt


def _arm(seconds: float):
    previous = signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    return previous


def _disarm(previous) -> None:
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, previous)


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


def _load_saved(spec: dict[str, str], suffix: str, folder: Path) -> types.ModuleType:
    name = spec["module"] + suffix
    path = folder / f"{name}.py"
    path.write_text(spec["source"], encoding="utf-8")
    module_spec = importlib.util.spec_from_file_location(name, path)
    if module_spec is None:
        raise EOFError("cannot load suite")
    if module_spec.loader is None:
        raise EOFError("cannot load suite")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
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


def _execute(spec: dict[str, str], names: tuple[str, str], folder: Path) -> tuple[str, str]:
    suffix = f"__{names[0]}__{names[1]}"
    module = _load_saved(spec, suffix, folder)
    return _run_case(module, names)


def _materialize(sources: dict[str, str]) -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory(prefix="vset-suite-")
    root = Path(temp.name)
    for name, text in sources.items():
        (root / name).write_text(text, encoding="utf-8")
    return temp


def _stems(sources: dict[str, str]) -> set[str]:
    return {Path(name).stem for name in sources}


def _grade_open(
    proc: subprocess.Popen[str],
    spec: dict[str, str],
    names: tuple[str, str],
    bundle: tuple[dict[str, str], frozenset[str]],
) -> tuple[str, str]:
    sources, src_names = bundle
    before = set(sys.modules)
    temp = _materialize(sources)
    folder = temp.name
    finder = _Finder(_Client(proc), _stems(sources), src_names)
    sys.meta_path.insert(0, finder)
    _push_path(folder)
    try:
        return _execute(spec, names, Path(folder))
    except (Exception, SystemExit) as exc:
        return "ERROR", f"{type(exc).__name__}: {exc}"
    finally:
        _pop_path(folder)
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        _drop_new(before)
        temp.cleanup()


def grade_test(
    work: Path,
    spec: dict[str, str],
    names: tuple[str, str],
    bundle: tuple[dict[str, str], frozenset[str]],
) -> tuple[str, str]:
    """Grade one id. Candidate calls run in ``work``; assertions run here."""

    global _alarm_tripped
    _alarm_tripped = False
    values.reset_identity()
    try:
        proc = _start_child(_worker_argv(work))
    except OSError as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    previous = _arm(_CHILD_TIMEOUT_S)
    try:
        return _grade_open(proc, spec, names, bundle)
    except KeyboardInterrupt:
        if not _alarm_tripped:
            raise
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, _TIMEOUT_MESSAGE) from None
    finally:
        _disarm(previous)
        _stop(proc)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
