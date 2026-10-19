#!/usr/bin/env python3
"""The sandboxed gate child: ``_child.py``'s doctest logic behind Landlock and a report nonce.

Standard library only; started by ``sandboxed.py`` inside the ``code_repair`` bwrap boundary as
``python3 -P -s -S -B -X utf8 _sandboxed_child.py WORKDIR FUNCTION CPU_SECONDS REPORT_FD``. The
workdir also holds ``_child.py`` (limits, loader, doctest runner), ``_sandbox.py`` and
``_sandbox_paths.py`` (the Landlock allowlist), all copied by the parent.

Order of events, each before ``program.py`` is read: the per-run nonce is consumed from stdin;
fds 0, 1 and 2 are pointed at ``os.devnull``; resource limits and the Landlock allowlist are
applied and attested on a duplicate of the real stdout. Only then is the program imported and its doctests run, and
the single report (protocol, nonce, counts) is written to the inherited unlinked report file.
The parent accepts a report only when it echoes the nonce, which no file, argument or
environment variable ever carried, so a program that writes to the report descriptor cannot
produce one. Failures are data, never exit codes.
"""

import importlib.util
import json
import os
import sys

LIMITS_PREFIX = "code-repair-limits-attestation/1 "
LANDLOCK_PREFIX = "code-repair-landlock-attestation/1 "
NONCE_BYTES = 64


def _sibling(name):
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_nonce():
    """Consume the nonce from stdin, then replace stdin so nothing can read it again."""

    data = os.read(0, NONCE_BYTES * 2)
    sink = os.open(os.devnull, os.O_RDONLY)
    try:
        os.dup2(sink, 0)
    finally:
        os.close(sink)
    return data.decode("ascii", "replace").strip()


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


def _write_report(fd, report):
    data = json.dumps(report, sort_keys=True).encode("utf-8")
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, data)
    os.ftruncate(fd, len(data))


def _verdict(inner, workdir, function):
    try:
        module = inner._load(workdir)
        attempted, failed = inner._doctests(module, function)
    except (Exception, SystemExit, KeyboardInterrupt, GeneratorExit) as exc:  # a program may raise these
        return inner._report("load_error", detail=type(exc).__name__)
    return inner._report("ran", attempted, failed)


def main(argv):
    workdir, function, cpu_seconds, report_fd = argv[1], argv[2], int(argv[3]), int(argv[4])
    inner = _sibling("_child")
    stream = os.fdopen(os.dup(1), "w", encoding="utf-8")
    nonce = _read_nonce()
    inner._silence_stdout()
    attested = _attest_limits(inner, cpu_seconds, stream) and _attest_landlock(workdir, stream)
    stream.close()  # no descriptor onto the attested stdout survives into the program
    if attested:
        report = _verdict(inner, workdir, function)
        report["nonce"] = nonce
        _write_report(report_fd, report)
    return 0


if __name__ == "__main__":
    os._exit(main(sys.argv))
