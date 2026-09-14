#!/usr/bin/env python3
"""Observability mill r159+: reserve → stage → publish unique debug pairs."""

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
from mill_plants_s import MORE as PAIRS_S  # noqa: E402
from mill_plants_t import MORE as PAIRS_T  # noqa: E402
from mill_plants_u import MORE as PAIRS_U  # noqa: E402
from mill_plants_v import MORE as PAIRS_V  # noqa: E402
from mill_plants_v import ROUND_PAIRS as EXTRA_V  # noqa: E402
from mill_plants_w import MORE as PAIRS_W  # noqa: E402
from mill_plants_w import ROUND_PAIRS as EXTRA_W  # noqa: E402
from mill_plants_x import MORE as PAIRS_X  # noqa: E402
from mill_plants_x import ROUND_PAIRS as EXTRA_X  # noqa: E402
from mill_plants_y import MORE as PAIRS_Y  # noqa: E402
from mill_plants_y import ROUND_PAIRS as EXTRA_Y  # noqa: E402
from mill_plants_z import MORE as PAIRS_Z  # noqa: E402
from mill_plants_z import ROUND_PAIRS as EXTRA_Z  # noqa: E402
from mill_plants_aa import MORE as PAIRS_AA  # noqa: E402
from mill_plants_aa import ROUND_PAIRS as EXTRA_AA  # noqa: E402
from mill_plants_ab import MORE as PAIRS_AB  # noqa: E402
from mill_plants_ab import ROUND_PAIRS as EXTRA_AB  # noqa: E402
from mill_plants_ac import MORE as PAIRS_AC  # noqa: E402
from mill_plants_ac import ROUND_PAIRS as EXTRA_AC  # noqa: E402
from mill_plants_ad import MORE as PAIRS_AD  # noqa: E402
from mill_plants_ad import ROUND_PAIRS as EXTRA_AD  # noqa: E402
from mill_plants_ae import MORE as PAIRS_AE  # noqa: E402
from mill_plants_ae import ROUND_PAIRS as EXTRA_AE  # noqa: E402
from mill_plants_af import MORE as PAIRS_AF  # noqa: E402
from mill_plants_af import ROUND_PAIRS as EXTRA_AF  # noqa: E402
from mill_plants_ag import MORE as PAIRS_AG  # noqa: E402
from mill_plants_ag import ROUND_PAIRS as EXTRA_AG  # noqa: E402
from mill_plants_ah import MORE as PAIRS_AH  # noqa: E402
from mill_plants_ah import ROUND_PAIRS as EXTRA_AH  # noqa: E402
from mill_plants_ai import MORE as PAIRS_AI  # noqa: E402
from mill_plants_ai import ROUND_PAIRS as EXTRA_AI  # noqa: E402

EXTRA_ROUNDS = {
    **EXTRA_V,
    **EXTRA_W,
    **EXTRA_X,
    **EXTRA_Y,
    **EXTRA_Z,
    **EXTRA_AA,
    **EXTRA_AB,
    **EXTRA_AC,
    **EXTRA_AD,
    **EXTRA_AE,
    **EXTRA_AF,
    **EXTRA_AG,
    **EXTRA_AH,
    **EXTRA_AI,
}

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
    + PAIRS_S
    + PAIRS_T
    + PAIRS_U
    + PAIRS_V
    + PAIRS_W
    + PAIRS_X
    + PAIRS_Y
    + PAIRS_Z
    + PAIRS_AA
    + PAIRS_AB
    + PAIRS_AC
    + PAIRS_AD
    + PAIRS_AE
    + PAIRS_AF
    + PAIRS_AG
    + PAIRS_AH
    + PAIRS_AI
)
START_ROUND = 159
FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "observability-debug-factory"
)
TXN = REPO / "pipelines" / "round_txn.py"
AGENTIC = FACTORY.parent
SKIP_HOP = {
    "eval-harness-trajectory-factory",
    "sandbox-refusal-factory",
}
HOP_ORDER = [
    AGENTIC / "payment-idempotency-factory",
    AGENTIC / "llm-eval-flakiness-factory",
    AGENTIC / "infra-as-code-factory",
    AGENTIC / "prompt-cache-invalidation-factory",
    AGENTIC / "log-redaction-factory",
    AGENTIC / "package-release-factory",
    AGENTIC / "data-pipeline-repair-factory",
    AGENTIC / "git-ops-recovery-factory",
]
REQUIRED_OK = (
    "slug",
    "service",
    "dashboard_uid",
    "panel",
    "query",
    "lie",
    "false_lead",
    "config_path",
    "lie_path",
    "truth_name",
    "reload_name",
    "side",
    "surfaces",
    "avoided",
    "this_is",
    "step_note",
    "search_cmd",
    "dash_cmd",
    "query_cmd",
    "false_cmd",
    "truth_cmd",
    "confirm_cmd",
    "reload_cmd",
    "requery_cmd",
    "grafana_ok_cmd",
    "side_cmd",
    "final_cmd",
    "patch_old",
    "patch_new",
    "runbook_path",
    "runbook",
    "goal",
    "plan",
    "outcome",
)
REQUIRED_FAIL = (
    "slug",
    "service",
    "dashboard_uid",
    "panel",
    "query",
    "lie",
    "false_lead",
    "config_path",
    "lie_path",
    "wrong_path",
    "reload_name",
    "ticket",
    "xfail",
    "surfaces",
    "avoided",
    "this_is",
    "step_note",
    "next_note",
    "search_cmd",
    "dash_cmd",
    "query_cmd",
    "false_cmd",
    "reload_cmd",
    "requery_cmd",
    "denied_cmd",
    "xfail_cmd",
    "wrong_old",
    "wrong_new",
    "wrong2_old",
    "wrong2_new",
    "ticket_path",
    "ticket_body",
    "goal",
    "plan",
    "outcome",
)


