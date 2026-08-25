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
  empty       a response whose measurement is empty
  fail        exit nonzero
"""

import json
import sys


def main(argv):
    mode = argv[1] if len(argv) > 1 else "ok"
    raw = sys.stdin.read()
    if mode == "fail":
        print("protocol double asked to fail", file=sys.stderr)
        return 3
    if mode == "badjson":
        sys.stdout.write("this is not json")
        return 0
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"protocol double got invalid request: {exc}", file=sys.stderr)
        return 4

    response = {
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
    if mode == "wrongproto":
        response["protocol"] = "sf-oracle/999"
    elif mode == "noversion":
        response.pop("runtime_version")
    elif mode == "empty":
        response["measured"] = {}
    elif mode == "unknowncommit":
        response["runtime_commit"] = "unknown"
    elif mode == "badcommit":
        response["runtime_commit"] = "not-a-source-revision"
    sys.stdout.write(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
