#!/usr/bin/env python3
"""llm-eval-flakiness mill: reserve → stage → publish unique pairs.

Does not clone leftover r76–r612 unicode/HTTP/coerce catalogs, r613–r628
agreement-metric plants, r629–r700 cache-omit/last-unit/seed-leak/temp0/
rubric-alias mills, or r701–r727 2PL/CUSUM/Angoff/MMLU-redux/SWE-ftp/
FActScore/PR-AUC/IOB2/tau-passk/lost-middle/GAIA/XSTest/TOST/Cronbach/
Western-Electric/CoNLL/Simpson methodology clones.
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
    build_partial,
    build_success,
    dumps_episode,
    notes_md,
    validate_pair,
)
from mill_plants import PAIRS as PAIRS_A  # noqa: E402
from mill_plants_b import MORE as PAIRS_B  # noqa: E402
from mill_plants_e import MORE as PAIRS_E  # noqa: E402

PAIRS_LEGACY = PAIRS_A + PAIRS_B
PAIRS_UNIQUE = PAIRS_E
PAIRS = PAIRS_LEGACY + PAIRS_UNIQUE
START_ROUND = 613
UNIQUE_FROM = 728
# r613–r727 catalogs. New plants must not mention these in theme blobs.
THEME_BAN = (
    "cohen",
    "fleiss",
    "krippendorff",
    "bootstrap",
    "mcnemar",
    "wilson",
    "bleurt",
    "bradley",
    "ece",
    "promptfoo",
    "ragas",
    "glicko",
    "trueskill",
    "arena elo",
    "combining mark",
    "sku-9",
    "skip-as-1.0",
    "numpy.bool_",
    "icl label",
    "nested cv",
    "deepeval",
    "cache omits",
    "last-2 rejected",
    "lora_adapter",
    "azure_api_version",
    "irt-2pl",
    "mantel-haenszel",
    "cusum",
    "hartigan",
    "angoff",
    "extrabinom",
    "mmlu-redux",
    "ifeval",
    "swebench",
    "humaneval-plus",
    "factscore",
    "split-conformal",
    "pr-auc",
    "iob2",
    "bioes",
    "taubench",
    "pass^k",
    "bfcl",
    "lost-middle",
    "lost in the middle",
    "ewma",
    "shewhart",
    "gaia",
    "xstest",
    "harmbench",
    "tost",
    "cronbach",
    "outfit",
    "western electric",
    "pelt",
    "conll",
    "simpson",
    "2pl",
)
CLONE_SLUGS = {
    "irt-2pl-vs-pct",
    "mantel-haenszel-dif",
    "cusum-early-stop",
    "hartigan-dip-bimodal",
    "angoff-vs-arb-cut",
    "extrabinom-phi",
    "mmlu-redux-errata",
    "ifeval-strict-vs-loose",
    "swebench-ftp-vs-ptp",
    "humaneval-plus-mut",
    "factscore-atomic-vs-ovr",
    "split-conformal-cov",
    "pr-auc-vs-roc",
    "mcc-vs-accuracy",
    "iob2-vs-bioes-span",
    "hamming-vs-subset-acc",
    "taubench-passk-vs-p1",
    "bfcl-ast-vs-exec",
    "lost-middle-needle",
    "ewma-vs-shewhart",
    "gaia-l3-vs-overall",
    "tqa-mc1-vs-mc2",
    "xstest-dual-axis",
    "harmbench-judge-asr",
    "tost-vs-nonsig",
    "posthoc-power-n40",
    "cronbach-vs-sum",
    "rasch-outfit-misfit",
    "we-rule-8below",
    "pelt-changepoint",
    "conll-coref-avg",
    "simpson-policy-mix",
}
FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "llm-eval-flakiness-factory"
)
HOP_FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "prompt-cache-invalidation-factory"
)

REQUIRED_OK = {
    "slug",
    "seed",
    "avoided",
    "dump",
    "first_apply",
    "plan",
    "plan_change",
    "goal",
    "outcome",
    "rg",
    "rg_obs",
    "test",
    "test_name",
    "test_body",
    "gate_want",
    "fail_obs",
    "fail_short",
    "src",
    "src_body",
    "obs5",
    "stats_cmd",
    "stats_obs",
    "wrong_old",
    "wrong_new",
    "wrong_label",
    "wrong_still",
    "still_fail",
    "fix_src",
    "rewrite_obs",
    "helper",
    "fix_helper",
    "helper_obs",
    "pass_obs",
    "suite_ok",
    "suite_short",
    "test2",
    "test2_body",
    "test2_pass",
    "residual",
    "residual_path",
    "residual_pat",
    "residual_obs",
    "gate_again",
    "confirm",
    "final_obs",
    "tests_passed",
}
REQUIRED_BAD = {
    "slug",
    "seed",
    "avoided",
    "dump",
    "first_apply",
    "plan",
    "plan_change",
    "goal",
    "outcome",
    "rg",
    "rg_obs",
    "test",
    "test_name",
    "test_body",
    "gate_want",
    "fail_obs",
    "fail_short",
    "src",
    "src_body",
    "obs5",
    "stats_cmd",
    "stats_obs",
    "wrong_old",
    "wrong_new",
    "wrong_label",
    "wrong_still",
    "still_fail",
    "fix_src",
    "rewrite_obs",
    "helper",
    "fix_helper",
    "helper_obs",
    "pass_obs",
    "suite_fail",
    "nightly",
    "nightly_test",
    "nightly_body",
    "xfail_old",
    "xfail_new",
    "handoff",
    "xfail_obs",
    "leftover_obs",
    "gate_again",
    "tests_passed",
}


def coverage_for(round_n: int, unique_start: int) -> int:
    return max(70, 88 - (round_n - unique_start))


def pair_for(round_n: int, unique_start: int):
    idx = round_n - unique_start
    if idx < 0 or idx >= len(PAIRS_UNIQUE):
        raise KeyError(
            f"no unique plant pair for round {round_n} "
            f"(have {len(PAIRS_UNIQUE)} from r{unique_start})"
        )
    return PAIRS_UNIQUE[idx]


def build_pair_from(round_n: int, ok: dict, bad: dict, unique_start: int):
    ok_ep = build_success(round_n, ok)
    bad_ep = build_partial(round_n, bad)
    validate_pair(ok_ep, bad_ep, round_n)
    notes = notes_md(round_n, ok, bad, coverage_for(round_n, unique_start))
    if "Novel coverage:" not in notes:
        raise ValueError("NOTES missing Novel coverage")
    return ok_ep, bad_ep, notes


def build_pair(round_n: int, unique_start: int):
    ok, bad = pair_for(round_n, unique_start)
    return build_pair_from(round_n, ok, bad, unique_start)


def emit_stage_pair(stage: Path, round_n: int, ok: dict, bad: dict, unique_start: int):
    ok_ep, bad_ep, notes = build_pair_from(round_n, ok, bad, unique_start)
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes_path = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        dumps_episode(ok_ep) + "\n" + dumps_episode(bad_ep) + "\n",
        encoding="utf-8",
    )
    notes_path.write_text(notes, encoding="utf-8")
    return ok_ep["id"], bad_ep["id"]


def emit_stage(stage: Path, round_n: int, unique_start: int):
    ok, bad = pair_for(round_n, unique_start)
    return emit_stage_pair(stage, round_n, ok, bad, unique_start)


def _theme_blob(ok: dict, bad: dict) -> str:
    parts = []
    for plant in (ok, bad):
        for key in (
            "slug",
            "seed",
            "goal",
            "plan",
            "plan_change",
            "dump",
            "first_apply",
        ):
            parts.append(str(plant.get(key, "")))
    return " ".join(parts).lower()


def self_check() -> None:
    slugs = []
    srcs = []
    tests = []
    helpers = []
    for i, (ok, bad) in enumerate(PAIRS):
        label = f"pair[{i}] {ok['slug']}"
        miss_ok = REQUIRED_OK - ok.keys()
        miss_bad = REQUIRED_BAD - bad.keys()
        if miss_ok:
            raise ValueError(f"{label} ok missing {sorted(miss_ok)}")
        if miss_bad:
            raise ValueError(f"{label} bad missing {sorted(miss_bad)}")
        if ok.get("success") is not True:
            raise ValueError(f"{label} ok success flag")
        if bad.get("success") is not False:
            raise ValueError(f"{label} bad success flag")
        for plant in (ok, bad):
            slugs.append(plant["slug"])
            srcs.append(plant["src"])
            tests.append(plant["test"])
            helpers.append(plant["helper"])
            if plant["wrong_old"] not in plant["src_body"]:
                raise ValueError(
                    f"{label} {plant['slug']} wrong_old not in src_body"
                )
        dummy = 9000 + i
        ok_ep, bad_ep, notes = build_pair_from(dummy, ok, bad, 9000)
        assert ok_ep["reward"]["success"] is True
        assert bad_ep["reward"]["success"] is False
        assert len(ok_ep["steps"]) == 16
        assert len(bad_ep["steps"]) == 16
        assert notes.startswith("# NOTES-")
        for ep in (ok_ep, bad_ep):
            for step in ep["steps"]:
                db = step["decision_basis"]
                if len(db) > 240:
                    raise ValueError(f"{ep['id']} step {step['n']} db {len(db)}")
    for i, (ok, bad) in enumerate(PAIRS_UNIQUE):
        blob = _theme_blob(ok, bad)
        for word in THEME_BAN:
            if word in blob:
                raise ValueError(
                    f"unique pair[{i}] {ok['slug']} banned theme {word!r}"
                )
        for plant in (ok, bad):
            if plant["slug"] in CLONE_SLUGS:
                raise ValueError(f"clone slug {plant['slug']}")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(srcs)) != len(srcs):
        raise ValueError(f"duplicate src paths: {srcs}")
    if len(set(tests)) != len(tests):
        raise ValueError(f"duplicate test paths: {tests}")
    if len(set(helpers)) != len(helpers):
        raise ValueError(f"duplicate helper paths: {helpers}")
    print(
        f"self_check ok: {len(PAIRS_UNIQUE)} unique pairs "
        f"(plus {len(PAIRS_LEGACY)} legacy r{START_ROUND}+)"
    )


def _published_slugs(factory_dir: Path) -> set[str]:
    used = set()
    for path in factory_dir.glob("batch-r*.jsonl"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = str(rec.get("id", ""))
            parts = eid.split("-", 2)
            if len(parts) == 3 and parts[0] == "lef":
                used.add(parts[2])
    return used


def run_loop(min_rounds: int = 12, max_rounds: int = 16) -> int:
    import time

    from round_txn import TransactionError, abort, frontier_status, publish, reserve

    published = []
    hops = []
    unique_start = None
    plant_i = 0
    last_hop_round = None
    used = _published_slugs(FACTORY)
    while plant_i < len(PAIRS_UNIQUE) and PAIRS_UNIQUE[plant_i][0]["slug"] in used:
        plant_i += 1
    deadline = time.time() + 40 * 60
    while len(published) < max_rounds and time.time() < deadline:
        if plant_i >= len(PAIRS_UNIQUE):
            print("STOP: unique plants exhausted")
            break
        while plant_i < len(PAIRS_UNIQUE) and PAIRS_UNIQUE[plant_i][0]["slug"] in used:
            plant_i += 1
        if plant_i >= len(PAIRS_UNIQUE):
            print("STOP: unique plants exhausted")
            break
        status = frontier_status(FACTORY)
        round_n = status["next_round"]
        reserved = FACTORY / f"ROUND-r{round_n:02d}.reserved.json"
        if reserved.exists():
            if last_hop_round != round_n:
                hop_status = frontier_status(HOP_FACTORY)
                hop = {
                    "lef_next": round_n,
                    "lef_reserved": True,
                    "hop_factory": HOP_FACTORY.name,
                    "hop_next": hop_status["next_round"],
                    "hop_reserved": (
                        HOP_FACTORY
                        / f"ROUND-r{hop_status['next_round']:02d}.reserved.json"
                    ).exists(),
                }
                hops.append(hop)
                print(json.dumps({"hop": hop}), flush=True)
                last_hop_round = round_n
            time.sleep(0.05)
            continue
        if unique_start is None:
            unique_start = round_n
        ok, bad = PAIRS_UNIQUE[plant_i]
        try:
            payload = reserve(FACTORY, round_n, 2)
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{round_n}: {exc}")
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"lef_next": round_n, "error": msg, "stolen": False})
                time.sleep(0.05)
                continue
            raise
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage_pair(stage, round_n, ok, bad, unique_start)
            manifest = publish(FACTORY, round_n, token)
            plant_i += 1
            used.add(ok["slug"])
            used.add(bad["slug"])
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
        print(json.dumps({"published": published[-1]}), flush=True)
    print(json.dumps({"published_rounds": [p["round"] for p in published], "hops": hops}))
    if len(published) < min_rounds and not hops:
        if published:
            return 0
        return 1
    return 0 if published else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "check":
        self_check()
        return 0
    if argv[0] == "emit":
        round_n = int(argv[1])
        dest = Path(argv[2])
        unique_start = int(argv[3]) if len(argv) > 3 else round_n
        dest.mkdir(parents=True, exist_ok=True)
        ids = emit_stage(dest, round_n, unique_start)
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