def coverage_for(round_n: int) -> int:
    return max(72, 92 - (round_n - START_ROUND))


def _extra_len() -> int:
    return (
        len(PAIRS_V)
        + len(PAIRS_W)
        + len(PAIRS_X)
        + len(PAIRS_Y)
        + len(PAIRS_Z)
        + len(PAIRS_AA)
        + len(PAIRS_AB)
        + len(PAIRS_AC)
        + len(PAIRS_AD)
        + len(PAIRS_AE)
        + len(PAIRS_AF)
        + len(PAIRS_AG)
        + len(PAIRS_AH)
        + len(PAIRS_AI)
    )


def pair_for(round_n: int):
    if round_n in EXTRA_ROUNDS:
        return EXTRA_ROUNDS[round_n]
    idx = round_n - START_ROUND
    if idx < 0 or idx >= len(PAIRS) - _extra_len():
        raise KeyError(
            f"no plant pair for round {round_n} (have sequential r{START_ROUND}–"
            f"{START_ROUND + len(PAIRS) - _extra_len() - 1} plus extra {sorted(EXTRA_ROUNDS)})"
        )
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


def _iter_catalog():
    seq = PAIRS[: len(PAIRS) - _extra_len()]
    for i, pair in enumerate(seq):
        yield START_ROUND + i, pair
    for round_n in sorted(EXTRA_ROUNDS):
        yield round_n, EXTRA_ROUNDS[round_n]


def self_check() -> None:
    slugs = []
    services = []
    dashes = []
    lies = []
    for round_n, (ok, bad) in _iter_catalog():
        for key in REQUIRED_OK:
            if key not in ok:
                raise ValueError(f"r{round_n} ok missing {key}")
        for key in REQUIRED_FAIL:
            if key not in bad:
                raise ValueError(f"r{round_n} fail missing {key}")
        for plant, kind in ((ok, "ok"), (bad, "bad")):
            slugs.append(plant["slug"])
            services.append(plant["service"])
            dashes.append(plant["dashboard_uid"])
            lies.append(plant["lie"])
            for n in range(1, 16):
                if not str(plant.get(f"obs{n}", "")).strip():
                    raise ValueError(f"r{round_n} {kind} missing obs{n}")
        ok_ep, bad_ep, notes = build_pair(round_n)
        assert ok_ep["reward"]["success"] is True
        assert bad_ep["reward"]["success"] is False
        assert len(ok_ep["steps"]) == 15
        assert len(bad_ep["steps"]) == 15
        assert notes.startswith("# NOTES-")
        assert "Novel coverage:" in notes
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs: {slugs}")
    if len(set(services)) != len(services):
        raise ValueError(f"duplicate services: {services}")
    if len(set(dashes)) != len(dashes):
        raise ValueError(f"duplicate dashboards: {dashes}")
    if len(set(lies)) != len(lies):
        raise ValueError("duplicate lies")
    last_seq = START_ROUND + len(PAIRS) - _extra_len() - 1
    extra = ",".join(str(n) for n in sorted(EXTRA_ROUNDS))
    print(f"self_check ok: sequential r{START_ROUND}–r{last_seq}; extra r{extra}")


def _cli(args: list[str], check: bool = True):
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(TXN), *args],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.stdout:
        if args and args[0] == "frontier":
            try:
                payload = json.loads(proc.stdout)
                print(
                    json.dumps(
                        {
                            "next_round": payload.get("next_round"),
                            "factory": payload.get("factory"),
                            "highest_flushed": payload.get("highest_flushed"),
                        }
                    ),
                    flush=True,
                )
            except json.JSONDecodeError:
                print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n", flush=True)
        else:
            print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n", flush=True)
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
    if check and proc.returncode != 0:
        from round_txn import TransactionError

        raise TransactionError((proc.stderr or proc.stdout or f"exit {proc.returncode}").strip())
    return proc


def _is_reserved(factory: Path, round_n: int) -> bool:
    return (factory / f"ROUND-r{round_n:02d}.reserved.json").exists()


def _mill_for(factory: Path) -> Path:
    slug = factory.name.removesuffix("-factory").replace("-", "_")
    return REPO / "scripts" / f"{slug}_mill" / "mill.py"


