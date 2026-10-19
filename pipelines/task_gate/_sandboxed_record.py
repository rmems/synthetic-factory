#!/usr/bin/env python3
"""Sealed records on the sandboxed gate child's report channel.

Standard library only: ``sandboxed.py`` copies this file into the child's workdir and the parent
imports it too, so both sides seal and open records with the same code. A record is one ASCII
line: the canonical JSON of ``{"payload", "mac"}``, where ``payload`` is the canonical JSON of
``{"protocol", "seq", "body"}`` and ``mac`` is its HMAC-SHA256 under the per-run key. ``seq``
numbers the records from zero, so a record cannot be dropped, repeated or moved without
``opened`` refusing it. The key reaches the child on stdin only; see ``_sandboxed_child.py``.
"""

import hashlib
import hmac
import json

PROTOCOL = "task-gate-sandboxed-report/1"
KEY_BYTES = 32
TEXT_LIMIT = 4096
DETAIL_LIMIT = 200
# Worst case per record: every text character escaped to a 12-byte surrogate pair in the payload,
# then every payload byte escaped again in the outer line, plus fixed framing.
RECORD_LIMIT = 24 * TEXT_LIMIT + 1024

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
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if not isinstance(inner, dict) or set(inner) != {"protocol", "seq", "body"}:
        return None
    if inner["protocol"] != PROTOCOL or type(inner["seq"]) is not int or inner["seq"] != seq:
        return None
    return inner["body"]


def observation(branch, text):
    """What one example produced: its output, or the exception line ``doctest`` compares."""

    return {"kind": KIND_OBSERVED, "branch": branch, "text": text[:TEXT_LIMIT],
            "cut": len(text) > TEXT_LIMIT}


def load_error(detail):
    """The run ended before every example was recorded; ``detail`` names what ended it."""

    return {"kind": KIND_LOAD_ERROR, "detail": detail[:DETAIL_LIMIT]}


def end(count):
    """Every example ran; ``count`` is how many were recorded."""

    return {"kind": KIND_END, "count": count}
