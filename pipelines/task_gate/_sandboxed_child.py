#!/usr/bin/env python3
"""The sandboxed gate child: runs the examples it is handed and seals what each one produced.

Standard library only; started by ``sandboxed.py`` inside the ``code_repair`` bwrap boundary as
``python3 -P -s -S -B -X utf8 _sandboxed_child.py WORKDIR FUNCTION CPU_SECONDS REPORT_FD``. The
workdir also holds ``_child.py`` (limits, loader), ``_sandboxed_record.py`` (sealed records),
``_sandbox.py`` and ``_sandbox_paths.py`` (the Landlock allowlist), all copied by the parent.

The child never judges. The parent parsed the target's doctests itself and wrote ``program.py``
with that docstring emptied; stdin carries only a per-run key and each example's source. Before
``program.py`` is read, the child consumes stdin and points fds 0 and 1 at ``os.devnull``, then
applies and attests the resource limits and the Landlock allowlist on a duplicate of the real
stdout. It then runs the examples through ``doctest`` with a checker that records what each one
produced instead of comparing it, and writes each record, sealed with the key and numbered, to
the inherited report file at the child's own offset. The expected outputs never enter this
process, so nothing here can report a pass; the parent compares (``sandboxed_judge.py``).
Failures are data, never exit codes.
"""

import doctest
import importlib.util
import json
import os
import sys

LIMITS_PREFIX = "code-repair-limits-attestation/1 "
LANDLOCK_PREFIX = "code-repair-landlock-attestation/1 "
PLAN_LIMIT = 8 << 20
WANT_SENTINEL = "\x00task-gate-want\n"
EXCEPTION_SENTINEL = "\x00task-gate-exception\n"


def _sibling(name):
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _replace_with_devnull(fd):
    sink = os.open(os.devnull, os.O_RDONLY)
    try:
        os.dup2(sink, fd)
    finally:
        os.close(sink)


def _drained(fd):
    chunks, size = [], 0
    while size <= PLAN_LIMIT:
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks)


def _read_plan(fd):
    """``(key, sources)`` read from ``fd`` to its end, or ``None``; ``fd`` is then devnull."""

    data = _drained(fd)
    _replace_with_devnull(fd)
    try:
        plan = json.loads(data)
        key, sources = bytes.fromhex(plan["key"]), plan["sources"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        return None
    return key, sources


def _attest_limits(inner, cpu_seconds, stream):
    applied = inner._limit(cpu_seconds)
    stream.write(LIMITS_PREFIX + str(applied).lower() + "\n")
    stream.flush()
    return applied


def _attest_landlock(workdir, stream):
    """Apply the allowlist and write its token; ``none`` when it cannot be applied."""

    report = {"load": {"status": "ok"}, "environment": {}}
    try:
        _sibling("_sandbox").enforce(workdir, {"require_landlock": True}, report, stream)
    except Exception:  # enforce wrote the attestation line before raising
        return False
    return True


class _Channel:
    """Seals each record with the run key and writes it at the child's own offset.

    Each write also truncates the file there, so bytes anything else wrote earlier are gone;
    bytes written after the last record make the report unreadable, never a verdict.
    """

    def __init__(self, fd, key, codec):
        self._fd, self._key, self._codec = fd, key, codec
        self._seq = self._offset = 0

    def send(self, body):
        data = self._codec.seal(self._key, self._seq, body)
        self._seq += 1
        written = 0
        while written < len(data):
            written += os.pwrite(self._fd, data[written:], self._offset + written)
        self._offset += len(data)
        os.ftruncate(self._fd, self._offset)


class _Recorder(doctest.OutputChecker):
    """A checker that records what each example produced; the comparison is the parent's."""

    def __init__(self, channel, codec):
        self._channel, self._codec = channel, codec

    def check_output(self, want, got, optionflags):
        branch = self._codec.BRANCH_OUTPUT if want == WANT_SENTINEL else self._codec.BRANCH_EXCEPTION
        self._channel.send(self._codec.observation(branch, got))
        return True


class _Ending:
    """Seals ``load_error`` for whatever ends the run before its ``end`` record.

    An ordinary exception (the program failed to load) is the result, so it stops here.
    ``SystemExit``, ``KeyboardInterrupt`` and the like are recorded, then propagate.
    """

    def __init__(self, channel, codec):
        self._channel, self._codec = channel, codec

    def __enter__(self):
        return self

    def __exit__(self, kind, _value, _traceback):
        if kind is None:
            return False
        self._channel.send(self._codec.load_error(kind.__name__))
        return issubclass(kind, Exception)


def _discard(_text):
    return None


def _test(module, function, sources):
    examples = [
        doctest.Example(source, WANT_SENTINEL, exc_msg=EXCEPTION_SENTINEL, lineno=index)
        for index, source in enumerate(sources)
    ]
    return doctest.DocTest(examples, dict(module.__dict__), function, "program.py", 0, None)


def _observe(inner, codec, channel, run):
    """Load the program, run every example, and seal one record per example, then ``end``."""

    workdir, function, sources = run
    with _Ending(channel, codec):
        module = inner._load(workdir)
        getattr(module, function)  # a missing target is a load error, as in ``_child.py``
        runner = doctest.DocTestRunner(
            checker=_Recorder(channel, codec), verbose=False, optionflags=0,
        )
        runner.run(_test(module, function, sources), out=_discard, clear_globs=False)
        channel.send(codec.end(len(sources)))


def main(argv):
    workdir, function, cpu_seconds, report_fd = argv[1], argv[2], int(argv[3]), int(argv[4])
    inner, codec = _sibling("_child"), _sibling("_sandboxed_record")
    stream = os.fdopen(os.dup(1), "w", encoding="utf-8")
    plan = _read_plan(0)
    inner._silence_stdout()
    attested = _attest_limits(inner, cpu_seconds, stream) and _attest_landlock(workdir, stream)
    stream.close()  # no descriptor onto the attested stdout survives into the program
    if attested and plan is not None:
        key, sources = plan
        _observe(inner, codec, _Channel(report_fd, key, codec), (workdir, function, sources))
    return 0


if __name__ == "__main__":
    os._exit(main(sys.argv))
