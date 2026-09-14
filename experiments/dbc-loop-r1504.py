#!/usr/bin/env python3
"""Prefer docker-build-cache r1504 mill. Never steal a reservation.

Never rewrite raw. Do not hop. Stop on foreign reservation or two
consecutive NOTES coverage values under 5%. Cap at 26 publishes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
DBC = AGENTIC / "docker-build-cache-factory"
DBC_MILL = ROOT / "experiments" / "dbc-mill-r1504.py"
LEDGER = ROOT / "experiments" / ".dbc-used-slugs.txt"

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


DBC_M = load(DBC_MILL, "dbc_mill_r1504")


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    text = proc.stdout.strip()
    payload = json.loads(text[text.rfind("{") :])
    print(
        json.dumps(
            {
                "factory": payload.get("factory"),
                "next_round": payload.get("next_round"),
                "highest_flushed": payload.get("highest_flushed"),
            }
        ),
        flush=True,
    )
    return payload["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def append_ledger(ids: list[str]) -> None:
    existing = LEDGER.read_text() if LEDGER.exists() else ""
    with LEDGER.open("a") as fh:
        for ident in ids:
            if ident and ident not in existing:
                fh.write(ident + "\n")


def notes_coverage(n: int) -> int | None:
    path = DBC / f"NOTES-r{n}.md"
    if not path.exists():
        path = DBC / f"NOTES-r{n:02d}.md"
    if not path.exists():
        return None
    match = re.search(r"Novel coverage:\s*(\d+)%", path.read_text())
    return int(match.group(1)) if match else None


def publish_one(factory: Path, n: int, mill: Path, extra: list[str] | None = None) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    mill_args = [
        sys.executable,
        str(mill),
        "--round",
        str(n),
        "--staging",
        staging,
    ]
    if extra:
        mill_args.extend(extra)
    mill_proc = run(mill_args)
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)
    try:
        mill_payload = json.loads(mill_proc.stdout.strip().splitlines()[-1])
        append_ledger(mill_payload.get("ids") or [])
    except (json.JSONDecodeError, IndexError, TypeError):
        pass


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    deadline = time.time() + 6 * 60 * 60
    done = 0
    published: list[str] = []
    low_streak = 0
    DBC_M.catalog_selfcheck()
    print(
        json.dumps({"catalog": len(DBC_M.PAIRS), "max_rounds": max_rounds}),
        flush=True,
    )
    while done < max_rounds and time.time() < deadline:
        idx = DBC_M.next_free_idx()
        if idx is None:
            print("docker r1504 catalog exhausted", flush=True)
            break
        n = frontier(DBC)
        if reserved(DBC, n) or writing(DBC):
            print(
                json.dumps({"docker_reserved": n, "stop": "foreign reservation"}),
                flush=True,
            )
            break
        try:
            publish_one(DBC, n, DBC_MILL, ["--idx", str(idx)])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(DBC, n) or writing(DBC):
                print("docker reserved during reserve; stop without stealing", flush=True)
                break
            print("docker mill/publish failed without seat", flush=True)
            return 5
        done += 1
        published.append(f"dbc-r{n}")
        cov = notes_coverage(n)
        print(f"published docker r{n} ({done}/{max_rounds}) idx={idx} cov={cov}", flush=True)
        if cov is not None and cov < 5:
            low_streak += 1
            if low_streak >= 2:
                print("two consecutive NOTES coverage <5%; stop", flush=True)
                break
        else:
            low_streak = 0
    print(json.dumps({"published": done, "rounds": published}))
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
