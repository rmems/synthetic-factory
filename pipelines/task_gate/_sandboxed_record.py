#!/usr/bin/env python3
"""Sealed records on the sandboxed gate child's report channel.

Standard library only: ``sandboxed.py`` copies this file into the child's workdir and the parent
imports it too, so both sides seal and open records with the same code. A record is one ASCII
line: the canonical JSON of ``{"payload", "mac"}``, where ``payload`` is the canonical JSON of
``{"protocol", "seq", "body"}`` and ``mac`` is its HMAC-SHA256 under the per-run key. ``seq``
numbers the records from zero, so a record cannot be dropped, repeated or moved without
``opened`` refusing it. The key reaches the child on stdin only; see ``_sandboxed_child.py``.

An observation carries the example's output as base64 of its UTF-8 bytes, so escaping cannot
inflate it. One run may record ``OUTPUT_BUDGET`` bytes of output across all its examples; the
child keeps a prefix of anything past that and marks it ``cut``, which the parent judges
``crashed`` (``output_truncated``), never ``failed``. ``REPORT_LIMIT`` bounds the honest report,
and the child raises its file-size limit to it so an honest report is never cut short.
"""

import base64
import hashlib
import hmac
import json

PROTOCOL = "task-gate-sandboxed-report/1"
KEY_BYTES = 32
OUTPUT_BUDGET = 1 << 20
MAX_EXAMPLES = 256
DETAIL_LIMIT = 64
# One record's bytes besides its output data: framing, MAC, seq, and a load_error detail whose
# every character is escaped twice (7 bytes); also the up-to-4-byte base64 padding per record.
FRAME_LIMIT = 1024


def report_limit(examples):
    """The most bytes an honest report of ``examples`` observations can hold."""

    return 4 * -(-OUTPUT_BUDGET // 3) + (examples + 2) * FRAME_LIMIT


REPORT_LIMIT = report_limit(MAX_EXAMPLES)

BRANCH_OUTPUT = "out"
BRANCH_EXCEPTION = "exc"
KIND_OBSERVED = "observed"
KIND_LOAD_ERROR = "load_error"
KIND_END = "end"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def _mac(key, payload):
    return hmac.new(key, payload.encode("ascii"), hashlib.sha256).hexdigest()


def seal(key, seq, body):
    """One record line: ``body`` at position ``seq``, authenticated with ``key``."""

    payload = _canonical({"protocol": PROTOCOL, "seq": seq, "body": body})
    return (_canonical({"payload": payload, "mac": _mac(key, payload)}) + "\n").encode("ascii")


def _unique(pairs):
    keys = [key for key, _value in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate key")
    return dict(pairs)


def _no_constant(name):
    raise ValueError(f"non-finite number {name}")


def _strict(text):
    return json.loads(text, object_pairs_hook=_unique, parse_constant=_no_constant)


def _authentic_payload(key, line):
    """The payload text of a line whose MAC verifies under ``key``; ``None`` otherwise."""

    outer = _strict(line.decode("ascii"))
    if not isinstance(outer, dict) or set(outer) != {"payload", "mac"}:
        return None
    payload, mac = outer["payload"], outer["mac"]
    if not (isinstance(payload, str) and isinstance(mac, str)):
        return None
    if not (payload.isascii() and mac.isascii()):
        return None
    return payload if hmac.compare_digest(mac.encode("ascii"), _mac(key, payload).encode("ascii")) else None


def opened(key, line, seq):
    """The body of ``line`` when it is the record sealed with ``key`` at ``seq``; else ``None``.

    Never raises on hostile bytes: anything that is not exactly such a record is ``None``.
    """

    try:
        payload = _authentic_payload(key, line)
        inner = None if payload is None else _strict(payload)
    except (ValueError, RecursionError):  # UnicodeDecodeError is a ValueError
        return None
    if not isinstance(inner, dict) or set(inner) != {"protocol", "seq", "body"}:
        return None
    header = (inner["protocol"], type(inner["seq"]), inner["seq"])
    return inner["body"] if header == (PROTOCOL, int, seq) else None


def observation(branch, data, cut=False, displayed=""):
    """What one example produced (UTF-8 bytes of its output or exception line); ``cut``
    when ``data`` is only a prefix because the run's output budget ran out.

    ``displayed`` is the repr of the value the example displayed, or empty when it
    displayed nothing. The parent uses it to tell extra stdout from a printed line.
    """

    return {"kind": KIND_OBSERVED, "branch": branch,
            "data": base64.b64encode(data).decode("ascii"), "cut": cut, "displayed": displayed}


def load_error(detail):
    """The run ended before every example was recorded; ``detail`` names what ended it."""

    return {"kind": KIND_LOAD_ERROR, "detail": detail[:DETAIL_LIMIT]}


def end(count):
    """Every example ran; ``count`` is how many were recorded."""

    return {"kind": KIND_END, "count": count}
