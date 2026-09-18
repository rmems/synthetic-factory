#!/usr/bin/env python3
"""Replay one producer coordinate in a fresh interpreter and private source tree."""

from __future__ import annotations

import json
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_simulator_worker")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_simulator_worker"
    )


def _selected_proposal(scenario, seed, count):
    """Advance the reviewed draw stream without retaining preceding proposals."""
    scenario._check_request(seed, count)
    stream = scenario.DrawStream(seed)
    for index in range(count):
        kind = scenario.fv.DISTURBANCES[index % len(scenario.fv.DISTURBANCES)]
        system = scenario._system_draw(stream)
        disturbance = scenario._disturbance(stream, kind, system["channels"])
    return [scenario._proposal(count - 1, system, disturbance)]


def replay(snapshot_pipelines, seed, index, stamp):
    sys.path.insert(0, snapshot_pipelines)
    from oracle_grounded import fault_oracle

    scenario = fault_oracle.scenario
    # Only the scenario selection changes. The pinned producer performs its
    # ordinary request checks, timestamp validation, oracle run and assembly.
    scenario.propose_scenarios = lambda seed, count: _selected_proposal(scenario, seed, count)
    return fault_oracle.build_records(seed, index + 1, produced_at=stamp)[0]


def main():
    snapshot_pipelines, seed, index, stamp = sys.argv[1:]
    record = replay(snapshot_pipelines, int(seed), int(index), stamp)
    print(json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False))


if __package__:
    _expose_package_sibling(__name__)

if __name__ == "__main__":
    main()
