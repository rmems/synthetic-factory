#!/usr/bin/env python3
"""Reserve → mill → publish leftover leftover leftover authz plants (16 rounds)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "authz-regression-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "azr_mill_r1415", ROOT / "experiments" / "azr-mill-r1415-leftover3.py"
)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)


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
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(n: int, pair_idx: int) -> list[str]:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(FACTORY),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    token = payload["token"]
    staging = payload["staging_dir"]
    try:
        _mill.write_round(n, Path(staging), pair_idx)
        pub = run(
            [
                sys.executable,
                str(TXN),
                "publish",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ]
        )
        print(pub.stdout, flush=True)
        return []
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(FACTORY),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    published: list[dict] = []
    pair_idx = 0
    spins = 0
    while pair_idx < max_rounds and spins < 400:
        spins += 1
        n = frontier(FACTORY)
        if reserved(FACTORY, n):
            print(f"authz r{n} reserved; wait (never steal)", flush=True)
            time.sleep(0.4)
            continue
        try:
            publish_one(n, pair_idx)
        except subprocess.CalledProcessError as exc:
            print((exc.stdout or "")[-1500:], (exc.stderr or "")[-1500:], flush=True)
            print(f"lost or failed r{n}; retry (never steal)", flush=True)
            time.sleep(0.25)
            continue
        except Exception as exc:
            print("error", exc, flush=True)
            time.sleep(0.2)
            continue
        sa, sb = _mill.PAIRS[pair_idx]
        rec = {
            "round": n,
            "ids": [f"azr-r{n}-{sa['slug']}", f"azr-r{n}-{sb['slug']}"],
        }
        published.append(rec)
        print(json.dumps({"published": rec}), flush=True)
        pair_idx += 1
    print(json.dumps({"ok": True, "count": len(published), "rounds": published}))
    return 0 if len(published) == max_rounds else 2


if __name__ == "__main__":
    raise SystemExit(main())
