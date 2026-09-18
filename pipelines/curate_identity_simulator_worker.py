#!/usr/bin/env python3
"""Replay bounded producer coordinates within one authenticated private snapshot."""

from __future__ import annotations

from collections import OrderedDict
import json
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_simulator_worker")
    from .oracle_grounded.distill_vocabulary import is_genuine_int
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_simulator_worker"
    )
    from oracle_grounded.distill_vocabulary import is_genuine_int

MAX_STREAMS = 8
MAX_DRAWS = 1_000_000
MAX_REQUEST_BYTES = 4096


class ProposalStreams:
    """Eight RNG states/proposals at most; cumulative work includes every reset.

    A worker owns exactly one authenticated snapshot. Seed and timestamp keys
    cannot share stream authority outside that snapshot or its batch lifetime.
    Reverse-order requests and eviction can repeat prefixes, but the lifetime
    draw budget bounds this work before any more RNG operations are performed.
    """

    def __init__(self, scenario, *, max_draws=MAX_DRAWS):
        self.scenario = scenario
        self.remaining = max_draws
        self.streams = OrderedDict()

    def _state(self, key, index):
        state = self.streams.pop(key, None)
        if state is None or state[1] > index:
            state = (self.scenario.DrawStream(key[0]), -1, None)
        needed = index - state[1]
        if needed > self.remaining:
            raise ValueError("simulator replay exhausted its batch work budget")
        self.remaining -= needed
        return state

    def select(self, seed, index, stamp):
        scenario = self.scenario
        scenario._check_request(seed, index + 1)
        key = (seed, stamp)
        stream, previous, proposal = self._state(key, index)
        for position in range(previous + 1, index + 1):
            kind = scenario.fv.DISTURBANCES[position % len(scenario.fv.DISTURBANCES)]
            system = scenario._system_draw(stream)
            disturbance = scenario._disturbance(stream, kind, system["channels"])
            proposal = scenario._proposal(position, system, disturbance)
        self.streams[key] = (stream, index, proposal)
        if len(self.streams) > MAX_STREAMS:
            self.streams.popitem(last=False)
        return proposal


def _request(payload):
    seed, index, stamp = json.loads(payload)
    if not is_genuine_int(seed) or not is_genuine_int(index):
        raise ValueError("simulator coordinates must be integers")
    if not isinstance(stamp, str):
        raise ValueError("simulator timestamp must be text")
    return seed, index, stamp


def serve(snapshot_pipelines, incoming, outgoing):
    sys.path.insert(0, snapshot_pipelines)
    from oracle_grounded import fault_oracle

    streams = ProposalStreams(fault_oracle.scenario)
    while payload := incoming.readline(MAX_REQUEST_BYTES + 1):
        if len(payload) > MAX_REQUEST_BYTES or not payload.endswith(b"\n"):
            raise ValueError("simulator replay request exceeds its bound")
        seed, index, stamp = _request(payload)
        proposal = streams.select(seed, index, stamp)
        # Selection changes only; the pinned producer retains validation,
        # timestamp handling, oracle execution and complete envelope assembly.
        fault_oracle.scenario.propose_scenarios = lambda seed, count, selected=proposal: [selected]
        record = fault_oracle.build_records(seed, index + 1, produced_at=stamp)[0]
        outgoing.write(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
        outgoing.flush()


def main():
    serve(sys.argv[1], sys.stdin.buffer, sys.stdout)


if __package__:
    _expose_package_sibling(__name__)

if __name__ == "__main__":
    main()