def _mill_covers(mill: Path, round_n: int) -> bool:
    """Skip hop mills whose in-memory catalog cannot emit this frontier."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"hop_{mill.parent.name}", mill)
    if spec is None or spec.loader is None:
        return False
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        start = int(getattr(mod, "START_ROUND", 1))
        pairs = getattr(mod, "PAIRS", ())
        extra = getattr(mod, "EXTRA_ROUNDS", {}) or {}
        last = max([start + len(pairs) - 1, *extra.keys()] or [start])
    except Exception as exc:
        print(f"{mill} catalog unreadable ({exc}); skip", flush=True)
        return False
    if round_n not in extra and (round_n < start or round_n > last):
        print(f"{mill.parent.name} catalog r{start}–r{last} misses r{round_n}; skip", flush=True)
        return False
    return True


def _try_hop(hops: list) -> int:
    """If observability is reserved, hop an unreserved named factory. Never steal."""
    import subprocess

    for hop in HOP_ORDER:
        if hop.name in SKIP_HOP:
            continue
        if not hop.is_dir():
            continue
        proc = _cli(["frontier", str(hop)], check=False)
        if proc.returncode != 0:
            print(f"{hop.name} frontier failed; skip", flush=True)
            continue
        try:
            hn = json.loads(proc.stdout)["next_round"]
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"{hop.name} frontier unreadable; skip", flush=True)
            continue
        if _is_reserved(hop, hn):
            print(f"{hop.name} r{hn} reserved; skip", flush=True)
            continue
        mill = _mill_for(hop)
        if not mill.is_file():
            print(f"{hop.name} unreserved but mill missing {mill}; try next hop", flush=True)
            continue
        if not _mill_covers(mill, hn):
            continue
        hops.append(
            {
                "obs_reserved": True,
                "hop": hop.name,
                "hop_next": hn,
                "mill": str(mill),
                "stolen": False,
            }
        )
        print(json.dumps({"hop": hops[-1]}), flush=True)
        print(f"hop mill {mill} run (unbounded catalog)", flush=True)
        child = subprocess.run(
            [sys.executable, str(mill), "run"],
            cwd=REPO,
            check=False,
        )
        return child.returncode
    print("no unreserved hop mill with catalog; retry obs (never steal)", flush=True)
    return 3


def run_loop(min_rounds: int = 1, max_rounds: int | None = None) -> int:
    from round_txn import TransactionError

    if max_rounds is None:
        max_rounds = 500
    published = []
    hops = []
    while len(published) < max_rounds:
        proc = _cli(["frontier", str(FACTORY)])
        status = json.loads(proc.stdout)
        round_n = status["next_round"]
        if _is_reserved(FACTORY, round_n):
            hops.append({"obs_next": round_n, "obs_reserved": True, "stolen": False})
            print(json.dumps({"hop": hops[-1]}), flush=True)
            hop_rc = _try_hop(hops)
            if hop_rc != 3:
                return hop_rc
            import time

            time.sleep(2)
            continue
        try:
            pair_for(round_n)
        except KeyError as exc:
            print(f"STOP: {exc}", flush=True)
            break
        proc = _cli(
            ["reserve", str(FACTORY), "--round", str(round_n), "--expected", "2"],
            check=False,
        )
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()
            print(f"reserve failed r{round_n}: {msg}", flush=True)
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"obs_next": round_n, "error": msg, "stolen": False})
                hop_rc = _try_hop(hops)
                if hop_rc != 3:
                    return hop_rc
                import time

                time.sleep(2)
                continue
            raise TransactionError(msg)
        payload = json.loads(proc.stdout)
        stage = Path(payload["staging_dir"])
        token = payload["token"]
        try:
            ids = emit_stage(stage, round_n)
            pub = _cli(
                ["publish", str(FACTORY), "--round", str(round_n), "--token", token]
            )
            manifest = json.loads(pub.stdout)
        except Exception as exc:
            try:
                _cli(
                    ["abort", str(FACTORY), "--round", str(round_n), "--token", token],
                    check=False,
                )
            except Exception as abort_exc:
                print(f"abort failed r{round_n}: {abort_exc}", flush=True)
            raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
        published.append(
            {
                "round": round_n,
                "ids": ids,
                "records": manifest.get("records"),
            }
        )
        print(json.dumps({"published": published[-1]}), flush=True)
    print(
        json.dumps(
            {
                "published_rounds": [p["round"] for p in published],
                "count": len(published),
                "min_rounds": min_rounds,
                "hops": hops,
                "catalog_last": START_ROUND + len(PAIRS) - 1,
            }
        ),
        flush=True,
    )
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
    if argv[0] == "run":
        self_check()
        n = int(argv[1]) if len(argv) > 1 else 500
        return run_loop(max_rounds=n)
    raise SystemExit(f"usage: mill.py [check|run|emit N DIR] got {argv}")


if __name__ == "__main__":
    raise SystemExit(main())
