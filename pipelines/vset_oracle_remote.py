"""Run oracle assertions here, and candidate code in a child.

The child imports ``src/`` and answers ``import``, attribute, and call
requests. It never reports a pass. ``unittest`` in this process decides
the status, so a forged ``TestCase.run`` or an early ``_exit`` cannot
make a suite ok.
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import io
import os
import signal
import subprocess  # nosec B404
import sys
import tempfile
import types
import unittest
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_remote")
    from .vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
    from .vset_oracle_codec import encode as _encode
    from . import vset_oracle_bridge as bridge
    from . import vset_oracle_pathguard as pathguard
    from . import vset_oracle_values as values
    from .vset_oracle_status import case_status as _case_status
    from .vset_oracle_status import status as _whole_status
    from .vset_oracle_worker import WORKER_SOURCE as _WORKER_SOURCE
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_remote"
    )
    from vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
    from vset_oracle_codec import encode as _encode
    import vset_oracle_bridge as bridge
    import vset_oracle_pathguard as pathguard
    import vset_oracle_values as values
    from vset_oracle_status import case_status as _case_status
    from vset_oracle_status import status as _whole_status
    from vset_oracle_worker import WORKER_SOURCE as _WORKER_SOURCE

def _status(result: unittest.TestResult) -> str:
    return _whole_status(result)


_CHILD_TIMEOUT_S = 30.0
_INTERPRETER_FLAGS = ("-I", "-B", "-X", "utf8")
_TIMEOUT_MESSAGE = "oracle runner failed: timed out"

# Passed to a fresh interpreter via -c. Nothing under the worktree is executed
# as the grader, so candidate code cannot replace this source for a later id.


class _Client:
    def __init__(self, proc: subprocess.Popen[str]) -> None:
        self.proc = proc

    def exchange(self, payload: dict[str, object]) -> object:
        return bridge.exchange(self, payload)

    def do_import(self, name: str) -> object:
        return self.exchange({"op": "import", "name": name})

    def get(self, oid: int, attr: str) -> object:
        return self.exchange({"op": "get", "oid": oid, "attr": attr})

    def set_attr(self, oid: int, name: str, value: object) -> None:
        self.exchange(
            {"op": "set", "oid": oid, "attr": name, "value": _encode(value)}
        )

    def delete_attr(self, oid: int, name: str) -> None:
        self.exchange({"op": "del", "oid": oid, "attr": name})

    def patch_module(self, name: str, attr: str, value: object, token: int) -> None:
        self.exchange(
            {
                "op": "patch",
                "name": name,
                "attr": attr,
                "value": _encode(value),
                "token": token,
            }
        )

    def unpatch_module(self, token: int) -> None:
        self.exchange({"op": "unpatch", "token": token})

    def shift_environ(self, changed: dict[str, str], dropped: list[str]) -> None:
        self.exchange({"op": "environ", "set": changed, "drop": dropped})

    def undo_environ(self) -> None:
        self.exchange({"op": "environ", "undo": True})

    def call(self, oid: int, args: tuple[object, ...], kwargs: dict[str, object]) -> object:
        return self.exchange(
            {
                "op": "call",
                "oid": oid,
                "args": [_encode(arg) for arg in args],
                "kwargs": {key: _encode(val) for key, val in kwargs.items()},
            }
        )

    def materialize(self, oid: int) -> object:
        return self.exchange({"op": "view", "oid": oid})


class _RemoteLoader:
    def __init__(self, client: _Client, fullname: str) -> None:
        self._client = client
        self._fullname = fullname

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> types.ModuleType:
        return bridge.remote_module(spec, self._client)

    def exec_module(self, module: types.ModuleType) -> None:
        proxy = self._client.do_import(self._fullname)
        module._vset_oid = proxy.oid  # type: ignore[attr-defined]
        oid = proxy.oid
        client = self._client

        def missing(name: str, _oid: int = oid, _client: _Client = client) -> object:
            return _client.get(_oid, name)

        module.__getattr__ = missing  # type: ignore[method-assign]
        module._vset_live = True  # type: ignore[attr-defined]


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


def _worker_argv(work: Path) -> list[str]:
    return [sys.executable, *_INTERPRETER_FLAGS, "-c", _WORKER_SOURCE, str(work)]


def _child_environment() -> dict[str, str]:
    """Keep the worker off the operator environment.

    ``-I`` does not drop ordinary variables, and candidate ``src/`` can read
    them. Pass only what the interpreter needs to start.
    """

    env = {"PATH": os.environ.get("PATH", os.defpath)}
    if os.name == "nt" and "SYSTEMROOT" in os.environ:
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


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
        env=_child_environment(),
    )


def _kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        proc.kill()


def _close(stream: object) -> None:
    if stream is None:
        return
    try:
        stream.close()  # type: ignore[attr-defined]
    except OSError:
        return


def _stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is None:
        _kill_group(proc)
    _close(proc.stdin)
    _close(proc.stdout)
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


class _FrozenLoader(importlib.abc.ExecutionLoader):
    """Load suite text from memory so a leftover process cannot plant bytecode."""

    def __init__(self, source: str, origin: str) -> None:
        self._source = source
        self._origin = origin

    def get_source(self, fullname: str) -> str:
        return self._source

    def get_filename(self, fullname: str) -> str:
        return self._origin


def _load_saved(spec: dict[str, str], suffix: str, folder: Path) -> types.ModuleType:
    name = spec["module"] + suffix
    origin = str(Path(spec["relative"]).resolve())
    loader = _FrozenLoader(spec["source"], origin)
    module_spec = importlib.util.spec_from_loader(name, loader, origin=origin)
    if module_spec is None:
        raise EOFError("cannot load suite")
    module = importlib.util.module_from_spec(module_spec)
    module.__file__ = origin
    sys.modules[name] = module
    if module_spec.loader is None:
        raise EOFError("cannot load suite")
    module_spec.loader.exec_module(module)
    return module


def _run_cases(module: types.ModuleType, cases: list[tuple[str, str]]) -> list[str]:
    tests = [getattr(module, class_name)(method_name) for class_name, method_name in cases]
    suite = unittest.TestSuite(tests)
    result = unittest.TestResult()
    suite.run(result)
    return [_case_status(result, test) for test in tests]


def _execute(
    spec: dict[str, str], cases: list[tuple[str, str]], folder: Path
) -> tuple[list[str], str]:
    suffix = "__" + "__".join(name for case in cases for name in case)
    buffer = io.StringIO()
    previous_out = sys.stdout
    previous_err = sys.stderr
    sys.stdout = buffer
    sys.stderr = buffer
    try:
        module = _load_saved(spec, suffix, folder)
        statuses = _run_cases(module, cases)
    finally:
        sys.stdout = previous_out
        sys.stderr = previous_err
    return statuses, buffer.getvalue()[-4000:]


def _materialize(sources: dict[str, str]) -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory(prefix="vset-suite-")
    root = Path(temp.name)
    for name, text in sources.items():
        (root / name).write_text(text, encoding="utf-8")
    return temp


def _stems(sources: dict[str, str]) -> set[str]:
    return {Path(name).stem for name in sources}


def _hide_shadowed(names: frozenset[str]) -> dict[str, object]:
    saved: dict[str, object] = {}
    for key in list(sys.modules):
        root = key.split(".", 1)[0]
        if root not in names:
            continue
        saved[key] = sys.modules.pop(key)
    return saved


def _restore_shadowed(saved: dict[str, object]) -> None:
    sys.modules.update(saved)


def _grade_open(
    proc: subprocess.Popen[str],
    spec: dict[str, str],
    cases: list[tuple[str, str]],
    bundle: tuple[dict[str, str], frozenset[str]],
) -> tuple[list[str], str]:
    sources, src_names = bundle
    before = set(sys.modules)
    hidden = _hide_shadowed(src_names)
    temp = _materialize(sources)
    folder = temp.name
    client = _Client(proc)
    finder = _Finder(client, _stems(sources), src_names)
    sys.meta_path.insert(0, finder)
    _push_path(folder)
    seen = pathguard.snapshot()
    guard = pathguard.PathGuard(seen)
    sys.meta_path.insert(1, guard)
    hooks = None
    try:
        hooks = bridge.install_patches(client)
        statuses, text = _execute(spec, cases, Path(folder))
        if pathguard.drift(seen):
            return ["ERROR"] * len(cases), "oracle import path changed"
        return statuses, text
    except (Exception, SystemExit) as exc:
        return ["ERROR"] * len(cases), f"{type(exc).__name__}: {exc}"
    finally:
        if hooks is not None:
            bridge.restore_patches(hooks)
        _pop_path(folder)
        if guard in sys.meta_path:
            sys.meta_path.remove(guard)
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        _drop_new(before)
        _restore_shadowed(hidden)
        temp.cleanup()


def grade_cases(
    work: Path,
    spec: dict[str, str],
    cases: list[tuple[str, str]],
    bundle: tuple[dict[str, str], frozenset[str]],
) -> tuple[list[str], str]:
    """Grade one module load. ``setUpClass`` runs once for its methods."""

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
    previous_cwd = Path.cwd()
    os.chdir(work)
    try:
        return _grade_open(proc, spec, cases, bundle)
    except KeyboardInterrupt:
        if not _alarm_tripped:
            raise
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, _TIMEOUT_MESSAGE) from None
    finally:
        os.chdir(previous_cwd)
        _disarm(previous)
        _stop(proc)


def grade_test(
    work: Path,
    spec: dict[str, str],
    names: tuple[str, str],
    bundle: tuple[dict[str, str], frozenset[str]],
) -> tuple[str, str]:
    """Grade one id. Candidate calls run in ``work``; assertions run here."""

    statuses, text = grade_cases(work, spec, [names], bundle)
    return statuses[0], text


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
