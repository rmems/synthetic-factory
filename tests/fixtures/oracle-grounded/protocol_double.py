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


def _early_response(mode):
    if mode == "fail":
        print("protocol double asked to fail", file=sys.stderr)
        return 3, True
    if mode == "badjson":
        sys.stdout.write("this is not json")
        return 0, True
    if mode == "stdout_flood":
        sys.stdout.write("x" * (9 * 1024 * 1024))
        return 0, True
    if mode == "stderr_flood":
        sys.stderr.write("x" * (2 * 1024 * 1024))
        return 3, True
    return 0, False


def _response(request):
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


def _mutate_response(response, mode):
    simple_changes = {
        "wrongproto": ("protocol", "sf-oracle/999"),
        "unknowncommit": ("runtime_commit", "unknown"),
        "badcommit": ("runtime_commit", "not-a-source-revision"),
    }
    if mode in simple_changes:
        key, value = simple_changes[mode]
        response[key] = value
    elif mode == "noversion":
        response.pop("runtime_version")
    elif mode == "empty":
        response["measured"] = {}
    elif mode == "emptyunits":
        response["units"] = {}
    elif mode in ("nan", "infinity"):
        response["measured"]["nonfinite"] = float("nan" if mode == "nan" else "inf")
    elif mode == "overflow":
        response["measured"]["nonfinite"] = "OVERFLOW_LITERAL"


def _serialize(response, mode):
    output = json.dumps(response, sort_keys=True)
    if mode == "overflow":
        return output.replace('"OVERFLOW_LITERAL"', "1e309")
    if mode == "dupkey":
        # A Python dict cannot hold a duplicate key, so splice a second
        # "runtime_version" into the serialized text directly.
        return '{"runtime_version": "duplicate-should-be-rejected", ' + output[1:]
    return output


def main(argv):
    mode = argv[1] if len(argv) > 1 else "ok"
    status, handled = _early_response(mode)
    if handled:
        return status
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        print(f"protocol double got invalid request: {exc}", file=sys.stderr)
        return 4
    response = _response(request)
    _mutate_response(response, mode)
    sys.stdout.write(_serialize(response, mode))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
