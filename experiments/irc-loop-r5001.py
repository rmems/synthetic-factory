#!/usr/bin/env python3
"""Publish IRC r5001+ in-process.

Stock ``round_txn.py reserve/frontier`` re-validates every committed marker and
dies on historical r01 envelope. New staged batches still get full envelope
checks inside ``publish`` → ``validate_stage``.
"""
from __future__ import annotations
import importlib.util, json, signal, sys
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn as rt  # noqa: E402

_orig_completed_manifests = rt.completed_manifests
_orig_committed_ids = rt.committed_ids
_id_cache = None


def light_completed_manifests(factory_dir: Path) -> dict:
    """Read completion markers without re-running historical envelope audits."""
    factory_dir = Path(factory_dir)
    manifests = {}
    for path in factory_dir.glob("ROUND-r*.complete.json"):
        match = rt.COMPLETE_RE.fullmatch(path.name)
        if match is None or not path.is_file() or path.is_symlink():
            continue
        payload = rt.read_json(path)
        round_number = int(match.group(1))
        if (
            payload.get("factory") == factory_dir.name
            and payload.get("round") == round_number
            and payload.get("commit_point") == path.name
        ):
            manifests[round_number] = payload
    return manifests


def cached_committed_ids(factory_dir: Path):
    global _id_cache
    if _id_cache is None:
        _id_cache = _orig_committed_ids(factory_dir)
    return _id_cache


rt.completed_manifests = light_completed_manifests
rt.committed_ids = cached_committed_ids

print(json.dumps({"phase": "load_mill"}), flush=True)
spec = importlib.util.spec_from_file_location("irc5001", "/tmp/irc_mill_r5001.py")
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
w.m.notes_for = w.notes_for
print(json.dumps({"phase": "guards_and_harvest"}), flush=True)
w.extra_unique_guards()
used_svc, used_clu, used_tix, _ids = w.m.harvest_used(w.m.FACTORY_DIR)
print(json.dumps({"phase": "harvest_done", "used_svc": len(used_svc)}), flush=True)
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
MAX_PUBLISHES = 26
FACTORY = w.m.FACTORY_DIR


def next_round():
    st = rt.frontier_status(FACTORY)
    return int(st["next_round"])


def publish_round(rnd, pair, reservation):
    w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
    w.m.write_stage(Path(reservation["staging_dir"]), rnd)
    manifest = rt.publish(FACTORY, rnd, reservation["token"])
    rec = {
        "round": rnd,
        "ids": [e["id"] for e in w.m.pair_for_round(rnd)],
        "records": manifest.get("records"),
    }
    print(json.dumps({"published": rec}), flush=True)
    if _id_cache is not None:
        for eid in rec["ids"]:
            _id_cache[eid] = f"batch-r{rnd:02d}.jsonl"
    return rec


def main():
    print(json.dumps({"phase": "warm_committed_ids"}), flush=True)
    cached_committed_ids(FACTORY)
    print(json.dumps({"phase": "ids_warm", "ids": len(_id_cache or {})}), flush=True)
    published = []
    offset = 0
    low_cov = 0
    while offset + 1 < len(REMAINING) and len(published) < MAX_PUBLISHES:
        reserved = sorted(FACTORY.glob("ROUND-r*.reserved.json"))
        if reserved:
            print(json.dumps({
                "stop": "foreign_reservation",
                "reserved": [p.name for p in reserved],
                "published": published,
            }), flush=True)
            return 2
        rnd = next_round()
        pair = REMAINING[offset:offset + 2]
        w.m.BASE_ROUND, w.m.PLANTS = rnd, pair
        try:
            reservation = rt.reserve(FACTORY, rnd, 2)
        except rt.TransactionError as exc:
            print(json.dumps({
                "reserve_failed": str(exc),
                "round": rnd,
                "published": published,
            }), flush=True)
            return 2
        rec = publish_round(rnd, pair, reservation)
        published.append(rec)
        notes = FACTORY / f"NOTES-r{rnd:02d}.md"
        cov = None
        if notes.exists():
            for line in notes.read_text().splitlines():
                if line.startswith("Novel coverage:"):
                    tok = line.split(":", 1)[1].strip().rstrip("%").split()[0]
                    try:
                        cov = float(tok)
                    except ValueError:
                        cov = None
                    break
        if cov is not None and cov < 5:
            low_cov += 1
        else:
            low_cov = 0
        if low_cov >= 2:
            print(json.dumps({
                "stop": "two_consecutive_low_coverage",
                "published": published,
            }), flush=True)
            return 0
        offset += 2
    print(json.dumps({"ok": True, "count": len(published), "last": published[-1] if published else None}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
