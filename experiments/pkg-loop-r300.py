#!/usr/bin/env python3
"""Reserve → mill → publish leftover dist-archive rounds for package-release r300+.

Never steal a reserved round. If package-release is reserved, hop
ssl-cert-rotation-factory only if that factory is unreserved and the ssl
mill covers its frontier. Never rewrite outputs/raw.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "pkg-mill-r300.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r35.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
SSL = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "ssl-cert-rotation-factory"

import importlib.util


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_m = _load(MILL)
CATALOG_FIRST = _m.CATALOG_FIRST
CATALOG_LAST = CATALOG_FIRST + len(_m.PAIRS) - 1
SSL_FIRST = SSL_LAST = None
if SSL_MILL.exists():
    _ssl = _load(SSL_MILL)
    SSL_FIRST = _ssl.CATALOG_FIRST
    SSL_LAST = SSL_FIRST + len(_ssl.PAIRS) - 1


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> dict:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    return json.loads(proc.stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def publish_round(factory: Path, mill: Path, n: int, expected: str = "2") -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            expected,
        ]
    )
    payload = json.loads(proc.stdout)
    token, staging = payload["token"], payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    try:
        mill_out = run([sys.executable, str(mill), "--round", str(n), "--staging", staging])
        print(mill_out.stdout, flush=True)
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
        run(
            [
                sys.executable,
                str(TXN),
                "abort",
                str(factory),
                "--round",
                str(n),
                "--token",
                token,
            ],
            check=False,
        )
        raise


def try_hop() -> str | None:
    if SSL_FIRST is None:
        return None
    try:
        hs = frontier(SSL)
    except Exception as exc:
        print(f"hop ssl frontier failed: {exc}", flush=True)
        return None
    hn = hs["next_round"]
    if reserved_path(SSL, hn).exists():
        print(f"hop ssl-cert-rotation r{hn} reserved; skip", flush=True)
        return None
    if not (SSL_FIRST <= hn <= SSL_LAST):
        print(f"hop ssl-cert-rotation r{hn} outside mill {SSL_FIRST}-{SSL_LAST}; skip", flush=True)
        return None
    print(f"hop ssl-cert-rotation r{hn}", flush=True)
    publish_round(SSL, SSL_MILL, hn)
    return f"ssl-{hn}"


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    deadline = time.time() + 40 * 60
    done = 0
    published: list[str] = []
    while done < max_rounds and time.time() < deadline:
        status = frontier(FACTORY)
        n = status["next_round"]
        if n > CATALOG_LAST:
            print(f"catalog exhausted at frontier {n} (last {CATALOG_LAST})", flush=True)
            break
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} already reserved; hop", flush=True)
            hopped = try_hop()
            if hopped is None:
                print("ssl hop blocked; never steal; wait 20s", flush=True)
                time.sleep(20)
                continue
            done += 1
            published.append(hopped)
            print(f"published hop {hopped} ({done})", flush=True)
            continue
        try:
            publish_round(FACTORY, MILL, n)
        except subprocess.CalledProcessError as exc:
            text = (exc.stderr or "") + (exc.stdout or "")
            if reserved_path(FACTORY, n).exists() and "already" in text.lower():
                print("lost race on reserve; never steal; hop", flush=True)
                hopped = try_hop()
                if hopped is None:
                    time.sleep(20)
                    continue
                done += 1
                published.append(hopped)
                continue
            print("reserve/mill/publish failed", flush=True)
            return 6
        done += 1
        published.append(f"pkg-{n}")
        print(f"published package-release r{n} ({done})", flush=True)
    nxt = frontier(FACTORY)["next_round"]
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "pkg_frontier": nxt,
                "catalog_last": CATALOG_LAST,
            }
        )
    )
    return 0 if done >= 12 or nxt > CATALOG_LAST else 2


if __name__ == "__main__":
    raise SystemExit(main())
