#!/usr/bin/env python3
"""eval-harness unique leftover mill: reserve → stage → publish.

Does not clone r50–r252 unicode leftover, r253–r293 eval-infra leftover,
or r294–r319 CI/judge/metric/trace/fmt/cache cartesian leftover.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MILL_DIR = Path(__file__).resolve().parent
REPO = MILL_DIR.parents[1]
sys.path.insert(0, str(MILL_DIR))
sys.path.insert(0, str(REPO / "pipelines"))

from mill_gen import (  # noqa: E402
    BANNED_SNIPPETS,
    build_episode,
    dumps_episode,
    notes_md,
    validate_pair,
)
import mill_plants  # noqa: E402
import mill_plants_b  # noqa: F401,E402
import mill_plants_c  # noqa: F401,E402
import mill_plants_d  # noqa: F401,E402
import mill_plants_e  # noqa: F401,E402
import mill_plants_f  # noqa: F401,E402
import mill_plants_g  # noqa: F401,E402
import mill_plants_h  # noqa: F401,E402
import mill_plants_i  # noqa: F401,E402
import mill_plants_j  # noqa: F401,E402
import mill_plants_k  # noqa: F401,E402
import mill_plants_l  # noqa: F401,E402
import mill_plants_m  # noqa: F401,E402
import mill_plants_n  # noqa: F401,E402
import mill_plants_o  # noqa: F401,E402
import mill_plants_p  # noqa: F401,E402
import mill_plants_q  # noqa: F401,E402
import mill_plants_r  # noqa: F401,E402
import mill_plants_s  # noqa: F401,E402
import mill_plants_t  # noqa: F401,E402
import mill_plants_u  # noqa: F401,E402
import mill_plants_v  # noqa: F401,E402
import mill_plants_w  # noqa: F401,E402
import mill_plants_x  # noqa: F401,E402
import mill_plants_y  # noqa: F401,E402
import mill_plants_z  # noqa: F401,E402
import mill_plants_aa  # noqa: F401,E402
import mill_plants_ab  # noqa: F401,E402
import mill_plants_ac  # noqa: F401,E402
import mill_plants_ad  # noqa: F401,E402
import mill_plants_ae  # noqa: F401,E402
import mill_plants_af  # noqa: F401,E402
import mill_plants_ag  # noqa: F401,E402
import mill_plants_ah  # noqa: F401,E402
import mill_plants_ai  # noqa: F401,E402
import mill_plants_aj  # noqa: F401,E402
import mill_plants_ak  # noqa: F401,E402
import mill_plants_al  # noqa: F401,E402
import mill_plants_am  # noqa: F401,E402
import mill_plants_an  # noqa: F401,E402
import mill_plants_ao  # noqa: F401,E402

PAIRS = mill_plants.PAIRS
START_ROUND = 294
FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "eval-harness-trajectory-factory"
)
HOP_FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "observability-debug-factory"
)

REQUIRED = {
    "slug",
    "domain",
    "kind",
    "avoided",
    "goal",
    "plan",
    "outcome",
    "ticket",
    "src",
    "src_obs",
    "run",
    "fail_obs",
    "inspect",
    "inspect_obs",
    "first_path",
    "first_old",
    "first_new",
    "first_obs",
    "rate_tail",
    "still_after_429",
    "grep",
    "grep_obs",
    "plan_change",
    "fix_path",
    "fix_old",
    "fix_new",
    "fix_obs",
    "retry_obs",
    "test",
    "test_body",
    "test_obs",
    "suite_obs",
    "gate_obs",
    "diff_obs",
    "residual",
    "success",
    "tests_passed",
    "tests_failed_as_designed",
}

THEME_BAN = (
    "combining mark",
    "u+2022",
    "u+2027",
    "14-day",
    "14‧day",
    "pytest-xdist",
    "litellm fallback",
    "json_mode",
    "latest_test_run",
    "vcr cassette",
    "mlflow",
    "langfuse",
    "cancelorderrequest",
    "cohere rerank",
    "semantic cache",
    "helm ",
    "sample_rate",
    "confident_sample_rate",
    "black wrap",
    "isort ",
    "pytest-randomly",
    "httpx.timeout",
    "ansible",
    "pulumi",
    "sku-9",
    "restore-keys",
    "outlines-schema",
    "task-completion",
    "json-sort",
    "diskcache",
    "trulens",
    "phoenix-eval",
    "evidently",
    "giskard",
    "neptune-log",
    "clearml",
    "comet-experiment",
    "aim-run-hash",
    "geval-cache",
    "geval cache",
    "temperature-seed",
    "faithfulness empty",
    "collectonly",
    "test_ prefix",
    "python_files = test_",
)


def coverage_for(round_n: int) -> int:
    return max(78, 84 - max(0, round_n - START_ROUND) // 4)


def pair_for(round_n: int):
    idx = round_n - START_ROUND
    if idx < 0 or idx >= len(PAIRS):
        raise KeyError(
            f"no unique plant pair for round {round_n} "
            f"(have {len(PAIRS)} from r{START_ROUND})"
        )
    return PAIRS[idx]


def build_pair(round_n: int):
    ok, bad = pair_for(round_n)
    ok_ep = build_episode(round_n, ok)
    bad_ep = build_episode(round_n, bad)
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


def _theme_blob(ok: dict, bad: dict) -> str:
    parts = []
    for plant in (ok, bad):
        for key in ("slug", "goal", "plan", "plan_change", "ticket", "outcome"):
            parts.append(str(plant.get(key, "")))
    return " ".join(parts).lower()


def self_check() -> None:
    slugs = []
    srcs = []
    tests = []
    domains = []
    for i, (ok, bad) in enumerate(PAIRS):
        label = f"pair[{i}] {ok['slug']}"
        for plant, expect in ((ok, True), (bad, False)):
            miss = REQUIRED - plant.keys()
            if miss:
                raise ValueError(f"{label} {plant['slug']} missing {sorted(miss)}")
            if plant.get("success") is not expect:
                raise ValueError(f"{label} {plant['slug']} success flag")
            slugs.append(plant["slug"])
            srcs.append((plant["src"], plant["inspect"], plant["test"]))
            tests.append(plant["test"])
            domains.append(plant["domain"])
            if len(plant["plan_change"]) > 180:
                raise ValueError(
                    f"{label} {plant['slug']} plan_change too long for db"
                )
        dummy = START_ROUND + i
        ok_ep, bad_ep, notes = build_pair(dummy)
        assert ok_ep["reward"]["success"] is True
        assert bad_ep["reward"]["success"] is False
        assert len(ok_ep["steps"]) == 16
        assert len(bad_ep["steps"]) == 16
        assert "Novel coverage:" in notes
        # Published r294–r319 may name their own leftover; ban clones only on r320+.
        if dummy >= 320:
            blob = _theme_blob(ok, bad)
            for word in THEME_BAN:
                if word in blob:
                    raise ValueError(
                        f"unique pair[{i}] {ok['slug']} banned theme {word!r}"
                    )
        for ep in (ok_ep, bad_ep):
            for step in ep["steps"]:
                db = step["decision_basis"]
                if len(db) > 240:
                    raise ValueError(f"{ep['id']} step {step['n']} db {len(db)}")
            dumped = dumps_episode(ep)
            for snippet in BANNED_SNIPPETS:
                if snippet.startswith("U+") or "‧" in snippet:
                    if snippet in dumped:
                        raise ValueError(f"{ep['id']} banned {snippet}")
                elif snippet.lower() in dumped.lower():
                    raise ValueError(f"{ep['id']} banned {snippet}")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(tests)) != len(tests):
        raise ValueError(f"duplicate test paths: {tests}")
    if len(set(domains)) != len(domains):
        raise ValueError(f"duplicate domains: {domains}")
    print(f"self_check ok: {len(PAIRS)} unique pairs from r{START_ROUND}")


def run_loop(min_rounds: int = 80, max_rounds: int = 80) -> int:
    import time

    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published = []
    hops = []
    last_hop_round = None
    deadline = time.time() + 8 * 60 * 60
    while len(published) < max_rounds and time.time() < deadline:
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            if last_hop_round != round_n:
                hop_status = frontier_status(HOP_FACTORY)
                hop = {
                    "evh_next": round_n,
                    "evh_reserved": True,
                    "stolen": False,
                    "hop_factory": HOP_FACTORY.name,
                    "hop_next": hop_status["next_round"],
                    "action": "HOP",
                }
                hops.append(hop)
                print(json.dumps({"hop": hop}), flush=True)
                last_hop_round = round_n
            time.sleep(3)
            continue
        try:
            pair_for(round_n)
        except KeyError:
            print(json.dumps({"stop": "plants exhausted", "next": round_n}))
            break
        try:
            payload = reserve(FACTORY, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{round_n}: {exc}", flush=True)
            if "already exists" in msg or "not the frontier" in msg:
                hops.append(
                    {"evh_next": round_n, "error": msg, "stolen": False, "action": "HOP"}
                )
                time.sleep(2)
                continue
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
                print(f"abort failed r{round_n}: {abort_exc}", flush=True)
                print(
                    json.dumps(
                        {
                            "held": round_n,
                            "token": token,
                            "stage": str(stage),
                            "error": str(exc),
                        }
                    ),
                    flush=True,
                )
                return 2
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        published.append(
            {
                "round": round_n,
                "ids": ids,
                "records": manifest.get("records"),
            }
        )
        print(json.dumps({"published": published[-1]}), flush=True)
        if len(published) >= min_rounds and time.time() >= deadline:
            break
    print(
        json.dumps(
            {
                "published_rounds": [p["round"] for p in published],
                "hops": hops,
                "count": len(published),
            }
        ),
        flush=True,
    )
    if len(published) >= min_rounds:
        return 0
    if published and hops:
        return 0
    return 0 if published else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "check":
        self_check()
        return 0
    if argv[0] == "emit":
        self_check()
        round_n = int(argv[1])
        dest = Path(argv[2])
        dest.mkdir(parents=True, exist_ok=True)
        ids = emit_stage(dest, round_n)
        print(json.dumps({"ids": ids}))
        return 0
    if argv[0] == "loop":
        self_check()
        min_rounds = int(argv[1]) if len(argv) > 1 else 200
        max_rounds = int(argv[2]) if len(argv) > 2 else 200
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds)
    raise SystemExit("usage: mill.py [check|emit N DIR|loop [min] [max]]")


if __name__ == "__main__":
    raise SystemExit(main())
