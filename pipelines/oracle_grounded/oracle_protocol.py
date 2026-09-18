"""Bounded process transport for the sf-oracle/1 protocol."""

import os
import select
import signal
import subprocess  # nosec B404 -- argv comes from an explicit runtime binding
import threading
import time

from .oracle_core import (
    MAX_PROTOCOL_STDERR_BYTES,
    MAX_PROTOCOL_STDOUT_BYTES,
    PROTOCOL_READ_BYTES,
    OracleError,
)


class _ProtocolSession:
    def __init__(self, command, payload, timeout_s, runtime):
        self.payload = payload
        self.timeout_s = timeout_s
        self.runtime = runtime
        self.deadline = time.monotonic() + float(timeout_s)
        try:
            self.process = subprocess.Popen(  # nosec B603 -- explicit binding, never a shell
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as exc:
            detail = exc.strerror or type(exc).__name__
            raise OracleError(
                f"{runtime}: could not execute configured command: {detail}"
            ) from exc
        self.chunks = {"stdout": [], "stderr": []}
        self.overflow = []
        self.io_errors = []
        self.timed_out_streams = []
        self.threads = []
        self.process_lock = threading.Lock()

    def remaining(self):
        return max(0.0, self.deadline - time.monotonic())

    def stop_process(self):
        with self.process_lock:
            if self.process.poll() is not None:
                return
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except OSError:
                try:
                    self.process.kill()
                except OSError:
                    pass

    def wait_process(self, timeout):
        """Wait in short locked slices so stream threads can still stop the process."""
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            with self.process_lock:
                try:
                    return self.process.wait(timeout=min(0.05, remaining))
                except subprocess.TimeoutExpired:
                    if remaining <= 0.0:
                        raise

    def close_pipes(self):
        try:
            devnull = os.open(os.devnull, os.O_RDWR)
        except OSError:
            devnull = None
        try:
            self._redirect_pipes(devnull)
        finally:
            if devnull is not None:
                try:
                    os.close(devnull)
                except OSError:
                    pass

    def _redirect_pipes(self, devnull):
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is None:
                continue
            try:
                descriptor = stream.fileno()
            except (ValueError, OSError):
                continue
            try:
                os.dup2(devnull, descriptor) if devnull is not None else os.close(descriptor)
            except OSError:
                pass

    def read_stream(self, name, stream, limit):
        total = 0
        try:
            descriptor = stream.fileno()
            while self._stream_has_time(name):
                ready, _, _ = select.select([descriptor], [], [], self.remaining())
                if not ready:
                    self.timed_out_streams.append(name)
                    break
                chunk = self._read_chunk(name, descriptor)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    self.overflow.append(name)
                    self.stop_process()
                    break
                self.chunks[name].append(chunk)
        except OSError as exc:
            self.io_errors.append((name, exc))
            self.stop_process()
        finally:
            try:
                stream.close()
            except OSError:
                pass

    def _stream_has_time(self, name):
        if self.remaining() > 0:
            return True
        self.timed_out_streams.append(name)
        return False

    def _read_chunk(self, name, descriptor):
        try:
            return os.read(descriptor, PROTOCOL_READ_BYTES)
        except OSError as exc:
            self.io_errors.append((name, exc))
            self.stop_process()
            return b""

    def write_stdin(self):
        try:
            self.process.stdin.write(self.payload)
            self.process.stdin.close()
        except BrokenPipeError:
            pass
        except OSError as exc:
            self.io_errors.append(("stdin", exc))
            self.stop_process()

    def start_threads(self):
        prefix = f"sf-oracle-{self.runtime}-"
        self.threads = [
            threading.Thread(
                target=self.read_stream,
                args=("stdout", self.process.stdout, MAX_PROTOCOL_STDOUT_BYTES),
                name=prefix + "stdout",
                daemon=True,
            ),
            threading.Thread(
                target=self.read_stream,
                args=("stderr", self.process.stderr, MAX_PROTOCOL_STDERR_BYTES),
                name=prefix + "stderr",
                daemon=True,
            ),
            threading.Thread(target=self.write_stdin, name=prefix + "stdin", daemon=True),
        ]
        for thread in self.threads:
            thread.start()

    def join_readers(self, timeout):
        cutoff = time.monotonic() + timeout
        for thread in self.threads:
            thread.join(timeout=max(0.0, cutoff - time.monotonic()))
        return any(thread.is_alive() for thread in self.threads)

    def reap(self):
        self.stop_process()
        self.close_pipes()
        self.join_readers(max(0.05, self.remaining()))
        try:
            self.wait_process(timeout=max(0.05, self.remaining()))
        except subprocess.TimeoutExpired:
            pass

    def run(self):
        self.start_threads()
        try:
            returncode = self.wait_process(timeout=self.remaining())
        except subprocess.TimeoutExpired as exc:
            self.reap()
            raise OracleError(
                f"{self.runtime}: timed out after {self.timeout_s}s"
            ) from exc
        if self.join_readers(max(0.05, self.remaining())) or self.timed_out_streams:
            self.reap()
            raise OracleError(
                f"{self.runtime}: timed out after {self.timeout_s}s "
                "waiting for inherited pipes to close"
            )
        self._raise_stream_error()
        try:
            stdout = b"".join(self.chunks["stdout"]).decode("utf-8")
        except UnicodeError as exc:
            raise OracleError(f"{self.runtime}: response was not valid UTF-8") from exc
        return returncode, stdout

    def _raise_stream_error(self):
        if self.overflow:
            stream = self.overflow[0]
            limit = (
                MAX_PROTOCOL_STDOUT_BYTES
                if stream == "stdout"
                else MAX_PROTOCOL_STDERR_BYTES
            )
            raise OracleError(
                f"{self.runtime}: {stream} exceeded the {limit}-byte protocol limit"
            )
        if self.io_errors:
            stream, exc = self.io_errors[0]
            detail = exc.strerror or type(exc).__name__
            raise OracleError(f"{self.runtime}: {stream} I/O failed: {detail}") from exc


def _run_protocol_command(command, payload, timeout_s, runtime):
    """Execute one protocol command while bounding both captured streams."""
    return _ProtocolSession(command, payload, timeout_s, runtime).run()
