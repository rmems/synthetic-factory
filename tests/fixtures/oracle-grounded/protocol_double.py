#!/usr/bin/env python3
"""A test double for the ``sf-oracle/1`` external oracle protocol.

This exists to prove the oracle boundary is wired, not to model anything. It
is NOT a neuromorphic simulator and its numbers are not measurements: every
response is tagged ``protocol_double: true`` so a record built from it could
never be mistaken for data. Records produced with this double are used only
inside unit tests and are never written into a dataset directory.

Modes, selected by argv[1] (default ``ok``):

  ok          a well-formed response
  badjson     stdout that is not JSON
  wrongproto  a response with the wrong protocol string
  noversion   a response missing runtime_version
  unknowncommit a response whose runtime_commit is unresolved
  badcommit   a response whose runtime_commit is not hexadecimal
  empty       a response whose measurement is empty
  emptyunits  a response whose units mapping is empty
  nan         a response containing JSON NaN
  infinity    a response containing JSON Infinity
  overflow    a response containing the finite-looking overflow literal 1e309
  dupkey      a response with runtime_version repeated as a duplicate JSON key
  stdout_flood stdout larger than the protocol capture limit
  stderr_flood stderr larger than the protocol capture limit
  fail        exit nonzero
"""

import json
import sys


def _fail(_response):
    print("protocol double asked to fail", file=sys.stderr)
    return 3


def _badjson(_response):
    sys.stdout.write("this is not json")
    return 0


def _stdout_flood(_response):
    sys.stdout.write("x" * (9 * 1024 * 1024))
    return 0


def _stderr_flood(_response):
    sys.stderr.write("x" * (2 * 1024 * 1024))
    return 3


# Modes that answer (or die) before the request is even parsed.
_EARLY_MODES = {
    "fail": _fail,
    "badjson": _badjson,
    "stdout_flood": _stdout_flood,
    "stderr_flood": _stderr_flood,
}


def _base_response(request):
    return {
        "protocol": "sf-oracle/1",
        "runtime_version": "0.0.0-double",
        "runtime_commit": "d0b1e00" + "0" * 33,
        "measured": {
            "protocol_double": True,
            "echoed_family": request.get("family"),
            "echoed_request_keys": sorted(request.get("request", {})),
        },
        "units": {"protocol_double": "not a measurement"},
    }


# Modes that break exactly one contractual field of a well-formed response.
_TWEAKS = {
    "wrongproto": lambda response: response.__setitem__("protocol", "sf-oracle/999"),
    "noversion": lambda response: response.pop("runtime_version"),
    "empty": lambda response: response.__setitem__("measured", {}),
    "emptyunits": lambda response: response.__setitem__("units", {}),
    "unknowncommit": lambda response: response.__setitem__("runtime_commit", "unknown"),
    "badcommit": lambda response: response.__setitem__(
        "runtime_commit", "not-a-source-revision"
    ),
    "nan": lambda response: response["measured"].__setitem__("nonfinite", float("nan")),
    "infinity": lambda response: response["measured"].__setitem__(
        "nonfinite", float("inf")
    ),
    "overflow": lambda response: response["measured"].__setitem__(
        "nonfinite", "OVERFLOW_LITERAL"
    ),
}


def _serialize(response, mode):
    output = json.dumps(response, sort_keys=True)
    if mode == "overflow":
        output = output.replace('"OVERFLOW_LITERAL"', "1e309")
    elif mode == "dupkey":
        # A Python dict cannot hold a duplicate key, so splice a second
        # "runtime_version" into the serialized text directly: this is
        # syntactically valid JSON that a last-key-wins decoder would accept.
        output = '{"runtime_version": "duplicate-should-be-rejected", ' + output[1:]
    return output


def main(argv):
    mode = argv[1] if len(argv) > 1 else "ok"
    raw = sys.stdin.read()
    early = _EARLY_MODES.get(mode)
    if early is not None:
        return early(None)
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"protocol double got invalid request: {exc}", file=sys.stderr)
        return 4
    response = _base_response(request)
    tweak = _TWEAKS.get(mode)
    if tweak is not None:
        tweak(response)
    sys.stdout.write(_serialize(response, mode))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
