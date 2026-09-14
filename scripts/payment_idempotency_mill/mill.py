#!/usr/bin/env python3
"""Payment mill r98+: reserve → stage → publish unique T/F pairs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

MILL_DIR = Path(__file__).resolve().parent
REPO = MILL_DIR.parents[1]
sys.path.insert(0, str(MILL_DIR))
sys.path.insert(0, str(REPO / "pipelines"))

from mill_gen import (  # noqa: E402
    build_fail,
    build_success,
    dumps_episode,
    notes_md,
    validate_pair,
)
from mill_plants import PAIRS as PAIRS_A  # noqa: E402
from mill_plants_b import MORE as PAIRS_B  # noqa: E402
from mill_plants_c import MORE as PAIRS_C  # noqa: E402
from mill_plants_d import MORE as PAIRS_D  # noqa: E402
from mill_plants_e import MORE as PAIRS_E  # noqa: E402
from mill_plants_f import MORE as PAIRS_F  # noqa: E402
from mill_plants_g import MORE as PAIRS_G  # noqa: E402
from mill_plants_h import MORE as PAIRS_H  # noqa: E402
from mill_plants_i import MORE as PAIRS_I  # noqa: E402
from mill_plants_j import MORE as PAIRS_J  # noqa: E402
from mill_plants_k import MORE as PAIRS_K  # noqa: E402
from mill_plants_l import MORE as PAIRS_L  # noqa: E402
from mill_plants_m import MORE as PAIRS_M  # noqa: E402
from mill_plants_n import MORE as PAIRS_N  # noqa: E402
from mill_plants_o import MORE as PAIRS_O  # noqa: E402
from mill_plants_p import MORE as PAIRS_P  # noqa: E402
from mill_plants_q import MORE as PAIRS_Q  # noqa: E402
from mill_plants_r import MORE as PAIRS_R  # noqa: E402

PAIRS = (
    PAIRS_A
    + PAIRS_B
    + PAIRS_C
    + PAIRS_D
    + PAIRS_E
    + PAIRS_F
    + PAIRS_G
    + PAIRS_H
    + PAIRS_I
    + PAIRS_J
    + PAIRS_K
    + PAIRS_L
    + PAIRS_M
    + PAIRS_N
    + PAIRS_O
    + PAIRS_P
    + PAIRS_Q
    + PAIRS_R
)
START_ROUND = 98
FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "payment-idempotency-factory"
)
HOP_FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "prompt-cache-invalidation-factory"
)


def coverage_for(round_n: int) -> int:
    if round_n >= 330:
        return 64
    if round_n >= 314:
        return 60
    if round_n >= 295:
        return 56
    if round_n >= 279:
        return 52
    return max(28, 43 - (round_n - START_ROUND) // 2)


def pair_for(round_n: int):
    idx = round_n - START_ROUND
    if idx < 0 or idx >= len(PAIRS):
        raise KeyError(f"no plant pair for round {round_n} (have {len(PAIRS)} from r{START_ROUND})")
    return PAIRS[idx]


def build_pair(round_n: int):
    ok, bad = pair_for(round_n)
    ok_ep = build_success(round_n, ok)
    bad_ep = build_fail(round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(round_n, ok, bad, coverage_for(round_n))
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
    srcs = []
    tables = []
    for i, (ok, bad) in enumerate(PAIRS):
        round_n = START_ROUND + i
        if ok.get("xfail") or bad.get("xfail") is None:
            pass
        if "xfail" not in bad:
            raise ValueError(f"r{round_n} fail plant missing xfail")
        for plant, kind in ((ok, "ok"), (bad, "bad")):
            slugs.append(plant["slug"])
            srcs.append(plant["src"])
            tables.append(plant["table"])
            if plant["skip_old"] not in plant["src_body"] and kind == "ok":
                # skip_old is applied to src; must match a line
                if plant["skip_old"] not in plant["src_body"]:
                    raise ValueError(f"r{round_n} {kind} skip_old not in src_body: {plant['slug']}")
            if plant["skip_old"] not in plant["src_body"]:
                raise ValueError(f"r{round_n} {plant['slug']} skip_old mismatch")
        ok_ep, bad_ep, notes = build_pair(round_n)
        assert ok_ep["reward"]["success"] is True
        assert bad_ep["reward"]["success"] is False
        assert len(ok_ep["steps"]) == 16
        assert len(bad_ep["steps"]) == 17
        assert notes.startswith("# NOTES-")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(srcs)) != len(srcs):
        raise ValueError(f"duplicate src paths: {srcs}")
    if len(set(tables)) != len(tables):
        raise ValueError(f"duplicate tables: {tables}")
    print(f"self_check ok: {len(PAIRS)} pairs r{START_ROUND}–r{START_ROUND + len(PAIRS) - 1}")


def run_loop(min_rounds: int = 12, max_rounds: int = 16) -> int:
    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published = []
    hops = []
    for _ in range(max_rounds):
        if len(published) >= min_rounds and _ >= min_rounds:
            # keep going until max_rounds unless frontier exhausted
            pass
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            hop_status = frontier_status(HOP_FACTORY)
            hops.append(
                {
                    "payment_next": round_n,
                    "payment_reserved": True,
                    "hop_factory": HOP_FACTORY.name,
                    "hop_next": hop_status["next_round"],
                    "hop_reserved": (
                        HOP_FACTORY / f"ROUND-r{hop_status['next_round']:02d}.reserved.json"
                    ).exists(),
                }
            )
            print(json.dumps({"hop": hops[-1]}))
            # Never steal. Prompt-cache mill is not this session's plant set.
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
                hops.append({"payment_next": round_n, "error": msg, "stolen": True})
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
    return 0 if published else 1


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
        min_rounds = int(argv[1]) if len(argv) > 1 else 12
        max_rounds = int(argv[2]) if len(argv) > 2 else 16
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit(f"usage: mill.py [check|emit N DIR|loop [min] [max]]")


if __name__ == "__main__":
    raise SystemExit(main())
