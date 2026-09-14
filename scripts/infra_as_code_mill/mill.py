#!/usr/bin/env python3
"""IaC mill r659+: reserve → stage → publish unique leftover/handoff pairs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

MILL_DIR = Path(__file__).resolve().parent
REPO = MILL_DIR.parents[1]
sys.path.insert(0, str(MILL_DIR))
sys.path.insert(0, str(REPO / "pipelines"))

from mill_gen import (  # noqa: E402
    assert_clean,
    build_fail,
    build_success,
    dumps_episode,
    notes_md,
)
from mill_plants import PAIRS as PAIRS_A  # noqa: E402
from mill_plants_b import MORE as PAIRS_B  # noqa: E402
from mill_plants_c import MORE as PAIRS_C  # noqa: E402

# r609–r624 used PAIRS_A+B (already published). Frontier is r659+.
PAIRS = PAIRS_C
START_ROUND = 659
FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "infra-as-code-factory"
)
BANNED_CLONE = (
    "state mv",
    "state-mv",
    "pulumi refresh",
    "cdk bootstrap",
    "tofu lock",
    "terragrunt include",
    "atlantis workspace",
    "spacelift-skip",
    "tfc-workspace",
    "import block",
    "migrate-state",
    "providers lock",
    "stack rename",
    "hotswap",
    "terraform test",
    "-target leftover",
    "mock_outputs",
    "tofu vs terraform workflow",
    "pulumi esc",
    "state encryption",
    "tfc-cancel",
    "bicep what-if",
    "arm --mode complete",
    "sam deploy",
    "cdktf synth",
    "consul-terraform-sync",
    "cts once",
    "packer build",
    "nomad job",
    "invalidparametervalue",
    "harborcluster",
    "sparkapplication",
    "leftover crd",
)


def coverage_for(round_n: int) -> int:
    return max(72, 86 - (round_n - START_ROUND) // 2)


def pair_for(round_n: int):
    idx = round_n - START_ROUND
    if idx < 0 or idx >= len(PAIRS):
        raise KeyError(
            f"no plant pair for round {round_n} (have {len(PAIRS)} from r{START_ROUND})"
        )
    return PAIRS[idx]


def build_pair(round_n: int):
    ok, bad, extra = pair_for(round_n)
    ok_ep = build_success(round_n, ok)
    bad_ep = build_fail(round_n, bad)
    assert_clean(ok_ep)
    assert_clean(bad_ep)
    if ok_ep["id"] == bad_ep["id"]:
        raise ValueError("duplicate ids in pair")
    blob = (json.dumps(ok_ep) + json.dumps(bad_ep) + extra).lower()
    for sub in BANNED_CLONE:
        if sub in blob:
            raise ValueError(f"clone theme leaked: {sub}")
    notes = notes_md(round_n, ok, bad, coverage_for(round_n), extra)
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def emit_stage(stage: Path, round_n: int):
    ok_ep, bad_ep, notes = build_pair(round_n)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def self_check() -> None:
    slugs = []
    tests = []
    cfgs = []
    plants = []
    for i, (ok, bad, extra) in enumerate(PAIRS):
        round_n = START_ROUND + i
        for plant in (ok, bad):
            slugs.append(plant["slug"])
            tests.append(plant["test"])
            cfgs.append(plant["cfg"])
            plants.append(plant["ticket"])
        ok_ep, bad_ep, notes = build_pair(round_n)
        assert ok_ep["reward"]["success"] is True
        assert bad_ep["reward"]["success"] is False
        assert len(ok_ep["steps"]) == 17
        assert len(bad_ep["steps"]) == 17
        assert ok_ep["meta"]["generator"] == "grok-4.6"
        assert notes.startswith("# NOTES-")
        print(f"ok r{round_n} {ok_ep['id']} {bad_ep['id']}")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(tests)) != len(tests):
        raise ValueError(f"duplicate tests: {tests}")
    if len(set(cfgs)) != len(cfgs):
        raise ValueError(f"duplicate cfgs: {cfgs}")
    legacy = []
    for ok, bad, _extra in PAIRS_A + PAIRS_B:
        legacy.extend((ok["slug"], bad["slug"], ok["test"], bad["test"], ok["cfg"], bad["cfg"]))
    collide = [x for x in slugs + tests + cfgs if x in set(legacy)]
    if collide:
        raise ValueError(f"collides with r609–r624 mill: {collide}")
    print(
        f"self_check ok: {len(PAIRS)} pairs r{START_ROUND}–r{START_ROUND + len(PAIRS) - 1}"
    )


def run_loop(min_rounds: int = 12, max_rounds: int = 16) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published = []
    hops = []
    for _ in range(max_rounds):
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            hops.append(
                {
                    "iac_next": round_n,
                    "iac_reserved": True,
                    "stolen": False,
                }
            )
            print(json.dumps({"hop": hops[-1]}))
            break
        try:
            pair_for(round_n)
        except KeyError as exc:
            print(f"STOP: {exc}")
            break
        try:
            payload = reserve(FACTORY, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{round_n}: {exc}")
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"iac_next": round_n, "error": msg, "stolen": True})
                break
            raise
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage(stage, round_n)
            manifest = publish(FACTORY, round_n, token)
        except Exception as exc:
            try:
                abort(FACTORY, round_n, token)
            except Exception as abort_exc:
                print(f"abort failed r{round_n}: {abort_exc}")
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        published.append(
            {
                "round": round_n,
                "ids": ids,
                "records": manifest.get("records"),
            }
        )
        print(json.dumps({"published": published[-1]}))
        if len(published) >= max_rounds:
            break
    print(json.dumps({"published_rounds": [p["round"] for p in published], "hops": hops}))
    if len(published) < min_rounds and not hops:
        return 1
    return 0 if published or hops else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "check":
        self_check()
        return 0
    if argv[0] == "emit":
        round_n = int(argv[1])
        dest = Path(argv[2])
        dest.mkdir(parents=True, exist_ok=True)
        ids = emit_stage(dest, round_n)
        print(json.dumps({"ids": ids}))
        return 0
    if argv[0] == "loop":
        self_check()
        min_rounds = int(argv[1]) if len(argv) > 1 else 12
        max_rounds = int(argv[2]) if len(argv) > 2 else 16
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit("usage: mill.py [check|emit N DIR|loop [min] [max]]")


if __name__ == "__main__":
    raise SystemExit(main())
