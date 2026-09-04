"""The ``sf-oracle/1`` wire protocol: one bounded child process per request.

An external runtime is an untrusted process. This module owns everything
about talking to it: spawning the configured command, feeding the request on
stdin, reading both output streams under hard byte caps, enforcing the
deadline even when a descendant holds the inherited pipes open, and killing
the whole session when any of that goes wrong. Every failure surfaces as
``OracleError`` so the record is dropped rather than filled in.
"""

import math
import os
import select
import signal
import subprocess
import threading
import time

PROTOCOL = "sf-oracle/1"
DEFAULT_TIMEOUT_S = 60
MAX_PROTOCOL_STDOUT_BYTES = 8 * 1024 * 1024
MAX_PROTOCOL_STDERR_BYTES = 1024 * 1024
PROTOCOL_READ_BYTES = 64 * 1024


class OracleError(RuntimeError):
    """A bound oracle could not produce an authoritative result."""


def _reject_json_constant(value):
    raise ValueError(f"non-finite JSON token {value}")


def _parse_finite_json_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


def _reject_duplicate_object_keys(pairs):
    """``object_pairs_hook`` that fails closed on an ambiguous JSON object.

    Python's default decoder applies last-key-wins to a duplicate key, but a
    bound runtime is an external process: silently picking one interpretation
    of an ambiguous response could stamp a value into provenance that another
    conforming JSON reader would have read differently.
    """
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _close_stream_quietly(stream):
    try:
        stream.close()
    except OSError:
        pass


def _close_fd_quietly(fd):
    try:
        os.close(fd)
    except OSError:
        pass


def _drop_stream_fd(stream, devnull):
    """Detach one child pipe without blocking on a concurrent read."""
    if stream is None:
        return
    try:
        fd = stream.fileno()
    except (ValueError, OSError):
        return
    if devnull is None:
        _close_fd_quietly(fd)
        return
    try:
        os.dup2(devnull, fd)
    except OSError:
        pass


class _ProtocolProcess:
    """One protocol child: bounded readers, a stdin writer, deadline reaping."""

    def __init__(self, command, payload, timeout_s, runtime):
        self._runtime = runtime
        self._payload = payload
        self._timeout_s = timeout_s
        self._deadline = time.monotonic() + float(timeout_s)
        self._chunks = {"stdout": [], "stderr": []}
        self._overflow = []
        self._io_errors = []
        self._threads = []
        self._process = self._spawn(command)

    def _spawn(self, command):
        try:
            return subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as exc:
            detail = exc.strerror or type(exc).__name__
            raise OracleError(
                f"{self._runtime}: could not execute configured command: {detail}"
            ) from exc

    def _remaining(self):
        return max(0.0, self._deadline - time.monotonic())

    def _stop_process(self):
        try:
            os.killpg(self._process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            self._kill_directly()

    def _kill_directly(self):
        try:
            self._process.kill()
        except (OSError, ProcessLookupError):
            pass

    def _close_pipes(self):
        # Closing a BufferedReader from this thread can block on a concurrent
        # read. Drop the raw fds so a descendant holding the write end cannot
        # keep us past the deadline; dup2 to /dev/null avoids fd-reuse races.
        try:
            devnull = os.open(os.devnull, os.O_RDWR)
        except OSError:
            devnull = None
        try:
            process = self._process
            for stream in (process.stdin, process.stdout, process.stderr):
                _drop_stream_fd(stream, devnull)
        finally:
            if devnull is not None:
                _close_fd_quietly(devnull)

    def _next_chunk(self, fd):
        """One bounded read; empty bytes on deadline, stream silence, or EOF."""
        wait = self._remaining()
        if wait <= 0:
            return b""
        ready, _, _ = select.select([fd], [], [], wait)
        if not ready:
            return b""
        return os.read(fd, PROTOCOL_READ_BYTES)

    def _pump_stream(self, name, fd, limit):
        total = 0
        chunk = self._next_chunk(fd)
        while chunk:
            total += len(chunk)
            if total > limit:
                self._overflow.append(name)
                self._stop_process()
                return
            self._chunks[name].append(chunk)
            chunk = self._next_chunk(fd)

    def _read_stream(self, name, stream, limit):
        try:
            self._pump_stream(name, stream.fileno(), limit)
        except OSError as exc:
            self._io_errors.append((name, exc))
            self._stop_process()
        finally:
            _close_stream_quietly(stream)

    def _write_stdin(self):
        try:
            self._process.stdin.write(self._payload)
            self._process.stdin.close()
        except BrokenPipeError:
            pass
        except OSError as exc:
            self._io_errors.append(("stdin", exc))
            self._stop_process()

    def _start_threads(self):
        prefix = f"sf-oracle-{self._runtime}-"
        process = self._process
        self._threads = [
            threading.Thread(
                target=self._read_stream,
                args=("stdout", process.stdout, MAX_PROTOCOL_STDOUT_BYTES),
                name=prefix + "stdout",
                daemon=True,
            ),
            threading.Thread(
                target=self._read_stream,
                args=("stderr", process.stderr, MAX_PROTOCOL_STDERR_BYTES),
                name=prefix + "stderr",
                daemon=True,
            ),
            threading.Thread(
                target=self._write_stdin,
                name=prefix + "stdin",
                daemon=True,
            ),
        ]
        for thread in self._threads:
            thread.start()

    def _join_readers(self, timeout):
        cutoff = time.monotonic() + timeout
        hung = False
        for thread in self._threads:
            thread.join(timeout=max(0.0, cutoff - time.monotonic()))
            if thread.is_alive():
                hung = True
        return hung

    def _reap(self):
        self._stop_process()
        self._close_pipes()
        self._join_readers(max(0.05, self._remaining()))
        try:
            self._process.wait(timeout=max(0.05, self._remaining()))
        except subprocess.TimeoutExpired:
            pass

    def _wait_for_exit(self):
        try:
            return self._process.wait(timeout=self._remaining())
        except subprocess.TimeoutExpired as exc:
            self._reap()
            raise OracleError(f"{self._runtime}: timed out after {self._timeout_s}s") from exc

    def _require_readers_finished(self):
        if self._join_readers(self._remaining()):
            self._reap()
            raise OracleError(
                f"{self._runtime}: timed out after {self._timeout_s}s "
                "waiting for inherited pipes to close"
            )

    def _require_stream_health(self):
        if self._overflow:
            stream = self._overflow[0]
            limit = MAX_PROTOCOL_STDOUT_BYTES if stream == "stdout" else MAX_PROTOCOL_STDERR_BYTES
            raise OracleError(f"{self._runtime}: {stream} exceeded the {limit}-byte protocol limit")
        if self._io_errors:
            stream, exc = self._io_errors[0]
            detail = exc.strerror or type(exc).__name__
            raise OracleError(f"{self._runtime}: {stream} I/O failed: {detail}") from exc

    def _decoded_stdout(self):
        try:
            return b"".join(self._chunks["stdout"]).decode("utf-8")
        except UnicodeError as exc:
            raise OracleError(f"{self._runtime}: response was not valid UTF-8") from exc

    def communicate(self):
        """Run the exchange to completion; ``(returncode, stdout_text)``."""
        self._start_threads()
        returncode = self._wait_for_exit()
        self._require_readers_finished()
        self._require_stream_health()
        return returncode, self._decoded_stdout()


def _run_protocol_command(command, payload, timeout_s, runtime):
    """Execute one protocol command while bounding both captured streams."""
    return _ProtocolProcess(command, payload, timeout_s, runtime).communicate()
