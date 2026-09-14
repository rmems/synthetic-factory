#!/usr/bin/env python3
"""Keep looping: MAC if unreserved else hop SIR r52+ / SSL r112+.

Never steal. Never sandbox-refusal if reserved or writing.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
sys.path.insert(0, str(REPO / "pipelines"))
import round_txn  # noqa: E402

AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
MAC = AGENTIC / "multi-agent-coordination-factory"
SIR = AGENTIC / "search-index-rebuild-factory"
SSL = AGENTIC / "ssl-cert-rotation-factory"
SBOX = AGENTIC / "sandbox-refusal-factory"
MAC_MILL = SourceFileLoader("mac3034", str(REPO / "experiments/mac-mill-r3034.py")).load_module()
SIR_MILL = REPO / "experiments/sir-mill-r52.py"
SSL_MILL = REPO / "experiments/ssl-mill-r112.py"
DEADLINE_S = 6 * 60 * 60


def busy(factory: Path) -> bool:
    return bool(list(factory.glob("ROUND-r*.reserved.json"))) or bool(
        list(factory.glob("ROUND-r*.publishing.json"))
    )


def used_mac_slugs() -> set[str]:
    slugs = set()
    for path in MAC.glob("batch-r*.jsonl"):
        try:
            rec = json.loads(path.read_text().splitlines()[0])
        except Exception:
            continue
        rid = rec.get("id", "")
        if rid.startswith("mac-r"):
            parts = rid.split("-", 2)
            if len(parts) == 3:
                slugs.add(parts[2])
    return slugs


def mill_cli(script: Path, rnd: int, stage: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(script), "--round", str(rnd), "--staging", str(stage)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    sys.stderr.write(proc.stderr or "")
    print(proc.stdout, flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{script.name} failed r{rnd}: {proc.stderr}")


def publish_hop(factory: Path, expected: int, mill: Path, first: int, last: int) -> bool:
    if factory == SBOX and busy(SBOX):
        print("never hop sandbox-refusal: reserved/writing", flush=True)
        return False
    if busy(factory):
        print(f"HOP skip {factory.name}: reserved/writing", flush=True)
        return False
    n = round_txn.frontier_status(factory)["next_round"]
    if n < first or n > last:
        print(f"HOP skip {factory.name}: r{n} outside {first}-{last}", flush=True)
        return False
    try:
        reservation = round_txn.reserve(factory, n, expected)
    except (round_txn.TransactionError, FileExistsError, OSError) as exc:
        print(f"HOP reserve fail {factory.name} r{n}: {exc}", flush=True)
        return False
    token = reservation["token"]
    stage = Path(reservation["staging_dir"])
    try:
        mill_cli(mill, n, stage)
        pub = round_txn.publish(factory, n, token)
    except Exception as exc:
        print(f"HOP mill/publish fail {factory.name} r{n}: {exc}", flush=True)
        try:
            round_txn.abort(factory, n, token)
        except round_txn.TransactionError:
            pass
        return False
    print(json.dumps({"hop": factory.name, "round": n, "records": pub.get("records")}), flush=True)
    return True


def publish_mac(spec: dict) -> bool:
    if busy(MAC):
        return False
    n = round_txn.frontier_status(MAC)["next_round"]
    try:
        reservation = round_txn.reserve(MAC, n, 1)
    except (round_txn.TransactionError, FileExistsError, OSError) as exc:
        print(f"MAC reserve fail r{n}: {exc}", flush=True)
        return False
    rec = MAC_MILL.build_record(n, spec)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    nbytes = len(line.encode())
    stage = Path(reservation["staging_dir"])
    (stage / reservation["batch_file"]).write_text(line + "\n")
    (stage / reservation["notes_file"]).write_text(MAC_MILL.notes_text(spec, nbytes, n))
    print(f"STAGED r{n} {rec['id']} {nbytes}B", flush=True)
    try:
        round_txn.publish(MAC, n, reservation["token"])
    except round_txn.TransactionError as exc:
        print(f"PUBLISH FAIL r{n}: {exc}", flush=True)
        try:
            round_txn.abort(MAC, n, reservation["token"])
        except round_txn.TransactionError:
            pass
        return False
    print(f"PUBLISHED r{n} {rec['id']} {nbytes}B", flush=True)
    return True


def try_hop() -> bool:
    if busy(SBOX):
        print("sandbox-refusal reserved/writing; never hop there", flush=True)
    if publish_hop(SIR, 2, SIR_MILL, 52, 51 + 20):
        return True
    if publish_hop(SSL, 2, SSL_MILL, 112, 111 + 20):
        return True
    return False


def main() -> int:
    MAC_MILL.self_check()
    taken = used_mac_slugs()
    mac_queue = [s for s in MAC_MILL.SCENARIOS if s["slug"] not in taken]
    print(json.dumps({"mac_remaining": len(mac_queue), "taken": len(taken)}), flush=True)
    published = {"mac": 0, "sir": 0, "ssl": 0}
    start = time.monotonic()
    mac_i = 0
    while time.monotonic() - start < DEADLINE_S:
        if mac_i < len(mac_queue) and not busy(MAC):
            if publish_mac(mac_queue[mac_i]):
                mac_i += 1
                published["mac"] += 1
                continue
        hopped = try_hop()
        if hopped:
            if SIR.exists() and not busy(SIR):
                published["sir"] += 1
            else:
                published["ssl"] += 1
            continue
        if mac_i >= len(mac_queue) and not hopped:
            # retry hops once more; if both catalogs blocked, wait then retry MAC
            time.sleep(2)
            if busy(MAC) and busy(SIR) and busy(SSL):
                time.sleep(3)
                continue
            n_sir = round_txn.frontier_status(SIR)["next_round"]
            n_ssl = round_txn.frontier_status(SSL)["next_round"]
            if (n_sir < 52 or n_sir > 71) and (n_ssl < 112 or n_ssl > 131) and (mac_i >= len(mac_queue) or busy(MAC)):
                print("catalogs exhausted and seats busy/out of range; keep waiting MAC", flush=True)
                time.sleep(4)
                # refresh mac queue in case another writer finished and we can resume remaining
                taken = used_mac_slugs()
                mac_queue = [s for s in MAC_MILL.SCENARIOS if s["slug"] not in taken]
                mac_i = 0
                if not mac_queue and (n_sir > 71) and (n_ssl > 131):
                    print("no remaining unique MAC plants and hop catalogs done", flush=True)
                    break
    print(json.dumps({"published": published, "mac_frontier": round_txn.frontier_status(MAC)["next_round"]}), flush=True)
    return 0 if sum(published.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
