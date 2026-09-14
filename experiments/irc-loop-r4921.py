#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, signal, sys
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

spec = importlib.util.spec_from_file_location("irc4921", "/tmp/irc_mill_r4921.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
w.m.notes_for = w.notes_for
w.extra_unique_guards()
used_svc, used_clu, used_tix, _ids = w.m.harvest_used(w.m.FACTORY_DIR)
for p in w.PLANTS:
    if p["service"] in used_svc:
        raise SystemExit(f"service collision {p['service']}")
    if p["cluster"] in used_clu:
        raise SystemExit(f"cluster collision {p['cluster']}")
    if p["ticket"] in used_tix:
        raise SystemExit(f"ticket collision {p['ticket']}")
for label, xs in (
    ("slug", [p["slug"] for p in w.PLANTS]),
    ("svc", [p["service"] for p in w.PLANTS]),
    ("clu", [p["cluster"] for p in w.PLANTS]),
    ("tix", [p["ticket"] for p in w.PLANTS]),
    ("node", [p["node"] for p in w.PLANTS]),
    ("ns", [p["ns"] for p in w.PLANTS]),
):
    if len(set(xs)) != len(xs):
        raise SystemExit("dup " + label)

REMAINING = list(w.PLANTS)
RAW = Path("/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-08-19-agentic")
SKIP = {"sandbox-refusal-factory"}


def hops():
    out = []
    for d in sorted(RAW.iterdir()):
        if not d.is_dir() or d.name in SKIP:
            continue
        if list(d.glob("ROUND-r*.reserved.json")):
            continue
        try:
            st = w.m.txn(["frontier", str(d)])
        except Exception:
            continue
        out.append({"factory": d.name, "next_round": st.get("next_round")})
    return out


def publish_round(rnd, pair, reservation):
    w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
    w.m.write_stage(Path(reservation["staging_dir"]), rnd)
    manifest = w.m.txn(
        ["publish", str(w.m.FACTORY_DIR), "--round", str(rnd), "--token", reservation["token"]]
    )
    rec = {"round": rnd, "ids": [e["id"] for e in w.m.pair_for_round(rnd)], "records": manifest.get("records")}
    print(json.dumps({"published": rec}), flush=True)
    return rec


def main():
    published = []
    offset = 0
    factory = w.m.FACTORY_DIR
    while offset + 1 < len(REMAINING):
        status = w.m.txn(["frontier", str(factory)])
        rnd = int(status["next_round"])
        pair = REMAINING[offset:offset + 2]
        w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
        try:
            reservation = w.m.txn(
                ["reserve", str(factory), "--round", str(rnd), "--expected", "2"]
            )
        except RuntimeError as exc:
            print(json.dumps({
                "reserve_failed": str(exc),
                "round": rnd,
                "published": published,
                "unreserved_hops": hops()[:16],
            }), flush=True)
            return 2
        rec = publish_round(rnd, pair, reservation)
        published.append(rec)
        offset += 2
    print(json.dumps({"ok": True, "count": len(published), "last": published[-1] if published else None}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
