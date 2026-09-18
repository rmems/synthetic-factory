#!/usr/bin/env python3
"""Batch-scoped isolated replay with authenticated files and bounded JSON frames."""

from __future__ import annotations

from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_simulator_process")
    from .curate_identity_json import IdentityCurationError
    from .curate_identity_registry_sources import simulator_source_snapshot
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_simulator_process"
    )
    from curate_identity_json import IdentityCurationError
    from curate_identity_registry_sources import simulator_source_snapshot

_WORKER = "pipelines/curate_identity_simulator_worker.py"
_MAX_RESULT_BYTES = 1_048_576
_MAX_REQUEST_BYTES = 4096
_REPLAY_TIMEOUT = 60
_SESSION = ContextVar("simulator_replay_session", default=None)


def _materialize(root, snapshot):
    for relative, payload in snapshot.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def _validate_coordinate(seed, index):
    if type(seed) is not int or type(index) is not int:
        raise IdentityCurationError("simulator coordinates must be integers")
    if not 0 <= seed < 2**64 or not 0 <= index < 100000:
        raise IdentityCurationError("simulator coordinate exceeds the reviewed producer domain")


def _request(coordinates):
    seed, index, stamp = coordinates
    _validate_coordinate(seed, index)
    if not isinstance(stamp, str):
        raise IdentityCurationError("simulator timestamp must be text")
    payload = (json.dumps(coordinates, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(payload) > _MAX_REQUEST_BYTES:
        raise IdentityCurationError("simulator replay request exceeds its bound")
    return payload


def _wait_readable(ready, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not ready.select(remaining):
        raise IdentityCurationError("isolated fault-recovery replay timed out")


def _read_frame(stream):
    deadline = time.monotonic() + _REPLAY_TIMEOUT
    payload = bytearray()
    with selectors.DefaultSelector() as ready:
        ready.register(stream, selectors.EVENT_READ)
        while not payload.endswith(b"\n"):
            _wait_readable(ready, deadline)
            chunk = os.read(stream.fileno(), min(65536, _MAX_RESULT_BYTES + 1 - len(payload)))
            if not chunk:
                raise IdentityCurationError("isolated fault-recovery replay refused")
            payload.extend(chunk)
            if len(payload) > _MAX_RESULT_BYTES:
                raise IdentityCurationError("isolated fault-recovery replay result exceeds its bound")
    return json.loads(payload)


def _stop(process):
    """No unbounded wait, including cancellation or failed protocol parsing."""
    process.stdin.close()
    process.stdout.close()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class _ReplaySession:
    """A lazy worker and private source snapshot owned by one synchronous batch."""

    def __init__(self, resources):
        self.resources = resources
        self.process = None
        self.failed = False

    def _launch(self):
        snapshot = simulator_source_snapshot()
        root = Path(self.resources.enter_context(tempfile.TemporaryDirectory(prefix="simulator-replay-")))
        _materialize(root, snapshot)
        command = [sys.executable, "-I", str(root / _WORKER), str(root / "pipelines")]
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=0, cwd=root, env={"TMPDIR": str(root)},
        )
        self.resources.callback(_stop, process)
        self.process = process

    def replay(self, payload):
        if self.failed:
            raise IdentityCurationError("isolated fault-recovery replay session has failed")
        try:
            if self.process is None:
                self._launch()
            self.process.stdin.write(payload)
            return _read_frame(self.process.stdout)
        except BaseException:
            self.failed = True
            self.resources.close()
            raise


@contextmanager
def replay_session():
    """Fresh authority per batch; ContextVar state is restored on every exit."""
    with ExitStack() as resources:
        token = _SESSION.set(_ReplaySession(resources))
        try:
            yield
        finally:
            _SESSION.reset(token)


def replay_coordinate(coordinates):
    payload = _request(coordinates)
    try:
        session = _SESSION.get()
        if session is not None:
            return session.replay(payload)
        with replay_session():
            return _SESSION.get().replay(payload)
    except (OSError, ValueError) as exc:
        raise IdentityCurationError(f"isolated fault-recovery replay failed: {exc}") from exc


if __package__:
    _expose_package_sibling(__name__)
